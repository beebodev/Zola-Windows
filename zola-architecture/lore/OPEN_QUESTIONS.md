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
- **S17 — Precise follow-up window (end-of-playback signal).**
  Recommended as the **top Phase 3 candidate**. The post-reply
  follow-up capture starts after an estimated speaking time (`P2-D15`)
  and ends on Hermes's fixed 15 s no-speech timeout (`P2-D06`). A real
  "finished speaking" event from Hermes would let the listener open
  exactly when Zola stops, and would retire most of `P2-D14`'s echo
  heuristics and `P2-D15`'s estimate. Evidence: Track 2's six-run
  measurement table (`P2-SPEAK_Progress.md`); the echo-rule history
  (`P2-D14`); long replies opening on the tail. Options: a small
  maintained Hermes patch (end-of-playback event plus a configurable
  no-speech timeout), or client-side Windows audio metering.
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
*S13 and S16 remain open. S17–S23 were added at Phase 2 closeout. S17 is the recommended top Phase 3 candidate. Resolved items stay in DESIGN_DECISIONS.md.*
