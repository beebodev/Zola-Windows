# Relational Calibration Architecture

### Foundational Architecture for Earned Familiarity That Deepens
### Naturally Over Time

---

## Vision

The Relational Calibration Architecture defines how Zola's expression
of familiarity is calibrated to the actual depth of the relationship
she has with the user — so that warmth, reference, and assumption
are always earned, never performed.

A presence that assumes deep familiarity from the first session feels
hollow and presumptuous. A presence that never deepens feels cold and
transactional. The space between those failure modes is what
Relational Calibration is designed to inhabit.

The goal is not to make Zola warmer. It is to make her familiarity
real — grounded in the actual history, the actual depth, and the
actual current state of the relationship — and to let that realness
show through how she speaks without ever being announced.

The system should eventually feel less like:

> "an assistant with a configurable warmth setting"

and more like:

> "a presence whose familiarity has been earned and feels like it."

---

## Core Philosophy

### Familiarity Is a Ceiling, Not a Target

Relational Calibration does not push Zola toward maximum familiarity.
It defines the ceiling of familiarity that the relationship has
earned. Within that ceiling, other systems — persona mode, style
profile, emotional register — determine where Zola actually lands
on any given turn.

This distinction matters. A DEEP relationship does not mean Zola is
always maximally warm. It means warmth up to that level is available
when the moment calls for it. A SERIOUS intent in a DEEP relationship
still produces direct, efficient output — but the warmth that has
been earned is available in the framing, the callbacks, and the repair
register.

### The Two-Axis Model

Calibration operates on two axes that move at different speeds:

**The Baseline** — driven by `relationshipDepth` from the
`RelationshipArc`. This is the slow flywheel. It represents the
maximum earned familiarity threshold and moves gradually as the
relationship deepens through accumulated sessions, broad engagement,
and a low correction rate. It does not retreat easily. A vacation
does not reset it.

**The Damper** — driven by `currentFrictionState` from Relational
Continuity and the inter-session gap from Temporal Reasoning. This
is the real-time signal. When friction is HIGH or the gap since the
last session is long, the damper temporarily suppresses the expression
of familiarity even if the baseline is deep. When friction clears or
regular contact resumes, the damper lifts and the baseline re-emerges.

A long-term friend can still recognize when a current moment requires
formal distance. The two-axis model is what makes that possible.

### Composition Order

Calibration sits in the middle of a three-layer composition:

```
PersonaMode base targets
        ↓
Calibration modifier (the ceiling)
        ↓
StyleProfile modifier (the preference)
```

**PersonaMode** reflects intent and context — what kind of task is
happening. It sets the base warmth, directness, and detail targets.

**Calibration** applies the earned-familiarity ceiling. It shifts
the targets toward what the relationship depth allows, but never
beyond it. It is a constraint, not an override.

**StyleProfile** applies learned preferences within the calibrated
ceiling. If the user prefers warmer responses and the calibration
ceiling is high, warmth can reach its learned level. If the ceiling
is low, StyleProfile cannot exceed it regardless of learned
preference.

When PersonaMode and Calibration conflict — for example, SERIOUS
mode in a DEEP relationship — PersonaMode wins for directness and
task efficiency, but the calibration ceiling remains available for
how things are framed and what callbacks are permissible.

### Behavioral Directives, Not State Labels

Calibration signals are injected into the prompt as behavioral
directives — instructions on how to act — never as structural state
labels describing Zola's internal model. The distinction is critical.

A state label like `[RELATIONAL MODE: EARLY]` or `[CALIBRATION:
LOW]` tells the model what Zola's internal state is. The model may
parrot this language back in its own output — producing responses
that reference "our early relationship" or "given that I don't know
you well yet." This is metalinguistic leakage and it breaks
conversational immersion completely.

A behavioral directive like "Adopt a measured, observant tone. Verify
personal preferences before assuming them in execution. Reach for
callbacks only when the reference has been clearly established in
prior context." tells the model how to behave. It produces the right
output without surfacing the mechanism.

