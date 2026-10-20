using Zola.Client;
using Zola.Client.Speech;
using Zola.Client.Supervision;

internal sealed partial class CheckRunner
{
    private void RunPhoneRows()
    {
        Phone("watcher start plan has no launch secret", () =>
        {
            var start = PythonStart.Build(
                @"C:\hermes\.venv\Scripts\python.exe",
                @"C:\hermes",
                @"C:\profile",
                "zola_workspace.watcher",
                "ZOLA_WATCHER_PARENT_PID",
                42,
                null);
            return start.FileName.EndsWith("python.exe", StringComparison.Ordinal)
                && start.WorkingDirectory == @"C:\hermes"
                && !start.UseShellExecute
                && start.CreateNoWindow
                && start.RedirectStandardOutput
                && start.RedirectStandardError
                && string.Join(" ", start.ArgumentList) == "-m zola_workspace.watcher"
                && start.Environment["HERMES_HOME"] == @"C:\profile"
                && start.Environment["PYTHONUNBUFFERED"] == "1"
                && start.Environment["ZOLA_WATCHER_PARENT_PID"] == "42"
                && start.Environment["PYTHONPATH"] == @"C:\profile\plugins" + Path.PathSeparator + @"C:\hermes"
                && !start.Environment.ContainsKey(PythonStart.SecretEnv);
        });
        Phone("phone start plan carries the secret and a different module", () =>
        {
            var start = PythonStart.Build(
                @"C:\hermes\.venv\Scripts\python.exe",
                @"C:\hermes",
                @"C:\profile",
                "zola_phone",
                "ZOLA_PHONE_PARENT_PID",
                42,
                "launch-secret");
            return string.Join(" ", start.ArgumentList) == "-m zola_phone"
                && start.Environment["ZOLA_PHONE_PARENT_PID"] == "42"
                && start.Environment[PythonStart.SecretEnv] == "launch-secret"
                && !start.Environment.ContainsKey("ZOLA_WATCHER_PARENT_PID");
        });
        Phone("companion latch wins and unknown stays hidden", () =>
        {
            var now = DateTimeOffset.Parse("2026-10-16T12:00:00Z");
            var hidden = SystemsCopy.Rows(Facts(now, WatcherProcessLatch.Running, null, false));
            var restarting = SystemsCopy.Rows(Facts(now, WatcherProcessLatch.Restarting, "connected", false));
            var failing = SystemsCopy.Rows(Facts(now, WatcherProcessLatch.Stopped, "connected", true));
            var quiet = SystemsCopy.Rows(Facts(now, WatcherProcessLatch.Running, "connected", false));
            var missed = SystemsCopy.Rows(Facts(now, WatcherProcessLatch.Running, "not_responding", false));
            var offline = SystemsCopy.Rows(Facts(now, WatcherProcessLatch.Running, "offline", false));
            var tailnet = SystemsCopy.Rows(Facts(now, WatcherProcessLatch.Running, "no_tailnet", false));
            return hidden.Length == 6
                && hidden[1].Label == SystemsCopy.WorkspaceWatcher
                && hidden[2].Label == SystemsCopy.GoogleAccount
                && !hidden[5].Visible
                && restarting[5].State == SystemsCopy.Restarting
                && restarting[5].Level == SystemsCopy.Level.Attention
                && failing[5].State == SystemsCopy.Failing
                && failing[5].Level == SystemsCopy.Level.Down
                && quiet[5].Visible
                && quiet[5].State is null
                && quiet[5].Level == SystemsCopy.Level.Quiet
                && missed[5].State == SystemsCopy.NotResponding
                && missed[5].Level == SystemsCopy.Level.Attention
                && offline[5].State == SystemsCopy.Offline
                && offline[5].Level == SystemsCopy.Level.Down
                && tailnet[5].State == SystemsCopy.NoTailnet
                && tailnet[5].Level == SystemsCopy.Level.Attention;
        });
        Phone("watcher environment matches the frozen start record", () =>
        {
            var blank = new System.Diagnostics.ProcessStartInfo();
            var start = PythonStart.Build(
                @"C:\hermes\.venv\Scripts\python.exe",
                @"C:\hermes",
                @"C:\profile",
                "zola_workspace.watcher",
                "ZOLA_WATCHER_PARENT_PID",
                42,
                null);
            string[] owned =
            [
                "HERMES_HOME",
                "PYTHONUNBUFFERED",
                "ZOLA_WATCHER_PARENT_PID",
                "PYTHONPATH",
            ];
            foreach (var key in start.Environment.Keys)
            {
                var changed = !blank.Environment.TryGetValue(key, out var previous) || previous != start.Environment[key];
                if (changed && Array.IndexOf(owned, key) < 0)
                {
                    return false;
                }
            }

            return start.FileName == @"C:\hermes\.venv\Scripts\python.exe"
                && start.WorkingDirectory == @"C:\hermes"
                && string.Join(" ", start.ArgumentList) == "-m zola_workspace.watcher"
                && start.Environment["HERMES_HOME"] == @"C:\profile"
                && start.Environment["PYTHONUNBUFFERED"] == "1"
                && start.Environment["ZOLA_WATCHER_PARENT_PID"] == "42"
                && start.Environment["PYTHONPATH"] == @"C:\profile\plugins" + Path.PathSeparator + @"C:\hermes"
                && !start.Environment.ContainsKey(PythonStart.SecretEnv);
        });
        Phone("phone restarts three times and the fourth keeps failing", () =>
        {
            var supervisor = new WatcherSupervisor();
            var now = DateTimeOffset.Parse("2026-10-20T12:00:00Z");
            var first = supervisor.BeginSpawn();
            var a = supervisor.NoteExit(first, now);
            var second = supervisor.BeginSpawn();
            var b = supervisor.NoteExit(second, now.AddMinutes(1));
            var third = supervisor.BeginSpawn();
            var c = supervisor.NoteExit(third, now.AddMinutes(2));
            var fourth = supervisor.BeginSpawn();
            var d = supervisor.NoteExit(fourth, now.AddMinutes(3));
            return a == WatcherExitKind.Spawn
                && b == WatcherExitKind.Spawn
                && c == WatcherExitKind.Spawn
                && d == WatcherExitKind.Terminal;
        });
        Phone("a deliberate phone stop does not count as a failure", () =>
        {
            var supervisor = new WatcherSupervisor();
            supervisor.NoteDeliberateStop();
            var generation = supervisor.BeginSpawn();
            return supervisor.NoteExit(generation, DateTimeOffset.Parse("2026-10-20T12:00:00Z"))
                == WatcherExitKind.IgnoredDeliberate;
        });
        Phone("a serve restart does not stop zola-phone", () =>
        {
            var root = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "..", "..", "..", ".."));
            var manager = File.ReadAllText(Path.Combine(root, "Zola.Client", "HermesProcessManager.cs"));
            var app = File.ReadAllText(Path.Combine(root, "Zola.Client", "App.xaml.cs"));
            var start = app.IndexOf("StartBackendAsync", StringComparison.Ordinal);
            var body = start < 0 ? "" : app[start..];
            return !manager.Contains("PhoneProcess", StringComparison.Ordinal)
                && !body.Contains("_phone", StringComparison.Ordinal)
                && PythonStart.Build(
                    @"C:\hermes\.venv\Scripts\python.exe",
                    @"C:\hermes",
                    @"C:\profile",
                    "zola_phone",
                    "ZOLA_PHONE_PARENT_PID",
                    7,
                    "secret").ArgumentList.Contains("zola_phone")
                && !PythonStart.Build(
                    @"C:\hermes\.venv\Scripts\python.exe",
                    @"C:\hermes",
                    @"C:\profile",
                    "hermes_cli.main",
                    "ZOLA_PHONE_PARENT_PID",
                    7,
                    null).ArgumentList.Contains("zola_phone");
        });
        Phone("companion row covers each link and the latch wins", () =>
        {
            var now = DateTimeOffset.Parse("2026-10-16T12:00:00Z");
            var paired = Row(now, WatcherProcessLatch.Running, "not_paired", false);
            var connected = Row(now, WatcherProcessLatch.Running, "connected", false);
            var missed = Row(now, WatcherProcessLatch.Running, "not_responding", false);
            var reconnecting = Row(now, WatcherProcessLatch.Running, "reconnecting", false);
            var offline = Row(now, WatcherProcessLatch.Running, "offline", false);
            var tailnet = Row(now, WatcherProcessLatch.Running, "no_tailnet", false);
            var restarting = Row(now, WatcherProcessLatch.Restarting, "connected", false);
            var failing = Row(now, WatcherProcessLatch.Stopped, "connected", true);
            return paired.State == SystemsCopy.NotPaired
                && paired.Level == SystemsCopy.Level.Attention
                && connected.Visible && connected.State is null && connected.Level == SystemsCopy.Level.Quiet
                && missed.State == SystemsCopy.NotResponding
                && reconnecting.State == SystemsCopy.Reconnecting && reconnecting.Level == SystemsCopy.Level.Attention
                && offline.State == SystemsCopy.Offline && offline.Level == SystemsCopy.Level.Down
                && tailnet.State == SystemsCopy.NoTailnet
                && restarting.State == SystemsCopy.Restarting
                && failing.State == SystemsCopy.Failing && failing.Level == SystemsCopy.Level.Down;
        });
        Phone("the pair dock button shows only when pairing is needed", () =>
        {
            var now = DateTimeOffset.Parse("2026-10-16T12:00:00Z");
            var unpaired = SystemsCopy.PairAction(Facts(now, WatcherProcessLatch.Running, "not_paired", false));
            var offline = SystemsCopy.PairAction(Facts(now, WatcherProcessLatch.Running, "offline", false));
            var connected = SystemsCopy.PairAction(Facts(now, WatcherProcessLatch.Running, "connected", false));
            var missed = SystemsCopy.PairAction(Facts(now, WatcherProcessLatch.Running, "not_responding", false));
            var reconnecting = SystemsCopy.PairAction(Facts(now, WatcherProcessLatch.Running, "reconnecting", false));
            var restarting = SystemsCopy.PairAction(Facts(now, WatcherProcessLatch.Restarting, "offline", false));
            var failing = SystemsCopy.PairAction(Facts(now, WatcherProcessLatch.Stopped, "offline", true));
            return unpaired == SystemsCopy.PairPhone
                && offline == SystemsCopy.RepairPhone
                && connected is null
                && missed is null
                && reconnecting is null
                && restarting is null
                && failing is null;
        });
        Phone("a phone poll skips while one is still running", () =>
        {
            var busy = 0;
            var first = PhonePollGate.TryEnter(ref busy);
            var second = PhonePollGate.TryEnter(ref busy);
            PhonePollGate.Exit(ref busy);
            var third = PhonePollGate.TryEnter(ref busy);
            return first && !second && third;
        });
        Phone("the pipe reader keeps a 64000 character line", () =>
        {
            var body = new string('Z', 64000);
            var json = "{\"text\":\"" + body + "\"}\n";
            using var stream = new MemoryStream(System.Text.Encoding.UTF8.GetBytes(json));
            var line = PhonePipe.ReadLine(stream);
            return line is not null && line.Contains(body, StringComparison.Ordinal) && !line.Contains('\n');
        });
    }

    private static SystemsCopy.View Row(DateTimeOffset now, WatcherProcessLatch latch, string link, bool failing)
    {
        return SystemsCopy.Rows(Facts(now, latch, link, failing))[5];
    }

    private static SystemsFacts Facts(DateTimeOffset now, WatcherProcessLatch latch, string? link, bool failing)
    {
        return new SystemsFacts(
            true, false, false, WatcherProcessLatch.Running, null, true,
            true, "idle", "2026-10-16T12:00:00Z", now, true, false,
            latch, link, failing);
    }

    private void Phone(string name, Func<bool> body)
    {
        _phoneTotal++;
        Run(name, body, pass =>
        {
            if (pass)
            {
                _phonePassed++;
            }
        });
    }
}
