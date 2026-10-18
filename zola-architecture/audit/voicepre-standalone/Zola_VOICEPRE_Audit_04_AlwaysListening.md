# VOICEPRE Audit 04 — Wake-free attention and Android lessons

Android is a behavioral reference. It is on `zola-main` at `a139ccac` and was not switched. The working tree has deleted `app/src/main/java/com/beebo/zolaassistant/speech/**`. Those files were read from `HEAD` blobs. `ListeningService`, the watchdog, and room-reading were read from the working tree. Nothing here is a Windows requirement.

## 1. Was Android capture continuous?

**Background: duty-cycled, and it does not transcribe.**

[WORKING TREE] `ListeningService.runWatchdogLoop` (`ListeningService.kt` L191–231) reads a Silero window, then `delay(VAD_IDLE_GAP_MS)`. `WatchdogConstants.kt`: window 512 samples, idle gap 100 ms, speech threshold 0.75, gatekeeper buffer 3000 ms. A hit records a short buffer and runs speaker verification. The file header says the service owns the mic only while the activity is backgrounded.

**Foreground: continuous cloud streaming, and it is a different engine.**

[HEAD BLOB] `DeepgramForegroundRecognitionEngine` is the foreground STT. `startRecognition` returns `SKIPPED_SPEAKING` when `isSpeaking()` is true (L245–247). While a session is already up, the capture loop still reads the mic but the post-playback guard is 220 ms (`WAVE5_POST_PLAYBACK_PCM_GUARD_MS`, L850) before PCM is sent again (L626–656). That is "do not feed the recognizer her own audio," not a second local transcript.

While Zola spoke, foreground STT either did not start or did not upload PCM, plus a short tail. Background VAD could still see energy; it did not produce text.

## 2. What directedness gates

[WORKING TREE] `DirectednessEvaluator.evaluate` (`DirectednessEvaluator.kt` L42–72) folds four signals into `ADDRESSED`, `NOT_ADDRESSED`, `LIKELY_ADDRESSED`, or `UNKNOWN`.

Callers that were found:

- `MainActivity.bindP20T5RoomReadingPhase8Wiring` (L2796–2803) builds a `RoomReadingGate` and assigns `ProactiveDeliveryCoordinator.roomReadingGate`. The VAD callback only calls `recordVadEvent()`.
- `ProactiveDeliveryCoordinator.evaluateRoomState` (L217–229) and `buildDeliveryPlan` (L274) use that gate to pick Hold, Check-in, Ambient, or Urgent (`selectTier` L233–239).

That is **outgoing** proactive speech (and a room state), not the decision to accept an incoming utterance. `QueryProcessor` does not call `DirectednessEvaluator`. A dismissal substring that drops some incoming lines was reported on `MainActivity.handleQuery` by the file search; it is a separate "does this text contain zola during a dismissal window" check, not the four-signal evaluator. It is not a Windows feature and it is not a complete addressee gate.

**VOICEPRE-AUD-15** [GAP] MEDIUM — SYM-04, `S19`, Master Plan §12. Windows has no directedness function at all. Android's version does not solve activation. Copying it would not decide which transcripts become turns.

## 3. What is reusable, and what is coupled

Reusable as a contract, not as Kotlin:

- One mic owner. Background and foreground do not both hold `AudioRecord`.
- Do not transcribe the always-on buffer. The gatekeeper buffer is discarded after a speaker check.
- While assistant audio is playing, do not send mic PCM to STT, and keep a short tail (Android used 220 ms; that number is not a Windows target).
- Directedness is an initiative filter. It is allowed to say "stay quiet." It is not an authenticator.
- A final transcript, not a partial, is what becomes a turn.

Coupled, and not a drop-in:

- Firebase uid, `LocalMemoryCache`, CampPlus enrollment, Deepgram WebSocket, Gemini Live playback, Firestore-backed initiative queues.
- The working tree's deleted `speech/` package means the live Android checkout and HEAD already disagree. Do not treat either as a stable library.

## 4. Three different missing Windows behaviors

