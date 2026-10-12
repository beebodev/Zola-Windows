namespace Zola.Client.Supervision;

// P9-SUPERVISE: every restart, hung, reconnect, and log limit is a named constant — P9-D02
public static class SupervisionConstants
{
    public const int RestartLimit = 3;
    public const int RestartWindowMinutes = 10;
    public const int RestartBackoffSeconds = 2;
    public const int ReconnectAttemptLimit = 5;
    public const int ReconnectSpacingSeconds = 5;
    public const int ReconnectBudgetSeconds = 30;
    public const int HungHealthFailureLimit = 3;
    public const int HungProbeSpacingSeconds = 10;
    public const int ServeStderrMaxBytes = 1_048_576;
    public const int ServeStderrMaxFiles = 3;
    public const int ServeStderrRetentionDays = 14;
    public const int DumpRetentionDays = 14;

    public const string StatusRestarting = "Zola's backend stopped. Restarting…";
    public const string StatusKeepsFailing = "Zola's backend keeps failing. Restart Zola to try again.";
    public const string VoiceOfflineLabel = "Offline";

    public const string ProcServe = "serve";
    public const string EventRestart = "restart";
    public const string EventStale = "stale";
    public const string EventKeepsFailing = "keeps_failing";
    public const string EventStderrAclFailed = "stderr_acl_failed";
    public const string EventTtsRestoreMismatch = "tts_restore_mismatch";
    public const string GapReason = "backend-unreachable";

    public static bool StderrShouldRotate(long length) => length >= ServeStderrMaxBytes;

    public static bool RetentionExpired(DateTimeOffset writtenUtc, DateTimeOffset now, int days)
        => writtenUtc <= now.AddDays(-days);
}
