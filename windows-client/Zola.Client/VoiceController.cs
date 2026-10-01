using System.Diagnostics;
using System.Text.RegularExpressions;

namespace Zola.Client;

// P2-VOICE: the client drives Hermes voice over the open /api/ws and never opens a microphone — P2-D01
sealed class VoiceController
{
    // P2-VOICE: RPC methods, actions, states, and payload fields are named constants — P2-D01
    public const string ModeVoice = "voice";
    public const string ModeText = "text";
    public const string StateListening = "listening";
    public const string StateTranscribing = "transcribing";
    public const string StateIdle = "idle";

    private const string MethodToggle = "voice.toggle";
    private const string MethodRecord = "voice.record";
    private const string ParamAction = "action";
    private const string ParamSessionId = "session_id";
    private const string ActionStatus = "status";
    private const string ActionOn = "on";
    private const string ActionOff = "off";
    // P2-SPEAK: tts flips spoken replies and is never sent blind — P2-D03
    private const string ActionTts = "tts";
    private const string ActionStart = "start";
    private const string ActionStop = "stop";
    private const string RecordBusy = "busy";
    private const string ReasonWakeOwned = "wake_owned";
    private const string NoticeNoSpeech = "No speech heard";
    private const string NoticeInterrupted = "Voice interrupted.";
    private const string NoticeBusy = "The microphone is busy.";
    private const string NoticeWakeOwned = "The wake word owns the microphone.";
    // P2-SPEAK: a tts flip that stays false is shown and logged, then left alone — P2-D03
    private const string NoticeSpokenRepliesOff = "Spoken replies did not turn on.";
    // P2-SPEAK: the clock does not run when tts is false or unknown — P2-D06
    private const string NoticeSpokenRepliesUnavailable = "Spoken replies unavailable";
    // P2-SPEAK: three self-trips in a row pause Voice so a bleed loop cannot continue — P2-D12
    private const string NoticeVoicePaused =
        "Voice paused: Zola may be hearing herself — check that the lid is open and review mic/speaker setup.";

    // P2-SPEAK: clock is a fixed startup cost plus a small per-sentence cost so long replies stay within ~3 s — P2-D06
    private const double EstimatedWordsPerSecond = 2.5;
    internal const double FirstSentenceLatencySeconds = 3.3;
    private const double PerSentenceOverheadSeconds = 0.5;
    // P4-VOICE: cover worst estimatedEnd lead (4.33 s on six-pack); fail late not early — P4-D22
    private const double FollowUpMarginSeconds = 5.0;
    private const double FollowUpMaxDelaySeconds = 90;
    private const double MaxEstimatedSpeechSeconds = 300;
    // P4-VOICE: bout-startup safety window; ≥1.5× worst Edge first-audio (~3.49 s → 5.3) — P4-D22
    private const double StartupWindowSeconds = 5.3;
    // P4-ASK: no-bout startup window before estimate fallback — P4-D13
    private const double QuestionBoutStartupWindowSeconds = StartupWindowSeconds;
    // P4-FEEDBACK: reply follow-up release — quiet after natural bout; startup from message.complete — P4-D18
    // P4-FEEDBACK: 0.5 s (was 1.2); bout stop already ~0.49 s debounce; bridged sentence gaps max 441 ms — P4-D18 amendment 2 / Probe2
    private const double FollowUpPostBoutQuietSeconds = 0.5;
    private const double ReplyBoutStartupWindowSeconds = StartupWindowSeconds;
    private const string LogFollowUpReleasePrefix = "follow_up_release rule=";
    private const string FollowUpRuleMonitor = "monitor";
    private const string FollowUpRuleNoBoutEstimate = "no_bout_estimate";
    private const string FollowUpRuleForcedEstimate = "forced_estimate";
    private const string FollowUpRuleMonitorUnavailable = "monitor_unavailable";
    private const string MethodTts = "voice.tts";
    private const string ParamText = "text";
    private const string SpokenBatchMoreSuffix = " …and there are more on screen.";
    private const string LogQuestionSpokenPrefix = "question_spoken id=";
    private const string LogQuestionReleasePrefix = "question_release rule=";
    private const string LogQuestionAbandonedPrefix = "question_abandoned id=";
    private const string LogQuestionRefusePrefix = "question_refuse reason=";
    private const string LogQuestionCaptureSkipPrefix = "question_capture_skipped id=";
    private const string QuestionRuleMonitor = "monitor";
    private const string QuestionRuleNoBoutEstimate = "no_bout_estimate";
    private const string QuestionRuleMonitorUnavailable = "monitor_unavailable";
    private const string QuestionRuleForcedEstimate = "forced_release_estimate";
    private const string AbandonReasonNewerClarify = "newer_clarify";
    private const string AbandonReasonRequestClosed = "request_closed";
    private const string AbandonReasonSessionChange = "session_change";
    private const string AbandonReasonUnreachable = "unreachable";
    private const string AbandonReasonTextMode = "text_mode";
    private const string AbandonReasonSpeechOff = "speech_off";
    private const string AbandonReasonVoiceGated = "voice_gated";
    private const string AbandonReasonTtsFailed = "tts_failed";
    private const string CaptureSkipTokenStale = "token_stale";
    private const string CaptureSkipNotOpen = "not_open";
    private const string CaptureSkipWrongSession = "wrong_session";
    private const string CaptureSkipGated = "gated";
    private const string CaptureSkipNotVoice = "not_voice";
    private const string CaptureSkipSpeechOff = "speech_off";
    private const string QuestionRefuseGated = "gated";
    private const string QuestionRefuseTextMode = "text_mode";
    private const string QuestionRefuseSpeechOff = "speech_off";
    private const string QuestionRefuseEmpty = "empty_text";
    // P3-STATE: unused bag-of-words echo constants are removed; the live rule is P2-D14 — P3-D15
    private const int EchoLookbackWords = 20;
    private const int EchoReopenLimit = 3;
    private const double EchoReopenDelaySeconds = 0.5;
    // P2-WAKE: drop a follow-up only when a ≥3-word in-order run is ≥0.60 of it and ends near her last spoken words — P2-D14
    private const int EchoMinContiguousWords = 3;
    private const double EchoAnchoredRatio = 0.60;
    private const int EchoEndSlackWords = 3;
    // P2-WAKE: slack grows with a long transcript so a late STT tail still anchors — P2-D14
    private const double EchoEndSlackRatio = 0.25;
    // P2-WAKE: one unmatched word (hers or STT) may sit inside the run; two breaks it — P2-D14
    private const int EchoMaxGapWords = 1;
    // P2-WAKE: SpokenDigitWeight is max(SpokenDigitWeightFloor, digitCount) on the clock only — P2-D12
    private const int SpokenDigitWeightFloor = 1;
    private const int SpokenAbbrevWords = 2;
    // P2-WAKE: PDT/NFL/USA are spelled out on the clock; haystack still stores one token — P2-D12
    private const int SpokenAcronymPerLetter = 1;
    private const int SpokenAcronymMinLetters = 2;
    private const int SpokenAcronymMaxLetters = 5;
    private const string NoticeIgnoredEcho = "Ignored: that sounded like Zola's own voice.";
    // P4-ASK: timeline tag when a late bound clarify answer is dropped — P4-D14
    private const string LogLateAnswerDroppedPrefix = "late_answer_dropped id=";
    // P2-SPEAK: three consecutive voice.interrupted trips with no complete in between pause Voice — P2-D12
    private const int SelfInterruptLimit = 3;
    // P2-SPEAK: one append-only line per spoken turn for Phase 5 measurement — P2-D06
    // P3-STATE: display-state.log shares this folder — P3-D03
    internal const string TimelineClientFolder = "ZolaClient";
    internal const string TimelineLogFolder = "logs";
    private const string TimelineLogFile = "voice-timeline.log";
    // P4-LOCK: gate facts update synchronously; close/open work is queued after — P4-D01 / P4-D02
    private const string GateFactLineFormat = "gate fact: locked={0} suspended={1}";
    private const string GateFactTrue = "true";
    private const string GateFactFalse = "false";
    private const string GateClosedStarting = "gate closed: starting";
    private const string GateClosedDone = "gate closed: done";
    private const string GateClosedFailed = "gate closed: failed — holding closed";
    private const string GateOpenedStarting = "gate opened: starting";
    private const string GateOpenedDone = "gate opened: done";
    private const string GateOpenedErrorPrefix = "gate opened: error ";
    private const string GateOpenedSkippedText = "gate opened: skipped — snapshot text mode";
    private const string GateSnapshotFormat = "gate snapshot: mode={0} speech={1} wakeArmed={2}";
    private const string GateStepCancelFollowUp = "gate step: cancel follow-up/echo";
    private const string GateStepRecordStopFormat = "gate step: voice.record stop ok={0} status={1} error={2}";
    private const string GateStepRecordStopSkipped = "gate step: voice.record stop skipped — no capture";
    private const string GateStepToggleOffFormat = "gate step: voice.toggle off ok={0} enabled={1} tts={2} error={3}";
    private const string GateStepWakeStop = "gate step: wake.stop via DisarmWakeAsync";
    private const string GateStepWakeStopRetry = "gate step: wake.stop retry — listening still true";
    private const string GateStepWakeStatusFormat = "gate step: wake.status listening={0} owned_by_caller={1}";
    private const string GateStepToggleOnFormat = "gate step: voice.toggle on ok={0} enabled={1} error={2}";
    private const string GateStepToggleStatusFormat = "gate step: voice.toggle status ok={0} enabled={1} tts={2} error={3}";
    private const string GateStepToggleTtsFormat = "gate step: voice.toggle tts ok={0} tts={1} error={2}";
    private const string GateStepToggleTtsSkipped = "gate step: voice.toggle tts skipped — snapshot speech off or already on";
    private const string GateStepWakeStart = "gate step: wake re-arm via ArmWakeAsync";
    private const string GateOpenAborted = "gate open aborted: re-gated";
    private const string GateSnapshotRetained = "gate snapshot: retained (same episode)";
    private const string GateSnapshotCleared = "gate snapshot: cleared";
    private const string GateRefusePrefix = "gate refuse: ";
    private const string GateRefuseWakeDetected = "wake.detected";
    private const string GateRefuseCaptureStart = "capture-start";
    private const string GateRefuseFollowUp = "follow-up";
    private const string GateRefuseEchoReopen = "echo-reopen";
    private const string GateRefuseWakeResume = "wake.resume";
    private const string GateRefuseWakeReconcileResume = "wake-reconcile-resume";
    private const string GateRefuseSyncVoiceWake = "sync-voice-wake";
    private const string GateRefuseArmWake = "wake.start";
    private const string GateRefuseTranscript = "transcript";
    private const string GateRefuseVoiceSubmit = "voice-submit";
    internal const string GateRefuseVoiceSubmitReason = GateRefuseVoiceSubmit;
    private const string GateRefuseResyncStop = "resync-after-stop";
    private const string GateCancelReason = "system-gate";
    private const string GateBoolTrue = "true";
    private const string GateBoolFalse = "false";
    // P4-FEEDBACK: Stop speaking through the serialized gate worker — P4-FB-STOP
    private const string StopSpeakingRequested = "stop_speaking requested";
    private const string StopSpeakingDone = "stop_speaking done";
    private const string StopSpeakingRefusedPrefix = "stop_speaking refused reason=";
    private const string StopSpeakingRefuseGated = "gated";
    private const string StopSpeakingRefuseNotSpeaking = "not_speaking";
    private const string StopSpeakingRefuseQuestionSpeaking = "question_speaking";
    private const string StopSpeakingRefuseReGated = "re-gated";
    private const string StopSpeakingStepPrefix = "stop_speaking step=";
    private const string StopSpeakingCancelReason = "stop-speaking";
    // P4-FEEDBACK: every voice.transcript line (length + flags + window; never text) — P4-D18
    private const string TranscriptLogFormat =
        "transcript len={0} filtered={1} stop={2} nospeech={3} bound={4} capture_start={5} capture_stop={6} duration_s={7}";
    private const string TranscriptBoundNone = "none";

    // P2-WAKE: wake RPC names, params, reasons, and timings are named constants — P2-D04
    private const string MethodWakeStart = "wake.start";
    private const string MethodWakeStop = "wake.stop";
    private const string MethodWakePause = "wake.pause";
    private const string MethodWakeResume = "wake.resume";
    private const string MethodWakeStatus = "wake.status";
    private const string ParamSurface = "surface";
    private const string SurfaceGui = "gui";
    private const string ReasonOwned = "owned";
    private const string ReasonUnavailable = "unavailable";
    private const string ReasonDisabled = "disabled";
    private const string ReasonDisabledForSurface = "disabled_for_surface";
    private const int WakeOwnedRetryCount = 3;
    private const int WakeOwnedRetryDelayMs = 1000;
    private const int WakeStartTimeoutSeconds = 60;
    private const string NoticeSettingUpWake = "Setting up wake word…";
    // P2-WAKE: after wake.start resolves, the status line returns to the ready state — P2-D08
    private const string NoticeSessionReady = "Session ready.";
    private const string NoticeWakeHeld = "Wake word held by another connection";
    private const string NoticeWakeMissed = "Didn't catch that — say 'Hey Zola' again";
    private const string NoticeStaleWake = "stale wake reply";
    private const string WakeModelRelativePath = @"cache\wakewords\sherpa-onnx-kws-zipformer-gigaspeech-3.3M-2024-01-01\tokens.txt";

    private static readonly Regex FenceBlocks = new("```[\\s\\S]*?```", RegexOptions.Compiled);
    private static readonly Regex MarkdownMarks = new(@"[#*_`>\[\]\(\)]+", RegexOptions.Compiled);
    // P2-WAKE: clock-only a.m./p.m. match; echo normalization is unchanged — P2-D12
    private static readonly Regex SpokenTimeAbbrev = new(@"^[ap]\.?m\.?$", RegexOptions.Compiled | RegexOptions.IgnoreCase);
    // P2-WAKE: leftover list bullets after punctuation strip; numbered markers fall out with the digit drop — P2-D12
    private static readonly Regex EchoListMarker = new(@"^[-*•]+$", RegexOptions.Compiled);

