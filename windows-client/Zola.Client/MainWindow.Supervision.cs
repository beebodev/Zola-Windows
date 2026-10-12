using Zola.Client.Supervision;

namespace Zola.Client;

public sealed partial class MainWindow
{
    private ProcessSupervisor? _supervisor;

    private ProcessSupervisor Supervisor => _supervisor ??= new ProcessSupervisor(
        _backend,
        _chat,
        new WindowGap(this),
        ConnectStoredOrNewAsync,
        () => DispatchAsync(() => ShowSupervisionStatus(keepsFailing: true)));

    internal void BeginBackendRecovery() => Supervisor.BeginAfterFailedStart();

    private async Task<bool> ConnectStoredOrNewAsync()
    {
        try
        {
            if (_voice.TtsBeforeGap is not null)
            {
                // P9-SUPERVISE: keep the snapshot; TTS is set after voice mode is on, not before resume — P9-D02
                _voice.PreserveTtsAcrossNextSync = true;
            }

            _chat.PrepareReconnect();
            var stored = _chat.StoredSessionId;
            if (!string.IsNullOrEmpty(stored))
            {
                // P9-SUPERVISE: resume the stored session; do not open a new conversation — P9-D02
                try
                {
                    await _chat.ResumeStoredAsync(stored).ConfigureAwait(false);
                }
                catch (InvalidOperationException ex) when (ResumeReconnect.IsUnstoredDraft(ex.Message))
                {
                    // P9-SUPERVISE: Hermes writes no db row until the first prompt, so an idle draft cannot be resumed — P9-D02
                    _chat.PrepareReconnect();
                    await _chat.StartAsync().ConfigureAwait(false);
                }
            }
            else
            {
                await _chat.StartAsync().ConfigureAwait(false);
            }

            // P9-SUPERVISE: no session id leaves the outage state and status line untouched — P9-D02
            return !string.IsNullOrEmpty(_chat.SessionId);
        }
        catch (Exception)
        {
            return false;
        }
    }

    private Task DispatchAsync(Action action)
    {
        var done = new TaskCompletionSource(TaskCreationOptions.RunContinuationsAsynchronously);
        if (!DispatcherQueue.TryEnqueue(() =>
            {
                try
                {
                    action();
                    done.TrySetResult();
                }
                catch (Exception ex)
                {
                    done.TrySetException(ex);
                }
            }))
        {
            done.TrySetResult();
        }

        return done.Task;
    }

    private sealed class WindowGap : IOutageGap
    {
        private readonly MainWindow _window;

        public WindowGap(MainWindow window)
        {
            _window = window;
        }

        public void InvalidateCapture() => _window._voice.InvalidateCaptureForOutage();

        public void DropPendingTranscript() => _window._voice.DropPendingTranscriptForOutage();

        public void StopPlayback()
        {
            _window._voice.StopLocalSpeechForOutage();
            _window._presence?.KillOwnedPlayback();
        }

        public void BlockInput() => _window.Dispatch(() => _window.ShowSupervisionStatus(keepsFailing: false));
    }
}
