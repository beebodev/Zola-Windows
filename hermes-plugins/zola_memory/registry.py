"""Session→provider registry for pre_llm_call (P6-D05)."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Dict, Optional

if TYPE_CHECKING:
    from provider import ZolaMemoryProvider

# P6-TIME: session→provider registry for pre_llm_call (never use module _provider) — P6-D05
_PROVIDER_BY_SESSION: Dict[str, "ZolaMemoryProvider"] = {}
_REGISTRY_LOCK = threading.Lock()


def put(sid: str, p: "ZolaMemoryProvider") -> None:
    if not sid:
        return
    with _REGISTRY_LOCK:
        _PROVIDER_BY_SESSION[sid] = p


def rekey(old: str, new: str, p: "ZolaMemoryProvider") -> None:
    # P6-TIME: only move an entry this provider currently owns; else no-op — P6-D05
    with _REGISTRY_LOCK:
        if not old or _PROVIDER_BY_SESSION.get(old) is not p:
            return
        del _PROVIDER_BY_SESSION[old]
        if new:
            _PROVIDER_BY_SESSION[new] = p


def remove(sid: str, p: "ZolaMemoryProvider") -> None:
    with _REGISTRY_LOCK:
        if sid and _PROVIDER_BY_SESSION.get(sid) is p:
            del _PROVIDER_BY_SESSION[sid]


def get(sid: str) -> Optional["ZolaMemoryProvider"]:
    with _REGISTRY_LOCK:
        return _PROVIDER_BY_SESSION.get(sid or "")


def clear_for_tests() -> None:
    """Test helper: drop all session→provider mappings."""
    with _REGISTRY_LOCK:
        _PROVIDER_BY_SESSION.clear()
