using System.Text;
using System.Text.RegularExpressions;

namespace Zola.Client.Voice;

// P7-LATENCY: pure per-turn timing record + Hermes sentence boundary — P7-D10

/// <summary>
/// Observes one client turn's timestamps. No I/O, no UI; callers pass <see cref="DateTimeOffset"/>.
/// Never consulted by turn / voice / capture decisions.
/// </summary>
public sealed class TurnTiming
{
    /// <summary>Mirrors <c>SentenceChunker(min_len=20)</c> in hermes-agent <c>tools/tts_streaming.py:72</c>.</summary>
    public const int MinSentenceLen = 20;

    /// <summary>Bounded wait after <c>message.complete</c> for first audio before writing the line.</summary>
    public const int FinalizeSeconds = 15;

    public const string KindVoice = "voice";
    public const string KindTyped = "typed";

    public const string LogPrefix = "turn_timing";
    public const string FieldTurn = "turn";
    public const string FieldKind = "kind";
    public const string FieldTranscriptToSubmitMs = "transcript_to_submit_ms";
    public const string FieldSubmitToFirstDeltaMs = "submit_to_first_delta_ms";
    public const string FieldFirstDeltaToFirstSentenceMs = "first_delta_to_first_sentence_ms";
    public const string FieldSubmitToFirstSentenceMs = "submit_to_first_sentence_ms";
    public const string FieldSubmitToCompleteMs = "submit_to_complete_ms";
    public const string FieldFirstSentenceToFirstAudioMs = "first_sentence_to_first_audio_ms";
    public const string FieldSubmitToFirstAudioMs = "submit_to_first_audio_ms";
    public const string FieldTools = "tools";
    public const string FieldApproval = "approval";
    public const string LogErrorPrefix = "turn_timing error=";

    // P7-LATENCY: same pattern as hermes-agent tools/tts_streaming.py:63 — P7-D10
    private static readonly Regex SentenceBoundary = new(
        @"(?<=[.!?])(?:\s|\n)|(?:\n\n)",
        RegexOptions.CultureInvariant | RegexOptions.Compiled);

    // P7-LATENCY: same strip as tts_streaming.py:65 — P7-D10
    private static readonly Regex ThinkBlock = new(
        @"<think[\s>].*?</think>",
        RegexOptions.CultureInvariant | RegexOptions.Compiled | RegexOptions.Singleline);

    private int _turn;
    private string _kind = "";
    private DateTimeOffset _submitAt;
    private DateTimeOffset? _transcriptAt;
    private DateTimeOffset? _firstDeltaAt;
    private DateTimeOffset? _firstSentenceAt;
    private DateTimeOffset? _completeAt;
    private DateTimeOffset? _firstAudioAt;
    private int _tools;
    private int _approval;
    private readonly StringBuilder _accumulated = new();
    private bool _written;

    public bool IsOpen => _submitAt != default && !_written;

    public bool HasComplete => _completeAt.HasValue;

    public bool HasFirstAudio => _firstAudioAt.HasValue;

    public int TurnNumber => _turn;

    /// <summary>
    /// True when accumulated reply text contains a first speakable sentence under Hermes's rule
    /// (<see cref="MinSentenceLen"/> + <see cref="SentenceBoundary"/>).
    /// </summary>
    public static bool HasCompleteFirstSentence(string accumulated, int minLen = MinSentenceLen)
    {
        return TryFindFirstSentenceEnd(accumulated, minLen, out _);
    }

    /// <summary>
    /// Returns the end index (exclusive) of the first sentence Hermes would emit, or false.
    /// </summary>
    public static bool TryFindFirstSentenceEnd(string accumulated, int minLen, out int endExclusive)
    {
        endExclusive = 0;
        if (string.IsNullOrEmpty(accumulated))
        {
            return false;
        }

        var buf = ThinkBlock.Replace(accumulated, "");
        if (buf.Contains("<think", StringComparison.Ordinal) && !buf.Contains("</think>", StringComparison.Ordinal))
        {
            return false;
        }

        var start = 0;
        while (true)
        {
            var m = SentenceBoundary.Match(buf, start);
            if (!m.Success)
            {
                return false;
            }

            var end = m.Index + m.Length;
            var head = buf.Substring(0, end);
            if (head.Trim().Length < minLen)
            {
                start = end;
                continue;
            }

            endExclusive = end;
            return true;
        }
    }

