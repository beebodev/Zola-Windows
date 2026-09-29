# P3-LORE Progress ? Phase 3 Lore Closeout

## Branch

- Branch: `p3-lore-closeout`
- Base / recorded HEAD on `main` at branch: `d3cedeb6e8894853b34070cb82176f7f2e7397e3` (`docs: record P3-LIFE merge SHA`)
- Expected successor of P3-LIFE merge `8a00f6e87c68d28231d9ba1fc9ec1f4d29de1f40` ? **matched**
- Prompt: P3-LORE v1.0
- Plan (binding for scope): `PHASE3_BUILD_PLAN.md` v1.7
- Presence UI architecture path: `zola-architecture/Zola_Presence_UI_Architecture.md`

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Branch, Read, and Gather | COMPLETE |
| 2 | Draft (for developer review) | COMPLETE |
| 3 | Write and Verify | COMPLETE |
| 4 | Closeout | COMPLETE |

## Guardrails summary

- **G-SCOPE:** Lore files + architecture Windows Track notes + `VoiceController.cs` comments only + this progress doc. No build-plan edit. No behaviour changes.
- **G-FACTS:** Every value, SHA, measurement and quote from a progress document or the plan, with source. Missing ? "not recorded".
- **G-VERBATIM:** Developer quotes copied exactly.
- **G-STYLE:** Match existing Phase 1 / Phase 2 lore format.
- **G-STOP / G-CLOSEOUT / G-NO-CROSS-SCOPE:** as prompt.

## Documents of Truth read

| Document | Path | Status |
|---|---|---|
| Plan v1.7 | `zola-architecture/lore/build-plans/PHASE3_BUILD_PLAN.md` | read (P3-D01?P3-D22, Lore Closeout, Exit Checklist, Defers) |
| P3-STATE | `zola-architecture/lore/prompts/progress/P3-STATE_Progress.md` | read |
| P3-SHELL | `zola-architecture/lore/prompts/progress/P3-SHELL_Progress.md` | read |
| P3-RENDER | `zola-architecture/lore/prompts/progress/P3-RENDER_Progress.md` | read |
| P3-LOOK | `zola-architecture/lore/prompts/progress/P3-LOOK_Progress.md` | read |
| P3-LIFE | `zola-architecture/lore/prompts/progress/P3-LIFE_Progress.md` | read |
| DESIGN_DECISIONS | `zola-architecture/lore/DESIGN_DECISIONS.md` | read (style + P2 section) |
| OPEN_QUESTIONS | `zola-architecture/lore/OPEN_QUESTIONS.md` | read |
| ROADMAP | `zola-architecture/lore/ROADMAP.md` | read |
| Presence UI Architecture | `zola-architecture/Zola_Presence_UI_Architecture.md` | read (Canonical Visual Direction, ?4 PresenceMode, ?5??9 motion, ?14 HUD) |
| VoiceController | `windows-client/Zola.Client/VoiceController.cs` | read (stale comments) |
| P2-LORE (style) | `zola-architecture/lore/prompts/progress/P2-LORE_Progress.md` | skimmed for closeout pattern |

`hermes-agent` at gather: clean at `345cd2b057a452236de401d3534b8502a7465e8d`.

---

## Facts table (KC1?KC3)

Status: **found** = in a progress doc or plan with a citeable location; **not recorded** = prompt/plan asked for it but no progress/plan source holds the exact value.

### Track merge SHAs and plan commits

| Fact | Value | Source | Status |
|---|---|---|---|
| P3PRE audit merge | `c2d6110fec5d9ee6c40a0d42d963d3838ab6fd63` | Plan footer; P3-STATE Branch | found |
| Plan v1.0 / initial plan commit | `5994e8bc4e1167c59304ec4b2317f8c9ed9ac94f` | P3-STATE SHAs | found |
| Plan v1.2 commit | `a03fda5389305f84668e63e437d9ee9f1b27d500` | P3-SHELL Branch / SHAs | found |
| Plan v1.3 commit | `eba07383ab752bb0e7a4e75d6eeea10636ff7de3` | P3-RENDER Branch / SHAs | found |
| Plan v1.4 commit | `4609c697937d2a5300897ec4575c02b38357f720` | P3-LOOK Branch / SHAs | found |
| Plan v1.7 commit | `819c51b0fab8b5dafb8256fa02a558236191db7a` | P3-LIFE Branch / SHAs | found |
| P3-STATE implementation | `104698ba10cffd3f12bcedd8e983ae1334520923` | P3-STATE SHAs | found |
| P3-STATE merge | `2fb98126eed05561c86b7b3e67ed454b0e7ef331` | P3-STATE SHAs | found |
| P3-SHELL implementation | `021210e71809dc1fb67ac644a7a40685219f28aa` | P3-SHELL SHAs | found |
| P3-SHELL merge | `b8bf6a15c8b806bca0fea499dbcfce0535e92932` | P3-SHELL SHAs | found |
| P3-RENDER implementation | `52f41e1edd33d19efe64d4174fed023918127f55` | P3-RENDER SHAs | found |
| P3-RENDER merge | `f61e1ae014bdf22bc0cab04e128bd93f0ffdebe5` | P3-RENDER SHAs | found |
| P3-LOOK implementation | `624dd20268de392e6969284aac4bec515944fa69` | P3-LOOK SHAs | found |
| P3-LOOK merge | `c8f666251deacaf0fcb6a714594abf44da2e931b` | P3-LOOK SHAs | found |
| P3-LIFE implementation | `8e4045f377fda3e995b354802562ffe53f6f62e7` | P3-LIFE SHAs | found |
| P3-LIFE merge | `8a00f6e87c68d28231d9ba1fc9ec1f4d29de1f40` | P3-LIFE SHAs | found |
| Lore closeout base HEAD | `d3cedeb6e8894853b34070cb82176f7f2e7397e3` | this branch | found |
| hermes pin | `345cd2b057a452236de401d3534b8502a7465e8d` / `v2026.9.14` | all track closeouts; ROADMAP header | found |

### P3-D20 look (Track 4)

| Fact | Value | Source | Status |
|---|---|---|---|
| Pipeline | unlit albedo; sRGB decode ? gain ? ACES Narkowicz ? sRGB encode | P3-LOOK Closeout / Android pipeline; Plan P3-D20 | found |
| `toneMapGain` | 4.4 | P3-LOOK Closeout approved defaults | found |
| `mipLodBias` | 0.75 | P3-LOOK Closeout | found |
| Texture size | 2048? | P3-LOOK Closeout Texture/memory | found |
| Look fingerprint (DEBUG) | `4392a2e0d851dc1e962c4ac5bfedf837e51c1645ed18d8bb044388fe346e83d8` | P3-LOOK Closeout; P3-LIFE Phase 3-D2 | found |
| Developer approval (verbatim) | `dark skin carrying gold from her own texture, white-gold eyes, glowing diamond and lit hair tips; dots softened; reads like Android.` | P3-LOOK Closeout Look approved; Plan P3-D20 | found |
| Process lessons | read source before tuning; raw live captures only; complete configs from reset | P3-LOOK Closeout Process lessons; Plan P3-D20 | found |
| CSO SHA (LOOK closeout / post-inventory) | `a9484343031bdde5dd2d1b09137e91791b6cc30000b5bc82a5882af72014e9e3` (1948 bytes) | P3-LOOK Closeout ACES | found |
| Backdrop | deferred (`P3-D21`); no glow/rings/brackets | P3-LOOK Closeout; Plan P3-D21 | found |

