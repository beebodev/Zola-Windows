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


def _must(payload):
    return [item["id"] for item in payload.get("must_tell") or []]


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
        import contact_index

        contact_index.reset_for_tests()
        contact_index.set_people_for_tests([])
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
        import contact_index

        contact_index.reset_for_tests()
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
        self.assertIn("the email I was holding", erased["message"])
        self.assertEqual(_must(erased), ["notifications_display_name"])
        self.assertNotIn("Notifications are matched", erased["message"])
        self.assertNotIn("conversation logs", erased["message"])

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
        self.assertEqual(erased["refused_reason"], "locked")
        self.assertEqual(erased["message"], forget.MSG_NOTHING_CHANGED)
        self.assertIsNotNone(
            self.memory.execute("SELECT id FROM entities WHERE id = ?", ("syn-entity",)).fetchone()
        )
        self.assertIsNotNone(
            self.proactive.execute("SELECT id FROM items WHERE id = ?", (seeded["id"],)).fetchone()
        )
        self.assertIsNone(store.meta_get(self.memory, forget.META_PENDING_PROACTIVE))

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

    def test_handler_forgets_a_contact_and_leaves_a_short_notification_name(self) -> None:
        import contact_index
        import phone_ids

        contact_index.reset_for_tests()
        contact_index.set_people_for_tests(
            [
                contact_index.Person(
                    handle="c_beebo",
                    display_name="Beebo Dev",
                    numbers=("+15555550100",),
                    number_hashes=frozenset({phone_ids.hash("+15555550100")}),
                    emails=("beebo@example.com",),
                    email_hashes=frozenset(),
                )
            ]
        )
        try:
            when = datetime.now(timezone.utc).replace(microsecond=0)
            text = proactive_store.ingest_phone_item(
                self.proactive,
                kind="sms",
                device_id="device-test",
                revision=1,
                completeness="complete",
                received_at=when,
                provider_id="m-forget",
                sender_raw="+15555550100",
                body="synthetic",
                is_group=0,
                now=when,
            )
            self.assertEqual(text.get("result"), "stored", text)
            full = proactive_store.ingest_phone_item(
                self.proactive,
                kind="notif",
                device_id="device-test",
                revision=1,
                completeness="complete",
                received_at=when,
                package="com.instagram.android",
                notification_key="full-name",
                newest_message_timestamp="1000",
                sender_display_name="Beebo Dev",
                body="synthetic",
                is_group=0,
                now=when,
            )
            short = proactive_store.ingest_phone_item(
                self.proactive,
                kind="notif",
                device_id="device-test",
                revision=1,
                completeness="complete",
                received_at=when,
                package="com.instagram.android",
                notification_key="short-name",
                newest_message_timestamp="1001",
                sender_display_name="Beebo",
                body="synthetic",
                is_group=0,
                now=when,
            )
            self.assertEqual(full.get("result"), "stored", full)
            self.assertEqual(short.get("result"), "stored", short)
            digest = phone_ids.hash("+15555550100")
            watch = proactive_store.insert_loop(
                self.proactive,
                intent="person",
                predicate={"op": "sender_any", "value": [digest]},
                session_id="s-p9",
                sender_display_name="Beebo Dev",
                address_hashes=[digest],
                name_source="contacts_index",
            )
            self.assertTrue(watch["ok"], watch)
            listed = self._forget("Forget Beebo Dev", confirm=False)
            self.assertTrue(listed["ok"], listed)
            ids = [
                candidate["id"]
                for group in listed["groups"]
                for candidate in group["candidates"]
                if candidate["kind"] == "person"
            ]
            self.assertEqual(len(ids), 1, listed)
            erased = self._forget("Forget Beebo Dev", confirm=True, target_ids=ids)
            self.assertTrue(erased["ok"], erased)
            self.assertIn("the texts I was holding", erased["message"])
            self.assertIn("the watches I was holding", erased["message"])
            self.assertEqual(
                _must(erased),
                ["notifications_display_name", "texts_on_phone"],
            )
            self.assertNotIn("Notifications are matched", erased["message"])
            self.assertNotIn("still on your phone", erased["message"])
            self.assertNotIn("conversation logs", erased["message"])
            self.assertIsNone(
                self.proactive.execute("SELECT id FROM items WHERE id = ?", (text["id"],)).fetchone()
            )
            self.assertIsNone(
                self.proactive.execute("SELECT id FROM items WHERE id = ?", (full["id"],)).fetchone()
            )
            self.assertIsNotNone(
                self.proactive.execute("SELECT id FROM items WHERE id = ?", (short["id"],)).fetchone()
            )
            closed = self.proactive.execute(
                "SELECT status, closed_intent FROM loops WHERE id = ?",
                (watch["id"],),
            ).fetchone()
            self.assertEqual(closed["status"], "closed")
            self.assertEqual(closed["closed_intent"], "forgotten")
        finally:
            contact_index.reset_for_tests()

    def _install_contact(self, *, numbers=("+15555550100",), emails=("beebo@example.com",), name="Beebo Dev", handle="c_beebo"):
        import address_hash
        import contact_index
        import phone_ids

        contact_index.reset_for_tests()
        contact_index.set_people_for_tests(
            [
                contact_index.Person(
                    handle=handle,
                    display_name=name,
                    numbers=tuple(numbers),
                    number_hashes=frozenset(phone_ids.hash(number) for number in numbers),
                    emails=tuple(emails),
                    email_hashes=frozenset(address_hash.address_hash(email) for email in emails),
                )
            ]
        )

    def _sms(self, provider, sender):
        when = datetime.now(timezone.utc).replace(microsecond=0)
        return proactive_store.ingest_phone_item(
            self.proactive,
            kind="sms",
            device_id="device-test",
            revision=1,
            completeness="complete",
            received_at=when,
            provider_id=provider,
            sender_raw=sender,
            body="synthetic",
            is_group=0,
            now=when,
        )

    def _confirm_contact(self, description):
        listed = self._forget(description, confirm=False)
        self.assertTrue(listed["ok"], listed)
        ids = [
            candidate["id"]
            for group in listed["groups"]
            for candidate in group["candidates"]
            if candidate["kind"] == "person"
        ]
        self.assertEqual(len(ids), 1, listed)
        erased = self._forget(description, confirm=True, target_ids=ids)
        self.assertTrue(erased["ok"], erased)
        return erased

    def test_forget_reply_texts_only(self) -> None:
        import contact_index

        self._install_contact()
        try:
            text = self._sms("texts-only", "+15555550100")
            self.assertEqual(text.get("result"), "stored", text)
            erased = self._confirm_contact("Forget Beebo Dev")
            self.assertIn("including the texts I was holding", erased["message"])
            self.assertNotIn("email", erased["message"])
            self.assertNotIn("watches", erased["message"])
            self.assertEqual(_must(erased), ["notifications_display_name", "texts_on_phone"])
            self.assertNotIn("Notifications are matched", erased["message"])
            self.assertNotIn("still on your phone", erased["message"])
            self.assertIsNone(self.proactive.execute("SELECT id FROM items WHERE id = ?", (text["id"],)).fetchone())
        finally:
            contact_index.reset_for_tests()

    def test_forget_reply_texts_and_email(self) -> None:
        import contact_index

        self._install_contact()
        try:
            self._sms("texts-mail", "+15555550100")
            mail = proactive_store.insert_item(
                self.proactive,
                source="gmail",
                message_id="beebo-mail",
                sender_address="beebo@example.com",
                subject="synth",
                now=datetime.now(timezone.utc),
            )
            self.assertTrue(mail["ok"], mail)
            erased = self._confirm_contact("Forget Beebo Dev")
            self.assertIn("the texts I was holding", erased["message"])
            self.assertIn("the email I was holding", erased["message"])
            self.assertNotIn("watches", erased["message"])
            self.assertIsNone(self.proactive.execute("SELECT id FROM items WHERE id = ?", (mail["id"],)).fetchone())
        finally:
            contact_index.reset_for_tests()

    def test_forget_person_texts_emails_notifications_watches(self) -> None:
        import contact_index
        import phone_ids

        self._install_contact()
        try:
            when = datetime.now(timezone.utc).replace(microsecond=0)
            self._sms("all-text", "+15555550100")
            mail = proactive_store.insert_item(
                self.proactive, source="gmail", message_id="all-mail",
                sender_address="beebo@example.com", subject="synth", now=when,
            )
            note = proactive_store.ingest_phone_item(
                self.proactive, kind="notif", device_id="device-test", revision=1,
                completeness="complete", received_at=when, package="com.instagram.android",
                notification_key="all-name", newest_message_timestamp="1000",
                sender_display_name="Beebo Dev", body="synthetic", is_group=0, now=when,
            )
            digest = phone_ids.hash("+15555550100")
            watch = proactive_store.insert_loop(
                self.proactive, intent="person", predicate={"op": "sender_any", "address_hashes": [digest]},
                session_id="s-p9", sender_display_name="Beebo Dev", address_hashes=[digest],
                name_source="contacts_index",
            )
            self.assertTrue(mail["ok"] and note.get("result") == "stored" and watch["ok"])
            erased = self._confirm_contact("Forget Beebo Dev")
            self.assertIn("the texts I was holding", erased["message"])
            self.assertIn("the email I was holding", erased["message"])
            self.assertIn("the watches I was holding", erased["message"])
            self.assertEqual(_must(erased), ["notifications_display_name", "texts_on_phone"])
            self.assertNotIn("Notifications are matched", erased["message"])
            self.assertEqual(self.proactive.execute("SELECT COUNT(*) FROM items").fetchone()[0], 1)
        finally:
            contact_index.reset_for_tests()

    def test_forget_reply_nothing_held(self) -> None:
        import contact_index

        self._install_contact()
        try:
            erased = self._confirm_contact("Forget Beebo Dev")
            self.assertIn("I wasn't holding anything for Beebo Dev.", erased["message"])
            self.assertEqual(_must(erased), ["notifications_display_name", "texts_on_phone"])
            self.assertNotIn("Notifications are matched", erased["message"])
            self.assertNotIn("still on your phone", erased["message"])
            self.assertNotIn("I've forgotten", erased["message"])
        finally:
            contact_index.reset_for_tests()

    def test_forget_reply_nothing_held_without_number(self) -> None:
        import contact_index

        self._install_contact(numbers=(), emails=("beebo@example.com",))
        try:
            erased = self._confirm_contact("Forget Beebo Dev")
            self.assertIn("I wasn't holding anything for Beebo Dev.", erased["message"])
            self.assertEqual(_must(erased), ["notifications_display_name"])
            self.assertNotIn("Notifications are matched", erased["message"])
            self.assertNotIn("still on your phone", erased["message"])
        finally:
            contact_index.reset_for_tests()

    def test_forget_reply_not_in_contacts(self) -> None:
        import contact_index

        contact_index.reset_for_tests()
        contact_index.set_people_for_tests([])
        try:
            listed = self._forget("Forget Beebo Dev", confirm=False)
            self.assertIn("I couldn't find Beebo Dev in your contacts", listed["message"])
            self.assertNotIn("Notifications are matched", listed["message"])
            self.assertNotIn("must_tell", listed)
            self.assertNotIn("I've forgotten", listed["message"])
        finally:
            contact_index.reset_for_tests()

    def test_partial_reply_index_down(self) -> None:
        import contact_index
        import phone_ids

        contact_index.reset_for_tests()
        contact_index.set_unavailable_for_tests(True)
        try:
            digest = phone_ids.hash("+15555550100")
            text = self._sms("down-text", "+15555550100")
            watch = proactive_store.insert_loop(
                self.proactive, intent="person", predicate={"op": "sender_any", "address_hashes": [digest]},
                session_id="s-p9", sender_display_name="Beebo Dev", address_hashes=[digest],
                name_source="contacts_index",
            )
            self.assertTrue(watch["ok"], watch)
            erased = self._confirm_contact("Forget Beebo Dev")
            self.assertIn("I forgot what I could for Beebo Dev.", erased["message"])
            self.assertIn("Contacts couldn't be checked", erased["message"])
            self.assertNotIn("I've forgotten", erased["message"])
            self.assertIsNone(self.proactive.execute("SELECT id FROM items WHERE id = ?", (text["id"],)).fetchone())
            closed = self.proactive.execute("SELECT status FROM loops WHERE id = ?", (watch["id"],)).fetchone()
            self.assertEqual(closed["status"], "closed")
        finally:
            contact_index.set_unavailable_for_tests(None)
            contact_index.reset_for_tests()

    def test_forget_number_only(self) -> None:
        import contact_index

        self._install_contact(numbers=("+15555550100", "+15555550199"))
        try:
            mine = self._sms("num-mine", "+15555550100")
            other = self._sms("num-other", "+15555550199")
            mail = proactive_store.insert_item(
                self.proactive, source="gmail", message_id="num-mail",
                sender_address="beebo@example.com", subject="synth", now=datetime.now(timezone.utc),
            )
            listed = self._forget("Forget 15555550100", confirm=False)
            ids = [
                candidate["id"]
                for group in listed["groups"]
                for candidate in group["candidates"]
                if candidate["kind"] == "number"
            ]
            self.assertEqual(len(ids), 1, listed)
            erased = self._forget("Forget 15555550100", confirm=True, target_ids=ids)
            self.assertIn("I've forgotten the texts from that number.", erased["message"])
            self.assertIn("Want me to forget Beebo Dev entirely?", erased["message"])
            self.assertNotIn("including", erased["message"])
            self.assertIsNone(self.proactive.execute("SELECT id FROM items WHERE id = ?", (mine["id"],)).fetchone())
            self.assertIsNotNone(self.proactive.execute("SELECT id FROM items WHERE id = ?", (other["id"],)).fetchone())
            self.assertIsNotNone(self.proactive.execute("SELECT id FROM items WHERE id = ?", (mail["id"],)).fetchone())
        finally:
            contact_index.reset_for_tests()

    def test_forget_contact_number_asks(self) -> None:
        import contact_index

        self._install_contact(numbers=("+15555550100", "+15555550199"))
        try:
            self._sms("ask-mine", "+15555550100")
            other = self._sms("ask-other", "+15555550199")
            mail = proactive_store.insert_item(
                self.proactive, source="gmail", message_id="ask-mail",
                sender_address="beebo@example.com", subject="synth", now=datetime.now(timezone.utc),
            )
            listed = self._forget("Forget 15555550100", confirm=False)
            ids = [
                candidate["id"]
                for group in listed["groups"]
                for candidate in group["candidates"]
                if candidate["kind"] == "number"
            ]
            asked = self._forget("Forget 15555550100", confirm=True, target_ids=ids)
            self.assertIn("Want me to forget Beebo Dev entirely?", asked["message"])
            widened = self._forget("Yes", confirm=True)
            self.assertTrue(widened["ok"], widened)
            self.assertIn("I've forgotten Beebo Dev", widened["message"])
            self.assertIsNone(self.proactive.execute("SELECT id FROM items WHERE id = ?", (other["id"],)).fetchone())
            self.assertIsNone(self.proactive.execute("SELECT id FROM items WHERE id = ?", (mail["id"],)).fetchone())
        finally:
            contact_index.reset_for_tests()

    def test_grouped_number_forget_uses_the_watch_extractor(self) -> None:
        import inspect

        import contact_index
        import loops
        import phone_ids

        forms = ("555-555-0100", "5555550100", "+1 555 555 0100")
        found = [phone_ids.spoken_number(form) for form in forms]
        self.assertTrue(all(kind == phone_ids.KIND_E164 for kind, _canon in found), found)
        self.assertEqual(len({canon for _kind, canon in found}), 1)
        self.assertIn("spoken_number", inspect.getsource(loops._create_contact_watch))
        self.assertIn("spoken_number", inspect.getsource(proactive_store.number_forget_plan))
        self._install_contact()
        try:
            plans = [
                proactive_store.number_forget_plan("Forget the texts from " + form + ".")
                for form in forms
            ]
            self.assertEqual(len({plan.get("hash") for plan in plans}), 1, plans)
            self.assertTrue(plans[0].get("hash"))
            mine = self._sms("grouped-mine", "+15555550100")
            listed = self._forget("Forget the texts from 555-555-0100.", confirm=False)
            ids = [
                candidate["id"]
                for group in listed["groups"]
                for candidate in group["candidates"]
                if candidate["kind"] == "number"
            ]
            self.assertEqual(len(ids), 1, listed)
            self.assertNotEqual(listed.get("status"), "no_number")
            self.assertNotEqual(listed.get("status"), "nothing_held")
            erased = self._forget(
                "Forget the texts from 555-555-0100.", confirm=True, target_ids=ids
            )
            self.assertIn("I've forgotten the texts from that number.", erased["message"])
            self.assertIsNone(
                self.proactive.execute("SELECT id FROM items WHERE id = ?", (mine["id"],)).fetchone()
            )
        finally:
            contact_index.reset_for_tests()

    def test_no_number_is_not_nothing_left(self) -> None:
        listed = self._forget("Forget the texts from the number.", confirm=False)
        self.assertEqual(listed.get("status"), "no_number")
        self.assertIn("must not say that nothing is left", listed["message"].casefold())
        self.assertNotIn("i've forgotten", listed["message"].casefold())
        self.assertIn("no number", listed["message"].casefold())
        self.assertIn("must not say that nothing is left", forget.TOOL_DESCRIPTION)
        self.assertIn("no_number", forget.TOOL_DESCRIPTION)
        person = self._forget("Forget NOMATCHTOKEN", confirm=False)
        self.assertNotEqual(person.get("status"), "no_number")

    def test_number_found_with_nothing_held(self) -> None:
        import contact_index

        self._install_contact()
        try:
            listed = self._forget("Forget the texts from 555-555-0100.", confirm=False)
            self.assertEqual(listed.get("status"), "nothing_held")
            self.assertNotEqual(listed.get("status"), "no_number")
            self.assertIn("nothing is held", listed["message"].casefold())
            self.assertEqual(listed.get("groups"), [])
            self.assertEqual(self.proactive.execute("SELECT COUNT(*) FROM items").fetchone()[0], 1)
        finally:
            contact_index.reset_for_tests()

    def test_forget_reply_includes_memory_facts(self) -> None:
        now = "2026-01-03T00:00:00Z"
        self.memory.execute(
            "INSERT INTO entities (id, name, kind, created_at) VALUES (?,?,?,?)",
            ("beebo-entity", "Beebo Dev", "person", now),
        )
        self.memory.execute(
            "INSERT INTO entities_fts (entity_id, name) VALUES (?, ?)",
            ("beebo-entity", "Beebo Dev"),
        )
        self.memory.execute(
            "INSERT INTO episodes (id, summary, significance, event_time, "
            "event_time_basis, event_time_evidence, open_items_json, "
            "source_session_id, source_turn_start, source_turn_end, recorded_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "ep-beebo",
                "Beebo Dev asked about the gate.",
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
            ("ep-beebo", "beebo-entity"),
        )
        self.memory.execute(
            "INSERT INTO episodes (id, summary, significance, event_time, "
            "event_time_basis, event_time_evidence, open_items_json, "
            "source_session_id, source_turn_start, source_turn_end, recorded_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "ep-stay",
                "The weather stayed mild.",
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
            ("ep-stay", "beebo-entity"),
        )
        self.memory.commit()
        listed = self._forget("Forget Beebo Dev", confirm=False)
        ids = [
            candidate["id"]
            for group in listed["groups"]
            for candidate in group["candidates"]
            if candidate["id"] in ("beebo-entity", "ep-beebo")
        ]
        self.assertIn("beebo-entity", ids, listed)
        self.assertIn("ep-beebo", ids, listed)
        erased = self._forget("Forget Beebo Dev", confirm=True, target_ids=ids)
        self.assertTrue(erased["ok"], erased)
        self.assertIn("the episodes I was holding", erased["message"])
        self.assertIn("notifications_display_name", _must(erased))
        self.assertNotIn("Notifications are matched", erased["message"])
        self.assertNotIn("conversation logs", erased["message"])

    def test_entity_forget_includes_the_contact_number(self) -> None:
        import contact_index
        import phone_ids

        name = "SYNCONTACT"
        number = "+15555550199"
        email = "syncontact@example.com"
        now = "2026-01-04T00:00:00Z"
        self.memory.execute(
            "INSERT INTO entities (id, name, kind, created_at) VALUES (?,?,?,?)",
            ("syn-contact", name, "person", now),
        )
        self.memory.execute(
            "INSERT INTO entities_fts (entity_id, name) VALUES (?, ?)",
            ("syn-contact", name),
        )
        self.memory.execute(
            "INSERT INTO entity_aliases (entity_id, alias) VALUES (?, ?)",
            ("syn-contact", "other-alias@example.com"),
        )
        self.memory.commit()
        contact_index.set_people_for_tests([
            contact_index.Person(
                handle="c_syn",
                display_name=name,
                numbers=(number,),
                number_hashes=frozenset({phone_ids.hash(number)}),
                emails=(email,),
                email_hashes=frozenset({proactive_store.address_hash(email)}),
            )
        ])
        when = datetime(2026, 1, 4, tzinfo=timezone.utc)
        text = proactive_store.ingest_phone_item(
            self.proactive,
            kind="sms",
            device_id="device-test",
            revision=1,
            completeness="complete",
            received_at=when,
            provider_id="syn-sms",
            package="",
            notification_key="",
            newest_message_timestamp="",
            sender_raw=number,
            sender_display_name="",
            body="zz-code",
            is_group=0,
            now=when,
        )
        self.assertTrue(text.get("ok"), text)
        mail = proactive_store.insert_item(
            self.proactive,
            source="gmail",
            message_id="syn-mail",
            sender_address=email,
            subject="quartz",
            now=when,
        )
        self.assertTrue(mail["ok"], mail)
        phrase = "Forget SYNCONTACT"
        listed = self._forget(phrase, confirm=False)
        self.assertTrue(listed["ok"], listed)
        ids = [
            candidate["id"]
            for group in listed["groups"]
            for candidate in group["candidates"]
            if candidate["kind"] == "person"
        ]
        self.assertEqual(ids, ["person:c_syn"], listed)
        erased = self._forget(phrase, confirm=True, target_ids=ids)
        self.assertTrue(erased["ok"], erased)
        self.assertIn("the texts I was holding", erased["message"])
        self.assertEqual(_must(erased), ["notifications_display_name", "texts_on_phone"])
        self.assertNotIn("still on your phone", erased["message"])
        self.assertIsNone(
            self.proactive.execute("SELECT id FROM items WHERE id = ?", (text["id"],)).fetchone()
        )
        self.assertIsNone(
            self.proactive.execute("SELECT id FROM items WHERE id = ?", (mail["id"],)).fetchone()
        )
        self.assertGreater(
            self.proactive.execute("SELECT COUNT(*) FROM phone_tombstones").fetchone()[0],
            0,
        )

    def _seed_memory_and_contact(self):
        """One memory record, one contact, a text, an email, and two watches.

        The second watch is already closed as delivered, which is the live
        number-watch case: a later yes still has to mark it forgotten.
        """
        import contact_index
        import phone_ids

        name = "SYNYES"
        number = "+15555550177"
        email = "synyes@example.com"
        now = "2026-01-05T00:00:00Z"
        self.memory.execute(
            "INSERT INTO entities (id, name, kind, created_at) VALUES (?,?,?,?)",
            ("synyes-entity", name, "person", now),
        )
        self.memory.execute(
            "INSERT INTO entities_fts (entity_id, name) VALUES (?, ?)",
            ("synyes-entity", name),
        )
        self.memory.execute(
            "INSERT INTO episodes (id, summary, significance, event_time, "
            "event_time_basis, event_time_evidence, open_items_json, "
            "source_session_id, source_turn_start, source_turn_end, recorded_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "ep-synyes",
                "SYNYES asked for a ride.",
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
            ("ep-synyes", "synyes-entity"),
        )
        self.memory.commit()
        contact_index.set_people_for_tests([
            contact_index.Person(
                handle="c_synyes",
                display_name=name,
                numbers=(number,),
                number_hashes=frozenset({phone_ids.hash(number)}),
                emails=(email,),
                email_hashes=frozenset({proactive_store.address_hash(email)}),
            )
        ])
        when = datetime(2026, 1, 5, tzinfo=timezone.utc)
        text = proactive_store.ingest_phone_item(
            self.proactive,
            kind="sms",
            device_id="device-test",
            revision=1,
            completeness="complete",
            received_at=when,
            provider_id="synyes-sms",
            package="",
            notification_key="",
            newest_message_timestamp="",
            sender_raw=number,
            sender_display_name="",
            body="zz-code",
            is_group=0,
            now=when,
        )
        self.assertTrue(text.get("ok"), text)
        mail = proactive_store.insert_item(
            self.proactive,
            source="gmail",
            message_id="synyes-mail",
            sender_address=email,
            subject="quartz",
            now=when,
        )
        self.assertTrue(mail["ok"], mail)
        digest = phone_ids.hash(number)
        opened = proactive_store.insert_loop(
            self.proactive,
            intent="number",
            predicate={"op": "sender_any", "value": [digest]},
            session_id="s-p9",
            sender_display_name="a number",
            address_hashes=[digest],
            name_source="mail",
        )
        self.assertTrue(opened["ok"], opened)
        delivered = proactive_store.insert_loop(
            self.proactive,
            intent="number",
            predicate={"op": "sender_any", "value": [digest]},
            session_id="s-p9",
            sender_display_name="a number",
            address_hashes=[digest],
            name_source="mail",
        )
        self.assertTrue(delivered["ok"], delivered)
        self.proactive.execute(
            "UPDATE loops SET status = 'closed', closed_intent = 'delivered', "
            "sender_display_name = NULL WHERE id = ?",
            (delivered["id"],),
        )
        self.proactive.commit()
        return {
            "name": name,
            "digest": digest,
            "text_id": text["id"],
            "mail_id": mail["id"],
            "open_watch": opened["id"],
            "delivered_watch": delivered["id"],
        }

    def test_yes_forgets_memory_and_the_bound_contact(self) -> None:
        import contact_index

        seeded = self._seed_memory_and_contact()
        tombs_before = self.proactive.execute("SELECT COUNT(*) FROM phone_tombstones").fetchone()[0]
        listed = self._forget("Forget SYNYES", confirm=False)
        self.assertTrue(listed["ok"], listed)
        ids = [
            candidate["id"]
            for group in listed["groups"]
            for candidate in group["candidates"]
        ]
        self.assertEqual(ids, ["person:c_synyes"], listed)
        self.assertEqual(
            [candidate["kind"] for group in listed["groups"] for candidate in group["candidates"]],
            ["person"],
        )
        erased = self._forget("Yes", confirm=True, target_ids=ids)
        self.assertTrue(erased["ok"], erased)
        self.assertIn("the texts I was holding", erased["message"])
        self.assertIn("the email I was holding", erased["message"])
        self.assertIn("the watches I was holding", erased["message"])
        self.assertIn("the episodes I was holding", erased["message"])
        self.assertEqual(_must(erased), ["notifications_display_name", "texts_on_phone"])
        self.assertNotIn("still on your phone", erased["message"])
        self.assertNotIn("Notifications are matched", erased["message"])
        self.assertNotIn("conversation logs", erased["message"])
        self.assertIsNone(
            self.memory.execute("SELECT id FROM entities WHERE id = ?", ("synyes-entity",)).fetchone()
        )
        self.assertIsNone(
            self.memory.execute("SELECT id FROM episodes WHERE id = ?", ("ep-synyes",)).fetchone()
        )
        self.assertIsNone(
            self.proactive.execute("SELECT id FROM items WHERE id = ?", (seeded["text_id"],)).fetchone()
        )
        self.assertIsNone(
            self.proactive.execute("SELECT id FROM items WHERE id = ?", (seeded["mail_id"],)).fetchone()
        )
        hinted = self.proactive.execute(
            "SELECT COUNT(*) FROM items WHERE sender_address_hash = ? AND sender_hint IS NOT NULL",
            (seeded["digest"],),
        ).fetchone()[0]
        self.assertEqual(hinted, 0)
        self.assertGreater(
            self.proactive.execute("SELECT COUNT(*) FROM phone_tombstones").fetchone()[0],
            tombs_before,
        )
        for watch_id in (seeded["open_watch"], seeded["delivered_watch"]):
            closed = self.proactive.execute(
                "SELECT status, closed_intent, sender_display_name, address_hashes_json "
                "FROM loops WHERE id = ?",
                (watch_id,),
            ).fetchone()
            self.assertEqual(closed["status"], "closed", watch_id)
            self.assertEqual(closed["closed_intent"], "forgotten", watch_id)
            self.assertIsNone(closed["sender_display_name"])
            self.assertEqual(closed["address_hashes_json"], "[]")
        self.assertIsNotNone(
            self.proactive.execute("SELECT id FROM items WHERE id = ?", (self.kept_item,)).fetchone()
        )
        self.assertEqual(len(contact_index.get_index().people), 1)

    def test_yes_reports_a_partial_when_proactive_fails(self) -> None:
        seeded = self._seed_memory_and_contact()
        listed = self._forget("Forget SYNYES", confirm=False)
        self.assertTrue(listed["ok"], listed)
        proactive_store.set_ticket_override_for_tests(False)
        try:
            erased = self._forget("Yes", confirm=True, target_ids=["person:c_synyes"])
        finally:
            proactive_store.set_ticket_override_for_tests(True)
        self.assertFalse(erased["ok"], erased)
        self.assertEqual(erased["refused_reason"], "origin")
        self.assertEqual(erased["message"], forget.MSG_NOTHING_CHANGED)
        self.assertNotIn("conversation logs", erased["message"])
        self.assertIsNotNone(
            self.memory.execute("SELECT id FROM episodes WHERE id = ?", ("ep-synyes",)).fetchone()
        )
        self.assertIsNotNone(
            self.memory.execute("SELECT id FROM entities WHERE id = ?", ("synyes-entity",)).fetchone()
        )
        self.assertIsNotNone(
            self.proactive.execute("SELECT id FROM items WHERE id = ?", (seeded["text_id"],)).fetchone()
        )
        self.assertIsNotNone(
            self.proactive.execute("SELECT id FROM items WHERE id = ?", (seeded["mail_id"],)).fetchone()
        )
        still_open = self.proactive.execute(
            "SELECT status FROM loops WHERE id = ?",
            (seeded["open_watch"],),
        ).fetchone()
        self.assertEqual(still_open["status"], "open")

    def test_brian_turn_branches_log_a_reason(self) -> None:
        import turn_context

        turn_context.clear_all_for_tests()
        try:
            with self.assertLogs("zola_workspace", level="WARNING") as empty_logs:
                self.assertFalse(turn_context.is_brian_turn())
            self.assertIn("reason=empty_turn_id", "\n".join(empty_logs.output))
            with self.assertLogs("zola_workspace", level="WARNING") as missing_logs:
                self.assertFalse(turn_context.is_brian_turn("turn-missing"))
            self.assertIn("reason=no_turn_record", "\n".join(missing_logs.output))
            turn_context.record_pre_llm_call(turn_id="turn-cron", platform="cron")
            with self.assertLogs("zola_workspace", level="WARNING") as platform_logs:
                self.assertFalse(turn_context.is_brian_turn("turn-cron"))
            self.assertIn("reason=platform", "\n".join(platform_logs.output))
            turn_context.record_pre_llm_call(
                turn_id="turn-parent", platform="tui", parent_session_id="other"
            )
            with self.assertLogs("zola_workspace", level="WARNING") as parent_logs:
                self.assertFalse(turn_context.is_brian_turn("turn-parent"))
            self.assertIn("reason=parent_session", "\n".join(parent_logs.output))
        finally:
            turn_context.clear_all_for_tests()

    def test_empty_context_var_still_forgets_when_the_turn_id_is_passed(self) -> None:
        import origin
        import registry
        import turn_context

        seeded = self._seed_memory_and_contact()
        listed = self._forget("Forget SYNYES", confirm=False)
        person_ids = [
            candidate["id"]
            for group in listed["groups"]
            for candidate in group["candidates"]
            if candidate["kind"] == "person"
        ]
        self.assertEqual(person_ids, ["person:c_synyes"], listed)
        forget.set_client_origin_override_for_tests(None)
        proactive_store.set_ticket_override_for_tests(None)
        try:
            turn_context.clear_all_for_tests()
            origin.clear_for_tests()
            turn_context.record_pre_llm_call(
                turn_id="turn-b6", platform="tui", user_message="Forget SYNYES"
            )
            origin.grant_turn_for_tests("turn-b6", "Forget SYNYES")
            self.assertFalse(turn_context.is_brian_turn())
            self.assertTrue(turn_context.is_brian_turn("turn-b6"))
            registry.put(self.provider._session_id, self.provider)
            self.provider._current_user_message = "Yes"
            args = {
                "description": "Yes",
                "confirm": True,
                "target_ids": person_ids,
            }
            minted = forget.pre_tool_call_hook(
                tool_name="forget_memory",
                args=args,
                session_id=self.provider._session_id,
                turn_id="turn-b6",
                tool_call_id="call-b6",
            )
            self.assertEqual(minted["action"], "modify", minted)
            args[forget._ORIGIN_TOKEN_KEY] = minted["args"][forget._ORIGIN_TOKEN_KEY]
            erased = json.loads(forget.handle_forget_memory(self.provider, args))
            self.assertTrue(erased["ok"], erased)
            self.assertNotIn(erased.get("refused_reason"), ("empty_turn_id", "origin"))
            self.assertIsNone(
                self.proactive.execute(
                    "SELECT id FROM items WHERE id = ?", (seeded["text_id"],)
                ).fetchone()
            )
        finally:
            forget.set_client_origin_override_for_tests(True)
            proactive_store.set_ticket_override_for_tests(True)
            registry.remove(self.provider._session_id, self.provider)
            turn_context.clear_all_for_tests()
            origin.clear_for_tests()

    def test_description_without_the_name_uses_his_message(self) -> None:
        self._seed_memory_and_contact()
        self.provider._current_user_message = "Forget SYNYES"
        listed = json.loads(
            forget.handle_forget_memory(
                self.provider,
                {"description": "the note from earlier", "confirm": False},
            )
        )
        ids = [
            candidate["id"]
            for group in listed["groups"]
            for candidate in group["candidates"]
        ]
        self.assertEqual(ids, ["person:c_synyes"], listed)

    def test_cold_index_waits_then_returns_one_person(self) -> None:
        import contact_index

        self._seed_memory_and_contact()
        person = contact_index.get_index().people[0]
        contact_index.set_people_for_tests(None)
        self.assertFalse(contact_index.index_loaded())
        real = contact_index.refresh_bounded

        def bounded(timeout=contact_index.TURN_REFRESH_BOUND_SECONDS):
            self.assertEqual(timeout, contact_index.TURN_REFRESH_BOUND_SECONDS)
            contact_index.set_people_for_tests([person])
            return True

        contact_index.refresh_bounded = bounded
        try:
            self.provider._current_user_message = "Forget SYNYES"
            listed = json.loads(
                forget.handle_forget_memory(
                    self.provider,
                    {"description": "a note", "confirm": False},
                )
            )
        finally:
            contact_index.refresh_bounded = real
        ids = [
            candidate["id"]
            for group in listed["groups"]
            for candidate in group["candidates"]
        ]
        self.assertEqual(ids, ["person:c_synyes"], listed)
        self.assertNotIn("No matches", listed["message"])

    def test_index_bound_forgets_what_it_can_and_says_so(self) -> None:
        import contact_index

        seeded = self._seed_memory_and_contact()
        self.proactive.execute(
            "UPDATE loops SET sender_display_name = ? WHERE id = ?",
            ("SYNYES", seeded["open_watch"]),
        )
        self.proactive.commit()
        contact_index.set_people_for_tests(None)
        real = contact_index.refresh_bounded

        def bounded(timeout=contact_index.TURN_REFRESH_BOUND_SECONDS):
            self.assertEqual(timeout, 2.0)
            return False

        contact_index.refresh_bounded = bounded
        try:
            self.provider._current_user_message = "Forget SYNYES"
            listed = json.loads(
                forget.handle_forget_memory(
                    self.provider,
                    {"description": "Forget SYNYES", "confirm": False},
                )
            )
            ids = [
                candidate["id"]
                for group in listed["groups"]
                for candidate in group["candidates"]
                if candidate["kind"] == "person"
            ]
            self.assertEqual(len(ids), 1, listed)
            erased = json.loads(
                forget.handle_forget_memory(
                    self.provider,
                    {"description": "Yes", "confirm": True, "target_ids": ids},
                )
            )
        finally:
            contact_index.refresh_bounded = real
        self.assertTrue(erased["ok"], erased)
        self.assertIn("within 2 seconds", erased["message"])
        self.assertIn("may be incomplete", erased["message"])
        self.assertIsNone(
            self.memory.execute("SELECT id FROM entities WHERE id = ?", ("synyes-entity",)).fetchone()
        )
        closed = self.proactive.execute(
            "SELECT status, closed_intent, address_hashes_json FROM loops WHERE id = ?",
            (seeded["open_watch"],),
        ).fetchone()
        self.assertEqual(closed["closed_intent"], "forgotten")
        self.assertEqual(closed["address_hashes_json"], "[]")

    def test_memory_remove_is_blocked_and_the_yes_sweeps_the_note(self) -> None:
        import registry

        hermes = Path(r"C:\Users\test\Dev\hermes-agent")
        if str(hermes) not in sys.path:
            sys.path.insert(0, str(hermes))
        from tools.memory_tool import MemoryStore

        seeded = self._seed_memory_and_contact()
        note = "SYNYES prefers tea."
        disk = MemoryStore()
        disk.load_from_disk()
        added = disk.add("memory", note)
        self.assertTrue(added.get("success"), added)
        now = "2026-01-05T00:00:00Z"
        self.memory.execute(
            "INSERT INTO facts (id, target, text, tag, state, learned_at, indexed_at, "
            "updated_at, superseded_at, source) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?)",
            ("fact-synyes", "memory", note, "", "active", now, now, "notify"),
        )
        self.memory.commit()
        self.provider._current_user_message = "Forget SYNYES"
        registry.put(self.provider._session_id, self.provider)
        try:
            blocked = forget.pre_tool_call_hook(
                tool_name="memory",
                args={"action": "remove", "target": "memory", "old_text": note},
                session_id=self.provider._session_id,
                turn_id="turn-note",
            )
            self.assertEqual(blocked["action"], "block", blocked)
            self.assertIn(note, (self.home / "memories" / "MEMORY.md").read_text(encoding="utf-8"))
            listed = self._forget("Forget SYNYES", confirm=False)
            ids = [
                candidate["id"]
                for group in listed["groups"]
                for candidate in group["candidates"]
                if candidate["kind"] == "person"
            ]
            erased = self._forget("Yes", confirm=True, target_ids=ids)
        finally:
            registry.remove(self.provider._session_id, self.provider)
        self.assertTrue(erased["ok"], erased)
        self.assertIn("the notes I was holding", erased["message"])
        self.assertNotIn(note, (self.home / "memories" / "MEMORY.md").read_text(encoding="utf-8"))
        self.assertIsNone(
            self.memory.execute("SELECT id FROM facts WHERE id = ?", ("fact-synyes",)).fetchone()
        )
        self.assertIsNone(
            self.proactive.execute("SELECT id FROM items WHERE id = ?", (seeded["text_id"],)).fetchone()
        )

    def test_one_person_folds_the_pending_turns_that_name_them(self) -> None:
        seeded = self._seed_memory_and_contact()
        now = "2026-01-05T00:00:00Z"
        rows = (
            ("pend-1", "SYNYES called."),
            ("pend-2", "Saw SYNYES today."),
            ("pend-3", "Note about SYNYES."),
        )
        for index, (row_id, text) in enumerate(rows):
            stamp = f"2026-01-05T00:00:0{index}Z"
            self.memory.execute(
                "INSERT INTO pending_turns (id, session_id, turn_index, user_text, "
                "assistant_text, user_time, assistant_time, consolidation_generation, "
                "forget_hold, created_at, turn_fingerprint) VALUES (?, ?, ?, ?, '', ?, '', 0, 0, ?, ?)",
                (row_id, "s-p9", index, text, stamp, stamp, row_id),
            )
        self.memory.commit()
        listed = self._forget("Forget SYNYES", confirm=False)
        ids = [
            candidate["id"]
            for group in listed["groups"]
            for candidate in group["candidates"]
        ]
        self.assertEqual(ids, ["person:c_synyes"], listed)
        self.assertEqual(len(listed["groups"]), 1)
        self.assertFalse(listed["groups"][0]["ask_brian"])
        erased = self._forget("Yes", confirm=True, target_ids=ids)
        self.assertTrue(erased["ok"], erased)
        self.assertEqual(_must(erased), ["notifications_display_name", "texts_on_phone"])
        self.assertEqual(
            self.memory.execute("SELECT COUNT(*) FROM pending_turns").fetchone()[0],
            0,
        )
        self.assertIsNone(
            self.proactive.execute("SELECT id FROM items WHERE id = ?", (seeded["text_id"],)).fetchone()
        )

    def _install_bebo(self):
        self._install_contact(
            name="Bebo",
            handle="c_bebo",
            numbers=("+15555550188",),
            emails=("bebo-test@example.com",),
        )

    def _insert_episode(self, row_id: str, summary: str) -> None:
        now = "2026-01-06T00:00:00Z"
        self.memory.execute(
            "INSERT INTO episodes (id, summary, significance, event_time, "
            "event_time_basis, event_time_evidence, open_items_json, "
            "source_session_id, source_turn_start, source_turn_end, recorded_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (row_id, summary, "synthetic", now, "stated", "", "[]", "s-p9", 1, 1, now),
        )
        self.memory.commit()

    def _insert_notebook_fact(self, fact_id: str, text: str) -> None:
        hermes = Path(r"C:\Users\test\Dev\hermes-agent")
        if str(hermes) not in sys.path:
            sys.path.insert(0, str(hermes))
        from tools.memory_tool import MemoryStore

        disk = MemoryStore()
        disk.load_from_disk()
        added = disk.add("memory", text)
        self.assertTrue(added.get("success"), added)
        now = "2026-01-06T00:00:00Z"
        self.memory.execute(
            "INSERT INTO facts (id, target, text, tag, state, learned_at, indexed_at, "
            "updated_at, superseded_at, source) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?)",
            (fact_id, "memory", text, "", "active", now, now, "notify"),
        )
        self.memory.commit()

    def test_possessive_notebook_fact_is_removed_by_forget_bebo(self) -> None:
        import contact_index

        straight = "Bebo's birthday is in March."
        curly = "Bebo\u2019s birthday is noted."
        self.assertTrue(forget._names_person(straight, "Bebo"))
        self.assertTrue(forget._names_person(curly, "Bebo"))
        self._install_bebo()
        try:
            self._insert_notebook_fact("fact-straight", straight)
            self._insert_notebook_fact("fact-curly", curly)
            listed = self._forget("Forget Bebo", confirm=False)
            ids = [
                candidate["id"]
                for group in listed["groups"]
                for candidate in group["candidates"]
            ]
            self.assertEqual(ids, ["person:c_bebo"], listed)
            self.assertEqual(len(listed["groups"]), 1)
            erased = self._forget("Yes", confirm=True, target_ids=ids)
            self.assertTrue(erased["ok"], erased)
            notebook = (self.home / "memories" / "MEMORY.md").read_text(encoding="utf-8")
            self.assertNotIn(straight, notebook)
            self.assertNotIn(curly, notebook)
            self.assertIsNone(
                self.memory.execute("SELECT id FROM facts WHERE id = ?", ("fact-straight",)).fetchone()
            )
            self.assertIsNone(
                self.memory.execute("SELECT id FROM facts WHERE id = ?", ("fact-curly",)).fetchone()
            )
        finally:
            contact_index.reset_for_tests()

    def test_possessive_episode_folds_into_one_person(self) -> None:
        import contact_index

        straight = "Bebo's birthday is in March."
        curly = "Bebo\u2019s birthday was mentioned."
        self.assertIn("bebo", forget._short_label(straight).casefold())
        self.assertTrue(forget._names_person(straight, "Bebo"))
        self.assertTrue(forget._names_person(curly, "Bebo"))
        self._install_bebo()
        try:
            self._insert_episode("ep-straight", straight)
            self._insert_episode("ep-curly", curly)
            listed = self._forget("Forget Bebo", confirm=False)
            ids = [
                candidate["id"]
                for group in listed["groups"]
                for candidate in group["candidates"]
            ]
            self.assertEqual(ids, ["person:c_bebo"], listed)
            self.assertEqual(len(listed["groups"]), 1)
            self.assertFalse(listed["groups"][0]["ask_brian"])
            erased = self._forget("Yes", confirm=True, target_ids=ids)
            self.assertTrue(erased["ok"], erased)
            self.assertIsNone(
                self.memory.execute("SELECT id FROM episodes WHERE id = ?", ("ep-straight",)).fetchone()
            )
            self.assertIsNone(
                self.memory.execute("SELECT id FROM episodes WHERE id = ?", ("ep-curly",)).fetchone()
            )
            self.assertIsNotNone(
                self.memory.execute("SELECT id FROM episodes WHERE id = ?", ("ep-kept",)).fetchone()
            )
        finally:
            contact_index.reset_for_tests()

    def test_longer_word_starting_with_the_name_is_not_removed(self) -> None:
        import contact_index

        place = "Beboland is west of here."
        episode = "Visited Beboland."
        self.assertFalse(forget._names_person(place, "Bebo"))
        self.assertFalse(forget._names_person(episode, "Bebo"))
        self.assertFalse(forget._names_person("BeboDev called.", "Bebo"))
        self._install_bebo()
        try:
            self._insert_notebook_fact("fact-place", place)
            self._insert_episode("ep-place", episode)
            listed = self._forget("Forget Bebo", confirm=False)
            ids = [
                candidate["id"]
                for group in listed["groups"]
                for candidate in group["candidates"]
            ]
            self.assertNotIn("fact-place", ids, listed)
            self.assertNotIn("ep-place", ids, listed)
            erased = self._forget("Yes", confirm=True, target_ids=["person:c_bebo"])
            self.assertTrue(erased["ok"], erased)
            self.assertIn(place, (self.home / "memories" / "MEMORY.md").read_text(encoding="utf-8"))
            self.assertIsNotNone(
                self.memory.execute("SELECT id FROM facts WHERE id = ?", ("fact-place",)).fetchone()
            )
            self.assertIsNotNone(
                self.memory.execute("SELECT id FROM episodes WHERE id = ?", ("ep-place",)).fetchone()
            )
        finally:
            contact_index.reset_for_tests()


