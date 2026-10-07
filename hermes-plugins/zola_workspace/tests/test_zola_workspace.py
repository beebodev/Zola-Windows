"""P8-HARDEN unit tests for zola_workspace (P8-D01 / P8-D02)."""

from __future__ import annotations

import contextvars
import importlib.util
import json
import socket
import sys
import time
import unittest
from pathlib import Path
from unittest import mock

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

import guards  # noqa: E402
import posture  # noqa: E402
import turn_context  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "zola_workspace_init",
    PLUGIN_ROOT / "__init__.py",
)
assert _spec is not None and _spec.loader is not None
plugin = importlib.util.module_from_spec(_spec)
sys.modules["zola_workspace_init"] = plugin
_spec.loader.exec_module(plugin)

SYN_CONFIG = r"C:\Users\test\AppData\Local\hermes\profiles\zola\config.yaml"
SYN_ENV = r"C:\Users\test\AppData\Local\hermes\profiles\zola\.env"
SYN_PROFILE = r"C:\Users\test\AppData\Local\hermes\profiles\zola"
SYN_OTHER = r"C:\Users\test\AppData\Local\hermes\profiles\zola\memories\note.txt"


class TurnContextTests(unittest.TestCase):
    def setUp(self) -> None:
        turn_context.clear_all_for_tests()

    def tearDown(self) -> None:
        turn_context.clear_all_for_tests()

    def test_01_same_turn_found(self) -> None:
        turn_context.record_pre_llm_call(
            turn_id="turn-a",
            task_id="sess",
            session_id="sess",
            platform="tui",
            parent_session_id="",
            user_message="synthetic A",
        )
        self.assertTrue(turn_context.is_brian_turn("turn-a"))

    def test_02_other_turn_same_session_not_confused_with_newest(self) -> None:
        turn_context.record_pre_llm_call(
            turn_id="turn-a",
            task_id="sess",
            session_id="sess",
            platform="tui",
            user_message="synthetic A",
        )
        time.sleep(0.01)
        turn_context.record_pre_llm_call(
            turn_id="turn-b",
            task_id="sess",
            session_id="sess",
            platform="tui",
            user_message="synthetic B",
        )
        with mock.patch.object(
            turn_context, "current_turn_id_from_context", return_value="turn-a"
        ):
            self.assertTrue(turn_context.is_brian_turn())
            rec = turn_context.get_record("turn-a")
            self.assertIsNotNone(rec)
            assert rec is not None
            self.assertEqual(rec.user_message, "synthetic A")
        self.assertFalse(turn_context.is_brian_turn("turn-other"))
        self.assertFalse(hasattr(turn_context, "latest_for_session"))
        self.assertFalse(hasattr(turn_context, "_by_session"))
        self.assertFalse(hasattr(turn_context, "_current_by_session"))

    def test_03_missing_turn_id(self) -> None:
        self.assertFalse(turn_context.is_brian_turn(""))
        self.assertFalse(turn_context.is_brian_turn("missing"))

    def test_04_expired_ttl(self) -> None:
        turn_context.record_pre_llm_call(
            turn_id="turn-old",
            task_id="sess",
            session_id="sess",
            platform="tui",
            user_message="synthetic",
        )
        rec = turn_context._records_by_turn_id["turn-old"]
        turn_context._records_by_turn_id["turn-old"] = turn_context.TurnRecord(
            turn_id=rec.turn_id,
            task_id=rec.task_id,
            session_id=rec.session_id,
            platform=rec.platform,
            parent_session_id=rec.parent_session_id,
            user_message=rec.user_message,
            created_at=time.monotonic() - turn_context.AUTHORITY_GRANT_TTL_SECONDS - 1,
        )
        self.assertFalse(turn_context.is_brian_turn("turn-old"))

    def test_05_wrong_platform(self) -> None:
        turn_context.record_pre_llm_call(
            turn_id="turn-x",
            platform="cron",
            parent_session_id="",
            user_message="synthetic",
        )
        self.assertFalse(turn_context.is_brian_turn("turn-x"))

    def test_06_nonempty_parent(self) -> None:
        turn_context.record_pre_llm_call(
            turn_id="turn-x",
            platform="tui",
            parent_session_id="parent-sess",
            user_message="synthetic",
        )
        self.assertFalse(turn_context.is_brian_turn("turn-x"))

    def test_07_restart_fresh_module(self) -> None:
        turn_context.record_pre_llm_call(
            turn_id="turn-x",
            platform="tui",
            user_message="synthetic",
        )
        turn_context.clear_all_for_tests()
        self.assertFalse(turn_context.is_brian_turn("turn-x"))

    def test_19_approval_turn_id_contextvar(self) -> None:
        try:
            from tools import approval_context
        except Exception as exc:  # pragma: no cover
            self.fail(
                "Hermes private dependency missing: tools.approval_context "
                f"(_approval_turn_id ContextVar) — {exc!r}"
            )
        if not hasattr(approval_context, "_approval_turn_id"):
            self.fail(
                "Hermes private dependency missing or renamed: "
                "tools.approval_context._approval_turn_id"
            )
        cv = approval_context._approval_turn_id
        if not isinstance(cv, contextvars.ContextVar):
            self.fail(
                "Hermes private dependency tools.approval_context._approval_turn_id "
                f"is not a ContextVar (got {type(cv)!r})"
            )


