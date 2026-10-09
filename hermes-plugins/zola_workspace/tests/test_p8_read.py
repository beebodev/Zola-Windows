"""P8-READ unit tests — Gmail, Drive, Contacts, guards, lineage (P8-D02/D07/D08/D09)."""

from __future__ import annotations

import base64
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

import auth  # noqa: E402
import contacts  # noqa: E402
import drive  # noqa: E402
import framing  # noqa: E402
import gcal  # noqa: E402
import gmail  # noqa: E402
import google_http  # noqa: E402
import guards  # noqa: E402
import log as wslog  # noqa: E402
import read_common  # noqa: E402
import taint  # noqa: E402
import textclean  # noqa: E402
import turn_context  # noqa: E402
from test_phase4_connect import _TempHome, _seed_brian_turn  # noqa: E402


def _unframe(raw: str) -> dict:
    if raw.startswith("<" + framing.DELIMITER_TOKEN):
        inner = raw.split("\n\n", 1)[1].rsplit("\n</" + framing.DELIMITER_TOKEN + ">", 1)[0]
        return json.loads(inner)
    return json.loads(raw)


def _b64(text: str, encoding: str = "utf-8") -> str:
    return base64.urlsafe_b64encode(text.encode(encoding)).decode("ascii").rstrip("=")


class _ReadHome(_TempHome):
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
        self._turn = mock.patch.object(
            turn_context, "current_turn_id_from_context", return_value="turn-brian"
        )
        self._turn.start()
        drive.set_pdf_runner_for_tests(None)

    def tearDown(self) -> None:
        drive.set_pdf_runner_for_tests(None)
        self._turn.stop()
        super().tearDown()

    def _log(self) -> str:
        path = self.home / "logs" / "zola_workspace.log"
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")


def _fake_dpapi():
    def protect(plain: bytes) -> bytes:
        return b"FAKE_DPAPI:" + plain

    def unprotect(blob: bytes) -> bytes:
        if not blob.startswith(b"FAKE_DPAPI:"):
            raise ValueError("bad_blob")
        return blob[len(b"FAKE_DPAPI:") :]

    return protect, unprotect


def _sessions(home: Path, rows) -> None:
    conn = __import__("sqlite3").connect(str(home / "state.db"))
    try:
        conn.execute("CREATE TABLE sessions (id TEXT PRIMARY KEY, parent_session_id TEXT)")
        for sid, parent in rows:
            conn.execute(
                "INSERT INTO sessions (id, parent_session_id) VALUES (?, ?)",
                (sid, parent),
            )
        conn.commit()
    finally:
        conn.close()


