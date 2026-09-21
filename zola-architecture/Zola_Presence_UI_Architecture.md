# Zola Presence UI Architecture Plan

## Foundational Roadmap for Entity-Based Interface and Functional Presence

---

## Vision

Zola is not intended to feel like a traditional assistant app with a decorative avatar.

The long-term goal is to create a persistent visual embodiment for Zola that supports:

- entity-like presence
- voice-first interaction
- contextual awareness
- ambient system state
- functional UI surfaces
- procedural visual life
- environmental responsiveness
- restrained attention behavior
- distributed endpoint adaptation
- emotionally appropriate visual expression

The interface should eventually feel less like:

> "an app screen with an assistant graphic"

and more like:

> "a persistent intelligence manifesting through the interface."

---

## Core Philosophy

## Presence-First Interface

Zola's visual system should begin with presence, not controls.

The user should feel that Zola is already there, aware, and available before any menu, button, panel, or text input appears.

Traditional assistant UI patterns emphasize:

- search bars
- command boxes
- chat history
- static icons
- tap-first controls
- full-screen menus

Zola's interface should emphasize:

- persistent manifestation
- voice-first interaction
- contextual surfaces
- minimal visible controls
- state-driven animation
- environmental reactivity
- restrained visual attention
- functional UI only when needed

---

## Canonical Visual Direction

Zola's primary visual identity is defined by the approved obsidian holographic entity concept.

The canonical reference asset is:
`zola-architecture/assets/zola_presence_ui_reference.svg`

This SVG is a layered vector blueprint. Its element IDs map directly to Compose layer names. Its gradient definitions, path coordinates, and color stops are the authoritative source for all Canvas draw calls. Cursor must read this file before implementing any render layer.

### Core Visual Traits

- dark obsidian background with radial warm center glow
- amber/gold holographic light throughout
- African-inspired feminine entity presence
- upper torso manifestation with holographic skin gradient
- stylized rather than realistic human rendering
- pixelated projection structure at body edges
- luminous amber eyes with strong inner glow
- asymmetric energy-like hair rendered as flowing stroke paths
- geometric diamond chest core with strong glow
- floating particle field with subtle rings
- minimal but precise HUD panels left and right
- bottom dock — contextual, not always visible, no permanent text bar

### Font Requirements

The HUD and dock use `Rajdhani` (primary) and `Orbitron` (wordmark/accent).
Both are Google Fonts and must be declared as downloadable fonts in the Android
project before any HUD text composables are built. Font setup is a prerequisite
step in the Wave 2 prompt. Do not use system fonts as substitutes.

### Important Principle

The reference SVG and reference image are the canonical visual targets.

Cursor must not reinterpret Zola's visual identity, generate a new design direction, or replace the manifestation with a generic avatar.

The goal is to recreate the approved obsidian holographic presence as a living, functional Compose interface.

---

## 1. Presence Layer

### Purpose

Render Zola as a persistent entity rather than a static assistant graphic.

This layer owns the central manifestation, including the holographic body, eyes, hair, glow, particles, and idle life.

### Responsibilities

- render central Zola manifestation
- maintain visual presence during idle states
- express listening, thinking, speaking, and alert states
- provide procedural breathing and subtle motion
- keep the entity visually alive without requiring video or cloud animation
- avoid uncanny realism
- maintain visual restraint

### Render Components

- `ZolaPresenceRenderer`
- `PresenceVisualState`
- `ZolaRenderLayers`
- `PresenceAnimationController`
- `ManifestationCoreLayer`
- `FaceLayer`
- `EyeLayer`
- `MouthLayer`
- `HairEnergyLayer`
- `PixelProjectionLayer`
- `HologramDistortionLayer`
- `ParticleFieldLayer`
- `CoreGlowLayer`

### Important Principle

Zola should feel alive because her visuals respond to internal state, not because a canned animation is playing.

---

## 2. Static Visual Reconstruction

### Purpose

Recreate the approved Zola concept as closely as possible in Jetpack Compose before introducing animation.

This prevents implementation drift.

### Responsibilities

- reproduce the obsidian/gold visual language
- recreate central manifestation layout from SVG coordinates
- recreate side HUD structure
- recreate bottom dock structure
- recreate glow, grid, and particle styling
- preserve proportions and visual hierarchy
- avoid redesigning the concept

### Implementation Strategy

The first implementation wave creates a static Compose reconstruction using:

- Canvas drawing with coordinates derived from `zola_presence_ui_reference.svg`
- layered composables matching SVG layer IDs
- gradients matching SVG gradient definitions
- alpha blending
- blur effects
- glow overlays
- simple vector geometry
- reusable design tokens

### Non-Goals

- no new avatar design
- no realistic 3D model
- no full character rig
- no generated replacement image
- no Lottie dependency as the primary animation path
- no cloud-rendered animation engine

### Important Principle

Static visual parity comes before animation.

If the still frame does not feel like Zola, motion will not fix it.

---

## 3. Procedural Life System

### Purpose

Make Zola feel alive using lightweight, local, procedural animation driven by system state.

### Core Animation Sources

- asymmetric sine breathing curve
- damped spring motion
- noise functions
- audio amplitude
- state transitions with staggered timing
- decay curves
- particle drift
- glow interpolation
- randomized micro-movement timers

### Cognitive Heartbeat

