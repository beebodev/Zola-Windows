# WINH06 Phase 4 — Self-Directed Identity, Config & Prompt Modification

Hermes pin: `v2026.9.14` / `345cd2b057a452236de401d3534b8502a7465e8d`.
Labels: `[MECHANISM]` / `[RISK]` / `[ABSENT]` / `[UNVERIFIED]`.
Question for this phase: can the **agent itself**, via a tool call, rewrite identity / persisted config / prompt-affecting state — and under what control.

WINH05-AUD-06 / WINH05-AUD-07 (multiple identity strings; no auto-propagation) are cited, not re-derived.

---

## 1. Can the agent edit its own `SOUL.md` through a tool call?

Identity load path (read-only here): `agent/prompt_builder.py` `load_soul_md` L1452–1484 reads `$HERMES_HOME/SOUL.md` (profile home). There is **no** `soul_edit` / `identity` tool. The write path is generic `write_file` / `patch`.

### WINH06-AUD-17 — `[RISK]` — HIGH — `tools/file_tools_write_guards.py` L182–187, L139–140; `tools/file_tools.py` L765–768; `agent/file_safety.py` L77–133

Protected-instruction gate (`_PROTECTED_INSTRUCTION_BASENAMES` includes `soul.md`, L139–140) is **project-local only**. Comment L182–187:

> `~/.hermes` itself is governed by its own guards (config.yaml hard-block, mirror guard, write_approval); this gate targets PROJECT-LOCAL files only.

If `realpath(target)` is under `get_hermes_home()`, `_protected_instruction_reason` returns `None` (L186–187). The always-ask that applies to a repo `SOUL.md` does **not** apply to `$HERMES_HOME/SOUL.md` — which is the file `load_soul_md` actually injects.

`file_safety.py` `build_write_denied_paths` / `_HERMES_PROTECTED_SUBPATHS` (L77–133) lists credentials, `state.db`, `sessions`, `mcp-tokens`, `pairing`. **SOUL.md is not on that list** (searched `file_safety.py` for `SOUL`: no matches).

`write_file` therefore reaches `file_ops.write_file` for `$HERMES_HOME/SOUL.md` without the protected-instruction prompt. Default `security.protected_instruction_files: True` (`config_defaults.py` L1623–1626) does not change this, because the home exemption runs first.

`threat_patterns.py` L86 (`hermes_config_mod`) matches prose about modifying `.hermes/config.yaml` or `SOUL.md` in **strict** scan scope (memory / skill-install scanners), not the file-tool write path.

### WINH06-AUD-18 — `[MECHANISM]` — MEDIUM — `file_tools_write_guards.py` L116–123, L208–213; `_check_protected_instruction_write` L278–288

Two controls that **do** exist:

1. **Project-local `SOUL.md` / `AGENTS.md` / `CLAUDE.md` / `.cursorrules`:** always-ask, not bypassed by `--yolo`, fail-closed with no human channel (`_request_protected_instruction_approval` L208–213).
2. **`$HERMES_HOME/config.yaml`:** hard refuse from `write_file` (`_check_sensitive_path` L116–123): "Agent cannot modify security-sensitive configuration. Edit ~/.hermes/config.yaml directly or use 'hermes config' instead."

Human-only identity/config writers (not agent tools):

- `/personality` → `hermes_cli/personality.py` `persist_personality` L127–145 writes `display.personality` via `atomic_roundtrip_yaml_update` (the "ONLY sanctioned write path" for that key). `tui_gateway/methods_slash.py` `_mirror_personality` L295–300.
- `/model` with persist → `hermes_cli/model_switch.py` `persist_model_selection` L1586–1604 writes `model.*` keys. `tui_gateway/model_switch.py` `_apply_model_switch` L246–248.

Those are operator slash commands. The model does not get a `persist_personality` tool.

---

## 2. Can the agent change persisted config through a tool call?

No `config_set` / `write_config` agent tool was found (searched `tools/*_tool.py`). Direct `write_file` of `config.yaml` is refused (AUD-18).

