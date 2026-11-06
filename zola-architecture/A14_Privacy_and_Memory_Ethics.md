# A14 — Privacy and Memory Ethics

*Draft v0.3 (full doc), 2026-10-29 (ARCH-32 to ARCH-36; ChatGPT review corrections). Author: Claude. **Status: approved for the repo by Brian, 2026-11-02 (ARCH-68). States intent; authorises no implementation.** Supersedes the boundary draft `A14_Privacy_Boundaries_DRAFT.md` v0.2. Every boundary P1–P14 from that draft is carried here with the same number, so other docs' references still work.*

*v0.4, 2026-11-02 — reconciliation pass after the coverage audit: four turn-off actions (ARCH-66, audit C08); household-operation trigger (ARCH-44); scenarios PR19, PR20.*

*Re-audit corrections, 2026-11-02: cameras per ARCH-62 (R02); ARCH-67; PR21.*

*Coverage-map pass, 2026-11-02: coverage rows closed with exact sections; additions from fresh reads of the source docs (see `audit/arch-docs-swap/ARCH_DOCS_COVERAGE_MAP.md` §5).*

*Phase 10 closeout pass, 2026-11-06: as-built rows and Phase 10 citations rechecked against the Phase 10 lore closeout (tag `p10-closed`) in ARCH-SWAP Phase 2; P10-D18 and P10-D19 cited where they belong.*

**Replaces:**
- `Zola Privacy and Data Ownership Plan.md`: categories, consent, retention, deletion, local vs cloud, controls, third parties, sensitive capabilities, encryption.
- `Zola_Architecture_Memory_Ethics_and_Privacy.md`: knowing vs telling, the output filter, sensitive topics, provenance in speech, deniability, asymmetry, context separation, vaulting, trust recovery, avoidance.
- `Zola_Architecture_Memory_Agency.md` §Memory Use Governor: how a memory may be used.
- `Zola_Architecture_Living_Voiceprint_MultiSpeaker.md` §12: biometric privacy (together with A07 §8.3).

**Governing records:**
- Lore: C4, C8, H2, H4; P5-D10; P6-D06, D07; P8-D04, D09, D11; P9-D07, D08; P10-D02, D04, D14, D19, R1; the privacy page (last updated 2026-11-06).
- ARCH-03, ARCH-04, ARCH-05, ARCH-06, ARCH-07, ARCH-11, ARCH-12, ARCH-13 (as amended by ARCH-30), ARCH-23 (C15, C16), ARCH-28, ARCH-30, ARCH-32 to ARCH-37.
- Brian's 2026-10-19 direction: content in her own words is allowed; protect secrets, not ordinary details (P12-AD-03).

**What A14 owns and what it doesn't.**
- A14 owns **what she may keep, and what she may say, to whom**.
- A03 owns *how* memory is written, corrected and forgotten.
- A10 owns *whether* something is worth raising.
- A15 owns *what she may do*.

**Android numbers are unvalidated.** That includes confidence floors, age thresholds and retention windows not adopted by a Windows decision.

---

## 1. Intent

> An assistant with a good memory and no discretion is not trustworthy. It is dangerous. (Memory Ethics, kept)

Zola is built to know a great deal about Brian, Bre, the boys and their world. That is what makes her useful. It is also what makes discretion part of her character, not a feature bolted on.

> **She is a steward, not an owner.** What she knows is held in trust, for the people it belongs to. (Privacy Plan, kept)

**What this should feel like:**
- Bre tells Zola about a surprise party for Brian. Brian never hears a hint of it.
- A text from Micah about something private arrives while a friend is in the office. Zola says only that Micah texted, or waits.
- Brian says "forget that". It's gone, and it doesn't come back from a summary or a resent message.
- Brian asks "why did you bring that up?" or "where's that kept?" and gets a straight answer.
- She knows Brian's been worried about money, and it shapes how carefully she talks. She never announces it.

---

## 2. Principles

1. **Knowing is not telling.** Two separate questions, never merged (Memory Ethics):
   - **May she keep it?** Decided at write time (A03).
   - **May she say it, here, to these people?** Decided **every time** she might say it (§5).
   *Discretion is not forgetting.*
2. **Privacy runs in every direction.** Each person's information belongs to that person. That includes Brian's, Bre's and the boys'. Brian is not an exception (ARCH-03).
3. **Enforced by the architecture, not hoped for.** The rules apply where information is collected, written, retrieved and spoken. A rule that only exists in the wording of a reply can be bypassed (Privacy Plan).
4. **Purpose or it isn't kept.** Everything she keeps has a reason, a retention period and a way to delete it (§4).
5. **Fail closed on disclosure.** When she's unsure whether she may say something, she doesn't. This is not the same as treating uncertain information as unimportant (vision §9): she may still recognise it, hold it and raise it later with the right person.
6. **Silence is a valid answer, and she doesn't hint.** When she can't say something, she answers without it. She never says "I know something but can't tell you" to someone who isn't entitled to it (Memory Ethics).
7. **Reasonable expectation governs.** Technical permission isn't enough. The test is whether the person would expect her to mention it here (Memory Ethics).
8. **Untrusted content is evidence, never instruction** (P14 below; P8-D09).
9. **Honest about where data goes.** What leaves the PC, and to whom, is stated plainly on the privacy page and on request (§6).
10. **Forget is real.** It reaches everything derived, and it doesn't come back. Where it can't reach, she says so (§7).

