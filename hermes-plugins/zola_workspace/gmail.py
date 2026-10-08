"""gmail_search and gmail_read — synchronous, read-only (P8-D07 / P8-D09)."""

from __future__ import annotations

import base64
import re
import time
from typing import Any, Dict, List, Tuple

try:
    from . import auth
    from . import google_http
    from . import log as wslog
    from . import read_common
    from . import textclean
except ImportError:  # P8-READ: flat unittest discover — P8-D07
    import auth
    import google_http
    import log as wslog
    import read_common
    import textclean

# P8-READ: named Gmail tools, routes, and caps — P8-D07
TOOL_SEARCH = "gmail_search"
TOOL_READ = "gmail_read"
TOOLSET_NAME = "zola_workspace"

LIST_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages"
GET_URL_TMPL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}"

REASON_MISSING_GMAIL_SCOPE = "missing_gmail_scope"
METADATA_HEADERS = ("From", "Subject", "Date")

_FROM_ANGLE_RE = re.compile(r"^(.*?)<([^>]+)>\s*$")
_CHARSET_RE = re.compile(r"charset\s*=\s*\"?([^\"\s;]+)", re.IGNORECASE)

# P8-READ: summaries must name person-mail; a colliding read must ask — P8-D07
_SEARCH_DESCRIPTION = (
    "Search Brian's Gmail with Gmail query syntax (for example newer_than:1d or "
    "from:someone@example.com). The query is passed through; this tool does not "
    "parse natural-language dates. Returns metadata and an opaque message id. "
    "Does not return message bodies or attachment bytes. "
    "When summarizing for Brian, account for every message returned: mention each message from a person by sender and subject, group the rest by type, and say how many you grouped. Never fold a message from a person into promotions."
)

_READ_DESCRIPTION = (
    "Read one Gmail message by the opaque id from gmail_search. Prefers plain text. "
    "A truncated body is an excerpt of the message, not the whole message. "
    "Attachment content is not returned. "
    "If Brian's words match more than one message, name the matching subjects and ask which one, unless one subject clearly matches his words."
)

_SEARCH_SCHEMA: Dict[str, Any] = {
    "name": TOOL_SEARCH,
    "description": _SEARCH_DESCRIPTION,
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Gmail search query, passed through to Google.",
            },
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
            "message_id": {
                "type": "string",
                "description": "Opaque id returned by gmail_search.",
            },
        },
        "required": ["message_id"],
        "additionalProperties": False,
    },
}


def search_schema() -> Dict[str, Any]:
    return dict(_SEARCH_SCHEMA)


def read_schema() -> Dict[str, Any]:
    return dict(_READ_SCHEMA)


def _header_map(payload: Dict[str, Any]) -> Dict[str, str]:
    found: Dict[str, str] = {}
    for header in payload.get("headers") or []:
        if not isinstance(header, dict):
            continue
        name = str(header.get("name") or "")
        if name:
            found[name.casefold()] = str(header.get("value") or "")
    return found


def parse_from(value: str) -> Tuple[str, str]:
    raw = str(value or "").strip()
    match = _FROM_ANGLE_RE.match(raw)
    if match:
        name = match.group(1).strip().strip('"')
        return name, match.group(2).strip()
    return "", raw


def _walk_parts(part: Dict[str, Any]) -> List[Dict[str, Any]]:
    found = [part]
    for child in part.get("parts") or []:
        if isinstance(child, dict):
            found.extend(_walk_parts(child))
    return found


