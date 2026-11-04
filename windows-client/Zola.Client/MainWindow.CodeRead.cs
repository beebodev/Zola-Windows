using Microsoft.UI.Xaml;
using Zola.Client.Speech;
using Zola.Client.Voice;

namespace Zola.Client;

// P10-READ: the window's half of the code reader. The window starts a read when the broker hands it a handle, and
// stops it on every loss: server cancel, socket replace, session change, connection loss, serve exit, a
// push-to-talk or stop, and window close. The value is spoken here or shown in CodeShownHost. It is never an
// AddBubble line, a notice, a status string, or a log field.
public sealed partial class MainWindow
{
    private const string CodeLogFile = "code-read.log";
    private CodeReader? _codeReader;
    private readonly object _codeLogGate = new();

    private void InitializeCodeRead()
    {
        var echo = new SpeechEchoGuard();
        _voice.CodeEcho = echo;
        _codeReader = new CodeReader(
            _phone?.CodeRedeemer ?? new PhoneCodeRedeemer(() => ""),
            new LocalCodeVoice(),
            new WindowCodeDisplay(this),
            new EchoCodeLatch(echo),
            (id, outcome, reason) => _requests.AnswerCodeRead(id, outcome, reason),
            WriteCodeLog,
            isVoiceMode: () => _voice.Mode == VoiceController.ModeVoice);
        // P10-READ F7: preferShow comes from the tool when Brian said "show me the code"
        _requests.CodeReadRequested += (id, sessionId, handle, preferShow) =>
            _codeReader.Start(id, sessionId, handle, preferShow);
        _requests.CodeReadWithdrawn += (id, reason) => _codeReader.Cancel(id, reason);
        // P10-READ: loss of the connection with no cancel message still stops playback
        _chat.ConnectionLost += _ => _codeReader.CancelAll("connection_lost");
        _backend.UnexpectedExit += _ => _codeReader.CancelAll("serve_restart");
        _voice.SpeechStamp += stamp =>
        {
            if (stamp == SpeechConstants.StampPushToTalk || stamp == SpeechConstants.StampStop)
            {
                _codeReader.CancelAll("stamp_" + stamp);
            }
        };
        Closed += (_, _) =>
        {
            _codeReader.CancelAll("window_closed");
            ClearCodeShown();
        };
    }

    private void ShowCodeShown(string value)
    {
        CodeShownText.Text = value;
        CodeShownHost.Visibility = Visibility.Visible;
    }

    private void ClearCodeShown()
    {
        CodeShownText.Text = "";
        CodeShownHost.Visibility = Visibility.Collapsed;
    }

    private void OnCodeShownDismiss(object sender, RoutedEventArgs e)
    {
        ClearCodeShown();
        _codeReader?.Dismiss();
    }

    private void WriteCodeLog(string line)
    {
        try
        {
            var root = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "ZolaClient", "logs");
            Directory.CreateDirectory(root);
            lock (_codeLogGate)
            {
                File.AppendAllText(Path.Combine(root, CodeLogFile), $"{DateTimeOffset.Now:o} {line}{Environment.NewLine}");
            }
        }
        catch (Exception)
        {
        }
    }

    // The only place the value touches the UI: one TextBlock outside the conversation, cleared on dismiss, deadline,
    // cancel, or close.
    private sealed class WindowCodeDisplay : ICodeDisplay
    {
        private readonly MainWindow _window;

        public WindowCodeDisplay(MainWindow window)
        {
            _window = window;
        }

        public void Show(string value) => _window.Dispatch(() => _window.ShowCodeShown(value));

        public void Clear() => _window.Dispatch(_window.ClearCodeShown);
    }
}
