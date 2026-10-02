"""Collector handle storage for the host PluginLlm accessor (P6-D04)."""

from __future__ import annotations

from typing import Any

# P6-STORE: collector retained for __init__._get_plugin_llm — P6-D04
_collector: Any = None


def set_collector(ctx: Any) -> None:
    global _collector
    _collector = ctx


def get_collector() -> Any:
    return _collector
