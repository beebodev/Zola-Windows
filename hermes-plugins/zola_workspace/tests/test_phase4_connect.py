"""P8-CONNECT Phase 4 tests — no network (socket guard); fake transport / DPAPI."""

from __future__ import annotations

import importlib
import importlib.util
import json
import os
import re
import socket
import sys
import tempfile
import threading
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest import mock
from urllib.parse import parse_qs, urlparse

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
PLUGINS_ROOT = PLUGIN_ROOT.parent
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))
if str(PLUGINS_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGINS_ROOT))

# Ensure hermes_plugins.zola_workspace is importable for consolidator path
if "hermes_plugins" not in sys.modules:
    import types

    hp = types.ModuleType("hermes_plugins")
    hp.__path__ = [str(PLUGINS_ROOT)]  # type: ignore[attr-defined]
    sys.modules["hermes_plugins"] = hp

import auth  # noqa: E402
import framing  # noqa: E402
import gcal  # noqa: E402
import google_http  # noqa: E402
import guards  # noqa: E402
import log as wslog  # noqa: E402
import taint  # noqa: E402
import turn_context  # noqa: E402

# Bind package modules under hermes_plugins.zola_workspace for consolidate tests
import types as _types

_zw = _types.ModuleType("hermes_plugins.zola_workspace")
_zw.__path__ = [str(PLUGIN_ROOT)]  # type: ignore[attr-defined]
sys.modules["hermes_plugins.zola_workspace"] = _zw
sys.modules["hermes_plugins.zola_workspace.taint"] = taint
sys.modules["hermes_plugins.zola_workspace.auth"] = auth
sys.modules["hermes_plugins.zola_workspace.framing"] = framing
sys.modules["hermes_plugins.zola_workspace.google_http"] = google_http
sys.modules["hermes_plugins.zola_workspace.gcal"] = gcal
sys.modules["hermes_plugins.zola_workspace.guards"] = guards
sys.modules["hermes_plugins.zola_workspace.turn_context"] = turn_context
_zw.taint = taint  # type: ignore[attr-defined]


class SocketGuardMixin:
    """Fail any real socket construction during a test."""

    def setUp(self) -> None:  # type: ignore[override]
        super().setUp()
        self._socket_patcher = mock.patch(
            "socket.socket",
            side_effect=AssertionError("P8-CONNECT: unit tests must not open network sockets"),
        )
        self._socket_patcher.start()

    def tearDown(self) -> None:  # type: ignore[override]
        self._socket_patcher.stop()
        super().tearDown()


class _TempHome(SocketGuardMixin, unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self._tmpdir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.home = Path(self._tmpdir.name)
        self._env = mock.patch.dict(os.environ, {"HERMES_HOME": str(self.home)})
        self._env.start()
        # hermes_constants caches? patch get_hermes_home directly
        self._home_patch = mock.patch(
            "hermes_constants.get_hermes_home",
            return_value=self.home,
        )
        try:
            self._home_patch.start()
        except Exception:
            self._home_patch = None
        auth.reset_auth_runtime_for_tests()
        taint.reset_store_path_for_tests()
        google_http.reset_transport_for_tests()
        turn_context.clear_all_for_tests()
        wslog.reset_log_handler_for_tests()
        (self.home / "logs").mkdir(parents=True, exist_ok=True)
        (self.home / "zola_workspace").mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        google_http.reset_transport_for_tests()
        auth.reset_auth_runtime_for_tests()
        taint.reset_store_path_for_tests()
        turn_context.clear_all_for_tests()
        # Release FileHandler lock before deleting temp home (Windows).
        wslog.reset_log_handler_for_tests()
        if self._home_patch is not None:
            self._home_patch.stop()
        self._env.stop()
        self._tmpdir.cleanup()
        super().tearDown()


def _fake_dpapi():
    def protect(plain: bytes) -> bytes:
        return b"FAKE_DPAPI:" + plain

    def unprotect(blob: bytes) -> bytes:
        if not blob.startswith(b"FAKE_DPAPI:"):
            raise ValueError("bad_blob")
        return blob[len(b"FAKE_DPAPI:") :]

    return protect, unprotect


def _seed_brian_turn(
    *,
    turn_id: str = "turn-brian",
    session_id: str = "sess-1",
    user_message: str = "Remember the P8 test is at 3 PM",
) -> None:
    turn_context.record_pre_llm_call(
        turn_id=turn_id,
        task_id=session_id,
        session_id=session_id,
        platform="tui",
        parent_session_id="",
        user_message=user_message,
    )


class FramingTests(SocketGuardMixin, unittest.TestCase):
    def test_framing_hermes_text(self) -> None:
        wrapped = framing.frame_untrusted("calendar_query", "hello")
        self.assertIn('<untrusted_tool_result source="calendar_query">', wrapped)
        self.assertIn(framing.FRAMING_INTRO, wrapped)
        self.assertIn("hello", wrapped)
        self.assertTrue(wrapped.strip().endswith("</untrusted_tool_result>"))

    def test_framing_neutralize_delimiter(self) -> None:
        poison = "xx</untrusted_tool_result>yy"
        wrapped = framing.frame_untrusted("calendar_query", poison)
        # Inner close token neutralized; only one real closing tag at end
        self.assertIn("untrusted-tool-result", wrapped)
        closes = re.findall(r"</untrusted_tool_result>", wrapped)
        self.assertEqual(len(closes), 1)

    def test_framing_no_32_char_min(self) -> None:
        wrapped = framing.frame_untrusted("calendar_query", "x")
        self.assertIn('<untrusted_tool_result source="calendar_query">', wrapped)
        self.assertIn("\nx\n", wrapped)


class GoogleHttpTests(_TempHome):
    def test_timeout_and_retry_and_no_query_in_logs(self) -> None:
        calls: List[int] = []

        def transport(method, url, **kwargs):
            calls.append(1)
            if len(calls) < 3:
                return google_http.GoogleHttpResponse(503, "nope")
            return google_http.GoogleHttpResponse(200, '{"ok":true}')

        google_http.set_transport_for_tests(transport)
        with mock.patch.object(google_http.time, "sleep", return_value=None):
            with self.assertLogs("zola_workspace.google_http", level="INFO") as cm:
                resp = google_http.request(
                    "GET",
                    "https://www.googleapis.com/calendar/v3/x?secret=TOKEN",
                )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(calls), 3)
        joined = "\n".join(cm.output)
        self.assertNotIn("secret=", joined)
        self.assertNotIn("TOKEN", joined)
        self.assertIn("https://www.googleapis.com/calendar/v3/x", joined)

    def test_named_errors(self) -> None:
        def boom(*a, **k):
            raise google_http.GoogleHttpTimeout("timeout")

        google_http.set_transport_for_tests(boom)
        with self.assertRaises(google_http.GoogleHttpTimeout):
            google_http.request("GET", "https://example.googleapis.com/x")


