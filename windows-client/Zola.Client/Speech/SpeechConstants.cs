namespace Zola.Client.Speech;

// P9-SPEAK: named bounds from the Phase 3 verdicts — P9-D11
public static class SpeechConstants
{
    public const int IdleSeconds = 20;
    public const int PollSeconds = 20;
    public const int SnapshotTimeoutSeconds = 2;
    public const int StartTimeoutSeconds = 15;
    public const int CompleteTimeoutSeconds = 60;
    public const int EchoTailSeconds = 2;
    public const int LockHoldMs = 50;
    public const int QuietStartHour = 22;
    public const int QuietEndHour = 7;
    public const int OutcomeRetrySeconds = 5;
    public const int GmailStaleSeconds = 360;
    public const int CalendarStaleSeconds = 14400;

    public const string StampComposer = "composer";
    public const string StampWake = "wake";
    public const string StampPushToTalk = "push_to_talk";
    public const string StampSubmit = "submit";
    public const string StampTurn = "turn";
    public const string StampStop = "stop";

    public static string CancelledBy(string stamp) => "cancelled_by_" + stamp;

    public const string ReasonNotIdle = "not_idle";
    public const string ReasonNothingSpeakable = "nothing_speakable";
    public const string ReasonQuietHours = "quiet_hours";
    public const string ReasonSnapshotStale = "snapshot_stale";
    public const string ReasonSnapshotTimeout = "snapshot_timeout";
    public const string ReasonBackendDown = "backend_down";
    public const string ReasonReservationLost = "reservation_lost";
    public const string ReasonSpeechStartedFailed = "speech_started_failed";
    public const string ReasonMonitorUnavailable = "monitor_unavailable";
    public const string ReasonVoiceTtsRefused = "voice_tts_refused";
    public const string ReasonStartTimeout = "start_timeout";
    public const string ReasonCompleteTimeout = "complete_timeout";
    public const string ReasonSecondBout = "second_bout";
    public const string ReasonOneAtATime = "one_at_a_time";
    public const string ReasonLocked = "locked";
    public const string ReasonSuspended = "suspended";
    public const string ReasonTextMode = "text_mode";
    public const string ReasonCapture = "capture";
    public const string ReasonTurn = "turn";
    public const string ReasonPlayback = "playback";
    public const string ReasonClarify = "clarify";
    public const string ReasonReviewedDraft = "reviewed_draft";
    public const string ReasonEcho = "echo";
    public const string ReasonRecoverFailed = "recover_failed";

    public static bool IsTerminalStoreReason(string? reason)
    {
        return reason is "illegal_transition" or "attempt_mismatch" or "not_found" or "bad_args";
    }

    public const string OutcomeDelivered = "delivered";
    public const string OutcomeUncertain = "delivery_uncertain";
    public const string OutcomeIdle = "idle";
    public const string OutcomeDeny = "deny";

    public const string HudWatcherStopped = "watcher stopped";
    public const string HudWatcherRestarting = "watcher restarting";
    public const string SpokenHealthy = "healthy";
    public const string SpokenDegraded = "degraded";
    public const string SpokenNeedsReconnect = "needs_reconnect";
    public const string SpokenUnknown = "unknown";
}
