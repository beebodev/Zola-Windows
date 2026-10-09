"""ZolaMemoryProvider — fact index foundation (P6-D01/D03/D06)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent.memory_provider import MemoryProvider

try:
    from . import (
        consolidate,
        fact_index,
        forget,
        log as memlog,
        pending,
        registry,
        retrieve,
        store,
    )
except ImportError:  # P6-STORE: flat unittest discover top — P6-D03
    import consolidate
    import fact_index
    import forget
    import log as memlog
    import pending
    import registry
    import retrieve
    import store

# P6-STORE: provider identity — P6-D03
PROVIDER_NAME = "zola_memory"


class ZolaMemoryProvider(MemoryProvider):
    """Indexes USER.md/MEMORY.md; exposes erase-only forget_memory (P6-D06)."""

    def __init__(self) -> None:
        import threading

        self.llm_available = False
        self._conn = None
        self._hermes_home: Optional[Path] = None
        self._session_id: Optional[str] = None
        self._platform: str = ""
        self._parent_session_id: str = ""
        self._current_user_message = ""
        self._initialized = False
        # P6-STORE: provider-level lock mirrors connection lock — P6-D03
        self._lock = threading.RLock()
        # P6-FORGET: disposition / hold / candidates (process memory) — P6-D06
        self._forget_state = forget.ForgetSessionState()
        # P6-EPISODES: per-session turn index (ordering metadata only; not dedupe) — P6-D04
        self._turn_index = 0

    @staticmethod
    def _get_plugin_llm():
        """Resolve plugin LLM without importing package __init__ by shadowed name."""
        try:
            from . import _get_plugin_llm as getter  # type: ignore

            return getter
        except ImportError:
            import llm_access

            def getter() -> Any:
                ctx = llm_access.get_collector()
                if ctx is None:
                    return None
                try:
                    return ctx._plugin_context().llm
                except Exception:
                    return None

            return getter

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
        # P6-FORGET: platform/parent for schema omit + tool refuse — P6-D06
        self._platform = str(kwargs.get("platform") or "")
        self._parent_session_id = str(kwargs.get("parent_session_id") or "")

        # P6-STORE: probe host LLM once — P6-D04
        try:
            llm = self._get_plugin_llm()()
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
            # P6-FORGET: restart with meta hold but empty candidates → expire — P6-D06
            forget.expire_orphan_hold_on_restart(self)
        # P6-TIME: registry only after store open + file check succeed — P6-D05
        if self._session_id:
            registry.put(self._session_id, self)
        # P6-EPISODES: quiet timer + initialize backlog consolidate signal — P6-D04
        consolidate.start_quiet_timer(self)
        try:
            with store.locked(self._conn):
                backlog = pending.count_pending(self._conn)
        except Exception:
            backlog = 0
        if backlog:
            consolidate.request_consolidate(self, "initialize")
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
        # P6-FORGET: Hermes add_provider reads schemas before initialize (platform unset) — P6-D06
        if not self._initialized:
            return [forget.FORGET_MEMORY_SCHEMA]
        # After initialize: omit for non-Brian conversations (cron/parent); refuse still in handler
        if not forget.is_brian_conversation(self._platform, self._parent_session_id):
            return []
        return [forget.FORGET_MEMORY_SCHEMA]

    def handle_tool_call(self, tool_name: str, args: Dict[str, Any], **kwargs: Any) -> str:
        if tool_name != forget.TOOL_NAME:
            return '{"ok":false,"refused_reason":"unknown_tool"}'
        with self._lock:
            return forget.handle_forget_memory(
                self, args if isinstance(args, dict) else {}, **kwargs
            )

    def prefetch(self, query: str, *, session_id: str = "") -> str:
        text = ""
        if self._conn is not None:
            with self._lock:
                with store.locked(self._conn):
                    text = retrieve.retrieve_episodes(
                        self._conn,
                        query or "",
                        platform=self._platform,
                        parent_session_id=self._parent_session_id,
                    )
        memlog.write_event(
            memlog.LOG_EVENT_PREFETCH,
            session_id=session_id or self._session_id or "-",
            returned_len=len(text),
        )
        return text

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
                provider=self,
            )

    def on_turn_start(self, turn_number: int, message: str, **kwargs) -> None:
        # P6-STORE: keep current user message in memory only for forget-intent — P6-D06
        with self._lock:
            self._current_user_message = message if isinstance(message, str) else ""
            session_id = self._session_id or ""
            memlog.write_event(
                memlog.LOG_EVENT_ON_TURN_START,
                session_id=session_id or "-",
                turn_number=turn_number,
                msg_len=len(self._current_user_message),
            )
            # P9-FIX-ARM: Hermes does not pass turn_id; the pre_llm context does — P8-D02
            tid = str(kwargs.get("turn_id") or "") or forget.current_origin_turn_id()
            forget.on_turn_start_forget_hooks(
                self, self._current_user_message, turn_id=tid
            )
            if self._conn is not None and self._hermes_home is not None:
                # P6-EPISODES: retry deferred G-ERASE WAL TRUNCATE — P6-D04
                try:
                    with store.locked(self._conn):
                        store.try_pending_sanitize(
                            self._conn, trigger="on_turn_start"
                        )
                except Exception:
                    pass
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
        with self._lock:
            # P6-EPISODES X6: disposition once → log + pending writer — P6-D04
            decision, reason = forget.turn_disposition(
                self._forget_state, user_content or ""
            )
            memlog.write_event(
                memlog.LOG_EVENT_TURN_DISPOSITION,
                decision=decision,
                reason=reason,
                ok=True,
            )
            memlog.write_event(
                memlog.LOG_EVENT_SYNC_TURN,
                session_id=session_id or self._session_id or "-",
                user_len=len(user_content or ""),
                assistant_len=len(assistant_content or ""),
            )
            if (
                self._conn is not None
                and forget.is_brian_conversation(
                    self._platform, self._parent_session_id
                )
                # P9-FIX-ARM: the permit matches this text; a remembered turn id is not used — P8-D02
                and forget.sync_turn_allowed(user_content or "")
                and decision == "keep"
            ):
                sid = session_id or self._session_id or ""
                self._turn_index += 1
                user_time = pending.resolve_user_time(
                    messages, user_content or ""
                )
                assistant_time = pending.resolve_assistant_time(messages)
                with store.locked(self._conn):
                    written = pending.write_pending(
                        self._conn,
                        session_id=sid,
                        turn_index=self._turn_index,
                        user_text=user_content or "",
                        assistant_text=assistant_content or "",
                        user_time=user_time,
                        assistant_time=assistant_time,
                        disposition=decision,
                    )
                if written:
                    consolidate.note_pending_write()

    def on_session_end(self, messages: List[Dict[str, Any]]) -> None:
        # P6-EPISODES: signal only — never inline consolidate (E5) — P6-D04
        consolidate.request_consolidate(self, "session_end")
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
        registry.rekey(old, new, self)
        self._session_id = new
        self._parent_session_id = parent_session_id or ""
        with self._lock:
            # P6-FORGET: E1 — disposition drops survive switch; E3 — hold ends — P6-D06
            forget.on_session_switch_forget_hooks(self)
            self._turn_index = 0
        # P6-EPISODES: signal only — never inline consolidate (E5) — P6-D04
        consolidate.request_consolidate(self, "session_switch")
        memlog.write_event(
            memlog.LOG_EVENT_ON_SESSION_SWITCH,
            session_id=new_session_id or "-",
            parent_session_id=parent_session_id or "-",
            reset=reset,
            rewound=rewound,
        )

    def on_pre_compress(self, messages: List[Dict[str, Any]]) -> str:
        # P6-EPISODES: waits for nothing — signal only (E5) — P6-D04
        consolidate.request_consolidate(self, "pre_compress")
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
            registry.remove(self._session_id or "", self)
            with self._lock:
                self._forget_state.clear_on_shutdown()
                if self._conn is not None:
                    try:
                        forget.clear_hold_meta(self._conn)
                    except Exception:
                        pass
                    store.release_lock(self._conn)
                    self._conn.close()
                    self._conn = None
        except Exception:
            ok = False
        memlog.write_event(memlog.LOG_EVENT_SHUTDOWN, ok=ok)
