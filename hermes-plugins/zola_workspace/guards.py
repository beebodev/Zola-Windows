"""pre_tool_call guards — config/.env self-edit (defense in depth, P8-D02)."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

try:
    from . import log as wslog
except ImportError:  # P8-HARDEN: flat unittest discover — P8-D02
    import log as wslog

# P8-HARDEN: named guard constants — P8-D02
GUARD_CONFIG_SELF_EDIT = "config_self_edit"
GUARD_MEMORY_TAINT = "memory_taint"
GUARD_TERMINAL_GOOGLE = "terminal_google"

# P8-CONNECT: memory_taint enabled; terminal_google remains Track 3 inert — P8-D09
GUARD_MEMORY_TAINT_ENABLED = True
GUARD_TERMINAL_GOOGLE_ENABLED = False

ACTION_ALLOW = "allow"
ACTION_BLOCK = "block"

REASON_CONFIG_OR_ENV_WRITE = "config_or_env_write"
REASON_HERMES_CONFIG_CLI = "hermes_config_cli"
REASON_STUB_ALLOW = "stub_inert"
REASON_NOT_APPLICABLE = "not_applicable"
REASON_GUARD_ERROR = "guard_error"
REASON_MEMORY_TAINT_BLOCK = "memory_taint_block"
REASON_SKILL_MANAGE_TAINT = "skill_manage_taint"
REASON_MISSING_TURN = "missing_turn"
REASON_BATCH_OP = "batch_op_blocked"

BLOCK_MESSAGE_CONFIG_OR_ENV = (
    "Blocked: editing the live Hermes config.yaml or .env is not allowed."
)

# P8-CONNECT: exact Brian block message — P8-D09
BLOCK_MESSAGE_MEMORY_TAINT = (
    "Not saved: in this conversation, a memory can only use Brian's exact words "
    "from his current message. Save his words as he said them, or ask him to state the fact."
)

BLOCK_MESSAGE_SKILL_MANAGE = (
    "Blocked: skill_manage is not allowed in a Workspace-tainted conversation."
)

TOOL_MEMORY = "memory"
TOOL_SKILL_MANAGE = "skill_manage"
MEMORY_ACTION_ADD = "add"
MEMORY_ACTION_REPLACE = "replace"
MEMORY_ACTION_REMOVE = "remove"

TOOL_WRITE_FILE = "write_file"
TOOL_PATCH = "patch"
TOOL_TERMINAL = "terminal"
TOOL_READ_FILE = "read_file"

# Filename tokens only (Brian edit #2) — not location-alone
FILENAME_TOKEN_RE = re.compile(
    r"(?i)(?<![A-Za-z0-9_])(config\.yaml|CONFIG~1\.YAM|\.env)(?![A-Za-z0-9_])"
)

# Broader scan for file-tool path args / V4A (basename match)
SENSITIVE_BASENAME_RE = re.compile(
    r"(?i)(?:^|[/\\])(?:config\.yaml|CONFIG~1\.YAM|\.env)$"
)
SENSITIVE_BASENAME_IN_TEXT_RE = re.compile(
    r"(?i)(config\.yaml|CONFIG~1\.YAM|(?<![A-Za-z0-9_])\.env(?![A-Za-z0-9_]))"
)

# P8-HARDEN: write/delete/rename verbs incl. cmd + PS aliases; > / >> optional space — P8-D02
WRITE_DELETE_VERB_RE = re.compile(
    r"(?ix)"
    r"(?:"
    r"Set-Content|Out-File|Add-Content|Copy-Item|Move-Item|New-Item|"
    r"Remove-Item|Rename-Item|"
    r"\bdel\b|\berase\b|\brm\b|\bren\b|"
    r"\bcopy\b|\bmove\b|\bxcopy\b|\brobocopy\b|\brmdir\b|\brd\b|"
    r"\btee\b|\bcp\b|\bmv\b|"
    r"\bsc\b|\bac\b|\bni\b|\bri\b|\brni\b|\bmi\b|\bcpi\b|"
    r"\[IO\.File\]::(?:Write\w*|Delete\w*)|"
    r">>|>"
    r")"
)

HERMES_CONFIG_CLI_RE = re.compile(r"(?i)\bhermes\b.*\bconfig\b\s+(set|edit)\b")

V4A_FILE_HEADER_RE = re.compile(
    r"(?im)^\*\*\*\s+(?:Update|Add|Delete|Move)\s+File:\s*(.+)$"
)


def _norm(text: str) -> str:
    return (text or "").replace("/", "\\")


def _path_looks_sensitive(path_text: str) -> bool:
    """True if a path string names config.yaml, CONFIG~1.YAM, or .env."""
    raw = str(path_text or "").strip().strip('"').strip("'")
    if not raw:
        return False
    norm = _norm(raw)
    # Basename check
    base = norm.rsplit("\\", 1)[-1]
    if SENSITIVE_BASENAME_RE.search("\\" + base) or base.casefold() in {
        "config.yaml",
        "config~1.yam",
        ".env",
    }:
        return True
    if SENSITIVE_BASENAME_IN_TEXT_RE.search(norm):
        return True
    return False


def _text_has_sensitive_filename(text: str) -> bool:
    return bool(FILENAME_TOKEN_RE.search(text or "") or SENSITIVE_BASENAME_IN_TEXT_RE.search(text or ""))


def _raw_args_text(args: Any) -> str:
    if isinstance(args, dict):
        return " ".join(str(v) for v in args.values())
    return str(args or "")


def _workdir_is_profile_home(workdir: str) -> bool:
    """True when workdir looks like a Hermes profile home (for bare-filename relative writes)."""
    wd = _norm(workdir or "").casefold()
    if not wd:
        return False
    # Profile homes end at the profile directory (contain hermes\profiles\<name>)
    if "hermes\\profiles\\" in wd:
        return True
    # Throwaway / HERMES_HOME roots used in tests often end with the home itself
    try:
        from hermes_constants import get_hermes_home

        home = _norm(str(get_hermes_home())).casefold()
        return bool(home) and (wd == home or wd.startswith(home + "\\"))
    except Exception:
        return False


def _file_tool_blocked(tool_name: str, args: dict) -> bool:
    if tool_name not in (TOOL_WRITE_FILE, TOOL_PATCH):
        return False
    path = str(args.get("path") or "")
    if _path_looks_sensitive(path):
        return True
    patch = str(args.get("patch") or "")
    if patch:
        for match in V4A_FILE_HEADER_RE.finditer(patch):
            if _path_looks_sensitive(match.group(1).strip()):
                return True
        if _text_has_sensitive_filename(patch):
            return True
    return False


def _terminal_blocked(args: dict) -> bool:
    cmd = str(args.get("command") or "")
    workdir = str(args.get("workdir") or "")
    if HERMES_CONFIG_CLI_RE.search(cmd):
        return True
    has_verb = bool(WRITE_DELETE_VERB_RE.search(cmd))
    if has_verb and _text_has_sensitive_filename(cmd):
        return True
    # workdir under profile + bare sensitive filename + write/delete verb
    if has_verb and _workdir_is_profile_home(workdir):
        if re.search(r"(?i)(?:^|[\s\"'=])(?:config\.yaml|CONFIG~1\.YAM|\.env)(?:\b|$)", cmd):
            return True
    return False


def evaluate_config_self_edit(tool_name: str, args: Any) -> Optional[Dict[str, str]]:
    """Return a block directive or None to allow."""
    name = str(tool_name or "")
    payload = args if isinstance(args, dict) else {}
    if name == TOOL_READ_FILE:
        return None
    if name in (TOOL_WRITE_FILE, TOOL_PATCH) and _file_tool_blocked(name, payload):
        return {"action": "block", "message": BLOCK_MESSAGE_CONFIG_OR_ENV}
    if name == TOOL_TERMINAL and _terminal_blocked(payload):
        return {"action": "block", "message": BLOCK_MESSAGE_CONFIG_OR_ENV}
    return None


def _normalize_disposition_key(text: str) -> str:
    """Containment key via zola_memory.forget (package or flat import)."""
    # P8-CONNECT: use forget.normalize_disposition_key for containment — P8-D09
    try:
        from hermes_plugins.zola_memory.forget import normalize_disposition_key

        return normalize_disposition_key(text)
    except Exception:
        pass
    try:
        from zola_memory.forget import normalize_disposition_key  # type: ignore

        return normalize_disposition_key(text)
    except Exception:
        pass
    try:
        import forget as forget_mod  # type: ignore

        return forget_mod.normalize_disposition_key(text)
    except Exception:
        # Last-resort local normalize (NFKC + whitespace + casefold)
        import unicodedata

        collapsed = " ".join(unicodedata.normalize("NFKC", text or "").split())
        return collapsed.casefold()


def _fact_text_from_op(op: Dict[str, Any]) -> str:
    """Fact text for add/replace: content or new_text."""
    content = op.get("content")
    if content is None:
        content = op.get("new_text")
    return content if isinstance(content, str) else str(content or "")


def _memory_ops_to_check(args: Any) -> List[Dict[str, Any]]:
    """Return add/replace ops that need containment checks (batch or single)."""
    payload = args if isinstance(args, dict) else {}
    operations = payload.get("operations")
    if operations is not None:
        if not isinstance(operations, list):
            return [{"action": MEMORY_ACTION_ADD, "content": ""}]  # force fail closed
        out: List[Dict[str, Any]] = []
        for op in operations:
            if not isinstance(op, dict):
                out.append({"action": MEMORY_ACTION_ADD, "content": ""})
                continue
            action = str(op.get("action") or "")
            if action in (MEMORY_ACTION_ADD, MEMORY_ACTION_REPLACE):
                out.append(op)
        return out
    action = str(payload.get("action") or "")
    if action in (MEMORY_ACTION_ADD, MEMORY_ACTION_REPLACE):
        return [payload]
    return []


def _session_id_from_kwargs(**kwargs: Any) -> str:
    sid = kwargs.get("session_id")
    if isinstance(sid, str) and sid:
        return sid
    # Fall back to turn record
    try:
        from . import turn_context
    except ImportError:
        import turn_context  # type: ignore

    turn_id = str(kwargs.get("turn_id") or "") or turn_context.current_turn_id_from_context()
    rec = turn_context.get_record(turn_id) if turn_id else None
    if rec is not None and rec.session_id:
        return str(rec.session_id)
    return ""


def _task_id_from_kwargs(**kwargs: Any) -> str:
    """Read task_id from pre_tool_call hook_kwargs (model_tools)."""
    # P8-CONNECT: task_id from hook kwargs; fall back to turn record — P8-D09
    tid = kwargs.get("task_id")
    if isinstance(tid, str) and tid:
        return tid
    try:
        from . import turn_context
    except ImportError:
        import turn_context  # type: ignore

    turn_id = str(kwargs.get("turn_id") or "") or turn_context.current_turn_id_from_context()
    rec = turn_context.get_record(turn_id) if turn_id else None
    if rec is not None and rec.task_id:
        return str(rec.task_id)
    return ""


def _user_message_for_turn(**kwargs: Any) -> Optional[str]:
    try:
        from . import turn_context
    except ImportError:
        import turn_context  # type: ignore

    turn_id = str(kwargs.get("turn_id") or "") or turn_context.current_turn_id_from_context()
    if not turn_id:
        return None
    rec = turn_context.get_record(turn_id)
    if rec is None:
        return None
    return rec.user_message if isinstance(rec.user_message, str) else ""


def _fact_contained(fact: str, user_message: str) -> bool:
    fact_key = _normalize_disposition_key(fact)
    msg_key = _normalize_disposition_key(user_message)
    if not fact_key:
        return False
    return fact_key in msg_key


def evaluate_memory_taint(
    tool_name: str = "",
    args: Any = None,
    **kwargs: Any,
) -> Optional[Dict[str, str]]:
    """Block memory add/replace (and skill_manage) when session/task is Workspace-tainted.

    MUST 2: missing both ids or any taint-path exception → block (fail closed).
    remove / forget / untainted unaffected.
    """
    # P8-CONNECT: ENABLE memory_taint; lineage-aware ids — P8-D09
    if not GUARD_MEMORY_TAINT_ENABLED:
        return None
    name = str(tool_name or "")
    if name not in (TOOL_MEMORY, TOOL_SKILL_MANAGE):
        return None

    # remove / unrelated memory ops — skip id/taint gates
    if name == TOOL_MEMORY:
        ops = _memory_ops_to_check(args)
        if not ops:
            return None
    else:
        ops = []

    try:
        from . import taint
    except ImportError:
        import taint  # type: ignore

    session_id = _session_id_from_kwargs(**kwargs)
    task_id = _task_id_from_kwargs(**kwargs)

    # P8-CONNECT: neither session_id nor task_id → BLOCK for add/replace/skill_manage — P8-D09
    if not session_id and not task_id:
        if name == TOOL_SKILL_MANAGE:
            return {"action": ACTION_BLOCK, "message": BLOCK_MESSAGE_SKILL_MANAGE}
        return {"action": ACTION_BLOCK, "message": BLOCK_MESSAGE_MEMORY_TAINT}

    try:
        tainted = taint.is_tainted_ids(session_id or None, task_id or None)
    except Exception:
        # Caller logs reason=guard_error; fail closed
        raise

    if not tainted:
        return None

    if name == TOOL_SKILL_MANAGE:
        return {"action": ACTION_BLOCK, "message": BLOCK_MESSAGE_SKILL_MANAGE}

    user_message = _user_message_for_turn(**kwargs)
    if user_message is None:
        # P8-CONNECT: missing turn when tainted → block — P8-D09
        return {"action": ACTION_BLOCK, "message": BLOCK_MESSAGE_MEMORY_TAINT}

    # P8-CONNECT: operations[] — block WHOLE batch if any op fails — P8-D09
    for op in ops:
        fact = _fact_text_from_op(op)
        if not _fact_contained(fact, user_message):
            return {"action": ACTION_BLOCK, "message": BLOCK_MESSAGE_MEMORY_TAINT}
    return None


def memory_taint_stub(tool_name: str = "", args: Any = None, **kwargs: Any) -> Optional[Dict[str, str]]:
    """Backward-compatible name — delegates to evaluate_memory_taint when enabled."""
    if not GUARD_MEMORY_TAINT_ENABLED:
        return None
    return evaluate_memory_taint(tool_name=tool_name, args=args, **kwargs)


def terminal_google_stub(tool_name: str = "", args: Any = None, **kwargs: Any) -> None:
    """Track 3 stub — always allow while disabled."""
    # P8-HARDEN: inert until Track 3 — P8-D02
    if not GUARD_TERMINAL_GOOGLE_ENABLED:
        return None
    return None


def pre_tool_call_hook(
    tool_name: str = "",
    args: Any = None,
    **kwargs: Any,
) -> Optional[Dict[str, str]]:
    """Config/.env self-edit guard + memory-taint + inert terminal stub."""
    name = str(tool_name or "")
    # P8-CONNECT: memory-taint exceptions → BLOCK + guard_error (MUST 2) — P8-D09
    try:
        blocked_taint = evaluate_memory_taint(tool_name=name, args=args, **kwargs)
    except Exception:
        if name in (TOOL_MEMORY, TOOL_SKILL_MANAGE):
            try:
                wslog.write_event(
                    wslog.LOG_EVENT_GUARD,
                    name=GUARD_MEMORY_TAINT,
                    action=ACTION_BLOCK,
                    reason=REASON_GUARD_ERROR,
                    tool=name,
                )
            except Exception:
                pass
            msg = (
                BLOCK_MESSAGE_SKILL_MANAGE
                if name == TOOL_SKILL_MANAGE
                else BLOCK_MESSAGE_MEMORY_TAINT
            )
            return {"action": ACTION_BLOCK, "message": msg}
        blocked_taint = None

    try:
        if blocked_taint is not None:
            reason = (
                REASON_SKILL_MANAGE_TAINT
                if name == TOOL_SKILL_MANAGE
                else REASON_MEMORY_TAINT_BLOCK
            )
            try:
                wslog.write_event(
                    wslog.LOG_EVENT_GUARD,
                    name=GUARD_MEMORY_TAINT,
                    action=ACTION_BLOCK,
                    reason=reason,
                    tool=name,
                )
            except Exception:
                pass
            return blocked_taint

        terminal_google_stub(tool_name=name, args=args, **kwargs)

        blocked = evaluate_config_self_edit(name, args)
        if blocked is not None:
            cmd = ""
            if isinstance(args, dict):
                cmd = str(args.get("command") or "")
            reason = (
                REASON_HERMES_CONFIG_CLI
                if name == TOOL_TERMINAL and HERMES_CONFIG_CLI_RE.search(cmd)
                else REASON_CONFIG_OR_ENV_WRITE
            )
            wslog.write_event(
                wslog.LOG_EVENT_GUARD,
                name=GUARD_CONFIG_SELF_EDIT,
                action=ACTION_BLOCK,
                reason=reason,
                tool=name,
            )
            return blocked
    except Exception:
        # P8-HARDEN: on internal error, block if sensitive tool+token else allow — P8-D02
        raw = _raw_args_text(args)
        sensitive = _text_has_sensitive_filename(raw)
        if name in (TOOL_WRITE_FILE, TOOL_PATCH, TOOL_TERMINAL) and sensitive:
            try:
                wslog.write_event(
                    wslog.LOG_EVENT_GUARD,
                    name=GUARD_CONFIG_SELF_EDIT,
                    action=ACTION_BLOCK,
                    reason=REASON_GUARD_ERROR,
                    tool=name,
                )
            except Exception:
                pass
            return {"action": "block", "message": BLOCK_MESSAGE_CONFIG_OR_ENV}
        try:
            wslog.write_event(
                wslog.LOG_EVENT_GUARD,
                name=GUARD_CONFIG_SELF_EDIT,
                action=ACTION_ALLOW,
                reason=REASON_GUARD_ERROR,
                tool=name or "-",
            )
        except Exception:
            pass
        return None
    return None
