"""Poll Gmail and Calendar into proactive.db (P9-D04 / P9-D09 / P9-D12).

No model, no tool handler, no origin ticket. Every store write goes through
proactive_store.
"""

from __future__ import annotations

import ctypes
import logging
import os
import sqlite3
import time
from ctypes import wintypes
from datetime import timedelta
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, List, Optional

try:
    from . import auth
    from . import background_read
    from . import loops
    from . import proactive_store
except ImportError:
    import auth
    import background_read
    import loops
    import proactive_store

GMAIL_POLL_SECONDS = 120
CALENDAR_POLL_SECONDS = 7200
CLOCK_JUMP_SECONDS = 15
ERROR_BACKOFF_CAP_SECONDS = 600
RECONNECT_RECHECK_SECONDS = 60
GMAIL_RECOVERY_WINDOW_DAYS = 7
GMAIL_RECOVERY_MARGIN_SECONDS = 120
WATCHER_LOG_MAX_BYTES = 1_000_000
WATCHER_LOG_BACKUPS = 3
EXIT_ALREADY_RUNNING = 2
CALENDAR_RESYNC_MARKER = "zola:calendar-resync"
_INSTANCE_MUTEX = "Local\\ZolaWatcher"
_instance_mutex_override: Optional[str] = None
_TERMINAL_INTENTS = frozenset({"cancelled", "status_change"})
_TRANSIENT_STATUS = frozenset({429, 500, 502, 503, 504})
_PERMANENT_STATUS = frozenset({400, 403})
_PERMANENT_REASONS = frozenset({"shape", "parse"})
_RECONNECT_ERRORS = frozenset(
    {
        auth.REASON_INVALID_GRANT,
        auth.REASON_SUB_MISMATCH,
        auth.REASON_ID_TOKEN_INVALID,
        auth.REASON_DECRYPT_FAILED,
        auth.REASON_MISSING_STORE,
        "missing_access_token",
    }
)

_log = logging.getLogger("zola_watcher")

_k32 = ctypes.WinDLL("kernel32", use_last_error=True)
_CreateMutexW = _k32.CreateMutexW
_CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
_CreateMutexW.restype = wintypes.HANDLE
_WaitForSingleObject = _k32.WaitForSingleObject
_WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
_WaitForSingleObject.restype = wintypes.DWORD
_ReleaseMutex = _k32.ReleaseMutex
_ReleaseMutex.argtypes = [wintypes.HANDLE]
_ReleaseMutex.restype = wintypes.BOOL
_CloseHandle = _k32.CloseHandle
_CloseHandle.argtypes = [wintypes.HANDLE]
_CloseHandle.restype = wintypes.BOOL
_OpenProcess = _k32.OpenProcess
_OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
_OpenProcess.restype = wintypes.HANDLE
_PROCESS_QUERY = 0x1000
_WAIT_TIMEOUT = 0x00000102

_instance_handle: Any = None


def _warn(reason: str, **fields: Any) -> None:
    # P9-WATCH: metadata only. Callers must not pass mail or calendar text — P9-D04
    parts = [f"reason={reason}"]
    for key in ("source", "ok", "new", "ms", "class"):
        if key in fields and fields[key] is not None:
            parts.append(f"{key}={fields[key]}")
    _log.warning("zola_watcher %s", " ".join(parts))


def _poll(source: str, *, ok: int, new: int, ms: int, skipped_not_inbox: Optional[int] = None) -> None:
    if skipped_not_inbox is None:
        _log.info("zola_watcher.poll source=%s ok=%s new=%s ms=%s", source, ok, new, ms)
        return
    _log.info(
        "zola_watcher.poll source=%s ok=%s new=%s ms=%s skipped_not_inbox=%s",
        source,
        ok,
        new,
        ms,
        skipped_not_inbox,
    )


def set_instance_mutex_name_for_tests(name: Optional[str]) -> None:
    # P9-WATCH: tests name their own instance mutex so a live watcher keeps its lock — P9-D04
    global _instance_mutex_override
    _instance_mutex_override = name


