# Privacy and Data Ownership Plan

### Foundational Architecture for Trustworthy Data Stewardship

---

## Vision

Zola is a deeply personal system. Over time she will accumulate schedules, behavioral patterns, relationships, emotional context, routines, location history, communication summaries, environmental activity history, security camera-derived events, and knowledge of the people and vehicles in the user's life.

This depth of personal knowledge is what makes Zola genuinely useful. It is also what makes the privacy architecture foundational — not optional, not a compliance checkbox, and not something that can be retrofitted after the system is built.

The goal is not to minimize what Zola knows. The goal is to ensure that everything she knows is held with the care, transparency, and user control that a system this personal demands.

The system should eventually feel less like:

> "a product that collects data about me"

and more like:

> "a presence that holds what I've shared in trust, uses it to help me, and gives me full control over what it keeps."

---

## Core Philosophy

### Privacy Is Architectural, Not Cosmetic

Traditional privacy implementations:

- apply privacy controls at the display layer after data is already collected
- treat consent as a one-time agreement at setup
- store everything by default and restrict access after the fact
- handle deletion requests incompletely, leaving copies in secondary stores

This system:

- enforces privacy at the collection layer, the write layer, the retrieval layer, and the output layer
- treats consent as a per-category, per-capability decision that can be changed at any time
- requires justification for collection — data that serves no purpose is not collected
- treats deletion as a cascade that must complete across all layers before it is considered done

Privacy is enforced by architecture. It is not described by policy and hoped for.

Traditional systems:

- collect broadly and restrict narrowly
- make consent binary and permanent
- treat privacy as a legal requirement
- handle deletion as best-effort

This system:

- collects purposefully and retains deliberately
- makes consent granular and revocable
- treats privacy as a trust relationship
- treats deletion as a guarantee, not a promise

---

## Long-Term Architectural Pillars

---

## 1. Data Category Inventory

### Purpose

Enumerate every category of data that Zola collects, generates, or retains — organized by sensitivity level — so that consent, retention, deletion, and processing rules can be defined precisely for each category.

### Tier 1 — Highest Sensitivity

These categories require explicit, separately granted consent before any collection or retention begins. They must be disabled by default.

**Facial and person recognition data** — the ability to identify specific individuals from camera feeds. This is the highest-sensitivity capability in the system. It requires explicit consent, may not be inferred from other permissions, and must be immediately disableable.

**Voice biometric data** — data that could be used to identify individuals by their voice. Distinct from voice transcripts — this is the biometric fingerprint, not the content.

**Health and biometric data** — data from wearables or health integrations including heart rate, activity levels, sleep patterns, and similar signals.

**Security camera-derived events with person identity** — structured events that associate a detected person with a known identity. The detection itself (motion, presence) is lower sensitivity; the identity association elevates it to Tier 1.

**Financial information** — any data related to accounts, transactions, or financial status that may be surfaced through integrations.

**Precise location history** — a timestamped record of the user's physical locations over time. Distinct from current location (used for context) and geofenced zones (used for awareness) — this is the historical log.

### Tier 2 — High Sensitivity

These categories are collected by default when the relevant feature is active, but require informed disclosure and must be individually revocable.

**Communication content** — the content of messages, emails, and calls that Zola accesses for summarization or priority detection. Sender identity and metadata are lower sensitivity than content.

**Episodic memory** — summarized records of meaningful conversations, personal stories, and emotionally significant exchanges.

**Relationship data** — structured records of who the user knows, how they relate to the user, and interaction patterns over time.

**Behavioral and preference patterns** — the Style Profile and associated interaction history that shapes how Zola communicates.

**Calendar content** — the details of scheduled events, not just the existence of calendar blocks.

**Environmental activity history** — records of what was detected in monitored zones over time, even without person identity association.

**Household patterns** — routines, occupancy patterns, and activity rhythms inferred from environmental signals.

### Tier 3 — Standard Sensitivity

These categories are collected as part of normal system operation. They are disclosed in system documentation and are subject to standard retention and deletion rules.

**Structured canonical facts** — durable facts about the user, their family, vehicles, projects, and relationships that the user has explicitly confirmed.

**Session and conversational memory** — the active topic, recent turns, and current task state that supports conversational continuity within and across sessions.

