# Environmental Event Bus + Current User State Model

### Foundational Architecture for Contextual Intelligence and Ambient Awareness

---

## Vision

The Attention/Relevance Engine is only as intelligent as the information it receives.

A relevance score computed against a raw sensor event is not intelligence — it is threshold matching. A dampening decision made without knowledge of what the user is currently doing is not restraint — it is guessing.

This document defines the two systems that give the Attention/Relevance Engine something real to work with.

The **Environmental Event Bus** is the transport and schema layer. It ensures that every signal — from every source, across every domain — arrives at the engine in a structured, interpretable, consistent form. Workers emit. The bus carries. The engine decides. No worker speaks directly. No signal arrives raw.

The **Current User State Model** is the contextual lens the engine reads before every decision. It is a continuously maintained snapshot of what the user is most likely experiencing right now — their activity, their environment, their cognitive load, their emotional register, their conversational openness. It does not tell the engine what to do. It tells the engine who it is about to interrupt.

Together, these two systems should eventually feel less like:

> "a stream of sensor alerts and a list of user attributes"

and more like:

> "a coherent, living picture of the user's world that makes every attention decision genuinely informed."

---

## Core Philosophy

### The Signal Is Not the Event. The Event Is Not the Insight.

Three distinct transformations must happen before any signal reaches the Attention/Relevance Engine.

**Perception** produces a raw signal: motion detected, message received, location changed.

**Interpretation** produces a structured event: unfamiliar person lingering near the shop after midnight; high-priority message from a close contact requiring a time-sensitive response.

**State modeling** produces a contextual snapshot: user is doing hands-busy work in the shop; noise level is elevated; two proactive updates were delivered in the last fifteen minutes; no user-initiated conversation has occurred in the last forty minutes.

Only when all three layers exist does the engine have enough information to make a decision that is genuinely intelligent rather than statistically lucky.

Traditional systems collapse these three steps. A camera detects motion and a notification fires. An email arrives and a badge appears. This is not contextual intelligence — it is mechanical reflex.

This architecture separates them deliberately and permanently.

Traditional systems:

- raw signal → immediate output
- no interpretation layer
- no user state awareness
- static threshold matching
- alert-first design

This system:

- raw signal → interpretation → structured event → state-informed decision → appropriate output
- interpretation before any routing decision
- continuous user state modeling
- dynamic threshold informed by context
- restraint-first design

---

## Long-Term Architectural Pillars

---

## 1. Structured Event Schema

### Purpose

Define a single event format that every signal source — environmental workers, human context workers, cognitive workers, and communication monitors — must conform to before emitting onto the bus.

This schema is the contract between every event producer and the Attention/Relevance Engine.

### Why a Unified Schema Matters

Without a schema, each new signal source requires custom handling downstream. The engine must learn the shape of each source's output. Interpretation logic becomes per-source rather than universal. Adding a new sensor requires touching the engine.

With a schema, the engine is source-agnostic. A weather anomaly event and a security camera event are structurally identical from the engine's perspective. Interpretation happens upstream. Routing, dampening, and delivery happen downstream. The engine evaluates the event, not the source.

### Core Event Fields

Every event emitted onto the bus must include the following fields.

---

**`eventId`**
A unique identifier for this event instance. Used for deduplication, deferred queue tracking, and audit logging.

**`sourceWorker`**
The identifier of the worker or monitor that emitted this event. Examples: `weather_monitor`, `sms_receiver`, `calendar_worker`, `security_camera_worker`, `gmail_monitor`. Used for rate limiting per source and for routing rules that apply source-specific handling.

**`eventCategory`**
A high-level category classification.

- `security` — physical security, property, access
- `communication` — messages, calls, email
- `environmental` — weather, traffic, location conditions
- `calendar` — scheduling, time-based events
- `health` — user health and activity signals
- `system` — device state, connectivity, DND
- `household` — deliveries, visitors, home activity
- `memory` — memory conflicts, stale items, resurfacing candidates
- `autonomous` — suggestions from the Autonomous Behavioral Engine

**`eventType`**
A specific type within the category. Examples within `security`: `unknown_person_detected`, `familiar_person_detected`, `vehicle_detected`, `package_delivered`. Examples within `communication`: `high_priority_message_received`, `email_from_known_contact`, `missed_call`.

**`timestamp`**
When the event was generated by the source worker. Not when it was emitted onto the bus — the origination time.

**`expiresAt`**
When this event stops being actionable. After this time, the deferred queue should drop it rather than surface it. Some events expire in minutes. Others remain relevant for hours. A few have no meaningful expiry.

Examples:
- traffic warning affecting a departure: expires at departure time
- package delivered: expires at end of day or user acknowledgment
- unknown person near property: expires after confirmed safe resolution
- calendar reminder for a passed meeting: expires at meeting end time

**`rawContent`**
A structured representation of the original signal — the interpreted meaning from the Contextual Interpretation Layer, not the raw sensor output. This is the human-readable and machine-processable description of what happened.

