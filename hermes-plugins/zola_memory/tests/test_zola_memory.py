"""Unit tests for zola_memory (synthetic data only; P6-D01/D03/D06)."""

from __future__ import annotations

import importlib
import os
import shutil
import sys
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

_HERMES_ROOT = Path(r"C:\Users\test\Dev\hermes-agent")
if str(_HERMES_ROOT) not in sys.path:
    sys.path.insert(0, str(_HERMES_ROOT))

# P6-TIME: system Python may lack tzdata; hermes-agent venv has it — P6-D05
_VENV_SITE = _HERMES_ROOT / ".venv" / "Lib" / "site-packages"
if _VENV_SITE.is_dir() and str(_VENV_SITE) not in sys.path:
    try:
        from zoneinfo import ZoneInfo as _ZI

        _ZI("America/Los_Angeles")
    except Exception:
        sys.path.insert(0, str(_VENV_SITE))

from zoneinfo import ZoneInfo

import consolidate
import fact_index
import forget
import log as memlog
import registry
import store
import time_context
from forget import has_forget_intent
from provider import ZolaMemoryProvider

# P6-TIME: fixed Pacific offset for stamp/relative tests (no IANA dependency) — P6-D05
_PDT = timezone(timedelta(hours=-7), name="PDT")
_PST = timezone(timedelta(hours=-8), name="PST")
_LA = ZoneInfo("America/Los_Angeles")

# P6-STORE: synthetic strings for content scans — P6-D02
SYN_A = "[project] Demo codename is Aurora Quill."
SYN_B = "[project] Demo codename is Blue Lantern."
SYN_PHONE = "[preference] Demo phone is 555-0100."
SYN_PHONE_REDUCED = "[preference] Demo has a landline."
SYN_ADDR = "[person] Demo address is 1 Example Lane."
SYN_CAR = "[car] Demo car is green."
SYN_CAR_BLUE = "[car] Demo car is blue."
ALL_SYN = (SYN_A, SYN_B, SYN_PHONE, SYN_PHONE_REDUCED, SYN_ADDR, SYN_CAR, SYN_CAR_BLUE)


class _TempHome(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.mkdtemp(prefix="zola_memory_test_")
        self.home = Path(self._tmpdir)
        self.memories = self.home / "memories"
        self.memories.mkdir(parents=True)
        (self.memories / "USER.md").write_text("", encoding="utf-8")
        (self.memories / "MEMORY.md").write_text("", encoding="utf-8")
        os.environ["HERMES_HOME"] = str(self.home)
        memlog.reset_log_handler_for_tests()
        forget.set_erase_failure_hook(None)
        consolidate.reset_for_tests()
        consolidate.set_background_enabled_for_tests(False)
        forget.set_client_origin_override_for_tests(True)

    def tearDown(self) -> None:
        forget.set_client_origin_override_for_tests(None)
        forget.set_erase_failure_hook(None)
        consolidate.reset_for_tests()
        memlog.reset_log_handler_for_tests()
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def _write_files(self, *, user=None, memory=None) -> None:
        u = user if user is not None else []
        m = memory if memory is not None else []
        (self.memories / "USER.md").write_text(store.ENTRY_DELIMITER.join(u), encoding="utf-8")
        (self.memories / "MEMORY.md").write_text(store.ENTRY_DELIMITER.join(m), encoding="utf-8")

    def _open(self):
        return store.open_store(self.home)

    def _assert_no_synthetic_in_artifacts(self, conn) -> None:
        for row in conn.execute(
            "SELECT id, record_kind, erased_at, counts_json FROM tombstones"
        ):
            blob = " ".join(str(x) for x in row)
            for syn in ALL_SYN:
                self.assertNotIn(syn, blob)
        log_path = self.home / "logs" / memlog.LOG_FILENAME
        if log_path.exists():
            text = log_path.read_text(encoding="utf-8")
            for syn in ALL_SYN:
                self.assertNotIn(syn, text)


class TestForgetIntent(unittest.TestCase):
    def test_quoted_forget_is_match(self) -> None:
        msg = (
            "When I said 'forget my address' yesterday, I didn't mean it; "
            "my address is actually 1 Demo Lane"
        )
        self.assertTrue(has_forget_intent(msg))

    def test_dont_forget_exclusion_no_match(self) -> None:
        self.assertFalse(has_forget_intent("Don't forget that I moved"))

    def test_do_not_forget_exclusion(self) -> None:
        self.assertFalse(has_forget_intent("Please do not forget the meeting"))

    def test_ordinary_correction_no_match(self) -> None:
        self.assertFalse(has_forget_intent("Actually, the car is blue, not green"))

    def test_genuine_forget(self) -> None:
        self.assertTrue(has_forget_intent("Please forget the demo project codename"))

    def test_dont_keep(self) -> None:
        self.assertTrue(
            has_forget_intent(
                "Don't keep my demo phone number anymore, just keep that I have a landline"
            )
        )

    def test_curly_dont_forget_exclusion(self) -> None:
        # U+2019 RIGHT SINGLE QUOTATION MARK
        self.assertFalse(has_forget_intent("Don\u2019t forget that I moved"))

    def test_curly_dont_keep_match(self) -> None:
        self.assertTrue(has_forget_intent("don\u2019t keep my number"))


class TestSchemaAndAuthority(_TempHome):
    def test_migrate_from_empty(self) -> None:
        conn = self._open()
        ver = store.meta_get(conn, store.META_SCHEMA_VERSION)
        self.assertEqual(ver, str(store.SCHEMA_VERSION))
        tables = {
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table','view')"
            )
        }
        for name in (
            "meta",
            "facts",
            "fact_history",
            "entities",
            "entity_aliases",
            "tombstones",
            "episodes",
            "episode_entities",
            "episode_fact_refs",
            "pending_turns",
            "facts_fts",
            "episodes_fts",
            "entities_fts",
        ):
            self.assertIn(name, tables)
        idx_sql = "\n".join(
            r[0] or ""
            for r in conn.execute(
                "SELECT sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL"
            )
        )
        self.assertIn("idx_entities_name", idx_sql)
        self.assertIn("idx_entity_aliases_alias", idx_sql)
        self.assertNotIn("ON entities(name, kind)", idx_sql)
        for row in conn.execute(
            "SELECT name, sql FROM sqlite_master WHERE type='index' AND name LIKE 'idx_ent%'"
        ):
            self.assertNotIn("UNIQUE", (row[1] or "").upper())
        conn.close()

    def test_empty_surfaces(self) -> None:
        p = ZolaMemoryProvider()
        p.initialize("sess", hermes_home=str(self.home))
        self.assertEqual(p.get_tool_schemas(), [])
        self.assertEqual(p.system_prompt_block(), "")
        self.assertEqual(p.prefetch("hi", session_id="sess"), "")
        p.shutdown()

    def test_never_opens_memory_files_for_write(self) -> None:
        self._write_files(memory=[SYN_A])
        p = ZolaMemoryProvider()
        real_open = open
        writes = []

        def gated_open(file, mode="r", *args, **kwargs):
            path = str(file)
            if ("MEMORY.md" in path or "USER.md" in path) and any(
                m in mode for m in ("w", "a", "x", "+")
            ):
                writes.append((path, mode))
            return real_open(file, mode, *args, **kwargs)

        with mock.patch("builtins.open", gated_open):
            p.initialize("sess", hermes_home=str(self.home))
            p.on_memory_write("add", "memory", SYN_B, metadata={})
            p.on_turn_start(1, "hello")
            p.shutdown()
        self.assertEqual(writes, [])


