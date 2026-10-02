# P6PRE Audit — Synthesis

**Audit ID:** P6PRE  
**Date:** 2026-10-02  
**Pin:** zola-windows `870b1706bb4b22fd7d4a7fda25780987e35f2bd7` on `p6pre-audit`. Hermes `345cd2b057a452236de401d3534b8502a7465e8d` (`v2026.9.14`).  
**Scope:** Memory layer, holographic provider, episodes/sessions, time (S43), forget/privacy, approvals (S35), live probes. Diagnostic only. No source changes.

Static: Audits 01–06. Live: Audit 07 (P-1/P-2 done; P-3 skipped — no safe credential path; P-4 complete). Pre-synthesis live hashes match Phase 1.

---

## 1. Finding summary

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
| P6PRE-AUD-17 | [RISK] | HIGH | sessions Windows path | MP `on_session_end` never/rarely (LEAD-4) |
| P6PRE-AUD-18 | [GAP] | HIGH | Hermes schema | No first-class episode store |
| P6PRE-AUD-19 | [MATCH] | — | session_search | P5-D06 bridge unchanged |
| P6PRE-AUD-20 | [MATCH] | — | state.db schema | Title yes; no durable recap column |
| P6PRE-AUD-21 | [RISK] | MEDIUM | turn_finalizer | Plugin `on_session_end` is per-turn (no transcript) |
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
| P6PRE-AUD-36 | [GAP] | MEDIUM | P-3 credential-free serve | Agent init fails before `_init_memory`; MP hooks unobservable without auth |
| P6PRE-AUD-37 | [RISK] | MEDIUM | B3 / code_execution_tool | One `execute_code` can raise **two** cards (whole-script + nested terminal); Approve once on the script does not prevent further cards |
| P6PRE-AUD-38 | [RISK] | MEDIUM | P-4 + `approval_detection.py` | Turn 1=`execute_code`; turns 2–3=`terminal` with `pattern_key=script execution via -e/-c flag`; not all terminal cmds card under manual |

**38 findings:** 5 HIGH RISK, 3 HIGH GAP, 10 MEDIUM RISK, 5 MEDIUM GAP, 2 LOW RISK, 2 LOW GAP, 11 MATCH.

---

## 2. Build plan implications

**P6PRE-AUD-04.** External prefetch timeout is fixed at 8s. A build that needs a tunable budget must add a config key (hermes-agent) or stay under that hard limit in the provider.

**P6PRE-AUD-06 / 07.** Live Zola has `memory.provider: ""` — no MemoryManager, no mirror/prefetch/hooks. Enabling any provider without closing bypasses (approve path, journey, review fork, second write tools) leaves dual or incomplete authority.

**P6PRE-AUD-08 / 27.** Holographic as shipped cannot be the forget/correction path: `on_memory_write` mirrors add only. P-2 confirmed replace/remove leave SQLite. Any plan that activates holographic without adapting that handler **fails open** on C8/P5-D10 — forgotten or corrected facts stay retrievable from the provider store.

**P6PRE-AUD-09 / 16.** Sync prefetch is fine at current sizes (~2 ms warm at 2k). Insert/HRR rebuild cost and SNR at ~2k/dim=1024 matter if mid-turn `add_fact` or large banks are expected. Queue prefetch remains unused.

**P6PRE-AUD-10 / 11.** Dual model-facing writers (`memory` + `fact_store`) plus auto_extract of raw user text fight “one write path” and P5-D03–D06. A Zola-owned plugin can strip tools and disable extract without editing hermes-agent.

**P6PRE-AUD-13 / 18.** No episode store in Hermes or holographic. S14 episode work is greenfield (profile store + writers), not an enable-flag.

**P6PRE-AUD-14.** Even if holographic is adapted, prefetch text omits timestamps — weak for “when did we learn this.”

**P6PRE-AUD-17 / 21 / 36.** MemoryProvider `on_session_end` is not a reliable Windows episode/flush moment: empty provider today; client never `session.close`; hard kill skips finalize; P-3 could not live-prove hooks without credentials (static LEAD-4 stands). Plugin `on_session_end` is per-turn and must not be mistaken for a boundary.

**P6PRE-AUD-23 / 24.** S43 “how long ago” lacks default per-message wire times and TZ-labeled search strings. Conditional `pre_llm_call` exists (AUD-25) without host edits.