    private readonly ChatSocket _chat;
    private readonly object _clockGate = new();
    private Timer? _followUpTimer;
    private int _followUpGeneration;
    private int _connectionGeneration;
    private int _selfInterruptCount;
    private bool? _ttsOn;
    private bool _followUpArmed;
    private bool _followUpCaptureStarted;
    private bool _followUpTranscriptSeen;
    // P2-WAKE: a late STT result after follow-up idle must still be echo-checked — P2-D12
    private bool _followUpEchoPending;
    private int _echoIgnoreCount;
    // P4-ASK: capture opened for a clarify carries its srq-* until the ending transcript — P4-D14
    private string? _pendingClarifyCaptureId;
    private string? _activeClarifyCaptureId;
    // P4-ASK: after Cancel/interrupt, keep the closed id so a late transcript drops (never prompt.submit) — P4-D14
    private string? _closedClarifyCaptureId;
    // P4-ASK: one pending-question token (id + generation) for speak → release → capture — P4-D13
    private string? _pendingQuestionId;
    private int _pendingQuestionGeneration;
    private bool _questionSpeaking;
    private bool _questionBoutArmed;
    private bool _questionBoutStarted;
    private bool _questionBoutActive;
    private TaskCompletionSource<bool>? _questionBoutStartedTcs;
    private TaskCompletionSource<bool>? _questionBoutStoppedTcs;
    private Func<bool>? _playbackMonitorAvailable;
    private Func<bool>? _playbackBoutActive;
    private Func<string, bool>? _clarifyCaptureStillValid;
    private string _accumulatedReply = "";
    // P2-WAKE: echo compares against recent spoken words across turns, not only the latest reply — P2-D12
    private string _echoHaystack = "";
    private int _countedWords;
    private int _countedSentences;
    private DateTimeOffset _turnStartedAt;
    private DateTimeOffset _estimatedSpeechEnd;
    private DateTimeOffset _turnCompletedAt;
    private double _timerDelaySeconds;
    private string _cancelReason = "";
    // P2-WAKE: a wake-started capture that never reaches listening must resume the detector — P2-D12
    private bool _wakeCapturePending;
    // P4-LOCK: applied hold stays true from first gated fact until open completes — P4-D02
    private bool _gateHolding;
    private bool _gateCloseCompleted;
    private bool _gateSnapshotTaken;
    private int _gateEpoch;
    private readonly SemaphoreSlim _gateSequenceLock = new(1, 1);
    private string _gateSnapshotMode = ModeVoice;
    private bool _gateSnapshotSpeechEnabled;
    private bool _gateSnapshotWakeArmed;
    // P4-FEEDBACK: Stop speaking queued into the same serialized worker as the gate — P4-FB-STOP
    private int _stopSpeakingQueued;
    private int _stopSpeakingDone;
    // P4-FEEDBACK: Stop silenced this turn's estimate; deltas must not re-arm Speaking/follow-up — P4-FB-STOP
    private bool _speechStoppedThisTurn;
    // P2-WAKE / P4-FEEDBACK: single-flight wake reconcile + pending coalesce — P2-D12 / P4-FB-STOP
    private int _wakeReconcileBusy;
    private int _wakeReconcilePending;
    private string _wakeReconcileReason = "";
    // P4-FEEDBACK: reply follow-up release arm (holds Speaking until release fires) — P4-D18
    private bool _replyReleaseArmed;
    private bool _replyBoutSeen;
    private bool _replyBoutActive;
    private TaskCompletionSource<bool>? _replyBoutStartedTcs;
    private TaskCompletionSource<bool>? _replyBoutStoppedTcs;
    private CancellationTokenSource? _replyQuietCts;
    // P4-FEEDBACK: capture window for transcript logging (never text) — P4-D18
    private DateTimeOffset _captureWindowStart;
    private DateTimeOffset _captureWindowStop;
    private bool _captureWindowOpen;

    public VoiceController(ChatSocket chat)
    {
        // P2-VOICE: one controller listens on the window's existing socket — P2-D01
        _chat = chat;
        _chat.VoiceStatusChanged += OnVoiceStatus;
        _chat.VoiceTranscriptReceived += OnVoiceTranscript;
        _chat.VoiceInterrupted += OnVoiceInterrupted;
        // P2-WAKE: this controller is the only subscriber and the only owner of wake RPCs — P2-D12
        _chat.WakeDetected += OnWakeDetected;
        _chat.BeforeReplaceAsync = DisarmWakeAsync;
    }

    public string Mode { get; private set; } = ModeVoice;

    public bool IsAvailable { get; private set; }

    public string UnavailableDetails { get; private set; } = "";

    public bool CaptureActive { get; private set; }

    public string RecorderState { get; private set; } = StateIdle;

    public bool SessionReady { get; private set; }

    public bool BackendReachable { get; private set; }

    public bool TurnRunning { get; private set; }

    // P2-SPEAK: Speaking is an estimate from the simulated playback clock, not measured audio — P2-D08
    // P4-ASK: also held true while QuestionSpeaking drives the Speaking display/monitor path — P4-D13
    // P4-FEEDBACK: also held while reply follow-up release is armed (bout + quiet) — P4-D18
    private bool _speakingEstimate;

    public bool Speaking => _speakingEstimate || _replyReleaseArmed;

    // P4-ASK: question TTS in flight until release rule fires (feeds Speaking) — P4-D13
    public bool QuestionSpeaking => _questionSpeaking;

    // P4-FEEDBACK: Stop visibility from existing VC facts only (estimate accuracy limit) — P4-FB-STOP
    // P4-FEEDBACK: not while QuestionSpeaking — toggle off would mute the rest of the turn's TTS — P4-FB-STOP
    public bool CanStopSpeaking =>
        Mode == ModeVoice && !VoiceGated && Speaking && !_questionSpeaking;

    // P2-WAKE: armed and paused update only from confirmed Hermes replies or wake.detected — P2-D04
    public bool WakeArmed { get; private set; }

    public bool WakePaused { get; private set; }

    public bool WakeHeldElsewhere { get; private set; }

    public bool WakeUnavailable { get; private set; }

    public bool WakeSettingUp { get; private set; }

    public bool WakeAudioSilent { get; private set; }

    public string WakeHint { get; private set; } = "";

    // P4-LOCK: queryable lock/sleep gate facts for voice and HUD — P4-D01
    public bool SystemLocked { get; private set; }

    public bool SystemSuspended { get; private set; }

    // P4-LOCK: facts or an in-flight hold after unlock until open finishes — P4-D02
    public bool VoiceGated => SystemLocked || SystemSuspended || _gateHolding;

    // P4-ASK: open clarify for current session — HUD waiting state (set by MainWindow) — P4-D15
    public bool AwaitingAnswer { get; private set; }

    public bool Resting
    {
        get
        {
            // P2-WAKE: Resting never depends on WakePaused, so a detect can still start a capture — P2-D12
            return Mode == ModeVoice
                && IsAvailable
                && SessionReady
                && BackendReachable
                && !TurnRunning
                && !Speaking
                && !CaptureActive
                && !_followUpArmed
                && !_followUpCaptureStarted;
        }
    }

    public bool CanStartCapture
    {
        get
        {
            // P2-SPEAK: the mic stays off while a turn runs or the speaking estimate is still open — P2-D12
            // P4-LOCK: lock/sleep hold refuses capture at the shared mic gate — P4-D02
            return Mode == ModeVoice && IsAvailable && SessionReady && BackendReachable && !TurnRunning && !Speaking && !VoiceGated;
        }
    }

    public event Action? StateChanged;

    // P4-ASK: second arg is the srq-* id when this transcript ends a clarify-answer capture — P4-D14
    public event Action<string, string?>? TranscriptReady;

    public event Action? VoiceChatEnded;

    public event Action<string>? StatusMessage;

    // P4-LOCK: facts update on the caller thread before any close/open work is queued — P4-D01 / P4-D02
    public void SetLocked(bool locked)
    {
        SystemLocked = locked;
        ApplyGateFactAndEnqueue();
    }

    public void SetSuspended(bool suspended)
    {
        SystemSuspended = suspended;
        ApplyGateFactAndEnqueue();
    }

    public void NoteGateRefusal(string reason)
    {
        // P4-LOCK: MainWindow belt-and-braces submit refusal shares the timeline — P4-D02
        WriteTimeline(GateRefusePrefix + reason);
    }

    // P4-ASK: Phase 5 calls this immediately before opening the clarify-answer voice.record — P4-D14
    public void ArmClarifyAnswerCapture(string requestId)
    {
        _pendingClarifyCaptureId = string.IsNullOrEmpty(requestId) ? null : requestId;
    }

    public void NoteLateAnswerDropped(string id, int length)
    {
        // P4-ASK: length only — never the spoken answer text — P4-D14 / G-PRIVACY
        WriteTimeline(LogLateAnswerDroppedPrefix + id + " len=" + length);
    }

    // P4-ASK: MainWindow sets this from broker open-clarify-for-current — P4-D15
    public void SetAwaitingAnswer(bool awaiting)
    {
        if (AwaitingAnswer == awaiting)
        {
            return;
        }

        AwaitingAnswer = awaiting;
        StateChanged?.Invoke();
    }

    // P4-ASK: MainWindow wires monitor availability and pre-capture recheck — P4-D13
    // P4-FEEDBACK: also wires bout-active for reply release seed at complete — P4-D18
    public void ConfigureQuestionSpeech(
        Func<bool> playbackMonitorAvailable,
        Func<string, bool> clarifyCaptureStillValid,
        Func<bool> playbackBoutActive)
    {
        _playbackMonitorAvailable = playbackMonitorAvailable;
        _clarifyCaptureStillValid = clarifyCaptureStillValid;
        _playbackBoutActive = playbackBoutActive;
    }

    // P4-ASK: PresenceView bout forward — P4-D13
    // P4-FEEDBACK: also arms reply follow-up release (same monitor) — P4-D18
    public void NotePlaybackBoutStarted()
    {
        if (_questionBoutArmed)
        {
            _questionBoutStarted = true;
            _questionBoutActive = true;
            // P4-ASK: stopped TCS was created at arm; do not recreate (waiter may already be awaiting it) — P4-D13
            _questionBoutStartedTcs?.TrySetResult(true);
            return;
        }

        if (!_replyReleaseArmed)
        {
            return;
        }

        // P4-FEEDBACK: set active before cancel so a cancelled quiet delay cannot open mid-bout — P4-D18
        _replyBoutSeen = true;
        _replyBoutActive = true;
        CancelReplyQuietWait();
        if (_replyBoutStoppedTcs is null || _replyBoutStoppedTcs.Task.IsCompleted)
        {
            _replyBoutStoppedTcs = new TaskCompletionSource<bool>(TaskCreationOptions.RunContinuationsAsynchronously);
        }

        _replyBoutStartedTcs?.TrySetResult(true);
        if (!_speakingEstimate)
        {
            // P4-FEEDBACK: bout keeps Speaking true so presence does not StopMonitoring mid-reply — P4-D18
            StateChanged?.Invoke();
            _ = ReconcileWakeRestingAsync("reply-bout-start");
        }
    }

    // P4-ASK: forced=true is never a rule-1 release — P4-D13
    public void NotePlaybackBoutStopped(bool forced)
    {
        if (_questionBoutArmed || _questionBoutActive)
        {
            _questionBoutActive = false;
            _questionBoutStoppedTcs?.TrySetResult(forced);
            return;
        }

        if (!_replyReleaseArmed && !_replyBoutActive)
        {
            return;
        }

        _replyBoutActive = false;
        _replyBoutStoppedTcs?.TrySetResult(forced);
    }

    public void AbandonPendingQuestion(string reason)
    {
        var id = _pendingQuestionId;
        if (id is null && !_questionSpeaking)
        {
            return;
        }

        if (id is not null)
        {
            WriteTimeline(LogQuestionAbandonedPrefix + id + " reason=" + reason);
        }

        ClearPendingQuestionToken();
        EndQuestionSpeaking();
    }

    public void AbandonPendingQuestionIfId(string id, string reason)
    {
        if (string.Equals(_pendingQuestionId, id, StringComparison.Ordinal))
        {
            AbandonPendingQuestion(reason);
        }

        // P4-ASK: speak token may already be cleared while the answer capture is still in flight — P4-D14
        var captureId = _activeClarifyCaptureId ?? _pendingClarifyCaptureId;
        if (string.Equals(captureId, id, StringComparison.Ordinal))
        {
            StashClosedClarifyCapture(captureId);
            _pendingClarifyCaptureId = null;
            _activeClarifyCaptureId = null;
        }
    }

    private void StashClosedClarifyCapture(string? id)
    {
        if (string.IsNullOrEmpty(id))
        {
            return;
        }

        _closedClarifyCaptureId = id;
    }

    private void ClearClosedClarifyCapture()
    {
        _closedClarifyCaptureId = null;
    }

    private static bool ShouldStashClosedClarify(string reason)
    {
        // P4-ASK: only Cancel/interrupt parks a late-drop id; idle/silence must not bind the next wake turn — P4-D14
        return string.Equals(reason, "interrupted", StringComparison.Ordinal)
            || string.Equals(reason, "voice.interrupted", StringComparison.Ordinal)
            || string.Equals(reason, GateCancelReason, StringComparison.Ordinal);
    }

    // P4-ASK: speak the clarify once, wait for playback release, open bound clarify-answer capture — P4-D13
    public async Task SpeakQuestionAsync(string id, ServerRequestBroker.ClarifyView view)
    {
        if (VoiceGated)
        {
            WriteTimeline(LogQuestionRefusePrefix + QuestionRefuseGated + " id=" + id);
            return;
        }

        if (Mode != ModeVoice)
        {
            WriteTimeline(LogQuestionRefusePrefix + QuestionRefuseTextMode + " id=" + id);
            return;
        }

        if (_ttsOn != true)
        {
            WriteTimeline(LogQuestionRefusePrefix + QuestionRefuseSpeechOff + " id=" + id);
            return;
        }

        if (_pendingQuestionId is not null)
        {
            AbandonPendingQuestion(AbandonReasonNewerClarify);
        }

        var spoken = BuildSpokenQuestionText(view);
        if (string.IsNullOrWhiteSpace(spoken))
        {
            WriteTimeline(LogQuestionRefusePrefix + QuestionRefuseEmpty + " id=" + id);
            return;
        }

        CancelFollowUp("question-speak");
        ClearClosedClarifyCapture();
        var tokenGeneration = Interlocked.Increment(ref _pendingQuestionGeneration);
        _pendingQuestionId = id;
        _questionSpeaking = true;
        SetSpeaking(true);
        ArmQuestionBoutWait();

        var ttsReply = await _chat.InvokeAsync(MethodTts, new Dictionary<string, string?>
        {
            [ParamText] = spoken,
        }).ConfigureAwait(false);

        if (!ttsReply.Ok)
        {
            WriteTimeline(LogQuestionRefusePrefix + AbandonReasonTtsFailed + " id=" + id + " error=" + (ttsReply.Error ?? ""));
            AbandonPendingQuestion(AbandonReasonTtsFailed);
            return;
        }

        RememberSpokenEcho(spoken);
        WriteTimeline(LogQuestionSpokenPrefix + id + " chars=" + spoken.Length);
        var ttsReturnedAt = DateTimeOffset.Now;
        await WaitForQuestionReleaseThenCaptureAsync(id, tokenGeneration, spoken, ttsReturnedAt).ConfigureAwait(false);
    }

    private void ArmQuestionBoutWait()
    {
        _questionBoutArmed = true;
        _questionBoutStarted = false;
        _questionBoutActive = false;
        // P4-ASK: both TCS live for the token lifetime so rule-1 never races a null stopped wait — P4-D13
        _questionBoutStartedTcs = new TaskCompletionSource<bool>(TaskCreationOptions.RunContinuationsAsynchronously);
        _questionBoutStoppedTcs = new TaskCompletionSource<bool>(TaskCreationOptions.RunContinuationsAsynchronously);
    }

