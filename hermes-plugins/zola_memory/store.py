"""SQLite store, migrations, and connection helpers for zola_memory (P6-D03)."""

from __future__ import annotations

import logging
import os
import re
import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Sequence, Tuple

try:
    from . import log as memlog
except ImportError:  # P6-STORE: flat unittest discover top — P6-D03
    import log as memlog

# P6-STORE: locks keyed by id(conn) — Connection rejects attributes / weakrefs — P6-D03
_CONN_LOCKS: Dict[int, threading.RLock] = {}
_CONN_LOCKS_GUARD = threading.Lock()

# P6-STORE: schema and path constants — P6-D03
SCHEMA_VERSION = 2
DB_DIRNAME = "zola_memory"
DB_FILENAME = "zola_memory.db"
META_SCHEMA_VERSION = "schema_version"
META_FILES_SHA256 = "files_sha256"
META_LAST_INTERACTION_AT = "last_interaction_at"
META_PENDING_ERASURES = "pending_erasures"
# P6-EPISODES: cross-process consolidator lease — P6-D04
META_CONSOLIDATE_LEASE_OWNER = "consolidate_lease_owner"
META_CONSOLIDATE_LEASE_EXPIRES_AT = "consolidate_lease_expires_at"
# P6-EPISODES: deferred G-ERASE physical sanitize when TRUNCATE busy — P6-D04
META_SANITIZE_PENDING = "sanitize_pending"
META_FTS_SECURE_DELETE = "fts_secure_delete"
FTS_TABLES = ("facts_fts", "episodes_fts", "entities_fts")

ENTRY_DELIMITER = "\n§\n"
TARGET_USER = "user"
TARGET_MEMORY = "memory"
STATE_ACTIVE = "active"
STATE_SUPERSEDED = "superseded"
SOURCE_NOTIFY = "notify"
SOURCE_FILE_CHECK = "file_check"

_TAG_RE = re.compile(r"^\[([a-z]+)\]\s*")


def db_path(hermes_home: Path) -> Path:
    return Path(hermes_home) / DB_DIRNAME / DB_FILENAME


def fts5_available() -> bool:
    """Return True when this runtime's sqlite3 can create an FTS5 table."""
    try:
        conn = sqlite3.connect(":memory:")
        try:
            conn.execute("CREATE VIRTUAL TABLE _zola_fts_probe USING fts5(x)")
            return True
        finally:
            conn.close()
    except Exception:
        return False


def normalize_entry(text: str) -> str:
    """Match Hermes MemoryStore strip semantics for set membership."""
    return (text or "").strip()


def parse_entries(raw: str) -> list[str]:
    """Split on the full ``\\n§\\n`` delimiter; strip; drop empties."""
    return [e for e in (normalize_entry(x) for x in (raw or "").split(ENTRY_DELIMITER)) if e]


def extract_tag(text: str) -> Optional[str]:
    match = _TAG_RE.match(text or "")
    return match.group(1) if match else None


def open_store(hermes_home: Path) -> sqlite3.Connection:
    path = db_path(hermes_home)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    # P6-EPISODES: G-ERASE — overwrite deleted content on page reuse — P6-D04
    conn.execute("PRAGMA secure_delete=ON")
    secure_row = conn.execute("PRAGMA secure_delete").fetchone()
    secure_val = int(secure_row[0]) if secure_row else -1
    # P6-STORE: one RLock per connection for all DB use — P6-D03
    with _CONN_LOCKS_GUARD:
        _CONN_LOCKS[id(conn)] = threading.RLock()
    with locked(conn):
        migrate(conn)
        fts_sd = enable_fts_secure_delete(conn)
        meta_set(conn, META_FTS_SECURE_DELETE, "1" if fts_sd else "0")
        conn.commit()
    memlog.write_event(
        memlog.LOG_EVENT_STORE_OPEN,
        pid=os.getpid(),
        secure_delete=secure_val,
        sqlite_version=sqlite3.sqlite_version,
        fts_secure_delete=fts_sd,
    )
    return conn


