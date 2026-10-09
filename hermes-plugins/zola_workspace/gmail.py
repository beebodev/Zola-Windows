"""gmail_search, gmail_read, gmail_draft, and gmail_send_draft (P8-D07 / P8-D05 / P8-D06)."""

from __future__ import annotations

import base64
import re
import time
from typing import Any, Dict, List, Optional, Tuple

try:
    from . import auth
    from . import google_http
    from . import log as wslog
    from . import posture
    from . import read_common
    from . import send_gate
    from . import textclean
    from . import turn_context
except ImportError:  # P8-READ: flat unittest discover — P8-D07
    import auth
    import google_http
    import log as wslog
    import posture
    import read_common
    import send_gate
    import textclean
    import turn_context

# P8-READ: named Gmail tools, routes, and caps — P8-D07
TOOL_SEARCH = "gmail_search"
TOOL_READ = "gmail_read"
# P8-SEND: draft and send are the only write tools — P8-D05 / P8-D06
TOOL_DRAFT = "gmail_draft"
TOOL_SEND = "gmail_send_draft"
TOOLSET_NAME = "zola_workspace"

DRAFTS_URL = "https://gmail.googleapis.com/gmail/v1/users/me/drafts"
DRAFTS_SEND_URL = DRAFTS_URL + "/send"
DRAFT_URL_TMPL = DRAFTS_URL + "/{draft_id}"

REASON_NOT_BRIAN = "not_brian"
REASON_POSTURE = "posture"
REASON_NEEDS_RECONNECT = "needs_reconnect"
REASON_BAD_ARGS = "bad_args"
REASON_FETCH_FAILED = "fetch_failed"
REASON_ATTACHMENT = "attachment_unsupported"
REASON_SEND_FAILED = "send_failed"
STATE_SENT = "sent"

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


_DRAFT_DESCRIPTION = (
    "Create, update, show, or delete one Gmail draft for Brian. "
    "Returns the recipients, subject, and body so they can be read back. Does not send."
)

_SEND_DESCRIPTION = (
    "Send one Gmail draft that was already read back in this conversation. "
    "Takes only the draft id. Refuses unless this turn is allowed to send that draft."
)

_DRAFT_SCHEMA: Dict[str, Any] = {
    "name": TOOL_DRAFT,
    "description": _DRAFT_DESCRIPTION,
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["create", "update", "show", "delete"],
                "description": "create, update, show, or delete.",
            },
            "draft_id": {
                "type": "string",
                "description": "Draft id for update, show, or delete.",
            },
            "to": {
                "description": "To addresses. A list, or one address string.",
            },
            "cc": {
                "description": "Cc addresses. A list, or one address string.",
            },
            "bcc": {
                "description": "Bcc addresses. A list, or one address string.",
            },
            "subject": {"type": "string", "description": "Subject line."},
            "body": {"type": "string", "description": "Plain-text body."},
            "reply_to_message_id": {
                "type": "string",
                "description": "Message to reply to. Sets threading and the default To.",
            },
        },
        "required": ["action"],
        "additionalProperties": False,
    },
}

_SEND_SCHEMA: Dict[str, Any] = {
    "name": TOOL_SEND,
    "description": _SEND_DESCRIPTION,
    "parameters": {
        "type": "object",
        "properties": {
            "draft_id": {
                "type": "string",
                "description": "Id of the draft to send.",
            },
        },
        "required": ["draft_id"],
        "additionalProperties": False,
    },
}


def draft_schema() -> Dict[str, Any]:
    return dict(_DRAFT_SCHEMA)


def send_schema() -> Dict[str, Any]:
    return dict(_SEND_SCHEMA)


def _as_list(value: Any) -> Optional[List[str]]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return list(value)
    return None


def _draft_refuse(tool_name: str, *, state: str, reason: str, draft_id: str = "") -> str:
    payload: Dict[str, Any] = {
        "ok": False,
        "state": state,
        "reason": reason,
        "draft_id": draft_id or "",
    }
    return read_common.dump_result(tool_name, payload)


def _turn() -> Tuple[str, str]:
    turn_id = turn_context.current_turn_id_from_context() or ""
    record = turn_context.get_record(turn_id) if turn_id else None
    session_id = str(record.session_id or "") if record is not None else ""
    return turn_id, session_id


