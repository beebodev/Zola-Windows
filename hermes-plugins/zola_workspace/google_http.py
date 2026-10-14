"""Google HTTP transport — the only module that talks to Google (P8-D03)."""

from __future__ import annotations

import logging
import re
import time
from typing import Any, Callable, Dict, Mapping, MutableMapping, Optional
from urllib.parse import urlparse

# P8-CONNECT: named transport caps — P8-D03
DEFAULT_TIMEOUT_SECONDS = 30.0
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = (0.5, 1.0, 2.0)
RETRY_STATUS_CODES = frozenset({429, 500, 502, 503, 504})
LOG_PREFIX = "zola_workspace.google_http"

# P8-CONNECT-FIX: route labels; a missing label logs unlabeled, never a path — P8-D11
ROUTE_CALENDAR_LIST = "calendar.calendarList.list"
ROUTE_CALENDAR_EVENTS = "calendar.events.list"
ROUTE_OAUTH_CERTS = "oauth.certs"
ROUTE_OAUTH_TOKEN = "oauth.token"
ROUTE_GMAIL_LIST = "gmail.users.messages.list"
ROUTE_GMAIL_GET = "gmail.users.messages.get"
# P9-WATCH: background routes; tool calls do not use these — P9-D04
ROUTE_GMAIL_PROFILE = "gmail.users.getProfile"
ROUTE_GMAIL_HISTORY = "gmail.users.history.list"
# P8-SEND: draft routes only; the messages-send route is not a constant here — P8-D06
ROUTE_GMAIL_DRAFTS_CREATE = "gmail.users.drafts.create"
ROUTE_GMAIL_DRAFTS_UPDATE = "gmail.users.drafts.update"
ROUTE_GMAIL_DRAFTS_GET = "gmail.users.drafts.get"
ROUTE_GMAIL_DRAFTS_DELETE = "gmail.users.drafts.delete"
ROUTE_GMAIL_DRAFTS_SEND = "gmail.users.drafts.send"
ROUTE_DRIVE_LIST = "drive.files.list"
ROUTE_DRIVE_GET = "drive.files.get"
ROUTE_DRIVE_EXPORT = "drive.files.export"
ROUTE_CONTACTS_SEARCH = "people.people.searchContacts"

_logger = logging.getLogger("zola_workspace.google_http")

# Injectable transport for unit tests (no network).
# Signature: (method, url, *, headers, params, data, json, timeout) -> ResponseLike
_transport: Optional[Callable[..., Any]] = None


_BACKGROUND_CAPABILITY = object()
_BACKGROUND_ONLY = frozenset({ROUTE_GMAIL_PROFILE, ROUTE_GMAIL_HISTORY})
_MESSAGE_ID = re.compile(r"^[A-Za-z0-9_-]+$")
_NEWER_THAN = re.compile(r"^newer_than:\d+d$")
_GMAIL_GET_FIELDS = "id,threadId,labelIds,snippet,payload,internalDate"
_CALENDAR_EVENT_FIELDS = (
    "items(id,updated,status,start,end,recurringEventId,originalStartTime),"
    "nextPageToken,nextSyncToken"
)
_CALENDAR_LIST_FIELDS = "items(id,selected),nextPageToken"
_CALENDAR_SYNC_FORBIDDEN = frozenset(
    {"timemin", "timemax", "orderby", "q", "singleevents", "icaluid", "updatedmin"}
)


def background_capability() -> object:
    """Token the watcher passes so request() enforces the fixed operation list."""
    return _BACKGROUND_CAPABILITY