### P3-D17 dock amendment (Track 4)

| Fact | Value | Source | Status |
|---|---|---|---|
| Reveal region | dock footprint + `DockRevealMargin` 12 (not full-width zone) | P3-LOOK Phase 8 amendment / Closeout Figures | found |
| Hide delay | `DockHideDelaySeconds` 2 | P3-LOOK Closeout | found |
| Fade | `DockFadeMilliseconds` 180 | P3-LOOK Closeout | found |
| Visibility | pointer position + focus/overlay/sessions/streaming; hysteresis via hide delay | P3-LOOK dock section; Plan P3-D17 + amendment | found |
| One decider | `UpdateDockVisibility` | P3-LOOK Exit criteria | found |

### P3-D24 background compositing (Track 5 amendment)

| Fact | Value | Source | Status |
|---|---|---|---|
| Why | brightness multipliers made clear-colour invert unworkable in 8 bits | P3-LIFE Phase 3-D2 / guardrail notes | found |
| Approved-look field before D2 | displayed `#070707` (invert of token) | P3-LOOK Closeout samples; P3-LIFE reference compare mask | found |
| After D2 | exact `#080808` from `ZolaBackground` token | P3-LIFE Phase 3-D2 / Closeout | found |
| Mechanism | scene clear A=0; bust A=1; shader `lerp(ZolaBackground, toneMapped(rgb), sceneAlpha)`; output A=1 | P3-LIFE Closeout Background invert | found |
| Scene alpha | binary for this asset (dump: bust=1 hair=1 edge=0 field=0) | P3-LIFE Phase 3-D2 | found |
| Fail-closed | opaque token background | P3-LIFE Phase 3-D2 verify | found |
| Old CSO (pre-D2 on LIFE branch) | `a9484343031bdde5dd2d1b09137e91791b6cc30000b5bc82a5882af72014e9e3` / 1948 | P3-LIFE Phase 3-D2 | found |
| New CSO (post-D2) | `89aa36150afc317544377d8b4b7235ea7b70f19da540cebe3ca5acefc3c298c8` / 2024 | P3-LIFE Phase 3-D2 | found |
| Invert constants | removed (`PresenceLook.DisplayBlackByte`, AcesA?E from look path) | P3-LIFE Phase 3-D2 | found |
| Look fingerprint after D2 | unchanged `4392a2e0?` | P3-LIFE Phase 3-D2 | found |

### P3-D22 / P3-D14 life values (Track 5 final)

| Fact | Value | Source | Status |
|---|---|---|---|
| Breathing (verbatim) | `None. Not necessary for AI to breathe.` | Plan P3-D22 | found |
| Head motion (verbatim) | `None. The model wasn't made for it.` | Plan P3-D22 | found |
| Full key surface (verbatim) | `I want to make sure we are actually exposing all the keys and not limiting ourselves to what Android was using.` | Plan P3-D22 | found |
| Grain of salt (verbatim) | `We should take the Android settings with a grain of salt though. We can use them as a starting point, but there will definitely need to be some fine tuning.` | Plan P3-D22 | found |
| Particles drop (verbatim) | `I'm almost thinking that we don't need the particles. Zola's image speaks for itself.` | P3-LIFE Phase 7 / Closeout | found |
| Life approved (verbatim) | `blinks and expressions feel natural in every mode, the mouth follows her voice with restrained, natural movement, and she stays composed. Alert reads as attentive, not startled.` | P3-LIFE Phase 6 / Closeout | found |
| Life fingerprint | `ef3c2c6eb9894a4fb83d473ba69bfba6e88e44f4ab4da69d88c3585510189777` | P3-LIFE Phase 6 / Closeout | found |
| Key count | 186 DEBUG / 185 Release | P3-LIFE Closeout | found |
| Blink | close 120 / open 180 ms; interval 3000?8000; Thinking 2000?4500 depth 0.4; mix Both=1; Dormant lidRest 0.3 | P3-LIFE Closeout Final tuned values | found |
| Expression | Listening BrowRaise 0.4; Thinking BrowFurrow 0.15; Alert WideEyes 0.35 / BrowRaise 0.3 / NostrilFlare 0.1 / WideEE 0; ease 300 ms | P3-LIFE Closeout + Round 5 | found |
| Brightness | Idle 1.0 / Listening 1.1 / Thinking 0.75 / Speaking 1.0 / Alert 1.25 / Dormant 0.5; Speaking pulse amp 0.05 period 1200 ms; ease 600 ms | P3-LIFE Closeout | found |
| Stagger | eyes 0 / brightness 450 / expression 850 ms | P3-LIFE Closeout; Plan P3-D22 | found |
| Mouth (Round 4 baseline + Round 1 keys kept) | step 150?250; jawBase 0.02 / jawRange 0.10; levelMax 0.85; OpenAH/MidOpen gains 0.5; ClosedMBP 0.6; TeethFV 0.3; wideEeScale 0; Round OO lean; releaseStiffnessScale 2.5; speakingTickIntervalMs 33 | P3-LIFE Round 1?4 + Closeout | found |
| ALERT note | placeholder-safe; no Windows trigger (`S25`) | P3-LIFE Round 5 | found |
| Dormant | BlinkBoth 0.30 held; brightness ?0.5; no blinks at rest | P3-LIFE Phase 4; Plan P3-D04/P3-D22 | found |
| Particles | **dropped** (all keys/layer/tokens removed) | P3-LIFE Phase 7 / Closeout | found |

### P3-D23 mouth timing (Track 5 Phase 5b)

