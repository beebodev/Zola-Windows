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
    // P2-SPEAK: follow-up echo uses a tail bag-of-words check plus a short phrase run; 80% missed an STT split of unless — P2-D12
    private const double EchoContainmentRatio = 0.60;
    private const int EchoLookbackWords = 20;
    private const int EchoMinWords = 3;
    private const int EchoPhraseWords = 4;
    private const int EchoReopenLimit = 3;
    private const double EchoReopenDelaySeconds = 0.5;
    private const string NoticeIgnoredEcho = "Ignored: that sounded like Zola's own voice.";
    // P2-SPEAK: three consecutive voice.interrupted trips with no complete in between pause Voice — P2-D12
    private const int SelfInterruptLimit = 3;
    // P2-SPEAK: one append-only line per spoken turn for Phase 5 measurement — P2-D06
    private const string TimelineClientFolder = "ZolaClient";
    private const string TimelineLogFolder = "logs";
    private const string TimelineLogFile = "voice-timeline.log";

    private static readonly Regex FenceBlocks = new("```[\\s\\S]*?```", RegexOptions.Compiled);
    private static readonly Regex MarkdownMarks = new(@"[#*_`>\[\]\(\)]+", RegexOptions.Compiled);

    private readonly ChatSocket _chat;
    private readonly object _clockGate = new();
    private Timer? _followUpTimer;
    private int _followUpGeneration;
    private int _selfInterruptCount;
    private bool? _ttsOn;
    private bool _followUpArmed;
    private bool _followUpCaptureStarted;
    private bool _followUpTranscriptSeen;
    private int _echoIgnoreCount;
    private string _accumulatedReply = "";
    private int _countedWords;
    private int _countedSentences;
    private DateTimeOffset _turnStartedAt;
    private DateTimeOffset _estimatedSpeechEnd;
    private DateTimeOffset _turnCompletedAt;
    private double _timerDelaySeconds;
    private string _cancelReason = "";

    public VoiceController(ChatSocket chat)
    {
        // P2-VOICE: one controller listens on the window's existing socket — P2-D01
        _chat = chat;
        _chat.VoiceStatusChanged += OnVoiceStatus;
        _chat.VoiceTranscriptReceived += OnVoiceTranscript;
        _chat.VoiceInterrupted += OnVoiceInterrupted;
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

        Mode = ModeText;
        CaptureActive = false;
        RecorderState = StateIdle;
        StateChanged?.Invoke();
    }

    public async Task EnterVoiceModeAsync()
    {
        // P2-SPEAK: returning to Voice clears a leftover self-trip count — P2-D12
        ResetSelfInterruptCount();
        // P2-VOICE: switching back to Voice re-syncs this socket instead of restarting serve — P2-D07
        Mode = ModeVoice;
        await SyncVoiceModeAsync().ConfigureAwait(false);
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
        _echoIgnoreCount = 0;
        _cancelReason = "";
        _turnStartedAt = DateTimeOffset.Now;
        _turnCompletedAt = default;
        _timerDelaySeconds = 0;
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

        var reply = await RecordAsync(ActionStart, allowResync: true, requiredGeneration).ConfigureAwait(false);
        if (requiredGeneration is int afterAwait && afterAwait != Volatile.Read(ref _followUpGeneration))
        {
            return;
        }

        if (IsBusy(reply))
        {
            ReportBusy(reply);
            return;
        }

        if (!reply.Ok)
        {
            StatusMessage?.Invoke(reply.Error ?? "Voice recording did not start.");
            return;
        }

        CaptureActive = true;
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
                _followUpCaptureStarted = false;
                SetSpeaking(false);
            }
        }
        else if (RecorderState == StateListening || RecorderState == StateTranscribing)
        {
            CaptureActive = true;
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
            if (_followUpCaptureStarted && IsEchoOfLastReply(transcript.Text))
            {
                WriteTimeline($"echo-ignored words={string.Join(' ', NormalizeSpokenWords(transcript.Text))}");
                StatusMessage?.Invoke(NoticeIgnoredEcho);
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
        SetSpeaking(false);
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
            foreach (var ch in token)
            {
                if (char.IsLetterOrDigit(ch))
                {
                    words++;
                    break;
                }
            }
        }

        return words;
    }

    private static int CountSpokenSentences(string text)
    {
        // P2-SPEAK: completed sentences are counted from the accumulated reply the same way words are — P2-D06
        var withoutFences = FenceBlocks.Replace(text ?? "", " ");
        var stripped = MarkdownMarks.Replace(withoutFences, " ");
        return Regex.Matches(stripped, @"[.!?]+").Count;
    }

    private bool IsEchoOfLastReply(string transcript)
    {
        // P2-SPEAK: drop a follow-up whose words or a short phrase already sit in Zola's last spoken tail — P2-D12
        var heard = NormalizeSpokenWords(transcript);
        if (heard.Count == 0)
        {
            return false;
        }

        var tail = NormalizeSpokenWords(_accumulatedReply);
        if (tail.Count > EchoLookbackWords)
        {
            tail = tail.GetRange(tail.Count - EchoLookbackWords, EchoLookbackWords);
        }

        if (heard.Count >= EchoMinWords)
        {
            var set = new HashSet<string>(tail, StringComparer.Ordinal);
            var contained = 0;
            foreach (var word in heard)
            {
                if (set.Contains(word))
                {
                    contained++;
                }
            }

            if (contained / (double)heard.Count >= EchoContainmentRatio)
            {
                return true;
            }
        }

        return ContainsSpokenPhrase(tail, heard, EchoPhraseWords);
    }

    private static bool ContainsSpokenPhrase(List<string> haystack, List<string> needle, int phraseWords)
    {
        if (needle.Count < phraseWords || haystack.Count < phraseWords)
        {
            return false;
        }

        for (var i = 0; i <= needle.Count - phraseWords; i++)
        {
            for (var j = 0; j <= haystack.Count - phraseWords; j++)
            {
                var n = 0;
                while (n < phraseWords && string.Equals(needle[i + n], haystack[j + n], StringComparison.Ordinal))
                {
                    n++;
                }

                if (n == phraseWords)
                {
                    return true;
                }
            }
        }

        return false;
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

    private void MarkUnavailable(string details)
    {
        // P2-VOICE: the probe details are what the status line shows — P2-D07
        IsAvailable = false;
        UnavailableDetails = details;
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
