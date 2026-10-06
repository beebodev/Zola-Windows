namespace Zola.Client.Voice;

// P7-CLARIFY: named log formats (lengths/ids/reasons only; never question text) — P7-D09

public static class ClarifyLog
{
    public const string QuietFormat = "clarify quiet id={0} shape={1} choices={2}";
    public const string PanelOpenFormat = "clarify panel_open reason={0} id={1}";

    public const string ReasonClarifyOpen = "clarify_open";
    public const string ReasonCollapse = "collapse";
    public const string ReasonModeText = "mode_text";
    public const string ReasonNoAnswer = "no_answer";
    public const string ReasonReshow = "reshow";
}