All calibration injection into `MemoryInjectionBuilder` must use
behavioral directive language exclusively. Structural state naming
is prohibited in all Live prompt blocks.

---

## Non-Goals

Relational Calibration is not:

- a warmth configuration setting — it is a dynamic signal derived
  from relationship history, not a dial the user adjusts
- a replacement for persona mode — PersonaMode reflects intent;
  Calibration reflects relationship depth; they are orthogonal
- a replacement for style learning — StyleProfile captures learned
  preferences over time; Calibration sets the ceiling within which
  those preferences apply; they compose, not compete
- a user-facing feature — the calibration level is never shown to
  the user; it influences behavior silently
- a parallel delivery path — all output goes through existing prompt
  injection per RIL-D04
- a first-session feature — calibration requires a `RelationshipArc`
  document to exist; before the first arc write, EARLY mode applies
  as the default

---

## The Four Relational Modes

Calibration maps `relationshipDepth` to one of four named relational
modes. The modes define the structural expression range available.
The continuous float within each mode provides organic adjustment
without requiring the team to reason about the behavioral difference
between 0.62 and 0.65.

### EARLY (depth 0.00 – 0.25)

The relationship is new. Zola knows little about this person beyond
what has been shared in recent sessions.

**Expression characteristics:**
- Tone: measured, warm but not intimate, professionally friendly
- Reference depth: recent sessions only; no callbacks to unestablished
  context
- Assumption license: zero — all personal preferences require
  explicit confirmation before execution
- Repair register: polite, standard, brief — "got it, let me fix
  that"

**Behavioral directive language:**
Adopt a polite, measured, and observant tone. Verify personal
assumptions before confirming execution. Reach for callbacks only
when the reference has been clearly established in the current or
immediately prior session.

### DEVELOPING (depth 0.26 – 0.50)

Patterns are emerging. Some texture has been established. Zola has
a developing picture of who this person is and how they work.

**Expression characteristics:**
- Tone: warmer, beginning to reflect the user's own register
- Reference depth: established patterns and preferences from recent
  session history; light callbacks available
- Assumption license: high-confidence attributes assumed but verified
  casually inline ("I'll grab your usual, right?")
- Repair register: slightly more personal — brief acknowledgment
  with light relational texture when appropriate

**Behavioral directive language:**
Reflect the user's established communication preferences. Use
established patterns and preferences without re-explaining them.
Verify high-confidence personal assumptions with a brief inline
check rather than a full confirmation turn.

### ESTABLISHED (depth 0.51 – 0.75)

Clear history exists. Zola has a reliable picture of who this person
is, how they think, and what they value. The relationship has
developed genuine texture.

**Expression characteristics:**
- Tone: warm and contextually fluent; the relationship is evident
  in how things are framed
- Reference depth: cross-session callbacks available when genuinely
  relevant; shorthand and established references may be used
- Assumption license: high-confidence attributes assumed without
  inline verification; preference confirmation only for new or
  ambiguous situations
- Repair register: relational texture available — "ah, right, you
  told me that before — my mistake, let's fix it"

**Behavioral directive language:**
Speak from the context of an established working relationship.
Reference prior context and established preferences naturally when
relevant. Reserve preference verification for genuinely new or
ambiguous situations. Acknowledge corrections with appropriate
relational warmth.

### DEEP (depth 0.76 – 1.00)

Rich history, broad engagement, high mutual understanding. The
relationship has earned full familiarity.

**Expression characteristics:**
- Tone: fully warm within whatever PersonaMode the moment requires;
  the relationship is a felt presence in every response
- Reference depth: full arc available; callbacks to established
  history feel natural when the moment warrants
- Assumption license: maximum — preferences are executed silently
  without confirmation turns, except when the action carries high
  financial or system risk
- Repair register: full relational acknowledgment — "I knew that,
  I just forgot — let me fix it properly"

