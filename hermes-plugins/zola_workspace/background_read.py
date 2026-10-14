"""Fixed Google reads for the watcher (P9-D04).

Tool handlers are not called. The background capability is what turns the
allowlist on inside google_http.request.
"""

from __future__ import annotations

import base64
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

try:
    from . import auth
    from . import google_http
    from . import textclean
except ImportError:
    import auth
    import google_http
    import textclean

GMAIL_PROFILE_URL = "https://gmail.googleapis.com/gmail/v1/users/me/profile"
GMAIL_HISTORY_URL = "https://gmail.googleapis.com/gmail/v1/users/me/history"
GMAIL_LIST_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages"
GMAIL_GET_TMPL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}"
CALENDAR_LIST_URL = "https://www.googleapis.com/calendar/v3/users/me/calendarList"
CALENDAR_EVENTS_TMPL = "https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events"

GMAIL_GET_FIELDS = "id,threadId,labelIds,snippet,payload,internalDate"
CALENDAR_LIST_FIELDS = "items(id,selected),nextPageToken"
CALENDAR_EVENT_FIELDS = (
    "items(id,updated,status,start,end,recurringEventId,originalStartTime),"
    "nextPageToken,nextSyncToken"
)
HISTORY_PAGE = 100
RECOVERY_PAGE = 50
CALENDAR_PAGE = 250


