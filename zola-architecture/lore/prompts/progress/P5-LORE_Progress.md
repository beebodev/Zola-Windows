# P5-LORE Progress — Phase 5 Lore Closeout

## Branch

- Branch: `p5-lore`
- Base (`main` HEAD at branch create): `f47a5f850bbd38058e4c66f13336fede22f1c428`
- Prompt version: 1.0 (2026-10-02)
- Prompt file (authoritative): `C:\Users\test\Dev\zola-spikes\prompts\P5-LORE_Prompt_v1.0.md`
  SHA-256 `7b4cf70c7bb202a1cbaca51d856e3334f15d9eeb28aa93dbe67da3b104b563a6` (verified 2026-10-02 before Phase 1)
- Hermes (read-only): `345cd2b057a452236de401d3534b8502a7465e8d` (expect clean at closeout)

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Branch and Progress Document | COMPLETE |
| 2 | Read, Cross-Check, Report | COMPLETE |
| 3 | Draft (STOP for review) | COMPLETE |
| 4 | Apply and Verify | COMPLETE |
| 5 | Closeout | COMPLETE |

## Guardrails summary

- **G-SCOPE:** Only `DESIGN_DECISIONS.md`, `OPEN_QUESTIONS.md`, `ROADMAP.md`, and this progress doc.
- **G-NOCHANGE:** No source/XAML/csproj, `identity/*`, build plans, other progress docs, audits, live profile, hermes-agent.
- **G-ARCH:** Build plan, progress docs, and Appendix A are truth. Appendix A wins where it explicitly corrects the plan. Progress-doc evidence wins for measured results. Uncovered conflicts → stop.
- **G-NO-INVENTION:** Every lore statement traces to a source; flag gaps.
- **G-FORMAT:** House style (Phase 4 pattern); CRLF; keep structure.
- **G-DRAFT-FIRST:** Draft in this doc (Phase 3) before any lore edit.
- **G-PRIVACY:** No memory/conversation/skill content beyond progress-doc test statements.
- **G-STOP / G-CLOSEOUT:** Stop after each phase; closeout only on "proceed to closeout".
- **G-NO-CROSS-SCOPE:** Android Zola out of scope.

## Routing checklist

### DESIGN_DECISIONS.md — "Phase 5 — Wake After Questions and Memory"

| Item | Record (summary) | Status |
|---|---|---|
| Pointer paragraph | Plan v1.2; P5PRE merge `c5be52e…`; P5-KICKOFF / P5-WAKE / P5-MEMORY | applied |
| P5-D01 | As revised v1.2; CancelFollowUp clears `seen`; supersedes v1.1 open-path reset; resolves S41; B1–B8 PASS | applied |
| P5-D02 | As built; one noop record per silent exit; resume-skipped first predicate; `_cancelReason` clear; `seen=`; 144 records | applied |
| P5-D03 | Amendment; identity-voiced SOUL; Brian STOP revisions; no fallback sentence; save-rate results; canonical `identity/SOUL.md` | applied |
| P5-D04 | As planned, ⚠️ 9/10; #12 → user `[schedule]`; S14 input | applied |
| P5-D05 | As planned; 2750→4000; capacity ~53 chars/fact; ~30 / ~74 remaining | applied |
| P5-D06 | As planned, ⚠️; search-on-ask OK, no timing; S43 evidence; S42 principle "never **automatically**" | applied |
| P5-D07 | As planned; blind test; per-candidate table; skills check 5 procedural | applied |
| P5-D08 | As planned; S36 gate NO; barge_in false; O2 only | applied |
| P5-D09 | As planned; S38 measurements; no tuning | applied |
| P5-D10 | Supersedes C8 MEMORY-only; forget both files; state.db not redacted | applied |
| P5-D11 | As planned; Phase 6 = S14 + S43; P4 revisit local-only | applied |
| Annotation C8 | Superseded by P5-D10 | applied |
| Annotation S14 | Phase 6 primary; episodes + capacity + routing miss + skills; P4 local-only | applied |
| Annotation P4 | Revisit Phase 6 local-only; not revised here | applied |
| Annotation P1-D05 | Budget 4400/4000; tags in live soul | applied (on C4; architect-approved) |
| Annotation P2-D12 | Closing window clears all flags (P5-D01) | applied |
| Annotation P4-D28 | Stands (P5-D08) | applied |
| Phase 5 execution notes | Six process lessons (overlap proof; close owns cleanup; autocrlf blob; spikes SHA; G-BLIND; noop placement) | applied |

