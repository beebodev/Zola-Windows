# P7-LORE Progress — Phase 7 Lore Closeout

## Branch

- Work branch: `p7-lore`
- Base `main` HEAD: `9f9999d816deb520edd30b0a369eba772ca4f726` (P7-LATENCY closeout tip) — **matched**
- Prompt: `P7-LORE_Prompt_v1.0.md` (canonical: `C:\Users\test\Dev\zola-spikes\prompts\P7-LORE_Prompt_v1.0.md`)
- Prompt SHA-256 (on-disk, 14,031 bytes): `F218DDC67E5AFFFB6D64F7521EF0F5E8DED88ED00B0A3E4EEF3E70D7D3C65B84`
  - Developer-supplied comparison SHA: **not included** in the Phase 1 instruction message; on-disk value recorded for Brian to confirm
- Snapshot: `PHASE7_DECISIONS_snapshot.md` (canonical: `C:\Users\test\Dev\zola-spikes\prompts\PHASE7_DECISIONS_snapshot.md`)
- Snapshot SHA-256 (on-disk, 23,083 bytes): `FFF4F614D8078F60F1D6903709D9CAF8DEDAA2CEB98E00FBBEE836D2E3E547CF`
  - Developer-supplied comparison SHA: **not included** in the Phase 1 instruction message; on-disk value recorded for Brian to confirm
- Build plan: `PHASE7_BUILD_PLAN.md` v1.1 on `main`
- Hermes HEAD: `345cd2b057a452236de401d3534b8502a7465e8d` (`v2026.9.14`); `git status --porcelain` empty

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Branch, inputs, inventory | COMPLETE (STOP) |
| 2 | Draft DESIGN_DECISIONS.md | COMPLETE — Brian (verbatim): "approved" |
| 3 | Draft OPEN_QUESTIONS.md | COMPLETE — Brian (verbatim): "approved" |
| 4 | Draft ROADMAP.md | COMPLETE — Brian (verbatim): "approved" |
| 5 | Identity and deploy verification | COMPLETE (STOP) |
| 6 | Apply, verify, STOP | COMPLETE |
| 7 | Commit and merge | COMPLETE |

## Guardrails summary

- **G-LORE-ONLY:** `DESIGN_DECISIONS.md`, `OPEN_QUESTIONS.md`, `ROADMAP.md`, this progress doc; `identity/` only if Phase 5 mismatch + Brian approves. No code/plugin/config/live edits.
- **G-VERDICTS:** quote snapshot / progress verbatim.
- **G-HONEST:** Track 3 causal ❌; Track 1 S1 PARTIAL (+ S1b); Track 2 C3 adapted; serve-crash unresolved.
- **G-PRIVACY / G-DECISION-ID / G-RESOLVED / G-STOP:** as prompt.

## Phase 1 inventory

### Ancestors of `main` HEAD `9f9999d8…`

| Item | Full SHA | Ancestor of main? |
|---|---|---|
| Plan commit | `b5583f97c3e13870abc5d483ec23566458cd828e` | YES |
| Plan merge | `ffef6f050a3fd6a8092d77fc055370296e2b522b` | YES |
| P7-VOICEAUTH merge | `3d264f07bb026c499c1fa8d82cce6dc71892f4e2` | YES |
| P7-FORENSIC-SERVE merge | `512d91490be6317e6f644afc8051160b7cb560ef` | YES |
| P7-CLARIFY merge | `80498b99f0e999efd91250fcc1c1d9315616bbb9` | YES |
| P7-LATENCY merge | `7b168cfbb4daa95f5fa58307fd2377176f9ffd35` | YES |

### Current lore structure (where Phase 7 goes)

**`DESIGN_DECISIONS.md`:** top-level sections through **Phase 6 — Memory She Lives With** (+ Known limits / Background-review skills / execution notes). **Phase 7** entries go as a new top-level section **after Phase 6**, same pattern as prior phases (“Phase 7 — Voice She Can Trust”).

**`OPEN_QUESTIONS.md`:** single body section **Research needed…**; OQs are `Snn` bullets in one stream. Status changes edit those bullets in place; **new OQs continue after highest existing S-number.**

**Highest existing S-number:** **S50** → new OQs start at **S51** (snapshot’s proposed S51/S52 keep those numbers; no collision).

**`ROADMAP.md`:** Phases 1–6 complete; **Current stage — Phase 7**. Replace/update that with **Phase 7 — COMPLETE** and a **Phase 8 stub**.

### Scratch folders under `zola-spikes\`

- **No `p7-*` folders remain** (confirmed).
- Older folders **out of scope** (not touched): `p3pre-helix`, `p4pre-voice`, `p5-lore`, `p5-memory`, `p5pre`, `p6-calc`, `p6-episodes`, `p6-fix-2`, `p6-fix-when`, `p6-forget`, `p6-store`, `p6-time`, plus `prompts\`.

## Phase 1 STOP

Inputs verified (on-disk SHAs recorded; confirm against developer-supplied if provided). Branch `p7-lore` created. Inventory complete.

---

## Phase 2 — Draft DESIGN_DECISIONS (not applied)

> Lore files are **not** edited until Phase 6 (after Phases 3–5 and Brian approval). Draft only.

### 1. G-DECISION-ID classification

| Item | Classification | One-line reason |
|---|---|---|
| Phase 7 invariant (ambiguous fails closed) | **stated under Phase 7 header** (not a new D-ID) | Governs P7-D01–D08; locked with the set |
| P7-D01…D13 (Appendix A / snapshot) | **keep IDs** | Locked 2026-10-05; durable authority / clarify / latency / track-order rules |
| Brian full-set: "approved." / S34: "Yes. keep S34" | **quoted under Phase 7 header** | Verdicts on the locked set |
| `CaptureLifecycle` + `TranscriptAdmission` + Checks | **note under P7-D01 / P7-D03** | Implementation of the admission authority |
| Frozen Hermes terminal set | **note under P7-D03** | Track 1 grounding; future phases must obey |
| Cancel mechanism A (`voice.record stop`) | **note under P7-D02** | Mechanism choice; decision already names stop |
| Clarify close → cancel bound capture | **note under P7-D02** (Track 2) | Same cancel method; not a new authority rule |
| Quiet card (Brian: "Quiet card (Recommended)") | **note under P7-D09** | Supersedes locked "no card" + plan "do not build or show the card"; panel auto-open still off |
| Spoken template / 20-word cap / Recommended drop / stem haystack / panel-once / typed Voice-only | **note under P7-D05 / P7-D09** | Track 2 mechanisms under locked D05/D09 |
| D06 hand-back + S37 smoke counts | **note under P7-D06** | Mechanism + measured acceptance |
| `turn_timing` observation-only | **note under P7-D10** | Instrumentation, not a product rule |
| Track 3 closed on findings; UTC offset kept; SOUL Everyday applied then reverted | **note under P7-D10** (+ **P6-D05** annotation) | Outcomes / fix attempts; causal ❌ acknowledged |
| Track 4 cut | **note under P7-D12** | Cut outcome; P4-D20/P4-D24 unchanged |
| P4-D27 = dangerous-pattern only (C7) | **annotation on P4-D27** | Clarifies existing decision; not a new ID |
| Annotations on P2-D05/D12/D14, P4-D13/D14/D18/D20/D24 | **annotations on earlier IDs** | Build-plan closeout requirement |
| Known limits (no capture ID, STT race, serve crash, composer-in-panel, execution_guidance, Edge/S-tts, flush, AUD-26) | **known limits** | Honest residual; OQs in Phase 3 |
| Process lessons (Claude probes, S1→S1b, G-CRASH, prompt-layer check, stage SHAs) | **process lesson** | Execution hygiene |

### 2. In-place annotations (exact text as it will appear; apply with Phase 6)

Each line is appended under the named bullet in `DESIGN_DECISIONS.md` (same indent style as existing Phase 4/6 annotations).

**P2-D05** — after the existing Phase 4 (`P4-D14`) line:
```
  Phase 7: **revised by P7-D02** (a transcript from a cancelled capture is dropped).
