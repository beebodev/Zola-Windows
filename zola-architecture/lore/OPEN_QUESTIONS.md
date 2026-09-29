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
  Partially resolved by `P3-D23`: mouth onset and release now follow real
  Hermes TTS playback presence (`TtsPlaybackMonitor`). Still open: the mouth
  cannot see pauses inside a sentence, and motion continues about 1 s after
  audible speech ends (suspected trailing silence in the sentence MP3; seen
  in two developer screen recordings; not yet measured). Shapes
  remain synthetic. The post-reply follow-up capture still uses the
  `P2-D15` estimate and Hermes's 15 s no-speech timeout (`P2-D06`). Future
  paths: a client-side scan of the MP3 ffplay is playing (envelope and
  silences); Hermes playback lifecycle events (optionally with a
  precomputed envelope). The peak meter returns 0 on this machine. Evidence: `P3-LIFE_Progress.md` Phase 5b and Phase 6;
  `P2-D14` / `P2-D15`.

- **S18 — Global push-to-talk hotkey.** `Ctrl+Space` works only while
  the window is focused. A system-wide hotkey is deferred.
- **S19 — Directed-speech detection (Master Plan §12).** Wake word is
  the primary trigger. Detecting speech meant for Zola without it,
  with addressee confidence tiers, is the long-term target. Hermes
  has no implementation (WINH09-AUD-14/15).
- **S20 — Client cannot answer Hermes clarify-tool requests.** Turns
  in which Zola asks a clarifying question stall until timeout.
  Phase 1 gap, observed in P2-VOICE: a running turn sat inside
  `clarify` for 115 s and only took a late steer, then ended
  `interrupted_by_user` with no reply text.
- **S21 — Typed Send and Cancel during speech are recorded as spoken
  interruptions.** Hermes latches "user interrupted you" for both
  (`SPEECH_INTERRUPTED_NOTE`), so Zola's next reply may act as if she
  was talked over. Confirmed in P2-SPEAK against Hermes source; no
  client handling was added.
- **S22 — Voice naturalness (pacing and inflection).** Brian wants
  Zola to sound less robotic. Options, cheapest first: a different
  Edge voice or rate (config only); reply-style shaping for speech
  (identity/prompt); an ElevenLabs streaming voice (revisits `P2`,
  and requires re-fitting `P2-D15`). Raised by Brian after the
  P2-SPEAK smoke test (2026-09-23).
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
  `_streaming` never clears (Audit 04 §1b), and the presence stays in
  `THINKING`. Phase 1 behaviour made more visible by Phase 3.
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

- **S32 — Voice active while Windows is locked (security/privacy).**
  Observed by the developer during the P3-LIFE smoke test (lock/unlock):
  Zola responds to voice while Windows is at the lock screen. Pre-existing
  P2 behaviour — the voice pipeline runs in Hermes; not caused by Track 5.
  Options: pause the wake word on lock; restrict replies while locked; keep
  deliberately. **Priority: high.** The mantra says "I protect", and a
  locked PC should not answer.
*S13 and S16 remain open. S17 updated at Phase 3 closeout; S18–S23 unchanged.
S24–S32 were added at Phase 3 closeout. Resolved items stay in
DESIGN_DECISIONS.md.*
