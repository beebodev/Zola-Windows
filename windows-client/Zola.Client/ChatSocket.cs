using System.Net.WebSockets;
using System.Text;
using System.Text.Json;

namespace Zola.Client;

// P1-CLIENT: /api/ws speaks JSON-RPC turns; opening the socket does not create a session — P1-D01
sealed class ChatSocket : IDisposable
{
    private const int RpcTimeoutMs = 45_000;
    private const int HealthIntervalMs = 2_000;

    private readonly HermesProcessManager _backend;
    private readonly CancellationTokenSource _lifetime = new();
    private readonly SemaphoreSlim _send = new(1, 1);
    private readonly Dictionary<int, TaskCompletionSource<RpcReply>> _pending = new();
    private readonly object _pendingGate = new();

    private ClientWebSocket? _socket;
    private int _nextId;
    private int _faulted;

    public ChatSocket(HermesProcessManager backend)
    {
        // P1-CLIENT: the socket uses the process manager's port and minted token after health passes — P1-D01
        _backend = backend;
    }

    public string? SessionId { get; private set; }

    public string? StoredSessionId { get; private set; }

    public event Action<string, string>? SessionReady;

    public event Action<string>? SubmitAcknowledged;

    public event Action? MessageStarted;

    public event Action<string>? MessageDelta;

    public event Action<string, string>? MessageCompleted;

    public event Action<string>? InterruptAcknowledged;

    public event Action<string>? Routed;

    public event Action<string>? Unreachable;

    public async Task StartAsync()
    {
        // P1-CLIENT: connect with ?token= then session.create once before any prompt.submit — P1-D01
        if (_backend.Port is not int port || port <= 0 || string.IsNullOrEmpty(_backend.SessionToken))
        {
            throw new ChatUnreachableException("Backend unreachable. The health gate is still closed.");
        }

        var socket = new ClientWebSocket();
        socket.Options.Proxy = null;
        _socket = socket;
        var uri = new Uri($"ws://{ZolaServeCommand.BindHost}:{port}/api/ws?token={Uri.EscapeDataString(_backend.SessionToken)}");
        try
        {
            await socket.ConnectAsync(uri, _lifetime.Token).ConfigureAwait(false);
        }
        catch (Exception ex) when (ex is WebSocketException or InvalidOperationException or OperationCanceledException)
        {
            // P1-CLIENT: a failed upgrade is the unreachable state, not a hung composer — P1-D01
            Fault(ex.Message);
            throw new ChatUnreachableException("Backend unreachable. /api/ws did not connect.");
        }

        _ = Task.Run(ReadLoopAsync);
        _ = Task.Run(WatchHealthAsync);
        RpcReply created;
        try
        {
            created = await CallAsync("session.create", new Dictionary<string, string?>()).ConfigureAwait(false);
        }
        catch (ChatUnreachableException)
        {
            throw;
        }
        catch (Exception ex)
        {
            Fault(ex.Message);
            throw new ChatUnreachableException("Backend unreachable. session.create was not answered.");
        }

        if (!created.Ok || string.IsNullOrEmpty(created.SessionId))
        {
            // P1-CLIENT: without a stored session id the composer stays closed — P1-D01
            throw new InvalidOperationException(created.Error ?? "session.create did not return a session id.");
        }

        SessionId = created.SessionId;
        StoredSessionId = created.StoredSessionId ?? "";
        SessionReady?.Invoke(SessionId, StoredSessionId);
    }

    public async Task SubmitAsync(string text)
    {
        // P1-CLIENT: prompt.submit returns status immediately; the reply arrives later as events — P1-D01
        if (string.IsNullOrEmpty(SessionId))
        {
            throw new InvalidOperationException("session.create has not finished.");
        }

        var reply = await CallAsync("prompt.submit", new Dictionary<string, string?>
        {
            ["session_id"] = SessionId,
            ["text"] = text,
        }).ConfigureAwait(false);
        if (!reply.Ok)
        {
            throw new InvalidOperationException(reply.Error ?? "prompt.submit failed.");
        }

        SubmitAcknowledged?.Invoke(reply.Status ?? "");
    }