The central presence has a subtle procedural breathing motion driven by an
asymmetric sine curve — inhale occupies 40% of the cycle with ease-in, exhale
occupies 60% of the cycle with ease-out. This asymmetry is what makes breathing
feel organic rather than mechanical.

Idle state should feel calm and slow.

Thinking or active cognition increases internal motion without becoming frantic.

The breath scale applies to chest core glow, torso light intensity, and subtle
projection density only — not the whole body. Full-body scale produces an
unnatural bobbing effect.

### Momentum Glow

Conversation momentum and topic heat drive subtle increases in glow intensity,
manifestation density, or particle activity.

As a conversation becomes active, Zola should visually warm up.

As momentum decays, the glow should gradually settle.

### Attention Leaning

When Zola detects that speech is likely directed at her, the manifestation may
slightly lean forward, brighten, or sharpen.

This should use spring-like motion rather than abrupt jumps.

### Environmental Jitter

Environmental noise or degraded listening conditions may introduce subtle pixel
instability, edge shimmer, or projection noise.

This gives the user a silent visual cue that the environment is affecting perception.

### Idle Personality System

When nothing is happening — no speech, no mode change, no attention signal —
Zola must still feel present rather than frozen.

The idle personality system is self-contained, requires no backend connection,
and runs on internal timers only:

- occasional slow micro-saccade eye drift every 4–8 seconds
- a deeper breath cycle every 30–40 seconds (brief amplitude increase then settle)
- a subtle glow shift on a slow randomized timer
- hair strand shimmer on staggered independent timers

This system is the difference between a person sitting still in a room and a
cardboard cutout. Both are motionless most of the time; only one reads as alive.

### Important Principle

Motion should be meaningful.

Zola should not animate just to look busy.

---

## 4. Animation Architecture

### Pipeline

All animation in the presence UI follows a strict state-down pipeline:

```
Zola runtime state
        ↓
PresenceStateAdapter
        ↓
PresenceVisualState
        ↓
PresenceAnimationControllers
        ↓
Compose Canvas Layers
```

No layer reads from the layer above it. No layer knows about the whole app.
Each layer receives only the render state it needs.

### Two-Version State Model

`PresenceVisualState` has two distinct concerns that must not be collapsed:

**`PresenceVisualState`** — what composables read. Pure UI state. No cognitive
class imports anywhere in this type or its consumers.

**`PresenceStateAdapter`** — translates backend signals into `PresenceVisualState`.
This is the only place where cognitive values (`currentHeat`, `attentionConfidence`,
`speechAmplitude` from `AudioOrchestrator`) are allowed. The adapter normalizes
these values into UI-safe floats before any composable sees them.

Composables never see `currentHeat` directly. They see `breathingRate` or
`glowIntensity` that the adapter derived from it.

### PresenceVisualState Model

```kotlin
data class PresenceVisualState(
    val mode: PresenceMode,
    val speechAmplitude: Float,       // 0.0–1.0, from AudioOrchestrator via adapter
    val attentionConfidence: Float,   // 0.0–1.0
    val cognitiveLoad: Float,         // 0.0–1.0, derived from currentHeat
    val environmentalNoise: Float,    // 0.0–1.0
    val breathingRateHz: Float,       // derived from mode
    val glowIntensity: Float,         // derived from mode + momentum
    val manifestationDensity: Float,
    val eyeLuminance: Float,
    val attentionLean: Float,
    val pixelJitter: Float,
    val mouthOpenness: Float,
    val blinkSuppression: Float,
    val emotionalWarmth: Float,
    val urgencySharpness: Float
)
```

**Normalization contract:** All fields in `PresenceVisualState` are normalized
UI-safe values. They are never raw backend objects or unprocessed signals.

- `speechAmplitude` is not a raw audio buffer value — it is a normalized float
  in 0.0–1.0 derived by `PresenceStateAdapter` from `AudioOrchestrator` output.
- `attentionConfidence` is not a raw engine score — it is a normalized float
  derived from `AttentionRelevanceEngine` output.
- `cognitiveLoad` is derived from `AttentionDampeningController.currentHeat`,
  not passed through directly.
- `environmentalNoise` is derived from `EnvironmentalEventBus` signal quality,
  not a raw bus value.

No cognitive types, raw audio data, or architecture objects cross the adapter
boundary. Composables may assume all fields are safe floats in the stated range.

In Wave 2 and Wave 3, `speechAmplitude` and cognitive fields are stubbed with
mock values. Real wiring through `PresenceStateAdapter` happens in Wave 7.

### PresenceMode

```kotlin
enum class PresenceMode {
    IDLE,
    LISTENING,
    THINKING,
    SPEAKING,
    ALERT
}
```

### Layer Render States

Each layer receives only its own scoped render state — not the full
`PresenceVisualState`. This enforces the principle that no layer knows the
whole app:

- `EyeLayer` receives `EyeRenderState`
- `MouthLayer` receives `MouthRenderState`
- `CoreBreathingLayer` receives `BreathingRenderState`
- `HairEnergyLayer` receives `HairRenderState`
- `ParticleFieldLayer` receives `ParticleRenderState`

`ZolaPresenceRenderer` assembles the full `PresenceVisualState` and derives
each layer's scoped render state before passing it down.

---

## 5. Animation Controllers

### Purpose

Each controller owns one animation concern. Controllers are composable functions
or remembered state holders. They do not know about each other.

