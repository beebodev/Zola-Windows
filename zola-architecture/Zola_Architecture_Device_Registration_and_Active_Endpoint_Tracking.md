# Device Registration and Active Endpoint Tracking

### Foundational Architecture for Distributed Presence

---

## Vision

The phrase "one mind, many bodies" only works if the mind knows which body is currently in use.

Without device registration, every endpoint is anonymous. Without active endpoint tracking, the intelligence layer has no way to know where the user is, what they are interacting through, or where output should be routed. Without a handoff protocol, switching devices means starting over — a cold restart that erases every signal of conversational continuity.

This document defines the minimum viable infrastructure for distributed presence: the layer that transforms Zola from a single-device app into a presence that knows its own endpoints, understands their capabilities, identifies which one the user is currently with, and coordinates gracefully when that changes.

This is not the full distributed presence architecture. It is the foundation that everything else in that architecture requires before it can be built. Endpoint-aware behavior, cross-device proactive routing, conversational handoff, and multi-endpoint coordination all assume this layer exists.

The system should eventually feel less like:

> "a phone app that also runs on a tablet"

and more like:

> "a presence that follows you, knows where you are, and meets you there."

---

## Core Philosophy

### Endpoints Are Surfaces, Not Identities

The intelligence is not the device. The device is a surface through which the intelligence expresses itself.

This distinction is not semantic. It is the structural principle that prevents Zola from becoming a collection of isolated per-device assistants that happen to share a Firebase account.

A registered endpoint has capabilities, a form factor, a location context, and an interaction profile. It does not have a personality, a memory, or a conversational identity. Those belong to the Core Presence Layer — which is account-scoped, device-independent, and shared across all surfaces.

The device registration system must never allow a device to behave as if it owns the intelligence. It owns a surface. The intelligence lives elsewhere.

Traditional multi-device systems:

- each device is an independent app instance
- shared data is the extent of coordination
- switching devices means re-establishing context manually
- no concept of which device is "in use" vs "available"
- output goes to whichever device generated the trigger

This system:

- devices are registered surfaces with known capabilities and states
- the active endpoint is tracked continuously
- switching devices triggers a structured handoff protocol
- the intelligence layer routes output to the right surface
- the user's experience is continuous regardless of which device they pick up

---

## Long-Term Architectural Pillars

---

## 1. Device Registration Model

### Purpose

Create a durable, cloud-backed record for every endpoint that connects to Zola's intelligence layer. Registration is the act of a device announcing itself, its capabilities, and its form factor to the shared presence layer.

### When Registration Occurs

A device registers itself at first sign-in or first launch after sign-in. Registration is idempotent — a device that registers again after reinstall should update its existing record, not create a duplicate.

Registration should be transparent to the user. It is infrastructure, not a user-facing onboarding step. The user does not "pair" devices — they simply sign in, and the device registers itself automatically.

### Registration Record Schema

Each registered device is stored as a Firestore document at:

```
users/{userId}/devices/{deviceId}
```

Where `deviceId` is a stable installation identifier generated at first launch and persisted in local storage. It must survive app restarts but should be regenerated on reinstall (treating reinstall as a new device registration).

---

**`deviceId`**
The stable installation identifier. Generated once at first launch. Not tied to hardware identifiers for privacy reasons — tied to the app installation.

**`deviceName`**
A human-readable label for this device. Initially derived from the Android device name (`Build.MODEL` or user-set device name). Editable by the user.

Examples: "Pixel 8 Pro", "Shop Tablet", "Living Room Display"

**`deviceType`**
The form-factor classification of this device.

- `PHONE` — primary mobile device; assumed to be with the user most of the time
- `TABLET` — larger screen; may be mounted or portable
- `DEDICATED_DISPLAY` — mounted shop display, wall panel, or kiosk-style endpoint
- `PC` — desktop or laptop agent (future)
- `VEHICLE` — in-vehicle integration (future)
- `WEARABLE` — watch or glasses (future)
- `UNKNOWN` — unclassified; treated conservatively

