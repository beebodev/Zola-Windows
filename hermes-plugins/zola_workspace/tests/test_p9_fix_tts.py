"""P9-FIX-TTS: key-path and live zola-tts script guard rows."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

_PLUGIN = Path(__file__).resolve().parents[1]
if str(_PLUGIN) not in sys.path:
    sys.path.insert(0, str(_PLUGIN))

import guards  # noqa: E402

_KEY = r"C:\Users\test\AppData\Local\ZolaClient\secrets\deepgram_api_key"
_KEY_FWD = "C:/Users/test/AppData/Local/ZolaClient/secrets/deepgram_api_key"
_KEY_ENV = r"%LOCALAPPDATA%\ZolaClient\secrets\deepgram_api_key"
_SCRIPT = r"C:\Users\test\AppData\Local\hermes\profiles\zola\zola-tts\deepgram_tts.py"
_SCRIPT_FWD = "C:/Users/test/AppData/Local/hermes/profiles/zola/zola-tts/deepgram_tts.py"


class DeepgramGuardTests(unittest.TestCase):
    def _block(self, tool: str, args: dict, message: str) -> None:
        result = guards.evaluate_deepgram_key(tool, args)
        self.assertIsNotNone(result)
        self.assertEqual(result["action"], "block")
        self.assertEqual(result["message"], message)

    def test_key_folder_blocks_terminal_read_write_and_patch(self) -> None:
        message = guards.BLOCK_MESSAGE_DEEPGRAM_KEY
        self._block("terminal", {"command": f"Get-Content '{_KEY}'"}, message)
        self._block("terminal", {"command": f"Get-Content '{_KEY_ENV}'"}, message)
        self._block("terminal", {"command": f"type {_KEY_FWD}"}, message)
        self._block("terminal", {"command": r"Get-Content ZOLACLIENT\SECRETS\deepgram_api_key"}, message)
        self._block("read_file", {"path": _KEY}, message)
        self._block("read_file", {"path": _KEY_FWD}, message)
        self._block("write_file", {"path": _KEY, "content": "x"}, message)
        self._block("patch", {"path": _KEY_FWD, "patch": "x"}, message)

    def test_key_file_name_blocks_without_the_folder(self) -> None:
        self._block(
            "terminal",
            {"command": "Get-Content .\\deepgram_api_key"},
            guards.BLOCK_MESSAGE_DEEPGRAM_KEY,
        )
        self._block(
            "read_file",
            {"path": "deepgram_api_key"},
            guards.BLOCK_MESSAGE_DEEPGRAM_KEY,
        )

    def test_script_dir_blocks_write_patch_and_terminal(self) -> None:
        message = guards.BLOCK_MESSAGE_TTS_SCRIPT
        self._block("write_file", {"path": _SCRIPT, "content": "x"}, message)
        self._block("patch", {"path": _SCRIPT_FWD, "patch": "x"}, message)
        self._block(
            "terminal",
            {"command": f"Set-Content '{_SCRIPT}' -Value 'x'"},
            message,
        )
        self._block(
            "terminal",
            {"command": f"Get-Content '{_SCRIPT_FWD}'"},
            message,
        )

    def test_script_read_file_stays_allowed(self) -> None:
        self.assertIsNone(guards.evaluate_deepgram_key("read_file", {"path": _SCRIPT}))
        self.assertIsNone(guards.evaluate_deepgram_key("read_file", {"path": _SCRIPT_FWD}))

    def test_residuals_are_not_blocked(self) -> None:
        # Encoded path, another tool, a glob, a variable, and a junction whose
        # command text does not name the folder or the key file.
        cases = (
            ("terminal", {"command": "python -c \"exec(__import__('base64').b64decode('cHJpbnQoMSk='))\""}),
            ("execute_code", {"code": f"open(r'{_KEY}').read()"}),
            ("terminal", {"command": r"Get-ChildItem $env:LOCALAPPDATA\Zola*"}),
            ("terminal", {"command": "Get-Content $p"}),
            ("terminal", {"command": r"Get-Content Z:\k", "workdir": _SCRIPT}),
            ("write_file", {"path": r"C:\Users\test\Dev\hermes-plugins\zola_tts\deepgram_tts.py", "content": "x"}),
        )
        for tool, args in cases:
            self.assertIsNone(guards.evaluate_deepgram_key(tool, args), tool)

    def test_hook_wires_both_rows(self) -> None:
        key = guards.pre_tool_call_hook(tool_name="read_file", args={"path": _KEY})
        self.assertEqual(key["action"], "block")
        self.assertEqual(key["message"], guards.BLOCK_MESSAGE_DEEPGRAM_KEY)
        script = guards.pre_tool_call_hook(tool_name="write_file", args={"path": _SCRIPT, "content": "x"})
        self.assertEqual(script["message"], guards.BLOCK_MESSAGE_TTS_SCRIPT)
        allowed = guards.pre_tool_call_hook(tool_name="read_file", args={"path": _SCRIPT})
        self.assertIsNone(allowed)

    def test_hook_fail_closed_when_the_evaluator_raises(self) -> None:
        with mock.patch.object(guards, "evaluate_deepgram_key", side_effect=RuntimeError("boom")):
            key = guards.pre_tool_call_hook(tool_name="read_file", args={"path": _KEY})
            script = guards.pre_tool_call_hook(
                tool_name="terminal", args={"command": f"Set-Content '{_SCRIPT}' -Value x"}
            )
        self.assertEqual(key["message"], guards.BLOCK_MESSAGE_DEEPGRAM_KEY)
        self.assertEqual(script["message"], guards.BLOCK_MESSAGE_TTS_SCRIPT)
        with mock.patch.object(guards, "evaluate_deepgram_key", side_effect=RuntimeError("boom")):
            allowed = guards.pre_tool_call_hook(tool_name="read_file", args={"path": _SCRIPT})
        self.assertIsNone(allowed)
