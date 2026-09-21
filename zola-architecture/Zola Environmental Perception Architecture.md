# Environmental Perception Architecture

### Foundational Architecture for Physical-World Environmental Understanding

---

## Vision

The Environmental Perception Architecture exists to allow Zola to continuously observe, classify, and understand meaningful activity occurring within the user's physical environment.

The long-term goal is not to create a surveillance system, a motion-alert platform, or a notification engine.

The long-term goal is to create:

> "a persistent environmental cognition layer capable of understanding what is happening around the user in the physical world."

Environmental Perception should eventually support:

- continuous environmental sensing
- contextual scene understanding
- spatial awareness
- temporal environmental continuity
- multi-sensor environmental reasoning
- environmental memory formation
- activity classification
- environmental anomaly detection
- environmental continuity tracking
- future multimodal environmental cognition

The system should eventually feel less like:

> "a collection of disconnected environmental sensors"

and more like:

> "a continuously aware environmental understanding system."

This architecture directly expands the Environmental Perception concepts introduced in the Zola Master Architecture Plan.

---

## Core Philosophy

### Perception Is Not Attention

Traditional smart systems often merge sensing, interpretation, and notification into a single pipeline.

Example: `motion detected → send alert`

This creates systems that become noisy, exhausting, interrupt-heavy, and behaviorally intrusive.

Traditional systems:

- detect motion and immediately alert
- treat every signal as equally urgent
- conflate awareness with interruption
- produce output without contextual judgment

Zola operates differently:

- perception and attention are architecturally separate
- most environmental activity never reaches the user
- signals are classified, scored, and interpreted before any behavioral decision is made
- silence is the default outcome; output must be earned

The perception layer creates structured environmental understanding. Downstream systems determine whether that understanding deserves attention.

---

## Long-Term Architectural Pillars

---

## 1. Environmental Input Layer

### Purpose

Continuously collect environmental signals from physical-world sensory systems and make them available to the perception pipeline.

### Responsibilities

- receive raw input from all connected sensor and camera sources
- support modular provider registration so new sensor types can be added without architectural changes
- tag each input with source identity, sensor type, and timestamp on ingestion
- pass raw inputs to the Sensor Adapter Layer without interpretation
- maintain no classification or decision logic of its own

### Possible Inputs

- security cameras, driveway cameras, doorbell cameras, and shop cameras
- microphones
- motion sensors and smart home sensors
- wearable sensors
- device telemetry and vehicle systems
- future smart glasses visual streams

### Important Principle

Environmental sensing should remain modular and provider-independent. The Input Layer is a collection surface, not an interpretation layer.

---

## 2. Sensor Adapter Layer

### Purpose

Normalize vendor-specific and hardware-specific environmental data into standardized internal perception signals so the rest of the architecture never depends on a specific provider's payload format.

### Responsibilities

- implement one adapter per sensor provider or hardware type
- translate vendor-specific payloads into a canonical internal signal format
- normalize metadata including timestamps, confidence values, and source identifiers
- apply source tagging so downstream layers always know which physical source generated a signal
- isolate schema changes to the adapter layer — no schema change should propagate into the core pipeline
- log adapter errors without crashing the pipeline; failed adapters should fail silently and be flagged for observability

### Canonical Signal Format

Every normalized signal passing out of the Sensor Adapter Layer must include at minimum:

- `signalId` — unique identifier for this signal instance
- `sourceId` — identifier of the physical sensor or camera that generated the signal
- `sourceType` — enum (CAMERA, MICROPHONE, MOTION_SENSOR, SMART_HOME, WEARABLE, DEVICE_TELEMETRY, VEHICLE, FUTURE_VISION)
- `rawEventType` — the provider's original event classification string (preserved for debugging)
- `timestamp` — normalized UTC timestamp
- `confidence` — normalized 0.0 to 1.0 value representing the provider's confidence in the signal
- `payload` — structured provider-specific data, preserved in canonical wrapper

### Important Principle

