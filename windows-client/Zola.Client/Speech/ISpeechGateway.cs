namespace Zola.Client.Speech;

// P9-SPEAK: the session talks to this seam. Checks supply a fake; the live client supplies the socket — P9-D11
internal interface ISpeechGateway
{
    Task<SpeechStoreReply> RecoverAsync();

    Task<SpeechSnapshot> SnapshotAsync();

    Task<SpeechClaimResult> ClaimAsync();

    Task<SpeechStoreReply> SpeechStartedAsync(string itemId, string attemptId);

    Task<SpeechStoreReply> OutcomeAsync(string itemId, string attemptId, string outcome);

    Task<SpeechStoreReply> ReleaseAsync(string itemId, string attemptId);

    Task<bool> SpeakAsync(string phrase);

    Task<WatcherHudResult> HealthAsync(WatcherProcessLatch latch, DateTimeOffset utcNow);
}