**Current location** — used for contextual awareness during active sessions. Not retained as a historical log unless explicitly enabled.

**Device state signals** — active call detection, Bluetooth connections, do-not-disturb status, and similar device context signals used for availability modeling.

**Environmental detection events without identity** — motion detection, package detection, vehicle presence without identity association.

**Weather and traffic context** — used for proactive assistance. Not retained beyond the active session.

### Tier 4 — Operational Data

These categories are required for system operation and are retained for operational purposes with defined windows.

**Interaction logs** — records of what Zola said and did, retained for observability, debugging, and audit purposes.

**Attention and routing decisions** — logs of how inputs were processed, which prove system behavior for debugging.

**Error and failure logs** — records of system failures used for reliability improvement.

**Anonymized usage patterns** — aggregate, non-identifying data about feature usage, if applicable.

### Important Principle

Every category of data Zola holds must have a defined purpose, a defined retention window, a defined deletion path, and a defined consent tier. Data without a defined purpose must not be collected.

---

## 2. Consent Architecture

### Purpose

Define a granular, revocable consent model that gives the user genuine control over what Zola collects and retains — without making consent so burdensome that it defeats the purpose of the system.

### Consent Tiers

**Tier 1 — Explicit opt-in required, off by default**

These features do not activate until the user explicitly enables them through a deliberate action — not buried in an onboarding flow, not pre-checked.

Applies to: facial and person recognition, voice biometrics, health data integration, precise location history retention, financial data integration, vehicle license plate recognition.

**Tier 2 — Informed default-on with individual revocation**

These features are active by default when the relevant capability is enabled, but the user is clearly informed of what is collected and can disable each category individually.

Applies to: communication content access, episodic memory, relationship data, behavioral preference learning, calendar content access, environmental activity history.

**Tier 3 — Standard operational with disclosure**

These features are active as part of normal system operation. They are disclosed in system documentation and subject to standard retention rules. Individual revocation is supported but may reduce system functionality.

Applies to: structured canonical facts, session memory, current location for context, device state signals, environmental detection without identity.

**Tier 4 — Operational requirements**

These are required for the system to function safely and reliably. They cannot be disabled without disabling the system. Retention windows are defined and enforced.

Applies to: interaction logs, routing decision logs, error logs.

### Consent Rules

- consent for Tier 1 features must be obtained through a separate, deliberate action — not bundled with general terms of service acceptance
- consent is per-category — enabling one Tier 1 feature does not imply consent for others
- consent is revocable at any time — revoking consent must trigger deletion of all data in that category
- consent must be re-obtained if the purpose or scope of a data category changes materially
- children and household members who did not consent must not have their data retained in identifiable form
- Zola must never acquire effective consent through repeated prompting, default behavior normalization, or making revocation unnecessarily difficult

### Important Principle

Consent is not a moment — it is an ongoing relationship. The user must be able to understand what they have consented to, change their mind at any time, and trust that revocation is complete.

---

## 3. Retention Policies

### Purpose

Define how long each data category is retained so that Zola holds information for exactly as long as it serves the user — and no longer.

### Retention Rules by Category

**Tier 1 — Highest Sensitivity**

| Category | Default Retention | Maximum Retention |
|---|---|---|
| Facial and person recognition data | Session only unless explicitly extended | User-defined, renewable |
| Voice biometric data | Not retained by default | User-defined with explicit consent |
| Health and biometric data | Current session for context | User-defined with explicit consent |
| Security camera events with identity | 24 hours unless user saves | User-defined maximum |
| Financial information | Not retained | Not applicable |
| Precise location history | Not retained by default | User-defined with explicit consent |

**Tier 2 — High Sensitivity**

| Category | Default Retention | Maximum Retention |
|---|---|---|
| Communication content | Not retained; processed transiently | Not retained without explicit consent |
| Episodic memory | Indefinite with decay | Indefinite; user-deletable at record level |
| Relationship data | Indefinite | Indefinite; user-deletable at record level |
| Behavioral preferences | Indefinite with decay | Indefinite; user-resetable |
| Calendar content | Not retained; accessed transiently | Not retained without explicit consent |
| Environmental activity history | 30 days rolling | User-defined |
| Household patterns | Indefinite with decay | Indefinite; user-deletable |

