"""P9-FIX-TTS: Deepgram command script. Fake key only. No network."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import textwrap
import unittest
import urllib.error
from email.message import Message
from pathlib import Path
from unittest import mock

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import deepgram_tts as tts  # noqa: E402

_FAKE_KEY = "unit-test-key-value"
_TEXT = "UNITTEXTMARKER morning meetings."
_REAL_KEY = r"C:\Users\test\AppData\Local\ZolaClient\secrets\deepgram_api_key"


class _Body:
    def __init__(self, data: bytes) -> None:
        self._data = data

    def read(self) -> bytes:
        return self._data

    def __enter__(self) -> "_Body":
        return self

    def __exit__(self, *args: object) -> bool:
        return False


class DeepgramTtsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.root = Path(self._dir.name)
        self.key_path = self.root / "deepgram_api_key"
        self.key_path.write_text(_FAKE_KEY + "\n", encoding="utf-8")
        self.input_path = self.root / "in.txt"
        self.output_path = self.root / "out" / "clip.mp3"
        patcher = mock.patch.object(tts, "KEY_PATH", self.key_path)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.assertNotEqual(tts.KEY_PATH, Path(_REAL_KEY))

    def _argv(self, *extra: str) -> list[str]:
        return ["deepgram_tts.py", str(self.input_path), str(self.output_path), *extra]

    def _invoke(self, argv: list[str], opener=None):
        err = io.StringIO()
        out = io.StringIO()
        seen: list = []

        def _open(request, timeout=None):
            seen.append(request)
            if opener is None:
                raise AssertionError("urlopen called")
            return opener(request, timeout)

        with (
            mock.patch.object(sys, "argv", argv),
            mock.patch.object(sys, "stderr", err),
            mock.patch.object(sys, "stdout", out),
            mock.patch("urllib.request.urlopen", _open),
        ):
            try:
                tts.main()
                code = 0
            except SystemExit as exc:
                code = exc.code
        return code, out.getvalue(), err.getvalue(), seen

    def _assert_quiet(self, out: str, err: str) -> None:
        blob = out + err
        self.assertNotIn(_FAKE_KEY, blob)
        self.assertNotIn(_TEXT, blob)
        self.assertNotIn("UNITTEXTMARKER", blob)

    def _ok(self, data: bytes = b"ID3fake"):
        def opener(request, timeout=None):
            return _Body(data)

        return opener

    def test_source_keeps_the_live_key_path(self) -> None:
        source = Path(tts.__file__).read_text(encoding="utf-8")
        self.assertIn(_REAL_KEY, source)
        self.assertNotEqual(self.key_path, Path(_REAL_KEY))

    def test_model_accepts_pandora_and_refuses_the_rest(self) -> None:
        self.input_path.write_text(_TEXT, encoding="utf-8")
        code, out, err, seen = self._invoke(self._argv("aura-2-pandora-en", "0.95"), self._ok())
        self.assertEqual(code, 0)
        self.assertEqual(len(seen), 1)
        self.assertIn("model=aura-2-pandora-en", seen[0].full_url)
        self._assert_quiet(out, err)

        for model in ("flux-brittany-en", "aura-2-Pandora-en"):
            code, out, err, seen = self._invoke(self._argv(model, "0.95"))
            self.assertEqual(code, 1)
            self.assertEqual(err.strip(), "deepgram: ValueError")
            self.assertEqual(seen, [])
            self._assert_quiet(out, err)
        code, out, err, seen = self._invoke(self._argv())
        self.assertEqual(code, 1)
        self.assertEqual(err.strip(), "deepgram: ValueError")
        self.assertEqual(seen, [])

    def test_speed_default_ok_rounding_and_refusal(self) -> None:
        self.input_path.write_text(_TEXT, encoding="utf-8")
        code, out, err, seen = self._invoke(self._argv("aura-2-pandora-en"), self._ok())
        self.assertEqual(code, 0)
        self.assertNotIn("speed=", seen[0].full_url)
        self._assert_quiet(out, err)

        code, out, err, seen = self._invoke(self._argv("aura-2-pandora-en", ""), self._ok())
        self.assertEqual(code, 0)
        self.assertNotIn("speed=", seen[0].full_url)

        code, out, err, seen = self._invoke(self._argv("aura-2-pandora-en", "0.95"), self._ok())
        self.assertEqual(code, 0)
        self.assertIn("speed=0.95", seen[0].full_url)

        code, out, err, seen = self._invoke(self._argv("aura-2-pandora-en", "0.96"), self._ok())
        self.assertEqual(code, 0)
        self.assertIn("speed=0.95", seen[0].full_url)
        self.assertNotIn("speed=0.96", seen[0].full_url)

        if self.output_path.exists():
            self.output_path.unlink()
        for bad in ("0.5", "1.6"):
            code, out, err, seen = self._invoke(self._argv("aura-2-pandora-en", bad))
            self.assertEqual(code, 1)
            self.assertEqual(err.strip(), "deepgram: ValueError")
            self.assertEqual(seen, [])
            self.assertFalse(self.output_path.exists())

    def test_pack_splits_on_whitespace_and_refuses_an_unbreakable_run(self) -> None:
        sentence = ("word " * 600).strip() + "."
        self.assertGreater(len(sentence), 2000)
        err = io.StringIO()
        with mock.patch.object(sys, "stderr", err):
            chunks = tts.pack(sentence)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk) <= 2000 for chunk in chunks))
        self.assertEqual(err.getvalue(), "")

        err = io.StringIO()
        with mock.patch.object(sys, "stderr", err):
            with self.assertRaises(SystemExit) as caught:
                tts.pack("a" * 2001)
        self.assertEqual(caught.exception.code, 1)
        self.assertEqual(err.getvalue().strip(), "deepgram: ValueError")
        self.assertNotIn("a" * 50, err.getvalue())

    def test_http_errors_and_timeout_are_metadata_only(self) -> None:
        self.input_path.write_text(_TEXT, encoding="utf-8")
        for status in (401, 403, 429, 500):
            def opener(request, timeout=None, status=status):
                raise urllib.error.HTTPError(
                    request.full_url, status, "nope", Message(), None
                )

            code, out, err, seen = self._invoke(
                self._argv("aura-2-pandora-en", "0.95"), opener
            )
            self.assertEqual(code, 1)
            self.assertEqual(err.strip(), f"deepgram: http {status}")
            self.assertNotIn("nope", err)
            self._assert_quiet(out, err)
            self.assertFalse(self.output_path.exists())

        def timeout(request, timeout=None):
            raise TimeoutError("not-for-stderr")

        code, out, err, seen = self._invoke(self._argv("aura-2-pandora-en", "0.95"), timeout)
        self.assertEqual(code, 1)
        self.assertEqual(err.strip(), "deepgram: TimeoutError")
        self.assertNotIn("not-for-stderr", err)
        self._assert_quiet(out, err)
        self.assertFalse(self.output_path.exists())

    def test_uncaught_exception_prints_the_class_only(self) -> None:
        self.input_path.write_text(_TEXT, encoding="utf-8")
        source = Path(tts.__file__).read_text(encoding="utf-8")
        block = textwrap.dedent(source.split('if __name__ == "__main__":', 1)[1])
        err = io.StringIO()
        out = io.StringIO()

        def boom(text: str):
            raise RuntimeError(_FAKE_KEY + " " + _TEXT)

        with (
            mock.patch.object(tts, "pack", boom),
            mock.patch.object(sys, "argv", self._argv("aura-2-pandora-en", "0.95")),
            mock.patch.object(sys, "stderr", err),
            mock.patch.object(sys, "stdout", out),
        ):
            with self.assertRaises(SystemExit) as caught:
                exec(block, {"main": tts.main, "sys": sys})
        self.assertEqual(caught.exception.code, 1)
        self.assertEqual(err.getvalue().strip(), "deepgram: RuntimeError")
        self._assert_quiet(out.getvalue(), err.getvalue())
        self.assertFalse(self.output_path.exists())

    def test_success_writes_audio_and_hides_key_and_text(self) -> None:
        self.input_path.write_text(_TEXT, encoding="utf-8")
        code, out, err, seen = self._invoke(
            self._argv("aura-2-pandora-en", "0.95"), self._ok(b"mp3-bytes")
        )
        self.assertEqual(code, 0)
        self.assertEqual(self.output_path.read_bytes(), b"mp3-bytes")
        body = json.loads(seen[0].data.decode("utf-8"))
        self.assertEqual(body["text"], _TEXT)
        self.assertIn(_FAKE_KEY, seen[0].headers["Authorization"])
        self._assert_quiet(out, err)

    def test_key_file_with_and_without_bom(self) -> None:
        self.input_path.write_text(_TEXT, encoding="utf-8")
        self.key_path.write_bytes(b"\xef\xbb\xbf" + _FAKE_KEY.encode("utf-8") + b"\n")
        code, out, err, seen = self._invoke(
            self._argv("aura-2-pandora-en", "0.95"), self._ok()
        )
        self.assertEqual(code, 0)
        self.assertIn(_FAKE_KEY, seen[0].headers["Authorization"])
        self.assertNotIn("\ufeff", seen[0].headers["Authorization"])
        self._assert_quiet(out, err)

        self.output_path.unlink()
        self.key_path.write_bytes(_FAKE_KEY.encode("utf-8") + b"\n")
        code, out, err, seen = self._invoke(
            self._argv("aura-2-pandora-en", "0.95"), self._ok(b"plain")
        )
        self.assertEqual(code, 0)
        self.assertEqual(self.output_path.read_bytes(), b"plain")
        self._assert_quiet(out, err)