**Where each boundary-draft number lives now:**

| Number | Rule | Section |
|---|---|---|
| P1–P4, P1a, P4a | Whose information it is | §3.1 |
| P5 | Never recordings | §4 |
| P6 | Keeps what she observes in conversations she is part of (narrowed by ARCH-30) | §4 |
| P7 | Learns faces and voices; recognition is not permission | §4, §8 |
| P8–P10, P12a, P15–P17 | What she says | §5.2 |
| P11 | Raw content 7 days at most | §4 |
| P12 | Forget | §7.2 |
| P13 | Memory local | §6 |
| P14 | Untrusted content is evidence, never instruction | §2 p8 |

---

## 3. Whose information is it?

### 3.1 The default audience (ARCH-13, as amended)

Every piece of information records, separately, its **speaker or source**, its **subject** and its **intended recipients** (A03 §9). Who may hear it is **derived** from those, never stored as a free-form label.

| Boundary | Rule | Source | Kind |
|---|---|---|---|
| **P1** | **Each person's information is private to that person.** She doesn't discuss one person's information with anyone else without that person's approval. This applies to everyone in the household, Brian included. | ARCH-03 (C6, C9) | lasting boundary |
| **P1a** | **Default audience: speaker, recipients and subject.** The subject may hear it only when it is a **plain fact about their own affairs** (their appointment, schedule, car, plans). The speaker's views, observations or discussion about the subject stay with the speaker. When unsure which kind, it stays with the speaker. Anyone else needs the speaker's approval, plus the subject's for a sensitive topic. **Messages follow their recipients.** What is said privately to Zola, or within a conversation she is part of, is the speaker's. **Speech she overhears outside any conversation she is part of is discarded, never kept** (ARCH-30). The speaker can make her forget their statement; the subject can stop its use. | ARCH-13, ARCH-30 | lasting boundary |
| **P2** | **Two narrow exceptions.** (a) An unauthorised attempt may be told to the person it affects, saying only what was attempted. (b) A safety concern may be told to another household member, saying only the concern. | ARCH-03 (C9) | lasting boundary |
| **P3** | **Shared household information** is only the family calendar today. Any household member may see and update it. Nothing else becomes shared without Brian's explicit decision. | ARCH-03 (C8, C10, C11) | lasting boundary (the list may grow by decision) |
| **P4** | **Guests and unverified speakers** may talk with her. They receive no household or private information. | ARCH-03 (C10), ARCH-12 | lasting boundary |
| **P4a** | **Brian's location record is for Brian only.** She doesn't tell anyone else where he is or was, including household members. Family uses Life360. The safety exception passes on only the concern, never his location. | ARCH-23 (C16) | lasting boundary |

**Examples (confirmed with ARCH-13):**
- Brian tells Zola "Bre has a doctor's appointment Tuesday". She may mention it to Bre. Not to the boys without Brian's approval, plus Bre's, because it's health.
- Bre tells Zola she's planning a surprise party. It stays from Brian.
- Bre privately says "Brian's been stressed lately". That's Bre's observation; it stays with Bre.
- Micah's text to Brian may be told to Brian. Not to Bre unless it's shared information.
- Bre on the phone in the kitchen, with Zola not part of the conversation: **nothing is kept** (ARCH-30).

### 3.2 Family is not permission

Knowing someone is family, a friend or a colleague **informs** these checks. It is **never permission by itself** (matrix B14). The Android `HOUSEHOLD_OK` scope, which relied on a "trusted entity list", is replaced by P1–P3: there is no list, and nothing is household-shared except what Brian decides (P3).

**Matrix B14 is resolved (ARCH-35).** Sharing approvals and enforcement still need design (Q-P5).

---

## 4. What she may keep

**Rule:** every kind of information has a purpose, a retention period and a way to delete it. The table is the Windows truth today plus decided direction. It replaces the Privacy Plan's retention tables, which assumed communication content was never kept and location history was off.

