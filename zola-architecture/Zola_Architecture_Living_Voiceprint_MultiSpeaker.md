# Zola Architecture — Living Voiceprint & Multi-Speaker Awareness

**Document version:** 1.1  
**Status:** Draft — pending lore integration  
**Authored:** Post-Phase 20 planning cycle  
**Depends on:** Phase 18 identity stack (`VoiceEmbeddingStore`, `GatekeeperEngine`, `PerceptionEventBus`, `CampPlus` via sherpa-onnx, Silero VAD v4)

---

## Section 1 — Purpose & Scope

This document defines the architecture for three interconnected capabilities that together constitute Zola's **living voiceprint system**:

1. **Continuous in-session identity tracking** — knowing who is speaking, moment to moment, during an active foreground conversation, without opening a second microphone.
2. **Ambient and introduction-triggered enrollment** — allowing new voices to be registered naturally during conversation rather than exclusively through the formal enrollment flow.
3. **Continuous embedding refinement** — treating each enrolled voiceprint as a living artifact that improves over time through accumulated real-world samples, organized as a pool rather than a single static vector.

These three capabilities are designed as a unified system. They share the same audio tap infrastructure, the same identity event bus, and the same embedding store. They are described in one document because building any one of them in isolation would produce an incomplete and potentially conflicting design.

This document governs how Zola perceives speaker identity during live sessions. It does not govern what Zola does with that identity in terms of memory, behavioral adaptation, or relationship modeling — those are separate architectural concerns addressed in companion documents.

### What This Document Covers

- The audio tap architecture and its relationship to `DeepgramForegroundRecognitionEngine`
- The `LiveSessionIdentityTracker` component and its responsibilities
- The `SpeakerEvent` bus and schema
- Introduction-triggered enrollment — both user-initiated and Zola-initiated
- The UNKNOWN cluster gate — protection against false introduction triggers
- The embedding pool model and pool-based scoring
- Formal enrollment pool seeding — multi-entry initialization
- Continuous refinement — eligibility, mechanics, and drift protection
- Multi-speaker conversation awareness — room model, turn management, speaker switching
- `VoiceEmbeddingStore` schema evolution
- Session lifecycle integration
- Privacy and consent model

### What This Document Does Not Cover

- Camera-based or visual identity (future perception tier)
- Wake-word triggered enrollment (not planned)
- Cloud voiceprint synchronization (explicitly excluded — all identity data is on-device only, always)
- Post-session transcript labeling by speaker (future candidate — full diarization pass)
- Behavioral differentiation per enrolled identity — Zola's personality is her personality; what varies across speakers is conversational context and memory, not character
- Barge-in mechanics — the multi-speaker barge-in exception inherits the Delta 1.6 / 1.8 barge-in architecture when that work lands; this document defines the policy but not the implementation

---

## Section 2 — Foundational Concepts

### The Voiceprint as a Living Artifact

Phase 18 established the voiceprint as a one-time enrollment product. Three prompted phrases were recorded, three embeddings extracted, averaged into one composite vector, and stored. That single vector is what the Gatekeeper has compared against ever since.

This was the right starting point. But a single composite vector captured on one day, in one acoustic environment, under one set of conditions, has a ceiling. Voice is not static. It varies with time of day, distance from the microphone, ambient noise, fatigue, and dozens of other factors. A voiceprint system that does not account for this variation will produce inconsistent confidence scores over time — sometimes too high (false acceptance), sometimes too low (failed recognition of the enrolled user).

The living voiceprint model treats enrollment as the beginning of a process, not the end of one. Every verified interaction is an opportunity to improve the model. Over time, the system accumulates a representative sample of what a person's voice actually sounds like across real conditions — not just what it sounded like on enrollment day.

### Identity Detection vs. Identity Tracking

These are two distinct operations that must not be conflated in the implementation:

**Identity detection** is what the Phase 18 Gatekeeper does. It answers a binary question: "Is the person now speaking someone I recognize, and if so who?" It runs on demand, on a fixed buffer, and produces a single `RecognizedIdentity` result. It is designed for the background-to-foreground activation path.

**Identity tracking** is what this architecture adds. It answers a continuous question: "Who is speaking right now, and has that changed since the last time I checked?" It runs throughout a foreground session, on a rolling basis, and produces a stream of `SpeakerEvent` signals that label the conversation over time. It is designed for the in-session multi-speaker awareness path.

Both use the same underlying model (CampPlus via sherpa-onnx) and the same embedding store. They are architecturally separate components with separate responsibilities and separate lifecycles.

### How This Sits on Top of Phase 18

Nothing in this architecture replaces or modifies Phase 18 components. The Gatekeeper continues to operate exactly as designed — it arms in the background, detects the primary user's voice, and foregrounds Zola. This architecture begins where Phase 18 ends: at the moment Zola is foregrounded and a live session begins.

The Phase 18 Gatekeeper is the door. This architecture is what happens inside the room.

---

## Section 3 — The Audio Tap Architecture

### The Core Constraint

The foreground microphone is owned by a single component during any
active session. No second `AudioRecord` instance is opened. No competing
audio reader is introduced. This constraint was established during Phase
18 mic contention resolution and must not be revisited.

**Correction from original (P22-AUD-01, P22-AUD-02):** The original
version of this document named `GeminiLiveClient` as the foreground mic
owner. The Phase 22 pre-build audit confirmed this was incorrect.
`DeepgramForegroundRecognitionEngine` is the sole owner of `AudioRecord`
during foreground sessions. `GeminiLiveClient` handles AI response
transport — it receives audio back from Vertex AI but does not read from
the microphone. All references to `GeminiLiveClient` as mic owner in
this section have been corrected accordingly.

### The Tap Pattern

