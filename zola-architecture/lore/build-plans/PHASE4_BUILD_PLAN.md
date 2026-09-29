# ZW Phase 4 Build Plan
## Conversation Safety and Voice: Lock Gate, Hermes Questions, Visible Progress, and Zola's Voice

**Base branch:** `main`
**Base SHA:** the `main` tip after the P4PRE closeout (the merge `4181f0402eaaaabf137bace3650615be00dca6af`
plus its "record merge SHA" commit). Record the actual tip at plan commit. Each track records the
actual HEAD it branches from.
**Audit:** P4PRE, merged at `4181f0402eaaaabf137bace3650615be00dca6af` (audit commit
`9a1f825cede8eae310a337d57b22393dabe26e25`). Documents in
`zola-architecture/audit/p4pre-conversation/`. 39 findings: 7 HIGH, 16 MEDIUM, 4 LOW, 12 MATCH.
**Theme:** Mixed remediation and new capability. This phase makes conversation safe, recoverable and
natural:
- Zola stops listening and speaking when Windows is locked or asleep (`S32`);
- the client answers the questions Hermes asks it (clarify and approval), on screen and by voice,
  instead of silently dropping them (`S20`);
- long turns show what she is doing, and system notices are visible with the conversation open;
- she speaks with the voice the developer chose by listening (`S22`).

This phase does **not**:
- edit Hermes (`hermes-agent` stays read-only at `v2026.9.14`);
- install anything;
- change TTS provider family (Edge + per-sentence `ffplay` stays, keeping `P3-D23` mouth timing
  intact);
- add detectors for non-interactive Windows states other than lock and sleep;
- implement whole-reply synthesis (Hermes hardcodes sentence splitting; see `P4-D24`);
- attempt audio-driven lip sync (`S17` remainder).

---

## Phase 4 Overview

| Track | Name | Scope | Complexity |
|---|---|---|---|
| 1 (`P4-LOCK`) | Lock and sleep gate | One app-level lock/sleep fact; `VoiceController` pauses wake, stops speech without an S21 latch, cancels listens, refuses voice submits; restores on unlock; honest HUD line | Medium |
| 2 (`P4-REQUEST`) | Server-request handler + cards | One handler for every Hermes server request, keyed by `srq-*` id; clarify card and approval card in the conversation panel; typed answers; declines for unhandled methods; cancel/reconnect/race rules; request log; clarify timeout 300 s | Medium-Large |
| 3 (`P4-ASK`) | Spoken questions and answers | In Voice mode she speaks a clarify question (`voice.tts`), then listens; the next transcript answers the open question through the existing transcript handler; honest presence and HUD while waiting | Medium |
| 4 (`P4-FEEDBACK`) | She never looks stuck | Tool activity line from `tool.*` events; notices visible above the conversation panel; reproduce and fix (or close) the lost spoken answer (AUD-37) | Medium |
| 5 (`P4-VOICE`) | Zola's voice | Sonia at speed 1.1 (live trial); speech-shaped replies in `SOUL.md`; blind pitch A/B via the command provider; refit `P2-D15`; record S17 silence | Medium |

**Sequencing rule:** strictly **1 → 2 → 3 → 4 → 5**. Each track merges before the next begins.
- Tracks 1–3 all modify `VoiceController.cs`, `ZolaDisplayState.cs` and `MainWindow.xaml.cs`.
- Track 2 builds the handler that Track 3 routes voice answers into.
- Track 4 changes the conversation panel and notice layout that Tracks 2–3 add cards to.
- Track 5 is last because its `P2-D15` refit must be done once, after Tracks 1, 3 and 4 have changed
  the listening windows.

Do not run tracks in parallel.

**Build command (all tracks):** `dotnet build windows-client/Zola.Client/Zola.Client.csproj -r win-x64`.
Use `-r win-x64`, never `-p:Platform=x64` (P3PRE Audit 03 §1).
**Test command (all tracks):** none. This project has no automated test suite. Smoke tests
(Cursor Part A, developer Part B, Cursor Part C) are the acceptance criteria.

---

## Grounding summary (established by P4PRE; cite, do not re-derive)

**Lock (`S32`)**
- `Presence/SessionLockWatcher.cs` raises `Locked` / `Unlocked` / `Suspending` / `Resumed` correctly
  (AUD-02). Its **only** subscriber is `PresenceView` (ctor, L211–215), which pauses rendering. Voice
  is never told (AUD-01, AUD-03).
- Live proof: she woke and answered **16.6 s after** Windows locked (L1b, AUD-30), and kept speaking
  and opened a follow-up listen through a lock (L2, AUD-31).
- The client drives every wake → capture → transcript → submit hop through `VoiceController` (AUD-04).
  Hermes speaks on its own once a turn is running (AUD-05).
- `wake.pause` releases the mic device; `wake.resume` reopens it (AUD-06).
  `ReconcileWakeRestingAsync` would auto-resume a paused wake unless it respects the lock fact
  (Audit 02 §5).
- Stopping speech: `session.interrupt` cancels the turn **and** latches `SPEECH_INTERRUPTED_NOTE`
  (S21). The `voice.toggle off` stop path uses `user_barge=False`, so **no latch** (Audit 02 §4).
- A dropped socket releases the wake lease, so an orphaned serve does not keep listening (AUD-09).
- The client cannot tell lock from UAC, screen-off or remote disconnect (AUD-08).

**Hermes questions (`S20`)**
- Clarify, approval, sudo, secret, vault and others are JSON-RPC **server requests**:
  `{"id":"srq-…","method":…,"params":{session_id,…}}`. The client answers with a response frame
  carrying the same `id` (Audit 03 §1, AUD-11). `ChatSocket.cs` L500–504 drops every one (AUD-12).
- Wire shapes: single `{"answer":"…"}` (`""` = skip); batch `{"answers":{qid:…}}`; `result:{}` on a
  batch = cancel all; JSON-RPC error = settled, not answered (Audit 03 §1, §12b).
- `request.cancel` arrives as an **event** `{id, method, reason}` with reasons
  `timeout | interrupted | shutdown | resolved | session_closed`. Unanswered requests come back in
  `open_requests` on `session.resume` / `session.activate` / `session.events.since`. The client reads
  neither (AUD-17).
- Clarify timeout today is **3600 s** (profile has no `clarify.timeout` / `agent.clarify_timeout`)
  (AUD-13). Live L6: the clarify tool blocked **83.7 s** with an empty bubble and THINKING until
  Cancel (AUD-34).
- Approval is dropped the same way and **denies after ~300 s** (fail-closed) (AUD-15).
- Typed Send is disabled while `_streaming` (`MainWindow` ~242). A voice transcript during a turn
  goes to `prompt.submit` and can interrupt and cancel an open clarify (AUD-19, Audit 03 §3).
- The clarify question is not spoken by Hermes. `voice.tts {text}` speaks arbitrary text through the
  same ffplay playback, barge-in aware (Audit 03 §7).
- She often asks questions in plain text instead of using the tool; those already work through
  `prompt.submit` (AUD-33).