### BlinkController

Randomized irregular blink timer. Blink is suppressed in ALERT mode.

```
interval: Random 2500–7500ms
blink progress: 0.0 (open) → 1.0 (closed) → 0.0 (open)
duration: ~150ms close, ~100ms open
implementation: Animatable with LaunchedEffect timer loop
```

Blink suppression is a float from `PresenceVisualState.blinkSuppression` —
values above 0.8 disable the blink timer entirely.

### MicroSaccadeController

Involuntary eye drift. This is the single most important thing that makes eyes
feel alive. Without it, even a blinking eye reads as a graphic.

```
interval: Random 1000–3000ms
displacement: max 5px in any direction
motion: spring settle (DampingRatioMediumBouncy, StiffnessMedium)
implementation: Animatable with randomized target per tick
```

Runs independently of blink. Both controllers update `EyeRenderState` and
`ZolaPresenceRenderer` merges them before passing to `EyeLayer`.

### BreathingController

Asymmetric sine curve. Inhale 40% of cycle, exhale 60%.

```kotlin
val breathingRate = when (state.mode) {
    PresenceMode.IDLE      -> 0.5f
    PresenceMode.LISTENING -> 0.75f
    PresenceMode.THINKING  -> 1.4f
    PresenceMode.SPEAKING  -> 1.0f
    PresenceMode.ALERT     -> 0.25f
}
```

Output `breathScale` applies to: chest core glow radius, torso light intensity,
projection density. Not applied to full body scale.

```
breathScale range: 1.0f ± 0.018f
glowPulse range:   0.65f + 0.12f * sin(phase)
```

### MouthMotionController

Amplitude-based mouth openness with spring physics.

```kotlin
val mouthOpen by animateFloatAsState(
    targetValue = state.speechAmplitude
        .coerceIn(0f, 1f)
        .let { it * 0.65f },
    animationSpec = spring(
        dampingRatio = Spring.DampingRatioMediumBouncy,
        stiffness = Spring.StiffnessMedium
    )
)
```

Mouth drawn as a cubic bezier path. `mouthOpen` drives the vertical
displacement of the center control points. Gives a convincing speaking
impression without phoneme-level lip sync.

In Wave 3 this is stubbed with mock amplitude. Real `AudioOrchestrator` wiring
happens in Wave 8.

### ExpressionMapper

Maps `PresenceMode` to `ExpressionPose` float targets. Animated with
`animateFloatAsState` per field.

```kotlin
data class ExpressionPose(
    val browTension: Float,
    val eyelidOpenness: Float,
    val mouthCurve: Float,
    val eyeSoftness: Float,
    val projectionStability: Float
)

fun expressionFor(mode: PresenceMode): ExpressionPose = when (mode) {
    PresenceMode.IDLE      -> ExpressionPose(.15f,  .75f,  .05f, .80f, .95f)
    PresenceMode.LISTENING -> ExpressionPose(.25f,  .90f,  .00f, .70f, .98f)
    PresenceMode.THINKING  -> ExpressionPose(.35f,  .80f, -.05f, .60f, .82f)
    PresenceMode.SPEAKING  -> ExpressionPose(.20f,  .82f,  .08f, .85f, .92f)
    PresenceMode.ALERT     -> ExpressionPose(.55f, 1.00f, -.12f, .35f, 1.0f)
}
```

### HairMotionController

Staggered independent opacity and position shimmer per strand. Strands do not
move together — each has its own timer offset. This produces an organic energy
field effect rather than synchronized wave motion.

```
per strand: opacity oscillation ± 0.08f on 3–6s randomized cycle
per strand: position drift ± 3px on 4–8s randomized cycle
implementation: multiple InfiniteTransition instances with staggered phase
```

---

## 6. Glow Hierarchy

### Purpose

A single glow value is insufficient for Zola's lighting model. Glow is
additive across four layers, each driven by a different source.

### Four Glow Layers

**Base Glow** — always present, very subtle. Never zero. Communicates that
Zola is active even in deep idle.

```
intensity: 0.12f constant
```

**Active Glow** — scales with `attentionConfidence`. When Zola is paying
attention, the manifestation brightens.

```
intensity: 0.0f–0.45f driven by attentionConfidence
```

**Speech Glow** — pulses with `speechAmplitude`. Synchronized with voice
output, gives the impression that Zola's presence intensifies when she speaks.

```
intensity: 0.0f–0.55f driven by speechAmplitude with spring smoothing
```

**Alert Glow** — full override. Activates in ALERT mode. Overrides all other
glow layers with maximum intensity and a sharper color temperature.

```
intensity: 1.0f, color shifts toward #FFE7A5 (bright amber-white)
```

Total glow is the sum of all active layers, clamped to 1.0f.

---

## 7. Ambient State System

### Purpose

`PresenceMode` should drive more than just facial expression. The entire scene
responds to mode, making Zola feel like the environment breathes with her state
rather than just her face changing.

### PresenceAmbientState

```kotlin
data class PresenceAmbientState(
    val particleDensity: Float,       // 0.0–1.0
    val particleDriftSpeed: Float,    // 0.0–1.0
    val eyeGlowRadius: Float,         // base radius multiplier
    val hairEnergyIntensity: Float,   // 0.0–1.0
    val backgroundGlowPulseRate: Float // Hz
)
```

Mode-to-ambient mapping:

