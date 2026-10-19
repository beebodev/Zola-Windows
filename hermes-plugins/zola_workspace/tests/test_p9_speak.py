"""P9-SPEAK Phase 4: claim predicate, attempt separation, recovery, retention."""

from __future__ import annotations

import inspect
import json
import os
import sys
import tempfile
import unittest
from unittest import mock
from datetime import datetime, timedelta, timezone
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

import log as wslog
import proactive_store
import speech
import surface

T0 = datetime(2026, 10, 16, 12, 0, tzinfo=timezone.utc)


def _at(**kwargs) -> datetime:
    return T0 + timedelta(**kwargs)


class SpeakClaimTests(unittest.TestCase):
    def setUp(self) -> None:
        self._dir = tempfile.TemporaryDirectory(prefix="p9speak_")
        self.path = Path(self._dir.name) / "proactive" / "proactive.db"
        proactive_store.set_ticket_override_for_tests(True)
        proactive_store.set_db_path_for_tests(self.path)
        self._old_home = os.environ.get("HERMES_HOME")
        os.environ["HERMES_HOME"] = self._dir.name
        wslog.reset_log_handler_for_tests()
        speech.reset_deliver_log_for_tests()
        self.conn = proactive_store.connect(self.path, retry=False)

    def tearDown(self) -> None:
        self.conn.close()
        proactive_store.set_ticket_override_for_tests(None)
        proactive_store.set_db_path_for_tests(None)
        wslog.reset_log_handler_for_tests()
        if self._old_home is None:
            os.environ.pop("HERMES_HOME", None)
        else:
            os.environ["HERMES_HOME"] = self._old_home
        self._dir.cleanup()

    def _gmail(self, message_id: str = "m1") -> str:
        made = proactive_store.insert_item(
            self.conn,
            source="gmail",
            message_id=message_id,
            thread_id="th-" + message_id,
            sender_address="speak-synthetic@example.com",
            sender_display_name="Synthetic",
            subject="package notice",
            snippet="a notice",
            body="body text",
            now=T0,
        )
        self.assertTrue(made.get("ok"), made)
        return made["id"]

    def _rank(self, item_id: str, label: str = "urgent") -> None:
        claimed = proactive_store.claim_rank(self.conn, item_id, now=T0)
        self.assertTrue(claimed.get("ok"), claimed)
        done = proactive_store.complete_rank(
            self.conn, item_id, claimed["attempt_id"], label=label, gist="gist", now=T0
        )
        self.assertTrue(done.get("ok"), done)

    def _row(self, item_id: str):
        return self.conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()

    def test_surface_attempt_id_clears_on_confirm_and_release_not_on_ttl(self) -> None:
        confirmed = self._gmail("confirm-me")
        self._rank(confirmed)
        selected = proactive_store.provisional_select(
            self.conn, confirmed, "surf-c", "turn-c", now=T0, reinject_cap=2, quiet_seconds=14400
        )
        self.assertTrue(selected.get("ok"), selected)
        done = proactive_store.confirm_surface_attempt(
            self.conn, "surf-c", "turn-c", now=T0, ttl_seconds=600, reinject_cap=2
        )
        self.assertTrue(done.get("ok"), done)
        self.assertIsNone(self._row(confirmed)["attempt_id"])

        released = self._gmail("release-me")
        self._rank(released)
        proactive_store.provisional_select(
            self.conn, released, "surf-r", "turn-r", now=T0, reinject_cap=2, quiet_seconds=14400
        )
        proactive_store.release_surface_attempt(self.conn, "surf-r")
        self.assertIsNone(self._row(released)["attempt_id"])

        stale = self._gmail("stale-me")
        self._rank(stale)
        proactive_store.provisional_select(
            self.conn, stale, "surf-s", "turn-s", now=T0, reinject_cap=2, quiet_seconds=14400
        )
        late = proactive_store.confirm_surface_attempt(
            self.conn, "surf-s", "turn-s", now=_at(seconds=601), ttl_seconds=600, reinject_cap=2
        )
        self.assertFalse(late.get("ok"), late)
        self.assertEqual(self._row(stale)["attempt_id"], "surf-s")

    def test_open_surface_attempt_blocks_claim(self) -> None:
        item_id = self._gmail("both")
        self._rank(item_id)
        proactive_store.set_loop_matched(self.conn, item_id, now=T0)
        proactive_store.provisional_select(
            self.conn, item_id, "surf-1", "turn-1", now=T0, reinject_cap=2, quiet_seconds=14400
        )
        claimed = proactive_store.claim_speech(self.conn, item_id, now=T0)
        self.assertFalse(claimed.get("ok"), claimed)
        self.assertEqual(claimed.get("refused_reason"), "surface_attempt_open")
        self.assertEqual(self._row(item_id)["delivery"], "none")

    def test_acknowledged_item_is_not_claimable(self) -> None:
        item_id = self._gmail("acked")
        self._rank(item_id)
        proactive_store.set_loop_matched(self.conn, item_id, now=T0)
        proactive_store.select_for_conversation(self.conn, item_id, now=T0)
        acked = proactive_store.acknowledge(self.conn, item_id, now=T0, turn_id="t")
        self.assertTrue(acked.get("ok"), acked)
        claimed = proactive_store.claim_speech(self.conn, item_id, now=T0)
        self.assertFalse(claimed.get("ok"), claimed)
        self.assertEqual(claimed.get("refused_reason"), "acknowledged")

    def test_content_expired_item_is_not_claimable(self) -> None:
        item_id = self._gmail("expired")
        self._rank(item_id)
        proactive_store.set_loop_matched(self.conn, item_id, now=T0)
        self.conn.execute(
            "UPDATE items SET content_state = 'content_expired' WHERE id = ?",
            (item_id,),
        )
        self.conn.commit()
        claimed = proactive_store.claim_speech(self.conn, item_id, now=T0)
        self.assertFalse(claimed.get("ok"), claimed)
        self.assertEqual(claimed.get("refused_reason"), "content_expired")
        self.assertEqual(self._row(item_id)["delivery"], "none")

    def test_urgent_without_loop_match_is_not_claimable(self) -> None:
        item_id = self._gmail("urgent")
        self._rank(item_id, label="urgent")
        self.assertEqual(self._row(item_id)["loop_matched"], 0)
        claimed = proactive_store.claim_speech(self.conn, item_id, now=T0)
        self.assertFalse(claimed.get("ok"), claimed)
        self.assertEqual(claimed.get("refused_reason"), "not_loop_matched")
        self.assertEqual(self._row(item_id)["delivery"], "none")

    def _speakable(self, message_id: str) -> str:
        item_id = self._gmail(message_id)
        self._rank(item_id)
        self.assertTrue(proactive_store.set_loop_matched(self.conn, item_id, now=T0)["ok"])
        return item_id

    def test_expired_surface_attempt_does_not_block_claim(self) -> None:
        item_id = self._speakable("stale-claim")
        proactive_store.provisional_select(
            self.conn, item_id, "surf-old", "turn-old", now=T0, reinject_cap=2, quiet_seconds=14400
        )
        claimed = proactive_store.claim_speech(self.conn, item_id, now=_at(seconds=601))
        self.assertTrue(claimed.get("ok"), claimed)
        self.assertEqual(self._row(item_id)["attempt_id"], "surf-old")

    def test_confirmed_note_stays_speakable(self) -> None:
        item_id = self._speakable("noted")
        proactive_store.provisional_select(
            self.conn, item_id, "surf-ok", "turn-ok", now=T0, reinject_cap=2, quiet_seconds=14400
        )
        done = proactive_store.confirm_surface_attempt(
            self.conn, "surf-ok", "turn-ok", now=T0, ttl_seconds=600, reinject_cap=2
        )
        self.assertTrue(done.get("ok"), done)
        self.assertGreaterEqual(self._row(item_id)["inject_count"], 1)
        claimed = proactive_store.claim_speech(self.conn, item_id, now=T0)
        self.assertTrue(claimed.get("ok"), claimed)

    def test_label_is_not_read(self) -> None:
        item_id = self._gmail("ignore-loop")
        marked = proactive_store.mark_loop_eligible(self.conn, item_id, now=T0)
        self.assertTrue(marked.get("ok"), marked)
        claimed_rank = proactive_store.claim_rank(self.conn, item_id, now=T0)
        proactive_store.complete_rank(
            self.conn, item_id, claimed_rank["attempt_id"], label="ignore", gist="gist", now=T0
        )
        source = inspect.getsource(proactive_store._claim_speech) + inspect.getsource(
            proactive_store._speech_block_reason
        )
        self.assertNotIn('row["label"]', source)
        self.assertNotIn("label =", source)
        claimed = proactive_store.claim_speech(self.conn, item_id, now=T0)
        self.assertTrue(claimed.get("ok"), claimed)

    def test_cross_attempt_cannot_complete_the_other(self) -> None:
        item_id = self._speakable("cross")
        proactive_store.provisional_select(
            self.conn, item_id, "surf-x", "turn-x", now=T0, reinject_cap=2, quiet_seconds=14400
        )
        proactive_store.release_surface_attempt(self.conn, "surf-x")
        speech = proactive_store.claim_speech(self.conn, item_id, now=T0)
        self.assertTrue(speech.get("ok"), speech)
        confirmed = proactive_store.confirm_surface_attempt(
            self.conn, speech["attempt_id"], "turn-x", now=T0, ttl_seconds=600, reinject_cap=2
        )
        self.assertFalse(confirmed.get("ok"), confirmed)
        self.assertEqual(self._row(item_id)["delivery"], "claimed")
        late = proactive_store.mark_delivered(self.conn, item_id, "surf-x", now=T0)
        self.assertEqual(late.get("refused_reason"), "attempt_mismatch")
        self.assertEqual(self._row(item_id)["conversation"], "none")

    def test_claim_recovers_expired_speech_started(self) -> None:
        item_id = self._speakable("recover")
        speech = proactive_store.claim_speech(self.conn, item_id, now=T0)
        proactive_store.mark_speech_started(self.conn, item_id, speech["attempt_id"], now=T0)
        other = self._speakable("other")
        claimed = proactive_store.claim_speech(self.conn, other, now=_at(seconds=121))
        self.assertTrue(claimed.get("ok"), claimed)
        self.assertEqual(self._row(item_id)["delivery"], "delivery_uncertain")

    def test_late_outcome_and_retry(self) -> None:
        item_id = self._speakable("late")
        speech = proactive_store.claim_speech(self.conn, item_id, now=T0)
        proactive_store.mark_speech_started(self.conn, item_id, speech["attempt_id"], now=T0)
        first = proactive_store.mark_delivered(self.conn, item_id, speech["attempt_id"], now=T0)
        self.assertTrue(first.get("ok"), first)
        again = proactive_store.mark_delivered(self.conn, item_id, speech["attempt_id"], now=T0)
        self.assertTrue(again.get("ok"), again)
        self.assertTrue(again.get("already"))
        count = self.conn.execute("SELECT COUNT(*) FROM deliveries").fetchone()[0]
        self.assertEqual(count, 1)
        uncertain_id = self._speakable("uncertain")
        uncertain = proactive_store.claim_speech(self.conn, uncertain_id, now=T0)
        proactive_store.mark_speech_started(self.conn, uncertain_id, uncertain["attempt_id"], now=T0)
        proactive_store.mark_delivery_uncertain(self.conn, uncertain_id, uncertain["attempt_id"], now=T0)
        late = proactive_store.mark_delivered(self.conn, uncertain_id, uncertain["attempt_id"], now=T0)
        self.assertFalse(late.get("ok"), late)
        self.assertEqual(self._row(uncertain_id)["delivery"], "delivery_uncertain")

    def test_delivered_text_waits_for_acknowledge_or_seven_days(self) -> None:
        item_id = self._speakable("kept")
        speech = proactive_store.claim_speech(self.conn, item_id, now=T0)
        proactive_store.mark_speech_started(self.conn, item_id, speech["attempt_id"], now=T0)
        proactive_store.mark_delivered(self.conn, item_id, speech["attempt_id"], now=T0)
        proactive_store.purge_retention(self.conn, now=_at(minutes=1))
        self.assertEqual(self._row(item_id)["subject"], "package notice")
        self.assertEqual(self._row(item_id)["gist"], "gist")
        self.assertIsNone(self._row(item_id)["body"])
        acked = proactive_store.acknowledge(
            self.conn, item_id, now=_at(minutes=2), turn_id="t", include_unselected=True
        )
        self.assertTrue(acked.get("ok"), acked)
        proactive_store.purge_retention(self.conn, now=_at(minutes=3))
        self.assertIsNone(self._row(item_id)["subject"])
        self.assertIsNone(self._row(item_id)["gist"])

    def test_unranked_loop_match_keeps_its_body(self) -> None:
        item_id = self._gmail("unranked")
        self.assertTrue(proactive_store.mark_loop_eligible(self.conn, item_id, now=T0)["ok"])
        speech = proactive_store.claim_speech(self.conn, item_id, now=T0)
        self.assertTrue(speech.get("ok"), speech)
        self.assertEqual(self._row(item_id)["body"], "body text")
        proactive_store.mark_speech_started(self.conn, item_id, speech["attempt_id"], now=T0)
        proactive_store.mark_delivered(self.conn, item_id, speech["attempt_id"], now=T0)
        proactive_store.purge_retention(self.conn, now=_at(minutes=1))
        self.assertEqual(self._row(item_id)["body"], "body text")

    def test_dismiss_clears_spoken_text_immediately(self) -> None:
        item_id = self._speakable("dismiss")
        speech = proactive_store.claim_speech(self.conn, item_id, now=T0)
        proactive_store.mark_speech_started(self.conn, item_id, speech["attempt_id"], now=T0)
        proactive_store.mark_delivered(self.conn, item_id, speech["attempt_id"], now=T0)
        dismissed = proactive_store.dismiss_item(self.conn, item_id, now=T0, turn_id="t")
        self.assertTrue(dismissed.get("ok"), dismissed)
        self.assertIsNone(self._row(item_id)["subject"])
        self.assertIsNone(self._row(item_id)["gist"])
        self.assertIsNone(self._row(item_id)["sender_display_name"])

    def test_gateway_claim_shape_and_disabled(self) -> None:
        item_id = self._speakable("gate")
        speech.set_speak_enabled_for_tests(False)
        try:
            refused = speech.claim_for_client({"item_id": item_id})
            self.assertEqual(refused.get("reason"), "speak_disabled")
            self.assertEqual(self._row(item_id)["delivery"], "none")
            speech.set_speak_enabled_for_tests(True)
            fresh = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            self.conn.execute("UPDATE items SET detected_at = ? WHERE id = ?", (fresh, item_id))
            self.conn.commit()
            claimed = speech.claim_for_client({})
            self.assertTrue(claimed.get("ok"), claimed)
            self.assertEqual(claimed.get("item_id"), item_id)
            self.assertEqual(claimed.get("source"), "gmail")
            self.assertEqual(
                set(claimed),
                {"ok", "item_id", "attempt_id", "name", "name_source", "source"},
            )
            self.assertNotIn("subject", claimed)
            self.assertNotIn("gist", claimed)
            self.assertNotIn("body", claimed)
            bad = speech.claim_for_client({"item_id": item_id})
            self.assertEqual(bad.get("reason"), "bad_args")
            snap = speech.snapshot_for_client({})
            self.assertTrue(snap.get("ok"), snap)
            self.assertIn("turn_in_flight", snap)
            self.assertNotIn("subject", snap)
        finally:
            speech.set_speak_enabled_for_tests(None)


    def test_refused_claim_keeps_expired_speech_recovery(self) -> None:
        item_id = self._speakable("expired-start")
        speech_claim = proactive_store.claim_speech(self.conn, item_id, now=T0)
        proactive_store.mark_speech_started(self.conn, item_id, speech_claim["attempt_id"], now=T0)
        refused = proactive_store.claim_speech(self.conn, item_id, now=_at(seconds=121))
        self.assertFalse(refused.get("ok"), refused)
        self.assertEqual(self._row(item_id)["delivery"], "delivery_uncertain")

    def test_claim_next_takes_the_oldest_and_no_item_id(self) -> None:
        older = self._speakable("older")
        newer = self._gmail("newer")
        self._rank(newer)
        self.assertTrue(proactive_store.set_loop_matched(self.conn, newer, now=_at(seconds=30))["ok"])
        self.conn.execute(
            "UPDATE items SET detected_at = ? WHERE id = ?",
            (_at(seconds=30).strftime("%Y-%m-%dT%H:%M:%SZ"), newer),
        )
        self.conn.commit()
        speech.set_speak_enabled_for_tests(True)
        try:
            fresh = datetime.now(timezone.utc)
            for item_id, skew in ((older, -60), (newer, -10)):
                stamp = (fresh + timedelta(seconds=skew)).strftime("%Y-%m-%dT%H:%M:%SZ")
                self.conn.execute("UPDATE items SET detected_at = ? WHERE id = ?", (stamp, item_id))
            self.conn.commit()
            claimed = speech.claim_for_client({})
            self.assertTrue(claimed.get("ok"), claimed)
            self.assertEqual(claimed.get("item_id"), older)
            self.assertEqual(claimed.get("source"), "gmail")
            self.assertEqual(
                set(claimed),
                {"ok", "item_id", "attempt_id", "name", "name_source", "source"},
            )
            refused = speech.claim_for_client({"item_id": older})
            self.assertEqual(refused.get("reason"), "bad_args")
        finally:
            speech.set_speak_enabled_for_tests(None)

    def test_name_follows_the_matching_sender_loop(self) -> None:
        item_id = self._gmail("thread-item")
        thread_id = "th-thread-item"
        hash_right = proactive_store.address_hash("speak-synthetic@example.com")
        hash_wrong = proactive_store.address_hash("other-synthetic@example.com")
        self.assertEqual(self._row(item_id)["sender_address_hash"], hash_right)
        for name, source, digest in (
            ("Zoe Caller", "contacts_ticket", hash_wrong),
            ("Ada Lovelace", "brian_message", hash_right),
        ):
            made = proactive_store.insert_loop(
                self.conn,
                intent="reply",
                predicate={
                    "op": "all",
                    "args": [
                        {"op": "gmail_thread", "thread_id": thread_id},
                        {"op": "sender_is", "address_hash": digest},
                    ],
                },
                session_id="sess",
                sender_display_name=name,
                name_source=source,
                source_ids=[thread_id],
                address_hashes=[digest],
                now=T0,
            )
            self.assertTrue(made.get("ok"), made)
        found_source, found_name = speech._name_for_item(self.conn, item_id)
        self.assertEqual(found_name, "Ada Lovelace")
        self.assertEqual(found_source, "brian_message")

    def test_name_lookup_failure_releases_the_claim(self) -> None:
        item_id = self._speakable("boom")
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.conn.execute("UPDATE items SET detected_at = ? WHERE id = ?", (stamp, item_id))
        self.conn.commit()
        speech.set_speak_enabled_for_tests(True)

        def explode(conn, claimed_id):
            raise RuntimeError("secret subject line")

        try:
            with mock.patch("speech._name_for_item", explode):
                result = speech.claim_for_client({})
            self.assertFalse(result.get("ok"), result)
            self.assertEqual(result.get("reason"), "error")
            self.assertEqual(self._row(item_id)["delivery"], "none")
            self.assertNotIn("secret subject", str(result))
        finally:
            speech.set_speak_enabled_for_tests(None)

    def test_wrapper_refuses_on_exception_class_only(self) -> None:
        def explode(params):
            raise RuntimeError("secret subject line")

        wrapped = speech._wrap(explode)
        with self.assertLogs("zola_workspace", level="INFO") as caught:
            result = wrapped("rpc-1", {})
        self.assertEqual(result["error"]["message"], "error")
        text = "\n".join(caught.output)
        self.assertIn("reason=RuntimeError", text)
        self.assertNotIn("secret subject", text)

    def test_snapshot_has_no_call_counter(self) -> None:
        snap = speech.snapshot_for_client({})
        self.assertTrue(snap.get("ok"), snap)
        self.assertNotIn("generation", snap)
        self.assertNotIn("snapshot_seq", snap)

    def test_deny_log_changes_once_and_idle_once(self) -> None:
        speech.reset_deliver_log_for_tests()
        speech.set_speak_enabled_for_tests(False)
        try:
            with self.assertLogs("zola_workspace", level="INFO") as caught:
                self.assertEqual(speech.claim_for_client({}).get("reason"), "speak_disabled")
                self.assertEqual(speech.claim_for_client({}).get("reason"), "speak_disabled")
                speech.set_speak_enabled_for_tests(True)
                self.assertEqual(speech.claim_for_client({}).get("reason"), "nothing_speakable")
                self.assertEqual(speech.claim_for_client({}).get("reason"), "nothing_speakable")
        finally:
            speech.set_speak_enabled_for_tests(None)
        text = "\n".join(caught.output)
        self.assertEqual(text.count("reason=speak_disabled"), 1)
        self.assertEqual(text.count("outcome=idle"), 1)
        self.assertEqual(text.count("reason=nothing_speakable"), 1)

    def test_recover_failure_logs_once(self) -> None:
        speech.reset_deliver_log_for_tests()
        with mock.patch("speech._connect", return_value=None):
            with self.assertLogs("zola_workspace", level="INFO") as caught:
                self.assertEqual(speech.recover_for_client({}).get("reason"), "no_store")
                self.assertEqual(speech.recover_for_client({}).get("reason"), "no_store")
        text = "\n".join(caught.output)
        self.assertEqual(text.count("reason=no_store"), 1)
        self.assertEqual(text.count("outcome=deny"), 1)

    def test_install_methods_match_the_contract(self) -> None:
        import types

        path = Path(__file__).resolve().parents[1] / "contracts" / "proactive_methods.json"
        expected = json.loads(path.read_text(encoding="utf-8"))["methods"]
        fake = types.ModuleType("tui_gateway.server")
        fake._methods = {}
        package = types.ModuleType("tui_gateway")
        package.server = fake
        package.__path__ = []
        with mock.patch.dict(sys.modules, {"tui_gateway": package, "tui_gateway.server": fake}):
            with mock.patch("origin.in_serve_process", return_value=True):
                self.assertTrue(speech.install_methods())
        registered = sorted(name for name in fake._methods if str(name).startswith("proactive."))
        self.assertEqual(registered, sorted(expected))

    def test_recover_does_not_claim(self) -> None:
        item_id = self._speakable("recover-only")
        speech_claim = proactive_store.claim_speech(self.conn, item_id, now=T0)
        proactive_store.mark_speech_started(self.conn, item_id, speech_claim["attempt_id"], now=T0)
        recovered = speech.recover_for_client({})
        self.assertTrue(recovered.get("ok"), recovered)
        self.assertEqual(self._row(item_id)["delivery"], "delivery_uncertain")
        self.assertNotIn("item_id", recovered)

    def test_watcher_health_adds_google_and_ranker_without_writing(self) -> None:
        proactive_store.write_ranker_status(self.conn, "provider_unavailable", now=T0)
        self.conn.commit()
        planted = "invalid_grant"
        with mock.patch("auth.store_status", return_value={"connected": True, "needs_reconnect": planted}):
            with mock.patch.object(proactive_store, "write_ranker_status", side_effect=AssertionError("write")):
                with mock.patch.object(proactive_store, "write_watcher_health", side_effect=AssertionError("write")):
                    body = speech.watcher_health_for_client({})
        encoded = json.dumps(body)
        self.assertNotIn(planted, encoded)
        self.assertIs(body.get("google_connected"), True)
        self.assertEqual(body.get("ranker_state"), "provider_unavailable")
        self.assertTrue(body.get("ranker_progress_at"))

    def test_surface_ttl_is_the_store_constant(self) -> None:
        self.assertIs(surface.SURFACE_ATTEMPT_TTL_SECONDS, proactive_store.SURFACE_ATTEMPT_TTL_SECONDS)