The broader perception architecture should never directly depend on vendor-specific APIs or payload formats. All provider coupling is contained within the adapter for that provider.

---

## 3. Signal Normalization Layer

### Purpose

Reduce environmental noise and stabilize raw environmental signals before higher-level perception processing occurs. A single physical event often generates multiple redundant or near-duplicate signals — this layer consolidates them.

### Responsibilities

- suppress duplicate signals from the same source within a short time window
- apply temporal smoothing to reduce jitter from rapidly toggling sensors
- debounce sensor signals that fire repeatedly for a single sustained event
- apply environmental noise reduction to audio and motion signals
- normalize confidence values across sources that use different scoring scales
- reconcile timestamp inconsistencies between sources that may have clock drift
- emit one stable, deduplicated signal per distinct real-world event

### Example

Raw input stream:
> motion detected (camera A, 14:03:01)
> motion detected (camera A, 14:03:01)
> motion detected (camera A, 14:03:02)

Normalized output:
> sustained motion activity detected (camera A, 14:03:01, duration: ongoing)

### Important Principle

The Normalization Layer ensures that one real-world event produces one signal in the pipeline, not a flood of redundant triggers.

---

## 4. Perception Worker Layer

### Purpose

Perform specialized environmental classification and understanding tasks. Each worker is responsible for one domain of environmental understanding and operates independently.

### Responsibilities

- classify normalized signals into meaningful environmental event types
- produce structured perception outputs with confidence scores
- operate as independent workers that do not share state directly
- pass all outputs to the Structured Environmental Event Layer
- never produce user-facing output directly

### Worker Definitions

**Motion Analysis Worker**
Responsibilities: detect and classify movement patterns, track movement persistence across time, analyze movement direction and trajectory, distinguish transient from sustained movement, detect movement anomalies relative to environmental baselines.

**Person Detection Worker**
Responsibilities: detect human presence from camera and sensor signals, classify persons as familiar or unknown where permitted and consented, track trajectory and movement intent (approaching, passing, loitering), distinguish stationary presence from transient passage, flag unexpected presence in sensitive zones.

**Vehicle Detection Worker**
Responsibilities: detect vehicle presence and movement, classify vehicle type where possible, match detected vehicles against known vehicle profiles where permitted, infer arrival and departure intent, detect unexpected vehicles in sensitive areas.

**Package Detection Worker**
Responsibilities: detect package appearance at known delivery locations, detect package removal, track package persistence (how long it has been present), flag packages that remain exposed for extended periods.

**Environmental Audio Worker**
Responsibilities: detect audio anomalies that may indicate meaningful activity, classify sound types (tool use, voices, alarms, vehicles, animals), infer likely activity from audio patterns, suppress audio classification during known high-noise periods such as active shop work.

**Scene Continuity Worker**
Responsibilities: maintain a baseline understanding of how each monitored zone normally appears, detect meaningful scene changes against that baseline, identify object displacement, detect new objects or removed objects in sensitive areas.

### Critical Safeguards

- no worker may produce speech, notifications, or user-facing output
- workers must pass all outputs through the Structured Environmental Event Layer
- person recognition features require explicit user consent before activation
- worker failures must be isolated — one failed worker must not halt the pipeline

### Important Principle

Each worker is a specialist. No worker has authority over user-facing behavior. Workers observe and classify — nothing more.

---

## 5. Spatial Awareness Layer

### Purpose

Allow environmental activity to carry spatial meaning by associating signals with named, user-defined zones that have different significance levels.

### Responsibilities

- maintain a registry of named environmental zones defined by the user
- classify incoming perception events by zone
- apply zone-specific sensitivity weights to events (some zones are more sensitive than others)
- model visibility and coverage gaps per zone so the system understands what it cannot see
- apply zone-based behavioral expectations (what is normal activity in this zone at this time)
- expose zone context to the Contextual Interpretation Layer for downstream meaning assignment

### Zone Examples