| Mode | Particles | Drift | Eye Glow | Hair | BG Pulse |
|------|-----------|-------|----------|------|----------|
| IDLE | 0.4 | 0.2 | 0.65 | 0.35 | 0.3 |
| LISTENING | 0.6 | 0.35 | 0.85 | 0.55 | 0.5 |
| THINKING | 0.8 | 0.6 | 0.75 | 0.8 | 0.9 |
| SPEAKING | 0.7 | 0.5 | 0.9 | 0.65 | 0.7 |
| ALERT | 1.0 | 0.1 | 1.2 | 0.3 | 0.15 |

`ExpressionMapper` derives both `ExpressionPose` and `PresenceAmbientState`
from mode. Both are consumed by `ZolaPresenceRenderer` and distributed to
the relevant layers.

---

## 8. Mode Transition Staggering

### Purpose

When `PresenceMode` changes, all float targets change simultaneously without
staggering. This reads as a mechanical switch even with `animateFloatAsState`.
Staggering makes mode changes feel like Zola is reacting rather than switching.

### Stagger Order

1. **Eyes respond first** — fastest; 150–250ms. Eyes are the most alert signal.
2. **Breathing adjusts second** — medium; 400–600ms. The body follows the eyes.
3. **Expression settles last** — slowest; 700–1000ms. The most considered response.

### Implementation

A `PresenceModeTransitionCoordinator` holds the current mode and exposes three
derived state values — `eyeTargetMode`, `breathingTargetMode`,
`expressionTargetMode` — each updating with its own `delay()` after a mode
change. Each controller reads from its own target rather than the raw mode
directly.

This is approximately 30–40 lines of orchestration code but produces a
significant perceptual improvement in how mode transitions feel.

---

## 9. Eye System

### Purpose

Give Zola awareness, focus, and presence without making her visually unsettling.

The eyes are the strongest cue of entity-like intelligence and must be controlled carefully.

### Responsibilities

- render luminous amber eyes using SVG eye path coordinates
- preserve visible pupil anchor point
- support soft eye illumination via `eyeGlow` radial gradient
- support attention focus via `MicroSaccadeController`
- support blink behavior via `BlinkController`
- avoid horror-like over-glow
- avoid exaggerated human emotion

### Eye States

- idle calm — low glow, slow micro-saccades
- listening focus — increased glow, forward focus
- thinking focus — medium glow, reduced saccade range
- speaking warmth — warm glow, natural movement
- uncertainty softness — reduced glow, slight downward drift
- alert sharpness — maximum glow, minimal movement
- low confidence dimming — reduced glow

### Blink Behavior

Blinking is procedural and irregular via `BlinkController`.

- idle: occasional soft blink, 2500–7500ms interval
- listening: reduced blinking, `blinkSuppression` elevated
- thinking: micro-flicker or partial blink
- speaking: subtle natural blink cadence
- alert: minimal or no blinking, `blinkSuppression` = 1.0

### Important Principle

Zola's eyes should feel aware, not aggressive.

Brightness should communicate presence, not threat.

---

## 10. Mouth and Speech Motion System

### Purpose

Provide subtle speech indication without attempting full realistic facial animation.

### Responsibilities

- show that Zola is speaking through amplitude-driven motion
- avoid uncanny lip sync
- support audio-amplitude mouth movement via `MouthMotionController`
- support restrained expression
- prepare for future viseme timing if available

### Initial Strategy

Amplitude-driven cubic bezier path. `mouthOpen` float drives the vertical
displacement of center control points on the mouth curve. Spring physics
smooth the movement so it does not snap.

Mouth states:
- closed (0.0)
- slight open (0.1–0.2)
- medium open (0.3–0.5)
- wide open (0.6–0.8)
- relaxed speaking (varies with amplitude)
- soft neutral (0.0 with slight upward curve)

### Future Strategy

If the TTS provider exposes viseme or phoneme timing, the mouth system may
evolve into a more precise viseme mapper. This should remain optional.

### Important Principle

The mouth should support speech presence, not become the center of the experience.

Zola should not look like a talking cartoon.

---

## 11. Facial Expression System

### Purpose

Represent Zola's emotional and cognitive posture through micro-expression rather than exaggerated emotion.

### Responsibilities

- maintain calm baseline expression
- support subtle warmth, focused attention, concern, confidence, alertness, uncertainty
- avoid theatrical facial acting

### Expression Inputs

- `PresenceMode` (primary driver via `ExpressionMapper`)
- emotional tone (future — Wave 8)
- urgency
- confidence
- attention state

### Expression Outputs (ExpressionPose fields)

- `browTension` — eyebrow tension
- `eyelidOpenness` — eyelid openness
- `mouthCurve` — mouth curve positive/negative
- `eyeSoftness` — eye softness
- `projectionStability` — hologram stability

All fields animate with `animateFloatAsState` per field individually.

### Important Principle

Zola should shift, not perform.

Her expression should feel composed and intelligent.

---

## 12. Hair and Energy Field System

### Purpose

Use Zola's hair as part of the holographic manifestation rather than realistic hair simulation.

The hair should feel like energy, projection, and identity.

### Responsibilities

- preserve asymmetrical silhouette from SVG hair stroke paths
- support particle drift via `HairMotionController`
- support subtle staggered strand shimmer
- support cognitive activity changes via `PresenceAmbientState.hairEnergyIntensity`
- avoid real hair physics complexity
- avoid excessive movement