def _gate(tool_name: str, draft_id: str, started: float, *, need_readonly: bool) -> Tuple[Optional[str], Optional[Dict[str, str]]]:
    """Brian, posture, then the local store. No Gmail call."""
    turn_id, _session_id = _turn()
    if not turn_context.is_brian_turn(turn_id):
        send_gate.log_decision(
            decision="refused",
            reason=REASON_NOT_BRIAN,
            draft_id=draft_id,
            started=started,
        )
        return (
            _draft_refuse(tool_name, state=read_common.STATE_ERROR, reason=REASON_NOT_BRIAN, draft_id=draft_id),
            None,
        )
    try:
        ok_posture = posture.posture_ok()
    except Exception:
        ok_posture = False
    if not ok_posture:
        send_gate.log_decision(
            decision="refused",
            reason=REASON_POSTURE,
            draft_id=draft_id,
            started=started,
        )
        return (
            _draft_refuse(tool_name, state=read_common.STATE_ERROR, reason=REASON_POSTURE, draft_id=draft_id),
            None,
        )
    auth.maybe_clear_stale_reconnect()
    status = auth.store_status()
    if status.get("needs_reconnect") or not status.get("connected"):
        send_gate.log_decision(
            decision="refused",
            reason=REASON_NEEDS_RECONNECT,
            draft_id=draft_id,
            started=started,
        )
        return (
            _draft_refuse(
                tool_name,
                state=read_common.STATE_NEEDS_RECONNECT,
                reason=REASON_NEEDS_RECONNECT,
                draft_id=draft_id,
            ),
            None,
        )
    try:
        record = auth.load_token_record()
    except Exception:
        record = None
    scopes = set(record.scopes) if record is not None else set()
    needed = {auth.SCOPE_GMAIL_COMPOSE}
    if need_readonly:
        needed.add(auth.SCOPE_GMAIL_READONLY)
    if record is None or not needed.issubset(scopes):
        send_gate.log_decision(
            decision="refused",
            reason=REASON_NEEDS_RECONNECT,
            draft_id=draft_id,
            started=started,
        )
        return (
            _draft_refuse(
                tool_name,
                state=read_common.STATE_NEEDS_RECONNECT,
                reason=REASON_NEEDS_RECONNECT,
                draft_id=draft_id,
            ),
            None,
        )
    try:
        headers = auth.authorization_header()
    except Exception:
        send_gate.log_decision(
            decision="refused",
            reason=REASON_NEEDS_RECONNECT,
            draft_id=draft_id,
            started=started,
        )
        return (
            _draft_refuse(
                tool_name,
                state=read_common.STATE_NEEDS_RECONNECT,
                reason=REASON_NEEDS_RECONNECT,
                draft_id=draft_id,
            ),
            None,
        )
    return None, headers


def _excerpt(body: str) -> str:
    """4000-character cap. Quote-trimming is for mail we read, not a draft being sent."""
    text = body or ""
    if len(text) <= textclean.BODY_CHAR_CAP:
        return text
    return text[: textclean.BODY_CHAR_CAP]


def _content_payload(action: str, fields: Dict[str, Any], *, reply_to_differs: bool) -> Dict[str, Any]:
    body = str(fields.get("body") or "")
    return {
        "ok": True,
        "state": read_common.STATE_COMPLETE,
        "action": action,
        "draft_id": str(fields.get("draft_id") or ""),
        "to": send_gate.people(str(fields.get("to") or "")),
        "cc": send_gate.people(str(fields.get("cc") or "")),
        "bcc": send_gate.people(str(fields.get("bcc") or "")),
        "subject": str(fields.get("subject") or ""),
        "body": _excerpt(body),
        "body_chars": len(body),
        "readback": send_gate.readback_for(body),
        "reply_to_differs": bool(reply_to_differs),
        "thread_id": str(fields.get("thread_id") or ""),
    }


def _recipient_count(fields: Dict[str, Any]) -> int:
    return (
        len(send_gate.people(str(fields.get("to") or "")))
        + len(send_gate.people(str(fields.get("cc") or "")))
        + len(send_gate.people(str(fields.get("bcc") or "")))
    )


def _present_result(action: str, fields: Dict[str, Any], *, differs: bool, started: float) -> str:
    turn_id, session_id = _turn()
    draft_id = str(fields.get("draft_id") or "")
    send_gate.present(
        session_id=session_id,
        turn_id=turn_id,
        draft_id=draft_id,
        fields=fields,
        reply_to_differs=differs,
    )
    send_gate.log_decision(
        decision="prepared",
        draft_id=draft_id,
        recipient_count=_recipient_count(fields),
        started=started,
    )
    return read_common.dump_result(TOOL_DRAFT, _content_payload(action, fields, reply_to_differs=differs))