class TestNotifyMirror(_TempHome):
    def test_add_replace_remove(self) -> None:
        conn = self._open()
        self._write_files(memory=[SYN_A])
        fact_index.run_file_check(conn, self.home, force=True)
        self._write_files(memory=[SYN_A, SYN_CAR])
        fact_index.handle_memory_write(
            conn,
            self.home,
            action="add",
            target="memory",
            content=SYN_CAR,
            metadata={},
            user_message="remember the car",
        )
        row = conn.execute(
            "SELECT id, learned_at, source FROM facts WHERE text = ?",
            (SYN_CAR,),
        ).fetchone()
        self.assertIsNotNone(row["learned_at"])
        self.assertEqual(row["source"], store.SOURCE_NOTIFY)
        fact_id = row["id"]

        self._write_files(memory=[SYN_A, SYN_CAR_BLUE])
        fact_index.handle_memory_write(
            conn,
            self.home,
            action="replace",
            target="memory",
            content=SYN_CAR_BLUE,
            metadata={"old_text": "green"},
            user_message="Actually, the car is blue, not green",
        )
        hist = conn.execute(
            "SELECT COUNT(*) AS c FROM fact_history WHERE fact_id = ?",
            (fact_id,),
        ).fetchone()["c"]
        self.assertEqual(hist, 1)
        active = conn.execute(
            "SELECT text FROM facts WHERE id = ?",
            (fact_id,),
        ).fetchone()["text"]
        self.assertEqual(active, SYN_CAR_BLUE)

        self._write_files(memory=[SYN_A])
        fact_index.handle_memory_write(
            conn,
            self.home,
            action="remove",
            target="memory",
            content=SYN_CAR_BLUE,
            metadata={"old_text": SYN_CAR_BLUE},
            user_message="forget the car color",
        )
        self.assertIsNone(
            conn.execute("SELECT id FROM facts WHERE id = ?", (fact_id,)).fetchone()
        )
        tomb = conn.execute(
            "SELECT record_kind, counts_json FROM tombstones WHERE id = ?",
            (fact_id,),
        ).fetchone()
        self.assertEqual(tomb["record_kind"], "fact")
        self.assertIn("fact_rows", tomb["counts_json"])
        self._assert_no_synthetic_in_artifacts(conn)
        conn.close()

    def test_replace_with_dont_keep_erases(self) -> None:
        conn = self._open()
        self._write_files(user=[SYN_PHONE])
        fact_index.run_file_check(conn, self.home, force=True)
        row = conn.execute("SELECT id FROM facts WHERE text = ?", (SYN_PHONE,)).fetchone()
        fact_id = row["id"]
        self._write_files(user=[SYN_PHONE_REDUCED])
        fact_index.handle_memory_write(
            conn,
            self.home,
            action="replace",
            target="user",
            content=SYN_PHONE_REDUCED,
            metadata={"old_text": "555-0100"},
            user_message=(
                "don't keep my demo phone number anymore, just keep that I have a landline"
            ),
        )
        self.assertIsNone(
            conn.execute("SELECT id FROM facts WHERE id = ?", (fact_id,)).fetchone()
        )
        neu = conn.execute(
            "SELECT source, learned_at FROM facts WHERE text = ?",
            (SYN_PHONE_REDUCED,),
        ).fetchone()
        self.assertIsNotNone(neu)
        self.assertEqual(neu["source"], store.SOURCE_FILE_CHECK)
        self.assertIsNone(neu["learned_at"])
        hist = conn.execute(
            "SELECT COUNT(*) AS c FROM fact_history WHERE fact_id = ?",
            (fact_id,),
        ).fetchone()["c"]
        self.assertEqual(hist, 0)
        self._assert_no_synthetic_in_artifacts(conn)
        conn.close()

    def test_dont_forget_keeps_history(self) -> None:
        conn = self._open()
        self._write_files(user=[SYN_ADDR])
        fact_index.run_file_check(conn, self.home, force=True)
        fact_id = conn.execute(
            "SELECT id FROM facts WHERE text = ?", (SYN_ADDR,)
        ).fetchone()["id"]
        new = "[person] Demo address is 2 Example Lane."
        self._write_files(user=[new])
        fact_index.handle_memory_write(
            conn,
            self.home,
            action="replace",
            target="user",
            content=new,
            metadata={"old_text": "1 Example Lane"},
            user_message="Don't forget that I moved — address is actually 2 Example Lane",
        )
        hist = conn.execute(
            "SELECT COUNT(*) AS c FROM fact_history WHERE fact_id = ?",
            (fact_id,),
        ).fetchone()["c"]
        self.assertEqual(hist, 1)
        self.assertEqual(
            conn.execute("SELECT text FROM facts WHERE id = ?", (fact_id,)).fetchone()[
                "text"
            ],
            new,
        )
        conn.close()