**Visibility**
- Hermes emits `tool.start`, `tool.complete`, `tool.generating`, `tool.output_risk`. `ChatSocket`
  drops them (`default: return`, ~595–597) (AUD-38). The Costco turn was 36.4 s of silent THINKING.
- `StatusText` / `DetailText` sit at Z 20, under the conversation panel at Z 40 (AUD-39). The
  "Ignored a server request" note was never visible and is not written to any log file.
- L5 follow-up: the capture was open for 17 s. VAD removed the whole clip and Whisper returned
  empty (AUD-37). It is unconfirmed whether the developer spoke during that window.

**Voice (`S22`)**
- The built-in Edge path passes only `voice` and `rate` (from `tts.edge.speed`). `pitch` and `volume`
  are reachable only through a `tts.providers.<name>` command provider running the `edge-tts` CLI
  (AUD-21, AUD-22).
- Edge + per-sentence ffplay is `P3-D23` **PASS**. Streaming / sounddevice providers are **BREAK**
  (AUD-23, AUD-24).
- Sentence splitting is hardcoded (`SentenceChunker`, `min_len=20`, `.!?`). There is no config knob
  for whole-line synthesis (AUD-29).
- There is no voice-only prompt slot. Shaping goes in `SOUL.md` and so affects typed replies too
  (AUD-28).
- Measured: Sonia +10% ≈ 3.89 WPS; trailing silence median 0.387 s (corpus 0.740 s); Edge
  per-sentence synth ≈ 0.74–0.81 s (Audit 06). `P2-D15` constants are invalid at speed 1.1 (AUD-25,
  AUD-36).
- Developer listening (verbatim, Audit 06): Sonia +10%, whole over split, definitely shaped, −2 Hz
  preferred. To be confirmed live.

---

## Decisions Resolved in This Build Plan

### Lock and sleep (Track 1)

**P4-D01 — One gate fact: "voice is gated" = Windows locked OR system suspending.**
There is exactly one `SessionLockWatcher` instance. It moves from `PresenceView` to `MainWindow`,
which owns it for the window's life. `MainWindow` forwards its events to both consumers:
- the existing presence pause, with unchanged behaviour and reasons (`locked`, `suspended`);
- `VoiceController`, through one new method (for example `SetSystemGate(bool locked, bool suspended)`).

`VoiceController` holds the queryable gate state and is the only component that acts on it for
voice (`P2-D12`). `ZolaDisplayState` reads it through `VoiceController`'s public properties
(`P3-D03`). No other component reads the watcher.

Why hoist rather than add a second watcher or have `PresenceView` re-raise: lock is an app-level
fact, not a rendering detail. Two watchers would be two authorities over one OS signal. Resolves the
S32 "no queryable fact" gap (AUD-03).

**P4-D02 — On gate: pause, stop, cancel, refuse. Fail closed.**
When the gate closes, `VoiceController`, in order:
1. cancels any pending follow-up timer and echo-reopen;
2. stops any open capture (`voice.record {action: stop}`);
3. stops speech **without** cancelling the turn and **without** latching `SPEECH_INTERRUPTED_NOTE`,
   using the `voice.toggle off` stop path (`user_barge=False`, Audit 02 §4). It first records the
   prior speech state so unlock can restore it (`P2-D03`: the action flips, so read status first);
4. pauses the wake word (`wake.pause`, which releases the mic).

While gated:
- `HandleWakeDetectedAsync`, `StartCaptureAsync`, follow-up and echo-reopen refuse to start;
- `ReconcileWakeRestingAsync` must not resume wake;
- any transcript that still arrives is dropped and logged, never submitted;
- a turn already running finishes silently, and its text lands in the conversation.

If the non-latching stop path does not exist as described, or does cancel the turn, the track stops
and flags (G-ARCH). It does not fall back to `session.interrupt` without a decision. Resolves AUD-01
and AUD-05.

**P4-D03 — On ungate: restore exactly the pre-gate state; never resume a cut-off reply.**
Unlocking proves the developer is present. "Pre-gate state" means *availability*, not activity:
it records whether speech output was enabled and whether the wake word was armed, never what was
playing. When the gate opens:
- if the client was in Voice mode, speech output is re-enabled for **subsequent** turns if it was
  enabled before the gate closed, and the wake word re-arms through the existing sync path
  (`wake.resume`, or `wake.start` with the existing retry if the lease was lost);
- Text mode stays Text mode;
- audio from the turn the gate interrupted is **never resumed, replayed or re-synthesized**. Its
  text is already in the conversation.

Resume from sleep usually lands at the lock screen: `Resumed` with `Locked` still set keeps the gate
closed until `Unlocked`.

**P4-D04 — Scope is lock and sleep only.**
UAC / secure desktop, screen-off without lock, remote disconnect and fast-user-switch are not
detected in Phase 4 (AUD-08, AUD-10). Filed as new open question **S33**. No new Windows detection
APIs.

**P4-D05 — Honest HUD while gated.**
`ZolaDisplayState` shows the mic line **"Mic: paused — Windows locked"** (and "…— sleeping" if only
suspended) whenever the gate is closed, ahead of every other mic state (`P2-D08` honesty).
`PresenceMode` rules are unchanged, since rendering is already paused. This string is distinct from
the operational "Wake listening paused" (Audit 02 §11).

### Hermes server requests (Track 2)

**P4-D06 — One server-request handler for every method.**
A new `ServerRequestBroker` (one file) is the single owner of open server requests. It is keyed by
`srq-*` id, with `session_id`, `method`, `params`, received time and state
(open / answered / cancelled / declined).
- `ChatSocket` parses the string-id request branch (L500–504) and hands the request to the broker
  instead of ignoring it. It adds one method that writes a response frame
  (`{"jsonrpc":"2.0","id":…,"result":…}` or an `error`).
- `ChatSocket` routes the `request.cancel` event to the broker.
- The broker raises typed events to `MainWindow`, which renders cards.
- Per-method handlers: **clarify** (P4-D08) and **approval** (P4-D07).
- Every other method (`sudo`, `secret`, `vault.*`, `mcp.setup`, `terminal.read`, `preview.*`,
  `window.read`, `tour`, unknown) is **declined immediately** with a JSON-RPC error
  (`-32601`, "not supported by this client"), plus a visible notice and a log line. Never silence.

Why generic first: the protocol is generic (AUD-18). A clarify-only fix would grow one special case
per method. Resolves AUD-12.

**P4-D07 — Approval card: Approve once / Deny. Typed or clicked only.**
An approval request shows a card in the conversation panel, and the panel opens automatically. The
card shows:
- the command;
- Hermes's description;
- **two buttons only: "Approve once" and "Deny"**, even if Hermes offers session or permanent
  scopes. Widening standing permissions is a separate future decision (new open question **S35**).

Approval is never granted by voice, never spoken aloud, and never answerable while the gate is
closed. Hermes's own ~300 s timeout still denies (fail-closed). The exact param and result shapes
are read from source in the track's read phase. Resolves AUD-15 for Phase 4. Keeps `A3`: Hermes's
gate stays the floor, the client only surfaces it.

