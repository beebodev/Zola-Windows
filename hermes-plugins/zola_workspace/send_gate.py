"""Presented-draft record, passphrase matcher, and single-use send authorization (P8-D05 / P8-D06)."""

from __future__ import annotations

import base64
import email.utils
import hashlib
import re
import sqlite3
import threading
import time
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

try:
    from . import log as wslog
    from . import turn_context
except ImportError:  # P8-SEND: flat unittest discover — P8-D05
    import log as wslog
    import turn_context

# P8-SEND: the passphrase is these three tokens, nothing else — P8-D05
PASSPHRASE_TOKENS = ("approved", "send", "it")
OPENERS = frozenset({"zola", "okay", "ok", "um", "uh"})
INTERRUPTED_MARK = "previous turn was interrupted"

# P8-SEND: verbatim read-back at or under this many body characters — P8-D05
READBACK_BODY_MAX = 400
READBACK_VERBATIM = "verbatim"
READBACK_GIST = "gist"

DELETE_PHRASES = (
    "delete that draft",
    "delete the draft",
    "delete this draft",
    "discard that draft",
    "discard the draft",
    "discard this draft",
)

REASON_NOT_REVIEWED = "not_reviewed"
REASON_NO_AUTHORIZATION = "no_authorization"
REASON_USED = "used"
REASON_WRONG_TURN = "wrong_turn"
REASON_WRONG_DRAFT = "wrong_draft"
REASON_CONTENT_CHANGED = "content_changed"
REASON_TURN_CHANGED = "turn_changed"
REASON_DELETE_NOT_REQUESTED = "delete_not_requested"
REASON_NOT_OWN_DRAFT = "not_own_draft"

_lock = threading.Lock()
_pending: Dict[str, "PendingDraft"] = {}
_own: Dict[str, set] = {}
_auths: Dict[str, "Authorization"] = {}
_snapshots: Dict[str, "UserSnapshot"] = {}
_reply_differs: Dict[Tuple[str, str], bool] = {}
_clock: Callable[[], float] = time.monotonic


@dataclass
class PendingDraft:
    draft_id: str
    content_hash: str
    turn_id: str
    session_id: str
    addresses: Tuple[str, ...]
    subject: str
    body: str
    check_body: bool
    readback: str
    reviewed: bool = False
    reviewed_at: Optional[float] = None


@dataclass
class Authorization:
    draft_id: str
    content_hash: str
    turn_id: str
    session_id: str
    used: bool = False


@dataclass
class UserSnapshot:
    session_id: str
    user_id: Optional[int]
    failed: bool


@dataclass(frozen=True)
class SendGrant:
    draft_id: str
    content_hash: str
    turn_id: str
    session_id: str


def set_clock_for_tests(fn: Optional[Callable[[], float]]) -> None:
    """Test helper: inject the clock used for review expiry."""
    global _clock
    _clock = fn or time.monotonic


def reset_for_tests() -> None:
    """Test helper: drop in-memory send state and restore the clock."""
    global _clock
    with _lock:
        _pending.clear()
        _own.clear()
        _auths.clear()
        _snapshots.clear()
        _reply_differs.clear()
    _clock = time.monotonic


def _now() -> float:
    return float(_clock())


def normalize_tokens(text: str) -> Tuple[str, ...]:
    """Casefold, drop apostrophes, and turn other non-alnum runs into spaces."""
    # P8-SEND: same rules for the passphrase and for read-back containment — P8-D05
    folded = (text or "").casefold()
    cleaned = re.sub(r"[^a-z0-9']+", " ", folded)
    cleaned = cleaned.replace("'", "")
    return tuple(part for part in cleaned.split() if part)


def passphrase_match(text: str) -> bool:
    """Whole-message match. An interrupted-turn note never matches."""
    if INTERRUPTED_MARK in (text or "").casefold():
        return False
    tokens = list(normalize_tokens(text))
    while tokens and tokens[0] in OPENERS:
        tokens.pop(0)
    return tuple(tokens) == PASSPHRASE_TOKENS


def delete_requested(text: str) -> bool:
    """True when this turn asks to delete or discard the draft.

    `don't` or `do not` immediately before the phrase does not count.
    """
    tokens = list(normalize_tokens(text))
    for phrase in DELETE_PHRASES:
        need = phrase.split()
        width = len(need)
        for index in range(0, len(tokens) - width + 1):
            if tokens[index : index + width] != need:
                continue
            if index >= 1 and tokens[index - 1] == "dont":
                continue
            if index >= 2 and tokens[index - 2] == "do" and tokens[index - 1] == "not":
                continue
            return True
    return False


