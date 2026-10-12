using Zola.Client.Supervision;

namespace Zola.Client;

// P9-SUPERVISE: one supervisor for hermes serve. The watcher in Track 3 can reuse RestartPolicy — P9-D02
internal sealed class ProcessSupervisor
{
    private readonly HermesProcessManager _backend;
    private readonly ChatSocket _chat;
    private readonly IOutageGap _gap;
    private readonly Func<Task<bool>> _connect;
    private readonly Func<Task> _showKeepsFailing;
    private int _loop;
    private int _lossSerial;

    public ProcessSupervisor(
        HermesProcessManager backend,
        ChatSocket chat,
        IOutageGap gap,
        Func<Task<bool>> connect,
        Func<Task> showKeepsFailing)
    {
        _backend = backend;
        _chat = chat;
        _gap = gap;
        _connect = connect;
        _showKeepsFailing = showKeepsFailing;
    }

    public void BeginAfterFailedStart()
    {
        // P9-SUPERVISE: a failed first start enters the same gap and restart policy — P9-D02
        NoteLoss(_backend.Generations.ProcessGeneration, _backend.Generations.ConnectionEpoch, processExit: true);
    }

    public void NoteLoss(long processGeneration, long connectionEpoch, bool processExit)
    {
        if (_backend.IsShutdown || _backend.Policy.IsDeliberate)
        {
            return;
        }

        if (!_backend.Generations.IsCurrentProcess(processGeneration))
        {
            // P9-SUPERVISE: a stale process generation is logged and ignored — P9-D02
            SupervisionLog.Write(
                SupervisionConstants.ProcServe,
                SupervisionConstants.EventStale,
                _backend.Policy.AttemptsInWindow(DateTimeOffset.Now),
                processGeneration);
            return;
        }

        if (!processExit && !_backend.Generations.IsCurrentEpoch(connectionEpoch))
        {
            // P9-SUPERVISE: a stale connection epoch is logged and ignored — P9-D02
            SupervisionLog.Write(
                SupervisionConstants.ProcServe,
                SupervisionConstants.EventStale,
                _backend.Policy.AttemptsInWindow(DateTimeOffset.Now),
                processGeneration);
            return;
        }

        var serial = Interlocked.Increment(ref _lossSerial);
        // P9-SUPERVISE: invalidate, drop, stop, and block before any restart await — P9-D02
        OutageGap.Apply(_backend.Generations, _gap);
        StartLoop(serial);
    }

    private void StartLoop(int serial)
    {
        if (Interlocked.CompareExchange(ref _loop, 1, 0) != 0)
        {
            return;
        }

        _ = LoopAsync(serial);
    }

    private async Task LoopAsync(int serial)
    {
        var seen = serial;
        try
        {
            while (!_backend.IsShutdown && !_backend.Policy.IsDeliberate)
            {
                var latest = Volatile.Read(ref _lossSerial);
                if (latest > seen)
                {
                    seen = latest;
                }

                var now = DateTimeOffset.Now;
                var alive = _backend.IsServeProcessAlive();
                RecoveryAction action;
                if (!alive)
                {
                    action = _backend.Policy.Decide(false, null, false, now);
                }
                else
                {
                    var health = await _backend.CheckHealthAsync(CancellationToken.None).ConfigureAwait(false);
                    action = _backend.Policy.Decide(true, health, _chat.IsSessionUsable, now);
                }

                switch (action)
                {
                    case RecoveryAction.Stopped:
                        return;
                    case RecoveryAction.Terminal:
                        SupervisionLog.Write(
                            SupervisionConstants.ProcServe,
                            SupervisionConstants.EventKeepsFailing,
                            _backend.Policy.AttemptsInWindow(now),
                            _backend.Generations.ProcessGeneration);
                        await _showKeepsFailing().ConfigureAwait(false);
                        return;
                    case RecoveryAction.TreeKillThenTerminal:
                        // P9-SUPERVISE: past the restart limit the process is still tree-killed — P9-D02
                        _backend.KillGenerationForRestart();
                        SupervisionLog.Write(
                            SupervisionConstants.ProcServe,
                            SupervisionConstants.EventKeepsFailing,
                            _backend.Policy.AttemptsInWindow(now),
                            _backend.Generations.ProcessGeneration);
                        await _showKeepsFailing().ConfigureAwait(false);
                        return;
                    case RecoveryAction.SpawnAfterBackoff:
                    case RecoveryAction.TreeKillThenSpawn:
                        SupervisionLog.Write(
                            SupervisionConstants.ProcServe,
                            SupervisionConstants.EventRestart,
                            _backend.Policy.AttemptsInWindow(now),
                            _backend.Generations.ProcessGeneration);
                        if (action == RecoveryAction.TreeKillThenSpawn)
                        {
                            _backend.KillGenerationForRestart();
                        }

                        await WaitAsync(SupervisionConstants.RestartBackoffSeconds, wakeIfProcessDies: false)
                            .ConfigureAwait(false);
                        if (_backend.IsShutdown || _backend.Policy.IsDeliberate)
                        {
                            return;
                        }

                        var spawned = await _backend.StartAsync(replace: true).ConfigureAwait(false);
                        if (!spawned)
                        {
                            continue;
                        }

                        if (await _connect().ConfigureAwait(false) && Volatile.Read(ref _lossSerial) == seen)
                        {
                            return;
                        }

                        continue;
                    case RecoveryAction.ProbeAgainAfterHungSpacing:
                        await WaitAsync(SupervisionConstants.HungProbeSpacingSeconds, wakeIfProcessDies: true)
                            .ConfigureAwait(false);
                        continue;
                    case RecoveryAction.Reconnect:
                        if (await _connect().ConfigureAwait(false) && Volatile.Read(ref _lossSerial) == seen)
                        {
                            return;
                        }

                        await WaitAsync(SupervisionConstants.ReconnectSpacingSeconds, wakeIfProcessDies: true)
                            .ConfigureAwait(false);
                        continue;
                    case RecoveryAction.Connected:
                        if (Volatile.Read(ref _lossSerial) == seen)
                        {
                            return;
                        }

                        continue;
                    default:
                        return;
                }
            }
        }
        finally
        {
            Interlocked.Exchange(ref _loop, 0);
            var latest = Volatile.Read(ref _lossSerial);
            if (latest != seen && !_backend.IsShutdown && !_backend.Policy.IsDeliberate)
            {
                StartLoop(latest);
            }
        }
    }

    private async Task WaitAsync(int seconds, bool wakeIfProcessDies)
    {
        var end = Environment.TickCount64 + seconds * 1000L;
        while (Environment.TickCount64 < end)
        {
            if (_backend.IsShutdown || _backend.Policy.IsDeliberate)
            {
                return;
            }

            if (wakeIfProcessDies && !_backend.IsTrackedProcessAlive() && !_backend.IsServeProcessAlive())
            {
                return;
            }

            await Task.Delay(200).ConfigureAwait(false);
        }
    }
}
