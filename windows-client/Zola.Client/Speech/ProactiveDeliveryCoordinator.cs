namespace Zola.Client.Speech;

// P9-SPEAK: claim runs only after the client gates and a fresh snapshot. speech_started is before dispatch — P9-D11
public sealed class ProactiveDeliveryCoordinator
{
    private readonly PhraseCursor _phrases = new();
    private bool _held;
    private bool _startRecorded;
    private bool _startRpcInFlight;
    private bool _dispatchInFlight;
    private bool _cancelled;
    private string? _cancelStamp;
    private bool _accepted;
    private bool _started;
    private string? _itemId;
    private string? _attemptId;
    private string? _nameSource;
    private int _phraseIndex = -1;
    private string? _phrase;
    private DateTimeOffset _acceptedAt;
    private DateTimeOffset _startedAt;
    private string? _pendingOutcome;
    private DateTimeOffset _pendingNotBefore;

    public SpeechDenyLog Log { get; } = new();

    public bool ReservationHeld => _held;

    public bool ClaimBlocked => _held || _pendingOutcome is not null;

    public SpeechAction Poll(SpeechFacts facts)
    {
        var timed = Advance(facts);
        if (timed is not null)
        {
            return timed;
        }

        if (_pendingOutcome is not null)
        {
            if (facts.UtcNow < _pendingNotBefore)
            {
                return Stop();
            }

            return Store(_pendingOutcome == "release" ? SpeechStep.Release : SpeechStep.Outcome, _pendingOutcome == "release" ? "" : _pendingOutcome);
        }

        if (_held)
        {
            return Deny(SpeechConstants.ReasonOneAtATime);
        }

        var gate = LocalGate(facts);
        if (gate is not null)
        {
            return Deny(gate);
        }

        if (!Idle(facts))
        {
            return Deny(SpeechConstants.ReasonNotIdle);
        }

        return new SpeechAction { Step = SpeechStep.Snapshot };
    }

    public SpeechAction NoteRecoverFailed(string? reason)
    {
        var shown = string.IsNullOrEmpty(reason) ? SpeechConstants.ReasonRecoverFailed : reason;
        return Deny(shown);
    }

    public SpeechAction NoteRecovered()
    {
        return new SpeechAction
        {
            Step = SpeechStep.Stop,
            LogLine = Log.NoteReturnToIdle("recovered"),
        };
    }

    public SpeechAction AfterSnapshot(SpeechFacts facts, SpeechSnapshot snapshot)
    {
        if (!snapshot.Ok)
        {
            var reason = snapshot.Reason == SpeechConstants.ReasonSnapshotTimeout
                ? SpeechConstants.ReasonSnapshotTimeout
                : SpeechConstants.ReasonBackendDown;
            return Deny(reason);
        }

        if (snapshot.ServerTime is not DateTimeOffset server
            || Math.Abs((facts.UtcNow - server).TotalSeconds) > SpeechConstants.SnapshotTimeoutSeconds)
        {
            return Deny(SpeechConstants.ReasonSnapshotStale);
        }

        if (snapshot.TurnInFlight || facts.Turn)
        {
            return Deny(SpeechConstants.ReasonTurn);
        }

        if (snapshot.ReviewedDraft)
        {
            return Deny(SpeechConstants.ReasonReviewedDraft);
        }

        var gate = LocalGate(facts);
        if (gate is not null)
        {
            return Deny(gate);
        }

        return new SpeechAction { Step = SpeechStep.Claim };
    }