**P6PRE-AUD-28.** Correction vs forget are distinguishable in the notify contract but not represented as states in holographic.

**P6PRE-AUD-32 / 37 / 38.** Gateway always cards whole `execute_code`; `once` does not persist. One approved `execute_code` can still raise a nested `terminal` card. P-4 also showed direct `terminal` for math with `pattern_key=script execution via -e/-c flag` (`python -c`) — S35 must cover `execute_code` and that terminal dangerous pattern (not “all terminal”).

**P6PRE-AUD-34 / 35.** A side-effect-free calculator plugin has no host approval certificate; discipline is design-time. Permanent allowlist / `smart` conflict with P4-D07/D27.

---

## 3. Pre-work required

- **P-3 residual:** MemoryProvider hook firing on the Windows orphan/reap path remains unproven live (skipped — no safe credential path). Static LEAD-4 stands; any design that depends on `on_session_end` for episodes needs a later credentialed probe or an alternate flush moment.
- **P-4 nested card:** Deny-only P-4 did not live-capture the second card after Approve. B3 historical pairing + code path still support AUD-37; an Approve-once probe would confirm nested `pattern_key` in `agent.log` if needed later.
- No config/memory-file drift from P-4 (hashes match). No blocked stop.

---

## 4. Assumptions confirmed

P6PRE-AUD-01, 02, 03, 05, 12, 15, 19, 20, 22, 25, 26, 29, 30, 31, 33.

In particular: profile providers load without hermes-agent edits; built-in files remain beside a provider; prefetch lands in the user turn; notify can mirror successful memory writes; holographic DB is local; `session_search` is still ask-only and not memory; date+TZ in system prompt; conditional time via `pre_llm_call`; forget is file-only (P5-D10); B3 was `execute_code`; live `approvals.mode: manual`.

---

## 5. Open questions for the developer

No recommendations. Options tables only.

### 5.1 Authority — which store is source of truth

| Model | SoT | Other store | Model-facing write path(s) | Fits notify bridge? | Dual-authority / drift hazard |
|-------|-----|-------------|----------------------------|---------------------|-------------------------------|
| A — Files SoT | MEMORY.md / USER.md | Provider as derived index | Intended: `memory` only (`get_tool_schemas→[]`) | Happy path yes (AUD-05) | **Medium** — AUD-06 bypasses write files without notify (index drifts stale/wrong); provider-alone writes avoided only if schemas empty |
| B — Store SoT, files off | Provider DB | Files disabled | Provider tools or adapted memory | Files off via flags | Low if single writer |
| C — Store SoT, files still written | Provider DB | Files as projection | Must not have two writers | Projection needs a single owner | **High** if memory tool still owns files |
| D — Dual tools (holographic as-is) | Unclear | Both | `memory` + `fact_store` (+ auto_extract) | Partial (add-only) | **High** (AUD-10) |

#### 5.1 data-flow diagrams (viable shapes)

**A — Files SoT + derived index (intended single write path)**

```
model
  → memory tool (add|replace|remove)
      → MEMORY.md / USER.md                 [SoT]
      → notify → on_memory_write
          → provider store                  [derived]
  → next turn: prefetch_all
      → user <memory-context>
  → file projections: the SoT files themselves
  → episode extraction: (none today) — needs separate writer moment

bypasses that reach files WITHOUT notify (AUD-06) — index not updated:
  → background review fork (skip_memory=True) may still call memory / write files
  → /memory approve apply path (when write_approval on)
  → journey / learning_mutations direct file writes
```

**B — Store SoT, files off**

```
model
  → provider write tool(s) only
      → provider store                      [SoT]
  → MEMORY.md / USER.md disabled            [not written]
  → next turn: prefetch / system_prompt_block
      → user or volatile system context
  → file projections: none (or later export job)
  → episode extraction: provider hooks if any fire
```

**C — Store SoT + file projection (must not show two model writes)**

```
model
  → ONE write API (memory tool OR provider tool — pick one)
      → provider store                         [SoT]
      → projection writer → MEMORY.md/USER.md   [derived files]
  ✗ second model-facing write path             [must not exist]
  → next turn: prefetch from store
  → episode extraction: separate from fact write
```

**D — Holographic as-is (not single-path; shown so duplication is visible)**