def _instance_mutex_name() -> str:
    return _instance_mutex_override or _INSTANCE_MUTEX


def acquire_instance() -> bool:
    """False when another watcher already holds the mutex."""
    global _instance_handle
    handle = _CreateMutexW(None, False, _instance_mutex_name())
    if not handle:
        return False
    waited = _WaitForSingleObject(handle, 0)
    if waited == _WAIT_TIMEOUT:
        _CloseHandle(handle)
        _warn("already_running")
        return False
    _instance_handle = handle
    return True


def parent_alive(pid: int) -> bool:
    if pid <= 0:
        return True
    handle = _OpenProcess(_PROCESS_QUERY, False, pid)
    if not handle:
        return False
    _CloseHandle(handle)
    return True


def catch_up(previous_wall: float, previous_mono: float, wall: float, mono: float) -> bool:
    # P9-WATCH: a sleep moves the wall clock and not the monotonic clock — P9-D02
    return (wall - previous_wall) - (mono - previous_mono) > CLOCK_JUMP_SECONDS


def due(
    *,
    last_mono: Optional[float],
    previous_wall: Optional[float],
    previous_mono: Optional[float],
    wall: float,
    mono: float,
    interval: float,
    reconnect_wait: bool,
) -> bool:
    if last_mono is None:
        return True
    if previous_wall is not None and previous_mono is not None and catch_up(
        previous_wall, previous_mono, wall, mono
    ):
        return True
    wait = RECONNECT_RECHECK_SECONDS if reconnect_wait else interval
    return (mono - last_mono) >= wait


def _iso(now: Any) -> str:
    return proactive_store._iso(proactive_store._now(now))


def _store_reason(result: Dict[str, Any]) -> str:
    return str(result.get("refused_reason") or result.get("reason") or "")


def _matching(conn: sqlite3.Connection, view: Dict[str, Any], intents: Any) -> List[Dict[str, Any]]:
    listed = proactive_store.list_open_loop_predicates(conn)
    if not listed.get("ok"):
        raise RuntimeError(_store_reason(listed) or "loops")
    found = []
    for loop in listed.get("loops") or []:
        if intents is not None and loop.get("intent") not in intents:
            continue
        if loops.evaluate(loop.get("predicate") or {}, view):
            found.append(loop)
    return found


def _finish_item(
    conn: sqlite3.Connection,
    item_id: str,
    view: Dict[str, Any],
    now: Any,
    *,
    close_terminal: bool,
) -> str:
    # P9-WATCH: evaluate replays too; a refusal is a named WARN — P9-D09
    try:
        matched = _matching(conn, view, None)
    except Exception:
        _warn("evaluate", source=view.get("source") or "-")
        return "held"
    for loop in matched:
        noted = proactive_store.note_loop_match_on_loop(conn, loop["id"], now=now)
        if not noted.get("ok"):
            reason = _store_reason(noted) or "match"
            if reason == "locked":
                return "held"
            _warn(reason, source=view.get("source") or "-")
            return "held"
    if not matched:
        return "ok"
    marked = proactive_store.mark_loop_eligible(conn, item_id, now=now)
    if not marked.get("ok"):
        if _store_reason(marked) == "locked":
            return "held"
        state = proactive_store.item_loop_state(conn, item_id)
        if (
            state.get("ok")
            and state.get("eligibility") == "eligible"
            and int(state.get("loop_matched") or 0) == 1
        ):
            pass
        elif state.get("ok") and state.get("eligibility") == "eligible":
            backed = proactive_store.set_loop_matched(conn, item_id, now=now)
            if not backed.get("ok"):
                _warn(_store_reason(backed) or "loop_not_matched", source=view.get("source") or "-")
                if _store_reason(backed) == "locked":
                    return "held"
        else:
            if state.get("closed"):
                reason = "closed"
            elif state.get("eligibility") in ("suppressed", "expired"):
                reason = str(state.get("eligibility"))
            else:
                reason = "loop_not_matched" if state.get("eligibility") == "pending" else "not_eligible"
            _warn(reason, source=view.get("source") or "-")
    if close_terminal:
        for loop in matched:
            if loop.get("intent") not in _TERMINAL_INTENTS:
                continue
            closed = proactive_store.close_loop_from_match(conn, loop["id"], loop["intent"])
            if not closed.get("ok") and not closed.get("already"):
                if _store_reason(closed) == "locked":
                    return "held"
                _warn(_store_reason(closed) or "close", source="calendar")
    return "ok"


