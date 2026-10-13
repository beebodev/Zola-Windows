"""P9-STORE origin expansion: forget token, permit lookup, ticketed retrieve."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

_MEMORY = Path(__file__).resolve().parents[1]
_WORKSPACE = _MEMORY.parent / "zola_workspace"
for _entry in (str(_WORKSPACE), str(_MEMORY)):
    while _entry in sys.path:
        sys.path.remove(_entry)
    sys.path.insert(0, str(_WORKSPACE))
    sys.path.insert(0, str(_MEMORY))

import forget
import log as memlog
import origin
import registry
import retrieve
import store
import turn_context

QUERY = "What did we decide about Alpine Quill"
SUMMARY = "Brian chose Alpine Quill for the Cedar demo project."


class _Provider:
    def __init__(self, conn) -> None:
        self._platform = "tui"
        self._parent_session_id = ""
        self._conn = conn
        self._forget_state = forget.ForgetSessionState()
        self._current_user_message = QUERY
        self._session_id = "s-origin"


class OriginTokenTests(unittest.TestCase):
    def setUp(self) -> None:
        self._dir = tempfile.TemporaryDirectory(prefix="p9origin_")
        self.home = Path(self._dir.name)
        self._old_home = os.environ.get("HERMES_HOME")
        os.environ["HERMES_HOME"] = str(self.home)
        memlog.reset_log_handler_for_tests()
        forget.set_client_origin_override_for_tests(None)
        forget.clear_origin_tokens_for_tests()
        origin.clear_for_tests()
        turn_context.clear_all_for_tests()
        registry.clear_for_tests()
        self.memory = store.open_store(self.home)
        self.provider = _Provider(self.memory)
        registry.put(self.provider._session_id, self.provider)

    def tearDown(self) -> None:
        try:
            self.memory.close()
        except Exception:
            pass
        forget.clear_origin_tokens_for_tests()
        forget.set_client_origin_override_for_tests(None)
        origin.clear_for_tests()
        turn_context.clear_all_for_tests()
        registry.clear_for_tests()
        memlog.reset_log_handler_for_tests()
        if self._old_home is None:
            os.environ.pop("HERMES_HOME", None)
        else:
            os.environ["HERMES_HOME"] = self._old_home
        self._dir.cleanup()

    def _arm(self, turn_id: str, message: str) -> None:
        if not origin.wrap_ok():
            origin._test_wrap_ok = True
        turn_context.record_pre_llm_call(
            turn_id=turn_id,
            platform="tui",
            parent_session_id="",
            user_message=message,
        )
        origin.grant_turn_for_tests(turn_id, message)

    def _mint(self, args: dict, turn_id: str = "turn-1") -> str:
        directive = forget.pre_tool_call_hook(
            tool_name="forget_memory",
            args=args,
            session_id=self.provider._session_id,
            turn_id=turn_id,
            tool_call_id="call-1",
        )
        self.assertIsNotNone(directive)
        self.assertEqual(directive["action"], "modify")
        token = directive["args"][forget._ORIGIN_TOKEN_KEY]
        self.assertTrue(token)
        self.assertNotIn(forget._ORIGIN_TOKEN_KEY, args)
        return token

    def _run(self, args: dict) -> str:
        return forget.handle_forget_memory(self.provider, args)

    def test_genuine_ticket_proceeds_and_token_stays_out_of_result_and_logs(self) -> None:
        self._arm("turn-1", QUERY)
        args = {"description": "synthetic", "confirm": False}
        with self.assertLogs("zola_memory", level="INFO") as logs:
            token = self._mint(args)
            args[forget._ORIGIN_TOKEN_KEY] = token
            raw = self._run(args)
        payload = json.loads(raw)
        self.assertTrue(payload["ok"], payload)
        self.assertNotIn(token, raw)
        blob = "\n".join(logs.output)
        self.assertNotIn(token, blob)
        self.assertIn("action=minted", blob)
        self.assertIn("action=consumed", blob)
        log_path = self.home / "logs" / "zola_memory.log"
        if log_path.is_file():
            self.assertNotIn(token, log_path.read_text(encoding="utf-8"))

    def test_no_ticket_refused(self) -> None:
        raw = self._run({"description": "synthetic", "confirm": False})
        payload = json.loads(raw)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["refused_reason"], "origin")

    def test_model_supplied_token_stripped_and_refused(self) -> None:
        forged = "model-supplied-token-value"
        args = {
            "description": "synthetic",
            "confirm": False,
            forget._ORIGIN_TOKEN_KEY: forged,
        }
        blocked = forget.pre_tool_call_hook(
            tool_name="forget_memory",
            args=args,
            session_id=self.provider._session_id,
            turn_id="turn-missing",
        )
        self.assertEqual(blocked["action"], "block")
        self.assertNotIn(forget._ORIGIN_TOKEN_KEY, args)
        self.assertNotIn(forged, json.dumps(blocked))
        raw = self._run(
            {
                "description": "synthetic",
                "confirm": False,
                forget._ORIGIN_TOKEN_KEY: forged,
            }
        )
        self.assertNotIn(forged, raw)
        self.assertEqual(json.loads(raw)["refused_reason"], "origin")

    def test_second_use_refused(self) -> None:
        self._arm("turn-1", QUERY)
        base = {"description": "synthetic", "confirm": False}
        token = self._mint(dict(base))
        first = dict(base)
        first[forget._ORIGIN_TOKEN_KEY] = token
        second = dict(first)
        self.assertTrue(json.loads(self._run(first))["ok"])
        again = json.loads(self._run(second))
        self.assertFalse(again["ok"])
        self.assertEqual(again["refused_reason"], "origin")
        self.assertNotIn(token, json.dumps(again))

    def test_args_changed_after_mint_refused(self) -> None:
        self._arm("turn-1", QUERY)
        minted_from = {"description": "synthetic", "confirm": False}
        token = self._mint(minted_from)
        changed = {
            "description": "synthetic changed",
            "confirm": False,
            forget._ORIGIN_TOKEN_KEY: token,
        }
        raw = self._run(changed)
        payload = json.loads(raw)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["refused_reason"], "origin")
        self.assertNotIn(token, raw)

    def test_expired_token_refused(self) -> None:
        self._arm("turn-1", QUERY)
        args = {"description": "synthetic", "confirm": False}
        token = self._mint(args)
        with forget._token_lock:
            row = forget._tokens[token]
            forget._tokens[token] = (row[0], row[1], row[2], row[3], time.monotonic() - 1)
        raw = self._run({**args, forget._ORIGIN_TOKEN_KEY: token})
        payload = json.loads(raw)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["refused_reason"], "origin")
        self.assertNotIn(token, raw)
        self.assertNotIn(token, forget._tokens)


class PermitLookupTests(unittest.TestCase):
    def setUp(self) -> None:
        origin.clear_for_tests()
        turn_context.clear_all_for_tests()
        if not origin.wrap_ok():
            origin._test_wrap_ok = True

    def tearDown(self) -> None:
        origin.clear_for_tests()
        turn_context.clear_all_for_tests()

    def test_one_match_resolves_and_does_not_consume(self) -> None:
        text = "synthetic permit one"
        turn_context.record_pre_llm_call(
            turn_id="turn-one",
            platform="tui",
            parent_session_id="",
            user_message=text,
        )
        origin.grant_turn_for_tests("turn-one", text)
        with self.assertNoLogs("zola_workspace", level="WARNING"):
            self.assertEqual(turn_context.resolve_turn_from_permit(text), "turn-one")
            self.assertEqual(turn_context.resolve_turn_from_permit(text), "turn-one")

    def test_zero_matches_fail_closed_and_warn(self) -> None:
        text = "synthetic permit zero"
        with self.assertLogs("zola_workspace", level="WARNING") as logs:
            self.assertIsNone(turn_context.resolve_turn_from_permit(text))
        blob = "\n".join(logs.output)
        self.assertIn("origin_unresolved path=permit reason=zero", blob)
        self.assertNotIn(text, blob)

    def test_two_matches_fail_closed_and_warn(self) -> None:
        text = "synthetic permit two"
        origin.grant_turn_for_tests("turn-a", text)
        origin.grant_turn_for_tests("turn-b", text)
        with self.assertLogs("zola_workspace", level="WARNING") as logs:
            self.assertIsNone(turn_context.resolve_turn_from_permit(text))
        blob = "\n".join(logs.output)
        self.assertIn("origin_unresolved path=permit reason=several", blob)
        self.assertNotIn(text, blob)


class TicketedRetrieveTests(unittest.TestCase):
    def setUp(self) -> None:
        self._dir = tempfile.TemporaryDirectory(prefix="p9retrieve_")
        self.home = Path(self._dir.name)
        self._old_home = os.environ.get("HERMES_HOME")
        os.environ["HERMES_HOME"] = str(self.home)
        memlog.reset_log_handler_for_tests()
        forget.set_client_origin_override_for_tests(None)
        origin.clear_for_tests()
        turn_context.clear_all_for_tests()
        self.memory = store.open_store(self.home)

    def tearDown(self) -> None:
        try:
            self.memory.close()
        except Exception:
            pass
        forget.set_client_origin_override_for_tests(None)
        origin.clear_for_tests()
        turn_context.clear_all_for_tests()
        memlog.reset_log_handler_for_tests()
        if self._old_home is None:
            os.environ.pop("HERMES_HOME", None)
        else:
            os.environ["HERMES_HOME"] = self._old_home
        self._dir.cleanup()

    def test_retrieve_returns_candidates_on_a_ticketed_turn(self) -> None:
        now = "2026-10-01T17:00:00-07:00"
        self.memory.execute(
            "INSERT INTO episodes (id, summary, significance, event_time, "
            "event_time_basis, event_time_evidence, open_items_json, "
            "source_session_id, source_turn_start, source_turn_end, "
            "recorded_at, source_user_time) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                "ep-quill",
                SUMMARY,
                "decision",
                None,
                "unknown",
                None,
                "[]",
                "s-origin",
                1,
                1,
                now,
                now,
            ),
        )
        self.memory.execute(
            "INSERT INTO episodes_fts (episode_id, summary) VALUES (?, ?)",
            ("ep-quill", SUMMARY),
        )
        self.memory.execute(
            "INSERT INTO entities (id, name, kind, created_at) VALUES (?,?,?,?)",
            ("ent-quill", "Alpine Quill", "project", now),
        )
        self.memory.execute(
            "INSERT INTO episode_entities (episode_id, entity_id) VALUES (?, ?)",
            ("ep-quill", "ent-quill"),
        )
        self.memory.commit()
        if not origin.wrap_ok():
            origin._test_wrap_ok = True
        turn_context.record_pre_llm_call(
            turn_id="turn-retrieve",
            platform="tui",
            parent_session_id="",
            user_message=QUERY,
        )
        origin.grant_turn_for_tests("turn-retrieve", QUERY)
        block = retrieve.retrieve_episodes(
            self.memory, QUERY, platform="tui", parent_session_id=""
        )
        self.assertIn("Alpine Quill", block)
        log_text = (self.home / "logs" / "zola_memory.log").read_text(encoding="utf-8")
        self.assertIn("candidates=1", log_text)
        self.assertIn("returned=1", log_text)