**`capabilities`**
A structured record of what this device can do.

```
capabilities: {
  hasMicrophone: boolean,
  hasSpeaker: boolean,
  hasDisplay: boolean,
  hasCamera: boolean,
  hasGps: boolean,
  hasNotifications: boolean,
  supportsTts: boolean,
  supportsLiveVoice: boolean,
  bluetoothAudio: boolean
}
```

Capabilities are reported by the device at registration and updated on capability change (e.g., a Bluetooth speaker is connected, changing `bluetoothAudio` to true).

**`interactionProfile`**
The default interaction style appropriate for this device type and context.

- `CONVERSATIONAL_FULL` — full voice interaction, long-form responses, proactive speech enabled
- `CONVERSATIONAL_BRIEF` — voice interaction, short responses preferred, mobile context
- `DISPLAY_PRIMARY` — visual output preferred; voice secondary or disabled
- `AMBIENT_MONITOR` — passive monitoring and brief voice output only; no long-form interaction
- `HANDS_FREE` — voice-primary with no screen interaction; shop or vehicle context

This profile feeds the identity and personality layer's endpoint-aware behavior adaptation.

**`preferredDampeningProfile`**
The default attention dampening profile to apply when this device is the active endpoint and workspace context cannot be determined from other signals.

- `SHOP` — high interruption cost, slow heat decay
- `DESK` — low interruption cost, fast heat decay
- `VEHICLE` — high cost, safety-constrained
- `HOME` — moderate cost
- `MOBILE` — moderate cost, user in motion

**`fcmToken`**
The Firebase Cloud Messaging token for this device. Used to deliver push coordination events when the device is not in an active session. Updated on each FCM token refresh.

**`lastSeenMs`**
Timestamp of the most recent activity from this device. Updated on every session heartbeat. Used to identify stale registrations and to determine which device is most recently active when the active endpoint cannot be determined from session state.

**`lastActiveSessionId`**
The session ID of the most recent active or completed session on this device. Used to correlate handoff events with the correct session context.

**`registeredAt`**
Timestamp of first registration.

**`appVersion`**
The app version string at registration time. Updated on app update. Used to identify capability mismatches between devices running different versions.

**`isActive`**
Boolean. Whether this device currently has an active session — meaning the user is interacting with it right now. Managed by the Active Endpoint Tracker (Section 2). Not self-reported by the device alone — requires coordination with the presence layer.

**`platform`**
The platform identifier for this device.

- `ANDROID` — current primary platform
- `IOS` — future
- `WEB` — future
- `CUSTOM` — future non-standard endpoints

---

### Registration Lifecycle

**First registration:** device generates a `deviceId`, collects capabilities, and writes the registration document to Firestore. FCM token is registered simultaneously.

**Session start:** device updates `lastSeenMs` and `lastActiveSessionId`. Active endpoint tracker is notified (Section 2).

**Capability change:** device detects a capability change (Bluetooth connected/disconnected, microphone permission granted/revoked) and updates the `capabilities` field.

**FCM token refresh:** Firebase SDK triggers a token refresh; device updates `fcmToken` in its registration document immediately.

**Reinstall:** new `deviceId` is generated. A new registration document is created. The old registration document is orphaned — stale registration cleanup (Section 4) will eventually remove it.

**Sign-out:** device marks its registration as inactive and clears its local session state. It does not delete the registration document — the user may sign back in on the same device.

---

## 2. Active Endpoint Tracker

### Purpose

Maintain a continuously updated record of which device is currently the active endpoint — the surface the user is most likely interacting through right now — and propagate that information to the systems that need it for output routing and behavioral adaptation.

### Why Active Endpoint Matters

The Attention/Relevance Engine needs to know where to route output. A proactive update that should be spoken cannot be spoken on a device the user is not near. A notification sent to the wrong device is either missed or disruptive.