class TestFileCheck(_TempHome):
    def test_bypass_add_and_removal(self) -> None:
        conn = self._open()
        self._write_files(memory=[SYN_A])
        fact_index.run_file_check(conn, self.home, force=True)
        self.assertEqual(fact_index.count_active(conn), 1)
        self._write_files(memory=[SYN_A, SYN_B])
        r = fact_index.run_file_check(conn, self.home, force=True)
        self.assertEqual(r["added"], 1)
        row = conn.execute(
            "SELECT source, learned_at FROM facts WHERE text = ?",
            (SYN_B,),
        ).fetchone()
        self.assertEqual(row["source"], store.SOURCE_FILE_CHECK)
        self.assertIsNone(row["learned_at"])
        self._write_files(memory=[SYN_A])
        r2 = fact_index.run_file_check(conn, self.home, force=True)
        self.assertEqual(r2["erased"], 1)
        self.assertIsNone(
            conn.execute("SELECT id FROM facts WHERE text = ?", (SYN_B,)).fetchone()
        )
        conn.close()

    def test_whitespace_reformat_no_change(self) -> None:
        conn = self._open()
        self._write_files(memory=[SYN_A])
        fact_index.run_file_check(conn, self.home, force=True)
        (self.memories / "MEMORY.md").write_text(SYN_A + "\n", encoding="utf-8")
        before = fact_index.count_active(conn)
        r = fact_index.run_file_check(conn, self.home, force=True)
        self.assertEqual(r["added"], 0)
        self.assertEqual(r["erased"], 0)
        self.assertEqual(fact_index.count_active(conn), before)
        conn.close()

    def test_unchanged_hash_skipped(self) -> None:
        conn = self._open()
        self._write_files(memory=[SYN_A])
        fact_index.run_file_check(conn, self.home, force=True)
        r = fact_index.run_file_check(conn, self.home, force=False)
        self.assertTrue(r["skipped_hash_match"])
        self.assertFalse(r["ran"])
        conn.close()

    def test_initial_import_learned_at_null(self) -> None:
        self._write_files(user=[SYN_ADDR], memory=[SYN_A])
        p = ZolaMemoryProvider()
        p.initialize("s", hermes_home=str(self.home))
        conn = p._conn
        self.assertEqual(fact_index.count_active(conn), 2)
        self.assertEqual(fact_index.count_learned_null(conn), 2)
        fact_index.handle_memory_write(
            conn,
            self.home,
            action="add",
            target="memory",
            content=SYN_CAR,
            metadata={},
            user_message="note",
        )
        row = conn.execute(
            "SELECT learned_at FROM facts WHERE text = ?",
            (SYN_CAR,),
        ).fetchone()
        self.assertIsNotNone(row["learned_at"])
        p.shutdown()


class TestReplaceUnmatched(_TempHome):
    def test_store_lagging_bypass(self) -> None:
        conn = self._open()
        self._write_files(memory=[SYN_A])
        fact_index.run_file_check(conn, self.home, force=True)
        # Bypass already rewrote the file to SYN_B; notify replace's old_text is absent from store
        self._write_files(memory=[SYN_B])
        fact_index.handle_memory_write(
            conn,
            self.home,
            action="replace",
            target="memory",
            content=SYN_B,
            metadata={"old_text": "text that was never indexed"},
            user_message="actually it's Blue Lantern",
        )
        self.assertIsNone(
            conn.execute("SELECT id FROM facts WHERE text = ?", (SYN_A,)).fetchone()
        )
        neu = conn.execute(
            "SELECT source, learned_at FROM facts WHERE text = ?",
            (SYN_B,),
        ).fetchone()
        self.assertEqual(neu["source"], store.SOURCE_FILE_CHECK)
        self.assertIsNone(neu["learned_at"])
        log = (self.home / "logs" / memlog.LOG_FILENAME).read_text(encoding="utf-8")
        self.assertIn(memlog.LOG_EVENT_REPLACE_UNMATCHED, log)
        self._assert_no_synthetic_in_artifacts(conn)
        conn.close()

    def test_ambiguous_substring(self) -> None:
        conn = self._open()
        a = "[project] Demo alpha token ZZMARKER is one."
        b = "[project] Demo beta token ZZMARKER is two."
        self._write_files(memory=[a, b])
        fact_index.run_file_check(conn, self.home, force=True)
        new_a = "[project] Demo alpha token ZZMARKER is updated."
        self._write_files(memory=[new_a, b])
        fact_index.handle_memory_write(
            conn,
            self.home,
            action="replace",
            target="memory",
            content=new_a,
            metadata={"old_text": "ZZMARKER"},
            user_message="update the alpha one",
        )
        texts = {
            r["text"]
            for r in conn.execute(
                "SELECT text FROM facts WHERE state = ?",
                (store.STATE_ACTIVE,),
            )
        }
        self.assertIn(new_a, texts)
        self.assertIn(b, texts)
        self.assertNotIn(a, texts)
        conn.close()


class TestEraseFailure(_TempHome):
    def test_rollback_and_file_check_recovery(self) -> None:
        conn = self._open()
        self._write_files(memory=[SYN_A])
        fact_index.run_file_check(conn, self.home, force=True)
        fact_id = conn.execute(
            "SELECT id FROM facts WHERE text = ?", (SYN_A,)
        ).fetchone()["id"]

        def boom():
            raise RuntimeError("simulated erase failure")

        forget.set_erase_failure_hook(boom)
        self._write_files(memory=[])
        ok = forget.erase_fact(conn, fact_id, reason=forget.ERASE_REASON_FILE_CHECK)
        self.assertFalse(ok)
        self.assertIsNotNone(
            conn.execute("SELECT id FROM facts WHERE id = ?", (fact_id,)).fetchone()
        )
        fts = conn.execute(
            "SELECT COUNT(*) AS c FROM facts_fts WHERE fact_id = ?",
            (fact_id,),
        ).fetchone()["c"]
        self.assertEqual(fts, 1)
        pending = forget._load_pending(conn)
        self.assertIn(fact_id, pending)

        forget.set_erase_failure_hook(None)

        def fail_mark(conn_arg, fid):
            memlog.write_event(memlog.LOG_EVENT_PENDING_ERASURE_MARK, fact_id=fid, ok=False)

        with mock.patch.object(forget, "_mark_pending_erasure", side_effect=fail_mark):
            forget.set_erase_failure_hook(boom)
            forget.erase_fact(conn, fact_id, reason=forget.ERASE_REASON_FILE_CHECK)
            forget.set_erase_failure_hook(None)

        r = fact_index.run_file_check(conn, self.home, force=True)
        self.assertGreaterEqual(r["erased"], 1)
        self.assertIsNone(
            conn.execute("SELECT id FROM facts WHERE id = ?", (fact_id,)).fetchone()
        )
        self._assert_no_synthetic_in_artifacts(conn)
        conn.close()