**Tier 3 — Standard Sensitivity**

| Category | Default Retention | Maximum Retention |
|---|---|---|
| Structured canonical facts | Indefinite | Indefinite; user-correctable and deletable |
| Session memory | Duration of session plus 24 hours | 7 days |
| Current location | Not retained; used transiently | Not retained |
| Device state signals | Not retained; used transiently | Not retained |
| Environmental detection without identity | 7 days | 30 days |
| Weather and traffic context | Not retained | Not retained |

**Tier 4 — Operational Data**

| Category | Default Retention | Maximum Retention |
|---|---|---|
| Interaction logs | 90 days | 1 year |
| Routing decision logs | 30 days | 90 days |
| Error and failure logs | 30 days | 90 days |

### Retention Enforcement Rules

- retention windows must be enforced automatically — data must not persist beyond its retention window without an active user extension
- retention windows run from the last meaningful update to a record, not from the original creation date
- records with active unresolved references (e.g., an episodic memory that is part of an active topic thread) may have their window extended until the reference is resolved
- retention extension must be logged and attributable to a specific system decision

### Important Principle

Retention is not storage. Retention is a commitment that data serves the user for exactly as long as it should — and that when the window closes, the data is actually gone.

---

## 4. Deletion and Forget Architecture

### Purpose

Define how deletion works across all memory layers, all endpoints, and all data categories so that when the user asks Zola to forget something, it is actually forgotten — not demoted, not masked, and not left in a secondary store.

### Deletion Types

**User-initiated record deletion** — the user explicitly requests deletion of a specific memory, event, or data record.

**Category-level deletion** — the user revokes consent for a data category, triggering deletion of all records in that category.

**Retention expiration deletion** — a retention window expires and the record is deleted automatically.

**Full account deletion** — the user deletes their account or data profile, triggering deletion of all retained data across all categories.

### Deletion Cascade Requirements

Deletion must cascade completely. A deletion request is not complete until:

1. the record is removed from its primary storage location
2. all secondary copies across all memory layers are removed (Layer 0 through Layer 6)
3. all endpoint caches that may hold a copy are cleared
4. all derived records that were generated from the deleted source are evaluated — those whose primary evidence was the deleted record must also be deleted
5. all index and search entries pointing to the deleted record are removed
6. a deletion confirmation is written to the audit log with the record identifier, deletion type, timestamp, and cascade completion status

A deletion that completes in the primary store but misses a secondary layer is not complete. The record will reappear, which is a trust violation.

### Forget Request Handling

When the user says something equivalent to "forget that" or "don't remember that":

1. identify the target memory or data category
2. confirm the scope with the user if ambiguous (this specific fact, this conversation, this topic area)
3. initiate the full deletion cascade
4. confirm completion to the user
5. log the forget request and cascade result

Forget requests must be treated with the same authority as the user's explicit instructions. They may not be deferred, queued, or partially applied.

### Ghost Memory Prevention

A ghost memory is a deleted record that reappears because deletion was incomplete. Ghost memories are a trust violation and must be architecturally prevented:

- deletion must be atomic across all layers — partial deletions must roll back and retry
- the Memory Hierarchy must maintain a deletion log that subsequent recall operations check before returning results
- any recall attempt for a record in the deletion log must return nothing
- the deletion log must persist for a defined window after the deletion to catch delayed cache invalidations

### Important Principle

Forget means gone. Not demoted, not suppressed, not archived. When the user asks Zola to forget something, the only acceptable outcome is that it no longer exists in any layer, any cache, or any derived record.

> **Windows Track (`C8`):** For Zola-Windows, "forget" is currently
> scoped to MEMORY.md only, matching Hermes's default behavior —
> `state.db` (raw session transcripts) is not part of the deletion
> cascade described above. This is a known, accepted gap against the
> guarantee above for v1, not a silent omission — it should be stated
> explicitly wherever the product documents what "forget" does. See
> `zola-architecture/lore/DESIGN_DECISIONS.md`.

---

## 5. Local Versus Cloud Processing

### Purpose

Define which processing must stay on-device, which can go to cloud services, and which requires a user choice — so that the system's processing model is transparent and the most sensitive processing stays closest to the user.

### Processing Classification

**Must remain local (no cloud transmission):**