The Current User State Model's workspace context inference uses device type and capabilities as signals. A shop tablet connected to a Bluetooth speaker is a very different context signal than a phone in a pocket.

The identity and personality layer's interaction profile selection depends on which device is active.

Without a reliable active endpoint, all of these systems are guessing.

### Active Endpoint Determination

The active endpoint is determined by combining multiple signals, not by a single authoritative source. No single signal is reliable enough alone.

**Signal 1 — Session heartbeat**
A device that has an open Live session or a recent STT recognition event is almost certainly the active device. The session heartbeat is the strongest active endpoint signal. Devices send a heartbeat to the presence layer every 30 seconds while a session is open.

**Signal 2 — Last user interaction**
The device from which the most recent user-initiated interaction (voice turn, touch, button press) originated. This has a short recency window — an interaction 20 minutes ago is a weaker signal than a heartbeat from 30 seconds ago.

**Signal 3 — Last seen timestamp**
The most recently active device by `lastSeenMs`. Used as a tiebreaker when heartbeat and interaction signals are equal or absent.

**Signal 4 — GPS proximity to known place**
If the Current User State Model has determined the user is at a known place that is associated with a specific device (e.g., shop tablet at the shop), that device is promoted as a candidate active endpoint even if it does not currently have an active session.

**Signal 5 — User explicit switch**
The user says "switch to the shop" or "use the tablet." Explicit intent is the highest-priority signal and should override all others immediately.

### Active Endpoint Record

The current active endpoint state is stored in Firestore at:

```
users/{userId}/presence/activeEndpoint
```

Fields:

**`activeDeviceId`**
The `deviceId` of the currently determined active endpoint.

**`activeSince`**
Timestamp when this device became the active endpoint.

**`determinationMethod`**
How the active endpoint was determined: `session_heartbeat`, `user_interaction`, `explicit_switch`, `last_seen`, `place_inference`.

**`confidence`**
Float 0.0–1.0. How confident the system is that this is the correct active endpoint. High confidence when determined by session heartbeat. Lower when determined by last-seen alone.

**`previousDeviceId`**
The `deviceId` of the prior active endpoint before this one. Used by handoff coordination to know where to pull context from.

**`candidateDevices`**
List of all registered devices that are candidates, with their individual signal scores. Retained for debugging and handoff decision-making.

### Active Endpoint Transitions

An active endpoint transition occurs when the system determines that a different device has become the active surface.

Transition triggers:

- a new session heartbeat arrives from a device that is not the current active endpoint
- a user interaction is detected on a non-active device
- the user issues an explicit switch command
- the current active device's heartbeat goes stale (no heartbeat within 90 seconds)
- the user's GPS location moves to a known place associated with a different device

Transition behavior:

1. The new active device is written to `activeEndpoint` with the determination method and confidence.
2. The handoff coordinator is notified (Section 3).
3. All output routing is updated to target the new active device.
4. The previous device receives a FCM message indicating it is no longer the active endpoint.

### No Active Endpoint State

When no device can be determined as active — all devices have stale heartbeats, no recent interactions, no location signal — the system enters a `NO_ACTIVE_ENDPOINT` state.

In this state:

- proactive speech is suppressed entirely
- deferred events continue to accumulate in the queue
- silent logging continues
- FCM notifications may still be sent to the most recently active device as a low-cost channel
- the state resolves automatically when any device resumes activity

---

## 3. Conversational Handoff Protocol

### Purpose

Define how conversational context is transferred from one device to another when the active endpoint changes, so the user's experience on the new device is continuous rather than cold.

### What Needs to Transfer

A Live session cannot be migrated. The WebSocket connection is device-specific and cannot be moved.

What can be transferred is the conversational context that was held in that session — the information that makes a new session feel like a continuation rather than a restart.

