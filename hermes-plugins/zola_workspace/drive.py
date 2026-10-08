"""drive_search and drive_read — synchronous, read-only (P8-D08 / P8-D09)."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from typing import Any, Callable, Dict, List, Optional

try:
    from . import auth
    from . import google_http
    from . import log as wslog
    from . import read_common
    from . import textclean
except ImportError:  # P8-READ: flat unittest discover — P8-D08
    import auth
    import google_http
    import log as wslog
    import read_common
    import textclean

# P8-READ: named Drive tools, MIME routing, and PDF limits — P8-D08
TOOL_SEARCH = "drive_search"
TOOL_READ = "drive_read"
TOOLSET_NAME = "zola_workspace"

LIST_URL = "https://www.googleapis.com/drive/v3/files"
GET_URL_TMPL = "https://www.googleapis.com/drive/v3/files/{file_id}"
EXPORT_URL_TMPL = "https://www.googleapis.com/drive/v3/files/{file_id}/export"

# P8-READ: pypdf 6.19.0 is installed at Phase 5b, not before — P8-D08
PYPDF_VERSION = "6.19.0"
PDF_MAX_BYTES = 10 * 1024 * 1024
PDF_MAX_PAGES = 50
PDF_TIMEOUT_SECONDS = 20
EXPORT_BYTE_CAP = 10 * 1024 * 1024

MIME_DOC = "application/vnd.google-apps.document"
MIME_SHEET = "application/vnd.google-apps.spreadsheet"
MIME_SLIDES = "application/vnd.google-apps.presentation"
MIME_PDF = "application/pdf"

OFFICE_MIME_TYPES = frozenset(
    {
        "application/msword",
        "application/vnd.ms-excel",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }
)

REASON_MISSING_DRIVE_SCOPE = "missing_drive_scope"
REASON_PDF_TOO_LARGE = "pdf_too_large"
REASON_PDF_ENCRYPTED = "pdf_encrypted"
REASON_PDF_TIMEOUT = "pdf_timeout"
REASON_PDF_UNAVAILABLE = "pdf_extractor_unavailable"
REASON_PDF_EXTRACT = "pdf_extract_error"
REASON_OFFICE = "office_unsupported"
REASON_UNSUPPORTED_MIME = "unsupported_mime"

_SEARCH_DESCRIPTION = (
    "Find files in Brian's Google Drive by name or full text. "
    "Returns an opaque file id, name, type, and modified time."
)

_READ_DESCRIPTION = (
    "Read one Drive file by the opaque id from drive_search. "
    "Google Docs and Slides export as text. Google Sheets export as CSV "
    "(first sheet). Plain text is downloaded. PDF text is extracted with "
    "the pinned reader. Word, Excel, and PowerPoint are not read. "
    "A truncated result is an excerpt, not the whole file."
)

_SEARCH_SCHEMA: Dict[str, Any] = {
    "name": TOOL_SEARCH,
    "description": _SEARCH_DESCRIPTION,
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Plain text matched against name and full text."},
            "max_results": {
                "type": "integer",
                "minimum": 1,
                "maximum": read_common.MAX_RESULTS_CAP,
                "description": (
                    f"1–{read_common.MAX_RESULTS_CAP}; default {read_common.MAX_RESULTS_DEFAULT}."
                ),
            },
        },
        "required": ["query"],
        "additionalProperties": False,
    },
}

_READ_SCHEMA: Dict[str, Any] = {
    "name": TOOL_READ,
    "description": _READ_DESCRIPTION,
    "parameters": {
        "type": "object",
        "properties": {
            "file_id": {"type": "string", "description": "Opaque id returned by drive_search."},
        },
        "required": ["file_id"],
        "additionalProperties": False,
    },
}

# Child reads PDF bytes on stdin and prints one JSON object. No file is written.
_PDF_CHILD = r"""
import json, sys
from io import BytesIO
def main():
    data = sys.stdin.buffer.read()
    try:
        from pypdf import PdfReader
    except Exception:
        json.dump({"ok": False, "error": "unavailable"}, sys.stdout)
        return
    try:
        reader = PdfReader(BytesIO(data))
        if getattr(reader, "is_encrypted", False):
            try:
                opened = reader.decrypt("")
            except Exception:
                opened = 0
            if not opened:
                json.dump({"ok": False, "encrypted": True}, sys.stdout)
                return
        pages = list(reader.pages)
        n = len(pages)
        limit = 50
        chunks = []
        for page in pages[:limit]:
            chunks.append(page.extract_text() or "")
        json.dump({"ok": True, "text": "\n".join(chunks), "pages": n, "pages_truncated": n > limit}, sys.stdout)
    except Exception as exc:
        name = type(exc).__name__.lower()
        message = str(exc).lower()
        encrypted = ("encrypt" in name) or ("password" in message)
        json.dump({"ok": False, "encrypted": encrypted, "error": "extract_failed"}, sys.stdout)
