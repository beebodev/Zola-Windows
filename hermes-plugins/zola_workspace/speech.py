"""Unprompted speech gateway. The client decides; this module does not speak."""

from __future__ import annotations

import hashlib
import json
import re
import threading
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

try:
    from . import log as wslog
    from . import proactive_store
    from . import ranker
    from . import recorded_results
    from . import send_gate
except ImportError:
    import log as wslog
    import proactive_store
    import ranker
    import recorded_results
    import send_gate

# P9-SPEAK: named bounds from the Phase 3 verdicts — P9-D11
SPEECH_IDLE_SECONDS = 20
SPEECH_POLL_SECONDS = 20
SPEECH_SNAPSHOT_TIMEOUT_SECONDS = 2
SPEECH_START_TIMEOUT_SECONDS = 15
SPEECH_COMPLETE_TIMEOUT_SECONDS = 60
SPEECH_ECHO_TAIL_SECONDS = 2
SPEECH_LOCK_HOLD_MS = 50
SPEECH_NAME_CAP = 40
QUIET_START_HOUR = 22
QUIET_END_HOUR = 7

GMAIL_NAMED = (
    "Brian, {name} got back to you.",
    "Heads up, {name} replied.",
    "{name} wrote back, Brian.",
    "You've got a reply from {name}.",
    "Quick one: {name} answered.",
)
GMAIL_UNNAMED = (
    "Brian, the reply you were waiting for just came in.",
    "Heads up, you've got the reply you were watching for.",
    "That email you were waiting on, they wrote back.",
)
CALENDAR_LINES = (
    "Brian, something you asked me to watch on your calendar just changed.",
    "Heads up, one of the events you asked me to watch was updated.",
)

_NAME = re.compile(r"^[A-Za-z](?:[A-Za-z' -]{0,38}[A-Za-z])?$")
_speak_enabled: Optional[bool] = None
_deliver_lock = threading.Lock()
_last_deliver: Optional[Tuple[str, str]] = None


def set_speak_enabled_for_tests(value: Optional[bool]) -> None:
    global _speak_enabled
    _speak_enabled = value


def speak_enabled() -> bool:
    # P9-SPEAK: missing or any value other than true stays off — P9-D11
    if _speak_enabled is not None:
        return bool(_speak_enabled)
    try:
        from hermes_cli.config import load_config_readonly
    except Exception:
        return False
    try:
        cfg = load_config_readonly() or {}
    except Exception:
        return False
    block = cfg.get("proactive") if isinstance(cfg, dict) else None
    if not isinstance(block, dict):
        return False
    return block.get("speak_enabled") is True


def sanitize_name(value: str) -> str:
    # P9-SPEAK: letters, spaces, apostrophe, hyphen; the word someone is the fallback set — P9-D11
    raw = str(value or "")
    if any(not (ch.isalpha() or ch in " '-") for ch in raw):
        return ""
    text = " ".join(raw.split())
    if not text or len(text) > SPEECH_NAME_CAP or text.casefold() == "someone":
        return ""
    if not _NAME.match(text):
        return ""
    return text


def _verbatim(name: str, message: str) -> bool:
    cleaned = name.strip()
    if len(cleaned) < 2 or not message:
        return False
    pattern = re.compile(r"(?<![A-Za-z])" + re.escape(cleaned) + r"(?![A-Za-z])", re.IGNORECASE)
    return pattern.search(message) is not None


def provenance(
    session_id: str,
    from_name: str,
    address_hashes: Any,
    user_message: str,
) -> Tuple[str, str]:
    """Code sets the source. A model argument is not a name Brian supplied."""
    hashes = {str(item) for item in (address_hashes or []) if item}
    contact_name = ""
    for row in recorded_results.live_records(session_id, recorded_results.KIND_CONTACT):
        if hashes and hashes.intersection(row.get("address_hashes") or []):
            contact_name = str(row.get("sender_display_name") or "")
            break
    if contact_name and _verbatim(contact_name, user_message) and sanitize_name(contact_name):
        return "brian_message", sanitize_name(contact_name)
    if from_name and _verbatim(from_name, user_message) and sanitize_name(from_name):
        return "brian_message", sanitize_name(from_name)
    if contact_name and sanitize_name(contact_name):
        return "contacts_ticket", sanitize_name(contact_name)
    return "mail", from_name


def _hash(attempt_id: str) -> str:
    return hashlib.sha256(str(attempt_id).encode("utf-8")).hexdigest()[:16]


def reset_deliver_log_for_tests() -> None:
    global _last_deliver
    with _deliver_lock:
        _last_deliver = None


def _log(outcome: str, *, attempt_id: str = "", reason: str = "", name_source: str = "") -> None:
    # P9-SPEAK: a repeated deny is one line. A new reason is logged at once. Idle is one line — P9-D11
    global _last_deliver
    shown = outcome
    shown_reason = reason or "-"
    if outcome == "deny" and shown_reason == "nothing_speakable":
        shown = "idle"
    try:
        with _deliver_lock:
            if shown in ("deny", "idle", "error"):
                key = (shown, shown_reason)
                if key == _last_deliver:
                    return
                _last_deliver = key
            else:
                _last_deliver = None
        wslog.write_event(
            wslog.LOG_EVENT_SPEAK,
            attempt=_hash(attempt_id) if attempt_id else "-",
            outcome=shown,
            reason=shown_reason,
            phrase="-",
            name_source=name_source or "-",
        )
    except Exception:
        pass


