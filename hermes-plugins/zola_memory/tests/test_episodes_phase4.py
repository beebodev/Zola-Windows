"""P6-EPISODES Phase 4 unit tests; synthetic data only."""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import sys
import tempfile
import threading
import time
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest import mock

_HERMES_ROOT = Path(r"C:\Users\test\Dev\hermes-agent")
if str(_HERMES_ROOT) not in sys.path:
    sys.path.insert(0, str(_HERMES_ROOT))

_VENV_SITE = _HERMES_ROOT / ".venv" / "Lib" / "site-packages"
if _VENV_SITE.is_dir() and str(_VENV_SITE) not in sys.path:
    try:
        from zoneinfo import ZoneInfo as _ZI

        _ZI("America/Los_Angeles")
    except Exception:
        sys.path.insert(0, str(_VENV_SITE))

from zoneinfo import ZoneInfo

import consolidate
import forget
import log as memlog
import pending
import retrieve
import store
import time_context
from provider import ZolaMemoryProvider

_LA = ZoneInfo("America/Los_Angeles")
_PDT = timezone(timedelta(hours=-7), name="PDT")

SYN_EP_SUMMARY = "Brian chose Alpine Quill for the Cedar demo project."
SYN_ENTITY = "Alpine Quill"
SYN_FACT = "[project] Demo codename is Alpine Quill."
SYN_PENDING_USER = "Let's go with Alpine Quill for the Cedar demo."
SYN_PENDING_ASST = "Got it — Alpine Quill it is."
SYN_UNRELATED = "What's a good movie for tonight?"
ALL_SYN = (
    SYN_EP_SUMMARY,
    SYN_ENTITY,
    SYN_FACT,
    SYN_PENDING_USER,
    SYN_PENDING_ASST,
    "Cedar",
    "Quill",
)


class _StubResult:
    def __init__(self, parsed: Any) -> None:
        self.parsed = parsed


class _StubLLM:
    def __init__(self, parsed: Any = None, *, boom: bool = False) -> None:
        self.parsed = parsed if parsed is not None else {"episodes": []}
        self.boom = boom
        self.calls = 0
        self.last_instructions = ""
        self._queue: List[Any] = []

    def queue(self, parsed: Any) -> None:
        self._queue.append(parsed)

    def complete_structured(self, **kwargs: Any) -> _StubResult:
        self.calls += 1
        self.last_instructions = kwargs.get("instructions") or ""
        if self.boom:
            raise RuntimeError("stub llm failure")
        if self._queue:
            return _StubResult(self._queue.pop(0))
        return _StubResult(self.parsed)


