using Microsoft.UI.Input;
using Microsoft.UI.Windowing;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Input;
using Microsoft.UI.Xaml.Media;
using Windows.Foundation;
using Windows.System;
using Windows.UI.Core;
using Zola.Client.Presence;

namespace Zola.Client;

// P1-CLIENT: one session on /api/ws streams turns, keeps that session for follow-ups, and can cancel — P1-D01
public sealed partial class MainWindow : Window
{
    private readonly HermesProcessManager _backend;
    private readonly ChatSocket _chat;
    private readonly VoiceController _voice;
    private readonly ZolaDisplayStateModel _display;
    private LiveResponse? _live;
    private bool _connectStarted;
    private bool _socketOwnsStatus;
    private bool _sessionReady;
    private bool _streaming;
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
    private readonly Dictionary<string, SessionRow> _sessionRows = new();
    private readonly HashSet<string> _serverSessionIds = new();
    private readonly Microsoft.UI.Dispatching.DispatcherQueueTimer _clockTimer;
    private PresenceView? _presence;
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
    private const string TokenUserBubble = "ZolaUserBubbleBrush";
    private const string TokenAssistantBubble = "ZolaAssistantBubbleBrush";
    private const string TokenAmberMuted = "ZolaAmberMutedBrush";
    private const string TokenAmberDark = "ZolaAmberDarkBrush";
    private const string TokenError = "ZolaErrorBrush";
    private const string TokenBodyStyle = "ZolaBodyStyle";
    private const string TokenBubbleHeadingStyle = "ZolaBubbleHeadingStyle";

    public MainWindow(HermesProcessManager backend)
    {
        // P1-CLIENT: the window subscribes before start so the first ready state can open the socket — P1-D01
        InitializeComponent();
        ApplyWindowMetrics();
        SizeChanged += OnWindowSizeChanged;
        // P3-RENDER: host the viewport in PresenceHost and pause when the window cannot be seen — P3-D02
        _presence = new PresenceView(WinRT.Interop.WindowNative.GetWindowHandle(this));
        PresenceHost.Children.Add(_presence);
        AppWindow.Changed += OnAppWindowChanged;
        VisibilityChanged += OnWindowVisibilityChanged;
#if DEBUG
        AddPresenceDebugAccelerators();
#endif
        _clockTimer = DispatcherQueue.CreateTimer();
        _clockTimer.IsRepeating = true;
        _clockTimer.Tick += OnClockTick;
        _backend = backend;
        _chat = new ChatSocket(backend);
        // P2-VOICE: one voice controller owns this window's socket; the window only renders and forwards input — P2-D12
        _voice = new VoiceController(_chat);
        // P3-STATE: the window renders the display record and does not derive it — P3-D03
        _display = new ZolaDisplayStateModel(_voice, DispatcherQueue);
        _voice.StateChanged += () => Dispatch(ApplyVoiceChrome);
        _voice.TranscriptReady += text => Dispatch(() => _ = SubmitTurnAsync(text));
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
            CompositionTarget.Rendering -= OnFirstShellRender;
            AppWindow.Changed -= OnAppWindowChanged;
            VisibilityChanged -= OnWindowVisibilityChanged;
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
        Composer.PlaceholderText = "Message";
        UpdateChrome();
    }

    private async void OnSendClick(object sender, RoutedEventArgs e)
    {
        var text = Composer.Text.Trim();
        if (!_sessionReady || _streaming || _unreachable || text.Length == 0)
        {
            return;
        }

        // P2-SPEAK: typed Send is the only path that cancels follow-up as a typed submit — P2-D12
        _voice.OnTypedSubmit();
        // P2-VOICE: Send keeps the composer read and clear, then uses the shared submit — P2-D05
        Composer.Text = "";
        // P3-SHELL: typed send returns focus to the composer when the turn ends — P3-D11
        _returnFocusToComposer = true;
        await SubmitTurnAsync(text);
    }

    private async Task SubmitTurnAsync(string text)
    {
        // P2-VOICE: transcripts and typed sends share this prompt.submit; a live turn is not a reason to hold the transcript — P2-D05
        if (!_sessionReady || _unreachable || text.Length == 0)
        {
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
                await _voice.EnterTextModeAsync().ConfigureAwait(false);
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
        // P2-VOICE: a spoken stop ends the exchange with a status line and no turn — P2-D05
        StatusText.Text = "Voice chat ended";
        UpdateChrome();
    }

    private void OnVoiceStatusMessage(string message)
    {
        // P2-VOICE: busy, no speech, and interrupt notices stay on the status line — P2-D08
        StatusText.Text = message;
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
        MicIndicatorText.Text = s.MicLine.ToUpperInvariant();
        ModeButtonLabel.Text = s.ModeWord.ToUpperInvariant();
        MicButtonLabel.Text = s.MicButtonContent.ToUpperInvariant();
        LinkText.Text = s.LinkLabel;
        ModeButton.IsEnabled = s.ModeButtonEnabled;
        MicButton.IsEnabled = s.MicButtonEnabled;
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
        _live.Body.Text += chunk;
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
        var body = new TextBlock { Style = Token<Style>(TokenBodyStyle), TextWrapping = TextWrapping.WrapWholeWords, IsTextSelectionEnabled = true };
        var stack = new StackPanel { Spacing = Token<double>(TokenSpace4) };
        stack.Children.Add(badge);
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
        return new LiveResponse(border, badge, body);
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

    private void UpdateChrome()
    {
        // P1-CLIENT: the composer is usable only with a session, no live turn, and a live backend — P1-D01
        var canType = _sessionReady && !_streaming && !_unreachable && !_switchInFlight && !_historyPending;
        var composerWasEnabled = Composer.IsEnabled;
        Composer.IsEnabled = canType;
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
        // P1-SESSION: the list can open beside a live chat; create and resume wait until the turn is idle — P1-D04
        var backendUp = _backend.WebSocketPermitted && !_unreachable && !_switchInFlight;
        SessionsButton.IsEnabled = backendUp;
        NewSessionButton.IsEnabled = backendUp && !_streaming && !_historyPending;
        // P2-VOICE: composer enablement stays the Phase 1 rule; voice chrome is applied beside it — P2-D07
        ApplyVoiceChrome();
        UpdateSessionHud();
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
                Composer.PlaceholderText = "Message";
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
        Transcript.Children.Clear();
        _live = null;
        _streaming = false;
        _turnFinalized = true;
        _orphanInterruptedCompletes = 0;
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
    }

    private void OnRootLoaded(object sender, RoutedEventArgs e)
    {
        SizeConversationOverlay();
        NoticeHost.MaxWidth = AppWindow.Size.Width * Token<double>(TokenNoticeMaxFraction);
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
        }
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
        RootGrid.KeyboardAccelerators.Add(CreatePresenceAccelerator(VirtualKey.F9, OnDebugBlinkHotkey));
        RootGrid.KeyboardAccelerators.Add(CreatePresenceAccelerator(VirtualKey.F10, OnDebugReloadHotkey));
        RootGrid.KeyboardAccelerators.Add(CreatePresenceAccelerator(VirtualKey.F11, OnDebugMorphHotkey));
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

    private sealed class LiveResponse
    {
        public LiveResponse(Border border, TextBlock badge, TextBlock body)
        {
            Border = border;
            Badge = badge;
            Body = body;
        }

        public Border Border { get; }

        public TextBlock Badge { get; }

        public TextBlock Body { get; }
    }
}
