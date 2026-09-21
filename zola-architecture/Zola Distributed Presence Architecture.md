# Distributed Presence Architecture

### Foundational Architecture for One Mind, Many Bodies

---

## Vision

Zola should not be architected as a single app, a single device, or a phone-bound assistant.

The long-term goal is to evolve Zola into a persistent cognitive presence capable of existing across multiple devices and environments simultaneously — where the intelligence is independent of any specific hardware, and devices become embodiments of a single unified mind.

The system should eventually feel less like:

> "an assistant app installed on a phone"

and more like:

> "a persistent presence that is with the user wherever they are."

The long-term architecture goal is: **one mind, many bodies.**

---

## Core Philosophy

### Intelligence Is Independent of Hardware

Traditional assistant systems:

- are bound to a specific device or app
- restart context when the user switches devices
- treat each device as an independent assistant instance
- require the user to re-establish context after any transition

This system:

- maintains persistent intelligence independent of any endpoint
- allows conversation to transition across devices without losing continuity
- treats devices as embodiments of a single cognitive layer, not isolated products
- ensures the user always feels like they are talking to the same Zola

The intelligence itself — memory, identity, reasoning, conversational continuity, personality — remains unified and device-independent. Devices become interfaces, embodiments, and interaction surfaces. The cognitive layer remains one.

---

## Long-Term Architectural Pillars

---

## 1. Core Presence Layer

### Purpose

Maintain the persistent, device-independent intelligence layer that all endpoints connect to. This is the unified mind — the single authoritative source for everything that defines who Zola is and what she knows.

### Responsibilities

- maintain Zola's identity and personality state
- maintain the unified memory hierarchy across all layers
- maintain conversational continuity and topic stack state
- maintain the current user state model
- maintain relationship understanding and social context
- own all autonomy rules and behavioral authority
- orchestrate cognition across all connected endpoints and workers
- remain operational and consistent regardless of which endpoints are active
- survive device switches, app restarts, hardware changes, and endpoint additions without losing state

### Shared State Owned by the Core Presence Layer

All endpoints read from and write to the Core Presence Layer for:

- Identity Seed and Style Profile (read-only for endpoints; written by Behavioral Learning Layer)
- Memory Hierarchy state across all six layers
- Conversational State Engine and topic stack
- Current User State Model
- Attention Dampening heat value
- Autonomous mode setting
- Trust and Permission Framework state
- Active environmental awareness context

### Important Principle

The Core Presence Layer must remain device-independent. It must survive any single endpoint going offline, any device being switched, and any hardware being replaced. The intelligence is not in the device — the device is a window into the intelligence.

---

## 2. Device Endpoint Layer

### Purpose

Provide physical interaction surfaces that connect into the Core Presence Layer, enabling the user to interact with Zola through whatever device is most appropriate for their current context.

### Responsibilities

- establish and maintain a connection to the Core Presence Layer
- capture speech and deliver spoken output appropriate to the endpoint's capabilities
- apply endpoint-specific interaction constraints (safety rules, privacy rules, delivery format)
- report endpoint context to the Core Presence Layer (device type, environment, noise level, active users)
- handle graceful degradation when Core Presence Layer connectivity is interrupted
- never operate as an independent assistant instance

### Endpoint Authority Model

Endpoints are clients of the Core Presence Layer — not independent agents. An endpoint:

- may capture input and forward it to the Core Presence Layer
- may render output as instructed by the Core Presence Layer
- may apply local delivery constraints (e.g., no private speech in public)
- may not make independent cognitive decisions
- may not maintain independent memory
- may not produce user-facing output without Core Presence Layer authorization

### Important Principle

Endpoints are embodiments, not brains. The intelligence lives in the Core Presence Layer. The endpoint provides the senses and the voice.

---

## 3. Phone Endpoint

### Purpose

Serve as the primary mobile embodiment and the initial anchor for the distributed presence system. The phone is the most capable and most consistently available endpoint.

### Why the Phone Is the Right Initial Anchor

