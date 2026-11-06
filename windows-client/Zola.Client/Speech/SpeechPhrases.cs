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

    // P10-WATCH: the same sets as speech.py — P10-D15 / verdict 5
    public static readonly string[] TextNamed =
    {
        "Brian, quick one: {name} texted you.",
        "Heads up, {name} just texted.",
        "Quick one: you've got a text from {name}.",
        "Brian, {name} texted you.",
        "Brian, quick one: {name} just sent you a text.",
    };

    public static readonly string[] TextUnnamed =
    {
        "Brian, someone you asked me to watch for just texted.",
        "Heads up, someone you're watching for just texted.",
        "Quick one: a text from someone you asked me to watch for.",
    };

    public static readonly string[] TextNumber =
    {
        "Brian, that number you asked me to watch just texted.",
        "Heads up, that number you asked me to watch just texted.",
        "Quick one: a text from the number you're watching.",
    };

    public static readonly string[] TextGroup =
    {
        "Brian, quick one: {name} texted in a group thread.",
        "Heads up, {name} just texted in a group thread.",
        "Quick one: a group text from {name}.",
        "Brian, {name} texted in a group thread.",
    };

    public static readonly string[] EmailPerson =
    {
        "Brian, quick one: {name} emailed you.",
        "Heads up, {name} just emailed.",
        "Quick one: you've got an email from {name}.",
        "Brian, {name} emailed you.",
    };

    public static string Pick(string? source, string? name, string? nameSource, PhraseCursor cursor, string? lineKind = null)
    {
        if (!string.IsNullOrEmpty(lineKind))
        {
            var chosen = LinesFor(lineKind);
            if (chosen is not null)
            {
                var taken = Take(chosen, ref IndexSlot(cursor, lineKind));
                return taken.Replace("{name}", name ?? "", StringComparison.Ordinal);
            }
        }

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

    private static string[]? LinesFor(string lineKind)
    {
        if (string.Equals(lineKind, "text_named", StringComparison.Ordinal)) return TextNamed;
        if (string.Equals(lineKind, "text_unnamed", StringComparison.Ordinal)) return TextUnnamed;
        if (string.Equals(lineKind, "text_number", StringComparison.Ordinal)) return TextNumber;
        if (string.Equals(lineKind, "text_group", StringComparison.Ordinal)) return TextGroup;
        if (string.Equals(lineKind, "email_person", StringComparison.Ordinal)) return EmailPerson;
        return null;
    }

    private static ref int IndexSlot(PhraseCursor cursor, string lineKind)
    {
        if (string.Equals(lineKind, "text_named", StringComparison.Ordinal)) return ref cursor.TextNamed;
        if (string.Equals(lineKind, "text_unnamed", StringComparison.Ordinal)) return ref cursor.TextUnnamed;
        if (string.Equals(lineKind, "text_number", StringComparison.Ordinal)) return ref cursor.TextNumber;
        if (string.Equals(lineKind, "text_group", StringComparison.Ordinal)) return ref cursor.TextGroup;
        return ref cursor.EmailPerson;
    }
}

public sealed class PhraseCursor
{
    public int GmailNamed = -1;
    public int GmailUnnamed = -1;
    public int Calendar = -1;
    public int TextNamed = -1;
    public int TextUnnamed = -1;
    public int TextNumber = -1;
    public int TextGroup = -1;
    public int EmailPerson = -1;
}
