"""pre_tool_call guards — config/.env self-edit (defense in depth, P8-D02)."""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

try:
    from . import log as wslog
except ImportError:  # P8-HARDEN: flat unittest discover — P8-D02
    import log as wslog

# P8-HARDEN: named guard constants — P8-D02
GUARD_CONFIG_SELF_EDIT = "config_self_edit"
GUARD_MEMORY_TAINT = "memory_taint"
GUARD_TERMINAL_GOOGLE = "terminal_google"

# Inert stubs (Track 2 / Track 3) — off until those tracks enable them
GUARD_MEMORY_TAINT_ENABLED = False
GUARD_TERMINAL_GOOGLE_ENABLED = False

ACTION_ALLOW = "allow"
ACTION_BLOCK = "block"

REASON_CONFIG_OR_ENV_WRITE = "config_or_env_write"
REASON_HERMES_CONFIG_CLI = "hermes_config_cli"
REASON_STUB_ALLOW = "stub_inert"
REASON_NOT_APPLICABLE = "not_applicable"
REASON_GUARD_ERROR = "guard_error"

BLOCK_MESSAGE_CONFIG_OR_ENV = (
    "Blocked: editing the live Hermes config.yaml or .env is not allowed."
)

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


def memory_taint_stub(tool_name: str = "", args: Any = None, **kwargs: Any) -> None:
    """Track 2 stub — always allow while disabled."""
    # P8-HARDEN: inert until Track 2 — P8-D02/D09
    if not GUARD_MEMORY_TAINT_ENABLED:
        return None
    return None


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
    """Config/.env self-edit guard + inert stubs. Defense in depth only."""
    name = str(tool_name or "")
    try:
        # Inert stubs first (always allow while disabled)
        memory_taint_stub(tool_name=name, args=args, **kwargs)
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
