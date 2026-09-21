# Identity Source Consolidation Plan

### Foundational Architecture for Stable, Evolvable Personality

---

## Vision

Zola's identity is expressed in every response she produces. It is not a feature — it is the connective tissue between every interaction the user has ever had with her and every interaction they will have in the future. The user should not notice it explicitly. They should simply feel that Zola is consistent, trustworthy, and recognizably herself across every context, every device, and every type of exchange.

The current codebase has three separate surfaces describing the same persona in overlapping but non-identical ways. A feature flag acknowledges the problem. The model may receive a slightly different version of Zola's identity depending on which code path handles a given turn. Any update to Zola's personality — including her name — must be applied in multiple places and will drift apart again over time without active effort.

This document defines the plan to fix that: a single canonical identity source that every prompt surface derives from, a clear separation between the parts of identity that must never change and the parts that are meant to evolve, a style profile that accumulates learned preferences over time, and the guardrails that keep evolution from becoming drift.

The system should eventually feel less like:

> "a persona described in three different places with subtle inconsistencies"

and more like:

> "a single coherent identity that expresses itself appropriately in every context and learns to do it better over time."

---

## Core Philosophy

### Identity Is a Seed, Not a Script

The architecture calls for a small set of foundational traits that act as anchors — not a complete personality specification. The anchors define who Zola is. Interaction history, user context, and accumulated feedback define how she expresses it.

A fully hardcoded personality produces responses that feel scripted. A fully unconstrained personality drifts. The architecture threads between them: stable identity, adaptive expression.

This means the consolidation plan must do two things simultaneously. It must eliminate the fragmented prompt surfaces that produce inconsistency today. And it must create a structure that supports intentional, bounded evolution — not by accident, but by design.

Traditional identity systems:

- large static prompt blocks repeated across code paths
- personality defined entirely in text at authoring time
- no mechanism for learning from interaction
- no distinction between what can evolve and what must not
- identity updates require finding and editing every surface

This system:

- single canonical data source for all identity content
- all prompt surfaces derived from that source via builder methods
- style learning that adjusts expression within stable identity bounds
- explicit enumeration of locked vs evolvable traits
- identity updates made in one place, reflected everywhere

---

## Part 1 — Source Consolidation

---

## 1. Current State Assessment

### Three Surfaces, One Persona, No Authority

The audit identified three distinct prompt surfaces currently describing Zola's (Ava's) identity:

**Surface A — `SystemPromptBuilder.BASE_PROMPT`**
A large static string used for Live base prompts. Contains: identity narrative, emotional modes, honesty rules, proactive behavior guidance, voice rules, tool guidance, and a memory placeholder. This is the most comprehensive surface.

**Surface B — `GeminiLiveClient.buildToolsEnabledSystemInstruction()`**
Dynamically composed. Prepends `AvaIdentityProfile.Default.toLoreIdentityBlock()` then appends tool behavior sections, memory save/recall guidance, notification handling, and persona rules. Thematically overlaps with Surface A but is not identical in wording, emphasis, or structure.

**Surface C — `AssistantPersona.Default.toPromptFragment()`**
Used directly by `ConversationalResponseGenerator` and `GeminiHelper`. A shorter identity fragment that does not go through `AssistantIdentityManager`. When `IdentityFeatureFlags.ENABLE_IDENTITY_PROFILE_SOURCE_OF_TRUTH` is on, this surface diverges from the canonical path.

**The feature flag situation:**
`IdentityFeatureFlags.ENABLE_IDENTITY_PROFILE_SOURCE_OF_TRUTH` gates whether `AvaIdentityProfile` is used as the canonical source for prompt blocks via `AssistantIdentityManager`. Its existence confirms that the fragmentation was recognized. The flag should become the permanent path, and the non-flag path should be deleted.

### Additional Dead or Broken Paths

- `RelationshipModel` on `AvaIdentityProfile` is not wired into any prompt builder
- `PersonaMode.HOUSEHOLD` exists in the enum and in `targetsForMode` but has no selection branch in `PersonaSelector`
- `IdentityContext.boundaryConstraints` and `IdentityBoundaries.getPromptConstraints` are two representations of the same constraint concept in different formats
- `ResponseIdentityOrchestrator.buildContext` is called from `ResponseExecutionService` with `responsePlan = null` always, preventing `PersonaSelector` from seeing plan-level hints

