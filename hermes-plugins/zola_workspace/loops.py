"""Loop predicate compile and evaluate, and the zola_loops tool (P9-D09)."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

try:
    from . import loop_match
    from . import proactive_store
    from . import read_common
    from . import recorded_results
    from . import taint
    from . import turn_context
    from . import log as wslog
except ImportError:
    import loop_match
    import proactive_store
    import read_common
    import recorded_results
    import taint
    import turn_context
    import log as wslog

# P10-INTAKE: one matcher object for the watcher, the tool, and zola-phone — P10-D12
evaluate = loop_match.evaluate

# P9-STORE: the model does not supply ids; these are the only actions — P9-D09
TOOL_NAME = "zola_loops"
TOOLSET_NAME = "zola_workspace"

# P9-STORE: list is the only source for what she is watching; memory is not — P9-D09
_DESCRIPTION = (
    "What Brian asked you to watch for: list, add, or close. "
    "Not for the mail watcher's health; use workspace_status for that. "
    "When Brian says what are you watching for, what are you keeping an eye on, "
    "what am I waiting on, any open loops, or what did I ask you to watch, call list. "
    "The list result is the only source of what you are watching. "
    "Never answer that question from memory or from the conversation. "
    "If the tool fails, say you could not check. "
    "Pass a handle from a tool result in this conversation. "
    "If Brian's words do not single out one result, ask him which one before you call create. "
    "If several results are live and you pass a handle, the reply names the sender and subject "
    "of that one result. Say those back to Brian before you treat the loop as settled. "
    "Do not pass a message id, thread id, event id, or email address."
)

_FORBIDDEN_KEYS = frozenset(
    {
        "message_id",
        "thread_id",
        "event_id",
        "address",
        "from",
        "email",
        "sender",
        "subject",
    }
)
_ALLOWED_KEYS = frozenset({"action", "handle", "intent", "loop_id"})
_INTENTS = frozenset({"reply", "cancelled", "status_change", "confirm_close"})
_SENT_LABELS = frozenset({"SENT", "DRAFT"})

_listed: Dict[str, set] = {}


def reset_for_tests() -> None:
    _listed.clear()


def _schema() -> Dict[str, Any]:
    return {
        "name": TOOL_NAME,
        "description": _DESCRIPTION,
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["create", "list", "close"]},
                "handle": {"type": "string"},
                "intent": {
                    "type": "string",
                    "enum": ["reply", "cancelled", "status_change", "confirm_close"],
                },
                "loop_id": {"type": "string"},
            },
            "required": ["action"],
            "additionalProperties": False,
        },
    }


def loops_schema() -> Dict[str, Any]:
    return _schema()


def _refuse(reason: str, **extra: Any) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"ok": False, "refused_reason": reason}
    payload.update(extra)
    return payload


def _kind_for(intent: str) -> str:
    if intent == "reply":
        return recorded_results.KIND_GMAIL
    if intent in ("cancelled", "status_change"):
        return recorded_results.KIND_CALENDAR
    return ""


def compile_predicate(intent: str, record: Optional[Dict[str, Any]], *, created_at: str) -> Dict[str, Any]:
    """Pure. Returns {ok, predicate} or a refusal. Does not write a loop."""
    if intent == "confirm_close":
        return {"ok": True, "predicate": {"op": "brian_confirms"}}
    if record is None:
        return _refuse("unknown_handle")
    if intent == "reply":
        labels = {str(item).upper() for item in (record.get("labels") or [])}
        hashes = list(record.get("address_hashes") or [])
        thread_id = str(record.get("thread_id") or "")
        message_id = str(record.get("message_id") or "")
        if labels & _SENT_LABELS:
            # P9-STORE: a message he sent does not name the other party — P9-D09
            return _refuse("sent_only")
        if not thread_id or not hashes or not message_id:
            return _refuse("not_compilable")
        return {
            "ok": True,
            "predicate": {
                "op": "all",
                "args": [
                    {"op": "gmail_thread", "thread_id": thread_id},
                    {"op": "sender_is", "address_hash": hashes[0]},
                    # P9-SPEAK: the message the loop was compiled from is not a reply — P9-D09
                    {"op": "not_source", "message_ids": [message_id]},
                    {"op": "after", "at": created_at},
                ],
            },
        }
    if intent == "cancelled":
        event_id = str(record.get("event_id") or "")
        if not event_id:
            return _refuse("not_compilable")
        return {
            "ok": True,
            "predicate": {
                "op": "all",
                "args": [
                    {"op": "calendar_event", "event_id": event_id},
                    {"op": "calendar_cancelled"},
                    {"op": "after", "at": created_at},
                ],
            },
        }
    if intent == "status_change":
        event_id = str(record.get("event_id") or "")
        status = str(record.get("calendar_status") or "")
        if not event_id or not status:
            return _refuse("not_compilable")
        return {
            "ok": True,
            "predicate": {
                "op": "all",
                "args": [
                    {"op": "calendar_event", "event_id": event_id},
                    {"op": "calendar_status_differs", "from_status": status},
                    {"op": "after", "at": created_at},
                ],
            },
        }
    return _refuse("bad_args")


def _session() -> tuple:
    turn_id = turn_context.current_turn_id_from_context()
    record = turn_context.get_record(turn_id) if turn_id else None
    if record is None:
        return "", ""
    return str(record.session_id or ""), str(record.turn_id or "")


def _untrusted(args: Dict[str, Any]) -> bool:
    if any(key not in _ALLOWED_KEYS for key in args):
        return True
    if any(key in args for key in _FORBIDDEN_KEYS):
        return True
    handle = str(args.get("handle") or "")
    if "@" in handle:
        return True
    return False


def create_loop(conn: Any, args: Dict[str, Any]) -> Dict[str, Any]:
    if not turn_context.is_brian_turn():
        return _refuse("origin")
    if _untrusted(args):
        return _refuse("untrusted_argument")
    intent = str(args.get("intent") or "")
    if intent not in _INTENTS:
        return _refuse("bad_args")
    session_id, turn_id = _session()
    if not session_id:
        return _refuse("origin")
    turn_record = turn_context.get_record(turn_id) if turn_id else None
    user_message = turn_record.user_message if turn_record and isinstance(turn_record.user_message, str) else ""
    record = None
    if intent != "confirm_close":
        kind = _kind_for(intent)
        resolved = recorded_results.resolve(session_id, kind, str(args.get("handle") or ""))
        if not resolved.get("ok"):
            return _refuse(str(resolved.get("refused_reason") or "unknown_handle"), count=resolved.get("count", 0))
        record = resolved["record"]
    from datetime import datetime, timezone

    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    compiled = compile_predicate(intent, record, created_at=created_at)
    if not compiled.get("ok"):
        return compiled
    try:
        try:
            from . import speech
        except ImportError:
            import speech
        source, chosen = speech.provenance(
            session_id,
            "" if record is None else str(record.get("sender_display_name") or ""),
            [] if record is None else list(record.get("address_hashes") or []),
            user_message,
        )
    except Exception:
        source, chosen = "mail", "" if record is None else str(record.get("sender_display_name") or "")
    display_name = chosen if source != "mail" else ("" if record is None else str(record.get("sender_display_name") or ""))
    stored = proactive_store.insert_loop(
        conn,
        intent=intent,
        predicate=compiled["predicate"],
        session_id=session_id,
        sender_display_name=display_name,
        name_source=source,
        subject="" if record is None else str(record.get("subject") or ""),
        source_ids=[]
        if record is None
        else [value for value in (record.get("message_id"), record.get("thread_id"), record.get("event_id")) if value],
        address_hashes=[] if record is None else list(record.get("address_hashes") or []),
    )
    if not stored.get("ok"):
        return stored
    _listed.setdefault(session_id, set()).add(stored["id"])
    watching = {
        "sender_display_name": "" if record is None else str(record.get("sender_display_name") or ""),
        "subject": "" if record is None else str(record.get("subject") or ""),
    }
    return {
        "ok": True,
        "loop_id": stored["id"],
        "intent": intent,
        "operators": _operator_names(compiled["predicate"]),
        "watching": watching,
    }


def _operator_names(predicate: Dict[str, Any]) -> List[str]:
    names = [str(predicate.get("op") or "")]
    for child in predicate.get("args") or []:
        if isinstance(child, dict):
            names.extend(_operator_names(child))
    return [name for name in names if name and name not in ("all", "any")]


def list_loops(conn: Any) -> Dict[str, Any]:
    if not turn_context.is_brian_turn():
        return _refuse("origin")
    session_id, _turn_id = _session()
    if not session_id:
        return _refuse("origin")
    listed = proactive_store.list_open_loops(conn)
    if not listed.get("ok"):
        return listed
    _listed[session_id] = {row["id"] for row in listed["loops"]}
    return listed


def close_listed(conn: Any, args: Dict[str, Any]) -> Dict[str, Any]:
    if not turn_context.is_brian_turn():
        return _refuse("origin")
    if _untrusted(args):
        return _refuse("untrusted_argument")
    session_id, _turn_id = _session()
    loop_id = str(args.get("loop_id") or "")
    if not session_id or not loop_id or loop_id not in _listed.get(session_id, set()):
        return _refuse("unknown_loop")
    intent = str(args.get("intent") or "")
    closed_intent = intent if intent in _INTENTS else None
    return proactive_store.close_loop(conn, loop_id, closed_intent=closed_intent)


def _watching_has_text(result: Dict[str, Any]) -> bool:
    watching = result.get("watching") or {}
    if not isinstance(watching, dict):
        return False
    return bool(
        str(watching.get("sender_display_name") or "").strip()
        or str(watching.get("subject") or "").strip()
    )


def _present(action: str, result: Dict[str, Any]) -> str:
    """Frame mail text the way a Gmail read does, and taint the session first."""
    if not result.get("ok"):
        return json.dumps(result, ensure_ascii=False)
    if action == "list":
        # P9-STORE: sender and subject came from mail, so the list is untrusted content — P9-D09
        return read_common.mark_then_frame(
            TOOL_NAME,
            result,
            empty_key="loops",
            log_event=wslog.LOG_EVENT_LOOPS,
            log_fields={"state": "complete", "count": len(result.get("loops") or [])},
        )
    if action == "create" and _watching_has_text(result):
        session_id, task_id = read_common._ids_for_turn()
        # P9-STORE: a create echo taints only when this session has not already read mail — P9-D09
        if not taint.is_tainted(session_id, task_id or None):
            return read_common.mark_then_frame(
                TOOL_NAME,
                result,
                empty_key="watching",
                log_event=wslog.LOG_EVENT_LOOPS,
                log_fields={"state": "complete", "count": 1},
            )
        return read_common.dump_result(TOOL_NAME, result)
    return json.dumps(result, ensure_ascii=False)


def loops_handler(args: dict, **kwargs: Any) -> str:
    """Ticket-checked create, list, and close. Never raises."""
    try:
        payload = args if isinstance(args, dict) else {}
        action = str(payload.get("action") or "")
        path = proactive_store.profile_db_path()
        if path is None:
            return json.dumps(_refuse("missing"), ensure_ascii=False)
        conn = proactive_store.connect(path)
        try:
            if action == "create":
                result = create_loop(conn, payload)
            elif action == "list":
                result = list_loops(conn)
            elif action == "close":
                result = close_listed(conn, payload)
            else:
                result = _refuse("bad_args")
        finally:
            conn.close()
        return _present(action, result)
    except Exception:
        return json.dumps(_refuse("error"), ensure_ascii=False)
