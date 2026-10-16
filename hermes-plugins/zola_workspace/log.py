"""zola_workspace logging — metadata only (P8-D11)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

# P8-HARDEN: named log prefixes — P8-D11
LOG_FILENAME = "zola_workspace.log"
LOG_EVENT_GUARD = "zola_workspace.guard"
LOG_EVENT_WORKSPACE_STATUS = "zola_workspace.workspace_status"
# P8-CONNECT: calendar metadata-only log event — P8-D11
LOG_EVENT_CALENDAR_QUERY = "zola_workspace.calendar_query"
LOG_EVENT_GMAIL_SEARCH = "zola_workspace.gmail_search"
LOG_EVENT_GMAIL_READ = "zola_workspace.gmail_read"
LOG_EVENT_DRIVE_SEARCH = "zola_workspace.drive_search"
LOG_EVENT_DRIVE_READ = "zola_workspace.drive_read"
LOG_EVENT_CONTACTS = "zola_workspace.contacts_lookup"
# P9-STORE: loop list and create log a count only; names and subjects stay out of the log — P9-D09
LOG_EVENT_LOOPS = "zola_workspace.loops"
# P8-SEND: send-gate metadata only — P8-D11
LOG_EVENT_SEND_GATE = "zola_workspace.send_gate"
# P9-RANK: metadata only. Never subject, gist, body, address, or model text — P8-D11
LOG_EVENT_RANKER = "zola_workspace.ranker"

_logger = logging.getLogger("zola_workspace")
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
        # P8-HARDEN: FileHandler avoids bare open() — P8-D11
        handler = logging.FileHandler(str(path), encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(message)s"))
        _logger.addHandler(handler)
        _logger.setLevel(logging.INFO)
        _logger.propagate = False
        _file_handler_ready = True
    except Exception:
        _logger.debug("zola_workspace log handler setup failed", exc_info=True)


def _format_event(event: str, fields: dict) -> str:
    parts = [event]
    for key, value in fields.items():
        if value is None:
            parts.append(f"{key}=-")
        elif isinstance(value, bool):
            parts.append(f"{key}={str(value).lower()}")
        else:
            parts.append(f"{key}={value}")
    return " ".join(parts)


def write_event(event: str, **fields: Any) -> None:
    """Append one metadata-only log line. Never pass message/command/path text."""
    _emit(logging.INFO, event, fields)


def write_warning(event: str, **fields: Any) -> None:
    """Same metadata line at WARNING. Never pass message text."""
    _emit(logging.WARNING, event, fields)


def _emit(level: int, event: str, fields: dict) -> None:
    line = _format_event(event, fields)
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
