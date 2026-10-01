# P4-LORE Progress — Phase 4 Lore Closeout

## Branch

- Branch: `p4-lore`
- Base / `main` tip at branch: `ce926058a0134186d770b9fb2e291d29af581868` (`P4-VOICE` closeout tip)
- Prompt version: 1.0 (2026-10-01)
- Hermes (read-only): `345cd2b057a452236de401d3534b8502a7465e8d` (expect clean at closeout)

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Branch and Progress Document Setup | COMPLETE |
| 2 | Read, Cross-Check and Report | COMPLETE |
| 3 | Draft (STOP for developer review) | COMPLETE |
| 4 | Apply and Verify | COMPLETE |
| 5 | Closeout | COMPLETE |

## Guardrails summary

- **G-SCOPE:** `DESIGN_DECISIONS.md`, `OPEN_QUESTIONS.md`, `ROADMAP.md`; `VOICE_CONFIG.md` consistency fixes only (approved at Phase 3 STOP); this progress doc.
- **G-NOCHANGE:** no source/XAML/csproj; not `PHASE4_BUILD_PLAN.md`; not track progress docs; not canonical `SOUL.md`, live profile, or hermes-agent.
- **G-ARCH:** plan / appendices / progress disagreements → list in Phase 2, stop; appendix wins over plan when they disagree.
- **G-FORMAT / G-NO-INVENTION / G-DRAFT-FIRST:** house style; every statement traced; draft in this doc before lore edits.
- **G-STOP / G-CLOSEOUT:** stop after each phase; closeout only on "proceed to closeout".

## Routing checklist (from prompt)

### DESIGN_DECISIONS.md — "Phase 4 — Conversation Safety and Voice"

| Decision | Record | Status |
|---|---|---|
| P4-D01 | As planned (one watcher, hoisted to `MainWindow`) | applied |
| P4-D02 | Corrections: `wake.stop` not `wake.pause`; reopen `wake.start` only (A1); never `voice.toggle tts` for gating (A3) | applied |
| P4-D03 | As planned | applied |
| P4-D04 | As planned; residuals in S33 incl. Modern Standby (A2) | applied |
| P4-D05 | As planned | applied |
| P4-D06 | As planned | applied |
| P4-D07 | Approval wire facts (A8) | applied |
| P4-D08, D09 | As planned | applied |
| P4-D10 | `agent.clarify_timeout: 300` | applied |
| P4-D11 | Execution detail + amendments (A5, A6, A7) | applied |
| P4-D12 | As planned | applied |
| P4-D13 | Amendment: question only (A17); C1 stale forced flag (A23); release rules; quiet window considered & withdrawn (A33, B38) | applied |
| P4-D14 | C5b binding clear (A23); closed-clarify id cleared on turn start (`P4-FEEDBACK` K2) | applied |
| P4-D15 | As planned | applied |
| P4-D16 | As built; Hermes batch-delayed completions (A31) | applied |
| P4-D17 | Choice from `P4-FEEDBACK`; notices fixed via `ShowRequestNotice` (A30) | applied |
| P4-D18 | AUD-37 closed; monitor bout stop + quiet 0.5 s; residual ~1 s clip (A26–A28) | applied |
| P4-D19 | Final Sonia @ **0.95** (not 1.1) (B41) | applied |
| P4-D20 | Spoken-style in `SOUL.md` (heading + pointer; no full copy) | applied |
| P4-D21 | Pitch dropped; built-in Edge (B43) | applied |
| P4-D22 | Constants unchanged; Margin 5.0; `StartupWindowSeconds` 5.3; fallback-only (A37, B39, B45) | applied |
| P4-D23, D24 | As planned | applied |
| P4-D25 | As planned (approved / backed up / mirrored) | applied |
| P4-D26 | As planned (order held) | applied |
| **P4-D27 (new)** | `approvals.mode: manual` (A9) | applied |
| **P4-D28 (new)** | `voice.barge_in: false` (A15) | applied |
| **P4-D29 (new)** | Stop speaking (A25) | applied |

**Annotations on earlier decisions:**

| Decision | Annotation | Status |
|---|---|---|
| P2-D03 | Voice superseded by P4-D19 | applied |
| P2-D05 | Clarify answers routed, not submitted (P4-D14) | applied |
| P2-D09 | `voice.barge_in` false (P4-D28) | applied |
| P2-D12 | Wake reconcile single-flight + convergence (A29) | applied |
| P2-D13 | Self-interrupt trips stopped with barge-in off (P4-D28) | applied |
| P2-D15 | Fallback-only; refit P4-D22 | applied |
| P3-D04 | Awaiting-answer mapping (P4-D15) | applied |
| P3-D23 | Monitor releases also a control input (A18) | applied |
| A3 | Approval surfaced (P4-D07) | applied |

**Lessons / execution notes:** A10, A30, B41, B46, "fix the authority, not the caller" (A29), "measure before tuning" (A27) — pending.

### OPEN_QUESTIONS.md

| Entry | Action | Status |
|---|---|---|
| S32 | RESOLVED by `P4-LOCK`; residuals → S33 | applied |
| S20 | RESOLVED by `P4-REQUEST` + `P4-ASK` | applied |
| S22 | RESOLVED by `P4-VOICE`; residual timbre → new entry | applied |
| S17 | Update trailing silence ~0.50 s; refit values; still open | applied |
| S21 | Update: lock gate + Stop avoid latch; typed Cancel still latches; still open | applied |
| S26 | Update: activity line; fold resumed-running gap (A11) unless separate; still open | applied |
| **S33 (new)** | Non-interactive Windows states + Modern Standby (A2) | applied |
| **S34 (new)** | Hermes per-sentence chunking + voice-only shaping / `voice-live` (B40) | applied |
| **S35 (new)** | Approval scopes beyond once; revisit `approvals.mode` (A9) | applied |
| **New: barge-in return** | A16 full; roadmap first; AUD-37 residual (A26); echo short-tail (A32) | applied |
| **New: estimate anchor** | B45 | applied |
| **New: listen-to-think latency** | B44 | applied |
| **New: voice timbre** | B42 | applied |
| **New: UI polish** | A34 | applied |

**Close as not an open question (one line each):** A33/B38 withdrawn; A22/P4-D29; AUD-37 closed (residual in barge-in); A20 dictation hygiene — pending.

### ROADMAP.md

| Item | Status |
|---|---|
| Phase 4 COMPLETE + plan/track SHAs + final tip after this task | applied |
| Phase 5 candidate stub (barge-in return first) | applied |

**SHA table (expand in Phase 2):**

