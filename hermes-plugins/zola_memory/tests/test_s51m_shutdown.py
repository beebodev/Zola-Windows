"""S51M-FIX: shutdown vs consolidator ordering, lease ownership, lock order."""

from __future__ import annotations

import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from contextlib import contextmanager
from pathlib import Path
from typing import Any, List
from unittest import mock

_HERMES_ROOT = Path(r"C:\Users\test\Dev\hermes-agent")
if str(_HERMES_ROOT) not in sys.path:
    sys.path.insert(0, str(_HERMES_ROOT))

import consolidate
import log as memlog
import pending
import store
from provider import ZolaMemoryProvider

SYN_USER = "Let's go with Alpine Quill for the Cedar demo."
SYN_ASST = "Got it — Alpine Quill it is."
SYN_SUMMARY = "Brian chose Alpine Quill for the Cedar demo project."

_PLUGIN_DIR = Path(__file__).resolve().parents[1]
_STRESS_N = 20
_STRESS_TIMEOUT_S = 60


class _PauseLLM:
    def __init__(self) -> None:
        self.entered = threading.Event()
        self.release = threading.Event()
        self.calls = 0

    def complete_structured(self, **kwargs: Any) -> Any:
        self.calls += 1
        self.entered.set()
        self.release.wait(30)
        return {"episodes": []}


class _DynamicEpisodeLLM:
    """Build a valid one-episode payload from the provider's current pending rows."""

    def __init__(self, provider: ZolaMemoryProvider) -> None:
        self.provider = provider
        self.calls = 0

    def complete_structured(self, **kwargs: Any) -> Any:
        self.calls += 1
        rows = pending.list_pending_ordered(self.provider._conn)
        ids = [r["id"] for r in rows]
        if not ids:
            return {"episodes": []}
        return {
            "episodes": [
                {
                    "summary": SYN_SUMMARY,
                    "significance": "decision",
                    "entities": [
                        {
                            "name": "Alpine Quill",
                            "kind": "project",
                            "id": None,
                            "alias": None,
                        }
                    ],
                    "fact_refs": [],
                    "source_turn_range": {
                        "start_pending_id": ids[0],
                        "end_pending_id": ids[-1],
                    },
                    "event_time": None,
                    "event_time_basis": "unknown",
                    "event_time_evidence": None,
                    "open_items": [],
                }
            ]
        }