- driveway
- front porch
- shop interior
- shop exterior and perimeter
- garage bay
- tool storage area
- mailbox area
- backyard
- vehicle parking area

### Example

Movement detected near the sidewalk adjacent to the property carries low significance — it is expected. Movement detected near the shop tool storage area after midnight carries high significance — it is unexpected in that zone at that time.

### Important Principle

Location matters as much as what was detected. The same signal in different zones may have completely different meanings.

---

## 6. Temporal Environmental Awareness Layer

### Purpose

Allow environmental understanding to evolve over time rather than existing as isolated instantaneous snapshots. Duration, recurrence, and timing all affect the meaning of an event.

### Responsibilities

- track how long a detected event has been ongoing (duration)
- detect repeated activity patterns and flag them for pattern analysis
- model environmental rhythms — what activity is normal at what times of day
- identify events that deviate from expected temporal patterns
- maintain event persistence state (event is ongoing, event has ended, event has resumed)
- expose temporal context to downstream interpretation layers

### Examples

- a person present near the driveway for thirty seconds is likely passing through
- a person present near the shop for eleven minutes after midnight is not passing through
- a vehicle entering the driveway at 6:00 PM on a weekday matches a known routine
- the same vehicle entering the driveway at 3:00 AM does not match any known routine

### Important Principle

Time is context. An event's meaning often cannot be determined without knowing how long it has been happening and when it is happening relative to normal patterns.

---

## 7. Multi-Sensor Correlation Layer

### Purpose

Combine signals from multiple independent sensors to produce stronger, more accurate environmental understanding and reduce false positives that any single sensor would generate in isolation.

### Responsibilities

- correlate signals from different source types that occurred in the same time window
- identify when multiple sensors agree on the same real-world event and increase confidence accordingly
- identify when a single sensor fires in isolation and apply appropriate confidence reduction
- resolve conflicts between sensors reporting inconsistent states
- produce fused perception outputs that represent the best available interpretation of what is happening

### Example Correlations

Camera detects vehicle entering driveway.
Bluetooth proximity detects a known phone nearby.
Fused interpretation: known person likely arriving home. Confidence: high.

Camera detects person near shop exterior.
Motion sensor inside shop does not trigger.
Audio worker does not detect tool use.
Fused interpretation: person is outside the shop, not inside. Zone and activity context both matter.

Camera detects movement near porch.
No other sensors confirm.
Lighting conditions are poor.
Fused interpretation: low confidence detection. Hold pending additional signal.

### Important Principle

No single sensor should be treated as definitive. Correlation across sources produces more reliable environmental understanding than any individual signal alone.

---

## 8. Structured Environmental Event Layer

### Purpose

Convert perception pipeline output into structured environmental events with a consistent schema that downstream cognitive systems can consume without needing to understand the raw perception internals.

### Responsibilities

- receive classified perception outputs from all workers and the correlation layer
- produce structured events in the canonical environmental event format
- attach spatial context from the Spatial Awareness Layer
- attach temporal context from the Temporal Environmental Awareness Layer
- attach confidence and uncertainty values
- assign an expiration timestamp to each event
- route structured events to the Environmental Event Bus

### Canonical Environmental Event Format

Every structured event must include:

- `eventId` — unique identifier
- `eventType` — enum (PERSON_DETECTED, VEHICLE_DETECTED, PACKAGE_DETECTED, MOTION_DETECTED, AUDIO_ANOMALY, SCENE_CHANGE, PERSON_LINGERING, UNKNOWN_PERSON, KNOWN_PERSON, KNOWN_VEHICLE, UNKNOWN_VEHICLE, etc.)
- `zone` — the named zone where the event occurred
- `timestamp` — UTC timestamp of event onset
- `duration` — how long the event has been ongoing (null if instantaneous)
- `confidence` — 0.0 to 1.0
- `sourceSensors` — list of source IDs that contributed to this event
- `correlationStrength` — single-source, partially-corroborated, or fully-corroborated
- `persistenceState` — ONSET, ONGOING, RESOLVED
- `privacySensitivity` — LOW, MEDIUM, HIGH (based on event type and zone)
- `expiresAt` — timestamp after which this event should no longer influence decisions
- `relatedEntityIds` — list of known entity IDs if a familiar person or vehicle was identified
- `metadata` — additional structured data specific to the event type

