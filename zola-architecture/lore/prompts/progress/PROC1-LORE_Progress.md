# PROC1-LORE — Progress

**Prompt:** v1.0 · SHA-256 `2d1b251afbafe39dde5c27de5ac2ad785ec88bc3455509b2106008f4a586555c` (verified 2026-11-16)  
**SOP:** v3.0 · PROC1-STABLE/ID/DEV/GATE + S51M-FIX merged  
**Worktree:** `C:\Users\test\Dev\zola-windows-proc1-lore` · branch `proc1-lore`  
**Guardrails:** G-SCOPE · G-PRIVACY · G-EVIDENCE · G-NO-DRIFT · G-GATE · G-STOP · G-MERGE

---

## Phase 1 — Inventory and proposals (STOP)

### 1. Baselines

| Item | Value |
|------|-------|
| Prompt SHA-256 | `2d1b251a…586555c` — **match** |
| Live checkout | `main` @ `68113754c42c7c6a057fff2130cfd8aa83a1027c` · clean · = `origin/main` |
| Tag `proc1-gate` | `ceb0476f31c5a12b82bcdcbc26fb7bb2d8f6744f` |
| Tag `fix-s51m` | `7b07c70e5e666c0831c6db86d4822ed775833895` |
| Stable | `current.txt` = **`fix-s51m`** |
| Worktree | created from `origin/main` @ `6811375` |

### 2. Lore inventory

**Root files today** (only these three; four SOP v3 files absent):

| File | Entry format (SOURCE) |
|------|------------------------|
| `DESIGN_DECISIONS.md` | Thematic `##` sections; bullets `- **ID — Title.**` then indented body (`C1`, `P2-D01`, …). |
| `OPEN_QUESTIONS.md` | `- **Snn — Title.**` multi-line body; dated bold annotations. |
| `ROADMAP.md` | `## Phase N complete` checklists; `## Next` / `## Later candidates`. |

**Already recorded for S51 / PROC1 / SOP v3:**
- **S51:** OPEN_QUESTIONS **S51** (cause historically open; Phase 8–10 annotations); ROADMAP later-candidates + Phase 10 honest items.
- **SOP v3:** ROADMAP one-liner — adopted 2026-11-06; transition until first process track merges. **No** PR-D01–D09 bodies in-repo.
- **PROC1 / S51F-D* / S51M-D*:** **not** in DESIGN_DECISIONS yet (only progress/build plans).
- **Four v3 lore files:** do not exist (`PROC1_05`).

**Deferral lines ("pending crash watch" / "S51F lore closeout"):** exact phrases **not** in root lore. Closest: `S51F_BUILD_PLAN.md` § After merge / Lore closeout (after the watch); `PROC1_BUILD_PLAN.md` (KNOWN_ISSUES reflects watch when LORE runs); S51M prompt out-of-scope naming PROC1-LORE + S51F lore closeout.

### 3. Templates

| Template | In repo? | Location |
|----------|----------|----------|
| Cursor Audit / Prompt / Build Plan | **No** | Off-disk (Downloads / StudioProjects copies). Claude updates its own. |
| `PROCESS_DECISIONS.md` / Phase_SOP v3 | **No** | Same gap as PROC1-AUDIT (**NOT FOUND** on disk). |

**In-repo loci still saying SOP v2.2 Stage 3** (proposed update targets under G-SCOPE lore):

| File | Line locus |
|------|------------|
| `lore/build-plans/PHASE6_BUILD_PLAN.md` | ~1158 closing |
| `PHASE7_BUILD_PLAN.md` | ~262 Phase 1; ~988 closing |
| `PHASE8_BUILD_PLAN.md` | ~353; ~1282 |
| `PHASE9_BUILD_PLAN.md` | ~221 |
| `PHASE10_BUILD_PLAN.md` | ~283 |
| `PROC1_BUILD_PLAN.md` | ~307 (meta: "update templates…") |
| `P10-LORE_Progress.md` | ~34 G-SOP (historical) |
| `ARCH-SWAP_Progress.md` | ~40 transition note (historical) |
| `audit/p6pre|p8pre|p9pre/*_PROGRESS.md` | headers SOP v2.2 Stage 1 |