The phone already contains:
- microphone and speaker access
- notifications and messaging
- GPS and location
- calendar access and contacts
- internet connectivity
- wearable integration
- persistent proximity to the user

### Responsibilities

- serve as the primary mobile interaction layer
- serve as the contextual awareness hub when other endpoints are not active
- provide location, calendar, messaging, and device state context to the Core Presence Layer
- handle all standard voice interaction
- relay wearable data to the Core Presence Layer
- act as the fallback endpoint when specialized endpoints are unavailable

### Interaction Profile

- response length: concise, mobile-appropriate
- tone: full personality access
- input method: voice primary, touch secondary
- privacy: standard — adapt based on environment detection

### Important Principle

The phone is the first body, not the only body. It establishes presence and provides context. As additional endpoints come online, the phone becomes one embodiment among several rather than the exclusive interaction surface.

---

## 4. PC and Desktop Endpoint

### Purpose

Provide a deeper, longer-form interaction surface for extended work sessions, technical collaboration, and productivity-aware assistance.

### Responsibilities

- support conversational continuity from phone sessions without requiring re-establishment of context
- provide a persistent ambient or sidebar mode for low-interruption awareness
- support deeper long-form interaction appropriate to a seated work context
- detect active work context (coding, writing, document work) and adapt proactive behavior accordingly
- enforce stronger privacy filtering — desktop environments may capture meeting audio or work calls

### Interaction Profile

- response length: fuller, more detailed when appropriate
- tone: collaborative, technically deeper
- input method: voice and keyboard
- privacy: elevated — shared workspace audio requires stronger ambient suppression

### Long-Term Goal

Conversation transitions naturally between phone and PC without the user needing to reintroduce context. A topic begun on the phone during a commute continues on the PC when the user sits down.

### Important Principle

The PC endpoint changes the depth and register of interaction — not the identity or the continuity. Zola on the PC is the same Zola as on the phone, with a different interaction style appropriate to the context.

---

## 5. Shop Presence Endpoint

### Purpose

Create a hands-free, environment-aware interaction layer specifically designed for workspace and garage contexts where the user's hands are occupied and the environment is loud.

### Potential Hardware

- mounted tablet
- dedicated speaker and microphone device
- local workstation
- future embedded system

### Responsibilities

- support hands-free voice interaction as the primary input mode
- apply elevated noise tolerance for high-ambient-noise environments
- activate project memory context relevant to current build work
- support technical lookups relevant to active projects (torque specs, part numbers, wiring diagrams)
- provide music control, message summaries, and work session continuity
- detect tool use and active shop work as signals for increased interruption restraint
- apply shop-specific autonomy mode constraints

### Interaction Profile

- response length: concise — the user's hands are busy
- tone: casual, practical, project-aware
- input method: voice only
- privacy: shop context — fewer third-party privacy concerns but elevated noise suppression needed

### Shop-Specific Authority Questions

The shop endpoint raises a coordination question that is not fully resolved: when the phone is not nearby, does the shop endpoint have local authority to handle requests independently, or does it always route through the Core Presence Layer?

The answer must be defined before the shop endpoint is built:

- **Full routing model**: the shop endpoint always routes through the Core Presence Layer. All cognition happens centrally. The shop endpoint is a pure audio interface.
- **Local authority model**: the shop endpoint can handle a defined subset of requests (music control, timers, simple lookups) locally when Core Presence Layer connectivity is degraded, but defers all memory writes and complex reasoning to the Core Presence Layer when connectivity is restored.

This is an open architectural decision that requires resolution during the audit and delta analysis phase.

### Long-Term Goal

The shop environment begins to feel conversationally interactive — not as a smart home gimmick, but as a genuine extension of Zola's presence into a space where the user spends meaningful time.

### Important Principle

The shop endpoint should reduce friction, not add it. Every interaction should feel faster and more natural than reaching for a phone.

---

## 6. Vehicle Endpoint

### Purpose

Provide a safety-aware interaction layer for driving contexts where the user's cognitive load and attention demands are fundamentally different from any other environment.

### Responsibilities

