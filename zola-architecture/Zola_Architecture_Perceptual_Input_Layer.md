# Perceptual Input Layer

### Foundational Architecture for Ambient Awareness, Identity Recognition, and Perception-Driven Presence

---

## Vision

Zola's awareness of the world has until now been entirely reported.

She knows what the user tells her. She knows what the phone's sensors
measure. She knows what past conversations have left in memory. Every
signal she receives is mediated — filtered through the user's words,
through app notifications, through scheduled checks. She does not
observe. She is informed.

This document defines the system that changes that.

The **Perceptual Input Layer** gives Zola the ability to directly
observe her environment — to see and to hear — not as a surveillance
mechanism, but as the foundation of genuine situational awareness. It
transforms Zola from an assistant who works from reports into a
presence that shares the user's world.

The perceptual layer does not replace the user as the primary
information source. It augments everything else. What the user says is
still the highest-trust signal. What Zola observes enriches, confirms,
and contextualizes it.

Together, the perceptual layer and the systems it feeds should
eventually feel less like:

> "an assistant that listens when spoken to"

and more like:

> "a presence that is genuinely aware of what is happening around it."

---

## Core Philosophy

### Perception Is Not Surveillance

The distinction between ambient awareness and surveillance is not
technical — it is architectural.

Surveillance captures and stores raw sensor data. It records what
happened. It accumulates evidence. It creates a historical record the
user cannot see or control.

Ambient awareness observes, interprets, acts, and releases. Raw sensor
data is never stored. What is stored is the meaning extracted from
it — a typed observation, a confidence score, an event on the bus.
The frame is gone. The interpretation remains only as long as it is
contextually relevant.

This distinction must be preserved at every layer of implementation.
Any path that persists raw camera frames, raw audio recordings, or
uninterpreted sensor streams is an architecture violation regardless
of the stated intent.

### The Watchdog Sees the Room. Active Perception Understands It.

Two fundamentally different modes of perception exist in this system.
They are not the same capability running at different intensities.
They are different systems with different purposes, different power
contracts, and different outputs.

The **Watchdog** maintains peripheral awareness. It is not analyzing.
It is noticing. Its only job is to detect that something has changed
and hand off to the system that can understand what that change means.

**Active Perception** understands. It runs full vision and audio
analysis, extracts typed observations, generates structured events,
and feeds them to the Environmental Event Bus. It does this work
because the Watchdog told it something warranted attention.

Traditional systems collapse these two modes. A camera either runs
full analysis or is off. This produces a binary choice between battery
drain and blindness.

This architecture separates them permanently.

Traditional perception systems:

- full analysis or nothing
- always-on or wake-word only
- camera as a feature, not a sense
- perception tied to active session
- raw events passed directly to output

This system:

- lightweight watchdog always running, full perception triggered
- ambient awareness independent of active session
- perception as a continuous background sense
- typed observations routed through the event bus
- the engine decides what to do with what perception sees

### Observation Feeds the Engine. The Engine Decides.

The perceptual layer is not an action system. It does not decide
whether Zola speaks, surfaces, or stays silent. It observes and
reports. Every observation becomes a typed event on the Environmental
Event Bus. The Attention/Relevance Engine reads those events alongside
everything else it knows and makes the interrupt decision.

This boundary must never be crossed. Perception must not trigger
output directly. A camera observation that Zola tries to act on
without routing through the engine is an architecture violation.
The engine is the sole interrupt authority. Perception is a sense,
not a voice.

---

## Long-Term Architectural Pillars

---

## 1. Two-Tier Perception Model

### Purpose

Define the two operational modes of the perceptual layer — their
responsibilities, their power contracts, their trigger relationships,
and their output destinations.

### Tier 1 — Watchdog

The Watchdog is always running. It consumes minimal power. It performs
no meaningful analysis. Its sole purpose is to detect that something
has changed in the user's environment that warrants Active Perception's
attention.

**Watchdog responsibilities:**

- Monitor front-facing camera at low resolution and low frame rate
  when phone is in upright orientation
- Run Voice Activity Detection (VAD) on microphone input — presence
  of speech only, no transcription, no identity matching
- Monitor phone orientation and motion via accelerometer
- Monitor app foreground/background state
- Detect significant audio events by amplitude threshold only

**Watchdog power contract:**

