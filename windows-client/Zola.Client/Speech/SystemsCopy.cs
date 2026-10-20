namespace Zola.Client.Speech;

// P9-SPEAK: row labels, state words, and the (row, state) colour live here — P9-D12
public static class SystemsCopy
{
    public const string Header = "SYSTEMS";
    public const string Backend = "BACKEND";
    public const string WorkspaceWatcher = "WORKSPACE WATCHER";
    public const string GoogleAccount = "GOOGLE ACCOUNT";
    public const string Ranking = "RANKING";
    public const string Voice = "VOICE";
    public const string Companion = "COMPANION WATCHER";
    public const string PairPhone = "PAIR PHONE";
    public const string RepairPhone = "RE-PAIR PHONE";
    public const string NotPaired = "NOT PAIRED";
    public const string NotResponding = "NOT RESPONDING";
    public const string Reconnecting = "RECONNECTING";
    public const string NoTailnet = "NO TAILNET";

    public const string Restarting = "RESTARTING";
    public const string Failing = "FAILING";
    public const string Offline = "OFFLINE";
    public const string Stopped = "STOPPED";
    public const string Degraded = "DEGRADED";
    public const string Unknown = "UNKNOWN";
    public const string Reconnect = "RECONNECT";
    public const string BackingOff = "BACKING OFF";
    public const string Unavailable = "UNAVAILABLE";
    public const string Auth = "AUTH";
    public const string Failed = "FAILED";
    public const string Stale = "STALE";
    public const string Outage = "OUTAGE";

    public const double PanelWidth = 340;
    public const int RankerStaleSeconds = 600;

    public enum Row
    {
        Backend,
        WorkspaceWatcher,
        GoogleAccount,
        Ranking,
        Voice,
        Companion,
    }

    public enum Level
    {
        Quiet,
        Attention,
        Down,
    }

    public readonly record struct View(Row Row, string Label, string? State, Level Level, bool Visible);

    private static readonly Dictionary<(Row Row, string State), Level> Levels = new()
    {
        { (Row.Backend, Restarting), Level.Attention },
        { (Row.Backend, Failing), Level.Down },
        { (Row.Backend, Offline), Level.Down },
        { (Row.WorkspaceWatcher, Restarting), Level.Attention },
        { (Row.WorkspaceWatcher, Stopped), Level.Down },
        { (Row.WorkspaceWatcher, Degraded), Level.Attention },
        { (Row.WorkspaceWatcher, Unknown), Level.Attention },
        { (Row.GoogleAccount, Reconnect), Level.Down },
        { (Row.Ranking, BackingOff), Level.Attention },
        { (Row.Ranking, Unavailable), Level.Attention },
        { (Row.Ranking, Auth), Level.Down },
        { (Row.Ranking, Failed), Level.Down },
        { (Row.Ranking, Stale), Level.Attention },
        { (Row.Voice, Unavailable), Level.Down },
        { (Row.Voice, Outage), Level.Down },
        { (Row.Companion, Restarting), Level.Attention },
        { (Row.Companion, Failing), Level.Down },
        { (Row.Companion, Stopped), Level.Down },
        { (Row.Companion, NotPaired), Level.Attention },
        { (Row.Companion, NotResponding), Level.Attention },
        { (Row.Companion, Reconnecting), Level.Attention },
        { (Row.Companion, Offline), Level.Down },
        { (Row.Companion, NoTailnet), Level.Attention },
    };

    public static Level LevelFor(Row row, string state)
    {
        return Levels.TryGetValue((row, state), out var level) ? level : Level.Quiet;
    }

    public static View[] Rows(SystemsFacts facts)
    {
        return
        [
            BackendRow(facts),
            WatcherRow(facts),
            GoogleRow(facts),
            RankerRow(facts),
            VoiceRow(facts),
            CompanionRow(facts),
        ];
    }

    private static View BackendRow(SystemsFacts facts)
    {
        string? state = facts.BackendKeepsFailing ? Failing
            : facts.BackendRestarting ? Restarting
            : facts.BackendUp ? null
            : Offline;
        return ViewOf(Row.Backend, Backend, state, visible: true);
    }

    private static View WatcherRow(SystemsFacts facts)
    {
        if (!facts.HealthSeen && facts.Latch == WatcherProcessLatch.Running)
        {
            return ViewOf(Row.WorkspaceWatcher, WorkspaceWatcher, null, visible: false);
        }

        string? state = facts.Latch switch
        {
            WatcherProcessLatch.Stopped => Stopped,
            WatcherProcessLatch.Restarting => Restarting,
            _ => WatcherHealth(facts),
        };
        return ViewOf(Row.WorkspaceWatcher, WorkspaceWatcher, state, visible: true);
    }