| Fact | Value | Source | Status |
|---|---|---|---|
| Prompt claim: first audio 2.4?64 s after SPEAKING | superseded by developer-supplied S17 analysis | **developer-supplied (S17 analysis report)** | found |
| S17 analysis: first owned playback after SPEAKING | 2.4?4.6 s typical (median 2.6 s); 63.8 s tool-heavy; gaps median 110 / max 138 ms; one 6.5 s mid-reply pause; earlier report 6.1?8.6 s vs 3.3 s estimate | **developer-supplied (S17 analysis report)** 2026-09-28; artifacts `%TEMP%\p3life-s17\` | found |
| Closest progress-doc Armed hold (Phase 5b n=3) | min 2361 / median 3176 / max 3176 ms | P3-LIFE Phase 5b Verify evidence | found |
| Motivation vs 3.3 s guess | estimate onset was wrong both late and early (Rounds 2?3); playback presence supersedes | P3-LIFE Round 2?3 + Phase 5b | found |
| Poll | `mouth.playbackPollHz` 20 | P3-LIFE Phase 5b Keys | found |
| Bout bridge | `mouth.releaseDebounceMs` 450 | P3-LIFE Phase 5b | found |
| Stop signal | owned session `Inactive` (adopted over session disappear) | P3-LIFE Round 1 end-tail | found |
| Ownership | Hermes serve process tree; foreign ffplay rejected | P3-LIFE Phase 5b | found |
| State machine | Idle ? Armed ? Active ? Releasing ? Idle; `SpeakingPlaybackArmed` holds THINKING look until first playback | P3-LIFE Phase 5b | found |
| `speakingPauseShowsThinking` | default **false** | P3-LIFE Phase 5b | found |
| Fail-closed | monitor unavailable ? estimate onset (`FirstSentenceLatencySeconds` + offset); SPEAKING clear always releases | P3-LIFE Phase 5b | found |
| Peak meter | QI ok; peak always 0 ? dropped | P3-LIFE Phase 5b S17 notes | found |
| P2-D01 amendment | display-only observe presence of Hermes-owned player sessions; no audio data/level/capture | P3-LIFE Phase 5b Developer decisions | found |

### Machine measurements

| Fact | Value | Source | Status |
|---|---|---|---|
| Idle GPU final (blinks, particles dropped) | avg **2.2725%** / max 12.7560 (60 s) | P3-LIFE Phase 7 / Closeout / GPU table | found |
| Idle GPU Phase 4 (blinks) | avg 2.4014 / max 13.3320 | P3-LIFE GPU table | found |
| Static GPU (LOOK A9 / approved) | avg **0.0013%** / max 0.0771 | P3-LOOK Closeout Figures / smoke A9 | found |
| Static GPU after inventory | avg 0.0012 / max 0.0727 | P3-LOOK Closeout | found |
| Speaking GPU (tick 16, Phase 5) | avg 34.1884 / max 38.5253 | P3-LIFE GPU table | found |
| Speaking GPU (tick 33, Phase 6 proxy 60 s) | avg ~33.5560 / max 36.3785 | P3-LIFE Round 1 historical / GPU section | found |
| Dormant GPU | avg **0.0005** / max 0.0315 (60 s) | P3-LIFE GPU table / Phase 4 | found |
| Cold resting memory | WS **809 MB** (848,560,128) / private 742 MB | P3-LOOK Closeout Texture/memory | found |
| Peak WS during load | 1004 MB | P3-LOOK Closeout | found |
| Cold load | 906 ms import / 2388 ms wall | P3-LOOK Closeout | found |

### S31 (LOOK)

| Fact | Value | Source | Status |
|---|---|---|---|
| Native climb per F10 reload | ~150 MB WS/private | P3-LOOK S31 section / Closeout | found |
| Managed | flat ~160 MB after first reload; not a managed leak | P3-LOOK S31 | found |
| Production exposure | lock/sleep/minimize reuse scene; F10 debug-only | P3-LOOK S31 | found |

### S30 Composition finding (LIFE Phase 7)

| Fact | Value | Source | Status |
|---|---|---|---|
| `AnimationController.Progress` setter | Access-violates; kills process | P3-LIFE Phase 7 Composition finding | found |
| Negative `DelayTime` | `ArgumentException: The parameter is incorrect` | same | found |
| `CompositionPropertySet.StartAnimation("t", Forever)` | Starts; `t` never advances | same | found |
| Forever on ElementVisual / ShapeVisual Offset/Opacity | Start succeeds; Progress stays 0; property unchanged | same | found |

### S32 (LIFE smoke)

| Fact | Value | Source | Status |
|---|---|---|---|
| Observation | Zola responds to voice while Windows is at the lock screen | P3-LIFE Phase 8 Proposed open question S32 | found |
| Cause | pre-existing P2; voice pipeline in Hermes; not Track 5 | same | found |
| Options | pause wake on lock; restrict replies while locked; keep deliberately | same | found |
| Priority high + mantra | prompt KC2 adds "I protect" / locked PC should not answer | **prompt only** ? not in progress | note for draft (flag) |

### S17 update facts

| Fact | Value | Source | Status |
|---|---|---|---|
| Timing partially resolved | session presence gates onset/release (`P3-D23`) | P3-LIFE Phase 5b / Closeout | found |
| Still open | in-sentence pauses + suspected trailing silence (~1 s after audible end; two screen recordings; not yet measured); shapes still synthetic | P3-LIFE Deferred S17; developer correction at lore write | found |
| Future paths | client MP3 envelope scan; Hermes lifecycle events; peak meter returns 0 | P3-LIFE Deferred S17; Phase 5b | found |

---

## Plan-versus-progress differences (amendments)

Progress wins where they disagree. Each difference must appear in the Phase 2 draft.

| # | Topic | Plan said | Progress / developer later | Source |
|---|---|---|---|---|
| A1 | **P3-D17 dock reveal** | Full-width `DockRevealZoneHeight` (120) strip | Footprint + `DockRevealMargin` 12; pointer-position; hysteresis via hide delay | P3-LOOK Phase 8 amendment |
| A2 | **P3-D20 background** | Clear-colour compensation so displayed bg stays `#080808` | Invert produced `#070707`; LIFE Option D (P3-D24) composites token in tone-map | P3-LOOK samples; P3-LIFE Phase 3-D2 |
| A3 | **P3-D14 mouth timing** | Procedural estimate + `FirstSentenceLatencySeconds` onset | Timing from observed TTS playback (`TtsPlaybackMonitor`) ? **new P3-D23**; shapes stay synthetic | P3-LIFE Phase 5b |
| A4 | **P2-D01** | Client never opens audio device / no audio | Amended **display-only**: may observe Hermes-owned player session **presence** (no data/level/capture) | P3-LIFE Phase 5b |
| A5 | **P3-D22 particles** | Separate droppable last phase; float Forever amendment during build | Particles **dropped** (verbatim); float amendment **superseded** | P3-LIFE Phase 7 |
| A6 | **P3-D22 ALERT starting values** | WideEyes 0.9, BrowRaise 0.6, Nostril 0.4, WideEE 0.4, brightness 1.60 | Final: 0.35 / 0.3 / 0.1 / 0 / brightness 1.25 | P3-LIFE Round 5 |
| A7 | **P3-D22 Speaking pulse** | ?0.15 sine over 1.2 s | Final amp **0.05** | P3-LIFE Round 3 / Closeout |
| A8 | **Mouth shape starting ? final** | Android-derived jaw/level/etc. | Round 4 approved mouth (jawRange 0.10, levelMax 0.85, gains, steps 150?250, speaking tick 33) | P3-LIFE Rounds 1?4 |
| A9 | **P3-D09 idle GPU** | ?10% with blinks (+ particles if kept) | Final **2.27%** without particles; particles never shipped | P3-LIFE Phase 7 |
| A10 | **OPEN_QUESTIONS plan list** | S24?S30 + S17 update; Phase 4 stub without S31/S32 | Progress proposes **S31**, **S32**; Composition note for S30; prompt extends Phase 4 stub (S32 first, +S31) | P3-LOOK S31; P3-LIFE S32/S30; this prompt KC2/KC3 |
| A11 | **DESIGN_DECISIONS range** | Plan lore closeout: P3-D01?P3-D22 | Prompt adds **P3-D23**, **P3-D24** from Track 5 amendments | this prompt KC1 |
| A12 | **Architecture doc notes** | Plan: Canonical Visual, ?4 DORMANT, ?14 true-state | Prompt also: motion ??5?9 citing P3-D22/P3-D23; P3-D20/P3-D24 on visual note | Plan vs this prompt KC4 |
| A13 | **P3-D15 comments** | STATE removed dead constants and retagged two comments to P2-D14 | Stale bag-of-words comment remains at L49; L57 still cites P2-D12 ? lore-closeout tidy | VoiceController.cs now; Plan code tidy; P3-STATE Phase 2 carry-over |

---

## VoiceController comment tidy (proposed)

**File:** `windows-client/Zola.Client/VoiceController.cs`  
**Constraint:** comments only; zero code tokens change.

### Current (lines 48?60)

