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

# P8-READ: terminal Google guard and self-mod rows are live — P8-D02
GUARD_MEMORY_TAINT_ENABLED = True
GUARD_TERMINAL_GOOGLE_ENABLED = True
GUARD_SELF_MOD = "self_mod"

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

# P8-CONNECT-FIX: exact words after the save phrase; one leading label ignored — P8-D09
BLOCK_MESSAGE_MEMORY_TAINT = (
    'Not saved: in this conversation, the memory must be Brian\'s exact words that come after "Remember" (or "Save", "Note that") in his current message, with nothing added. Save those words, or ask him to state the fact.'
)

# P8-READ: digits are allowed after the label's first letter; the stored text keeps the label — P8-D09
_LEADING_LABEL_RE = re.compile(r"^\[[A-Za-z][A-Za-z0-9 _-]{0,30}\]\s*")

# P8-CONNECT-FIX: tainted save must start with a save request — P8-D09
BLOCK_MESSAGE_MEMORY_SAVE_REQUEST = (
    'Not saved: in this conversation, a memory needs Brian to ask for it at the start '
    'of his message, in his own words, like "Remember the test is at 3 PM." '
    "Ask him to say it that way."
)

# Longest first so "note that" wins over "note" at the same token.
SAVE_INTENT_PHRASES = (
    "do not forget",
    "don't forget",
    "keep in mind",
    "make a note",
    "note that",
    "remember",
    "save",
    "note",
)

SAVE_LEAD_IN_WORDS = frozenset(
    {
        "zola",
        "hey",
        "ok",
        "okay",
        "please",
        "so",
        "and",
        "also",
        "alright",
        "oh",
    }
)

BLOCK_MESSAGE_SKILL_MANAGE = (
    "Blocked: skill_manage is not allowed in a Workspace-tainted conversation."
)

BLOCK_MESSAGE_TERMINAL_GOOGLE = (
    "Blocked: that command is not allowed to reach Google or the Workspace store."
)

