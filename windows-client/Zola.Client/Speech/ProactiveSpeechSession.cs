namespace Zola.Client.Speech;

// P9-SPEAK: reservation ordering. _gate is the reservation lock. No store or socket call runs while it is held.
// Push-to-talk, submit, composer, wake, turn, and Stop speaking all enter through OnStampAsync, which takes _gate
// before capture or submit continues. The order is:
//   claim → final check → speech_started → revalidate under _gate → voice.tts.
// A stamp before speech_started is sent releases the claim and voice.tts is not called.
// A stamp while speech_started is in flight only sets Cancelled. When the call returns, a failure releases
// and does not dispatch. A success records uncertain and does not dispatch.
// ConfirmDispatch sets dispatch-in-flight under _gate immediately before voice.tts. A stamp during that call
// sets Cancelled and does not send an outcome. When voice.tts returns, playback is stopped and the outcome is
// uncertain. A later bout end cannot send delivered once an outcome is pending, and a release is never followed
// by an outcome for that attempt.
internal sealed class ProactiveSpeechSession
{
    private readonly ISpeechGateway _gateway;
    private readonly ProactiveDeliveryCoordinator _coordinator = new();
    private readonly Func<SpeechFacts> _facts;
    private readonly Action? _stopPlayback;
    private readonly Action<string>? _rememberPhrase;
    private readonly Action<WatcherHudResult>? _onHud;
    private readonly Action<string?> _writeLog;
    private readonly Func<WatcherProcessLatch> _latch;
    private readonly Func<Task>? _prepareMonitor;
    private readonly Action<string>? _noteSpoken;
    private readonly object _gate = new();
    private bool _recovered;

    internal Func<Task>? BeforeSpeechStartedForTests { get; set; }
    public DateTimeOffset? LastComposerInputUtc { get; private set; }
    public DateTimeOffset? LastSubmitUtc { get; private set; }

    public SpeechEchoGuard Echo { get; } = new();

    public ProactiveSpeechSession(
        ISpeechGateway gateway,
        Func<SpeechFacts> facts,
        Func<WatcherProcessLatch> latch,
        Action? stopPlayback,
        Action<string>? rememberPhrase,
        Action<WatcherHudResult>? onHud,
        Action<string?>? writeLog = null,
        Func<Task>? prepareMonitor = null,
        Action<string>? noteSpoken = null)
    {
        _gateway = gateway;
        _facts = facts;
        _latch = latch;
        _stopPlayback = stopPlayback;
        _rememberPhrase = rememberPhrase;
        _onHud = onHud;
        _writeLog = writeLog ?? WriteLogFile;
        _prepareMonitor = prepareMonitor;
        _noteSpoken = noteSpoken;
    }

    public void NoteComposer(DateTimeOffset utcNow)
    {
        LastComposerInputUtc = utcNow;
        _ = OnStampAsync(SpeechConstants.StampComposer);
    }

    public void NoteSubmit(DateTimeOffset utcNow)
    {
        LastSubmitUtc = utcNow;
        _ = OnStampAsync(SpeechConstants.StampSubmit);
    }

    public Task OnStampAsync(string stamp)
    {
        SpeechAction action;
        lock (_gate)
        {
            action = _coordinator.NoteStamp(stamp, _facts());
        }

        StopIfNeeded(action);
        return ExecuteAsync(action);
    }

    public Task NotePlayback(bool active, bool forced)
    {
        SpeechAction action;
        lock (_gate)
        {
            action = _coordinator.NotePlayback(_facts(), active, forced);
        }

        // P9-SPEAK: only the proactive bout ends the tail. A later reply must not restart it — P9-D11
        if (!active && action.Step == SpeechStep.Outcome)
        {
            Echo.NoteCompleted(_facts().UtcNow);
        }

        StopIfNeeded(action);
        return ExecuteAsync(action);
    }

    public async Task PollAsync()
    {
        if (!_recovered)
        {
            SpeechStoreReply recovered;
            try
            {
                recovered = await _gateway.RecoverAsync().ConfigureAwait(false);
            }
            catch (Exception)
            {
                recovered = new SpeechStoreReply(false, SpeechConstants.ReasonBackendDown);
            }

            SpeechAction note;
            lock (_gate)
            {
                _recovered = recovered.Ok;
                note = recovered.Ok
                    ? _coordinator.NoteRecovered()
                    : _coordinator.NoteRecoverFailed(recovered.Reason);
            }

            _writeLog(note.LogLine);
        }

        try
        {
            var hud = await _gateway.HealthAsync(_latch(), _facts().UtcNow).ConfigureAwait(false);
            _onHud?.Invoke(hud);
        }
        catch (Exception)
        {
            _onHud?.Invoke(WatcherHud.Classify(null, _latch(), _facts().UtcNow));
        }

        if (!_recovered)
        {
            return;
        }

        SpeechAction action;
        lock (_gate)
        {
            action = _coordinator.Poll(_facts());
        }

        await ExecuteAsync(action).ConfigureAwait(false);
    }