    public SpeechAction AfterClaim(SpeechFacts facts, SpeechClaimResult claim)
    {
        if (!claim.Ok)
        {
            var reason = string.IsNullOrEmpty(claim.Reason) ? SpeechConstants.ReasonReservationLost : claim.Reason;
            return Deny(reason, claim.AttemptId);
        }

        _itemId = claim.ItemId;
        _attemptId = claim.AttemptId;
        _held = true;
        var blocked = BlockReason(facts);
        if (blocked is not null)
        {
            return BeginRelease(blocked);
        }

        _accepted = false;
        _started = false;
        _startRecorded = false;
        _startRpcInFlight = false;
        _dispatchInFlight = false;
        _cancelled = false;
        _cancelStamp = null;
        _itemId = claim.ItemId;
        _attemptId = claim.AttemptId;
        _nameSource = string.IsNullOrEmpty(claim.Name) ? "someone" : (claim.NameSource ?? "someone");
        _phrase = SpeechPhrases.Pick(claim.Source, claim.Name, claim.NameSource, _phrases);
        _phraseIndex = IndexOf(_phrase, claim.Source, claim.Name, claim.NameSource);
        return Store(SpeechStep.SpeechStarted, "");
    }

    public bool BeginStartRpc()
    {
        if (!_held || _startRecorded || _pendingOutcome is not null || _cancelled)
        {
            return false;
        }

        _startRpcInFlight = true;
        return true;
    }

    public SpeechAction AfterSpeechStarted(SpeechFacts facts, SpeechStoreReply reply)
    {
        _startRpcInFlight = false;
        if (!_held || _pendingOutcome is not null)
        {
            return Stop();
        }

        if (!reply.Ok)
        {
            return BeginRelease(SpeechConstants.ReasonSpeechStartedFailed);
        }

        _startRecorded = true;
        var blocked = BlockReason(facts);
        if (blocked is not null)
        {
            return BeginUncertain(blocked, stopPlayback: false);
        }

        return SpeakNow();
    }

    public SpeechAction ConfirmDispatch(SpeechFacts facts)
    {
        if (!_held || _pendingOutcome is not null)
        {
            return Stop();
        }

        var blocked = BlockReason(facts);
        if (!_startRecorded || blocked is not null)
        {
            var reason = blocked ?? SpeechConstants.ReasonReservationLost;
            return _startRecorded
                ? BeginUncertain(reason, stopPlayback: false)
                : BeginRelease(reason);
        }

        _dispatchInFlight = true;
        return SpeakNow();
    }

    public SpeechAction AfterSpeak(SpeechFacts facts, bool accepted)
    {
        _dispatchInFlight = false;
        if (!_held || _pendingOutcome is not null || !_startRecorded)
        {
            return Stop();
        }

        if (_cancelStamp is not null)
        {
            return BeginUncertain(SpeechConstants.CancelledBy(_cancelStamp), stopPlayback: true);
        }

        if (!accepted)
        {
            return BeginUncertain(SpeechConstants.ReasonVoiceTtsRefused, stopPlayback: false);
        }

        if (!facts.MonitorAvailable)
        {
            return BeginUncertain(SpeechConstants.ReasonMonitorUnavailable, stopPlayback: true);
        }

        _accepted = true;
        _acceptedAt = facts.UtcNow;
        return Stop();
    }

    public SpeechAction NotePlayback(SpeechFacts facts, bool active, bool forced)
    {
        if (!_held || !_accepted || _pendingOutcome is not null)
        {
            return Stop();
        }

        if (_cancelStamp is not null)
        {
            return BeginUncertain(SpeechConstants.CancelledBy(_cancelStamp), stopPlayback: true);
        }

        if (active && !_started)
        {
            _started = true;
            _startedAt = facts.UtcNow;
            return Stop();
        }

        if (active && _started)
        {
            return BeginUncertain(SpeechConstants.ReasonSecondBout, stopPlayback: true);
        }

        if (!active && _started)
        {
            return forced
                ? BeginUncertain(SpeechConstants.ReasonReservationLost, stopPlayback: true)
                : BeginDelivered();
        }

        if (!active && forced)
        {
            return BeginUncertain(SpeechConstants.ReasonReservationLost, stopPlayback: true);
        }

        return Stop();
    }

    public SpeechAction NoteStamp(string stamp, SpeechFacts facts)
    {
        _ = facts;
        if (!_held || _pendingOutcome is not null)
        {
            return Stop();
        }

        _cancelStamp = stamp;
        _cancelled = true;
        if (_dispatchInFlight || _startRpcInFlight)
        {
            return Stop();
        }

        var reason = SpeechConstants.CancelledBy(stamp);
        if (!_startRecorded)
        {
            return BeginRelease(reason);
        }

        return BeginUncertain(reason, stopPlayback: _accepted || _started);
    }

