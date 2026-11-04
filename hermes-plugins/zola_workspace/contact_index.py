"""In-memory index of Brian's Google Contacts for the phone-message track (P10-READ).

Memory only. Nothing here writes a file or the proactive store, and nothing logs a
name, number, address, or resourceName. Only counts and states reach the log.
"""

from __future__ import annotations

import hashlib
import logging
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, FrozenSet, List, Optional, Tuple

try:
    from . import address_hash
    from . import auth
    from . import google_http
    from . import phone_ids
except ImportError:  # P10-READ: flat unittest discover
    import address_hash
    import auth
    import google_http
    import phone_ids

# P10-READ: named caps; the TTL is the 30-minute freshness rule
TTL_SECONDS = 30 * 60
# P10-READ: a miss or a failure may retry at most this often, so a stranger's name
# cannot turn into one People API call per lookup
REFRESH_MIN_INTERVAL_SECONDS = 60.0
# P10-READ F8: on-miss / bounded wait inside the phone_read_texts overall budget — never on the inject path
TURN_REFRESH_BOUND_SECONDS = 2.0
CONNECTIONS_URL = "https://people.googleapis.com/v1/people/me/connections"
PERSON_FIELDS = "names,emailAddresses,phoneNumbers"
PAGE_SIZE = 1000
MAX_PAGES = 50
REQUEST_TIMEOUT_SECONDS = 30.0
SOURCE_CONTACTS = "READ_SOURCE_TYPE_CONTACT"
LOG_NAME = "zola_workspace.contact_index"

_logger = logging.getLogger(LOG_NAME)
_now: Callable[[], float] = time.monotonic


@dataclass(frozen=True, repr=False)
class Person:
    """One contact. repr shows the handle only, so a stray log line leaks nothing."""

    handle: str
    display_name: str
    numbers: Tuple[str, ...]
    number_hashes: FrozenSet[str]
    emails: Tuple[str, ...]
    email_hashes: FrozenSet[str]

    def __repr__(self) -> str:
        return f"Person(handle={self.handle})"


class _Index:
    """Immutable lookup tables built once per refresh."""

    def __init__(self, people: List[Person]) -> None:
        self.people = tuple(people)
        self.by_handle: Dict[str, Person] = {p.handle: p for p in people}
        self._by_name: Dict[str, List[Person]] = {}
        self._by_number_hash: Dict[str, List[Person]] = {}
        self._by_email_hash: Dict[str, List[Person]] = {}
        for person in people:
            key = _name_key(person.display_name)
            if key:
                self._by_name.setdefault(key, []).append(person)
            for digest in person.number_hashes:
                self._by_number_hash.setdefault(digest, []).append(person)
            for digest in person.email_hashes:
                self._by_email_hash.setdefault(digest, []).append(person)

    def names(self, key: str) -> List[Person]:
        return list(self._by_name.get(key, ()))

    def by_number_hash(self, digest: str) -> List[Person]:
        return list(self._by_number_hash.get(digest, ()))

    def by_email_hash(self, digest: str) -> List[Person]:
        return list(self._by_email_hash.get(digest, ()))

    def shared_number_hashes(self) -> FrozenSet[str]:
        return frozenset(h for h, owners in self._by_number_hash.items() if len(owners) > 1)


_lock = threading.RLock()
_index: Optional[_Index] = None
_loaded_at: Optional[float] = None
_last_attempt_at: Optional[float] = None
_unavailable = False
_phone_fallbacks = 0
_refresh_thread: Optional[threading.Thread] = None
# Tests that are not about F8 may run the refresh inline so annotate sees a settled index.
_sync_refresh_for_tests = False


def _name_key(name: str) -> str:
    return " ".join(str(name or "").split()).casefold()