def addr_specs(values: Sequence[str]) -> List[str]:
    """Unique casefolded addr-specs, sorted. Display names are dropped."""
    found = []
    for _name, addr in email.utils.getaddresses([str(item) for item in values if item]):
        text = str(addr or "").strip()
        if "@" not in text or any(ch in text for ch in "\r\n"):
            continue
        found.append(text.casefold())
    return sorted(set(found))


def canon_subject(value: str) -> str:
    text = str(value or "").replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
    return re.sub(r"\s+", " ", text).strip()


def canon_body(value: str) -> str:
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    return "\n".join(lines).strip()


def canonical_text(
    to: Sequence[str],
    cc: Sequence[str],
    bcc: Sequence[str],
    subject: str,
    body: str,
    html: str,
    thread_id: str,
) -> str:
    """UTF-8 canonical form. Field order is part of the hash."""
    # P8-SEND: display names are not part of the hash — P8-D06
    return "\n".join(
        [
            "to:" + ",".join(addr_specs(to)),
            "cc:" + ",".join(addr_specs(cc)),
            "bcc:" + ",".join(addr_specs(bcc)),
            "subject:" + canon_subject(subject),
            "body:" + canon_body(body),
            "html:" + (canon_body(html) if html else ""),
            "thread:" + str(thread_id or ""),
        ]
    )


def content_hash(
    to: Sequence[str],
    cc: Sequence[str],
    bcc: Sequence[str],
    subject: str,
    body: str,
    html: str,
    thread_id: str,
) -> str:
    raw = canonical_text(to, cc, bcc, subject, body, html, thread_id)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def handle_hash(draft_id: str) -> str:
    return hashlib.sha256(str(draft_id or "").encode("utf-8")).hexdigest()[:16]


def people(header: str) -> List[Dict[str, str]]:
    """Tool-result recipients. Addresses are casefolded; names may be empty."""
    out: List[Dict[str, str]] = []
    seen = set()
    source = [header] if header else []
    for name, addr in email.utils.getaddresses(source):
        text = str(addr or "").strip()
        if "@" not in text:
            continue
        key = text.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append({"name": str(name or ""), "address": key})
    return out


def header_value(values: Sequence[str]) -> str:
    parts: List[str] = []
    for name, addr in email.utils.getaddresses([str(item) for item in values if item]):
        text = str(addr or "").strip()
        if "@" not in text or any(ch in text for ch in "\r\n"):
            continue
        display = str(name or "").replace("\r", " ").replace("\n", " ").strip()
        if display:
            parts.append(email.utils.formataddr((display, text)))
        else:
            parts.append(text)
    return ", ".join(parts)


def build_raw(
    *,
    to: Sequence[str],
    cc: Sequence[str],
    bcc: Sequence[str],
    subject: str,
    body: str,
    in_reply_to: str = "",
    references: str = "",
) -> str:
    """Base64url MIME for drafts.create / drafts.update. No attachment part."""
    message = EmailMessage()
    to_header = header_value(to)
    cc_header = header_value(cc)
    bcc_header = header_value(bcc)
    if to_header:
        message["To"] = to_header
    if cc_header:
        message["Cc"] = cc_header
    if bcc_header:
        message["Bcc"] = bcc_header
    message["Subject"] = canon_subject(subject)
    if in_reply_to:
        message["In-Reply-To"] = str(in_reply_to).replace("\r", "").replace("\n", "")
    if references:
        message["References"] = str(references).replace("\r", " ").replace("\n", " ")
    message.set_content(canon_body(body))
    encoded = base64.urlsafe_b64encode(bytes(message)).decode("ascii").rstrip("=")
    return encoded


def _header_map(payload: Dict[str, Any]) -> Dict[str, str]:
    found: Dict[str, str] = {}
    for header in payload.get("headers") or []:
        if not isinstance(header, dict):
            continue
        name = str(header.get("name") or "")
        if name:
            found[name.casefold()] = str(header.get("value") or "")
    return found


