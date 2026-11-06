# A13 — Presence UI and Avatar

*Draft v0.2, 2026-11-02 (ARCH-55 to ARCH-58; ChatGPT review). Author: Claude. **Status: approved for the repo by Brian, 2026-11-02 (ARCH-68). States intent; authorises no implementation.***

**Replaces:**
- `Zola_Presence_UI_Architecture.md` (Android): presence-first design, procedural life, glow, ambient state, eyes, mouth, expression, hair, projection, HUD, dock, context panels, authority boundaries, visual restraint, endpoint adaptation, performance and validation.
  - **Kept:** the vision, principles and behavioural intent.
  - **Dropped:** the Compose and Canvas mechanics, the SVG coordinate rules, Android build waves and Cursor rules. These were already superseded for Windows by P3-D01.

**Governing records:**
- Lore: P3-D01–D24 (in particular D01 engine, D03 one display-state authority, D04 modes, D05/D22 motion channels, D06/D07 HUD, D09 idle budget, D17 dock, D20 the look, D21 backdrop, D23 mouth timing, D24 background); P4-D15; P9 Systems panel and proactive bubbles; S17, S24, S25, S27, S30.
- Avatar track (claude.ai project records, not in the repo): `AVATAR_DECISIONS.md` (head motion "plan for it", 2026-10-08; look locked to the current app, 2026-10-26); `AV5_STEP2_SKIN.md` (dots and squares removed); `AV7_EXPORT_PREP.md` (the AV7 `.glb`, the Helix test pending).
- ARCH-21, ARCH-22, ARCH-24, ARCH-26, ARCH-29, ARCH-31, ARCH-54 to ARCH-58.

**Android numbers are unvalidated.** That includes the glow levels, ambient tables and timings. Windows finals are the P3 values.

---

## 1. Intent

> The interface should feel less like "an app screen with an assistant graphic" and more like "a persistent intelligence manifesting through the interface." (Presence UI, kept)

> "I want her to look as she does in the current app. No deviation in coloring. This is not negotiable. This is Zola." (Brian, avatar track, 2026-10-26)

Zola is **seen** as much as heard. The window is her, not an app with her picture in it. She is calm, composed and visibly alive, and her face and body tell the truth about what she's doing: listening, thinking, speaking, waiting or unreachable. Controls appear only when they're needed.

**What this should feel like:**
- Brian glances at the screen and knows at once whether she's listening, thinking or speaking.
- When she's idle, she's present, not frozen. When she's unreachable, she looks it.
- She makes a slight, engaged movement towards the screen when he talks to her, and her hair-ends sway a little as she talks (avatar v2, ARCH-54, ARCH-55).
- The screen never nags. No blinking badge or glowing "I have something" cue (ARCH-21).
- On the phone, it's the same Zola, the full avatar (ARCH-24).

---

## 2. Principles

1. **Presence first.** She is on screen before any control is. Text input, panels and the dock are options, not the anchor (P3-D11, P3-D17).
2. **She looks like Zola, always.** The approved look is locked (§3). Changes to it are Brian's decision.
3. **The visuals show true state only.** Nothing she shows may imply something that isn't happening: no "listening" look while the mic is off, no fake activity indicators (P3-D06; A12 §4.2). Where today's mechanism has known limits, the doc says so (§4).
4. **The UI does presentation work; it authorises nothing.** It schedules animation, plays audio, renders and handles controls. It never independently authorises content, actions or disclosure, writes memory, or speaks as Zola (§9; Presence UI §18).
5. **One display-state authority.** One place turns runtime facts into what she shows (P3-D03).
6. **Motion is meaningful.** She doesn't animate to look busy. Idle life exists so she reads as present, not as a cardboard cutout (Presence UI §3).
7. **Composed, not theatrical.** Her face shifts; it doesn't perform. Expression follows state and fits her identity (A02, "emotionally appropriate").
8. **Visual restraint matches her verbal restraint.** The screen doesn't spam, flash or nag any more than she would (Presence UI §19; ARCH-21).
9. **Same Zola on every screen.** Delivery adapts to the device; she doesn't (A12, ARCH-24).
10. **Performance and accessibility are part of the design,** not a later fix (P3-D09; reduced motion).

---

## 3. Her look

### 3.1 What is locked

