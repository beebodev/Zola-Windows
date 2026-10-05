# Zola-Windows Design Decisions
Decisions resolved during Phase SOP Stage 2 (Decisions Locked), worked
through in conversation per the process document. IDs match
`Zola_WINH00_MasterSynthesis.md` Section 5 (the audit series' own
decision-point IDs); these carry forward into the eventual Build Plan's
`P##-D0X` numbering in Stage 3, cross-referenced there.
This file is updated as each decision-bucket closes, not written once
at the end.
## Client integration path
- **C1 — Client integration path: Path B.** Fresh native Windows client
  against JSON-RPC / `apps/shared`, running against `hermes serve`. Not
  Path A (fork `apps/desktop`), Path C (HTTP-API-only), or Path D (ACP
  stdio). Accepts `WINH02-AUD-02` (un-semvered JSON-RPC contract) as a
  standing risk rather than avoiding it via Path C.
- **C2 — Severity: HIGH.** For the default-on skill-write finding
  (`WINH04-AUD-09` vs `WINH06-AUD-02`), WINH06's HIGH stands — the
  review fork raises this above WINH04's original MEDIUM. WINH05 vs
  WINH06 identity-file findings stay additive, not relabeled.
- **C3 — Voice capture topology: single owner, consistent with C1.**
  The native Windows client is the sole JSON-RPC owner of mic/speaker
  capture (`WINH09-AUD-09`). No separate dashboard/TUI voice client
  competes for the mic. Revisit only if a companion app is added later.
  Phase 2 (`P2-D01`): "sole owner" means the Windows client is the only
  process that issues `voice.*` / `wake.*` RPCs to Zola's serve. The
  physical device handle belongs to that serve child.
- **C4 — Memory store: Extend (flat-file), with a stated long-term
  target (see `S14`).** Corrected from the original framing after
  inspecting Hermes's actual memory implementation:
  `MEMORY.md`/`USER.md` are not a database with a schema — each is a
  flat, budget-capped list of plain-text entries (2,200 / 1,375
  characters, `§`-delimited, rendered directly into the system
  prompt). "Extend" for v1 means: raise the character budget, and add
  a lightweight in-text tagging convention (e.g. `[project]`,
  `[person]`, `[car]`) so entries stay scannable — both cheap,
  config/prompt-level changes, not new engineering. MEMORY.md/USER.md
  remain the single live store for v1.
  Phase 5 (`P5-D05` / P1-D05): budget now 4400 / 4000; the `[tag]`
  convention is now in the live soul (`What I remember`).
  Phase 6: **extended.** Files remain the fact authority; the structured store sits beside them (P6-D01).
- **C5 — Identity assembly: Extend.** Zola edits `SOUL.md` content to be
  her own identity and extends `system_prompt.py`'s assembly logic
  wherever stock Hermes doesn't support what Zola needs (e.g. dynamic
  Self-Model Awareness / Relational Calibration hooks). Same shape as
  C4 — modify the live pipeline, don't build a parallel one. "Zola has
  her own identity" (content) was a non-negotiable must; this resolves
  the mechanism.
- **C6 — Session model: Live / wrap.** The Windows conversation ID wraps
  Hermes's own durable `sessions` table row directly. No separate Zola
  `SessionRecord` (foreground/background state, 30s grace, `deviceId`).
- **C7 — Layer 5 context-scoped preference records: deferred.** Not in
  the first build. Revisit in a later version.
- **C8 — "Forget" scope: defaults to Hermes's current behavior.**
  Forget is scoped to MEMORY.md only; `state.db` (raw session
  transcripts) is not redacted. Weaker than P-CASCADE — an accepted
  posture for v1, to be stated explicitly (not left as a silent gap)
  wherever the product documents what "forget" does.
  Phase 5 (`P5-D10`): superseded — forget removes the entry from whichever
  memory file holds it (`MEMORY.md` or `USER.md`); `state.db` is not
  redacted.
  Phase 6: forget now cascades through the provider; `state.db` is still not redacted (P6-D06).
- **C9/C10 — Both architecture docs written.** `Zola_Capability_Acquisition_Architecture.md`
  and `Zola_Tool_Authorization_Architecture.md` are written, covering
  the WINH06 and WINH08 domains that had no Document of Truth during
  the audit series. Drafted after `H1`–`H6` and `A1`–`A9` locked, per
  the original plan.
- **C11 — Lore tracking: created now.** This file, `ROADMAP.md`, and
  `OPEN_QUESTIONS.md` are maintained incrementally through Decisions
  Locked rather than assembled once at the end.
- **C12 — No independent content.** Pointer only to `S9`/`S11`/`C7`.
## Scope / deferral
- **S1 — Voice identity (voiceprint system): deferred, revisit later.**
  No per-speaker voice recognition for v1 — voice input is treated as
  coming from "the user" (reasonable given a Windows PC is already
  single-user via OS login). Nothing in Hermes to extend here (`WINH09`
  confirmed a full capability gap); building this later means a new
  external integration (e.g. Azure Speaker Recognition), not a modification
  of existing STT/TTS plumbing. Documented as a candidate to revisit as
  the product evolves, not ruled out permanently. Phase 2: still deferred;
  the wake word does not identify the speaker.
- **S2 — Relational Intelligence Layer: deferred.** Full five-subsystem
  build is too much for v1. Revisit once the foundation (Temporal
  Reasoning, Self-Model Awareness) is solid.
- **S3 — Calibration: blocked.** Stays blocked until the underlying SMA
  confidence/correction-signal gaps close. No standalone proxy for v1.
- **S4 — "Text the user" channel: deferred**, with intent recorded for
  later: the real requirement is Zola proactively surfacing/reminding
  the user about incoming texts needing attention — not necessarily a
  full send-capable channel. When this is picked back up, scope it as a
  notification/awareness feature first, and reassess whether a
  send-capable channel (Twilio SMS, already available in Hermes, vs
  WhatsApp/Signal) is needed at all.
- **S5 — Full-duplex voice transport: moot, not a Windows-track
  requirement.** Hermes's chained STT→Reasoning→TTS mode already matches
  the current sequential model; GPT-Live is OpenAI-based, not the
  Gemini-Live style used on Android. `WINH09-AUD-07` treated as a
  non-issue for Windows.