def _decode_data(data: str) -> str:
    if not data:
        return ""
    pad = "=" * (-len(data) % 4)
    try:
        raw = base64.urlsafe_b64decode(data + pad)
    except Exception:
        return ""
    return raw.decode("utf-8", "replace")


def _walk(part: Dict[str, Any]) -> List[Dict[str, Any]]:
    found = [part]
    for child in part.get("parts") or []:
        if isinstance(child, dict):
            found.extend(_walk(child))
    return found


def parse_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """Canonical fields from a Gmail message resource."""
    payload = message.get("payload") if isinstance(message, dict) else None
    if not isinstance(payload, dict):
        payload = {}
    headers = _header_map(payload)
    plain: List[str] = []
    html: List[str] = []
    filenames: List[str] = []
    for part in _walk(payload):
        filename = str(part.get("filename") or "")
        if filename:
            filenames.append(filename)
            continue
        mime = str(part.get("mimeType") or "")
        data = str((part.get("body") or {}).get("data") or "")
        if not data:
            continue
        text = _decode_data(data)
        if mime == "text/html":
            html.append(text)
        elif mime == "text/plain" or not mime:
            plain.append(text)
    return {
        "to": headers.get("to", ""),
        "cc": headers.get("cc", ""),
        "bcc": headers.get("bcc", ""),
        "subject": canon_subject(headers.get("subject", "")),
        "body": canon_body("\n".join(plain)),
        "html": canon_body("\n".join(html)) if html else "",
        "thread_id": str(message.get("threadId") or ""),
        "in_reply_to": headers.get("in-reply-to", ""),
        "references": headers.get("references", ""),
        "filenames": filenames,
    }


def parse_draft(draft: Dict[str, Any]) -> Dict[str, Any]:
    message = draft.get("message") if isinstance(draft, dict) else None
    if not isinstance(message, dict):
        message = {}
    fields = parse_message(message)
    fields["draft_id"] = str(draft.get("id") or "")
    return fields


def hash_fields(fields: Dict[str, Any]) -> str:
    return content_hash(
        [fields.get("to") or ""],
        [fields.get("cc") or ""],
        [fields.get("bcc") or ""],
        str(fields.get("subject") or ""),
        str(fields.get("body") or ""),
        str(fields.get("html") or ""),
        str(fields.get("thread_id") or ""),
    )


def reply_plan(message: Dict[str, Any]) -> Dict[str, Any]:
    """Threading headers and whether Reply-To differs from From."""
    payload = message.get("payload") if isinstance(message, dict) else None
    headers = _header_map(payload if isinstance(payload, dict) else {})
    from_header = headers.get("from", "")
    reply_header = headers.get("reply-to", "")
    message_id = headers.get("message-id", "")
    references = headers.get("references", "")
    from_specs = addr_specs([from_header])
    reply_specs = addr_specs([reply_header])
    differs = bool(reply_specs) and reply_specs != from_specs
    default_to = reply_header if reply_specs else from_header
    ref_out = references
    if message_id and message_id not in references:
        ref_out = (references + " " + message_id).strip()
    return {
        "default_to": default_to,
        "reply_to_differs": differs,
        "in_reply_to": message_id,
        "references": ref_out,
        "thread_id": str(message.get("threadId") or ""),
    }


def readback_for(body: str) -> str:
    if len(canon_body(body)) <= READBACK_BODY_MAX:
        return READBACK_VERBATIM
    return READBACK_GIST


def _live(draft: PendingDraft, now: Optional[float] = None) -> bool:
    """Reviewed and still inside the authority TTL measured from review time."""
    # P8-SEND: expiry starts when the draft was reviewed, and uses the existing TTL — P8-D05
    if not draft.reviewed or draft.reviewed_at is None:
        return False
    current = _now() if now is None else now
    return (current - draft.reviewed_at) <= turn_context.AUTHORITY_GRANT_TTL_SECONDS


def _expired(draft: PendingDraft, now: float) -> bool:
    """Reviewed and past the authority TTL. An unreviewed draft is not expired."""
    if not draft.reviewed or draft.reviewed_at is None:
        return False
    return (now - draft.reviewed_at) > turn_context.AUTHORITY_GRANT_TTL_SECONDS


def _covers(reply: str, draft: PendingDraft) -> bool:
    subject = " ".join(normalize_tokens(draft.subject))
    hay = " ".join(normalize_tokens(reply))
    if not subject or subject not in hay:
        return False
    folded = (reply or "").casefold()
    if not draft.addresses:
        return False
    for addr in draft.addresses:
        if addr.casefold() not in folded:
            return False
    if draft.check_body:
        body = " ".join(normalize_tokens(draft.body))
        if body and body not in hay:
            return False
    return True