class SpeechTextTests(unittest.TestCase):
    def test_sanitizer_and_unnamed_lines(self) -> None:
        self.assertEqual(speech.sanitize_name("Ada Lovelace"), "Ada Lovelace")
        self.assertEqual(speech.sanitize_name("O'Brien-Smith"), "O'Brien-Smith")
        self.assertEqual(speech.sanitize_name("someone"), "")
        self.assertEqual(speech.sanitize_name("<img onerror=alert(1)>"), "")
        self.assertEqual(speech.sanitize_name("Ada\nLovelace"), "")
        self.assertEqual(speech.sanitize_name("Robert'); DROP TABLE items;--"), "")
        self.assertEqual(speech.sanitize_name("A" * 41), "")
        for line in speech.GMAIL_UNNAMED:
            self.assertNotIn("{name}", line)
            self.assertNotIn("someone", line.casefold())
        for line in speech.GMAIL_NAMED:
            self.assertIn("{name}", line)
        for line in speech.CALENDAR_LINES:
            self.assertNotIn("{name}", line)

    def test_watcher_fixture_matches_sentence(self) -> None:
        path = Path(__file__).resolve().parents[1] / "contracts" / "watcher_health.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        clock = datetime(2026, 10, 16, 12, 0, tzinfo=timezone.utc)
        for case in payload["cases"]:
            state, _sentence = surface.watcher_sentence(case["row"], clock)
            self.assertEqual(state, case["spoken"], case["name"])


if __name__ == "__main__":
    unittest.main()