- Camera: active only when phone is upright; low resolution
  (e.g. 320×240); maximum 2–4 frames per second; no frame storage
- Microphone: VAD only; no audio capture; no buffering beyond the
  VAD window; no cloud transmission
- CPU: minimal; no ML inference at this tier beyond VAD
- Network: zero; Watchdog never makes network calls

**Watchdog outputs:**

The Watchdog does not emit events to the bus. It emits trigger signals
to Active Perception only. Trigger signals are internal. They carry
the trigger type and a timestamp. Nothing else.

**Watchdog trigger taxonomy:**

| Trigger | Condition | Notes |
|---------|-----------|-------|
| `FACE_PRESENCE` | Face detected in low-res frame | Not identified — presence only |
| `VOICE_ACTIVITY` | VAD detects speech | Speaker not identified at this tier |
| `PHONE_RAISED` | Orientation shift to upright | Combined with accelerometer |
| `SIGNIFICANT_AUDIO` | Amplitude threshold exceeded | Loud event, not speech |
| `APP_FOREGROUNDED` | Zola app enters foreground | Session-independent trigger |
| `AMBIENT_CHECKIN` | Scheduled low-frequency check | Maximum once per 5 minutes |

**Watchdog camera policy:**

The camera watchdog activates only when the phone is in an upright
orientation consistent with being held or propped facing the user.
When the phone is face-down, in a pocket (detected via proximity
sensor), or lying flat, the camera watchdog suspends. Audio VAD
continues regardless of orientation.

This policy is not a power optimization alone. It is a privacy
commitment. Zola does not attempt to see when the phone is not
positioned to be seen.

### Tier 2 — Active Perception

Active Perception runs when the Watchdog hands off a trigger, or
when a conversation session begins. It performs full vision and audio
analysis. It extracts typed observations. It generates structured
events for the Environmental Event Bus. It runs for as long as the
triggering context warrants, then steps back to Tier 1.

**Active Perception responsibilities:**

- Face detection and identity confirmation
- Emotional state and expression reading
- Environment classification (shop, office, home, vehicle, outdoor)
- Voice tone and stress analysis
- Speaker identification and voiceprint matching
- Scene understanding (activity happening, objects present)
- Object recognition when contextually relevant
- Multi-person detection (user present, others present)

**Active Perception power contract:**

- Camera: full resolution; normal frame rate; no frame storage;
  processing happens in-memory only; frames discarded after analysis
- Microphone: full audio capture during analysis windows; no raw
  audio storage; processed audio discarded after interpretation
- CPU: normal processing load; expected to be intermittent not
  continuous
- Network: on-device processing preferred; cloud vision (Gemini)
  permitted for complex scene understanding with user consent only

**Active Perception activation sources:**

Active Perception has two independent activation paths. Both are
valid. Both must be handled without duplication.

1. **Watchdog trigger** — Watchdog detected a change and handed off
2. **Session start** — A conversation session began

When both paths fire simultaneously, Active Perception runs once
under a shared instance. It is aware of both activation sources and
uses both to inform the duration and depth of its analysis.

**Active Perception lifetime:**

| Activation Source | Lifetime |
|-------------------|----------|
| Watchdog trigger | Until trigger context resolves + 30 second tail |
| Session start | Duration of the conversation session |
| Both simultaneously | Longer of the two; session takes precedence |

When Active Perception steps down, it emits a `PERCEPTION_IDLE` event
to the bus and returns control to the Watchdog.

---

## 2. Observation Schema

### Purpose

Define the typed observation format that Active Perception produces.
Every output of the perceptual layer must conform to this schema
before it reaches the Environmental Event Bus.

### Why a Typed Schema Matters

Raw perception output is not useful to downstream systems. "Face
detected" is not an event — it is a raw signal. "User confirmed
present, expression focused, alone, shop environment, confidence 0.91"
is an observation that the Attention/Relevance Engine can actually use.

The observation schema is the translation layer between what the
sensors produce and what the rest of the system understands.

### Observation Fields

**`observationType`**
The category of observation. Typed enum. See observation taxonomy
below.

**`subject`**
Who or what this observation is about. Values: `USER`, `ENVIRONMENT`,
`THIRD_PARTY`, `OBJECT`, `AUDIO_EVENT`.

**`confidence`**
Float 0.0–1.0. How confident the perception system is in this
observation. All downstream consumers must carry this value and
apply it to their decisions. Low confidence observations must not
produce high-weight actions.