def _reconnect_blocked(conn: sqlite3.Connection, source: str) -> bool:
    status = auth.store_status()
    reason = status.get("needs_reconnect")
    if not reason:
        proactive_store.write_watcher_health(conn, needs_reconnect=False)
        return False
    # P9-WATCH: local store only; this path does not call Google — P9-D03
    proactive_store.write_watcher_health(
        conn,
        needs_reconnect=True,
        gmail_error=str(reason) if source == "gmail" else None,
        calendar_error=str(reason) if source == "calendar" else None,
    )
    _warn("needs_reconnect", source=source)
    return True


def _cycle_error(source: str, exc: BaseException) -> Dict[str, Any]:
    # P9-WATCH: a cycle exception stays in the process; the log keeps the class only — P9-D04
    name = type(exc).__name__
    if isinstance(exc, RuntimeError) and str(exc) in _RECONNECT_ERRORS:
        auth.set_reconnect_reason(str(exc))
        return {"ok": False, "skipped": True, "reason": "needs_reconnect", "new": 0}
    if isinstance(exc, background_read.ReadError):
        reason = f"http_{exc.status}" if exc.status else (exc.reason or "transport")
        _warn(reason, source=source)
        return {"ok": False, "held": True, "reason": reason, "new": 0}
    _warn("unexpected", source=source, **{"class": name})
    return {"ok": False, "held": True, "reason": "unexpected", "new": 0, "class": name}


def _reject(conn: sqlite3.Connection, source: str, raw_id: str, error_class: str, *, terminal: bool, now: Any) -> str:
    noted = proactive_store.note_watcher_reject(
        conn,
        source=source,
        source_id_hash=proactive_store.address_hash(raw_id),
        error_class=error_class,
        terminal=terminal,
        now=now,
    )
    if not noted.get("ok"):
        return "held"
    _warn(error_class, source=source)
    return "ok" if noted.get("disposition") == "terminal" else "held"


def _record_cycle(conn: sqlite3.Connection, source: str, result: Dict[str, Any], *, now: Any) -> None:
    if result.get("reason") == "needs_reconnect":
        proactive_store.write_watcher_health(
            conn,
            needs_reconnect=True,
            gmail_error=auth.get_reconnect_reason() if source == "gmail" else None,
            calendar_error=auth.get_reconnect_reason() if source == "calendar" else None,
            now=now,
        )
        _warn("needs_reconnect", source=source)
        return
    if result.get("ok"):
        return
    error = result.get("class") or result.get("reason")
    if not error:
        return
    proactive_store.write_watcher_health(
        conn,
        gmail_error=str(error) if source == "gmail" else None,
        calendar_error=str(error) if source == "calendar" else None,
        now=now,
    )


def run_gmail(conn: sqlite3.Connection, now: Any = None) -> Dict[str, Any]:
    started = time.monotonic()
    if _reconnect_blocked(conn, "gmail"):
        return {"ok": False, "skipped": True, "reason": "needs_reconnect", "new": 0}
    try:
        return _run_gmail(conn, now, started)
    except auth.RefreshLockTimeout:
        result = {"ok": False, "held": True, "reason": "refresh_lock_timeout", "new": 0}
        _warn("refresh_lock_timeout", source="gmail")
    except sqlite3.OperationalError as exc:
        if "locked" in str(exc).lower() or "busy" in str(exc).lower():
            _warn("db_locked", source="gmail")
            return {"ok": False, "skipped": True, "reason": "db_locked", "new": 0}
        result = _cycle_error("gmail", exc)
    except Exception as exc:
        result = _cycle_error("gmail", exc)
    _record_cycle(conn, "gmail", result, now=now)
    return result


