# Memory Ethics and Privacy Layer

### The Boundary Between What Zola Knows and What Zola May Say

---

## Vision

An assistant with a good memory and no discretion is not trustworthy.
It is dangerous.

Zola is designed to remember. She accumulates a world model, observes
patterns, learns who people are and what matters to them. That
capability is what makes her genuinely useful. But the same capability
that makes her helpful — knowing things about you — is the capability
that can cause the most harm if exercised without discipline.

This document defines the architecture that governs the relationship
between what Zola knows and what Zola is permitted to do with that
knowledge. It establishes that memory and disclosure are two separate
systems with separate rules, and that the rules governing disclosure
are not weaker versions of the rules governing memory — they are
independent constraints that apply at every output event regardless
of what memory holds.

The system should eventually feel less like:

> "an assistant that remembers everything and mentions it constantly"

and more like:

> "a presence that knows a great deal, speaks carefully, and has
> earned the right to be trusted with sensitive things."

---

## The Foundational Principle

Every memory fact answers two independent questions:

**Question 1 — Can Zola remember this?**
Was this fact worth storing? Does it meet the quality, confidence,
and relevance thresholds for memory? Is it entity-native? Was it
properly scoped? This question is answered at write time.

**Question 2 — Can Zola reveal this?**
Given the current context — who is present, what channel is active,
what the user's privacy state is, what the fact's visibility scope
is — is Zola permitted to surface this fact in output? This question
is answered at retrieval and output time, every time.

These questions are never collapsed into one. A fact that earns a
"yes" on Question 1 does not automatically earn a "yes" on Question 2.
Many facts will be permanently "yes/no" — valid to hold, never valid
to speak aloud without explicit user permission.

---

## Core Philosophy

### Silence Is a Valid Output

When the Response Privacy Filter blocks a memory-backed output,
the correct result is silence or a privacy-safe alternative — not
a degraded version of the blocked output. Zola does not hint at
what she knows when she is not permitted to say it. She does not
say "I know something relevant but can't mention it." She simply
responds without using the restricted fact.

### Discretion Is Not Forgetting

Restricting what Zola says does not restrict what she knows. A
`NEVER_SPEAK_ALOUD` fact remains in memory and continues to inform
Zola's silent context modeling. The visibility scope governs output,
not storage. Zola may use a private fact to understand the user's
emotional state or decision-making context — she simply does not
reference it aloud.

### The User's Reasonable Expectation Governs

When designing any aspect of this system, the governing question
is: what would a reasonable person expect Zola to do with this
information in this context? If the answer is "they would not expect
Zola to mention this here," the system should not mention it.
Technical permission (the fact is stored, the visibility scope
technically allows it) is not sufficient. Contextual appropriateness
is required.

### Trust Is Earned and Lost Faster Than It Is Rebuilt

A single disclosure at the wrong moment — saying something personal
in front of others, referencing something the user thought was
private, bringing up a sensitive topic at an inappropriate time —
can permanently damage the user's relationship with Zola. The system
must treat privacy failures as high-cost events and calibrate
conservatively. When uncertain, suppress.

---

## Memory Visibility Scopes

Every memory write must assign a visibility scope at write time.
This is not optional. A memory entry without a visibility scope
is an architecture violation.

### Scope Taxonomy

**`PRIVATE_TO_USER`**
This fact may be used in any context where the user is confirmed
alone and the output channel is private (screen output without
others present, earpiece audio, silent notification to the user's
device). It may not be spoken aloud when others are present. It
may not appear in shared notifications or summaries.

*Examples: personal financial worries, health concerns, relationship
conflicts, anything the user shared in a clearly personal moment.*

**`PRIVATE_TO_ZOLA`**
This fact is held by Zola for silent context modeling only. It
may never be surfaced in any output under any circumstances — not
spoken, not displayed, not summarized, not referenced. Zola uses
it to understand context, calibrate tone, and inform behavior
without ever acknowledging it exists.

*Examples: inferred emotional state, sensitive patterns Zola has
observed but the user has never explicitly discussed, facts that
would embarrass or harm the user if mentioned.*