def _connect():
    path = proactive_store.profile_db_path()
    if path is None or not path.exists():
        return None
    return proactive_store.connect(path, retry=False)


def _sender_hashes(node: Any) -> set:
    found: set = set()
    if not isinstance(node, dict):
        return found
    if node.get("op") == "sender_is":
        digest = str(node.get("address_hash") or "")
        if digest:
            found.add(digest)
    for child in node.get("args") or []:
        found.update(_sender_hashes(child))
    return found


def _name_for_item(conn, item_id: str) -> Tuple[str, str]:
    # The store does not record which loop matched. The spoken name is the loop
    # whose sender_is hash equals this item's sender hash.
    item = proactive_store._item(conn, item_id)
    if item is None:
        return "someone", ""
    sender = str(item["sender_address_hash"] or "")
    if not sender:
        return "someone", ""
    chosen = ("someone", "")
    for loop in conn.execute(
        "SELECT status, sender_display_name, name_source, predicate_json FROM loops"
    ):
        try:
            predicate = json.loads(loop["predicate_json"] or "{}")
        except json.JSONDecodeError:
            continue
        if sender not in _sender_hashes(predicate):
            continue
        source = str(loop["name_source"] or "mail")
        if source == "mail":
            continue
        cleaned = sanitize_name(str(loop["sender_display_name"] or ""))
        if not cleaned:
            continue
        if loop["status"] == "open":
            return source, cleaned
        chosen = (source, cleaned)
    return chosen