def _run_gmail(conn: sqlite3.Connection, now: Any, started: float) -> Dict[str, Any]:
    cursor = proactive_store.read_cursor(conn, "gmail", "mailbox")
    if not cursor.get("ok"):
        reason = "db_locked" if _store_reason(cursor) == "locked" else (_store_reason(cursor) or "cursor")
        _warn(reason, source="gmail")
        return {"ok": False, "skipped": reason == "db_locked", "held": True, "reason": reason, "new": 0}
    if not cursor.get("cursor_value"):
        try:
            profile = background_read.gmail_profile()
        except background_read.ReadError as exc:
            reason = f"http_{exc.status}" if exc.status else (exc.reason or "transport")
            proactive_store.write_watcher_health(conn, gmail_error=reason, now=now)
            _warn(reason, source="gmail")
            return {"ok": False, "held": True, "reason": reason, "new": 0}
        wrote = proactive_store.write_cursor(conn, "gmail", "mailbox", profile["history_id"], now=now)
        if not wrote.get("ok"):
            reason = "db_locked" if _store_reason(wrote) == "locked" else (_store_reason(wrote) or "cursor")
            _warn(reason, source="gmail")
            return {"ok": False, "skipped": reason == "db_locked", "held": True, "reason": reason, "new": 0}
        proactive_store.write_watcher_health(conn, gmail_ok=True, needs_reconnect=False, now=now)
        _poll("gmail", ok=1, new=0, ms=int((time.monotonic() - started) * 1000), skipped_not_inbox=0)
        return {"ok": True, "new": 0, "baseline": True}
    start_id = str(cursor["cursor_value"])
    try:
        new, history_id, held, skipped = _history_pages(conn, start_id, now)
    except background_read.ReadError as exc:
        if exc.status == 404:
            recovered = _recover_gmail(conn, now)
            recovered["ms"] = int((time.monotonic() - started) * 1000)
            return recovered
        reason = f"http_{exc.status}" if exc.status else exc.reason
        proactive_store.write_watcher_health(conn, gmail_error=reason, now=now)
        _warn(reason, source="gmail")
        return {"ok": False, "held": True, "reason": reason, "new": 0}
    if held:
        return {"ok": False, "held": True, "reason": "partial", "new": new}
    if history_id:
        wrote = proactive_store.write_cursor(conn, "gmail", "mailbox", history_id, now=now)
        if not wrote.get("ok"):
            return {"ok": False, "held": True, "reason": _store_reason(wrote), "new": new}
    proactive_store.write_watcher_health(conn, gmail_ok=True, needs_reconnect=False, now=now)
    _poll(
        "gmail",
        ok=1,
        new=new,
        ms=int((time.monotonic() - started) * 1000),
        skipped_not_inbox=skipped,
    )
    return {"ok": True, "new": new, "skipped_not_inbox": skipped}


def _history_pages(conn: sqlite3.Connection, start_id: str, now: Any):
    page = ""
    new = 0
    skipped = 0
    history_id = ""
    while True:
        body = background_read.gmail_history(start_id, page)
        history_id = body.get("history_id") or history_id
        for added in body.get("added") or []:
            outcome, created, skip = _ingest_message(
                conn, added["message_id"], added.get("thread_id") or "", now
            )
            if outcome == "held":
                return new, history_id, True, skipped
            if skip:
                skipped += 1
            else:
                new += 1 if created else 0
        page = body.get("next_page_token") or ""
        if not page:
            return new, history_id, False, skipped


def _message_failure(exc: background_read.ReadError) -> str:
    # P9-WATCH: transport and 429/5xx stay held and do not count toward the cap — P9-D04
    if exc.reason == "transport" or exc.status in _TRANSIENT_STATUS:
        return "transient"
    if exc.status == 404:
        return "gone"
    if exc.status in _PERMANENT_STATUS or exc.reason in _PERMANENT_REASONS:
        return "permanent"
    return "transient"