class GuardTests(unittest.TestCase):
    def _block(self, tool: str, args: dict) -> bool:
        result = guards.evaluate_config_self_edit(tool, args)
        return result is not None and result.get("action") == "block"

    def test_08_blocks_file_and_terminal_rows(self) -> None:
        cases = [
            ("write_file", {"path": SYN_CONFIG, "content": "x"}),
            ("write_file", {"path": "config.yaml", "content": "x"}),
            ("write_file", {"path": SYN_ENV, "content": "x"}),
            ("write_file", {"path": ".env", "content": "x"}),
            ("patch", {"path": SYN_CONFIG, "old_string": "a", "new_string": "b"}),
            (
                "patch",
                {
                    "mode": "patch",
                    "patch": "*** Update File: profiles/zola/config.yaml\n@@\n-a\n+b\n",
                },
            ),
            ("terminal", {"command": f'Set-Content -Path "{SYN_CONFIG}" -Value "x"'}),
            ("terminal", {"command": f'Remove-Item -Path "{SYN_CONFIG}"'}),
            ("terminal", {"command": f'Rename-Item "{SYN_CONFIG}" config.bak'}),
            ("terminal", {"command": f'del "{SYN_CONFIG}"'}),
            ("terminal", {"command": f'Copy-Item evil.yaml "{SYN_CONFIG}"'}),
            ("terminal", {"command": f'Set-Content -Path "{SYN_ENV}" -Value "x"'}),
            ("terminal", {"command": "hermes config set approvals.mode off"}),
            (
                "terminal",
                {"command": "Set-Content config.yaml x", "workdir": SYN_PROFILE},
            ),
            (
                "terminal",
                {"command": "Remove-Item .env", "workdir": SYN_PROFILE},
            ),
            ("terminal", {"command": r"Set-Content D:\other\config.yaml x"}),
            ("terminal", {"command": r"echo x > CONFIG~1.YAM"}),
            # Claude review: cmd copy/move/xcopy/robocopy/rmdir/rd; PS aliases; > without space
            ("terminal", {"command": r"copy evil.yaml config.yaml"}),
            ("terminal", {"command": r"move config.yaml config.bak"}),
            ("terminal", {"command": r"xcopy config.yaml D:\backup"}),
            ("terminal", {"command": r"robocopy . D:\bak config.yaml"}),
            ("terminal", {"command": r"rmdir config.yaml"}),
            ("terminal", {"command": r"rd .env"}),
            ("terminal", {"command": r"sc config.yaml x"}),
            ("terminal", {"command": r"ac .env x"}),
            ("terminal", {"command": r"ni config.yaml"}),
            ("terminal", {"command": r"ri config.yaml"}),
            ("terminal", {"command": r"rni config.yaml config.bak"}),
            ("terminal", {"command": r"mi config.yaml D:\other"}),
            ("terminal", {"command": r"cpi evil.yaml config.yaml"}),
            ("terminal", {"command": r"echo x>config.yaml"}),
            ("terminal", {"command": r"echo x>>.env"}),
        ]
        for tool, args in cases:
            with self.subTest(tool=tool, args=args):
                self.assertTrue(self._block(tool, args), f"expected block for {tool} {args}")

    def test_09_allows_reads(self) -> None:
        allow_cases = [
            ("read_file", {"path": SYN_CONFIG}),
            ("terminal", {"command": f'Get-Content "{SYN_CONFIG}"'}),
            ("terminal", {"command": f'type "{SYN_CONFIG}"'}),
            ("terminal", {"command": f'Get-Content "{SYN_ENV}"'}),
        ]
        for tool, args in allow_cases:
            with self.subTest(tool=tool, args=args):
                self.assertFalse(self._block(tool, args), f"expected allow for {tool}")

    def test_10_inert_stubs_allow(self) -> None:
        self.assertIsNone(guards.memory_taint_stub(tool_name="memory", args={}))
        self.assertIsNone(guards.terminal_google_stub(tool_name="terminal", args={"command": "x"}))
        self.assertFalse(guards.GUARD_MEMORY_TAINT_ENABLED)
        self.assertFalse(guards.GUARD_TERMINAL_GOOGLE_ENABLED)

    def test_20_delete_env_and_other_profile_file(self) -> None:
        self.assertTrue(
            self._block("terminal", {"command": f'Remove-Item "{SYN_CONFIG}"'})
        )
        self.assertTrue(
            self._block("terminal", {"command": f'Rename-Item "{SYN_CONFIG}" x.yaml'})
        )
        self.assertTrue(self._block("write_file", {"path": SYN_ENV, "content": "x"}))
        self.assertFalse(
            self._block("write_file", {"path": SYN_OTHER, "content": "note"})
        )
        self.assertFalse(
            self._block(
                "terminal",
                {"command": f'Set-Content -Path "{SYN_OTHER}" -Value "note"'},
            )
        )


