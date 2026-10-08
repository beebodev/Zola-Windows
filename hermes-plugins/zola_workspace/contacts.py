"""contacts_lookup — synchronous, read-only (P8-D09)."""

from __future__ import annotations

import time
from typing import Any, Dict, List

try:
    from . import auth
    from . import google_http
    from . import log as wslog
    from . import read_common
except ImportError:  # P8-READ: flat unittest discover — P8-D09
    import auth
    import google_http
    import log as wslog
    import read_common

# P8-READ: searchContacts only; an empty result is no_match with no wait — P8-D09
TOOL_NAME = "contacts_lookup"
TOOLSET_NAME = "zola_workspace"
SEARCH_URL = "https://people.googleapis.com/v1/people:searchContacts"
READ_MASK = "names,emailAddresses,phoneNumbers"
REASON_MISSING_CONTACTS_SCOPE = "missing_contacts_scope"

_DESCRIPTION = (
    "Look up a person in Brian's Google Contacts by name, email, or phone. "
    "Returns display name, email addresses, and phone numbers. "
    "A contact created moments ago may not appear yet; a second lookup is the retry. "
    "Other contacts (auto-saved addresses) are not searched."
)

_SCHEMA: Dict[str, Any] = {
    "name": TOOL_NAME,
    "description": _DESCRIPTION,
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Name, email, or phone to search."},
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


def contacts_schema() -> Dict[str, Any]:
    return dict(_SCHEMA)


def shape_person(person: Dict[str, Any]) -> Dict[str, Any]:
    names = person.get("names") or []
    display = ""
    if names and isinstance(names[0], dict):
        display = str(names[0].get("displayName") or "")
    emails = []
    for item in person.get("emailAddresses") or []:
        if isinstance(item, dict) and item.get("value"):
            emails.append(str(item["value"]))
    phones = []
    for item in person.get("phoneNumbers") or []:
        if isinstance(item, dict) and item.get("value"):
            phones.append(str(item["value"]))
    return {"display_name": display, "emails": emails, "phones": phones}


def _elapsed(started: float) -> int:
    return int((time.monotonic() - started) * 1000)


def _impl(args: Dict[str, Any]) -> str:
    started = time.monotonic()
    query = str(args.get("query") or "").strip()
    if not query:
        return read_common.refuse(
            TOOL_NAME,
            state=read_common.STATE_ERROR,
            reason=read_common.REASON_BAD_ARGS,
            empty_key="contacts",
        )
    max_results = read_common.clamp_max_results(args.get("max_results"))
    if max_results is None:
        return read_common.refuse(
            TOOL_NAME,
            state=read_common.STATE_ERROR,
            reason=read_common.REASON_BAD_ARGS,
            empty_key="contacts",
        )
    refusal, headers = read_common.authorize(
        TOOL_NAME,
        required_scope=auth.SCOPE_CONTACTS_READONLY,
        missing_scope_reason=REASON_MISSING_CONTACTS_SCOPE,
        empty_key="contacts",
        log_event=wslog.LOG_EVENT_CONTACTS,
        started_ms=_elapsed(started),
    )
    if refusal is not None or headers is None:
        return refusal or ""
    try:
        body = read_common.google_get(
            SEARCH_URL,
            headers=headers,
            route=google_http.ROUTE_CONTACTS_SEARCH,
            params={"query": query, "pageSize": max_results, "readMask": READ_MASK},
        ).json()
    except google_http.GoogleHttpError:
        return read_common.refuse(
            TOOL_NAME,
            state=read_common.STATE_INCOMPLETE,
            reason="contacts_search_failed",
            empty_key="contacts",
        )
    contacts: List[Dict[str, Any]] = []
    for item in (body.get("results") or [])[:max_results]:
        if not isinstance(item, dict):
            continue
        person = item.get("person") or item
        if isinstance(person, dict):
            contacts.append(shape_person(person))
    more_available = bool(body.get("nextPageToken"))
    state = read_common.STATE_NO_MATCH if not contacts else read_common.STATE_COMPLETE
    payload = {
        "ok": True,
        "state": state,
        "more_available": more_available,
        "contacts": contacts,
    }
    return read_common.mark_then_frame(
        TOOL_NAME,
        payload,
        empty_key="contacts",
        log_event=wslog.LOG_EVENT_CONTACTS,
        log_fields={
            "state": state,
            "count": len(contacts),
            "more": more_available,
            "ms": _elapsed(started),
        },
    )


def contacts_lookup_handler(args: dict, **kwargs) -> str:
    started = time.monotonic()
    try:
        return _impl(args if isinstance(args, dict) else {})
    except Exception:
        try:
            wslog.write_event(
                wslog.LOG_EVENT_CONTACTS,
                state=read_common.STATE_ERROR,
                count=0,
                ms=_elapsed(started),
            )
        except Exception:
            pass
        return read_common.refuse(
            TOOL_NAME,
            state=read_common.STATE_ERROR,
            reason="internal_error",
            empty_key="contacts",
        )