def _fetch_draft(draft_id: str, headers: Dict[str, str]) -> Dict[str, Any]:
    # P8-SEND: drafts.get passes its route label — P8-D06
    return google_http.request(
        "GET",
        DRAFT_URL_TMPL.format(draft_id=draft_id),
        headers=headers,
        params={"format": "full"},
        timeout=30.0,
        route=google_http.ROUTE_GMAIL_DRAFTS_GET,
    ).json()


def _source_message(message_id: str, headers: Dict[str, str]) -> Dict[str, Any]:
    return read_common.google_get(
        GET_URL_TMPL.format(message_id=message_id),
        headers=headers,
        route=google_http.ROUTE_GMAIL_GET,
        params={
            "format": "metadata",
            "metadataHeaders": ["From", "Reply-To", "Message-Id", "References", "Subject"],
        },
    ).json()


def _create(args: Dict[str, Any], headers: Dict[str, str], started: float) -> str:
    to_items = _as_list(args.get("to")) if "to" in args else None
    cc_items = _as_list(args.get("cc")) if "cc" in args else []
    bcc_items = _as_list(args.get("bcc")) if "bcc" in args else []
    subject = args.get("subject")
    body = args.get("body")
    reply_id = str(args.get("reply_to_message_id") or "").strip()
    if cc_items is None or bcc_items is None or not isinstance(subject, str) or not isinstance(body, str):
        return _draft_refuse(TOOL_DRAFT, state=read_common.STATE_ERROR, reason=REASON_BAD_ARGS)
    plan = {
        "default_to": "",
        "reply_to_differs": False,
        "in_reply_to": "",
        "references": "",
        "thread_id": "",
    }
    if reply_id:
        if not read_common.valid_opaque_id(reply_id):
            return _draft_refuse(TOOL_DRAFT, state=read_common.STATE_ERROR, reason=REASON_BAD_ARGS)
        try:
            plan = send_gate.reply_plan(_source_message(reply_id, headers))
        except google_http.GoogleHttpError:
            return _draft_refuse(TOOL_DRAFT, state=read_common.STATE_ERROR, reason=REASON_FETCH_FAILED)
    if "to" in args:
        if to_items is None:
            return _draft_refuse(TOOL_DRAFT, state=read_common.STATE_ERROR, reason=REASON_BAD_ARGS)
    elif plan.get("default_to"):
        to_items = [str(plan["default_to"])]
    else:
        return _draft_refuse(TOOL_DRAFT, state=read_common.STATE_ERROR, reason=REASON_BAD_ARGS)
    if not send_gate.addr_specs(to_items or []):
        return _draft_refuse(TOOL_DRAFT, state=read_common.STATE_ERROR, reason=REASON_BAD_ARGS)
    if not send_gate.canon_subject(subject):
        return _draft_refuse(TOOL_DRAFT, state=read_common.STATE_ERROR, reason=REASON_BAD_ARGS)
    raw = send_gate.build_raw(
        to=to_items or [],
        cc=cc_items or [],
        bcc=bcc_items or [],
        subject=subject,
        body=body,
        in_reply_to=str(plan.get("in_reply_to") or ""),
        references=str(plan.get("references") or ""),
    )
    message: Dict[str, Any] = {"raw": raw}
    thread_id = str(plan.get("thread_id") or "")
    if thread_id:
        message["threadId"] = thread_id
    try:
        created = google_http.request(
            "POST",
            DRAFTS_URL,
            headers=headers,
            json={"message": message},
            timeout=30.0,
            route=google_http.ROUTE_GMAIL_DRAFTS_CREATE,
        ).json()
    except google_http.GoogleHttpError:
        return _draft_refuse(TOOL_DRAFT, state=read_common.STATE_ERROR, reason=REASON_FETCH_FAILED)
    draft_id = str(created.get("id") or "")
    if not read_common.valid_opaque_id(draft_id):
        return _draft_refuse(TOOL_DRAFT, state=read_common.STATE_ERROR, reason=REASON_FETCH_FAILED)
    _turn_id, session_id = _turn()
    send_gate.remember_own(session_id, draft_id)
    send_gate.note_reply_differs(session_id, draft_id, bool(plan.get("reply_to_differs")))
    try:
        fetched = _fetch_draft(draft_id, headers)
    except google_http.GoogleHttpError:
        return _draft_refuse(
            TOOL_DRAFT, state=read_common.STATE_ERROR, reason=REASON_FETCH_FAILED, draft_id=draft_id
        )
    fields = send_gate.parse_draft(fetched)
    fields["draft_id"] = draft_id
    if fields.get("filenames"):
        return _draft_refuse(
            TOOL_DRAFT, state=read_common.STATE_ERROR, reason=REASON_ATTACHMENT, draft_id=draft_id
        )
    return _present_result(
        "create",
        fields,
        differs=bool(plan.get("reply_to_differs")),
        started=started,
    )