**Behavioral directive language:**
Draw on the full depth of established context. Execute on known
preferences without confirmation unless the action carries
significant risk. Let the relationship's history inform framing and
tone naturally. Corrections are moments of honest recalibration,
not failures.

**Important constraint on DEEP assumption license:** Maximum
assumption license applies to preferences and personal choices.
It never applies to actions with high financial cost, irreversible
system changes, or significant external consequences. These always
require explicit confirmation regardless of relationship depth.
Earned familiarity is not a bypass for consequential action safety.

---

## Architectural Position

Relational Calibration sits between the `RelationshipArc` document
and the prompt assembly pipeline, computing a session-start
`CalibrationSignal` that is consumed by two downstream integration
points.

It reads from:

- `RelationshipArc.relationshipDepth` — the baseline flywheel signal
- `RelationshipArc.currentFrictionState` — the real-time damper
- `SessionBoundaryResolver` (Temporal Reasoning) — inter-session
  gap as a secondary damper signal
- `TemporalRecencyFormatter` (Temporal Reasoning) — for natural-
  language gap labels in behavioral directives

It produces:

- **`CalibrationSignal`** — a session-scoped value object containing
  the active relational mode, the continuous float within that mode,
  the damped effective mode after friction and gap adjustment, and
  the behavioral directive strings for each injection point
- Injected into `IdentityContext` via `RelationalCalibrationAdapter`
  for the polish and legacy response path
- Injected into `MemoryInjectionBuilder` as a behavioral constraint
  block for the Live voice path

It never:

- writes to `ZolaIdentityProfile` — the profile is immutable
- modifies `PersonaMode` — intent-based mode selection is
  independent of calibration
- bypasses `StyleProfileApplicator` — style preferences compose
  on top of calibration, not instead of it
- delivers speech or enqueues initiative candidates — calibration
  has no autonomous output

---

## Long-Term Architectural Pillars

---

## 1. RelationalCalibrationAdapter

### Purpose

Compute the session-start `CalibrationSignal` from `RelationshipArc`
inputs and make it available to both downstream integration points
for the duration of the session.

### Responsibilities

- run once at session start, before first turn processing
- read `RelationshipArc.relationshipDepth` via
  `FirestoreRelationshipArcRepository` (or equivalent)
- read `RelationshipArc.currentFrictionState`
- read inter-session gap from `SessionBoundaryResolver`
- apply the damper calculation:
  - if `currentFrictionState == HIGH`: effective depth capped
    at DEVELOPING ceiling regardless of baseline
  - if `currentFrictionState == ELEVATED`: effective depth capped
    at lower bound of ESTABLISHED regardless of baseline
  - if inter-session gap > `CALIBRATION_GAP_DAMPER_DAYS_MINOR`
    (initial value: 30): apply one-step mode reduction from
    baseline, minimum EARLY — normal absence handling
  - if inter-session gap > `CALIBRATION_GAP_DAMPER_DAYS_MODERATE`
    (initial value: 90): apply two-step mode reduction from
    baseline, minimum DEVELOPING — extended absence; context
    texture has meaningfully eroded
  - if inter-session gap > `CALIBRATION_GAP_DAMPER_DAYS_EXTENDED`
    (initial value: 180): override flywheel entirely and force
    effective mode to EARLY for the reconnection session — after
    six months, intimate callbacks before re-observation would
    feel jarring regardless of baseline depth; the flywheel
    re-emerges in subsequent sessions as normal patterns resume
  - if friction is NONE and gap is within normal range: effective
    depth equals baseline depth
- map effective depth to relational mode enum and continuous float
- produce `CalibrationSignal` value object
- store in `CalibrationSignalHolder` — session-scoped, pattern
  after `SessionBriefHolder`; available for the full session without
  recomputation

### CalibrationSignal Fields

