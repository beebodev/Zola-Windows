using System.Security.Cryptography;
using System.Text;

namespace Zola.Client.Speech;

// P9-SPEAK: log a deny only when the reason changes, and one line on the return to idle — P9-D11
public sealed class SpeechDenyLog
{
    private readonly List<string> _lines = new();
    private string? _lastKey;

    public IReadOnlyList<string> Lines => _lines;

    public string? Note(string outcome, string reason, string? attemptId = null, int phraseIndex = -1, string? nameSource = null)
    {
        var shown = outcome;
        var shownReason = string.IsNullOrEmpty(reason) ? "-" : reason;
        if (outcome == SpeechConstants.OutcomeDeny && shownReason == SpeechConstants.ReasonNothingSpeakable)
        {
            shown = SpeechConstants.OutcomeIdle;
        }

        if (shown is SpeechConstants.OutcomeDeny or SpeechConstants.OutcomeIdle or "error")
        {
            var key = shown + "\n" + shownReason;
            if (key == _lastKey)
            {
                return null;
            }

            _lastKey = key;
        }
        else
        {
            _lastKey = null;
        }

        var line = "proactive.deliver"
            + " attempt=" + Hash(attemptId)
            + " outcome=" + shown
            + " reason=" + shownReason
            + " phrase=" + (phraseIndex < 0 ? "-" : phraseIndex.ToString())
            + " name_source=" + (string.IsNullOrEmpty(nameSource) ? "-" : nameSource);
        _lines.Add(line);
        return line;
    }

    public string? NoteReturnToIdle(string reason)
    {
        if (_lastKey is null)
        {
            return null;
        }

        return Note(SpeechConstants.OutcomeIdle, reason);
    }

    public static string Hash(string? attemptId)
    {
        if (string.IsNullOrEmpty(attemptId))
        {
            return "-";
        }

        var bytes = SHA256.HashData(Encoding.UTF8.GetBytes(attemptId));
        var hex = Convert.ToHexString(bytes);
        return hex[..16].ToLowerInvariant();
    }
}
