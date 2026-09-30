using System.Text.Json;

namespace Zola.Client;

// P4-REQUEST: single owner of open server requests — P4-D06 / P4-D11 / P4-D12
sealed class ServerRequestBroker
{
    private const string MethodClarify = "clarify";
    private const string MethodApproval = "approval";
    private const string ChoiceOnce = "once";
    private const string ChoiceDeny = "deny";
    private const int ErrorMethodNotFound = -32601;
    private const string ErrorNotSupportedMessage = "not supported by this client";
    private const string NoticeUnsupportedPrefix = "Declined unsupported server request: ";
    private const string NoticeApprovalUnparseable = "Approval request could not be shown; denied.";
    private const string NoticeWithdrawnWhileAway = "A waiting question was withdrawn while you were away.";
    private const string LogClientFolder = "ZolaClient";
    private const string LogFolder = "logs";
    private const string LogFileName = "server-requests.log";
    private const string EventReceived = "received";
    private const string EventShown = "shown";
    private const string EventParked = "parked";
    private const string EventReshown = "reshown";
    private const string EventAnswered = "answered";
    private const string EventDeclined = "declined";
    private const string EventCancelled = "cancelled";
    private const string EventDropped = "dropped";
    private const string EventSendFailed = "send_failed";
    private const string EventWithdrawnWhileAway = "withdrawn_while_away";
    private const string EventReplayed = "replayed";
    private const string EventReplayIgnoredClosed = "replay_ignored_closed";
    private const string EventGatedClickRefused = "gated_click_refused";
    private const string EventPendingApprovalIgnored = "pending_approval_ignored";
    private const string DropReasonNotOpen = "not_open";
    private const string DropReasonAlreadySettled = "already_settled";
    private const string FieldSessionId = "session_id";
    private const string FieldQuestion = "question";
    private const string FieldQuestions = "questions";
    private const string FieldChoices = "choices";
    private const string FieldMultiSelect = "multi_select";
    private const string FieldAnswers = "answers";
    private const string FieldQid = "qid";
    private const string FieldCommand = "command";
    private const string FieldDescription = "description";
    private const string FieldRequestId = "request_id";
    private const string FieldAnswer = "answer";
    private const string FieldChoice = "choice";
    private const string RecommendedLabel = "(Recommended)";
    private const string DropReasonNoCurrentSession = "no_current_session";
    private const string DropReasonForeignSession = "foreign_session";

    private readonly object _gate = new();
    private readonly object _logGate = new();
    private readonly Dictionary<string, Entry> _entries = new(StringComparer.Ordinal);
    private readonly HashSet<string> _tombstones = new(StringComparer.Ordinal);
    private readonly ChatSocket _socket;
    private string? _currentSessionId;
    private long _nextSequence;
    // P4-REQUEST: sequences at/before this mark may be withdrawn on reconcile after socket replace — P4-D11
    private long _replaceMark;

    public ServerRequestBroker(ChatSocket socket)
    {
        _socket = socket;
    }

    public event Action<string, ClarifyView>? ClarifyOpened;

    public event Action<string, ApprovalView>? ApprovalOpened;

    public event Action<string, CloseOutcome>? RequestClosed;

    public event Action<string>? Notice;

    public enum Lifecycle
    {
        Open,
        Sending,
        Answered,
        Declined,
        Cancelled,
        SendFailed,
    }

    public enum CloseOutcome
    {
        Answered,
        Declined,
        Cancelled,
        SendFailed,
        WithdrawnWhileAway,
    }

    public sealed class ClarifyQuestionView
    {
        public string Qid { get; init; } = "";
        public string Question { get; init; } = "";
        public IReadOnlyList<string> Choices { get; init; } = Array.Empty<string>();
        public bool MultiSelect { get; init; }
        public string PrefillAnswer { get; init; } = "";
    }

    public sealed class ClarifyView
    {
        public bool IsBatch { get; init; }
        public string Question { get; init; } = "";
        public IReadOnlyList<string> Choices { get; init; } = Array.Empty<string>();
        public bool MultiSelect { get; init; }
        public IReadOnlyList<ClarifyQuestionView> Questions { get; init; } = Array.Empty<ClarifyQuestionView>();
        public bool Replayed { get; init; }
    }