**Must transfer:**
- active conversation frame (current topic, active entities, recent query history)
- current clarification state (if awaiting a clarification response)
- active task state (if an orchestration scenario was in progress)
- recent conversation history tail (last N exchanges, sufficient to re-establish LLM context)
- current mood and emotional register signals
- any deferred events that were queued for the user

**Should transfer when available:**
- unresolved topic list
- pending follow-up items
- active project or work session context

**Does not transfer:**
- the Live session WebSocket connection
- in-flight audio playback
- UI state specific to the originating device

### Handoff Serialization Format

When a transition is detected, the outgoing device serializes its current conversational context to:

```
users/{userId}/presence/handoffContext
```

This document is ephemeral — it is written on transition and read by the incoming device during session initialization. It is not a long-term store.

Fields:

**`sourceDeviceId`**
The device that serialized this context.

**`serializedAt`**
Timestamp of serialization. Used by the receiving device to assess freshness.

**`expiresAt`**
When this handoff context is no longer useful. Suggested: 10 minutes. After this window, the context is considered stale and the incoming device should initialize a warm session from durable memory rather than a cold handoff.

**`conversationFrame`**
Serialized representation of the current `ConversationContextSnapshot` — topic, active entities, anchor, clarification state, frame strength.

**`recentHistory`**
The last N conversation turns (suggested: 10) as a list of `{ role, content, timestampMs }` objects. Sufficient to reconstruct LLM context on the receiving device without loading full history from RTDB.

**`pendingClarification`**
If the user was awaiting a clarification response, the clarification question and context. The receiving device should re-surface this naturally.

**`deferredQueuePath`**
Reference to the shared deferred event queue at `users/{userId}/presence/deferredQueue`. The incoming device reads this path directly on session start to inherit all queued events. No event migration is required — the queue is shared across devices and the new active device simply takes ownership of it.

**`activeTaskState`**
If an orchestration scenario was in progress, a serialized snapshot of the task state. Null if no active task.

**`sessionNotes`**
A brief natural language summary of the current conversational context, suitable for injecting into the system prompt of the new session to orient the LLM without requiring it to re-read full history. Generated by the outgoing device before serializing.

Example:
> "We were talking about the oil change on the Camaro. User asked about torque specs for the drain plug. Had not yet answered. User also has a 4 PM call on their calendar."

### Handoff Reception

When the incoming device becomes the active endpoint:

1. It reads `presence/handoffContext` and checks `expiresAt`.
2. If fresh: it initializes its conversational state from the serialized frame, injects `sessionNotes` into the system prompt, loads `recentHistory` into the session context, and reads the shared deferred queue at `users/{userId}/presence/deferredQueue` to inherit any pending events.
3. If stale or absent: it initializes from durable memory (Firestore structured memory + RTDB history tail) using the warm-start path rather than a cold-start path. This produces a less seamless experience but is still better than a fully cold start.
4. The device acknowledges receipt by writing a `handoffAcknowledged` timestamp to `presence/handoffContext`.
5. Zola's first response on the new device should reflect continuity naturally — not announce the handoff, but simply continue where things left off.

### Handoff Announcement Principle

The handoff should be invisible to the user unless something went wrong.

The user picks up the shop tablet and Zola simply continues. There is no "I see you've switched devices" announcement. There is no re-introduction. Context is already there.

If the handoff context was stale and a warm-start was used instead, Zola may briefly orient herself:

> "I haven't heard from you in a bit — we were talking about the Camaro earlier. Where were we?"

This is the only user-visible acknowledgment that a transition occurred, and it should only appear when the context gap is large enough that pretending continuity would be confusing.

---

## 4. Output Routing

### Purpose

Ensure that all output — spoken, notified, displayed, or logged — is directed to the correct endpoint based on the current active endpoint, the event's urgency tier, and the receiving device's capabilities.

### Routing Decision Inputs

When the Attention/Relevance Engine decides to surface an event, it passes the output to the routing layer with:

- the decided delivery channel (spoken, notification, display, log)
- the event's urgency tier
- the event's privacy sensitivity

