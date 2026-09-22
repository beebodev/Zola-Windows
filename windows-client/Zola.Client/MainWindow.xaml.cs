using Microsoft.UI.Input;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Input;
using Microsoft.UI.Xaml.Media;
using Windows.System;
using Windows.UI;
using Windows.UI.Core;

namespace Zola.Client;

// P1-CLIENT: one session on /api/ws streams turns, keeps that session for follow-ups, and can cancel — P1-D01
public sealed partial class MainWindow : Window
{
    private readonly HermesProcessManager _backend;
    private readonly ChatSocket _chat;
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

    public MainWindow(HermesProcessManager backend)
    {
        // P1-CLIENT: the window subscribes before start so the first ready state can open the socket — P1-D01
        InitializeComponent();
        AppWindow.Resize(new Windows.Graphics.SizeInt32(960, 720));
        _backend = backend;
        _chat = new ChatSocket(backend);
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
        Closed += (_, _) => _chat.Dispose();
        Render();
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
        // P1-CLIENT: store both ids once; later sends reuse them so the agent keeps context — P1-D01
        _sessionReady = true;
        StatusText.Text = "Session ready.";
        _sessionDetail = $"session {sessionId} · stored {storedId}";
        // P1-CLIENT: an error event can arrive before session.create's result; keep it beside the ids — P1-D01
        DetailText.Text = _routedNote is null ? _sessionDetail : _routedNote + Environment.NewLine + _sessionDetail;
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

        // P1-CLIENT: show the user turn locally; prompt.submit's status is not the assistant reply — P1-D01
        Composer.Text = "";
        AddBubble("You", text, mine: true);
        _streaming = true;
        _turnFinalized = false;
        StatusText.Text = "Sending…";
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
                _streaming = false;
                _turnFinalized = true;
                StatusText.Text = ex.Message;
                UpdateChrome();
            });
        }
    }

    private void OnSubmitAcknowledged(string status)
    {
        // P1-CLIENT: streaming, queued, steered, and redirected are acks, not reply text — P1-D01
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
        if (_unreachable)
        {
            return;
        }

        // P1-CLIENT: message.start clears the in-progress response so deltas do not stick to the previous turn — P1-D01
        if (_live is not null && !_turnFinalized)
        {
            _live.Body.Text = "";
            _live.Badge.Visibility = Visibility.Collapsed;
            _live.Border.Background = BubbleBrush(mine: false, outcome: "complete");
        }
        else
        {
            _live = AddLiveBubble();
        }

        _turnFinalized = false;
        _streaming = true;
        StatusText.Text = "Responding…";
        UpdateChrome();
        ScrollToEnd();
    }

    private void OnMessageDelta(string chunk)
    {
        if (_unreachable || _turnFinalized)
        {
            return;
        }

        // P1-CLIENT: each message.delta appends one chunk into the prepared response — P1-D01
        _live ??= AddLiveBubble();
        _live.Body.Text += chunk;
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
        StatusText.Text = outcome == "error" ? "The turn ended with an error." : "Session ready.";
        UpdateChrome();
    }

    private void OnRouted(string note)
    {
        // P1-CLIENT: non-turn frames update the detail line and never the assistant text — P1-D01
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

        _live.Border.Background = BubbleBrush(mine: false, outcome: outcome);
        if (outcome is "error" or "interrupted")
        {
            _live.Badge.Text = outcome == "error" ? "Error" : "Interrupted";
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
        var badge = new TextBlock { FontWeight = Microsoft.UI.Text.FontWeights.SemiBold, Visibility = Visibility.Collapsed };
        var body = new TextBlock { TextWrapping = TextWrapping.WrapWholeWords, IsTextSelectionEnabled = true };
        var stack = new StackPanel { Spacing = 4 };
        stack.Children.Add(badge);
        stack.Children.Add(body);
        var border = new Border
        {
            Child = stack,
            Padding = new Thickness(12),
            CornerRadius = new CornerRadius(8),
            HorizontalAlignment = HorizontalAlignment.Left,
            MaxWidth = 720,
            Background = BubbleBrush(mine: false, outcome: "complete"),
        };
        Transcript.Children.Add(border);
        return new LiveResponse(border, badge, body);
    }

    private void AddBubble(string title, string text, bool mine)
    {
        // P1-CLIENT: the user's own send is local; it is not a socket frame — P1-D01
        var heading = new TextBlock { Text = title, FontWeight = Microsoft.UI.Text.FontWeights.SemiBold };
        var body = new TextBlock { Text = text, TextWrapping = TextWrapping.WrapWholeWords, IsTextSelectionEnabled = true };
        var stack = new StackPanel { Spacing = 4 };
        stack.Children.Add(heading);
        stack.Children.Add(body);
        Transcript.Children.Add(new Border
        {
            Child = stack,
            Padding = new Thickness(12),
            CornerRadius = new CornerRadius(8),
            HorizontalAlignment = mine ? HorizontalAlignment.Right : HorizontalAlignment.Left,
            MaxWidth = 720,
            Background = BubbleBrush(mine, outcome: "complete"),
        });
        ScrollToEnd();
    }

    private void UpdateChrome()
    {
        // P1-CLIENT: the composer is usable only with a session, no live turn, and a live backend — P1-D01
        var canType = _sessionReady && !_streaming && !_unreachable;
        Composer.IsEnabled = canType;
        SendButton.IsEnabled = canType && Composer.Text.Trim().Length > 0;
        CancelButton.IsEnabled = _streaming && !_unreachable;
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

    private static Brush BubbleBrush(bool mine, string outcome)
    {
        // P1-CLIENT: error and interrupted turns use different fills from a clean complete — P1-D01
        if (!mine && outcome == "error")
        {
            return BrushOr("SystemFillColorCriticalBackgroundBrush", Color.FromArgb(255, 255, 214, 214));
        }

        if (!mine && outcome == "interrupted")
        {
            return BrushOr("SystemFillColorCautionBackgroundBrush", Color.FromArgb(255, 255, 236, 204));
        }

        if (mine)
        {
            return BrushOr("AccentFillColorDefaultBrush", Color.FromArgb(255, 214, 228, 255));
        }

        return BrushOr("CardBackgroundFillColorDefaultBrush", Color.FromArgb(255, 244, 244, 244));
    }

    private static Brush BrushOr(string key, Color fallback)
    {
        if (Application.Current.Resources.TryGetValue(key, out var value) && value is Brush brush)
        {
            return brush;
        }

        return new SolidColorBrush(fallback);
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