    public sealed class ApprovalView
    {
        public string Command { get; init; } = "";
        public string Description { get; init; } = "";
        public bool Replayed { get; init; }
    }

    private sealed class Entry
    {
        public required string Id;
        public required string SessionId;
        public required string Method;
        public required Dictionary<string, JsonElement> Params;
        public required DateTimeOffset ReceivedAt;
        public required long ReceiptSequence;
        public Lifecycle State;
        public bool Replayed;
        public ClarifyView? Clarify;
        public ApprovalView? Approval;
    }

    public void MarkSocketReplacing()
    {
        // P4-REQUEST: clear current session before old socket dies; mark seq for reconcile — P4-D11
        lock (_gate)
        {
            _currentSessionId = null;
            _replaceMark = _nextSequence;
        }
    }

    public void OnSessionChanged(string? currentSessionId)
    {
        List<Action> raises;
        lock (_gate)
        {
            _currentSessionId = currentSessionId;
            raises = new List<Action>();
            foreach (var entry in _entries.Values)
            {
                if (entry.State != Lifecycle.Open)
                {
                    continue;
                }

                if (!string.IsNullOrEmpty(currentSessionId) && entry.SessionId == currentSessionId)
                {
                    // Re-show Open entries for the new current session (e.g. arrived during replace).
                    WriteLogLocked(EventReshown, entry.Id, entry.Method, entry.SessionId, null, "session_changed");
                    if (entry.Clarify is { } clarify)
                    {
                        var id = entry.Id;
                        raises.Add(() => ClarifyOpened?.Invoke(id, clarify));
                    }
                    else if (entry.Approval is { } approval)
                    {
                        var id = entry.Id;
                        raises.Add(() => ApprovalOpened?.Invoke(id, approval));
                    }

                    continue;
                }

                // Parked: stay Open; UI will hide via ClearTranscript.
                WriteLogLocked(EventParked, entry.Id, entry.Method, entry.SessionId, textOrLen: null, reason: "session_changed");
            }
        }

        RaiseAll(raises);
    }

    public void OnRequest(string id, string method, Dictionary<string, JsonElement> parameters, bool replayed = false)
    {
        List<Action> raises;
        lock (_gate)
        {
            raises = AcceptRequestLocked(id, method, parameters, replayed);
        }

        RaiseAll(raises);
    }

    public void OnCancel(string id, string? method, string? reason)
    {
        List<Action> raises;
        lock (_gate)
        {
            raises = AcceptCancelLocked(id, method, reason);
        }

        RaiseAll(raises);
    }

    public void LoadOpenRequests(string sessionId, IReadOnlyList<ChatSocket.OpenRequestSnapshot> snapshots)
    {
        List<Action> raises;
        lock (_gate)
        {
            raises = ReconcileOpenRequestsLocked(sessionId, snapshots);
        }

        RaiseAll(raises);
    }

    public void NotePendingApprovalIgnored(string? sessionId)
    {
        WriteLog(EventPendingApprovalIgnored, id: "-", method: MethodApproval, sessionId: sessionId ?? "", textOrLen: null, reason: "no_srq_id");
    }

    public void NoteGatedClickRefused(string id)
    {
        WriteLog(EventGatedClickRefused, id, MethodApproval, _currentSessionId ?? "", null, "voice_gated");
    }

    public Lifecycle? GetState(string id)
    {
        lock (_gate)
        {
            return _entries.TryGetValue(id, out var entry) ? entry.State : null;
        }
    }

    public bool HasOpenClarify(string? sessionId)
    {
        lock (_gate)
        {
            if (string.IsNullOrEmpty(sessionId))
            {
                return false;
            }

            foreach (var entry in _entries.Values)
            {
                if (entry.State == Lifecycle.Open && entry.Method == MethodClarify && entry.SessionId == sessionId)
                {
                    return true;
                }
            }

            return false;
        }
    }