- apply driving-aware interaction constraints across all output types
- limit proactive output to navigation, safety, and time-critical information only
- shorten all responses significantly — driving is not a context for extended conversation
- support route-aware and traffic-aware contextual assistance tied to active navigation
- detect driving state from Bluetooth connection, GPS movement speed, or explicit signal
- disable or heavily suppress non-urgent autonomous behavior during active driving

### Interaction Profile

- response length: very short — one or two sentences maximum for most responses
- tone: calm, direct, no humor
- input method: voice only
- privacy: vehicle context — concise information only, no sensitive content surfaced

### Safety Override Rules

In the vehicle context:

- navigation and safety events may surface without full dampening evaluation
- all non-safety proactive output is suppressed during active driving
- message content must not be read aloud without explicit prior permission
- complex technical discussions should be deferred to a non-driving context

### Important Principle

Safety is not a feature of the vehicle endpoint — it is the defining constraint. Every design decision for the vehicle endpoint must begin with: does this make the driving context safer or less safe?

---

## 7. Wearables and Smart Glasses Endpoint

### Purpose

Provide a lightweight, ambient interaction layer through wearable devices — with smart glasses representing the most significant long-term embodiment opportunity for persistent vocal computing.

### Responsibilities

- support passive contextual awareness through wearable sensors
- relay health, activity, and proximity data to the Core Presence Layer
- support lightweight voice interaction appropriate to wearable form factors
- for smart glasses: provide heads-up contextual information that is useful without being distracting
- for smart glasses: support vision-assisted environmental understanding and scene awareness
- apply elevated privacy constraints in public environments

### Smart Glasses Interaction Principles

Smart glasses must not become:
- a constant notification overlay
- a distraction layer that competes with the user's physical environment
- a gimmicky heads-up display for information the user did not ask for

Smart glasses should instead become:
- a lightweight ambient awareness surface for genuinely useful contextual information
- a natural extension of voice interaction that does not require reaching for a phone
- a vision-assisted cognition layer that helps Zola understand the user's environment

### Long-Term Strategic Importance

Smart glasses may eventually become the most natural embodiment of persistent vocal computing. The interaction model — always present, always aware, requiring no device retrieval — is the closest existing technology comes to the vision of Zola as a persistent presence rather than an app.

### Interaction Profile

- response length: minimal — glasses interactions should be brief and ambient
- tone: lightweight, non-intrusive
- input method: voice primary
- privacy: elevated — public environment requires strong suppression of private content

### Important Principle

Glasses interactions should feel like having a knowledgeable presence nearby — not like wearing a notification device. The bar for surfacing information through glasses must be higher than any other endpoint, not lower.

---

## 8. Endpoint Coordination and Transition

### Purpose

Define how multiple active endpoints coordinate with each other and the Core Presence Layer so that conversation transitions between devices feel seamless and the user never experiences a context reset.

### Responsibilities

- maintain awareness of which endpoints are currently active and connected
- determine the primary active endpoint at any given moment
- route input from the correct source when multiple endpoints are active simultaneously
- deliver output to the correct endpoint based on context and user location
- handle seamless transition when the user moves from one endpoint context to another
- prevent duplicate responses when multiple endpoints are active
- resolve conflicts when multiple endpoints receive the same input simultaneously

### Primary Endpoint Determination

When multiple endpoints are active, the Core Presence Layer must determine which is primary for input and output. Priority order:

1. endpoint the user most recently actively interacted with
2. endpoint closest to the user's current physical location (where determinable)
3. endpoint most appropriate for the current context (vehicle while driving, shop while in shop)
4. phone as default fallback

### Transition Behavior

When the user moves from one endpoint context to another:

- the Core Presence Layer continues uninterrupted — there is no "handoff"
- the new endpoint connects and identifies itself and its context
- the Core Presence Layer updates the active endpoint priority
- no conversational context is lost
- no reintroduction of topics is required
- the Style Profile adapts to the new endpoint context label automatically

Example transition:

