"""zola_memory — Zola-owned local memory provider foundation (P6-D01/D03/D06)."""

from __future__ import annotations

import logging
from typing import Any, Optional

try:
    from . import log as memlog
    from . import llm_access
    from .provider import ZolaMemoryProvider
except ImportError:  # P6-STORE: flat unittest discover top — P6-D03
    import log as memlog
    import llm_access
    from provider import ZolaMemoryProvider

_provider: Optional[ZolaMemoryProvider] = None


def _get_plugin_llm() -> Any:
    """Sole call site for ``ctx._plugin_context()`` (private Hermes API @ v2026.9.14)."""
    # P6-STORE: private PluginContext bridge; pinned hermes-agent v2026.9.14 — P6-D04
    ctx = llm_access.get_collector()
    if ctx is None:
        return None
    try:
        return ctx._plugin_context().llm
    except Exception:
        return None


def _probe_llm(provider: ZolaMemoryProvider) -> None:
    llm = _get_plugin_llm()
    provider.llm_available = llm is not None
    memlog.write_event(
        memlog.LOG_EVENT_LLM_PROBE,
        level=logging.WARNING if not provider.llm_available else logging.INFO,
        llm_available=provider.llm_available,
    )


def _logging_hook_factory(event_name: str):
    """Logging-only observer; never returns context (G4/G10 hook proof)."""

    def _hook(**kwargs: Any) -> None:
        session_id = kwargs.get("session_id") or "-"
        memlog.write_event(event_name, session_id=session_id, observer=1)

    return _hook


def register(ctx) -> None:
    """Register the memory provider with Hermes' memory-provider collector."""
    global _provider
    llm_access.set_collector(ctx)
    provider = ZolaMemoryProvider()
    _provider = provider
    _probe_llm(provider)
    ctx.register_memory_provider(provider)

    # P6-STORE: logging-only hooks for AUD-36 proof; no returned context — P6-D03
    try:
        ctx.register_hook("pre_llm_call", _logging_hook_factory(memlog.LOG_EVENT_PRE_LLM_CALL))
    except Exception:
        pass
