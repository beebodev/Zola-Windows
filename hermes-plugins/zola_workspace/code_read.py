"""phone_read_code: the tool half of the code path (P10-READ, mechanism B).

The value of a code never passes through this process. The flow is:

  1. Brian's own message for this turn asks for the code (code_phrase), and the item is a masked
     verification-code text from the listing Zola just gave him.
  2. This tool arms one read in zola-phone and gets an opaque handle (60 s).
  3. It sends ONE Hermes server request, `code_read`, to the client carrying only that handle, and
     waits on that same request's response (45 s). The client redeems the handle on the zola-phone
     pipe, speaks or shows the value locally, and answers read, shown, failed, or cancelled.
  4. On every exit the tool disarms the handle. The model gets one fixed sentence, never the value.

Why a blocked tool does not block the client: tui_gateway.server_requests.send writes the request
frame and then waits on a threading.Event on the agent thread. The websocket dispatcher is a
different thread, so the client receives the frame and answers it with a normal JSON-RPC response,
which server_requests.resolve_response matches by id. The clarify tool waits the same way.
"""

from __future__ import annotations

import sys
import threading
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

try:
    from . import code_phrase
    from . import framing
    from . import log as wslog
    from . import phone_tools
    from . import proactive_store
    from . import surface
    from . import turn_context
except ImportError:  # flat unittest discover
    import code_phrase  # type: ignore
    import framing  # type: ignore
    import log as wslog  # type: ignore
    import phone_tools  # type: ignore
    import proactive_store  # type: ignore
    import surface  # type: ignore
    import turn_context  # type: ignore

TOOL_NAME = "phone_read_code"
TOOLSET_NAME = "zola_workspace"
METHOD_CODE_READ = "code_read"

# P10-READ: handle 60 s, tool wait 45 s, and the client's own deadline (35 s) is shorter than the wait
CODE_HANDLE_TTL_SECONDS = 60
CODE_TOOL_WAIT_SECONDS = 45.0
CODE_CLIENT_DEADLINE_SECONDS = 35.0
CODE_AGE_LIMIT_SECONDS = 24 * 3600

OUTCOME_READ = "read"
OUTCOME_SHOWN = "shown"
OUTCOME_FAILED = "failed"
OUTCOME_CANCELLED = "cancelled"

# Every sentence the model can get. None of them contains a value.
SENTENCE_READ = "The code was read to Brian."
SENTENCE_SHOWN = "The code was shown to Brian."
SENTENCE_CANCELLED = "The read was cancelled, so nothing was read. Don't say it was."
SENTENCE_NO_ANSWER = "The read timed out or was cancelled, so nothing was read. Don't say it was."
SENTENCE_FAILED = "I couldn't read the code out. Don't say it was read."
SENTENCE_NOT_BRIAN = "That needs Brian's own turn."
SENTENCE_NOT_ASKED = (
    "I only read a code out when Brian asks me to himself, right now, in his own words. "
    "Ask him if he wants it read."
)
SENTENCE_STALE_HANDLE = "That one isn't on the list I just gave. Ask what's pending again."
SENTENCE_NO_LIST = "I couldn't check what's pending just now."
SENTENCE_NO_SESSION = "I can't tell which conversation this is, so I won't read a code."
SENTENCE_NOTIFICATION = "That one is a notification. The code is only on Brian's phone."
SENTENCE_NOT_TEXT = "That isn't a text message."
SENTENCE_GONE = "That one is no longer pending."
SENTENCE_NO_CODE = "That text doesn't have a code I can read out."
SENTENCE_LINK = "That is a reset link, not a code. I don't read links out."
SENTENCE_UNSURE = "I'm not sure that text has a code in it, so I won't read it out."
SENTENCE_OLD = "That code is more than a day old, so I won't read it out."
SENTENCE_NO_CLIENT = "I couldn't reach the part of Zola that speaks it, so I didn't read it."
# P10-READ F9: Hermes private registry / session lookup missing or changed
SENTENCE_HERMES = "I can't read codes out right now."

FAILURE_SENTENCES = {
    "not_identifiable": "The phone couldn't find a code in that text, so nothing was read.",
    "no_connection": phone_tools.SENTENCE_NO_CONNECTION,
    "not_paired": phone_tools.SENTENCE_NOT_PAIRED,
    "timeout": phone_tools.SENTENCE_TIMEOUT,
    "phone_unavailable": phone_tools.SENTENCE_NO_CONNECTION,
    "expired": "The read took too long and expired, so nothing was read.",
    "deadline": "The read took too long and expired, so nothing was read.",
    "busy": "I was already reading another code, so nothing was read.",
    "not_a_code": SENTENCE_LINK,
    "playback_failed": "The voice didn't work, so nothing was read.",
    "wrong_session": "That read belonged to a different conversation, so nothing was read.",
}

