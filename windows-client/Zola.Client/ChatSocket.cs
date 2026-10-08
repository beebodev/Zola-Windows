using System.Net.WebSockets;
using System.Text;
using System.Text.Json;

namespace Zola.Client;

// P1-CLIENT: /api/ws speaks JSON-RPC turns; opening the socket does not create a session — P1-D01
sealed class ChatSocket : IDisposable
{
    private const int RpcTimeoutMs = 45_000;
    private const int HealthIntervalMs = 2_000;

    // P2-VOICE: voice event names and payload fields are named constants on this socket — P2-D01
    private const string EventVoiceStatus = "voice.status";
    private const string EventVoiceTranscript = "voice.transcript";
    private const string EventVoiceInterrupted = "voice.interrupted";
    private const string EventWakeDetected = "wake.detected";
    private const string FieldState = "state";
    private const string FieldText = "text";
    private const string FieldStopPhrase = "stop_phrase";
    private const string FieldNoSpeechLimit = "no_speech_limit";
    private const string FieldFiltered = "filtered";
    private const string FieldPhrase = "phrase";
    private const string FieldProfile = "profile";
    private const string FieldStartNewSession = "start_new_session";
    private const string FieldEnabled = "enabled";
    private const string FieldAvailable = "available";
    private const string FieldAudioAvailable = "audio_available";
    private const string FieldSttAvailable = "stt_available";
    // P2-SPEAK: voice.toggle replies report spoken replies in tts — P2-D03
    private const string FieldTts = "tts";
    private const string FieldDetails = "details";
    private const string FieldReason = "reason";
    // P2-WAKE: wake.* replies add started/stopped/paused/resumed/listening and status flags — P2-D04
    private const string FieldStarted = "started";
    private const string FieldStopped = "stopped";
    private const string FieldPaused = "paused";
    private const string FieldResumed = "resumed";
    private const string FieldListening = "listening";
    private const string FieldOwnedByCaller = "owned_by_caller";
    private const string FieldAudioSilent = "audio_silent";
    private const string FieldHint = "hint";
    // P4-FEEDBACK: tool.* event names and payload fields — P4-D16
    private const string EventToolStart = "tool.start";
    private const string EventToolComplete = "tool.complete";
    private const string EventToolGenerating = "tool.generating";
    private const string EventToolOutputRisk = "tool.output_risk";
    private const string FieldToolId = "tool_id";
    private const string FieldName = "name";
    private const string FieldRisk = "risk";
    private const string ToolRiskLogFile = "tool-events.log";
    private const string ToolRiskLineFormat = "tool.output_risk name={0} risk={1}";
    internal const string ErrorTimeout = "timeout";

    private readonly HermesProcessManager _backend;
    private readonly CancellationTokenSource _lifetime = new();
    private readonly SemaphoreSlim _send = new(1, 1);
    private readonly Dictionary<int, TaskCompletionSource<RpcReply>> _pending = new();
    private readonly object _pendingGate = new();

    private readonly SemaphoreSlim _open = new(1, 1);
    private ClientWebSocket? _socket;
    private Task _reader = Task.CompletedTask;
    private int _nextId;
    private int _faulted;
    private int _suppressFault;
    private int _healthStarted;

    public ChatSocket(HermesProcessManager backend)
    {
        // P1-CLIENT: the socket uses the process manager's port and minted token after health passes — P1-D01
        _backend = backend;
    }

    public string? SessionId { get; private set; }

    public string? StoredSessionId { get; private set; }

    public event Action<string, string>? SessionReady;

    // P4-REQUEST: last open_requests snapshot from create/resume/activate — P4-D11
    public IReadOnlyList<OpenRequestSnapshot> LastOpenRequests { get; private set; } = Array.Empty<OpenRequestSnapshot>();

    public bool LastPendingApprovalPresent { get; private set; }

    public event Action<string>? SubmitAcknowledged;