def attachment_meta(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Name, MIME, and size only. Attachment bytes are not downloaded."""
    # P8-READ: list filename, type, and size — P8-D07
    items: List[Dict[str, Any]] = []
    for part in _walk_parts(payload):
        filename = str(part.get("filename") or "")
        if not filename:
            continue
        body = part.get("body") or {}
        items.append(
            {
                "filename": filename,
                "mime_type": str(part.get("mimeType") or ""),
                "size": int(body.get("size") or 0),
            }
        )
    return items


def shape_metadata(message: Dict[str, Any]) -> Dict[str, Any]:
    payload = message.get("payload") or {}
    headers = _header_map(payload if isinstance(payload, dict) else {})
    from_name, from_address = parse_from(headers.get("from", ""))
    return {
        "id": str(message.get("id") or ""),
        "thread_id": str(message.get("threadId") or ""),
        "from_name": from_name,
        "from_address": from_address,
        "subject": headers.get("subject", ""),
        "date": headers.get("date", ""),
        "labels": [str(item) for item in (message.get("labelIds") or [])],
        "snippet": str(message.get("snippet") or ""),
        "attachments": attachment_meta(payload if isinstance(payload, dict) else {}),
    }


def _charset_of(part: Dict[str, Any]) -> str:
    headers = _header_map(part)
    content_type = headers.get("content-type", "")
    match = _CHARSET_RE.search(content_type)
    if match:
        return match.group(1)
    return "utf-8"


def _decode_body(data: str, charset: str) -> str:
    raw = str(data or "")
    pad = "=" * (-len(raw) % 4)
    try:
        blob = base64.urlsafe_b64decode(raw + pad)
    except Exception:
        return ""
    try:
        return blob.decode(charset or "utf-8", errors="replace")
    except LookupError:
        return blob.decode("utf-8", errors="replace")


def extract_body(payload: Dict[str, Any]) -> Tuple[str, bool, int]:
    """Prefer text/plain. Returns (text, html_used, truncated, chars_total)."""
    plain: List[str] = []
    html_parts: List[str] = []
    for part in _walk_parts(payload):
        mime = str(part.get("mimeType") or "").casefold()
        body = part.get("body") or {}
        data = body.get("data")
        if str(part.get("filename") or ""):
            continue
        if not data or body.get("attachmentId"):
            continue
        text = _decode_body(str(data), _charset_of(part))
        if mime == "text/plain":
            plain.append(text)
        elif mime == "text/html":
            html_parts.append(text)
    if plain:
        return textclean.prepare_body("\n".join(plain), html=False)
    if html_parts:
        excerpt, truncated, total = textclean.prepare_body("\n".join(html_parts), html=True)
        return excerpt, truncated, total
    return "", False, 0


def _elapsed(started: float) -> int:
    return int((time.monotonic() - started) * 1000)


def _search_impl(args: Dict[str, Any]) -> str:
    started = time.monotonic()
    query = str(args.get("query") or "").strip()
    if not query:
        return read_common.refuse(
            TOOL_SEARCH,
            state=read_common.STATE_ERROR,
            reason=read_common.REASON_BAD_ARGS,
            empty_key="messages",
        )
    max_results = read_common.clamp_max_results(args.get("max_results"))
    if max_results is None:
        return read_common.refuse(
            TOOL_SEARCH,
            state=read_common.STATE_ERROR,
            reason=read_common.REASON_BAD_ARGS,
            empty_key="messages",
        )
    refusal, headers = read_common.authorize(
        TOOL_SEARCH,
        required_scope=auth.SCOPE_GMAIL_READONLY,
        missing_scope_reason=REASON_MISSING_GMAIL_SCOPE,
        empty_key="messages",
        log_event=wslog.LOG_EVENT_GMAIL_SEARCH,
        started_ms=_elapsed(started),
    )
    if refusal is not None or headers is None:
        return refusal or ""
    try:
        listed = read_common.google_get(
            LIST_URL,
            headers=headers,
            route=google_http.ROUTE_GMAIL_LIST,
            params={"q": query, "maxResults": max_results},
        ).json()
    except google_http.GoogleHttpError:
        return read_common.refuse(
            TOOL_SEARCH,
            state=read_common.STATE_INCOMPLETE,
            reason="gmail_list_failed",
            empty_key="messages",
        )
    stubs = [item for item in (listed.get("messages") or []) if isinstance(item, dict)]
    more_available = bool(listed.get("nextPageToken"))
    messages: List[Dict[str, Any]] = []
    for stub in stubs[:max_results]:
        message_id = str(stub.get("id") or "")
        if not message_id:
            continue
        try:
            full = read_common.google_get(
                GET_URL_TMPL.format(message_id=message_id),
                headers=headers,
                route=google_http.ROUTE_GMAIL_GET,
                params={
                    "format": "metadata",
                    "metadataHeaders": list(METADATA_HEADERS),
                },
            ).json()
        except google_http.GoogleHttpError:
            return read_common.refuse(
                TOOL_SEARCH,
                state=read_common.STATE_INCOMPLETE,
                reason="gmail_metadata_failed",
                empty_key="messages",
            )
        messages.append(shape_metadata(full))
    state = read_common.STATE_NO_MATCH if not messages else read_common.STATE_COMPLETE
    payload = {
        "ok": True,
        "state": state,
        "more_available": more_available,
        "messages": messages,
    }
    return read_common.mark_then_frame(
        TOOL_SEARCH,
        payload,
        empty_key="messages",
        log_event=wslog.LOG_EVENT_GMAIL_SEARCH,
        log_fields={
            "state": state,
            "count": len(messages),
            "more": more_available,
            "ms": _elapsed(started),
        },
    )


def _read_impl(args: Dict[str, Any]) -> str:
    started = time.monotonic()
    message_id = str(args.get("message_id") or "").strip()
    if not read_common.valid_opaque_id(message_id):
        return read_common.refuse(
            TOOL_READ,
            state=read_common.STATE_ERROR,
            reason=read_common.REASON_BAD_ARGS,
            empty_key="text",
        )
    refusal, headers = read_common.authorize(
        TOOL_READ,
        required_scope=auth.SCOPE_GMAIL_READONLY,
        missing_scope_reason=REASON_MISSING_GMAIL_SCOPE,
        empty_key="text",
        log_event=wslog.LOG_EVENT_GMAIL_READ,
        started_ms=_elapsed(started),
    )
    if refusal is not None or headers is None:
        return refusal or ""
    try:
        message = read_common.google_get(
            GET_URL_TMPL.format(message_id=message_id),
            headers=headers,
            route=google_http.ROUTE_GMAIL_GET,
            params={"format": "full"},
        ).json()
    except google_http.GoogleHttpError:
        return read_common.refuse(
            TOOL_READ,
            state=read_common.STATE_INCOMPLETE,
            reason="gmail_get_failed",
            empty_key="text",
        )
    payload_body = message.get("payload") or {}
    if not isinstance(payload_body, dict):
        payload_body = {}
    text, truncated, total = extract_body(payload_body)
    meta = shape_metadata(message)
    meta.pop("id", None)
    result = {
        "ok": True,
        "state": read_common.STATE_COMPLETE,
        "truncated": truncated,
        "chars_returned": len(text),
        "chars_total": total,
        "text": text,
        **{
            key: meta[key]
            for key in (
                "from_name",
                "from_address",
                "subject",
                "date",
                "labels",
                "snippet",
                "attachments",
            )
        },
    }
    return read_common.mark_then_frame(
        TOOL_READ,
        result,
        empty_key="text",
        log_event=wslog.LOG_EVENT_GMAIL_READ,
        log_fields={
            "state": read_common.STATE_COMPLETE,
            "truncated": truncated,
            "chars": len(text),
            "handle": read_common.handle_hash(message_id),
            "ms": _elapsed(started),
        },
    )


def _guarded(tool_name: str, log_event: str, impl, args: dict) -> str:
    started = time.monotonic()
    try:
        return impl(args if isinstance(args, dict) else {})
    except Exception:
        try:
            wslog.write_event(log_event, state=read_common.STATE_ERROR, count=0, ms=_elapsed(started))
        except Exception:
            pass
        empty = "messages" if tool_name == TOOL_SEARCH else "text"
        return read_common.refuse(
            tool_name,
            state=read_common.STATE_ERROR,
            reason="internal_error",
            empty_key=empty,
        )


def gmail_search_handler(args: dict, **kwargs) -> str:
    return _guarded(TOOL_SEARCH, wslog.LOG_EVENT_GMAIL_SEARCH, _search_impl, args)


def gmail_read_handler(args: dict, **kwargs) -> str:
    return _guarded(TOOL_READ, wslog.LOG_EVENT_GMAIL_READ, _read_impl, args)