    private void ClearPendingQuestionToken()
    {
        _pendingQuestionId = null;
        Interlocked.Increment(ref _pendingQuestionGeneration);
        _questionBoutArmed = false;
        _questionBoutStarted = false;
        _questionBoutActive = false;
        _questionBoutStartedTcs?.TrySetCanceled();
        _questionBoutStoppedTcs?.TrySetCanceled();
        _questionBoutStartedTcs = null;
        _questionBoutStoppedTcs = null;
    }

    private void EndQuestionSpeaking()
    {
        if (!_questionSpeaking)
        {
            return;
        }

        _questionSpeaking = false;
        SetSpeaking(false);
    }

    private static string BuildSpokenQuestionText(ServerRequestBroker.ClarifyView view)
    {
        // P4-ASK: speak question text only — never choices (developer 2026-09-30 / P4-D13 amend) — P4-D13
        if (view.IsBatch)
        {
            var first = view.Questions.Count > 0 ? view.Questions[0].Question.Trim() : "";
            if (string.IsNullOrEmpty(first))
            {
                return "";
            }

            return view.Questions.Count > 1 ? first + SpokenBatchMoreSuffix : first;
        }

        return view.Question.Trim();
    }

    private double EstimateQuestionPlaybackSeconds(string text)
    {
        var words = CountSpokenWords(text);
        var sentences = Math.Max(1, CountSpokenSentences(text));
        return FirstSentenceLatencySeconds
            + (words / EstimatedWordsPerSecond)
            + (sentences * PerSentenceOverheadSeconds);
    }

    private bool IsPendingQuestionCurrent(string id, int tokenGeneration)
    {
        return tokenGeneration == Volatile.Read(ref _pendingQuestionGeneration)
            && string.Equals(_pendingQuestionId, id, StringComparison.Ordinal);
    }

    private async Task WaitForQuestionReleaseThenCaptureAsync(
        string id,
        int tokenGeneration,
        string spoken,
        DateTimeOffset ttsReturnedAt)
    {
        try
        {
            if (!IsPendingQuestionCurrent(id, tokenGeneration))
            {
                return;
            }

            var monitorAvailable = _playbackMonitorAvailable?.Invoke() == true;
            string rule;
            if (!monitorAvailable)
            {
                rule = QuestionRuleMonitorUnavailable;
                var estimateSeconds = EstimateQuestionPlaybackSeconds(spoken) + FollowUpMarginSeconds;
                WriteTimeline(
                    LogQuestionReleasePrefix + rule
                    + " id=" + id
                    + " estimate_s=" + estimateSeconds.ToString("0.###")
                    + " tts_at=" + ttsReturnedAt.ToString("o"));
                await Task.Delay(TimeSpan.FromSeconds(estimateSeconds)).ConfigureAwait(false);
            }
            else
            {
                var startedTcs = _questionBoutStartedTcs;
                var startup = Task.Delay(TimeSpan.FromSeconds(QuestionBoutStartupWindowSeconds));
                var startedWait = startedTcs?.Task ?? Task.FromResult(false);
                var winner = await Task.WhenAny(startedWait, startup).ConfigureAwait(false);
                if (!IsPendingQuestionCurrent(id, tokenGeneration))
                {
                    return;
                }

                if (winner == startedWait && _questionBoutStarted)
                {
                    // P4-ASK: rule 1 — bout started; exits are natural stop, forced estimate, or invalidation only — P4-D13
                    var stoppedTcs = _questionBoutStoppedTcs
                        ?? throw new InvalidOperationException("question bout stopped TCS missing while bout started");
                    bool forced;
                    try
                    {
                        forced = await stoppedTcs.Task.ConfigureAwait(false);
                    }
                    catch (TaskCanceledException)
                    {
                        return;
                    }

                    if (!IsPendingQuestionCurrent(id, tokenGeneration))
                    {
                        return;
                    }

                    if (forced)
                    {
                        // Forced release → unobservable; estimate from tts return unless abandoned.
                        rule = QuestionRuleForcedEstimate;
                        var elapsed = (DateTimeOffset.Now - ttsReturnedAt).TotalSeconds;
                        var estimateSeconds = EstimateQuestionPlaybackSeconds(spoken) + FollowUpMarginSeconds;
                        var remaining = Math.Max(0, estimateSeconds - elapsed);
                        WriteTimeline(
                            LogQuestionReleasePrefix + rule
                            + " id=" + id
                            + " remaining_s=" + remaining.ToString("0.###"));
                        if (remaining > 0)
                        {
                            await Task.Delay(TimeSpan.FromSeconds(remaining)).ConfigureAwait(false);
                        }
                    }
                    else
                    {
                        rule = QuestionRuleMonitor;
                        WriteTimeline(
                            LogQuestionReleasePrefix + rule
                            + " id=" + id
                            + " tts_at=" + ttsReturnedAt.ToString("o")
                            + " released_at=" + DateTimeOffset.Now.ToString("o"));
                    }
                }
                else
                {
                    // Rule 2: no bout within startup window — estimate; late bout inside estimate upgrades to rule 1.
                    rule = QuestionRuleNoBoutEstimate;
                    var estimateSeconds = EstimateQuestionPlaybackSeconds(spoken) + FollowUpMarginSeconds;
                    WriteTimeline(
                        LogQuestionReleasePrefix + rule
                        + " id=" + id
                        + " estimate_s=" + estimateSeconds.ToString("0.###")
                        + " startup_s=" + QuestionBoutStartupWindowSeconds.ToString("0.###"));
                    var estimateDelay = Task.Delay(TimeSpan.FromSeconds(estimateSeconds));
                    while (true)
                    {
                        if (!IsPendingQuestionCurrent(id, tokenGeneration))
                        {
                            return;
                        }

                        if (_questionBoutStarted)
                        {
                            // P4-ASK: late bout → rule 1; wait for stop (never timer while active) — P4-D13
                            var stoppedTcs = _questionBoutStoppedTcs
                                ?? throw new InvalidOperationException("question bout stopped TCS missing while bout started");
                            bool forced;
                            try
                            {
                                forced = await stoppedTcs.Task.ConfigureAwait(false);
                            }
                            catch (TaskCanceledException)
                            {
                                return;
                            }

                            if (!IsPendingQuestionCurrent(id, tokenGeneration))
                            {
                                return;
                            }

                            if (forced)
                            {
                                var elapsed = (DateTimeOffset.Now - ttsReturnedAt).TotalSeconds;
                                var remaining = Math.Max(0, estimateSeconds - elapsed);
                                WriteTimeline(
                                    LogQuestionReleasePrefix + QuestionRuleForcedEstimate
                                    + " id=" + id
                                    + " late_bout=1 remaining_s=" + remaining.ToString("0.###"));
                                if (remaining > 0)
                                {
                                    await Task.Delay(TimeSpan.FromSeconds(remaining)).ConfigureAwait(false);
                                }
                            }
                            else
                            {
                                WriteTimeline(
                                    LogQuestionReleasePrefix + QuestionRuleMonitor
                                    + " id=" + id
                                    + " late_bout=1");
                            }

                            break;
                        }

                        if (estimateDelay.IsCompleted)
                        {
                            break;
                        }

                        await Task.WhenAny(estimateDelay, Task.Delay(50)).ConfigureAwait(false);
                    }
                }
            }

            if (!IsPendingQuestionCurrent(id, tokenGeneration))
            {
                return;
            }

            await OpenClarifyAnswerCaptureAsync(id, tokenGeneration).ConfigureAwait(false);
        }
        finally
        {
            // P4-ASK: always drop QuestionSpeaking after the wait chain (capture may still be open) — P4-D13
            EndQuestionSpeaking();
            _questionBoutArmed = false;
        }
    }

    private async Task OpenClarifyAnswerCaptureAsync(string id, int tokenGeneration)
    {
        if (!IsPendingQuestionCurrent(id, tokenGeneration))
        {
            WriteTimeline(LogQuestionCaptureSkipPrefix + id + " reason=" + CaptureSkipTokenStale);
            return;
        }

        if (VoiceGated)
        {
            WriteTimeline(LogQuestionCaptureSkipPrefix + id + " reason=" + CaptureSkipGated);
            ClearPendingQuestionToken();
            return;
        }

        if (Mode != ModeVoice)
        {
            WriteTimeline(LogQuestionCaptureSkipPrefix + id + " reason=" + CaptureSkipNotVoice);
            ClearPendingQuestionToken();
            return;
        }

        if (_ttsOn != true)
        {
            WriteTimeline(LogQuestionCaptureSkipPrefix + id + " reason=" + CaptureSkipSpeechOff);
            ClearPendingQuestionToken();
            return;
        }

        if (_clarifyCaptureStillValid?.Invoke(id) != true)
        {
            WriteTimeline(LogQuestionCaptureSkipPrefix + id + " reason=" + CaptureSkipNotOpen);
            ClearPendingQuestionToken();
            return;
        }

        ArmClarifyAnswerCapture(id);
        _followUpArmed = true;
        _followUpEchoPending = true;
        _followUpTranscriptSeen = false;
        _echoIgnoreCount = 0;
        _cancelReason = "";
        var generation = Volatile.Read(ref _followUpGeneration);
        // P4-ASK: clear question token before capture; Speaking ends in WaitFor finally — P4-D13
        ClearPendingQuestionToken();
        EndQuestionSpeaking();
        _followUpArmed = true;
        await StartCaptureAsync(generation).ConfigureAwait(false);
        if (!CaptureActive)
        {
            CancelFollowUp("clarify-capture-failed");
        }
    }

    public void SetCaptureGate(bool sessionReady, bool backendReachable, bool turnRunning)
    {
        // P2-VOICE: the window reports session and turn facts; this object keeps the enable rule — P2-D12
        if (SessionReady == sessionReady && BackendReachable == backendReachable && TurnRunning == turnRunning)
        {
            return;
        }

        SessionReady = sessionReady;
        BackendReachable = backendReachable;
        TurnRunning = turnRunning;
        StateChanged?.Invoke();
        // P2-WAKE: TurnRunning leaving or entering Resting pauses or resumes the detector — P2-D12
        _ = ReconcileWakeRestingAsync(turnRunning ? "turn-start" : "turn-end");
    }

    private void ApplyGateFactAndEnqueue()
    {
        // P4-LOCK: hold begins with the first gated fact so guards never see an open window — P4-D02
        var factsGated = SystemLocked || SystemSuspended;
        if (factsGated)
        {
            _gateHolding = true;
        }

        WriteTimeline(string.Format(
            GateFactLineFormat,
            SystemLocked ? GateFactTrue : GateFactFalse,
            SystemSuspended ? GateFactTrue : GateFactFalse));
        StateChanged?.Invoke();
        Interlocked.Increment(ref _gateEpoch);
        _ = RunGateSequenceAsync();
    }

    private async Task RunGateSequenceAsync()
    {
        // P4-LOCK: one worker; re-reads facts each loop so latest desired state wins — P4-D02 / P4-D03
        // P4-FEEDBACK: Stop speaking shares this worker; a gated close always wins — P4-FB-STOP
        await _gateSequenceLock.WaitAsync().ConfigureAwait(false);
        try
        {
            while (true)
            {
                var epoch = Volatile.Read(ref _gateEpoch);
                var factsGated = SystemLocked || SystemSuspended;
                if (factsGated)
                {
                    // P4-FEEDBACK: gate close supersedes any pending Stop restore — P4-FB-STOP
                    Volatile.Write(ref _stopSpeakingDone, Volatile.Read(ref _stopSpeakingQueued));
                    _gateHolding = true;
                    if (!_gateCloseCompleted)
                    {
                        var closed = await CloseGateAsync().ConfigureAwait(false);
                        _gateCloseCompleted = true;
                        if (!closed)
                        {
                            WriteTimeline(GateClosedFailed);
                        }
                    }
                }
                else if (_gateHolding)
                {
                    await OpenGateAsync().ConfigureAwait(false);
                    if (!(SystemLocked || SystemSuspended))
                    {
                        _gateHolding = false;
                        _gateCloseCompleted = false;
                        ClearGateSnapshot();
                        StateChanged?.Invoke();
                    }
                }
                else if (Volatile.Read(ref _stopSpeakingQueued) > Volatile.Read(ref _stopSpeakingDone))
                {
                    await ExecuteStopSpeakingAsync().ConfigureAwait(false);
                    Volatile.Write(ref _stopSpeakingDone, Volatile.Read(ref _stopSpeakingQueued));
                }

                if (epoch == Volatile.Read(ref _gateEpoch))
                {
                    break;
                }
            }
        }
        finally
        {
            _gateSequenceLock.Release();
        }
    }

    // P4-FEEDBACK: Stop = toggle off + restore availability; no interrupt; no AbandonPendingQuestion — P4-FB-STOP
    public async Task StopSpeakingAsync()
    {
        WriteTimeline(StopSpeakingRequested);
        if (SystemLocked || SystemSuspended || _gateHolding)
        {
            WriteTimeline(StopSpeakingRefusedPrefix + StopSpeakingRefuseGated);
            return;
        }

        // P4-FEEDBACK: refuse while clarify question TTS — off would silence the whole turn — P4-FB-STOP
        if (_questionSpeaking)
        {
            WriteTimeline(StopSpeakingRefusedPrefix + StopSpeakingRefuseQuestionSpeaking);
            return;
        }

        if (!Speaking)
        {
            WriteTimeline(StopSpeakingRefusedPrefix + StopSpeakingRefuseNotSpeaking);
            return;
        }

        Interlocked.Increment(ref _stopSpeakingQueued);
        Interlocked.Increment(ref _gateEpoch);
        await RunGateSequenceAsync().ConfigureAwait(false);
    }

