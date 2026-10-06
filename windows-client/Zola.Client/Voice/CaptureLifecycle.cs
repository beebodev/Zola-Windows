namespace Zola.Client.Voice;

// P7-VOICEAUTH: pure capture lifecycle — one outstanding generation, proven terminals only — P7-D03

public enum CaptureState
{
    Starting,
    Accepting,
    Cancelled,
    Settled,
}

public enum CaptureKind
{
    Wake,
    Manual,
    FollowUp,
    EchoReopen,
    Clarify,
}

public enum StartDisposition
{
    Began,
    Rejected,
    Deferred,
    SupersededAndDeferred,
}

public enum LifecycleSignal
{
    Listening,
    Transcribing,
    Idle,
    TranscriptText,
    TranscriptStopPhrase,
    TranscriptNoSpeechLimit,
    StartBusy,
    StartError,
    ClientCancel,
    RecoverTimeout,
    StartListeningTimeout,
    PendingExpired,
    SpeakTextPauseResume,
}

public static class CaptureConstants
{
    public const double CaptureSettleTimeoutSeconds = 180;
    public const double CancelSettleTimeoutSeconds = 30;
    public const double LatchIdleTimeoutSeconds = 65;
    public const double StartListeningTimeoutSeconds = 3;
    public const double PendingStartExpirySeconds = 5;
    public const double ClarifyPendingStartExpirySeconds = 15;
    public const double D06HandbackMaxSeconds = 120;

    public const string StatusListening = "listening";
    public const string StatusTranscribing = "transcribing";
    public const string StatusIdle = "idle";

    public const string SignalRecoverTimeout = "recover_timeout";
    public const string SignalStartNoListening = "start_no_listening";
    public const string SignalStartFailed = "start_failed";
    public const string SignalIdle = "idle";
    public const string SignalTranscript = "transcript";
    public const string SignalClientCancel = "client_cancel";
    public const string SignalListening = "listening";

    public const string ReasonBusy = "busy";
    public const string ReasonExpired = "expired";
    public const string ReasonStartNoListening = "start_no_listening";
    public const string ReasonStaleGeneration = "stale_generation";
    public const string ReasonWakeStale = "wake_stale";

    public const string SignalStartAborted = "start_aborted";

    public const string LogLifecycleFormat =
        "capture lifecycle gen={0} kind={1} from={2} to={3} signal={4}";
    public const string LogStartRejectedFormat =
        "capture start_rejected kind={0} reason={1} gen={2}";
    public const string LogStartDeferredFormat =
        "capture start_deferred kind={0} reason={1} gen={2}";
    public const string LogStartSupersedeFormat =
        "capture start_supersede kind={0} reason={1} gen={2}";
    public const string LogStartExpiredFormat =
        "capture start_expired kind={0} reason={1}";
    public const string LogStartDiscardedFormat =
        "capture start_discarded kind={0} reason={1}";
    public const string LogStartAbortedFormat =
        "capture start_aborted gen={0} reason={1}";
    public const string LogStartNoListeningFormat =
        "capture start_no_listening gen={0} kind={1}";
    public const string LogCancelFormat =
        "capture cancel gen={0} kind={1} reason={2}";
    public const string LogStopSentFormat =
        "capture stop_sent gen={0}";
    public const string LogRecoverFormat =
        "capture recover_timeout gen={0}";
    public const string LogLatchRecover =
        "capture latch_recover";
    public const string LogHandbackFollowUpFormat =
        "follow_up_release handback_active_bout rule={0}";
    public const string LogHandbackQuestionFormat =
        "question_release handback_active_bout rule={0}";
    public const string LogHandbackTimeoutFormat =
        "follow_up_release handback_timeout rule={0}";
}