1. User begins a conversation about a car project on the phone during a commute.
2. User arrives at the shop. Shop endpoint activates.
3. Shop endpoint reports its context to the Core Presence Layer.
4. Core Presence Layer updates the active endpoint and context label.
5. User continues the car project conversation on the shop endpoint without any reset.
6. Zola's style adapts to shop context — more casual, more project-aware — while the topic thread continues.

### Simultaneous Endpoint Handling

When multiple endpoints are active simultaneously and receive the same input (e.g., a voice command audible to both the phone and the shop device):

- the Conversational Attention Architecture determines which endpoint's detection takes priority
- the Core Presence Layer processes the input once from the authoritative source
- only one endpoint produces output
- duplicate processing is suppressed

### Important Principle

Transitions between endpoints should be invisible to the user. The user should never need to say "continue where we left off" after moving from one device to another.

---

## 9. State Synchronization Protocol

### Purpose

Define how the Core Presence Layer maintains consistent state across all endpoints and how state is restored after disconnection, device switch, or session interruption.

### Responsibilities

- serialize conversational state into portable snapshots at regular intervals and on meaningful events
- distribute state snapshots to all connected endpoints for local caching
- restore state from the most valid available snapshot after reconnection
- detect and resolve conflicts between snapshots from different sources
- ensure that state restoration does not overwrite more recent valid state with older cached state

### State Snapshot Contents

The state snapshot includes:
- active topic and topic stack (from Conversational State Engine)
- active entities and unresolved references
- current emotional tone
- current attention weights
- current user state model
- current autonomy mode
- current heat value from Attention Dampening System
- Style Profile current state
- active environmental context
- last interaction timestamp
- source endpoint identifier

### Conflict Resolution Rules

When snapshots from multiple sources conflict:

1. compare last meaningful interaction timestamp — not last sync timestamp
2. prefer the snapshot from the endpoint with the most recent genuine user interaction
3. if timestamps are equivalent, prefer the snapshot with higher confidence values
4. if unresolved tasks exist in one snapshot but not the other, preserve them
5. log the conflict and both snapshot states for auditability

The newest snapshot does not automatically win. The most valid snapshot wins.

### Offline and Degraded Connectivity Behavior

When an endpoint loses connectivity to the Core Presence Layer:

- the endpoint may continue handling simple, local requests if the local authority model is implemented (see Shop Presence Endpoint)
- the endpoint must not write to memory, execute sensitive tools, or make behavioral decisions that require Core Presence Layer authority
- when connectivity is restored, the endpoint syncs its local interaction log and defers all pending decisions to the Core Presence Layer
- the Core Presence Layer resolves any conflicts between what the endpoint handled locally and the authoritative state

### Important Principle

State synchronization must prioritize accuracy over speed. A slightly delayed state restoration that is correct is always preferable to an immediate restoration that overwrites valid state with stale data.

---

## 10. Distributed Cognitive Worker Architecture

### Purpose

Allow Zola to scale cognitive processing, environmental awareness, monitoring, and background reasoning through specialized background workers — without distributing the behavioral authority that belongs exclusively to the Core Presence Layer.

### Core Philosophy

Workers are not independent assistants. Workers are specialized cognitive subsystems that observe, analyze, prepare, or monitor specific domains. All behavioral authority remains with the Core Presence Layer.

### Worker Categories

**Environmental Workers** — observe and classify physical environment signals.

Examples: security camera analysis worker, vehicle activity worker, smart home monitoring worker, environmental audio worker, weather and traffic watcher.

Responsibilities: environmental observation, event generation, anomaly detection, structured environmental summaries.

**Human Context Workers** — enrich the user state model with human context signals.

Examples: calendar awareness worker, health and activity worker, messaging summarization worker, communication priority worker, routine analysis worker.

Responsibilities: context enrichment, routine tracking, behavioral pattern analysis, human-state signal generation.

**Cognitive and Memory Workers** — support background memory operations without blocking live conversation.

Examples: episodic memory consolidation worker, conversational summary worker, deferred cognition worker, relationship trend analysis worker, memory resurfacing worker.

