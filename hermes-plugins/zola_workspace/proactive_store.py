"""proactive.db: schema, transitions, leases, retention (P9-D06 / P9-D07).

Every write to this file goes through the functions here. Callers get a
refusal dict. A refusal leaves the row unchanged.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

# P9-STORE: marker so zola_memory can find this module without a hard import cycle — P9-D06
PROACTIVE_STORE_MARKER = "p9-store"

SCHEMA_VERSION = 2
# P9-STORE: why a loop ended; NULL means the live row was already closed before this column — P9-D09
CLOSED_INTENTS = frozenset(
    {"reply", "cancelled", "status_change", "confirm_close", "expired", "forgotten"}
)
DB_DIRNAME = "proactive"
DB_FILENAME = "proactive.db"
META_SCHEMA_VERSION = "schema_version"

# P9-STORE: named limits from the locked Phase 3 proposal — P9-D06 / P9-D07 / P9-D09
RANK_LEASE_SECONDS = 120
SPEECH_CLAIM_LEASE_SECONDS = 30
SPEECH_OUTCOME_LEASE_SECONDS = 120
RANK_ATTEMPT_CAP = 5
BODY_MAX_AGE_DAYS = 7
TEXT_MAX_AGE_DAYS = 7
DELIVERY_KEEP_DAYS = 30
PURGE_INTERVAL_SECONDS = 3600
LOOP_DEFAULT_EXPIRY_DAYS = 14
LOOP_MAX_EXPIRY_DAYS = 90
BUSY_TIMEOUT_MS = 5000

MEMORY_DIRNAME = "zola_memory"
MEMORY_FILENAME = "zola_memory.db"
PENDING_META_KEY = "pending_proactive_forget"

_IN_FLIGHT = ("claimed", "speech_started", "delivery_uncertain")
_ticket_override: Optional[bool] = None
_db_path_override: Optional[Path] = None
_purge_started = False


def set_ticket_override_for_tests(value: Optional[bool]) -> None:
    global _ticket_override
    _ticket_override = value


def set_db_path_for_tests(path: Optional[Path]) -> None:
    global _db_path_override
    _db_path_override = None if path is None else Path(path)


def address_hash(address: str) -> str:
    # P9-STORE: forget matches the hash, so the pending record need not keep the address — P9-D06
    return hashlib.sha256(address.strip().casefold().encode("utf-8")).hexdigest()


def _ticket_ok() -> bool:
    if _ticket_override is not None:
        return bool(_ticket_override)
    try:
        try:
            from . import turn_context
        except ImportError:
            import turn_context
        return bool(turn_context.is_brian_turn())
    except Exception:
        return False


def _no(reason: str) -> Dict[str, Any]:
    return {"ok": False, "refused_reason": reason}


def _ok(**extra: Any) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"ok": True}
    payload.update(extra)
    return payload


def _iso(when: datetime) -> str:
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return when.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def _now(now: Optional[datetime]) -> datetime:
    if now is None:
        return datetime.now(timezone.utc)
    if now.tzinfo is None:
        return now.replace(tzinfo=timezone.utc)
    return now.astimezone(timezone.utc)


def _rollback(conn: sqlite3.Connection) -> None:
    try:
        conn.execute("ROLLBACK")
    except sqlite3.Error:
        pass


def _new_id() -> str:
    return str(uuid.uuid4())


def default_db_path(hermes_home: Path) -> Path:
    return Path(hermes_home) / DB_DIRNAME / DB_FILENAME


def profile_db_path() -> Optional[Path]:
    if _db_path_override is not None:
        return _db_path_override
    try:
        from hermes_constants import get_hermes_home

        return default_db_path(Path(get_hermes_home()))
    except Exception:
        return None


def connect(
    path: Path,
    *,
    timeout_ms: int = BUSY_TIMEOUT_MS,
    retry: bool = True,
) -> sqlite3.Connection:
    # P9-STORE: WAL and an explicit busy timeout, matching the H-4 measurement — P9-D06
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(
        str(path),
        timeout=timeout_ms / 1000.0,
        check_same_thread=False,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(f"PRAGMA busy_timeout={int(timeout_ms)}")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA secure_delete=ON")
    _migrate(conn)
    if retry:
        _retry_sibling_pending(path, conn)
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
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
                f"proactive schema_version {current} newer than supported {SCHEMA_VERSION}"
            )
        if current < 1:
            _migrate_v1(conn)
            current = 1
        if current < 2:
            _migrate_v2(conn)
            current = 2
        conn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (META_SCHEMA_VERSION, str(current)),
        )
        conn.execute("COMMIT")
    except Exception:
        _rollback(conn)
        raise


def _migrate_v1(conn: sqlite3.Connection) -> None:
    # P9-STORE: orthogonal dimensions so delivery and content can both be true — P9-D06
    conn.executescript(
        """
        CREATE TABLE items (
          id TEXT PRIMARY KEY,
          source TEXT NOT NULL CHECK (source IN ('gmail', 'calendar')),
          message_id TEXT,
          thread_id TEXT,
          event_id TEXT,
          event_updated TEXT,
          idempotency_key TEXT NOT NULL,
          sender_address TEXT,
          sender_address_hash TEXT,
          sender_display_name TEXT,
          entity_id TEXT,
          contacts_handle TEXT,
          entity_resolution TEXT NOT NULL
            CHECK (entity_resolution IN ('memory_entity', 'contacts_handle', 'unresolved')),
          label TEXT CHECK (label IS NULL OR label IN ('urgent', 'important', 'normal', 'ignore')),
          processing TEXT NOT NULL
            CHECK (processing IN ('unranked', 'ranked', 'rank_failed')),
          eligibility TEXT NOT NULL
            CHECK (eligibility IN ('pending', 'eligible', 'suppressed', 'expired')),
          conversation TEXT NOT NULL
            CHECK (conversation IN ('none', 'selected', 'possibly_surfaced', 'acknowledged')),
          delivery TEXT NOT NULL
            CHECK (delivery IN ('none', 'claimed', 'speech_started', 'delivery_uncertain', 'delivered')),
          content_state TEXT NOT NULL
            CHECK (content_state IN ('available', 'content_expired', 'forgotten')),
          loop_matched INTEGER NOT NULL DEFAULT 0,
          rank_attempts INTEGER NOT NULL DEFAULT 0,
          closed_at TEXT,
          detected_at TEXT NOT NULL,
          ranked_at TEXT,
          eligible_at TEXT,
          updated_at TEXT NOT NULL,
          subject TEXT,
          snippet TEXT,
          body TEXT,
          gist TEXT,
          calendar_status TEXT
        );
        CREATE UNIQUE INDEX idx_items_idempotency ON items (idempotency_key);

        CREATE TABLE item_attempts (
          attempt_id TEXT PRIMARY KEY,
          item_id TEXT NOT NULL REFERENCES items (id),
          purpose TEXT NOT NULL CHECK (purpose IN ('rank', 'speech')),
          status TEXT NOT NULL CHECK (status IN ('open', 'completed', 'released', 'uncertain')),
          lease_expires_at TEXT NOT NULL,
          created_at TEXT NOT NULL
        );

        CREATE TABLE loops (
          id TEXT PRIMARY KEY,
          status TEXT NOT NULL CHECK (status IN ('open', 'closed', 'expired')),
          intent TEXT NOT NULL,
          predicate_json TEXT NOT NULL,
          created_at TEXT NOT NULL,
          expires_at TEXT NOT NULL,
          matched_at TEXT,
          lapse_told INTEGER NOT NULL DEFAULT 0,
          session_id TEXT NOT NULL,
          entity_id TEXT,
          source_ids_json TEXT NOT NULL,
          address_hashes_json TEXT NOT NULL,
          sender_display_name TEXT,
          subject TEXT
        );

        CREATE TABLE deliveries (
          id TEXT PRIMARY KEY,
          item_id TEXT NOT NULL,
          attempt_id TEXT NOT NULL,
          outcome TEXT NOT NULL,
          at TEXT NOT NULL
        );

        CREATE TABLE cursors (
          source TEXT NOT NULL,
          scope_key TEXT NOT NULL,
          cursor_value TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          PRIMARY KEY (source, scope_key)
        );

        CREATE TABLE watcher_health (
          id INTEGER PRIMARY KEY CHECK (id = 1),
          last_ok_at TEXT,
          error_class TEXT,
          updated_at TEXT NOT NULL
        );
        """
    )


def _migrate_v2(conn: sqlite3.Connection) -> None:
    # Existing closed rows stay NULL. A later close writes its own reason.
    conn.execute(
        """
        ALTER TABLE loops ADD COLUMN closed_intent TEXT
        CHECK (
          closed_intent IS NULL OR closed_intent IN (
            'reply', 'cancelled', 'status_change', 'confirm_close', 'expired', 'forgotten'
          )
        )
        """
    )


def _call(fn, *args, **kwargs) -> Dict[str, Any]:
    try:
        return fn(*args, **kwargs)
    except sqlite3.OperationalError as exc:
        conn = args[0] if args else None
        if isinstance(conn, sqlite3.Connection):
            _rollback(conn)
        text = str(exc).lower()
        if "locked" in text or "busy" in text:
            return _no("locked")
        return _no("error")
    except Exception:
        conn = args[0] if args else None
        if isinstance(conn, sqlite3.Connection):
            _rollback(conn)
        return _no("error")


def _item(conn: sqlite3.Connection, item_id: str) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()


def _idempotency_key(
    *,
    source: str,
    message_id: str,
    event_id: str,
    event_updated: str,
) -> str:
    if source == "gmail":
        return "gmail:" + message_id
    return "calendar:" + event_id + ":" + event_updated


def insert_item(
    conn: sqlite3.Connection,
    *,
    source: str,
    message_id: str = "",
    thread_id: str = "",
    event_id: str = "",
    event_updated: str = "",
    sender_address: str = "",
    sender_display_name: str = "",
    subject: str = "",
    snippet: str = "",
    body: str = "",
    calendar_status: str = "",
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    # P9-STORE: one insert, unresolved until Track 3 stores sender resolution — P9-D06
    return _call(
        _insert_item,
        conn,
        source=source,
        message_id=message_id,
        thread_id=thread_id,
        event_id=event_id,
        event_updated=event_updated,
        sender_address=sender_address,
        sender_display_name=sender_display_name,
        subject=subject,
        snippet=snippet,
        body=body,
        calendar_status=calendar_status,
        now=now,
    )


def _insert_item(conn: sqlite3.Connection, **kwargs: Any) -> Dict[str, Any]:
    source = str(kwargs["source"])
    message_id = str(kwargs.get("message_id") or "")
    event_id = str(kwargs.get("event_id") or "")
    event_updated = str(kwargs.get("event_updated") or "")
    if source not in ("gmail", "calendar"):
        return _no("bad_args")
    if source == "gmail" and not message_id:
        return _no("bad_args")
    if source == "calendar" and not event_id:
        return _no("bad_args")
    key = _idempotency_key(
        source=source,
        message_id=message_id,
        event_id=event_id,
        event_updated=event_updated,
    )
    stamp = _iso(_now(kwargs.get("now")))
    address = str(kwargs.get("sender_address") or "")
    item_id = _new_id()
    conn.execute("BEGIN IMMEDIATE")
    try:
        conn.execute(
            """
            INSERT INTO items (
              id, source, message_id, thread_id, event_id, event_updated,
              idempotency_key, sender_address, sender_address_hash, sender_display_name,
              entity_id, contacts_handle, entity_resolution, label,
              processing, eligibility, conversation, delivery, content_state,
              loop_matched, rank_attempts, closed_at, detected_at, ranked_at,
              eligible_at, updated_at, subject, snippet, body, gist, calendar_status
            ) VALUES (
              ?, ?, ?, ?, ?, ?,
              ?, ?, ?, ?,
              NULL, NULL, 'unresolved', NULL,
              'unranked', 'pending', 'none', 'none', 'available',
              0, 0, NULL, ?, NULL,
              NULL, ?, ?, ?, ?, NULL, ?
            )
            """,
            (
                item_id,
                source,
                message_id,
                str(kwargs.get("thread_id") or ""),
                event_id,
                event_updated,
                key,
                address,
                address_hash(address) if address else "",
                str(kwargs.get("sender_display_name") or ""),
                stamp,
                stamp,
                str(kwargs.get("subject") or ""),
                str(kwargs.get("snippet") or ""),
                str(kwargs.get("body") or ""),
                str(kwargs.get("calendar_status") or ""),
            ),
        )
        conn.execute("COMMIT")
        return _ok(id=item_id, created=True)
    except sqlite3.IntegrityError:
        _rollback(conn)
        row = conn.execute(
            "SELECT id FROM items WHERE idempotency_key = ?",
            (key,),
        ).fetchone()
        if row is None:
            return _no("error")
        return _ok(id=row["id"], created=False)


def set_sender_resolution(
    conn: sqlite3.Connection,
    item_id: str,
    *,
    entity_id: str = "",
    contacts_handle: str = "",
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    # P9-STORE: Track 3 fills identity so a later forget can see the row — P9-D06
    return _call(
        _set_sender_resolution,
        conn,
        item_id,
        entity_id=entity_id,
        contacts_handle=contacts_handle,
        now=now,
    )


def _set_sender_resolution(
    conn: sqlite3.Connection,
    item_id: str,
    *,
    entity_id: str,
    contacts_handle: str,
    now: Optional[datetime],
) -> Dict[str, Any]:
    if entity_id and contacts_handle:
        resolution = "memory_entity"
    elif entity_id:
        resolution = "memory_entity"
    elif contacts_handle:
        resolution = "contacts_handle"
    else:
        return _no("bad_args")
    stamp = _iso(_now(now))
    conn.execute("BEGIN IMMEDIATE")
    cur = conn.execute(
        """
        UPDATE items
           SET entity_id = ?,
               contacts_handle = ?,
               entity_resolution = ?,
               updated_at = ?
         WHERE id = ? AND closed_at IS NULL AND content_state != 'forgotten'
        """,
        (entity_id or None, contacts_handle or None, resolution, stamp, item_id),
    )
    if cur.rowcount != 1:
        _rollback(conn)
        return _no("illegal_transition")
    conn.execute("COMMIT")
    return _ok()


def _open_attempt(
    conn: sqlite3.Connection,
    item_id: str,
    purpose: str,
    now_iso: str,
) -> Optional[sqlite3.Row]:
    return conn.execute(
        """
        SELECT attempt_id FROM item_attempts
         WHERE item_id = ? AND purpose = ? AND status = 'open' AND lease_expires_at > ?
        """,
        (item_id, purpose, now_iso),
    ).fetchone()


def claim_rank(
    conn: sqlite3.Connection,
    item_id: str,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    return _call(_claim_rank, conn, item_id, now=now)


def _claim_rank(
    conn: sqlite3.Connection,
    item_id: str,
    *,
    now: Optional[datetime],
) -> Dict[str, Any]:
    clock = _now(now)
    stamp = _iso(clock)
    lease = _iso(clock + timedelta(seconds=RANK_LEASE_SECONDS))
    conn.execute("BEGIN IMMEDIATE")
    row = _item(conn, item_id)
    if row is None or row["processing"] != "unranked" or row["closed_at"]:
        _rollback(conn)
        return _no("illegal_transition")
    if _open_attempt(conn, item_id, "rank", stamp) is not None:
        _rollback(conn)
        return _no("illegal_transition")
    attempt_id = _new_id()
    conn.execute(
        """
        INSERT INTO item_attempts (
          attempt_id, item_id, purpose, status, lease_expires_at, created_at
        ) VALUES (?, ?, 'rank', 'open', ?, ?)
        """,
        (attempt_id, item_id, lease, stamp),
    )
    conn.execute("COMMIT")
    return _ok(attempt_id=attempt_id)


def complete_rank(
    conn: sqlite3.Connection,
    item_id: str,
    attempt_id: str,
    *,
    label: str,
    gist: str = "",
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    # P9-STORE: ranking nulls the body and does not touch eligibility or delivery — P9-D07
    return _call(
        _complete_rank,
        conn,
        item_id,
        attempt_id,
        label=label,
        gist=gist,
        now=now,
    )


def _complete_rank(
    conn: sqlite3.Connection,
    item_id: str,
    attempt_id: str,
    *,
    label: str,
    gist: str,
    now: Optional[datetime],
) -> Dict[str, Any]:
    if label not in ("urgent", "important", "normal", "ignore"):
        return _no("bad_args")
    stamp = _iso(_now(now))
    conn.execute("BEGIN IMMEDIATE")
    cur = conn.execute(
        """
        UPDATE items
           SET processing = 'ranked',
               label = ?,
               gist = ?,
               body = NULL,
               ranked_at = ?,
               updated_at = ?
         WHERE id = ?
           AND processing = 'unranked'
        """,
        (label, gist, stamp, stamp, item_id),
    )
    if cur.rowcount != 1:
        _rollback(conn)
        return _no("illegal_transition")
    done = conn.execute(
        """
        UPDATE item_attempts
           SET status = 'completed'
         WHERE attempt_id = ? AND item_id = ? AND purpose = 'rank' AND status = 'open'
        """,
        (attempt_id, item_id),
    )
    if done.rowcount != 1:
        _rollback(conn)
        return _no("attempt_mismatch")
    conn.execute("COMMIT")
    return _ok()


def fail_rank(
    conn: sqlite3.Connection,
    item_id: str,
    attempt_id: str,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    # P9-STORE: the capped row stays visible as rank_failed; it is not deleted — P9-D08
    return _call(_fail_rank, conn, item_id, attempt_id, now=now)


def _fail_rank(
    conn: sqlite3.Connection,
    item_id: str,
    attempt_id: str,
    *,
    now: Optional[datetime],
) -> Dict[str, Any]:
    stamp = _iso(_now(now))
    conn.execute("BEGIN IMMEDIATE")
    row = _item(conn, item_id)
    if row is None:
        _rollback(conn)
        return _no("illegal_transition")
    attempts = int(row["rank_attempts"]) + 1
    processing = "rank_failed" if attempts >= RANK_ATTEMPT_CAP else "unranked"
    cur = conn.execute(
        """
        UPDATE items
           SET processing = ?,
               rank_attempts = ?,
               updated_at = ?
         WHERE id = ? AND processing = 'unranked'
        """,
        (processing, attempts, stamp, item_id),
    )
    if cur.rowcount != 1:
        _rollback(conn)
        return _no("illegal_transition")
    done = conn.execute(
        """
        UPDATE item_attempts
           SET status = 'released'
         WHERE attempt_id = ? AND item_id = ? AND purpose = 'rank' AND status = 'open'
        """,
        (attempt_id, item_id),
    )
    if done.rowcount != 1:
        _rollback(conn)
        return _no("attempt_mismatch")
    conn.execute("COMMIT")
    return _ok(processing=processing, rank_attempts=attempts)


def release_rank_lease(
    conn: sqlite3.Connection,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    return _call(_release_rank_lease, conn, now=now)


def _release_rank_lease(
    conn: sqlite3.Connection,
    *,
    now: Optional[datetime],
) -> Dict[str, Any]:
    stamp = _iso(_now(now))
    conn.execute("BEGIN IMMEDIATE")
    cur = conn.execute(
        """
        UPDATE item_attempts
           SET status = 'released'
         WHERE purpose = 'rank' AND status = 'open' AND lease_expires_at <= ?
        """,
        (stamp,),
    )
    conn.execute("COMMIT")
    return _ok(released=cur.rowcount)


def mark_loop_eligible(
    conn: sqlite3.Connection,
    item_id: str,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    # P9-STORE: a loop match is code, so eligibility does not wait for ranking — P9-D08
    return _call(_mark_loop_eligible, conn, item_id, now=now)


def _mark_loop_eligible(
    conn: sqlite3.Connection,
    item_id: str,
    *,
    now: Optional[datetime],
) -> Dict[str, Any]:
    stamp = _iso(_now(now))
    conn.execute("BEGIN IMMEDIATE")
    cur = conn.execute(
        """
        UPDATE items
           SET eligibility = 'eligible',
               loop_matched = 1,
               eligible_at = ?,
               updated_at = ?
         WHERE id = ?
           AND eligibility = 'pending'
           AND closed_at IS NULL
        """,
        (stamp, stamp, item_id),
    )
    if cur.rowcount != 1:
        _rollback(conn)
        return _no("illegal_transition")
    conn.execute("COMMIT")
    return _ok()


def mark_eligible(
    conn: sqlite3.Connection,
    item_id: str,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    return _call(_mark_eligible, conn, item_id, now=now)


def _mark_eligible(
    conn: sqlite3.Connection,
    item_id: str,
    *,
    now: Optional[datetime],
) -> Dict[str, Any]:
    stamp = _iso(_now(now))
    conn.execute("BEGIN IMMEDIATE")
    cur = conn.execute(
        """
        UPDATE items
           SET eligibility = 'eligible',
               eligible_at = ?,
               updated_at = ?
         WHERE id = ?
           AND eligibility = 'pending'
           AND processing = 'ranked'
           AND closed_at IS NULL
        """,
        (stamp, stamp, item_id),
    )
    if cur.rowcount != 1:
        _rollback(conn)
        return _no("illegal_transition")
    conn.execute("COMMIT")
    return _ok()


def suppress(conn: sqlite3.Connection, item_id: str, *, now: Optional[datetime] = None) -> Dict[str, Any]:
    return _call(_set_eligibility, conn, item_id, "suppressed", ("pending", "eligible"), now=now)


def expire_eligibility(
    conn: sqlite3.Connection,
    item_id: str,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    return _call(_set_eligibility, conn, item_id, "expired", ("pending", "eligible"), now=now)


def _set_eligibility(
    conn: sqlite3.Connection,
    item_id: str,
    dest: str,
    sources: Sequence[str],
    *,
    now: Optional[datetime],
) -> Dict[str, Any]:
    stamp = _iso(_now(now))
    marks = ",".join("?" for _ in sources)
    conn.execute("BEGIN IMMEDIATE")
    cur = conn.execute(
        f"""
        UPDATE items
           SET eligibility = ?, updated_at = ?
         WHERE id = ? AND eligibility IN ({marks}) AND closed_at IS NULL
        """,
        (dest, stamp, item_id, *sources),
    )
    if cur.rowcount != 1:
        _rollback(conn)
        return _no("illegal_transition")
    conn.execute("COMMIT")
    return _ok()


def select_for_conversation(
    conn: sqlite3.Connection,
    item_id: str,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    return _call(_set_conversation, conn, item_id, "selected", ("none",), now=now, ticket=False)


def mark_possibly_surfaced(
    conn: sqlite3.Connection,
    item_id: str,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    return _call(
        _set_conversation,
        conn,
        item_id,
        "possibly_surfaced",
        ("selected",),
        now=now,
        ticket=False,
    )


def acknowledge(
    conn: sqlite3.Connection,
    item_id: str,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    # P9-STORE: acknowledged only on a ticket turn — P9-D09
    return _call(
        _set_conversation,
        conn,
        item_id,
        "acknowledged",
        ("selected", "possibly_surfaced"),
        now=now,
        ticket=True,
    )


def _set_conversation(
    conn: sqlite3.Connection,
    item_id: str,
    dest: str,
    sources: Sequence[str],
    *,
    now: Optional[datetime],
    ticket: bool,
) -> Dict[str, Any]:
    if ticket and not _ticket_ok():
        return _no("origin")
    stamp = _iso(_now(now))
    marks = ",".join("?" for _ in sources)
    conn.execute("BEGIN IMMEDIATE")
    cur = conn.execute(
        f"""
        UPDATE items
           SET conversation = ?, updated_at = ?
         WHERE id = ? AND conversation IN ({marks})
        """,
        (dest, stamp, item_id, *sources),
    )
    if cur.rowcount != 1:
        _rollback(conn)
        return _no("illegal_transition")
    conn.execute("COMMIT")
    return _ok()


def claim_speech(
    conn: sqlite3.Connection,
    item_id: str,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    return _call(_claim_speech, conn, item_id, now=now)


def _claim_speech(
    conn: sqlite3.Connection,
    item_id: str,
    *,
    now: Optional[datetime],
) -> Dict[str, Any]:
    clock = _now(now)
    stamp = _iso(clock)
    lease = _iso(clock + timedelta(seconds=SPEECH_CLAIM_LEASE_SECONDS))
    conn.execute("BEGIN IMMEDIATE")
    cur = conn.execute(
        """
        UPDATE items
           SET delivery = 'claimed', updated_at = ?
         WHERE id = ?
           AND eligibility = 'eligible'
           AND delivery = 'none'
           AND closed_at IS NULL
        """,
        (stamp, item_id),
    )
    if cur.rowcount != 1:
        _rollback(conn)
        return _no("illegal_transition")
    attempt_id = _new_id()
    conn.execute(
        """
        INSERT INTO item_attempts (
          attempt_id, item_id, purpose, status, lease_expires_at, created_at
        ) VALUES (?, ?, 'speech', 'open', ?, ?)
        """,
        (attempt_id, item_id, lease, stamp),
    )
    conn.execute("COMMIT")
    return _ok(attempt_id=attempt_id)


def mark_speech_started(
    conn: sqlite3.Connection,
    item_id: str,
    attempt_id: str,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    return _call(_mark_speech_started, conn, item_id, attempt_id, now=now)


def _mark_speech_started(
    conn: sqlite3.Connection,
    item_id: str,
    attempt_id: str,
    *,
    now: Optional[datetime],
) -> Dict[str, Any]:
    clock = _now(now)
    stamp = _iso(clock)
    lease = _iso(clock + timedelta(seconds=SPEECH_OUTCOME_LEASE_SECONDS))
    conn.execute("BEGIN IMMEDIATE")
    cur = conn.execute(
        """
        UPDATE items
           SET delivery = 'speech_started', updated_at = ?
         WHERE id = ? AND delivery = 'claimed'
        """,
        (stamp, item_id),
    )
    if cur.rowcount != 1:
        _rollback(conn)
        return _no("illegal_transition")
    done = conn.execute(
        """
        UPDATE item_attempts
           SET lease_expires_at = ?
         WHERE attempt_id = ? AND item_id = ? AND purpose = 'speech' AND status = 'open'
        """,
        (lease, attempt_id, item_id),
    )
    if done.rowcount != 1:
        _rollback(conn)
        return _no("attempt_mismatch")
    conn.execute("COMMIT")
    return _ok()


def mark_delivered(
    conn: sqlite3.Connection,
    item_id: str,
    attempt_id: str,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    return _call(_mark_delivered, conn, item_id, attempt_id, now=now)


def _mark_delivered(
    conn: sqlite3.Connection,
    item_id: str,
    attempt_id: str,
    *,
    now: Optional[datetime],
) -> Dict[str, Any]:
    stamp = _iso(_now(now))
    conn.execute("BEGIN IMMEDIATE")
    cur = conn.execute(
        """
        UPDATE items
           SET delivery = 'delivered', updated_at = ?
         WHERE id = ? AND delivery = 'speech_started'
        """,
        (stamp, item_id),
    )
    if cur.rowcount != 1:
        _rollback(conn)
        return _no("illegal_transition")
    done = conn.execute(
        """
        UPDATE item_attempts
           SET status = 'completed'
         WHERE attempt_id = ? AND item_id = ? AND purpose = 'speech' AND status = 'open'
        """,
        (attempt_id, item_id),
    )
    if done.rowcount != 1:
        _rollback(conn)
        return _no("attempt_mismatch")
    conn.execute(
        """
        INSERT INTO deliveries (id, item_id, attempt_id, outcome, at)
        VALUES (?, ?, ?, 'delivered', ?)
        """,
        (_new_id(), item_id, attempt_id, stamp),
    )
    conn.execute("COMMIT")
    return _ok()


def mark_delivery_uncertain(
    conn: sqlite3.Connection,
    item_id: str,
    attempt_id: str,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    # P9-STORE: uncertain is not claimable again — P9-D06
    return _call(_mark_delivery_uncertain, conn, item_id, attempt_id, now=now)


def _mark_delivery_uncertain(
    conn: sqlite3.Connection,
    item_id: str,
    attempt_id: str,
    *,
    now: Optional[datetime],
) -> Dict[str, Any]:
    stamp = _iso(_now(now))
    conn.execute("BEGIN IMMEDIATE")
    cur = conn.execute(
        """
        UPDATE items
           SET delivery = 'delivery_uncertain', updated_at = ?
         WHERE id = ? AND delivery = 'speech_started'
        """,
        (stamp, item_id),
    )
    if cur.rowcount != 1:
        _rollback(conn)
        return _no("illegal_transition")
    done = conn.execute(
        """
        UPDATE item_attempts
           SET status = 'uncertain'
         WHERE attempt_id = ? AND item_id = ? AND purpose = 'speech' AND status = 'open'
        """,
        (attempt_id, item_id),
    )
    if done.rowcount != 1:
        _rollback(conn)
        return _no("attempt_mismatch")
    conn.execute("COMMIT")
    return _ok()


def release_speech_lease(
    conn: sqlite3.Connection,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    return _call(_recover_speech, conn, now=now)


def _recover_speech(
    conn: sqlite3.Connection,
    *,
    now: Optional[datetime],
) -> Dict[str, Any]:
    """Claimed and expired returns to none. Speech started and expired becomes uncertain."""
    stamp = _iso(_now(now))
    conn.execute("BEGIN IMMEDIATE")
    released = conn.execute(
        """
        SELECT item_id, attempt_id FROM item_attempts
         WHERE purpose = 'speech' AND status = 'open' AND lease_expires_at <= ?
        """,
        (stamp,),
    ).fetchall()
    released_n = 0
    uncertain_n = 0
    for attempt in released:
        item = _item(conn, attempt["item_id"])
        if item is None:
            continue
        if item["delivery"] == "claimed":
            conn.execute(
                """
                UPDATE items SET delivery = 'none', updated_at = ?
                 WHERE id = ? AND delivery = 'claimed'
                """,
                (stamp, item["id"]),
            )
            conn.execute(
                "UPDATE item_attempts SET status = 'released' WHERE attempt_id = ?",
                (attempt["attempt_id"],),
            )
            released_n += 1
        elif item["delivery"] == "speech_started":
            conn.execute(
                """
                UPDATE items SET delivery = 'delivery_uncertain', updated_at = ?
                 WHERE id = ? AND delivery = 'speech_started'
                """,
                (stamp, item["id"]),
            )
            conn.execute(
                "UPDATE item_attempts SET status = 'uncertain' WHERE attempt_id = ?",
                (attempt["attempt_id"],),
            )
            uncertain_n += 1
    conn.execute("COMMIT")
    return _ok(released=released_n, uncertain=uncertain_n)


def close_item(
    conn: sqlite3.Connection,
    item_id: str,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    return _call(_close_item, conn, item_id, now=now)


def _close_item(
    conn: sqlite3.Connection,
    item_id: str,
    *,
    now: Optional[datetime],
) -> Dict[str, Any]:
    if not _ticket_ok():
        return _no("origin")
    stamp = _iso(_now(now))
    conn.execute("BEGIN IMMEDIATE")
    cur = conn.execute(
        """
        UPDATE items
           SET closed_at = ?, updated_at = ?
         WHERE id = ?
           AND closed_at IS NULL
           AND delivery NOT IN ('claimed', 'speech_started')
        """,
        (stamp, stamp, item_id),
    )
    if cur.rowcount != 1:
        _rollback(conn)
        return _no("illegal_transition")
    conn.execute("COMMIT")
    return _ok()


def insert_loop(
    conn: sqlite3.Connection,
    *,
    intent: str,
    predicate: Dict[str, Any],
    session_id: str,
    sender_display_name: str = "",
    subject: str = "",
    entity_id: str = "",
    source_ids: Optional[Sequence[str]] = None,
    address_hashes: Optional[Sequence[str]] = None,
    now: Optional[datetime] = None,
    expiry_days: int = LOOP_DEFAULT_EXPIRY_DAYS,
) -> Dict[str, Any]:
    # P9-STORE: a loop row is created only on a ticket turn — P9-D09
    return _call(
        _insert_loop,
        conn,
        intent=intent,
        predicate=predicate,
        session_id=session_id,
        sender_display_name=sender_display_name,
        subject=subject,
        entity_id=entity_id,
        source_ids=list(source_ids or []),
        address_hashes=list(address_hashes or []),
        now=now,
        expiry_days=expiry_days,
    )


def _insert_loop(conn: sqlite3.Connection, **kwargs: Any) -> Dict[str, Any]:
    if not _ticket_ok():
        return _no("origin")
    days = int(kwargs["expiry_days"])
    if days < 1 or days > LOOP_MAX_EXPIRY_DAYS:
        return _no("bad_args")
    clock = _now(kwargs.get("now"))
    stamp = _iso(clock)
    expires = _iso(clock + timedelta(days=days))
    loop_id = _new_id()
    conn.execute("BEGIN IMMEDIATE")
    conn.execute(
        """
        INSERT INTO loops (
          id, status, intent, predicate_json, created_at, expires_at, matched_at,
          lapse_told, session_id, entity_id, source_ids_json, address_hashes_json,
          sender_display_name, subject
        ) VALUES (?, 'open', ?, ?, ?, ?, NULL, 0, ?, ?, ?, ?, ?, ?)
        """,
        (
            loop_id,
            str(kwargs["intent"]),
            json.dumps(kwargs["predicate"], separators=(",", ":")),
            stamp,
            expires,
            str(kwargs["session_id"]),
            str(kwargs.get("entity_id") or "") or None,
            json.dumps(list(kwargs["source_ids"]), separators=(",", ":")),
            json.dumps(list(kwargs["address_hashes"]), separators=(",", ":")),
            str(kwargs.get("sender_display_name") or ""),
            str(kwargs.get("subject") or ""),
        ),
    )
    conn.execute("COMMIT")
    return _ok(id=loop_id, expires_at=expires)


def note_loop_match_on_loop(
    conn: sqlite3.Connection,
    loop_id: str,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    # P9-STORE: matched is not closed — P9-D09
    return _call(_note_loop_match_on_loop, conn, loop_id, now=now)


def _note_loop_match_on_loop(
    conn: sqlite3.Connection,
    loop_id: str,
    *,
    now: Optional[datetime],
) -> Dict[str, Any]:
    stamp = _iso(_now(now))
    conn.execute("BEGIN IMMEDIATE")
    cur = conn.execute(
        """
        UPDATE loops
           SET matched_at = ?
         WHERE id = ? AND status = 'open'
        """,
        (stamp, loop_id),
    )
    if cur.rowcount != 1:
        _rollback(conn)
        return _no("illegal_transition")
    row = conn.execute("SELECT status FROM loops WHERE id = ?", (loop_id,)).fetchone()
    conn.execute("COMMIT")
    if row is None or row["status"] != "open":
        return _no("illegal_transition")
    return _ok()


def close_loop(
    conn: sqlite3.Connection,
    loop_id: str,
    *,
    closed_intent: Optional[str] = None,
) -> Dict[str, Any]:
    if closed_intent is not None and closed_intent not in CLOSED_INTENTS:
        return _no("bad_args")
    return _call(_close_loop, conn, loop_id, closed_intent=closed_intent)


def _close_loop(
    conn: sqlite3.Connection,
    loop_id: str,
    *,
    closed_intent: Optional[str] = None,
) -> Dict[str, Any]:
    if not _ticket_ok():
        return _no("origin")
    conn.execute("BEGIN IMMEDIATE")
    cur = conn.execute(
        """
        UPDATE loops
           SET status = 'closed',
               subject = NULL,
               sender_display_name = NULL,
               closed_intent = ?
         WHERE id = ? AND status = 'open'
        """,
        (closed_intent, loop_id),
    )
    if cur.rowcount != 1:
        _rollback(conn)
        return _no("illegal_transition")
    conn.execute("COMMIT")
    return _ok()


def list_open_loops(conn: sqlite3.Connection) -> Dict[str, Any]:
    # P9-STORE: a loop is Brian's, not a session's; session_id stays on the row as provenance — P9-D09
    try:
        rows = conn.execute(
            """
            SELECT id, intent, expires_at, matched_at, sender_display_name, subject
              FROM loops
             WHERE status = 'open'
             ORDER BY created_at
            """
        ).fetchall()
        return _ok(
            loops=[
                {
                    "id": row["id"],
                    "intent": row["intent"],
                    "expires_at": row["expires_at"],
                    "matched": bool(row["matched_at"]),
                    "sender_display_name": row["sender_display_name"] or "",
                    "subject": row["subject"] or "",
                }
                for row in rows
            ]
        )
    except sqlite3.OperationalError as exc:
        text = str(exc).lower()
        return _no("locked" if "locked" in text or "busy" in text else "error")
    except Exception:
        return _no("error")


def list_open_items(conn: sqlite3.Connection) -> Dict[str, Any]:
    # P9-STORE: rank_failed stays in this list; content columns are not returned — P9-D08
    try:
        rows = conn.execute(
            """
            SELECT id, processing, eligibility, conversation, delivery, content_state, loop_matched
              FROM items
             WHERE closed_at IS NULL
             ORDER BY detected_at
            """
        ).fetchall()
        items = []
        for row in rows:
            reason = "rank_failed" if row["processing"] == "rank_failed" else row["eligibility"]
            items.append(
                {
                    "id": row["id"],
                    "processing": row["processing"],
                    "eligibility": row["eligibility"],
                    "conversation": row["conversation"],
                    "delivery": row["delivery"],
                    "content_state": row["content_state"],
                    "loop_matched": int(row["loop_matched"]),
                    "reason": reason,
                }
            )
        return _ok(items=items)
    except sqlite3.OperationalError as exc:
        text = str(exc).lower()
        return _no("locked" if "locked" in text or "busy" in text else "error")
    except Exception:
        return _no("error")


def _name_hit(name: str, row: sqlite3.Row) -> bool:
    token = (name or "").strip().casefold()
    if len(token) < 3:
        return False
    blob = "\n".join(
        str(row[column] or "") for column in ("subject", "snippet", "gist")
    ).casefold()
    return token in blob


def forget_subject(
    conn: sqlite3.Connection,
    *,
    entity_id: str = "",
    address_hashes: Optional[Sequence[str]] = None,
    source_ids: Optional[Sequence[str]] = None,
    names: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    # P9-STORE: entity, address hash, and source id first; a text sweep is extra — P9-D06
    return _call(
        _forget_subject,
        conn,
        entity_id=entity_id,
        address_hashes=list(address_hashes or []),
        source_ids=list(source_ids or []),
        names=list(names or []),
    )


def _forget_subject(
    conn: sqlite3.Connection,
    *,
    entity_id: str,
    address_hashes: List[str],
    source_ids: List[str],
    names: List[str],
    ticket_checked: bool = False,
) -> Dict[str, Any]:
    # A retry finishes a forget that already passed the ticket. Store open has no turn.
    if not ticket_checked and not _ticket_ok():
        return _no("origin")
    hashes = {value for value in address_hashes if value}
    sources = {value for value in source_ids if value}
    conn.execute("BEGIN IMMEDIATE")
    rows = conn.execute("SELECT * FROM items").fetchall()
    delete_ids = []
    redact_ids = []
    for row in rows:
        linked = False
        if entity_id and row["entity_id"] == entity_id:
            linked = True
        elif row["sender_address_hash"] and row["sender_address_hash"] in hashes:
            linked = True
        elif row["message_id"] in sources or row["thread_id"] in sources or row["event_id"] in sources:
            linked = True
        elif entity_id and any(_name_hit(name, row) for name in names):
            linked = True
        if not linked:
            continue
        if row["delivery"] in _IN_FLIGHT:
            redact_ids.append(row["id"])
        else:
            delete_ids.append(row["id"])
    for item_id in delete_ids:
        conn.execute("DELETE FROM item_attempts WHERE item_id = ?", (item_id,))
        conn.execute("DELETE FROM deliveries WHERE item_id = ?", (item_id,))
        conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
    for item_id in redact_ids:
        conn.execute(
            """
            UPDATE items
               SET subject = NULL, snippet = NULL, body = NULL, gist = NULL,
                   sender_address = NULL, sender_display_name = NULL,
                   entity_id = NULL, contacts_handle = NULL,
                   content_state = 'forgotten'
             WHERE id = ?
            """,
            (item_id,),
        )
    loops = conn.execute("SELECT * FROM loops").fetchall()
    loops_deleted = 0
    for loop in loops:
        try:
            loop_sources = set(json.loads(loop["source_ids_json"] or "[]"))
            loop_hashes = set(json.loads(loop["address_hashes_json"] or "[]"))
        except json.JSONDecodeError:
            loop_sources = set()
            loop_hashes = set()
        if (
            (entity_id and loop["entity_id"] == entity_id)
            or loop_hashes & hashes
            or loop_sources & sources
        ):
            # Keep the row so a prior close reason stays. An open loop ends as forgotten.
            cur = conn.execute(
                """
                UPDATE loops
                   SET status = 'closed',
                       closed_intent = 'forgotten',
                       sender_display_name = NULL,
                       subject = NULL
                 WHERE id = ? AND status = 'open'
                """,
                (loop["id"],),
            )
            loops_deleted += cur.rowcount
    conn.execute("COMMIT")
    return _ok(
        items_deleted=len(delete_ids),
        items_redacted=len(redact_ids),
        loops_deleted=loops_deleted,
    )


def source_ids_for(
    conn: sqlite3.Connection,
    *,
    entity_id: str = "",
    address_hashes: Optional[Sequence[str]] = None,
) -> List[str]:
    hashes = {value for value in (address_hashes or []) if value}
    found: List[str] = []
    for row in conn.execute("SELECT * FROM items"):
        if entity_id and row["entity_id"] == entity_id:
            pass
        elif row["sender_address_hash"] and row["sender_address_hash"] in hashes:
            pass
        else:
            continue
        for column in ("message_id", "thread_id", "event_id"):
            if row[column]:
                found.append(row[column])
    return found


def purge_retention(
    conn: sqlite3.Connection,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    # P9-STORE: content may be nulled; delivery, claim, and the attempt stay — P9-D07
    return _call(_purge_retention, conn, now=now)


def _purge_retention(
    conn: sqlite3.Connection,
    *,
    now: Optional[datetime],
) -> Dict[str, Any]:
    clock = _now(now)
    stamp = _iso(clock)
    body_cutoff = _iso(clock - timedelta(days=BODY_MAX_AGE_DAYS))
    text_cutoff = _iso(clock - timedelta(days=TEXT_MAX_AGE_DAYS))
    delivery_cutoff = _iso(clock - timedelta(days=DELIVERY_KEEP_DAYS))
    recovery = _recover_speech(conn, now=clock)
    if not recovery.get("ok"):
        return recovery
    rank_release = _release_rank_lease(conn, now=clock)
    if not rank_release.get("ok"):
        return rank_release
    conn.execute("BEGIN IMMEDIATE")
    bodies = conn.execute(
        """
        UPDATE items
           SET body = NULL,
               content_state = 'content_expired'
         WHERE processing = 'unranked'
           AND detected_at <= ?
           AND content_state = 'available'
           AND body IS NOT NULL
        """,
        (body_cutoff,),
    )
    texts = conn.execute(
        """
        UPDATE items
           SET subject = NULL,
               snippet = NULL,
               gist = NULL,
               sender_display_name = NULL
         WHERE content_state != 'forgotten'
           AND (delivery = 'delivered' OR detected_at <= ?)
           AND (
             subject IS NOT NULL OR snippet IS NOT NULL OR gist IS NOT NULL
             OR sender_display_name IS NOT NULL
           )
        """,
        (text_cutoff,),
    )
    expired = conn.execute(
        """
        UPDATE items
           SET content_state = 'content_expired'
         WHERE content_state = 'available'
           AND body IS NULL
           AND subject IS NULL
           AND snippet IS NULL
           AND gist IS NULL
        """
    )
    old_deliveries = conn.execute(
        "DELETE FROM deliveries WHERE at <= ?",
        (delivery_cutoff,),
    )
    loops = conn.execute(
        """
        UPDATE loops
           SET status = 'expired',
               sender_display_name = NULL,
               subject = NULL,
               closed_intent = 'expired'
         WHERE status = 'open' AND expires_at <= ?
        """,
        (stamp,),
    )
    # P9-STORE: closed and expired loops keep ids and hashes for forget; the mail text does not — P9-D07
    loop_text = conn.execute(
        """
        UPDATE loops
           SET sender_display_name = NULL,
               subject = NULL
         WHERE status IN ('closed', 'expired')
           AND (sender_display_name IS NOT NULL OR subject IS NOT NULL)
        """
    )
    conn.execute("COMMIT")
    return _ok(
        bodies=bodies.rowcount,
        texts=texts.rowcount,
        content_expired=expired.rowcount,
        deliveries_deleted=old_deliveries.rowcount,
        loops_expired=loops.rowcount,
        loops_text_cleared=loop_text.rowcount,
        speech_released=recovery.get("released", 0),
        speech_uncertain=recovery.get("uncertain", 0),
    )


def _memory_path_for(db_path: Path) -> Path:
    return db_path.parent.parent / MEMORY_DIRNAME / MEMORY_FILENAME


def _retry_sibling_pending(db_path: Path, conn: sqlite3.Connection) -> None:
    memory_path = _memory_path_for(Path(db_path))
    if not memory_path.exists():
        return
    memory = sqlite3.connect(str(memory_path), timeout=BUSY_TIMEOUT_MS / 1000.0)
    memory.row_factory = sqlite3.Row
    try:
        _retry_pending(memory, conn)
    finally:
        memory.close()


def _retry_pending(memory: sqlite3.Connection, conn: sqlite3.Connection) -> Dict[str, Any]:
    row = memory.execute(
        "SELECT value FROM meta WHERE key = ?",
        (PENDING_META_KEY,),
    ).fetchone()
    if row is None or not row["value"]:
        return _ok(retried=False)
    try:
        payload = json.loads(row["value"])
    except json.JSONDecodeError:
        return _no("error")
    result = _forget_subject(
        conn,
        entity_id=str(payload.get("entity_id") or ""),
        address_hashes=list(payload.get("address_hashes") or []),
        source_ids=list(payload.get("source_ids") or []),
        names=[],
        ticket_checked=True,
    )
    if not result.get("ok"):
        return result
    memory.execute("BEGIN IMMEDIATE")
    memory.execute("DELETE FROM meta WHERE key = ?", (PENDING_META_KEY,))
    memory.execute("COMMIT")
    return _ok(retried=True)


def retry_pending_forget(
    memory: sqlite3.Connection,
    conn: sqlite3.Connection,
) -> Dict[str, Any]:
    """Finish a proactive forget whose memory side already committed."""
    return _call(_retry_pending, memory, conn)


def forget_subject_from_profile(payload: Dict[str, Any], names: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    path = profile_db_path()
    if path is None or not path.exists():
        return _no("missing")
    try:
        conn = connect(path, retry=False)
    except sqlite3.OperationalError as exc:
        text = str(exc).lower()
        return _no("locked" if "locked" in text or "busy" in text else "error")
    except Exception:
        return _no("missing")
    try:
        return forget_subject(
            conn,
            entity_id=str(payload.get("entity_id") or ""),
            address_hashes=list(payload.get("address_hashes") or []),
            source_ids=list(payload.get("source_ids") or []),
            names=list(names or []),
        )
    finally:
        conn.close()


def start_purge_thread() -> None:
    """One daemon purge when this process is serve. Unit tests do not pass that argv."""
    global _purge_started
    if _purge_started:
        return
    try:
        try:
            from . import origin
        except ImportError:
            import origin
        if not origin.in_serve_process():
            return
    except Exception:
        return
    _purge_started = True

    def _loop() -> None:
        while True:
            path = profile_db_path()
            if path is not None:
                try:
                    conn = connect(path, retry=True)
                    try:
                        purge_retention(conn)
                    finally:
                        conn.close()
                except Exception:
                    pass
            threading.Event().wait(PURGE_INTERVAL_SECONDS)

    threading.Thread(target=_loop, name="zola-proactive-purge", daemon=True).start()
