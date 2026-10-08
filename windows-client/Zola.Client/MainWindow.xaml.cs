using System.Runtime.InteropServices;
using System.Text.Json;
using Microsoft.UI.Input;
using Microsoft.UI.Windowing;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Input;
using Microsoft.UI.Xaml.Media;
using Microsoft.UI.Xaml.Media.Animation;
using Windows.Foundation;
using Windows.System;
using Windows.UI.Core;
using Windows.UI.ViewManagement;
using Zola.Client.Presence;
using Zola.Client.Voice;

namespace Zola.Client;

// P1-CLIENT: one session on /api/ws streams turns, keeps that session for follow-ups, and can cancel — P1-D01
public sealed partial class MainWindow : Window
{
    private readonly HermesProcessManager _backend;
    private readonly ChatSocket _chat;
    private readonly VoiceController _voice;
    private readonly ServerRequestBroker _requests;
    private readonly ZolaDisplayStateModel _display;
    private LiveResponse? _live;
    private bool _connectStarted;
    private bool _socketOwnsStatus;
    private bool _sessionReady;
    private bool _streaming;
    private int _compressInFlight;
    private bool _turnFinalized = true;
    private bool _unreachable;
    private int _orphanInterruptedCompletes;
    private string _sessionDetail = "";
    private string? _routedNote;
    private bool _sessionsOpen;
    private bool _historyPending;
    private bool _switchInFlight;
    private bool _modeSwitching;
    private bool _returnFocusToComposer;
    private bool _lastTurnErrored;
    private Point? _lastPointerInRoot;
    private string _noticeSeenText = "";
    private readonly Dictionary<string, SessionRow> _sessionRows = new();
    private readonly HashSet<string> _serverSessionIds = new();
    private readonly Microsoft.UI.Dispatching.DispatcherQueueTimer _clockTimer;
    private readonly Microsoft.UI.Dispatching.DispatcherQueueTimer _dockHideTimer;
    private readonly Microsoft.UI.Dispatching.DispatcherQueueTimer _noticeHoldTimer;
    private readonly UISettings _uiSettings = new();
    private Storyboard? _dockStoryboard;
    private bool _dockRevealTarget;
    private Storyboard? _noticeStoryboard;
    private PresenceView? _presence;
    // P4-LOCK: one app-level lock/sleep watcher — P4-D01
    private SessionLockWatcher? _lockWatcher;
    private const int SessionIdDisplayLength = 8;
    private const string SessionHudPrefix = "SESSION ";
    private const string SessionHudEmpty = "SESSION —";
    private const string TimeFormat = "HH:mm";
    private const string VoiceBulletPrefix = "• ";
    private const string TokenWindowWidth = "ZolaWindowWidth";
    private const string TokenWindowHeight = "ZolaWindowHeight";
    private const string TokenWindowMinWidth = "ZolaWindowMinWidth";
    private const string TokenWindowMinHeight = "ZolaWindowMinHeight";
    private const string TokenOverlayMaxWidth = "ConversationOverlayMaxWidth";
    private const string TokenOverlayMaxFraction = "ConversationOverlayMaxFraction";
    private const string TokenNoticeMaxFraction = "ZolaNoticeMaxFraction";
    private const string TokenBubbleMaxWidth = "ZolaBubbleMaxWidth";
    private const string TokenBubblePadding = "ZolaBubblePadding";
    private const string TokenBubbleCornerRadius = "ZolaBubbleCornerRadius";
    private const string TokenBubbleBorderThickness = "ZolaBubbleBorderThickness";
    private const string TokenSpace4 = "ZolaSpace4";
    private const string TokenSpace8 = "ZolaSpace8";
    private const string TokenUserBubble = "ZolaUserBubbleBrush";
    private const string TokenAssistantBubble = "ZolaAssistantBubbleBrush";
    private const string TokenAmberMuted = "ZolaAmberMutedBrush";
    private const string TokenAmberDark = "ZolaAmberDarkBrush";
    private const string TokenError = "ZolaErrorBrush";
    private const string TokenBodyStyle = "ZolaBodyStyle";
    private const string TokenBubbleHeadingStyle = "ZolaBubbleHeadingStyle";
    private const string TokenPanelBorderStyle = "ZolaPanelBorderStyle";
    private const string TokenTextButtonStyle = "ZolaTextButtonStyle";
    private const string TokenComposerStyle = "ZolaComposerStyle";
    private const string TokenDockRevealMargin = "DockRevealMargin";
    private const string TokenDockHideDelaySeconds = "DockHideDelaySeconds";
    private const string TokenDockFadeMilliseconds = "DockFadeMilliseconds";
    private const string TokenNoticeHoldSeconds = "NoticeHoldSeconds";
    private const string TokenNoticeMargin = "ZolaNoticeMargin";
    private const double DockShownOpacity = 1;
    private const double DockHiddenOpacity = 0;
    // P4-REQUEST: composer and card chrome strings — P4-D08 / P4-D09
    private const string PlaceholderAnswerClarify = "Answer Zola's question…";
    private const string PlaceholderMessage = "Message";
    private const string LabelApproveOnce = "Approve once";
    private const string LabelDeny = "Deny";
    private const string LabelSkip = "Skip";
    private const string LabelSend = "Send";
    private const string LabelRecommended = "(Recommended)";
    private const string RecordAnsweredPrefix = "You answered: ";
    private const string RecordApprovedPrefix = "You approved once: ";
    private const string RecordDeniedPrefix = "You denied: ";
    private const string RecordSkipped = "Skipped";
    private const string RecordCancelled = "Cancelled";
    private const string RecordSendFailed = "Send failed";
    private const string RecordDeclined = "Declined";
    private const string RecordWithdrawn = "Withdrawn";
    // P4-ASK: late bound answer after the card closed — P4-D14
    private const string NoticeLateAnswer =
        "Your answer arrived after Zola stopped waiting — say it again if you still need it.";
    private const string HeadingClarify = "Zola asks";
    private const string HeadingApproval = "Approval needed";
    private const string CommandFontFamilyName = "Cascadia Mono";
    private const string MethodTour = "tour";
    private const string MethodClarify = "clarify";
    private const string MethodApproval = "approval";
    private const string DebugRequestIdPrefix = "srq-debug-";
    private const string FieldSessionId = "session_id";
    private const string FieldQuestion = "question";
    private const string FieldQuestions = "questions";
    private const string FieldChoices = "choices";
    private const string FieldMultiSelect = "multi_select";
    private const string FieldCommand = "command";
    private const string FieldDescription = "description";
    private const string FieldRequestId = "request_id";
    private const string FieldQid = "qid";
    private readonly Dictionary<string, FrameworkElement> _requestCards = new(StringComparer.Ordinal);
    private readonly Dictionary<string, string> _requestCloseRecords = new(StringComparer.Ordinal);
    // P4-ASK: one spoken question per clarify id; re-shows do not speak again — P4-D13
    private readonly HashSet<string> _spokenClarifyIds = new(StringComparer.Ordinal);
    // P7-CLARIFY: quiet singles (Voice) — skip auto panel; track no-answer panel once — P7-D09
    private readonly HashSet<string> _quietClarifyIds = new(StringComparer.Ordinal);
    private readonly HashSet<string> _noAnswerPanelOpenedIds = new(StringComparer.Ordinal);

    public MainWindow(HermesProcessManager backend)
    {
        // P1-CLIENT: the window subscribes before start so the first ready state can open the socket — P1-D01
        InitializeComponent();
        ApplyWindowMetrics();
        SizeChanged += OnWindowSizeChanged;
        // P3-RENDER: host the viewport in PresenceHost and pause when the window cannot be seen — P3-D02
        // P4-LOCK: hwnd feeds the single SessionLockWatcher owned here, not PresenceView — P4-D01
        var hwnd = WinRT.Interop.WindowNative.GetWindowHandle(this);
        var presence = new PresenceView();
        _presence = presence;
        PresenceHost.Children.Add(presence);
        AppWindow.Changed += OnAppWindowChanged;
        VisibilityChanged += OnWindowVisibilityChanged;
        Activated += OnWindowActivated;
        _dockHideTimer = DispatcherQueue.CreateTimer();
        _dockHideTimer.IsRepeating = false;
        _dockHideTimer.Tick += OnDockHideTimerTick;
        _noticeHoldTimer = DispatcherQueue.CreateTimer();
        _noticeHoldTimer.IsRepeating = false;
        _noticeHoldTimer.Tick += OnNoticeHoldTimerTick;
#if DEBUG
        AddPresenceDebugAccelerators();
        // P4-REQUEST: env-triggered card inject for screenshot capture when hotkeys cannot reach WinUI — P4-D08
        CompositionTarget.Rendering += OnDebugInjectCardsOnce;
#endif
        _clockTimer = DispatcherQueue.CreateTimer();
        _clockTimer.IsRepeating = true;
        _clockTimer.Tick += OnClockTick;
        _backend = backend;
        _chat = new ChatSocket(backend);
        // P2-VOICE: one voice controller owns this window's socket; the window only renders and forwards input — P2-D12
        _voice = new VoiceController(_chat);
        // P4-REQUEST: one broker owns open server requests — P4-D06
        _requests = new ServerRequestBroker(_chat);
        // P4-LOCK: one lock/sleep watcher, app-level — P4-D01
        _lockWatcher = new SessionLockWatcher(hwnd);
        _lockWatcher.Locked += OnSystemLocked;
        _lockWatcher.Unlocked += OnSystemUnlocked;
        _lockWatcher.Suspending += OnSystemSuspending;
        _lockWatcher.Resumed += OnSystemResumed;
        // P3-STATE: the window renders the display record and does not derive it — P3-D03
        _display = new ZolaDisplayStateModel(_voice, DispatcherQueue);
        // P3-LIFE: animator follows display mode and the window's reduced-motion flag — P3-D22
        _presence!.AttachDisplay(_display);
        _presence.AttachPlaybackMonitor(() => _backend.ServeProcessId);
        // P4-ASK: monitor bout forward + question speech wiring — P4-D13
        _presence.PlaybackBoutStarted += () => _voice.NotePlaybackBoutStarted();
        _presence.PlaybackBoutStopped += forced => _voice.NotePlaybackBoutStopped(forced);
        // P7-VOICEAUTH: broker query scoped to clarify id + current session (never "any open") — P7-D05
        _voice.ConfigureQuestionSpeech(
            () => _presence?.PlaybackMonitorAvailable == true,
            id =>
            {
                if (_requests.GetState(id) != ServerRequestBroker.Lifecycle.Open)
                {
                    return false;
                }

                var sessionId = _requests.TryGetSessionId(id);
                return !string.IsNullOrEmpty(sessionId)
                    && string.Equals(sessionId, _chat.SessionId, StringComparison.Ordinal);
            },
            () => _presence?.PlaybackBoutActive == true);
        _presence.SetReducedMotion(!_uiSettings.AnimationsEnabled);
        if (OperatingSystem.IsWindowsVersionAtLeast(10, 0, 19041))
        {
            _uiSettings.AnimationsEnabledChanged += OnAnimationsEnabledChanged;
        }
        _voice.StateChanged += () => Dispatch(ApplyVoiceChrome);
        // P4-LOCK: belt-and-braces refuse of voice submit while gated — P4-D02
        // P4-ASK: bound clarify id, then open clarify, else prompt.submit — P4-D14
        _voice.TranscriptReady += (text, boundClarifyId) => Dispatch(() => OnTranscriptReady(text, boundClarifyId));
        // P7-CLARIFY: bound capture ended without admit → quiet panel once — P7-D09
        _voice.ClarifyAnswerCaptureEndedWithoutAnswer += id => Dispatch(() => OnClarifyNoAnswer(id));
        _voice.VoiceChatEnded += () => Dispatch(OnVoiceChatEnded);
        _voice.StatusMessage += message => Dispatch(() => OnVoiceStatusMessage(message));
        _chat.SessionReady += (sessionId, storedId) => Dispatch(() => OnSessionReady(sessionId, storedId));
        _chat.SubmitAcknowledged += status => Dispatch(() => OnSubmitAcknowledged(status));
        _chat.MessageStarted += () => Dispatch(OnMessageStarted);
        _chat.MessageDelta += chunk => Dispatch(() => OnMessageDelta(chunk));
        _chat.MessageCompleted += (status, text) => Dispatch(() => OnMessageCompleted(status, text));
        _chat.InterruptAcknowledged += status => Dispatch(() => OnInterruptAcknowledged(status));
        _chat.Routed += note => Dispatch(() => OnRouted(note));
        _chat.Unreachable += reason => Dispatch(() => ShowUnreachable(reason));
        // P4-FEEDBACK: tool lifecycle → display activity line — P4-D16
        _chat.ToolStarted += (id, name, _) => Dispatch(() => OnToolStarted(id, name));
        _chat.ToolCompleted += (id, name, _) => Dispatch(() => OnToolCompleted(id, name));
        _chat.ToolGenerating += (name, _) => Dispatch(() => OnToolGenerating(name));
        // P4-REQUEST: socket hand-off into the broker; notices use the existing route — P4-D06
        _chat.Replacing += () => _requests.MarkSocketReplacing();
        _chat.ServerRequestReceived += (id, method, parameters) => _requests.OnRequest(id, method, parameters);
        _chat.ServerRequestCancelled += (id, method, reason) => _requests.OnCancel(id, method, reason);
        // P4-FEEDBACK: broker notices use StatusText so NoticeHost / panel mirror show them — P4-D17
        _requests.Notice += text => Dispatch(() => ShowRequestNotice(text));
        // P4-REQUEST: card UI listens for open/close; render only while still Open — P4-D07 / P4-D08
        _requests.ClarifyOpened += (id, view) => Dispatch(() => OnClarifyOpened(id, view));
        _requests.ApprovalOpened += (id, view) => Dispatch(() => OnApprovalOpened(id, view));
        _requests.RequestClosed += (id, outcome) => Dispatch(() => OnRequestClosed(id, outcome));
        _backend.StateChanged += (_, _) => DispatcherQueue.TryEnqueue(Render);
        Composer.TextChanged += (_, _) => UpdateChrome();
        Composer.PreviewKeyDown += OnComposerKeyDown;
        Closed += (_, _) =>
        {
            // P2-SPEAK: app close cancels a pending follow-up before the socket is disposed — P2-D06
            // P3-STATE: window close stops the stale-thinking timer — P3-D04
            // P3-SHELL: window close also stops the HUD clock — P3-D06
            _clockTimer.Stop();
            _clockTimer.Tick -= OnClockTick;
            _dockHideTimer.Stop();
            _dockHideTimer.Tick -= OnDockHideTimerTick;
            _noticeHoldTimer.Stop();
            _noticeHoldTimer.Tick -= OnNoticeHoldTimerTick;
            CompositionTarget.Rendering -= OnFirstShellRender;
            AppWindow.Changed -= OnAppWindowChanged;
            VisibilityChanged -= OnWindowVisibilityChanged;
            Activated -= OnWindowActivated;
            if (OperatingSystem.IsWindowsVersionAtLeast(10, 0, 19041))
            {
                _uiSettings.AnimationsEnabledChanged -= OnAnimationsEnabledChanged;
            }
            // P4-LOCK: dispose the app-level lock watcher before presence — P4-D01
            _lockWatcher?.Dispose();
            _lockWatcher = null;
            _presence?.Dispose();
            _display.Dispose();
            _voice.Shutdown();
            _chat.Dispose();
        };
        Render();
        ApplyVoiceChrome();
        UpdateClock();
        UpdateSessionHud();
        StartClock();
    }