```
48|    // P3-STATE: unused bag-of-words echo constants are removed; the live rule is P2-D14 ? P3-D15
49|    // P2-SPEAK: follow-up echo uses a tail bag-of-words check plus a short phrase run; 80% missed an STT split of unless ? P2-D14
50|    private const int EchoLookbackWords = 20;
?
53|    // P2-WAKE: drop a follow-up only when a ?3-word in-order run is ?0.60 of it and ends near her last spoken words ? P2-D14
?
57|    // P2-WAKE: slack grows with a long transcript so a late STT tail still anchors ? P2-D12
58|    private const double EchoEndSlackRatio = 0.25;
59|    // P2-WAKE: one unmatched word (hers or STT) may sit inside the run; two breaks it ? P2-D12
60|    private const int EchoMaxGapWords = 1;
```

### Diagnosis

- Line **49** still describes the **removed** bag-of-words approach (`EchoContainmentRatio` / phrase match). P3-STATE deleted those constants but left this descriptive comment (only flipped the ID to P2-D14).
- Line **57** cites **P2-D12** for a live echo-rule parameter; the live rule is **P2-D14** (plan lore-closeout / P3-D15 intent).
- Line **59** also cites P2-D12 for an echo-rule gap parameter (same issue; adjacent to 57). Prompt names ?near lines 49 and 57?; propose fixing **59** the same way for consistency.
- Line **48** correctly records the P3-D15 removal; keep it.
- Line **53** already states the live P2-D14 rule; keep it.

### Proposed replacement

| Line | Action |
|---|---|
| 49 | **Delete** the bag-of-words comment entirely (describes removed constants). |
| 57 | Change trailing ID `P2-D12` ? `P2-D14`. Text unchanged otherwise: `// P2-WAKE: slack grows with a long transcript so a late STT tail still anchors ? P2-D14` |
| 59 | Change trailing ID `P2-D12` ? `P2-D14` (same class of stale ID). |

No `const` names, types, or values change. Proof in Phase 3: comment/whitespace-ignored diff empty of code tokens; `dotnet build ? -r win-x64` 0 warnings.

---

### Shell / notice tokens (for P3-D07 / P3-D08 / P3-D18 drafts)

| Fact | Value | Source | Status |
|---|---|---|---|
| `NoticeHoldSeconds` | 4 | P3-LOOK Tokens / Figures | found |
| `ZolaMantraIndent` (final) | `100,0,0,0` | P3-LOOK Tokens / Figures (SHELL Phase 4 had 124; LOOK finish) | found |
| Overlay max width / fraction | 440 / 0.45 | P3-SHELL Closeout | found |
| Rajdhani Regular SHA-256 | `F0BA67D6EF91BCFF8B0E43A051F7483DD83EBFCADE19880CD15DF29890234D2E` | P3-SHELL Phase 3 / Closeout | found |
| Rajdhani SemiBold SHA-256 | `5FD51C1334CAFD3654059B0EE61AA470088A70E4637A9CFC0274557C751EB0CD` | P3-SHELL Phase 3 / Closeout | found |
| LinkLabel cases | OFFLINE / LOCAL LINK ? RECONNECTING / CONNECTED / CONNECTING | P3-SHELL Phase 2?3 | found |
| P3-D15 constants removed | `EchoContainmentRatio`, `EchoMinWords`, `EchoPhraseWords` | P3-STATE Phase 4 / Exit criteria | found |
| LOOK displayed bg pre-D2 | samples `7,7,7` (invert of token `#080808`) | P3-LOOK Closeout | found |
| S30 in LOOK progress | named in plan v1.6 surface only; no LOOK body ? Composition Forever table is LIFE Phase 7 | P3-LOOK Step 0; P3-LIFE Phase 7 | found |

## Phase 1 notes for Phase 2 draft

1. Flag **not recorded:** prompt?s ?first audio 2.4?64 s? ? draft P3-D23 using Armed hold **2.3?3.2 s** (n=3) and ?longer tool-style holds, no timeout,? and mark the 64 s upper bound as not recorded unless the developer supplies it.
2. Flag **S32 priority / mantra wording** as prompt-added (not in P3-LIFE progress); include in draft for developer review.
3. Architecture path confirmed: `zola-architecture/Zola_Presence_UI_Architecture.md`.
4. No lore files edited this phase.
5. Fact extracts from track progress ([STATE/SHELL](4fa7203f-0e12-41d0-b67d-165ef07ae996), [RENDER/LOOK](5acdd14b-9065-4e73-9d58-259164f0ad6c), [LIFE+plan](0f48c816-f619-49e5-a1d9-ec2c30faa2c7)) cross-checked; SHAs and core KC1?KC3 values matched; shell/notice rows above folded in.


---

## Phase 2 ? Draft (for developer review)

Full proposed text exactly as it will appear in the lore/doc files. Source tags in
`[src: ?]` are for review only; they are **stripped** when applying in Phase 3.

**Flags for developer review:**
- **F1:** Prompt claimed first audio ?2.4?64 s after SPEAKING? ? **not recorded** in
  progress. Draft uses Armed hold **2.3?3.2 s** (n=3) and ?longer tool-style holds, no
  timeout.? `[src: P3-LIFE Phase 5b]`
- **F2:** S32 ?Priority: high? and mantra ?I protect? / locked PC should not answer ?
  from this closeout prompt, not P3-LIFE progress. Included below for review.

---

### KC1 ? `DESIGN_DECISIONS.md`

#### Annotation on existing `P2-D01` (append after the current entry?s last sentence)

```
  Phase 3 amendment (`P3-D23`): for display only, the client may observe the
  presence of audio sessions belonging to Hermes's own player processes (TTS
  playback gating for the mouth). No audio data, no level, and no capture.
  Device ownership is unchanged. [src: P3-LIFE Phase 5b Developer decisions;
  amends P2-D01]
```

#### Annotation on existing `P2-D08` (append after the current entry?s last sentence)

```
  Phase 3 (`P3-D03`): the voice-state label and mic line are now derived only
  by `ZolaDisplayState`. The strings and priority order are unchanged from
  Phase 2. [src: plan Lore Closeout; P3-STATE Exit criteria]
```

#### New section (append after Phase 2 ? Voice)

