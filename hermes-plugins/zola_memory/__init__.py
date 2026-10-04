"""zola_memory — Zola-owned local memory provider foundation (P6-D01/D03/D06)."""

from __future__ import annotations

import logging
import threading
import time as _time
from typing import Any, Dict, Optional

try:
    from . import log as memlog
    from . import llm_access
    from . import time_context
    from .provider import ZolaMemoryProvider
except ImportError:  # P6-STORE: flat unittest discover top — P6-D03
    import log as memlog
    import llm_access
    import time_context
    from provider import ZolaMemoryProvider

_provider: Optional[ZolaMemoryProvider] = None

# P6-TIME: session→provider registry for pre_llm_call (never use _provider for time) — P6-D05
_PROVIDER_BY_SESSION: Dict[str, ZolaMemoryProvider] = {}
_REGISTRY_LOCK = threading.Lock()


def _registry_put(sid: str, p: ZolaMemoryProvider) -> None:
    if not sid:
        return
    with _REGISTRY_LOCK:
        _PROVIDER_BY_SESSION[sid] = p


def _registry_rekey(old: str, new: str, p: ZolaMemoryProvider) -> None:
    # P6-TIME: only move an entry this provider currently owns; else no-op — P6-D05
    with _REGISTRY_LOCK:
        if not old or _PROVIDER_BY_SESSION.get(old) is not p:
            return
        del _PROVIDER_BY_SESSION[old]
        if new:
            _PROVIDER_BY_SESSION[new] = p


def _registry_remove(sid: str, p: ZolaMemoryProvider) -> None:
    with _REGISTRY_LOCK:
        if sid and _PROVIDER_BY_SESSION.get(sid) is p:
            del _PROVIDER_BY_SESSION[sid]


def _registry_get(sid: str) -> Optional[ZolaMemoryProvider]:
    with _REGISTRY_LOCK:
        return _PROVIDER_BY_SESSION.get(sid or "")


def clear_registry_for_tests() -> None:
    """Test helper: drop all session→provider mappings."""
    with _REGISTRY_LOCK:
        _PROVIDER_BY_SESSION.clear()


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


def _pre_llm_call_hook(**kwargs: Any) -> Any:
    """Ambient time injection (P6-D05); returns ``{"context": ...}`` or None."""
    # P6-TIME: resolve provider by session_id registry — never module _provider — P6-D05
    t0 = _time.perf_counter()
    sid = kwargs.get("session_id") or ""
    provider = _registry_get(str(sid))
    if provider is None:
        memlog.write_event(
            memlog.LOG_EVENT_TIME_CONTEXT,
            ok=False,
            reason="no_provider",
            gap_minutes="-",
            gap_line=False,
            elapsed_ms=int((_time.perf_counter() - t0) * 1000),
        )
        return None
    return time_context.handle_pre_llm_call(provider, **kwargs)


def register(ctx) -> None:
    """Register the memory provider with Hermes' memory-provider collector."""
    global _provider
    llm_access.set_collector(ctx)
    provider = ZolaMemoryProvider()
    _provider = provider
    _probe_llm(provider)
    ctx.register_memory_provider(provider)

    try:
        ctx.register_hook("pre_llm_call", _pre_llm_call_hook)
    except Exception:
        pass