| Item | SHA (short in prompt → verify) |
|---|---|
| P4PRE audit merge | `4181f0402eaaaabf137bace3650615be00dca6af` |
| Plan v1.1 | `5eb8fd94…` |
| P4-LOCK impl / merge | `c01fe3b6…` / `245d171e…` |
| P4-REQUEST impl / merge | `d21ff9f9…` / `76ea6985…` |
| P4-ASK impl / merge | `7d0d81fc…` / `95578b10…` |
| P4-FEEDBACK impl / merge | `5c3197ed0b7f16ac75c95ccb12dc04bac0a2a290` / `044df5e3ab6ec7d6393e0ebfa915583782177c3c` |
| P4-VOICE impl / merge | `81652ca7442dd96aace777ff21914f9c9256ab42` / `e1a069eccca1e0c3d2bdc40c1c7bc5d4764f2a03` |

### VOICE_CONFIG.md (consistency)

| Check | Status |
|---|---|
| Sonia / 0.95 / edge | applied |
| `clarify_timeout: 300`, `approvals.mode: manual`, `barge_in: false` | applied |
| Tuning log Margin 5.0, StartupWindow 5.3 vs `VoiceController.cs` | applied |
| Known fix: barge-in cites P4-D28 (under P4-D25), not P4-D25 alone | applied |
| Other mismatches (report only until approved) | applied |

## Phase 1 notes

- `git status` clean on `main`.
- `git log -1 --format=%H main` = `ce926058a0134186d770b9fb2e291d29af581868` (matched).
- Branch `p4-lore` created from that tip.
- This progress document created with phase table + routing checklist.

## Phase 2 report — Read, Cross-Check and Report

### 1. Lore file conventions

**`DESIGN_DECISIONS.md`**
- `#` title; thematic `##` buckets; phase sections as `## Phase N — Name`.
- Decision bullets: `- **P#-D## — Title.**` body; cross-refs in backticks.
- Later annotations are **inline** on the older entry (e.g. `Phase 3 amendment (\`P3-D23\`): …`), not a separate changelog.
- Phase sections use intro + bullets; optional `### Decisions added during execution`, `### Final tuned values`, `### Machine notes`.
- Quoted example:

```markdown
## Phase 3 — Presence UI
…
- **P3-D10 — Location is not shown.** No Windows source; privacy. Revisit
  with `S25`.
```

**`OPEN_QUESTIONS.md`**
- Bullets `- **S## — Title.**` then body. Highest existing ID: **S32**.
- Convention: **resolved items are removed** from this file and kept in `DESIGN_DECISIONS.md` (not left as “RESOLVED” stubs). Updates edit the open entry in place (e.g. S17 “Partially resolved by…”).
- Closeout footnote at end lists what stayed open / was updated / was added.
- Quoted example:

```markdown
- **S17 — Audio-driven lip sync and precise speaking end.**
  Partially resolved by `P3-D23`: …
```

Footer pattern: `*S13 and S16 remain open. S17 updated at Phase 3 closeout; … Resolved items stay in DESIGN_DECISIONS.md.*`

**`ROADMAP.md`**
- Complete phases: `## Phase N complete` or `## Current stage — Phase N complete` with numbered ✅ steps 1–7 (AUDIT … LORE CLOSEOUT).
- SHAs as indented sub-bullets under TRACK MERGED, full hashes.
- Candidate stub: `## Phase N — not started` + disclaimer + `S##` bullets (priority first).
- Quoted stub header:

```markdown
## Phase 4 — not started
Candidates for Brian to prioritize. Not a committed order. No plan yet.
- `S32` — … Listed first.
```

### 2. Cross-check (progress vs routing / appendices)

**No hard contradictions of values/SHAs between appendices and progress** that would block drafting. Appendix wins vs plan where they disagree (e.g. `wake.stop` vs plan `wake.pause`; Sonia **0.95** vs plan provisional 1.1; pitch dropped).

#### Items in progress **not** covered by routing/appendices — need developer destination

| # | Source | Summary | Proposed destination |
|---|---|---|---|
| X1 | `P4-VOICE` Phase 6 notes | Mic stays **OFF** after clarify tool path until Text↔Voice toggle; missing `wake.resume` vs earlier sessions | **OPEN_QUESTIONS** (new) or fold into S26 / barge-in return — **ask** |
| X2 | `P4-REQUEST` B11 | ⚠️ PARTIAL: second Send after `message.complete` → new submit; drop path walkthrough-only | **note-only** under P4-D11/D12 (or OQ if developer wants) — **ask** |
| X3 | `P4-VOICE` Phase 6 | Edge “Yeah” inflection; markdown/em-dash collapses spoken pauses | Fold into **S39 timbre** / **S34 shaping**, or **ignore** — **ask** |
| X4 | `P4-FEEDBACK_D18_Probe2` | No RPC for discard-capable `voice.record stop` | Fold into **S36 barge-in return** (already in A16) — recommend fold |
| X5 | `P4-ASK` Phase 5 | Clinical “Skip” / follow-up wording is Hermes shaping | Fold into **S34** / spoken-style residual — recommend fold |
| X6 | Exit checklist / V7 | **GPU idle within 10%** never measured in `P4-VOICE` V7 | Track as **⚠️ PARTIAL acknowledged** on exit checklist, or re-measure — **ask** |
| X7 | `P4-LOCK` / REQUEST | Fact-before-queue; `_lastGatedMicLine`; Cascadia Mono; DEBUG harness | **note-only** / **ignore** (execution or style) |

#### Appendix items progress supports (no conflict)

A1–A37 / B38–B47 align with track progress (wake.stop, Modern Standby PARTIAL, barge_in false, Stop speaking, AUD-37 closed, K1 withdrawn, Sonia 0.95, pitch dropped, StartupWindow 5.3, Margin 5.0, estimate-anchor finding, etc.).

**Facts for draft (confirmed):**
- P4-D17 choice: **panel-header mirror** (not z-order raise); later `ShowRequestNotice` → `StatusText`.
- SOUL heading: `## How I talk out loud`.
- Trailing silence: **median ~0.496 s** (S17 update).

### 3. Plan “Lore Closeout” / “Exit Checklist” coverage

**Plan lore actions vs routing:** every planned action is covered; routing **adds** (appendix wins): P4-D27–D29; annotations P2-D09, P2-D12, P2-D13, P3-D23; AUD-37 closed into barge-in residual (plan said “AUD-37 if not fully fixed”); barge-in return + estimate anchor + listen-to-think + timbre + UI polish; ROADMAP barge-in first.

**Exit Checklist status (from progress):**

