"""proactive.db: schema, transitions, leases, retention (P9-D06 / P9-D07).

Every write to this file goes through the functions here. Callers get a
refusal dict. A refusal leaves the row unchanged.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set

# P10-STORE: package load uses relative imports; flat tests use the fallback — P10-D11
try:
    from . import address_hash as address_hash_mod
    from . import phone_ids
except ImportError:
    import address_hash as address_hash_mod
    import phone_ids

_LOG = logging.getLogger("zola_workspace.proactive_store")

# P9-STORE: marker so zola_memory can find this module without a hard import cycle — P9-D06
PROACTIVE_STORE_MARKER = "p9-store"

SCHEMA_VERSION = 6
# P10-STORE: the v6 rebuild writes 6 even after SCHEMA_VERSION moves on — P10-D11
SCHEMA_V6 = 6
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
# P9-SPEAK: a loop match older than this waits for a conversation — P9-D11
SPEECH_MAX_AGE_SECONDS = 7200
# P9-SPEAK: same 600 s window as a surface attempt; only an unexpired open one blocks speech — P9-D11
SURFACE_ATTEMPT_TTL_SECONDS = 600
# P9-SPEAK: one follow-up note after evidenced speech, inside the surface gap — P9-D07
POST_SPEECH_WINDOW_SECONDS = 900
META_SPEECH_POST_NOTED = "speech_post_noted_attempt"
NAME_SOURCES = frozenset({"mail", "contacts_ticket", "brian_message"})
RANK_ATTEMPT_CAP = 5
BODY_MAX_AGE_DAYS = 7
TEXT_MAX_AGE_DAYS = 7
DELIVERY_KEEP_DAYS = 30
PURGE_INTERVAL_SECONDS = 3600
LOOP_DEFAULT_EXPIRY_DAYS = 14
LOOP_MAX_EXPIRY_DAYS = 90
# P9-SURFACE: pending counts stop at this window; purge closes the rest — P9-D10
SURFACE_LIST_WINDOW_DAYS = 7
META_SURFACE_MARKER = "surface_last_ticket_turn_at"
META_SURFACE_ATTEMPT = "surface_last_attempt_id"
META_SURFACE_CONFIRMED = "surface_last_confirmed"
# P9-WATCH: a transient fetch becomes terminal after this many tries — P9-D04
POISON_ATTEMPT_CAP = 5
BUSY_TIMEOUT_MS = 5000
# P10-STORE: phone kinds share one source list with the conversation hold Track 5 removes — P10-D11
PHONE_SOURCES = ("sms", "mms", "notif")
PHONE_CONVERSATION_HOLD = PHONE_SOURCES
PHONE_TEXT_KINDS = ("sms", "mms")
PHONE_NOTIF_KIND = "notif"
IDENTITY_VERSION = "v1"
IDENTITY_SEPARATOR = "\x1f"
MASK_KINDS = ("verification_code", "reset_link", "unsure")
ATTACHMENT_KINDS = ("image", "video", "audio", "other")
COMPLETENESS_VALUES = ("complete", "incomplete", "exhausted")
# P10-STORE: incomplete stays in the schema CHECK and is never ingested — P10-D01a
ACCEPTED_COMPLETENESS = ("complete", "exhausted")
# P10-STORE: body limits and reject reasons come from the contract file — P10-D01a
_PHONE_PROTOCOL = json.loads(
    (Path(__file__).resolve().parent / "contracts" / "phone_protocol.json").read_text(encoding="utf-8")
)
TEXT_BODY_CHARS = int(_PHONE_PROTOCOL["size_limits"]["text_body_chars"])
NOTIFICATION_TEXT_CHARS = int(_PHONE_PROTOCOL["size_limits"]["notification_text_chars"])
INGEST_REJECT_REASONS = tuple(_PHONE_PROTOCOL["ingest_reject_reasons"])
RCS_FLAGS = ("yes", "no", "unknown")
PHONE_TOMBSTONE_KEEP_DAYS = 30
INGEST_RESULTS = ("stored", "updated", "duplicate", "suppressed", "rejected", "ignored")

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
    # P10-STORE: re-export so watcher.py keeps this call and the bytes stay the same — P10-D10
    return address_hash_mod.address_hash(address)


def _sql_list(values: Sequence[str]) -> str:
    return ", ".join("'" + value + "'" for value in values)


def _phone_hold_sql() -> str:
    # P10-STORE: one constant; Track 5 deletes this predicate — P10-D11
    return "source NOT IN (" + _sql_list(PHONE_CONVERSATION_HOLD) + ")"


def _phone_source_sql() -> str:
    return "source IN (" + _sql_list(PHONE_SOURCES) + ")"


def _ticket_ok(turn_id: Optional[str] = None) -> bool:
    if _ticket_override is not None:
        return bool(_ticket_override)
    try:
        try:
            from . import turn_context
        except ImportError:
            import turn_context
        if turn_id:
            return bool(turn_context.is_brian_turn(turn_id))
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
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(f"PRAGMA busy_timeout={int(timeout_ms)}")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA secure_delete=ON")
        _migrate(conn)
        if retry:
            _retry_sibling_pending(path, conn)
    except Exception:
        conn.close()
        raise
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
        if current < 3:
            _migrate_v3(conn)
            current = 3
        if current < 4:
            _migrate_v4(conn)
            current = 4
        if current < 5:
            _migrate_v5(conn)
            current = 5
        # P10-STORE: version 6 rebuilds items, and foreign_keys cannot change inside this transaction — R2
        needs_v6 = current < SCHEMA_V6
        conn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (META_SCHEMA_VERSION, str(current)),
        )
        conn.execute("COMMIT")
    except Exception:
        _rollback(conn)
        raise
    if needs_v6:
        _migrate_v6_committed(conn)


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


def _migrate_v3(conn: sqlite3.Connection) -> None:
    # P9-WATCH: known calendar state, poison records, and per-source health — P9-D04 / P9-D12
    conn.executescript(
        """
        CREATE TABLE calendar_events (
          calendar_id TEXT NOT NULL,
          event_id TEXT NOT NULL,
          event_updated TEXT NOT NULL,
          calendar_status TEXT,
          start_at TEXT,
          end_at TEXT,
          recurring_event_id TEXT,
          original_start TEXT,
          updated_at TEXT NOT NULL,
          PRIMARY KEY (calendar_id, event_id)
        );

        CREATE TABLE watcher_rejects (
          source TEXT NOT NULL,
          source_id_hash TEXT NOT NULL,
          error_class TEXT NOT NULL,
          disposition TEXT NOT NULL,
          attempts INTEGER NOT NULL,
          first_seen TEXT NOT NULL,
          last_seen TEXT NOT NULL,
          PRIMARY KEY (source, source_id_hash)
        );
        """
    )
    for column, ddl in (
        ("gmail_ok_at", "ALTER TABLE watcher_health ADD COLUMN gmail_ok_at TEXT"),
        ("calendar_ok_at", "ALTER TABLE watcher_health ADD COLUMN calendar_ok_at TEXT"),
        ("gmail_error", "ALTER TABLE watcher_health ADD COLUMN gmail_error TEXT"),
        ("calendar_error", "ALTER TABLE watcher_health ADD COLUMN calendar_error TEXT"),
        ("needs_reconnect", "ALTER TABLE watcher_health ADD COLUMN needs_reconnect INTEGER"),
        (
            "recovery_count",
            "ALTER TABLE watcher_health ADD COLUMN recovery_count INTEGER NOT NULL DEFAULT 0",
        ),
    ):
        existing = {row[1] for row in conn.execute("PRAGMA table_info(watcher_health)")}
        if column not in existing:
            conn.execute(ddl)


def _migrate_v4(conn: sqlite3.Connection) -> None:
    # P9-SURFACE: attempt bookkeeping and a purge-owned close reason — P9-D10
    item_columns = (
        ("selected_at", "ALTER TABLE items ADD COLUMN selected_at TEXT"),
        ("inject_count", "ALTER TABLE items ADD COLUMN inject_count INTEGER NOT NULL DEFAULT 0"),
        ("acknowledged_at", "ALTER TABLE items ADD COLUMN acknowledged_at TEXT"),
        ("attempt_id", "ALTER TABLE items ADD COLUMN attempt_id TEXT"),
        ("attempt_turn_id", "ALTER TABLE items ADD COLUMN attempt_turn_id TEXT"),
        ("attempt_at", "ALTER TABLE items ADD COLUMN attempt_at TEXT"),
        (
            "closed_reason",
            "ALTER TABLE items ADD COLUMN closed_reason TEXT "
            "CHECK (closed_reason IS NULL OR closed_reason IN ('dismissed', 'aged_out'))",
        ),
    )
    existing = {row[1] for row in conn.execute("PRAGMA table_info(items)")}
    for name, ddl in item_columns:
        if name not in existing:
            conn.execute(ddl)
    loop_columns = (
        ("lapse_attempt_id", "ALTER TABLE loops ADD COLUMN lapse_attempt_id TEXT"),
        ("lapse_attempt_turn_id", "ALTER TABLE loops ADD COLUMN lapse_attempt_turn_id TEXT"),
    )
    existing_loops = {row[1] for row in conn.execute("PRAGMA table_info(loops)")}
    for name, ddl in loop_columns:
        if name not in existing_loops:
            conn.execute(ddl)


def _migrate_v5(conn: sqlite3.Connection) -> None:
    # P9-SPEAK: provenance is code-checked; existing rows stay mail and are spoken as someone — P9-D11
    existing = {row[1] for row in conn.execute("PRAGMA table_info(loops)")}
    if "name_source" in existing:
        return
    conn.execute(
        """
        ALTER TABLE loops ADD COLUMN name_source TEXT NOT NULL DEFAULT 'mail'
        CHECK (name_source IN ('mail', 'contacts_ticket', 'brian_message'))
        """
    )


def _migrate_v6_committed(conn: sqlite3.Connection) -> None:
    # P10-STORE: drop items only with foreign keys off; item_attempts still points at those ids — R2
    conn.execute("PRAGMA foreign_keys=OFF")
    try:
        conn.execute("BEGIN IMMEDIATE")
        try:
            # P10-STORE: a second opener may already have committed schema 6 — P10-D11
            current = conn.execute(
                "SELECT value FROM meta WHERE key = ?",
                (META_SCHEMA_VERSION,),
            ).fetchone()
            if current is not None and int(current["value"]) >= SCHEMA_V6:
                conn.execute("ROLLBACK")
                return
            _migrate_v6(conn)
            if conn.execute("PRAGMA foreign_key_check").fetchall():
                raise RuntimeError("proactive schema rebuild failed foreign_key_check")
            conn.execute(
                "INSERT INTO meta (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (META_SCHEMA_VERSION, str(SCHEMA_V6)),
            )
            conn.execute("COMMIT")
        except Exception:
            _rollback(conn)
            raise
    finally:
        conn.execute("PRAGMA foreign_keys=ON")


def _migrate_v6(conn: sqlite3.Connection) -> None:
    # P10-STORE: sms, mms, and notif join Gmail and Calendar; Phase 9 rows stay model — P10-D11
    index_sql = [
        row[0]
        for row in conn.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'index' AND tbl_name = 'items' AND sql IS NOT NULL"
        )
    ]
    conn.execute(
        """
        CREATE TABLE items_v6 (
          id TEXT PRIMARY KEY,
          source TEXT NOT NULL CHECK (source IN ('gmail', 'calendar', 'sms', 'mms', 'notif')),
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
          calendar_status TEXT,
          selected_at TEXT,
          inject_count INTEGER NOT NULL DEFAULT 0,
          acknowledged_at TEXT,
          attempt_id TEXT,
          attempt_turn_id TEXT,
          attempt_at TEXT,
          closed_reason TEXT
            CHECK (closed_reason IS NULL OR closed_reason IN ('dismissed', 'aged_out')),
          device_id TEXT,
          revision INTEGER,
          completeness TEXT
            CHECK (completeness IS NULL OR completeness IN ('complete', 'incomplete', 'exhausted')),
          rcs_flag TEXT
            CHECK (rcs_flag IS NULL OR rcs_flag IN ('yes', 'no', 'unknown')),
          sender_kind TEXT
            CHECK (sender_kind IS NULL OR sender_kind IN ('e164', 'shortcode', 'alnum', 'unparsed')),
          is_group INTEGER CHECK (is_group IS NULL OR is_group IN (0, 1)),
          participant_count INTEGER,
          attachment_has INTEGER CHECK (attachment_has IS NULL OR attachment_has IN (0, 1)),
          attachment_count INTEGER,
          attachment_kind TEXT
            CHECK (attachment_kind IS NULL OR attachment_kind IN ('image', 'video', 'audio', 'other')),
          mask_kind TEXT
            CHECK (mask_kind IS NULL OR mask_kind IN ('verification_code', 'reset_link', 'unsure')),
          truncated INTEGER
            CHECK (truncated IS NULL OR truncated IN (0, 1)),
          ranking_source TEXT NOT NULL DEFAULT 'model'
            CHECK (ranking_source IN ('model', 'code')),
          judgment TEXT,
          watch_evaluated INTEGER
            CHECK (watch_evaluated IS NULL OR watch_evaluated IN (0, 1))
        )
        """
    )
    old_cols = [row[1] for row in conn.execute("PRAGMA table_info(items)")]
    col_list = ", ".join(old_cols)
    conn.execute(
        f"INSERT INTO items_v6 (rowid, {col_list}, ranking_source) "
        f"SELECT rowid, {col_list}, 'model' FROM items"
    )
    conn.execute("DROP TABLE items")
    conn.execute("ALTER TABLE items_v6 RENAME TO items")
    for sql in index_sql:
        conn.execute(sql)
    conn.execute(
        "CREATE INDEX idx_items_phone_sender ON items (sender_address_hash, detected_at) "
        "WHERE source IN ('sms', 'mms', 'notif')"
    )
    conn.execute(
        """
        CREATE TABLE phone_tombstones (
          identity_key_hash TEXT PRIMARY KEY,
          created_at TEXT NOT NULL
        )
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


