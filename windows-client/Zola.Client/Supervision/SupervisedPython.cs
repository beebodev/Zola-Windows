using System.Diagnostics;
using System.Runtime.InteropServices;
using Zola.Client.Speech;

namespace Zola.Client.Supervision;

// P10-INTAKE: the watcher and zola-phone share this spawn, job, and restart path — P10-D12
public sealed class SupervisedPython
{
    private readonly string _profileDirectory;
    private readonly string _procName;
    private readonly string _module;
    private readonly string _parentEnv;
    private readonly Func<string?>? _secret;
    private readonly WatcherSupervisor _supervisor = new();
    private readonly object _gate = new();
    private readonly ServeStderrLog _output;
    private Process? _child;
    private SafeHandle? _job;
    private bool _stopped;
    private bool _keepsFailing;
    private WatcherProcessLatch _latch = WatcherProcessLatch.Stopped;

    public SupervisedPython(
        string profileDirectory,
        string procName,
        string module,
        string parentEnv,
        string outputFileName,
        Func<string?>? secret)
    {
        _profileDirectory = profileDirectory;
        _procName = procName;
        _module = module;
        _parentEnv = parentEnv;
        _secret = secret;
        _output = new ServeStderrLog(Path.Combine(profileDirectory, "logs"), outputFileName);
    }

    public WatcherSupervisor Supervisor => _supervisor;

    public WatcherProcessLatch Latch
    {
        get
        {
            lock (_gate)
            {
                return _latch;
            }
        }
    }

    public bool KeepsFailing
    {
        get
        {
            lock (_gate)
            {
                return _keepsFailing;
            }
        }
    }

    public event Action? LatchChanged;

    public void Start()
    {
        if (!HermesLaunchResolver.TryResolve(out var pythonPath, out var hermesRoot, out _))
        {
            SupervisionLog.Write(
                _procName,
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
            _keepsFailing = false;
        }

        SetLatch(WatcherProcessLatch.Stopped);
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

        var start = PythonStart.Build(
            pythonPath,
            hermesRoot,
            _profileDirectory,
            _module,
            _parentEnv,
            Environment.ProcessId,
            _secret?.Invoke());
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
            _procName,
            assigned ? SupervisionConstants.EventJobAssigned : SupervisionConstants.EventJobAssignFailed,
            _supervisor.Policy.AttemptsInWindow(DateTimeOffset.Now),
            generation,
            child.Id);

        lock (_gate)
        {
            _child = child;
            _keepsFailing = false;
        }

        SetLatch(WatcherProcessLatch.Running);
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
            SupervisionLog.Write(_procName, named, restarts, generation);
            child.Dispose();
            return;
        }

        var kind = _supervisor.NoteExit(generation, now);
        restarts = _supervisor.Policy.AttemptsInWindow(now);
        if (kind == WatcherExitKind.Spawn)
        {
            SetLatch(WatcherProcessLatch.Restarting);
            SupervisionLog.Write(_procName, SupervisionConstants.EventRestart, restarts, generation);
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
        if (kind == WatcherExitKind.Terminal)
        {
            lock (_gate)
            {
                _keepsFailing = true;
            }

            SetLatch(WatcherProcessLatch.Stopped);
        }

        SupervisionLog.Write(_procName, eventName, restarts, generation);
        child.Dispose();
    }

    private void SetLatch(WatcherProcessLatch value)
    {
        lock (_gate)
        {
            _latch = value;
        }

        LatchChanged?.Invoke();
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