```

**P2-D12** — after the body ending "the client submits once and never holds." (before "Phase 1 client defects…"):
```
  Phase 7: **revised by P7-D04** (no mid-turn unbound voice submits; one admission authority, P7-D01).
```

**P2-D14** — after the final end-anchored rule paragraph (under "Decisions added during execution"):
```
  Phase 7: unchanged; defense only (P7-D07).
```

**P4-D13** — after the Question quiet window / withdrawn sentence:
```
  Phase 7: **revised by P7-D09** (choices spoken; quiet card for a single question in Voice mode — card built, panel never auto-opens).
```

**P4-D14** — after the Binding clear / closed-clarify sentence:
```
  Phase 7: **revised in part by P7-D05** (no newest-clarify fallback; only the bound clarify capture answers).
```

**P4-D18** — after the Quiet window required (F1) sentence:
```
  Phase 7: preserved; the monitor outranks the estimate (P7-D06).
```

**P4-D20** — after "Do not copy the full text here.":
```
  Phase 7: unchanged (Track 4 cut).
```

**P4-D24** — after "Filed as `S34`.":
```
  Phase 7: unchanged (Track 4 cut).
```

**P4-D27** — after the existing "Phase 6: stand (P6-D08)." line:
```
  Phase 7: `approvals.mode: manual` means **dangerous-pattern approval only**, not approve-all (P7-CLARIFY C7: Hermes `approval.py` 1093–1124, `approval_detection.py` 227; `Remove-Item -Force` raised the card).
```

**P6-D05** — after the Same-day recall may still omit "when" sentence:
```
  Phase 7 (P7-LATENCY): stamp gains an explicit UTC offset parenthetical, e.g. `[Time: Tue Oct 6, 6:47 PM PDT (UTC−07:00)]` (`time_context.py` `327A027A…`).
```

### 3. New section — insert after Phase 6 execution notes (revised draft)

**Restored vs prior draft (Appendix A verbatim check):**
- **P7-D09:** restored locked **"with no card and no automatic panel opening"** (prior draft had dropped "with no card").
- **P7-D01–D08, D10–D13:** restored full Appendix A paragraphs (Why / Future / Evidence / Acceptance / Revises quotes / Candidates / LIVE-PROBE tag / paraphrase-false / skip-or-never-mind / "since Brian said nothing" / wake-mic-hotkey / grounding-enumerate / stage-timing list) that the condensed draft had shortened. Locked bodies below are Appendix A exact; notes follow separately.

```markdown
## Phase 7 — Voice She Can Trust
Recorded from `PHASE7_BUILD_PLAN.md` v1.1 (`P7-D01`–`P7-D13`, Appendix A),
the P7PRE audit (merge `3e87e7c47ed2eee4a26f53dc9c4bba7d6f16b1ee`), the
working decisions snapshot (`PHASE7_DECISIONS_snapshot.md`), and the
progress docs `P7-VOICEAUTH`, `P7-FORENSIC-SERVE_Findings`, `P7-CLARIFY`,
`P7-LATENCY`. Full locked wording stays in Appendix A / the snapshot;
this section is the lore pointer, track amendments, and measured limits.

**Brian's verdicts (verbatim, 2026-10-05):** On the full decision set,
including the revisions to P2-D05, P2-D12, P4-D13 and P4-D14: "approved."
On S34: "Yes. keep S34"

### The Phase 7 invariant
A voice transcript is not Brian merely because Hermes transcribed microphone
audio. The Windows client admits it as Brian only when the current conversational and capture state
authorizes that input. Cancelled, stale, unbound or state-incompatible transcripts fail closed and
are never replayed later. Content similarity to Zola is a secondary defense only.

**How it is applied (v1.1).** A transcript becomes Brian's
input only when the client can **prove** it came from a currently authorized capture opportunity.
The absence of contrary evidence is not proof. **Ambiguous** transcripts fail closed, alongside
cancelled, stale, unbound and state-incompatible ones. Ambiguity is the core risk, because Hermes
supplies no capture ID. Dropped transcripts are logged with reason and length (never text). The
echo matcher may reject; it may never admit.

- **P7-D01 — One transcript-admission authority.** **As locked.**
  `VoiceController` is the single authority that decides whether a transcript is Brian's input. A
  transcript is admitted only when the current capture state authorizes it. Content resemblance to
  Zola can reject a transcript; it can never admit one. The check order is: capture ownership and
  lifecycle → turn state and clarify binding → content echo check (reject-only, including clarify
  answers).
  - Evidence: AUD-08, Audit 01 §10–11.
  **Brian's verdict:** "approved."
  **Implementation:** pure `CaptureLifecycle` + `TranscriptAdmission`
  (`Voice/CaptureLifecycle.cs`, `Voice/TranscriptAdmission.cs`);
  `TranscriptAdmission.Decide` is the only admission site
  (`VoiceController.OnVoiceTranscript`, snapshot before `ApplyTranscript`).
  Dependency-free `Zola.Client.Checks` project (lifecycle / admission /
  latch / wiring tables). MainWindow never re-decides admission.

- **P7-D02 — Cancel invalidates, then stops (revises P2-D05).** **As locked.**
  Every intentional client cancellation invalidates the current capture generation **before**
  Hermes is told to stop. `CancelFollowUp` and every other cancel path that can leave Hermes
  recording (typed submit, Stop speaking, mode change, session ready) issue `voice.record stop`. The
  forced transcript from that stop belongs to the cancelled generation and is inadmissible.
  - **Revises P2-D05** ("every voice transcript is sent immediately"): a transcript from a cancelled
    capture is dropped.
  - Evidence: AUD-01, AUD-02, AUD-09, L-3.
  **Brian's verdict:** "approved."
  **Implementation:** cancel mechanism **A** (`voice.record stop`; forced
  transcript dropped). One cancel method (`InvalidateCapture` +
  `SendRecordStopAsync`). Track 2: closing a clarify request (typed,
  click, skip, timeout) cancels its bound capture through that same method.

