using Zola.Client.Speech;

namespace Zola.Client.Voice;

// P10-READ: the client half of the code path (mechanism B). The tool sends one `code_read` server request with a
// handle. This class redeems the handle on the zola-phone pipe, speaks or shows the value on this computer only,
// and answers that same request with read | shown | failed(+reason) | cancelled. It is pure: the pipe, the voice,
// the screen, and the echo latch are injected, so the lifecycle can be checked without any of them.
//
// The value lives in one local variable inside RunAsync. It is never passed to the answer callback, never logged,
// never put in the conversation, and never stored. A cancel, the client deadline, a connection loss, or a serve
// restart stops playback, clears the screen, ends the latch, and answers `cancelled`.
internal static class CodeReadConstants
{
    public const string Method = "code_read";

    // P10-READ: one named local voice; no fallback voice, because a missing voice shows the code on screen instead
    public const string VoiceName = "Zira";

    // P10-READ: the handle lives 60 s and the tool waits 45 s; the client gives up first, so playback never
    // starts after the deadline and the tool's answer is a real one
    public static readonly TimeSpan ClientDeadline = TimeSpan.FromSeconds(35);

    public const string OutcomeRead = "read";
    public const string OutcomeShown = "shown";
    public const string OutcomeFailed = "failed";
    public const string OutcomeCancelled = "cancelled";

    public const string ReasonBusy = "busy";
    public const string ReasonPlayback = "playback_failed";
    public const string ReasonNoConnection = "no_connection";
    public const string ReasonInternal = "internal";

    // P10-READ: what the echo latch remembers. It is a fixed phrase, never the code.
    public const string LatchPhrase = "reading a verification code";
}

internal readonly record struct CodeRedeemResult(bool Ok, string? Value, string? Reason);

internal enum CodePlayback
{
    Completed,
    Failed,
    Cancelled,
}

internal interface ICodeRedeemer
{
    // Honours the token: after it fires the caller stops waiting and a late value is dropped.
    Task<CodeRedeemResult> RedeemAsync(string sessionId, string handle, CancellationToken ct);
}

internal interface ICodeVoice
{
    // Must not start playback when the token is already cancelled, and must stop it when the token fires.
    Task<CodePlayback> SpeakAsync(string value, CancellationToken ct);

    void Stop();
}

internal interface ICodeDisplay
{
    void Show(string value);

    void Clear();
}

internal interface ICodeLatch
{
    void Begin();

    void End();
}

// P10-READ: the capture latch is the same SpeechEchoGuard idea the proactive voice uses. While it is up the mic
// does not open, so the spoken digits are not transcribed into the conversation.
internal sealed class EchoCodeLatch : ICodeLatch
{
    private readonly SpeechEchoGuard _guard;
    private readonly Func<DateTimeOffset> _now;

    public EchoCodeLatch(SpeechEchoGuard guard, Func<DateTimeOffset>? now = null)
    {
        _guard = guard;
        _now = now ?? (() => DateTimeOffset.UtcNow);
    }

    public void Begin() => _guard.Remember(CodeReadConstants.LatchPhrase, _now());

    public void End() => _guard.NoteCompleted(_now());
}

internal sealed class CodeReader
{
    private readonly ICodeRedeemer _redeemer;
    private readonly ICodeVoice _voice;
    private readonly ICodeDisplay _display;
    private readonly ICodeLatch _latch;
    private readonly Action<string, string, string?> _answer;
    private readonly Action<string> _log;
    private readonly Func<bool> _isVoiceMode;
    private readonly TimeSpan _deadline;
    private readonly object _gate = new();
    private Run? _active;

    public CodeReader(
        ICodeRedeemer redeemer,
        ICodeVoice voice,
        ICodeDisplay display,
        ICodeLatch latch,
        Action<string, string, string?> answer,
        Action<string>? log = null,
        TimeSpan? deadline = null,
        Func<bool>? isVoiceMode = null)
    {
        _redeemer = redeemer;
        _voice = voice;
        _display = display;
        _latch = latch;
        _answer = answer;
        _log = log ?? (_ => { });
        // P10-READ F7: default voice so older checks keep the speak path; the window passes Mode
        _isVoiceMode = isVoiceMode ?? (() => true);
        _deadline = deadline ?? CodeReadConstants.ClientDeadline;
    }

    private sealed class Run
    {
        public required string Id;
        public required CancellationTokenSource Cts;
        public string? CancelReason;
        public int Answered;
    }

    public bool IsActive
    {
        get
        {
            lock (_gate)
            {
                return _active is not null;
            }
        }
    }

    public Task StartAsync(string id, string sessionId, string handle, bool preferShow = false)
    {
        Run? run = null;
        lock (_gate)
        {
            if (_active is null)
            {
                run = new Run { Id = id, Cts = new CancellationTokenSource(_deadline) };
                _active = run;
            }
        }

        if (run is null)
        {
            // one read at a time: a second ask is refused, not queued
            Log(id, CodeReadConstants.OutcomeFailed, CodeReadConstants.ReasonBusy);
            _answer(id, CodeReadConstants.OutcomeFailed, CodeReadConstants.ReasonBusy);
            return Task.CompletedTask;
        }

        var started = run;
        // P10-READ F7: text mode, or a "show me the code" ask, shows on screen and never speaks
        var showOnly = preferShow || !_isVoiceMode();
        return Task.Run(() => RunAsync(started, sessionId, handle, showOnly));
    }

    public void Start(string id, string sessionId, string handle, bool preferShow = false) =>
        _ = StartAsync(id, sessionId, handle, preferShow);

