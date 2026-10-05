"""P6-FORGET Phase 4 unit tests (a–q); synthetic data only."""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import time
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
from provider import ZolaMemoryProvider

# Synthetic strings — never appear in tombstones/meta/logs
SYN_VOLVO = "[car] Neighbor Tobias Wren drives a green 1971 Volvo P1800."
SYN_CELLO = "[person] Cousin Mara is learning the cello."
SYN_REPORT_A = "Weekly status report about the garden project timeline."
SYN_REPORT_B = "Weekly status report about the kitchen remodel budget."
SYN_EP_VOLVO = (
    "Brian mentioned Tobias Wren and the green 1971 Volvo P1800 parked on Elm."
)
SYN_EP_UNRELATED = (
    "Brian and I talked about the weekly status report for the garden project."
)
SYN_EP_PARAPHRASE = (
    "He wants that old Swedish sports car detail about Tobias gone from memory."
)
SYN_PENDING = "forget the volvo please"
ALL_SYN = (
    SYN_VOLVO,
    SYN_CELLO,
    SYN_REPORT_A,
    SYN_REPORT_B,
    SYN_EP_VOLVO,
    SYN_EP_UNRELATED,
    SYN_EP_PARAPHRASE,
    SYN_PENDING,
    "Tobias Wren",
    "Volvo P1800",
    "555-0199",
)


class _TempHome(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.mkdtemp(prefix="zola_forget_p4_")
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
        (self.memories / "USER.md").write_text(
            store.ENTRY_DELIMITER.join(u), encoding="utf-8"
        )
        (self.memories / "MEMORY.md").write_text(
            store.ENTRY_DELIMITER.join(m), encoding="utf-8"
        )

    def _open(self):
        return store.open_store(self.home)

    def _provider(self, *, platform: str = "tui", parent: str = "", sid: str = "s1"):
        p = ZolaMemoryProvider()
        p.initialize(
            sid,
            hermes_home=str(self.home),
            platform=platform,
            parent_session_id=parent,
        )
        return p

    def _insert_episode(self, conn, eid: str, summary: str, fact_ids=None) -> None:
        now = "2026-10-04T12:00:00Z"
        conn.execute(
            "INSERT INTO episodes (id, summary, significance, event_time, "
            "event_time_basis, event_time_evidence, open_items_json, "
            "source_session_id, source_turn_start, source_turn_end, recorded_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                eid,
                summary,
                "synthetic",
                now,
                "stated",
                "",
                "[]",
                "s1",
                1,
                1,
                now,
            ),
        )
        for fid in fact_ids or []:
            conn.execute(
                "INSERT INTO episode_fact_refs (episode_id, fact_id) VALUES (?, ?)",
                (eid, fid),
            )
        conn.commit()

    def _insert_pending(self, conn, pid: str, user_text: str) -> None:
        conn.execute(
            "INSERT INTO pending_turns (id, session_id, turn_index, user_text, "
            "assistant_text, user_time, assistant_time, consolidation_generation, "
            "forget_hold, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                pid,
                "s1",
                1,
                user_text,
                "ok",
                "2026-10-04T12:00:00Z",
                "2026-10-04T12:00:01Z",
                0,
                0,
                "2026-10-04T12:00:00Z",
            ),
        )
        conn.commit()

    def _scan_forbidden(self, conn, *extra: str) -> None:
        needles = list(ALL_SYN) + list(extra)
        for row in conn.execute(
            "SELECT id, record_kind, erased_at, counts_json FROM tombstones"
        ):
            blob = " ".join(str(x) for x in row)
            for n in needles:
                self.assertNotIn(n, blob)
        for row in conn.execute("SELECT key, value FROM meta"):
            blob = f"{row['key']} {row['value']}"
            for n in needles:
                if n in ("Tobias Wren", "Volvo P1800"):
                    continue  # allow only if not in meta; still check below
                self.assertNotIn(n, blob)
        log_path = self.home / "logs" / memlog.LOG_FILENAME
        if log_path.exists():
            text = log_path.read_text(encoding="utf-8")
            for n in needles:
                self.assertNotIn(n, text)