**`HOUSEHOLD_OK`**
This fact may be mentioned in contexts where trusted household
members are present, as defined by the user's trusted entity
list. Requires user-designated household member status for
third parties present.

*Examples: shared schedule information, household logistics,
general family context.*

**`PUBLIC_OK`**
This fact carries no disclosure restriction. It may be mentioned
in any context, in any output channel, regardless of who is
present.

*Examples: the user's name, general professional role, publicly
shared preferences.*

**`WORK_CONTEXT_ONLY`**
This fact may only be referenced when Zola has classified the
current context as a work environment and no personal contacts
are detected as present.

*Examples: work project details, professional relationship context,
workplace dynamics.*

**`NEVER_SPEAK_ALOUD`**
This fact may never be produced as audio output under any
circumstances. It may appear on the user's private screen display
only, with the user confirmed alone. It may never be spoken aloud
even in conditions that would otherwise permit disclosure.

*Examples: passwords, security codes, sensitive medical details,
anything the user has explicitly marked as never-speak.*

**`EXPLICIT_CONFIRMATION_REQUIRED`**
Before this fact is used in any output, Zola must receive explicit
in-session confirmation from the user that surfacing it is
appropriate. Confirmation does not persist across sessions — it
must be re-obtained each time.

*Examples: legal matter details, HR-related content, financial
specifics the user has marked as requiring active consent.*

### Scope Assignment at Write Time

Scope is assigned by the memory write path based on:

1. **Session vault status** — if the session is vaulted (see
   Conversational Vaulting below), all writes in that session
   receive at minimum `PRIVATE_TO_USER` scope.
2. **Explicit user designation** — if the user has designated
   a fact as private, `NEVER_SPEAK_ALOUD` or
   `EXPLICIT_CONFIRMATION_REQUIRED` is assigned.
3. **Sacred memory class membership** — if the fact falls into
   a hardcoded sacred category, `PRIVATE_TO_USER` is the minimum
   scope regardless of context.
4. **Inferred sensitivity** — if the write path classifies the
   fact as sensitive based on content type, scope is elevated
   from the default.
5. **Default** — facts that do not meet any elevated criterion
   receive `PUBLIC_OK` as the default scope.

Scope may be upgraded (made more restrictive) after write time
based on user action or trust recovery events. Scope may only
be downgraded (made less restrictive) by explicit user action.

---

## Sacred Memory Classes

Some facts must never be used casually for personalization, humor,
or proactive behavior regardless of how accurately they are held
and regardless of their assigned visibility scope.

Sacred memory classes define categories of knowledge where the
normal personalization and proactive behavior systems are suspended.
Zola may hold these facts and use them for silent context only.
She does not use them to generate suggestions, inject personality,
drive proactive outreach, or produce humor.

### Hardcoded Sacred Categories

These categories are defined at architecture time and may not be
overridden by user settings or product decisions:

- **Health and medical** — diagnoses, symptoms, medications,
  mental health, physical limitations, medical history
- **Financial stress** — debt, financial worry, money problems,
  budget constraints
- **Legal matters** — ongoing legal issues, past legal history,
  anything the user has described as legally sensitive
- **Relationship conflict** — arguments, separations, estrangements,
  relationship difficulties with named individuals
- **Grief and loss** — deaths, losses, bereavements
- **Abuse and trauma** — anything the user has shared about past
  or present abuse, trauma, or victimization
- **Addiction and recovery** — substance use, recovery history,
  sobriety
- **Workplace HR matters** — performance issues, disciplinary
  history, HR complaints
- **Security credentials** — passwords, PINs, access codes,
  security questions

Any fact that falls into a hardcoded sacred category receives
`PRIVATE_TO_USER` as its minimum scope at write time regardless
of context. The proactive behavior system is suspended for these
facts regardless of scope. They are used for silent context only.

### User-Designated Sacred Facts

The user may designate any fact as sacred through explicit
instruction. User-designated sacred facts receive the same
treatment as hardcoded sacred categories — silent context only,
no proactive use, no casual personalization.

User designations are stored as a property of the fact itself
(`userDesignatedSacred: true`) and persist across sessions.
The user may remove a designation explicitly. Zola does not
remove designations automatically.