### State Reactions

Idle: slow drift, low particle activity

Listening: slightly more defined edges, attention-facing stabilization

Thinking: increased internal shimmer, denser pixel activity

Speaking: subtle pulse synchronized with voice energy

Noisy Environment: minor edge agitation, signal-like distortion

Alert: sharper outline, reduced decorative drift

### Important Principle

Hair motion should reinforce presence and state without distracting from conversation.

---

## 13. Hologram and Pixel Projection System

### Purpose

Maintain Zola's non-human, entity-like quality through projection artifacts and pixelated construction.

This layer prevents the manifestation from becoming too realistic.

### Responsibilities

- render pixel blocks from SVG `pixel_projection_blocks` coordinates
- render grid structure using SVG `microGrid` pattern
- render holographic scan effects
- render partial body dissolution at edges
- create depth through layered transparency
- support manifestation density changes via `PresenceAmbientState`
- preserve abstraction

### State Reactions

Idle: stable low-density projection

Thinking: denser internal movement, more visible computational structure

Speaking: subtle waveform-like body pulses

Uncertainty: slight projection instability

High Confidence: cleaner, more resolved projection

High Urgency: sharper edges and higher contrast

### Important Principle

Zola should remain stylized and partially abstract.

The projection layer is a guardrail against uncanny realism.

---

## 14. HUD Layer

### Purpose

Display functional system information around Zola without overpowering the central presence.

### Responsibilities

- show relevant system state using `Rajdhani` font
- show active mode
- show environmental context
- show attention level
- show conversation momentum
- show status indicators
- support expandable detail surfaces
- avoid visual clutter

### HUD Sections (from SVG reference)

Left panel:
- core systems menu with geometric icons
- version info
- encrypted connection status
- coordinates / location

Right panel:
- system status
- attention level with bar graph
- conversational momentum percentage
- emotional tone
- time
- environment
- obsidian mode status

### Important Principle

HUD content should be contextual, not decorative.

If a HUD element does not communicate useful state, it should be hidden or minimized.

---

## 15. Bottom Dock Navigation

### Purpose

Provide touch-accessible functionality without turning the interface into a chat app.

The bottom dock replaces the permanent text input bar.

### Responsibilities

- expose primary functional areas
- appear when useful, hide during ambient presence
- support endpoint-specific controls
- support manual interaction without dominating voice-first flow

### Dock Items (from SVG reference)

Voice, Memory, Env, Security, Systems — rendered as labeled icon buttons
inside a rounded pill shell with amber stroke border.

### Behavior

Idle: minimal or hidden

User taps screen: dock appears

Active conversation: conversation controls appear

Security event: security controls appear

Manual text mode: text input expands from dock

### Important Principle

Text input should be an option, not the default visual anchor.

Zola is voice-first.

---

## 16. Context Panels

### Purpose

Provide functional depth only when needed.

Context panels appear around Zola as temporary surfaces, not permanent app chrome.

### Responsibilities

- display detailed information
- support tool results, memory views, environmental summaries
- support settings and permissions
- support conversation history
- support security/camera actions
- preserve central presence

### Panel Types

**Conversation Panel** — recent transcript, current response, clarification prompts, follow-up options

**Memory Panel** — recalled facts, relationship context, episodic references, memory confidence

**Environment Panel** — location context, weather, traffic, nearby events, shop/home mode

**Security Panel** — camera event summaries, known/unknown person state, urgency level, available actions

**Systems Panel** — connection state, microphone state, TTS state, model/provider state, local/cloud mode

**Settings Panel** — permissions, voice mode, autonomy preferences, privacy controls, theme controls

### Important Principle

Panels should orbit the presence.

They should never replace Zola as the center of the interface.

---

## 17. Functional UI Integration

### Purpose

Tie visual surfaces to real system functionality without violating authority boundaries.

### Responsibilities

- display authoritative state
- expose approved actions
- reflect tool execution progress
- display confirmations
- show passive awareness
- show deferred summaries
- support user control
- avoid hidden UI-driven logic

### Functional Areas

voice state, listening state, speech state, memory recall, environmental
awareness, security events, calendar/events, messages, Gmail summaries,
health context, weather/traffic, music control, autonomous mode, permissions

### Important Principle

The UI presents and controls approved behavior.

It does not independently reason, decide, or bypass Zola's core runtime.

---

## 18. Authority Boundaries

### Purpose

Ensure the presence UI does not become a second assistant brain.

### The UI may:

- render state
- animate state
- expose user actions
- display system output
- request actions through approved channels
- show passive awareness

### The UI must not:

- generate facts
- reinterpret reasoning results
- bypass response authority
- independently classify user intent
- silently execute tools
- create memory writes directly
- override privacy rules
- speak directly to the user
- import cognitive classes (`QueryProcessor`, `GeminiLiveClient`,
  `ResponseExecutionService`, `ProactiveAutonomousEngine`, or any
  memory, attention, or proactive class) into any composable

### Important Principle

Zola's core runtime owns cognition, reasoning, speech authority, memory authority, and action authority.

The UI owns manifestation, presentation, and user interaction surfaces.

---

## 19. Visual Restraint and Attention Discipline

### Purpose

Ensure the UI follows the same restraint principles as Zola's autonomous behavior.