Examples:
- `{ person: "unknown", location: "shop_zone", time: "02:14", behavior: "lingering" }`
- `{ sender: "contact:spouse", channel: "sms", preview: "heading home soon", priority: "high" }`
- `{ condition: "severe_thunderstorm_warning", area: "current_location", onset: "45_minutes" }`

**`suggestedSummary`**
A pre-drafted natural language summary of this event, suitable for use in a spoken or displayed delivery if the engine decides to surface it. The engine may use this directly, combine it with other events in a summary, or discard it in favor of model-generated phrasing. This is not the speech output — it is a structured input hint.

Examples:
- `"UPS dropped off a package at the front door."`
- `"There's a severe thunderstorm warning starting in about 45 minutes."`
- `"Someone unfamiliar is near the shop. It's after 2 AM."`

**`baseRelevanceScore`**
A pre-computed relevance estimate from the emitting worker, reflecting how much this event is likely to matter to the user in isolation — before context, heat, or cost modifiers. This is a float from 0.0 to 1.0. The Attention/Relevance Engine may use this as a starting point, override it, or weight it against its own evaluation.

**`urgencyTier`**
The worker's assessment of urgency classification before the engine applies state-aware judgment.

- `TIER_1_OVERRIDE_ELIGIBLE` — potential safety or security event
- `TIER_2_STANDARD_INTERRUPT` — relevant and time-sensitive
- `TIER_3_LOW_PRIORITY` — worth surfacing eventually
- `TIER_4_PASSIVE_LOG` — no realistic interrupt case

The engine may promote or demote this classification based on user state context.

**`confidenceScore`**
How confident the emitting worker or Contextual Interpretation Layer is in the interpretation. A float from 0.0 to 1.0. Low confidence events should generally not promote above tier 3 regardless of apparent urgency. A motion detection at 60% confidence that something is a person is very different from a motion detection at 97% confidence.

**`privacySensitivity`**
Classification of whether this event contains content that must be handled with privacy constraints.

- `PUBLIC` — no restriction; can be spoken aloud in any context
- `HOUSEHOLD_AWARE` — safe at home, but should not be spoken in shared or public environments
- `PRIVATE` — should never be spoken aloud where others may hear; notification-only in shared contexts
- `SENSITIVE` — requires explicit user permission before surfacing in any channel

**`requiresUserDecision`**
Boolean. Whether this event warrants presenting the user with options rather than simply informing them. A package delivery does not require a decision. An unknown person near the shop at night may warrant offering: "Want me to pull up the camera feed?" True for tier 1 events that involve security escalation pathways.

**`relatedEntities`**
Optional list of entity IDs from the memory graph that are relevant to this event. Used to enrich interpretation, apply relationship-aware priority weighting, and support memory linkage after the event is resolved.

Examples:
- a message from a contact → entity ID for that contact
- a visitor at the door → entity ID if recognized
- a calendar event → entity ID for that event

**`deduplicationKey`**
A key used to prevent the same event from being emitted multiple times within a suppression window. The bus should reject a second event with the same deduplication key within a configurable time window. Format: `{sourceWorker}:{eventType}:{primaryEntityOrLocation}`.

Examples:
- `sms_receiver:high_priority_message_received:contact:spouse`
- `camera_worker:unknown_person_detected:zone:shop`

---

### Optional Fields

These fields are included when available and meaningful, but are not required for all events.

**`locationContext`**
The user's known location at the time of the event. Used for geographic relevance filtering — a traffic warning for a road the user is not near is less relevant.

**`userStateSnapshot`**
A lightweight copy of the relevant Current User State Model fields at the time of event generation. Allows the engine to evaluate the event against the state at the moment it occurred, not the state at the moment it is evaluated (which may be different if the event was queued).

**`suggestedDeliveryChannel`**
The worker's recommendation for how this event should be delivered if the engine decides to surface it. The engine is not obligated to follow this. It is a hint.

- `spoken_brief` — one or two sentences spoken aloud
- `spoken_full` — full spoken update with context
- `passive_notification` — visual notification, no speech
- `silent_log` — no user-facing output; record only
- `security_escalation` — structured decision workflow

**`groupingTag`**
Optional tag used by the deferred summary coordinator to group related events into a single summary. Events sharing a grouping tag and a summary window can be batched into a single delivery rather than surfaced individually.

Examples: `package_activity`, `property_visitors`, `morning_briefing`, `communication_catch_up`

---

### Schema Integrity Rules

The bus must enforce these rules on every inbound event before it is forwarded.

1. Events missing required fields are rejected with a structured error logged to the worker that emitted them.
2. Events with a `confidenceScore` below the minimum threshold (configurable, suggested default 0.4) are automatically downgraded to `TIER_4_PASSIVE_LOG` regardless of the emitting worker's tier classification.
3. Events with an `expiresAt` timestamp already in the past are dropped on arrival.
4. Events matching an active deduplication key within the suppression window are dropped silently.
5. Events with `privacySensitivity: SENSITIVE` that do not have a matching user permission record are automatically downgraded to `silent_log` and flagged for permission review.

