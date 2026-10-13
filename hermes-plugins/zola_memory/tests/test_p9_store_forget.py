"""P9-STORE forget: exactly one synthetic entity, then an unmapped name."""

from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

_MEMORY = Path(__file__).resolve().parents[1]
_WORKSPACE = _MEMORY.parent / "zola_workspace"
# Discover already has the memory root on sys.path, so insert it at the front
# or `import log` binds the workspace logger.
for _entry in (str(_WORKSPACE), str(_MEMORY)):
    while _entry in sys.path:
        sys.path.remove(_entry)
sys.path.insert(0, str(_WORKSPACE))
sys.path.insert(0, str(_MEMORY))

import forget
import log as memlog
import proactive_store
import store

TOKEN = "P9STORE_SYNTHETIC"
ADDRESS = "p9store-synthetic@example.com"
KEPT_NAME = "KEPTPERSON"


def _counts(conn: sqlite3.Connection, tables: tuple) -> dict:
    return {
        name: conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        for name in tables
    }


class _Provider:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._platform = "tui"
        self._parent_session_id = ""
        self._conn = conn
        self._forget_state = forget.ForgetSessionState()
        self._current_user_message = ""
        self._session_id = "s-p9"


class ForgetProactiveTests(unittest.TestCase):
    def setUp(self) -> None:
        self._dir = tempfile.TemporaryDirectory(prefix="p9forget_")
        self.home = Path(self._dir.name)
        self._old_home = os.environ.get("HERMES_HOME")
        os.environ["HERMES_HOME"] = str(self.home)
        memlog.reset_log_handler_for_tests()
        forget.set_client_origin_override_for_tests(True)
        proactive_store.set_ticket_override_for_tests(True)
        self.memory = store.open_store(self.home)
        self.proactive_path = self.home / "proactive" / "proactive.db"
        proactive_store.set_db_path_for_tests(self.proactive_path)
        self.proactive = proactive_store.connect(self.proactive_path, retry=False)
        self.provider = _Provider(self.memory)
        self._seed_kept()

    def tearDown(self) -> None:
        for conn in (getattr(self, "proactive", None), getattr(self, "memory", None)):
            try:
                if conn is not None:
                    conn.close()
            except Exception:
                pass
        forget.set_client_origin_override_for_tests(None)
        proactive_store.set_ticket_override_for_tests(None)
        proactive_store.set_db_path_for_tests(None)
        memlog.reset_log_handler_for_tests()
        if self._old_home is None:
            os.environ.pop("HERMES_HOME", None)
        else:
            os.environ["HERMES_HOME"] = self._old_home
        self._dir.cleanup()

    def _seed_kept(self) -> None:
        now = "2026-01-01T00:00:00Z"
        self.memory.execute(
            "INSERT INTO entities (id, name, kind, created_at) VALUES (?,?,?,?)",
            ("kept-entity", KEPT_NAME, "person", now),
        )
        self.memory.execute(
            "INSERT INTO entities_fts (entity_id, name) VALUES (?, ?)",
            ("kept-entity", KEPT_NAME),
        )
        self.memory.execute(
            "INSERT INTO entity_aliases (entity_id, alias) VALUES (?, ?)",
            ("kept-entity", "kept@example.com"),
        )
        self.memory.execute(
            "INSERT INTO episodes (id, summary, significance, event_time, "
            "event_time_basis, event_time_evidence, open_items_json, "
            "source_session_id, source_turn_start, source_turn_end, recorded_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "ep-kept",
                "A kept episode about the weather.",
                "synthetic",
                now,
                "stated",
                "",
                "[]",
                "s-p9",
                1,
                1,
                now,
            ),
        )
        self.memory.execute(
            "INSERT INTO episode_entities (episode_id, entity_id) VALUES (?, ?)",
            ("ep-kept", "kept-entity"),
        )
        self.memory.commit()
        kept = proactive_store.insert_item(
            self.proactive,
            source="gmail",
            message_id="kept-msg",
            sender_address="kept@example.com",
            subject="weather note",
            now=__import__("datetime").datetime(2026, 1, 1, tzinfo=__import__("datetime").timezone.utc),
        )
        self.assertTrue(kept["ok"], kept)
        resolved = proactive_store.set_sender_resolution(
            self.proactive, kept["id"], entity_id="kept-entity"
        )
        self.assertTrue(resolved["ok"], resolved)
        self.kept_item = kept["id"]

    def _memory_counts(self) -> dict:
        return _counts(
            self.memory,
            (
                "entities",
                "entity_aliases",
                "entities_fts",
                "episodes",
                "episode_entities",
                "tombstones",
                "facts",
            ),
        )

    def _proactive_counts(self) -> dict:
        return _counts(
            self.proactive,
            ("items", "loops", "item_attempts", "deliveries"),
        )

    def _forget(self, description: str, *, confirm: bool, target_ids=None) -> dict:
        self.provider._current_user_message = description
        args = {"description": description, "confirm": confirm}
        if target_ids is not None:
            args["target_ids"] = target_ids
        return json.loads(forget.handle_forget_memory(self.provider, args))

    def test_zero_hit_then_exactly_one_entity_counts(self) -> None:
        before_memory = self._memory_counts()
        before_proactive = self._proactive_counts()
        unmapped = self._forget(
            "Forget everything about NOMATCHTOKEN",
            confirm=False,
        )
        self.assertTrue(unmapped["ok"], unmapped)
        self.assertIn(forget.MSG_PROACTIVE_UNMAPPED, unmapped["message"])
        self.assertEqual(self._memory_counts(), before_memory)
        self.assertEqual(self._proactive_counts(), before_proactive)
        self.assertIsNotNone(
            self.proactive.execute("SELECT id FROM items WHERE id = ?", (self.kept_item,)).fetchone()
        )

        now = "2026-01-02T00:00:00Z"
        self.memory.execute(
            "INSERT INTO entities (id, name, kind, created_at) VALUES (?,?,?,?)",
            ("syn-entity", TOKEN, "person", now),
        )
        self.memory.execute(
            "INSERT INTO entities_fts (entity_id, name) VALUES (?, ?)",
            ("syn-entity", TOKEN),
        )
        self.memory.execute(
            "INSERT INTO entity_aliases (entity_id, alias) VALUES (?, ?)",
            ("syn-entity", ADDRESS),
        )
        self.memory.commit()
        seeded = proactive_store.insert_item(
            self.proactive,
            source="gmail",
            message_id="syn-msg",
            sender_address=ADDRESS,
            subject="package notice",
        )
        self.assertTrue(seeded["ok"], seeded)
        resolved = proactive_store.set_sender_resolution(
            self.proactive, seeded["id"], entity_id="syn-entity"
        )
        self.assertTrue(resolved["ok"], resolved)

        after_seed_memory = self._memory_counts()
        after_seed_proactive = self._proactive_counts()
        self.assertEqual(after_seed_memory["entities"], before_memory["entities"] + 1)
        self.assertEqual(after_seed_memory["entity_aliases"], before_memory["entity_aliases"] + 1)
        self.assertEqual(after_seed_memory["entities_fts"], before_memory["entities_fts"] + 1)
        self.assertEqual(after_seed_proactive["items"], before_proactive["items"] + 1)
        for key, value in before_memory.items():
            if key not in ("entities", "entity_aliases", "entities_fts"):
                self.assertEqual(after_seed_memory[key], value, key)
        for key, value in before_proactive.items():
            if key != "items":
                self.assertEqual(after_seed_proactive[key], value, key)

        phrase = f"Forget everything about {TOKEN}"
        listed = self._forget(phrase, confirm=False)
        self.assertTrue(listed["ok"], listed)
        ids = [
            candidate["id"]
            for group in listed["groups"]
            for candidate in group["candidates"]
            if candidate["kind"] == "entity"
        ]
        self.assertEqual(ids, ["syn-entity"])
        erased = self._forget(phrase, confirm=True, target_ids=["syn-entity"])
        self.assertTrue(erased["ok"], erased)
        self.assertIn("pending list was included", erased["message"])

        self.assertEqual(self._memory_counts(), before_memory)
        self.assertEqual(self._proactive_counts(), before_proactive)
        self.assertIsNone(
            self.memory.execute("SELECT id FROM entities WHERE id = ?", ("syn-entity",)).fetchone()
        )
        self.assertIsNone(
            self.proactive.execute("SELECT id FROM items WHERE id = ?", (seeded["id"],)).fetchone()
        )
        self.assertIsNotNone(
            self.memory.execute("SELECT id FROM entities WHERE id = ?", ("kept-entity",)).fetchone()
        )
        self.assertIsNotNone(
            self.proactive.execute("SELECT id FROM items WHERE id = ?", (self.kept_item,)).fetchone()
        )
        pending = store.meta_get(self.memory, forget.META_PENDING_PROACTIVE)
        self.assertIsNone(store.meta_get(self.memory, forget.META_PENDING_PROACTIVE))

    def test_unmapped_subject_leaves_open_loop(self) -> None:
        before_memory = self._memory_counts()
        before_loops = self.proactive.execute("SELECT COUNT(*) FROM loops").fetchone()[0]
        created = proactive_store.insert_loop(
            self.proactive,
            intent="reply",
            predicate={"op": "brian_confirms"},
            session_id="s-p9",
            sender_display_name="Synthetic Sender",
            subject="quartz lantern",
            source_ids=["src-lantern"],
            address_hashes=["hash-lantern"],
            now=datetime(2026, 1, 3, tzinfo=timezone.utc),
        )
        self.assertTrue(created["ok"], created)
        listed = self._forget("Forget the quartz lantern", confirm=False)
        self.assertTrue(listed["ok"], listed)
        self.assertEqual(listed["groups"], [])
        self.assertIn(forget.MSG_PROACTIVE_UNMAPPED, listed["message"])
        self.assertNotIn("Ask Brian which one", listed["message"])
        row = self.proactive.execute(
            "SELECT status, sender_display_name, subject FROM loops WHERE id = ?",
            (created["id"],),
        ).fetchone()
        self.assertEqual(row["status"], "open")
        self.assertEqual(row["sender_display_name"], "Synthetic Sender")
        self.assertEqual(row["subject"], "quartz lantern")
        self.assertEqual(
            self.proactive.execute("SELECT COUNT(*) FROM loops").fetchone()[0],
            before_loops + 1,
        )
        self.assertEqual(self._memory_counts(), before_memory)

    def test_partial_reply_when_proactive_is_locked(self) -> None:
        now = "2026-01-02T00:00:00Z"
        self.memory.execute(
            "INSERT INTO entities (id, name, kind, created_at) VALUES (?,?,?,?)",
            ("syn-entity", TOKEN, "person", now),
        )
        self.memory.execute(
            "INSERT INTO entity_aliases (entity_id, alias) VALUES (?, ?)",
            ("syn-entity", ADDRESS),
        )
        self.memory.commit()
        seeded = proactive_store.insert_item(
            self.proactive,
            source="gmail",
            message_id="syn-msg",
            sender_address=ADDRESS,
            subject="package notice",
        )
        proactive_store.set_sender_resolution(
            self.proactive, seeded["id"], entity_id="syn-entity"
        )
        phrase = f"Forget everything about {TOKEN}"
        listed = self._forget(phrase, confirm=False)
        self.assertTrue(any(
            candidate["id"] == "syn-entity"
            for group in listed["groups"]
            for candidate in group["candidates"]
        ))

        def locked_connect(*_args, **_kwargs):
            raise sqlite3.OperationalError("database is locked")

        original = proactive_store.connect
        proactive_store.connect = locked_connect
        try:
            erased = self._forget(phrase, confirm=True, target_ids=["syn-entity"])
        finally:
            proactive_store.connect = original
        self.assertFalse(erased["ok"])
        self.assertEqual(erased["message"], forget.MSG_PROACTIVE_PARTIAL)
        self.assertIsNone(
            self.memory.execute("SELECT id FROM entities WHERE id = ?", ("syn-entity",)).fetchone()
        )
        self.assertIsNotNone(
            self.proactive.execute("SELECT id FROM items WHERE id = ?", (seeded["id"],)).fetchone()
        )
        self.assertTrue(store.meta_get(self.memory, forget.META_PENDING_PROACTIVE))
        retried = proactive_store.retry_pending_forget(self.memory, self.proactive)
        self.assertTrue(retried["ok"], retried)
        self.assertIsNone(
            self.proactive.execute("SELECT id FROM items WHERE id = ?", (seeded["id"],)).fetchone()
        )
        self.assertIsNone(store.meta_get(self.memory, forget.META_PENDING_PROACTIVE))
        self.assertTrue(proactive_store.retry_pending_forget(self.memory, self.proactive)["ok"])

    def test_locked_proactive_leaves_pending_then_retry(self) -> None:
        now = "2026-01-02T00:00:00Z"
        self.memory.execute(
            "INSERT INTO entities (id, name, kind, created_at) VALUES (?,?,?,?)",
            ("syn-entity", TOKEN, "person", now),
        )
        self.memory.execute(
            "INSERT INTO entity_aliases (entity_id, alias) VALUES (?, ?)",
            ("syn-entity", ADDRESS),
        )
        self.memory.commit()
        seeded = proactive_store.insert_item(
            self.proactive,
            source="gmail",
            message_id="syn-msg",
            sender_address=ADDRESS,
            subject="package notice",
        )
        proactive_store.set_sender_resolution(
            self.proactive, seeded["id"], entity_id="syn-entity"
        )
        phrase = f"Forget everything about {TOKEN}"
        listed = self._forget(phrase, confirm=False)
        entity_ids = [
            candidate["id"]
            for group in listed["groups"]
            for candidate in group["candidates"]
            if candidate["id"] == "syn-entity"
        ]
        self.assertEqual(entity_ids, ["syn-entity"])

        other = proactive_store.connect(self.proactive_path, timeout_ms=200, retry=False)
        holder = sqlite3.connect(str(self.proactive_path), timeout=0.2)
        try:
            holder.execute("BEGIN IMMEDIATE")
            payload = {
                "entity_id": "syn-entity",
                "address_hashes": [proactive_store.address_hash(ADDRESS)],
                "source_ids": ["syn-msg"],
            }
            self.memory.execute("BEGIN IMMEDIATE")
            self.memory.execute("DELETE FROM entity_aliases WHERE entity_id = ?", ("syn-entity",))
            self.memory.execute("DELETE FROM entities WHERE id = ?", ("syn-entity",))
            store.meta_set(
                self.memory,
                forget.META_PENDING_PROACTIVE,
                json.dumps(payload),
            )
            self.memory.execute("COMMIT")
            locked = proactive_store.forget_subject(
                other,
                entity_id="syn-entity",
                address_hashes=payload["address_hashes"],
                source_ids=payload["source_ids"],
            )
        finally:
            holder.rollback()
            holder.close()
            other.close()
        self.assertEqual(locked["refused_reason"], "locked")
        self.assertIsNotNone(
            self.proactive.execute("SELECT id FROM items WHERE id = ?", (seeded["id"],)).fetchone()
        )
        self.assertTrue(store.meta_get(self.memory, forget.META_PENDING_PROACTIVE))
        retried = proactive_store.retry_pending_forget(self.memory, self.proactive)
        self.assertTrue(retried["ok"], retried)
        self.assertIsNone(
            self.proactive.execute("SELECT id FROM items WHERE id = ?", (seeded["id"],)).fetchone()
        )
        self.assertIsNone(store.meta_get(self.memory, forget.META_PENDING_PROACTIVE))
        again = proactive_store.retry_pending_forget(self.memory, self.proactive)
        self.assertTrue(again["ok"], again)

    def test_connect_finishes_pending_after_crash(self) -> None:
        seeded = proactive_store.insert_item(
            self.proactive,
            source="gmail",
            message_id="syn-msg",
            sender_address=ADDRESS,
            subject="package notice",
        )
        proactive_store.set_sender_resolution(
            self.proactive, seeded["id"], entity_id="syn-entity"
        )
        payload = {
            "entity_id": "syn-entity",
            "address_hashes": [proactive_store.address_hash(ADDRESS)],
            "source_ids": ["syn-msg"],
        }
        self.memory.execute("BEGIN IMMEDIATE")
        store.meta_set(self.memory, forget.META_PENDING_PROACTIVE, json.dumps(payload))
        self.memory.execute("COMMIT")
        self.proactive.close()
        self.memory.close()
        reopened = proactive_store.connect(self.proactive_path, retry=True)
        try:
            self.assertIsNone(
                reopened.execute("SELECT id FROM items WHERE id = ?", (seeded["id"],)).fetchone()
            )
        finally:
            reopened.close()
        memory = sqlite3.connect(str(store.db_path(self.home)))
        try:
            row = memory.execute(
                "SELECT value FROM meta WHERE key = ?",
                (forget.META_PENDING_PROACTIVE,),
            ).fetchone()
            self.assertIsNone(row)
        finally:
            memory.close()
            self.memory = store.open_store(self.home)
            self.proactive = proactive_store.connect(self.proactive_path, retry=False)