```
## Phase 3 ? Presence UI
Recorded from `PHASE3_BUILD_PLAN.md` v1.7 (`P3-D01`?`P3-D22`) and from the five
track progress docs. Amendments approved during the tracks are folded in
(`P3-D17` dock, `P3-D14`/`P3-D22` life and mouth, plus new `P3-D23` and
`P3-D24`). Full wording for the original decisions lives in the plan; this
section is the lore pointer plus final values and execution corrections.
[src: plan Lore Closeout; progress wins on amendments]

- **P3-D01 ? The GLB replaces the SVG as Zola's canonical visual on Windows.**
  `zola.glb` (SHA-256 `1edf2bf5898528fd405cd3131fcf75548c6d5d1e893501467c65845b5d7a054b`,
  33,972,240 bytes) [src: P3-RENDER Closeout] is the presence. The SVG
  reference is not a Windows target. Supersedes SVG coordinate rules, the
  "no realistic 3D model" non-goals, and Compose/Canvas mechanics for
  Windows. Presence-first design, state-down pipeline, restraint, reduced
  motion, and performance discipline still bind. [src: plan P3-D01]

- **P3-D02 ? Engine: Helix Toolkit 3.1.2 (Set A), native in-process.**
  Packages: `HelixToolkit.WinUI.SharpDX` 3.1.2 and
  `HelixToolkit.SharpDX.Assimp` 3.1.2. `Viewport3DX` is constructed in code,
  never XAML. Track 4 then replaced the lit PBR path with the approved unlit
  look (`P3-D20`). WebView2 + three.js and Unity were ruled out. [src: plan
  P3-D02; P3-LOOK P3-D20]

- **P3-D03 ? One display-state authority: `ZolaDisplayState`.**
  `ZolaDisplayStateModel` is the only place that turns runtime facts into the
  voice-state label, mic-indicator line, Voice/Text mode word, mic-button
  enablement and content, and `PresenceMode`. It reads `VoiceController`
  public properties; the window pushes facts through one
  `UpdateWindowFacts(...)`. `ApplyVoiceChrome` is assign-only.
  `VoiceController` keeps listeners, `voice.*` / `wake.*`, and
  transcript-to-submit (`P2-D12`). Label and mic-line strings and order match
  Audit 01 ?3. [src: plan P3-D03; P3-STATE]

- **P3-D04 ? `PresenceMode` values and mapping (Windows addition: `DORMANT`).**
  Modes: `IDLE`, `LISTENING`, `THINKING`, `SPEAKING`, `ALERT`, plus `DORMANT`.
  Priority (first match): unreachable ? `DORMANT`; switch/history ? `IDLE`;
  `Speaking` ? `SPEAKING`; streaming ? `THINKING`; transcribing / capture /
  listening ? `LISTENING`; Text mode or unavailable ? `IDLE`; else `IDLE`.
  `Speaking` outranks streaming for presence; the HUD voice label keeps its
  Phase 2 order (streaming before Speaking). `ALERT` is defined but never
  produced this phase (`S25`). Final Dormant look: `Blink both` held at 0.30,
  brightness ?0.50, no blinks at rest [src: P3-LIFE Phase 4 / Closeout; plan
  P3-D04 v1.7].

- **P3-D05 ? Model gaps: approximate what the asset supports, defer the rest.**
  Built: blink, expression morphs, speaking mouth, brightness per mode.
  Dropped by developer (`P3-D22`): breathing and head motion. Deferred to
  `S24`: micro-saccade, hair strand shimmer, projection/hologram layers,
  frown and eye-softness targets. [src: plan P3-D05 / P3-D22]

- **P3-D06 ? The HUD shows only true state; everything else is hidden.**
  Shown: VOICE block (label + mic line), TIME, SESSION, LINK, notices.
  Hidden for lack of source (`S25`): attention, momentum, emotional tone,
  system health, environment, version, encrypted link, location, Core
  Systems destinations. [src: plan P3-D06]

- **P3-D07 ? Identity text is kept, as an explicit exception to ?14.**
  ZOLA wordmark, three-line tagline (`PERSISTENT` / `CONVERSATIONAL` /
  `INTELLIGENCE`), mantra, OBSIDIAN INTERFACE. Waveform space reserved and
  left empty (`S27`). Mantra indent final token `100,0,0,0` [src: P3-LOOK
  Figures]. [src: plan P3-D07; P3-SHELL]

- **P3-D08 ? Visual tokens, fonts and scale.**
  Colours, type, and spacing live in `ZolaTokens.xaml`. Rajdhani (Regular +
  SemiBold) with OFL; Orbitron wordmark not used. Conversation overlay max
  width 440 / fraction 0.45 [src: P3-SHELL Closeout]. Overlay opacity 0.94
  [src: P3-LOOK Closeout]. [src: plan P3-D08]

- **P3-D09 ? Idle performance budget: ? 10% GPU on the Latitude 7430.**
  Idle life (blinks; particles if kept) averaged over 60 s, sum of GPU-engine
  utilization for the client process. Final idle with blinks, particles
  dropped: avg **2.2725%** / max 12.7560 [src: P3-LIFE Closeout / GPU
  table]. Static approved look (LOOK): avg **0.0013%** / max 0.0771 [src:
  P3-LOOK smoke A9]. Dormant at rest: avg **0.0005%** / max 0.0315 [src:
  P3-LIFE GPU table]. Speaking is recorded, not scored against the idle
  budget (e.g. ~33.6% at speaking tick 33 ms) [src: P3-LIFE GPU table].

- **P3-D10 ? Location is not shown.** No Windows source; privacy. Revisit
  with `S25`. [src: plan P3-D10]

- **P3-D11 ? Layout: full presence, conversation on demand.**
  Full-window presence; HUD; dock (hidden until needed, `P3-D17`);
  conversation and sessions overlays. Default 1280?800; minimum 900?640.
  [src: plan P3-D11; P3-SHELL]

- **P3-D12 ? Asset storage.**
  `zola.glb` in plain git at `Assets/Presence/`; `.gitattributes` binary; no
  LFS. [src: plan P3-D12; P3-RENDER]

- **P3-D13 ? Fidelity is judged by the developer against the Android
  reference.** Texture size tested; **2048?** kept (cold rest 809 MB <
  900 MB gate; 1024? not run) [src: P3-LOOK Step 3 / Closeout].

- **P3-D14 ? Speaking mouth is procedural; shapes are synthetic.**
  Viseme-band blend with springs; jaw and mouth morphs only while speaking.
  Timing is no longer the `P2-D15` estimate alone ? onset and release follow
  observed TTS playback (`P3-D23`). Final mouth values (Round 4 baseline,
  baked): step 150?250 ms; `jawBase` 0.02 / `jawRange` 0.10; `levelMin`
  0.1 / `levelMax` 0.85; OpenAH / MidOpen gains 0.5; ClosedMBP 0.6; TeethFV
  0.3; `wideEeScale` 0; Round OO chance 0.3 / weight 0.35;
  `releaseStiffnessScale` 2.5; `engine.speakingTickIntervalMs` 33 [src:
  P3-LIFE Round 4 / Closeout]. Real amplitude and in-sentence pauses remain
  `S17`.

- **P3-D15 ? Carry-over: remove dead echo constants.**
  Removed unused `EchoContainmentRatio`, `EchoMinWords`, and
  `EchoPhraseWords`. Live echo rule remains `P2-D14`. `VOICE_CONFIG.md`
  rows marked `Removed (P3-STATE)`. Comment tidy completed in this lore
  closeout. [src: plan P3-D15; P3-STATE Exit criteria]

- **P3-D16 ? No `hermes-agent` edits; no Python installs.**
  Carries forward `P2-D10` / `P2-D17`. hermes-agent stayed clean at
  `345cd2b057a452236de401d3534b8502a7465e8d` through every track closeout.
  [src: plan P3-D16; all track Closeouts]

- **P3-D17 ? The dock is hidden until needed (v1.4; Track 4 amendment).**
  Fades in when the pointer is inside the dock footprint plus
  `DockRevealMargin` **12**, or keyboard focus is in the dock, or the
  conversation/sessions overlay is open, or a turn is streaming. Fades out
  after `DockHideDelaySeconds` **2**; fade `DockFadeMilliseconds` **180**
  (instant with reduced motion). Hidden is opacity 0 (not `Collapsed`).
  Visibility is decided by pointer position against the inflated footprint
  (hysteresis via the hide delay). One decider: `UpdateDockVisibility`.
  Supersedes the plan?s full-width `DockRevealZoneHeight` strip. [src:
  plan P3-D17; P3-LOOK Phase 8 amendment / Closeout]

- **P3-D18 ? The notice line fades; problems stay.**
  New messages show, then fade after `NoticeHoldSeconds` **4**. Sticky while
  unreachable, switch in flight, history pending, or last turn errored.
  `DetailText` only while sticky. One decider: `UpdateNoticeVisibility`.
  [src: plan P3-D18; P3-LOOK]

- **P3-D19 ? ACES Filmic tone mapping as a custom post-effect.**
  Narkowicz 2015 ACES in `AcesTonemap.hlsl` / `.cso`, compiled once with
  `fxc`, embedded resource, fail-closed. Final LOOK-era CSO SHA-256
  `a9484343031bdde5dd2d1b09137e91791b6cc30000b5bc82a5882af72014e9e3`
  (1948 bytes) [src: P3-LOOK Closeout]. Background compositing later moved
  into this pass (`P3-D24`).

- **P3-D20 ? Texture-driven presence look (developer-approved 2026-09-25).**
  Pipeline: Helix unlit albedo; sRGB decode ? gain **4.4** ? ACES ? sRGB
  encode; mip LOD bias **0.75**; texture **2048?**. Lights, bloom, and rim
  off. Look-defaults fingerprint (DEBUG):
  `4392a2e0d851dc1e962c4ac5bfedf837e51c1645ed18d8bb044388fe346e83d8`
  [src: P3-LOOK Closeout]. Developer approval, verbatim: "dark skin carrying
  gold from her own texture, white-gold eyes, glowing diamond and lit hair
  tips; dots softened; reads like Android." [src: P3-LOOK Look approved;
  plan P3-D20]. Process lessons (kept): read the source implementation
  before tuning toward a reference; judge only raw live captures, never
  scaled composites; every tuning candidate is a complete configuration
  applied from a reset. [src: P3-LOOK Process lessons; plan P3-D20]
  Background field after Track 4 still sampled `7,7,7`; exact token
  `#080808` is `P3-D24`.

