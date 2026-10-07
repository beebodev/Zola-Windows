"""Per-turn context store — keyed only by turn_id (P8-D02 / HD-G1)."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

# P8-HARDEN: authority TTL; missing/expired = not authorized — P8-D02
AUTHORITY_GRANT_TTL_SECONDS = 900

PLATFORM_TUI = "tui"

# P8-HARDEN: records keyed by turn_id only — no per-session "latest" pointer — P8-D02
_records_by_turn_id: Dict[str, "TurnRecord"] = {}


@dataclass(frozen=True)
class TurnRecord:
    turn_id: str
    task_id: str
    session_id: str
    platform: str
    parent_session_id: str
    user_message: str  # in memory only — never logged or persisted
    created_at: float


def clear_all_for_tests() -> None:
    """Drop all authority records (simulates restart / fresh module)."""
    _records_by_turn_id.clear()


def _prune_expired(now: Optional[float] = None) -> None:
    """Remove expired authority records so the store stays bounded."""
    # P8-HARDEN: prune on insert — P8-D02
    clock = time.monotonic() if now is None else now
    expired = [
        key
        for key, rec in _records_by_turn_id.items()
        if (clock - rec.created_at) > AUTHORITY_GRANT_TTL_SECONDS
    ]
    for key in expired:
        _records_by_turn_id.pop(key, None)


def record_pre_llm_call(
    *,
    turn_id: str,
    task_id: str = "",
    session_id: str = "",
    platform: str = "",
    parent_session_id: str = "",
    user_message: str = "",
) -> None:
    """Store this turn's record. Keyed only by turn_id. Prunes expired entries first."""
    # P8-HARDEN: turn_id is the sole join key (TUI task_id == session_key) — P8-D02
    tid = str(turn_id or "")
    now = time.monotonic()
    _prune_expired(now)
    if not tid:
        return
    _records_by_turn_id[tid] = TurnRecord(
        turn_id=tid,
        task_id=str(task_id or ""),
        session_id=str(session_id or ""),
        platform=str(platform or ""),
        parent_session_id=str(parent_session_id or ""),
        user_message=user_message if isinstance(user_message, str) else "",
        created_at=now,
    )


def get_record(turn_id: str) -> Optional[TurnRecord]:
    """Return the record for turn_id if present and not expired; else None."""
    tid = str(turn_id or "")
    if not tid:
        return None
    rec = _records_by_turn_id.get(tid)
    if rec is None:
        return None
    if (time.monotonic() - rec.created_at) > AUTHORITY_GRANT_TTL_SECONDS:
        # P8-HARDEN: expiry only removes authority — P8-D02
        _records_by_turn_id.pop(tid, None)
        return None
    return rec


def current_turn_id_from_context() -> str:
    """Read the Hermes observability ContextVar bound around tool dispatch."""
    try:
        from tools.approval_context import _approval_turn_id

        return str(_approval_turn_id.get() or "")
    except Exception:
        return ""


def is_brian_turn(turn_id: Optional[str] = None) -> bool:
    """True only for this exact turn_id, platform tui, empty parent, unexpired.

    Missing, stale, mismatched, or absent key → False. No session/latest fallback.
    """
    # P8-HARDEN: "this turn" means the approved turn_id correlation only — P8-D02
    tid = str(turn_id or "") if turn_id is not None else current_turn_id_from_context()
    if not tid:
        return False
    rec = get_record(tid)
    if rec is None:
        return False
    if (rec.platform or "").lower() != PLATFORM_TUI:
        return False
    if rec.parent_session_id:
        return False
    return True


def pre_llm_call_hook(**kwargs: Any) -> None:
    """Hermes pre_llm_call: store turn context for later Brian-only checks."""
    try:
        record_pre_llm_call(
            turn_id=str(kwargs.get("turn_id") or ""),
            task_id=str(kwargs.get("task_id") or ""),
            session_id=str(kwargs.get("session_id") or ""),
            platform=str(kwargs.get("platform") or ""),
            parent_session_id=str(kwargs.get("parent_session_id") or ""),
            user_message=kwargs.get("user_message") if isinstance(kwargs.get("user_message"), str) else "",
        )
    except Exception:
        pass
    return None