    private static string? WatcherHealth(SystemsFacts facts)
    {
        var row = facts.Health;
        if (row is null)
        {
            return Unknown;
        }

        var errored = !string.IsNullOrEmpty(row.ErrorClass)
            || !string.IsNullOrEmpty(row.GmailError)
            || !string.IsNullOrEmpty(row.CalendarError);
        var gmail = Age(row.GmailOkAt, facts.UtcNow);
        var calendar = Age(row.CalendarOkAt, facts.UtcNow);
        if (errored || gmail > SpeechConstants.GmailStaleSeconds || calendar > SpeechConstants.CalendarStaleSeconds)
        {
            return Degraded;
        }

        return null;
    }

    private static View GoogleRow(SystemsFacts facts)
    {
        if (facts.GoogleConnected is null)
        {
            return ViewOf(Row.GoogleAccount, GoogleAccount, null, visible: false);
        }

        return ViewOf(Row.GoogleAccount, GoogleAccount, facts.GoogleConnected.Value ? null : Reconnect, visible: true);
    }

    private static View RankerRow(SystemsFacts facts)
    {
        if (!facts.HealthSeen || string.IsNullOrEmpty(facts.RankerState))
        {
            return ViewOf(Row.Ranking, Ranking, null, visible: false);
        }

        if (Age(facts.RankerProgressAt, facts.UtcNow) > RankerStaleSeconds)
        {
            return ViewOf(Row.Ranking, Ranking, Stale, visible: true);
        }

        var state = facts.RankerState switch
        {
            "backing_off" => BackingOff,
            "provider_unavailable" => Unavailable,
            "auth_unavailable" => Auth,
            "worker_failed" => Failed,
            _ => null,
        };
        return ViewOf(Row.Ranking, Ranking, state, visible: true);
    }

    private static View VoiceRow(SystemsFacts facts)
    {
        string? state = facts.TtsRestoreActive ? Outage
            : facts.VoiceAvailable ? null
            : Unavailable;
        return ViewOf(Row.Voice, Voice, state, visible: true);
    }

    private static View CompanionRow(SystemsFacts facts)
    {
        // P10-INTAKE: the process latch wins. The link is a separate fact — P10-D12
        if (facts.PhoneKeepsFailing)
        {
            return ViewOf(Row.Companion, Companion, Failing, visible: true);
        }

        if (facts.PhoneLatch == WatcherProcessLatch.Restarting)
        {
            return ViewOf(Row.Companion, Companion, Restarting, visible: true);
        }

        if (facts.PhoneLatch == WatcherProcessLatch.Stopped)
        {
            return ViewOf(Row.Companion, Companion, Stopped, visible: true);
        }

        if (string.IsNullOrEmpty(facts.PhoneLink) || facts.PhoneLink == "unknown")
        {
            return ViewOf(Row.Companion, Companion, null, visible: false);
        }

        string? state = facts.PhoneLink switch
        {
            "connected" => null,
            "not_responding" => NotResponding,
            "reconnecting" => Reconnecting,
            "offline" => Offline,
            "no_tailnet" => NoTailnet,
            "not_paired" => NotPaired,
            _ => null,
        };
        var visible = state is not null || facts.PhoneLink == "connected";
        return ViewOf(Row.Companion, Companion, state, visible);
    }

    public static string? PairAction(SystemsFacts facts)
    {
        // P10-INTAKE: the dock button follows the row. The latch still wins — P10-D12
        var state = CompanionRow(facts).State;
        if (state == NotPaired)
        {
            return PairPhone;
        }

        if (state == Offline)
        {
            return RepairPhone;
        }

        return null;
    }

    private static View ViewOf(Row row, string label, string? state, bool visible)
    {
        var level = state is null ? Level.Quiet : LevelFor(row, state);
        return new View(row, label, state, level, visible);
    }

    private static double Age(string? stamp, DateTimeOffset utcNow)
    {
        if (string.IsNullOrEmpty(stamp) || !DateTimeOffset.TryParse(stamp, out var parsed))
        {
            return double.MaxValue;
        }

        return (utcNow - parsed).TotalSeconds;
    }
}

public readonly record struct SystemsFacts(
    bool BackendUp,
    bool BackendRestarting,
    bool BackendKeepsFailing,
    WatcherProcessLatch Latch,
    WatcherHealthRow? Health,
    bool HealthSeen,
    bool? GoogleConnected,
    string? RankerState,
    string? RankerProgressAt,
    DateTimeOffset UtcNow,
    bool VoiceAvailable,
    bool TtsRestoreActive,
    WatcherProcessLatch PhoneLatch = WatcherProcessLatch.Running,
    string? PhoneLink = null,
    bool PhoneKeepsFailing = false);
