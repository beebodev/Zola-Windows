# ZW Phase 2 Build Plan
## Voice — Wake Word, Local Speech-to-Text, Spoken Replies, Text Fallback

**Base branch:** `main`
**Base SHA:** `8964bdce9a7361e3887a43b3dd381f5f979e9a64` (`main` HEAD at plan
drafting, after the Phase 1 lore closeout. This plan's own commit will move
`main` ahead of it. Track 1 records the actual HEAD it branches from, the same
way Phase 1 tracks did.)
**Audit:** none. The voice surface of the pinned Hermes tag (`v2026.9.14` /
`345cd2b057a452236de401d3534b8502a7465e8d`) was already audited in `WINH09`
(merged to `main` at `da6c35fd997487db23bb15c08eb9056e28413e39`). Planning
re-read the source files listed below on 2026-09-22 and found nothing that
contradicts WINH09. Each track's Phase 2 (Read and Understand) is its
grounding pass, as in Phase 1. See `P2-D11`.
**Theme:** New-feature work. Makes voice the primary way to talk to Zola on
Windows: a "Hey Zola" wake word, a mic button and hotkey as fallback,
on-device speech-to-text, spoken replies with barge-in, and a short
follow-up listening window after each reply. The text composer stays fully
working in both modes. It is a fallback, not removed. This phase wires the
client to Hermes's **existing** voice pipeline. It builds no new
speech-to-text, text-to-speech, or audio engine, and it does **not** attempt
directed-speech detection (Master Plan §12), voice identity (`S1`), the
Obsidian Interface theme, or Google Workspace (`S16`).

---

## Phase 2 Overview

| Track | Name | Scope | Complexity |
|---|---|---|---|
| 1 (`P2-VOICE`) | Voice core | Zola profile voice/STT config + dependency check; client drives `voice.toggle`/`voice.record` over the existing `/api/ws`; mic button + hotkey; transcript → `prompt.submit`; voice state indicator; Voice/Text mode toggle | Medium-Large |
| 2 (`P2-SPEAK`) | Spoken replies + follow-up | Turn spoken replies on in Voice mode; handle barge-in (`voice.interrupted`) and interjection transcripts; follow-up listening window after each spoken reply | Medium |
| 3 (`P2-WAKE`) | "Hey Zola" wake word | Wake-word config (sherpa, "hey zola", local capture, continue current session) + dependency check; client arms/re-arms `wake.start` per socket and starts capture on `wake.detected` | Medium |

**Sequencing rule:** Track 1 must merge before Track 2 or Track 3 begins.
Tracks 2 and 3 both need Track 1's voice controller and its `voice.*` event
plumbing. Tracks 2 and 3 do not depend on each other's behavior, but both
modify the same new client files (`VoiceController.cs`, `MainWindow.xaml(.cs)`).
**Run them sequentially: 1 → 2 → 3.** Do not run them in parallel.

**Build command (all tracks):** `dotnet build windows-client/Zola.Client/Zola.Client.csproj`
**Test command (all tracks):** none. This project has no automated test
suite (same as Phase 1). The smoke tests are the acceptance criteria.

---

## Grounding summary (what Hermes already provides at the pinned tag)

Recorded so every track prompt can cite it instead of re-deriving it.
Planning read every item below in source on 2026-09-22.

- **`/api/ws` already carries voice.** `/api/ws` is `tui_gateway.ws.handle_ws`
  (`P1-D02`). `tui_gateway/methods_voice.py` registers these handlers on that
  same socket:
  - `voice.toggle` (`status` | `on` | `off` | `tts`, lines 614–682)
  - `voice.record` (`start` | `stop`, lines 705–764)
  - `voice.tts` (lines 767–777)
  - `wake.start` / `wake.stop` / `wake.pause` / `wake.resume` / `wake.status` / `wake.feed` (lines 451–611)
  - `ping` (line 444)

  Events reach the client as `method: "event"` frames with `params.type`:
  - `voice.status` (`{state}`: `listening` → `transcribing` → `idle`; `hermes_cli/voice.py` 384, 413, 457, 485, 513, 545)
  - `voice.transcript` (`{text}`, or `{stop_phrase: true, text}`, or `{no_speech_limit: true}`)
  - `voice.interrupted` (line 248)
  - `wake.detected` (`{phrase, profile, start_new_session}`, lines 426–430)

  Phase 1's `ChatSocket.DispatchEvent` currently discards all of them
  (its `default:` branch).
- **Voice events are session-addressed.** `voice.*` events go to the session id
  most recently passed on `voice.record`'s `session_id` param
  (`_voice_event_sid`, lines 30–34 and 721–722). `wake.detected` goes to the
  `session_id` passed on `wake.start` (lines 492–493). The client's existing
  session filter (`ChatSocket.cs` `DispatchEvent`) drops events for any other
  runtime session id, so the client **must** pass its current runtime
  `session_id` on both calls.
- **The mode flags are process-wide and live only in memory.** `HERMES_VOICE` /
  `HERMES_VOICE_TTS` are environment variables of the `hermes serve` process,
  never written to `config.yaml` (lines 18–19, 45–50). They survive a socket
  reconnect (new session / resume) but not a `hermes serve` restart.
  `voice.toggle action=tts` **flips** the flag (lines 662–666). It does not
  set it, so the client must read `voice.toggle status` first and toggle only
  when the current value differs. `voice.toggle action=off` also turns spoken
  replies off (line 650).
- **Hermes transcribes; the client submits.** Hermes emits
  `voice.transcript` and never calls `prompt.submit` itself (WINH09-AUD-05).
  The client sends the text through the same `prompt.submit` path it already
  uses for typed turns. Typed and spoken turns land in one session and one
  history.
- **Speech-to-text runs after capture, not live.** `voice.record start` opens a
  capture on the serve process's default input device (sounddevice/PortAudio).
  The capture stops after `voice.silence_duration` seconds of silence
  following speech, and the WAV file is then transcribed
  (`hermes_cli/voice.py` 330–385, 460–515). The gateway always calls it with
  `auto_restart=False` (line 754), so every capture is one utterance and the
  client decides whether to listen again.
- **The no-speech timeout is fixed.** `AudioRecorder._max_wait = 15.0`
  (`tools/voice_mode.py` line 620) stops a capture in which no speech ever
  started. No config key reaches it. When it fires, the client sees
  `voice.status idle` with no `voice.transcript`
  (`_continuous_on_silence` → `_rearm_after_turn` → `_deactivate`).
- **Spoken replies stream sentence by sentence on the server.** When
  `HERMES_VOICE_TTS=1`, `prompt_turn.py` (`_start_turn_voice` 183–205, delta
  feed 529–530, end sentinel 740–741) feeds reply deltas into
  `stream_tts_to_speaker`. For Edge, which has no chunked streamer, the
  speaker path uses `_SyncSentencePipeline`: each sentence is synthesized
  while the previous one plays (`tools/tts_tool_speaker.py` header). The
  client plays no audio itself.
- **Barge-in is built in.** While a turn runs or speech plays, a full-duplex
  listener keeps the mic open (`methods_voice.py` 139–261). If the user
  speaks, it:
  - cuts the speech;
  - interrupts a running turn;
  - emits `voice.interrupted`;
  - transcribes what the user said and emits it as `voice.transcript`;
  - latches a "user interrupted you" note into the next turn
    (`SPEECH_INTERRUPTED_NOTE`, `prompt_turn.py` 509–511).

  It is gated by `voice.barge_in` (default `true`).
