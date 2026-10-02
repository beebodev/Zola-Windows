# ZW Phase 5 Build Plan
## Wake After Questions, and Memory She Actually Keeps

**Base branch:** `main`
**Base SHA:** `9523422d7db3c208b66fb078bcbd4c8f1c8d3f30` (`main` tip after the P5PRE closeout).
Record the actual tip at plan commit. Each track records the actual HEAD it branches from.
**Audit:** P5PRE, merged at `c5be52e47ef8686d3643f5c57cf262cfd3991b8b` (audit commit
`5629bc2ba04bbfe7a12489946623249b243fba62`). Documents in `zola-architecture/audit/p5pre-phase5/`.
19 findings: 4 HIGH, 3 MEDIUM, 2 LOW, 10 MATCH.
**Theme:** Remediation, plus one behavior change. This phase:
- fixes the mic staying off after a spoken clarify answer (`S41`);
- makes Zola actually save lasting facts, so they carry across sessions (`S42`, facts half);
- lets her search past conversations when Brian explicitly asks about them (`S42`, episode bridge).

This phase does **not**:
- edit Hermes (`hermes-agent` stays read-only at `v2026.9.14` / `345cd2b0…`);
- install anything;
- add a memory provider, or build the structured memory store (`S14` is Phase 6);
- bring back barge-in (`S36`, feasibility gate NO);
- tune listen-to-think latency (`S38`, measure-only);
- add time awareness (`S43`, Phase 6).

---

## Phase 5 Overview

| Track | Name | Scope | Complexity |
|---|---|---|---|
| 1 (`P5-WAKE`) | Wake after a clarify answer | Each reply follow-up window starts with clean per-window state; reconcile diagnostics; `VoiceController.cs` only | Small |
| 2 (`P5-MEMORY`) | Memory she keeps | Live `SOUL.md` memory section (what to save, where, tags, brief mention, explicit-only conversation search); `user_char_limit` 2750 → 4000; mirrors in `identity/`; skills check; scripted save-rate test | Small-Medium |

**Sequencing rule:** strictly **1 → 2**. Track 1 merges before Track 2 begins, so Track 2's live
voice testing isn't affected by the S41 mic bug. Do not run the tracks in parallel.

**Build command (all tracks):** `dotnet build windows-client/Zola.Client/Zola.Client.csproj -r win-x64`.
**Test command (all tracks):** none. This project has no automated test suite. Smoke tests are the
acceptance criteria. Cursor does every non-interactive step; live steps run one at a time (as in
P5PRE G-LIVE). The external dictation tool must be confirmed off before any voice step.

---

## Grounding summary (established by P5PRE; cite, do not re-derive)

**S41**
- A bound clarify answer is routed to the open request. It does not start a turn (AUD-03,
  `MainWindow.OnTranscriptReady`).
- The per-window follow-up fields are cleared at turn start (`VoiceController.OnTurnStarted`, around
  L1564–1569) and when a clarify-answer window opens (`OpenClarifyAnswerCaptureAsync`, around
  L885–889). They are **not** cleared where a reply's follow-up window opens (`OnTurnCompleted`
  "complete" path, around L1648).
- After a clarify answer, `_followUpTranscriptSeen` stays `true`, and `_cancelReason` keeps
  `"voice.transcript"`. The reply's silent follow-up then skips `CancelFollowUp` (around L1873),
  `Resting` never returns, and `wake.resume` is never sent (AUD-01). This was reproduced live on L1
  try 2 and matches the 2026-10-01 09:58–09:59 log.
- `CancelFollowUp` (around L2117–2145) is the single place a follow-up window ends. It clears
  `_followUpArmed` and `_followUpCaptureStarted`, but not `_followUpTranscriptSeen`. Every
  non-empty transcript sets `seen = true` (around L1954) and then calls `CancelFollowUp` (around
  L1963).
