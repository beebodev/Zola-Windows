"""zola_workspace — boundary skeleton (P8-D01 / P8-D02). No Google code."""

from __future__ import annotations

import json
import time
from typing import Any, Dict

try:
    from . import guards
    from . import log as wslog
    from . import posture
    from . import turn_context
except ImportError:  # P8-HARDEN: flat unittest discover — P8-D02
    import guards
    import log as wslog
    import posture
    import turn_context

# P8-HARDEN: named tool / toolset constants — P8-D01
TOOL_NAME = "workspace_status"
TOOLSET_NAME = "zola_workspace"
HOOK_PRE_LLM_CALL = "pre_llm_call"
HOOK_PRE_TOOL_CALL = "pre_tool_call"

_WORKSPACE_STATUS_DESCRIPTION = (
    "Report whether Google Workspace is connected for Zola and whether this "
    "conversation may use Workspace tools. Does not call Google."
)

_WORKSPACE_STATUS_SCHEMA: Dict[str, Any] = {
    "name": TOOL_NAME,
    "description": _WORKSPACE_STATUS_DESCRIPTION,
    "parameters": {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    },
}


def workspace_status_handler(args: dict, **kwargs) -> str:
    """Brian-only status probe; never opens a network socket; never raises."""
    started = time.monotonic()
    try:
        # P8-HARDEN: turn_id only from observability ContextVar — no kwargs fallback — P8-D02
        turn_id = turn_context.current_turn_id_from_context()
        allowed = turn_context.is_brian_turn(turn_id) if turn_id else False
        ok_posture = posture.posture_ok()
        # P8-HARDEN: connected always false in Track 1 — no Google — P8-D01
        outcome = {
            "ok": True,
            "connected": False,
            "allowed_here": bool(allowed),
            "posture_ok": bool(ok_posture),
        }
    except Exception:
        outcome = {
            "ok": True,
            "connected": False,
            "allowed_here": False,
            "posture_ok": False,
        }
    elapsed_ms = int((time.monotonic() - started) * 1000)
    try:
        wslog.write_event(
            wslog.LOG_EVENT_WORKSPACE_STATUS,
            ok=bool(outcome.get("ok")),
            allowed_here=bool(outcome.get("allowed_here")),
            posture_ok=bool(outcome.get("posture_ok")),
            ms=elapsed_ms,
        )
    except Exception:
        pass
    try:
        return json.dumps(outcome, ensure_ascii=False)
    except Exception:
        return json.dumps(
            {"ok": True, "connected": False, "allowed_here": False, "posture_ok": False},
            ensure_ascii=False,
        )


def register(ctx) -> None:
    """Register hooks and the workspace_status tool (synchronous)."""
    # P8-HARDEN: pre_llm_call stores turn_id-keyed context — P8-D02
    ctx.register_hook(HOOK_PRE_LLM_CALL, turn_context.pre_llm_call_hook)
    # P8-HARDEN: config/.env self-edit guard + inert stubs — P8-D02
    ctx.register_hook(HOOK_PRE_TOOL_CALL, guards.pre_tool_call_hook)
    # P8-HARDEN: is_async=False required (Brian Phase 3 edit #4) — P8-D01
    ctx.register_tool(
        name=TOOL_NAME,
        toolset=TOOLSET_NAME,
        schema=_WORKSPACE_STATUS_SCHEMA,
        handler=workspace_status_handler,
        description=_WORKSPACE_STATUS_DESCRIPTION,
        is_async=False,
    )