### Important Principle

The Structured Environmental Event Layer is the contract boundary between perception and cognition. Downstream systems should never need to understand how the perception pipeline works internally.

---

## 9. Confidence and Uncertainty Layer

### Purpose

Maintain explicit uncertainty throughout the perception architecture so that downstream systems always know how much to trust a given signal or event.

### Responsibilities

- track confidence values from the point of raw signal ingestion through to structured event output
- apply confidence degradation rules when conditions reduce signal reliability (poor lighting, sensor obstruction, environmental noise)
- apply confidence boosting rules when multiple independent sources corroborate the same event
- flag events with confidence below the minimum actionable threshold as LOW_CONFIDENCE
- prevent LOW_CONFIDENCE events from triggering high-urgency downstream behavior
- expose confidence history for observability and debugging

### Confidence Degradation Conditions

- poor lighting or night conditions for camera-based detection
- heavy rain, wind, or weather affecting outdoor sensors
- sensor obstruction (camera obscured, microphone muffled)
- high environmental noise interfering with audio classification
- single-source detection with no corroboration

### Confidence Boosting Conditions

- multiple independent sensors agree on the same event
- temporal persistence increases (event has been ongoing, making it less likely to be a false positive)
- known entity match confirmed (vehicle or person recognized against a known profile)
- environmental conditions are favorable

### Important Principle

Low confidence should cause suppression, soft phrasing, or confirmation requests — never high-urgency escalation. Certainty must be earned.

---

## 10. Environmental Continuity Layer

### Purpose

Maintain a continuous, evolving understanding of the environment across time rather than treating each detected event as a fresh, isolated occurrence.

### Responsibilities

- maintain a running environmental state model per zone
- track the current state of ongoing events (who or what is present, how long, in which zone)
- detect when an ongoing event changes state (person arrived, person is lingering, person departed)
- detect when an expected event does not occur (package that was present is no longer present)
- detect environmental state transitions that require re-evaluation of prior interpretations
- provide the current environmental state to the Contextual Interpretation Layer on request

### Example

Instead of:
> motion detected (14:03)
> motion detected (14:09)
> motion detected (14:14)

The Environmental Continuity Layer produces:
> unknown person has been present near the shop exterior for eleven minutes

This is the input the Contextual Interpretation Layer can reason about meaningfully.

### Important Principle

Environmental continuity converts isolated detections into ongoing situational awareness. Duration and persistence carry meaning that individual snapshots do not.

---

## 11. Environmental Memory Integration Layer

### Purpose

Allow meaningful environmental activity to contribute to the Memory Hierarchy so that Zola learns what is normal, recognizes recurring patterns, and improves contextual interpretation over time.

### Responsibilities

- identify environmental events that are candidates for episodic or behavioral memory
- pass memory write candidates to the Memory Hierarchy's Durable Write Authority — never write directly
- contribute to routine and baseline modeling (what visitors, vehicles, and activity patterns are normal)
- enable the Temporal Environmental Awareness Layer to compare current activity against learned historical patterns
- support retention and deletion of environmental memory in accordance with user privacy settings

### Write Candidate Types

- recurring visitor pattern (a person appears regularly at predictable times)
- known vehicle arrival pattern (a specific vehicle arrives on a regular schedule)
- environmental baseline update (what the shop perimeter normally looks like at night)
- anomaly that confirmed as significant (used to tune future anomaly detection thresholds)

### Write Rules

- all memory writes must pass through Durable Write Authority
- low-confidence events must not create durable memory entries
- privacy-sensitive events (person recognition data) require explicit user consent before any write
- environmental memory must support user-initiated deletion at the individual record level

### Important Principle