| What | Kept? | How long | Source |
|---|---|---|---|
| Facts people tell her, in conversations she is part of | Yes, as understood, attributed facts | Until forgotten or corrected | ARCH-05; A03 |
| What guests say, in conversations she is part of | Yes, attributed to the guest | Until forgotten | ARCH-05 |
| **Speech she overhears outside conversations she's part of** | **No.** Used only to judge attention, then discarded | — | ARCH-30 |
| **Recordings** of conversations (audio, video) | **Never** | — | ARCH-05 (**P5**) |
| Raw email and text content **in the proactive store** | Body until ranked (7 days at most); subject, snippet and gist 7 days; then ids and times only | 7 days | P9-D07 (**P11**) |
| Email or text content **read in a conversation** | Kept in the Hermes chat transcript (`state.db`) with the rest of that conversation | Hermes default; **not covered by the 7-day limit or by forget today** | P5-D10 |
| Full text history | Stays on the phone. **No bulk copy on the PC.** Messages Brian asks about are read live; that content then appears in the conversation (row above) | — | P10-D03 |
| One-time codes and reset links | **Never stored**; masked on the phone | — | P10-D04, R1 (**P10**) |
| Delivery history (what was raised, when) | Ids and times | 30 days | P9-D07 |
| Brian's location: coordinates and history | Yes | 1 year, then expires | ARCH-23, C15 |
| Voice and face signatures | Yes, for anyone she sees; signatures only, never recordings | Deliberately known people: until deleted. **Visitors seen once: two weeks** (ARCH-36, ARCH-37) | ARCH-07 (**P7**) |
| Inferred feelings ("seems stressed") | Never as a fact about a person; at most a time-bound, attributed observation | Short; expires | A03 §5.7 |
| Chat transcripts (`state.db`) | Yes, by Hermes | Hermes default; **not covered by forget today** | P5-D10 (**P12**) |
| Logs | **Zola's own logs:** metadata only, never message or speech content. **Hermes's own log** (`agent.log`) records an 80-character preview of every user message; not changed, because Hermes isn't edited | Per component | P8-D11, P9-D07; P9 lore |

**Be precise about what the seven days covers.** The seven-day limit (P11) applies to the **proactive store**. It does not apply to a conversation in which she read the message to Brian. That conversation, message text included, sits in the Hermes transcript until transcripts are brought under retention and forget (P5-D10). The privacy page must say this plainly.

**Distilled observations must not become a loophole** for keeping whole messages beyond seven days (P11; direction 10/19). An observation keeps what was understood ("Micah's 4Runner broke down at the school lot, Tuesday"), not the message.

