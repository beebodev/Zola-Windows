"""Security-posture invariant — veto only; fail closed (P8-D02 layer 1)."""

from __future__ import annotations

from typing import Tuple

# P8-HARDEN: named posture outcomes — P8-D02
MODE_MANUAL = "manual"
MODE_OFF = "off"
MODE_SMART = "smart"

REASON_OK = "ok"
REASON_MODE = "approvals_mode"
REASON_MODE_UNREADABLE = "approvals_mode_unreadable"
REASON_YOLO_ENV = "yolo_env"
REASON_YOLO_ENV_UNREADABLE = "yolo_env_unreadable"
REASON_YOLO_SESSION = "yolo_session"
REASON_YOLO_SESSION_UNREADABLE = "yolo_session_unreadable"


def _normalize_mode(mode) -> str:
    """Match approval_context._normalize_approval_mode (L200–214) for a value actually read."""
    if isinstance(mode, bool):
        return MODE_OFF if mode is False else MODE_MANUAL
    if isinstance(mode, str):
        normalized = mode.strip().lower()
        if normalized in (MODE_MANUAL, MODE_SMART, MODE_OFF):
            return normalized
    return MODE_MANUAL


def _read_approval_mode() -> str:
    """Effective approvals.mode via Hermes's reader. Raises on import/call failure."""
    # P8-HARDEN: fail closed — no soft fallback to manual — P8-D02
    from tools.approval_context import _get_approval_mode

    return _get_approval_mode()


def _yolo_env_frozen() -> bool:
    """Process YOLO frozen at tools.approval import. Raises on import/read failure."""
    from tools.approval import _YOLO_MODE_FROZEN

    return bool(_YOLO_MODE_FROZEN)


def _yolo_session() -> bool:
    """Session YOLO. Raises on import/call failure."""
    from tools.approval import is_current_session_yolo_enabled

    return bool(is_current_session_yolo_enabled())


def posture_ok() -> bool:
    """True iff approvals.mode == manual and YOLO off (env + session). Veto only."""
    # P8-HARDEN: never authorizes; unreadable readers veto — P8-D02
    return posture_detail()[0]


def posture_detail() -> Tuple[bool, str]:
    """Return (ok, reason_constant). Fail closed on unreadable Hermes readers."""
    try:
        mode = _normalize_mode(_read_approval_mode())
    except Exception:
        return False, REASON_MODE_UNREADABLE
    if mode != MODE_MANUAL:
        return False, REASON_MODE

    try:
        yolo_env = _yolo_env_frozen()
    except Exception:
        # P8-HARDEN: unreadable → treat as YOLO on / unknown — P8-D02
        return False, REASON_YOLO_ENV_UNREADABLE
    if yolo_env:
        return False, REASON_YOLO_ENV

    try:
        yolo_sess = _yolo_session()
    except Exception:
        return False, REASON_YOLO_SESSION_UNREADABLE
    if yolo_sess:
        return False, REASON_YOLO_SESSION

    return True, REASON_OK