def log_decision(
    *,
    decision: str,
    reason: str = "",
    draft_id: str = "",
    recipient_count: int = 0,
    started: Optional[float] = None,
) -> None:
    """Metadata only. Never recipients, subject, body, or the user's text."""
    elapsed = 0
    if started is not None:
        elapsed = int((time.monotonic() - started) * 1000)
    try:
        wslog.write_event(
            wslog.LOG_EVENT_SEND_GATE,
            decision=decision,
            reason=reason or "-",
            handle=handle_hash(draft_id) if draft_id else "-",
            recipient_count=int(recipient_count),
            ms=elapsed,
        )
    except Exception:
        pass


def remember_own(session_id: str, draft_id: str) -> None:
    if not session_id or not draft_id:
        return
    with _lock:
        _own.setdefault(session_id, set()).add(draft_id)


def owns(session_id: str, draft_id: str) -> bool:
    with _lock:
        return draft_id in _own.get(session_id, set())


def note_reply_differs(session_id: str, draft_id: str, differs: bool) -> None:
    with _lock:
        _reply_differs[(session_id, draft_id)] = bool(differs)


def reply_differs(session_id: str, draft_id: str) -> bool:
    with _lock:
        return bool(_reply_differs.get((session_id, draft_id), False))


def present(
    *,
    session_id: str,
    turn_id: str,
    draft_id: str,
    fields: Dict[str, Any],
    reply_to_differs: bool,
) -> PendingDraft:
    """Store one prepared draft. A newer presentation replaces the older and clears authorization."""
    # P8-SEND: prepared is not reviewed — P8-D05
    addresses = tuple(
        addr_specs([fields.get("to") or ""])
        + addr_specs([fields.get("cc") or ""])
        + addr_specs([fields.get("bcc") or ""])
    )
    body = str(fields.get("body") or "")
    check_body = len(canon_body(body)) <= READBACK_BODY_MAX
    draft = PendingDraft(
        draft_id=draft_id,
        content_hash=hash_fields(fields),
        turn_id=turn_id,
        session_id=session_id,
        addresses=addresses,
        subject=str(fields.get("subject") or ""),
        body=body,
        check_body=check_body,
        readback=READBACK_VERBATIM if check_body else READBACK_GIST,
        reviewed=False,
        reviewed_at=None,
    )
    with _lock:
        # P8-SEND: other sessions' expired reviews must not accumulate — P8-D05
        now = _now()
        for other_id, other in list(_pending.items()):
            if other_id == session_id or not _expired(other, now):
                continue
            _pending.pop(other_id, None)
            _reply_differs.pop((other_id, other.draft_id), None)
        _pending[session_id] = draft
        _own.setdefault(session_id, set()).add(draft_id)
        _reply_differs[(session_id, draft_id)] = bool(reply_to_differs)
        for key in list(_auths):
            if _auths[key].session_id == session_id:
                del _auths[key]
    return draft


def drop_pending(session_id: str, draft_id: str) -> None:
    with _lock:
        current = _pending.get(session_id)
        if current is not None and current.draft_id == draft_id:
            _pending.pop(session_id, None)
        _own.get(session_id, set()).discard(draft_id)
        _reply_differs.pop((session_id, draft_id), None)


def clear_authorization(turn_id: str) -> None:
    with _lock:
        _auths.pop(turn_id, None)


def clear_session(session_id: str) -> None:
    """Drop the pending draft and any authorization for this session."""
    if not session_id:
        return
    with _lock:
        _pending.pop(session_id, None)
        _own.pop(session_id, None)
        for key in list(_auths):
            if _auths[key].session_id == session_id:
                del _auths[key]
        for key in list(_snapshots):
            if _snapshots[key].session_id == session_id:
                del _snapshots[key]
        for key in list(_reply_differs):
            if key[0] == session_id:
                del _reply_differs[key]


def _state_db_path():
    from hermes_constants import get_hermes_home

    return get_hermes_home() / "state.db"


