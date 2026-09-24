using Microsoft.UI.Dispatching;

namespace Zola.Client;

public enum PresenceMode
{
    Idle,
    Listening,
    Thinking,
    Speaking,
    Alert,
    Dormant,
}

public sealed record ZolaDisplayState(
    string VoiceLabel,
    string MicLine,
    string ModeWord,
    bool ModeButtonEnabled,
    bool MicButtonEnabled,
    string MicButtonContent,
    PresenceMode PresenceMode);

// P3-STATE: one model owns the voice label, the mic line, and presence mode — P3-D03
public sealed class ZolaDisplayStateModel : IDisposable
{
    private const string VoiceUnavailableLabel = "Voice unavailable";
    private const string VoiceUnavailablePrefix = "Voice unavailable — ";
    private const string TextModeLabel = "Text mode";
    private const string ThinkingLabel = "Thinking";
    private const string SpeakingLabel = "Speaking";
    private const string TranscribingLabel = "Transcribing";
    private const string ListeningLabel = "Listening";
    private const string IdleLabel = "Idle";
    private const string MicOffLabel = "Mic: off";
    private const string MicRecordingLabel = "Mic: recording";
    private const string MicInterruptionsLabel = "Mic: listening for interruptions";
    private const string MicReconnectingLabel = "Reconnecting voice…";
    private const string WakeUnavailableLabel = "Wake word unavailable";
    private const string WakePausedLabel = "Wake listening paused";
    private const string WakeListeningLabel = "Mic: listening for \"Hey Zola\"";
    private const string ModeWordVoice = "Voice";
    private const string ModeWordText = "Text";
    private const string MicContentListening = "Listening";
    private const string MicContentMic = "Mic";
    private const string DisplayStateLogFile = "display-state.log";
    private const string DisplayStateLineFormat = "P3-STATE: display state voice=\"{0}\" mic=\"{1}\" mode={2}";
    private const string FactLineFormat = "P3-STATE: fact {0}={1}";
    private const string FactUnreachable = "unreachable";
    private const string FactSwitchInFlight = "switchInFlight";
    private const string FactHistoryPending = "historyPending";
    private const string FactTrue = "true";
    private const string FactFalse = "false";
    private const string StaleThinkingLineFormat = "P3-STATE: thinking with no events for {0}s (S26)";
    private const int StaleThinkingCheckSeconds = 10;
    private const int StaleThinkingWarnSeconds = 120;
    private const long MillisecondsPerSecond = 1000;

    // P3-STATE: XAML defaults until the window pushes facts; construction does not invent them — P3-D03
    private static readonly ZolaDisplayState InitialState = new(
        IdleLabel,
        MicOffLabel,
        ModeWordVoice,
        false,
        false,
        MicContentMic,
        PresenceMode.Dormant);

    private readonly VoiceController _voice;
    private readonly DispatcherQueueTimer _staleTimer;
    private bool _hasWindowFacts;
    private bool _streaming;
    private bool _unreachable;
    private bool _switchInFlight;
    private bool _historyPending;
    private bool _modeSwitching;
    private bool _backendReachable;
    private bool _hasSessionId;
    private int _turnGeneration;
    private int _warnedGeneration;
    private long _lastActivityTicks;

    internal ZolaDisplayStateModel(VoiceController voice, DispatcherQueue dispatcher)
    {
        _voice = voice;
        Current = InitialState;
        _staleTimer = dispatcher.CreateTimer();
        _staleTimer.Interval = TimeSpan.FromSeconds(StaleThinkingCheckSeconds);
        _staleTimer.IsRepeating = true;
        _staleTimer.Tick += OnStaleThinkingTick;
    }

    public ZolaDisplayState Current { get; private set; }

    public event Action? Changed;

    // P3-STATE: the window pushes facts, then the controller keeps the one mic-gate write — P3-D03
    public void UpdateWindowFacts(
        bool sessionReady,
        bool backendReachable,
        bool streaming,
        bool switchInFlight,
        bool historyPending,
        bool modeSwitching,
        bool unreachable,
        bool hasSessionId)
    {
        LogFactChange(FactUnreachable, _unreachable, unreachable);
        LogFactChange(FactSwitchInFlight, _switchInFlight, switchInFlight);
        LogFactChange(FactHistoryPending, _historyPending, historyPending);
        _voice.SetCaptureGate(sessionReady, backendReachable, streaming);
        TrackStreaming(streaming);
        _unreachable = unreachable;
        _switchInFlight = switchInFlight;
        _historyPending = historyPending;
        _modeSwitching = modeSwitching;
        _backendReachable = backendReachable;
        _hasSessionId = hasSessionId;
        Recompute();
    }

    // P3-STATE: turn events refresh the stale-thinking clock and do not change the mode — P3-D04
    public void NoteTurnActivity()
    {
        _lastActivityTicks = Environment.TickCount64;
    }

    // P3-STATE: window close stops the one stale-thinking timer — P3-D04
    public void Dispose()
    {
        _staleTimer.Stop();
        _staleTimer.Tick -= OnStaleThinkingTick;
    }

    private void TrackStreaming(bool streaming)
    {
        if (streaming == _streaming)
        {
            return;
        }

        _streaming = streaming;
        if (!streaming)
        {
            _staleTimer.Stop();
            return;
        }

        _turnGeneration++;
        _lastActivityTicks = Environment.TickCount64;
        _staleTimer.Start();
    }