### OPEN_QUESTIONS.md

| Entry | Action | Status |
|---|---|---|
| S41 | Remove; footer | applied |
| S42 | Keep/update; facts half resolved; principle amended; episodes → S14 | applied |
| S36 | Update; gate NO; options matrix; stays open | applied |
| S38 | Update with P5-D09 measurements; stays open | applied |
| S35 | Add B3 approval-per-math-problem observation | applied |
| S40 | Add empty-box-while-thinking observation | applied |
| S43 (new) | Time awareness; BR1 evidence; Phase 6 with S14 | applied |
| S44 (new) | No clarify card in Voice mode (Appendix A3) | applied |
| Footer | S41 resolved; S42 facts half; S43/S44 added; S35/S36/S38/S40 updated | applied |

### ROADMAP.md

| Item | Action | Status |
|---|---|---|
| Phase 5 complete | Replace "Phase 5 scoped"; 7-stage list; theme; track results | applied |
| Phase 6 stub | Current stage — Memory (not started); S14+S43; carry candidates | applied |

## Phase 2 cross-check

### Confirmations

- **S14 location:** In `DESIGN_DECISIONS.md` under `## Scope / deferral` (bullet **S14**), not in `OPEN_QUESTIONS.md`. Confirmed.
- **OPEN_QUESTIONS footer (current, exact sense):** italic block ending the file — S13/S16 remain open; S17/S21/S26 updated at Phase 4 lore; S20/S22/S32 resolved (DESIGN_DECISIONS Phase 4); S33–S41 added at Phase 4 lore; S42 added at Phase 5 kickoff (2026-10-01); plus non-open one-liners; "Resolved items stay in DESIGN_DECISIONS.md."
- **ROADMAP `## Current stage — Phase 5 scoped`:** Present at L124–139 (scope locked 2026-10-01; track order S41→S42→S36; P5PRE not started; in-scope S41/S42/S36/S38; candidates list). Blank-line density is thinner than Phase 4 complete block (P5-KICKOFF note in prompt: restore house style when rewriting).

### Full SHAs (from progress docs / plan)

| Item | Full SHA |
|---|---|
| P5PRE merge | `c5be52e47ef8686d3643f5c57cf262cfd3991b8b` |
| Plan v1.1 commit / merge | `4c6c6439ec20e689a584d42b4c073920fb1afcd2` / `198fb00a28ea7036624ff44d0d3e58fa228e474a` |
| Plan v1.2 commit / merge | `e2150607f24f9efa04098049dc0610f59d3c79bb` / `97dd29b40ae16d4b79aff436cfed08b35c2d18ca` |
| P5-KICKOFF impl / merge | `41585cfdff5f00ee6845fe12753bad8390573ebd` / `9b2ca57f94d42ea5a4a7388c8fddb5d649b1d7b1` |
| P5-WAKE impl / merge | `fdfe3bf255e7c0847a90f241d9e03e6293434727` / `d20fbe96fc4af4bf78d48b753b2e3acfa2615418` |
| P5-MEMORY impl / merge | `9a0e45991d45a7e0d191db2e8df864399551bf48` / `569d0d0f24414b3493586237d8039ae2866f93e8` |
| P5-MEMORY final tip (pre-lore) | `f47a5f850bbd38058e4c66f13336fede22f1c428` |

### Evidence map (routing checklist → sources)