- **P3-D21 ? Backdrop and decoration deferred.**
  No warm glow, floor rings, or corner brackets. Clean field from the
  background token. Particles moved to Track 5 and were later dropped
  (`P3-D22`). Filed as `S30`. [src: plan P3-D21; P3-LOOK; P3-LIFE Phase 7]

- **P3-D22 ? Track 5 motion follows Android's actual 3D behaviour.**
  Channels on Windows: blink, expression, brightness (tone-map gain
  multiplier), speaking mouth. Developer decisions, verbatim: Breathing:
  "None. Not necessary for AI to breathe." Head motion: "None. The model
  wasn't made for it." [src: plan P3-D22]. Full key surface (developer,
  verbatim): "I want to make sure we are actually exposing all the keys and
  not limiting ourselves to what Android was using." [src: plan P3-D22].
  Android values were starting points; finals below. Particles: built as a
  droppable last phase; float/Composition Forever amendment superseded when
  the developer dropped them, verbatim: "I'm almost thinking that we don't
  need the particles. Zola's image speaks for itself." [src: P3-LIFE
  Phase 7]. Life approved, verbatim: "blinks and expressions feel natural
  in every mode, the mouth follows her voice with restrained, natural
  movement, and she stays composed. Alert reads as attentive, not
  startled." [src: P3-LIFE Phase 6 / Closeout].
  Final tuned values (named constants in `PresenceLife.cs`):
  - Blink: close 120 / open 180 ms; interval 3000?8000; Thinking
    2000?4500 half-blink depth 0.4; mix Both=1; Dormant lid rest 0.3.
  - Expression: Listening BrowRaise 0.4; Thinking BrowFurrow 0.15; Alert
    WideEyes 0.35 / BrowRaise 0.3 / NostrilFlare 0.1 / WideEE 0; ease
    300 ms. ALERT is placeholder-safe until a Windows trigger exists
    (`S25`).
  - Brightness: Idle 1.0 / Listening 1.1 / Thinking 0.75 / Speaking 1.0 /
    Alert 1.25 / Dormant 0.5; Speaking pulse amp 0.05 period 1200 ms;
    ease 600 ms; stagger eyes 0 / brightness 450 / expression 850 ms.
  - Mouth: see `P3-D14` / `P3-D23`.
  - Engine: tick 16 ms idle / 33 ms speaking.
  - Particles: dropped.
  - Life-defaults fingerprint:
    `ef3c2c6eb9894a4fb83d473ba69bfba6e88e44f4ab4da69d88c3585510189777`.
  - Key count: **186 DEBUG / 185 Release**.
  [src: P3-LIFE Closeout Final tuned values / Round 5]

- **P3-D23 ? Mouth timing from observed TTS playback (`TtsPlaybackMonitor`).**
  (New; Track 5 amendment.) The `P2-D15` first-sentence guess (3.3 s) was
  not a reliable audible-onset anchor: estimate-based onset was both late
  and early in tuning [src: P3-LIFE Rounds 2?3]. Measured Armed hold until
  first owned playback segment: **2.3?3.2 s** on multi-sentence turns
  (n=3: 2361?3176 ms); longer tool-style holds are allowed with no timeout
  [src: P3-LIFE Phase 5b]. *(Prompt?s ?2.4?64 s? range: not recorded.)*
  Monitor: ownership by the Hermes serve process tree; poll at 20 Hz; stop
  when the owned session goes Inactive; bout bridge
  `releaseDebounceMs` 450. Mouth state machine: Armed
  (`SpeakingPlaybackArmed`) holds the THINKING look until first playback;
  then Active; `speakingPauseShowsThinking` defaults to false. Forced
  release on cancel / interrupt / SPEAKING clear / pause / scene loss.
  Fail-closed: if the monitor is unavailable, fall back to the estimate
  onset; SPEAKING clear always releases. Peak meter: interface obtained,
  level always 0 ? dropped. Cross-reference: `P2-D01` display-only
  amendment. [src: P3-LIFE Phase 5b]

- **P3-D24 ? The background is composited by the tone-map pass.**
  (New; Track 5 amendment.) Brightness multipliers made the old
  clear-colour invert compensation unworkable in 8 bits. The approved
  look?s field had been displaying `#070707` (invert of the token); it is
  now exactly `#080808` from `ZolaBackground`. Scene alpha is binary for
  this asset; the shader lerps `lerp(ZolaBackground, toneMapped(rgb),
  sceneAlpha)` with output A=1. Fail-closed stays an opaque token clear.
  CSO SHA-256 old
  `a9484343031bdde5dd2d1b09137e91791b6cc30000b5bc82a5882af72014e9e3`
  (1948 bytes) ? new
  `89aa36150afc317544377d8b4b7235ea7b70f19da540cebe3ca5acefc3c298c8`
  (2024 bytes). Invert helpers and constants removed. Look fingerprint
  unchanged (`4392a2e0?`). Amends `P3-D19`/`P3-D20` for the background
  only; bust look unchanged. [src: P3-LIFE Phase 3-D2 / Closeout]

### Machine notes (Latitude 7430)
- Idle GPU (blinks, particles dropped, 60 s): avg **2.2725%** [src: P3-LIFE].
- Static GPU (approved look, 60 s): avg **0.0013%** [src: P3-LOOK A9].
- Speaking GPU (tick 33 ms, 60 s proxy): avg ~**33.6%** [src: P3-LIFE].
- Dormant GPU (60 s): avg **0.0005%** [src: P3-LIFE].
- Cold resting memory (LOOK, 2048?): WS **809 MB** / private 742 MB; peak
  during load **1004 MB**; import 906 ms / wall 2388 ms [src: P3-LOOK
  Closeout].