def _ingest_message(
    conn: sqlite3.Connection,
    message_id: str,
    thread_id: str,
    now: Any,
    *,
    not_before_ms: Optional[int] = None,
):
    try:
        message = background_read.gmail_message(message_id)
    except background_read.ReadError as exc:
        kind = _message_failure(exc)
        if kind == "transient":
            reason = f"http_{exc.status}" if exc.status else "transport"
            proactive_store.write_watcher_health(conn, gmail_error=reason, now=now)
            _warn(reason, source="gmail")
            return "held", False, False
        error_class = "http_404" if kind == "gone" else (
            f"http_{exc.status}" if exc.status else exc.reason
        )
        outcome = _reject(
            conn,
            "gmail",
            message_id,
            error_class,
            terminal=kind == "gone",
            now=now,
        )
        return outcome, False, False
    # P9-WATCH: a message outside INBOX is finished; the cursor may pass it — P9-D04
    labels = {str(label).upper() for label in (message.get("labels") or [])}
    if "INBOX" not in labels:
        return "ok", False, True
    if not_before_ms is not None:
        raw = str(message.get("internal_date") or "")
        if raw.isdigit() and int(raw) < not_before_ms:
            return "ok", False, False
    inserted = proactive_store.insert_item(
        conn,
        source="gmail",
        message_id=message.get("message_id") or message_id,
        thread_id=message.get("thread_id") or thread_id,
        sender_address=message.get("from_address") or "",
        sender_display_name=message.get("from_name") or "",
        subject=message.get("subject") or "",
        snippet=message.get("snippet") or "",
        body=message.get("body") or "",
        now=now,
    )
    if not inserted.get("ok"):
        if _store_reason(inserted) == "locked":
            return "held", False, False
        _warn(_store_reason(inserted) or "insert", source="gmail")
        return "held", False, False
    view = {
        "source": "gmail",
        "message_id": message.get("message_id") or message_id,
        "thread_id": message.get("thread_id") or thread_id,
        "sender_address_hash": proactive_store.address_hash(message.get("from_address") or ""),
        "internal_date": str(message.get("internal_date") or ""),
        "detected_at": _iso(now),
    }
    if _finish_item(conn, inserted["id"], view, now, close_terminal=False) == "held":
        return "held", False, False
    return "ok", bool(inserted.get("created")), False


def _recovery_cutoff_ms(updated_at: Optional[str]) -> Optional[int]:
    if not updated_at:
        return None
    try:
        stamp = proactive_store._parse(updated_at) - timedelta(seconds=GMAIL_RECOVERY_MARGIN_SECONDS)
    except (TypeError, ValueError):
        return None
    return int(stamp.timestamp() * 1000)


def _recover_gmail(conn: sqlite3.Connection, now: Any) -> Dict[str, Any]:
    # P9-WATCH: historyId is taken before the list, and written after the candidates — P9-D04
    try:
        profile = background_read.gmail_profile()
    except background_read.ReadError as exc:
        reason = f"http_{exc.status}" if exc.status else exc.reason
        _warn(reason, source="gmail")
        return {"ok": False, "held": True, "reason": reason, "new": 0}
    history_id = profile["history_id"]
    cursor = proactive_store.read_cursor(conn, "gmail", "mailbox")
    if not cursor.get("ok"):
        return {"ok": False, "held": True, "reason": _store_reason(cursor), "new": 0}
    cutoff = _recovery_cutoff_ms(cursor.get("updated_at"))
    page = ""
    new = 0
    skipped = 0
    while True:
        try:
            listed = background_read.gmail_recovery_list(GMAIL_RECOVERY_WINDOW_DAYS, page)
        except background_read.ReadError as exc:
            reason = f"http_{exc.status}" if exc.status else exc.reason
            _warn(reason, source="gmail")
            return {"ok": False, "held": True, "reason": reason, "new": new}
        for item in listed.get("messages") or []:
            known = proactive_store.gmail_message_known(conn, item["message_id"])
            if not known.get("ok"):
                return {"ok": False, "held": True, "reason": _store_reason(known), "new": new}
            if known.get("known"):
                continue
            outcome, created, skip = _ingest_message(
                conn,
                item["message_id"],
                item.get("thread_id") or "",
                now,
                not_before_ms=cutoff,
            )
            if outcome == "held":
                return {"ok": False, "held": True, "reason": "partial", "new": new}
            if skip:
                skipped += 1
            else:
                new += 1 if created else 0
        page = listed.get("next_page_token") or ""
        if not page:
            break
    wrote = proactive_store.write_cursor(conn, "gmail", "mailbox", history_id, now=now)
    if not wrote.get("ok"):
        return {"ok": False, "held": True, "reason": _store_reason(wrote), "new": new}
    proactive_store.write_watcher_health(
        conn, gmail_ok=True, recovery=True, needs_reconnect=False, now=now
    )
    _poll("gmail", ok=1, new=new, ms=0, skipped_not_inbox=skipped)
    return {"ok": True, "new": new, "recovery": True}


