# Zola-Windows Open Questions
Remaining Decisions-Locked items from `Zola_WINH00_MasterSynthesis.md`
Section 5, not yet resolved. Resolved items move to
`DESIGN_DECISIONS.md` and are removed from here. IDs match the master
synthesis document.
---
## Research needed (surfaced after Decisions Locked closed)
- **S13 — Windows-viable path to read the user's own incoming SMS.**
  See `DESIGN_DECISIONS.md` S13. Candidates to evaluate: Microsoft
  Phone Link (companion sync from a paired Android/iPhone), a
  Twilio-provisioned number (texts arrive at a Twilio number, not the
  user's personal number — different UX tradeoff), or another
  mechanism not yet identified. Needs research before it can be scoped
  into a build track. The `SMS On-Demand Query Path` pattern in
  `Zola_Sms_Intelligence_Architecture.md` (on-demand read/search/send,
  independent of the Daily Brief pipeline) is the likely v1 shape once
  an access path is found — not the full five-stage intelligence
  analyzer, which is deferred with the rest of the Daily Brief per S12.
  **Brainstorm intake (P9-KICKOFF, 2026-10-09; not a decision):** The brainstorm favored an Android companion app over Phone Link or Google Messages for Web (neither has a public API; both would mean reverse-engineering a private protocol). Shape discussed: a `NotificationListenerService` on Google Messages, whose `MessagingStyle` extras usually carry the last several messages of the thread (RCS has no public read API; group history and older messages are not available); replies through the notification's `RemoteInput` action, which could cover RCS and SMS (to verify on an RCS group thread); push from the phone rather than polling, with queueing while Windows is offline; its own auth token on the phone-to-PC channel; LAN-only v1 versus a relay undecided. Replies stay under `A1`. Brian (verbatim): "Let's remember that for when we get to that point." See `S73` and the strawman `Zola_Architecture_Distributed_Presence_Device_Capabilities.md` (DP-Q06).
- **S14 — Structured memory store (foundation complete, not resolved).**
  Phase 6 built a local Zola store beside the flat files: structured fact
  index (files remain fact authority), episodes with consolidation and
  lexical/entity retrieval, ambient time, and forget with physical erasure
  (`P6-D01`–`D11`). **Still open:** (1) long-term retrieval quality —
  associative/paraphrased episode recall was 0/4 under fixed blind queries
  (see `S46`); (2) evidence-based migration of fact authority to the store
  (relevance, prompt cost, memory quality — not fill %); (3) measurement
  plan — report fill %, prefetch relevance, and prompt cost before any
  migration call. Tiers/confidence/decay and environmental facts remain
  out of scope until that evidence exists.

- **S16 — Google Workspace Integration (Gmail, Calendar, Drive,
  Contacts) — deferred from Phase 1.** Phase 1's email track
  (`P1-EMAIL`) was blocked in grounding. None of the paths already in
  the pinned Hermes checkout fit an email-only, app-password,
  config-only track that also keeps send behind a real gate. The
  bundled IMAP/SMTP adapter (`plugins/platforms/email/`) is only an
  autonomous gateway poll-and-reply loop. It registers no
  agent-callable tool, so the Windows chat cannot read or send through
  it on demand. Himalaya and the Google Workspace skill are both
  already present and both run through the terminal tool. That tool
  does not call `request_tool_approval()` for ordinary commands, so
  once credentials exist the agent can send with no approval step.
  `approvals.deny` can block a command string, but it does not
  understand the skill, cannot see inside a script, and a different
  command using the same credential still reaches the API. The
  Workspace skill's pinned `setup.py` always requests the full scope
  list (`gmail.readonly`, `gmail.send`, `gmail.modify`, plus Calendar,
  Drive, Contacts, Sheets, and Docs). The `--services` flag described
  in the skill text is not implemented, so this script cannot consent
  to read-only now and add send later. Brian wants the eventual scope
  to be Gmail, Calendar, Drive, and Contacts together, not email
  alone, so a narrow OAuth setup now would be redone later. When this
  is picked up, the recommended shape is a custom user-plugin tool
  (`%LOCALAPPDATA%\hermes\profiles\zola\plugins\<name>\`,
  `register_tool()`, no edit to the pinned checkout): register read
  operations first, and add send later as its own tool behind
  `request_tool_approval()`. That is a code-level gate, not a
  bypassable command filter, and it is its own build once the full
  Workspace surface is being designed. OAuth consent has not been
  started: no Google Cloud project, OAuth client, consent screen, test
  user, or token exists for this profile.
  **Phase 8: RESOLVED.** Shipped as `zola_workspace` across P8-HARDEN, P8-CONNECT, P8-READ, and P8-SEND. Calendar past and upcoming; read-only Gmail triage; Drive find and read, including PDF; Contacts lookup; Gmail drafts and passphrase-approved sends. SEND closeout: five `drafts.send`, zero `messages.send`. The send gate is the passphrase in P8-D06, not the card S16 recommended.
- **S17 — Audio-driven lip sync and precise speaking end.**
  Partially resolved by `P3-D23` (mouth follows TTS playback presence) and
  Phase 4 monitor-driven follow-up / question release (`P4-D18`, `P4-D13`).
  Trailing silence on Sonia 0.95: median **~0.50 s** per sentence (bout stop
  minus last segment stop; n=9; `P4-VOICE` Phase 7). `P2-D15` refit values:
  WPS 2.5, FSL 3.3, OV 0.5, margin 5.0; startup window 5.3 s (separate).
  Still open: no true end-of-playback signal from Hermes; mouth still cannot
  see mid-sentence pauses; shapes remain synthetic. Peak meter still 0 on
  this machine.

- **S18 — Global push-to-talk hotkey.** `Ctrl+Space` works only while
  the window is focused. A system-wide hotkey is deferred.
- **S19 — Directed-speech detection (Master Plan §12).** Wake word is
  the primary trigger. Detecting speech meant for Zola without it,
  with addressee confidence tiers, is the long-term target. Hermes
  has no implementation (WINH09-AUD-14/15).

- **S21 — Typed Send and Cancel during speech are recorded as spoken
  interruptions.** Hermes still latches `SPEECH_INTERRUPTED_NOTE` for typed
  Cancel during speech. Phase 4 lock gate and Stop speaking (`P4-D02`,
  `P4-D29`) use the no-latch `voice.toggle off` path and avoid the latch.
  Still open for typed Cancel (and any other latching interrupt path).


- **S23 — First-utterance speech-to-text delay.** About 7 s for the
  first transcription after launch (model load), then about 1.7 s
  (P2-VOICE). A warm-up could hide it.
- **S24 — GLB asset rework.** Separate eye geometry (saccade), a hair mesh
  (strand shimmer), projection geometry, head/neck articulation (head
  motion, `P3-D22`), a frown/negative mouth target, and an eye-softness
  target (`P3PRE-AUD-10`–`16`). Any rework must keep the 15 morph targets
  and their order, or update `MorphTarget.cs`.
- **S25 — HUD data sources.** Attention level, conversational momentum,
  emotional tone, system health, environment, version, and the dock and
  Core Systems destinations (Memory, Environment, Awareness, Behavior,
  Security, Systems, Settings, Account). Each needs a real source first
  (`P3-D06`). `ALERT` has no Windows trigger; its Track 5 values are
  placeholder-safe until one exists.
- **S26 — A missing `message.complete` leaves the turn "Thinking".**
  `_streaming` never clears (Audit 04 §1b); presence can stay `THINKING`.
  Phase 4 activity line (`P4-D16`) improves visibility during tools. Related
  gap (K7 / A11): resuming a still-running turn can leave `_streaming=false`
  ("resumed-running"). Still open.

- **S27 — Mic-input meter in the identity block.** Track 5 did not fill
  the reserved waveform space: the client has no mic level (`P2-D01`), so
  a meter needs a new source (`P3-D07`).
- **S28 — Session UI retirement.** The developer expects his memory system
  to make sessions unnecessary. When it does, remove the SESSION HUD line
  and the Sessions dock button together.
  **Phase 6:** episodes now exist (P6-EPISODES) with cross-session
  prefetch. Session UI retirement can be evaluated; no retirement decision
  yet.

- **S29 — Markdown rendering in chat bubbles.** Bubbles are plain text, so
  fenced code, lists and links show as raw markdown. Predates Phase 3.

- **S30 — Presence backdrop and decoration.** Warm background glow, floor
  rings, base light pooling (concept art), corner brackets if wanted, and
  particles — all deferred by the developer (`P3-D21`; particles dropped in
  Track 5). On this WinUI + Helix SharpDX surface, Composition `Forever`
  keyframe animations do not advance. Tried: (1) `AnimationController.Progress`
  setter — access-violates, kills the process; (2) negative `DelayTime` —
  `ArgumentException`; (3) `CompositionPropertySet.StartAnimation("t",
  Forever)` — starts, `t` never advances; (4) Forever on ElementVisual /
  ShapeVisual Offset/Opacity — Start succeeds, Progress stays 0. Any future
  animated decoration must solve that first.
- **S31 — Helix reload memory.** Each F10 debug reload adds about **150 MB**
  of native memory inside Helix's texture registration; managed memory stays
  flat (~160 MB after the first real reload). Ordinary lock, sleep and
  minimize reuse the scene. No product fix in Phase 3; F10 stays debug-only.
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
  **Phase 7:** Track 4 (`P7-VOICEPROSE`) **cut** — Brian (verbatim): "Cut it;
  go to lore closeout (Recommended)". Reasons: S-sentence ≈4% of the wait;
  prose shaping depends on the Phase 8 voice-pipeline choice (streaming TTS);
  the voice-live note's Edge "paraphrase" claim is false (P7-D12 evaluation).
  Inputs carried to Phase 8 voice work: voice-live note evaluation; short-
  first-sentence idea; one-sentence end-of-stream flush (6/8 baseline replies
  spoken only after the full stream); Brian's observation that speech lags
  the text. `P4-D20` and `P4-D24` unchanged.

- **S35 — Approval scopes beyond "once"; revisit `approvals.mode`.**
  Phase 4 forces `manual` (`P4-D27`) because Hermes's default `smart` can
  auto-approve. Session/always scopes and whether `manual` remains required
  need their own decision.
  Observation (P5-WAKE smoke B3): a plain arithmetic question produced
  one approval card per math problem (developer: "she showed a card for
  each math problem for approval.").
  **Phase 6:** arithmetic case **RESOLVED** by `P6-CALC` / `P6-D08` —
  bounded `calculate` tool; three arithmetic prompts, zero cards; control
  still cards; `P4-D07`/`P4-D27` stand. **Session/always scopes stay open.**

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

- **S39 — Voice timbre (husky / breathiness).** Developer wants her huskier
  or deeper. Edge exposes rate/pitch/volume only; texture needs a premium
  provider (`P4-D23`). Also: Edge "Yeah" inflection noted live (`P4-VOICE`).
  Revisit by listening.

- **S40 — UI polish after Phase 4.** Esc priority vs open clarify panel
  (F7); hold important request notices before the next status line replaces
  them; activity line can show a finished tool during a concurrent Hermes
  batch (A31 / A34).
  Observation (P5-MEMORY cleanup): an "empty box while thinking" was
  seen once before she said "forgotten"; watch for recurrence.



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

- **S46 — Semantic / associative episode retrieval.**
  Direct lexical episode recall passed in Track 5. Associative /
  paraphrased retrieval found **0/4** under the fixed blind queries
  (shared-word counts with stored summaries: Q2=0, Q3=1, Q4=0, Q5=0;
  prefetch miss on all four). This is a **retrieval-quality** limitation,
  not an episodic-memory persistence failure. Phase 6 intentionally did
  not add embeddings or vector retrieval. Next-phase question: "What is
  the minimum semantic retrieval mechanism that materially improves
  associative recall without creating another memory authority?"

- **S47 — Notebook-fact clarification is model judgment.**
  For notebook facts, whether she asks before erasing is SOUL-guided
  judgment, not code-enforced: with Mara (separate messages) she asked;
  with two Rosas in one sentence she erased both, then restored the aunt
  on correction (Brian accepted). The `forget_guard` / `ask_brian` path
  enforces clarification for episode memory and after a forget lookup
  flags `ask_brian`, not for ordinary notebook removes. Decide whether
  notebook clarification needs a stronger gate.

- **S48 — Consolidator honors "no need to save a note" as don't-remember.**
  Observed in Track 5 (S1' and Fernhill leak-test): an explicit "no need
  to save a note" / don’t-note request was treated as consent not to
  write an episode. Not designed as a product rule. Decide whether that
  is the intended consent behavior and document it if so.

- **S49 — Background-review skill edits — is a policy needed?**
  During Phase 6 smokes, background review created/patched procedural
  skills (`communication/conversation-memory`,
  `communication/everyday-assistance`; 0 personal facts). Brian
  (verbatim): "Keep". Pattern: background review edits skills
  autonomously. Decide whether that needs an explicit policy (what it may
  write, review cadence, or a hold).

- **S50 — Phase 6 memory tunables after real use.**
  Named starting values shipped and smoke-checked:
  `MEANINGFUL_GAP_MINUTES = 30`, `CONSOLIDATE_QUIET_MINUTES = 10`,
  `EPISODE_MIN_SCORE = 0.15` (calibrated on synthetic related vs
  single-common-word corpus). Retune only with measured over-mention,
  missed consolidations, or prefetch false-positives/negatives — not by
  feel.

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
  **Phase 8 annotation (2026-10-08 ~11:07):** During CONNECT-FIX, a typed sentence landed at 11:07:48 on a process that died before the turn finished. After relaunch, Hermes replayed it with a leading interrupted-turn note. The memory guard failed closed on that note. A later message with the sentence alone was saved. The progress doc records a process death and that side effect. It does not record a new APPCRASH classification for this occurrence.

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
  **Phase 8 annotation:** Retiring `google-workspace`, `himalaya`, and `email-inbox-triage` removed the Gmail `skill_view` route. In CONNECT C9, asked to check email with Himalaya, she ran `command -v himalaya` (exit 1) and did not `skill_view` that skill. The terminal guard now blocks commands that name Google API hosts or the token store. That C9 command names neither. The `execution_guidance` decision stays open.

- **S55 — Streaming TTS bake-off.**
  Raised by Brian during Track 3. ElevenLabs, OpenAI, Gemini and xAI
  streamers exist at the Hermes pin; Edge has none; Cartesia is not built
  in. Voice choice is Brian's. Any switch must re-validate the playback
  monitor and Track 1/2 admission / clarify behavior on the new playback
  path. Related: Edge S-tts ≈2.0 s per first sentence; one-sentence flush
  (`S34` inputs).
  **Brainstorm intake (P9-KICKOFF, 2026-10-09; not a decision):** Brian (verbatim, 2026-09-24): "Zola's wit is coming through better in text than verbally." Untested free lever: SSML prosody and breaks on Edge, if Hermes's Edge path can pass SSML at all (to check at the pin). Edge does not expose Azure's `express-as` styles. Candidates beyond Edge for expressive delivery: the full Azure Speech SDK (same voice family, with styles), ElevenLabs, and OpenAI TTS (natural-language tone direction). Any switch keeps the re-validation rule above. Related: `S39`.

- **S56 — Voice I/O ownership study.**
  Brian asked (2026-10-06) whether to fork Hermes. Compare (read-only
  pre-audit): (1) status quo; (2) a minimal documented patch set on a fork;
  (3) Zola owns voice I/O (client- or helper-process mic + STT; Hermes stays
  stock as the brain — reverses `C3` / `P2-D01`). Every upstream-blocked
  voice item (capture ID, record cancel, `S52` race, `S36` barge-in/pre-roll,
  likely `S51` native crashes) sits in the voice/audio layer. Wholesale fork
  of the whole agent is not the default recommendation (provider/API drift
  and security fixes become Zola's burden).
  **Brian, 2026-10-06 (verbatim):** "I'm not so much thinking about that. I think I will continue with the current way we are doing things." The pinned upstream checkout stays (no fork). The study remains available if a concrete voice-layer need reopens it.

- **S57 — Voice mode with no cards.**
  **Brian (verbatim, 2026-10-07):** "I want the only time a card is necessary
  is when in text mode.  No need in voice mode." Scope: batch and
  multi-select clarify by voice (AUD-13; a voice protocol for several
  answers). Continues the unresolved remainder of `S44` after the quiet-card
  Phase 7 reading. **Open sub-questions, not decided:** (1) whether this
  extends to **approvals** (P4-D07 / P4-D27; voice approval of commands
  carries echo and mis-hearing risk); (2) typed answers in Voice mode
  currently need the panel open (composer lives inside it).
  **Phase 8: partly answered.** Workspace sends are approved by the passphrase in text and voice, with no card (P8-D06). Command approvals remain visual (P4-D07). Batch and multi-select by voice stay open. The two sub-questions stay open.

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

- **S60 — Gmail triage actions.** Mark read, archive, and label. They need `gmail.modify`. Deferred by P8-D07. **Brian (verbatim):** "3. Read only for now."

- **S61 — Calendar writes.** Create, then update and delete, including invitations. Deferred: side effects on other people, and enough new authority already in Phase 8.

- **S62 — Gmail attachment content.** Phase 8 returns name, type, and size only. Attachment content was left out by the locked P8-D08 (Brian: "approved."). A later read would reuse the Drive reader.

- **S63 — Provenance-aware memory.** Would allow P8-D09 Option B, an attributed save. Not chosen. **Brian (verbatim):** "Let's go with option A for now."

- **S64 — Office extraction.** Word, Excel, and PowerPoint stay `unsupported_type`. PDF is installed (pypdf 6.19.0, P2-D17). The candidate Office libraries pull in compiled `lxml`. This is an install decision, not a default.

- **S65 — An OS-level credential boundary.** A broker process or a separate Windows user, if the application boundary in P8-D02 proves insufficient. Phase 8 accepted the application boundary. Same-user code can still reach the token.

- **S66 — Proactive Workspace surfacing.** Push, webhooks, and the brainstorm items (email or calendar raised without a question). Proactive behavior is its own phase.
  **Brainstorm intake (P9-KICKOFF, 2026-10-09; not a decision):** Brian (verbatim, 2026-10-06): "I'm also thinking about proactive actions. Surfacing important emails or messages without being asked. Following up on them and reporting what action was taken suggesting a response based on what it knows about my day to day." Brainstorm staging: ingest and rank, then tie items to calendar and memory, then open loops (`S71`), and only then limited approved actions. Start with a quiet surface (an on-request "what's pending", or a digest); add voice or push interrupts only after ranking has proven itself on real mail, since a wrong interruption costs more trust than a missed one. Email and message bodies are untrusted (`P8-D09`). Habits such as "you usually handle this the same day" are inferred at read time, not stored as facts. **Authority conflict to resolve before any background surfacing:** `P8-D02` makes Workspace Brian-only (`platform == "tui"` and an empty `parent_session_id`) and excludes cron, subagents and background review, so a background reader needs a new, narrow, read-only authority decision, or surfacing must happen inside Brian's own turns. Relates to `S12` (Daily Brief) and `S4` (texting Brian).

- **S67 — Summary selectivity.** R1, R8, and the R1 rerun left both smoke emails out of the triage summary. Asked for a gist of a reviewed draft, she omitted both addresses. That gist turn had no passphrase. The harness refused `not_reviewed` when a reply omitted the Bcc address. Candidate: a structured per-sender breakdown from `gmail_search`, after diagnosing read versus unread. **Brian (verbatim):** "I think this is a bit much. I can confirm that the smoke test passed." Accepted, not fixed.

- **S68 — OAuth publishing.** The app is in Testing. Refresh tokens last about seven days, so setup is re-run until it is published. Production needs a homepage and a privacy-policy URL. Pages were drafted for GitHub Pages. **Brian (verbatim, 2026-10-07):** "I went with test for now to keep things moving. I will work on setting up the site later." After publishing, run setup once.

- **S69 — Whole-message matches versus Hermes-injected text.** The interrupted-turn note in front of a replayed message blocked a valid save (CONNECT-FIX, 2026-10-08, fail-closed). The passphrase matcher has the same exposure: a message containing "previous turn was interrupted" anywhere never matches (`send_gate.py` L133). Decide whether to strip a known Hermes prefix, and how to prove the prefix is Hermes's, or keep failing closed with her explanation.

- **S70 — Voice playback-completion signal.** A read-back interrupted mid-speech still counts as reviewed. There is no playback-completion signal. Ties to the voice I/O ownership study (`S56`).

- **S71 — Open loops (follow-up commitments).** Brainstorm intake (P9-KICKOFF, 2026-10-09; not a decision). When Zola says she will watch for something or follow up, a real record must exist behind it: source, subject, what closes it, an expiry, and a place Brian can see it. A promise with nothing watching is worse than not offering. Open loops are the foundation for proactive surfacing (`S66`), background agents (`S72`) and escalation (`S74`). Open: which store owns them (one authority; the Phase 6 store is the candidate); how a loop closes (event, Brian, expiry); how she lists them by voice ("what's pending").

- **S72 — Background agents and agent status.** Brainstorm intake (P9-KICKOFF, 2026-10-09; not a decision). Brian (verbatim, 2026-10-07): "Background agents for email, sms, and other functions. These agents would report up to Zola, but I could also communicate directly with each agent. They would show up in the HUD for online status in the left side as we had in the Android version. Zola would be able to report verbally on each status as well." On the channel (verbatim): "All voice." Brainstorm notes: agents prepare and Zola alone decides what surfaces; an agent never messages Brian on its own, never bypasses a send gate, and never writes memory on its own authority because Brian was the one talking to it; HUD and spoken status come from observed health (last successful check, queue size, errors) and never from an agent's self-report, with at least online, degraded and unknown states; most monitors can be plain code that calls the model only when something new arrives (cost and reliability); by voice, addressing needs a design (a hand-off with a visible "on the line" state versus naming the agent each time), each agent needs a distinct voice or spoken cue, and replies stay short while barge-in is off (`S36`). Shape (Hermes subagents, cron under `S7`, or Windows-side services) depends on the WINH08 tooling findings. Touches `S25` (HUD data sources) and the `P8-D02` authority conflict noted in `S66`.

- **S73 — Android companion and distributed presence.** Brainstorm intake (P9-KICKOFF, 2026-10-09; not a decision). Brian's strawman `zola-architecture/Zola_Architecture_Distributed_Presence_Device_Capabilities.md` (v0.1, 2026-10-03; every DP-D entry is a proposal, and its DP IDs are local to that draft) is committed by P9-KICKOFF. It predates Phases 6–8, so its references to S16, S42, Workspace and memory are out of date. Brainstorm review (2026-10-03): resolve gateway placement (DP-Q01) before designing the capability registry; the transitional state where Windows keeps its direct RPC beside the gateway needs a hard cutover condition, or it becomes a permanent duplicate path; hardcode the first two or three capabilities before building a general registry. Same Zola from the phone: a second client reaching the same `hermes serve` through an authenticated tunnel works in principle, because sessions are per user, gated on serve's network binding, the PC being awake, the `H1`–`H6` revisit trigger for off-device exposure, and wake and mic ownership by one socket. Avatar on the phone: a passive mirror of Windows state only, shown in the foreground only; Ava on the same phone should be a deliberate choice. SMS: see `S13`.

- **S74 — Remote escalation (phone call).** Brainstorm intake (P9-KICKOFF, 2026-10-09; not a decision). Idea: when Zola judges something urgent and Brian is away from the PC, she escalates through a ladder ending in a phone call, and Brian can also call her. Brainstorm notes: a late rung, not an early feature; telephony is a new voice transport and needs a reviewed change to Windows audio ownership (`C3` / `P2-D01`); inbound calls need authentication beyond caller ID (spoofable) and beyond a voiceprint (`S1` deferred), such as a PIN; raw Hermes JSON-RPC is never exposed publicly; escalation needs hard limits (maximum attempts, quiet hours, an acknowledgement that stops it, and stop when unsure). `P8-D06` approves a send by a spoken passphrase in Brian's room; a phone line is a weaker channel and needs its own decision. Suggested first step: a companion high-priority push that opens a talk-to-Zola screen (`S73`).

- **S75 — Speaker and face recognition as signals.** Brainstorm intake (P9-KICKOFF, 2026-10-09; not a decision). Brian (verbatim, 2026-10-06): "voice recognition and eventually facial recognition through the PC or cellular camera." Brainstorm notes: both are signals Zola weighs, never authentication. Speaker identification (Brian versus others, the TV, guests) supports directed speech (`S19`) and revisits `S1`; the voiceprint is biometric, kept local, deletable, and never an ordinary memory fact. For "is this Brian at the PC", use Windows Hello rather than a custom face matcher; identifying other people raises consent. Cameras are user-initiated with a visible indicator, never continuous; processing is local; an uncertain match is reported as uncertain. Order: speaker identification before any camera work.

- **S76 — Smart home: Kasa lights.** Brainstorm intake (P9-KICKOFF, 2026-10-09; not a decision). Brian (verbatim, 2026-10-08): "I use Kasa devices. Is there a way to give Zola control?" and "I only have lights, so not a big concern." Brainstorm notes: a small local tool built on `python-kasa` (an install decision under `P2-D17`); Home Assistant only if other device types are added; same network as the PC only. With lights only there is no confirmation tier: she acts, then reads the device state back and says so plainly when a light is unreachable. To check: whether current Kasa firmware needs TP-Link account credentials for local control (if so, storage follows the `P8-D04` DPAPI precedent).

*S13 remains open. S16 resolved at Phase 8 lore closeout (P8-D01–P8-D12). S17, S21, S26 updated at Phase 4 lore closeout. S20, S22, S32 resolved (see DESIGN_DECISIONS Phase 4). S33–S41 added at Phase 4 lore closeout. S42 added at Phase 5 kickoff (2026-10-01). S41 resolved (see DESIGN_DECISIONS Phase 5). S42 and S43 resolved at Phase 6 lore closeout (episodes + ambient time). S35 arithmetic resolved by P6-CALC; session/always scopes remain. S14 annotated (foundation complete, not resolved). S28 annotated (episodes exist; retirement evaluable). S45 and S37 resolved at Phase 7 lore closeout (P7-VOICEAUTH / P7-D06). S44 partly resolved (quiet card); remainder → S57. S38 updated (not resolved); S34/S36 annotated. S51–S59 added at Phase 7 lore closeout. S51 annotated at Phase 8 (2026-10-08 process death and the interrupted-turn note). S54 annotated at Phase 8 (skill route removed; decision open). S57 partly answered at Phase 8 (Workspace sends); batch and command approvals stay open. S60–S70 added at Phase 8 lore closeout. S71–S76 added, and S13, S55, S56 and S66 annotated, at the Phase 9 kickoff (P9-KICKOFF, 2026-10-09: brainstorm intake; nothing decided). Not open questions (one line): question quiet window withdrawn (B38); gap "no Stop" closed by P4-D29; AUD-37 closed by P4-D18 (residual in S36); external dictation tool is test hygiene (A20). Resolved items stay in DESIGN_DECISIONS.md.*