    public async Task InterruptAsync()
    {
        // P1-CLIENT: session.interrupt returns {status: interrupted} and the turn also completes later — P1-D01
        if (string.IsNullOrEmpty(SessionId))
        {
            return;
        }

        var reply = await CallAsync("session.interrupt", new Dictionary<string, string?>
        {
            ["session_id"] = SessionId,
        }).ConfigureAwait(false);
        if (!reply.Ok)
        {
            throw new InvalidOperationException(reply.Error ?? "session.interrupt failed.");
        }

        InterruptAcknowledged?.Invoke(reply.Status ?? "");
    }

    public void Dispose()
    {
        // P1-CLIENT: window close cancels the read loop without treating it as a second shutdown of hermes — P1-D01
        try
        {
            _lifetime.Cancel();
        }
        catch (ObjectDisposedException)
        {
        }

        try
        {
            _socket?.Abort();
        }
        catch (WebSocketException)
        {
        }

        _lifetime.Dispose();
        _send.Dispose();
    }

    private async Task<RpcReply> CallAsync(string method, Dictionary<string, string?> parameters)
    {
        // P1-CLIENT: integer ids stay clear of server srq- request ids on the same socket — P1-D01
        var id = Interlocked.Increment(ref _nextId);
        var pending = new TaskCompletionSource<RpcReply>(TaskCreationOptions.RunContinuationsAsynchronously);
        lock (_pendingGate)
        {
            _pending[id] = pending;
        }

        var payload = new Dictionary<string, object?>
        {
            ["jsonrpc"] = "2.0",
            ["id"] = id,
            ["method"] = method,
            ["params"] = parameters,
        };
        try
        {
            await SendTextAsync(JsonSerializer.Serialize(payload)).ConfigureAwait(false);
            return await pending.Task.WaitAsync(TimeSpan.FromMilliseconds(RpcTimeoutMs), _lifetime.Token).ConfigureAwait(false);
        }
        catch (OperationCanceledException) when (_lifetime.IsCancellationRequested)
        {
            throw new ChatUnreachableException("Backend unreachable. The socket closed.");
        }
        catch (TimeoutException)
        {
            Fault("the request was not answered");
            throw new ChatUnreachableException("Backend unreachable. The request was not answered.");
        }
        finally
        {
            lock (_pendingGate)
            {
                _pending.Remove(id);
            }
        }
    }

    private async Task SendTextAsync(string json)
    {
        var socket = _socket;
        if (socket is null || socket.State != WebSocketState.Open)
        {
            // P1-CLIENT: a send after the socket drops is unreachable, not a silent retry — P1-D01
            Fault("the socket is not open");
            throw new ChatUnreachableException("Backend unreachable. The socket is not open.");
        }

        var bytes = Encoding.UTF8.GetBytes(json);
        await _send.WaitAsync(_lifetime.Token).ConfigureAwait(false);
        try
        {
            await socket.SendAsync(bytes, WebSocketMessageType.Text, true, _lifetime.Token).ConfigureAwait(false);
        }
        catch (Exception ex) when (ex is WebSocketException or OperationCanceledException or ObjectDisposedException)
        {
            Fault(ex.Message);
            throw new ChatUnreachableException("Backend unreachable. The socket closed.");
        }
        finally
        {
            _send.Release();
        }
    }