**P4-D08 — Clarify card.**
A clarify request shows a card in the conversation panel, and the panel opens automatically. The
card has:
- the question;
- one button per choice if `choices` is present (the Hermes "(Recommended)" marker shown as a label,
  not sent back);
- a free-text field;
- **Skip** (sends `{"answer":""}`).

Other cases:
- `multi_select`: checkboxes, and one Send.
- Batch (`questions[]`): one card with a row per `qid`. One final response `{"answers":{…}}`;
  `clarify.lock` is not used.
- After a response is sent, the card collapses to a read-only "You answered: …" record in the
  conversation.

**P4-D09 — Typing while a question is open answers it.**
While a clarify is open for the current session:
- the composer is **enabled even though the turn is streaming**;
- its placeholder reads "Answer Zola's question…";
- Send answers the open question (the newest open clarify for the current session, if several)
  rather than calling `prompt.submit`.

With no open clarify, the composer's behaviour is unchanged.

**P4-D10 — Clarify timeout 300 s.**
Profile `agent.clarify_timeout: 300`, applied by Cursor only after the developer approves the exact
line, and recorded in `VOICE_CONFIG.md` (`P2-D09`). A question left for 5 minutes is skipped by
Hermes. The card is then removed by `request.cancel` (`timeout`) with the notice "Zola stopped
waiting for an answer."

**P4-D11 — Stale, duplicate and foreign answers are impossible by construction.**
- Every answer names its `srq-*` id.
- The broker sends at most one response per id, and only while that id is open. A second Send or
  transcript for an answered id is dropped and logged.
- `request.cancel` (any reason) closes the id, removes or greys the card, and shows a notice.
- A request whose `session_id` is not the current session is not shown, and is **intentionally left
  open**. It belongs to that session and must survive session switching: its card reappears if that
  session becomes current again. Otherwise Hermes's own timeout (P4-D10) or cancel closes it. It is
  logged on arrival and on every hide/re-show. This is a deliberate exception to "never leave a
  request hanging": it is not hanging, it is parked with its own session. Do not "fix" it by
  declining.
- On `session.resume` / `session.activate`, `open_requests` is parsed and each request re-enters the
  broker as if new (re-shown). Batch `answers` already locked are pre-filled.
- Switching sessions hides, but does not answer, the other session's cards.

This covers every row of Audit 03 §12c. Resolves AUD-17.

**P4-D12 — Server requests are logged.**
New file `%LOCALAPPDATA%\ZolaClient\logs\server-requests.log`. One line per event: received, shown,
answered, declined, cancelled (with reason), dropped (with why). Fields: time, id, method,
session_id, and the question or command text. **Answer text is never logged, only its length.**
Secret, vault and sudo params are never logged beyond the method name. `Routed` notes about requests
are also written here. Closes the evidence gap in Audit 05 §3.

### Spoken questions and answers (Track 3)

**P4-D13 — In Voice mode she says the question, then listens.**
When a clarify card appears in Voice mode, the gate is open, and speech is on:
1. `VoiceController` (the RPC owner) calls `voice.tts` with a spoken rendering of the question.
   With choices: "<question> Options: A, B, or C." ("(Recommended)" removed.) Batch: first question
   only, plus "…and there are more on screen."
2. When that playback ends, it opens an answer capture: the same `voice.record` path as follow-up,
   carrying a "clarify-answer" tag.

Playback end comes from `TtsPlaybackMonitor` release (`P3-D23`), with the `P2-D15` estimate as the
fail-closed fallback. The question text joins the echo-guard haystack (`P2-D14`). Approval is never
spoken (P4-D07).

**P4-D14 — One transcript consumer routes answers.**
The existing `TranscriptReady` handler in `MainWindow`, the one place transcripts become turns today
(`P2-D05`, `P2-D12`), gains one branch. If the broker has an open clarify for the current session,
the transcript is sent as that clarify's `answer` (verbatim; Hermes interprets "the second one");
otherwise the path is unchanged.
- A stop phrase ("stop") sends Skip (`""`).
- An echo-guard drop is dropped as today.
- **A transcript from a `clarify-answer` capture is bound to the `srq-*` id that opened that
  capture** (P4-D13 records the id on the capture). It may answer only that id. If that id is no
  longer open when the transcript arrives (answered, cancelled, timed out, or session switched), the
  transcript is **dropped and logged, never submitted as a prompt**. A notice says "Your answer
  arrived after Zola stopped waiting — say it again if you still need it."
- A transcript from any **other** capture (wake, mic button, ordinary follow-up) keeps today's
  behaviour: if a clarify is open for the current session it answers it; otherwise it becomes a
  prompt.

No second submit path exists. Resolves AUD-19 and closes the late-answer race (an answer to a
cancelled question must never become a brand-new turn).

**P4-D15 — Presence and HUD while waiting for an answer.**
While a clarify is open for the current session:
- the HUD voice label reads **"Waiting for your answer"**;
- `PresenceMode` is `LISTENING` if a capture is open, otherwise `IDLE`. **Not `THINKING`**;
- the stale-thinking clock does not run.

No new `PresenceMode` value (`P3-D04` unchanged). Resolves AUD-16, and matches Attention §10
`CLARIFICATION_PENDING` in behaviour.

### She never looks stuck (Track 4)

**P4-D16 — Tool activity line.**
`ChatSocket` forwards `tool.start`, `tool.complete` and `tool.generating` (currently dropped) as
facts. `ZolaDisplayState` keeps an **ID-aware set of active tools** (keyed by the tool-call id Hermes
sends; the read phase confirms the field, and if none exists, keys by start event order, never by
tool name). Completing one tool removes only that entry. The display shows **one** string, from the
newest still-active entry, so when a newer tool finishes, an older still-running one reappears. The
whole set is cleared on turn end (`message.complete`), interrupt, disconnect, and session switch, as
a safety net for a missed `tool.complete`. The string is shown on the HUD and in the live reply
bubble while it is empty, through a friendly-name map:
- `web_search` → "Searching the web…";
- `terminal` → "Running a command…";
- `skill_view` → "Checking a skill…";
- `clarify` → no line (the card shows);
- unknown → "Working…".

The line clears on `tool.complete` or the first reply text. Any tool event counts as turn activity
for the stale-thinking clock. `PresenceMode` stays `THINKING` (truthful). Resolves AUD-38.

**P4-D17 — Notices are visible with the conversation panel open.**
The notice layer (`StatusText` / `DetailText`) renders above the conversation panel (z-order), or,
if that collides with the panel's layout, is mirrored into the panel header. The track's read phase
chooses based on the XAML and reports the choice before building. Resolves AUD-39.

**P4-D18 — Lost spoken answer: reproduce first, then fix or close.**
The track's first live step reproduces AUD-37: she asks a plain-text question in Voice mode, and the
developer answers clearly within 2 s of her finishing, five times.
- If any answer is lost, find which layer lost it (capture window timing vs VAD vs hallucination
  filter), with evidence, and fix it with the smallest change, preferring a config key over code.