main()
"""

_pdf_runner: Optional[Callable[[bytes], Dict[str, Any]]] = None


class PdfTimeout(Exception):
    """The PDF child exceeded its timeout. Stdout is discarded."""


def search_schema() -> Dict[str, Any]:
    return dict(_SEARCH_SCHEMA)


def read_schema() -> Dict[str, Any]:
    return dict(_READ_SCHEMA)


def set_pdf_runner_for_tests(fn: Optional[Callable[[bytes], Dict[str, Any]]]) -> None:
    global _pdf_runner
    _pdf_runner = fn


def escape_drive_query_text(text: str) -> str:
    """Escape backslash and single quote for a Drive q string literal."""
    # P8-READ: backslash first, then quote — P8-D08
    return str(text or "").replace("\\", "\\\\").replace("'", "\\'")


def build_drive_q(text: str) -> str:
    escaped = escape_drive_query_text(text)
    return f"name contains '{escaped}' or fullText contains '{escaped}'"


def _run_pdf_child(
    data: bytes,
    *,
    timeout_s: float = PDF_TIMEOUT_SECONDS,
    argv: Optional[List[str]] = None,
) -> Dict[str, Any]:
    cmd = argv or [sys.executable, "-c", _PDF_CHILD]
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    try:
        out, _err = proc.communicate(data, timeout=timeout_s)
    except subprocess.TimeoutExpired:
        proc.kill()
        try:
            proc.communicate(timeout=2)
        except Exception:
            pass
        raise PdfTimeout()
    try:
        payload = json.loads(out.decode("utf-8", errors="replace") or "{}")
    except Exception:
        return {"ok": False, "error": "extract_failed"}
    return payload if isinstance(payload, dict) else {"ok": False, "error": "extract_failed"}


def extract_pdf_bytes(data: bytes) -> Dict[str, Any]:
    """Apply the PDF limits. Returns a result fragment, never a partial on failure."""
    # P8-READ: size, pages, timeout, encryption — P8-D08
    if len(data) > PDF_MAX_BYTES:
        return {"state": read_common.STATE_UNSUPPORTED, "reason": REASON_PDF_TOO_LARGE}
    runner = _pdf_runner or _run_pdf_child
    try:
        payload = runner(data)
    except PdfTimeout:
        return {"state": read_common.STATE_ERROR, "reason": REASON_PDF_TIMEOUT}
    except Exception:
        return {"state": read_common.STATE_ERROR, "reason": REASON_PDF_EXTRACT}
    if not isinstance(payload, dict) or not payload.get("ok"):
        if payload.get("encrypted") if isinstance(payload, dict) else False:
            return {"state": read_common.STATE_UNSUPPORTED, "reason": REASON_PDF_ENCRYPTED}
        if isinstance(payload, dict) and payload.get("error") == "unavailable":
            return {"state": read_common.STATE_ERROR, "reason": REASON_PDF_UNAVAILABLE}
        return {"state": read_common.STATE_ERROR, "reason": REASON_PDF_EXTRACT}
    pages = int(payload.get("pages") or 0)
    text, truncated, total = textclean.prepare_body(str(payload.get("text") or ""), html=False)
    if pages > PDF_MAX_PAGES or payload.get("pages_truncated"):
        truncated = True
    return {
        "state": read_common.STATE_COMPLETE,
        "text": text,
        "truncated": truncated,
        "chars_returned": len(text),
        "chars_total": total,
    }


def _elapsed(started: float) -> int:
    return int((time.monotonic() - started) * 1000)


def _text_result(mime: str, body: str, *, html: bool = False) -> Dict[str, Any]:
    text, truncated, total = textclean.prepare_body(body, html=html)
    return {
        "ok": True,
        "state": read_common.STATE_COMPLETE,
        "mime_type": mime,
        "truncated": truncated,
        "chars_returned": len(text),
        "chars_total": total,
        "text": text,
    }


def _bytes_of(resp: google_http.GoogleHttpResponse) -> bytes:
    """Media and export bodies. Never re-encoded from the text view."""
    # P8-READ: PDF bytes must survive the transport unchanged — P8-D08
    content = getattr(resp, "content", None)
    if isinstance(content, (bytes, bytearray)):
        return bytes(content)
    return b""


def _search_impl(args: Dict[str, Any]) -> str:
    started = time.monotonic()
    query = str(args.get("query") or "").strip()
    if not query:
        return read_common.refuse(
            TOOL_SEARCH,
            state=read_common.STATE_ERROR,
            reason=read_common.REASON_BAD_ARGS,
            empty_key="files",
        )
    max_results = read_common.clamp_max_results(args.get("max_results"))
    if max_results is None:
        return read_common.refuse(
            TOOL_SEARCH,
            state=read_common.STATE_ERROR,
            reason=read_common.REASON_BAD_ARGS,
            empty_key="files",
        )
    refusal, headers = read_common.authorize(
        TOOL_SEARCH,
        required_scope=auth.SCOPE_DRIVE_READONLY,
        missing_scope_reason=REASON_MISSING_DRIVE_SCOPE,
        empty_key="files",
        log_event=wslog.LOG_EVENT_DRIVE_SEARCH,
        started_ms=_elapsed(started),
    )
    if refusal is not None or headers is None:
        return refusal or ""
    try:
        listed = read_common.google_get(
            LIST_URL,
            headers=headers,
            route=google_http.ROUTE_DRIVE_LIST,
            params={
                "q": build_drive_q(query),
                "pageSize": max_results,
                "orderBy": "modifiedTime desc",
                "fields": "nextPageToken,files(id,name,mimeType,modifiedTime)",
                "supportsAllDrives": True,
                "includeItemsFromAllDrives": True,
            },
        ).json()
    except google_http.GoogleHttpError:
        return read_common.refuse(
            TOOL_SEARCH,
            state=read_common.STATE_INCOMPLETE,
            reason="drive_list_failed",
            empty_key="files",
        )
    files: List[Dict[str, Any]] = []
    for item in (listed.get("files") or [])[:max_results]:
        if not isinstance(item, dict):
            continue
        files.append(
            {
                "id": str(item.get("id") or ""),
                "name": str(item.get("name") or ""),
                "mime_type": str(item.get("mimeType") or ""),
                "modified_time": str(item.get("modifiedTime") or ""),
            }
        )
    more_available = bool(listed.get("nextPageToken"))
    state = read_common.STATE_NO_MATCH if not files else read_common.STATE_COMPLETE
    payload = {"ok": True, "state": state, "more_available": more_available, "files": files}
    return read_common.mark_then_frame(
        TOOL_SEARCH,
        payload,
        empty_key="files",
        log_event=wslog.LOG_EVENT_DRIVE_SEARCH,
        log_fields={"state": state, "count": len(files), "more": more_available, "ms": _elapsed(started)},
    )


def _read_impl(args: Dict[str, Any]) -> str:
    started = time.monotonic()
    file_id = str(args.get("file_id") or "").strip()
    if not read_common.valid_opaque_id(file_id):
        return read_common.refuse(
            TOOL_READ,
            state=read_common.STATE_ERROR,
            reason=read_common.REASON_BAD_ARGS,
            empty_key="text",
        )
    refusal, headers = read_common.authorize(
        TOOL_READ,
        required_scope=auth.SCOPE_DRIVE_READONLY,
        missing_scope_reason=REASON_MISSING_DRIVE_SCOPE,
        empty_key="text",
        log_event=wslog.LOG_EVENT_DRIVE_READ,
        started_ms=_elapsed(started),
    )
    if refusal is not None or headers is None:
        return refusal or ""
    try:
        meta_resp = read_common.google_get(
            GET_URL_TMPL.format(file_id=file_id),
            headers=headers,
            route=google_http.ROUTE_DRIVE_GET,
            params={"fields": "id,mimeType,size", "supportsAllDrives": True},
        )
        meta = meta_resp.json()
    except google_http.GoogleHttpError:
        return read_common.refuse(
            TOOL_READ,
            state=read_common.STATE_INCOMPLETE,
            reason="drive_get_failed",
            empty_key="text",
        )
    mime = str(meta.get("mimeType") or "")
    try:
        size = int(meta.get("size") or 0)
    except (TypeError, ValueError):
        size = 0
    outcome = _read_mime(file_id, mime, size, headers)
    if outcome.get("state") in (read_common.STATE_INCOMPLETE, read_common.STATE_ERROR) and not outcome.get("ok"):
        return read_common.refuse(
            TOOL_READ,
            state=str(outcome.get("state")),
            reason=str(outcome.get("reason") or "drive_read_failed"),
            empty_key="text",
        )
    if outcome.get("state") == read_common.STATE_UNSUPPORTED:
        payload = {
            "ok": False,
            "state": read_common.STATE_UNSUPPORTED,
            "reason": outcome.get("reason"),
            "mime_type": mime,
            "text": "",
        }
    else:
        payload = outcome
    return read_common.mark_then_frame(
        TOOL_READ,
        payload,
        empty_key="text",
        log_event=wslog.LOG_EVENT_DRIVE_READ,
        log_fields={
            "state": payload.get("state"),
            "truncated": bool(payload.get("truncated")),
            "chars": len(str(payload.get("text") or "")),
            "handle": read_common.handle_hash(file_id),
            "ms": _elapsed(started),
        },
    )


def _read_mime(file_id: str, mime: str, size: int, headers: Dict[str, str]) -> Dict[str, Any]:
    if mime in OFFICE_MIME_TYPES:
        return {"state": read_common.STATE_UNSUPPORTED, "reason": REASON_OFFICE}
    if mime == MIME_PDF:
        if size > PDF_MAX_BYTES:
            return {"state": read_common.STATE_UNSUPPORTED, "reason": REASON_PDF_TOO_LARGE}
        try:
            resp = read_common.google_get(
                GET_URL_TMPL.format(file_id=file_id),
                headers=headers,
                route=google_http.ROUTE_DRIVE_GET,
                params={"alt": "media", "supportsAllDrives": True},
            )
        except google_http.GoogleHttpError:
            return {"ok": False, "state": read_common.STATE_INCOMPLETE, "reason": "drive_download_failed"}
        data = _bytes_of(resp)
        if len(data) > PDF_MAX_BYTES:
            return {"state": read_common.STATE_UNSUPPORTED, "reason": REASON_PDF_TOO_LARGE}
        extracted = extract_pdf_bytes(data)
        if extracted.get("state") != read_common.STATE_COMPLETE:
            return extracted
        extracted["ok"] = True
        extracted["mime_type"] = mime
        return extracted
    if mime == MIME_DOC:
        export_mime = "text/plain"
    elif mime == MIME_SHEET:
        export_mime = "text/csv"
    elif mime == MIME_SLIDES:
        export_mime = "text/plain"
    elif mime.startswith("text/"):
        export_mime = ""
    else:
        return {"state": read_common.STATE_UNSUPPORTED, "reason": REASON_UNSUPPORTED_MIME}
    ranged = size > EXPORT_BYTE_CAP and not export_mime
    req_headers = dict(headers)
    if ranged:
        # P8-READ: over the cap, fetch the first cap bytes and mark truncated — P8-D08
        req_headers["Range"] = f"bytes=0-{EXPORT_BYTE_CAP - 1}"
    try:
        if export_mime:
            resp = read_common.google_get(
                EXPORT_URL_TMPL.format(file_id=file_id),
                headers=req_headers,
                route=google_http.ROUTE_DRIVE_EXPORT,
                params={"mimeType": export_mime},
            )
        else:
            resp = read_common.google_get(
                GET_URL_TMPL.format(file_id=file_id),
                headers=req_headers,
                route=google_http.ROUTE_DRIVE_GET,
                params={"alt": "media", "supportsAllDrives": True},
            )
    except google_http.GoogleHttpError:
        return {"ok": False, "state": read_common.STATE_INCOMPLETE, "reason": "drive_download_failed"}
    data = _bytes_of(resp)
    truncated_bytes = ranged or len(data) > EXPORT_BYTE_CAP
    if len(data) > EXPORT_BYTE_CAP:
        data = data[:EXPORT_BYTE_CAP]
    result = _text_result(mime, data.decode("utf-8", "replace"))
    if truncated_bytes:
        result["truncated"] = True
    return result


def _guarded(tool_name: str, log_event: str, impl, args: dict) -> str:
    started = time.monotonic()
    try:
        return impl(args if isinstance(args, dict) else {})
    except Exception:
        try:
            wslog.write_event(log_event, state=read_common.STATE_ERROR, count=0, ms=_elapsed(started))
        except Exception:
            pass
        empty = "files" if tool_name == TOOL_SEARCH else "text"
        return read_common.refuse(
            tool_name,
            state=read_common.STATE_ERROR,
            reason="internal_error",
            empty_key=empty,
        )


def drive_search_handler(args: dict, **kwargs) -> str:
    return _guarded(TOOL_SEARCH, wslog.LOG_EVENT_DRIVE_SEARCH, _search_impl, args)


def drive_read_handler(args: dict, **kwargs) -> str:
    return _guarded(TOOL_READ, wslog.LOG_EVENT_DRIVE_READ, _read_impl, args)