def _speech_form(name: str) -> str:
    """Casefold; drop punctuation; collapse whitespace. Digits stay (exact only — never fuzzy)."""
    folded = str(name or "").casefold()
    chars: List[str] = []
    for ch in folded:
        if ch.isalnum():
            chars.append(ch)
        elif ch.isspace() and chars and chars[-1] != " ":
            chars.append(" ")
    return "".join(chars).strip()


def _compact_form(name: str) -> str:
    return _speech_form(name).replace(" ", "")


def _name_tokens(name: str) -> Tuple[str, ...]:
    return tuple(tok for tok in _speech_form(name).split(" ") if tok)


def _edit_distance(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    if abs(len(a) - len(b)) > 2:
        return 99
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        curr = [i]
        for j, cb in enumerate(b, start=1):
            cost = 0 if ca == cb else 1
            curr.append(min(curr[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost))
        prev = curr
    return prev[-1]


def _fuzzy_allowed(a: str, b: str) -> bool:
    """Small misspellings only: both sides length ≥ 4; never against a digit-only string.

    Max Levenshtein distance is 1 when either side is length 4–5, else 2 when both ≥ 6.
    Digits alone are never fuzzy-matched (phone numbers must not resolve as names).
    """
    if not a or not b:
        return False
    if a.isdigit() or b.isdigit():
        return False
    if len(a) < 4 or len(b) < 4:
        return False
    limit = 1 if min(len(a), len(b)) < 6 else 2
    return _edit_distance(a, b) <= limit


def _person_matches_query(person: Person, query: str) -> bool:
    q_speech = _speech_form(query)
    if not q_speech:
        return False
    q_compact = _compact_form(query)
    q_tokens = _name_tokens(query)
    name_speech = _speech_form(person.display_name)
    if not name_speech:
        return False
    name_compact = _compact_form(person.display_name)
    name_tokens = _name_tokens(person.display_name)
    # Exact: spaced form or compacted (spacing/punctuation already stripped).
    if q_speech == name_speech or (q_compact and q_compact == name_compact):
        return True
    # First or last name alone (exact token).
    if len(q_tokens) == 1 and q_tokens[0] in name_tokens:
        return True
    # Fuzzy: compact full name, or single-token query vs each name token.
    if q_compact and name_compact and _fuzzy_allowed(q_compact, name_compact):
        return True
    if len(q_tokens) == 1:
        qt = q_tokens[0]
        for token in name_tokens:
            if _fuzzy_allowed(qt, token):
                return True
    return False


def _handle_for(resource_name: str) -> str:
    # P10-READ: stable, opaque, not reversible; the resourceName itself is never kept
    digest = hashlib.sha256(("zola-contact\x1f" + resource_name).encode("utf-8")).hexdigest()
    return "c_" + digest[:16]


def _display_name(person: Dict[str, Any]) -> str:
    names = [n for n in (person.get("names") or []) if isinstance(n, dict)]
    primary = [n for n in names if (n.get("metadata") or {}).get("primary")]
    for item in primary + names:
        text = str(item.get("displayName") or "").strip()
        if text:
            return text
    return ""


def _numbers(person: Dict[str, Any]) -> List[str]:
    global _phone_fallbacks
    found: List[str] = []
    for item in person.get("phoneNumbers") or []:
        if not isinstance(item, dict):
            continue
        canonical = ""
        form = item.get("canonicalForm")
        if isinstance(form, str) and form.strip():
            kind, value = phone_ids.normalize(form)
            if kind == phone_ids.KIND_E164 and form.strip().startswith("+"):
                canonical = value
        if not canonical:
            # P10-READ: no usable canonicalForm; fall back to the shared normalizer
            raw = item.get("value")
            if isinstance(raw, str) and raw.strip():
                kind, value = phone_ids.normalize(raw)
                if phone_ids.matchable(kind):
                    canonical = value
                    _phone_fallbacks += 1
        if canonical and canonical not in found:
            found.append(canonical)
    return found


def _emails(person: Dict[str, Any]) -> List[str]:
    found: List[str] = []
    for item in person.get("emailAddresses") or []:
        if not isinstance(item, dict):
            continue
        value = str(item.get("value") or "").strip().casefold()
        if "@" in value and value not in found:
            found.append(value)
    return found


def _build_person(raw: Dict[str, Any]) -> Optional[Person]:
    resource = raw.get("resourceName")
    if not isinstance(resource, str) or not resource:
        return None
    numbers = _numbers(raw)
    emails = _emails(raw)
    return Person(
        handle=_handle_for(resource),
        display_name=_display_name(raw),
        numbers=tuple(numbers),
        number_hashes=frozenset(phone_ids.hash(n) for n in numbers),
        emails=tuple(emails),
        email_hashes=frozenset(address_hash.address_hash(e) for e in emails),
    )


def _headers() -> Dict[str, str]:
    """Bearer header, or raise. Tests patch this; the failure text is never surfaced."""
    status = auth.store_status()
    if status.get("needs_reconnect") or not status.get("connected"):
        raise RuntimeError("not_connected")
    record = auth.load_token_record()
    if record is None or auth.SCOPE_CONTACTS_READONLY not in set(record.scopes):
        raise RuntimeError("missing_scope")
    return auth.authorization_header()


def _fetch_people() -> List[Dict[str, Any]]:
    """Every page of people.connections.list. A truncated list is a failure."""
    headers = _headers()
    people: List[Dict[str, Any]] = []
    token = ""
    for _ in range(MAX_PAGES):
        params: Dict[str, Any] = {
            "personFields": PERSON_FIELDS,
            "pageSize": PAGE_SIZE,
            "sources": SOURCE_CONTACTS,
        }
        if token:
            params["pageToken"] = token
        body = google_http.request(
            "GET",
            CONNECTIONS_URL,
            headers=headers,
            params=params,
            timeout=REQUEST_TIMEOUT_SECONDS,
            route=google_http.ROUTE_CONTACTS_CONNECTIONS,
        ).json()
        if not isinstance(body, dict):
            raise ValueError("bad_body")
        for item in body.get("connections") or []:
            if isinstance(item, dict):
                people.append(item)
        token = str(body.get("nextPageToken") or "")
        if not token:
            return people
    raise ValueError("too_many_pages")


def _log(event: str, **fields: Any) -> None:
    parts = [f"{LOG_NAME}.{event}"] + [f"{k}={v}" for k, v in fields.items()]
    try:
        _logger.info(" ".join(parts))
    except Exception:
        pass


def _apply_refresh_result(built: Optional[_Index], attempted_at: float) -> bool:
    """Install a finished fetch under the lock. built=None means the fetch failed."""
    global _index, _loaded_at, _last_attempt_at, _unavailable, _phone_fallbacks
    _last_attempt_at = attempted_at
    if built is None:
        # P10-READ: a failed refresh leaves nobody known; callers say so — never stale data
        _index = None
        _loaded_at = None
        _unavailable = True
        _phone_fallbacks = 0
        _log("refresh", state="unavailable")
        return False
    _index = built
    _loaded_at = attempted_at
    _unavailable = False
    _log("refresh", state="ok", count=len(built.people))
    return True


def _fetch_and_build() -> Optional[_Index]:
    """People API fetch off the lock. None on any failure."""
    global _phone_fallbacks
    try:
        raw_people = _fetch_people()
        # number fallbacks accumulate during _numbers; reset then rebuild under one pass
        prior = _phone_fallbacks
        people = [p for p in (_build_person(item) for item in raw_people) if p is not None]
        built = _Index(people)
        # keep fallback count from this build only
        _ = prior
        return built
    except Exception:
        return None


def _refresh_locked() -> bool:
    """Blocking refresh; tests and the bounded on-miss path use this under the lock."""
    global _phone_fallbacks
    attempted = _now()
    _phone_fallbacks = 0
    # release so Google I/O does not hold the lock for up to 30 s × pages (F8)
    _lock.release()
    try:
        built = _fetch_and_build()
    finally:
        _lock.acquire()
    return _apply_refresh_result(built, attempted)


def _stale() -> bool:
    return _index is None or _loaded_at is None or (_now() - _loaded_at) >= TTL_SECONDS


def _cooled_down() -> bool:
    return _last_attempt_at is None or (_now() - _last_attempt_at) >= REFRESH_MIN_INTERVAL_SECONDS


def _start_background_refresh_locked() -> None:
    """Kick a daemon refresh; the turn path never waits on it (F8 option a)."""
    global _refresh_thread, _last_attempt_at
    if _refresh_thread is not None and _refresh_thread.is_alive():
        return
    # stamp the attempt so cooldown applies even while the thread runs
    _last_attempt_at = _now()
    attempted = _last_attempt_at

    def run() -> None:
        global _phone_fallbacks
        _phone_fallbacks = 0
        built = _fetch_and_build()
        with _lock:
            _apply_refresh_result(built, attempted)

    if _sync_refresh_for_tests:
        run()
        return
    _refresh_thread = threading.Thread(target=run, name="zola-contacts-refresh", daemon=True)
    _refresh_thread.start()
    _log("refresh", state="background")


def set_sync_refresh_for_tests(enabled: bool) -> None:
    """When True, refresh_if_stale runs the fetch inline (surface suite default). F8 tests leave this False."""
    global _sync_refresh_for_tests
    _sync_refresh_for_tests = bool(enabled)


def refresh_if_stale() -> bool:
    """Non-blocking for the turn / inject path. Starts a background reload when stale.

    Returns True when an index is available *right now* (possibly aged). A first load or a
    failed prior refresh returns False immediately and kicks the background fetch.
    """
    with _lock:
        if _stale() and (_index is not None or _last_attempt_at is None or _cooled_down()):
            _start_background_refresh_locked()
        return _index is not None


def wait_refresh_for_tests(timeout: float = 5.0) -> None:
    """Join the background refresh thread (tests only)."""
    thread = _refresh_thread
    if thread is not None:
        thread.join(timeout)


def refresh_bounded(timeout: float = TURN_REFRESH_BOUND_SECONDS) -> bool:
    """Blocking refresh with a short bound for on-miss inside phone_read_texts.

    Returns True when an index is available after the wait (or already was). On timeout the
    background thread may still finish; this turn treats contacts as currently unavailable
    when there is no index yet. Joins an in-flight first load kicked by refresh_if_stale.
    """
    with _lock:
        if _index is not None and not _stale():
            return True
        thread = _refresh_thread
        if thread is None or not thread.is_alive():
            if not (_index is not None or _last_attempt_at is None or _cooled_down()):
                return _index is not None
            _start_background_refresh_locked()
            thread = _refresh_thread
    if thread is not None:
        thread.join(timeout)
    with _lock:
        return _index is not None


def _refresh_on_miss() -> bool:
    """On-demand reload after a name miss, F8-bounded. True when an index is available after.

    Runs even when the current index is still inside its TTL (a contact may have been
    added since the last load). Honours REFRESH_MIN_INTERVAL so a stranger's name
    cannot turn into one People call per lookup. Always joins an in-flight refresh
    kicked by refresh_if_stale (first load on the annotate path).
    """
    with _lock:
        thread = _refresh_thread
        in_flight = thread is not None and thread.is_alive()
        if not in_flight:
            if _last_attempt_at is not None and not _cooled_down():
                return _index is not None
            _start_background_refresh_locked()
            thread = _refresh_thread
    if thread is not None:
        thread.join(TURN_REFRESH_BOUND_SECONDS)
    with _lock:
        return _index is not None


def get_index() -> Optional[_Index]:
    """The current index. Never blocks on Google; may kick a background refresh when stale."""
    with _lock:
        refresh_if_stale()
        return _index


def contacts_unavailable() -> bool:
    """True when contacts cannot be trusted for naming right now.

    Failed refresh (approved) or a first load still in flight (F8) — callers say the
    "contacts could not be checked" sentence instead of "isn't in your contacts".
    """
    with _lock:
        if _unavailable:
            return True
        if _index is None and _refresh_thread is not None and _refresh_thread.is_alive():
            return True
        return False


def _single(matches: List[Person]) -> Optional[Person]:
    # P10-READ: two owners means ambiguous, so neither is returned
    return matches[0] if len(matches) == 1 else None


def _match_in_index(index: _Index, query: str) -> Tuple[Person, ...]:
    """Unique people that speech-match query. Order follows index load order."""
    seen: Dict[str, Person] = {}
    for person in index.people:
        if person.handle in seen:
            continue
        if _person_matches_query(person, query):
            seen[person.handle] = person
    return tuple(seen.values())


def match_people_by_name(query: str) -> Tuple[Person, ...]:
    """Speech-tolerant name match for Brian's contact list.

    Returns zero, one, or many people. Empty when unknown or contacts unavailable.
    Several means ask which (never auto-pick). Fuzzy never merges two people into one
    hit and never chooses between two — that is the caller's job (ask, or stop).

    Track 6 carry-forward: forget and watches use this same resolver, but must CONFIRM
    a fuzzy match with Brian before acting. phone_read_texts may proceed on a unique
    fuzzy hit and names who it resolved to so he can correct her.
    """
    if not _speech_form(query):
        return ()
    with _lock:
        index = get_index()
        if index is not None:
            hits = _match_in_index(index, query)
            if hits:
                return hits
    # F8: join outside the lock so the background refresh can install the index
    if not _refresh_on_miss():
        return ()
    with _lock:
        if _index is None:
            return ()
        return _match_in_index(_index, query)


def resolve_person_by_name(query: str) -> Optional[Person]:
    """Unique speech-tolerant display-name match. None when unknown, ambiguous, or unavailable."""
    hits = match_people_by_name(query)
    return hits[0] if len(hits) == 1 else None


def resolve_person_by_phone_hash(digest: str) -> Optional[Person]:
    """Owner of a canonical-number hash. A number on two people resolves to neither.

    Does not wait on Google (F8). Callers on the turn path use whatever index is loaded;
    phone_read_texts name resolution waits via match_people_by_name / refresh_bounded.
    """
    with _lock:
        index = get_index()
        return _single(index.by_number_hash(str(digest or ""))) if index is not None else None


def resolve_person_by_email_hash(digest: str) -> Optional[Person]:
    with _lock:
        index = get_index()
        return _single(index.by_email_hash(str(digest or ""))) if index is not None else None


def canonical_numbers_for(person: Any) -> Tuple[str, ...]:
    """E.164 numbers that belong to this person alone. A shared number is left out."""
    with _lock:
        index = _index
        if isinstance(person, str):
            person = index.by_handle.get(person) if index is not None else None
        if not isinstance(person, Person):
            return ()
        shared = index.shared_number_hashes() if index is not None else frozenset()
        return tuple(n for n in person.numbers if phone_ids.hash(n) not in shared)


def phone_fallback_count() -> int:
    """Numbers in the last refresh that had to use phone_ids.normalize (tests)."""
    return _phone_fallbacks


def reset_for_tests() -> None:
    global _index, _loaded_at, _last_attempt_at, _unavailable, _phone_fallbacks, _now, _refresh_thread
    global _sync_refresh_for_tests
    thread = _refresh_thread
    if thread is not None and thread.is_alive():
        thread.join(5.0)
    with _lock:
        _index = None
        _loaded_at = None
        _last_attempt_at = None
        _unavailable = False
        _phone_fallbacks = 0
        _refresh_thread = None
        _now = time.monotonic
        _sync_refresh_for_tests = False