- facial and person recognition processing when enabled
- voice biometric processing if implemented
- real-time security camera analysis
- health and biometric signal processing
- content of messages and emails during summarization processing — only summaries or metadata may be transmitted, never raw content
- any data the user has explicitly designated as local-only

**May use cloud processing with disclosure:**

- speech-to-text transcription (current: Deepgram)
- language model reasoning (current: Gemini)
- conversational voice synthesis (current: Gemini Live API)
- weather, traffic, and mapping data
- calendar and messaging metadata (not content)

**Requires user choice (hybrid options):**

- episodic memory storage — local-first option must be available
- structured canonical memory — local-first option must be available
- behavioral preference data — local-first option must be available
- environmental activity history — user selects local or cloud

### Data Minimization Rules for Cloud Processing

When data must be transmitted to cloud services:

- transmit the minimum necessary for the task — do not send full context when a summary suffices
- strip identifying information where the task can be completed without it
- do not transmit Tier 1 data to cloud services under any circumstances
- do not transmit raw communication content — process locally, transmit only summaries or intent signals
- treat third-party API responses as untrusted and validate before using

### Local-First Memory Option

Zola must support a local-first memory mode in which all personal memory — episodic, canonical, behavioral — is stored on the user's primary device rather than in cloud infrastructure. This mode:

- may reduce functionality (cross-device sync requires either cloud storage or direct device-to-device sync)
- must be supported as a first-class option, not a degraded fallback
- must be clearly explained to the user in terms of the tradeoffs

### Important Principle

The closer sensitive processing stays to the user's device, the less exposure there is to third-party data handling. Local processing is the default preference for sensitive categories. Cloud processing is used when local processing is not feasible or when the user explicitly prefers it.

---

## 6. User-Facing Controls

### Purpose

Define what the user can see, understand, adjust, and delete about Zola's data holdings — ensuring that the system is transparent and that user control is genuine rather than nominal.

### Required User-Facing Capabilities

**Data inventory view** — the user must be able to see a summary of what categories of data Zola currently holds about them, organized by sensitivity tier. Not a raw data dump — a comprehensible summary.

**Memory browser** — the user must be able to browse episodic memories, structured canonical facts, and behavioral preferences individually. Each record must be viewable and deletable.

**Consent management** — the user must be able to see all current consent settings, understand what each one enables, and change or revoke any of them from a single location.

**Forget controls** — the user must be able to request deletion of specific memories, data categories, or all data from within the primary interface. Deletion must not require contacting support.

**Monitoring controls** — the user must be able to see which sensors and cameras are currently active, which zones are being monitored, and disable monitoring for specific zones or sources.

**Retention window visibility** — the user must be able to see how long specific data categories will be retained and, where supported, adjust the window.

**Processing location visibility** — the user must be able to see whether their data is being processed locally or transmitted to cloud services, and for which capabilities.

**Audit log access** — the user must be able to request a summary of significant data events — what was written, what was deleted, what was transmitted to cloud services — for a defined recent period.

### Explanation Requirements

For any data-related decision Zola makes — storing a memory, surfacing a past event, transmitting data to a cloud service — the system must be able to explain:

- what data was involved
- why it was used or stored
- where it is held
- how long it will be kept
- how the user can change or delete it

The explanation does not need to be surfaced proactively for every operation — but it must be available on request.

### Important Principle

User control is not a UI feature. It is a behavioral commitment. The controls must work completely, must be discoverable, and must produce immediate and verifiable results.

---

## 7. Third-Party Data Boundaries

### Purpose

Define what data may leave Zola's data boundary into third-party services, under what conditions, and with what limitations — ensuring that Zola's role as data steward does not enable third-party data aggregation.

### Third-Party Service Categories

**Speech processing providers** (current: Deepgram)
- what may be transmitted: audio captured for transcription
- what must not be transmitted: audio from ambient monitoring, audio captured during clearly private conversations
- retention limit: providers must not retain audio beyond the transcription task
- contractual requirement: data processing agreements required

**Language model providers** (current: Gemini, future: others)
- what may be transmitted: the minimum context needed to generate a response
- what must not be transmitted: Tier 1 data, raw communication content, data the user has designated local-only
- context minimization: prompts must be constructed to include only what is necessary — not full memory dumps
- retention limit: providers must not retain prompts or responses for training without explicit separate consent