# Injectable seams for tests
_server_send: Optional[Callable[[str, str, Dict[str, Any], float], Optional[Dict[str, Any]]]] = None


def set_server_send_for_tests(fn: Optional[Callable[..., Optional[Dict[str, Any]]]]) -> None:
    global _server_send
    _server_send = fn


_contract_lock = threading.Lock()
_contract_ready = False


def ensure_contract() -> bool:
    """Declare the code_read server request with Hermes' own contract registry, once.

    server_requests.send refuses a method with no contract. The plugin adds its own entry at run
    time, so nothing under hermes-agent changes. False when the registry cannot be reached.
    """
    global _contract_ready
    if _contract_ready:
        return True
    with _contract_lock:
        if _contract_ready:
            return True
        try:
            from tui_gateway.contracts import registry
            from tui_gateway.contracts.base import Result
            from tui_gateway.contracts.server_requests import ServerRequestParams

            if METHOD_CODE_READ not in registry.SERVER_REQUESTS:

                class CodeReadRequestParams(ServerRequestParams):
                    handle: str
                    prefer_show: bool = False

                class CodeReadResult(Result):
                    outcome: str
                    reason: Optional[str] = None

                registry.server_request(
                    METHOD_CODE_READ,
                    params=CodeReadRequestParams,
                    result=CodeReadResult,
                    doc="Zola's code reader: the client redeems the handle, speaks or shows the code, and answers.",
                )
            _contract_ready = True
        except Exception:
            return False
    return True


def reset_for_tests() -> None:
    global _contract_ready, _server_send
    _server_send = None
    _contract_ready = False


def hermes_internals_present() -> Tuple[bool, str]:
    """True when the named Hermes pieces this tool leans on are importable with the expected attributes.

    P10-READ F9: a Hermes upgrade that renames these must fail the pin test and refuse at run time with
    SENTENCE_HERMES (reason=hermes_internals), not the timeout sentence.

    The server module is only attribute-checked when already imported (serve process). Unit tests that
    inject `_server_send` never load it; the pin test imports it explicitly before calling this.
    """
    try:
        from tui_gateway.contracts import registry
        from tui_gateway import server_requests
    except Exception:
        return False, "import_contracts"
    if not hasattr(registry, "SERVER_REQUESTS") or not hasattr(registry, "server_request"):
        return False, "registry_api"
    if not hasattr(server_requests, "send"):
        return False, "server_requests_send"
    hermes_server = sys.modules.get("tui_gateway.server")
    if hermes_server is None:
        return True, "ok_contracts_only"
    if not hasattr(hermes_server, "_sessions"):
        return False, "no__sessions"
    if not hasattr(hermes_server, "_current_runtime_session_record"):
        return False, "no__current_runtime_session_record"
    return True, "ok"


def gateway_sid(record: Any) -> str:
    """The gateway's session id for this turn. Empty when it cannot be told apart."""
    ok, _why = hermes_internals_present()
    if not ok:
        return ""
    server = sys.modules.get("tui_gateway.server")
    if server is None:
        try:
            import tui_gateway.server as server  # type: ignore
        except Exception:
            return ""
    sessions = getattr(server, "_sessions", None)
    if not isinstance(sessions, dict):
        return ""
    items = list(sessions.items())
    try:
        current = server._current_runtime_session_record.get()
    except Exception:
        current = None
    if isinstance(current, dict):
        for sid, session in items:
            if session is current:
                return str(sid)
    keys = {str(getattr(record, "task_id", "") or ""), str(getattr(record, "session_id", "") or "")} - {""}
    matches = [str(sid) for sid, session in items if isinstance(session, dict) and session.get("session_key") in keys]
    if len(matches) == 1:
        return matches[0]
    for key in keys:
        if key in sessions:
            return key
    return ""


def _send(sid: str, handle: str, prefer_show: bool = False) -> Optional[Dict[str, Any]]:
    params: Dict[str, Any] = {"handle": handle, "prefer_show": bool(prefer_show)}
    if _server_send is not None:
        return _server_send(METHOD_CODE_READ, sid, params, CODE_TOOL_WAIT_SECONDS)
    if not ensure_contract():
        return None
    from tui_gateway import server_requests

    return server_requests.send(METHOD_CODE_READ, sid, params, timeout=CODE_TOOL_WAIT_SECONDS)


