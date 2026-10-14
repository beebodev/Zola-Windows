using System.Diagnostics;
using System.Runtime.InteropServices;
using Zola.Client.Supervision;

namespace Zola.Client;

// P9-WATCH: the watcher is a child of the client, not of serve — P9-D02
public sealed class WatcherProcess
{
    private readonly string _profileDirectory;
    private readonly WatcherSupervisor _supervisor = new();
    private readonly object _gate = new();
    private Process? _child;
    private SafeHandle? _job;
    private bool _stopped;
    private readonly ServeStderrLog _output;

    public WatcherProcess(string profileDirectory)
    {
        _profileDirectory = profileDirectory;
        _output = new ServeStderrLog(
            Path.Combine(profileDirectory, "logs"),
            SupervisionConstants.WatcherOutputFileName);
    }

    public WatcherSupervisor Supervisor => _supervisor;

    public void Start()
    {
        if (!HermesLaunchResolver.TryResolve(out var pythonPath, out var hermesRoot, out _))
        {
            SupervisionLog.Write(
                SupervisionConstants.ProcWatcher,
                SupervisionConstants.EventResolveFailed,
                _supervisor.Policy.AttemptsInWindow(DateTimeOffset.Now),
                0);
            return;
        }

        Spawn(pythonPath, hermesRoot);
    }

    public void StopDeliberate()
    {
        _supervisor.NoteDeliberateStop();
        lock (_gate)
        {
            _stopped = true;
        }

        KillChild();
    }

    private void Spawn(string pythonPath, string hermesRoot)
    {
        long generation;
        lock (_gate)
        {
            if (_stopped)
            {
                return;
            }

            generation = _supervisor.BeginSpawn();
        }

        var plugins = Path.Combine(_profileDirectory, "plugins");
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
        start.ArgumentList.Add("zola_workspace.watcher");
        start.Environment["HERMES_HOME"] = _profileDirectory;
        start.Environment["PYTHONUNBUFFERED"] = "1";
        start.Environment["ZOLA_WATCHER_PARENT_PID"] = Environment.ProcessId.ToString();
        var pythonPathEnv = plugins + Path.PathSeparator + hermesRoot;
        start.Environment["PYTHONPATH"] = pythonPathEnv;
        var child = new Process { StartInfo = start, EnableRaisingEvents = true };
        child.OutputDataReceived += (_, e) => _output.WriteLine(e.Data);
        child.ErrorDataReceived += (_, e) => _output.WriteLine(e.Data);
        child.Exited += (_, _) => OnExit(generation, child);
        if (!child.Start())
        {
            return;
        }

        child.BeginOutputReadLine();
        child.BeginErrorReadLine();

        var assigned = false;
        try
        {
            _job ??= WatcherJob.CreateKillOnClose();
            assigned = WatcherJob.TryAssign(_job, child.Handle);
        }
        catch (InvalidOperationException)
        {
            assigned = false;
        }

        SupervisionLog.Write(
            SupervisionConstants.ProcWatcher,
            assigned ? SupervisionConstants.EventJobAssigned : SupervisionConstants.EventJobAssignFailed,
            _supervisor.Policy.AttemptsInWindow(DateTimeOffset.Now),
            generation,
            child.Id);

        lock (_gate)
        {
            _child = child;
        }
    }

    private void OnExit(long generation, Process child)
    {
        var now = DateTimeOffset.Now;
        var restarts = _supervisor.Policy.AttemptsInWindow(now);
        int exitCode;
        try
        {
            exitCode = child.HasExited ? child.ExitCode : -1;
        }
        catch (InvalidOperationException)
        {
            exitCode = -1;
        }

        if (WatcherSupervisor.ClassifyExit(exitCode) is string named)
        {
            SupervisionLog.Write(SupervisionConstants.ProcWatcher, named, restarts, generation);
            child.Dispose();
            return;
        }

        var kind = _supervisor.NoteExit(generation, now);
        restarts = _supervisor.Policy.AttemptsInWindow(now);
        if (kind == WatcherExitKind.Spawn)
        {
            SupervisionLog.Write(SupervisionConstants.ProcWatcher, SupervisionConstants.EventRestart, restarts, generation);
            Task.Delay(TimeSpan.FromSeconds(SupervisionConstants.RestartBackoffSeconds))
                .ContinueWith(_ => Start());
            return;
        }

        var eventName = kind switch
        {
            WatcherExitKind.IgnoredStale => SupervisionConstants.EventStale,
            WatcherExitKind.Terminal => SupervisionConstants.EventKeepsFailing,
            _ => "stop",
        };
        SupervisionLog.Write(SupervisionConstants.ProcWatcher, eventName, restarts, generation);
        child.Dispose();
    }

    private void KillChild()
    {
        Process? child;
        lock (_gate)
        {
            child = _child;
            _child = null;
        }

        if (child is null)
        {
            return;
        }

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
    }
}
