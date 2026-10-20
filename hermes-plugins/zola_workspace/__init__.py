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
    from . import send_gate
    from . import turn_context
    from . import loops as zola_loops
    from . import surface as zola_surface
except ImportError:  # P8-HARDEN: flat unittest discover — P8-D02
    import auth
    import contacts
    import drive
    import gcal
    import gmail
    import guards
    import log as wslog
    import posture
    import send_gate
    import turn_context
    import loops as zola_loops
    import surface as zola_surface

# P8-HARDEN / P8-CONNECT: named tool / toolset constants — P8-D01 / P8-D08
TOOL_NAME = "workspace_status"
TOOL_CALENDAR_QUERY = gcal.TOOL_NAME
TOOLSET_NAME = "zola_workspace"
HOOK_PRE_LLM_CALL = "pre_llm_call"
HOOK_PRE_TOOL_CALL = "pre_tool_call"
# P8-SEND: review on the finalized reply; clear the draft when the session ends — P8-D05
HOOK_POST_LLM_CALL = "post_llm_call"
HOOK_ON_SESSION_END = "on_session_end"
HOOK_AGENT_LOOP_STOPPED = "agent_loop_stopped"

_WORKSPACE_STATUS_DESCRIPTION = (
    "Mail watcher health and Google connection: when mail was last checked, "
    "and whether Google needs reconnecting. "
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
        outcome.update(zola_surface.status_fields())
    except Exception:
        outcome = {
            "ok": True,
            "connected": False,
            "needs_reconnect": auth.REASON_MISSING_STORE,
            "missing_scopes": [],
            "allowed_here": False,
            "posture_ok": False,
            "watcher_state": "unknown",
            "gmail_ok_at": "",
            "calendar_ok_at": "",
            "watcher_needs_reconnect": 0,
            "watcher_sentence": "I can't tell whether the watcher is running.",
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
    # P10-INTAKE: take the launch secret out of the environment before any tool runs — P10-D12
    try:
        from . import launch_secret
    except ImportError:
        import launch_secret
    launch_secret.take()
    # P8-HARDEN: pre_llm_call stores turn_id-keyed context — P8-D02
    ctx.register_hook(HOOK_PRE_LLM_CALL, turn_context.pre_llm_call_hook)
    # P8-SEND: review the read-back, then drop this turn's authorization — P8-D05
    ctx.register_hook(HOOK_POST_LLM_CALL, send_gate.post_llm_call_hook)
    # P9-SURFACE: confirm the attempt on the generated reply — P9-D10
    ctx.register_hook(HOOK_POST_LLM_CALL, zola_surface.post_llm_call_hook)
    ctx.register_hook(HOOK_ON_SESSION_END, send_gate.on_session_end_hook)
    ctx.register_hook(HOOK_AGENT_LOOP_STOPPED, send_gate.agent_loop_stopped_hook)
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
        (gmail.TOOL_DRAFT, gmail.draft_schema(), gmail.gmail_draft_handler, gmail._DRAFT_DESCRIPTION),
        (gmail.TOOL_SEND, gmail.send_schema(), gmail.gmail_send_draft_handler, gmail._SEND_DESCRIPTION),
    ):
        ctx.register_tool(
            name=name,
            toolset=TOOLSET_NAME,
            schema=schema,
            handler=handler,
            description=description,
            is_async=False,
        )
    # P9-SURFACE: whats_pending is the only "what's pending" source — P9-D10
    ctx.register_tool(
        name=zola_surface.TOOL_NAME,
        toolset=TOOLSET_NAME,
        schema=zola_surface.whats_pending_schema(),
        handler=zola_surface.whats_pending_handler,
        description=zola_surface._DESCRIPTION,
        is_async=False,
    )
    # P9-STORE: same toolset as the other Brian-only tools; no config.yaml line — P9-D09
    ctx.register_tool(
        name=zola_loops.TOOL_NAME,
        toolset=TOOLSET_NAME,
        schema=zola_loops.loops_schema(),
        handler=zola_loops.loops_handler,
        description=zola_loops._DESCRIPTION,
        is_async=False,
    )
    # P9-FIX-ARM: wrap prompt.submit only in the serve process, before any turn — P8-D02
    try:
        from . import origin
    except ImportError:
        import origin  # type: ignore
    origin.install_for_serve()
    # P9-SPEAK: gateway methods, serve process only, no Hermes edit — P9-D11
    try:
        try:
            from . import speech
        except ImportError:
            import speech
        speech.install_methods()
    except Exception:
        pass
    # P9-RANK: the worker starts only in serve, and only when the config flag is true — P9-D08
    try:
        try:
            from . import ranker
        except ImportError:
            import ranker
        unload = getattr(ctx, "on_unload", None)
        if callable(unload):
            unload(ranker.stop_worker)
        ranker.start_from_register(ctx)
    except Exception:
        try:
            wslog.write_warning(wslog.LOG_EVENT_RANKER, reason="start_failed", state="worker_failed")
        except Exception:
            pass
    # P9-STORE: purge only in serve; tests do not pass that argv — P9-D07
    try:
        try:
            from . import proactive_store
        except ImportError:
            import proactive_store
        proactive_store.start_purge_thread()
    except Exception:
        pass