| Checklist item | Status |
|---|---|
| Track 1 P4-LOCK merged | ✅ (impl `c01fe3b6…`, merge `245d171e…`); sleep/wake ⚠️ PARTIAL ack |
| Track 2 P4-REQUEST merged | ✅ (impl `d21ff9f9…`, merge `76ea6985…`); B11 ⚠️ PARTIAL ack |
| Track 3 P4-ASK merged | ✅ (impl `7d0d81fc…`, merge `95578b10…`) |
| Track 4 P4-FEEDBACK merged | ✅ (impl `5c3197ed…`, merge `044df5e3…`); AUD-37 closed |
| Track 5 P4-VOICE merged | ✅ (impl `81652ca7…`, merge `e1a069ec…`) |
| One authority / no duplicate paths / named constants | ✅ per-track Part C |
| hermes-agent clean / no installs | ✅ |
| Live-profile edits P4-D25 | ✅ |
| Build on main after merges | ✅ (VOICE closeout) |
| Smoke after each track | ✅ (PARTIAL items acknowledged) |
| Phase 1–3 regression after Track 5 | ⚠️ **V7 PASS** for cold launch / Voice-Text / sessions / presence / lock / barge-in-off; **GPU idle within 10% not recorded** |
| DESIGN / OPEN / ROADMAP lore | Pending this task |

### 4. Proposed open-question ID mapping

Highest existing: **S32**. Assign next free IDs in prompt order:

| ID | Title / topic | Source |
|---|---|---|
| **S33** | Non-interactive Windows states + Modern Standby gap | A2, A4, plan |
| **S34** | Hermes per-sentence chunking + voice-only reply shaping (`voice-live`) | A4, B40, plan |
| **S35** | Approval scopes beyond “once”; revisit `approvals.mode` | A4, A9, plan |
| **S36** | Barge-in return (state-aware policy; acceptance a–e; pre-roll; AUD-37 residual; echo 1–2 word limit) | A16, A26, A32 — **roadmap first** |
| **S37** | Estimate anchor (re-anchor FSL on first reply text; `forced_estimate` no margin) | B45 |
| **S38** | Listen-to-think latency (`silence_duration` + Whisper CPU) | B44 |
| **S39** | Voice timbre (husky / breathiness → premium provider) | B42 |
| **S40** | UI polish (Esc priority; notice hold; activity during concurrent batches) | A34 |

**Resolve by removal (footnote + DESIGN pointer):** S32, S20, S22.

**Close as not an OQ (one-line notes):** A33/B38 withdrawn; A22→P4-D29; AUD-37 closed (residual→S36); A20 dictation hygiene.

### 5. SHAs (expanded and verified)

| Item | Full SHA |
|---|---|
| P4PRE audit merge | `4181f0402eaaaabf137bace3650615be00dca6af` |
| Plan v1.1 | `5eb8fd94c69889701fe12809fc2b56b79644a8dc` |
| P4-LOCK impl | `c01fe3b6725a3814a368d48c0d06a2da1d16305f` |
| P4-LOCK merge | `245d171ebd106f5af52190b63c7d18f866c5a923` |
| P4-REQUEST impl | `d21ff9f9ceeeb1fecb16c5603c6b0b9549f41ace` |
| P4-REQUEST merge | `76ea698542da538d2f8c8a0a32bf9ac1986ea062` |
| P4-ASK impl | `7d0d81fcd8283234a62ed54a3f0acaf15fb3d46c` |
| P4-ASK merge | `95578b10843feed473b83482c30e199bb909aa61` |
| P4-FEEDBACK impl | `5c3197ed0b7f16ac75c95ccb12dc04bac0a2a290` |
| P4-FEEDBACK merge | `044df5e3ab6ec7d6393e0ebfa915583782177c3c` |
| P4-VOICE impl | `81652ca7442dd96aace777ff21914f9c9256ab42` |
| P4-VOICE merge | `e1a069eccca1e0c3d2bdc40c1c7bc5d4764f2a03` |
| Base tip (this branch) | `ce926058a0134186d770b9fb2e291d29af581868` |

Hermes: `345cd2b057a452236de401d3534b8502a7465e8d` (read-only).

### 6. `VOICE_CONFIG.md` mismatches

**Matches live / code (OK):**
- yaml: `tts.provider: edge`, Sonia, `speed: 0.95`, `voice.barge_in: false`
- Live: `clarify_timeout: 300`, `approvals.mode: manual` (documented in dedicated sections)
- Tuning log: Margin **5.0**, StartupWindow **5.3** match `VoiceController.cs`

**Propose fix (known):**
1. Barge-in decision cite: change `P4-D25` / Option A → **`P4-D28` (applied under `P4-D25`)** in key bullet + “Barge-in off” table `Decision` field + section lead line.

**Other mismatches (report; fix only if approved):**
2. Section heading still **`## Voice: Sonia at 1.1`** though final speed is **0.95** — propose rename to `## Voice: Sonia at 0.95` (or “Sonia (P4-VOICE Round 1)”).
3. Top yaml restore block does **not** include `agent.clarify_timeout` or `approvals.mode` (those live in later sections only). Optional: add under `agent:` / `approvals:` for one-block restore fidelity — **ask**.
4. No factual drift found vs live Sonia/0.95/edge/barge_in/timeout/manual.

### Phase 2 stop — developer decisions needed

Before Phase 3 draft, please decide:
1. **X1** mic-off-after-clarify → new OQ / fold / ignore?
2. **X2** B11 PARTIAL → note-only vs OQ?
3. **X3** Yeah / em-dash → fold vs ignore?
4. **X6** GPU idle 10% → acknowledge ⚠️ PARTIAL vs re-measure?
5. **VOICE_CONFIG** items 2–3 (heading; yaml restore block) → approve / skip?
6. Confirm **ID map S33–S40** as proposed.

To continue: reply **proceed to phase 3** (with decisions on items 2 and 6 above).

## Developer decisions (Phase 2 → Phase 3)

| Item | Decision |
|---|---|
| X1 | New **S41** — wake/mic not restored after clarify until Text↔Voice toggle. Phase 5 stub: **S36 first, then S41**. |
| X2 | Note-only under **P4-D11**. |
| X3 | "Yeah" inflection → **S39**; markdown/em-dash pause collapse → **S34**. |
| X4 / X5 | Fold as proposed (Probe2 discard → S36; clinical Hermes wording → S34). |
| X6 | Measure GPU idle before draft (attempt 1 invalid; attempt 2 valid — see below). |
| X7 | Ignore. |
| VOICE_CONFIG | Approve all three fixes (P4-D28 cite; heading Sonia at 0.95; clarify + approvals in top yaml). |
| IDs | **S33–S41** confirmed. |

### X6 — GPU idle measurement (2026-10-01)