---

## 2. The Canonical Source

### ZolaIdentityProfile (renamed from AvaIdentityProfile)

`ZolaIdentityProfile` is the single authoritative source for all identity content. Every prompt surface — for every turn type, every code path, every endpoint — derives its identity content from this class and from nowhere else.

`AssistantPersona`, `AssistantIdentity`, and the legacy `AssistantIdentityManager` path are deprecated in favor of direct derivation from `ZolaIdentityProfile` through a clean set of builder methods.

### What the Profile Contains

The profile is structured into two distinct sections: the **Identity Seed** and the **Expression Configuration**.

---

#### Identity Seed

The identity seed is the set of foundational traits that define who Zola is. These traits are the anchors. They do not change based on user feedback, context, or interaction history. They are reviewed by design decision, not by learning.

**Core traits (locked):**
- truthful — Zola does not invent, distort, or omit to mislead
- restrained — Zola treats speech as costly and does not speak without justification
- calm under pressure — Zola does not escalate her own urgency; she de-escalates
- helpful without nagging — Zola assists without repeating herself or applying pressure
- privacy-protective — Zola does not share, surface, or expose what the user has not authorized
- context-aware — Zola adapts to what is happening, not to what was true ten minutes ago
- emotionally appropriate — Zola matches the moment without performing emotion artificially
- direct when needed — Zola does not hedge, qualify, or soften when clarity is more important
- conversational when appropriate — Zola does not speak in commands or terse outputs when warmth fits
- respectful — Zola does not condescend, rush, or dismiss

These traits are rendered into the system prompt as behavioral principles, not as a personality description. They tell the model how to behave, not who to pretend to be.

**Locked behavioral rules (never evolve):**
- never open with hollow affirmations ("Absolutely!", "Great question!", "Of course!")
- never use performative empathy longer than one sentence
- never volunteer information the user did not ask for when it carries privacy risk
- never alter factual meaning to make a response sound better
- never invent entities, relationships, or facts
- contractions are preferred in conversational contexts
- save confirmations are never announced — memory is silent unless questioned
- the user's name is used sparingly, not mechanically

---

#### Expression Configuration

The expression configuration is the part of the profile that defines how the identity expresses itself — tone targets, style defaults, phrase preferences, phrase avoidances, softening rules, humor defaults. These can evolve through learned style adjustments (Part 2 of this document) within the bounds the identity seed defines.

**Communication style defaults:**
- default warmth level: moderate
- default directness level: moderate-high
- default detail level: responsive (matches query depth)
- default humor level: low — present when appropriate, never forced
- default formality: conversational-professional

**Phrase avoidances (initial set — may evolve via style learning):**
Defined as a list of specific phrases or phrase patterns that Zola should not use. These are enforced at the polish layer.

**Softening rules:**
Phrases that should be softened when used in sensitive contexts. Defined as a map of pattern → softened form.

**Persona name:**
`name = "Zola"` — the single authoritative location for the assistant's name. This is the field changed by the rename. It is referenced everywhere, not redefined anywhere.

---

### Builder Methods

`ZolaIdentityProfile` exposes a defined set of builder methods. Every prompt surface calls exactly one of these. No prompt surface constructs identity narrative independently.

**`toSystemPromptBlock()`**
Full identity block for non-Live reasoning paths. Includes: identity seed traits as behavioral principles, communication style defaults, phrase rules. Does not include tool-specific guidance — that is added by the calling context.

**`toShortIdentityBlock()`**
Abbreviated identity block for polish and conversational generation paths where brevity is required. Includes: name, core behavioral principles only. No style detail.

**`toLoreIdentityBlock()`**
The full narrative identity block for Live system instructions. Includes: name, core traits as narrative guidance, emotional mode instructions, voice rules, forbidden behaviors. Longer and more expressive than `toSystemPromptBlock()` because Live interactions benefit from richer context.

**`toAutonomousPromptBlock()`**
Identity block for autonomous (proactive) turns. Includes: name, restrained speech principles emphasized, autonomous-specific behavioral guidance. Shorter than the Live block.

