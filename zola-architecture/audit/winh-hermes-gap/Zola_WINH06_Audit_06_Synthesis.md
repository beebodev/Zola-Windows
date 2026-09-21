# WINH06 Phase 6 — Synthesis: Hermes Self-Improvement & Capability Acquisition

Hermes pin: `v2026.9.14` / `345cd2b057a452236de401d3534b8502a7465e8d`.
Exploratory inventory. **No Zola Document of Truth** for this domain. Labels are `[MECHANISM]` / `[RISK]` / `[ABSENT]` / `[UNVERIFIED]`, not MATCH/GAP/PARTIAL.

Source documents: Audit_02 SkillSelfAuthoring, Audit_03 ToolPluginAcquisition, Audit_04 SelfDirectedConfigModification, Audit_05 LearningAdaptation.

---

## Section 1 — Finding Summary Table

| ID | Label | Severity | File | One-line |
|---|---|---|---|---|
| WINH06-AUD-01 | MECHANISM | MEDIUM | `tools/skill_manager_tool.py` L682–688 | Agent `skill_manage` create/edit/patch/delete/write_file/remove_file; no enable/disable action |
| WINH06-AUD-02 | RISK | HIGH | `write_approval.py` L171–175; `config_defaults.py` L1376 | `skills.write_approval` default False; gate fail-open on import (WINH04-AUD-09 confirmed) |
| WINH06-AUD-03 | ABSENT | HIGH | `skill_manager_tool.py` L392–415, L49–63 | No dry-run/staging; `guard_agent_created` default False; write then live |
| WINH06-AUD-04 | MECHANISM | LOW | `tools/skill_ledger.py` L1–8, L246–266 | JSONL mutation ledger with before/after blobs; `session_id` in evidence when dispatch injects it |
| WINH06-AUD-05 | RISK | MEDIUM | `skill_ledger.py` L6–8, L269–288 | Ledger is telemetry not a gate; append failures do not block the write |
| WINH06-AUD-06 | MECHANISM | MEDIUM | `skill_ledger.py` `rollback_entry` L338–402 | CLI `hermes curator rollback <id>`; foreground delete is hard; no transcript cascade |
| WINH06-AUD-07 | MECHANISM | HIGH | `agent/background_review.py` L1–6, L1025–1065 | Post-turn fork can `skill_manage`; default `background_review.enabled: True` |
| WINH06-AUD-08 | RISK | HIGH | `write_approval.py` L174–175 | Same ungated default applies to the review fork |
| WINH06-AUD-09 | MECHANISM | MEDIUM | `tools/setup_mcp_tool.py` L1–32 | Desktop `setup_mcp` is a human consent card, not a silent config write |
| WINH06-AUD-10 | RISK | HIGH | `setup_mcp_tool.py` L29–32; `mcp_config.py` `cmd_mcp_add` | Non-desktop fallback is `terminal` `hermes mcp install/add`; not in hardline patterns |
| WINH06-AUD-11 | MECHANISM | MEDIUM | `hermes_cli/plugins_cmd.py`; `plugins_discovery.py` L173–218 | Plugin install is CLI/TUI; `plugin_guard`; `plugins.enabled` opt-in; capability consent |
| WINH06-AUD-12 | ABSENT | MEDIUM | searched `tools/*_tool.py` | No agent plugin-install tool (directory-drop still needs `plugins.enabled` in config) |
| WINH06-AUD-13 | RISK | HIGH | `plugins.py` `register_tool` L460–502; `plugin_guard.py` L3–4 | New plugins in-process; MCP stdio as same OS user; no extra sandbox for newly added capability |
| WINH06-AUD-14 | ABSENT | MEDIUM | `methods_tools.py` `tools.list` / `plugins.list` | No single inventory of skills + tools + plugins + MCP |
| WINH06-AUD-15 | MECHANISM | MEDIUM | `tools/lazy_deps.py` L324–332; `config_defaults.py` L1640 | Lazy PyPI installs into the venv; `allow_lazy_installs` default True |
| WINH06-AUD-16 | UNVERIFIED | LOW | `methods_slash.py` `_mirror_reload_mcp` L320–322 | Live attach of CLI-installed MCP without `/reload-mcp` not confirmed in this checkout |
| WINH06-AUD-17 | RISK | HIGH | `file_tools_write_guards.py` L182–187 | `$HERMES_HOME/SOUL.md` exempt from protected-instruction always-ask; `write_file` can rewrite it |
| WINH06-AUD-18 | MECHANISM | MEDIUM | `file_tools_write_guards.py` L116–123, L208–213 | Project-local SOUL.md always-ask; `config.yaml` hard-blocked on `write_file` |
| WINH06-AUD-19 | ABSENT | HIGH | searched write_approval / personality / prompt_builder | No draft/review state for identity or config self-modification |
| WINH06-AUD-20 | RISK | HIGH | `prompt_builder.py` `load_soul_md` L1452–1484 | SOUL rewrite has no SOUL ledger; WINH05-AUD-06/07 strings do not follow |
| WINH06-AUD-21 | RISK | MEDIUM | `approval_detection.py` (no `hermes config` patterns) | `hermes config set` via `terminal` bypasses the `write_file` config hard-block |
| WINH06-AUD-22 | ABSENT | LOW | searched agent/tools/cli for train/RLHF | No bundled fine-tune/RLHF/weight loop; optional TRL skill is user documentation |
| WINH06-AUD-23 | MECHANISM | MEDIUM | `agent/background_review.py` | Only non-memory adaptation loop: post-turn skill/memory fork |
| WINH06-AUD-24 | ABSENT | MEDIUM | `agent/curator.py` (WINH04); no outcome scorer | No performance self-eval / A/B / prompt-optimization loop |
| WINH06-AUD-25 | MECHANISM | LOW | `tui_gateway/model_switch.py` L203–254; `model_tools.py` L212–221 | `/model` is a human slash; toolsets do not change with model id |

