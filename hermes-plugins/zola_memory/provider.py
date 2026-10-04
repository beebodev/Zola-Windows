"""ZolaMemoryProvider — fact index foundation (P6-D01/D03/D06)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent.memory_provider import MemoryProvider

try:
    from . import fact_index, log as memlog, store
except ImportError:  # P6-STORE: flat unittest discover top — P6-D03
    import fact_index
    import log as memlog
    import store

# P6-STORE: provider identity — P6-D03
PROVIDER_NAME = "zola_memory"


class ZolaMemoryProvider(MemoryProvider):
    """Indexes USER.md/MEMORY.md; does not author facts or surface tools this track."""

    def __init__(self) -> None:
        import threading

        self.llm_available = False
        self._conn = None
        self._hermes_home: Optional[Path] = None
        self._session_id: Optional[str] = None
        self._current_user_message = ""
        self._initialized = False
        # P6-STORE: provider-level lock mirrors connection lock — P6-D03
        self._lock = threading.RLock()

    @staticmethod
    def _registry():
        """Lazy import of session→provider registry helpers (avoid import cycle)."""
        try:
            from . import (
                _registry_put,
                _registry_rekey,
                _registry_remove,
            )
        except ImportError:  # P6-TIME: flat unittest discover top — P6-D05
            import importlib

            mod = importlib.import_module("__init__")
            _registry_put = mod._registry_put
            _registry_rekey = mod._registry_rekey
            _registry_remove = mod._registry_remove
        return _registry_put, _registry_rekey, _registry_remove

    @property
    def name(self) -> str:
        return PROVIDER_NAME

    def is_available(self) -> bool:
        # P6-STORE: fail closed without FTS5 — P6-D03
        return store.fts5_available()

    def unavailable_reason(self) -> str:
        if not store.fts5_available():
            return "SQLite FTS5 is not available in this Python runtime"
        return ""

    def initialize(self, session_id: str, **kwargs) -> None:
        import time as _time

        t0 = _time.perf_counter()
        hermes_home = Path(kwargs.get("hermes_home") or "")
        if not hermes_home:
            from hermes_constants import get_hermes_home

            hermes_home = Path(get_hermes_home())
        self._hermes_home = hermes_home

        # P6-STORE: probe host LLM once via __init__._get_plugin_llm — P6-D04
        try:
            from . import _get_plugin_llm
        except ImportError:
            import importlib

            _get_plugin_llm = importlib.import_module("__init__")._get_plugin_llm  # type: ignore
        try:
            llm = _get_plugin_llm()
        except Exception:
            llm = None
        self.llm_available = llm is not None
        memlog.write_event(
            memlog.LOG_EVENT_LLM_PROBE,
            level=logging.WARNING if not self.llm_available else logging.INFO,
            llm_available=self.llm_available,
        )

        fts_ok = store.fts5_available()
        if not fts_ok:
            memlog.write_event(
                memlog.LOG_EVENT_INITIALIZE,
                ok=False,
                schema_version=store.SCHEMA_VERSION,
                fts_ok=False,
                import_count=0,
                elapsed_ms=int((_time.perf_counter() - t0) * 1000),
            )
            return

        with self._lock:
            self._conn = store.open_store(hermes_home)
            result = fact_index.run_file_check(self._conn, hermes_home, force=True)
            self._initialized = True
            self._session_id = session_id or ""
        # P6-TIME: registry only after store open + file check succeed — P6-D05
        if self._session_id:
            put, _, _ = self._registry()
            put(self._session_id, self)
        memlog.write_event(
            memlog.LOG_EVENT_INITIALIZE,
            ok=True,
            schema_version=store.SCHEMA_VERSION,
            fts_ok=True,
            import_count=result.get("added", 0),
            elapsed_ms=int((_time.perf_counter() - t0) * 1000),
        )

    def system_prompt_block(self) -> str:
        return ""

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        return []

    def prefetch(self, query: str, *, session_id: str = "") -> str:
        memlog.write_event(
            memlog.LOG_EVENT_PREFETCH,
            session_id=session_id or "-",
            returned_len=0,
        )
        return ""

    def on_memory_write(
        self,
        action: str,
        target: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        if self._conn is None or self._hermes_home is None:
            return
        with self._lock:
            fact_index.handle_memory_write(
                self._conn,
                self._hermes_home,
                action=action,
                target=target,
                content=content,
                metadata=metadata,
                user_message=self._current_user_message,
            )

    def on_turn_start(self, turn_number: int, message: str, **kwargs) -> None:
        # P6-STORE: keep current user message in memory only for forget-intent — P6-D06
        with self._lock:
            self._current_user_message = message if isinstance(message, str) else ""
            session_id = kwargs.get("session_id") or ""
            memlog.write_event(
                memlog.LOG_EVENT_ON_TURN_START,
                session_id=session_id or "-",
                turn_number=turn_number,
                msg_len=len(self._current_user_message),
            )
            if self._conn is not None and self._hermes_home is not None:
                fact_index.run_file_check(self._conn, self._hermes_home, force=False)

    def sync_turn(
        self,
        user_content: str,
        assistant_content: str,
        *,
        session_id: str = "",
        messages: Optional[List[Dict[str, Any]]] = None,
        turn_author: Optional[Dict[str, Any]] = None,
    ) -> None:
        memlog.write_event(
            memlog.LOG_EVENT_SYNC_TURN,
            session_id=session_id or "-",
            user_len=len(user_content or ""),
            assistant_len=len(assistant_content or ""),
        )

    def on_session_end(self, messages: List[Dict[str, Any]]) -> None:
        memlog.write_event(
            memlog.LOG_EVENT_ON_SESSION_END,
            session_id="-",
            message_count=len(messages or []),
        )

    def on_session_switch(
        self,
        new_session_id: str,
        *,
        parent_session_id: str = "",
        reset: bool = False,
        rewound: bool = False,
        **kwargs,
    ) -> None:
        old = self._session_id or ""
        new = new_session_id or ""
        # P6-TIME: re-key session→provider registry on switch — P6-D05
        _, rekey, _ = self._registry()
        rekey(old, new, self)
        self._session_id = new
        memlog.write_event(
            memlog.LOG_EVENT_ON_SESSION_SWITCH,
            session_id=new_session_id or "-",
            parent_session_id=parent_session_id or "-",
            reset=reset,
            rewound=rewound,
        )

    def on_pre_compress(self, messages: List[Dict[str, Any]]) -> str:
        memlog.write_event(
            memlog.LOG_EVENT_ON_PRE_COMPRESS,
            session_id="-",
            message_count=len(messages or []),
        )
        return ""

    def shutdown(self) -> None:
        ok = True
        try:
            # P6-TIME: identity-checked registry remove before closing conn — P6-D05
            _, _, remove = self._registry()
            remove(self._session_id or "", self)
            with self._lock:
                if self._conn is not None:
                    store.release_lock(self._conn)
                    self._conn.close()
                    self._conn = None
        except Exception:
            ok = False
        memlog.write_event(memlog.LOG_EVENT_SHUTDOWN, ok=ok)