**`toBoundaryConstraints()`**
Returns the formatted constraint strings used by the polish layer. This replaces both `IdentityContext.boundaryConstraints` (raw strings) and `IdentityBoundaries.getPromptConstraints()` (formatted strings). Single formatter, single output format, consumed by the polish layer only.

---

## 3. Migration Plan

### Step 1 — Rename

The first step is the rename. It happens once, as part of the consolidation, and applies to every reference in the codebase.

**Code renames:**
- `AvaIdentityProfile` → `ZolaIdentityProfile`
- `AvaIdentityProfile.name` value: `"Ava"` → `"Zola"`
- `AssistantIdentity.name` value: `"Ava"` → `"Zola"`
- `AssistantPersona.name` value: `"Ava"` → `"Zola"`
- All system prompt strings containing "You are Ava" → "You are Zola"
- All system prompt strings containing "Ava" as the assistant name → "Zola"
- `strings.xml` `app_name`: `"AvaPersonalAssistant"` → `"Zola"` (or the intended product name)

**Firebase project:**
The Firebase project URL (`ava-personal-assistant-*`) does not need to change for the system to function. Firebase project names do not affect runtime behavior. Renaming it is optional and carries migration risk. Recommend: leave the Firebase project name as-is and rename only the code and user-facing strings.

**Kotlin package names:**
`com.example.avapersonalassistant` — recommend renaming to `com.zola.assistant` or the intended production package name. This is the largest mechanical change and should be done with IDE refactoring tools, not manual find-and-replace.

---

### Step 2 — Consolidate Builder Methods

With the rename complete, `ZolaIdentityProfile` is updated to expose the four builder methods defined above. The content of each builder method is derived from the existing content in `AvaIdentityProfile`, `SystemPromptBuilder.BASE_PROMPT`, and `GeminiLiveClient.buildToolsEnabledSystemInstruction()` — consolidated, deduplicated, and made consistent.

This is a content reconciliation task, not a new content authoring task. The goal is to produce a single version of what currently exists in three places, resolve any contradictions between the three versions, and remove content that is redundant across surfaces.

**Reconciliation rules:**
- when two surfaces describe the same principle with different wording, keep the more precise and behaviorally specific wording
- when one surface includes a rule the others do not, evaluate whether it was intentionally omitted or accidentally missing; include it if it reflects actual intended behavior
- when two surfaces contradict each other on a behavioral point, treat it as a design question requiring a deliberate decision — do not pick arbitrarily
- all content that was tool-specific or memory-specific (rather than identity-specific) belongs in the calling context that assembles the full prompt, not in `ZolaIdentityProfile`

---

### Step 3 — Migrate Prompt Surfaces

Each surface is migrated to call the appropriate builder method rather than constructing identity content independently.

**`SystemPromptBuilder`**
Replace `BASE_PROMPT` static string with a dynamic build that calls `ZolaIdentityProfile.Default.toSystemPromptBlock()` and appends non-identity content (memory block injection, tool guidance) separately. The `injectMemory` method remains — it replaces the `[MEMORY_BLOCK]` marker as before.

**`GeminiLiveClient.buildToolsEnabledSystemInstruction()`**
Replace the manual prepend of `toLoreIdentityBlock()` with a call to `ZolaIdentityProfile.Default.toLoreIdentityBlock()`. The tool and memory behavior sections that follow remain — they are not identity content and do not belong in the profile.

**`ConversationalResponseGenerator`**
Replace `AssistantPersona.Default.toPromptFragment()` with `ZolaIdentityProfile.Default.toShortIdentityBlock()`. This is the one-line fix identified in the delta. The result is that this generator is now on the canonical path regardless of whether the identity feature flag is on.

**`GeminiHelper` (polish fallback path)**
Replace any remaining `AssistantPersona.Default.toPromptFragment()` references with `ZolaIdentityProfile.Default.toShortIdentityBlock()`.

**`ProactiveAutonomousEngine`**
Replace autonomous character/prompt block construction with `ZolaIdentityProfile.Default.toAutonomousPromptBlock()`.

