"""P10-WATCH. Synthetic contact only. No live Google and no phone."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

import contact_index
import loops
import origin
import proactive_store
import speech
import turn_context

NOW = datetime.now(timezone.utc).replace(microsecond=0)
NUMBER = "+15555550100"
NAME = "Beebo Dev"


def _person() -> contact_index.Person:
    import phone_ids
    import address_hash

    return contact_index.Person(
        handle="c_beebo",
        display_name=NAME,
        numbers=(NUMBER,),
        number_hashes=frozenset({phone_ids.hash(NUMBER)}),
        emails=("beebo@example.com",),
        email_hashes=frozenset({address_hash.address_hash("beebo@example.com")}),
    )


class WatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self._dir = tempfile.TemporaryDirectory()
        self.path = Path(self._dir.name) / "proactive.db"
        proactive_store.set_db_path_for_tests(self.path)
        proactive_store.set_ticket_override_for_tests(True)
        self.conn = proactive_store.connect(self.path, retry=False)
        contact_index.reset_for_tests()
        contact_index.set_people_for_tests([_person()])
        loops.reset_for_tests()
        self._turn = 0

    def tearDown(self) -> None:
        self.conn.close()
        proactive_store.set_db_path_for_tests(None)
        proactive_store.set_ticket_override_for_tests(None)
        contact_index.reset_for_tests()
        loops.reset_for_tests()
        self._dir.cleanup()

    def _turn_on(self, message: str, session_id: str = "sess-watch"):
        self._turn += 1
        turn_id = "turn-%s" % self._turn
        turn_context.record_pre_llm_call(
            turn_id=turn_id,
            session_id=session_id,
            platform="tui",
            user_message=message,
        )
        origin.grant_turn_for_tests(turn_id, message)
        return mock.patch.object(turn_context, "current_turn_id_from_context", return_value=turn_id)

    def _create(self, message: str, **args):
        payload = {"action": "create", "intent": "person", "person": NAME}
        payload.update(args)
        with self._turn_on(message):
            return loops.create_loop(self.conn, payload)

    def _ingest(
        self,
        provider_id: str,
        when: datetime,
        *,
        kind: str = "sms",
        group: int = 0,
        sender: str = NUMBER,
        package: str = "",
        notification_key: str = "",
    ):
        return proactive_store.ingest_phone_item(
            self.conn,
            kind=kind,
            device_id="device-test",
            revision=1,
            completeness="complete",
            received_at=when,
            provider_id=provider_id,
            package=package,
            notification_key=notification_key,
            newest_message_timestamp="1000" if kind == "notif" else "",
            sender_raw=sender,
            sender_display_name=NAME if kind == "notif" else "",
            body="synthetic",
            is_group=group,
            now=when,
        )

    def _evaluate(self, item_id: str) -> None:
        row = self.conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
        view = {
            "source": row["source"],
            "message_id": row["message_id"],
            "sender_address_hash": row["sender_address_hash"],
            "detected_at": row["detected_at"],
            "is_group": row["is_group"],
        }
        found = proactive_store.list_open_loop_predicates(self.conn)
        for loop in found["loops"]:
            if loops.evaluate(loop["predicate"], view):
                proactive_store.bind_open_loop_match(self.conn, loop["id"], item_id, now=NOW)

    def test_schema8_scratch_counts(self) -> None:
        self.conn.close()
        raw = proactive_store.connect(self.path, retry=False)
        before_items = raw.execute("SELECT COUNT(*) FROM items").fetchone()[0]
        before_loops = raw.execute("SELECT COUNT(*) FROM loops").fetchone()[0]
        version = raw.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()[0]
        self.assertEqual(version, "8")
        raw.execute(
            """
            INSERT INTO loops (
              id, status, intent, predicate_json, created_at, expires_at, matched_at,
              lapse_told, session_id, entity_id, source_ids_json, address_hashes_json,
              sender_display_name, subject, name_source
            ) VALUES (
              'keep', 'open', 'person', '{}', '2026-06-01T00:00:00Z', '2026-06-15T00:00:00Z',
              NULL, 0, 'sess', NULL, '[]', '[]', 'Kept', NULL, 'contacts_index'
            )
            """
        )
        raw.commit()
        self.assertEqual(raw.execute("SELECT COUNT(*) FROM loops").fetchone()[0], before_loops + 1)
        self.assertEqual(raw.execute("SELECT COUNT(*) FROM items").fetchone()[0], before_items)
        raw.close()
        self.conn = proactive_store.connect(self.path, retry=False)

    def test_hear_from_is_both_and_text_noun_is_not_a_channel(self) -> None:
        created = self._create("Let me know when I hear from Beebo Dev about the text I sent.")
        self.assertTrue(created["ok"], created)
        self.assertEqual(created["channel"], "both")
        self.assertIn("numbers and email addresses saved", created["say"])
        row = self.conn.execute("SELECT predicate_json, name_source FROM loops").fetchone()
        self.assertEqual(row["name_source"], "contacts_index")
        predicate = json.loads(row["predicate_json"])
        self.assertEqual(predicate["channel"], "both")
        self.assertEqual(predicate["lifetime"], "once")

    def test_dont_watch_stop_and_what_are_you_watching_create_nothing(self) -> None:
        for message in (
            "Don't watch Beebo Dev.",
            "Stop watching Beebo Dev.",
            "What are you watching for Beebo Dev?",
        ):
            created = self._create(message)
            self.assertEqual(created.get("refused_reason"), "not_a_watch", message)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM loops").fetchone()[0], 0)

    def test_watch_for_is_one_shot(self) -> None:
        created = self._create("Watch for Beebo Dev.")
        self.assertTrue(created["ok"], created)
        self.assertEqual(created["lifetime"], "once")

    def test_fuzzy_yes_creates_and_no_does_not(self) -> None:
        asked = self._create("Watch for Bebo Dev.", person="Bebo Dev")
        self.assertEqual(asked.get("refused_reason"), "confirm_needed", asked)
        with self._turn_on("No"):
            refused = loops.create_loop(self.conn, {"action": "create", "intent": "person", "person": "Bebo Dev"})
        self.assertFalse(self.conn.execute("SELECT COUNT(*) FROM loops").fetchone()[0])
        self.assertIn("didn't change", refused.get("say") or "")
        asked = self._create("Watch for Bebo Dev.", person="Bebo Dev")
        self.assertEqual(asked.get("refused_reason"), "confirm_needed")
        with self._turn_on("Yes"):
            created = loops.create_loop(self.conn, {"action": "create", "intent": "person", "person": "Bebo Dev"})
        self.assertTrue(created["ok"], created)
        self.assertEqual(created["display_name"], NAME)

    def test_one_shot_satisfied_mutes_later_matches(self) -> None:
        created = self._create("Let me know when I hear from Beebo Dev.")
        self.assertTrue(created["ok"], created)
        base = datetime.now(timezone.utc).replace(microsecond=0)
        first = self._ingest("m1", base + timedelta(minutes=1))
        second = self._ingest("m2", base + timedelta(hours=1))
        self._evaluate(first["id"])
        self._evaluate(second["id"])
        self.assertEqual(self.conn.execute("SELECT loop_matched FROM items WHERE id = ?", (second["id"],)).fetchone()[0], 1)
        claim = proactive_store.claim_next_speech(self.conn, now=base + timedelta(hours=2))
        self.assertTrue(claim["ok"], claim)
        self.assertEqual(claim["item_id"], first["id"])
        started = proactive_store.mark_speech_started(self.conn, claim["item_id"], claim["attempt_id"], now=base + timedelta(hours=2))
        self.assertTrue(started["ok"], started)
        delivered = proactive_store.mark_delivered(self.conn, claim["item_id"], claim["attempt_id"], now=base + timedelta(hours=2, minutes=1))
        self.assertTrue(delivered["ok"], delivered)
        closed = self.conn.execute("SELECT status, closed_intent FROM loops").fetchone()
        self.assertEqual(closed["status"], "closed")
        self.assertEqual(closed["closed_intent"], "delivered")
        again = proactive_store.claim_next_speech(self.conn, now=base + timedelta(hours=3))
        self.assertEqual(again.get("refused_reason"), "nothing_speakable")
        self.assertEqual(self.conn.execute("SELECT loop_matched FROM items WHERE id = ?", (second["id"],)).fetchone()[0], 1)

    def test_standing_says_direct_only_and_gap_joins_one_line(self) -> None:
        created = self._create("Let me know every time Beebo Dev texts.")
        self.assertTrue(created["ok"], created)
        self.assertIn("direct texts only", created["say"])
        base = datetime.now(timezone.utc).replace(microsecond=0)
        direct = self._ingest("d1", base + timedelta(minutes=1), group=0)
        group = self._ingest("g1", base + timedelta(minutes=2), group=1)
        self._evaluate(direct["id"])
        self._evaluate(group["id"])
        self.assertEqual(self.conn.execute("SELECT loop_matched FROM items WHERE id = ?", (group["id"],)).fetchone()[0], 0)
        claim = proactive_store.claim_next_speech(self.conn, now=base + timedelta(minutes=3))
        self.assertEqual(claim["item_id"], direct["id"])
        proactive_store.mark_speech_started(self.conn, claim["item_id"], claim["attempt_id"], now=base + timedelta(minutes=3))
        proactive_store.mark_delivered(self.conn, claim["item_id"], claim["attempt_id"], now=base + timedelta(minutes=4))
        later = self._ingest("d2", base + timedelta(minutes=10))
        self._evaluate(later["id"])
        held = proactive_store.claim_next_speech(self.conn, now=base + timedelta(minutes=20))
        self.assertEqual(held.get("refused_reason"), "nothing_speakable")
        after = proactive_store.claim_next_speech(self.conn, now=base + timedelta(minutes=40))
        self.assertEqual(after.get("item_id"), later["id"])

    def test_forget_reply_names_only_what_was_held(self) -> None:
        held = proactive_store.forget_person_message(name=NAME, texts=2, has_number=True)
        self.assertIn("the texts I was holding", held)
        self.assertNotIn("email", proactive_store.forget_person_message(name=NAME, texts=1, has_number=True))
        self.assertNotIn("still on your phone", held)
        self.assertNotIn("Notifications are matched", held)
        self.assertEqual(
            [item["id"] for item in proactive_store.forget_must_tell(has_number=True)],
            ["notifications_display_name", "texts_on_phone"],
        )
        self.assertEqual(
            [item["id"] for item in proactive_store.forget_must_tell(has_number=False)],
            ["notifications_display_name"],
        )

    def test_stop_pronoun_one_path(self) -> None:
        created = self._create("Watch for Beebo Dev.")
        with self._turn_on("Stop watching for her."):
            closed = loops.close_listed(self.conn, {"action": "close", "intent": "cancelled"})
        self.assertTrue(closed["ok"], closed)
        self.assertEqual(closed["loop_id"], created["loop_id"])
        self.assertEqual(self.conn.execute("SELECT closed_intent FROM loops").fetchone()[0], "cancelled")

    def _stop_by_id(self, message: str) -> None:
        loops.reset_for_tests()
        contact_index.set_people_for_tests([_person()])
        created = self._create("Watch for Beebo Dev.")
        self.assertTrue(created["ok"], created)
        with self._turn_on(message):
            listed = loops.list_loops(self.conn)
            self.assertTrue(listed["ok"], listed)
            closed = loops.close_listed(
                self.conn, {"action": "close", "loop_id": created["loop_id"]}
            )
        self.assertTrue(closed["ok"], message)
        row = self.conn.execute(
            "SELECT status, closed_intent FROM loops WHERE id = ?",
            (created["loop_id"],),
        ).fetchone()
        self.assertEqual(row["status"], "closed", message)
        self.assertEqual(row["closed_intent"], "cancelled", message)

    def test_stop_by_name_and_pronoun_records_cancelled(self) -> None:
        self._stop_by_id("Stop watching for Beebo Dev.")
        self._stop_by_id("Stop watching for her.")

    def test_each_close_path_records_its_reason(self) -> None:
        import phone_ids

        base = datetime.now(timezone.utc).replace(microsecond=0)
        delivered = self._create("Let me know when I hear from Beebo Dev.")
        item = self._ingest("reason-d", base + timedelta(minutes=1))
        self._evaluate(item["id"])
        claim = proactive_store.claim_next_speech(self.conn, now=base + timedelta(minutes=2))
        proactive_store.mark_speech_started(
            self.conn, claim["item_id"], claim["attempt_id"], now=base
        )
        proactive_store.mark_delivered(
            self.conn, claim["item_id"], claim["attempt_id"], now=base
        )
        self.assertEqual(self._reason(delivered["loop_id"]), "delivered")

        contact_index.set_people_for_tests([_person()])
        acked = self._create("Let me know when I hear from Beebo Dev.")
        noted = self._ingest("reason-a", base + timedelta(minutes=3))
        self._evaluate(noted["id"])
        acknowledged = proactive_store.acknowledge(
            self.conn, noted["id"], include_unselected=True, now=base + timedelta(minutes=4)
        )
        self.assertTrue(acknowledged["ok"], acknowledged)
        self.assertEqual(self._reason(acked["loop_id"]), "acknowledged")

        contact_index.set_people_for_tests([_person()])
        expired = self._create("Watch for Beebo Dev.")
        self.conn.execute(
            "UPDATE loops SET expires_at = ? WHERE id = ?",
            ("2020-01-01T00:00:00Z", expired["loop_id"]),
        )
        self.conn.commit()
        proactive_store.purge_retention(self.conn, now=base)
        self.assertEqual(self._reason(expired["loop_id"]), "expired")

        contact_index.set_people_for_tests([_person()])
        forgotten = self._create("Watch for Beebo Dev.")
        forgot = proactive_store.forget_subject(
            self.conn, address_hashes=[phone_ids.hash(NUMBER)]
        )
        self.assertTrue(forgot["ok"], forgot)
        self.assertEqual(self._reason(forgotten["loop_id"]), "forgotten")

    def test_close_by_id_on_his_turn_records_cancelled(self) -> None:
        created = self._create("Watch for Beebo Dev.")
        with self._turn_on("Please close that."):
            listed = loops.list_loops(self.conn)
            self.assertTrue(listed["ok"], listed)
            closed = loops.close_listed(
                self.conn, {"action": "close", "loop_id": created["loop_id"]}
            )
        self.assertTrue(closed["ok"], closed)
        self.assertEqual(self._reason(created["loop_id"]), "cancelled")

    def test_widen_close_says_the_text_watch_now_covers_email(self) -> None:
        text = self._create("Tell me when Beebo Dev texts.")
        self.assertEqual(text["channel"], "text")
        self.assertEqual(text["lifetime"], "once")
        with self._turn_on("Let me know when I hear from Beebo Dev."):
            listed = loops.list_loops(self.conn)
            self.assertTrue(listed["ok"], listed)
            early = loops.close_listed(
                self.conn, {"action": "close", "loop_id": text["loop_id"]}
            )
            self.assertEqual(early.get("refused_reason"), "not_covered")
            widened = loops.create_loop(
                self.conn,
                {"action": "create", "intent": "person", "person": NAME, "channel": "both"},
            )
            self.assertTrue(widened["ok"], widened)
            self.assertEqual(widened["channel"], "both")
            self.assertEqual(widened["lifetime"], "once")
            listed = loops.list_loops(self.conn)
            self.assertTrue(listed["ok"], listed)
            closed = loops.close_listed(
                self.conn, {"action": "close", "loop_id": text["loop_id"]}
            )
        self.assertTrue(closed["ok"], closed)
        self.assertIn("I've widened your text watch to cover email.", closed.get("say") or "")
        self.assertEqual(self._reason(text["loop_id"]), "cancelled")
        still = self.conn.execute(
            "SELECT status FROM loops WHERE id = ?",
            (widened["loop_id"],),
        ).fetchone()
        self.assertEqual(still["status"], "open")

    def test_close_refuses_a_watch_the_new_one_does_not_cover(self) -> None:
        text = self._create("Tell me when Beebo Dev texts.")
        with self._turn_on("Tell me when Beebo Dev emails."):
            email = loops.create_loop(
                self.conn,
                {"action": "create", "intent": "person", "person": NAME, "channel": "email"},
            )
            self.assertTrue(email["ok"], email)
            self.assertEqual(email["channel"], "email")
            loops.list_loops(self.conn)
            closed = loops.close_listed(
                self.conn, {"action": "close", "loop_id": text["loop_id"]}
            )
        self.assertEqual(closed.get("refused_reason"), "not_covered")
        row = self.conn.execute(
            "SELECT status, closed_intent FROM loops WHERE id = ?",
            (text["loop_id"],),
        ).fetchone()
        self.assertEqual(row["status"], "open")
        self.assertIsNone(row["closed_intent"])
        standing = self._create("Let me know every time Beebo Dev texts.")
        self.assertEqual(standing["lifetime"], "standing")
        with self._turn_on("Let me know when I hear from Beebo Dev."):
            once = loops.create_loop(
                self.conn,
                {"action": "create", "intent": "person", "person": NAME, "channel": "both"},
            )
            self.assertEqual(once["lifetime"], "once")
            loops.list_loops(self.conn)
            lifetime = loops.close_listed(
                self.conn, {"action": "close", "loop_id": standing["loop_id"]}
            )
        self.assertEqual(lifetime.get("refused_reason"), "not_covered")
        self.assertEqual(
            self.conn.execute(
                "SELECT status FROM loops WHERE id = ?",
                (standing["loop_id"],),
            ).fetchone()["status"],
            "open",
        )

    def _reason(self, loop_id: str) -> str:
        return self.conn.execute(
            "SELECT closed_intent FROM loops WHERE id = ?",
            (loop_id,),
        ).fetchone()[0]

    def test_notification_never_matches(self) -> None:
        created = self._create("Let me know when I hear from Beebo Dev.")
        self.assertTrue(created["ok"], created)
        note = self._ingest(
            "n1",
            NOW + timedelta(minutes=1),
            kind="notif",
            sender="",
            package="com.instagram.android",
            notification_key="n1",
        )
        self.assertEqual(note.get("result"), "stored", note)
        self.conn.execute(
            "UPDATE items SET sender_display_name = ? WHERE id = ?",
            (NAME, note["id"]),
        )
        self.conn.commit()
        self._evaluate(note["id"])
        self.assertEqual(self.conn.execute("SELECT loop_matched FROM items WHERE id = ?", (note["id"],)).fetchone()[0], 0)

    def _number_watch(self, message: str = "Watch 15555550100."):
        payload = {"action": "create", "intent": "number", "number": NUMBER}
        with self._turn_on(message):
            return loops.create_loop(self.conn, payload)

    def test_widen_yes_creates_the_person_and_a_lapse_or_other_session_does_not(self) -> None:
        clock = {"t": 1000.0}
        loops.set_confirm_clock_for_tests(lambda: clock["t"])
        created = self._number_watch()
        self.assertTrue(created["ok"], created)
        self.assertIn(NAME, created["say"])
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM loops").fetchone()[0], 1)
        with self._turn_on("Yes", session_id="sess-other"):
            elsewhere = loops.create_loop(self.conn, {"action": "create", "intent": "number", "number": NUMBER})
        self.assertNotEqual(elsewhere.get("intent"), "person")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM loops WHERE intent = 'person'").fetchone()[0], 0)
        clock["t"] += loops.CONFIRM_TTL_SECONDS + 1
        with self._turn_on("Yes"):
            lapsed = loops.create_loop(self.conn, {"action": "create", "intent": "person", "person": NAME})
        self.assertNotEqual(lapsed.get("intent"), "person")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM loops WHERE intent = 'person'").fetchone()[0], 0)
        clock["t"] = 1000.0
        again = self._number_watch("Watch 15555550100 again.")
        self.assertIn(NAME, again["say"])
        with self._turn_on("Yes"):
            widened = loops.create_loop(self.conn, {"action": "create", "intent": "number", "number": NUMBER})
        self.assertTrue(widened["ok"], widened)
        self.assertEqual(widened.get("intent"), "person")
        self.assertEqual(widened.get("display_name"), NAME)

    def test_burst_already_waiting_joins_and_a_released_claim_is_one_line(self) -> None:
        created = self._create("Let me know every time Beebo Dev texts.")
        self.assertTrue(created["ok"], created)
        base = datetime.now(timezone.utc).replace(microsecond=0)
        first = self._ingest("b1", base + timedelta(minutes=1))
        waiting = self._ingest("b2", base + timedelta(minutes=2))
        self._evaluate(first["id"])
        self._evaluate(waiting["id"])
        claim = proactive_store.claim_next_speech(self.conn, now=base + timedelta(minutes=3))
        self.assertEqual(claim["item_id"], first["id"])
        released = proactive_store.release_speech_claim(
            self.conn, claim["item_id"], claim["attempt_id"], now=base + timedelta(minutes=3)
        )
        self.assertTrue(released["ok"], released)
        again = proactive_store.claim_next_speech(self.conn, now=base + timedelta(minutes=4))
        self.assertEqual(again["item_id"], first["id"])
        proactive_store.mark_speech_started(self.conn, again["item_id"], again["attempt_id"], now=base + timedelta(minutes=4))
        delivered = proactive_store.mark_delivered(
            self.conn, again["item_id"], again["attempt_id"], now=base + timedelta(minutes=5)
        )
        self.assertTrue(delivered["ok"], delivered)
        later = proactive_store.claim_next_speech(self.conn, now=base + timedelta(hours=2))
        self.assertEqual(later.get("refused_reason"), "nothing_speakable")
        self.assertEqual(self.conn.execute("SELECT loop_matched FROM items WHERE id = ?", (waiting["id"],)).fetchone()[0], 1)

    def test_stop_without_a_person_and_two_people(self) -> None:
        with self._turn_on("Stop watching for her."):
            missing = loops.close_listed(self.conn, {"action": "close", "intent": "cancelled"})
        self.assertEqual(missing.get("refused_reason"), "no_reference")
        loops.note_session_person("sess-watch", "c_beebo", NAME, "")
        loops.note_session_person("sess-watch", "c_other", "Other Person", "")
        with self._turn_on("Stop watching for her."):
            which = loops.close_listed(self.conn, {"action": "close", "intent": "cancelled"})
        self.assertEqual(which.get("refused_reason"), "which")

    def test_group_lines_name_the_person_and_not_a_group(self) -> None:
        for line in speech.TEXT_GROUP:
            self.assertIn("{name}", line)
            self.assertNotIn("{group", line)
            self.assertIn("group", line)

    def test_phrase_sets_match_the_client(self) -> None:
        client = (
            Path(__file__).resolve().parents[3] / "windows-client" / "Zola.Client" / "Speech" / "SpeechPhrases.cs"
        ).read_text(encoding="utf-8")
        for name, lines in (
            ("TextNamed", speech.TEXT_NAMED),
            ("TextUnnamed", speech.TEXT_UNNAMED),
            ("TextNumber", speech.TEXT_NUMBER),
            ("TextGroup", speech.TEXT_GROUP),
            ("EmailPerson", speech.EMAIL_PERSON),
        ):
            for line in lines:
                self.assertIn('"' + line + '"', client, name)
                self.assertTrue(
                    line.startswith("Brian,") or line.startswith("Heads up,") or line.startswith("Quick one:"),
                    line,
                )


if __name__ == "__main__":
    unittest.main()
