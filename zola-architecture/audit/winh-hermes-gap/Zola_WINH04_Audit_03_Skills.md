# WINH04 Audit 03 — Skill Creation, Curation & Storage

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

Sources: `skills/AGENTS.md`, `tools/skills_tool.py`, `tools/skill_manager_tool.py`, `agent/curator.py`, `tools/skill_usage.py`, `agent/skill_commands.py`, `hermes_cli/subcommands/skills.py`, `tools/skills_sync.py`, `tools/write_approval.py`, `tools/skill_ledger.py`.

---

## 1. Full lifecycle

### 1.1 Where a skill comes from

| Origin | How it enters | Key functions |
|---|---|---|
| **Bundled** | Repo `skills/` copied into `$HERMES_HOME/skills/` | `tools/skills_sync.py` — manifest `.bundled_manifest`; new copies; updates only if user copy still matches origin hash; user-deleted not re-added (module docstring L1–6) |
| **Official-optional** | Repo `optional-skills/` **not** active until install | `skills/AGENTS.md` L7–12; `hermes skills install official/<category>/<skill>` via `tools/skills_hub_official.py` `OptionalSkillSource` |
| **Hub / registries** | CLI search/install | `hermes_cli/subcommands/skills.py` `build_skills_parser` L20–24; sources include official, skills-sh, GitHub, ClawHub, NVIDIA, OpenAI, … (`_SOURCE_CHOICES` L15–17) |
| **User-authored** | Files dropped under `$HERMES_HOME/skills/` or project `./.hermes/skills` after `hermes skills trust` | `skills.py` trust/untrust L28–36; `skills_tool.py` `_skill_search_dirs` L170–178 (project dirs first) |
| **Agent-authored** | `skill_manage` `create` | `tools/skill_manager_tool.py` `skill_manage` L742–784; description L788–805: create lands in the **active profile** skills dir |

Slash-command index: `agent/skill_commands.py` `scan_skill_commands` L366 / `get_skill_commands` L419 / `reload_skills` L453. Invocation assembly: `build_skill_invocation_message` L479.

### 1.2 Where it lands

`skill_manager_tool.py` L68: `SKILLS_DIR = HERMES_HOME / "skills"`. Resolver `_skills_dir()` L74–80 retargets when `HERMES_HOME` switches (gateway multi-profile). Bundled sync writes the same directory (`skills_sync.py` L36–37).

Search order for **use** (`skills_tool.py` `_skill_search_dirs` L170–178): trusted project dirs → `$HERMES_HOME/skills` → external dirs. First-wins by name.

### 1.3 What promotes / curates into active use

**Load:** `skills_tool.py` `_find_all_skills` L181+ builds the listing; `skill_view` loads SKILL.md. Disabled names: config `skills.disabled` + `platform_disabled` (`_is_skill_disabled` L149–167). Platform frontmatter can mark unsupported (`skill_view` L545–546).

**Slash commands:** `skill_commands.py` `_scan_skill_md` L329 skips disabled; `build_preloaded_skills_prompt` L579 injects selected skills into the prompt.

**Curator (agent-created only):** `agent/curator.py` docstring L1–7; `skills/AGENTS.md` L61–75.

- Telemetry: `tools/skill_usage.py` → `$HERMES_HOME/skills/.usage.json` (use/view/patch counts, `state` active/stale/archived, `pinned`).
- `apply_automatic_transitions` (`curator.py` L191–218): stale after `get_stale_after_days()` (default 14), archive after `get_archive_after_days()` (default 30). Pinned and cron-referenced skills skipped. **Never deletes** — archive to `.archive/`.
- `created_by: "agent"` marker from `skill_manage` — curator **never infers** from path (`skill_usage.py` L1–5). Bundled/hub skills are off-limits.
- Optional LLM fork (`DEFAULT_CONSOLIDATE = False`, `curator.py` L32) may pin/archive/patch via `skill_manage`.
- Archive helper sets ledger actor `"curator"` (`curator.py` L180–188).

**Human CLI:** `hermes skills` (install, browse, trust, config) and `hermes curator status|run|pause|pin|archive|restore|…` (`skills/AGENTS.md` L66–67).

---

## 2. Can the agent create/modify a skill without human approval?

**Yes, by default.**

`skill_manage` always **attempts** the write-approval gate (`skill_manager_tool.py` L754–760: “skills are too large to review inline, so they always stage regardless of origin”). Implementation: `_apply_skill_write_gate` → `write_approval.evaluate_gate(SKILLS)` (`skill_manager_tool.py` L584–595).