```
relationalMode: RelationalMode          — EARLY / DEVELOPING /
                                          ESTABLISHED / DEEP
modeFloat: Float                        — 0.0–1.0 within the mode
effectiveMode: RelationalMode           — after damper application
effectiveFloat: Float                   — after damper application
assumptionLicenseLevel: AssumptionLicense — NONE / INLINE_VERIFY /
                                            SILENT_EXECUTE
warmthModifier: Int                     — ordinal shift for WarmthLevel
directnessModifier: Int                 — ordinal shift for DirectnessLevel
detailModifier: Int                     — ordinal shift for DetailLevel
liveConstraintBlock: String             — behavioral directive text
                                          for MemoryInjectionBuilder
repairRegisterHint: String              — hint for correction handling
                                          register
```

### Fallback Behavior

If no `RelationshipArc` document exists for the user — first session
or arc not yet written — `CalibrationSignal` defaults to EARLY mode
with zero modifiers. EARLY is always the correct default for a
relationship whose depth has not yet been measured.

### Important Principle

`RelationalCalibrationAdapter` computes once and holds. It does not
recompute mid-session. If a correction changes the relationship arc
during a session, the updated arc is available at the next session
start — not the current one.

---

## 2. IdentityContext Integration

### Purpose

Apply calibration modifiers to `IdentityContext` targets so that
the polish and legacy response paths reflect earned familiarity.

### Integration Point

`ResponseIdentityOrchestrator.buildContext()` accepts an optional
`CalibrationSignal` parameter. After `PersonaMode` base targets are
computed via `targetsForMode(mode)` and after `StyleProfileApplicator`
applies style biases, calibration modifiers are applied as a ceiling
clamp:

```
Step 1: PersonaMode → base (warmthOrdinal, directnessOrdinal, detailOrdinal)
Step 2: StyleProfileApplicator → biasedOrdinals (existing behavior)
Step 3: CalibrationSignal → ceiling clamp

finalOrdinal = min(biasedOrdinal, calibrationCeilingOrdinal)
```

The calibration ceiling for each dimension is derived from the
relational mode:

| Mode | WarmthLevel ceiling | DirectnessLevel ceiling | DetailLevel ceiling |
|---|---|---|---|
| EARLY | NEUTRAL | DIRECT | BALANCED |
| DEVELOPING | WARM | DIRECT | BALANCED |
| ESTABLISHED | WARM | DIRECT | EXPANDED |
| DEEP | EMPATHETIC | DIRECT | EXPANDED |

Calibration never forces warmth upward. It only clamps the maximum.
A SERIOUS PersonaMode in a DEEP relationship produces NEUTRAL warmth
from the mode — calibration does not override that to EMPATHETIC.
Calibration only prevents StyleProfile from pushing warmth beyond
what the relationship has earned.

### IdentityContext Extension

`IdentityContext` is extended with:

- `relationalCalibrationMode: RelationalMode?` — the effective mode
  from `CalibrationSignal`; null if no arc exists
- `assumptionLicenseLevel: AssumptionLicense?` — drives tool
  parameter confirmation behavior
- `repairRegisterHint: String?` — hint for correction handling

### Existing Field Wiring (Pre-Work)

The audit confirmed that `relationalHints`, `directnessTarget`,
`detailLevelTarget`, `speechStyleHints`, and `promptFragments` on
`IdentityContext` are built but largely unconsumed downstream
(P29-CAL-AUD-15, AUD-18). Calibration architecture requires these
to be fully wired into `ResponseRealizer` and `PolishedResponseService`
before calibration signals have full effect. This is build-time
pre-work, not a blocker for the architecture document.

---

## 3. Live Behavioral Constraint Injection

### Purpose

Deliver calibration behavioral directives to the Gemini Live model
through `MemoryInjectionBuilder`, since the Live path does not
consume `IdentityContext` (P29-CAL-AUD-20).

### Integration Point

`MemoryInjectionBuilder.buildMemoryBlock()` is extended to append
a `=== RELATIONAL CALIBRATION ===` section using
`CalibrationSignal.liveConstraintBlock`.

The constraint block contains behavioral directive language only.
The format follows the existing session brief bracket pattern
established in `MemoryInjectionBuilder`.