The routing layer then determines: which device receives this output, and in what form.

### Routing Rules

**Active endpoint receives primary output.**
The active endpoint is the default target for all spoken and display output.

**Capability filtering.**
If the decided channel requires a capability the active endpoint lacks, the channel is downgraded.

Example: spoken output routed to a device with `hasSpeaker: false` → downgraded to passive notification if `hasDisplay: true`, or to silent log if neither.

**Privacy sensitivity filtering.**
If the event carries `PRIVATE` or `SENSITIVE` privacy sensitivity, and the active endpoint's context suggests others may be present (`othersPresent: true` in the state model), spoken delivery is suppressed. The event is delivered as a silent notification or held in the deferred queue.

**Urgency override routing.**
Tier 1 override events may be delivered to a non-active device if the active device lacks the capability to deliver the urgency appropriately.

Example: the active endpoint is a shop display with no notification capability, and a tier 1 security event fires. The event is also sent to the user's phone via FCM as a high-priority push notification.

**No-active-endpoint fallback.**
When `NO_ACTIVE_ENDPOINT` is the current state, spoken output is suppressed. FCM notifications may be sent to the most recently active device for tier 2 and above events.

### Multi-Device Notification

For events where notifying the active endpoint alone is insufficient — tier 1 events, time-sensitive events where the user may not be watching the active display — the routing layer may send an FCM notification to one or more additional registered devices as a secondary delivery path.

This is not the same as broadcasting to all devices. It is a targeted secondary delivery decision made per-event based on urgency and context.

---

## 5. FCM Coordination Layer

### Purpose

Provide the push channel for cross-device coordination events and secondary notification delivery. FCM is the mechanism by which devices signal each other and receive presence updates when not in an active session.

### FCM Message Types

All FCM messages to Zola endpoints use a structured data payload (not notification payloads, which are OS-rendered and cannot be fully controlled). The app processes FCM messages on receipt and takes appropriate action.

**`HANDOFF_CONTEXT_AVAILABLE`**
Sent to the incoming device when handoff context has been serialized and is ready to read.

Payload:
```
{
  type: "HANDOFF_CONTEXT_AVAILABLE",
  sourceDeviceId: string,
  serializedAt: timestamp,
  expiresAt: timestamp
}
```

**`ACTIVE_ENDPOINT_CHANGED`**
Sent to all registered devices when the active endpoint changes. Allows non-active devices to suspend background activity and adjust behavior accordingly.

Payload:
```
{
  type: "ACTIVE_ENDPOINT_CHANGED",
  newActiveDeviceId: string,
  previousDeviceId: string,
  determinationMethod: string
}
```

**`DEFERRED_EVENT_AVAILABLE`**
Sent to the active device when a deferred event in the queue has reached a priority threshold that warrants delivery. Used when the event was queued on a different device.

Payload:
```
{
  type: "DEFERRED_EVENT_AVAILABLE",
  eventId: string,
  urgencyTier: string
}
```

**`PRESENCE_HEARTBEAT_REQUEST`**
Sent from the presence layer to a device that has gone quiet, requesting a heartbeat response to confirm whether the device is still active.

Payload:
```
{
  type: "PRESENCE_HEARTBEAT_REQUEST",
  requestedAt: timestamp
}
```

**`SESSION_INVALIDATED`**
Sent to a device whose session has been superseded by a new active endpoint. The device should gracefully wind down its active session without producing any further output.

Payload:
```
{
  type: "SESSION_INVALIDATED",
  newActiveDeviceId: string
}
```

### FCM Token Management

FCM tokens must be kept current for coordination to work.

- tokens are registered at device registration
- tokens are updated immediately on Firebase SDK token refresh
- stale tokens (registration updated but no FCM delivery success in 30 days) trigger a token refresh request
- sign-out clears the FCM token from the registration document

---

## 6. Stale Registration Cleanup

### Purpose

