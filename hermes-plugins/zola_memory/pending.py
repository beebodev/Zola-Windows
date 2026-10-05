"""Pending-turn queue writer for episode consolidation (P6-D04)."""

from __future__ import annotations

import hashlib
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

try:
    from . import forget
    from . import log as memlog
    from . import time_context
except ImportError:  # P6-EPISODES: flat unittest discover top — P6-D04
    import forget
    import log as memlog
    import time_context


def new_pending_id() -> str:
    return str(uuid.uuid4())


def turn_fingerprint(user_text: str, assistant_text: str) -> str:
    raw = f"{user_text or ''}\0{assistant_text or ''}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _iso_now() -> str:
    return time_context.marker_iso(time_context.capture_now())


def _message_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text") or ""))
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(parts)
    return str(content or "")


# P6-EPISODES: unix floats above this are treated as epoch seconds (not years) — P6-D04
_UNIX_SECONDS_FLOOR = 1_000_000_000  # ~2001-09-09


def normalize_message_timestamp(ts: Any) -> Optional[str]:
    """Hermes message timestamp → ISO-8601 local-with-offset (Track 3 localize).

    Accepts ``datetime``, unix ``int``/``float`` (or numeric string), or ISO string.
    Unparseable → ``None`` (X4).
    """
    if ts is None:
        return None
    dt: Optional[datetime] = None
    if isinstance(ts, datetime):
        dt = ts
    elif isinstance(ts, bool):
        return None
    elif isinstance(ts, (int, float)):
        try:
            dt = datetime.fromtimestamp(float(ts), tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    elif isinstance(ts, str):
        text = ts.strip()
        if not text:
            return None
        try:
            as_float = float(text)
        except ValueError:
            as_float = None
        if as_float is not None and as_float >= _UNIX_SECONDS_FLOOR:
            try:
                dt = datetime.fromtimestamp(as_float, tz=timezone.utc)
            except (OverflowError, OSError, ValueError):
                return None
        if dt is None:
            try:
                iso = text
                if iso.endswith("Z"):
                    iso = iso[:-1] + "+00:00"
                dt = datetime.fromisoformat(iso)
            except ValueError:
                return None
    else:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return time_context.marker_iso(time_context.localize_marker(dt))


def resolve_user_time(
    messages: Optional[List[Dict[str, Any]]],
    user_content: str = "",
) -> Optional[str]:
    """ISO timestamp from the persisted user message matching this turn's content.

    Match uses Track 4 normalization + containment (exact key, or message key
    contained in redirect-augmented sync content). Prefer the latest match.
    No match → None (X4 write with NULL). Timestamps are normalized at the
    source (unix float/int, ISO string, or datetime → local ISO with offset).

    Note: ``sync_turn``'s ``messages`` is a **live list** reference from the
    agent transcript (not a snapshot) — see ``turn_finalizer.py`` L604–606
    passing ``messages=messages`` into async ``sync_all`` — so the last user
    row may already belong to a later turn; content match is required.
    """
    if not messages:
        return None
    sync_key = forget.normalize_disposition_key(user_content or "")
    if not sync_key:
        return None
    for msg in reversed(messages):
        if not isinstance(msg, dict):
            continue
        if str(msg.get("role") or "").lower() != "user":
            continue
        msg_key = forget.normalize_disposition_key(_message_text(msg.get("content")))
        if not msg_key:
            continue
        # Exact, or message original contained in redirect-augmented sync (Track 4)
        if msg_key == sync_key or msg_key in sync_key:
            return normalize_message_timestamp(msg.get("timestamp"))
    return None


def resolve_assistant_time(
    messages: Optional[List[Dict[str, Any]]],
) -> Optional[str]:
    """Normalized assistant timestamp, or ``None`` if unparseable (X4).

    When no assistant message / no timestamp is present, fall back to now so
    ordering still has a value; a present-but-unparseable timestamp → NULL.
    """
    if messages:
        for msg in reversed(messages):
            if not isinstance(msg, dict):
                continue
            if str(msg.get("role") or "").lower() != "assistant":
                continue
            if "timestamp" not in msg or msg.get("timestamp") is None:
                break
            return normalize_message_timestamp(msg.get("timestamp"))
    return _iso_now()


def write_pending(
    conn: sqlite3.Connection,
    *,
    session_id: str,
    turn_index: int,
    user_text: str,
    assistant_text: str,
    user_time: Optional[str],
    assistant_time: Optional[str],
    disposition: str,
) -> Optional[str]:
    """Insert one pending row when disposition is keep. Returns pending id or None."""
    if disposition != "keep":
        return None
    sid = session_id or ""
    if not sid:
        return None
    fp = turn_fingerprint(user_text or "", assistant_text or "")
    pid = new_pending_id()
    gen = forget.get_consolidation_generation(conn)
    created = _iso_now()
    missing_user_time = 1 if not user_time else 0
    try:
        cur = conn.execute(
            "INSERT OR IGNORE INTO pending_turns ("
            "  id, session_id, turn_index, user_text, assistant_text,"
            "  user_time, assistant_time, consolidation_generation,"
            "  forget_hold, created_at, turn_fingerprint"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)",
            (
                pid,
                sid,
                int(turn_index),
                user_text or "",
                assistant_text or "",
                user_time,
                assistant_time,
                gen,
                created,
                fp,
            ),
        )
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        memlog.write_event(
            memlog.LOG_EVENT_PENDING_WRITE,
            session_id=sid or "-",
            pending_id="-",
            turn_index=turn_index,
            ok=False,
        )
        return None
    if cur.rowcount == 0:
        # Duplicate fingerprint for this session/user_time — already queued
        memlog.write_event(
            memlog.LOG_EVENT_PENDING_WRITE,
            session_id=sid or "-",
            pending_id="dup",
            turn_index=turn_index,
            ok=True,
        )
        return None
    if missing_user_time:
        memlog.write_event(
            memlog.LOG_EVENT_PENDING_MISSING_USER_TIME,
            session_id=sid or "-",
            count=1,
        )
    memlog.write_event(
        memlog.LOG_EVENT_PENDING_WRITE,
        session_id=sid or "-",
        pending_id=pid,
        turn_index=turn_index,
        ok=True,
    )
    return pid


def list_pending_ordered(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    return list(
        conn.execute(
            "SELECT * FROM pending_turns "
            "ORDER BY user_time IS NULL, user_time, created_at, id"
        )
    )


def count_pending(conn: sqlite3.Connection) -> int:
    return int(conn.execute("SELECT COUNT(*) FROM pending_turns").fetchone()[0])