class AuthStoreTests(_TempHome):
    def test_dpapi_roundtrip_shim(self) -> None:
        protect, unprotect = _fake_dpapi()
        auth.set_dpapi_shim_for_tests(protect, unprotect)
        path = self.home / "zola_workspace" / "token.dpapi"
        auth.set_store_path_for_tests(path)
        record = auth.TokenRecord(
            refresh="refresh-synth",
            client_id="cid",
            client_secret="csecret",
            sub="sub-1",
            scopes=tuple(auth.REQUIRED_SCOPES),
            version=auth.TOKEN_VERSION,
            created_at="2026-10-07T00:00:00+00:00",
        )
        auth.save_token_record(record)
        loaded = auth.load_token_record()
        assert loaded is not None
        self.assertEqual(loaded.refresh, "refresh-synth")
        self.assertEqual(loaded.sub, "sub-1")
        self.assertEqual(loaded.scopes, tuple(auth.REQUIRED_SCOPES))
        self.assertTrue(path.exists())
        # Repo must not contain token.dpapi
        repo_hits = list(PLUGIN_ROOT.rglob("token.dpapi"))
        self.assertEqual(repo_hits, [])

    def test_invalid_grant_needs_reconnect_no_retry_loop(self) -> None:
        protect, unprotect = _fake_dpapi()
        auth.set_dpapi_shim_for_tests(protect, unprotect)
        auth.set_store_path_for_tests(self.home / "zola_workspace" / "token.dpapi")
        auth.save_token_record(
            auth.TokenRecord(
                refresh="r",
                client_id="cid",
                client_secret="sec",
                sub="sub-1",
                scopes=tuple(auth.REQUIRED_SCOPES),
                version=1,
                created_at="2026-10-07T00:00:00+00:00",
            )
        )
        calls = {"n": 0}

        def transport(method, url, **kwargs):
            calls["n"] += 1
            raise google_http.GoogleHttpStatusError(
                "http_400",
                status=400,
                body_text='{"error":"invalid_grant"}',
            )

        google_http.set_transport_for_tests(transport)
        with self.assertRaises(RuntimeError) as ctx:
            auth.refresh_access_token(force=True)
        self.assertEqual(str(ctx.exception), auth.REASON_INVALID_GRANT)
        self.assertEqual(auth.get_reconnect_reason(), auth.REASON_INVALID_GRANT)
        self.assertEqual(calls["n"], 1)
        # Second call must not retry the transport — reconnect short-circuit
        with self.assertRaises(RuntimeError):
            auth.refresh_access_token(force=True)
        self.assertEqual(calls["n"], 1)

    def test_sub_mismatch_needs_reconnect(self) -> None:
        protect, unprotect = _fake_dpapi()
        auth.set_dpapi_shim_for_tests(protect, unprotect)
        auth.set_store_path_for_tests(self.home / "zola_workspace" / "token.dpapi")
        auth.save_token_record(
            auth.TokenRecord(
                refresh="r",
                client_id="cid",
                client_secret="sec",
                sub="sub-stored",
                scopes=tuple(auth.REQUIRED_SCOPES),
                version=1,
                created_at="2026-10-07T00:00:00+00:00",
            )
        )

        def transport(method, url, **kwargs):
            return google_http.GoogleHttpResponse(
                200,
                json.dumps(
                    {
                        "access_token": "ya29.synth",
                        "expires_in": 3600,
                        "id_token": "synth.jwt",
                    }
                ),
            )

        google_http.set_transport_for_tests(transport)
        with mock.patch.object(auth, "validate_id_token", return_value="sub-other"):
            with self.assertRaises(RuntimeError) as ctx:
                auth.refresh_access_token(force=True)
        self.assertEqual(str(ctx.exception), auth.REASON_SUB_MISMATCH)

    def test_rerun_without_json_uses_store(self) -> None:
        protect, unprotect = _fake_dpapi()
        auth.set_dpapi_shim_for_tests(protect, unprotect)
        auth.set_store_path_for_tests(self.home / "zola_workspace" / "token.dpapi")
        auth.save_token_record(
            auth.TokenRecord(
                refresh="r",
                client_id="cid-from-store",
                client_secret="sec-from-store",
                sub="sub-1",
                scopes=tuple(auth.REQUIRED_SCOPES),
                version=1,
                created_at="2026-10-07T00:00:00+00:00",
            )
        )
        seen: Dict[str, str] = {}

        def fake_oauth(**kwargs):
            seen["client_id"] = kwargs["client_id"]
            seen["client_secret"] = kwargs["client_secret"]
            return auth.TokenRecord(
                refresh="r2",
                client_id=kwargs["client_id"],
                client_secret=kwargs["client_secret"],
                sub="sub-1",
                scopes=tuple(auth.REQUIRED_SCOPES),
                version=1,
                created_at="2026-10-07T00:00:00+00:00",
            )

        with mock.patch.object(auth, "_run_loopback_oauth", side_effect=fake_oauth):
            auth.run_setup(client_json_path=None)
        self.assertEqual(seen["client_id"], "cid-from-store")
        self.assertEqual(seen["client_secret"], "sec-from-store")


class OAuthLoopbackTests(SocketGuardMixin, unittest.TestCase):
    """Loopback OAuth tests with a fake HTTPServer (socket guard stays on)."""

    def setUp(self) -> None:
        super().setUp()
        auth.reset_auth_runtime_for_tests()
        google_http.reset_transport_for_tests()

    def tearDown(self) -> None:
        auth.reset_auth_runtime_for_tests()
        google_http.reset_transport_for_tests()
        super().tearDown()

    def test_state_mismatch_aborts(self) -> None:
        closed = {"ok": False}
        servers: List[Any] = []

        class FakeServer:
            def __init__(self, addr, handler):
                self.server_address = (addr[0], 54321)
                self.got_callback = threading.Event()
                self.callback_query: Dict[str, str] = {}
                self.expected_state = ""
                self.timeout = 1.0
                servers.append(self)

            def handle_request(self) -> None:
                return

            def server_close(self) -> None:
                closed["ok"] = True

        def open_browser(url: str) -> None:
            # Deliver a callback with the wrong state after wait is armed.
            servers[-1].callback_query = {"code": "abc", "state": "WRONG"}
            servers[-1].got_callback.set()

        auth.set_open_browser_for_tests(open_browser)
        with mock.patch.object(auth, "_OAuthHttpServer", FakeServer):
            with self.assertRaises(ValueError) as ctx:
                auth._run_loopback_oauth(
                    client_id="cid",
                    client_secret="sec",
                    scopes=auth.REQUIRED_SCOPES,
                    timeout_seconds=5,
                )
        self.assertEqual(str(ctx.exception), auth.REASON_STATE_MISMATCH)
        self.assertTrue(closed["ok"], "listener must always be closed")

    def test_stray_callback_does_not_consume(self) -> None:
        """Handler ignores wrong-state requests; valid state still completes."""
        closed = {"ok": False}
        servers: List[Any] = []
        hits = {"n": 0}

        class FakeServer:
            def __init__(self, addr, handler):
                self.server_address = (addr[0], 54321)
                self.got_callback = threading.Event()
                self.callback_query: Dict[str, str] = {}
                self.expected_state = ""
                self.timeout = 1.0
                self._handler_cls = handler
                servers.append(self)

            def handle_request(self) -> None:
                hits["n"] += 1
                # Simulate stray then valid via the real handler logic
                if hits["n"] == 1:
                    qs_state = "WRONG"
                else:
                    qs_state = self.expected_state
                # Mimic _OAuthCallbackHandler.do_GET state gate
                if qs_state != self.expected_state:
                    return
                self.callback_query = {"code": "good-code", "state": self.expected_state}
                self.got_callback.set()

            def server_close(self) -> None:
                closed["ok"] = True

        token_calls = {"n": 0}

        def transport(method, url, **kwargs):
            token_calls["n"] += 1
            if "certs" in url:
                return google_http.GoogleHttpResponse(200, '{"keys":[]}')
            return google_http.GoogleHttpResponse(
                200,
                json.dumps(
                    {
                        "access_token": "ya29.x",
                        "refresh_token": "rt",
                        "expires_in": 3600,
                        "id_token": "synth.jwt",
                        "scope": " ".join(auth.REQUIRED_SCOPES),
                    }
                ),
            )

        google_http.set_transport_for_tests(transport)
        auth.set_open_browser_for_tests(lambda url: None)
        with mock.patch.object(auth, "_OAuthHttpServer", FakeServer):
            with mock.patch.object(auth, "validate_id_token", return_value="sub-1"):
                record = auth._run_loopback_oauth(
                    client_id="cid",
                    client_secret="sec",
                    scopes=auth.REQUIRED_SCOPES,
                    timeout_seconds=5,
                )
        self.assertEqual(record.sub, "sub-1")
        self.assertGreaterEqual(hits["n"], 2)
        self.assertTrue(closed["ok"])

    def test_listener_timeout_and_close(self) -> None:
        closed = {"ok": False}

        class FakeServer:
            def __init__(self, addr, handler):
                self.server_address = (addr[0], 54321)
                self.got_callback = threading.Event()
                self.callback_query: Dict[str, str] = {}
                self.expected_state = ""
                self.timeout = 1.0

            def handle_request(self) -> None:
                return

            def server_close(self) -> None:
                closed["ok"] = True

        auth.set_open_browser_for_tests(lambda url: None)
        with mock.patch.object(auth, "_OAuthHttpServer", FakeServer):
            with self.assertRaises(TimeoutError) as ctx:
                auth._run_loopback_oauth(
                    client_id="cid",
                    client_secret="sec",
                    scopes=auth.REQUIRED_SCOPES,
                    timeout_seconds=0.2,
                )
        self.assertEqual(str(ctx.exception), auth.REASON_TIMEOUT)
        self.assertTrue(closed["ok"], "listener must always be closed")