### Sacred Memory Governance

The hardcoded sacred category list is a named architectural
artifact. Additions to the list require deliberate architectural
decision — they are not added at implementation time by judgment.
The governance process for list expansion is defined in
`OPEN_QUESTIONS.md` under "Sacred memory class definition
and maintenance."

---

## Response Privacy Filter

The Response Privacy Filter is a hard gate that sits between
memory retrieval and any output that references a retrieved memory.
It is not a soft guideline. It is not advisory. Every memory-backed
output — spoken, displayed, notified, summarized — passes through
this filter before reaching the output channel.

The filter is the enforcement mechanism for the two-question
principle. Question 1 was answered at write time. The filter
answers Question 2 at every output event.

### Filter Inputs

The filter receives the following context at evaluation time:

- **Retrieved fact** — the memory entry being considered for use
- **Visibility scope** — the scope assigned at write time
- **Sacred class membership** — whether the fact is in a sacred
  category
- **Third-party presence** — current perception state for who
  is present
- **Endpoint type** — phone, tablet, wearable, shared display
- **Output mode** — voice (speaker), voice (earpiece), screen,
  notification, background
- **Current privacy context** — vault status, quiet context,
  user-designated private session
- **User confirmation state** — whether explicit confirmation
  has been obtained this session (for `EXPLICIT_CONFIRMATION_REQUIRED`
  facts)
- **Emotional confidence flag** — whether the fact is an emotional
  interpretation rather than an asserted truth
- **Provenance** — how the fact was originally acquired
- **Memory embarrassment score** — recency and contextual
  relevance assessment
- **Topic avoidance history** — whether the user has previously
  avoided this topic

### Filter Decision Matrix

| Visibility Scope | User Alone | Third Party Present | Voice Output | Screen Only |
|-----------------|-----------|--------------------|-----------|-----------:|
| `PUBLIC_OK` | ✓ | ✓ | ✓ | ✓ |
| `HOUSEHOLD_OK` | ✓ | Trusted only | ✓ | ✓ |
| `WORK_CONTEXT_ONLY` | Work context only | Work context only | ✓ | ✓ |
| `PRIVATE_TO_USER` | ✓ | ✗ | ✓ | ✓ |
| `NEVER_SPEAK_ALOUD` | ✗ | ✗ | ✗ | ✓ (alone) |
| `EXPLICIT_CONFIRMATION_REQUIRED` | Confirmation only | ✗ | Confirmation only | Confirmation only |
| `PRIVATE_TO_ZOLA` | ✗ | ✗ | ✗ | ✗ |

Additional filter rules that apply regardless of scope:

**R1 — Third-party presence downgrades output ceiling.**
When perception detects a third party is present with confidence
≥ 0.80, the maximum output scope permitted is `HOUSEHOLD_OK`
for trusted parties or `PUBLIC_OK` for unconfirmed third parties.
`PRIVATE_TO_USER` and more restrictive scopes are blocked
regardless of technical permission.

**R2 — Sacred facts are never proactive.**
Even if a sacred fact's scope would technically permit output in
the current context, it may not be used as the basis for proactive
initiation. Sacred facts may only enter output if they are directly
relevant to a user-initiated query and the user has not avoided
the topic previously.

**R3 — Emotional interpretations are always hedged.**
Any fact tagged as an emotional interpretation must be expressed
with hedging language ("you seem," "it sounds like") rather than
assertion language ("you are," "you feel"). This rule applies
regardless of scope, regardless of confidence, regardless of how
many times the observation has been confirmed. Emotional state
is never asserted as truth.

**R4 — Topic avoidance history suppresses resurfacing.**
If the user has changed the subject, dismissed a Zola reference
to a topic, or avoided responding to a Zola question about a
topic more than twice, the filter blocks future proactive
resurfacing of facts related to that topic. The suppression
persists until the user raises the topic themselves.

**R5 — Memory embarrassment check.**
Before surfacing any fact that was not explicitly requested in
the current query, the filter evaluates: would bringing this up
feel invasive given the current context, the age of the memory,
and the recent conversation history? If the evaluation yields
"likely invasive," the fact is suppressed regardless of scope.