**The look is the current app's look, exactly** (Brian, 2026-10-26, avatar track). P3-D20 describes it as "dark skin carrying gold from her own texture, white-gold eyes, glowing diamond and lit hair tips; dots softened", rendered unlit (sRGB decode, gain 4.4, ACES, sRGB encode) on the `#080808` field (P3-D24).

**Carried into avatar v2, same colours** (AV5):
- the dark skin carrying gold;
- white-gold eyes, now on real eyeballs;
- the face centre line;
- the chest diamond and the collarbone gold lines;
- lit hair tips;
- the gold grid on the shaved right side, extended around the back and across the whole nape.

**Deliberately removed in v2** (Brian, AV5 step 2): the skin dot grid and the shoulder pixel squares. *"I don't think we need to carry over the dots and squares."*

**The obsidian-and-gold identity** (wordmark, palette, Rajdhani type) stays (P3-D07, P3-D08).

### 3.2 Stylised, not realistic

The Android doc used pixel projection and hologram effects as "a guardrail against uncanny realism". On Windows:
- The **colouring and unlit gold look are the guardrail.** She reads as an entity, not a photographed person.
- Avatar v2 is more anatomically real (real eyes and lids, a jaw, a skeleton). That serves **natural motion**, not realism for its own sake.
- Particles, rings and backdrop decoration were dropped by Brian: *"Zola's image speaks for itself."* (P3-D21, P3-D22; S30).
- **Projection and hologram effects** (scanlines, edge dissolve, noise shimmer) are **dropped from the intended design** (ARCH-56). Her look already carries the entity feel. They can be revisited deliberately later.

### 3.3 The avatar (status)

| Asset | State |
|---|---|
| `zola.glb` (PROD, v1): Meshy-derived bust, 15 morphs, no skeleton | live in the app |
| `zola_av7_v1.glb` (v2): MPFB base fitted to Zola, 67 expression keys (52 ARKit + visemes), real eyeballs, teeth and tongue, 212-joint skeleton including 49 hair-end bones, PROD hair with movable ends | exported 2026-10-27; **Helix test pending** |

**Integration of v2 is its own scoped phase** (AVATAR_DECISIONS). It needs at least:
- a shape-key schema for 67 keys instead of 15;
- a bone writer (head, eyes, hair ends);
- multi-mesh morph binding (today `FindMorph` binds the first skinned mesh only);
- framing: v2 is full-body at real scale, while PROD was a bust;
- per-eye gaze mapping (the eye-bone axes are mirrored);
- the 11 old fringe keys mapped or dropped;
- the 4-bone-influence check on head and hair motion.

**Memory:** the whole v2 asset and rendering pipeline must fit the client's **cold-rest memory gate of 900 MB** (P3-D13; 809 MB measured with PROD at 2048²). The 4096² skin is one input to that measurement, not a separate allowance.

---

## 4. States: what she looks like when

From P3-D04 and P3-D22, as built:

| Mode | When | How she looks (today) |
|---|---|---|
| **Idle** | Nothing happening | Natural blinks every 3–8 s; full brightness |
| **Listening** | Capture or transcribing | Brows slightly raised; brighter (×1.1) |
| **Thinking** | Generating | A slight furrow; half-blinks; dimmer (×0.75) |
| **Speaking** | Her voice is playing (see limits below) | The mouth follows her voice; a gentle brightness pulse |
| **Waiting for Brian** | A clarify is open | Mapped into presence and the HUD (P4-D15) |
| **Alert** | *Defined, no producer yet* (S25). **Only for an urgent item A10 has authorised her to present now** (ARCH-58) | Wider eyes, raised brows, brighter (×1.25). Attentive, not startled |
| **Dormant** | Backend unreachable | Lids at rest 0.3, half brightness, no blinks |

**Changes are staggered**, which already exists: the eyes respond first, then brightness, then expression (0 / 450 / 850 ms). The effect is that she *reacts* rather than *switches*.

**Immediate truth outranks staggered animation** (ChatGPT review, adopted). These take effect **at once**, not after a stagger:
- capture stops;
- the connection is lost (Dormant);
- her speech is cancelled or interrupted;
- the audience changes (§7);
- the conversation hands off to another device (A12 §7).