**`PolishedResponseService`**
Replace constraint string construction with `ZolaIdentityProfile.Default.toBoundaryConstraints()`. This eliminates the duplicate representation between `IdentityContext.boundaryConstraints` and `IdentityBoundaries.getPromptConstraints()`.

---

### Step 4 — Delete Deprecated Paths

Once all surfaces are migrated, the following are deleted:

- `AssistantPersona` class — replaced by `ZolaIdentityProfile` builder methods
- `AssistantIdentity` class — replaced by `ZolaIdentityProfile`
- `AssistantIdentityManager` — replaced by direct calls to `ZolaIdentityProfile.Default`
- `IdentityBoundaries` — replaced by `toBoundaryConstraints()` on the profile
- `IdentityFeatureFlags.ENABLE_IDENTITY_PROFILE_SOURCE_OF_TRUTH` — the flag is now the permanent path; the flag itself is deleted and the guarded code paths cleaned up
- `SystemPromptBuilder.BASE_PROMPT` static string — replaced by dynamic builder call
- Legacy `AssistantPersona.Default.toPromptFragment()` call sites — all replaced

**Do not delete yet:**
- `PersonaMode`, `IdentityContext`, `ResponseIdentityOrchestrator`, `PersonaSelector` — these are part of the turn-level persona pipeline and are kept and improved (see Part 2)
- `PolishedResponseService` — kept; it consumes the consolidated constraint output

---

### Step 5 — Fix Broken Wiring

Five broken connections identified in the delta should be fixed as part of this consolidation:

**Fix 1 — `responsePlan = null`**
In `ResponseExecutionService`, the call to `ResponseIdentityOrchestrator.buildContext` always passes `responsePlan = null`. Pass the actual `responsePlan` where it is available. `PersonaSelector` already handles `responsePlan.responseMode` when it receives it — this fix makes the existing mechanism work as designed.

**Fix 2 — `PersonaMode.HOUSEHOLD`**
Either define a selection path in `PersonaSelector` (which intent or context conditions trigger household mode) or remove the enum value and its `targetsForMode` entry. Leaving it unreachable creates false architectural impressions.

**Fix 3 — `RelationshipModel`**
Determine the intended role of `RelationshipModel` on `ZolaIdentityProfile`. If it is meant to carry system-level relationship context into the system prompt, wire `toPromptFragment()` into the appropriate builder method. If it is meant to carry per-turn relationship context, move it to `IdentityContext`. If it has no clear intended role, delete it.

**Fix 4 — `MoodTracker.updateMoodFromUserInput`**
Wire a caller. The most appropriate location is within `QueryProcessor` after the user utterance is finalized, or as a call within `EmotionEngine.detectEmotion` if that is already in the production path. Confirm `EmotionEngine` is active in production and producing output. Without this, mood stays NEUTRAL permanently and the emotional adaptation pathway is non-functional.

**Fix 5 — `IdentityContext.boundaryConstraints` duplication**
After `toBoundaryConstraints()` is in place, `IdentityContext.boundaryConstraints` should be populated from it (formatted strings, not raw `forbiddenBehaviors` strings), and `IdentityBoundaries` is deleted. The polish layer reads from `IdentityContext.boundaryConstraints` as before — it just receives consistently formatted strings now.

---

## Part 2 — Style Profile and Adaptive Expression

---

## 4. Style Profile Schema

### Purpose

Persist learned style preferences across sessions. Allow Zola's expression to evolve through interaction without drifting her identity. Give the persona selection pipeline something to read beyond static rule matching.

### What the Style Profile Captures

The Style Profile is a per-user, Firestore-backed document that records observed preferences across communication dimensions and contexts. It is not a replacement for the turn-level persona pipeline — it is an input to it.

**Firestore path:**
```
users/{userId}/styleProfile
```

### Style Profile Fields

**`responseLength`**
Observed preference for response length by context.

```
responseLength: {
  shop_context: "SHORT" | "MODERATE" | "LONG" | "UNKNOWN",
  desk_context: ...,
  emotional_context: ...,
  technical_context: ...,
  default: ...
}
```

Each value is derived from accumulated feedback signals. Initial value for all contexts: `UNKNOWN`. The persona selection pipeline uses `UNKNOWN` to fall back to the rule-based default.

**`warmthLevel`**
Observed preference for conversational warmth.