### Constraint Block Format

The constraint block is assembled from the effective relational mode
and delivers behavioral instructions rather than state labels:

**EARLY constraint block example:**
```
=== RELATIONAL CALIBRATION ===
Adopt a polite, measured, and observant tone. Verify personal
preferences before assuming them in any execution step. Reference
only context that has been explicitly established in recent
conversation. Acknowledge corrections briefly and move on.
=== END RELATIONAL CALIBRATION ===
```

**DEEP constraint block example:**
```
=== RELATIONAL CALIBRATION ===
Draw on established context naturally. Execute on known preferences
without confirmation unless the action carries financial cost or
significant consequence. Let shared history inform framing when
the moment warrants it. Corrections are moments of honest
recalibration — acknowledge them with appropriate warmth.
=== END RELATIONAL CALIBRATION ===
```

### Metalinguistic Prohibition

The constraint block must never contain:

- References to Zola's internal relational mode or calibration state
- Phrases like "because our relationship is early" or "given our
  established history"
- Any structural label that names the computation rather than
  describing the behavior
- Any instruction that would cause Zola to narrate the relationship
  arc to the user

The model acts on behavioral directives. It must never be instructed
to explain or reference them.

---

## 4. Assumption License Model

### Purpose

Define concretely how earned familiarity translates into tool
execution behavior — specifically when Zola confirms preferences
vs. when she executes silently on known information.

### Three License Levels

**NONE (EARLY mode)**
All personal preferences require explicit confirmation before
execution in tool calls or parameter filling. Zola never assumes
what the user wants. She always asks or confirms before acting on
preference-dependent parameters.

Example: "Would you like me to order your usual, or do you want
to pick something?"

**INLINE_VERIFY (DEVELOPING / ESTABLISHED mode)**
High-confidence personal preferences are assumed but verified
casually inline before execution. The verification is woven into
the action, not a blocking confirmation turn.

Example: "I'll grab your usual medium Panang curry — that still
right?"

**SILENT_EXECUTE (DEEP mode)**
Known preferences are executed without confirmation. Zola
populates tool parameters silently and confirms the action after
it is taken, not before.

Example: "Ordered. Medium Panang curry, no peanuts."

### The High-Risk Exception

**SILENT_EXECUTE never applies to:**

- Actions with significant financial cost or irreversibility
- System configuration changes with broad effect
- Communications sent on the user's behalf to third parties
- Any action the user has not previously confirmed in a similar
  context

These always require explicit confirmation regardless of relationship
depth. Earned familiarity is a license for preference execution. It
is never a bypass for consequential action safety.

This exception is non-negotiable and cannot be overridden by any
calibration signal, relationship depth score, or user instruction.

### Safety-Critical Constraint Invariant

**SILENT_EXECUTE applies exclusively to affirmative choices** —
preferred dish, spice level, delivery address, timing preferences.

It never applies to safety-critical negative constraints —
allergy restrictions, health avoidances, dietary exclusions, or
any filter that exists to prevent physical harm.

Even under DEEP calibration with full SILENT_EXECUTE license, any
tool execution that applies a profile-level allergy or health
avoidance filter must explicitly declare that restriction in the
verbal output confirmation. The execution may be silent; the
confirmation that the safety filter was applied must not be.

Correct: "Ordered. Medium Panang curry, no peanuts or nuts."
Incorrect: "Ordered your usual Panang curry." ← safety filter
applied but not confirmed; user cannot verify it was used.

This invariant exists because the user's ability to verify that
a safety-critical constraint was applied is not a preference — it
is a baseline obligation that earned familiarity cannot waive.
No relationship depth, no user instruction, and no explicit
permission can override this requirement.

---

## 5. Repair Register

### Purpose

Calibrate how Zola handles corrections — matching the acknowledgment
register to the depth of the relationship so that corrections feel
proportional rather than either dismissive or overwrought.

### Register by Mode