The interface should not visually spam the user any more than Zola should verbally interrupt them.

### Responsibilities

- suppress unnecessary visual noise
- reduce motion during high cognitive load
- avoid constant alerts
- dim low-priority state
- group passive information
- escalate visually only when justified
- support attention dampening

### Visual Dampening Examples

High CurrentHeat:
- reduce decorative motion
- suppress low-priority panel appearances
- keep dock minimized
- only show urgent changes

Low CurrentHeat:
- allow gentle ambient motion
- allow passive status hints
- allow contextual UI suggestions

Urgent Event:
- sharpen contrast
- increase eye focus
- surface relevant controls
- display concise event context

### Important Principle

The UI should communicate intelligence through restraint.

---

## 20. Endpoint Adaptation

### Purpose

Allow the Zola presence system to adapt across phone, desktop, shop display, vehicle display, and future smart glasses.

### Phone Mode

- primary mobile embodiment
- full-screen presence
- compact dock
- touch fallback
- notification-aware

### Desktop Mode

- sidebar or ambient panel
- richer context panels
- productivity/coding support
- larger HUD surfaces

### Shop Mode

- high-contrast visibility
- larger controls
- noise-aware visual cues
- hands-free priority
- simplified touch targets

### Vehicle Mode

- minimal visuals
- reduced animation
- driving-safe information
- high restraint
- urgent-only interruptions

### Smart Glasses Mode

- lightweight overlays
- no clutter
- glanceable state
- low distraction
- environmental awareness cues

### Important Principle

The manifestation should remain recognizably Zola across endpoints, while interaction surfaces adapt to context.

One mind, many bodies.

---

## 21. Implementation Architecture

### Purpose

Define a clean internal structure for building the presence UI incrementally.

### Proposed Package Structure

```text
ui/presence/
  PresenceRoot.kt                       ← top-level composable (Wave 1 ✅)
  ZolaPresenceRenderer.kt               ← assembles layers, derives scoped states
  PresenceVisualState.kt                ← UI-only state model
  PresenceMode.kt                       ← mode enum
  PresenceStateAdapter.kt               ← cognitive → visual translation (Wave 8)
  PresenceModeTransitionCoordinator.kt  ← staggered mode transition orchestration
  PresenceAmbientState.kt               ← ambient scene state derived from mode

ui/presence/layers/
  BackgroundLayer.kt          ← obsidian background + grid (Wave 1 ✅)
  ParticleFieldLayer.kt       ← particle field (Wave 1 ✅)
  ManifestationCoreLayer.kt   ← torso geometry (Wave 1 ✅)
  FaceLayer.kt                ← face, brows, mouth path
  EyeLayer.kt                 ← eyes, glow, blink, saccade
  MouthLayer.kt               ← amplitude-driven mouth
  HairEnergyLayer.kt          ← hair stroke paths + shimmer
  PixelProjectionLayer.kt     ← pixel blocks + grid overlay
  HologramDistortionLayer.kt  ← edge dissolution + scan effects
  CoreGlowLayer.kt            ← additive glow hierarchy
  HudShellLayer.kt            ← HUD frame (Wave 1 ✅)
  HudLayer.kt                 ← functional HUD content
  DockShellLayer.kt           ← dock shell (Wave 1 ✅)
  BottomDockLayer.kt          ← functional dock content
  ContextPanelLayer.kt        ← context panels

ui/presence/controllers/
  BlinkController.kt
  MicroSaccadeController.kt
  BreathingController.kt
  MouthMotionController.kt
  ExpressionMapper.kt
  HairMotionController.kt
  HologramNoiseController.kt

ui/presence/state/
  ExpressionPose.kt
  EyeRenderState.kt
  MouthRenderState.kt
  BreathingRenderState.kt
  HairRenderState.kt
  ParticleRenderState.kt
  ZolaUiState.kt
  HudState.kt
  DockState.kt
  ContextPanelState.kt
  PresenceInteractionEvent.kt
```

### Important Principle

The presence system should be modular from the beginning.

No layer should know the whole app.

Cursor should not build one giant composable that becomes impossible to evolve.

---

## 22. Build Waves

### Wave 1 — Static Presence Reconstruction ✅ COMPLETE

**Goal:** Recreate the approved Zola image as a static Compose interface.

**Deliverables:**
- obsidian background with grid
- central manifestation geometric placeholder
- amber/gold visual tokens
- HUD shell layout (left and right)
- bottom dock shell
- particle field baseline
- no animation

**Validation:**
- visual comparison against reference image
- no new visual direction introduced
- no permanent text bar
- zero cognitive class imports in `ui/presence/`

**Merged:** `a4ffc26` on `zola-main`

---

### Wave 2 — Idle Animation

**Goal:** Make Zola feel alive with self-contained idle animation that requires
no backend connection.

**Prerequisites:**
- `Rajdhani` and `Orbitron` fonts declared as downloadable fonts in the project
- SVG reference at `zola-architecture/assets/zola_presence_ui_reference.svg`
  read by Cursor before any Canvas work