`DeepgramForegroundRecognitionEngine` already reads PCM audio in a
continuous loop — `runAudioSendLoop` — which reads chunks from
`AudioRecord` and streams them to the Deepgram cloud endpoint. Those
chunks exist in memory, in Kotlin, for the brief moment between being
read and being sent.

The tap intercepts a copy of each chunk at that moment. The primary
Deepgram send path is completely unchanged. The tap is additive only.

Conceptually:

```kotlin
// Before (Phase 18/21)
while (sessionActive) {
    val chunk = audioRecord.read(...)
    sendToDeepgram(chunk)
}

// After (Phase 22)
while (sessionActive) {
    val chunk = audioRecord.read(...)
    sendToDeepgram(chunk)                  // unchanged — primary STT path
    audioChunkFlow.tryEmit(chunk.copy())   // tap — identity tracker observer path
}
```

`audioChunkFlow` is a `MutableSharedFlow<ShortArray>` with `replay = 0`,
`extraBufferCapacity = 8`, and `onBufferOverflow = DROP_OLDEST`. The
Deepgram send path never waits for the observer. If the identity tracker
falls behind, chunks are dropped silently. The primary STT session is
never degraded.

### Threading Model

`runAudioSendLoop` runs on a blocking background `Thread` — not a
coroutine dispatcher. The `tryEmit` call on `audioChunkFlow` is
non-blocking by design — it returns immediately whether or not the
emission succeeded. This is safe to call from the Deepgram thread. The
identity tracker subscribes to `audioChunkFlow` on a separate
`Dispatchers.Default` coroutine. CampPlus inference runs on that same
background coroutine. The Deepgram send thread is never blocked by
identity tracking work.

### Chunk Format Compatibility

The Phase 22 pre-build audit confirmed: `DeepgramForegroundRecognitionEngine`
captures 16kHz, 16-bit PCM mono audio. This is the same format CampPlus
expects. The tapped chunks require no format conversion before being
passed to the identity tracker.

### Scope of the Tap

The tap is scoped to foreground sessions only. `audioChunkFlow` is
initialized when `DeepgramForegroundRecognitionEngine` starts its audio
loop and cancelled when the loop stops. It has no presence in
`ListeningService` and no relationship to the background Watchdog. The
Watchdog and the tap are mutually exclusive by session state — one is
active when Zola is in the background, the other when she is in the
foreground.

### Wave 5 PCM Guard Policy

`DeepgramForegroundRecognitionEngine` applies a PCM suppression guard
during Live audio playback — the `WAVE5_POST_PLAYBACK_PCM_GUARD_MS`
window. When the guard is active, PCM frames are not sent to Deepgram
(self-hear suppression).

The identity tracker tap obeys the same guard. When the Wave 5 guard
suppresses PCM to Deepgram, no chunk is emitted to `audioChunkFlow`.
The tracker receives no audio during Zola's own speech. Rationale:
voice samples captured while Zola is speaking are likely barge-ins or
ambient noise — not clean speech from an identifiable person. Running
inference on that audio would produce low-confidence, unreliable
results. A parallel unguarded tap path is not introduced. Silence in
the tracker during playback is correct and expected behavior
(P22-D02).

---

## Section 4 — LiveSessionIdentityTracker

`LiveSessionIdentityTracker` is a new component scoped to the foreground session lifecycle. It subscribes to `audioChunkFlow`, accumulates speech segments, runs CampPlus inference, and emits `SpeakerEvent` signals. It has no other responsibilities.

### Responsibilities

- Subscribe to `audioChunkFlow` at session start
- Apply VAD gating to accumulate only real speech (not silence)
- Accumulate speech samples until a CampPlus-compatible window is filled
- Run CampPlus inference on each completed window
- Score the resulting embedding against all enrolled voiceprints in `VoiceEmbeddingStore`
- Emit a `SpeakerEvent` with identity, confidence, and timestamp range
- Handle unknown voices (no enrolled match above threshold)
- Release resources and cancel its coroutine at session end

### VAD-Gated Accumulation

CampPlus requires a minimum of approximately 3 seconds of real speech to produce a reliable embedding. Speech during a live conversation is intermittent — there are pauses, short phrases, overlapping turns, and silence. The tracker must accumulate only voiced frames, not wall-clock time.

Silero VAD is already running in the stack. The tracker uses VAD output to gate accumulation: only frames classified as speech are added to the accumulation buffer. Once the buffer contains 3 seconds of voiced audio, inference runs and the buffer resets.

This means identity resolution latency is a function of how much the person is actually talking, not how many seconds have elapsed. A person speaking continuously will be identified in approximately 3 seconds. A person making short interjections may take longer. This is acceptable and expected.

### Scoring

After CampPlus produces an embedding from each completed window, the tracker scores it against the full enrollment pool in `VoiceEmbeddingStore` using cosine similarity. The scoring model is pool-based (see Section 7) — the tracker takes the maximum similarity score across all pool entries for each enrolled voice, then takes the highest-scoring enrolled voice above threshold as the match.

The confidence threshold for in-session identity tracking is distinct from the Gatekeeper threshold. The Gatekeeper threshold (currently 0.60) was calibrated for background activation — a context where false acceptance has real consequences (unwanted foreground launch). In-session tracking is a lower-stakes context — a misidentification during a conversation is recoverable, whereas a missed background activation is a failure of the primary use case. The in-session threshold is therefore set lower, at **0.50**, as a starting default, with a sanity self-similarity floor of **0.40** below which a result is discarded entirely regardless of it being the best match. Both values must be empirically calibrated on device and documented in the implementing phase progress document.

### Unknown Voice Handling

When no enrolled voice scores above the in-session threshold, the tracker emits a `SpeakerEvent` with `identity = UNKNOWN` and a confidence score reflecting the best match found. This signal is meaningful — it tells the conversation layer that someone is speaking who Zola does not recognize. The conversation layer and `ProvisionalEnrollmentManager` decide what to do with it (see Sections 6 and 9).

