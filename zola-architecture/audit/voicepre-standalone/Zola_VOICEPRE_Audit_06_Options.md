# VOICEPRE Audit 06 — Options and supportability

A, B, and C are scored separately for barge-in and for wake-free attention. Static feasibility is not a passed runtime test. Config-only meets **none** of SYM-01 through SYM-05 as a fix. A headset can shrink echo and does not add a buffer or a listener.

## Symptom coverage

| | A. Config / plugin | B. Small Hermes voice patch | C. Zola-owned audio (client or helper) |
|---|---|---|---|
| SYM-01 self-echo | No new mechanism. Text matcher stays. | Can keep the mic closed during playback and add pre-roll so follow-up need not open late. Does not add acoustic cancellation unless the patch also feeds a reference. | Can mute or AEC against a reference **if** it owns playback too. Still needs the text matcher. Unproven on this hardware. |
| SYM-02 clipped words | No pre-roll hook. | Add a ring buffer on `voice.record` and/or keep the barge buffer. This is the direct repair for the known hole. | Same buffer in the owner process. |
| SYM-03 talk-over | Flipping `barge_in` cuts audio and **drops** the words (`AUD-06`). | State-aware trip plus a client admit path. This is the smallest design that can pass S36 (a) and (b) together. | Do not arm Hermes barge-in. Detect speech locally, stop the player, then submit through the client. |
| SYM-04 wake-free | No attention gate and no continuous STT. | A "small" patch does not include this. Continuous STT plus an addressee policy is a large Hermes change, close to a voice-layer fork. | Possible, because the stream already exists. Still a new policy, not a consequence of owning the device. |
| SYM-05 first audio and gaps | No chunker or player change. | Could speak larger chunks or stream, but that is `S34`/`S55`, a different patch from barge-in. | Only if the new player overlaps synth and playback on one stream. Owning the mic does not speed TTS. |

## A — Supported seams only

What exists:

- `voice.barge_in`, `barge_in_grace_seconds`, `barge_in_threshold_multiplier` (`methods_voice.py` L158–161, L208–216).
- `voice.silence_duration`, beep, stop phrases.
- `voice.toggle` on/off/tts. `tts` is a **flip**, not "set off" (`L660–664`).
- `voice.tts` for a one-shot line (P9).
- `prompt.submit` for an already-admitted transcript.
- Plugin RPCs in `zola_workspace` (proactive claim, not audio).

What does not exist: a clarify-aware trip, record pre-roll, `voice.record cancel`, a capture id, a playback-completed event, an addressee gate, a hook a plugin can use to wrap `full_duplex_listen`.

**A meets none of the requested capabilities.** It is the right place to leave the system until a proof and an amendment exist. Raising the barge threshold does not make the trip clarify-aware.

## B — Smallest Hermes change set

On this pin, confirmed absent (Audit 02): capture id, record cancel, record pre-roll, clarify check inside `_fd_trip`.

Smallest set that addresses barge-in and first words, and does not pretend to be wake-free:

1. `voice.record` keeps a bounded pre-roll (about 1.2 s, the figure already used by `full_duplex_listen`) and can start without discarding it. Beep moves after the buffer is armed, or the beep is excluded from the buffer.
2. `voice.record cancel` discards audio, does not emit a transcript, and does not resume wake until the pipeline is idle (`S52`).
3. Transcript and terminal status carry the capture id the client sent or Hermes minted (`S53`).
4. `_fd_trip` takes a policy: during reply playback, cut TTS and emit a transcript **with an id**; during an open clarify, do not latch `voice.interrupted` and do not `agent.interrupt()`; the client already has a bound capture for the answer.
5. Client: one new admission arm so that id is Accepting as an interruption, after the turn is cancelled, still inside `TranscriptAdmission.Decide`. `P7-D04` needs an amendment that says "unbound" does not include this id.

Not in the smallest set: streaming STT, addressee model, new TTS provider, WebRTC, editing the agent loop.