def run_calendar(conn: sqlite3.Connection, now: Any = None) -> Dict[str, Any]:
    started = time.monotonic()
    if _reconnect_blocked(conn, "calendar"):
        return {"ok": False, "skipped": True, "reason": "needs_reconnect", "new": 0}
    try:
        result = _run_calendar(conn, now)
    except auth.RefreshLockTimeout:
        result = {"ok": False, "held": True, "reason": "refresh_lock_timeout", "new": 0}
        _warn("refresh_lock_timeout", source="calendar")
        _record_cycle(conn, "calendar", result, now=now)
        return result
    except sqlite3.OperationalError as exc:
        if "locked" in str(exc).lower() or "busy" in str(exc).lower():
            _warn("db_locked", source="calendar")
            return {"ok": False, "skipped": True, "reason": "db_locked", "new": 0}
        result = _cycle_error("calendar", exc)
        _record_cycle(conn, "calendar", result, now=now)
        return result
    except Exception as exc:
        result = _cycle_error("calendar", exc)
        _record_cycle(conn, "calendar", result, now=now)
        return result
    result["ms"] = int((time.monotonic() - started) * 1000)
    if result.get("ok"):
        proactive_store.write_watcher_health(conn, calendar_ok=True, needs_reconnect=False, now=now)
        _poll("calendar", ok=1, new=int(result.get("new") or 0), ms=result["ms"])
    return result


def _run_calendar(conn: sqlite3.Connection, now: Any) -> Dict[str, Any]:
    page = ""
    ids: List[str] = []
    while True:
        try:
            listed = background_read.calendar_ids(page)
        except background_read.ReadError as exc:
            reason = f"http_{exc.status}" if exc.status else exc.reason
            proactive_store.write_watcher_health(conn, calendar_error=reason, now=now)
            _warn(reason, source="calendar")
            return {"ok": False, "held": True, "reason": reason, "new": 0}
        ids.extend(listed.get("ids") or [])
        page = listed.get("next_page_token") or ""
        if not page:
            break
    new = 0
    failed: List[str] = []
    for calendar_id in ids:
        outcome = _sync_calendar(conn, calendar_id, now)
        if outcome.get("held"):
            reason = outcome.get("reason") or "partial"
            if reason == "locked":
                reason = "db_locked"
            # P9-WATCH: one calendar keeps its cursor; the others still finish — P9-D04
            _warn(reason, source="calendar")
            failed.append(reason)
            continue
        new += int(outcome.get("new") or 0)
    if failed:
        summary = f"{failed[0]} failed={len(failed)}"
        proactive_store.write_watcher_health(conn, calendar_error=summary, now=now)
        return {"ok": False, "held": True, "reason": summary, "new": new}
    return {"ok": True, "new": new}