**`observedAt`**
Timestamp of observation. Not processing time — the moment the
sensor captured the signal.

**`payload`**
Type-specific structured data. See per-observation-type definitions
below.

**`processingTier`**
Which tier produced this observation: `ON_DEVICE` or `CLOUD`. Cloud
observations carry additional latency and require consent to have
been granted.

**`sessionContext`**
Whether an active conversation session was running at time of
observation. Informs downstream interpretation.

**`activationSource`**
What triggered Active Perception: `WATCHDOG` or `SESSION`.

### Observation Taxonomy

**Identity Observations**

| Type | Description | Key Payload Fields |
|------|-------------|-------------------|
| `USER_CONFIRMED` | User identity verified | confidence, method (FACE / VOICE / BOTH) |
| `USER_ABSENT` | User not detected in frame | confidence, duration since last confirmation |
| `THIRD_PARTY_PRESENT` | Non-user person detected | confidence, count |
| `THIRD_PARTY_ABSENT` | Previously detected third party no longer present | — |
| `IDENTITY_UNCERTAIN` | Face present but not confirmed | confidence |

**State Observations**

| Type | Description | Key Payload Fields |
|------|-------------|-------------------|
| `EXPRESSION_READING` | Facial expression interpreted | expressionClass, confidence |
| `VOICE_TONE` | Vocal tone and stress reading | toneClass, stressLevel, confidence |
| `ATTENTION_DIRECTION` | Where user appears to be focused | focusTarget, confidence |
| `ACTIVITY_INFERRED` | Physical activity inferred | activityClass, confidence |

**Environment Observations**

| Type | Description | Key Payload Fields |
|------|-------------|-------------------|
| `ENVIRONMENT_CLASSIFIED` | Scene environment identified | environmentClass, confidence |
| `NOISE_LEVEL` | Ambient audio environment | noiseClass, decibelEstimate |
| `LIGHTING_CONDITION` | Lighting environment | lightingClass |
| `OBJECT_DETECTED` | Relevant object in frame | objectClass, confidence |

**Audio Events**

| Type | Description | Key Payload Fields |
|------|-------------|-------------------|
| `SIGNIFICANT_AUDIO_EVENT` | Non-speech loud event | eventClass, amplitude, duration |
| `MULTIPLE_VOICES` | More than one speaker detected | speakerCount, confidence |
| `SILENCE_EXTENDED` | Unusual silence after activity | durationMs |

### Expression Classes

`FOCUSED` `RELAXED` `STRESSED` `FRUSTRATED` `ENGAGED`
`FATIGUED` `NEUTRAL` `UNCERTAIN`

These are interpreted states, not raw emotion labels. The system
infers what the expression suggests about the user's current
cognitive and emotional state — not what emotion the user is
experiencing.

### Environment Classes

`SHOP` `OFFICE` `HOME` `VEHICLE` `OUTDOOR` `PUBLIC_SPACE`
`UNKNOWN`

### Activity Classes

`HANDS_BUSY` `STATIONARY` `IN_MOTION` `FOCUSED_TASK`
`RESTING` `UNKNOWN`

---

## 3. Identity Recognition System

### Purpose

Define how Zola learns to recognize the user and distinguishes
the user from others — through vision, voice, or both — without
requiring an explicit authentication step.

### Philosophy

Identity recognition in this system is not a gate. The user does
not authenticate to Zola. Zola recognizes the user as a natural
consequence of perception. The difference matters.

A gate creates friction. It positions Zola as a system the user
must prove themselves to. Recognition positions Zola as a presence
that knows who she is talking to. The same technical capability,
entirely different experience.

### Enrollment

During initial setup, Zola establishes a baseline identity profile
for the user. This enrollment is brief, explicit, and explained.

**Voice enrollment:**
The user speaks a set of natural phrases during setup. Zola
extracts a voiceprint. The voiceprint is stored on-device only.
It is never transmitted. It is used exclusively for identity
confirmation during Active Perception sessions.

**Face enrollment:**
With camera permission granted, Zola captures several frames of
the user's face during setup under varying conditions (angle,
lighting). A face embedding is derived and stored on-device only.
Raw frames are discarded immediately after embedding extraction.
The embedding is used exclusively for identity confirmation.