Responsibilities: memory organization, contextual summarization, long-term pattern extraction, deferred insight generation.

**Attention and Behavioral Workers** — prepare attention and behavioral signals for the Core Presence Layer's decision-making.

Examples: interruption scoring worker, conversational attention worker, urgency classification worker, trust and privacy validation worker, social context worker.

Responsibilities: attention analysis, interruption suitability scoring, speech suppression recommendations, contextual gating.

### Worker Authority Boundary

Workers may:
- observe signals from their domain
- produce structured events and recommendations
- prepare context for the Core Presence Layer
- summarize and organize information

Workers must not:
- speak directly to the user
- send notifications independently
- write to memory directly
- make behavioral decisions
- bypass the Core Presence Layer's authority

### Event Bus

Workers communicate with the Core Presence Layer through structured events on a shared event bus — not through direct function calls or shared mutable state. This creates modularity, auditability, and centralized behavioral control.

Each event includes: event source, event type, timestamp, urgency score, confidence score, environmental context, user-state assumptions, expiration time, suggested actions, suppression recommendations, privacy sensitivity level, and escalation capability.

### Important Principle

Workers increase capability. They must never distribute authority. The Core Presence Layer remains the single behavioral authority regardless of how many workers are running.

---

## Core Architectural Principles

---

### One Mind, Many Bodies

The intelligence is unified and device-independent. Endpoints are embodiments, not instances. The user is always talking to the same Zola — the delivery adapts to the device, the identity does not.

---

### Endpoints Are Clients, Not Agents

No endpoint has independent cognitive authority. Endpoints capture input, render output, and apply local delivery constraints. All reasoning, memory, and behavioral decisions belong to the Core Presence Layer.

---

### Transitions Must Be Invisible

Moving from one endpoint to another should produce no perceptible break in conversation, no loss of context, and no requirement to reintroduce topics. The user should never need to manage their own conversational state across devices.

---

### State Accuracy Over Speed

State synchronization prioritizes correctness over immediacy. A delayed but accurate state restoration is always preferable to an immediate restoration that corrupts valid state with stale data.

---

### Workers Amplify, They Do Not Decide

The distributed worker architecture scales capability without distributing authority. Workers observe, prepare, and recommend. The Core Presence Layer decides, speaks, and acts.

---

## Integration Points

This document connects directly to:

- Zola Master Architecture Plan (Sections 12 and 20)
- Conversational Continuity Architecture (State Snapshot and Sync Protocol)
- Identity and Personality Framework (cross-endpoint consistency)
- Memory Hierarchy Architecture (shared memory state across endpoints)
- Conversational Attention Architecture (multi-endpoint attention coordination)
- Environmental Awareness Architecture (distributed environmental workers)
- Environmental Perception Architecture (distributed perception workers)
- Autonomous Behavior Architecture (worker authority boundaries)
- Trust, Permission, and Privacy Framework (endpoint-specific privacy rules)

---

## Failure Modes and Safeguards

### Context Loss on Transition

Risk: When the user moves from one endpoint to another, conversational context is lost and the user must reintroduce topics — breaking the seamless presence promise.

Safeguards:
- state snapshots are distributed to all active endpoints so local caches exist
- the Core Presence Layer never loses state — endpoints connect to it, not the other way around
- transition behavior is explicitly tested as a required proof point before any new endpoint ships

### Stale Snapshot Overwrite

Risk: A reconnecting endpoint pushes a cached snapshot that is older than the current Core Presence Layer state, corrupting valid state with stale data.

Safeguards:
- conflict resolution compares meaningful interaction timestamp, not sync timestamp
- the Core Presence Layer state is authoritative — endpoints may not overwrite it without resolution
- all conflicts are logged with both states for auditability

### Duplicate Response

Risk: Multiple endpoints receive the same voice input simultaneously and both attempt to respond, producing competing or duplicated output.

Safeguards:
- the Conversational Attention Architecture determines input authority per endpoint
- the Core Presence Layer processes each input once from the authoritative source
- output is routed to one endpoint only — duplicate suppression is enforced at the Core Presence Layer