Environmental memory should make the system smarter over time — not become a surveillance record. Retention must be purposeful, consent-driven, and deletable.

---

## 12. Environmental Event Bus Layer

### Purpose

Route structured environmental events from the perception pipeline to all downstream cognitive systems that need to consume them, without creating tight coupling between producers and consumers.

### Responsibilities

- receive structured events from the Structured Environmental Event Layer
- route events to registered consumers (Contextual Interpretation Layer, Environmental Awareness Architecture, Current User State Model, Environmental Memory Integration Layer)
- support consumer registration and deregistration without pipeline disruption
- apply privacy sensitivity filters — HIGH privacy sensitivity events must only route to consumers with appropriate permission
- log all routing decisions for observability
- handle consumer failures gracefully — a failed consumer must not block event delivery to other consumers

### Important Principle

The Event Bus decouples perception from cognition. Producers do not need to know who consumes their events, and consumers do not need to understand how events were produced.

---

## 13. Distributed Environmental Cognition Layer

### Purpose

Allow environmental perception to scale through distributed specialized workers that operate in parallel without creating competing decision authorities.

### Responsibilities

- support multiple perception workers running in parallel on independent signal streams
- coordinate worker outputs through the Structured Environmental Event Layer
- prevent any individual worker from producing user-facing behavior independently
- isolate worker failures so that one failed worker does not halt environmental perception
- support future addition of new worker types without architectural changes to the core pipeline

### Authority Boundary

Workers in this layer may:
- observe environmental signals
- produce classification outputs
- contribute to structured environmental events

Workers in this layer must not:
- speak to the user
- send notifications
- write to memory directly
- escalate to security workflows
- make behavioral decisions

All behavioral decisions remain with the centralized attention and authority systems.

### Important Principle

Distribution increases capability. It must not distribute authority. Zola remains the single behavioral authority regardless of how many perception workers are running.

---

## 14. Privacy, Trust, and Permission Layer

### Purpose

Ensure that all environmental perception operates within user-defined privacy boundaries, that sensitive capabilities require explicit consent, and that the system remains explainable and user-controlled.

### Responsibilities

- maintain the registry of permitted sensor sources and zones per user
- enforce zone-level monitoring permissions (some zones may be explicitly excluded from monitoring)
- gate person recognition features behind explicit consent — these features must be disabled by default
- prevent camera or sensor data from being retained beyond the defined retention window without consent
- apply privacy sensitivity labels to all structured events
- block HIGH sensitivity events from routing to consumers without appropriate permission
- support user-initiated audit of what is being monitored and what has been detected
- support user-initiated deletion of specific environmental memory records

### Protected Categories

The following require explicit, separately granted consent before activation:

- facial or person recognition
- vehicle license plate recognition
- retention of camera-derived events beyond the current session
- sharing of environmental data with external services

### Zone Exclusions

Users must be able to explicitly exclude zones from monitoring. Excluded zones must be enforced at the Input Layer — signals from excluded zones must not enter the pipeline at all.

### Important Principle

Trust depends on the user knowing what is being monitored, being able to turn it off, and being able to see what has been recorded. Environmental perception must never operate in a way the user would not sanction if they knew about it.

---

## 15. Failure and Reliability Layer

### Purpose

Ensure that environmental perception degrades gracefully when sensors fail, connectivity is lost, or workers encounter errors — without silently producing incorrect output.

### Responsibilities

- detect sensor failures and flag affected signal streams as UNAVAILABLE
- apply confidence decay to zones where sensors have gone offline (reduced coverage means reduced certainty)
- isolate worker failures so the pipeline continues operating with reduced capability
- surface sensor availability status to the observability layer
- prevent a degraded perception state from producing overconfident events
- support graceful recovery when sensors come back online

### Failure Behaviors

When a sensor goes offline:
- mark its zone coverage as PARTIAL or UNAVAILABLE
- apply a confidence penalty to events in that zone
- do not produce HIGH confidence events for zones with degraded coverage