    private void Render()
    {
        // P1-CLIENT: open /api/ws only after health, token, and port are all present — P1-D01
        if (!_socketOwnsStatus)
        {
            StatusText.Text = _backend.StatusText;
            DetailText.Text = _backend.DetailText;
        }

        if (_backend.WebSocketPermitted && !_connectStarted)
        {
            _connectStarted = true;
            _socketOwnsStatus = true;
            StatusText.Text = "Connecting to /api/ws…";
            _ = ConnectAsync();
        }
    }

    private async Task ConnectAsync()
    {
        try
        {
            // P1-CLIENT: session.create runs inside start; the composer stays disabled until it returns — P1-D01
            await _chat.StartAsync().ConfigureAwait(false);
        }
        catch (ChatUnreachableException ex)
        {
            Dispatch(() => ShowUnreachable(ex.Message));
        }
        catch (Exception ex)
        {
            Dispatch(() =>
            {
                _sessionReady = false;
                StatusText.Text = ex.Message;
                UpdateChrome();
            });
        }
    }

    private void OnSessionReady(string sessionId, string storedId)
    {
        // P2-SPEAK: every SessionReady cancels a leftover follow-up from the previous session — P2-D06
        _voice.OnSessionReady();
        // P4-REQUEST: reconcile parked/open requests against this session's open_requests — P4-D11
        _requests.OnSessionChanged(sessionId);
        if (_chat.LastPendingApprovalPresent)
        {
            _requests.NotePendingApprovalIgnored(sessionId);
        }

        _requests.LoadOpenRequests(sessionId, _chat.LastOpenRequests);
        // P1-CLIENT: store both ids once; later sends reuse them so the agent keeps context — P1-D01
        _sessionDetail = $"session {sessionId} · stored {storedId}";
        // P1-CLIENT: an error event can arrive before session.create's result; keep it beside the ids — P1-D01
        DetailText.Text = _routedNote is null ? _sessionDetail : _routedNote + Environment.NewLine + _sessionDetail;
        // P1-SESSION: show the stored id as soon as session.create or session.resume acknowledges it — P1-D04
        NoteAcknowledgedSession(storedId);
        // P2-VOICE: every new socket re-syncs Voice mode, including new session and resume — P2-D07
        if (_voice.Mode == VoiceController.ModeVoice)
        {
            _ = SyncVoiceAsync();
        }

        if (_historyPending)
        {
            // P1-SESSION: resume keeps the composer off until the fetched turns are on screen — P1-D04
            StatusText.Text = "Loading earlier turns…";
            UpdateChrome();
            return;
        }

        _sessionReady = true;
        StatusText.Text = "Session ready.";
        Composer.PlaceholderText = PlaceholderMessage;
        UpdateChrome();
    }

    private async void OnSendClick(object sender, RoutedEventArgs e)
    {
        var text = Composer.Text.Trim();
        if (!_sessionReady || _unreachable || text.Length == 0)
        {
            return;
        }

        // P4-REQUEST: open clarify routes Send to the broker, not prompt.submit — P4-D09
        var openClarify = _requests.HasOpenClarify(_chat.SessionId);
        if (!openClarify && _streaming)
        {
            return;
        }

        if (openClarify)
        {
            var id = _requests.NewestOpenClarify(_chat.SessionId);
            if (id is null)
            {
                return;
            }

            var view = _requests.TryGetClarifyView(id);
            if (view is null)
            {
                return;
            }

            Composer.Text = "";
            if (view.IsBatch)
            {
                // P7-CLARIFY: Voice quiet single fill-then-send; Text fills only (card Send) — P7-D09
                FillFirstUnansweredBatchRow(id, text);
                if (_voice.Mode == VoiceController.ModeVoice
                    && IsQuietClarifyView(view)
                    && !BatchHasUnansweredRows(id))
                {
                    var answers = CollectBatchAnswers(id);
                    if (answers.Count > 0)
                    {
                        _requestCloseRecords[id] = RecordAnsweredPrefix + string.Join("; ", answers.Values);
                        _requests.AnswerBatch(id, answers);
                    }
                }

                UpdateChrome();
                return;
            }

            _requestCloseRecords[id] = RecordAnsweredPrefix + text;
            _requests.AnswerClarify(id, text);
            UpdateChrome();
            return;
        }

        // P2-SPEAK: typed Send is the only path that cancels follow-up as a typed submit — P2-D12
        _voice.OnTypedSubmit();
        // P2-VOICE: Send keeps the composer read and clear, then uses the shared submit — P2-D05
        Composer.Text = "";
        // P3-SHELL: typed send returns focus to the composer when the turn ends — P3-D11
        _returnFocusToComposer = true;
        await SubmitTurnAsync(text, Voice.TurnTiming.KindTyped);
    }

    private async Task SubmitCompressAsync()
    {
        // P8-READ: no You bubble and no streaming turn; the gateway output is one system line — P8-D09
        // P8-READ: a second /compress while slash.exec is in flight is one System line and no second send — P8-D09
        if (!CompressCommand.TryBegin(ref _compressInFlight))
        {
            AddBubble("System", CompressCommand.AlreadyRunningText, mine: false);
            return;
        }

        try
        {
            var output = await _chat.ExecSlashAsync(CompressCommand.CommandText).ConfigureAwait(false);
            Dispatch(() => AddBubble("System", output, mine: false));
        }
        catch (ChatUnreachableException ex)
        {
            Dispatch(() => ShowUnreachable(ex.Message));
        }
        catch (Exception ex)
        {
            Dispatch(() => AddBubble("System", ex.Message, mine: false));
        }
        finally
        {
            CompressCommand.End(ref _compressInFlight);
        }
    }

    private async Task SubmitTurnAsync(string text, string turnKind)
    {
        // P2-VOICE: transcripts and typed sends share this prompt.submit; a live turn is not a reason to hold the transcript — P2-D05
        if (!_sessionReady || _unreachable || text.Length == 0)
        {
            return;
        }

        if (turnKind == Voice.TurnTiming.KindTyped && CompressCommand.IsExactCompress(text))
        {
            // P8-READ: exact /compress is slash.exec and one system line — P8-D09
            await SubmitCompressAsync().ConfigureAwait(false);
            return;
        }

        // P2-VOICE: a transcript during a running turn adds the You bubble and leaves the open assistant bubble streaming — P2-D12
        var duringTurn = _streaming;
        AddBubble("You", text, mine: true);
        if (!duringTurn)
        {
            // P1-CLIENT: show the user turn locally; prompt.submit's status is not the assistant reply — P1-D01
            _streaming = true;
            _turnFinalized = false;
            StatusText.Text = "Sending…";
        }

        UpdateChrome();
        try
        {
            await _chat.SubmitAsync(text).ConfigureAwait(false);
            // P7-LATENCY: submit clock for turn_timing (typed vs voice) — P7-D10
            _voice.NoteTurnSubmit(turnKind, DateTimeOffset.Now);
        }
        catch (ChatUnreachableException ex)
        {
            Dispatch(() => ShowUnreachable(ex.Message));
        }
        catch (Exception ex)
        {
            Dispatch(() =>
            {
                // P2-VOICE: a failed barge-in submit does not settle the turn that is still running — P2-D12
                if (!duringTurn)
                {
                    _streaming = false;
                    _turnFinalized = true;
                }

                StatusText.Text = ex.Message;
                UpdateChrome();
            });
        }
    }

    private async Task SyncVoiceAsync()
    {
        // P2-VOICE: voice.toggle status, then on, runs after the socket reports a session — P2-D07
        try
        {
            // P2-WAKE: SessionReady and Voice-mode entry arm after the voice sync — P2-D04
            await _voice.SyncVoiceAndWakeAsync().ConfigureAwait(false);
        }
        catch (ChatUnreachableException ex)
        {
            Dispatch(() => ShowUnreachable(ex.Message));
        }
        catch (Exception ex)
        {
            Dispatch(() =>
            {
                StatusText.Text = ex.Message;
                UpdateChrome();
            });
        }
    }

    private async void OnMicClick(object sender, RoutedEventArgs e)
    {
        // P2-VOICE: the mic button uses the controller's capture gate and toggle — P2-D04
        await ToggleVoiceCaptureAsync();
    }

    private async void OnVoiceHotkey(KeyboardAccelerator sender, KeyboardAcceleratorInvokedEventArgs args)
    {
        // P2-VOICE: Ctrl+Space is the same capture toggle as the mic button — P2-D04
        args.Handled = true;
        await ToggleVoiceCaptureAsync();
    }

    private async Task ToggleVoiceCaptureAsync()
    {
        // P2-VOICE: the button and the hotkey do nothing unless the controller allows a capture — P2-D12
        if (!_voice.CanStartCapture)
        {
            return;
        }

        try
        {
            await _voice.ToggleCaptureAsync().ConfigureAwait(false);
        }
        catch (ChatUnreachableException ex)
        {
            Dispatch(() => ShowUnreachable(ex.Message));
        }
        catch (Exception ex)
        {
            Dispatch(() =>
            {
                StatusText.Text = ex.Message;
                UpdateChrome();
            });
        }
    }

    private async void OnModeClick(object sender, RoutedEventArgs e)
    {
        // P2-VOICE: the header control switches Voice and Text without a second voice owner — P2-D07
        if (_unreachable || _modeSwitching || string.IsNullOrEmpty(_chat.SessionId))
        {
            return;
        }

        _modeSwitching = true;
        _returnFocusToComposer = false;
        UpdateChrome();
        try
        {
            if (_voice.Mode == VoiceController.ModeVoice)
            {
                // P7-CLARIFY: Voice→Text with quiet single open → show the card — P7-D09
                var quietId = NewestOpenQuietClarifyId();
                await _voice.EnterTextModeAsync().ConfigureAwait(false);
                if (quietId is not null)
                {
                    Dispatch(() => OpenClarifyPanelIfStillOpen(quietId, ClarifyLog.ReasonModeText));
                }
            }
            else
            {
                await _voice.EnterVoiceModeAsync().ConfigureAwait(false);
            }
        }
        catch (ChatUnreachableException ex)
        {
            Dispatch(() => ShowUnreachable(ex.Message));
        }
        catch (Exception ex)
        {
            Dispatch(() =>
            {
                StatusText.Text = ex.Message;
                UpdateChrome();
            });
        }
        finally
        {
            Dispatch(() =>
            {
                _modeSwitching = false;
                UpdateChrome();
            });
        }
    }

    private void OnVoiceChatEnded()
    {
        // P4-ASK: stop phrase while a clarify is open sends Skip, then existing end handling — P4-D14
        if (_requests.HasOpenClarify(_chat.SessionId))
        {
            var id = _requests.NewestOpenClarify(_chat.SessionId);
            if (id is not null)
            {
                _requestCloseRecords[id] = RecordSkipped;
                _requests.SkipClarify(id);
            }
        }

        // P2-VOICE: a spoken stop ends the exchange with a status line and no turn — P2-D05
        StatusText.Text = "Voice chat ended";
        UpdateChrome();
    }