def _identity_dirty(value: str) -> bool:
    return IDENTITY_SEPARATOR in value


def _phone_identity(
    *,
    kind: str,
    device_id: str,
    provider_id: str,
    package: str,
    notification_key: str,
    newest_message_timestamp: str,
) -> Optional[str]:
    fields = [IDENTITY_VERSION, device_id, kind]
    if kind in PHONE_TEXT_KINDS:
        fields.append(provider_id)
    elif kind == PHONE_NOTIF_KIND:
        fields.extend((package, notification_key, newest_message_timestamp))
    else:
        return None
    if any(_identity_dirty(field) or field == "" for field in fields):
        return None
    return IDENTITY_SEPARATOR.join(fields)


def _content_gone(row: sqlite3.Row) -> bool:
    # P10-STORE: a revision never puts removed content back — P10-D03
    if row["content_state"] != "available":
        return True
    if row["acknowledged_at"] or row["conversation"] == "acknowledged":
        return True
    if row["closed_at"]:
        return True
    return False


def _phone_content_absent_sql() -> str:
    # P10-STORE: ack, close, and purge share one empty-content rule — P10-D03
    return """
           body IS NULL
           AND subject IS NULL
           AND snippet IS NULL
           AND gist IS NULL
           AND sender_display_name IS NULL
           AND attachment_has IS NULL
           AND attachment_count IS NULL
           AND attachment_kind IS NULL
    """


def _expire_cleared_phone_content_locked(
    conn: sqlite3.Connection,
    item_id: Optional[str] = None,
) -> None:
    phone = _phone_source_sql()
    absent = _phone_content_absent_sql()
    if item_id is None:
        conn.execute(
            f"""
            UPDATE items
               SET content_state = 'content_expired'
             WHERE {phone}
               AND content_state = 'available'
               AND {absent}
            """
        )
        return
    conn.execute(
        f"""
        UPDATE items
           SET content_state = 'content_expired'
         WHERE id = ?
           AND {phone}
           AND content_state = 'available'
           AND {absent}
        """,
        (item_id,),
    )


def _clear_phone_content_locked(conn: sqlite3.Connection, item_id: str) -> None:
    # P10-STORE: phone body and display end at ack, dismiss, close, or forget — P10-D03
    phone = _phone_source_sql()
    conn.execute(
        f"""
        UPDATE items
           SET body = NULL,
               subject = NULL,
               snippet = NULL,
               gist = NULL,
               sender_display_name = NULL,
               attachment_has = NULL,
               attachment_count = NULL,
               attachment_kind = NULL
         WHERE id = ?
           AND {phone}
        """,
        (item_id,),
    )
    _expire_cleared_phone_content_locked(conn, item_id)


def _write_tombstone_locked(conn: sqlite3.Connection, identity_key: str, stamp: str) -> None:
    conn.execute(
        """
        INSERT INTO phone_tombstones (identity_key_hash, created_at)
        VALUES (?, ?)
        ON CONFLICT(identity_key_hash) DO NOTHING
        """,
        (address_hash(identity_key), stamp),
    )