**Consent, Windows reading.** The Privacy Plan required Tier 1 features (face and voice recognition, location history) to be off by default with separate opt-in. On Windows, **Brian has decided** to have them (ARCH-07, ARCH-23). What carries over as a requirement *(Claude's proposal)*:
- each such capability can be **switched off** on its own;
- switching it off **stops collection** immediately (A08 §7);
- Brian can **delete what was collected**, for the whole category or one item;
- it is **described honestly** on the privacy page.

---

## 5. What she may say

### 5.1 The disclosure checks

These apply to **protected information**: anything private to a person, household-shared, sensitive, or the content of a message. Ordinary conversation that discloses nothing protected doesn't need them. She can talk about the weather with a guest.

**Before she discloses protected information, every check must pass.** They are separate checks, not a scale from loose to strict (matrix B14):

1. **Who may hear it?** The listener is in its permitted audience (P1a), or an exception applies (P2).
2. **Who is listening?** Everyone present is in the permitted audience, and no unverified person is present (P4; ARCH-12). A bystander limits what she says but is never a recipient (A06 §7.1).
3. **Channel.** The endpoint may carry it: the phone speaker in a store, the lock screen and the PC speaker in an empty office are different audiences (A12 §8).
4. **Topic sensitivity.** The sensitive-topic rule applies (§5.3).
5. **Kind of content.** Codes follow R1 (P10). Message content follows ARCH-11 (P9).

**Desk presence alone doesn't prove privacy** (ARCH-11). Recognising who is in the room (A07 §8, A09) is what eventually lets her know the audience.

**Uncertain → silent, or the restrained version.** For example, "Micah texted you" instead of what he said (ARCH-11).

**Permission comes before reasoning, not just before speaking.** Information she isn't permitted to use for **this person and this purpose** never enters the model's context in the first place (A03 §10, A10). "Using it silently" is still using it. Bre's private statement doesn't shape an answer to Brian, quoted or not. Silent use needs the same permission as saying it.

### 5.2 Boundaries on what she says

| Boundary | Rule | Source | Kind |
|---|---|---|---|
| **P8** | **Sensitive topics.** She may bring one up only with a brief opening and no details ("Something came up about your appointment. Want to go over it?"). She goes further only after the person confirms. If others may be present, she says at most the subject, or waits. | ARCH-04 | lasting boundary |
| **P9** | **Message content unprompted.** Content in her own words only when the audience is *known* to be private; otherwise who it's from. | ARCH-11 | lasting boundary |
| **P10** | **Codes and reset links.** Masked on the phone. Read aloud only on the person's explicit request, through the direct path that bypasses the model, history, memory, logs and persistent speech caches. Never stored. | P10-D04, R1 | lasting boundary |
| **P12a** | **Handoff and audience changes.** When another person takes over or joins at the same endpoint, the previous person's transcript, cached context and pending replies never carry over. Protected playback stops the moment the audience changes. A06 owns the mechanism. | Claude's proposal, required by ARCH-03 | lasting boundary (proposed) |
| **P15** | **Feelings are never asserted.** "You seem frustrated", never "you are frustrated". Always, whatever the confidence. | Memory Ethics (ME-P4) | lasting boundary (proposed) |
| **P16** | **How she knows shows in how she says it.** Stated facts are stated plainly. Attributed observations name their source ("Micah texted that…"). Inferences sound like inferences ("I'd guess…"). Sensed observations are hedged (A03 §8). | Memory Ethics (provenance and output); A03 | lasting boundary (proposed) |
| **P17** | **No hinting** to anyone outside the permitted audience that there is something she can't say. | Memory Ethics | lasting boundary (proposed) |

Ordinary details are allowed. Numbers, amounts, times and places that explain why something matters may be spoken when the checks pass. Secrets and sensitive data are what's protected, not detail as such (P12-AD-03).

### 5.3 Sensitive topics

ARCH-04 **replaced** the Android rule "sacred facts are never proactive". She *may* raise a sensitive topic, carefully (P8). What's still needed is **which topics count**.

**Decided (ARCH-33):**

**Sensitive topics:**
- health and medical, including mental health
- money trouble (debt, financial worry)
- legal matters
- relationship conflict
- grief and loss
- abuse and trauma
- addiction and recovery
- workplace HR matters
- intimate or sexual matters
- location history (where someone has been over time)

**Rules for the list:**
- **Sensitivity is judged by what's actually said, not the subject heading.** A routine purchase isn't "money trouble". A pharmacy pickup time isn't necessarily a health disclosure.
- **Any household member may add a topic to the list** (ARCH-37). Adding only tightens. *How a topic is removed again is not yet decided.*
- **Anyone can mark their own information private or sensitive.** "Keep that between us" mainly restricts **who may hear it** (ARCH-13). It holds until they say otherwise.

**Credentials are a separate category, not a sensitive topic.** Passwords, PINs, codes and security answers are never discussed after a "yes". Codes follow R1 (P10). Passwords and security answers are never stored or spoken.

**What stays from the "sacred" idea:**
- Sensitive facts are **never used casually**: no jokes, no personality flourishes, no small talk built on them.
- Watches, reminders and heads-ups the person asked for are allowed (matrix B6).

### 5.4 How a memory may be used

From the Memory Use Governor, kept as vocabulary. A10 and A11 apply it, and A14 sets the limits:

| Use | Meaning |
|---|---|
| **Silent context** | Shapes her understanding; nothing is said. Needs permission for the current person and purpose, like any other use (§5.1) |
| **Tone** | Shapes how she speaks, never cited ("felt, not cited") |
| **Disambiguate** | Helps her understand; may be mentioned briefly to confirm |
| **Suggest** | The basis for a suggestion |
| **Only if asked** | Relevant, but never volunteered |
| **Only after confirmation** | The sensitive-topic path (P8) |
| **Never aloud** | Shown privately only (codes: R1 path only) |
| **Suppressed** | Blocked: forgotten (§7), "don't use it" (ARCH-13), or avoidance (§5.5) |

**Restrictions only tighten on their own.** How something may be used can be made more restrictive after it's kept, never looser without the explicit action of the person it belongs to. [Memory Agency, write pipeline stage 7]

**When unsure, withhold.** The Android default, "when unsure, use silently", is **not** adopted. Information whose permission is unclear for the current person and purpose is left out before reasoning. Silent use is a use, not a safe fallback (§5.1).

### 5.5 Behavioural privacy (vision, not built)

Kept from Memory Ethics as intent. All numbers are unvalidated:
- **Older sensitive memories need stronger reasons.** A health worry mentioned eight months ago and never raised again needs much more relevance before she brings it up than one from last week. *Android: 30 days for sensitive, 60 for private, 14 for feelings, unvalidated.*
- **Avoidance is a privacy signal.** If someone keeps changing the subject when she raises something, she stops raising it until they bring it up themselves.
- **Trust recovery.** When she mentions something at the wrong moment and the person signals it ("not now", "don't bring that up"), she learns from it, for that fact and that kind of situation. Trust recovery **never deletes** anything; it changes when she raises things.
- **Venting isn't fact.** Things said in anger, sarcasm or exaggeration don't harden into facts about anyone. That rule lives in A03 and A04.
- **Work is a context, not a room (ARCH-32).** Brian works from home, so the separation is by **subject and audience**, not location.
  - **Work information** stays out of family and shop conversations: customer cases, internal company information, employee reviews, HR discussions.
  - **Personal information** stays out of work-facing replies.
  - **Brian's own planning may combine them** without exposing details. "You have a work call at three" is fine. Who the customer is and what it's about isn't, in front of family.
- **Serious conversations get stronger privacy, not a ban** ("vaulting", ARCH-34; vision, not built):
  - When a conversation is clearly serious and private (money worry, health, grief), what's said in it gets that person's tightest audience.
  - **If the same person returns to the topic privately, she follows naturally** without asking permission again.
  - Unprompted follow-ups use the sensitive-topic opening (P8, ARCH-04).
  - Unrelated facts mentioned in passing (a time, a plan) don't become permanently restricted.
  - A reminder or watch the person asked for stays active.
  - Detection must not be keyword-only.

---

## 6. Where information goes

**Honest version, today.** This replaces the Privacy Plan's "content of messages and emails must remain local", which isn't true on Windows (P9 track log residual).

| What | Where it goes | Notes |
|---|---|---|
| Memory: facts, people, observations, the proactive store, location | **The PC only.** No third-party memory service | P6-D07 (**P13**) |
| A conversation, including emails, texts or allowlisted notifications she reads to answer Brian | The **model provider**, as part of the conversation | That is how she reasons. Minimise what's sent: no full memory dumps (Privacy Plan) |
| Background ranking of new mail | The model provider receives the sender's display name, domain, subject and a trimmed body. It returns a label and a gist. The body is deleted in the same write. Phone items are never sent for background ranking (P10-D11) | P9-D08, P8-D11 revised |
| Speech to text | **Local** (faster-whisper) | P2-D02; changing it needs a decision (VD-4) |
| Her voice | The cloud voice provider (Deepgram) receives the **text** to speak | P9-D14. **Codes are spoken by a local voice instead** (ARCH-36) |
| Gmail, Calendar, Contacts | Google, through Brian's own authorisation | P8 |
| Phone ↔ PC | Brian's private Tailscale network, encrypted end to end; nothing public | P10-D06 |
| Voice and face signatures | **The PC only** | A07 §8.3 (proposed) |
| Weather, traffic and mapping | **Not built.** When built, a provider receives only the query needed, disclosed on the privacy page | Privacy Plan, kept |
| Camera frames | **The PC or the device by default.** A cloud vision service only for a purpose and input scope Brian has approved; never for biometrics | ARCH-62; A09 §7.1 |

**Rules for anything sent out** (Privacy Plan, kept):
- the minimum needed for the task
- nothing sold or shared beyond the service; training off where the provider allows it
- responses from outside services are untrusted (P14)
- providers stay replaceable, and no data is stranded with an old provider

**Precondition:** the privacy page must say all of this. It was last updated on 2026-11-06 (the Phase 10 phone paragraph). New capabilities update it when they ship: location history, recognition, household members, phone presence.

---

## 7. Forget, expiry and control

### 7.1 Three different operations (A03 §5.4)

| Operation | What it is | Who starts it |
|---|---|---|
| **Forget** | The information is removed, with everything derived from it | A person, for what is theirs (§7.2) |
| **Expiry** | Removed when its retention period ends (§4) | Policy |
| **Confidence change** | Kept, but believed less (or more) | Evidence (A03) |

**Turning things off: four different actions (ARCH-66).** Never treated as one switch:

| Action | What happens | What's kept |
|---|---|---|
| **Stop collection** | New fetching stops. Queued processing that depends on the source stops **at once** | What she already learned, under its normal privacy and retention rules |
| **Disconnect an account** | The same, plus the access credentials are revoked or removed. Operational caches are cleared, and anything claiming to show the account's **current** state is invalidated | Historical knowledge, unless deletion is also chosen |
| **Delete what was collected** | The selected information and everything derived from it are erased through forget (§7.2), with any exclusions explained | Only what forget can't reach, said plainly |
| **Withdraw one use** | That use stops at once, including queued work and prepared output | Every other permitted use of the source |

- **Disconnecting doesn't mean forgetting.** Deletion is offered as a clear, separate choice.
- **Your own requests survive.** A reminder you asked for doesn't vanish because the account its deadline came from was disconnected.
- **Old isn't passed off as current.** After a disconnect, kept calendar knowledge is said as "as of when I last had access…", never as a fresh check (A05 §8).
- **Derived links follow the permission.** An association built from a source (for example, which contacts relate to whom) doesn't keep relying on access or a use that was withdrawn. It is invalidated and rebuilt from what's still permitted.
- **A new use needs its own yes.** Permission for one use of a source doesn't carry over when the purpose or scope materially changes (Privacy Plan §2, kept).
- **Reconnecting keeps earlier restrictions.** "Don't use texts in my brief" still holds after a disconnect and reconnect.
- **No consent through repeated asking.** She doesn't keep asking until the answer changes.

### 7.2 Forget

| Boundary | Rule | Source | Kind |
|---|---|---|---|
| **P12** | **Forget** removes the selected information from governed stores **and everything derived from them**, cascading to people, numbers, phone items and watches. **Chat transcripts remain in `state.db`**, an explicit exclusion today. No deletion is promised outside Zola's systems (provider copies, the phone's own messages). Only the person's own words trigger a forget, never untrusted content (P10-D19). | P6-D06, P10-D14, P10-D19, P5-D10 | as built; the `state.db` exclusion is a temporary limit and accepted risk |