def _load_own(draft_id: str, headers: Dict[str, str]) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    _turn_id, session_id = _turn()
    if not send_gate.owns(session_id, draft_id):
        return (
            _draft_refuse(
                TOOL_DRAFT,
                state=read_common.STATE_ERROR,
                reason=send_gate.REASON_NOT_OWN_DRAFT,
                draft_id=draft_id,
            ),
            None,
        )
    try:
        fetched = _fetch_draft(draft_id, headers)
    except google_http.GoogleHttpError:
        return (
            _draft_refuse(
                TOOL_DRAFT, state=read_common.STATE_ERROR, reason=REASON_FETCH_FAILED, draft_id=draft_id
            ),
            None,
        )
    fields = send_gate.parse_draft(fetched)
    fields["draft_id"] = draft_id
    if fields.get("filenames"):
        return (
            _draft_refuse(
                TOOL_DRAFT, state=read_common.STATE_ERROR, reason=REASON_ATTACHMENT, draft_id=draft_id
            ),
            None,
        )
    return None, fields


def _update(args: Dict[str, Any], headers: Dict[str, str], started: float) -> str:
    draft_id = str(args.get("draft_id") or "").strip()
    if not read_common.valid_opaque_id(draft_id):
        return _draft_refuse(TOOL_DRAFT, state=read_common.STATE_ERROR, reason=REASON_BAD_ARGS)
    refusal, fields = _load_own(draft_id, headers)
    if refusal is not None or fields is None:
        return refusal or ""
    to_items = _as_list(args["to"]) if "to" in args else [str(fields.get("to") or "")]
    cc_items = _as_list(args["cc"]) if "cc" in args else [str(fields.get("cc") or "")]
    bcc_items = _as_list(args["bcc"]) if "bcc" in args else [str(fields.get("bcc") or "")]
    subject = args["subject"] if "subject" in args else str(fields.get("subject") or "")
    body = args["body"] if "body" in args else str(fields.get("body") or "")
    if (
        to_items is None
        or cc_items is None
        or bcc_items is None
        or not isinstance(subject, str)
        or not isinstance(body, str)
    ):
        return _draft_refuse(
            TOOL_DRAFT, state=read_common.STATE_ERROR, reason=REASON_BAD_ARGS, draft_id=draft_id
        )
    if not send_gate.addr_specs(to_items) or not send_gate.canon_subject(subject):
        return _draft_refuse(
            TOOL_DRAFT, state=read_common.STATE_ERROR, reason=REASON_BAD_ARGS, draft_id=draft_id
        )
    raw = send_gate.build_raw(
        to=to_items,
        cc=cc_items,
        bcc=bcc_items,
        subject=subject,
        body=body,
        in_reply_to=str(fields.get("in_reply_to") or ""),
        references=str(fields.get("references") or ""),
    )
    message: Dict[str, Any] = {"raw": raw}
    thread_id = str(fields.get("thread_id") or "")
    if thread_id:
        message["threadId"] = thread_id
    try:
        google_http.request(
            "PUT",
            DRAFT_URL_TMPL.format(draft_id=draft_id),
            headers=headers,
            json={"id": draft_id, "message": message},
            timeout=30.0,
            route=google_http.ROUTE_GMAIL_DRAFTS_UPDATE,
        )
        fetched = _fetch_draft(draft_id, headers)
    except google_http.GoogleHttpError:
        return _draft_refuse(
            TOOL_DRAFT, state=read_common.STATE_ERROR, reason=REASON_FETCH_FAILED, draft_id=draft_id
        )
    updated = send_gate.parse_draft(fetched)
    updated["draft_id"] = draft_id
    if updated.get("filenames"):
        return _draft_refuse(
            TOOL_DRAFT, state=read_common.STATE_ERROR, reason=REASON_ATTACHMENT, draft_id=draft_id
        )
    _turn_id, session_id = _turn()
    return _present_result(
        "update",
        updated,
        differs=send_gate.reply_differs(session_id, draft_id),
        started=started,
    )