**Proposed v3 wording** (for build-plan Phase 1 / closing lines — Brian approves before Phase 2 write):

> **Phase 1:** commit this build plan under SOP v3 (Claude places it; Cursor verifies disk and blob). Stage 0 of the first track reads `KNOWN_ISSUES.md` and `EXPERIENCE_LOG.md`. Merge uses the one-command test gate (`Run-TestGate.ps1`, Zola closed, exit 0). Everyday stable is changed only by `tools/stable/` promotion when Brian approves.

Historical progress-doc G-SOP lines: leave as historical **or** add a one-line dated note — proposal: **leave unchanged** (G-NO-DRIFT).

### 4. Proposed `KNOWN_ISSUES.md` entries

Claude's S51 flag recommendation (for Brian): `0x3b1ff`/sqlite **serious=yes**, status **fix shipped, watching** until ~2026-11-23; PortAudio Group A **serious=yes**, status **mitigated, watching**, same window.

**Crash count since watch restart 2026-11-16 07:43:37** (S51M rule: serve `child_pid` **or** faulthandler in `serve-stderr`): **0** live (MEASURED 2026-11-16).

| id | title | area | severity | serious? | status | evidence | source |
|----|-------|------|----------|----------|--------|----------|--------|
| KI-S51-PA | PortAudio / Group A serve crash | voice/audio | high | **yes** (Claude rec.) | mitigated, watching | No PortAudio module crash since 2026-11-09 13:23:08; S51F-D01/D03 | S51 audit; S51F |
| KI-S51-3B1FF | `python312.dll+0x3b1ff` shutdown race | memory/serve | critical | **yes** (Claude rec.) | fix shipped, watching | S51M fix promoted 2026-11-16 07:43:37; 4 live serve crashes on old code fit race; history 6/3/1 | S51M-FIX; post-closeout |
| KI-S51-SQLITE | sqlite AV during consolidate/shutdown | memory/serve | critical | **yes** (Claude rec.) | fix shipped, watching | Same race class; history 0/2/1; Nov-12 10:47 live | S51M-FIX |
| KI-S51-UI | `Zola.Client.exe` UI crash class | client | medium | no | open / historical | Sep–Oct S51 audit client dumps | S51 audit |
| KI-S51F-ADMIT | Admit→submit gap ~22 ms median | voice | low | no | open | S51F-FIX measured | S51F-FIX |
| KI-S51F-ECHO | Self-echo (incl. 2026-11-09 S1) | voice | medium | no | open | S51F / speech baseline | S51F; spikes |
| KI-S51F-MIC | Mic button does not interrupt reply | voice | medium | no | open | S51F known | S51F |
| KI-S51F-STOP | Stop Speaking unavailable on unprompted lines | voice | medium | no | open | S51F / P9 | S51F |
| KI-S51F-CLIP | Clipped opening words | voice/TTS | medium | no | open | S51F | S51F |
| KI-S51F-HERMESROOT | Release build outside Dev can't find Hermes | launch | high | no | **fixed** | Fixed by PROC1-STABLE `ZOLA_HERMES_ROOT` | PROC1-STABLE |
| KI-PROC1-PRESENCE | `presence.log` unbounded growth | ops | medium | no | open | Was ~280 MB in PROC1 plan; remeasure at write | PROC1_05 / plan |
| KI-PROC1-WT | Leftover worktree folders | ops | low | no | open | On disk: `zola-windows-proc1-gate`, `-id`, `-stable`; `_failed` under stable | MEASURED 2026-11-16 |
| KI-PROC1-BACKUP | Stable backups never pruned | ops | low | no | open | 5 backup folders under `stable\backups` | MEASURED |
| KI-PROC1-WATCHER | Watcher `job_assigned` missing 2026-11-10 09:19 | supervision | low | no | open / historical | PROC1-STABLE record | PROC1-STABLE |
| KI-PROC1-AUTH | `hermes auth add openai-codex` "Added" without persist | auth | medium | no | open | PROC1 progress | PROC1 |
| KI-S51M-LOCK | Forget/tool reads not serialized with consolidator | memory | medium | no | open (known, not fixed) | S51M Phase 3 known issue | S51M-FIX |
| KI-S51M-RETRIEVE | Retrieval sees only finished episodes (catch-up after reopen) | memory | medium | no | open (known) | S51M | S51M-FIX |
| KI-S51M-CLOSE | Client close kills serve; graceful teardown skipped | session | medium | no | open (known) | S51M Phase 5 SOURCE | S51M-FIX |
| KI-S100-* | S100 Phase 10 ops hygiene (10 bullets) | phone/ops | low–medium | no | open | OPEN_QUESTIONS S100 | OQ S100 |
| KI-FEAT-GAUTH | Google sign-in from inside the app | auth/UX | — (feature) | no | requested | Brian verbatim appendix | appendix |

