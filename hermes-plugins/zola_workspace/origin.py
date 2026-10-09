"""Client-origin tickets for prompt.submit (P9-FIX-ARM). Process memory only."""

from __future__ import annotations

import hashlib
import logging
import sys
import threading
import time
import contextvars
from typing import Any, Optional

# P9-FIX-ARM: marker so a reload does not wrap the wrapper — P8-D02
MARKER = "_p9_fix_arm_wrap"
ORIGIN_MODULE_MARKER = "p9-fix-arm"

# P9-FIX-ARM: covers the default 600s agent build wait and the turn-record TTL — P8-D02
TICKET_TTL_SECONDS = 900

# P9-FIX-ARM: a long serve must not grow the turn maps without bound — P8-D02
_BOUND_CAP = 256
_LOGGED_CAP = 256
_SYNC_CAP = 256

REASON_UNKNOWN = "origin_unknown"
REASON_WRAP_MISSING = "origin_wrap_missing"
REASON_CHECK_ERROR = "origin_check_error"

_REASONS = frozenset({REASON_UNKNOWN, REASON_WRAP_MISSING, REASON_CHECK_ERROR})

class _TicketBucket:
    """One session's tickets. Identity is the session object (`is`), not id()."""

    __slots__ = ("session", "items")

    def __init__(self, session: dict) -> None:
        self.session = session
        self.items: list[tuple[str, float]] = []


_lock = threading.Lock()
# P9-FIX-ARM: the session object itself is the key (`is`), not id() — P8-D02
_pending: list[_TicketBucket] = []
_bound: dict[str, float] = {}
_logged: dict[tuple[str, str], float] = {}
# P9-FIX-ARM: one permit per consumed text; sync matches the hash, not a remembered turn id — P8-D02
_sync_ready: list[tuple[str, str, float]] = []
_test_wrap_ok = False
_thread_ok: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "zola_origin_turn", default=False
)
_thread_turn_id: contextvars.ContextVar[str] = contextvars.ContextVar(
    "zola_origin_turn_id", default=""
)
_install_logged = False

_logger = logging.getLogger("zola_workspace")


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def in_serve_process() -> bool:
    # P9-FIX-ARM: the client starts `hermes serve`; other commands must not wrap — P8-D02
    return any(arg == "serve" for arg in sys.argv)


def wrap_ok() -> bool:
    """True only when prompt.submit is our wrapper, or a unit test granted the flag."""
    mod = sys.modules.get("tui_gateway.server")
    if mod is not None:
        methods = getattr(mod, "_methods", None)
        fn = methods.get("prompt.submit") if isinstance(methods, dict) else None
        return bool(getattr(fn, MARKER, False))
    return _test_wrap_ok


def _prune_timed_locked(table: dict, now: float, cap: int) -> None:
    expired = [key for key, created in table.items() if now - created > TICKET_TTL_SECONDS]
    for key in expired:
        table.pop(key, None)
    overflow = len(table) - cap
    if overflow <= 0:
        return
    oldest = sorted(table.items(), key=lambda item: item[1])[:overflow]
    for key, _created in oldest:
        table.pop(key, None)


def _bind(turn_id: str) -> None:
    tid = str(turn_id or "")
    if not tid:
        return
    now = time.monotonic()
    with _lock:
        _bound[tid] = now
        _prune_timed_locked(_bound, now, _BOUND_CAP)


def _prune_sync_locked(now: float) -> None:
    _sync_ready[:] = [item for item in _sync_ready if now - item[2] <= TICKET_TTL_SECONDS]
    overflow = len(_sync_ready) - _SYNC_CAP
    if overflow <= 0:
        return
    ordered = sorted(_sync_ready, key=lambda item: item[2])
    del ordered[:overflow]
    _sync_ready[:] = ordered


def _note_sync_ready(turn_id: str, user_message: str) -> None:
    tid = str(turn_id or "")
    message = user_message if isinstance(user_message, str) else ""
    if not tid or not message:
        return
    now = time.monotonic()
    with _lock:
        _sync_ready.append((tid, text_hash(message), now))
        _prune_sync_locked(now)


def _bound_unexpired(turn_id: str) -> bool:
    tid = str(turn_id or "")
    if not tid:
        return False
    now = time.monotonic()
    with _lock:
        created = _bound.get(tid)
        if created is None:
            return False
        if now - created > TICKET_TTL_SECONDS:
            _bound.pop(tid, None)
            return False
        return True


def turn_is_bound(turn_id: str) -> bool:
    if not wrap_ok():
        return False
    return _bound_unexpired(turn_id)


def thread_turn_is_client() -> bool:
    try:
        return bool(_thread_ok.get()) and wrap_ok()
    except Exception:
        return False


def current_turn_id() -> str:
    try:
        return str(_thread_turn_id.get() or "")
    except Exception:
        return ""


def _mark_thread(turn_id: str) -> None:
    try:
        _thread_ok.set(True)
        _thread_turn_id.set(str(turn_id or ""))
    except Exception:
        pass