| Checklist row | Evidence present? | Primary sources |
|---|---|---|
| Pointer | yes | `PHASE5_BUILD_PLAN.md` v1.2; P5PRE merge above; `P5-KICKOFF`/`P5-WAKE`/`P5-MEMORY` progress |
| P5-D01 | yes | Plan P5-D01 v1.2; `P5-WAKE` Phase 2 overlap BLOCKED → v1.2; B1–B8 PASS; impl `fdfe3bf2…` |
| P5-D02 | yes | Plan P5-D02; `P5-WAKE` Phase 3 + logging corrections; Part C 144 noops |
| P5-D03 | yes | Appendix A1 (wins over plan "outranks"); `P5-MEMORY` approved SOUL text + 6/6,0/4,2/2,correction PASS |
| P5-D04 | yes | `P5-MEMORY` exit ⚠️ #12 → user `[schedule]`; developer-ack; S14 input |
| P5-D05 | yes | Plan P5-D05; live config; capacity ~53.3 / ~30 / ~74 in `P5-MEMORY` |
| P5-D06 | yes | Plan + Appendix A2; BR1 PARTIAL (search OK, no timing); S42 principle amend |
| P5-D07 | yes | Plan; per-candidate table; skills 5 procedural (`P5-MEMORY` Phase 2) |
| P5-D08 | yes | Plan; P5PRE SYNTHESIS feasibility NO; O1–O5 matrix; P4-D28 stands |
| P5-D09 | yes | Plan P5-D09 numbers (1500 ms; 1562–1847 ms; <15 ms) |
| P5-D10 | yes | Plan P5-D10; cleanup forgot both files BYTE-IDENTICAL; supersedes C8 |
| P5-D11 | yes | Plan P5-D11; Phase 6 = S14+S43; P4 local-only revisit |
| Ann. C8 | yes | Plan lore closeout; C8 at DESIGN_DECISIONS Client integration |
| Ann. S14 | yes | S14 under Scope/deferral; Appendix A5 inputs |
| Ann. P4 | yes | P4 bullet under Provider/vendor L171; P5-D11 |
| Ann. P1-D05 | **gap** | Fact evidence yes (`P5-MEMORY`, `MEMORY_CONVENTIONS`, C4). **No `P1-D05` bullet exists in DESIGN_DECISIONS.md** (P1-MEMORY track used that ID; lore only has C4's "raise budget / tagging"). See Discrepancies. |
| Ann. P2-D12 | yes | P2-D12 in Phase 2 section; P5-D01 window-close rule |
| Ann. P4-D28 | yes | P4-D28 in Phase 4 section; P5-D08 |
| Exec notes | yes | Appendix A6; `P5-WAKE` Phase 1 autocrlf / Phase 2 BLOCKED / logging; `P5-MEMORY` |
| OQ S41 remove | yes | Resolved P5-D01 / P5-WAKE |
| OQ S42 update | yes | Facts half P5-MEMORY; principle P5-D06; episodes → S14 |
| OQ S36 update | yes | P5PRE SYNTHESIS matrix; gate NO |
| OQ S38 update | yes | P5-D09 measurements |
| OQ S35 add | yes | `P5-WAKE` B3 Brian: card per math problem |
| OQ S40 add | yes | `P5-MEMORY` cleanup: empty box while thinking |
| OQ S43 new | yes | Plan + Appendix; BR1 no timing |
| OQ S44 new | yes | Appendix A3 |
| OQ Footer | yes | Current footer text above; will extend |
| ROADMAP P5 complete | yes | SHAs + smoke results above; Phase 4 style at L83–122 |
| ROADMAP P6 stub | yes | Plan P5-D11 + prompt carry list |

### Conflicts (plan vs progress vs Appendix A)

| Topic | Conflict | Resolution (G-ARCH) |
|---|---|---|
| P5-D03 "outranks" | Plan P5-D03 paragraph vs identity-voiced approved SOUL | **Appendix A1 wins** — record Amendment; fallback sentence not used |
| P5-D01 open-path reset | Plan v1.1 vs v1.2 CancelFollowUp | **Plan v1.2 + P5-WAKE evidence** — As revised |
| P5-D04 / D06 results | Plan exit criteria ideal ✅ vs measured ⚠️ | **Progress-doc evidence wins** — record ⚠️ as in routing table |
| P1-D05 annotation target | Checklist names P1-D05; file has no such bullet | **Discrepancy** — propose annotate **C4** (or add thin P1-D05 pointer). Needs architect call at Phase 3 STOP; not inventing a new decision |

No uncovered conflict requiring hard BLOCKED stop; P1-D05 placement is the only placement gap.

## Phase 3 draft

**Placement call (STOP):** P1-D05 annotation goes on **C4** (no standalone `P1-D05` bullet exists). Say so if you want a thin new bullet instead.

> Lore files are **not** edited until **"proceed to phase 4"**. Apply only this approved text (plus any edits sent with that reply).

### A. `DESIGN_DECISIONS.md`

#### A.1 New section — insert after Phase 4 execution notes

```markdown
## Phase 5 — Wake After Questions and Memory
Recorded from `PHASE5_BUILD_PLAN.md` v1.2 (`P5-D01`–`P5-D11`), the P5PRE
audit (merge `c5be52e47ef8686d3643f5c57cf262cfd3991b8b`), and the progress
docs `P5-KICKOFF_Progress.md`, `P5-WAKE_Progress.md`, and
`P5-MEMORY_Progress.md`. Full plan wording stays in the build plan; this
section is the lore pointer, amendments, and measured results.

- **P5-D01 — A follow-up window that closes clears all of its own flags.**
  **As revised in plan v1.2.** `CancelFollowUp`, the single window-closing
  path, also clears `_followUpTranscriptSeen`. **Amendment:** the v1.1
  approach (reset five fields at window open in `OnTurnCompleted`) was
  superseded after P5-WAKE Phase 2 found that a clarify capture can still
  be live at turn completion (`AbandonPendingQuestionIfId` on card Cancel
  or timeout). Resolves `S41`. Smoke B1–B8 PASS.

- **P5-D02 — Make wake reconcile observable.** **As built.** One structured
  `wake reconcile noop reason=…` record per silent exit, carrying the full
  `Resting` snapshot, written only when the pass sent neither pause nor
  resume. `wake.resume skipped reason=` names the first failing predicate.
  `_cancelReason` is cleared at reply-window arm (logging latch). `seen=`
  is on `follow_up_release`. Observed volume: 144 records in ~40 min of
  smoke testing (watch it).

- **P5-D03 — She saves lasting facts, and her instructions override the
  tool's.** **Amendment.** The "What I remember" section is
  **identity-voiced** (not the plan paragraph's "outranks" phrasing).
  Brian revised it at the P5-MEMORY Phase 3 STOP, adding "I save what
  Brian tells me, what we clearly decide, and what I've confirmed; I
  don't turn guesses or assumptions into facts" and "When Brian corrects
  something or it changes, I update the existing fact instead of keeping
  both versions." The pre-agreed fallback priority sentence was **not
  needed**. Results: lasting 6/6, trivial 0/4, explicit 2/2, correction
  PASS (add then replace), brief mention heard on every self-initiated
  save. Canonical text: `identity/SOUL.md`.

- **P5-D04 — Routing between the two files.** **As planned, result ⚠️
  9/10.** #12 (registration) went to `user` as `[schedule]`, grouped by
  kind of fact, not by subject. Developer-acknowledged. Recall is
  unaffected (both files are injected every turn). An `S14` input.

- **P5-D05 — Budget.** **As planned.** `user_char_limit` 2750 → 4000
  (`memory_char_limit` stays 4400). Capacity data: ~53 characters per
  saved fact; after the test, room for ~30 more in `USER.md` and ~74 in
  `MEMORY.md`.

- **P5-D06 — Episode bridge: search past conversations only when asked.**
  **As planned, result ⚠️.** `session_search` ran only on the explicit
  question, the answer was correct, and nothing was saved from it, but
  there was **no timing** in the reply. Developer-acknowledged. Evidence
  for `S43`. Amends the `S42` principle to: sessions never
  **automatically** read each other's transcripts.

- **P5-D07 — Proof is a scripted save-rate test, not a feel.** **As
  planned.** Blind, scripted save-rate test; per-candidate table in
  `P5-MEMORY_Progress.md`; skills check found 5 agent-managed skills, all
  procedural, with no personal facts.

- **P5-D08 — S36 deferred by the feasibility gate.** **As planned.**
  Feasibility gate NO. `voice.barge_in: false` stands (`P4-D28`). Only
  upstream O2 passes acceptance (a)–(e).

- **P5-D09 — S38 stays open, with its measurements.** **As planned.**
  Warm, after he stops talking: 1500 ms configured silence; 1562–1847 ms
  WAV → transcript (Whisper `base` + delivery), roughly flat across
  2.5–11 s clips; other stages under 15 ms. No tuning.

- **P5-D10 — Forget scope (supersedes C8's `MEMORY.md`-only scope).**
  Forget removes the entry from whichever memory file holds it,
  `MEMORY.md` or `USER.md`. `state.db` (transcripts and stored prompts)
  is not redacted (accepted v1 posture).

- **P5-D11 — Phase 6 is memory.** **As planned.** Phase 6 = `S14`
  (structured local store: entity facts, episodes, relevance retrieval) +
  `S43` (time awareness), starting with its own audit. `P4` to be
  revisited there as "local only".

### Phase 5 execution notes
- A G-ARCH pre-check stopped a fix that would have clobbered a live
  capture. **Prove the overlap before building.**
- A window's **close** owns its cleanup: the authority that ends a window
  clears all of its flags.
- The repo uses `core.autocrlf=true`. Verify the **staged blob** hash,
  not "no normalization".
- Prompts are also written to `zola-spikes\prompts\`, with SHA read-back.
  Staged files get unique, versioned names (a cached write was caught by
  read-back).
- Blind behavioral tests (G-BLIND) plus per-candidate data beat feel.
- Logging records must not claim "noop" after an action. Review
  diagnostic placement.
```

#### A.2 Annotations (inline, one short Phase 5 note each)

**C8** — append after existing body:
```markdown
  Phase 5 (`P5-D10`): superseded — forget removes the entry from whichever
  memory file holds it (`MEMORY.md` or `USER.md`); `state.db` is not
  redacted.
```

**C4** (stands in for P1-D05 / P1-MEMORY — STOP placement):
```markdown
  Phase 5 (`P5-D05` / P1-D05): budget now 4400 / 4000; the `[tag]`
  convention is now in the live soul (`What I remember`).
```

**S14** — append after existing body:
```markdown
  Phase 5 (`P5-D11`): Phase 6 primary. Adds the `S42` episodes remainder,
  P5-MEMORY capacity data (~53 chars/fact), the routing-miss pattern
  (#12), and the skills finding (no personal facts in agent-managed
  skills). `P4` to be revisited as "local only".
```

**P4** (Provider/vendor — no external memory provider) — append:
```markdown
  Phase 5 (`P5-D11`): to be revisited in Phase 6 as "local only". Not
  revised here.
```

**P2-D12** — append after the Phase 4 single-flight note:
```markdown
  Phase 5 (`P5-D01`): a closing follow-up window clears all of its own
  flags.
```

**P4-D28** — append after existing body:
```markdown
  Phase 5 (`P5-D08`): stands.
```

---

### B. `OPEN_QUESTIONS.md`

#### B.1 Remove S41 (resolved → DESIGN_DECISIONS Phase 5 / P5-D01)

Delete the entire `- **S41 — …**` bullet (through the source line).

#### B.2 Replace S42 body (keep heading; facts half resolved)

```markdown
- **S42 — Memory is not shared across sessions.** Developer-requested
  2026-10-01; Phase 5 scope. **Facts half resolved** by P5-MEMORY
  (`P5-D03`–`P5-D07`; save rate lasting 6/6, trivial 0/4, explicit 2/2;
  correction PASS). Principle **amended** (`P5-D06`): sessions never
  **automatically** read each other's transcripts — explicit
  `session_search` when asked is allowed; search results are not memory.
  **Open remainder:** episodes ("what did we decide…" without being
  asked), which moves to `S14` in Phase 6. Related: `S28`, `S43`.
```

#### B.3 Replace S36 body (feasibility gate)

```markdown
- **S36 — Bring back talk-over barge-in without breaking Phase 4.**
  **Feasibility gate: NO** (P5PRE AUD-14/15/16; `P5-D08`). Acceptance
  (all): (a) talk-over stops a long reply; (b) spoken clarify answer works
  with no "Interrupted"; (c) no `P2-D13` loop; (d) Track 1 gate still fails
  closed; (e) an instant answer given as soon as she stops speaking (before
  the beep) keeps its first word (needs ~1.2 s pre-roll; `voice.record`
  has none). Options matrix: O1 fails (b) and (e); O3 has no hook that
  passes without turning barge-in on; O4 fails (b); O5 conflicts with
  `P2-D01`; only upstream O2 (clarify-aware listener, discardable record
  stop, pre-roll on `voice.record`) can pass (a)/(b)/(e), and it is not on
  this pin. `voice.barge_in` stays `false` (`P4-D28`). Stays open,
  upstream-gated. Keep `P4-D13`/`D14`/`D15`/`D18`. Echo filter still only
  drops ≥3-word / ≥60% tail runs (A32).
```

#### B.4 Replace S38 body (measurements)

```markdown
- **S38 — Listen-to-think latency.** Measured in P5PRE / `P5-D09` (warm,
  after he stops talking): 1500 ms configured silence; 1562–1847 ms
  WAV → transcript (Whisper `base` + delivery), roughly flat across
  2.5–11 s clips; other stages under 15 ms. That is a substantial
  per-turn transcription component worth isolating later. No Phase 5
  tuning. Stays open.
```

#### B.5 Add to S35 (after existing body)

```markdown
  Observation (P5-WAKE smoke B3): a plain arithmetic question produced
  one approval card per math problem (developer: "she showed a card for
  each math problem for approval."). Inputs: which tool she used;
  whether harmless tools can be scoped out of manual approval without
  weakening `P4-D07`.
```

#### B.6 Add to S40 (after existing body)

```markdown
  Observation (P5-MEMORY cleanup): an "empty box while thinking" was
  seen once before she said "forgotten"; watch for recurrence.
```

#### B.7 New S43

```markdown
- **S43 — Time awareness in conversation.** She knows the current time,
  but not when each message or session happened, so "5 minutes ago" and
  "24 hours ago" look alike. Live evidence: the P5-MEMORY BR1 answer had
  no timing, although `session_search` results carry session start dates.
  Inputs: `Zola_Temporal_Reasoning_Architecture.md`, WINH12-02. Phase 6,
  with `S14`.
```

#### B.8 New S44

```markdown
- **S44 — No clarify card in Voice mode.** Developer, 2026-10-02. In
  Voice mode, clarify questions should be purely conversational: she
  asks, he answers out loud, and no card appears; the conversation panel
  is not forced open. Approvals keep cards (`P4-D07`, never by voice).
  Text mode keeps the clarify card (`P4-D08`). Touches `P4-D08` and
  `P4-D13`. Open: voice Cancel/Skip ("never mind", "skip", timeout);
  multi-select; batch `questions[]`; late-answer drop (`P4-D14`) tied
  today to card Cancel. Needs a short audit of card users before any
  build. Not Phase 5; with `S40` or in Phase 6 (developer's call).
```

#### B.9 Footer (replace current italic footer)

```markdown
*S13 and S16 remain open. S17, S21, S26 updated at Phase 4 lore closeout.
S20, S22, S32 resolved (see DESIGN_DECISIONS Phase 4). S41 resolved (see
DESIGN_DECISIONS Phase 5). S42 facts half resolved at Phase 5 lore
closeout; episodes remainder moves to S14. S33–S40 remain; S35, S36,
S38, and S40 updated at Phase 5 lore closeout. S43 and S44 added at
Phase 5 lore closeout. Not open questions (one line): question quiet
window withdrawn (B38); gap "no Stop" closed by P4-D29; AUD-37 closed by
P4-D18 (residual in S36); external dictation tool is test hygiene (A20).
Resolved items stay in DESIGN_DECISIONS.md.*
```

---

### C. `ROADMAP.md`

Replace `## Current stage — Phase 5 scoped` through its candidate list with:

```markdown
## Phase 5 complete
Phase 5 closed two tracks plus this lore pass. S41 fixed; S42 facts
carried across sessions; S36 deferred (feasibility gate NO); S38
measured (no tuning).

1. ✅ **AUDIT** — P5PRE, merge `c5be52e47ef8686d3643f5c57cf262cfd3991b8b`.
2. ✅ **DECISIONS LOCKED** — `P5-D01`–`P5-D11`.
3. ✅ **BUILD PLAN WRITTEN** — v1.1 commit
   `4c6c6439ec20e689a584d42b4c073920fb1afcd2`, merge
   `198fb00a28ea7036624ff44d0d3e58fa228e474a`; v1.2 commit
   `e2150607f24f9efa04098049dc0610f59d3c79bb`, merge
   `97dd29b40ae16d4b79aff436cfed08b35c2d18ca`.
4. ✅ **TRACKS EXECUTED** — two tracks.
5. ✅ **VERIFICATION / SMOKE TEST**
   - P5-WAKE B1–B8 PASS;
   - P5-MEMORY save rate PASS, routing ⚠️ 9/10, bridge timing ⚠️ (both
     developer-acknowledged).
6. ✅ **TRACK MERGED**
   - kickoff `41585cfdff5f00ee6845fe12753bad8390573ebd` /
     `9b2ca57f94d42ea5a4a7388c8fddb5d649b1d7b1`;
   - P5-WAKE impl `fdfe3bf255e7c0847a90f241d9e03e6293434727` / merge
     `d20fbe96fc4af4bf78d48b753b2e3acfa2615418`;
   - P5-MEMORY impl `9a0e45991d45a7e0d191db2e8df864399551bf48` / merge
     `569d0d0f24414b3493586237d8039ae2866f93e8`.
7. ✅ **LORE CLOSEOUT** — this pass.

One-line track results:
- **P5-WAKE** — wake after clarify answer; B1–B8 PASS; reconcile
  diagnostics.
- **P5-MEMORY** — lasting-fact saving + routing + explicit-only search;
  save rate PASS; routing ⚠️ 9/10; bridge timing ⚠️.

## Current stage — Phase 6 — Memory (not started)
Primary: `S14` (structured local memory: entity facts, episodes at
session end, relevance retrieval) + `S43` (time awareness). Starts with
its own audit. `P4` is to be revisited as "local only".
Then carry candidates forward (not a committed order):
- `S44`, `S35`, `S40`, `S38`;
- `S36` (upstream-gated);
- `S33`, `S34`, `S37`, `S39`, `S17`, `S21`, `S26`, `S28`;
- `S12`, `S13`, `S16`, `S24`, `S25`, `S31`.
```

## Discrepancies

1. **P1-D05 has no DESIGN_DECISIONS home.** Resolved at Phase 3/4 STOP: annotate **C4** (architect-approved). Applied.
2. **ROADMAP Phase 5 scoped block** blank-line density. Resolved in Phase 4 rewrite to "Phase 5 complete" (house style restored).
3. **OQ S36/S38/S42:** Phase 4 initially replaced bodies; architect corrected (update = add). Restored before closeout.

## Closeout SHAs

- Implementation commit: c2d738e5bf8cae2449f05711d33913244fd54587
- Merge SHA on main: 09e4f55d27a1d6bfb0a9baa0e5486e90c59f16c6
- Final main tip: *(this docs commit)*