public readonly struct CaptureSnapshot
{
    public CaptureSnapshot(
        long generation,
        CaptureKind kind,
        string? clarifyId,
        CaptureState state,
        DateTimeOffset? windowStart,
        DateTimeOffset? windowStop,
        bool hasOutstanding,
        bool hermesBusyUntilIdle)
    {
        Generation = generation;
        Kind = kind;
        ClarifyId = clarifyId;
        State = state;
        WindowStart = windowStart;
        WindowStop = windowStop;
        HasOutstanding = hasOutstanding;
        HermesBusyUntilIdle = hermesBusyUntilIdle;
    }

    public long Generation { get; }
    public CaptureKind Kind { get; }
    public string? ClarifyId { get; }
    public CaptureState State { get; }
    public DateTimeOffset? WindowStart { get; }
    public DateTimeOffset? WindowStop { get; }
    public bool HasOutstanding { get; }
    public bool HermesBusyUntilIdle { get; }

    public bool IsAccepting => HasOutstanding && State == CaptureState.Accepting;
    public bool IsBusyForStart => HasOutstanding || HermesBusyUntilIdle;
}

public readonly struct PendingStart
{
    // P7-VOICEAUTH: follow-up generation frozen at deferral (P2-D06 stale guard on release) — P7-D03
    public PendingStart(CaptureKind kind, string? clarifyId, DateTimeOffset expiresAt, int? followUpGeneration = null)
    {
        Kind = kind;
        ClarifyId = clarifyId;
        ExpiresAt = expiresAt;
        FollowUpGeneration = followUpGeneration;
    }

    public CaptureKind Kind { get; }
    public string? ClarifyId { get; }
    public DateTimeOffset ExpiresAt { get; }
    public int? FollowUpGeneration { get; }
}

public readonly struct BeginStartResult
{
    public BeginStartResult(
        StartDisposition disposition,
        CaptureSnapshot snapshot,
        string? logLine,
        bool needsHermesStop,
        PendingStart? pending)
    {
        Disposition = disposition;
        Snapshot = snapshot;
        LogLine = logLine;
        NeedsHermesStop = needsHermesStop;
        Pending = pending;
    }

    public StartDisposition Disposition { get; }
    public CaptureSnapshot Snapshot { get; }
    public string? LogLine { get; }
    public bool NeedsHermesStop { get; }
    public PendingStart? Pending { get; }
}

public readonly struct TransitionResult
{
    public TransitionResult(
        CaptureSnapshot snapshot,
        string? logLine,
        bool needsHermesStop,
        bool releasePendingNow,
        PendingStart? pending,
        bool startRejectedAfterNoListening)
    {
        Snapshot = snapshot;
        LogLine = logLine;
        NeedsHermesStop = needsHermesStop;
        ReleasePendingNow = releasePendingNow;
        Pending = pending;
        StartRejectedAfterNoListening = startRejectedAfterNoListening;
    }

    public CaptureSnapshot Snapshot { get; }
    public string? LogLine { get; }
    public bool NeedsHermesStop { get; }
    public bool ReleasePendingNow { get; }
    public PendingStart? Pending { get; }
    public bool StartRejectedAfterNoListening { get; }
}

public sealed class CaptureLifecycle
{
    private long _nextGeneration = 1;
    private long _generation;
    private CaptureKind _kind;
    private string? _clarifyId;
    private CaptureState _state = CaptureState.Settled;
    private bool _hasOutstanding;
    private DateTimeOffset? _windowStart;
    private DateTimeOffset? _windowStop;
    private DateTimeOffset? _startedAt;
    private DateTimeOffset? _listeningDeadline;
    private DateTimeOffset? _settleDeadline;
    private DateTimeOffset? _latchDeadline;
    private PendingStart? _pending;
    // P7-VOICEAUTH: owner follow-up generation for re-defer after start_no_listening — P7-D03
    private int? _ownerFollowUpGeneration;
    // P7-VOICEAUTH: true only after MarkStartSent (voice.record start in flight or done) — P7-D03
    private bool _startSent;
    // P7-VOICEAUTH: operability latch — set on listening, cleared on idle/recover/latch timeout — P7-D03
    private bool _hermesBusyUntilIdle;
    private bool _noListeningRejectWakeOrManual;

    public CaptureSnapshot Snapshot()
    {
        return new CaptureSnapshot(
            _generation,
            _kind,
            _clarifyId,
            _hasOutstanding ? _state : CaptureState.Settled,
            _windowStart,
            _windowStop,
            _hasOutstanding,
            _hermesBusyUntilIdle);
    }

    public PendingStart? Pending => _pending;

    public bool HermesBusyUntilIdle => _hermesBusyUntilIdle;