class TextCleanTests(unittest.TestCase):
    def test_each_hidden_case_removed(self) -> None:
        cases = {
            "script": "<p>keep</p><script>alert(1)</script>",
            "style": "<style>.x{color:red}</style><p>keep</p>",
            "head": "<head><title>nope</title></head><p>keep</p>",
            "comment": "<p>keep</p><!-- hide me -->",
            "hidden": "<p hidden>nope</p><p>keep</p>",
            "display": '<span style="display:none">nope</span><p>keep</p>',
            "visibility": '<span style="visibility: hidden">nope</span><p>keep</p>',
            "font": '<span style="font-size: 0px">nope</span><p>keep</p>',
            "opacity": '<span style="opacity:0">nope</span><p>keep</p>',
        }
        for name, html in cases.items():
            with self.subTest(name=name):
                text = textclean.html_to_visible_text(html)
                self.assertIn("keep", text)
                self.assertNotIn("nope", text)
                self.assertNotIn("alert", text)
                self.assertNotIn("hide me", text)

    def test_opacity_half_and_external_class_stay(self) -> None:
        html = '<p class="secret-sheet">shown</p><span style="opacity:0.5">half</span>'
        text = textclean.html_to_visible_text(html)
        self.assertIn("shown", text)
        self.assertIn("half", text)
        wrapped = framing.frame_untrusted("gmail_read", text)
        self.assertIn(framing.FRAMING_INTRO, wrapped)
        self.assertIn("shown", wrapped)

    def test_quote_and_signature_trimmed_then_capped(self) -> None:
        html = (
            "<p>hello</p>"
            '<div class="gmail_quote">quoted block</div>'
            "<p>&gt; already</p>"
        )
        body = textclean.html_to_visible_text(html) + "\nOn Monday wrote:\n-- \nSig"
        # The html path drops gmail_quote. Plain trim drops > lines, On wrote, signature.
        plain = "hello\n> quoted\nOn Monday wrote:\nkeep\n-- \nSig"
        trimmed = textclean.trim_quotes(plain)
        self.assertEqual(trimmed, "hello\nkeep")
        self.assertNotIn("quoted block", textclean.html_to_visible_text(html))
        long = "x" * (textclean.BODY_CHAR_CAP + 10)
        excerpt, truncated, total = textclean.cap_text(long)
        self.assertTrue(truncated)
        self.assertEqual(len(excerpt), textclean.BODY_CHAR_CAP)
        self.assertEqual(total, textclean.BODY_CHAR_CAP + 10)
    def test_realistic_email_head_and_void_meta(self) -> None:
        html = (
            "<html><head><meta charset=\"utf-8\"><title>Subject line</title>"
            "<style>p{color:red}</style></head><body><p>visible body</p></body></html>"
        )
        text = textclean.html_to_visible_text(html)
        self.assertIn("visible body", text)
        self.assertNotIn("Subject line", text)
        self.assertNotIn("color", text)

    def test_br_inside_hidden_span_does_not_hide_later_text(self) -> None:
        html = '<span style="display:none">nope<br>still hidden</span><p>later visible</p>'
        text = textclean.html_to_visible_text(html)
        self.assertIn("later visible", text)
        self.assertNotIn("nope", text)
        self.assertNotIn("still hidden", text)

    def test_nested_hidden_divs(self) -> None:
        html = '<div hidden><div>inner secret</div>also hidden</div><p>after</p>'
        text = textclean.html_to_visible_text(html)
        self.assertIn("after", text)
        self.assertNotIn("inner secret", text)
        self.assertNotIn("also hidden", text)

    def test_optional_end_closes_hidden_sibling(self) -> None:
        lists = textclean.html_to_visible_text(
            '<ul><li>a<li style="display:none">hid<li>c</ul>'
        )
        self.assertIn("a", lists)
        self.assertIn("c", lists)
        self.assertNotIn("hid", lists)
        cells = textclean.html_to_visible_text(
            '<table><tr><td style="display:none">x<td>y</table>'
        )
        self.assertIn("y", cells)
        self.assertNotIn("x", cells)
        paras = textclean.html_to_visible_text('<p style="display:none">hid<p>shown')
        self.assertIn("shown", paras)
        self.assertNotIn("hid", paras)