    private void OnTranscriptReady(string text, string? boundClarifyId)
    {
        if (_voice.VoiceGated)
        {
            _voice.NoteGateRefusal(VoiceController.GateRefuseVoiceSubmitReason);
            return;
        }

        // P4-ASK: transcript from a clarify-answer capture answers only that id — P4-D14
        if (!string.IsNullOrEmpty(boundClarifyId))
        {
            if (_requests.GetState(boundClarifyId) == ServerRequestBroker.Lifecycle.Open)
            {
                ApplyVoiceClarifyAnswer(boundClarifyId, text);
                return;
            }

            _voice.NoteLateAnswerDropped(boundClarifyId, text.Length);
            _requests.NoteLateAnswerDropped(boundClarifyId, text.Length);
            ShowRequestNotice(NoticeLateAnswer);
            return;
        }

        // P7-VOICEAUTH: unbound admitted transcripts never answer clarify (newest-clarify removed) — P7-D05
        _ = SubmitTurnAsync(text, Voice.TurnTiming.KindVoice);
    }

    private void ApplyVoiceClarifyAnswer(string id, string text)
    {
        var view = _requests.TryGetClarifyView(id);
        if (view is null)
        {
            // P4-ASK: missing view for an id is a late/stale drop, never silent — P4-D14
            _voice.NoteLateAnswerDropped(id, text.Length);
            _requests.NoteLateAnswerDropped(id, text.Length);
            ShowRequestNotice(NoticeLateAnswer);
            return;
        }

        if (view.IsBatch)
        {
            // P4-ASK: fill first unanswered row; Hermes always wires clarify as questions[] (batch).
            // Auto-send when no unanswered rows remain (one-question = C1; multi stays open for C8) — P4-D14 / K7
            FillFirstUnansweredBatchRow(id, text);
            if (!BatchHasUnansweredRows(id))
            {
                var answers = CollectBatchAnswers(id);
                if (answers.Count > 0)
                {
                    _requestCloseRecords[id] = RecordAnsweredPrefix + string.Join("; ", answers.Values);
                    _requests.AnswerBatch(id, answers);
                }
            }

            UpdateChrome();
            return;
        }

        _requestCloseRecords[id] = RecordAnsweredPrefix + text;
        _requests.AnswerClarify(id, text);
        UpdateChrome();
    }

    private void OnVoiceStatusMessage(string message)
    {
        // P2-VOICE: busy, no speech, and interrupt notices stay on the status line — P2-D08
        StatusText.Text = message;
        UpdateChrome();
    }

    // P4-FEEDBACK: request notices share StatusText with voice so the panel-header mirror sees them — P4-D17
    private void ShowRequestNotice(string text)
    {
        if (_unreachable || string.IsNullOrWhiteSpace(text))
        {
            if (!string.IsNullOrWhiteSpace(text))
            {
                WriteDockLog("request_notice_skipped_unreachable text_len=" + text.Length);
            }

            return;
        }

        StatusText.Text = text;
        UpdateChrome();
    }

    private void ApplyVoiceChrome()
    {
        // P3-STATE: the window assigns chrome from the display record — P3-D03
        _display.UpdateWindowFacts(
            _sessionReady,
            _backend.WebSocketPermitted && !_unreachable,
            _streaming,
            _switchInFlight,
            _historyPending,
            _modeSwitching,
            _unreachable,
            !string.IsNullOrEmpty(_chat.SessionId));
        var s = _display.Current;
        // P3-SHELL: HUD and dock labels are presentation-only upper-case; the model strings stay as they are — P3-D06
        VoiceStateText.Text = VoiceBulletPrefix + s.VoiceLabel.ToUpperInvariant();
        // P4-FEEDBACK: activity line under VOICE; empty when Waiting or reply text — P4-D16
        if (string.IsNullOrEmpty(s.ActivityLine))
        {
            ActivityText.Text = "";
            ActivityText.Visibility = Visibility.Collapsed;
        }
        else
        {
            ActivityText.Text = s.ActivityLine;
            ActivityText.Visibility = Visibility.Visible;
        }

        MicIndicatorText.Text = s.MicLine.ToUpperInvariant();
        ModeButtonLabel.Text = s.ModeWord.ToUpperInvariant();
        MicButtonLabel.Text = s.MicButtonContent.ToUpperInvariant();
        LinkText.Text = s.LinkLabel;
        ModeButton.IsEnabled = s.ModeButtonEnabled;
        MicButton.IsEnabled = s.MicButtonEnabled;
        // P4-REQUEST: approval buttons follow VoiceGated on every chrome refresh — P4-D07
        RefreshApprovalGateButtons();
        SyncLiveBubbleActivity(s.ActivityLine);
    }

    // P4-FEEDBACK: tool events feed the display model and refresh chrome — P4-D16
    private void OnToolStarted(string? toolId, string name)
    {
        _display.OnToolStarted(toolId, name);
        // P7-LATENCY: count tool.start on the open turn — P7-D10
        _voice.NoteTurnToolStart();
        ApplyVoiceChrome();
        UpdateDockVisibility();
    }

    private void OnToolCompleted(string? toolId, string name)
    {
        _display.OnToolCompleted(toolId, name);
        ApplyVoiceChrome();
    }

    private void OnToolGenerating(string name)
    {
        _display.OnToolGenerating(name);
        ApplyVoiceChrome();
        UpdateDockVisibility();
    }

    // P4-FEEDBACK: empty live bubble shows the activity line until reply text arrives — P4-D16
    private void SyncLiveBubbleActivity(string activityLine)
    {
        if (_live is null || _turnFinalized)
        {
            return;
        }

        if (!string.IsNullOrEmpty(_live.Body.Text))
        {
            _live.Activity.Visibility = Visibility.Collapsed;
            _live.Activity.Text = "";
            return;
        }

        if (string.IsNullOrEmpty(activityLine))
        {
            _live.Activity.Visibility = Visibility.Collapsed;
            _live.Activity.Text = "";
            return;
        }

        _live.Activity.Text = activityLine;
        _live.Activity.Visibility = Visibility.Visible;
    }

    private void OnSubmitAcknowledged(string status)
    {
        // P1-CLIENT: streaming, queued, steered, and redirected are acks, not reply text — P1-D01
        // P3-STATE: a turn event resets the stale-thinking clock — P3-D04
        _display.NoteTurnActivity();
        if (_unreachable || _turnFinalized)
        {
            return;
        }

        // P3-LOOK: an accepted turn clears the sticky error notice — P3-D18
        _lastTurnErrored = false;
        _streaming = true;
        StatusText.Text = status switch
        {
            "streaming" => "Responding…",
            "queued" => "Queued. Waiting for the current turn to finish.",
            "steered" => "Steered into the current turn.",
            "redirected" => "Redirected the current turn.",
            _ => "Waiting…",
        };
        UpdateChrome();
    }

    private async void OnCancelClick(object sender, RoutedEventArgs e)
    {
        if (!_streaming || _unreachable)
        {
            return;
        }

        // P1-CLIENT: session.interrupt can wait on agent startup; show that the click was accepted — P1-D01
        StatusText.Text = "Cancelling…";
        CancelButton.IsEnabled = false;
        try
        {
            // P1-CLIENT: the interrupt result returns the UI to usable before message.complete arrives — P1-D01
            await _chat.InterruptAsync().ConfigureAwait(false);
        }
        catch (ChatUnreachableException ex)
        {
            Dispatch(() => ShowUnreachable(ex.Message));
        }
        catch (Exception ex)
        {
            Dispatch(() =>
            {
                StatusText.Text = ex.Message;
                UpdateChrome();
            });
        }
    }

    // P4-FEEDBACK: Stop speaking — voice only; turn and text keep going — P4-FB-STOP
    private async void OnStopSpeakingClick(object sender, RoutedEventArgs e)
    {
        if (!_voice.CanStopSpeaking || _unreachable)
        {
            return;
        }

        StopSpeakingButton.IsEnabled = false;
        try
        {
            await _voice.StopSpeakingAsync().ConfigureAwait(false);
        }
        catch (ChatUnreachableException ex)
        {
            Dispatch(() => ShowUnreachable(ex.Message));
        }
        catch (Exception ex)
        {
            Dispatch(() =>
            {
                StatusText.Text = ex.Message;
                UpdateChrome();
            });
        }

        Dispatch(UpdateChrome);
    }

    private void OnInterruptAcknowledged(string status)
    {
        if (!string.Equals(status, "interrupted", StringComparison.Ordinal))
        {
            StatusText.Text = string.IsNullOrEmpty(status) ? "Interrupt was not accepted." : status;
            UpdateChrome();
            return;
        }

        // P1-CLIENT: settle from the RPC once; a later interrupted complete for this turn is ignored — P1-D01
        FinishTurn("interrupted", "", fromComplete: false);
    }

    private void OnMessageStarted()
    {
        // P3-STATE: a turn event resets the stale-thinking clock — P3-D04
        _display.NoteTurnActivity();
        if (_unreachable)
        {
            return;
        }

        // P2-VOICE: open a new assistant bubble when none is live; clear only a second message.start before message.complete — P2-D12
        if (_live is not null && !_turnFinalized)
        {
            _live.Body.Text = "";
            _live.Badge.Visibility = Visibility.Collapsed;
            ApplyBubbleChrome(_live.Border, mine: false, "complete");
            // P4-FEEDBACK: cleared bubble can show tools again until text arrives — P4-D16
            _display.NoteLiveBubbleReset();
        }
        else
        {
            _live = AddLiveBubble();
        }

        _turnFinalized = false;
        _streaming = true;
        // P2-SPEAK: the controller owns the speaking estimate; the window only forwards the event — P2-D12
        _voice.OnTurnStarted();
        StatusText.Text = "Responding…";
        UpdateChrome();
        ScrollToEnd();
    }

    private void OnMessageDelta(string chunk)
    {
        // P3-STATE: a turn event resets the stale-thinking clock — P3-D04
        _display.NoteTurnActivity();
        if (_unreachable || _turnFinalized)
        {
            return;
        }

        // P1-CLIENT: each message.delta appends one chunk into the prepared response — P1-D01
        _live ??= AddLiveBubble();
        var hadText = _live.Body.Text.Length > 0;
        _live.Body.Text += chunk;
        // P4-FEEDBACK: first reply text clears the activity line — P4-D16
        if (!hadText && _live.Body.Text.Length > 0)
        {
            _display.NoteReplyTextStarted();
            ApplyVoiceChrome();
        }

        // P2-SPEAK: the controller counts the accumulated reply, not this chunk alone — P2-D12
        _voice.OnTurnDelta(chunk);
        ScrollToEnd();
    }

    private void OnMessageCompleted(string status, string text)
    {
        if (_unreachable)
        {
            return;
        }

        // P1-CLIENT: complete, error, and interrupted end the turn with different chrome — P1-D01
        FinishTurn(string.IsNullOrEmpty(status) ? "complete" : status, text, fromComplete: true);
    }

    private void FinishTurn(string status, string text, bool fromComplete)
    {
        if (string.Equals(status, "interrupted", StringComparison.Ordinal))
        {
            if (fromComplete && _orphanInterruptedCompletes > 0)
            {
                // P1-CLIENT: this complete is the pair of an interrupt result already applied — P1-D01
                _orphanInterruptedCompletes--;
                return;
            }

            if (_turnFinalized)
            {
                return;
            }

            _turnFinalized = true;
            _streaming = false;
            if (!fromComplete)
            {
                _orphanInterruptedCompletes++;
            }

            // P4-FEEDBACK: interrupt clears the activity set — P4-D16
            _display.ClearToolActivity();
            StyleLive("interrupted", text, replaceText: fromComplete && text.Length > 0);
            // P2-VOICE: the styled bubble stays in the transcript; the next message.start opens a new one — P2-D12
            _live = null;
            // P2-SPEAK: interrupted complete starts no follow-up timer — P2-D12
            _voice.OnTurnCompleted("interrupted");
            StatusText.Text = "Interrupted.";
            UpdateChrome();
            return;
        }

        if (_turnFinalized)
        {
            return;
        }

        _turnFinalized = true;
        _streaming = false;
        var outcome = string.Equals(status, "error", StringComparison.Ordinal) ? "error" : "complete";
        if (outcome == "error")
        {
            // P3-LOOK: last-turn error stays until the next turn is accepted — P3-D18
            _lastTurnErrored = true;
        }

        // P4-FEEDBACK: turn end clears the activity set — P4-D16
        _display.ClearToolActivity();
        StyleLive(outcome, text, replaceText: text.Length > 0);
        // P2-VOICE: the styled bubble stays in the transcript; the next message.start opens a new one — P2-D12
        _live = null;
        // P2-SPEAK: complete starts the follow-up timer; error does not — P2-D12
        _voice.OnTurnCompleted(outcome);
        StatusText.Text = outcome == "error" ? "The turn ended with an error." : "Session ready.";
        UpdateChrome();
    }