### Recognition During Active Perception

When Active Perception activates, identity confirmation is the
first step — not the last.

**Recognition priority order:**
1. Face embedding match (if camera available and upright)
2. Voiceprint match (if voice activity present)
3. Combined confidence (both signals raise confidence floor)
4. Fallback to `IDENTITY_UNCERTAIN` if neither confirms

Identity confirmation produces a `USER_CONFIRMED` or
`IDENTITY_UNCERTAIN` observation before any other analysis proceeds.

**Non-user voice handling:**
If voice activity is detected but voiceprint does not match the
enrolled user, Active Perception emits a `THIRD_PARTY_PRESENT`
observation and steps down from full analysis. Zola does not
attempt to identify the third party. She notes their presence and
reduces her proactive surface posture accordingly.

### Confidence Thresholds

| Threshold | Action |
|-----------|--------|
| ≥ 0.90 | Full user confirmed — all Active Perception capabilities enabled |
| 0.70–0.89 | Soft confirmation — Active Perception continues; foregrounding limited to Level 1 |
| < 0.70 | Identity uncertain — Active Perception steps down; no foregrounding |

These thresholds are configurable and should be validated against
real-world performance on target hardware.

### Identity Data Storage Policy

- Voiceprint embedding: stored on-device, encrypted at rest
- Face embedding: stored on-device, encrypted at rest
- Raw enrollment frames: discarded immediately after embedding
- Raw recognition frames: never stored; discarded after in-memory analysis
- Recognition results: stored as typed observations only (no biometric data)
- Cloud transmission: never; identity recognition is always on-device

---

## 4. Foregrounding System

### Purpose

Define how Zola surfaces herself when perception determines that
the user's attention is warranted — including when Zola is not
the active foreground application.

### Philosophy

Foregrounding is the most consequential output of the perceptual
layer. It is the moment Zola reaches into the user's experience
and requests their attention. Done poorly, this trains the user to
resent Zola's awareness. Done well, it feels like a thoughtful
presence noticing the right moment to speak.

The foregrounding system exists on a deliberate spectrum. Not every
perception observation warrants the same level of surface. The
weight of the surfacing must match the weight of what was observed.

**The foregrounding system does not make the interrupt decision.**
That decision belongs exclusively to the Attention/Relevance Engine.
The foregrounding system defines the *mechanisms* available to the
engine. The engine selects the appropriate mechanism based on its
own reasoning about urgency, user state, and dampening heat.

### Three Foregrounding Levels

**Level 1 — Ambient Surface**

Zola does not take the foreground. She appears as a subtle presence
indicator — a gentle overlay at the edge of the user's current
experience. She is signaling availability, not demanding attention.
The user may acknowledge or ignore. No action is required.

*Mechanism:* System overlay permission (draws over other apps);
minimal footprint; no interaction required; dismisses automatically
if not acknowledged.

*Appropriate when:*
- Watchdog detected user presence (low urgency)
- Active Perception confirmed user but no action is warranted
- Zola has something available but not time-sensitive
- Dampening heat is moderate

*Visual expression:*
Zola's presence indicator appears at low opacity at the edge
of the screen. It breathes. It does not animate aggressively.
It does not obscure content.

**Level 2 — Soft Foreground**

Zola requests attention through a dismissible notification or
heads-up surface. She has something worth the user's attention.
She acknowledges the user may be busy. She waits.

*Mechanism:* Heads-up notification (Android standard pattern);
includes a brief indication of what prompted the surface;
dismissible without penalty; tapping opens Zola.

*Appropriate when:*
- Active Perception identified a relevant situation (medium urgency)
- A perception-driven proactive observation has crossed relevance threshold
- Dampening heat is low to moderate
- User identity confirmed at ≥ 0.90

*Example trigger:*
Perception detects sustained frustrated expression and hands-busy
activity during a task context. Engine determines this warrants a
soft surface offer of assistance.

**Level 3 — Hard Foreground**

Zola takes the foreground deliberately. This is reserved for
situations where perception has identified something genuinely
urgent and the engine has determined the user's attention cannot
wait. Used sparingly. Overuse destroys trust in the system.

*Mechanism:* Full activity bring-to-front; Zola renders immediately;
audio cue accompanies if audio is not suppressed; designed to be
calm and clear, not alarming.