```
model
  → memory tool ──────────────→ MEMORY.md/USER.md
  │                              └─ notify → SQLite (add only)
  → fact_store tool ──────────→ SQLite directly
  → auto_extract (sync_turn) ─→ SQLite (raw user text)
  → prefetch ← SQLite
```

### 5.2 Provider

| Option | What | Hermes edit? | Forget/correction | Dual write | Episodes |
|--------|------|--------------|-------------------|------------|----------|
| Holographic as-is | Enable bundled/plugin holographic | No | **Fails** (AUD-08/27) | Yes (AUD-10) | None (AUD-13) |
| Holographic adapted (Zola-owned copy) | Fix `on_memory_write` replace/remove; empty tool schemas; no auto_extract; optional dated prefetch | No (profile plugin) | Can match notify contract | Avoidable | Still none unless added |
| Zola-owned provider | New local store + hooks | No | Designed fail-closed | Designed single path | Can add episode tables |
| Stay empty provider | Status quo | No | File-only (AUD-26) | N/A | N/A |

### 5.3 Episode writing

Keep rows separate — S14 must not become a pile of session summaries.

| Row | Candidate moment | Fires on Windows defaults? | Receives transcript? | If moment never fires |
|-----|------------------|----------------------------|----------------------|-----------------------|
| Session recap | Finalize / `commit_memory_session` | Rare (no `session.close`; kill skips) | If agent+history present | Title only; no durable recap column (AUD-20) |
| Session recap | Compression handoff | When context compresses | Yes (compressor) | Continues conversation — wrong “end” signal |
| Episode / event | MP `on_session_end` | **No** with empty provider; LEAD-4 if enabled | Yes when finalize runs | Missed until alternate flush |
| Episode / event | Next `session.create` / orphan reap (~20s) | Strong client signal; WS reclaim seen in P-3 | Finalize may still skip MP | Need explicit writer on create/reap |
| Episode / event | Per-turn plugin `on_session_end` | Always | **No** (AUD-21) | Wrong grain — not an episode |
| Durable fact / decision | `memory` tool (model chooses) | When she calls it | N/A | Fact never stored (P5PRE pattern) |

### 5.4 Time delivery (S43)

| Mechanism | Cache impact | Cost / tokens | Hermes edit? |
|-----------|--------------|---------------|--------------|
| Refresh `_timestamp_line` every turn | Breaks volatile system cache every turn | ~1 line/turn | Yes |
| Status quo + tools (`session_search`) | Safe | Tool when used; “when” lacks TZ (AUD-24) | No |
| Enable `gateway.message_timestamps` | User-msg history grows | ~1 prefix/msg | No (config) |
| `pre_llm_call` conditional context | User turn only; system prefix intact | Conditional | No (plugin) |
| Provider prefetch / `system_prompt_block` | User / volatile system | Conditional / on rebuild | No (profile plugin) |
| SOUL: use tools for exact time | None until tool | 0 | No (identity) |
| Client-side prefix on prompt | User turn | Per turn if always | Client only |

### 5.5 Retrieval budget (P-1 vs S38)

S38 per-turn reference: **1.5 s silence + 1.56–1.85 s transcription**.

| n facts | Warm prefetch median | vs S38 listen path | Insert median (not on critical path unless mid-turn) |
|--------:|---------------------:|--------------------|-----------------------------------------------------|
| 50 | 1.6 ms | ≪ | 7.7 ms |
| 500 | 1.9 ms | ≪ | 26.7 ms |
| 2,000 | 2.0 ms | ≪ | 61 ms (total insert run ~120 s for 2k) |

Warm HRR prefetch is negligible vs listen. Insert/bank rebuild and SNR warnings near 2k/dim=1024 are the scaling concerns (AUD-16). Prefetch timeout headroom is 8 s (AUD-04).

### 5.6 Forget — fail-closed options (correction ≠ forget)

| | Option | Requires to fail closed | Notes |
|---|--------|-------------------------|-------|
| Correction | File-only `replace` (today) | Model calls `memory replace` with `old_text` | state.db unchanged (P5-D10) |
| Correction | Provider mirror of `replace` | Handler applies `old_text` (or id) to store + index | Holographic as-is **fails** |
| Correction | Superseded state in store | Schema + retrieval hide superseded | Not in holographic (AUD-28) |
| Forget | File-only `remove` (today) | Model calls `memory remove` | Transcripts remain |
| Forget | Provider mirror of `remove` | Content/id/entity delete + FTS/vector cleanup atomic with logical delete | Holographic as-is **fails** |
| Forget | Cascade derived episodes | Episode unlink/delete when fact forgotten | No episodes today |
| Forget | Forgotten tombstone | State distinct from superseded | Not present (AUD-28) |