class TestFtsMissing(unittest.TestCase):
    def test_is_available_false(self) -> None:
        with mock.patch.object(store, "fts5_available", return_value=False):
            p = ZolaMemoryProvider()
            self.assertFalse(p.is_available())


class TestPhase4bPendingRetry(_TempHome):
    def test_failed_erase_blocks_hash_skip_then_retries(self) -> None:
        conn = self._open()
        self._write_files(memory=[SYN_A])
        fact_index.run_file_check(conn, self.home, force=True)
        fact_id = conn.execute(
            "SELECT id FROM facts WHERE text = ?", (SYN_A,)
        ).fetchone()["id"]
        stored_hash = store.meta_get(conn, store.META_FILES_SHA256)

        def boom():
            raise RuntimeError("simulated erase failure")

        forget.set_erase_failure_hook(boom)
        self._write_files(memory=[])  # bypass removal
        r = fact_index.run_file_check(conn, self.home, force=True)
        self.assertGreaterEqual(r.get("erase_failures", 0), 1)
        # Hash must not advance while erase failed
        self.assertEqual(store.meta_get(conn, store.META_FILES_SHA256), stored_hash)
        self.assertIsNotNone(
            conn.execute("SELECT id FROM facts WHERE id = ?", (fact_id,)).fetchone()
        )
        self.assertIn(fact_id, forget._load_pending(conn))

        forget.set_erase_failure_hook(None)
        # Simulate matching hash (old bug) — pending_erasures must still force a retry
        empty_digest = store.combined_files_sha256(self.home)
        with store.locked(conn):
            conn.execute("BEGIN IMMEDIATE")
            store.meta_set(conn, store.META_FILES_SHA256, empty_digest)
            conn.execute("COMMIT")
        r2 = fact_index.run_file_check(conn, self.home, force=False)
        self.assertFalse(r2.get("skipped_hash_match"))
        self.assertIsNone(
            conn.execute("SELECT id FROM facts WHERE id = ?", (fact_id,)).fetchone()
        )
        conn.close()


class TestPhase4bReadFailure(_TempHome):
    def test_unreadable_user_md_aborts_check(self) -> None:
        conn = self._open()
        self._write_files(user=[SYN_ADDR], memory=[SYN_A])
        fact_index.run_file_check(conn, self.home, force=True)
        before_ids = {
            r["id"]
            for r in conn.execute("SELECT id FROM facts WHERE state = 'active'")
        }
        before_learned = {
            (r["id"], r["learned_at"])
            for r in conn.execute("SELECT id, learned_at FROM facts")
        }
        before_hist = conn.execute("SELECT COUNT(*) AS c FROM fact_history").fetchone()[
            "c"
        ]
        before_hash = store.meta_get(conn, store.META_FILES_SHA256)

        real_read = store.read_memory_file

        def flaky(path: Path):
            if path.name == "USER.md":
                return "", False
            return real_read(path)

        with mock.patch.object(store, "read_memory_file", side_effect=flaky):
            r = fact_index.run_file_check(conn, self.home, force=True)
        self.assertTrue(r.get("read_error"))
        self.assertEqual(r.get("added"), 0)
        self.assertEqual(r.get("erased"), 0)
        after_ids = {
            r["id"]
            for r in conn.execute("SELECT id FROM facts WHERE state = 'active'")
        }
        self.assertEqual(after_ids, before_ids)
        after_learned = {
            (r["id"], r["learned_at"])
            for r in conn.execute("SELECT id, learned_at FROM facts")
        }
        self.assertEqual(after_learned, before_learned)
        self.assertEqual(
            conn.execute("SELECT COUNT(*) AS c FROM fact_history").fetchone()["c"],
            before_hist,
        )
        self.assertEqual(store.meta_get(conn, store.META_FILES_SHA256), before_hash)
        log = (self.home / "logs" / memlog.LOG_FILENAME).read_text(encoding="utf-8")
        self.assertIn(memlog.LOG_EVENT_FILE_CHECK_READ_ERROR, log)

        # Next successful check behaves normally (bypass add)
        self._write_files(user=[SYN_ADDR], memory=[SYN_A, SYN_B])
        r2 = fact_index.run_file_check(conn, self.home, force=True)
        self.assertEqual(r2.get("added"), 1)
        conn.close()


class TestPhase4bConcurrency(_TempHome):
    def test_concurrent_notify_and_file_check(self) -> None:
        conn = self._open()
        self._write_files(memory=[SYN_A])
        fact_index.run_file_check(conn, self.home, force=True)
        errors: list[BaseException] = []

        def adder(n: int) -> None:
            try:
                for i in range(8):
                    text = f"[project] Demo concurrent item {n}-{i}."
                    self._write_files(memory=[SYN_A, text])
                    fact_index.handle_memory_write(
                        conn,
                        self.home,
                        action="add",
                        target="memory",
                        content=text,
                        metadata={},
                        user_message="note",
                    )
            except BaseException as exc:  # noqa: BLE001
                errors.append(exc)

        def checker() -> None:
            try:
                for _ in range(12):
                    fact_index.run_file_check(conn, self.home, force=True)
            except BaseException as exc:  # noqa: BLE001
                errors.append(exc)

        threads = [
            threading.Thread(target=adder, args=(1,)),
            threading.Thread(target=adder, args=(2,)),
            threading.Thread(target=checker),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)
        self.assertEqual(errors, [])
        active = fact_index.count_active(conn)
        self.assertGreaterEqual(active, 1)
        # No orphan FTS rows without facts
        orphan = conn.execute(
            "SELECT COUNT(*) AS c FROM facts_fts f "
            "WHERE NOT EXISTS (SELECT 1 FROM facts x WHERE x.id = f.fact_id)"
        ).fetchone()["c"]
        self.assertEqual(orphan, 0)
        conn.close()


class TestPhase4bRemoveUnmatched(_TempHome):
    def test_remove_no_unique_match_runs_file_check(self) -> None:
        conn = self._open()
        self._write_files(memory=[SYN_A, SYN_B])
        fact_index.run_file_check(conn, self.home, force=True)
        # File already lost SYN_A via bypass; remove notify with unmatched old_text
        self._write_files(memory=[SYN_B])
        fact_index.handle_memory_write(
            conn,
            self.home,
            action="remove",
            target="memory",
            content=SYN_A,
            metadata={"old_text": "text that was never indexed"},
            user_message="remove that",
        )
        self.assertIsNone(
            conn.execute("SELECT id FROM facts WHERE text = ?", (SYN_A,)).fetchone()
        )
        self.assertIsNotNone(
            conn.execute("SELECT id FROM facts WHERE text = ?", (SYN_B,)).fetchone()
        )
        log = (self.home / "logs" / memlog.LOG_FILENAME).read_text(encoding="utf-8")
        self.assertIn("remove_unmatched", log)
        conn.close()