Prevent the device registry from accumulating orphaned registrations from old installations, test devices, or devices the user no longer uses.

### Staleness Definition

A registration is considered stale when:
- `lastSeenMs` is older than 90 days, AND
- the FCM token has not been successfully contacted in 30 days, AND
- the device is not the current active endpoint

### Cleanup Behavior

Stale registrations are not deleted immediately. They are:

1. Marked with a `staleAt` timestamp.
2. Excluded from active endpoint determination.
3. Excluded from output routing.
4. Removed from the registry after a 30-day grace period, during which reinstalling the app on that device will revive the registration.

Cleanup runs as a background operation triggered by the presence layer on session start and on a periodic schedule.

The user may also view and manually remove device registrations from a device management surface (future).

---

## 7. Conflict Resolution for Concurrent Device Writes

### Purpose

Define how write conflicts are handled when two devices attempt to write to shared Firestore state simultaneously.

### Write Categories and Conflict Approach

Not all writes carry the same conflict risk. Different write categories require different conflict strategies.

**Conversation history (RTDB `push()`):**
No conflict. Each entry is an independent document with a unique auto-key. Two devices writing simultaneously produce interleaved entries, which is acceptable. Ordering is by timestamp. No change required.

**Active endpoint document:**
Highest conflict risk. Two devices may simultaneously attempt to claim the active endpoint. Resolution: use Firestore transactions with optimistic locking. The device that wins the transaction becomes active. The losing device receives `SESSION_INVALIDATED` via FCM and yields.

**Handoff context document:**
Written only by the outgoing device, read only by the incoming device. No concurrent write risk by design — only one device is outgoing at any given transition.

**Durable memory (Firestore entity/profile documents):**
Medium conflict risk. Two devices running memory workers may write simultaneously. Resolution: use last-modified timestamp comparison. Each write includes a `lastModifiedMs` field. A write is rejected if the document's current `lastModifiedMs` is newer than the value the writing device read. On rejection, the writer re-reads and merges locally before retrying. This is optimistic concurrency control without Firestore transactions, which avoids transaction overhead on high-frequency memory writes.

The active-endpoint transaction/optimistic-locking approach and the durable-memory `lastModifiedMs` comparison are applications of the canonical transaction-and-precondition pattern now defined in `Zola_Firestore_Write_Safety_Architecture.md` (Pattern A), which should be treated as the reference going forward.

**Shared deferred event queue (`presence/deferredQueue`):**
The active device owns and drains the queue. Only the active device should be writing to or removing from this queue at any given time — ownership transfers with the active endpoint transition. The outgoing device stops writing to the queue when it receives `SESSION_INVALIDATED`. The incoming device begins managing the queue after it reads the handoff context. Concurrent write risk is low by design because only one device holds the active endpoint at a time, but the active endpoint document's Firestore transaction (above) must resolve before queue ownership transfers.

**CurrentHeat (dampening system):**
Per-device. Heat is a property of recent output on a specific device, not shared state. Each device maintains its own `CurrentHeat` in its local dampening system, backed by a device-scoped Firestore path:
```
users/{userId}/devices/{deviceId}/dampeningState
```
No cross-device conflict because heat is not shared. Cross-device coordination of heat is not needed — if the user switches devices, the new device's heat starts from its own recent history, which is the correct behavior.

**User profile and preferences:**
Low write frequency. Resolution: last-writer-wins is acceptable for most preference fields. For fields where loss of an update would be user-visible (e.g., a preference the user just explicitly changed), the writing device should include the `lastModifiedMs` check before writing.

---

## Core Architectural Principles

---

### Registration Is Infrastructure, Not Onboarding

The user should never have to think about device registration. It happens automatically at first sign-in. It updates automatically as capabilities change. The device management surface (viewing and removing registrations) is available but not required.

Making registration a user-facing step creates friction and introduces the possibility of the user skipping it, leaving the presence layer without accurate device information.

---

### Active Endpoint Is a System Determination, Not a User Setting