**Attempt 1 (invalid for presence confirm):** pid **7940** → process **`Zola.Client`**; 60 s; 26 GPU Engine instances; avg **0.0000%** / max 0.0000. No blink confirmation in that first run — discarded for exit-checklist scoring.

**Attempt 2 (valid):** window restored + foregrounded (`foregroundMatch=True`); presence rendering confirmed.
- Mapping: pid **7940** → **`Zola.Client`** (MainWindowTitle `Zola`).
- Method: 60 s, 1 s samples, sum of `GPU Engine(pid_7940_*)\Utilization Percentage` (26 instances).
- Presence: **26** `blink start` lines in `presence.log` during the window (16:03:22 … 16:05:24).
- Result: avg **3.5291%**, max **17.3556%** (n=60).
- Phase 3 baseline (idle with blinks): avg **2.2725%**.
- Budget (`P3-D09` / exit checklist ≤ 10%): **PASS**.

## Phase 3 draft — proposed lore text (revised)

> Lore files are **not** edited until the developer replies **apply lore**. Apply only this approved text (plus any developer edits sent with that reply).

### Corrections in this revision (vs prior draft)

| Change | Detail |
|---|---|
| **P4-D03** | Restored to plan title ("pre-gate state"); body: availability; never resume/replay cut-off reply; Text stays Text; Resumed+Locked stays gated until Unlocked |
| **P4-D08** | Restored to plan clarify-card list (Recommended label; free text; Skip `""`; multi-select; batch one card; collapse "You answered") |
| **P4-D09** | Restored to plan: typing answers newest open; composer enabled while streaming; answer placeholder |
| **P4-D12** | Restored to plan: `server-requests.log` (length only; no secret/vault/sudo params) |
| **Cascadia Mono** | Moved to **P4-D07** |
| **P4-D01, D02, D06, D07, D11, D14, D15, D18** | One-line titles re-aligned to plan *Decisions Resolved* |
| **P4-D13** | Removed stray "S note"; quiet-window withdrawal cites B38 only |
| **S36 (e)** | Instant answer as soon as she stops speaking (before the beep) keeps its first word |
| **GPU / ROADMAP** | Valid measurement recorded (pid→process, blinks); ROADMAP uses measured PASS |
| **ROADMAP Phase 3** | **Only** heading rename; body byte-identical to current `ROADMAP.md` |

**Other one-line re-alignments while checking every P4-D against the plan:**
- **D01** → plan title (one gate fact / one watcher hoisted).
- **D02** → plan title "On gate: pause, stop, cancel, refuse"; A1/A3 corrections stay in body.
- **D06** → "One server-request handler for every method."
- **D07** → "Approval card: Approve once / Deny" + Cascadia Mono.
- **D11** → plan title on stale/duplicate/foreign; amendments A5–A7 + B11 note-only in body.
- **D14** → "One transcript consumer routes answers."
- **D15** → "Presence and HUD while waiting for an answer."
- **D18** → plan "reproduce first, then fix or close" + AUD-37 outcome.
- **D19** → plan provisional 1.1 title; body records final **0.95**.

No other decision IDs changed meaning.

---

### A. `DESIGN_DECISIONS.md`

#### A.1 New section — insert after Phase 3 Machine notes