    private async Task ExecuteStopSpeakingAsync()
    {
        if (SystemLocked || SystemSuspended)
        {
            WriteTimeline(StopSpeakingRefusedPrefix + StopSpeakingRefuseGated);
            return;
        }

        // P4-FEEDBACK: refuse while clarify question TTS — off would silence the whole turn — P4-FB-STOP
        if (_questionSpeaking)
        {
            WriteTimeline(StopSpeakingRefusedPrefix + StopSpeakingRefuseQuestionSpeaking);
            return;
        }

        if (!Speaking)
        {
            WriteTimeline(StopSpeakingRefusedPrefix + StopSpeakingRefuseNotSpeaking);
            return;
        }

        var speechWasOn = _ttsOn == true;
        var wakeWasArmed = WakeArmed;
        WriteTimeline(string.Format(
            StopSpeakingStepPrefix + "snapshot speech={0} wake={1}",
            speechWasOn ? GateBoolTrue : GateBoolFalse,
            wakeWasArmed ? GateBoolTrue : GateBoolFalse));

        // P4-FEEDBACK: cancel pending follow-up so she does not auto-listen; keep clarify token — P4-FB-STOP
        WriteTimeline(StopSpeakingStepPrefix + "cancel_follow_up");
        CancelFollowUp(StopSpeakingCancelReason);
        // P4-FEEDBACK: freeze P2-D15 estimate for the rest of this turn (not QuestionSpeaking) — P4-FB-STOP
        _speechStoppedThisTurn = true;

        try
        {
            // P4-FEEDBACK: same voice.toggle off as gate close — no S21 latch — P4-FB-STOP
            WriteTimeline(StopSpeakingStepPrefix + "voice.toggle_off");
            var off = await ToggleAsync(ActionOff).ConfigureAwait(false);
            WriteTimeline(string.Format(
                StopSpeakingStepPrefix + "voice.toggle_off ok={0} enabled={1} tts={2} error={3}",
                off.Ok ? GateBoolTrue : GateBoolFalse,
                off.Enabled?.ToString() ?? "",
                off.Tts?.ToString() ?? "",
                off.Error ?? ""));
        }
        catch (Exception ex)
        {
            WriteTimeline(StopSpeakingStepPrefix + "voice.toggle_off error=" + ex.Message);
        }

        if (SystemLocked || SystemSuspended)
        {
            WriteTimeline(StopSpeakingRefusedPrefix + StopSpeakingRefuseReGated);
            return;
        }

        try
        {
            WriteTimeline(StopSpeakingStepPrefix + "voice.toggle_on");
            var on = await ToggleAsync(ActionOn).ConfigureAwait(false);
            WriteTimeline(string.Format(
                StopSpeakingStepPrefix + "voice.toggle_on ok={0} enabled={1} error={2}",
                on.Ok ? GateBoolTrue : GateBoolFalse,
                on.Enabled?.ToString() ?? "",
                on.Error ?? ""));
            if (!on.Ok || on.Enabled == false)
            {
                WriteTimeline(StopSpeakingDone);
                StateChanged?.Invoke();
                return;
            }

            if (SystemLocked || SystemSuspended)
            {
                WriteTimeline(StopSpeakingRefusedPrefix + StopSpeakingRefuseReGated);
                return;
            }

            var status = await ToggleAsync(ActionStatus).ConfigureAwait(false);
            WriteTimeline(string.Format(
                StopSpeakingStepPrefix + "voice.toggle_status ok={0} tts={1} error={2}",
                status.Ok ? GateBoolTrue : GateBoolFalse,
                status.Tts?.ToString() ?? "",
                status.Error ?? ""));
            if (status.Ok)
            {
                IsAvailable = status.Available == true && status.AudioAvailable == true && status.SttAvailable == true;
                UnavailableDetails = status.Details ?? "";
            }

            // P4-FEEDBACK: restore speech via P2-D03 status-first flip only (not used to stop) — P4-FB-STOP
            if (speechWasOn && status.Ok && status.Tts == false)
            {
                WriteTimeline(StopSpeakingStepPrefix + "voice.toggle_tts_restore");
                var spoken = await ToggleAsync(ActionTts).ConfigureAwait(false);
                WriteTimeline(string.Format(
                    StopSpeakingStepPrefix + "voice.toggle_tts_restore ok={0} tts={1} error={2}",
                    spoken.Ok ? GateBoolTrue : GateBoolFalse,
                    spoken.Tts?.ToString() ?? "",
                    spoken.Error ?? ""));
            }
            else
            {
                WriteTimeline(StopSpeakingStepPrefix + "voice.toggle_tts_restore skipped");
            }

            if (SystemLocked || SystemSuspended)
            {
                WriteTimeline(StopSpeakingRefusedPrefix + StopSpeakingRefuseReGated);
                return;
            }

            if (wakeWasArmed)
            {
                WriteTimeline(StopSpeakingStepPrefix + "wake_rearm");
                await ArmWakeAsync().ConfigureAwait(false);
            }
        }
        catch (Exception ex)
        {
            WriteTimeline(StopSpeakingStepPrefix + "restore error=" + ex.Message);
        }

        WriteTimeline(StopSpeakingDone);
        StateChanged?.Invoke();
    }

    private async Task<bool> CloseGateAsync()
    {
        // P4-LOCK: fail-closed close sequence; never session.interrupt; never voice.toggle tts — P4-D02
        // P4-LOCK: wake.stop (not pause) so Hermes resume retries after record-stop cannot reopen the mic — P4-D02
        WriteTimeline(GateClosedStarting);
        if (!_gateSnapshotTaken)
        {
            _gateSnapshotMode = Mode;
            _gateSnapshotSpeechEnabled = _ttsOn == true;
            _gateSnapshotWakeArmed = WakeArmed;
            _gateSnapshotTaken = true;
            WriteTimeline(string.Format(
                GateSnapshotFormat,
                _gateSnapshotMode,
                _gateSnapshotSpeechEnabled ? GateBoolTrue : GateBoolFalse,
                _gateSnapshotWakeArmed ? GateBoolTrue : GateBoolFalse));
        }
        else
        {
            WriteTimeline(GateSnapshotRetained);
        }

        WriteTimeline(GateStepCancelFollowUp);
        // P4-ASK: gate close abandons pending question speech/capture chain — P4-D13
        AbandonPendingQuestion(AbandonReasonVoiceGated);
        CancelFollowUp(GateCancelReason);

        var ok = true;
        if (CaptureActive)
        {
            try
            {
                var stop = await RecordAsync(ActionStop, allowResync: false, requiredGeneration: null).ConfigureAwait(false);
                WriteTimeline(string.Format(
                    GateStepRecordStopFormat,
                    stop.Ok ? GateBoolTrue : GateBoolFalse,
                    stop.Status ?? "",
                    stop.Error ?? ""));
                if (!stop.Ok)
                {
                    ok = false;
                }
            }
            catch (Exception ex)
            {
                WriteTimeline(string.Format(GateStepRecordStopFormat, GateBoolFalse, "", ex.Message));
                ok = false;
            }
        }
        else
        {
            WriteTimeline(GateStepRecordStopSkipped);
        }

        try
        {
            // P4-LOCK: voice.toggle off stops TTS without S21 latch and kills the full-duplex barge mic — P4-D02
            // Mode is not assigned here; only EnterTextModeAsync / EnterVoiceModeAsync / MarkUnavailable set Mode.
            var off = await ToggleAsync(ActionOff).ConfigureAwait(false);
            WriteTimeline(string.Format(
                GateStepToggleOffFormat,
                off.Ok ? GateBoolTrue : GateBoolFalse,
                off.Enabled?.ToString() ?? "",
                off.Tts?.ToString() ?? "",
                off.Error ?? ""));
            if (!off.Ok)
            {
                ok = false;
            }
        }
        catch (Exception ex)
        {
            WriteTimeline(string.Format(GateStepToggleOffFormat, GateBoolFalse, "", "", ex.Message));
            ok = false;
        }

        try
        {
            WriteTimeline(GateStepWakeStop);
            await DisarmWakeAsync().ConfigureAwait(false);
        }
        catch (Exception ex)
        {
            WriteTimeline(GateStepWakeStop + " error=" + ex.Message);
            ok = false;
        }

        try
        {
            var status = await _chat.InvokeAsync(
                MethodWakeStatus,
                new Dictionary<string, string?> { [ParamSurface] = SurfaceGui }).ConfigureAwait(false);
            var listening = status.Listening == true;
            WriteTimeline(string.Format(
                GateStepWakeStatusFormat,
                status.Listening?.ToString() ?? "",
                status.OwnedByCaller?.ToString() ?? ""));
            if (listening)
            {
                WriteTimeline(GateStepWakeStopRetry);
                await DisarmWakeAsync().ConfigureAwait(false);
                ok = false;
            }
        }
        catch (Exception ex)
        {
            WriteTimeline(string.Format(GateStepWakeStatusFormat, "", "") + " error=" + ex.Message);
            ok = false;
        }

        WriteTimeline(GateClosedDone);
        return ok;
    }

    private async Task OpenGateAsync()
    {
        // P4-LOCK: reset close-completed so a mid-open relock re-runs CloseGateAsync — P4-D03
        _gateCloseCompleted = false;
        WriteTimeline(GateOpenedStarting);
        if (AbortOpenIfReGated())
        {
            return;
        }

        if (!string.Equals(_gateSnapshotMode, ModeVoice, StringComparison.Ordinal) || Mode != ModeVoice)
        {
            WriteTimeline(GateOpenedSkippedText);
            WriteTimeline(GateOpenedDone);
            return;
        }

        try
        {
            if (AbortOpenIfReGated())
            {
                return;
            }

            var on = await ToggleAsync(ActionOn).ConfigureAwait(false);
            WriteTimeline(string.Format(
                GateStepToggleOnFormat,
                on.Ok ? GateBoolTrue : GateBoolFalse,
                on.Enabled?.ToString() ?? "",
                on.Error ?? ""));
            if (!on.Ok || on.Enabled == false)
            {
                WriteTimeline(GateOpenedDone);
                return;
            }

            if (AbortOpenIfReGated())
            {
                return;
            }

            var status = await ToggleAsync(ActionStatus).ConfigureAwait(false);
            WriteTimeline(string.Format(
                GateStepToggleStatusFormat,
                status.Ok ? GateBoolTrue : GateBoolFalse,
                status.Enabled?.ToString() ?? "",
                status.Tts?.ToString() ?? "",
                status.Error ?? ""));
            if (!status.Ok)
            {
                WriteTimeline(GateOpenedDone);
                return;
            }

            IsAvailable = status.Available == true && status.AudioAvailable == true && status.SttAvailable == true;
            UnavailableDetails = status.Details ?? "";
            if (!IsAvailable)
            {
                WriteTimeline(GateOpenedDone);
                StateChanged?.Invoke();
                return;
            }

            if (AbortOpenIfReGated())
            {
                return;
            }

            // P4-LOCK: on does not enable TTS; status-first flip only when snapshot had speech — P4-D03 / P2-D03
            if (_gateSnapshotSpeechEnabled && status.Tts == false)
            {
                var spoken = await ToggleAsync(ActionTts).ConfigureAwait(false);
                WriteTimeline(string.Format(
                    GateStepToggleTtsFormat,
                    spoken.Ok ? GateBoolTrue : GateBoolFalse,
                    spoken.Tts?.ToString() ?? "",
                    spoken.Error ?? ""));
            }
            else
            {
                WriteTimeline(GateStepToggleTtsSkipped);
            }

            if (AbortOpenIfReGated())
            {
                return;
            }

            if (_gateSnapshotWakeArmed)
            {
                WriteTimeline(GateStepWakeStart);
                // P4-LOCK: open uses wake.start only; never wake.resume after wake.stop close — P4-D02 / P4-D03
                await ArmWakeAsync(fromGateOpen: true).ConfigureAwait(false);
            }

            StateChanged?.Invoke();
        }
        catch (Exception ex)
        {
            WriteTimeline(GateOpenedErrorPrefix + ex.Message);
        }

        WriteTimeline(GateOpenedDone);
    }

    private bool AbortOpenIfReGated()
    {
        if (!(SystemLocked || SystemSuspended))
        {
            return false;
        }

        WriteTimeline(GateOpenAborted);
        return true;
    }

    private void ClearGateSnapshot()
    {
        _gateSnapshotTaken = false;
        WriteTimeline(GateSnapshotCleared);
    }

    private bool RefuseIfGated(string reason)
    {
        if (!VoiceGated)
        {
            return false;
        }

        WriteTimeline(GateRefusePrefix + reason);
        return true;
    }

    public async Task SyncVoiceModeAsync()
    {
        // P2-VOICE: each socket re-reads voice status and turns voice on only when it is off — P2-D07
        if (Mode != ModeVoice)
        {
            return;
        }

        // P4-LOCK: reconnect sync must not reopen Hermes voice behind a closed gate — P4-D02
        if (RefuseIfGated(GateRefuseSyncVoiceWake))
        {
            return;
        }

        var status = await ToggleAsync(ActionStatus).ConfigureAwait(false);
        if (!status.Ok)
        {
            // P2-VOICE: a failed status probe leaves the composer usable in Text mode — P2-D07
            MarkUnavailable(status.Error ?? status.Details ?? "");
            return;
        }

        IsAvailable = status.Available == true && status.AudioAvailable == true && status.SttAvailable == true;
        UnavailableDetails = status.Details ?? "";
        if (!IsAvailable)
        {
            // P2-VOICE: unavailable voice does not block typed chat — P2-D07
            MarkUnavailable(UnavailableDetails);
            return;
        }

        if (status.Enabled != true)
        {
            // P2-VOICE: voice.toggle on enables capture — P2-D07
            var enabled = await ToggleAsync(ActionOn).ConfigureAwait(false);
            if (!enabled.Ok || enabled.Enabled == false)
            {
                MarkUnavailable(enabled.Error ?? enabled.Details ?? UnavailableDetails);
                return;
            }

            // P2-SPEAK: on does not change tts, so the flip check uses a new status read — P2-D03
            status = await ToggleAsync(ActionStatus).ConfigureAwait(false);
            if (!status.Ok)
            {
                MarkUnavailable(status.Error ?? status.Details ?? UnavailableDetails);
                return;
            }
        }

        // P2-SPEAK: action=tts is sent once, and only when this status says tts is false — P2-D03
        if (status.Tts == false)
        {
            var spoken = await ToggleAsync(ActionTts).ConfigureAwait(false);
            if (!spoken.Ok || spoken.Tts != true)
            {
                StatusMessage?.Invoke(NoticeSpokenRepliesOff);
                Debug.WriteLine(NoticeSpokenRepliesOff);
            }
        }

        StateChanged?.Invoke();
    }

    public async Task SyncVoiceAndWakeAsync()
    {
        // P4-LOCK: SessionReady sync must not re-arm wake behind the gate — P4-D02
        if (RefuseIfGated(GateRefuseSyncVoiceWake))
        {
            return;
        }

        // P2-WAKE: every new socket and Voice-mode entry syncs voice, then arms wake — P2-D04
        await SyncVoiceModeAsync().ConfigureAwait(false);
        if (Mode == ModeVoice && IsAvailable)
        {
            await ArmWakeAsync().ConfigureAwait(false);
        }
    }

    public async Task EnterTextModeAsync()
    {
        // P2-SPEAK: leaving Voice cancels the follow-up window and clears the self-trip count — P2-D06
        ResetSelfInterruptCount();
        // P4-ASK: Text mode invalidates a pending spoken question — P4-D13
        AbandonPendingQuestion(AbandonReasonTextMode);
        CancelFollowUp("mode-text");
        // P2-VOICE: text mode turns Hermes voice off and clears a live capture — P2-D07
        var reply = await ToggleAsync(ActionOff).ConfigureAwait(false);
        if (!reply.Ok)
        {
            StatusMessage?.Invoke(reply.Error ?? "Voice could not be turned off.");
            return;
        }

        // P2-WAKE: Text mode disarms; the loop guard reaches here through this method — P2-D07
        await DisarmWakeAsync().ConfigureAwait(false);
        BumpConnectionGeneration();
        Mode = ModeText;
        CaptureActive = false;
        RecorderState = StateIdle;
        // P4-LOCK: mode change while gated updates the unlock snapshot — P4-D03
        if (_gateHolding || SystemLocked || SystemSuspended)
        {
            _gateSnapshotMode = ModeText;
            _gateSnapshotSpeechEnabled = false;
            _gateSnapshotWakeArmed = false;
        }

        StateChanged?.Invoke();
    }