BLOCK_MESSAGE_SELF_MOD = (
    "Blocked: changing the Workspace plugin or its store is not allowed."
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

# P8-READ: host suffix, not a substring of a lookalike domain — P8-D02
GOOGLE_HOST_RE = re.compile(
    r"(?i)(?:^|[^A-Za-z0-9.-])"
    r"(?:(?:[A-Za-z0-9-]+\.)*googleapis\.com|accounts\.google\.com)"
    r"(?![A-Za-z0-9.-])"
)
STORE_PATH_RE = re.compile(
    r"(?i)(?:"
    r"%localappdata%[/\\]hermes[/\\]profiles[/\\]zola[/\\]zola_workspace"
    r"|%hermes_home%[/\\]zola_workspace"
    r"|[/\\]hermes[/\\]profiles[/\\]zola[/\\]zola_workspace"
    r")"
)
STORE_FILE_RE = re.compile(
    r"(?i)(?<![A-Za-z0-9_])(?:token\.dpapi|taint\.sqlite|token~1\.dpa|taint~1\.sql)(?![A-Za-z0-9_])"
)
SETUP_MODULE_RE = re.compile(r"(?i)(?<![A-Za-z0-9_])zola_workspace\.setup(?![A-Za-z0-9_])")
PLUGIN_TREE_RE = re.compile(
    r"(?i)plugins[/\\]zola_(?:workspace|memory|tools)\b"
)
# P8-READ: SOUL.md in the live profile or zola-architecture\identity — P8-D02
SOUL_RE = re.compile(r"(?i)(?<![A-Za-z0-9_])soul\.md(?![A-Za-z0-9_])")
IDENTITY_RE = re.compile(r"(?i)zola-architecture[/\\]identity\b")

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


def _normalize_apostrophes(text: str) -> str:
    """Fold U+2019 / U+2018 via zola_memory.forget (package or flat import)."""
    # P8-CONNECT-FIX: curly and straight apostrophes compare equal — P8-D09
    raw = text if isinstance(text, str) else ""
    try:
        from hermes_plugins.zola_memory.forget import normalize_apostrophes

        return normalize_apostrophes(raw)
    except Exception:
        pass
    try:
        from zola_memory.forget import normalize_apostrophes  # type: ignore

        return normalize_apostrophes(raw)
    except Exception:
        pass
    try:
        import forget as forget_mod  # type: ignore

        return forget_mod.normalize_apostrophes(raw)
    except Exception:
        return raw.replace("\u2019", "'").replace("\u2018", "'")


def _compare_key(text: str) -> str:
    """Disposition key, then apostrophe fold. Used by containment and the save-request parse."""
    # P8-CONNECT-FIX: both normalizers on fact and message — P8-D09
    return _normalize_apostrophes(_normalize_disposition_key(text))


def _save_token_spans(compare_key: str) -> List[tuple]:
    """Tokens of letters, digits, and U+0027, with spans into compare_key."""
    spans: List[tuple] = []
    i = 0
    n = len(compare_key)
    while i < n:
        ch = compare_key[i]
        if ch.isalnum() or ch == "'":
            j = i + 1
            while j < n and (compare_key[j].isalnum() or compare_key[j] == "'"):
                j += 1
            spans.append((compare_key[i:j], i, j))
            i = j
        else:
            i += 1
    return spans


def _save_request_suffix(user_message: str) -> Optional[str]:
    """Compare-key text after the first intent phrase.

    None when no phrase appears, or a token before it is not a lead-in.
    """
    # P8-CONNECT-FIX: save request must lead the message — P8-D09
    key = _compare_key(user_message)
    spans = _save_token_spans(key)
    tokens = [span[0] for span in spans]
    phrase_tokens = [tuple(phrase.split(" ")) for phrase in SAVE_INTENT_PHRASES]
    found: Optional[tuple] = None
    for i in range(len(tokens)):
        for phrase in phrase_tokens:
            n = len(phrase)
            if tuple(tokens[i : i + n]) == phrase:
                found = (i, spans[i + n - 1][2])
                break
        if found is not None:
            break
    if found is None:
        return None
    start_index, end_offset = found
    for token, _start, _end in spans[:start_index]:
        if token not in SAVE_LEAD_IN_WORDS:
            return None
    return key[end_offset:]


def _strip_one_leading_label(fact: str) -> str:
    """Drop one leading [label] before the compare key. The saved text is unchanged."""
    # P8-CONNECT-FIX: containment ignores one bracketed label — P8-D09
    return _LEADING_LABEL_RE.sub("", fact or "", count=1)


def _fact_compare_key(fact: str) -> str:
    return _compare_key(_strip_one_leading_label(fact))


def _fact_contained(fact: str, user_message: str) -> bool:
    fact_key = _fact_compare_key(fact)
    msg_key = _compare_key(user_message)
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

    # P8-CONNECT-FIX: phrase and lead-ins, then exact words after the phrase — P8-D09
    try:
        suffix = _save_request_suffix(user_message)
    except Exception:
        return {"action": ACTION_BLOCK, "message": BLOCK_MESSAGE_MEMORY_TAINT}
    if suffix is None:
        return {"action": ACTION_BLOCK, "message": BLOCK_MESSAGE_MEMORY_SAVE_REQUEST}

    # P8-CONNECT: operations[] — block WHOLE batch if any op fails — P8-D09
    for op in ops:
        fact = _fact_text_from_op(op)
        fact_key = _fact_compare_key(fact)
        if not fact_key or fact_key not in suffix:
            return {"action": ACTION_BLOCK, "message": BLOCK_MESSAGE_MEMORY_TAINT}
    return None


def memory_taint_stub(tool_name: str = "", args: Any = None, **kwargs: Any) -> Optional[Dict[str, str]]:
    """Backward-compatible name — delegates to evaluate_memory_taint when enabled."""
    if not GUARD_MEMORY_TAINT_ENABLED:
        return None
    return evaluate_memory_taint(tool_name=tool_name, args=args, **kwargs)


def _command_text(tool_name: str, args: Any) -> str:
    payload = args if isinstance(args, dict) else {}
    if tool_name == TOOL_TERMINAL:
        return str(payload.get("command") or "")
    parts = [str(payload.get("path") or ""), str(payload.get("patch") or "")]
    return "\n".join(parts)


def terminal_google_hit(command: str) -> bool:
    text = command or ""
    return bool(
        GOOGLE_HOST_RE.search(text)
        or STORE_PATH_RE.search(text)
        or STORE_FILE_RE.search(text)
        or SETUP_MODULE_RE.search(text)
    )


def self_mod_hit(text: str) -> bool:
    raw = text or ""
    return bool(
        PLUGIN_TREE_RE.search(raw)
        or STORE_PATH_RE.search(raw)
        or STORE_FILE_RE.search(raw)
        or SOUL_RE.search(raw)
        or IDENTITY_RE.search(raw)
    )


def evaluate_terminal_google(tool_name: str = "", args: Any = None, **kwargs: Any) -> Optional[Dict[str, str]]:
    """Block terminal commands that name Google or the Workspace store."""
    # P8-READ: terminal Google guard live — P8-D02
    if not GUARD_TERMINAL_GOOGLE_ENABLED:
        return None
    if str(tool_name or "") != TOOL_TERMINAL:
        return None
    if terminal_google_hit(_command_text(TOOL_TERMINAL, args)):
        return {"action": ACTION_BLOCK, "message": BLOCK_MESSAGE_TERMINAL_GOOGLE}
    return None


def evaluate_self_mod(tool_name: str = "", args: Any = None, **kwargs: Any) -> Optional[Dict[str, str]]:
    """Block writes and commands that name the plugin tree or the store."""
    # P8-READ: self-modification rows — P8-D02
    name = str(tool_name or "")
    if name not in (TOOL_WRITE_FILE, TOOL_PATCH, TOOL_TERMINAL):
        return None
    if self_mod_hit(_command_text(name, args)):
        return {"action": ACTION_BLOCK, "message": BLOCK_MESSAGE_SELF_MOD}
    return None


def terminal_google_stub(tool_name: str = "", args: Any = None, **kwargs: Any) -> Optional[Dict[str, str]]:
    """Delegates to evaluate_terminal_google."""
    return evaluate_terminal_google(tool_name=tool_name, args=args, **kwargs)


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

        terminal = evaluate_terminal_google(tool_name=name, args=args, **kwargs)
        if terminal is not None:
            try:
                wslog.write_event(
                    wslog.LOG_EVENT_GUARD,
                    name=GUARD_TERMINAL_GOOGLE,
                    action=ACTION_BLOCK,
                    reason="terminal_google",
                    tool=name,
                )
            except Exception:
                pass
            return terminal

        self_mod = evaluate_self_mod(tool_name=name, args=args)
        if self_mod is not None:
            try:
                wslog.write_event(
                    wslog.LOG_EVENT_GUARD,
                    name=GUARD_SELF_MOD,
                    action=ACTION_BLOCK,
                    reason="self_mod",
                    tool=name,
                )
            except Exception:
                pass
            return self_mod

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
        if name == TOOL_TERMINAL and terminal_google_hit(raw):
            return {"action": ACTION_BLOCK, "message": BLOCK_MESSAGE_TERMINAL_GOOGLE}
        if name in (TOOL_WRITE_FILE, TOOL_PATCH, TOOL_TERMINAL) and self_mod_hit(raw):
            return {"action": ACTION_BLOCK, "message": BLOCK_MESSAGE_SELF_MOD}
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