### 5. Proposed `SCENARIO_LIBRARY.md` entries

| id | title | steps (short) | expected | guards |
|----|-------|---------------|----------|--------|
| SC-S51F-SM1 | No beeps; listening cue | Wake / follow-up / clarify after S51F | No beeps; can tell listening | S51F-D03 |
| SC-S51F-SM2 | Lost request on serve kill | Kill serve mid-turn | Notice to ask again; no auto-resubmit | S51F-D04 |
| SC-S51F-SM3 | Faulthandler + restart lines | After SM2 | Env + supervisor restart/start | S51F-D06 |
| SC-S51F-EXP | Beeps / lost-request experience | Everyday after S51F | Brian's S51F experience sentences | S51F |
| SC-PROC1-S1 | Stable shortcut smoke | Desktop shortcut; wake; Q; tools | Same as pre-stable daily use | PROC1-STABLE |
| SC-PROC1-S2 | Shortcut targets stable folder | After Switch | Exe under `stable\<tag>\` | PROC1-STABLE |
| SC-PROC1-S3 | Stable isolation hashes | Cursor checks | Shortcut outside repos; hashes hold | PROC1-STABLE |
| SC-PROC1-ID1–5 | Second instance + drift | Dual start; drift notice | Refuse naming holder; drift fields | PROC1-ID |
| SC-PROC1-DEV1–6 | Dev isolation | Missing profile; synthetic mem; no phone; test Google | Live untouched | PROC1-DEV |
| SC-PROC1-GATE | Gate experience | After gate track | "Works as expected" | PROC1-GATE |
| SC-S51M-ORPHAN | New Conversation teardown + recall | Invented fact → New Conversation → ≥30s → ask | No crash; recall; WS-orphan shutdown | S51M |
| SC-SPEECH-* | Speech-baseline refs | — | Reference `zola-spikes/speech-baseline` (PROC1-D11); do not copy | PROC1-D11 |

### 6. Proposed `EXPERIENCE_LOG.md` entries

| date | track | Brian (verbatim) | note |
|------|-------|------------------|------|
| 2026-11-09 | S51F-FIX | `she no longer beeps at me.` | experience |
| 2026-11-09 | S51F-FIX | `If her backend dies while I'm asking something, I'm told it didn't go through and to ask again` | experience |
| 2026-11-10 | PROC1-STABLE | `SM-S1 is passed.  All functions worked and starting the app from the shortcut feels teh same as before.` | **repo** (use this; see disagreement) |
| 2026-11-10 | PROC1-ID | `If I start Zola twice, the second one tells me which Zola is already running and leaves her alone.` | |
| 2026-11-13 | PROC1-DEV | `I can try things in a dev Zola with made-up data and my test Google account, and my real Zola, data and phone aren't touched.` | |
| 2026-11-13 | PROC1-GATE | `Works as expected` | |
| 2026-11-15 | S51M-FIX | `When a conversation ends, Zola doesn't crash, and what I told her is still remembered next time.` | |
| 2026-11-15 | S51M-FIX smoke | `She recalled that I used to be an astronaut.` | invented fact |

