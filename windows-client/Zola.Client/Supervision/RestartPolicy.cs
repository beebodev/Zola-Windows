namespace Zola.Client.Supervision;

public enum RestartChoice
{
    BackoffThenSpawn,
    Terminal,
    IgnoredDeliberate,
}

public enum RecoveryAction
{
    SpawnAfterBackoff,
    ProbeAgainAfterHungSpacing,
    Reconnect,
    TreeKillThenSpawn,
    TreeKillThenTerminal,
    Terminal,
    Connected,
    Stopped,
}

// P9-SUPERVISE: pure restart and unreachable decisions; the host injects the clock — P9-D02
public sealed class RestartPolicy
{
    private readonly List<DateTimeOffset> _attempts = new();
    private readonly object _gate = new();
    private bool _terminal;
    private bool _deliberate;
    private int _healthFailures;
    private int _reconnectAttempts;
    private DateTimeOffset? _reconnectStarted;

    public bool IsTerminal
    {
        get
        {
            lock (_gate)
            {
                return _terminal;
            }
        }
    }

    public bool IsDeliberate
    {
        get
        {
            lock (_gate)
            {
                return _deliberate;
            }
        }
    }

    public int AttemptsInWindow(DateTimeOffset now)
    {
        lock (_gate)
        {
            Prune(now);
            return _attempts.Count;
        }
    }

    public void NoteDeliberateStop()
    {
        lock (_gate)
        {
            _deliberate = true;
        }
    }

    public void Reset()
    {
        lock (_gate)
        {
            _attempts.Clear();
            _terminal = false;
            _deliberate = false;
            _healthFailures = 0;
            _reconnectAttempts = 0;
            _reconnectStarted = null;
        }
    }

    public RestartChoice NoteRestartAttempt(DateTimeOffset now)
    {
        lock (_gate)
        {
            if (_deliberate)
            {
                return RestartChoice.IgnoredDeliberate;
            }

            if (_terminal)
            {
                return RestartChoice.Terminal;
            }

            Prune(now);
            _attempts.Add(now);
            if (_attempts.Count > SupervisionConstants.RestartLimit)
            {
                _terminal = true;
                return RestartChoice.Terminal;
            }

            return RestartChoice.BackoffThenSpawn;
        }
    }

    public RecoveryAction Decide(bool processAlive, bool? healthOk, bool socketUp, DateTimeOffset now)
    {
        lock (_gate)
        {
            if (_deliberate)
            {
                return RecoveryAction.Stopped;
            }

            if (_terminal)
            {
                return processAlive ? RecoveryAction.TreeKillThenTerminal : RecoveryAction.Terminal;
            }

            if (!processAlive)
            {
                return MapRestart(NoteRestartAttemptLocked(now), processAlive: false);
            }

            if (healthOk == false)
            {
                // P9-SUPERVISE: first failure is fail-closed; hung tree-kill waits for HungHealthFailureLimit — P9-D02
                _healthFailures++;
                if (_healthFailures < SupervisionConstants.HungHealthFailureLimit)
                {
                    return RecoveryAction.ProbeAgainAfterHungSpacing;
                }

                _healthFailures = 0;
                _reconnectAttempts = 0;
                _reconnectStarted = null;
                return MapRestart(NoteRestartAttemptLocked(now), processAlive: true);
            }

            if (healthOk == true)
            {
                _healthFailures = 0;
                if (socketUp)
                {
                    _reconnectAttempts = 0;
                    _reconnectStarted = null;
                    return RecoveryAction.Connected;
                }

                if (!ReconnectAllowedLocked(now))
                {
                    // P9-SUPERVISE: exhausted reconnects tree-kill and count; the process is not left running — P9-D02
                    _reconnectAttempts = 0;
                    _reconnectStarted = null;
                    return MapRestart(NoteRestartAttemptLocked(now), processAlive: true);
                }

                _reconnectStarted ??= now;
                _reconnectAttempts++;
                return RecoveryAction.Reconnect;
            }

            return RecoveryAction.ProbeAgainAfterHungSpacing;
        }
    }

    private RecoveryAction MapRestart(RestartChoice choice, bool processAlive)
    {
        if (choice == RestartChoice.IgnoredDeliberate)
        {
            return RecoveryAction.Stopped;
        }

        if (choice == RestartChoice.Terminal)
        {
            return processAlive ? RecoveryAction.TreeKillThenTerminal : RecoveryAction.Terminal;
        }

        return processAlive ? RecoveryAction.TreeKillThenSpawn : RecoveryAction.SpawnAfterBackoff;
    }

    private RestartChoice NoteRestartAttemptLocked(DateTimeOffset now)
    {
        if (_deliberate)
        {
            return RestartChoice.IgnoredDeliberate;
        }

        if (_terminal)
        {
            return RestartChoice.Terminal;
        }

        Prune(now);
        _attempts.Add(now);
        if (_attempts.Count > SupervisionConstants.RestartLimit)
        {
            _terminal = true;
            return RestartChoice.Terminal;
        }

        return RestartChoice.BackoffThenSpawn;
    }

    private bool ReconnectAllowedLocked(DateTimeOffset now)
    {
        if (_reconnectAttempts >= SupervisionConstants.ReconnectAttemptLimit)
        {
            return false;
        }

        if (_reconnectStarted is { } started
            && (now - started).TotalSeconds >= SupervisionConstants.ReconnectBudgetSeconds)
        {
            return false;
        }

        return true;
    }

    private void Prune(DateTimeOffset now)
    {
        var window = TimeSpan.FromMinutes(SupervisionConstants.RestartWindowMinutes);
        _attempts.RemoveAll(stamp => now - stamp >= window);
    }
}