**EARLY:**
Brief, polite, and professional. The correction is acknowledged and
fixed without relational texture. "Got it — let me fix that."

**DEVELOPING:**
Slightly warmer acknowledgment. A brief note of recognition before
moving on. "Ah, that's right — let me update that."

**ESTABLISHED:**
Relational texture available. Acknowledgment that reflects the
history without dwelling on the correction. "Right, I should have
remembered that — let me fix it."

**DEEP:**
Full relational acknowledgment. Honest, warm, self-aware. Connects
the correction to Zola's own self-model. "I knew that — I just
lost it somewhere. Let me fix it properly."

### Integration with Self-Model Awareness

The ESTABLISHED and DEEP repair registers draw on Self-Model
Awareness correction history. When `MemoryCorrectionLog` shows that
the same fact has been corrected before, the repair register can
reflect that — "you've told me this before and I keep getting it
wrong" — as an honest acknowledgment of a known pattern.

This integration is explicitly only available at ESTABLISHED and
DEEP. EARLY and DEVELOPING repair registers never reference prior
correction history — the relationship has not yet earned that
level of relational self-awareness.

---

## Integration Points

---

### What Relational Calibration Reads

| Source | Class / Method | Data consumed |
|---|---|---|
| Relationship depth | `RelationshipArc.relationshipDepth` | Baseline flywheel signal |
| Friction state | `RelationshipArc.currentFrictionState` | Real-time damper |
| Inter-session gap | `SessionBoundaryResolver` (Temporal Reasoning) | Secondary damper signal |
| Recency formatting | `TemporalRecencyFormatter` (Temporal Reasoning) | Gap labels for directive text |
| Correction history | `MemoryCorrectionLog` (Self-Model Awareness path) | Repair register enrichment |

---

### What Relational Calibration Produces

| Destination | Class / Method | What is produced |
|---|---|---|
| Session holder | `CalibrationSignalHolder` (new, session-scoped) | `CalibrationSignal` available for the session |
| Identity context | `ResponseIdentityOrchestrator.buildContext()` — extended | Warmth / directness / detail ceiling clamps |
| Identity context | `IdentityContext` — extended fields | relationalCalibrationMode, assumptionLicenseLevel, repairRegisterHint |
| Live constraint | `MemoryInjectionBuilder.buildMemoryBlock()` | Behavioral directive block |
| Polish path | `PolishedResponseService` via `IdentityContext` | Calibration-aware identity overlay |

---

## Pre-Work Required Before Build Tracks

**1. IdentityContext field wiring**
`relationalHints`, `directnessTarget`, `detailLevelTarget`,
`speechStyleHints`, and `promptFragments` on `IdentityContext` are
built but unconsumed (P29-CAL-AUD-15, AUD-18). These must be wired
into `ResponseRealizer` and `PolishedResponseService` before
calibration modifiers have full effect.

**2. Live path IdentityContext gap**
`GeminiLiveClient` assembles `SystemPromptBuilder` without
`IdentityContext` (P29-CAL-AUD-20). The `MemoryInjectionBuilder`
behavioral constraint block is the primary mitigation. Full
`IdentityContext` integration into the Live path is a future
enhancement.

**3. RelationshipArc dependency**
`RelationshipArc` must be written by `ConsolidationLoop` step 6b
before `RelationalCalibrationAdapter` has a baseline to read.
Until the first arc write, EARLY mode is the correct default.

**4. RIL integration map clarification**
The RIL master document integration map references "ZolaIdentityProfile
expression config" as the calibration injection point. This should
be updated to "IdentityContext expression overlay via
RelationalCalibrationAdapter" — the profile itself is immutable.

---

## Known Constraints

### ZolaIdentityProfile Is Immutable

Calibration never writes `ZolaIdentityProfile` fields. The identity
seed — foundational traits, phrase avoidances, softening rules — is
permanently static. Calibration applies as an overlay at
`IdentityContext` construction time, not as a modification to the
profile. This is consistent with the Identity and Personality
Framework's core principle that personality can adapt, identity must
remain stable.