When a worker fails:
- log the failure with timestamp and error details
- continue operating with the remaining workers
- do not suppress events from other workers
- flag the affected event types as WORKER_UNAVAILABLE in the Event Bus

When the Event Bus fails:
- log all undelivered events locally with timestamps
- attempt replay when connectivity is restored
- do not block the perception pipeline waiting for consumers

### Important Principle

A degraded system should produce uncertain output, not confident wrong output. Sensor failures must reduce confidence, not be silently ignored.

---

## 16. Observability and Debugging Layer

### Purpose

Provide deep visibility into every stage of the environmental perception pipeline so that any output — or any absence of output — can be explained, traced, and validated.

### Responsibilities

- log every signal received at the Input Layer with source, type, and timestamp
- log every normalization action taken (duplicate suppressed, signal debounced, confidence adjusted)
- log every worker classification output with confidence and source signals
- log every correlation decision with the contributing signals and the fused result
- log every structured event produced with its full schema
- log every routing decision in the Event Bus
- log every confidence adjustment applied by the Confidence and Uncertainty Layer
- expose a queryable log surface for debugging unexpected behavior

### Required Queryable Questions

The observability system must be able to answer:

- Why did Zola speak about this event?
- Why did Zola stay silent about this event?
- What sensors contributed to this event?
- What was the confidence level at each stage?
- Was this event within a permitted zone?
- Was this event routed to the attention system?
- Was this event suppressed before reaching the attention system, and why?

### Important Principle

If the system cannot explain its behavior in retrospect, it cannot be trusted. Observability is not optional.

---

## 17. Future Vision Intelligence Layer

### Purpose

Support future vision-assisted environmental understanding capabilities that go beyond motion and presence detection toward genuine scene comprehension.

### Responsibilities

- provide an integration point for future computer vision models
- support tool and object recognition in the shop environment
- support workspace state awareness (tools in use, project state, workspace changes)
- support smart glasses visual stream integration when available
- support scene description and contextual annotation of physical environments
- maintain the same privacy, consent, and authority boundaries as all other perception layers

### Future Capabilities

