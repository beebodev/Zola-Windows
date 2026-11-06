"""P10-WATCH approved tests. Synthetic contact only. Real entry points."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

import address_hash
import contact_index
import loops
import origin
import phone_ids
import proactive_store
import speech
import surface
import taint
import turn_context
import watcher
import log as wslog

NAME = "Beebo Dev"
NUMBER = "+15555550100"
OTHER = "+15555550101"
EMAIL = "beebo@example.com"


def _person(numbers=(NUMBER,), emails=(EMAIL,), handle="c_beebo", name=NAME):
    return contact_index.Person(
        handle=handle,
        display_name=name,
        numbers=tuple(numbers),
        number_hashes=frozenset(phone_ids.hash(number) for number in numbers),
        emails=tuple(emails),
        email_hashes=frozenset(address_hash.address_hash(email) for email in emails),
    )


class ApprovedTests(unittest.TestCase):
    def setUp(self) -> None:
        self._dir = tempfile.TemporaryDirectory()
        self.home = Path(self._dir.name)
        self.path = self.home / "proactive.db"
        self._old_home = os.environ.get("HERMES_HOME")
        os.environ["HERMES_HOME"] = str(self.home)
        proactive_store.set_db_path_for_tests(self.path)
        proactive_store.set_ticket_override_for_tests(True)
        self.conn = proactive_store.connect(self.path, retry=False)
        contact_index.reset_for_tests()
        contact_index.set_people_for_tests([_person()])
        loops.reset_for_tests()
        watcher.set_evaluate_fault_for_tests(None)
        surface.reset_for_tests()
        self._turn = 0

    def tearDown(self) -> None:
        watcher.set_evaluate_fault_for_tests(None)
        surface.reset_for_tests()
        wslog.reset_log_handler_for_tests()
        self.conn.close()
        proactive_store.set_db_path_for_tests(None)
        proactive_store.set_ticket_override_for_tests(None)
        contact_index.reset_for_tests()
        loops.reset_for_tests()
        if self._old_home is None:
            os.environ.pop("HERMES_HOME", None)
        else:
            os.environ["HERMES_HOME"] = self._old_home
        self._dir.cleanup()

    def _turn_on(self, message: str, session_id: str = "sess-watch"):
        self._turn += 1
        turn_id = "turn-%s" % self._turn
        turn_context.record_pre_llm_call(
            turn_id=turn_id, session_id=session_id, platform="tui", user_message=message
        )
        origin.grant_turn_for_tests(turn_id, message)
        return mock.patch.object(turn_context, "current_turn_id_from_context", return_value=turn_id)

    def _create(self, message: str, **args):
        payload = {"action": "create", "intent": "person", "person": NAME}
        payload.update(args)
        with self._turn_on(message):
            return loops.create_loop(self.conn, payload)

    def _ingest(self, provider_id, when, *, kind="sms", sender=NUMBER, group=0, body="synthetic", package="", key=""):
        return proactive_store.ingest_phone_item(
            self.conn,
            kind=kind,
            device_id="device-test",
            revision=1,
            completeness="complete",
            received_at=when,
            provider_id=provider_id,
            package=package,
            notification_key=key,
            newest_message_timestamp="1000" if kind == "notif" else "",
            sender_raw=sender,
            sender_display_name=NAME if kind == "notif" else "",
            body=body,
            is_group=group,
            now=when,
        )

    def _predicate(self):
        row = self.conn.execute("SELECT predicate_json FROM loops ORDER BY created_at").fetchall()
        return [json.loads(item["predicate_json"]) for item in row]

    def _evaluate(self, item_id, when):
        row = self.conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
        keys = set(row.keys())
        view = {
            "source": row["source"],
            "message_id": row["message_id"],
            "thread_id": row["thread_id"],
            "sender_address_hash": row["sender_address_hash"],
            "detected_at": row["detected_at"],
            "internal_date": row["detected_at"] if "internal_date" not in keys else row["internal_date"],
            "is_group": row["is_group"],
        }
        for loop in proactive_store.list_open_loop_predicates(self.conn)["loops"]:
            if loops.evaluate(loop["predicate"], view):
                proactive_store.bind_open_loop_match(self.conn, loop["id"], item_id, now=when)

    def test_person_watch_text_only(self) -> None:
        created = self._create("Let me know when Beebo Dev texts.")
        self.assertEqual(created.get("channel"), "text", created)
        self.assertEqual(self._predicate()[-1]["channel"], "text")

    def test_person_watch_email_only(self) -> None:
        created = self._create("Let me know when Beebo Dev emails me.")
        self.assertEqual(created.get("channel"), "email", created)

    def test_person_watch_unnamed_channel_both(self) -> None:
        created = self._create("Let me know when I hear from Beebo Dev.")
        self.assertEqual(created.get("channel"), "both", created)

    def test_person_watch_several_numbers_and_emails(self) -> None:
        contact_index.set_people_for_tests([_person(numbers=(NUMBER, OTHER))])
        created = self._create("Let me know when I hear from Beebo Dev.")
        self.assertTrue(created["ok"], created)
        self.assertEqual(created.get("channel"), "both")
        hashes = self._predicate()[-1]["args"][0]["address_hashes"]
        self.assertEqual(len(hashes), 3)

    def test_number_watch(self) -> None:
        with self._turn_on("Watch 15555550100."):
            created = loops.create_loop(self.conn, {"action": "create", "intent": "number", "number": NUMBER})
        self.assertTrue(created["ok"], created)
        self.assertEqual(created["intent"], "number")
        self.assertIn(NAME, created["say"])
        self.assertNotIn(NUMBER, created["say"])

    def test_ten_digit_number_is_the_spoken_number(self) -> None:
        contact_index.set_people_for_tests([])
        with self._turn_on("Let me know when I hear from 5555550100."):
            created = loops.create_loop(
                self.conn,
                {"action": "create", "intent": "number", "number": "5555550100", "channel": "text"},
            )
        self.assertTrue(created.get("ok"), created)
        self.assertEqual(created.get("intent"), "number")
        self.assertNotIn("5555550100", created.get("say") or "")
        self.assertNotIn("I won't say the digits", created.get("say") or "")
        self.assertIn("may repeat a number he said", loops._DESCRIPTION)
        for line in speech.TEXT_NUMBER:
            self.assertFalse(any(ch.isdigit() for ch in line), line)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM loops WHERE intent = 'number'").fetchone()[0], 1)

    def test_number_watch_on_a_contact_does_not_widen(self) -> None:
        contact_index.set_people_for_tests([_person(numbers=(NUMBER, OTHER))])
        with self._turn_on("Watch 15555550100."):
            created = loops.create_loop(self.conn, {"action": "create", "intent": "number", "number": NUMBER})
        self.assertIn(NAME, created["say"])
        base = datetime.now(timezone.utc).replace(microsecond=0)
        other = self._ingest("other", base + timedelta(minutes=1), sender=OTHER)
        mail = proactive_store.insert_item(
            self.conn, source="gmail", message_id="other-mail", thread_id="th-other",
            sender_address=EMAIL, subject="synth", now=base + timedelta(minutes=1),
        )
        self._evaluate(other["id"], base)
        self._evaluate(mail["id"], base)
        matched = self.conn.execute("SELECT COALESCE(SUM(loop_matched), 0) FROM items").fetchone()[0]
        self.assertEqual(matched, 0)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM loops WHERE intent = 'person'").fetchone()[0], 0)

    def test_widen_only_after_yes(self) -> None:
        contact_index.set_people_for_tests([_person(numbers=(NUMBER, OTHER))])
        with self._turn_on("Watch 15555550100."):
            loops.create_loop(self.conn, {"action": "create", "intent": "number", "number": NUMBER})
        with self._turn_on("Yes"):
            widened = loops.create_loop(self.conn, {"action": "create", "intent": "number", "number": NUMBER})
        self.assertEqual(widened.get("intent"), "person")
        base = datetime.now(timezone.utc).replace(microsecond=0)
        other = self._ingest("widened", base + timedelta(minutes=1), sender=OTHER)
        self._evaluate(other["id"], base)
        self.assertEqual(self.conn.execute("SELECT loop_matched FROM items WHERE id = ?", (other["id"],)).fetchone()[0], 1)

    def test_name_missing_from_contacts_refused(self) -> None:
        refused = self._create("Watch for Nobody Here.", person="Nobody Here")
        self.assertEqual(refused.get("refused_reason"), "not_in_contacts")
        self.assertIn("tell me the number", refused.get("say") or "")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM loops").fetchone()[0], 0)

    def test_shared_number_asks(self) -> None:
        contact_index.set_people_for_tests([
            _person(handle="c_one", name="Ada One"),
            _person(handle="c_two", name="Ada Two"),
        ])
        with self._turn_on("Watch 15555550100."):
            refused = loops.create_loop(self.conn, {"action": "create", "intent": "number", "number": NUMBER})
        self.assertEqual(refused.get("refused_reason"), "shared_number")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM loops").fetchone()[0], 0)

    def test_name_only_in_text_body_refused(self) -> None:
        refused = self._create("Let me know when I hear from someone.", person=NAME)
        self.assertEqual(refused.get("refused_reason"), "name_not_in_message")

    def test_number_only_in_text_body_refused(self) -> None:
        with self._turn_on("Watch for a text."):
            refused = loops.create_loop(self.conn, {"action": "create", "intent": "number", "number": NUMBER})
        self.assertEqual(refused.get("refused_reason"), "number_not_in_message")

    def test_channel_argument_disagrees(self) -> None:
        refused = self._create("Let me know when Beebo Dev texts.", channel="email")
        self.assertEqual(refused.get("refused_reason"), "channel_disagrees")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM loops").fetchone()[0], 0)

    def test_keep_an_eye_on_asks(self) -> None:
        asked = self._create("Keep an eye on Beebo Dev.")
        self.assertEqual(asked.get("refused_reason"), "confirm_needed")
        self.assertIn("Every time", asked.get("say") or "")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM loops").fetchone()[0], 0)

    def test_fuzzy_token_lapses(self) -> None:
        clock = {"t": 1000.0}
        loops.set_confirm_clock_for_tests(lambda: clock["t"])
        asked = self._create("Watch for Bebo Dev.", person="Bebo Dev")
        self.assertEqual(asked.get("refused_reason"), "confirm_needed")
        clock["t"] += 121
        with self._turn_on("Yes"):
            lapsed = loops.create_loop(self.conn, {"action": "create", "intent": "person", "person": "Bebo Dev"})
        self.assertNotEqual(lapsed.get("intent"), "person")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM loops").fetchone()[0], 0)

    def test_no_after_did_you_mean_changes_nothing(self) -> None:
        asked = self._create("Watch for Bebo Dev.", person="Bebo Dev")
        self.assertIn("Did you mean", asked.get("say") or "")
        with self._turn_on("No."):
            answer = loops.create_loop(self.conn, {"action": "create", "intent": "person", "person": "Bebo Dev"})
        self.assertEqual(answer.get("say"), "All right. I didn't change anything.")
        self.assertFalse(answer.get("created", True))
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM loops").fetchone()[0], 0)

    def test_confirmation_answer_must_call_the_tool(self) -> None:
        text = " ".join(loops._DESCRIPTION.split()).casefold()
        self.assertNotIn("that is your whole reply", text)
        self.assertIn("a yes or a no after you asked him to confirm a name is another call to this tool", text)

    def test_unrelated_turn_drops_an_open_confirmation(self) -> None:
        asked = self._create("Watch for Bebo Dev.", person="Bebo Dev")
        self.assertEqual(asked.get("refused_reason"), "confirm_needed")
        with self._turn_on("What time is it?"):
            pass
        with self._turn_on("Yes"):
            later = loops.create_loop(
                self.conn, {"action": "create", "intent": "person", "person": "Bebo Dev"}
            )
        self.assertNotEqual(later.get("intent"), "person")
        self.assertFalse(later.get("loop_id"))
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM loops").fetchone()[0], 0)

    def test_fuzzy_token_other_session(self) -> None:
        self._create("Watch for Bebo Dev.", person="Bebo Dev")
        with self._turn_on("Yes", session_id="sess-other"):
            elsewhere = loops.create_loop(self.conn, {"action": "create", "intent": "person", "person": "Bebo Dev"})
        self.assertNotEqual(elsewhere.get("display_name"), NAME)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM loops").fetchone()[0], 0)

    def test_fuzzy_token_other_action(self) -> None:
        self._create("Watch for Bebo Dev.", person="Bebo Dev")
        with self._turn_on("Yes"):
            other = loops.create_loop(self.conn, {"action": "create", "intent": "reply", "handle": "h"})
        self.assertEqual(other.get("refused_reason"), "lapsed")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM loops").fetchone()[0], 0)

    def test_fuzzy_token_text_body_yes(self) -> None:
        self._create("Watch for Bebo Dev.", person="Bebo Dev")
        when = datetime.now(timezone.utc)
        self._ingest("body-yes", when, body="yes please")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM loops").fetchone()[0], 0)
        with self._turn_on("Yes"):
            created = loops.create_loop(self.conn, {"action": "create", "intent": "person", "person": "Bebo Dev"})
        self.assertEqual(created.get("display_name"), NAME)

    def test_confirmation_turn_without_name(self) -> None:
        self._create("Watch for Bebo Dev.", person="Bebo Dev")
        with self._turn_on("Yes"):
            created = loops.create_loop(self.conn, {"action": "create", "intent": "person", "person": "Bebo Dev"})
        self.assertEqual(created.get("display_name"), NAME)
        self.assertNotIn("Bebo", created.get("say") or "")

    def test_confirmation_refuses_a_changed_proposal(self) -> None:
        self._create("Watch for Bebo Dev.", person="Bebo Dev")
        with self._turn_on("Yes, every time"):
            refused = loops.create_loop(self.conn, {"action": "create", "intent": "person", "person": "Bebo Dev"})
        self.assertEqual(refused.get("refused_reason"), "confirm_stale")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM loops").fetchone()[0], 0)
        loops.reset_for_tests()
        self._create("Let me know when Bebo Dev texts.", person="Bebo Dev")
        with self._turn_on("Yes, when he emails me"):
            channel = loops.create_loop(self.conn, {"action": "create", "intent": "person", "person": "Bebo Dev"})
        self.assertEqual(channel.get("refused_reason"), "confirm_stale")
        loops.reset_for_tests()
        self._create("Let me know every time Bebo Dev texts.", person="Bebo Dev")
        with self._turn_on("Yes, including group threads"):
            groups = loops.create_loop(self.conn, {"action": "create", "intent": "person", "person": "Bebo Dev"})
        self.assertEqual(groups.get("refused_reason"), "confirm_stale")
        loops.reset_for_tests()
        self._create("Watch for Bebo Dev.", person="Bebo Dev")
        contact_index.set_people_for_tests([_person(numbers=(OTHER,))])
        with self._turn_on("Yes"):
            changed = loops.create_loop(self.conn, {"action": "create", "intent": "person", "person": "Bebo Dev"})
        self.assertEqual(changed.get("refused_reason"), "confirm_stale")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM loops").fetchone()[0], 0)

    def test_untrusted_argument(self) -> None:
        with self._turn_on("Let me know when Beebo Dev texts."):
            refused = loops.create_loop(
                self.conn, {"action": "create", "intent": "person", "person": NAME, "email": EMAIL}
            )
        self.assertEqual(refused.get("refused_reason"), "untrusted_argument")

    def test_reply_and_calendar_predicates_unchanged(self) -> None:
        reply = {
            "op": "all",
            "args": [
                {"op": "gmail_thread", "thread_id": "thread-good"},
                {"op": "sender_is", "address_hash": "abc"},
                {"op": "after", "at": "2020-01-01T00:00:00Z"},
            ],
        }
        calendar = {
            "op": "all",
            "args": [
                {"op": "calendar_event", "event_id": "ev-1"},
                {"op": "calendar_status_differs", "from_status": "confirmed"},
            ],
        }
        self.assertTrue(loops.evaluate(reply, {
            "source": "gmail", "thread_id": "thread-good", "sender_address_hash": "abc",
            "internal_date": "2026-06-01T00:00:00Z",
        }))
        self.assertFalse(loops.evaluate(reply, {
            "source": "gmail", "thread_id": "thread-other", "sender_address_hash": "abc",
            "internal_date": "2026-06-01T00:00:00Z",
        }))
        self.assertTrue(loops.evaluate(calendar, {
            "source": "calendar", "event_id": "ev-1", "calendar_status": "cancelled",
        }))

    def test_phone_row_matches_on_detected_at(self) -> None:
        created = self._create("Let me know when I hear from Beebo Dev.")
        self.assertTrue(created["ok"], created)
        base = datetime.now(timezone.utc).replace(microsecond=0)
        early = self._ingest("early", base - timedelta(days=2))
        late = self._ingest("late", base + timedelta(minutes=1))
        self._evaluate(early["id"], base)
        self._evaluate(late["id"], base)
        matched = {
            row["id"]: row["loop_matched"]
            for row in self.conn.execute("SELECT id, loop_matched FROM items")
        }
        self.assertEqual(matched[early["id"]], 0)
        self.assertEqual(matched[late["id"]], 1)

    def test_notification_never_matches_through_ingest(self) -> None:
        self._create("Let me know when I hear from Beebo Dev.")
        when = datetime.now(timezone.utc)
        note = self._ingest("n1", when, kind="notif", sender="", package="com.instagram.android", key="n1")
        self.assertEqual(note.get("result"), "stored", note)
        self._evaluate(note["id"], when)
        self.assertEqual(self.conn.execute("SELECT loop_matched FROM items").fetchone()[0], 0)

    def test_notification_never_claimed(self) -> None:
        when = datetime.now(timezone.utc)
        note = self._ingest("n2", when, kind="notif", sender="", package="com.instagram.android", key="n2")
        proactive_store.mark_loop_eligible(self.conn, note["id"], now=when)
        proactive_store.set_loop_matched(self.conn, note["id"], now=when)
        claimed = proactive_store.claim_speech(self.conn, note["id"], now=when)
        self.assertEqual(claimed.get("refused_reason"), "phone_deferred")

    def test_unwatched_text_never_claimed(self) -> None:
        when = datetime.now(timezone.utc)
        item = self._ingest("free", when)
        proactive_store.mark_loop_eligible(self.conn, item["id"], now=when)
        proactive_store.set_loop_matched(self.conn, item["id"], now=when)
        claimed = proactive_store.claim_next_speech(self.conn, now=when)
        self.assertNotEqual(claimed.get("item_id"), item["id"])

    def test_one_shot_stays_open_through_quiet_hours_release_and_uncertain(self) -> None:
        self._create("Let me know when I hear from Beebo Dev.")
        base = datetime.now(timezone.utc).replace(microsecond=0)
        item = self._ingest("q1", base + timedelta(minutes=1))
        self._evaluate(item["id"], base)
        claim = proactive_store.claim_next_speech(self.conn, now=base + timedelta(minutes=2))
        self.assertEqual(claim.get("item_id"), item["id"])
        proactive_store.release_speech_claim(self.conn, claim["item_id"], claim["attempt_id"], now=base + timedelta(minutes=2))
        self.assertEqual(self.conn.execute("SELECT status FROM loops").fetchone()[0], "open")
        again = proactive_store.claim_next_speech(self.conn, now=base + timedelta(minutes=3))
        proactive_store.mark_speech_started(self.conn, again["item_id"], again["attempt_id"], now=base + timedelta(minutes=3))
        uncertain = proactive_store.mark_delivery_uncertain(self.conn, again["item_id"], again["attempt_id"], now=base + timedelta(minutes=3))
        self.assertTrue(uncertain["ok"], uncertain)
        self.assertEqual(self.conn.execute("SELECT status FROM loops").fetchone()[0], "open")
        self.assertNotEqual(self.conn.execute("SELECT delivery FROM items").fetchone()[0], "delivered")

    def test_one_shot_closes_delivered_acknowledged_cancelled_expired(self) -> None:
        created = self._create("Let me know when I hear from Beebo Dev.")
        base = datetime.now(timezone.utc).replace(microsecond=0)
        item = self._ingest("c1", base + timedelta(minutes=1))
        self._evaluate(item["id"], base)
        claim = proactive_store.claim_next_speech(self.conn, now=base + timedelta(minutes=2))
        proactive_store.mark_speech_started(self.conn, claim["item_id"], claim["attempt_id"], now=base)
        proactive_store.mark_delivered(self.conn, claim["item_id"], claim["attempt_id"], now=base)
        self.assertEqual(self.conn.execute("SELECT closed_intent FROM loops").fetchone()[0], "delivered")

        contact_index.set_people_for_tests([_person()])
        asked = self._create("Watch for Beebo Dev.")
        with self._turn_on("Stop watching for her."):
            loops.close_listed(self.conn, {"action": "close", "intent": "cancelled"})
        self.assertEqual(
            self.conn.execute("SELECT closed_intent FROM loops WHERE id = ?", (asked["loop_id"],)).fetchone()[0],
            "cancelled",
        )

        third = self._create("Let me know when I hear from Beebo Dev.")
        self.conn.execute(
            "UPDATE loops SET expires_at = ? WHERE id = ?",
            ("2020-01-01T00:00:00Z", third["loop_id"]),
        )
        self.conn.commit()
        proactive_store.purge_retention(self.conn, now=base)
        self.assertEqual(
            self.conn.execute("SELECT closed_intent FROM loops WHERE id = ?", (third["loop_id"],)).fetchone()[0],
            "expired",
        )

        contact_index.set_people_for_tests([_person()])
        acked = self._create("Let me know when I hear from Beebo Dev.")
        acknowledged = self._ingest("ack", base + timedelta(minutes=4))
        self._evaluate(acknowledged["id"], base)
        noted = proactive_store.acknowledge(
            self.conn, acknowledged["id"], include_unselected=True, now=base + timedelta(minutes=4)
        )
        self.assertTrue(noted["ok"], noted)
        self.assertEqual(
            self.conn.execute("SELECT closed_intent FROM loops WHERE id = ?", (acked["loop_id"],)).fetchone()[0],
            "acknowledged",
        )

    def test_burst_three_texts_one_claim(self) -> None:
        self._create("Let me know every time Beebo Dev texts.")
        base = datetime.now(timezone.utc).replace(microsecond=0)
        ids = []
        for index, minutes in enumerate((1, 2, 3)):
            item = self._ingest("b%s" % index, base + timedelta(minutes=minutes))
            self._evaluate(item["id"], base)
            ids.append(item["id"])
        claim = proactive_store.claim_next_speech(self.conn, now=base + timedelta(minutes=4))
        self.assertEqual(claim.get("item_id"), ids[0])
        self.assertEqual(
            proactive_store.claim_next_speech(self.conn, now=base + timedelta(minutes=4)).get("refused_reason"),
            "nothing_speakable",
        )

    def test_burst_window_boundary(self) -> None:
        self._create("Let me know every time Beebo Dev texts.")
        base = datetime.now(timezone.utc).replace(microsecond=0)
        anchor = self._ingest("edge", base + timedelta(minutes=1))
        inside = self._ingest("in", base + timedelta(minutes=1, seconds=180))
        outside = self._ingest("out", base + timedelta(minutes=1, seconds=181))
        for item in (anchor, inside, outside):
            self._evaluate(item["id"], base)
        claim = proactive_store.claim_next_speech(self.conn, now=base + timedelta(minutes=2))
        proactive_store.mark_speech_started(self.conn, claim["item_id"], claim["attempt_id"], now=base + timedelta(minutes=2))
        proactive_store.mark_delivered(self.conn, claim["item_id"], claim["attempt_id"], now=base + timedelta(minutes=2))
        held = proactive_store.claim_next_speech(self.conn, now=base + timedelta(minutes=3))
        self.assertEqual(held.get("refused_reason"), "nothing_speakable")
        later = proactive_store.claim_next_speech(self.conn, now=base + timedelta(minutes=40))
        self.assertEqual(later.get("item_id"), outside["id"])
        self.assertNotEqual(later.get("item_id"), inside["id"])

    def test_text_and_email_one_line_both_pending(self) -> None:
        self._create("Let me know when I hear from Beebo Dev.")
        base = datetime.now(timezone.utc).replace(microsecond=0)
        text = self._ingest("both-text", base + timedelta(minutes=1))
        mail = proactive_store.insert_item(
            self.conn,
            source="gmail",
            message_id="both-mail",
            thread_id="th-both",
            sender_address=EMAIL,
            subject="synth",
            now=base + timedelta(minutes=1),
        )
        self.assertTrue(mail["ok"], mail)
        self._evaluate(text["id"], base)
        self._evaluate(mail["id"], base)
        claim = proactive_store.claim_next_speech(self.conn, now=base + timedelta(minutes=2))
        self.assertTrue(claim.get("ok"), claim)
        other = proactive_store.claim_next_speech(self.conn, now=base + timedelta(minutes=2))
        self.assertEqual(other.get("refused_reason"), "nothing_speakable")
        deliveries = {
            row["id"]: row["delivery"]
            for row in self.conn.execute("SELECT id, delivery FROM items")
        }
        self.assertNotEqual(deliveries[text["id"]], "delivered")
        self.assertNotEqual(deliveries[mail["id"]], "delivered")
        self.assertIsNone(self.conn.execute("SELECT acknowledged_at FROM items WHERE acknowledged_at IS NOT NULL").fetchone())

    def test_overlapping_watches_one_claim(self) -> None:
        self._create("Let me know when Beebo Dev texts.")
        with self._turn_on("Watch 15555550100."):
            loops.create_loop(self.conn, {"action": "create", "intent": "number", "number": NUMBER})
        base = datetime.now(timezone.utc).replace(microsecond=0)
        item = self._ingest("over", base + timedelta(minutes=1))
        self._evaluate(item["id"], base)
        claim = proactive_store.claim_next_speech(self.conn, now=base + timedelta(minutes=2))
        self.assertEqual(claim.get("item_id"), item["id"])
        matched = self.conn.execute("SELECT COUNT(*) FROM loops WHERE matched_at IS NOT NULL").fetchone()[0]
        self.assertEqual(matched, 2)
        self.assertEqual(
            proactive_store.claim_next_speech(self.conn, now=base + timedelta(minutes=2)).get("refused_reason"),
            "nothing_speakable",
        )

    def test_delivered_text_does_not_close_a_reply_watch(self) -> None:
        self._create("Let me know when Beebo Dev texts.")
        reply = proactive_store.insert_loop(
            self.conn,
            intent="reply",
            predicate={"op": "sender_is", "address_hash": "reply-hash"},
            session_id="sess-watch",
            sender_display_name="Other",
        )
        base = datetime.now(timezone.utc).replace(microsecond=0)
        item = self._ingest("solo", base + timedelta(minutes=1))
        self._evaluate(item["id"], base)
        claim = proactive_store.claim_next_speech(self.conn, now=base + timedelta(minutes=2))
        proactive_store.mark_speech_started(self.conn, claim["item_id"], claim["attempt_id"], now=base)
        proactive_store.mark_delivered(self.conn, claim["item_id"], claim["attempt_id"], now=base)
        row = self.conn.execute("SELECT status FROM loops WHERE id = ?", (reply["id"],)).fetchone()
        self.assertEqual(row["status"], "open")

    def test_standing_gap_one_line_not_one_per_half_hour(self) -> None:
        self._create("Let me know every time Beebo Dev texts.")
        base = datetime.now(timezone.utc).replace(microsecond=0)
        first = self._ingest("g0", base + timedelta(minutes=1))
        self._evaluate(first["id"], base)
        claim = proactive_store.claim_next_speech(self.conn, now=base + timedelta(minutes=2))
        proactive_store.mark_speech_started(self.conn, claim["item_id"], claim["attempt_id"], now=base)
        proactive_store.mark_delivered(self.conn, claim["item_id"], claim["attempt_id"], now=base + timedelta(minutes=2))
        held_ids = []
        for index, minutes in enumerate((10, 20)):
            item = self._ingest("g%s" % (index + 1), base + timedelta(minutes=minutes))
            self._evaluate(item["id"], base)
            held_ids.append(item["id"])
        self.assertEqual(
            proactive_store.claim_next_speech(self.conn, now=base + timedelta(minutes=25)).get("refused_reason"),
            "nothing_speakable",
        )
        after = proactive_store.claim_next_speech(self.conn, now=base + timedelta(minutes=40))
        self.assertIn(after.get("item_id"), held_ids)
        proactive_store.mark_speech_started(self.conn, after["item_id"], after["attempt_id"], now=base + timedelta(minutes=40))
        proactive_store.mark_delivered(self.conn, after["item_id"], after["attempt_id"], now=base + timedelta(minutes=40))
        self.assertEqual(
            proactive_store.claim_next_speech(self.conn, now=base + timedelta(minutes=41)).get("refused_reason"),
            "nothing_speakable",
        )

    def test_quiet_hours_unchanged(self) -> None:
        self._create("Let me know when I hear from Beebo Dev.")
        night = (datetime.now(timezone.utc) - timedelta(days=1)).replace(hour=23, minute=10, second=0, microsecond=0)
        predicate = json.loads(self.conn.execute("SELECT predicate_json FROM loops").fetchone()[0])
        for child in predicate["args"]:
            if child.get("op") == "after":
                child["at"] = "2020-01-01T00:00:00Z"
        saved = proactive_store.replace_loop_predicate(
            self.conn, self.conn.execute("SELECT id FROM loops").fetchone()[0], predicate
        )
        self.assertTrue(saved["ok"], saved)
        item = self._ingest("night", night)
        self._evaluate(item["id"], night)
        claim = proactive_store.claim_next_speech(self.conn, now=night + timedelta(minutes=20))
        self.assertEqual(claim.get("item_id"), item["id"], claim)
        self.assertNotEqual(claim.get("refused_reason"), "quiet_hours")

    def test_text_phrases_sms_mms_both_sides(self) -> None:
        self.assertTrue(speech.TEXT_NAMED)
        self.assertTrue(all(line.startswith(("Brian,", "Heads up,", "Quick one:")) for line in speech.TEXT_NAMED))

    def test_forget_race_watcher(self) -> None:
        created = self._create("Let me know when Beebo Dev emails me.")
        base = datetime.now(timezone.utc).replace(microsecond=0)
        mail = proactive_store.insert_item(
            self.conn, source="gmail", message_id="race-mail", thread_id="th-race",
            sender_address=EMAIL, subject="synth", now=base + timedelta(minutes=1),
        )
        row = self.conn.execute("SELECT * FROM items WHERE id = ?", (mail["id"],)).fetchone()
        view = {
            "source": "gmail", "message_id": row["message_id"], "thread_id": row["thread_id"],
            "sender_address_hash": row["sender_address_hash"], "internal_date": row["detected_at"], "is_group": 0,
        }
        digest = address_hash.address_hash(EMAIL)

        def forget_now():
            proactive_store.forget_subject(self.conn, address_hashes=[digest])

        watcher.set_evaluate_fault_for_tests(forget_now)
        watcher._finish_item(self.conn, mail["id"], view, base, close_terminal=False)
        left = self.conn.execute("SELECT loop_matched FROM items WHERE id = ?", (mail["id"],)).fetchone()
        self.assertTrue(left is None or left["loop_matched"] == 0)
        claim = proactive_store.claim_next_speech(self.conn, now=base)
        self.assertNotIn(NAME, json.dumps(claim))
        self.assertNotEqual(self.conn.execute("SELECT status FROM loops WHERE id = ?", (created["loop_id"],)).fetchone()[0], "open")

    def test_stop_race_watcher(self) -> None:
        created = self._create("Let me know when Beebo Dev emails me.")
        base = datetime.now(timezone.utc).replace(microsecond=0)
        mail = proactive_store.insert_item(
            self.conn, source="gmail", message_id="stop-mail", thread_id="th-stop",
            sender_address=EMAIL, subject="synth", now=base + timedelta(minutes=1),
        )
        row = self.conn.execute("SELECT * FROM items WHERE id = ?", (mail["id"],)).fetchone()
        view = {
            "source": "gmail", "message_id": row["message_id"], "thread_id": row["thread_id"],
            "sender_address_hash": row["sender_address_hash"], "internal_date": row["detected_at"], "is_group": 0,
        }

        def stop_now():
            proactive_store.close_loop(self.conn, created["loop_id"], closed_intent="cancelled")

        watcher.set_evaluate_fault_for_tests(stop_now)
        watcher._finish_item(self.conn, mail["id"], view, base, close_terminal=False)
        matched = self.conn.execute("SELECT loop_matched FROM items WHERE id = ?", (mail["id"],)).fetchone()[0]
        self.assertEqual(matched, 0)
        self.assertEqual(
            self.conn.execute("SELECT closed_intent FROM loops").fetchone()[0], "cancelled"
        )
        self.conn.execute("UPDATE loops SET expires_at = ? ", ("2020-01-01T00:00:00Z",))
        self.conn.commit()
        proactive_store.purge_retention(self.conn, now=base)
        proactive_store.purge_retention(self.conn, now=base)
        self.assertEqual(self.conn.execute("SELECT closed_intent FROM loops").fetchone()[0], "cancelled")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM loops WHERE status = 'expired'").fetchone()[0], 0)

    def test_sender_hint_cleared(self) -> None:
        base = datetime.now(timezone.utc)
        item = self._ingest("hint", base)
        self.assertIsNotNone(self.conn.execute("SELECT sender_hint FROM items").fetchone()[0])
        proactive_store.forget_subject(self.conn, address_hashes=[phone_ids.hash(NUMBER)])
        row = self.conn.execute("SELECT sender_hint, body FROM items").fetchone()
        self.assertTrue(row is None or row["sender_hint"] is None)
        self.assertTrue(row is None or row["body"] is None)

    def test_tombstone_on_delete_and_redact(self) -> None:
        self._create("Let me know when Beebo Dev texts.")
        base = datetime.now(timezone.utc).replace(microsecond=0)
        gone = self._ingest("del", base + timedelta(minutes=1))
        flying = self._ingest("fly", base + timedelta(minutes=2))
        self._evaluate(gone["id"], base)
        self._evaluate(flying["id"], base)
        claim = proactive_store.claim_next_speech(self.conn, now=base + timedelta(minutes=3))
        self.assertEqual(claim.get("item_id"), gone["id"])
        proactive_store.forget_subject(self.conn, address_hashes=[phone_ids.hash(NUMBER)])
        self.assertIsNone(self.conn.execute("SELECT id FROM items WHERE id = ?", (flying["id"],)).fetchone())
        redacted = self.conn.execute("SELECT content_state FROM items WHERE id = ?", (gone["id"],)).fetchone()
        self.assertEqual(redacted["content_state"], "forgotten")
        self.assertGreaterEqual(self.conn.execute("SELECT COUNT(*) FROM phone_tombstones").fetchone()[0], 2)

    def test_resend_suppressed(self) -> None:
        base = datetime.now(timezone.utc)
        self._ingest("same", base)
        proactive_store.forget_subject(self.conn, address_hashes=[phone_ids.hash(NUMBER)])
        again = self._ingest("same", base + timedelta(seconds=1))
        self.assertEqual(again.get("result"), "suppressed")

    def test_reinstall_limit_documented(self) -> None:
        self.assertIn("does not cover a new install", proactive_store.REINSTALL_TOMBSTONE_LIMIT)
        base = datetime.now(timezone.utc)
        self._ingest("old-install", base)
        proactive_store.forget_subject(self.conn, address_hashes=[phone_ids.hash(NUMBER)])
        fresh = proactive_store.ingest_phone_item(
            self.conn, kind="sms", device_id="device-new-install", revision=1, completeness="complete",
            received_at=base, provider_id="old-install", sender_raw=NUMBER, body="synthetic", is_group=0, now=base,
        )
        self.assertEqual(fresh.get("result"), "stored", fresh)

    def test_new_text_after_forget_stored(self) -> None:
        base = datetime.now(timezone.utc)
        self._ingest("first", base)
        proactive_store.forget_subject(self.conn, address_hashes=[phone_ids.hash(NUMBER)])
        nxt = self._ingest("second", base + timedelta(minutes=1))
        self.assertEqual(nxt.get("result"), "stored")
        created = self._create("Let me know when Beebo Dev texts.")
        self.assertTrue(created["ok"], created)

    def test_forget_in_flight_claimed(self) -> None:
        self._inflight("claimed")

    def test_forget_in_flight_speech_started(self) -> None:
        self._inflight("speech_started")

    def test_forget_in_flight_uncertain(self) -> None:
        self._inflight("delivery_uncertain")

    def _inflight(self, stage: str) -> None:
        self._create("Let me know when Beebo Dev texts.")
        base = datetime.now(timezone.utc).replace(microsecond=0)
        item = self._ingest("fly-%s" % stage, base + timedelta(minutes=1))
        self._evaluate(item["id"], base)
        claim = proactive_store.claim_next_speech(self.conn, now=base + timedelta(minutes=2))
        self.assertTrue(claim["ok"], claim)
        if stage != "claimed":
            started = proactive_store.mark_speech_started(self.conn, item["id"], claim["attempt_id"], now=base)
            self.assertTrue(started["ok"], started)
        if stage == "delivery_uncertain":
            uncertain = proactive_store.mark_delivery_uncertain(self.conn, item["id"], claim["attempt_id"], now=base)
            self.assertTrue(uncertain["ok"], uncertain)
        forgot = proactive_store.forget_subject(self.conn, address_hashes=[phone_ids.hash(NUMBER)])
        self.assertTrue(forgot["ok"], forgot)
        row = self.conn.execute("SELECT * FROM items WHERE id = ?", (item["id"],)).fetchone()
        self.assertEqual(row["content_state"], "forgotten")
        self.assertIsNone(row["sender_hint"])
        self.assertIsNone(row["body"])
        outcome = proactive_store.mark_delivered(self.conn, item["id"], claim["attempt_id"], now=base)
        self.assertFalse(outcome.get("ok"))
        self.assertNotEqual(self.conn.execute("SELECT delivery FROM items WHERE id = ?", (item["id"],)).fetchone()[0], "delivered")
        self.assertIsNone(
            self.conn.execute("SELECT id FROM deliveries WHERE item_id = ? AND outcome = 'delivered'", (item["id"],)).fetchone()
        )

    def test_briefing_watched_phone_line(self) -> None:
        block = self._watched_block("What came in?")
        self.assertIn("His current request comes first; mention it when it fits.", block)
        self.assertNotIn("reply on a thread", block)

    def test_briefing_task_before_watched_item(self) -> None:
        block = self._watched_block("Help me with this car")
        self.assertLess(block.index("current request"), block.index(NAME))
        self.assertIn("His current request comes first; mention it when it fits.", block)

    def test_pending_watched_burst_one_line(self) -> None:
        block = self._watched_block("What came in?", extra=1)
        self.assertEqual(block.count(NAME), 1)

    def test_followup_pronoun_live_read(self) -> None:
        import phone_tools

        self._watched_block("What came in?")
        seen = {}

        def fake(request, **fields):
            seen["request"] = request
            seen["selector"] = fields.get("selector")
            return {"ok": True, "status": "ok", "items": [{"body": "on the phone", "direction": "in", "kind": "sms"}]}

        with self._turn_on("What did they say?"), mock.patch.object(phone_tools, "phone_call", fake):
            out = phone_tools.phone_read_texts_handler({"person": "they"})
        self.assertEqual(seen.get("request"), "read_history")
        self.assertEqual(seen.get("selector"), NUMBER)
        self.assertIn("on the phone", out)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM items").fetchone()[0], 1)

    def test_pronoun_two_people_asks(self) -> None:
        import phone_tools

        loops.note_session_person("sess-watch", "c_beebo", NAME)
        loops.note_session_person("sess-watch", "c_other", "Other Person")
        with self._turn_on("What did they say?"):
            out = phone_tools.phone_read_texts_handler({"person": "they"})
        self.assertIn("Which one", out)
        self.assertIn(NAME, out)

    def test_several_matches_ask(self) -> None:
        contact_index.set_people_for_tests([
            _person(),
            _person(handle="c_dale", name="Beebo Dale", numbers=(OTHER,), emails=("dale@example.com",)),
        ])
        with self._turn_on("Watch for Beebo."):
            refused = loops.create_loop(self.conn, {"action": "create", "intent": "person", "person": "Beebo"})
        self.assertEqual(refused.get("refused_reason"), "which")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM loops").fetchone()[0], 0)

    def test_read_after_forget_stores_nothing(self) -> None:
        import phone_tools

        self._watched_block("What came in?")
        proactive_store.forget_subject(self.conn, address_hashes=[phone_ids.hash(NUMBER)])
        before = {
            name: self.conn.execute("SELECT COUNT(*) FROM " + name).fetchone()[0]
            for name in ("items", "loops", "phone_tombstones", "deliveries", "item_attempts")
        }

        def fake(request, **fields):
            return {"ok": True, "status": "ok", "items": [{"body": "on the phone", "direction": "in", "kind": "sms"}]}

        with self._turn_on("Read texts from Beebo Dev"), mock.patch.object(phone_tools, "phone_call", fake):
            out = phone_tools.phone_read_texts_handler({"person": NAME})
        self.assertIn("on the phone", out)
        after = {
            name: self.conn.execute("SELECT COUNT(*) FROM " + name).fetchone()[0]
            for name in before
        }
        self.assertEqual(after, before)

    def test_watched_line_survives_real_shaped_volume(self) -> None:
        moment = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(minutes=1)
        self._create("Let me know when Beebo Dev texts.")
        watched = self._ingest("watched", moment)
        self._evaluate(watched["id"], moment)
        for index in range(6):
            self._ingest("plain%s" % index, moment + timedelta(seconds=index + 1), sender=OTHER)
            self._ingest(
                "note%s" % index, moment + timedelta(seconds=index + 10), kind="notif",
                package="com.instagram.android", key="n%s" % index,
            )
            mail = proactive_store.insert_item(
                self.conn, source="gmail", message_id="vol-%s" % index, thread_id="th-%s" % index,
                sender_address="other@example.com", subject="synth", now=moment,
            )
            self.conn.execute(
                "UPDATE items SET label = 'important', processing = 'ranked', eligibility = 'eligible', gist = ? WHERE id = ?",
                ("VOL%s" % index, mail["id"]),
            )
        self.conn.commit()
        taint.set_store_path_for_tests(self.home / "taint.sqlite")
        taint.set_lineage_root_fn_for_tests(lambda _session: None)
        surface.set_enabled_for_tests(True)
        surface.set_now_for_tests(moment + timedelta(minutes=5))
        surface.set_gap_for_tests(0)
        self.conn.execute(
            "UPDATE meta SET value = ? WHERE key = ?",
            ((moment - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ"), proactive_store.META_PHONE_SURFACE_CUTOFF),
        )
        self.conn.commit()
        with self._turn_on("What came in?"):
            block = surface.pre_llm_call_hook(
                turn_id=turn_context.current_turn_id_from_context(),
                session_id="sess-watch",
                task_id="task-1",
                user_message="What came in?",
            )
        self.assertIsNotNone(block)
        self.assertIn(NAME, block)
        self.assertIn("His current request comes first; mention it when it fits.", block)
        self.assertLess(sum(1 for index in range(6) if ("VOL%s" % index) in block), 6)

    def _watched_block(self, message: str, extra: int = 0) -> str:
        taint.set_store_path_for_tests(self.home / "taint.sqlite")
        taint.set_lineage_root_fn_for_tests(lambda _session: None)
        surface.set_enabled_for_tests(True)
        now = datetime.now(timezone.utc).replace(microsecond=0)
        surface.set_now_for_tests(now)
        surface.set_gap_for_tests(0)
        self.conn.execute(
            "UPDATE meta SET value = ? WHERE key = ?",
            ((now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ"), proactive_store.META_PHONE_SURFACE_CUTOFF),
        )
        self.conn.commit()
        self._create("Let me know when Beebo Dev texts.")
        moment = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(minutes=1)
        surface.set_now_for_tests(moment + timedelta(minutes=5))
        self.conn.execute(
            "UPDATE meta SET value = ? WHERE key = ?",
            ((moment - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ"), proactive_store.META_PHONE_SURFACE_CUTOFF),
        )
        self.conn.commit()
        first = self._ingest("surf", moment)
        self._evaluate(first["id"], moment)
        for index in range(extra):
            item = self._ingest("surf%s" % index, moment + timedelta(seconds=index + 1))
            self._evaluate(item["id"], moment)
        with self._turn_on(message):
            block = surface.pre_llm_call_hook(
                turn_id=turn_context.current_turn_id_from_context(),
                session_id="sess-watch",
                task_id="task-1",
                user_message=message,
            )
        self.assertIsNotNone(block)
        return block or ""