A single UNKNOWN event is never sufficient to trigger any user-facing action. See Section 6 for the UNKNOWN cluster gate requirement.

### Authority Boundary

`LiveSessionIdentityTracker` is an observer. It emits signals. It does not:
- Write to `VoiceEmbeddingStore` directly
- Modify conversation state
- Trigger Zola responses
- Make routing decisions

All of those responsibilities belong to components downstream of the `SpeakerEvent` bus.

---

## Section 5 — The SpeakerEvent Bus

### Design

`SpeakerEvent` signals travel on a dedicated flow, separate from the existing `PerceptionEventBus`. The existing bus carries `RecognizedIdentity` signals from the Gatekeeper — those are background activation signals with a different lifecycle and different consumers. Mixing them would create ambiguity about signal source and context.

A new `SessionIdentityBus` carries `SpeakerEvent` signals during foreground sessions only. It is a `MutableSharedFlow` with the same drop-oldest overflow policy as the audio chunk flow. It is session-scoped — created at session start, cancelled at session end.

### SpeakerEvent Schema

```kotlin
data class SpeakerEvent(
    val sessionId: String,
    val identity: SpeakerIdentity,
    val confidenceScore: Float,
    val windowStartMs: Long,
    val windowEndMs: Long,
    val source: SpeakerEventSource
)

sealed class SpeakerIdentity {
    data class Known(val personId: String, val userType: UserType) : SpeakerIdentity()
    object Unknown : SpeakerIdentity()
}

enum class SpeakerEventSource {
    LIVE_SESSION_TRACKER,    // from LiveSessionIdentityTracker during active session
    INTRODUCTION_RESOLUTION  // from the introduction resolution window
}
```

### Consumers

In the initial implementation, the primary consumers of `SessionIdentityBus` are:

- **ConversationIdentityCoordinator** (Section 9) — maintains the live speaker model for the active conversation
- **ProvisionalEnrollmentManager** (Section 6) — listens for UNKNOWN signals and applies the cluster gate before triggering any introduction flow
- **RefinementSampleCollector** (Section 8) — listens for high-confidence KNOWN signals to accumulate refinement candidates

Each consumer subscribes independently. No consumer has authority over another.

---

## Section 6 — Introduction-Triggered Enrollment

### Two Trigger Paths

Ambient enrollment can be initiated in two ways. Both result in the same provisional slot creation and accumulation process.

**Path A — User-initiated introduction:** The primary user says something Zola interprets as an introduction. Natural language patterns include "Zola, this is Marcus," "Meet Marcus," "This is my friend Marcus," or similar. Zola extracts the name from the utterance, creates a provisional slot for that name, and begins attributing unrecognized voice segments to it.

**Path B — Zola-initiated introduction:** When `ProvisionalEnrollmentManager` detects a qualifying cluster of UNKNOWN events (see UNKNOWN Cluster Gate below), it surfaces this to the conversation layer. Zola acknowledges the unknown voice naturally — "I don't recognize that voice — who's joining us?" or similar phrasing consistent with her character. This opens an **introduction resolution window**.

### The UNKNOWN Cluster Gate

This gate is mandatory. A single UNKNOWN `SpeakerEvent` is never sufficient to trigger a Zola-initiated introduction. The shop environment produces transient acoustic events — pneumatic tools, compressor blowoffs, metallic impacts — that can occasionally pass VAD and produce a near-zero CampPlus match, generating a spurious UNKNOWN event. Acting on a single event would cause Zola to interrupt the user every time a tool drops.

`ProvisionalEnrollmentManager` maintains a rolling window of UNKNOWN events. A Zola-initiated introduction is triggered only when:

- At least **2 UNKNOWN events** are received within a **6-second rolling window**
- Each event scored above the 0.40 sanity floor (ruling out pure noise bursts that produce garbage embeddings near zero)

Two consecutive 3-second windows of unrecognized but speech-quality audio is strong evidence that a distinct human voice is present. A dropped tool or compressor burst does not produce two consecutive windows of scored audio above floor. This gate is the difference between a useful ambient awareness feature and a constantly interrupting annoyance.

### Introduction Resolution Window

When Zola asks who is speaking, she opens a time window during which she is listening specifically for a name in response. The default window duration is **8 seconds**. If VAD detects a sustained ambient noise floor spike immediately after Zola asks her introductory question — indicating the shop environment became louder at that moment — the window is extended to **12 seconds** to give the user time to finish what they are doing before responding. The noise spike detection uses the same VAD amplitude signal already flowing; no separate model is required.

During this window, the response can come from either speaker:

**If the unknown speaker answers** ("I'm Marcus"): The utterance serves double duty. It names the provisional slot and simultaneously becomes the first confirmed speech sample toward enrollment. The audio from that utterance is captured and tagged to the new provisional identity.

**If the known speaker answers** ("That's Marcus"): The name is applied to the provisional slot. The known speaker's audio is not tagged to the provisional slot. The tracker continues accumulating audio from the unrecognized voice separately, now with a name to attach it to.

**If no answer is received** within the window, the provisional slot is created with a generated placeholder name (e.g. "Guest-[timestamp]") and accumulation continues. The placeholder name is surfaced in settings and the user can rename it later.

The introduction resolution window does not block conversation. Zola continues listening and responding normally. The window simply flags the enrollment subsystem to be alert for a name signal in the next few utterances.

### Provisional Slot Creation

When a provisional slot is created, a new `EnrolledVoice` entry is written to `VoiceEmbeddingStore` with:
- `enrollmentState = PROVISIONAL`
- `displayName` set to the resolved name or placeholder
- `embeddingPool` empty — no embeddings yet
- `provisionalStartedAtMs` set to the current timestamp
- `provisionalSessionId` set to the current session ID

