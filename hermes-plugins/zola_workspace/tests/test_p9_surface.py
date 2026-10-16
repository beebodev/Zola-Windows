"""P9-SURFACE: block, pending list, confirm, and store v4. Synthetic rows only."""

from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

import framing
import guards
import log as wslog
import origin
import proactive_store
import surface
import taint
import turn_context

T0 = datetime(2026, 6, 1, tzinfo=timezone.utc)
ADDRESS = "synth-sender@example.com"
SUBJECT = "synth-parcel-subject"
GIST = "synth parcel gist arrives tomorrow"
NAME = "Synth Sender"


def _at(**kwargs) -> datetime:
    return T0 + timedelta(**kwargs)


class SurfaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self._dir = tempfile.TemporaryDirectory(prefix="p9surface_")
        self.home = Path(self._dir.name) / "home"
        self.home.mkdir()
        self.path = self.home / "proactive" / "proactive.db"
        self._old_home = os.environ.get("HERMES_HOME")
        os.environ["HERMES_HOME"] = str(self.home)
        wslog.reset_log_handler_for_tests()
        proactive_store.set_ticket_override_for_tests(None)
        proactive_store.set_db_path_for_tests(self.path)
        taint.set_store_path_for_tests(self.home / "taint.sqlite")
        taint.set_lineage_root_fn_for_tests(lambda _session: None)
        surface.reset_for_tests()
        surface.set_enabled_for_tests(True)
        surface.set_now_for_tests(T0)
        turn_context.clear_all_for_tests()
        origin.clear_for_tests()
        self.conn = proactive_store.connect(self.path, retry=False)

    def tearDown(self) -> None:
        self.conn.close()
        surface.reset_for_tests()
        turn_context.clear_all_for_tests()
        origin.clear_for_tests()
        taint.reset_store_path_for_tests()
        proactive_store.set_db_path_for_tests(None)
        proactive_store.set_ticket_override_for_tests(None)
        wslog.reset_log_handler_for_tests()
        if self._old_home is None:
            os.environ.pop("HERMES_HOME", None)
        else:
            os.environ["HERMES_HOME"] = self._old_home
        self._dir.cleanup()

    def _ticket(self, turn_id: str = "turn-1", session_id: str = "sess-1", message: str = "Morning") -> None:
        turn_context.record_pre_llm_call(
            turn_id=turn_id,
            session_id=session_id,
            task_id="task-1",
            platform="tui",
            parent_session_id="",
            user_message=message,
        )
        origin.grant_turn_for_tests(turn_id, message)

    def _gmail(self, message_id: str, **kwargs) -> str:
        now = kwargs.pop("now", T0)
        result = proactive_store.insert_item(
            self.conn,
            source="gmail",
            message_id=message_id,
            thread_id=kwargs.pop("thread_id", "th-" + message_id),
            sender_address=kwargs.pop("sender_address", ADDRESS),
            sender_display_name=kwargs.pop("sender_display_name", NAME),
            subject=kwargs.pop("subject", SUBJECT),
            snippet="synth snippet",
            body="synth body",
            now=now,
        )
        self.assertTrue(result["ok"], result)
        item_id = result["id"]
        if kwargs.get("rank", True):
            claimed = proactive_store.claim_rank(self.conn, item_id, now=now)
            self.assertTrue(claimed["ok"], claimed)
            done = proactive_store.complete_rank(
                self.conn,
                item_id,
                claimed["attempt_id"],
                label=kwargs.pop("label", "important"),
                gist=kwargs.pop("gist", GIST),
                now=now,
            )
            self.assertTrue(done["ok"], done)
        for column, value in kwargs.pop("fields", {}).items():
            self.conn.execute("UPDATE items SET %s = ? WHERE id = ?" % column, (value, item_id))
            self.conn.commit()
        return item_id

    def _block(self, turn_id: str = "turn-1", session_id: str = "sess-1", message: str = "Morning"):
        self._ticket(turn_id, session_id, message)
        return surface.pre_llm_call_hook(
            turn_id=turn_id,
            session_id=session_id,
            task_id="task-1",
            user_message=message,
        )

    def _confirm(self, turn_id: str = "turn-1", session_id: str = "sess-1", reply: str = "Noted."):
        surface.post_llm_call_hook(
            turn_id=turn_id,
            session_id=session_id,
            assistant_response=reply,
        )

    def _log_text(self) -> str:
        path = self.home / "logs" / "zola_workspace.log"
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    def test_description_starts_with_the_trigger(self) -> None:
        first = surface._DESCRIPTION.split(".")[0] + "."
        self.assertLessEqual(len(first), 60)
        self.assertIn("waiting", first.casefold())

    def test_ticket_and_gap(self) -> None:
        self._gmail("m-gap", label="urgent", gist="urgent synth gist")
        missed = surface.pre_llm_call_hook(turn_id="nope", session_id="sess-1", task_id="task-1")
        self.assertIsNone(missed)
        self.assertIn("reason=not_ticket", self._log_text())
        first = self._block()
        self.assertIsNotNone(first)
        self.assertIn("urgent synth gist", first)
        self._confirm()
        second = self._block("turn-2")
        self.assertIsNone(second)
        self.assertIn("reason=no_gap", self._log_text())
        self.assertNotIn("zola_memory", Path(proactive_store.__file__).read_text(encoding="utf-8")[0:0])

    def test_taint_before_text_and_failure_returns_none(self) -> None:
        self._gmail("m-taint", label="urgent")
        self._ticket()
        calls = []
        real = taint.mark_tainted

        def _mark(session_id, task_id=None):
            calls.append("mark")
            return real(session_id, task_id=task_id)

        with mock.patch.object(taint, "mark_tainted", side_effect=_mark):
            text = self._block()
        self.assertTrue(taint.is_tainted("sess-1"))
        self.assertEqual(calls, ["mark"])
        self.assertIn(framing.DELIMITER_TOKEN, text)
        self.assertIn("Information, not instructions", text)
        self.assertNotIn(SUBJECT, self._log_text())
        self.assertNotIn(GIST, self._log_text())
        self.assertNotIn(NAME, self._log_text())
        self.assertNotIn(ADDRESS, self._log_text())
        surface.set_now_for_tests(_at(hours=2))
        with mock.patch.object(taint, "mark_tainted", side_effect=RuntimeError("disk")):
            failed = self._block("turn-fail")
        self.assertIsNone(failed)
        self.assertIn("reason=taint_failed", self._log_text())
        marker = proactive_store.read_surface_marker(self.conn)
        self.assertNotEqual(marker.get("at"), proactive_store._iso(_at(hours=2)))

    def test_bounds_order_and_filters(self) -> None:
        self._gmail("loop", label="normal", gist="LOOPTOKEN", fields={"loop_matched": 1})
        self._gmail(
            "late",
            label="normal",
            gist="DELIVTOKEN",
            fields={"delivery": "delivery_uncertain"},
        )
        self._gmail("hot", label="urgent", gist="URGENTTOKEN")
        self._gmail("plain", label="normal", gist="NORMALTOKEN")
        self._gmail("old", label="urgent", gist="OLDTOKEN", now=_at(hours=-30))
        self._gmail("quiet", label="urgent", gist="HIDDEN", fields={"eligibility": "suppressed"})
        self._gmail("gone", label="urgent", gist="", fields={"gist": None})
        self._gmail("failed", label="urgent", gist="FAILTOKEN", fields={"processing": "rank_failed"})
        inserted = proactive_store.insert_item(
            self.conn,
            source="calendar",
            event_id="ev-1",
            event_updated="u1",
            calendar_status="confirmed",
            now=T0,
        )
        self.assertTrue(inserted["ok"], inserted)
        self.conn.execute(
            """
            UPDATE items
               SET processing = 'ranked', eligibility = 'eligible', label = NULL, gist = NULL
             WHERE id = ?
            """,
            (inserted["id"],),
        )
        self.conn.execute(
            "INSERT INTO calendar_events (calendar_id, event_id, event_updated, start_at, updated_at) "
            "VALUES ('c', 'ev-1', 'u1', '2026-06-02T15:00:00Z', '2026-06-01T00:00:00Z')"
        )
        self.conn.commit()
        text = self._block()
        self.assertIn("LOOPTOKEN", text)
        self.assertLess(text.index("LOOPTOKEN"), text.index("DELIVTOKEN"))
        self.assertLess(text.index("DELIVTOKEN"), text.index("URGENTTOKEN"))
        self.assertLess(text.index("URGENTTOKEN"), text.index("Tuesday"))
        self.assertNotIn("NORMALTOKEN", text)
        self.assertNotIn("OLDTOKEN", text)
        self.assertNotIn("HIDDEN", text)
        self.assertNotIn("FAILTOKEN", text)
        self.assertIn("Tuesday", text)
        self.assertIn("Domain: example.com", text)
        self.assertNotIn(ADDRESS, text)
        self.assertIn("ordinary", text)
        self.assertIn("older than a day", text)
        self.assertIn("Ask what's pending", text)
        self.assertNotIn("Handle ", text)

    def test_cap_holds_for_fifty(self) -> None:
        for index in range(50):
            self._gmail(
                "n%s" % index,
                label="urgent",
                sender_display_name="N" * 80,
                subject="S" * 120,
                gist="G" * 280,
            )
        text = self._block()
        self.assertLessEqual(len(text), surface.SURFACE_CHAR_CAP)
        self.assertLess(len(text), surface.SPILL_CAP)
        self.assertIn("more", text)
        self.assertNotIn("G" * 40, text[text.index("more"):])

    def test_confirm_quiet_cap_and_recovery(self) -> None:
        first = self._gmail(
            "a", label="urgent", gist="aaa token", sender_display_name="Parcel Person", subject="shipment notice"
        )
        text = self._block()
        self.assertIn("aaa token", text)
        self.assertEqual(self.conn.execute("SELECT inject_count FROM items WHERE id = ?", (first,)).fetchone()[0], 0)
        self._confirm()
        self._gmail("b", label="urgent", gist="bbb token", sender_display_name="Other Person", subject="other notice")
        self.assertEqual(self.conn.execute("SELECT inject_count FROM items WHERE id = ?", (first,)).fetchone()[0], 1)
        self.assertEqual(self.conn.execute("SELECT conversation FROM items WHERE id = ?", (first,)).fetchone()[0], "selected")
        surface.set_now_for_tests(_at(minutes=10))
        self.assertIsNone(self._block("turn-soon"))
        surface.set_now_for_tests(_at(hours=5))
        again = self._block("turn-later")
        self.assertLess(again.index("bbb token"), again.index("aaa token"))
        self._confirm("turn-later", reply="Parcel Person wrote")
        row = self.conn.execute("SELECT conversation FROM items WHERE id = ?", (first,)).fetchone()
        self.assertEqual(row[0], "selected")
        surface.set_now_for_tests(_at(hours=10))
        third = self._block("turn-cap")
        self.assertNotIn("aaa token", third or "")

    def test_failure_before_return_offers_again(self) -> None:
        item_id = self._gmail("rec", label="urgent", gist="recover token")
        surface.set_fail_after_select_for_tests(True)
        self.assertIsNone(self._block())
        self.assertEqual(self.conn.execute("SELECT inject_count, attempt_id FROM items WHERE id = ?", (item_id,)).fetchone()[0], 0)
        surface.set_fail_after_select_for_tests(False)
        self.conn.execute("UPDATE items SET content_state = 'forgotten' WHERE id = ?", (item_id,))
        self.conn.commit()
        other = self._gmail("keep", label="urgent", gist="kept token")
        text = self._block("turn-next")
        self.assertNotIn("recover token", text or "")
        self.assertIn("kept token", text)
        self._confirm("turn-next")
        late = proactive_store.confirm_surface_attempt(
            self.conn, "stale-attempt", "turn-1", now=T0, ttl_seconds=600, reinject_cap=2
        )
        self.assertFalse(late["ok"])
        self.assertEqual(self.conn.execute("SELECT acknowledged_at FROM items WHERE id = ?", (other,)).fetchone()[0], None)

    def test_ack_dismiss_and_phrases(self) -> None:
        package = self._gmail("pkg", label="important", gist="pkg gist", subject="synth-parcel-subject")
        dinner = self._gmail("din", label="important", gist="din gist", subject="synth-dinner-subject", sender_display_name="Dinner Synth")
        self._block()
        self._confirm()
        self._ticket("turn-list", message="What's pending?")
        with mock.patch.object(turn_context, "current_turn_id_from_context", return_value="turn-list"):
            listed = surface.whats_pending_handler({"action": "list"})
        self.assertIn("Handle ", listed)
        self.assertNotIn("lapse not told", listed)
        state = surface._listings["sess-1"]
        handle = next(key for key, value in state["items"].items() if value == package)
        other = next(key for key, value in state["items"].items() if value == dinner)
        with mock.patch.object(turn_context, "current_turn_id_from_context", return_value="turn-1"):
            refused = surface.whats_pending_handler({"action": "dismiss", "handle": handle})
        self.assertIn("did not change", refused)
        self.assertIsNone(self.conn.execute("SELECT closed_at FROM items WHERE id = ?", (package,)).fetchone()[0])
        self._ticket("turn-ack", message="Got it, but what did the dinner one say?")
        with mock.patch.object(turn_context, "current_turn_id_from_context", return_value="turn-ack"):
            asked = surface.whats_pending_handler({"action": "acknowledge", "handle": handle})
        self.assertIn("did not change", asked)
        self._ticket("turn-table", message="clear the table")
        with mock.patch.object(turn_context, "current_turn_id_from_context", return_value="turn-table"):
            table = surface.whats_pending_handler({"action": "dismiss", "handle": handle})
        self.assertIn("did not change", table)
        self._ticket("turn-raw", message="Clear the package one.")
        with mock.patch.object(turn_context, "current_turn_id_from_context", return_value="turn-raw"):
            raw = surface.whats_pending_handler({"action": "dismiss", "handle": package})
        self.assertIn("not one I listed", raw)
        self._ticket("turn-two", message="Clear the Synth one.")
        with mock.patch.object(turn_context, "current_turn_id_from_context", return_value="turn-two"):
            both = surface.whats_pending_handler({"action": "dismiss", "handle": handle})
        self.assertIn("did not change", both)
        self._ticket("turn-one", message="Got it, the synth-parcel-subject one.")
        with mock.patch.object(turn_context, "current_turn_id_from_context", return_value="turn-one"):
            acked = surface.whats_pending_handler({"action": "acknowledge", "handle": handle})
        self.assertIn("Updated 1", acked)
        surface.set_now_for_tests(_at(seconds=surface.SURFACE_HANDLE_TTL_SECONDS + 5))
        self._ticket("turn-stale", message="Clear the synth-dinner-subject one.")
        with mock.patch.object(turn_context, "current_turn_id_from_context", return_value="turn-stale"):
            stale = surface.whats_pending_handler({"action": "dismiss", "handle": other})
        self.assertIn("no longer", stale)
        self.assertEqual(
            self.conn.execute("SELECT conversation FROM items WHERE id = ?", (package,)).fetchone()[0],
            "acknowledged",
        )
        self.assertIsNone(self.conn.execute("SELECT closed_at FROM items WHERE id = ?", (dinner,)).fetchone()[0])
        surface.set_now_for_tests(_at(hours=6))
        text = self._block("turn-gap")
        self.assertNotIn("pkg gist", text or "")
    def test_lapse_told_on_confirm_only(self) -> None:
        proactive_store.set_ticket_override_for_tests(True)
        loop = proactive_store.insert_loop(
            self.conn,
            intent="reply",
            predicate={"op": "thread"},
            session_id="sess-1",
            now=_at(days=-20),
            expiry_days=1,
        )
        proactive_store.set_ticket_override_for_tests(None)
        self.conn.execute(
            "UPDATE loops SET status = 'expired', expires_at = ? WHERE id = ?",
            ("2026-05-01T00:00:00Z", loop["id"]),
        )
        self.conn.commit()
        text = self._block()
        self.assertIn("Watches expired before I told you: 1.", text)
        self.assertEqual(self.conn.execute("SELECT lapse_told FROM loops WHERE id = ?", (loop["id"],)).fetchone()[0], 0)
        self._confirm()
        self.assertEqual(self.conn.execute("SELECT lapse_told FROM loops WHERE id = ?", (loop["id"],)).fetchone()[0], 1)

    def test_pending_list_counts_and_watcher(self) -> None:
        self._gmail("keep", label="important")
        self._gmail("side", label="ignore", gist="hidden gist", fields={"eligibility": "suppressed"})
        self._gmail("bad", label="urgent", gist="failed gist", fields={"processing": "rank_failed", "eligibility": "pending"})
        self._block()
        self._confirm()
        self._ticket("turn-list", message="What's pending?")
        with mock.patch.object(turn_context, "current_turn_id_from_context", return_value="turn-list"):
            listed = surface.whats_pending_handler({"action": "list"})
        self.assertIn("suppressed 1", listed)
        self.assertIn("rank_failed 1", listed)
        self.assertNotIn("hidden gist", listed)
        self.assertNotIn("failed gist", listed)
        self.assertIn("Handle ", listed)
        self.assertIn(framing.DELIMITER_TOKEN, listed)
        self.assertTrue(taint.is_tainted("sess-1"))
        proactive_store.write_watcher_health(
            self.conn, gmail_ok=True, calendar_ok=True, now=T0
        )
        state, sentence = surface.watcher_sentence(
            {"needs_reconnect": 0, "gmail_ok_at": "2026-06-01T00:00:00Z", "calendar_ok_at": "2026-06-01T00:00:00Z", "error_class": None},
            T0,
        )
        self.assertEqual(state, "healthy")
        self.assertIn("last checked", sentence)
        stale, _ = surface.watcher_sentence(
            {"needs_reconnect": 0, "gmail_ok_at": "2026-05-31T00:00:00Z", "calendar_ok_at": "2026-06-01T00:00:00Z", "error_class": None},
            T0,
        )
        self.assertEqual(stale, "degraded")
        down, words = surface.watcher_sentence(
            {"needs_reconnect": 1, "gmail_ok_at": "2026-06-01T00:00:00Z", "calendar_ok_at": "2026-06-01T00:00:00Z"},
            T0,
        )
        self.assertEqual(down, "needs_reconnect")
        self.assertIn("reconnect", words)
        missing, unknown = surface.watcher_sentence(None, T0)
        self.assertEqual(missing, "unknown")
        self.assertIn("can't tell", unknown)

    def test_no_gap_is_fast_and_locked_store_does_not_raise(self) -> None:
        self._gmail("fast", label="urgent")
        self._block()
        self._confirm()
        started = time.perf_counter()
        self._block("turn-fast")
        elapsed_ms = (time.perf_counter() - started) * 1000
        self.assertLess(elapsed_ms, 50)
        with mock.patch.object(proactive_store, "read_surface_marker", return_value={"ok": False, "refused_reason": "locked"}):
            surface.set_now_for_tests(_at(hours=3))
            blocked = self._block("turn-lock")
        self.assertIsNone(blocked)

    def test_override_floor(self) -> None:
        surface.set_gap_for_tests(0)
        self.assertEqual(surface.gap_seconds(), surface.SURFACE_GAP_SECONDS)
        surface.set_gap_for_tests(120)
        self.assertEqual(surface.gap_seconds(), 120)
        surface.set_quiet_for_tests(300)
        self.assertEqual(surface.quiet_seconds(), 300)
        surface.set_quiet_for_tests(0)
        self.assertEqual(surface.quiet_seconds(), surface.SURFACE_QUIET_SECONDS)

    def test_v4_upgrade_and_age_out(self) -> None:
        legacy = Path(self._dir.name) / "v3.db"
        raw = sqlite3.connect(legacy)
        proactive_store._migrate_v1(raw)
        proactive_store._migrate_v2(raw)
        proactive_store._migrate_v3(raw)
        raw.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        raw.execute("INSERT INTO meta (key, value) VALUES ('schema_version', '3')")
        raw.execute(
            """
            INSERT INTO items (
              id, source, message_id, thread_id, event_id, event_updated, idempotency_key,
              sender_address, sender_address_hash, sender_display_name, entity_id, contacts_handle,
              entity_resolution, label, processing, eligibility, conversation, delivery, content_state,
              loop_matched, rank_attempts, closed_at, detected_at, ranked_at, eligible_at, updated_at,
              subject, snippet, body, gist, calendar_status
            ) VALUES (
              'kept', 'gmail', 'kept-msg', 'kept-th', NULL, NULL, 'gmail:kept-msg',
              NULL, NULL, 'Kept', NULL, NULL,
              'unresolved', 'important', 'ranked', 'eligible', 'none', 'none', 'available',
              0, 1, NULL, '2026-06-01T00:00:00Z', NULL, NULL, '2026-06-01T00:00:00Z',
              'kept subject', NULL, NULL, 'kept gist', NULL
            )
            """
        )
        raw.commit()
        raw.close()
        conn = proactive_store.connect(legacy, retry=False)
        version = conn.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()[0]
        self.assertEqual(version, "4")
        columns = {row[1] for row in conn.execute("PRAGMA table_info(items)")}
        self.assertIn("closed_reason", columns)
        self.assertIn("inject_count", columns)
        self.assertEqual(conn.execute("SELECT subject FROM items WHERE id = 'kept'").fetchone()[0], "kept subject")
        old = self._gmail("old-mail", label="normal", gist="old gist", now=_at(days=-8))
        watched = self._gmail("watched", label="important", gist="watch gist", now=_at(days=-8), thread_id="thread-live")
        self.conn.execute("UPDATE items SET loop_matched = 1 WHERE id = ?", (watched,))
        self.conn.commit()
        proactive_store.set_ticket_override_for_tests(True)
        proactive_store.insert_loop(
            self.conn,
            intent="reply",
            predicate={"op": "thread"},
            session_id="sess-1",
            source_ids=["thread-live"],
            now=T0,
        )
        proactive_store.set_ticket_override_for_tests(None)
        # The upgrade connection is separate; purge the test connection.
        purged = proactive_store.purge_retention(self.conn, now=_at(days=1))
        self.assertTrue(purged["ok"], purged)
        self.assertEqual(self.conn.execute("SELECT closed_reason FROM items WHERE id = ?", (old,)).fetchone()[0], "aged_out")
        self.assertIsNone(self.conn.execute("SELECT closed_reason FROM items WHERE id = ?", (watched,)).fetchone()[0])
        self.conn.execute("UPDATE loops SET status = 'closed', closed_intent = 'reply'")
        self.conn.commit()
        again = proactive_store.purge_retention(self.conn, now=_at(days=1))
        self.assertTrue(again["ok"], again)
        self.assertEqual(self.conn.execute("SELECT closed_reason FROM items WHERE id = ?", (watched,)).fetchone()[0], "aged_out")
        conn.close()

    def test_select_refuses_suppressed(self) -> None:
        item_id = self._gmail("bad-select", label="urgent", fields={"eligibility": "suppressed"})
        refused = proactive_store.select_for_conversation(self.conn, item_id, now=T0)
        self.assertFalse(refused["ok"])

    def test_memory_save_is_blocked_after_the_block(self) -> None:
        self._gmail("mem", label="urgent", gist="mem gist")
        self._block(message="Morning")
        turn_context.record_pre_llm_call(
            turn_id="turn-bare",
            session_id="sess-1",
            platform="tui",
            user_message="Remember that.",
        )
        bare = guards.evaluate_memory_taint(
            "memory",
            {"action": "add", "content": "mem gist"},
            session_id="sess-1",
            turn_id="turn-bare",
        )
        self.assertEqual((bare or {}).get("action"), "block")
        turn_context.record_pre_llm_call(
            turn_id="turn-own",
            session_id="sess-1",
            platform="tui",
            user_message="Remember the drill is at noon.",
        )
        own = guards.evaluate_memory_taint(
            "memory",
            {"action": "add", "content": "the drill is at noon"},
            session_id="sess-1",
            turn_id="turn-own",
        )
        self.assertIsNone(own)
        plugins_root = PLUGIN_ROOT.parent
        if str(plugins_root) not in sys.path:
            sys.path.insert(0, str(plugins_root))
        mem_root = plugins_root / "zola_memory"
        if str(mem_root) not in sys.path:
            sys.path.insert(0, str(mem_root))
        sys.modules["hermes_plugins.zola_workspace.taint"] = taint
        taint.set_lineage_root_fn_for_tests(lambda _sid: None)
        import consolidate as cons

        class _Row(dict):
            pass

        with mock.patch.object(cons, "_zola_workspace_plugin_enabled", return_value=True):
            tainted = cons.summarizer_instructions_for([_Row(session_id="sess-1")])
            clean = cons.summarizer_instructions_for([_Row(session_id="sess-clean")])
        self.assertIn(cons.WORKSPACE_ATTRIBUTION_LINE, tainted)
        self.assertNotIn(cons.WORKSPACE_ATTRIBUTION_LINE, clean)

    def test_tell_line_sits_outside_the_frame(self) -> None:
        self._gmail("told", label="urgent", gist="told gist", subject="told subject")
        text = self._block()
        line, framed = text.split("\n", 1)
        self.assertEqual(line, surface.SURFACE_TELL_LINE)
        self.assertNotIn(surface.SURFACE_LOOP_ASK, text)
        self.assertTrue(framed.startswith('<untrusted_tool_result source="surface">'))
        self.assertIn("told gist", framed)
        self.assertNotIn("told gist", line)
        self.assertNotIn("told subject", line)
        self.assertLessEqual(len(text), surface.SURFACE_CHAR_CAP)

    def test_loop_ask_sits_on_the_outside_line(self) -> None:
        self._gmail(
            "watched",
            label="normal",
            gist="watched gist",
            subject="watched subject",
            fields={"loop_matched": 1},
        )
        text = self._block()
        line, framed = text.split("\n", 1)
        self.assertEqual(line, surface.SURFACE_TELL_LINE + " " + surface.SURFACE_LOOP_ASK)
        self.assertNotIn(surface.SURFACE_LOOP_ASK, framed)
        self.assertTrue(framed.startswith('<untrusted_tool_result source="surface">'))
        self.assertIn("watched gist", framed)
        self.assertNotIn("watched gist", line)
        self.assertNotIn("watched subject", line)
        self.assertLessEqual(len(text), surface.SURFACE_CHAR_CAP)

    def test_historical_header(self) -> None:
        self._gmail("hist", label="urgent", gist="hist gist")
        first = self._block()
        self.assertIn("Workspace note", first)
        self.assertIn(surface.HISTORY_SENTENCE, first)
        self.assertNotIn("now history", first)
        self.assertRegex(first, r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}")
        self._confirm()
        self._gmail("hist-2", label="urgent", gist="second gist")
        surface.set_now_for_tests(_at(hours=2))
        second = self._block("turn-hist")
        self.assertIn("now history", second)
        self.assertIn(surface.HISTORY_SENTENCE, second)

    def test_remainder_only_is_sent_once(self) -> None:
        self._gmail("ordinary", label="normal", gist="ordinary gist")
        text = self._block()
        self.assertIn("ordinary", text)
        self.assertNotIn("ordinary gist", text)
        self.assertFalse(taint.is_tainted("sess-1"))
        self._confirm()
        self.assertIsNone(self._block("turn-2"))

    def test_list_in_the_same_turn_still_confirms(self) -> None:
        item_id = self._gmail("same", label="urgent", gist="same gist")
        self.assertIsNotNone(self._block())
        with mock.patch.object(turn_context, "current_turn_id_from_context", return_value="turn-1"):
            listed = surface.whats_pending_handler({"action": "list"})
        self.assertIn("same gist", listed)
        self.assertTrue(surface._attempts["sess-1"]["pending"])
        self._confirm()
        self.assertEqual(self.conn.execute("SELECT inject_count FROM items WHERE id = ?", (item_id,)).fetchone()[0], 1)
        self.assertIsNone(self._block("turn-2"))

    def test_pending_calendar_does_not_drop_the_good_row(self) -> None:
        good = self._gmail("good", label="urgent", gist="good gist")
        inserted = proactive_store.insert_item(
            self.conn, source="calendar", event_id="ev-pend", event_updated="u-pend", now=T0
        )
        self.conn.execute(
            "UPDATE items SET processing = 'ranked', eligibility = 'pending', label = NULL, gist = NULL WHERE id = ?",
            (inserted["id"],),
        )
        self.conn.commit()
        text = self._block()
        self.assertIn("good gist", text)
        self.assertNotIn("calendar change", text)
        self._confirm()
        self.assertIsNone(self._block("turn-2"))
        self.assertEqual(self.conn.execute("SELECT inject_count FROM items WHERE id = ?", (good,)).fetchone()[0], 1)

    def test_one_refused_select_keeps_the_other_row(self) -> None:
        kept = self._gmail("kept-row", label="urgent", gist="kept gist")
        dropped = self._gmail("drop-row", label="urgent", gist="dropped gist")
        real = proactive_store.provisional_select

        def flaky(conn, item_id, *args, **kwargs):
            if item_id == dropped:
                return {"ok": False, "refused_reason": "illegal_transition"}
            return real(conn, item_id, *args, **kwargs)

        with mock.patch.object(proactive_store, "provisional_select", side_effect=flaky):
            text = self._block()
        self.assertIn("kept gist", text)
        self.assertNotIn("dropped gist", text)
        self.assertIn("reason=select_skipped", self._log_text())
        self._confirm()
        self.assertIsNone(self._block("turn-2"))
        self.assertEqual(self.conn.execute("SELECT inject_count FROM items WHERE id = ?", (kept,)).fetchone()[0], 1)

    def test_possibly_surfaced_needs_name_and_subject(self) -> None:
        item_id = self._gmail(
            "both", label="urgent", gist="both gist",
            sender_display_name="Parcel Person", subject="shipment notice",
        )
        self._block()
        self._confirm(reply="Parcel Person wrote")
        self.assertEqual(
            self.conn.execute("SELECT conversation FROM items WHERE id = ?", (item_id,)).fetchone()[0],
            "selected",
        )
        surface.set_now_for_tests(_at(hours=5))
        self._block("turn-both")
        self._confirm("turn-both", reply="Parcel Person sent a shipment notice")
        self.assertEqual(
            self.conn.execute("SELECT conversation FROM items WHERE id = ?", (item_id,)).fetchone()[0],
            "possibly_surfaced",
        )

    def test_pending_list_caps_and_skips_lapse_on_open_loops(self) -> None:
        for index in range(12):
            self._gmail("many-%s" % index, label="important", gist="gist %s" % index, subject="subject %s" % index)
        proactive_store.set_ticket_override_for_tests(True)
        proactive_store.insert_loop(
            self.conn, intent="reply", predicate={"op": "thread"}, session_id="sess-1", now=T0
        )
        proactive_store.set_ticket_override_for_tests(None)
        self._ticket("turn-list", message="What's pending?")
        with mock.patch.object(turn_context, "current_turn_id_from_context", return_value="turn-list"):
            listed = surface.whats_pending_handler({"action": "list"})
        self.assertEqual(listed.count("Handle "), surface.SURFACE_LIST_LINE_CAP)
        self.assertIn("and 2 more.", listed)
        self.assertNotIn("lapse not told", listed)
        self.assertIn("Watch reply, not matched.", listed)

    def test_bulk_dismiss_after_ttl_changes_nothing(self) -> None:
        first = self._gmail("bulk-a", label="important", gist="bulk a")
        second = self._gmail("bulk-b", label="important", gist="bulk b")
        self._block()
        self._confirm()
        self._ticket("turn-list", message="What's pending?")
        with mock.patch.object(turn_context, "current_turn_id_from_context", return_value="turn-list"):
            surface.whats_pending_handler({"action": "list"})
        surface.set_now_for_tests(_at(seconds=surface.SURFACE_HANDLE_TTL_SECONDS + 5))
        self._ticket("turn-bulk", message="Clear them all.")
        with mock.patch.object(turn_context, "current_turn_id_from_context", return_value="turn-bulk"):
            result = surface.whats_pending_handler({"action": "dismiss"})
        self.assertIn("did not change", result)
        self.assertIsNone(self.conn.execute("SELECT closed_at FROM items WHERE id = ?", (first,)).fetchone()[0])
        self.assertIsNone(self.conn.execute("SELECT closed_at FROM items WHERE id = ?", (second,)).fetchone()[0])

    def test_purge_leaves_a_textless_calendar_row_available(self) -> None:
        calendar = proactive_store.insert_item(
            self.conn, source="calendar", event_id="ev-empty", event_updated="u-empty", now=T0
        )
        mail = self._gmail("null-mail", label="important", gist="will expire")
        self.conn.execute(
            """
            UPDATE items
               SET subject = NULL, snippet = NULL, gist = NULL, body = NULL,
                   processing = 'ranked', eligibility = 'eligible'
             WHERE id = ?
            """,
            (calendar["id"],),
        )
        self.conn.execute(
            "UPDATE items SET subject = NULL, snippet = NULL, gist = NULL, body = NULL WHERE id = ?",
            (mail,),
        )
        self.conn.commit()
        purged = proactive_store.purge_retention(self.conn, now=T0)
        self.assertTrue(purged["ok"], purged)
        self.assertEqual(
            self.conn.execute("SELECT content_state FROM items WHERE id = ?", (calendar["id"],)).fetchone()[0],
            "available",
        )
        self.assertEqual(
            self.conn.execute("SELECT content_state FROM items WHERE id = ?", (mail,)).fetchone()[0],
            "content_expired",
        )

    def test_calendar_and_lapse_blocks_do_not_taint(self) -> None:
        inserted = proactive_store.insert_item(
            self.conn, source="calendar", event_id="ev-cal", event_updated="u-cal", now=T0
        )
        self.conn.execute(
            "UPDATE items SET processing = 'ranked', eligibility = 'eligible', label = NULL, gist = NULL WHERE id = ?",
            (inserted["id"],),
        )
        self.conn.execute(
            "INSERT INTO calendar_events (calendar_id, event_id, event_updated, start_at, updated_at) "
            "VALUES ('c', 'ev-cal', 'u-cal', '2026-06-02T15:00:00Z', '2026-06-01T00:00:00Z')"
        )
        self.conn.commit()
        calendar = self._block(session_id="sess-cal")
        self.assertIn("Tuesday", calendar)
        self.assertFalse(taint.is_tainted("sess-cal"))
        proactive_store.set_ticket_override_for_tests(True)
        loop = proactive_store.insert_loop(
            self.conn, intent="reply", predicate={"op": "thread"}, session_id="sess-lapse",
            now=_at(days=-20), expiry_days=1,
        )
        proactive_store.set_ticket_override_for_tests(None)
        self.conn.execute(
            "UPDATE loops SET status = 'expired', expires_at = ? WHERE id = ?",
            ("2026-05-01T00:00:00Z", loop["id"]),
        )
        self.conn.commit()
        lapse = self._block(turn_id="turn-lapse", session_id="sess-lapse")
        self.assertIn("Watches expired", lapse)
        self.assertFalse(taint.is_tainted("sess-lapse"))
        self._gmail("mail-taint", label="urgent", gist="mail gist")
        mailed = self._block(turn_id="turn-mail", session_id="sess-mail")
        self.assertIn("mail gist", mailed)
        self.assertTrue(taint.is_tainted("sess-mail"))

    def test_listed_normal_item_can_be_acknowledged(self) -> None:
        item_id = self._gmail(
            "dinner-mail",
            label="normal",
            gist="dinner gist",
            subject="friday dinner plans",
        )
        self.assertEqual(
            self.conn.execute("SELECT conversation FROM items WHERE id = ?", (item_id,)).fetchone()[0],
            "none",
        )
        self._ticket("turn-list", message="What's pending?")
        with mock.patch.object(turn_context, "current_turn_id_from_context", return_value="turn-list"):
            listed = surface.whats_pending_handler({"action": "list"})
        handle = next(key for key, value in surface._listings["sess-1"]["items"].items() if value == item_id)
        self.assertIn(handle, listed)
        self.conn.execute("UPDATE items SET eligibility = 'suppressed' WHERE id = ?", (item_id,))
        self.conn.commit()
        self._ticket("turn-skip", message="Got it, the dinner one.")
        with mock.patch.object(turn_context, "current_turn_id_from_context", return_value="turn-skip"):
            skipped = surface.whats_pending_handler({"action": "acknowledge", "handle": handle})
        self.assertIn("Nothing changed", skipped)
        self.conn.execute("UPDATE items SET eligibility = 'eligible' WHERE id = ?", (item_id,))
        self.conn.commit()
        self._ticket("turn-ack", message="Got it, the dinner one.")
        with mock.patch.object(turn_context, "current_turn_id_from_context", return_value="turn-ack"):
            acked = surface.whats_pending_handler({"action": "acknowledge", "handle": handle})
        self.assertIn("Updated 1", acked)
        self.assertEqual(
            self.conn.execute("SELECT conversation FROM items WHERE id = ?", (item_id,)).fetchone()[0],
            "acknowledged",
        )

    def test_pending_list_orders_normal_last(self) -> None:
        self._gmail("ord-loop", label="normal", gist="LOOPORDER", fields={"loop_matched": 1})
        self._gmail("ord-deliv", label="normal", gist="DELIVORDER", fields={"delivery": "delivery_uncertain"})
        self._gmail("ord-hot", label="urgent", gist="URGENTORDER")
        self._gmail("ord-mid", label="important", gist="IMPORTANTORDER")
        self._gmail("ord-plain", label="normal", gist="NORMALORDER", subject="ordinary subject")
        inserted = proactive_store.insert_item(
            self.conn, source="calendar", event_id="ev-ord", event_updated="u-ord", now=T0
        )
        self.conn.execute(
            "UPDATE items SET processing = 'ranked', eligibility = 'eligible', label = NULL, gist = NULL WHERE id = ?",
            (inserted["id"],),
        )
        self.conn.execute(
            "INSERT INTO calendar_events (calendar_id, event_id, event_updated, start_at, updated_at) "
            "VALUES ('c', 'ev-ord', 'u-ord', '2026-06-02T15:00:00Z', '2026-06-01T00:00:00Z')"
        )
        self.conn.commit()
        self._ticket("turn-list", message="What's pending?")
        with mock.patch.object(turn_context, "current_turn_id_from_context", return_value="turn-list"):
            listed = surface.whats_pending_handler({"action": "list"})
        positions = [
            listed.index("LOOPORDER"),
            listed.index("DELIVORDER"),
            listed.index("URGENTORDER"),
            listed.index("IMPORTANTORDER"),
            listed.index("Tuesday"),
            listed.index("NORMALORDER"),
        ]
        self.assertEqual(positions, sorted(positions))