- The **only** reader of `_followUpTranscriptSeen` is the idle check
  `_followUpCaptureStarted && !_followUpTranscriptSeen` (around L1873). The only reader of
  `_cancelReason` gates one timeline line in `CancelFollowUp` (around L2123).
- **P5-WAKE Phase 2 (v1.1 plan):** a clarify-answer capture can still be live when
  `OnTurnCompleted("complete")` runs. `MainWindow.OnRequestClosed` → `AbandonPendingQuestionIfId`
  clears the capture ids on a card Cancel or a timeout, without ending the capture. A reset at
  window open would clobber that live capture. That's why P5-D01 was revised in v1.2.
- Several `ReconcileWakeRestingAsync` exits are silent, and no line snapshots the `Resting` inputs
  (AUD-02).

**S42**
- Facts that are written do cross sessions. Each new session builds a new agent and re-reads
  `MEMORY.md` / `USER.md` (AUD-09; L2 B1 and C1 PASS with no `session_search`).
- She almost never writes: 2 memory-tool results across 93 sessions (AUD-07). The memory tool's own
  description (`tools/memory_tool.py` `MEMORY_SCHEMA`, in `hermes-agent`, not editable) says to save
  only facts that apply to every session. It sends work preferences to skills (`skill_manage`) and
  past events to `session_search`.
- The live store at audit time: `USER.md` 12 entries, 1938/2750 chars (70%); `MEMORY.md` 1 entry,
  234/4400. No entry uses the P1-MEMORY `[tag]` convention, which is not in the live `SOUL.md`
  (AUD-12).
- The writing agent's prompt snapshot stays frozen after a write (AUD-08, LOW). Same-session recall
  comes from the transcript. Not a Phase 5 concern.

---

## Decisions Resolved in This Build Plan

### Wake (Track 1)

**P5-D01 — A follow-up window that closes clears all of its own flags (revised in v1.2).**
`CancelFollowUp`, the single place a follow-up window ends, sets `_followUpTranscriptSeen = false`
together with the `_followUpArmed = false` and `_followUpCaptureStarted = false` it already sets. A
closed window then leaves nothing behind for the next one. That includes the reply window after a
clarify answer, which is not a new turn and so never reaches `OnTurnStarted`'s reset.

**Why this has no effect on the ordinary path:**
- The only reader of `seen` is the idle check, which also requires `_followUpCaptureStarted`.
- `CancelFollowUp` clears `started` in the same step, so the cleared `seen` is never read until a
  **new** window sets `started = true` again.
- That new window is exactly the case S41 needs fixed.