A provisional voice is **not used by the Gatekeeper** for background activation. It is visible to `LiveSessionIdentityTracker` for in-session tracking purposes, but at a reduced confidence threshold that flags its outputs as provisional.

### Attribution During Accumulation

Once a provisional slot exists, audio segments that score below the enrolled threshold for all confirmed voices — but above the 0.40 sanity floor — are tentatively attributed to the provisional slot. This is the "voice that isn't anyone I already know" heuristic.

In a two-person session (Brian confirmed, Marcus provisional), attribution is reasonably clean. In a three-or-more person session, attribution becomes ambiguous when multiple unknowns are present simultaneously. In that case, provisional accumulation is paused until the room composition becomes clearer. Ambiguous attribution is never used for enrollment — it is better to accumulate slowly with clean samples than quickly with noisy ones.

### Provisional to Confirmed Promotion

A provisional voice is promoted to `CONFIRMED` enrollment state when:
- At least **8 distinct speech windows** have been attributed to it (approximately 24 seconds of real speech total)
- Each attributed window scored above the quality floor of **0.40** cosine similarity against the accumulating pool
- The session has not ended (promotion happens during the session, not after)

Once promoted to CONFIRMED, the voice is treated equivalently to a formally enrolled voice for all in-session purposes. It remains ineligible for Gatekeeper background activation until the user explicitly grants that in settings — a deliberate friction point that protects against accidental background activation by a newly introduced person.

### Provisional Cleanup

If a session ends before a provisional slot reaches the promotion threshold, the slot is retained but marked `PROVISIONAL_INCOMPLETE`. On the next session where that voice is recognized (if recognition is possible from the partial pool), accumulation continues. After 30 days without promotion, `PROVISIONAL_INCOMPLETE` slots are deleted and the user is notified via settings.

### Consent Consideration

Introduction-triggered enrollment is intentional — the primary user chose to introduce someone to Zola, or Zola asked and received confirmation. This is meaningfully different from silent passive enrollment. Even so, the enrolled person may not be aware their voice is being stored on-device. The settings panel should surface all enrolled voices (including provisionally enrolled ones) with enough context that the primary user can explain what was stored and delete any entry. This is a transparency requirement, not a hard consent gate.

---

## Section 7 — The Embedding Pool Model

### Why a Pool

A single composite embedding — even a well-averaged one from three formal enrollment phrases — represents one slice of one acoustic moment. Real voice varies. The pool model acknowledges this by storing a small collection of representative embeddings rather than a single averaged vector.

Each pool entry is a distinct sample, captured under different conditions across different sessions. The pool collectively represents the breadth of what a person's voice actually sounds like. Scoring against the pool means asking "does this audio match any of the conditions under which this person's voice has been observed?" rather than "does this audio match a single average?"

### Pool Structure

Each enrolled voice maintains a pool of up to **20 embedding entries**. Each entry carries:

```kotlin
data class EmbeddingPoolEntry(
    val embedding: FloatArray,
    val capturedAtMs: Long,
    val sessionId: String,
    val source: EmbeddingSource,          // FORMAL_ENROLLMENT, REFINEMENT, PROVISIONAL_ACCUMULATION
    val confidenceAtCapture: Float,
    val ambientConditionTag: AmbientConditionTag
)

enum class AmbientConditionTag {
    QUIET,           // VAD speech ratio high, consistent amplitude
    MODERATE_NOISE,  // some background noise detected
    HIGH_NOISE,      // significant background noise
    UNKNOWN          // condition not determinable
}
```

Ambient condition tagging is a best-effort classification based on the ratio of voiced frames to total frames in the accumulation window and the amplitude variance of the audio. It does not require a separate noise detection model — it is derived from data already available in the VAD pipeline.

### Scoring Against a Pool

When `LiveSessionIdentityTracker` scores an inference embedding against an enrolled voice:

1. Compute cosine similarity between the inference embedding and every entry in that voice's pool
2. Take the **maximum similarity score** across all pool entries as the score for that enrolled voice
3. Compare against threshold

Maximum similarity is used rather than average because the pool is designed to cover variance. A person speaking from across a noisy shop should match the pool entry captured in similar conditions — that match should count, even if it does not match the quiet-room entries.

Pool scoring performance is not a bottleneck. Matrix-multiplying a 1×192 float vector against a 20×192 pool using standard Kotlin loops takes under 1 millisecond on any modern Android chipset. The dominant cost is CampPlus neural network inference, not pool comparison. The 20-entry cap is safe from a CPU overhead perspective at any realistic number of enrolled voices.

### Pool Eviction

When the pool reaches 20 entries and a new entry is to be added:

- The `FORMAL_ENROLLMENT` anchor entry is **never evicted** regardless of pool pressure — it is the recovery anchor if refinement drifts
- The oldest entry tagged `QUIET` is never evicted if it is the only `QUIET` entry — it represents the cleanest possible baseline sample
- Otherwise, the entry with the lowest `confidenceAtCapture` score is evicted
- If scores are equal, the oldest entry is evicted

The goal is to maintain a pool that is both diverse (different acoustic conditions) and high-quality (high confidence captures).

### Formal Enrollment Pool Seeding

When a voice is formally enrolled through the settings flow, the Phase 18 process records three prompted phrases and extracts three individual embeddings before averaging them into a composite. Under this architecture, **all three individual phrase embeddings are stored as separate pool entries**, plus the composite average as a fourth entry, giving the pool four entries from day one.

This is architecturally important. The Phase 18 composite embedding was built by averaging three embeddings, each derived from approximately 3 seconds of speech — matching the duration of live tracking windows. The composite average occupies a slightly different region of the embedding space than any individual 3-second window, because averaging smooths the natural variance across phrases. Seeding the pool with all three individual embeddings alongside the composite ensures the pool has immediate short-duration diversity that matches the live tracking window format. The composite remains as a fourth entry and serves as the formal enrollment anchor that is never evicted.

