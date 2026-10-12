namespace Zola.Client.Supervision;

// P9-SUPERVISE: an unstored draft is not a failed reconnect; every other resume error is — P9-D02
public static class ResumeReconnect
{
    public static bool IsUnstoredDraft(string? message)
        => message != null && message.Contains("session not found", StringComparison.Ordinal);

    public static bool CountsAsFailedReconnect(string? message)
        => !IsUnstoredDraft(message);
}