---

## 2. Environmental Event Bus

### Purpose

Provide the transport, routing, and lifecycle management layer for all structured events emitted by workers and monitors. The bus is the single path from every event source to the Attention/Relevance Engine. Nothing bypasses it.

### Responsibilities

- accept structured events from all workers and monitors
- enforce schema validation before forwarding
- apply deduplication rules
- manage event lifecycle (expiry, drop, log)
- forward valid events to the Contextual Interpretation Layer for events that require enrichment
- forward fully interpreted events to the Attention/Relevance Engine
- maintain an audit log of all received events and their disposition
- support backpressure when the engine is processing at capacity

### Bus Architecture

The bus operates as a single logical channel with internal routing.

**Inbound lane:** accepts events from all workers. Schema validation happens here.

**Interpretation lane:** events that arrive as pre-interpreted (from workers that include their own interpretation, such as the Contextual Interpretation Layer itself) pass directly to the outbound lane. Events that arrive as raw signals from lower-level workers pass through an interpretation step before forwarding.

**Outbound lane:** delivers fully interpreted, schema-valid events to the Attention/Relevance Engine. This is the only path to the engine.

**Audit lane:** all events — accepted, rejected, dropped, expired — are logged to a structured audit log. This log supports debugging, pattern analysis, and dampening calibration.

```
Workers / Monitors
        │
        ▼
  [ Inbound Lane ]
  Schema validation
  Deduplication check
  Expiry check
        │
        ├──► rejected / dropped ──► Audit Log
        │
        ▼
  [ Interpretation Lane ]
  Pre-interpreted events: pass through
  Raw signal events: Contextual Interpretation Layer enrichment
        │
        ▼
  [ Outbound Lane ]
  Fully interpreted, validated event
        │
        ├──► Attention/Relevance Engine
        └──► Audit Log
```

### What May Emit to the Bus

Every event source that wants to produce user-facing output of any kind — spoken, notified, displayed, or logged — must do so by emitting a structured event onto the bus.

**May emit:**
- Environmental workers (camera, sensor, weather, traffic)
- Human context workers (calendar, health, messaging)
- Cognitive and memory workers (memory conflicts, resurfacing candidates)
- Communication monitors (SMS receiver, Gmail monitor, morning briefing emitter)
- Autonomous Behavioral Engine (proposed proactive content)
- Reminder system (when a reminder is due)
- Sports alert worker (when a game event is relevant)

**May not emit, may not bypass:**
- No worker may call `sendAssistantInitiatedTurn` directly.
- No worker may call `NotificationManager.notify` directly for user-facing notifications.
- No worker may write to any UI state that the user sees without passing through the bus and the engine.

The existing `ProactiveEventBus` (SharedFlow) should be evaluated for replacement or absorption into this bus. If it is retained, it must be wired as a feeder into the inbound lane of the Environmental Event Bus rather than operating as a parallel channel.

### Event Lifecycle

An event enters the bus and follows exactly one of these paths:

1. **Rejected at inbound** — schema invalid or confidence below floor. Logged. Worker notified.
2. **Dropped — duplicate** — matches active deduplication key. Logged silently.
3. **Dropped — expired** — `expiresAt` already past. Logged silently.
4. **Forwarded to engine — immediate** — fully interpreted, valid, non-expired. Delivered to engine for evaluation.
5. **Forwarded to interpretation — enrichment needed** — valid schema but raw signal content; routed through Contextual Interpretation Layer before forwarding to engine.

After the engine evaluates an event, the outcome is written back to the audit log:
- spoken, notified, displayed, silent log, deferred, or dropped by engine.

---

## 3. Contextual Interpretation Layer

### Purpose

Convert raw environmental signals into meaningful situational events before they reach the Attention/Relevance Engine. This layer answers the question: what does this signal actually mean in context?

The engine should never receive a raw motion detection or a raw message arrival. It should receive an interpreted understanding: an unfamiliar person is near a high-value area at an unusual hour, or a high-priority contact sent a message that appears to require a response.

### Responsibilities

- accept raw signal events from workers that emit low-level observations
- correlate signals with user context: location, time-of-day, calendar, known routines, known entities
- distinguish normal from anomalous activity
- compare detected activity against expected patterns
- identify known vs unknown persons, vehicles, or entities
- evaluate time-of-day significance
- assess false positive likelihood
- produce a fully enriched, interpreted event with a confidence score
- emit the interpreted event back to the bus outbound lane

### Interpretation Inputs

For each raw event, the Contextual Interpretation Layer reads:

- **Current time and day** — is this activity expected at this hour?
- **Known place context** — which zone or location is this event associated with?
- **Calendar state** — is the user expecting someone? Is there a delivery scheduled? Are they away?
- **Known entity graph** — is this person, vehicle, or entity recognized from memory?
- **Recent event history** — has this same signal occurred recently? Is this a pattern or an anomaly?
- **Environmental baseline** — what is the normal activity level in this zone at this time?
- **User routine model** — does this match a known routine, or is it a departure from one?

