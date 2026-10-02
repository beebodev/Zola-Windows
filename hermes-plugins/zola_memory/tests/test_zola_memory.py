"""Unit tests for zola_memory (synthetic data only; P6-D01/D03/D06)."""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

_HERMES_ROOT = Path(r"C:\Users\test\Dev\hermes-agent")
if str(_HERMES_ROOT) not in sys.path:
    sys.path.insert(0, str(_HERMES_ROOT))

import fact_index
import forget
import log as memlog
import store
from forget import has_forget_intent
from provider import ZolaMemoryProvider

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

    def tearDown(self) -> None:
        forget.set_erase_failure_hook(None)
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


if __name__ == "__main__":
    unittest.main()