### 7. `FAST_LANE_LOG.md`

**Header / rules (proposed — PROCESS_DECISIONS not on disk; Brian confirms):**

```
# Fast-lane log (SOP v3)

Work that used the fast lane instead of a full multi-phase track.
Each row: date, title, why it qualified, merge/tag, Brian approval.

Definition (to confirm against Claude's PROCESS_DECISIONS / Phase_SOP v3 when available):
small, scoped fix or docs with an existing decision; still gated; still recorded here.
```

**Work since SOP v3 adoption that might belong:**
- S51F-FIX (single-track fix under v3 transition) — natural exemplar (`PROC1_05`)
- ARCH-SWAP (docs-only + Brian everyday approval)
- S51M-FIX — see below
- PROC1 tracks — **full lane** by plan (five sequenced tracks)

**S51M-FIX lane proposal (for Brian):**  
S51M was run as a **full-lane hotfix** (Phases 1–7, design STOP, D1, stress, dev smoke, promote). SOP fast-lane (when defined) is for smaller scoped work. **Propose: record S51M as full-lane hotfix**, and optionally note it could have been argued as fast-lane crash fix — Brian decides. Canonical fast-lane text **unavailable** on disk (report at STOP).

### 8. Proposed lore records (exact draft text)

#### DESIGN_DECISIONS (new section `## Process and crash fixes`)

```
## Process and crash fixes (PROC1 / S51F / S51M)

- **S51F-D01 — Thinking sound off.** `voice.thinking_sound: false`. Crash watch starts at relaunch.
  Brian preferred spoken "let me check" style later (speech track); not hardcoded. (2026-11-09)

- **S51F-D02 — Pre-tool acknowledgement → speech track.** Deferred; Brian agreed with Claude's 5 points.

- **S51F-D03 — Hermes beeps off.** `voice.beep_enabled: false` directly after `thinking_sound: false`.
  Smoke: no beeps; can tell when listening.

- **S51F-D04 — Lost-request notice.** Visible line: "Sorry, your last request didn't go through. Please ask again."
  No auto-resubmit; no spoken notice now. Brian: "I guess the first one for now."

- **S51F-D05 — No Zira / spoken crash notice.** Agreed with Claude's recommendation (2026-11-09).

- **S51F-D06 — Faulthandler on Python children.** `PYTHONFAULTHANDLER=1` + pid logging. Agreed 2026-11-09.

- **S51M-D1 — Shutdown vs consolidator.** (A) Stop cleanly, finish later: null `_conn`, wait `store.locked`,
  then close; pending consolidates on later initialize/quiet. Brian: "(A) Approved".

- **PROC1-D1 — Stable folder + shortcut.** Release exe under `C:\Users\test\Zola\stable\<tag>\`; `dotnet run` = dev-only.
- **PROC1-D2 — Framework-dependent build.**
- **PROC1-D3 — Stable shares hermes-agent/venv for now.**
- **PROC1-D4 — Dev profile fail-closed.** Profile `zola-dev`. **Amendment:** Hermes root
  `%LOCALAPPDATA%\hermes-dev` → `hermes-dev\profiles\zola-dev`. Brian: "Approved".
- **PROC1-D5 — Dev shares Deepgram/LLM keys for now.**
- **PROC1-D6 — No real phone in dev.**
- **PROC1-D7 — Second Zola refuses; names holder; never kills first.**
- **PROC1-D8 — INFRA ≠ pass; clean full gate on exact commit.**
- **PROC1-D9 — Kotlin unit in gate; assembleDebug at promotion.**
- **PROC1-D10 — Four SOP v3 lore files as lore root siblings.**
- **PROC1-D11 — Speech baseline referenced, not copied into lore.**
- **PROC1-D12 — Backup + restore drill every promotion.**
- **PROC1-D13 — Plugins to live only via promotion; stable manifest / start check.**
- **PROC1-D14 — Dev = test Google only (or Google off); never live token.**

Brian (2026-11-09): PROC1 D1–D14 "approved". SOP v3: "SOP v3 is good".
```