def enable_fts_secure_delete(conn: sqlite3.Connection) -> bool:
    """Enable FTS5 secure-delete on all episode/fact FTS tables (SQLite 3.44+)."""
    for table in FTS_TABLES:
        try:
            conn.execute(
                f"INSERT INTO {table}({table}, rank) VALUES('secure-delete', 1)"
            )
        except sqlite3.Error:
            return False
    return True


def fts_secure_delete_active(conn: sqlite3.Connection) -> bool:
    return (meta_get(conn, META_FTS_SECURE_DELETE) or "") == "1"


@contextmanager
def locked(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """Hold the connection's RLock for the duration of a critical section."""
    key = id(conn)
    with _CONN_LOCKS_GUARD:
        lock = _CONN_LOCKS.get(key)
        if lock is None:
            lock = threading.RLock()
            _CONN_LOCKS[key] = lock
    with lock:
        yield conn


def release_lock(conn: sqlite3.Connection) -> None:
    """Drop the lock entry when a connection is closed."""
    with _CONN_LOCKS_GUARD:
        _CONN_LOCKS.pop(id(conn), None)


def migrate(conn: sqlite3.Connection) -> None:
    """Apply migrations inside BEGIN IMMEDIATE. Fail closed on unknown future version."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS meta ("
            "  key TEXT PRIMARY KEY,"
            "  value TEXT NOT NULL"
            ")"
        )
        row = conn.execute(
            "SELECT value FROM meta WHERE key = ?",
            (META_SCHEMA_VERSION,),
        ).fetchone()
        current = int(row["value"]) if row else 0
        if current > SCHEMA_VERSION:
            raise RuntimeError(
                f"zola_memory schema_version {current} newer than supported {SCHEMA_VERSION}"
            )
        if current < 1:
            _migrate_v1(conn)
            conn.execute(
                "INSERT INTO meta (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (META_SCHEMA_VERSION, "1"),
            )
            conn.execute(
                "INSERT OR IGNORE INTO meta (key, value) VALUES (?, ?)",
                (META_PENDING_ERASURES, "[]"),
            )
            conn.execute(
                "INSERT OR IGNORE INTO meta (key, value) VALUES (?, ?)",
                (META_FILES_SHA256, ""),
            )
            conn.execute(
                "INSERT OR IGNORE INTO meta (key, value) VALUES (?, ?)",
                (META_LAST_INTERACTION_AT, ""),
            )
            current = 1
        if current < 2:
            _migrate_v2(conn)
            conn.execute(
                "INSERT INTO meta (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (META_SCHEMA_VERSION, "2"),
            )
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise


def _migrate_v1(conn: sqlite3.Connection) -> None:
    # P6-STORE: Track 2 schema + empty Track 4–5 tables — P6-D01/D03
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS facts (
            id TEXT PRIMARY KEY,
            target TEXT NOT NULL,
            text TEXT NOT NULL,
            tag TEXT,
            state TEXT NOT NULL,
            learned_at TEXT,
            indexed_at TEXT NOT NULL,
            updated_at TEXT,
            superseded_at TEXT,
            source TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_facts_target_state ON facts(target, state);
        CREATE INDEX IF NOT EXISTS idx_facts_state ON facts(state);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_facts_active_text
            ON facts(target, text) WHERE state = 'active';

        CREATE VIRTUAL TABLE IF NOT EXISTS facts_fts USING fts5(
            fact_id UNINDEXED,
            text
        );

        CREATE TABLE IF NOT EXISTS fact_history (
            id TEXT PRIMARY KEY,
            fact_id TEXT NOT NULL,
            text TEXT NOT NULL,
            superseded_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_fact_history_fact_id ON fact_history(fact_id);

        CREATE TABLE IF NOT EXISTS entities (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            kind TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);

        CREATE TABLE IF NOT EXISTS entity_aliases (
            entity_id TEXT NOT NULL,
            alias TEXT NOT NULL,
            PRIMARY KEY (entity_id, alias)
        );
        CREATE INDEX IF NOT EXISTS idx_entity_aliases_alias ON entity_aliases(alias);

        CREATE TABLE IF NOT EXISTS tombstones (
            id TEXT PRIMARY KEY,
            record_kind TEXT NOT NULL,
            erased_at TEXT NOT NULL,
            counts_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS episodes (
            id TEXT PRIMARY KEY,
            summary TEXT,
            significance TEXT,
            event_time TEXT,
            event_time_basis TEXT,
            event_time_evidence TEXT,
            open_items_json TEXT,
            source_session_id TEXT,
            source_turn_start INTEGER,
            source_turn_end INTEGER,
            recorded_at TEXT
        );

        CREATE TABLE IF NOT EXISTS episode_entities (
            episode_id TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            PRIMARY KEY (episode_id, entity_id)
        );

        CREATE TABLE IF NOT EXISTS episode_fact_refs (
            episode_id TEXT NOT NULL,
            fact_id TEXT NOT NULL,
            PRIMARY KEY (episode_id, fact_id)
        );

        CREATE TABLE IF NOT EXISTS pending_turns (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            turn_index INTEGER NOT NULL,
            user_text TEXT,
            assistant_text TEXT,
            user_time TEXT,
            assistant_time TEXT,
            consolidation_generation INTEGER NOT NULL DEFAULT 0,
            forget_hold INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        );
        """
    )