### Endpoint Acting as Independent Agent

Risk: An endpoint — particularly the shop endpoint in offline mode — begins making behavioral decisions, writing memory, or producing output independently, bypassing the Core Presence Layer's authority.

Safeguards:
- local authority scope (if implemented) is strictly defined and limited to a small set of safe, reversible actions
- memory writes are always deferred to the Core Presence Layer
- all locally handled interactions are logged and synced for Core Presence Layer review on reconnection
- any output produced offline is marked as local-provisional and reviewed before being treated as authoritative

### Worker Authority Drift

Risk: A cognitive worker begins making behavioral decisions or producing user-facing output directly, bypassing the Core Presence Layer.

Safeguards:
- workers have no access to speech, notification, or memory write APIs
- all worker outputs route through the event bus to the Core Presence Layer
- observability logs prove the source of every output
- any output not traceable to Core Presence Layer authorization is a violation

### Identity Fragmentation

Risk: Different endpoints develop meaningfully different interaction styles over time, causing the user to experience Zola as different assistants on different devices.

Safeguards:
- Style Profile is maintained as a shared Core Presence Layer resource, not per-endpoint
- endpoint-specific context labels allow appropriate style adaptation without fragmenting identity
- baseline review in the Identity and Personality Framework checks for cross-endpoint consistency

---

## Roadmap Considerations

> Note: Implementation phases and sequencing will be defined after the Ava codebase audit and delta analysis are complete. This section captures architectural intent only.

### Dependencies

- Conversational Continuity Architecture must be stable before state snapshot and sync can be built on top of it
- Memory Hierarchy Architecture must be stable before the Core Presence Layer can own shared memory state
- Identity and Personality Framework must define the shared Style Profile before cross-endpoint synchronization is implemented
- Conversational Attention Architecture must resolve multi-endpoint input coordination before simultaneous endpoints are supported

### Open Questions

- Should the Core Presence Layer be a server-side service, a local service on the primary device, or a hybrid? This is the most consequential architectural decision for this system and must be resolved before any implementation begins.
- What is the exact scope of local authority for the shop endpoint in offline mode — and is local authority worth the added complexity?
- How should the system handle a user who uses multiple accounts or profiles across devices?
- What is the maximum acceptable latency for state synchronization between the Core Presence Layer and connected endpoints before the user perceives a break in continuity?
- How should the system handle an endpoint that goes offline mid-conversation and comes back online after the conversation has moved on?
- Should the user be able to see which endpoint is currently primary and which endpoints are connected?

### Architectural Risks

- The shop endpoint local authority question is the largest unresolved risk in this architecture — the decision to support local authority adds significant complexity and offline conflict resolution requirements; the decision not to support it requires reliable connectivity to the Core Presence Layer from the shop, which may not always be available
- The Core Presence Layer's hosting model — server-side versus local — has profound implications for latency, privacy, offline behavior, and data sovereignty; this decision must be made deliberately and early
- State synchronization conflict resolution is easy to implement incorrectly in subtle ways; a conflict resolution policy that seems correct in most cases may produce wrong results in edge cases that are hard to test but visible to the user

---

## Long-Term End State

Distributed Presence eventually evolves toward:

- seamless conversational continuity across phone, PC, shop, vehicle, and wearables
- zero-friction endpoint transitions where the user never manages their own context
- a shop presence so capable that the environment itself feels conversationally interactive
- smart glasses integration that makes Zola a natural ambient presence without distraction
- distributed cognitive workers that monitor, analyze, and prepare continuously without consuming live conversation resources
- a Core Presence Layer robust enough to survive any individual endpoint failure without losing state

The system should ultimately feel:

- omnipresent without being intrusive
- consistent without being rigid
- seamlessly transitioned without requiring management
- more capable than any single device could be alone

without losing:

- the unified identity that makes Zola recognizably the same presence everywhere
- the centralized authority that keeps behavioral decisions in one place
- the privacy discipline that governs what each endpoint may and may not surface
- the principle that intelligence lives in the Core Presence Layer, not in the endpoints