- **S6 — Warm-start/speculation cache: deferred.** Accept less
  speculative behavior than the Android Agent Map for now; revisit if
  responsiveness becomes a real problem on Windows/Hermes.
- **S7 — Scheduled work: use Hermes cron.** Use Hermes's existing cron
  for prepare/brief-style scheduled work rather than a separate Zola
  sidecar. Fall back to the sidecar approach in a later version only if
  cron doesn't meet actual needs (cron jobs run as full unsupervised
  `run_conversation`s — a known authority-shape tradeoff, accepted for
  now).
- **S8 — On-box training loop: confirmed non-goal, no decision needed.**
  Rest of the WINH06 Section 4 scratch-vs-inherit question remains
  blocked on `C9` (capability-acquisition architecture doc).
- **S12 — Daily Brief pipeline: not in v1.** *(Newly discovered during
  the architecture-doc annotation pass — not in the original WINH00
  Section 5 list.)* The proactive relationship-scoring / urgency-
  heuristics / brief-assembly layer described in
  `Zola_Communication_Intelligence_Architecture.md` and
  `Zola_Sms_Intelligence_Architecture.md` (Daily Brief) is deferred.
  Basic email and SMS read/send functionality is the v1 priority; the
  Daily Brief pipeline is a later layer on top of that, once basics
  work.
- **S14 — Structured memory store with tiers/confidence, projecting
  into MEMORY.md: deferred, stated long-term target.** *(Newly
  clarified while scoping `C4` for the Build Plan — not in the
  original WINH00 Section 5 list.)* This is the real long-term goal —
  something closer to the Android Memory Hierarchy's tiered,
  confidence/decay model, scaled to what Windows/Hermes actually
  needs — but is deliberately not built for v1. Building it now would
  mean designing the "real" architecture before there's any usage data
  from Zola-Windows to inform it, and a meaningful share of Android's
  six-layer complexity exists to handle signal types (environmental
  events, location history, camera-derived facts) that don't apply on
  Windows yet. Revisit once the foundational Phase 1 tracks are
  working and real usage patterns exist. When built, this store
  becomes the real source of truth and projects a curated summary down
  into MEMORY.md's flat entries so Hermes's existing prompt-injection
  mechanism keeps working unchanged.
  Phase 5 (`P5-D11`): Phase 6 primary. Adds the `S42` episodes remainder,
  P5-MEMORY capacity data (~53 chars/fact), the routing-miss pattern
  (#12), and the skills finding (no personal facts in agent-managed
  skills). `P4` to be revisited as "local only".
  Phase 6: **foundation complete, not resolved.** Built: the local store, the fact index, episodes, lexical/entity retrieval, time and forget. Still open: long-term retrieval quality (associative-recall table from Track 5); the evidence-based fact-authority migration (P6-D01).
- **S15 — Gmail OAuth (Google API), replacing the app-password
  adapter: deferred, stated long-term target.** *(Newly clarified
  while scoping Track 5 for the Build Plan — not in the original
  WINH00 Section 5 list.)* App passwords require a 2FA-enabled Google
  account and are IMAP/SMTP-based (polling, not push); real Gmail API
  + OAuth would be a proper long-term integration but is real
  engineering, not a v1-sized task. Revisit once Phase 1's
  foundational tracks are working, or sooner if the app-password path
  breaks (Google tightens or removes app-password support for the
  account in use).
- **S13 — Reading incoming SMS: not deferred, needs research.**
  *(Newly discovered during the architecture-doc annotation pass — not
  in the original WINH00 Section 5 list.)* Distinct from `S4` (Zola
  *sending* texts as a notification channel — stays deferred): the
  capability to *read* the user's own incoming text messages is a real
  v1 goal. Android reads this natively via `Telephony.Sms.CONTENT_URI`;
  Windows has no equivalent on-device access. Needs proper research
  into a Windows-viable path (e.g. Microsoft Phone Link sync, a
  Twilio-provisioned number, or another mechanism) before this can be
  scoped or locked as a build decision. Tracked as an open research
  item in `OPEN_QUESTIONS.md`, not resolved here.
## Provider / vendor
- **P1 — Conversational model: configure existing adapters.** No
  custom provider work needed. Hermes's existing registry (Anthropic,
  Gemini, OpenAI, Bedrock, Vertex, Azure, Moonshot, plus local models
  via LM Studio) already covers the Master Plan's abstraction targets,
  including live model/provider switching (`model_switch.py`). Default
  model(s) to configure get pinned down in the Build Plan.
- **P2 — TTS: Edge (free) for now; STT: local faster-whisper (see
  P2-D02).** Edge has no speech-to-text. ElevenLabs revisited later
  once there's a working baseline to compare quality/cost/latency
  against. Not a capability gap either way — Hermes supports both.
- **P3 — Email: Gmail via the existing generic email platform adapter
  (IMAP/SMTP, app password), OAuth deferred (see `S15`).** Corrected
  from the original "Hermes dedicated connector" framing after
  inspecting the repo: no dedicated/native Gmail connector exists.
  `plugins/platforms/email/` is a generic IMAP/SMTP platform adapter
  (poll inbox via IMAP, send via SMTP), authenticated with an app
  password, not OAuth — Gmail is referenced only as an example host
  (`smtp.gmail.com`/`imap.gmail.com`). For v1: configure this adapter
  with a Gmail App Password (`EMAIL_ADDRESS`, `EMAIL_PASSWORD`,
  `EMAIL_SMTP_HOST=smtp.gmail.com`, `EMAIL_IMAP_HOST=imap.gmail.com`)
  — zero new engineering, works today, gated by the same two-step
  confirmed-send pattern as `A1`.
- **P4 — No external memory provider (Honcho/Hindsight or similar).**
  Consistent with `C4` (Zola extends her own MEMORY.md store). Closes
  off the `P-3P` (provider retention/stranding) risk category before
  it becomes a build concern.
  Phase 5 (`P5-D11`): to be revisited in Phase 6 as "local only". Not
  revised here.
  Phase 6: **revised by P6-D07** (local only; the model-processing boundary stated).
## Security / hardening
**Standing trigger for this whole bucket:** every item below is
deferred on the same basis — accepted as-is for personal, single-user
use; all six get revisited together before any public release or
multi-user distribution. This is one decision applied six times, not
six independent ones.
- **H1 — No code signing for now.** Accept unsigned Windows builds
  (this Hermes tag ships unsigned by default: `signAndEditExecutable:
  false`, no Authenticode CI) and the resulting SmartScreen warnings.
  Revisit if/when this goes public.
