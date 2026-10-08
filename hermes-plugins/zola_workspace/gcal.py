"""calendar_query — synchronous Google Calendar read (P8-D08 / P8-D10)."""

from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
from zoneinfo import ZoneInfo

try:
    from . import auth
    from . import framing
    from . import google_http
    from . import log as wslog
    from . import taint
    from . import turn_context
except ImportError:  # P8-CONNECT: flat unittest discover — P8-D08
    import auth
    import framing
    import google_http
    import log as wslog
    import taint
    import turn_context

# P8-CONNECT: named calendar caps / windows / states — P8-D08 / P8-D10
TOOL_NAME = "calendar_query"
TOOLSET_NAME = "zola_workspace"

MAX_RESULTS_DEFAULT = 10
MAX_RESULTS_CAP = 25
LOOKBACK_DAYS = 730
FORWARD_DAYS = 90
MOST_RECENT_CHUNK_DAYS = 30
MAX_PAGES_PER_CALENDAR = 10
EVENTS_PAGE_SIZE = 100

ORDER_SOONEST = "soonest"
ORDER_MOST_RECENT = "most_recent"
ORDERS = frozenset({ORDER_SOONEST, ORDER_MOST_RECENT})

STATE_COMPLETE = "complete"
STATE_NO_MATCH = "no_match"
STATE_INCOMPLETE = "incomplete"
STATE_NEEDS_RECONNECT = "needs_reconnect"
STATE_ERROR = "error"

REASON_NOT_BRIAN = "not_brian_turn"
REASON_TAINT_WRITE_FAILED = "taint_write_failed"
REASON_BAD_ARGS = "bad_args"
REASON_MISSING_CALENDAR_SCOPE = "missing_calendar_scope"

TZ_SOURCE_CALENDAR_PRIMARY = "calendar_primary"
TZ_SOURCE_LOCAL = "local"

RESPONSE_ORGANIZER = "organizer"
RESPONSE_NONE = "none"

CALENDAR_LIST_URL = "https://www.googleapis.com/calendar/v3/users/me/calendarList"
EVENTS_URL_TMPL = "https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events"

_CALENDAR_DESCRIPTION = (
    "Search Brian's selected Google Calendars. Pass an optional text query and/or "
    "explicit ISO-8601 start/end with offsets. order is 'soonest' or 'most_recent'. "
    "Does not parse natural-language dates."
)

_CALENDAR_SCHEMA: Dict[str, Any] = {
    "name": TOOL_NAME,
    "description": _CALENDAR_DESCRIPTION,
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Optional free-text calendar search (Google q=).",
            },
            "start": {
                "type": "string",
                "description": "Optional ISO-8601 start with offset (e.g. 2026-10-07T00:00:00-07:00).",
            },
            "end": {
                "type": "string",
                "description": "Optional ISO-8601 end with offset.",
            },
            "order": {
                "type": "string",
                "enum": [ORDER_SOONEST, ORDER_MOST_RECENT],
                "description": "soonest (ascending upcoming) or most_recent (latest past matches).",
            },
            "max_results": {
                "type": "integer",
                "minimum": 1,
                "maximum": MAX_RESULTS_CAP,
                "description": f"1–{MAX_RESULTS_CAP}; default {MAX_RESULTS_DEFAULT}.",
            },
        },
        "additionalProperties": False,
    },
}


def calendar_schema() -> Dict[str, Any]:
    return dict(_CALENDAR_SCHEMA)


def _parse_iso_offset(value: str, field: str) -> datetime:
    raw = str(value or "").strip()
    if not raw:
        raise ValueError(field)
    # P8-CONNECT: NO natural-language date parsing; ISO-8601 with offset only — P8-D08
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        raise ValueError(f"{field}_missing_offset")
    return dt


