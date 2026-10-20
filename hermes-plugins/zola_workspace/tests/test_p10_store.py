"""P10-STORE: schema 6, phone ingest, tombstones, ranker skip, contract vectors."""

from __future__ import annotations

import ast
import base64
import json
import logging
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

import address_hash
import loops
import phone_ids
import proactive_store

T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
DEVICE = "zp10-device-1"
BODY = "ZP10-synthetic"
CONTRACTS = PLUGIN_ROOT / "contracts"
RECORDED_HASHES = {
    "": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "5551234567": "3c95277da5fd0da6a1a44ee3fdf56d20af6c6d242695a40e18e6e90dc3c5872c",
    "+15551234567": "8a59780bb8cd2ba022bfa5ba2ea3b6e07af17a7d8b30c1f9b3390e36f69019e4",
    "amzn": "b923405ba2c6a80ac557a30930e6119300a1c0805536c8dd0795340970591324",
    "ZP10-synthetic": "783f21b98663b5d809b9503f825edcba3522161c497d102d479261d11bc87c3a",
}
NORMALIZER_CASES = (
    ("(555) 123-4567", "e164", "+15551234567", True),
    ("555-123-4567", "e164", "+15551234567", True),
    ("+1 555 123 4567", "e164", "+15551234567", True),
    ("1-555-123-4567", "e164", "+15551234567", True),
    ("5551234567", "e164", "+15551234567", True),
    ("15551234567", "e164", "+15551234567", True),
    ("+15551234567", "e164", "+15551234567", True),
    ("+44 20 7946 0958", "e164", "+442079460958", True),
    ("32665", "shortcode", "32665", False),
    ("AMZN", "alnum", "amzn", False),
    ("", "unparsed", "", False),
    ("junk", "alnum", "junk", False),
    ("abc!@#def", "unparsed", "abc!@#def", False),
    ("hello-world-123456", "unparsed", "hello-world-123456", False),
)


def _at(**kwargs) -> datetime:
    return T0 + timedelta(**kwargs)