def _clear_thread() -> None:
    # P9-FIX-ARM: the flag must not outlive the turn that consumed the ticket — P8-D02
    try:
        _thread_ok.set(False)
    except Exception:
        pass
    try:
        _thread_turn_id.set("")
    except Exception:
        pass


def end_turn(turn_id: str = "") -> None:
    """Drop this thread's origin flag and this turn's binding. The sync permit stays."""
    current = current_turn_id()
    _clear_thread()
    ids = {str(turn_id or ""), current}
    ids.discard("")
    if not ids:
        return
    with _lock:
        for tid in ids:
            _bound.pop(tid, None)


def take_sync_for_text(user_content: str) -> bool:
    """One pending-row write when this text is an unexpired consumed turn. A miss leaves other permits."""
    if not wrap_ok():
        return False
    message = user_content if isinstance(user_content, str) else ""
    if not message:
        return False
    digest = text_hash(message)
    now = time.monotonic()
    with _lock:
        _prune_sync_locked(now)
        for index, (_tid, item_digest, _created) in enumerate(_sync_ready):
            if item_digest == digest:
                del _sync_ready[index]
                return True
        return False


def refusal_reason(turn_id: str) -> str:
    try:
        if not wrap_ok():
            return REASON_WRAP_MISSING
        if not _bound_unexpired(turn_id):
            return REASON_UNKNOWN
        return ""
    except Exception:
        return REASON_CHECK_ERROR


def log_refuse(reason: str, turn_id: str = "") -> None:
    # P9-FIX-ARM: metadata only; the reason token never carries the prompt — P8-D02
    token = reason if reason in _REASONS else REASON_CHECK_ERROR
    key = (token, str(turn_id or "") or "-")
    now = time.monotonic()
    with _lock:
        _prune_timed_locked(_logged, now, _LOGGED_CAP)
        if key in _logged:
            return
        _logged[key] = now
        _prune_timed_locked(_logged, now, _LOGGED_CAP)
    try:
        _logger.info("gate brian_only action=refuse reason=%s", token)
    except Exception:
        pass


def grant_turn_for_tests(turn_id: str, user_message: str = "") -> None:
    """Mark one turn as client-origin without a gateway. Serve tests use the real wrap."""
    global _test_wrap_ok
    if sys.modules.get("tui_gateway.server") is None:
        _test_wrap_ok = True
    _bind(turn_id)
    if user_message:
        _note_sync_ready(turn_id, user_message)
    _mark_thread(turn_id)


def clear_for_tests() -> None:
    global _test_wrap_ok
    with _lock:
        _pending.clear()
        _bound.clear()
        _logged.clear()
        _sync_ready.clear()
    _test_wrap_ok = False
    _clear_thread()


def _sanitize(params: dict) -> str:
    raw = params.get("text", "")
    if not isinstance(raw, str):
        return ""
    from hermes_cli.input_sanitize import sanitize_user_prompt_text

    return sanitize_user_prompt_text(raw)


def _is_slash(text: str) -> bool:
    # P9-FIX-ARM: slash prompts are a known fail-closed limit — P8-D02
    return text.lstrip().startswith("/")


def _is_delivery_author(value: Any) -> bool:
    if value is None:
        return False
    try:
        from tools.bot_relay import DeliveryAuthor
    except Exception:
        return type(value).__name__ == "DeliveryAuthor"
    return isinstance(value, DeliveryAuthor)


def _may_mint(params: dict) -> bool:
    # P9-FIX-ARM: only a real prompt.submit RPC, never hosted or relay authorship — P8-D02
    try:
        import tui_gateway.server as server
    except Exception:
        return False
    if server._current_rpc_method.get() != "prompt.submit":
        return False
    if params.get("_hosted_task") is not None:
        return False
    if params.get("_hosted_terminal_callback") is not None:
        return False
    if _is_delivery_author(params.get("_turn_author")):
        return False
    return True


def _session_for(params: dict) -> Optional[dict]:
    import tui_gateway.server as server

    sid = params.get("session_id") or ""
    if not isinstance(sid, str) or not sid:
        return None
    session = server._sessions.get(sid)
    return session if isinstance(session, dict) else None


def _current_session() -> Optional[dict]:
    import tui_gateway.server as server

    session = server._current_runtime_session_record.get()
    return session if isinstance(session, dict) else None


def _find_bucket(session: dict) -> Optional[_TicketBucket]:
    for bucket in _pending:
        if bucket.session is session:
            return bucket
    return None


def _drop_expired_locked(now: float) -> None:
    kept: list[_TicketBucket] = []
    for bucket in _pending:
        bucket.items = [item for item in bucket.items if item[1] > now]
        if bucket.items:
            kept.append(bucket)
    _pending[:] = kept