def _show(args: Dict[str, Any], headers: Dict[str, str], started: float) -> str:
    draft_id = str(args.get("draft_id") or "").strip()
    if not read_common.valid_opaque_id(draft_id):
        return _draft_refuse(TOOL_DRAFT, state=read_common.STATE_ERROR, reason=REASON_BAD_ARGS)
    refusal, fields = _load_own(draft_id, headers)
    if refusal is not None or fields is None:
        return refusal or ""
    _turn_id, session_id = _turn()
    return _present_result(
        "show",
        fields,
        differs=send_gate.reply_differs(session_id, draft_id),
        started=started,
    )


def _delete(args: Dict[str, Any], headers: Dict[str, str], started: float) -> str:
    draft_id = str(args.get("draft_id") or "").strip()
    turn_id, session_id = _turn()
    if not read_common.valid_opaque_id(draft_id):
        return _draft_refuse(TOOL_DRAFT, state=read_common.STATE_ERROR, reason=REASON_BAD_ARGS)
    if not send_gate.owns(session_id, draft_id):
        send_gate.log_decision(
            decision="refused",
            reason=send_gate.REASON_NOT_OWN_DRAFT,
            draft_id=draft_id,
            started=started,
        )
        return _draft_refuse(
            TOOL_DRAFT,
            state=read_common.STATE_ERROR,
            reason=send_gate.REASON_NOT_OWN_DRAFT,
            draft_id=draft_id,
        )
    text = send_gate.current_turn_text(turn_id)
    if text is None or not send_gate.delete_requested(text):
        send_gate.log_decision(
            decision="refused",
            reason=send_gate.REASON_DELETE_NOT_REQUESTED,
            draft_id=draft_id,
            started=started,
        )
        return _draft_refuse(
            TOOL_DRAFT,
            state=read_common.STATE_ERROR,
            reason=send_gate.REASON_DELETE_NOT_REQUESTED,
            draft_id=draft_id,
        )
    try:
        google_http.request(
            "DELETE",
            DRAFT_URL_TMPL.format(draft_id=draft_id),
            headers=headers,
            timeout=30.0,
            route=google_http.ROUTE_GMAIL_DRAFTS_DELETE,
        )
    except google_http.GoogleHttpError:
        return _draft_refuse(
            TOOL_DRAFT, state=read_common.STATE_ERROR, reason=REASON_FETCH_FAILED, draft_id=draft_id
        )
    send_gate.drop_pending(session_id, draft_id)
    send_gate.log_decision(decision="deleted", draft_id=draft_id, started=started)
    return read_common.dump_result(
        TOOL_DRAFT,
        {"ok": True, "state": read_common.STATE_COMPLETE, "action": "delete", "draft_id": draft_id},
    )


def _draft_impl(args: Dict[str, Any]) -> str:
    started = time.monotonic()
    action = str(args.get("action") or "").strip()
    draft_id = str(args.get("draft_id") or "").strip()
    if action not in {"create", "update", "show", "delete"}:
        return _draft_refuse(TOOL_DRAFT, state=read_common.STATE_ERROR, reason=REASON_BAD_ARGS, draft_id=draft_id)
    refusal, headers = _gate(
        TOOL_DRAFT,
        draft_id,
        started,
        need_readonly=bool(str(args.get("reply_to_message_id") or "").strip()),
    )
    if refusal is not None or headers is None:
        return refusal or ""
    if action == "create":
        return _create(args, headers, started)
    if action == "update":
        return _update(args, headers, started)
    if action == "show":
        return _show(args, headers, started)
    return _delete(args, headers, started)


