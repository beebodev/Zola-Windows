"""zola_workspace — Google Workspace boundary (P8-D01 / P8-D02 / P8-D03 / P8-D08)."""

from __future__ import annotations

import json
import time
from typing import Any, Dict

try:
    from . import auth
    from . import contacts
    from . import drive
    from . import gcal
    from . import gmail
    from . import guards
    from . import log as wslog
    from . import posture
    from . import turn_context
except ImportError:  # P8-HARDEN: flat unittest discover — P8-D02
    import auth
    import contacts
    import drive
    import gcal
    import gmail
    import guards
    import log as wslog
    import posture
    import turn_context

# P8-HARDEN / P8-CONNECT: named tool / toolset constants — P8-D01 / P8-D08
TOOL_NAME = "workspace_status"
TOOL_CALENDAR_QUERY = gcal.TOOL_NAME
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
        # P8-CONNECT: connected / needs_reconnect / missing_scopes from local store — P8-D03
        store = auth.store_status()
        outcome = {
            "ok": True,
            "connected": bool(store.get("connected")),
            "needs_reconnect": store.get("needs_reconnect"),
            "missing_scopes": list(store.get("missing_scopes") or []),
            "allowed_here": bool(allowed),
            "posture_ok": bool(ok_posture),
        }
    except Exception:
        outcome = {
            "ok": True,
            "connected": False,
            "needs_reconnect": auth.REASON_MISSING_STORE,
            "missing_scopes": [],
            "allowed_here": False,
            "posture_ok": False,
        }
    elapsed_ms = int((time.monotonic() - started) * 1000)
    try:
        wslog.write_event(
            wslog.LOG_EVENT_WORKSPACE_STATUS,
            ok=bool(outcome.get("ok")),
            connected=bool(outcome.get("connected")),
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
            {
                "ok": True,
                "connected": False,
                "needs_reconnect": auth.REASON_MISSING_STORE,
                "missing_scopes": [],
                "allowed_here": False,
                "posture_ok": False,
            },
            ensure_ascii=False,
        )


def register(ctx) -> None:
    """Register hooks, workspace_status, and calendar_query (synchronous)."""
    # P8-HARDEN: pre_llm_call stores turn_id-keyed context — P8-D02
    ctx.register_hook(HOOK_PRE_LLM_CALL, turn_context.pre_llm_call_hook)
    # P8-HARDEN / P8-CONNECT: config self-edit + memory-taint — P8-D02 / P8-D09
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
    # P8-CONNECT: register calendar_query synchronous — P8-D08
    ctx.register_tool(
        name=TOOL_CALENDAR_QUERY,
        toolset=TOOLSET_NAME,
        schema=gcal.calendar_schema(),
        handler=gcal.calendar_query_handler,
        description=gcal._CALENDAR_DESCRIPTION,
        is_async=False,
    )
    # P8-READ: five read-only tools, synchronous, same toolset — P8-D07 / P8-D08
    for name, schema, handler, description in (
        (gmail.TOOL_SEARCH, gmail.search_schema(), gmail.gmail_search_handler, gmail._SEARCH_DESCRIPTION),
        (gmail.TOOL_READ, gmail.read_schema(), gmail.gmail_read_handler, gmail._READ_DESCRIPTION),
        (drive.TOOL_SEARCH, drive.search_schema(), drive.drive_search_handler, drive._SEARCH_DESCRIPTION),
        (drive.TOOL_READ, drive.read_schema(), drive.drive_read_handler, drive._READ_DESCRIPTION),
        (contacts.TOOL_NAME, contacts.contacts_schema(), contacts.contacts_lookup_handler, contacts._DESCRIPTION),
    ):
        ctx.register_tool(
            name=name,
            toolset=TOOLSET_NAME,
            schema=schema,
            handler=handler,
            description=description,
            is_async=False,
        )
