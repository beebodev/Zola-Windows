using System.Diagnostics;
using System.Management;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using Zola.Client.Supervision;

namespace Zola.Client;

// P1-CLIENT: spawn or attach hermes serve on the zola profile and gate /api/ws on GET /api/health — P1-D01
public sealed partial class HermesProcessManager : IDisposable
{
    private const int ReadyTimeoutMs = 90_000;
    private const int HealthTimeoutMs = 45_000;
    private const int HealthPollMs = 500;

    private readonly object _gate = new();
    private readonly HttpClient _http = new() { Timeout = TimeSpan.FromSeconds(5) };
    private readonly ServeStderrLog _stderr = new();
    private Process? _child;
    private bool _shutdown;
    private long _ignoreExitGeneration = -1;

    // P9-SUPERVISE: one policy and one pair of counters for this client process — P9-D02
    public ServeGenerations Generations { get; } = new();

    public RestartPolicy Policy { get; } = new();

    public event Action<long>? UnexpectedExit;

    public bool IsShutdown => _shutdown;

    public HermesProcessManager()
    {
        // P1-CLIENT: dedicated profile lives under the Hermes profiles root, never the shared home — P1-D01
        ProfileDirectory = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "hermes",
            "profiles",
            ZolaServeCommand.ProfileName);
        StatusText = "Starting the Zola backend…";
        DetailText = ProfileDirectory;
    }

    public string ProfileDirectory { get; }

    public string StatusText { get; private set; }

    public string DetailText { get; private set; }

    public bool HealthPassed { get; private set; }

    public bool OwnsProcess { get; private set; }

    // P3-LIFE: launched/attached serve identity for TTS playback ownership — P3-D14 / S17
    public int? ServeProcessId { get; private set; }

    public int? Port { get; private set; }

    public string? SessionToken { get; private set; }

    public bool WebSocketPermitted => HealthPassed && !string.IsNullOrEmpty(SessionToken) && Port is > 0;

    public async Task<bool> CheckHealthAsync(CancellationToken cancellationToken)
    {
        // P1-CLIENT: chat watches GET /api/health so a dead serve becomes "backend unreachable" — P1-D01
        if (Port is not int port || port <= 0)
        {
            return false;
        }

        var probe = await ProbeHealthAsync(BaseUrl(port), cancellationToken).ConfigureAwait(false);
        return probe.Ok;
    }

    public event EventHandler? StateChanged;

    public async Task<bool> StartAsync(bool replace = false)
    {
        if (_shutdown)
        {
            return false;
        }

        try
        {
            if (replace)
            {
                // P9-SUPERVISE: tree-kill the previous generation before every replacement spawn — P9-D02
                KillGenerationForRestart();
            }

            // P1-CLIENT: empty profile dir lets -p zola resolve; Hermes seeds files, this client does not write SOUL.md — P1-D01
            Directory.CreateDirectory(ProfileDirectory);
            if (!HermesLaunchResolver.TryResolve(out var pythonPath, out var hermesRoot, out var error))
            {
                Fail(error);
                return false;
            }

            if (!replace)
            {
                var existing = await FindDedicatedServeAsync().ConfigureAwait(false);
                if (existing is not null)
                {
                    return await AttachAsync(existing.Value).ConfigureAwait(false);
                }
            }

            return await SpawnAsync(pythonPath, hermesRoot).ConfigureAwait(false);
        }
        catch (Exception ex)
        {
            // P1-CLIENT: surface startup failure instead of hanging on a missing backend — P1-D01
            Fail(ex.Message);
            return false;
        }
    }

    public void Shutdown()
    {
        // P9-SUPERVISE: app close is deliberate, so the exit must not count or restart — P9-D02
        Policy.NoteDeliberateStop();
        Volatile.Write(ref _ignoreExitGeneration, Generations.ProcessGeneration);
        Process? child;
        var owns = false;
        lock (_gate)
        {
            // P1-CLIENT: a second close must not kill a backend this window did not spawn — P1-D01
            if (_shutdown)
            {
                return;
            }

            _shutdown = true;
            child = _child;
            owns = OwnsProcess;
            _child = null;
            ServeProcessId = null;
        }

        if (!owns || child is null)
        {
            return;
        }

        try
        {
            // P1-CLIENT: tree-kill only the serve process this client spawned — P1-D01
            if (!child.HasExited)
            {
                child.Kill(entireProcessTree: true);
                child.WaitForExit(5_000);
            }
        }
        catch (InvalidOperationException)
        {
            // P1-CLIENT: the child already exited between the check and the kill — P1-D01
        }
        catch (System.ComponentModel.Win32Exception)
        {
            // P1-CLIENT: the pid was already gone when the tree kill ran — P1-D01
        }
        finally
        {
            child.Dispose();
        }
    }

    public void Dispose()
    {
        // P1-CLIENT: window close and dispose share one shutdown path — P1-D01
        Shutdown();
        _http.Dispose();
    }

    private async Task<bool> AttachAsync((int Pid, int Port, string CommandLine) existing)
    {
        // P9-SUPERVISE: an attached serve still gets a process generation so later callbacks can be stale — P9-D02
        Generations.BumpProcessGeneration();
        // P1-CLIENT: an already-running dedicated serve is attached and never killed on close — P1-D01
        Publish(
            "Attached to an already-running hermes serve. This window will not stop it.",
            $"pid {existing.Pid}  {existing.CommandLine}");
        Port = existing.Port;
        OwnsProcess = false;
        ServeProcessId = existing.Pid;
        var baseUrl = BaseUrl(existing.Port);
        var health = await WaitForHealthAsync(baseUrl).ConfigureAwait(false);
        if (!health.Ok)
        {
            Fail($"Attached process on {baseUrl} did not pass GET /api/health. WebSocket stays closed.");
            return false;
        }

        if (health.AuthRequired)
        {
            Fail("GET /api/health passed, but auth_required is true, so the loopback session token will be rejected. WebSocket stays closed.");
            return false;
        }

        SessionToken = await DashboardSessionToken.ReadServedTokenAsync(_http, baseUrl, CancellationToken.None)
            .ConfigureAwait(false);
        if (string.IsNullOrEmpty(SessionToken))
        {
            Fail("Attached backend is healthy, but GET / did not publish a session token. WebSocket stays closed.");
            return false;
        }

        NoteReady(baseUrl, spawned: false);
        return true;
    }

    private async Task<bool> SpawnAsync(string pythonPath, string hermesRoot)
    {
        // P9-SUPERVISE: process generation bumps on every spawn, before the child is published — P9-D02
        var generation = Generations.BumpProcessGeneration();
        Volatile.Write(ref _ignoreExitGeneration, generation);
        // P1-CLIENT: parent mints the token; Hermes reads HERMES_DASHBOARD_SESSION_TOKEN and does not print it — P1-D01
        var spawnToken = DashboardSessionToken.Mint();
        var start = new ProcessStartInfo
        {
            FileName = pythonPath,
            WorkingDirectory = hermesRoot,
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
        };
        start.ArgumentList.Add("-m");
        start.ArgumentList.Add("hermes_cli.main");
        start.ArgumentList.Add("-p");
        start.ArgumentList.Add(ZolaServeCommand.ProfileName);
        start.ArgumentList.Add("serve");
        start.ArgumentList.Add("--isolated");
        start.ArgumentList.Add("--host");
        start.ArgumentList.Add(ZolaServeCommand.BindHost);
        // P1-CLIENT: port 0 lets the ready sentinel name a free port when 9119 is already taken — P1-D01
        start.ArgumentList.Add("--port");
        start.ArgumentList.Add("0");
        start.Environment["HERMES_HOME"] = ProfileDirectory;
        start.Environment["HERMES_DASHBOARD_SESSION_TOKEN"] = spawnToken;
        start.Environment["PYTHONUNBUFFERED"] = "1";
        PrependPythonPath(start, hermesRoot);
        start.Environment.Remove("HERMES_DESKTOP");
        start.Environment.Remove("HERMES_WEB_DIST");
        start.Environment.Remove("HERMES_SERVE_HEADLESS");

        var child = new Process { StartInfo = start, EnableRaisingEvents = true };
        var ready = new TaskCompletionSource<int>(TaskCreationOptions.RunContinuationsAsynchronously);
        var blocked = new TaskCompletionSource<string>(TaskCreationOptions.RunContinuationsAsynchronously);
        var output = new StringBuilder();

        void OnLine(string? line, bool fromError)
        {
            if (fromError)
            {
                // P9-SUPERVISE: keep draining stderr into the rotating log so the pipe cannot block serve — P9-D02
                _stderr.WriteLine(line);
            }

            // P1-CLIENT: HERMES_BACKEND_READY port=n is the spawn sentinel; port-in-use must not be killed — P1-D01
            if (string.IsNullOrEmpty(line))
            {
                return;
            }

            lock (output)
            {
                if (output.Length < 16_000)
                {
                    output.AppendLine(line);
                }
            }

            var readyMatch = ReadySentinel().Match(line);
            if (readyMatch.Success && int.TryParse(readyMatch.Groups[1].Value, out var port))
            {
                ready.TrySetResult(port);
            }

            var busyMatch = PortInUseSentinel().Match(line);
            if (busyMatch.Success)
            {
                blocked.TrySetResult($"Port {busyMatch.Groups[1].Value} is already in use by a process this client did not spawn.");
            }
        }

        child.OutputDataReceived += (_, e) => OnLine(e.Data, fromError: false);
        child.ErrorDataReceived += (_, e) => OnLine(e.Data, fromError: true);
        child.Exited += (_, _) =>
        {
            // P1-CLIENT: an exit before the ready sentinel is a failed start, not an attach — P1-D01
            ready.TrySetCanceled();
            blocked.TrySetResult("hermes serve exited before HERMES_BACKEND_READY.");
            // P9-SUPERVISE: ignore a stale generation and a deliberate tree-kill; a live generation is unexpected — P9-D02
            if (!Generations.IsCurrentProcess(generation))
            {
                SupervisionLog.Write(SupervisionConstants.ProcServe, SupervisionConstants.EventStale, Policy.AttemptsInWindow(DateTimeOffset.Now), generation);
                return;
            }

            if (_shutdown || generation == Volatile.Read(ref _ignoreExitGeneration))
            {
                return;
            }

            UnexpectedExit?.Invoke(generation);
        };

        if (!child.Start())
        {
            Fail("Failed to start python for hermes serve.");
            child.Dispose();
            return false;
        }

        lock (_gate)
        {
            if (_shutdown)
            {
                TryKill(child);
                return false;
            }

            _child = child;
            OwnsProcess = true;
            ServeProcessId = child.Id;
        }

        child.BeginOutputReadLine();
        child.BeginErrorReadLine();
        Publish("Launching hermes serve --isolated against the zola profile…", $"{pythonPath} -m hermes_cli.main -p zola serve --isolated --host 127.0.0.1 --port 0");

        var finished = await Task.WhenAny(ready.Task, blocked.Task, Task.Delay(ReadyTimeoutMs)).ConfigureAwait(false);
        if (finished != ready.Task || !ready.Task.IsCompletedSuccessfully)
        {
            var reason = blocked.Task.IsCompletedSuccessfully
                ? blocked.Task.Result
                : child.HasExited
                    ? $"hermes serve exited ({child.ExitCode}) before HERMES_BACKEND_READY."
                    : "Timed out waiting for HERMES_BACKEND_READY.";
            string tail;
            lock (output)
            {
                tail = output.ToString();
            }

            // P1-CLIENT: a port conflict belongs to another process; do not kill it — P1-D01
            // P1-CLIENT: stop only the child this client spawned; the process holding the port is left alone — P1-D01
            // P9-SUPERVISE: do not latch app shutdown, or the next restart cannot spawn — P9-D02
            StopSpawnedChild();

            Fail(string.IsNullOrWhiteSpace(tail) ? reason : reason + Environment.NewLine + tail.Trim());
            return false;
        }

        var announcedPort = ready.Task.Result;
        if (announcedPort <= 0)
        {
            StopSpawnedChild();
            Fail("HERMES_BACKEND_READY did not include a local port. WebSocket stays closed.");
            return false;
        }

        Port = announcedPort;
        var baseUrl = BaseUrl(announcedPort);
        var health = await WaitForHealthAsync(baseUrl).ConfigureAwait(false);
        if (!health.Ok)
        {
            StopSpawnedChild();
            Fail($"HERMES_BACKEND_READY arrived, but GET {baseUrl}/api/health did not return ok. WebSocket stays closed.");
            return false;
        }

        if (health.AuthRequired)
        {
            StopSpawnedChild();
            Fail("GET /api/health passed, but auth_required is true, so the loopback session token will be rejected. WebSocket stays closed.");
            return false;
        }

        var served = await DashboardSessionToken.ReadServedTokenAsync(_http, baseUrl, CancellationToken.None)
            .ConfigureAwait(false);
        var childAlive = !child.HasExited;
        if (!string.IsNullOrEmpty(served) && served != spawnToken && !childAlive)
        {
            // P1-CLIENT: a different token from a dead child is a foreign backend; refuse it — P1-D01
            Fail("The spawned process exited and GET / is served by a different token. WebSocket stays closed.");
            return false;
        }

        SessionToken = string.IsNullOrEmpty(served) ? spawnToken : served;
        NoteReady(baseUrl, spawned: true);
        // P9-SUPERVISE: a ready process's later exit is unexpected and may count — P9-D02
        if (Generations.IsCurrentProcess(generation))
        {
            Volatile.Write(ref _ignoreExitGeneration, -1);
        }

        return true;
    }

    private async Task<(bool Ok, bool AuthRequired)> WaitForHealthAsync(string baseUrl)
    {
        // P1-CLIENT: readiness is GET /api/health specifically, polled until ok or the budget ends — P1-D01
        var deadline = Environment.TickCount64 + HealthTimeoutMs;
        while (Environment.TickCount64 < deadline)
        {
            var probe = await ProbeHealthAsync(baseUrl).ConfigureAwait(false);
            if (probe.Ok)
            {
                HealthPassed = true;
                return probe;
            }

            await Task.Delay(HealthPollMs).ConfigureAwait(false);
        }

        return (false, false);
    }

    private async Task<(bool Ok, bool AuthRequired)> ProbeHealthAsync(string baseUrl, CancellationToken cancellationToken = default)
    {
        try
        {
            // P1-CLIENT: /api/health is unauthenticated and is the only gate before a later /api/ws open — P1-D01
            using var response = await _http.GetAsync(baseUrl + "/api/health", cancellationToken).ConfigureAwait(false);
            if (!response.IsSuccessStatusCode)
            {
                return (false, false);
            }

            await using var stream = await response.Content.ReadAsStreamAsync().ConfigureAwait(false);
            using var doc = await JsonDocument.ParseAsync(stream).ConfigureAwait(false);
            var ok = doc.RootElement.TryGetProperty("ok", out var okValue) && okValue.ValueKind == JsonValueKind.True;
            var authRequired = doc.RootElement.TryGetProperty("auth_required", out var authValue)
                && authValue.ValueKind == JsonValueKind.True;
            return (ok, authRequired);
        }
        catch (HttpRequestException)
        {
            return (false, false);
        }
        catch (TaskCanceledException)
        {
            return (false, false);
        }
        catch (JsonException)
        {
            return (false, false);
        }
    }

    private static async Task<(int Pid, int Port, string CommandLine)?> FindDedicatedServeAsync()
    {
        try
        {
            // P1-CLIENT: a dedicated serve may still be binding; wait for its loopback socket before spawning another — P1-D01
            var deadline = Environment.TickCount64 + 20_000;
            do
            {
                var pending = false;
                using var searcher = new ManagementObjectSearcher(
                    "SELECT ProcessId, CommandLine FROM Win32_Process WHERE CommandLine LIKE '%--isolated%'");
                foreach (var item in searcher.Get())
                {
                    using var row = (ManagementObject)item;
                    var commandLine = row["CommandLine"] as string ?? "";
                    if (!ZolaServeCommand.IsDedicatedServe(commandLine))
                    {
                        continue;
                    }

                    var pid = Convert.ToInt32(row["ProcessId"]);
                    var port = ZolaServeCommand.ReadPort(commandLine);
                    if (port == 0)
                    {
                        port = LoopbackListener.PortFor(pid);
                    }

                    if (port <= 0)
                    {
                        pending = true;
                        continue;
                    }

                    return (pid, port, commandLine);
                }

                if (!pending)
                {
                    return null;
                }

                await Task.Delay(250).ConfigureAwait(false);
            }
            while (Environment.TickCount64 < deadline);
        }
        catch (ManagementException)
        {
            // P1-CLIENT: if process query fails, fall through to spawn rather than attaching blindly — P1-D01
        }

        return null;
    }

    private void NoteReady(string baseUrl, bool spawned)
    {
        // P1-CLIENT: health passed and the token is known, so the chat view may open /api/ws — P1-D01
        var soul = Path.Combine(ProfileDirectory, "SOUL.md");
        var soulNote = File.Exists(soul)
            ? $"SOUL.md is under the zola profile ({soul})."
            : $"SOUL.md is not in the zola profile yet ({soul}).";
        var mode = spawned ? "Spawned" : "Attached";
        Publish(
            $"{mode}. Backend ready at {baseUrl}.",
            $"{soulNote} Bind {ZolaServeCommand.BindHost}. Session token held.");
    }

    private void Fail(string message)
    {
        // P1-CLIENT: a failed start leaves the WebSocket gate closed — P1-D01
        HealthPassed = false;
        SessionToken = null;
        ServeProcessId = null;
        Publish("Backend unreachable. " + message, ProfileDirectory);
    }

    private void Publish(string status, string detail)
    {
        StatusText = status;
        DetailText = detail;
        StateChanged?.Invoke(this, EventArgs.Empty);
    }

    private static void TryKill(Process child)
    {
        // P1-CLIENT: shutdown won the race with spawn; stop only this new child — P1-D01
        try
        {
            if (!child.HasExited)
            {
                child.Kill(entireProcessTree: true);
            }
        }
        catch (InvalidOperationException)
        {
        }
        catch (System.ComponentModel.Win32Exception)
        {
        }
        finally
        {
            child.Dispose();
        }
    }

    private static void PrependPythonPath(ProcessStartInfo start, string hermesRoot)
    {
        // P1-CLIENT: the checkout must stay importable when the child cwd is the hermes root — P1-D01
        var current = start.Environment.TryGetValue("PYTHONPATH", out var existing) ? existing : "";
        start.Environment["PYTHONPATH"] = string.IsNullOrEmpty(current)
            ? hermesRoot
            : hermesRoot + Path.PathSeparator + current;
    }

    private static string BaseUrl(int port) => $"http://{ZolaServeCommand.BindHost}:{port}";

    [GeneratedRegex(@"HERMES_BACKEND_READY port=(\d+)")]
    private static partial Regex ReadySentinel();

    [GeneratedRegex(@"BACKEND_PORT_IN_USE port=(\d+)")]
    private static partial Regex PortInUseSentinel();
}