    private void OnRouted(string note)
    {
        // P1-CLIENT: non-turn frames update the detail line and never the assistant text — P1-D01
        // P3-STATE: a turn event resets the stale-thinking clock — P3-D04
        _display.NoteTurnActivity();
        if (_unreachable || string.IsNullOrWhiteSpace(note))
        {
            return;
        }

        // P1-CLIENT: keep the stored session ids visible when a non-chat frame is routed here — P1-D01
        _routedNote = note;
        DetailText.Text = _sessionDetail.Length == 0 ? note : note + Environment.NewLine + _sessionDetail;
    }

    private void ShowUnreachable(string reason)
    {
        // P1-CLIENT: socket close and health failure share one visible stop, with input turned off — P1-D01
        if (_unreachable)
        {
            return;
        }

        _unreachable = true;
        _streaming = false;
        _sessionReady = false;
        // P4-ASK: disconnect abandons pending question speech/capture — P4-D13
        _voice.AbandonPendingQuestion("unreachable");
        // P4-FEEDBACK: disconnect clears the activity set — P4-D16
        _display.ClearToolActivity();
        StatusText.Text = reason.StartsWith("Backend unreachable", StringComparison.Ordinal)
            ? reason
            : "Backend unreachable. " + reason;
        DetailText.Text = "hermes serve is not reachable. This window will not keep waiting.";
        UpdateChrome();
    }

    private void OnComposerKeyDown(object sender, KeyRoutedEventArgs e)
    {
        // P1-CLIENT: Enter submits; Shift+Enter keeps a newline in the composer — P1-D01
        if (e.Key != VirtualKey.Enter)
        {
            return;
        }

        var shift = InputKeyboardSource.GetKeyStateForCurrentThread(VirtualKey.Shift);
        if (shift.HasFlag(CoreVirtualKeyStates.Down))
        {
            return;
        }

        e.Handled = true;
        OnSendClick(Composer, new RoutedEventArgs());
    }

    private void StyleLive(string outcome, string text, bool replaceText)
    {
        _live ??= AddLiveBubble();
        if (replaceText)
        {
            _live.Body.Text = text;
        }

        ApplyBubbleChrome(_live.Border, mine: false, outcome);
        if (outcome is "error" or "interrupted")
        {
            _live.Badge.Text = outcome == "error" ? "Error" : "Interrupted";
            _live.Badge.Foreground = Token<Brush>(outcome == "error" ? TokenError : TokenAmberMuted);
            _live.Badge.Visibility = Visibility.Visible;
        }
        else
        {
            _live.Badge.Visibility = Visibility.Collapsed;
        }

        ScrollToEnd();
    }

    private LiveResponse AddLiveBubble()
    {
        // P1-CLIENT: a fresh assistant bubble is the response area for this turn — P1-D01
        var badge = new TextBlock { Style = Token<Style>(TokenBubbleHeadingStyle), Visibility = Visibility.Collapsed };
        // P4-FEEDBACK: activity sits above the body while the reply is still empty — P4-D16
        var activity = new TextBlock
        {
            Style = Token<Style>(TokenBubbleHeadingStyle),
            TextWrapping = TextWrapping.WrapWholeWords,
            Visibility = Visibility.Collapsed,
        };
        var body = new TextBlock { Style = Token<Style>(TokenBodyStyle), TextWrapping = TextWrapping.WrapWholeWords, IsTextSelectionEnabled = true };
        var stack = new StackPanel { Spacing = Token<double>(TokenSpace4) };
        stack.Children.Add(badge);
        stack.Children.Add(activity);
        stack.Children.Add(body);
        var border = new Border
        {
            Child = stack,
            Padding = new Thickness(Token<double>(TokenBubblePadding)),
            CornerRadius = new CornerRadius(Token<double>(TokenBubbleCornerRadius)),
            HorizontalAlignment = HorizontalAlignment.Left,
            MaxWidth = Token<double>(TokenBubbleMaxWidth),
        };
        ApplyBubbleChrome(border, mine: false, "complete");
        Transcript.Children.Add(border);
        return new LiveResponse(border, badge, activity, body);
    }

    private void AddBubble(string title, string text, bool mine)
    {
        // P1-CLIENT: the user's own send is local; it is not a socket frame — P1-D01
        var heading = new TextBlock { Text = title, Style = Token<Style>(TokenBubbleHeadingStyle) };
        var body = new TextBlock { Text = text, Style = Token<Style>(TokenBodyStyle), TextWrapping = TextWrapping.WrapWholeWords, IsTextSelectionEnabled = true };
        var stack = new StackPanel { Spacing = Token<double>(TokenSpace4) };
        stack.Children.Add(heading);
        stack.Children.Add(body);
        var border = new Border
        {
            Child = stack,
            Padding = new Thickness(Token<double>(TokenBubblePadding)),
            CornerRadius = new CornerRadius(Token<double>(TokenBubbleCornerRadius)),
            HorizontalAlignment = mine ? HorizontalAlignment.Right : HorizontalAlignment.Left,
            MaxWidth = Token<double>(TokenBubbleMaxWidth),
        };
        ApplyBubbleChrome(border, mine, "complete");
        Transcript.Children.Add(border);
        ScrollToEnd();
    }

    // P4-REQUEST: clarify and approval cards live in the transcript — P4-D07 / P4-D08
    private void OnClarifyOpened(string id, ServerRequestBroker.ClarifyView view)
    {
        if (_historyPending)
        {
            return;
        }

        if (_requests.GetState(id) != ServerRequestBroker.Lifecycle.Open)
        {
            return;
        }

        if (_requestCards.ContainsKey(id))
        {
            return;
        }

        var fresh = _requests.TryGetClarifyView(id);
        if (fresh is null)
        {
            return;
        }

        var card = BuildClarifyCard(id, fresh);
        _requestCards[id] = card;
        Transcript.Children.Add(card);

        // P7-CLARIFY: quiet single in Voice — build card, never auto-open panel — P7-D09
        var quiet = _voice.Mode == VoiceController.ModeVoice && IsQuietClarifyView(fresh);
        if (quiet)
        {
            _quietClarifyIds.Add(id);
            var choiceCount = fresh.IsBatch
                ? (fresh.Questions.Count > 0 ? fresh.Questions[0].Choices.Count : 0)
                : fresh.Choices.Count;
            _voice.NoteClarifyTimeline(string.Format(
                ClarifyLog.QuietFormat,
                id,
                ClarifyShape.ShapeSingle,
                choiceCount));
            // P7-CLARIFY: quiet card stays in view when the panel is already open — P7-D09
            if (ConversationOverlay.Visibility == Visibility.Visible)
            {
                ScrollToEnd();
            }
        }
        else
        {
            EnsureConversationOpen();
            _voice.NoteClarifyTimeline(string.Format(
                ClarifyLog.PanelOpenFormat,
                fresh.Replayed ? ClarifyLog.ReasonReshow : ClarifyLog.ReasonClarifyOpen,
                id));
        }

        UpdateChrome();

        // P4-ASK: Voice mode speaks each clarify id once after the card is rendered Open — P4-D13
        if (_voice.Mode == VoiceController.ModeVoice
            && _requests.GetState(id) == ServerRequestBroker.Lifecycle.Open
            && !_spokenClarifyIds.Contains(id)
            && string.Equals(fresh.SessionId, _chat.SessionId, StringComparison.Ordinal))
        {
            _spokenClarifyIds.Add(id);
            _ = _voice.SpeakQuestionAsync(id, fresh);
        }
    }

    private void OnApprovalOpened(string id, ServerRequestBroker.ApprovalView view)
    {
        if (_historyPending)
        {
            return;
        }

        if (_requests.GetState(id) != ServerRequestBroker.Lifecycle.Open)
        {
            return;
        }

        if (_requestCards.ContainsKey(id))
        {
            return;
        }

        var fresh = _requests.TryGetApprovalView(id);
        if (fresh is null)
        {
            return;
        }

        var card = BuildApprovalCard(id, fresh);
        _requestCards[id] = card;
        // P7-LATENCY: approval card shown for open turn — P7-D10
        _voice.NoteTurnApproval();
        Transcript.Children.Add(card);
        EnsureConversationOpen();
        UpdateChrome();
    }

    private void OnRequestClosed(string id, ServerRequestBroker.CloseOutcome outcome)
    {
        // P4-ASK: closing the card abandons pending speak/capture for that id — P4-D13
        _voice.AbandonPendingQuestionIfId(id, "request_closed");

        if (!_requestCards.TryGetValue(id, out var card))
        {
            _requestCloseRecords.Remove(id);
            _quietClarifyIds.Remove(id);
            _noAnswerPanelOpenedIds.Remove(id);
            UpdateChrome();
            return;
        }

        var record = _requestCloseRecords.TryGetValue(id, out var summary)
            ? summary
            : DefaultCloseRecord(outcome);
        _requestCloseRecords.Remove(id);
        CollapseCardToRecord(id, card, record);
        _quietClarifyIds.Remove(id);
        _noAnswerPanelOpenedIds.Remove(id);
        UpdateChrome();
    }

    private static string DefaultCloseRecord(ServerRequestBroker.CloseOutcome outcome) => outcome switch
    {
        ServerRequestBroker.CloseOutcome.Cancelled => RecordCancelled,
        ServerRequestBroker.CloseOutcome.SendFailed => RecordSendFailed,
        ServerRequestBroker.CloseOutcome.Declined => RecordDeclined,
        ServerRequestBroker.CloseOutcome.WithdrawnWhileAway => RecordWithdrawn,
        ServerRequestBroker.CloseOutcome.Answered => RecordAnsweredPrefix.TrimEnd(' ', ':'),
        _ => RecordDeclined,
    };

    private void CollapseCardToRecord(string id, FrameworkElement card, string record)
    {
        var index = Transcript.Children.IndexOf(card);
        if (index < 0)
        {
            _requestCards.Remove(id);
            return;
        }

        var body = new TextBlock
        {
            Text = record,
            Style = Token<Style>(TokenBodyStyle),
            TextWrapping = TextWrapping.WrapWholeWords,
            IsTextSelectionEnabled = true,
        };
        var border = new Border
        {
            Child = body,
            Style = Token<Style>(TokenPanelBorderStyle),
            Padding = new Thickness(Token<double>(TokenBubblePadding)),
            CornerRadius = new CornerRadius(Token<double>(TokenBubbleCornerRadius)),
            HorizontalAlignment = HorizontalAlignment.Left,
            MaxWidth = Token<double>(TokenBubbleMaxWidth),
        };
        Transcript.Children[index] = border;
        _requestCards.Remove(id);
        // P7-CLARIFY: quiet single in Voice — collapse without auto-opening the panel — P7-D09
        if (!(_voice.Mode == VoiceController.ModeVoice && _quietClarifyIds.Contains(id)))
        {
            EnsureConversationOpen();
            _voice.NoteClarifyTimeline(string.Format(
                ClarifyLog.PanelOpenFormat,
                ClarifyLog.ReasonCollapse,
                id));
        }

        ScrollToEnd();
    }

    private Border BuildClarifyCard(string id, ServerRequestBroker.ClarifyView view)
    {
        var stack = new StackPanel { Spacing = Token<double>(TokenSpace8) };
        stack.Children.Add(new TextBlock { Text = HeadingClarify, Style = Token<Style>(TokenBubbleHeadingStyle) });

        BatchCardState? batchState = null;
        if (view.IsBatch)
        {
            batchState = new BatchCardState();
            foreach (var question in view.Questions)
            {
                var row = BuildClarifyQuestionBlock(
                    question.Question,
                    question.Choices,
                    question.MultiSelect,
                    question.PrefillAnswer,
                    onChoice: bare =>
                    {
                        if (batchState.Rows.TryGetValue(question.Qid, out var state))
                        {
                            state.FreeText.Text = bare;
                        }
                    },
                    out var freeText,
                    out var checks);
                if (!string.IsNullOrEmpty(question.PrefillAnswer))
                {
                    freeText.Text = question.PrefillAnswer;
                }

                batchState.Rows[question.Qid] = new BatchRowState(freeText, checks, question.MultiSelect);
                stack.Children.Add(row);
            }

            var batchActions = new StackPanel { Orientation = Orientation.Horizontal, Spacing = Token<double>(TokenSpace8) };
            var batchSend = MakeTextButton(LabelSend, (_, _) =>
            {
                if (_requests.GetState(id) != ServerRequestBroker.Lifecycle.Open)
                {
                    return;
                }

                var answers = new Dictionary<string, string>(StringComparer.Ordinal);
                foreach (var (qid, row) in batchState.Rows)
                {
                    answers[qid] = ReadRowAnswer(row);
                }

                _requestCloseRecords[id] = RecordAnsweredPrefix + string.Join("; ", answers.Values);
                _requests.AnswerBatch(id, answers);
            });
            var batchSkip = MakeTextButton(LabelSkip, (_, _) =>
            {
                _requestCloseRecords[id] = RecordSkipped;
                _requests.SkipClarify(id);
            });
            batchActions.Children.Add(batchSend);
            batchActions.Children.Add(batchSkip);
            stack.Children.Add(batchActions);
        }
        else
        {
            var block = BuildClarifyQuestionBlock(
                view.Question,
                view.Choices,
                view.MultiSelect,
                prefill: "",
                onChoice: bare =>
                {
                    _requestCloseRecords[id] = RecordAnsweredPrefix + bare;
                    _requests.AnswerClarify(id, bare);
                },
                out var freeText,
                out var checks);

            stack.Children.Add(block);
            var actions = new StackPanel { Orientation = Orientation.Horizontal, Spacing = Token<double>(TokenSpace8) };
            var send = MakeTextButton(LabelSend, (_, _) =>
            {
                if (_requests.GetState(id) != ServerRequestBroker.Lifecycle.Open)
                {
                    return;
                }

                if (view.MultiSelect)
                {
                    var labels = checks.Where(c => c.IsChecked == true).Select(c => (string)c.Tag).ToList();
                    if (labels.Count == 0 && freeText.Text.Trim().Length > 0)
                    {
                        _requestCloseRecords[id] = RecordAnsweredPrefix + freeText.Text.Trim();
                        _requests.AnswerClarify(id, freeText.Text.Trim());
                        return;
                    }

                    _requestCloseRecords[id] = RecordAnsweredPrefix + string.Join(", ", labels);
                    _requests.AnswerClarifyMulti(id, labels);
                    return;
                }

                var text = freeText.Text.Trim();
                if (text.Length == 0)
                {
                    return;
                }

                _requestCloseRecords[id] = RecordAnsweredPrefix + text;
                _requests.AnswerClarify(id, text);
            });
            var skip = MakeTextButton(LabelSkip, (_, _) =>
            {
                _requestCloseRecords[id] = RecordSkipped;
                _requests.SkipClarify(id);
            });
            actions.Children.Add(send);
            actions.Children.Add(skip);
            stack.Children.Add(actions);
        }

        var border = new Border
        {
            Child = stack,
            Style = Token<Style>(TokenPanelBorderStyle),
            Padding = new Thickness(Token<double>(TokenBubblePadding)),
            CornerRadius = new CornerRadius(Token<double>(TokenBubbleCornerRadius)),
            HorizontalAlignment = HorizontalAlignment.Left,
            MaxWidth = Token<double>(TokenBubbleMaxWidth),
            Tag = batchState,
        };
        return border;
    }