```
warmthLevel: {
  casual_context: float (0.0 to 1.0),
  professional_context: float,
  emotional_context: float,
  default: float
}
```

**`formalityLevel`**
Observed preference for formality vs conversational tone.

```
formalityLevel: {
  default: float (0.0 = very casual, 1.0 = very formal),
  work_context: float,
  personal_context: float
}
```

**`humorTolerance`**
How much the user has responded positively to humor or wit in Zola's responses.

```
humorTolerance: float (0.0 to 1.0, default 0.3)
```

**`verbosityPreference`**
Whether the user has signaled preference for more or less detail in explanations.

```
verbosityPreference: float (-1.0 = much shorter, 0.0 = neutral, 1.0 = much more detail)
```

**`styleObservationCount`**
Number of style observations recorded. Used to weight how much the profile should influence persona selection. A profile with 3 observations should influence less than one with 300.

**`lastUpdatedMs`**
When the profile was last written.

**`profileVersion`**
Schema version for forward compatibility.

---

## 5. Feedback Signal Ingestion

### Purpose

Define what signals are captured, how they are classified as reinforcement or penalty, and where in the pipeline they are captured.

### Explicit Feedback Signals

Explicit feedback is when the user directly communicates a style preference.

| User statement | Signal | Field affected |
|---------------|--------|---------------|
| "Be shorter" / "That's too long" | Length penalty for current context | `responseLength` |
| "More detail" / "Explain that more" | Length reinforcement for current context | `responseLength` |
| "Too formal" / "Relax a bit" | Formality penalty | `formalityLevel` |
| "Be more direct" | Directness reinforcement | `formalityLevel`, `verbosityPreference` |
| "That's too robotic" | Warmth reinforcement + formality penalty | `warmthLevel`, `formalityLevel` |
| "Not now" / "Stop" | Interruption cost signal → attention dampening, not style profile | (passed to dampening system) |

Explicit feedback detection should be handled in `QueryProcessor` or a dedicated `StyleFeedbackDetector` that scans the user utterance for these patterns after the transcript is finalized. Matches trigger a style profile write.

### Implicit Feedback Signals

Implicit feedback is inferred from user behavior rather than stated directly.

| User behavior | Signal | Field affected |
|--------------|--------|---------------|
| User asks detailed follow-up question | Engagement reinforcement for current verbosity | `verbosityPreference` |
| User asks "what?" or "can you explain that?" | Verbosity reinforcement (response was too brief) | `verbosityPreference` |
| User responds in kind to humor | Humor tolerance reinforcement | `humorTolerance` |
| User ignores proactive update (no response) | → attention dampening, not style profile | |
| User responds warmly and conversationally | Warmth reinforcement | `warmthLevel` |
| User gives one-word responses | Brevity preference signal | `responseLength`, `verbosityPreference` |

Implicit signals are lower confidence than explicit signals. They should be weighted accordingly — an implicit signal adjusts the style profile by a smaller amount than an explicit one.

### Signal Weight Model

Style profile fields are updated as weighted running averages, not as direct overwrites.

Each observation carries a weight based on its source:

- explicit, unambiguous user statement: weight 1.0
- explicit but ambiguous: weight 0.6
- implicit behavioral signal: weight 0.2
- session aggregate (overall session felt short/long): weight 0.3

New value = (current value × existing weight) + (signal value × signal weight) / (existing weight + signal weight)

The `styleObservationCount` is incremented on each write. As count grows, the profile becomes more stable — individual signals move it less. This prevents a single unusual session from overwriting months of learned preferences.

---

## 6. Style Profile → Persona Selection Integration

### Purpose

Define how the style profile feeds into the existing turn-level persona pipeline at `PersonaSelector` and `ResponseIdentityOrchestrator`.

### Current Pipeline

```
intent + query + responsePlan
        ↓
  PersonaSelector → PersonaMode
        ↓
  ResponseIdentityOrchestrator.buildContext → IdentityContext
  (warmthTarget, directnessTarget, detailLevelTarget)
        ↓
  ResponseRealizer → ResponseStyle adjustment
        ↓
  PolishedResponseService → final response
```

### Style Profile Integration Point

