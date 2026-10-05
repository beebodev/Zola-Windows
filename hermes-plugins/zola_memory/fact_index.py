"""Notify mirror and file-check fact index (P6-D01/D06)."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Set, Tuple  # Any used for optional provider

try:
    from . import forget, log as memlog, store
except ImportError:  # P6-STORE: flat unittest discover top — P6-D03
    import forget
    import log as memlog
    import store

# P6-STORE: reason strings for erase — P6-D06
REASON_REMOVE = forget.ERASE_REASON_REMOVE
REASON_FORGET_INTENT = forget.ERASE_REASON_FORGET_INTENT
REASON_FILE_CHECK = forget.ERASE_REASON_FILE_CHECK
REASON_PENDING_RETRY = forget.ERASE_REASON_PENDING_RETRY


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _find_unique_active(
    conn: sqlite3.Connection, target: str, old_text: str
) -> Tuple[Optional[str], bool]:
    """Return (fact_id, ambiguous) using Hermes substring uniqueness rules."""
    needle = store.normalize_entry(old_text)
    if not needle:
        return None, False
    rows = conn.execute(
        "SELECT id, text FROM facts WHERE target = ? AND state = ?",
        (target, store.STATE_ACTIVE),
    ).fetchall()
    matches = [r for r in rows if needle in r["text"]]
    if not matches:
        return None, False
    distinct = {r["text"] for r in matches}
    if len(distinct) > 1:
        return None, True
    return matches[0]["id"], False


def handle_memory_write(
    conn: sqlite3.Connection,
    hermes_home: Path,
    *,
    action: str,
    target: str,
    content: str,
    metadata: Optional[Dict[str, Any]],
    user_message: str,
    provider: Any = None,
) -> None:
    """Mirror a notified memory-tool write."""
    with store.locked(conn):
        tgt = store.TARGET_USER if target == "user" else store.TARGET_MEMORY
        meta = dict(metadata or {})
        action = (action or "").strip().lower()

        if action == "add":
            _notify_add(conn, hermes_home, tgt, content)
        elif action == "replace":
            _notify_replace(
                conn,
                hermes_home,
                tgt,
                content,
                meta.get("old_text"),
                user_message,
                provider=provider,
            )
        elif action == "remove":
            _notify_remove(
                conn,
                hermes_home,
                tgt,
                content,
                meta.get("old_text"),
                provider=provider,
            )


def _notify_add(conn: sqlite3.Connection, hermes_home: Path, target: str, content: str) -> None:
    text = store.normalize_entry(content)
    if not text:
        return
    now = _utc_now()
    fact_id = forget.new_id()
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            "INSERT INTO facts (id, target, text, tag, state, learned_at, indexed_at, "
            "updated_at, superseded_at, source) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?)",
            (
                fact_id,
                target,
                text,
                store.extract_tag(text),
                store.STATE_ACTIVE,
                now,
                now,
                store.SOURCE_NOTIFY,
            ),
        )
        conn.execute(
            "INSERT INTO facts_fts (fact_id, text) VALUES (?, ?)",
            (fact_id, text),
        )
        conn.execute("COMMIT")
        memlog.write_event(
            memlog.LOG_EVENT_FACT_ADD,
            fact_id=fact_id,
            target=target,
            source=store.SOURCE_NOTIFY,
        )
    except Exception:
        try:
            conn.execute("ROLLBACK")
        except Exception:
            pass
        # P6-STORE: uniqueness/constraint conflict → full file check, no guess — P6-D06
        _unmatched_fallback(conn, hermes_home, event_note="add_conflict")


def _notify_replace(
    conn: sqlite3.Connection,
    hermes_home: Path,
    target: str,
    content: str,
    old_text: Optional[str],
    user_message: str,
    *,
    provider: Any = None,
) -> None:
    new_text = store.normalize_entry(content)
    old = store.normalize_entry(old_text or "")
    if not new_text or not old:
        _unmatched_fallback(conn, hermes_home, event_note="replace_empty")
        return

    fact_id, ambiguous = _find_unique_active(conn, target, old)
    if fact_id is None or ambiguous:
        _unmatched_fallback(conn, hermes_home, event_note="replace_unmatched")
        return

    if forget.has_forget_intent(user_message):
        ok = forget.erase_fact(conn, fact_id, reason=REASON_FORGET_INTENT)
        # P6-FORGET: D2 — notify forget path marks the turn; file-check does not — P6-D06
        forget.mark_after_notify_cascade(provider, ok=ok)
        run_file_check(conn, hermes_home, force=True)
        return

    now = _utc_now()
    hist_id = forget.new_id()
    try:
        conn.execute("BEGIN IMMEDIATE")
        old_row = conn.execute(
            "SELECT text FROM facts WHERE id = ?",
            (fact_id,),
        ).fetchone()
        if old_row is None:
            conn.execute("ROLLBACK")
            _unmatched_fallback(conn, hermes_home, event_note="replace_missing")
            return
        conn.execute(
            "INSERT INTO fact_history (id, fact_id, text, superseded_at) VALUES (?, ?, ?, ?)",
            (hist_id, fact_id, old_row["text"], now),
        )
        conn.execute(
            "UPDATE facts SET text = ?, tag = ?, updated_at = ?, source = ? WHERE id = ?",
            (new_text, store.extract_tag(new_text), now, store.SOURCE_NOTIFY, fact_id),
        )
        conn.execute("DELETE FROM facts_fts WHERE fact_id = ?", (fact_id,))
        conn.execute(
            "INSERT INTO facts_fts (fact_id, text) VALUES (?, ?)",
            (fact_id, new_text),
        )
        conn.execute("COMMIT")
        memlog.write_event(
            memlog.LOG_EVENT_FACT_REPLACE,
            fact_id=fact_id,
            target=target,
            history=1,
        )
    except Exception:
        try:
            conn.execute("ROLLBACK")
        except Exception:
            pass
        _unmatched_fallback(conn, hermes_home, event_note="replace_conflict")


def _notify_remove(
    conn: sqlite3.Connection,
    hermes_home: Path,
    target: str,
    content: str,
    old_text: Optional[str],
    *,
    provider: Any = None,
) -> None:
    needle = store.normalize_entry(old_text or content or "")
    if not needle:
        return
    fact_id, ambiguous = _find_unique_active(conn, target, needle)
    if fact_id is None or ambiguous:
        # P6-STORE: exact-text erase + full file check (fail closed) — P6-D06
        rows = conn.execute(
            "SELECT id FROM facts WHERE target = ? AND state = ? AND text = ?",
            (target, store.STATE_ACTIVE, needle),
        ).fetchall()
        any_ok = False
        for row in rows:
            ok = forget.erase_fact(conn, row["id"], reason=REASON_REMOVE)
            any_ok = any_ok or ok
            if provider is not None:
                forget.end_hold_if_candidate_removed(provider, row["id"])
        # P6-FORGET: D2 — notification remove marks the turn (not file-check) — P6-D06
        forget.mark_after_notify_cascade(provider, ok=any_ok)
        _unmatched_fallback(conn, hermes_home, event_note="remove_unmatched")
        return
    ok = forget.erase_fact(conn, fact_id, reason=REASON_REMOVE)
    forget.mark_after_notify_cascade(provider, ok=ok)
    if provider is not None:
        forget.end_hold_if_candidate_removed(provider, fact_id)


def _unmatched_fallback(
    conn: sqlite3.Connection, hermes_home: Path, *, event_note: str
) -> None:
    before = _active_ids(conn)
    result = run_file_check(conn, hermes_home, force=True)
    after = _active_ids(conn)
    erased = len(before - after)
    added = len(after - before)
    memlog.write_event(
        memlog.LOG_EVENT_REPLACE_UNMATCHED,
        note=event_note,
        erased=erased,
        added=added,
        drift=result.get("drift", 0),
    )


def _active_ids(conn: sqlite3.Connection) -> Set[str]:
    return {
        r["id"]
        for r in conn.execute(
            "SELECT id FROM facts WHERE state = ?",
            (store.STATE_ACTIVE,),
        ).fetchall()
    }


def run_file_check(
    conn: sqlite3.Connection,
    hermes_home: Path,
    *,
    force: bool = False,
) -> Dict[str, Any]:
    """Reconcile active facts with USER.md / MEMORY.md. Files are authority."""
    import time

    with store.locked(conn):
        t0 = time.perf_counter()

        # P6-STORE: abort on unreadable existing file — no erases/adds/hash — P6-D01
        file_entries, read_ok = _load_file_entry_set(hermes_home)
        if not read_ok:
            elapsed = int((time.perf_counter() - t0) * 1000)
            memlog.write_event(
                memlog.LOG_EVENT_FILE_CHECK_READ_ERROR,
                elapsed_ms=elapsed,
                active_count=count_active(conn),
            )
            return {
                "ran": False,
                "read_error": True,
                "skipped_hash_match": False,
                "added": 0,
                "erased": 0,
                "drift": 0,
            }

        digest = store.combined_files_sha256(hermes_home)
        pending = forget._load_pending(conn)
        # P6-STORE: never hash-skip while pending erasures remain — P6-D06
        if not force:
            prev = store.meta_get(conn, store.META_FILES_SHA256) or ""
            if prev and prev == digest and not pending:
                elapsed = int((time.perf_counter() - t0) * 1000)
                memlog.write_event(
                    memlog.LOG_EVENT_FILE_CHECK,
                    ran=False,
                    drift=0,
                    added=0,
                    erased=0,
                    skipped_hash_match=True,
                    elapsed_ms=elapsed,
                )
                return {
                    "ran": False,
                    "skipped_hash_match": True,
                    "added": 0,
                    "erased": 0,
                    "drift": 0,
                }

        active = conn.execute(
            "SELECT id, target, text FROM facts WHERE state = ?",
            (store.STATE_ACTIVE,),
        ).fetchall()

        added = 0
        erased = 0
        erase_failures = 0
        file_keys = set(file_entries.keys())
        active_keys = {(r["target"], r["text"]) for r in active}

        for row in active:
            key = (row["target"], row["text"])
            if key not in file_keys:
                if forget.erase_fact(conn, row["id"], reason=REASON_FILE_CHECK):
                    erased += 1
                else:
                    erase_failures += 1

        for fact_id in list(forget._load_pending(conn)):
            row = conn.execute(
                "SELECT id FROM facts WHERE id = ?", (fact_id,)
            ).fetchone()
            if row is None:
                try:
                    conn.execute("BEGIN IMMEDIATE")
                    forget._remove_pending_erasure(conn, fact_id)
                    conn.execute("COMMIT")
                except Exception:
                    try:
                        conn.execute("ROLLBACK")
                    except Exception:
                        pass
                continue
            if forget.erase_fact(conn, fact_id, reason=REASON_PENDING_RETRY):
                erased += 1
            else:
                erase_failures += 1

        # Recompute active keys after erases for adds
        still_active = {
            (r["target"], r["text"])
            for r in conn.execute(
                "SELECT target, text FROM facts WHERE state = ?",
                (store.STATE_ACTIVE,),
            ).fetchall()
        }
        for target, text in file_keys - still_active:
            if _insert_file_check_fact(conn, target, text):
                added += 1

        # P6-STORE: do not advance files_sha256 if any erase failed — P6-D06
        if erase_failures == 0:
            try:
                conn.execute("BEGIN IMMEDIATE")
                store.meta_set(conn, store.META_FILES_SHA256, digest)
                conn.execute("COMMIT")
            except Exception:
                try:
                    conn.execute("ROLLBACK")
                except Exception:
                    pass

        drift = added + erased
        elapsed = int((time.perf_counter() - t0) * 1000)
        memlog.write_event(
            memlog.LOG_EVENT_FILE_CHECK,
            ran=True,
            drift=drift,
            added=added,
            erased=erased,
            erase_failures=erase_failures,
            skipped_hash_match=False,
            elapsed_ms=elapsed,
        )
        return {
            "ran": True,
            "skipped_hash_match": False,
            "added": added,
            "erased": erased,
            "erase_failures": erase_failures,
            "drift": drift,
        }


def _load_file_entry_set(
    hermes_home: Path,
) -> Tuple[Dict[Tuple[str, str], str], bool]:
    """Map (target, normalized_text) → text. Second value False if a file exists but is unreadable."""
    mem = store.memories_dir(hermes_home)
    out: Dict[Tuple[str, str], str] = {}
    for target, name in (
        (store.TARGET_USER, "USER.md"),
        (store.TARGET_MEMORY, "MEMORY.md"),
    ):
        raw, ok = store.read_memory_file(mem / name)
        if not ok:
            return {}, False
        for entry in store.parse_entries(raw):
            out[(target, entry)] = entry
    return out, True


def _insert_file_check_fact(conn: sqlite3.Connection, target: str, text: str) -> bool:
    fact_id = forget.new_id()
    now = _utc_now()
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            "INSERT INTO facts (id, target, text, tag, state, learned_at, indexed_at, "
            "updated_at, superseded_at, source) VALUES (?, ?, ?, ?, ?, NULL, ?, NULL, NULL, ?)",
            (
                fact_id,
                target,
                text,
                store.extract_tag(text),
                store.STATE_ACTIVE,
                now,
                store.SOURCE_FILE_CHECK,
            ),
        )
        conn.execute(
            "INSERT INTO facts_fts (fact_id, text) VALUES (?, ?)",
            (fact_id, text),
        )
        conn.execute("COMMIT")
        memlog.write_event(
            memlog.LOG_EVENT_FACT_ADD,
            fact_id=fact_id,
            target=target,
            source=store.SOURCE_FILE_CHECK,
        )
        return True
    except Exception:
        try:
            conn.execute("ROLLBACK")
        except Exception:
            pass
        return False


def count_active(conn: sqlite3.Connection) -> int:
    with store.locked(conn):
        return int(
            conn.execute(
                "SELECT COUNT(*) AS c FROM facts WHERE state = ?",
                (store.STATE_ACTIVE,),
            ).fetchone()["c"]
        )


def count_learned_null(conn: sqlite3.Connection) -> int:
    with store.locked(conn):
        return int(
            conn.execute(
                "SELECT COUNT(*) AS c FROM facts WHERE state = ? AND learned_at IS NULL",
                (store.STATE_ACTIVE,),
            ).fetchone()["c"]
        )
