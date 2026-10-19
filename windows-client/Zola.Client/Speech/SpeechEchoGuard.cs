namespace Zola.Client.Speech;

// P9-SPEAK: the exact phrase stays in the haystack, and a capture during playback is refused — P9-D11
public sealed class SpeechEchoGuard
{
    private string _phrase = "";
    private DateTimeOffset _rememberedUtc;
    private DateTimeOffset? _completedUtc;
    private bool _queuedOrPlaying;

    public string Haystack => Active(DateTimeOffset.UtcNow) ? _phrase : "";

    public void Remember(string phrase, DateTimeOffset utcNow)
    {
        _phrase = phrase ?? "";
        _rememberedUtc = utcNow;
        _completedUtc = null;
        _queuedOrPlaying = true;
    }

    public void NoteCompleted(DateTimeOffset utcNow)
    {
        _queuedOrPlaying = false;
        _completedUtc = utcNow;
    }

    public void Clear()
    {
        _phrase = "";
        _queuedOrPlaying = false;
        _completedUtc = null;
    }

    public bool Active(DateTimeOffset utcNow)
    {
        if (string.IsNullOrEmpty(_phrase))
        {
            return false;
        }

        if (_queuedOrPlaying)
        {
            return true;
        }

        if (_completedUtc is DateTimeOffset done)
        {
            return utcNow < done.AddSeconds(SpeechConstants.EchoTailSeconds);
        }

        return utcNow < _rememberedUtc.AddSeconds(SpeechConstants.EchoTailSeconds);
    }

    public bool TranscriptMatches(string transcript, DateTimeOffset utcNow)
    {
        if (!Active(utcNow) || string.IsNullOrWhiteSpace(transcript))
        {
            return false;
        }

        return transcript.Contains(_phrase, StringComparison.OrdinalIgnoreCase);
    }

    public bool AllowsCapture(bool pushToTalk, DateTimeOffset captureStartUtc)
    {
        // Push-to-talk cancels the proactive line first, then the capture may proceed.
        if (pushToTalk)
        {
            return true;
        }

        if (string.IsNullOrEmpty(_phrase))
        {
            return true;
        }

        if (_queuedOrPlaying)
        {
            return false;
        }

        if (_completedUtc is DateTimeOffset done
            && captureStartUtc < done.AddSeconds(SpeechConstants.EchoTailSeconds))
        {
            return false;
        }

        return true;
    }
}