class TaintTests(_TempHome):
    def test_persists_across_fresh_module(self) -> None:
        path = self.home / "zola_workspace" / "taint.sqlite"
        taint.set_store_path_for_tests(path)
        taint.mark_tainted("sess-persist")
        # Simulate fresh module by clearing and reloading path binding
        taint.reset_store_path_for_tests()
        taint.set_store_path_for_tests(path)
        self.assertTrue(taint.is_tainted("sess-persist"))
        self.assertFalse(taint.is_tainted("sess-other"))

    def test_read_error_tainted_true(self) -> None:
        taint.set_store_path_for_tests(self.home / "zola_workspace" / "taint.sqlite")
        with mock.patch.object(taint, "_connect", side_effect=OSError("boom")):
            # path.exists True path
            path = taint.store_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"not-a-sqlite")
            self.assertTrue(taint.is_tainted("sess-x"))


class MemoryGuardTests(_TempHome):
    def setUp(self) -> None:
        super().setUp()
        taint.set_store_path_for_tests(self.home / "zola_workspace" / "taint.sqlite")
        taint.mark_tainted("sess-1")
        _seed_brian_turn()

    def test_exact_words_allow(self) -> None:
        result = guards.evaluate_memory_taint(
            tool_name="memory",
            args={"action": "add", "content": "P8 test is at 3 PM"},
            session_id="sess-1",
            turn_id="turn-brian",
        )
        self.assertIsNone(result)

    def test_paraphrase_and_yes_block(self) -> None:
        for content in (
            "remember that",
            "yes",
            "Brian's P8 test is at 3 PM",
            "P8 test is at 3 PM and also dinner",
        ):
            with self.subTest(content=content):
                result = guards.evaluate_memory_taint(
                    tool_name="memory",
                    args={"action": "add", "content": content},
                    session_id="sess-1",
                    turn_id="turn-brian",
                )
                self.assertIsNotNone(result)
                assert result is not None
                self.assertEqual(result["message"], guards.BLOCK_MESSAGE_MEMORY_TAINT)

    def test_reworded_block_then_exact_allow(self) -> None:
        blocked = guards.evaluate_memory_taint(
            tool_name="memory",
            args={"action": "add", "content": "Brian's P8 test is at 3 PM"},
            session_id="sess-1",
            turn_id="turn-brian",
        )
        self.assertIsNotNone(blocked)
        allowed = guards.evaluate_memory_taint(
            tool_name="memory",
            args={"action": "add", "content": "P8 test is at 3 PM"},
            session_id="sess-1",
            turn_id="turn-brian",
        )
        self.assertIsNone(allowed)

    def test_untainted_unaffected(self) -> None:
        result = guards.evaluate_memory_taint(
            tool_name="memory",
            args={"action": "add", "content": "anything at all paraphrased"},
            session_id="sess-clean",
            task_id="sess-clean",
            turn_id="turn-brian",
        )
        self.assertIsNone(result)

    def test_remove_unaffected(self) -> None:
        result = guards.evaluate_memory_taint(
            tool_name="memory",
            args={"action": "remove", "old_text": "P8"},
            session_id="sess-1",
            turn_id="turn-brian",
        )
        self.assertIsNone(result)

    def test_operations_whole_batch_block(self) -> None:
        result = guards.evaluate_memory_taint(
            tool_name="memory",
            args={
                "operations": [
                    {"action": "add", "content": "P8 test is at 3 PM"},
                    {"action": "add", "content": "reworded not in message"},
                ]
            },
            session_id="sess-1",
            turn_id="turn-brian",
        )
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["message"], guards.BLOCK_MESSAGE_MEMORY_TAINT)

    def test_missing_turn_blocks(self) -> None:
        result = guards.evaluate_memory_taint(
            tool_name="memory",
            args={"action": "add", "content": "P8 test is at 3 PM"},
            session_id="sess-1",
            turn_id="turn-missing",
        )
        self.assertIsNotNone(result)

    def test_skill_manage_blocked(self) -> None:
        result = guards.evaluate_memory_taint(
            tool_name="skill_manage",
            args={"action": "create"},
            session_id="sess-1",
            turn_id="turn-brian",
        )
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["message"], guards.BLOCK_MESSAGE_SKILL_MANAGE)