    private async Task ReadLoopAsync()
    {
        // P1-CLIENT: one read loop demuxes events, RPC replies, and server requests — P1-D01
        var socket = _socket;
        if (socket is null)
        {
            return;
        }

        var buffer = new byte[8192];
        using var message = new MemoryStream();
        try
        {
            while (!_lifetime.IsCancellationRequested && socket.State == WebSocketState.Open)
            {
                message.SetLength(0);
                WebSocketReceiveResult result;
                do
                {
                    result = await socket.ReceiveAsync(buffer, _lifetime.Token).ConfigureAwait(false);
                    if (result.MessageType == WebSocketMessageType.Close)
                    {
                        Fault("the socket closed");
                        return;
                    }

                    message.Write(buffer, 0, result.Count);
                    if (message.Length > 8_000_000)
                    {
                        Fault("a frame was too large");
                        return;
                    }
                }
                while (!result.EndOfMessage);

                if (result.MessageType != WebSocketMessageType.Text || message.Length == 0)
                {
                    continue;
                }

                var json = Encoding.UTF8.GetString(message.GetBuffer(), 0, (int)message.Length);
                Dispatch(json);
            }
        }
        catch (OperationCanceledException)
        {
            // P1-CLIENT: dispose cancels the reader; that is not a backend failure — P1-D01
        }
        catch (WebSocketException ex)
        {
            Fault(ex.Message);
        }
        catch (Exception ex) when (ex is IOException or ObjectDisposedException)
        {
            Fault(ex.Message);
        }
    }

    private async Task WatchHealthAsync()
    {
        // P1-CLIENT: a later GET /api/health failure surfaces backend unreachable while the socket looks idle — P1-D01
        while (!_lifetime.IsCancellationRequested)
        {
            try
            {
                await Task.Delay(HealthIntervalMs, _lifetime.Token).ConfigureAwait(false);
                var ok = await _backend.CheckHealthAsync(_lifetime.Token).ConfigureAwait(false);
                if (_lifetime.IsCancellationRequested)
                {
                    return;
                }

                if (!ok)
                {
                    Fault("GET /api/health failed");
                    return;
                }
            }
            catch (OperationCanceledException)
            {
                return;
            }
            catch (Exception ex) when (ex is HttpRequestException or TaskCanceledException)
            {
                if (!_lifetime.IsCancellationRequested)
                {
                    Fault(ex.Message);
                }

                return;
            }
        }
    }

    private void Dispatch(string json)
    {
        try
        {
            using var doc = JsonDocument.Parse(json);
            var root = doc.RootElement;
            var method = ReadString(root, "method");
            if (method == "event")
            {
                // P1-CLIENT: method event is a notification; only message.* turns change the reply — P1-D01
                DispatchEvent(root);
                return;
            }

            if (method is not null && root.TryGetProperty("id", out var requestId) && requestId.ValueKind == JsonValueKind.String)
            {
                // P1-CLIENT: srq- server requests share this socket and are not chat tokens — P1-D01
                Routed?.Invoke($"Ignored a server request ({method}). It was not treated as a chat message.");
                return;
            }

            if (!root.TryGetProperty("id", out var idElement) || !idElement.TryGetInt32(out var id))
            {
                Routed?.Invoke("Ignored a socket frame that was not a chat turn.");
                return;
            }

            TaskCompletionSource<RpcReply>? pending;
            lock (_pendingGate)
            {
                _pending.TryGetValue(id, out pending);
            }

            pending?.TrySetResult(ReadReply(root));
        }
        catch (JsonException)
        {
            // P1-CLIENT: a non-JSON frame is dropped instead of being painted as assistant text — P1-D01
            Routed?.Invoke("Ignored a socket frame that was not JSON.");
        }
    }