**Counts:** 25 findings — **9 HIGH**, **12 MEDIUM**, **4 LOW**.

HIGH: AUD-02, 03, 07, 08, 10, 13, 17, 19, 20. MEDIUM: AUD-01, 05, 06, 09, 11, 12, 14, 15, 18, 21, 23, 24. LOW: AUD-04, 16, 22, 25.

---

## Section 2 — What Hermes covers as-is

**Skill authoring.** The agent can create, rewrite, patch, and delete skills and their support files through `skill_manage` (AUD-01). Newly written skills become live after a syntax/frontmatter check and a prompt-cache clear; there is no dry-run (AUD-03). A JSONL ledger records mutations (AUD-04) and CLI rollback can restore blobs (AUD-06), but the ledger is not a gate (AUD-05). Default config does not require human approval (AUD-02). A background-review fork, on by default, can author skills after a turn without the user asking (AUD-07/08). Hub install (`hermes skills install`) is a separate human/CLI path with quarantine; it is not the `skill_manage` create path. Skill **enable/disable** is `skills.disabled` in config, not a `skill_manage` action.

**Plugin / tool / MCP registration.** Desktop MCP add is a consent card (`setup_mcp`, AUD-09). Plugins install through human CLI/TUI, with `plugin_guard`, catalog kill-list, `plugins.enabled` opt-in, and capability consent for declared overrides (AUD-11). There is no agent plugin-install tool (AUD-12). Residual: the agent is told to run `hermes mcp install` / can run `hermes plugins install` / `hermes config set` via `terminal` (AUD-10, AUD-21). Newly registered plugins run in-process; MCP children run as the same user (AUD-13). Lazy PyPI installs can add native code to the venv with `allow_lazy_installs` default True (AUD-15). No unified "what is this agent allowed to do right now" listing (AUD-14). Live MCP attach after CLI install without `/reload-mcp` is unverified (AUD-16).