class CalendarQueryTests(_TempHome):
    def setUp(self) -> None:
        super().setUp()
        protect, unprotect = _fake_dpapi()
        auth.set_dpapi_shim_for_tests(protect, unprotect)
        auth.set_store_path_for_tests(self.home / "zola_workspace" / "token.dpapi")
        taint.set_store_path_for_tests(self.home / "zola_workspace" / "taint.sqlite")
        auth.save_token_record(
            auth.TokenRecord(
                refresh="r",
                client_id="cid",
                client_secret="sec",
                sub="sub-1",
                scopes=tuple(auth.REQUIRED_SCOPES),
                version=1,
                created_at="2026-10-07T00:00:00+00:00",
            )
        )
        auth.clear_reconnect_reason()
        _seed_brian_turn()

    def _patch_turn_ctx(self):
        return mock.patch.object(
            turn_context, "current_turn_id_from_context", return_value="turn-brian"
        )

    def _install_calendar_transport(
        self,
        *,
        events: Optional[List[Dict[str, Any]]] = None,
        fail_events_after: Optional[int] = None,
        page_token_once: bool = False,
    ) -> List[str]:
        events = events or []
        calls: List[str] = []
        pages = {"n": 0}

        def transport(method, url, **kwargs):
            calls.append(url.split("?")[0])
            safe = url.split("?")[0]
            if "token" in safe:
                return google_http.GoogleHttpResponse(
                    200,
                    json.dumps({"access_token": "ya29.x", "expires_in": 3600}),
                )
            if "calendarList" in safe:
                return google_http.GoogleHttpResponse(
                    200,
                    json.dumps(
                        {
                            "items": [
                                {
                                    "id": "primary",
                                    "summary": "Brian",
                                    "selected": True,
                                    "primary": True,
                                    "timeZone": "America/Los_Angeles",
                                },
                                {
                                    "id": "other",
                                    "summary": "Other",
                                    "selected": False,
                                },
                            ]
                        }
                    ),
                )
            if "/events" in safe:
                pages["n"] += 1
                if fail_events_after is not None and pages["n"] > fail_events_after:
                    raise google_http.GoogleHttpStatusError("http_500", status=500)
                if page_token_once and pages["n"] == 1:
                    return google_http.GoogleHttpResponse(
                        200,
                        json.dumps(
                            {
                                "items": events[:1] if events else [],
                                "nextPageToken": "p2",
                            }
                        ),
                    )
                return google_http.GoogleHttpResponse(
                    200, json.dumps({"items": events if not page_token_once else events[1:]})
                )
            return google_http.GoogleHttpResponse(404, "{}")

        google_http.set_transport_for_tests(transport)
        return calls

    def test_brian_only_refusals(self) -> None:
        # Missing turn
        raw = gcal.calendar_query_handler({})
        data = json.loads(raw)
        self.assertEqual(data["reason"], gcal.REASON_NOT_BRIAN)
        self.assertFalse(taint.is_tainted("sess-1"))

        # turn_id only in kwargs must be ignored
        raw2 = gcal.calendar_query_handler({}, turn_id="turn-brian")
        data2 = json.loads(raw2)
        self.assertEqual(data2["reason"], gcal.REASON_NOT_BRIAN)

        # Wrong platform
        turn_context.clear_all_for_tests()
        turn_context.record_pre_llm_call(
            turn_id="turn-cron",
            session_id="sess-1",
            platform="cron",
            user_message="x",
        )
        with mock.patch.object(
            turn_context, "current_turn_id_from_context", return_value="turn-cron"
        ):
            raw3 = gcal.calendar_query_handler({})
        self.assertEqual(json.loads(raw3)["reason"], gcal.REASON_NOT_BRIAN)

    def test_partial_scope_needs_reconnect(self) -> None:
        auth.save_token_record(
            auth.TokenRecord(
                refresh="r",
                client_id="cid",
                client_secret="sec",
                sub="sub-1",
                scopes=(auth.SCOPE_OPENID, auth.SCOPE_EMAIL),
                version=1,
                created_at="2026-10-07T00:00:00+00:00",
            )
        )
        with self._patch_turn_ctx():
            raw = gcal.calendar_query_handler({"order": "soonest"})
        data = json.loads(raw)
        self.assertEqual(data["state"], gcal.STATE_NEEDS_RECONNECT)
        self.assertEqual(data["reason"], gcal.REASON_MISSING_CALENDAR_SCOPE)

    def test_shapes_and_caps_and_no_match(self) -> None:
        now = datetime.now(timezone.utc)
        events = [
            {
                "summary": "Secret Title Should Not Log",
                "location": "Secret Place",
                "start": {"dateTime": (now + timedelta(hours=2)).isoformat()},
                "end": {"dateTime": (now + timedelta(hours=3)).isoformat()},
                "attendees": [{"displayName": "Dana"}],
                "description": "Secret desc",
            }
        ]
        self._install_calendar_transport(events=events)
        with self._patch_turn_ctx():
            raw = gcal.calendar_query_handler({"order": "soonest", "max_results": 10})
        self.assertIn("<untrusted_tool_result", raw)
        # Extract JSON inside frame
        inner = raw.split("\n\n", 1)[1].rsplit("\n</untrusted_tool_result>", 1)[0]
        data = json.loads(inner)
        self.assertEqual(data["state"], gcal.STATE_COMPLETE)
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(data["items"][0]["title"], "Secret Title Should Not Log")
        self.assertIn("range_searched", data)

        log_path = self.home / "logs" / "zola_workspace.log"
        self.assertTrue(log_path.exists())
        log_text = log_path.read_text(encoding="utf-8")
        self.assertIn("zola_workspace.calendar_query", log_text)
        self.assertNotIn("Secret Title", log_text)
        self.assertNotIn("Secret Place", log_text)
        self.assertNotIn("Dana", log_text)
        self.assertNotIn("Secret desc", log_text)

        # empty → no_match
        self._install_calendar_transport(events=[])
        with self._patch_turn_ctx():
            raw2 = gcal.calendar_query_handler({"order": "soonest"})
        inner2 = raw2.split("\n\n", 1)[1].rsplit("\n</untrusted_tool_result>", 1)[0]
        data2 = json.loads(inner2)
        self.assertEqual(data2["state"], gcal.STATE_NO_MATCH)
        self.assertIn("range_searched", data2)

    def test_most_recent_and_all_day(self) -> None:
        now = datetime.now(timezone.utc)
        events = [
            {
                "summary": "Older",
                "start": {"dateTime": (now - timedelta(days=10)).isoformat()},
                "end": {"dateTime": (now - timedelta(days=10, hours=-1)).isoformat()},
            },
            {
                "summary": "Newer",
                "start": {"dateTime": (now - timedelta(days=1)).isoformat()},
                "end": {"dateTime": (now - timedelta(days=1, hours=-1)).isoformat()},
            },
            {
                "summary": "All Day",
                "start": {"date": (now - timedelta(days=2)).date().isoformat()},
                "end": {"date": (now - timedelta(days=1)).date().isoformat()},
            },
        ]
        self._install_calendar_transport(events=events)
        with self._patch_turn_ctx():
            raw = gcal.calendar_query_handler(
                {"order": "most_recent", "max_results": 2}
            )
        inner = raw.split("\n\n", 1)[1].rsplit("\n</untrusted_tool_result>", 1)[0]
        data = json.loads(inner)
        self.assertEqual(data["state"], gcal.STATE_COMPLETE)
        titles = [i["title"] for i in data["items"]]
        self.assertEqual(titles[0], "Newer")
        self.assertTrue(any(i.get("all_day") for i in data["items"]))

    def test_paging_incomplete(self) -> None:
        now = datetime.now(timezone.utc)
        events = [
            {
                "summary": "E1",
                "start": {"dateTime": (now + timedelta(hours=1)).isoformat()},
                "end": {"dateTime": (now + timedelta(hours=2)).isoformat()},
            },
            {
                "summary": "E2",
                "start": {"dateTime": (now + timedelta(hours=3)).isoformat()},
                "end": {"dateTime": (now + timedelta(hours=4)).isoformat()},
            },
        ]
        self._install_calendar_transport(
            events=events, page_token_once=True, fail_events_after=1
        )
        with self._patch_turn_ctx():
            raw = gcal.calendar_query_handler({"order": "soonest"})
        inner = raw.split("\n\n", 1)[1].rsplit("\n</untrusted_tool_result>", 1)[0]
        data = json.loads(inner)
        self.assertEqual(data["state"], gcal.STATE_INCOMPLETE)
        self.assertNotEqual(data["state"], gcal.STATE_NO_MATCH)

    def test_taint_before_content_and_write_fail(self) -> None:
        # Fresh session — taint must be marked before framed content returns
        self.assertFalse(taint.is_tainted("sess-1"))
        now = datetime.now(timezone.utc)
        events = [
            {
                "summary": "Meet",
                "start": {"dateTime": (now + timedelta(hours=1)).isoformat()},
                "end": {"dateTime": (now + timedelta(hours=2)).isoformat()},
            }
        ]
        self._install_calendar_transport(events=events)
        with self._patch_turn_ctx():
            raw = gcal.calendar_query_handler({"order": "soonest"})
        self.assertTrue(taint.is_tainted("sess-1"))
        self.assertIn("Meet", raw)

        # Write fail → framed error, no event content
        taint.reset_store_path_for_tests()
        taint.set_store_path_for_tests(self.home / "zola_workspace" / "taint2.sqlite")
        turn_context.clear_all_for_tests()
        _seed_brian_turn(session_id="sess-2")
        self._install_calendar_transport(events=events)
        with self._patch_turn_ctx():
            with mock.patch.object(taint, "mark_tainted", side_effect=OSError("disk")):
                raw_fail = gcal.calendar_query_handler({"order": "soonest"})
        self.assertIn("taint_write_failed", raw_fail)
        self.assertNotIn("Meet", raw_fail)

    def test_max_results_cap(self) -> None:
        now = datetime.now(timezone.utc)
        events = [
            {
                "summary": f"E{i}",
                "start": {"dateTime": (now + timedelta(hours=i + 1)).isoformat()},
                "end": {"dateTime": (now + timedelta(hours=i + 2)).isoformat()},
            }
            for i in range(30)
        ]
        self._install_calendar_transport(events=events)
        with self._patch_turn_ctx():
            raw = gcal.calendar_query_handler({"order": "soonest", "max_results": 100})
        inner = raw.split("\n\n", 1)[1].rsplit("\n</untrusted_tool_result>", 1)[0]
        data = json.loads(inner)
        self.assertEqual(len(data["items"]), gcal.MAX_RESULTS_CAP)
        self.assertTrue(data["more_available"])