def _migrate_v2(conn: sqlite3.Connection) -> None:
    # P6-EPISODES: FTS, pending dedupe fingerprint, episode source_user_time — P6-D04
    cols = {
        r["name"]
        for r in conn.execute("PRAGMA table_info(pending_turns)").fetchall()
    }
    if "turn_fingerprint" not in cols:
        conn.execute(
            "ALTER TABLE pending_turns ADD COLUMN turn_fingerprint TEXT NOT NULL DEFAULT ''"
        )
    ep_cols = {
        r["name"] for r in conn.execute("PRAGMA table_info(episodes)").fetchall()
    }
    if "source_user_time" not in ep_cols:
        conn.execute("ALTER TABLE episodes ADD COLUMN source_user_time TEXT")
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_pending_dedupe "
        "ON pending_turns(session_id, ifnull(user_time, ''), turn_fingerprint)"
    )
    conn.execute(
        "CREATE VIRTUAL TABLE IF NOT EXISTS episodes_fts USING fts5("
        "  episode_id UNINDEXED,"
        "  summary"
        ")"
    )
    conn.execute(
        "CREATE VIRTUAL TABLE IF NOT EXISTS entities_fts USING fts5("
        "  entity_id UNINDEXED,"
        "  name"
        ")"
    )


def sanitize_after_erase(
    conn: sqlite3.Connection,
    *,
    fts_tables_touched: Optional[Sequence[str]] = None,
) -> None:
    """G-ERASE: FTS secure-delete/rebuild + WAL TRUNCATE after committed delete.

    Used after cascade erase, every consolidate commit (episodes or zero), and
    forget requests that match nothing (Phase 7-WAL). Must use the same
    connection only — a second connection TRUNCATE while this writer is still
    locked deadlocks file_check / nested erase callers. Always commit afterward
    so an implicit DML transaction cannot nest into later BEGIN IMMEDIATE
    callers (file_check adds). No silent PASSIVE fallback — busy TRUNCATE
    defers via meta.sanitize_pending.
    """
    t0 = time.perf_counter()
    touched = list(fts_tables_touched) if fts_tables_touched else list(FTS_TABLES)
    fts_mode = "secure-delete" if fts_secure_delete_active(conn) else "rebuild"
    fts_ms = 0
    busy, log_frames, checkpointed = -1, -1, -1
    try:
        t_fts = time.perf_counter()
        if fts_mode == "secure-delete":
            for table in FTS_TABLES:
                try:
                    conn.execute(f"INSERT INTO {table}({table}) VALUES('optimize')")
                except sqlite3.Error:
                    pass
        else:
            for table in touched:
                if table not in FTS_TABLES:
                    continue
                try:
                    conn.execute(f"INSERT INTO {table}({table}) VALUES('rebuild')")
                except sqlite3.Error:
                    pass
        # Commit FTS DML before TRUNCATE — an open write txn makes checkpoint busy=1
        # even with no second reader (C1 / long-lived single-conn failure mode).
        try:
            conn.commit()
        except sqlite3.Error:
            pass
        fts_ms = int((time.perf_counter() - t_fts) * 1000)
        busy, log_frames, checkpointed = _checkpoint_truncate_or_defer(conn)
    finally:
        try:
            conn.commit()
        except sqlite3.Error:
            pass
        pending = meta_get(conn, META_SANITIZE_PENDING) or "0"
        try:
            secure_row = conn.execute("PRAGMA secure_delete").fetchone()
            secure_val = int(secure_row[0]) if secure_row else -1
        except sqlite3.Error:
            secure_val = -1
        memlog.write_event(
            memlog.LOG_EVENT_SANITIZE_AFTER_ERASE,
            secure_delete=secure_val,
            fts_mode=fts_mode,
            fts_ms=fts_ms,
            checkpoint_busy=busy,
            checkpoint_log=log_frames,
            checkpoint_frames=checkpointed,
            sanitize_pending=pending,
            ok=(busy == 0),
            elapsed_ms=int((time.perf_counter() - t0) * 1000),
        )
        if busy != 0:
            memlog.write_event(
                memlog.LOG_EVENT_SANITIZE_RETRY,
                level=logging.WARNING,
                trigger="sanitize_after_erase",
                action="defer",
                checkpoint_busy=busy,
                checkpoint_log=log_frames,
                checkpoint_frames=checkpointed,
                ok=False,
            )


