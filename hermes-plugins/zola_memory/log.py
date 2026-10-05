"""zola_memory logging — IDs, counts, and ms only (P6-D02/D06 privacy)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

# P6-STORE: named log event prefixes — P6-D03
LOG_FILENAME = "zola_memory.log"
LOG_EVENT_INITIALIZE = "zola_memory.initialize"
LOG_EVENT_LLM_PROBE = "zola_memory.llm_probe"
LOG_EVENT_FILE_CHECK = "zola_memory.file_check"
LOG_EVENT_FILE_CHECK_READ_ERROR = "zola_memory.file_check_read_error"
LOG_EVENT_FACT_ADD = "zola_memory.fact_add"
LOG_EVENT_FACT_REPLACE = "zola_memory.fact_replace"
LOG_EVENT_FACT_ERASE = "zola_memory.fact_erase"
LOG_EVENT_ERASE_ROLLBACK = "zola_memory.erase_rollback"
LOG_EVENT_PENDING_ERASURE_MARK = "zola_memory.pending_erasure_mark"
LOG_EVENT_REPLACE_UNMATCHED = "zola_memory.replace_unmatched"
LOG_EVENT_ON_TURN_START = "zola_memory.on_turn_start"
LOG_EVENT_SYNC_TURN = "zola_memory.sync_turn"
LOG_EVENT_ON_SESSION_END = "zola_memory.on_session_end"
LOG_EVENT_ON_SESSION_SWITCH = "zola_memory.on_session_switch"
LOG_EVENT_ON_PRE_COMPRESS = "zola_memory.on_pre_compress"
LOG_EVENT_PREFETCH = "zola_memory.prefetch"
LOG_EVENT_PRE_LLM_CALL = "zola_memory.pre_llm_call"
LOG_EVENT_TIME_CONTEXT = "zola_memory.time_context"
LOG_EVENT_TIME_MARKER_UPDATE = "zola_memory.time_marker_update"
LOG_EVENT_SHUTDOWN = "zola_memory.shutdown"
LOG_EVENT_FORGET_CASCADE = "zola_memory.forget_cascade"
LOG_EVENT_FORGET_TOOL = "zola_memory.forget_tool"
LOG_EVENT_FORGET_HOLD = "zola_memory.forget_hold"
LOG_EVENT_FORGET_GUARD = "zola_memory.forget_guard"
LOG_EVENT_TURN_DISPOSITION = "zola_memory.turn_disposition"
LOG_EVENT_PENDING_WRITE = "zola_memory.pending_write"
LOG_EVENT_CONSOLIDATE = "zola_memory.consolidate"
LOG_EVENT_CONSOLIDATE_GIVEUP = "zola_memory.consolidate.giveup"
LOG_EVENT_CONSOLIDATE_DISCARD = "zola_memory.consolidate.discard"
LOG_EVENT_CONSOLIDATE_LEASE = "zola_memory.consolidate.lease"
LOG_EVENT_RETRIEVE = "zola_memory.retrieve"
LOG_EVENT_PENDING_MISSING_USER_TIME = "zola_memory.pending_missing_user_time"
LOG_EVENT_CONSOLIDATE_TIME_UNRESOLVED = "zola_memory.consolidate.time_unresolved"
LOG_EVENT_STORE_OPEN = "zola_memory.store_open"
LOG_EVENT_SANITIZE_AFTER_ERASE = "zola_memory.sanitize_after_erase"
LOG_EVENT_SANITIZE_RETRY = "zola_memory.sanitize_retry"

_logger = logging.getLogger("zola_memory")
_file_handler_ready = False


def _log_path() -> Path:
    from hermes_constants import get_hermes_home

    return get_hermes_home() / "logs" / LOG_FILENAME


def _ensure_file_handler() -> None:
    global _file_handler_ready
    if _file_handler_ready:
        return
    try:
        path = _log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        # P6-STORE: FileHandler avoids a bare open() in production source — P6-D03
        handler = logging.FileHandler(str(path), encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
        _logger.addHandler(handler)
        _logger.setLevel(logging.INFO)
        _logger.propagate = False
        _file_handler_ready = True
    except Exception:
        _logger.debug("zola_memory log handler setup failed", exc_info=True)


def write_event(event: str, *, level: int = logging.INFO, **fields: Any) -> None:
    """Append one metadata-only log line. Never pass fact text in *fields*."""
    parts = [event]
    for key, value in fields.items():
        if value is None:
            parts.append(f"{key}=-")
        elif isinstance(value, bool):
            parts.append(f"{key}={str(value).lower()}")
        else:
            parts.append(f"{key}={value}")
    line = " ".join(parts)
    try:
        _ensure_file_handler()
        _logger.log(level, line)
    except Exception:
        pass


def reset_log_handler_for_tests() -> None:
    """Test helper: drop handlers so a new HERMES_HOME can attach a fresh file."""
    global _file_handler_ready
    for handler in list(_logger.handlers):
        _logger.removeHandler(handler)
        try:
            handler.close()
        except Exception:
            pass
    _file_handler_ready = False


def log_path_for_tests() -> Optional[Path]:
    try:
        return _log_path()
    except Exception:
        return None