```markdown
## Phase 4 — Conversation Safety and Voice
Recorded from `PHASE4_BUILD_PLAN.md` v1.1 (`P4-D01`–`P4-D26`) and from the five
track progress docs, plus execution corrections and new decisions `P4-D27`–
`P4-D29` (Appendices A/B). Full plan wording stays in the build plan; this
section is the lore pointer, final values, and corrections. Evidence:
`P4-LOCK_Progress.md`, `P4-REQUEST_Progress.md`, `P4-ASK_Progress.md`,
`P4-FEEDBACK_Progress.md`, `P4-VOICE_Progress.md`.

- **P4-D01 — One gate fact: "voice is gated" = Windows locked OR system
  suspending.** Exactly one `SessionLockWatcher`, hoisted from `PresenceView`
  to `MainWindow`. `VoiceController` holds queryable gate state; presence pause
  reasons unchanged (`locked`, `suspended`).

- **P4-D02 — On gate: pause, stop, cancel, refuse. Fail closed.** Cancel
  follow-up/echo; stop capture; stop speech without cancelling the turn or
  latching `SPEECH_INTERRUPTED_NOTE` (`voice.toggle off`); refuse wake/capture/
  submit while gated. **Execution corrections:** disarm with **`wake.stop`**,
  not `wake.pause`; reopen with **`wake.start` only** (no `wake.resume`) (A1);
  never use `voice.toggle tts` for gating (A3).

- **P4-D03 — On ungate: restore exactly the pre-gate state; never resume a
  cut-off reply.** "Pre-gate state" means *availability*, not activity:
  whether speech output was enabled and whether wake was armed — never what
  was playing. Subsequent turns may speak again if speech was on before the
  gate; Text mode stays Text; audio from the interrupted turn is never
  resumed, replayed, or re-synthesized (text stays in the conversation).
  Resume-from-sleep at the lock screen (`Resumed` with `Locked` still set)
  keeps the gate closed until `Unlocked`.

- **P4-D04 — Scope is lock and sleep only.** UAC, screen-off, remote, and
  user-switch stay deferred (`S33`). Residual: Modern Standby on the Latitude
  7430 never sets `suspended=true` (⚠️ PARTIAL; sign-in-on-wake mitigation in
  `P4-REQUEST` B16). See `S33`.

- **P4-D05 — Honest HUD while gated.** Mic line shows paused for Windows
  locked/suspended ahead of other mic states.

- **P4-D06 — One server-request handler for every method.** `ServerRequestBroker`
  owns open `srq-*` requests. Clarify and approval handled; every other method
  declined visibly with a JSON-RPC error.

- **P4-D07 — Approval card: Approve once / Deny. Typed or clicked only.**
  Two buttons only (no session/permanent scopes in Phase 4). Never by voice;
  never while gated. Wire facts (A8): `all` never sent; `once` persists nothing;
  error = withdrawn; builders emit only once/deny; `pending_approval` never
  rendered; approvals coalesce. Surfaced Hermes's gate (`A3`). Command text
  uses a **Cascadia Mono** constant (token later).

- **P4-D08 — Clarify card.** Panel opens with the question; one button per
  choice if present (Hermes "(Recommended)" is a **label only**, not sent
  back); free-text field; **Skip** sends `{"answer":""}`. Multi-select:
  checkboxes + Send. Batch (`questions[]`): one card with a row per `qid`,
  one final `{"answers":{…}}`. After send, card collapses to read-only
  "You answered: …".

- **P4-D09 — Typing while a question is open answers it.** Composer stays
  **enabled while the turn is streaming**; placeholder "Answer Zola's
  question…"; Send answers the **newest open clarify** for the current
  session (not `prompt.submit`). Unchanged when no clarify is open.

- **P4-D10 — Clarify timeout 300 s.** Profile `agent.clarify_timeout: 300`
  under `P4-D25`.

- **P4-D11 — Stale, duplicate and foreign answers are impossible by
  construction.** Answers name `srq-*`; at most one response per open id;
  foreign-session requests park and re-show. **Amendments:** restart test in
  attach mode (A5); session switch stays locked while streaming with
  park/re-show (A6); reconciliation, tombstones, `_replaceMark` (A7).
  **Note:** B11 ⚠️ PARTIAL — second Send after `message.complete` starts a new
  turn; drop path walkthrough-covered only (`P4-REQUEST`).

- **P4-D12 — Server requests are logged.** `%LOCALAPPDATA%\ZolaClient\logs\
  server-requests.log`: received/shown/answered/declined/cancelled/dropped.
  **Answer text never logged — length only.** Secret, vault, and sudo params
  never logged beyond the method name.

- **P4-D13 — In Voice mode she says the question, then listens.** Amendment
  (2026-09-30): she speaks the **question only**, never the choice list;
  buttons stay on the card; spoken answers are free text. Release: natural
  bout stop authoritative; startup window then estimate; monitor unavailable
  → estimate; forced releases flagged. Mid-smoke: stale forced-release flag
  fixed (C1). Question quiet window considered and **withdrawn** (single-file
  `voice.tts` / single bout; B38).

- **P4-D14 — One transcript consumer routes answers.** `TranscriptReady`
  branch: open clarify → answer that request; else unchanged submit. Binding
  clear on C5b; closed-clarify id cleared on turn start (`P4-FEEDBACK` K2).

- **P4-D15 — Presence and HUD while waiting for an answer.** HUD
  "Waiting for your answer"; `LISTENING` if capturing else `IDLE` (not
  `THINKING`); stale-thinking clock does not run.

- **P4-D16 — Tool activity line.** Id-aware set; provisional `tool.generating`
  hint. Hermes may delay batch tool completions until the whole batch ends;
  the line shows the newest-started tool until then (A31).

- **P4-D17 — Notices are visible with the conversation panel open.** Choice:
  **panel-header mirror** (not raising Z above the panel). Execution
  correction: `ShowRequestNotice` → `StatusText` (A30).

- **P4-D18 — Lost spoken answer: reproduce first, then fix or close.**
  AUD-37 reproduced; root cause capture **timing**, not VAD (`vad: false`
  rejected). Fix: monitor natural bout stop; seed bout; quiet **0.5 s** with
  `quiet_restart`; startup window. Residual ~1 s clip on instant answers →
  `S36`. Quiet window required (F1).

- **P4-D19 — Voice: `en-GB-SoniaNeural` at speed 1.1, provisional until a live
  trial.** Live trial rejected 1.1; blind speed A/B picked **0.95**. Mirrored under
  `P4-D25`.

- **P4-D20 — Speech-shaped replies in `SOUL.md`.** Heading: `## How I talk
  out loud` (canonical file; live byte-identical). Do not copy the full text
  here.

- **P4-D21 — Pitch: blind A/B through the command provider, kept only if it
  wins.** Pitch **dropped**; built-in Edge kept (command-provider first-audio
  failed the +300 ms gate). Offline A/B heard; 0 Hz kept (B43).

- **P4-D22 — Refit `P2-D15` for the final voice.** WPS/FSL/OV unchanged;
  `FollowUpMarginSeconds` 3.0 → **5.0**; new `StartupWindowSeconds` **5.3**
  (decoupled). Estimates **fallback-only**. See `S37`.

- **P4-D23 — No premium or local neural providers in Phase 4.**

- **P4-D24 — Whole-line synthesis is not in Phase 4.** Filed as `S34`.

- **P4-D25 — Live profile edits are developer-approved, exact, and
  mirrored.**

- **P4-D26 — Track order: Lock → Request → Ask → Feedback → Voice.** Held.

- **P4-D27 — `approvals.mode: manual`.** (New.) Hermes default `smart` can
  auto-approve. Revisit with `S35`.

- **P4-D28 — `voice.barge_in: false`.** (New; `P4-ASK` Option A.) Stops the
  full-duplex barge listener from latching spoken clarify answers. Cost:
  talk-over no longer stops her (`P4-D29`). Side benefit: no `P2-D13` trips.
  Applied under `P4-D25`.

- **P4-D29 — Stop speaking.** (New.) On-screen Stop + Esc; `voice.toggle off`
  → `on` (no latch). Hidden while `QuestionSpeaking`. No follow-up after Stop.
  Known edges noted in `P4-FEEDBACK`; future with `S36`.

### Phase 4 execution notes
- Effective config = profile + `hermes_cli/config_defaults.py` (A10).
- Verify user-facing notices **on screen**, not only in logs (A30).
- Confirm voice parameters **live and blind** (B41).
- Check per-case estimate error **signs**, not averages (B46).
- Fix the **authority**, not every caller — wake reconcile single-flight
  (A29 / `P2-D12`).
- Measure before tuning capture timing (A27 / Probe 2).
```

#### A.2 Annotations — append to existing entries

**On `P2-D03`:**
```markdown
  Phase 4 (`P4-D19`): spoken voice superseded — `en-GB-SoniaNeural` at
  speed 0.95 (was Aria / provisional Sonia 1.1).
```

**On `P2-D05`:**
```markdown
  Phase 4 (`P4-D14`): clarify answers are routed to the open request, not
  submitted as a normal user turn.
```

**On `P2-D09`:**
```markdown
  Phase 4 (`P4-D28`): `voice.barge_in` is now `false` on the live profile.
```

**On `P2-D12`:**
```markdown
  Phase 4 execution correction: `ReconcileWakeRestingAsync` is single-flight
  and re-checks after await (≤ 3 passes, logged) so an in-flight pause cannot
  strand wake paused (`P4-FEEDBACK` F5b / A29).
```

**On `P2-D13`:**
```markdown
  Phase 4 (`P4-D28`): with barge-in off, the `P2-D13` self-interrupt trip
  loop no longer fires in normal Voice use.
```

**On `P2-D15`:**
```markdown
  Phase 4 (`P4-D22`): estimate is fallback-only; refit left WPS/FSL/OV
  unchanged; `FollowUpMarginSeconds` 5.0; see also `StartupWindowSeconds`
  and `S37`.
```