**A delayed transition that's overtaken never fires afterwards.** It can't put her back into a state she has already left.

**Every state must be true,** within the stated limits of today's mechanism. For example, she never shows Listening on the PC while the phone has the conversation (A12 §7).

**Speaking: today's limits** (P3-D23). Speaking follows **observed playback**, with two known approximations:
- a **450 ms bridge** between sentences keeps the mouth in speaking mode across short gaps;
- if the playback monitor is unavailable, onset falls back to an **estimate**.

SPEAKING always releases when speech ends or is cancelled. **For the future:** mouth timing is driven from playback **at the endpoint actually producing the sound**, including cancellation and handoff (A12).

**The mic indicator says exactly what's happening** (ChatGPT review, adopted). Once she listens without a wake word (ARCH-31), these are different states and are named differently:
- **mic active:** local audio processing is running, nothing accepted;
- **capturing your turn:** speech has been accepted as directed to her;
- **transcribing:** turning it into text.

Her face may simplify (for example, Listening only when capturing a turn), but the indicator is precise.

---

## 5. Motion and life

### 5.1 Decided

| Motion | Decision | Source |
|---|---|---|
| Blink, expression, brightness, speaking mouth | Built | P3-D22 |
| **Head motion** | **Wanted.** Was "none; the model wasn't made for it", reversed when v2 was planned: "Yes, plan for it." | P3-D22 → AVATAR_DECISIONS 2026-10-08; **ARCH-54** |
| **Hair motion** | **Wanted**, mainly the hanging ends (49 hair-end bones in v2) | Avatar track; **ARCH-54** |
| **Breathing** | **None.** *"Not necessary for AI to breathe."* | P3-D22 (Brian) |
| Particles | Dropped | P3-D22 |

**Matrix B12 is answered by ARCH-54:** "no head motion" was a **temporary limit** of the old model, not a boundary.

### 5.2 What head, eye and hair motion should do (vision, for the integration phase)

Kept as intent from Presence UI §3, §9 and §12, adjusted to the decisions above:
- **Gaze and head (ARCH-55):**
  - small, slow movements at idle (eye drift every few seconds);
  - a slight engaged movement **towards the viewer** (the screen) when she's addressed or listening ("attention leaning");
  - steadier while she's speaking.
  - Spring-like, never abrupt.
  - **A known direction is required for anything more.** Being addressed doesn't tell her where the speaker is standing. Without a qualified position source (A09), she never appears to track someone around the room, with head or gaze.
- **Hair ends:** a slight, natural sway that follows head motion and her speech, not a constant wave. Strands don't move in lockstep.
- **Eyes:** aware, not aggressive. Never a fixed stare and never horror-bright.
- **Mouth:** procedural today, timed to observed playback (P3-D14, P3-D23). v2's visemes allow real **viseme-timed speech** later if the voice provider exposes timing. *The mouth supports her speech; she should never look like a talking cartoon.*
- **No new motion without a reason.** Every motion maps to a state or a natural idle behaviour, within the idle performance budget (§10).

*Exact ranges and timings are set in the integration phase. Android numbers are unvalidated.* **Confirmed as the target (ARCH-55).**

### 5.3 Expression

Expressions **follow state and her identity**: calm baseline, focus, warmth, concern, alertness, uncertainty. They are never theatrical (Presence UI §11). Later inputs may include the tone of the moment (A02b §5.1), but **her face never claims a feeling about the person** that she hasn't been told (A14 P15). It only reflects her own state.

---

## 6. Around her: HUD, dock, panels and conversation

**As built:**
- **HUD: true state only** (P3-D06). Voice block (label and mic line), time, session, link and notices. Identity text is an explicit exception (P3-D07). Hidden until real sources exist (S25): attention, momentum, emotional tone, environment, location.
- **Systems panel** (P9, P10): Backend, Workspace watcher, Google account, Ranking, Voice, and later Phone. A dim dot when healthy, gold for attention, red for down.
- **Dock:** hidden until needed. It appears on pointer, keyboard focus, an open overlay or a streaming turn, and fades after 2 s (P3-D17).
- **Conversation overlay** on demand (P3-D11). Her unprompted lines appear as her own bubbles (P9).
- **Notices** fade after 4 s; problems stay (P3-D18).

