"""Persisted Workspace taint — content-free session flags (P8-D09)."""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Callable, Optional, Set


# P8-CONNECT: content-free taint store under HERMES_HOME — P8-D09
STORE_DIR_NAME = "zola_workspace"
TAINT_FILENAME = "taint.sqlite"
TABLE_NAME = "session_taint"
STATE_DB_NAME = "state.db"
LINEAGE_WALK_CAP = 100

# Injectable path override for tests
_store_path_override: Optional[Path] = None
# Injectable lineage resolver: session_id -> root (or None if unresolved)
_lineage_root_fn: Optional[Callable[[str], Optional[str]]] = None


class LineageLookupError(Exception):
    """state.db unreadable/locked/query failure, or lineage walk cap hit."""


def set_store_path_for_tests(path: Optional[Path]) -> None:
    global _store_path_override
    _store_path_override = path


def reset_store_path_for_tests() -> None:
    set_store_path_for_tests(None)
    set_lineage_root_fn_for_tests(None)


def set_lineage_root_fn_for_tests(fn: Optional[Callable[[str], Optional[str]]]) -> None:
    global _lineage_root_fn
    _lineage_root_fn = fn


def _store_dir() -> Path:
    from hermes_constants import get_hermes_home

    return get_hermes_home() / STORE_DIR_NAME


def store_path() -> Path:
    if _store_path_override is not None:
        return Path(_store_path_override)
    return _store_dir() / TAINT_FILENAME


def _state_db_path() -> Path:
    from hermes_constants import get_hermes_home

    return get_hermes_home() / STATE_DB_NAME


def _connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=5.0)
    conn.execute(
        f"CREATE TABLE IF NOT EXISTS {TABLE_NAME} ("
        "  session_id TEXT PRIMARY KEY NOT NULL,"
        "  first_tainted_at REAL NOT NULL"
        ")"
    )
    conn.commit()
    return conn


def lineage_root(session_id: str) -> Optional[str]:
    """Walk parent_session_id to compression lineage root.

    Returns:
      - the root session id on a normal walk (including no parent / no row)
      - None if session_id empty or state.db is absent (non-error)

    Raises:
      LineageLookupError on state.db unreadable/locked/query failure, or walk-cap hit.
    """
    # P8-CONNECT: task_id is not stable across compression — use lineage root — P8-D09
    sid = str(session_id or "")
    if not sid:
        return None
    if _lineage_root_fn is not None:
        try:
            return _lineage_root_fn(sid)
        except LineageLookupError:
            raise
        except Exception as exc:
            raise LineageLookupError("lineage_resolver_error") from exc
    try:
        db_path = _state_db_path()
        if not db_path.exists():
            # Absent state.db is non-error (fresh home / tests without Hermes DB)
            return None
        # Read-only open — never mutate Hermes state.db
        uri = f"file:{db_path.as_posix()}?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=5.0)
        try:
            current = sid
            seen: Set[str] = set()
            root = sid
            while current and current not in seen:
                if len(seen) >= LINEAGE_WALK_CAP:
                    raise LineageLookupError("lineage_walk_cap")
                seen.add(current)
                root = current
                try:
                    row = conn.execute(
                        "SELECT parent_session_id FROM sessions WHERE id = ?",
                        (current,),
                    ).fetchone()
                except Exception as exc:
                    raise LineageLookupError("lineage_query_error") from exc
                if row is None:
                    break
                parent = row[0]
                if not parent:
                    break
                current = str(parent)
            return root
        finally:
            conn.close()
    except LineageLookupError:
        raise
    except Exception as exc:
        # Unreadable / locked / other open failures — fail closed for readers
        raise LineageLookupError("lineage_state_db_error") from exc


def _safe_lineage_root_for_mark(session_id: str) -> Optional[str]:
    """Resolve root for mark writes; lookup errors skip root (raw ids still marked)."""
    try:
        return lineage_root(session_id)
    except LineageLookupError:
        return None


def _keys_to_mark(session_id: str, task_id: Optional[str] = None) -> Set[str]:
    keys: Set[str] = set()
    sid = str(session_id or "")
    tid = str(task_id or "") if task_id is not None else ""
    if sid:
        keys.add(sid)
        root = _safe_lineage_root_for_mark(sid)
        if root:
            keys.add(root)
    if tid:
        keys.add(tid)
        root = _safe_lineage_root_for_mark(tid)
        if root:
            keys.add(root)
    return keys


def mark_tainted(session_id: str, task_id: Optional[str] = None) -> None:
    """Persist content-free taint marks for session_id, task_id, and lineage roots.

    Raises on write failure for the required session_id key. Lineage-root resolve
    failures are soft (raw ids still marked).
    """
    # P8-CONNECT: mark session_id + task_id + lineage roots before content — P8-D09
    sid = str(session_id or "")
    if not sid:
        raise ValueError("session_id required")
    keys = _keys_to_mark(sid, task_id)
    if not keys:
        raise ValueError("session_id required")
    path = store_path()
    conn = _connect(path)
    try:
        now = time.time()
        for key in keys:
            conn.execute(
                f"INSERT INTO {TABLE_NAME} (session_id, first_tainted_at) VALUES (?, ?) "
                f"ON CONFLICT(session_id) DO NOTHING",
                (key, now),
            )
        conn.commit()
    finally:
        conn.close()


def _row_marked(conn: sqlite3.Connection, key: str) -> bool:
    row = conn.execute(
        f"SELECT 1 FROM {TABLE_NAME} WHERE session_id = ? LIMIT 1",
        (key,),
    ).fetchone()
    return row is not None


def is_tainted(session_id: Optional[str] = None, task_id: Optional[str] = None) -> bool:
    """True if session_id, task_id, or either lineage root is marked.

    Empty both → False. Read errors or lineage lookup errors → True (fail closed).
    """
    # P8-CONNECT: read error → tainted True; empty both → False — P8-D09
    sid = str(session_id or "")
    tid = str(task_id or "")
    if not sid and not tid:
        return False
    try:
        path = store_path()
        if not path.exists():
            # Still resolve lineage: lookup error → tainted even with no store yet
            for key in (sid, tid):
                if not key:
                    continue
                try:
                    lineage_root(key)
                except LineageLookupError:
                    return True
            return False
        conn = _connect(path)
        try:
            candidates: Set[str] = set()
            if sid:
                candidates.add(sid)
                try:
                    root = lineage_root(sid)
                except LineageLookupError:
                    return True
                if root:
                    candidates.add(root)
            if tid:
                candidates.add(tid)
                try:
                    root = lineage_root(tid)
                except LineageLookupError:
                    return True
                if root:
                    candidates.add(root)
            for key in candidates:
                if _row_marked(conn, key):
                    return True
            return False
        finally:
            conn.close()
    except LineageLookupError:
        return True
    except Exception:
        return True


def is_tainted_ids(session_id: Optional[str], task_id: Optional[str]) -> bool:
    """Helper for guards: True if either id (or lineage) is tainted."""
    return is_tainted(session_id=session_id, task_id=task_id)