def _send_impl(args: Dict[str, Any]) -> str:
    started = time.monotonic()
    draft_id = str(args.get("draft_id") or "").strip()
    if not read_common.valid_opaque_id(draft_id):
        return _draft_refuse(TOOL_SEND, state=read_common.STATE_ERROR, reason=REASON_BAD_ARGS)
    refusal, headers = _gate(TOOL_SEND, draft_id, started, need_readonly=False)
    if refusal is not None or headers is None:
        return refusal or ""
    turn_id, session_id = _turn()
    status, grant = send_gate.begin_send(session_id, turn_id, draft_id)
    if status != "ok" or grant is None:
        send_gate.log_decision(decision="refused", reason=status, draft_id=draft_id, started=started)
        return _draft_refuse(TOOL_SEND, state=read_common.STATE_ERROR, reason=status, draft_id=draft_id)
    try:
        try:
            fetched = _fetch_draft(draft_id, headers)
        except google_http.GoogleHttpError:
            send_gate.clear_authorization(turn_id)
            send_gate.log_decision(
                decision="refused", reason=REASON_FETCH_FAILED, draft_id=draft_id, started=started
            )
            return _draft_refuse(
                TOOL_SEND, state=read_common.STATE_ERROR, reason=REASON_FETCH_FAILED, draft_id=draft_id
            )
        fields = send_gate.parse_draft(fetched)
        if fields.get("filenames"):
            send_gate.clear_authorization(turn_id)
            send_gate.log_decision(
                decision="refused", reason=REASON_ATTACHMENT, draft_id=draft_id, started=started
            )
            return _draft_refuse(
                TOOL_SEND, state=read_common.STATE_ERROR, reason=REASON_ATTACHMENT, draft_id=draft_id
            )
        fetched_hash = send_gate.hash_fields(fields)
        reviewed_hash = send_gate.live_hash(session_id)
        if reviewed_hash is None:
            send_gate.clear_authorization(turn_id)
            send_gate.log_decision(
                decision="refused",
                reason=send_gate.REASON_NOT_REVIEWED,
                draft_id=draft_id,
                started=started,
            )
            return _draft_refuse(
                TOOL_SEND,
                state=read_common.STATE_ERROR,
                reason=send_gate.REASON_NOT_REVIEWED,
                draft_id=draft_id,
            )
        if fetched_hash != grant.content_hash or fetched_hash != reviewed_hash:
            send_gate.clear_authorization(turn_id)
            send_gate.log_decision(
                decision="refused",
                reason=send_gate.REASON_CONTENT_CHANGED,
                draft_id=draft_id,
                started=started,
            )
            return _draft_refuse(
                TOOL_SEND,
                state=read_common.STATE_ERROR,
                reason=send_gate.REASON_CONTENT_CHANGED,
                draft_id=draft_id,
            )
        # P8-SEND: the re-check is the last step before drafts.send — P8-D06
        if send_gate.turn_changed(turn_id):
            send_gate.clear_authorization(turn_id)
            send_gate.log_decision(
                decision="refused",
                reason=send_gate.REASON_TURN_CHANGED,
                draft_id=draft_id,
                started=started,
            )
            return _draft_refuse(
                TOOL_SEND,
                state=read_common.STATE_ERROR,
                reason=send_gate.REASON_TURN_CHANGED,
                draft_id=draft_id,
            )
        try:
            google_http.request(
                "POST",
                DRAFTS_SEND_URL,
                headers=headers,
                json={"id": draft_id},
                timeout=30.0,
                route=google_http.ROUTE_GMAIL_DRAFTS_SEND,
            )
        except google_http.GoogleHttpError:
            send_gate.clear_authorization(turn_id)
            send_gate.log_decision(
                decision="refused", reason=REASON_SEND_FAILED, draft_id=draft_id, started=started
            )
            return _draft_refuse(
                TOOL_SEND, state=read_common.STATE_ERROR, reason=REASON_SEND_FAILED, draft_id=draft_id
            )
        send_gate.clear_authorization(turn_id)
        send_gate.drop_pending(session_id, draft_id)
        send_gate.log_decision(
            decision="sent",
            draft_id=draft_id,
            recipient_count=_recipient_count(fields),
            started=started,
        )
        return read_common.dump_result(
            TOOL_SEND,
            {"ok": True, "state": STATE_SENT, "draft_id": draft_id},
        )
    except Exception:
        send_gate.clear_authorization(turn_id)
        send_gate.log_decision(decision="refused", reason="internal_error", draft_id=draft_id, started=started)
        return _draft_refuse(TOOL_SEND, state=read_common.STATE_ERROR, reason="internal_error", draft_id=draft_id)


def gmail_draft_handler(args: dict, **kwargs) -> str:
    started = time.monotonic()
    try:
        return _draft_impl(args if isinstance(args, dict) else {})
    except Exception:
        send_gate.log_decision(decision="refused", reason="internal_error", started=started)
        return _draft_refuse(TOOL_DRAFT, state=read_common.STATE_ERROR, reason="internal_error")


def gmail_send_draft_handler(args: dict, **kwargs) -> str:
    return _send_impl(args if isinstance(args, dict) else {})