class TestTimeContextStamp(unittest.TestCase):
    def test_stamp_format_integers_and_english_names(self) -> None:
        now = datetime(2026, 10, 2, 15, 45, tzinfo=_PDT)
        self.assertEqual(
            time_context.format_stamp(now),
            "[Time: Fri Oct 2, 3:45 PM PDT (UTC\u221207:00)]",
        )
        self.assertEqual(
            time_context.format_stamp_body(now),
            "Fri Oct 2, 3:45 PM PDT (UTC\u221207:00)",
        )

    def test_stamp_midnight_and_noon(self) -> None:
        midnight = datetime(2026, 10, 3, 0, 17, tzinfo=_PDT)
        self.assertEqual(
            time_context.format_stamp(midnight),
            "[Time: Sat Oct 3, 12:17 AM PDT (UTC\u221207:00)]",
        )
        noon = datetime(2026, 10, 3, 12, 5, tzinfo=_PDT)
        self.assertEqual(
            time_context.format_stamp(noon),
            "[Time: Sat Oct 3, 12:05 PM PDT (UTC\u221207:00)]",
        )

    def test_stamp_year_boundary(self) -> None:
        now = datetime(2027, 1, 1, 0, 1, tzinfo=_PST)
        self.assertEqual(
            time_context.format_stamp(now),
            "[Time: Fri Jan 1, 12:01 AM PST (UTC\u221208:00)]",
        )

    def test_stamp_locale_independent_dow_month(self) -> None:
        # P6-TIME: fixed English constants — not strftime %a/%b — P6-D05
        now = datetime(2026, 3, 15, 9, 5, tzinfo=_PDT)  # Sunday
        body = time_context.format_stamp_body(now)
        self.assertTrue(body.startswith("Sun Mar 15,"))
        self.assertIn("9:05 AM", body)
        self.assertIn("(UTC\u221207:00)", body)
        for name in time_context.DOW_NAMES:
            self.assertEqual(len(name), 3)
        for name in time_context.MONTH_NAMES:
            self.assertEqual(len(name), 3)

    def test_windows_tz_abbrev_and_utc_fallback(self) -> None:
        long_tz = timezone(timedelta(hours=-7), name="Pacific Daylight Time")
        now = datetime(2026, 10, 2, 15, 45, tzinfo=long_tz)
        self.assertEqual(time_context.short_zone_label(now), "PDT")
        odd = timezone(timedelta(hours=5, minutes=30), name="Some Long Zone Name")
        odd_now = datetime(2026, 10, 2, 15, 45, tzinfo=odd)
        self.assertEqual(time_context.short_zone_label(odd_now), "UTC+05:30")

    def test_stamp_always_includes_numeric_utc_offset(self) -> None:
        # P7-LATENCY: PDT + explicit offset — P7-D10
        pdt = datetime(2026, 10, 6, 15, 16, tzinfo=_PDT)
        self.assertEqual(
            time_context.format_stamp(pdt),
            "[Time: Tue Oct 6, 3:16 PM PDT (UTC\u221207:00)]",
        )
        self.assertEqual(time_context.utc_offset_label(pdt), "UTC\u221207:00")

    def test_stamp_dst_and_standard_offsets(self) -> None:
        # P7-LATENCY: DST vs standard numeric offsets — P7-D10
        dst = datetime(2026, 10, 2, 15, 45, tzinfo=_PDT)
        std = datetime(2027, 1, 1, 12, 0, tzinfo=_PST)
        self.assertIn("(UTC\u221207:00)", time_context.format_stamp(dst))
        self.assertIn("PDT", time_context.format_stamp(dst))
        self.assertIn("(UTC\u221208:00)", time_context.format_stamp(std))
        self.assertIn("PST", time_context.format_stamp(std))

    def test_stamp_zone_with_no_percent_z_abbreviation(self) -> None:
        # P7-LATENCY: long/unknown %Z → offset alone (no doubled parenthetical) — P7-D10
        odd = timezone(timedelta(hours=5, minutes=30), name="Some Long Zone Name")
        now = datetime(2026, 10, 2, 15, 45, tzinfo=odd)
        body = time_context.format_stamp_body(now)
        self.assertEqual(body, "Fri Oct 2, 3:45 PM UTC+05:30")
        self.assertNotIn("(", body)
        self.assertEqual(time_context.utc_offset_label(now), "UTC+05:30")


class TestTimeContextRelative(unittest.TestCase):
    def setUp(self) -> None:
        # Pin fixed offset so calendar math does not depend on the host zone.
        time_context.set_clock_for_tests(None, timezone=_PDT)

    def tearDown(self) -> None:
        time_context.set_clock_for_tests(None)

    def test_brian_calendar_and_singular_cases(self) -> None:
        mon = datetime(2026, 9, 28, 23, 0, tzinfo=_PDT)
        wed = datetime(2026, 9, 30, 5, 0, tzinfo=_PDT)
        self.assertEqual(time_context.format_relative(wed, mon), "2 days ago")

        day = datetime(2026, 10, 2, 12, 0, tzinfo=_PDT)
        self.assertEqual(
            time_context.format_relative(day + timedelta(minutes=61), day),
            "about an hour ago",
        )
        self.assertEqual(
            time_context.format_relative(day + timedelta(minutes=1), day),
            "1 minute ago",
        )
        self.assertEqual(
            time_context.format_relative(day + timedelta(days=15), day),
            "2 weeks ago",
        )

    def test_relative_thresholds(self) -> None:
        base = datetime(2026, 10, 2, 12, 0, tzinfo=_PDT)
        self.assertEqual(
            time_context.format_relative(base + timedelta(seconds=30), base),
            "less than a minute ago",
        )
        self.assertEqual(
            time_context.format_relative(base + timedelta(minutes=45), base),
            "45 minutes ago",
        )
        self.assertEqual(
            time_context.format_relative(base + timedelta(hours=5), base),
            "about 5 hours ago",
        )
        yesterday = datetime(2026, 10, 1, 20, 10, tzinfo=_PDT)
        self.assertEqual(
            time_context.format_relative(base, yesterday), "yesterday"
        )
        self.assertEqual(
            time_context.format_relative(base + timedelta(days=3), base),
            "3 days ago",
        )

    def test_dst_spring_forward_and_fall_back(self) -> None:
        # Synthetic fixed-offset labels (stamp body uses clock fields, not OS DST tables)
        spring_before = datetime(2026, 3, 8, 1, 30, tzinfo=_PST)
        spring_after = datetime(2026, 3, 8, 3, 30, tzinfo=_PDT)
        self.assertEqual(
            time_context.format_stamp(spring_before),
            "[Time: Sun Mar 8, 1:30 AM PST (UTC\u221208:00)]",
        )
        self.assertEqual(
            time_context.format_stamp(spring_after),
            "[Time: Sun Mar 8, 3:30 AM PDT (UTC\u221207:00)]",
        )
        fall = datetime(2026, 11, 1, 1, 30, tzinfo=_PST)
        self.assertEqual(
            time_context.format_stamp(fall),
            "[Time: Sun Nov 1, 1:30 AM PST (UTC\u221208:00)]",
        )