For previously enrolled voices being migrated from the Phase 18 schema: if the three individual phrase embeddings were not retained (only the composite was stored), the composite is migrated as a single `FORMAL_ENROLLMENT` anchor entry. The pool will build diversity through normal refinement over subsequent sessions. Retroactive phrase-level seeding is not possible without re-enrollment, but re-enrollment is always available through settings.

---

## Section 8 — Continuous Refinement

### What Refinement Is

Refinement is the process of adding new pool entries from verified in-session samples. Every foreground session where a voice is recognized at high confidence generates potential refinement material. The `RefinementSampleCollector` accumulates these samples during the session. After the session closes, a post-session refinement pass evaluates them and adds qualifying entries to the pool.

Refinement is entirely passive. No user action is required. No UI is shown during refinement. The pool simply gets better over time.

### Session Eligibility

A session qualifies for refinement contribution for a given enrolled voice only if:
- That voice was recognized during the session
- The **sustained confidence** across all recognition events for that voice during the session averaged **0.70 or higher** — well above the in-session threshold of 0.50
- At least 3 distinct recognition windows fired for that voice during the session

A single high-confidence detection is not enough. Sustained confidence across multiple windows in the same session is required. This filters out sessions where the person was briefly present or marginally recognized.

### Sample Collection During Session

`RefinementSampleCollector` listens to `SessionIdentityBus`. When it receives a `SpeakerEvent` for a known identity with `confidenceScore >= 0.70`, it retains the inference embedding from that window as a refinement candidate, tagged with the session ID, timestamp, and ambient condition.

Candidates are held in memory only — they are never written to persistent storage during the session. If the session ends abnormally, all candidates are discarded. Only a clean session close triggers the refinement pass.

### Refinement Frequency Policy

Refinement uses a **time-and-variance token system** rather than a simple session-based cap. This better serves extended shop sessions where a person may be present for several hours.

The rules are:
- One refinement pool entry may be added per enrolled voice per **30 minutes of active recognized speech** within a session
- A new entry is only added if its `AmbientConditionTag` adds meaningful coverage — if the pool already contains two or more entries tagged `QUIET`, a new `QUIET` candidate has lower marginal value than a `MODERATE_NOISE` or `HIGH_NOISE` candidate from the same session
- Condition diversity is explicitly prioritized: if the shop environment changes mid-session (e.g. a compressor starts running, raising the noise floor), a high-confidence capture in that new condition is immediately valuable and should be captured even if a `QUIET` entry was already added earlier in the session

This approach ensures that long sessions generate proportionally more refinement value, and that the pool builds acoustic condition diversity rather than redundant entries from the same conditions.

### Post-Session Refinement Pass

The refinement pass runs after `ConsolidationLoop` completes at session end. It is a background job on `Dispatchers.IO`. For each enrolled voice that accumulated refinement candidates during the session:

1. Evaluate whether the session meets the eligibility criteria above
2. Apply the time-and-variance token policy to determine how many entries may be added
3. For each token available, select the best candidate for each underrepresented ambient condition
4. Add qualifying candidates to the pool subject to pool eviction rules
5. Update `lastRefinedAtMs` and increment `refinementCount` on the `EnrolledVoice` record

### Drift Protection

The greatest risk in a refinement system is **identity drift** — the gradual corruption of a voiceprint by low-quality samples that pull it away from the true voice. Three mechanisms protect against this:

**Confidence floor:** No sample below 0.70 confidence is ever added to the pool as a refinement entry. This is a hard floor, not a soft suggestion.

**Anchor preservation:** The formal enrollment entries are never evicted (Section 7). If refinement ever produces a pool that recognizes the voice poorly, the formal enrollment entries remain as a recovery anchor. Re-running the formal enrollment flow resets the pool to a clean state.

**Condition diversity requirement:** The time-and-variance token system actively discourages adding redundant entries from the same acoustic condition. Over-concentration of pool entries in one condition reduces the pool's ability to handle the other conditions — the diversity requirement is also a drift protection mechanism.

---

## Section 9 — Multi-Speaker Conversation Model

### Zola as a Room-Aware Entity

Zola is not a one-on-one assistant. She is a conversational entity who is aware of the room she is in. When multiple people are present, she perceives that. She knows who is speaking. She can address individuals by name, track what each person has said, and respond to the room as a whole or to a specific person as the moment demands.

This is a meaningful departure from the conventional assistant model, and it is the correct model for Zola. A shop environment with multiple people present is the primary use case. Zola must be able to hold her own in a room.

### The ConversationIdentityCoordinator

A new component, `ConversationIdentityCoordinator`, maintains the live speaker model for the active session. It subscribes to `SessionIdentityBus` and maintains a running picture of who is present and who is speaking.

Its state at any moment includes:
- **Active speakers** — enrolled voices who have been recognized at least once in this session
- **Current speaker** — the most recently identified speaker (updated on each `SpeakerEvent`)
- **Speaker history** — a time-ordered log of `SpeakerEvent` signals for the session, used for context reconstruction
- **Unknown voices** — count of distinct unrecognized voice patterns detected (best-effort; true diarization of unknown voices is not attempted)

This state is available to the conversation layer — specifically to whatever component assembles context for Gemini Live — so that Zola's responses can be informed by who is in the room and who asked what.

### Turn Management

**Default behavior — natural pause:** Zola waits for a natural pause in the human conversation before responding. She does not interrupt. In a multi-person conversation, this means she may be tracking and processing what multiple people are saying before she has an opportunity to respond. This is normal and expected.

A natural pause is detected by VAD — when speech activity drops below the active threshold for a defined silence window (approximately 1.0–1.5 seconds). At that point, if Zola has a queued response intent, she delivers it.