    public async Task EnterVoiceModeAsync()
    {
        // P2-SPEAK: returning to Voice clears a leftover self-trip count — P2-D12
        ResetSelfInterruptCount();
        // P2-WAKE: a mode change invalidates in-flight wake replies, then arms after sync — P2-D04
        BumpConnectionGeneration();
        // P2-VOICE: switching back to Voice re-syncs this socket instead of restarting serve — P2-D07
        Mode = ModeVoice;
        // P4-LOCK: while gated, only update the snapshot; unlock runs the open sequence — P4-D03
        if (_gateHolding || SystemLocked || SystemSuspended)
        {
            _gateSnapshotMode = ModeVoice;
            _gateSnapshotSpeechEnabled = true;
            _gateSnapshotWakeArmed = true;
            StateChanged?.Invoke();
            return;
        }

        await SyncVoiceAndWakeAsync().ConfigureAwait(false);
    }

    public async Task ToggleCaptureAsync()
    {
        // P2-VOICE: the mic button and hotkey share one capture toggle — P2-D04
        if (Mode != ModeVoice || !IsAvailable)
        {
            return;
        }

        if (!CaptureActive)
        {
            await StartCaptureAsync(requiredGeneration: null).ConfigureAwait(false);
            return;
        }

        if (RecorderState == StateTranscribing)
        {
            // P2-VOICE: a capture that is already transcribing is left to finish — P2-D05
            return;
        }

        await StopCaptureAsync().ConfigureAwait(false);
    }

    public void OnTurnStarted()
    {
        // P2-SPEAK: a new turn invalidates any pending follow-up and restarts the clock — P2-D06
        // P4-FEEDBACK: typed or voice turn clears the closed-clarify late-drop id — P4-D14
        ClearClosedClarifyCapture();
        // P4-FEEDBACK: new turn clears Stop-this-turn freeze so the estimate can run again — P4-FB-STOP
        _speechStoppedThisTurn = false;
        BumpFollowUpGeneration();
        DisposeFollowUpTimer();
        // P4-FEEDBACK: new turn drops reply release arm (Speaking hold) — P4-D18
        ClearReplyFollowUpRelease();
        _accumulatedReply = "";
        _countedWords = 0;
        _countedSentences = 0;
        _followUpArmed = false;
        _followUpCaptureStarted = false;
        _followUpTranscriptSeen = false;
        _followUpEchoPending = false;
        _echoIgnoreCount = 0;
        _cancelReason = "";
        _turnStartedAt = DateTimeOffset.Now;
        _turnCompletedAt = default;
        _timerDelaySeconds = 0;
        // P2-WAKE: a turn start leaves Resting; pause before barge-in shares the mic — P2-D12
        _ = ReconcileWakeRestingAsync("turn-start");
        if (!ClockEligible)
        {
            SetSpeaking(false);
            if (Mode == ModeVoice)
            {
                StatusMessage?.Invoke(NoticeSpokenRepliesUnavailable);
            }

            return;
        }

        _estimatedSpeechEnd = _turnStartedAt.AddSeconds(FirstSentenceLatencySeconds);
        SetSpeaking(true);
    }

    public void OnTurnDelta(string chunk)
    {
        // P2-SPEAK: word count is always from the accumulated reply, never from one raw delta — P2-D06
        if (!ClockEligible)
        {
            return;
        }

        // P4-FEEDBACK: after Stop, still accumulate text for echo; do not re-arm the estimate — P4-FB-STOP
        if (_speechStoppedThisTurn)
        {
            _accumulatedReply += chunk ?? "";
            _countedWords = CountSpokenWords(_accumulatedReply);
            _countedSentences = CountSpokenSentences(_accumulatedReply);
            return;
        }

        _accumulatedReply += chunk ?? "";
        var cumulativeWords = CountSpokenWords(_accumulatedReply);
        var cumulativeSentences = CountSpokenSentences(_accumulatedReply);
        var newWords = Math.Max(0, cumulativeWords - _countedWords);
        var newSentences = Math.Max(0, cumulativeSentences - _countedSentences);
        _countedWords = cumulativeWords;
        _countedSentences = cumulativeSentences;
        var now = DateTimeOffset.Now;
        var baseEnd = _estimatedSpeechEnd > now ? _estimatedSpeechEnd : now;
        _estimatedSpeechEnd = baseEnd.AddSeconds(newWords / EstimatedWordsPerSecond + newSentences * PerSentenceOverheadSeconds);
    }

    public void OnTurnCompleted(string status)
    {
        // P2-SPEAK: only a complete reply starts the follow-up timer — P2-D06
        if (string.Equals(status, "complete", StringComparison.Ordinal))
        {
            ResetSelfInterruptCount();
            // P4-FEEDBACK: Stop this turn → no follow-up auto-listen; Speaking stays false — P4-FB-STOP
            if (_speechStoppedThisTurn)
            {
                SetSpeaking(false);
                _turnCompletedAt = DateTimeOffset.Now;
                RememberSpokenEcho(_accumulatedReply);
                WriteTimeline(StopSpeakingStepPrefix + "follow_up_skipped");
                _ = ReconcileWakeRestingAsync("stop-speaking-complete");
                return;
            }

            if (!ClockEligible)
            {
                SetSpeaking(false);
                return;
            }

            _turnCompletedAt = DateTimeOffset.Now;
            RememberSpokenEcho(_accumulatedReply);
            if ((_estimatedSpeechEnd - _turnStartedAt).TotalSeconds > MaxEstimatedSpeechSeconds)
            {
                WriteTimeline($"WARN estimated-speech={(_estimatedSpeechEnd - _turnStartedAt).TotalSeconds:0.###}s exceeds {MaxEstimatedSpeechSeconds}s");
            }

            var generation = _followUpGeneration;
            _followUpArmed = true;
            DisposeFollowUpTimer();
            // P4-FEEDBACK: arm reply release (monitor + quiet, or estimate fallback) — P4-D18
            ArmReplyFollowUpRelease();
            _ = RunReplyFollowUpReleaseAsync(generation);
            // P2-WAKE: an armed follow-up window is not Resting, so the detector stays paused — P2-D12
            _ = ReconcileWakeRestingAsync("follow-up-armed");
            return;
        }

        CancelFollowUp(status);
    }

    public void OnTypedSubmit()
    {
        // P2-SPEAK: a typed Send cancels follow-up and is not a self-trip — P2-D06
        ResetSelfInterruptCount();
        CancelFollowUp("typed-submit");
    }

    public void OnSessionReady()
    {
        // P2-WAKE: a new socket invalidates in-flight wake replies from the previous transport — P2-D04
        BumpConnectionGeneration();
        // P2-SPEAK: every new or resumed session drops a pending follow-up — P2-D06
        CancelFollowUp("session-ready");
    }

    public void Shutdown()
    {
        // P2-SPEAK: closing the window must not leave a follow-up timer armed — P2-D06
        CancelFollowUp("app-close");
    }

    private bool ClockEligible => Mode == ModeVoice && _ttsOn == true;

    private async Task StartCaptureAsync(int? requiredGeneration)
    {
        // P4-LOCK: every capture path refuses while the system gate holds — P4-D02
        if (RefuseIfGated(GateRefuseCaptureStart))
        {
            return;
        }

        // P2-VOICE: voice.record always carries the current runtime session id — P2-D01
        if (string.IsNullOrEmpty(_chat.SessionId))
        {
            return;
        }

        // P4-ASK: a new wake capture is a fresh turn — never bind it to a prior cancelled clarify — P4-D14
        if (requiredGeneration is null)
        {
            ClearClosedClarifyCapture();
        }

        // P2-SPEAK: a stale follow-up must not send voice.record after any await — P2-D06
        if (requiredGeneration is int generation && generation != Volatile.Read(ref _followUpGeneration))
        {
            return;
        }

        // P2-WAKE: client-initiated captures await pause before voice.record; wake.detected already paused — P2-D12
        var wakeGeneration = Volatile.Read(ref _connectionGeneration);
        await PauseWakeForCaptureAsync(wakeGeneration).ConfigureAwait(false);
        if (requiredGeneration is int afterPause && afterPause != Volatile.Read(ref _followUpGeneration))
        {
            return;
        }

        if (wakeGeneration != Volatile.Read(ref _connectionGeneration))
        {
            WriteTimeline(NoticeStaleWake);
            _pendingClarifyCaptureId = null;
            await RecoverWakeCaptureIfNeededAsync(wakeGeneration).ConfigureAwait(false);
            return;
        }

        var reply = await RecordAsync(ActionStart, allowResync: true, requiredGeneration).ConfigureAwait(false);
        if (requiredGeneration is int afterAwait && afterAwait != Volatile.Read(ref _followUpGeneration))
        {
            // P4-ASK: interrupt may bump generation after Hermes already started record — keep id for late drop — P4-D14
            StashClosedClarifyCapture(_pendingClarifyCaptureId);
            _pendingClarifyCaptureId = null;
            return;
        }

        if (IsBusy(reply))
        {
            ReportBusy(reply);
            await RecoverWakeCaptureIfNeededAsync(wakeGeneration).ConfigureAwait(false);
            if (requiredGeneration is not null)
            {
                // P2-WAKE: a failed follow-up listen must not leave Resting blocked — P2-D12
                CancelFollowUp("follow-up-record-failed");
            }
            else
            {
                _pendingClarifyCaptureId = null;
            }

            return;
        }

        if (!reply.Ok)
        {
            StatusMessage?.Invoke(reply.Error ?? "Voice recording did not start.");
            await RecoverWakeCaptureIfNeededAsync(wakeGeneration).ConfigureAwait(false);
            if (requiredGeneration is not null)
            {
                // P2-WAKE: a failed follow-up listen must not leave Resting blocked — P2-D12
                CancelFollowUp("follow-up-record-failed");
            }
            else
            {
                _pendingClarifyCaptureId = null;
            }

            return;
        }

        CaptureActive = true;
        // P4-FEEDBACK: capture window opens on successful voice.record start — P4-D18
        NoteCaptureWindowStarted();
        // P2-WAKE: a successful record start confirms the wake capture; do not resume — P2-D12
        _wakeCapturePending = false;
        // P4-ASK: bind this capture to the armed clarify id (if any); otherwise unbound — P4-D14
        _activeClarifyCaptureId = _pendingClarifyCaptureId;
        _pendingClarifyCaptureId = null;
        if (RecorderState == StateIdle)
        {
            RecorderState = StateListening;
        }

        if (requiredGeneration is not null)
        {
            _followUpCaptureStarted = true;
        }

        StateChanged?.Invoke();
    }

    private async Task StopCaptureAsync()
    {
        // P2-VOICE: stop forces transcription; capture stays active until voice.status idle — P2-D05
        var reply = await RecordAsync(ActionStop, allowResync: true, requiredGeneration: null).ConfigureAwait(false);
        if (IsBusy(reply))
        {
            ReportBusy(reply);
            return;
        }

        if (!reply.Ok)
        {
            StatusMessage?.Invoke(reply.Error ?? "Voice recording did not stop.");
        }
    }

    private async Task<ChatSocket.RpcReply> RecordAsync(string action, bool allowResync, int? requiredGeneration)
    {
        // P2-SPEAK: the generation check sits immediately before each voice.record start — P2-D06
        if (requiredGeneration is int beforeFirst && beforeFirst != Volatile.Read(ref _followUpGeneration))
        {
            return new ChatSocket.RpcReply(false, "stale follow-up", null, null, null);
        }

        // P2-VOICE: a voice-off error re-syncs once, then the same failure is shown — P2-D07
        var reply = await _chat.InvokeAsync(MethodRecord, RecordParameters(action)).ConfigureAwait(false);
        if (reply.Ok || !allowResync)
        {
            return reply;
        }

        await SyncVoiceModeAsync().ConfigureAwait(false);
        if (Mode != ModeVoice || !IsAvailable)
        {
            return reply;
        }

        if (requiredGeneration is int beforeRetry && beforeRetry != Volatile.Read(ref _followUpGeneration))
        {
            return reply;
        }

        return await _chat.InvokeAsync(MethodRecord, RecordParameters(action)).ConfigureAwait(false);
    }

    private Dictionary<string, string?> RecordParameters(string action)
    {
        // P2-VOICE: the session id is the runtime id from the latest session.create or session.resume — P2-D01
        return new Dictionary<string, string?>
        {
            [ParamAction] = action,
            [ParamSessionId] = _chat.SessionId,
        };
    }

    private async Task<ChatSocket.RpcReply> ToggleAsync(string action)
    {
        // P2-SPEAK: status, on, off, and tts share this send; tts is requested only after a false status — P2-D03
        var reply = await _chat.InvokeAsync(MethodToggle, new Dictionary<string, string?>
        {
            [ParamAction] = action,
        }).ConfigureAwait(false);
        if (reply.Ok)
        {
            // P2-SPEAK: the clock uses the latest toggle tts flag and does not guess — P2-D06
            _ttsOn = reply.Tts;
        }

        return reply;
    }

    private void OnVoiceStatus(string state)
    {
        // P2-VOICE: capture is active from a successful start until the recorder reports idle — P2-D08
        RecorderState = string.IsNullOrEmpty(state) ? StateIdle : state;
        if (RecorderState == StateIdle)
        {
            CaptureActive = false;
            // P4-FEEDBACK: capture window closes on idle — P4-D18
            NoteCaptureWindowStopped();
            // P2-SPEAK: a silent follow-up ends on Hermes's 15 s no-speech timeout and returns to Idle — P2-D06
            if (_followUpCaptureStarted && !_followUpTranscriptSeen)
            {
                // P2-WAKE: one 15s silence is idle + empty STT, not no_speech_limit (that takes three); end the window so Resting can resume — P2-D12
                _followUpEchoPending = true;
                CancelFollowUp("follow-up-idle");
            }

            // P2-WAKE: idle ends a capture; resume only if we are actually Resting — P2-D12
            _ = ReconcileWakeRestingAsync("capture-idle");
        }
        else if (RecorderState == StateListening || RecorderState == StateTranscribing)
        {
            CaptureActive = true;
            if (RecorderState == StateListening)
            {
                // P2-WAKE: listening confirms the wake-started capture so recovery does not resume — P2-D12
                _wakeCapturePending = false;
            }
        }

        StateChanged?.Invoke();
    }