class _TempHome(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.mkdtemp(prefix="zola_episodes_p4_")
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
        time_context.set_clock_for_tests(None, timezone=_LA)
        forget.set_client_origin_override_for_tests(True)

    def tearDown(self) -> None:
        forget.set_client_origin_override_for_tests(None)
        forget.set_erase_failure_hook(None)
        consolidate.reset_for_tests()
        time_context.set_clock_for_tests(None)
        memlog.reset_log_handler_for_tests()
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def _provider(self, sid: str = "sess-ep", platform: str = "tui") -> ZolaMemoryProvider:
        p = ZolaMemoryProvider()
        p.initialize(sid, hermes_home=str(self.home), platform=platform, parent_session_id="")
        return p

    def _messages(self, user: str, asst: str, user_ts: Optional[str]) -> List[Dict[str, Any]]:
        msgs: List[Dict[str, Any]] = []
        if user_ts is not None:
            msgs.append({"role": "user", "content": user, "timestamp": user_ts})
        else:
            msgs.append({"role": "user", "content": user})
        msgs.append(
            {
                "role": "assistant",
                "content": asst,
                "timestamp": user_ts or time_context.marker_iso(time_context.capture_now()),
            }
        )
        return msgs

    def _episode_payload(
        self,
        *,
        pending_ids: List[str],
        summary: str = SYN_EP_SUMMARY,
        entities: Optional[List[Dict[str, Any]]] = None,
        fact_refs: Optional[List[str]] = None,
        evidence: Optional[str] = None,
        basis: str = "unknown",
        open_items: Optional[List[str]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        ep: Dict[str, Any] = {
            "summary": summary,
            "significance": "decision",
            "entities": entities
            if entities is not None
            else [{"name": "Alpine Quill", "kind": "project", "id": None, "alias": None}],
            "fact_refs": fact_refs or [],
            "source_turn_range": {
                "start_pending_id": pending_ids[0],
                "end_pending_id": pending_ids[-1],
            },
            "event_time": None,
            "event_time_basis": basis,
            "event_time_evidence": evidence,
            "open_items": open_items or [],
        }
        if extra:
            ep.update(extra)
        return {"episodes": [ep]}


class TestSchemaV2(_TempHome):
    def test_schema_version_2_and_dedupe_index(self) -> None:
        conn = store.open_store(self.home)
        self.assertEqual(store.meta_get(conn, store.META_SCHEMA_VERSION), "2")
        idx = "\n".join(
            (r[0] or "")
            for r in conn.execute(
                "SELECT sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL"
            )
        )
        self.assertIn("idx_pending_dedupe", idx)
        row = conn.execute("PRAGMA secure_delete").fetchone()
        self.assertEqual(int(row[0]), 1)
        conn.close()


class TestPendingWriter(_TempHome):
    def test_keep_writes_drop_skips_and_disposition_once(self) -> None:
        p = self._provider()
        ts = "2026-10-03T15:00:00-07:00"
        with mock.patch.object(
            forget, "turn_disposition", wraps=forget.turn_disposition
        ) as wrapped:
            p.sync_turn(
                SYN_PENDING_USER,
                SYN_PENDING_ASST,
                session_id="sess-ep",
                messages=self._messages(SYN_PENDING_USER, SYN_PENDING_ASST, ts),
            )
            self.assertEqual(wrapped.call_count, 1)
        n = p._conn.execute("SELECT COUNT(*) FROM pending_turns").fetchone()[0]
        self.assertEqual(n, 1)
        # forget-intent → drop → no second pending
        p.sync_turn(
            "Please forget Alpine Quill",
            "which one?",
            session_id="sess-ep",
            messages=self._messages("Please forget Alpine Quill", "which one?", ts),
        )
        n2 = p._conn.execute("SELECT COUNT(*) FROM pending_turns").fetchone()[0]
        self.assertEqual(n2, 1)

    def test_dedupe_same_turn_and_relaunch_still_queues(self) -> None:
        p = self._provider()
        ts = "2026-10-03T15:00:00-07:00"
        msgs = self._messages(SYN_PENDING_USER, SYN_PENDING_ASST, ts)
        p.sync_turn(SYN_PENDING_USER, SYN_PENDING_ASST, session_id="sess-ep", messages=msgs)
        p.sync_turn(SYN_PENDING_USER, SYN_PENDING_ASST, session_id="sess-ep", messages=msgs)
        n = p._conn.execute("SELECT COUNT(*) FROM pending_turns").fetchone()[0]
        self.assertEqual(n, 1)
        # Simulate relaunch: new provider, same session id, surviving pending
        p.shutdown()
        p2 = self._provider("sess-ep")
        n_before = p2._conn.execute("SELECT COUNT(*) FROM pending_turns").fetchone()[0]
        self.assertEqual(n_before, 1)
        new_user = "Also pick Cedar Blue for the trim."
        new_asst = "Cedar Blue noted."
        p2.sync_turn(
            new_user,
            new_asst,
            session_id="sess-ep",
            messages=self._messages(new_user, new_asst, "2026-10-03T15:05:00-07:00"),
        )
        n_after = p2._conn.execute("SELECT COUNT(*) FROM pending_turns").fetchone()[0]
        self.assertEqual(n_after, 2)

    def test_missing_user_time_still_writes(self) -> None:
        p = self._provider()
        p.sync_turn(
            SYN_PENDING_USER,
            SYN_PENDING_ASST,
            session_id="sess-ep",
            messages=[{"role": "user", "content": SYN_PENDING_USER}, {"role": "assistant", "content": SYN_PENDING_ASST}],
        )
        row = p._conn.execute("SELECT user_time FROM pending_turns").fetchone()
        self.assertIsNone(row["user_time"])

    def test_user_time_matches_turn_content_not_latest(self) -> None:
        """R3: last user row may belong to the next turn (live messages list)."""
        p = self._provider()
        turn_ts = "2026-10-03T15:00:00-07:00"
        next_ts = "2026-10-03T15:05:00-07:00"
        messages = [
            {"role": "user", "content": SYN_PENDING_USER, "timestamp": turn_ts},
            {"role": "assistant", "content": SYN_PENDING_ASST, "timestamp": turn_ts},
            # Already appended next-turn user message on the live list
            {"role": "user", "content": "What about dinner?", "timestamp": next_ts},
        ]
        p.sync_turn(
            SYN_PENDING_USER,
            SYN_PENDING_ASST,
            session_id="sess-ep",
            messages=messages,
        )
        row = p._conn.execute(
            "SELECT user_time, user_text FROM pending_turns"
        ).fetchone()
        self.assertEqual(row["user_time"], turn_ts)
        # Redirect-augmented sync still finds the original message timestamp
        orig = "Let's go with Alpine Quill."
        redirect = (
            f"{orig}\n\nUser correction during the turn: Actually make it Cedar."
        )
        messages2 = [
            {"role": "user", "content": orig, "timestamp": turn_ts},
            {"role": "assistant", "content": "ok", "timestamp": turn_ts},
            {"role": "user", "content": "next turn already here", "timestamp": next_ts},
        ]
        got = pending.resolve_user_time(messages2, redirect)
        self.assertEqual(got, turn_ts)

    def test_cron_writes_no_pending(self) -> None:
        p = self._provider(platform="cron")
        p._platform = "cron"
        p.sync_turn(
            SYN_PENDING_USER,
            SYN_PENDING_ASST,
            session_id="cron-1",
            messages=self._messages(SYN_PENDING_USER, SYN_PENDING_ASST, "2026-10-03T15:00:00-07:00"),
        )
        n = p._conn.execute("SELECT COUNT(*) FROM pending_turns").fetchone()[0]
        self.assertEqual(n, 0)

    def test_hermes_unix_float_timestamp_normalizes(self) -> None:
        """F1: live Hermes message shape — timestamp is unix float (state.db typeof=real)."""
        # Fixture from live S1 turn 6 (20261005_073256_a2d789): messages.timestamp
        hermes_unix = 1791211837.5515141
        user = "Oh, and I took the Alpine Quill crate to the shop yesterday."
        asst = "I'll remember the Alpine Quill crate."
        # Real Hermes shape: role / content / timestamp as float (not ISO string)
        messages = [
            {"role": "user", "content": user, "timestamp": hermes_unix},
            {"role": "assistant", "content": asst, "timestamp": hermes_unix},
        ]
        expected = pending.normalize_message_timestamp(hermes_unix)
        self.assertEqual(expected, "2026-10-05T07:50:37-07:00")
        self.assertEqual(
            consolidate.resolve_stated_time("yesterday", expected), "2026-10-04"
        )
        p = self._provider()
        p.sync_turn(user, asst, session_id="sess-ep", messages=messages)
        row = p._conn.execute(
            "SELECT user_time, assistant_time FROM pending_turns"
        ).fetchone()
        self.assertEqual(row["user_time"], expected)
        self.assertEqual(row["assistant_time"], expected)
        # Unparseable → NULL (X4)
        self.assertIsNone(pending.normalize_message_timestamp("not-a-time"))
        self.assertIsNone(pending.normalize_message_timestamp(True))


class TestConsolidateCore(_TempHome):
    def test_zero_episode_consumes_pending(self) -> None:
        p = self._provider()
        p.llm_available = True
        stub = _StubLLM({"episodes": []})
        consolidate.set_llm_for_tests(stub)
        p.sync_turn(
            "hi",
            "hello",
            session_id="sess-ep",
            messages=self._messages("hi", "hello", "2026-10-03T15:00:00-07:00"),
        )
        self.assertTrue(consolidate.run_consolidation(p, "test"))
        n = p._conn.execute("SELECT COUNT(*) FROM pending_turns").fetchone()[0]
        self.assertEqual(n, 0)
        self.assertIn("Do not create an episode merely because Zola restated", stub.last_instructions)
        self.assertIn(
            "A plan, next step, or follow-up about the same thing",
            stub.last_instructions,
        )
        self.assertIn("they'll do the tires next week", stub.last_instructions)
        self.assertIn("do not split an episode per fact_ref", stub.last_instructions)

    def test_stated_unparseable_user_time_logs_keeps_episode(self) -> None:
        """F2: stated phrase + bad user_time → episode kept unknown + time_unresolved log."""
        p = self._provider()
        p.llm_available = True
        user = "I took the Alpine Quill crate to the shop yesterday."
        p.sync_turn(
            user,
            "ok",
            session_id="sess-ep",
            messages=self._messages(user, "ok", "2026-10-05T07:50:37-07:00"),
        )
        pid = p._conn.execute("SELECT id FROM pending_turns").fetchone()["id"]
        p._conn.execute(
            "UPDATE pending_turns SET user_time = ?", ("not-a-timestamp",)
        )
        p._conn.commit()
        stub = _StubLLM(
            self._episode_payload(
                pending_ids=[pid],
                summary="Brian took the Alpine Quill crate to the shop.",
                evidence="yesterday",
                basis="stated",
            )
        )
        consolidate.set_llm_for_tests(stub)
        self.assertTrue(consolidate.run_consolidation(p, "test"))
        ep = p._conn.execute(
            "SELECT event_time, event_time_basis, event_time_evidence FROM episodes"
        ).fetchone()
        self.assertEqual(ep["event_time_basis"], "unknown")
        self.assertIsNone(ep["event_time"])
        self.assertIsNone(ep["event_time_evidence"])
        log_text = (self.home / "logs" / "zola_memory.log").read_text(encoding="utf-8")
        self.assertIn("zola_memory.consolidate.time_unresolved", log_text)
        self.assertIn("reason=unparseable_user_time", log_text)
        self.assertIn("count=1", log_text)

    def test_validation_rejects_bad_fact_ref_system_basis_and_partial(self) -> None:
        p = self._provider()
        p.llm_available = True
        p.sync_turn(
            SYN_PENDING_USER,
            SYN_PENDING_ASST,
            session_id="sess-ep",
            messages=self._messages(SYN_PENDING_USER, SYN_PENDING_ASST, "2026-10-03T15:00:00-07:00"),
        )
        pid = p._conn.execute("SELECT id FROM pending_turns").fetchone()["id"]
        # unknown fact_ref
        stub = _StubLLM(
            self._episode_payload(pending_ids=[pid], fact_refs=["no-such-fact"])
        )
        consolidate.set_llm_for_tests(stub)
        self.assertFalse(consolidate.run_consolidation(p, "test"))
        self.assertEqual(p._conn.execute("SELECT COUNT(*) FROM pending_turns").fetchone()[0], 1)

        # system basis
        stub2 = _StubLLM(
            {
                "episodes": [
                    {
                        **self._episode_payload(pending_ids=[pid])["episodes"][0],
                        "event_time_basis": "system",
                        "event_time_evidence": None,
                    }
                ]
            }
        )
        consolidate.set_llm_for_tests(stub2)
        self.assertFalse(consolidate.run_consolidation(p, "test"))

        # one valid + one invalid → nothing
        good = self._episode_payload(pending_ids=[pid])["episodes"][0]
        bad = dict(good)
        bad["fact_refs"] = ["missing"]
        stub3 = _StubLLM({"episodes": [good, bad]})
        consolidate.set_llm_for_tests(stub3)
        self.assertFalse(consolidate.run_consolidation(p, "test"))
        self.assertEqual(p._conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0], 0)

        # fact-creating field
        stub4 = _StubLLM({"episodes": [good], "new_facts": [{"text": "x"}]})
        consolidate.set_llm_for_tests(stub4)
        self.assertFalse(consolidate.run_consolidation(p, "test"))

    def test_entity_grounding_and_fact_substring(self) -> None:
        p = self._provider()
        p.llm_available = True
        # active fact for substring grounding
        fid = str(uuid.uuid4())
        now = time_context.marker_iso(time_context.capture_now())
        p._conn.execute(
            "INSERT INTO facts (id, target, text, tag, state, learned_at, indexed_at, "
            "updated_at, superseded_at, source) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (fid, "memory", SYN_FACT, "project", "active", now, now, None, None, "file_check"),
        )
        p._conn.commit()
        p.sync_turn(
            "We should lock the demo name.",
            "Agreed.",
            session_id="sess-ep",
            messages=self._messages(
                "We should lock the demo name.", "Agreed.", "2026-10-03T15:00:00-07:00"
            ),
        )
        pid = p._conn.execute("SELECT id FROM pending_turns").fetchone()["id"]
        # name only in fact text (substring), not in turns — allowed by X5
        stub = _StubLLM(
            self._episode_payload(
                pending_ids=[pid],
                summary="Chose the demo codename from the notebook.",
                entities=[{"name": "Alpine Quill", "kind": "project", "id": None, "alias": None}],
                fact_refs=[fid],
            )
        )
        consolidate.set_llm_for_tests(stub)
        self.assertTrue(consolidate.run_consolidation(p, "test"))

        # absent from turns and facts → fail
        p.sync_turn(
            "Something else entirely.",
            "ok",
            session_id="sess-ep",
            messages=self._messages(
                "Something else entirely.", "ok", "2026-10-03T15:10:00-07:00"
            ),
        )
        pid2 = p._conn.execute("SELECT id FROM pending_turns").fetchone()["id"]
        stub_bad = _StubLLM(
            self._episode_payload(
                pending_ids=[pid2],
                entities=[{"name": "ZebraMoon", "kind": "project", "id": None, "alias": None}],
            )
        )
        consolidate.set_llm_for_tests(stub_bad)
        self.assertFalse(consolidate.run_consolidation(p, "test"))

    def test_generation_discard_and_giveup(self) -> None:
        p = self._provider()
        p.llm_available = True
        p.sync_turn(
            SYN_PENDING_USER,
            SYN_PENDING_ASST,
            session_id="sess-ep",
            messages=self._messages(SYN_PENDING_USER, SYN_PENDING_ASST, "2026-10-03T15:00:00-07:00"),
        )
        pid = p._conn.execute("SELECT id FROM pending_turns").fetchone()["id"]
        # Slow stub: bump generation mid-flight via forget API after begin
        real_commit = consolidate._commit

        def flip_then_commit(conn, token, rows, episodes, pending_ids):
            forget.bump_consolidation_generation_best_effort(conn)
            return real_commit(conn, token, rows, episodes, pending_ids)

        stub = _StubLLM(self._episode_payload(pending_ids=[pid]))
        consolidate.set_llm_for_tests(stub)
        with mock.patch.object(consolidate, "_commit", side_effect=flip_then_commit):
            ok = consolidate.run_consolidation(p, "test")
        self.assertFalse(ok)
        self.assertEqual(p._conn.execute("SELECT COUNT(*) FROM pending_turns").fetchone()[0], 1)

        # giveup after max attempts
        consolidate.reset_for_tests()
        consolidate.set_background_enabled_for_tests(False)
        boom = _StubLLM(boom=True)
        consolidate.set_llm_for_tests(boom)
        p.llm_available = True
        for _ in range(consolidate.CONSOLIDATE_MAX_ATTEMPTS):
            consolidate.run_consolidation(p, "test")
        self.assertEqual(p._conn.execute("SELECT COUNT(*) FROM pending_turns").fetchone()[0], 1)

    def test_stated_time_phrases(self) -> None:
        # Fixed Pacific local: Wed Oct 1 2025 15:00 PDT
        turn = datetime(2025, 10, 1, 15, 0, tzinfo=_LA)
        iso = time_context.marker_iso(turn)
        cases = [
            ("yesterday", "2025-09-30"),
            ("today", "2025-10-01"),
            ("last night", "2025-09-30"),
            ("the day before yesterday", "2025-09-29"),
            ("3 days ago", "2025-09-28"),
            ("last monday", "2025-09-29"),
            ("on tuesday", "2025-09-30"),
            ("october 1", "2025-10-01"),
        ]
        for phrase, expect in cases:
            got = consolidate.resolve_stated_time(phrase, iso)
            self.assertEqual(got, expect, phrase)
        # year-omitted past month → nearest past year; explicit future year → unknown
        self.assertEqual(consolidate.resolve_stated_time("october 15", iso), "2024-10-15")
        self.assertIsNone(consolidate.resolve_stated_time("october 15 2027", iso))
        _got, future_reason = consolidate.resolve_stated_time_with_reason(
            "october 15 2027", iso
        )
        self.assertIsNone(_got)
        self.assertEqual(future_reason, "future")
        _got2, bad_phrase = consolidate.resolve_stated_time_with_reason(
            "sometime soonish", iso
        )
        self.assertIsNone(_got2)
        self.assertEqual(bad_phrase, "phrase_not_in_table")
        # DST spring forward: 2025-03-09 01:30 PST → "yesterday" = Mar 8
        dst_turn = datetime(2025, 3, 9, 10, 0, tzinfo=_LA)
        self.assertEqual(
            consolidate.resolve_stated_time("yesterday", time_context.marker_iso(dst_turn)),
            "2025-03-08",
        )
        # missing user_time path → unknown at validate (covered via NULL pending)

    def test_last_weekend_interval_by_turn_day(self) -> None:
        """P6-FIX-2: last weekend → Sat–Sun interval; Mon/Sat/Sun + month boundary + DST."""
        # Mon Oct 5 2026 → Oct 3–4
        mon = datetime(2026, 10, 5, 12, 0, tzinfo=_LA)
        self.assertEqual(
            consolidate.resolve_stated_time("last weekend", time_context.marker_iso(mon)),
            "2026-10-03/2026-10-04",
        )
        # Sat Oct 3 2026 → Sep 26–27
        sat = datetime(2026, 10, 3, 12, 0, tzinfo=_LA)
        self.assertEqual(
            consolidate.resolve_stated_time("last weekend", time_context.marker_iso(sat)),
            "2026-09-26/2026-09-27",
        )
        # Sun Oct 4 2026 → Sep 26–27
        sun = datetime(2026, 10, 4, 12, 0, tzinfo=_LA)
        self.assertEqual(
            consolidate.resolve_stated_time("last weekend", time_context.marker_iso(sun)),
            "2026-09-26/2026-09-27",
        )
        # Month boundary: Mon Nov 2 2026 → Oct 31–Nov 1
        mon_nov = datetime(2026, 11, 2, 12, 0, tzinfo=_LA)
        self.assertEqual(
            consolidate.resolve_stated_time(
                "last weekend", time_context.marker_iso(mon_nov)
            ),
            "2026-10-31/2026-11-01",
        )
        # DST spring-forward weekend: Mon Mar 10 2025 → Mar 8–9
        dst_mon = datetime(2025, 3, 10, 12, 0, tzinfo=_LA)
        self.assertEqual(
            consolidate.resolve_stated_time(
                "last weekend", time_context.marker_iso(dst_mon)
            ),
            "2025-03-08/2025-03-09",
        )
        got, reason = consolidate.resolve_stated_time_with_reason(
            "last weekend", time_context.marker_iso(mon)
        )
        self.assertEqual(got, "2026-10-03/2026-10-04")
        self.assertIsNone(reason)

    def test_last_weekend_display_wording(self) -> None:
        """P6-FIX-2: retrieval wording at 1 day / 10 days / 3 weeks after the Sunday."""
        interval = "2026-10-03/2026-10-04"
        # +1 day (Mon Oct 5) → last weekend
        now1 = datetime(2026, 10, 5, 12, 0, tzinfo=_LA)
        line1 = retrieve.format_episode_line(
            source_user_time="2026-10-05T12:00:00-07:00",
            event_time=interval,
            summary="Painted the Ashford shed trim.",
            open_items=[],
            now=now1,
        )
        self.assertIn(
            "happened: the weekend of Oct 3–4 (last weekend)",
            line1,
        )
        # +10 days (Oct 14) → by Sunday → 10 days ago
        now10 = datetime(2026, 10, 14, 12, 0, tzinfo=_LA)
        line10 = retrieve.format_episode_line(
            source_user_time="2026-10-05T12:00:00-07:00",
            event_time=interval,
            summary="Painted the Ashford shed trim.",
            open_items=[],
            now=now10,
        )
        self.assertIn(
            "happened: the weekend of Oct 3–4 (10 days ago)",
            line10,
        )
        # +3 weeks from Sunday Oct 4 → Oct 25 = 21 days → 3 weeks ago
        now21 = datetime(2026, 10, 25, 12, 0, tzinfo=_LA)
        line21 = retrieve.format_episode_line(
            source_user_time="2026-10-05T12:00:00-07:00",
            event_time=interval,
            summary="Painted the Ashford shed trim.",
            open_items=[],
            now=now21,
        )
        self.assertIn(
            "happened: the weekend of Oct 3–4 (3 weeks ago)",
            line21,
        )
        # Cross-month span wording
        from datetime import date as _date

        cross = retrieve.format_weekend_happened(
            _date(2026, 10, 31),
            _date(2026, 11, 1),
            datetime(2026, 11, 2, 12, 0, tzinfo=_LA),
        )
        self.assertEqual(cross, "the weekend of Oct 31–Nov 1 (last weekend)")

    def test_single_consolidator_lock(self) -> None:
        p1 = self._provider("s1")
        p2 = ZolaMemoryProvider()
        p2.initialize("s2", hermes_home=str(self.home), platform="tui", parent_session_id="")
        p1.llm_available = True
        p2.llm_available = True
        p1.sync_turn(
            SYN_PENDING_USER,
            SYN_PENDING_ASST,
            session_id="s1",
            messages=self._messages(SYN_PENDING_USER, SYN_PENDING_ASST, "2026-10-03T15:00:00-07:00"),
        )
        started = threading.Event()
        release = threading.Event()

        class SlowLLM(_StubLLM):
            def complete_structured(self, **kwargs):
                started.set()
                release.wait(2.0)
                return super().complete_structured(**kwargs)

        pid = p1._conn.execute("SELECT id FROM pending_turns").fetchone()["id"]
        consolidate.set_llm_for_tests(SlowLLM(self._episode_payload(pending_ids=[pid])))
        results: List[bool] = []

        def run1():
            results.append(consolidate.run_consolidation(p1, "a"))

        def run2():
            started.wait(2.0)
            results.append(consolidate.run_consolidation(p2, "b"))

        t1 = threading.Thread(target=run1)
        t2 = threading.Thread(target=run2)
        t1.start()
        t2.start()
        time.sleep(0.05)
        release.set()
        t1.join(3)
        t2.join(3)
        # One acquired lease and committed; the other saw busy or empty pending
        self.assertEqual(sum(1 for x in results if x), 1)


class TestRetrieve(_TempHome):
    def _seed_episode(self, conn, summary: str, entity: str, source_user_time: str, event_time: Optional[str]) -> str:
        eid = str(uuid.uuid4())
        ent = str(uuid.uuid4())
        now = time_context.marker_iso(time_context.capture_now())
        conn.execute(
            "INSERT INTO episodes (id, summary, significance, event_time, event_time_basis, "
            "event_time_evidence, open_items_json, source_session_id, source_turn_start, "
            "source_turn_end, recorded_at, source_user_time) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                eid,
                summary,
                "decision",
                event_time,
                "stated" if event_time else "unknown",
                "yesterday" if event_time else None,
                json.dumps(["call Cedar"], separators=(",", ":")),
                "s1",
                1,
                1,
                now,
                source_user_time,
            ),
        )
        conn.execute(
            "INSERT INTO episodes_fts (episode_id, summary) VALUES (?, ?)",
            (eid, summary),
        )
        conn.execute(
            "INSERT INTO entities (id, name, kind, created_at) VALUES (?,?,?,?)",
            (ent, entity, "project", now),
        )
        conn.execute(
            "INSERT INTO entities_fts (entity_id, name) VALUES (?, ?)",
            (ent, entity),
        )
        conn.execute(
            "INSERT INTO episode_entities (episode_id, entity_id) VALUES (?, ?)",
            (eid, ent),
        )
        conn.commit()
        return eid

    def test_prefetch_block_shape_and_calendar_relative(self) -> None:
        p = self._provider()
        now = datetime(2026, 10, 4, 12, 0, tzinfo=_LA)
        time_context.set_clock_for_tests(lambda: now, timezone=_LA)
        src = "2026-10-03T15:00:00-07:00"  # yesterday
        self._seed_episode(p._conn, SYN_EP_SUMMARY, "Alpine Quill", src, "2026-10-02")
        text = p.prefetch("Tell me about Alpine Quill Cedar demo", session_id="sess-ep")
        self.assertTrue(text.startswith(retrieve.EPISODES_BLOCK_HEADER + "\n"))
        self.assertEqual(
            retrieve.EPISODES_BLOCK_HEADER,
            '[Episodes — past conversations. If you use one, mention roughly when it was '
            '(e.g. "yesterday", "last week").]',
        )
        self.assertIn("talked about", text)
        self.assertIn("happened:", text)
        self.assertIn("still open: call Cedar", text)
        self.assertIn("yesterday", text)
        # date-only relative must not use hours wording
        self.assertNotIn("hours ago", text)
        # same-day → today
        self._seed_episode(
            p._conn,
            "Brian confirmed the Quill palette today.",
            "Quill",
            "2026-10-04T09:00:00-07:00",
            "2026-10-04",
        )
        text2 = retrieve.format_episode_line(
            source_user_time="2026-10-04T09:00:00-07:00",
            event_time="2026-10-04",
            summary="x",
            open_items=[],
            now=now,
        )
        self.assertIn("today", text2)

    def test_gate_movie_query_and_brian_only(self) -> None:
        p = self._provider()
        self._seed_episode(
            p._conn,
            SYN_EP_SUMMARY,
            "Alpine Quill",
            "2026-10-03T15:00:00-07:00",
            None,
        )
        self.assertEqual(p.prefetch(SYN_UNRELATED, session_id="sess-ep"), "")
        p._platform = "cron"
        self.assertEqual(
            p.prefetch("Alpine Quill Cedar demo project", session_id="sess-ep"),
            "",
        )

    def test_r1_entity_word_boundary_match(self) -> None:
        p = self._provider()
        self._seed_episode(
            p._conn,
            "Brian talked with Al about the schedule.",
            "Al",
            "2026-10-03T15:00:00-07:00",
            None,
        )
        self._seed_episode(
            p._conn,
            "Brian renamed the effort Project Larkspur.",
            "Project Larkspur",
            "2026-10-03T16:00:00-07:00",
            None,
        )
        self.assertFalse(retrieve.surface_matches_text("Al", "I'm also tired today"))
        self.assertTrue(retrieve.surface_matches_text("Al", "Al called"))
        self.assertTrue(
            retrieve.surface_matches_text("Project Larkspur", "about Project Larkspur today")
        )
        self.assertEqual(
            p.prefetch("I'm also tired today", session_id="sess-ep"),
            "",
        )
        hit_al = p.prefetch("Al called earlier", session_id="sess-ep")
        self.assertTrue(hit_al.startswith(retrieve.EPISODES_BLOCK_HEADER + "\n"))
        self.assertIn("Al", hit_al)
        hit_phrase = p.prefetch("Project Larkspur status?", session_id="sess-ep")
        self.assertTrue(hit_phrase.startswith(retrieve.EPISODES_BLOCK_HEADER + "\n"))
        self.assertIn("Larkspur", hit_phrase)

    def test_r2_per_candidate_gate_single_common_word(self) -> None:
        p = self._provider()
        self._seed_episode(
            p._conn,
            "Brian said tonight works for the movie plan.",
            "MoviePlan",
            "2026-10-03T15:00:00-07:00",
            None,
        )
        # Query shares only "tonight" with the episode — must not surface
        self.assertEqual(p.prefetch("Any plans tonight?", session_id="sess-ep"), "")

    def test_calibrate_episode_min_score(self) -> None:
        """Phase 4b: per-candidate gate + floor vs single-common-word must-nots."""
        p = self._provider()
        self._seed_episode(
            p._conn,
            SYN_EP_SUMMARY,
            "Alpine Quill",
            "2026-10-03T15:00:00-07:00",
            "2026-10-02",
        )
        self._seed_episode(
            p._conn,
            "Brian scheduled the Cedar demo dry-run for Friday.",
            "Cedar",
            "2026-10-03T16:00:00-07:00",
            None,
        )
        # Single-common-word overlap corpora (must not surface)
        self._seed_episode(
            p._conn,
            "Brian said tonight is fine for a quiet evening.",
            "QuietEvening",
            "2026-10-03T17:00:00-07:00",
            None,
        )
        self._seed_episode(
            p._conn,
            "Brian mentioned the car needs a wash this week.",
            "CarWash",
            "2026-10-03T17:05:00-07:00",
            None,
        )
        self._seed_episode(
            p._conn,
            "Brian talked about work being busy lately.",
            "BusyWork",
            "2026-10-03T17:10:00-07:00",
            None,
        )
        self._seed_episode(
            p._conn,
            "Brian blocked the weekend for rest.",
            "WeekendRest",
            "2026-10-03T17:15:00-07:00",
            None,
        )
        related = [
            "What did we decide about Alpine Quill?",
            "Cedar demo dry-run plan",
            "Alpine Quill project decision",
        ]
        must_not = [
            "Any plans tonight?",
            "How is the car?",
            "How is work going?",
            "Any weekend plans?",
            SYN_UNRELATED,
        ]
        retrieve.set_episode_min_score_for_tests(0.0)

        def returned_top_score(q: str) -> float:
            # Exercise full retrieve path (per-candidate gate)
            block = retrieve.retrieve_episodes(
                p._conn, q, platform="tui", parent_session_id=""
            )
            if not block:
                return 0.0
            # Entity-qualified related hits are boosted to ≥ 1.0
            entity_hits = retrieve._entity_name_hits(p._conn, q)
            if entity_hits:
                return 1.0
            return 0.5

        rel_scores = [returned_top_score(q) for q in related]
        unrel_scores = [returned_top_score(q) for q in must_not]
        self.assertTrue(all(s >= 1.0 for s in rel_scores), rel_scores)
        self.assertTrue(all(s == 0.0 for s in unrel_scores), unrel_scores)
        floor = 0.15
        retrieve.set_episode_min_score_for_tests(floor)
        TestRetrieve.calibrated_floor = floor
        TestRetrieve.calibrated_rel = rel_scores
        TestRetrieve.calibrated_unrel = unrel_scores
        for q in related:
            self.assertTrue(
                retrieve.retrieve_episodes(
                    p._conn, q, platform="tui", parent_session_id=""
                ).startswith(retrieve.EPISODES_BLOCK_HEADER),
                q,
            )
        for q in must_not:
            self.assertEqual(
                retrieve.retrieve_episodes(
                    p._conn, q, platform="tui", parent_session_id=""
                ),
                "",
                q,
            )


class TestForgetReachAndErase(_TempHome):
    def test_cascade_clears_fts_and_bytes(self) -> None:
        """Long-lived provider connection: cascade + sanitize → whole-file clean."""
        p = self._provider()
        self.assertEqual(p._conn.execute("PRAGMA secure_delete").fetchone()[0], 1)
        self.assertTrue(store.fts_secure_delete_active(p._conn))
        eid = str(uuid.uuid4())
        ent = str(uuid.uuid4())
        now = time_context.marker_iso(time_context.capture_now())
        needle = "ZephyrMangoPuzzle42"
        p._conn.execute(
            "INSERT INTO episodes (id, summary, significance, event_time, event_time_basis, "
            "event_time_evidence, open_items_json, source_session_id, source_turn_start, "
            "source_turn_end, recorded_at, source_user_time) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                eid,
                f"Talked about {needle}",
                "event",
                None,
                "unknown",
                None,
                "[]",
                "s1",
                1,
                1,
                now,
                now,
            ),
        )
        p._conn.execute(
            "INSERT INTO episodes_fts (episode_id, summary) VALUES (?, ?)",
            (eid, f"Talked about {needle}"),
        )
        p._conn.execute(
            "INSERT INTO entities (id, name, kind, created_at) VALUES (?,?,?,?)",
            (ent, needle, "other", now),
        )
        p._conn.execute(
            "INSERT INTO entities_fts (entity_id, name) VALUES (?, ?)",
            (ent, needle),
        )
        p._conn.execute(
            "INSERT INTO entity_aliases (entity_id, alias) VALUES (?, ?)",
            (ent, f"{needle}-alias"),
        )
        p._conn.execute(
            "INSERT INTO episode_entities (episode_id, entity_id) VALUES (?, ?)",
            (eid, ent),
        )
        p._conn.commit()
        ok, counts = forget.forget_cascade(
            p._conn,
            [{"id": eid, "kind": forget.RECORD_KIND_EPISODE}],
            reason="tool",
            terms_source=needle,
        )
        self.assertTrue(ok)
        self.assertGreaterEqual(counts["episode_rows"], 1)
        # Same long-lived connection — no close/reopen cheat
        self.assertEqual(store.meta_get(p._conn, store.META_SANITIZE_PENDING) or "0", "0")
        db_path = store.db_path(self.home)
        raw = db_path.read_bytes()
        self.assertNotIn(needle.encode("utf-8"), raw)
        wal = Path(str(db_path) + "-wal")
        if wal.exists() and wal.stat().st_size > 0:
            self.assertNotIn(needle.encode("utf-8"), wal.read_bytes())

    def test_truncate_busy_defers_then_retry_clears_bytes(self) -> None:
        """Second open reader → first TRUNCATE defers; retry after reader closes → scan 0."""
        p = self._provider()
        eid = str(uuid.uuid4())
        now = time_context.marker_iso(time_context.capture_now())
        needle = "BusyReaderToken99"
        p._conn.execute(
            "INSERT INTO episodes (id, summary, significance, event_time, event_time_basis, "
            "event_time_evidence, open_items_json, source_session_id, source_turn_start, "
            "source_turn_end, recorded_at, source_user_time) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                eid,
                f"Talked about {needle}",
                "event",
                None,
                "unknown",
                None,
                "[]",
                "s1",
                1,
                1,
                now,
                now,
            ),
        )
        p._conn.execute(
            "INSERT INTO episodes_fts (episode_id, summary) VALUES (?, ?)",
            (eid, f"Talked about {needle}"),
        )
        p._conn.commit()
        db_path = store.db_path(self.home)
        reader = sqlite3.connect(str(db_path))
        reader.execute("BEGIN")
        reader.execute("SELECT COUNT(*) FROM episodes").fetchone()
        try:
            ok, _counts = forget.forget_cascade(
                p._conn,
                [{"id": eid, "kind": forget.RECORD_KIND_EPISODE}],
                reason="tool",
                terms_source=needle,
            )
            self.assertTrue(ok)
            self.assertEqual(
                p._conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0], 0
            )
            pending = store.meta_get(p._conn, store.META_SANITIZE_PENDING) or "0"
            self.assertEqual(
                pending,
                "1",
                "expected TRUNCATE busy with open reader → sanitize_pending=1",
            )
            log_text = (self.home / "logs" / "zola_memory.log").read_text(encoding="utf-8")
            self.assertIn("zola_memory.sanitize_retry", log_text)
            self.assertIn("action=defer", log_text)
            reader.commit()
            reader.close()
            self.assertTrue(store.try_pending_sanitize(p._conn, trigger="test_retry"))
            self.assertEqual(
                store.meta_get(p._conn, store.META_SANITIZE_PENDING) or "0", "0"
            )
            log_text = (self.home / "logs" / "zola_memory.log").read_text(encoding="utf-8")
            self.assertIn("action=success", log_text)
            raw = db_path.read_bytes()
            self.assertNotIn(needle.encode("utf-8"), raw)
            wal = Path(str(db_path) + "-wal")
            if wal.exists() and wal.stat().st_size > 0:
                self.assertNotIn(needle.encode("utf-8"), wal.read_bytes())
        finally:
            try:
                reader.close()
            except Exception:
                pass

    def test_consolidate_clears_pending_wal_bytes(self) -> None:
        """Phase 7-WAL: pending insert → consolidate (0 eps) → .db/-wal whole-file clean."""
        p = self._provider()
        p.llm_available = True
        needle = "FernhillWalToken77"
        user = f"Quick note: Project {needle} prototype passed."
        asst = f"Noted about {needle}."
        consolidate.set_llm_for_tests(_StubLLM({"episodes": []}))
        p.sync_turn(
            user,
            asst,
            session_id="sess-ep",
            messages=self._messages(user, asst, "2026-10-05T11:00:00-07:00"),
        )
        self.assertEqual(p._conn.execute("SELECT COUNT(*) FROM pending_turns").fetchone()[0], 1)
        self.assertTrue(consolidate.run_consolidation(p, "test"))
        self.assertEqual(p._conn.execute("SELECT COUNT(*) FROM pending_turns").fetchone()[0], 0)
        self.assertEqual(store.meta_get(p._conn, store.META_SANITIZE_PENDING) or "0", "0")
        db_path = store.db_path(self.home)
        raw = db_path.read_bytes()
        self.assertNotIn(needle.encode("utf-8"), raw)
        wal = Path(str(db_path) + "-wal")
        if wal.exists() and wal.stat().st_size > 0:
            self.assertNotIn(needle.encode("utf-8"), wal.read_bytes())

    def test_zero_match_forget_clears_wal_bytes(self) -> None:
        """Phase 7-WAL: confirm=false with no matches still sanitizes → scan clean."""
        p = self._provider()
        needle = "ZeroMatchWalToken88"
        now = time_context.marker_iso(time_context.capture_now())
        pid = str(uuid.uuid4())
        p._conn.execute(
            "INSERT INTO pending_turns (id, session_id, turn_index, user_text, assistant_text, "
            "user_time, assistant_time, consolidation_generation, forget_hold, created_at, "
            "turn_fingerprint) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                pid,
                "sess-ep",
                1,
                f"Talk about {needle}",
                f"Ok {needle}",
                now,
                now,
                0,
                0,
                now,
                "fp-" + needle,
            ),
        )
        p._conn.commit()
        p._conn.execute("DELETE FROM pending_turns WHERE id = ?", (pid,))
        p._conn.commit()
        # Deleted pending still in WAL frames until sanitize
        db_path = store.db_path(self.home)
        wal = Path(str(db_path) + "-wal")
        self.assertTrue(wal.exists() and wal.stat().st_size > 0)
        self.assertIn(needle.encode("utf-8"), wal.read_bytes())
        out = json.loads(
            forget.handle_forget_memory(
                p, {"description": needle, "confirm": False}
            )
        )
        self.assertTrue(out.get("ok"))
        self.assertIn("No matches", out.get("message", ""))
        self.assertEqual(store.meta_get(p._conn, store.META_SANITIZE_PENDING) or "0", "0")
        raw = db_path.read_bytes()
        self.assertNotIn(needle.encode("utf-8"), raw)
        if wal.exists() and wal.stat().st_size > 0:
            self.assertNotIn(needle.encode("utf-8"), wal.read_bytes())

    def test_forgotten_episode_not_retrieved(self) -> None:
        p = self._provider()
        eid = str(uuid.uuid4())
        now = time_context.marker_iso(time_context.capture_now())
        summary = "Brian parked the Vespa near Cedar."
        p._conn.execute(
            "INSERT INTO episodes (id, summary, significance, event_time, event_time_basis, "
            "event_time_evidence, open_items_json, source_session_id, source_turn_start, "
            "source_turn_end, recorded_at, source_user_time) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                eid,
                summary,
                "event",
                None,
                "unknown",
                None,
                "[]",
                "s1",
                1,
                1,
                now,
                now,
            ),
        )
        p._conn.execute(
            "INSERT INTO episodes_fts (episode_id, summary) VALUES (?, ?)",
            (eid, summary),
        )
        p._conn.commit()
        forget.forget_cascade(
            p._conn,
            [{"id": eid, "kind": forget.RECORD_KIND_EPISODE}],
            reason="tool",
            terms_source="Vespa Cedar",
        )
        self.assertEqual(
            retrieve.retrieve_episodes(
                p._conn, "Vespa Cedar", platform="tui", parent_session_id=""
            ),
            "",
        )