    public event Action? MessageStarted;

    public event Action<string>? MessageDelta;

    public event Action<string, string>? MessageCompleted;

    public event Action<string>? InterruptAcknowledged;

    public event Action<string>? Routed;

    public event Action<string>? Unreachable;

    // P2-VOICE: voice.status, voice.transcript, voice.interrupted, and wake.detected become typed events — P2-D01
    public event Action<string>? VoiceStatusChanged;

    public event Action<VoiceTranscript>? VoiceTranscriptReceived;

    public event Action? VoiceInterrupted;

    public event Action<string, string?, bool>? WakeDetected;

    // P2-WAKE: wake.stop must run on the old socket before Abort; VoiceController owns the handler — P2-D04
    public Func<Task>? BeforeReplaceAsync { get; set; }

    public Task StartAsync()
    {
        // P1-SESSION: launch still asks the server for a new id; the client does not mint one — P1-D04
        return OpenAsync("session.create", new Dictionary<string, string?>());
    }

    public Task BeginNewSessionAsync()
    {
        // P1-SESSION: a new session is a fresh /api/ws plus session.create, which assigns both ids — P1-D04
        return OpenAsync("session.create", new Dictionary<string, string?>());
    }

    public Task ResumeStoredAsync(string storedSessionId)
    {
        // P1-SESSION: session.resume takes the stored id and returns a new runtime session_id — P1-D04
        return OpenAsync("session.resume", new Dictionary<string, string?>
        {
            ["session_id"] = storedSessionId,
        });
    }

    // P4-REQUEST: cloned server-request frames for the broker — P4-D06
    public event Action<string, string, Dictionary<string, JsonElement>>? ServerRequestReceived;

    // P4-REQUEST: request.cancel payload for the broker — P4-D11
    public event Action<string, string?, string?>? ServerRequestCancelled;

    // P4-REQUEST: socket about to be replaced; broker clears current session — P4-D11
    public event Action? Replacing;

    // P4-FEEDBACK: typed tool lifecycle for the activity line (time = UTC ticks) — P4-D16
    public event Action<string?, string, long>? ToolStarted;

    public event Action<string?, string, long>? ToolCompleted;

    public event Action<string, long>? ToolGenerating;

#if DEBUG
    // P4-REQUEST: DEBUG inject shares the live ServerRequestReceived hand-off — P4-D06
    public void DebugInjectServerRequest(string id, string method, Dictionary<string, JsonElement> parameters)
    {
        ServerRequestReceived?.Invoke(id, method, parameters);
    }
#endif