    private void DispatchEvent(JsonElement root)
    {
        if (!root.TryGetProperty("params", out var eventParams) || eventParams.ValueKind != JsonValueKind.Object)
        {
            return;
        }

        var type = ReadString(eventParams, "type") ?? "";
        var sessionId = ReadString(eventParams, "session_id");
        if (!string.IsNullOrEmpty(SessionId) && !string.IsNullOrEmpty(sessionId) && sessionId != SessionId)
        {
            // P1-CLIENT: events for another runtime session are not appended to this transcript — P1-D01
            return;
        }

        var hasPayload = eventParams.TryGetProperty("payload", out var payload) && payload.ValueKind == JsonValueKind.Object;
        switch (type)
        {
            case "message.start":
                MessageStarted?.Invoke();
                return;
            case "message.delta":
                if (hasPayload && DeltaChunk(payload) is string chunk)
                {
                    MessageDelta?.Invoke(chunk);
                }

                return;
            case "message.complete":
                MessageCompleted?.Invoke(
                    hasPayload ? ReadString(payload, "status") ?? "complete" : "complete",
                    hasPayload ? FinalText(payload) : "");
                return;
            case "status.update":
                // P1-CLIENT: status.update is routed to the status line, not the assistant bubble — P1-D01
                if (hasPayload)
                {
                    Routed?.Invoke(ReadString(payload, "text") ?? type);
                }

                return;
            case "error":
                // P1-CLIENT: an error event is routed aside so it is not parsed as a streamed token — P1-D01
                Routed?.Invoke(hasPayload ? ReadString(payload, "message") ?? "error" : "error");
                return;
            default:
                // P1-CLIENT: reasoning.delta and other event types are read and not appended — P1-D01
                return;
        }
    }

    private void Fault(string reason)
    {
        if (Interlocked.Exchange(ref _faulted, 1) != 0)
        {
            return;
        }

        // P1-CLIENT: unblock anyone waiting on an RPC so the UI cannot sit on a dead socket — P1-D01
        List<TaskCompletionSource<RpcReply>> waiters;
        lock (_pendingGate)
        {
            waiters = _pending.Values.ToList();
            _pending.Clear();
        }

        foreach (var waiter in waiters)
        {
            waiter.TrySetException(new ChatUnreachableException("Backend unreachable. " + reason));
        }

        try
        {
            _socket?.Abort();
        }
        catch (WebSocketException)
        {
        }

        Unreachable?.Invoke(string.IsNullOrWhiteSpace(reason) ? "Backend unreachable." : "Backend unreachable. " + reason);
    }

    private static RpcReply ReadReply(JsonElement root)
    {
        if (root.TryGetProperty("error", out var error) && error.ValueKind == JsonValueKind.Object)
        {
            return new RpcReply(false, ReadString(error, "message") ?? "request failed", null, null, null);
        }

        if (!root.TryGetProperty("result", out var result) || result.ValueKind != JsonValueKind.Object)
        {
            return new RpcReply(true, null, null, null, null);
        }

        return new RpcReply(
            true,
            null,
            ReadString(result, "status"),
            ReadString(result, "session_id"),
            ReadString(result, "stored_session_id"));
    }

    private static string? DeltaChunk(JsonElement payload)
    {
        // P1-CLIENT: text is the delta; rendered is the same chunk's display form, not a second token — P1-D01
        var text = ReadString(payload, "text");
        if (!string.IsNullOrEmpty(text))
        {
            return text;
        }

        var rendered = ReadString(payload, "rendered");
        return string.IsNullOrEmpty(rendered) ? null : rendered;
    }

    private static string FinalText(JsonElement payload)
    {
        // P1-CLIENT: message.complete text replaces the streamed bubble; it is not another delta — P1-D01
        var text = ReadString(payload, "text");
        if (!string.IsNullOrEmpty(text))
        {
            return text;
        }

        return ReadString(payload, "rendered") ?? "";
    }

    private static string? ReadString(JsonElement obj, string name)
    {
        if (!obj.TryGetProperty(name, out var value))
        {
            return null;
        }

        return value.ValueKind == JsonValueKind.String ? value.GetString() : value.ToString();
    }

    private readonly record struct RpcReply(bool Ok, string? Error, string? Status, string? SessionId, string? StoredSessionId);
}

// P1-CLIENT: socket loss and health loss share one exception so the composer cannot keep waiting — P1-D01
sealed class ChatUnreachableException : IOException
{
    public ChatUnreachableException(string message)
        : base(message)
    {
    }
}