**Deliverables:**
- `PresenceMode.kt`
- `PresenceVisualState.kt` — with mock/stub values for all fields
- `PresenceAmbientState.kt`
- `BlinkController.kt` — randomized irregular blink, 2500–7500ms
- `MicroSaccadeController.kt` — involuntary eye drift, spring settle, max 5px
- `BreathingController.kt` — asymmetric sine, mode-driven rate
- `ExpressionPose.kt` — float pose model
- `ExpressionMapper.kt` — mode-to-pose mapping
- `PresenceModeTransitionCoordinator.kt` — staggered eye / breathing / expression
- `EyeLayer.kt` — glow + blink + saccade, SVG coordinates
- `CoreBreathingLayer.kt` — chest glow pulse only
- `ZolaPresenceRenderer.kt` — assembles layers, derives scoped states
- Face geometry from SVG paths in `FaceLayer.kt`

**Validation:**
- Zola blinks irregularly
- Eyes have subtle involuntary drift
- Breathing pulse visible on chest glow only
- Mode switch produces staggered eye → breathing → expression response
- Zero cognitive class imports anywhere in `ui/presence/`
- All mock state values, no backend wiring

---

### Wave 3 — Expression and Speech Motion

**Goal:** Add expression states and amplitude-driven speech motion.

**Deliverables:**
- `MouthMotionController.kt` — spring amplitude driver
- `MouthLayer.kt` — bezier path mouth
- `HairMotionController.kt` — staggered strand shimmer
- `PresenceStateAdapter.kt` — stub only; real wiring Wave 8
- Update `PresenceVisualState.kt` with speech and expression fields
- `PresenceAmbientState` wired to all scene layers

**Validation:**
- Mouth opens/closes with mock amplitude
- Expression pose changes smoothly across modes
- Hair strands shimmer independently, not in sync
- Scene ambient responds to mode (particles, glow, hair)

---

### Wave 4 — Hologram, Pixel Projection, Full Glow Hierarchy

**Goal:** Complete the holographic entity quality. Add pixel projection,
dissolution, and the four-layer glow system.

**Deliverables:**
- `PixelProjectionLayer.kt` — pixel blocks + micro-grid from SVG
- `HologramDistortionLayer.kt` — edge dissolution, scan effects
- `CoreGlowLayer.kt` — four additive glow layers
- `HologramNoiseController.kt`
- Idle personality system integrated into idle animation loop

**Validation:**
- Projection instability responds to uncertainty state
- Glow hierarchy adds correctly, does not exceed 1.0
- Idle personality triggers are natural and non-intrusive

---

### Wave 5 — Functional HUD and Dock

**Goal:** Connect HUD and dock to real application state.

**Deliverables:**
- `HudLayer.kt` — functional HUD content with `Rajdhani` font
- `BottomDockLayer.kt` — functional dock with icon buttons
- `HudState.kt`, `DockState.kt` — state models
- text input as optional dock expansion
- active mode display

**Validation:**
- dock is not always visible as a text bar
- voice-first presence remains central
- UI controls route through approved app actions
- HUD reflects real state values

---

### Wave 6 — Context Panels

**Goal:** Add functional panels for conversation, memory, environment, security, systems, and settings.

**Deliverables:**
- reusable context panel shell
- panel state model
- panel transitions
- panel priority rules
- initial functional content mapping

**Validation:**
- panels do not overpower Zola
- panels appear only when useful
- no duplicated reasoning or data ownership

---

### Wave 7 — Real Cognitive Signal Integration

**Goal:** Connect the presence UI to real architecture signals through
`PresenceStateAdapter`.

**Possible signals:**
- listening state
- speech state from `AudioOrchestrator` (`speechAmplitude`)
- attention confidence from `AttentionRelevanceEngine`
- current heat from `AttentionDampeningController`
- conversational momentum
- environmental noise from `EnvironmentalEventBus`
- active mode
- urgency level
- emotional tone
- tool execution state

**Validation:**
- visual behavior reflects real system state
- no direct coupling to internal reasoning objects
- `PresenceStateAdapter` is the only mapping boundary
- all cognitive values arrive as normalized floats; no cognitive types
  cross the adapter boundary into composables

---

## 23. Performance Boundaries

### Purpose

The presence UI combines blur, particles, Canvas drawing, glow layers, and
continuous animation. Without discipline this stack will cause frame drops on
mid-range Android devices — which are the majority of real-world hardware.

Performance is a first-class architecture concern, not a post-launch fix.

### Rules

**Cap particles at 40 initially.**
Do not exceed 40 active particles until profiling confirms headroom on a
mid-range device. Particle count is a constant in `ZolaFeatureFlags`, not
hardcoded in the layer.

**Cache static paths with `drawWithCache`.**
Any Canvas path that does not change between frames — face geometry, grid
lines, torso outline, dock shell, HUD brackets — must be inside a
`drawWithCache` block. Only animated values (glow radius, eye position,
mouth curve) should trigger redraws. Recomputing static path objects every
frame is the most common avoidable performance cost in Canvas-heavy UIs.

**Store path objects in `remember`.**
Bezier path objects for the mouth curve, face shape, hair strokes, and chest
diamond must be computed once and stored with `remember`. They are updated only
when their input coordinates change. Never construct a `Path` object inside
a draw lambda.

**Keep animated layers isolated.**
Each layer composable reads only its own scoped render state. No layer reads
from the full `PresenceVisualState` directly. This ensures that when one
layer's values change, only that layer redraws — not the entire screen.
This is the implementation-level guarantee of the scoped render state model
defined in Section 4.