    public string? NewestOpenClarify(string? sessionId)
    {
        lock (_gate)
        {
            if (string.IsNullOrEmpty(sessionId))
            {
                return null;
            }

            string? bestId = null;
            var bestSeq = long.MinValue;
            foreach (var entry in _entries.Values)
            {
                if (entry.State != Lifecycle.Open || entry.Method != MethodClarify || entry.SessionId != sessionId)
                {
                    continue;
                }

                if (entry.ReceiptSequence >= bestSeq)
                {
                    bestSeq = entry.ReceiptSequence;
                    bestId = entry.Id;
                }
            }

            return bestId;
        }
    }

    public ClarifyView? TryGetClarifyView(string id)
    {
        lock (_gate)
        {
            return _entries.TryGetValue(id, out var entry) && entry.State == Lifecycle.Open ? entry.Clarify : null;
        }
    }

    public ApprovalView? TryGetApprovalView(string id)
    {
        lock (_gate)
        {
            return _entries.TryGetValue(id, out var entry) && entry.State == Lifecycle.Open ? entry.Approval : null;
        }
    }

    public void AnswerClarify(string id, string text) =>
        _ = ClaimAndSendAsync(id, new Dictionary<string, object?> { [FieldAnswer] = text }, answerLen: text.Length, choice: null);

    public void AnswerClarifyMulti(string id, IReadOnlyList<string> labels)
    {
        var payload = JsonSerializer.Serialize(labels);
        AnswerClarify(id, payload);
    }

    public void AnswerBatch(string id, IReadOnlyDictionary<string, string> answersByQid) =>
        _ = ClaimAndSendAsync(id, new Dictionary<string, object?> { [FieldAnswers] = answersByQid }, answerLen: answersByQid.Values.Sum(v => v.Length), choice: null);

    public void SkipClarify(string id)
    {
        Dictionary<string, object?> result;
        lock (_gate)
        {
            if (!_entries.TryGetValue(id, out var entry) || entry.State != Lifecycle.Open)
            {
                WriteLog(EventDropped, id, MethodClarify, _currentSessionId ?? "", null, DropReasonNotOpen);
                return;
            }

            result = entry.Clarify?.IsBatch == true
                ? new Dictionary<string, object?>()
                : new Dictionary<string, object?> { [FieldAnswer] = "" };
        }

        _ = ClaimAndSendAsync(id, result, answerLen: 0, choice: null, skipped: true);
    }

    public void ApproveOnce(string id) =>
        _ = ClaimAndSendAsync(id, new Dictionary<string, object?> { [FieldChoice] = ChoiceOnce }, answerLen: null, choice: ChoiceOnce);

    public void Deny(string id) =>
        _ = ClaimAndSendAsync(id, new Dictionary<string, object?> { [FieldChoice] = ChoiceDeny }, answerLen: null, choice: ChoiceDeny);

    public void DeclineUnsupported(string id, string method) =>
        _ = ClaimAndSendErrorAsync(id, method, ErrorMethodNotFound, ErrorNotSupportedMessage);