    private async Task ExecuteAsync(SpeechAction action)
    {
        _writeLog(action.LogLine);
        switch (action.Step)
        {
            case SpeechStep.Snapshot:
                var snapshot = await _gateway.SnapshotAsync().ConfigureAwait(false);
                SpeechAction afterSnapshot;
                lock (_gate)
                {
                    afterSnapshot = _coordinator.AfterSnapshot(_facts(), snapshot);
                }

                await ExecuteAsync(afterSnapshot).ConfigureAwait(false);
                break;
            case SpeechStep.Claim:
                var claim = await _gateway.ClaimAsync().ConfigureAwait(false);
                SpeechAction afterClaim;
                lock (_gate)
                {
                    afterClaim = _coordinator.AfterClaim(_facts(), claim);
                }

                await ExecuteAsync(afterClaim).ConfigureAwait(false);
                break;
            case SpeechStep.SpeechStarted:
                if (BeforeSpeechStartedForTests is not null)
                {
                    await BeforeSpeechStartedForTests().ConfigureAwait(false);
                }

                if (string.IsNullOrEmpty(action.ItemId) || string.IsNullOrEmpty(action.AttemptId))
                {
                    break;
                }

                bool send;
                lock (_gate)
                {
                    send = _coordinator.BeginStartRpc();
                }

                if (!send)
                {
                    break;
                }

                var started = await _gateway.SpeechStartedAsync(action.ItemId, action.AttemptId).ConfigureAwait(false);
                SpeechAction afterStarted;
                lock (_gate)
                {
                    afterStarted = _coordinator.AfterSpeechStarted(_facts(), started);
                }

                StopIfNeeded(afterStarted);
                await ExecuteAsync(afterStarted).ConfigureAwait(false);
                break;
            case SpeechStep.Speak:
                SpeechAction decision;
                lock (_gate)
                {
                    decision = _coordinator.ConfirmDispatch(_facts());
                }

                if (decision.Step != SpeechStep.Speak)
                {
                    StopIfNeeded(decision);
                    await ExecuteAsync(decision).ConfigureAwait(false);
                    break;
                }

                if (!string.IsNullOrEmpty(decision.Phrase))
                {
                    Echo.Remember(decision.Phrase, _facts().UtcNow);
                    _rememberPhrase?.Invoke(decision.Phrase);
                }

                var phrase = decision.Phrase ?? "";
                var accepted = await _gateway.SpeakAsync(phrase).ConfigureAwait(false);
                if (accepted && phrase.Length > 0)
                {
                    // P9-SPEAK: the conversation list only has chat turns, so the spoken line is added here — P9-D11
                    _noteSpoken?.Invoke(phrase);
                }

                if (accepted && _prepareMonitor is not null)
                {
                    await _prepareMonitor().ConfigureAwait(false);
                }

                SpeechAction afterSpeak;
                lock (_gate)
                {
                    afterSpeak = _coordinator.AfterSpeak(_facts(), accepted);
                }

                StopIfNeeded(afterSpeak);
                if (afterSpeak.Step == SpeechStep.Outcome)
                {
                    Echo.NoteCompleted(_facts().UtcNow);
                }

                await ExecuteAsync(afterSpeak).ConfigureAwait(false);
                break;
            case SpeechStep.Release:
                await FinishStoreAsync(action, (item, attempt, _) => _gateway.ReleaseAsync(item, attempt)).ConfigureAwait(false);
                break;
            case SpeechStep.Outcome:
                await FinishStoreAsync(action, (item, attempt, outcome) => _gateway.OutcomeAsync(item, attempt, outcome ?? "")).ConfigureAwait(false);
                break;
        }
    }

    private async Task FinishStoreAsync(
        SpeechAction action,
        Func<string, string, string?, Task<SpeechStoreReply>> call)
    {
        if (string.IsNullOrEmpty(action.ItemId) || string.IsNullOrEmpty(action.AttemptId))
        {
            return;
        }

        if (action.Step == SpeechStep.Outcome && string.IsNullOrEmpty(action.StoreOutcome))
        {
            return;
        }

        var reply = await call(action.ItemId, action.AttemptId, action.StoreOutcome).ConfigureAwait(false);
        string? line;
        lock (_gate)
        {
            line = _coordinator.AfterStore(_facts(), reply);
        }

        _writeLog(line);
    }

    private void StopIfNeeded(SpeechAction action)
    {
        if (action.StopPlayback)
        {
            _stopPlayback?.Invoke();
        }
    }

    private static void WriteLogFile(string? line)
    {
        if (string.IsNullOrEmpty(line))
        {
            return;
        }

        try
        {
            var dir = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "ZolaClient",
                "logs");
            Directory.CreateDirectory(dir);
            File.AppendAllText(Path.Combine(dir, "proactive.log"), line + Environment.NewLine);
        }
        catch (Exception)
        {
            // A log failure must not become a speech.
        }
    }
}
