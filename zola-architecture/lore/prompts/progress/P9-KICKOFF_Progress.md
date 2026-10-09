# P9-KICKOFF Progress — Brainstorm Intake into Lore

## Branch

- Branch: `p9-kickoff` (from `main`, not committed)
- Base / `main` HEAD: `bf38518b78d0fd44d59d64fe88c4c2ca9a9ca2cb` (P8-LORE metadata commit)
- `origin/main`: `bf38518b78d0fd44d59d64fe88c4c2ca9a9ca2cb` — matched
- Prompt: `P9-KICKOFF_Prompt_v1.0.md` (canonical: `C:\Users\test\Dev\zola-spikes\prompts\P9-KICKOFF_Prompt_v1.0.md`)
- Prompt version: 1.0 (2026-10-09)
- Prompt SHA-256 (on-disk, 22,683 bytes): `17ecfa43723e26f7ae3bccfe165fb364c605c9d8a6a33e9fba3067b32b9e3f57`
  - Developer-supplied comparison SHA: **not included** in the Phase 1 instruction. On-disk value recorded for Brian to confirm.
- Strawman: `zola-architecture/Zola_Architecture_Distributed_Presence_Device_Capabilities.md`
- Strawman SHA-256: `ba2258d00f665f4d70932a8c018fcbf965b74a65c586924bd23b851d4f4586dd` (28,627 bytes; LF; 0 CRLF; no BOM) — matched
- Hermes (read-only, closeout check only): expected `345cd2b057a452236de401d3534b8502a7465e8d`

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Inputs, branch, progress document | COMPLETE (STOP) |
| 2 | Read and confirm anchors | COMPLETE (STOP) |
| 3 | Apply the edits, show the diff | COMPLETE (STOP) |
| 4 | Closeout | COMPLETE |

## Guardrails summary

- **G-SCOPE:** docs only. `OPEN_QUESTIONS.md` annotations and S71–S76; `ROADMAP.md` candidate lines and one source line; commit the strawman byte for byte; this progress doc. Nothing else.
- **G-NO-INVENTION:** insert only the prompt's text, character for character.
- **G-ANCHORS:** exact anchors. A missing, repeated, or differing anchor stops BLOCKED.
- **G-NOCHANGE:** `DESIGN_DECISIONS.md` is read-only. No build plans, other progress docs, `identity/*`, architecture edits, source, plugin, config, client, live profile, or `hermes-agent`.
- **G-STRAWMAN:** commit the strawman unchanged. Do not reformat it or convert its line endings.
- **G-NO-CROSS-SCOPE:** do not open, read, search, or cite the Android Zola project, including `Zola Distributed Presence Architecture.md`.
- **G-PRIVACY:** no personal content beyond what the prompt supplies.
- **G-STOP:** stop after every phase.
- **G-CLOSEOUT:** commit and merge only on "proceed to closeout".
- **G-LORE-SCOPE:** no OQ is resolved or renumbered.

## Discrepancies and flags

- The developer did not supply a prompt SHA. The on-disk prompt hash above is what was computed.
- **Amendment A1** (Brian, 2026-10-09), caused by the Phase 2 flag that `DESIGN_DECISIONS.md` does not number a "layer 5" inside `P8-D02`. In E4 only, `` `P8-D02` layer 5 makes Workspace Brian-only and removes it from cron, so a background reader needs `` was replaced with `` `P8-D02` makes Workspace Brian-only (`platform == "tui"` and an empty `parent_session_id`) and excludes cron, subagents and background review, so a background reader needs ``. E1–E3 and E5–E8 are the prompt text unchanged.

## Phase 1 notes

- `main` porcelain was exactly one line: `?? zola-architecture/Zola_Architecture_Distributed_Presence_Device_Capabilities.md`.
- HEAD and `origin/main` both `bf38518b78d0fd44d59d64fe88c4c2ca9a9ca2cb`.
- Strawman matched the expected hash, size, LF endings, and no BOM. It was not opened in an editor.
- Branch `p9-kickoff` created from that tip. No lore edits.

## Phase 2 report — Read and confirm anchors

No lore edits.

### Anchor table