class PostureTests(unittest.TestCase):
    def test_11_modes(self) -> None:
        with mock.patch.object(posture, "_read_approval_mode", return_value="manual"), mock.patch.object(
            posture, "_yolo_env_frozen", return_value=False
        ), mock.patch.object(posture, "_yolo_session", return_value=False):
            self.assertTrue(posture.posture_ok())
        with mock.patch.object(posture, "_read_approval_mode", return_value="off"), mock.patch.object(
            posture, "_yolo_env_frozen", return_value=False
        ), mock.patch.object(posture, "_yolo_session", return_value=False):
            self.assertFalse(posture.posture_ok())
        with mock.patch.object(posture, "_read_approval_mode", return_value="smart"), mock.patch.object(
            posture, "_yolo_env_frozen", return_value=False
        ), mock.patch.object(posture, "_yolo_session", return_value=False):
            self.assertFalse(posture.posture_ok())

    def test_12_yolo_env(self) -> None:
        with mock.patch.object(posture, "_read_approval_mode", return_value="manual"), mock.patch.object(
            posture, "_yolo_env_frozen", return_value=True
        ), mock.patch.object(posture, "_yolo_session", return_value=False):
            self.assertFalse(posture.posture_ok())

    def test_13_yolo_session(self) -> None:
        with mock.patch.object(posture, "_read_approval_mode", return_value="manual"), mock.patch.object(
            posture, "_yolo_env_frozen", return_value=False
        ), mock.patch.object(posture, "_yolo_session", return_value=True):
            self.assertFalse(posture.posture_ok())