**Voice synthesis providers** (current: Gemini Live API, future: ElevenLabs, Cartesia, others)
- what may be transmitted: the text to be spoken
- what must not be transmitted: identifying information about who the text is for or what the underlying user data was

**Mapping and traffic providers** (Google Maps Platform)
- what may be transmitted: location information needed for the query
- what must not be transmitted: precise location history or routine patterns

**Calendar and communication providers** (Google Calendar, Gmail)
- what may be transmitted: queries and updates as authorized by the user through OAuth or equivalent
- what must not be transmitted: content beyond what the specific task requires

### Data Processing Agreement Requirements

Any third-party service that receives personal data must operate under a data processing agreement that includes:

- a prohibition on using received data for purposes beyond the contracted service
- a prohibition on selling or sharing received data with other parties
- a defined retention limit for data received
- a data breach notification requirement
- audit rights

### Provider Abstraction and Replaceability

The provider abstraction philosophy defined in the master plan — keeping providers replaceable — has a privacy dimension: Zola must not build functionality that depends on a specific provider's data retention or data sharing in order to work. If a provider is replaced, no user data should be stranded with the old provider.

### Important Principle

Zola is the user's agent, not a data broker. Data the user shares with Zola does not implicitly become data shared with every third party Zola uses. Third-party data transmission must be minimal, purposeful, and governed.

---

## 8. Sensitive Capability Governance

### Purpose

Define the governance rules for the highest-risk capabilities in the system — those that, if misused, would cause the most serious harm to user trust and privacy.

### Security Camera and Person Recognition

This is the highest-risk capability combination in the system.

Rules:
- camera monitoring requires explicit user consent before activation
- person recognition requires separate, additional explicit consent beyond camera monitoring consent
- person recognition must be disabled by default and must not activate through any implicit signal
- recognized person data must not be retained beyond the defined retention window without user extension
- zone exclusions must be enforced at the signal ingestion level — data from excluded zones must never enter the pipeline
- security camera event data must not be transmitted to cloud services for analysis — analysis must occur locally or on a trusted local device

### Always-On Listening

Always-on listening — continuous microphone monitoring without a wake word — is the second-highest-risk capability.

Rules:
- must require explicit opt-in separate from wake-word-based activation
- must have a clear, user-visible indicator when active
- ambient speech captured during always-on listening must not be stored as memory
- the user must be able to disable always-on listening without disabling the entire system
- explicit wake-word activation must always remain available as an alternative

### Household and Multi-Person Environments

When multiple people are present in the environment:

- data about people other than the primary user must be handled with elevated restraint
- household members who have not consented to data collection must not have identifying information retained
- guests and visitors must not be enrolled in person recognition without their explicit consent
- conversations involving non-consenting parties must not be retained as episodic memory

### Autonomous Actions

When Zola takes autonomous actions — sending messages, creating calendar events, executing reminders — without direct user initiation:

- the action must be within the explicitly authorized scope of autonomous behavior
- the action must be logged with full context
- irreversible actions must require confirmation before execution unless the user has explicitly pre-authorized them
- the user must be able to review and reverse autonomous actions

### Important Principle

The capabilities with the highest privacy risk require the most explicit consent, the most conservative defaults, and the most careful governance. Risk scales with intimacy and irreversibility.

---

## 9. Encryption and Storage Security

### Purpose

Define the minimum security requirements for data at rest and in transit so that Zola's data holdings are protected against unauthorized access.

### Encryption Requirements

**Data in transit:**
- all data transmitted between the device and any cloud service must use TLS 1.2 or higher
- all data transmitted between endpoints within the Distributed Presence Architecture must be encrypted in transit

**Data at rest:**
- all personal data stored on-device must be encrypted using platform-standard encryption at minimum
- Tier 1 and Tier 2 data stored in cloud infrastructure must use encryption at rest with user-controlled key options where feasible
- encryption keys must not be held by the same service that holds the encrypted data

**Memory-specific requirements:**
- structured canonical memory must be encrypted at rest
- episodic memory must be encrypted at rest
- behavioral preference data must be encrypted at rest
- security camera-derived events must be encrypted at rest