def snapshot_for_client(params: Optional[dict] = None) -> Dict[str, Any]:
    # P9-SPEAK: the poll is read-only. Recovery runs in claim and in the surface note — P9-D11
    if params is not None and not isinstance(params, dict):
        return {"ok": False, "reason": "bad_args"}
    return {
        "ok": True,
        "turn_in_flight": bool(ranker.turn_in_flight()),
        "reviewed_draft": bool(send_gate.has_reviewed_draft()),
        "server_time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def claim_for_client(params: Optional[dict] = None) -> Dict[str, Any]:
    if params is not None and not isinstance(params, dict):
        return {"ok": False, "reason": "bad_args"}
    if not speak_enabled():
        _log("deny", reason="speak_disabled")
        return {"ok": False, "reason": "speak_disabled"}
    if isinstance(params, dict) and "item_id" in params:
        return {"ok": False, "reason": "bad_args"}
    conn = _connect()
    if conn is None:
        _log("deny", reason="no_store")
        return {"ok": False, "reason": "no_store"}
    try:
        claimed = proactive_store.claim_next_speech(conn)
        if not claimed.get("ok"):
            reason = str(claimed.get("refused_reason") or "illegal_transition")
            _log("deny", reason=reason)
            return {"ok": False, "reason": reason}
        item_id = str(claimed.get("item_id") or "")
        attempt_id = str(claimed.get("attempt_id") or "")
        try:
            name_source, name = _name_for_item(conn, item_id)
        except Exception as exc:
            proactive_store.release_speech_claim(conn, item_id, attempt_id)
            _log("error", attempt_id=attempt_id, reason=type(exc).__name__)
            return {"ok": False, "reason": "error"}
        _log("claimed", attempt_id=attempt_id, name_source=name_source if name else "someone")
        return {
            "ok": True,
            "item_id": item_id,
            "attempt_id": attempt_id,
            "name": name,
            "name_source": name_source if name else "someone",
            "source": str(claimed.get("source") or ""),
        }
    finally:
        conn.close()


def speech_started_for_client(params: Optional[dict] = None) -> Dict[str, Any]:
    return _attempt_call(params, "speech_started")


def outcome_for_client(params: Optional[dict] = None) -> Dict[str, Any]:
    if not isinstance(params, dict):
        return {"ok": False, "reason": "bad_args"}
    outcome = params.get("outcome")
    if outcome not in ("delivered", "delivery_uncertain"):
        return {"ok": False, "reason": "bad_args"}
    return _attempt_call(params, outcome)


def release_for_client(params: Optional[dict] = None) -> Dict[str, Any]:
    return _attempt_call(params, "release")


def watcher_health_for_client(params: Optional[dict] = None) -> Dict[str, Any]:
    if params is not None and not isinstance(params, dict):
        return {"ok": False, "reason": "bad_args"}
    conn = _connect()
    if conn is None:
        return {"ok": True, "row": None}
    try:
        health = proactive_store.read_watcher_health(conn)
        if not health.get("ok"):
            return {"ok": False, "reason": health.get("refused_reason") or "error"}
        google_connected, ranker_state, ranker_progress_at = _systems_fields(conn)
        row = health.get("row") or None
        body = {
            "ok": True,
            "row": None,
            "google_connected": google_connected,
            "ranker_state": ranker_state,
            "ranker_progress_at": ranker_progress_at,
        }
        if row is None:
            return body
        allowed = (
            "gmail_ok_at",
            "calendar_ok_at",
            "gmail_error",
            "calendar_error",
            "needs_reconnect",
            "last_ok_at",
            "error_class",
            "updated_at",
        )
        body["row"] = {key: row.get(key) for key in allowed}
        return body
    finally:
        conn.close()


def _systems_fields(conn) -> Tuple[Optional[bool], Optional[str], Optional[str]]:
    # P9-SPEAK: read-only. connected is a bool. The token and the reconnect reason stay out — P9-D12
    google_connected = None
    try:
        try:
            from . import auth
        except ImportError:
            import auth
        status = auth.store_status()
        if isinstance(status, dict) and "connected" in status:
            google_connected = bool(status.get("connected"))
    except Exception:
        google_connected = None
    ranker_state = None
    ranker_progress_at = None
    try:
        found = {
            key: value
            for key, value in conn.execute(
                "SELECT key, value FROM meta WHERE key IN ('ranker_state', 'ranker_progress_at')"
            ).fetchall()
        }
        ranker_state = found.get("ranker_state") or None
        ranker_progress_at = found.get("ranker_progress_at") or None
    except Exception:
        ranker_state = None
        ranker_progress_at = None
    return google_connected, ranker_state, ranker_progress_at


def recover_for_client(params: Optional[dict] = None) -> Dict[str, Any]:
    # P9-SPEAK: startup recovery is not a claim and does not list items — P9-D11
    if params is not None and not isinstance(params, dict):
        _log("deny", reason="bad_args")
        return {"ok": False, "reason": "bad_args"}
    conn = _connect()
    if conn is None:
        _log("deny", reason="no_store")
        return {"ok": False, "reason": "no_store"}
    try:
        recovered = proactive_store.release_speech_lease(conn)
        if not recovered.get("ok"):
            reason = str(recovered.get("refused_reason") or "error")
            _log("deny", reason=reason)
            return {"ok": False, "reason": reason}
        return {"ok": True}
    finally:
        conn.close()


def _attempt_call(params: Optional[dict], kind: str) -> Dict[str, Any]:
    if not isinstance(params, dict) or not isinstance(params.get("attempt_id"), str) or not params.get("attempt_id"):
        return {"ok": False, "reason": "bad_args"}
    if not isinstance(params.get("item_id"), str) or not params.get("item_id"):
        return {"ok": False, "reason": "bad_args"}
    conn = _connect()
    if conn is None:
        return {"ok": False, "reason": "no_store"}
    try:
        item_id = params["item_id"]
        attempt_id = params["attempt_id"]
        if kind == "speech_started":
            result = proactive_store.mark_speech_started(conn, item_id, attempt_id)
        elif kind == "delivered":
            result = proactive_store.mark_delivered(conn, item_id, attempt_id)
        elif kind == "delivery_uncertain":
            result = proactive_store.mark_delivery_uncertain(conn, item_id, attempt_id)
        else:
            result = proactive_store.release_speech_claim(conn, item_id, attempt_id)
        if not result.get("ok"):
            reason = str(result.get("refused_reason") or "illegal_transition")
            _log("deny", attempt_id=attempt_id, reason=reason)
            return {"ok": False, "reason": reason}
        outcome = "released" if kind == "release" else kind
        if kind == "delivered":
            outcome = "delivered"
        elif kind == "delivery_uncertain":
            outcome = "uncertain"
        _log(outcome, attempt_id=attempt_id)
        return {"ok": True, "attempt_id": attempt_id}
    finally:
        conn.close()


def _rpc_ok(rid: Any, result: Dict[str, Any]) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": rid, "result": result}


def _rpc_err(rid: Any, reason: str) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": 4030, "message": reason}}


def _wrap(fn):
    def method(rid: Any, params: Any = None) -> Dict[str, Any]:
        try:
            body = fn(params if isinstance(params, dict) else None)
        except Exception as exc:
            _log("error", reason=type(exc).__name__)
            return _rpc_err(rid, "error")
        if not body.get("ok"):
            return _rpc_err(rid, str(body.get("reason") or "error"))
        result = {key: value for key, value in body.items() if key != "ok"}
        return _rpc_ok(rid, result)

    return method


def install_methods() -> bool:
    # P9-SPEAK: same serve-only install as the prompt.submit wrap. No Hermes edit — P9-D11
    try:
        try:
            from . import origin
        except ImportError:
            import origin
        if not origin.in_serve_process():
            return False
        import tui_gateway.server as server
    except Exception:
        return False
    server._methods["proactive.snapshot"] = _wrap(snapshot_for_client)
    server._methods["proactive.recover"] = _wrap(recover_for_client)
    server._methods["proactive.claim"] = _wrap(claim_for_client)
    server._methods["proactive.speech_started"] = _wrap(speech_started_for_client)
    server._methods["proactive.outcome"] = _wrap(outcome_for_client)
    server._methods["proactive.release"] = _wrap(release_for_client)
    server._methods["proactive.watcher_health"] = _wrap(watcher_health_for_client)
    return True