### Interpretation Output Examples

Raw signal from camera worker:
```
eventType: motion_detected
zone: driveway
confidence: 0.91
timestamp: 14:23
```

Interpreted event:
```
eventType: familiar_person_approaching
interpretation: "Neighbor approaching during typical afternoon visit window"
anomalyScore: 0.08
confidenceScore: 0.87
urgencyTier: TIER_3_LOW_PRIORITY
suggestedSummary: "Looks like your neighbor is coming up the driveway."
```

Raw signal from camera worker:
```
eventType: motion_detected
zone: shop
confidence: 0.94
timestamp: 02:17
```

Interpreted event:
```
eventType: unknown_person_detected
interpretation: "Unrecognized person near high-value area at unusual hour"
anomalyScore: 0.94
confidenceScore: 0.91
urgencyTier: TIER_1_OVERRIDE_ELIGIBLE
requiresUserDecision: true
suggestedSummary: "Someone unfamiliar is near the shop. It's after 2 AM."
```

### Confidence and False Positive Reduction

Not every motion is a person. Not every vehicle is unfamiliar. Not every message requires a response.

The interpretation layer must apply active false positive reduction:

- animals, shadows, weather, and headlights should be distinguished from human presence where possible
- routine activity (own vehicle in driveway, regular visitor pattern) should be classified as expected rather than flagged
- repeated identical signals within a short window should not produce repeated events — deduplication handles this upstream, but interpretation should also recognize sustained vs transient events
- low-confidence interpretations should produce low-confidence events that the engine will route conservatively

### Interpretation Authority

The Contextual Interpretation Layer owns the meaning of an event.

The Attention/Relevance Engine owns the decision of what to do about it.

These must not be conflated. The interpretation layer should not encode delivery decisions. The engine should not re-interpret raw signals that interpretation has already processed.

---

## 4. Current User State Model

### Purpose

Maintain a continuously updated, multi-signal snapshot of the user's likely current state — what they are doing, where they are, how cognitively loaded they are, and how open they are to interruption right now.

This model is the primary contextual input to the Attention/Relevance Engine's dampening and cost calculations. It is also a shared resource for the conversational state layer, the identity and personality system, and any system that needs to adapt its behavior to the user's current reality.

### Design Principle

The model does not observe the user directly.

It aggregates signals from available sources and maintains a probabilistic estimate of the user's current state.

Every field in the model is an inference, not a certainty. Fields carry a confidence level and a staleness indicator. The engine treats low-confidence or stale fields conservatively.

### State Model Fields

---

#### Activity State

**`primaryActivity`**
The most likely current activity.

- `HANDS_BUSY_WORK` — active shop or physical work context
- `DESK_WORK` — seated, screen-focused, lower physical demand
- `IN_TRANSIT_DRIVING` — active vehicle operation
- `IN_TRANSIT_PASSENGER` — vehicle, not driving
- `WALKING_LIGHT_ACTIVITY` — mobile but low cognitive load
- `IDLE_AVAILABLE` — no detected active task
- `SLEEPING` — inferred from time, health signals, or DND
- `IN_MEETING` — calendar-confirmed or inferred from audio patterns
- `IN_CALL` — active phone call detected
- `ACTIVE_CONVERSATION_WITH_ZOLA` — current conversation in progress
- `UNKNOWN` — insufficient signal to classify

**`activityConfidence`**
Float 0.0–1.0. How confident the model is in the current `primaryActivity` classification.

**`activitySource`**
Which signals contributed to this classification. A list from: `location`, `calendar`, `bluetooth_audio`, `motion`, `call_state`, `dnd_state`, `time_of_day`, `health`, `audio_environment`.

---

#### Location and Workspace Context

**`workspaceContext`**
The semantic workspace the user is most likely in.

- `SHOP` — identified by known-place GPS anchor, Bluetooth device identity, or explicit check-in
- `HOME` — home anchor
- `OFFICE` — office anchor
- `VEHICLE` — driving or parked vehicle
- `IN_TRANSIT` — moving between known places
- `UNKNOWN_LOCATION` — no anchor match
- `PUBLIC_SPACE` — inferred from location not matching any known anchor

**`workspaceConfidence`**
Float 0.0–1.0.

**`knownPlaceId`**
If the user is at a known place, the identifier of that place in the known-place model. Null if not at a known anchor.

---

#### Cognitive Load Estimate

**`cognitiveLoad`**
An estimate of the user's current cognitive demand.

- `LOW` — idle, walking, passenger, simple task
- `MODERATE` — desk work, light task, light conversation
- `HIGH` — focused work, complex task, active meeting, driving
- `CRITICAL` — emergency context, high-stress signal, active safety situation

**`cognitiveLoadConfidence`**
Float 0.0–1.0.