class TestTimeContextBuildAndHook(_TempHome):
    def setUp(self) -> None:
        super().setUp()
        # Fixed-offset path for non-ZoneInfo gap tests.
        time_context.set_clock_for_tests(None, timezone=_PDT)

    def tearDown(self) -> None:
        time_context.set_clock_for_tests(None)
        super().tearDown()

    def _provider_with_conn(self):
        p = ZolaMemoryProvider()
        p._conn = self._open()
        p._hermes_home = self.home
        p._initialized = True
        return p

    def test_gap_threshold_29_30_31(self) -> None:
        now = datetime(2026, 10, 2, 15, 0, tzinfo=_PDT)
        last29 = (now - timedelta(minutes=29)).isoformat(timespec="seconds")
        last30 = (now - timedelta(minutes=30)).isoformat(timespec="seconds")
        last31 = (now - timedelta(minutes=31)).isoformat(timespec="seconds")
        self.assertEqual(
            time_context.build_turn_time_context(now, last29),
            time_context.format_stamp(now),
        )
        block30 = time_context.build_turn_time_context(now, last30)
        self.assertIn("\n[Gap:", block30)
        self.assertIn("30 minutes ago", block30)
        block31 = time_context.build_turn_time_context(now, last31)
        self.assertIn("\n[Gap:", block31)
        self.assertIn("31 minutes ago", block31)

    def test_first_run_no_gap_line(self) -> None:
        now = datetime(2026, 10, 2, 15, 45, tzinfo=_PDT)
        stamp = "[Time: Fri Oct 2, 3:45 PM PDT (UTC\u221207:00)]"
        self.assertEqual(time_context.build_turn_time_context(now, None), stamp)
        self.assertEqual(time_context.build_turn_time_context(now, ""), stamp)
        self.assertEqual(
            time_context.build_turn_time_context(now, "not-a-timestamp"), stamp
        )

    def test_block_joined_with_newline(self) -> None:
        now = datetime(2026, 10, 2, 15, 45, tzinfo=_PDT)
        last = datetime(2026, 9, 30, 21, 14, tzinfo=_PDT)
        block = time_context.build_turn_time_context(
            now, last.isoformat(timespec="seconds")
        )
        self.assertEqual(
            block,
            "[Time: Fri Oct 2, 3:45 PM PDT (UTC\u221207:00)]\n"
            "[Gap: Brian's last message to me was 2 days ago "
            "(Wed Sep 30, 9:14 PM PDT (UTC\u221207:00)).]",
        )

    def test_allow_list_predicate(self) -> None:
        self.assertTrue(time_context.is_user_turn("tui", ""))
        self.assertTrue(time_context.is_user_turn("TUI", None))  # type: ignore[arg-type]
        self.assertFalse(time_context.is_user_turn("tui", "parent-1"))
        for platform in (
            "cron",
            "subagent",
            "curator",
            "gateway_hygiene",
            "some_new_platform",
        ):
            self.assertFalse(time_context.is_user_turn(platform, ""))

    def test_hook_non_user_turn_no_marker_move(self) -> None:
        provider = self._provider_with_conn()
        now = datetime(2026, 10, 2, 15, 45, tzinfo=_PDT)
        time_context.set_clock_for_tests(lambda: now)
        prior = "2026-10-01T12:00:00-07:00"
        with store.locked(provider._conn):
            provider._conn.execute("BEGIN IMMEDIATE")
            store.meta_set(provider._conn, store.META_LAST_INTERACTION_AT, prior)
            provider._conn.commit()
        for kwargs in (
            {"platform": "cron", "parent_session_id": "", "session_id": "s1"},
            {"platform": "tui", "parent_session_id": "child", "session_id": "s1"},
            {"platform": "subagent", "parent_session_id": "p", "session_id": "s1"},
            {"platform": "curator", "parent_session_id": "", "session_id": "s1"},
            {
                "platform": "some_new_platform",
                "parent_session_id": "",
                "session_id": "s1",
            },
        ):
            result = time_context.handle_pre_llm_call(provider, **kwargs)
            self.assertIsNone(result)
            self.assertEqual(
                store.meta_get(provider._conn, store.META_LAST_INTERACTION_AT), prior
            )
        provider._conn.close()

    def test_hook_success_updates_marker_to_captured_now(self) -> None:
        provider = self._provider_with_conn()
        now = datetime(2026, 10, 2, 15, 45, 30, tzinfo=_PDT)
        time_context.set_clock_for_tests(lambda: now)
        last = datetime(2026, 10, 2, 10, 0, tzinfo=_PDT)
        with store.locked(provider._conn):
            provider._conn.execute("BEGIN IMMEDIATE")
            store.meta_set(
                provider._conn,
                store.META_LAST_INTERACTION_AT,
                last.isoformat(timespec="seconds"),
            )
            provider._conn.commit()
        result = time_context.handle_pre_llm_call(
            provider,
            platform="tui",
            parent_session_id="",
            session_id="sess-time",
            user_message="hello from Brian synthetic",
        )
        self.assertIsInstance(result, dict)
        self.assertIn("context", result)
        self.assertTrue(
            result["context"].startswith(
                "[Time: Fri Oct 2, 3:45 PM PDT (UTC\u221207:00)]"
            )
        )
        self.assertIn("[Gap:", result["context"])
        marker = store.meta_get(provider._conn, store.META_LAST_INTERACTION_AT)
        self.assertEqual(marker, time_context.marker_iso(now))
        self.assertEqual(marker, "2026-10-02T15:45:30-07:00")
        # Marker is time-only (no gap wording)
        self.assertNotIn("Gap", marker)
        self.assertNotIn("ago", marker)
        log = (self.home / "logs" / memlog.LOG_FILENAME).read_text(encoding="utf-8")
        self.assertIn(memlog.LOG_EVENT_TIME_CONTEXT, log)
        self.assertIn(memlog.LOG_EVENT_TIME_MARKER_UPDATE, log)
        self.assertIn(memlog.LOG_EVENT_PRE_LLM_CALL, log)
        self.assertNotIn("hello from Brian synthetic", log)
        provider._conn.close()

    def test_ordering_construction_failure_leaves_marker(self) -> None:
        provider = self._provider_with_conn()
        now = datetime(2026, 10, 2, 15, 45, tzinfo=_PDT)
        time_context.set_clock_for_tests(lambda: now)
        prior = "2026-09-30T21:14:00-07:00"
        with store.locked(provider._conn):
            provider._conn.execute("BEGIN IMMEDIATE")
            store.meta_set(provider._conn, store.META_LAST_INTERACTION_AT, prior)
            provider._conn.commit()

        def boom(*_a, **_k):
            raise RuntimeError("simulated build failure")

        with mock.patch.object(time_context, "build_turn_time_context", side_effect=boom):
            result = time_context.handle_pre_llm_call(
                provider,
                platform="tui",
                parent_session_id="",
                session_id="sess-fail",
            )
        self.assertIsNone(result)
        self.assertEqual(
            store.meta_get(provider._conn, store.META_LAST_INTERACTION_AT), prior
        )
        log = (self.home / "logs" / memlog.LOG_FILENAME).read_text(encoding="utf-8")
        self.assertIn(f"{memlog.LOG_EVENT_TIME_CONTEXT} ok=false", log)
        provider._conn.close()

    def test_capture_now_raising_leaves_marker(self) -> None:
        provider = self._provider_with_conn()
        prior = "2026-09-30T21:14:00-07:00"
        with store.locked(provider._conn):
            provider._conn.execute("BEGIN IMMEDIATE")
            store.meta_set(provider._conn, store.META_LAST_INTERACTION_AT, prior)
            provider._conn.commit()

        def boom():
            raise RuntimeError("simulated clock failure")

        time_context.set_clock_for_tests(boom, timezone=_PDT)
        result = time_context.handle_pre_llm_call(
            provider,
            platform="tui",
            parent_session_id="",
            session_id="sess-clock-fail",
        )
        self.assertIsNone(result)
        self.assertEqual(
            store.meta_get(provider._conn, store.META_LAST_INTERACTION_AT), prior
        )
        log = (self.home / "logs" / memlog.LOG_FILENAME).read_text(encoding="utf-8")
        self.assertIn(f"{memlog.LOG_EVENT_TIME_CONTEXT} ok=false", log)
        provider._conn.close()