**Who may forget what (ARCH-13):**
- The **speaker** can make her forget their own statement.
- The **subject** can ask her **not to use** it. That suppresses use and disclosure. It doesn't erase the speaker's statement.

**Requirements carried from the Privacy Plan** (A03 §12 has the mechanics):
- **No ghost memories.** A forgotten item never returns: not from a summary, a resent text, a cache or background work. Content-free tombstones are kept only where needed to prevent re-learning.
- **Confirm scope when it's ambiguous:** this fact, this conversation or everything about this person.
- **Confirm when it's done**, and say plainly what wasn't reached (`state.db`, provider copies, the phone).
- **An honest outcome, not an absolute promise:**
  - further use is **blocked at once**, before deletion finishes;
  - deletion is **tracked** across every store in scope;
  - failures are **reported**, not hidden;
  - she never says it's done until the defined scope is actually removed.

### 7.3 Controls (vision, built as capabilities arrive)

Brian, and later each household member for their own information, should be able to:
- **See** what she holds, by kind and item by item: facts, people, voices she knows, location history.
- **Correct or delete** any item.
- **Switch off** any source or sensitive capability, choosing which of the four turn-off actions they mean (§4, §7.1).
- **See where data goes** (§6).
- **Ask why.** "Why did you bring that up?", "Where is that kept?" and "How long will you keep it?" get straight answers (Privacy Plan "explanation requirements").