**Self-directed identity / config.** `$HERMES_HOME/SOUL.md` — the file the prompt actually loads — is writable via `write_file` because the protected-instruction always-ask exempts HERMES_HOME (AUD-17). Project-local `SOUL.md` *is* always-ask; `config.yaml` is hard-blocked on `write_file` (AUD-18). No draft/review for identity or config (AUD-19). `/personality` and `/model --global` persist through sanctioned YAML updaters, as human slash commands, not agent tools (AUD-18, AUD-25). `hermes config set` via terminal is the bypass around the hard-block (AUD-21). Blast radius of a home-SOUL rewrite is a silent identity change with no SOUL ledger and no propagation to the other identity strings WINH05 already flagged (AUD-20).

**Learning / adaptation beyond memory.** No bundled fine-tune, RLHF, or weight-update runtime (AUD-22) — that whole category is absent, which is a factual inventory result, not a Zola miss. The only non-memory future-behavior loop is background review writing skills/memory (AUD-23). No outcome-scored self-eval or A/B (AUD-24). `/model` does not install tools; toolsets are independent of model id (AUD-25).

---

## Section 3 — Authority & audit posture, in one place

Rows are every `[MECHANISM]` from Phases 2–5. Gate / log / reversible as actually implemented at this pin.

| ID | Mechanism | Gate (default) | Logged | Reversible |
|---|---|---|---|---|
| AUD-01 | `skill_manage` mutations | `skills.write_approval` **off**; fail-open if import fails | Yes — `skill_ledger` JSONL (not a gate) | Yes via CLI `rollback_entry`; foreground delete is hard |
| AUD-04 | Skill ledger itself | `skills.ledger` **on**; never blocks writes | It *is* the log | Rollback fail-closed if blobs missing |
| AUD-06 | Ledger/curator rollback | Human CLI only | Rollback writes its own ledger entries | Safety entry makes the rollback undoable |
| AUD-07 / AUD-23 | Background-review skill/memory writes | Same skills/memory `write_approval` (**off**); tool whitelist only | Ledger + memory files; origin tagged `curator`/`background_review` | Same as skill/memory rollback; no "undo this review pass" button |
| AUD-09 | Desktop `setup_mcp` | Human consent card | Desktop/REST flow; MCP config stanza preserved if later disabled as suspicious | `hermes mcp remove`; `/reload-mcp` |
| AUD-11 | Plugin install CLI/TUI | Human command + `plugin_guard` + kill list + `plugins.enabled` + capability consent | Install metadata / catalog sidecar | `hermes plugins` uninstall/disable (CLI); not an agent tool |
| AUD-15 | Lazy PyPI install | `security.allow_lazy_installs` **True** | pip/venv side effects; no Hermes capability ledger | Uninstall packages by hand; no agent rollback |
| AUD-18 | Project SOUL.md always-ask; `config.yaml` `write_file` refuse | Always-ask (project); hard-block (`config.yaml`) | Transcript of the tool error / approval | N/A for refused writes |
| AUD-25 | `/model` switch | Human slash; optional expensive-model confirm | Session marker `display_kind: model_switch`; persist-global writes `model.*` | Switch back with another `/model`; session vs global scope |

Related `[RISK]` rows that are **not** mechanisms but describe missing gates on the rows above: AUD-02, 05, 08, 10, 13, 17, 20, 21.

---

## Section 4 — Candidate scratch-build list

Not "must build to match a Zola requirement." Candidates a future policy document for this domain would need to **decide on**:

