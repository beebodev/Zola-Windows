"""P9-STORE Phase 4: transitions, leases, forget, loops, and one-owner SQL."""

from __future__ import annotations

import json
import re
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

import loops
import origin
import proactive_store
import recorded_results
import send_gate
import taint
import turn_context

T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
TOKEN = "P9STORE_SYNTHETIC"
ADDRESS = "p9store-synthetic@example.com"
SQL_OWNER = re.compile(
    r"(?i)\b(?:insert\s+into|update|delete\s+from)\s+"
    r"(?:items|loops|item_attempts|deliveries|cursors|watcher_health|calendar_events|watcher_rejects)\b"
)


def _at(**kwargs) -> datetime:
    return T0 + timedelta(**kwargs)


def _row(conn: sqlite3.Connection, item_id: str):
    return conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()


def _snap(conn: sqlite3.Connection, item_id: str):
    row = _row(conn, item_id)
    return None if row is None else tuple(row)


class StoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self._dir = tempfile.TemporaryDirectory(prefix="p9store_")
        self.path = Path(self._dir.name) / "proactive" / "proactive.db"
        proactive_store.set_ticket_override_for_tests(True)
        proactive_store.set_db_path_for_tests(self.path)
        self.conn = proactive_store.connect(self.path, retry=False)

    def tearDown(self) -> None:
        self.conn.close()
        proactive_store.set_ticket_override_for_tests(None)
        proactive_store.set_db_path_for_tests(None)
        self._dir.cleanup()

    def _gmail(self, message_id: str = "m1", **kwargs):
        now = kwargs.pop("now", T0)
        result = proactive_store.insert_item(
            self.conn,
            source="gmail",
            message_id=message_id,
            thread_id=kwargs.pop("thread_id", "th"),
            sender_address=kwargs.pop("sender_address", ADDRESS),
            sender_display_name=kwargs.pop("sender_display_name", "Synthetic"),
            subject=kwargs.pop("subject", "package notice"),
            snippet=kwargs.pop("snippet", "a notice"),
            body=kwargs.pop("body", "body text"),
            now=now,
        )
        self.assertTrue(result["ok"], result)
        return result["id"]

    def _rank(self, item_id: str, *, now: datetime = T0, label: str = "normal"):
        claimed = proactive_store.claim_rank(self.conn, item_id, now=now)
        self.assertTrue(claimed["ok"], claimed)
        done = proactive_store.complete_rank(
            self.conn, item_id, claimed["attempt_id"], label=label, gist="gist", now=now
        )
        self.assertTrue(done["ok"], done)
        return claimed["attempt_id"]

    def _eligible(self, item_id: str, *, now: datetime = T0):
        self._rank(item_id, now=now)
        # P9-RANK: complete_rank writes eligibility. mark_eligible remains the sweep path.
        if _row(self.conn, item_id)["eligibility"] == "pending":
            marked = proactive_store.mark_eligible(self.conn, item_id, now=now)
            self.assertTrue(marked["ok"], marked)

    def test_allowed_transitions_once(self) -> None:
        item_id = self._gmail()
        self.assertEqual(_row(self.conn, item_id)["processing"], "unranked")
        self._eligible(item_id)
        self.assertEqual(_row(self.conn, item_id)["eligibility"], "eligible")
        self.assertIsNone(_row(self.conn, item_id)["body"])
        selected = proactive_store.select_for_conversation(self.conn, item_id, now=T0)
        self.assertTrue(selected["ok"], selected)
        surfaced = proactive_store.mark_possibly_surfaced(self.conn, item_id, now=T0)
        self.assertTrue(surfaced["ok"], surfaced)
        acked = proactive_store.acknowledge(self.conn, item_id, now=T0)
        self.assertTrue(acked["ok"], acked)
        speech = proactive_store.claim_speech(self.conn, item_id, now=T0)
        self.assertTrue(speech["ok"], speech)
        started = proactive_store.mark_speech_started(
            self.conn, item_id, speech["attempt_id"], now=T0
        )
        self.assertTrue(started["ok"], started)
        delivered = proactive_store.mark_delivered(
            self.conn, item_id, speech["attempt_id"], now=T0
        )
        self.assertTrue(delivered["ok"], delivered)
        self.assertEqual(_row(self.conn, item_id)["delivery"], "delivered")
        closed = proactive_store.close_item(self.conn, item_id, now=T0)
        self.assertTrue(closed["ok"], closed)
        self.assertIsNotNone(_row(self.conn, item_id)["closed_at"])

    def test_illegal_transition_changes_nothing(self) -> None:
        item_id = self._gmail()
        before = _snap(self.conn, item_id)
        for result in (
            proactive_store.complete_rank(self.conn, item_id, "nope", label="normal", now=T0),
            proactive_store.mark_eligible(self.conn, item_id, now=T0),
            proactive_store.claim_speech(self.conn, item_id, now=T0),
            proactive_store.acknowledge(self.conn, item_id, now=T0),
        ):
            self.assertFalse(result["ok"], result)
            self.assertEqual(_snap(self.conn, item_id), before)
        held = self._gmail("held-close")
        self._eligible(held)
        speech = proactive_store.claim_speech(self.conn, held, now=T0)
        self.assertTrue(speech["ok"], speech)
        held_before = _snap(self.conn, held)
        refused_close = proactive_store.close_item(self.conn, held, now=T0)
        self.assertFalse(refused_close["ok"], refused_close)
        self.assertEqual(_snap(self.conn, held), held_before)

    def test_rank_lease_expiry_and_attempt_mismatch(self) -> None:
        item_id = self._gmail()
        first = proactive_store.claim_rank(self.conn, item_id, now=T0)
        self.assertTrue(first["ok"], first)
        early = proactive_store.release_rank_lease(self.conn, now=_at(seconds=119))
        self.assertEqual(early.get("released"), 0)
        stolen = proactive_store.claim_rank(self.conn, item_id, now=_at(seconds=119))
        self.assertFalse(stolen["ok"])
        mismatch = proactive_store.complete_rank(
            self.conn, item_id, "other-attempt", label="normal", now=_at(seconds=119)
        )
        self.assertEqual(mismatch.get("refused_reason"), "attempt_mismatch")
        self.assertEqual(_row(self.conn, item_id)["processing"], "unranked")
        self.assertEqual(_row(self.conn, item_id)["body"], "body text")
        released = proactive_store.release_rank_lease(self.conn, now=_at(seconds=121))
        self.assertEqual(released.get("released"), 1)
        again = proactive_store.claim_rank(self.conn, item_id, now=_at(seconds=121))
        self.assertTrue(again["ok"], again)

    def test_delivery_uncertain_is_not_claimable(self) -> None:
        item_id = self._gmail()
        self._eligible(item_id)
        speech = proactive_store.claim_speech(self.conn, item_id, now=T0)
        started = proactive_store.mark_speech_started(
            self.conn, item_id, speech["attempt_id"], now=T0
        )
        self.assertTrue(started["ok"], started)
        recovered = proactive_store.release_speech_lease(self.conn, now=_at(seconds=121))
        self.assertEqual(recovered.get("uncertain"), 1)
        self.assertEqual(_row(self.conn, item_id)["delivery"], "delivery_uncertain")
        again = proactive_store.claim_speech(self.conn, item_id, now=_at(seconds=121))
        self.assertFalse(again["ok"])
        self.assertEqual(_row(self.conn, item_id)["delivery"], "delivery_uncertain")

    def test_expired_claim_returns_to_none(self) -> None:
        item_id = self._gmail()
        self._eligible(item_id)
        speech = proactive_store.claim_speech(self.conn, item_id, now=T0)
        self.assertTrue(speech["ok"], speech)
        recovered = proactive_store.release_speech_lease(self.conn, now=_at(seconds=31))
        self.assertEqual(recovered.get("released"), 1)
        self.assertEqual(_row(self.conn, item_id)["delivery"], "none")
        again = proactive_store.claim_speech(self.conn, item_id, now=_at(seconds=31))
        self.assertTrue(again["ok"], again)

    def test_retention_nulls_content_and_keeps_inflight_delivery(self) -> None:
        old = _at(days=-8)
        idle = self._gmail("old-idle", now=old, subject="old subject", body="old body")
        held = self._gmail("old-held", now=old, subject="held subject", body="held body")
        self._eligible(held, now=old)
        speech = proactive_store.claim_speech(self.conn, held, now=T0)
        self.assertTrue(speech["ok"], speech)
        first = proactive_store.purge_retention(self.conn, now=T0)
        self.assertTrue(first["ok"], first)
        self.assertEqual(_row(self.conn, idle)["body"], None)
        self.assertEqual(_row(self.conn, idle)["content_state"], "content_expired")
        self.assertEqual(_row(self.conn, held)["delivery"], "claimed")
        self.assertEqual(_row(self.conn, held)["subject"], None)
        attempt = self.conn.execute(
            "SELECT status FROM item_attempts WHERE attempt_id = ?",
            (speech["attempt_id"],),
        ).fetchone()
        self.assertEqual(attempt["status"], "open")
        second = proactive_store.purge_retention(self.conn, now=T0)
        self.assertEqual(second.get("bodies"), 0)
        self.assertEqual(_row(self.conn, held)["delivery"], "claimed")

    def test_purge_nulls_closed_and_expired_loop_text(self) -> None:
        expired = proactive_store.insert_loop(
            self.conn,
            intent="reply",
            predicate={"op": "brian_confirms"},
            session_id="sess-old",
            sender_display_name="Old Synthetic",
            subject="old subject",
            source_ids=["src-old"],
            address_hashes=["hash-old"],
            now=_at(days=-30),
        )
        self.assertTrue(expired["ok"], expired)
        closed = proactive_store.insert_loop(
            self.conn,
            intent="confirm_close",
            predicate={"op": "brian_confirms"},
            session_id="sess-closed",
            sender_display_name="Closed Synthetic",
            subject="closed subject",
            source_ids=["src-closed"],
            address_hashes=["hash-closed"],
            now=T0,
        )
        self.assertTrue(closed["ok"], closed)
        live = proactive_store.insert_loop(
            self.conn,
            intent="confirm_close",
            predicate={"op": "brian_confirms"},
            session_id="sess-live",
            sender_display_name="Live Synthetic",
            subject="live subject",
            source_ids=["src-live"],
            address_hashes=["hash-live"],
            now=T0,
        )
        self.assertTrue(live["ok"], live)
        # close_loop already clears text. This row is closed and still holds it, which is what purge must finish.
        self.conn.execute(
            "UPDATE loops SET status = 'closed' WHERE id = ?",
            (closed["id"],),
        )
        self.conn.commit()
        purged = proactive_store.purge_retention(self.conn, now=T0)
        self.assertTrue(purged["ok"], purged)
        self.assertGreaterEqual(purged.get("loops_expired", 0), 1)

        def _loop(loop_id: str):
            return self.conn.execute(
                "SELECT status, subject, sender_display_name, source_ids_json, "
                "address_hashes_json, closed_intent FROM loops WHERE id = ?",
                (loop_id,),
            ).fetchone()

        expired_row = _loop(expired["id"])
        self.assertEqual(expired_row["status"], "expired")
        self.assertEqual(expired_row["closed_intent"], "expired")
        self.assertIsNone(expired_row["subject"])
        self.assertIsNone(expired_row["sender_display_name"])
        self.assertIn("src-old", expired_row["source_ids_json"])
        self.assertIn("hash-old", expired_row["address_hashes_json"])
        closed_row = _loop(closed["id"])
        self.assertEqual(closed_row["status"], "closed")
        self.assertIsNone(closed_row["closed_intent"])
        self.assertIsNone(closed_row["subject"])
        self.assertIsNone(closed_row["sender_display_name"])
        self.assertIn("src-closed", closed_row["source_ids_json"])
        self.assertIn("hash-closed", closed_row["address_hashes_json"])
        live_row = _loop(live["id"])
        self.assertEqual(live_row["status"], "open")
        self.assertIsNone(live_row["closed_intent"])
        self.assertEqual(live_row["subject"], "live subject")
        self.assertEqual(live_row["sender_display_name"], "Live Synthetic")

    def test_forget_by_entity_hash_and_source_and_unmapped(self) -> None:
        by_entity = self._gmail("ent-msg", subject="alpha notice")
        proactive_store.set_sender_resolution(self.conn, by_entity, entity_id="ent-1")
        by_hash = self._gmail("hash-msg", sender_address=ADDRESS, subject="beta notice")
        by_source = self._gmail("src-msg", subject="gamma notice")
        kept = self._gmail("kept-msg", sender_address="other@example.com", subject="kept")
        digest = proactive_store.address_hash(ADDRESS)
        gone = proactive_store.forget_subject(
            self.conn,
            entity_id="ent-1",
            address_hashes=[digest],
            source_ids=["src-msg"],
        )
        self.assertTrue(gone["ok"], gone)
        self.assertIsNone(_row(self.conn, by_entity))
        self.assertIsNone(_row(self.conn, by_hash))
        self.assertIsNone(_row(self.conn, by_source))
        self.assertIsNotNone(_row(self.conn, kept))
        before = _snap(self.conn, kept)
        unmapped = proactive_store.forget_subject(
            self.conn,
            entity_id="",
            names=["P9STORE_SYNTHETIC"],
        )
        self.assertTrue(unmapped["ok"], unmapped)
        self.assertEqual(unmapped["items_deleted"], 0)
        self.assertEqual(_snap(self.conn, kept), before)

    def test_inflight_forget_redacts_and_keeps_delivery(self) -> None:
        item_id = self._gmail(subject="speak this")
        proactive_store.set_sender_resolution(self.conn, item_id, entity_id="ent-fly")
        self._eligible(item_id)
        speech = proactive_store.claim_speech(self.conn, item_id, now=T0)
        result = proactive_store.forget_subject(self.conn, entity_id="ent-fly")
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["items_redacted"], 1)
        row = _row(self.conn, item_id)
        self.assertEqual(row["content_state"], "forgotten")
        self.assertEqual(row["delivery"], "claimed")
        self.assertIsNone(row["subject"])
        self.assertIsNone(row["entity_id"])
        attempt = self.conn.execute(
            "SELECT attempt_id FROM item_attempts WHERE attempt_id = ?",
            (speech["attempt_id"],),
        ).fetchone()
        self.assertIsNotNone(attempt)

    def test_loop_eligible_and_rank_failed_stays_listed(self) -> None:
        item_id = self._gmail()
        marked = proactive_store.mark_loop_eligible(self.conn, item_id, now=T0)
        self.assertTrue(marked["ok"], marked)
        self.assertEqual(_row(self.conn, item_id)["processing"], "unranked")
        self.assertEqual(_row(self.conn, item_id)["eligibility"], "eligible")
        failed = self._gmail("fail-me")
        for _ in range(5):
            claimed = proactive_store.claim_rank(self.conn, failed, now=T0)
            self.assertTrue(claimed["ok"], claimed)
            outcome = proactive_store.fail_rank(
                self.conn, failed, claimed["attempt_id"], now=T0
            )
            self.assertTrue(outcome["ok"], outcome)
        self.assertEqual(_row(self.conn, failed)["processing"], "rank_failed")
        again = proactive_store.mark_loop_eligible(self.conn, failed, now=T0)
        self.assertTrue(again["ok"], again)
        listed = proactive_store.list_open_items(self.conn)
        reasons = {row["id"]: row["reason"] for row in listed["items"]}
        self.assertEqual(reasons[failed], "rank_failed")
        proactive_store.suppress(self.conn, item_id, now=T0)
        refused = proactive_store.mark_loop_eligible(self.conn, item_id, now=T0)
        self.assertFalse(refused["ok"])
        self.assertEqual(_row(self.conn, item_id)["eligibility"], "suppressed")

    def test_locked_connection_returns_locked(self) -> None:
        item_id = self._gmail()
        other = proactive_store.connect(self.path, timeout_ms=200, retry=False)
        holder = sqlite3.connect(str(self.path), timeout=0.2)
        try:
            holder.execute("BEGIN IMMEDIATE")
            result = proactive_store.forget_subject(other, entity_id="missing")
        finally:
            holder.rollback()
            holder.close()
            other.close()
        self.assertEqual(result["refused_reason"], "locked")
        self.assertIsNotNone(_row(self.conn, item_id))

    def test_forget_closes_open_loop_as_forgotten(self) -> None:
        opened = proactive_store.insert_loop(
            self.conn,
            intent="reply",
            predicate={"op": "brian_confirms"},
            session_id="sess-forget",
            entity_id="ent-forget",
            sender_display_name="Synthetic Sender",
            subject="quartz lantern",
            source_ids=["src-forget"],
            address_hashes=["hash-forget"],
            now=T0,
        )
        self.assertTrue(opened["ok"], opened)
        kept = proactive_store.insert_loop(
            self.conn,
            intent="reply",
            predicate={"op": "brian_confirms"},
            session_id="sess-kept",
            entity_id="ent-forget",
            sender_display_name="Kept Sender",
            subject="kept subject",
            source_ids=["src-kept"],
            address_hashes=["hash-kept"],
            now=T0,
        )
        self.assertTrue(kept["ok"], kept)
        closed = proactive_store.close_loop(self.conn, kept["id"], closed_intent="cancelled")
        self.assertTrue(closed["ok"], closed)
        result = proactive_store.forget_subject(self.conn, entity_id="ent-forget")
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["loops_deleted"], 1)
        forgotten = self.conn.execute(
            "SELECT status, closed_intent, subject, sender_display_name, source_ids_json "
            "FROM loops WHERE id = ?",
            (opened["id"],),
        ).fetchone()
        self.assertEqual(forgotten["status"], "closed")
        self.assertEqual(forgotten["closed_intent"], "forgotten")
        self.assertIsNone(forgotten["subject"])
        self.assertIsNone(forgotten["sender_display_name"])
        self.assertIn("src-forget", forgotten["source_ids_json"])
        prior = self.conn.execute(
            "SELECT status, closed_intent, source_ids_json FROM loops WHERE id = ?",
            (kept["id"],),
        ).fetchone()
        self.assertEqual(prior["status"], "closed")
        self.assertEqual(prior["closed_intent"], "cancelled")
        self.assertIn("src-kept", prior["source_ids_json"])

    def test_v1_schema_migrates_without_guessing_closed_intent(self) -> None:
        self.conn.close()
        legacy = Path(self._dir.name) / "legacy.db"
        raw = sqlite3.connect(legacy)
        raw.row_factory = sqlite3.Row
        proactive_store._migrate_v1(raw)
        raw.execute(
            "CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        raw.execute(
            "INSERT INTO meta (key, value) VALUES ('schema_version', '1')"
        )
        raw.execute(
            """
            INSERT INTO loops (
              id, status, intent, predicate_json, created_at, expires_at, matched_at,
              lapse_told, session_id, entity_id, source_ids_json, address_hashes_json,
              sender_display_name, subject
            ) VALUES (
              'old-closed', 'closed', 'reply', '{}', '2026-01-01T00:00:00Z',
              '2026-02-01T00:00:00Z', NULL, 0, 'sess-old', NULL, '[]', '[]',
              NULL, NULL
            )
            """
        )
        raw.execute(
            """
            INSERT INTO loops (
              id, status, intent, predicate_json, created_at, expires_at, matched_at,
              lapse_told, session_id, entity_id, source_ids_json, address_hashes_json,
              sender_display_name, subject
            ) VALUES (
              'old-open', 'open', 'reply', '{}', '2026-01-01T00:00:00Z',
              '2026-02-01T00:00:00Z', NULL, 0, 'sess-old', NULL, '[]', '[]',
              'Open Synthetic', 'open subject'
            )
            """
        )
        raw.commit()
        raw.close()
        self.conn = proactive_store.connect(legacy, retry=False)
        version = self.conn.execute(
            "SELECT value FROM meta WHERE key = 'schema_version'"
        ).fetchone()[0]
        self.assertEqual(version, str(proactive_store.SCHEMA_VERSION))
        columns = {row[1] for row in self.conn.execute("PRAGMA table_info(loops)")}
        self.assertIn("closed_intent", columns)
        closed = self.conn.execute(
            "SELECT status, closed_intent FROM loops WHERE id = 'old-closed'"
        ).fetchone()
        opened = self.conn.execute(
            "SELECT status, closed_intent FROM loops WHERE id = 'old-open'"
        ).fetchone()
        self.assertEqual(closed["status"], "closed")
        self.assertIsNone(closed["closed_intent"])
        self.assertEqual(opened["status"], "open")
        self.assertIsNone(opened["closed_intent"])

    def test_one_owner_sql(self) -> None:
        offenders = []
        root = REPO_ROOT / "hermes-plugins"
        for path in root.rglob("*.py"):
            if path.name == "proactive_store.py":
                continue
            if "tests" in path.parts:
                continue
            text = path.read_text(encoding="utf-8")
            if SQL_OWNER.search(text):
                offenders.append(str(path))
        self.assertEqual(offenders, [])