**Vision, kept:**
- **Panels orbit the presence;** they never replace her as the centre. Candidate panels: conversation, memory (what she knows, A14 §7.3), environment, systems, settings (proactivity, privacy, permissions, learned style, ARCH-48), later security and cameras (A09).
- **Panels show authoritative state** and offer approved actions. A panel showing an approval shows exactly what's being approved, but the approval itself follows A15 (on the PC, the passphrase; ARCH-27 on the phone).
- **HUD items appear only when a real source exists** (S25). There are no decorative gauges.

---

## 7. Visual restraint

- **No on-screen attention cue** (ARCH-21). She never signals "I have something" with a glow, badge or pulse on the PC. She asks aloud, or the item waits. *This replaces the Android "foregrounding levels" and a presence-glow door-knock.*
- **Interjections wait for a pause** (ARCH-22). The same applies to anything visual that would interrupt.
- **Calm when it's busy.** During intense conversation or high attention heat (ARCH-18), she keeps decorative motion low (Presence UI §19). Urgency sharpens her; it never makes her frantic.
- **Quiet hours and Dormant are visibly quiet.**
- **A waiting item never changes her expression** (ARCH-58). That would be a silent attention cue, against ARCH-21. Alert is only for an urgent item A10 has authorised her to present now.

**Privacy on screen (ARCH-57).** Text on a screen is a **channel**, like speech (A14 §5.1, check 3). When the audience changes or may have changed:
- **Prevent:** newly disallowed content doesn't appear.
- **Conceal:** protected content **already visible** is hidden, at once.

This covers everything on screen: conversation history, text still streaming in, memory panels, approval details and notifications.

**Recognition alone doesn't establish who can see the screen.** Someone can be in view of it without speaking. The requirement is fixed; the detection mechanism is open (A09).

---

## 8. Every screen

| Endpoint | Presence |
|---|---|
| **PC** | The full window: presence, HUD, dock, panels (as built) |
| **Phone (companion)** | **The full avatar** (ARCH-24). Layout open until there's a mockup; the leaning is the full avatar for voice and a smaller presence for typed chat (ARCH-55, A12 Q-D4). Notifications say only "Zola needs your attention" (ARCH-26). States shown are the phone's real states (A12 §4.2). "Can't reach Zola" is a status message, not an answer from her (A12 §9) |
| **Shop and car devices** | Android companions: the same as the phone (ARCH-29). The car keeps visuals minimal while driving (A08) |
| **Glasses, wearables** | Vision. Glanceable, minimal, the highest bar for showing anything |

**The avatar must perform on each device.** On the phone, a lighter rendering of the same look may be needed. Whatever runs, it must be recognisably her and must not change her colours (§3.1).

---

## 9. What the UI may and may not do

**May (presentation work):**
- render and animate state, including scheduling its own animation and transitions;
- play audio it's given;
- show system output and passive status;
- handle controls and offer approved actions through approved channels;
- show a status message, such as "can't reach Zola" (A12 §9).

**Must not (authority):**
- independently authorise content, disclosure or actions;
- generate facts or reinterpret her answers;
- decide *what* she says or whether something should be raised (A10);
- run tools or approve anything by itself (A15);
- write memory;
- override privacy (A14);
- speak as Zola on its own;
- show a state that isn't true (§2 p3).

*Presence UI §18, kept. Windows equivalent of "no cognitive classes in composables": the client's presence code reads display state only (P3-D03).*

---

## 10. Performance and accessibility

