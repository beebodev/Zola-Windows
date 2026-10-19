using System.Text.Json;

namespace Zola.Client.Speech;

// P9-SPEAK: proactive calls use the 2s timeout and fault on timeout. wake.start is unchanged — P9-D11
internal sealed class ChatSpeechGateway : ISpeechGateway
{
    private readonly ChatSocket _chat;
    private static readonly TimeSpan Timeout = TimeSpan.FromSeconds(SpeechConstants.SnapshotTimeoutSeconds);

    public ChatSpeechGateway(ChatSocket chat)
    {
        _chat = chat;
    }

    public async Task<SpeechStoreReply> RecoverAsync()
    {
        var reply = await CallAsync("proactive.recover").ConfigureAwait(false);
        return ToStore(reply);
    }

    public async Task<SpeechSnapshot> SnapshotAsync()
    {
        var reply = await CallAsync("proactive.snapshot").ConfigureAwait(false);
        if (!reply.Ok)
        {
            return new SpeechSnapshot(false, FailureReason(reply, SpeechConstants.ReasonSnapshotTimeout), false, false, null);
        }

        using var doc = JsonDocument.Parse(reply.Payload ?? "{}");
        var root = doc.RootElement;
        DateTimeOffset? server = null;
        if (root.TryGetProperty("server_time", out var stamp)
            && stamp.ValueKind == JsonValueKind.String
            && DateTimeOffset.TryParse(stamp.GetString(), out var parsed))
        {
            server = parsed;
        }

        return new SpeechSnapshot(
            true,
            null,
            ReadBool(root, "turn_in_flight"),
            ReadBool(root, "reviewed_draft"),
            server);
    }

    public async Task<SpeechClaimResult> ClaimAsync()
    {
        var reply = await CallAsync("proactive.claim").ConfigureAwait(false);
        if (!reply.Ok)
        {
            return new SpeechClaimResult(false, reply.Error ?? SpeechConstants.ReasonBackendDown, null, null, null, null, null);
        }

        using var doc = JsonDocument.Parse(reply.Payload ?? "{}");
        var root = doc.RootElement;
        return new SpeechClaimResult(
            true,
            null,
            ReadString(root, "item_id"),
            ReadString(root, "attempt_id"),
            ReadString(root, "name"),
            ReadString(root, "name_source"),
            ReadString(root, "source"));
    }

    public Task<SpeechStoreReply> SpeechStartedAsync(string itemId, string attemptId)
    {
        return AttemptAsync("proactive.speech_started", itemId, attemptId, null);
    }

    public Task<SpeechStoreReply> OutcomeAsync(string itemId, string attemptId, string outcome)
    {
        return AttemptAsync("proactive.outcome", itemId, attemptId, outcome);
    }

    public Task<SpeechStoreReply> ReleaseAsync(string itemId, string attemptId)
    {
        return AttemptAsync("proactive.release", itemId, attemptId, null);
    }

    public async Task<bool> SpeakAsync(string phrase)
    {
        var reply = await CallAsync("voice.tts", new Dictionary<string, string?> { ["text"] = phrase }).ConfigureAwait(false);
        return reply.Ok && string.Equals(reply.Status, "speaking", StringComparison.Ordinal);
    }

    public async Task<WatcherHudResult> HealthAsync(WatcherProcessLatch latch, DateTimeOffset utcNow)
    {
        var reply = await CallAsync("proactive.watcher_health").ConfigureAwait(false);
        if (!reply.Ok)
        {
            return WatcherHud.Classify(null, latch, utcNow);
        }

        using var doc = JsonDocument.Parse(reply.Payload ?? "{}");
        var root = doc.RootElement;
        WatcherHealthRow? health = null;
        if (root.TryGetProperty("row", out var row) && row.ValueKind == JsonValueKind.Object)
        {
            health = new WatcherHealthRow
            {
                NeedsReconnect = ReadBool(row, "needs_reconnect") ? 1 : ReadInt(row, "needs_reconnect"),
                GmailOkAt = ReadString(row, "gmail_ok_at"),
                CalendarOkAt = ReadString(row, "calendar_ok_at"),
                GmailError = ReadString(row, "gmail_error"),
                CalendarError = ReadString(row, "calendar_error"),
                ErrorClass = ReadString(row, "error_class"),
            };
        }

        var classified = WatcherHud.Classify(health, latch, utcNow);
        return classified with
        {
            GoogleConnected = ReadOptionalBool(root, "google_connected"),
            RankerState = ReadString(root, "ranker_state"),
            RankerProgressAt = ReadString(root, "ranker_progress_at"),
            HealthSeen = true,
            Health = health,
        };
    }

    private async Task<SpeechStoreReply> AttemptAsync(string method, string itemId, string attemptId, string? outcome)
    {
        var parameters = new Dictionary<string, string?>
        {
            ["item_id"] = itemId,
            ["attempt_id"] = attemptId,
        };
        if (outcome is not null)
        {
            parameters["outcome"] = outcome;
        }

        var reply = await CallAsync(method, parameters).ConfigureAwait(false);
        return ToStore(reply);
    }

    private static SpeechStoreReply ToStore(ChatSocket.RpcReply reply)
    {
        if (reply.Ok)
        {
            return new SpeechStoreReply(true, null);
        }

        var reason = string.Equals(reply.Error, SpeechConstants.ReasonSnapshotTimeout, StringComparison.Ordinal)
            ? SpeechConstants.ReasonSnapshotTimeout
            : (reply.Error ?? SpeechConstants.ReasonBackendDown);
        return new SpeechStoreReply(false, reason);
    }

    private async Task<ChatSocket.RpcReply> CallAsync(string method, Dictionary<string, string?>? parameters = null)
    {
        try
        {
            return await _chat.InvokeAsync(
                method,
                parameters ?? new Dictionary<string, string?>(),
                Timeout,
                faultOnTimeout: true).ConfigureAwait(false);
        }
        catch (ChatUnreachableException ex)
        {
            var reason = ex.Message.Contains("not answered", StringComparison.Ordinal)
                ? SpeechConstants.ReasonSnapshotTimeout
                : SpeechConstants.ReasonBackendDown;
            return new ChatSocket.RpcReply(false, reason, null, null, null);
        }
    }

    private static string FailureReason(ChatSocket.RpcReply reply, string timeoutReason)
    {
        if (string.Equals(reply.Error, SpeechConstants.ReasonSnapshotTimeout, StringComparison.Ordinal))
        {
            return timeoutReason;
        }

        return reply.Error ?? SpeechConstants.ReasonBackendDown;
    }

    private static bool? ReadOptionalBool(JsonElement obj, string name)
    {
        if (!obj.TryGetProperty(name, out var value))
        {
            return null;
        }

        if (value.ValueKind == JsonValueKind.True)
        {
            return true;
        }

        if (value.ValueKind == JsonValueKind.False)
        {
            return false;
        }

        return null;
    }

    private static bool ReadBool(JsonElement obj, string name)
    {
        if (!obj.TryGetProperty(name, out var value))
        {
            return false;
        }

        return value.ValueKind == JsonValueKind.True
            || (value.ValueKind == JsonValueKind.Number && value.GetInt32() != 0);
    }

    private static int ReadInt(JsonElement obj, string name)
    {
        if (!obj.TryGetProperty(name, out var value) || value.ValueKind != JsonValueKind.Number)
        {
            return 0;
        }

        return value.GetInt32();
    }

    private static string? ReadString(JsonElement obj, string name)
    {
        if (!obj.TryGetProperty(name, out var value) || value.ValueKind != JsonValueKind.String)
        {
            return null;
        }

        return value.GetString();
    }
}