    private List<Action> AcceptRequestLocked(string id, string method, Dictionary<string, JsonElement> parameters, bool replayed)
    {
        var raises = new List<Action>();
        var sessionId = ReadString(parameters, FieldSessionId) ?? "";
        if (_tombstones.Contains(id) || (_entries.TryGetValue(id, out var existing) && existing.State != Lifecycle.Open))
        {
            WriteLogLocked(EventReplayIgnoredClosed, id, method, sessionId, null, replayed ? "replay" : "duplicate");
            return raises;
        }

        if (_entries.ContainsKey(id))
        {
            WriteLogLocked(EventDropped, id, method, sessionId, null, "already_open");
            return raises;
        }

        WriteLogLocked(EventReceived, id, method, sessionId, null, replayed ? "replayed" : null);
        if (replayed)
        {
            WriteLogLocked(EventReplayed, id, method, sessionId, null, null);
        }

        if (method != MethodClarify && method != MethodApproval)
        {
            var entry = NewEntry(id, sessionId, method, parameters, replayed, null, null);
            entry.State = Lifecycle.Sending;
            _entries[id] = entry;
            raises.Add(() => _ = SendErrorThenCloseAsync(entry, ErrorMethodNotFound, ErrorNotSupportedMessage));
            raises.Add(() => Notice?.Invoke(NoticeUnsupportedPrefix + method));
            return raises;
        }

        if (method == MethodApproval)
        {
            if (!TryBuildApprovalView(parameters, replayed, out var approval))
            {
                var bad = NewEntry(id, sessionId, method, parameters, replayed, null, null);
                bad.State = Lifecycle.Sending;
                _entries[id] = bad;
                raises.Add(() => _ = SendResultThenCloseAsync(bad, new Dictionary<string, object?> { [FieldChoice] = ChoiceDeny }, ChoiceDeny));
                raises.Add(() => Notice?.Invoke(NoticeApprovalUnparseable));
                return raises;
            }

            var approvalEntry = NewEntry(id, sessionId, method, parameters, replayed, null, approval);
            _entries[id] = approvalEntry;
            if (!string.IsNullOrEmpty(_currentSessionId) && sessionId == _currentSessionId)
            {
                WriteLogLocked(EventShown, id, method, sessionId, null, null);
                raises.Add(() => ApprovalOpened?.Invoke(id, approval));
            }
            else
            {
                WriteLogLocked(EventParked, id, method, sessionId, null, "foreign_session");
            }

            return raises;
        }

        var clarify = BuildClarifyView(parameters, replayed);
        var clarifyEntry = NewEntry(id, sessionId, method, parameters, replayed, clarify, null);
        _entries[id] = clarifyEntry;
        if (!string.IsNullOrEmpty(_currentSessionId) && sessionId == _currentSessionId)
        {
            WriteLogLocked(EventShown, id, method, sessionId, null, null);
            raises.Add(() => ClarifyOpened?.Invoke(id, clarify));
        }
        else
        {
            WriteLogLocked(EventParked, id, method, sessionId, null, "foreign_session");
        }

        return raises;
    }

    private List<Action> AcceptCancelLocked(string id, string? method, string? reason)
    {
        var raises = new List<Action>();
        if (!_entries.TryGetValue(id, out var entry))
        {
            _tombstones.Add(id);
            WriteLogLocked(EventCancelled, id, method ?? "-", _currentSessionId ?? "", null, reason ?? "unknown_id");
            return raises;
        }

        if (entry.State is Lifecycle.Sending or Lifecycle.Answered or Lifecycle.Declined or Lifecycle.SendFailed or Lifecycle.Cancelled)
        {
            WriteLogLocked(EventDropped, id, entry.Method, entry.SessionId, null, DropReasonAlreadySettled);
            return raises;
        }

        entry.State = Lifecycle.Cancelled;
        _tombstones.Add(id);
        WriteLogLocked(EventCancelled, id, entry.Method, entry.SessionId, null, reason);
        raises.Add(() => RequestClosed?.Invoke(id, CloseOutcome.Cancelled));
        return raises;
    }