    public void Cancel(string id, string reason)
    {
        Run? run;
        lock (_gate)
        {
            run = _active is { } active && active.Id == id ? active : null;
        }

        CancelRun(run, reason);
    }

    // P10-READ: connection loss, socket replace, session change, serve restart, window close
    public void CancelAll(string reason)
    {
        Run? run;
        lock (_gate)
        {
            run = _active;
        }

        CancelRun(run, reason);
    }

    // The screen's dismiss button
    public void Dismiss() => CancelAll("dismissed");

    private static void CancelRun(Run? run, string reason)
    {
        if (run is null)
        {
            return;
        }

        run.CancelReason ??= reason;
        try
        {
            run.Cts.Cancel();
        }
        catch (ObjectDisposedException)
        {
        }
    }

    private async Task RunAsync(Run run, string sessionId, string handle, bool showOnly)
    {
        var ct = run.Cts.Token;
        var outcome = CodeReadConstants.OutcomeCancelled;
        string? reason = null;
        var displayed = false;
        var latchHeld = false;
        string? value = null;
        // P10-READ F7: show-only never arms the echo latch (no audio to protect)
        if (!showOnly)
        {
            _latch.Begin();
            latchHeld = true;
        }

        try
        {
            CodeRedeemResult redeemed;
            try
            {
                redeemed = await _redeemer.RedeemAsync(sessionId, handle, ct).ConfigureAwait(false);
            }
            catch (OperationCanceledException)
            {
                redeemed = new CodeRedeemResult(false, null, CodeReadConstants.OutcomeCancelled);
            }
            catch (Exception)
            {
                redeemed = new CodeRedeemResult(false, null, CodeReadConstants.ReasonNoConnection);
            }

            if (redeemed.Ok && !string.IsNullOrEmpty(redeemed.Value))
            {
                value = redeemed.Value;
            }

            if (ct.IsCancellationRequested)
            {
                // after the deadline or a cancel the value is dropped and nothing is spoken
                value = null;
            }
            else if (value is null)
            {
                if (redeemed.Reason == CodeReadConstants.OutcomeCancelled)
                {
                    // the tool disarmed first
                }
                else
                {
                    outcome = CodeReadConstants.OutcomeFailed;
                    reason = Sanitize(redeemed.Reason);
                }
            }
            else if (showOnly)
            {
                _display.Show(value);
                displayed = true;
                outcome = CodeReadConstants.OutcomeShown;
            }
            else
            {
                var playback = await SpeakAsync(value, ct).ConfigureAwait(false);
                if (playback == CodePlayback.Completed)
                {
                    outcome = CodeReadConstants.OutcomeRead;
                }
                else if (playback == CodePlayback.Failed && !ct.IsCancellationRequested)
                {
                    // the voice could not play: show it on this screen, outside the conversation, until dismissed
                    // or the deadline
                    _display.Show(value);
                    displayed = true;
                    outcome = CodeReadConstants.OutcomeShown;
                }
                else
                {
                    outcome = CodeReadConstants.OutcomeCancelled;
                }
            }
        }
        catch (Exception)
        {
            outcome = CodeReadConstants.OutcomeFailed;
            reason = CodeReadConstants.ReasonInternal;
        }

        value = null;
        if (outcome == CodeReadConstants.OutcomeCancelled)
        {
            // stop first, so a cancel never leaves a spoken tail behind
            SafeStop();
        }

        Settle(run, outcome, reason);
        if (displayed)
        {
            try
            {
                await Task.Delay(Timeout.Infinite, ct).ConfigureAwait(false);
            }
            catch (OperationCanceledException)
            {
            }
        }

        try
        {
            if (displayed)
            {
                _display.Clear();
            }
        }
        finally
        {
            SafeStop();
            if (latchHeld)
            {
                _latch.End();
            }

            lock (_gate)
            {
                _active = null;
            }

            run.Cts.Dispose();
        }
    }

    private async Task<CodePlayback> SpeakAsync(string value, CancellationToken ct)
    {
        try
        {
            return await _voice.SpeakAsync(value, ct).ConfigureAwait(false);
        }
        catch (OperationCanceledException)
        {
            return CodePlayback.Cancelled;
        }
        catch (Exception)
        {
            return CodePlayback.Failed;
        }
    }

    private void SafeStop()
    {
        try
        {
            _voice.Stop();
        }
        catch (Exception)
        {
        }
    }

    private void Settle(Run run, string outcome, string? reason)
    {
        if (Interlocked.Exchange(ref run.Answered, 1) != 0)
        {
            return;
        }

        Log(run.Id, outcome, reason ?? run.CancelReason);
        try
        {
            _answer(run.Id, outcome, reason);
        }
        catch (Exception)
        {
        }
    }

    // The tool maps a reason to a fixed sentence and ignores anything it does not know, but nothing but a short
    // lower-case token leaves this client.
    private static string Sanitize(string? reason)
    {
        if (string.IsNullOrEmpty(reason) || reason.Length > 32)
        {
            return "failed";
        }

        foreach (var c in reason)
        {
            if (!(c is >= 'a' and <= 'z' || c == '_'))
            {
                return "failed";
            }
        }

        return reason;
    }

    private void Log(string id, string outcome, string? reason)
    {
        // ids, outcomes, and reasons only; there is no value to log
        try
        {
            _log($"code_read id={id} outcome={outcome} reason={reason ?? "-"}");
        }
        catch (Exception)
        {
        }
    }
}