- **No "finished speaking" signal exists.** Nothing on the socket marks the
  end of playback. `message.complete` fires when the *text* ends, while speech
  may still be playing. Plugins cannot add one: there is no playback hook in
  `VALID_HOOKS` and no RPC registration in `hermes_cli/plugins.py`. This
  constrains `P2-D06`.
- **Wake word.**
  - Engines (`tools/wake_word_engines.py`): `openwakeword` (default, bundled
    `hey_hermes` model only), `sherpa` (any typed phrase, no training,
    auto-downloads a ~13 MB model from GitHub on first use, lines 133–165),
    and `porcupine` (paid key).
  - `wake_word.capture: local` pins capture to the serve process's mic even
    for a `gui` surface (`resolve_capture_mode`, `tools/wake_word.py`
    184–196).
  - The detector has one owning transport (socket). The first `wake.start`
    owns it until `wake.stop` or the socket dies (`methods_voice.py`
    311–509).
  - While a transport owns the wake word, `voice.record` from any other
    transport returns `{status:"busy", reason:"wake_owned"}` (lines 714–716).
  - `voice.record` pauses the detector and resumes it on the capture's
    terminal event (lines 685–702, 743–748).
- **Speech-to-text provider.**
  - Built-ins: `local` (faster-whisper), `groq`, `openai`, `mistral`, `xai`,
    `elevenlabs`, `deepinfra`.
  - **There is no Edge speech-to-text.** The `P2` lore entry is wrong on
    this point; see the Lore Closeout.
  - With `stt.provider` unset, Hermes auto-detects local first and then falls
    back to the cloud. With it set, there is no silent cloud fallback
    (`tools/transcription_tools.py` 235–263).
  - faster-whisper lazy-installs through `tools.lazy_deps`, gated by
    `security.allow_lazy_installs` (`tools/transcription_local.py` 58–76).
- **Requirement probes exist.** `voice.toggle action=status` returns
  `available` / `audio_available` / `stt_available` / `details` (lines
  614–626). `wake.status` returns `available` / `hint` / `capture` /
  `listening` (lines 548–584).

---

## Decisions Resolved in This Build Plan

**P2-D01 — Hermes owns the audio devices; the client drives voice over `/api/ws`.**
Where the audio code runs:
- Mic capture, silence detection, speech-to-text, spoken-reply playback,
  barge-in and wake-word detection all run inside the `hermes serve` child
  process on the same PC.
- The Windows client controls them through the `voice.*` / `wake.*` methods on
  the `/api/ws` connection it already holds, and renders the resulting events.

What the client does not do:
- It never opens an audio device.
- It never uses the `/api/audio/*` REST upload endpoints or the client-direct
  voice-config path.

Why this option:
- It reuses every piece of the pipeline Hermes already ships (see Grounding
  summary).
- The alternative, capturing in C# and sending audio to
  `/api/audio/transcribe` + `/api/audio/speak-stream`, would mean
  re-implementing silence detection, barge-in and sentence chunking in C#.
- On Edge that alternative is also slower: `speak-stream` answers
  `{"type":"fallback"}` for providers without a chunked streamer, which forces
  whole-reply synthesis.

This decision clarifies `C3`. "Sole JSON-RPC owner of mic/speaker capture"
means the Windows client is the only process that issues voice/wake RPCs to
Zola's serve. The physical device handle belongs to that serve child. Ruled
out: client-side audio capture, and any second process issuing voice RPCs to
this serve. Decided by Brian 2026-09-22 (Option A).

**P2-D02 — Speech-to-text is local faster-whisper, pinned explicitly.**
- Config: `stt.provider: local`, `stt.local.model: base`, `stt.language: en`
  (already the default).
- Setting the provider explicitly turns off Hermes's cloud fallback, so audio
  never leaves the PC without a deliberate config change.
- Hardware: the target machine (Latitude 7430, i7-1265U, 32 GB, Iris Xe, no
  CUDA) runs faster-whisper on CPU.
- `base` is the starting model. Track 1's smoke test records the measured
  delay from end of speech to transcript. If accuracy is poor, `small` is the
  next step, trading speed for accuracy; that is a config-only change.

This corrects `P2` in `DESIGN_DECISIONS.md`, which says "Edge (free) TTS/STT".
Edge is text-to-speech only. Ruled out for now: cloud speech-to-text (Groq /
OpenAI / ElevenLabs). Decided by Brian 2026-09-22.

**P2-D03 — Spoken replies: Edge, default voice, on by default in Voice mode.**
- Config: `tts.provider: edge` (the Hermes default), voice
  `en-US-AriaNeural` (the Hermes default). The voice can be changed in a smoke
  test with a config-only edit to `tts.edge.voice`.
- In Voice mode the client makes sure `HERMES_VOICE_TTS` is on: read
  `voice.toggle status`, then send `voice.toggle action=tts` only if `tts` is
  `false`, because the action flips the flag (Grounding summary).
- Spoken replies apply to every turn while Voice mode is on, typed turns
  included.
- The client plays no audio. Hermes's server-side sentence pipeline speaks.

This carries forward `P2`'s Edge-for-now choice. ElevenLabs is still to be
revisited once a baseline exists. Decided by Brian 2026-09-22.

**P2-D04 — Starting a voice turn: "Hey Zola" wake word first, mic button and hotkey as fallback.**

Wake-word config:
- `wake_word.enabled: true`, `provider: sherpa`, `phrase: "hey zola"`.
- `capture: local`, per `P2-D01`. This must be explicit, because the default
  `auto` with a `gui` surface prefers client capture.
- `start_new_session: false`: a wake continues the current conversation.
- `profile_routing: false`: listen only for Zola's phrase, not every
  profile's `hey <profile>`. This machine has other Hermes profiles.
- `sensitivity` stays at its default (0.6), tunable in smoke test.

Why sherpa: openWakeWord only ships a `hey_hermes` model, and a custom
openWakeWord model would need training.

Fallback triggers:
- A mic button.
- An in-window hotkey (`Ctrl+Space`) that sends `voice.record start`, or
  `stop` while a capture is active.
- Both use the same code path as a wake detection.

Master Plan §12's long-term target is directed-speech detection with the wake
word as fallback. That does not exist in Hermes (WINH09-AUD-14/15) and is
deferred. Decided by Brian 2026-09-22.

**P2-D05 — Every voice transcript is sent to Zola immediately.**
- Any `voice.transcript` event with non-empty `text` and no `stop_phrase` is
  shown as a user bubble and sent with `prompt.submit` on the current runtime
  session, exactly like a typed turn. There is no draft-and-edit step.
- This applies both to transcripts from `voice.record` and to interjections
  from the barge-in listener.