`evaluate_gate` (`write_approval.py` L166–175): if `write_approval_enabled(subsystem)` is false → **`GateDecision(allow=True)` immediately**. Default: `skills.write_approval: False` (`config_defaults.py` L1373–1376). Comment: unset/invalid also means gate **off** (`write_approval.py` L43–51).

When the gate **is** on: skills always **stage** (`evaluate_gate` L174–175); human reviews via `/skills pending|diff|approve|reject`.

**Also ungated by default:**

- `skills.guard_agent_created: False` (`config_defaults.py` L1367) — security scan of agent-written skills is off; a dangerous verdict would be a tool error the agent can retry, not a human gate.
- `skills.inline_shell: False` (L1362) — `!`cmd snippets in SKILL.md are **not** auto-exec at load (fail-closed for that vector).
- Curator LLM fork, if enabled, mutates via the same `skill_manage` path (inherits the same gate setting). Deterministic archive does not need the LLM.

**Factual answer for WINH05/06:** with stock config the agent can `skill_manage create/edit/patch/delete` in-session with **no** human step. Approval is an **opt-in** config bit, not the default.

**Label:** `[RISK]` `WINH04-AUD-09` (MEDIUM) against Zola “fail-closed when uncertain” / Master Plan single-authority for capability acquisition — **not** a WINH06 design; just the default path.

---

## 3. What happens when a skill errors during use

**Load / view (fail-visible, not silent):**

- Read failure → JSON `_fail(...)` (`skills_tool.py` L540–542).
- Wrong platform → `_fail(..., readiness_status=UNSUPPORTED)` L545–546.
- Disabled → `_fail` with enable hint L548–549.
- `_skill_readiness` L565 reports extra readiness metadata on success.

**Disabled is config, not auto:** `_is_skill_disabled` reads `skills.disabled` / platform lists. A runtime exception inside a skill’s procedure (bad script, failed `terminal` command) is **that tool’s error**, returned to the model. Nothing in `skills_tool.py` / `skill_commands.py` **auto-disables** a skill after a failed run.

**Inline shell:** off by default (`inline_shell: False`) — untrusted `!`cmd in SKILL.md does not run at preprocess time.

**Hub installs:** always scanned (`config_defaults.py` L1366); `tier1_advisory` NVIDIA SkillEvaluator is informational, never blocking (L1368–1372).

**Curator:** errors in usage telemetry are DEBUG-logged and **must not** break the tool call (`skill_usage.py` L1–3). That is fail-open for **counters**, not for skill execution.

**No infinite retry loop** dedicated to skills was found: the agent tool-round retries are the generic conversation loop, not a skill supervisor. A broken SKILL.md can be re-invoked every turn if the model keeps calling `skill_view` / slash-command.

**Label:** `[PARTIAL]` `WINH04-AUD-10` (MEDIUM) — view/platform/disabled fail closed **at load**; execution failures are surfaced as tool errors but **not** fail-closed at the skill registry (no disable-on-error).

---

## 4. Skill storage vs fact-memory storage

**Separate backends, confirmed in code (not by folder name alone):**

| Store | Path / type | Writer |
|---|---|---|
| Fact memory (builtin) | `$HERMES_HOME/memories/MEMORY.md`, `USER.md` — markdown via `MemoryStore` / `atomic_write_text` | `memory_tool` |
| Fact memory (holographic) | `$HERMES_HOME/memory_store.db` SQLite | holographic plugin |
| Session transcript | `state.db` | `hermes_state*` |
| Skills | `$HERMES_HOME/skills/<name>/SKILL.md` (+ scripts/refs) | `skill_manage`, `skills_sync`, hub install |
| Skill telemetry | `$HERMES_HOME/skills/.usage.json` | `skill_usage.py` |
| Skill audit | `$HERMES_HOME/skills/.curator_ledger.jsonl` + blobs | `skill_ledger.py` (default on) |

No shared `MemoryStore` class between skills and MEMORY.md. `skill_manage` does not call `memory_tool`. Curator does not write USER.md.

**Label:** `[MATCH]` `WINH04-AUD-08` (LOW).

Skill mutations **do** have an integrity ledger; fact-memory does not (`WINH04-AUD-07`). That contrast is Phase 3, not a skills defect.

---

## 5. Notes for WINH05 / WINH06 (not findings here)

- Agent-authored skills are the closest Hermes analogue to “capability acquisition from experience.” Default ungated create is `WINH04-AUD-09`.
- Curator auto-archive is lifecycle hygiene, not a governance board.
- `created_by: "agent"` vs bundled/hub split is a **hard** curator invariant — useful if Zola later adds an approval plane only around agent-created packages.