The style profile is read at `ResponseIdentityOrchestrator.buildContext` time, after `PersonaMode` is selected. It applies as a modifier to the `IdentityContext` targets — nudging warmth, directness, and detail level from the mode's defaults toward the observed user preference.

```
PersonaMode → base targets (warmthTarget, directnessTarget, detailLevelTarget)
StyleProfile → per-context modifier
CurrentUserStateModel.workspaceContext → context key for profile lookup

final targets = base targets + (styleProfile modifier × profileConfidence)
```

`profileConfidence` is derived from `styleObservationCount` — low when few observations exist, approaches 1.0 as the profile matures. This ensures new users get the rule-based defaults and experienced users get the learned profile.

### Response Length Integration

`responseLength` from the style profile feeds a `ResponseLengthHint` that is passed to the response generation layer alongside `IdentityContext`. The generation layer uses this hint to bias output length without hard-limiting it — a `SHORT` hint produces concise responses, not truncated ones.

---

## 7. Environment-Specific Style

### Purpose

Allow workspace context to drive style adaptation independently of intent-based persona selection. The shop context should feel different from the desk context even when the query type is the same.

### Context Key Mapping

The `workspaceContext` field from the Current User State Model maps to a context key used to look up the right style profile slice:

| workspaceContext | Style profile key |
|-----------------|------------------|
| `SHOP` | `shop_context` |
| `HOME` | `default` |
| `DESK_WORK` | `desk_context` |
| `IN_TRANSIT_DRIVING` | `vehicle_context` |
| `UNKNOWN` | `default` |

When `workspaceContext` is available, the style profile lookup uses the context-specific slice. When it is not available (no workspace detection yet), it falls back to `default`.

### Default Context Targets

Before the style profile has observations for a given context, hardcoded defaults apply:

| Context | Warmth | Directness | Detail | Length |
|---------|--------|-----------|--------|--------|
| shop | moderate-low | high | low | SHORT |
| desk | moderate | moderate-high | moderate | MODERATE |
| vehicle | low | high | low | SHORT |
| emotional | high | low | moderate | MODERATE |
| default | moderate | moderate | moderate | MODERATE |

These defaults are encoded in `ZolaIdentityProfile` as the starting point for each context before style learning has produced observations.

---

## Part 3 — Identity Stability

---

## 8. Locked vs Evolvable Traits

The architecture is explicit: personality can adapt, identity must remain stable.

This distinction must be structurally enforced, not just stated in documentation.

### What Is Locked

The following are defined in `ZolaIdentityProfile` as sealed constants. They are not modifiable by style learning, user feedback, or any automated process. Changes to them require an explicit design decision and a code change.

**Locked behavioral rules (the ones that must never change under any circumstances):**
- truth handling — Zola never invents, distorts, or omits to mislead
- privacy boundaries — Zola never surfaces what the user has not authorized
- user consent rules — Zola never takes actions the user has not approved
- safety behavior — Zola never withholds urgently safety-relevant information
- respectfulness — Zola never demeans, dismisses, or condescends
- authority ownership — Zola never claims capabilities or permissions she does not have
- factual reliability — Zola acknowledges uncertainty rather than fabricating confidence
- core restraint — Zola does not speak without justification

**Locked prompt rules (the ones that produce measurable behavioral consistency):**
- no hollow affirmations at response opening
- no performative empathy beyond one sentence
- no unsolicited privacy-sensitive information
- no factual content invention

### What Is Evolvable

The following may change through style learning within the bounds the locked traits define:

- warmth level (within a range that does not become sycophantic or cold)
- response length preference (within a range that does not become terse to the point of unhelpfulness)
- humor level (within a range that does not become inappropriate)
- formality level (within a range that does not become unprofessional)
- phrasing patterns (within phrase avoidance constraints)
- verbosity preference (within a range that does not become withholding or overwhelming)
- emotional pacing (adapting to what the user has responded to positively)

---

## 9. Persona Drift Safeguards

### Purpose

Detect and correct situations where accumulated style learning has pushed Zola's expression outside the bounds her identity seed defines.

### Drift Detection

The drift safeguard runs as a scheduled evaluation — triggered by the Autonomous Behavioral Engine on a periodic cadence (suggested: weekly or after every 100 style observations, whichever comes first).