class GmailTests(_ReadHome):
    def _transport(self, *, messages=None, token=None, fail_list=False, fail_get=False, body=None):
        messages = messages or []

        def transport(method, url, **kwargs):
            safe = url.split("?")[0]
            if safe.endswith("/token") or "/token" in safe:
                return google_http.GoogleHttpResponse(
                    200, json.dumps({"access_token": "ya29.x", "expires_in": 3600})
                )
            if fail_list and safe.endswith("/messages"):
                raise google_http.GoogleHttpStatusError("http_500", status=500)
            if safe.endswith("/messages"):
                params = kwargs.get("params") or {}
                self._last_params = params
                return google_http.GoogleHttpResponse(
                    200,
                    json.dumps(
                        {
                            "messages": [{"id": item["id"], "threadId": item["threadId"]} for item in messages],
                            **({"nextPageToken": token} if token else {}),
                        }
                    ),
                )
            if "/messages/" in safe:
                if fail_get:
                    raise google_http.GoogleHttpStatusError("http_500", status=500)
                message_id = safe.rsplit("/", 1)[-1]
                found = next(item for item in messages if item["id"] == message_id)
                return google_http.GoogleHttpResponse(200, json.dumps(found if body is None else body))
            return google_http.GoogleHttpResponse(404, "{}")

        google_http.set_transport_for_tests(transport)

    def _message(self, **over):
        payload = {
            "mimeType": "multipart/alternative",
            "headers": [
                {"name": "From", "value": '"Ada Lovelace" <ada@example.com>'},
                {"name": "Subject", "value": "P8 smoke"},
                {"name": "Date", "value": "Thu, 8 Oct 2026 12:00:00 -0700"},
            ],
            "parts": [
                {
                    "mimeType": "text/plain",
                    "body": {"data": _b64("plain wins"), "size": 10},
                },
                {
                    "mimeType": "text/html",
                    "body": {"data": _b64("<p>html loses</p>"), "size": 16},
                },
                {
                    "mimeType": "application/pdf",
                    "filename": "note.pdf",
                    "body": {"size": 40, "attachmentId": "att-1"},
                },
            ],
        }
        message = {
            "id": "msg-1",
            "threadId": "th-1",
            "labelIds": ["INBOX", "UNREAD"],
            "payload": payload,
        }
        message.update(over)
        return message

    def test_query_passthrough_metadata_and_more(self) -> None:
        message = self._message()
        self._transport(messages=[message], token="next")
        raw = gmail.gmail_search_handler({"query": "newer_than:1d", "max_results": 100})
        data = _unframe(raw)
        self.assertEqual(self._last_params["q"], "newer_than:1d")
        self.assertEqual(self._last_params["maxResults"], gmail.read_common.MAX_RESULTS_CAP)
        self.assertEqual(data["state"], "complete")
        self.assertTrue(data["more_available"])
        row = data["messages"][0]
        self.assertEqual(row["from_name"], "Ada Lovelace")
        self.assertEqual(row["from_address"], "ada@example.com")
        self.assertEqual(row["subject"], "P8 smoke")
        self.assertEqual(row["labels"], ["INBOX", "UNREAD"])
        self.assertEqual(row["attachments"], [{"filename": "note.pdf", "mime_type": "application/pdf", "size": 40}])
        self.assertNotIn("newer_than:1d", self._log())
        self.assertNotIn("ada@example.com", self._log())
        self.assertNotIn("P8 smoke", self._log())
        self.assertNotIn("msg-1", self._log())
        self.assertTrue(taint.is_tainted("sess-1"))

    def test_failed_list_and_metadata_are_incomplete(self) -> None:
        self._transport(fail_list=True)
        data = _unframe(gmail.gmail_search_handler({"query": "in:inbox"}))
        self.assertEqual(data["state"], "incomplete")
        self.assertEqual(data["messages"], [])
        self.assertFalse(taint.is_tainted("sess-1"))

        self._transport(messages=[self._message()], fail_get=True)
        data = _unframe(gmail.gmail_search_handler({"query": "in:inbox"}))
        self.assertEqual(data["state"], "incomplete")
        self.assertEqual(data["messages"], [])
        self.assertNotIn("P8 smoke", json.dumps(data))

    def test_read_prefers_plain_and_caps(self) -> None:
        message = self._message()
        self._transport(messages=[message], body=message)
        data = _unframe(gmail.gmail_read_handler({"message_id": "msg-1"}))
        self.assertEqual(data["text"], "plain wins")
        self.assertFalse(data["truncated"])
        self.assertNotIn("html loses", data["text"])
        self.assertIn(read_common.handle_hash("msg-1"), self._log())
        self.assertNotIn("msg-1", self._log())

    def test_html_charset_quote_cap_and_delimiter(self) -> None:
        cafe = "caf\u00e9"
        html = (
            "<p>visible</p><script>secret()</script>"
            '<div class="gmail_quote">old thread</div>'
            "<p>&gt; quoted</p>"
        )
        # Body is HTML only, latin-1 for a second part is covered by decode helper.
        decoded = gmail._decode_body(_b64(cafe, "latin-1"), "latin-1")
        self.assertEqual(decoded, cafe)
        payload = {
            "mimeType": "text/html",
            "headers": [{"name": "Content-Type", "value": "text/html; charset=utf-8"}],
            "body": {"data": _b64(html + ("Z" * 5000))},
        }
        text, truncated, total = gmail.extract_body(payload)
        self.assertIn("visible", text)
        self.assertNotIn("secret", text)
        self.assertNotIn("old thread", text)
        self.assertTrue(truncated)
        self.assertLessEqual(len(text), textclean.BODY_CHAR_CAP)
        self.assertGreater(total, textclean.BODY_CHAR_CAP)
        poison = framing.frame_untrusted("gmail_read", "untrusted_tool_result")
        self.assertNotIn("<untrusted_tool_result source", poison.split("\n", 1)[1])
        self.assertIn("untrusted-tool-result", poison)

    def test_not_brian_no_taint_and_taint_failure_hides_content(self) -> None:
        turn_context.clear_all_for_tests()
        data = _unframe(gmail.gmail_search_handler({"query": "in:inbox"}))
        self.assertEqual(data["reason"], read_common.REASON_NOT_BRIAN)
        self.assertFalse(taint.is_tainted("sess-1"))
        _seed_brian_turn()
        self._transport(messages=[self._message()])
        with mock.patch.object(taint, "mark_tainted", side_effect=OSError("disk")):
            failed = _unframe(gmail.gmail_search_handler({"query": "in:inbox"}))
        self.assertEqual(failed["reason"], read_common.REASON_TAINT_WRITE_FAILED)
        self.assertEqual(failed["messages"], [])
        self.assertNotIn("P8 smoke", json.dumps(failed))

    def test_search_snippet_framed_not_logged(self) -> None:
        message = self._message()
        message["snippet"] = "SNIPPET_TOKEN_p8"
        self._transport(messages=[message])
        raw = gmail.gmail_search_handler({"query": "in:inbox"})
        data = _unframe(raw)
        self.assertEqual(data["messages"][0]["snippet"], "SNIPPET_TOKEN_p8")
        self.assertIn("SNIPPET_TOKEN_p8", raw)
        self.assertIn(framing.DELIMITER_TOKEN, raw)
        self.assertNotIn("SNIPPET_TOKEN_p8", self._log())

    def test_inline_text_plain_attachment_skipped(self) -> None:
        payload = {
            "mimeType": "multipart/mixed",
            "parts": [
                {"mimeType": "text/plain", "body": {"data": _b64("visible body")}},
                {
                    "mimeType": "text/plain",
                    "filename": "note.txt",
                    "body": {"data": _b64("SECRET-INLINE"), "size": 13},
                },
            ],
        }
        text, _truncated, _total = gmail.extract_body(payload)
        self.assertIn("visible body", text)
        self.assertNotIn("SECRET-INLINE", text)

    def test_bad_message_id_no_google_call(self) -> None:
        calls = []

        def transport(method, url, **kwargs):
            calls.append(url)
            raise AssertionError("bad id must not call Google")

        google_http.set_transport_for_tests(transport)
        for bad in ("a/b", "..", "id?x", "%2F"):
            with self.subTest(bad=bad):
                data = _unframe(gmail.gmail_read_handler({"message_id": bad}))
                self.assertEqual(data["reason"], read_common.REASON_BAD_ARGS)
        self.assertEqual(calls, [])