def outcome_sentence(result: Optional[Dict[str, Any]]) -> Tuple[str, str]:
    """(state, sentence). Only fixed strings leave here; a value in the result is ignored."""
    if not isinstance(result, dict):
        return "no_answer", SENTENCE_NO_ANSWER
    outcome = result.get("outcome")
    if outcome == OUTCOME_READ:
        return OUTCOME_READ, SENTENCE_READ
    if outcome == OUTCOME_SHOWN:
        return OUTCOME_SHOWN, SENTENCE_SHOWN
    if outcome == OUTCOME_CANCELLED:
        return OUTCOME_CANCELLED, SENTENCE_CANCELLED
    if outcome == OUTCOME_FAILED:
        reason = str(result.get("reason") or "")
        return OUTCOME_FAILED, FAILURE_SENTENCES.get(reason, SENTENCE_FAILED)
    return "no_answer", SENTENCE_NO_ANSWER


def _log(state: str, **fields: Any) -> None:
    try:
        wslog.write_event(wslog.LOG_EVENT_PHONE_CODE, state=state, **fields)
    except Exception:
        pass


def _say(text: str) -> str:
    return framing.frame_untrusted(TOOL_NAME, text)


# ── tool ─────────────────────────────────────────────────────────────────────────────────────

_DESCRIPTION = (
    "Read a verification code from a text on Brian's phone out loud, or show it, on this computer only. "
    "Use it only when Brian has just asked for the code in his own message, and pass the handle of "
    "that text from the pending list. The code itself never comes back to you; you get one sentence "
    "saying whether it was read. Never say, guess, or repeat a code yourself."
)

_SCHEMA: Dict[str, Any] = {
    "name": TOOL_NAME,
    "description": _DESCRIPTION,
    "parameters": {
        "type": "object",
        "properties": {"handle": {"type": "string", "description": "Handle of one text from the pending list."}},
        "required": ["handle"],
        "additionalProperties": False,
    },
}


def code_schema() -> Dict[str, Any]:
    return dict(_SCHEMA)


def classify_row(row: Any, now: datetime) -> Tuple[bool, str]:
    """Can this stored phone item be read out? (ok, sentence). Fail closed."""
    if row is None or row["closed_at"] or row["content_state"] != "available":
        return False, SENTENCE_GONE
    source = str(row["source"] or "")
    if source == "notif":
        return False, SENTENCE_NOTIFICATION
    if source not in proactive_store.PHONE_TEXT_KINDS:
        return False, SENTENCE_NOT_TEXT
    mask = row["mask_kind"]
    if not mask:
        return False, SENTENCE_NO_CODE
    if mask == "reset_link":
        return False, SENTENCE_LINK
    if mask != "verification_code":
        return False, SENTENCE_UNSURE
    detected = surface._parse_iso(row["detected_at"])
    if detected is None or (now - detected).total_seconds() > CODE_AGE_LIMIT_SECONDS:
        return False, SENTENCE_OLD
    if not str(row["message_id"] or ""):
        return False, SENTENCE_NO_CODE
    return True, ""


