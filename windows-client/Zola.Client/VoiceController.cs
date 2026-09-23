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
    private const string ActionStart = "start";
    private const string ActionStop = "stop";
    private const string RecordBusy = "busy";
    private const string ReasonWakeOwned = "wake_owned";
    private const string NoticeNoSpeech = "No speech heard";
    private const string NoticeInterrupted = "Voice interrupted.";
    private const string NoticeBusy = "The microphone is busy.";
    private const string NoticeWakeOwned = "The wake word owns the microphone.";

    private readonly ChatSocket _chat;

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

    public bool CanStartCapture
    {
        get
        {
            // P2-VOICE: the mic control stays off while a turn runs, because barge-in already has the microphone — P2-D12
            return Mode == ModeVoice && IsAvailable && SessionReady && BackendReachable && !TurnRunning;
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
            // P2-VOICE: voice.toggle on enables capture; this track never sends action tts — P2-D03
            var enabled = await ToggleAsync(ActionOn).ConfigureAwait(false);
            if (!enabled.Ok || enabled.Enabled == false)
            {
                MarkUnavailable(enabled.Error ?? enabled.Details ?? UnavailableDetails);
                return;
            }
        }

        StateChanged?.Invoke();
    }

    public async Task EnterTextModeAsync()
    {
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
            await StartCaptureAsync().ConfigureAwait(false);
            return;
        }

        if (RecorderState == StateTranscribing)
        {
            // P2-VOICE: a capture that is already transcribing is left to finish — P2-D05
            return;
        }

        await StopCaptureAsync().ConfigureAwait(false);
    }

    private async Task StartCaptureAsync()
    {
        // P2-VOICE: voice.record always carries the current runtime session id — P2-D01
        if (string.IsNullOrEmpty(_chat.SessionId))
        {
            return;
        }

        var reply = await RecordAsync(ActionStart, allowResync: true).ConfigureAwait(false);
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

        StateChanged?.Invoke();
    }

    private async Task StopCaptureAsync()
    {
        // P2-VOICE: stop forces transcription; capture stays active until voice.status idle — P2-D05
        var reply = await RecordAsync(ActionStop, allowResync: true).ConfigureAwait(false);
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

    private async Task<ChatSocket.RpcReply> RecordAsync(string action, bool allowResync)
    {
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

    private Task<ChatSocket.RpcReply> ToggleAsync(string action)
    {
        // P2-VOICE: voice.toggle is status, on, or off; spoken replies are left untouched — P2-D03
        return _chat.InvokeAsync(MethodToggle, new Dictionary<string, string?>
        {
            [ParamAction] = action,
        });
    }

    private void OnVoiceStatus(string state)
    {
        // P2-VOICE: capture is active from a successful start until the recorder reports idle — P2-D08
        RecorderState = string.IsNullOrEmpty(state) ? StateIdle : state;
        if (RecorderState == StateIdle)
        {
            CaptureActive = false;
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
            VoiceChatEnded?.Invoke();
            _ = ResyncAfterStopAsync();
            return;
        }

        if (transcript.IsNoSpeechLimit)
        {
            // P2-VOICE: three silent captures are a status line, not a turn — P2-D05
            StatusMessage?.Invoke(NoticeNoSpeech);
            return;
        }

        if (transcript.Text.Trim().Length > 0)
        {
            // P2-VOICE: a non-empty transcript is submitted once by the window — P2-D05
            TranscriptReady?.Invoke(transcript.Text.Trim());
        }
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
        // P2-VOICE: the interjection arrives later as a normal transcript; this event is status only — P2-D08
        StatusMessage?.Invoke(NoticeInterrupted);
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