    private List<Action> ReconcileOpenRequestsLocked(string sessionId, IReadOnlyList<ChatSocket.OpenRequestSnapshot> snapshots)
    {
        var raises = new List<Action>();
        var present = new HashSet<string>(StringComparer.Ordinal);
        foreach (var snap in snapshots)
        {
            present.Add(snap.Id);
        }

        foreach (var entry in _entries.Values.Where(e => e.SessionId == sessionId && e.State == Lifecycle.Open).ToList())
        {
            if (present.Contains(entry.Id))
            {
                continue;
            }

            // P4-REQUEST: keep entries that arrived on the new socket after replace mark — P4-D11
            if (entry.ReceiptSequence > _replaceMark)
            {
                continue;
            }

            entry.State = Lifecycle.Cancelled;
            _tombstones.Add(entry.Id);
            WriteLogLocked(EventWithdrawnWhileAway, entry.Id, entry.Method, entry.SessionId, null, "absent_from_open_requests");
            raises.Add(() => RequestClosed?.Invoke(entry.Id, CloseOutcome.WithdrawnWhileAway));
            raises.Add(() => Notice?.Invoke(NoticeWithdrawnWhileAway));
        }

        foreach (var snap in snapshots)
        {
            if (_tombstones.Contains(snap.Id))
            {
                WriteLogLocked(EventReplayIgnoredClosed, snap.Id, snap.Method, sessionId, null, "tombstone");
                continue;
            }

            if (_entries.TryGetValue(snap.Id, out var existing))
            {
                if (existing.State == Lifecycle.Open && existing.SessionId == sessionId)
                {
                    WriteLogLocked(EventReshown, snap.Id, snap.Method, sessionId, null, null);
                    if (existing.Clarify is { } clarify)
                    {
                        raises.Add(() => ClarifyOpened?.Invoke(snap.Id, clarify));
                    }
                    else if (existing.Approval is { } approval)
                    {
                        raises.Add(() => ApprovalOpened?.Invoke(snap.Id, approval));
                    }
                }

                continue;
            }

            raises.AddRange(AcceptRequestLocked(snap.Id, snap.Method, snap.Params, replayed: true));
        }

        return raises;
    }

    private Entry NewEntry(
        string id,
        string sessionId,
        string method,
        Dictionary<string, JsonElement> parameters,
        bool replayed,
        ClarifyView? clarify,
        ApprovalView? approval)
    {
        return new Entry
        {
            Id = id,
            SessionId = sessionId,
            Method = method,
            Params = parameters,
            ReceivedAt = DateTimeOffset.Now,
            ReceiptSequence = ++_nextSequence,
            State = Lifecycle.Open,
            Replayed = replayed,
            Clarify = clarify,
            Approval = approval,
        };
    }

    private async Task ClaimAndSendAsync(string id, Dictionary<string, object?> result, int? answerLen, string? choice, bool skipped = false)
    {
        Entry entry;
        lock (_gate)
        {
            if (!_entries.TryGetValue(id, out entry!) || entry.State != Lifecycle.Open)
            {
                WriteLogLocked(EventDropped, id, "-", _currentSessionId ?? "", null, DropReasonNotOpen);
                return;
            }

            // P4-REQUEST: send only while a current session is set and matches the entry — P4-D11
            if (string.IsNullOrEmpty(_currentSessionId))
            {
                WriteLogLocked(EventDropped, id, entry.Method, entry.SessionId, null, DropReasonNoCurrentSession);
                return;
            }

            if (entry.SessionId != _currentSessionId)
            {
                WriteLogLocked(EventDropped, id, entry.Method, entry.SessionId, null, DropReasonForeignSession);
                return;
            }

            entry.State = Lifecycle.Sending;
        }

        try
        {
            await _socket.SendResponseAsync(id, result).ConfigureAwait(false);
            lock (_gate)
            {
                entry.State = Lifecycle.Answered;
                _tombstones.Add(id);
                var textOrLen = choice ?? (skipped ? "skip" : answerLen?.ToString());
                WriteLogLocked(EventAnswered, id, entry.Method, entry.SessionId, textOrLen, choice is null ? null : "choice");
            }

            RequestClosed?.Invoke(id, CloseOutcome.Answered);
        }
        catch (Exception)
        {
            lock (_gate)
            {
                entry.State = Lifecycle.SendFailed;
                _tombstones.Add(id);
                WriteLogLocked(EventSendFailed, id, entry.Method, entry.SessionId, null, "socket");
            }

            RequestClosed?.Invoke(id, CloseOutcome.SendFailed);
        }
    }