- If none is lost in five tries, close AUD-37 as "not reproduced", with evidence.

In both cases the client logs every `voice.transcript` with its `filtered` flag and the capture
window times.

### Zola's voice (Track 5)

**P4-D19 — Voice: `en-GB-SoniaNeural` at speed 1.1, provisional until a live trial.**
Profile `tts.edge.voice: en-GB-SoniaNeural`, `tts.edge.speed: 1.1`. Applied by Cursor after the
developer approves the exact lines; recorded in `VOICE_CONFIG.md`. Confirmed only when the developer
passes a live trial through Hermes playback (Part B). If the trial fails, the track stops for a
decision; it does not silently revert. Supersedes `P2-D03`'s voice choice.

**P4-D20 — Speech-shaped replies in `SOUL.md`.**
Add a short spoken-style section to Zola's live profile `SOUL.md` and its canonical copy
`zola-architecture/identity/SOUL.md`, following the P1-IDENTITY process:
- plain spoken prose, contractions;
- **a short first sentence** (so the first audio starts fast);
- then fewer, longer sentences joined naturally rather than clipped fragments;
- no markdown lists, bold or headers unless asked;
- numbers and times written as she would say them.

Hermes has no voice-only slot (AUD-28), so this also shapes typed replies. That was accepted, and it
helps because bubbles show raw markdown today (S29). The exact text is shown to the developer for
approval before it is written.

**P4-D21 — Pitch: blind A/B through the command provider, kept only if it wins.**
The read phase confirms the `tts.providers.<name>` command-provider schema and that it writes an MP3
that Hermes plays through a child `ffplay`, so the monitor still sees it (`P3-D23` PASS, AUD-22). The
developer then hears the same reply at 0, −2 and −4 Hz, in random order and unlabeled.
- If a non-zero pitch wins, the command provider becomes the TTS provider, with that pitch.
- If 0 Hz wins, or the command provider fails the PASS check, or its median first-audio latency is
  more than 300 ms worse than built-in Edge, the built-in Edge provider stays and pitch is dropped.

**P4-D22 — Refit `P2-D15` for the final voice.**
After P4-D19 and P4-D21 settle, re-measure and refit `EstimatedWordsPerSecond`,
`FirstSentenceLatencySeconds`, `PerSentenceOverheadSeconds` and `FollowUpMarginSeconds` from at least
six live replies (short, medium, long; the `P2-D15` method), against ffplay-gone times. Record the
old and new values in `VOICE_CONFIG.md`'s tuning log, and record trailing silence per sentence
against `S17`.

**P4-D23 — No premium or local neural providers in Phase 4.**
ElevenLabs, OpenAI, Gemini, xAI, Piper, NeuTTS and KittenTTS need installs or keys, and the
streaming paths are `P3-D23` BREAK (AUD-24). Not in scope.

**P4-D24 — Whole-line synthesis is not in Phase 4.**
Hermes hardcodes per-sentence chunking (AUD-29). There is no config route, and Hermes is never
edited. P4-D20's "fewer, longer sentences" approximates it. Filed as new open question **S34**.

### Cross-cutting

**P4-D25 — Live profile edits are developer-approved, exact, and mirrored.**
Every Phase 4 change to `%LOCALAPPDATA%\hermes\profiles\zola\` (`config.yaml` keys in P4-D10,
P4-D19, P4-D21; `SOUL.md` in P4-D20) is proposed as exact text at a STOP point. Cursor applies it
only after the developer's approval, then records it in `VOICE_CONFIG.md` or the identity canonical
copy in the same track (`P2-D09`). The profile is backed up before each edit (a timestamped copy in
the profile folder).

**P4-D26 — Track order: Lock → Request → Ask → Feedback → Voice.**
See the sequencing rule. Confirms the P4PRE synthesis Section 5 item 14.

---

## Track 1 — Lock and Sleep Gate (`P4-LOCK`)

### Problem

Windows lock and sleep pause only the 3D presence. The wake word, capture, submit and speech all
continue. Live, she woke and answered 16.6 s after lock (L1b, AUD-30), and kept speaking and listening
through a lock (L2, AUD-31). `SessionLockWatcher` has one subscriber, `PresenceView` (AUD-01). There
is no lock fact that voice or the HUD can read (AUD-03, AUD-07).

### Files to read

- `windows-client/Zola.Client/Presence/SessionLockWatcher.cs` (all)
- `windows-client/Zola.Client/Presence/PresenceView.cs` (ctor L200–230; `PauseRendering`,
  `OnUnlockOrPowerResume`, `_pauseReasons`)
- `windows-client/Zola.Client/VoiceController.cs` (`HandleWakeDetectedAsync`, `StartCaptureAsync`,
  `CanStartCapture`, `OnFollowUpTimerAsync`, echo reopen, `ResumeWakeAsync`,
  `ReconcileWakeRestingAsync`, `SyncVoiceAndWakeAsync`, `EnterTextModeAsync`, `voice.toggle` usage)
- `windows-client/Zola.Client/ZolaDisplayState.cs` (`Recompute`, mic-line priority, `WakePausedLabel`)
- `windows-client/Zola.Client/MainWindow.xaml.cs` (ctor wiring, `TranscriptReady` handler,
  `SubmitTurnAsync`)
- Hermes, read-only: `tui_gateway/methods_voice.py` (`voice.toggle` actions and their stop path with
  `user_barge`; `wake.pause` / `wake.resume` ~525–545), `tools/tts_streaming.py`
  (`SPEECH_INTERRUPTED_NOTE`, ~46–60)
- `zola-architecture/audit/p4pre-conversation/Zola_P4PRE_Audit_02_LockSurface.md`

### Changes

**`MainWindow.xaml.cs`:** construct the single `SessionLockWatcher` (after the window handle exists).
Forward `Locked` / `Unlocked` / `Suspending` / `Resumed` to the presence pause (same reasons and order
as today) and to `VoiceController.SetSystemGate(...)`. Dispose it on close. Tag:
`// P4-LOCK: one lock/sleep watcher, app-level — P4-D01`.

**`Presence/PresenceView.cs`:** stop constructing `SessionLockWatcher`. Expose the existing
pause/resume entry points (or accept the four events) so `MainWindow` drives them. Rendering
behaviour on lock, unlock, suspend and resume is **byte-for-byte unchanged** in effect (same pause
reasons, same revalidate on resume). Tag `— P4-D01`.

**`VoiceController.cs`:**
- Gate state: `SystemLocked`, `SystemSuspended`, `VoiceGated => SystemLocked || SystemSuspended`,
  plus the pre-gate snapshot (mode, speech on/off, wake armed).
- `SetSystemGate`, which on close runs P4-D02 steps 1–4 in order and on open runs P4-D03.
- Guards in wake-detected, capture start, follow-up, echo reopen, and wake reconcile/resume.
- A drop-and-log for transcripts while gated.
- Each state change is logged to `voice-timeline.log` (`gate closed: locked`, `gate opened`, each RPC
  and result).
