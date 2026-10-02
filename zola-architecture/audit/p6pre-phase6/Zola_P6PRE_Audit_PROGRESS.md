# P6PRE Audit — Progress

**Prompt:** `C:\Users\test\Dev\zola-spikes\prompts\P6PRE_Audit_Prompt_v1.1.md`  
**Prompt SHA-256:** `FCD123964D5F8406039C61A8324CCCE041EBD344A452D2235604ABD2C675965F`  
**Prompt bytes:** 34818  
**Developer SHA verification:** **confirmed** 2026-10-02 (matches developer copy)

**Audit start:** 2026-10-02  
**Work branch:** `p6pre-audit`  
**SOP:** v2.2 Stage 1 · **Template:** v2.1 · **Prompt:** v1.1

---

## Repositories

| Repo | Path | Branch / state | HEAD | Clean? |
|------|------|----------------|------|--------|
| zola-windows | `C:\Users\test\Dev\zola-windows` | `p6pre-audit` (from `main`) | `870b1706bb4b22fd7d4a7fda25780987e35f2bd7` | yes (at branch create) |
| hermes-agent | `C:\Users\test\Dev\hermes-agent` | detached `v2026.9.14` | `345cd2b057a452236de401d3534b8502a7465e8d` | yes (`git status --porcelain` empty) |

`git describe` (hermes-agent): `v2026.9.14`

---

## Folders