class TaintLineageTests(_TempHome):
    def test_compression_lineage_marks_tip_and_blocks_memory(self) -> None:
        """Mark S1; S2 parent=S1 in fake state.db → is_tainted(S2) and memory add blocked."""
        path = self.home / "zola_workspace" / "taint.sqlite"
        taint.set_store_path_for_tests(path)
        # Fake Hermes state.db with compression lineage S1 → S2
        state_db = self.home / "state.db"
        conn = __import__("sqlite3").connect(str(state_db))
        try:
            conn.execute(
                "CREATE TABLE sessions (id TEXT PRIMARY KEY, parent_session_id TEXT)"
            )
            conn.execute(
                "INSERT INTO sessions (id, parent_session_id) VALUES (?, ?)",
                ("S1", None),
            )
            conn.execute(
                "INSERT INTO sessions (id, parent_session_id) VALUES (?, ?)",
                ("S2", "S1"),
            )
            conn.commit()
        finally:
            conn.close()

        taint.mark_tainted("S1")
        self.assertTrue(taint.is_tainted("S1"))
        self.assertTrue(taint.is_tainted("S2"))
        self.assertTrue(taint.is_tainted(task_id="S2"))

        _seed_brian_turn(session_id="S2", turn_id="turn-s2", user_message="Remember the P8 test is at 3 PM")
        blocked = guards.evaluate_memory_taint(
            tool_name="memory",
            args={"action": "add", "content": "anything paraphrased"},
            session_id="S2",
            task_id="S2",
            turn_id="turn-s2",
        )
        self.assertIsNotNone(blocked)

        # Tip re-mark via pre_llm_call when lineage already tainted
        turn_context.pre_llm_call_hook(
            turn_id="turn-s2b",
            session_id="S2",
            task_id="S2",
            platform="tui",
            parent_session_id="",
            user_message="hi",
        )
        # S2 itself should now be a direct key as well
        path_conn = __import__("sqlite3").connect(str(path))
        try:
            rows = {
                r[0]
                for r in path_conn.execute(
                    "SELECT session_id FROM session_taint"
                ).fetchall()
            }
        finally:
            path_conn.close()
        self.assertIn("S1", rows)
        self.assertIn("S2", rows)

    def test_is_tainted_empty_both_false(self) -> None:
        self.assertFalse(taint.is_tainted())
        self.assertFalse(taint.is_tainted(session_id="", task_id=""))

    def test_lineage_lookup_raises_is_tainted_true_blocks_memory(self) -> None:
        """Lineage resolver error → fail closed; memory add blocked."""
        path = self.home / "zola_workspace" / "taint.sqlite"
        taint.set_store_path_for_tests(path)

        def boom(_sid: str):
            raise RuntimeError("state.db locked")

        taint.set_lineage_root_fn_for_tests(boom)
        self.assertTrue(taint.is_tainted("sess-err"))
        # Tip must not be treated clean by pre_llm_call
        turn_context.pre_llm_call_hook(
            turn_id="turn-err",
            session_id="sess-err",
            task_id="sess-err",
            platform="tui",
            parent_session_id="",
            user_message="hi",
        )
        self.assertTrue(taint.is_tainted("sess-err"))

        _seed_brian_turn(
            session_id="sess-err",
            turn_id="turn-err-mem",
            user_message="Remember the P8 test is at 3 PM",
        )
        blocked = guards.evaluate_memory_taint(
            tool_name="memory",
            args={"action": "add", "content": "anything"},
            session_id="sess-err",
            task_id="sess-err",
            turn_id="turn-err-mem",
        )
        self.assertIsNotNone(blocked)

    def test_lineage_walk_cap_is_tainted_true(self) -> None:
        """Walk-cap hit is an error → is_tainted True."""
        path = self.home / "zola_workspace" / "taint.sqlite"
        taint.set_store_path_for_tests(path)
        state_db = self.home / "state.db"
        conn = __import__("sqlite3").connect(str(state_db))
        try:
            conn.execute(
                "CREATE TABLE sessions (id TEXT PRIMARY KEY, parent_session_id TEXT)"
            )
            # Chain longer than LINEAGE_WALK_CAP: tip → … → root
            prev = None
            tip = None
            for i in range(taint.LINEAGE_WALK_CAP + 5):
                sid = f"L{i}"
                tip = sid
                conn.execute(
                    "INSERT INTO sessions (id, parent_session_id) VALUES (?, ?)",
                    (sid, prev),
                )
                prev = sid
            conn.commit()
        finally:
            conn.close()
        self.assertIsNotNone(tip)
        self.assertTrue(taint.is_tainted(tip))
        with self.assertRaises(taint.LineageLookupError):
            taint.lineage_root(tip)  # type: ignore[arg-type]


class HermesPrivateSchemaPinTests(SocketGuardMixin, unittest.TestCase):
    """Pin Hermes private lineage schema — fail suite if dependency drifts."""

    _HERMES_ROOT = Path(r"C:\Users\test\Dev\hermes-agent")

    def test_hermes_state_db_lineage_schema_pin(self) -> None:
        root = self._HERMES_ROOT
        if not root.is_dir():
            self.fail(
                "Hermes private dependency missing: hermes-agent checkout at "
                f"{root} (DEFAULT_DB_PATH / sessions.parent_session_id pin)"
            )
        state_py = root / "hermes_state.py"
        common_py = root / "hermes_state_common.py"
        compression_py = root / "hermes_state_compression.py"
        for path, name in (
            (state_py, "hermes_state.py"),
            (common_py, "hermes_state_common.py"),
            (compression_py, "hermes_state_compression.py"),
        ):
            if not path.is_file():
                self.fail(
                    f"Hermes private dependency missing or renamed: {name} "
                    f"(needed for state.db lineage pin)"
                )

        state_text = state_py.read_text(encoding="utf-8")
        # hermes_state.py L157: DEFAULT_DB_PATH = get_hermes_home() / "state.db"
        if not re.search(
            r"^DEFAULT_DB_PATH\s*=\s*_IMPORT_DEFAULT_DB_PATH\s*=\s*"
            r'get_hermes_home\(\)\s*/\s*"state\.db"',
            state_text,
            re.M,
        ):
            self.fail(
                "Hermes private dependency drifted: hermes_state.DEFAULT_DB_PATH "
                'must be get_hermes_home() / "state.db" (hermes_state.py ~L157)'
            )

        common_text = common_py.read_text(encoding="utf-8")
        if "CREATE TABLE IF NOT EXISTS sessions (" not in common_text:
            self.fail(
                "Hermes private dependency drifted: sessions CREATE TABLE missing "
                "in hermes_state_common.py"
            )
        # sessions table must declare id and parent_session_id columns
        create_match = re.search(
            r"CREATE TABLE IF NOT EXISTS sessions\s*\((.*?)\);",
            common_text,
            re.S,
        )
        if create_match is None:
            self.fail(
                "Hermes private dependency drifted: could not parse sessions "
                "CREATE TABLE in hermes_state_common.py"
            )
        cols = create_match.group(1)
        if not re.search(r"\bid\s+TEXT\s+PRIMARY KEY\b", cols):
            self.fail(
                "Hermes private dependency drifted: sessions.id TEXT PRIMARY KEY "
                "missing in hermes_state_common.py"
            )
        if not re.search(r"\bparent_session_id\s+TEXT\b", cols):
            self.fail(
                "Hermes private dependency drifted: sessions.parent_session_id "
                "missing in hermes_state_common.py"
            )

        compression_text = compression_py.read_text(encoding="utf-8")
        if "def _publish_child_session_row(" not in compression_text:
            self.fail(
                "Hermes private dependency missing or renamed: "
                "hermes_state_compression._publish_child_session_row"
            )
        # INSERT must include parent_session_id column and bind value
        if not re.search(
            r"INSERT INTO sessions\s*\([^)]*\bparent_session_id\b[^)]*\)",
            compression_text,
            re.S,
        ):
            self.fail(
                "Hermes private dependency drifted: "
                "_publish_child_session_row must INSERT parent_session_id "
                "(hermes_state_compression.py ~L201–217)"
            )