class LoopTests(unittest.TestCase):
    def setUp(self) -> None:
        self._dir = tempfile.TemporaryDirectory(prefix="p9loops_")
        self.path = Path(self._dir.name) / "proactive" / "proactive.db"
        proactive_store.set_ticket_override_for_tests(None)
        proactive_store.set_db_path_for_tests(self.path)
        recorded_results.reset_for_tests()
        loops.reset_for_tests()
        turn_context.clear_all_for_tests()
        self.conn = proactive_store.connect(self.path, retry=False)
        self._clock = {"now": 1000.0}
        recorded_results.set_clock_for_tests(lambda: self._clock["now"])

    def tearDown(self) -> None:
        self.conn.close()
        recorded_results.reset_for_tests()
        loops.reset_for_tests()
        turn_context.clear_all_for_tests()
        proactive_store.set_db_path_for_tests(None)
        proactive_store.set_ticket_override_for_tests(None)
        self._dir.cleanup()

    def _ticket(self, session_id: str = "sess-1", turn_id: str = "turn-1"):
        turn_context.record_pre_llm_call(
            turn_id=turn_id,
            session_id=session_id,
            platform="tui",
            user_message="watch that mail",
        )
        origin.grant_turn_for_tests(turn_id, "watch that mail")
        return mock.patch.object(
            turn_context, "current_turn_id_from_context", return_value=turn_id
        )

    def _remember(self, *, name: str, subject: str, address: str, labels=None, session_id="sess-1"):
        with self._ticket(session_id):
            return recorded_results.remember(
                kind=recorded_results.KIND_GMAIL,
                message_id="mid-" + name,
                thread_id="thread-1",
                address=address,
                sender_display_name=name,
                subject=subject,
                labels=labels or ["INBOX"],
                session_id=session_id,
                turn_id="turn-1",
            )

    def test_catalog_first_sentence_is_short_and_says_watch(self) -> None:
        text = " ".join(loops._DESCRIPTION.split())
        end = text.find(".")
        self.assertGreater(end, 0)
        first = text[: end + 1]
        self.assertLessEqual(len(first), 60)
        self.assertIn("watch", first.casefold())

    def test_list_description_names_triggers_and_only_source(self) -> None:
        text = loops._DESCRIPTION.casefold()
        for phrase in (
            "what are you watching for",
            "what are you keeping an eye on",
            "what am i waiting on",
            "any open loops",
            "what did i ask you to watch",
        ):
            self.assertIn(phrase, text)
        self.assertIn("the list result is the only source of what you are watching", text)
        self.assertIn("never answer that question from memory or from the conversation", text)
        self.assertIn("if the tool fails, say you could not check", text)
        self.assertIn("pass a handle from a tool result in this conversation", text)
        self.assertIn("ask him which one before you call create", text)
        self.assertIn("names the sender and subject", text)
        self.assertIn("do not pass a message id, thread id, event id, or email address", text)

    def test_one_handle_several_ambiguous_and_explicit(self) -> None:
        only = self._remember(name="Ada Synthetic", subject="Only subject", address="ada@example.com")
        with self._ticket():
            created = loops.create_loop(self.conn, {"action": "create", "intent": "reply"})
        self.assertTrue(created["ok"], created)
        self.assertEqual(created["watching"]["sender_display_name"], "Ada Synthetic")
        self.assertEqual(created["watching"]["subject"], "Only subject")
        self._remember(name="Bea Synthetic", subject="Second subject", address="bea@example.com")
        with self._ticket():
            ambiguous = loops.create_loop(self.conn, {"action": "create", "intent": "reply"})
        self.assertEqual(ambiguous.get("refused_reason"), "ambiguous")
        with self._ticket():
            chosen = loops.create_loop(
                self.conn,
                {"action": "create", "intent": "reply", "handle": only},
            )
        self.assertTrue(chosen["ok"], chosen)
        self.assertEqual(chosen["watching"]["sender_display_name"], "Ada Synthetic")
        self.assertEqual(chosen["watching"]["subject"], "Only subject")

    def test_expired_other_session_and_typed_id_refused(self) -> None:
        handle = self._remember(name="Ada Synthetic", subject="Only subject", address="ada@example.com")
        self._clock["now"] += recorded_results.HANDLE_TTL_SECONDS + 1
        with self._ticket():
            expired = loops.create_loop(
                self.conn, {"action": "create", "intent": "reply", "handle": handle}
            )
        self.assertEqual(expired.get("refused_reason"), "unknown_handle")
        self._clock["now"] = 1000.0
        fresh = self._remember(
            name="Ada Synthetic",
            subject="Only subject",
            address="ada@example.com",
            session_id="sess-1",
        )
        with self._ticket("other-session"):
            other = loops.create_loop(
                self.conn, {"action": "create", "intent": "reply", "handle": fresh}
            )
        self.assertEqual(other.get("refused_reason"), "unknown_handle")
        with self._ticket():
            typed = loops.create_loop(
                self.conn,
                {"action": "create", "intent": "reply", "message_id": "mid-typed"},
            )
        self.assertEqual(typed.get("refused_reason"), "untrusted_argument")
        with self._ticket():
            mailed = loops.create_loop(
                self.conn,
                {"action": "create", "intent": "reply", "handle": "ada@example.com"},
            )
        self.assertEqual(mailed.get("refused_reason"), "untrusted_argument")

    def test_reply_compile_incoming_matches_and_sent_refuses(self) -> None:
        handle = self._remember(name="Ada Synthetic", subject="Only subject", address="ada@example.com")
        with self._ticket():
            record = recorded_results.resolve("sess-1", recorded_results.KIND_GMAIL, handle)["record"]
        compiled = loops.compile_predicate("reply", record, created_at="2026-01-02T00:00:00Z")
        self.assertTrue(compiled["ok"], compiled)
        incoming = {
            "thread_id": "thread-1",
            "sender_address_hash": record["address_hashes"][0],
            "detected_at": "2026-01-03T00:00:00Z",
        }
        self.assertTrue(loops.evaluate(compiled["predicate"], incoming))
        own = dict(incoming)
        own["sender_address_hash"] = proactive_store.address_hash("brian-sent@example.com")
        self.assertFalse(loops.evaluate(compiled["predicate"], own))
        sent = dict(record)
        sent["labels"] = ["SENT"]
        refused = loops.compile_predicate("reply", sent, created_at="2026-01-02T00:00:00Z")
        self.assertEqual(refused.get("refused_reason"), "sent_only")
        draft = dict(record)
        draft["labels"] = ["DRAFT"]
        draft["address_hashes"] = []
        self.assertEqual(
            loops.compile_predicate("reply", draft, created_at="2026-01-02T00:00:00Z").get("refused_reason"),
            "sent_only",
        )

    def test_match_does_not_close_and_close_needs_list_and_ticket(self) -> None:
        self._remember(name="Ada Synthetic", subject="Only subject", address="ada@example.com")
        with self._ticket():
            created = loops.create_loop(self.conn, {"action": "create", "intent": "reply"})
        self.assertTrue(created["ok"], created)
        noted = proactive_store.note_loop_match_on_loop(self.conn, created["loop_id"], now=T0)
        self.assertTrue(noted["ok"], noted)
        status = self.conn.execute(
            "SELECT status, subject FROM loops WHERE id = ?",
            (created["loop_id"],),
        ).fetchone()
        self.assertEqual(status["status"], "open")
        proactive_store.set_ticket_override_for_tests(False)
        turn_context.clear_all_for_tests()
        refused = proactive_store.close_loop(self.conn, created["loop_id"])
        self.assertEqual(refused.get("refused_reason"), "origin")
        proactive_store.set_ticket_override_for_tests(True)
        with self._ticket():
            listed = loops.list_loops(self.conn)
        self.assertTrue(listed["ok"], listed)
        self.assertEqual(listed["loops"][0]["subject"], "Only subject")
        self.assertEqual(listed["loops"][0]["sender_display_name"], "Ada Synthetic")
        self.assertEqual(listed["loops"][0]["intent"], "reply")
        with self._ticket():
            closed = loops.close_listed(self.conn, {"action": "close", "loop_id": created["loop_id"]})
        self.assertTrue(closed["ok"], closed)
        after = self.conn.execute(
            "SELECT status, subject, sender_display_name FROM loops WHERE id = ?",
            (created["loop_id"],),
        ).fetchone()
        self.assertEqual(after["status"], "closed")
        self.assertFalse(after["subject"])
        self.assertFalse(after["sender_display_name"])

    def test_session_end_hook_keeps_handles(self) -> None:
        handle = self._remember(name="Ada Synthetic", subject="Only subject", address="ada@example.com")
        send_gate.on_session_end_hook(turn_id="turn-1", session_id="sess-1")
        resolved = recorded_results.resolve("sess-1", recorded_results.KIND_GMAIL, handle)
        self.assertTrue(resolved["ok"], resolved)
        self.assertEqual(resolved["record"]["subject"], "Only subject")

    def test_session_b_lists_and_closes_a_loop_from_session_a(self) -> None:
        self._remember(
            name="Ada Synthetic",
            subject="Only subject",
            address="ada@example.com",
            session_id="sess-a",
        )
        with self._ticket("sess-a", "turn-a"):
            created = loops.create_loop(self.conn, {"action": "create", "intent": "reply"})
        self.assertTrue(created["ok"], created)
        with self._ticket("sess-b", "turn-b"):
            early = loops.close_listed(
                self.conn, {"action": "close", "loop_id": created["loop_id"]}
            )
        self.assertEqual(early.get("refused_reason"), "unknown_loop")
        with self._ticket("sess-b", "turn-b"):
            listed = loops.list_loops(self.conn)
        self.assertTrue(listed["ok"], listed)
        self.assertEqual(listed["loops"][0]["id"], created["loop_id"])
        self.assertEqual(listed["loops"][0]["sender_display_name"], "Ada Synthetic")
        self.assertEqual(listed["loops"][0]["subject"], "Only subject")
        with self._ticket("sess-b", "turn-b"):
            closed = loops.close_listed(
                self.conn, {"action": "close", "loop_id": created["loop_id"]}
            )
        self.assertTrue(closed["ok"], closed)
        status = self.conn.execute(
            "SELECT status, session_id FROM loops WHERE id = ?",
            (created["loop_id"],),
        ).fetchone()
        self.assertEqual(status["status"], "closed")
        self.assertEqual(status["session_id"], "sess-a")

    def test_list_frames_and_taints_and_create_echo_taints_once(self) -> None:
        import os

        import log as wslog

        home = Path(self._dir.name)
        previous = os.environ.get("HERMES_HOME")
        os.environ["HERMES_HOME"] = str(home)
        wslog.reset_log_handler_for_tests()
        taint.set_store_path_for_tests(home / "taint.sqlite")
        taint.set_lineage_root_fn_for_tests(lambda _sid: None)
        try:
            self._remember(
                name="Ada Synthetic",
                subject="Only subject",
                address="ada@example.com",
                session_id="sess-frame",
            )
            self.assertFalse(taint.is_tainted("sess-frame"))
            with self._ticket("sess-frame", "turn-frame"):
                raw = loops.loops_handler({"action": "create", "intent": "reply"})
            self.assertIn("<untrusted_tool_result", raw)
            self.assertIn("Only subject", raw)
            self.assertIn("Ada Synthetic", raw)
            self.assertTrue(taint.is_tainted("sess-frame"))
            with self._ticket("sess-frame", "turn-frame"):
                again = loops.loops_handler({"action": "list"})
            self.assertIn("<untrusted_tool_result", again)
            inner = again.split("\n\n", 1)[1].rsplit("\n</untrusted_tool_result>", 1)[0]
            listed = json.loads(inner)
            self.assertEqual(listed["loops"][0]["subject"], "Only subject")
            self.assertEqual(listed["loops"][0]["sender_display_name"], "Ada Synthetic")
            log_path = home / "logs" / "zola_workspace.log"
            if log_path.exists():
                log_text = log_path.read_text(encoding="utf-8")
                self.assertNotIn("Only subject", log_text)
                self.assertNotIn("Ada Synthetic", log_text)
        finally:
            taint.reset_store_path_for_tests()
            wslog.reset_log_handler_for_tests()
            if previous is None:
                os.environ.pop("HERMES_HOME", None)
            else:
                os.environ["HERMES_HOME"] = previous

    def test_each_close_intent_is_stored_and_watch_intent_stays(self) -> None:
        for index, closed_intent in enumerate(
            ("reply", "cancelled", "status_change", "confirm_close")
        ):
            recorded_results.reset_for_tests()
            loops.reset_for_tests()
            session_id = f"sess-close-{index}"
            self._remember(
                name="Ada Synthetic",
                subject="Only subject",
                address="ada@example.com",
                session_id=session_id,
            )
            with self._ticket(session_id, f"turn-{index}"):
                created = loops.create_loop(
                    self.conn, {"action": "create", "intent": "reply"}
                )
            self.assertTrue(created["ok"], created)
            with self._ticket(session_id, f"turn-{index}"):
                loops.list_loops(self.conn)
                closed = loops.close_listed(
                    self.conn,
                    {
                        "action": "close",
                        "loop_id": created["loop_id"],
                        "intent": closed_intent,
                    },
                )
            self.assertTrue(closed["ok"], closed)
            row = self.conn.execute(
                "SELECT status, intent, closed_intent FROM loops WHERE id = ?",
                (created["loop_id"],),
            ).fetchone()
            self.assertEqual(row["status"], "closed")
            self.assertEqual(row["intent"], "reply")
            self.assertEqual(row["closed_intent"], closed_intent)