    public string? AfterStore(SpeechFacts facts, SpeechStoreReply reply)
    {
        if (reply.Ok)
        {
            ClearHold();
            return null;
        }

        if (reply.Terminal)
        {
            var line = Log.Note("error", reply.Reason ?? "illegal_transition", _attemptId, _phraseIndex, _nameSource);
            ClearHold();
            return line;
        }

        if (_pendingOutcome is null)
        {
            return null;
        }

        _pendingNotBefore = facts.UtcNow.AddSeconds(SpeechConstants.OutcomeRetrySeconds);
        return null;
    }

    private SpeechAction? Advance(SpeechFacts facts)
    {
        if (!_held || _pendingOutcome is not null || _dispatchInFlight || _startRpcInFlight)
        {
            return null;
        }

        if (_accepted && !_started && facts.UtcNow > _acceptedAt.AddSeconds(SpeechConstants.StartTimeoutSeconds))
        {
            return BeginUncertain(SpeechConstants.ReasonStartTimeout, stopPlayback: false);
        }

        if (_started && facts.UtcNow > _startedAt.AddSeconds(SpeechConstants.CompleteTimeoutSeconds))
        {
            return BeginUncertain(SpeechConstants.ReasonCompleteTimeout, stopPlayback: true);
        }

        if (_started && !facts.BackendUp)
        {
            return BeginUncertain(SpeechConstants.ReasonBackendDown, stopPlayback: true);
        }

        return null;
    }

    private SpeechAction BeginRelease(string reason)
    {
        if (_pendingOutcome is not null)
        {
            return Stop();
        }

        _pendingOutcome = "release";
        _pendingNotBefore = DateTimeOffset.MinValue;
        var line = Log.Note("released", reason, _attemptId, _phraseIndex, _nameSource);
        return Store(SpeechStep.Release, "", reason, line);
    }

    // P9-SPEAK: reservation_lost is only a forced playback end, or a dispatch before speech_started, when no stamp or gate was recorded — P9-D11
    private string? BlockReason(SpeechFacts facts)
    {
        if (_cancelStamp is not null)
        {
            return SpeechConstants.CancelledBy(_cancelStamp);
        }

        var gate = LocalGate(facts);
        if (gate is not null)
        {
            return gate;
        }

        if (!Idle(facts))
        {
            return SpeechConstants.ReasonNotIdle;
        }

        return null;
    }

    private SpeechAction BeginUncertain(string reason, bool stopPlayback)
    {
        if (_pendingOutcome is not null)
        {
            return Stop();
        }

        _pendingOutcome = SpeechConstants.OutcomeUncertain;
        _pendingNotBefore = DateTimeOffset.MinValue;
        var line = Log.Note("uncertain", reason, _attemptId, _phraseIndex, _nameSource);
        return Store(SpeechStep.Outcome, SpeechConstants.OutcomeUncertain, reason, line, stopPlayback);
    }

    private SpeechAction BeginDelivered()
    {
        if (_pendingOutcome is not null)
        {
            return Stop();
        }

        _pendingOutcome = SpeechConstants.OutcomeDelivered;
        _pendingNotBefore = DateTimeOffset.MinValue;
        var line = Log.Note(SpeechConstants.OutcomeDelivered, "-", _attemptId, _phraseIndex, _nameSource);
        return Store(SpeechStep.Outcome, SpeechConstants.OutcomeDelivered, "", line);
    }

    private SpeechAction SpeakNow()
    {
        return Store(SpeechStep.Speak, "");
    }

