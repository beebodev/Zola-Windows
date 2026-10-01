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
    PresenceMode PresenceMode,
    string LinkLabel,
    // P4-FEEDBACK: separate activity string; never replaces Waiting — P4-D16
    string ActivityLine);

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
    // P4-ASK: HUD while a clarify is open for the current session — P4-D15
    private const string WaitingForAnswerLabel = "Waiting for your answer";
    private const string MicOffLabel = "Mic: off";
    private const string MicRecordingLabel = "Mic: recording";
    private const string MicInterruptionsLabel = "Mic: listening for interruptions";
    private const string MicReconnectingLabel = "Reconnecting voice…";
    private const string WakeUnavailableLabel = "Wake word unavailable";
    private const string WakePausedLabel = "Wake listening paused";
    private const string WakeListeningLabel = "Mic: listening for \"Hey Zola\"";
    // P4-LOCK: gated mic lines sit above every other mic state — P4-D05
    private const string MicPausedLockedLabel = "Mic: paused — Windows locked";
    private const string MicPausedSleepingLabel = "Mic: paused — sleeping";
    private const string ModeWordVoice = "Voice";
    private const string ModeWordText = "Text";
    private const string MicContentListening = "Listening";
    private const string MicContentMic = "Mic";
    // P3-SHELL: HUD link line is first-match from facts the model already has — P3-D06
    private const string LinkOfflineLabel = "OFFLINE";
    private const string LinkReconnectingLabel = "LOCAL LINK • RECONNECTING";
    private const string LinkConnectedLabel = "LOCAL LINK • CONNECTED";
    private const string LinkConnectingLabel = "LOCAL LINK • CONNECTING";
    private const string DisplayStateLogFile = "display-state.log";
    private const string DisplayStateLineFormat = "P3-STATE: display state voice=\"{0}\" mic=\"{1}\" mode={2} link=\"{3}\" activity=\"{4}\"";
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
    // P4-FEEDBACK: friendly-name table for the tool activity line — P4-D16
    private const string ToolNameWebSearch = "web_search";
    private const string ToolNameTerminal = "terminal";
    private const string ToolNameSkillView = "skill_view";
    private const string ToolNameSkillsList = "skills_list";
    private const string ToolNameSkillManage = "skill_manage";
    private const string ToolNameClarify = "clarify";
    private const string ActivityWebSearch = "Searching the web…";
    private const string ActivityTerminal = "Running a command…";
    private const string ActivitySkillView = "Checking a skill…";
    private const string ActivitySkillsList = "Checking skills…";
    private const string ActivitySkillManage = "Managing a skill…";
    private const string ActivityUnknown = "Working…";

    // P4-FEEDBACK: named friendly-name map (clarify → null / no line) — P4-D16
    private static readonly Dictionary<string, string?> ToolActivityNames = new(StringComparer.Ordinal)
    {
        [ToolNameWebSearch] = ActivityWebSearch,
        [ToolNameTerminal] = ActivityTerminal,
        [ToolNameSkillView] = ActivitySkillView,
        [ToolNameSkillsList] = ActivitySkillsList,
        [ToolNameSkillManage] = ActivitySkillManage,
        [ToolNameClarify] = null,
    };

    // P3-STATE: XAML defaults until the window pushes facts; construction does not invent them — P3-D03
    private static readonly ZolaDisplayState InitialState = new(
        IdleLabel,
        MicOffLabel,
        ModeWordVoice,
        false,
        false,
        MicContentMic,
        PresenceMode.Dormant,
        LinkOfflineLabel,
        "");

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
    private bool _sessionReady;
    private int _turnGeneration;
    private int _warnedGeneration;
    private long _lastActivityTicks;
    // P4-LOCK: keep the last gated mic string while VoiceGated is hold-only after unlock — P4-D05
    private string? _lastGatedMicLine;
    // P4-FEEDBACK: id-aware active tools (order = newest last); provisional has no id — P4-D16
    private readonly List<(string Id, string Name)> _activeTools = new();
    private string? _provisionalToolName;
    private bool _suppressActivityForReply;

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
        _sessionReady = sessionReady;
        Recompute();
    }

    // P3-STATE: turn events refresh the stale-thinking clock and do not change the mode — P3-D04
    public void NoteTurnActivity()
    {
        _lastActivityTicks = Environment.TickCount64;
    }

    // P4-FEEDBACK: tool.start keyed by tool_id; clarify stays out of the set — P4-D16
    public void OnToolStarted(string? toolId, string name)
    {
        NoteTurnActivity();
        _provisionalToolName = null;
        if (string.IsNullOrEmpty(toolId))
        {
            // P4-FEEDBACK: no id → provisional hint only (no synthetic ids) — P4-D16
            if (!string.IsNullOrEmpty(name))
            {
                _provisionalToolName = name;
            }

            Recompute();
            return;
        }

        for (var i = _activeTools.Count - 1; i >= 0; i--)
        {
            if (string.Equals(_activeTools[i].Id, toolId, StringComparison.Ordinal))
            {
                _activeTools.RemoveAt(i);
            }
        }

        _activeTools.Add((toolId, name ?? ""));
        Recompute();
    }

    // P4-FEEDBACK: complete removes only that tool_id; older still-active reappears — P4-D16
    public void OnToolCompleted(string? toolId, string name)
    {
        NoteTurnActivity();
        _provisionalToolName = null;
        if (!string.IsNullOrEmpty(toolId))
        {
            for (var i = _activeTools.Count - 1; i >= 0; i--)
            {
                if (string.Equals(_activeTools[i].Id, toolId, StringComparison.Ordinal))
                {
                    _activeTools.RemoveAt(i);
                }
            }
        }

        Recompute();
    }

    // P4-FEEDBACK: generating is provisional and never enters the id-aware set — P4-D16
    public void OnToolGenerating(string name)
    {
        NoteTurnActivity();
        _provisionalToolName = string.IsNullOrEmpty(name) ? null : name;
        Recompute();
    }

    // P4-FEEDBACK: first reply text hides the activity line without dropping the set — P4-D16
    public void NoteReplyTextStarted()
    {
        if (_suppressActivityForReply)
        {
            return;
        }

        _suppressActivityForReply = true;
        _provisionalToolName = null;
        Recompute();
    }

    // P4-FEEDBACK: a new empty live bubble can show tools again until text arrives — P4-D16
    public void NoteLiveBubbleReset()
    {
        if (!_suppressActivityForReply)
        {
            return;
        }

        _suppressActivityForReply = false;
        Recompute();
    }

    // P4-FEEDBACK: clear-all safety net for missed tool.complete — P4-D16
    public void ClearToolActivity()
    {
        if (_activeTools.Count == 0 && _provisionalToolName is null && !_suppressActivityForReply)
        {
            return;
        }

        _activeTools.Clear();
        _provisionalToolName = null;
        _suppressActivityForReply = false;
        Recompute();
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
        // P4-ASK: stale-thinking clock does not run while awaiting a clarify answer — P4-D15
        if (_voice.AwaitingAnswer)
        {
            return;
        }

        _staleTimer.Start();
    }

    private void OnStaleThinkingTick(DispatcherQueueTimer sender, object args)
    {
        // P4-ASK: suspend stale warn for the whole clarify wait — P4-D15
        if (_voice.AwaitingAnswer)
        {
            _lastActivityTicks = Environment.TickCount64;
            return;
        }

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
        // P4-ASK: keep the stale timer stopped for the whole await; restart only after — P4-D15
        if (_voice.AwaitingAnswer)
        {
            _staleTimer.Stop();
        }
        else if (_streaming)
        {
            _staleTimer.Start();
        }

        // P3-STATE: voice-label priority stays the P2 order from Audit 01 §3 — P3-D03
        // P4-ASK: Waiting inserts after Text/unavailable and before Thinking — P4-D15
        // Priority: unavailable(+details) → Text mode → Waiting for your answer → Thinking → Speaking → Transcribing → Listening → Idle
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
        else if (_voice.AwaitingAnswer)
        {
            voiceLabel = WaitingForAnswerLabel;
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

        // P4-LOCK: gated mic line first; hold after unlock keeps the last gated string — P4-D05
        string micLine;
        if (_voice.VoiceGated)
        {
            if (_voice.SystemLocked)
            {
                _lastGatedMicLine = MicPausedLockedLabel;
            }
            else if (_voice.SystemSuspended)
            {
                _lastGatedMicLine = MicPausedSleepingLabel;
            }

            micLine = _lastGatedMicLine ?? MicPausedLockedLabel;
        }
        else
        {
            _lastGatedMicLine = null;
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
        }

        var modeWord = _voice.Mode == VoiceController.ModeVoice ? ModeWordVoice : ModeWordText;
        var modeButtonEnabled = !_unreachable && !_modeSwitching && _hasSessionId;
        var micButtonEnabled = _voice.CanStartCapture;
        var micButtonContent = _voice.CaptureActive ? MicContentListening : MicContentMic;

        // P3-STATE: Speaking outranks streaming, and text mode is checked last — P3-D04
        // P4-ASK: while awaiting, never THINKING; LISTENING if capture else IDLE (Speaking still wins for question TTS) — P4-D15
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
        else if (_voice.AwaitingAnswer)
        {
            presenceMode = _voice.CaptureActive || _voice.RecorderState == VoiceController.StateListening
                || _voice.RecorderState == VoiceController.StateTranscribing
                ? PresenceMode.Listening
                : PresenceMode.Idle;
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

        string linkLabel;
        if (_unreachable || !_backendReachable)
        {
            linkLabel = LinkOfflineLabel;
        }
        else if (_switchInFlight || _historyPending)
        {
            linkLabel = LinkReconnectingLabel;
        }
        else if (_sessionReady)
        {
            linkLabel = LinkConnectedLabel;
        }
        else
        {
            linkLabel = LinkConnectingLabel;
        }

        // P4-FEEDBACK: Waiting wins; else newest real tool; else provisional; else empty — P4-D16
        var activityLine = BuildActivityLine();

        var next = new ZolaDisplayState(
            voiceLabel,
            micLine,
            modeWord,
            modeButtonEnabled,
            micButtonEnabled,
            micButtonContent,
            presenceMode,
            linkLabel,
            activityLine);
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
            WriteDisplayLog(string.Format(
                DisplayStateLineFormat,
                next.VoiceLabel,
                next.MicLine,
                next.PresenceMode,
                next.LinkLabel,
                next.ActivityLine));
        }

        if (differs)
        {
            Changed?.Invoke();
        }
    }

    private string BuildActivityLine()
    {
        // P4-FEEDBACK: activity must not override Waiting (K7) — P4-D16
        if (_voice.AwaitingAnswer || _suppressActivityForReply)
        {
            return "";
        }

        for (var i = _activeTools.Count - 1; i >= 0; i--)
        {
            var mapped = MapToolActivity(_activeTools[i].Name);
            if (mapped is not null)
            {
                return mapped;
            }
        }

        if (_provisionalToolName is not null)
        {
            return MapToolActivity(_provisionalToolName) ?? "";
        }

        return "";
    }

    private static string? MapToolActivity(string name)
    {
        if (ToolActivityNames.TryGetValue(name, out var mapped))
        {
            return mapped;
        }

        return ActivityUnknown;
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
