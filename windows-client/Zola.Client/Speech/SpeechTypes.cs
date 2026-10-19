namespace Zola.Client.Speech;

public enum SpeechStep
{
    Stop,
    Snapshot,
    Claim,
    Speak,
    SpeechStarted,
    Release,
    Outcome,
}

public sealed class SpeechFacts
{
    public DateTimeOffset UtcNow { get; set; }
    public DateTimeOffset LocalNow { get; set; }
    public bool Locked { get; set; }
    public bool Suspended { get; set; }
    public bool TextMode { get; set; }
    public bool Capture { get; set; }
    public bool Turn { get; set; }
    public bool Playback { get; set; }
    public bool Clarify { get; set; }
    public bool BackendUp { get; set; } = true;
    public bool MonitorAvailable { get; set; } = true;
    public DateTimeOffset? LastComposerInputUtc { get; set; }
    public DateTimeOffset? LastWakeUtc { get; set; }
    public DateTimeOffset? LastPushToTalkUtc { get; set; }
    public DateTimeOffset? LastSubmitUtc { get; set; }
    public DateTimeOffset? LastTurnUtc { get; set; }
    public DateTimeOffset? LastBoutStoppedUtc { get; set; }
}

public readonly record struct SpeechSnapshot(
    bool Ok,
    string? Reason,
    bool TurnInFlight,
    bool ReviewedDraft,
    DateTimeOffset? ServerTime);

public readonly record struct SpeechClaimResult(
    bool Ok,
    string? Reason,
    string? ItemId,
    string? AttemptId,
    string? Name,
    string? NameSource,
    string? Source);

public readonly record struct SpeechStoreReply(bool Ok, string? Reason)
{
    public bool Terminal => SpeechConstants.IsTerminalStoreReason(Reason);
}

public sealed class SpeechAction
{
    public SpeechStep Step { get; init; } = SpeechStep.Stop;
    public string Reason { get; init; } = "";
    public string? ItemId { get; init; }
    public string? AttemptId { get; init; }
    public string? Phrase { get; init; }
    public int PhraseIndex { get; init; } = -1;
    public string? NameSource { get; init; }
    public string? StoreOutcome { get; init; }
    public string? LogLine { get; init; }
    public bool StopPlayback { get; init; }
}