- **H2 — Credential storage: deferred.** No Windows Credential
  Manager/DPAPI wrapping. BitLocker-at-rest accepted as the working
  credential-protection posture for a single-user machine.
- **H3 — Ship bar: deferred.** No formal blocking-items list
  established yet. Current posture (unsigned binary, no update-
  signature verification, Electron sandbox with `--no-sandbox`
  fallback) accepted for now; revisit alongside H1 before real
  distribution.
- **H4 — `state.db`/MEMORY.md encryption: deferred.** No
  application-level encryption (e.g. SQLCipher). BitLocker-at-rest
  treated as satisfying both the general "platform-standard encryption
  at minimum" and the memory-specific "must be encrypted at rest"
  bullets in Privacy Plan §9, for now.
- **H5 — Hermes default-config risks: accepted as-is.** No extra
  gating added beyond Hermes's stock behavior for skill writes/review
  fork (`AUD-02`/`08`), CLI fallbacks (`AUD-10`/`21`), or home-directory
  SOUL.md (`AUD-17`).
- **H6 — MCP/plugin secret inheritance: accepted as-is.** No
  sandboxing or privilege reduction added for third-party MCP servers.
  Hermes's existing `_build_safe_env()` behavior (deliberately
  re-injecting configured secrets into MCP subprocess environments)
  stands unchanged.
## Confirmed-action / authorization
- **A1 — Confirmed send: already decided.** Zola builds her own
  approval UI in front of `send_message_tool`/`adapter.send`, covering
  gateway chat replies as well as any other outbound send path. Treated
  as an existing product commitment (per the SMS Intelligence
  architecture's "Send Is Confirmed, Not Autonomous" requirement), not
  a genuinely open Decisions-Locked item.
- **A2 — Client-side response arbitration: no suppression for now.**
  Accept Hermes's extra speech paths (`review.summary`, child-session
  completes, heartbeat events) as-is. Observe real behavior before
  deciding whether an arbitration/filtering layer is needed.
- **A3 — Trust/Permission layer: Hermes's existing gate is enough for
  now.** No separate Zola-owned permission-checking layer added in
  front of Hermes's `approvals.mode`/danger-command overlay.
  Phase 4 (`P4-D07`): Hermes approvals are surfaced in the Windows client
  (cards); mode forced `manual` (`P4-D27`).
- **A4 — Truth/speech separation: accepted for v1.** No verification/
  formatting layer splitting fact from phrasing. Model output treated
  as both, matching Hermes's native behavior.
- **A5 — Background-review combined authority: Hermes defaults
  accepted**, consistent with `H5`. No added gating on the
  background-review fork's combined write + speak + tool authority
  beyond what Hermes ships with.
- **A6 — RIL single delivery path: moot**, consistent with `S2`'s
  deferral of the full Relational Intelligence Layer. Revisit only if
  RIL is picked back up.
- **A7 — SMA write ban: stick with Hermes's general posture.** The
  Self-Model Awareness read-only boundary is not enforced more strictly
  than Hermes's own write-authority model elsewhere in the agent.
