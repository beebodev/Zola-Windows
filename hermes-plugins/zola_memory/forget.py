"""Forget-intent recognition and transactional fact erase (P6-D06)."""

from __future__ import annotations

import json
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Optional

try:
    from . import log as memlog
except ImportError:  # P6-STORE: flat unittest discover top — P6-D03
    import log as memlog

# P6-STORE: forget-intent phrases — escalation only — P6-D06
FORGET_INTENT_PHRASES = (
    "forget",
    "don't remember",
    "do not remember",
    "don't keep",
    "do not keep",
    "stop remembering",
    "delete",
    "erase",
    "remove that",
    "get rid of",
    "no longer remember",
)

# P6-STORE: bare "forget" cancelled inside these phrases — P6-D06
FORGET_INTENT_EXCLUSIONS = (
    "don't forget",
    "do not forget",
    "never forget",
    "won't forget",
    "not forget",
)

RECORD_KIND_FACT = "fact"
ERASE_REASON_REMOVE = "remove"
ERASE_REASON_FORGET_INTENT = "forget_intent"
ERASE_REASON_FILE_CHECK = "file_check"
ERASE_REASON_PENDING_RETRY = "pending_retry"

META_PENDING_ERASURES = "pending_erasures"

# P6-STORE: test hook to simulate mid-erase failure — P6-D06
_erase_failure_hook: Optional[Callable[[], None]] = None


def set_erase_failure_hook(hook: Optional[Callable[[], None]]) -> None:
    global _erase_failure_hook
    _erase_failure_hook = hook


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_apostrophes(message: str) -> str:
    # P6-STORE: curly quotes → ASCII before phrase match — P6-D06
    return (message or "").replace("\u2019", "'").replace("\u2018", "'")


def has_forget_intent(message: str) -> bool:
    """True when the current user message matches a forget phrase (exclusions applied)."""
    if not message:
        return False
    lower = normalize_apostrophes(message).lower()
    exclusion_spans = []
    for excl in FORGET_INTENT_EXCLUSIONS:
        for match in re.finditer(re.escape(excl), lower):
            exclusion_spans.append((match.start(), match.end()))

    def _inside_exclusion(start: int, end: int) -> bool:
        return any(es <= start and end <= ee for es, ee in exclusion_spans)

    for phrase in FORGET_INTENT_PHRASES:
        pattern = r"(?<!\w)" + re.escape(phrase) + r"(?!\w)"
        for match in re.finditer(pattern, lower):
            if phrase == "forget" and _inside_exclusion(match.start(), match.end()):
                continue
            return True
    return False


def erase_fact(
    conn: sqlite3.Connection,
    fact_id: str,
    *,
    reason: str,
) -> bool:
    """Erase fact + FTS + history and write a content-free tombstone in one IMMEDIATE txn.

    On failure: roll back completely, then best-effort mark ``pending_erasures``.
    Returns True on committed erase.
    """
    try:
        from . import store as _store
    except ImportError:
        import store as _store

    with _store.locked(conn):
        try:
            conn.execute("BEGIN IMMEDIATE")
            cur = conn.execute(
                "SELECT id FROM facts WHERE id = ?",
                (fact_id,),
            )
            if cur.fetchone() is None:
                conn.execute("COMMIT")
                return False

            hist = conn.execute(
                "SELECT COUNT(*) FROM fact_history WHERE fact_id = ?",
                (fact_id,),
            ).fetchone()[0]
            fts = conn.execute(
                "SELECT COUNT(*) FROM facts_fts WHERE fact_id = ?",
                (fact_id,),
            ).fetchone()[0]

            conn.execute("DELETE FROM fact_history WHERE fact_id = ?", (fact_id,))
            conn.execute("DELETE FROM facts_fts WHERE fact_id = ?", (fact_id,))
            conn.execute("DELETE FROM facts WHERE id = ?", (fact_id,))

            # P6-STORE: injected failure after deletes, before tombstone — P6-D06
            if _erase_failure_hook is not None:
                _erase_failure_hook()

            counts = {
                "fact_rows": 1,
                "history_rows": int(hist),
                "fts_rows": int(fts),
            }
            conn.execute(
                "INSERT OR REPLACE INTO tombstones (id, record_kind, erased_at, counts_json) "
                "VALUES (?, ?, ?, ?)",
                (
                    fact_id,
                    RECORD_KIND_FACT,
                    _utc_now(),
                    json.dumps(counts, separators=(",", ":")),
                ),
            )
            _remove_pending_erasure(conn, fact_id)
            conn.execute("COMMIT")
            memlog.write_event(
                memlog.LOG_EVENT_FACT_ERASE,
                fact_id=fact_id,
                reason=reason,
                history_rows=int(hist),
                ok=True,
            )
            return True
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
            memlog.write_event(memlog.LOG_EVENT_ERASE_ROLLBACK, fact_id=fact_id)
            _mark_pending_erasure(conn, fact_id)
            memlog.write_event(
                memlog.LOG_EVENT_FACT_ERASE,
                fact_id=fact_id,
                reason=reason,
                history_rows=0,
                ok=False,
            )
            return False


def _load_pending(conn: sqlite3.Connection) -> list[str]:
    row = conn.execute(
        "SELECT value FROM meta WHERE key = ?",
        (META_PENDING_ERASURES,),
    ).fetchone()
    if not row:
        return []
    try:
        data = json.loads(row[0])
        return [str(x) for x in data] if isinstance(data, list) else []
    except Exception:
        return []


def _save_pending(conn: sqlite3.Connection, ids: list[str]) -> None:
    conn.execute(
        "INSERT INTO meta (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (META_PENDING_ERASURES, json.dumps(ids, separators=(",", ":"))),
    )


def _mark_pending_erasure(conn: sqlite3.Connection, fact_id: str) -> None:
    ok = False
    try:
        conn.execute("BEGIN IMMEDIATE")
        ids = _load_pending(conn)
        if fact_id not in ids:
            ids.append(fact_id)
        _save_pending(conn, ids)
        conn.execute("COMMIT")
        ok = True
    except Exception:
        try:
            conn.execute("ROLLBACK")
        except Exception:
            pass
    memlog.write_event(memlog.LOG_EVENT_PENDING_ERASURE_MARK, fact_id=fact_id, ok=ok)


def _remove_pending_erasure(conn: sqlite3.Connection, fact_id: str) -> None:
    ids = [x for x in _load_pending(conn) if x != fact_id]
    _save_pending(conn, ids)


def new_id() -> str:
    return str(uuid.uuid4())
