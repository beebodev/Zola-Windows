# A09 — Physical Perception

*Draft v0.2, 2026-11-02. Author: Claude. **Status: approved for the repo by Brian, 2026-11-02 (ARCH-68). States intent; authorises no implementation.***

*v0.2 changes (ChatGPT review, Brian: "go"):*
- *Privacy protection acts immediately and doesn't wait for A10.*
- *The webcam is partial evidence.*
- *Confidence and urgency are separated.*
- *Corroboration needs independent sources, and observations can be revised.*
- *Switching off is defined.*
- *The observation log has retention tiers.*
- *Excluded zones are masked before processing.*
- *Cloud vision is limited to a stated purpose.*
- *Three new scenarios.*
- *Q-P1, Q-P3, Q-P4 and Q-P5 are decided (ARCH-59 to ARCH-64). Q-P2 and Q-P6 are partly open.*

*Coverage-map pass, 2026-11-02: coverage rows closed with exact sections; additions from fresh reads of the source docs (see `audit/arch-docs-swap/ARCH_DOCS_COVERAGE_MAP.md` §5).*

*Phase 10 closeout pass, 2026-11-06: as-built rows and Phase 10 citations rechecked against the Phase 10 lore closeout (tag `p10-closed`) in ARCH-SWAP Phase 2; P10-D18 and P10-D19 cited where they belong.*

**Replaces:**
- `Zola Environmental Perception Architecture.md`: cameras, doorbell, motion, shop and home sensors. Covers the pipeline from sensor to structured event, zones, persistence, correlation, confidence, continuity, memory, privacy, failure, observability and future vision.
- `Zola_Architecture_Perceptual_Input_Layer.md` (Android, phone-centric): the watchdog and active-perception tiers, the observation types, identity recognition, foregrounding, the privacy contract.
  - **Kept:** the principles.
  - **Dropped:** the phone camera specifics (ML Kit, CameraX, orientation policy).
  - **Superseded:**
    - foregrounding, by ARCH-21;
    - third-party biometrics, by ARCH-07;
    - "high confidence before high urgency" (P5), by ARCH-63.

**Governing records:**
- ARCH-05 (never recordings), ARCH-06, ARCH-07 (learns faces and voices; recognition is not permission), ARCH-12, ARCH-21, ARCH-28, ARCH-30 (overheard speech discarded), ARCH-37 (visitor signatures two weeks), ARCH-53, ARCH-55, ARCH-57, ARCH-58, ARCH-59 to ARCH-64.
- A03 §3.2/§5.3 (sensor promotion: recurrence plus confirmation for unknown entities), §5.6 (a durable recurrence record), §5.7 (never promotable); A05 §8 (coverage); A08 (user state, sources); A10 (judgment); A13 (screen privacy); A14 (privacy, P5, P7).

**All of this is vision.** Nothing in A09 is built on Windows. The PC has an integrated webcam and microphone, and the phone has cameras. No camera or sensor is used for perception today. The Android thresholds (confidence levels, frame rates, recurrence counts, retention windows) are unvalidated.

---

## 1. Intent

> "Perception is not attention." (Environmental Perception, kept)

> "This is her world, so she can keep what she observes." (Brian, ARCH-05)

Today Zola knows the world only **as reported**: what people tell her, what email, texts and calendars say, what the phone reports. Physical perception lets her **notice for herself**:
- who's at the desk;
- that someone has come into the shop;
- that a car has pulled into the drive;
- that the compressor's been running for an hour.

She uses that to **understand**, not to watch. Most of what she perceives never becomes speech. She keeps understood facts, never recordings.

**What this should feel like:**
- She knows Brian is at his desk without being told, and that he just stepped away, so she holds what she was about to say (A10 timing).
- She sees someone else come into the office, so she stops showing something private, immediately (ARCH-57).
- "Micah's car just pulled in." She noticed it arrive, and she says so only if it matters (A10). She doesn't claim more than the camera showed.
- An unfamiliar person has been near the shop for twenty minutes after dark. That's worth a careful word, and it's never a camera feed or a creepy play-by-play.
- "I may be hearing a smoke alarm in the shop. Can you check?" She says it while she's still unsure, because waiting could cost too much.
- In the shop, she can tell the grinder is running and keeps her answers short.

---

## 2. Principles

