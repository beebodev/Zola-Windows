using Zola.Client.Speech;
using Zola.Client.Supervision;

namespace Zola.Client;

// P9-WATCH: the watcher is a child of the client, not of serve — P9-D02
public sealed class WatcherProcess
{
    private readonly SupervisedPython _inner;

    public WatcherProcess(string profileDirectory)
    {
        _inner = new SupervisedPython(
            profileDirectory,
            SupervisionConstants.ProcWatcher,
            "zola_workspace.watcher",
            "ZOLA_WATCHER_PARENT_PID",
            SupervisionConstants.WatcherOutputFileName,
            secret: null);
        _inner.LatchChanged += () => LatchChanged?.Invoke();
    }

    public WatcherProcessLatch Latch => _inner.Latch;

    public event Action? LatchChanged;

    public WatcherSupervisor Supervisor => _inner.Supervisor;

    public void Start() => _inner.Start();

    public void StopDeliberate() => _inner.StopDeliberate();
}