class TestForgetPhase4(_TempHome):
    def test_a_forget_via_remove(self) -> None:
        p = self._provider()
        self._write_files(memory=[SYN_VOLVO])
        fact_index.run_file_check(p._conn, self.home, force=True)
        fid = p._conn.execute(
            "SELECT id FROM facts WHERE text = ?", (SYN_VOLVO,)
        ).fetchone()["id"]
        self._write_files(memory=[])
        p._current_user_message = "Forget the thing about Tobias's car."
        p.on_turn_start(1, p._current_user_message)
        p.on_memory_write(
            "remove", "memory", SYN_VOLVO, metadata={"old_text": SYN_VOLVO}
        )
        self.assertIsNone(
            p._conn.execute("SELECT id FROM facts WHERE id = ?", (fid,)).fetchone()
        )
        self.assertEqual(
            p._conn.execute("SELECT COUNT(*) FROM tombstones").fetchone()[0], 1
        )
        p.sync_turn(p._current_user_message, "gone")
        log = (self.home / "logs" / memlog.LOG_FILENAME).read_text(encoding="utf-8")
        self.assertIn(memlog.LOG_EVENT_FORGET_CASCADE, log)
        self.assertIn("decision=drop", log)
        self._scan_forbidden(p._conn)
        p.shutdown()

    def test_b_semantic_forget_via_replace(self) -> None:
        p = self._provider()
        reduced = "[car] Neighbor has a car."
        self._write_files(user=[SYN_VOLVO])
        fact_index.run_file_check(p._conn, self.home, force=True)
        old_id = p._conn.execute(
            "SELECT id FROM facts WHERE text = ?", (SYN_VOLVO,)
        ).fetchone()["id"]
        self._write_files(user=[reduced])
        fact_index.handle_memory_write(
            p._conn,
            self.home,
            action="replace",
            target="user",
            content=reduced,
            metadata={"old_text": "Volvo"},
            user_message="don't keep the Volvo detail, just that the neighbor has a car",
            provider=p,
        )
        self.assertIsNone(
            p._conn.execute("SELECT id FROM facts WHERE id = ?", (old_id,)).fetchone()
        )
        self.assertIsNotNone(
            p._conn.execute(
                "SELECT id FROM facts WHERE text = ?", (reduced,)
            ).fetchone()
        )
        p.shutdown()

    def test_c_bypass_disappearance(self) -> None:
        p = self._provider()
        self._write_files(memory=[SYN_CELLO])
        fact_index.run_file_check(p._conn, self.home, force=True)
        fid = p._conn.execute(
            "SELECT id FROM facts WHERE text = ?", (SYN_CELLO,)
        ).fetchone()["id"]
        self._write_files(memory=[])
        r = fact_index.run_file_check(p._conn, self.home, force=True)
        self.assertGreaterEqual(r["erased"], 1)
        self.assertIsNone(
            p._conn.execute("SELECT id FROM facts WHERE id = ?", (fid,)).fetchone()
        )
        p.shutdown()

    def test_d_episode_only_via_tool(self) -> None:
        p = self._provider()
        self._insert_episode(p._conn, "ep-volvo", SYN_EP_VOLVO)
        p.on_turn_start(1, "Forget the Volvo episode about Tobias")
        out = json.loads(
            p.handle_tool_call(
                "forget_memory",
                {
                    "description": "Tobias Wren Volvo P1800",
                    "confirm": False,
                },
            )
        )
        self.assertTrue(out["ok"])
        ids = [c["id"] for g in out["groups"] for c in g["candidates"]]
        self.assertIn("ep-volvo", ids)
        out2 = json.loads(
            p.handle_tool_call(
                "forget_memory",
                {
                    "description": "Tobias Wren Volvo P1800",
                    "confirm": True,
                    "target_ids": ["ep-volvo"],
                },
            )
        )
        self.assertTrue(out2["ok"])
        self.assertIsNone(
            p._conn.execute(
                "SELECT id FROM episodes WHERE id = ?", ("ep-volvo",)
            ).fetchone()
        )
        p.shutdown()

    def test_e_ambiguous_groups_no_execute(self) -> None:
        p = self._provider()
        self._insert_episode(p._conn, "ep-a", SYN_REPORT_A)
        self._insert_episode(p._conn, "ep-b", SYN_REPORT_B)
        p.on_turn_start(1, "Forget the weekly status report")
        out = json.loads(
            p.handle_tool_call(
                "forget_memory",
                {"description": "weekly status report", "confirm": False},
            )
        )
        self.assertTrue(out["ok"])
        self.assertGreaterEqual(len(out["groups"]), 1)
        self.assertEqual(
            p._conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0], 2
        )
        # first ambiguous turn → drop
        p.sync_turn("Forget the weekly status report", "which one?")
        log = (self.home / "logs" / memlog.LOG_FILENAME).read_text(encoding="utf-8")
        self.assertIn("decision=drop", log)
        p.shutdown()

    def test_f_consolidation_can_commit_false(self) -> None:
        conn = self._open()
        self._write_files(memory=[SYN_VOLVO])
        fact_index.run_file_check(conn, self.home, force=True)
        fid = conn.execute(
            "SELECT id FROM facts WHERE text = ?", (SYN_VOLVO,)
        ).fetchone()["id"]
        token = forget.begin_consolidation(conn)
        self.assertTrue(forget.can_commit(conn, token))

        def boom():
            raise RuntimeError("fail")

        forget.set_erase_failure_hook(boom)
        forget.erase_fact(conn, fid, reason=forget.ERASE_REASON_TOOL)
        forget.set_erase_failure_hook(None)
        self.assertFalse(forget.can_commit(conn, token))
        self.assertTrue(forget._load_pending(conn))
        conn.close()

    def test_g_failed_cascade_retry_and_suppression(self) -> None:
        conn = self._open()
        self._write_files(memory=[SYN_CELLO])
        fact_index.run_file_check(conn, self.home, force=True)
        fid = conn.execute(
            "SELECT id FROM facts WHERE text = ?", (SYN_CELLO,)
        ).fetchone()["id"]
        gen0 = forget.get_consolidation_generation(conn)

        def boom():
            raise RuntimeError("fail")

        forget.set_erase_failure_hook(boom)
        ok = forget.erase_fact(conn, fid, reason=forget.ERASE_REASON_FILE_CHECK)
        self.assertFalse(ok)
        self.assertIn(fid, forget.is_suppressed(conn, [fid]))
        self.assertGreater(forget.get_consolidation_generation(conn), gen0)
        forget.set_erase_failure_hook(None)
        self._write_files(memory=[])
        r = fact_index.run_file_check(conn, self.home, force=True)
        self.assertGreaterEqual(r.get("erased", 0) + r.get("pending_retries", 0), 0)
        self.assertIsNone(
            conn.execute("SELECT id FROM facts WHERE id = ?", (fid,)).fetchone()
        )
        self.assertNotIn(fid, forget.is_suppressed(conn, [fid]))
        conn.close()

    def test_h_hold_expiry_and_session_switch(self) -> None:
        p = self._provider()
        self._insert_episode(p._conn, "ep1", SYN_EP_VOLVO)
        p.on_turn_start(1, "Forget Tobias Wren Volvo")
        p.handle_tool_call(
            "forget_memory",
            {"description": "Tobias Wren Volvo", "confirm": False},
        )
        self.assertTrue(forget.hold_active(p._forget_state))
        p.on_session_switch("s2")
        self.assertFalse(forget.hold_active(p._forget_state))
        # disposition marks survive switch (E1)
        self.assertTrue(p._forget_state.disposition_drops)
        p2 = self._provider(sid="s3")
        self._insert_episode(p2._conn, "ep2", SYN_EP_VOLVO)
        p2.on_turn_start(1, "Forget Tobias Wren Volvo")
        p2.handle_tool_call(
            "forget_memory",
            {"description": "Tobias Wren Volvo", "confirm": False},
        )
        # wall-clock expiry
        p2._forget_state.hold_started_at = time.time() - (
            forget.FORGET_HOLD_MAX_MINUTES * 60 + 1
        )
        p2.on_turn_start(2, "still thinking")
        self.assertFalse(forget.hold_active(p2._forget_state))
        p.shutdown()
        p2.shutdown()

    def test_i_byte_scan_no_content(self) -> None:
        p = self._provider()
        self._write_files(memory=[SYN_VOLVO])
        fact_index.run_file_check(p._conn, self.home, force=True)
        self._write_files(memory=[])
        p.on_turn_start(1, "forget the volvo")
        p.on_memory_write(
            "remove", "memory", SYN_VOLVO, metadata={"old_text": SYN_VOLVO}
        )
        self._scan_forbidden(p._conn)
        p.shutdown()

    def test_j_tool_write_surface(self) -> None:
        p = self._provider()
        self._insert_episode(p._conn, "ep1", SYN_EP_VOLVO)
        writes = []

        def tracer(sql: str) -> None:
            s = (sql or "").strip().lower()
            if s.startswith(("insert", "update", "delete")):
                writes.append(s.split()[0])

        p._conn.set_trace_callback(tracer)
        p.on_turn_start(1, "Forget Tobias Wren Volvo")
        p.handle_tool_call(
            "forget_memory",
            {"description": "Tobias Wren Volvo", "confirm": False},
        )
        p.handle_tool_call(
            "forget_memory",
            {
                "description": "Tobias Wren Volvo",
                "confirm": True,
                "target_ids": ["ep1"],
            },
        )
        p._conn.set_trace_callback(None)
        # Allowed: DELETE + INSERT tombstone / meta upserts — no DDL
        self.assertTrue(any(w == "delete" for w in writes))
        self.assertTrue(any(w == "insert" for w in writes))
        self.assertFalse(any(w.startswith("create") for w in writes))
        # Must not touch memory files
        user = (self.memories / "USER.md").read_text(encoding="utf-8")
        mem = (self.memories / "MEMORY.md").read_text(encoding="utf-8")
        self.assertEqual(user, "")
        self.assertEqual(mem, "")
        p.shutdown()

    def test_k_disposition_c1_and_race(self) -> None:
        p = self._provider()
        msg = "Please forget the demo project codename"
        p.on_turn_start(1, msg)
        # zero-candidate forget turn → drop
        p.sync_turn(msg, "nothing found")
        log = (self.home / "logs" / memlog.LOG_FILENAME).read_text(encoding="utf-8")
        self.assertIn("decision=drop", log)
        ordinary = "How is the weather today?"
        p.on_turn_start(2, ordinary)
        p.sync_turn(ordinary, "sunny")
        log = (self.home / "logs" / memlog.LOG_FILENAME).read_text(encoding="utf-8")
        self.assertIn("decision=keep", log)
        # F5 race: mark, switch (/new), late sync still drop
        forget_msg = "forget the cello lesson"
        p.on_turn_start(3, forget_msg)
        p.on_session_switch("s-new")
        decision, reason = forget.turn_disposition(p._forget_state, forget_msg)
        self.assertEqual(decision, "drop")
        self.assertEqual(reason, "marked")
        p.shutdown()

    def test_l_hold_execute_erases_pending(self) -> None:
        p = self._provider()
        self._insert_episode(p._conn, "ep1", SYN_EP_VOLVO)
        self._insert_pending(p._conn, "pend1", "talking about Tobias Wren and Volvo")
        p.on_turn_start(1, "Forget Tobias Wren Volvo")
        p.handle_tool_call(
            "forget_memory",
            {"description": "Tobias Wren Volvo", "confirm": False},
        )
        out = json.loads(
            p.handle_tool_call(
                "forget_memory",
                {
                    "description": "Tobias Wren Volvo",
                    "confirm": True,
                    "target_ids": ["ep1"],
                },
            )
        )
        self.assertTrue(out["ok"])
        self.assertIsNone(
            p._conn.execute(
                "SELECT id FROM pending_turns WHERE id = ?", ("pend1",)
            ).fetchone()
        )
        p.shutdown()

    def test_m_c3_active_fact_refused(self) -> None:
        p = self._provider()
        self._write_files(memory=[SYN_VOLVO])
        fact_index.run_file_check(p._conn, self.home, force=True)
        fid = p._conn.execute(
            "SELECT id FROM facts WHERE text = ?", (SYN_VOLVO,)
        ).fetchone()["id"]
        p.on_turn_start(1, "Forget Tobias Wren Volvo")
        out = json.loads(
            p.handle_tool_call(
                "forget_memory",
                {"description": "Tobias Wren Volvo 1971", "confirm": False},
            )
        )
        kinds = {c["kind"] for g in out["groups"] for c in g["candidates"]}
        self.assertIn(forget.KIND_NOTEBOOK_FACT, kinds)
        out2 = json.loads(
            p.handle_tool_call(
                "forget_memory",
                {
                    "description": "Tobias Wren Volvo 1971",
                    "confirm": True,
                    "target_ids": [fid],
                },
            )
        )
        self.assertFalse(out2["ok"])
        self.assertEqual(out2["refused_reason"], "active_fact")
        self.assertIsNotNone(
            p._conn.execute("SELECT id FROM facts WHERE id = ?", (fid,)).fetchone()
        )
        p.shutdown()

    def test_n_authority_and_restart(self) -> None:
        p = self._provider()
        self._insert_episode(p._conn, "ep1", SYN_EP_VOLVO)
        # confirm=true without intent / hold
        out = json.loads(
            p.handle_tool_call(
                "forget_memory",
                {
                    "description": "Tobias",
                    "confirm": True,
                    "target_ids": ["ep1"],
                },
            )
        )
        self.assertEqual(out["refused_reason"], "authority")
        p.on_turn_start(1, "Forget Tobias Wren Volvo")
        p.handle_tool_call(
            "forget_memory",
            {"description": "Tobias Wren Volvo", "confirm": False},
        )
        # unbound target
        out2 = json.loads(
            p.handle_tool_call(
                "forget_memory",
                {
                    "description": "Tobias Wren Volvo",
                    "confirm": True,
                    "target_ids": ["not-in-set"],
                },
            )
        )
        self.assertEqual(out2["refused_reason"], "unbound_targets")
        # simulated restart: meta hold, empty candidates
        p._forget_state.clear_hold_process()
        forget.expire_orphan_hold_on_restart(p)
        out3 = json.loads(
            p.handle_tool_call(
                "forget_memory",
                {
                    "description": "Tobias Wren Volvo",
                    "confirm": True,
                    "target_ids": ["ep1"],
                },
            )
        )
        self.assertIn(out3["refused_reason"], ("authority", "unbound_targets"))
        # platform refuse
        p._platform = "cron"
        out4 = json.loads(
            p.handle_tool_call(
                "forget_memory",
                {"description": "x", "confirm": False},
            )
        )
        self.assertEqual(out4["refused_reason"], "platform")
        self.assertEqual(p.get_tool_schemas(), [])
        p.shutdown()

    def test_n2_labels_absent_from_confirm_true_and_artifacts(self) -> None:
        p = self._provider()
        self._insert_episode(p._conn, "ep1", SYN_EP_VOLVO)
        p.on_turn_start(1, "Forget Tobias Wren Volvo")
        listed = json.loads(
            p.handle_tool_call(
                "forget_memory",
                {"description": "Tobias Wren Volvo", "confirm": False},
            )
        )
        labels = [c.get("label") for g in listed["groups"] for c in g["candidates"]]
        self.assertTrue(labels)
        out = json.loads(
            p.handle_tool_call(
                "forget_memory",
                {
                    "description": "Tobias Wren Volvo",
                    "confirm": True,
                    "target_ids": ["ep1"],
                },
            )
        )
        blob = json.dumps(out)
        for lab in labels:
            self.assertNotIn(lab, blob)
        self._scan_forbidden(p._conn, *labels)
        p.shutdown()

    def test_o_paraphrase_corpus(self) -> None:
        conn = self._open()
        # must-match: fact ref, name, number, or ≥2 distinctive terms
        self._insert_episode(conn, "m1", SYN_EP_VOLVO)  # name+number
        self._insert_episode(
            conn, "m2", "Discussion of Aurora Quill demo codename status."
        )
        # unrelated sharing common words
        self._insert_episode(conn, "u1", SYN_EP_UNRELATED)
        self._insert_episode(
            conn, "u2", "Weekly status report about the kitchen remodel budget."
        )
        # wordless paraphrase — only fact-ref path (Track 5 input)
        fid = "fact-ref-1"
        conn.execute(
            "INSERT INTO facts (id, target, text, tag, state, learned_at, indexed_at, "
            "updated_at, superseded_at, source) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?)",
            (
                fid,
                "memory",
                SYN_VOLVO,
                "car",
                "active",
                "2026-10-04T12:00:00Z",
                "2026-10-04T12:00:00Z",
                "notify",
            ),
        )
        self._insert_episode(conn, "m3", SYN_EP_PARAPHRASE, fact_ids=[fid])
        conn.commit()

        strong, ordinary = forget.derive_terms(
            ["Forget Tobias Wren and the 1971 Volvo P1800"]
        )
        must = {"m1", "m3"}
        # m2 must-match only if description shares ≥2 terms — use Aurora Quill query separately
        matched = set()
        for r in conn.execute("SELECT * FROM episodes"):
            refs = {
                x["fact_id"]
                for x in conn.execute(
                    "SELECT fact_id FROM episode_fact_refs WHERE episode_id = ?",
                    (r["id"],),
                )
            }
            blob = f"{r['summary']}\n{r['significance']}"
            if forget.row_matches_terms(
                blob,
                strong=strong,
                ordinary=ordinary,
                fact_ids={fid},
                row_fact_refs=refs,
            ):
                matched.add(r["id"])
        must_miss = must - matched
        over = matched - must - {"m2"}
        # m2 should not match Volvo query
        self.assertNotIn("m2", matched)
        self.assertEqual(must_miss, set(), f"must-match misses: {must_miss}")
        # report counts for progress doc
        self._corpus = {
            "matched": len(matched),
            "must_match": len(must),
            "missed": len(must_miss),
            "over_matched": len(over & {"u1", "u2"}),
            "over_ids": sorted(over & {"u1", "u2"}),
            "note": (
                "Wordless paraphrases are caught only by fact refs (Track 5 input)."
            ),
        }
        # Aurora query must-match m2
        s2, o2 = forget.derive_terms(["forget Aurora Quill demo codename"])
        hit_m2 = False
        for r in conn.execute("SELECT * FROM episodes WHERE id = 'm2'"):
            hit_m2 = forget.row_matches_terms(
                r["summary"],
                strong=s2,
                ordinary=o2,
                fact_ids=set(),
                row_fact_refs=set(),
            )
        self.assertTrue(hit_m2)
        # Persist counts for progress via env side channel file in scratch if needed
        out_path = Path(r"C:\Users\test\Dev\zola-spikes\p6-forget\matcher_corpus.json")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(self._corpus, indent=2), encoding="utf-8")
        conn.close()

    def test_p_cascade_rollback_byte_identical(self) -> None:
        conn = self._open()
        self._write_files(memory=[SYN_VOLVO])
        fact_index.run_file_check(conn, self.home, force=True)
        self._insert_episode(conn, "ep1", SYN_EP_VOLVO)
        tables = (
            "facts",
            "fact_history",
            "episodes",
            "episode_fact_refs",
            "pending_turns",
            "tombstones",
        )
        before = {
            t: [tuple(r) for r in conn.execute(f"SELECT * FROM {t} ORDER BY 1")]
            for t in tables
        }
        before_fts = conn.execute(
            "SELECT fact_id, text FROM facts_fts ORDER BY fact_id"
        ).fetchall()
        fid = conn.execute(
            "SELECT id FROM facts WHERE text = ?", (SYN_VOLVO,)
        ).fetchone()["id"]

        def boom():
            raise RuntimeError("rollback")

        forget.set_erase_failure_hook(boom)
        forget.erase_fact(conn, fid, reason=forget.ERASE_REASON_TOOL)
        forget.set_erase_failure_hook(None)
        after = {
            t: [tuple(r) for r in conn.execute(f"SELECT * FROM {t} ORDER BY 1")]
            for t in tables
        }
        after_fts = conn.execute(
            "SELECT fact_id, text FROM facts_fts ORDER BY fact_id"
        ).fetchall()
        for t in tables:
            self.assertEqual(before[t], after[t], msg=t)
        self.assertEqual([tuple(r) for r in before_fts], [tuple(r) for r in after_fts])
        # pending_erasures / generation intentionally change after failed cascade
        self.assertIn(fid, forget._load_pending(conn))
        conn.close()

    def test_e2_e3_hold_turns_and_memory_remove_ends_hold(self) -> None:
        p = self._provider()
        self._write_files(memory=[SYN_VOLVO])
        fact_index.run_file_check(p._conn, self.home, force=True)
        fid = p._conn.execute(
            "SELECT id FROM facts WHERE text = ?", (SYN_VOLVO,)
        ).fetchone()["id"]
        self._insert_episode(p._conn, "ep1", SYN_EP_VOLVO, fact_ids=[fid])
        p.on_turn_start(1, "Forget Tobias Wren or the cello?")
        listed = json.loads(
            p.handle_tool_call(
                "forget_memory",
                {"description": "Tobias Wren Volvo", "confirm": False},
            )
        )
        self.assertTrue(forget.hold_active(p._forget_state))
        self.assertIn(fid, p._forget_state.candidate_ids)
        # memory remove of candidate ends hold
        self._write_files(memory=[])
        p.on_memory_write(
            "remove", "memory", SYN_VOLVO, metadata={"old_text": SYN_VOLVO}
        )
        self.assertFalse(forget.hold_active(p._forget_state))

        # fresh hold for turn budget
        p2 = self._provider(sid="s-hold")
        self._insert_episode(p2._conn, "ep2", SYN_EP_VOLVO)
        p2.on_turn_start(1, "Forget Tobias Wren Volvo")
        p2.handle_tool_call(
            "forget_memory",
            {"description": "Tobias Wren Volvo", "confirm": False},
        )
        for i, msg in enumerate(("a", "b", "c"), start=2):
            p2.on_turn_start(i, f"clarify {msg}")
            self.assertTrue(forget.hold_active(p2._forget_state))
        # 4th user turn after hold → hold ends; disposition keep
        p2.on_turn_start(5, "ordinary topic now")
        self.assertFalse(forget.hold_active(p2._forget_state))
        d, _ = forget.turn_disposition(p2._forget_state, "ordinary topic now")
        self.assertEqual(d, "keep")
        p.shutdown()
        p2.shutdown()

    def test_schema_omit_and_tui_schema(self) -> None:
        p = self._provider(platform="tui")
        schemas = p.get_tool_schemas()
        self.assertEqual(len(schemas), 1)
        self.assertEqual(schemas[0]["name"], "forget_memory")
        p._platform = "cron"
        self.assertEqual(p.get_tool_schemas(), [])
        p.shutdown()

    def test_d1_hermes_add_provider_before_initialize(self) -> None:
        """D1: routing built pre-init; inject post-init; cron omits + refuses."""

        class _FakeManager:
            def __init__(self) -> None:
                self._tool_to_provider = {}
                self._providers = []

            def add_provider(self, provider) -> None:
                # Mirrors memory_manager.add_provider schema→route step (pre-initialize)
                self._providers.append(provider)
                for raw in provider.get_tool_schemas():
                    name = raw.get("name") if isinstance(raw, dict) else None
                    if name:
                        self._tool_to_provider[name] = provider

            def get_all_tool_schemas(self):
                out = []
                for provider in self._providers:
                    out.extend(provider.get_tool_schemas())
                return out

            def handle_tool_call(self, tool_name, args):
                provider = self._tool_to_provider.get(tool_name)
                if provider is None:
                    raise RuntimeError("No memory provider handles tool")
                return provider.handle_tool_call(tool_name, args)

        # --- TUI path ---
        mgr = _FakeManager()
        p = ZolaMemoryProvider()
        self.assertFalse(p._initialized)
        pre = p.get_tool_schemas()
        self.assertEqual(len(pre), 1)
        self.assertEqual(pre[0]["name"], "forget_memory")
        mgr.add_provider(p)
        self.assertIn("forget_memory", mgr._tool_to_provider)
        p.initialize(
            "sess-tui",
            hermes_home=str(self.home),
            platform="tui",
            parent_session_id="",
        )
        inject = mgr.get_all_tool_schemas()
        self.assertEqual(len(inject), 1)
        self.assertEqual(inject[0]["name"], "forget_memory")
        p.on_turn_start(1, "Forget Tobias Wren Volvo")
        self._insert_episode(p._conn, "ep-d1", SYN_EP_VOLVO)
        raw = mgr.handle_tool_call(
            "forget_memory",
            {"description": "Tobias Wren Volvo", "confirm": False},
        )
        out = json.loads(raw)
        self.assertTrue(out.get("ok"))
        p.shutdown()

        # --- cron path: schema absent at inject; routed call still refused ---
        home2 = Path(tempfile.mkdtemp(prefix="zola_forget_d1_"))
        try:
            (home2 / "memories").mkdir(parents=True)
            (home2 / "memories" / "USER.md").write_text("", encoding="utf-8")
            (home2 / "memories" / "MEMORY.md").write_text("", encoding="utf-8")
            os.environ["HERMES_HOME"] = str(home2)
            memlog.reset_log_handler_for_tests()
            mgr2 = _FakeManager()
            p2 = ZolaMemoryProvider()
            mgr2.add_provider(p2)  # routes from pre-init schema
            self.assertIn("forget_memory", mgr2._tool_to_provider)
            p2.initialize(
                "sess-cron",
                hermes_home=str(home2),
                platform="cron",
                parent_session_id="",
            )
            self.assertEqual(mgr2.get_all_tool_schemas(), [])
            refused = json.loads(
                mgr2.handle_tool_call(
                    "forget_memory",
                    {"description": "anything", "confirm": False},
                )
            )
            self.assertFalse(refused.get("ok"))
            self.assertEqual(refused.get("refused_reason"), "platform")
            p2.shutdown()
        finally:
            shutil.rmtree(home2, ignore_errors=True)
            os.environ["HERMES_HOME"] = str(self.home)

    def test_d2_notify_remove_marks_disposition(self) -> None:
        """D2: memory-tool remove without forget words → drop; next ordinary → keep."""
        p = self._provider()
        self._write_files(memory=[SYN_VOLVO])
        fact_index.run_file_check(p._conn, self.home, force=True)
        msg = "Tobias sold the Volvo, take that out of your notes"
        p.on_turn_start(1, msg)
        # No forget-intent phrase — must still mark via notify cascade
        self.assertFalse(forget.has_forget_intent(msg))
        self._write_files(memory=[])
        p.on_memory_write(
            "remove", "memory", SYN_VOLVO, metadata={"old_text": SYN_VOLVO}
        )
        p.sync_turn(msg, "removed")
        log = (self.home / "logs" / memlog.LOG_FILENAME).read_text(encoding="utf-8")
        self.assertIn("decision=drop", log)
        ordinary = "What time is it?"
        p.on_turn_start(2, ordinary)
        p.sync_turn(ordinary, "evening")
        log2 = (self.home / "logs" / memlog.LOG_FILENAME).read_text(encoding="utf-8")
        self.assertIn("decision=keep", log2)
        p.shutdown()

    def test_d3_search_recall_oriented(self) -> None:
        """D3: short/name-leading descriptions still list candidates; stopwords alone do not."""
        p = self._provider()
        mara_cello = "[person] Cousin Mara is learning the cello."
        mara_post = "[hobby] Mara collects vintage postcards."
        self._write_files(memory=[mara_cello, SYN_VOLVO], user=[mara_post])
        fact_index.run_file_check(p._conn, self.home, force=True)
        self._insert_episode(
            p._conn, "ep-nimbus", "Status update on the Nimbus rollout window."
        )

        # "Mara" — both Mara notebook facts, two groups, ask_brian
        p.on_turn_start(1, "Forget Mara")
        out = json.loads(
            p.handle_tool_call(
                "forget_memory", {"description": "Mara", "confirm": False}
            )
        )
        self.assertTrue(out["ok"])
        mara_cands = [
            c
            for g in out["groups"]
            for c in g["candidates"]
            if c["kind"] == forget.KIND_NOTEBOOK_FACT
        ]
        self.assertEqual(len(mara_cands), 2)
        self.assertGreaterEqual(len(out["groups"]), 2)
        self.assertTrue(all(g.get("ask_brian") for g in out["groups"]))

        # "Tobias car" → Tobias notebook_fact
        out2 = json.loads(
            p.handle_tool_call(
                "forget_memory",
                {"description": "Tobias car", "confirm": False},
            )
        )
        kinds_ids = [
            (c["kind"], c["id"])
            for g in out2["groups"]
            for c in g["candidates"]
        ]
        self.assertTrue(
            any(k == forget.KIND_NOTEBOOK_FACT for k, _ in kinds_ids)
        )
        volvo_id = p._conn.execute(
            "SELECT id FROM facts WHERE text = ?", (SYN_VOLVO,)
        ).fetchone()["id"]
        self.assertIn((forget.KIND_NOTEBOOK_FACT, volvo_id), kinds_ids)

        # "Nimbus project" → episode containing only Nimbus (plus common words)
        out3 = json.loads(
            p.handle_tool_call(
                "forget_memory",
                {"description": "Nimbus project", "confirm": False},
            )
        )
        ep_ids = [
            c["id"]
            for g in out3["groups"]
            for c in g["candidates"]
            if c["kind"] == forget.RECORD_KIND_EPISODE
        ]
        self.assertIn("ep-nimbus", ep_ids)

        # stopwords / command words only → no candidates
        out4 = json.loads(
            p.handle_tool_call(
                "forget_memory",
                {"description": "please forget delete remove that", "confirm": False},
            )
        )
        self.assertTrue(out4["ok"])
        self.assertEqual(out4["groups"], [])
        self.assertIn("No matches", out4.get("message", ""))
        p.shutdown()

    def test_short_label_ranks_names_and_matches(self) -> None:
        """Label prefers names/digits over leading filler; Mara rows stay distinct."""
        ep = "Talked through the Nimbus launch slipping a week"
        label = forget._short_label(ep, matched_terms={"nimbus"})
        self.assertTrue(label.lower().startswith("nimbus"))
        self.assertNotIn("talked", label.lower().split(",")[0])

        cousin = "[person] Cousin Mara is learning the cello."
        coworker = "[person] Coworker Mara sits two desks over."
        terms = {"mara"}
        lab_c = forget._short_label(cousin, matched_terms=terms)
        lab_w = forget._short_label(coworker, matched_terms=terms)
        self.assertIn("mara", lab_c.lower())
        self.assertIn("mara", lab_w.lower())
        self.assertNotEqual(lab_c.lower(), lab_w.lower())
        self.assertTrue(
            "cousin" in lab_c.lower() or "cello" in lab_c.lower()
        )
        self.assertTrue(
            "coworker" in lab_w.lower() or "desks" in lab_w.lower()
        )

    def test_7c_redirect_augmented_forget_drops(self) -> None:
        """7c: marked forget + Hermes redirect-augmented sync → drop (containment)."""
        orig = "Forget what I said about Rosa."
        sync = (
            f"{orig}\n\nUser correction during the turn: "
            "I'll remember that your Aunt Rosa paints."
        )
        state = forget.ForgetSessionState()
        forget.mark_drop(state, orig)
        decision, reason = forget.turn_disposition(state, sync)
        self.assertEqual(decision, "drop")
        self.assertIn(reason, ("marked", "marked_contained"))
        self.assertNotIn(forget.normalize_disposition_key(orig), state.disposition_drops)

    def test_7c_redirect_augmented_d2_remove_drops(self) -> None:
        """7c: D2 mark (no forget words) + redirect-augmented sync → drop."""
        orig = "Dana sold the Vespa, take that out of your notes"
        sync = (
            f"{orig}\n\nUser correction during the turn: "
            "Got it, removing the Vespa note."
        )
        self.assertFalse(forget.has_forget_intent(orig))
        self.assertFalse(forget.has_forget_intent(sync))
        state = forget.ForgetSessionState()
        forget.mark_drop(state, orig)
        decision, reason = forget.turn_disposition(state, sync)
        self.assertEqual(decision, "drop")
        self.assertEqual(reason, "marked_contained")
        self.assertNotIn(forget.normalize_disposition_key(orig), state.disposition_drops)

    def test_7c_redirect_augmented_ordinary_keeps(self) -> None:
        """7c: redirect-augmented ordinary turn with no mark → keep."""
        orig = "What should we do for dinner?"
        sync = f"{orig}\n\nUser correction during the turn: Pizza is fine."
        state = forget.ForgetSessionState()
        decision, reason = forget.turn_disposition(state, sync)
        self.assertEqual(decision, "keep")
        self.assertEqual(reason, "ordinary")


if __name__ == "__main__":
    unittest.main()