The system determines which device is active from signals — heartbeat, interaction, location, explicit command. It is not a persistent user preference that the user configures once and forgets.

This matters because the active endpoint changes continuously. A user who had their phone as the active endpoint this morning may have their shop tablet as the active endpoint this afternoon. That transition should happen automatically, not require the user to go into settings and switch.

The user can issue an explicit switch command when the automatic determination is wrong. But the system should be right often enough that explicit switches are the exception.

---

### Handoff Must Be Invisible When Successful

A successful handoff should produce no user-visible artifact. The user picks up a different device and the conversation is already there.

Any announcement of the handoff — "I see you've switched to the shop tablet" — is a signal that the handoff either failed or the context gap was too large to bridge seamlessly. Announcements are a fallback, not a feature.

---

### Devices Yield, They Do Not Compete

When the active endpoint changes, the outgoing device yields cleanly. It serializes its context, suspends its output, and stops competing for the user's attention. It does not continue producing output on the assumption that the user might come back.

This is enforced by the `SESSION_INVALIDATED` FCM message and the protocol that the outgoing device must honor it promptly.

---

### Output Routing Is Centralized

The Attention/Relevance Engine decides what to surface. The routing layer decides where to surface it. These are distinct responsibilities.

No worker, monitor, or subsystem decides independently which device receives its output. All routing decisions flow through the routing layer, which reads the active endpoint record and applies capability and privacy filters before delivery.

---

## Integration Points

This document connects directly to:

- Attention/Relevance Engine — the routing layer is a downstream executor of engine decisions; the engine passes channel decisions to routing, which resolves the target device
- Environmental Event Bus — events on the bus carry no device target; routing is determined at delivery time by the routing layer
- Current User State Model — the state model's workspace context and device state fields are informed by device registration capabilities and Bluetooth device type; the state model reads the active endpoint record to determine which device's signals are most relevant
- Conversational State and Momentum Layer — handoff context serialization depends on the conversational state layer producing a serializable frame snapshot; this document is a consumer of the state serialization design from Domain 3
- Attention Dampening System — `CurrentHeat` is device-scoped; each device maintains its own dampening state; the dampening system reads device registration to determine the appropriate dampening profile
- Trust, Permission, and Privacy Framework — privacy sensitivity on events is evaluated by the routing layer against the active endpoint's context; the framework defines which capabilities require explicit permission
- Identity and Personality Layer — `interactionProfile` from the device registration feeds the persona's endpoint-aware behavior selection

---

## Failure Modes and Safeguards

### Active Endpoint Stuck on Wrong Device

Risk: the system determines the wrong device is active and routes output there, where the user cannot receive it.

Safeguards:
- heartbeat staleness detection (90-second window) ensures a device that has gone silent is eventually demoted
- user explicit switch command provides an immediate escape hatch
- FCM delivery failure on the presumed active device triggers a fallback routing attempt to other registered devices
- the `NO_ACTIVE_ENDPOINT` state prevents output from going nowhere silently — it suppresses speech rather than routing to a wrong device

### Handoff Context Race

Risk: a new session starts on the incoming device before the outgoing device has finished serializing the handoff context, resulting in the incoming device initializing from stale or absent context.

Safeguards:
- the incoming device waits for `HANDOFF_CONTEXT_AVAILABLE` FCM message before reading handoff context, with a configurable timeout
- if the timeout expires, the device falls through to warm-start from durable memory rather than blocking
- `serializedAt` and `expiresAt` on the handoff document allow the receiving device to assess freshness before using

### FCM Token Stale or Invalid

Risk: the FCM token for a device is stale, causing coordination messages to fail silently.

Safeguards:
- FCM delivery failure should trigger a token refresh request on the next available channel
- the active endpoint determination falls back to `lastSeenMs` when FCM coordination fails
- devices refresh their FCM token proactively on each app startup

### Device Registry Bloat