    public BeginStartResult BeginStart(
        CaptureKind kind,
        string? clarifyId,
        DateTimeOffset now,
        int? followUpGeneration = null)
    {
        if (kind == CaptureKind.Clarify && string.IsNullOrEmpty(clarifyId))
        {
            return Reject(kind, CaptureConstants.ReasonBusy, needsStop: false);
        }

        // Busy when an outstanding capture exists or the Hermes latch is still held.
        if (_hasOutstanding || _hermesBusyUntilIdle)
        {
            return HandleStartWhileBusy(kind, clarifyId, now, followUpGeneration);
        }

        return BeginFresh(
            kind,
            clarifyId,
            now,
            StartDisposition.Began,
            log: null,
            needsStop: false,
            followUpGeneration);
    }

    // P7-VOICEAUTH: drop a stale deferred start (revalidation failure or cancelled window) — P7-D03
    public TransitionResult DiscardPending(string reason)
    {
        if (_pending is not { } pending)
        {
            return NoOp();
        }

        _pending = null;
        var log = string.Format(
            CaptureConstants.LogStartDiscardedFormat,
            FormatKind(pending.Kind, pending.ClarifyId),
            reason);
        return new TransitionResult(Snapshot(), log, false, false, null, false);
    }

    // P7-VOICEAUTH: release/normal Began result is ready for voice.record (no second BeginStart) — P7-D03
    public bool CanSendRecordStart(BeginStartResult begin)
    {
        return begin.Disposition == StartDisposition.Began
            && _hasOutstanding
            && _state == CaptureState.Starting
            && !_startSent
            && begin.Snapshot.Generation == _generation
            && begin.Snapshot.HasOutstanding
            && begin.Snapshot.State == CaptureState.Starting;
    }

    // P7-VOICEAUTH: mark immediately before voice.record start RPC — P7-D03
    public TransitionResult MarkStartSent(long generation)
    {
        if (!_hasOutstanding
            || _state != CaptureState.Starting
            || _generation != generation
            || _startSent)
        {
            return FailClosedIgnore();
        }

        _startSent = true;
        return NoOp();
    }

    // P7-VOICEAUTH: Starting and not sent → Settled immediately (no stop, no latch) — P7-D03
    public TransitionResult AbortUnsentStart(long generation, string reason, DateTimeOffset now)
    {
        if (!_hasOutstanding
            || _state != CaptureState.Starting
            || _generation != generation
            || _startSent)
        {
            return FailClosedIgnore();
        }

        return SettleUnsentStart(reason, now);
    }

    public TransitionResult ApplyStatus(string status, DateTimeOffset now)
    {
        if (string.Equals(status, CaptureConstants.StatusListening, StringComparison.Ordinal))
        {
            return ApplyListening(now);
        }

        if (string.Equals(status, CaptureConstants.StatusTranscribing, StringComparison.Ordinal))
        {
            return NoOp();
        }

        if (string.Equals(status, CaptureConstants.StatusIdle, StringComparison.Ordinal))
        {
            return ApplyIdle(now);
        }

        return FailClosedIgnore();
    }

    public TransitionResult ApplyTranscript(LifecycleSignal signal, DateTimeOffset now)
    {
        if (signal != LifecycleSignal.TranscriptText
            && signal != LifecycleSignal.TranscriptStopPhrase
            && signal != LifecycleSignal.TranscriptNoSpeechLimit)
        {
            return FailClosedIgnore();
        }

        if (!_hasOutstanding)
        {
            return NoOp();
        }

        if (_state == CaptureState.Starting)
        {
            // Impossible pair: transcript before listening — fail-closed to Settled; latch unchanged.
            return ForceSettle(CaptureConstants.SignalTranscript, now, needsStop: false);
        }

        if (_state == CaptureState.Accepting || _state == CaptureState.Cancelled)
        {
            // Settle ownership; latch stays until idle so deferred starts are not Begun early.
            return ForceSettle(CaptureConstants.SignalTranscript, now, needsStop: false);
        }

        return NoOp();
    }