- **A8 — Skills governance: accept Hermes's default** (`write_approval:
  False`), consistent with `H5`.
- **A9 — One policy vs path-dependent gating: confirmed moot.** `C1`
  locked a single integration path (Path B); gating is uniform by
  construction, no path-dependent split to design for.
## Phase 2 — Voice
Recorded from `PHASE2_BUILD_PLAN.md` v1.1 (`P2-D01`–`P2-D12`) and from
the three track progress docs (`P2-D13`–`P2-D17`). Full wording lives
in the plan; this section is the lore pointer plus execution
corrections and final tuned values.
- **P2-D01 — Hermes owns the audio devices; the client drives voice
  over `/api/ws`.** Mic, STT, TTS playback, barge-in, and wake
  detection run in the Zola `hermes serve` child. The client never
  opens an audio device and never uses `/api/audio/*`. Clarifies `C3`
  as annotated above. See the plan.
  Phase 3 amendment (`P3-D23`): for display only, the client may observe the
  presence of audio sessions belonging to Hermes's own player processes (TTS
  playback gating for the mouth). No audio data, no level, and no capture.
  Device ownership is unchanged.
- **P2-D02 — Speech-to-text is local faster-whisper, pinned
  explicitly.** `stt.provider: local`, `stt.local.model: base` (CPU on
  the Latitude 7430). Turns off Hermes's cloud STT fallback. Corrects
  `P2`.
- **P2-D03 — Spoken replies: Edge, default voice, on by default in
  Voice mode.** `tts.provider: edge`, `tts.edge.voice:
  en-US-AriaNeural`. The client reads `voice.toggle status` and sends
  `tts` only when speech is off, because the action flips. Hermes
  speaks; the client plays no audio.
  Phase 4 (`P4-D19`): spoken voice superseded — `en-GB-SoniaNeural` at
  speed 0.95 (was Aria / provisional Sonia 1.1).
- **P2-D04 — Starting a voice turn: "Hey Zola" first; mic button and
  `Ctrl+Space` as fallback.** Sherpa, `phrase: "hey zola"`,
  `capture: local`, `start_new_session: false`,
  `profile_routing: false`, `sensitivity: 0.6`. Directed-speech
  (`S19`) stays deferred.
  Handover correction (plan Track 3 "release and retry once" on
  `owned` is wrong): Hermes `wake.stop` releases only the caller's
  own lease. The client retries `wake.start` 3 times, 1 s apart,
  relying on dead-transport release. The old socket sends `wake.stop`
  before it is aborted (`P2-WAKE`).
- **P2-D05 — Every voice transcript is sent immediately.** Non-empty
  `voice.transcript` without a stop phrase is a user bubble and
  `prompt.submit` on the current session. No draft-and-edit.
  Phase 4 (`P4-D14`): clarify answers are routed to the open request, not
  submitted as a normal user turn.
- **P2-D06 — Follow-up listening uses Hermes as-is.** Barge-in while
  she speaks; after that, one estimated-delay `voice.record`. The
  clock is provisional; final constants are `P2-D15`. A precise
  end-of-playback signal is `S17`.
- **P2-D07 — Voice/Text mode toggle; both modes always work.** Launch
  defaults to Voice. Text composer stays enabled in both. Text mode
  turns voice and wake off. Every new `/api/ws` re-syncs Voice state.
- **P2-D08 — Voice state indicator comes from events only.** Separate
  honest mic indicator: listening for "Hey Zola" / recording /
  listening for interruptions / off. Never call the pipeline offline:
  STT is on-device; Edge TTS and the conversational model are cloud.
  Phase 3 (`P3-D03`): the voice-state label and mic line are now derived only
  by `ZolaDisplayState`. The strings and priority order are unchanged from
  Phase 2.
- **P2-D09 — Configuration lives in the live profile, with a
  canonical copy in the repo.** Live:
  `%LOCALAPPDATA%\hermes\profiles\zola\config.yaml`. Canonical:
  `zola-architecture/identity/VOICE_CONFIG.md`.
- **P2-D10 — Optional Python dependencies are installed only with
  Brian's approval; Hermes source is never edited.** Enforced by
  `security.allow_lazy_installs: false`. Installed set is `P2-D17`.
  Hermes packaging gap: `wake.sherpa` omits `pypinyin`, which
  `sherpa_onnx.text2token` needs even for English phrases (`P2-WAKE`).
  Phase 4 (`P4-D28`): `voice.barge_in` is now `false` on the live profile.
- **P2-D11 — No separate pre-build audit for Phase 2.** WINH09 already
  covered this pinned tag's voice surface.
- **P2-D12 — One owner for voice state; one listener per state; one
  utterance, one turn.** `VoiceController.cs` alone sends
  `voice.record` / `wake.*` and turns a transcript into a submit.
  `MainWindow` only forwards and renders. Running-turn
  `prompt.submit` is accepted (redirect or queue); the client submits
  once and never holds.
Phase 1 client defects fixed in Phase 2 (`P2-VOICE`):
  Phase 4 execution correction: `ReconcileWakeRestingAsync` is single-flight
  and re-checks after await (≤ 3 passes, logged) so an in-flight pause cannot
  strand wake paused (`P4-FEEDBACK` F5b / A29).
  Phase 5 (`P5-D01`): a closing follow-up window clears all of its own
  flags.
- Each new turn overwrote the previous assistant bubble.
- Interjection/submit handling was tied to that overwrite; the
  event-driven bubble lifecycle now keeps earlier replies on screen.
### Decisions added during execution
- **P2-D13 — Runaway-loop guard.** Three consecutive spoken turns
  ended by `voice.interrupted`, with no completed turn in between,
  switch the client to Text mode with a lid/mic/speaker notice. Added
  because a closed laptop lid caused an endless self-interruption
  loop (`P2-SPEAK`).
  Phase 4 (`P4-D28`): with barge-in off, the `P2-D13` self-interrupt trip
  loop no longer fires in normal Voice use.
- **P2-D14 — Echo guard (final, position-anchored rule).** Follow-up
  captures only. Transcripts under 3 words are never dropped. Digit
  tokens and list markers are stripped on both sides. Drop when an
  in-order run (at most 1 unmatched word) is at least 3 words and
  0.60 of the transcript, and ends within
  `max(3, ceil(0.25 × n))` words of Zola's most recent spoken words
  (rolling 20-word haystack). `EchoReopenLimit = 3`. History, each
  replaced after review or dry-run against logged transcripts: (1)
  P2-SPEAK shipped 0.80 bag-of-words; (2) lowered at P2-SPEAK smoke
  to 0.60 bag-of-words plus a 4-word phrase match after Whisper
  heard 'unless' as 'and less'; (3) P2-WAKE mid-smoke added a
  rolling tail and a digit-fragment rule; review showed this version
  would drop real follow-ups (e.g. 'What's the population of
  France?') and short number answers; (4) contiguous 0.80 / 5-word
  run: dry run dropped a user quoting Zola; (5) end-anchored
  contiguous: dry run missed number-heavy echoes; (6) final:
  digit-stripped, gap-tolerant, end-anchored (this rule).
- **P2-D15 — Simulated playback clock, final model.** Speech
  estimate: `FirstSentenceLatencySeconds = 3.3`, plus
  `EstimatedWordsPerSecond = 2.5`, plus
  `PerSentenceOverheadSeconds = 0.5` per sentence. Spoken-word
  weighting: digit tokens count as `max(1, digitCount)` words;
  a.m./p.m. count as 2; all-caps 2–5 letter acronyms count one word
  per letter. `FollowUpMarginSeconds = 3.0`. Fitted from six
  measured replies. The per-sentence cost is ffplay starting once
  per sentence (`P2-SPEAK`, `P2-WAKE`).
  Phase 4 (`P4-D22`): estimate is fallback-only; refit left WPS/FSL/OV
  unchanged; `FollowUpMarginSeconds` 5.0; see also `StartupWindowSeconds`
  and `S37`.
- **P2-D16 — Machine setup is a hard requirement for spoken
  replies.** Required: lid **open**, mic input 100, Windows audio
  enhancements **ON** (echo cancellation), speakers ~15, and FFmpeg
  (`ffplay`) on PATH. With the lid closed, speaker bleed reached the
  mic louder than the user's voice (about 9,600 vs 2,800–4,200 RMS).
  The built-in mic array sits in the lid bezel (`P2-SPEAK`).
- **P2-D17 — No automatic installs.**
  `security.allow_lazy_installs: false` in the Zola profile. Every
  Python or system dependency is installed only with developer
  approval. Installed set: faster-whisper 1.2.1, sounddevice 0.5.5,
  numpy 2.4.3 (accepted after an unapproved lazy install);
  sherpa-onnx 1.13.4, sentencepiece 0.2.2, pypinyin 0.55.0;
  FFmpeg 9.0.2 via winget.
### Final tuned values
Whisper `base`; Edge `en-US-AriaNeural`; `silence_duration` 1.5;
clock as `P2-D15`; `EchoReopenLimit` 3; wake `sensitivity` 0.6
(0 false wakes in 10 min of video audio, seated in front of the
laptop, 2026-09-24). Canonical table:
`zola-architecture/identity/VOICE_CONFIG.md`.
## Phase 3 — Presence UI
Recorded from `PHASE3_BUILD_PLAN.md` v1.7 (`P3-D01`–`P3-D22`) and from the five
track progress docs. Amendments approved during the tracks are folded in
(`P3-D17` dock, `P3-D14`/`P3-D22` life and mouth, plus new `P3-D23` and
`P3-D24`). Full wording for the original decisions lives in the plan; this
section is the lore pointer plus final values and execution corrections.


- **P3-D01 — The GLB replaces the SVG as Zola's canonical visual on Windows.**
  `zola.glb` (SHA-256 `1edf2bf5898528fd405cd3131fcf75548c6d5d1e893501467c65845b5d7a054b`,
  33,972,240 bytes) is the presence. The SVG
  reference is not a Windows target. Supersedes SVG coordinate rules, the
  "no realistic 3D model" non-goals, and Compose/Canvas mechanics for
  Windows. Presence-first design, state-down pipeline, restraint, reduced
  motion, and performance discipline still bind.

- **P3-D02 — Engine: Helix Toolkit 3.1.2 (Set A), native in-process.**
  Packages: `HelixToolkit.WinUI.SharpDX` 3.1.2 and
  `HelixToolkit.SharpDX.Assimp` 3.1.2. `Viewport3DX` is constructed in code,
  never XAML. Track 4 then replaced the lit PBR path with the approved unlit
  look (`P3-D20`). WebView2 + three.js and Unity were ruled out.

- **P3-D03 — One display-state authority: `ZolaDisplayState`.**
  `ZolaDisplayStateModel` is the only place that turns runtime facts into the
  voice-state label, mic-indicator line, Voice/Text mode word, mic-button
  enablement and content, and `PresenceMode`. It reads `VoiceController`
  public properties; the window pushes facts through one
  `UpdateWindowFacts(...)`. `ApplyVoiceChrome` is assign-only.
  `VoiceController` keeps listeners, `voice.*` / `wake.*`, and
  transcript-to-submit (`P2-D12`). Label and mic-line strings and order match
  Audit 01 §3.

- **P3-D04 — `PresenceMode` values and mapping (Windows addition: `DORMANT`).**
  Modes: `IDLE`, `LISTENING`, `THINKING`, `SPEAKING`, `ALERT`, plus `DORMANT`.
  Priority (first match): unreachable → `DORMANT`; switch/history → `IDLE`;
  `Speaking` → `SPEAKING`; streaming → `THINKING`; transcribing / capture /
  listening → `LISTENING`; Text mode or unavailable → `IDLE`; else `IDLE`.
  `Speaking` outranks streaming for presence; the HUD voice label keeps its
  Phase 2 order (streaming before Speaking). `ALERT` is defined but never
  produced this phase (`S25`). Final Dormant look: `Blink both` held at 0.30,
  brightness ×0.50, no blinks at rest.
  Phase 4 (`P4-D15`): awaiting-answer / waiting-for-user maps into presence
  and HUD while a clarify is open.

- **P3-D05 — Model gaps: approximate what the asset supports, defer the rest.**
  Built: blink, expression morphs, speaking mouth, brightness per mode.
  Dropped by developer (`P3-D22`): breathing and head motion. Deferred to
  `S24`: micro-saccade, hair strand shimmer, projection/hologram layers,
  frown and eye-softness targets.

- **P3-D06 — The HUD shows only true state; everything else is hidden.**
  Shown: VOICE block (label + mic line), TIME, SESSION, LINK, notices.
  Hidden for lack of source (`S25`): attention, momentum, emotional tone,
  system health, environment, version, encrypted link, location, Core
  Systems destinations.

- **P3-D07 — Identity text is kept, as an explicit exception to §14.**
  ZOLA wordmark, three-line tagline (`PERSISTENT` / `CONVERSATIONAL` /
  `INTELLIGENCE`), mantra, OBSIDIAN INTERFACE. Waveform space reserved and
  left empty (`S27`). Mantra indent final token `100,0,0,0`.

- **P3-D08 — Visual tokens, fonts and scale.**
  Colours, type, and spacing live in `ZolaTokens.xaml`. Rajdhani (Regular +
  SemiBold) with OFL; Orbitron wordmark not used. Conversation overlay max
  width 440 / fraction 0.45. Overlay opacity 0.94.

- **P3-D09 — Idle performance budget: ≤ 10% GPU on the Latitude 7430.**
  Idle life (blinks; particles if kept) averaged over 60 s, sum of GPU-engine
  utilization for the client process. Final idle with blinks, particles
  dropped: avg **2.2725%** / max 12.7560. Static approved look (LOOK): avg **0.0013%** / max 0.0771. Dormant at rest: avg **0.0005%** / max 0.0315. Speaking is recorded, not scored against the idle
  budget (e.g. ~33.6% at speaking tick 33 ms).

- **P3-D10 — Location is not shown.** No Windows source; privacy. Revisit
  with `S25`.

- **P3-D11 — Layout: full presence, conversation on demand.**
  Full-window presence; HUD; dock (hidden until needed, `P3-D17`);
  conversation and sessions overlays. Default 1280×800; minimum 900×640.


- **P3-D12 — Asset storage.**
  `zola.glb` in plain git at `Assets/Presence/`; `.gitattributes` binary; no
  LFS.

- **P3-D13 — Fidelity is judged by the developer against the Android
  reference.** Texture size tested; **2048²** kept (cold rest 809 MB <
  900 MB gate; 1024² not run).

- **P3-D14 — Speaking mouth is procedural; shapes are synthetic.**
  Viseme-band blend with springs; jaw and mouth morphs only while speaking.
  Timing is no longer the `P2-D15` estimate alone — onset and release follow
  observed TTS playback (`P3-D23`). Final mouth values (Round 4 baseline,
  baked): step 150–250 ms; `jawBase` 0.02 / `jawRange` 0.10; `levelMin`
  0.1 / `levelMax` 0.85; OpenAH / MidOpen gains 0.5; ClosedMBP 0.6; TeethFV
  0.3; `wideEeScale` 0; Round OO chance 0.3 / weight 0.35;
  `releaseStiffnessScale` 2.5; `engine.speakingTickIntervalMs` 33. Real amplitude and in-sentence pauses remain
  `S17`.

- **P3-D15 — Carry-over: remove dead echo constants.**
  Removed unused `EchoContainmentRatio`, `EchoMinWords`, and
  `EchoPhraseWords`. Live echo rule remains `P2-D14`. `VOICE_CONFIG.md`
  rows marked `Removed (P3-STATE)`. Comment tidy completed in this lore
  closeout.

- **P3-D16 — No `hermes-agent` edits; no Python installs.**
  Carries forward `P2-D10` / `P2-D17`. hermes-agent stayed clean at
  `345cd2b057a452236de401d3534b8502a7465e8d` through every track closeout.


- **P3-D17 — The dock is hidden until needed (v1.4; Track 4 amendment).**
  Fades in when the pointer is inside the dock footprint plus
  `DockRevealMargin` **12**, or keyboard focus is in the dock, or the
  conversation/sessions overlay is open, or a turn is streaming. Fades out
  after `DockHideDelaySeconds` **2**; fade `DockFadeMilliseconds` **180**
  (instant with reduced motion). Hidden is opacity 0 (not `Collapsed`).
  Visibility is decided by pointer position against the inflated footprint
  (hysteresis via the hide delay). One decider: `UpdateDockVisibility`.
  Supersedes the plan’s full-width `DockRevealZoneHeight` strip.

- **P3-D18 — The notice line fades; problems stay.**
  New messages show, then fade after `NoticeHoldSeconds` **4**. Sticky while
  unreachable, switch in flight, history pending, or last turn errored.
  `DetailText` only while sticky. One decider: `UpdateNoticeVisibility`.


- **P3-D19 — ACES Filmic tone mapping as a custom post-effect.**
  Narkowicz 2015 ACES in `AcesTonemap.hlsl` / `.cso`, compiled once with
  `fxc`, embedded resource, fail-closed. Final LOOK-era CSO SHA-256
  `a9484343031bdde5dd2d1b09137e91791b6cc30000b5bc82a5882af72014e9e3`
  (1948 bytes). Background compositing later moved
  into this pass (`P3-D24`).

- **P3-D20 — Texture-driven presence look (developer-approved 2026-09-25).**
  Pipeline: Helix unlit albedo; sRGB decode × gain **4.4** → ACES → sRGB
  encode; mip LOD bias **0.75**; texture **2048²**. Lights, bloom, and rim
  off. Look-defaults fingerprint (DEBUG):
  `4392a2e0d851dc1e962c4ac5bfedf837e51c1645ed18d8bb044388fe346e83d8`.
  Developer approval, verbatim: "dark skin carrying
  gold from her own texture, white-gold eyes, glowing diamond and lit hair
  tips; dots softened; reads like Android." Process lessons (kept): read the source implementation
  before tuning toward a reference; judge only raw live captures, never
  scaled composites; every tuning candidate is a complete configuration
  applied from a reset.
  Background field after Track 4 still sampled `7,7,7`; exact token
  `#080808` is `P3-D24`.

- **P3-D21 — Backdrop and decoration deferred.**
  No warm glow, floor rings, or corner brackets. Clean field from the
  background token. Particles moved to Track 5 and were later dropped
  (`P3-D22`). Filed as `S30`.

- **P3-D22 — Track 5 motion follows Android's actual 3D behaviour.**
  Channels on Windows: blink, expression, brightness (tone-map gain
  multiplier), speaking mouth. Developer decisions, verbatim: Breathing:
  "None. Not necessary for AI to breathe." Head motion: "None. The model
  wasn't made for it." Full key surface (developer,
  verbatim): "I want to make sure we are actually exposing all the keys and
  not limiting ourselves to what Android was using."
  Android values were starting points; finals below. Particles: built as a
  droppable last phase; float/Composition Forever amendment superseded when
  the developer dropped them, verbatim: "I'm almost thinking that we don't
  need the particles. Zola's image speaks for itself." Life approved, verbatim: "blinks and expressions feel natural
  in every mode, the mouth follows her voice with restrained, natural
  movement, and she stays composed. Alert reads as attentive, not
  startled."
  Final tuned values (named constants in `PresenceLife.cs`):
  - Blink: close 120 / open 180 ms; interval 3000–8000; Thinking
    2000–4500 half-blink depth 0.4; mix Both=1; Dormant lid rest 0.3.
  - Expression: Listening BrowRaise 0.4; Thinking BrowFurrow 0.15; Alert
    WideEyes 0.35 / BrowRaise 0.3 / NostrilFlare 0.1 / WideEE 0; ease
    300 ms. ALERT is placeholder-safe until a Windows trigger exists
    (`S25`).
  - Brightness: Idle 1.0 / Listening 1.1 / Thinking 0.75 / Speaking 1.0 /
    Alert 1.25 / Dormant 0.5; Speaking pulse amp 0.05 period 1200 ms;
    ease 600 ms; stagger eyes 0 / brightness 450 / expression 850 ms.
  - Mouth: see `P3-D14` / `P3-D23`.
  - Engine: tick 16 ms idle / 33 ms speaking.
  - Particles: dropped.
  - Life-defaults fingerprint:
    `ef3c2c6eb9894a4fb83d473ba69bfba6e88e44f4ab4da69d88c3585510189777`.
  - Key count: **186 DEBUG / 185 Release**.


- **P3-D23 — Mouth timing from observed TTS playback (`TtsPlaybackMonitor`).**
  (New; Track 5 amendment.) The `P2-D15` first-sentence guess (3.3 s) was
  not a reliable audible-onset anchor: estimate-based onset was both late
  and early in tuning. Measured Armed hold until
  first owned playback segment: **2.3–3.2 s** on multi-sentence turns
  (n=3: 2361–3176 ms); longer tool-style holds are allowed with no timeout.
  S17 analysis pass (5 multi-sentence replies, 20 Hz session enumeration):
  first owned playback after SPEAKING 2.4–4.6 s typical (median 2.6 s),
  63.8 s on a tool-heavy turn; inter-sentence gaps median 110 ms, max
  138 ms, plus one real 6.5 s mid-reply pause. The earlier S17 report
  measured 6.1–8.6 s against the 3.3 s estimate. These set the no-timeout
  Armed hold and the 450 ms bout bridge.
  Monitor: ownership by the Hermes serve process tree; poll at 20 Hz; stop
  when the owned session goes Inactive; bout bridge
  `releaseDebounceMs` 450. Mouth state machine: Armed
  (`SpeakingPlaybackArmed`) holds the THINKING look until first playback;
  then Active; `speakingPauseShowsThinking` defaults to false. Forced
  release on cancel / interrupt / SPEAKING clear / pause / scene loss.
  Fail-closed: if the monitor is unavailable, fall back to the estimate
  onset; SPEAKING clear always releases. Peak meter: interface obtained,
  level always 0 — dropped. Cross-reference: `P2-D01` display-only
  amendment.

  Phase 4 (`P4-ASK` / `P4-FEEDBACK`): monitor bout start/stop is also a
  **control input** for clarify-answer capture and reply follow-up release
  (via `PresenceAnimator` pass-through). Forced releases are flagged (A18).
- **P3-D24 — The background is composited by the tone-map pass.**
  (New; Track 5 amendment.) Brightness multipliers made the old
  clear-colour invert compensation unworkable in 8 bits. The approved
  look’s field had been displaying `#070707` (invert of the token); it is
  now exactly `#080808` from `ZolaBackground`. Scene alpha is binary for
  this asset; the shader lerps `lerp(ZolaBackground, toneMapped(rgb),
  sceneAlpha)` with output A=1. Fail-closed stays an opaque token clear.
  CSO SHA-256 old
  `a9484343031bdde5dd2d1b09137e91791b6cc30000b5bc82a5882af72014e9e3`
  (1948 bytes) → new
  `89aa36150afc317544377d8b4b7235ea7b70f19da540cebe3ca5acefc3c298c8`
  (2024 bytes). Invert helpers and constants removed. Look fingerprint
  unchanged (`4392a2e0…`). Amends `P3-D19`/`P3-D20` for the background
  only; bust look unchanged.

### Machine notes (Latitude 7430)
- Idle GPU (blinks, particles dropped, 60 s): avg **2.2725%**.
- Static GPU (approved look, 60 s): avg **0.0013%**.
- Speaking GPU (tick 33 ms, 60 s proxy): avg ~**33.6%**.
- Dormant GPU (60 s): avg **0.0005%**.
- Cold resting memory (LOOK, 2048²): WS **809 MB** / private 742 MB; peak
  during load **1004 MB**; import 906 ms / wall 2388 ms.

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
  Phase 6: stand (P6-D08).

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
  Phase 6: stand (P6-D08).

- **P4-D28 — `voice.barge_in: false`.** (New; `P4-ASK` Option A.) Stops the
  full-duplex barge listener from latching spoken clarify answers. Cost:
  talk-over no longer stops her (`P4-D29`). Side benefit: no `P2-D13` trips.
  Applied under `P4-D25`.
  Phase 5 (`P5-D08`): stands.

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

- **P5-D03 — She saves lasting facts on her own.** **Amendment.** The "What
  I remember" section is **identity-voiced** (not the plan paragraph's
  "outranks" phrasing). Brian revised it at the P5-MEMORY Phase 3 STOP,
  adding "I save what Brian tells me, what we clearly decide, and what I've
  confirmed; I don't turn guesses or assumptions into facts" and "When Brian
  corrects something or it changes, I update the existing fact instead of
  keeping both versions." The pre-agreed fallback priority sentence was
  **not needed**. Results: lasting 6/6, trivial 0/4, explicit 2/2, correction
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
  Phase 6: stands, restated in P6-D02 rule 8.

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
  Phase 6: forget now cascades through the provider; `state.db` is still not redacted (P6-D06).

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

## Phase 6 — Memory She Lives With
Recorded from `PHASE6_BUILD_PLAN.md` v1.1 (`P6-D01`–`P6-D08`, Appendix A),
the P6PRE audit (merge `92dc707ac047d2808b9f1848bb0e31f96689065a`), the
working decisions snapshot (`PHASE6_DECISIONS_snapshot.md`), and the
progress docs `P6-CALC` through `P6-FIX-2`. Full locked wording stays in
Appendix A / the snapshot; this section is the lore pointer, track
amendments, and measured limits.

- **P6-D01 — Two kinds of memory, one authority each.** **As locked.**
  `USER.md`/`MEMORY.md` stay the authority for current durable facts
  (memory tool only). A Zola-owned local store holds (a) a structured fact
  index rebuildable from the files and (b) episodes (store is sole
  authority). Episodes may reference facts; they never create or change
  them. Phase 6 retrieval surfaces episodes and temporal context, not a
  second copy of current facts. Fact-authority migration is a future
  evidence-based decision. **Brian's verdict:** "I agree"

- **P6-D02 — Memory invariants.** **As locked** (eight rules: one author
  each for facts and episodes; episodes never mutate facts; entities
  organize only; timestamps record only what's known; correction preserves
  history / forget erases; retrieval never becomes persistence; raw
  conversation is evidence). Rule 8 keeps `P5-D06` (search past
  conversations only when asked). **Brian's verdict:** "With that
  correction to Rule 8, I would record P6-D02. I wouldn't change Rule 6
  yet; your note captures exactly what the later forget decision needs to
  solve."

- **P6-D03 — A Zola-owned local memory provider (amended by P6-D06).**
  **As locked, then amended.** Own provider (not Holographic); profile
  plugin `zola_memory`; repo source `hermes-plugins/zola_memory/`; local
  SQLite + FTS; no new installs. Model-facing tools: none, **amended** to
  one erase-only forget operation. Must not depend on unreliable Windows
  `on_session_end`. **Brian's verdict:** "yes." Amendment with D06:
  "lock with amendment".

- **P6-D04 — Episodes are written by a background summarizer inside the
  provider.** **As locked.** Host-owned plugin LLM; pending-turn queue;
  consolidate on quiet gap / startup / pre-compress / session end if it
  fires; never reads `state.db`; commit only if pending unchanged;
  bounded retry. `event_time` only when stated or from an authoritative
  system source. **Brian's verdict:** "lock"
  **G-BRIAN-ONLY note:** only `tui` + empty-parent turns become pending /
  episodes (same allow-list as ambient time).
  **Blind test:** first S1 run **failed** (Miata split into two episodes;
  "yesterday" lost to the Unix-float timestamp bug); **C2** (rerun after
  7-FIX: normalize Hermes unix floats; significance/`plan` rule)
  **passed** — Miata+belt one episode, `event_time=2026-10-04` /
  `stated` / `yesterday`; Brian summaries "good". Prefetch p95 ~1.7 ms.
  **P6-FIX-2 note:** phrase table adds "last weekend" → Sat–Sun interval
  (`YYYY-MM-DD/YYYY-MM-DD`, displayed "the weekend of Oct 3–4"; Ashford
  ✅). Merge `fa6c7f078ab988a5c07c992f53f4c77b34521f5f`.

- **P6-D05 — Ambient, system-stamped time.** **As locked.** Per-message
  local stamp via `pre_llm_call`; cross-session gap via content-free
  `last_interaction_at`; relative ages at read time; never invent unknown
  event times; never read stamps aloud. `MeaningfulGapMinutes = 30`
  tunable. Smoke: stamps on trivial turns; gap awareness; no spoken
  readout. **Brian's verdict:** "Yes. I would put both into the build
  plan, and I think the `last_interaction_at` marker is the correct
  solution."
  **P6-FIX-WHEN note:** SOUL line — when recalling a past conversation,
  mention roughly when (merge `a2900eefae3b45222510962d5eb640e7641a0727`,
  landed before a spoken-when PASS — recorded error). **P6-FIX-2 note:**
  episodes-block cue asks her to mention roughly when if she uses an
  episode. **R6 PASS** ("We settled that yesterday.") used a
  Brian-approved one-day backdate of the kiln episode's
  `source_user_time`/`recorded_at` (deviation, not a natural cross-day
  result). Same-day recall may still omit "when".

- **P6-D06 — Forget erases every copy the memory system controls.**
  **As locked with amendment.** Recognition fails closed; cascade deletes
  every provider-controlled copy (index, history, FTS, links, pending,
  whole episodes); content-free tombstones only; `state.db` not redacted
  (`P5-D10` stands); confirmation mentions chat history remains. Episode
  memory: one erase-only `forget_memory` tool (amends D03). Proven across
  Track 4 (mechanism) and Track 5 (live episode forget + paraphrase via
  fact-ref cascade). **Brian's verdict:** "lock with amendment"

- **P6-D07 — P4 revised: memory local; no third-party memory service.**
  **As locked.** Persistent memory stays on-machine; no Honcho/Hindsight/
  mem0/etc. Episode consolidation may resend pending turns through the
  host-owned model path (same trust boundary as conversation) — model
  processing, not off-device memory. At-rest encryption stays deferred
  (H4). **Brian's verdict:** "lock"

- **P6-D08 — Math without code; approvals unchanged.** **As locked.**
  Bounded `calculate` tool in `zola_tools` (no eval/shell/side effects;
  fails closed); outside the approval gate by contract. `approvals.mode:
  manual`, `P4-D07` and `P4-D27` stand. Resolves the arithmetic case of
  `S35` only. Live: three arithmetic prompts, zero cards; control still
  cards. **Brian's verdict:** "lock"

- **P6-D09 — Forget authority (G-AUTHORITY + G-LABELS).** **Adopted Track
  4.** **Brian's verdicts (verbatim, `P6-FORGET_Progress.md` Phase 3
  approval):** "1 G-AUTHORITY adopt. 2 G-LABELS adopt, F6
  transcript/state.db persistence of args + labels accepted knowingly."
  **G-AUTHORITY:** `confirm=true` runs only when (forget intent or an
  active clarification hold) **and** every `target_id` is in the transient
  candidate set from the latest authorized `confirm=false` for this
  provider instance (plus `is_brian_conversation()`).
  **G-LABELS:** `confirm=false` labels are minimal disambiguators only;
  never persisted by the provider (not logged, tombstoned, or written to
  `meta`); never echoed after `confirm=true` (IDs/kinds/counts only). F6
  transcript/`state.db` persistence of tool args and candidate labels is
  accepted knowingly.
  **G-BRIAN-ONLY note:** `forget_memory` schema omitted after init and
  execution refused (`refused_reason=platform`) for cron/non-Brian agents
  (not `tui` + empty parent).
  **Extension (Track 5):** after `ask_brian=true` she bypassed asking via
  memory-tool `remove` (Larkspur episode lost). Brian adopted a
  `pre_tool_call` guard blocking memory-tool remove/replace while an
  `ask_brian` hold is unresolved. **Brian (verbatim):** "I agree. Yes."
  ⚠️ Guard **not fired live** in later smoke (she asked); unit-tested.

- **P6-D10 — Physical erasure (G-ERASE).** **Adopted in Track 5
  (Brian).** After every cascade, consolidation commit, and zero-match
  forget: `secure_delete=ON`, FTS5 secure-delete, and
  `wal_checkpoint(TRUNCATE)` (commit before checkpoint). Approved
  deferred-sanitize safety net when checkpoint is busy. ⚠️ Live
  `action=defer` count **0** in smoke (never busy); unit defer→success
  covered.

- **P6-D11 — Phase-track backups are deleted after merge.** **Brian
  (closeout, verbatim):** "delete old ones and track passes." Forget
  cannot reach backups, so backups are deleted at each track's closeout
  after merge. Phase 6 backups are deleted at this lore closeout (Phase 6
  STOP delete list).

### Known limits
- **AUD-24:** `session_search` "when" strings omit timezone (Hermes-side;
  no pin edit).
- **Wordless paraphrase → episode:** caught only via `episode_fact_refs`
  (D2' erased after notebook remove; accepted caveat).
- **Notebook-fact clarification:** model judgment (Mara asked; two Rosas
  in one sentence did not); enforced ask exists for episode memory /
  after forget lookup flags `ask_brian`.
- **Same-day recall** may omit spoken "when" even when prefetch supplies
  it (FIX-WHEN / FIX-2 cue; R6 PASS was seeded cross-day).
- **Associative/paraphrased episode retrieval:** 0/4 under fixed blind
  queries (shared words Q2=0, Q3=1, Q4=0, Q5=0) — retrieval-quality limit;
  OQ in Phase 3. Direct lexical recall passed.
- **forget_guard / deferred-sanitize:** not observed live (unit-proven).

### Background-review skills (closeout)
Brian (verbatim): "Keep" — `communication/conversation-memory` and
`communication/everyday-assistance` (procedural; 0 personal facts).
Whether autonomous skill edits need a policy → OQ (Phase 3).

### Phase 6 execution notes
- Deploys must verify **every** Hermes process restarted (stale serve kept
  old modules).
- Module-level provider state is unsafe — one provider per agent; resolve
  via the session registry (identity-checked put/rekey/remove).
- Hermes message timestamps are Unix floats (normalize at write).
- Prompts must say **"merge only on PASS"** (FIX-WHEN merged before spoken
  when PASS — recorded).
