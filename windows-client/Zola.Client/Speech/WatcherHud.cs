namespace Zola.Client.Speech;

public enum WatcherProcessLatch
{
    Running,
    Restarting,
    Stopped,
}

public sealed class WatcherHealthRow
{
    public int NeedsReconnect { get; init; }
    public string? GmailOkAt { get; init; }
    public string? CalendarOkAt { get; init; }
    public string? GmailError { get; init; }
    public string? CalendarError { get; init; }
    public string? ErrorClass { get; init; }
}

public readonly record struct WatcherHudResult(
    string Spoken,
    string HudLine,
    bool? GoogleConnected = null,
    string? RankerState = null,
    string? RankerProgressAt = null,
    bool HealthSeen = false,
    WatcherHealthRow? Health = null)
{
    public string DisplayLine => string.IsNullOrEmpty(HudLine) ? Spoken : HudLine;
}

// P9-SPEAK: spoken state is the health row. The latch can only add a process line — P9-D12
public static class WatcherHud
{
    public static WatcherHudResult Classify(WatcherHealthRow? row, WatcherProcessLatch latch, DateTimeOffset utcNow)
    {
        var spoken = Spoken(row, utcNow);
        var hud = latch switch
        {
            WatcherProcessLatch.Stopped => SpeechConstants.HudWatcherStopped,
            WatcherProcessLatch.Restarting => SpeechConstants.HudWatcherRestarting,
            _ => "",
        };
        return new WatcherHudResult(spoken, hud);
    }

    private static string Spoken(WatcherHealthRow? row, DateTimeOffset utcNow)
    {
        if (row is null)
        {
            return SpeechConstants.SpokenUnknown;
        }

        if (row.NeedsReconnect != 0)
        {
            return SpeechConstants.SpokenNeedsReconnect;
        }

        var gmailAge = AgeSeconds(row.GmailOkAt, utcNow);
        var calendarAge = AgeSeconds(row.CalendarOkAt, utcNow);
        var errored = !string.IsNullOrEmpty(row.ErrorClass)
            || !string.IsNullOrEmpty(row.GmailError)
            || !string.IsNullOrEmpty(row.CalendarError);
        if (errored || gmailAge > SpeechConstants.GmailStaleSeconds || calendarAge > SpeechConstants.CalendarStaleSeconds)
        {
            return SpeechConstants.SpokenDegraded;
        }

        return SpeechConstants.SpokenHealthy;
    }

    private static double AgeSeconds(string? stamp, DateTimeOffset utcNow)
    {
        if (string.IsNullOrEmpty(stamp) || !DateTimeOffset.TryParse(stamp, out var parsed))
        {
            return double.MaxValue;
        }

        return (utcNow - parsed).TotalSeconds;
    }
}