**Blur radius is a `ZolaFeatureFlags` constant.**
`BlurMaskFilter` and `Modifier.blur()` must not have hardcoded radius values.
Blur radius lives in `ZolaFeatureFlags` as a named constant so it can be tuned
without a code change. Default values must be conservative. On devices that
drop frames, lowering the blur radius is the first tuning lever.

**Defer blur to Wave 4.**
Waves 2 and 3 use alpha-based glow only — no `BlurMaskFilter`, no
`Modifier.blur()`. The full blur-based glow hierarchy is introduced in Wave 4
after the basic animation stack has been profiled. Adding blur before profiling
the base stack makes it impossible to isolate the source of frame drops.

**Render glow-heavy center to an offscreen bitmap.**
The manifestation center glow covers most of the screen and is the most
expensive area to blur. It must be rendered to an offscreen bitmap at 75%
of screen resolution and scaled up. Blur applied to a smaller surface is
approximately 4x cheaper than full-resolution. The human eye does not detect
the resolution difference on soft-edged glow elements.

**Respect Android reduced-motion accessibility setting.**
`ZolaPresenceRenderer` checks `LocalDensity` and the system reduced-motion
preference at startup. In reduced-motion mode:
- no particle drift
- no hair shimmer
- breathing reduced to a very slow glow pulse only
- blink and micro-saccades remain active (they are not distracting motion)
- no mode transition animation — state changes are instant

**Profile on a mid-range device.**
Every wave must be profiled on a mid-range device (not a flagship) before
merging. Suggested baseline: a device with ~6GB RAM and a mid-tier GPU
released within the last 3 years. Flagship-only profiling produces false
confidence. Frame time target is 16ms (60fps) sustained during idle animation.

### Important Principle

Performance problems that appear in Wave 4 are usually architecture decisions
made in Wave 2.

Build the performance constraints in from the start.

---

## 24. Cursor Execution Rules

### Hard Rules

Cursor must not:
- redesign the approved Zola visual direction
- replace the image with a generic assistant avatar
- create a realistic human avatar system
- build one monolithic composable
- connect UI directly to reasoning internals
- create duplicate tool/action execution paths
- make text chat the primary UI
- introduce cloud animation dependencies
- bypass architecture authority boundaries
- import `QueryProcessor`, `GeminiLiveClient`, `ResponseExecutionService`,
  `ProactiveAutonomousEngine`, or any cognitive, memory, attention, or
  proactive class into any composable in `ui/presence/`

Cursor must:
- read `zola_presence_ui_reference.svg` before implementing any render layer
- derive Canvas coordinates from the SVG, not invent new geometry
- use the approved image as canonical reference
- rebuild the interface in layered Compose components
- preserve voice-first design
- keep Zola centered
- make controls contextual
- use structured visual state
- keep animation procedural and local
- maintain restraint
- document changes per wave

### Important Principle

Cursor is not being asked to invent Zola's look.

Cursor is being asked to implement the approved presence system.

---

## 25. Validation Criteria

### Visual Validation

- Does the still frame resemble the approved concept and SVG reference?
- Does Zola feel like an entity rather than an app mascot?
- Does the interface preserve obsidian/gold contrast?
- Does the UI avoid looking like a generic chatbot?
- Does the bottom dock avoid becoming a permanent text bar?

### Motion Validation

- Does Zola feel subtly alive while idle?
- Are animations restrained?
- Do state changes feel meaningful?
- Do eyes feel aware but not unsettling?
- Does speech motion avoid uncanny behavior?
- Does mode transition staggering feel like reaction, not switching?
- Does breathing feel organic (asymmetric) rather than mechanical?
- Do micro-saccades make eyes feel alive?

### Functional Validation

- Do controls map to real app functions?
- Do panels appear only when needed?
- Does the UI reflect authoritative state?
- Are actions routed through approved handlers?
- Does the UI avoid duplicating reasoning logic?

### Architecture Validation

- Is visual state abstracted from cognitive internals?
- Are layers modular with scoped render states?
- Is the presence renderer reusable across endpoints?
- Are authority boundaries preserved?
- Can future signals be added without redesigning the UI?
- Does `PresenceStateAdapter` remain the only cognitive boundary?

### Performance Validation

- Are static paths cached with `drawWithCache` and `remember`?
- Do animated layers read only their own scoped render state?
- Is particle count within the `ZolaFeatureFlags` cap?
- Is blur radius a named constant, not hardcoded?
- Has the wave been profiled on a mid-range device at 60fps?
- Does reduced-motion mode suppress particle drift and hair shimmer?
- Is the manifestation center glow rendered to an offscreen bitmap?

---

## Long-Term End State

Zola's UI eventually evolves toward:

- persistent visual presence
- procedural entity-like life
- voice-first interaction
- contextual functional surfaces
- adaptive HUD behavior
- endpoint-aware presentation
- restrained visual attention
- state-driven expression
- environmental reactivity
- modular render architecture
- identity-stable manifestation

The system should ultimately feel:

- alive
- calm
- intelligent
- present
- restrained
- powerful
- voice-native
- environmentally aware
- functionally useful
- visually distinct

without becoming:

- a generic avatar
- a chatbot screen
- a decorative animation
- a notification wall
- a realistic uncanny human
- a second reasoning system
- a UI that competes with Zola's core authority

---

## Final Principle

Zola's interface should not simply show that the assistant is available.

It should make the user feel that Zola is present.