    private void OnVoiceTranscript(ChatSocket.VoiceTranscript transcript)
    {
        // P4-FEEDBACK: log every transcript (length + flags + window; never text) — P4-D18
        LogVoiceTranscript(transcript);

        // P4-LOCK: drop any transcript that arrives while gated; never raise TranscriptReady — P4-D02
        if (VoiceGated)
        {
            WriteTimeline(GateRefusePrefix + GateRefuseTranscript);
            return;
        }

        if (transcript.IsStopPhrase)
        {
            // P2-VOICE: Hermes already turned voice off; syncing turns it back on for the next capture — P2-D05
            CancelFollowUp("voice.transcript");
            VoiceChatEnded?.Invoke();
            _ = ResyncAfterStopAsync();
            return;
        }

        if (transcript.IsNoSpeechLimit)
        {
            // P2-VOICE: three silent captures are a status line, not a turn — P2-D05
            CancelFollowUp("no-speech");
            StatusMessage?.Invoke(NoticeNoSpeech);
            return;
        }

        if (transcript.Text.Trim().Length > 0)
        {
            // P2-SPEAK: only a follow-up capture may drop an echo of the reply that just finished — P2-D12
            var echoEligible = _followUpCaptureStarted || _followUpEchoPending;
            if (echoEligible && IsEchoOfLastReply(transcript.Text))
            {
                WriteTimeline($"echo-ignored words={string.Join(' ', NormalizeSpokenWords(transcript.Text))}");
                StatusMessage?.Invoke(NoticeIgnoredEcho);
                _followUpEchoPending = false;
                if (!_followUpCaptureStarted || !_followUpArmed)
                {
                    return;
                }

                _followUpCaptureStarted = false;
                _echoIgnoreCount++;
                // P2-SPEAK: an ignored tail must not consume the follow-up window; reopen listen for the user — P2-D12
                if (_echoIgnoreCount > EchoReopenLimit)
                {
                    CancelFollowUp("echo-ignored-limit");
                    return;
                }

                var generation = Volatile.Read(ref _followUpGeneration);
                _ = ReopenFollowUpAfterEchoAsync(generation);
                return;
            }

            _followUpEchoPending = false;
            _followUpTranscriptSeen = true;
            // P4-ASK: prefer live binding; else closed id from Cancel so late answers drop (C4) — P4-D14
            var boundClarifyId = _activeClarifyCaptureId;
            if (string.IsNullOrEmpty(boundClarifyId))
            {
                boundClarifyId = _closedClarifyCaptureId;
            }

            _activeClarifyCaptureId = null;
            if (!string.IsNullOrEmpty(boundClarifyId)
                && string.Equals(boundClarifyId, _closedClarifyCaptureId, StringComparison.Ordinal))
            {
                ClearClosedClarifyCapture();
            }

            // P2-SPEAK: a transcript is a new utterance, so the pending follow-up is cancelled — P2-D06
            CancelFollowUp("voice.transcript");
            // P2-VOICE: a non-empty transcript is submitted once by the window — P2-D05
            TranscriptReady?.Invoke(transcript.Text.Trim(), boundClarifyId);
        }
    }

    // P4-FEEDBACK: capture window bookkeeping for transcript lines — P4-D18
    private void NoteCaptureWindowStarted()
    {
        _captureWindowStart = DateTimeOffset.Now;
        _captureWindowStop = default;
        _captureWindowOpen = true;
    }

    private void NoteCaptureWindowStopped()
    {
        if (!_captureWindowOpen)
        {
            return;
        }

        _captureWindowStop = DateTimeOffset.Now;
        _captureWindowOpen = false;
    }

    private void LogVoiceTranscript(ChatSocket.VoiceTranscript transcript)
    {
        var stop = _captureWindowOpen ? DateTimeOffset.Now : _captureWindowStop;
        if (_captureWindowOpen)
        {
            NoteCaptureWindowStopped();
            stop = _captureWindowStop;
        }

        var bound = _activeClarifyCaptureId ?? _closedClarifyCaptureId;
        if (string.IsNullOrEmpty(bound))
        {
            bound = TranscriptBoundNone;
        }

        var startText = _captureWindowStart == default ? "" : _captureWindowStart.ToString("o");
        var stopText = stop == default ? "" : stop.ToString("o");
        var duration = "";
        if (_captureWindowStart != default && stop != default)
        {
            duration = (stop - _captureWindowStart).TotalSeconds.ToString("0.###");
        }

        WriteTimeline(string.Format(
            TranscriptLogFormat,
            transcript.Text?.Length ?? 0,
            transcript.Filtered ? GateBoolTrue : GateBoolFalse,
            transcript.IsStopPhrase ? GateBoolTrue : GateBoolFalse,
            transcript.IsNoSpeechLimit ? GateBoolTrue : GateBoolFalse,
            bound,
            startText,
            stopText,
            duration));
    }

    private async Task ReopenFollowUpAfterEchoAsync(int generation)
    {
        // P2-SPEAK: wait a beat so the spent echo capture goes idle, then listen again — P2-D12
        await Task.Delay(TimeSpan.FromSeconds(EchoReopenDelaySeconds)).ConfigureAwait(false);
        if (generation != Volatile.Read(ref _followUpGeneration))
        {
            return;
        }

        // P4-LOCK: echo reopen must not start a capture while gated — P4-D02
        if (RefuseIfGated(GateRefuseEchoReopen))
        {
            return;
        }

        if (Mode != ModeVoice || !IsAvailable || TurnRunning)
        {
            WriteTimeline("echo-reopen skipped");
            return;
        }

        WriteTimeline($"echo-reopen count={_echoIgnoreCount}");
        await StartCaptureAsync(generation).ConfigureAwait(false);
    }

    private async Task ResyncAfterStopAsync()
    {
        // P4-LOCK: stop-phrase resync must not turn voice back on while gated — P4-D02
        if (RefuseIfGated(GateRefuseResyncStop))
        {
            return;
        }

        // P2-VOICE: the stop phrase ends the exchange and Voice mode is armed again — P2-D05
        try
        {
            await SyncVoiceModeAsync().ConfigureAwait(false);
        }
        catch (ChatUnreachableException ex)
        {
            StatusMessage?.Invoke(ex.Message);
        }
    }

    private void OnVoiceInterrupted()
    {
        // P2-SPEAK: barge-in ends the speaking estimate and counts toward the bleed-loop pause — P2-D12
        CancelFollowUp("voice.interrupted");
        _selfInterruptCount++;
        if (_selfInterruptCount >= SelfInterruptLimit)
        {
            ResetSelfInterruptCount();
            StatusMessage?.Invoke(NoticeVoicePaused);
            _ = EnterTextModeAsync();
            return;
        }

        // P2-SPEAK: the interjection still arrives as its own transcript and is submitted by the existing path — P2-D05
        StatusMessage?.Invoke(NoticeInterrupted);
    }

    private async Task OnFollowUpTimerAsync(int generation)
    {
        // P2-SPEAK: generation is checked at fire and again immediately before voice.record start — P2-D06
        SetSpeaking(false);
        if (generation != Volatile.Read(ref _followUpGeneration))
        {
            return;
        }

        // P4-LOCK: follow-up timer must not open the mic while gated — P4-D02
        if (RefuseIfGated(GateRefuseFollowUp))
        {
            return;
        }

        if (Mode != ModeVoice || !IsAvailable || CaptureActive || TurnRunning)
        {
            WriteTimelineLine(started: false, fireOrCancel: "ineligible");
            return;
        }

        WriteTimelineLine(started: true, fireOrCancel: DateTimeOffset.Now.ToString("o"));
        await StartCaptureAsync(generation).ConfigureAwait(false);
    }

    private void CancelFollowUp(string reason)
    {
        // P2-SPEAK: every cancel cause bumps generation so a later timer cannot start a capture — P2-D06
        BumpFollowUpGeneration();
        DisposeFollowUpTimer();
        // P4-FEEDBACK: cancel reply release arm with the follow-up — P4-D18
        ClearReplyFollowUpRelease();
        if (_followUpArmed && string.IsNullOrEmpty(_cancelReason))
        {
            _cancelReason = reason;
            WriteTimelineLine(started: false, fireOrCancel: reason);
        }

        _followUpArmed = false;
        // P2-WAKE: Resting also requires this flag off; leaving it true ignores later detections as follow-up — P2-D12
        _followUpCaptureStarted = false;
        // P4-ASK: stash closed id only on interrupt-like cancel (not idle/silence — that stole the next wake turn) — P4-D14
        if (ShouldStashClosedClarify(reason))
        {
            StashClosedClarifyCapture(_activeClarifyCaptureId ?? _pendingClarifyCaptureId);
        }

        _pendingClarifyCaptureId = null;
        _activeClarifyCaptureId = null;
        SetSpeaking(false);
        // P2-WAKE: ending the follow-up window can re-enter Resting — P2-D12
        _ = ReconcileWakeRestingAsync("follow-up-end");
    }

    private void BumpFollowUpGeneration()
    {
        Interlocked.Increment(ref _followUpGeneration);
    }

    private void DisposeFollowUpTimer()
    {
        lock (_clockGate)
        {
            _followUpTimer?.Dispose();
            _followUpTimer = null;
        }
    }

    private void SetSpeaking(bool value)
    {
        var previous = Speaking;
        if (_speakingEstimate == value)
        {
            return;
        }

        _speakingEstimate = value;
        if (Speaking == previous)
        {
            return;
        }

        StateChanged?.Invoke();
        // P2-WAKE: Speaking starting leaves Resting; the estimate ending may re-enter it — P2-D12
        _ = ReconcileWakeRestingAsync(Speaking ? "speaking-start" : "speaking-end");
    }

    // P4-FEEDBACK: arm reply bout wait; Speaking stays held via _replyReleaseArmed — P4-D18
    private void ArmReplyFollowUpRelease()
    {
        var previous = Speaking;
        CancelReplyQuietWait();
        // P4-FEEDBACK: arm before seed so a stop between check and seed still hits NotePlaybackBoutStopped — P4-D18
        _replyReleaseArmed = true;
        _replyBoutSeen = false;
        _replyBoutActive = false;
        _replyBoutStartedTcs = new TaskCompletionSource<bool>(TaskCreationOptions.RunContinuationsAsynchronously);
        _replyBoutStoppedTcs = new TaskCompletionSource<bool>(TaskCreationOptions.RunContinuationsAsynchronously);
        if (!_speakingEstimate)
        {
            _speakingEstimate = true;
        }

        if (Speaking != previous)
        {
            StateChanged?.Invoke();
            _ = ReconcileWakeRestingAsync("reply-release-arm");
        }

        // P4-FEEDBACK: seed if a bout is already playing at message.complete (streaming TTS) — P4-D18
        var monitorAvailable = _playbackMonitorAvailable?.Invoke() == true;
        if (monitorAvailable && _playbackBoutActive?.Invoke() == true)
        {
            _replyBoutSeen = true;
            _replyBoutActive = true;
            _replyBoutStartedTcs.TrySetResult(true);
            WriteTimeline("follow_up_release seeded_active_bout=true");
        }
    }

    private void ClearReplyFollowUpRelease()
    {
        var previous = Speaking;
        CancelReplyQuietWait();
        _replyReleaseArmed = false;
        _replyBoutSeen = false;
        _replyBoutActive = false;
        _replyBoutStartedTcs?.TrySetCanceled();
        _replyBoutStoppedTcs?.TrySetCanceled();
        _replyBoutStartedTcs = null;
        _replyBoutStoppedTcs = null;
        if (Speaking != previous)
        {
            StateChanged?.Invoke();
            _ = ReconcileWakeRestingAsync(Speaking ? "speaking-start" : "speaking-end");
        }
    }

    private void CancelReplyQuietWait()
    {
        try
        {
            _replyQuietCts?.Cancel();
        }
        catch (ObjectDisposedException)
        {
        }

        _replyQuietCts?.Dispose();
        _replyQuietCts = null;
    }

    private double EstimateFollowUpDelayFromCompleteSeconds()
    {
        var remaining = (_estimatedSpeechEnd - DateTimeOffset.Now).TotalSeconds;
        var uncapped = Math.Max(0, remaining) + FollowUpMarginSeconds;
        if (uncapped > FollowUpMaxDelaySeconds)
        {
            WriteTimeline($"WARN uncapped-follow-up-delay={uncapped:0.###}s capped={FollowUpMaxDelaySeconds}s");
        }

        return Math.Min(uncapped, FollowUpMaxDelaySeconds);
    }

    private bool IsReplyReleaseCurrent(int generation)
    {
        return _replyReleaseArmed && generation == Volatile.Read(ref _followUpGeneration);
    }

    // P4-FEEDBACK: open follow-up on monitor natural+quiet, or estimate fallbacks — P4-D18
    private async Task RunReplyFollowUpReleaseAsync(int generation)
    {
        try
        {
            if (!IsReplyReleaseCurrent(generation))
            {
                return;
            }

            var completeAt = _turnCompletedAt;
            var estimatedEnd = _estimatedSpeechEnd;
            var monitorAvailable = _playbackMonitorAvailable?.Invoke() == true;
            string rule;

            if (!monitorAvailable)
            {
                rule = FollowUpRuleMonitorUnavailable;
                var delay = EstimateFollowUpDelayFromCompleteSeconds();
                _timerDelaySeconds = delay;
                WriteTimeline(
                    LogFollowUpReleasePrefix + rule
                    + " complete=" + completeAt.ToString("o")
                    + " estimatedEnd=" + estimatedEnd.ToString("o")
                    + " delay_s=" + delay.ToString("0.###"));
                await Task.Delay(TimeSpan.FromSeconds(delay)).ConfigureAwait(false);
                if (!IsReplyReleaseCurrent(generation))
                {
                    return;
                }

                ClearReplyFollowUpRelease();
                await OnFollowUpTimerAsync(generation).ConfigureAwait(false);
                return;
            }

            var startedTcs = _replyBoutStartedTcs;
            var startup = Task.Delay(TimeSpan.FromSeconds(ReplyBoutStartupWindowSeconds));
            var startedWait = startedTcs?.Task ?? Task.FromResult(false);
            var winner = await Task.WhenAny(startedWait, startup).ConfigureAwait(false);
            if (!IsReplyReleaseCurrent(generation))
            {
                return;
            }

            if (winner == startedWait && _replyBoutSeen)
            {
                await WaitReplyBoutsThenOpenAsync(generation, completeAt, estimatedEnd).ConfigureAwait(false);
                return;
            }

            // No bout within startup window — estimate; late bout upgrades to monitor wait.
            rule = FollowUpRuleNoBoutEstimate;
            var estimateDelay = EstimateFollowUpDelayFromCompleteSeconds();
            _timerDelaySeconds = estimateDelay;
            WriteTimeline(
                LogFollowUpReleasePrefix + rule
                + " complete=" + completeAt.ToString("o")
                + " estimatedEnd=" + estimatedEnd.ToString("o")
                + " startup_s=" + ReplyBoutStartupWindowSeconds.ToString("0.###")
                + " delay_s=" + estimateDelay.ToString("0.###"));
            var estimateTask = Task.Delay(TimeSpan.FromSeconds(estimateDelay));
            while (true)
            {
                if (!IsReplyReleaseCurrent(generation))
                {
                    return;
                }

                if (_replyBoutSeen)
                {
                    await WaitReplyBoutsThenOpenAsync(generation, completeAt, estimatedEnd).ConfigureAwait(false);
                    return;
                }

                if (estimateTask.IsCompleted)
                {
                    if (!IsReplyReleaseCurrent(generation))
                    {
                        return;
                    }

                    ClearReplyFollowUpRelease();
                    await OnFollowUpTimerAsync(generation).ConfigureAwait(false);
                    return;
                }

                var lateStart = _replyBoutStartedTcs?.Task ?? Task.Delay(Timeout.Infinite);
                await Task.WhenAny(estimateTask, lateStart).ConfigureAwait(false);
            }
        }
        catch (TaskCanceledException)
        {
        }
    }