    private FrameworkElement BuildClarifyQuestionBlock(
        string question,
        IReadOnlyList<string> choices,
        bool multiSelect,
        string prefill,
        Action<string> onChoice,
        out TextBox freeText,
        out List<CheckBox> checks)
    {
        var stack = new StackPanel { Spacing = Token<double>(TokenSpace4) };
        stack.Children.Add(new TextBlock
        {
            Text = question,
            Style = Token<Style>(TokenBodyStyle),
            TextWrapping = TextWrapping.WrapWholeWords,
            IsTextSelectionEnabled = true,
        });

        checks = new List<CheckBox>();
        if (multiSelect)
        {
            foreach (var choice in choices)
            {
                var bare = ServerRequestBroker.StripRecommended(choice);
                var row = new StackPanel { Orientation = Orientation.Horizontal, Spacing = Token<double>(TokenSpace4) };
                var box = new CheckBox
                {
                    Content = bare,
                    Tag = bare,
                    Foreground = Token<Brush>(TokenAmberMuted),
                };
                checks.Add(box);
                row.Children.Add(box);
                if (!string.Equals(choice.Trim(), bare, StringComparison.Ordinal))
                {
                    row.Children.Add(new TextBlock
                    {
                        Text = LabelRecommended,
                        Style = Token<Style>(TokenBodyStyle),
                        Foreground = Token<Brush>(TokenAmberMuted),
                        VerticalAlignment = VerticalAlignment.Center,
                    });
                }

                stack.Children.Add(row);
            }
        }
        else
        {
            foreach (var choice in choices)
            {
                var bare = ServerRequestBroker.StripRecommended(choice);
                var row = new StackPanel { Orientation = Orientation.Horizontal, Spacing = Token<double>(TokenSpace4) };
                var button = MakeTextButton(bare, (_, _) => onChoice(bare));
                row.Children.Add(button);
                if (!string.Equals(choice.Trim(), bare, StringComparison.Ordinal))
                {
                    row.Children.Add(new TextBlock
                    {
                        Text = LabelRecommended,
                        Style = Token<Style>(TokenBodyStyle),
                        Foreground = Token<Brush>(TokenAmberMuted),
                        VerticalAlignment = VerticalAlignment.Center,
                    });
                }

                stack.Children.Add(row);
            }
        }

        freeText = new TextBox
        {
            Style = Token<Style>(TokenComposerStyle),
            AcceptsReturn = false,
            TextWrapping = TextWrapping.Wrap,
            Text = prefill,
        };
        stack.Children.Add(freeText);
        return stack;
    }

    private Border BuildApprovalCard(string id, ServerRequestBroker.ApprovalView view)
    {
        var stack = new StackPanel { Spacing = Token<double>(TokenSpace8) };
        stack.Children.Add(new TextBlock { Text = HeadingApproval, Style = Token<Style>(TokenBubbleHeadingStyle) });
        if (!string.IsNullOrEmpty(view.Description))
        {
            stack.Children.Add(new TextBlock
            {
                Text = view.Description,
                Style = Token<Style>(TokenBodyStyle),
                TextWrapping = TextWrapping.WrapWholeWords,
                IsTextSelectionEnabled = true,
            });
        }

        // FLAG: no monospace token in ZolaTokens; Cascadia Mono used for the command line only.
        stack.Children.Add(new TextBlock
        {
            Text = view.Command,
            Style = Token<Style>(TokenBodyStyle),
            FontFamily = new FontFamily(CommandFontFamilyName),
            TextWrapping = TextWrapping.WrapWholeWords,
            IsTextSelectionEnabled = true,
        });

        var gated = _voice.VoiceGated;
        var approve = MakeTextButton(LabelApproveOnce, (_, _) => OnApproveOnceClick(id, view.Command));
        var deny = MakeTextButton(LabelDeny, (_, _) => OnDenyClick(id, view.Command));
        approve.IsEnabled = !gated;
        deny.IsEnabled = !gated;
        var actions = new StackPanel { Orientation = Orientation.Horizontal, Spacing = Token<double>(TokenSpace8) };
        actions.Children.Add(approve);
        actions.Children.Add(deny);
        stack.Children.Add(actions);

        var border = new Border
        {
            Child = stack,
            Style = Token<Style>(TokenPanelBorderStyle),
            Padding = new Thickness(Token<double>(TokenBubblePadding)),
            CornerRadius = new CornerRadius(Token<double>(TokenBubbleCornerRadius)),
            HorizontalAlignment = HorizontalAlignment.Left,
            MaxWidth = Token<double>(TokenBubbleMaxWidth),
            Tag = new ApprovalCardState(approve, deny),
        };
        return border;
    }

    private void OnApproveOnceClick(string id, string command)
    {
        // P4-REQUEST: re-check VoiceGated before ApproveOnce — P4-D07
        if (_voice.VoiceGated)
        {
            _requests.NoteGatedClickRefused(id);
            RefreshApprovalGateButtons();
            return;
        }

        _requestCloseRecords[id] = RecordApprovedPrefix + command;
        _requests.ApproveOnce(id);
    }

    private void OnDenyClick(string id, string command)
    {
        // P4-REQUEST: re-check VoiceGated before Deny — P4-D07
        if (_voice.VoiceGated)
        {
            _requests.NoteGatedClickRefused(id);
            RefreshApprovalGateButtons();
            return;
        }

        _requestCloseRecords[id] = RecordDeniedPrefix + command;
        _requests.Deny(id);
    }

    private void RefreshApprovalGateButtons()
    {
        var gated = _voice.VoiceGated;
        foreach (var card in _requestCards.Values)
        {
            if (card is Border { Tag: ApprovalCardState state })
            {
                state.ApproveButton.IsEnabled = !gated;
                state.DenyButton.IsEnabled = !gated;
            }
        }
    }

    // P7-CLARIFY: quiet-single classification shared by panel / typed / speech paths — P7-D09
    private static bool IsQuietClarifyView(ServerRequestBroker.ClarifyView view) =>
        VoiceController.IsQuietSingleView(view);

    private string? NewestOpenQuietClarifyId()
    {
        var id = _requests.NewestOpenClarify(_chat.SessionId);
        if (id is null)
        {
            return null;
        }

        var view = _requests.TryGetClarifyView(id);
        return view is not null && IsQuietClarifyView(view) ? id : null;
    }

    private void OpenClarifyPanelIfStillOpen(string id, string reason)
    {
        if (_requests.GetState(id) != ServerRequestBroker.Lifecycle.Open)
        {
            return;
        }

        EnsureConversationOpen();
        _voice.NoteClarifyTimeline(string.Format(ClarifyLog.PanelOpenFormat, reason, id));
    }

    private void OnClarifyNoAnswer(string id)
    {
        // P7-CLARIFY: Voice quiet single, request still open, panel once — P7-D09
        if (_voice.Mode != VoiceController.ModeVoice)
        {
            return;
        }

        if (_requests.GetState(id) != ServerRequestBroker.Lifecycle.Open)
        {
            return;
        }

        if (!_quietClarifyIds.Contains(id))
        {
            return;
        }

        if (!_noAnswerPanelOpenedIds.Add(id))
        {
            return;
        }

        OpenClarifyPanelIfStillOpen(id, ClarifyLog.ReasonNoAnswer);
    }

    private void FillFirstUnansweredBatchRow(string id, string text)
    {
        if (!_requestCards.TryGetValue(id, out var card) || card is not Border { Tag: BatchCardState batch })
        {
            return;
        }

        foreach (var row in batch.Rows.Values)
        {
            if (row.MultiSelect)
            {
                if (row.Checks.Any(c => c.IsChecked == true))
                {
                    continue;
                }
            }
            else if (row.FreeText.Text.Trim().Length > 0)
            {
                continue;
            }

            row.FreeText.Text = text;
            return;
        }
    }

    // P4-ASK: true while any batch row still needs an answer — P4-D14 / K7
    private bool BatchHasUnansweredRows(string id)
    {
        if (!_requestCards.TryGetValue(id, out var card) || card is not Border { Tag: BatchCardState batch })
        {
            return true;
        }

        foreach (var row in batch.Rows.Values)
        {
            if (row.MultiSelect)
            {
                if (!row.Checks.Any(c => c.IsChecked == true) && row.FreeText.Text.Trim().Length == 0)
                {
                    return true;
                }
            }
            else if (row.FreeText.Text.Trim().Length == 0)
            {
                return true;
            }
        }

        return false;
    }

    private Dictionary<string, string> CollectBatchAnswers(string id)
    {
        var answers = new Dictionary<string, string>(StringComparer.Ordinal);
        if (!_requestCards.TryGetValue(id, out var card) || card is not Border { Tag: BatchCardState batch })
        {
            return answers;
        }

        foreach (var (qid, row) in batch.Rows)
        {
            answers[qid] = ReadRowAnswer(row);
        }

        return answers;
    }

    private static string ReadRowAnswer(BatchRowState row)
    {
        if (row.MultiSelect)
        {
            var labels = row.Checks.Where(c => c.IsChecked == true).Select(c => (string)c.Tag).ToList();
            if (labels.Count > 0)
            {
                return JsonSerializer.Serialize(labels);
            }
        }

        return row.FreeText.Text.Trim();
    }

    private Button MakeTextButton(string content, RoutedEventHandler handler)
    {
        var button = new Button
        {
            Content = content,
            Style = Token<Style>(TokenTextButtonStyle),
        };
        button.Click += handler;
        return button;
    }

    private void EnsureConversationOpen()
    {
        if (ConversationOverlay.Visibility != Visibility.Visible)
        {
            HideSessions();
            SizeConversationOverlay();
            ConversationOverlay.Visibility = Visibility.Visible;
            UpdateDockVisibility();
            UpdateNoticeVisibility();
        }

        ScrollToEnd();
    }

    private sealed class ApprovalCardState(Button approveButton, Button denyButton)
    {
        public Button ApproveButton { get; } = approveButton;
        public Button DenyButton { get; } = denyButton;
    }

    private sealed class BatchRowState(TextBox freeText, List<CheckBox> checks, bool multiSelect)
    {
        public TextBox FreeText { get; } = freeText;
        public List<CheckBox> Checks { get; } = checks;
        public bool MultiSelect { get; } = multiSelect;
    }

    private sealed class BatchCardState
    {
        public Dictionary<string, BatchRowState> Rows { get; } = new(StringComparer.Ordinal);
    }