class DriveTests(_ReadHome):
    def test_escape_quotes_and_backslashes(self) -> None:
        built = drive.build_drive_q("a'b\\c")
        self.assertEqual(
            built,
            "name contains 'a\\'b\\\\c' or fullText contains 'a\\'b\\\\c'",
        )
        seen = {}

        def transport(method, url, **kwargs):
            if "/token" in url:
                return google_http.GoogleHttpResponse(
                    200, json.dumps({"access_token": "ya29.x", "expires_in": 3600})
                )
            seen["params"] = kwargs.get("params")
            return google_http.GoogleHttpResponse(
                200,
                json.dumps(
                    {
                        "nextPageToken": "n",
                        "files": [
                            {
                                "id": "file-1",
                                "name": "notes.txt",
                                "mimeType": "text/plain",
                                "modifiedTime": "2026-10-08T00:00:00Z",
                            }
                        ],
                    }
                ),
            )

        google_http.set_transport_for_tests(transport)
        before = {p.name for p in self.home.rglob("*") if p.is_file()}
        data = _unframe(drive.drive_search_handler({"query": "a'b\\c"}))
        after = {p.name for p in self.home.rglob("*") if p.is_file()}
        self.assertEqual(seen["params"]["q"], built)
        self.assertTrue(data["more_available"])
        self.assertEqual(data["files"][0]["id"], "file-1")
        self.assertNotIn("a'b\\c", self._log())
        self.assertNotIn("notes.txt", self._log())
        self.assertNotIn("file-1", self._log())
        extra = after - before - {"zola_workspace.log", "taint.sqlite", "token.dpapi"}
        self.assertEqual(extra, set())

    def test_routing_unsupported_truncate_and_failed_download(self) -> None:
        calls = []

        def transport(method, url, **kwargs):
            calls.append((url, kwargs.get("params")))
            if "/token" in url:
                return google_http.GoogleHttpResponse(
                    200, json.dumps({"access_token": "ya29.x", "expires_in": 3600})
                )
            params = kwargs.get("params") or {}
            if params.get("fields"):
                mime = params.get("_mime") or self._mime
                return google_http.GoogleHttpResponse(
                    200, json.dumps({"id": "f", "mimeType": mime, "size": self._size})
                )
            if self._fail:
                raise google_http.GoogleHttpStatusError("http_500", status=500)
            body = self._body
            return google_http.GoogleHttpResponse(200, body, content=body.encode("utf-8"))

        self._mime = "application/vnd.google-apps.document"
        self._size = 10
        self._body = "doc text"
        self._fail = False
        google_http.set_transport_for_tests(transport)
        doc = _unframe(drive.drive_read_handler({"file_id": "f"}))
        self.assertEqual(doc["text"], "doc text")
        self.assertTrue(any(item[1] and item[1].get("mimeType") == "text/plain" for item in calls))

        calls.clear()
        self._mime = "application/vnd.google-apps.spreadsheet"
        sheet = _unframe(drive.drive_read_handler({"file_id": "f"}))
        self.assertEqual(sheet["text"], "doc text")
        self.assertTrue(any(item[1] and item[1].get("mimeType") == "text/csv" for item in calls))

        self._mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        office = _unframe(drive.drive_read_handler({"file_id": "f"}))
        self.assertEqual(office["state"], "unsupported_type")
        self.assertEqual(office["reason"], drive.REASON_OFFICE)
        self.assertEqual(office["text"], "")

        self._mime = "text/plain"
        self._body = "y" * (textclean.BODY_CHAR_CAP + 5)
        capped = _unframe(drive.drive_read_handler({"file_id": "f"}))
        self.assertEqual(capped["state"], "complete")
        self.assertTrue(capped["truncated"])
        self.assertEqual(capped["chars_returned"], textclean.BODY_CHAR_CAP)

        self._fail = True
        self._body = "should-not-appear"
        failed = _unframe(drive.drive_read_handler({"file_id": "f"}))
        self.assertEqual(failed["state"], "incomplete")
        self.assertNotIn("should-not-appear", json.dumps(failed))

        self._fail = False
        self._mime = "application/vnd.google-apps.document"
        self._body = "z" * (drive.EXPORT_BYTE_CAP + 1)
        huge = _unframe(drive.drive_read_handler({"file_id": "f"}))
        self.assertEqual(huge["state"], "complete")
        self.assertTrue(huge["truncated"])
        self.assertNotIn("incomplete", huge["state"])
        self.assertLessEqual(huge["chars_returned"], textclean.BODY_CHAR_CAP)

    def test_pdf_limits(self) -> None:
        self.assertEqual(drive.PYPDF_VERSION, "6.19.0")
        self.assertEqual(drive.PDF_TIMEOUT_SECONDS, 20)
        self.assertEqual(drive.PDF_MAX_PAGES, 50)
        self.assertIn("is_encrypted", drive._PDF_CHILD)
        called = {"n": 0}

        def runner(data: bytes):
            called["n"] += 1
            return {"ok": True, "text": "page", "pages": 1}

        drive.set_pdf_runner_for_tests(runner)
        big = drive.extract_pdf_bytes(b"x" * (drive.PDF_MAX_BYTES + 1))
        self.assertEqual(big["reason"], drive.REASON_PDF_TOO_LARGE)
        self.assertEqual(called["n"], 0)
        self.assertNotIn("text", big)

        pages = drive.extract_pdf_bytes(b"%PDF")
        runner_many = lambda data: {"ok": True, "text": "first-fifty", "pages": 51, "pages_truncated": True}
        drive.set_pdf_runner_for_tests(runner_many)
        many = drive.extract_pdf_bytes(b"%PDF")
        self.assertTrue(many["truncated"])
        self.assertEqual(many["text"], "first-fifty")

        drive.set_pdf_runner_for_tests(lambda data: {"ok": False, "encrypted": True, "text": "SECRET"})
        encrypted = drive.extract_pdf_bytes(b"%PDF")
        self.assertEqual(encrypted["state"], "unsupported_type")
        self.assertEqual(encrypted["reason"], drive.REASON_PDF_ENCRYPTED)
        self.assertNotIn("text", encrypted)
        self.assertNotIn("SECRET", json.dumps(encrypted))

        with self.assertRaises(drive.PdfTimeout):
            drive._run_pdf_child(
                b"%PDF",
                timeout_s=0.2,
                argv=[sys.executable, "-c", "import time; time.sleep(30)"],
            )
        drive.set_pdf_runner_for_tests(lambda data: (_ for _ in ()).throw(drive.PdfTimeout()))
        timed = drive.extract_pdf_bytes(b"%PDF")
        self.assertEqual(timed["reason"], drive.REASON_PDF_TIMEOUT)
        self.assertNotIn("text", timed)

    def test_non_utf8_media_bytes_reach_pdf_runner(self) -> None:
        raw = b"\xff\xfe\x00\x80%PDF-1.4"
        seen = {}

        class RawBody:
            def __init__(self, content: bytes) -> None:
                self.status_code = 200
                self.content = content
                self.text = "CORRUPT"
                self.headers = {}

        def transport(method, url, **kwargs):
            if "/token" in url:
                return google_http.GoogleHttpResponse(
                    200, json.dumps({"access_token": "ya29.x", "expires_in": 3600})
                )
            params = kwargs.get("params") or {}
            if params.get("fields"):
                return google_http.GoogleHttpResponse(
                    200,
                    json.dumps({"id": "f", "mimeType": "application/pdf", "size": len(raw)}),
                )
            return RawBody(raw)

        def runner(data: bytes):
            seen["data"] = data
            return {"ok": True, "text": "extracted", "pages": 1}

        google_http.set_transport_for_tests(transport)
        drive.set_pdf_runner_for_tests(runner)
        data = _unframe(drive.drive_read_handler({"file_id": "f"}))
        self.assertEqual(seen["data"], raw)
        self.assertEqual(data["text"], "extracted")
        self.assertNotIn("CORRUPT", data["text"])

    def test_google_http_preserves_raw_content(self) -> None:
        raw = b"\xff\xfe\x80\x00"

        class RawBody:
            status_code = 200
            content = raw
            text = "CORRUPT"
            headers = {}

        google_http.set_transport_for_tests(lambda *a, **k: RawBody())
        resp = google_http.request("GET", "https://www.googleapis.com/drive/v3/files/f", route=google_http.ROUTE_DRIVE_GET)
        self.assertEqual(resp.content, raw)
        self.assertNotEqual(resp.content, b"CORRUPT")

    def test_media_over_cap_uses_range_and_truncates(self) -> None:
        seen = {}

        def transport(method, url, **kwargs):
            if "/token" in url:
                return google_http.GoogleHttpResponse(
                    200, json.dumps({"access_token": "ya29.x", "expires_in": 3600})
                )
            params = kwargs.get("params") or {}
            headers = kwargs.get("headers") or {}
            if params.get("fields"):
                return google_http.GoogleHttpResponse(
                    200,
                    json.dumps(
                        {
                            "id": "f",
                            "mimeType": "text/plain",
                            "size": drive.EXPORT_BYTE_CAP + 10,
                        }
                    ),
                )
            seen["range"] = headers.get("Range")
            return google_http.GoogleHttpResponse(200, "AAAA", content=b"AAAA")

        google_http.set_transport_for_tests(transport)
        data = _unframe(drive.drive_read_handler({"file_id": "f"}))
        self.assertEqual(seen["range"], f"bytes=0-{drive.EXPORT_BYTE_CAP - 1}")
        self.assertEqual(data["state"], "complete")
        self.assertTrue(data["truncated"])
        self.assertEqual(data["text"], "AAAA")

    def test_bad_file_id_no_google_call(self) -> None:
        calls = []

        def transport(method, url, **kwargs):
            calls.append(url)
            raise AssertionError("bad id must not call Google")

        google_http.set_transport_for_tests(transport)
        for bad in ("a/b", "..", "id?x", "%2F"):
            with self.subTest(bad=bad):
                data = _unframe(drive.drive_read_handler({"file_id": bad}))
                self.assertEqual(data["reason"], read_common.REASON_BAD_ARGS)
        self.assertEqual(calls, [])