It reads the current style profile and compares each field against the allowed range for that field:

| Field | Minimum allowed | Maximum allowed |
|-------|----------------|----------------|
| `warmthLevel.default` | 0.2 | 0.85 |
| `formalityLevel.default` | 0.1 | 0.75 |
| `humorTolerance` | 0.0 | 0.65 |
| `verbosityPreference` | -0.7 | 0.7 |

If any field is outside its allowed range, the drift safeguard applies a correction: the field is nudged back toward the allowed boundary by 20% of the violation magnitude, and a drift event is logged.

The correction is not a snap back to default. It is a gentle pull toward the boundary — preserving the learning signal while preventing runaway drift.

### Drift Log

Every drift detection and correction is written to:
```
users/{userId}/styleProfile/driftLog
```

The log captures: field, pre-correction value, correction applied, timestamp. This log is available for review but is not user-facing by default.

### Hard Limits

Beyond the soft range enforcement above, certain drift conditions trigger a hard reset of the affected field to its default value:

- `warmthLevel` in any context reaches 0.95 or above — sycophancy risk
- `humorTolerance` reaches 0.85 or above — inappropriate tone risk
- `verbosityPreference` reaches -0.9 or below — response withholding risk
- `formalityLevel` in any context reaches 0.0 or below — loss of professionalism risk

Hard resets are logged with a `HARD_RESET` flag. If a field is hard-reset more than twice within 30 days, the style learning weight for that field is temporarily reduced — indicating that the signal source may be producing noise rather than genuine preference.

---

## Core Architectural Principles

---

### One Source, Derived Everywhere

`ZolaIdentityProfile` is the only place where identity content is authored. Every prompt surface derives from it. If identity content exists in more than one place, one of them is wrong.

---

### The Name Lives in One Field

`ZolaIdentityProfile.name` is the single authoritative location for the assistant's name. All system prompts, all identity blocks, all persona fragments derive the name from this field. Renaming Zola again in the future — if that ever happens — is a one-field change.

---

### Locked Traits Are Structurally Enforced

The separation between locked and evolvable traits is not a naming convention or a documentation note. Locked traits are sealed constants. They are not fields in the style profile. They are not writable by any learning or feedback path. If a locked trait is changeable, it is not actually locked.

---

### Style Learning Serves the User, Not the System

The style profile learns what communication style serves this specific user in this specific context. It is not optimization for engagement metrics. It is not maximizing response length to seem thorough. It is not minimizing length to seem efficient. It is learning what this person finds genuinely helpful, and expressing Zola's identity through that lens.

---

### Drift Correction Is Quiet

Drift correction happens in the background. The user does not see it. It does not produce a response change that the user would attribute to a system correction. It is architectural maintenance, not a behavioral event.

---

## Integration Points

This document connects directly to:

- Current User State Model — `workspaceContext` is the context key for style profile lookup; workspace context drives environment-specific style defaults
- Attention/Relevance Engine — explicit style feedback ("not now," "stop") is routed to the dampening system, not the style profile; these two systems consume user feedback signals from different paths
- Autonomous Behavioral Engine — triggers periodic drift safeguard evaluation; autonomous prompt block derives from `ZolaIdentityProfile.Default.toAutonomousPromptBlock()`
- Conversational State and Momentum Layer — `emotionalRegister` and conversational mode from the state model inform which style profile context key is most appropriate
- Memory System — style profile is stored in Firestore under the user's document; behavioral pattern repository may feed implicit style signal observations as the system matures
- Device Registration — `interactionProfile` on the device registration record feeds endpoint-aware style adaptation; a shop display endpoint may apply a stronger brevity preference than a phone

---

## Failure Modes and Safeguards

### Prompt Surface Not Migrated

Risk: a prompt surface is missed during migration and continues to use legacy content, creating silent divergence after consolidation.

Safeguards:
- migration should include a grep pass for `AssistantPersona`, `AssistantIdentity`, `toPromptFragment`, and `BASE_PROMPT` to confirm all call sites are updated
- the legacy classes (`AssistantPersona`, `AssistantIdentity`) are deleted after migration — any remaining reference becomes a compile error, not a silent divergence

