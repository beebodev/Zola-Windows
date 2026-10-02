"""zola_tools — side-effect-free calculate tool for Zola (P6-D08)."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict

try:
    from . import calculator
except ImportError:  # P6-CALC: loose-module load in unit tests — P6-D08
    import calculator

# P6-CALC: log event prefixes and tool metadata — P6-D08
LOG_EVENT_CALCULATE = "zola_tools.calculate"
TOOL_NAME = "calculate"
TOOLSET_NAME = "zola_tools"
LOG_FILENAME = "zola_tools.log"

_CALCULATE_DESCRIPTION = (
    "Evaluate arithmetic only. Supports + - * / ** , parentheses, unary +/- , "
    "and functions abs, round, min, max, sqrt, floor, ceil. "
    "Percentages: write 0.15*240 (not %). % and // are not supported; use floor() "
    "for rounding down. Cannot run code, shell, imports, files, or network."
)

_logger = logging.getLogger("zola_tools")
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
        # P6-CALC: logging.FileHandler appends without a banned builtin in this file — P6-D08
        handler = logging.FileHandler(str(path), encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(message)s"))
        _logger.addHandler(handler)
        _logger.setLevel(logging.INFO)
        _logger.propagate = False
        _file_handler_ready = True
    except Exception:
        _logger.debug("zola_tools log handler setup failed", exc_info=True)


def _write_plugin_log(
    *,
    ok: bool,
    error: str | None,
    input_length: int,
    node_count: int | None,
    elapsed_ms: int,
) -> None:
    # P6-CALC: metadata only — never expression text or results — P6-D08
    line = (
        f"{LOG_EVENT_CALCULATE} ok={str(ok).lower()} "
        f"error={error or '-'} input_length={input_length} "
        f"node_count={node_count if node_count is not None else '-'} "
        f"elapsed_ms={elapsed_ms}"
    )
    try:
        _ensure_file_handler()
        _logger.info(line)
    except Exception:
        pass


_CALCULATE_SCHEMA: Dict[str, Any] = {
    "name": TOOL_NAME,
    "description": _CALCULATE_DESCRIPTION,
    "parameters": {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Arithmetic expression to evaluate (Decimal math only).",
            },
        },
        "required": ["expression"],
    },
}


def calculate_handler(args: dict, **kwargs) -> str:
    """Hermes tool handler: JSON string; never raises."""
    started = time.monotonic()
    input_length = 0
    node_count = None
    try:
        expression = args.get("expression") if isinstance(args, dict) else None
        # P6-CALC: type and length checks before node_count for logging — P6-D08
        if not isinstance(expression, str):
            outcome = {"ok": False, "error": calculator.ERROR_INVALID_TYPE}
        elif len(expression) > calculator.MAX_INPUT_LENGTH:
            input_length = len(expression)
            outcome = {"ok": False, "error": calculator.ERROR_INPUT_TOO_LONG}
        else:
            input_length = len(expression)
            try:
                node_count = calculator.node_count_of(expression)
            except Exception:
                node_count = None
            try:
                outcome = calculator.evaluate(expression)
            except Exception:
                outcome = {"ok": False, "error": calculator.ERROR_INVALID_ARGUMENT}
    except Exception:
        outcome = {"ok": False, "error": calculator.ERROR_INVALID_ARGUMENT}
    elapsed_ms = int((time.monotonic() - started) * 1000)
    try:
        _write_plugin_log(
            ok=bool(outcome.get("ok")),
            error=None if outcome.get("ok") else str(outcome.get("error") or "-"),
            input_length=input_length,
            node_count=node_count,
            elapsed_ms=elapsed_ms,
        )
    except Exception:
        pass
    try:
        return json.dumps(outcome, ensure_ascii=False)
    except Exception:
        return json.dumps(
            {"ok": False, "error": calculator.ERROR_INVALID_ARGUMENT},
            ensure_ascii=False,
        )


def register(ctx) -> None:
    """Register the single calculate tool on the zola_tools toolset."""
    # P6-CALC: one side-effect-free tool — P6-D08
    ctx.register_tool(
        name=TOOL_NAME,
        toolset=TOOLSET_NAME,
        schema=_CALCULATE_SCHEMA,
        handler=calculate_handler,
        description=_CALCULATE_DESCRIPTION,
    )
