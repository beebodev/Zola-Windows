# P4-LOCK Progress — Lock and Sleep Gate

## Branch

- Branch: `p4-lock-gate`
- Recorded `main` HEAD before the plan commit: `e6d0d09f9355235d80ec98387ce8213c5ac9f9aa` (`audit: record P4PRE merge SHA`)
- Plan commit SHA (= base SHA): `5eb8fd94c69889701fe12809fc2b56b79644a8dc` (`docs: add Phase 4 build plan v1.1`)
- Plan source SHA-256: `d98b3e6c87457266c8c2d06fc57a771cb1c56977790198fa2020429a5216616e` (matched; 54,285 bytes; staged blob byte-identical to source)
- Prompt version: 1.0

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Plan Commit, Branch, and Progress Document | COMPLETE |
| 2 | Read and Understand | PENDING |
| 3 | Build: One Lock Watcher (`P4-D01`) | PENDING |
| 4 | Build: The Voice Gate (`P4-D02`, `P4-D03`) | PENDING |
| 5 | Build: Honest HUD Line (`P4-D05`) | PENDING |
| 6 | Smoke Test | PENDING |
| 7 | Closeout | PENDING |

## Guardrails summary

- **G-SCOPE:** Changes only `PHASE4_BUILD_PLAN.md` (Phase 1 on `main`), `MainWindow.xaml.cs`, `Presence/PresenceView.cs`, `VoiceController.cs`, `ZolaDisplayState.cs`, and this progress document. `SessionLockWatcher.cs` unmodified unless Phase 2 proves a hoist need (flag first).
- **G-ARCH:** The build plan is truth. Conflicts that affect a task are a stop, not a silent deviation. P4-D02 speech-stop must be proven from Hermes source in Phase 2.
- **G-PATTERN:** Read every relevant file in full before changing it. No changes from partial reads or memory of earlier phases.
- **G-NOCHANGE:** No `ChatSocket.cs`, session/process managers, XAML, Themes, csproj, other Presence files, live Hermes profile, or package installs.
- **G-COMMENT:** One `// P4-LOCK: [one-line rationale] — P4-D0X` per logically distinct changed block.
- **G-STOP:** Stop after each phase; wait for that phase's exact proceed message.
- **G-CLOSEOUT:** Closeout begins only on "proceed to closeout".
- **G-LORE-SCOPE:** `ROADMAP.md`, `DESIGN_DECISIONS.md`, and `OPEN_QUESTIONS.md` are out of scope, including closeout. `PHASE4_BUILD_PLAN.md` is not edited after Phase 1. `VOICE_CONFIG.md` is not changed.
- **G-NO-CROSS-SCOPE:** Android Zola, Ava, and the P4PRE spike folder are out of scope.
- **G-ONE-AUTHORITY:** One `SessionLockWatcher` owned by `MainWindow`. One voice gate owned by `VoiceController` (sole `wake.*` / `voice.*` / capture owner). `ZolaDisplayState` alone derives HUD strings from `VoiceController` public properties. No second transcript-to-submit path.
- **G-FAIL-CLOSED:** Any gate-close failure keeps the gate closed; open only on explicit Unlocked/Resumed leaving both locked and suspended false. Never retry into open.
- **G-CONST:** Every new string, timeout, and interval is a named constant.
- **G-DEPS:** No installs of any kind.

## Phase 2 understanding

(Pending — Phase 2.)

## Discrepancies and flags

- Phase 1: `core.autocrlf=true` emitted a checkout warning ("LF will be replaced by CRLF the next time Git touches it"). Staged blob was verified byte-identical to the plan source (SHA-256 match); commit proceeded.
- hermes-agent at Phase 1: HEAD `345cd2b057a452236de401d3534b8502a7465e8d`, tag `v2026.9.14`, `git status --porcelain` empty.

## Smoke evidence tables (Phase 6)

(Pending — Phase 6.)

## Exit-criteria table (closeout)

(Pending — Phase 7.)