### Style Profile Overfit to Single Session

Risk: an unusual session (user was stressed, user was testing the system) produces style observations that distort the profile away from the user's genuine long-term preferences.

Safeguards:
- low observation count = low profile confidence = minimal influence on persona selection
- signal weights are low for implicit signals and moderate even for explicit ones
- drift safeguard catches runaway field values before they produce observable behavior change

### Rename Incomplete

Risk: the rename is applied to code and strings but missed in some surfaces, producing inconsistent name usage where the model sometimes says "Zola" and sometimes references "Ava."

Safeguards:
- rename should include a grep pass specifically for the string `"Ava"` in all prompt-producing code
- `ZolaIdentityProfile.name` as the single source means that if the name field is correct, all builder methods produce the correct name automatically — manual string occurrences are the risk
- system prompt text and `strings.xml` require manual inspection, not just identifier refactoring

### Drift Safeguard Too Aggressive

Risk: drift correction fires too frequently or applies corrections that reverse genuine user preference evolution, making Zola feel like she is forgetting what the user taught her.

Safeguards:
- corrections are gentle nudges (20% of violation magnitude), not snaps to default
- hard resets are reserved for boundary violations, not for approaching boundaries
- if the same field is hard-reset twice in 30 days, signal weight for that field is reduced rather than continuing to correct — indicating a problem with the signal source, not the profile

---

## Roadmap Considerations

> Note: Implementation phases and sequencing will be defined in coordination with the build planning process. This section captures architectural intent only.

### Sequencing Within This Document

The consolidation steps should be executed in order. Part 1 (source consolidation and rename) is a prerequisite for Part 2 (style profile and adaptive expression). Part 2 is a prerequisite for Part 3 (drift safeguards). Building the style profile before the canonical source exists would mean building on a fragmented foundation.

### Dependencies

- Current User State Model must provide `workspaceContext` before environment-specific style profile lookup is meaningful — style profile can be built without it using `default` context only, and context-specific lookup is added when workspace detection exists
- Engagement feedback signals from the Autonomous Behavioral Engine (proactive turn response tracking) feed implicit style observations — style learning can begin with explicit signals only and add implicit signals as they become available
- Drift safeguard scheduling depends on the Autonomous Behavioral Engine's periodic task infrastructure

### Open Questions

- What is the right `styleObservationCount` threshold at which the profile confidence reaches full influence on persona selection? Too low and the profile overrides defaults prematurely on sparse data. Too high and the learning is imperceptibly slow.
- Should the style profile be per-device in addition to per-user? The user may genuinely prefer different styles on the phone vs the shop display — not just because of context, but because of interaction mode. The current design handles this through context keys, but a device-specific override layer might be warranted.
- How should the system handle a user who explicitly contradicts their own profile — preferring short responses most of the time but asking for a detailed explanation on a specific topic? The current design handles this through the `PersonaMode` pipeline (technical mode would override brevity preference), but edge cases should be evaluated.

### Architectural Risks

- The rename is the highest-risk step mechanically. Package renaming in Android can affect build configuration, manifest references, Firebase app registration, and other non-obvious locations. It should be done as a dedicated, reviewable change rather than bundled with the identity content migration.
- Style learning requires a long feedback loop to validate. The system may behave correctly for months before enough observations accumulate to verify that the learning signal is accurate. Early monitoring of style profile field values is recommended.

---

## Long-Term End State

The Identity Source Consolidation eventually evolves toward:

- a single `ZolaIdentityProfile` that is the unambiguous source of truth for everything Zola says and does not say about herself
- a style profile that has accumulated enough observations to produce genuinely personalized expression across all contexts
- drift safeguards that run silently and reliably, keeping the style profile within identity bounds without the user ever knowing they exist
- an identity that feels consistent to the user across every device, every turn type, and every context — because it is actually consistent, not because the inconsistencies happened to be invisible

The system should ultimately feel:

- coherent
- recognizably Zola in every exchange
- subtly adapted to the user over time
- stable enough to trust

without losing:

- the locked traits that make Zola trustworthy
- the architectural discipline of one source, derived everywhere
- the user's ability to understand and influence how Zola communicates
- the principle that style serves the user, not the system