    private void UpdateChrome()
    {
        // P1-CLIENT: the composer is usable only with a session, no live turn, and a live backend — P1-D01
        // P4-REQUEST: open clarify is the only streaming exception for canType — P4-D09
        var openClarify = _requests.HasOpenClarify(_chat.SessionId);
        // P4-ASK: awaiting fact from broker open clarify for current session; clear on disconnect — P4-D15
        _voice.SetAwaitingAnswer(!_unreachable && openClarify);
        var canType = _sessionReady && !_unreachable && !_switchInFlight && !_historyPending
            && (!_streaming || openClarify);
        var composerWasEnabled = Composer.IsEnabled;
        Composer.IsEnabled = canType;
        if (openClarify)
        {
            Composer.PlaceholderText = PlaceholderAnswerClarify;
        }
        else if (_sessionReady && !_historyPending)
        {
            Composer.PlaceholderText = PlaceholderMessage;
        }

        // P3-SHELL: typed send returns focus to the composer when the turn ends — P3-D11
        if (!composerWasEnabled && canType && _returnFocusToComposer && ConversationOverlay.Visibility == Visibility.Visible)
        {
            Composer.Focus(FocusState.Programmatic);
            _returnFocusToComposer = false;
        }
        SendButton.IsEnabled = canType && Composer.Text.Trim().Length > 0;
        CancelButton.IsEnabled = _streaming && !_unreachable;
        // P3-SHELL: Cancel is in the dock only while a turn is live — P3-D11
        CancelButton.Visibility = _streaming && !_unreachable ? Visibility.Visible : Visibility.Collapsed;
        // P4-FEEDBACK: Stop is separate from Cancel; visibility from VC facts — P4-FB-STOP
        var canStop = _voice.CanStopSpeaking && !_unreachable;
        StopSpeakingButton.IsEnabled = canStop;
        StopSpeakingButton.Visibility = canStop ? Visibility.Visible : Visibility.Collapsed;
        // P1-SESSION: the list can open beside a live chat; create and resume wait until the turn is idle — P1-D04
        var backendUp = _backend.WebSocketPermitted && !_unreachable && !_switchInFlight;
        SessionsButton.IsEnabled = backendUp;
        NewSessionButton.IsEnabled = backendUp && !_streaming && !_historyPending;
        // P2-VOICE: composer enablement stays the Phase 1 rule; voice chrome is applied beside it — P2-D07
        ApplyVoiceChrome();
        UpdateSessionHud();
        UpdateDockVisibility();
        UpdateNoticeVisibility();
    }

    private async void OnSessionsToggle(object sender, RoutedEventArgs e)
    {
        // P1-SESSION: the same control opens and closes the list; the chat column stays in place — P1-D04
        if (_sessionsOpen)
        {
            HideSessions();
            return;
        }

        // P3-SHELL: one panel at a time; opening sessions collapses the overlay — P3-D11
        _returnFocusToComposer = false;
        CollapseConversationOverlay();
        _sessionsOpen = true;
        SessionPanel.Visibility = Visibility.Visible;
        UpdateDockVisibility();
        BindSessions();
        try
        {
            var listed = await SessionCatalog.ListAsync(_backend, CancellationToken.None).ConfigureAwait(false);
            Dispatch(() => ApplyServerSessions(listed));
        }
        catch (Exception ex)
        {
            Dispatch(() =>
            {
                DetailText.Text = ex.Message;
                BindSessions();
            });
        }
    }

    private void OnCloseSessionsClick(object sender, RoutedEventArgs e)
    {
        // P1-SESSION: the panel's own close control hides the list and returns focus to the composer — P1-D04
        HideSessions();
    }

    private void HideSessions()
    {
        // P1-SESSION: hiding the list leaves the transcript where it was and focuses the composer — P1-D04
        _sessionsOpen = false;
        SessionPanel.Visibility = Visibility.Collapsed;
        UpdateDockVisibility();
        UpdateNoticeVisibility();
        // P3-SHELL: closing a panel returns focus to the root so Ctrl+Space still works — P3-D11
        RootGrid.Focus(FocusState.Programmatic);
    }

    private async void OnNewSessionClick(object sender, RoutedEventArgs e)
    {
        if (_switchInFlight || _streaming || _unreachable || _historyPending)
        {
            return;
        }

        // P1-SESSION: session.create on a fresh socket; the returned stored id is listed before any prompt — P1-D04
        _switchInFlight = true;
        _historyPending = false;
        _sessionReady = false;
        ClearTranscript();
        StatusText.Text = "Starting a new session…";
        UpdateChrome();
        try
        {
            await _chat.BeginNewSessionAsync().ConfigureAwait(false);
        }
        catch (Exception ex)
        {
            var message = ex.Message;
            var stillLive = !string.IsNullOrEmpty(_chat.SessionId);
            Dispatch(() =>
            {
                _sessionReady = stillLive;
                StatusText.Text = message;
            });
        }
        finally
        {
            Dispatch(() =>
            {
                _switchInFlight = false;
                UpdateChrome();
            });
        }
    }

    private async void OnSessionItemClick(object sender, ItemClickEventArgs e)
    {
        if (e.ClickedItem is not SessionRow row || _switchInFlight || _streaming || _unreachable || _historyPending)
        {
            return;
        }

        if (row.Id == _chat.StoredSessionId && _sessionReady)
        {
            // P1-SESSION: the session already on screen only closes the panel — P1-D04
            HideSessions();
            return;
        }

        // P1-SESSION: load messages before the socket swap so a missing session leaves the current chat up — P1-D04
        _switchInFlight = true;
        _historyPending = true;
        _sessionReady = false;
        StatusText.Text = "Resuming session…";
        UpdateChrome();
        var resumed = false;
        try
        {
            var turns = await SessionCatalog.MessagesAsync(_backend, row.Id, CancellationToken.None).ConfigureAwait(false);
            await _chat.ResumeStoredAsync(row.Id).ConfigureAwait(false);
            resumed = true;
            Dispatch(() =>
            {
                ClearTranscript();
                foreach (var turn in turns)
                {
                    AddBubble(turn.Role == "user" ? "You" : "Zola", turn.Text, turn.Role == "user");
                }

                _historyPending = false;
                _sessionReady = true;
                _switchInFlight = false;
                StatusText.Text = "Session ready.";
                Composer.PlaceholderText = PlaceholderMessage;
                // P4-REQUEST: re-show open cards after history bubbles (ClearTranscript dropped visuals) — P4-D08 / P4-D11
                _requests.OnSessionChanged(_chat.SessionId);
                UpdateChrome();
                HideSessions();
            });
        }
        catch (Exception ex)
        {
            var message = ex.Message;
            var keepCurrent = !resumed && !string.IsNullOrEmpty(_chat.SessionId);
            Dispatch(() =>
            {
                _historyPending = false;
                _sessionReady = keepCurrent;
                StatusText.Text = message;
            });
        }
        finally
        {
            Dispatch(() =>
            {
                _switchInFlight = false;
                UpdateChrome();
            });
        }
    }

    private void ApplyServerSessions(IReadOnlyList<SessionListItem> listed)
    {
        // P1-SESSION: replace list times from GET /api/sessions and keep an acknowledged id the server has not stored yet — P1-D04
        _serverSessionIds.Clear();
        foreach (var item in listed)
        {
            _serverSessionIds.Add(item.Id);
            _sessionRows[item.Id] = SessionRow.FromServer(item);
        }

        var live = _chat.StoredSessionId;
        foreach (var id in _sessionRows.Keys.ToList())
        {
            if (!_serverSessionIds.Contains(id) && id != live)
            {
                _sessionRows.Remove(id);
            }
        }

        BindSessions();
    }

    private void NoteAcknowledgedSession(string storedId)
    {
        // P1-SESSION: the server-assigned stored id is visible in the list as soon as the RPC returns — P1-D04
        if (string.IsNullOrEmpty(storedId))
        {
            return;
        }

        if (!_sessionRows.ContainsKey(storedId))
        {
            _sessionRows[storedId] = SessionRow.JustAcknowledged(storedId);
        }

        if (_sessionsOpen)
        {
            BindSessions();
        }
    }

    private void BindSessions()
    {
        // P1-SESSION: the open panel shows stored id and last-activity text, newest activity first — P1-D04
        var rows = _sessionRows.Values.OrderByDescending(row => row.SortKey).ToList();
        SessionList.ItemsSource = rows;
        var empty = rows.Count == 0;
        EmptySessionsText.Visibility = empty ? Visibility.Visible : Visibility.Collapsed;
        SessionList.Visibility = empty ? Visibility.Collapsed : Visibility.Visible;
    }

    private void ClearTranscript()
    {
        // P1-SESSION: new and resumed sessions do not keep the previous transcript on screen — P1-D04
        // P4-ASK: session change abandons pending question; spoken-id set kept so re-shows stay silent — P4-D13
        _voice.AbandonPendingQuestion("session_change");
        // P4-FEEDBACK: session switch clears the activity set — P4-D16
        _display.ClearToolActivity();
        Transcript.Children.Clear();
        // P4-REQUEST: card visuals drop with the transcript; broker keeps parked entries — P4-D08
        _requestCards.Clear();
        _requestCloseRecords.Clear();
        // P7-CLARIFY: quiet tracking is visual; re-show reclassifies — P7-D09
        _quietClarifyIds.Clear();
        _noAnswerPanelOpenedIds.Clear();
        _live = null;
        _streaming = false;
        _turnFinalized = true;
        _orphanInterruptedCompletes = 0;
        // P3-LOOK: the error belonged to the old conversation — P3-D18
        _lastTurnErrored = false;
    }

    private void ScrollToEnd()
    {
        TranscriptScroll.UpdateLayout();
        TranscriptScroll.ChangeView(null, TranscriptScroll.ScrollableHeight, null, true);
    }

    private void Dispatch(Action action)
    {
        // P1-CLIENT: socket callbacks arrive off the UI thread — P1-D01
        DispatcherQueue.TryEnqueue(() => action());
    }

    private void OnAnimationsEnabledChanged(UISettings sender, object args)
    {
        Dispatch(() => _presence?.SetReducedMotion(!sender.AnimationsEnabled));
    }

    // P3-SHELL: bubble fills and borders come from tokens, not system theme brushes — P3-D08
    private static void ApplyBubbleChrome(Border border, bool mine, string outcome)
    {
        border.Background = mine ? Token<Brush>(TokenUserBubble) : Token<Brush>(TokenAssistantBubble);
        if (!mine && outcome == "error")
        {
            border.BorderBrush = Token<Brush>(TokenError);
        }
        else if (!mine && outcome == "interrupted")
        {
            border.BorderBrush = Token<Brush>(TokenAmberMuted);
        }
        else if (mine)
        {
            border.BorderBrush = Token<Brush>(TokenAmberMuted);
        }
        else
        {
            border.BorderBrush = Token<Brush>(TokenAmberDark);
        }

        border.BorderThickness = new Thickness(Token<double>(TokenBubbleBorderThickness));
    }

    private void ApplyWindowMetrics()
    {
        // P3-SHELL: 1280x800 start, 900x640 floor — P3-D11
        AppWindow.Resize(new Windows.Graphics.SizeInt32((int)Token<double>(TokenWindowWidth), (int)Token<double>(TokenWindowHeight)));
        if (AppWindow.Presenter is OverlappedPresenter presenter)
        {
            presenter.PreferredMinimumWidth = (int)Token<double>(TokenWindowMinWidth);
            presenter.PreferredMinimumHeight = (int)Token<double>(TokenWindowMinHeight);
        }
    }

    private void OnWindowSizeChanged(object sender, Microsoft.UI.Xaml.WindowSizeChangedEventArgs e)
    {
        SizeConversationOverlay();
        NoticeHost.MaxWidth = e.Size.Width * Token<double>(TokenNoticeMaxFraction);
        UpdateNoticeVisibility();
        UpdateDockVisibility();
    }

    private void OnRootLoaded(object sender, RoutedEventArgs e)
    {
        SizeConversationOverlay();
        NoticeHost.MaxWidth = AppWindow.Size.Width * Token<double>(TokenNoticeMaxFraction);
        StatusText.RegisterPropertyChangedCallback(TextBlock.TextProperty, OnNoticeTextChanged);
        DetailText.RegisterPropertyChangedCallback(TextBlock.TextProperty, OnNoticeTextChanged);
        UpdateDockVisibility();
        UpdateNoticeVisibility();
        _presence?.NoteRootLoaded();
        CompositionTarget.Rendering += OnFirstShellRender;
    }

    private void OnFirstShellRender(object? sender, object e)
    {
        CompositionTarget.Rendering -= OnFirstShellRender;
        if (_presence is null)
        {
            return;
        }

        _presence.NoteRenderOpportunity();
        _ = _presence.LoadAsync();
    }

    private void OnAppWindowChanged(AppWindow sender, AppWindowChangedEventArgs args)
    {
        if (sender.Presenter is not OverlappedPresenter presenter || _presence is null)
        {
            return;
        }

        if (presenter.State == OverlappedPresenterState.Minimized)
        {
            _presence.PauseRendering("minimized");
        }
        else
        {
            _presence.ResumeRendering("minimized");
            UpdateDockVisibility();
        }
    }

    // P4-LOCK: forward lock/sleep to presence pause and the voice gate fact — P4-D01
    private void OnSystemLocked()
    {
        _presence?.PauseRendering(PresenceView.PauseLocked);
        _voice.SetLocked(true);
    }

    private void OnSystemUnlocked()
    {
        _presence?.OnUnlockOrPowerResume(PresenceView.PauseLocked);
        _voice.SetLocked(false);
    }

    private void OnSystemSuspending()
    {
        _presence?.PauseRendering(PresenceView.PauseSuspended);
        _voice.SetSuspended(true);
    }

    private void OnSystemResumed()
    {
        _presence?.OnUnlockOrPowerResume(PresenceView.PauseSuspended);
        _voice.SetSuspended(false);
    }