**Why this is safe with a live capture:** nothing runs when the reply window opens. A clarify
capture still live after a card Cancel or timeout (the v1.1 plan's Phase 2 finding) is never
touched. Its own idle or transcript ending runs the existing paths.

**v1.1 approach, superseded:** resetting five fields where the reply window opens
(`OnTurnCompleted`). P5-WAKE Phase 2 proved it could clobber a live clarify capture.

**Rejected alternatives:**
- clearing the flag in the clarify-answer routing (a caller-side patch that the next non-turn path
  would miss);
- letting the idle path always cancel (changes ordinary follow-up semantics);
- adding a second resume path (violates P2-D12);
- deferring window initialization until an orphaned capture ends (adds a second initialization
  moment for no gain over this fix).

Resolves `S41`.

**P5-D02 — Make wake reconcile observable.** Add the diagnostic lines P5PRE Audit 01 names:
- a one-line snapshot of every `Resting` input whenever `ReconcileWakeRestingAsync` returns without
  sending `wake.pause` / `wake.resume`;
- a line on each early return that is silent today (`!WakeArmed`, generation mismatch, `!Resting`
  inside `ResumeWakeAsync`, the converged-no-op return);
- `seen=` on the existing `follow_up_release` line;
- `_cancelReason = ""` at the point `OnTurnCompleted`'s "complete" path arms the reply window. This
  field only latches one timeline line per window. Left stale after a clarify answer, it would
  suppress the reply window's `fireOrCancel=` line. Clearing it can't affect a live capture, because
  nothing but that log line reads it.

These are logging changes only, with no behavior change. They let this fix, and any future stuck
pause, be confirmed from `voice-timeline.log` alone.

### Memory (Track 2)

**P5-D03 — She saves lasting facts, and her instructions override the tool's.**
A new section in the live `SOUL.md` (canonical copy `identity/SOUL.md`) tells her to save, without
being asked, facts that will still matter later:
- Brian himself;
- the people in his life;
- his projects and vehicles;
- standing preferences;
- decisions with lasting effect.

Not small talk, one-off task progress, or things easily looked up again. "Remember this" is always
saved. Changed facts replace the old entry instead of adding a duplicate.

The section says explicitly that it outranks general guidance to save less. That's needed because
the tool description, which can't be edited, pulls the other way.

When she saves something on her own, she mentions it in a few natural words ("I'll remember that.")
and carries on (developer choice, 2026-10-01).

Each entry starts with one lowercase `[tag]`, per P1-MEMORY.

**P5-D04 — Routing between the two files.**
- `user` (`USER.md`): Brian as a person: identity, preferences, the people in his life.
- `memory` (`MEMORY.md`): his world: projects, vehicles, decisions, conventions, how things are set
  up.

This uses `MEMORY.md`'s free space instead of filling `USER.md`.

**Tie-breaker:** a fact that plausibly fits both files (for example "I prefer ISR parts on my drift
cars") is stored **once**, in the file for what it is primarily about. It is never duplicated to
satisfy both. Avoiding duplicates matters more than perfect classification.

Existing entries are not edited by hand and not retro-tagged. She updates them naturally when they
come up.

**P5-D05 — Budget.** Live `config.yaml` `memory.user_char_limit` goes from 2750 to 4000.
`memory_char_limit` stays 4400. That's roughly 300 extra prompt tokens per turn at full use (an estimate; the real figure
depends on the content).

The block is mirrored in `identity/MEMORY_CONVENTIONS.md`, which already records the P1-MEMORY
budget. Revisit with fill data; that data is a Phase 6 (`S14`) input.

**P5-D06 — Episode bridge: search past conversations only when asked.**
When Brian asks about something from an earlier conversation ("what did we decide about…", "where
did we leave…") and it isn't in her notes, she uses `session_search` and says roughly when it was.
She does not search past conversations on her own for ordinary turns, and normal memory never
depends on it.

Search results are evidence for the current answer, **not** automatically memory. Nothing found by
`session_search` is saved just because it was found. If Brian confirms or corrects something
lasting in response, P5-D03 saves that new statement normally.

This amends the `S42` principle "sessions never read each other's transcripts" to "never
**automatically**". This is a bridge until Phase 6 episodes.

**P5-D07 — Proof is a scripted save-rate test, not a feel.**
In one session, Brian says 6 lasting facts and 4 trivial things, in natural conversation, with no
"remember". In a fresh session, Cursor reads the memory files and the tool calls.

Pass:
- at least 5 of 6 lasting facts saved;
- at most 1 of 4 trivial ones saved;
- 2 of 2 explicit "remember this" saved;
- a correction pair (a lasting fact, then later in the conversation "actually, I changed my mind…")
  leaves exactly one entry, holding the corrected value;
- each saved fact in the P5-D04 file with a `[tag]`, and no fact stored in both files;
- no budget rejection;
- the brief mention heard on each self-initiated save.

The bridge test passes when:
- an explicit question about a prior session's topic that's not in memory triggers `session_search`
  and gets a dated answer;
- no `session_search` runs on any other turn of the test.

**The test is blind.** The statements are said in natural conversation. Which are lasting, which
are trivial, and which form the correction pair is held by Brian and Cursor's script, and is never
said to Zola. Otherwise the test measures compliance with a test prompt, not her normal judgment.

**Record data, not just pass/fail.** The progress doc keeps one row per candidate statement:
expected, saved?, file, tag, self-initiated?, correct?. It also records `USER.md` and `MEMORY.md`
characters before and after the test. Those rows give Phase 6 its numbers: false-save and
missed-save rates, routing errors, correction behavior, characters per lasting fact, and projected
flat-file capacity.

Track 2 also starts with a read-only check of whether facts about Brian have gone into skill files
via `skill_manage` (AUD-07 follow-up).

Test facts are fictional but plausible. They are removed afterwards through Zola, with a semantic
restore check against a backup, as in P5PRE L2.

### Recorded, not built

**P5-D08 — S36 deferred by the feasibility gate.** No option passes acceptance criteria (a)–(e)
without editing `hermes-agent` (AUD-14/15/16).
- `voice.barge_in` stays `false`; P4-D28 stands.
- The only passing path is upstream (O2: a clarify-aware listener, a discardable record stop, and
  pre-roll on `voice.record`).
- The options matrix is recorded with `S36`.

**P5-D09 — S38 stays open, with its measurements.** Warm, after he stops talking:
- the 1500 ms configured silence;
- 1562–1847 ms WAV → transcript (Whisper `base` plus delivery), roughly flat across the five
  measured 2.5–11 s clips. That suggests a substantial per-turn component worth isolating later;
- everything else under 15 ms.

No Phase 5 track and no tuning.

**P5-D10 — Forget scope (supersedes C8's `MEMORY.md`-only scope).** "Forget" removes the entry
from whichever memory file holds it, `MEMORY.md` or `USER.md`.
Conversation history in `state.db`, including the stored system prompts, is not redacted. That's
the accepted v1 posture, now stated plainly.

**P5-D11 — Phase 6 is memory.** Its scope:
- `S14`: a structured local store with entity facts and episodes written at session end, retrieved
  by relevance per turn;
- new `S43`: time awareness, so she can tell "5 minutes ago" from "yesterday"; the turn and
  message timing she sees.

Phase 6 starts with its own audit, which also covers:
- `Zola_Temporal_Reasoning_Architecture.md`;
- WINH12-02;
- revisiting P4 as "no cloud or third-party memory provider; local only".

Phase 5 fill and save-rate data feed into it.

### Cross-cutting

Live-profile edits (`SOUL.md`, `config.yaml`) follow the P4-D25 pattern:
1. Back up first.
2. Propose the exact text at a STOP.
3. Apply only after developer approval.
4. Mirror into `identity/`.

Brian's verdicts are recorded in his own words.

---

## Track 1 — Wake After a Clarify Answer (`P5-WAKE`)

### Problem
After Brian answers a spoken clarify question by voice, the reply's follow-up window ends silently,
and wake is never resumed: HUD Idle, `MIC: OFF`, and "Hey Zola" does nothing until a Text↔Voice
toggle (P5PRE-AUD-01, L1 try 2; 2026-10-01 09:58–09:59 log). `CancelFollowUp` ends the answer
capture's window but leaves `_followUpTranscriptSeen = true`. A clarify answer starts no turn, so
`OnTurnStarted` never clears it, and the reply window inherits it. A stale `_cancelReason` also hides
that window's cancel line. The failure is invisible in the client log (AUD-02).

### Files to read
- `windows-client/Zola.Client/VoiceController.cs`. Focus on:
  - `OnTurnStarted` (~L1550–1580), `OnTurnCompleted` (~L1619–1660);
  - `OpenClarifyAnswerCaptureAsync` (~L848–900), `OnVoiceStatus` (~L1860–1890),
    `OnVoiceTranscript` (~L1920–1975);
  - `CancelFollowUp` (~L2117–2145), `ReconcileWakeRestingAsync` (~L2956–3031),
    `ResumeWakeAsync` (~L3072–3123);
  - `RunReplyFollowUpReleaseAsync` and the `follow_up_release` log line.
- `windows-client/Zola.Client/MainWindow.xaml.cs` (`OnTranscriptReady`, clarify wiring): read-only
  context.
- `zola-architecture/audit/p5pre-phase5/Zola_P5PRE_Audit_01_ClarifyWakeResume.md` and
  `Zola_P5PRE_Audit_05_LiveProbes.md` (L1).

### Changes

**`VoiceController.cs`:**
1. **`CancelFollowUp` (P5-D01):** add `_followUpTranscriptSeen = false;` beside the existing
   `_followUpCaptureStarted = false;` (~L2131). One comment:
   `// P5-WAKE: a closed window clears all its flags; a clarify answer starts no turn to reset seen — P5-D01`.
   **Pre-check (Phase 2 of the track prompt):**
   - confirm, by listing every read site, that the idle check is the only reader of
     `_followUpTranscriptSeen`, and that every path setting `_followUpCaptureStarted = true` is a
     new capture start;
   - confirm that `CancelFollowUp` is the only window-closing path that leaves `seen` stale.

   If any other reader exists, stop G-ARCH.
1b. **`OnTurnCompleted`, "complete" path (P5-D02, logging):** set `_cancelReason = "";` immediately
   before `_followUpArmed = true;` (~L1650). One comment:
   `// P5-WAKE: fresh window gets its own cancel log line — P5-D02`. Confirm in Phase 2 that its
   only reader is the timeline-line gate in `CancelFollowUp`.
2. **`ReconcileWakeRestingAsync` and `ResumeWakeAsync`:** add the P5-D02 diagnostic lines to
   `voice-timeline.log`:
   - a compact `Resting` input snapshot in one line (for example
     `wake reconcile noop reason=… mode=… avail=… session=… backend=… turn=… speaking=… capture=…
     armed=… started=… seen=… paused=… gated=…`);
   - one line per previously silent early return, naming the predicate.

   Use named constants for the log prefixes, matching the existing `Log…Prefix` style. Logging only;
   no behavior change.
3. **`follow_up_release` line:** append `seen=<bool>`.

No changes to `MainWindow.xaml.cs`, `ServerRequestBroker.cs`, `ZolaDisplayState.cs`, or any
Hermes RPC usage.

### Exit criteria
- [ ] After a spoken clarify answer and a silent reply follow-up, the log shows `follow-up-idle`
      (or another cancel) and `wake.resume reason=follow-up-end`. HUD is Idle with mic listening for
      "Hey Zola". A following "Hey Zola" produces `wake.detected`. (HUMAN-RUN, two different
      clarify prompts.)
- [ ] Regression, ordinary reply follow-up: silent ending resumes wake; spoken follow-up still
      submits a turn.
- [ ] Regression, clarify cancelled (Cancel on the card) and clarify answered by typing: mic returns
      to listening.
- [ ] Clarify **timeout** (no answer for `agent.clarify_timeout` 300 s): no capture is misread as a
      fresh window, the turn completes, and the mic returns to listening. This is the case most
      likely to expose the overlap risk.
- [ ] Regression, Stop speaking during a reply: no follow-up, and wake resumes (`P4-D29`).
- [ ] Regression, lock gate: locking during a follow-up refuses resume (`gate refuse:` line), and
      unlock restores wake (`P4-D02`).
- [ ] The new diagnostic lines appear in the L1 replay log. At least one `wake reconcile noop`
      snapshot is present.
- [ ] No other method's behavior changes. Diff is limited to `VoiceController.cs`.
- [ ] Build passes (0 warnings introduced).

**Complexity:** Small
**Primary risk:** An orphaned clarify capture is still live when the reply window arms, after a card
Cancel or a timeout. The fix itself doesn't touch it, but the existing late-drop and idle paths must
end it cleanly and still resume wake. Smoke steps B4 (Cancel during the answer capture) and B6
(timeout) are the proof. A failure there is pre-existing behavior to report, not to patch inside
this track.

---

## Track 2 — Memory She Keeps (`P5-MEMORY`)

### Problem
Saved facts already cross sessions, but she almost never saves (AUD-07). Her only guidance is the
Hermes memory tool's description, which says to keep memory minimal. `USER.md` is 70% full with no
routing rule. The `[tag]` convention never reached the live profile (AUD-12). Past conversations
have no sanctioned recall path.

### Files to read
- Live profile (`%LOCALAPPDATA%\hermes\profiles\zola\`): `SOUL.md`, `config.yaml` (`memory`
  section), `memories/` (counts, tags and sizes only; no entry text in any repo document),
  `skills/` (Phase 2 check).
- `zola-architecture/identity/SOUL.md`, `identity/MEMORY_CONVENTIONS.md`.
- `hermes-agent` (read-only): `tools/memory_tool.py` (`MEMORY_SCHEMA`, target narrowing),
  `tools/session_search_tool.py`, and the skill-writing tool (`tools/skill_manager_tool.py`).
- `zola-architecture/audit/p5pre-phase5/Zola_P5PRE_Audit_02_CrossSessionMemory.md`,
  `Zola_P5PRE_Audit_05_LiveProbes.md` (L2).

### Changes

**Phase 2 checks (read-only, before any edit):**
- Skills: list the profile's skills with their created/modified dates. Report whether any skill
  created or edited by Zola holds facts about Brian. Cursor may read skill content locally to
  classify it, but no personal fact text goes into the progress doc, lore or logs. Report only the
  skill name, dates, the count of personal facts, and the classification. If any does, it's a
  STOP item for the developer; nothing is moved in this track.
- Report the current memory fill (counts and chars) as the Phase 5 baseline.

**Live `SOUL.md`, a new section after "How I talk out loud":**
- Proposed as exact text at a STOP, backed up first, then applied (P4-D25 pattern), then mirrored
  verbatim into `identity/SOUL.md`.
- Starting draft below. Final wording is Brian's call at the STOP; keep the voice consistent with
  the rest of `SOUL.md`.

> ## What I remember
> I keep a small notebook that carries over between our conversations. When Brian tells me
> something that will still matter later — about him, the people in his life, his projects and
> cars, how he likes things done, or a decision we've made — I write it down with my memory tool,
> even if he didn't ask me to. I keep the notebook small and selective, but lasting facts about
> Brian and his world belong in it, his preferences included. They go in my notebook, not tucked
> away somewhere else. When he says "remember this," I always do. When I save something on my
> own, I mention it in a few words, like "I'll remember that," and keep going.
> Facts about Brian himself — who he is, what he prefers, the people in his life — go in his
> profile. Facts about his world — projects, vehicles, decisions, how things are set up — go in my
> notes. Each entry starts with one lowercase tag in square brackets, like [car] or [project],
> then the fact in a sentence. I don't save small talk, one-off task progress, or things I can
> easily look up again. When something changes, I update the old entry instead of adding a second
> one. If the notebook is full, I tighten or drop what's stale to make room.
> When Brian asks about something from an earlier conversation and it isn't in my notebook, I
> search our past conversations and tell him roughly when it was. I don't go through past
> conversations on my own.

**Live `config.yaml`:** `memory.user_char_limit: 4000` (from 2750). `memory_char_limit` stays 4400.
Backed up first, and applied only after STOP approval. The comment tag reads
`# P5-MEMORY: USER.md budget raised for lasting-fact saves — P5-D05`.

**`identity/MEMORY_CONVENTIONS.md`:** update the budget block to 4400/4000. Add the routing rule
(P5-D04), the brief-mention rule and the explicit-only search rule (P5-D03/D06) as short prose,
with one prose note citing P5-D03–D06.

No client source changes.

### Exit criteria
- [ ] Live `SOUL.md` contains the approved section verbatim, and `identity/SOUL.md` matches the live
      file byte for byte, apart from line endings.
- [ ] A fresh `MemoryStore` under the profile reports limits 4400 / 4000. `MEMORY_CONVENTIONS.md`
      matches.
- [ ] Save-rate test (HUMAN-RUN, P5-D07) passes:
  - at least 5 of 6 lasting facts saved;
  - at most 1 of 4 trivial ones saved;
  - 2 of 2 explicit "remember this" saved;
  - the correction pair leaves one entry with the corrected value;
  - routing correct, with no duplicates across the two files;
  - every new entry tagged;
  - no budget rejection;
  - brief mention heard on each self-initiated save (Brian's words recorded).
- [ ] Bridge test passes:
  - an explicit question about a prior session's topic triggers `session_search` with a dated
    answer;
  - zero `session_search` calls on the other test turns.
- [ ] Recall in a fresh session (no tools) for at least 3 of the saved test facts.
- [ ] The per-candidate table and the before/after character counts are recorded in the progress
      doc (P5-D07).
- [ ] Cleanup: test facts removed through Zola; semantic restore against the pre-test backup
      (byte-identical recorded if it holds). No hand edits to memory files.
- [ ] Skills check reported. No skill files changed by this track.
- [ ] `hermes-agent` clean at the pin. No client source changes.

**Complexity:** Small-Medium
**Primary risk:** The instruction conflict. The memory tool's own description (not editable) keeps
telling her to save little and to send preferences to skills. `SOUL.md` may win only some of the
time, so the save rate lands just short of the threshold. If the test fails, stop and report the
per-fact results. Don't loosen the threshold or add a second mechanism without a new decision.

**Pre-agreed fallback wording:** if the per-fact results show the tool description winning, propose
at a STOP adding this explicit priority sentence to the section, then rerun the test once:
"That's what my notebook is for, and it comes before any general guidance to save less."
Brian still approves the exact text.

---

## Phase 5 Lore Closeout

After both tracks are merged to `main`:

### DESIGN_DECISIONS.md
- Record P5-D01 through P5-D11 under "Phase 5 — Wake After Questions and Memory".
- Annotate:
  - `C8`: **superseded** by P5-D10 (forget covers both memory files; `state.db` is not redacted);
  - `P4-D28` (stands, per P5-D08);
  - `P2-D12` (window-state rule: a closing window clears all its flags, per P5-D01);
  - `P1-MEMORY` / `P1-D05` (budget 4400/4000; tags now in the live soul);
  - `P4` (to be revisited in Phase 6 as "local only", per P5-D11; not revised here).

### OPEN_QUESTIONS.md
- `S41`: RESOLVED by `P5-WAKE`. Note that the per-window reset happens where the window opens, and
  that reconcile diagnostics were added.
- `S42`: facts half RESOLVED by `P5-MEMORY` (the save-rate result). Amend the principle to "never
  automatically" (P5-D06). The episodes remainder moves to `S14` (Phase 6).
- `S36`: updated. Feasibility gate NO; options matrix summary; upstream O2 is the only path. Stays
  open.
- `S38`: updated with the P5PRE measurements (P5-D09). Stays open.
- `S14`: annotated as the Phase 6 primary, with the episodes requirement from `S42`.
- File **`S43` — Time awareness in conversation.** She knows the current time, but not when each
  message or session happened, so "5 minutes ago" and "24 hours ago" look alike. Inputs:
  `Zola_Temporal_Reasoning_Architecture.md`, WINH12-02, and session start dates in
  `session_search` results. Phase 6, with `S14`.
- If the skills check found facts filed in skills, file it as an `S14` input.

### ROADMAP.md
- Mark Phase 5 COMPLETE, with plan, track and merge SHAs.
- Restore the blank lines lost in the P5-KICKOFF stub (house style).
- Add a Phase 6 stub: **memory, `S14` + `S43`**, starting with its own audit. Carry the other
  candidates forward.

### identity/
- `SOUL.md` and `MEMORY_CONVENTIONS.md` were already updated by Track 2. Lore closeout only
  confirms they match the live profile.

---

## Phase 5 Exit Checklist
- [ ] Track 1 (`P5-WAKE`) merged. The S41 replay resumes wake and "Hey Zola" works; all four
      regressions pass.
- [ ] Track 2 (`P5-MEMORY`) merged. The save-rate and bridge tests pass; live profile and
      `identity/` match.
- [ ] No `hermes-agent` edits; `git status` clean at `345cd2b0…` after each track.
- [ ] No installs. No new config keys beyond `memory.user_char_limit`.
- [ ] New log prefixes are named constants; no magic strings.
- [ ] Build passes on `main` after both merges.
- [ ] Smoke test after each track boundary.
- [ ] `DESIGN_DECISIONS.md`: P5-D01–D11 recorded, with annotations.
- [ ] `OPEN_QUESTIONS.md`: S41 resolved; S42 facts resolved and the principle amended;
      S36/S38/S14 updated; S43 filed.
- [ ] `ROADMAP.md`: Phase 5 COMPLETE; Phase 6 stub added.

---

## What Phase 5 Explicitly Defers

| Item | Reason | When |
|---|---|---|
| `S14` structured memory: entity facts, episodes at session end, relevance retrieval | The biggest architecture piece in the project; needs its own audit and design; waits on Phase 5 usage data | Phase 6 (primary) |
| `S43` time awareness | Belongs with episode design; needs an audit | Phase 6 |
| P4 revision to "local only" | Only needed if Phase 6 chooses a provider | Phase 6 decisions |
| Snapshot refresh on write (AUD-08) | Needs a `hermes-agent` edit; not the cross-session cause | Upstream, or not at all |
| `S36` barge-in | Feasibility gate NO on this pin | When upstream O2 exists |
| `S38` latency tuning (silence, Whisper device, compute type, model) | Measure-only this phase | Future track |
| Retro-tagging or editing existing memory entries | No hand edits to memory files; she updates entries naturally | Not planned |
| `SOUL.md`'s line "I operate through a text-based Windows client" is outdated | Not memory scope; identity wording is the developer's call | Developer decision, any time |
| `S33`, `S34`, `S35`, `S37`, `S39`, `S40`, `S17`, `S21`, `S26`, `S12`, `S13`, `S16`, `S24`, `S25`, `S28`, `S31` | Not in Phase 5 scope | Later phases |

---

## Complexity Legend

| Track | Complexity | Primary Risk |
|---|---|---|
| 1 — `P5-WAKE` | Small | The reset clobbers a clarify capture still open at turn completion (clarify timeout) |
| 2 — `P5-MEMORY` | Small-Medium | `SOUL.md` loses to the uneditable tool description some of the time, and the save rate misses the threshold |

---

*Phase 5 Build Plan version 1.2 (v1.2: P5-D01 revised. The window close (`CancelFollowUp`) clears `seen`, after P5-WAKE Phase 2 found that a window-open reset could clobber a live clarify capture; `_cancelReason` moves to P5-D02 logging. v1.1: ChatGPT review: atomic window init, clarify-timeout smoke, identity-voiced save wording with a fallback, correction pair, routing tie-breaker, search ≠ memory, blind test with per-candidate data, D09 wording, D10 supersedes C8, skills privacy)*
*Created 2026-10-01*
*Base SHA: `9523422d7db3c208b66fb078bcbd4c8f1c8d3f30` (record the actual tip at plan commit)*
*Prerequisite audit: P5PRE — merge `c5be52e47ef8686d3643f5c57cf262cfd3991b8b`*
*All Phase 5 decisions locked before plan was written (developer approval 2026-10-01).*
*Next step: commit this build plan to `zola-architecture/lore/build-plans/` on `main`, then begin
Track 1 (`P5-WAKE`).*