def _user_rows(session_id: str) -> List[Tuple[int, str]]:
    """Read-only user rows. Raises on any read error, including a missing database."""
    path = _state_db_path()
    if not path.exists():
        raise OSError("state_db_missing")
    uri = f"file:{path.as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=5.0)
    try:
        rows = conn.execute(
            "SELECT id, content FROM messages "
            "WHERE session_id = ? AND role = 'user' AND active = 1 "
            "ORDER BY id ASC",
            (session_id,),
        ).fetchall()
    finally:
        conn.close()
    parsed: List[Tuple[int, str]] = []
    for row_id, content in rows:
        parsed.append((int(row_id), "" if content is None else str(content)))
    return parsed


def _snapshot(session_id: str, turn_id: str) -> None:
    """Max user-row id that exists now. None means the read failed.

    An empty messages table is id 0, not a failure: this turn's row is often
    flushed after pre_llm_call.
    """
    # P8-SEND: snapshot is the high-water mark, not this turn's text — P8-D06
    failed = False
    user_id: Optional[int] = 0
    try:
        rows = _user_rows(session_id)
        if rows:
            user_id = rows[-1][0]
    except Exception:
        failed = True
        user_id = None
    with _lock:
        _snapshots[turn_id] = UserSnapshot(
            session_id=session_id, user_id=user_id, failed=failed
        )


def on_pre_llm_call(*, session_id: str, turn_id: str, user_message: str) -> None:
    """Snapshot the user row and, when the passphrase matches a live review, authorize."""
    # P8-SEND: the model never authorizes; only this hook does — P8-D02
    if not session_id or not turn_id:
        return
    _snapshot(session_id, turn_id)
    # P9-FIX-ARM: a passphrase without a client-origin ticket writes no authorization — P8-D02
    try:
        from . import turn_context
    except ImportError:
        import turn_context  # type: ignore
    if not turn_context.is_brian_turn(turn_id):
        return
    with _lock:
        draft = _pending.get(session_id)
        if draft is None or not _live(draft):
            return
        if not passphrase_match(user_message):
            return
        _auths[turn_id] = Authorization(
            draft_id=draft.draft_id,
            content_hash=draft.content_hash,
            turn_id=turn_id,
            session_id=session_id,
            used=False,
        )
        draft_id = draft.draft_id
    log_decision(decision="authorized", draft_id=draft_id)


def _newer_user_rows(turn_id: str) -> Optional[List[str]]:
    """User rows committed after the pre_llm snapshot. None on a read error."""
    with _lock:
        snap = _snapshots.get(turn_id)
    if snap is None or snap.failed or snap.user_id is None:
        return None
    try:
        rows = _user_rows(snap.session_id)
    except Exception:
        return None
    return [content for row_id, content in rows if row_id > snap.user_id]


def turn_changed(turn_id: str) -> bool:
    """True when a row newer than the snapshot is not this turn's own late flush.

    The authorization already matched pre_llm_call's user_message. The snapshot
    row itself is not checked again. Zero newer rows is unchanged. One newer row
    is unchanged only when it is the passphrase (the flush that landed after
    pre_llm_call). Any other newer row, or more than one, is turn_changed.
    """
    # P8-SEND: a merged redirect is a second user row and cancels the send — P8-D06
    newer = _newer_user_rows(turn_id)
    if newer is None:
        return True
    if not newer:
        return False
    if len(newer) == 1 and passphrase_match(newer[0]):
        return False
    return True


def current_turn_text(turn_id: str) -> Optional[str]:
    """This turn's text: the TurnRecord plus user rows flushed after the snapshot.

    None when the read fails (delete then refuses). The snapshot row is an earlier
    turn and is not included.
    """
    newer = _newer_user_rows(turn_id)
    if newer is None:
        return None
    record = turn_context.get_record(turn_id)
    base = record.user_message if record is not None else ""
    parts = [base] if base else []
    parts.extend(newer)
    return "\n".join(parts)