- Tag `// P4-LOCK: … — P4-D02` / `— P4-D03`.

**`ZolaDisplayState.cs`:** add the gated mic line from P4-D05 at the top of the mic-line priority.
Read only `VoiceController` public properties. Tag `— P4-D05`.

**`MainWindow.xaml.cs` (`TranscriptReady` handler / `SubmitTurnAsync`):** refuse voice-sourced
submits while `VoiceGated` (belt and braces with the controller drop). Tag `— P4-D02`.

**Read-phase STOP condition:** before building, report from Hermes source exactly what
`voice.toggle off` does to (a) TTS currently playing, (b) the running turn, (c) the S21 latch, and
(d) wake arming. If it cancels the turn or latches, stop and flag (P4-D02).

### Exit criteria

- [ ] Exactly one `SessionLockWatcher` instance exists (constructor search shows one call site, in
      `MainWindow`).
- [ ] Presence still pauses and resumes on lock, unlock, suspend and resume (`presence.log` lines as
      in P3-LIFE).
- [ ] Idle Voice mode → Win+L → wait 10 s → "Hey Zola, what time is it?" → **no answer**; no
      `wake.detected` → `prompt.submit` pair in the logs while locked; `voice-timeline.log` shows
      `gate closed: locked` and `wake.pause` → `paused=true`.
- [ ] Speaking → Win+L → speech stops within 1 s (developer ear + ffplay session gone in the monitor
      log); no follow-up capture opens while locked; the turn's text still lands in the
      conversation; the next turn after unlock carries **no** "user interrupted you" note (agent log
      shows no latch).
- [ ] Unlock in Voice mode → wake re-armed within 3 s (HUD "Listening for 'Hey Zola'"); "Hey Zola"
      works. Unlock in Text mode → still Text mode, mic off.
- [ ] Sleep (Start → Sleep) and wake → gate closed across sleep; after sign-in it re-opens only on
      `Unlocked`.
- [ ] HUD mic line reads "Mic: paused — Windows locked" while locked (visible at the moment of
      unlock, before re-arm).
- [ ] Voice/Text toggle, barge-in, follow-up, and the P2-D13 loop guard behave as before outside a
      lock (Phase 2 regression list).
- [ ] No changes to `TtsPlaybackMonitor`, `PresenceAnimator` or the render pipeline.
- [ ] Build passes.
- [ ] Smoke test (HUMAN-RUN Part B): L1b, L2 and L3 from P4PRE, repeated, plus sleep/wake. All pass
      per the lines above.

**Complexity:** Medium
**Primary risk:** `ReconcileWakeRestingAsync` or the Resting auto-resume re-arms the wake word behind
the gate's back after a turn ends while locked, silently reopening the mic.

---

## Track 2 — Server-Request Handler and Cards (`P4-REQUEST`)

### Problem

Hermes asks the client questions as JSON-RPC server requests, and `ChatSocket` drops every one
(L500–504, AUD-12). A clarify blocks the turn for up to 3600 s (AUD-13); live, 83.7 s of empty
bubble and THINKING until Cancel (L6, AUD-34). Approvals for dangerous commands are dropped too, and
deny after about 300 s with no sign to the developer (AUD-15). `request.cancel` and `open_requests`
are ignored (AUD-17). The composer is disabled while a turn streams, so a typed answer is impossible.

### Files to read

- `windows-client/Zola.Client/ChatSocket.cs` (frame dispatch ~480–520, `DispatchEvent` ~560–600,
  `CallAsync` frame writer, `OpenAsync` / resume handling)
- `windows-client/Zola.Client/MainWindow.xaml` and `MainWindow.xaml.cs` (conversation panel, bubble
  creation ~697+, `OnSendClick` ~242, `SubmitTurnAsync`, `OnRouted`, session switch)
- `windows-client/Zola.Client/Themes/ZolaTokens.xaml` (card styling tokens)
- `windows-client/Zola.Client/ZolaDisplayState.cs` (stale-thinking clock, only to leave it
  untouched here; Track 3 owns the waiting state)
- Hermes, read-only: `tui_gateway/server_requests.py`, `tui_gateway/server.py` (`_clarify_block`,
  approval `send_async` ~730, `open_requests` ~2787), `tui_gateway/contracts/server_requests.py`
  (**approval params and result shape**, cancel reasons), `tui_gateway/methods_prompt.py`
  (`clarify.lock`, busy input), `tools/clarify_tool.py`, `tools/clarify_gateway.py`
- `apps/shared` TypeScript request channel (reference only)
- `zola-architecture/audit/p4pre-conversation/Zola_P4PRE_Audit_03_Clarify.md` §1, §5, §12b, §12c

### Changes

**New `ServerRequestBroker.cs`:**
- The open-request map, and the states in P4-D06.
- Methods: `OnRequest(frame)`, `OnCancel(id, method, reason)`, `LoadOpenRequests(list)`,
  `Answer(id, result)`, `Decline(id, reason)`.
- Events for `MainWindow` (`ClarifyOpened`, `ApprovalOpened`, `RequestClosed`, `Notice`).
- The P4-D11 rules and P4-D12 logging.
- Thread-safe: frames arrive on the socket thread, UI on the dispatcher.
- Tag `// P4-REQUEST: … — P4-D06`.

**`ChatSocket.cs`:**
- Replace the ignore branch with a hand-off to the broker.
- Add `SendResponseAsync(id, result)` and `SendErrorAsync(id, code, message)`, which write frames on
  the existing send path.
- Route the `request.cancel` event.
- Pass `open_requests` from resume/activate replies to the broker.
- No other dispatch changes (tool events are Track 4).
- Tag `— P4-D06` / `— P4-D11`.

**`MainWindow.xaml(.cs)`:**
- The clarify card (P4-D08) and approval card (P4-D07) templates in the conversation panel, using
  existing tokens.
- Auto-open the panel.
- The composer is enabled with the answer placeholder while a clarify is open; Send answers it
  (P4-D09).
- Collapse answered cards to a read-only record.
- Notices from the broker go to the existing notice path (made visible in Track 4; until then, they
  are also written to `server-requests.log`).
- Approval buttons are disabled while `VoiceGated`.
- Tag `— P4-D07` / `— P4-D08` / `— P4-D09`.

**Live profile `config.yaml`:** `agent.clarify_timeout: 300`, per P4-D25, with a STOP for approval.
Record in `VOICE_CONFIG.md` (`P4-D10`).

**Read-phase STOP condition:** report the exact approval request params and the accepted result
shape (from `contracts/server_requests.py` and the approval code), including every choice value
Hermes offers. Confirm that "Approve once" maps to a single-use approval and that "Deny" is
unambiguous. If single-use approval is not expressible, stop and flag.

### Exit criteria

- [ ] Forced clarify (the L6 prompt) in Text mode → a card appears within 1 s of the request (log
      time); a typed answer → Hermes continues and replies using it (agent log: clarify tool
      completes with the answer; reply names the city).
- [ ] A clarify with choices → one button per choice; clicking sends that choice's text without the
      "(Recommended)" marker.