*Appropriate when:*
- Perception has detected a high-confidence urgent event
- Tier 1 override threshold has been crossed in the engine
- DND and call suppression rules have been evaluated and do not apply
- User identity is confirmed at ≥ 0.90

*Example trigger:*
Significant audio event detected — rapid loud impact followed by
extended silence, no voice response. Engine classifies as potential
safety event. Hard foreground triggered.

### Foregrounding Rules

These rules apply at all levels and may not be overridden by
any downstream system:

**R1 — Confidence gates level.**
Level 2 requires Active Perception confidence ≥ 0.80.
Level 3 requires Active Perception confidence ≥ 0.90 and user
identity confirmed. Low confidence observations may produce Level 1
only.

**R2 — The engine owns the decision.**
Perception observations do not directly produce foregrounding actions.
Every observation routes through the Environmental Event Bus to the
Attention/Relevance Engine. The engine selects the level. Perception
provides the input only.

**R3 — Existing suppression applies.**
Active call, DND mode, high dampening heat, and engine-defined
suppression rules apply to foregrounding decisions exactly as they
apply to proactive speech decisions. Perception does not bypass
existing engine gates.

**R4 — Identity required for Level 2 and above.**
Level 2 and Level 3 foregrounding require user identity confirmed
at threshold. Zola does not surface aggressively toward an
unconfirmed identity.

**R5 — User sensitivity setting is respected.**
The user's configured proactivity sensitivity maps to a foregrounding
ceiling. A user who has set low proactivity receives Level 1 maximum
from perception-driven events. This setting does not affect safety
events (Level 3 safety override is separate).

**R6 — Foregrounding history informs dampening.**
Every Level 2 and Level 3 foreground event is recorded in the
dampening system exactly as a proactive speech event is recorded.
It draws from the user's attention balance. The engine accounts for
recent foreground events when evaluating subsequent ones.

---

## 5. Privacy Architecture

### Purpose

Define the privacy contract the perceptual layer makes with the
user — what is observed, what is stored, what is transmitted,
and how the user remains in control.

### The Privacy Contract

**What Zola observes:**
Camera frames during upright phone orientation (Watchdog: low-res,
low-rate; Active: full, triggered). Audio presence via VAD
(Watchdog). Full audio during Active Perception sessions.

**What Zola stores:**
Typed observations (no raw sensor data). Voiceprint embedding
(on-device, encrypted). Face embedding (on-device, encrypted).
Observations that cross the memory salience threshold become
memory facts (entity-native, per the memory architecture).

**What Zola never stores:**
Raw camera frames. Raw audio recordings. Uninterpreted sensor
streams. Third-party biometric data of any kind.

**What Zola transmits:**
Nothing from the perceptual layer without explicit user consent.
On-device processing handles all Tier 1 and basic Tier 2 analysis.
Cloud vision (Gemini) for complex scene understanding requires
a separate explicit consent and is disabled by default.

### Perception Transparency

The user must always be able to know what Zola is perceiving.

**Visual indicator:**
Zola's presence UI reflects perception state. A subtle indicator
distinguishes Watchdog state from Active Perception state. The
user is never unaware that Active Perception is running.

**Perception log:**
A user-accessible log of recent perception events — not raw data,
but plain-language summaries. "Detected your presence at 2:14 PM.
Classified environment as shop." This is not surfaced by default
but is available in settings.

**User controls:**
Three settings govern perception behavior:

- **Perception tier ceiling:** Full (Watchdog + Active), Watchdog
  only, or Off. Off returns Zola to a purely reactive assistant.
- **Proactivity sensitivity:** How aggressively perception
  observations translate into foregrounding actions. Low / Medium
  / High.
- **Cloud vision consent:** Whether complex scene understanding
  may use Gemini Vision. Off by default.

These settings are plain-language, not technical. The user
understands what they are controlling.

### Third-Party Privacy

When perception detects a third party is present, Zola's behavior
changes:

- Proactive foregrounding reduces to Level 1 maximum
- Memory writing of conversation content is suspended
- Voice response volume awareness increases (Zola does not
  announce private information if others are present)
- Third-party face data is never captured, stored, or processed
  beyond detecting that a non-user person is in frame

---

## 6. Technology Stack

### Purpose

Define the recommended technology stack per perceptual capability,
distinguishing on-device from cloud paths and noting Android API
dependencies.