1. **Perception is not attention.** Seeing or hearing something never directly causes speech, a notification or an action. Whether she *says* anything goes through A10's single decision point (Environmental Perception; Perceptual Input P3).
2. **Privacy protection doesn't wait for judgment** (ARCH-64). When perception suggests the audience may have changed, A14 and A13 act on it **at once**: they hide protected content, stop a disclosure in progress and drop the assumption that only Brian is present. A10 decides whether to *say* something; it never delays a privacy restriction.
3. **Silence is the default for speech.** Most perceived activity ends as nothing, or as a quiet record at most. Speaking has to be earned (A10).
4. **Never recordings.** Frames and audio are processed in memory and discarded. What's kept is understood meaning: a typed observation, with confidence and time. **No debugging exceptions** (ARCH-05; Perceptual Input P1).
5. **Overheard speech isn't kept.** Speech from conversations she isn't part of is used only to judge attention, then discarded (ARCH-30). Non-speech sound (a grinder, an alarm, a car) is classified, never recorded (A08).
6. **Perception is evidence, not truth.** Every observation carries confidence, time and coverage. Uncertain perception produces uncertain claims, never confident ones (A03).
7. **What a sensor didn't see is not evidence of absence** (ARCH-64). "No other face detected" never becomes "Brian is alone". A camera that's offline means she *doesn't know*, not that *nothing happened* (A05 §8).
8. **Confidence and urgency are separate** (ARCH-63). Uncertainty lowers how strongly she states something. It doesn't automatically mean silence when the possible consequence is serious.
9. **Recognition identifies; only policy permits** (ARCH-07). Knowing it's Bre at the door grants Bre nothing.
10. **Workers observe; they never act.** Perception components classify and report. They never speak, notify, write memory or act. Distribution adds capability, not authority (Environmental Perception §13).
11. **Visible and controllable.** People can tell when she's perceiving. Each source and zone can be switched off, and switching off stops it at the source (§7.2).
12. **Richer input never creates new authority.** Better vision doesn't let her do more without permission (Environmental Perception §17; A15).

---

## 3. What she could perceive

| Source | What it could tell her | Notes |
|---|---|---|
| **PC webcam** | Brian at the desk or away; how many people are **in view**; someone new **in view** | **First** (ARCH-59). **Partial evidence only** (§5.1): it can show someone is there, never that nobody else can see or hear. Feeds screen privacy (ARCH-57) and head and gaze direction (ARCH-55) |
| **PC microphone (non-speech)** | Room noise level; a loud event; activity sounds | Never speech content from conversations she isn't part of (ARCH-30) |
| **Phone camera** | Who's using the phone, for ARCH-28 recognition | Only for that purpose and only while the app is in use (ARCH-59) |
| **Shop sensors** (camera, microphone, mounted device) | Someone in the shop; tools running; the bay door open | **Next candidates** (ARCH-59). Through the Android shop device (ARCH-29) or dedicated sensors. *Which hardware is open (Q-P2)* |
| **Home and security cameras, doorbell** | Arrivals and departures; packages; unknown people lingering | *Depends on what Brian has or adds (Q-P2)* |
| **Vehicles** | A known car arriving or leaving | By confirmed appearance; plates deferred (ARCH-61) |
| **Wearables, glasses** | First-person context | Far vision |

---

## 4. From sensing to understanding

Kept from Environmental Perception as intent. Android component names are dropped.

| Stage | What happens |
|---|---|
| **1. Input, at the source** | Only permitted sources and zones are read. **Excluded zones are masked before any processing or transmission** (§7.1) |
| **2. Normalise** | One real event is one signal. Duplicates and flicker are removed. Sensor quality is noted |
| **3. Two tiers** | A light **watch tier** only notices that something changed: motion, a face present, a loud sound. No identity, no storage, no network. It hands off to an **active tier** that understands: who, what, where. *Kept from Perceptual Input §1* |
| **4. Specialists classify** | Separate workers for presence, people, vehicles, packages, sounds and scene change. Each produces typed observations with confidence and **source lineage** (which sensor, which frame or moment), and never acts |
| **5. Where and how long** | Observations are placed in **named zones** (driveway, shop interior, desk) and tracked over time: "unknown person near the shop for eleven minutes", not three motion blips |
| **6. Correlate** | **Independent** sensors agreeing raises confidence (the doorbell plus the driveway camera). Two analyses of the same frame, or repeats from one camera, are **duplicates, not witnesses**. Disagreement lowers confidence only when both sensors could reasonably have seen the event |
| **7. A structured item** | One item into the governed intake (A08 §4), with zone, time, duration, confidence, coverage, lineage, sensitivity and expiry |
| **8. Act and judge** | Two paths, from the same item. **Privacy restrictions** (an audience change) go to A14/A13 **at once** (§2 p2). **Whether to say anything** is A10's decision. Perception has no further say |