```

---

### KC2 ? `OPEN_QUESTIONS.md`

#### Replace existing `S17` entry with:

```
- **S17 ? Audio-driven lip sync and precise speaking end.**
  Partially resolved by `P3-D23`: mouth onset and release now follow real
  Hermes TTS playback presence (`TtsPlaybackMonitor`). Still open: the mouth
  cannot see pauses inside a sentence, and motion continues about 1 s after
  audible speech ends (trailing silence in the sentence MP3; e.g. last-bout
  last segment **19722 ms**) [src: P3-LIFE Deferred S17 / Round 4]. Shapes
  remain synthetic. The post-reply follow-up capture still uses the
  `P2-D15` estimate and Hermes's 15 s no-speech timeout (`P2-D06`). Future
  paths: a client-side scan of the MP3 ffplay is playing (envelope and
  silences); Hermes playback lifecycle events (optionally with a
  precomputed envelope). The peak meter returns 0 on this machine [src:
  P3-LIFE Phase 5b]. Evidence: `P3-LIFE_Progress.md` Phase 5b and Phase 6;
  `P2-D14` / `P2-D15`.
```

#### Append after `S23` (new entries; leave `S13`, `S16`, `S18`?`S23` body text unchanged):

```
- **S24 ? GLB asset rework.** Separate eye geometry (saccade), a hair mesh
  (strand shimmer), projection geometry, head/neck articulation (head
  motion, `P3-D22`), a frown/negative mouth target, and an eye-softness
  target (`P3PRE-AUD-10`?`16`). Any rework must keep the 15 morph targets
  and their order, or update `MorphTarget.cs`. [src: plan Lore Closeout]
- **S25 ? HUD data sources.** Attention level, conversational momentum,
  emotional tone, system health, environment, version, and the dock and
  Core Systems destinations (Memory, Environment, Awareness, Behavior,
  Security, Systems, Settings, Account). Each needs a real source first
  (`P3-D06`). `ALERT` has no Windows trigger; its Track 5 values are
  placeholder-safe until one exists [src: plan; P3-LIFE Round 5].
- **S26 ? A missing `message.complete` leaves the turn "Thinking".**
  `_streaming` never clears (Audit 04 ?1b), and the presence stays in
  `THINKING`. Phase 1 behaviour made more visible by Phase 3. [src: plan]
- **S27 ? Mic-input meter in the identity block.** Track 5 did not fill
  the reserved waveform space: the client has no mic level (`P2-D01`), so
  a meter needs a new source (`P3-D07`). [src: plan v1.7]
- **S28 ? Session UI retirement.** The developer expects his memory system
  to make sessions unnecessary. When it does, remove the SESSION HUD line
  and the Sessions dock button together. [src: plan]
- **S29 ? Markdown rendering in chat bubbles.** Bubbles are plain text, so
  fenced code, lists and links show as raw markdown. Predates Phase 3.
  [src: plan]
- **S30 ? Presence backdrop and decoration.** Warm background glow, floor
  rings, base light pooling (concept art), corner brackets if wanted, and
  particles ? all deferred by the developer (`P3-D21`; particles dropped in
  Track 5). On this WinUI + Helix SharpDX surface, Composition `Forever`
  keyframe animations do not advance. Tried: (1) `AnimationController.Progress`
  setter ? access-violates, kills the process; (2) negative `DelayTime` ?
  `ArgumentException`; (3) `CompositionPropertySet.StartAnimation("t",
  Forever)` ? starts, `t` never advances; (4) Forever on ElementVisual /
  ShapeVisual Offset/Opacity ? Start succeeds, Progress stays 0. Any future
  animated decoration must solve that first. [src: plan P3-D21/S30;
  P3-LIFE Phase 7 Composition finding]
- **S31 ? Helix reload memory.** Each F10 debug reload adds about **150 MB**
  of native memory inside Helix's texture registration; managed memory stays
  flat (~160 MB after the first real reload). Ordinary lock, sleep and
  minimize reuse the scene. No product fix in Phase 3; F10 stays debug-only.
  [src: P3-LOOK S31 / Closeout]
- **S32 ? Voice active while Windows is locked (security/privacy).**
  Observed by the developer during the P3-LIFE smoke test (lock/unlock):
  Zola responds to voice while Windows is at the lock screen. Pre-existing
  P2 behaviour ? the voice pipeline runs in Hermes; not caused by Track 5.
  Options: pause the wake word on lock; restrict replies while locked; keep
  deliberately. **Priority: high.** The mantra says "I protect", and a
  locked PC should not answer. [src: P3-LIFE Phase 8 S32; priority/mantra:
  this closeout prompt ? F2]
```

#### Replace closing italic with:

```
*S13 and S16 remain open. S17 updated at Phase 3 closeout; S18?S23 unchanged.
S24?S32 were added at Phase 3 closeout. Resolved items stay in
DESIGN_DECISIONS.md.*
```

---

### KC3 ? `ROADMAP.md`

#### Change heading `## Current stage ? Phase 2 complete` ? `## Phase 2 complete`
(body of Phase 2 section unchanged).

#### Replace `## Phase 3 ? not started` ? through the candidate list with:

```
## Current stage ? Phase 3 complete
Phase 3 closed at five presence tracks plus this lore pass. The Windows
client is presence-first: Helix renders `zola.glb` with the approved unlit
look (`P3-D20` / `P3-D24`), `ZolaDisplayState` owns labels and
`PresenceMode` (`P3-D03` / `P3-D04`), and procedural life drives blink,
expression, brightness, and a TTS-gated mouth (`P3-D22` / `P3-D23`).
Particles were dropped. Idle GPU with blinks averages **2.27%** (? 10%);
static look ~**0.0013%**; cold rest memory **809 MB** (2048?).
1. ? **AUDIT** ? P3PRE presence-UI audit, merged at
   `c2d6110fec5d9ee6c40a0d42d963d3838ab6fd63`.
2. ? **DECISIONS LOCKED** ? `P3-D01`?`P3-D24`. See `DESIGN_DECISIONS.md`
   Phase 3 ? Presence UI. `P2-D01` and `P2-D08` annotated.
3. ? **BUILD PLAN WRITTEN** ? complete. See
   `zola-architecture/lore/build-plans/PHASE3_BUILD_PLAN.md` v1.7.
4. ? **TRACKS EXECUTED** ? five tracks merged.
5. ? **VERIFICATION / SMOKE TEST** ? each track's smoke passed. Track 5
   HUMAN-RUN smoke passed (developer: "smoke test passed") [src: P3-LIFE
   Phase 8].
6. ? **TRACK MERGED**
   - Plan initial: `5994e8bc4e1167c59304ec4b2317f8c9ed9ac94f`
   - Plan v1.2: `a03fda5389305f84668e63e437d9ee9f1b27d500`
   - Plan v1.3: `eba07383ab752bb0e7a4e75d6eeea10636ff7de3`
   - Plan v1.4: `4609c697937d2a5300897ec4575c02b38357f720`
   - Plan v1.7: `819c51b0fab8b5dafb8256fa02a558236191db7a`
   - P3-STATE: `2fb98126eed05561c86b7b3e67ed454b0e7ef331`
   - P3-SHELL: `b8bf6a15c8b806bca0fea499dbcfce0535e92932`
   - P3-RENDER: `f61e1ae014bdf22bc0cab04e128bd93f0ffdebe5`
   - P3-LOOK: `c8f666251deacaf0fcb6a714594abf44da2e931b`
   - P3-LIFE: `8a00f6e87c68d28231d9ba1fc9ec1f4d29de1f40`
7. ? **LORE CLOSEOUT** ? this pass. `S17` updated; `S24`?`S32` filed.
## Phase 4 ? not started
Candidates for Brian to prioritize. Not a committed order. No plan yet.
- `S32` ? Voice active while Windows is locked (security/privacy). Listed
  first.
- `S17` ? Audio-driven lip sync / precise speaking end (remainder).
- `S22` ? Voice naturalness (pacing and inflection).
- `S16` ? Google Workspace (Gmail, Calendar, Drive, Contacts).
- `S20` ? Client cannot answer Hermes clarify-tool requests.
- `S24` ? GLB asset rework.
- `S25` ? HUD data sources (includes ALERT trigger).
- `S13` ? SMS-reading research.
- `S12` ? Daily Brief pipeline.
- `S31` ? Helix reload memory.
```