    public TransitionResult Cancel(string reason, DateTimeOffset now)
    {
        // Pending FollowUp/EchoReopen belongs to the cancelled window; Clarify is kept for broker revalidation.
        var discardLog = DiscardFollowUpOrEchoPending(reason);

        if (!_hasOutstanding || _state == CaptureState.Settled)
        {
            return new TransitionResult(Snapshot(), discardLog, false, false, _pending, false);
        }

        if (_state == CaptureState.Cancelled)
        {
            var cancelOnly = string.Format(CaptureConstants.LogCancelFormat, _generation, FormatKind(), reason);
            var cancelledLog = string.IsNullOrEmpty(discardLog) ? cancelOnly : discardLog + " | " + cancelOnly;
            return new TransitionResult(
                Snapshot(),
                cancelledLog,
                true,
                false,
                _pending,
                false);
        }

        // Starting without voice.record start → settle immediately (no stop, no 30s Cancelled wait).
        if (_state == CaptureState.Starting && !_startSent)
        {
            var aborted = SettleUnsentStart(reason, now);
            var log = string.IsNullOrEmpty(discardLog)
                ? aborted.LogLine
                : discardLog + " | " + aborted.LogLine;
            return new TransitionResult(aborted.Snapshot, log, false, false, _pending, false);
        }

        var from = _state;
        _state = CaptureState.Cancelled;
        _listeningDeadline = null;
        ArmCancelSettleDeadline(now);
        var cancelLog = string.Format(CaptureConstants.LogLifecycleFormat, _generation, FormatKind(), from, _state, CaptureConstants.SignalClientCancel)
            + " | "
            + string.Format(CaptureConstants.LogCancelFormat, _generation, FormatKind(), reason);
        if (!string.IsNullOrEmpty(discardLog))
        {
            cancelLog = discardLog + " | " + cancelLog;
        }

        return new TransitionResult(Snapshot(), cancelLog, true, false, _pending, false);
    }

    public TransitionResult NoteStartRpcFailed(bool busy, DateTimeOffset now)
    {
        if (!_hasOutstanding || _state != CaptureState.Starting)
        {
            return FailClosedIgnore();
        }

        _ = busy;
        return ForceSettle(CaptureConstants.SignalStartFailed, now, needsStop: false);
    }

    // P7-VOICEAUTH: speak_text cancels/restarts the recorder with no status events; stay Accepting — P7-D03
    public TransitionResult NoteSpeakTextPauseResume(DateTimeOffset now)
    {
        _ = now;
        if (!_hasOutstanding || _state != CaptureState.Accepting)
        {
            return FailClosedIgnore();
        }

        return NoOp();
    }

    public TransitionResult Tick(DateTimeOffset now)
    {
        // Do not expire a deferred start while the latch is held — it is waiting for idle/latch_recover.
        if (!_hermesBusyUntilIdle && _pending is { } pending && now >= pending.ExpiresAt)
        {
            _pending = null;
            var expiredLog = string.Format(
                CaptureConstants.LogStartExpiredFormat,
                FormatKind(pending.Kind, pending.ClarifyId),
                CaptureConstants.ReasonExpired);
            return new TransitionResult(Snapshot(), expiredLog, false, false, null, false);
        }

        if (_hasOutstanding
            && _state == CaptureState.Starting
            && _listeningDeadline is { } listenBy
            && now >= listenBy)
        {
            return ApplyStartListeningTimeout(now);
        }

        if (_hasOutstanding
            && _state != CaptureState.Settled
            && _settleDeadline is { } settleBy
            && now >= settleBy)
        {
            var from = _state;
            _state = CaptureState.Settled;
            _hasOutstanding = false;
            _windowStop ??= now;
            _listeningDeadline = null;
            _settleDeadline = null;
            // recover_timeout clears the latch (backstop); next Accepting still needs listening.
            _hermesBusyUntilIdle = false;
            _latchDeadline = null;
            var log = string.Format(CaptureConstants.LogRecoverFormat, _generation)
                + " | "
                + string.Format(
                    CaptureConstants.LogLifecycleFormat,
                    _generation,
                    FormatKind(),
                    from,
                    CaptureState.Settled,
                    CaptureConstants.SignalRecoverTimeout);
            return new TransitionResult(Snapshot(), log, true, _pending is not null, _pending, false);
        }

        // Latch held with no outstanding: lost idle must not deafen forever.
        if (!_hasOutstanding
            && _hermesBusyUntilIdle
            && _latchDeadline is { } latchBy
            && now >= latchBy)
        {
            _hermesBusyUntilIdle = false;
            _latchDeadline = null;
            return new TransitionResult(
                Snapshot(),
                CaptureConstants.LogLatchRecover,
                false,
                _pending is not null,
                _pending,
                false);
        }

        return NoOp();
    }