def mint(session: dict, text: str) -> None:
    digest = text_hash(text)
    expires = time.monotonic() + TICKET_TTL_SECONDS
    now = time.monotonic()
    with _lock:
        _drop_expired_locked(now)
        bucket = _find_bucket(session)
        if bucket is None:
            bucket = _TicketBucket(session)
            _pending.append(bucket)
        bucket.items.append((digest, expires))


def revoke(session: dict, text: str) -> None:
    digest = text_hash(text)
    with _lock:
        bucket = _find_bucket(session)
        if bucket is None:
            return
        for index, (item_digest, _exp) in enumerate(bucket.items):
            if item_digest == digest:
                del bucket.items[index]
                break
        if not bucket.items:
            _pending.remove(bucket)


def pending_count_for_tests(session: dict) -> int:
    now = time.monotonic()
    with _lock:
        bucket = _find_bucket(session)
        if bucket is None:
            return 0
        return sum(1 for _digest, exp in bucket.items if exp > now)


def _take_match(session: dict, digest: str) -> bool:
    now = time.monotonic()
    with _lock:
        bucket = _find_bucket(session)
        if bucket is None:
            return False
        # P9-FIX-ARM: a miss drops expired tickets only; other pending lines stay — P8-D02
        live = [item for item in bucket.items if item[1] > now]
        for index, (item_digest, _exp) in enumerate(live):
            if item_digest == digest:
                del live[index]
                bucket.items = live
                if not live:
                    _pending.remove(bucket)
                return True
        bucket.items = live
        if not live:
            _pending.remove(bucket)
        return False


def consume_for_hook(turn_id: str, user_message: str) -> str:
    """Bind turn_id to a matching ticket. Empty string means this turn is client-origin."""
    # P9-FIX-ARM: clear before any return so a miss cannot inherit the previous turn — P8-D02
    _clear_thread()
    tid = str(turn_id or "")
    try:
        if not wrap_ok():
            return REASON_WRAP_MISSING
        if _bound_unexpired(tid):
            _mark_thread(tid)
            return ""
        session = _current_session()
        message = user_message if isinstance(user_message, str) else ""
        if session is None or not tid or not _take_match(session, text_hash(message)):
            return REASON_UNKNOWN
        _bind(tid)
        _note_sync_ready(tid, message)
        _mark_thread(tid)
        return ""
    except Exception:
        _clear_thread()
        return REASON_CHECK_ERROR


def _queue_holds_exact(session: dict, text: str) -> bool:
    entries = []
    head = session.get("queued_prompt")
    if isinstance(head, dict):
        entries.append(head)
    for item in session.get("queued_prompts") or []:
        if isinstance(item, dict):
            entries.append(item)
    return any(item.get("text") == text for item in entries)


def _keep_ticket(response: Any, session: dict, text: str) -> bool:
    # P9-FIX-ARM: keep only when a turn starts or the queue still holds this exact text — P8-D02
    if not isinstance(response, dict) or "error" in response:
        return False
    result = response.get("result")
    if not isinstance(result, dict) or result.get("voice_stopped"):
        return False
    status = result.get("status")
    if status == "streaming":
        return True
    if status == "queued":
        return _queue_holds_exact(session, text)
    return False


def _dispatch(original: Any, rid: Any, params: Any) -> Any:
    ticket: Optional[tuple[dict, str]] = None
    if isinstance(params, dict) and _may_mint(params):
        text = _sanitize(params)
        session = _session_for(params)
        if session is not None and text and not _is_slash(text):
            mint(session, text)
            ticket = (session, text)
    try:
        response = original(rid, params)
    except Exception:
        if ticket is not None:
            revoke(ticket[0], ticket[1])
        raise
    if ticket is not None and not _keep_ticket(response, ticket[0], ticket[1]):
        revoke(ticket[0], ticket[1])
    return response


def install_wrap() -> bool:
    """Wrap prompt.submit once. Importing the gateway here is the serve-process install."""
    global _install_logged
    import tui_gateway.server as server

    current = server._methods.get("prompt.submit")
    if current is None:
        return False
    if getattr(current, MARKER, False):
        return True
    # P9-FIX-ARM: store the original so reload cannot stack wrappers — P8-D02

    def wrapper(rid: Any, params: Any = None) -> Any:
        return _dispatch(current, rid, params)

    setattr(wrapper, MARKER, True)
    setattr(wrapper, "_p9_original", current)
    server._methods["prompt.submit"] = wrapper
    if not _install_logged:
        _install_logged = True
        try:
            # P9-FIX-ARM: one install line, method name only — P8-D02
            _logger.info("origin wrap installed method=prompt.submit")
        except Exception:
            pass
    return True


def install_for_serve() -> bool:
    if not in_serve_process():
        return False
    try:
        installed = install_wrap()
    except Exception:
        installed = False
    if not installed:
        try:
            # P9-FIX-ARM: serve installed nothing; metadata only, no prompt text — P8-D02
            _logger.warning("origin wrap missing method=prompt.submit")
        except Exception:
            pass
    return installed