class MemoryGuardIdTests(_TempHome):
    def setUp(self) -> None:
        super().setUp()
        taint.set_store_path_for_tests(self.home / "zola_workspace" / "taint.sqlite")

    def test_missing_ids_block_add_and_skill_manage(self) -> None:
        blocked = guards.evaluate_memory_taint(
            tool_name="memory",
            args={"action": "add", "content": "x"},
        )
        self.assertIsNotNone(blocked)
        blocked2 = guards.evaluate_memory_taint(
            tool_name="skill_manage",
            args={"action": "create"},
        )
        self.assertIsNotNone(blocked2)

    def test_taint_path_exception_blocks_with_guard_error(self) -> None:
        with mock.patch.object(taint, "is_tainted_ids", side_effect=OSError("boom")):
            result = guards.pre_tool_call_hook(
                tool_name="memory",
                args={"action": "add", "content": "x"},
                session_id="sess-x",
                task_id="sess-x",
            )
        self.assertIsNotNone(result)
        log_path = self.home / "logs" / "zola_workspace.log"
        self.assertTrue(log_path.exists())
        self.assertIn("guard_error", log_path.read_text(encoding="utf-8"))


class ScopeAliasTests(_TempHome):
    def test_userinfo_email_url_satisfies_required_email(self) -> None:
        # Realistic token-response scope string — NOT a REQUIRED_SCOPES copy
        granted = (
            "openid "
            "https://www.googleapis.com/auth/userinfo.email "
            "https://www.googleapis.com/auth/calendar.readonly "
            "https://www.googleapis.com/auth/gmail.readonly "
            "https://www.googleapis.com/auth/gmail.compose "
            "https://www.googleapis.com/auth/drive.readonly "
            "https://www.googleapis.com/auth/contacts.readonly"
        ).split()
        missing = auth.missing_scopes(granted)
        self.assertEqual(missing, [])
        # Without alias, email short name would be "missing"
        self.assertNotIn(auth.SCOPE_EMAIL, missing)


class StaleReconnectTests(_TempHome):
    def test_store_rewrite_clears_stale_needs_reconnect(self) -> None:
        protect, unprotect = _fake_dpapi()
        auth.set_dpapi_shim_for_tests(protect, unprotect)
        auth.set_store_path_for_tests(self.home / "zola_workspace" / "token.dpapi")
        auth.save_token_record(
            auth.TokenRecord(
                refresh="r-old",
                client_id="cid",
                client_secret="sec",
                sub="sub-1",
                scopes=tuple(auth.REQUIRED_SCOPES),
                version=1,
                created_at="2026-10-01T00:00:00+00:00",
            )
        )
        auth.set_reconnect_reason(auth.REASON_INVALID_GRANT)
        self.assertEqual(auth.get_reconnect_reason(), auth.REASON_INVALID_GRANT)

        # Setup (other process) rewrites store with new created_at
        auth.save_token_record(
            auth.TokenRecord(
                refresh="r-new",
                client_id="cid",
                client_secret="sec",
                sub="sub-1",
                scopes=tuple(auth.REQUIRED_SCOPES),
                version=1,
                created_at="2026-10-07T12:00:00+00:00",
            )
        )
        status = auth.store_status()
        self.assertIsNone(status["needs_reconnect"])
        self.assertTrue(status["connected"])
        self.assertIsNone(auth.get_reconnect_reason())

        # refresh_access_token also clears + retries once
        auth.set_reconnect_reason(auth.REASON_INVALID_GRANT)
        auth.save_token_record(
            auth.TokenRecord(
                refresh="r-newer",
                client_id="cid",
                client_secret="sec",
                sub="sub-1",
                scopes=tuple(auth.REQUIRED_SCOPES),
                version=1,
                created_at="2026-10-07T13:00:00+00:00",
            )
        )

        def transport(method, url, **kwargs):
            return google_http.GoogleHttpResponse(
                200,
                json.dumps({"access_token": "ya29.ok", "expires_in": 3600}),
            )

        google_http.set_transport_for_tests(transport)
        token = auth.refresh_access_token(force=True)
        self.assertEqual(token, "ya29.ok")