### Vision Stack

| Capability | Technology | Tier | Notes |
|------------|------------|------|-------|
| Face presence detection | ML Kit Face Detection | On-device | Low-latency; Watchdog safe at low res |
| Face identity matching | ML Kit Face Recognition / custom embedding | On-device | Enrollment embedding stored locally |
| Expression reading | ML Kit Face Mesh + custom classifier | On-device | Expression class inference only |
| Object detection | ML Kit Object Detection | On-device | Triggered only; not continuous |
| Scene classification | ML Kit Image Labeling | On-device | Environment class inference |
| Complex scene understanding | Gemini Vision API | Cloud | Consent required; disabled by default |
| Camera access | CameraX | On-device | Modern Android camera API; supports low-power modes |

### Audio Stack

| Capability | Technology | Tier | Notes |
|------------|------------|------|-------|
| Voice Activity Detection | Android AudioRecord + VAD library | On-device | Watchdog tier; no capture |
| Speech transcription | Deepgram (existing) | Cloud | Session-scoped; existing pipeline |
| Speaker identification | Deepgram diarization | Cloud | Session-scoped; separates voices |
| Voiceprint matching | On-device embedding comparison | On-device | Enrollment embedding stored locally |
| Tone and stress analysis | Audio feature extraction + classifier | On-device | Prosody analysis; no transcription required |
| Audio event classification | TensorFlow Lite audio classifier | On-device | Significant event detection |

### Identity Stack

| Capability | Technology | Tier | Notes |
|------------|------------|------|-------|
| Face enrollment | ML Kit + custom embedding | On-device | One-time setup; frames discarded after |
| Voice enrollment | On-device embedding | On-device | One-time setup; phrases discarded after |
| Combined identity confidence | Fusion layer | On-device | Weighted combination of face + voice scores |
| Embedding storage | Android Keystore + EncryptedSharedPreferences | On-device | Encrypted at rest |

---

## 7. Integration with Existing Architecture

### Environmental Event Bus

The perceptual layer is a first-class event producer on the
Environmental Event Bus. Every typed observation from Active
Perception becomes a structured bus event. The observation schema
maps directly to the bus event schema defined in the Environmental
Event Bus architecture.

Perception events carry a `sourceType` of `PERCEPTION` on the bus.
The engine treats them with the same routing logic as all other
event types. No special perception handling in the engine — the
bus schema is the interface contract.

### Current User State Model

Perception observations are the highest-quality input the User
State Model can receive. They replace soft inferences with direct
observations.

Specifically:

- `activityState` is informed by `ACTIVITY_INFERRED` observations
- `environmentClass` is informed by `ENVIRONMENT_CLASSIFIED` observations
- `cognitiveLoad` is informed by `EXPRESSION_READING` and `VOICE_TONE` observations
- `isAlone` is informed by `THIRD_PARTY_PRESENT` / `THIRD_PARTY_ABSENT` observations
- `userPresenceConfirmed` is a new field driven by `USER_CONFIRMED` observations

### Attention/Relevance Engine

The engine consumes perception-sourced bus events exactly as it
consumes all other events. The foregrounding system outputs
defined in this document represent mechanisms the engine selects
from — not behaviors the perception layer triggers directly.

The engine's existing dampening, suppression, and override tier
logic applies to perception-driven decisions without modification.
Perception is a better-informed input source, not a privileged one.

### Memory System

The perceptual layer does not write directly to long-term memory.
Observations flow through a three-layer perception memory pipeline
before any fact may be promoted to the world graph. This pipeline
exists to prevent ephemeral observations from polluting durable truth.

The three layers are defined in full in the Perception Memory
Architecture document. The perceptual layer's responsibility ends
at the second layer — episodic memory. Promotion from episodic to
world graph is owned entirely by the memory system.

**Layer 1 — Ephemeral State Memory (perception-owned)**

Active Perception writes observations into a short-lived in-memory
buffer. This buffer is the perception layer's working memory. It
holds the current moment only.

- Held in-memory; never written to Firestore
- Decays on a per-observation-type schedule (seconds to minutes)
- Feeds the Environmental Event Bus and User State Model in real time
- Does not survive session boundaries
- Examples: "Brian appears stressed right now", "shop is noisy",
  "unknown vehicle in frame"

**Layer 2 — Environmental Episodic Memory (perception-owned)**