    private void OnStaleThinkingTick(DispatcherQueueTimer sender, object args)
    {
        if (!_streaming || _warnedGeneration == _turnGeneration)
        {
            return;
        }

        var elapsedSeconds = (Environment.TickCount64 - _lastActivityTicks) / MillisecondsPerSecond;
        if (elapsedSeconds < StaleThinkingWarnSeconds)
        {
            return;
        }

        _warnedGeneration = _turnGeneration;
        WriteDisplayLog(string.Format(StaleThinkingLineFormat, elapsedSeconds));
    }

    private void Recompute()
    {
        // P3-STATE: voice-label priority stays the P2 order from Audit 01 §3 — P3-D03
        string voiceLabel;
        if (!_voice.IsAvailable && _voice.Mode == VoiceController.ModeText)
        {
            var details = _voice.UnavailableDetails;
            voiceLabel = details.Length == 0 ? VoiceUnavailableLabel : VoiceUnavailablePrefix + details;
        }
        else if (_voice.Mode == VoiceController.ModeText)
        {
            voiceLabel = TextModeLabel;
        }
        else if (_streaming)
        {
            voiceLabel = ThinkingLabel;
        }
        else if (_voice.Speaking)
        {
            voiceLabel = SpeakingLabel;
        }
        else if (_voice.RecorderState == VoiceController.StateTranscribing)
        {
            voiceLabel = TranscribingLabel;
        }
        else if (_voice.CaptureActive || _voice.RecorderState == VoiceController.StateListening)
        {
            voiceLabel = ListeningLabel;
        }
        else
        {
            voiceLabel = IdleLabel;
        }

        // P3-STATE: mic-line priority stays the Audit 01 §3 order — P3-D03
        string micLine;
        if (_voice.Mode != VoiceController.ModeVoice || !_voice.IsAvailable)
        {
            micLine = MicOffLabel;
        }
        else if (_voice.CaptureActive)
        {
            micLine = MicRecordingLabel;
        }
        else if (_streaming || _voice.Speaking)
        {
            micLine = MicInterruptionsLabel;
        }
        else if (_switchInFlight || _historyPending)
        {
            micLine = MicReconnectingLabel;
        }
        else if (_voice.WakeUnavailable || _voice.WakeHeldElsewhere)
        {
            micLine = WakeUnavailableLabel;
        }
        else if (_voice.Resting && _voice.WakeArmed && _voice.WakePaused)
        {
            micLine = WakePausedLabel;
        }
        else if (_voice.Resting && _voice.WakeArmed && !_voice.WakePaused)
        {
            micLine = WakeListeningLabel;
        }
        else
        {
            micLine = MicOffLabel;
        }

        var modeWord = _voice.Mode == VoiceController.ModeVoice ? ModeWordVoice : ModeWordText;
        var modeButtonEnabled = !_unreachable && !_modeSwitching && _hasSessionId;
        var micButtonEnabled = _voice.CanStartCapture;
        var micButtonContent = _voice.CaptureActive ? MicContentListening : MicContentMic;

        // P3-STATE: Speaking outranks streaming, and text mode is checked last — P3-D04
        PresenceMode presenceMode;
        if (_unreachable || !_backendReachable)
        {
            presenceMode = PresenceMode.Dormant;
        }
        else if (_switchInFlight || _historyPending)
        {
            presenceMode = PresenceMode.Idle;
        }
        else if (_voice.Speaking)
        {
            presenceMode = PresenceMode.Speaking;
        }
        else if (_streaming)
        {
            presenceMode = PresenceMode.Thinking;
        }
        else if (_voice.RecorderState == VoiceController.StateTranscribing)
        {
            presenceMode = PresenceMode.Listening;
        }
        else if (_voice.CaptureActive || _voice.RecorderState == VoiceController.StateListening)
        {
            presenceMode = PresenceMode.Listening;
        }
        else if (_voice.Mode == VoiceController.ModeText || !_voice.IsAvailable)
        {
            presenceMode = PresenceMode.Idle;
        }
        else
        {
            presenceMode = PresenceMode.Idle;
        }

        var next = new ZolaDisplayState(
            voiceLabel,
            micLine,
            modeWord,
            modeButtonEnabled,
            micButtonEnabled,
            micButtonContent,
            presenceMode);
        var first = !_hasWindowFacts;
        var differs = next != Current;
        _hasWindowFacts = true;
        if (!first && !differs)
        {
            return;
        }

        Current = next;
        if (first || differs)
        {
            WriteDisplayLog(string.Format(DisplayStateLineFormat, next.VoiceLabel, next.MicLine, next.PresenceMode));
        }

        if (differs)
        {
            Changed?.Invoke();
        }
    }

    private void LogFactChange(string name, bool previous, bool current)
    {
        if (previous == current)
        {
            return;
        }

        WriteDisplayLog(string.Format(FactLineFormat, name, current ? FactTrue : FactFalse));
    }

    // P3-STATE: display-state.log sits beside voice-timeline.log, and a failed write is ignored — P3-D03
    private static void WriteDisplayLog(string line)
    {
        try
        {
            var root = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                VoiceController.TimelineClientFolder,
                VoiceController.TimelineLogFolder);
            Directory.CreateDirectory(root);
            File.AppendAllText(
                Path.Combine(root, DisplayStateLogFile),
                DateTimeOffset.Now.ToString("o") + " " + line + Environment.NewLine);
        }
        catch
        {
        }
    }
}