- **Idle budget:** at most 10% GPU on the Latitude 7430, averaged over 60 s (P3-D09). Today's idle is about 2.3%. **Head and hair motion must fit within it.** If they don't, the motion is simplified before the budget is raised (Brian's call).
- **Speaking is measured separately** from idle, as P3 did (about 33.6% at the 33 ms speaking tick).
- **Animation must not hurt audio responsiveness.** A check confirms that animation work doesn't delay capture, playback or the speech track's timing (A07).
- **Memory:** the whole client, with v2 loaded, stays under the **900 MB cold-rest gate** (P3-D13).
- **Reduced motion:** Windows' setting is honoured. Blinks stay. Idle drift, hair sway and transition animation are reduced or instant (Presence UI §23, kept; dock fades are already instant under it, P3-D17).
- **Phone:** frame rate and battery on the real device decide the phone's rendering (A12 Q-D4).

---

## 11. As built on Windows (2026-11-02)

| Capability | State | Evidence | Decisions |
|---|---|---|---|
| `zola.glb` in-process with Helix 3.1.2; approved unlit look; `#080808` field | live-tested | P3 | P3-D01, D02, D20, D24 |
| One display-state authority; modes including Dormant | live-tested | P3 | P3-D03, D04 |
| Blink, expression, brightness, speaking mouth; staggered transitions | live-tested | P3 | P3-D22, D23 |
| Waiting-for-Brian state during a clarify | live-tested | P4 | P4-D15 |
| HUD true state only; identity text; dock hidden until needed; notices | live-tested | P3 | P3-D06, D07, D17, D18 |
| Systems panel; proactive lines as bubbles | live-tested | P9 | — |
| Idle 2.3% GPU | measured | P3 | P3-D09 |
| Avatar v2 (`zola_av7_v1.glb`) | exported; **Helix test pending** | AV7 | AVATAR_DECISIONS |
| Head and hair motion, gaze, visemes | **not built** (needs v2 integration) | — | ARCH-54 |
| Alert producer; attention, momentum and environment HUD items | **not built** | — | S25 |
| Phone presence | **not built** | — | P12-D01, ARCH-24 |

---

## 12. Limits

| Limit | Kind | Accepted risk | Note |
|---|---|---|---|
| No head or hair motion | temporary limit | — | ARCH-54; v2 integration |
| Alert never produced | temporary limit | — | S25 |
| HUD items hidden without real sources | lasting boundary (true state only) | — | P3-D06 |
| No on-screen attention cue on the PC; a waiting item never changes her expression | lasting boundary | — | ARCH-21, ARCH-58 |
| Screen privacy: prevent and conceal on audience change | lasting boundary | — | ARCH-57 |
| No breathing | Brian's decision | — | P3-D22 |
| No hologram or projection effects | Brian's decision (revisitable) | — | ARCH-56 |
| Speaking state uses a 450 ms bridge and an estimate fallback | temporary limit | yes | P3-D23 |
| No head or gaze tracking of people around the room without a qualified position source | lasting boundary | — | ARCH-55 |
| No particles or backdrop decoration | Brian's decision | — | P3-D21, P3-D22 |
| Colouring locked to the current app | lasting boundary | — | Brian 2026-10-26 |
| UI never authorises content, actions or disclosure, writes memory or speaks as Zola | lasting boundary | — | §9 |
| Idle GPU budget | lasting boundary unless changed | — | P3-D09 |

---

## 13. Open questions

**Resolved 2026-11-02** (Brian: "go"):
- **Q-U1.** Phone layout stays open until there's a mockup; the leaning is the full avatar for voice and a smaller presence for typed chat (ARCH-55).
- **Q-U2.** Subtle head movement, idle gaze and hair following motion, towards the viewer unless a qualified position source exists (ARCH-55).
- **Q-U3.** Hologram and projection effects dropped from the intended design; revisitable deliberately (ARCH-56).
- **Q-U4.** Screen privacy: both prevent and conceal (ARCH-57).
- **Q-U5.** Alert only for an urgent item A10 has authorised her to present now; a waiting item never changes her expression (ARCH-58).
- **Q-U6.** The reserved waveform space is released (S27); added later only for a real purpose (ARCH-56).

**Still open:**
- **The phone layout itself** (A12 Q-D4), once there's a mockup.
- **How the screen audience is detected** (A09).

---

## 14. Acceptance scenarios

- **U1. True state at a glance.** Over a session, each state shows only when it's true: listening only while capturing, thinking only while generating, speaking only while her voice plays, Dormant when the backend is down.
- **U2. Unreachable looks it.** Serve stops. She goes Dormant within the reconnect window, and the HUD notice stays until recovery.
- **U3. No nagging screen.** An eligible item is waiting while Brian works. No glow, badge or pulse appears. She asks aloud at a good moment, or it waits (ARCH-21).
- **U4. Look unchanged** (at v2 integration). Side by side with PROD through the same pipeline, per-region colour difference within the approved tolerance; Brian's "is this Zola" verdict; dots and squares absent as decided.
- **U5. Head and hair** (at v2 integration). Addressed, she turns slightly towards Brian; while she talks, her hair-ends sway a little. Idle stays calm. The idle GPU budget holds.
- **U6. Reduced motion.** With Windows reduced motion on, blinks stay; drift, sway and transitions are reduced or instant.
- **U7. Phone is the same Zola** (when built). Same colours and character on the phone; states match the phone's real activity.
- **U8. UI can't act.** No click in a panel sends an email or writes memory without going through A15 and A03.
- **U9. Audience change with private text open.** Brian has a private conversation open in the overlay. Someone walks into view. The protected text is hidden at once, streaming text included, and nothing new and protected appears (ARCH-57).
- **U10. Cancel during a delayed transition.** Brian cancels her mid-sentence just as a staggered expression change is scheduled. She stops speaking at once, and the delayed change never fires afterwards.
- **U11. Phone handoff during speech** (when built). She's speaking on the PC when Brian picks up the phone. The PC's mouth and speaking state stop immediately; speaking shows only where the sound is actually playing (A12 §7).
- **U12. Mic indicator precision** (when wake-free listening exists). Room talk not directed at her: the indicator says the mic is active, not that she's capturing his turn.
- **U13. No direction, no tracking.** Brian speaks from across the shop. She makes an engaged gesture towards the screen; her head and eyes don't swing around the room.
- **U14. Animation doesn't slow her ears.** With head and hair motion running, capture start and first-word retention measure the same as without them (A07).

---

## 15. Coverage of the source docs

**Status of this map.** "Verified" means the destination section exists and was checked against the source.

**`Zola_Presence_UI_Architecture.md`**

| Source section | Destination | Treatment | Status |
|---|---|---|---|
| Vision; presence-first interface | §1, §2 p1 | preserved | verified |
| Canonical visual direction; SVG; fonts | §3.1 | superseded for Windows by P3-D01, D07, D08, D20; SVG is not a Windows target | verified |
| §1 Presence layer | §2, §4 | merged | verified |
| §2 Static visual reconstruction | — | superseded (Windows renders the 3D model, P3-D01) | verified |
| §3 Procedural life (heartbeat, momentum glow, attention leaning, jitter, idle personality) | §5 | merged; breathing dropped by Brian (P3-D22); attention leaning kept for v2, towards the viewer (ARCH-55); momentum glow and jitter not adopted | verified |
| §4 Animation architecture; modes; layer states | §4; P3-D03 | merged; DORMANT added; Compose types dropped | verified |
| §5 Animation controllers (blink, saccade, breathing, mouth, expression, hair) | §4, §5 | merged | verified |
| §6 Glow hierarchy | §4 | superseded by brightness per mode (P3-D22) | verified |
| §7 Ambient state | §4 | superseded (no particles) | verified |
| §8 Mode transition staggering | §4 | preserved (built) | verified |
| §9 Eye system | §5.2 | preserved as intent | verified |
| §10 Mouth and speech | §5.2 | preserved; P3-D14/D23 as built | verified |
| §11 Facial expression | §5.3 | preserved | verified |
| §12 Hair and energy field | §5.1, §5.2 | adapted to hair-end bones (ARCH-54) | verified |
| §13 Hologram and pixel projection | §3.2 | dropped from the intended design (ARCH-56) | verified |
| §14 HUD | §6 | preserved with P3-D06/D07 | verified |
| §15 Bottom dock | §6 | preserved with P3-D17 | verified |
| §16 Context panels | §6 | preserved as vision | verified |
| §17 Functional UI integration | §6, §9 | merged | verified |
| §18 Authority boundaries | §9 | preserved | verified |
| §19 Visual restraint | §7 | preserved; foregrounding cues replaced by ARCH-21 | verified |
| §20 Endpoint adaptation | §8 | merged with A12 decisions | verified |
| §21 Implementation architecture (Kotlin packages) | — | intentionally dropped (Android) | verified |
| §22 Build waves | — | intentionally dropped (Android; Windows P3 tracks are the record) | verified |
| §23 Performance boundaries | §10 | principles kept; Android specifics dropped | verified |
| §24 Cursor execution rules | — | intentionally dropped (Android) | verified |
| §25 Validation criteria | §14 | merged | verified |
| End state; final principle | §1 | merged | verified |
