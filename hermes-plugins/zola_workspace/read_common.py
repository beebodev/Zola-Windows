"""Shared gate for the read-only Workspace tools (P8-D07 / P8-D08 / P8-D09)."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Dict, Optional, Tuple

try:
    from . import auth
    from . import framing
    from . import google_http
    from . import log as wslog
    from . import taint
    from . import turn_context
except ImportError:  # P8-READ: flat unittest discover — P8-D07
    import auth
    import framing
    import google_http
    import log as wslog
    import taint
    import turn_context

# P8-READ: same caps as calendar_query — P8-D08
MAX_RESULTS_DEFAULT = 10
MAX_RESULTS_CAP = 25

STATE_COMPLETE = "complete"
STATE_NO_MATCH = "no_match"
STATE_INCOMPLETE = "incomplete"
STATE_UNSUPPORTED = "unsupported_type"
STATE_NEEDS_RECONNECT = "needs_reconnect"
STATE_ERROR = "error"

REASON_NOT_BRIAN = "not_brian_turn"
REASON_TAINT_WRITE_FAILED = "taint_write_failed"
REASON_BAD_ARGS = "bad_args"

# P8-READ: opaque ids are a single path segment, never a URL — P8-D07 / P8-D08
OPAQUE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,256}$")


def valid_opaque_id(value: str) -> bool:
    return bool(OPAQUE_ID_RE.fullmatch(str(value or "")))


def clamp_max_results(raw: Any) -> Optional[int]:
    if raw is None:
        return MAX_RESULTS_DEFAULT
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return None
    if value < 1:
        return 1
    if value > MAX_RESULTS_CAP:
        return MAX_RESULTS_CAP
    return value


def handle_hash(value: str) -> str:
    """Log token for an opaque id. Not reversible in the log line."""
    # P8-READ: hash handles; never log the raw id — P8-D11
    return hashlib.sha256(str(value or "").encode("utf-8")).hexdigest()[:16]


def _ids_for_turn() -> Tuple[str, str]:
    tid = turn_context.current_turn_id_from_context()
    rec = turn_context.get_record(tid) if tid else None
    if rec is None:
        return "", ""
    return str(rec.session_id or ""), str(rec.task_id or "")


def dump_result(tool_name: str, payload: Dict[str, Any]) -> str:
    return framing.frame_untrusted(tool_name, json.dumps(payload, ensure_ascii=False))


def refuse(
    tool_name: str,
    *,
    state: str,
    reason: str,
    empty_key: str,
    extra: Optional[Dict[str, Any]] = None,
) -> str:
    payload: Dict[str, Any] = {
        "ok": False,
        "state": state,
        "reason": reason,
        empty_key: [] if empty_key != "text" else "",
    }
    if extra:
        payload.update(extra)
    return dump_result(tool_name, payload)


def authorize(
    tool_name: str,
    *,
    required_scope: str,
    missing_scope_reason: str,
    empty_key: str,
    log_event: str,
    started_ms: int,
) -> Tuple[Optional[str], Optional[Dict[str, str]]]:
    """Brian-only, store, and scope gate. (refusal, headers). Refusal is already framed."""
    turn_id = turn_context.current_turn_id_from_context()
    if not turn_context.is_brian_turn(turn_id):
        try:
            wslog.write_event(
                log_event,
                state=STATE_ERROR,
                reason=REASON_NOT_BRIAN,
                count=0,
                ms=started_ms,
            )
        except Exception:
            pass
        return (
            refuse(tool_name, state=STATE_ERROR, reason=REASON_NOT_BRIAN, empty_key=empty_key),
            None,
        )

    auth.maybe_clear_stale_reconnect()
    status = auth.store_status()
    if status.get("needs_reconnect") or not status.get("connected"):
        reason = status.get("needs_reconnect") or auth.REASON_MISSING_STORE
        return (
            refuse(
                tool_name,
                state=STATE_NEEDS_RECONNECT,
                reason=str(reason),
                empty_key=empty_key,
                extra={"missing_scopes": list(status.get("missing_scopes") or [])},
            ),
            None,
        )
    try:
        record = auth.load_token_record()
    except Exception:
        return (
            refuse(
                tool_name,
                state=STATE_NEEDS_RECONNECT,
                reason=auth.REASON_DECRYPT_FAILED,
                empty_key=empty_key,
            ),
            None,
        )
    if record is None:
        return (
            refuse(
                tool_name,
                state=STATE_NEEDS_RECONNECT,
                reason=auth.REASON_MISSING_STORE,
                empty_key=empty_key,
            ),
            None,
        )
    if required_scope not in set(record.scopes):
        return (
            refuse(
                tool_name,
                state=STATE_NEEDS_RECONNECT,
                reason=missing_scope_reason,
                empty_key=empty_key,
                extra={"missing_scopes": auth.missing_scopes(record.scopes)},
            ),
            None,
        )
    try:
        headers = auth.authorization_header()
    except RuntimeError as exc:
        reason = str(exc) or auth.REASON_INVALID_GRANT
        auth.set_reconnect_reason(reason)
        return (
            refuse(tool_name, state=STATE_NEEDS_RECONNECT, reason=reason, empty_key=empty_key),
            None,
        )
    except Exception:
        return (
            refuse(tool_name, state=STATE_ERROR, reason="auth_error", empty_key=empty_key),
            None,
        )
    return None, headers


def mark_then_frame(
    tool_name: str,
    payload: Dict[str, Any],
    *,
    empty_key: str,
    log_event: str,
    log_fields: Dict[str, Any],
) -> str:
    """Mark taint before the framed body. A failed mark returns no content."""
    # P8-READ: taint before content — P8-D09
    session_id, task_id = _ids_for_turn()
    try:
        if not session_id:
            raise ValueError("missing_session_id")
        taint.mark_tainted(session_id, task_id=task_id or None)
    except Exception:
        try:
            wslog.write_event(
                log_event,
                state=STATE_ERROR,
                reason=REASON_TAINT_WRITE_FAILED,
                count=0,
                **{k: v for k, v in log_fields.items() if k in ("ms",)},
            )
        except Exception:
            pass
        return refuse(
            tool_name,
            state=STATE_ERROR,
            reason=REASON_TAINT_WRITE_FAILED,
            empty_key=empty_key,
        )
    try:
        wslog.write_event(log_event, **log_fields)
    except Exception:
        pass
    return dump_result(tool_name, payload)


def google_get(
    url: str,
    *,
    headers: Dict[str, str],
    route: str,
    params: Optional[Dict[str, Any]] = None,
) -> "google_http.GoogleHttpResponse":
    # P8-READ: every call passes a route constant — P8-D11
    return google_http.request(
        "GET", url, headers=headers, params=params, timeout=30.0, route=route
    )