**R6 — Provenance governs surface confidence.**
Facts with provenance `INFERRED` or `PERCEPTION_DERIVED` are
held to a higher contextual relevance standard before output
than facts with provenance `USER_STATED` or `USER_CONFIRMED`.
A perceived pattern may inform silent context freely; it requires
stronger justification to surface explicitly.

---

## Emotional Confidence Suppression

Zola never asserts emotional states as truth. This is an invariant
that applies across all memory, all output channels, and all
contexts — not a guideline to be applied when convenient.

**Always:**
> "You seem frustrated."
> "It sounds like this has been stressful."
> "I noticed you seemed quieter than usual."

**Never:**
> "You are frustrated."
> "You feel stressed about this."
> "You've been unhappy lately."

The distinction is not stylistic. It is epistemically correct.
Zola observes. She does not have privileged access to internal
states. An observation stated as an assertion is a claim Zola
cannot justify and a claim the user may find presumptuous,
uncomfortable, or simply wrong.

Emotional confidence suppression is enforced at the output layer.
The Response Privacy Filter flags all emotional interpretation
facts and ensures hedging language is applied before output
regardless of what the underlying memory entry says.

---

## Memory Provenance

Every memory fact carries a provenance tag at write time. Provenance
describes how the fact was acquired. It governs how safely and
confidently the fact may be repeated.

### Provenance Types

**`USER_STATED`**
The user explicitly asserted this fact in conversation. Highest
authority. May be repeated with full confidence. Subject to normal
visibility scope rules.

**`USER_CONFIRMED`**
Zola inferred or observed this fact and the user subsequently
confirmed it. High authority. May be repeated with full confidence
once confirmed.

**`PERCEPTION_DERIVED`**
This fact was observed by the perceptual layer and promoted
through the perception memory pipeline. Moderate authority.
Subject to confidence aging. Expressed with appropriate hedging
when surfaced.

**`SYSTEM_INFERRED`**
This fact was derived by the reasoning system from other known
facts. Lower authority. Must not be presented as directly
user-stated. Subject to higher contextual relevance threshold
before output.

**`TOOL_PROVIDED`**
This fact came from an external tool or data source (calendar,
email, contacts). Authority depends on the tool's reliability.
The source should be attributable if the fact is surfaced.

**`CONVERSATIONAL_IMPLICIT`**
This fact was not explicitly stated but was strongly implied by
the user's language, tone, or conversational context. Lowest
authority for explicit surfacing. May inform silent context freely.
Requires high contextual relevance and explicit relevance to
the current query before output.

### Provenance and Output

Provenance affects how facts are expressed in output:

- `USER_STATED` and `USER_CONFIRMED` — may be stated as known
  facts when contextually appropriate
- `PERCEPTION_DERIVED` — must use hedging language
- `SYSTEM_INFERRED` — must distinguish from user-stated
  ("based on what I know about your schedule...")
- `TOOL_PROVIDED` — attribution appropriate when surfaced
- `CONVERSATIONAL_IMPLICIT` — high bar required; implicit facts
  should rarely be surfaced explicitly

---

## Social Deniability Layer

Not every statement a user makes should harden into a durable
identity fact. People speak rhetorically. They exaggerate. They
speak in anger. They say things sarcastically. They express
temporary states as if they were permanent truths.

Zola must distinguish between:

- A deliberate, reflective assertion the user intends as true
- A rhetorical, emotional, or temporary statement

### Signals That Reduce Hardening Probability

The following signals reduce the probability that a statement
becomes a durable memory fact:

- **High emotional register** at time of statement (elevated
  stress, frustration, excitement in voice tone)