class AllowlistError(Exception):
    """The background call is not on the fixed list. No HTTP was attempted."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class GoogleHttpError(Exception):
    """Base error for Google HTTP failures (never embeds secrets)."""

    def __init__(self, message: str, *, status: Optional[int] = None) -> None:
        super().__init__(message)
        self.status = status


class GoogleHttpTimeout(GoogleHttpError):
    """Request timed out."""


class GoogleHttpStatusError(GoogleHttpError):
    """Non-success HTTP status after retries exhausted (or non-retryable)."""

    def __init__(
        self,
        message: str,
        *,
        status: Optional[int] = None,
        body_text: str = "",
    ) -> None:
        super().__init__(message, status=status)
        # Body kept for callers that must classify OAuth errors; never logged.
        self.body_text = body_text if isinstance(body_text, str) else ""

    def json(self) -> Any:
        import json as _json

        if not self.body_text:
            return {}
        return _json.loads(self.body_text)


class GoogleHttpTransportError(GoogleHttpError):
    """Connection / transport failure."""


class GoogleHttpResponse:
    """Minimal response object returned by the default requests transport."""

    def __init__(
        self,
        status_code: int,
        text: str,
        headers: Optional[Mapping[str, str]] = None,
        content: Optional[bytes] = None,
    ) -> None:
        self.status_code = int(status_code)
        self.headers = dict(headers or {})
        # P8-READ: raw bytes are the body. Text is a separate view and must not
        # be re-encoded over content — that corrupts PDF media — P8-D08
        if isinstance(content, (bytes, bytearray)):
            self.content = bytes(content)
        elif isinstance(text, str):
            self.content = text.encode("utf-8")
        else:
            self.content = b""
        self.text = text if isinstance(text, str) else ""

    def json(self) -> Any:
        import json as _json

        return _json.loads(self.text)


def set_transport_for_tests(fn: Optional[Callable[..., Any]]) -> None:
    """Install or clear a fake transport (unit tests only)."""
    global _transport
    _transport = fn


def reset_transport_for_tests() -> None:
    set_transport_for_tests(None)


def _log_event(event: str, **fields: Any) -> None:
    parts = [f"{LOG_PREFIX}.{event}"]
    for key, value in fields.items():
        if value is None:
            parts.append(f"{key}=-")
        else:
            parts.append(f"{key}={value}")
    try:
        _logger.info(" ".join(parts))
    except Exception:
        pass


def _default_transport(
    method: str,
    url: str,
    *,
    headers: Optional[Mapping[str, str]],
    params: Optional[Mapping[str, Any]],
    data: Any,
    json: Any,
    timeout: float,
) -> GoogleHttpResponse:
    import requests

    try:
        resp = requests.request(
            method=method.upper(),
            url=url,
            headers=dict(headers or {}),
            params=dict(params) if params else None,
            data=data,
            json=json,
            timeout=timeout,
        )
    except requests.Timeout as exc:
        raise GoogleHttpTimeout("timeout") from exc
    except requests.RequestException as exc:
        raise GoogleHttpTransportError("transport_error") from exc
    raw = getattr(resp, "content", None)
    content = bytes(raw) if isinstance(raw, (bytes, bytearray)) else b""
    # Decode only the text view. Never rebuild content from resp.text.
    text = content.decode("utf-8", "replace")
    return GoogleHttpResponse(resp.status_code, text, dict(resp.headers), content=content)


def _route_for_log(route: Optional[str]) -> str:
    """Named route, or unlabeled. Never a URL path."""
    # P8-CONNECT-FIX: missing route logs unlabeled — P8-D11
    text = str(route or "").strip()
    return text if text else "unlabeled"


def _refuse_allowlist(route_label: str, reason: str) -> None:
    # P9-WATCH: a refusal is a WARN and happens before the transport — P9-D04
    try:
        _logger.warning("%s.refused route=%s reason=%s", LOG_PREFIX, route_label, reason)
    except Exception:
        pass
    raise AllowlistError(reason)


def _param_map(params: Optional[Mapping[str, Any]]) -> Dict[str, str]:
    found: Dict[str, str] = {}
    for key, value in (params or {}).items():
        found[str(key)] = "" if value is None else str(value)
    return found


def _check_background(method: str, url: str, route: str, params: Optional[Mapping[str, Any]]) -> None:
    # P9-WATCH: route, path shape, and parameters are fixed before any HTTP — P9-D04
    if method.upper() != "GET":
        _refuse_allowlist(route or "unlabeled", "method")
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.query or parsed.fragment:
        _refuse_allowlist(route or "unlabeled", "url")
    host = (parsed.hostname or "").casefold()
    gmail_routes = {
        ROUTE_GMAIL_PROFILE,
        ROUTE_GMAIL_HISTORY,
        ROUTE_GMAIL_LIST,
        ROUTE_GMAIL_GET,
    }
    calendar_routes = {ROUTE_CALENDAR_LIST, ROUTE_CALENDAR_EVENTS}
    if route in gmail_routes and host != "gmail.googleapis.com":
        _refuse_allowlist(route, "host")
    if route in calendar_routes and host != "www.googleapis.com":
        _refuse_allowlist(route, "host")
    path = parsed.path
    query = _param_map(params)
    lowered = {key.casefold() for key in query}
    if route == ROUTE_GMAIL_PROFILE:
        if path != "/gmail/v1/users/me/profile" or query:
            _refuse_allowlist(route, "profile")
        return
    if route == ROUTE_GMAIL_HISTORY:
        allowed = {"starthistoryid", "historytypes", "labelid", "pagetoken", "maxresults"}
        if path != "/gmail/v1/users/me/history" or not lowered <= allowed:
            _refuse_allowlist(route, "history")
        if "startHistoryId" not in query:
            _refuse_allowlist(route, "history")
        if query.get("historyTypes") not in (None, "messageAdded"):
            _refuse_allowlist(route, "history_type")
        if query.get("labelId") not in (None, "INBOX"):
            _refuse_allowlist(route, "label")
        return
    if route == ROUTE_GMAIL_LIST:
        allowed = {"labelids", "q", "pagetoken", "maxresults"}
        if path != "/gmail/v1/users/me/messages" or not lowered <= allowed:
            _refuse_allowlist(route, "list")
        if query.get("labelIds") != "INBOX":
            _refuse_allowlist(route, "label")
        if not _NEWER_THAN.match(query.get("q") or ""):
            _refuse_allowlist(route, "query")
        return
    if route == ROUTE_GMAIL_GET:
        prefix = "/gmail/v1/users/me/messages/"
        message_id = path[len(prefix):] if path.startswith(prefix) else ""
        if not _MESSAGE_ID.match(message_id):
            _refuse_allowlist(route, "path")
        if query.get("format") != "full" or query.get("fields") != _GMAIL_GET_FIELDS:
            _refuse_allowlist(route, "fields")
        extra = lowered - {"format", "fields"}
        if extra:
            _refuse_allowlist(route, "parameter")
        return
    if route == ROUTE_CALENDAR_LIST:
        if path != "/calendar/v3/users/me/calendarList":
            _refuse_allowlist(route, "path")
        if not lowered <= {"maxresults", "pagetoken", "fields"}:
            _refuse_allowlist(route, "parameter")
        if query.get("fields") != _CALENDAR_LIST_FIELDS:
            _refuse_allowlist(route, "fields")
        return
    if route == ROUTE_CALENDAR_EVENTS:
        marker = "/calendars/"
        if not path.startswith("/calendar/v3") or marker not in path or not path.endswith("/events"):
            _refuse_allowlist(route, "path")
        # P9-WATCH: the id is one encoded segment; a raw # @ or / is not a path — P9-D04
        ident = path[path.find(marker) + len(marker) : -len("/events")]
        if not ident or any(char in ident for char in "/@#?"):
            _refuse_allowlist(route, "path")
        if lowered & _CALENDAR_SYNC_FORBIDDEN:
            _refuse_allowlist(route, "parameter")
        if not lowered <= {"showdeleted", "maxresults", "pagetoken", "synctoken", "fields"}:
            _refuse_allowlist(route, "parameter")
        if query.get("showDeleted") not in (None, "true"):
            _refuse_allowlist(route, "show_deleted")
        if query.get("fields") != _CALENDAR_EVENT_FIELDS:
            _refuse_allowlist(route, "fields")
        return
    _refuse_allowlist(route or "unlabeled", "route")


def request(
    method: str,
    url: str,
    *,
    headers: Optional[Mapping[str, str]] = None,
    params: Optional[Mapping[str, Any]] = None,
    data: Any = None,
    json: Any = None,
    timeout: Optional[float] = None,
    route: Optional[str] = None,
    capability: Any = None,
) -> GoogleHttpResponse:
    """Perform one Google HTTP call with bounded 5xx/429 retry and backoff.

    Never logs query strings, headers, bodies, or URL paths.
    """
    # P8-CONNECT: sole Google HTTP entry; timeouts + bounded retry — P8-D03
    # P8-CONNECT-FIX: log route= only — P8-D11
    # P9-WATCH: the background capability turns the allowlist on; tool calls omit it — P9-D04
    route_label = _route_for_log(route)
    if capability is not None:
        if capability is not _BACKGROUND_CAPABILITY:
            _refuse_allowlist(route_label, "capability")
        _check_background(method, url, route or "", params)
    elif route in _BACKGROUND_ONLY:
        _refuse_allowlist(route_label, "capability")
    timeout_s = float(DEFAULT_TIMEOUT_SECONDS if timeout is None else timeout)
    transport = _transport or _default_transport
    last_status: Optional[int] = None
    attempts = 0
    while True:
        attempts += 1
        try:
            resp = transport(
                method,
                url,
                headers=headers,
                params=params,
                data=data,
                json=json,
                timeout=timeout_s,
            )
        except GoogleHttpTimeout:
            _log_event("timeout", method=method.upper(), route=route_label, attempt=attempts)
            raise
        except GoogleHttpTransportError:
            _log_event(
                "transport_error", method=method.upper(), route=route_label, attempt=attempts
            )
            raise
        except GoogleHttpError:
            raise
        except Exception as exc:
            _log_event(
                "transport_error", method=method.upper(), route=route_label, attempt=attempts
            )
            raise GoogleHttpTransportError("transport_error") from exc

        status = int(getattr(resp, "status_code", 0) or 0)
        last_status = status
        if 200 <= status < 300:
            _log_event(
                "ok", method=method.upper(), route=route_label, status=status, attempt=attempts
            )
            if isinstance(resp, GoogleHttpResponse):
                return resp
            hdrs = getattr(resp, "headers", {}) or {}
            raw = getattr(resp, "content", None)
            if isinstance(raw, (bytes, bytearray)):
                content = bytes(raw)
                text = content.decode("utf-8", "replace")
            else:
                text = getattr(resp, "text", "") or ""
                content = text.encode("utf-8") if isinstance(text, str) else b""
            return GoogleHttpResponse(status, text, hdrs, content=content)

        retryable = status in RETRY_STATUS_CODES
        if (not retryable) or attempts > MAX_RETRIES:
            _log_event(
                "status_error",
                method=method.upper(),
                route=route_label,
                status=status,
                attempt=attempts,
            )
            body_text = getattr(resp, "text", "") or ""
            raise GoogleHttpStatusError(
                f"http_{status}",
                status=status,
                body_text=body_text,
            )

        backoff_idx = min(attempts - 1, len(RETRY_BACKOFF_SECONDS) - 1)
        delay = RETRY_BACKOFF_SECONDS[backoff_idx]
        _log_event(
            "retry",
            method=method.upper(),
            route=route_label,
            status=status,
            attempt=attempts,
            backoff_s=delay,
        )
        time.sleep(delay)

    # Unreachable; keeps type checkers happy
    raise GoogleHttpStatusError(f"http_{last_status or 0}", status=last_status)