**Exception — barge-in:** When something said is sufficiently urgent or directly addressed to Zola in a way that demands immediate response, she can interject before the natural pause. The definition of "sufficiently urgent" inherits from the barge-in architecture (Delta 1.6 / 1.8) when that work lands. For now, the policy is documented as existing and the mechanism is deferred. The bar for interrupting a two-person human conversation is higher than for a one-on-one session — this distinction must be explicitly defined when barge-in is implemented.

### Speaker Switch Handling

When `ConversationIdentityCoordinator` detects a speaker change — the `SpeakerEvent` identity differs from the current speaker — it updates the current speaker and logs the switch to the speaker history.

Zola's response to a speaker switch is contextual, not automatic:

**If the new speaker is continuing a topic already in progress:** Zola does not explicitly acknowledge the switch. She understands who is now speaking and continues the conversation with that understanding.

**If the new speaker introduces a new topic or addresses Zola directly:** Zola responds to the content naturally, and may address the person by name if it adds clarity or warmth — "Good question, Marcus" or similar, where using the name is genuine rather than mechanical.

**If the new speaker is unknown:** The `ProvisionalEnrollmentManager` UNKNOWN cluster gate begins counting. If the gate threshold is reached, Zola may ask who is joining at the next natural conversational pause. She does not ask mid-sentence while someone else is speaking.

Zola never robotically announces speaker switches ("I detect that Brian is now speaking"). Speaker awareness is ambient to her behavior, not a feature she narrates.

### Context Continuity Across Speaker Switches

The active conversation context — what topics are in play, what questions are open, what Zola was in the middle of explaining — survives speaker switches. Zola does not reset her conversational state when a new person speaks.

The speaker history log maintained by `ConversationIdentityCoordinator` allows Zola to know not just what was said but who said it. This can be surfaced to Gemini Live as part of the conversation context — "Brian asked X, Marcus added Y, Brian responded Z" rather than a speaker-agnostic transcript. This identity-tagged context is richer and allows Zola to respond in ways that acknowledge who contributed what.

### Addressing the Room vs. Addressing an Individual

When Zola formulates a response:

- If the response is directly answering a question from a specific person, she addresses that person (by name if it aids clarity)
- If the response is relevant to everyone present, she addresses the room without singling anyone out
- If she is asking a clarifying question, she addresses the person who raised the ambiguity

She does not mechanically alternate between people or force equal-time engagement. She responds to what is actually happening in the conversation.

### What Zola Knows About Who Is in the Room

At any moment during a session, Zola's context includes:
- Which enrolled voices are present (recognized at least once this session)
- Who spoke most recently
- A speaker-tagged history of the current session's turns
- Whether any unknown voices have been detected and whether the cluster gate has been triggered

This information is available to the conversation layer and can inform Zola's responses naturally. She does not maintain a formal "room attendance" list as a separate construct — the speaker history is the room model.

---

## Section 10 — VoiceEmbeddingStore Schema Evolution

### Current Schema (Phase 18)

```kotlin
data class EnrolledVoice(
    val displayName: String,
    val embedding: FloatArray,
    val enrolledAtMs: Long
)
```

### Evolved Schema

```kotlin
data class EnrolledVoice(
    val displayName: String,
    val embeddingPool: List<EmbeddingPoolEntry>,  // replaces single embedding
    val enrolledAtMs: Long,
    val enrollmentState: EnrollmentState,
    val refinementCount: Int,
    val lastRefinedAtMs: Long?,
    val provisionalStartedAtMs: Long?,            // null if formally enrolled
    val provisionalSessionId: String?,            // null if formally enrolled
    val gatekeeperEligible: Boolean               // false for PROVISIONAL voices
)

enum class EnrollmentState {
    FORMAL,                  // enrolled through the settings enrollment flow
    CONFIRMED,               // ambient enrollment that reached promotion threshold
    PROVISIONAL,             // accumulating; not yet promoted
    PROVISIONAL_INCOMPLETE   // session ended before promotion; accumulation may continue
}
```

`EmbeddingPoolEntry` schema is defined in Section 7.

### Backward Compatibility

Existing formally enrolled voices stored under the Phase 18 schema must be migrated on first read under the new schema:
- The single `embedding: FloatArray` becomes the composite anchor entry in `embeddingPool` with `source = FORMAL_ENROLLMENT` and `confidenceAtCapture = 1.0`
- `enrollmentState = FORMAL`
- `gatekeeperEligible = true`
- `refinementCount = 0`
- Provisional fields `null`

If the three individual phrase embeddings from formal enrollment were retained separately (this depends on whether the implementing phase chooses to store them), they are added as additional `FORMAL_ENROLLMENT` pool entries alongside the composite. If only the composite was stored (the Phase 18 default), the pool starts with one entry and builds diversity through refinement. Re-enrollment through settings is always available to seed the full four-entry pool.

Migration runs on first access after the schema upgrade. No data is lost. The migration is safe to run multiple times (idempotent).

### Storage Size Consideration

A CampPlus embedding is 192 floats × 4 bytes = 768 bytes per entry. A pool of 20 entries per voice is approximately 15KB per enrolled voice. With pool metadata, the total is under 25KB per enrolled voice. `EncryptedSharedPreferences` handles this comfortably. The storage concern is negligible even with 10 or more enrolled voices.

---

## Section 11 — Session Lifecycle Integration

### Where This Work Lives in the Session

The session lifecycle, as established by the Consolidation Loop architecture, has a defined sequence at session close. This architecture adds work at two points:

**During session — passive collection:**
`LiveSessionIdentityTracker` and `RefinementSampleCollector` run throughout the session. They do not interact with the Consolidation Loop. Their work is parallel, not sequential.

**After session close — refinement pass:**
The refinement pass runs after Step 7 of the Consolidation Loop (ephemeral buffer clear). It is the final post-session operation. Ordering matters: the session must be fully closed before refinement runs, because refinement decisions are based on the whole session's recognition history, not a partial view.

