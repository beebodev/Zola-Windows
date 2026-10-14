namespace Zola.Client.Supervision;

// P9-WATCH: the watcher has its own policy and generation, separate from serve — P9-D02
public enum WatcherExitKind
{
    IgnoredStale,
    IgnoredDeliberate,
    Spawn,
    Terminal,
}

public sealed class WatcherSupervisor
{
    public RestartPolicy Policy { get; } = new();

    public ServeGenerations Generations { get; } = new();

    public long BeginSpawn() => Generations.BumpProcessGeneration();

    public void NoteDeliberateStop() => Policy.NoteDeliberateStop();

    public static string? ClassifyExit(int exitCode)
    {
        if (exitCode == SupervisionConstants.WatcherAlreadyRunningExit)
        {
            return SupervisionConstants.EventAlreadyRunning;
        }

        return null;
    }

    public WatcherExitKind NoteExit(long generation, DateTimeOffset now)
    {
        if (!Generations.IsCurrentProcess(generation))
        {
            return WatcherExitKind.IgnoredStale;
        }

        var choice = Policy.NoteRestartAttempt(now);
        if (choice == RestartChoice.IgnoredDeliberate)
        {
            return WatcherExitKind.IgnoredDeliberate;
        }

        if (choice == RestartChoice.Terminal)
        {
            return WatcherExitKind.Terminal;
        }

        return WatcherExitKind.Spawn;
    }
}