When an observation recurs with sufficient consistency, it is
promoted from the ephemeral buffer to the episodic store. This layer
exists in Firestore under the existing episodic memory path
(`users/{userId}/episodic/`) using `EpisodicMemoryEntry` with
`source: PERCEPTION` tagging.

Promotion from Layer 1 to Layer 2 requires:
- Recurrence: observation of the same type and subject seen N times
- Time window: recurrences distributed across separate sessions,
  not clustered in a single session
- Confidence floor: each recurrence must meet minimum confidence
- Consistency: observation is stable across varying conditions,
  not only present in one context

Examples of valid Layer 2 entries:
- "Shop environment observed on weekday mornings across 8 sessions"
- "Elevated voice stress observed in deadline-adjacent conversations"
- "Unknown vehicle (silver, recurring) observed 5 times this week"

The episodic entry carries: observation type, subject, recurrence
count, session distribution, confidence statistics, first and last
observed timestamps, and a `promotionEligible` flag.

**Layer 3 — World Graph Promotion (memory system-owned)**

The perceptual layer does not perform world graph promotion. It sets
`promotionEligible: true` on episodic entries that have crossed the
recurrence and stability thresholds. The memory system reads this
flag and applies its own promotion rules — including user confirmation
for entity candidates, authority hierarchy enforcement, and world
graph integrity checks.

The handoff is the `promotionEligible` flag. What happens after is
not this layer's concern. See the Perception Memory Architecture
document for the full promotion model.

### Presence UI

The Presence UI reflects perception state visibly. The perception
tier indicator is part of the UI layer — not a separate system.

When Watchdog is running: baseline presence state.
When Active Perception is running: a subtle but visible indicator
distinguishes active perception from idle. This is the transparency
commitment made visible.

Foregrounding Level 1 uses the overlay presence layer already
defined in the Presence UI architecture. Level 2 uses Android
notification. Level 3 uses full activity foreground. The Presence
UI renders in all three cases.

---

## 8. Phase Sequencing

### Purpose

Map the perceptual layer's capabilities to the project's phase
structure. Perception is a multi-phase build. This document defines
the full architecture. Implementation follows the phase plan.

### Phase 2 — Architecture and Lore (Current)

- This document committed to architecture lore
- Technology stack decisions recorded
- Open questions identified and logged
- No implementation

### Phase 3 — Watchdog and Basic Active Perception

**Goal:** Zola has functional ambient awareness. She knows when
the user is present, what environment she is in, and whether a
third party is nearby. Basic foregrounding is live.

Deliverables:
- Watchdog implemented with full trigger taxonomy
- VAD-based audio trigger operational
- Camera watchdog operational (upright-only policy enforced)
- Basic face presence detection (not identity — presence only)
- Basic environment classification
- `USER_CONFIRMED` / `THIRD_PARTY_PRESENT` / `ENVIRONMENT_CLASSIFIED`
  observations emitted to bus
- Level 1 and Level 2 foregrounding operational
- Perception transparency indicator in Presence UI
- User perception settings (tier ceiling, proactivity sensitivity)
- All perception behind `ENABLE_PERCEPTION` feature flag

### Phase 4 — Identity Recognition and Emotional State

**Goal:** Zola knows who she is talking to and reads their state.
Enrollment is live. Identity confirmation is reliable. Emotional
and tonal reading informs engine decisions.

Deliverables:
- Voice and face enrollment flow
- Voiceprint matching operational
- Face identity matching operational
- Combined confidence scoring
- `EXPRESSION_READING` and `VOICE_TONE` observations operational
- Identity confirmation gates foregrounding levels as defined
- Level 3 foregrounding operational with safety event detection
- Cloud vision consent setting and Gemini Vision integration
- Perception log accessible in settings

### Phase 5 — Advanced Scene Understanding and Proactive Perception

**Goal:** Zola acts on what she perceives without being asked.
Scene understanding is deep. Perception-driven proactive behavior
is calibrated and trusted.

Deliverables:
- Object recognition in-context
- Activity inference from combined signals
- Multi-person awareness with conversation privacy mode
- Proactive perception-driven assistance patterns
- Calibration of perception confidence thresholds from real-world
  data
- User sensitivity tuning from observed foreground response patterns

---

## Open Questions

The following questions require decisions before Phase 3
implementation begins. They are logged here and in
`OPEN_QUESTIONS.md`.