    private SpeechAction Store(SpeechStep step, string storeOutcome, string reason = "", string? line = null, bool stopPlayback = false)
    {
        return new SpeechAction
        {
            Step = step,
            Reason = reason,
            ItemId = _itemId,
            AttemptId = _attemptId,
            Phrase = _phrase,
            PhraseIndex = _phraseIndex,
            NameSource = _nameSource,
            StoreOutcome = string.IsNullOrEmpty(storeOutcome) || storeOutcome == "release" ? null : storeOutcome,
            LogLine = line,
            StopPlayback = stopPlayback,
        };
    }

    private SpeechAction Deny(string reason, string? attemptId = null)
    {
        return new SpeechAction
        {
            Step = SpeechStep.Stop,
            Reason = reason,
            LogLine = Log.Note(SpeechConstants.OutcomeDeny, reason, attemptId),
        };
    }

    private void ClearHold()
    {
        _pendingOutcome = null;
        _held = false;
        _accepted = false;
        _started = false;
        _startRecorded = false;
        _startRpcInFlight = false;
        _dispatchInFlight = false;
        _cancelled = false;
        _cancelStamp = null;
        _itemId = null;
        _attemptId = null;
    }

    private static SpeechAction Stop() => new() { Step = SpeechStep.Stop };

    public static string? LocalGate(SpeechFacts facts)
    {
        if (!facts.BackendUp)
        {
            return SpeechConstants.ReasonBackendDown;
        }

        if (facts.Locked)
        {
            return SpeechConstants.ReasonLocked;
        }

        if (facts.Suspended)
        {
            return SpeechConstants.ReasonSuspended;
        }

        if (facts.TextMode)
        {
            return SpeechConstants.ReasonTextMode;
        }

        if (facts.Capture)
        {
            return SpeechConstants.ReasonCapture;
        }

        if (facts.Turn)
        {
            return SpeechConstants.ReasonTurn;
        }

        if (facts.Playback)
        {
            return SpeechConstants.ReasonPlayback;
        }

        if (facts.Clarify)
        {
            return SpeechConstants.ReasonClarify;
        }

        if (Quiet(facts.LocalNow))
        {
            return SpeechConstants.ReasonQuietHours;
        }

        return null;
    }

    public static bool Quiet(DateTimeOffset local)
    {
        var hour = local.Hour;
        return hour >= SpeechConstants.QuietStartHour || hour < SpeechConstants.QuietEndHour;
    }

    public static bool Idle(SpeechFacts facts)
    {
        DateTimeOffset? latest = null;
        Touch(ref latest, facts.LastComposerInputUtc);
        Touch(ref latest, facts.LastWakeUtc);
        Touch(ref latest, facts.LastPushToTalkUtc);
        Touch(ref latest, facts.LastSubmitUtc);
        Touch(ref latest, facts.LastTurnUtc);
        Touch(ref latest, facts.LastBoutStoppedUtc);
        if (latest is not DateTimeOffset stamp)
        {
            return true;
        }

        return facts.UtcNow - stamp >= TimeSpan.FromSeconds(SpeechConstants.IdleSeconds);
    }

    private static void Touch(ref DateTimeOffset? latest, DateTimeOffset? stamp)
    {
        if (stamp is not DateTimeOffset value)
        {
            return;
        }

        if (latest is null || value > latest)
        {
            latest = value;
        }
    }

    private static int IndexOf(string? phrase, string? source, string? name, string? nameSource)
    {
        if (string.IsNullOrEmpty(phrase))
        {
            return -1;
        }

        var named = !string.IsNullOrEmpty(name) && !string.Equals(nameSource, "someone", StringComparison.Ordinal);
        string[] set;
        if (string.Equals(source, "calendar", StringComparison.Ordinal))
        {
            set = SpeechPhrases.CalendarLines;
        }
        else if (!named)
        {
            set = SpeechPhrases.GmailUnnamed;
        }
        else
        {
            set = SpeechPhrases.GmailNamed;
        }

        for (var i = 0; i < set.Length; i++)
        {
            var candidate = named && !string.Equals(source, "calendar", StringComparison.Ordinal)
                ? set[i].Replace("{name}", name, StringComparison.Ordinal)
                : set[i];
            if (candidate == phrase)
            {
                return i;
            }
        }

        return -1;
    }
}