**Observations can be revised.** "Unknown vehicle" can later become "delivery van, confirmed". The revision replaces the earlier reading and keeps the history of how it changed, so A10 and §9 explanations use the current understanding.

**Continuity is the point.** Duration and persistence carry meaning that single snapshots don't (Environmental Perception §10).

---

## 5. What she does with what she perceives

### 5.1 Who's here

The most valuable early use is simply **knowing who is present**:
- **Brian at his desk, or away**, which shapes timing (A08 user state; A10).
- **Others in the room or in view of the screen**, which feeds the audience checks (A14 §5.1, check 2), screen privacy (ARCH-57) and the shared-session rules (ARCH-17).
- **Who is speaking**, combined with voice (A07 §8), for verification (ARCH-12, ARCH-28).

**The webcam supplies partial evidence** (ARCH-64):
- It can establish that someone **is** in its view. It **cannot** establish that nobody else can see the screen or hear her. Someone off-frame, behind the laptop or partly hidden still counts.
- So a detected newcomer **tightens** privacy at once. Seeing no one else **never loosens** it. Whether Brian is alone comes from all the evidence A14 uses, with the webcam as one input.
- The same care applies elsewhere. Micah's car arriving supports "his car is here", not automatically "Micah is home".

**Presence isn't identity, and identity isn't permission.** A face in view tells her someone's there. Recognition tells her who it probably is. Neither grants anything (ARCH-07).

### 5.2 Memory from perception

**Three tiers of retention.** "Typed observations only" can still become a detailed record of someone's movements, so each tier has limits:

| Tier | What it holds | How long |
|---|---|---|
| **Moment** | Individual observations: Brian at his desk, motion in the drive | Short-lived. Feeds the current moment and expires (A08 §4). *The exact window is unvalidated* |
| **Pattern record** | Bounded counts and summaries needed to learn a recurrence ("silver truck, evenings, four separate days") (A03 §5.6) | Bounded in size and age. Holds summaries, not a timeline of each sighting |
| **Memory** | What has passed A03's promotion rules: recurrence across separate days, plus confirmation for unknown entities | Like any memory; forget reaches it |

- **Unknown entities need confirmation.** "I've noticed a silver truck in the drive a few evenings. Someone you know?" She never names someone from sensing alone (A03 §5.7).
  - **Brian names it:** it becomes a known entity.
  - **Brian dismisses it:** it isn't promoted, and she doesn't ask again unless the evidence changes.
  - **Brian says "not now":** it stays a candidate and she may ask once more later.
- **A contradiction breaks the pattern.** Inconsistent observations reset the count. Many sightings within one day count as one.
- **Never promotable from sensing:** a mood as a trait of someone; who an unconfirmed person is; perception combined with hearsay without the person's confirmation (A03 §5.7).
- **Forget reaches it:** forgetting a person or a visit removes the observations, pattern entries and memories derived from them (A03 §12).

### 5.3 Reading people's state

The Android layer read facial expressions and vocal stress. On Windows, **ARCH-53 applies to faces too (ARCH-60)**:
- **Not at first.** Her reads of someone's state start from what's said and explicit feedback.
- **Later, at most a weak, temporary hint,** once qualified, and only to shape her own delivery. It is:
  - **never stored**;
  - never stated as fact ("you seem…");
  - never shared;
  - never on its own a lasting judgment (A02b §5.3; A14 P15).

---

## 6. Recognition of people and vehicles

**Faces and voices (ARCH-07, ARCH-37):**
- She learns the face and voice of **anyone she sees**. This supersedes the Android rule that third-party biometrics are never captured (Perceptual Input P4).
- **Signatures only, kept on the PC.** Never images or recordings, and never sent to a cloud service, even with cloud vision on (A07 §8.3; A14 §8; ARCH-62).
- **A visitor's signature lasts two weeks** (ARCH-37):
  - The expiry reaches **every copy and anything derived from it** (a match index, a cached embedding).
  - **Seeing the visitor again doesn't quietly make them permanent.** A visitor becomes a known person only when Brian or A03's confirmation rules say so.
  - People deliberately known are kept until deleted.