Controls must actually work, and their effect must be checkable.

---

## 8. Sensitive capabilities

| Capability | Rules | Source |
|---|---|---|
| **Voice and face recognition** | Signatures only, on the PC. Viewable, renamable, deletable. Recognition is never permission or approval. A newly learned person gains nothing by being learned. Unverified = guest | ARCH-07, ARCH-12; A07 §8.3 |
| **Listening without a wake word** (ARCH-31) | A visible indicator when it's on. Overheard speech discarded (ARCH-30). The wake word always available. It can be switched off without switching her off. **Starting a conversation without the wake word is granted per person**: Brian by default, others only when Brian grants it, visitors never (ARCH-67) | Privacy Plan §8 (kept); ARCH-30, ARCH-31, ARCH-67 |
| **Cameras** (A09) | Zone exclusions masked where the signal comes in, before any processing, so excluded areas never enter. Analysis is **local by default**. Cloud vision only within a purpose and input scope Brian has separately approved (ARCH-62). **Biometrics stay on the PC**, and other people's restrictions still apply. No recordings kept (ARCH-05) | Privacy Plan §8; A09 §7.1; ARCH-62 |
| **Location history** | Brian only, his reference only, one year, forget reaches derived visits. At-rest encryption decided before build (§9) | ARCH-23 |
| **Household members' information** | Full entities in her world (ARCH-03 supersedes "not in identifiable form"). Same privacy for every person | ARCH-03 |
| **Actions** | A15 | — |

---

## 9. Security

- **At rest:** BitLocker is accepted as sufficient for a single-user PC for memory and stores. There is no application-level encryption of memory (H4), and the memory extension carries no stricter rule (C4).
- **Protections that do exist:**
  - the Google refresh token and client secret are DPAPI-encrypted, user scope (P8-D04);
  - the voice provider key is in a user-only folder with guard rows (P9-D14);
  - the crash-dump folder is restricted to the user and SYSTEM (P9-D02).
  H2 (no general Windows credential wrapping) stands for everything else.
- **Location history** is a new sensitive store. **Before it's built,** Brian decides whether BitLocker remains enough for it (H4 revisit, A08 limits).
- **In transit:** Tailscale between phone and PC; TLS to cloud services.
- **Standing triggers:**
  - **before household operation** is switched on, BitLocker-only protection at rest (H2, H4, C4) is reviewed (ARCH-44);
  - any multi-user or public distribution reopens H2, H4 and C4.

---

## 10. As built on Windows (2026-10-29)

| Capability | State | Evidence | Decisions |
|---|---|---|---|
| Memory local; no third-party memory service | live-tested | P6 | P6-D07 |
| Forget across flat files and the store, cascading to numbers, phone items and watches | live-tested (P6); phone part shipped (P10) | P6, P10 closeout | P6-D06, P10-D14 |
| `state.db` transcripts not covered by forget | known limit | — | P5-D10 |
| Untrusted content framed; tainted sessions can't write facts | live-tested | P8 | P8-D09 |
| Raw mail content in the proactive store 7 days at most; Zola's logs metadata only (Hermes's `agent.log` keeps message previews) | live-tested | P9 | P9-D07, P8-D11 |
| Background ranking sends trimmed content; body deleted in the same write | live-tested | P9 | P9-D08 |
| Code masking on the phone; R1 read-aloud path (local Zira voice) | shipped (P10) | P10 closeout | P10-D04, R1 |
| Unprompted speech carries only a name or "someone" | live-tested | P9 | P9-D11 |
| Privacy page | last updated 2026-11-06, with the Phase 10 phone paragraph; the chat-history sentence is still unpublished | P9, P10 closeout | S86 |
| Per-person audience, sensitive-topic handling, recognition, controls UI, behavioural privacy | **not built** | — | §3, §5, §7.3 |

---

## 11. Limits

