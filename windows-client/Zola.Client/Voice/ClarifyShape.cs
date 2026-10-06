using System.Text.RegularExpressions;

namespace Zola.Client.Voice;

// P7-CLARIFY: pure quiet-single vs card-required classification — P7-D09

public static class ClarifyShape
{
    public const int SpokenChoicesMaxWords = 20;
    public const string ShapeSingle = "single";
    public const string ShapeCardRequired = "card_required";
    public const string RecommendedMarker = "(Recommended)";

    private static readonly Regex NonWord = new(@"[^a-z0-9\s]+", RegexOptions.CultureInvariant | RegexOptions.Compiled);
    private static readonly Regex Whitespace = new(@"\s+", RegexOptions.CultureInvariant | RegexOptions.Compiled);

    public static string StripRecommended(string choice)
    {
        var trimmed = (choice ?? "").Trim();
        if (trimmed.EndsWith(RecommendedMarker, StringComparison.Ordinal))
        {
            return trimmed[..^RecommendedMarker.Length].TrimEnd();
        }

        return trimmed;
    }

    public static int CountSpokenChoiceWords(IReadOnlyList<string> choices)
    {
        var total = 0;
        if (choices is null)
        {
            return 0;
        }

        foreach (var choice in choices)
        {
            var label = StripRecommended(choice);
            if (label.Length == 0)
            {
                continue;
            }

            total += label.Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries).Length;
        }

        return total;
    }

    // Batch: one non-multi-select question under the spoken-choice word cap.
    // Legacy: !multiSelect and under the same cap. Over-cap or multi/batch → card-required.
    public static bool IsQuietSingle(
        bool isBatch,
        IReadOnlyList<ClarifyQuestionFacts> questions,
        bool legacyMultiSelect,
        IReadOnlyList<string> legacyChoices)
    {
        if (isBatch)
        {
            if (questions is null || questions.Count != 1 || questions[0].MultiSelect)
            {
                return false;
            }

            return CountSpokenChoiceWords(questions[0].Choices) <= SpokenChoicesMaxWords;
        }

        if (legacyMultiSelect)
        {
            return false;
        }

        return CountSpokenChoiceWords(legacyChoices ?? Array.Empty<string>()) <= SpokenChoicesMaxWords;
    }

    public static string ClassifyShape(bool quietSingle) =>
        quietSingle ? ShapeSingle : ShapeCardRequired;

    public static string NormalizeContainment(string text)
    {
        var cleaned = NonWord.Replace((text ?? "").ToLowerInvariant(), " ");
        return Whitespace.Replace(cleaned, " ").Trim();
    }

    public static bool AllLabelsAppearInQuestion(string question, IReadOnlyList<string> labels)
    {
        if (labels is null || labels.Count == 0)
        {
            return false;
        }

        var qWords = NormalizeContainment(question).Split(' ', StringSplitOptions.RemoveEmptyEntries);
        if (qWords.Length == 0)
        {
            return false;
        }

        foreach (var label in labels)
        {
            var labelWords = NormalizeContainment(label).Split(' ', StringSplitOptions.RemoveEmptyEntries);
            if (labelWords.Length == 0 || !ContainsWholeWordSequence(qWords, labelWords))
            {
                return false;
            }
        }

        return true;
    }

    // Label words must appear as consecutive whole words in the question (not substrings).
    public static bool ContainsWholeWordSequence(string[] haystack, string[] needle)
    {
        if (haystack is null || needle is null || needle.Length == 0 || needle.Length > haystack.Length)
        {
            return false;
        }

        for (var i = 0; i <= haystack.Length - needle.Length; i++)
        {
            var match = true;
            for (var j = 0; j < needle.Length; j++)
            {
                if (!string.Equals(haystack[i + j], needle[j], StringComparison.Ordinal))
                {
                    match = false;
                    break;
                }
            }

            if (match)
            {
                return true;
            }
        }

        return false;
    }
}

public readonly struct ClarifyQuestionFacts
{
    public ClarifyQuestionFacts(bool multiSelect, IReadOnlyList<string> choices)
    {
        MultiSelect = multiSelect;
        Choices = choices ?? Array.Empty<string>();
    }

    public bool MultiSelect { get; }
    public IReadOnlyList<string> Choices { get; }
}
