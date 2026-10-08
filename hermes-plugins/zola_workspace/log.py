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


def write_event(event: str, **fields: Any) -> None:
    """Append one metadata-only log line. Never pass message/command/path text."""
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
        _logger.info(line)
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
