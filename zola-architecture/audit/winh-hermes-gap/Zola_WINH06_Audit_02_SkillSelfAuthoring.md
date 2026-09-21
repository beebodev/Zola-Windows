# WINH06 Phase 2 — Skill Self-Authoring & Approval Gates

Hermes pin: `v2026.9.14` / `345cd2b057a452236de401d3534b8502a7465e8d`.
Labels (this phase only): `[MECHANISM]` / `[RISK]` / `[ABSENT]` / `[UNVERIFIED]`.
This is an inventory, not a gap-audit against a Zola Document of Truth.

Curator staleness/archival mechanics are already findings of record in WINH04. They are cited by ID only.

---

## 1. What the agent can create or change about its own skill set, unassisted

### WINH06-AUD-01 — `[MECHANISM]` — MEDIUM — `tools/skill_manager_tool.py`

The agent-facing mutation surface is `skill_manage`. `_ACTION_HANDLERS` (L682–688) enumerates six actions:

| Action | Handler | What it does |
|---|---|---|
| `create` | `_create_skill` L392–415 | Writes a new `SKILL.md` under the profile skills dir (`_resolve_skill_dir`) |
| `edit` | `_edit_skill` L418–429 | Full rewrite of an existing `SKILL.md` (legacy alias; still accepted, not advertised) |
| `patch` | `_act_patch` | Targeted find-and-replace in `SKILL.md` or a supporting file |
| `delete` | `_delete_skill` | Foreground: hard-delete. Background-review/curator consolidation: recoverable archive (L728–736) |
| `write_file` | `_write_file` | Supporting files under `references/` / `templates/` / `scripts/` / `assets/` (`ALLOWED_SUBDIRS` L88) |
| `remove_file` | `_remove_file` | Deletes a supporting file |

There is **no** `enable` / `disable` action on `skill_manage`. Disabling is a config-file concern: installed skills are enabled unless listed in `skills.disabled` (`tui_gateway/methods_profiles.py` L412). That key lives in `config.yaml`, which `write_file` hard-blocks (Phase 4, WINH06-AUD-18).

Advertised call shape is an `operations` array (`SKILL_MANAGE_SCHEMA` L815–892). The flat `action=` shape is still accepted for staged-write replay.

Unassisted paths that can mutate skills without a human typing a CLI command:

1. Foreground tool call: `skill_manage` from the live turn (`toolsets.py` lists it with `skills_list` / `skill_view`).
2. Background review fork: after a turn, `agent/background_review.py` may spawn a daemon that is dispatch-whitelisted for `skill_manage` (WINH06-AUD-07).
3. Hub / CLI install is a **human** surface (`hermes skills install`, `/skills install` in `hermes_cli/skills_hub.py`). The agent can still invoke that CLI through `terminal` — there is no `hermes skills` / `hermes config` pattern in `tools/approval_detection.py` `detect_hardline_command` (searched; no matches). That fallback is the same class of control as WINH06-AUD-10.

### WINH06-AUD-02 — `[RISK]` — HIGH — `tools/write_approval.py` L166–175; `hermes_cli/config_defaults.py` L1373–1376

**WINH04-AUD-09 still holds at this pin.** `evaluate_gate` returns `GateDecision(allow=True)` whenever `write_approval_enabled(subsystem)` is false (L171–172). Default config is `"skills": { "write_approval": False }` (`config_defaults.py` L1376). When the gate *is* on, skills always stage (`subsystem == SKILLS` L174–175) rather than prompting inline.

The gate is also fail-open on import failure: `_run_write_gate` (`skill_manager_tool.py` L581–588) `except Exception: return None  # fail open`.

Confirmed at this pin, not re-derived: same `evaluate_gate` L171–175 and `skills.write_approval: False` L1376 cited by WINH04-AUD-09.

---

## 2. Is a newly self-authored skill tested or validated before it goes live?

### WINH06-AUD-03 — `[ABSENT]` — HIGH — `tools/skill_manager_tool.py` `_create_skill` L392–415; `_security_scan_skill` L49–63; `config_defaults.py` L1364–1367

What *does* run before the file is treated as a live skill:

- `_validate_name` / `_validate_category` / `_validate_frontmatter` / `_validate_content_size` (L393–394). Frontmatter check is YAML parse + required `name`/`description` + non-empty body (L130–163). That is a **syntax/shape check**, not a dry-run of the skill body.
- `_create_skill` then `atomic_write_text` to `SKILL.md` (L401) and optionally `_security_scan_skill` (L402–404). If the scan returns an error, the new directory is `rmtree`'d. The scan is a no-op unless `skills.guard_agent_created` is on (`_guard_agent_created_enabled` L40–44, default `False` at `config_defaults.py` L1367). Comment at L41: "terminal() runs the same code ungated."
- `_record_success` (L702–718) then `clear_skills_system_prompt_cache(clear_snapshot=True)`. The next prompt rebuild sees the new `SKILL.md` via `_build_skills_manifest` (`agent/prompt_builder.py` L1092+). `skills_tool.py` discovery cache TTL is 30s (`_SKILLS_CACHE_TTL_SECONDS` L38) but the prompt cache is explicitly cleared.

What was **not** found (searched: `skill_manager_tool.py`, `skills_tool.py`, `skills_guard.py`, `skills_hub_install.py`):

- No staging directory that stays out of the live index until approval (unless `skills.write_approval` is flipped on — default off).
- No dry-run, sandbox execution of `scripts/`, or invocation test.
- No "pending skill" state distinct from "file exists on disk."