Risk: the registry accumulates many stale registrations from old devices, test installations, or frequent reinstalls, creating noise in active endpoint determination.

Safeguards:
- stale registration definition and cleanup process (Section 6)
- active endpoint determination explicitly excludes registrations marked stale
- user-facing device management surface allows manual cleanup

### Concurrent Active Endpoint Claims

Risk: two devices simultaneously attempt to become the active endpoint, creating a conflict in the `activeEndpoint` document.

Safeguards:
- Firestore transaction with optimistic locking on the `activeEndpoint` document
- the losing device receives `SESSION_INVALIDATED` and yields
- tie-breaking favors the device with the more recent user interaction signal

---

## Roadmap Considerations

> Note: Implementation phases and sequencing will be defined in coordination with the build planning process. This section captures architectural intent only.

### Dependencies

- Firebase Auth must be in place before device registration can use `userId` as the registry root — this exists today
- FCM SDK must be integrated before the coordination layer can function — this does not currently exist in the codebase
- The Attention/Relevance Engine must exist before output routing has meaningful decisions to execute
- The Conversational State and Momentum Layer must define its serialization format before handoff context can be written — this is a joint design dependency with Domain 3
- The Current User State Model must be operational before GPS-based known-place signals can contribute to active endpoint determination

### Open Questions

- What is the right heartbeat interval? 30 seconds is suggested but may be too aggressive for battery on devices that are nominally active but not being actively used.
- How should the system handle a scenario where the user is genuinely using two devices simultaneously — phone in hand, shop tablet visible? Should both be considered active, or should one yield?
- Should `CurrentHeat` be shared across devices in any way — for example, should a proactive update delivered to the phone affect the heat level on the shop tablet? The current design says no — heat is per-device. This should be confirmed as correct.
- **Resolved:** The deferred event queue is shared across devices, not per-device. It lives at `users/{userId}/presence/deferredQueue` as a collection of full structured event documents. The active device owns and drains the queue. When the active endpoint changes, the new device takes ownership of the same queue — no migration required, no id-only lookups, no events lost in transition. This produces a smoother user experience (queued events surface on whichever device the user is currently with) and reduces per-device overhead (one queue, one expiry model, one summary batch). The `deferredEventIds` field in the handoff context document is therefore unnecessary and should be omitted — the incoming device reads the shared queue directly on session start.
- How should the backend scope be defined for non-Android endpoints? This document assumes Android-only for now, but the registration schema should be forward-compatible with future platforms.

### Architectural Risks

- FCM reliability is not guaranteed, especially on Android devices with aggressive battery optimization. Coordination messages may be delayed or dropped. All critical coordination paths must have a fallback that does not depend on FCM delivery succeeding.
- The handoff protocol assumes the outgoing device is capable of serializing context before the incoming device needs it. In practice, the outgoing device may be powered off, have lost connectivity, or have crashed. The incoming device must handle absent handoff context gracefully without blocking session start.
- Active endpoint determination from signal aggregation will have edge cases where the system is confidently wrong. The user experience in these cases — output going to the wrong device — must be recoverable quickly without requiring the user to understand the underlying system.

---

## Long-Term End State

The Device Registration and Active Endpoint Tracking system eventually evolves toward:

- a fully populated device registry covering phone, shop display, PC, vehicle, and wearable endpoints
- active endpoint determination that is reliably accurate across all transition scenarios
- handoff protocol that makes device switching feel instantaneous and invisible
- output routing that selects not just the right device but the right channel and format for that device
- conflict resolution that handles all concurrent write scenarios without data loss
- a user-facing device management surface that is simple enough that most users never need it

The system should ultimately feel:

- invisible when working correctly
- continuous across device transitions
- appropriately context-aware per endpoint
- reliable enough that the user stops thinking about which device they are on

without losing:

- the principle that the intelligence is not the device
- privacy discipline in output routing
- the user's ability to override automatic determinations
- graceful degradation when signals are absent or unreliable