    public BeginStartResult TryReleasePending(DateTimeOffset now)
    {
        if (_hermesBusyUntilIdle || _hasOutstanding)
        {
            return new BeginStartResult(StartDisposition.Rejected, Snapshot(), null, false, _pending);
        }

        if (_pending is not { } pending)
        {
            return new BeginStartResult(StartDisposition.Rejected, Snapshot(), null, false, null);
        }

        if (now >= pending.ExpiresAt)
        {
            _pending = null;
            var expired = string.Format(
                CaptureConstants.LogStartExpiredFormat,
                FormatKind(pending.Kind, pending.ClarifyId),
                CaptureConstants.ReasonExpired);
            return new BeginStartResult(StartDisposition.Rejected, Snapshot(), expired, false, null);
        }

        _pending = null;
        return BeginFresh(
            pending.Kind,
            pending.ClarifyId,
            now,
            StartDisposition.Began,
            log: null,
            needsStop: false,
            pending.FollowUpGeneration);
    }

    private BeginStartResult HandleStartWhileBusy(
        CaptureKind kind,
        string? clarifyId,
        DateTimeOffset now,
        int? followUpGeneration)
    {
        if (kind == CaptureKind.Wake || kind == CaptureKind.Manual)
        {
            return Reject(kind, CaptureConstants.ReasonBusy, needsStop: false);
        }

        if (kind == CaptureKind.Clarify)
        {
            // Cancel first only when a capture is outstanding; latch-only → just defer.
            if (_hasOutstanding)
            {
                var cancel = Cancel(CaptureConstants.ReasonBusy, now);
                Defer(kind, clarifyId, now, CaptureConstants.ClarifyPendingStartExpirySeconds, followUpGeneration);
                var log = string.Format(
                        CaptureConstants.LogStartSupersedeFormat,
                        FormatKind(kind, clarifyId),
                        CaptureConstants.ReasonBusy,
                        _generation)
                    + " | "
                    + string.Format(
                        CaptureConstants.LogStartDeferredFormat,
                        FormatKind(kind, clarifyId),
                        CaptureConstants.ReasonBusy,
                        _generation);
                if (!string.IsNullOrEmpty(cancel.LogLine))
                {
                    log = cancel.LogLine + " | " + log;
                }

                return new BeginStartResult(
                    StartDisposition.SupersededAndDeferred,
                    Snapshot(),
                    log,
                    cancel.NeedsHermesStop,
                    _pending);
            }

            Defer(kind, clarifyId, now, CaptureConstants.ClarifyPendingStartExpirySeconds, followUpGeneration);
            var deferredOnly = string.Format(
                CaptureConstants.LogStartDeferredFormat,
                FormatKind(kind, clarifyId),
                CaptureConstants.ReasonBusy,
                _generation);
            return new BeginStartResult(StartDisposition.Deferred, Snapshot(), deferredOnly, false, _pending);
        }

        // FollowUp / EchoReopen: defer (one pending; newer replaces).
        Defer(kind, clarifyId, now, CaptureConstants.PendingStartExpirySeconds, followUpGeneration);
        var deferredLog = string.Format(
            CaptureConstants.LogStartDeferredFormat,
            FormatKind(kind, clarifyId),
            CaptureConstants.ReasonBusy,
            _generation);
        return new BeginStartResult(StartDisposition.Deferred, Snapshot(), deferredLog, false, _pending);
    }