def _sync_calendar(
    conn: sqlite3.Connection,
    calendar_id: str,
    now: Any,
) -> Dict[str, Any]:
    # P9-WATCH: the cursor decides the mode. Empty stays a first sync until the token — P9-D04
    cursor = proactive_store.read_cursor(conn, "calendar", calendar_id)
    if not cursor.get("ok"):
        return {"held": True, "reason": _store_reason(cursor) or "cursor", "new": 0}
    value = str(cursor.get("cursor_value") or "")
    if not value:
        mode = "baseline"
    elif value == CALENDAR_RESYNC_MARKER:
        mode = "recovery"
    else:
        mode = "incremental"
    page = ""
    sync = value if mode == "incremental" else ""
    new = 0
    while True:
        try:
            body = background_read.calendar_events(
                calendar_id,
                page_token=page,
                sync_token="" if page else sync,
            )
        except background_read.ReadError as exc:
            if exc.status == 410 and mode == "incremental":
                wrote = proactive_store.write_cursor(
                    conn, "calendar", calendar_id, CALENDAR_RESYNC_MARKER, now=now
                )
                if not wrote.get("ok"):
                    return {"held": True, "reason": _store_reason(wrote) or "cursor", "new": new}
                proactive_store.write_watcher_health(conn, recovery=True, calendar_error="gone", now=now)
                return _sync_calendar(conn, calendar_id, now)
            reason = "http_410" if exc.status == 410 else (f"http_{exc.status}" if exc.status else exc.reason)
            return {"held": True, "reason": reason, "new": new}
        for event in body.get("events") or []:
            applied = _apply_event(conn, calendar_id, event, now, mode=mode)
            if applied == "held":
                return {"held": True, "reason": "partial", "new": new}
            new += int(applied)
        page = body.get("next_page_token") or ""
        if page:
            continue
        token = body.get("next_sync_token") or ""
        if not token:
            return {"held": True, "reason": "missing_token", "new": new}
        wrote = proactive_store.write_cursor(conn, "calendar", calendar_id, token, now=now)
        if not wrote.get("ok"):
            return {"held": True, "reason": _store_reason(wrote) or "cursor", "new": new}
        return {"held": False, "new": new}


def _apply_event(
    conn: sqlite3.Connection,
    calendar_id: str,
    event: Dict[str, Any],
    now: Any,
    *,
    mode: str,
) -> Any:
    known = proactive_store.get_calendar_event(conn, calendar_id, event["event_id"])
    if not known.get("ok"):
        return "held"
    baseline = mode == "baseline"
    recovering = mode == "recovery"
    view = {
        "source": "calendar",
        "event_id": event["event_id"],
        "calendar_status": event.get("calendar_status") or "",
        "event_updated": str(event.get("event_updated") or ""),
        "detected_at": _iso(now),
    }
    try:
        matches = [] if baseline else _matching(conn, view, _TERMINAL_INTENTS)
    except Exception:
        _warn("evaluate", source="calendar")
        return "held"
    updated_changed = known.get("known") and known.get("event_updated") != event.get("event_updated")
    unknown_during_recovery = recovering and not known.get("known")
    should_insert = (
        (not baseline)
        and not unknown_during_recovery
        and ((not known.get("known")) or (updated_changed and bool(matches)))
    )
    item_id = None
    created = False
    if should_insert:
        inserted = proactive_store.insert_item(
            conn,
            source="calendar",
            event_id=event["event_id"],
            event_updated=event.get("event_updated") or "",
            calendar_status=event.get("calendar_status") or "",
            now=now,
        )
        if not inserted.get("ok"):
            return "held"
        item_id = inserted["id"]
        created = bool(inserted.get("created"))
    else:
        found = proactive_store.find_item_id(
            conn,
            source="calendar",
            event_id=event["event_id"],
            event_updated=event.get("event_updated") or "",
        )
        if not found.get("ok"):
            return "held"
        item_id = found.get("id")
    if item_id and not baseline:
        if _finish_item(conn, item_id, view, now, close_terminal=True) == "held":
            return "held"
    saved = proactive_store.save_calendar_event(
        conn,
        calendar_id=calendar_id,
        event_id=event["event_id"],
        event_updated=event.get("event_updated") or "",
        calendar_status=event.get("calendar_status") or "",
        start_at=event.get("start_at") or "",
        end_at=event.get("end_at") or "",
        recurring_event_id=event.get("recurring_event_id") or "",
        original_start=event.get("original_start") or "",
        now=now,
    )
    if not saved.get("ok"):
        return "held"
    return 1 if created else 0