def _canon(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _load_pub(pem: str):
    return serialization.load_pem_public_key(pem.encode("ascii"))


def _verifies(public_pem: str, payload: dict, signature: str) -> bool:
    if not signature:
        return False
    try:
        raw = base64.b64decode(signature)
        _load_pub(public_pem).verify(raw, _canon(payload), ec.ECDSA(hashes.SHA256()))
    except (InvalidSignature, ValueError, TypeError):
        return False
    return True


def _case_payload(case: dict) -> dict:
    payload = dict(case.get("payload") or {})
    if case.get("pad_bytes"):
        payload["pad"] = "x" * int(case["pad_bytes"])
    return payload


def _decide(case: dict, protocol: dict, keys: dict, vectors: dict) -> str:
    # P10-INTAKE: golden vectors go through zola-phone's verifier — P10-D12
    plugins = str(PLUGIN_ROOT.parent)
    if plugins not in sys.path:
        sys.path.insert(0, plugins)
    from zola_phone.wire import decide_case

    return decide_case(case, protocol, keys, vectors)


class _StoreCase(unittest.TestCase):
    def setUp(self) -> None:
        self._dir = tempfile.TemporaryDirectory(prefix="p10store_")
        self.path = Path(self._dir.name) / "proactive" / "proactive.db"
        proactive_store.set_ticket_override_for_tests(True)
        proactive_store.set_db_path_for_tests(self.path)
        self.conn = proactive_store.connect(self.path, retry=False)

    def tearDown(self) -> None:
        self.conn.close()
        proactive_store.set_ticket_override_for_tests(None)
        proactive_store.set_db_path_for_tests(None)
        self._dir.cleanup()

    def _ingest(self, **kwargs):
        fields = dict(
            kind="sms",
            device_id=DEVICE,
            provider_id="prov-1",
            revision=1,
            completeness="complete",
            received_at=T0,
            sender_raw="5551234567",
            sender_display_name="Synthetic",
            body=BODY,
            now=T0,
        )
        fields.update(kwargs)
        return proactive_store.ingest_phone_item(self.conn, **fields)

    def _row(self, item_id: str):
        return self.conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()


class MigrationTests(unittest.TestCase):
    def test_schema5_rows_survive_and_second_run_is_quiet(self) -> None:
        folder = tempfile.TemporaryDirectory(prefix="p10mig_")
        self.addCleanup(folder.cleanup)
        path = Path(folder.name) / "proactive.db"
        raw = sqlite3.connect(path)
        proactive_store._migrate_v1(raw)
        proactive_store._migrate_v2(raw)
        proactive_store._migrate_v3(raw)
        proactive_store._migrate_v4(raw)
        proactive_store._migrate_v5(raw)
        raw.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        raw.execute("INSERT INTO meta (key, value) VALUES ('schema_version', '5')")
        raw.execute("INSERT INTO meta (key, value) VALUES ('ranker_state', 'idle')")
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
              'p9@example.com', 'hash-kept', 'Kept', NULL, NULL,
              'unresolved', 'important', 'ranked', 'eligible', 'selected', 'none', 'available',
              1, 0, NULL, '2026-06-01T00:00:00Z', '2026-06-01T00:00:01Z', '2026-06-01T00:00:01Z',
              '2026-06-01T00:00:00Z', 'kept subject', 'kept snippet', 'kept body', 'kept gist', NULL
            )
            """
        )
        raw.execute(
            """
            INSERT INTO loops (
              id, status, intent, predicate_json, created_at, expires_at, matched_at,
              lapse_told, session_id, entity_id, source_ids_json, address_hashes_json,
              sender_display_name, subject, name_source
            ) VALUES (
              'loop-1', 'open', 'reply', '{}', '2026-06-01T00:00:00Z', '2026-06-15T00:00:00Z', NULL,
              0, 'sess', NULL, '[]', '[]', 'Kept', 'kept subject', 'mail'
            )
            """
        )
        raw.commit()
        before_items = raw.execute("SELECT COUNT(*) FROM items").fetchone()[0]
        before_loops = raw.execute("SELECT COUNT(*) FROM loops").fetchone()[0]
        raw.close()
        conn = proactive_store.connect(path, retry=False)
        self.addCleanup(conn.close)
        version = conn.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()[0]
        self.assertEqual(version, "6")
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM items").fetchone()[0], before_items)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM loops").fetchone()[0], before_loops)
        self.assertEqual(conn.execute("SELECT value FROM meta WHERE key = 'ranker_state'").fetchone()[0], "idle")
        row = conn.execute("SELECT * FROM items WHERE id = 'kept'").fetchone()
        self.assertEqual(row["subject"], "kept subject")
        self.assertEqual(row["body"], "kept body")
        self.assertEqual(row["eligibility"], "eligible")
        self.assertEqual(row["conversation"], "selected")
        self.assertEqual(row["ranking_source"], "model")
        self.assertIsNone(row["device_id"])
        self.assertIsNone(row["judgment"])
        self.assertIsNone(row["watch_evaluated"])
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM phone_tombstones").fetchone()[0], 0)
        tomb_cols = [info[1] for info in conn.execute("PRAGMA table_info(phone_tombstones)")]
        self.assertEqual(tomb_cols, ["identity_key_hash", "created_at"])
        first = [tuple(item) for item in conn.execute("SELECT * FROM items ORDER BY id")]
        conn.close()
        again = proactive_store.connect(path, retry=False)
        self.addCleanup(again.close)
        self.assertEqual(again.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()[0], "6")
        second = [tuple(item) for item in again.execute("SELECT * FROM items ORDER BY id")]
        self.assertEqual(second, first)
        self.assertEqual(again.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_unknown_schema_is_refused(self) -> None:
        folder = tempfile.TemporaryDirectory(prefix="p10refuse_")
        self.addCleanup(folder.cleanup)
        path = Path(folder.name) / "proactive.db"
        raw = sqlite3.connect(path)
        proactive_store._migrate_v1(raw)
        proactive_store._migrate_v2(raw)
        proactive_store._migrate_v3(raw)
        proactive_store._migrate_v4(raw)
        proactive_store._migrate_v5(raw)
        raw.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        raw.execute("INSERT INTO meta (key, value) VALUES ('schema_version', '99')")
        raw.commit()
        raw.close()
        with self.assertRaises(RuntimeError):
            proactive_store.connect(path, retry=False)
        check = sqlite3.connect(path)
        self.addCleanup(check.close)
        self.assertEqual(check.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()[0], "99")
        columns = {info[1] for info in check.execute("PRAGMA table_info(items)")}
        self.assertNotIn("ranking_source", columns)


class IngestTests(_StoreCase):
    def test_identity_splits_device_kind_and_provider(self) -> None:
        first = self._ingest()
        again = self._ingest()
        self.assertEqual(first["result"], "stored")
        self.assertEqual(again["result"], "duplicate")
        self.assertEqual(again["id"], first["id"])
        other_device = self._ingest(device_id="zp10-device-2", provider_id="prov-1")
        other_kind = self._ingest(kind="mms", provider_id="prov-1")
        other_provider = self._ingest(provider_id="prov-2")
        ids = {first["id"], other_device["id"], other_kind["id"], other_provider["id"]}
        self.assertEqual(len(ids), 4)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM items").fetchone()[0], 4)

    def test_revisions_and_no_content_restore(self) -> None:
        stored = self._ingest(body=BODY, attachment_kind="image", attachment_has=1, attachment_count=1)
        item_id = stored["id"]
        higher = self._ingest(revision=2, body="ZP10-later", sender_display_name="Later")
        self.assertEqual(higher["result"], "updated")
        self.assertEqual(self._row(item_id)["body"], "ZP10-later")
        same = self._ingest(revision=2, body="ZP10-nope")
        self.assertEqual(same["result"], "duplicate")
        self.assertEqual(self._row(item_id)["body"], "ZP10-later")
        with self.assertLogs("zola_workspace.proactive_store", level="INFO") as caught:
            lower = self._ingest(revision=1, body="ZP10-old")
        self.assertEqual(lower["result"], "ignored")
        self.assertIn("result=ignored", "\n".join(caught.output))
        self.assertNotIn(BODY, "\n".join(caught.output))
        self.assertEqual(self._row(item_id)["body"], "ZP10-later")
        self.assertEqual(self._row(item_id)["sender_address"], "")
        kind, canonical = phone_ids.normalize("5551234567")
        self.assertEqual(self._row(item_id)["sender_address_hash"], phone_ids.hash(canonical))
        self.assertEqual(kind, "e164")

        acked = self._ingest(provider_id="ack", revision=1, body=BODY, attachment_kind="image", attachment_has=1, attachment_count=1)
        proactive_store.acknowledge(self.conn, acked["id"], now=T0, include_unselected=True)
        revised = self._ingest(provider_id="ack", revision=2, body="ZP10-back", attachment_kind="video", sender_display_name="Back")
        self.assertEqual(revised["result"], "updated")
        row = self._row(acked["id"])
        self.assertIsNone(row["body"])
        self.assertIsNone(row["sender_display_name"])
        self.assertIsNone(row["attachment_kind"])
        self.assertEqual(row["revision"], 2)
        self.assertEqual(row["content_state"], "content_expired")

        dismissed = self._ingest(provider_id="dismiss", body=BODY, attachment_kind="audio", attachment_has=1, attachment_count=1)
        proactive_store.dismiss_item(self.conn, dismissed["id"], now=T0)
        self._ingest(provider_id="dismiss", revision=2, body="ZP10-back", attachment_kind="image")
        row = self._row(dismissed["id"])
        self.assertIsNone(row["body"])
        self.assertIsNone(row["attachment_kind"])
        self.assertEqual(row["delivery"], "none")

        closed = self._ingest(provider_id="close", body=BODY, sender_display_name="Shown")
        proactive_store.close_item(self.conn, closed["id"], now=T0)
        self._ingest(provider_id="close", revision=2, body="ZP10-back", sender_display_name="Back")
        row = self._row(closed["id"])
        self.assertIsNone(row["body"])
        self.assertIsNone(row["sender_display_name"])

        aged = self._ingest(provider_id="aged", body=BODY, attachment_kind="other", attachment_has=1, attachment_count=2, received_at=_at(days=-8))
        purged = proactive_store.purge_retention(self.conn, now=T0)
        self.assertTrue(purged["ok"], purged)
        row = self._row(aged["id"])
        self.assertIsNone(row["body"])
        self.assertIsNone(row["sender_display_name"])
        self.assertIsNone(row["attachment_kind"])
        self.assertEqual(row["content_state"], "content_expired")
        self.assertEqual(row["delivery"], "none")
        self._ingest(provider_id="aged", revision=2, body="ZP10-back", attachment_kind="image", received_at=_at(days=-8))
        row = self._row(aged["id"])
        self.assertIsNone(row["body"])
        self.assertIsNone(row["attachment_kind"])
        self.assertEqual(row["revision"], 2)

        redacted = self._ingest(provider_id="redact", body=BODY, attachment_kind="image", attachment_has=1, attachment_count=1)
        self.conn.execute("UPDATE items SET delivery = 'claimed' WHERE id = ?", (redacted["id"],))
        self.conn.commit()
        sender_hash = self._row(redacted["id"])["sender_address_hash"]
        forgot = proactive_store.forget_subject(self.conn, address_hashes=[sender_hash])
        self.assertEqual(forgot["items_redacted"], 1)
        self._ingest(provider_id="redact", revision=2, body="ZP10-back", attachment_kind="video")
        row = self._row(redacted["id"])
        self.assertIsNone(row["body"])
        self.assertIsNone(row["attachment_kind"])
        self.assertEqual(row["content_state"], "forgotten")

        deleted = self._ingest(provider_id="gone", body=BODY)
        gone_hash = self._row(deleted["id"])["sender_address_hash"]
        removed = proactive_store.forget_subject(self.conn, address_hashes=[gone_hash])
        self.assertEqual(removed["items_deleted"], 1)
        suppressed = self._ingest(provider_id="gone", revision=3, body="ZP10-back")
        self.assertEqual(suppressed["result"], "suppressed")
        self.assertIsNone(self._row(deleted["id"]))

    def test_tombstone_expires_and_holds_no_content(self) -> None:
        key = proactive_store._phone_identity(
            kind="sms", device_id=DEVICE, provider_id="tomb", package="", notification_key="", newest_message_timestamp=""
        )
        old = proactive_store.record_phone_tombstone(self.conn, key, now=_at(days=-31))
        fresh_key = proactive_store._phone_identity(
            kind="sms", device_id=DEVICE, provider_id="fresh-tomb", package="", notification_key="", newest_message_timestamp=""
        )
        proactive_store.record_phone_tombstone(self.conn, fresh_key, now=T0)
        self.assertTrue(old["ok"], old)
        blocked = self._ingest(provider_id="tomb", body=BODY)
        self.assertEqual(blocked["result"], "suppressed")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM items WHERE message_id = 'tomb'").fetchone()[0], 0)
        proactive_store.purge_retention(self.conn, now=T0)
        left = self.conn.execute("SELECT identity_key_hash FROM phone_tombstones").fetchall()
        self.assertEqual(len(left), 1)
        self.assertEqual(left[0][0], proactive_store.address_hash(fresh_key))
        columns = [info[1] for info in self.conn.execute("PRAGMA table_info(phone_tombstones)")]
        self.assertEqual(columns, ["identity_key_hash", "created_at"])

    def test_bad_mask_attachment_and_separator_store_nothing(self) -> None:
        self.assertEqual(self._ingest(mask_kind="nope")["result"], "rejected")
        self.assertEqual(self._ingest(attachment_kind="pdf")["result"], "rejected")
        self.assertEqual(self._ingest(mask_kind=None)["result"], "stored")
        self.assertEqual(self._ingest(device_id="bad\u001fid", provider_id="sep")["result"], "rejected")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM items").fetchone()[0], 1)

    def test_young_phone_content_survives_purge(self) -> None:
        stored = self._ingest(body=BODY, attachment_kind="image", attachment_has=1, attachment_count=1)
        purged = proactive_store.purge_retention(self.conn, now=T0)
        self.assertTrue(purged["ok"], purged)
        row = self._row(stored["id"])
        self.assertEqual(row["body"], BODY)
        self.assertEqual(row["attachment_kind"], "image")
        self.assertEqual(row["delivery"], "none")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM item_attempts").fetchone()[0], 0)


class RankAndHoldTests(_StoreCase):
    def test_ranker_skips_phone_and_still_claims_gmail(self) -> None:
        phone = self._ingest(body=BODY)
        self.conn.execute(
            "UPDATE items SET processing = 'unranked', body = ? WHERE id = ?",
            (BODY, phone["id"]),
        )
        self.conn.commit()
        gmail = proactive_store.insert_item(
            self.conn,
            source="gmail",
            message_id="g-1",
            thread_id="th",
            sender_address="p9@example.com",
            subject="notice",
            body="mail body",
            now=T0,
        )
        claimed = proactive_store.claim_next_rank(self.conn, now=T0)
        self.assertTrue(claimed["ok"], claimed)
        self.assertEqual(claimed["id"], gmail["id"])
        refused = proactive_store.claim_rank(self.conn, phone["id"], now=T0)
        self.assertEqual(refused.get("refused_reason"), "not_rankable")
        source = Path(proactive_store.__file__).read_text(encoding="utf-8")
        self.assertIn("ranking_source = 'model'", source)
        self.assertIn('row["ranking_source"] != "model"', source)

    def test_phone_row_stays_out_of_surface_and_speech(self) -> None:
        phone = self._ingest(body=BODY)
        matched = proactive_store.set_loop_matched(self.conn, phone["id"], now=T0)
        self.assertTrue(matched["ok"], matched)
        gmail = proactive_store.insert_item(
            self.conn, source="gmail", message_id="g-speak", thread_id="th", body="mail", now=T0
        )
        proactive_store.mark_loop_eligible(self.conn, gmail["id"], now=T0)
        listed = proactive_store.list_surface_rows(self.conn)
        ids = {row["id"] for row in listed["items"]}
        self.assertIn(gmail["id"], ids)
        self.assertNotIn(phone["id"], ids)
        speech = proactive_store.claim_speech(self.conn, phone["id"], now=T0)
        self.assertEqual(speech.get("refused_reason"), "phone_deferred")
        nxt = proactive_store.claim_next_speech(self.conn, now=T0)
        self.assertEqual(nxt.get("item_id"), gmail["id"])
        selected = proactive_store.provisional_select(
            self.conn, phone["id"], "attempt", "turn", now=T0, reinject_cap=2, quiet_seconds=0
        )
        self.assertFalse(selected["ok"])
        stamp = proactive_store._iso(T0)
        self.conn.execute(
            "INSERT INTO deliveries (id, item_id, attempt_id, outcome, at) VALUES ('d-phone', ?, 'a-phone', 'delivered', ?)",
            (phone["id"], stamp),
        )
        self.conn.execute(
            "INSERT INTO deliveries (id, item_id, attempt_id, outcome, at) VALUES ('d-mail', ?, 'a-mail', 'delivered', ?)",
            (gmail["id"], proactive_store._iso(_at(seconds=-1))),
        )
        self.conn.commit()
        post = proactive_store.post_speech_candidate(self.conn, now=T0)
        self.assertEqual(post["item"]["id"], gmail["id"])


class WatchRecoveryTests(_StoreCase):
    def _recover(self, predicate: dict) -> int:
        fresh = 0
        listed = proactive_store.list_unevaluated_phone_items(self.conn)
        self.assertTrue(listed["ok"], listed)
        for item in listed["items"]:
            view = {
                "source": item["source"],
                "sender_address_hash": item["sender_address_hash"],
                "message_id": item["message_id"],
            }
            if loops.evaluate(predicate, view):
                noted = proactive_store.note_loop_match_on_loop(self.conn, "loop-phone", now=T0)
                matched = proactive_store.set_loop_matched(self.conn, item["id"], now=T0)
                self.assertTrue(noted["ok"] and matched["ok"])
                if not noted.get("already"):
                    fresh += 1
            marked = proactive_store.mark_watch_evaluated(self.conn, item["id"], now=T0)
            self.assertTrue(marked["ok"], marked)
        return fresh

    def test_crash_before_evaluation_matches_once(self) -> None:
        stored = self._ingest()
        sender = self._row(stored["id"])["sender_address_hash"]
        proactive_store.insert_loop(
            self.conn,
            intent="reply",
            predicate={"op": "sender_is", "address_hash": sender},
            session_id="sess",
            now=T0,
        )
        self.conn.execute("UPDATE loops SET id = 'loop-phone'")
        self.conn.commit()
        self.assertEqual(self._recover({"op": "sender_is", "address_hash": sender}), 1)
        self.assertEqual(self._recover({"op": "sender_is", "address_hash": sender}), 0)
        self.assertEqual(self._row(stored["id"])["loop_matched"], 1)
        self.assertIsNotNone(self.conn.execute("SELECT matched_at FROM loops WHERE id = 'loop-phone'").fetchone()[0])

    def test_crash_after_match_does_not_match_again(self) -> None:
        stored = self._ingest()
        sender = self._row(stored["id"])["sender_address_hash"]
        predicate = {"op": "sender_is", "address_hash": sender}
        proactive_store.insert_loop(
            self.conn, intent="reply", predicate=predicate, session_id="sess", now=T0
        )
        self.conn.execute("UPDATE loops SET id = 'loop-phone'")
        self.conn.commit()
        view = {"source": "sms", "sender_address_hash": sender, "message_id": "prov-1"}
        self.assertTrue(loops.evaluate(predicate, view))
        proactive_store.note_loop_match_on_loop(self.conn, "loop-phone", now=T0)
        proactive_store.set_loop_matched(self.conn, stored["id"], now=T0)
        matched_at = self.conn.execute("SELECT matched_at FROM loops WHERE id = 'loop-phone'").fetchone()[0]
        self.assertEqual(self._recover(predicate), 0)
        again = self._ingest(revision=1)
        self.assertEqual(again["result"], "duplicate")
        self.assertEqual(self._recover(predicate), 0)
        self.assertEqual(
            self.conn.execute("SELECT matched_at FROM loops WHERE id = 'loop-phone'").fetchone()[0],
            matched_at,
        )
        self.assertEqual(self._row(stored["id"])["loop_matched"], 1)
        self.assertEqual(proactive_store.list_unevaluated_phone_items(self.conn)["items"], [])


class NormalizerTests(unittest.TestCase):
    def test_plan_inputs_and_recorded_hashes(self) -> None:
        for raw, kind, canonical, matchable in NORMALIZER_CASES:
            got_kind, got_canonical = phone_ids.normalize(raw)
            self.assertEqual((got_kind, got_canonical), (kind, canonical), raw)
            self.assertEqual(phone_ids.matchable(got_kind), matchable, raw)
        for text, digest in RECORDED_HASHES.items():
            self.assertEqual(address_hash.address_hash(text), digest)
            self.assertEqual(proactive_store.address_hash(text), digest)
            self.assertEqual(phone_ids.hash(text), digest)

    def test_phone_ids_imports_stay_clean(self) -> None:
        tree = ast.parse((PLUGIN_ROOT / "phone_ids.py").read_text(encoding="utf-8"))
        allowed = {"address_hash"}
        banned = {"watcher", "auth", "google_http", "gmail", "gcal", "drive", "contacts", "proactive_store", "hermes"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name.split(".")[0]
                    self.assertNotIn(name, banned)
                    self.assertTrue(name in allowed or name in sys.stdlib_module_names, name)
            if isinstance(node, ast.ImportFrom):
                if node.level:
                    modules = [alias.name.split(".")[0] for alias in node.names]
                else:
                    modules = [(node.module or "").split(".")[0]]
                for module in modules:
                    self.assertNotIn(module, banned)
                    self.assertTrue(module in allowed or module in sys.stdlib_module_names, module)


class ContractTests(unittest.TestCase):
    def test_vectors_match_the_protocol(self) -> None:
        protocol = json.loads((CONTRACTS / "phone_protocol.json").read_text(encoding="utf-8"))
        keys = json.loads((CONTRACTS / "phone_test_keys.json").read_text(encoding="utf-8"))
        vectors = json.loads((CONTRACTS / "phone_vectors.json").read_text(encoding="utf-8"))
        self.assertIn("TEST KEYS", keys["label"])
        self.assertEqual(protocol["identity_separator"], "\u001f")
        self.assertTrue(protocol["pairing"]["keeps_device_id"])
        self.assertEqual(protocol["pairing"]["old_key_after_repair"], "unknown-key")
        self.assertTrue(protocol["pairing"]["stores_nothing_on_refusal"])
        self.assertEqual(protocol["mask_kind"], ["verification_code", "reset_link", "unsure"])
        self.assertEqual(protocol["attachment_kind"], ["image", "video", "audio", "other"])
        order = [step["step"] for step in protocol["check_precedence"]]
        names = [case["name"] for case in vectors["cases"]]
        positions = [names.index(step) for step in order]
        self.assertEqual(positions, sorted(positions))
        for step, index in zip(protocol["check_precedence"], positions):
            self.assertEqual(_decide(vectors["cases"][index], protocol, keys, vectors), step["reason"], step["step"])
        for case in vectors["cases"]:
            self.assertEqual(_decide(case, protocol, keys, vectors), case["expect"], case["name"])
        repair = next(case for case in vectors["cases"] if case["name"] == "repair-keeps-device")
        self.assertEqual(repair["payload"]["device_id"], keys["paired_device_id"])
        self.assertEqual(repair["replaces_key"], "old")
        self.assertEqual(
            next(case["expect"] for case in vectors["cases"] if case["name"] == "old-key-refused"),
            "unknown-key",
        )
        self.assertEqual(
            next(case["expect"] for case in vectors["cases"] if case["name"] == "unauthorized-key-refused"),
            "unknown-key",
        )
        self.assertTrue(loops.evaluate is __import__("loop_match").evaluate)


INGEST_REJECT_REASONS = (
    "bad_kind",
    "bad_revision",
    "bad_completeness",
    "bad_time",
    "bad_identity",
    "separator",
    "bad_mask",
    "bad_attachment",
    "bad_field",
    "too_large",
)


def _schema5(path: Path) -> sqlite3.Connection:
    raw = sqlite3.connect(path)
    raw.row_factory = sqlite3.Row
    proactive_store._migrate_v1(raw)
    proactive_store._migrate_v2(raw)
    proactive_store._migrate_v3(raw)
    proactive_store._migrate_v4(raw)
    proactive_store._migrate_v5(raw)
    raw.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    raw.execute("INSERT INTO meta (key, value) VALUES ('schema_version', '5')")
    raw.commit()
    return raw


class Phase5Fixes(_StoreCase):
    def test_f1_package_import_without_plugin_dir(self) -> None:
        # watcher.py has no argument parser; main() polls. Importing the module is the light entry.
        plugins = str(PLUGIN_ROOT.parent)
        env = os.environ.copy()
        env["PYTHONPATH"] = plugins
        env.pop("PYTHONSAFEPATH", None)
        code = (
            "import zola_workspace.proactive_store, zola_workspace.phone_ids, "
            "zola_workspace.watcher\n"
            "print('package-import-ok')"
        )
        proc = subprocess.run(
            [sys.executable, "-c", code],
            cwd=tempfile.gettempdir(),
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("package-import-ok", proc.stdout)

    def test_f2_second_v6_is_a_noop_and_dangling_fk_rolls_back(self) -> None:
        folder = tempfile.TemporaryDirectory(prefix="p10f2_")
        self.addCleanup(folder.cleanup)
        path = Path(folder.name) / "proactive.db"
        first = _schema5(path)
        first.execute(
            """
            INSERT INTO items (
              id, source, message_id, thread_id, event_id, event_updated, idempotency_key,
              sender_address, sender_address_hash, sender_display_name, entity_id, contacts_handle,
              entity_resolution, label, processing, eligibility, conversation, delivery, content_state,
              loop_matched, rank_attempts, closed_at, detected_at, ranked_at, eligible_at, updated_at,
              subject, snippet, body, gist, calendar_status
            ) VALUES (
              'kept', 'gmail', 'kept-msg', 'kept-th', NULL, NULL, 'gmail:kept-msg',
              '', 'hash-kept', 'Kept', NULL, NULL,
              'unresolved', NULL, 'ranked', 'eligible', 'none', 'none', 'available',
              0, 0, NULL, '2026-06-01T00:00:00Z', NULL, NULL,
              '2026-06-01T00:00:00Z', 'kept subject', 'kept snippet', 'kept body', NULL, NULL
            )
            """
        )
        first.commit()
        second = sqlite3.connect(path)
        second.row_factory = sqlite3.Row
        self.addCleanup(second.close)
        self.addCleanup(first.close)
        before = first.execute("SELECT COUNT(*) FROM items").fetchone()[0]
        self.assertEqual(first.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()[0], "5")
        self.assertEqual(second.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()[0], "5")
        proactive_store._migrate_v6_committed(first)
        proactive_store._migrate_v6_committed(second)
        self.assertEqual(first.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()[0], "6")
        self.assertEqual(second.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()[0], "6")
        self.assertEqual(first.execute("SELECT COUNT(*) FROM items").fetchone()[0], before)
        names = [row[0] for row in first.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]
        self.assertIn("items", names)
        self.assertNotIn("items_v6", names)
        self.assertEqual(
            first.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type = 'index' AND name = 'idx_items_phone_sender'"
            ).fetchone()[0],
            1,
        )

        broken_path = Path(folder.name) / "dangling.db"
        broken = _schema5(broken_path)
        self.addCleanup(broken.close)
        broken.execute("PRAGMA foreign_keys=OFF")
        broken.execute(
            """
            INSERT INTO item_attempts (
              attempt_id, item_id, purpose, status, lease_expires_at, created_at
            ) VALUES ('att-dangling', 'missing-item', 'rank', 'open', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')
            """
        )
        broken.commit()
        with self.assertRaises(RuntimeError):
            proactive_store._migrate_v6_committed(broken)
        self.assertEqual(broken.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()[0], "5")
        columns = [info[1] for info in broken.execute("PRAGMA table_info(items)")]
        self.assertNotIn("ranking_source", columns)
        self.assertNotIn("truncated", columns)
        tables = [row[0] for row in broken.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]
        self.assertNotIn("phone_tombstones", tables)

    def test_f3_open_loop_phone_row_expires_and_stays_empty(self) -> None:
        stored = self._ingest(
            provider_id="held",
            received_at=_at(days=-8),
            body=BODY,
            sender_display_name="Shown",
            subject="Sub",
            snippet="Snip",
            attachment_has=1,
            attachment_count=1,
            attachment_kind="image",
        )
        proactive_store.insert_loop(
            self.conn,
            intent="reply",
            predicate={"op": "sender_is", "address_hash": "not-used"},
            session_id="sess",
            now=T0,
        )
        self.conn.execute(
            "UPDATE loops SET source_ids_json = ? WHERE status = 'open'",
            (json.dumps([stored["id"]]),),
        )
        self.conn.commit()
        matched = proactive_store.set_loop_matched(self.conn, stored["id"], now=T0)
        self.assertTrue(matched["ok"], matched)
        purged = proactive_store.purge_retention(self.conn, now=T0)
        self.assertTrue(purged["ok"], purged)
        row = self._row(stored["id"])
        self.assertIsNone(row["closed_at"])
        self.assertEqual(row["loop_matched"], 1)
        self.assertIsNone(row["body"])
        self.assertIsNone(row["subject"])
        self.assertIsNone(row["snippet"])
        self.assertIsNone(row["sender_display_name"])
        self.assertIsNone(row["attachment_kind"])
        self.assertEqual(row["content_state"], "content_expired")
        revised = self._ingest(
            provider_id="held",
            revision=2,
            body="ZP10-back",
            sender_display_name="Back",
            received_at=_at(days=-8),
            attachment_kind="image",
            attachment_has=1,
            attachment_count=1,
        )
        self.assertEqual(revised["result"], "updated")
        row = self._row(stored["id"])
        self.assertIsNone(row["body"])
        self.assertIsNone(row["sender_display_name"])
        self.assertIsNone(row["attachment_kind"])
        self.assertEqual(row["revision"], 2)
        self.assertEqual(row["content_state"], "content_expired")

    def test_f4_incomplete_is_rejected(self) -> None:
        result = self._ingest(completeness="incomplete")
        self.assertEqual(result["result"], "rejected")
        self.assertEqual(result["reason"], "bad_completeness")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM items").fetchone()[0], 0)

    def test_f5_each_reject_reason_once(self) -> None:
        protocol = json.loads((CONTRACTS / "phone_protocol.json").read_text(encoding="utf-8"))
        self.assertEqual(tuple(protocol["ingest_reject_reasons"]), INGEST_REJECT_REASONS)
        cases = {
            "bad_kind": dict(kind="email"),
            "bad_revision": dict(revision=-1),
            "bad_completeness": dict(completeness="partial"),
            "bad_time": dict(received_at="2026-01-01T00:00:00Z"),
            "bad_identity": dict(device_id=""),
            "separator": dict(provider_id="a\x1fb"),
            "bad_mask": dict(mask_kind="nope"),
            "bad_attachment": dict(attachment_kind="pdf"),
            "bad_field": dict(is_group=2),
            "too_large": dict(body="x" * 16001),
        }
        self.assertEqual(set(cases), set(INGEST_REJECT_REASONS))
        for reason, fields in cases.items():
            payload = dict(fields)
            payload.setdefault("provider_id", f"rej-{reason}")
            result = self._ingest(**payload)
            self.assertEqual(result["result"], "rejected", reason)
            self.assertEqual(result.get("reason"), reason, reason)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM items").fetchone()[0], 0)

    def test_f6_size_limits_and_truncated_column(self) -> None:
        protocol = json.loads((CONTRACTS / "phone_protocol.json").read_text(encoding="utf-8"))
        text_limit = int(protocol["size_limits"]["text_body_chars"])
        note_limit = int(protocol["size_limits"]["notification_text_chars"])
        self.assertEqual(proactive_store.TEXT_BODY_CHARS, text_limit)
        self.assertEqual(proactive_store.NOTIFICATION_TEXT_CHARS, note_limit)
        over = self._ingest(provider_id="over-text", body="x" * (text_limit + 1))
        self.assertEqual(over["result"], "rejected")
        self.assertEqual(over["reason"], "too_large")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM items").fetchone()[0], 0)
        held = self._ingest(provider_id="at-text", body="x" * text_limit, truncated=1)
        self.assertEqual(held["result"], "stored")
        self.assertEqual(self._row(held["id"])["truncated"], 1)
        self.assertEqual(len(self._row(held["id"])["body"]), text_limit)
        note = self._ingest(
            kind="notif",
            provider_id="",
            package="app.synthetic",
            notification_key="note-1",
            newest_message_timestamp="1",
            body="n" * (note_limit + 1),
        )
        self.assertEqual(note["result"], "rejected")
        self.assertEqual(note["reason"], "too_large")
        bad_flag = self._ingest(provider_id="bad-flag", truncated=True)
        self.assertEqual(bad_flag["result"], "rejected")
        self.assertEqual(bad_flag["reason"], "bad_field")
        folder = tempfile.TemporaryDirectory(prefix="p10f6_")
        self.addCleanup(folder.cleanup)
        path = Path(folder.name) / "proactive.db"
        raw = _schema5(path)
        raw.execute(
            """
            INSERT INTO items (
              id, source, message_id, thread_id, event_id, event_updated, idempotency_key,
              sender_address, sender_address_hash, sender_display_name, entity_id, contacts_handle,
              entity_resolution, label, processing, eligibility, conversation, delivery, content_state,
              loop_matched, rank_attempts, closed_at, detected_at, ranked_at, eligible_at, updated_at,
              subject, snippet, body, gist, calendar_status
            ) VALUES (
              'phase9', 'gmail', 'p9', 'th', NULL, NULL, 'gmail:p9',
              '', 'hash-p9', 'Kept', NULL, NULL,
              'unresolved', NULL, 'ranked', 'eligible', 'none', 'none', 'available',
              0, 0, NULL, '2026-06-01T00:00:00Z', NULL, NULL,
              '2026-06-01T00:00:00Z', 's', 'n', 'b', NULL, NULL
            )
            """
        )
        raw.commit()
        raw.close()
        upgraded = proactive_store.connect(path, retry=False)
        self.addCleanup(upgraded.close)
        row = upgraded.execute("SELECT * FROM items WHERE id = 'phase9'").fetchone()
        self.assertIsNone(row["truncated"])
        self.assertEqual(row["ranking_source"], "model")

    def test_f8_v6_writes_six_when_supported_version_moves(self) -> None:
        folder = tempfile.TemporaryDirectory(prefix="p10f8_")
        self.addCleanup(folder.cleanup)
        fresh = _schema5(Path(folder.name) / "from5.db")
        self.addCleanup(fresh.close)
        already = _schema5(Path(folder.name) / "at6.db")
        self.addCleanup(already.close)
        proactive_store._migrate_v6_committed(already)
        self.assertEqual(
            already.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()[0],
            "6",
        )
        with mock.patch.object(proactive_store, "SCHEMA_VERSION", 7):
            with self.subTest("version 5 writes 6"):
                proactive_store._migrate_v6_committed(fresh)
                version = fresh.execute(
                    "SELECT value FROM meta WHERE key = 'schema_version'"
                ).fetchone()[0]
                self.assertEqual(version, "6")
                columns = [info[1] for info in fresh.execute("PRAGMA table_info(items)")]
                self.assertIn("ranking_source", columns)
            with self.subTest("version 6 is a no-op"):
                proactive_store._migrate_v6_committed(already)
                again = already.execute(
                    "SELECT value FROM meta WHERE key = 'schema_version'"
                ).fetchone()[0]
                self.assertEqual(again, "6")

    def test_f7_digits_are_ascii(self) -> None:
        for raw in ("555123456²", "٥٥٥١٢٣٤٥٦٧"):
            kind, canonical = phone_ids.normalize(raw)
            self.assertEqual(kind, "unparsed", raw)
            self.assertNotIn("+", canonical)


if __name__ == "__main__":
    logging.basicConfig(level="INFO")
    unittest.main()