    private async Task WaitReplyBoutsThenOpenAsync(int generation, DateTimeOffset completeAt, DateTimeOffset estimatedEnd)
    {
        while (IsReplyReleaseCurrent(generation))
        {
            // Wait until a bout is active (or its stop TCS is pending).
            if (!_replyBoutActive)
            {
                var startedTcs = _replyBoutStartedTcs
                    ?? new TaskCompletionSource<bool>(TaskCreationOptions.RunContinuationsAsynchronously);
                _replyBoutStartedTcs = startedTcs;
                if (!startedTcs.Task.IsCompleted)
                {
                    try
                    {
                        await startedTcs.Task.ConfigureAwait(false);
                    }
                    catch (TaskCanceledException)
                    {
                        return;
                    }
                }

                if (!IsReplyReleaseCurrent(generation))
                {
                    return;
                }
            }

            var stoppedTcs = _replyBoutStoppedTcs
                ?? throw new InvalidOperationException("reply bout stopped TCS missing while bout active");
            bool forced;
            try
            {
                forced = await stoppedTcs.Task.ConfigureAwait(false);
            }
            catch (TaskCanceledException)
            {
                return;
            }

            if (!IsReplyReleaseCurrent(generation))
            {
                return;
            }

            if (forced)
            {
                var remaining = Math.Max(0, (estimatedEnd - DateTimeOffset.Now).TotalSeconds);
                _timerDelaySeconds = remaining;
                WriteTimeline(
                    LogFollowUpReleasePrefix + FollowUpRuleForcedEstimate
                    + " complete=" + completeAt.ToString("o")
                    + " estimatedEnd=" + estimatedEnd.ToString("o")
                    + " remaining_s=" + remaining.ToString("0.###"));
                if (remaining > 0)
                {
                    await Task.Delay(TimeSpan.FromSeconds(remaining)).ConfigureAwait(false);
                }

                if (!IsReplyReleaseCurrent(generation))
                {
                    return;
                }

                ClearReplyFollowUpRelease();
                await OnFollowUpTimerAsync(generation).ConfigureAwait(false);
                return;
            }

            // Natural stop — quiet window; a new bout restarts the wait.
            var boutStoppedAt = DateTimeOffset.Now;
            while (IsReplyReleaseCurrent(generation))
            {
                CancelReplyQuietWait();
                _replyBoutStartedTcs = new TaskCompletionSource<bool>(TaskCreationOptions.RunContinuationsAsynchronously);
                var boutDuringQuiet = _replyBoutStartedTcs.Task;
                var quietCts = new CancellationTokenSource();
                _replyQuietCts = quietCts;
                Task quietTask;
                try
                {
                    quietTask = Task.Delay(TimeSpan.FromSeconds(FollowUpPostBoutQuietSeconds), quietCts.Token);
                }
                catch (ObjectDisposedException)
                {
                    return;
                }

                await Task.WhenAny(quietTask, boutDuringQuiet).ConfigureAwait(false);
                if (!IsReplyReleaseCurrent(generation))
                {
                    return;
                }

                // P4-FEEDBACK: open only on a fully elapsed quiet with no bout; cancelled delay must not open — P4-D18
                if (quietTask.Status != TaskStatus.RanToCompletion || _replyBoutActive)
                {
                    // P4-FEEDBACK: sentence gap beat debounce — log gap for Probe telemetry — P4-D18 amendment 2
                    var gapMs = Math.Max(0, (DateTimeOffset.Now - boutStoppedAt).TotalMilliseconds);
                    WriteTimeline(
                        "follow_up_release quiet_restart gap_ms="
                        + gapMs.ToString("0", System.Globalization.CultureInfo.InvariantCulture));
                    // Cancelled quiet, or bout started during quiet — wait for that bout's stop.
                    break;
                }

                WriteTimeline(
                    LogFollowUpReleasePrefix + FollowUpRuleMonitor
                    + " complete=" + completeAt.ToString("o")
                    + " estimatedEnd=" + estimatedEnd.ToString("o")
                    + " bout_stop=" + DateTimeOffset.Now.ToString("o")
                    + " quiet_s=" + FollowUpPostBoutQuietSeconds.ToString("0.###")
                    + " fire=" + DateTimeOffset.Now.ToString("o"));
                ClearReplyFollowUpRelease();
                await OnFollowUpTimerAsync(generation).ConfigureAwait(false);
                return;
            }
        }
    }

    private void ResetSelfInterruptCount()
    {
        // P2-SPEAK: a completed turn, typed Send, or mode change means the loop did not continue — P2-D12
        _selfInterruptCount = 0;
    }

    private static int CountSpokenWords(string text)
    {
        // P2-SPEAK: fences and marks are stripped, then letter-or-digit tokens are counted once — P2-D06
        var withoutFences = FenceBlocks.Replace(text ?? "", " ");
        var stripped = MarkdownMarks.Replace(withoutFences, " ");
        var words = 0;
        foreach (var token in stripped.Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries))
        {
            if (!TokenHasLetterOrDigit(token))
            {
                continue;
            }

            if (IsSpokenTimeAbbrev(token))
            {
                // P2-WAKE: a.m./p.m. are two clock words so the follow-up does not open on the tail — P2-D12
                words += SpokenAbbrevWords;
                continue;
            }

            var digits = 0;
            foreach (var ch in token)
            {
                if (char.IsDigit(ch))
                {
                    digits++;
                }
            }

            if (digits > 0)
            {
                // P2-WAKE: SpokenDigitWeight is max(SpokenDigitWeightFloor, digitCount); echo haystack still stores one token — P2-D12
                words += Math.Max(SpokenDigitWeightFloor, digits);
                continue;
            }

            if (IsSpokenAcronym(token))
            {
                // P2-WAKE: SpokenAcronymPerLetter turns PDT into three clock words so follow-up waits out the spelled tail — P2-D12
                words += token.Length * SpokenAcronymPerLetter;
                continue;
            }

            words++;
        }