    private void OnWindowVisibilityChanged(object sender, WindowVisibilityChangedEventArgs args)
    {
        if (_presence is null)
        {
            return;
        }

        if (args.Visible)
        {
            _presence.ResumeRendering("hidden");
        }
        else
        {
            _presence.PauseRendering("hidden");
        }
    }

#if DEBUG
    private void AddPresenceDebugAccelerators()
    {
        // P3-LIFE: F6 writes defaults, F7 reloads life, F8 cycles forced mode — P3-D22
        RootGrid.KeyboardAccelerators.Add(CreatePresenceAccelerator(VirtualKey.F6, OnDebugLifeDefaultsHotkey));
        RootGrid.KeyboardAccelerators.Add(CreatePresenceAccelerator(VirtualKey.F7, OnDebugLifeReloadHotkey));
        RootGrid.KeyboardAccelerators.Add(CreatePresenceAccelerator(VirtualKey.F8, OnDebugForcedModeHotkey));
        RootGrid.KeyboardAccelerators.Add(CreatePresenceAccelerator(VirtualKey.F9, OnDebugBlinkHotkey));
        RootGrid.KeyboardAccelerators.Add(CreatePresenceAccelerator(VirtualKey.F10, OnDebugReloadHotkey));
        RootGrid.KeyboardAccelerators.Add(CreatePresenceAccelerator(VirtualKey.F11, OnDebugMorphHotkey));
        // P3-LOOK: F12 reloads presence-look.json onto the live scene — P3-D13
        RootGrid.KeyboardAccelerators.Add(CreatePresenceAccelerator(VirtualKey.F12, OnDebugLookHotkey));
        // P3-LIFE: F3 force monitor fallback; F4 cycle segment override (pause sim) — P3-D14 / S17
        RootGrid.KeyboardAccelerators.Add(CreatePresenceAccelerator(VirtualKey.F3, OnDebugPlaybackUnavailableHotkey));
        RootGrid.KeyboardAccelerators.Add(CreatePresenceAccelerator(VirtualKey.F4, OnDebugPlaybackSegmentHotkey));
        // P4-REQUEST: F5 injects a synthetic tour decline; F1/F2 preview clarify/approval cards — P4-D06
        RootGrid.KeyboardAccelerators.Add(CreatePresenceAccelerator(VirtualKey.F5, OnDebugTourRequestHotkey));
        RootGrid.KeyboardAccelerators.Add(CreatePresenceAccelerator(VirtualKey.F1, OnDebugClarifyCardHotkey));
        RootGrid.KeyboardAccelerators.Add(CreatePresenceAccelerator(VirtualKey.F2, OnDebugApprovalCardHotkey));
    }

    private static KeyboardAccelerator CreatePresenceAccelerator(VirtualKey key, TypedEventHandler<KeyboardAccelerator, KeyboardAcceleratorInvokedEventArgs> handler)
    {
        var accelerator = new KeyboardAccelerator
        {
            Key = key,
            Modifiers = VirtualKeyModifiers.Control | VirtualKeyModifiers.Shift,
        };
        accelerator.Invoked += handler;
        return accelerator;
    }

    private void OnDebugLifeDefaultsHotkey(KeyboardAccelerator sender, KeyboardAcceleratorInvokedEventArgs args)
    {
        args.Handled = true;
        _presence?.DebugWriteLifeDefaults();
    }

    private void OnDebugLifeReloadHotkey(KeyboardAccelerator sender, KeyboardAcceleratorInvokedEventArgs args)
    {
        args.Handled = true;
        _presence?.DebugReloadLife();
    }

    private void OnDebugForcedModeHotkey(KeyboardAccelerator sender, KeyboardAcceleratorInvokedEventArgs args)
    {
        args.Handled = true;
        _presence?.DebugCycleForcedMode();
    }

    private void OnDebugBlinkHotkey(KeyboardAccelerator sender, KeyboardAcceleratorInvokedEventArgs args)
    {
        args.Handled = true;
        _presence?.DebugBlink();
    }

    private void OnDebugReloadHotkey(KeyboardAccelerator sender, KeyboardAcceleratorInvokedEventArgs args)
    {
        args.Handled = true;
        _presence?.DebugReload();
    }

    private void OnDebugMorphHotkey(KeyboardAccelerator sender, KeyboardAcceleratorInvokedEventArgs args)
    {
        args.Handled = true;
        _presence?.DebugMorphStep();
    }

    private void OnDebugLookHotkey(KeyboardAccelerator sender, KeyboardAcceleratorInvokedEventArgs args)
    {
        args.Handled = true;
        _presence?.DebugReloadLook();
    }

    private bool _debugForceMonitorUnavailable;

    private void OnDebugPlaybackUnavailableHotkey(KeyboardAccelerator sender, KeyboardAcceleratorInvokedEventArgs args)
    {
        args.Handled = true;
        _debugForceMonitorUnavailable = !_debugForceMonitorUnavailable;
        _presence?.DebugForceMonitorUnavailable(_debugForceMonitorUnavailable);
    }

    private int _debugSegmentOverrideCycle;

    private void OnDebugPlaybackSegmentHotkey(KeyboardAccelerator sender, KeyboardAcceleratorInvokedEventArgs args)
    {
        args.Handled = true;
        _debugSegmentOverrideCycle = (_debugSegmentOverrideCycle + 1) % 3;
        bool? value = _debugSegmentOverrideCycle switch
        {
            1 => false,
            2 => true,
            _ => null,
        };
        _presence?.DebugSetSegmentOverride(value);
    }

    private void OnDebugTourRequestHotkey(KeyboardAccelerator sender, KeyboardAcceleratorInvokedEventArgs args)
    {
        if (args is not null)
        {
            args.Handled = true;
        }

        var sessionId = _chat.SessionId ?? "";
        var id = DebugRequestIdPrefix + Guid.NewGuid().ToString("N")[..12];
        var parameters = new Dictionary<string, JsonElement>
        {
            [FieldSessionId] = JsonSerializer.SerializeToElement(sessionId),
        };
        _chat.DebugInjectServerRequest(id, MethodTour, parameters);
    }

    private void OnDebugClarifyCardHotkey(KeyboardAccelerator sender, KeyboardAcceleratorInvokedEventArgs args)
    {
        if (args is not null)
        {
            args.Handled = true;
        }

        var sessionId = _chat.SessionId ?? "";
        if (string.IsNullOrEmpty(sessionId))
        {
            return;
        }

        var id = DebugRequestIdPrefix + Guid.NewGuid().ToString("N")[..12];
        // Alternate single-choice vs batch for UI screenshots.
        _debugClarifyBatch ^= true;
        Dictionary<string, JsonElement> parameters;
        if (_debugClarifyBatch)
        {
            parameters = new Dictionary<string, JsonElement>
            {
                [FieldSessionId] = JsonSerializer.SerializeToElement(sessionId),
                [FieldQuestions] = JsonSerializer.SerializeToElement(new[]
                {
                    new Dictionary<string, object?>
                    {
                        [FieldQid] = "q1",
                        [FieldQuestion] = "Which city?",
                        [FieldChoices] = new[] { "Seattle (Recommended)", "Portland" },
                        [FieldMultiSelect] = false,
                    },
                    new Dictionary<string, object?>
                    {
                        [FieldQid] = "q2",
                        [FieldQuestion] = "Pick themes",
                        [FieldChoices] = new[] { "Quiet", "Bright" },
                        [FieldMultiSelect] = true,
                    },
                }),
            };
        }
        else
        {
            parameters = new Dictionary<string, JsonElement>
            {
                [FieldSessionId] = JsonSerializer.SerializeToElement(sessionId),
                [FieldQuestion] = JsonSerializer.SerializeToElement("Which reply shape do you want?"),
                [FieldChoices] = JsonSerializer.SerializeToElement(new[] { "Short (Recommended)", "Detailed", "Bullet list" }),
                [FieldMultiSelect] = JsonSerializer.SerializeToElement(false),
            };
        }

        _chat.DebugInjectServerRequest(id, MethodClarify, parameters);
    }

    private bool _debugClarifyBatch;
    private bool _debugInjectCardsArmed;
    private bool _debugInjectCardsDone;

    private void OnDebugInjectCardsOnce(object? sender, object e)
    {
        if (_debugInjectCardsDone)
        {
            return;
        }

        if (!_debugInjectCardsArmed)
        {
            var flag = Environment.GetEnvironmentVariable("ZOLA_DEBUG_INJECT_CARDS");
            if (string.IsNullOrEmpty(flag))
            {
                CompositionTarget.Rendering -= OnDebugInjectCardsOnce;
                _debugInjectCardsDone = true;
                return;
            }

            _debugInjectCardsArmed = true;
        }

        if (string.IsNullOrEmpty(_chat.SessionId) || !_sessionReady)
        {
            return;
        }

        _debugInjectCardsDone = true;
        CompositionTarget.Rendering -= OnDebugInjectCardsOnce;
        var mode = (Environment.GetEnvironmentVariable("ZOLA_DEBUG_INJECT_CARDS") ?? "").Trim().ToLowerInvariant();
        DispatcherQueue.TryEnqueue(() =>
        {
            switch (mode)
            {
                case "batch":
                    _debugClarifyBatch = false;
                    OnDebugClarifyCardHotkey(null!, null!);
                    break;
                case "approval":
                    OnDebugApprovalCardHotkey(null!, null!);
                    break;
                case "record":
                    _debugClarifyBatch = true;
                    OnDebugClarifyCardHotkey(null!, null!);
                    var settle = DispatcherQueue.CreateTimer();
                    settle.IsRepeating = false;
                    settle.Interval = TimeSpan.FromMilliseconds(400);
                    settle.Tick += (_, _) =>
                    {
                        settle.Stop();
                        var id = _requests.NewestOpenClarify(_chat.SessionId);
                        if (id is null)
                        {
                            return;
                        }

                        _requestCloseRecords[id] = RecordAnsweredPrefix + "Short";
                        _requests.AnswerClarify(id, "Short");
                    };
                    settle.Start();
                    break;
                default:
                    _debugClarifyBatch = true;
                    OnDebugClarifyCardHotkey(null!, null!);
                    break;
            }
        });
    }

    private void OnDebugApprovalCardHotkey(KeyboardAccelerator sender, KeyboardAcceleratorInvokedEventArgs args)
    {
        if (args is not null)
        {
            args.Handled = true;
        }

        var sessionId = _chat.SessionId ?? "";
        if (string.IsNullOrEmpty(sessionId))
        {
            return;
        }

        var id = DebugRequestIdPrefix + Guid.NewGuid().ToString("N")[..12];
        var parameters = new Dictionary<string, JsonElement>
        {
            [FieldSessionId] = JsonSerializer.SerializeToElement(sessionId),
            [FieldRequestId] = JsonSerializer.SerializeToElement(id),
            [FieldCommand] = JsonSerializer.SerializeToElement(
                "Remove-Item -LiteralPath 'C:\\Users\\test\\AppData\\Local\\Temp\\zola-p4-approval-probe.txt' -Recurse -Force"),
            [FieldDescription] = JsonSerializer.SerializeToElement("PowerShell destructive delete (Remove-Item)"),
            [FieldChoices] = JsonSerializer.SerializeToElement(new[] { "once", "session", "always", "deny" }),
        };
        _chat.DebugInjectServerRequest(id, MethodApproval, parameters);
    }
#endif

    private void SizeConversationOverlay()
    {
        var maxWidth = Token<double>(TokenOverlayMaxWidth);
        var fraction = Token<double>(TokenOverlayMaxFraction);
        ConversationOverlay.Width = Math.Min(maxWidth, AppWindow.Size.Width * fraction);
    }

    private void OnConversationClick(object sender, RoutedEventArgs e)
    {
        // P3-SHELL: conversation and sessions are mutually exclusive — P3-D11
        if (ConversationOverlay.Visibility == Visibility.Visible)
        {
            HideConversation();
            return;
        }

        HideSessions();
        SizeConversationOverlay();
        ConversationOverlay.Visibility = Visibility.Visible;
        UpdateDockVisibility();
        UpdateNoticeVisibility();
        if (Composer.IsEnabled)
        {
            Composer.Focus(FocusState.Programmatic);
        }

        ScrollToEnd();
    }

    private void OnConversationCloseClick(object sender, RoutedEventArgs e)
    {
        HideConversation();
    }

    private void HideConversation()
    {
        _returnFocusToComposer = false;
        CollapseConversationOverlay();
        RootGrid.Focus(FocusState.Programmatic);
    }

    private void CollapseConversationOverlay()
    {
        ConversationOverlay.Visibility = Visibility.Collapsed;
        UpdateDockVisibility();
        UpdateNoticeVisibility();
    }

    private void OnEscapeKey(KeyboardAccelerator sender, KeyboardAcceleratorInvokedEventArgs args)
    {
        if (ConversationOverlay.Visibility == Visibility.Visible)
        {
            args.Handled = true;
            HideConversation();
            return;
        }

        if (_sessionsOpen)
        {
            args.Handled = true;
            HideSessions();
            return;
        }

        // P4-FEEDBACK: Esc → Stop when panels are closed; QuestionSpeaking = no-op + log — P4-FB-STOP
        if (_unreachable)
        {
            return;
        }

        if (_voice.QuestionSpeaking)
        {
            args.Handled = true;
            _ = _voice.StopSpeakingAsync();
            return;
        }

        if (_voice.CanStopSpeaking)
        {
            args.Handled = true;
            OnStopSpeakingClick(StopSpeakingButton, new RoutedEventArgs());
        }
    }