Upstream: this audit did not find those five behaviors on `345cd2b`. No newer Hermes commit was checked out. Availability of a later upstream patch is **UNVERIFIED**. Do not treat "latest Hermes" as installed.

Ownership stays Hermes. Echo strategy stays "don't listen until playback is actually done," plus the text matcher. Acoustic echo is unimproved unless Windows enhancements happen to be on, which is UNKNOWN.

Maintenance: `P2-D10` says Hermes source is never edited. `S56` records a preference not to fork. A patch on a detached pin will miss upstream security fixes unless someone rebases it. That cost is real and smaller than owning the whole agent. It is still a decision, not a technical impossibility.

Regression surface: clarify latch (`P4-D28`), `P2-D13` text-mode trip, P7 drop reasons, wake resume race (`S51` class — not proven fixed), follow-up double-listen if both the FD listener and `voice.record` run. Rollback: revert the pin delta and ship the previous client; profile `barge_in` stays false until the client knows the new id.

Effort: one Hermes voice module set plus `TranscriptAdmission` and the interrupt handler. Not a new process.

## C — Client-owned audio, or a supervised helper

Hermes keeps the turn, memory, and tools. The new owner captures, optionally transcribes, and plays. There is no fourth brain.

### Supported path for text

- Admitted text still goes to `prompt.submit` on the current session.
- A spoken reply's text still arrives as `message.delta` / `message.complete`.
- A one-shot line can still be `voice.tts`, **or** the owner speaks it and Hermes must not.

### Missing seams

- No absolute "TTS off, voice mode on." `voice.toggle tts` flips (`methods_voice.py` L660–664). Stop speaking depends on off-then-on.
- No RPC that says "do not open the microphone." The client can only avoid calling `wake.start` / `voice.record`. A restarted serve with voice mode on can still open them if something else calls those methods. One owner means the client must be the only caller (`C3`) **and** Hermes voice capture must stay disarmed.
- `voice.client_direct` is HTTP `/api/audio` for cloud provider keys (`voice_client_config.py` L1–10). It is forbidden by `P2-D01` and it does not stream the local Whisper mic. It is not option C.
- The ffplay monitor will not see a new player (Audit 05).

### Client-owned

The WinUI process would open WASAPI or sounddevice, run VAD, and play. Pros: one less process, same lock and UI thread can gate it. Cons: a capture glitch takes down the avatar; the UI thread must not run STT; `P2-D01` changes; P9 and presence both move.

### Supervised helper

A child process the client already knows how to watch (the serve supervisor is the pattern, not a drop-in). Pros: mic and player can restart without killing the window; AEC reference and the ring buffer sit beside the player; Hermes stays stock. Cons: another lifecycle (lock, crash, device loss); a protocol for "candidate utterance" versus "admitted turn"; the client must still be the only admit authority.

Both must suppress Hermes capture and Hermes playback or she will speak twice and listen twice.

Echo: the helper can tap PCM before the device and run endpoint AEC or AEC3. The client-owned path can do the same. Neither is proven here. Pre-roll lives in that process. Clarify routing stays in `TranscriptAdmission` with the bound id. Correlation is the capture id from Audit 06-B, even if Hermes never sees the audio: the **client** mints it. Cancel means drop the buffer and do not submit. P9: split `ReasonCapture` as in AUD-13; `delivered` follows the helper's completion, not ffplay.

Effort: larger than B. New audio code, a player, a gate amendment, presence retarget, and a proof. Maintenance is Zola's, which is the point of not forking Hermes. Regression surface is every voice state in Audit 05 plus device hot-plug.

Rollback: stop the helper, turn Hermes voice back on, previous client build. Profile TTS provider can stay.

## What this does not decide

B is the smallest change that can restore talk-over and the first words **if** the patch is allowed. C is the only option in this set that can also hold a wake-free stream without growing Hermes into a second product. A cannot. The synthesis separates those two recommendations. Neither is a locked decision.