class ContactsTests(_ReadHome):
    def test_parse_empty_and_no_sleep(self) -> None:
        source = (PLUGIN_ROOT / "contacts.py").read_text(encoding="utf-8")
        self.assertNotIn("otherContacts.search", source)
        self.assertNotIn("time.sleep", source)

        def transport(method, url, **kwargs):
            if "/token" in url:
                return google_http.GoogleHttpResponse(
                    200, json.dumps({"access_token": "ya29.x", "expires_in": 3600})
                )
            self.params = kwargs.get("params")
            return google_http.GoogleHttpResponse(
                200,
                json.dumps(
                    {
                        "results": [
                            {
                                "person": {
                                    "names": [{"displayName": "Ada"}],
                                    "emailAddresses": [{"value": "ada@example.com"}],
                                    "phoneNumbers": [{"value": "555"}],
                                }
                            }
                        ]
                    }
                ),
            )

        google_http.set_transport_for_tests(transport)
        data = _unframe(contacts.contacts_lookup_handler({"query": "Ada", "max_results": 100}))
        self.assertEqual(self.params["pageSize"], read_common.MAX_RESULTS_CAP)
        self.assertEqual(self.params["readMask"], contacts.READ_MASK)
        self.assertEqual(data["contacts"][0]["display_name"], "Ada")
        self.assertNotIn("Ada", self._log())
        self.assertNotIn("ada@example.com", self._log())

        def empty(method, url, **kwargs):
            if "/token" in url:
                return google_http.GoogleHttpResponse(
                    200, json.dumps({"access_token": "ya29.x", "expires_in": 3600})
                )
            return google_http.GoogleHttpResponse(200, json.dumps({"results": []}))

        google_http.set_transport_for_tests(empty)
        none = _unframe(contacts.contacts_lookup_handler({"query": "nobody"}))
        self.assertEqual(none["state"], "no_match")
        self.assertEqual(none["contacts"], [])