- A `stop_phrase` transcript (the user says "stop", `voice.stop_phrases`
  default) ends the voice exchange. Hermes has already turned voice mode off
  (`_end_voice_chat`). The client shows that and returns to Voice mode's
  resting state (wake word armed again by `P2-D07`'s re-sync).
- `no_speech_limit` is shown as a status line, not a turn.

Decided by Brian 2026-09-22 (Decision 4) and Planning (auto-submit).

**P2-D06 — Follow-up listening uses Hermes as-is: barge-in during speech, then one estimated-delay capture.**
Brian chose to leave Hermes unmodified (2026-09-22). The follow-up window
therefore has two parts.

(a) **While Zola is speaking**, the user can simply talk. Hermes's barge-in
listener catches it (`P2-D05`), with no client work beyond handling the
events.

(b) **After Zola finishes**, the client cannot observe the end of playback
(see Grounding summary). It estimates the end with a **simulated playback
clock** that follows the reply as it streams, then starts one follow-up
capture.

*v1.1 change:* v1.0 counted the whole reply's words from
`message.complete`. That was wrong: Hermes speaks sentence by sentence
while the text is still generating. By `message.complete`, most of a long
reply may already have been spoken, so v1.0's delay would have started
listening long after she finished.

1. On `message.start` for a spoken turn, set
   `estimatedSpeechEnd = now + FirstSentenceLatencySeconds`.
2. On every `message.delta`, count the words in that chunk after the same
   markdown stripping used for display, then set:
   `estimatedSpeechEnd = max(estimatedSpeechEnd, now) + chunkWords / EstimatedWordsPerSecond`.
   This models one speaker playing sentences in order:
   - Speech can't finish before its text exists.
   - Speech that falls behind stacks up.
   - A pause for a tool call is absorbed by the `max(…, now)`.
3. On `message.complete` with status `complete`, set a single-shot timer
   for `max(0, estimatedSpeechEnd − now) + FollowUpMarginSeconds`, capped
   at `FollowUpMaxDelaySeconds`.

Constants and start values (named constants, all tuned in Track 2):
- `EstimatedWordsPerSecond = 2.5`
- `FirstSentenceLatencySeconds = 1.0`
- `FollowUpMarginSeconds = 1.0`
- `FollowUpMaxDelaySeconds = 90`

4. When the timer fires, send `voice.record start` with the current runtime
   `session_id`, but only if all of these hold: still in Voice mode, no
   capture already active, no new turn has started, and the user hasn't
   typed. These are the resting/follow-up rules in `P2-D12`.
5. The capture then ends one of two ways:
   - The user speaks: a transcript is submitted and the cycle repeats.
   - Nothing is said: Hermes's fixed 15 s no-speech timeout
     (`AudioRecorder._max_wait`) ends it, and the client returns to resting
     state (wake word armed).
6. Cancel the pending timer on any of: a `voice.transcript` (barge-in
   already started the next turn), `voice.interrupted`, a typed submit, a
   mode switch to Text, or a session switch.

Accepted costs:
- The window after playback is about 15 s, not "a few seconds".
- A too-short estimate lets the mic hear the tail of Zola's own speech, which
  would be transcribed and submitted as the user's turn. The margin errs long
  to prevent this.
- A too-long estimate leaves a short gap in which speech is missed: barge-in
  has stopped and the follow-up capture has not started yet.

**This implementation is provisional.**
- Track 2 must measure the real gap between the moment Zola's speech ends
  (heard) and the follow-up capture starting (indicator shows
  *Recording*).
- Measure it across four replies:
  - a short reply (one sentence);
  - a medium reply (about four sentences);
  - a long reply (ten or more sentences);
  - a reply that includes a tool call.
- Target in every case:
  - no self-transcription;
  - the capture starts within about 3 s of her last word.
- If tuning the constants cannot meet this, Track 2 stops BLOCKED and
  reports the measurements, and Brian decides whether to escalate `S17`. It
  does **not** mark the track complete with an unusable follow-up.

A precise version is filed as new `S17`, not built here. It would be either
client-side Windows audio-meter observation or a small Hermes patch adding
an end-of-playback event and a configurable no-speech timeout. This
addresses WINH09-AUD-16 within the as-is constraint without fully closing
it.

**P2-D07 — Voice/Text mode toggle; both modes always work.**
- A two-state mode toggle in the client, **Voice** or **Text**. The app
  launches in **Voice** mode. No settings persistence is added this phase.
- The text composer and Send button stay enabled in **both** modes.

Voice mode:
- Voice mode on (`voice.toggle on`).
- Spoken replies on (`P2-D03`).
- Wake word armed (Track 3).
- Mic button and hotkey enabled.

Text mode:
- `voice.toggle off`, which also silences speech and stops any capture.
- `wake.stop` (Track 3).
- Mic button and hotkey disabled.
- Replies are text-only.

Reconnect and failure handling:
- Every new `/api/ws` connection re-syncs Voice-mode state: `voice.toggle
  status`, then `on` / `tts` as needed, and `wake.start` in Track 3. This
  covers new session, resume, and reconnect.
- If the requirement probes report voice unavailable, the client stays usable
  in Text mode and shows the probe's `details`/`hint` text.

**P2-D08 — Voice state indicator comes from events only.**
- The status area shows one voice state, driven purely by socket events and
  the client's own turn state: *Idle*, *Listening for "Hey Zola"* (Track 3),
  *Listening* (`voice.status listening`), *Transcribing*
  (`voice.status transcribing`), *Thinking* (turn running), and *Speaking*
  (Track 2).
- *Speaking* is the client's estimate from `P2-D06`: from `message.start`
  until the simulated playback clock runs out. The label says so in a code
  comment.
- **Honest microphone indicator** *(v1.1)*: next to the voice state, a
  separate mic indicator always says what Hermes's mic is doing, from
  `P2-D12`'s table:
  - *Mic: listening for "Hey Zola"*
  - *Mic: recording*
  - *Mic: listening for interruptions* (Voice mode while a turn runs or
    Zola speaks, because Hermes's barge-in listener has the mic open)
  - *Mic: off* (Text mode, or voice unavailable)

  Why this matters: in Voice mode, Hermes opens the mic during **every**
  turn, typed ones included (`prompt_turn.py` 190–191). That must be
  visible, not implied.
- Privacy wording: never describe the pipeline as offline.
  - Speech-to-text is on-device (`P2-D02`).
  - Edge TTS sends reply text to Microsoft's online speech service.
  - The conversational model is a cloud provider.
- This is a plain status element. The Obsidian Interface attention-level
  indicator that will later visualize these same states is deferred.

**P2-D09 — Configuration lives in the live profile, with a canonical copy in the repo.**
Same pattern as `P1-MEMORY`:
- The voice/STT/TTS/wake keys are written to the live Zola profile
  `%LOCALAPPDATA%\hermes\profiles\zola\config.yaml`, which is outside git.
- The exact block is recorded as the canonical copy in a new repo file,
  `zola-architecture/identity/VOICE_CONFIG.md`.
- Track 1 creates the file with the `stt` / `tts` / `voice` keys. Track 3
  appends the `wake_word` block.
- `load_config()` deep-merges over defaults, so only the keys being set are
  written.

Starting values (all tunable in smoke tests):
- `stt.provider: local`, `stt.local.model: base`
- `tts.provider: edge`, `tts.edge.voice: en-US-AriaNeural`
- `voice.silence_duration: 1.5`. The default of 3.0 s of trailing silence
  before a capture ends is too slow for conversation.
- `voice.barge_in: true`
- `voice.stop_phrases: ["stop"]`
- `voice.thinking_sound: true`
- `security.allow_lazy_installs: false` (*v1.1*, see `P2-D10`)

**P2-D10 — Optional Python dependencies are installed only with Brian's approval; Hermes source is never edited.**
- Voice needs packages that may not be in the Python environment the client
  launches Hermes with (`HermesLaunchResolver`: `ZOLA_HERMES_PYTHON`, else
  `hermes-agent\.venv`, else PATH): sounddevice + numpy (Hermes `voice`
  extra), faster-whisper (Track 1), sherpa-onnx (Track 3).
- Each track's Phase 2 probes with `voice.toggle status` / `wake.status`,
  plus Hermes's own `lazy_deps.feature_install_command` hint.
- If anything is missing, the phase stops BLOCKED with the exact install
  command. Cursor installs into that environment only after Brian's explicit
  approval.
- Installing packages into the environment is allowed. Editing any file in
  the `hermes-agent` checkout is not: it stays read-only, and
  `git status` there must be clean at every closeout.
- *v1.1:* during Track 1 Phase 2, calling `check_voice_requirements()` with
  `stt.provider` unset made Hermes lazy-install faster-whisper 1.2.1,
  sounddevice 0.5.5 and numpy 2.4.3 as a side effect. These are Hermes's
  own pinned versions, and Brian accepted them after the fact.
- To enforce this decision structurally, the Zola profile sets
  `security.allow_lazy_installs: false` (added to `P2-D09`'s Track 1 keys).
  Hermes can then never install packages silently. A missing dependency
  becomes a requirement hint instead.

**P2-D11 — No separate pre-build audit for Phase 2.**
- WINH09 already audited this exact pinned tag's voice surface, and the
  Grounding summary re-confirms it against source.
- Per SOP Stage 1, an audit is skipped when the developer agrees. Brian
  confirms by approving this plan.
- Each track's Phase 2 re-reads its files in full (`G-PATTERN`). A conflict
  with this plan stops the track (`G-ARCH`).

**P2-D12 — One owner for voice state; exactly one listener active per state; one utterance, one turn.** *(v1.1)*

**Single owner.**
- `VoiceController.cs` is the only place that:
  - decides which listening mechanism should be active;
  - sends `voice.record` / `wake.*`;
  - turns a transcript into a submit.
- `MainWindow` only renders its state and forwards clicks and keys.
- Tracks 2 and 3 extend `VoiceController`. They do not add voice logic to
  `MainWindow.xaml.cs`.

**Microphone ownership table (Voice mode unless stated):**

| Zola state | Hermes listener that should be active | Client may start `voice.record`? | Client acts on `wake.detected`? |
|---|---|---|---|
| Resting | Wake detector (Track 3); none before Track 3 | Yes (mic button / hotkey) | Yes |
| Recording | `voice.record` capture (Hermes pauses the wake detector) | No (a second press = stop) | No |
| Transcribing | None new | No | No |
| Thinking (turn running) | Barge-in listener (`barge_in: true`) | **No**: mic button and hotkey disabled | **No**: ignored |
| Speaking (simulated clock running) | Barge-in listener | **No** | **No**: ignored |
| Follow-up | `voice.record` capture | Only the one `P2-D06` follow-up capture | No |
| Text mode | None (`voice.toggle off`, `wake.stop`) | No | No (wake stopped) |

**Why the Thinking/Speaking rows matter.**
- If the client opened a `voice.record` capture while Hermes's barge-in
  listener already had the mic, both would hear the same sentence. The
  result would be two `voice.transcript` events and two submitted turns.
- The same happens if "Hey Zola" is said while Zola speaks:
  - the barge-in listener trips and emits the words as a transcript;
  - `wake.detected` may also fire.
- Acting on only one of them keeps it to a single turn.

**Duplicate and stale protection.**
- Hermes provides no utterance ID. The guarantee rests on three things:
  1. The table above: at most one Hermes listener that produces
     transcripts at any time.
  2. The existing runtime-`session_id` filter: events from a previous
     session's socket are dropped.
  3. The client ignores `voice.transcript` while in Text mode.
- Text matching is **not** used. Saying the same thing twice is
  legitimate.
- Each track's Phase 2 must confirm from source which listener emitted
  each transcript path, and write down any case the table does not
  cover. Found cases are handled by fixing the state rules, never by
  de-duplicating text.

**Running-turn submits.**
- Track 1 Phase 2 found that `prompt.submit` during a running turn is
  accepted. Hermes either redirects it into the live turn
  (`{status:"redirected"}`) or queues it and interrupts
  (`{status:"queued"}`).
- The client therefore submits every transcript once, immediately, and
  never holds or re-submits it.
- The client renders the "You" bubble without disturbing an open assistant
  bubble.

---

## Track 1 — Voice Core (`P2-VOICE`)

### Problem
Zola-Windows has no voice input. Hermes already exposes a complete chained
voice pipeline on the socket the client holds, but Phase 1's client ignores
every `voice.*` event and never calls a voice method. See the Grounding
summary, `ChatSocket.cs` `DispatchEvent` `default:` branch, and
WINH09-AUD-05. The live Zola profile also has no speech-to-text provider set.
Auto-detect would silently pick a cloud provider if faster-whisper is missing
(`transcription_tools.py` 235–263).

### Files to read

**zola-windows (in scope):**
- `windows-client/Zola.Client/ChatSocket.cs`: `Dispatch` / `DispatchEvent`
  (around lines 408–500), `CallAsync`, `SubmitAsync` (176–195), session-id
  handling after `session.create` / `session.resume` (around 555).
- `windows-client/Zola.Client/MainWindow.xaml` and `MainWindow.xaml.cs`:
  status area, composer, Send/Cancel buttons, and the turn-state handling
  wired to `MessageStarted` / `MessageDelta` / `MessageCompleted`.
- `windows-client/Zola.Client/HermesLaunchResolver.cs`: which Python
  environment serve runs in (for `P2-D10`).
- `zola-architecture/identity/MEMORY_CONVENTIONS.md`: the pattern to mirror
  for `VOICE_CONFIG.md`.
- Live `%LOCALAPPDATA%\hermes\profiles\zola\config.yaml`: current contents,
  read before adding keys.

**hermes-agent (READ-ONLY, never modified):**
- `tui_gateway/methods_voice.py`, in full. Focus: `_voice_toggle_*` 614–682,
  `voice.record` 705–764, `_vr_*` callbacks 685–702, `_voice_emit` 30–34.
- `hermes_cli/voice.py`: `start_continuous` 330–385, `stop_continuous`
  388–430, `_continuous_on_silence` / `_rearm_after_turn` 460–545.
- `tools/voice_mode.py`: `AudioRecorder` 603–700 (silence detection,
  `_max_wait`), `check_voice_requirements`.
- `tools/transcription_tools.py` 235–263 (`_get_provider`);
  `tools/transcription_local.py` 58–76 (lazy install).
- `hermes_cli/config_defaults.py` 1005–1160 (`tts`, `stt`, `voice` blocks).
- `tui_gateway/contracts/`: confirm the exact event names and payload
  fields above. Planning did not read this directory.
- `tui_gateway/server.py`: `_emit`, to confirm event frame shape
  (`params.type` / `params.session_id` / `params.payload`).

### Changes

**Live profile `config.yaml` (outside git):** add the `stt`, `tts` and
`voice` keys from `P2-D09`. Change nothing else.

**`zola-architecture/identity/VOICE_CONFIG.md` (new):**
- The exact YAML block written above.
- One line per key saying why.
- A "Dependencies" section recording what the Phase 2 probe found and what
  was installed (if anything, with Brian's approval).
- Prose note tag: `P2-VOICE — P2-D09`.

**Dependency probe (Phase 2 of the track, no code):**
1. With serve running on the Zola profile, call `voice.toggle action=status`
   and record `available` / `audio_available` / `stt_available` / `details`.
2. If any is false, stop BLOCKED with the install command (`P2-D10`).
3. After install, re-probe and confirm faster-whisper loads the `base` model
   on CPU. Run one transcription through the normal `voice.record` path.

**`windows-client/Zola.Client/VoiceController.cs` (new):**
- Owns voice-mode state and talks to `ChatSocket`. All RPC method names,
  event type names, and timings are named constants (no inline literals).
- `SyncVoiceModeAsync()`: runs on every socket open while in Voice mode, and
  on switching into Voice mode:
  1. `voice.toggle status`.
  2. If `enabled` is false, `voice.toggle on`.
  3. Store availability flags. If unavailable, surface `details` and force
     Text mode (`P2-D07`).
- `EnterTextModeAsync()`: sends `voice.toggle off`.
- `StartCaptureAsync()` / `StopCaptureAsync()`: send `voice.record` with
  `action` and the current runtime `session_id` (always passed; see
  Grounding summary). Handle `{status:"busy"}` by showing it on the status
  line, not as an error.
- Event handlers:
  - `voice.status`: updates the state indicator (`P2-D08`).
  - `voice.transcript`: per `P2-D05`. Text → raise `TranscriptReady(text)`;
    `stop_phrase` → voice exchange ended; `no_speech_limit` → status line.
- Tag: `// P2-VOICE: [rationale] — P2-D0X` on every new line or block.

**`ChatSocket.cs`:**
- In `DispatchEvent`, add cases for `voice.status`, `voice.transcript`,
  `voice.interrupted`, `wake.detected`, each raising a typed C# event with
  the parsed payload. The existing session-id filter stays as-is. `wake.*`
  and `voice.interrupted` cases are parsed now and consumed by Tracks 2/3.
- Expose a generic `CallAsync` wrapper if one is not already public. Change
  no existing message-handling behavior.
- Tag: `// P2-VOICE: … — P2-D01`.

**`MainWindow.xaml` / `MainWindow.xaml.cs`:**
- Mic button next to Send. It is a toggle: start/stop capture.
- `Ctrl+Space` keyboard accelerator on the window, same action (`P2-D04`).
- Voice/Text mode toggle.
- Voice state indicator in the status area (`P2-D08`).
- Honest mic indicator (`P2-D08` v1.1). Track 1 states:
  - *Mic: recording*
  - *Mic: listening for interruptions*, while a turn runs in Voice mode
  - *Mic: off*

  Track 3 adds *Mic: listening for "Hey Zola"*.
- Mic button and hotkey are **disabled while a turn is running** (`P2-D12`).
  Hermes's barge-in listener already has the mic in that state.
- `TranscriptReady` → append a user bubble and call the **existing** submit
  path used by the Send button. There must be no second submit path
  ("One authority per responsibility").
- A transcript arriving during a running turn (barge-in) is submitted
  immediately. Hermes redirects or queues it (`P2-D12`), and the client
  never holds or re-submits.
- Composer and Send remain enabled in both modes. The typed Send guard
  while streaming is unchanged from Phase 1.
- Tag: `// P2-VOICE: … — P2-D0X`.

### Exit criteria
- [ ] `stt.provider: local` (and the rest of the `P2-D09` Track 1 block) is
      in the live profile `config.yaml` and matches `VOICE_CONFIG.md`
      verbatim.
- [ ] `voice.toggle status` on the Zola serve reports `available`,
      `audio_available` and `stt_available` all `true`. Any package installed
      is recorded in `VOICE_CONFIG.md`.
- [ ] Clicking the mic button or pressing `Ctrl+Space`, speaking one sentence
      and pausing produces a user bubble with the transcript and a normal
      streamed reply. No typing, no Send click.
- [ ] Transcripts are submitted through the same method the Send button uses
      (verified by reading the diff).
- [ ] Voice state indicator walks *Listening → Transcribing → Thinking →
      Idle* for that turn.
- [ ] Saying just "stop" during a capture ends the voice exchange and sends
      no turn.
- [ ] Text mode: mic button and hotkey disabled, `voice.toggle status` shows
      `enabled: false`, and typed turns work. Switching back to Voice
      re-enables voice without restarting the app.
- [ ] After **New session** and after **Resume** (each opens a fresh
      `/api/ws`), the mic still works and the transcript lands in the new
      session. This confirms `session_id` is passed and the re-sync runs.
- [ ] With the Zola serve killed, the mic control is disabled along with the
      composer (Phase 1's unreachable state still holds).
- [ ] While a turn is running in Voice mode, the mic button and hotkey are
      disabled, and the mic indicator reads *Mic: listening for
      interruptions*. In Text mode it reads *Mic: off* (`P2-D08`,
      `P2-D12`).
- [ ] Speaking over a running turn produces exactly **one** user bubble and
      one submitted turn, with no duplicated or orphaned assistant bubbles
      (`P2-D12`).
- [ ] Live profile has `security.allow_lazy_installs: false`, and
      `pip check` on the Hermes interpreter is clean (`P2-D10` v1.1).
- [ ] `git status` in `C:\Users\test\Dev\hermes-agent` is clean.
- [ ] `dotnet build windows-client/Zola.Client/Zola.Client.csproj` passes
      with 0 warnings.
- [ ] Smoke test (HUMAN-RUN):
  1. Launch the client and confirm Voice mode.
  2. Press `Ctrl+Space`, say "What's the capital of France?", and pause.
  3. Pass signal: the transcript bubble appears and Zola's text reply streams.
  4. Brian reports the approximate delay from finishing the sentence to the
     transcript bubble appearing (`base` model on CPU). The number is
     recorded in the progress doc, not pass/fail.
  5. Switch to Text, type a message, and confirm it works. Switch back to
     Voice.

**Complexity:** Medium-Large
**Primary risk:** the events never reach the UI. If `voice.record` is sent
without the current runtime `session_id` (or after a resume, with the old
one), `_voice_event_sid` points at a different session. Every
`voice.transcript` / `voice.status` is then silently dropped by the client's
existing session filter: the mic records, Hermes transcribes, and nothing
appears. The New session / Resume exit criterion exists to catch exactly
this.

---

## Track 2 — Spoken Replies and Follow-up (`P2-SPEAK`)

### Problem
After Track 1, Zola hears but does not speak. Hermes will speak every reply
server-side once `HERMES_VOICE_TTS` is on (`prompt_turn.py` 183–205, 529–530,
740–741). But the client never turns it on, ignores `voice.interrupted`, and
has no follow-up behavior after a reply (WINH09-AUD-16; Brian's Decision 4).

### Files to read

**zola-windows (in scope):**
- `windows-client/Zola.Client/VoiceController.cs`, `ChatSocket.cs`,
  `MainWindow.xaml(.cs)`, all as merged by Track 1.
- `zola-architecture/identity/VOICE_CONFIG.md`.

**hermes-agent (READ-ONLY):**
- `tui_gateway/methods_voice.py`: `_tts_stream_begin/_stop` 97–136,
  full-duplex listener 139–261, `_voice_toggle_tts` / `_set_voice_tts`
  654–666.
- `tui_gateway/prompt_turn.py`: `_start_turn_voice` 183–205, fallback speak
  344–352, delta feed 506–530, end-of-text 738–741.
- `tools/tts_tool_speaker.py` in full (`_SyncSentencePipeline` is the Edge
  path).
- `tools/tts_streaming.py`: `mark_speech_interrupted` /
  `take_speech_interrupted`.
- `tools/voice_mode.py`: `AudioRecorder._max_wait` (line 620),
  `is_audio_output_active`.

### Changes

**`VoiceController.cs`:**

Spoken replies:
- Extend `SyncVoiceModeAsync()`: after voice mode is on, if
  `voice.toggle status` shows `tts: false`, send `voice.toggle action=tts`
  once. Never send it blind, because it flips (`P2-D03`).
- Spoken replies are on for all turns while in Voice mode.

Barge-in handling:
- On `voice.interrupted`: cancel any pending follow-up timer and set the
  indicator to *Listening*. The interjection itself arrives as a normal
  `voice.transcript`, handled by Track 1's submit path.
- No client-side interrupt RPC is needed: Hermes already interrupted the
  turn.

Follow-up window (`P2-D06`):
- Named constants: `EstimatedWordsPerSecond = 2.5`,
  `FirstSentenceLatencySeconds = 1.0`, `FollowUpMarginSeconds = 1.0`,
  `FollowUpMaxDelaySeconds = 90`.
- Simulated playback clock (`P2-D06` v1.1), while in Voice mode with spoken
  replies on:
  - `MessageStarted` initializes `estimatedSpeechEnd`.
  - Each `MessageDelta` advances it.
  - `MessageCompleted` with status `complete` starts the single-shot timer
    for the remaining estimate plus the margin.
  - The indicator shows *Speaking* from `MessageStarted` until the timer
    fires.
  - Log (debug level) each turn's `message.start` time, `message.complete`
    time, final `estimatedSpeechEnd`, and timer fire time. Track 2's
    measurement uses these.
- On fire, if still eligible (`P2-D06` conditions), call
  `StartCaptureAsync()`. Track 1's handlers then take over.
- Cancel on:
  - `voice.transcript`
  - `voice.interrupted`
  - typed submit
  - mode → Text
  - session switch
  - app close
- `MessageCompleted` with status `interrupted` or `error` starts no timer.
- A follow-up capture that ends `idle` with no transcript returns the
  indicator to *Idle* (Track 3 will make this *Listening for "Hey Zola"*).
- Tag: `// P2-SPEAK: [rationale] — P2-D0X`.

**`MainWindow.xaml(.cs)`:**
- Typing and Send while Zola is speaking must cut her speech. Hermes already
  does this: a new turn's `_tts_stream_begin` stops the previous pipeline.
  Confirm it in this track's reading, and add nothing if it holds. If it
  does not hold, stop (`G-ARCH`).
- The Cancel button during a spoken turn keeps Phase 1 behavior
  (`session.interrupt`). Confirm speech also stops. If it does not, flag it
  and do not add a workaround.
- Tag as above.

### Exit criteria
- [ ] In Voice mode, a spoken or typed turn's reply is heard through the
      default speakers as it streams, starting before the full reply text has
      finished.
- [ ] `voice.toggle action=tts` is only ever sent after a `status` read
      showing `tts: false` (verified by reading the diff).
- [ ] Talking over Zola mid-reply stops her speech within about 1 s. What
      was said becomes the next user bubble and turn, and her next reply
      reflects being interrupted.
- [ ] After a reply finishes, asking a follow-up question without the wake
      word or button is transcribed and answered.
- [ ] Follow-up measurement (`P2-D06` v1.1): for a short, a medium, a long,
      and a tool-using reply, the gap from her last spoken word to the mic
      indicator showing *Mic: recording* is recorded in the progress doc.
      Each gap is within about 3 s, with no self-transcription. If that
      can't be met by tuning, the track stops BLOCKED (not COMPLETE).
- [ ] Thinking/Speaking states: the mic button and hotkey are disabled, and
      the mic indicator reads *Mic: listening for interruptions*
      (`P2-D12`).
- [ ] After a reply finishes, staying silent returns the indicator to
      *Idle* on its own. With the fixed timeout this takes about 15 s after
      the capture starts.
- [ ] Over 5 consecutive spoken replies on the laptop's built-in speakers
      (no headset), Zola's own speech never appears as a user bubble.
- [ ] Text mode: replies are not spoken, and no follow-up capture ever
      starts.
- [ ] `git status` in `hermes-agent` is clean.
- [ ] `dotnet build …` passes with 0 warnings.
- [ ] Smoke test (HUMAN-RUN), in Voice mode:
  1. Ask "Tell me three facts about Seattle."
  2. Interrupt her halfway with "actually, make it Portland."
  3. After her reply, ask a follow-up without pressing anything.
  4. Then stay silent until she stops listening.
  5. Pass signals: each step behaves as in the criteria above, and no
     self-transcription is seen.
  6. Run the four follow-up measurement replies. Tune
     `EstimatedWordsPerSecond`, `FirstSentenceLatencySeconds` and
     `FollowUpMarginSeconds` until the targets hold. Record the final values
     and the measured gaps in the progress doc.
  7. Brian may try alternate Edge voices here (`tts.edge.voice`); the final
     choice is recorded in `VOICE_CONFIG.md`.

**Complexity:** Medium
**Primary risk:** self-transcription from an under-estimated follow-up
delay. Edge's real speaking rate and the per-sentence synthesis gaps in
`_SyncSentencePipeline` make actual playback longer than a word-count
estimate. If the follow-up `voice.record` opens while the speakers are still
playing, Hermes's recorder (plain RMS silence detection, no echo
cancellation, unlike the barge-in listener's calibrated threshold) hears
Zola's voice. It transcribes it and the client submits it as the user,
starting a self-talk loop. The 5-reply built-in-speaker exit criterion and
the long-biased margin exist for this.

---

## Track 3 — "Hey Zola" Wake Word (`P2-WAKE`)

### Problem
Brian chose a wake word as the primary trigger (`P2-D04`). Hermes's wake
detector exists but is off by default (`wake_word.enabled: false`). Its
default engine only knows "hey hermes". Its default capture mode would ask a
GUI client to stream audio (`wake.feed`). And its detector belongs to one
socket at a time, while this client opens a fresh `/api/ws` per session
(`P1-SESSION` handshake notes).

### Files to read

**zola-windows (in scope):**
- `windows-client/Zola.Client/VoiceController.cs`, `ChatSocket.cs`,
  `MainWindow.xaml(.cs)`, all as merged by Track 2.
- `zola-architecture/identity/VOICE_CONFIG.md`.
- Live profile `config.yaml`.

**hermes-agent (READ-ONLY):**
- `tui_gateway/methods_voice.py`: wake section 311–611 in full, plus
  `voice.record`'s wake interplay 713–716 and 743–748.
- `tools/wake_word.py`, in full. Focus: `resolve_capture_mode` 184–196,
  `wake_surface_enabled` 218–223, profile-phrase enrollment (around 226–
  260), `check_wake_word_requirements` 366–400.
- `tools/wake_word_engines.py`: `_SherpaKwsEngine` and model download
  133–215.
- `hermes_cli/config_defaults.py` 1161–1198 (`wake_word` block).
- `tools/lazy_deps.py`: the `wake.sherpa` feature entry, for the install
  command.

### Changes

**Live profile `config.yaml` + `VOICE_CONFIG.md` (append):** add the
`wake_word` block:

```yaml
wake_word:
  enabled: true
  provider: sherpa
  phrase: "hey zola"
  capture: local
  surface: auto
  start_new_session: false
  profile_routing: false
  sensitivity: 0.6
```

In Phase 2, confirm from `wake_word.py` that `profile_routing: false` limits
detection to `phrase`. If it does not, stop (`G-ARCH`).

**Dependency probe (Phase 2 of the track):**
1. Call `wake.status` with `surface: "gui"` and record `available`, `hint`,
   and `capture`. `capture` must be `local`.
2. If sherpa-onnx is missing, stop BLOCKED with the install command
   (`P2-D10`).
   - With `security.allow_lazy_installs: false` set in Track 1, Hermes
     cannot auto-install it.
   - Confirm from `wake_word_engines.py` whether the separate model download
     (`urllib.request.urlretrieve`) is also blocked by that setting, or
     still runs on first arm. Report which.
3. The one-time ~13 MB model download from GitHub happens on first arm.
   Record where it landed.

**`VoiceController.cs`:**

Arming:
- `ArmWakeAsync()` calls `wake.start` with `surface: "gui"`, the current
  runtime `session_id`, and no `persist`. It handles each response:
  - `started: true` → set the indicator to *Listening for "Hey Zola"*.
  - `reason: "owned"` → release and retry once (see Socket handover).
  - `unavailable` / `disabled` → show `hint` and leave the mic button
    working.
- `DisarmWakeAsync()` calls `wake.stop`, with no `persist`.

Socket handover (must happen on every session change):
1. Call `DisarmWakeAsync()` on the **old** socket **before** it is closed.
2. Call `ArmWakeAsync()` on the new socket after `SyncVoiceModeAsync()`.

This is necessary for two reasons:
- The detector is owned by a transport.
- `voice.record` from any non-owner transport returns
  `busy / wake_owned`.

Detection:
- On `wake.detected`, call `StartCaptureAsync()` (the same path as the mic
  button) **only in the Resting state** of `P2-D12`'s table. In every other
  state, ignore it and log that it was ignored.

  Most important case: saying "Hey Zola" while Zola is thinking or
  speaking. Hermes's barge-in listener already turns that speech into a
  transcript, so acting on `wake.detected` too would create a second
  capture and a second turn.
- Phase 2 must confirm from source whether the wake detector stays armed
  during a running turn and during TTS playback. Record which listeners can
  fire for one "Hey Zola" said while she speaks.
- Ignore `start_new_session`. The current session continues, per `P2-D04`.
  Hermes resumes the detector itself after the capture's terminal event.

Mode and resting state:
- Text mode → `DisarmWakeAsync()`.
- Voice mode → `ArmWakeAsync()`.
- The resting state after any capture ends (including Track 2's follow-up
  timeout) is *Listening for "Hey Zola"* when armed.
- Use `wake.status` to refresh the indicator after reconnects.
  `audio_silent: true` is surfaced with its `hint`.

Tag: `// P2-WAKE: [rationale] — P2-D04`.

### Exit criteria
- [ ] Live `config.yaml` `wake_word` block matches `VOICE_CONFIG.md`
      verbatim.
- [ ] `wake.status` (surface `gui`) reports `available: true`,
      `capture: "local"`, `listening: true`, `owned_by_caller: true` while in
      Voice mode.
- [ ] Saying "Hey Zola, what time is it?" while the app is idle is detected.
      The detection can be the phrase alone followed by the question, per
      sherpa behavior. A capture starts, and the question is answered in the
      **current** session, with no new session in the list.
- [ ] Detection works with the client window minimized or unfocused (the
      detector runs in serve).
- [ ] After each voice turn and after a Track 2 follow-up timeout, the wake
      word works again without any click.
- [ ] After New session and after Resume, the wake word still works and the
      mic button never returns `busy / wake_owned`.
- [ ] Saying "Hey Zola, stop talking about that" while Zola is speaking
      produces exactly **one** user bubble and one turn, with no second
      capture started (`P2-D12`).
- [ ] Mic indicator reads *Mic: listening for "Hey Zola"* in the Resting
      state, and *Mic: off* in Text mode.
- [ ] Text mode: saying "Hey Zola" does nothing, and `wake.status` shows
      `listening: false`.
- [ ] "Hey Hermes" does **not** wake Zola.
- [ ] `git status` in `hermes-agent` is clean.
- [ ] `dotnet build …` passes with 0 warnings.
- [ ] Smoke test (HUMAN-RUN):
  1. With the client minimized in Voice mode, say "Hey Zola", then ask a
     question.
  2. Continue the conversation using Track 2's follow-up window.
  3. Let it time out, then wake her again with "Hey Zola".
  4. Switch sessions and repeat once.
  5. Then run 10 minutes of normal room audio (talking, video playing)
     without the phrase.
  6. Pass signals: every step above works. Brian reports the false-wake
     count from the 10 minutes and judges whether `sensitivity` needs
     tuning. The final value is recorded in `VOICE_CONFIG.md`.

**Complexity:** Medium
**Primary risk:** a stale owning transport. `P1-SESSION` opens a new
`/api/ws` for every new session and resume. If the old socket closes without
`wake.stop`, the detector stays owned by a transport that `_transport_is_dead`
may not flag immediately. Until it does:
- `wake.start` on the new socket is refused as `owned`;
- the mic button's `voice.record` returns `busy / wake_owned`;
- `wake.detected` fires to the dead socket.

The result is a silent, dead wake word after the first session switch. The
disarm-before-close ordering and the session-switch exit criterion target
this.

---

## Phase 2 Lore Closeout

After all three tracks are merged to `main`:

### DESIGN_DECISIONS.md
- Record `P2-D01` through `P2-D12` in a new "Phase 2 — Voice" section, with
  each track's final tuned values (Whisper model, Edge voice,
  `silence_duration`, follow-up constants, wake `sensitivity`).
- **Correct `P2`:** replace "TTS/STT: Edge (free)" with "TTS: Edge (free);
  STT: local faster-whisper (see P2-D02). Edge has no speech-to-text."
- **Annotate `C3`:** cite `P2-D01` for what "sole owner" means in practice.
- **Annotate `S1`:** still deferred. The wake word does not identify the
  speaker.

### OPEN_QUESTIONS.md
- **File `S17` — Precise follow-up window.** Wording: the post-reply
  follow-up capture currently starts after an estimated speaking time and
  ends on Hermes's fixed 15 s no-speech timeout (`P2-D06`). Doing better
  needs one of:
  - a Hermes-side end-of-playback event plus a configurable no-speech
    timeout, which requires a maintained patch to the pinned checkout;
  - client-side observation of Windows audio level meters.

  Include Track 2's measured gap/self-transcription results.
- **File `S18` — Global push-to-talk hotkey.** `Ctrl+Space` only works while
  the window has focus. A system-wide hotkey is deferred.
- **File `S19` — Directed-speech detection (Master Plan §12).** Wake word is
  the primary trigger for now. Detecting speech meant for Zola without a
  wake word, with addressee confidence tiers, is the long-term target. Hermes
  has no implementation (WINH09-AUD-14/15).
- No existing OQ (`S13`, `S16`) is resolved by Phase 2.

### ROADMAP.md
- Mark Phase 2 COMPLETE with the three track merge SHAs.
- Add a Phase 3 stub with candidates only:
  - Obsidian Interface theme + attention-level indicator (now backed by
    `P2-D08`'s voice states)
  - Google Workspace (`S16`)
  - `S17`
  - `S13`
  - `S12`

### Zola Master Architecture Plan.md (architecture doc, named explicitly as in scope for the lore-closeout prompt only)
- Correct the "Windows Track" note under External API Strategy → Tier 1.
  "Hermes's free Edge TTS/STT" becomes "Edge TTS (free) and local
  faster-whisper STT (on-device)", citing `P2-D02`.

---

## Phase 2 Exit Checklist

- [ ] Track 1 (`P2-VOICE`) complete and merged. Voice input via mic/hotkey,
      auto-submit, Voice/Text toggle, and local speech-to-text all verified
      by smoke test.
- [ ] Track 2 (`P2-SPEAK`) complete and merged. Spoken replies, barge-in,
      and the follow-up window verified, with no self-transcription over 5
      replies on built-in speakers.
- [ ] Track 3 (`P2-WAKE`) complete and merged. "Hey Zola" works minimized,
      re-arms after turns and session switches, and stays silent in Text
      mode.
- [ ] All RPC method names, event type names, timing values and thresholds
      in client code are named constants. There are no inline literals.
- [ ] No file in `C:\Users\test\Dev\hermes-agent` modified. `git status`
      there is clean after every track.
- [ ] No client code opens an audio device (no NAudio/WASAPI/MediaCapture
      references), per `P2-D01`.
- [ ] Exactly one submit path. Typed and spoken turns both reach
      `prompt.submit` through the same method.
- [ ] Live profile `config.yaml` voice/STT/TTS/wake keys match
      `zola-architecture/identity/VOICE_CONFIG.md`.
- [ ] `dotnet build windows-client/Zola.Client/Zola.Client.csproj` passes on
      `main` after all merges.
- [ ] Combined smoke pass on `main` after Track 3:
  1. Cold launch → "Hey Zola" question → spoken answer.
  2. Barge-in.
  3. Follow-up.
  4. Timeout → wake again.
  5. Switch to Text → typed turn silent → back to Voice.
  6. Resume an older session → wake word works there.
  7. Close Zola, relaunch from the normal shortcut (no terminal open), and
     confirm the voice pipeline reconnects: wake word armed and mic
     indicator correct.
  8. Say "Hey Zola" from normal speaking distance across the room, not
     leaning into the laptop.
  9. All on the Latitude 7430 that Zola actually runs on.
- [ ] One voice-state owner: every `voice.record` / `wake.*` call and every
      transcript-to-submit decision lives in `VoiceController.cs`
      (`P2-D12`), verified by searching the client source.
- [ ] No utterance ever produced two submitted turns in any track's smoke
      test (`P2-D12`).
- [ ] `DESIGN_DECISIONS.md`: `P2-D01`–`P2-D12` recorded, and `P2` corrected.
- [ ] `OPEN_QUESTIONS.md`: `S17`, `S18`, `S19` filed.
- [ ] `ROADMAP.md`: Phase 2 COMPLETE with SHAs, and Phase 3 stub added.
- [ ] Master Plan Tier 1 Windows note corrected.

---

## What Phase 2 Explicitly Defers

| Item | Reason | When |
|---|---|---|
| Precise follow-up window (end-of-playback signal, few-second no-speech timeout) | Needs a Hermes patch or client audio metering. Brian chose Hermes as-is (`P2-D06`) | `S17`, future track |
| Global (system-wide) push-to-talk hotkey | In-window hotkey is enough for v1 | `S18` |
| Directed-speech detection / addressee confidence (Master Plan §12) | No Hermes implementation (WINH09-AUD-14/15); large research item | `S19`, future phase |
| Voice identity / voiceprint | Already deferred (`S1`) | Unchanged |
| Cloud speech-to-text (Groq/OpenAI/ElevenLabs) | Local chosen (`P2-D02`) | If local latency or accuracy proves inadequate |
| ElevenLabs or other premium voice | Edge baseline first (`P2`/`P2-D03`) | After Phase 2 usage |
| GPT-Live / full-duplex vendor voice | Not a Windows requirement (`S5`) | Unchanged |
| Client-side audio capture (`/api/audio/*`, client-direct) | Ruled out by `P2-D01` | Only if a remote/companion client appears |
| Obsidian Interface theme + attention-level indicator visuals | Separate future phase. `P2-D08` supplies its states | Phase 3 candidate |
| Persisting Voice/Text mode choice across launches | No client settings store yet. Launch defaults to Voice | Future client-settings work |
| Google Workspace | `S16` | Future phase |
| Streaming (partial) speech-to-text, speculative reasoning | Master Plan §3 long-term model. Hermes speech-to-text works on the whole utterance | Future |

---

## Complexity Legend

| Track | Complexity | Primary Risk |
|---|---|---|
| 1 — Voice core (`P2-VOICE`) | Medium-Large | Missing/stale `session_id` on `voice.record` → voice events silently dropped by the client's session filter |
| 2 — Spoken replies + follow-up (`P2-SPEAK`) | Medium | Under-estimated follow-up delay → mic hears Zola's own speech → self-talk loop |
| 3 — "Hey Zola" wake word (`P2-WAKE`) | Medium | Stale wake-owner transport after a session switch → dead wake word and `busy / wake_owned` mic |

---

*Phase 2 Build Plan version 1.1*
*Created 2026-09-22. v1.1 2026-09-23 (review amendments):*
*P2-D06 simulated playback clock, and follow-up made provisional and*
*measured; P2-D08 honest mic indicator and privacy wording; P2-D10*
*lazy-installs off; new P2-D12 (single voice-state owner, mic-ownership*
*table, one-utterance-one-turn, running-turn submits). Track 1/2/3 exit*
*criteria and combined smoke pass extended to match.*
*Base SHA: `8964bdce9a7361e3887a43b3dd381f5f979e9a64` (pre-plan baseline; tracks record their actual branch point)*
*Prerequisite audit: none. WINH09 (merged at `da6c35fd997487db23bb15c08eb9056e28413e39`) plus the source grounding recorded above (`P2-D11`).*
*All Phase 2 decisions locked before plan was written (Brian, 2026-09-22).*
*Next step: commit this build plan to `zola-architecture/lore/build-plans/`*
*on `main`, then begin tracks strictly in order 1 → 2 → 3.*
