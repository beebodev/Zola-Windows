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
    private const double FirstSentenceLatencySeconds = 3.3;
    private const double PerSentenceOverheadSeconds = 0.5;
    private const double FollowUpMarginSeconds = 3.0;
    private const double FollowUpMaxDelaySeconds = 90;
    private const double MaxEstimatedSpeechSeconds = 300;
    // P3-STATE: unused bag-of-words echo constants are removed; the live rule is P2-D14 — P3-D15
    // P2-SPEAK: follow-up echo uses a tail bag-of-words check plus a short phrase run; 80% missed an STT split of unless — P2-D14
    private const int EchoLookbackWords = 20;
    private const int EchoReopenLimit = 3;
    private const double EchoReopenDelaySeconds = 0.5;
    // P2-WAKE: drop a follow-up only when a ≥3-word in-order run is ≥0.60 of it and ends near her last spoken words — P2-D14
    private const int EchoMinContiguousWords = 3;
    private const double EchoAnchoredRatio = 0.60;
    private const int EchoEndSlackWords = 3;
    // P2-WAKE: slack grows with a long transcript so a late STT tail still anchors — P2-D12
    private const double EchoEndSlackRatio = 0.25;
    // P2-WAKE: one unmatched word (hers or STT) may sit inside the run; two breaks it — P2-D12
    private const int EchoMaxGapWords = 1;
    // P2-WAKE: SpokenDigitWeight is max(SpokenDigitWeightFloor, digitCount) on the clock only — P2-D12
    private const int SpokenDigitWeightFloor = 1;
    private const int SpokenAbbrevWords = 2;
    // P2-WAKE: PDT/NFL/USA are spelled out on the clock; haystack still stores one token — P2-D12
    private const int SpokenAcronymPerLetter = 1;
    private const int SpokenAcronymMinLetters = 2;
    private const int SpokenAcronymMaxLetters = 5;
    private const string NoticeIgnoredEcho = "Ignored: that sounded like Zola's own voice.";
    // P2-SPEAK: three consecutive voice.interrupted trips with no complete in between pause Voice — P2-D12
    private const int SelfInterruptLimit = 3;
    // P2-SPEAK: one append-only line per spoken turn for Phase 5 measurement — P2-D06
    // P3-STATE: display-state.log shares this folder — P3-D03
    internal const string TimelineClientFolder = "ZolaClient";
    internal const string TimelineLogFolder = "logs";
    private const string TimelineLogFile = "voice-timeline.log";

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
    public bool Speaking { get; private set; }

    // P2-WAKE: armed and paused update only from confirmed Hermes replies or wake.detected — P2-D04
    public bool WakeArmed { get; private set; }

    public bool WakePaused { get; private set; }

    public bool WakeHeldElsewhere { get; private set; }

    public bool WakeUnavailable { get; private set; }

    public bool WakeSettingUp { get; private set; }

    public bool WakeAudioSilent { get; private set; }

    public string WakeHint { get; private set; } = "";

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
            return Mode == ModeVoice && IsAvailable && SessionReady && BackendReachable && !TurnRunning && !Speaking;
        }
    }

    public event Action? StateChanged;

    public event Action<string>? TranscriptReady;

    public event Action? VoiceChatEnded;

    public event Action<string>? StatusMessage;

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

    public async Task SyncVoiceModeAsync()
    {
        // P2-VOICE: each socket re-reads voice status and turns voice on only when it is off — P2-D07
        if (Mode != ModeVoice)
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
        BumpFollowUpGeneration();
        DisposeFollowUpTimer();
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
            if (!ClockEligible)
            {
                SetSpeaking(false);
                return;
            }

            _turnCompletedAt = DateTimeOffset.Now;
            RememberSpokenEcho(_accumulatedReply);
            var remaining = (_estimatedSpeechEnd - _turnCompletedAt).TotalSeconds;
            var uncapped = Math.Max(0, remaining) + FollowUpMarginSeconds;
            var delay = Math.Min(uncapped, FollowUpMaxDelaySeconds);
            _timerDelaySeconds = delay;
            if (uncapped > FollowUpMaxDelaySeconds)
            {
                WriteTimeline($"WARN uncapped-follow-up-delay={uncapped:0.###}s capped={FollowUpMaxDelaySeconds}s");
            }

            if ((_estimatedSpeechEnd - _turnStartedAt).TotalSeconds > MaxEstimatedSpeechSeconds)
            {
                WriteTimeline($"WARN estimated-speech={(_estimatedSpeechEnd - _turnStartedAt).TotalSeconds:0.###}s exceeds {MaxEstimatedSpeechSeconds}s");
            }

            var generation = _followUpGeneration;
            _followUpArmed = true;
            DisposeFollowUpTimer();
            _followUpTimer = new Timer(_ => _ = OnFollowUpTimerAsync(generation), null, TimeSpan.FromSeconds(delay), Timeout.InfiniteTimeSpan);
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
        // P2-VOICE: voice.record always carries the current runtime session id — P2-D01
        if (string.IsNullOrEmpty(_chat.SessionId))
        {
            return;
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
            await RecoverWakeCaptureIfNeededAsync(wakeGeneration).ConfigureAwait(false);
            return;
        }

        var reply = await RecordAsync(ActionStart, allowResync: true, requiredGeneration).ConfigureAwait(false);
        if (requiredGeneration is int afterAwait && afterAwait != Volatile.Read(ref _followUpGeneration))
        {
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

            return;
        }

        CaptureActive = true;
        // P2-WAKE: a successful record start confirms the wake capture; do not resume — P2-D12
        _wakeCapturePending = false;
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
            // P2-SPEAK: a transcript is a new utterance, so the pending follow-up is cancelled — P2-D06
            CancelFollowUp("voice.transcript");
            // P2-VOICE: a non-empty transcript is submitted once by the window — P2-D05
            TranscriptReady?.Invoke(transcript.Text.Trim());
        }
    }

    private async Task ReopenFollowUpAfterEchoAsync(int generation)
    {
        // P2-SPEAK: wait a beat so the spent echo capture goes idle, then listen again — P2-D12
        await Task.Delay(TimeSpan.FromSeconds(EchoReopenDelaySeconds)).ConfigureAwait(false);
        if (generation != Volatile.Read(ref _followUpGeneration))
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
        if (_followUpArmed && string.IsNullOrEmpty(_cancelReason))
        {
            _cancelReason = reason;
            WriteTimelineLine(started: false, fireOrCancel: reason);
        }

        _followUpArmed = false;
        // P2-WAKE: Resting also requires this flag off; leaving it true ignores later detections as follow-up — P2-D12
        _followUpCaptureStarted = false;
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
        if (Speaking == value)
        {
            return;
        }

        Speaking = value;
        StateChanged?.Invoke();
        // P2-WAKE: Speaking starting leaves Resting; the estimate ending may re-enter it — P2-D12
        _ = ReconcileWakeRestingAsync(value ? "speaking-start" : "speaking-end");
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

    public async Task ArmWakeAsync()
    {
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
        var generation = Volatile.Read(ref _connectionGeneration);
        if (!WakeArmed || generation != Volatile.Read(ref _connectionGeneration))
        {
            return;
        }

        try
        {
            if (!Resting && !WakePaused)
            {
                await PauseWakeAsync(reason, generation).ConfigureAwait(false);
                return;
            }

            if (Resting && WakePaused)
            {
                await ResumeWakeAsync(reason, generation).ConfigureAwait(false);
            }
        }
        catch (ChatUnreachableException ex)
        {
            WriteTimeline("wake reconcile unreachable " + ex.Message);
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