    private async Task OpenAsync(string method, Dictionary<string, string?> parameters)
    {
        // P1-SESSION: replace the previous socket so create and resume do not share one runtime session — P1-D04
        if (_backend.Port is not int port || port <= 0 || string.IsNullOrEmpty(_backend.SessionToken))
        {
            throw new ChatUnreachableException("Backend unreachable. The health gate is still closed.");
        }

        await _open.WaitAsync(_lifetime.Token).ConfigureAwait(false);
        try
        {
            // P4-REQUEST: signal replace before aborting so mid-resume requests are not tombstoned — P4-D11
            Replacing?.Invoke();

            // P2-WAKE: disarm the old transport while Send still works; skip if that socket is already dead — P2-D04
            if (_socket is { State: WebSocketState.Open } && BeforeReplaceAsync is { } replacing)
            {
                try
                {
                    await replacing().ConfigureAwait(false);
                }
                catch (ChatUnreachableException)
                {
                }
            }

            Interlocked.Exchange(ref _suppressFault, 1);
            AbandonPending();
            var previous = _socket;
            _socket = null;
            SessionId = null;
            try
            {
                previous?.Abort();
            }
            catch (WebSocketException)
            {
            }

            try
            {
                await _reader.WaitAsync(TimeSpan.FromSeconds(2)).ConfigureAwait(false);
            }
            catch (TimeoutException)
            {
            }

            var socket = new ClientWebSocket();
            socket.Options.Proxy = null;
            var uri = new Uri($"ws://{ZolaServeCommand.BindHost}:{port}/api/ws?token={Uri.EscapeDataString(_backend.SessionToken)}");
            try
            {
                await socket.ConnectAsync(uri, _lifetime.Token).ConfigureAwait(false);
            }
            catch (Exception ex) when (ex is WebSocketException or InvalidOperationException or OperationCanceledException)
            {
                // P1-SESSION: a failed upgrade still means the backend is unreachable — P1-D04
                Interlocked.Exchange(ref _suppressFault, 0);
                Fault(ex.Message);
                throw new ChatUnreachableException("Backend unreachable. /api/ws did not connect.");
            }

            Interlocked.Exchange(ref _suppressFault, 0);
            _socket = socket;
            _reader = Task.Run(() => ReadLoopAsync());
            if (Interlocked.Exchange(ref _healthStarted, 1) == 0)
            {
                _ = Task.Run(WatchHealthAsync);
            }

            RpcReply greeted;
            try
            {
                greeted = await CallAsync(method, parameters).ConfigureAwait(false);
            }
            catch (ChatUnreachableException)
            {
                throw;
            }
            catch (Exception ex)
            {
                Fault(ex.Message);
                throw new ChatUnreachableException("Backend unreachable. " + method + " was not answered.");
            }

            if (!greeted.Ok || string.IsNullOrEmpty(greeted.SessionId))
            {
                // P1-SESSION: without a runtime session id the composer stays closed — P1-D04
                throw new InvalidOperationException(greeted.Error ?? method + " did not return a session id.");
            }

            SessionId = greeted.SessionId;
            StoredSessionId = greeted.StoredSessionId ?? parameters.GetValueOrDefault("session_id") ?? "";
            // P4-REQUEST: surface open_requests; ignore pending_approval (no srq id) — P4-D11
            LastOpenRequests = greeted.OpenRequests ?? Array.Empty<OpenRequestSnapshot>();
            LastPendingApprovalPresent = greeted.PendingApprovalPresent;
            SessionReady?.Invoke(SessionId, StoredSessionId);
        }
        finally
        {
            _open.Release();
        }
    }