def _clamp_window(
    start: Optional[datetime],
    end: Optional[datetime],
    *,
    order: str,
    now: datetime,
) -> Tuple[datetime, datetime, bool]:
    """Return (start, end, was_clamped) within −730 / +90 days of now.

    Raises ValueError when end < start (bad_args — no silent default).
    """
    lo = now - timedelta(days=LOOKBACK_DAYS)
    hi = now + timedelta(days=FORWARD_DAYS)
    clamped = False
    if start is None and end is None:
        if order == ORDER_MOST_RECENT:
            start, end = lo, now
        else:
            start, end = now, hi
    elif start is None:
        start = lo
        clamped = True
    elif end is None:
        end = hi
        clamped = True
    assert start is not None and end is not None
    # P8-CONNECT: end < start → bad_args (no silent swap) — P8-D08
    if end < start:
        raise ValueError(REASON_BAD_ARGS)
    if start < lo:
        start = lo
        clamped = True
    if end > hi:
        end = hi
        clamped = True
    if end < start:
        raise ValueError(REASON_BAD_ARGS)
    return start, end, clamped


def _rfc3339(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_tz(name: str):
    try:
        return ZoneInfo(name)
    except Exception:
        return None


def _pc_local_timezone_name() -> str:
    """IANA or offset name for the PC local zone — never silent UTC."""
    # P8-CONNECT: fallback is PC local + timezone_source, never silent UTC — P8-D08
    local = datetime.now().astimezone()
    tzinfo = local.tzinfo
    if tzinfo is None:
        # Extremely defensive — still surface an offset, not bare UTC
        return "local"
    key = getattr(tzinfo, "key", None)
    if isinstance(key, str) and key:
        return key
    name = getattr(tzinfo, "zone", None)
    if isinstance(name, str) and name:
        return name
    # Offset-based: e.g. UTC-07:00
    off = local.utcoffset()
    if off is not None:
        total = int(off.total_seconds())
        sign = "+" if total >= 0 else "-"
        total = abs(total)
        hours, rem = divmod(total, 3600)
        mins = rem // 60
        return f"UTC{sign}{hours:02d}:{mins:02d}"
    return str(tzinfo)


def _format_in_tz(dt: Optional[datetime], tz) -> Optional[str]:
    if dt is None:
        return None
    return dt.astimezone(tz).isoformat()


def _event_bounds(event: Dict[str, Any], tz) -> Tuple[Optional[datetime], Optional[datetime], bool]:
    start = event.get("start") or {}
    end = event.get("end") or {}
    all_day = False
    start_dt: Optional[datetime] = None
    end_dt: Optional[datetime] = None
    if start.get("date") and not start.get("dateTime"):
        all_day = True
        d0 = datetime.fromisoformat(str(start["date"]))
        start_dt = d0.replace(tzinfo=tz)
        if end.get("date"):
            d1 = datetime.fromisoformat(str(end["date"]))
            end_dt = d1.replace(tzinfo=tz)
    else:
        if start.get("dateTime"):
            start_dt = datetime.fromisoformat(str(start["dateTime"]).replace("Z", "+00:00"))
        if end.get("dateTime"):
            end_dt = datetime.fromisoformat(str(end["dateTime"]).replace("Z", "+00:00"))
    return start_dt, end_dt, all_day


def _brian_response_status(event: Dict[str, Any]) -> str:
    """Brian's attendee responseStatus, or organizer / none."""
    # P8-CONNECT: response_status per item — P8-D08
    for att in event.get("attendees") or []:
        if isinstance(att, dict) and att.get("self") is True:
            status = att.get("responseStatus")
            if status:
                return str(status)
    organizer = event.get("organizer") or {}
    if isinstance(organizer, dict) and organizer.get("self") is True:
        return RESPONSE_ORGANIZER
    return RESPONSE_NONE


def _shape_event(event: Dict[str, Any], *, calendar_name: str, tz) -> Dict[str, Any]:
    start_dt, end_dt, all_day = _event_bounds(event, tz)
    attendees = []
    for att in event.get("attendees") or []:
        if isinstance(att, dict):
            name = att.get("displayName") or att.get("email") or ""
            if name:
                attendees.append(str(name))
    return {
        "start": _format_in_tz(start_dt, tz),
        "end": _format_in_tz(end_dt, tz),
        "all_day": all_day,
        "title": str(event.get("summary") or ""),
        "location": str(event.get("location") or ""),
        "attendees": attendees,
        "calendar_name": calendar_name,
        "response_status": _brian_response_status(event),
        "_start_dt": start_dt,
    }


def _google_get(
    url: str,
    *,
    headers: Dict[str, str],
    route: str,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    # P8-CONNECT-FIX: every Google call passes a route constant — P8-D11
    resp = google_http.request(
        "GET", url, headers=headers, params=params, timeout=30.0, route=route
    )
    return resp.json()


def _calendar_list(headers: Dict[str, str]) -> List[Dict[str, Any]]:
    body = _google_get(
        CALENDAR_LIST_URL,
        headers=headers,
        params={"maxResults": 250},
        route=google_http.ROUTE_CALENDAR_LIST,
    )
    items = body.get("items") or []
    return [c for c in items if isinstance(c, dict)]


def _selected_calendars(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [c for c in items if c.get("selected") is True]


def _resolve_timezone(items: List[Dict[str, Any]]) -> Tuple[str, str, Any]:
    """Return (tz_name, timezone_source, tzinfo). Never silent UTC."""
    # P8-CONNECT: timeZone from calendarList primary==true — P8-D08
    for c in items:
        if c.get("primary") is True:
            tz_name = str(c.get("timeZone") or "").strip()
            if tz_name:
                tz = _load_tz(tz_name)
                if tz is not None:
                    return tz_name, TZ_SOURCE_CALENDAR_PRIMARY, tz
            break
    local_name = _pc_local_timezone_name()
    tz = _load_tz(local_name)
    if tz is None:
        # Offset / unknown name — use system local tzinfo directly
        tz = datetime.now().astimezone().tzinfo or timezone(timedelta(0))
    return local_name, TZ_SOURCE_LOCAL, tz


def _list_events_for_calendar(
    calendar_id: str,
    *,
    headers: Dict[str, str],
    time_min: datetime,
    time_max: datetime,
    query: str,
) -> Tuple[List[Dict[str, Any]], bool]:
    """Return (events, incomplete). incomplete if page fail or page-cap hit."""
    events: List[Dict[str, Any]] = []
    page_token: Optional[str] = None
    pages = 0
    while True:
        if pages >= MAX_PAGES_PER_CALENDAR:
            # P8-CONNECT: per-calendar page cap → incomplete — P8-D08
            return events, True
        params: Dict[str, Any] = {
            "singleEvents": "true",
            "orderBy": "startTime",
            "timeMin": _rfc3339(time_min),
            "timeMax": _rfc3339(time_max),
            "maxResults": EVENTS_PAGE_SIZE,
        }
        if query:
            params["q"] = query
        if page_token:
            params["pageToken"] = page_token
        url = EVENTS_URL_TMPL.format(calendar_id=calendar_id)
        try:
            body = _google_get(
                url,
                headers=headers,
                params=params,
                route=google_http.ROUTE_CALENDAR_EVENTS,
            )
        except Exception:
            return events, True
        pages += 1
        for item in body.get("items") or []:
            if isinstance(item, dict):
                events.append(item)
        page_token = body.get("nextPageToken")
        if not page_token:
            return events, False


def _sort_key_dt(item: Dict[str, Any]) -> datetime:
    # P8-CONNECT: sort by parsed datetime, not string — P8-D08
    dt = item.get("_start_dt")
    if isinstance(dt, datetime):
        return dt
    raw = item.get("start")
    if isinstance(raw, str) and raw:
        try:
            return datetime.fromisoformat(raw)
        except Exception:
            pass
    return datetime.min.replace(tzinfo=timezone.utc)


def _strip_internal(item: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in item.items() if not k.startswith("_")}


def _refuse(state: str, reason: str, **extra: Any) -> str:
    payload = {"ok": False, "state": state, "reason": reason, "items": [], **extra}
    return framing.frame_untrusted(TOOL_NAME, json.dumps(payload, ensure_ascii=False))


def _ids_for_turn() -> Tuple[str, str]:
    tid = turn_context.current_turn_id_from_context()
    rec = turn_context.get_record(tid) if tid else None
    if rec is None:
        return "", ""
    return str(rec.session_id or ""), str(rec.task_id or "")


def calendar_query_handler(args: dict, **kwargs) -> str:
    """Synchronous calendar_query. Never raises."""
    started = time.monotonic()
    try:
        return _calendar_query_impl(args if isinstance(args, dict) else {})
    except Exception:
        try:
            wslog.write_event(
                wslog.LOG_EVENT_CALENDAR_QUERY,
                state=STATE_ERROR,
                count=0,
                ms=int((time.monotonic() - started) * 1000),
            )
        except Exception:
            pass
        return _refuse(STATE_ERROR, "internal_error")


def _collect_most_recent_with_query(
    *,
    calendars: List[Dict[str, Any]],
    headers: Dict[str, str],
    win_start: datetime,
    win_end: datetime,
    query: str,
    tz,
) -> Tuple[List[Dict[str, Any]], bool]:
    """One full-window paged search per calendar. Caller keeps the latest."""
    # P8-CONNECT-FIX: most_recent with q skips 30-day chunks — P8-D08
    all_shaped: List[Dict[str, Any]] = []
    incomplete = False
    seen_keys: Set[Tuple[str, str]] = set()
    from urllib.parse import quote

    for cal in calendars:
        cal_id = str(cal.get("id") or "")
        if not cal_id:
            continue
        cal_name = str(cal.get("summary") or cal_id)
        enc_id = quote(cal_id, safe="")
        raw_events, page_incomplete = _list_events_for_calendar(
            enc_id,
            headers=headers,
            time_min=win_start,
            time_max=win_end,
            query=query,
        )
        if page_incomplete:
            incomplete = True
        for ev in raw_events:
            eid = str(ev.get("id") or "")
            if eid:
                key = (cal_id, eid)
                if key in seen_keys:
                    continue
                seen_keys.add(key)
            all_shaped.append(_shape_event(ev, calendar_name=cal_name, tz=tz))
    all_shaped.sort(key=_sort_key_dt, reverse=True)
    return all_shaped, incomplete


def _collect_most_recent(
    *,
    calendars: List[Dict[str, Any]],
    headers: Dict[str, str],
    win_start: datetime,
    win_end: datetime,
    query: str,
    max_results: int,
    tz,
) -> Tuple[List[Dict[str, Any]], bool]:
    """Search backward in MOST_RECENT_CHUNK_DAYS windows until max_results filled.

    A non-empty query uses one full-window search per calendar instead.
    """
    # P8-CONNECT: most_recent backward 30-day chunks from now — P8-D08
    if str(query or "").strip():
        return _collect_most_recent_with_query(
            calendars=calendars,
            headers=headers,
            win_start=win_start,
            win_end=win_end,
            query=str(query).strip(),
            tz=tz,
        )
    all_shaped: List[Dict[str, Any]] = []
    incomplete = False
    cursor = win_end
    from urllib.parse import quote

    # De-dupe multi-day events that span chunk boundaries before counting
    seen_keys: Set[Tuple[str, str]] = set()

    while cursor > win_start and len(all_shaped) < max_results:
        chunk_end = cursor
        chunk_start = max(win_start, cursor - timedelta(days=MOST_RECENT_CHUNK_DAYS))
        chunk_items: List[Tuple[str, str, Dict[str, Any]]] = []
        for cal in calendars:
            cal_id = str(cal.get("id") or "")
            if not cal_id:
                continue
            cal_name = str(cal.get("summary") or cal_id)
            enc_id = quote(cal_id, safe="")
            raw_events, page_incomplete = _list_events_for_calendar(
                enc_id,
                headers=headers,
                time_min=chunk_start,
                time_max=chunk_end,
                query=query,
            )
            if page_incomplete:
                incomplete = True
            for ev in raw_events:
                eid = str(ev.get("id") or "")
                shaped = _shape_event(ev, calendar_name=cal_name, tz=tz)
                chunk_items.append((cal_id, eid, shaped))
        chunk_items.sort(key=lambda t: _sort_key_dt(t[2]), reverse=True)
        for cal_id, eid, item in chunk_items:
            if eid:
                key = (cal_id, eid)
                if key in seen_keys:
                    continue
                seen_keys.add(key)
            all_shaped.append(item)
            if len(all_shaped) >= max_results:
                break
        if chunk_start <= win_start:
            break
        cursor = chunk_start
    return all_shaped, incomplete


def _calendar_query_impl(args: Dict[str, Any]) -> str:
    started = time.monotonic()
    # 1. Brian-only via ContextVar turn_id (never kwargs)
    turn_id = turn_context.current_turn_id_from_context()
    if not turn_context.is_brian_turn(turn_id):
        try:
            wslog.write_event(
                wslog.LOG_EVENT_CALENDAR_QUERY,
                state=STATE_ERROR,
                reason=REASON_NOT_BRIAN,
                count=0,
                ms=int((time.monotonic() - started) * 1000),
            )
        except Exception:
            pass
        # Refusals: plain JSON reason, never mark taint
        return json.dumps(
            {"ok": False, "state": STATE_ERROR, "reason": REASON_NOT_BRIAN, "items": []},
            ensure_ascii=False,
        )

    # 2. needs_reconnect / scope check
    auth.maybe_clear_stale_reconnect()
    status = auth.store_status()
    if status.get("needs_reconnect") or not status.get("connected"):
        reason = status.get("needs_reconnect") or auth.REASON_MISSING_STORE
        return json.dumps(
            {
                "ok": False,
                "state": STATE_NEEDS_RECONNECT,
                "reason": reason,
                "missing_scopes": status.get("missing_scopes") or [],
                "items": [],
            },
            ensure_ascii=False,
        )
    try:
        record = auth.load_token_record()
    except Exception:
        return json.dumps(
            {
                "ok": False,
                "state": STATE_NEEDS_RECONNECT,
                "reason": auth.REASON_DECRYPT_FAILED,
                "items": [],
            },
            ensure_ascii=False,
        )
    if record is None:
        return json.dumps(
            {
                "ok": False,
                "state": STATE_NEEDS_RECONNECT,
                "reason": auth.REASON_MISSING_STORE,
                "items": [],
            },
            ensure_ascii=False,
        )
    if auth.SCOPE_CALENDAR_READONLY not in set(record.scopes):
        return json.dumps(
            {
                "ok": False,
                "state": STATE_NEEDS_RECONNECT,
                "reason": REASON_MISSING_CALENDAR_SCOPE,
                "missing_scopes": auth.missing_scopes(record.scopes),
                "items": [],
            },
            ensure_ascii=False,
        )

    # 3. Build query (no NL date parsing)
    query = str(args.get("query") or "").strip()
    order = str(args.get("order") or ORDER_SOONEST).strip().lower()
    if order not in ORDERS:
        return _refuse(STATE_ERROR, REASON_BAD_ARGS)
    try:
        max_results = int(args.get("max_results") if args.get("max_results") is not None else MAX_RESULTS_DEFAULT)
    except Exception:
        return _refuse(STATE_ERROR, REASON_BAD_ARGS)
    if max_results < 1:
        max_results = 1
    if max_results > MAX_RESULTS_CAP:
        max_results = MAX_RESULTS_CAP

    now = datetime.now(timezone.utc)
    start_dt: Optional[datetime] = None
    end_dt: Optional[datetime] = None
    try:
        if args.get("start"):
            start_dt = _parse_iso_offset(str(args.get("start")), "start")
        if args.get("end"):
            end_dt = _parse_iso_offset(str(args.get("end")), "end")
    except Exception:
        return _refuse(STATE_ERROR, REASON_BAD_ARGS)

    try:
        win_start, win_end, was_clamped = _clamp_window(start_dt, end_dt, order=order, now=now)
    except ValueError:
        return _refuse(STATE_ERROR, REASON_BAD_ARGS)

    range_searched = {
        "start": win_start.isoformat(),
        "end": win_end.isoformat(),
        "clamped": was_clamped,
    }

    # 4. google_http
    try:
        headers = auth.authorization_header()
    except RuntimeError as exc:
        reason = str(exc) or auth.REASON_INVALID_GRANT
        auth.set_reconnect_reason(reason)
        return json.dumps(
            {
                "ok": False,
                "state": STATE_NEEDS_RECONNECT,
                "reason": reason,
                "items": [],
            },
            ensure_ascii=False,
        )
    except Exception:
        return _refuse(STATE_ERROR, "auth_error")

    try:
        list_items = _calendar_list(headers)
        tz_name, tz_source, tz = _resolve_timezone(list_items)
        calendars = _selected_calendars(list_items)
    except google_http.GoogleHttpError:
        return _refuse(STATE_ERROR, "google_http_error", range_searched=range_searched)
    except Exception:
        return _refuse(STATE_ERROR, "calendar_list_error", range_searched=range_searched)

    incomplete = False
    if order == ORDER_MOST_RECENT:
        all_shaped, incomplete = _collect_most_recent(
            calendars=calendars,
            headers=headers,
            win_start=win_start,
            win_end=win_end,
            query=query,
            max_results=max_results,
            tz=tz,
        )
        more_available = len(all_shaped) > max_results
        items_raw = all_shaped[:max_results]
    else:
        all_shaped = []
        from urllib.parse import quote

        for cal in calendars:
            cal_id = str(cal.get("id") or "")
            if not cal_id:
                continue
            cal_name = str(cal.get("summary") or cal_id)
            enc_id = quote(cal_id, safe="")
            raw_events, page_incomplete = _list_events_for_calendar(
                enc_id,
                headers=headers,
                time_min=win_start,
                time_max=win_end,
                query=query,
            )
            if page_incomplete:
                incomplete = True
            for ev in raw_events:
                all_shaped.append(_shape_event(ev, calendar_name=cal_name, tz=tz))

        all_shaped.sort(key=_sort_key_dt)
        more_available = len(all_shaped) > max_results
        items_raw = all_shaped[:max_results]

    items = [_strip_internal(i) for i in items_raw]

    if incomplete:
        state = STATE_INCOMPLETE
    elif not items:
        state = STATE_NO_MATCH
    else:
        state = STATE_COMPLETE

    result = {
        "ok": True,
        "state": state,
        "items": items,
        "more_available": more_available,
        "range_searched": range_searched,
        "timezone": tz_name,
        "timezone_source": tz_source,
    }

    # 6. mark_tainted BEFORE any content; fail → framed error, no content
    session_id, task_id = _ids_for_turn()
    try:
        if not session_id:
            raise ValueError("missing_session_id")
        taint.mark_tainted(session_id, task_id=task_id or None)
    except Exception:
        try:
            wslog.write_event(
                wslog.LOG_EVENT_CALENDAR_QUERY,
                state=STATE_ERROR,
                reason=REASON_TAINT_WRITE_FAILED,
                count=0,
                range_start=range_searched["start"],
                range_end=range_searched["end"],
                ms=int((time.monotonic() - started) * 1000),
            )
        except Exception:
            pass
        return _refuse(STATE_ERROR, REASON_TAINT_WRITE_FAILED, range_searched=range_searched)

    # Log state/counts/range only — NEVER titles/locations/attendees/descriptions
    try:
        wslog.write_event(
            wslog.LOG_EVENT_CALENDAR_QUERY,
            state=state,
            count=len(items),
            more=more_available,
            range_start=range_searched["start"],
            range_end=range_searched["end"],
            clamped=was_clamped,
            ms=int((time.monotonic() - started) * 1000),
        )
    except Exception:
        pass

    # 7. frame
    return framing.frame_untrusted(TOOL_NAME, json.dumps(result, ensure_ascii=False))