class GuardRowTests(unittest.TestCase):
    def test_terminal_and_self_mod_rows(self) -> None:
        blocked = [
            ("terminal", {"command": "curl https://gmail.googleapis.com/gmail/v1/users/me/messages"}),
            ("terminal", {"command": "curl https://accounts.google.com/o/oauth2/v2/auth"}),
            ("terminal", {"command": r"Get-Content %LOCALAPPDATA%\hermes\profiles\zola\zola_workspace\token.dpapi"}),
            ("terminal", {"command": r"Get-Content %HERMES_HOME%\zola_workspace\taint.sqlite"}),
            ("terminal", {"command": "python -m zola_workspace.setup"}),
            ("terminal", {"command": r"Remove-Item C:\Users\test\AppData\Local\hermes\profiles\zola\zola_workspace"}),
            ("write_file", {"path": r"C:\src\plugins\zola_workspace\guards.py", "content": "x"}),
            ("patch", {"path": r"C:\src\plugins\zola_workspace\guards.py", "patch": "x"}),
            ("terminal", {"command": r"Set-Content plugins\zola_workspace\guards.py x"}),
            ("terminal", {"command": r"Remove-Item token.dpapi"}),
        ]
        allowed = [
            ("terminal", {"command": "curl https://example.com"}),
            ("terminal", {"command": r"Get-ChildItem C:\Users\test\Dev"}),
            ("terminal", {"command": "python -m pip list"}),
            ("write_file", {"path": r"C:\Users\test\Dev\notes\todo.txt", "content": "x"}),
            ("terminal", {"command": "curl https://notgoogleapis.com"}),
        ]
        for tool, args in blocked:
            with self.subTest(tool=tool, args=args):
                result = guards.pre_tool_call_hook(tool_name=tool, args=args)
                self.assertIsNotNone(result)
        for tool, args in allowed:
            with self.subTest(tool=tool, args=args):
                self.assertIsNone(guards.pre_tool_call_hook(tool_name=tool, args=args))

    def test_residuals_are_not_blocked(self) -> None:
        residuals = [
            "curl https://142.250.190.14/",
            "curl https://xn--p1ai/",
            "curl --resolve example.com:443:1.2.3.4 https://example.com",
            'curl "$host$rest"',
            r"Get-Content Z:\secret.bin",
            "powershell -EncodedCommand QQ==",
            r"powershell -File C:\Users\test\Dev\notes\run.ps1",
            r"copy \\?\Volume{abc}\guards.pyc C:\temp\g.pyc",
        ]
        for command in residuals:
            with self.subTest(command=command):
                self.assertIsNone(
                    guards.pre_tool_call_hook(tool_name="terminal", args={"command": command})
                )

    def test_self_mod_memory_tools_and_soul(self) -> None:
        blocked = [
            ("write_file", {"path": r"C:\src\plugins\zola_memory\consolidate.py", "content": "x"}),
            ("write_file", {"path": r"C:\src\plugins\zola_tools\calculator.py", "content": "x"}),
            ("patch", {"path": r"C:\src\plugins\zola_memory\forget.py", "patch": "x"}),
            (
                "write_file",
                {"path": r"C:\Users\test\AppData\Local\hermes\profiles\zola\SOUL.md", "content": "x"},
            ),
            (
                "write_file",
                {
                    "path": r"C:\Users\test\Dev\zola-windows\zola-architecture\identity\SOUL.md",
                    "content": "x",
                },
            ),
            ("terminal", {"command": r"Set-Content plugins\zola_memory\x.py y"}),
            ("terminal", {"command": r"Set-Content plugins\zola_tools\x.py y"}),
            ("terminal", {"command": r"Get-Content zola-architecture\identity\SOUL.md"}),
        ]
        for tool, args in blocked:
            with self.subTest(tool=tool, args=args):
                self.assertIsNotNone(guards.pre_tool_call_hook(tool_name=tool, args=args))

    def test_self_mod_residuals_not_blocked(self) -> None:
        """A path built in a variable, a junction path, or an encoded command is not blocked."""
        residuals = [
            "Set-Content $dest $bytes",
            r"Copy-Item Z:\file.txt C:\temp\out.txt",
            "powershell -EncodedCommand QQ==",
        ]
        for command in residuals:
            with self.subTest(command=command):
                self.assertIsNone(
                    guards.pre_tool_call_hook(tool_name="terminal", args={"command": command})
                )