def record_phone_tombstone(
    conn: sqlite3.Connection,
    identity_key: str,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    # P10-STORE: forget writes a content-free hash; Track 6 calls this — P10-D14
    return _call(_record_phone_tombstone, conn, identity_key, now=now)


def _record_phone_tombstone(
    conn: sqlite3.Connection,
    identity_key: str,
    *,
    now: Optional[datetime],
) -> Dict[str, Any]:
    if not identity_key:
        return _no("bad_args")
    stamp = _iso(_now(now))
    conn.execute("BEGIN IMMEDIATE")
    _write_tombstone_locked(conn, identity_key, stamp)
    conn.execute("COMMIT")
    return _ok()


def ingest_phone_item(
    conn: sqlite3.Connection,
    *,
    kind: str,
    device_id: str,
    revision: int,
    completeness: str,
    received_at: datetime,
    provider_id: str = "",
    package: str = "",
    notification_key: str = "",
    newest_message_timestamp: str = "",
    sender_raw: str = "",
    sender_display_name: str = "",
    body: str = "",
    subject: str = "",
    snippet: str = "",
    is_group: int = 0,
    participant_count: Optional[int] = None,
    rcs_flag: Optional[str] = None,
    attachment_has: Optional[int] = None,
    attachment_count: Optional[int] = None,
    attachment_kind: Optional[str] = None,
    mask_kind: Optional[str] = None,
    truncated: Optional[int] = None,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    # P10-STORE: one transaction; the store normalizes the sender — P10-D01a / P10-D10
    return _call(
        _ingest_phone_item,
        conn,
        kind=kind,
        device_id=device_id,
        revision=revision,
        completeness=completeness,
        received_at=received_at,
        provider_id=provider_id,
        package=package,
        notification_key=notification_key,
        newest_message_timestamp=newest_message_timestamp,
        sender_raw=sender_raw,
        sender_display_name=sender_display_name,
        body=body,
        subject=subject,
        snippet=snippet,
        is_group=is_group,
        participant_count=participant_count,
        rcs_flag=rcs_flag,
        attachment_has=attachment_has,
        attachment_count=attachment_count,
        attachment_kind=attachment_kind,
        mask_kind=mask_kind,
        truncated=truncated,
        now=now,
    )


def _ingest_rejected(reason: str) -> Dict[str, Any]:
    return _ok(result="rejected", reason=reason)


def _ingest_phone_item(conn: sqlite3.Connection, **kwargs: Any) -> Dict[str, Any]:
    kind = str(kwargs.get("kind") or "")
    device_id = str(kwargs.get("device_id") or "")
    provider_id = str(kwargs.get("provider_id") or "")
    package = str(kwargs.get("package") or "")
    notification_key = str(kwargs.get("notification_key") or "")
    newest = str(kwargs.get("newest_message_timestamp") or "")
    revision = kwargs.get("revision")
    completeness = str(kwargs.get("completeness") or "")
    received_at = kwargs.get("received_at")
    if kind not in PHONE_SOURCES:
        return _ingest_rejected("bad_kind")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
        return _ingest_rejected("bad_revision")
    if completeness not in ACCEPTED_COMPLETENESS:
        return _ingest_rejected("bad_completeness")
    if not isinstance(received_at, datetime):
        return _ingest_rejected("bad_time")
    identity_fields = [device_id, kind]
    if kind in PHONE_TEXT_KINDS:
        identity_fields.append(provider_id)
    else:
        identity_fields.extend((package, notification_key, newest))
    if any(IDENTITY_SEPARATOR in field for field in identity_fields):
        return _ingest_rejected("separator")
    identity = _phone_identity(
        kind=kind,
        device_id=device_id,
        provider_id=provider_id,
        package=package,
        notification_key=notification_key,
        newest_message_timestamp=newest,
    )
    if identity is None:
        return _ingest_rejected("bad_identity")
    mask_kind = kwargs.get("mask_kind")
    if mask_kind is not None and mask_kind not in MASK_KINDS:
        return _ingest_rejected("bad_mask")
    attachment_kind = kwargs.get("attachment_kind")
    if attachment_kind is not None and attachment_kind not in ATTACHMENT_KINDS:
        return _ingest_rejected("bad_attachment")
    attachment_has = kwargs.get("attachment_has")
    if attachment_has is not None and (isinstance(attachment_has, bool) or attachment_has not in (0, 1)):
        return _ingest_rejected("bad_field")
    attachment_count = kwargs.get("attachment_count")
    if attachment_count is not None and (
        isinstance(attachment_count, bool) or not isinstance(attachment_count, int) or attachment_count < 0
    ):
        return _ingest_rejected("bad_field")
    is_group = kwargs.get("is_group")
    if isinstance(is_group, bool) or is_group not in (0, 1):
        return _ingest_rejected("bad_field")
    rcs_flag = kwargs.get("rcs_flag")
    if rcs_flag is not None and rcs_flag not in RCS_FLAGS:
        return _ingest_rejected("bad_field")
    participant_count = kwargs.get("participant_count")
    if participant_count is not None and (
        isinstance(participant_count, bool) or not isinstance(participant_count, int) or participant_count < 0
    ):
        return _ingest_rejected("bad_field")
    truncated = kwargs.get("truncated")
    if truncated is not None and (isinstance(truncated, bool) or truncated not in (0, 1)):
        return _ingest_rejected("bad_field")
    body = str(kwargs.get("body") or "")
    body_limit = TEXT_BODY_CHARS if kind in PHONE_TEXT_KINDS else NOTIFICATION_TEXT_CHARS
    if len(body) > body_limit:
        return _ingest_rejected("too_large")
    sender_kind, canonical = phone_ids.normalize(str(kwargs.get("sender_raw") or ""))
    sender_hash = phone_ids.hash(canonical)
    clock = _now(kwargs.get("now"))
    stamp = _iso(clock)
    detected = _iso(_now(received_at))
    key_hash = address_hash(identity)
    conn.execute("BEGIN IMMEDIATE")
    tomb = conn.execute(
        "SELECT 1 FROM phone_tombstones WHERE identity_key_hash = ?",
        (key_hash,),
    ).fetchone()
    if tomb is not None:
        conn.execute("COMMIT")
        return _ok(result="suppressed")
    row = conn.execute(
        "SELECT * FROM items WHERE idempotency_key = ?",
        (identity,),
    ).fetchone()
    if row is None:
        item_id = _new_id()
        message_id = provider_id if kind in PHONE_TEXT_KINDS else notification_key
        conn.execute(
            """
            INSERT INTO items (
              id, source, message_id, thread_id, event_id, event_updated,
              idempotency_key, sender_address, sender_address_hash, sender_display_name,
              entity_id, contacts_handle, entity_resolution, label,
              processing, eligibility, conversation, delivery, content_state,
              loop_matched, rank_attempts, closed_at, detected_at, ranked_at,
              eligible_at, updated_at, subject, snippet, body, gist, calendar_status,
              device_id, revision, completeness, rcs_flag, sender_kind, is_group,
              participant_count, attachment_has, attachment_count, attachment_kind,
              mask_kind, truncated, ranking_source, judgment, watch_evaluated
            ) VALUES (
              ?, ?, ?, '', NULL, NULL,
              ?, '', ?, ?,
              NULL, NULL, 'unresolved', NULL,
              'ranked', 'eligible', 'none', 'none', 'available',
              0, 0, NULL, ?, ?,
              ?, ?, ?, ?, ?, NULL, NULL,
              ?, ?, ?, ?, ?, ?,
              ?, ?, ?, ?,
              ?, ?, 'code', NULL, 0
            )
            """,
            (
                item_id,
                kind,
                message_id,
                identity,
                sender_hash,
                str(kwargs.get("sender_display_name") or ""),
                detected,
                stamp,
                stamp,
                stamp,
                str(kwargs.get("subject") or ""),
                str(kwargs.get("snippet") or ""),
                body,
                device_id,
                revision,
                completeness,
                rcs_flag,
                sender_kind,
                is_group,
                participant_count,
                attachment_has,
                attachment_count,
                attachment_kind,
                mask_kind,
                truncated,
            ),
        )
        conn.execute("COMMIT")
        return _ok(result="stored", id=item_id)
    existing = int(row["revision"] or 0)
    if revision < existing:
        conn.execute("COMMIT")
        _LOG.info(
            "result=ignored key_hash=%s revision=%s existing=%s",
            key_hash,
            revision,
            existing,
        )
        return _ok(result="ignored", id=row["id"])
    if revision == existing:
        conn.execute("COMMIT")
        return _ok(result="duplicate", id=row["id"])
    if _content_gone(row):
        conn.execute(
            """
            UPDATE items
               SET revision = ?, completeness = ?, updated_at = ?
             WHERE id = ?
            """,
            (revision, completeness, stamp, row["id"]),
        )
    else:
        conn.execute(
            """
            UPDATE items
               SET body = ?,
                   sender_display_name = ?,
                   sender_address_hash = ?,
                   sender_kind = ?,
                   is_group = ?,
                   participant_count = ?,
                   attachment_has = ?,
                   attachment_count = ?,
                   attachment_kind = ?,
                   mask_kind = ?,
                   truncated = ?,
                   rcs_flag = ?,
                   completeness = ?,
                   revision = ?,
                   detected_at = ?,
                   updated_at = ?
             WHERE id = ?
            """,
            (
                body,
                str(kwargs.get("sender_display_name") or ""),
                sender_hash,
                sender_kind,
                is_group,
                participant_count,
                attachment_has,
                attachment_count,
                attachment_kind,
                mask_kind,
                truncated,
                rcs_flag,
                completeness,
                revision,
                detected,
                stamp,
                row["id"],
            ),
        )
    conn.execute("COMMIT")
    return _ok(result="updated", id=row["id"])


def list_unevaluated_phone_items(conn: sqlite3.Connection) -> Dict[str, Any]:
    # P10-STORE: startup recovery lists phone rows whose watch marker is still 0 — R2
    try:
        phone = _phone_source_sql()
        rows = conn.execute(
            f"""
            SELECT id, source, message_id, sender_address_hash, detected_at, idempotency_key
              FROM items
             WHERE {phone}
               AND watch_evaluated = 0
             ORDER BY detected_at, id
            """
        ).fetchall()
        return _ok(items=[dict(row) for row in rows])
    except sqlite3.OperationalError as exc:
        text = str(exc).lower()
        return _no("locked" if "locked" in text or "busy" in text else "error")
    except Exception:
        return _no("error")


def mark_watch_evaluated(
    conn: sqlite3.Connection,
    item_id: str,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    # P10-STORE: the marker is saved only after match calls return ok or already — R2
    return _call(_mark_watch_evaluated, conn, item_id, now=now)


def _mark_watch_evaluated(
    conn: sqlite3.Connection,
    item_id: str,
    *,
    now: Optional[datetime],
) -> Dict[str, Any]:
    stamp = _iso(_now(now))
    conn.execute("BEGIN IMMEDIATE")
    row = conn.execute(
        "SELECT source, watch_evaluated, closed_at FROM items WHERE id = ?",
        (item_id,),
    ).fetchone()
    if row is None or row["source"] not in PHONE_SOURCES:
        _rollback(conn)
        return _no("illegal_transition")
    if int(row["watch_evaluated"] or 0) == 1:
        conn.execute("COMMIT")
        return _ok(already=True)
    cur = conn.execute(
        """
        UPDATE items
           SET watch_evaluated = 1, updated_at = ?
         WHERE id = ? AND watch_evaluated = 0
        """,
        (stamp, item_id),
    )
    if cur.rowcount != 1:
        _rollback(conn)
        return _no("illegal_transition")
    conn.execute("COMMIT")
    return _ok()


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
    # P9-RANK: Gmail only, and body IS NOT NULL (an empty string may be claimed) — P9-D08
    # P10-STORE: ranking_source model keeps phone rows out of this claim — P10-D11
    if (
        row is None
        or row["source"] != "gmail"
        or row["ranking_source"] != "model"
        or row["processing"] != "unranked"
        or row["closed_at"]
        or row["content_state"] != "available"
        or row["body"] is None
    ):
        _rollback(conn)
        return _no("not_rankable")
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
    # P9-RANK: the body is deleted and eligibility is written in this same transaction — P9-D08
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
    row = _item(conn, item_id)
    if row is None:
        _rollback(conn)
        return _no("gone")
    if row["closed_at"] or row["content_state"] != "available" or row["processing"] != "unranked":
        _rollback(conn)
        return _no("not_rankable")
    attempt = conn.execute(
        """
        SELECT status, lease_expires_at FROM item_attempts
         WHERE attempt_id = ? AND item_id = ? AND purpose = 'rank'
        """,
        (attempt_id, item_id),
    ).fetchone()
    if attempt is None:
        _rollback(conn)
        return _no("attempt_mismatch")
    if attempt["status"] != "open" or attempt["lease_expires_at"] <= stamp:
        _rollback(conn)
        return _no("lease_expired")
    if int(row["loop_matched"]):
        eligibility = "eligible"
        eligible_at = row["eligible_at"] or stamp
    elif label == "ignore":
        eligibility = "suppressed"
        eligible_at = row["eligible_at"]
    else:
        eligibility = "eligible"
        eligible_at = stamp
    cur = conn.execute(
        """
        UPDATE items
           SET processing = 'ranked',
               label = ?,
               gist = ?,
               body = NULL,
               ranked_at = ?,
               eligibility = ?,
               eligible_at = ?,
               updated_at = ?
         WHERE id = ?
           AND processing = 'unranked'
           AND closed_at IS NULL
           AND content_state = 'available'
        """,
        (label, gist, stamp, eligibility, eligible_at, stamp, item_id),
    )
    if cur.rowcount != 1:
        _rollback(conn)
        return _no("not_rankable")
    done = conn.execute(
        """
        UPDATE item_attempts
           SET status = 'completed'
         WHERE attempt_id = ? AND item_id = ? AND purpose = 'rank' AND status = 'open'
           AND lease_expires_at > ?
        """,
        (attempt_id, item_id, stamp),
    )
    if done.rowcount != 1:
        _rollback(conn)
        return _no("lease_expired")
    conn.execute("COMMIT")
    return _ok(eligibility=eligibility)


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
        return _no("gone")
    if row["closed_at"] or row["content_state"] != "available" or row["processing"] != "unranked":
        _rollback(conn)
        return _no("not_rankable")
    attempt = conn.execute(
        """
        SELECT status, lease_expires_at FROM item_attempts
         WHERE attempt_id = ? AND item_id = ? AND purpose = 'rank'
        """,
        (attempt_id, item_id),
    ).fetchone()
    if attempt is None:
        _rollback(conn)
        return _no("attempt_mismatch")
    if attempt["status"] != "open" or attempt["lease_expires_at"] <= stamp:
        _rollback(conn)
        return _no("lease_expired")
    attempts = int(row["rank_attempts"]) + 1
    processing = "rank_failed" if attempts >= RANK_ATTEMPT_CAP else "unranked"
    # P9-RANK: the capped failure deletes the body in this same write — P9-D07
    cur = conn.execute(
        """
        UPDATE items
           SET processing = ?,
               rank_attempts = ?,
               body = CASE WHEN ? = 'rank_failed' THEN NULL ELSE body END,
               updated_at = ?
         WHERE id = ? AND processing = 'unranked'
           AND closed_at IS NULL AND content_state = 'available'
        """,
        (processing, attempts, processing, stamp, item_id),
    )
    if cur.rowcount != 1:
        _rollback(conn)
        return _no("not_rankable")
    done = conn.execute(
        """
        UPDATE item_attempts
           SET status = 'released'
         WHERE attempt_id = ? AND item_id = ? AND purpose = 'rank' AND status = 'open'
           AND lease_expires_at > ?
        """,
        (attempt_id, item_id, stamp),
    )
    if done.rowcount != 1:
        _rollback(conn)
        return _no("lease_expired")
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


def release_rank_transient(
    conn: sqlite3.Connection,
    item_id: str,
    attempt_id: str,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    # P9-RANK: a provider or store failure releases the lease and does not count — P9-D08
    return _call(_release_rank_transient, conn, item_id, attempt_id, now=now)


def _release_rank_transient(
    conn: sqlite3.Connection,
    item_id: str,
    attempt_id: str,
    *,
    now: Optional[datetime],
) -> Dict[str, Any]:
    del now
    conn.execute("BEGIN IMMEDIATE")
    cur = conn.execute(
        """
        UPDATE item_attempts
           SET status = 'released'
         WHERE attempt_id = ? AND item_id = ? AND purpose = 'rank' AND status = 'open'
        """,
        (attempt_id, item_id),
    )
    conn.execute("COMMIT")
    return _ok(released=cur.rowcount)


RANKER_STATES = frozenset(
    {
        "idle",
        "processing",
        "backing_off",
        "provider_unavailable",
        "auth_unavailable",
        "worker_failed",
    }
)


def write_ranker_status(
    conn: sqlite3.Connection,
    state: str,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    return _call(_write_ranker_status, conn, state, now=now)


def _write_ranker_status(
    conn: sqlite3.Connection,
    state: str,
    *,
    now: Optional[datetime],
) -> Dict[str, Any]:
    if state not in RANKER_STATES:
        return _no("bad_args")
    stamp = _iso(_now(now))
    conn.execute("BEGIN IMMEDIATE")
    for key, value in (("ranker_state", state), ("ranker_progress_at", stamp)):
        conn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
    conn.execute("COMMIT")
    return _ok(state=state)


def claim_next_rank(
    conn: sqlite3.Connection,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    return _call(_claim_next_rank, conn, now=now)


def _claim_next_rank(
    conn: sqlite3.Connection,
    *,
    now: Optional[datetime],
) -> Dict[str, Any]:
    stamp = _iso(_now(now))
    row = conn.execute(
        """
        SELECT id FROM items
         WHERE source = 'gmail'
           AND ranking_source = 'model'
           AND processing = 'unranked'
           AND closed_at IS NULL
           AND content_state = 'available'
           AND body IS NOT NULL
           AND NOT EXISTS (
             SELECT 1 FROM item_attempts
              WHERE item_id = items.id AND purpose = 'rank' AND status = 'open'
                AND lease_expires_at > ?
           )
         ORDER BY detected_at
         LIMIT 1
        """,
        (stamp,),
    ).fetchone()
    if row is None:
        return _ok(claimed=False)
    claimed = _claim_rank(conn, row["id"], now=now)
    if not claimed.get("ok"):
        return claimed
    return _ok(claimed=True, id=row["id"], attempt_id=claimed["attempt_id"])


def rank_calendar(
    conn: sqlite3.Connection,
    item_id: str,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    # P9-RANK: calendar is code only. The label stays NULL — P9-D08
    return _call(_rank_calendar, conn, item_id, now=now)


def _rank_calendar(
    conn: sqlite3.Connection,
    item_id: str,
    *,
    now: Optional[datetime],
) -> Dict[str, Any]:
    stamp = _iso(_now(now))
    conn.execute("BEGIN IMMEDIATE")
    row = _item(conn, item_id)
    if row is None:
        _rollback(conn)
        return _no("gone")
    if (
        row["source"] != "calendar"
        or row["processing"] != "unranked"
        or row["closed_at"]
        or row["content_state"] != "available"
    ):
        _rollback(conn)
        return _no("not_rankable")
    eligible_at = row["eligible_at"] or stamp
    cur = conn.execute(
        """
        UPDATE items
           SET processing = 'ranked',
               label = NULL,
               gist = NULL,
               ranked_at = ?,
               eligibility = 'eligible',
               eligible_at = ?,
               updated_at = ?
         WHERE id = ?
           AND source = 'calendar'
           AND processing = 'unranked'
           AND closed_at IS NULL
           AND content_state = 'available'
        """,
        (stamp, eligible_at, stamp, item_id),
    )
    if cur.rowcount != 1:
        _rollback(conn)
        return _no("not_rankable")
    conn.execute("COMMIT")
    return _ok()


def rank_next_calendar(
    conn: sqlite3.Connection,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    return _call(_rank_next_calendar, conn, now=now)


def _rank_next_calendar(
    conn: sqlite3.Connection,
    *,
    now: Optional[datetime],
) -> Dict[str, Any]:
    row = conn.execute(
        """
        SELECT id FROM items
         WHERE source = 'calendar'
           AND processing = 'unranked'
           AND closed_at IS NULL
           AND content_state = 'available'
         ORDER BY detected_at
         LIMIT 1
        """
    ).fetchone()
    if row is None:
        return _ok(ranked=False)
    done = _rank_calendar(conn, row["id"], now=now)
    if not done.get("ok"):
        return done
    return _ok(ranked=True, id=row["id"])


def sweep_rank_eligibility(
    conn: sqlite3.Connection,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    # P9-RANK: finishes a ranked row whose eligibility write did not land — P9-D08
    return _call(_sweep_rank_eligibility, conn, now=now)


def _sweep_rank_eligibility(
    conn: sqlite3.Connection,
    *,
    now: Optional[datetime],
) -> Dict[str, Any]:
    stamp = _iso(_now(now))
    conn.execute("BEGIN IMMEDIATE")
    eligible = conn.execute(
        """
        UPDATE items
           SET eligibility = 'eligible',
               eligible_at = COALESCE(eligible_at, ?),
               updated_at = ?
         WHERE processing = 'ranked'
           AND eligibility = 'pending'
           AND closed_at IS NULL
           AND (
             label IN ('urgent', 'important', 'normal')
             OR source = 'calendar'
             OR loop_matched = 1
           )
        """,
        (stamp, stamp),
    )
    suppressed = conn.execute(
        """
        UPDATE items
           SET eligibility = 'suppressed',
               updated_at = ?
         WHERE processing = 'ranked'
           AND eligibility = 'pending'
           AND closed_at IS NULL
           AND label = 'ignore'
           AND loop_matched = 0
        """,
        (stamp,),
    )
    conn.execute("COMMIT")
    return _ok(eligible=eligible.rowcount, suppressed=suppressed.rowcount)


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
    turn_id: Optional[str] = None,
    include_unselected: bool = False,
) -> Dict[str, Any]:
    # P9-STORE: acknowledged only on a ticket turn — P9-D09
    # P9-SURFACE: a listed item can be acknowledged before it was injected — P9-D10
    sources = ("none", "selected", "possibly_surfaced") if include_unselected else ("selected", "possibly_surfaced")
    return _call(
        _set_conversation,
        conn,
        item_id,
        "acknowledged",
        sources,
        now=now,
        ticket=True,
        turn_id=turn_id,
    )


def _set_conversation(
    conn: sqlite3.Connection,
    item_id: str,
    dest: str,
    sources: Sequence[str],
    *,
    now: Optional[datetime],
    ticket: bool,
    turn_id: Optional[str] = None,
) -> Dict[str, Any]:
    if ticket and not _ticket_ok(turn_id):
        return _no("origin")
    stamp = _iso(_now(now))
    marks = ",".join("?" for _ in sources)
    extra = ""
    ack_sql = ""
    params: List[Any] = [dest, stamp]
    if dest == "acknowledged":
        # P9-SURFACE: a closed or suppressed row cannot be acknowledged — P9-D10
        ack_sql = ", acknowledged_at = ?"
        params.append(stamp)
        extra = (
            " AND closed_at IS NULL"
            " AND eligibility NOT IN ('suppressed', 'expired')"
            " AND content_state = 'available'"
        )
    elif dest == "selected":
        # P9-SURFACE: selection requires an open eligible row — P9-D10
        extra = (
            " AND eligibility = 'eligible'"
            " AND closed_at IS NULL"
            " AND content_state = 'available'"
            " AND processing = 'ranked'"
        )
    params.extend((item_id, *sources))
    conn.execute("BEGIN IMMEDIATE")
    cur = conn.execute(
        f"""
        UPDATE items
           SET conversation = ?, updated_at = ?{ack_sql}
         WHERE id = ? AND conversation IN ({marks}){extra}
        """,
        tuple(params),
    )
    if cur.rowcount != 1:
        _rollback(conn)
        return _no("illegal_transition")
    if dest == "acknowledged":
        _clear_phone_content_locked(conn, item_id)
    conn.execute("COMMIT")
    return _ok()


def claim_speech(
    conn: sqlite3.Connection,
    item_id: str,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    return _call(_claim_speech, conn, item_id, now=now)


def _speech_block_reason(row: Optional[sqlite3.Row], earliest_surface: str, oldest: str) -> Optional[str]:
    # P9-SPEAK: the label is not a speech check. An open surface attempt blocks only inside its TTL — P9-D11
    if row is None:
        return "not_found"
    # P10-STORE: phone rows stay out of speech until Track 5 removes the hold — P10-D11
    if row["source"] in PHONE_CONVERSATION_HOLD:
        return "phone_deferred"
    if int(row["loop_matched"] or 0) != 1:
        return "not_loop_matched"
    if row["eligibility"] != "eligible":
        return "not_eligible"
    if row["delivery"] != "none":
        return "delivery_held"
    if row["closed_reason"] == "dismissed":
        return "dismissed"
    if row["closed_at"]:
        return "closed"
    if row["acknowledged_at"] or row["conversation"] == "acknowledged":
        return "acknowledged"
    if row["content_state"] == "content_expired":
        return "content_expired"
    if row["content_state"] != "available":
        return "content_unavailable"
    if row["attempt_id"] and row["attempt_at"] and row["attempt_at"] >= earliest_surface:
        return "surface_attempt_open"
    if row["detected_at"] < oldest:
        return "too_old"
    return None


def _claim_speech(
    conn: sqlite3.Connection,
    item_id: str,
    *,
    now: Optional[datetime],
) -> Dict[str, Any]:
    clock = _now(now)
    stamp = _iso(clock)
    lease = _iso(clock + timedelta(seconds=SPEECH_CLAIM_LEASE_SECONDS))
    earliest_surface = _iso(clock - timedelta(seconds=SURFACE_ATTEMPT_TTL_SECONDS))
    oldest = _iso(clock - timedelta(seconds=SPEECH_MAX_AGE_SECONDS))
    # P9-SPEAK: recovery commits on its own. A refused claim must not roll it back — P9-D11
    recovered = _recover_speech(conn, now=clock)
    if not recovered.get("ok"):
        return recovered
    conn.execute("BEGIN IMMEDIATE")
    reason = _speech_block_reason(_item(conn, item_id), earliest_surface, oldest)
    if reason:
        _rollback(conn)
        return _no(reason)
    hold = _phone_hold_sql()
    cur = conn.execute(
        f"""
        UPDATE items
           SET delivery = 'claimed', updated_at = ?
         WHERE id = ?
           AND loop_matched = 1
           AND eligibility = 'eligible'
           AND delivery = 'none'
           AND closed_at IS NULL
           AND acknowledged_at IS NULL
           AND conversation != 'acknowledged'
           AND content_state = 'available'
           AND (
             attempt_id IS NULL
             OR attempt_at IS NULL
             OR attempt_at < ?
           )
           AND detected_at >= ?
           AND {hold}
        """,
        (stamp, item_id, earliest_surface, oldest),
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


def claim_next_speech(
    conn: sqlite3.Connection,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    return _call(_claim_next_speech, conn, now=now)


def _claim_next_speech(
    conn: sqlite3.Connection,
    *,
    now: Optional[datetime],
) -> Dict[str, Any]:
    """Recovery commits first. The next transaction claims the oldest speakable row."""
    clock = _now(now)
    recovered = _recover_speech(conn, now=clock)
    if not recovered.get("ok"):
        return recovered
    stamp = _iso(clock)
    lease = _iso(clock + timedelta(seconds=SPEECH_CLAIM_LEASE_SECONDS))
    earliest_surface = _iso(clock - timedelta(seconds=SURFACE_ATTEMPT_TTL_SECONDS))
    oldest = _iso(clock - timedelta(seconds=SPEECH_MAX_AGE_SECONDS))
    conn.execute("BEGIN IMMEDIATE")
    hold = _phone_hold_sql()
    row = conn.execute(
        f"""
        SELECT id, source FROM items
         WHERE loop_matched = 1
           AND eligibility = 'eligible'
           AND delivery = 'none'
           AND closed_at IS NULL
           AND acknowledged_at IS NULL
           AND conversation != 'acknowledged'
           AND content_state = 'available'
           AND (
             attempt_id IS NULL
             OR attempt_at IS NULL
             OR attempt_at < ?
           )
           AND detected_at >= ?
           AND {hold}
         ORDER BY detected_at, id
         LIMIT 1
        """,
        (earliest_surface, oldest),
    ).fetchone()
    if row is None:
        conn.execute("COMMIT")
        return _no("nothing_speakable")
    cur = conn.execute(
        f"""
        UPDATE items
           SET delivery = 'claimed', updated_at = ?
         WHERE id = ?
           AND loop_matched = 1
           AND eligibility = 'eligible'
           AND delivery = 'none'
           AND closed_at IS NULL
           AND acknowledged_at IS NULL
           AND conversation != 'acknowledged'
           AND content_state = 'available'
           AND (
             attempt_id IS NULL
             OR attempt_at IS NULL
             OR attempt_at < ?
           )
           AND detected_at >= ?
           AND {hold}
        """,
        (stamp, row["id"], earliest_surface, oldest),
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
        (attempt_id, row["id"], lease, stamp),
    )
    conn.execute("COMMIT")
    return _ok(item_id=row["id"], attempt_id=attempt_id, source=row["source"])


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
    # P9-SPEAK: a retry of the same completion is the lost response, not a second delivery — P9-D11
    already = _speech_outcome_already(conn, item_id, attempt_id, "delivered", "completed")
    if already == "same":
        conn.execute("COMMIT")
        return _ok(already=True)
    if already == "other":
        _rollback(conn)
        return _no("illegal_transition")
    attempt = conn.execute(
        """
        SELECT status FROM item_attempts
         WHERE attempt_id = ? AND item_id = ? AND purpose = 'speech' AND status = 'open'
        """,
        (attempt_id, item_id),
    ).fetchone()
    if attempt is None:
        _rollback(conn)
        return _no("attempt_mismatch")
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
    # P9-SPEAK: a retry of the same uncertain outcome does not speak again — P9-D11
    already = _speech_outcome_already(conn, item_id, attempt_id, "delivery_uncertain", "uncertain")
    if already == "same":
        conn.execute("COMMIT")
        return _ok(already=True)
    if already == "other":
        _rollback(conn)
        return _no("illegal_transition")
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


def _speech_outcome_already(
    conn: sqlite3.Connection,
    item_id: str,
    attempt_id: str,
    delivery: str,
    status: str,
) -> Optional[str]:
    attempt = conn.execute(
        """
        SELECT status FROM item_attempts
         WHERE attempt_id = ? AND item_id = ? AND purpose = 'speech'
        """,
        (attempt_id, item_id),
    ).fetchone()
    if attempt is None:
        return None
    item = _item(conn, item_id)
    if item is None:
        return None
    if item["delivery"] == delivery and attempt["status"] == status:
        return "same"
    if attempt["status"] in ("completed", "released", "uncertain"):
        return "other"
    if item["delivery"] in ("delivered", "delivery_uncertain", "none") and item["delivery"] != "none":
        return "other"
    return None


def release_speech_claim(
    conn: sqlite3.Connection,
    item_id: str,
    attempt_id: str,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    # P9-SPEAK: cancel before audio releases this claim only — P9-D11
    return _call(_release_speech_claim, conn, item_id, attempt_id, now=now)


def _release_speech_claim(
    conn: sqlite3.Connection,
    item_id: str,
    attempt_id: str,
    *,
    now: Optional[datetime],
) -> Dict[str, Any]:
    stamp = _iso(_now(now))
    conn.execute("BEGIN IMMEDIATE")
    attempt = conn.execute(
        """
        SELECT status FROM item_attempts
         WHERE attempt_id = ? AND item_id = ? AND purpose = 'speech'
        """,
        (attempt_id, item_id),
    ).fetchone()
    item = _item(conn, item_id)
    if attempt is not None and attempt["status"] == "released" and item is not None and item["delivery"] == "none":
        conn.execute("COMMIT")
        return _ok(already=True)
    if attempt is None or attempt["status"] != "open" or item is None or item["delivery"] != "claimed":
        _rollback(conn)
        return _no("illegal_transition")
    conn.execute(
        """
        UPDATE items SET delivery = 'none', updated_at = ?
         WHERE id = ? AND delivery = 'claimed'
        """,
        (stamp, item_id),
    )
    conn.execute(
        """
        UPDATE item_attempts SET status = 'released'
         WHERE attempt_id = ? AND item_id = ? AND purpose = 'speech' AND status = 'open'
        """,
        (attempt_id, item_id),
    )
    conn.execute("COMMIT")
    return _ok()


def release_speech_lease(
    conn: sqlite3.Connection,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    return _call(_recover_speech, conn, now=now)


def _recover_speech_locked(conn: sqlite3.Connection, stamp: str) -> tuple:
    """Caller holds the transaction. Expired claims return to none. Expired speech becomes uncertain."""
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
    return released_n, uncertain_n


def _recover_speech(
    conn: sqlite3.Connection,
    *,
    now: Optional[datetime],
) -> Dict[str, Any]:
    """Claimed and expired returns to none. Speech started and expired becomes uncertain."""
    stamp = _iso(_now(now))
    conn.execute("BEGIN IMMEDIATE")
    released_n, uncertain_n = _recover_speech_locked(conn, stamp)
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
    _clear_phone_content_locked(conn, item_id)
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
    name_source: str = "mail",
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
        name_source=name_source,
    )


def _insert_loop(conn: sqlite3.Connection, **kwargs: Any) -> Dict[str, Any]:
    if not _ticket_ok():
        return _no("origin")
    days = int(kwargs["expiry_days"])
    if days < 1 or days > LOOP_MAX_EXPIRY_DAYS:
        return _no("bad_args")
    name_source = str(kwargs.get("name_source") or "mail")
    if name_source not in NAME_SOURCES:
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
          sender_display_name, subject, name_source
        ) VALUES (?, 'open', ?, ?, ?, ?, NULL, 0, ?, ?, ?, ?, ?, ?, ?)
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
            name_source,
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
    row = conn.execute(
        "SELECT status, matched_at FROM loops WHERE id = ?",
        (loop_id,),
    ).fetchone()
    if row is None or row["status"] != "open":
        _rollback(conn)
        return _no("illegal_transition")
    if row["matched_at"]:
        conn.execute("COMMIT")
        return _ok(already=True)
    cur = conn.execute(
        """
        UPDATE loops
           SET matched_at = ?
         WHERE id = ? AND status = 'open' AND matched_at IS NULL
        """,
        (stamp, loop_id),
    )
    if cur.rowcount != 1:
        _rollback(conn)
        return _no("illegal_transition")
    conn.execute("COMMIT")
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
    forget_stamp = _iso(_now(None))
    for item_id in delete_ids:
        gone = conn.execute("SELECT source, idempotency_key FROM items WHERE id = ?", (item_id,)).fetchone()
        if gone is not None and gone["source"] in PHONE_SOURCES:
            _write_tombstone_locked(conn, str(gone["idempotency_key"]), forget_stamp)
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
                   attachment_has = NULL, attachment_count = NULL, attachment_kind = NULL,
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
    tomb_cutoff = _iso(clock - timedelta(days=PHONE_TOMBSTONE_KEEP_DAYS))
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
               content_state = 'content_expired',
               eligibility = CASE WHEN loop_matched = 1 THEN 'eligible' ELSE 'expired' END,
               eligible_at = CASE
                 WHEN loop_matched = 1 THEN COALESCE(eligible_at, ?)
                 ELSE eligible_at
               END
         WHERE processing = 'unranked'
           AND detected_at <= ?
           AND content_state = 'available'
           AND body IS NOT NULL
        """,
        (stamp, body_cutoff),
    )
    # P9-RANK: no body survives 7 days, including rank_failed — P9-D07
    other_bodies = conn.execute(
        """
        UPDATE items
           SET body = NULL
         WHERE processing != 'unranked'
           AND detected_at <= ?
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
           AND (
             detected_at <= ?
             OR (
               delivery = 'delivered'
               AND (acknowledged_at IS NOT NULL OR closed_at IS NOT NULL)
             )
           )
           AND (
             subject IS NOT NULL OR snippet IS NOT NULL OR gist IS NOT NULL
             OR sender_display_name IS NOT NULL
           )
        """,
        (text_cutoff,),
    )
    # P10-STORE: phone attachment metadata ages out with the other display fields — P10-D03
    phone = _phone_source_sql()
    conn.execute(
        f"""
        UPDATE items
           SET attachment_has = NULL,
               attachment_count = NULL,
               attachment_kind = NULL
         WHERE {phone}
           AND detected_at <= ?
           AND (
             attachment_has IS NOT NULL
             OR attachment_count IS NOT NULL
             OR attachment_kind IS NOT NULL
           )
        """,
        (text_cutoff,),
    )
    # P10-STORE: a cleared phone row must not accept a later body — P10-D03
    _expire_cleared_phone_content_locked(conn)
    # P9-SURFACE: calendar rows have no mail text; expiring them hides the change — P9-D10
    expired = conn.execute(
        """
        UPDATE items
           SET content_state = 'content_expired'
         WHERE content_state = 'available'
           AND source != 'calendar'
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
    conn.execute(
        "DELETE FROM phone_tombstones WHERE created_at <= ?",
        (tomb_cutoff,),
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
    aged = _age_out_items(conn, stamp, text_cutoff)
    conn.execute("COMMIT")
    return _ok(
        bodies=bodies.rowcount + other_bodies.rowcount,
        texts=texts.rowcount,
        content_expired=expired.rowcount,
        deliveries_deleted=old_deliveries.rowcount,
        loops_expired=loops.rowcount,
        loops_text_cleared=loop_text.rowcount,
        aged_out=aged,
        speech_released=recovery.get("released", 0),
        speech_uncertain=recovery.get("uncertain", 0),
    )


def _age_out_items(conn: sqlite3.Connection, stamp: str, cutoff: str) -> int:
    # P9-SURFACE: purge closes rows past the list window; an open loop keeps its matches — P9-D10
    protected: Set[str] = set()
    for loop in conn.execute(
        "SELECT source_ids_json FROM loops WHERE status = 'open'"
    ):
        try:
            values = json.loads(loop["source_ids_json"] or "[]")
        except json.JSONDecodeError:
            values = []
        for value in values:
            if value:
                protected.add(str(value))
    rows = conn.execute(
        """
        SELECT id, message_id, thread_id, event_id, loop_matched
          FROM items
         WHERE closed_at IS NULL
           AND detected_at <= ?
           AND delivery NOT IN ('claimed', 'speech_started')
        """,
        (cutoff,),
    ).fetchall()
    aged = 0
    for row in rows:
        if int(row["loop_matched"] or 0):
            keys = {
                str(row["id"] or ""),
                str(row["message_id"] or ""),
                str(row["thread_id"] or ""),
                str(row["event_id"] or ""),
            }
            keys.discard("")
            if keys & protected:
                continue
        cur = conn.execute(
            """
            UPDATE items
               SET closed_at = ?, updated_at = ?, closed_reason = 'aged_out'
             WHERE id = ?
               AND closed_at IS NULL
               AND delivery NOT IN ('claimed', 'speech_started')
            """,
            (stamp, stamp, row["id"]),
        )
        aged += cur.rowcount
    return aged


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


def read_cursor(
    conn: sqlite3.Connection,
    source: str,
    scope_key: str,
) -> Dict[str, Any]:
    # P9-WATCH: one cursor per mailbox and per calendar id — P9-D04
    try:
        row = conn.execute(
            """
            SELECT cursor_value, updated_at FROM cursors
             WHERE source = ? AND scope_key = ?
            """,
            (source, scope_key),
        ).fetchone()
    except sqlite3.OperationalError as exc:
        text = str(exc).lower()
        return _no("locked" if "locked" in text or "busy" in text else "error")
    if row is None:
        return _ok(cursor_value=None, updated_at=None)
    return _ok(cursor_value=row["cursor_value"], updated_at=row["updated_at"])


def write_cursor(
    conn: sqlite3.Connection,
    source: str,
    scope_key: str,
    cursor_value: str,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    # P9-WATCH: the cursor moves only after the caller finished the page — P9-D04
    return _call(
        _write_cursor,
        conn,
        source,
        scope_key,
        cursor_value,
        now=now,
    )


def _write_cursor(
    conn: sqlite3.Connection,
    source: str,
    scope_key: str,
    cursor_value: str,
    *,
    now: Optional[datetime],
) -> Dict[str, Any]:
    stamp = _iso(_now(now))
    conn.execute("BEGIN IMMEDIATE")
    conn.execute(
        """
        INSERT INTO cursors (source, scope_key, cursor_value, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(source, scope_key) DO UPDATE SET
          cursor_value = excluded.cursor_value,
          updated_at = excluded.updated_at
        """,
        (source, scope_key, cursor_value, stamp),
    )
    conn.execute("COMMIT")
    return _ok()


def clear_cursor(conn: sqlite3.Connection, source: str, scope_key: str) -> Dict[str, Any]:
    return _call(_clear_cursor, conn, source, scope_key)


def _clear_cursor(conn: sqlite3.Connection, source: str, scope_key: str) -> Dict[str, Any]:
    conn.execute("BEGIN IMMEDIATE")
    conn.execute(
        "DELETE FROM cursors WHERE source = ? AND scope_key = ?",
        (source, scope_key),
    )
    conn.execute("COMMIT")
    return _ok()


def get_calendar_event(
    conn: sqlite3.Connection,
    calendar_id: str,
    event_id: str,
) -> Dict[str, Any]:
    # P9-WATCH: known state is ids, status, and times — P9-D04
    try:
        row = conn.execute(
            """
            SELECT event_updated, calendar_status, start_at, end_at
              FROM calendar_events
             WHERE calendar_id = ? AND event_id = ?
            """,
            (calendar_id, event_id),
        ).fetchone()
    except sqlite3.OperationalError as exc:
        text = str(exc).lower()
        return _no("locked" if "locked" in text or "busy" in text else "error")
    if row is None:
        return _ok(known=False)
    return _ok(
        known=True,
        event_updated=row["event_updated"],
        calendar_status=row["calendar_status"] or "",
        start_at=row["start_at"] or "",
        end_at=row["end_at"] or "",
    )


def save_calendar_event(
    conn: sqlite3.Connection,
    *,
    calendar_id: str,
    event_id: str,
    event_updated: str,
    calendar_status: str = "",
    start_at: str = "",
    end_at: str = "",
    recurring_event_id: str = "",
    original_start: str = "",
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    # P9-WATCH: one row per event id; a later update replaces it — P9-D04
    return _call(
        _save_calendar_event,
        conn,
        calendar_id=calendar_id,
        event_id=event_id,
        event_updated=event_updated,
        calendar_status=calendar_status,
        start_at=start_at,
        end_at=end_at,
        recurring_event_id=recurring_event_id,
        original_start=original_start,
        now=now,
    )


def _save_calendar_event(conn: sqlite3.Connection, **kwargs: Any) -> Dict[str, Any]:
    stamp = _iso(_now(kwargs.get("now")))
    conn.execute("BEGIN IMMEDIATE")
    conn.execute(
        """
        INSERT INTO calendar_events (
          calendar_id, event_id, event_updated, calendar_status, start_at, end_at,
          recurring_event_id, original_start, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(calendar_id, event_id) DO UPDATE SET
          event_updated = excluded.event_updated,
          calendar_status = excluded.calendar_status,
          start_at = excluded.start_at,
          end_at = excluded.end_at,
          recurring_event_id = excluded.recurring_event_id,
          original_start = excluded.original_start,
          updated_at = excluded.updated_at
        """,
        (
            kwargs["calendar_id"],
            kwargs["event_id"],
            kwargs["event_updated"],
            kwargs.get("calendar_status") or "",
            kwargs.get("start_at") or "",
            kwargs.get("end_at") or "",
            kwargs.get("recurring_event_id") or "",
            kwargs.get("original_start") or "",
            stamp,
        ),
    )
    conn.execute("COMMIT")
    return _ok()


def find_item_id(
    conn: sqlite3.Connection,
    *,
    source: str,
    message_id: str = "",
    event_id: str = "",
    event_updated: str = "",
) -> Dict[str, Any]:
    # P9-WATCH: replay finds the row the idempotency key already stored — P9-D06
    try:
        key = _idempotency_key(
            source=source,
            message_id=message_id,
            event_id=event_id,
            event_updated=event_updated,
        )
        row = conn.execute(
            "SELECT id FROM items WHERE idempotency_key = ?",
            (key,),
        ).fetchone()
    except sqlite3.OperationalError as exc:
        text = str(exc).lower()
        return _no("locked" if "locked" in text or "busy" in text else "error")
    except Exception:
        return _no("bad_args")
    if row is None:
        return _ok(id=None)
    return _ok(id=row["id"])


def gmail_message_known(conn: sqlite3.Connection, message_id: str) -> Dict[str, Any]:
    try:
        row = conn.execute(
            "SELECT id FROM items WHERE source = 'gmail' AND message_id = ?",
            (message_id,),
        ).fetchone()
    except sqlite3.OperationalError as exc:
        text = str(exc).lower()
        return _no("locked" if "locked" in text or "busy" in text else "error")
    return _ok(known=row is not None)


def list_open_loop_predicates(conn: sqlite3.Connection) -> Dict[str, Any]:
    # P9-WATCH: the watcher evaluates predicates; names stay off this read — P9-D09
    try:
        rows = conn.execute(
            """
            SELECT id, intent, predicate_json
              FROM loops
             WHERE status = 'open'
             ORDER BY created_at
            """
        ).fetchall()
    except sqlite3.OperationalError as exc:
        text = str(exc).lower()
        return _no("locked" if "locked" in text or "busy" in text else "error")
    found = []
    for row in rows:
        try:
            predicate = json.loads(row["predicate_json"] or "{}")
        except json.JSONDecodeError:
            predicate = {}
        found.append({"id": row["id"], "intent": row["intent"], "predicate": predicate})
    return _ok(loops=found)


def item_loop_state(conn: sqlite3.Connection, item_id: str) -> Dict[str, Any]:
    try:
        row = conn.execute(
            """
            SELECT eligibility, loop_matched, closed_at
              FROM items WHERE id = ?
            """,
            (item_id,),
        ).fetchone()
    except sqlite3.OperationalError as exc:
        text = str(exc).lower()
        return _no("locked" if "locked" in text or "busy" in text else "error")
    if row is None:
        return _no("missing")
    return _ok(
        eligibility=row["eligibility"],
        loop_matched=int(row["loop_matched"]),
        closed=row["closed_at"] is not None,
    )


def set_loop_matched(
    conn: sqlite3.Connection,
    item_id: str,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    # P9-WATCH: backstop when the row is already eligible — P9-D09
    return _call(_set_loop_matched, conn, item_id, now=now)


def _set_loop_matched(
    conn: sqlite3.Connection,
    item_id: str,
    *,
    now: Optional[datetime],
) -> Dict[str, Any]:
    stamp = _iso(_now(now))
    conn.execute("BEGIN IMMEDIATE")
    row = conn.execute(
        "SELECT eligibility, loop_matched, closed_at FROM items WHERE id = ?",
        (item_id,),
    ).fetchone()
    if row is None or row["closed_at"] is not None:
        _rollback(conn)
        return _no("illegal_transition")
    if int(row["loop_matched"]) == 1:
        conn.execute("COMMIT")
        return _ok(already=True)
    cur = conn.execute(
        """
        UPDATE items
           SET loop_matched = 1, updated_at = ?
         WHERE id = ? AND closed_at IS NULL AND loop_matched = 0
        """,
        (stamp, item_id),
    )
    if cur.rowcount != 1:
        _rollback(conn)
        return _no("illegal_transition")
    conn.execute("COMMIT")
    return _ok()


def close_loop_from_match(
    conn: sqlite3.Connection,
    loop_id: str,
    closed_intent: str,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    # P9-WATCH: a terminal calendar predicate closes without a ticket — P9-D09
    return _call(_close_loop_from_match, conn, loop_id, closed_intent, now=now)


def _close_loop_from_match(
    conn: sqlite3.Connection,
    loop_id: str,
    closed_intent: str,
    *,
    now: Optional[datetime],
) -> Dict[str, Any]:
    if closed_intent not in ("cancelled", "status_change"):
        return _no("bad_args")
    conn.execute("BEGIN IMMEDIATE")
    row = conn.execute(
        "SELECT status, closed_intent FROM loops WHERE id = ?",
        (loop_id,),
    ).fetchone()
    if row is None:
        _rollback(conn)
        return _no("missing")
    if row["status"] != "open":
        _rollback(conn)
        if row["closed_intent"] == closed_intent:
            return _ok(already=True)
        return _no("illegal_transition")
    cur = conn.execute(
        """
        UPDATE loops
           SET status = 'closed', closed_intent = ?
         WHERE id = ? AND status = 'open'
        """,
        (closed_intent, loop_id),
    )
    if cur.rowcount != 1:
        _rollback(conn)
        return _no("illegal_transition")
    conn.execute("COMMIT")
    return _ok()


def note_watcher_reject(
    conn: sqlite3.Connection,
    *,
    source: str,
    source_id_hash: str,
    error_class: str,
    terminal: bool,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    # P9-WATCH: the record stores a class and a hash, never the message — P9-D04
    return _call(
        _note_watcher_reject,
        conn,
        source=source,
        source_id_hash=source_id_hash,
        error_class=error_class,
        terminal=terminal,
        now=now,
    )


def _note_watcher_reject(conn: sqlite3.Connection, **kwargs: Any) -> Dict[str, Any]:
    stamp = _iso(_now(kwargs.get("now")))
    source = str(kwargs["source"])
    source_hash = str(kwargs["source_id_hash"])
    error_class = str(kwargs["error_class"])
    conn.execute("BEGIN IMMEDIATE")
    row = conn.execute(
        """
        SELECT attempts FROM watcher_rejects
         WHERE source = ? AND source_id_hash = ?
        """,
        (source, source_hash),
    ).fetchone()
    attempts = int(row["attempts"]) + 1 if row else 1
    disposition = "terminal" if kwargs["terminal"] or attempts >= POISON_ATTEMPT_CAP else "transient"
    if row is None:
        conn.execute(
            """
            INSERT INTO watcher_rejects (
              source, source_id_hash, error_class, disposition, attempts, first_seen, last_seen
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (source, source_hash, error_class, disposition, attempts, stamp, stamp),
        )
    else:
        conn.execute(
            """
            UPDATE watcher_rejects
               SET error_class = ?, disposition = ?, attempts = ?, last_seen = ?
             WHERE source = ? AND source_id_hash = ?
            """,
            (error_class, disposition, attempts, stamp, source, source_hash),
        )
    conn.execute("COMMIT")
    return _ok(attempts=attempts, disposition=disposition)


def write_watcher_health(
    conn: sqlite3.Connection,
    *,
    gmail_ok: bool = False,
    calendar_ok: bool = False,
    gmail_error: Optional[str] = None,
    calendar_error: Optional[str] = None,
    needs_reconnect: Optional[bool] = None,
    recovery: bool = False,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    # P9-WATCH: one row, each source keeps its own time — P9-D12
    return _call(
        _write_watcher_health,
        conn,
        gmail_ok=gmail_ok,
        calendar_ok=calendar_ok,
        gmail_error=gmail_error,
        calendar_error=calendar_error,
        needs_reconnect=needs_reconnect,
        recovery=recovery,
        now=now,
    )


def _write_watcher_health(conn: sqlite3.Connection, **kwargs: Any) -> Dict[str, Any]:
    stamp = _iso(_now(kwargs.get("now")))
    conn.execute("BEGIN IMMEDIATE")
    row = conn.execute("SELECT * FROM watcher_health WHERE id = 1").fetchone()
    gmail_ok_at = row["gmail_ok_at"] if row else None
    calendar_ok_at = row["calendar_ok_at"] if row else None
    gmail_error = row["gmail_error"] if row else None
    calendar_error = row["calendar_error"] if row else None
    reconnect = row["needs_reconnect"] if row else None
    recovery_count = int(row["recovery_count"] or 0) if row else 0
    last_ok = row["last_ok_at"] if row else None
    if kwargs.get("gmail_ok"):
        gmail_ok_at = stamp
        gmail_error = None
        last_ok = stamp
    if kwargs.get("calendar_ok"):
        calendar_ok_at = stamp
        calendar_error = None
        last_ok = stamp
    if kwargs.get("gmail_error") is not None:
        gmail_error = kwargs["gmail_error"]
    if kwargs.get("calendar_error") is not None:
        calendar_error = kwargs["calendar_error"]
    if kwargs.get("needs_reconnect") is not None:
        reconnect = 1 if kwargs["needs_reconnect"] else 0
    if kwargs.get("recovery"):
        recovery_count += 1
    error_class = gmail_error or calendar_error
    if row is None:
        conn.execute(
            """
            INSERT INTO watcher_health (
              id, last_ok_at, error_class, updated_at,
              gmail_ok_at, calendar_ok_at, gmail_error, calendar_error,
              needs_reconnect, recovery_count
            ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                last_ok,
                error_class,
                stamp,
                gmail_ok_at,
                calendar_ok_at,
                gmail_error,
                calendar_error,
                reconnect,
                recovery_count,
            ),
        )
    else:
        conn.execute(
            """
            UPDATE watcher_health
               SET last_ok_at = ?, error_class = ?, updated_at = ?,
                   gmail_ok_at = ?, calendar_ok_at = ?, gmail_error = ?,
                   calendar_error = ?, needs_reconnect = ?, recovery_count = ?
             WHERE id = 1
            """,
            (
                last_ok,
                error_class,
                stamp,
                gmail_ok_at,
                calendar_ok_at,
                gmail_error,
                calendar_error,
                reconnect,
                recovery_count,
            ),
        )
    conn.execute("COMMIT")
    return _ok(recovery_count=recovery_count)


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


def _meta_get(conn: sqlite3.Connection, key: str) -> Optional[str]:
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    if row is None:
        return None
    return str(row["value"])


def _meta_set(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO meta (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )


def read_surface_marker(conn: sqlite3.Connection) -> Dict[str, Any]:
    # P9-SURFACE: the gap clock is this store's meta, not memory's — P9-D10
    try:
        return _ok(
            at=_meta_get(conn, META_SURFACE_MARKER),
            attempt_id=_meta_get(conn, META_SURFACE_ATTEMPT) or "",
            confirmed=_meta_get(conn, META_SURFACE_CONFIRMED) == "1",
        )
    except sqlite3.OperationalError as exc:
        text = str(exc).lower()
        return _no("locked" if "locked" in text or "busy" in text else "error")
    except Exception:
        return _no("error")


def write_surface_marker(
    conn: sqlite3.Connection,
    *,
    now: Optional[datetime] = None,
    attempt_id: str = "",
    confirmed: bool = False,
) -> Dict[str, Any]:
    # P9-SURFACE: a failed gap must not move this clock — P9-D10
    return _call(
        _write_surface_marker,
        conn,
        now=now,
        attempt_id=attempt_id,
        confirmed=confirmed,
    )


def _write_surface_marker(conn: sqlite3.Connection, **kwargs: Any) -> Dict[str, Any]:
    stamp = _iso(_now(kwargs.get("now")))
    conn.execute("BEGIN IMMEDIATE")
    _meta_set(conn, META_SURFACE_MARKER, stamp)
    _meta_set(conn, META_SURFACE_ATTEMPT, str(kwargs.get("attempt_id") or ""))
    _meta_set(conn, META_SURFACE_CONFIRMED, "1" if kwargs.get("confirmed") else "0")
    conn.execute("COMMIT")
    return _ok()


def mark_surface_confirmed(conn: sqlite3.Connection, attempt_id: str) -> Dict[str, Any]:
    # P9-SURFACE: only this attempt's confirm lets the next turn trust the marker — P9-D10
    return _call(_mark_surface_confirmed, conn, attempt_id)


def _mark_surface_confirmed(conn: sqlite3.Connection, attempt_id: str) -> Dict[str, Any]:
    conn.execute("BEGIN IMMEDIATE")
    current = _meta_get(conn, META_SURFACE_ATTEMPT) or ""
    if not attempt_id or current != attempt_id:
        _rollback(conn)
        return _no("attempt_mismatch")
    _meta_set(conn, META_SURFACE_CONFIRMED, "1")
    conn.execute("COMMIT")
    return _ok()


def list_surface_rows(conn: sqlite3.Connection) -> Dict[str, Any]:
    # P9-SURFACE: closed rows stay out of the pending counts — P9-D10
    # P10-STORE: phone rows stay out of this list until Track 5 — P10-D11
    try:
        hold = _phone_hold_sql()
        rows = conn.execute(
            f"""
            SELECT id, source, label, eligibility, processing, conversation, delivery,
                   content_state, loop_matched, gist, subject, sender_display_name,
                   sender_address, detected_at, inject_count, selected_at, acknowledged_at,
                   message_id, thread_id, event_id,
                   (
                     SELECT start_at FROM calendar_events
                      WHERE event_id = items.event_id
                      ORDER BY updated_at DESC LIMIT 1
                   ) AS start_at
              FROM items
             WHERE closed_at IS NULL
               AND {hold}
             ORDER BY detected_at
            """
        ).fetchall()
        return _ok(items=[dict(row) for row in rows])
    except sqlite3.OperationalError as exc:
        text = str(exc).lower()
        return _no("locked" if "locked" in text or "busy" in text else "error")
    except Exception:
        return _no("error")


def list_untold_lapses(conn: sqlite3.Connection) -> Dict[str, Any]:
    try:
        rows = conn.execute(
            """
            SELECT id FROM loops
             WHERE status = 'expired' AND lapse_told = 0
             ORDER BY expires_at
            """
        ).fetchall()
        return _ok(ids=[row["id"] for row in rows])
    except sqlite3.OperationalError as exc:
        text = str(exc).lower()
        return _no("locked" if "locked" in text or "busy" in text else "error")
    except Exception:
        return _no("error")


def provisional_select(
    conn: sqlite3.Connection,
    item_id: str,
    attempt_id: str,
    turn_id: str,
    *,
    now: Optional[datetime] = None,
    reinject_cap: int,
    quiet_seconds: int,
) -> Dict[str, Any]:
    # P9-SURFACE: an attempt is not a confirmed tell — P9-D10
    return _call(
        _provisional_select,
        conn,
        item_id,
        attempt_id,
        turn_id,
        now=now,
        reinject_cap=reinject_cap,
        quiet_seconds=quiet_seconds,
    )


def _provisional_select(conn: sqlite3.Connection, item_id: str, attempt_id: str, turn_id: str, **kwargs: Any) -> Dict[str, Any]:
    clock = _now(kwargs.get("now"))
    stamp = _iso(clock)
    quiet_before = _iso(clock - timedelta(seconds=int(kwargs["quiet_seconds"])))
    cap = int(kwargs["reinject_cap"])
    hold = _phone_hold_sql()
    conn.execute("BEGIN IMMEDIATE")
    cur = conn.execute(
        f"""
        UPDATE items
           SET attempt_id = ?, attempt_turn_id = ?, attempt_at = ?, updated_at = ?
         WHERE id = ?
           AND closed_at IS NULL
           AND content_state = 'available'
           AND acknowledged_at IS NULL
           AND conversation != 'acknowledged'
           AND inject_count < ?
           AND (
             (processing = 'ranked' AND eligibility = 'eligible')
             OR (loop_matched = 1 AND processing != 'rank_failed'
                 AND eligibility NOT IN ('suppressed', 'expired'))
           )
           AND conversation IN ('none', 'selected', 'possibly_surfaced')
           AND (
             conversation = 'none'
             OR selected_at IS NULL
             OR selected_at <= ?
           )
           AND {hold}
        """,
        (attempt_id, turn_id, stamp, stamp, item_id, cap, quiet_before),
    )
    if cur.rowcount != 1:
        _rollback(conn)
        return _no("illegal_transition")
    conn.execute("COMMIT")
    return _ok()


def release_surface_attempt(conn: sqlite3.Connection, attempt_id: str) -> Dict[str, Any]:
    return _call(_release_surface_attempt, conn, attempt_id)


def _release_surface_attempt(conn: sqlite3.Connection, attempt_id: str) -> Dict[str, Any]:
    conn.execute("BEGIN IMMEDIATE")
    conn.execute(
        """
        UPDATE items
           SET attempt_id = NULL, attempt_turn_id = NULL, attempt_at = NULL
         WHERE attempt_id = ?
        """,
        (attempt_id,),
    )
    conn.execute(
        """
        UPDATE loops
           SET lapse_attempt_id = NULL, lapse_attempt_turn_id = NULL
         WHERE lapse_attempt_id = ? AND lapse_told = 0
        """,
        (attempt_id,),
    )
    conn.execute("COMMIT")
    return _ok()


def note_lapse_attempt(
    conn: sqlite3.Connection,
    loop_id: str,
    attempt_id: str,
    turn_id: str,
) -> Dict[str, Any]:
    return _call(_note_lapse_attempt, conn, loop_id, attempt_id, turn_id)


def _note_lapse_attempt(
    conn: sqlite3.Connection, loop_id: str, attempt_id: str, turn_id: str
) -> Dict[str, Any]:
    conn.execute("BEGIN IMMEDIATE")
    cur = conn.execute(
        """
        UPDATE loops
           SET lapse_attempt_id = ?, lapse_attempt_turn_id = ?
         WHERE id = ? AND status = 'expired' AND lapse_told = 0
        """,
        (attempt_id, turn_id, loop_id),
    )
    if cur.rowcount != 1:
        _rollback(conn)
        return _no("illegal_transition")
    conn.execute("COMMIT")
    return _ok()


def confirm_surface_attempt(
    conn: sqlite3.Connection,
    attempt_id: str,
    turn_id: str,
    *,
    now: Optional[datetime] = None,
    ttl_seconds: int,
    reinject_cap: int,
) -> Dict[str, Any]:
    # P9-SURFACE: confirmation is the same turn and the same attempt — P9-D10
    return _call(
        _confirm_surface_attempt,
        conn,
        attempt_id,
        turn_id,
        now=now,
        ttl_seconds=ttl_seconds,
        reinject_cap=reinject_cap,
    )


def _confirm_surface_attempt(conn: sqlite3.Connection, attempt_id: str, turn_id: str, **kwargs: Any) -> Dict[str, Any]:
    clock = _now(kwargs.get("now"))
    stamp = _iso(clock)
    earliest = _iso(clock - timedelta(seconds=int(kwargs["ttl_seconds"])))
    cap = int(kwargs["reinject_cap"])
    conn.execute("BEGIN IMMEDIATE")
    cur = conn.execute(
        """
        UPDATE items
           SET conversation = 'selected',
               inject_count = inject_count + 1,
               selected_at = ?,
               updated_at = ?,
               attempt_id = NULL,
               attempt_turn_id = NULL,
               attempt_at = NULL
         WHERE attempt_id = ?
           AND attempt_turn_id = ?
           AND attempt_at >= ?
           AND closed_at IS NULL
           AND content_state = 'available'
           AND acknowledged_at IS NULL
           AND inject_count < ?
           AND (
             (processing = 'ranked' AND eligibility = 'eligible')
             OR (loop_matched = 1 AND eligibility NOT IN ('suppressed', 'expired'))
           )
        """,
        (stamp, stamp, attempt_id, turn_id, earliest, cap),
    )
    confirmed = cur.rowcount
    lapses = conn.execute(
        """
        UPDATE loops
           SET lapse_told = 1
         WHERE lapse_attempt_id = ?
           AND lapse_attempt_turn_id = ?
           AND lapse_told = 0
        """,
        (attempt_id, turn_id),
    )
    if confirmed < 1 and lapses.rowcount < 1:
        _rollback(conn)
        return _no("attempt_mismatch")
    conn.execute("COMMIT")
    return _ok(confirmed=confirmed, lapses=lapses.rowcount)


def dismiss_item(
    conn: sqlite3.Connection,
    item_id: str,
    *,
    now: Optional[datetime] = None,
    turn_id: Optional[str] = None,
) -> Dict[str, Any]:
    # P9-SURFACE: dismiss is a ticketed close, distinct from age_out — P9-D10
    return _call(_dismiss_item, conn, item_id, now=now, turn_id=turn_id)


def _dismiss_item(conn: sqlite3.Connection, item_id: str, **kwargs: Any) -> Dict[str, Any]:
    if not _ticket_ok(kwargs.get("turn_id")):
        return _no("origin")
    stamp = _iso(_now(kwargs.get("now")))
    conn.execute("BEGIN IMMEDIATE")
    cur = conn.execute(
        """
        UPDATE items
           SET closed_at = ?, updated_at = ?, closed_reason = 'dismissed',
               subject = NULL, snippet = NULL, gist = NULL, sender_display_name = NULL
         WHERE id = ?
           AND closed_at IS NULL
           AND delivery NOT IN ('claimed', 'speech_started')
           AND content_state = 'available'
        """,
        (stamp, stamp, item_id),
    )
    if cur.rowcount != 1:
        _rollback(conn)
        return _no("illegal_transition")
    _clear_phone_content_locked(conn, item_id)
    conn.execute("COMMIT")
    return _ok()


def open_loop_source_ids(conn: sqlite3.Connection) -> Dict[str, Any]:
    try:
        found: Set[str] = set()
        for loop in conn.execute("SELECT source_ids_json FROM loops WHERE status = 'open'"):
            try:
                values = json.loads(loop["source_ids_json"] or "[]")
            except json.JSONDecodeError:
                values = []
            for value in values:
                if value:
                    found.add(str(value))
        return _ok(ids=sorted(found))
    except sqlite3.OperationalError as exc:
        text = str(exc).lower()
        return _no("locked" if "locked" in text or "busy" in text else "error")
    except Exception:
        return _no("error")


def read_watcher_health(conn: sqlite3.Connection) -> Dict[str, Any]:
    # P9-SURFACE: the token store is not the watcher — P9-D12
    try:
        row = conn.execute("SELECT * FROM watcher_health WHERE id = 1").fetchone()
        if row is None:
            return _ok(row=None)
        return _ok(row=dict(row))
    except sqlite3.OperationalError as exc:
        text = str(exc).lower()
        return _no("locked" if "locked" in text or "busy" in text else "error")
    except Exception:
        return _no("error")


def post_speech_candidate(
    conn: sqlite3.Connection,
    *,
    now: Optional[datetime] = None,
    window_seconds: int = POST_SPEECH_WINDOW_SECONDS,
) -> Dict[str, Any]:
    # P9-SPEAK: the first note after evidenced speech, bound to that attempt — P9-D07
    try:
        clock = _now(now)
        earliest = _iso(clock - timedelta(seconds=int(window_seconds)))
        noted = _meta_get(conn, META_SPEECH_POST_NOTED) or ""
        hold = _phone_hold_sql()
        row = conn.execute(
            f"""
            SELECT d.attempt_id AS speech_attempt_id, i.*
              FROM deliveries d
              JOIN items i ON i.id = d.item_id
             WHERE d.outcome = 'delivered'
               AND d.at >= ?
               AND i.closed_at IS NULL
               AND i.acknowledged_at IS NULL
               AND i.content_state = 'available'
               AND d.attempt_id != ?
               AND i.{hold}
             ORDER BY d.at DESC
             LIMIT 1
            """,
            (earliest, noted),
        ).fetchone()
        if row is None:
            return _ok(item=None, speech_attempt_id="")
        item = {key: row[key] for key in row.keys() if key != "speech_attempt_id"}
        return _ok(item=item, speech_attempt_id=row["speech_attempt_id"])
    except sqlite3.OperationalError as exc:
        text = str(exc).lower()
        return _no("locked" if "locked" in text or "busy" in text else "error")
    except Exception:
        return _no("error")


def note_post_speech(
    conn: sqlite3.Connection,
    attempt_id: str,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    # P9-SPEAK: one note per evidenced attempt — P9-D07
    return _call(_note_post_speech, conn, attempt_id, now=now)


def _note_post_speech(conn: sqlite3.Connection, attempt_id: str, **kwargs: Any) -> Dict[str, Any]:
    if not attempt_id:
        return _no("bad_args")
    conn.execute("BEGIN IMMEDIATE")
    current = _meta_get(conn, META_SPEECH_POST_NOTED) or ""
    if current == attempt_id:
        conn.execute("COMMIT")
        return _ok(already=True)
    _meta_set(conn, META_SPEECH_POST_NOTED, attempt_id)
    conn.execute("COMMIT")
    return _ok()