Hub installs (`tools/skills_hub_install.py` `install_from_quarantine`) do use a quarantine path before promoting into `skills/`. That is the **CLI/hub** install path, not `skill_manage` create. Agent-authored skills skip it.

Live-on-write is the default: write the file, clear the cache, it is in the skill index.

---

## 3. Is there an audit trail of self-authored changes?

### WINH06-AUD-04 — `[MECHANISM]` — LOW — `tools/skill_ledger.py`

`skill_ledger.py` L1–8 is explicit: this is a **per-mutation audit ledger**, JSONL at `~/.hermes/skills/.curator_ledger.jsonl`, content-addressed blobs under `~/.hermes/.curator_backups/blobs/`. It is **not** the skill file's own content. Default on: `skills.ledger: True` (`config_defaults.py` L1377–1381).

Each `append_entry` (L246–266) records `id`, UTC `ts`, `actor` (`curator` / `agent` / `user`), `action`, `skill`, `evidence`, `before`, `after`. `derive_actor` (L54–63) tags background-review as `curator`, else `agent`. `_record_success` (skill_manager_tool.py L712–715) puts `session_id` into `evidence` when the executor injected it.

Session/turn injection **does** exist at this pin: `agent/tool_executor.py` L1541 passes `session_id=agent.session_id or ""` into `model_tools.handle_function_call`, and the `skill_manage` handler reads `kw.get("session_id")` (skill_manager_tool.py L901–902). Ledger rows can therefore name the session, distinct from SKILL.md body.

### WINH06-AUD-05 — `[RISK]` — MEDIUM — `tools/skill_ledger.py` L6–8, L264–266, L269–288

The module docstring: "TELEMETRY, NOT A GATE: every public write path swallows and logs — except `rollback_entry`." `record_mutation` L286–288: failures log a warning and leave the mutation in place. `append_entry` L264–266: write failure returns `None`, mutation unaffected. An operator cannot treat the ledger as an authoritative "this change was recorded" guarantee.

There is no turn-id field in the ledger schema (`append_entry` L254–258). Turn correlation would have to be inferred from `ts` + `evidence.session_id` against `state.db` transcripts. `[UNVERIFIED]` whether every gateway/CLI surface always has a non-empty `agent.session_id` at dispatch — searched `tool_executor.py` L1541; empty string is the fallback.

---

## 4. Can a self-authored skill be rolled back?

### WINH06-AUD-06 — `[MECHANISM]` — MEDIUM — `tools/skill_ledger.py` `rollback_entry` L338–402; `hermes_cli/curator.py` L408–409

Actual revert mechanisms:

1. **Ledger rollback (file restore):** `rollback_entry` restores the `before` blobs, deletes files the mutation created, fail-closed if a blob is missing or the pre-rollback safety capture fails (L361–379). Operator command: `hermes curator rollback <id>` (`hermes_cli/curator.py` L408). This is **not** exposed as an agent tool.
2. **Whole-tree curator snapshot:** `curator.backup.enabled: True` (`config_defaults.py` L1404–1408) snapshots `~/.hermes/skills/` before curator passes. Separate from per-mutation ledger rollback.
3. **Foreground `delete`:** hard-delete (`skill_manager_tool.py` L728–736: "Foreground, user-directed deletes keep their existing hard-delete semantics"; `forget(name)` drops usage telemetry). Background-review consolidation archives instead.
4. **Hub uninstall:** lock-file-backed `uninstall_skill` in `skills_hub_install.py` — hub-installed skills only.

Cascade: rollback/delete restores or removes files under `HERMES_HOME/skills/`. `_validate_entry_paths` refuses paths outside `HERMES_HOME` (L326–334). Searched: no write-back into `state.db` transcripts, no rewrite of other skills that merely mention the name in prose. Usage telemetry (`tools/skill_usage.py`) is updated (`forget` / `bump_patch` / `record_created`) but that is not a transcript cascade.

If `skills.ledger` is False, per-mutation rollback has nothing to replay. Curator tar snapshots may still exist if backup is on.

---

## 5. Background review as unattended skill authoring

### WINH06-AUD-07 — `[MECHANISM]` — HIGH — `agent/background_review.py` L1–6, L1025–1065; `config_defaults.py` L748

After every turn, `AIAgent.run_conversation` may spawn a daemon fork whose prompt asks whether a skill should be saved or updated (module docstring L1–6). Default: `auxiliary.background_review.enabled: True` (`config_defaults.py` L748). Dispatch whitelist (`_review_tool_whitelist` L1025–1065) includes the `skills` toolset (`skill_manage`) plus `read_file` / `search_files`. Writes go "straight to the memory + skill stores" (L3–4).

This is self-directed skill acquisition without a human in that turn, distinct from the curator lifecycle already audited in WINH04.

### WINH06-AUD-08 — `[RISK]` — HIGH — `tools/write_approval.py` L174–175; `config_defaults.py` L1376

The same `skills.write_approval: False` default applies to the fork. When the gate is on, `current_origin() == "background_review"` also stages (L174). Default off means the fork's `skill_manage` commits immediately, same as the foreground agent. Combined with WINH06-AUD-03 (no dry-run) and WINH06-AUD-02 (ungated), a single user turn can produce a live skill the human never saw.

---

## Cross-references (not re-audited)

- WINH04-AUD-09 — `skill_manage` ungated by default. Confirmed still true (WINH06-AUD-02).
- WINH04-AUD-10 — skill load failures fail-visible; no auto-disable. Not re-audited; relevant to "broken self-authored skill stays invocable."
- Skill curator lifecycle — WINH04 Phase 3. Archival/restore is a rollback cousin, not re-described here.