- **P7-D03 — One capture at a time, with a proven end.** **As locked.**
  Only one client-owned capture may be outstanding. A new capture cannot accept speech until the
  previous client-owned capture has reached a **proven terminal Hermes state**. The VOICEAUTH track's
  grounding step enumerates every Hermes event or state that can settle a client-started capture,
  proves whether a text transcript can still arrive after each one, and then freezes the terminal
  set. "Idle" is not assumed terminal until proven. A transcript received with no accepting capture
  owner is dropped. A bounded recovery timeout may clear a stuck lifecycle, but it never
  retroactively admits a transcript.
  - Why: with no capture ID, "drop the next transcript after a stop" can drop Brian's real speech if
    the cancelled capture had already ended on silence.
  - Future (upstream, not Phase 7): a Hermes-issued capture correlation ID.
  - Evidence: 5.1a, AUD-23.
  **Brian's verdict:** "approved."
  **Frozen Hermes terminal set (Track 1 grounding):** transcript text /
  `stop_phrase` / `no_speech_limit` settle admission; `idle` is required
  before the next Accepting. Grounding: `listening` is emitted only by a
  genuine `start_continuous` start, so it proves a fresh capture;
  `start_continuous` is a no-op when already active. No
  `LateTranscriptGuardSeconds`. Recovery never admits.
  **Lifecycle constants:** `StartListeningTimeoutSeconds = 3` (no
  `listening` after our start → `start_no_listening`, cancel A, wait
  idle, then start-policy); `CaptureSettleTimeoutSeconds = 180`
  (Starting/Accepting settle backstop); `CancelSettleTimeoutSeconds = 30`
  (Cancelled after stop sent settles faster); `LatchIdleTimeoutSeconds =
  65` (Hermes longest TTS wait 60 s + margin; clears stuck
  `HermesBusyUntilIdle` with no outstanding capture); `HermesBusyUntilIdle`
  latch (set on `listening`, cleared on `idle`; no new Accepting while
  held). **Pending-start policy:** Wake/Manual **reject**; FollowUp /
  EchoReopen **defer** 5 s (`PendingStartExpirySeconds`); Clarify
  **supersede** outstanding then **defer** 15 s
  (`ClarifyPendingStartExpirySeconds`). The 65 s / 30 s timeouts fixed the
  stuck-latch deafness path found in review.

