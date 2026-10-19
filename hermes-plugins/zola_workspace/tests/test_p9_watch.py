"""P9-WATCH Phase 4. Fakes only. Synthetic content. No live Google."""

from __future__ import annotations

import ast
import json
import logging
import os
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

import auth
import background_read
import google_http
import loops
import proactive_store
import watcher

# P9-WATCH: suites and their child processes take private mutexes — P9-D04
_TEST_INSTANCE_MUTEX = "Local\\ZolaWatcherTest"
_TEST_REFRESH_MUTEX = "Local\\ZolaOAuthRefreshTest"
auth.set_refresh_mutex_name_for_tests(_TEST_REFRESH_MUTEX)
watcher.set_instance_mutex_name_for_tests(_TEST_INSTANCE_MUTEX)

T0 = datetime(2026, 6, 1, tzinfo=timezone.utc)
SUBJECT = "SYNTHETIC_SUBJECT"
ADDRESS = "synthetic@example.com"
PROFILE_ADDRESS = "profile-synthetic@example.com"
TITLE = "SYNTHETIC_TITLE"
FORBIDDEN = (SUBJECT, ADDRESS, PROFILE_ADDRESS, TITLE)


class _Fake:
    def __init__(self) -> None:
        self.calls = []
        self.params = []
        self.profile_id = "h-1"
        self.history_status = 200
        self.history_added = []
        self.history_id = "h-2"
        self.messages = {}
        self.fail_messages = set()
        self.transport_fail = False
        self.recovery = []
        self.calendars = [{"id": "cal-1", "selected": True}, {"id": "cal-skip", "selected": False}]
        self.event_pages = {"cal-1": [{"items": [], "nextSyncToken": "sync-1"}]}
        self.event_index = {}
        self.gone_on_sync = False

    def __call__(self, method, url, **kwargs):
        path = urlparse(url).path
        params = kwargs.get("params") or {}
        self.calls.append(path)
        self.params.append(dict(params))
        if self.transport_fail and path.endswith("/messages/" + path.rsplit("/", 1)[-1]) and "/history" not in path:
            if not path.endswith("/messages"):
                raise google_http.GoogleHttpTransportError("transport_error")
        if path.endswith("/profile"):
            return google_http.GoogleHttpResponse(
                200,
                json.dumps({"historyId": self.profile_id, "emailAddress": PROFILE_ADDRESS}),
            )
        if path.endswith("/history"):
            if self.history_status != 200:
                return google_http.GoogleHttpResponse(self.history_status, "")
            history = []
            for item in self.history_added:
                history.append(
                    {"messagesAdded": [{"message": {"id": item["id"], "threadId": item["thread"]}}]}
                )
            return google_http.GoogleHttpResponse(
                200,
                json.dumps(
                    {
                        "history": history,
                        "historyId": self.history_id,
                        "nextPageToken": "",
                    }
                ),
            )
        if "/messages/" in path:
            message_id = path.rsplit("/", 1)[-1]
            if message_id in self.fail_messages:
                return google_http.GoogleHttpResponse(404, "")
            if self.transport_fail:
                raise google_http.GoogleHttpTransportError("transport_error")
            payload = self.messages.get(message_id) or {}
            return google_http.GoogleHttpResponse(200, json.dumps(payload))
        if path.endswith("/messages"):
            return google_http.GoogleHttpResponse(
                200,
                json.dumps({"messages": self.recovery, "nextPageToken": ""}),
            )
        if path.endswith("/calendarList"):
            return google_http.GoogleHttpResponse(
                200,
                json.dumps({"items": self.calendars}),
            )
        if path.endswith("/events"):
            if self.gone_on_sync and params.get("syncToken"):
                return google_http.GoogleHttpResponse(410, "")
            calendar_id = unquote(path.split("/calendars/")[1].split("/events")[0])
            pages = self.event_pages.get(calendar_id) or [{"items": [], "nextSyncToken": "sync-x"}]
            index = self.event_index.get(calendar_id, 0)
            if index >= len(pages):
                raise google_http.GoogleHttpTransportError("transport_error")
            page = pages[index]
            self.event_index[calendar_id] = index + 1
            if page.get("fail"):
                raise google_http.GoogleHttpTransportError("transport_error")
            return google_http.GoogleHttpResponse(200, json.dumps(page))
        return google_http.GoogleHttpResponse(404, "")


def _message(message_id: str, thread_id: str, address: str = ADDRESS, internal_ms: str = "") -> dict:
    raw = __import__("base64").urlsafe_b64encode(b"hello").decode().rstrip("=")
    payload = {
        "id": message_id,
        "threadId": thread_id,
        "labelIds": ["INBOX"],
        "snippet": "synthetic snippet",
        "payload": {
            "mimeType": "text/plain",
            "headers": [
                {"name": "From", "value": f"Synthetic <{address}>"},
                {"name": "Subject", "value": SUBJECT},
            ],
            "body": {"data": raw},
        },
    }
    if internal_ms:
        payload["internalDate"] = internal_ms
    return payload


def _event(event_id: str, updated: str, status: str = "confirmed", recurring: str = "") -> dict:
    payload = {
        "id": event_id,
        "updated": updated,
        "status": status,
        "summary": TITLE,
        "start": {"dateTime": "2026-06-02T15:00:00Z"},
        "end": {"dateTime": "2026-06-02T16:00:00Z"},
    }
    if recurring:
        payload["recurringEventId"] = recurring
    return payload


class WatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self._dir = tempfile.TemporaryDirectory(prefix="p9watch_")
        self.path = Path(self._dir.name) / "proactive.db"
        self.fake = _Fake()
        google_http.set_transport_for_tests(self.fake)
        self._header = mock.patch.object(
            auth, "authorization_header", return_value={"Authorization": "Bearer synthetic"}
        )
        self._header.start()
        self._status = mock.patch.object(
            auth,
            "store_status",
            return_value={"connected": True, "needs_reconnect": None, "missing_scopes": []},
        )
        self._status.start()
        proactive_store.set_ticket_override_for_tests(True)
        proactive_store.set_db_path_for_tests(self.path)
        self.conn = proactive_store.connect(self.path, retry=False)
        self.records = []
        self._logger = logging.getLogger("zola_watcher")
        self._logger.setLevel(logging.INFO)
        self._handler = logging.Handler()
        self._handler.emit = lambda record: self.records.append(record)
        self._logger.addHandler(self._handler)

    def tearDown(self) -> None:
        self._logger.removeHandler(self._handler)
        self.conn.close()
        google_http.reset_transport_for_tests()
        self._header.stop()
        self._status.stop()
        auth.reset_auth_runtime_for_tests()
        proactive_store.set_db_path_for_tests(None)
        proactive_store.set_ticket_override_for_tests(None)
        self._dir.cleanup()

    def _logs(self) -> str:
        return "\n".join(record.getMessage() for record in self.records)

    def _assert_logs_clean(self) -> None:
        text = self._logs()
        for token in FORBIDDEN:
            self.assertNotIn(token, text)

    def _deliver(self, item_id: str) -> None:
        row = proactive_store._item(self.conn, item_id)
        if row["source"] == "calendar":
            done = proactive_store.rank_calendar(self.conn, item_id, now=T0)
            self.assertTrue(done["ok"], done)
        else:
            claimed = proactive_store.claim_rank(self.conn, item_id, now=T0)
            self.assertTrue(claimed["ok"], claimed)
            done = proactive_store.complete_rank(
                self.conn, item_id, claimed["attempt_id"], label="normal", gist="g", now=T0
            )
            self.assertTrue(done["ok"], done)
        if proactive_store._item(self.conn, item_id)["eligibility"] == "pending":
            self.assertTrue(proactive_store.mark_eligible(self.conn, item_id, now=T0)["ok"])
        self.assertTrue(proactive_store.set_loop_matched(self.conn, item_id, now=T0)["ok"])
        speech = proactive_store.claim_speech(self.conn, item_id, now=T0)
        self.assertTrue(speech["ok"], speech)
        self.assertTrue(
            proactive_store.mark_speech_started(self.conn, item_id, speech["attempt_id"], now=T0)["ok"]
        )
        self.assertTrue(
            proactive_store.mark_delivered(self.conn, item_id, speech["attempt_id"], now=T0)["ok"]
        )

    def test_source_scan_and_one_owner_imports(self) -> None:
        allowed_routes = {
            "ROUTE_GMAIL_PROFILE",
            "ROUTE_GMAIL_HISTORY",
            "ROUTE_GMAIL_LIST",
            "ROUTE_GMAIL_GET",
            "ROUTE_CALENDAR_LIST",
            "ROUTE_CALENDAR_EVENTS",
        }
        forbidden = {
            "gmail",
            "gcal",
            "contacts",
            "drive",
            "framing",
            "guards",
            "send_gate",
            "origin",
            "hermes_cli",
            "agent",
            "gateway",
        }
        for name in ("watcher.py", "background_read.py"):
            tree = ast.parse((PLUGIN_ROOT / name).read_text(encoding="utf-8"))
            routes = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertNotIn(alias.name.split(".")[0], forbidden)
                if isinstance(node, ast.ImportFrom):
                    module = (node.module or "").split(".")[0]
                    self.assertNotIn(module, forbidden)
                    for alias in node.names:
                        self.assertNotIn(alias.name, forbidden)
                if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                    if node.value.id == "google_http" and node.attr.startswith("ROUTE_"):
                        routes.add(node.attr)
            if name == "background_read.py":
                self.assertTrue(routes <= allowed_routes)
                self.assertIn("ROUTE_GMAIL_HISTORY", routes)

    def test_v2_upgrades_to_v3(self) -> None:
        self.conn.close()
        legacy = Path(self._dir.name) / "v2.db"
        raw = sqlite3.connect(legacy)
        proactive_store._migrate_v1(raw)
        proactive_store._migrate_v2(raw)
        raw.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        raw.execute("INSERT INTO meta (key, value) VALUES ('schema_version', '2')")
        raw.commit()
        raw.close()
        conn = proactive_store.connect(legacy, retry=False)
        version = conn.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()[0]
        self.assertEqual(version, str(proactive_store.SCHEMA_VERSION))
        self.assertIn("calendar_events", {row[0] for row in conn.execute("SELECT name FROM sqlite_master")})
        self.assertIn("watcher_rejects", {row[0] for row in conn.execute("SELECT name FROM sqlite_master")})
        columns = {row[1] for row in conn.execute("PRAGMA table_info(watcher_health)")}
        self.assertIn("gmail_ok_at", columns)
        self.assertIn("recovery_count", columns)
        conn.close()

    def test_gmail_baseline_stores_history_id_only(self) -> None:
        result = watcher.run_gmail(self.conn, now=T0)
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["new"], 0)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM items").fetchone()[0], 0)
        cursor = self.conn.execute("SELECT cursor_value FROM cursors").fetchone()[0]
        self.assertEqual(cursor, "h-1")
        blob = Path(self.path).read_bytes()
        self.assertNotIn(PROFILE_ADDRESS.encode(), blob)
        self._assert_logs_clean()

    def test_reply_matches_other_thread_does_not_and_replay_is_once(self) -> None:
        watcher.run_gmail(self.conn, now=T0)
        address_hash = proactive_store.address_hash(ADDRESS)
        proactive_store.insert_loop(
            self.conn,
            intent="reply",
            predicate={
                "op": "all",
                "args": [
                    {"op": "gmail_thread", "thread_id": "thread-good"},
                    {"op": "sender_is", "address_hash": address_hash},
                    {"op": "after", "at": "2020-01-01T00:00:00Z"},
                ],
            },
            session_id="sess",
            expiry_days=7,
            now=T0,
        )
        self.fake.history_added = [{"id": "m-other", "thread": "thread-other"}]
        self.fake.messages["m-other"] = _message("m-other", "thread-other")
        self.fake.history_id = "h-3"
        other = watcher.run_gmail(self.conn, now=T0)
        self.assertEqual(other["new"], 1)
        self.assertIsNone(self.conn.execute("SELECT matched_at FROM loops").fetchone()[0])
        self.fake.history_added = [{"id": "m-good", "thread": "thread-good"}]
        self.fake.messages["m-good"] = _message("m-good", "thread-good", internal_ms="1780272000000")
        self.fake.history_id = "h-4"
        good = watcher.run_gmail(self.conn, now=T0)
        self.assertEqual(good["new"], 1)
        row = self.conn.execute("SELECT status, matched_at FROM loops").fetchone()
        self.assertEqual(row["status"], "open")
        self.assertIsNotNone(row["matched_at"])
        item = self.conn.execute(
            "SELECT eligibility, loop_matched FROM items WHERE message_id = 'm-good'"
        ).fetchone()
        self.assertEqual(item["eligibility"], "eligible")
        self.assertEqual(item["loop_matched"], 1)
        stamped = row["matched_at"]
        self.fake.history_id = "h-4"
        self.conn.execute("UPDATE cursors SET cursor_value = 'h-3'")
        self.conn.commit()
        again = watcher.run_gmail(self.conn, now=T0)
        self.assertEqual(again["new"], 0)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM items").fetchone()[0], 2)
        self.assertEqual(self.conn.execute("SELECT matched_at FROM loops").fetchone()[0], stamped)
        self._assert_logs_clean()

    def test_crash_before_evaluation_records_the_match_once(self) -> None:
        watcher.run_gmail(self.conn, now=T0)
        proactive_store.insert_loop(
            self.conn,
            intent="reply",
            predicate={
                "op": "all",
                "args": [
                    {"op": "gmail_thread", "thread_id": "thread-good"},
                    {"op": "sender_is", "address_hash": proactive_store.address_hash(ADDRESS)},
                    {"op": "after", "at": "2020-01-01T00:00:00Z"},
                ],
            },
            session_id="sess",
            expiry_days=7,
            now=T0,
        )
        self.fake.history_added = [{"id": "m-crash", "thread": "thread-good"}]
        self.fake.messages["m-crash"] = _message("m-crash", "thread-good", internal_ms="1780272000000")
        self.fake.history_id = "h-9"
        original = loops.evaluate
        calls = {"n": 0}

        def boom(predicate, item):
            calls["n"] += 1
            if calls["n"] == 1:
                raise RuntimeError("boom")
            return original(predicate, item)

        with mock.patch.object(loops, "evaluate", boom):
            held = watcher.run_gmail(self.conn, now=T0)
        self.assertTrue(held.get("held"), held)
        self.assertEqual(self.conn.execute("SELECT cursor_value FROM cursors").fetchone()[0], "h-1")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM items").fetchone()[0], 1)
        self.assertIsNone(self.conn.execute("SELECT matched_at FROM loops").fetchone()[0])
        again = watcher.run_gmail(self.conn, now=T0)
        self.assertTrue(again["ok"], again)
        self.assertEqual(again["new"], 0)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM items").fetchone()[0], 1)
        self.assertIsNotNone(self.conn.execute("SELECT matched_at FROM loops").fetchone()[0])
        self.assertEqual(
            self.conn.execute("SELECT loop_matched FROM items").fetchone()[0],
            1,
        )

    def test_old_message_seen_after_the_loop_does_not_match(self) -> None:
        watcher.run_gmail(self.conn, now=T0)
        address_hash = proactive_store.address_hash(ADDRESS)
        proactive_store.insert_loop(
            self.conn,
            intent="reply",
            predicate={
                "op": "all",
                "args": [
                    {"op": "gmail_thread", "thread_id": "thread-good"},
                    {"op": "sender_is", "address_hash": address_hash},
                    {"op": "after", "at": "2026-06-01T00:00:00Z"},
                ],
            },
            session_id="sess",
            expiry_days=7,
            now=T0,
        )
        before = str(int(datetime(2026, 5, 1, tzinfo=timezone.utc).timestamp() * 1000))
        after = str(int(datetime(2026, 6, 2, tzinfo=timezone.utc).timestamp() * 1000))
        self.fake.history_added = [{"id": "m-old", "thread": "thread-good"}]
        self.fake.messages["m-old"] = _message("m-old", "thread-good", internal_ms=before)
        self.fake.history_id = "h-old"
        ingested = watcher.run_gmail(self.conn, now=T0)
        self.assertEqual(ingested["new"], 1)
        self.assertIsNone(self.conn.execute("SELECT matched_at FROM loops").fetchone()[0])
        self.fake.history_added = [{"id": "m-reply", "thread": "thread-good"}]
        self.fake.messages["m-reply"] = _message("m-reply", "thread-good", internal_ms=after)
        self.fake.history_id = "h-reply"
        replied = watcher.run_gmail(self.conn, now=T0)
        self.assertEqual(replied["new"], 1)
        self.assertIsNotNone(self.conn.execute("SELECT matched_at FROM loops").fetchone()[0])
        matched = {
            row[0]
            for row in self.conn.execute(
                "SELECT message_id FROM items WHERE loop_matched = 1"
            )
        }
        self.assertEqual(matched, {"m-reply"})

    def test_partial_get_holds_the_cursor(self) -> None:
        watcher.run_gmail(self.conn, now=T0)
        self.fake.history_added = [
            {"id": "m-1", "thread": "t-1"},
            {"id": "m-2", "thread": "t-2"},
        ]
        self.fake.messages["m-1"] = _message("m-1", "t-1")
        self.fake.messages["m-2"] = _message("m-2", "t-2")
        self.fake.history_id = "h-5"
        self.fake.transport_fail = True
        # First message is fetched before the flag is general. Fail only m-2 via transport after m-1.
        self.fake.transport_fail = False
        self.fake.fail_messages = set()

        def flaky(method, url, **kwargs):
            path = urlparse(url).path
            if path.endswith("/m-2"):
                raise google_http.GoogleHttpTransportError("transport_error")
            return _Fake.__call__(self.fake, method, url, **kwargs)

        self.fake.transport_fail = False
        google_http.set_transport_for_tests(flaky)
        held = watcher.run_gmail(self.conn, now=T0)
        self.assertTrue(held.get("held"), held)
        self.assertEqual(self.conn.execute("SELECT cursor_value FROM cursors").fetchone()[0], "h-1")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM items").fetchone()[0], 1)
        google_http.set_transport_for_tests(self.fake)
        done = watcher.run_gmail(self.conn, now=T0)
        self.assertTrue(done["ok"], done)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM items").fetchone()[0], 2)
        self.assertEqual(self.conn.execute("SELECT cursor_value FROM cursors").fetchone()[0], "h-5")

    def test_deleted_message_is_terminal_then_the_cursor_advances(self) -> None:
        watcher.run_gmail(self.conn, now=T0)
        self.fake.history_added = [{"id": "m-gone", "thread": "t-gone"}]
        self.fake.fail_messages.add("m-gone")
        self.fake.history_id = "h-6"
        result = watcher.run_gmail(self.conn, now=T0)
        self.assertTrue(result["ok"], result)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM items").fetchone()[0], 0)
        self.assertEqual(self.conn.execute("SELECT cursor_value FROM cursors").fetchone()[0], "h-6")
        row = self.conn.execute("SELECT * FROM watcher_rejects").fetchone()
        self.assertEqual(row["disposition"], "terminal")
        self.assertEqual(row["attempts"], 1)
        self.assertEqual(row["error_class"], "http_404")
        self.assertNotIn("subject", row.keys())

    def test_transport_errors_stay_held_past_the_cap(self) -> None:
        watcher.run_gmail(self.conn, now=T0)
        self.fake.history_added = [{"id": "m-flake", "thread": "t-flake"}]
        self.fake.history_id = "h-7"

        def boom(method, url, **kwargs):
            if urlparse(url).path.endswith("/m-flake"):
                raise google_http.GoogleHttpTransportError("transport_error")
            return _Fake.__call__(self.fake, method, url, **kwargs)

        google_http.set_transport_for_tests(boom)
        for _ in range(6):
            held = watcher.run_gmail(self.conn, now=T0)
            self.assertTrue(held.get("held"), held)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM watcher_rejects").fetchone()[0], 0)
        self.assertEqual(self.conn.execute("SELECT cursor_value FROM cursors").fetchone()[0], "h-1")
        health = self.conn.execute("SELECT gmail_error FROM watcher_health").fetchone()[0]
        self.assertEqual(health, "transport")
        google_http.set_transport_for_tests(self.fake)
        self.fake.messages["m-flake"] = _message("m-flake", "t-flake")
        done = watcher.run_gmail(self.conn, now=T0)
        self.assertTrue(done["ok"], done)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM items").fetchone()[0], 1)
        self.assertEqual(self.conn.execute("SELECT cursor_value FROM cursors").fetchone()[0], "h-7")

    def test_history_404_recovery_skips_stored_ids(self) -> None:
        watcher.run_gmail(self.conn, now=T0)
        self.fake.history_added = [{"id": "m-old", "thread": "t-old"}]
        self.fake.messages["m-old"] = _message("m-old", "t-old")
        self.fake.history_id = "h-8"
        self.assertTrue(watcher.run_gmail(self.conn, now=T0)["ok"])
        self.fake.history_status = 404
        self.fake.recovery = [{"id": "m-old", "threadId": "t-old"}, {"id": "m-new", "threadId": "t-new"}]
        self.fake.messages["m-new"] = _message("m-new", "t-new")
        self.fake.profile_id = "h-10"
        recovered = watcher.run_gmail(self.conn, now=T0)
        self.assertTrue(recovered.get("recovery"), recovered)
        ids = {row[0] for row in self.conn.execute("SELECT message_id FROM items")}
        self.assertEqual(ids, {"m-old", "m-new"})
        self.assertEqual(self.conn.execute("SELECT cursor_value FROM cursors").fetchone()[0], "h-10")
        health = self.conn.execute("SELECT recovery_count FROM watcher_health").fetchone()[0]
        self.assertEqual(health, 1)
        self.assertNotIn(PROFILE_ADDRESS.encode(), Path(self.path).read_bytes())

    def test_sent_only_is_skipped_and_inbox_is_stored(self) -> None:
        watcher.run_gmail(self.conn, now=T0)
        sent = _message("m-sent", "t-sent")
        sent["labelIds"] = ["SENT"]
        both = _message("m-both", "t-both")
        both["labelIds"] = ["INBOX", "SENT"]
        self.fake.history_added = [
            {"id": "m-sent", "thread": "t-sent"},
            {"id": "m-in", "thread": "t-in"},
            {"id": "m-both", "thread": "t-both"},
        ]
        self.fake.messages["m-sent"] = sent
        self.fake.messages["m-in"] = _message("m-in", "t-in")
        self.fake.messages["m-both"] = both
        self.fake.history_id = "h-inbox"
        result = watcher.run_gmail(self.conn, now=T0)
        self.assertEqual(result["new"], 2, result)
        self.assertEqual(result["skipped_not_inbox"], 1)
        ids = {row[0] for row in self.conn.execute("SELECT message_id FROM items")}
        self.assertEqual(ids, {"m-in", "m-both"})
        self.assertEqual(self.conn.execute("SELECT cursor_value FROM cursors").fetchone()[0], "h-inbox")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM watcher_rejects").fetchone()[0], 0)
        self.assertIn("skipped_not_inbox=1", self._logs())
        self.fake.history_status = 404
        draft = _message("m-draft", "t-draft")
        draft["labelIds"] = ["DRAFT"]
        self.fake.recovery = [
            {"id": "m-draft", "threadId": "t-draft"},
            {"id": "m-back", "threadId": "t-back"},
        ]
        self.fake.messages["m-draft"] = draft
        self.fake.messages["m-back"] = _message("m-back", "t-back")
        self.fake.profile_id = "h-after"
        recovered = watcher.run_gmail(self.conn, now=T0)
        self.assertTrue(recovered.get("recovery"), recovered)
        ids = {row[0] for row in self.conn.execute("SELECT message_id FROM items")}
        self.assertEqual(ids, {"m-in", "m-both", "m-back"})
        self.assertEqual(self.conn.execute("SELECT cursor_value FROM cursors").fetchone()[0], "h-after")
        self.assertIn("skipped_not_inbox=1", self._logs())

    def test_recovery_keeps_the_history_id_from_before_the_list(self) -> None:
        watcher.run_gmail(self.conn, now=T0)
        self.fake.calls.clear()
        self.fake.params.clear()
        self.fake.history_status = 404
        self.fake.profile_id = "h-capture"
        old_ms = str(int((T0 - timedelta(days=3)).timestamp() * 1000))
        fresh_ms = str(int((T0 + timedelta(minutes=5)).timestamp() * 1000))
        self.fake.recovery = [
            {"id": "m-old-window", "threadId": "t-old"},
            {"id": "m-fresh", "threadId": "t-fresh"},
        ]
        self.fake.messages["m-old-window"] = _message("m-old-window", "t-old", internal_ms=old_ms)
        self.fake.messages["m-fresh"] = _message("m-fresh", "t-fresh", internal_ms=fresh_ms)
        recovered = watcher.run_gmail(self.conn, now=T0)
        self.assertTrue(recovered.get("recovery"), recovered)
        paths = [path for path in self.fake.calls]
        profile_at = next(i for i, path in enumerate(paths) if path.endswith("/profile"))
        list_at = next(i for i, path in enumerate(paths) if path.endswith("/messages"))
        self.assertLess(profile_at, list_at)
        ids = {row[0] for row in self.conn.execute("SELECT message_id FROM items")}
        self.assertEqual(ids, {"m-fresh"})
        self.assertEqual(self.conn.execute("SELECT cursor_value FROM cursors").fetchone()[0], "h-capture")
        self.fake.history_status = 200
        self.fake.history_added = [{"id": "m-during", "thread": "t-during"}]
        self.fake.messages["m-during"] = _message("m-during", "t-during", internal_ms=fresh_ms)
        self.fake.history_id = "h-next"
        followed = watcher.run_gmail(self.conn, now=T0)
        self.assertEqual(followed["new"], 1)
        history_params = [
            params
            for path, params in zip(self.fake.calls, self.fake.params)
            if path.endswith("/history")
        ]
        self.assertEqual(history_params[-1].get("startHistoryId"), "h-capture")
        self.assertIn("m-during", {row[0] for row in self.conn.execute("SELECT message_id FROM items")})

    def test_calendar_token_waits_for_the_last_page(self) -> None:
        self.fake.event_pages = {
            "cal-1": [
                {"items": [_event("evt-a", "u1")], "nextPageToken": "p2"},
                {"fail": True},
            ]
        }
        held = watcher.run_calendar(self.conn, now=T0)
        self.assertTrue(held.get("held"), held)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM cursors").fetchone()[0], 0)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM items").fetchone()[0], 0)
        self.fake.event_index = {}
        self.fake.event_pages = {
            "cal-1": [
                {"items": [_event("evt-a", "u1")], "nextPageToken": "p2"},
                {"items": [_event("evt-b", "u1")], "nextSyncToken": "sync-final"},
            ]
        }
        done = watcher.run_calendar(self.conn, now=T0)
        self.assertTrue(done["ok"], done)
        self.assertEqual(done["new"], 0)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM items").fetchone()[0], 0)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM calendar_events").fetchone()[0], 2)
        self.assertEqual(
            self.conn.execute("SELECT cursor_value FROM cursors").fetchone()[0],
            "sync-final",
        )
        for params in self.fake.params:
            keys = {key.lower() for key in params}
            self.assertNotIn("singleevents", keys)
            self.assertNotIn("timemin", keys)
            self.assertNotIn("timemax", keys)
            self.assertNotIn("orderby", keys)
            self.assertNotIn("q", keys)
        blob = Path(self.path).read_bytes()
        self.assertNotIn(TITLE.encode(), blob)

    def test_cancellation_of_a_delivered_event_is_a_second_item(self) -> None:
        self.fake.event_pages = {
            "cal-1": [{"items": [_event("evt-old", "u0")], "nextSyncToken": "sync-a"}]
        }
        self.assertTrue(watcher.run_calendar(self.conn, now=T0)["ok"])
        self.fake.event_index = {}
        self.fake.event_pages = {
            "cal-1": [{"items": [_event("evt-new", "u1")], "nextSyncToken": "sync-b"}]
        }
        created = watcher.run_calendar(self.conn, now=T0)
        self.assertEqual(created["new"], 1)
        first = self.conn.execute("SELECT id FROM items").fetchone()[0]
        self._deliver(first)
        proactive_store.insert_loop(
            self.conn,
            intent="cancelled",
            predicate={
                "op": "all",
                "args": [
                    {"op": "calendar_event", "event_id": "evt-new"},
                    {"op": "calendar_cancelled"},
                ],
            },
            session_id="sess",
            expiry_days=7,
            now=T0,
        )
        self.fake.event_index = {}
        self.fake.event_pages = {
            "cal-1": [
                {"items": [_event("evt-new", "u2", "cancelled")], "nextSyncToken": "sync-c"}
            ]
        }
        cancelled = watcher.run_calendar(self.conn, now=T0)
        self.assertEqual(cancelled["new"], 1)
        rows = self.conn.execute(
            "SELECT id, eligibility, loop_matched, processing, delivery, idempotency_key, calendar_status FROM items"
        ).fetchall()
        self.assertEqual(len(rows), 2)
        by_id = {row["id"]: row for row in rows}
        self.assertEqual(by_id[first]["delivery"], "delivered")
        second = [row for row in rows if row["id"] != first][0]
        self.assertEqual(second["processing"], "unranked")
        self.assertEqual(second["eligibility"], "eligible")
        self.assertEqual(second["loop_matched"], 1)
        self.assertIn(":u2", second["idempotency_key"])
        self.assertNotEqual(by_id[first]["idempotency_key"], second["idempotency_key"])
        loop = self.conn.execute("SELECT status, closed_intent FROM loops").fetchone()
        self.assertEqual(loop["status"], "closed")
        self.assertEqual(loop["closed_intent"], "cancelled")
        self.fake.event_index = {}
        replay = watcher.run_calendar(self.conn, now=T0)
        self.assertEqual(replay["new"], 0)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM items").fetchone()[0], 2)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM calendar_events WHERE event_id = 'evt-new'").fetchone()[0], 1)

    def test_recurring_events_follow_the_approved_key(self) -> None:
        self.fake.event_pages = {
            "cal-1": [
                {
                    "items": [
                        _event("series-1", "su1"),
                        _event("series-1_a", "iu1", recurring="series-1"),
                    ],
                    "nextSyncToken": "sync-r",
                }
            ]
        }
        self.assertEqual(watcher.run_calendar(self.conn, now=T0)["new"], 0)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM calendar_events").fetchone()[0], 2)
        self.fake.event_index = {}
        self.assertEqual(watcher.run_calendar(self.conn, now=T0)["new"], 0)
        self.fake.event_index = {}
        self.fake.event_pages = {
            "cal-1": [
                {
                    "items": [
                        _event("series-1", "su2"),
                        _event("series-1_a", "iu1", recurring="series-1"),
                    ],
                    "nextSyncToken": "sync-r2",
                }
            ]
        }
        self.assertEqual(watcher.run_calendar(self.conn, now=T0)["new"], 0)
        self.assertEqual(
            self.conn.execute(
                "SELECT event_updated FROM calendar_events WHERE event_id = 'series-1'"
            ).fetchone()[0],
            "su2",
        )
        self.fake.event_index = {}
        self.fake.event_pages = {
            "cal-1": [
                {
                    "items": [_event("series-1_b", "iu2", recurring="series-1")],
                    "nextSyncToken": "sync-r3",
                }
            ]
        }
        modified = watcher.run_calendar(self.conn, now=T0)
        self.assertEqual(modified["new"], 1)
        proactive_store.insert_loop(
            self.conn,
            intent="cancelled",
            predicate={
                "op": "all",
                "args": [
                    {"op": "calendar_event", "event_id": "series-1_a"},
                    {"op": "calendar_cancelled"},
                ],
            },
            session_id="sess",
            expiry_days=7,
            now=T0,
        )
        self.fake.event_index = {}
        self.fake.event_pages = {
            "cal-1": [
                {
                    "items": [_event("series-1_a", "iu3", "cancelled", recurring="series-1")],
                    "nextSyncToken": "sync-r4",
                }
            ]
        }
        cancelled = watcher.run_calendar(self.conn, now=T0)
        self.assertEqual(cancelled["new"], 1)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM calendar_events").fetchone()[0], 3)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM items").fetchone()[0], 2)

    def test_calendar_410_rebaseline_adds_no_item(self) -> None:
        self.fake.event_pages = {
            "cal-1": [{"items": [_event("evt-a", "u1")], "nextSyncToken": "sync-old"}]
        }
        self.assertTrue(watcher.run_calendar(self.conn, now=T0)["ok"])
        self.fake.event_index = {}
        self.fake.gone_on_sync = True
        self.fake.event_pages = {
            "cal-1": [
                {
                    "items": [_event("evt-a", "u1"), _event("evt-during-gap", "u9")],
                    "nextSyncToken": "sync-new",
                }
            ]
        }
        recovered = watcher.run_calendar(self.conn, now=T0)
        self.assertTrue(recovered["ok"], recovered)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM items").fetchone()[0], 0)
        self.assertEqual(self.conn.execute("SELECT cursor_value FROM cursors").fetchone()[0], "sync-new")
        self.assertEqual(self.conn.execute("SELECT recovery_count FROM watcher_health").fetchone()[0], 1)

    def test_resync_of_a_known_cancellation_matches_the_loop(self) -> None:
        self.fake.event_pages = {
            "cal-1": [{"items": [_event("evt-e", "u1")], "nextSyncToken": "sync-old"}]
        }
        self.assertTrue(watcher.run_calendar(self.conn, now=T0)["ok"])
        proactive_store.insert_loop(
            self.conn,
            intent="cancelled",
            predicate={
                "op": "all",
                "args": [
                    {"op": "calendar_event", "event_id": "evt-e"},
                    {"op": "calendar_cancelled"},
                ],
            },
            session_id="sess",
            expiry_days=7,
            now=T0,
        )
        self.fake.event_index = {}
        self.fake.gone_on_sync = True
        self.fake.event_pages = {
            "cal-1": [{"items": [_event("evt-e", "u2", "cancelled")], "nextSyncToken": "sync-new"}]
        }
        recovered = watcher.run_calendar(self.conn, now=T0)
        self.assertTrue(recovered["ok"], recovered)
        self.assertEqual(recovered["new"], 1)
        item = self.conn.execute(
            "SELECT eligibility, loop_matched FROM items"
        ).fetchone()
        self.assertEqual(item["eligibility"], "eligible")
        self.assertEqual(item["loop_matched"], 1)
        loop = self.conn.execute("SELECT status, closed_intent FROM loops").fetchone()
        self.assertEqual(loop["status"], "closed")
        self.assertEqual(loop["closed_intent"], "cancelled")

    def test_resync_crash_stays_in_recovery(self) -> None:
        self.fake.event_pages = {
            "cal-1": [
                {
                    "items": [_event("evt-e", "u1"), _event("evt-keep", "u1")],
                    "nextSyncToken": "sync-old",
                }
            ]
        }
        self.assertEqual(watcher.run_calendar(self.conn, now=T0)["new"], 0)
        proactive_store.insert_loop(
            self.conn,
            intent="cancelled",
            predicate={
                "op": "all",
                "args": [
                    {"op": "calendar_event", "event_id": "evt-e"},
                    {"op": "calendar_cancelled"},
                ],
            },
            session_id="sess",
            expiry_days=7,
            now=T0,
        )
        self.fake.event_index = {}
        self.fake.gone_on_sync = True
        self.fake.event_pages = {
            "cal-1": [
                {"items": [_event("evt-keep", "u1")], "nextPageToken": "p2"},
                {"fail": True},
            ]
        }
        held = watcher.run_calendar(self.conn, now=T0)
        self.assertTrue(held.get("held"), held)
        self.assertEqual(
            self.conn.execute("SELECT cursor_value FROM cursors").fetchone()[0],
            watcher.CALENDAR_RESYNC_MARKER,
        )
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM items").fetchone()[0], 0)
        self.fake.event_index = {}
        self.fake.gone_on_sync = False
        self.fake.calls.clear()
        self.fake.params.clear()
        self.fake.event_pages = {
            "cal-1": [
                {"items": [_event("evt-keep", "u1")], "nextPageToken": "p2"},
                {
                    "items": [
                        _event("evt-e", "u2", "cancelled"),
                        _event("evt-new", "u1"),
                    ],
                    "nextSyncToken": "sync-done",
                },
            ]
        }
        resumed = watcher.run_calendar(self.conn, now=T0)
        self.assertTrue(resumed["ok"], resumed)
        self.assertEqual(resumed["new"], 1)
        event_params = [
            params
            for path, params in zip(self.fake.calls, self.fake.params)
            if str(path).endswith("/events")
        ]
        self.assertTrue(event_params)
        self.assertTrue(all(not params.get("syncToken") for params in event_params))
        ids = {row[0] for row in self.conn.execute("SELECT event_id FROM items")}
        self.assertEqual(ids, {"evt-e"})
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM calendar_events").fetchone()[0], 3)
        self.assertEqual(
            self.conn.execute("SELECT cursor_value FROM cursors").fetchone()[0],
            "sync-done",
        )
        loop = self.conn.execute("SELECT status, closed_intent FROM loops").fetchone()
        self.assertEqual(loop["status"], "closed")
        self.assertEqual(loop["closed_intent"], "cancelled")

    def test_allowlist_refuses_before_http(self) -> None:
        called = {"n": 0}

        def transport(method, url, **kwargs):
            called["n"] += 1
            return google_http.GoogleHttpResponse(200, "{}")

        google_http.set_transport_for_tests(transport)
        warnings = []
        logger = logging.getLogger("zola_workspace.google_http")
        logger.setLevel(logging.WARNING)
        handler = logging.Handler()
        handler.emit = lambda record: warnings.append(record)
        logger.addHandler(handler)
        try:
            with self.assertRaises(google_http.AllowlistError):
                google_http.request(
                    "GET",
                    background_read.GMAIL_PROFILE_URL,
                    route=google_http.ROUTE_GMAIL_PROFILE,
                )
            self.assertEqual(called["n"], 0)
            with self.assertRaises(google_http.AllowlistError):
                google_http.request(
                    "GET",
                    background_read.GMAIL_GET_TMPL.format(message_id="m"),
                    route=google_http.ROUTE_GMAIL_GET,
                    params={"format": "full", "fields": "snippet"},
                    capability=google_http.background_capability(),
                )
            self.assertEqual(called["n"], 0)
            google_http.request(
                "GET",
                "https://gmail.googleapis.com/gmail/v1/users/me/messages",
                route=google_http.ROUTE_GMAIL_LIST,
                params={"q": "in:inbox", "maxResults": 1},
            )
            self.assertEqual(called["n"], 1)
        finally:
            logger.removeHandler(handler)
        self.assertTrue(any(record.levelno >= logging.WARNING for record in warnings))

    def test_allowlist_requires_https_host_and_a_clean_url(self) -> None:
        called = {"n": 0}

        def transport(method, url, **kwargs):
            called["n"] += 1
            return google_http.GoogleHttpResponse(200, "{}")

        google_http.set_transport_for_tests(transport)
        capability = google_http.background_capability()
        samples = [
            "http://gmail.googleapis.com/gmail/v1/users/me/profile",
            "https://evil.example/gmail/v1/users/me/profile",
            background_read.GMAIL_PROFILE_URL + "?x=1",
            background_read.GMAIL_PROFILE_URL + "#part",
            "https://gmail.googleapis.com/calendar/v3/users/me/calendarList",
        ]
        for url in samples:
            route = (
                google_http.ROUTE_CALENDAR_LIST
                if "/calendar/" in url
                else google_http.ROUTE_GMAIL_PROFILE
            )
            with self.assertRaises(google_http.AllowlistError):
                google_http.request("GET", url, route=route, capability=capability)
        self.assertEqual(called["n"], 0)
        google_http.request(
            "GET",
            background_read.GMAIL_PROFILE_URL,
            route=google_http.ROUTE_GMAIL_PROFILE,
            capability=capability,
        )
        self.assertEqual(called["n"], 1)

    def test_encoded_calendar_id_passes_and_the_raw_form_is_refused(self) -> None:
        seen = []

        def transport(method, url, **kwargs):
            seen.append(url)
            return google_http.GoogleHttpResponse(200, json.dumps({"items": []}))

        google_http.set_transport_for_tests(transport)
        capability = google_http.background_capability()
        samples = ["id#part", "owner@example.com", "team/calendar"]
        params = {
            "showDeleted": "true",
            "maxResults": 250,
            "fields": background_read.CALENDAR_EVENT_FIELDS,
        }
        for calendar_id in samples:
            raw = background_read.CALENDAR_EVENTS_TMPL.format(calendar_id=calendar_id)
            with self.assertRaises(google_http.AllowlistError):
                google_http.request(
                    "GET",
                    raw,
                    route=google_http.ROUTE_CALENDAR_EVENTS,
                    params=params,
                    capability=capability,
                )
            background_read.calendar_events(calendar_id)
        self.assertEqual(len(seen), len(samples))
        for calendar_id, url in zip(samples, seen):
            parsed = urlparse(url)
            encoded = quote(calendar_id, safe="")
            ident = parsed.path.split("/calendars/")[1].split("/events")[0]
            self.assertEqual(ident, encoded)
            self.assertFalse(parsed.query)
            self.assertFalse(parsed.fragment)
            self.assertNotIn("#", ident)
            self.assertNotIn("@", ident)
            self.assertNotIn("/", ident)

    def test_one_calendar_failure_does_not_block_the_others(self) -> None:
        self.fake.calendars = [
            {"id": "cal-1", "selected": True},
            {"id": "cal-2", "selected": True},
            {"id": "cal-3", "selected": True},
            {"id": "cal-4", "selected": True},
        ]
        self.fake.event_pages = {
            "cal-1": [{"fail": True}],
            "cal-2": [{"items": [], "nextSyncToken": "sync-2"}],
            "cal-3": [{"items": [], "nextSyncToken": "sync-3"}],
            "cal-4": [{"items": [], "nextSyncToken": "sync-4"}],
        }
        result = watcher.run_calendar(self.conn, now=T0)
        self.assertTrue(result.get("held"), result)
        self.assertEqual(result["new"], 0)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM items").fetchone()[0], 0)
        rows = {
            row[0]: row[1]
            for row in self.conn.execute(
                "SELECT scope_key, cursor_value FROM cursors WHERE source = 'calendar'"
            )
        }
        self.assertNotIn("cal-1", rows)
        self.assertEqual(rows, {"cal-2": "sync-2", "cal-3": "sync-3", "cal-4": "sync-4"})
        self.assertNotIn(watcher.CALENDAR_RESYNC_MARKER, rows.values())
        error = self.conn.execute("SELECT calendar_error FROM watcher_health").fetchone()[0]
        self.assertEqual(error, "transport failed=1")

    def test_forget_reaches_a_hashed_sender_and_not_an_unmapped_one(self) -> None:
        watcher.run_gmail(self.conn, now=T0)
        self.fake.history_added = [
            {"id": "m-alias", "thread": "t-a"},
            {"id": "m-other", "thread": "t-b"},
        ]
        self.fake.messages["m-alias"] = _message("m-alias", "t-a", ADDRESS)
        self.fake.messages["m-other"] = _message("m-other", "t-b", "other@example.com")
        self.fake.history_id = "h-f"
        self.assertEqual(watcher.run_gmail(self.conn, now=T0)["new"], 2)
        resolutions = {
            row[0]
            for row in self.conn.execute("SELECT entity_resolution FROM items")
        }
        self.assertEqual(resolutions, {"unresolved"})
        forgotten = proactive_store.forget_subject(
            self.conn,
            entity_id="ent-synthetic",
            address_hashes=[proactive_store.address_hash(ADDRESS)],
        )
        self.assertEqual(forgotten["items_deleted"], 1)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM items").fetchone()[0], 1)
        self.assertEqual(
            self.conn.execute("SELECT entity_resolution FROM items").fetchone()[0],
            "unresolved",
        )

    def test_locked_store_skips_the_cycle(self) -> None:
        self.conn.close()
        self.conn = proactive_store.connect(self.path, timeout_ms=200, retry=False)
        holder = sqlite3.connect(self.path)
        holder.execute("BEGIN IMMEDIATE")
        result = watcher.run_gmail(self.conn, now=T0)
        holder.close()
        self.assertEqual(result.get("reason"), "db_locked")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM items").fetchone()[0], 0)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM cursors").fetchone()[0], 0)
        self.assertIn("db_locked", self._logs())

    def test_clock_jump_is_due_and_a_normal_gap_is_not(self) -> None:
        self.assertFalse(
            watcher.due(
                last_mono=0,
                previous_wall=0,
                previous_mono=0,
                wall=10,
                mono=10,
                interval=watcher.GMAIL_POLL_SECONDS,
                reconnect_wait=False,
            )
        )
        self.assertTrue(
            watcher.due(
                last_mono=0,
                previous_wall=0,
                previous_mono=0,
                wall=100,
                mono=1,
                interval=watcher.GMAIL_POLL_SECONDS,
                reconnect_wait=False,
            )
        )
        self.assertFalse(
            watcher.due(
                last_mono=0,
                previous_wall=0,
                previous_mono=0,
                wall=0,
                mono=30,
                interval=watcher.GMAIL_POLL_SECONDS,
                reconnect_wait=True,
            )
        )
        self.assertTrue(
            watcher.due(
                last_mono=0,
                previous_wall=0,
                previous_mono=0,
                wall=0,
                mono=60,
                interval=watcher.GMAIL_POLL_SECONDS,
                reconnect_wait=True,
            )
        )

    def test_needs_reconnect_does_not_call_google_until_the_reason_clears(self) -> None:
        calls = {"n": 0}

        def status():
            calls["n"] += 1
            if calls["n"] == 1:
                return {"connected": False, "needs_reconnect": "invalid_grant", "missing_scopes": []}
            return {"connected": True, "needs_reconnect": None, "missing_scopes": []}

        with mock.patch.object(auth, "store_status", status):
            stopped = watcher.run_gmail(self.conn, now=T0)
            self.assertEqual(stopped.get("reason"), "needs_reconnect")
            self.assertEqual(self.fake.calls, [])
            resumed = watcher.run_gmail(self.conn, now=T0)
        self.assertTrue(resumed["ok"], resumed)
        self.assertEqual(resumed["new"], 0)
        self.assertTrue(self.fake.calls)

    def test_set_loop_matched_is_the_backstop(self) -> None:
        inserted = proactive_store.insert_item(
            self.conn, source="gmail", message_id="m-back", thread_id="t", now=T0
        )
        self._deliver(inserted["id"])
        refused = proactive_store.mark_loop_eligible(self.conn, inserted["id"], now=T0)
        self.assertFalse(refused["ok"])
        backed = proactive_store.set_loop_matched(self.conn, inserted["id"], now=T0)
        self.assertTrue(backed["ok"], backed)
        state = proactive_store.item_loop_state(self.conn, inserted["id"])
        self.assertEqual(state["eligibility"], "eligible")
        self.assertEqual(state["loop_matched"], 1)

    def test_second_instance_exits(self) -> None:
        self.assertEqual(watcher._instance_mutex_name(), _TEST_INSTANCE_MUTEX)
        self.assertNotEqual(_TEST_INSTANCE_MUTEX, watcher._INSTANCE_MUTEX)
        self.assertTrue(watcher.acquire_instance())
        script = str(Path(__file__).resolve())
        child = subprocess.run(
            [sys.executable, script, "--instance"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(child.returncode, watcher.EXIT_ALREADY_RUNNING)


class RefreshLockTests(unittest.TestCase):
    def tearDown(self) -> None:
        google_http.reset_transport_for_tests()
        auth.reset_auth_runtime_for_tests()

    def test_lock_timeout_does_not_set_needs_reconnect_and_invalid_grant_does(self) -> None:
        script = str(Path(__file__).resolve())
        holder = subprocess.Popen(
            [sys.executable, script, "--hold-refresh", "3"],
            stdout=subprocess.PIPE,
            text=True,
        )
        line = holder.stdout.readline() if holder.stdout is not None else ""
        self.assertEqual(line.strip(), "held")
        auth.set_refresh_lock_timeout_for_tests(0.3)
        try:
            with self.assertRaises(auth.RefreshLockTimeout):
                auth.refresh_access_token(force=True)
            self.assertIsNone(auth.get_reconnect_reason())
        finally:
            holder.wait(timeout=5)
            if holder.stdout is not None:
                holder.stdout.close()
            auth.reset_auth_runtime_for_tests()

    def test_two_processes_post_one_at_a_time(self) -> None:
        spans = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:  # noqa: N802
                start = time.monotonic()
                time.sleep(0.25)
                spans.append((start, time.monotonic()))
                body = b'{"access_token":"ya29.synthetic","expires_in":3600}'
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format: str, *args) -> None:  # noqa: A003
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = __import__("threading").Thread(target=server.serve_forever, daemon=True)
        thread.start()
        home = tempfile.TemporaryDirectory(prefix="p9refresh_")
        try:
            store = Path(home.name) / "token.dpapi"
            _seed_store(store)
            url = f"http://127.0.0.1:{server.server_address[1]}/token"
            script = str(Path(__file__).resolve())
            children = [
                subprocess.Popen(
                    [sys.executable, script, "--refresh-post", url, str(store)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                for _ in range(2)
            ]
            for child in children:
                out, err = child.communicate(timeout=15)
                self.assertEqual(child.returncode, 0, err)
                self.assertIn("ok", out)
            self.assertEqual(len(spans), 2)
            ordered = sorted(spans)
            self.assertLessEqual(ordered[0][1], ordered[1][0] + 0.05)
        finally:
            server.shutdown()
            server.server_close()
            home.cleanup()

    def test_dead_holder_does_not_block(self) -> None:
        script = str(Path(__file__).resolve())
        holder = subprocess.Popen(
            [sys.executable, script, "--hold-refresh", "30"],
            stdout=subprocess.PIPE,
            text=True,
        )
        line = holder.stdout.readline() if holder.stdout is not None else ""
        self.assertEqual(line.strip(), "held")
        home = tempfile.TemporaryDirectory(prefix="p9dead_")
        try:
            store = Path(home.name) / "token.dpapi"
            _seed_store(store)
            auth.set_token_endpoint_for_tests("http://127.0.0.1:9/unused")
            auth.set_refresh_lock_timeout_for_tests(2.0)

            def transport(method, url, **kwargs):
                return google_http.GoogleHttpResponse(
                    200, '{"access_token":"ya29.synthetic","expires_in":3600}'
                )

            google_http.set_transport_for_tests(transport)
            started = time.monotonic()
            box = {}

            def go() -> None:
                box["token"] = auth.refresh_access_token(force=True)

            worker = __import__("threading").Thread(target=go)
            worker.start()
            time.sleep(0.3)
            self.assertTrue(worker.is_alive())
            holder.kill()
            holder.wait(timeout=5)
            worker.join(2)
            self.assertFalse(worker.is_alive())
            self.assertLess(time.monotonic() - started, 2.0)
            self.assertEqual(box["token"], "ya29.synthetic")
            self.assertIsNone(auth.get_reconnect_reason())
        finally:
            if holder.poll() is None:
                holder.kill()
                holder.wait(timeout=5)
            if holder.stdout is not None:
                holder.stdout.close()
            home.cleanup()

    def test_invalid_grant_stops_polling(self) -> None:
        home = tempfile.TemporaryDirectory(prefix="p9grant_")
        db = tempfile.TemporaryDirectory(prefix="p9grantdb_")
        try:
            store = Path(home.name) / "token.dpapi"
            _seed_store(store)
            calls = {"n": 0}

            def transport(method, url, **kwargs):
                calls["n"] += 1
                raise google_http.GoogleHttpStatusError(
                    "http_400",
                    status=400,
                    body_text='{"error":"invalid_grant"}',
                )

            google_http.set_transport_for_tests(transport)
            with self.assertRaises(RuntimeError):
                auth.refresh_access_token(force=True)
            self.assertEqual(auth.get_reconnect_reason(), auth.REASON_INVALID_GRANT)
            with self.assertRaises(RuntimeError):
                auth.refresh_access_token(force=True)
            self.assertEqual(calls["n"], 1)
            path = Path(db.name) / "proactive.db"
            conn = proactive_store.connect(path, retry=False)
            try:
                calls["n"] = 0
                result = watcher.run_gmail(conn, now=T0)
            finally:
                conn.close()
            self.assertEqual(result.get("reason"), "needs_reconnect")
            self.assertEqual(calls["n"], 0)
        finally:
            home.cleanup()
            db.cleanup()


def _dpapi_pair():
    def protect(plain: bytes) -> bytes:
        return b"FAKE_DPAPI:" + plain

    def unprotect(blob: bytes) -> bytes:
        if not blob.startswith(b"FAKE_DPAPI:"):
            raise ValueError("bad_blob")
        return blob[len(b"FAKE_DPAPI:") :]

    return protect, unprotect


def _arm_store(path: Path) -> None:
    protect, unprotect = _dpapi_pair()
    auth.set_dpapi_shim_for_tests(protect, unprotect)
    auth.set_store_path_for_tests(path)


def _seed_store(path: Path) -> None:
    _arm_store(path)
    auth.save_token_record(
        auth.TokenRecord(
            refresh="synthetic-refresh",
            client_id="cid",
            client_secret="sec",
            sub="sub-synthetic",
            scopes=tuple(auth.REQUIRED_SCOPES),
            version=1,
            created_at="2026-06-01T00:00:00+00:00",
        )
    )


class CycleTests(unittest.TestCase):
    def tearDown(self) -> None:
        google_http.reset_transport_for_tests()
        auth.reset_auth_runtime_for_tests()
        proactive_store.set_db_path_for_tests(None)
        proactive_store.set_ticket_override_for_tests(None)

    def test_invalid_grant_from_the_header_returns_needs_reconnect(self) -> None:
        home = tempfile.TemporaryDirectory(prefix="p9cycle_")
        try:
            store = Path(home.name) / "token.dpapi"
            db = Path(home.name) / "proactive.db"
            _seed_store(store)
            proactive_store.set_ticket_override_for_tests(True)
            proactive_store.set_db_path_for_tests(db)
            conn = proactive_store.connect(db, retry=False)
            called = {"n": 0}

            def boom():
                called["n"] += 1
                raise RuntimeError("invalid_grant")

            try:
                with mock.patch.object(auth, "authorization_header", boom):
                    result = watcher.run_gmail(conn, now=T0)
            finally:
                conn.close()
            self.assertEqual(result.get("reason"), "needs_reconnect")
            self.assertEqual(called["n"], 1)
            self.assertEqual(auth.get_reconnect_reason(), "invalid_grant")
            check = sqlite3.connect(db)
            try:
                self.assertEqual(
                    check.execute("SELECT needs_reconnect FROM watcher_health").fetchone()[0],
                    1,
                )
            finally:
                check.close()
        finally:
            home.cleanup()

    def test_main_stays_up_after_auth_and_a_down_profile(self) -> None:
        script = str(Path(__file__).resolve())
        home = tempfile.TemporaryDirectory(prefix="p9main_")
        try:
            db = Path(home.name) / "proactive.db"
            auth_child = subprocess.run(
                [sys.executable, script, "--cycle-reconnect", home.name, str(db)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(auth_child.returncode, 0, auth_child.stderr)
            self.assertNotIn("Traceback", auth_child.stderr)
            self.assertNotIn("invalid_grant", auth_child.stderr)
            check = sqlite3.connect(db)
            try:
                self.assertEqual(
                    check.execute("SELECT needs_reconnect FROM watcher_health").fetchone()[0],
                    1,
                )
            finally:
                check.close()
            offline = subprocess.run(
                [sys.executable, script, "--cycle-offline", home.name, str(db) + ".off"],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(offline.returncode, 0, offline.stderr)
            self.assertNotIn("Traceback", offline.stderr)
            off = sqlite3.connect(str(db) + ".off")
            try:
                self.assertEqual(off.execute("SELECT COUNT(*) FROM cursors").fetchone()[0], 0)
                self.assertEqual(off.execute("SELECT COUNT(*) FROM items").fetchone()[0], 0)
            finally:
                off.close()
            log_path = Path(home.name) / "logs" / "zola_watcher.log"
            text = log_path.read_text(encoding="utf-8")
            self.assertIn("zola_watcher.purge bodies=", text)
            self.assertNotIn(SUBJECT, text)
        finally:
            home.cleanup()


def _cycle_child(mode: str) -> None:
    home = Path(sys.argv[2])
    db = Path(sys.argv[3])
    os.environ["HERMES_HOME"] = str(home)
    os.environ["ZOLA_WATCHER_PARENT_PID"] = "4"
    proactive_store.set_db_path_for_tests(db)
    proactive_store.set_ticket_override_for_tests(True)
    state = {"n": 0}

    def alive(pid: int) -> bool:
        state["n"] += 1
        return state["n"] < 2

    watcher.parent_alive = alive
    watcher.time.sleep = lambda *_args, **_kwargs: None
    if mode == "reconnect":
        _seed_store(home / "token.dpapi")

        def boom():
            raise RuntimeError("invalid_grant")

        auth.authorization_header = boom
    else:
        _seed_store(home / "token-off.dpapi")

        def transport(method, url, **kwargs):
            if "/profile" in url:
                raise google_http.GoogleHttpTransportError("transport_error")
            return google_http.GoogleHttpResponse(
                200, '{"access_token":"ya29.synthetic","expires_in":3600}'
            )

        google_http.set_transport_for_tests(transport)
    raise SystemExit(watcher.main())


def _child_main() -> None:
    if "--instance" in sys.argv:
        raise SystemExit(0 if watcher.acquire_instance() else watcher.EXIT_ALREADY_RUNNING)
    if "--hold-refresh" in sys.argv:
        auth.hold_refresh_mutex_for_tests(float(sys.argv[sys.argv.index("--hold-refresh") + 1]))
        return
    if "--refresh-post" in sys.argv:
        index = sys.argv.index("--refresh-post")
        url = sys.argv[index + 1]
        store = Path(sys.argv[index + 2])
        _arm_store(store)
        auth.set_token_endpoint_for_tests(url)
        auth.refresh_access_token(force=True)
        print("ok")
        return
    if "--cycle-reconnect" in sys.argv:
        _cycle_child("reconnect")
        return
    if "--cycle-offline" in sys.argv:
        _cycle_child("offline")
        return


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].startswith("--"):
        _child_main()
    else:
        unittest.main()