    private BeginStartResult BeginFresh(
        CaptureKind kind,
        string? clarifyId,
        DateTimeOffset now,
        StartDisposition disposition,
        string? log,
        bool needsStop,
        int? followUpGeneration)
    {
        _generation = _nextGeneration++;
        _kind = kind;
        _clarifyId = kind == CaptureKind.Clarify ? clarifyId : null;
        _state = CaptureState.Starting;
        _hasOutstanding = true;
        _windowStart = now;
        _windowStop = null;
        _startedAt = now;
        _listeningDeadline = now.AddSeconds(CaptureConstants.StartListeningTimeoutSeconds);
        ArmSettleDeadline(now);
        _noListeningRejectWakeOrManual = false;
        _startSent = false;
        _ownerFollowUpGeneration = kind is CaptureKind.FollowUp or CaptureKind.EchoReopen or CaptureKind.Clarify
            ? followUpGeneration
            : null;
        var lifecycleLog = string.Format(
            CaptureConstants.LogLifecycleFormat,
            _generation,
            FormatKind(),
            CaptureState.Settled,
            CaptureState.Starting,
            "start");
        var combined = string.IsNullOrEmpty(log) ? lifecycleLog : log + " | " + lifecycleLog;
        return new BeginStartResult(disposition, Snapshot(), combined, needsStop, _pending);
    }

    private BeginStartResult Reject(CaptureKind kind, string reason, bool needsStop)
    {
        var log = string.Format(
            CaptureConstants.LogStartRejectedFormat,
            FormatKind(kind, null),
            reason,
            _hasOutstanding ? _generation : 0);
        return new BeginStartResult(StartDisposition.Rejected, Snapshot(), log, needsStop, _pending);
    }

    private void Defer(
        CaptureKind kind,
        string? clarifyId,
        DateTimeOffset now,
        double expirySeconds,
        int? followUpGeneration = null)
    {
        var gen = followUpGeneration
            ?? (kind is CaptureKind.FollowUp or CaptureKind.EchoReopen or CaptureKind.Clarify
                ? _ownerFollowUpGeneration
                : null);
        _pending = new PendingStart(kind, clarifyId, now.AddSeconds(expirySeconds), gen);
    }

    private string? DiscardFollowUpOrEchoPending(string reason)
    {
        if (_pending is not { } pending)
        {
            return null;
        }

        if (pending.Kind is not (CaptureKind.FollowUp or CaptureKind.EchoReopen))
        {
            return null;
        }

        return DiscardPending(reason).LogLine;
    }

    private TransitionResult ApplyListening(DateTimeOffset now)
    {
        if (!_hasOutstanding || _state != CaptureState.Starting)
        {
            return FailClosedIgnore();
        }

        var from = _state;
        _state = CaptureState.Accepting;
        _listeningDeadline = null;
        _windowStart ??= now;
        _hermesBusyUntilIdle = true;
        _latchDeadline = null;
        ArmSettleDeadline(now);
        var log = string.Format(
            CaptureConstants.LogLifecycleFormat,
            _generation,
            FormatKind(),
            from,
            _state,
            CaptureConstants.SignalListening);
        return new TransitionResult(Snapshot(), log, false, false, _pending, false);
    }

    private TransitionResult ApplyIdle(DateTimeOffset now)
    {
        // Any idle clears the operability latch (including late idle after latch_recover).
        _hermesBusyUntilIdle = false;
        _latchDeadline = null;

        if (_hasOutstanding && _state == CaptureState.Starting)
        {
            // Stale idle from the previous loop; failed starts report via RPC, not idle.
            // Stay Starting; keep waiting for listening or StartListeningTimeoutSeconds.
            var reject = ConsumeNoListeningReject();
            return new TransitionResult(Snapshot(), null, false, false, _pending, reject);
        }

        if (_hasOutstanding && (_state == CaptureState.Accepting || _state == CaptureState.Cancelled))
        {
            var result = ForceSettle(CaptureConstants.SignalIdle, now, needsStop: false);
            var reject = ConsumeNoListeningReject();
            return new TransitionResult(
                result.Snapshot,
                result.LogLine,
                result.NeedsHermesStop,
                !reject && _pending is not null,
                _pending,
                reject);
        }

        // No outstanding: latch cleared; release any deferred start (wiring revalidates).
        var rejectOnly = ConsumeNoListeningReject();
        return new TransitionResult(
            Snapshot(),
            null,
            false,
            !rejectOnly && _pending is not null,
            _pending,
            rejectOnly);
    }