> **Windows Track (`H2`, `H4`, `C4`):** For Zola-Windows, BitLocker-at-
> rest is accepted as satisfying both the general "platform-standard
> encryption at minimum" requirement above and this memory-specific
> "encrypted at rest" bullet — no application-level encryption (e.g.
> SQLCipher) added for now (`H4`). No separate Windows Credential
> Manager/DPAPI wrapping for secrets either; BitLocker is treated as
> sufficient for a single-user machine (`H2`). This applies equally to
> the extended MEMORY.md store Zola-Windows builds on top of Hermes's
> own schema (`C4`) — the extension doesn't carry a stricter
> encryption requirement than the base store. All of this is deferred
> pending any future public or multi-user distribution — see
> `zola-architecture/lore/DESIGN_DECISIONS.md`.

### Access Control

- memory write access must be gated by Durable Write Authority — not accessible directly
- Tier 1 and Tier 2 data must not be accessible to third-party integrations without explicit separate authorization
- authentication must be required before any user-facing data management capability is accessible

### Important Principle

Encryption and access control are the floor, not the ceiling. A system that encrypts data but transmits it unnecessarily or retains it beyond its window has not solved the privacy problem.

---

## Core Architectural Principles

---

### Privacy Is Enforced by Architecture

Privacy controls are enforced at the collection layer, the write layer, the retrieval layer, and the output layer. A privacy rule that only exists at the display layer can always be bypassed. Architecture-level enforcement cannot be accidentally bypassed.

---

### Data Has Purpose or It Is Not Collected

Every category of data Zola holds must serve a defined purpose that benefits the user. Data collected for speculative future use, for system improvement without user consent, or because collection is convenient rather than necessary is not collected.

---

### Consent Is Granular, Informed, and Revocable

Consent is not binary. It is per-category, per-capability, and per-purpose. It is always revocable. Revoking consent must trigger deletion. Consent obtained through friction, default, or normalization is not valid consent.

---

### Deletion Is a Guarantee

When the user asks Zola to forget something, it is deleted. Not suppressed, not demoted, not archived. The deletion cascades across all layers, all caches, and all derived records. The result is confirmed and logged.

---

### Zola Is a Steward, Not an Owner

The data in Zola's memory belongs to the user. Zola holds it in trust to help the user. It is not an asset to be retained, analyzed for system improvement, or shared with third parties beyond what is required to deliver the service the user has authorized.

---

## Integration Points

This document connects directly to:

- Zola Master Architecture Plan (Privacy and Trust Architecture section)
- Memory Hierarchy Architecture (all six layers, Durable Write Authority, forget request handling)
- Environmental Perception Architecture (Privacy, Trust, and Permission Layer)
- Environmental Awareness Architecture (privacy and trust boundaries)
- Conversational Attention Architecture (sensitive domain handling, no ambient durable writes)
- Autonomous Behavior Architecture (autonomous action safeguards)
- Identity and Personality Framework (locked privacy trait, Style Profile data)
- Distributed Presence Architecture (endpoint privacy rules, cloud versus local processing)
- Streaming Cognition Architecture (no streaming memory writes)

---

## Failure Modes and Safeguards

### Ghost Memory

Risk: A deleted record reappears because deletion was incomplete — missed a secondary layer, a cache, or a derived record.

Safeguards:
- deletion must cascade atomically across all layers
- the Memory Hierarchy maintains a deletion log that recall operations check before returning results
- any recall attempt for a deleted record must return nothing
- deletion completion is logged and confirmable

### Consent Boundary Violation

Risk: A Tier 1 feature activates without the required explicit consent — through default behavior, implicit inference, or bundled consent.

Safeguards:
- Tier 1 features are disabled at the capability level until explicit consent is recorded
- consent records are checked at activation time, not only at setup
- consent status changes trigger immediate capability state changes

### Retention Window Violation

Risk: Data persists beyond its defined retention window because enforcement is not automated or is bypassed.

Safeguards:
- retention enforcement is automated — it does not depend on manual review
- retention logs are auditable and include confirmation of deletion at window close
- data reads for records past their retention window must return nothing even if the record has not yet been physically deleted

### Third-Party Data Leak

Risk: Data transmitted to a cloud service provider is used beyond the contracted purpose — for training, profiling, or sharing with other parties.