The refinement pass is a background job on `Dispatchers.IO`. It does not block session close. The session is considered closed when Step 7 completes — the refinement pass runs asynchronously afterward.

### Provisional Cleanup at Session End

When a session closes, `ProvisionalEnrollmentManager` evaluates any provisional slots that were active during the session:
- Slots that reached the promotion threshold during the session are already `CONFIRMED` — no action needed
- Slots that did not reach the threshold are marked `PROVISIONAL_INCOMPLETE`
- The partial embedding pool accumulated so far is retained for the next session

**Tracker lifecycle** is bound to the `DeepgramForegroundRecognitionEngine`
audio loop, not to the assistant auth session or the Gemini Live
WebSocket connection. The tracker requires live PCM audio — it must be
active exactly when audio is flowing and inactive when it is not
(P22-D03).

**Start:** `LiveSessionIdentityTracker.start()` is called when
`DeepgramForegroundRecognitionEngine` starts its audio loop — the
existing `onResume`/foreground path in `MainActivity` where
`ForegroundSpeechRecognitionEngine.startRecognition()` is called.

**Stop:** `LiveSessionIdentityTracker.stop()` is called when
`DeepgramForegroundRecognitionEngine` stops its audio loop — the
existing `onPause`/`stopRecognition()` path.

Both hooks are wired in `MainActivity` alongside the existing
recognition start/stop calls. `LiveSessionIdentityTracker` is a
session-scoped object created at activity resume and released at
activity pause.

### Session End Hook

The Phase 22 pre-build audit confirmed that
`SessionMemoryCoordinator.onSessionEnd()` does not exist (P22-AUD-25,
P22-AUD-27). The build plan adds
`SessionMemoryCoordinator.registerSessionEndHook(tag, block)` — a
lightweight, ordered hook registry. Hooks execute in registration order
after the existing turn buffer is cleared (after Consolidation Loop
Step 7). This is the attachment point for:

- `ProvisionalEnrollmentManager` session close evaluation
- `RefinementSampleCollector` eligibility check and refinement pass
  dispatch

Both register their hooks at session start and are automatically called
at session end.

### Lifecycle Ordering Summary

```
Deepgram audio loop starts
    ↓
LiveSessionIdentityTracker.start()
RefinementSampleCollector.start()          ← both start here
    ↓
[session active — passive collection throughout]
    ↓
Deepgram audio loop stops
    ↓
LiveSessionIdentityTracker.stop()
RefinementSampleCollector.stop()           ← both stop here
    ↓
[separately, at assistant session end:]
Consolidation Loop Steps 1–7 (existing)
    ↓
SessionMemoryCoordinator registered end hooks fire in order:
    → ProvisionalEnrollmentManager.onSessionClose()
    → RefinementSampleCollector.onSessionClose()
    ↓
Refinement pass (background, async — Dispatchers.IO)
    ↓
Session fully closed
```

### Interaction with Phase 20 Session Scopes

Phase 20 introduced initiative session scopes and resurfacing logic
wired into `SessionMemoryCoordinator.onSessionStart()`. The session end
hook registry is additive — it appends new post-session work after the
existing consolidation sequence. Phase 20 initiative and resurfacing
logic is unaffected.

---

## Section 12 — Privacy & Consent Model

### On-Device Always

All voiceprint data — enrolled embeddings, pool entries, provisional slots, refinement candidates — lives on-device in Keystore-backed `EncryptedSharedPreferences`. No embedding is ever transmitted to any server. No raw audio is ever stored. This is an absolute constraint inherited from Phase 18 and extended through this architecture.

### What Is Stored

The embedding store contains:
- Embedding vectors (numerical arrays — not audio)
- Display names (provided by the user)
- Timestamps and session IDs (for auditability)
- Ambient condition tags (derived from audio statistics, not audio itself)

No raw audio. No transcripts tied to individual voices. No biometric data beyond the embedding vectors themselves.

### User Control

The primary user has full control over the embedding store through the settings panel:
- View all enrolled voices and their enrollment state
- Delete any enrolled voice (formal, confirmed, or provisional)
- Rename any provisional or confirmed voice
- Review refinement history (count and last refinement date) for any enrolled voice
- Explicitly grant or revoke Gatekeeper background activation eligibility per enrolled voice

Deletion is immediate and permanent. There is no soft delete or recovery path. This is consistent with the Phase 18 principle that the user can always remove identity data entirely.

### Gatekeeper Eligibility as a Gate

Provisionally enrolled and confirmed voices are not eligible for background Gatekeeper activation without explicit user permission. The primary user must affirmatively enable background activation for a given enrolled voice in settings. This prevents a scenario where a newly introduced person could subsequently trigger Zola to foreground without the primary user's knowledge.

### Backup Exclusion

The backup exclusion rules established in Phase 18 cover the encrypted preferences file. The evolved schema stores new data in the same encrypted preferences file and therefore inherits the same backup exclusion automatically. No additional backup rule changes are required.

### Transparency for Introduced Parties

When a voice is enrolled through the introduction flow, the enrolled person may not be aware of it. The primary user bears responsibility for transparency with people they introduce to Zola. The settings panel makes all enrolled voices visible and deletable, providing the mechanism for the primary user to manage this. No automatic notification to the introduced party is implemented — Zola runs on the primary user's device and the primary user controls what is stored on it.

---

## Section 13 — Identity Metadata Storage

### The On-Device Constraint (unchanged and absolute)

All voiceprint embedding data — enrolled pool entries, provisional
accumulation buffers, refinement candidates — lives on-device in
Keystore-backed `EncryptedSharedPreferences`. This constraint is
absolute and inherited from Phase 18. No embedding vector, no raw
audio, and no biometric-adjacent data is ever written to Firestore or
transmitted to any server.

