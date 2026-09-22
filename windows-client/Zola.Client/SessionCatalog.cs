using System.Net.Http;
using System.Text;
using System.Text.Json;

namespace Zola.Client;

// P1-SESSION: list and transcript reads stay on the existing HTTP routes — P1-D04
sealed class SessionCatalog
{
    private static readonly HttpClient Http = new() { Timeout = TimeSpan.FromSeconds(30) };

    public static async Task<IReadOnlyList<SessionListItem>> ListAsync(HermesProcessManager backend, CancellationToken cancellationToken)
    {
        // P1-SESSION: GET /api/sessions supplies id and last_active for the toggle list — P1-D04
        using var doc = await GetAsync(backend, "/api/sessions?limit=100&order=recent", cancellationToken).ConfigureAwait(false);
        if (!doc.RootElement.TryGetProperty("sessions", out var sessions) || sessions.ValueKind != JsonValueKind.Array)
        {
            return Array.Empty<SessionListItem>();
        }

        var rows = new List<SessionListItem>();
        foreach (var session in sessions.EnumerateArray())
        {
            var id = ReadString(session, "id");
            if (string.IsNullOrEmpty(id))
            {
                continue;
            }

            var lastActive = ReadUnix(session, "last_active") ?? ReadUnix(session, "started_at") ?? 0;
            rows.Add(new SessionListItem { Id = id, LastActiveUnix = lastActive });
        }

        return rows;
    }

    public static async Task<IReadOnlyList<SessionTurn>> MessagesAsync(HermesProcessManager backend, string sessionId, CancellationToken cancellationToken)
    {
        // P1-SESSION: prior turns are GET /api/sessions/{id}/messages; the detail route has no transcript — P1-D04
        var path = "/api/sessions/" + Uri.EscapeDataString(sessionId) + "/messages";
        using var doc = await GetAsync(backend, path, cancellationToken).ConfigureAwait(false);
        if (!doc.RootElement.TryGetProperty("messages", out var messages) || messages.ValueKind != JsonValueKind.Array)
        {
            return Array.Empty<SessionTurn>();
        }

        var turns = new List<SessionTurn>();
        foreach (var message in messages.EnumerateArray())
        {
            if (ReadString(message, "display_kind") == "hidden")
            {
                continue;
            }

            var role = ReadString(message, "role");
            if (role is not ("user" or "assistant"))
            {
                continue;
            }

            var text = ReadText(message, "content");
            if (string.IsNullOrWhiteSpace(text))
            {
                text = ReadText(message, "display_content");
            }

            if (string.IsNullOrWhiteSpace(text))
            {
                continue;
            }

            turns.Add(new SessionTurn { Role = role, Text = text });
        }

        return turns;
    }

    private static async Task<JsonDocument> GetAsync(HermesProcessManager backend, string path, CancellationToken cancellationToken)
    {
        // P1-SESSION: these GETs take the dashboard token header; ?token= is only for /api/ws — P1-D04
        if (backend.Port is not int port || port <= 0 || string.IsNullOrEmpty(backend.SessionToken))
        {
            throw new SessionApiException("Backend unreachable. The session list has no token yet.");
        }

        var uri = new Uri($"http://{ZolaServeCommand.BindHost}:{port}{path}");
        using var request = new HttpRequestMessage(HttpMethod.Get, uri);
        request.Headers.TryAddWithoutValidation("X-Hermes-Session-Token", backend.SessionToken);
        HttpResponseMessage response;
        try
        {
            response = await Http.SendAsync(request, cancellationToken).ConfigureAwait(false);
        }
        catch (Exception ex) when (ex is HttpRequestException or TaskCanceledException)
        {
            throw new SessionApiException("Backend unreachable. " + ex.Message);
        }

        using (response)
        {
            var body = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
            if (!response.IsSuccessStatusCode)
            {
                throw new SessionApiException(ErrorText(body, (int)response.StatusCode));
            }

            try
            {
                return JsonDocument.Parse(body);
            }
            catch (JsonException)
            {
                throw new SessionApiException("The session service returned a response that was not JSON.");
            }
        }
    }

    private static string ErrorText(string body, int status)
    {
        try
        {
            using var doc = JsonDocument.Parse(body);
            var detail = ReadString(doc.RootElement, "detail");
            if (!string.IsNullOrEmpty(detail))
            {
                return detail;
            }
        }
        catch (JsonException)
        {
        }

        return $"Session request failed ({status}).";
    }

    private static string? ReadString(JsonElement obj, string name)
    {
        if (!obj.TryGetProperty(name, out var value) || value.ValueKind != JsonValueKind.String)
        {
            return null;
        }

        return value.GetString();
    }

    private static double? ReadUnix(JsonElement obj, string name)
    {
        if (!obj.TryGetProperty(name, out var value) || value.ValueKind != JsonValueKind.Number || !value.TryGetDouble(out var unix))
        {
            return null;
        }

        return unix;
    }

    private static string? ReadText(JsonElement message, string name)
    {
        if (!message.TryGetProperty(name, out var value))
        {
            return null;
        }

        if (value.ValueKind == JsonValueKind.String)
        {
            return value.GetString();
        }

        if (value.ValueKind != JsonValueKind.Array)
        {
            return null;
        }

        var text = new StringBuilder();
        foreach (var part in value.EnumerateArray())
        {
            if (part.ValueKind == JsonValueKind.String)
            {
                text.Append(part.GetString());
            }
            else if (part.ValueKind == JsonValueKind.Object && part.TryGetProperty("text", out var chunk) && chunk.ValueKind == JsonValueKind.String)
            {
                text.Append(chunk.GetString());
            }
        }

        return text.ToString();
    }
}

// P1-SESSION: one list row is the stored session id plus its last-activity time — P1-D04
sealed class SessionListItem
{
    public string Id { get; init; } = "";

    public double LastActiveUnix { get; init; }
}

// P1-SESSION: a resumed turn is a user or assistant message from the messages route — P1-D04
sealed class SessionTurn
{
    public string Role { get; init; } = "";

    public string Text { get; init; } = "";
}

// P1-SESSION: the list binds these fields and nothing else from the session row — P1-D04
public sealed class SessionRow
{
    public string Id { get; init; } = "";

    public string LastActiveText { get; init; } = "";

    public double SortKey { get; init; }

    internal static SessionRow FromServer(SessionListItem item)
    {
        return new SessionRow
        {
            Id = item.Id,
            LastActiveText = Format(item.LastActiveUnix),
            SortKey = item.LastActiveUnix,
        };
    }

    public static SessionRow JustAcknowledged(string id)
    {
        // P1-SESSION: a session.create result is listed before GET /api/sessions has the row — P1-D04
        return new SessionRow
        {
            Id = id,
            LastActiveText = "Just now",
            SortKey = DateTimeOffset.UtcNow.ToUnixTimeSeconds(),
        };
    }

    private static string Format(double unix)
    {
        if (unix <= 0)
        {
            return "No activity yet";
        }

        return DateTimeOffset.FromUnixTimeMilliseconds((long)(unix * 1000)).ToLocalTime().ToString("g");
    }
}

// P1-SESSION: a failed list or transcript read stays on the chat surface — P1-D04
sealed class SessionApiException : IOException
{
    public SessionApiException(string message)
        : base(message)
    {
    }
}