def _purge_counts(conn: sqlite3.Connection, now: Any = None) -> None:
    # P9-WATCH: retention still runs while serve is down — P9-D07
    result = proactive_store.purge_retention(conn, now=now)
    if not result.get("ok"):
        _warn(_store_reason(result) or "purge")
        return
    _log.info(
        "zola_watcher.purge bodies=%s texts=%s deliveries=%s loops=%s",
        result.get("bodies", 0),
        result.get("texts", 0),
        result.get("deliveries_deleted", 0),
        result.get("loops_expired", 0),
    )


def configure_logging(log_path: str) -> None:
    _log.setLevel(logging.INFO)
    _log.handlers.clear()
    handler = RotatingFileHandler(
        log_path,
        maxBytes=WATCHER_LOG_MAX_BYTES,
        backupCount=WATCHER_LOG_BACKUPS,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    _log.addHandler(handler)


def main() -> int:
    # P9-WATCH: one process; a second launch logs and exits — P9-D04
    if not acquire_instance():
        return EXIT_ALREADY_RUNNING
    home = os.environ.get("HERMES_HOME") or ""
    if home:
        log_dir = os.path.join(home, "logs")
        os.makedirs(log_dir, exist_ok=True)
        configure_logging(os.path.join(log_dir, "zola_watcher.log"))
    parent = int(os.environ.get("ZOLA_WATCHER_PARENT_PID") or "0")
    gmail_mono: Optional[float] = None
    calendar_mono: Optional[float] = None
    previous_wall: Optional[float] = None
    previous_mono: Optional[float] = None
    gmail_reconnect = False
    calendar_reconnect = False
    gmail_backoff = 0.0
    calendar_backoff = 0.0
    purged_at: Optional[float] = None
    while True:
        if parent and not parent_alive(parent):
            return 0
        wall = time.time()
        mono = time.monotonic()
        path = proactive_store.profile_db_path()
        if path is None:
            time.sleep(1)
            continue
        try:
            conn = proactive_store.connect(path)
        except sqlite3.OperationalError as exc:
            if "locked" in str(exc).lower() or "busy" in str(exc).lower():
                _warn("db_locked")
            time.sleep(1)
            continue
        try:
            if purged_at is None or (mono - purged_at) >= proactive_store.PURGE_INTERVAL_SECONDS:
                _purge_counts(conn)
                purged_at = time.monotonic()
            if due(
                last_mono=gmail_mono,
                previous_wall=previous_wall,
                previous_mono=previous_mono,
                wall=wall,
                mono=mono,
                interval=GMAIL_POLL_SECONDS + gmail_backoff,
                reconnect_wait=gmail_reconnect,
            ):
                try:
                    result = run_gmail(conn)
                except Exception as exc:
                    result = _cycle_error("gmail", exc)
                    _record_cycle(conn, "gmail", result, now=None)
                gmail_mono = time.monotonic()
                gmail_reconnect = result.get("reason") == "needs_reconnect"
                if result.get("ok"):
                    gmail_backoff = 0.0
                elif not gmail_reconnect:
                    gmail_backoff = min(ERROR_BACKOFF_CAP_SECONDS, max(30.0, gmail_backoff * 2 or 30.0))
            if due(
                last_mono=calendar_mono,
                previous_wall=previous_wall,
                previous_mono=previous_mono,
                wall=wall,
                mono=mono,
                interval=CALENDAR_POLL_SECONDS + calendar_backoff,
                reconnect_wait=calendar_reconnect,
            ):
                try:
                    result = run_calendar(conn)
                except Exception as exc:
                    result = _cycle_error("calendar", exc)
                    _record_cycle(conn, "calendar", result, now=None)
                calendar_mono = time.monotonic()
                calendar_reconnect = result.get("reason") == "needs_reconnect"
                if result.get("ok"):
                    calendar_backoff = 0.0
                elif not calendar_reconnect:
                    calendar_backoff = min(
                        ERROR_BACKOFF_CAP_SECONDS, max(30.0, calendar_backoff * 2 or 30.0)
                    )
        finally:
            conn.close()
        previous_wall = wall
        previous_mono = mono
        time.sleep(1)


if __name__ == "__main__":
    raise SystemExit(main())