### WINH06-AUD-21 — `[RISK]` — MEDIUM — `file_tools_write_guards.py` L123; `tools/approval_detection.py` (no `hermes config` patterns)

The refuse message itself points the model at `'hermes config'`. `hermes config set <key> <value>` is the operator CLI that *is* allowed to mutate `config.yaml`. Searched `approval_detection.py` for `hermes config`: **no matches**. A `terminal` call running `hermes config set skills.write_approval false` (or flipping `approvals.mode`, `security.protected_instruction_files`, `plugins.enabled`, `mcp_servers`, …) is not a hardline command.

`[UNVERIFIED]` whether a given Windows-track surface even exposes `terminal` (WINH02 Path C HTTP-only would not). On Path A/B (desktop / `hermes serve` with terminal toolset), this is a live bypass of the `write_file` config hard-block.

Runtime-overridable surface in `config_defaults.py` is large (memory, skills, security, mcp, plugins, model, …). Anything `hermes config set` can write is in play via that terminal fallback. This checkout cannot prove a live TUI would auto-approve that command — only that no dedicated pattern exists.

---

## 3. Draft / review state for self-modification

### WINH06-AUD-19 — `[ABSENT]` — HIGH — searched `write_approval.py`, `file_tools_write_guards.py`, `prompt_builder.py`, `personality.py`

No propose-then-approve draft for:

- `$HERMES_HOME/SOUL.md`
- `agent.system_prompt`
- `display.personality` (slash persists immediately)
- arbitrary `config.yaml` keys via `hermes config set`

Do not infer one from skills `write_approval` or sudo/dangerous-command gates. Those are other subsystems. Skills staging (`/skills pending`) exists only when `skills.write_approval` is on (default off) and only for `skill_manage`. Protected-instruction always-ask is **immediate** approve-or-deny of the write, not a persisted draft. It also does not cover home `SOUL.md` (AUD-17).

---

## 4. Blast radius if the path is abused or malfunctions

### WINH06-AUD-20 — `[RISK]` — HIGH — `load_soul_md` L1452–1484; WINH05-AUD-06 / WINH05-AUD-07

If `write_file` to `$HERMES_HOME/SOUL.md` succeeds without the project-file always-ask:

- The next `load_soul_md` injects the new text as identity slot #1. There is no "previous SOUL" rollback tool analogous to `skill_ledger.rollback_entry`.
- WINH05-AUD-06: other "You are…" strings (`default_soul.py`, `personality.py`, `voice_live.py`, `auxiliary_client.py`, `doctor_state.py`) are **not** updated. The agent can believe it rewrote identity while voice / auxiliary / doctor still speak the old one.
- WINH05-AUD-07: customized SOUL.md is never auto-updated *from* those strings either — a one-file rewrite is the live prompt identity, but the rest of the product diverges.
- No ledger like `skill_ledger` was found for SOUL.md (searched `tools/` for `soul` ledger: none). Audit trail is whatever `write_file` leaves in the transcript, plus filesystem mtime.
- Mid-session: prompt rebuild / next turn picks up the file. `[UNVERIFIED]` whether an already-cached system prompt in the current turn is invalidated immediately; `load_soul_md` is called from prompt assembly, not from `write_file`.

If `hermes config set` is used (AUD-21): worst case is flipping security/approval keys (`approvals.mode`, `skills.write_approval`, `security.protected_instruction_files`, `security.allow_lazy_installs`, enabling a plugin, adding `mcp_servers`) — i.e. disabling the gates this inventory is describing. That is a larger blast radius than a cosmetic persona edit.

`config.yaml` hard-block on `write_file` is the main reason this is not "the agent can silently edit every safety setting through the same tool it uses for notes." The terminal-CLI bypass is the residual.

---

## Cross-references (not re-audited)

- WINH05-AUD-06 — multiple independently-maintained identity strings. Additive here: the agent can rewrite one of them (`SOUL.md`) without touching the others.
- WINH05-AUD-07 — identity change is a multi-file edit; customized SOUL.md never auto-updated. Additive: self-directed SOUL write makes that split worse, not better.
- WINH04 memory DWA / write-authority findings — out of scope; memory writes are not identity-file writes.