Safeguards:
- data processing agreements prohibit use beyond contracted purpose
- context minimization reduces the value of transmitted data for unauthorized purposes
- Tier 1 data is never transmitted to cloud services regardless of DPA terms
- provider replaceability ensures no single provider accumulates irreplaceable data about the user

### Household Privacy Violation

Risk: Data about household members or guests who did not consent is retained in identifiable form.

Safeguards:
- person recognition requires individual consent — household membership does not imply consent
- conversations involving non-consenting parties are not retained as episodic memory
- environmental detection events that include non-consenting individuals are handled at the lowest retention tier

### Autonomous Action Overreach

Risk: Zola takes an autonomous action — sending a message, creating a calendar event — that was not within the authorized scope, or takes an irreversible action without confirmation.

Safeguards:
- autonomous action scope is explicitly defined and enforced by the Trust and Permission Framework
- irreversible actions require confirmation before execution unless explicitly pre-authorized
- all autonomous actions are logged with full context for user review

---

## Roadmap Considerations

> Note: Implementation phases and sequencing will be defined after the Ava codebase audit and delta analysis are complete. This section captures architectural intent only.

### Dependencies

- Memory Hierarchy Architecture must be stable before retention enforcement and deletion cascades can be built on top of it
- Durable Write Authority must exist before consent-gated write paths can be enforced
- Environmental Perception Architecture's Privacy and Permission Layer must be built before any camera or person recognition features are activated
- Distributed Presence Architecture must resolve the local versus cloud hosting model before cloud data transmission rules can be fully specified

### Critical Pre-Implementation Decisions

The following decisions must be made before implementation begins. They cannot be deferred to later phases because they shape the fundamental data architecture:

**Local versus cloud memory hosting** — will the default memory store be local-first, cloud-first, or user-selectable at setup? This decision affects encryption requirements, sync architecture, and the feasibility of the local-first option.

**Speech processing data retention** — what contractual requirements will govern Deepgram and other STT providers? Audio data retention by third parties is a significant risk surface.

**Person recognition architecture** — will person recognition be built as a local-only capability or will it use cloud-based vision APIs? The answer determines whether this feature can be activated at all under the Tier 1 local processing requirement.

**Household member model** — how does the system distinguish the primary user from household members for data handling purposes? This affects memory write authority, person recognition consent, and episodic memory retention.

### Open Questions

- What is the mechanism for the user to verify that deletion has completed? Should the system provide a deletion receipt?
- Should the user be able to export all their data in a portable format? If so, what format?
- How should the system handle data from integrations that are discontinued — for example, if a connected calendar service is removed?
- What is the process for handling a data breach — what is Zola's obligation to the user if retained data is exposed?
- Should there be a transparency report or periodic summary of what data was held, processed, and deleted?
- How are minors in the household handled — is there a separate data model for household members under 18?

### Architectural Risks

- Deletion cascade completeness is the highest-risk implementation area — every additional layer, cache, or derived record added to the system is a potential ghost memory vector; the deletion architecture must be designed for the complete future system, not just the current one
- The local versus cloud decision for memory storage is foundational — building on a cloud-first model and then trying to retrofit local-first later is extremely difficult; this decision must be made before memory persistence is implemented
- Third-party data processing agreements are legal instruments that take time to negotiate; the privacy requirements they need to satisfy must be defined before provider selection is finalized

---

## Long-Term End State

Privacy and Data Ownership eventually evolves toward:

- a system the user genuinely trusts with deeply personal information because that trust has been earned and maintained
- granular consent controls that give the user real understanding and real power over what Zola holds
- retention enforcement that happens automatically and completely without user management
- deletion that is genuinely complete and verifiably so
- local-first processing for the most sensitive capabilities, with cloud processing used minimally and transparently
- third-party data boundaries enforced by architecture and contract, not by policy and hope

The system should ultimately feel:

- trustworthy because what it knows about you is held carefully
- transparent because you can always understand what it holds and why
- respectful because it forgets what it should and keeps only what serves you
- safe because your most sensitive data stays closest to you

without losing:

- the usefulness that comes from Zola knowing you well
- the architectural discipline that makes privacy enforcement reliable rather than aspirational
- the principle that the user owns their data and Zola is its steward
- the guarantee that forget means gone