    private TransitionResult ApplyStartListeningTimeout(DateTimeOffset now)
    {
        var kind = _kind;
        var clarifyId = _clarifyId;
        var logNo = string.Format(CaptureConstants.LogStartNoListeningFormat, _generation, FormatKind());
        var cancel = Cancel(CaptureConstants.ReasonStartNoListening, now);

        if (kind == CaptureKind.Wake || kind == CaptureKind.Manual)
        {
            _noListeningRejectWakeOrManual = true;
            _pending = null;
        }
        else
        {
            _noListeningRejectWakeOrManual = false;
            var expiry = kind == CaptureKind.Clarify
                ? CaptureConstants.ClarifyPendingStartExpirySeconds
                : CaptureConstants.PendingStartExpirySeconds;
            if (_pending is null
                || _pending.Value.Kind != kind
                || !string.Equals(_pending.Value.ClarifyId, clarifyId, StringComparison.Ordinal))
            {
                Defer(kind, clarifyId, now, expiry, _ownerFollowUpGeneration);
            }
        }

        var log = logNo + (string.IsNullOrEmpty(cancel.LogLine) ? "" : " | " + cancel.LogLine);
        return new TransitionResult(Snapshot(), log, true, false, _pending, false);
    }

    private bool ConsumeNoListeningReject()
    {
        var reject = _noListeningRejectWakeOrManual;
        _noListeningRejectWakeOrManual = false;
        return reject;
    }

    private TransitionResult SettleUnsentStart(string reason, DateTimeOffset now)
    {
        var from = _state;
        var gen = _generation;
        _state = CaptureState.Settled;
        _hasOutstanding = false;
        _windowStop = now;
        _listeningDeadline = null;
        _settleDeadline = null;
        _latchDeadline = null;
        _startSent = false;
        // Never arm the latch — voice.record start was never sent.
        var log = string.Format(
                CaptureConstants.LogLifecycleFormat,
                gen,
                FormatKind(),
                from,
                CaptureState.Settled,
                CaptureConstants.SignalStartAborted)
            + " | "
            + string.Format(CaptureConstants.LogStartAbortedFormat, gen, reason);
        return new TransitionResult(Snapshot(), log, false, false, _pending, false);
    }

    private TransitionResult ForceSettle(string signal, DateTimeOffset now, bool needsStop)
    {
        if (!_hasOutstanding)
        {
            return NoOp();
        }

        var from = _state;
        _state = CaptureState.Settled;
        _hasOutstanding = false;
        _windowStop = now;
        _listeningDeadline = null;
        _settleDeadline = null;
        _startSent = false;
        if (_hermesBusyUntilIdle)
        {
            ArmLatchDeadline(now);
        }
        else
        {
            _latchDeadline = null;
        }

        var log = string.Format(
            CaptureConstants.LogLifecycleFormat,
            _generation,
            FormatKind(),
            from,
            CaptureState.Settled,
            signal);
        return new TransitionResult(Snapshot(), log, needsStop, false, _pending, false);
    }

    private TransitionResult NoOp()
        => new TransitionResult(Snapshot(), null, false, false, _pending, false);

    private TransitionResult FailClosedIgnore()
        => new TransitionResult(Snapshot(), null, false, false, _pending, false);

    private void ArmSettleDeadline(DateTimeOffset now)
    {
        _settleDeadline = now.AddSeconds(CaptureConstants.CaptureSettleTimeoutSeconds);
    }

    private void ArmCancelSettleDeadline(DateTimeOffset now)
    {
        _settleDeadline = now.AddSeconds(CaptureConstants.CancelSettleTimeoutSeconds);
    }

    private void ArmLatchDeadline(DateTimeOffset now)
    {
        _latchDeadline = now.AddSeconds(CaptureConstants.LatchIdleTimeoutSeconds);
    }

    private string FormatKind() => FormatKind(_kind, _clarifyId);

    private static string FormatKind(CaptureKind kind, string? clarifyId)
    {
        return kind == CaptureKind.Clarify && !string.IsNullOrEmpty(clarifyId)
            ? "Clarify(" + clarifyId + ")"
            : kind.ToString();
    }
}