| Anchor | File | Found once | Line |
|---|---|---|---|
| A1 | `OPEN_QUESTIONS.md` | yes | 18 |
| A2 | `OPEN_QUESTIONS.md` | yes | 342 |
| A3 | `OPEN_QUESTIONS.md` | yes | 352 |
| A4 | `OPEN_QUESTIONS.md` | yes | 390 |
| A5 | `OPEN_QUESTIONS.md` | yes | 398 |
| A6 | `OPEN_QUESTIONS.md` | yes | 400 |
| A7 | `ROADMAP.md` | yes | 331–332 |
| A8 | `ROADMAP.md` | yes | 337 |

Highest S-number in `OPEN_QUESTIONS.md` is **S70**. S71–S76 are not filed.

Line endings: `OPEN_QUESTIONS.md` 400 CRLF, 0 bare LF. `ROADMAP.md` 337 CRLF, 0 bare LF.

`DESIGN_DECISIONS.md`: `S1 — Voice identity` present. `S4 — "Text the user" channel` present. `S7 — Scheduled work` present. `S12 — Daily Brief pipeline` present. `P8-D02` present.

No placement conflict. E4's phrase "P8-D02 layer 5" is not a numbered label in `DESIGN_DECISIONS.md`. That decision says "Five layers," then Brian-only and cron exclusion. The supplied text is unchanged. The strawman still describes Workspace and the structured store as deferred; S73's supplied text records that it predates Phases 6–8.

## Phase 3 notes

Applied E1–E8. E4 uses Amendment A1. Nothing committed. `DESIGN_DECISIONS.md` diff is empty. Strawman SHA-256 is still `ba2258d00f665f4d70932a8c018fcbf965b74a65c586924bd23b851d4f4586dd` and the file is still untracked. Removing the inserted text restores both lore files to HEAD. Bare LF count in both lore files is 0. Each of E1–E8 appears once. S71–S76 each appear once.

## Phase 4 — Closeout

### Exit criteria (before the implementation commit)

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | E1–E4 once, verbatim, directly after their anchors | ✅ | Each block count 1. E4 is Amendment A1. Removing the four lines restores the anchor lines' following lines. |
| 2 | S71–S76 once, verbatim, after S70, stated spacing | ✅ | One blank line before S71 and between entries. Block count 1. Restoring the lines matches HEAD. |
| 3 | Footer sentence once; rest of the footer unchanged | ✅ | E6 count 1. Removing that substring restores the HEAD footer line. |
| 4 | E7 and E8 once; nothing else in ROADMAP changed | ✅ | Both counts 1. Restoring those lines matches HEAD. |
| 5 | `DESIGN_DECISIONS.md` unchanged versus `main` | ✅ | `git diff` against HEAD is empty. HEAD is `main` `bf38518b`. |
| 6 | Strawman SHA-256 on disk and staged blob | ✅ | On disk and `git cat-file blob :zola-architecture/Zola_Architecture_Distributed_Presence_Device_Capabilities.md \| sha256sum` both `ba2258d00f665f4d70932a8c018fcbf965b74a65c586924bd23b851d4f4586dd`. Git printed the expected LF-to-CRLF checkout warning. The file was not edited. |
| 7 | Staged set is exactly the four files | ✅ | Checked immediately before the implementation commit. |
| 8 | `hermes-agent` clean at `345cd2b0…` | ✅ | HEAD `345cd2b057a452236de401d3534b8502a7465e8d`. Porcelain empty. |

### Files in the implementation commit

- `zola-architecture/lore/OPEN_QUESTIONS.md`
- `zola-architecture/lore/ROADMAP.md`
- `zola-architecture/Zola_Architecture_Distributed_Presence_Device_Capabilities.md`
- `zola-architecture/lore/prompts/progress/P9-KICKOFF_Progress.md`

Implementation commit: `86b96a7d70af56744724e6b59fc3c7443829ede9`

Implementation-SHA metadata commit: `5bf38cc6b78b48eee12936012b526c2223b665fe`

Merge (`--no-ff` `p9-kickoff` → `main`): `9d50ebcc7d6370c289419f7122536366b1e25df3`

Branch `p9-kickoff` deleted locally and on `origin` after this metadata commit is pushed.