def _checkpoint_truncate_or_defer(
    conn: sqlite3.Connection,
) -> Tuple[int, int, int]:
    """Run wal_checkpoint(TRUNCATE); on busy set sanitize_pending (no PASSIVE)."""
    busy, log_frames, checkpointed = -1, -1, -1
    try:
        conn.execute("PRAGMA busy_timeout=50")
        row = conn.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
        if row is not None:
            busy = int(row[0])
            log_frames = int(row[1])
            checkpointed = int(row[2])
    except sqlite3.Error:
        busy = 1
    try:
        meta_set(conn, META_SANITIZE_PENDING, "0" if busy == 0 else "1")
    except sqlite3.Error:
        pass
    return busy, log_frames, checkpointed


def try_pending_sanitize(conn: sqlite3.Connection, *, trigger: str) -> bool:
    """Retry deferred WAL TRUNCATE when meta.sanitize_pending is set."""
    pending = meta_get(conn, META_SANITIZE_PENDING) or "0"
    if pending != "1":
        return True
    busy, log_frames, checkpointed = _checkpoint_truncate_or_defer(conn)
    try:
        conn.commit()
    except sqlite3.Error:
        pass
    if busy == 0:
        memlog.write_event(
            memlog.LOG_EVENT_SANITIZE_RETRY,
            trigger=trigger,
            action="success",
            checkpoint_busy=busy,
            checkpoint_log=log_frames,
            checkpoint_frames=checkpointed,
            ok=True,
        )
        return True
    memlog.write_event(
        memlog.LOG_EVENT_SANITIZE_RETRY,
        level=logging.WARNING,
        trigger=trigger,
        action="retry",
        checkpoint_busy=busy,
        checkpoint_log=log_frames,
        checkpoint_frames=checkpointed,
        ok=False,
    )
    return False


def meta_get(conn: sqlite3.Connection, key: str) -> Optional[str]:
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None


def meta_set(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO meta (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )


def memories_dir(hermes_home: Path) -> Path:
    return Path(hermes_home) / "memories"


def read_memory_file(path: Path) -> Tuple[str, bool]:
    """Return (text, ok). Missing file → ("", True). Read-only."""
    if not path.exists():
        return "", True
    try:
        return path.read_text(encoding="utf-8-sig"), True
    except (OSError, UnicodeDecodeError):
        return "", False


def combined_files_sha256(hermes_home: Path) -> str:
    import hashlib

    mem = memories_dir(hermes_home)
    user_raw, _ = read_memory_file(mem / "USER.md")
    memory_raw, _ = read_memory_file(mem / "MEMORY.md")
    # P6-STORE: hash raw decoded text bytes (utf-8) for cheap drift detection — P6-D01
    h = hashlib.sha256()
    h.update(user_raw.encode("utf-8"))
    h.update(b"\0")
    h.update(memory_raw.encode("utf-8"))
    return h.hexdigest()