- tool recognition (which tools are in use, which are missing)
- workspace continuity (project state tracked across shop sessions)
- smart glasses scene understanding (ambient contextual awareness from the user's point of view)
- object tracking across sessions (where did that part end up)
- environmental change detection at a semantic level (the car has been moved, the hood is open)

### Important Principle

Vision intelligence must remain within the same architectural boundaries as all other perception. Richer input does not create new behavioral authority.

---

## Core Architectural Principles

---

### Perception Is Continuous

Environmental perception operates regardless of whether the user is actively interacting with Zola. Understanding the environment is a background responsibility, not an on-demand capability.

---

### Perception and Attention Are Architecturally Separate

Detection is never directly coupled to interruption. Every signal passes through classification, interpretation, and attention scoring before any behavioral decision is made. The perception pipeline has no authority over user-facing behavior.

---

### Environmental Signals Are Not Notifications

The vast majority of environmental signals should result in silence — a silent log entry at most. Interrupting the user requires the signal to pass through the full attention and relevance system. The perception layer never makes that call.

---

### Environmental Understanding Is Probabilistic

The system operates on confidence levels, not binary certainty. Low-confidence signals must produce uncertain outputs. High-urgency behavior requires high confidence. The two must be explicitly linked.

---

### Restraint Is Intelligence

The measure of this system's quality is not how much it detects — it is how accurately it understands what matters. A system that fires on everything is as useless as one that fires on nothing.

---

## Integration Points

This document connects directly to:

- Zola Master Architecture Plan (Sections 7 and 8)
- Environmental Awareness Architecture
- Contextual Interpretation Layer
- Attention and Relevance Engine (Sections 9 and 9a)
- Memory Hierarchy Architecture
- Autonomous Behavior Architecture
- Current User State Model (Section 17)
- Trust, Permission, and Privacy Framework (Section 13)
- Distributed Cognitive Worker Architecture (Section 20)

---

## Failure Modes and Safeguards

### False Positive Flood

Risk: Sensors produce a high volume of low-quality signals that overwhelm the pipeline and cause the system to generate excessive environmental events, leading to attention fatigue downstream.

Safeguards:
- Signal Normalization Layer deduplicates and debounces before events reach workers
- Confidence and Uncertainty Layer flags low-quality signals before they propagate
- workers apply minimum confidence thresholds before producing classification outputs
- the Attention and Relevance Engine applies heat-based suppression downstream

### Silent Sensor Failure

Risk: A sensor goes offline and the system continues operating as if it has full coverage, producing overconfident events for zones it can no longer see.

Safeguards:
- Failure and Reliability Layer detects sensor unavailability and marks affected zones
- confidence is degraded for zones with reduced coverage
- HIGH confidence events cannot be produced for zones with PARTIAL or UNAVAILABLE coverage

### Privacy Boundary Violation

Risk: Person recognition, camera retention, or sensitive zone monitoring activates without explicit user consent.

Safeguards:
- Privacy, Trust, and Permission Layer gates consent-required features at the Input Layer
- excluded zones are enforced before signals enter the pipeline — not filtered after
- HIGH sensitivity events are blocked from routing to consumers without permission

### Worker Authority Drift

Risk: A perception worker begins producing user-facing output or writing to memory directly, bypassing the authority structure.

Safeguards:
- workers have no access to speech, notification, or memory write APIs
- all worker outputs route through the Structured Environmental Event Layer
- observability logs prove the source of every output; any output not traceable to the Response Governor is a violation

### Stale Event Acting

Risk: An event that was generated under different conditions remains active past its relevance window and influences downstream decisions based on outdated information.

Safeguards:
- every structured event carries an `expiresAt` timestamp
- downstream consumers must not act on expired events
- the Event Bus must filter expired events before delivery

---

## Roadmap Considerations

> Note: Implementation phases and sequencing will be defined after the Ava codebase audit and delta analysis are complete. This section captures architectural intent only.

### Dependencies

- Sensor Adapter Layer must exist before any other perception component can receive normalized signals
- Structured Environmental Event canonical format must be defined and agreed upon before workers, the Event Bus, or downstream consumers are built
- Privacy and Permission Layer must be implemented before any person recognition or camera retention features are activated
- Memory Hierarchy Architecture must be stable before the Environmental Memory Integration Layer can write candidates

### Open Questions

- Which sensor and camera integrations exist in Ava today and which need to be built from scratch?
- Should perception workers run as separate processes, separate threads, or coroutines within a single runtime?
- What is the minimum retention window for environmental events before they expire?
- How should the system handle zones where coverage is permanently partial (a camera that only sees part of the driveway)?
- Should the user be able to see a live view of what environmental events have been detected in the current session?

### Architectural Risks

- Person recognition is a high-value feature that carries significant privacy and consent risk — building it before the Privacy and Permission Layer is solid is a serious architectural mistake
- Sensor adapter proliferation may become a maintenance burden if each adapter is built ad hoc rather than against a strict interface contract
- Environmental continuity state may become large over time if events are not expired and cleaned up aggressively

---

## Long-Term End State

Environmental Perception eventually evolves toward:

- continuous, reliable understanding of all monitored physical zones
- accurate person, vehicle, package, and activity classification
- rich temporal and spatial context attached to every event
- multi-sensor corroboration producing high-confidence, low-noise output
- vision-assisted scene understanding in the shop and future environments
- smart glasses integration enabling ambient first-person environmental awareness
- environmental memory that improves accuracy and reduces false positives over time

The system should ultimately feel:

- continuously aware without being intrusive
- accurate enough to trust for security and safety decisions
- spatially and temporally intelligent
- privacy-respecting by architecture, not by policy alone

without losing:

- the separation between perception and behavioral authority
- user control over what is monitored and what is retained
- confidence discipline — uncertain signals must never produce certain outputs
- the principle that restraint is a measure of intelligence, not a limitation