def begin_send(session_id: str, turn_id: str, draft_id: str) -> Tuple[str, Optional[SendGrant]]:
    """Consume this turn's authorization, or return a refusal reason. No Gmail call."""
    with _lock:
        draft = _pending.get(session_id)
        if draft is None or not _live(draft):
            return REASON_NOT_REVIEWED, None
        if draft.draft_id != draft_id:
            return REASON_WRONG_DRAFT, None
        auth = _auths.get(turn_id)
        if auth is None:
            for other in _auths.values():
                if (
                    other.session_id == session_id
                    and other.draft_id == draft_id
                    and other.turn_id != turn_id
                ):
                    return REASON_WRONG_TURN, None
            return REASON_NO_AUTHORIZATION, None
        if auth.used:
            return REASON_USED, None
        if auth.draft_id != draft_id:
            return REASON_WRONG_DRAFT, None
        if auth.content_hash != draft.content_hash:
            return REASON_CONTENT_CHANGED, None
        auth.used = True
        return "ok", SendGrant(
            draft_id=auth.draft_id,
            content_hash=auth.content_hash,
            turn_id=auth.turn_id,
            session_id=auth.session_id,
        )


def live_hash(session_id: str) -> Optional[str]:
    with _lock:
        draft = _pending.get(session_id)
        if draft is None or not _live(draft):
            return None
        return draft.content_hash


def _end_origin_turn(turn_id: str = "") -> None:
    # P9-FIX-ARM: drop the thread flag and this turn's binding; the sync permit stays — P8-D02
    try:
        import origin

        origin.end_turn(turn_id)
    except Exception:
        pass


def post_llm_call_hook(**kwargs: Any) -> None:
    """Mark the presented draft reviewed when the reply covers it, then end the turn's authorization."""
    _end_origin_turn(str(kwargs.get("turn_id") or ""))
    session_id = str(kwargs.get("session_id") or "")
    turn_id = str(kwargs.get("turn_id") or "")
    reply = kwargs.get("assistant_response")
    if not isinstance(reply, str):
        reply = ""
    try:
        reviewed_id = ""
        with _lock:
            draft = _pending.get(session_id)
            if (
                draft is not None
                and draft.turn_id == turn_id
                and not draft.reviewed
                and _covers(reply, draft)
            ):
                draft.reviewed = True
                draft.reviewed_at = _now()
                reviewed_id = draft.draft_id
        if reviewed_id:
            log_decision(decision="reviewed", draft_id=reviewed_id)
    except Exception:
        pass
    try:
        clear_authorization(turn_id)
    except Exception:
        pass


def on_session_end_hook(**kwargs: Any) -> None:
    """Leave the pending draft in place.

    Hermes invokes this hook at the end of every turn
    (agent/turn_finalizer.py, the on_session_end call after the turn result).
    Clearing here made the next turn not_reviewed and not_own_draft.
    post_llm_call already drops this turn's authorization. The draft stays
    until 900 seconds after review, a newer present() for this session_id,
    or an interrupt.
    """
    # P8-SEND: per-turn on_session_end must not drop the reviewed draft — P8-D05
    # P9-FIX-ARM: this hook runs on the turn thread, including an interrupt — P8-D02
    _end_origin_turn(str(kwargs.get("turn_id") or ""))


def agent_loop_stopped_hook(**kwargs: Any) -> None:
    """Drop the draft when a live turn is interrupted, not when a turn finishes.

    tui_gateway/session_lifecycle.py fires this only inside the interrupt path
    (should_interrupt). gateway/run_agent_cache.py fires it only when a running
    agent is interrupted. hermes_cli/plugins.py documents the same: /stop, or
    /new while an agent is running. A finished turn does not call it.
    """
    # P8-SEND: interrupt still drops the draft; turn end does not — P8-D05
    # P9-FIX-ARM: clears this thread only; the turn thread is cleared in on_session_end — P8-D02
    _end_origin_turn(str(kwargs.get("turn_id") or ""))
    session_id = str(kwargs.get("session_key") or kwargs.get("session_id") or "")
    try:
        clear_session(session_id)
    except Exception:
        pass


def pending_for_tests(session_id: str) -> Optional[Dict[str, Any]]:
    with _lock:
        draft = _pending.get(session_id)
        if draft is None:
            return None
        return {
            "draft_id": draft.draft_id,
            "content_hash": draft.content_hash,
            "turn_id": draft.turn_id,
            "reviewed": draft.reviewed,
            "reviewed_at": draft.reviewed_at,
            "readback": draft.readback,
            "live": _live(draft),
        }


def authorization_for_tests(turn_id: str) -> Optional[Dict[str, Any]]:
    with _lock:
        auth = _auths.get(turn_id)
        if auth is None:
            return None
        return {
            "draft_id": auth.draft_id,
            "content_hash": auth.content_hash,
            "turn_id": auth.turn_id,
            "used": auth.used,
        }
