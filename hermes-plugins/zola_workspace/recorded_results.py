"""Opaque handles for tool results this process recorded (P9-D09).

The handle proves an id was in a result. It does not prove Brian meant that result.
"""

from __future__ import annotations

import hashlib
import time
import uuid
from typing import Any, Dict, List, Optional

# P9-STORE: named bounds from the locked proposal — P9-D09
HANDLE_TTL_SECONDS = 1800
RECORDED_RESULTS_CAP = 64

KIND_GMAIL = "gmail_message"
KIND_CALENDAR = "calendar_event"
KIND_CONTACT = "contact"

_rows: Dict[str, Dict[str, Any]] = {}
_clock: Optional[Any] = None


def set_clock_for_tests(fn: Optional[Any]) -> None:
    global _clock
    _clock = fn


def reset_for_tests() -> None:
    _rows.clear()
    set_clock_for_tests(None)


def _now() -> float:
    if _clock is not None:
        return float(_clock())
    return time.monotonic()


def _turn_ids() -> tuple:
    try:
        try:
            from . import turn_context
        except ImportError:
            import turn_context
        turn_id = turn_context.current_turn_id_from_context()
        record = turn_context.get_record(turn_id) if turn_id else None
        if record is None:
            return "", ""
        return str(record.session_id or ""), str(record.turn_id or "")
    except Exception:
        return "", ""


def _hash(value: str) -> str:
    try:
        try:
            from . import proactive_store
        except ImportError:
            import proactive_store
        return proactive_store.address_hash(value)
    except Exception:
        return hashlib.sha256(value.strip().casefold().encode("utf-8")).hexdigest()


def _prune(now: float) -> None:
    stale = [key for key, row in _rows.items() if now - float(row["created_at"]) > HANDLE_TTL_SECONDS]
    for key in stale:
        _rows.pop(key, None)
    overflow = len(_rows) - RECORDED_RESULTS_CAP
    if overflow <= 0:
        return
    oldest = sorted(_rows.items(), key=lambda item: float(item[1]["created_at"]))[:overflow]
    for key, _row in oldest:
        _rows.pop(key, None)


def remember(
    *,
    kind: str,
    message_id: str = "",
    thread_id: str = "",
    event_id: str = "",
    event_updated: str = "",
    address: str = "",
    addresses: Optional[List[str]] = None,
    sender_display_name: str = "",
    subject: str = "",
    labels: Optional[List[str]] = None,
    calendar_status: str = "",
    session_id: str = "",
    turn_id: str = "",
) -> str:
    # P9-STORE: the model sees a handle, not a trusted copy of an id it typed — P9-D09
    if not session_id or not turn_id:
        session_id, turn_id = _turn_ids()
    if not session_id or not turn_id:
        return ""
    now = _now()
    _prune(now)
    hashes = []
    if address:
        hashes.append(_hash(address))
    for value in addresses or []:
        if value:
            hashes.append(_hash(value))
    handle = uuid.uuid4().hex
    _rows[handle] = {
        "handle": handle,
        "kind": kind,
        "session_id": session_id,
        "turn_id": turn_id,
        "message_id": message_id,
        "thread_id": thread_id,
        "event_id": event_id,
        "event_updated": event_updated,
        "address_hashes": hashes,
        "sender_display_name": sender_display_name,
        "subject": subject,
        "labels": list(labels or []),
        "calendar_status": calendar_status,
        "created_at": now,
    }
    _prune(now)
    return handle


def _live(session_id: str, kind: str) -> List[Dict[str, Any]]:
    now = _now()
    _prune(now)
    return [
        row
        for row in _rows.values()
        if row["session_id"] == session_id and row["kind"] == kind and now - float(row["created_at"]) <= HANDLE_TTL_SECONDS
    ]


def live_records(session_id: str, kind: str) -> List[Dict[str, Any]]:
    # P9-SPEAK: a contact recorded this process, not a name the model typed — P9-D11
    return [dict(row) for row in _live(session_id, kind)]


def resolve(session_id: str, kind: str, handle: str = "") -> Dict[str, Any]:
    """One live candidate, or an explicit handle. Several and no handle is ambiguous."""
    if handle:
        row = _rows.get(handle)
        now = _now()
        if (
            row is None
            or row["session_id"] != session_id
            or row["kind"] != kind
            or now - float(row["created_at"]) > HANDLE_TTL_SECONDS
        ):
            return {"ok": False, "refused_reason": "unknown_handle"}
        return {"ok": True, "record": row, "count": len(_live(session_id, kind))}
    matches = _live(session_id, kind)
    if len(matches) == 1:
        return {"ok": True, "record": matches[0], "count": 1}
    if not matches:
        return {"ok": False, "refused_reason": "unknown_handle"}
    return {"ok": False, "refused_reason": "ambiguous", "count": len(matches)}


def clear_session(session_id: str) -> None:
    for key, row in list(_rows.items()):
        if row["session_id"] == session_id:
            _rows.pop(key, None)