**`cognitiveLoadSource`**
Which signals contributed: `activity_state`, `calendar`, `audio_environment`, `emotional_state`, `conversational_state`.

---

#### Interruption Tolerance

**`interruptionTolerance`**
The model's estimate of how open the user is to being interrupted right now.

- `OPEN` — idle, conversationally active with Zola, user has signaled availability
- `REDUCED` — moderate task, some cognitive load, recent interruptions
- `LOW` — high cognitive load, noisy environment, recent dismissals
- `MINIMAL` — hands-busy work, active call, active human conversation nearby
- `EMERGENCY_ONLY` — driving in complex conditions, explicit DND, critical focus

This field is the most direct input to the Attention/Relevance Engine's dampening modifier selection. It is derived from the combination of `primaryActivity`, `cognitiveLoad`, `currentHeat` (from the dampening system), and recent user interaction signals.

**`interruptionToleranceConfidence`**
Float 0.0–1.0.

---

#### Environmental Signals

**`noiseLevel`**
Estimated ambient noise level.

- `QUIET`
- `AMBIENT` — background noise, music, moderate activity
- `ELEVATED` — tools, machinery, loud environment
- `UNKNOWN`

**`noiseLevelSource`**
`audio_environment_monitor`, `bluetooth_device_type`, `workspace_context_inference`.

**`othersPresent`**
Boolean estimate of whether other people are likely present in the user's immediate environment. Derived from: audio detection of multiple speakers, calendar (meeting context), known-place context (public space), social context signals.

**`othersPresentConfidence`**
Float 0.0–1.0.

**`deviceState`**
Relevant device state signals as a structured object.

- `dndEnabled`: boolean
- `callActive`: boolean
- `screenOn`: boolean
- `bluetoothAudioConnected`: boolean
- `bluetoothDeviceType`: `car_stereo` | `shop_speaker` | `headphones` | `home_speaker` | `unknown`

---

#### Conversational State

**`conversationalReadiness`**
How open the user is to a conversational exchange right now, independent of interruption tolerance.

- `ACTIVELY_CONVERSING` — mid-conversation with Zola
- `RECENTLY_CONVERSED` — last exchange within the past few minutes
- `AVAILABLE` — no recent conversation, low activity
- `DISTRACTED` — signals suggest attention is elsewhere
- `UNAVAILABLE` — call active, human conversation nearby, or sleeping

**`lastUserInitiatedTurnMs`**
Milliseconds since the user last spoke to Zola. Used by the dampening system to calculate how long the user has been conversationally passive.

**`lastZolaSpeechMs`**
Milliseconds since Zola last produced spoken output of any kind, including proactive turns.

---

#### Emotional State

**`emotionalRegister`**
The model's current best estimate of the user's emotional state.

- `NEUTRAL`
- `POSITIVE` — engaged, upbeat signals from conversational tone
- `STRESSED` — urgency signals, clipped responses, elevated activity
- `TIRED` — time-of-day inference combined with health or motion signals
- `FOCUSED` — deep work signals
- `UNKNOWN`

**`emotionalRegisterSource`**
`conversational_tone`, `time_of_day`, `health_signal`, `explicit_signal`, `unknown`.

**`emotionalRegisterConfidence`**
Float 0.0–1.0.

---

#### Calendar Context

**`calendarState`**
The user's current calendar situation.

- `inEventNow`: boolean — is a calendar event active right now?
- `currentEventType`: `meeting` | `personal` | `blocked` | `travel` | `unknown`
- `currentEventTitle`: string — optionally available if permission allows
- `upcomingEventInMinutes`: integer — minutes until next event, null if none within horizon
- `dayDensity`: `light` | `moderate` | `heavy` — how packed is today's calendar

---

#### Model Metadata

**`modelVersion`**
Which version of the state model produced this snapshot.

**`lastUpdatedMs`**
When the model was last refreshed. Consumers should treat fields as stale if `lastUpdatedMs` is more than a configurable threshold old (suggested: 60 seconds for activity state, 5 minutes for calendar context, 30 seconds for device state).

**`overallConfidence`**
A rolled-up confidence score across all fields. Low overall confidence should shift the engine toward conservative (lower interruption) behavior.

---

## 5. State Model Update Architecture

### Purpose

Define how and when the Current User State Model is updated, and how updates propagate to consumers.

### Update Philosophy

The model should update continuously from available signals, not on-demand per event.

Staleness is a first-class concern. A state model that is 10 minutes old is not a current user state model — it is a historical snapshot. Consumers must know how fresh each field is.

### Signal Sources and Update Frequency