    private async Task ClaimAndSendErrorAsync(string id, string method, int code, string message)
    {
        Entry entry;
        lock (_gate)
        {
            if (!_entries.TryGetValue(id, out entry!))
            {
                entry = NewEntry(id, _currentSessionId ?? "", method, new Dictionary<string, JsonElement>(), false, null, null);
                entry.State = Lifecycle.Sending;
                _entries[id] = entry;
            }
            else if (entry.State != Lifecycle.Open && entry.State != Lifecycle.Sending)
            {
                WriteLogLocked(EventDropped, id, method, entry.SessionId, null, DropReasonNotOpen);
                return;
            }
            else
            {
                entry.State = Lifecycle.Sending;
            }
        }

        await SendErrorThenCloseAsync(entry, code, message).ConfigureAwait(false);
    }

    private async Task SendErrorThenCloseAsync(Entry entry, int code, string message)
    {
        try
        {
            await _socket.SendErrorAsync(entry.Id, code, message).ConfigureAwait(false);
            lock (_gate)
            {
                entry.State = Lifecycle.Declined;
                _tombstones.Add(entry.Id);
                WriteLogLocked(EventDeclined, entry.Id, entry.Method, entry.SessionId, null, message);
            }

            RequestClosed?.Invoke(entry.Id, CloseOutcome.Declined);
        }
        catch (Exception)
        {
            lock (_gate)
            {
                entry.State = Lifecycle.SendFailed;
                _tombstones.Add(entry.Id);
                WriteLogLocked(EventSendFailed, entry.Id, entry.Method, entry.SessionId, null, "socket");
            }

            RequestClosed?.Invoke(entry.Id, CloseOutcome.SendFailed);
        }
    }

    private async Task SendResultThenCloseAsync(Entry entry, Dictionary<string, object?> result, string? choice)
    {
        try
        {
            await _socket.SendResponseAsync(entry.Id, result).ConfigureAwait(false);
            lock (_gate)
            {
                entry.State = Lifecycle.Answered;
                _tombstones.Add(entry.Id);
                WriteLogLocked(EventAnswered, entry.Id, entry.Method, entry.SessionId, choice, "choice");
            }

            RequestClosed?.Invoke(entry.Id, CloseOutcome.Answered);
        }
        catch (Exception)
        {
            lock (_gate)
            {
                entry.State = Lifecycle.SendFailed;
                _tombstones.Add(entry.Id);
                WriteLogLocked(EventSendFailed, entry.Id, entry.Method, entry.SessionId, null, "socket");
            }

            RequestClosed?.Invoke(entry.Id, CloseOutcome.SendFailed);
        }
    }

    private static ClarifyView BuildClarifyView(Dictionary<string, JsonElement> parameters, bool replayed)
    {
        if (parameters.TryGetValue(FieldQuestions, out var questionsEl) && questionsEl.ValueKind == JsonValueKind.Array)
        {
            var prefills = ReadStringMap(parameters, FieldAnswers);
            var list = new List<ClarifyQuestionView>();
            foreach (var item in questionsEl.EnumerateArray())
            {
                if (item.ValueKind != JsonValueKind.Object)
                {
                    continue;
                }

                var qid = ReadString(item, FieldQid) ?? "";
                list.Add(new ClarifyQuestionView
                {
                    Qid = qid,
                    Question = ReadString(item, FieldQuestion) ?? "",
                    Choices = ReadStringList(item, FieldChoices),
                    MultiSelect = ReadBool(item, FieldMultiSelect),
                    PrefillAnswer = prefills.TryGetValue(qid, out var pre) ? pre : "",
                });
            }

            return new ClarifyView
            {
                IsBatch = true,
                Questions = list,
                Replayed = replayed,
            };
        }

        return new ClarifyView
        {
            IsBatch = false,
            Question = ReadString(parameters, FieldQuestion) ?? "",
            Choices = ReadStringList(parameters, FieldChoices),
            MultiSelect = ReadBool(parameters, FieldMultiSelect),
            Replayed = replayed,
        };
    }

    private static bool TryBuildApprovalView(Dictionary<string, JsonElement> parameters, bool replayed, out ApprovalView view)
    {
        // P4-REQUEST: fail-closed when Hermes request_id or command is missing — P4-D07
        var requestId = ReadString(parameters, FieldRequestId);
        var command = ReadString(parameters, FieldCommand);
        view = new ApprovalView
        {
            Command = command ?? "",
            Description = ReadString(parameters, FieldDescription) ?? "",
            Replayed = replayed,
        };
        return !string.IsNullOrEmpty(requestId) && !string.IsNullOrEmpty(command);
    }