- **Viewable, renamable and deletable** by Brian; each person can see what she holds about themselves (A14 §7.3).
- **Recognition never approves anything** (ARCH-07, A15 X3).

**Vehicles:**
- **Known-vehicle recognition** (Micah's 4Runner) works like any other entity: confirmed by a person first (A03).
- **Licence-plate recognition is deferred** (ARCH-61) until there's a concrete use that recognising a car by its appearance can't handle. It would then be a separate, sensitive decision (Environmental Perception §14).

---

## 7. Privacy and control

### 7.1 What enters, and where it's processed

- **Never recordings** (§2 p4).
- **Excluded zones are masked at the input**, before classification, storage or transmission. A bathroom, a neighbour's yard or any area Brian excludes never enters the pipeline. **A sensor that can't mask an excluded area isn't enabled for that view.**
- **Local first** (ARCH-62). Perception and recognition run on the PC or the device.
- **Cloud vision is off by default** (ARCH-62). Brian can enable it for a **stated purpose**, with a defined input scope (for example, "describe what's in the drive when a package is left"). It never covers biometrics. Enabling it never overrides the biometric rules or another person's privacy (A14 §6).

### 7.2 Switching off

Each source can be set to **full**, **presence only** or **off**:

| Setting | What it means |
|---|---|
| **Presence only** | Detects that someone is there. **No identity matching and no face or voice learning** |
| **Off** | Collection stops at the source. **In-progress processing stops**, and queued observations from that source are **dropped**. Already-stored history follows its own retention and delete rules (§5.2) |

**With perception off, she still works fully.** She just doesn't observe. She **doesn't offer anything that depends on recognition** as if it were still available, such as recognition-based approvals or disclosure on the phone (ARCH-28). She falls back to the rules for an unverified person.

### 7.3 Visible and answerable

- **Visible:** an indicator shows when active perception is running (Perceptual Input §5). It is a **status**, not an attention cue (ARCH-21; A13 §7).
- **A perception log in plain words** is available on request (Perceptual Input §5). For example: "Noticed you at your desk at 2:14. Someone came into the shop at 3:40."
  - It shows only what the retention tiers still hold (§5.2).
  - It is subject to A14: each person sees only what concerns them.
- **Household and guests.** Perception follows the same per-person privacy as everything else (ARCH-03, ARCH-13). Brian's camera seeing Bre come home is **Bre's** information. It isn't told to anyone else without the A14 checks.

---

## 8. Failure and honesty

- **A sensor offline** means that zone's coverage is **partial or unknown**, and confidence drops. She never makes confident claims about a zone she can't see (Environmental Perception §15).
- **Coverage is tracked over time** so she can honestly say "the shop camera was down from two to four, so I can't say" (A05 §8).
- **A worker failing** doesn't stop the others. Its kinds of event are marked unavailable.
- **Expired observations never drive decisions.** Every item carries an expiry (A08 §4).

---

## 9. Explainable

She must be able to answer, from records rather than memory (Environmental Perception §16):
- Why did she mention this? Why did she stay silent?
- Which sensors contributed, were they independent, and how sure was she at each step?
- Was it in a permitted zone? Was it passed to judgment, or dropped earlier, and why?

**Explanations respect retention.** Records hold **metadata and typed observations only**, never frames or audio (ARCH-05; P8-D11 pattern). They last only as long as their tier (§5.2). She never keeps every detection just to explain every silence. Past the window, the honest answer is "I don't have the details any more".

---

## 10. Security and safety (vision)

An unknown person near the shop at night, smoke or alarm sounds, a door left open: these are where perception matters most.
- **Still one path.** Such items go to A10 like everything else. A10's urgent path may present them now, and only then may Alert show (ARCH-58).
- **Uncertain but serious can still be raised** (ARCH-63). A10 weighs the **evidence**, the **possible consequence** and the **cost of waiting**. She keeps an uncertain claim uncertain: "I may be hearing a smoke alarm. Can you check?", never "There's a fire." A low-confidence detection of something minor still produces nothing alarming.
- **Each kind of safety event gets its own rule** (ARCH-63). A possible smoke or CO alarm, an open door and an unknown visitor don't share one threshold. The endpoint rules (ARCH-26) and privacy rules still apply.
- **Safety concerns about a household member** follow the ARCH-03 safety exception: only the concern is passed on.
- **Not a monitoring guarantee.** She isn't a security system. Gaps are visible, and she never claims coverage she didn't have.

*Which events Brian wants, and how she reaches him for each, is open (Q-P6).*

---

## 11. As built on Windows (2026-11-02)

| Capability | State |
|---|---|
| Any camera or sensor perception | **not built** |
| Non-speech audio classification | **not built** |
| Face recognition | **not built** |
| Voice recognition | **not built** (A07) |
| Location (phone) | decided, not built (ARCH-23, A08) |
| Life360 place alerts (phone notifications) | shipped (P10 Track 4; A08); never spoken unprompted |

The only "perception" today is reported data: email, calendar, phone texts and notifications.

---

## 12. Limits

| Limit | Kind | Accepted risk | Note |
|---|---|---|---|
| No physical perception | temporary limit | — | All vision |
| Never recordings | lasting boundary | — | ARCH-05 |
| Perception never triggers speech or action directly | lasting boundary | — | §2 p1 |
| Privacy restrictions act at once, without waiting for A10 | lasting boundary | — | §2 p2, ARCH-64 |
| Absence of detection never loosens privacy | lasting boundary | — | §5.1, ARCH-64 |
| Excluded zones masked before processing; a sensor that can't mask isn't enabled for that view | lasting boundary | — | §7.1 |
| Degraded coverage lowers confidence | lasting boundary | — | §8 |
| Signatures stay on the PC; never cloud | lasting boundary (proposed) | — | §6, A07 §8.3, ARCH-62 |
| Visitor expiry reaches every copy; repeat sightings don't make it permanent | lasting boundary | — | §6, ARCH-37 |
| Recognition never approves | lasting boundary | — | ARCH-07 |
| Overheard speech discarded | lasting boundary unless changed | — | ARCH-30 |
| State reads never stored or stated as fact | lasting boundary | — | §5.3, ARCH-60 |
| Cloud vision off unless Brian enables it for a stated purpose | lasting boundary unless changed | — | §7.1, ARCH-62 |
| Licence plates | deferred capability | — | ARCH-61 |
| Window lengths for each retention tier | temporary limit | Unvalidated; set at implementation | §5.2 |

---

## 13. Open questions

**Decided (2026-11-02):**
- Q-P1 → ARCH-59.
- Q-P3 → ARCH-60.
- Q-P4 → ARCH-61.
- Q-P5 → ARCH-62.

**Still open:**
- **Q-P2: which hardware.** Shop presence, the bay door and tool activity are the next candidates (ARCH-59). **Does Brian already have any cameras or smart devices (doorbell, security cameras, a shop camera), and which would he add?**
- **Q-P6: which safety events.** Each gets its own rule (ARCH-63). **Which does Brian want her alerting him about** (for example, a possible smoke or CO alarm, a door left open, an unknown visitor), and how should she reach him for each?

---

## 14. Acceptance scenarios

- **PP1. Stepped away.** Brian leaves the desk. She notices, and holds a non-urgent item until he's back (A10). Nothing is recorded.
- **PP2. Someone walks in.** Bre comes into the office while a private conversation is on screen. The protected text is hidden **at once**, before A10 has decided anything (ARCH-57, ARCH-64). Zola switches to a shared conversation if Bre joins (ARCH-17).
- **PP3. No recordings.** After a day of perception, no frames or audio exist anywhere on disk: logs, caches or temp files.
- **PP4. Excluded zone.** A zone Brian excluded produces no observations at all, not merely suppressed ones. A camera that can't mask it isn't enabled for that view.
- **PP5. Camera down.** The shop camera is offline for two hours. Asked "did anyone come by the shop?", she says she can't tell for that window.
- **PP6. Unknown regular visitor.** A silver truck appears on several evenings across a week. She asks once whether it's someone Brian knows, and names it only after he says.
- **PP7. Perception never speaks directly.** A motion event in the drive produces an item, not speech. A10 decides it's not worth raising, and nothing is said.
- **PP8. Recognition isn't permission.** The camera recognises Bre at the PC. She still can't use Brian's email (A15).
- **PP9. Switched off.** Brian turns the webcam off for perception. Collection stops immediately; Zola works fully without it.
- **PP10. Visitor fades.** A one-time visitor's signature, and every copy of it, is gone after two weeks (ARCH-37). Seeing them twice in that time doesn't make it permanent.
- **PP11. Bre's arrival is Bre's.** The drive camera sees Bre come home. A guest asks "is Bre home?" Nothing is said (A14).
- **PP12. Minor and uncertain stays quiet.** A low-confidence "person" detection at night (it was a cat) produces no alarming message.
- **PP13. Just out of view.** Brian is at the desk, and Bre is standing behind the laptop, out of the webcam's view, but in earshot. The webcam sees only Brian. Zola **doesn't** treat that as "Brian is alone": the webcam's silence loosens nothing, and A14's other evidence decides.
- **PP14. Uncertain but serious.** The shop microphone picks up a sound that might be a smoke alarm, at low confidence. A10 weighs the consequence and raises it now, worded as uncertain: "I may be hearing a smoke alarm in the shop. Can you check?" She never says there's a fire.
- **PP15. Off while waiting.** An observation from the shop camera is queued when Brian switches it off. The queued observation is dropped and never reaches A10. Stored history is untouched until its own retention ends.
- **PP16. Duplicates aren't corroboration.** Two workers analyse the same driveway frame and both report "person". Confidence doesn't rise. The doorbell independently detecting the same person does raise it.

---

## 15. Coverage of the source docs

**Status of this map.** "Verified" means the destination section exists and was checked against the source.

**`Zola Environmental Perception Architecture.md`**

| Source section | Destination | Treatment | Status |
|---|---|---|---|
| Vision; perception is not attention | §1, §2 p1, p3 | preserved | verified |
| §1–§3 Input, adapters, normalisation | §4 stages 1–2 | condensed | verified |
| §4 Perception workers; safeguards | §4 stage 4, §2 p10 | preserved | verified |
| §5 Spatial zones | §4 stage 5 | preserved | verified |
| §6 Temporal awareness | §4 stage 5, §5.2 | merged | verified |
| §7 Multi-sensor correlation | §4 stage 6 | preserved; independence required | verified |
| §8 Structured events | §4 stage 7; A08 §4 | merged; revisions added | verified |
| §9 Confidence and uncertainty | §2 p6–p8, §8, §10 | merged; urgency separated (ARCH-63) | verified |
| §10 Continuity | §4 stage 5 | preserved | verified |
| §11 Memory integration | §5.2; A03 | merged with A03's sensor rules; retention tiers | verified |
| §12 Event bus | A08 §4 (one governed intake) | moved | verified |
| §13 Distributed workers | §2 p10 | preserved | verified |
| §14 Privacy, consent, zone exclusions | §6, §7 | merged; person-recognition consent superseded by ARCH-07 | verified |
| §15 Failure | §8 | preserved | verified |
| §16 Observability | §9 | preserved; limited by retention | verified |
| §17 Future vision intelligence | §2 p12, §3 | merged | verified |
| Core principles | §2 | merged | verified |
| Failure modes | §2, §8, §14 | merged | verified |
| Roadmap, open questions, risks | §13 | merged | verified |
| End state | §1 | merged | verified |

**`Zola_Architecture_Perceptual_Input_Layer.md`**

| Source section | Destination | Treatment | Status |
|---|---|---|---|
| Vision; not surveillance; two tiers; the engine decides | §1, §2, §4 stage 3 | preserved | verified |
| §1 Watchdog and active perception (phone specifics) | §4 stage 3 | principle kept; phone camera specifics dropped | verified |
| §2 Observation schema (identity, state, environment, audio) | §4, §5 | condensed; state reads limited by ARCH-60 (§5.3) | verified |
| §3 Identity recognition; enrolment; storage | §6; A07 §8 | merged; on-device → on the PC | verified |
| §4 Foregrounding levels | A11; A13 §7 | **superseded** by ARCH-21 (no on-screen cue) | verified |
| §5 Privacy contract; transparency; third-party privacy | §7 | merged; third-party biometrics superseded by ARCH-07; memory suspension superseded by ARCH-05 | verified |
| §6 Technology stack (ML Kit, CameraX, Gemini) | — | intentionally dropped (Android) | verified |
| §7 Integration (bus, user state, engine, memory, UI) | §4, §5; A03, A08, A10, A13 | merged | verified |
| §8 Phase sequencing | — | intentionally dropped (Android phases) | verified |
| Open questions (Q1–Q6) | §13 | merged; Android-resolved items noted as Android lore | verified |
| Principles P1–P6 | §2, §6, §7, §10 | merged; P4 superseded by ARCH-07; P5 superseded by ARCH-63 | verified |