| Signal Source | Fields Updated | Target Refresh Rate |
|--------------|---------------|---------------------|
| Device call state (`TelephonyCallback`) | `callActive`, `primaryActivity`, `interruptionTolerance` | On change |
| DND state (`NotificationManager`) | `dndEnabled`, `interruptionTolerance` | On change |
| Bluetooth audio routing | `bluetoothConnected`, `bluetoothDeviceType`, `workspaceContext` | On change |
| Fused location | `workspaceContext`, `knownPlaceId`, `primaryActivity` | Every 2–5 minutes or on significant movement |
| Calendar reader | `calendarState`, `cognitiveLoad` | Every 5 minutes or on calendar change event |
| Audio environment monitor | `noiseLevel`, `othersPresent` | Every 30 seconds while active |
| Conversational state layer | `conversationalReadiness`, `lastUserInitiatedTurnMs`, `lastZolaSpeechMs` | On every turn event |
| Health Connect | `primaryActivity`, `emotionalRegister` | Every 5–15 minutes |
| Time of day | `primaryActivity` inference, `emotionalRegister` inference | Continuous, low cost |
| Dampening system | `interruptionTolerance` (via `currentHeat`) | On every heat change event |

### Update Propagation

The state model maintains an internal update timestamp per field group.

Consumers — primarily the Attention/Relevance Engine — read the model synchronously when evaluating an event. The model does not push updates to the engine; the engine pulls the current snapshot at evaluation time.

The Conversational State Layer and the Identity/Personality system read the model on a best-effort basis at the start of each turn.

### Conflict Resolution Between Signals

When two signals disagree about the user's state, the model should apply the following resolution rules:

**Higher confidence wins.** If Bluetooth audio routing indicates driving but location says stationary, confidence scores arbitrate.

**Higher cost wins on ambiguity.** When two signals disagree and confidence is equal, the model should assume the higher-cost interpretation for interruption purposes. It is better to under-interrupt than to interrupt at the wrong moment.

**On-change events take priority over periodic readings.** A call state change is more current than a location reading from 3 minutes ago.

---

## 6. Known-Place Model

### Purpose

Provide the semantic location anchors that allow the state model to identify where the user is in meaningful terms — not just GPS coordinates, but named places with known contexts and zone definitions.

### Known Place Schema

Each known place is a named anchor with:

- **`placeId`** — unique identifier
- **`placeName`** — user-readable name: "Home," "Shop," "Office," "Dad's House"
- **`placeType`** — `home` | `shop` | `office` | `vehicle_storage` | `frequent_destination` | `custom`
- **`gpsCenter`** — latitude/longitude of the anchor center
- **`radiusMeters`** — detection radius for geofence entry/exit
- **`associatedBluetoothDevices`** — optional list of Bluetooth device names associated with this place (shop speaker, home hub, etc.) for high-confidence identification when GPS is ambiguous
- **`defaultDampeningProfile`** — which dampening profile to apply when the user is at this place: `shop`, `home`, `office`, `vehicle`, `public`
- **`privacyProfile`** — default privacy sensitivity for events surfaced at this location
- **`zones`** — optional sub-zones within the place (driveway, front door, shop interior, back yard) used by the Environmental Perception Layer for zone-aware events

### Place Detection

The state model attempts to match the current location to a known place using:

1. **GPS proximity** — is the current location within `radiusMeters` of a known place center?
2. **Bluetooth device identity** — is a known associated Bluetooth device connected?
3. **Historical pattern** — does the user frequently visit this location at this time of day?

If two or more signals agree, confidence is high. If only one signal is available, confidence is moderate. If no signals match, `workspaceContext` is set to `UNKNOWN_LOCATION` or `PUBLIC_SPACE`.

### Known Place Lifecycle

Known places can be:

- **Explicitly created** by the user ("set this as my shop")
- **Suggested** by the system when a location is visited frequently over time
- **Edited** to adjust radius or add zone definitions
- **Deleted** with full removal from geofencing and state model

Known place data is durable (Firestore-backed) and shared across devices.

---

## 7. Calendar Context Reader

### Purpose

Provide a continuously updated calendar state signal that reflects what the user's schedule looks like right now and in the near future, so the state model can incorporate scheduling context into interruption tolerance and cognitive load estimates.

### Responsibilities

- read current and upcoming calendar events from `CalendarManager`
- classify the current event type if one is active
- estimate time until the next event
- assess day-level schedule density
- produce a structured `calendarState` object for the state model
- refresh on calendar change events and on a periodic schedule

### Calendar State Derivations

**In-event detection:** if the current time falls within a calendar event's start and end time, `inEventNow` is true. Event type classification (meeting, personal, blocked, travel) uses keywords from the event title and description where permission allows, falling back to `unknown`.

**Upcoming event pressure:** `upcomingEventInMinutes` provides the engine with awareness of schedule pressure. A user 8 minutes from a meeting is in a different interruption context than a user with nothing on their calendar for 3 hours.

**Day density:** light (0–2 events), moderate (3–5 events), heavy (6+ events or back-to-back blocks). Dense schedules correlate with higher baseline cognitive load.

### Privacy Constraints

Calendar content is personal. The calendar context reader should produce structured state signals — event type, timing, density — without reading event content into the state model unless the user has explicitly permitted content-aware calendar integration. Event titles and descriptions should not appear in event bus events or spoken outputs without permission.