        return words;
    }

    private static bool TokenHasLetterOrDigit(string token)
    {
        foreach (var ch in token)
        {
            if (char.IsLetterOrDigit(ch))
            {
                return true;
            }
        }

        return false;
    }

    private static bool IsSpokenTimeAbbrev(string token)
    {
        // P2-WAKE: a.m. / p.m. / am / pm are the spoken abbrev, not other dotted tokens — P2-D12
        return SpokenTimeAbbrev.IsMatch(token);
    }

    private static bool IsSpokenAcronym(string token)
    {
        // P2-WAKE: all-caps 2–5 letters only; mixed case and one-letter tokens stay one clock word — P2-D12
        if (token.Length < SpokenAcronymMinLetters || token.Length > SpokenAcronymMaxLetters)
        {
            return false;
        }

        foreach (var ch in token)
        {
            if (!char.IsLetter(ch) || !char.IsUpper(ch))
            {
                return false;
            }
        }

        return true;
    }

    private static int CountSpokenSentences(string text)
    {
        // P2-SPEAK: completed sentences are counted from the accumulated reply the same way words are — P2-D06
        var withoutFences = FenceBlocks.Replace(text ?? "", " ");
        var stripped = MarkdownMarks.Replace(withoutFences, " ");
        return Regex.Matches(stripped, @"[.!?]+").Count;
    }

    private void RememberSpokenEcho(string reply)
    {
        // P2-WAKE: keep the last EchoLookbackWords of digit-free tokens across turns — P2-D12
        var words = NormalizeEchoWords(reply);
        if (words.Count == 0)
        {
            return;
        }

        var prior = NormalizeEchoWords(_echoHaystack);
        prior.AddRange(words);
        if (prior.Count > EchoLookbackWords)
        {
            prior = prior.GetRange(prior.Count - EchoLookbackWords, EchoLookbackWords);
        }

        _echoHaystack = string.Join(' ', prior);
    }

    private bool IsEchoOfLastReply(string transcript)
    {
        // P2-WAKE: drop only a ≥3-word gapped in-order run that is ≥0.60 of the transcript and ends near her last words — P2-D12
        var heard = NormalizeEchoWords(transcript);
        if (heard.Count < EchoMinContiguousWords)
        {
            return false;
        }

        var tail = NormalizeEchoWords(string.IsNullOrEmpty(_echoHaystack) ? _accumulatedReply : _echoHaystack);
        if (tail.Count > EchoLookbackWords)
        {
            tail = tail.GetRange(tail.Count - EchoLookbackWords, EchoLookbackWords);
        }

        var run = LongestGappedSpokenRun(tail, heard, EchoMaxGapWords);
        if (run.Length < EchoMinContiguousWords)
        {
            return false;
        }

        if (run.Length / (double)heard.Count < EchoAnchoredRatio)
        {
            return false;
        }

        var slack = Math.Max(EchoEndSlackWords, (int)Math.Ceiling(EchoEndSlackRatio * heard.Count));
        return run.EndIndex >= tail.Count - slack;
    }

    private readonly struct SpokenRun
    {
        public SpokenRun(int length, int endIndex)
        {
            Length = length;
            EndIndex = endIndex;
        }

        public int Length { get; }
        public int EndIndex { get; }
    }

    private static SpokenRun LongestGappedSpokenRun(List<string> haystack, List<string> needle, int maxGap)
    {
        // P2-WAKE: in-order match with at most one unmatched word on either side; ties take the rightmost end — P2-D12
        var longest = 0;
        var endIndex = -1;
        for (var i0 = 0; i0 < needle.Count; i0++)
        {
            for (var j0 = 0; j0 < haystack.Count; j0++)
            {
                if (!string.Equals(needle[i0], haystack[j0], StringComparison.Ordinal))
                {
                    continue;
                }

                WalkGappedRun(haystack, needle, maxGap, i0, j0, 0, 1, j0, ref longest, ref endIndex);
            }
        }

        return new SpokenRun(longest, endIndex);
    }

    private static void WalkGappedRun(
        List<string> haystack,
        List<string> needle,
        int maxGap,
        int i,
        int j,
        int gaps,
        int matched,
        int end,
        ref int longest,
        ref int endIndex)
    {
        if (matched > longest || (matched == longest && end > endIndex))
        {
            longest = matched;
            endIndex = end;
        }

        if (i + 1 < needle.Count && j + 1 < haystack.Count
            && string.Equals(needle[i + 1], haystack[j + 1], StringComparison.Ordinal))
        {
            WalkGappedRun(haystack, needle, maxGap, i + 1, j + 1, gaps, matched + 1, j + 1, ref longest, ref endIndex);
        }

        if (gaps >= maxGap)
        {
            return;
        }

        if (i + 1 < needle.Count && j + 2 < haystack.Count
            && string.Equals(needle[i + 1], haystack[j + 2], StringComparison.Ordinal))
        {
            WalkGappedRun(haystack, needle, maxGap, i + 1, j + 2, gaps + 1, matched + 1, j + 2, ref longest, ref endIndex);
        }

        if (i + 2 < needle.Count && j + 1 < haystack.Count
            && string.Equals(needle[i + 2], haystack[j + 1], StringComparison.Ordinal))
        {
            WalkGappedRun(haystack, needle, maxGap, i + 2, j + 1, gaps + 1, matched + 1, j + 1, ref longest, ref endIndex);
        }
    }

    private static List<string> NormalizeSpokenWords(string text)
    {
        var cleaned = Regex.Replace((text ?? "").ToLowerInvariant(), @"[^a-z0-9\s]+", " ");
        var words = new List<string>();
        foreach (var token in cleaned.Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries))
        {
            words.Add(token);
        }

        return words;
    }

    private static List<string> NormalizeEchoWords(string text)
    {
        // P2-WAKE: list ranks, years, times, and markers are stripped so "8 2019" cannot hide a Super Bowl tail — P2-D12
        var cleaned = Regex.Replace((text ?? "").ToLowerInvariant(), @"[^a-z0-9\s]+", " ");
        var words = new List<string>();
        foreach (var token in cleaned.Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries))
        {
            if (EchoListMarker.IsMatch(token))
            {
                continue;
            }

            var hasDigit = false;
            foreach (var ch in token)
            {
                if (char.IsDigit(ch))
                {
                    hasDigit = true;
                    break;
                }
            }

            if (hasDigit)
            {
                continue;
            }

            words.Add(token);
        }

        return words;
    }

    private void WriteTimelineLine(bool started, string fireOrCancel)
    {
        // P2-SPEAK: one diagnostic line per spoken turn; a write failure must not affect voice — P2-D06
        var start = _turnStartedAt == default ? "" : _turnStartedAt.ToString("o");
        var complete = _turnCompletedAt == default ? "" : _turnCompletedAt.ToString("o");
        var estimate = _estimatedSpeechEnd == default ? "" : _estimatedSpeechEnd.ToString("o");
        WriteTimeline(
            $"start={start} complete={complete} estimatedEnd={estimate} delay={_timerDelaySeconds:0.###}s fireOrCancel={fireOrCancel} followUpStarted={started} words={_countedWords}");
    }

    private void WriteTimeline(string line)
    {
        try
        {
            var root = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), TimelineClientFolder, TimelineLogFolder);
            Directory.CreateDirectory(root);
            File.AppendAllText(Path.Combine(root, TimelineLogFile), DateTimeOffset.Now.ToString("o") + " " + line + Environment.NewLine);
        }
        catch
        {
        }
    }

    public async Task ArmWakeAsync(bool fromGateOpen = false)
    {
        // P4-LOCK: open-sequence arm passes fromGateOpen; still refuses if facts are gated — P4-D02 / P4-D03
        if (fromGateOpen)
        {
            if (SystemLocked || SystemSuspended)
            {
                WriteTimeline(GateRefusePrefix + GateRefuseArmWake);
                return;
            }
        }
        else if (RefuseIfGated(GateRefuseArmWake))
        {
            return;
        }

        // P2-WAKE: first wake.start may download the sherpa model inside this call — P2-D04
        var generation = Volatile.Read(ref _connectionGeneration);
        if (Mode != ModeVoice || !IsAvailable || string.IsNullOrEmpty(_chat.SessionId))
        {
            return;
        }

        WakeSettingUp = true;
        WakeHeldElsewhere = false;
        WakeUnavailable = false;
        var outcomeNotice = false;
        StatusMessage?.Invoke(NoticeSettingUpWake);
        StateChanged?.Invoke();
        try
        {
            for (var attempt = 1; attempt <= WakeOwnedRetryCount; attempt++)
            {
                if (generation != Volatile.Read(ref _connectionGeneration))
                {
                    WriteTimeline(NoticeStaleWake);
                    return;
                }

                if (attempt > 1)
                {
                    await Task.Delay(WakeOwnedRetryDelayMs).ConfigureAwait(false);
                    if (generation != Volatile.Read(ref _connectionGeneration))
                    {
                        WriteTimeline(NoticeStaleWake);
                        return;
                    }

                    // P4-LOCK: mid-retry relock must not complete wake.start from an open sequence — P4-D03
                    if (fromGateOpen && (SystemLocked || SystemSuspended))
                    {
                        WriteTimeline(GateRefusePrefix + GateRefuseArmWake);
                        return;
                    }
                }

                var startedAt = DateTimeOffset.Now;
                ChatSocket.RpcReply reply;
                try
                {
                    reply = await _chat.InvokeAsync(
                        MethodWakeStart,
                        new Dictionary<string, string?>
                        {
                            [ParamSurface] = SurfaceGui,
                            [ParamSessionId] = _chat.SessionId,
                        },
                        TimeSpan.FromSeconds(WakeStartTimeoutSeconds),
                        faultOnTimeout: false).ConfigureAwait(false);
                }
                catch (ChatUnreachableException ex)
                {
                    WriteTimeline("wake.start unreachable " + ex.Message);
                    await ReconcileWakeStatusAsync(generation).ConfigureAwait(false);
                    outcomeNotice = WakeAudioSilent && !string.IsNullOrEmpty(WakeHint);
                    return;
                }

                var duration = (DateTimeOffset.Now - startedAt).TotalSeconds;
                WriteTimeline($"wake.start attempt={attempt} duration={duration:0.###}s ok={reply.Ok} started={reply.Started} reason={reply.Reason} error={reply.Error}");
                if (generation != Volatile.Read(ref _connectionGeneration))
                {
                    WriteTimeline(NoticeStaleWake);
                    return;
                }

                if (string.Equals(reply.Error, ChatSocket.ErrorTimeout, StringComparison.Ordinal))
                {
                    // P2-WAKE: a timeout is not owned; reconcile listening from wake.status — P2-D04
                    await ReconcileWakeStatusAsync(generation).ConfigureAwait(false);
                    outcomeNotice = WakeAudioSilent && !string.IsNullOrEmpty(WakeHint);
                    return;
                }

                if (reply.Started == true)
                {
                    WakeArmed = true;
                    WakePaused = false;
                    WakeHeldElsewhere = false;
                    WakeUnavailable = false;
                    RecordWakeModelLanding(duration);
                    StateChanged?.Invoke();
                    return;
                }

                if (string.Equals(reply.Reason, ReasonOwned, StringComparison.Ordinal))
                {
                    continue;
                }

                if (reply.Reason is ReasonUnavailable or ReasonDisabled or ReasonDisabledForSurface)
                {
                    WakeUnavailable = true;
                    WakeHint = reply.Hint ?? reply.Reason ?? "";
                    StatusMessage?.Invoke(string.IsNullOrEmpty(WakeHint) ? (reply.Reason ?? ReasonUnavailable) : WakeHint);
                    outcomeNotice = true;
                    StateChanged?.Invoke();
                    return;
                }

                if (!reply.Ok)
                {
                    await ReconcileWakeStatusAsync(generation).ConfigureAwait(false);
                    outcomeNotice = WakeAudioSilent && !string.IsNullOrEmpty(WakeHint);
                    return;
                }
            }

            WakeHeldElsewhere = true;
            StatusMessage?.Invoke(NoticeWakeHeld);
            outcomeNotice = true;
            WriteTimeline(NoticeWakeHeld);
            StateChanged?.Invoke();
        }
        finally
        {
            // P2-WAKE: drop the pending setup line on success, refusal, timeout, or stale — P2-D08
            WakeSettingUp = false;
            if (generation == Volatile.Read(ref _connectionGeneration) && !outcomeNotice)
            {
                StatusMessage?.Invoke(NoticeSessionReady);
            }

            StateChanged?.Invoke();
        }
    }

    public async Task DisarmWakeAsync()
    {
        // P2-WAKE: wake.stop has no persist; flags clear only on confirmation or a dead socket — P2-D04
        var generation = Volatile.Read(ref _connectionGeneration);
        if (_chat.SessionId is null)
        {
            WakeArmed = false;
            WakePaused = false;
            StateChanged?.Invoke();
            return;
        }

        ChatSocket.RpcReply reply;
        try
        {
            reply = await _chat.InvokeAsync(MethodWakeStop, new Dictionary<string, string?>()).ConfigureAwait(false);
        }
        catch (ChatUnreachableException)
        {
            WakeArmed = false;
            WakePaused = false;
            StateChanged?.Invoke();
            return;
        }

        if (generation != Volatile.Read(ref _connectionGeneration))
        {
            WriteTimeline(NoticeStaleWake);
            return;
        }

        if (reply.Ok && reply.Stopped != false)
        {
            WakeArmed = false;
            WakePaused = false;
            WakeHeldElsewhere = false;
            StateChanged?.Invoke();
        }
    }

    private async Task ReconcileWakeRestingAsync(string reason)
    {
        // P2-WAKE: one method owns pause and resume; Resting is re-checked after every await — P2-D12
        // P4-FEEDBACK: single-flight + post-await converge so concurrent stop-speaking-complete / turn-end cannot no-op — P4-FB-STOP
        _wakeReconcileReason = reason;
        if (Interlocked.Exchange(ref _wakeReconcileBusy, 1) == 1)
        {
            Volatile.Write(ref _wakeReconcilePending, 1);
            return;
        }

        try
        {
            for (var pass = 1; pass <= 3; pass++)
            {
                Interlocked.Exchange(ref _wakeReconcilePending, 0);
                var passReason = _wakeReconcileReason;
                if (pass > 1)
                {
                    WriteTimeline($"wake reconcile pass={pass} reason={passReason}");
                }

                var generation = Volatile.Read(ref _connectionGeneration);
                if (!WakeArmed || generation != Volatile.Read(ref _connectionGeneration))
                {
                    return;
                }

                try
                {
                    if (!Resting && !WakePaused)
                    {
                        await PauseWakeAsync(passReason, generation).ConfigureAwait(false);
                    }
                    else if (Resting && WakePaused)
                    {
                        // P4-LOCK: Resting auto-resume must not reopen the mic behind the gate — P4-D02
                        if (RefuseIfGated(GateRefuseWakeReconcileResume))
                        {
                            return;
                        }

                        await ResumeWakeAsync(passReason, generation).ConfigureAwait(false);
                    }

                    generation = Volatile.Read(ref _connectionGeneration);
                    if (!WakeArmed || generation != Volatile.Read(ref _connectionGeneration))
                    {
                        return;
                    }

                    var converged = (Resting && !WakePaused) || (!Resting && WakePaused);
                    var pending = Volatile.Read(ref _wakeReconcilePending) == 1;
                    if (converged && !pending)
                    {
                        return;
                    }
                }
                catch (ChatUnreachableException ex)
                {
                    WriteTimeline("wake reconcile unreachable " + ex.Message);
                    return;
                }
            }

            WriteTimeline("wake reconcile not converged");
        }
        finally
        {
            Interlocked.Exchange(ref _wakeReconcileBusy, 0);
            if (Interlocked.Exchange(ref _wakeReconcilePending, 0) == 1)
            {
                _ = ReconcileWakeRestingAsync(_wakeReconcileReason);
            }
        }
    }

    private async Task PauseWakeForCaptureAsync(int generation)
    {
        // P2-WAKE: mic, hotkey, and follow-up await pause; skip when Hermes already paused on detect — P2-D12
        if (!WakeArmed || WakePaused)
        {
            return;
        }

        await PauseWakeAsync("capture", generation).ConfigureAwait(false);
    }

    private async Task PauseWakeAsync(string reason, int generation)
    {
        if (generation != Volatile.Read(ref _connectionGeneration) || !WakeArmed || WakePaused)
        {
            return;
        }

        var reply = await _chat.InvokeAsync(MethodWakePause, new Dictionary<string, string?>()).ConfigureAwait(false);
        if (generation != Volatile.Read(ref _connectionGeneration))
        {
            WriteTimeline(NoticeStaleWake);
            return;
        }

        if (reply.Paused == true)
        {
            WakePaused = true;
            WriteTimeline($"wake.pause reason={reason}");
            StateChanged?.Invoke();
            return;
        }

        if (!reply.Ok)
        {
            await ReconcileWakeStatusAsync(generation).ConfigureAwait(false);
        }
    }

    private async Task ResumeWakeAsync(string reason, int generation)
    {
        // P4-LOCK: every wake.resume path refuses while gated — P4-D02
        if (RefuseIfGated(GateRefuseWakeResume))
        {
            return;
        }

        if (generation != Volatile.Read(ref _connectionGeneration))
        {
            WriteTimeline(NoticeStaleWake);
            return;
        }

        // P2-WAKE: Resting is re-checked immediately before wake.resume so a stale resume cannot re-open — P2-D12
        if (!Resting || !WakeArmed || !WakePaused)
        {
            return;
        }

        var reply = await _chat.InvokeAsync(MethodWakeResume, new Dictionary<string, string?>()).ConfigureAwait(false);
        if (generation != Volatile.Read(ref _connectionGeneration))
        {
            WriteTimeline(NoticeStaleWake);
            return;
        }

        if (!Resting)
        {
            WriteTimeline($"wake.resume skipped after await reason={reason}");
            return;
        }

        if (reply.Resumed == true)
        {
            WakePaused = false;
            WriteTimeline($"wake.resume reason={reason}");
            StateChanged?.Invoke();
            if (!Resting)
            {
                // P2-WAKE: a resume that landed after Resting ended is paused again — P2-D12
                await PauseWakeAsync("stale-resume", generation).ConfigureAwait(false);
            }

            return;
        }

        if (!reply.Ok)
        {
            await ReconcileWakeStatusAsync(generation).ConfigureAwait(false);
        }
    }

    private async Task ReconcileWakeStatusAsync(int generation)
    {
        // P2-WAKE: failed or timed-out wake.start reads listening from status, never owned-retry — P2-D04
        if (generation != Volatile.Read(ref _connectionGeneration))
        {
            WriteTimeline(NoticeStaleWake);
            return;
        }

        ChatSocket.RpcReply reply;
        try
        {
            reply = await _chat.InvokeAsync(
                MethodWakeStatus,
                new Dictionary<string, string?> { [ParamSurface] = SurfaceGui }).ConfigureAwait(false);
        }
        catch (ChatUnreachableException ex)
        {
            WriteTimeline("wake.status unreachable " + ex.Message);
            return;
        }

        if (generation != Volatile.Read(ref _connectionGeneration))
        {
            WriteTimeline(NoticeStaleWake);
            return;
        }

        if (!reply.Ok)
        {
            return;
        }

        WakeArmed = reply.Listening == true && reply.OwnedByCaller == true;
        WakePaused = WakeArmed && reply.Listening != true;
        WakeHeldElsewhere = reply.OwnedByCaller == false && !string.IsNullOrEmpty(reply.Reason);
        WakeUnavailable = reply.Available == false;
        WakeAudioSilent = reply.AudioSilent == true;
        WakeHint = reply.Hint ?? "";
        if (WakeAudioSilent && !string.IsNullOrEmpty(WakeHint))
        {
            StatusMessage?.Invoke(WakeHint);
        }

        WriteTimeline($"wake.status listening={reply.Listening} owned={reply.OwnedByCaller} available={reply.Available} silent={reply.AudioSilent}");
        StateChanged?.Invoke();
    }

    private void OnWakeDetected(string phrase, string? profile, bool startNewSession)
    {
        // P2-WAKE: start_new_session is ignored; the current session continues — P2-D04
        _ = HandleWakeDetectedAsync(phrase, profile);
    }

    private async Task HandleWakeDetectedAsync(string phrase, string? profile)
    {
        var generation = Volatile.Read(ref _connectionGeneration);
        // P2-WAKE: Hermes paused before emit, so this event confirms WakePaused — P2-D04
        WakePaused = true;
        StateChanged?.Invoke();
        if (generation != Volatile.Read(ref _connectionGeneration))
        {
            WriteTimeline(NoticeStaleWake);
            return;
        }

        // P4-LOCK: wake.detected must not start a capture while gated — P4-D02
        if (RefuseIfGated(GateRefuseWakeDetected))
        {
            return;
        }

        if (!Resting)
        {
            var state = DescribeBusyState();
            WriteTimeline($"wake ignored: {state} phrase={phrase} profile={profile}");
            return;
        }

        WriteTimeline($"wake.detected phrase={phrase} profile={profile}");
        _wakeCapturePending = true;
        try
        {
            await StartCaptureAsync(requiredGeneration: null).ConfigureAwait(false);
        }
        catch (ChatUnreachableException ex)
        {
            StatusMessage?.Invoke(ex.Message);
            await RecoverWakeCaptureIfNeededAsync(generation).ConfigureAwait(false);
        }

        if (_wakeCapturePending)
        {
            await RecoverWakeCaptureIfNeededAsync(generation).ConfigureAwait(false);
        }
    }

    private async Task RecoverWakeCaptureIfNeededAsync(int generation)
    {
        if (!_wakeCapturePending)
        {
            return;
        }

        _wakeCapturePending = false;
        if (generation != Volatile.Read(ref _connectionGeneration))
        {
            WriteTimeline(NoticeStaleWake);
            return;
        }

        if (Resting && WakeArmed && WakePaused)
        {
            await ResumeWakeAsync("capture-failed", generation).ConfigureAwait(false);
            StatusMessage?.Invoke(NoticeWakeMissed);
        }
    }

    private string DescribeBusyState()
    {
        if (Mode != ModeVoice)
        {
            return "text";
        }

        if (CaptureActive)
        {
            return "capture";
        }

        if (TurnRunning)
        {
            return "turn";
        }

        if (Speaking)
        {
            return "speaking";
        }

        if (_followUpArmed || _followUpCaptureStarted)
        {
            return "follow-up";
        }

        return "not-resting";
    }

    private void BumpConnectionGeneration()
    {
        // P2-WAKE: a new generation drops confirmed flags that belonged to the previous socket or mode — P2-D04
        Interlocked.Increment(ref _connectionGeneration);
        WakeArmed = false;
        WakePaused = false;
        WakeHeldElsewhere = false;
        WakeUnavailable = false;
        WakeSettingUp = false;
        WakeAudioSilent = false;
        _wakeCapturePending = false;
        _followUpEchoPending = false;
        _echoHaystack = "";
    }

    private void RecordWakeModelLanding(double durationSeconds)
    {
        var tokens = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "hermes",
            "profiles",
            "zola",
            WakeModelRelativePath);
        WriteTimeline($"wake.model duration={durationSeconds:0.###}s tokens={(File.Exists(tokens) ? tokens : "missing")}");
    }

    private void MarkUnavailable(string details)
    {
        // P2-VOICE: the probe details are what the status line shows — P2-D07
        IsAvailable = false;
        UnavailableDetails = details;
        // P2-WAKE: unavailable Voice is Text; drop unconfirmed wake flags with the generation — P2-D07
        BumpConnectionGeneration();
        Mode = ModeText;
        CaptureActive = false;
        StateChanged?.Invoke();
    }

    private static bool IsBusy(ChatSocket.RpcReply reply)
    {
        // P2-VOICE: busy and wake-owned are status, not exceptions — P2-D01
        return reply.Ok && string.Equals(reply.Status, RecordBusy, StringComparison.Ordinal);
    }

    private void ReportBusy(ChatSocket.RpcReply reply)
    {
        // P2-VOICE: wake-owned is the same busy result with a reason the status line can show — P2-D01
        var wakeOwned = string.Equals(reply.Reason, ReasonWakeOwned, StringComparison.Ordinal);
        StatusMessage?.Invoke(wakeOwned ? NoticeWakeOwned : NoticeBusy);
    }
}