### 5.7 P4 revision inputs (“local only”)

| Fact | Evidence |
|------|----------|
| Built-in memory files live under `$HERMES_HOME/memories/` | Profile layout; AUD-26/29 |
| Holographic `memory_store.db` is under HERMES_HOME; no network client | AUD-12, AUD-29 |
| Hermes backup walks home + quick state files (includes memory_store.db) | AUD-29 |
| Cloud memory providers exist in ecosystem but are **not** activated live | AUD-29; live `memory.provider: ""` |
| Activating a cloud provider would add network + vendor retention | Inventory note Audit 05 |
| `state.db` / memory files / SQLite are plaintext at rest | AUD-30 (H4 deferred) |
| P-4 math turns did not change MEMORY.md / USER.md hashes | Audit 07 pre-synthesis |

### 5.8 S35 — arithmetic guidance + calculator candidates

**Plain (AUD-37):** one `execute_code` run can raise **more than one** approval card — the whole-script gate (`pattern_key=execute_code`) plus a nested `terminal` command approval inside the session kernel. Approving the script **once** does **not** prevent further cards from nested tool RPCs (and `once` does not persist for later `execute_code` calls either).

**Patterns S35 must cover (AUD-38 / Audit 06):**

| Entry | `pattern_key` | Seen live |
|-------|---------------|-----------|
| Whole-script `execute_code` | `execute_code` | B3; P-4 turn 1 |
| Nested or direct `terminal` with `python -c …` | `script execution via -e/-c flag` | P-4 turns 2–3 (direct); B3 nested card inferred same class |
| Other ordinary terminal | *(none — no card under manual)* | Not a math-card source; S16 still holds for non-matching cmds |

Manual mode does **not** card every terminal command; `python -c` is a dangerous-pattern hit (`approval_detection.py` L901–917, L1427–1440).

| Shape | Still cards | Stops cards | Weakens P4-D07? | Edits hermes-agent? | Fail |
|-------|-------------|----------------|-----------------|---------------------|------|
| SOUL: simple math without tools | Control tools; clarify | (a) if she complies | No | No | Open if she still tools |
| Side-effect-free calculator tool | Control tools | (a)/(b) if she uses it | No | No (profile plugin) if ungated | Closed if tool is pure |
| Guidance + calculator (both) | Control tools | (a) via guidance; (b) via calc | No | No | Open if she still chooses `execute_code`/`python -c` |
| Session scope for `execute_code` | First call; later free in session | Repeat math in session | Softens once-only UX | Likely client + host | Open after first approve; nested `-e/-c` terminal still cards |
| Permanent allowlist `execute_code` | Other tools | All execute_code | **Yes** | Config | Open; `-e/-c` terminal math may remain |
| Permanent allowlist `script execution via -e/-c flag` | Other dangerous patterns | That pattern only | Softens once-only for scripts | Config | Open for other math entry points |
| `smart` mode | Escalations only? | Auto-approved “safe” | Conflicts P4-D27 | Config | Open |
| Leave as-is | Every gateway `execute_code` + `-e/-c` terminal math | Nothing | No | No | Closed for code; noisy for math |

---

## 6. LEAD outcomes

| LEAD | Topic | Outcome | Finding ID |
|------|-------|---------|------------|
| LEAD-1 | B3 math → `execute_code` not `terminal` | **Confirmed** for B3 window; **qualified** by P-4 (also direct `terminal`) | P6PRE-AUD-31, AUD-38 |
| LEAD-2 | holographic `on_memory_write` mirrors only `add` | **Confirmed** (code + P-2) | P6PRE-AUD-08, AUD-27 |
| LEAD-3 | holographic `prefetch` sync vs queued | **Confirmed** | P6PRE-AUD-09 |
| LEAD-4 | `on_session_end` rarely fires on Windows path | **Confirmed** (static + empty provider); live hook probe skipped (AUD-36) | P6PRE-AUD-17, AUD-36 |
| LEAD-5 | dual write paths + competing prompt text | **Confirmed** | P6PRE-AUD-10 |
| LEAD-6 | `auto_extract` stores raw user text | **Confirmed** | P6PRE-AUD-11 |