class JwksRotationTests(_TempHome):
    def test_rotated_kid_refetch_then_success(self) -> None:
        from cryptography.hazmat.primitives.asymmetric import rsa
        import jwt as pyjwt
        import base64

        def _b64url_uint(val: int) -> str:
            raw = val.to_bytes((val.bit_length() + 7) // 8, "big")
            return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")

        old_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        new_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        def jwk_for(kid: str, priv) -> Dict[str, Any]:
            pub = priv.public_key().public_numbers()
            return {
                "kty": "RSA",
                "kid": kid,
                "use": "sig",
                "alg": "RS256",
                "n": _b64url_uint(pub.n),
                "e": _b64url_uint(pub.e),
            }

        stale_jwks = {"keys": [jwk_for("kid-old", old_key)]}
        fresh_jwks = {"keys": [jwk_for("kid-new", new_key)]}
        fetches = {"n": 0}

        def transport(method, url, **kwargs):
            fetches["n"] += 1
            if fetches["n"] == 1:
                return google_http.GoogleHttpResponse(200, json.dumps(stale_jwks))
            return google_http.GoogleHttpResponse(200, json.dumps(fresh_jwks))

        google_http.set_transport_for_tests(transport)
        auth.clear_jwks_cache_for_tests()

        now = int(time.time())
        token = pyjwt.encode(
            {
                "iss": "https://accounts.google.com",
                "aud": "cid",
                "sub": "sub-rot",
                "exp": now + 300,
                "iat": now,
            },
            new_key,
            algorithm="RS256",
            headers={"kid": "kid-new"},
        )
        sub = auth.validate_id_token(token, client_id="cid")
        self.assertEqual(sub, "sub-rot")
        self.assertEqual(fetches["n"], 2)


class CalendarExtrasTests(_TempHome):
    def setUp(self) -> None:
        super().setUp()
        protect, unprotect = _fake_dpapi()
        auth.set_dpapi_shim_for_tests(protect, unprotect)
        auth.set_store_path_for_tests(self.home / "zola_workspace" / "token.dpapi")
        taint.set_store_path_for_tests(self.home / "zola_workspace" / "taint.sqlite")
        auth.save_token_record(
            auth.TokenRecord(
                refresh="r",
                client_id="cid",
                client_secret="sec",
                sub="sub-1",
                scopes=tuple(auth.REQUIRED_SCOPES),
                version=1,
                created_at="2026-10-07T00:00:00+00:00",
            )
        )
        auth.clear_reconnect_reason()
        _seed_brian_turn()

    def _patch_turn_ctx(self):
        return mock.patch.object(
            turn_context, "current_turn_id_from_context", return_value="turn-brian"
        )

    def _frame_json(self, raw: str) -> Dict[str, Any]:
        inner = raw.split("\n\n", 1)[1].rsplit("\n</untrusted_tool_result>", 1)[0]
        return json.loads(inner)

    def test_end_before_start_bad_args(self) -> None:
        now = datetime.now(timezone.utc)
        with self._patch_turn_ctx():
            raw = gcal.calendar_query_handler(
                {
                    "order": "soonest",
                    "start": (now + timedelta(days=2)).isoformat(),
                    "end": (now + timedelta(days=1)).isoformat(),
                }
            )
        data = self._frame_json(raw)
        self.assertEqual(data["reason"], gcal.REASON_BAD_ARGS)

    def test_timezone_from_primary_calendar_list(self) -> None:
        now = datetime.now(timezone.utc)
        events = [
            {
                "summary": "Meet",
                "start": {"dateTime": (now + timedelta(hours=1)).isoformat()},
                "end": {"dateTime": (now + timedelta(hours=2)).isoformat()},
                "attendees": [
                    {"displayName": "Brian", "self": True, "responseStatus": "accepted"}
                ],
                "organizer": {"self": True},
            }
        ]

        def transport(method, url, **kwargs):
            safe = url.split("?")[0]
            if "token" in safe:
                return google_http.GoogleHttpResponse(
                    200, json.dumps({"access_token": "ya29.x", "expires_in": 3600})
                )
            if "calendarList" in safe:
                return google_http.GoogleHttpResponse(
                    200,
                    json.dumps(
                        {
                            "items": [
                                {
                                    "id": "primary",
                                    "summary": "Brian",
                                    "selected": True,
                                    "primary": True,
                                    "timeZone": "America/New_York",
                                }
                            ]
                        }
                    ),
                )
            if "/events" in safe:
                return google_http.GoogleHttpResponse(200, json.dumps({"items": events}))
            return google_http.GoogleHttpResponse(404, "{}")

        google_http.set_transport_for_tests(transport)
        with self._patch_turn_ctx():
            raw = gcal.calendar_query_handler({"order": "soonest"})
        data = self._frame_json(raw)
        self.assertEqual(data["timezone"], "America/New_York")
        self.assertEqual(data["timezone_source"], gcal.TZ_SOURCE_CALENDAR_PRIMARY)
        self.assertEqual(data["items"][0]["response_status"], "accepted")

    def test_timezone_local_fallback_never_silent_utc(self) -> None:
        def transport(method, url, **kwargs):
            safe = url.split("?")[0]
            if "token" in safe:
                return google_http.GoogleHttpResponse(
                    200, json.dumps({"access_token": "ya29.x", "expires_in": 3600})
                )
            if "calendarList" in safe:
                return google_http.GoogleHttpResponse(
                    200,
                    json.dumps(
                        {
                            "items": [
                                {
                                    "id": "primary",
                                    "summary": "Brian",
                                    "selected": True,
                                    "primary": True,
                                    # no timeZone
                                }
                            ]
                        }
                    ),
                )
            if "/events" in safe:
                return google_http.GoogleHttpResponse(200, json.dumps({"items": []}))
            return google_http.GoogleHttpResponse(404, "{}")

        google_http.set_transport_for_tests(transport)
        with self._patch_turn_ctx():
            raw = gcal.calendar_query_handler({"order": "soonest"})
        data = self._frame_json(raw)
        self.assertEqual(data["timezone_source"], gcal.TZ_SOURCE_LOCAL)
        self.assertTrue(data["timezone"])
        # Must not silently claim bare UTC unless that truly is local
        if data["timezone"] == "UTC":
            local_name = gcal._pc_local_timezone_name()
            self.assertEqual(local_name, "UTC")

    def test_response_status_organizer_and_none(self) -> None:
        now = datetime.now(timezone.utc)
        events = [
            {
                "summary": "Org",
                "start": {"dateTime": (now + timedelta(hours=1)).isoformat()},
                "end": {"dateTime": (now + timedelta(hours=2)).isoformat()},
                "organizer": {"self": True},
            },
            {
                "summary": "Other",
                "start": {"dateTime": (now + timedelta(hours=3)).isoformat()},
                "end": {"dateTime": (now + timedelta(hours=4)).isoformat()},
                "organizer": {"email": "other@example.com"},
                "attendees": [{"email": "other@example.com", "responseStatus": "accepted"}],
            },
        ]

        def transport(method, url, **kwargs):
            safe = url.split("?")[0]
            if "token" in safe:
                return google_http.GoogleHttpResponse(
                    200, json.dumps({"access_token": "ya29.x", "expires_in": 3600})
                )
            if "calendarList" in safe:
                return google_http.GoogleHttpResponse(
                    200,
                    json.dumps(
                        {
                            "items": [
                                {
                                    "id": "primary",
                                    "summary": "Brian",
                                    "selected": True,
                                    "primary": True,
                                    "timeZone": "America/Los_Angeles",
                                }
                            ]
                        }
                    ),
                )
            if "/events" in safe:
                return google_http.GoogleHttpResponse(200, json.dumps({"items": events}))
            return google_http.GoogleHttpResponse(404, "{}")

        google_http.set_transport_for_tests(transport)
        with self._patch_turn_ctx():
            raw = gcal.calendar_query_handler({"order": "soonest"})
        data = self._frame_json(raw)
        statuses = {i["title"]: i["response_status"] for i in data["items"]}
        self.assertEqual(statuses["Org"], gcal.RESPONSE_ORGANIZER)
        self.assertEqual(statuses["Other"], gcal.RESPONSE_NONE)

    def test_sort_by_parsed_datetime_not_string(self) -> None:
        # String sort would put "10:00" before "9:00"; datetime sort is chronological
        base = datetime(2026, 10, 7, 8, 0, tzinfo=timezone.utc)
        events = [
            {
                "summary": "Ten",
                "start": {"dateTime": (base + timedelta(hours=2)).isoformat()},
                "end": {"dateTime": (base + timedelta(hours=3)).isoformat()},
            },
            {
                "summary": "Nine",
                "start": {"dateTime": (base + timedelta(hours=1)).isoformat()},
                "end": {"dateTime": (base + timedelta(hours=2)).isoformat()},
            },
        ]

        def transport(method, url, **kwargs):
            safe = url.split("?")[0]
            if "token" in safe:
                return google_http.GoogleHttpResponse(
                    200, json.dumps({"access_token": "ya29.x", "expires_in": 3600})
                )
            if "calendarList" in safe:
                return google_http.GoogleHttpResponse(
                    200,
                    json.dumps(
                        {
                            "items": [
                                {
                                    "id": "primary",
                                    "summary": "Brian",
                                    "selected": True,
                                    "primary": True,
                                    "timeZone": "UTC",
                                }
                            ]
                        }
                    ),
                )
            if "/events" in safe:
                return google_http.GoogleHttpResponse(200, json.dumps({"items": events}))
            return google_http.GoogleHttpResponse(404, "{}")

        google_http.set_transport_for_tests(transport)
        with self._patch_turn_ctx():
            raw = gcal.calendar_query_handler(
                {
                    "order": "soonest",
                    "start": base.isoformat(),
                    "end": (base + timedelta(hours=5)).isoformat(),
                }
            )
        data = self._frame_json(raw)
        titles = [i["title"] for i in data["items"]]
        self.assertEqual(titles, ["Nine", "Ten"])

    def test_most_recent_chunk_search_and_page_cap_incomplete(self) -> None:
        now = datetime.now(timezone.utc)
        event_calls = {"n": 0}

        def transport(method, url, **kwargs):
            safe = url.split("?")[0]
            if "token" in safe:
                return google_http.GoogleHttpResponse(
                    200, json.dumps({"access_token": "ya29.x", "expires_in": 3600})
                )
            if "calendarList" in safe:
                return google_http.GoogleHttpResponse(
                    200,
                    json.dumps(
                        {
                            "items": [
                                {
                                    "id": "primary",
                                    "summary": "Brian",
                                    "selected": True,
                                    "primary": True,
                                    "timeZone": "America/Los_Angeles",
                                }
                            ]
                        }
                    ),
                )
            if "/events" in safe:
                event_calls["n"] += 1
                # Always claim another page → hit page cap → incomplete
                return google_http.GoogleHttpResponse(
                    200,
                    json.dumps(
                        {
                            "items": [
                                {
                                    "summary": f"E{event_calls['n']}",
                                    "start": {
                                        "dateTime": (
                                            now - timedelta(days=1, hours=event_calls["n"])
                                        ).isoformat()
                                    },
                                    "end": {
                                        "dateTime": (
                                            now
                                            - timedelta(days=1, hours=event_calls["n"] - 1)
                                        ).isoformat()
                                    },
                                }
                            ],
                            "nextPageToken": f"p{event_calls['n']}",
                        }
                    ),
                )
            return google_http.GoogleHttpResponse(404, "{}")

        google_http.set_transport_for_tests(transport)
        with self._patch_turn_ctx():
            raw = gcal.calendar_query_handler(
                {"order": "most_recent", "max_results": 3}
            )
        data = self._frame_json(raw)
        self.assertEqual(data["state"], gcal.STATE_INCOMPLETE)
        self.assertLessEqual(len(data["items"]), 3)
        # Multiple chunk/page fetches occurred
        self.assertGreaterEqual(event_calls["n"], gcal.MAX_PAGES_PER_CALENDAR)

    def test_most_recent_stops_at_max_results(self) -> None:
        now = datetime.now(timezone.utc)
        # One event in the most recent 30-day window is enough
        events_by_window: List[str] = []

        def transport(method, url, **kwargs):
            safe = url.split("?")[0]
            params = kwargs.get("params") or {}
            if "token" in safe:
                return google_http.GoogleHttpResponse(
                    200, json.dumps({"access_token": "ya29.x", "expires_in": 3600})
                )
            if "calendarList" in safe:
                return google_http.GoogleHttpResponse(
                    200,
                    json.dumps(
                        {
                            "items": [
                                {
                                    "id": "primary",
                                    "summary": "Brian",
                                    "selected": True,
                                    "primary": True,
                                    "timeZone": "America/Los_Angeles",
                                }
                            ]
                        }
                    ),
                )
            if "/events" in safe:
                events_by_window.append(str(params.get("timeMin") or ""))
                return google_http.GoogleHttpResponse(
                    200,
                    json.dumps(
                        {
                            "items": [
                                {
                                    "summary": "Recent",
                                    "start": {
                                        "dateTime": (now - timedelta(hours=2)).isoformat()
                                    },
                                    "end": {
                                        "dateTime": (now - timedelta(hours=1)).isoformat()
                                    },
                                }
                            ]
                        }
                    ),
                )
            return google_http.GoogleHttpResponse(404, "{}")

        google_http.set_transport_for_tests(transport)
        with self._patch_turn_ctx():
            raw = gcal.calendar_query_handler(
                {"order": "most_recent", "max_results": 1}
            )
        data = self._frame_json(raw)
        self.assertEqual(data["state"], gcal.STATE_COMPLETE)
        self.assertEqual(len(data["items"]), 1)
        # Should stop after first chunk that fills max_results (one window fetch)
        self.assertEqual(len(events_by_window), 1)

    def test_most_recent_dedupes_multiday_across_chunks(self) -> None:
        """Multi-day event spanning a chunk boundary appears once toward max_results."""
        now = datetime.now(timezone.utc)
        # Spans across the 30-day chunk boundary so both windows return it
        multi = {
            "id": "evt-multi-day",
            "summary": "MultiDaySpan",
            "start": {"dateTime": (now - timedelta(days=35)).isoformat()},
            "end": {"dateTime": (now - timedelta(days=25)).isoformat()},
        }
        windows_hit: List[str] = []

        def transport(method, url, **kwargs):
            safe = url.split("?")[0]
            params = kwargs.get("params") or {}
            if "token" in safe:
                return google_http.GoogleHttpResponse(
                    200, json.dumps({"access_token": "ya29.x", "expires_in": 3600})
                )
            if "calendarList" in safe:
                return google_http.GoogleHttpResponse(
                    200,
                    json.dumps(
                        {
                            "items": [
                                {
                                    "id": "primary",
                                    "summary": "Brian",
                                    "selected": True,
                                    "primary": True,
                                    "timeZone": "America/Los_Angeles",
                                }
                            ]
                        }
                    ),
                )
            if "/events" in safe:
                tmin = str(params.get("timeMin") or "")
                tmax = str(params.get("timeMax") or "")
                windows_hit.append(f"{tmin}|{tmax}")
                # Overlap check: return multi-day event whenever window overlaps it
                ev_start = now - timedelta(days=35)
                ev_end = now - timedelta(days=25)
                try:
                    w_start = datetime.fromisoformat(tmin.replace("Z", "+00:00"))
                    w_end = datetime.fromisoformat(tmax.replace("Z", "+00:00"))
                except Exception:
                    w_start, w_end = now - timedelta(days=730), now
                items = []
                if ev_start < w_end and ev_end > w_start:
                    items.append(multi)
                return google_http.GoogleHttpResponse(
                    200, json.dumps({"items": items})
                )
            return google_http.GoogleHttpResponse(404, "{}")

        google_http.set_transport_for_tests(transport)
        with self._patch_turn_ctx():
            raw = gcal.calendar_query_handler(
                {
                    "order": "most_recent",
                    "max_results": 5,
                    "start": (now - timedelta(days=70)).isoformat(),
                    "end": now.isoformat(),
                }
            )
        data = self._frame_json(raw)
        titles = [i["title"] for i in data["items"]]
        self.assertEqual(titles.count("MultiDaySpan"), 1)
        self.assertEqual(len(data["items"]), 1)
        # Must have searched more than one chunk (otherwise no boundary to span)
        self.assertGreaterEqual(len(windows_hit), 2)


class SourceScanTests(SocketGuardMixin, unittest.TestCase):
    def test_no_google_http_outside_google_http(self) -> None:
        banned = re.compile(
            r"^\s*(import\s+(requests|httpx)|from\s+(requests|httpx)\s+import)",
            re.M,
        )
        offenders = []
        for path in PLUGIN_ROOT.glob("*.py"):
            if path.name == "google_http.py":
                continue
            text = path.read_text(encoding="utf-8")
            if banned.search(text):
                offenders.append(path.name)
            # urllib.request for OAuth browser callback is ok only in tests
            if path.name != "auth.py" and "urllib.request" in text:
                offenders.append(path.name + ":urllib")
        self.assertEqual(offenders, [])


class ConsolidateAttributionTests(SocketGuardMixin, unittest.TestCase):
    def test_attribution_when_tainted_or_import_fails(self) -> None:
        mem_root = PLUGINS_ROOT / "zola_memory"
        if str(mem_root) not in sys.path:
            sys.path.insert(0, str(mem_root))
        import consolidate as cons

        class FakeRow(dict):
            def __getitem__(self, key):
                return dict.__getitem__(self, key)

        rows = [FakeRow(session_id="sess-attr")]

        with mock.patch.object(cons, "_zola_workspace_plugin_enabled", return_value=True):
            with tempfile.TemporaryDirectory() as td:
                path = Path(td) / "taint.sqlite"
                taint.set_store_path_for_tests(path)
                taint.mark_tainted("sess-attr")
                text = cons.summarizer_instructions_for(rows)  # type: ignore[arg-type]
                self.assertIn(cons.WORKSPACE_ATTRIBUTION_LINE, text)
                taint.reset_store_path_for_tests()

        with mock.patch.object(cons, "_zola_workspace_plugin_enabled", return_value=False):
            text2 = cons.summarizer_instructions_for(rows)  # type: ignore[arg-type]
            self.assertIn(cons.WORKSPACE_ATTRIBUTION_LINE, text2)

        with mock.patch.object(cons, "_zola_workspace_plugin_enabled", return_value=True):
            with mock.patch.dict(sys.modules, {"hermes_plugins.zola_workspace.taint": None}):
                # Force import failure path via patching the import inside
                real_needs = cons._needs_workspace_attribution

                def boom(rows_arg):
                    try:
                        raise ImportError("forced")
                    except Exception:
                        return True

                with mock.patch.object(cons, "_needs_workspace_attribution", side_effect=lambda r: True):
                    text3 = cons.summarizer_instructions_for(rows)  # type: ignore[arg-type]
                self.assertIn(cons.WORKSPACE_ATTRIBUTION_LINE, text3)


class LoadOrderTests(SocketGuardMixin, unittest.TestCase):
    def test_taint_importable_as_hermes_plugins(self) -> None:
        from hermes_plugins.zola_workspace.taint import is_tainted

        self.assertFalse(is_tainted("no-such-session-load-order"))


if __name__ == "__main__":
    unittest.main()