class LineageMissingRowTests(_TempHome):
    def test_missing_row_tainted_and_existing_row_unaffected(self) -> None:
        taint.set_store_path_for_tests(self.home / "zola_workspace" / "taint.sqlite")
        _sessions(self.home, [("fresh", None)])
        self.assertFalse(taint.is_tainted("fresh"))
        _seed_brian_turn(session_id="fresh", user_message="Remember the P8 test is at 3 PM")
        allowed = guards.evaluate_memory_taint(
            tool_name="memory",
            args={"action": "add", "content": "the P8 test is at 3 PM"},
            session_id="fresh",
            task_id="fresh",
            turn_id="turn-brian",
        )
        self.assertIsNone(allowed)

        self.assertTrue(taint.is_tainted("missing-row"))
        with self.assertRaises(taint.LineageLookupError):
            taint.lineage_root("missing-row")
        blocked = guards.evaluate_memory_taint(
            tool_name="memory",
            args={"action": "add", "content": "a paraphrased fact"},
            session_id="missing-row",
            task_id="missing-row",
            turn_id="turn-brian",
        )
        self.assertIsNotNone(blocked)

    def test_absent_state_db_stays_non_error(self) -> None:
        self.assertIsNone(taint.lineage_root("no-db"))
        self.assertFalse(taint.is_tainted("no-db"))