1. **Default-on approval for agent skill writes** — flip `skills.write_approval` (and decide whether background review is allowed to stage vs forbidden). Addresses AUD-02, AUD-08.
2. **Test-or-quarantine before a self-authored skill is indexed** — staging dir, dry-run, or hub-style quarantine for `skill_manage` create. Addresses AUD-03.
3. **Treat ledger failures as fail-closed *or* alert** — today swallow. Addresses AUD-05.
4. **Agent-tool rollback** vs CLI-only. Addresses AUD-06 usability, not existence.
5. **Kill or tightly bound background-review skill writes** on the Windows track. Addresses AUD-07/08/23.
6. **Do not instruct the model to `hermes mcp install` via terminal** on non-desktop surfaces; fail closed instead of falling back. Same for `hermes plugins install` and `hermes config set`. Addresses AUD-10, AUD-12 residual, AUD-21.
7. **Sandbox or reduced privilege for newly added MCP/plugins** (or refuse third-party MCP on Windows until reviewed). Addresses AUD-13.
8. **Single capability inventory API** for the Windows client (skills + toolsets + plugins + MCP). Addresses AUD-14.
9. **Default `allow_lazy_installs: false`** on Windows. Addresses AUD-15.
10. **Close the HERMES_HOME SOUL.md exemption** (always-ask or hard-block, plus a SOUL ledger). Addresses AUD-17, AUD-19, AUD-20.
11. **Draft/review for identity and security-relevant config**, not only skills. Addresses AUD-19.
12. **Explicit non-goal: no on-box training loop** — document AUD-22 as accepted absence so WINH00 does not invent a Zola training requirement by accident.
13. **Unified reload policy** after MCP/plugin install (AUD-16).

---

## Section 5 — Open questions for WINH00

Do not resolve these here.

1. **Should Zola-Windows write an architecture document for this domain** (mirroring Memory Hierarchy / Identity & Personality) before WINH00? This audit had nothing to score against. Without that document, WINH00 cannot convert Section 4 into "scratch-build vs inherit."

2. **Of the `[RISK]` findings in Section 3's companion list, which should block adopting Hermes's default config as-is for the Windows track**, versus which are acceptable because a human operator is assumed present?
   - Strongest default-config problems if the Windows client exposes `skill_manage` + `terminal` + `write_file`: AUD-02/08 (ungated skill writes, including the review fork), AUD-10/21 (CLI fallbacks), AUD-17 (home SOUL.md).
   - More acceptable if a human is always on the desktop card and terminal is disabled: AUD-09 then covers MCP; AUD-11 covers plugins; AUD-02 still matters because background review does not need the user to type `skill_manage`.

3. **One policy vs surface-dependent gating (WINH02/03 Path A/B/C/D)?**
   - Path A (fork `apps/desktop`): inherits `setup_mcp` cards, `plugins.manage` RPC, slash `/model` `/personality`, and whatever toolsets the fork leaves enabled.
   - Path B (`hermes serve` / JSON-RPC): same gateway gates **if** the Windows client implements the consent/approval methods; otherwise timeouts skip/deny per WINH03-AUD-12.
   - Path C (HTTP API only): no desktop card, no slash commands; agent tool surface is whatever the API session enables — `setup_mcp` will tell the model to use `terminal` (AUD-10) if terminal exists.
   - Path D (ACP): file/terminal shims; `file_safety.py` already notes it is not a security boundary.
   - Question: one Windows policy ("no self-authored live skills, no config CLI, always-ask SOUL") applied in the client, or per-path?

4. **Cross-reference WINH04-AUD-09 / -10 and WINH05-AUD-06 / -07: additive or severity-changing?**
   - WINH04-AUD-09: **confirmed, not re-raised as a new WINH04 finding**. WINH06-AUD-02 is the same default, restated because this phase's question is capability acquisition rather than memory safety. WINH04 recorded it as MEDIUM; WINH06 scores HIGH (ungated live skills plus the default-on review fork). WINH00 should pick one severity for the Windows default. Scratch-build framing in WINH04 (gate skill writes) is **reinforced**, not replaced.
   - WINH04-AUD-10: **unchanged**. WINH06-AUD-03 (no pre-live test) is additive: a broken skill not only fails visible (AUD-10), it went live without any test.
   - WINH05-AUD-06 / -07: **not re-derived**. WINH06-AUD-17/20 are additive: the agent can **itself** rewrite one identity file, which makes the multi-string split (AUD-06) and non-propagation (AUD-07) operationally worse. They do not change those findings' labels; they add a write-authority problem WINH05 did not ask.

Await developer review before a build plan. Phase 7 closeout (commit) does not start until the developer says "proceed to closeout."
