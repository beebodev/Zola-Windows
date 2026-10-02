"""SQLite store, migrations, and connection helpers for zola_memory (P6-D03)."""

from __future__ import annotations

import re
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Iterator, Optional, Tuple

# P6-STORE: locks keyed by id(conn) — Connection rejects attributes / weakrefs — P6-D03
_CONN_LOCKS: Dict[int, threading.RLock] = {}
_CONN_LOCKS_GUARD = threading.Lock()

# P6-STORE: schema and path constants — P6-D03
SCHEMA_VERSION = 1
DB_DIRNAME = "zola_memory"
DB_FILENAME = "zola_memory.db"
META_SCHEMA_VERSION = "schema_version"
META_FILES_SHA256 = "files_sha256"
META_LAST_INTERACTION_AT = "last_interaction_at"
META_PENDING_ERASURES = "pending_erasures"

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
    # P6-STORE: one RLock per connection for all DB use — P6-D03
    with _CONN_LOCKS_GUARD:
        _CONN_LOCKS[id(conn)] = threading.RLock()
    with locked(conn):
        migrate(conn)
    return conn


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
                (META_SCHEMA_VERSION, str(SCHEMA_VERSION)),
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