| Role | Path |
|------|------|
| Output | `zola-architecture/audit/p6pre-phase6/` |
| Scratch | `C:\Users\test\Dev\zola-spikes\p6pre\` |
| Scratch profile | `C:\Users\test\Dev\zola-spikes\p6pre\profile\` |
| Live profile | `%LOCALAPPDATA%\hermes\profiles\zola\` |
| Client logs | `%LOCALAPPDATA%\ZolaClient\logs\` |

---

## Guardrails (summary)

| ID | Rule |
|----|------|
| G-SCOPE | Diagnostic audit only; findings under `p6pre-phase6/` (+ scratch) |
| G-NOCHANGE | No edits to client, hermes-agent, live profile, lore, identity, build plans |
| G-NO-INSTALL | No package installs |
| G-SCRATCH | Probes use scratch profile only; synthetic facts; live hashes must match |
| G-ARCH | Lore is truth; code conflicts are findings; C4/S14/P4/P4-D07/P4-D27/P5-D10 locked |
| G-QUALITY | Findings cite file/class/method + line range; Hermes at pinned commit |
| G-HYPOTHESIS | LEADs confirmed/refuted with evidence; never copied as findings |
| G-PRIVACY | Counts/tags/hashes/IDs only in repo docs; no personal fact content |
| G-LIVE | Brian steps one at a time; wait for report |
| G-CLOSEOUT | Closeout only after "proceed to closeout" |
| G-NO-CROSS-SCOPE | No Android project; Android designs are context only |

---

## Phase status

| Phase | Name | Status |
|-------|------|--------|
| 1 | Setup | COMPLETE |
| 2 | Hermes Memory Layer | COMPLETE |
| 3 | Holographic Provider | COMPLETE |
| 4 | Episodes / Sessions | COMPLETE |
| 5 | Time Awareness (S43) | COMPLETE |
| 6 | Forget / Privacy | COMPLETE |
| 7 | Approvals (S35) | COMPLETE |
| 8 | Live Probes | COMPLETE |
| 9 | Synthesis | COMPLETE |
| 10 | Closeout | COMPLETE |

---

## Live profile — effective memory / approvals / agent (Phase 1)

Effective = profile `config.yaml` + `hermes_cli/config_defaults.py` (pin `345cd2b0`).

### From profile `config.yaml` (explicit)

| Key | Value | Source |
|-----|-------|--------|
| `memory.memory_char_limit` | `4400` | profile (P1-D05) |
| `memory.user_char_limit` | `4000` | profile (P5-D05) |
| `approvals.mode` | `manual` | profile (P4-D27) |
| `agent.reasoning_effort` | `medium` | profile |
| `agent.clarify_timeout` | `300` | profile |
| `model.provider` | `openai-codex` | profile |
| `model.default` | `gpt-5.6-terra` | profile |
| `security.allow_lazy_installs` | `false` | profile |

### From defaults (not overridden in profile; relevant)

| Key | Default | Source |
|-----|---------|--------|
| `memory.memory_enabled` | `True` | default |
| `memory.user_profile_enabled` | `True` | default |
| `memory.write_approval` | `False` | default |
| `memory.nudge_interval` | `10` | default |
| `memory.provider` | `""` (built-in only) | default — **no external provider active live** |
| `approvals.timeout` | `300` | default |
| `approvals.cron_mode` | `deny` | default |
| `approvals.single_query_mode` | `deny` | default |
| `approvals.unattended_mode` | `deny` | default |
| `approvals.smart_policy` | `""` | default |
| `approvals.denial_breaker_threshold` | `3` | default |
| `approvals.deny` | `[]` | default |
| `approvals.mcp_reload_confirm` | `True` | default |
| `approvals.destructive_slash_confirm` | `True` | default |
| `command_allowlist` | `[]` | default |

Note: default `approvals.mode` is `smart`; live profile forces `manual`.

---

## Live-profile hashes

### Phase 1 entry (2026-10-02)

| File | SHA-256 | Counts |
|------|---------|--------|
| `config.yaml` | `F8D7A1498F3EB41F424CCF36704B94F2E439C599002094403FEB55D30D5B05EF` | 3106 bytes |
| `memories/MEMORY.md` | `8264268512E5CC7A37FFF847F523CA142C310DBF21BEF30C2AD601EE3A5986EB` | 234 chars; 1 entry (non-heading body line) |
| `memories/USER.md` | `47A732A0B218936C9B465F6BB8ADA34BCDA4FE027660F000E9B139B4E7022D12` | 2108 chars; 25 non-heading body lines (Known Context cited 13 entries — different prior counting; chars match) |

### Pre-synthesis (Phase 8)

| File | SHA-256 | Notes |
|------|---------|-------|
| `config.yaml` | `F8D7A1498F3EB41F424CCF36704B94F2E439C599002094403FEB55D30D5B05EF` | matches Phase 1 |
| `memories/MEMORY.md` | `8264268512E5CC7A37FFF847F523CA142C310DBF21BEF30C2AD601EE3A5986EB` | matches Phase 1 — no P-4 memory write |
| `memories/USER.md` | `47A732A0B218936C9B465F6BB8ADA34BCDA4FE027660F000E9B139B4E7022D12` | matches Phase 1 — no P-4 memory write |

---

## LEAD status

| LEAD | Topic | Status | Finding ID |
|------|-------|--------|------------|
| LEAD-1 | B3 math → `execute_code` not `terminal` | **Confirmed** | P6PRE-AUD-31 |
| LEAD-2 | holographic `on_memory_write` mirrors only `add` | **Confirmed** (code + P-2) | P6PRE-AUD-08 |
| LEAD-3 | holographic `prefetch` sync vs queued | **Confirmed** | P6PRE-AUD-09 |
| LEAD-4 | `on_session_end` rarely fires on Windows path | **Confirmed** (MP path) | P6PRE-AUD-17 |
| LEAD-5 | dual write paths + competing prompt text | **Confirmed** | P6PRE-AUD-10 |
| LEAD-6 | `auto_extract` stores raw user text | **Confirmed** | P6PRE-AUD-11 |

---

## Findings (running)

| ID | Label | Severity | File | Summary |
|----|-------|----------|------|---------|
| P6PRE-AUD-01 | [MATCH] | — | `plugins/memory/__init__.py` | Profile `$HERMES_HOME/plugins/<name>/` loads without hermes-agent edits |
| P6PRE-AUD-02 | [MATCH] | — | `agent_init.py` | Built-in files stay active beside external provider |
| P6PRE-AUD-03 | [MATCH] | — | `turn_context.py` / `memory_manager.py` | Prefetch → user `<memory-context>` fence; trivial skip |
| P6PRE-AUD-04 | [GAP] | LOW | `memory_manager.py` | Prefetch timeout 8s hardcoded; no config key |
| P6PRE-AUD-05 | [MATCH] | — | `inline_tool_executors.py` | Successful add/replace/remove can mirror via notify |
| P6PRE-AUD-06 | [RISK] | MEDIUM | `agent_init.py` + loss table | Empty provider → no manager; several bypasses even when set |
| P6PRE-AUD-07 | [RISK] | MEDIUM | write inventory | Multiple memory-like writers; dual tools if provider writes |
| P6PRE-AUD-08 | [RISK] | HIGH | holographic `on_memory_write` | Add-only mirror; replace/remove leave SQLite (LEAD-2) |
| P6PRE-AUD-09 | [RISK] | MEDIUM | holographic `prefetch` | Sync search; no queue_prefetch (LEAD-3) |
| P6PRE-AUD-10 | [RISK] | HIGH | holographic tools/prompt | Dual write paths + proactive prompt (LEAD-5) |
| P6PRE-AUD-11 | [RISK] | MEDIUM | holographic auto_extract | Raw user text ≤400 chars (LEAD-6) |
| P6PRE-AUD-12 | [MATCH] | — | holographic store | Profile-local SQLite; no network |
| P6PRE-AUD-13 | [GAP] | HIGH | holographic | No episodes |
| P6PRE-AUD-14 | [GAP] | MEDIUM | holographic prefetch | Timestamps not shown to model |
| P6PRE-AUD-15 | [MATCH] | — | holographic store | Stable fact_id; real delete |
| P6PRE-AUD-16 | [RISK] | MEDIUM | P-1 | Warm prefetch fast; inserts/HRR SNR costly at 2k |
| P6PRE-AUD-17 | [RISK] | HIGH | sessions Windows path | MP on_session_end never/rarely (LEAD-4) |
| P6PRE-AUD-18 | [GAP] | HIGH | Hermes schema | No first-class episode store |
| P6PRE-AUD-19 | [MATCH] | — | session_search | P5-D06 bridge unchanged |
| P6PRE-AUD-20 | [MATCH] | — | state.db schema | Title yes; no durable recap column |
| P6PRE-AUD-21 | [RISK] | MEDIUM | turn_finalizer | Plugin on_session_end is per-turn (no transcript) |
| P6PRE-AUD-22 | [MATCH] | — | system_prompt.py | Date+TZ frozen until compression |
| P6PRE-AUD-23 | [GAP] | HIGH | message wire | Per-message times not on model wire by default |
| P6PRE-AUD-24 | [GAP] | MEDIUM | session_search | “when” strings omit TZ |
| P6PRE-AUD-25 | [MATCH] | — | pre_llm_call | Conditional time injection possible |
| P6PRE-AUD-26 | [MATCH] | — | memory_tool / P5-D10 | Forget files only; state.db stays |
| P6PRE-AUD-27 | [RISK] | HIGH | holographic + P-2 | Forget/correction do not reach provider store |
| P6PRE-AUD-28 | [GAP] | MEDIUM | stores | No superseded vs forgotten states |
| P6PRE-AUD-29 | [MATCH] | — | backup / holographic | Local; backup covers memory_store.db |
| P6PRE-AUD-30 | [MATCH] | — | disk | No encryption at rest (H4 deferred) |
| P6PRE-AUD-31 | [MATCH] | — | approval.py + logs | B3 = execute_code (LEAD-1) |
| P6PRE-AUD-32 | [RISK] | MEDIUM | execute_code guard | Always whole-script card in gateway; once non-persisting |
| P6PRE-AUD-33 | [MATCH] | — | P4-D27 | smart rejected; manual forced |
| P6PRE-AUD-34 | [GAP] | LOW | plugin register_tool | No built-in approval on plugin tools |
| P6PRE-AUD-35 | [RISK] | LOW | S35 candidates | Some shapes weaken P4-D07/D27 |
| P6PRE-AUD-36 | [GAP] | MEDIUM | P-3 credential-free serve | Agent init fails before `_init_memory`; MP hooks unobservable without auth; orphan reap still fires at WS layer |
| P6PRE-AUD-37 | [RISK] | MEDIUM | B3 / Audit 06 | One `execute_code` can raise **two** cards (whole-script + nested terminal); Approve once on the script does not block the nested card |
| P6PRE-AUD-38 | [RISK] | MEDIUM | P-4 + approval_detection | Turn 1 `execute_code`; turns 2–3 `terminal` `pattern_key=script execution via -e/-c flag` |

---

## Synthesis review fixes (2026-10-02, pre-closeout)

1. P-4 turns 2–3 `pattern_key`/`description` recorded; S16 reconcile in Audit 06; §5.8 patterns table.
2. §2 AUD-08/27: “fails open” (not closed).
3. §5.1 Model A: AUD-06 bypasses in hazard + diagram; hazard Medium.
4. §5.8: removed recommendation wording; Audit 07 Brian reports labeled paraphrase.

---

## Documents written

- `Zola_P6PRE_Audit_PROGRESS.md`
- `Zola_P6PRE_Audit_01_MemoryLayer.md`
- `Zola_P6PRE_Audit_02_Holographic.md`
- `Zola_P6PRE_Audit_03_EpisodesSessions.md`
- `Zola_P6PRE_Audit_04_Time.md`
- `Zola_P6PRE_Audit_05_ForgetPrivacy.md`
- `Zola_P6PRE_Audit_06_Approvals.md`
- `Zola_P6PRE_Audit_07_LiveProbes.md` (P-1–P-4 complete; P-3 skipped)
- `Zola_P6PRE_Audit_SYNTHESIS.md`

---

## Final findings count

**38 findings:** 8 HIGH (5 RISK + 3 GAP), 15 MEDIUM (10 RISK + 5 GAP), 4 LOW (2 RISK + 2 GAP), 11 MATCH.

**LEADs:** 6 confirmed / 0 refuted / 0 partly (LEAD-1 confirmed for B3, qualified by P-4 `terminal` path).

## Closeout

| Step | Status |
|------|--------|
| 10a Verify | PASS — changes only under `p6pre-phase6/`; hermes clean; live hashes match Phase 1 |
| 10b Progress | done — 38 findings |
| 10c Audit commit | `84f14d83db8efd7e495acbfa078a8da66b415683` |
| 10d Tip SHA | `f5fe97d99ac0953dc85137563649577c7b6a9147` |
| 10e Push branch | done |
| 10f Merge main | done (`--no-ff`) |
| 10g Merge SHA | `92dc707ac047d2808b9f1848bb0e31f96689065a` |
| 10h Delete branch | done (local + origin) |
| 10i Delete scratch | done — `C:\Users\test\Dev\zola-spikes\p6pre\` gone |

## Notes

- Audit documents only under `zola-architecture/audit/p6pre-phase6/`.