#### OPEN_QUESTIONS (S51 update + new)

```
- **S51 — Backend native crash (update 2026-11-16).** PortAudio Group A mitigated by S51F (thinking sound +
  beeps off); no PortAudio crash since 2026-11-09 13:23:08. The `0x3b1ff` / sqlite class matches the S51M
  shutdown-vs-consolidator race on measured live stacks (Nov-12 pair; Nov-14 16:22; Nov-15 12:54). Fix shipped
  and promoted as `fix-s51m` (serve watch restart 2026-11-16 07:43:37). History fit remains 6/3/1 and 0/2/1 —
  longer observation decides whether that accounts for all historical rows. Counting rule: serve child_pid in
  supervisor.log (or faulthandler in serve-stderr). Supervision/recovery from P9 remains.

- **S103 — Stream direction / mic ownership residuals.** (If still open from voice tracks — keep pointer; do not
  invent.) [Phase 2: only if confirmed still open in OQ/S77 area]

- **S104 — Does S51M explain all historical 0x3b1ff/sqlite crashes?** Open by design until quiet watch on
  `fix-s51m` (~to 2026-11-23). Not claimed closed.
```

#### ROADMAP (replace/extend `## Next` process bits)

```
## Process tracks (PROC1) — COMPLETE

| Track | Tag | Implementation / merge tip |
|-------|-----|----------------------------|
| PROC1-STABLE | (via fix-s51f promote path) | see PROC1-STABLE_Progress |
| PROC1-ID | `proc1-id` | see PROC1-ID_Progress |
| PROC1-DEV | `proc1-dev` | see PROC1-DEV_Progress |
| PROC1-GATE | `proc1-gate` → `ceb0476…` | |
| S51F-FIX | `fix-s51f` | |
| S51M-FIX | `fix-s51m` → `7b07c70…` | watch restarted 2026-11-16 07:43:37 |
| PROC1-LORE | `proc1-lore` (this track) | four SOP v3 lore files |

SOP v3 rules now on after PROC1-LORE merges: Stage 0 reads KNOWN_ISSUES + EXPERIENCE_LOG; fast-lane log in use;
scenario library grows at lore closeout; merge gate = Run-TestGate (Zola closed, exit 0); stable only via tools/stable.

## Phase 11 readiness

Blocked while open **serious** known issues remain under PR-D03 (proposed: KI-S51-PA, KI-S51-3B1FF, KI-S51-SQLITE
watching). Clear only after Brian accepts dated resolve notes or changes serious flags.
```

---

## Repo vs appendix disagreements

| Topic | Appendix | Repo | Proposal |
|-------|----------|------|----------|
| STABLE experience | `I start Zola from a shortcut, and she works the same as before.` | `SM-S1 is passed.  All functions worked and starting the app from the shortcut feels teh same as before.` | **Use repo** for EXPERIENCE_LOG; note appendix paraphrase |
| PROCESS_DECISIONS / PR-D03–D04 / fast-lane full text | Prompt DoT cites them | **NOT FOUND** on disk (PROC1-AUDIT same) | Brian/Claude place files, or approve proposals from prompt quotes |
| "Pending crash watch" root lore placeholders | Implied deferred closeout | No exact root placeholders; watch result now available | Proceed to seed KNOWN_ISSUES from S51M/S51F |

---

## STOP — Phase 1

Inventory + proposals complete. **No lore files written yet.**  
Await Brian's decisions: serious flags (esp. S51 rows), FAST_LANE vs full-lane for S51M, EXPERIENCE_LOG STABLE wording, template/build-plan update scope, and any edits to the proposed tables/text.

---

## Phase 2 — Write (STOP)