**On `P3-D04`:**
```markdown
  Phase 4 (`P4-D15`): awaiting-answer / waiting-for-user maps into presence
  and HUD while a clarify is open.
```

**On `P3-D23`:**
```markdown
  Phase 4 (`P4-ASK` / `P4-FEEDBACK`): monitor bout start/stop is also a
  **control input** for clarify-answer capture and reply follow-up release
  (via `PresenceAnimator` pass-through). Forced releases are flagged (A18).
```

**On `A3`:**
```markdown
  Phase 4 (`P4-D07`): Hermes approvals are surfaced in the Windows client
  (cards); mode forced `manual` (`P4-D27`).
```

---

### B. `OPEN_QUESTIONS.md`

#### B.1 Remove (resolved → DESIGN_DECISIONS)

Delete full bullets for **S20**, **S22**, **S32**.

#### B.2 Update in place

**S17:**
```markdown
- **S17 — Audio-driven lip sync and precise speaking end.**
  Partially resolved by `P3-D23` (mouth follows TTS playback presence) and
  Phase 4 monitor-driven follow-up / question release (`P4-D18`, `P4-D13`).
  Trailing silence on Sonia 0.95: median **~0.50 s** per sentence (bout stop
  minus last segment stop; n=9; `P4-VOICE` Phase 7). `P2-D15` refit values:
  WPS 2.5, FSL 3.3, OV 0.5, margin 5.0; startup window 5.3 s (separate).
  Still open: no true end-of-playback signal from Hermes; mouth still cannot
  see mid-sentence pauses; shapes remain synthetic. Peak meter still 0 on
  this machine.
```

**S21:**
```markdown
- **S21 — Typed Send and Cancel during speech are recorded as spoken
  interruptions.** Hermes still latches `SPEECH_INTERRUPTED_NOTE` for typed
  Cancel during speech. Phase 4 lock gate and Stop speaking (`P4-D02`,
  `P4-D29`) use the no-latch `voice.toggle off` path and avoid the latch.
  Still open for typed Cancel (and any other latching interrupt path).
```

**S26:**
```markdown
- **S26 — A missing `message.complete` leaves the turn "Thinking".**
  `_streaming` never clears (Audit 04 §1b); presence can stay `THINKING`.
  Phase 4 activity line (`P4-D16`) improves visibility during tools. Related
  gap (K7 / A11): resuming a still-running turn can leave `_streaming=false`
  ("resumed-running"). Still open.
```

#### B.3 New entries

```markdown
- **S33 — Non-interactive Windows states beyond lock/sleep.** UAC / secure
  desktop, screen-off, remote disconnect, user switch — no existing client
  signal (`P4-D04`). Also: **Modern Standby gap** on the Latitude 7430 —
  sleep did not deliver WTS lock or APM suspend (`suspended=true` never
  fired); Track 1 ⚠️ PARTIAL; mitigated/verified via sign-in-on-wake
  (`P4-REQUEST` B16). Fix candidates include
  `RegisterPowerSettingNotification` and related power APIs. Priority:
  raised vs Phase 3 S32 residual.

- **S34 — Hermes per-sentence chunking and voice-only reply shaping.**
  Whole-line / paragraph synthesis is blocked while Hermes hardcodes
  `SentenceChunker` (`P4-D24`). Related: a `voice-live` / `VOICE_LIVE_TURN_NOTE`
  path exists in Hermes for GPT-Live delegation but is unused by Windows;
  wording assumes paraphrase (inaccurate for Edge reading exact text) (B40).
  Also: markdown / em-dash in replies can collapse spoken pauses on Edge
  (`P4-VOICE` Phase 6 notes). Best path is upstream note or careful adopt of
  `voice-live` after tracing surface effects.

- **S35 — Approval scopes beyond "once"; revisit `approvals.mode`.**
  Phase 4 forces `manual` (`P4-D27`) because Hermes's default `smart` can
  auto-approve. Session/always scopes and whether `manual` remains required
  need their own decision.

- **S36 — Bring back talk-over barge-in without breaking Phase 4.**
  **Developer-requested; Phase 5 stub lists this first.** Reframe: detecting
  speech and interrupting her are separate — state-aware policy: speech
  during her reply → interrupt; during open clarify → answer; her echo →
  ignore. Acceptance (all): (a) talk-over stops a long reply; (b) spoken
  clarify answer works with no "Interrupted"; (c) no `P2-D13` loop; (d)
  Track 1 gate still fails closed; (e) an instant answer given as soon as she
  stops speaking (before the beep) keeps its first word (needs ~1.2 s
  pre-roll; `voice.record` has none — Probe 2 / AUD-37 residual ~1 s clip).
  Blocked by one process-global Hermes listener. Candidates: upstream
  pause-barge / clarify-aware listener / discard-capable record stop /
  pre-roll on `voice.record`; echo cancel or headset; least preferred
  client detector (`P2-D01`). Keep `P4-D13`/`D14`/`D15`/`D18`. Echo filter
  still only drops ≥3-word / ≥60% tail runs (A32).

- **S37 — Re-anchor speech estimate on first reply text.**
  `FirstSentenceLatencySeconds` is seeded at turn start; late first text
  leaves real TTS start delay uncounted, so short/medium fallback estimates
  can lead the bout (up to ~4.33 s before margin 5.0). Reply `forced_estimate`
  uses **no** `FollowUpMarginSeconds`. Monitor path is primary; this is
  fallback-only (`P4-D22` / B45).

- **S38 — Listen-to-think latency.** Too long between the user finishing
  and Zola starting to think. Measure before tuning: `voice.silence_duration`
  1.5 s and local Whisper `base` CPU time (capture stop → transcript →
  `prompt.submit`). Shorter silence risks cutting mid-thought (B44).

- **S39 — Voice timbre (husky / breathiness).** Developer wants her huskier
  or deeper. Edge exposes rate/pitch/volume only; texture needs a premium
  provider (`P4-D23`). Also: Edge "Yeah" inflection noted live (`P4-VOICE`).
  Revisit by listening.

- **S40 — UI polish after Phase 4.** Esc priority vs open clarify panel
  (F7); hold important request notices before the next status line replaces
  them; activity line can show a finished tool during a concurrent Hermes
  batch (A31 / A34).

- **S41 — Wake/mic not restored after the clarify path until a Text↔Voice
  toggle.** Observed in `P4-VOICE` Phase 6 (~2026-10-01): after a clarify
  tool turn, HUD can stay `IDLE` / `MIC: OFF`; `follow_up_release` fires but
  no `wake.resume` in the log tail (contrast earlier `wake.resume
  reason=follow-up-end`). Fails quiet (mic off). Open: exact repro; whether
  the `P2-D12` wake-reconcile fix should cover it, or the clarify path never
  requests resume. Source: `P4-VOICE_Progress.md` Phase 6 developer notes.
```