class TestCrashSafety(_TempHome):
    def test_pending_survives_and_consolidates_on_new_provider(self) -> None:
        p = self._provider()
        p.sync_turn(
            SYN_PENDING_USER,
            SYN_PENDING_ASST,
            session_id="sess-ep",
            messages=self._messages(SYN_PENDING_USER, SYN_PENDING_ASST, "2026-10-03T15:00:00-07:00"),
        )
        # Process "dies" — no shutdown
        p2 = ZolaMemoryProvider()
        p2.initialize("sess-ep", hermes_home=str(self.home), platform="tui", parent_session_id="")
        p2.llm_available = True
        pid = p2._conn.execute("SELECT id FROM pending_turns").fetchone()["id"]
        consolidate.set_llm_for_tests(_StubLLM(self._episode_payload(pending_ids=[pid])))
        self.assertTrue(consolidate.run_consolidation(p2, "initialize"))
        self.assertEqual(p2._conn.execute("SELECT COUNT(*) FROM pending_turns").fetchone()[0], 0)
        self.assertEqual(p2._conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0], 1)


class TestPrecompressSignal(_TempHome):
    def test_pre_compress_returns_immediately_without_llm(self) -> None:
        p = self._provider()
        p.llm_available = True
        stub = _StubLLM({"episodes": []})
        consolidate.set_llm_for_tests(stub)
        consolidate.set_background_enabled_for_tests(True)
        t0 = time.perf_counter()
        out = p.on_pre_compress([])
        elapsed = time.perf_counter() - t0
        consolidate.set_background_enabled_for_tests(False)
        self.assertEqual(out, "")
        self.assertLess(elapsed, 0.2)
        # Give background thread a moment; must not have required waiting in on_pre_compress
        time.sleep(0.05)


if __name__ == "__main__":
    unittest.main()