    internal static string StripRecommended(string choice)
    {
        var trimmed = choice.Trim();
        if (trimmed.EndsWith(RecommendedLabel, StringComparison.Ordinal))
        {
            return trimmed[..^RecommendedLabel.Length].TrimEnd();
        }

        return trimmed;
    }

    private static void RaiseAll(List<Action> raises)
    {
        foreach (var raise in raises)
        {
            raise();
        }
    }

    private void WriteLog(string eventName, string id, string method, string sessionId, string? textOrLen, string? reason)
    {
        lock (_logGate)
        {
            WriteLogCore(eventName, id, method, sessionId, textOrLen, reason);
        }
    }

    private void WriteLogLocked(string eventName, string id, string method, string sessionId, string? textOrLen, string? reason)
    {
        // Broker state lock may already be held; log uses a separate lock (developer decision).
        lock (_logGate)
        {
            WriteLogCore(eventName, id, method, sessionId, textOrLen, reason);
        }
    }

    private static void WriteLogCore(string eventName, string id, string method, string sessionId, string? textOrLen, string? reason)
    {
        try
        {
            var root = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), LogClientFolder, LogFolder);
            Directory.CreateDirectory(root);
            var line = $"{DateTimeOffset.Now:o} {eventName} id={id} method={method} session_id={sessionId} text_or_len={textOrLen ?? "-"} reason={reason ?? "-"}{Environment.NewLine}";
            File.AppendAllText(Path.Combine(root, LogFileName), line);
        }
        catch
        {
        }
    }

    private static string? ReadString(Dictionary<string, JsonElement> map, string name) =>
        map.TryGetValue(name, out var value) ? ReadString(value) : null;

    private static string? ReadString(JsonElement obj, string name) =>
        obj.ValueKind == JsonValueKind.Object && obj.TryGetProperty(name, out var value) ? ReadString(value) : null;

    private static string? ReadString(JsonElement value) =>
        value.ValueKind == JsonValueKind.String ? value.GetString() : value.ValueKind is JsonValueKind.Null or JsonValueKind.Undefined ? null : value.ToString();

    private static bool ReadBool(Dictionary<string, JsonElement> map, string name) =>
        map.TryGetValue(name, out var value) && value.ValueKind == JsonValueKind.True;

    private static bool ReadBool(JsonElement obj, string name) =>
        obj.ValueKind == JsonValueKind.Object && obj.TryGetProperty(name, out var value) && value.ValueKind == JsonValueKind.True;

    private static IReadOnlyList<string> ReadStringList(Dictionary<string, JsonElement> map, string name) =>
        map.TryGetValue(name, out var value) ? ReadStringList(value) : Array.Empty<string>();

    private static IReadOnlyList<string> ReadStringList(JsonElement obj, string name) =>
        obj.ValueKind == JsonValueKind.Object && obj.TryGetProperty(name, out var value) ? ReadStringList(value) : Array.Empty<string>();

    private static IReadOnlyList<string> ReadStringList(JsonElement value)
    {
        if (value.ValueKind != JsonValueKind.Array)
        {
            return Array.Empty<string>();
        }

        var list = new List<string>();
        foreach (var item in value.EnumerateArray())
        {
            var s = ReadString(item);
            if (!string.IsNullOrEmpty(s))
            {
                list.Add(s);
            }
        }

        return list;
    }

    private static Dictionary<string, string> ReadStringMap(Dictionary<string, JsonElement> map, string name)
    {
        var result = new Dictionary<string, string>(StringComparer.Ordinal);
        if (!map.TryGetValue(name, out var value) || value.ValueKind != JsonValueKind.Object)
        {
            return result;
        }

        foreach (var prop in value.EnumerateObject())
        {
            result[prop.Name] = ReadString(prop.Value) ?? "";
        }

        return result;
    }
}