#### B.4 Footer replace

```markdown
*S13 and S16 remain open. S17, S21, S26 updated at Phase 4 lore closeout.
S20, S22, S32 resolved (see DESIGN_DECISIONS Phase 4). S33–S41 added at
Phase 4 lore closeout. Not open questions (one line): question quiet window
withdrawn (B38); gap "no Stop" closed by P4-D29; AUD-37 closed by P4-D18
(residual in S36); external dictation tool is test hygiene (A20). Resolved
items stay in DESIGN_DECISIONS.md.*
```

---

### C. `ROADMAP.md`

#### C.1 Phase 3 heading only (body byte-identical)

**Before:** `## Current stage — Phase 3 complete`  
**After:** `## Phase 3 complete`

The remainder of the Phase 3 section is unchanged. Verification block (heading renamed only):

```markdown
## Phase 3 complete
Phase 3 closed at five presence tracks plus this lore pass. The Windows
client is presence-first: Helix renders `zola.glb` with the approved unlit
look (`P3-D20` / `P3-D24`), `ZolaDisplayState` owns labels and
`PresenceMode` (`P3-D03` / `P3-D04`), and procedural life drives blink,
expression, brightness, and a TTS-gated mouth (`P3-D22` / `P3-D23`).
Particles were dropped. Idle GPU with blinks averages **2.27%** (≤ 10%);
static look ~**0.0013%**; cold rest memory **809 MB** (2048²).
1. ✅ **AUDIT** — P3PRE presence-UI audit, merged at
   `c2d6110fec5d9ee6c40a0d42d963d3838ab6fd63`.
2. ✅ **DECISIONS LOCKED** — `P3-D01`–`P3-D24`. See `DESIGN_DECISIONS.md`
   Phase 3 — Presence UI. `P2-D01` and `P2-D08` annotated.
3. ✅ **BUILD PLAN WRITTEN** — complete. See
   `zola-architecture/lore/build-plans/PHASE3_BUILD_PLAN.md` v1.7.
4. ✅ **TRACKS EXECUTED** — five tracks merged.
5. ✅ **VERIFICATION / SMOKE TEST** — each track's smoke passed. Track 5
   HUMAN-RUN smoke passed (developer: "smoke test passed").
6. ✅ **TRACK MERGED**
   - Plan initial: `5994e8bc4e1167c59304ec4b2317f8c9ed9ac94f`
   - Plan v1.2: `a03fda5389305f84668e63e437d9ee9f1b27d500`
   - Plan v1.3: `eba07383ab752bb0e7a4e75d6eeea10636ff7de3`
   - Plan v1.4: `4609c697937d2a5300897ec4575c02b38357f720`
   - Plan v1.7: `819c51b0fab8b5dafb8256fa02a558236191db7a`
   - P3-STATE: `2fb98126eed05561c86b7b3e67ed454b0e7ef331`
   - P3-SHELL: `b8bf6a15c8b806bca0fea499dbcfce0535e92932`
   - P3-RENDER: `f61e1ae014bdf22bc0cab04e128bd93f0ffdebe5`
   - P3-LOOK: `c8f666251deacaf0fcb6a714594abf44da2e931b`
   - P3-LIFE: `8a00f6e87c68d28231d9ba1fc9ec1f4d29de1f40`
7. ✅ **LORE CLOSEOUT** — this pass. `S17` updated; `S24`–`S32` filed.

## Current stage — Phase 4 complete
Phase 4 closed five conversation-safety and voice tracks plus this lore
pass. Lock/sleep gate; server-request broker; spoken clarify; tool activity
and Stop speaking; Sonia at 0.95 with spoken-style shaping; pitch dropped
(Edge). Idle GPU (Voice app idle, window foreground, presence blinks
confirmed, 60 s GPU Engine sum): avg **3.5291%** (≤ 10% budget;
Phase 3 blinks baseline was 2.27%).
1. ✅ **AUDIT** — P4PRE conversation audit, merge
   `4181f0402eaaaabf137bace3650615be00dca6af`.
2. ✅ **DECISIONS LOCKED** — `P4-D01`–`P4-D29`. See `DESIGN_DECISIONS.md`
   Phase 4 — Conversation Safety and Voice.
3. ✅ **BUILD PLAN WRITTEN** — `PHASE4_BUILD_PLAN.md` v1.1, commit
   `5eb8fd94c69889701fe12809fc2b56b79644a8dc`.
4. ✅ **TRACKS EXECUTED** — five tracks merged.
5. ✅ **VERIFICATION / SMOKE TEST** — per-track Part B; acknowledged
   PARTIALs: LOCK sleep/Modern Standby; REQUEST B11; VOICE V7 GPU
   measured at lore closeout (PASS ≤ 10%; pid 7940 → Zola.Client, 26 blinks).
6. ✅ **TRACK MERGED**
   - Plan v1.1: `5eb8fd94c69889701fe12809fc2b56b79644a8dc`
   - P4-LOCK impl: `c01fe3b6725a3814a368d48c0d06a2da1d16305f`
   - P4-LOCK merge: `245d171ebd106f5af52190b63c7d18f866c5a923`
   - P4-REQUEST impl: `d21ff9f9ceeeb1fecb16c5603c6b0b9549f41ace`
   - P4-REQUEST merge: `76ea698542da538d2f8c8a0a32bf9ac1986ea062`
   - P4-ASK impl: `7d0d81fcd8283234a62ed54a3f0acaf15fb3d46c`
   - P4-ASK merge: `95578b10843feed473b83482c30e199bb909aa61`
   - P4-FEEDBACK impl: `5c3197ed0b7f16ac75c95ccb12dc04bac0a2a290`
   - P4-FEEDBACK merge: `044df5e3ab6ec7d6393e0ebfa915583782177c3c`
   - P4-VOICE impl: `81652ca7442dd96aace777ff21914f9c9256ab42`
   - P4-VOICE merge: `e1a069eccca1e0c3d2bdc40c1c7bc5d4764f2a03`
   - Final `main` tip after this lore task: `5a43c3698ebc4796992f2709c1bfd2e1d96a8e05`
7. ✅ **LORE CLOSEOUT** — this pass. `S20`/`S22`/`S32` resolved; `S17`/`S21`/
   `S26` updated; `S33`–`S41` filed; `P2`/`P3`/`A3` annotated.

One-line track results:
- **P4-LOCK** — lock/sleep voice gate; Modern Standby ⚠️ PARTIAL.
- **P4-REQUEST** — broker + cards; `approvals.mode: manual`; B11 ⚠️ PARTIAL.
- **P4-ASK** — spoken clarify; barge_in false; question-only speech.
- **P4-FEEDBACK** — activity + notices + Stop; AUD-37 closed.
- **P4-VOICE** — Sonia 0.95; shaping; pitch dropped; P2-D15 refit/margin/
  startup window.

## Phase 5 — not started
Scope TBD; await developer instruction. Candidates (not a committed order):
- `S36` — Barge-in return (state-aware). **Listed first.**
- `S41` — Wake/mic not restored after clarify until Text↔Voice toggle.
- `S33` — Non-interactive Windows states + Modern Standby.
- `S34` — Hermes chunking / voice-only shaping / `voice-live`.
- `S35` — Approval scopes / `approvals.mode`.
- `S37` — Estimate anchor on first reply text.
- `S38` — Listen-to-think latency.
- `S39` — Voice timbre (premium provider).
- `S40` — UI polish (Esc, notice hold, activity batch).
- `S17` — Audio-driven lip sync / true end-of-playback (remainder).
- `S21` — Typed Cancel latch (remainder).
- `S26` — Missing `message.complete` / resumed-running (remainder).
- `S12` — Daily Brief pipeline.
- `S13` — SMS-reading research.
- `S16` — Google Workspace.
- `S24` — GLB asset rework.
- `S25` — HUD data sources.
- `S31` — Helix reload memory.
```