class S51MShutdownTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.mkdtemp(prefix="s51m_shutdown_")
        self.home = Path(self._tmpdir)
        (self.home / "memories").mkdir(parents=True)
        (self.home / "memories" / "USER.md").write_text("", encoding="utf-8")
        (self.home / "memories" / "MEMORY.md").write_text("", encoding="utf-8")
        os.environ["HERMES_HOME"] = str(self.home)
        memlog.reset_log_handler_for_tests()
        consolidate.reset_for_tests()
        consolidate.set_background_enabled_for_tests(False)

    def tearDown(self) -> None:
        consolidate.reset_for_tests()
        memlog.reset_log_handler_for_tests()
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def _provider(self, sid: str = "sess-a") -> ZolaMemoryProvider:
        p = ZolaMemoryProvider()
        p.initialize(sid, hermes_home=str(self.home), platform="tui", parent_session_id="")
        p.llm_available = True
        return p

    def _seed(self, p: ZolaMemoryProvider, n: int = 2) -> List[str]:
        ids: List[str] = []
        with store.locked(p._conn):
            for i in range(n):
                ids.append(
                    pending.write_pending(
                        p._conn,
                        session_id=p._session_id or "sess",
                        turn_index=i,
                        user_text=f"{SYN_USER} {i}",
                        assistant_text=f"{SYN_ASST} {i}",
                        user_time="2026-10-03T15:00:00-07:00",
                        assistant_time="2026-10-03T15:00:01-07:00",
                        disposition="keep",
                    )
                )
        return ids

    def test_shutdown_waits_for_store_lock_then_closes(self) -> None:
        """Deterministic: close cannot finish while another thread holds store.locked."""
        p = self._provider()
        conn = p._conn
        assert conn is not None
        hold = threading.Event()
        released = threading.Event()
        closed_during_hold = []

        def holder() -> None:
            with store.locked(conn):
                hold.set()
                time.sleep(0.15)
                conn.execute("SELECT 1").fetchone()
                closed_during_hold.append(p._conn is None)
            released.set()

        t = threading.Thread(target=holder, daemon=True)
        t.start()
        self.assertTrue(hold.wait(2))
        t0 = time.perf_counter()
        p.shutdown()
        wait_ms = (time.perf_counter() - t0) * 1000
        self.assertTrue(released.wait(2))
        t.join(2)
        self.assertIsNone(p._conn)
        self.assertTrue(closed_during_hold[0] or wait_ms >= 50)
        p.shutdown()

    def test_shutdown_during_llm_no_attempt_no_further_db(self) -> None:
        p = self._provider()
        self._seed(p, 2)
        llm = _PauseLLM()
        consolidate.set_llm_for_tests(llm)
        real_db = consolidate._db
        after_shutdown = {"armed": False, "yields": 0}

        @contextmanager
        def wrapped_db(provider, conn=None):
            with real_db(provider, conn) as c:
                if after_shutdown["armed"]:
                    after_shutdown["yields"] += 1
                yield c

        done = threading.Event()
        result: List[bool] = []

        def worker() -> None:
            with mock.patch.object(consolidate, "_db", wrapped_db):
                result.append(consolidate.run_consolidation(p, "session_end"))
            done.set()

        before = dict(consolidate._attempt_counts)
        threading.Thread(target=worker, daemon=True).start()
        self.assertTrue(llm.entered.wait(5))
        after_shutdown["armed"] = True
        p.shutdown()
        llm.release.set()
        self.assertTrue(done.wait(10))
        self.assertFalse(result[0])
        self.assertEqual(consolidate._attempt_counts, before)
        self.assertEqual(after_shutdown["yields"], 0)

    def test_store_closed_not_counted_as_attempt(self) -> None:
        p = self._provider()
        ids = self._seed(p, 1)
        key = ",".join(sorted(ids))
        llm = _PauseLLM()
        consolidate.set_llm_for_tests(llm)
        done = threading.Event()

        def worker() -> None:
            consolidate.run_consolidation(p, "session_end")
            done.set()

        threading.Thread(target=worker, daemon=True).start()
        self.assertTrue(llm.entered.wait(5))
        p.shutdown()
        llm.release.set()
        self.assertTrue(done.wait(10))
        self.assertNotIn(key, consolidate._attempt_counts)

    def test_programming_error_on_live_provider_counts_attempt(self) -> None:
        p = self._provider()
        ids = self._seed(p, 1)
        key = ",".join(sorted(ids))

        class BoomLLM:
            def complete_structured(self, **kwargs: Any) -> Any:
                raise sqlite3.ProgrammingError("synthetic live-store bug")

        consolidate.set_llm_for_tests(BoomLLM())
        ok = consolidate.run_consolidation(p, "session_end")
        self.assertFalse(ok)
        self.assertFalse(p._shutting_down)
        self.assertIsNotNone(p._conn)
        self.assertEqual(consolidate._attempt_counts.get(key), 1)
        p.shutdown()

    def test_two_store_closed_events_for_two_providers(self) -> None:
        events: List[str] = []
        real_write = memlog.write_event

        def capture(event: str, **fields: Any) -> None:
            events.append(event)
            real_write(event, **fields)

        pa = self._provider("sess-a")
        pb = self._provider("sess-b")
        self._seed(pa, 1)
        self._seed(pb, 1)
        la, lb = _PauseLLM(), _PauseLLM()
        # Shared override — both runs pause; swap per thread via side effect queue
        queue = [la, lb]
        idx = {"i": 0}

        class QueueLLM:
            def complete_structured(self, **kwargs: Any) -> Any:
                llm = queue[idx["i"]]
                idx["i"] += 1
                return llm.complete_structured(**kwargs)

        consolidate.set_llm_for_tests(QueueLLM())
        done_a, done_b = threading.Event(), threading.Event()

        def wa() -> None:
            consolidate.run_consolidation(pa, "session_end")
            done_a.set()

        def wb() -> None:
            consolidate.run_consolidation(pb, "session_end")
            done_b.set()

        with mock.patch.object(memlog, "write_event", capture):
            threading.Thread(target=wa, daemon=True).start()
            self.assertTrue(la.entered.wait(5))
            # B cannot hold lease while A does — release A into shutdown path first
            # Instead: sequential mid-run shutdowns each logging store_closed.
            pa_shut = threading.Event()

            def shut_a() -> None:
                pa.shutdown()
                pa_shut.set()

            threading.Thread(target=shut_a, daemon=True).start()
            # Allow shutdown to mark closed while A is in LLM
            time.sleep(0.05)
            la.release.set()
            self.assertTrue(done_a.wait(10))
            self.assertTrue(pa_shut.wait(10))

            threading.Thread(target=wb, daemon=True).start()
            self.assertTrue(lb.entered.wait(5))
            pb.shutdown()
            lb.release.set()
            self.assertTrue(done_b.wait(10))

        closed = [e for e in events if e == memlog.LOG_EVENT_STORE_CLOSED]
        self.assertEqual(len(closed), 2)

    def test_two_providers_shutdown_a_leaves_b_lease(self) -> None:
        pa = self._provider("sess-a")
        pb = self._provider("sess-b")
        self.assertIsNot(pa._conn, pb._conn)
        self._seed(pb, 2)

        class PauseThenEmpty(_PauseLLM):
            def complete_structured(self, **kwargs: Any) -> Any:
                self.calls += 1
                self.entered.set()
                self.release.wait(30)
                return {"episodes": []}

        llm = PauseThenEmpty()
        consolidate.set_llm_for_tests(llm)
        done = threading.Event()
        committed: List[bool] = []

        def worker() -> None:
            committed.append(consolidate.run_consolidation(pb, "session_end"))
            done.set()

        threading.Thread(target=worker, daemon=True).start()
        self.assertTrue(llm.entered.wait(5))
        with consolidate._lock:
            self.assertEqual(consolidate._lease_holder_id, id(pb))
        pa.shutdown()
        with consolidate._lock:
            self.assertEqual(consolidate._lease_holder_id, id(pb))
        owner = store.meta_get(pb._conn, store.META_CONSOLIDATE_LEASE_OWNER)
        self.assertEqual(owner, consolidate._instance_id)
        llm.release.set()
        self.assertTrue(done.wait(15))
        self.assertEqual(committed, [True])
        self.assertEqual(
            pb._conn.execute("SELECT COUNT(*) FROM pending_turns").fetchone()[0], 0
        )
        pb.shutdown()

    def test_lock_order_never_store_then_provider(self) -> None:
        import inspect
        import re

        src = inspect.getsource(consolidate)
        self.assertIsNone(
            re.search(r"with\s+provider\._lock|provider\._lock\.acquire", src)
        )
        self.assertIn("store.locked", inspect.getsource(consolidate._db))

        p = self._provider()
        conn = p._conn
        assert conn is not None
        hold = threading.Event()
        done = threading.Event()

        def hold_store() -> None:
            with store.locked(conn):
                hold.set()
                time.sleep(0.2)
            done.set()

        threading.Thread(target=hold_store, daemon=True).start()
        self.assertTrue(hold.wait(2))
        t0 = time.perf_counter()
        p.shutdown()
        self.assertLess(time.perf_counter() - t0, 5.0)
        self.assertTrue(done.wait(2))

    def test_quiet_timer_skips_shutting_down_provider(self) -> None:
        consolidate.set_background_enabled_for_tests(True)
        consolidate.set_quiet_minutes_for_tests(0.001)
        pa = self._provider("sess-a")
        pb = self._provider("sess-b")
        self._seed(pb, 1)
        consolidate.note_pending_write()
        pa._shutting_down = True
        picked = consolidate._pick_live_provider()
        self.assertIs(picked, pb)
        pa._shutting_down = False
        pa.shutdown()
        picked2 = consolidate._pick_live_provider()
        self.assertIs(picked2, pb)
        pb.shutdown()

    def test_replacement_provider_recovers_pending(self) -> None:
        pa = self._provider("sess-a")
        self._seed(pa, 2)
        llm = _PauseLLM()
        consolidate.set_llm_for_tests(llm)
        done = threading.Event()

        def worker() -> None:
            consolidate.run_consolidation(pa, "session_end")
            done.set()

        threading.Thread(target=worker, daemon=True).start()
        self.assertTrue(llm.entered.wait(5))
        pa.shutdown()
        llm.release.set()
        self.assertTrue(done.wait(10))

        # Replacement via normal initialize trigger (background on); no hand-run.
        consolidate.set_background_enabled_for_tests(True)
        pb = ZolaMemoryProvider()
        dyn = _DynamicEpisodeLLM(pb)
        consolidate.set_llm_for_tests(dyn)
        pb.initialize("sess-b", hermes_home=str(self.home), platform="tui")
        pb.llm_available = True
        dyn.provider = pb

        deadline = time.time() + 10.0
        while time.time() < deadline:
            if pending.count_pending(pb._conn) == 0:
                break
            time.sleep(0.05)
        self.assertEqual(pending.count_pending(pb._conn), 0)
        eps = pb._conn.execute("SELECT COUNT(*) AS n FROM episodes").fetchone()["n"]
        self.assertEqual(eps, 1)
        pb.shutdown()

    def test_worker_blocked_on_store_lock_gets_store_closed(self) -> None:
        p = self._provider()
        ids = self._seed(p, 1)
        key = ",".join(sorted(ids))
        conn = p._conn
        assert conn is not None
        hold = threading.Event()
        worker_started = threading.Event()
        done = threading.Event()
        outcome: List[Any] = []

        def holder() -> None:
            with store.locked(conn):
                hold.set()
                # Stay until shutdown has nulled _conn and is waiting on this lock.
                while p._conn is not None:
                    time.sleep(0.01)
                time.sleep(0.05)

        def worker() -> None:
            worker_started.set()
            try:
                # Blocks on store.locked inside _acquire_lease / _db until holder releases.
                outcome.append(consolidate.run_consolidation(p, "session_end"))
            except Exception as exc:  # noqa: BLE001
                outcome.append(exc)
            done.set()

        threading.Thread(target=holder, daemon=True).start()
        self.assertTrue(hold.wait(2))
        threading.Thread(target=worker, daemon=True).start()
        self.assertTrue(worker_started.wait(2))
        time.sleep(0.05)  # let worker block on store.locked
        p.shutdown()
        self.assertTrue(done.wait(10))
        self.assertEqual(outcome, [False])
        self.assertNotIn(key, consolidate._attempt_counts)

    def test_unsafe_close_ordering_detected_on_hooks(self) -> None:
        """Fails if connection is closed while another thread still holds store.locked
        without waiting — the fixed shutdown waits, so this passes."""
        p = self._provider()
        conn = p._conn
        assert conn is not None
        in_block = threading.Event()
        saw_closed_in_block = []

        def holder() -> None:
            with store.locked(conn):
                in_block.set()
                time.sleep(0.1)
                try:
                    conn.execute("SELECT 1").fetchone()
                    saw_closed_in_block.append(False)
                except Exception:
                    saw_closed_in_block.append(True)

        threading.Thread(target=holder, daemon=True).start()
        self.assertTrue(in_block.wait(2))
        p.shutdown()
        time.sleep(0.15)
        self.assertEqual(saw_closed_in_block, [False])

    def test_bounded_stress_no_access_violation(self) -> None:
        """Subprocess stress (~20 iters, <60s, faulthandler); fail on any AV."""
        script_path = Path(self._tmpdir) / "bounded_stress.py"
        script_path.write_text(
            "\n".join(
                [
                    "import os, shutil, subprocess, sys, tempfile, threading, time",
                    "from pathlib import Path",
                    f"PLUGIN = Path({str(_PLUGIN_DIR)!r})",
                    f"HERMES = Path({str(_HERMES_ROOT)!r})",
                    f"N = {_STRESS_N}",
                    "",
                    "def child(delay_ms, llm_delay_s):",
                    "    sys.path.insert(0, str(PLUGIN))",
                    "    sys.path.insert(0, str(HERMES))",
                    "    os.environ.setdefault('PYTHONFAULTHANDLER', '1')",
                    "    import faulthandler; faulthandler.enable()",
                    "    import consolidate, pending as pm, store",
                    "    from provider import ZolaMemoryProvider",
                    "    class FakeLLM:",
                    "        def __init__(self, d): self.d = d",
                    "        def complete_structured(self, **k):",
                    "            time.sleep(self.d); return {'episodes': []}",
                    "    home = Path(tempfile.mkdtemp(prefix='s51m-bound-'))",
                    "    try:",
                    "        consolidate.reset_for_tests()",
                    "        consolidate.set_background_enabled_for_tests(False)",
                    "        consolidate.set_llm_for_tests(FakeLLM(llm_delay_s))",
                    "        p = ZolaMemoryProvider()",
                    "        p.initialize('s', hermes_home=str(home), platform='tui')",
                    "        p.llm_available = True",
                    "        with store.locked(p._conn):",
                    "            for i in range(3):",
                    "                pm.write_pending(p._conn, session_id='s', turn_index=i,",
                    "                    user_text='u%d' % i, assistant_text='a%d' % i,",
                    "                    user_time='2026-10-03T15:00:00-07:00',",
                    "                    assistant_time='2026-10-03T15:00:01-07:00', disposition='keep')",
                    "        started, done, err = threading.Event(), threading.Event(), []",
                    "        def worker():",
                    "            try:",
                    "                started.set()",
                    "                consolidate.run_consolidation(p, 'session_end')",
                    "            except BaseException as e:",
                    "                err.append(e)",
                    "            finally:",
                    "                done.set()",
                    "        threading.Thread(target=worker, daemon=True).start()",
                    "        started.wait(2)",
                    "        time.sleep(max(0.0, delay_ms) / 1000.0)",
                    "        p.shutdown()",
                    "        done.wait(30)",
                    "        print('clean' if not err else 'worker_exc')",
                    "        return 0 if not err else 4",
                    "    finally:",
                    "        consolidate.reset_for_tests()",
                    "        shutil.rmtree(home, ignore_errors=True)",
                    "",
                    "if __name__ == '__main__':",
                    "    if len(sys.argv) >= 2 and sys.argv[1] == '--child':",
                    "        raise SystemExit(child(float(sys.argv[2]), float(sys.argv[3])))",
                    "    delays = [0, 1, 2, 5, 10, 20, 50, 100]",
                    "    llm_delays = [0.01, 0.05, 0.2, 0.5]",
                    "    env = os.environ.copy(); env['PYTHONFAULTHANDLER'] = '1'",
                    "    av = 0",
                    "    for n in range(N):",
                    "        d = delays[n % len(delays)]",
                    "        ld = llm_delays[(n // len(delays)) % len(llm_delays)]",
                    "        proc = subprocess.run(",
                    "            [sys.executable, str(Path(__file__).resolve()), '--child', str(d), str(ld)],",
                    "            capture_output=True, text=True, env=env, timeout=30,",
                    "        )",
                    "        rc = proc.returncode & 0xFFFFFFFF",
                    "        out = (proc.stdout or '') + (proc.stderr or '')",
                    "        if rc == 0xC0000005 or 'access violation' in out.lower():",
                    "            av += 1",
                    "            print('AV', n, hex(rc))",
                    "    print('SUMMARY av=%d n=%d' % (av, N))",
                    "    raise SystemExit(1 if av else 0)",
                    "",
                ]
            ),
            encoding="utf-8",
            newline="\n",
        )
        t0 = time.time()
        proc = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=_STRESS_TIMEOUT_S + 30,
            env={**os.environ, "PYTHONFAULTHANDLER": "1"},
        )
        elapsed = time.time() - t0
        self.assertLess(elapsed, _STRESS_TIMEOUT_S + 25)
        self.assertEqual(
            proc.returncode,
            0,
            msg=f"stress failed rc={proc.returncode}\n{proc.stdout}\n{proc.stderr}",
        )
        self.assertIn("av=0", proc.stdout)


if __name__ == "__main__":
    unittest.main()