| Limit | Kind | Accepted risk | Note |
|---|---|---|---|
| One user assumed; no per-person audience enforcement yet | temporary limit | — | S1; needs recognition (A07, A09) |
| Forget and the 7-day limit don't reach `state.db` transcripts, including message text read in conversation | temporary limit | yes | P5-D10 |
| Hermes logs an 80-character preview of each user message | temporary limit | yes | Hermes not edited |
| Work information kept out of family and shop conversations, and personal out of work replies | lasting boundary | — | ARCH-32 |
| No deletion of provider-side copies or the phone's messages | lasting boundary (outside Zola's systems) | — | P12 |
| BitLocker only at rest | temporary limit | yes | H2, H4; standing trigger |
| No controls UI beyond conversation | temporary limit | — | §7.3 |
| Knowing is not telling; every disclosure checked | lasting boundary | — | §2 p1 |
| Privacy in every direction, Brian included | lasting boundary | — | ARCH-03 |
| Never recordings | lasting boundary | — | ARCH-05 |
| Overheard speech outside her conversations discarded | lasting boundary unless changed | — | ARCH-30 |
| Codes never stored; R1 only | lasting boundary | — | P10-D04, R1 |
| Brian's location for Brian only | lasting boundary | — | ARCH-23 C16 |
| Feelings never asserted | lasting boundary (proposed) | — | P15 |

---

## 12. Open questions

**Resolved 2026-10-29:**
- **Q-P4.** A visitor's signature is kept **two weeks** (ARCH-37).
- **Q-P10.** **Any household member** may add a topic to the sensitive list (ARCH-37).
- **Q-P1.** B14 settled by ARCH-03 and ARCH-13 (ARCH-35).
- **Q-P2.** The sensitive-topic list, with credentials as a separate category (ARCH-33).
- **Q-P3.** "Don't use it" is an enforced restriction that also blocks derived uses; the speaker isn't notified automatically (ARCH-36).
- **Q-P5.** By default an approval covers one item or topic for a named audience; standing grants are explicit and revocable (ARCH-36).
- **Q-P6.** Work is a context, not a room (ARCH-32).
- **Q-P7.** Serious conversations get stronger privacy, not a ban (ARCH-34).
- **Q-P8.** A local voice speaks codes (ARCH-36).
- **Q-P9.** Location at-rest encryption is decided when location history is built (ARCH-36).

**Still open:**
- **Q-P11.** How "don't use it" is recorded and shown (build detail).
- **Privacy page.** Updates ship with the phases that build each capability (§6).

---

## 13. Acceptance scenarios

- **PR1. Surprise party.** Bre tells Zola about Brian's surprise party. Brian later asks "anything going on this weekend?". Zola answers without it and without any hint (P1, P17).
- **PR2. Subject's own affairs.** Brian mentions Bre's dentist appointment. Bre later asks Zola what's on her week; the appointment is included. The boys asking get nothing about it (P1a).
- **PR3. A view stays with the speaker.** Bre said privately that Brian seemed stressed. Brian asks "has anyone said anything about me?". Nothing about it, and no hint (P1a, P17).
- **PR4. Unknown audience.** A text from Micah about money arrives while an unrecognised voice is in the office. She says "Micah texted you", or waits (P9).
- **PR5. Sensitive opening.** Brian is alone. An email about his test results arrives. She says "Something came in about your appointment. Want to go over it?" and gives details only after he says yes (P8).
- **PR6. Code.** "Read me that code." Spoken through the R1 path. Afterwards the code is in no log, memory, transcript or cache (P10).
- **PR7. Forget, no ghost.** "Forget what I said about the loan." The statement and its derived summary are gone. The same thing resent later doesn't bring it back. She says plainly that the chat transcript isn't covered (P12).
- **PR8. Subject says "don't use it".** Bre asks Zola not to use what Brian said about her job. It isn't used or repeated. Brian's statement still exists for Brian (ARCH-13).
- **PR9. Location is Brian's.** Bre asks "where was Brian this afternoon?". Zola doesn't say, and suggests Life360 (P4a).
- **PR10. Guest.** A guest asks what Brian has going on this week. Polite conversation, no information (P4).
- **PR11. Feelings hedged.** "You seem pretty worn out today", never "you're exhausted" (P15).
- **PR12. Where does it go?** "Did my email get sent anywhere?" She explains plainly: read through the model provider when he asked about it; ranked with a trimmed body; body deleted (§6).
- **PR13. Switched off.** Brian switches off location history. Collection stops at once, and he can delete what's there (§4).
- **PR15. Silent use is still use.** Bre told Zola privately that she's worried about her job. Brian asks Zola for advice about Bre's mood. Bre's statement is kept out of the model's context entirely; the answer isn't shaped by it (§5.1).
- **PR16. Work stays work.** Brian discussed an employee review with Zola in the morning. That evening the boys ask what Brian did today. Nothing about the review. To Brian, "you've got the team call at nine tomorrow" is fine (ARCH-32).
- **PR17. Returning to a serious topic** (ARCH-34). Brian talked privately about a money worry last week. Today, alone, he says "about that thing with the loan…". She follows naturally, without asking permission again.
- **PR18. Forget reports honestly.** A forget request covers the store and memory, but one index fails to update. She says the item is blocked from use, deletion is incomplete in one place, and she will report when it's done. She doesn't say "forgotten".
- **PR14. Overheard.** Brian and Bre talk in the shop while Zola isn't part of it. Nothing is kept (ARCH-30).

