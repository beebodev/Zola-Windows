# PROC1_05 — Lore Files

**Audit:** PROC1 · Phase 2 · read-only  
**Prompt:** v1.1 · SHA-256 `94f130a0e81abb6a56a73d0bfd00ce5ab53c550bcaffed0b1295dbe0dc1d542f`

## Summary

Lore today is three root files plus `build-plans/` and `prompts/progress/`. The four SOP v3 lore files (known-issues, scenario library, experience log, fast-lane log) **do not exist yet**. Plenty of seed material already lives in S51F/S51 audits, OPEN_QUESTIONS, Phase 10 smokes, and the speech-baseline spike. Several build plans still say “SOP v2.2 Stage 3” and would need a wording pass when v3 lore lands. Proposed paths below are **options for the build plan**, not decisions.

## Evidence

### 1. Current layout and proposed homes

```
zola-architecture/lore/
  DESIGN_DECISIONS.md
  OPEN_QUESTIONS.md
  ROADMAP.md
  build-plans/          # PHASE*_BUILD_PLAN.md, S51F_BUILD_PLAN.md, …
  prompts/progress/     # *Progress.md (tracks + PROC1-AUDIT)
```

| New file (SOP v3) | Proposed path (fit root-sibling style) |
|---|---|
| Known-issues list | `zola-architecture/lore/KNOWN_ISSUES.md` |
| Behavioral scenario library | `zola-architecture/lore/SCENARIO_LIBRARY.md` |
| Experience log | `zola-architecture/lore/EXPERIENCE_LOG.md` |
| Fast-lane log | `zola-architecture/lore/FAST_LANE_LOG.md` |

Optional later: `lore/process/` if process docs proliferate — not required by the current three-root pattern.

### 2. Seed material (titles / references only)

#### Known-issues seeds

| Source | Seeds |
|---|---|
| `S51F-FIX_Progress.md` | Admit→submit coverage gap (~22 ms median); LostTurnNotice limits; beep/`sd.play` removed; `child_pid` leaf-lookup residual; crash-watch context |
| `zola-architecture/audit/s51-crash/` (`Zola_S51_Audit_01`…`_05`, `_SYNTHESIS`, `_PROGRESS`) | Group A PortAudio / Group B sqlite; serve vs client dump counts; Phase 11 block under PR-D03 |
| `OPEN_QUESTIONS.md` | **S51** (serious); **S77** speech pipeline; **S86** privacy/logs; **S90–S102** Phase 10 residuals (incl. **S100** mutex / `ANDROID_HOME` / `phone_test_keys` hygiene) |
| `P10-LORE_Progress.md` | Known-issue candidates; S51 severity confirmed Serious by Brian |
| Speech baseline (spike, not under `audit/`) | `C:\Users\test\Dev\zola-spikes\speech-baseline\SPEECH-BASELINE_Progress.md`, `findings\SPEECH-BASELINE_Findings.md` (SYM-01/02/05, S51 during A11/B6) |
| In-repo speech-related audits | No dedicated speech-baseline folder under `zola-architecture/audit/`. Related: `voicepre-standalone/`, WINH07/09, p7 echo audits |

#### Scenario / experience seeds

| Source | Seeds |
|---|---|
| P10-LORE SOP v3 candidates | P10-C4, P10-R3, P10-W1, P10-W4, P10-W6, P10-R2, P10-R1, P10-C6 |
| Phase 10 progress smokes | COMPANION C1–C11; NOTIFY N*; READ B*/R*; WATCH W1–W6; INTAKE F1–F7 |
| S51F-FIX Phase 6 | SM1 (beeps/listening), SM2 (kill + lost notice), SM3; experience checks |
| SPEECH-BASELINE | Sessions A/B cases A1–A11, B1–B10, A10r/A11r; findings Q1–Q6 |

#### Fast-lane log seeds

| Source | Note |
|---|---|
| `S51F_BUILD_PLAN.md` / `S51F-FIX_Progress.md` | Single-track fix under SOP v3 transition — natural first fast-lane exemplar |
| `ARCH-SWAP_Progress.md` | Docs-only merge under v3 transition + Brian everyday-build approval |

### 3. Templates / docs referencing SOP v2.2 (update list)

| File | Section / locus |
|---|---|
| `lore/build-plans/PHASE6_BUILD_PLAN.md` | Closing “SOP v2.2 Stage 3” |
| `lore/build-plans/PHASE7_BUILD_PLAN.md` | Phase 1 commit block; closing Stage 3 |
| `lore/build-plans/PHASE8_BUILD_PLAN.md` | Phase 1 commit block; closing Stage 3 |
| `lore/build-plans/PHASE9_BUILD_PLAN.md` | Changes → Phase 1 Stage 3 |
| `lore/build-plans/PHASE10_BUILD_PLAN.md` | Changes → Phase 1 Stage 3 |
| `lore/prompts/progress/P10-LORE_Progress.md` | G-SOP “SOP v2.2 with the v3 transition rule” (historical) |
| `lore/prompts/progress/ARCH-SWAP_Progress.md` | “SOP v2.2 verification and merge rules still apply” |
| `audit/p6pre-phase6/Zola_P6PRE_Audit_PROGRESS.md` | Header `SOP: v2.2 Stage 1` |
| `audit/p8pre-phase8/Zola_P8PRE_Audit_PROGRESS.md` | Header `SOP: v2.2 Stage 1` |
| `audit/p9pre-phase9/Zola_P9PRE_Audit_PROGRESS.md` | Header `SOP: v2.2 Stage 1` |

**Already on v3 transition wording:** `S51F_BUILD_PLAN.md`, `S51F-FIX_Progress.md`, `audit/s51-crash/*_PROGRESS`, `audit/s51f-pre/*_PROGRESS`, `ROADMAP.md` adoption line.

**Off-disk:** `Phase_SOP_Generic.md` (Claude’s project) — same gap as Phase 1. Spikes prompts under `zola-spikes\prompts\` still say SOP v2.2 in many headers (out of lore tree).

## Gaps against target state

| Target | Today |
|---|---|
| Known-issues list, scenario library, experience log, fast-lane log | Missing; seeds scattered across progress/audits/spikes |
| SOP v3 as the living process text in-repo | Partial (transition notes); canonical SOP file not on disk |

## Open questions for Brian

1. Prefer the four new files as root siblings of `DESIGN_DECISIONS.md`, or under a new `lore/process/` folder?
2. Should speech-baseline findings stay cited from `zola-spikes`, or be copied/summarized into the known-issues list when that file is created?