---

## 8. Audio Environment Monitor

### Purpose

Provide a lightweight continuous signal about the acoustic environment the user is in, which informs noise level classification and other-presence detection in the state model.

### Signal Approach

The audio environment monitor uses the microphone during listening windows (when the STT engine is active or when background listening is permitted) to classify the acoustic environment rather than transcribe it.

It does not record audio. It does not transmit audio. It produces a classification signal only.

**Noise level classification:** quiet, ambient, elevated. Based on RMS level and frequency pattern analysis.

**Other-presence inference:** detection of multiple distinct voices in the environment suggests others are present. This is a probabilistic inference, not a speaker identification.

### Privacy Constraints

The audio environment monitor operates strictly within the privacy boundaries established by the Trust and Permission Framework. It must never:

- store audio
- transmit audio outside the device
- attempt to identify specific speakers
- run when the user has not granted microphone permission
- run beyond the scope of what the user has been informed about

The classification outputs — noise level and presence inference — are the only artifacts that leave the monitor. They feed the state model and nothing else.

---

## Core Architectural Principles

---

### The Bus Is the Only Path

Every event producer emits to the bus. The bus is the only path to the engine. No worker, monitor, or subsystem may produce user-facing output through any other channel.

This is not a performance recommendation. It is an authority constraint. The moment a secondary path exists, the attention model breaks — because some fraction of output will always escape the engine's judgment.

---

### Interpretation Before Routing

No raw signal reaches the Attention/Relevance Engine.

Every signal is interpreted before it is forwarded. Every event that arrives at the engine carries a meaning — what this signal most likely represents in context — not just what was detected.

The engine evaluates meaning, urgency, and cost. It does not interpret raw sensor output.

---

### State Model Is Always an Estimate

Every field in the Current User State Model is an inference from available signals, not a direct observation. The model carries confidence scores because uncertainty is real and must be accounted for in downstream decisions.

When confidence is low, the engine should behave conservatively — lean toward not interrupting, not toward surfacing.

---

### Staleness Is an Error Condition

A state model field that has not been refreshed within its expected window is not merely imprecise — it is actively misleading. Stale fields must be flagged as such and treated as low-confidence by consumers.

The state model update architecture must prioritize freshness of the fields that change most frequently: device state, conversational state, and activity state.

---

### Heat and State Are Separate Concerns

The Current User State Model describes the user's world. The Attention Dampening System describes Zola's recent behavior. These are conceptually and structurally distinct.

`CurrentHeat` must never be a field in the state model. The state model is a collection of observations about the user's current condition — activity, environment, cognitive load, emotional register. `CurrentHeat` is a measure of how much Zola has recently spent of the user's attention. Mixing these would mean that any consumer reading the state model to understand the user's context also silently reads Zola's speech history, which it neither asked for nor should depend on.

The correct relationship: the dampening system reads the state model to determine which decay rate and dampening profile to apply. The engine reads the dampening system and the state model independently. They meet only inside the engine at the point of decision.

---

### Privacy by Default

The event bus and state model touch sensitive signals: location, audio environment, calendar content, communication metadata, and behavioral patterns. The default posture for all of these is minimum exposure.

- signals are collected only with appropriate permission
- sensitive content (message previews, calendar event titles) does not enter the bus as readable text without explicit user permission
- `privacySensitivity` on events is set conservatively — when in doubt, classify higher
- the state model does not store history; it maintains only the current snapshot

---

## Integration Points

This document connects directly to:

- Attention/Relevance Engine — the primary consumer of both structured events from the bus and the Current User State Model snapshot
- Environmental Perception Layer — the future source of camera, sensor, and smart home raw signals that feed the interpretation lane of the bus
- Contextual Interpretation Layer — defined within this document; processes raw signals before bus forwarding
- Autonomous Behavioral Engine — must emit proposed proactive content as structured bus events rather than calling speech directly
- Conversational State and Momentum Layer — provides and consumes `conversationalReadiness` and turn timing fields from the state model
- Trust, Permission, and Privacy Framework — governs which signals may be collected, what content may appear in events, and which delivery channels are available in which contexts
- Memory System — `relatedEntities` field on events enables post-resolution memory linkage; known-place model is stored in durable memory
- Distributed Presence Architecture — the state model is per-device but must be accessible to the active endpoint concept; known places are shared across devices

---

## Failure Modes and Safeguards

### Bus Bypass

Risk: a worker or monitor produces user-facing output without going through the bus, either by calling speech directly or by posting a notification through a side channel.

Safeguards:
- Architectural enforcement: all existing direct speech calls (`sendAssistantInitiatedTurn`, `NotificationManager.notify` for user-facing notifications) must be removed from workers during the proactive path refactor
- Audit log review: the bus audit log should be compared against actual speech and notification output periodically; any output not traceable to a bus event is a violation
- No worker should hold a reference to `GeminiLiveSession` or `NotificationManager` directly