def _age_words(now: datetime, row: Any) -> str:
    detected = surface._parse_iso(row["detected_at"])
    if detected is None:
        return "earlier"
    minutes = max(0, int((now - detected).total_seconds() // 60))
    if minutes < 2:
        return "a minute ago"
    if minutes < 90:
        return "%d minutes ago" % minutes
    return "about %d hours ago" % round(minutes / 60)


def phone_read_code_handler(args: Any = None, **kwargs: Any) -> str:
    started = time.monotonic()
    try:
        return _read_code(args if isinstance(args, dict) else {}, started)
    except Exception:
        _log("error", reason="internal_error", ms=int((time.monotonic() - started) * 1000))
        return _say(SENTENCE_FAILED)


def _read_code(args: Dict[str, Any], started: float) -> str:
    def ms() -> int:
        return int((time.monotonic() - started) * 1000)

    turn_id = turn_context.current_turn_id_from_context()
    if not turn_id or not turn_context.is_brian_turn(turn_id):
        _log("refused", reason="not_brian", ms=ms())
        return _say(SENTENCE_NOT_BRIAN)
    record = turn_context.get_record(turn_id)
    if record is None:
        _log("refused", reason="no_record", ms=ms())
        return _say(SENTENCE_NOT_BRIAN)
    # the current message must ask for this; nothing the model read or was shown counts
    asked, why, after = code_phrase.check(record.user_message if isinstance(record.user_message, str) else "")
    if not asked:
        _log("refused", reason="phrase_" + why, ms=ms())
        return _say(SENTENCE_NOT_ASKED)
    handle = str(args.get("handle") or "")
    conn = surface._connect()
    if conn is None:
        _log("refused", reason="no_store", ms=ms())
        return _say(SENTENCE_NO_LIST)
    try:
        now = surface._clock()
        item_id = surface._handle_live(record.session_id, handle, now) if handle else None
        if not item_id:
            _log("refused", reason="stale_handle", ms=ms())
            return _say(SENTENCE_STALE_HANDLE)
        row = proactive_store._item(conn, item_id)
        ok, sentence = classify_row(row, now)
        if not ok:
            _log("refused", reason="item", ms=ms())
            return _say(sentence)
        state = surface._listing_state(record.session_id, now) or {}
        candidates: List[Tuple[str, Any]] = []
        for other_handle, other_id in dict(state.get("items") or {}).items():
            other = proactive_store._item(conn, other_id)
            if classify_row(other, now)[0]:
                candidates.append((other_handle, other))
        if len(candidates) > 1:
            ordered = sorted(candidates, key=lambda pair: str(pair[1]["detected_at"] or ""))
            choice = code_phrase.recency_choice(after)
            # newest/latest is unambiguous at any count; older only when exactly two (verdict 2)
            if choice == "newest":
                handle, row = ordered[-1]
            elif choice == "oldest" and len(candidates) == 2:
                handle, row = ordered[0]
            else:
                ages = ", ".join(_age_words(now, pair[1]) for pair in reversed(ordered))
                _log("refused", reason="two_codes", count=len(candidates), ms=ms())
                if len(candidates) == 2:
                    ask = (
                        "There is more than one code pending (%s). Ask Brian which one: the newest, or the older one."
                        % ages
                    )
                else:
                    ask = "There is more than one code pending (%s). Ask Brian which one." % ages
                return _say(ask)
            item_id = str(row["id"] or "")
        provider_id = str(row["message_id"] or "")
        kind = str(row["source"] or "")
    finally:
        conn.close()
    ok_hermes, hermes_why = hermes_internals_present()
    if not ok_hermes or not ensure_contract():
        _log("refused", reason="hermes_internals", detail=hermes_why, ms=ms())
        return _say(SENTENCE_HERMES)
    sid = gateway_sid(record)
    if not sid:
        _log("refused", reason="no_session", ms=ms())
        return _say(SENTENCE_NO_SESSION)
    armed = phone_tools.phone_call(
        "code.arm", session_id=sid, turn_id=turn_id, item_id=item_id, provider_id=provider_id, kind=kind
    )
    if not armed.get("ok") or not armed.get("handle"):
        reason = str(armed.get("reason") or "no_connection")
        _log("failed", reason="arm_" + reason, ms=ms())
        return _say(FAILURE_SENTENCES.get(reason, phone_tools.SENTENCE_NO_CONNECTION))
    code_handle = str(armed["handle"])
    prefer_show = code_phrase.prefers_show(
        record.user_message if isinstance(record.user_message, str) else ""
    )
    result: Optional[Dict[str, Any]] = None
    try:
        result = _send(sid, code_handle, prefer_show=prefer_show)
    except Exception:
        result = None
    finally:
        # timeout, cancel, interrupt, or success: the arm is cleared on every exit
        try:
            phone_tools.phone_call("code.disarm", handle=code_handle)
        except Exception:
            pass
    state_word, sentence = outcome_sentence(result)
    reason = str((result or {}).get("reason") or "") if isinstance(result, dict) else ""
    _log(state_word, reason=reason or None, ms=ms())
    return _say(sentence)


def disarm_all_best_effort() -> None:
    """A serve restart loses any waiting tool, so clear every arm zola-phone still holds."""
    try:
        phone_tools.phone_call("code.disarm", all=True)
    except Exception:
        pass


def start_disarm_on_boot() -> None:
    """Serve process only: clear stale arms off the load path, on a daemon thread."""
    try:
        try:
            from . import origin
        except ImportError:
            import origin  # type: ignore
        if not origin.in_serve_process():
            return
        threading.Thread(target=disarm_all_best_effort, name="zola-code-disarm", daemon=True).start()
    except Exception:
        pass