class WorkspaceStatusTests(unittest.TestCase):
    def setUp(self) -> None:
        turn_context.clear_all_for_tests()

    def tearDown(self) -> None:
        turn_context.clear_all_for_tests()

    def test_14_brian_turn_allowed(self) -> None:
        # Use the same turn_context module object the plugin bound
        tc = plugin.turn_context
        tc.clear_all_for_tests()
        tc.record_pre_llm_call(
            turn_id="turn-brian",
            platform="tui",
            parent_session_id="",
            user_message="synthetic",
        )
        with mock.patch.object(plugin.posture, "posture_ok", return_value=True):
            with mock.patch.object(
                tc, "current_turn_id_from_context", return_value="turn-brian"
            ):
                raw = plugin.workspace_status_handler({})
        data = json.loads(raw)
        self.assertTrue(data["ok"])
        self.assertFalse(data["connected"])
        self.assertTrue(data["allowed_here"])
        self.assertTrue(data["posture_ok"])

    def test_15_non_brian_false(self) -> None:
        tc = plugin.turn_context
        tc.clear_all_for_tests()
        tc.record_pre_llm_call(
            turn_id="turn-cron",
            platform="cron",
            parent_session_id="",
            user_message="synthetic",
        )
        with mock.patch.object(plugin.posture, "posture_ok", return_value=True):
            with mock.patch.object(
                tc, "current_turn_id_from_context", return_value="turn-cron"
            ):
                raw = plugin.workspace_status_handler({})
        data = json.loads(raw)
        self.assertFalse(data["allowed_here"])
        self.assertFalse(data["connected"])

    def test_16_no_socket(self) -> None:
        tc = plugin.turn_context
        tc.clear_all_for_tests()
        tc.record_pre_llm_call(
            turn_id="turn-brian",
            platform="tui",
            user_message="synthetic",
        )

        class BoomSocket(socket.socket):
            def __init__(self, *a, **k):
                raise AssertionError("workspace_status must not open a socket")

        with mock.patch.object(plugin.posture, "posture_ok", return_value=True):
            with mock.patch.object(
                tc, "current_turn_id_from_context", return_value="turn-brian"
            ):
                with mock.patch("socket.socket", BoomSocket):
                    raw = plugin.workspace_status_handler({})
        data = json.loads(raw)
        self.assertTrue(data["ok"])


class RegisterTests(unittest.TestCase):
    def test_register_sync_tool(self) -> None:
        seen = {}

        class FakeCtx:
            def register_hook(self, name, fn):
                seen.setdefault("hooks", []).append(name)

            def register_tool(self, **kwargs):
                seen["tool"] = kwargs

        plugin.register(FakeCtx())
        self.assertIn("pre_llm_call", seen["hooks"])
        self.assertIn("pre_tool_call", seen["hooks"])
        self.assertEqual(seen["tool"]["name"], "workspace_status")
        self.assertEqual(seen["tool"]["toolset"], "zola_workspace")
        self.assertFalse(seen["tool"]["is_async"])


class HookBlockMessageTests(unittest.TestCase):
    def test_hook_returns_block_message(self) -> None:
        result = guards.pre_tool_call_hook(
            tool_name="write_file",
            args={"path": SYN_CONFIG, "content": "x"},
        )
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["action"], "block")
        self.assertEqual(result["message"], guards.BLOCK_MESSAGE_CONFIG_OR_ENV)