class SourceScanTests(unittest.TestCase):
    def test_no_write_endpoints_and_routes(self) -> None:
        gmail_src = (PLUGIN_ROOT / "gmail.py").read_text(encoding="utf-8")
        drive_src = (PLUGIN_ROOT / "drive.py").read_text(encoding="utf-8")
        # P8-SEND: drafts create/update/get/delete/send are the Gmail writes — P8-D06
        for banned in ("messages/send", ".trash", ".modify", "/attachments", "batch"):
            self.assertNotIn(banned, gmail_src)
        for banned in ("uploadType", "files.delete", "permissions"):
            self.assertNotIn(banned, drive_src)
        offenders = []
        for path in PLUGIN_ROOT.glob("*.py"):
            if path.name == "google_http.py":
                continue
            text = path.read_text(encoding="utf-8")
            if "import requests" in text or "from requests" in text:
                offenders.append(path.name)
        self.assertEqual(offenders, [])


class GmailSummaryWordingTests(unittest.TestCase):
    def test_search_and_read_descriptions_include_summary_rules(self) -> None:
        search = (
            "When summarizing for Brian, account for every message returned: mention each "
            "message from a person by sender and subject, group the rest by type, and say "
            "how many you grouped. Never fold a message from a person into promotions."
        )
        read = (
            "If Brian's words match more than one message, name the matching subjects and "
            "ask which one, unless one subject clearly matches his words."
        )
        self.assertIn(search, gmail._SEARCH_SCHEMA["description"])
        self.assertIn(read, gmail._READ_SCHEMA["description"])


class CalendarDescriptionTests(unittest.TestCase):
    def test_descriptions_not_returned(self) -> None:
        from datetime import timezone

        item = gcal._shape_event(
            {
                "summary": "Meet",
                "description": "secret",
                "start": {"dateTime": "2026-10-08T12:00:00Z"},
                "end": {"dateTime": "2026-10-08T13:00:00Z"},
            },
            calendar_name="Brian",
            tz=timezone.utc,
        )
        self.assertFalse(item["descriptions_included"])
        self.assertNotIn("description", item)
        self.assertIn("Event descriptions are not returned.", gcal._CALENDAR_DESCRIPTION)


if __name__ == "__main__":
    unittest.main()
