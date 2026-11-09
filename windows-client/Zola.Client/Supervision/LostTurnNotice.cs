namespace Zola.Client.Supervision;

// S51F-FIX: decide once whether an unreachable gap drops an in-flight turn — S51F-D04
public static class LostTurnNotice
{
    public const string LogUiFinalizedPrefix = "turn_ui_finalized";
    public const string FieldTurn = "turn";
    public const string FieldStatus = "status";
    public const string FieldTime = "time";

    public const string StatusLost = "lost";

    public readonly record struct Decision(
        bool ShowNotice,
        bool FinalizeLiveAsInterrupted,
        string? SkipReason);

    public static bool IsInFlight(
        bool turnFinalized,
        bool streaming,
        bool timingOpen,
        bool awaitingTranscript)
    {
        // S51F-FIX: Transcribing is existing capture-ended/waiting-for-transcript state — S51F-D04
        if (awaitingTranscript)
        {
            return true;
        }

        return !turnFinalized && (streaming || timingOpen);
    }

    public static Decision Decide(
        bool deliberate,
        bool turnFinalized,
        bool streaming,
        bool timingOpen,
        bool awaitingTranscript,
        bool alreadyApplied)
    {
        if (deliberate)
        {
            return new Decision(false, false, "deliberate");
        }

        if (alreadyApplied)
        {
            return new Decision(false, false, "already_applied");
        }

        if (!IsInFlight(turnFinalized, streaming, timingOpen, awaitingTranscript))
        {
            return new Decision(false, false, "not_in_flight");
        }

        // Partial reply bubble exists only when a turn was open for streaming text.
        var finalizeLive = !turnFinalized && (streaming || timingOpen);
        return new Decision(true, finalizeLive, null);
    }

    // S51F-FIX: fields only for SM2 open-turn proof — S51F-D04
    public static string FormatUiFinalized(int turnId, string status, DateTimeOffset time)
    {
        return LogUiFinalizedPrefix
            + " " + FieldTurn + "=" + turnId.ToString(System.Globalization.CultureInfo.InvariantCulture)
            + " " + FieldStatus + "=" + status
            + " " + FieldTime + "=" + time.ToString("o", System.Globalization.CultureInfo.InvariantCulture);
    }
}