class ClaudeReviewPhase4Tests(unittest.TestCase):
    """Claude review fixes (Phase 4) — tests 21–25."""

    def setUp(self) -> None:
        turn_context.clear_all_for_tests()
        plugin.turn_context.clear_all_for_tests()

    def tearDown(self) -> None:
        turn_context.clear_all_for_tests()
        plugin.turn_context.clear_all_for_tests()

    def test_21_posture_hermes_private_deps(self) -> None:
        try:
            from tools import approval
            from tools import approval_context
        except Exception as exc:  # pragma: no cover
            self.fail(f"Hermes private dependency import failed — {exc!r}")
        if not hasattr(approval, "_YOLO_MODE_FROZEN"):
            self.fail(
                "Hermes private dependency missing or renamed: "
                "tools.approval._YOLO_MODE_FROZEN"
            )
        if not hasattr(approval, "is_current_session_yolo_enabled"):
            self.fail(
                "Hermes private dependency missing or renamed: "
                "tools.approval.is_current_session_yolo_enabled"
            )
        if not hasattr(approval_context, "_get_approval_mode"):
            self.fail(
                "Hermes private dependency missing or renamed: "
                "tools.approval_context._get_approval_mode"
            )

    def test_22_posture_readers_raise_fail_closed(self) -> None:
        with mock.patch.object(
            posture, "_read_approval_mode", side_effect=RuntimeError("mode boom")
        ):
            ok, reason = posture.posture_detail()
            self.assertFalse(ok)
            self.assertEqual(reason, posture.REASON_MODE_UNREADABLE)
            self.assertFalse(posture.posture_ok())
        with mock.patch.object(
            posture, "_read_approval_mode", return_value="manual"
        ), mock.patch.object(
            posture, "_yolo_env_frozen", side_effect=RuntimeError("yolo env boom")
        ):
            ok, reason = posture.posture_detail()
            self.assertFalse(ok)
            self.assertEqual(reason, posture.REASON_YOLO_ENV_UNREADABLE)
            self.assertFalse(posture.posture_ok())
        with mock.patch.object(
            posture, "_read_approval_mode", return_value="manual"
        ), mock.patch.object(
            posture, "_yolo_env_frozen", return_value=False
        ), mock.patch.object(
            posture, "_yolo_session", side_effect=RuntimeError("yolo sess boom")
        ):
            ok, reason = posture.posture_detail()
            self.assertFalse(ok)
            self.assertEqual(reason, posture.REASON_YOLO_SESSION_UNREADABLE)
            self.assertFalse(posture.posture_ok())

    def test_23_workspace_status_real_contextvar_path(self) -> None:
        from tools.approval_context import (
            reset_current_observability_context,
            set_current_observability_context,
        )

        tc = plugin.turn_context
        tc.clear_all_for_tests()
        turn_id = "turn-real-ctx-001"
        tc.record_pre_llm_call(
            turn_id=turn_id,
            platform="tui",
            parent_session_id="",
            user_message="synthetic",
        )
        tokens = set_current_observability_context(
            turn_id=turn_id, tool_call_id="call-1", session_id="sess-1"
        )
        try:
            with mock.patch.object(plugin.posture, "posture_ok", return_value=True):
                # turn_id only in kwargs must be ignored
                raw = plugin.workspace_status_handler(
                    {}, turn_id="kwargs-only-must-be-ignored"
                )
            data = json.loads(raw)
            self.assertTrue(data["allowed_here"], data)
        finally:
            reset_current_observability_context(tokens)

        with mock.patch.object(plugin.posture, "posture_ok", return_value=True):
            raw2 = plugin.workspace_status_handler(
                {}, turn_id="kwargs-only-must-be-ignored"
            )
        data2 = json.loads(raw2)
        self.assertFalse(data2["allowed_here"], data2)

    def test_24_guard_error_path(self) -> None:
        with mock.patch.object(
            guards, "evaluate_config_self_edit", side_effect=RuntimeError("boom")
        ):
            blocked = guards.pre_tool_call_hook(
                tool_name="write_file",
                args={"path": "config.yaml", "content": "x"},
            )
            self.assertIsNotNone(blocked)
            assert blocked is not None
            self.assertEqual(blocked["action"], "block")
            self.assertEqual(blocked["message"], guards.BLOCK_MESSAGE_CONFIG_OR_ENV)

            allowed = guards.pre_tool_call_hook(
                tool_name="write_file",
                args={"path": SYN_OTHER, "content": "note"},
            )
            self.assertIsNone(allowed)

            allowed_term = guards.pre_tool_call_hook(
                tool_name="terminal",
                args={"command": "echo hello"},
            )
            self.assertIsNone(allowed_term)

    def test_25_prune_expired_on_insert(self) -> None:
        tc = turn_context
        tc.clear_all_for_tests()
        tc.record_pre_llm_call(
            turn_id="turn-old",
            platform="tui",
            user_message="synthetic old",
        )
        old = tc._records_by_turn_id["turn-old"]
        tc._records_by_turn_id["turn-old"] = tc.TurnRecord(
            turn_id=old.turn_id,
            task_id=old.task_id,
            session_id=old.session_id,
            platform=old.platform,
            parent_session_id=old.parent_session_id,
            user_message=old.user_message,
            created_at=time.monotonic() - tc.AUTHORITY_GRANT_TTL_SECONDS - 1,
        )
        self.assertIn("turn-old", tc._records_by_turn_id)
        tc.record_pre_llm_call(
            turn_id="turn-new",
            platform="tui",
            user_message="synthetic new",
        )
        self.assertNotIn("turn-old", tc._records_by_turn_id)
        self.assertIn("turn-new", tc._records_by_turn_id)


if __name__ == "__main__":
    unittest.main()