### Stale State Driving Decisions

Risk: the state model is not refreshed frequently enough, and the engine makes dampening decisions against state that no longer reflects reality.

Safeguards:
- per-field staleness timestamps with consumer-side staleness checks
- on-change event sources (call state, DND, Bluetooth) must update the model immediately on change — not on a polling cycle
- the engine should treat `overallConfidence` below a threshold as a signal to apply conservative (low interruption) behavior

### Interpretation Overconfidence

Risk: the Contextual Interpretation Layer assigns high confidence to an interpretation that is wrong, causing the engine to escalate an event inappropriately.

Safeguards:
- confidence scores on interpreted events should reflect both the quality of the raw signal and the quality of the contextual correlation
- tier 1 events should require high confidence from multiple signals, not a single high-confidence sensor reading
- the false positive reduction rules in the interpretation layer must be actively maintained and tuned

### Event Flood

Risk: a high-frequency signal source (camera detecting motion in a busy area) emits events faster than the engine can process, creating a queue that delays high-urgency events.

Safeguards:
- deduplication keys prevent redundant events from the same source within the suppression window
- tier 4 events should be dropped at the inbound lane during high bus load rather than queued
- the interpretation layer should apply event coalescing — multiple motion detections in the same zone within a short window become one sustained-presence event, not ten individual events

### Known-Place Misidentification

Risk: the user is at an unknown location that is GPS-near a known place and is incorrectly assigned to that place's workspace context.

Safeguards:
- confidence scoring requires agreement between GPS and at least one secondary signal (Bluetooth device, historical pattern) before applying a known-place workspace context with high confidence
- GPS-only place matches should produce moderate confidence at most
- the dampening profile applied from a known place should be confirmed by at least one corroborating signal before selecting a high-cost profile like `SHOP`

---

## Roadmap Considerations

> Note: Implementation phases and sequencing will be defined in coordination with the build planning process. This section captures architectural intent only.

### Dependencies

- The Attention/Relevance Engine must be implemented before the bus outbound lane has a consumer — the bus can be built and validated independently, but events have nowhere to go until the engine exists
- The Environmental Perception Layer (cameras, sensors, smart home) is a future source of raw signals for the interpretation lane — the interpretation lane must be designed to handle raw signals from day one even if the only current sources are software-level workers
- The Trust and Permission Framework must define which signals are permissible and under what conditions before the audio environment monitor and camera integration are activated
- The Known-Place Model requires a user-facing management surface (create, edit, delete known places) before it can be populated beyond defaults

### Open Questions

- What is the right staleness threshold per field category? Activity state may need 30-second freshness. Calendar context can tolerate 5 minutes. What are the right defaults and should they be configurable?
- How should the state model handle a user who has not granted location permission? Which fields degrade gracefully and which become unavailable?
- **Resolved:** `CurrentHeat` is not a field in the state model. The state model describes the user's world. `CurrentHeat` describes Zola's recent output history — it is internal system state owned by the dampening system, not an observation about the user. The dampening system reads the state model to select decay rates and dampening profiles. The Attention/Relevance Engine reads the dampening system and the state model as independent inputs and combines them at evaluation time. `CurrentHeat` is Firestore-backed within the dampening system and persists across process restarts independently of the state model.
- How does the state model behave in a distributed presence scenario where two devices have different local signals? Is the state model per-device, or is there a shared cloud-backed component?
- What is the right minimum confidence threshold for tier 1 events that require override evaluation? This threshold has safety implications and needs careful design.

### Architectural Risks

- The state model's accuracy is directly bounded by the quality and freshness of its signal sources. Early implementations with few signals will produce low-confidence states. The engine must be calibrated to behave correctly under low-confidence conditions, not optimized for the high-confidence case.
- The interpretation layer requires ongoing tuning. Initial false positive rates on camera-derived events may be high enough to erode trust in the system quickly. A conservative default (underclassify rather than overclassify urgency) is strongly preferred during early operation.
- The known-place model depends on user setup. A user who has not defined known places has no workspace context. The fallback behavior — treating unknown location as a moderate-cost context — must be explicitly designed.

---

## Long-Term End State

The Environmental Event Bus and Current User State Model eventually evolve toward:

- a fully populated, continuously refreshed state model with high-confidence signal coverage across all field groups
- interpretation that draws on rich routine history, relationship understanding, and behavioral pattern memory
- a bus that handles camera, sensor, smart home, wearable, and vehicle signals in addition to software-level monitors
- known-place models that include sub-zone awareness and zone-specific dampening profiles
- state model fields that are shared appropriately across the distributed presence layer
- interpretation accuracy that reduces false positives to a level where tier 1 events are genuinely trustworthy

The system should ultimately feel:

- ambient
- accurate
- consistently current
- genuinely contextual

without losing:

- privacy discipline
- signal confidence honesty
- the principle that interpretation and decision are distinct responsibilities
- conservative behavior under uncertainty