    private void AbandonPending()
    {
        // P1-SESSION: RPCs on the socket being replaced are cancelled, not reported as an unreachable backend — P1-D04
        List<TaskCompletionSource<RpcReply>> waiters;
        lock (_pendingGate)
        {
            waiters = _pending.Values.ToList();
            _pending.Clear();
        }

        foreach (var waiter in waiters)
        {
            waiter.TrySetCanceled();
        }
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

    public async Task<string> ExecSlashAsync(string command)
    {
        // P8-READ: /compress is slash.exec, not prompt.submit — P8-D09
        if (string.IsNullOrEmpty(SessionId))
        {
            throw new InvalidOperationException("session.create has not finished.");
        }

        var reply = await CallAsync("slash.exec", new Dictionary<string, string?>
        {
            ["session_id"] = SessionId,
            ["command"] = command,
        }).ConfigureAwait(false);
        if (!reply.Ok)
        {
            throw new InvalidOperationException(reply.Error ?? "slash.exec failed.");
        }

        return reply.Output ?? "";
    }

    public Task<RpcReply> InvokeAsync(string method, Dictionary<string, string?> parameters)
    {
        // P2-VOICE: voice methods use the same JSON-RPC send as chat, without a second socket — P2-D01
        return CallAsync(method, parameters);
    }

    public Task<RpcReply> InvokeAsync(string method, Dictionary<string, string?> parameters, TimeSpan timeout, bool faultOnTimeout)
    {
        // P2-WAKE: wake.start can download the sherpa model; a timeout must not Fault the socket — P2-D04
        return CallAsync(method, parameters, timeout, faultOnTimeout);
    }

    // P4-REQUEST: broker-only response writers; no method member (is_response_frame) — P4-D06
    public Task SendResponseAsync(string id, object result)
    {
        var payload = new Dictionary<string, object?>
        {
            ["jsonrpc"] = "2.0",
            ["id"] = id,
            ["result"] = result,
        };
        return SendTextAsync(JsonSerializer.Serialize(payload));
    }

    public Task SendErrorAsync(string id, int code, string message)
    {
        var payload = new Dictionary<string, object?>
        {
            ["jsonrpc"] = "2.0",
            ["id"] = id,
            ["error"] = new Dictionary<string, object?>
            {
                ["code"] = code,
                ["message"] = message,
            },
        };
        return SendTextAsync(JsonSerializer.Serialize(payload));
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
        _open.Dispose();
    }

    private Task<RpcReply> CallAsync(string method, Dictionary<string, string?> parameters)
    {
        return CallAsync(method, parameters, TimeSpan.FromMilliseconds(RpcTimeoutMs), faultOnTimeout: true);
    }

    private async Task<RpcReply> CallAsync(string method, Dictionary<string, string?> parameters, TimeSpan timeout, bool faultOnTimeout)
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
            return await pending.Task.WaitAsync(timeout, _lifetime.Token).ConfigureAwait(false);
        }
        catch (OperationCanceledException) when (_lifetime.IsCancellationRequested)
        {
            throw new ChatUnreachableException("Backend unreachable. The socket closed.");
        }
        catch (TimeoutException)
        {
            if (!faultOnTimeout)
            {
                // P2-WAKE: a wake.start timeout reconciles via wake.status instead of killing the socket — P2-D04
                return new RpcReply(false, ErrorTimeout, null, null, null);
            }

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
                    // P1-SESSION: replacing the socket must not stop the health watch — P1-D04
                    if (Volatile.Read(ref _suppressFault) != 0)
                    {
                        continue;
                    }

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
                // P4-REQUEST: hand string-id server requests to the broker; clone params first — P4-D06
                var requestIdText = requestId.GetString() ?? "";
                Dictionary<string, JsonElement> parameters;
                if (root.TryGetProperty("params", out var paramsElement) && paramsElement.ValueKind == JsonValueKind.Object)
                {
                    parameters = CloneObject(paramsElement);
                }
                else
                {
                    parameters = new Dictionary<string, JsonElement>(StringComparer.Ordinal);
                }

                ServerRequestReceived?.Invoke(requestIdText, method, parameters);
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
            case EventVoiceStatus:
                // P2-VOICE: recorder state is a status event, not assistant text — P2-D01
                VoiceStatusChanged?.Invoke(hasPayload ? ReadString(payload, FieldState) ?? "" : "");
                return;
            case EventVoiceTranscript:
                // P2-VOICE: text, stop phrase, and no-speech limit are one transcript event — P2-D01
                // P4-FEEDBACK: filtered flag for hallucination logging (never text) — P4-D18
                VoiceTranscriptReceived?.Invoke(new VoiceTranscript(
                    hasPayload ? ReadString(payload, FieldText) ?? "" : "",
                    hasPayload && ReadBool(payload, FieldStopPhrase) == true,
                    hasPayload && ReadBool(payload, FieldNoSpeechLimit) == true,
                    hasPayload && ReadBool(payload, FieldFiltered) == true));
                return;
            case EventVoiceInterrupted:
                // P2-VOICE: barge-in is parsed now; Track 2 is what acts on it beyond a status line — P2-D01
                VoiceInterrupted?.Invoke();
                return;
            case EventWakeDetected:
                // P2-WAKE: VoiceController is the only subscriber and decides whether a capture starts — P2-D04
                WakeDetected?.Invoke(
                    hasPayload ? ReadString(payload, FieldPhrase) ?? "" : "",
                    hasPayload ? ReadString(payload, FieldProfile) : null,
                    hasPayload && ReadBool(payload, FieldStartNewSession) == true);
                return;
            case "request.cancel":
                // P4-REQUEST: forward cancel to the broker — P4-D11
                if (hasPayload)
                {
                    ServerRequestCancelled?.Invoke(
                        ReadString(payload, "id") ?? "",
                        ReadString(payload, "method"),
                        ReadString(payload, "reason"));
                }

                return;
            case EventToolStart:
                // P4-FEEDBACK: forward tool.start with tool_id + name — P4-D16
                if (hasPayload)
                {
                    ToolStarted?.Invoke(
                        ReadString(payload, FieldToolId),
                        ReadString(payload, FieldName) ?? "",
                        DateTimeOffset.UtcNow.UtcTicks);
                }

                return;
            case EventToolComplete:
                // P4-FEEDBACK: forward tool.complete with tool_id + name — P4-D16
                if (hasPayload)
                {
                    ToolCompleted?.Invoke(
                        ReadString(payload, FieldToolId),
                        ReadString(payload, FieldName) ?? "",
                        DateTimeOffset.UtcNow.UtcTicks);
                }

                return;
            case EventToolGenerating:
                // P4-FEEDBACK: provisional hint only (no tool_id) — P4-D16
                if (hasPayload)
                {
                    ToolGenerating?.Invoke(
                        ReadString(payload, FieldName) ?? "",
                        DateTimeOffset.UtcNow.UtcTicks);
                }

                return;
            case EventToolOutputRisk:
                // P4-FEEDBACK: log name + risk only; never findings text — P4-D16
                if (hasPayload)
                {
                    WriteToolRiskLog(string.Format(
                        ToolRiskLineFormat,
                        ReadString(payload, FieldName) ?? "",
                        ReadString(payload, FieldRisk) ?? ""));
                }

                return;
            default:
                // P1-CLIENT: reasoning.delta and other event types are read and not appended — P1-D01
                return;
        }
    }

    // P4-FEEDBACK: tool.output_risk lands beside voice-timeline; write failures are ignored — P4-D16
    private static void WriteToolRiskLog(string line)
    {
        try
        {
            var root = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                VoiceController.TimelineClientFolder,
                VoiceController.TimelineLogFolder);
            Directory.CreateDirectory(root);
            File.AppendAllText(
                Path.Combine(root, ToolRiskLogFile),
                DateTimeOffset.Now.ToString("o") + " " + line + Environment.NewLine);
        }
        catch
        {
        }
    }

    private void Fault(string reason)
    {
        // P1-SESSION: aborting the previous socket for create or resume is not a dead backend — P1-D04
        if (Volatile.Read(ref _suppressFault) != 0)
        {
            return;
        }

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
            // P1-SESSION: session.create returns stored_session_id; session.resume returns session_key — P1-D04
            ReadString(result, "stored_session_id") ?? ReadString(result, "session_key") ?? ReadString(result, "resumed"),
            // P2-VOICE: voice.toggle and voice.record answers are read here without changing chat replies — P2-D01
            ReadBool(result, FieldEnabled),
            ReadBool(result, FieldAvailable),
            ReadBool(result, FieldAudioAvailable),
            ReadBool(result, FieldSttAvailable),
            ReadString(result, FieldDetails),
            ReadString(result, FieldReason),
            // P2-SPEAK: tts is the spoken-reply flag; chat replies leave it unset — P2-D03
            ReadBool(result, FieldTts),
            // P2-WAKE: wake.start/stop/pause/resume/status fields; other RPCs leave them unset — P2-D04
            ReadBool(result, FieldStarted),
            ReadBool(result, FieldStopped),
            ReadBool(result, FieldPaused),
            ReadBool(result, FieldResumed),
            ReadBool(result, FieldListening),
            ReadBool(result, FieldOwnedByCaller),
            ReadBool(result, FieldAudioSilent),
            ReadString(result, FieldHint),
            // P4-REQUEST: typed open_requests only; pending_approval is a presence flag — P4-D11
            ReadOpenRequests(result),
            result.TryGetProperty("pending_approval", out var pending) && pending.ValueKind == JsonValueKind.Object,
            // P8-READ: slash.exec compress returns output as one system line — P8-D09
            ReadString(result, "output"));
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

    private static bool? ReadBool(JsonElement obj, string name)
    {
        // P2-VOICE: voice flags are JSON booleans, not the string fields chat already reads — P2-D01
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

    // P4-REQUEST: clone open_requests entries out of the reply document — P4-D11
    private static IReadOnlyList<OpenRequestSnapshot>? ReadOpenRequests(JsonElement result)
    {
        if (!result.TryGetProperty("open_requests", out var list) || list.ValueKind != JsonValueKind.Array)
        {
            return null;
        }

        var snapshots = new List<OpenRequestSnapshot>();
        foreach (var item in list.EnumerateArray())
        {
            if (item.ValueKind != JsonValueKind.Object)
            {
                continue;
            }

            var id = ReadString(item, "id");
            var method = ReadString(item, "method");
            if (string.IsNullOrEmpty(id) || string.IsNullOrEmpty(method))
            {
                continue;
            }

            Dictionary<string, JsonElement> parameters;
            if (item.TryGetProperty("params", out var paramsElement) && paramsElement.ValueKind == JsonValueKind.Object)
            {
                parameters = CloneObject(paramsElement);
            }
            else
            {
                parameters = new Dictionary<string, JsonElement>(StringComparer.Ordinal);
            }

            snapshots.Add(new OpenRequestSnapshot(id, method, parameters));
        }

        return snapshots;
    }

    private static Dictionary<string, JsonElement> CloneObject(JsonElement obj)
    {
        var map = new Dictionary<string, JsonElement>(StringComparer.Ordinal);
        foreach (var prop in obj.EnumerateObject())
        {
            map[prop.Name] = prop.Value.Clone();
        }

        return map;
    }

    // P2-VOICE: voice replies add optional fields; chat still reads Ok, Error, Status, and the session ids — P2-D01
    internal readonly record struct RpcReply(
        bool Ok,
        string? Error,
        string? Status,
        string? SessionId,
        string? StoredSessionId,
        bool? Enabled = null,
        bool? Available = null,
        bool? AudioAvailable = null,
        bool? SttAvailable = null,
        string? Details = null,
        string? Reason = null,
        // P2-SPEAK: null until a voice.toggle reply includes tts — P2-D03
        bool? Tts = null,
        // P2-WAKE: null until a wake.* reply includes the field — P2-D04
        bool? Started = null,
        bool? Stopped = null,
        bool? Paused = null,
        bool? Resumed = null,
        bool? Listening = null,
        bool? OwnedByCaller = null,
        bool? AudioSilent = null,
        string? Hint = null,
        // P4-REQUEST: optional open_requests from resume/activate — P4-D11
        IReadOnlyList<OpenRequestSnapshot>? OpenRequests = null,
        bool PendingApprovalPresent = false,
        string? Output = null);

    // P4-REQUEST: one open_requests row cloned for the broker — P4-D11
    internal readonly record struct OpenRequestSnapshot(string Id, string Method, Dictionary<string, JsonElement> Params);

    // P2-VOICE: one transcript carries the text plus the stop-phrase and no-speech flags — P2-D01
    // P4-FEEDBACK: filtered is the hallucination flag; timeline logs never include text — P4-D18
    internal readonly record struct VoiceTranscript(string Text, bool IsStopPhrase, bool IsNoSpeechLimit, bool Filtered);
}

// P1-CLIENT: socket loss and health loss share one exception so the composer cannot keep waiting — P1-D01
sealed class ChatUnreachableException : IOException
{
    public ChatUnreachableException(string message)
        : base(message)
    {
    }
}