    // P3-SHELL: session line has one writer; it never infers identity from the link — P3-D06
    private void UpdateSessionHud()
    {
        var id = _chat.SessionId;
        SessionText.Text = string.IsNullOrEmpty(id)
            ? SessionHudEmpty
            : SessionHudPrefix + (id.Length <= SessionIdDisplayLength ? id : id[..SessionIdDisplayLength]);
    }

    private void StartClock()
    {
        var now = DateTime.Now;
        var toNextMinute = TimeSpan.FromMinutes(1) - TimeSpan.FromSeconds(now.Second) - TimeSpan.FromMilliseconds(now.Millisecond);
        _clockTimer.Interval = toNextMinute <= TimeSpan.Zero ? TimeSpan.FromMinutes(1) : toNextMinute;
        _clockTimer.Start();
    }

    private void OnClockTick(Microsoft.UI.Dispatching.DispatcherQueueTimer sender, object args)
    {
        UpdateClock();
        _clockTimer.Interval = TimeSpan.FromMinutes(1);
    }

    private void UpdateClock()
    {
        TimeText.Text = DateTime.Now.ToString(TimeFormat);
    }

    private static T Token<T>(string key)
    {
        if (Application.Current.Resources.TryGetValue(key, out var value) && value is T typed)
        {
            return typed;
        }

        throw new InvalidOperationException(key);
    }

    // P3-LOOK: one method decides dock opacity, hit-testing, and the hide delay — P3-D17
    private void UpdateDockVisibility()
    {
        var inReveal = PointerInDockReveal();
        // P4-FEEDBACK: keep the dock visible while Stop is available — P4-FB-STOP
        var wanted = inReveal
            || FocusInsideDock()
            || ConversationOverlay.Visibility == Visibility.Visible
            || _sessionsOpen
            || _streaming
            || _voice.CanStopSpeaking;
        if (wanted)
        {
            _dockHideTimer.Stop();
            SetDockRevealed(true);
            return;
        }

        if (!_dockRevealTarget && DockHost.Opacity <= DockHiddenOpacity && !DockHost.IsHitTestVisible)
        {
            return;
        }

        if (_dockHideTimer.IsRunning)
        {
            return;
        }

        _dockHideTimer.Interval = TimeSpan.FromSeconds(Token<double>(TokenDockHideDelaySeconds));
        _dockHideTimer.Start();
    }

    private void OnDockHideTimerTick(Microsoft.UI.Dispatching.DispatcherQueueTimer sender, object args)
    {
        sender.Stop();
        if (PointerInDockReveal() || FocusInsideDock() || ConversationOverlay.Visibility == Visibility.Visible || _sessionsOpen || _streaming || _voice.CanStopSpeaking)
        {
            return;
        }

        SetDockRevealed(false);
    }

    private void SetDockRevealed(bool show)
    {
        if (_dockRevealTarget == show)
        {
            return;
        }

        _dockRevealTarget = show;
        WriteDockLog(show ? "P3-LOOK: dock shown" : "P3-LOOK: dock hidden");
        if (show)
        {
            DockHost.IsHitTestVisible = true;
        }

        var target = show ? DockShownOpacity : DockHiddenOpacity;
        _dockStoryboard?.Stop();
        if (!_uiSettings.AnimationsEnabled)
        {
            DockHost.Opacity = target;
            if (!show)
            {
                DockHost.IsHitTestVisible = false;
            }

            return;
        }

        var anim = new DoubleAnimation
        {
            To = target,
            Duration = new Duration(TimeSpan.FromMilliseconds(Token<double>(TokenDockFadeMilliseconds))),
            EnableDependentAnimation = true,
        };
        Storyboard.SetTarget(anim, DockHost);
        Storyboard.SetTargetProperty(anim, "Opacity");
        var board = new Storyboard();
        board.Children.Add(anim);
        if (!show)
        {
            board.Completed += (_, _) =>
            {
                if (DockHost.Opacity <= DockHiddenOpacity && !FocusInsideDock() && !PointerInDockReveal())
                {
                    DockHost.IsHitTestVisible = false;
                }
            };
        }

        _dockStoryboard = board;
        board.Begin();
    }

    private bool PointerInDockReveal()
    {
        var point = QueryCursorInRoot() ?? _lastPointerInRoot;
        if (point is null || DockHost.ActualWidth <= 0 || DockHost.ActualHeight <= 0)
        {
            return false;
        }

        var bounds = DockHost.TransformToVisual(RootGrid)
            .TransformBounds(new Rect(0, 0, DockHost.ActualWidth, DockHost.ActualHeight));
        var margin = Token<double>(TokenDockRevealMargin);
        var reveal = new Rect(
            bounds.X - margin,
            bounds.Y - margin,
            bounds.Width + (margin * 2),
            bounds.Height + (margin * 2));
        return reveal.Contains(point.Value);
    }

    private static void WriteDockLog(string line)
    {
        try
        {
            var root = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                VoiceController.TimelineClientFolder,
                VoiceController.TimelineLogFolder);
            Directory.CreateDirectory(root);
            File.AppendAllText(
                Path.Combine(root, "display-state.log"),
                DateTimeOffset.Now.ToString("o") + " " + line + Environment.NewLine);
        }
        catch
        {
        }
    }

    private bool FocusInsideDock()
    {
        if (RootGrid.XamlRoot is null)
        {
            return false;
        }

        var focused = FocusManager.GetFocusedElement(RootGrid.XamlRoot) as DependencyObject;
        while (focused is not null)
        {
            if (ReferenceEquals(focused, DockHost))
            {
                return true;
            }

            focused = VisualTreeHelper.GetParent(focused);
        }

        return false;
    }

    private void OnRootPointerMoved(object sender, PointerRoutedEventArgs e)
    {
        _lastPointerInRoot = e.GetCurrentPoint(RootGrid).Position;
        UpdateDockVisibility();
    }

    private void OnRootPointerExited(object sender, PointerRoutedEventArgs e)
    {
        _lastPointerInRoot = null;
        UpdateDockVisibility();
    }

    private void OnDockGettingFocus(UIElement sender, GettingFocusEventArgs args)
    {
        UpdateDockVisibility();
    }

    private void OnDockLosingFocus(UIElement sender, LosingFocusEventArgs args)
    {
        DispatcherQueue.TryEnqueue(UpdateDockVisibility);
    }

    private void OnWindowActivated(object sender, Microsoft.UI.Xaml.WindowActivatedEventArgs e)
    {
        if (e.WindowActivationState == WindowActivationState.Deactivated)
        {
            return;
        }

        _lastPointerInRoot = QueryCursorInRoot();
        UpdateDockVisibility();
    }

    private Point? QueryCursorInRoot()
    {
        if (!GetCursorPos(out var screen))
        {
            return null;
        }

        var hwnd = WinRT.Interop.WindowNative.GetWindowHandle(this);
        var client = screen;
        if (!ScreenToClient(hwnd, ref client) || RootGrid.XamlRoot is null)
        {
            return null;
        }

        var scale = RootGrid.XamlRoot.RasterizationScale;
        return new Point(client.X / scale, client.Y / scale);
    }

    // P3-LOOK: one method decides notice opacity, DetailText, and overlay placement — P3-D18
    // P4-FEEDBACK: when the panel is open, mirror notices into the panel header — P4-D17
    private void UpdateNoticeVisibility()
    {
        var sticky = _unreachable || _switchInFlight || _historyPending || _lastTurnErrored;
        var text = StatusText.Text ?? "";
        var textChanged = text != _noticeSeenText;
        _noticeSeenText = text;
        var detailVisible = sticky && !string.IsNullOrEmpty(DetailText.Text);
        DetailText.Visibility = detailVisible ? Visibility.Visible : Visibility.Collapsed;
        SyncPanelNoticeMirror(text, detailVisible);
        PlaceNotice();
        if (sticky)
        {
            _noticeHoldTimer.Stop();
            SetNoticeShown(true);
            return;
        }

        if (string.IsNullOrWhiteSpace(text))
        {
            _noticeHoldTimer.Stop();
            SetNoticeShown(false);
            return;
        }

        if (textChanged)
        {
            SetNoticeShown(true);
            _noticeHoldTimer.Interval = TimeSpan.FromSeconds(Token<double>(TokenNoticeHoldSeconds));
            _noticeHoldTimer.Start();
        }
    }

    // P4-FEEDBACK: panel header shows the same status/detail the bottom host would — P4-D17
    private void SyncPanelNoticeMirror(string statusText, bool detailVisible)
    {
        var panelOpen = ConversationOverlay.Visibility == Visibility.Visible;
        var hasStatus = !string.IsNullOrWhiteSpace(statusText);
        PanelNoticeStatus.Text = hasStatus ? statusText : "";
        PanelNoticeDetail.Text = detailVisible ? (DetailText.Text ?? "") : "";
        PanelNoticeDetail.Visibility = detailVisible && panelOpen ? Visibility.Visible : Visibility.Collapsed;
        PanelNoticeHost.Visibility = panelOpen && (hasStatus || detailVisible) ? Visibility.Visible : Visibility.Collapsed;
    }

    private void OnNoticeTextChanged(DependencyObject sender, DependencyProperty dp)
    {
        UpdateNoticeVisibility();
    }

    private void OnNoticeHoldTimerTick(Microsoft.UI.Dispatching.DispatcherQueueTimer sender, object args)
    {
        sender.Stop();
        if (_unreachable || _switchInFlight || _historyPending || _lastTurnErrored)
        {
            return;
        }

        SetNoticeShown(false);
    }

    private void SetNoticeShown(bool show)
    {
        var sticky = _unreachable || _switchInFlight || _historyPending || _lastTurnErrored;
        var panelOpen = ConversationOverlay.Visibility == Visibility.Visible;
        // P4-FEEDBACK: bottom host stays hidden while the panel mirrors notices — P4-D17
        if (panelOpen)
        {
            var hasStatus = !string.IsNullOrWhiteSpace(PanelNoticeStatus.Text);
            var hasDetail = PanelNoticeDetail.Visibility == Visibility.Visible
                && !string.IsNullOrEmpty(PanelNoticeDetail.Text);
            PanelNoticeHost.Visibility = (show || sticky) && (hasStatus || hasDetail)
                ? Visibility.Visible
                : Visibility.Collapsed;
            show = false;
        }

        var target = show ? DockShownOpacity : DockHiddenOpacity;
        _noticeStoryboard?.Stop();
        if (!_uiSettings.AnimationsEnabled)
        {
            NoticeHost.Opacity = target;
            return;
        }

        var anim = new DoubleAnimation
        {
            To = target,
            Duration = new Duration(TimeSpan.FromMilliseconds(Token<double>(TokenDockFadeMilliseconds))),
            EnableDependentAnimation = true,
        };
        Storyboard.SetTarget(anim, NoticeHost);
        Storyboard.SetTargetProperty(anim, "Opacity");
        var board = new Storyboard();
        board.Children.Add(anim);
        _noticeStoryboard = board;
        board.Begin();
    }

    private void PlaceNotice()
    {
        var overlayOpen = ConversationOverlay.Visibility == Visibility.Visible;
        var windowWidth = RootGrid.ActualWidth > 0 ? RootGrid.ActualWidth : AppWindow.Size.Width;
        // P4-FEEDBACK: panel open → notices live in the header; keep bottom host collapsed — P4-D17
        if (overlayOpen)
        {
            NoticeHost.ClearValue(FrameworkElement.WidthProperty);
            NoticeHost.HorizontalAlignment = HorizontalAlignment.Center;
            NoticeHost.Margin = Token<Thickness>(TokenNoticeMargin);
            NoticeHost.MaxWidth = windowWidth * Token<double>(TokenNoticeMaxFraction);
            return;
        }

        NoticeHost.ClearValue(FrameworkElement.WidthProperty);
        NoticeHost.HorizontalAlignment = HorizontalAlignment.Center;
        NoticeHost.Margin = Token<Thickness>(TokenNoticeMargin);
        NoticeHost.MaxWidth = windowWidth * Token<double>(TokenNoticeMaxFraction);
    }

    [DllImport("user32.dll")]
    private static extern bool GetCursorPos(out ScreenPoint point);

    [DllImport("user32.dll")]
    private static extern bool ScreenToClient(IntPtr hwnd, ref ScreenPoint point);

    [StructLayout(LayoutKind.Sequential)]
    private struct ScreenPoint
    {
        public int X;
        public int Y;
    }

    private sealed class LiveResponse
    {
        public LiveResponse(Border border, TextBlock badge, TextBlock activity, TextBlock body)
        {
            Border = border;
            Badge = badge;
            Activity = activity;
            Body = body;
        }

        public Border Border { get; }

        public TextBlock Badge { get; }

        // P4-FEEDBACK: activity line inside the empty live bubble — P4-D16
        public TextBlock Activity { get; }

        public TextBlock Body { get; }
    }
}
