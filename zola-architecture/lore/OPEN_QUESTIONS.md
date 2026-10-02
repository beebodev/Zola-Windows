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

- **S35 — Approval scopes beyond "once"; revisit `approvals.mode`.**
  Phase 4 forces `manual` (`P4-D27`) because Hermes's default `smart` can
  auto-approve. Session/always scopes and whether `manual` remains required
  need their own decision.
  Observation (P5-WAKE smoke B3): a plain arithmetic question produced
  one approval card per math problem (developer: "she showed a card for
  each math problem for approval."). Inputs: which tool she used;
  whether harmless tools can be scoped out of manual approval without
  weakening `P4-D07`.

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

- **S37 — Re-anchor speech estimate on first reply text.**
  `FirstSentenceLatencySeconds` is seeded at turn start; late first text
  leaves real TTS start delay uncounted, so short/medium fallback estimates
  can lead the bout (up to ~4.33 s before margin 5.0). Reply `forced_estimate`
  uses **no** `FollowUpMarginSeconds`. Monitor path is primary; this is
  fallback-only (`P4-D22` / B45).

- **S38 — Listen-to-think latency.** Too long between the user finishing and
  Zola starting to think. Measured in P5PRE / `P5-D09` (warm, after he stops
  talking): 1500 ms configured silence; 1562–1847 ms WAV → transcript
  (Whisper `base` + delivery), roughly flat across 2.5–11 s clips; other
  stages under 15 ms. That is a substantial per-turn transcription component
  worth isolating later. Shorter silence risks cutting mid-thought (B44). No
  Phase 5 tuning. Stays open.

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

- **S42 — Memory is not shared across sessions.** Developer-requested
  2026-10-01; Phase 5 scope. Principle (developer): a Hermes session is a
  conversation boundary, not a Zola memory boundary. Durable facts, decisions
  and episodes belong to Zola and are retrieved by relevance in any session;
  sessions produce and consume memories but never **automatically** read each
  other's transcripts (amended by `P5-D06`: explicit `session_search` when
  asked is allowed; search results are not memory). P5PRE found that written
  facts already cross sessions (each new session reloads `MEMORY.md` /
  `USER.md`); the gap was that she rarely saved. **Facts half resolved** by
  P5-MEMORY (`P5-D03`–`P5-D07`; save rate lasting 6/6, trivial 0/4, explicit
  2/2; correction PASS). **Open remainder:** episodes ("what did we decide…"
  without being asked), which moves to `S14` in Phase 6. Phase 6 input:
  Hermes's pluggable memory layer (`agent/memory_provider.py`,
  `agent/memory_manager.py`; one external provider via `memory.provider`,
  loadable from the profile's `plugins/` without editing `hermes-agent`;
  hooks `system_prompt_block`, per-turn `prefetch`, `sync_turn`,
  `on_session_end`, `on_pre_compress`, `on_memory_write`). Related: `S28`,
  `S43`.

- **S43 — Time awareness in conversation.** She knows the current time,
  but not when each message or session happened, so "5 minutes ago" and
  "24 hours ago" look alike. Live evidence: the P5-MEMORY BR1 answer had
  no timing, although `session_search` results carry session start dates.
  Inputs: `Zola_Temporal_Reasoning_Architecture.md`, WINH12-02. Phase 6,
  with `S14`.

- **S44 — No clarify card in Voice mode.** Developer, 2026-10-02. In
  Voice mode, clarify questions should be purely conversational: she
  asks, he answers out loud, and no card appears; the conversation panel
  is not forced open. Approvals keep cards (`P4-D07`, never by voice).
  Text mode keeps the clarify card (`P4-D08`). Touches `P4-D08` and
  `P4-D13`. Open: voice Cancel/Skip ("never mind", "skip", timeout);
  multi-select; batch `questions[]`; late-answer drop (`P4-D14`) tied
  today to card Cancel. Needs a short audit of card users before any
  build. Not Phase 5; with `S40` or in Phase 6 (developer's call).

*S13 and S16 remain open. S17, S21, S26 updated at Phase 4 lore closeout.
S20, S22, S32 resolved (see DESIGN_DECISIONS Phase 4). S33–S41 added at
Phase 4 lore closeout. S42 added at Phase 5 kickoff (2026-10-01). S41
resolved (see DESIGN_DECISIONS Phase 5). S42 facts half resolved at Phase 5
lore closeout; episodes remainder moves to S14. S35, S36, S38, and S40
updated at Phase 5 lore closeout. S43 and S44 added at Phase 5 lore
closeout. Not open questions (one line): question quiet window withdrawn
(B38); gap "no Stop" closed by P4-D29; AUD-37 closed by P4-D18 (residual
in S36); external dictation tool is test hygiene (A20). Resolved items stay
in DESIGN_DECISIONS.md.*
