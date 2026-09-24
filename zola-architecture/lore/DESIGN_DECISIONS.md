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
- **P2-D02 — Speech-to-text is local faster-whisper, pinned
  explicitly.** `stt.provider: local`, `stt.local.model: base` (CPU on
  the Latitude 7430). Turns off Hermes's cloud STT fallback. Corrects
  `P2`.
- **P2-D03 — Spoken replies: Edge, default voice, on by default in
  Voice mode.** `tts.provider: edge`, `tts.edge.voice:
  en-US-AriaNeural`. The client reads `voice.toggle status` and sends
  `tts` only when speech is off, because the action flips. Hermes
  speaks; the client plays no audio.
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
- **P2-D09 — Configuration lives in the live profile, with a
  canonical copy in the repo.** Live:
  `%LOCALAPPDATA%\hermes\profiles\zola\config.yaml`. Canonical:
  `zola-architecture/identity/VOICE_CONFIG.md`.
- **P2-D10 — Optional Python dependencies are installed only with
  Brian's approval; Hermes source is never edited.** Enforced by
  `security.allow_lazy_installs: false`. Installed set is `P2-D17`.
  Hermes packaging gap: `wake.sherpa` omits `pypinyin`, which
  `sherpa_onnx.text2token` needs even for English phrases (`P2-WAKE`).
- **P2-D11 — No separate pre-build audit for Phase 2.** WINH09 already
  covered this pinned tag's voice surface.
- **P2-D12 — One owner for voice state; one listener per state; one
  utterance, one turn.** `VoiceController.cs` alone sends
  `voice.record` / `wake.*` and turns a transcript into a submit.
  `MainWindow` only forwards and renders. Running-turn
  `prompt.submit` is accepted (redirect or queue); the client submits
  once and never holds.
Phase 1 client defects fixed in Phase 2 (`P2-VOICE`):
- Each new turn overwrote the previous assistant bubble.
- Interjection/submit handling was tied to that overwrite; the
  event-driven bubble lifecycle now keeps earlier replies on screen.
### Decisions added during execution
- **P2-D13 — Runaway-loop guard.** Three consecutive spoken turns
  ended by `voice.interrupted`, with no completed turn in between,
  switch the client to Text mode with a lid/mic/speaker notice. Added
  because a closed laptop lid caused an endless self-interruption
  loop (`P2-SPEAK`).
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