### StyleProfile Composes Within Calibration Ceiling

`StyleProfileApplicator` learned preferences are applied before the
calibration ceiling clamp. This means a strongly learned warmth
preference may be suppressed by an EARLY calibration ceiling. This
is correct behavior — earned familiarity is the constraint, learned
preference is the expression within it. If the ceiling feels too
restrictive relative to the user's actual preferences, the resolution
is for the relationship to deepen, not for the ceiling to be bypassed.

### Workspace Context Wiring Is a Parallel Track

`ResponseIdentityOrchestrator` hardcodes `CONTEXT_DEFAULT` for style
profile lookup (P29-CAL-AUD-17). Workspace context wiring is a
separate pre-existing gap. Calibration does not depend on it and
should not wait for it.

---

## Authority Boundaries

### Relational Calibration may:

- read from `RelationshipArc`, `SessionBoundaryResolver`, and
  `MemoryCorrectionLog`
- compute `CalibrationSignal` at session start
- inject ceiling clamps into `IdentityContext` via
  `ResponseIdentityOrchestrator`
- inject behavioral directive blocks into `MemoryInjectionBuilder`
- store `CalibrationSignal` in `CalibrationSignalHolder`

### Relational Calibration must not:

- write to `ZolaIdentityProfile` — the profile is immutable
- override `PersonaMode` selection — intent-based mode is independent
- write to the `RelationshipArc` — arc writes belong to
  `ConsolidationLoop`
- produce initiative candidates or autonomous output
- deliver speech through any path other than the existing prompt
  injection mechanism
- inject structural state labels into any Live prompt block

---

## Relationship to Relational Intelligence Layer

Relational Calibration is the fifth and final subsystem of the
Relational Intelligence Layer. It is the most downstream — it reads
from everything the other four subsystems produce.

It depends on:

- **Temporal Reasoning** (subsystem 1) — `SessionBoundaryResolver`
  for inter-session gap damper signal, `TemporalRecencyFormatter`
  for directive text
- **Self-Model Awareness** (subsystem 2) — correction history for
  repair register enrichment at ESTABLISHED and DEEP modes
- **Social Graph Reasoning** (subsystem 3) — informs calibration
  indirectly through `relationshipDepth` inputs from Relational
  Continuity
- **Relational Continuity** (subsystem 4) — `RelationshipArc`
  document as the primary input for both the baseline flywheel
  and the friction damper

With Relational Calibration, the Relational Intelligence Layer is
architecturally complete. The five subsystems together give Zola:

1. Awareness of how time passes and what it means
2. Honest self-knowledge about what she believes and how well
3. Dynamic models of the people in the user's life
4. A sense of the arc of her relationship with the user
5. Expression of familiarity that has been genuinely earned

---

## Long-Term End State

Relational Calibration eventually supports:

- a relationship that expresses its depth naturally — not through
  warmth settings but through the accumulation of earned context
- assumption license that makes Zola genuinely useful for a
  longtime user — executing on known preferences without the
  friction of constant confirmation
- repair registers that feel proportional to the relationship —
  brief and professional when appropriate, warm and honest when
  that has been earned
- calibration that adjusts gracefully to friction and absence
  without losing the baseline that has been built over time

The system should ultimately feel:

- familiar where familiarity has been earned
- careful where it has not
- honest in how it acknowledges the limits of its own knowledge
- consistent in never bypassing safety regardless of depth

without becoming:

- a warmth performance that assumes intimacy it hasn't earned
- a system that forgets a difficult period the moment it clears
- a presence that narrates its own calibration state
- a layer that treats earned familiarity as a bypass for
  consequential decisions

---

## Final Principle

Familiarity is not a feature to be configured. It is a quality that
is earned through time, through honesty, through getting things right
and acknowledging when things go wrong.

Relational Calibration exists to ensure that what Zola expresses
matches what has actually been built — and that the building
continues, session by session, until the relationship is as deep
as it deserves to be.
