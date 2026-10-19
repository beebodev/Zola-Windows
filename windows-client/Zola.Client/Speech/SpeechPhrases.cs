namespace Zola.Client.Speech;

// P9-SPEAK: the same sets as speech.py. Code picks one and does not repeat the last index — P9-D11
public static class SpeechPhrases
{
    public static readonly string[] GmailNamed =
    {
        "Brian, {name} got back to you.",
        "Heads up, {name} replied.",
        "{name} wrote back, Brian.",
        "You've got a reply from {name}.",
        "Quick one: {name} answered.",
    };

    public static readonly string[] GmailUnnamed =
    {
        "Brian, the reply you were waiting for just came in.",
        "Heads up, you've got the reply you were watching for.",
        "That email you were waiting on, they wrote back.",
    };

    public static readonly string[] CalendarLines =
    {
        "Brian, something you asked me to watch on your calendar just changed.",
        "Heads up, one of the events you asked me to watch was updated.",
    };

    public static string Pick(string? source, string? name, string? nameSource, PhraseCursor cursor)
    {
        var named = !string.IsNullOrEmpty(name) && !string.Equals(nameSource, "someone", StringComparison.Ordinal);
        if (string.Equals(source, "calendar", StringComparison.Ordinal))
        {
            return Take(CalendarLines, ref cursor.Calendar);
        }

        if (!named)
        {
            return Take(GmailUnnamed, ref cursor.GmailUnnamed);
        }

        var line = Take(GmailNamed, ref cursor.GmailNamed);
        return line.Replace("{name}", name, StringComparison.Ordinal);
    }

    private static string Take(string[] lines, ref int last)
    {
        var index = 0;
        if (lines.Length > 1)
        {
            index = (last + 1) % lines.Length;
            if (index == last)
            {
                index = (index + 1) % lines.Length;
            }
        }

        last = index;
        return lines[index];
    }
}

public sealed class PhraseCursor
{
    public int GmailNamed = -1;
    public int GmailUnnamed = -1;
    public int Calendar = -1;
}