class TestTimeContextZoneInfoDst(_TempHome):
    """Real America/Los_Angeles zoneinfo across DST (configured + system-local)."""

    def tearDown(self) -> None:
        time_context.set_clock_for_tests(None)
        super().tearDown()

    def _assert_fall_back_gap(self) -> None:
        now = datetime(2026, 11, 2, 9, 0, tzinfo=_LA)
        block = time_context.build_turn_time_context(now, "2026-10-31T21:00:00-07:00")
        # P7-LATENCY: gap past_body includes numeric offset — P7-D10
        self.assertIn("Sat Oct 31, 9:00 PM PDT (UTC\u221207:00)", block)
        self.assertIn("2 days ago", block)
        self.assertIn("Mon Nov 2, 9:00 AM PST (UTC\u221208:00)", block)
        self.assertNotIn("8:00 PM", block)

    def _assert_spring_forward_gap(self) -> None:
        now = datetime(2026, 3, 8, 10, 0, tzinfo=_LA)
        block = time_context.build_turn_time_context(now, "2026-03-07T22:00:00-08:00")
        self.assertIn("Sat Mar 7, 10:00 PM PST (UTC\u221208:00)", block)
        self.assertIn("yesterday", block)
        self.assertIn("Sun Mar 8, 10:00 AM PDT (UTC\u221207:00)", block)

    def test_fall_back_configured_zone(self) -> None:
        time_context.set_clock_for_tests(
            lambda: datetime(2026, 11, 2, 9, 0, tzinfo=_LA),
            timezone=_LA,
        )
        self._assert_fall_back_gap()

    def test_fall_back_system_local(self) -> None:
        time_context.set_clock_for_tests(
            lambda: datetime(2026, 11, 2, 9, 0, tzinfo=_LA),
            timezone=None,
        )
        self._assert_fall_back_gap()

    def test_spring_forward_configured_zone(self) -> None:
        time_context.set_clock_for_tests(
            lambda: datetime(2026, 3, 8, 10, 0, tzinfo=_LA),
            timezone=_LA,
        )
        self._assert_spring_forward_gap()

    def test_spring_forward_system_local(self) -> None:
        time_context.set_clock_for_tests(
            lambda: datetime(2026, 3, 8, 10, 0, tzinfo=_LA),
            timezone=None,
        )
        self._assert_spring_forward_gap()