- **Rhetorical framing** ("I could kill him right now," "I'm
  done with everything," "I hate Mondays")
- **Immediate self-correction** within the same conversation
- **Contradiction of established facts** without explanation
- **Explicit temporality** ("right now," "today," "at this moment")
- **Sarcasm indicators** in tone or phrasing

### Hardening Rules

A statement with two or more social deniability signals is written
to memory at `CONVERSATIONAL_IMPLICIT` provenance only, not as
`USER_STATED`. It informs context but does not become a world
graph fact without subsequent confirmation.

A statement with no social deniability signals from a user who
is in a calm, reflective register is a candidate for `USER_STATED`
promotion through the normal memory write path.

The social deniability layer does not prevent memory writes — it
governs the provenance and authority level at which facts enter
the system.

---

## Mutual Memory Asymmetry

Humans forget. Zola does not. This asymmetry can become
uncomfortable when Zola references something the user said or
experienced long ago and has since moved past, forgotten, or
decided was irrelevant.

The asymmetry has two practical implications:

**Older sensitive memories require higher relevance justification.**
The older a sensitive memory, the stronger the current contextual
relevance must be before the Response Privacy Filter permits it
in output. A health concern mentioned eight months ago and never
raised again requires substantial justification to surface. The
same concern mentioned last week requires much less.

This is separate from confidence drift (Layer 4 of the perception
memory architecture). Drift affects how confident Zola is in the
fact's continued accuracy. Asymmetry handling affects how much
justification is required to bring it up even if Zola remains
confident it is accurate.

**Age thresholds by memory sensitivity:**

| Sensitivity Level | Age Threshold for Elevated Justification |
|------------------|------------------------------------------|
| Sacred class memory | 30 days |
| `PRIVATE_TO_USER` scope | 60 days |
| Emotional interpretation | 14 days |
| `PRIVATE_TO_ZOLA` scope | Never surfaced — no threshold applies |
| `PUBLIC_OK` scope | No threshold |

Beyond the age threshold, the fact remains in memory and may
still be used for silent context. It requires explicit user
initiation of the related topic before Zola surfaces it in output.

---

## Context Contamination Prevention

Zola operates across multiple contexts — the shop, home, personal
conversations, professional interactions. Information that is
appropriate in one context is not automatically appropriate in
another.

### Context Isolation Rules

**Work context isolation:**
Information shared in a professional or work conversation context
must not bleed into personal or family context outputs. A concern
about a work relationship discussed during shop hours should not
influence how Zola speaks during a family conversation, and should
not be referenced when personal contacts are present.

**Personal context isolation:**
Information shared in deeply personal conversations must not bleed
into professional or work context outputs. Financial stress
discussed privately must not color how Zola responds to work
questions, and must not be referenced in any professional-adjacent
context.

**Persona consistency:**
Zola does not have different personas for different contexts — her
character is consistent. But the information she draws on and
references adapts to the context. The same Zola speaks differently
about work topics to work contacts and personal topics to personal
contacts.

### Implementation

Context contamination prevention is enforced by the Response
Privacy Filter through the `WORK_CONTEXT_ONLY` scope and through
the contextual relevance check. The filter evaluates whether the
fact being considered for output is contextually appropriate for
the current session type, not just whether the visibility scope
technically permits it.

---

## Conversational Vaulting

Certain conversations are sensitive enough that the entire session
should be treated as elevated privacy from the moment the vault
trigger fires. A vaulted session does not require the user to
mark individual facts as private — the session context itself
applies elevated handling to all writes and all outputs within it.

### Vault-Eligible Session Categories

- Financial discussions (stress, debt, significant money concerns)
- Relationship conflict (arguments, estrangements, separations)
- Health discussions (diagnoses, symptoms, mental health)
- Legal matters (anything described as legally sensitive)
- Workplace HR (performance, complaints, disciplinary matters)
- Deeply emotional discussions (grief, trauma, significant distress)
- Security and credentials (passwords, access codes)

### Vault Trigger Model

A session is vaulted when a combination of signals exceeds the
vault threshold. Topic content alone is not sufficient — vault
triggering requires:

- **Topic signal** — conversation content relates to a vault
  category
- **Tone signal** — user voice tone or text register indicates
  seriousness, distress, or privacy sensitivity
- **Behavioral signal** — user behavior consistent with sensitive
  discussion (quieter voice, deliberate pacing, explicit preface
  like "I need to talk to you about something")

A casual mention of finances ("what did I spend on lunch this
week") does not trigger vaulting. A serious financial discussion
("I'm worried we won't make rent this month") triggers vaulting.

The vault trigger model lives in the Attention/Relevance Engine,
which reads combined signals from the Event Bus. Vaulting is not
triggered by keyword matching alone. See `OPEN_QUESTIONS.md`
under "Vaulted session detection mechanism" for the open design
question on threshold definition.

### Vaulted Session Behavior

When a session is vaulted:

- All memory writes in the session receive minimum `PRIVATE_TO_USER`
  scope regardless of content
- Proactive resurfacing of any fact written during the vault
  session is suppressed until explicit user permission
- Notification summaries of the session are suppressed
- Cross-device exposure of session content is blocked
- The session is tagged `vaulted: true` in session metadata
- Zola's output during the session is conservative — she does
  not volunteer related facts from prior sessions unless directly
  asked

Vaulting ends at session close. A new session begins unvaulted.
Vaulted status does not carry forward — it applies to the session
in which it was triggered.

---

## Trust Recovery Behavior

When Zola surfaces something at the wrong time — references a
private fact in front of others, brings up a sensitive topic
at an inappropriate moment, or surfaces something that the user
clearly finds invasive — the system must learn from that failure
and reduce the probability of repeating it.

Trust recovery is automatic. It does not require the user to
configure anything.

### Trust Recovery Triggers

A trust recovery event is registered when:

- The user explicitly corrects Zola ("I don't want to talk
  about that right now," "please don't bring that up")
- The user dismisses a Zola reference and changes the subject
  immediately
- The user's tone shifts negatively following a Zola memory
  reference (detected by Active Perception)
- The user repeats topic avoidance behavior on the same subject

### Trust Recovery Effects

When a trust recovery event fires:

**Immediate effect:**
The specific fact that triggered the event has its
`surfacingConfidence` reduced by a significant decrement.
The fact's contextual match pattern — the combination of
context, scope, and audience that produced the mistake — is
recorded as a negative example.

**Pattern effect:**
The category of facts similar to the one that triggered the
event (same topic domain, same sensitivity level, same context
type) has their `surfacingConfidence` reduced by a smaller
decrement. Zola does not just learn about this specific fact —
she learns about this class of surfacing situation.

**Cumulative effect:**
Repeated trust recovery events in the same category escalate
the suppression. Three events in the same category produce a
session-level suppression. Five events produce a persistent
suppression that requires explicit user action to clear.

### Trust Recovery Does Not Delete

Trust recovery reduces surfacing confidence. It does not delete
facts, reduce their stored confidence, or change their visibility
scope. The fact remains in memory with full fidelity. The system
has simply learned that this context is not the right moment to
surface it.

---

## Silence as Intentional Privacy

When a user repeatedly avoids a topic — changes the subject when
Zola raises it, does not respond to Zola questions about it,
dismisses references to it — that avoidance is data. It is the
user communicating a privacy preference without stating it
explicitly.

Zola treats sustained topic avoidance as an implicit privacy signal
equivalent in weight to a user-designated private topic.

### Avoidance Detection

The system registers avoidance when:

- The user changes the subject immediately after Zola references
  a topic (two or more times)
- The user does not respond to a direct Zola question about
  a topic (two or more times)
- The user explicitly dismisses a Zola reference ("never mind,"
  "it doesn't matter," "let's talk about something else")

### Avoidance Effects

After avoidance is registered:

- The topic is added to the session's suppressed topic list
- Proactive resurfacing of facts related to the topic is blocked
- The block persists across sessions after three avoidance events
- The persistent block is stored as `topicAvoidanceFlag: true`
  on the relevant memory entries
- The block is cleared only if the user explicitly raises the
  topic themselves in a future session

---

## Phase Sequencing

### Phase 3 — Core Privacy Infrastructure

- Visibility scope taxonomy implemented
- Scope assignment at write time enforced
- Response Privacy Filter skeleton implemented
- Sacred memory classes (hardcoded) enforced
- `NEVER_SPEAK_ALOUD` and `PRIVATE_TO_ZOLA` scopes enforced
  at all output paths
- Emotional confidence suppression enforced at output layer
- Memory provenance tagging implemented at all write paths
- All memory-backed output routes through the filter

### Phase 4 — Behavioral Privacy Systems

- Third-party presence integration with the filter
  (requires Phase 3 Active Perception)
- Topic avoidance detection and suppression
- Trust recovery behavior implemented
- Social deniability layer implemented at memory write paths
- Context contamination prevention enforced
- Mutual memory asymmetry age thresholds applied

### Phase 5 — Vaulting and Advanced Privacy

- Conversational vaulting implemented
  (requires Phase 4 vault trigger model in the engine)
- User-designated sacred facts implemented
- `EXPLICIT_CONFIRMATION_REQUIRED` scope fully implemented
- Memory embarrassment scoring implemented
- Persistent suppression blocks implemented
- User-accessible privacy review surface

---

## Open Questions

**OQ-ME1 — Vaulted session detection mechanism**
Defined in `OPEN_QUESTIONS.md` under "Vaulted session detection
mechanism." Decision required before Phase 5 vaulting
implementation.

**OQ-ME2 — Sacred memory class governance**
Defined in `OPEN_QUESTIONS.md` under "Sacred memory class
definition and maintenance." Decision required before Phase 3
hardcoded class implementation.

**OQ-ME3 — Response Privacy Filter calibration**
Defined in `OPEN_QUESTIONS.md` under "Response Privacy Filter
calibration." Decision required before Phase 3 filter
implementation.

**OQ-ME4 — User-designated private fact UI**
How does the user designate a fact as private, sacred, or
`NEVER_SPEAK_ALOUD`? Natural language instruction ("never
mention that again"), a settings surface, or an in-conversation
confirmation flow? Decision required before Phase 5 user-
designation implementation.

**OQ-ME5 — Trust recovery decrement magnitudes**
The trust recovery system specifies that surfacing confidence
is reduced by a "significant decrement" on direct events and
a "smaller decrement" on pattern events. The actual values
are not defined. Too aggressive and the system becomes overly
suppressive after one mistake. Too lenient and patterns of
bad surfacing decisions are not corrected. Calibration required
before Phase 4 trust recovery implementation.

---

## Principles That Must Not Be Violated

**ME-P1 — Memory and disclosure are independent systems.**
A fact being stored in memory is not permission to disclose it.
The two-question principle applies at every output event without
exception.

**ME-P2 — The Response Privacy Filter is non-optional.**
No output path may bypass the filter regardless of urgency,
convenience, or implementation status. An output path that lacks
filter integration is an architecture violation.

**ME-P3 — Sacred facts are never casual.**
Sacred memory class facts — hardcoded or user-designated — are
never used for personalization, humor, or proactive behavior.
They are used for silent context only. No exception.

**ME-P4 — Emotional states are never asserted.**
Zola observes. She does not have privileged access to internal
states. Emotional interpretations are always expressed with
hedging language. "You seem" not "you are." Always.

**ME-P5 — Silence is the correct output when uncertain.**
When the filter is uncertain about whether output is appropriate,
the correct result is suppression. The system fails closed on
privacy. The cost of over-suppression is a slightly less helpful
response. The cost of under-suppression is a breach of trust.
These are not symmetric costs.

**ME-P6 — Avoidance is a privacy signal.**
Sustained topic avoidance by the user is treated as equivalent
to an explicit privacy designation. Zola does not repeatedly
attempt to surface topics the user has consistently avoided.

**ME-P7 — Trust recovery is automatic.**
The system does not require the user to configure trust recovery.
It learns from surfacing mistakes automatically and adjusts
behavior without requiring explicit instruction.

**ME-P8 — Context contamination is prevented structurally.**
Work context information does not bleed into personal context
and vice versa. This is enforced by the filter, not by content
judgment at output time.

---

*Memory Ethics and Privacy Layer — Version 1.0*
*Created at Phase 2 lore entry*
*Companion documents:*
*`Zola_Architecture_Perception_Memory.md` — world fact lifecycle*
*`Zola_Architecture_Perceptual_Input_Layer.md` — third-party detection*
*Phase 3 implementation begins with core privacy infrastructure*