class ReadError(Exception):
    def __init__(self, reason: str, *, status: Optional[int] = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.status = status


def _headers() -> Dict[str, str]:
    return auth.authorization_header()


def _get(url: str, *, route: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    try:
        response = google_http.request(
            "GET",
            url,
            headers=_headers(),
            params=params,
            timeout=30.0,
            route=route,
            capability=google_http.background_capability(),
        )
        body = response.json()
    except google_http.GoogleHttpStatusError as exc:
        raise ReadError("http", status=exc.status) from exc
    except google_http.AllowlistError as exc:
        raise ReadError(exc.reason) from exc
    except google_http.GoogleHttpError as exc:
        raise ReadError("transport") from exc
    if not isinstance(body, dict):
        raise ReadError("shape")
    return body


def gmail_profile() -> Dict[str, str]:
    # P9-WATCH: historyId only; the address in the payload is dropped — P9-D04
    body = _get(GMAIL_PROFILE_URL, route=google_http.ROUTE_GMAIL_PROFILE)
    history_id = str(body.get("historyId") or "")
    if not history_id:
        raise ReadError("profile")
    return {"history_id": history_id}


def gmail_history(start_history_id: str, page_token: str = "") -> Dict[str, Any]:
    params: Dict[str, Any] = {
        "startHistoryId": start_history_id,
        "historyTypes": "messageAdded",
        "labelId": "INBOX",
        "maxResults": HISTORY_PAGE,
    }
    if page_token:
        params["pageToken"] = page_token
    body = _get(GMAIL_HISTORY_URL, route=google_http.ROUTE_GMAIL_HISTORY, params=params)
    added: List[Dict[str, str]] = []
    for record in body.get("history") or []:
        if not isinstance(record, dict):
            continue
        for entry in record.get("messagesAdded") or []:
            if not isinstance(entry, dict):
                continue
            message = entry.get("message") or {}
            if not isinstance(message, dict):
                continue
            message_id = str(message.get("id") or "")
            if message_id:
                added.append(
                    {"message_id": message_id, "thread_id": str(message.get("threadId") or "")}
                )
    return {
        "added": added,
        "next_page_token": str(body.get("nextPageToken") or ""),
        "history_id": str(body.get("historyId") or ""),
    }


def gmail_recovery_list(window_days: int, page_token: str = "") -> Dict[str, Any]:
    params: Dict[str, Any] = {
        "labelIds": "INBOX",
        "q": f"newer_than:{int(window_days)}d",
        "maxResults": RECOVERY_PAGE,
    }
    if page_token:
        params["pageToken"] = page_token
    body = _get(GMAIL_LIST_URL, route=google_http.ROUTE_GMAIL_LIST, params=params)
    messages = []
    for item in body.get("messages") or []:
        if isinstance(item, dict) and item.get("id"):
            messages.append(
                {"message_id": str(item["id"]), "thread_id": str(item.get("threadId") or "")}
            )
    return {"messages": messages, "next_page_token": str(body.get("nextPageToken") or "")}


def _decode(data: str) -> str:
    pad = "=" * (-len(data) % 4)
    raw = base64.urlsafe_b64decode(data + pad)
    return raw.decode("utf-8", "replace")


def _walk(payload: Dict[str, Any]):
    yield payload
    for part in payload.get("parts") or []:
        if isinstance(part, dict):
            yield from _walk(part)


def _message_text(payload: Dict[str, Any]) -> str:
    plain: List[str] = []
    html_parts: List[str] = []
    for part in _walk(payload):
        if str(part.get("filename") or ""):
            continue
        body = part.get("body") or {}
        if not isinstance(body, dict) or body.get("attachmentId") or not body.get("data"):
            continue
        text = _decode(str(body["data"]))
        mime = str(part.get("mimeType") or "").casefold()
        if mime == "text/plain":
            plain.append(text)
        elif mime == "text/html":
            html_parts.append(text)
    if plain:
        excerpt, _truncated, _total = textclean.prepare_body("\n".join(plain), html=False)
        return excerpt
    if html_parts:
        excerpt, _truncated, _total = textclean.prepare_body("\n".join(html_parts), html=True)
        return excerpt
    return ""


def _header_map(payload: Dict[str, Any]) -> Dict[str, str]:
    found: Dict[str, str] = {}
    for item in payload.get("headers") or []:
        if isinstance(item, dict):
            found[str(item.get("name") or "").casefold()] = str(item.get("value") or "")
    return found


def _from_header(value: str) -> Tuple[str, str]:
    text = (value or "").strip()
    if text.endswith(">") and "<" in text:
        name, address = text.rsplit("<", 1)
        return name.strip().strip('"'), address[:-1].strip()
    return "", text


def gmail_message(message_id: str) -> Dict[str, Any]:
    body = _get(
        GMAIL_GET_TMPL.format(message_id=message_id),
        route=google_http.ROUTE_GMAIL_GET,
        params={"format": "full", "fields": GMAIL_GET_FIELDS},
    )
    payload = body.get("payload") if isinstance(body.get("payload"), dict) else {}
    headers = _header_map(payload)
    name, address = _from_header(headers.get("from", ""))
    return {
        "message_id": str(body.get("id") or message_id),
        "thread_id": str(body.get("threadId") or ""),
        "from_name": name,
        "from_address": address,
        "subject": headers.get("subject", ""),
        "snippet": str(body.get("snippet") or ""),
        "body": _message_text(payload),
        "labels": [str(item) for item in (body.get("labelIds") or [])],
        "internal_date": str(body.get("internalDate") or ""),
    }


def calendar_ids(page_token: str = "") -> Dict[str, Any]:
    params: Dict[str, Any] = {"maxResults": 250, "fields": CALENDAR_LIST_FIELDS}
    if page_token:
        params["pageToken"] = page_token
    body = _get(CALENDAR_LIST_URL, route=google_http.ROUTE_CALENDAR_LIST, params=params)
    selected = []
    for item in body.get("items") or []:
        if isinstance(item, dict) and item.get("selected") is True and item.get("id"):
            selected.append(str(item["id"]))
    return {"ids": selected, "next_page_token": str(body.get("nextPageToken") or "")}


def _when(value: Any) -> str:
    if not isinstance(value, dict):
        return ""
    return str(value.get("dateTime") or value.get("date") or "")


def calendar_events(
    calendar_id: str,
    *,
    page_token: str = "",
    sync_token: str = "",
) -> Dict[str, Any]:
    params: Dict[str, Any] = {
        "showDeleted": "true",
        "maxResults": CALENDAR_PAGE,
        "fields": CALENDAR_EVENT_FIELDS,
    }
    if sync_token:
        params["syncToken"] = sync_token
    if page_token:
        params["pageToken"] = page_token
    # P9-WATCH: quote the id the same way gcal does, so # stays in the path — P9-D04
    body = _get(
        CALENDAR_EVENTS_TMPL.format(calendar_id=quote(calendar_id, safe="")),
        route=google_http.ROUTE_CALENDAR_EVENTS,
        params=params,
    )
    events = []
    for item in body.get("items") or []:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        original = item.get("originalStartTime")
        events.append(
            {
                "event_id": str(item.get("id") or ""),
                "event_updated": str(item.get("updated") or ""),
                "calendar_status": str(item.get("status") or ""),
                "start_at": _when(item.get("start")),
                "end_at": _when(item.get("end")),
                "recurring_event_id": str(item.get("recurringEventId") or ""),
                "original_start": _when(original),
            }
        )
    return {
        "events": events,
        "next_page_token": str(body.get("nextPageToken") or ""),
        "next_sync_token": str(body.get("nextSyncToken") or ""),
    }
