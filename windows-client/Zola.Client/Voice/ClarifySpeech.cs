namespace Zola.Client.Voice;

// P7-CLARIFY: spoken clarify template + echo haystack stem (no UI / I/O) — P7-D09

public static class ClarifySpeech
{
    public const string IsItPrefix = " Is it ";
    public const string OrWord = " or ";
    public const string CommaSep = ", ";
    public const string QuestionMark = "?";

    // TTS text for a quiet single. Free text / already-named labels → question only.
    // 1–4 choices after stripping "(Recommended)". Caller must not invoke when card-required.
    public static string BuildSpokenTemplate(string question, IReadOnlyList<string> choices)
    {
        var q = (question ?? "").Trim();
        if (q.Length == 0)
        {
            return "";
        }

        var labels = SpokenLabels(choices);
        if (labels.Count == 0)
        {
            return q;
        }

        if (ClarifyShape.AllLabelsAppearInQuestion(q, labels))
        {
            return q;
        }

        if (labels.Count == 1)
        {
            return q + IsItPrefix + labels[0] + QuestionMark;
        }

        if (labels.Count == 2)
        {
            return q + IsItPrefix + labels[0] + OrWord + labels[1] + QuestionMark;
        }

        // 3+ (Hermes caps at 4): "{q} Is it {A}, {B}, or {C}?"
        var body = string.Join(CommaSep, labels.Take(labels.Count - 1)) + CommaSep + "or " + labels[^1];
        return q + IsItPrefix + body + QuestionMark;
    }

    // Echo haystack for a quiet single: question stem only (never the spoken choice list).
    public static string EchoHaystackStem(string question) => (question ?? "").Trim();

    public static IReadOnlyList<string> SpokenLabels(IReadOnlyList<string> choices)
    {
        if (choices is null || choices.Count == 0)
        {
            return Array.Empty<string>();
        }

        var labels = new List<string>(choices.Count);
        foreach (var choice in choices)
        {
            var label = ClarifyShape.StripRecommended(choice);
            if (label.Length > 0)
            {
                labels.Add(label);
            }
        }

        return labels;
    }
}