Brian (verbatim): "[Go with Claude's recommendations]" plus Phase 2 corrections (serious S51 watching; S51M full-lane; EXPERIENCE_LOG repo STABLE wording; no historical build-plan/progress/audit edits; drop build-plan wording proposal; SOP quotes from Claude's copies as given in the proceed message).

### Wrote / updated

| File | Action |
|------|--------|
| `lore/KNOWN_ISSUES.md` | **new** — PR-D03 serious definition; S51 rows serious=yes watching; KI-S51-UI 4 Xaml AEs since 2026-11-01 (reported before write); presence.log absent; KI-S100 pointer; dated status lines |
| `lore/SCENARIO_LIBRARY.md` | **new** — PR-D08 fields; S51F / PROC1 / S51M scenarios; speech-baseline referenced |
| `lore/EXPERIENCE_LOG.md` | **new** — repo STABLE wording; PR-D04 minimum quote |
| `lore/FAST_LANE_LOG.md` | **new** — PR-D07 rules; no entries since SOP v3; S51M full-lane note |
| `lore/DESIGN_DECISIONS.md` | appended Process and crash fixes (S51F-D01–D06, S51M-D1, PROC1-D1–D14, PR-D01–D09) with appendix verbatim |
| `lore/OPEN_QUESTIONS.md` | S51 2026-11-16 update (stream UNRESOLVED in Group A); **S103** (S51M history) |
| `lore/ROADMAP.md` | Process tracks table with real tags/SHAs/promotion dates; Next updated |

### Verifications (MEASURED 2026-11-16)

- Tags/SHAs: PROC1-AUDIT `659025c`/`9c7059a`; STABLE `ed985f7`/`5db407f` `proc1-stable`; ID `471c5f7`/`c8bc877` `proc1-id`; DEV `07c1d4a`/`2e9bc4a` `proc1-dev`; GATE `ceb0476` `proc1-gate`; S51F `37e5f49`/`74941cf` `fix-s51f`; S51M `7b07c70` `fix-s51m`.
- Promotions: fix-s51f 2026-11-10; proc1-id 2026-11-12 07:45:41; proc1-dev 2026-11-13 11:56:37; fix-s51m 2026-11-16 07:42:36.
- Next OQ id after S102 = **S103** (used for S51M history; stream kept inside S51).
- Templates / build-plan wording: **not** edited (G-NO-DRIFT; Claude updates its copies).

Diff: `C:\Users\test\Dev\zola-spikes\prompts\PROC1-LORE_Phase2.diff`

---

## Phase 3 — Review fixes (STOP)

Applied Brian's Phase 2 review fixes:
- KNOWN_ISSUES header first sentence replaced; serious definition kept; "area the next phase builds on" remains a serious criterion.
- KI-PROC1-PRESENCE: SOURCE `PresenceView.WriteLog` → `ClientPaths.LogsDirectory`; MEASURED `%LOCALAPPDATA%\ZolaClient\logs\presence.log` = 375,592,721 bytes (unrotated); `ZolaClient-dev\logs\presence.log` = 1,481,716.
- KI-S51-UI: Nov-10 = PROC1-STABLE publish miss (fixed `dotnet build -o` + resource gate); Sep–Oct class last 2026-10-13 15:34:04; no recurrence identified since; serious=no.
- PR-D01–D09: decision then Brian verdict once each.
- PROC1-D2 build-o note; PROC1-D4 lease-sweep reason; PROC1-D6 decision text + PROC1-DEV implementation (no Tailscale sentence).
- SCENARIO_LIBRARY: removed SC-PROC1-GATE; SC-S51F-SM3 area → conversation continuity.
- ROADMAP: section "— COMPLETE"; PROC1-LORE = this commit · proc1-lore; Next drops speech-baseline item.

Diff: `C:\Users\test\Dev\zola-spikes\prompts\PROC1-LORE_Phase2.diff` (updated for Phase 3).

---

## Phase 4 — Gate, commit and merge

**Brian (verbatim):** `[commit and merge]`

### Commit