- **P7-D04 — No unbound transcripts during a running turn (revises P2-D12).** **As locked.**
  During `TurnRunning`, an ordinary unbound transcript is inadmissible. It is dropped, never held or
  replayed. No genuine input is lost: with `voice.barge_in: false`, Brian cannot start a capture
  during a turn (wake requires Resting, and the mic button and hotkey require `!TurnRunning`).
  - **Revises P2-D12** ("running-turn `prompt.submit` is accepted; the client submits once and never
    holds"): mid-turn voice submits stop. Typed submits are unchanged.
  - Evidence: AUD-05, E2.
  **Brian's verdict:** "approved."

- **P7-D05 — Only the bound clarify capture answers a clarify (revises P4-D14 in part).** **As locked.**
  A transcript may answer a clarify only if it comes from the active clarify-answer capture bound to
  that request. The fallback that lets an unbound transcript answer the newest open clarify is
  removed. Typed answers through the composer (P4-D09) are unchanged.
  - Evidence: AUD-12, Audit 03.
  **Brian's verdict:** "approved."
  **Track 2 notes:** echo haystack for clarify is the **question stem
  only** (CL-G5: 0/90 vs 3/90 false drops). Typed fill-then-send for a
  single question in **Voice mode only** (Brian: "Voice mode only
  (Recommended)"); Text mode unchanged.

- **P7-D06 — The playback monitor outranks the estimate.** **As locked.**
  A fallback or estimate release cannot create an accepting capture while the playback monitor
  reports Zola still speaking. Monitor-driven release remains authoritative and unchanged (P4-D18
  preserved). **S37 closes into this decision.** Acceptance: if an estimate release fires while she
  is still audible, her speech cannot become admitted Brian input.
  - Why: A + B alone miss this case. The turn is already complete (`TurnRunning` false) while her
    audio continues, so a fallback capture would otherwise be a current, owned capture.
  - Evidence: AUD-20, AUD-21, Audit 05 §7.
  **Brian's verdict:** "approved."
  **Implementation (D06 hand-back):** when release rule is estimate /
  forced-estimate / no-bout-estimate (or estimate branch of question
  release), the hand-back applies only when the monitor is available and
  reports an active bout — then do not open capture; hand back to monitor
  bout-stop + quiet rule (`D06HandbackMaxSeconds = 120`; timeout → no
  capture). Monitor unavailable → today's estimate behavior unchanged.
  Smoke S1–S8: **1** `no_bout_estimate` (S8), **0** `forced_estimate`,
  **1** `question_release rule=monitor` (S5); estimate did not open
  capture during bout. Audit context: 196/205 releases were monitor-driven
  (AUD-21).

- **P7-D07 — The echo matcher is defense-in-depth only.** **As locked.**
  `IsEchoOfLastReply` stays as is: end-anchored, follow-up and clarify captures, P2-D14 unchanged. It
  can reject only. No un-anchoring in Phase 7 (H-2: quote false positives).
  **Brian's verdict:** "approved."

- **P7-D08 — Drops are logged, not announced.** **As locked.**
  Every dropped transcript gets a log line with the reason and length (never text). No on-screen
  notice, since Brian said nothing. The capture-window bookkeeping is fixed so log lines describe the
  capture that produced the transcript (AUD-23).
  **Brian's verdict:** "approved."

- **P7-D09 — Clarify in Voice mode (revises P4-D13).** **As locked.**
  In Voice mode, a **single** clarify question is asked conversationally, with no card and no
  automatic panel opening. If it has choices, she speaks the choices (**revises the P4-D13
  amendment** "question only, never the choice list"). Batch (`questions[]`) and multi-select keep
  the visual card in Phase 7. Exact "stop" keeps its current meaning; no new command words ("skip" or
  "never mind" reach her as ordinary answers). Text-mode clarify is unchanged (P4-D08, P4-D09).
  Approvals stay visual and manual (P4-D07, P4-D27).
  - Depends on P7-D01–D06: the answer capture must be Brian-only.
  - Evidence: AUD-12–15, AUD-24, Audit 03.
  **Brian's verdict:** "approved."
  **Quiet card (Brian, 2026-10-06, verbatim selection):** "Quiet card
  (Recommended)". Brian's selection supersedes the locked "no card"
  wording (and the build plan's "do not build or show the card"), while
  "no automatic panel opening" stands. Hermes wires every clarify as
  `questions[]` (`IsBatch=true` even for one); voice and typed paths fill
  card rows. Single-question card is still built in the conversation, but
  the panel never auto-opens for it (not on open, not on collapse).
  **Spoken choices (Brian Phase 3 selections, verbatim):** "(Recommended)"
  when spoken: "Drop it (Recommended)" (card may still show it). Typed
  scope: "Voice mode only (Recommended)". Long choices: "Cap → show card
  (Recommended)" (`SpokenChoicesMaxWords = 20`). Template:
  `"{q} Is it A, B, or C?"` (skipped when the question already names every
  choice, whole-word match). No admitted answer → panel opens once
  (silence, gate, Stop, clarify-echo; echo-reopen refused while awaiting).

- **P7-D10 — Latency is measure → STOP → fix → measure again.** **As locked.**
  First add the missing stage timing: `prompt.submit` → first model token → first speakable sentence
  → Edge synthesis start and end → playback; Whisper infer start and end (AUD-26); and
  within-utterance pause lengths (for a future silence decision). Investigate unnecessary tool use on
  simple questions first (AUD-25). At the STOP, choose and implement the largest proven, safely
  addressable cause within Phase 7, then measure again. No changes to the Whisper model, beam size or
  silence duration without new evidence.
  - Candidates noted (not chosen): `SOUL.md` guidance to answer common knowledge and conversions
    directly; extending the bounded `calculate` tool to unit conversion.
  **Brian's verdict:** "approved."
  **Instrumentation:** one `turn_timing` line per turn; pure `TurnTiming`
  (mirrors Hermes `SentenceChunker`); `VoiceController` sole owner;
  observation only (never drives decisions).
  **Track 3 outcome — closed on findings (causal target not met).**
  Baseline EoS→first audio median 9534 ms; additive median shares
  S-model 51.4%, pre-submit 31.3%, S-tts (Edge) 19.3% (≈2.0 s),
  S-sentence 4.3%, S-play 1.5%; 6/8 replies spoken only on end-of-stream
  flush. Tool vs no-tool submit→first audio 17.8 s vs 5.4 s. AUD-26 =
  in-call (standalone ≈1.0 s, live ≈1.6 s). Pause median 120 ms, max
  1360 ms < 1500 ms silence. **AUD-25 root cause:** Hermes
  `OPENAI_MODEL_EXECUTION_GUIDANCE` / `agent.execution_guidance`
  outranks `SOUL.md` (time/date → terminal; arithmetic → terminal;
  reinforced by everyday-assistance MUST-`skill_view`). Phase 4 Brian:
  "Narrow SOUL + UTC offset (Recommended)", "Keep calculate
  (Recommended)". Phase 5: "Approved, with Claude's one edit to the
  SOUL.md draft." Diagnosis: "C: close on findings (Recommended)",
  "Revert it (Recommended)". Kept: UTC offset in the time stamp. Reverted:
  SOUL "Everyday answers" (`E3D7BF9A…`). Brian on the wait: "The wait
  still feels the same."

- **P7-D11 — No memory cleanup.** **As locked.**
  The 10 probe pending rows (7 tagged `LIVE-PROBE-CONTAMINATION`) were consolidated into nothing,
  with zero episodes. E1 and E2 stay in `state.db` as conversation history and forensic evidence
  (P5-D10).
  **Brian's verdict:** "approved."

- **P7-D12 — voice-live is checked before it is adopted.** **As locked.**
  Track 4 starts by capturing the exact `voice_live_turn_note` at `345cd2b0` and evaluating every
  instruction against Zola's chained Edge setup. Phase 4 found it says a voice model "paraphrases"
  her text, which is false for Edge. Adoption, editing or rejection is decided at a STOP. Sentence
  streaming stays; no whole-line synthesis. Last track, explicitly cuttable.
  **Brian (2026-10-05):** "Yes. keep S34"
  **Track 4 cut (Brian, 2026-10-07, verbatim):** "Cut it; go to lore
  closeout (Recommended)". Reasons: S-sentence ≈4% of the wait; prose
  shaping depends on the Phase 8 voice-pipeline choice (streaming TTS);
  the voice-live note's Edge "paraphrase" claim is false. Inputs carried
  forward: voice-live evaluation, short-first-sentence idea, one-sentence
  end-of-stream flush (6/8 baseline), Brian's speech-lags-text
  observation. **P4-D20 and P4-D24 unchanged.**

- **P7-D13 — Track order.** **As locked.**
  VOICEAUTH (S45 + S37) → CLARIFY (S44) → LATENCY (S38) → VOICEPROSE (S34). A Hermes capture
  correlation ID is filed as a future upstream improvement.
  **Brian's verdict:** "approved."
  FORENSIC-SERVE ran after Track 1 (read-only); Tracks 2–3 followed;
  Track 4 cut.

### Known limits
- **No Hermes capture ID** on `voice.transcript` / status terminals
  (upstream; client generation + lifecycle is the ownership model).
- **Stop-vs-silence-STT race** and **native serve APPCRASH** class
  (`0xc0000005`; filed; Brian: "Let's file both the hotfix and the crash
  issue and prioritize for a future phase."). Unresolved in Phase 7.
- **Composer lives inside the conversation panel** — typed clarify in
  Voice mode needs the panel open (C3 adapted).
- **Hermes `execution_guidance` outranks `SOUL.md`** for time and math
  tool use (Track 3 causal ❌).
- **Edge has no streaming TTS** — about 2.0 s of synthesis per first
  sentence (S-tts median ≈2004 ms).
- **One-sentence replies** are spoken only after the full stream
  (end-of-stream flush; 6/8 baseline).
- **AUD-26 live residual:** standalone warm STT ≈1.0 s vs live ≈1.6 s
  (in-call; not a config-key fix).

### Process lessons
- Claude's independent probes caught critical wiring bugs before deploy
  (a released start never sent; a stuck-latch deafness path).
- Add a live test for the exact original failure path when a smoke step
  only exercises an easier variant (S1 → S1b).
- Backend crashes during smoke are recorded and repeated, not treated as
  failures (G-CRASH).
- Verify which prompt layer controls a behavior before trying to change
  it with `SOUL.md` (Track 3).
- Stage files under unique paths and read back their SHAs.

### Phase 7 execution notes
- Frozen terminal set and cancel mechanism A are binding for any later
  voice-admission work.
- Quiet card is the Phase 7 reading of P7-D09; Brian's later direction
  ("only time a card is necessary is when in text mode") is a Phase 8 OQ,
  not a Phase 7 revision.
- Track 3 "Complete" on the roadmap means the planned measure→fix→remeasure
  shipped and closed on findings — not that latency is solved.
- S45 RESOLVED by P7-VOICEAUTH (P7-D01–D08): the orphan capture that turned
  her speech into Brian's turn is closed by the admission authority,
  cancel-before-stop, serialized captures, no unbound mid-turn transcripts
  and the D06 hand-back. Smoke S1–S8 plus S1b (S1 PARTIAL at Starting; the
  Accepting → forced-transcript drop proven live in S1b). S37 RESOLVED,
  closed into P7-D06.
```

### Phase 2 STOP (revised)

Classification approved (no new IDs). Four draft fixes applied in progress doc; `DESIGN_DECISIONS.md` still unmodified.

**Brian (verbatim, Phase 2 approval):** "approved"

---

## Phase 3 — Draft OPEN_QUESTIONS (not applied)

> Lore files are **not** edited until Phase 6. Draft only.
> ID mapping: snapshot proposed S51/S52 — no collision with existing IDs (highest was S50); keep S51–S52 as proposed. New OQs continue S53–S59.

### G-RESOLVED checks

| ID | Original scope (summary) | Proposed status | Why (G-RESOLVED) |
|---|---|---|---|
| **S45** | Voice echo → "User correction during the turn"; Brian: "We have to get this tightened." Mid-turn redirect / orphan capture. | **RESOLVED** → remove; mechanism under P7-D01–D08 / P7-VOICEAUTH | Authority + cancel-before-stop + one capture + no unbound mid-turn + D06 hand-back shipped. Smoke S1–S8 + **S1b** (S1 PARTIAL at Starting; Accepting→forced-transcript drop proven live in S1b). Original question answered by shipped behavior. |
| **S37** | Re-anchor speech estimate on first reply text (fallback leading the bout). | **RESOLVED** → remove; closed into **P7-D06** | Monitor outranks estimate; hand-back when bout active. Smoke: 1× `no_bout_estimate`, 0× `forced_estimate`, estimate did not open capture during bout. Original fallback-estimate risk closed. |
| **S44** | Voice mode: purely conversational clarify; **no card**; panel not forced open. Approvals keep cards. Open: Cancel/Skip; multi-select; batch; late-answer drop. | **Partly resolved — keep, reframe** | Single questions: spoken choices + quiet card (card built, panel never auto-opens) — P7-CLARIFY / P7-D09. Original "no card appears" not fully met (quiet card still built). Batch/multi-select still carded. Brian 2026-10-07: "I want the only time a card is necessary is when in text mode. No need in voice mode." → remainder + new OQ S57. |
| **S38** | Listen-to-think latency too long; P5PRE STT component; no Phase 5 tuning. | **Updated, not resolved** | Instrumented + attributed; causal fix ❌ (execution_guidance). Brian: "The wait still feels the same." Original wait not closed. |
| **S34** | Per-sentence chunking / voice-live shaping / Edge paraphrase mismatch. | **Annotated, not resolved** | Track 4 **cut** (Brian: "Cut it; go to lore closeout (Recommended)"). Inputs carried; P4-D20/P4-D24 unchanged. |
| **S36** | Talk-over barge-in; state-aware policy including "her echo → ignore"; upstream-gated. | **Annotated, not resolved** | Echo→ignore part now the P7 admission authority. Barge-in itself still upstream-gated (`voice.barge_in: false`). |

### Proposed new OQ IDs (S51–S59)

| ID | Title | Evidence |
|---|---|---|
| **S51** | Backend native crash + no automatic recovery | FORENSIC-SERVE; Brian: "Let's file both the hotfix and the crash issue…" |
| **S52** | Stop-vs-silence-STT race client guard | Same verdict; proposed guard + duplicate-stop no-op |
| **S53** | Hermes capture correlation ID + `voice.record cancel` | Upstream; Track 1 notes / P7-D03 |
| **S54** | `agent.execution_guidance` decision | Track 3 root cause; tool rounds +8–12 s |
| **S55** | Streaming TTS bake-off | Brian-raised; Edge has none at pin |
| **S56** | Voice I/O ownership study | Brian fork question; Claude three-way compare |
| **S57** | Voice mode with no cards | Brian 2026-10-07 verbatim direction |
| **S58** | Smaller Whisper models | P2-D17; AUD-26 data |
| **S59** | `silence_duration` | LT-G3 pause data only; no recommendation |

### Drafted edits

#### Remove (RESOLVED → DESIGN_DECISIONS / P7-Dxx)

- Entire **S45** bullet (resolved by P7-VOICEAUTH / P7-D01–D08).
- Entire **S37** bullet (closed into P7-D06).

#### Replace S34 with:

```markdown
- **S34 — Hermes per-sentence chunking and voice-only reply shaping.**
  Whole-line / paragraph synthesis is blocked while Hermes hardcodes
  `SentenceChunker` (`P4-D24`). Related: a `voice-live` / `VOICE_LIVE_TURN_NOTE`
  path exists in Hermes for GPT-Live delegation but is unused by Windows;
  wording assumes paraphrase (inaccurate for Edge reading exact text) (B40).
  Also: markdown / em-dash in replies can collapse spoken pauses on Edge
  (`P4-VOICE` Phase 6 notes). Best path is upstream note or careful adopt of
  `voice-live` after tracing surface effects.
  **Phase 7:** Track 4 (`P7-VOICEPROSE`) **cut** — Brian (verbatim): "Cut it;
  go to lore closeout (Recommended)". Reasons: S-sentence ≈4% of the wait;
  prose shaping depends on the Phase 8 voice-pipeline choice (streaming TTS);
  the voice-live note's Edge "paraphrase" claim is false (P7-D12 evaluation).
  Inputs carried to Phase 8 voice work: voice-live note evaluation; short-
  first-sentence idea; one-sentence end-of-stream flush (6/8 baseline replies
  spoken only after the full stream); Brian's observation that speech lags
  the text. `P4-D20` and `P4-D24` unchanged.
```

#### Replace S36 with:

```markdown
- **S36 — Bring back talk-over barge-in without breaking Phase 4.**
  **Developer-requested.** Reframe: detecting speech and interrupting her are
  separate — state-aware policy: speech during her reply → interrupt; during
  open clarify → answer; her echo → ignore. **Feasibility gate: NO** (P5PRE
  AUD-14/15/16; `P5-D08`). Acceptance (all): (a) talk-over stops a long
  reply; (b) spoken clarify answer works with no "Interrupted"; (c) no
  `P2-D13` loop; (d) Track 1 gate still fails closed; (e) an instant answer
  given as soon as she stops speaking (before the beep) keeps its first word
  (needs ~1.2 s pre-roll; `voice.record` has none — Probe 2 / AUD-37 residual
  ~1 s clip). Blocked by one process-global Hermes listener. Options matrix:
  O1 fails (b) and (e); O3 has no hook that passes without turning barge-in
  on; O4 fails (b); O5 conflicts with `P2-D01`; only upstream O2
  (clarify-aware listener, discardable record stop, pre-roll on
  `voice.record`) can pass (a)/(b)/(e), and it is not on this pin.
  `voice.barge_in` stays `false` (`P4-D28`). Stays open, upstream-gated. Keep
  `P4-D13`/`D14`/`D15`/`D18`. Echo filter still only drops ≥3-word / ≥60%
  tail runs (A32).
  **Phase 7:** the "her echo → ignore" part of this policy is now the P7
  transcript-admission authority (`P7-D01`–`D08`; content matcher remains
  defense only, `P7-D07`). Barge-in / talk-over itself stays upstream-gated.
```

#### Replace S38 with:

```markdown
- **S38 — Listen-to-think latency.** Too long between the user finishing and
  Zola starting to think. Measured in P5PRE / `P5-D09` (warm, after he stops
  talking): 1500 ms configured silence; 1562–1847 ms WAV → transcript
  (Whisper `base` + delivery), roughly flat across 2.5–11 s clips; other
  stages under 15 ms. That is a substantial per-turn transcription component
  worth isolating later. Shorter silence risks cutting mid-thought (B44). No
  Phase 5 tuning. Stays open.
  **Phase 7 (`P7-LATENCY` / P7-D10) — updated, not resolved.** Instrumented
  `turn_timing` (observation only). **Baseline** EoS→first audio median
  **9534 ms** (n=7). Additive median shares: S-model **51.4%**, pre-submit
  **31.3%**, S-tts (Edge) **19.3%** (≈2.0 s), S-sentence **4.3%**, S-play
  **1.5%**; 6/8 replies spoken only on end-of-stream flush. **Tool vs
  no-tool:** submit→first audio **17.8 s** vs **5.4 s**. **AUD-26 = in-call**
  (standalone `transcribe_recording` ≈1.0 s, idle-serve ≈1.2 s, live ≈1.6 s).
  **Pauses (LT-G3):** median **120 ms**, p90 **484 ms**, max **1360 ms** vs
  `silence_duration` 1500 ms (0 pauses ≥1500 ms). Remeasure after narrow SOUL
  + UTC offset: causal B1/B2 still used tools; additive shares shifted but
  wait remained. **Root cause:** Hermes `OPENAI_MODEL_EXECUTION_GUIDANCE` /
  `agent.execution_guidance` outranks `SOUL.md` (see `S54`). SOUL "Everyday
  answers" applied then reverted; UTC offset kept. Brian (verbatim): "The
  wait still feels the same." Causal pass bar ❌; closed on findings
  (Brian: "C: close on findings (Recommended)").
```

#### Replace S44 with:

```markdown
- **S44 — No clarify card in Voice mode (partly resolved).**
  **Original scope:** In Voice mode, clarify questions should be purely
  conversational: she asks, he answers out loud, and no card appears; the
  conversation panel is not forced open. Approvals keep cards (`P4-D07`,
  never by voice). Text mode keeps the clarify card (`P4-D08`). Open then:
  voice Cancel/Skip ("never mind", "skip", timeout); multi-select; batch
  `questions[]`; late-answer drop (`P4-D14`) tied today to card Cancel.
  **Phase 7 (partly resolved by `P7-CLARIFY` / P7-D09):** single questions
  are voice-first with spoken choices and the **quiet card** (card still
  built in the conversation; panel never auto-opens). Typed fill-then-send
  in Voice mode only; no-answer opens the panel once; C3 adapted (composer
  lives inside the panel). Batch and multi-select still use the visual card.
  Exact "stop" unchanged; no new command words.
  **Remainder (Brian, 2026-10-07, verbatim):** "I want the only time a card
  is necessary is when in text mode.  No need in voice mode." Full Voice-
  mode-with-no-cards scope (batch / multi-select by voice, and open
  sub-questions on approvals and typed answers) → **`S57`**. Not marked
  fully RESOLVED.
```

#### Add after S50 (new OQs):

```markdown
- **S51 — Backend native crash + no automatic recovery.**
  Serve child dies as native APPCRASH (`0xc0000005`) with no Python
  traceback; Zola needs a manual relaunch. P7-FORENSIC-SERVE: (a) 08:48:12
  `python312.dll` (not Track-1-related; same class as three crashes on
  2026-10-05); (b) 10:52:31 `ntdll.dll` during silence auto-stop → client
  `voice.record stop` → `_resume_voice_wake` while silence-path STT in
  flight (indirect Track 1 relation). Clue: **zero** python APPCRASHes
  09-01→10-04, then **five in two days** (something changed ~10-04/10-05;
  not yet checked). Future work: find what changed (Windows/driver, uv
  CPython, Hermes env packages, P7PRE); persist Hermes stderr; enable WER
  local dumps; backend supervision (client respawns serve on unexpected
  exit; fail-closed voice during restart). Upstream note for the native
  crash. **Brian (verbatim, 2026-10-06):** "Let's file both the hotfix and
  the crash issue and prioritize for a future phase."

- **S52 — Stop-vs-silence-STT race client guard.**
  Same forensic window as `S51`(b). Proposed client guard: once Hermes
  reports `transcribing` for the current capture, a cancel invalidates
  only (no `voice.record stop`; transcript dropped as `cancelled`; idle
  settles); Cancel on an already-Cancelled capture is a no-op (no
  duplicate stop). Needs grounding that wake resumes on its own after
  silence-path idle. Upstream: `voice.record stop` should not resume wake
  until the silence/forced-stop pipeline reaches idle. **Brian (verbatim,
  2026-10-06):** "Let's file both the hotfix and the crash issue and
  prioritize for a future phase."

- **S53 — Hermes capture correlation ID + `voice.record cancel` (upstream).**
  No capture/correlation ID on `voice.transcript` or status terminals
  (`P7-D03`; AUD-23). `voice.record stop` always force-transcribes; there
  is no `voice.record cancel` that ends without transcription. Client
  lifecycle is enough for Phase 7; durable fix is upstream (Track 1
  progress notes / P7-D13).

- **S54 — `agent.execution_guidance` decision.**
  Largest measured latency lever from `P7-LATENCY`: tool rounds ≈ **+8–12 s
  per turn**; submit→first audio **17.8 s** with tools vs **5.4 s** without.
  Hermes `OPENAI_MODEL_EXECUTION_GUIDANCE` `<mandatory_tool_use>`
  (time/date/timezone → terminal; arithmetic → terminal) + `<act_dont_ask>`,
  gated by `agent.execution_guidance` (`prompt_builder.py` ~L333–345,
  402–431, 470), outranks `SOUL.md`; reinforced by MUST-`skill_view` /
  `everyday-assistance`. Needs its own audit: what each part of the block
  protects; a broad regression test; possibly a `SOUL.md` replacement for
  the good parts. Upstream note: the time/date → terminal rule conflicts
  with a trusted time context, and `TZ=… date` is wrong on Windows.

- **S55 — Streaming TTS bake-off.**
  Raised by Brian during Track 3. ElevenLabs, OpenAI, Gemini and xAI
  streamers exist at the Hermes pin; Edge has none; Cartesia is not built
  in. Voice choice is Brian's. Any switch must re-validate the playback
  monitor and Track 1/2 admission / clarify behavior on the new playback
  path. Related: Edge S-tts ≈2.0 s per first sentence; one-sentence flush
  (`S34` inputs).

- **S56 — Voice I/O ownership study.**
  Brian asked (2026-10-06) whether to fork Hermes. Compare (read-only
  pre-audit): (1) status quo; (2) a minimal documented patch set on a fork;
  (3) Zola owns voice I/O (client- or helper-process mic + STT; Hermes stays
  stock as the brain — reverses `C3` / `P2-D01`). Every upstream-blocked
  voice item (capture ID, record cancel, `S52` race, `S36` barge-in/pre-roll,
  likely `S51` native crashes) sits in the voice/audio layer. Wholesale fork
  of the whole agent is not the default recommendation (provider/API drift
  and security fixes become Zola's burden).

- **S57 — Voice mode with no cards.**
  **Brian (verbatim, 2026-10-07):** "I want the only time a card is necessary
  is when in text mode.  No need in voice mode." Scope: batch and
  multi-select clarify by voice (AUD-13; a voice protocol for several
  answers). Continues the unresolved remainder of `S44` after the quiet-card
  Phase 7 reading. **Open sub-questions, not decided:** (1) whether this
  extends to **approvals** (P4-D07 / P4-D27; voice approval of commands
  carries echo and mis-hearing risk); (2) typed answers in Voice mode
  currently need the panel open (composer lives inside it).

- **S58 — Smaller Whisper models (P2-D17 install decision).**
  Download = install (`P2-D17`). AUD-26 / LT-G1: standalone entry ≈**1.0 s**,
  live ≈**1.6 s** (in-call). Candidate sizes and English-only variants need
  measured WER vs latency before any change. No Phase 7 Whisper model change
  (P7-D10).

- **S59 — `silence_duration` (data only).**
  Live `silence_duration` = **1500 ms**. LT-G3 within-utterance pauses
  (9 clips, 78 pauses): median **120 ms**, p90 **484 ms**, max **1360 ms**;
  **0** pauses ≥1500 ms. Data filed for a future decision; **no
  recommendation** in Phase 7 (P7-D10: no silence change without new
  evidence).
```

#### Replace footer with:

```markdown
*S13 and S16 remain open. S17, S21, S26 updated at Phase 4 lore closeout.
S20, S22, S32 resolved (see DESIGN_DECISIONS Phase 4). S33–S41 added at
Phase 4 lore closeout. S42 added at Phase 5 kickoff (2026-10-01). S41
resolved (see DESIGN_DECISIONS Phase 5). S42 and S43 resolved at Phase 6
lore closeout (episodes + ambient time). S35 arithmetic resolved by
P6-CALC; session/always scopes remain. S14 annotated (foundation
complete, not resolved). S28 annotated (episodes exist; retirement
evaluable). S45 and S37 resolved at Phase 7 lore closeout (P7-VOICEAUTH /
P7-D06). S44 partly resolved (quiet card); remainder → S57. S38 updated
(not resolved); S34/S36 annotated. S51–S59 added at Phase 7 lore closeout.
Not open questions (one line): question quiet window withdrawn (B38); gap
"no Stop" closed by P4-D29; AUD-37 closed by P4-D18 (residual in S36);
external dictation tool is test hygiene (A20). Resolved items stay in
DESIGN_DECISIONS.md.*
```

### Phase 3 STOP

Draft only — `OPEN_QUESTIONS.md` not modified. G-RESOLVED table above; S51/S52 keep snapshot numbers (no collision).

**Brian (verbatim, Phase 3 approval):** "approved"
*(Corrected: a stray "<" from a template was recorded earlier; Brian's verdict is "approved".)*

**Phase 2 draft amendment (post-approval, house style):** S45/S37 RESOLVED note added to Phase 7 execution notes (above) because those OQs leave `OPEN_QUESTIONS.md`.

---

## Phase 4 — Draft ROADMAP (not applied)

> Lore files are **not** edited until Phase 6. Draft only.
> Replace `## Current stage — Phase 7 (scope is Brian's call)` through the carry-candidates list with the two blocks below. Keep `## Source documents` unchanged.

```markdown
## Phase 7 — COMPLETE: Voice She Can Trust
Phase 7 closed three tracks plus a read-only forensic pass; Track 4 was
cut. "Complete" means the planned phase shipped — not that voice work is
done. Shipped: transcript admission authority (her voice can't become
Brian's turn); voice clarify with spoken choices and the quiet card;
per-turn latency instrumentation and the first stage-level attribution;
the UTC offset in the time stamp. Measured limitations: latency was not
improved (causal target ❌); root cause identified as Hermes
`execution_guidance` outranking `SOUL.md`. `S45` and `S37` resolved;
`S44` partly resolved (remainder → `S57`); `S38` updated, not resolved;
`S34`/`S36` annotated.

1. ✅ **AUDIT** — P7PRE, merge `3e87e7c47ed2eee4a26f53dc9c4bba7d6f16b1ee`
   (audit content `044fe10a857edc364b0fa69cd2f72be5f45067d8`).
2. ✅ **DECISIONS LOCKED** — `P7-D01`–`P7-D13` (Appendix A); Brian
   (verbatim): "approved."; S34: "Yes. keep S34". Quiet-card reading of
   P7-D09 adopted during Track 2.
3. ✅ **BUILD PLAN WRITTEN** — `PHASE7_BUILD_PLAN.md` v1.1, commit
   `b5583f97c3e13870abc5d483ec23566458cd828e`, merge
   `ffef6f050a3fd6a8092d77fc055370296e2b522b`.
4. ✅ **TRACKS EXECUTED** — Tracks 1–3 merged; Track 4 cut; FORENSIC-SERVE
   read-only merged.
5. ✅ **VERIFICATION / SMOKE TEST** — per-track; recorded ⚠️: Track 1 S1
   PARTIAL at Starting (S1b PASS); Track 2 C3 adapted (composer in panel);
   Track 3 causal ❌ closed on findings (Brian: "C: close on findings
   (Recommended)"); serve APPCRASH class unresolved (`S51`/`S52`).
6. ✅ **TRACK MERGED**
   - Plan: `ffef6f050a3fd6a8092d77fc055370296e2b522b`
   - P7-VOICEAUTH: `3d264f07bb026c499c1fa8d82cce6dc71892f4e2`
   - P7-FORENSIC-SERVE: `512d91490be6317e6f644afc8051160b7cb560ef`
   - P7-CLARIFY: `80498b99f0e999efd91250fcc1c1d9315616bbb9`
   - P7-LATENCY: `7b168cfbb4daa95f5fa58307fd2377176f9ffd35`
   - Track 4 (VOICEPROSE): **cut** — Brian (verbatim): "Cut it; go to lore
     closeout (Recommended)"
7. ✅ **LORE CLOSEOUT** — this pass.

One-line track results:
- **P7-VOICEAUTH** — admission authority; cancel-before-stop; frozen
  terminal set; D06 hand-back; S45/S37 closed.
- **P7-FORENSIC-SERVE** — native APPCRASH class documented; filed `S51`/`S52`.
- **P7-CLARIFY** — spoken choices + quiet card; C1–C9/T1 PASS (C3 adapted).
- **P7-LATENCY** — `turn_timing`; stage attribution; UTC offset kept; SOUL
  Everyday reverted; closed on findings.
- **P7-VOICEPROSE** — cut (S-sentence ≈4%; depends on streaming-TTS choice).

## Current stage — Phase 8 (scope is Brian's call)
Candidates only (not a committed order); each with one line of evidence:
- **Voice I/O ownership study (`S56`)** — every upstream-blocked voice item
  sits in the voice/audio layer; Brian asked whether to fork.
- **`agent.execution_guidance` decision (`S54`)** — largest measured latency
  lever (tool rounds ≈ +8–12 s/turn; 17.8 s vs 5.4 s submit→audio).
- **Streaming TTS bake-off (`S55`)** — Edge has no streamer; ~2.0 s S-tts;
  Brian raised; re-validate monitor + Track 1/2 on any new path.
- **Backend crash / recovery (`S51`)** — five APPCRASHes in two days after
  zero 09-01→10-04; no automatic relaunch.
- **Stop-vs-silence-STT race guard (`S52`)** — forensic (b); client guard +
  duplicate-stop no-op proposed.
- **Voice mode with no cards (`S57`)** — Brian: "I want the only time a card
  is necessary is when in text mode.  No need in voice mode."
- **Memory round two (`S46`, P6-D01 migration, `S48`–`S50`)** — associative
  recall 0/4; fact-authority migration evidence-based; don't-note / skill
  policy / tunables after real use.
- **`S35` scopes, `S40`, `S28`** — session/always approvals; UI polish;
  session UI retirement (episodes exist; evaluate).
```

### Phase 4 STOP

Draft only — `ROADMAP.md` not modified. Phase 2 execution-notes amendment included.

**Brian (verbatim, Phase 4 approval):** "approved"

---

## Phase 5 — Identity and deploy verification (read-only)

### SOUL.md

| Copy | Path | Raw SHA-256 | LF SHA-256 |
|---|---|---|---|
| Live | `%LOCALAPPDATA%\hermes\profiles\zola\SOUL.md` | `E3D7BF9AC29B46237A2685BEBAE2E89E1A5952EDB23E5AFEEE0EE8363009FB49` | `BB793A70497CD8CE4C09DB9F8311B64425C9A12DBE3CE1CD527772FA42E4868B` |
| Identity | `zola-architecture/identity/SOUL.md` | same | same |

**MATCH ✅** — byte-identical; raw = expected reverted state `E3D7BF9A…`. No `## Everyday answers` section (reverted).

### `identity/VOICE_CONFIG.md` vs live `config.yaml` voice keys

Live config raw SHA-256: `7BA2E676A04FF92047C8D711FCB022BE8A532B11BAAC6F74B08986744E704570` (unchanged from Track 3 record).

| Key | Live | VOICE_CONFIG | Status |
|---|---|---|---|
| `stt.provider` | `local` | `local` | ✅ |
| `stt.local.model` | `base` | `base` | ✅ |
| `tts.provider` | `edge` | `edge` | ✅ |
| `tts.edge.voice` | `en-GB-SoniaNeural` | `en-GB-SoniaNeural` | ✅ |
| `tts.edge.speed` | `0.95` | `0.95` | ✅ |
| `voice.silence_duration` | `1.5` | `1.5` | ✅ |
| `voice.barge_in` | `false` | `false` | ✅ |
| `voice.stop_phrases` | `["stop"]` | `["stop"]` | ✅ |
| `voice.thinking_sound` | `true` | `true` | ✅ |
| `approvals.mode` | `manual` | `manual` | ✅ |
| `security.allow_lazy_installs` | `false` | `false` | ✅ |
| `wake_word.provider` | `sherpa` | `sherpa` | ✅ |
| `wake_word.phrase` | `hey zola` | `hey zola` | ✅ |
| `wake_word.sensitivity` | `0.6` | `0.6` | ✅ |

**No Phase 7 config changes** — keys match VOICE_CONFIG. ✅

### `plugins/zola_memory/` vs `hermes-plugins/zola_memory/` (source; tests/`__pycache__` excluded)

| File | Live = Repo (raw) |
|---|---|
| `__init__.py` | ✅ `7FAA42BC…` |
| `consolidate.py` | ✅ `1B2D8D8A…` |
| `fact_index.py` | ✅ `AA0CCE9E…` |
| `forget.py` | ✅ `A9B62AA8…` |
| `llm_access.py` | ✅ `EC5A8F31…` |
| `log.py` | ✅ `A2515A96…` |
| `pending.py` | ✅ `9FF6156C…` |
| `provider.py` | ✅ `E2920937…` |
| `registry.py` | ✅ `86AA4DA0…` |
| `retrieve.py` | ✅ `53D8044D…` |
| `store.py` | ✅ `C471EA12…` |
| `time_context.py` | ✅ `327A027A740D4CD4DAA6A046245A0B44606DC39B774BAECACDB5A327597BC1BE` |

**12/12 MATCH** (raw). `time_context.py` = expected `327A027A…` on both sides.

### `plugins/zola_tools/` vs `hermes-plugins/zola_tools/`

| File | Raw | LF-normalized |
|---|---|---|
| `__init__.py` | differ (repo CRLF) | ✅ `A1EF8541…` |
| `calculator.py` | differ (repo CRLF) | ✅ `0F29F3FC…` |
| `plugin.yaml` | differ (repo CRLF) | ✅ `F329E906…` |

**Content MATCH ✅** (LF-normalized). Raw mismatch is `core.autocrlf` CRLF in repo working tree vs LF on live — same as P6-LORE Phase 5. No fix required.

### Hermes pin

`345cd2b057a452236de401d3534b8502a7465e8d` — porcelain empty (Phase 1; not re-checked this phase beyond prior clean).

### Phase 5 STOP

No content mismatches requiring approval. Identity mirrors match live (SOUL reverted; plugins deployed; voice keys unchanged).

---

## Phase 6 — Apply approved drafts + exit checklist (STOP — no commit)

### Applied

- `DESIGN_DECISIONS.md` — 10 in-place annotations + Phase 7 section (approved Phase 2 draft, incl. S45/S37 execution note).
- `OPEN_QUESTIONS.md` — S45/S37 removed; S34/S36/S38/S44 updated; S51–S59 added; footer updated (approved Phase 3 draft).
- `ROADMAP.md` — Phase 7 COMPLETE + Phase 8 stub (approved Phase 4 draft).
- Diff maps only to approved draft text (no extra reformatting). `git diff --stat`: 3 files, +474 / −43.

### Phase 7 Exit Checklist

| Item | Result |
|---|---|
| Track 1 (`P7-VOICEAUTH`) merged; terminal set; checks; S1–S7; zero orphan admits; drops logged | ✅ (merge `3d264f07…`; S1 ⚠️ PARTIAL at Starting, S1b PASS) |
| Track 2 (`P7-CLARIFY`) merged; C1–C7; Text/approvals unchanged | ✅ (merge `80498b99…`; C3 adapted — composer in panel) |
| Track 3 (`P7-LATENCY`) merged; baseline/after; **chosen fix meets pass bar**; AUD-26 | ⚠️ merged `7b168cfb…`; AUD-26 = in-call; **pass bar ❌** — Brian: "C: close on findings (Recommended)" |
| Track 4 merged or cut with grounding recorded | ✅ **cut** — Brian: "Cut it; go to lore closeout (Recommended)"; grounding in P7-D12 / S34 |
| No `hermes-agent` edits; clean at `345cd2b0…` | ✅ porcelain empty @ `345cd2b0…` |
| No installs unless STOP-approved | ✅ |
| Live-profile changes limited / mirrored / backups deleted at track closeout | ✅ (UTC offset kept; SOUL Everyday reverted; config `7BA2E676…` unchanged this closeout) |
| Named constants; no transcript/reply text in logs/docs | ✅ |
| Client builds; `Zola.Client.Checks` pass on main after merges; plugin tests if plugin changed | ✅ build 0/0; Checks coverage all PASS (lifecycle 22/22 … timing 8/8); `zola_memory` 112 OK; `zola_tools` 44 OK |
| Smoke after each track boundary | ✅ (per track progress; G-CRASH recorded) |
| `DESIGN_DECISIONS.md`: P7-D01–D13 + annotations | ✅ applied |
| `OPEN_QUESTIONS.md`: S45/S37 resolved; S44 partly; S38/S34/S36 annotated; new OQs | ✅ applied (S51–S59) |
| `ROADMAP.md`: Phase 7 COMPLETE; Phase 8 stub | ✅ applied |

### Diff verification

Every hunk maps to approved draft text (annotations, Phase 7 section, OQ status changes/new IDs, ROADMAP replace). No opportunistic cleanup.

### Phase 6 STOP

**No commit.** Lore applied on `p7-lore`. Awaiting **"proceed to commit and merge"**.

---

## Phase 7 — Commit and merge

| Item | SHA |
|---|---|
| Lore commit | `53cd1b3dc929c3b8b1463ad397c1ec08c5563c8d` |
| Merge (`--no-ff` `p7-lore` → `main`) | `c7e46fb308c7e21d47e72183944ba5e74a2c0081` |
| Final `main` HEAD (after this metadata commit) | recorded below |

Branch `p7-lore` deleted locally and on `origin`.

### Phase 7 CLOSED

Phase 7 lore closeout merged. New OQs: S51–S59. Phase 8 candidates listed in ROADMAP.