class TestSessionRegistry(_TempHome):
    """P6-TIME FIX-B: session_id → provider registry for pre_llm_call."""

    def setUp(self) -> None:
        super().setUp()
        registry.clear_for_tests()
        time_context.set_clock_for_tests(
            lambda: datetime(2026, 10, 2, 15, 45, tzinfo=_PDT),
            timezone=_PDT,
        )
        self._home_b = Path(tempfile.mkdtemp(prefix="zola_memory_test_b_"))
        (self._home_b / "memories").mkdir(parents=True)
        (self._home_b / "memories" / "USER.md").write_text("", encoding="utf-8")
        (self._home_b / "memories" / "MEMORY.md").write_text("", encoding="utf-8")

    def tearDown(self) -> None:
        registry.clear_for_tests()
        time_context.set_clock_for_tests(None)
        shutil.rmtree(self._home_b, ignore_errors=True)
        super().tearDown()

    def _hook(self, session_id: str, **extra):
        kwargs = {
            "platform": "tui",
            "parent_session_id": "",
            "session_id": session_id,
            "user_message": "synthetic registry probe",
        }
        kwargs.update(extra)
        return time_context.pre_llm_call_hook(**kwargs)

    def _log(self) -> str:
        path = self.home / "logs" / memlog.LOG_FILENAME
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def test_two_providers_hook_routes_by_session(self) -> None:
        pa = ZolaMemoryProvider()
        pb = ZolaMemoryProvider()
        pa.initialize("sid-A", hermes_home=str(self.home))
        pb.initialize("sid-B", hermes_home=str(self._home_b))
        seen = []
        real_handle = time_context.handle_pre_llm_call

        def capture(provider, **kwargs):
            seen.append(provider)
            return real_handle(provider, **kwargs)

        with mock.patch.object(
            time_context, "handle_pre_llm_call", side_effect=capture
        ):
            ra = self._hook("sid-A")
            rb = self._hook("sid-B")
        self.assertIsNotNone(ra)
        self.assertIsNotNone(rb)
        self.assertEqual(seen, [pa, pb])
        self.assertIs(seen[0]._conn, pa._conn)
        self.assertIs(seen[1]._conn, pb._conn)
        pa.shutdown()
        pb.shutdown()

    def test_register_without_initialize_does_not_break_active_session(self) -> None:
        pa = ZolaMemoryProvider()
        pa.initialize("sid-A", hermes_home=str(self.home))

        class _Ctx:
            def __init__(self) -> None:
                self.hooks = []
                self.providers = []

            def register_memory_provider(self, p) -> None:
                self.providers.append(p)

            def register_hook(self, name, fn) -> None:
                self.hooks.append((name, fn))

            def _plugin_context(self):
                class _PC:
                    llm = None

                return _PC()

        ctx = _Ctx()
        import importlib.util

        init_path = Path(__file__).resolve().parents[1] / "__init__.py"
        spec = importlib.util.spec_from_file_location("_zola_memory_pkg_init", init_path)
        zola = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        # Avoid double-exec if already loaded by a prior test
        if "_zola_memory_pkg_init" in sys.modules:
            zola = sys.modules["_zola_memory_pkg_init"]
        else:
            sys.modules["_zola_memory_pkg_init"] = zola
            spec.loader.exec_module(zola)
        zola.register(ctx)
        self.assertEqual(len(ctx.providers), 1)
        self.assertIsNot(ctx.providers[0], pa)
        self.assertIs(zola._provider, ctx.providers[0])
        self.assertIsNone(ctx.providers[0]._conn)
        # Hook re-registered (no once-guard); skills_tool path left A intact.
        self.assertIn(("pre_llm_call", zola._pre_llm_call_hook), ctx.hooks)
        result = self._hook("sid-A")
        self.assertIsNotNone(result)
        self.assertIn("context", result)
        pa.shutdown()

    def test_shutdown_isolation_and_no_provider_leaves_marker(self) -> None:
        pa = ZolaMemoryProvider()
        pb = ZolaMemoryProvider()
        pa.initialize("sid-A", hermes_home=str(self.home))
        pb.initialize("sid-B", hermes_home=str(self._home_b))
        self.assertIsNotNone(self._hook("sid-A"))
        marker = store.meta_get(pa._conn, store.META_LAST_INTERACTION_AT)
        self.assertTrue(marker)

        pb.shutdown()
        self.assertIsNotNone(self._hook("sid-A"))
        self.assertEqual(
            store.meta_get(pa._conn, store.META_LAST_INTERACTION_AT), marker
        )

        # Re-read after second hook (marker may advance); then A shutdown.
        marker_after = store.meta_get(pa._conn, store.META_LAST_INTERACTION_AT)
        # Keep a second read-conn open after pa.shutdown closes its conn.
        observer = store.open_store(self.home)
        try:
            with store.locked(observer):
                frozen = store.meta_get(observer, store.META_LAST_INTERACTION_AT)
            self.assertEqual(frozen, marker_after)
            pa.shutdown()
            result = self._hook("sid-A")
            self.assertIsNone(result)
            self.assertIn(
                f"{memlog.LOG_EVENT_TIME_CONTEXT} ok=false reason=no_provider",
                self._log(),
            )
            with store.locked(observer):
                self.assertEqual(
                    store.meta_get(observer, store.META_LAST_INTERACTION_AT), frozen
                )
        finally:
            observer.close()

    def test_session_switch_rekeys(self) -> None:
        pa = ZolaMemoryProvider()
        pa.initialize("sid-A", hermes_home=str(self.home))
        pa.on_session_switch("sid-A2")
        self.assertIsNotNone(self._hook("sid-A2"))
        self.assertIsNone(self._hook("sid-A"))
        self.assertIn(
            f"{memlog.LOG_EVENT_TIME_CONTEXT} ok=false reason=no_provider",
            self._log(),
        )
        pa.shutdown()

    def test_stale_shutdown_does_not_remove_newer(self) -> None:
        stale = ZolaMemoryProvider()
        newer = ZolaMemoryProvider()
        stale.initialize("sid-S", hermes_home=str(self.home))
        newer.initialize("sid-S", hermes_home=str(self._home_b))
        self.assertIs(registry.get("sid-S"), newer)
        stale.shutdown()
        self.assertIs(registry.get("sid-S"), newer)
        seen = []

        def capture(provider, **kwargs):
            seen.append(provider)
            return None

        with mock.patch.object(
            time_context, "handle_pre_llm_call", side_effect=capture
        ):
            self._hook("sid-S")
        self.assertEqual(seen, [newer])
        newer.shutdown()

    def test_unknown_sid_no_provider(self) -> None:
        result = self._hook("sid-unknown")
        self.assertIsNone(result)
        self.assertIn(
            f"{memlog.LOG_EVENT_TIME_CONTEXT} ok=false reason=no_provider",
            self._log(),
        )

    def test_uninitialized_switch_creates_no_ghost_entry(self) -> None:
        owner = ZolaMemoryProvider()
        owner.initialize("sid-owned", hermes_home=str(self.home))
        ghost = ZolaMemoryProvider()
        self.assertIsNone(ghost._session_id)
        self.assertIsNone(ghost._conn)
        ghost.on_session_switch("S-ghost")
        self.assertIsNone(registry.get("S-ghost"))
        # Ghost must not overwrite an initialized provider's sid.
        ghost.on_session_switch("sid-owned")
        self.assertIs(registry.get("sid-owned"), owner)
        self.assertIsNone(registry.get("S-ghost"))
        owner.shutdown()


if __name__ == "__main__":
    unittest.main()