    public void Begin(int turn, string kind, DateTimeOffset submitAt, DateTimeOffset? transcriptAt)
    {
        _turn = turn;
        _kind = kind ?? "";
        _submitAt = submitAt;
        _transcriptAt = transcriptAt;
        _firstDeltaAt = null;
        _firstSentenceAt = null;
        _completeAt = null;
        _firstAudioAt = null;
        _tools = 0;
        _approval = 0;
        _accumulated.Clear();
        _written = false;
    }

    public void NoteDelta(string? chunk, DateTimeOffset now)
    {
        if (!IsOpen || string.IsNullOrEmpty(chunk))
        {
            return;
        }

        _firstDeltaAt ??= now;
        _accumulated.Append(chunk);
        if (_firstSentenceAt is null
            && TryFindFirstSentenceEnd(_accumulated.ToString(), MinSentenceLen, out _))
        {
            _firstSentenceAt = now;
        }
    }

    public void NoteComplete(DateTimeOffset now)
    {
        if (!IsOpen)
        {
            return;
        }

        _completeAt ??= now;
    }

    public void NoteFirstAudio(DateTimeOffset now)
    {
        if (!IsOpen)
        {
            return;
        }

        _firstAudioAt ??= now;
    }

    public void NoteToolStart()
    {
        if (!IsOpen)
        {
            return;
        }

        _tools++;
    }

    public void NoteApproval()
    {
        if (!IsOpen)
        {
            return;
        }

        _approval = 1;
    }

    /// <summary>
    /// Ready to write when complete and first audio both seen, or complete and
    /// <paramref name="now"/> is at least <see cref="FinalizeSeconds"/> after complete (no audio),
    /// or forced.
    /// </summary>
    public bool ShouldFinalize(DateTimeOffset now, bool force = false)
    {
        if (!IsOpen || _written)
        {
            return false;
        }

        if (force)
        {
            return true;
        }

        if (_completeAt is { } complete && _firstAudioAt.HasValue)
        {
            return true;
        }

        if (_completeAt is { } c && (now - c).TotalSeconds >= FinalizeSeconds)
        {
            return true;
        }

        return false;
    }

    public bool TryFormatLine(out string line)
    {
        line = "";
        if (_submitAt == default || _written)
        {
            return false;
        }

        line = FormatLine(
            _turn,
            _kind,
            Ms(_transcriptAt, _submitAt),
            Ms(_submitAt, _firstDeltaAt),
            Ms(_firstDeltaAt, _firstSentenceAt),
            Ms(_submitAt, _firstSentenceAt),
            Ms(_submitAt, _completeAt),
            Ms(_firstSentenceAt, _firstAudioAt),
            Ms(_submitAt, _firstAudioAt),
            _tools,
            _approval);
        return true;
    }

    public string? Finalize(DateTimeOffset now, bool force = false)
    {
        if (!ShouldFinalize(now, force))
        {
            return null;
        }

        if (!TryFormatLine(out var line))
        {
            return null;
        }

        _written = true;
        return line;
    }

    public static string FormatLine(
        int turn,
        string kind,
        string transcriptToSubmitMs,
        string submitToFirstDeltaMs,
        string firstDeltaToFirstSentenceMs,
        string submitToFirstSentenceMs,
        string submitToCompleteMs,
        string firstSentenceToFirstAudioMs,
        string submitToFirstAudioMs,
        int tools,
        int approval)
    {
        return string.Concat(
            LogPrefix,
            " ", FieldTurn, "=", turn.ToString(),
            " ", FieldKind, "=", kind,
            " ", FieldTranscriptToSubmitMs, "=", transcriptToSubmitMs,
            " ", FieldSubmitToFirstDeltaMs, "=", submitToFirstDeltaMs,
            " ", FieldFirstDeltaToFirstSentenceMs, "=", firstDeltaToFirstSentenceMs,
            " ", FieldSubmitToFirstSentenceMs, "=", submitToFirstSentenceMs,
            " ", FieldSubmitToCompleteMs, "=", submitToCompleteMs,
            " ", FieldFirstSentenceToFirstAudioMs, "=", firstSentenceToFirstAudioMs,
            " ", FieldSubmitToFirstAudioMs, "=", submitToFirstAudioMs,
            " ", FieldTools, "=", tools.ToString(),
            " ", FieldApproval, "=", approval.ToString());
    }

    private static string Ms(DateTimeOffset? from, DateTimeOffset? to)
    {
        if (from is null || to is null)
        {
            return "";
        }

        var ms = (long)Math.Round((to.Value - from.Value).TotalMilliseconds);
        if (ms < 0)
        {
            ms = 0;
        }

        return ms.ToString();
    }
}