| Need | What Windows does now | What is still missing |
|---|---|---|
| Idle, no wake word | Resting state runs sherpa for "hey zola" only (`P2-D04`). No STT. | A policy for when ambient speech may become a turn, and a capture that is already rolling so the first words exist. |
| Continued conversation | After a reply, one `voice.record` if the monitor says she finished (`P4-D18`). Then wake again. `auto_restart=False`. | Another utterance after silence, without "hey zola", and without opening the mic only after the beep. |
| Answer to her question | Clarify capture is bound to the request and opens after she finishes the question (`P7-D05`, `VoiceController` question path). | The same first-word hole as any other `voice.record`. Talk-over during the question is the thing `P4-D28` turned off. |

These three are not one feature. Idle attention can be false. A follow-up window can be true. A clarify binding can be true. SYM-04 asks for the idle case. SYM-02 and SYM-03 are about the other two.

## 5. Local VAD plus bounded STT, streaming local STT, cloud streaming

No provider is selected.

| Approach | Privacy | Cost | Machine | Disconnect | Admission |
|---|---|---|---|---|---|
| Local VAD + bounded utterance STT (what Hermes record already is, minus the pre-roll) | Audio stays on the PC if STT stays `local` (`P2-D02`). | No per-minute cloud STT. | Whisper `base` on CPU was ~1–1.6 s per clip [HISTORY]. A always-on VAD is cheap; a always-on Whisper is not, so STT should run on bounded clips. | Works offline for STT. The conversational model may still be cloud. | The clip is explicit, so P7 can still require an Accepting generation. |
| Streaming local STT | Audio stays local. Partials exist before endpoint. | Engine install (`P2-D17`). | Holds a model resident. | Offline STT. | Partials must not be turns, memory, or approvals. |
| Cloud streaming (Android foreground shape) | PCM leaves the machine for the whole listen, not just her replies. `P9-FIX-TTS` already sends **reply text** to Deepgram. Continuous mic audio would be a larger export. | Metered for as long as the socket is open. | Lighter CPU, needs network. | A drop ends the listen; Android reconnected without replaying audio. | Same rule: only a final that passes the attention gate is a turn. |

`P2-D02` currently turns off Hermes cloud STT fallback. A cloud stream would be a new decision, not a config flip.

## 6. Evidence that he is talking to her

Recognizing Brian's voice does not mean the words were for Zola, and it does not authorize a send.

| Evidence | False accept | False reject |
|---|---|---|
| He just finished a turn with her, and the next utterance is inside a short window | He turns and talks to someone else in that window | He pauses longer than the window and has to wake her |
| The utterance is an answer shape right after her question | Someone else answers | He answers before the window opens (today's clip) |
| He says her name | The name appears in a story or on the TV | He never uses the name, which is the point of SYM-04 |
| A second voice or a conversational rhythm (Android signals 2 and 4) | Two people including him, and he is the one addressing her, so she stays silent | TV dialogue, or a rhythm that looks like turn-taking with her |
| Speaker match | A similar voice, or the TV playing him | He fails the threshold and she ignores him |
| Shop noise energy | The VAD opens a clip on a grinder or a radio | — |

None of these belong in the tool-approval path. `P4-D07` keeps command approval visual. `P8` passphrase sends are a separate gate. Ambient text must not satisfy them.

## 7. State and retention

A wake-free design needs states that today's client does not have:

| State | Listens | May become a turn | May be stored |
|---|---|---|---|
| Paused (lock, suspend, Text, mute) | No | No | No |
| Ambient | VAD, maybe a rolling buffer | No | No transcript. Buffer overwritten. |
| Continuation window | Yes, already rolling | Yes, if the window is open and the utterance is not echo | The admitted turn only, through the existing submit path |
| Awaiting her question | Yes | Yes, bound to that clarify id | The answer only, as the clarify response |
| Rejected ambient | The clip existed | No | Discard. Not memory, not a background prompt, not an approval |

Android background audio never became a transcript. Android foreground audio **did** become a user turn unless a narrow dismissal rule dropped it. The Windows rule has to be the stricter one: ambient text is not a turn.

**VOICEPRE-AUD-10** [GAP] HIGH — SYM-04, `S19`, `P2-D04`, Master Plan §12 L610–666. Idle wake-free conversation is not implemented. Wake, the mic button, and Ctrl+Space are the starters. After one utterance the recorder stops (`auto_restart=False`). This is a deferred target, not a regression of a shipped feature.