**Q1 resolution:** Resolved — Phase 18. Silero VAD via TFLite
selected. See P18-D01 in DESIGN_DECISIONS.md.

**Q1 — VAD library selection**
Which VAD library is the correct choice for Watchdog-tier audio
presence detection on Android? Requirements: low power, no audio
capture, accurate in noisy environments (shop context). Decision
required before Phase 3 audio watchdog implementation.

**Q2 resolution:** Resolved — Phase 18. Watchdog remains
identity-blind. Two-stage gate with SpeechBrain ECAPA-TDNN
Gatekeeper handles identity confirmation. See P18-D02 and P18-D05
in DESIGN_DECISIONS.md.

**Q2 — Face presence vs identity at Watchdog tier**
The Watchdog is specified for face presence only — not identity.
Should the Watchdog carry a very lightweight embedding comparison
to soft-confirm identity before triggering Active Perception?
Trade-off: slightly higher power vs. reducing false Active
Perception triggers from non-user faces. Decision required before
Phase 3 camera watchdog implementation.

**Q3 resolution:** Resolved — Phase 18. App kill stops Watchdog.
User relaunch required to rearm. Self-resurrection not implemented
by design. See P18-D06 in DESIGN_DECISIONS.md.

**Q3 — Perception state persistence across app restarts**
When the app is killed and restarted, should the Watchdog resume
immediately or wait for an explicit user action? A backgrounded
app with a persistent Watchdog requires a foreground service.
This has notification and user perception implications. Decision
required before Phase 3 implementation begins.

**Q4 — Recurrence thresholds for Layer 1 to Layer 2 promotion**
What recurrence count and session distribution qualifies an
ephemeral observation for promotion to episodic memory? The
threshold must be high enough to filter one-off observations
but low enough to capture genuine patterns within a reasonable
timeframe. Separate thresholds likely needed per observation
type — environmental patterns (shop context) may promote faster
than behavioral patterns (stress correlation). Decision required
before Phase 4 memory integration.

**Q6 — Entity candidate surface timing**
When an episodic entry is flagged `promotionEligible` and
represents an unknown entity (e.g. recurring unknown vehicle),
how soon should Zola surface a confirmation question to the
user? Too soon and Zola asks about things that aren't worth
naming. Too late and the entity has been observed many times
without being grounded. Decision required before Phase 4
entity candidate implementation.

**Q5 — Level 3 safety event taxonomy**
What specific audio and visual patterns constitute a Level 3
safety event? The architecture specifies high-confidence urgent
events, but the taxonomy of what qualifies must be explicitly
defined before Level 3 foregrounding is implemented. This
decision has direct product and ethical implications.

---

## Principles That Must Not Be Violated

The following principles are architectural invariants. They apply
to every implementation wave in this layer. They may not be
overridden by product decisions, performance optimizations, or
implementation convenience.

**P1 — Raw sensor data is never stored.**
Frames and audio are processed in memory and discarded. No
exceptions. No temporary storage. No "just for debugging" paths.

**P2 — Identity data never leaves the device.**
Voiceprint and face embeddings are on-device only. The recognition
pipeline is on-device only. Cloud transmission of biometric data
is never permitted regardless of consent state.

**P3 — Perception never triggers output directly.**
All observations route through the Environmental Event Bus to
the Attention/Relevance Engine. The engine is the sole interrupt
and foreground authority.

**P4 — Third-party biometric data is never captured.**
When a non-user person is detected, Zola notes presence and
nothing more. No face capture. No voice capture. No identity
attempt.

**P5 — Confidence gates action level.**
Low confidence observations produce low-weight actions. The
system fails down — uncertain perception reduces Zola's
proactivity, it never increases it.

**P6 — The user is always in control.**
Perception can be reduced or disabled entirely. Zola degrades
gracefully. A user who disables perception has a fully functional
assistant — one that simply does not observe.

---

*Perceptual Input Layer Architecture — Version 1.1*
*Created at Phase 2 lore entry*
*Updated: three-layer perception memory pipeline added (section 7,*
*memory integration). Full promotion model in*
*`Zola_Architecture_Perception_Memory.md`.*
*Implementation begins Phase 3*
*Next step: commit to `zola-architecture/` and log open questions
in `OPEN_QUESTIONS.md`*