- [ ] Skip → `{"answer":""}` sent; she proceeds without the answer.
- [ ] Batch clarify (prompt: "use your clarify tool to ask me two questions at once: my city and
      my favourite cuisine") → one card, two rows, one `answers` response.
- [ ] Approval: a prompt that makes her run a command Hermes classes as dangerous (the read phase
      picks a harmless command that still triggers approval, and names it) → card; "Deny" → command
      not run (agent log); repeat and "Approve once" → runs once; a third run asks again.
- [ ] An unhandled method (read phase names one that can be triggered safely, or documents why none
      can, with a source-level test of the decline branch) → immediate error response, notice, log
      line.
- [ ] Cancel during an open clarify → `request.cancel` (`interrupted`) closes the card with a notice.
- [ ] Client restart with a clarify open (close client within 60 s of the card) → on relaunch/resume
      the card re-appears; answering it works.
- [ ] A second Send after answering → dropped, with a log line, not sent.
- [ ] Session switch with a clarify open → the card hides; the request stays open (log shows it
      parked, no response sent); switching back re-shows the card and answering works.
- [ ] `server-requests.log` has a line for every event above; no answer text in it.
- [ ] Plain-text questions (she asks without the tool) still work through normal Send (AUD-33
      regression).
- [ ] Build passes.
- [ ] Smoke test (HUMAN-RUN Part B): the list above, in Text mode.

**Complexity:** Medium-Large
**Primary risk:** thread and ordering races between the socket thread (request / cancel / response)
and the UI thread (card render / Send), leading to a card that answers a closed id or a response sent
twice.

---

## Track 3 — Spoken Questions and Answers (`P4-ASK`)

### Problem

In Voice mode, a clarify question is never spoken (Audit 03 §7), and a spoken reply becomes a new
`prompt.submit` that can interrupt and cancel the open question (AUD-19, Audit 03 §3). While waiting,
the presence shows THINKING and the stale-thinking clock runs (AUD-16).

### Files to read

- `windows-client/Zola.Client/VoiceController.cs` (follow-up capture path, echo haystack
  `P2-D14`, clock `P2-D15`, `voice.*` RPC helpers, gate from Track 1)
- `windows-client/Zola.Client/Presence/TtsPlaybackMonitor.cs` (release signal)
- `windows-client/Zola.Client/ServerRequestBroker.cs` (from Track 2)
- `windows-client/Zola.Client/MainWindow.xaml.cs` (`TranscriptReady` handler)
- `windows-client/Zola.Client/ZolaDisplayState.cs` (voice label, `PresenceMode` mapping,
  stale-thinking clock)
- Hermes, read-only: `tui_gateway/methods_voice.py` (`voice.tts` ~765–775, `_speak_text_with_barge`)

### Changes

**`VoiceController.cs`:**
- `SpeakQuestionAsync(clarify)`: builds the spoken text (P4-D13), calls `voice.tts`, adds the text
  to the echo haystack, and waits for monitor release (estimate fallback). Then it opens a capture
  tagged `clarify-answer` **carrying the `srq-*` id** it answers, with the follow-up margin. The
  capture's resulting transcript carries the same tag and id through `TranscriptReady` (P4-D14).
- Refuses while gated (Track 1) or when speech is off.
- Exposes an `AwaitingAnswer` fact (from the broker via `MainWindow`) for display.
- Tag `// P4-ASK: … — P4-D13`.

**`MainWindow.xaml.cs`:**
- On `ClarifyOpened` in Voice mode, call `SpeakQuestionAsync`.
- In the one `TranscriptReady` handler, add the P4-D14 branch (open clarify → `broker.Answer`;
  stop phrase → Skip).
- Tag `— P4-D14`.

**`ZolaDisplayState.cs`:** implement P4-D15 (label "Waiting for your answer"; `LISTENING` / `IDLE`;
stale-thinking clock suspended while awaiting). Tag `— P4-D15`.

### Exit criteria

- [ ] Voice mode, forced clarify spoken ("Hey Zola, before you answer, use your clarify tool to ask
      me which city I'm in, then tell me a good lunch spot there") → she **says** the question
      (developer ear; `voice.tts` in log); the capture opens after playback (monitor release time
      before `voice.record start`); the developer says a city → the card shows "You answered:
      <city>" and she replies about that city.
- [ ] Choices spoken as "Options: …"; answering "the second one" → Hermes receives the transcript
      verbatim and uses the second choice.
- [ ] Saying "stop" while a question is open → Skip sent.
- [ ] Late-answer race: the question is spoken and the answer capture opens; the developer presses
      Cancel (or the card is cancelled) **before** speaking; then the developer speaks → the
      transcript is dropped with a `server-requests.log` / `voice-timeline.log` line naming the
      closed `srq-*` id, the "Your answer arrived after…" notice shows, and **no** `prompt.submit`
      occurs (agent log shows no new turn).
- [ ] The question's own words picked up by the mic are dropped by the echo guard (no self-answer).
- [ ] While waiting: HUD "Waiting for your answer"; presence `LISTENING` during capture, `IDLE`
      after; no stale-thinking warning at 120 s (display-state log).
- [ ] Locked while a question is open → nothing spoken or captured (Track 1 gate); after unlock the
      card is still there and can be answered by typing.
- [ ] A normal (no-clarify) voice turn is unchanged: transcript → `prompt.submit` (Phase 2
      regression).
- [ ] Build passes.
- [ ] Smoke test (HUMAN-RUN Part B): the list above.

**Complexity:** Medium
**Primary risk:** the answer capture opens while her question is still playing (monitor release
missed, or the estimate is short), so she transcribes herself. That is the echo guard's job, but it
must be proven live.

---

## Track 4 — She Never Looks Stuck (`P4-FEEDBACK`)

### Problem

Long tool turns show only THINKING: the Costco turn was 36.4 s of silence, because `tool.*` events
are dropped (AUD-38). This is the likely source of the developer's real-world "she just sits there
thinking". System notices render under the conversation panel (Z 20 vs 40), so they are invisible
when it is open (AUD-39). In L5, a 17 s follow-up capture produced nothing (VAD removed the whole
clip); whether an answer was lost is unconfirmed (AUD-37).

### Files to read

- `windows-client/Zola.Client/ChatSocket.cs` (`DispatchEvent` ~560–600)
- `windows-client/Zola.Client/ZolaDisplayState.cs` (turn-activity clock, HUD strings)
- `windows-client/Zola.Client/MainWindow.xaml` (notice layer, conversation panel z-order) and
  `MainWindow.xaml.cs` (`OnRouted`, live bubble)
- `windows-client/Zola.Client/VoiceController.cs` (follow-up capture timing, transcript handling)
- Hermes, read-only: `tui_gateway/contracts/events.py` (`tool.*` payloads), `tui_gateway/tool_progress.py`,
  `tools/voice_mode.py` (VAD filter, hallucination filter, and their config keys)

### Changes

**`ChatSocket.cs`:** add cases for `tool.start`, `tool.complete`, `tool.generating`, raising a typed
event with tool name, id and time. `tool.output_risk` is logged only. Tag
`// P4-FEEDBACK: … — P4-D16`.

**`ZolaDisplayState.cs`:** the ID-aware active-tool set, the single display string from the newest
active entry, the clear-all on turn end / interrupt / disconnect / session switch, and the
friendly-name map (P4-D16, map as a named constant table); tool events reset the stale-thinking
clock. Read phase: report the tool-call id field in the `tool.*` payloads before building. Tag
`— P4-D16`.

**`MainWindow.xaml(.cs)`:**
- Render the activity line (HUD and the empty live bubble).
- Apply P4-D17 (the read phase reports z-order vs mirror before building).
- Tag `— P4-D16` / `— P4-D17`.

**`VoiceController.cs`:** log every `voice.transcript` with `filtered`, text length and the capture
window (start, stop, duration) to `voice-timeline.log`. P4-D18 fix only if reproduced, and the fix
is proposed at a STOP before it is built. Tag `— P4-D18`.

### Exit criteria

- [ ] "Give me driving directions to the nearest Costco" → within 1 s of each tool starting, the HUD
      shows the matching activity line; it clears when text arrives; no stale-thinking warning
      during tool activity.
- [ ] Overlapping tools (from the event log of a turn that ran two tools at once, or a prompt the
      read phase picks to cause it): when the newer tool completes while the older one is still
      running, the older one's line reappears, not blank. After Cancel mid-tool, the line is gone.
- [ ] Conversation panel open + a notice (for example, an unhandled server request, or the
      clarify-timeout notice) → the notice is visible (screenshot).
- [ ] AUD-37: five scripted voice Q&A attempts (she asks a plain-text question; the developer answers
      within 2 s). Evidence table per attempt: capture window, transcript, `filtered`. Result:
      reproduced (with the root cause, and a fix proposed and approved) or closed as not reproduced.
- [ ] No change to the PresenceMode mapping except the activity line (presence stays `THINKING`
      during tools).
- [ ] Build passes.
- [ ] Smoke test (HUMAN-RUN Part B): Costco turn, notice visibility, the AUD-37 script.

**Complexity:** Medium
**Primary risk:** the activity line flickers or sticks. Tool events can overlap, or a
`tool.complete` can be missed on interrupt, leaving "Searching the web…" on screen after the turn
ends. The line must clear on turn end and on interrupt, not only on `tool.complete`.

---

## Track 5 — Zola's Voice (`P4-VOICE`)

### Problem

The developer finds her robotic (`S22`). He chose `en-GB-SoniaNeural` at +10% by listening, and
preferred speech-shaped replies and −2 Hz (Audit 06). Speed 1.1 invalidates the `P2-D15` constants
(AUD-25, AUD-36). Pitch needs the command provider (AUD-21, AUD-22).

### Files to read

- `zola-architecture/identity/VOICE_CONFIG.md`, `zola-architecture/identity/SOUL.md`, and the live
  profile `SOUL.md` and `config.yaml` (read-only until approval)
- `windows-client/Zola.Client/VoiceController.cs` (`P2-D15` constants ~42–45, clock)
- `windows-client/Zola.Client/Presence/TtsPlaybackMonitor.cs` (to confirm PASS)
- Hermes, read-only: `tools/tts_command_provider.py` (`tts.providers.<name>` schema,
  placeholders, output handling), `tools/tts_tool.py` (provider resolution), `tools/voice_mode.py`
  (playback of command output)
- `zola-architecture/audit/p4pre-conversation/Zola_P4PRE_Audit_04_TtsPaths.md`,
  `Zola_P4PRE_Audit_06_VoiceSamples.md`
- `zola-architecture/lore/prompts/progress/P2-SPEAK_Progress.md` (the `P2-D15` fitting method)

### Changes

**Round 1, voice (P4-D19):** propose the exact `tts.edge.voice` / `tts.edge.speed` lines → STOP →
apply after approval → restart serve → developer live trial (Part B: five everyday prompts). Record
in `VOICE_CONFIG.md`.

**Round 2, shaping (P4-D20):** propose the exact `SOUL.md` section → STOP → apply to the live
profile and the canonical copy → the developer compares three replies before and after.

**Round 3, pitch (P4-D21):**
1. Read and confirm the command-provider schema, and the PASS check (a monitor log line shows the
   ffplay session for command output).
2. Propose the config block → STOP.
3. Apply it on a timestamped profile backup.
4. Run the blind A/B: the same three replies at 0 / −2 / −4 Hz, with random labels A/B/C recorded
   in the progress doc, sealed until the developer picks.
5. Keep the winner, or revert to built-in Edge per P4-D21.
6. Measure the median first-audio latency of the built-in provider vs the command provider (n ≥ 6
   each).

**Round 4, refit (P4-D22):** at least six live replies → fit → propose the new constants → STOP →
edit `VoiceController.cs` constants only → verify follow-up timing on long replies (no tail capture,
no timed-out listen). Tag `// P4-VOICE: refit for <voice/speed/provider> — P4-D22`. Record in the
`VOICE_CONFIG.md` tuning log, with trailing silence against `S17`.

### Exit criteria

- [ ] Live profile speaks `en-GB-SoniaNeural` at +10%; developer passes the live trial (Part B
      reply recorded verbatim).
- [ ] The `SOUL.md` spoken-style section is in the live profile and the canonical copy
      (byte-identical section); developer approves the before/after.
- [ ] Pitch: the blind A/B result is recorded with its label key. The final provider is either the
      command provider at the winning pitch (PASS shown in the monitor log; latency within 300 ms)
      or built-in Edge with pitch dropped.
- [ ] `P2-D15` constants refit, with the fit table (≥ 6 replies) in the progress doc. Follow-up
      opens after audible end on short, medium and long replies, with no tail captured (developer
      check).
- [ ] Mouth onset and release still follow playback (`P3-D23`): monitor log shows sessions for every
      sentence.
- [ ] `VOICE_CONFIG.md` updated: every changed key, the tuning log rows, and trailing silence per
      voice.
- [ ] No Hermes changes; no installs; `hermes-agent` `git status` clean.
- [ ] Build passes.
- [ ] Smoke test (HUMAN-RUN Part B): 10-minute natural conversation in Voice mode: no clipped
      follow-ups, no self-capture, mouth in time; the developer's verdict recorded.

**Complexity:** Medium
**Primary risk:** the command provider's MP3 is played by a path the monitor does not recognise
(not a child `ffplay` of serve), silently breaking mouth timing. It must be proven PASS before the
A/B, not after.

---

## Phase 4 Lore Closeout

After all five tracks are merged to `main`:

### DESIGN_DECISIONS.md

- Add **Phase 4 — Conversation Safety and Voice** with `P4-D01`–`P4-D26` (lore pointer, final
  values, execution corrections).
- Annotate `P2-D03` (voice superseded by `P4-D19`), `P2-D05` (clarify answers are routed, not
  submitted: `P4-D14`), `P2-D15` (refit: `P4-D22`), `P3-D04` (awaiting-answer mapping: `P4-D15`), and
  `A3` (approval surfaced: `P4-D07`).

### OPEN_QUESTIONS.md

- `S32` → **RESOLVED** by `P4-LOCK` (lock and sleep gate); residual states moved to new `S33`.
- `S20` → **RESOLVED** by `P4-REQUEST` + `P4-ASK` (clarify answered on screen and by voice;
  approval surfaced; other methods declined visibly).
- `S22` → **RESOLVED** by `P4-VOICE` for voice, rate, shaping and pitch; whole-line synthesis moved
  to new `S34`.
- `S17` → update: trailing silence per sentence for the final voice; `P2-D15` refit values; still
  open (no end-of-playback signal).
- `S21` → update: the lock gate avoids the latch; typed Cancel during speech still latches. Still
  open.
- `S26` → unchanged unless Track 4's activity work changes its visibility; note either way.
- New: **S33** non-interactive Windows states (UAC / screen-off / remote / user switch); **S34**
  Hermes per-sentence chunking (whole-line synthesis); **S35** approval scopes beyond "once"; and
  **AUD-37** if it was reproduced and not fully fixed.

### ROADMAP.md

- Mark Phase 4 COMPLETE with the plan commit, all five track merge SHAs and the final `main` tip.
- Add a Phase 5 candidate stub (scope TBD, await developer instruction). Carry forward S16, S24, S25,
  S13, S12, S31, S33–S35.

### identity/VOICE_CONFIG.md

Final `tts.*`, `agent.clarify_timeout`, command-provider block (if kept), and the `P2-D15` tuning
rows.

---

## Phase 4 Exit Checklist

- [ ] Track 1 `P4-LOCK` merged. Locked or asleep: no wake, no capture, no speech, no submit; unlock
      restores the pre-lock mode; honest HUD line.
- [ ] Track 2 `P4-REQUEST` merged. Every server request is answered, declined, or cancelled
      visibly; clarify and approval cards work by typing and clicking; reconnect restores open
      requests; `server-requests.log` complete.
- [ ] Track 3 `P4-ASK` merged. Voice-mode clarify is spoken and answerable by voice through the one
      transcript handler; waiting state is honest.
- [ ] Track 4 `P4-FEEDBACK` merged. Tool activity visible; notices visible over the panel; AUD-37
      reproduced-and-fixed or closed with evidence.
- [ ] Track 5 `P4-VOICE` merged. Final voice live-confirmed; shaping in `SOUL.md`; pitch decided
      blind; `P2-D15` refit.
- [ ] One authority per responsibility: one lock watcher (`MainWindow`), one voice gate
      (`VoiceController`), one server-request owner (`ServerRequestBroker`), one transcript consumer
      (the `TranscriptReady` handler), one display authority (`ZolaDisplayState`). Verified by
      search in each track's Part C.
- [ ] No duplicate execution paths: no second `prompt.submit` path; no second watcher; no client
      audio playback (`P2-D01`, `voice.tts` only).
- [ ] All new strings and thresholds are named constants (labels, timeouts, the tool-name map,
      error code).
- [ ] `hermes-agent` `git status` clean at every closeout; no installs (`P2-D17`).
- [ ] Every live-profile edit is developer-approved, backed up, and mirrored (`P4-D25`).
- [ ] Build passes on `main` after all merges.
- [ ] Smoke test after each track boundary (Part B per track).
- [ ] Phase 1–3 regression spot-check after Track 5: cold launch, Voice/Text toggle, barge-in,
      follow-up, sessions, presence modes, lock pause, GPU idle within 10%.
- [ ] `DESIGN_DECISIONS.md`: `P4-D01`–`P4-D26` recorded.
- [ ] `OPEN_QUESTIONS.md`: S20, S22, S32 resolved; S17, S21, S26 updated; S33–S35 added.
- [ ] `ROADMAP.md`: Phase 4 COMPLETE; Phase 5 stub added.

---

## What Phase 4 Explicitly Defers

| Item | Reason | When |
|---|---|---|
| UAC / secure desktop, screen-off, remote disconnect, user switch (S33) | No existing signal; new detection is scope growth (AUD-08, P4-D04) | Future review |
| Whole-line / paragraph synthesis (S34) | Hermes hardcodes `SentenceChunker`; Hermes is never edited (AUD-29, P4-D24) | Revisit on a Hermes upgrade or config support |
| Approval "session" / "always" scopes (S35) | Widening standing permissions needs its own decision (P4-D07) | Future review |
| Handlers for sudo / secret / vault / mcp.setup / desktop reads / tour | Declined visibly for now (P4-D06); no current need | When a feature needs one |
| ElevenLabs, OpenAI, Gemini, xAI, Piper, NeuTTS, KittenTTS | Installs or keys; streaming paths break mouth timing (AUD-24, P4-D23) | Future phase, by listening |
| Audio-driven lip sync; true end-of-playback signal (S17 remainder) | No Hermes event (AUD-26) | Future phase |
| Typed Cancel during speech latching "interrupted" (S21) | Not required by any Phase 4 decision | Future review |
| Missing `message.complete` stall (S26) | Different cause; Track 4 improves visibility only | Future review |
| Markdown rendering in bubbles (S29) | Shaping reduces markdown; rendering is separate | Future phase |
| Speaker verification (only the owner can talk to her) | Large new capability (voice biometrics) | Future phase |
| Location source (P3-D10) | Unchanged; questions like "where are you?" are now answerable | Future review |

---

## Complexity Legend

| Track | Complexity | Primary Risk |
|---|---|---|
| 1 — `P4-LOCK` | Medium | Wake reconcile re-arms the mic behind the gate after a locked turn ends |
| 2 — `P4-REQUEST` | Medium-Large | Socket/UI thread races answer a closed id or answer twice |
| 3 — `P4-ASK` | Medium | Answer capture opens during her own question and she transcribes herself |
| 4 — `P4-FEEDBACK` | Medium | Activity line sticks after interrupt or overlapping tools |
| 5 — `P4-VOICE` | Medium | Command-provider audio not seen by `TtsPlaybackMonitor`, breaking mouth timing |

---

*Phase 4 Build Plan version 1.1*
*v1.1 (2026-09-29, external review): P4-D03 speech availability vs activity; P4-D11 foreign-session*
*requests parked intentionally; P4-D14 clarify-answer transcripts bound to their `srq-*` id (late*
*answers dropped, never submitted); P4-D16 ID-aware active-tool set. Matching changes and tests in*
*Tracks 2–4.*
*Created 2026-09-29*
*Base SHA: the `main` tip after the P4PRE closeout (record at plan commit)*
*Prerequisite audit: P4PRE — merge `4181f0402eaaaabf137bace3650615be00dca6af`*
*All Phase 4 decisions were locked with the developer before this plan was written.*
*Next step: commit this plan to `zola-architecture/lore/build-plans/` on `main`, then begin Track 1*
*(`P4-LOCK`). Tracks run strictly 1 → 2 → 3 → 4 → 5.*