---

### KC4 ? `Zola_Presence_UI_Architecture.md` (notes only)

#### Under `## Canonical Visual Direction`, insert after the opening paragraph
(before ?The canonical reference asset is:?):

```
> **Windows Track:** On Windows the canonical presence is `zola.glb` rendered
> in-process with Helix Toolkit (`P3-D01`). The approved look is texture-driven
> unlit albedo with sRGB/ACES/gain (`P3-D20`); the field background is the
> `ZolaBackground` token composited in the tone-map pass (`P3-D24`). The SVG
> remains the Android/Compose reference, not the Windows render target.
```

#### Under `### PresenceMode` (after the kotlin enum block, before `### Layer Render States`):

```
> **Windows Track:** Windows adds `DORMANT` when the backend is unreachable
> (`P3-D04`). `ALERT` is defined in life values but has no Windows producer
> yet (`S25`).
```

#### Under `## 5. Animation Controllers` / after `### Purpose` (motion ??5?9 note once):

```
> **Windows Track:** Motion channels are blink, expression, brightness
> (tone-map gain multiplier), and the speaking mouth (`P3-D22` / `P3-D23`).
> There is no breathing and no head motion, by developer decision. Mouth
> timing follows observed Hermes TTS playback presence; shapes remain
> procedural. Particles and backdrop decoration are deferred (`S30`).
```

#### Under `## 14. HUD Layer` / after `### Important Principle`:

```
> **Windows Track:** The HUD shows only true state (`P3-D06`). Identity text
> (wordmark, tagline, mantra) is an explicit exception (`P3-D07`). Attention,
> momentum, emotion, health, environment, version, encrypted link, and
> location are not shown until real sources exist (`S25`).
```

---

### VoiceController tidy (reminder; applied in Phase 3)

As Phase 1: delete L49 bag-of-words comment; change L57 and L59 `P2-D12` ?
`P2-D14`. Zero code tokens.

---

### Phase 2 review checklist

- [ ] F1 first-audio wording OK (2.3?3.2 s; 64 s omitted)?
- [ ] F2 S32 priority/mantra wording OK?
- [ ] Any P3-D wording edits before Phase 3 apply?

---

## Phase 3 ? Write and Verify

Applied the Phase 2 draft (source tags stripped) to lore/docs; VoiceController comment tidy.

### Verify checklist

- [x] Draft entries appear in files (source tags stripped; formatting normalized to 2-space continuations)
- [x] `DESIGN_DECISIONS.md` has `P3-D01`?`P3-D24`; `P2-D01` and `P2-D08` annotated
- [x] `OPEN_QUESTIONS.md` has `S24`?`S32` filed and `S17` updated; `S13`, `S16`, `S18`?`S23` unchanged (`git`/extract proof)
- [x] `ROADMAP.md` marks Phase 3 COMPLETE with plan + track merge SHAs; Phase 4 stub (`S32` first)
- [x] Presence UI doc: exactly four `Windows Track` notes; `+21` lines only
- [x] `VoiceController.cs`: comment-only (deleted bag-of-words comment; L57/L59 `P2-D12`?`P2-D14`); comment-stripped equality **True**; build **0 warnings**
- [x] Cross-refs resolve (cited `P3-D` / `P2-D` / `S` IDs all defined)
- [x] `hermes-agent` clean at `345cd2b057a452236de401d3534b8502a7465e8d`

### Phase 3 Exit Checklist (plan + P3-D23/D24 + S31/S32)

- ? Track 1 (`P3-STATE`) merged ? `2fb98126?` [src: P3-STATE Closeout]
- ? Track 2 (`P3-SHELL`) merged ? `b8bf6a15?` [src: P3-SHELL Closeout]
- ? Track 3 (`P3-RENDER`) merged ? `f61e1ae0?` [src: P3-RENDER Closeout]
- ? Track 4 (`P3-LOOK`) merged ? `c8f66625?`; fidelity judgement recorded; static GPU = 1% [src: P3-LOOK]
- ? Track 5 (`P3-LIFE`) merged ? `8a00f6e8?`; life per `P3-D22`; idle GPU 2.27%; reduced motion in smoke [src: P3-LIFE]
- ? One authority ? labels/`PresenceMode` in `ZolaDisplayState`; morph/gain writes in `PresenceAnimator` [src: track exit criteria]
- ? No UI design literals outside tokens / look file (track exit criteria)
- ? No HUD text claiming unprovable state [src: SHELL/LOOK exit]
- ? `P2-D01` holds for devices; display-only session presence via `P3-D23` amendment
- ? One submit path unchanged [src: track scope]
- ? hermes-agent unmodified / clean
- ? Packages: Phase 2 + two Helix [src: LOOK Closeout]
- ? `dotnet build ? -r win-x64` 0 warnings (this phase after comment tidy)
- ? Track 5 HUMAN-RUN smoke passed ("smoke test passed") [src: P3-LIFE Phase 8]
- ? `DESIGN_DECISIONS.md` `P3-D01`?`P3-D24`; `P2-D08` / `P2-D01` annotated
- ? `OPEN_QUESTIONS.md` `S24`?`S32`; `S17` updated
- ? `ROADMAP.md` Phase 3 COMPLETE; Phase 4 stub
- ? Presence UI Windows Track notes
- ? `P3-D23` / `P3-D24` recorded
- ? `S31` / `S32` filed


---

## Phase 4 ? Closeout

### Pre-closeout lore corrections (developer)
1. `P3-D23`: replaced prompt \"not recorded\" note with **developer-supplied (S17 analysis report)** figures (2026-09-28; `%TEMP%\p3life-s17\`): first owned playback 2.4?4.6 s typical (median 2.6 s), 63.8 s tool-heavy; gaps median 110 / max 138 ms; 6.5 s mid-reply pause; earlier 6.1?8.6 s vs 3.3 s estimate; sets no-timeout Armed hold and 450 ms bout bridge.
2. `S17`: trailing silence wording ? suspected; two screen recordings; not yet measured (removed 19722 ms example).
3. `P3-D08` stray lone `.` removed; `P3-D20` fingerprint sentence ends with `.` before Developer approval.

Cross-ref after corrections: missing IDs **none**.

### 4a
- `dotnet build ? -r win-x64`: 0 warnings, 0 errors.
- `hermes-agent` clean at `345cd2b057a452236de401d3534b8502a7465e8d`.
- Diff scope: G-SCOPE files only (DESIGN_DECISIONS, OPEN_QUESTIONS, ROADMAP, presence architecture, VoiceController comments, this progress).

### SHAs
- Lore commit: `e400abd062f786eb9ff52689f92fddf2331e7fa8`
- Merge SHA on `main`: `159646b312b558430cca77560169347354c891e0`