*(Keep existing `## Source documents` block unchanged.)*

**ROADMAP edit note:** rename prior `## Current stage — Phase 3 complete` → `## Phase 3 complete` only. Phase 3 body is byte-identical to current `ROADMAP.md`. Phase 4 becomes the current complete stage as shown above.

---

### D. `VOICE_CONFIG.md` — approved consistency fixes (before → after)

#### D.1 Top yaml restore block — add agent + approvals

**Before (excerpt):**
```yaml
tts:
  provider: edge
  edge:
    voice: en-GB-SoniaNeural
    speed: 0.95
voice:
  silence_duration: 1.5
  barge_in: false
  ...
```

**After (insert after `tts` / before or after `voice` as fits house style — propose after `tts` block, before `voice`):**
```yaml
tts:
  provider: edge
  edge:
    voice: en-GB-SoniaNeural
    speed: 0.95
agent:
  clarify_timeout: 300
approvals:
  mode: manual
voice:
  silence_duration: 1.5
  barge_in: false
  stop_phrases: ["stop"]
  thinking_sound: true
```

#### D.2 Barge-in bullet cite

**Before:** `` `voice.barge_in`: `false` (P4-ASK Option A / `P4-D25`). ``  
**After:** `` `voice.barge_in`: `false` (`P4-D28`, applied under `P4-D25` / P4-ASK Option A). ``

#### D.3 Section `## Barge-in off` lead + table

**Before lead:** `P4-ASK: … — P4-D25 / Option A`  
**After lead:** `P4-ASK: … — P4-D28 (applied under P4-D25) / Option A`

**Before table Decision:** `P4-D25` / Option A  
**After:** `P4-D28` (applied under `P4-D25`) / Option A

#### D.4 Section heading

**Before:** `## Voice: Sonia at 1.1 (P4-VOICE Round 1)`  
**After:** `## Voice: Sonia at 0.95 (P4-VOICE Round 1)`

---

### E. Draft checklist (self-check before apply)

- [ ] P4-D01–P4-D29 in DESIGN section; one-line titles match plan Decisions Resolved
- [ ] Cascadia Mono under P4-D07 (not D09)
- [ ] Annotations on P2-D03, P2-D05, P2-D09, P2-D12, P2-D13, P2-D15, P3-D04, P3-D23, A3
- [ ] S20/S22/S32 removed; S17/S21/S26 updated; S33–S41 present; S36(e) before-beep wording
- [ ] ROADMAP Phase 3 heading rename only (body byte-identical); Phase 4 COMPLETE; Phase 5 stub S36 then S41 first
- [ ] VOICE_CONFIG three fixes (+ Sonia heading)
- [ ] GPU idle: valid foreground + blinks measurement recorded; ROADMAP uses measured value only if valid

Applied. See Phase 4 apply notes below.

## Phase 4 apply notes (2026-10-01)

Applied approved Phase 3 draft (revised) to lore files. No source/profile/plan edits.

| File | Change |
|---|---|
| `DESIGN_DECISIONS.md` | New **Phase 4 — Conversation Safety and Voice** (`P4-D01`–`P4-D29` + execution notes); annotations on `P2-D03`, `P2-D05`, `P2-D09`, `P2-D12`, `P2-D13`, `P2-D15`, `P3-D04`, `P3-D23`, `A3` |
| `OPEN_QUESTIONS.md` | Removed `S20`/`S22`/`S32`; updated `S17`/`S21`/`S26`; added `S33`–`S41`; footer replaced |
| `ROADMAP.md` | Phase 3 heading rename only (body byte-identical to pre-edit); Phase 4 COMPLETE (GPU avg **3.5291%**); Phase 5 stub (`S36` then `S41` first); Source documents unchanged |
| `VOICE_CONFIG.md` | Top yaml `agent.clarify_timeout` + `approvals.mode`; barge-in cites `P4-D28`; Sonia heading **0.95** |

### Verify (self-check)

- [x] P4-D01–P4-D29 present; Cascadia under D07; D03/D08/D09/D12 plan wording
- [x] Annotations on listed P2/P3/A3 entries
- [x] S20/S22/S32 gone; S17/S21/S26 updated; S33–S41 present; S36(e) before-beep
- [x] ROADMAP Phase 3 body == git pre-edit body; Phase 4 GPU 3.5291; Phase 5 order
- [x] VOICE_CONFIG four consistency fixes
- [x] No edits outside G-SCOPE

## Phase 5 closeout notes (2026-10-01)

### 5a — Verify
- Build: Release win-x64 — **0 warnings, 0 errors** (`Zola.Client.csproj -c Release -r win-x64`).
- hermes-agent: clean at `345cd2b057a452236de401d3534b8502a7465e8d`.
- Diff scope: G-SCOPE only — `DESIGN_DECISIONS.md`, `OPEN_QUESTIONS.md`, `ROADMAP.md`, `VOICE_CONFIG.md`, this progress doc.

### Closeout SHAs
- Lore commit: `0fba13dc95e95780312a42febbf0a0538c5b898e`
- Merge SHA on main: `5a43c3698ebc4796992f2709c1bfd2e1d96a8e05`
- Final main tip: `43e0df5ea8678df23c375fd5eba64d62f7206a84`