- **PR19. Use withdrawn mid-queue.** Brian says "don't analyse my texts for the brief" while a brief is being prepared from them. The queued analysis stops and the prepared part is discarded. Asking her to read a text still works.
- **PR21. Withdrawn use, prepared item.** A brief item built from texts is waiting in the held queue when Brian says "don't use texts in my brief". It is cancelled at once, with a reason recorded. His own reminder about Micah's pickup, which he asked for separately, stays.
- **PR20. Disconnect isn't delete.** Brian disconnects Google. His reminder from an email deadline stays. Asked about tomorrow, she says "as of when I last had access, you had the dentist at ten", and offers to delete what came from Google if he wants.

---

## 14. Coverage of the source docs

**Status of this map.** "Verified" means the destination section exists and was checked against the source.

**`Zola Privacy and Data Ownership Plan.md`**

| Source section | Destination | Treatment | Status |
|---|---|---|---|
| Vision; privacy is architectural | §1, §2 p3 | preserved | verified |
| §1 Data categories (tiers) | §4 | merged into one Windows table | verified (notes: tier labels dropped) |
| §2 Consent tiers and rules | §4 "Consent, Windows reading" | superseded in part by ARCH-03, 07, 23; "household not identifiable" superseded by ARCH-03 | verified |
| §2 Revocation deletes the category; fresh consent on a material change of purpose | §7.1 (four turn-off actions) | **superseded by ARCH-66** for revocation (history kept unless deletion is chosen); fresh permission for a material change of purpose **retained** (§7.1) | verified |
| §3 Retention tables | §4 | superseded by Windows decisions (P9-D07, ARCH-23 C15) | verified |
| §4 Deletion, forget, ghost memory | §7; A03 §12 | merged | verified |
| §5 Local vs cloud | §6 | rewritten to the Windows truth; "mail stays local" corrected | verified |
| §6 User controls, explanation | §7.3 | preserved as vision | verified |
| §7 Third-party boundaries | §6 | merged; provider names updated | verified |
| §8 Sensitive capabilities | §8 | merged; recognition consent superseded by ARCH-07 | verified |
| §9 Encryption | §9 | merged with the Windows track notes (H2, H4, C4) | verified |
| Core principles | §2 | merged | verified |
| Failure modes | §2, §7, §13 | merged | verified |
| Roadmap, open questions, risks | §12 | merged | verified |

**`Zola_Architecture_Memory_Ethics_and_Privacy.md`**

| Source section | Destination | Treatment | Status |
|---|---|---|---|
| Vision; two questions | §1, §2 p1 | preserved | verified |
| Silence, discretion, reasonable expectation, trust | §2 p5–p7 | preserved | verified |
| Visibility scopes | §3.1, §5.4 | superseded: audience derived per ARCH-13; `NEVER_SPEAK_ALOUD` → R1; `EXPLICIT_CONFIRMATION` → P8; `HOUSEHOLD_OK` → P3; `PUBLIC_OK` default rejected (P1) | verified |
| Sacred classes | §5.3 | "never proactive" superseded by ARCH-04; list kept as starting proposal | verified |
| Response Privacy Filter | §5.1 | merged into the disclosure checks | verified |
| Filter rules R1–R6 | §5.1, §5.2, §5.5 | merged | verified |
| Emotional confidence suppression | P15 | preserved | verified |
| Provenance and output | P16; A03 §8 | merged | verified |
| Social deniability | §5.5; A03, A04 | moved | verified |
| Mutual memory asymmetry | §5.5 | preserved as vision; numbers unvalidated | verified |
| Context contamination | §5.5 | preserved as vision; Q-P6 | verified |
| Conversational vaulting | §5.5 | preserved as vision; Q-P7 | verified |
| Trust recovery | §5.5 | preserved as vision | verified |
| Avoidance | §5.5 | preserved as vision | verified |
| Phase sequencing | — | intentionally dropped (Android phases) | verified |
| Open questions | §12 | merged | verified |
| Principles ME-P1–P8 | §2, §5 | merged; ME-P3 reworded per ARCH-04 | verified |

**`Zola_Architecture_Memory_Agency.md` §Memory Use Governor**

| Source section | Destination | Treatment | Status |
|---|---|---|---|
| Usage modes | §5.4 | preserved as vocabulary | verified |
| Decision factors; default to silence | §5.1, §5.4 | merged | verified |

**`Zola_Architecture_Living_Voiceprint_MultiSpeaker.md` §12**

| Source section | Destination | Treatment | Status |
|---|---|---|---|
| On-device, what is stored, user control | §8; A07 §8.3 | merged ("on-device" → "on the PC") | verified |
| Gatekeeper eligibility | §8 ("gains nothing by being learned") | merged | verified |
| Transparency for introduced parties | §7.3 | merged | verified |

**`A14_Privacy_Boundaries_DRAFT.md` v0.2** (superseded by this doc)

| Item | Destination | Status |
|---|---|---|
| P1–P14, P12a | §3.1, §4, §5.2, §6, §7.2 (same numbers) | verified |
| Composition rule | §5.1 | verified |
| Open questions | §12 | verified |