### What Goes to Firestore

Embedding vectors are biometric-adjacent and stay on-device. The
following are relational and operational metadata — not biometric —
and belong in Firestore:

- The fact that a voice named "Breanna" is enrolled, and when
- The current enrollment state (provisional, confirmed, formal)
- The pool size and last refinement date for a confirmed voice
- The window accumulation count for a provisional slot
- Whether a voice is eligible for Gatekeeper background activation

This metadata has no discriminatory power on its own. It is the same
class of data as any other entity attribute in the world model.

### Firestore Path

Identity metadata is written to:

```
users/{userId}/world/voice_identities/{voiceId}/
```

Where `voiceId` is derived from the `VoiceEmbeddingStore` key for that
voice — normalized to a Firestore-safe identifier.

Document schema:

```
{
  displayName: String,          // user-provided name e.g. "Breanna"
  enrollmentState: String,      // "PROVISIONAL" | "CONFIRMED" | "FORMAL"
  gatekeeperEligible: Boolean,  // explicit user-granted permission
  poolSize: Int,                // count of pool entries currently on-device
  refinementCount: Int,         // total refinement passes applied
  lastRefinedAtMs: Long?,       // null if never refined
  enrolledAtMs: Long,           // first enrollment timestamp
  provisionalWindowCount: Int?, // null if not provisional
  promotedAtMs: Long?           // null if not yet promoted
}
```

### Write Policy

Identity metadata is written to Firestore at these moments:

- **On formal enrollment** — when `VoiceEmbeddingStore.saveEmbedding()`
  is called from the enrollment flow
- **On provisional slot creation** — when `ProvisionalEnrollmentManager`
  creates a new slot
- **On provisional promotion** — when a provisional slot reaches the
  confirmation threshold
- **After each refinement pass** — to update `poolSize`,
  `refinementCount`, `lastRefinedAtMs`
- **On deletion** — document deleted when voice is removed from
  `VoiceEmbeddingStore`

All writes are fire-and-forget on `Dispatchers.IO`. They do not block
any user-facing or session-active path.

### UI Visibility

The settings panel reads identity metadata from Firestore to display
enrolled voices — names, states, pool sizes, refinement history. It
does not read `VoiceEmbeddingStore` directly for display purposes.
`VoiceEmbeddingStore` remains the source of truth for embeddings;
Firestore is the source of truth for what the UI shows.

### Future Bridge to World Model

This section establishes the foundation for a future link between a
voice identity and a PERSON entity in the world model. When a
provisional voice is given a name and confirmed, the voice identity
document is the natural attachment point for a `linkedEntityId` field
pointing to the corresponding PERSON entity. That linkage is not
implemented in Phase 22. The schema above does not include
`linkedEntityId` yet, but the path structure accommodates it without
migration.

---

## Section 14 — Open Questions

**OQ-VOICE-01 — In-session confidence threshold calibration**
Starting defaults: tracking threshold 0.50, sanity floor 0.40. Both must be calibrated empirically on-device across multiple acoustic conditions — quiet office, moderate shop noise, heavy shop noise. Too low on the tracking threshold produces false speaker assignments. Too high produces tracking gaps. Calibration results must be documented in the implementing phase progress document and the final values recorded in `DESIGN_DECISIONS.md`.

**OQ-VOICE-02 — Unknown voice diarization in multi-unknown sessions**
When two or more unknown voices are present simultaneously, provisional attribution becomes ambiguous. The current architecture pauses provisional accumulation in this case. A future enhancement could attempt to separate unknown voices by embedding clustering — treating embeddings that are consistently dissimilar as belonging to different speakers. This is non-trivial and deferred to a later phase.

**OQ-VOICE-03 — Refinement frequency policy**
Resolved. The time-and-variance token system defined in Section 8 governs refinement frequency: one entry per 30 minutes of active recognized speech, prioritizing ambient condition diversity over recency. This replaces the original one-per-session cap.

**OQ-VOICE-04 — Pool size cap empirical calibration**
Resolved. The 20-entry pool cap is confirmed safe from a CPU overhead perspective — pool scoring against 20 entries takes under 1 millisecond on modern Android chipsets; the bottleneck is CampPlus inference, not pool comparison. 20 entries remains the cap. Revisit only if on-device benchmarking during implementation reveals unexpected overhead.

**OQ-VOICE-05 — Provisional minimum speech duration**
The 8-window promotion threshold (approximately 24 seconds of real speech) is an initial estimate. The right value depends on how quickly CampPlus embeddings converge to a stable representation for a new voice. This should be tested empirically during Phase implementation and the final value recorded in `DESIGN_DECISIONS.md`.

**OQ-VOICE-06 — Barge-in policy for multi-speaker urgency**
The barge-in exception inherits from Delta 1.6 / 1.8. Until that work lands, the policy is natural-pause-only. When barge-in is implemented, the multi-speaker urgency criteria must be explicitly defined — the bar for interrupting a two-person human conversation is higher than for a one-on-one session and must be specified at that time.

**OQ-VOICE-07 — Introduction resolution window duration**
Resolved. Default window is 8 seconds. If VAD detects a sustained ambient noise floor spike immediately after Zola asks her introduction question, the window extends to 12 seconds. The noise spike detection is derived from the existing VAD amplitude signal — no additional model required.

---

*Zola Architecture — Living Voiceprint & Multi-Speaker Awareness*  
*Version 1.1 — Post-Phase 20 planning cycle*  
*This document governs implementation. No code is written in the implementing phase until this document is committed to the repository and all open questions that block implementation are resolved. OQ-VOICE-03, OQ-VOICE-04, and OQ-VOICE-07 are resolved within this document. OQ-VOICE-01, OQ-VOICE-05 require on-device calibration during implementation. OQ-VOICE-02 and OQ-VOICE-06 are deferred.*