class HermesForgetPinTests(unittest.TestCase):
    """Fail if a Hermes rename moves an internal the forget path calls."""

    def test_forget_path_hermes_internals_keep_their_names(self) -> None:
        import inspect

        hermes = Path(r"C:\Users\test\Dev\hermes-agent")
        if str(hermes) not in sys.path:
            sys.path.append(str(hermes))
        import agent.inline_tool_executors as inline
        import agent.memory_manager as memory_manager
        import agent.memory_provider as memory_provider
        import agent.tool_executor as tool_executor
        import tools.memory_tool as memory_tool
        from provider import ZolaMemoryProvider

        self.assertTrue(callable(memory_tool.memory_tool))
        self.assertTrue(callable(memory_tool.load_on_disk_store))
        signature = inspect.signature(memory_tool.memory_tool)
        for name in ("action", "target", "old_text", "store"):
            self.assertIn(name, signature.parameters)

        self.assertTrue(callable(inline.tool_hook_ids))

        class _Agent:
            session_id = "pin-session"
            _current_turn_id = "turn-pin"
            _current_api_request_id = "req-pin"

        ids = inline.tool_hook_ids(_Agent(), "task-pin", "call-pin")
        self.assertEqual(ids.get("turn_id"), "turn-pin")
        self.assertEqual(
            set(ids),
            {"task_id", "session_id", "tool_call_id", "turn_id", "api_request_id"},
        )

        pre_tool = inspect.getsource(tool_executor._pre_tool_block)
        self.assertIn("tool_hook_ids(", pre_tool)
        dispatch = inspect.getsource(tool_executor._resolve_sequential_dispatch)
        self.assertIn("has_tool", dispatch)
        self.assertIn("handle_tool_call", dispatch)

        manager_start = inspect.signature(memory_manager.MemoryManager.on_turn_start)
        provider_start = inspect.signature(memory_provider.MemoryProvider.on_turn_start)
        self.assertIn("message", manager_start.parameters)
        self.assertIn("message", provider_start.parameters)
        self.assertIn(
            "p.on_turn_start(turn_number, message",
            inspect.getsource(memory_manager.MemoryManager.on_turn_start),
        )
        self.assertIn(
            "_current_user_message",
            inspect.getsource(ZolaMemoryProvider.on_turn_start),
        )

