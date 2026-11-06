# A12 — Distributed Presence and Devices

*Draft v0.4, 2026-10-29 (Brian's answers ARCH-24 to ARCH-29; ARCH-28 interim; ChatGPT review). Author: Claude. **Status: approved for the repo by Brian, 2026-11-02 (ARCH-68). States intent; authorises no implementation.***

*v0.5, 2026-11-02 — reconciliation pass after the coverage audit: state-synchronisation coverage row split; scenario D20.*

*Re-audit corrections, 2026-11-02: D15b public audience (R01); "delivery unconfirmed".*

*Coverage-map pass, 2026-11-02: coverage rows closed with exact sections; additions from fresh reads of the source docs (see `audit/arch-docs-swap/ARCH_DOCS_COVERAGE_MAP.md` §5).*

*Phase 10 closeout pass, 2026-11-06: as-built rows and Phase 10 citations rechecked against the Phase 10 lore closeout (tag `p10-closed`) in ARCH-SWAP Phase 2; P10-D18 and P10-D19 cited where they belong.*

**Replaces:**
- `Zola_Architecture_Distributed_Presence_Device_Capabilities.md`: the Windows strawman v0.1 and the **primary source**. Its DP-D proposals are reconciled with P10 below.
- `Zola Distributed Presence Architecture.md` (Android): kept for the vision, the endpoint profiles and its failure modes. Its framing that "the phone is the first anchor" is dropped.
- `Zola_Architecture_Device_Registration_and_Active_Endpoint_Tracking.md` (Android): kept for registration, active endpoint, handoff and output routing. Its Firebase coordination layer is dropped (P10-D07).

**Governing records:**
- Lore: P10-D02, D03, D05–D07, D12, D15–D19; R1–R4. Phase 10 closed 2026-11-06 (tag `p10-closed`).
- `PHASE12_DECISIONS.md`: P12-D01 ("PC first, phone later").
- ARCH-03, ARCH-12, ARCH-13, ARCH-16, ARCH-17, ARCH-18, ARCH-19, ARCH-21, ARCH-22, ARCH-23, ARCH-24, ARCH-25, ARCH-26, ARCH-27, ARCH-28, ARCH-29.

**Android numbers and Android locks are not Windows locks.** For example, the DP-D and Device Registration rules stay proposals unless a P10 or ARCH decision adopts them.

---

## 1. Intent

> "A12 is different than the original Android application. In this instance, it will depend on the companion app and how we present Zola within the app while actual Zola resides on the PC." (Brian, 10/29)

> "All of Zola-Windows should be PC controlled, so we are continuing the same conversation with the same brain." (Brian, ARCH-16)

**Zola lives on the PC.** Her identity, memory, conversations, judgment and authority run there, and nowhere else.

The **companion app** on the phone does two jobs:
1. **It presents her.** It is a window where Brian can see, hear and talk to the same Zola when he's away from the desk.
2. **It extends her senses and reach.** It provides phone capabilities: texts, notifications, location (ARCH-23) and, later, other things. She uses them only as far as Brian has allowed.

The app is never a second Zola. It may process what comes in and show what the PC authorises, but it holds no memory of its own, does no conversational reasoning and has no authority to act. It never speaks for her without the PC.

**What this should feel like:**
- Brian walks out to the shop and keeps talking. Zola answers on the phone, mid-thought, without "where were we?" (ARCH-16).
- He opens the app and she looks and sounds like herself, not like a messaging app with her name on it.
- When the PC can't be reached, the app says so plainly. It never fakes an answer.
- He never has to think about which device she's "on". She is simply there, wherever he can reach her.

> **The intelligence is not in the device. The device is a window into the intelligence.** (Distributed Presence §1, kept)

---

## 2. Principles

1. **One brain, on the PC, defined by authority.** Every endpoint is a client of the PC (ARCH-16; DP-D01). The boundary:
   > **Endpoints may process input and present PC-authorised output. They hold no independent canonical memory, conversational reasoning or action authority.**
   - Allowed on an endpoint: audio capture and playback, rendering the avatar, speech-to-text, permission handling, code masking (P10-D04), queues and display caches.
   - Not allowed: an endpoint deciding what to say, keeping its own memory of people or conversations, scheduling, or authorising an action.
   - Speech-to-text or recognition processing on a device doesn't make it a second brain, as long as the PC makes the final call on who is speaking, what is permitted and what happens.
2. **No answering as Zola without the PC.** That holds even while the PC is down (ARCH-25, §9). An endpoint that generated its own replies, from a cache or an on-device model, would be a second Zola. *Proposed as a lasting boundary; changing it needs an explicit architecture decision.*
3. **Capabilities, not devices.** Zola asks for an outcome ("read the latest texts"), not for "the phone". Contracts name capabilities and carry device ids (P10 R4). That keeps the path open for a second phone, a shop speaker or glasses.
4. **Device access is specific and revocable.** Pairing a phone grants nothing beyond the capabilities Brian has enabled. Switching one off on the phone stops it immediately, and the PC must stop relying on it (DP §6).
5. **The phone decides what Zola may see; the PC decides what matters** (P10-D02). The phone applies visibility rules only: the allowlist and code masking (P10-D04). It never ranks or filters by importance.
6. **One active endpoint per conversation.** One person's conversation has one place where it is heard and spoken at a time. Two devices never answer the same turn (§7).
7. **Each device owns its own microphone and speaker.** The phone never triggers the PC's recording, and the PC never "becomes" the phone's audio (DP §10; P2-D01).
8. **Observation, delivery and memory are separate decisions.** A notification arriving is not a reason to speak it or to remember it (DP §7).
9. **Phone content is untrusted data.** Text in a message or notification can inform her understanding. It can never grant itself trust, permission or action ("content informs; it never grants", Phase 12).
10. **A trusted device is not a trusted person.** Brian's unlocked phone in Bre's hand is not Brian's conversation (ARCH-12; A06 §7).
11. **Honest when degraded.** If an endpoint or a capability is unavailable, she says so. She does not answer from stale data as if it were live (P10-D03).

---

## 3. Who does what

| Part | Owns | Never does |
|---|---|---|
| **PC: Zola (Hermes + plugins)** | Identity, memory, sessions, judgment, scheduling, approvals, action authority | Hand any of these to an endpoint |
| **PC: `zola-phone`** | The only PC link to the phone: accepts the held connection, checks signatures, takes in phone items, relays on-demand reads (P10-D12) | Hold Google tokens, run the model or tools, decide importance |
| **PC: the Windows client** | The PC's own endpoint: window, avatar, PC microphone and speaker | Hold its own conversation state (A06) |
| **Phone: companion app** | Presenting Zola on the phone; phone capabilities; its own microphone, speaker and screen; visibility rules; a bounded queue while the PC is unreachable | Reason, remember, rank, schedule, speak without the PC, or widen its own permissions |
| **Later endpoints** (shop and car: Android devices running the companion, ARCH-29; glasses later) | Exactly the phone's role (§10) | The same limits |

**Today the phone is a sensor, not yet a presence.** Phase 10 builds the phone as a source of texts and notifications only. Zola cannot yet be seen, heard or spoken to through the app (P12-D01: the PC first, the phone as a speaking endpoint later). Sections 4, 7 and 8 describe the vision this doc protects.

---

## 4. How Zola is presented in the companion app (vision)

This is the part Brian's framing puts at the centre. The app is how Zola **appears** away from the PC. It needs to feel like her, not like a remote control for her.

**Brian's verdicts (ARCH-24 to ARCH-28) are recorded in the table. What is still open is listed in §13.**

### 4.1 What the app should carry

| Surface | What it is | Decided | Source |
|---|---|---|---|
| **Talking to her** | Push-to-talk voice on the phone's microphone. Speech-to-text runs on the PC or the phone; either way, the words go to the same PC session (ARCH-16). | **Both voice and typed.** Build order is a build-plan choice. Wake-word listening on the phone is later, separate research (DP §6). | ARCH-24 |
| **Typing to her** | A chat view of the same conversation. | **Yes**, for when speaking isn't appropriate (in a store, a meeting). | ARCH-24 |
| **Her voice** | Her speech is generated on the PC (Deepgram Pandora) and played on the phone. It is the same voice, not a phone voice. | Same voice. | — |
| **Her look** | The obsidian-and-gold identity. Ideally the avatar, otherwise a lightweight presence image while mobile rendering is proven (DP §13). | **The full avatar.** How it is laid out in the app is still open. | ARCH-24; Q-D4 |
| **Her state** | Real states only: listening, thinking, speaking, waiting on Brian, can't reach the PC. | Shown | §4.2 |
| **Her proactive asks** | When she has something for Brian and he's away from the PC (A11). | **A notification; once he opens it, she proceeds. Otherwise she stays silent.** | ARCH-26; §8 |
| **Approvals** | Brian approving an action she has proposed (A15). | **On the phone, spoken only**, in his own turn. The screen may show what is being approved, but a tap or a typed message on the phone never approves. The PC's own approval rules are unchanged (A15). | ARCH-27 |
| **What she can see** | Which phone capabilities are on, whether each is working, and when it last succeeded (DP §13). | Shown in settings (Claude's proposal). | — |

### 4.2 Rules for the presentation

- **One identity.** Same name, voice, personality and palette on every device. No phone-only persona (A02).
- **The app's register can differ; she doesn't.** The Distributed Presence profiles are kept as intent: fuller on the PC, shorter on the phone, very short while driving (§10). Style adapts to context. Identity does not.
- **States are honest.** The app never shows "listening" unless the phone's own microphone is on. A turn running on the PC never makes the phone show "recording" (DP §10).
- **Nothing private shows on the lock screen or in her notification.** It says only something like "Zola needs your attention" (ARCH-26, confirmed).
- **The required Android notification stays plain.** The held connection needs a permanent notification (P10-D07). It shows that the connection is running, not message content.

### 4.3 Away from the PC only (ARCH-24)

> "Only when away from the PC." (Brian)

The app is Zola's presence when Brian is **away from the PC**. At the PC, the PC is her endpoint, and the phone does not compete with it: no phone notifications and no phone playback while he is there (§7.1).

**Confirmed:** "away from the PC" means anywhere away from the office. The shop and other rooms at home count. Brian: *"Away from the PC means anywhere away from the office, so shop and other rooms apply."*

---

## 5. Device identity and trust

**Built in Phase 10 (P10 T1–T3):**
- Pairing between the phone and the PC, with a **device id** carried on every phone item and message (R4).
- A signed, held connection from the phone to `zola-phone` over Brian's private Tailscale network. Nothing is reachable from the public internet (P10-D06, D07).
- Unsigned, unpaired or replayed messages are rejected.

**Required as the app becomes a presence (vision):**
- **Revocation.** Unpairing a phone, or reporting it lost, blocks it immediately on the PC. A replacement pairs fresh. Credentials are never copied from the PC to the phone; model and Google credentials stay on the PC (DP §4).
- **No general remote control.** The app never gets a terminal, arbitrary commands or the raw Hermes interface (DP-D03). It gets defined capabilities and its conversation turns, nothing more.
- **Who is holding the phone.** A paired, unlocked phone shows that it is *Brian's phone*. It does not show that *Brian* is the one using it.
  - Sensitive content and approvals need an interaction the PC can attribute to Brian.
  - When it can't, the speaker is treated as a guest (ARCH-12). Recognition is not permission (ARCH-07).
  - **Decided (ARCH-28):** camera (face) or voice recognition establishes it, once those are built (A07, A09). Brian: *"Camera or voice recognition once implemented."* An unlocked phone alone is not enough for sensitive content or approvals.
  - **Interim, until recognition exists (ARCH-28, option b).** Brian's own paired, unlocked phone counts as Brian for **his own everyday items**: for example, who texted and the gist. Still waiting for recognition:
    - sensitive items (A14)
    - other people's private information (ARCH-13)
    - all approvals (ARCH-27)
  - **Accepted risk of the interim:** someone else holding Brian's unlocked phone could hear his everyday items. This is a **temporary limit** that ends when recognition is built.
  - **Where recognition runs is open.** It could run on the PC from what the phone sends, or partly on the phone. Either way, the PC makes the final decision on who is speaking (§2 p1).
- **Other people's phones.** Family members get Zola on their own devices only through a later decision (A15; Q-W2). Their phones would be separate endpoints with their own pairing, never a shared login on Brian's.

---

## 6. Capabilities and contracts

**Purpose:** let Zola ask for an outcome without depending on how any one phone or app does it.

### 6.1 The contract

Each capability declares:
- its name and version, and the endpoint (device id)
- its kind: **observation** (the phone reports something), **query** (Zola asks), **action** (Zola does something) or **subscription** (tell me when…) (DP-D05)
- its **availability**: available, permission needed, needs the app open, offline, unsupported or degraded (DP §5)

Each result carries:
- what it is and where it came from
- when it was observed and when it was received
- accuracy or confidence where that means something
- whether it is complete and how fresh it is

Errors keep their meaning: permission denied, stale, endpoint offline, unsupported, timed out, or **outcome uncertain**. A timed-out action is never assumed safe to retry (§9).

### 6.2 Capabilities today and in the vision

| Capability | Kind | State | Notes |
|---|---|---|---|
| New texts (SMS, MMS, RCS) | observation | shipped (P10); in conversation through the briefing and "what's pending", metadata only | P10-D01, D01a, D03, D11; codes masked (D04) |
| Text history and search | query | shipped (P10) | Live from the phone; never copied to the PC (P10-D03) |
| Allowlisted notifications (Life360, Visual Voicemail, Instagram) | observation and query | shipped (P10) | Never spoken unprompted in P10 (D15); Messenger dropped (D16) |
| Device health (link, battery, permissions) | observation | shipped (P10): Systems panel companion row | P10-D12 |
| Read a code aloud on request | query | shipped (P10) | R1: direct path, local Zira voice, never stored |
| Brian's location (coordinates, history) | observation | decided, not built | ARCH-23, C15, C16; A08 §6.1 |
| Life360 place alerts about family | observation | shipped (P10) | Last-reported place and its age; never live location (DP §8) |
| Talk to Zola on the phone (voice, typed) | conversation endpoint | **not built** | P12-D01; §4 |
| Her voice and presence on the phone | output endpoint | **not built** | §4 |
| Reply to or send texts | action | deferred | P10-D17 |
| Contacts, media control, camera, app launch, calendar on the phone | various | vision | DP §6; calendar must not create a second Google authority (P9-D06) |

**Subject binding.** A request about a person goes to an authorised source bound to that person. It never quietly substitutes Brian's phone location for Micah's, and a Life360 arrival alert never becomes a live position (DP §5, §8).

---

## 7. Active endpoint and handoff (vision)

### 7.1 One conversation, one place at a time

Brian's conversation is **one Hermes session on the PC** (ARCH-16). Endpoints attach to it. At any moment that conversation has **one active endpoint**: the device where his turns come in and her replies go out.

**How the active endpoint is chosen (proposed, from Device Registration §2 and Distributed Presence §8):**
1. **An explicit choice wins.** "Switch to the phone" or tapping talk on the phone.
2. **Where he last actually interacted.** Real interaction, not a phone merely being connected.
3. **Whether he is at the PC.** At the PC, the PC is the endpoint (ARCH-24). Away from it, the phone is. Signals include PC input activity, the PC camera later (A09) and the phone's location (ARCH-23) (Q-D10).
4. **Context fit.** In the car, the vehicle endpoint, once it exists.
5. **Otherwise no endpoint.** See §7.3.

The decision is the PC's. Devices **yield, they don't compete**. If two devices claim the conversation at once, the PC picks one by these rules and tells the other to stand down.

### 7.2 Handoff

When the active endpoint changes:
**What the PC owns and what the devices must coordinate.** Memory, the conversation, the topic stack, pending questions and held items are all on the PC, so none of them has to be copied between devices (A06). What the devices **do** have to coordinate:
- which device currently has the conversation's input and output
- how far her current reply got in playback
- input that is in flight: a turn being spoken or typed when the switch happens
- what each screen is showing

**Handoff requirements** (mechanics left to the build plan):
- **The PC grants control.** The new device receives the conversation's input and output from the PC. Each grant has a sequence number and an expiry (DP §10, "leases").
- **The old device is told to stop**, and stops playback where it can. She doesn't keep talking to an empty room.
- **If the old device never confirms** (it lost signal mid-reply), the PC does not wait for it. Its grant lapses at expiry, the new device proceeds, and any output the old device later sends is ignored.
- **Playback progress is recorded as far as it is known.** What was confirmed played counts as played. Anything unconfirmed counts as **delivery unconfirmed** (assumed not heard) (A06, played vs acknowledged), so she can offer to finish rather than assume.
- **Late input is sorted, not dropped** (§7.4).
- **An open question stays bound to what it asked.** If she asked "should I reply?" on the PC and Brian answers on the phone, the answer applies to that question, not as a new prompt (DP §10; A11 §6.0).
- **Pending approvals keep their identity.** Approval on another device approves the same action, and only that action (A15).
- **Handoff is invisible when it works.** She only remarks on it when something was lost or a lot of time has passed. For example: "I haven't heard from you in a bit. We were talking about the Camaro…" (Device Registration §3).

**Between people, handoff never carries anything over.** The A06 §7 participant and audience rules apply on every device. If Bre picks up Brian's phone, she does not inherit his conversation (A03 scenario K; ARCH-17). Unverified, she is treated as a guest (ARCH-12). Once she can be verified, she gets her own permitted conversation (ARCH-03), never Brian's.

### 7.3 No active endpoint

Sometimes nobody is reachable. The phone is off and Brian is away from the PC. Then:
- **Nothing is spoken.** She doesn't talk to an empty office.
- **Items keep being held** in the proactive store (A11 §6.0), with their alert windows and expiry.
- **When an endpoint comes back, judgment runs again** (A10 step 8). What was urgent then may not be now; what expired is summarised as history, not announced as news.

### 7.4 Late and held input

A turn can arrive after the conversation has moved, or after the PC has been unreachable. It is sorted, never silently dropped:

| Case | Example | What happens |
|---|---|---|
| **Duplicate** | The phone resends a turn after a dropped connection | Recognised by its id and ignored; the original's outcome stands |
| **Sent before the switch, arriving after** | Brian spoke on the phone, then sat at the PC before it arrived | Still Brian's. It is handled, and the reply goes to the device he is on **now**, checked against who is there (A14) |
| **Already accepted** | The PC had started on it when the device changed | Its outcome is recorded and reported on the current device; it never disappears |
| **Obsolete output** | A reply still being sent to the old device | Not delivered there; it continues on the current device, or is offered again |

**Held typed messages (ARCH-25):**
- Brian can **cancel** a held message before it is sent.
- On reconnect, each one goes through with **the time it was written** (A05). She treats it as a message from then, not now.
- If a held request now looks stale, or the situation has changed, she **checks with Brian** before acting on it.
- A held message is never an approval (ARCH-27). Pending approvals are rechecked on reconnect and expire as usual (A15).

---

## 8. Output routing and delivery

**A10 decides whether to raise something and in what form. A12 decides which endpoint can carry it.** Choosing an endpoint is a capability decision, never hard-wired to "the PC" (P12-D01).

**Routing inputs:**
- the active endpoint (§7)
- what each endpoint can do right now: speak, show, vibrate; available or not
- **channel privacy**: the PC speaker in an empty office, the phone speaker in a store and the lock screen are different audiences (A14 P1, step 3 "channel")
- each person's own proactivity level and preferences (ARCH-19), quiet hours and **attention heat**, which is per person, so moving to the phone doesn't reset her restraint (ARCH-18)
- the endpoint's veto: an endpoint that can't carry something privately is a **temporary block**, and the item is held, not downgraded into something less private (A10 §4, the three kinds of veto)

**Rules carried from earlier decisions:**
- **On the PC: a spoken ask, no on-screen cue** (ARCH-21).
- **On the phone: a notification first (ARCH-26).** Brian: *"I would go with a notification and once opened, she can proceed. Otherwise she stays silent."*
  - The notification takes the place of the spoken "Got a second?". It is a phone rule; ARCH-21 is unchanged on the PC.
  - **Opening it permits her to continue; it does not release content or approve anything.** Once he opens it, she continues in the app (A11), but before saying any content she still checks:
    - **who is using the phone:** ARCH-28, including the interim rule for his everyday items
    - **who can hear:** the A14 channel check.
  - **She speaks** when he opens it (ARCH-26, confirmed). Brian: *"Speaking."* What she says aloud is limited by the two checks above: under the interim rule, his everyday items; sensitive items wait for recognition. If he would rather not hear it aloud, he can switch to typed chat.
  - Sensitive items and approvals still wait for recognition (ARCH-27, ARCH-28).
  - If he doesn't open it, she says nothing. The item stays held for the next natural moment, a summary, or "what's pending" (A11 §6.0).
  - **One notification covers everything waiting**, not one per item. It is **withdrawn** if he deals with the items at the PC first (ARCH-26, confirmed). It carries no content.
  - Choosing whether something deserves a notification at all is A10's decision, with the same bar, heat and quiet hours as anywhere else.
- **Wait for a natural pause unless time-critical** (ARCH-22). The same applies on the phone.
- **Codes are read only on Brian's explicit request** (R1), on whichever endpoint he asks from, over the direct path.
- **Unprompted speech for phone items is watched items only** in Phase 10 (P10-D15). Later phases change this through A10, not through A12.

**One delivery, one record.** Each delivery has one id across every surface it touches: speech on the PC, playback on the phone, a lock-screen line. That prevents the same thing being raised twice on two devices. The record keeps generated, delivered, played and acknowledged as separate states (A11 §6.0; A06). A notification shown is not a notification read.

**Approvals.** An approval shows exactly what will happen (recipient, channel, content), is bound to that one action, expires, and is rechecked by the executor before it runs. A notification's inline reply is still a send and goes through the same approval (DP §11; P10-D17).

---

## 9. When the PC can't be reached

**Proposed lasting boundary: the app never answers as Zola without the PC.**

- **The app says so plainly.** The app separates "the phone is working" from "Zola is reachable". When the PC is down, asleep or off the network, the app shows it can't reach her.
- **Spoken turns are refused; typed turns are held** (ARCH-25). A typed message is marked as not yet sent and goes through when the PC is reachable. A spoken turn answered an hour later would be confusing, so the app says she can't be reached instead.
- **Queues have limits, and gaps are reported.** Texts are not lost: they stay in the phone's own message store, and the cursor resends them (P10-D03). Notifications go into a **bounded** queue, so a long outage can overflow it. When that happens, the gap is recorded and she says so ("I may have missed some notifications between 2 and 4"), rather than implying full coverage (A05 §8).
- **On reconnect:**
  - queued items replay **with their original times** (P10-D08);
  - nothing is told twice (R2);
  - expired items become history, never fresh urgent alerts (DP §12; A05);
  - a turn Brian submitted is processed **at most once**. If its fate is uncertain, she says so rather than guessing.
- **Actions are never retried blindly.** If a send or other action may or may not have happened, she reports that it's uncertain and checks before trying again (DP §12).
- **The PC is always on** (Brian, P10-D06), so this is the exception, not the normal state. It still has to be honest when it happens.

A future always-available core (a hosted brain that doesn't depend on the PC) would be a separate hosting decision, not something the app grows into (DP §17).

---

## 10. Future endpoints (vision)

Each endpoint is the same Zola with a different profile. Profiles are kept from Distributed Presence as intent; none is built or scheduled.

| Endpoint | What it's for | Profile | Defining rule |
|---|---|---|---|
| **PC** | Deep, longer work and conversation | Fuller replies; voice and keyboard | Stronger ambient privacy: the PC can hear calls and meetings |
| **Phone (companion)** | Away from the desk | Shorter replies; voice and typed | Public places: be careful what's spoken aloud |
| **Shop** (an Android device running the companion, ARCH-29) | Hands-free, loud, project-focused | Same as the phone; concise, practical | Reduce friction: faster than reaching for the phone |
| **Car** (an Android device running the companion, ARCH-29) | Driving | Same as the phone; one or two sentences; calm | **Safety is the defining constraint.** The driving limits on unprompted output come from Brian's user state (A08 §5), not from the device, so they apply on any device while he drives |
| **Wearables, glasses** | Ambient presence | Minimal | **The highest bar of any endpoint** for raising anything; never a notification overlay |

**Shop and car devices are Android devices that perform the same as the phone (ARCH-29).** Brian: *"Future shop or car devices should be android devices that perform same as the phone."*
- They run the companion app. They pair, attach to the same PC conversation and follow every rule in this doc, as the phone does.
- **No local authority.** This answers the Distributed Presence §5 question: the shop device handles nothing without the PC (§2, §9).
- Each is its own endpoint with its own device id (P10 R4). The active-endpoint rule (§7) chooses between them and the phone.
- *Claude's note, unconfirmed:* it isn't settled whether a mounted shop or car device takes over phone duties (texts, location) or only presents Zola. Claude assumes it only presents her, and the phone stays the source for texts and location. To settle when one is built.

Wearables and glasses remain vision only.

**Workers amplify, they don't decide** (Distributed Presence §10). Any background helper on any device prepares information for the PC. It never speaks, writes memory or acts (A01 principle; P9-D01).

---

## 11. As built on Windows (2026-10-29)

| Capability | State | Evidence | Decisions |
|---|---|---|---|
| Phone pairing; device id on every item and message; capability-named contract | shipped (P10) | P10 closeout | R4 |
| Held, signed connection over Tailscale; PC-initiated keepalive | shipped (P10); C10 passed under Brian's amendments (11 h 20 min first window for survival, battery and reads; 6-hour rerun for the fixes), not as a graded 12-hour run; W2 Firebase wake untested | P10 closeout | P10-D06, D07, R3; S92 |
| `zola-phone`: the only PC link to the phone; supervised; no Google tokens, no model | shipped (P10) | P10 closeout | P10-D12 |
| Phone texts into the proactive store; in conversation through the briefing and "what's pending" | shipped (P10) | P10 closeout | P10-D03, P10-D11 |
| Phone controls visibility only; codes masked on the phone | shipped (P10) | P10 closeout | P10-D02, D04 |
| Notifications (Track 4), on-demand reads (Track 5), companion health row (Track 6) | shipped (P10) | P10 closeout | P10-D01, D12, D16 |
| Talking to Zola on the phone; her voice, look or proactive asks on the phone | **not built** | — | P12-D01 |
| Active endpoint, handoff, routing across devices | **not built** (PC-only delivery) | — | ARCH-16 |
| Revocation and lost-device flow | **not verified** | — | §5 |

---

## 12. Limits

| Limit | Kind | Accepted risk | Note |
|---|---|---|---|
| Phone is a source only; Zola can't be seen, heard or spoken to there | temporary limit | — | P12-D01 |
| No sensitive content or approvals on the phone until face or voice recognition exists | temporary limit | — | ARCH-28 |
| The app is Zola's presence only away from the PC | lasting boundary unless changed | — | ARCH-24 |
| Phone approvals are spoken only, never a tap or typed (the PC's own rules unchanged) | lasting boundary unless changed | — | ARCH-27 |
| Interim: Brian's unlocked phone counts as Brian for his own everyday items | temporary limit | yes: someone else holding the unlocked phone could hear them | ARCH-28 interim |
| No answer from the app without the PC; spoken turns refused, typed held | lasting boundary | — | ARCH-25, §9 |
| PC-only delivery | temporary limit | — | Vision §5; A01 |
| One phone (Brian's); no family devices | temporary limit | — | §5; Q-W2 |
| Tailscale only; no public entry point | temporary limit (Brian's choice) | — | P10-D06 |
| Permanent Android notification for the held connection | accepted cost | yes | P10-D07 |
| No texting or replying from Zola | temporary limit | — | P10-D17 |
| Life360: last-reported place only, never live location | lasting boundary unless a supported live path is found | — | DP §8, DP-D06 |
| Endpoints hold no canonical memory, conversational reasoning or action authority, and never answer as Zola without the PC | lasting boundary (proposed; ARCH-25 covers the PC-down case) | — | §2 p1–p2, §9 |
| No remote terminal, arbitrary commands or raw Hermes access from an endpoint | lasting boundary | — | DP-D03 |
| Phone decides visibility only, never importance | lasting boundary | — | P10-D02 |
| Each device owns its own audio | lasting boundary | — | DP §10; P2-D01 |
| No Accessibility automation, broad app inspection or always-on phone microphone | temporary limit | — | DP-D12; each needs its own decision |
| Shop, vehicle, wearable endpoints | deferred capability | — | §10 |

---

## 13. Open questions

**Resolved 2026-10-29:**
- **Q-D1** both voice and typed (ARCH-24).
- **Q-D2** only away from the PC (ARCH-24).
- **Q-D3** spoken refused, typed held (ARCH-25).
- **Q-D5** camera or voice recognition, once built (ARCH-28).
- **Q-D6** notification, then she proceeds once opened (ARCH-26).
- **Q-D7** spoken only (ARCH-27).
- **Q-D8** shop and car devices are Android companions with no local authority (ARCH-29).
- **Q-D11** away = anywhere away from the office; notification content-free ("Zola needs your attention"); one notification for everything, withdrawn when handled at the PC; she speaks when it's opened (ARCH-24, ARCH-26).

**Still open:**
- **Q-D4: how the full avatar is presented in the app.** Brian: *"Full avatar, but how it is presented yet I'm not sure."* For example: full screen while talking, a smaller presence during typed chat. Depends on phone rendering performance (DP-Q12). Settled with A13.
**Architecture:**
- **Q-D9: phone voice transport.** Speech-to-text on the phone or the PC, and how her PC-generated voice reaches the phone with trustworthy "finished playing" signals (DP-Q03). A build-time feasibility question.
- **Q-D10: how the PC detects where Brian is** for the active-endpoint rule: phone location, PC input activity, both (shared with A08 Q-W5).

---

## 14. Acceptance scenarios

- **D1. Same brain.** Brian asks something on the PC, walks to the shop and follows up on the phone with "and what about the other one?" She answers in context. There is one Hermes session (ARCH-16).
- **D2. No double answer.** The PC and the phone are both connected and Brian speaks to the phone. Only the phone replies. Nothing plays on the PC.
- **D3. Late turns sorted.**
  - A duplicate resend is ignored and the original outcome stands.
  - A turn Brian spoke on the phone just before sitting at the PC is still handled, and the reply comes on the PC.
  - Output still heading to the phone is not played there.
- **D3b. Old device drops mid-reply.** The phone loses signal while she is speaking. Brian continues at the PC. The PC doesn't wait for the phone, and the unconfirmed part of her reply is treated as **delivery unconfirmed**; she offers to finish it.
- **D4. Question bound across devices.** On the PC she asks "want me to watch for Micah's reply?" Brian says "yes" on the phone. The watch is created; "yes" isn't treated as a new conversation.
- **D5. Playback stops on handoff.** She is mid-sentence on the PC when Brian taps talk on the phone. The PC stops speaking.
- **D6. PC unreachable.** The PC is off the network. The app shows Zola can't be reached and gives no answer of its own. Texts keep queuing; on reconnect they arrive with their original times and none is told twice.
- **D7. Expired, not urgent.** A time-critical item expired while no endpoint was reachable. On reconnect it is mentioned as history, if at all, never as a fresh alert.
- **D8. Phone in Bre's hand.** Bre talks to the app on Brian's phone.
  - **Unverified:** she gets a guest-level conversation.
  - **Verified** (once recognition exists): she gets her own permitted conversation.
  - Either way, none of Brian's conversation, pending items or private information reaches her (ARCH-03, ARCH-12, ARCH-17).
- **D9. Revoked phone.** Brian unpairs the phone. Its next message is rejected, and the Systems panel shows it as unpaired.
- **D10. Capability switched off.** Brian removes Life360 from the allowlist. Life360 items stop at once, and Zola says she can't see Life360 rather than reporting the last known place as current.
- **D11. Subject binding.** "Where's Micah?" Zola answers from Life360's last arrival alert, with its age. She never answers from Brian's own phone location.
- **D12. Heat follows Brian.** She raised three things on the PC this morning. When he picks up the phone, her restraint carries over; she doesn't start fresh (ARCH-18).
- **D13. Private channel.** A private item comes in while the phone is the active endpoint on speaker in a public place. It is held (temporary block) and raised when the channel is private, not read aloud (A14).
- **D15. Notification, then conversation.** Brian is in the shop with the phone. A watched text arrives. He gets a notification (ARCH-26) and opens it.
  - **Before saying any content,** she checks who is using the phone and who can hear (§8).
  - The notification says only something like "Zola needs your attention" and covers everything waiting.
  - It's an everyday item, so under the interim rule (ARCH-28) she tells him about it aloud, in her own words. He replies without repeating anything.
- **D15b. Opened in a store.** Brian opens the notification in a store, on the phone's speaker. Recognising him (ARCH-28) settles who is holding the phone, not who can hear. With an unknown audience she gives only the minimal opener ("Micah texted you") and holds the content. She gives the gist once the channel is private (earbuds in, or Brian confirms it's fine to talk). A sensitive item waits until he's somewhere private or at the PC. A notification tap never establishes privacy.
- **D15c. Handled at the PC first.** The notification is on the phone. Brian walks back into the office and Zola raises the items on the PC. The phone notification is withdrawn.
- **D15d. Shop device.** A mounted Android device in the shop runs the companion. Brian talks to it, and it continues the same PC conversation as the phone would. With the PC unreachable, it refuses spoken turns, exactly like the phone (ARCH-25, ARCH-29).
- **D16. Unopened stays silent.** He never opens the notification. She says nothing on the phone. The item is waiting when he next talks to her, at the PC or on the phone.
- **D17. At the desk, no phone.** Brian is at the PC. A new item is raised on the PC only. No phone notification is sent (ARCH-24).
- **D18. PC down, spoken vs typed.** The PC is unreachable. A push-to-talk turn is refused with "can't reach Zola right now". A typed message is held as unsent and is answered once, after reconnect (ARCH-25).
- **D19. No tap approvals.** Zola proposes an action on the phone. Tapping the screen does not approve it. Only Brian's spoken approval does, and only once he is recognised (ARCH-27, ARCH-28).
- **D14. Uncertain send** (when sending exists). The connection drops mid-send. She says she isn't sure it went and checks before trying again. She never sends twice.

- **D20. Handing off with something private on screen.** Brian is in a private conversation at the PC and moves to the phone. The conversation goes with him (ARCH-16). Bre sits down at the PC: the private text isn't left visible there (ARCH-57), and the PC gives her a conversation of her own.

---

## 15. Coverage of the source docs

**Status of this map.** "Verified" means the destination section exists in this draft and was checked against the source. Rows pointing to other docs that aren't written yet are "planned".

**`Zola_Architecture_Distributed_Presence_Device_Capabilities.md` (primary)**

| Source section | Destination | Treatment | Status |
|---|---|---|---|
| Vision; §1 Purpose and scope | §1, §2 | merged | verified |
| §2 Current foundation | §11; superseded where P10 decided | merged / superseded (P10-D06, D07, D12) | verified |
| §3 Logical architecture; gateway | §3 (`zola-phone` is the gateway) | superseded by P10-D12 | verified |
| §4 Device identity and trust | §5 | merged | verified |
| §5 Capability registry and contracts | §6 | preserved | verified |
| §6 Android access model | §6.2, §12; platform detail kept as build-time reference | merged | verified (notes: per-permission table left to build plans) |
| §7 Notification and event pipeline | §2 p8–9; A08 §4 | merged | verified (A08 part verified) |
| §8 Life360 and family location | §6.2, D11; A08 | merged | verified |
| §9 Conversation continuity and memory | §7; A06 §8; A03 | merged; ARCH-16 adopts §9's "attach" | verified |
| §10 Voice ownership and handoff | §2 p7, §7.2, Q-D9; A07 | merged | verified (A07 §10.2 checked) |
| §11 Proactive delivery and action authority | §8; A15 | merged | verified (A15 §6 checked) |
| §12 Connectivity, offline, retention | §9 | merged; local-network-only superseded by P10-D06 | verified |
| §13 Mobile presence and UX | §4; A13 | merged | verified (A13 §8 checked) |
| §14 DP-D01–D12 | §2, §12; reconciled with P10 | proposals carried as proposals; D11 superseded by P10-D06 | verified |
| §15 DP-Q01–Q12 | Q01 resolved by P10-D12; Q03 → Q-D9; Q04 → T4; Q06 → P10-D17; Q07 → P10-D06; Q08 → P10-D07; Q12 → Q-D4; Q11 → A03/P11 | merged | verified |
| §16 Build sequence | dropped; superseded by the P10/P12 phase plans | intentionally dropped | verified |
| §17 End state | §1, §9, §10 | merged | verified |
| §18 References | build-time reference | intentionally dropped from the vision doc (the repo copy stays with lore history) | verified |

**`Zola Distributed Presence Architecture.md` (Android)**

| Source section | Destination | Treatment | Status |
|---|---|---|---|
| Vision; core philosophy | §1 | merged | verified |
| §1 Core Presence Layer | §2 p1, §3 (the PC) | merged; "server, local or hybrid?" answered: the PC | verified |
| §2 Device Endpoint Layer; authority model | §2, §3 | preserved | verified |
| §3 Phone endpoint ("the right initial anchor") | §3, §10 | superseded: the PC is the anchor (vision §5) | verified |
| §4–§7 PC, shop, vehicle, wearables | §10 | merged | verified |
| §5 Shop authority question | §10 | answered by ARCH-29 (no local authority) | verified |
| §8 Endpoint coordination and transition | §7 | merged | verified |
| §9 State synchronisation | Conversation state: A06 §8 (central on the PC, ARCH-16). Endpoint coordination (which device holds the conversation, leases, progress, late input): §7.1–§7.4 | split; peer synchronisation superseded by ARCH-16 | verified |
| §10 Distributed workers | §10; A01 | merged | verified |
| Core principles | §2 | merged | verified |
| Failure modes | §7, §9, D2–D3 | merged | verified |
| Roadmap, open questions, risks | §13 | merged | verified |
| Heat as shared core state | §8 | adopted per person (ARCH-18) | verified |

**`Zola_Architecture_Device_Registration_and_Active_Endpoint_Tracking.md` (Android)**

| Source section | Destination | Treatment | Status |
|---|---|---|---|
| §1 Registration model | §5, §6.1 | merged; schema left to the build plan | verified |
| §2 Active endpoint tracker; no-active-endpoint | §7.1, §7.3 | merged | verified |
| §3 Handoff protocol; announcement principle | §7.2 | merged; serialisation dropped (state stays on the PC) | verified |
| §4 Output routing | §8 | merged | verified |
| §5 FCM coordination layer | — | superseded by P10-D07 (no Firebase) | verified |
| §6 Stale registration cleanup | §5 (revocation) | merged | verified (notes: staleness timing left to the build plan) |
| §7 Concurrent device writes | §2 p1 (only the PC writes) | superseded: endpoints don't write shared state | verified |
| Core principles ("devices yield, they don't compete"; "routing is centralised") | §2, §7.1 | preserved | verified |
| Heat per device (§7) | §8 | superseded by ARCH-18 (per person) | verified |
| Failure modes | §7, D2–D3 | merged | verified |
