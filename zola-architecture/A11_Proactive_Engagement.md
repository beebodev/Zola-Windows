# A11 — Proactive Engagement

*Draft v0.2, 2026-10-29 (ARCH-21, ARCH-22; ChatGPT review). Author: Claude. **Status: approved for the repo by Brian, 2026-11-02 (ARCH-68). States intent; authorises no implementation.***

*v0.3, 2026-11-02 — reconciliation pass after the coverage audit: §5.1 daily brief (ARCH-65, audit C01); scenario E14.*

*Re-audit corrections, 2026-11-02: held-queue removal reasons (R03); confirmed playback wording.*

*Coverage-map pass, 2026-11-02: coverage rows closed with exact sections; additions from fresh reads of the source docs (see `audit/arch-docs-swap/ARCH_DOCS_COVERAGE_MAP.md` §5).*

*Phase 10 closeout pass, 2026-11-06: as-built rows and Phase 10 citations rechecked against the Phase 10 lore closeout (tag `p10-closed`) in ARCH-SWAP Phase 2; P10-D18 and P10-D19 cited where they belong.*

**Replaces**
- `Zola_Architecture_Cognitive_Engagement.md`
- Memory Agency, three parts:
  - open loops (as watches)
  - cognitive tension (as a signal)
  - the contextual resurfacing engine
- Autonomous Behavior: deferred summaries and emotional regulation
- Master Plan pillar 16, deferred cognition
- Perceptual Input: foregrounding levels
- Cognitive Engine: the initiative queue

**Governing records**
- **Lore:**
  - P9-D06: the proactive store
  - P9-D09: open loops and watches
  - P9-D10: surfacing
  - P9-D11: unprompted speech and delivery evidence
  - P10-D13–D15
  - the SOUL watch and offer lines
- **Phase 12 decisions:** P12-D01, P12-D02, P12-D04, P12-AD-03 and the "continuity of what was delivered" requirement
- **Architecture-doc decisions:** ARCH-04, ARCH-09, ARCH-11, ARCH-13, ARCH-15 (C12, C13), ARCH-16 to ARCH-19
- **Related drafts:** A06 §6–7, A10

**Phase status.** This is the vision doc for **Phase 12**. Nothing here is a locked Phase 12 decision. Android numbers (session ceilings, weekly limits, urgency tiers) are **unvalidated**.

---

## 1. Intent

> An assistant that only answers questions is reactive. It waits. An entity that uses what it knows to actively engage is different. It participates. (Cognitive Engagement, kept)

A10 decides **whether** something should reach someone, and when. A11 owns **how she engages**. That has two halves:
- **Engagement inside a conversation.** She lets what she knows shape her answers, notices connections, asks the question she genuinely wants answered, and brings back something relevant from last week.
- **Engagement she starts.** Something happens in Brian's world. She gets his attention appropriately, tells him in her own words, and the conversation carries on naturally from there.

The Android docs covered the first half well and the second only thinly. On Windows the second half already partly exists: Phase 9 watches and unprompted speech.

**What this should feel like**
- *"Hey, got a second?"* She waits for him to look up. Then: *"Micah texted. His car died at the school and he's asking if you can call."* Brian: "Did he say what happened?" She answers from the text, with no wake word and no restating.
- *"A few things came in while you were in the shop. The parts order shipped, Bre's practice moved to Thursday on the family calendar, and the registration's due Friday. Want me to remind you tomorrow?"*
- Mid-conversation about the engine: *"That might tie back to the heat-soak thing from last week. Did that ever pan out?"* It comes from a genuine gap, not a script.
- Not: *"Reminder: you mentioned an engine noise on Tuesday. Would you like to update the status of this item?"*

---

## 2. Principles

1. **A10 decides whether; A11 decides how.**
   - A11 never makes its own decision to raise something. Every unprompted output comes from the A10 decision point (ARCH-09).
   - This includes curiosity questions and resurfaced memories.
   - The Engagement Governor's checks (frequency, timing, social fit, sensitivity) are **steps feeding that one decision**, not a second gate with its own final say.
2. **Check again at the moment of delivery.** An A10 approval is not a licence. Immediately before anything plays or shows, A11 re-checks the current state (A10 §5.2 step 8):
   - who is present: audience and participants
   - the endpoint
   - preferences and proactivity level
   - the item's status

   Anything changed sends the item back to A10 or holds it.
3. **Silent engagement is the default** (CE-P4). Most of what she knows shapes her answers invisibly. She knows; she doesn't always say.
4. **Motivated, not scripted** (CE-P1). A curiosity question comes from a real gap meeting the present moment. A scripted follow-up is noise.
5. **Her own words, with context; protect secrets, not ordinary details** (P12-AD-03, P12-D02).
   - Numbers, amounts, times and places are fine.
   - Codes follow R1.
   - Sensitive topics get the brief opening and wait for a yes (ARCH-04).
   - Content goes only to a known-private audience (ARCH-11).
6. **Grounded, never embellished** (A01 principle 4). Phrasing is hers. The facts come from the authorised content. She never adds, changes meaning or fills gaps.
   - **Never manipulative** (Autonomous Behavior, kept). She never creates false urgency, plays on emotions to get attention, invents memories, pushes engagement for its own sake or works around what the person has said they want.
7. **Combining never loosens restrictions** (A10 principle 8). A summary or a connected mention keeps every source's disclosure restrictions.
8. **Record what was delivered, as Zola's message** (A06 §6). These are recorded separately:
   - the authorised content;
   - **what played and where playback stopped**: generated, queued, started, interrupted at a point, completed or failed;
   - whether delivery is uncertain;
   - **acknowledgement**, if any.

   Playback is never proof that someone heard or understood. It is never a synthetic user turn, and unplayed text is never treated as heard.
11. **An answer belongs to the question that was asked.** "Got a second?" followed by "Yeah" permits *delivering that update*, nothing more. It never approves a send, closes a watch, confirms a sensitive detail or settles any other pending item.

    Each pending question Zola asks records:
    - which item it is about;
    - **who it was asked of**;
    - **how long an answer stays valid**.

    Only that person's answer, inside that window, counts. Turning toward the PC or looking up can indicate *attention*. It is never an explicit confirmation of sensitive details or of an action (A15; P12-D04 approval binding).
9. **Avoidance ends inquiry** (CE-P5). If someone dodges or dismisses a curiosity question, she doesn't rephrase it and try again, and she eases off that domain.
10. **She never stops watching on her own** (P9-D09 SOUL line). She closes a watch only on the person's confirmation, or on its deterministic close condition.

---

## 3. Getting someone's attention

A10 decides an item should reach Brian now and in what form. A11 delivers it so that it feels like **someone at the office door, not a pager**. **She asks aloud. There is no on-screen "I have something" cue (ARCH-21).**

| Level | What it sounds like | When |
|---|---|---|
| **Spoken ask** | A short opener: "Hey, got a second?" or "Brian, quick one." Then she waits briefly for an answer. | Ordinary items worth raising now |
| **Straight in** | She delivers directly and briefly | Time-critical items, or when he's clearly already listening |
| **Hard foreground** | She takes the foreground deliberately | Rare: safety, or the conservative override (A10 §4.4) |

Items that wouldn't justify a spoken ask are **held**: for the next natural moment, a summary, or "what's pending". They are not signalled on screen.

**Rules**
- **The ask respects the answer.**
  - "Not now" holds the item and adds heat (A10 §7).
  - "Go ahead" or "yeah" delivers *that update only* (principle 11).
  - No answer: she tries again later at a better moment. She doesn't repeat the ask in the meantime.
- **She speaks naturally, then listens.** After she speaks, follow-up listening opens so Brian can just answer (A06 §6). It is gated by the speech work: no self-echo, no clipped openings (A07; SPEECH_DECISIONS). Today a proactive line opens no follow-up listen, which is a temporary limit.
- **Varied phrasing.** Brian, P9: *"I'm not sure if I like the same wording every time."* She doesn't use one fixed sentence.
- **Endpoint by capability** (A12, P12-D01). PC first; the phone as a speaking endpoint later. The choice is driven by capability and A10's form decision, never hard-wired to "the PC". Because there is one conversation across devices (ARCH-16), what she says on the phone is part of the same conversation.

---

## 4. Saying it

- **Her own words, grounded in what she was cleared to say.**
  - The opener carries a short summary in context: who, what, and why it matters to Brian.
  - Full detail comes when he asks (P12-D02).
  - The sender's name comes from Contacts or memory, never from the message itself (P12-D02, P9-D11 name rule).
- **Failure behaviour.** If the generated announcement fails a check, A11 does not automatically fall back to name-only. Example checks: grounding, a protected category, an unknown audience. The fallback is chosen per case: a minimal announcement, a permitted brief form, or holding it (P12-D02 requirement).
- **Per audience** (ARCH-11, A06 §7.1). The audience decides how much she says:
  - Known-private audience: content in her own words.
  - Unknown audience: restrained ("Micah texted you").
  - A bystander present: no protected content.
- **Tone fits the moment.** This is emotional regulation, kept from the Android docs: *"Emotional regulation is not about simulating emotion. It is about behaving appropriately for the moment."* She is calm for a breakdown, brief when Brian is busy and warm when it's personal. Her style comes from A02.

---

## 5. "While you were away": summaries

Several items that wouldn't each justify an interruption can be **held and told together** at a natural moment (A10 disposition "hold for summary"; Master Plan pillar 16; Attention Engine §8). Today this exists as P9 surfacing after a gap (P9-D10).

> *"A few things came in while you were working. UPS dropped something off, the parts order shipped, and you've got the 4 o'clock call coming up."*

**Rules**
- **Group by meaning, order by importance.** Related items are told together.
- **Each item keeps its restrictions.** A summary told to Brian includes only what Brian may hear. With others present, it covers only what everyone present may hear (principle 7).
- **The alert window and the issue are separate** (A10 §4.3). An item whose alert window passed drops out of the summary *as an alert*. Ongoing issues stay, and an overdue commitment is told as overdue.
- **What she held is not hidden, within limits.** "What's pending?" or "anything new?" lists the *eligible* held items (P9-D10 `whats_pending`):
  - only what the person asking may hear, given privacy and audience;
  - fresh ones first;
  - kept to a sensible length.

  It never dumps everything. It never implies that an item left out doesn't exist ("…and a few more; want the rest?").
- **Delivered means delivered.** A summary interrupted halfway records the confirmed playback progress, with acknowledgement kept separately (principle 8).
- **No synthetic filler.** An empty summary is said in a sentence, or not at all.

### 5.1 The daily brief (deferred, ARCH-65)

A **different feature** from catching up on held items. The summary above tells you what came in while you were away. The brief is a **planned overview of the day**, assembled even when nothing is waiting:

> *"Morning. You've got the dentist at ten and the parts supplier call at two. Rain's coming in this afternoon, so if you're moving the Camaro, do it before lunch. Micah's flight lands at six."*

**What it draws on** (A08 supplies the sources): calendar, weather, travel time, communications, open commitments and watches, and relevant memory.

**How it's delivered**
- **On request:** "Give me today's brief" works at any time. It doesn't depend on there being anything held.
- **Optional morning overview:** off unless the person switches it on. If on, it's given in the first suitable moment of their day, not as an interruption at a fixed time.
- **Once means once.** A morning brief already given isn't repeated because of a restart or a second device. Asking again gives a fresh one.

**Rules**
- **Each person chooses for themselves:** whether the morning overview is on, and which sources their brief uses. Choosing sources is the same mechanism as withdrawing one use of a source (ARCH-66): leaving texts out of the brief doesn't turn texts off elsewhere, and doesn't widen access to anything.
- **Fresh, or labelled.** Each part is current when given, or said with its age ("as of last night…"). Retained information never passes for a fresh check (ARCH-66; A05 §8).
- **The normal checks still apply.** A10 decides whether a morning brief is given now; A14 decides what may be said given who can hear.
- **No filler.** A quiet day gets a short brief. Nothing is invented to fill it.
- **It may offer a next step** ("Micah's waiting on an answer. Want to reply?"). Acting on it goes through the normal draft-and-approve path (A15). The brief adds no new way to send anything.
- *Android specifics not carried:* the morning window, the four-hour expiry, the prompt packaging and the class names. *Unvalidated.*
- **Source evidence limit.** The Android originals refer to `Zola_Daily_Brief_Architecture.md`, which isn't in the Windows checkout. This section was rebuilt from Agent Map (Agent 15), Communication Intelligence and SMS Intelligence only.

---

## 6. Watches and commitments

This is the operational side of "remembered situations vs watches" (A03 §11; matrix §3.4).

### 6.0 The held-items queue (contract)

Everything she is holding for someone lives in **one durable queue** in the proactive store (P9-D06). That includes:
- deferred updates;
- items waiting for a summary;
- interrupted announcements;
- unanswered spoken asks;
- curiosity questions waiting for the right moment;
- watch matches.

Each queue entry has these properties:
- **Survives across sessions and restarts.** It is never silently discarded (Cognitive Engine, kept).
- **Belongs to one person** (ARCH-19). It is never shown to anyone else.
- **Has a stable id** and a clear lifecycle state.
- **Is deduplicated** across summaries, surfacing, spoken delivery and devices (ARCH-16). One item is told once, however many paths could carry it.
- **Keeps its source restrictions** (A10 principle 8).
- **Leaves the queue only for a recorded reason.** Never by being quietly dropped. The reasons:
  - delivered, dismissed or completed;
  - superseded by a newer item about the same thing;
  - past its maximum age, or its approved retention expiry. An alert's window closing isn't the issue resolving (A10 §4.3);
  - **policy removal:** forget (A03 §12), a withdrawn use, or its source being switched off or disconnected (ARCH-66). The removal records a privacy-safe reason, never the forgotten content.
- **Removing a delivery item never closes anything else.** A reminder or watch the person asked for, and knowledge that's still permitted, are separate and survive (ARCH-66; §6.3).

Several states stay separate and must never be merged:

| State | Meaning |
|---|---|
| Generated | Content authorised and prepared |
| Delivered | Played or shown, with how much |
| Acknowledged | The person responded to it |
| Dismissed | The person said not to bother |
| Completed | For commitments and watches: done, on confirmation |
| Expired alert | The delivery window passed; any ongoing issue remains (A10 §4.3) |

The detailed mechanics belong to the Phase 12 build plan.

### 6.1 What a watch is

A **watch** is a standing instruction to keep an eye out for something and tell the person. It lives in the proactive store (P9-D06), separate from memory, and is linked to any remembered situation by a stable id.

| Kind | Created from | Example |
|---|---|---|
| **Reply or person watch** | The person's own words, or an offer they accept (P9-D09; P10-D13). Never from what a message says (P10-D19) | "Tell me when Micah texts." "Let me know when the ECU email comes." |
| **Commitment watch** | A commitment the person states with a time (ARCH-15, C12) | "I need to renew the registration by the 15th." |
| **Offered watch** | An offer the person accepts about a deadline she observed (C13) | A DMV email says it expires the 15th. "Want me to keep an eye on that?" "Yes." |

**Never a watch**
- A vague intention, which is only remembered (C12).
- An ordinary unresolved topic.
- Anything created by untrusted content on its own (C13).

### 6.2 What a watch does

- **Watching.** A matching item becomes eligible for A10 (today `loop_matched`). Matching uses source timestamps and never matches the message the watch was created from (P9-D09 fix; A05).
- **Check-ins.** For commitments, she checks in before the due date at eligible moments. She offers help: drafting, looking something up, a reminder. Example: *"The registration's due Friday. Want me to pull up the renewal page?"*
- **Verifying completion.** Evidence can suggest a commitment is done, for example a confirmation email. When it does, she **asks**: *"Looks like the registration went through. Want me to close that out?"* She closes it only on a yes (ARCH-15).
- **Asking whether to keep watching.** When something she was watching for comes in, she tells the person and asks whether to keep watching (P9-D09 SOUL line).
- **Lapses.** A watch that lapses (for example, past its due date with no completion) is told **once**, then becomes *overdue* (A05 §7). It is never silently dropped.
- **Per person.** A watch belongs to the person who set it (P9 "a loop belongs to Brian, not to a session"; ARCH-03). Bre's watches are hers.

### 6.3 Who closes what

| Event | Watch (A11) | Remembered situation (A03) |
|---|---|---|
| The person confirms done | Closed by the person's confirmation | Updated to resolved, with the confirmation as evidence |
| Evidence suggests done | Stays open; she asks for confirmation | **Evidence recorded immediately, attributed:** "A confirmation email reports the renewal succeeded; Brian hasn't confirmed." She can tell him so. The watch is not closed. |
| The person says stop watching | Closed | Unchanged: the situation may still be unresolved |
| Due date passes | Told once; marked overdue | Condition stays open (A05) |
| Forget (the subject or the watch) | Removed (P10-D14) | Removed per A03 §12 scope |

Neither owner edits the other's status directly. A change is passed across by id, and the receiving owner applies it under its own rules.

---

## 7. Engagement inside a conversation

### 7.0 Answering vs. raising something new

These are different, and only the second counts against proactive restraint.

| Part of answering the person's request | Raising something new |
|---|---|
| Using what she knows to answer well | Introducing a separate topic |
| Mentioning a directly relevant connection inside the answer | An unsolicited curiosity question |
| Asking a question the task needs ("is it a cold start or warm?") | Resurfacing something unrelated to the request |

**Answering is never suppressed** for proactive reasons: heat, proactivity level or curiosity limits (A10 principle 7). Privacy still applies to everything. Only *raising something new* goes through the A10 decision point.

### 7.1 Silent enrichment (most of the time)

What she knows shapes her answers without being cited:
- She doesn't ask what she already knows.
- She speaks carefully around what's sensitive.
- She tailors her advice to the specific engine, build or person.

This is the most valuable and the most common form of engagement (Cognitive Engagement, kept).

### 7.2 Resurfacing connections

- **She notices and mentions what connects.** When something being discussed connects to something she knows, she may mention it in passing: *"That might tie back to the shifter sitting too far back, from last week."*
- **The surfacing route.** Candidates come from noticing connections between the current context and memory:
  - direct relevance
  - a causal link
  - a pattern the moment fits or breaks

  They go to A10 like everything else.
- **What she may draw on.** Only knowledge the conversation's participants may receive (A03 §9, A06 §7).

### 7.3 Curiosity

Three kinds, from rarest restraint to most:

| Kind | What it is | Example | *Android limit (unvalidated)* |
|---|---|---|---|
| **Curiosity question** | A genuine gap or an unresolved situation meets the present moment | "Last time you weren't sure if the noise was load-dependent. Did you figure that out?" | ~1 per conversation |
| **Checking a pattern** | A tentative hypothesis, asked to check her understanding, not to assert it | "You tend to come back to the architecture late at night. Is that on purpose?" | ~1 per conversation, only if no curiosity question was asked |
| **Getting to know** | Asked for her own understanding, not for a task | "You've mentioned Double R a lot. What does 'done' look like for that build?" | ~1 per week per subject, relaxed moments only |

**Rules (kept)**
- **Only for genuine gaps.** Curiosity comes only from a real gap. No gap, no question.
- **Timing.** Unsolicited curiosity questions never come when the person is stressed, rushed, mid-task or in a rapid exchange. Questions the task itself needs are part of answering (§7.0), not curiosity.
- **Sensitive topics.** **Curiosity never probes sensitive topics** (CE-P6). Raising a sensitive item that matters follows ARCH-04: a brief opening, then confirmation. That is a different thing from curiosity about it.
- **Avoidance ends it** (principle 9).
- **Answers feed memory.** An answer is that person's own statement (A03 §5.3). It may resolve a remembered situation or confirm or correct a pattern.
- **Curiosity eases as she learns.** Where her knowledge is thin she has more to ask; as the gaps close she asks less and shifts towards observations and connections. It follows the real state of her knowledge, never a manual dial (Cognitive Engine CEA-D06, kept as intent; the density score and fixed-per-session mechanics aren't carried).
- **One new kind at a time.** Each new kind of unprompted behaviour is switched on and checked under real conditions on its own before the next is added (CEA-D08, kept as a build principle).
- **Patterns must be genuinely uncertain.** Patterns she checks need independent evidence across separate conversations (A03 §5.5). Her own repetition doesn't count.

**Unresolved things stay with her.** Cognitive tension, the Android idea, is kept as a *signal*. Unresolved, recurring, contradictory or anomalous things she knows raise her attention to related context. That makes connections and curiosity more likely. It never produces output by itself, and it never creates a watch (A03 §11).

### 7.4 Events arriving mid-conversation

The Android Cognitive Engine rule "no new candidates mid-session" is **not carried over**.
- **Curiosity.** Curiosity can arise from the present conversation: she may notice a new gap. Background preparation happens beforehand, but it does not freeze her ability to notice.
- **Live events.** A text from Micah arriving while Brian is talking with Zola is evaluated normally by A10. If it is eligible, she **waits for a natural pause** before bringing it in: *"Oh, Micah just texted, actually."* **Only time-critical items may cut in** (ARCH-22). Otherwise it is held.

---

## 8. As built on Windows (2026-10-29)

| Capability | State | Evidence | Decisions |
|---|---|---|---|
| Watches from Brian's words or an accepted offer; deterministic close or Brian confirms; lapse told once; "I never stop watching on my own" | live-tested | P9 | P9-D09 |
| Watch matching uses the source's own timestamp; never matches its own source message | live-tested | P9 | P9-D09 fix |
| Watching a person across texts and email | shipped (P10) | P10 closeout | P10-D13, P10-D19 |
| Surfacing after a gap: bounded note, most important first, at gist level; "what's pending" lists held items | live-tested | P9 | P9-D10 |
| Unprompted speech: one coordinator; fixed phrasings with a name or "someone"; no subject or gist; final check under a reservation lock; accepted ≠ started ≠ completed; uncertain never re-spoken | live-tested (some gates harness-only) | P9 | P9-D11 |
| Proactive line shown as a bubble, not stored in the session; no follow-up listen | known limits | P9 | S87; D7 (a) |
| Only watched phone items speak; bursts coalesce; notifications never speak | shipped (P10) | P10 closeout | P10-D15 |
| Knock ladder, her own words, summaries beyond surfacing, commitment check-ins and verification, curiosity, resurfacing | **not built** | — | Phase 12 |

---

## 9. Limits

| Limit | Kind | Accepted risk | Note |
|---|---|---|---|
| Fixed proactive phrasings, no content | temporary limit | — | Brian 10/19; P12-D02 |
| No follow-up listening after an unprompted line | temporary limit | — | Speech work |
| Proactive line not stored in the conversation | temporary limit | — | S87 |
| Ordinary-reply echo can become a turn | temporary limit | yes | S77; speech work |
| Only watches speak unprompted | temporary limit | — | A10 |
| Commitment watches (ARCH-15) | deferred capability | — | Needs SOUL change approval when built |
| She never stops watching on her own | lasting boundary | — | P9-D09 |
| Untrusted content never creates a watch | lasting boundary | — | C13 |
| Curiosity never probes sensitive topics | lasting boundary | — | CE-P6 |
| Never embellish authorised content | lasting boundary | — | A01 p4 |
| Phone as a speaking endpoint | deferred capability | — | P12-D01, A12 |

---

## 10. Open questions

- **Q-E1.** *Resolved by ARCH-21:* a spoken ask only, no on-screen cue.
- **Q-E2.** How long she waits after a spoken ask before treating it as "not now", and how often she may ask again. *Unvalidated, Phase 12.*
- **Q-E3.** Curiosity limits. The Android ceilings are a starting point. The calibration and the minimum gap between engagement moments are open (OQ-CE1, OQ-CE2).
- **Q-E4.** How "was that welcome?" is detected, for trust and avoidance signals (OQ-CE4).
- **Q-E5.** *Resolved by ARCH-22:* she waits for a natural pause unless the item is time-critical.
- **OQ-P12-01, OQ-P12-02.** Interruption frequency; learning from feedback. These belong to A10, and A11 consumes the results.

---

## 11. Acceptance scenarios

- **E1. Spoken ask.** Brian is at the desk working. She says "Got a second?" and he says "Yeah". She then delivers Micah's text in her own words, with context. He says "What else did he say?" and she answers without restating. No wake word is needed after her opener (follow-up listening is a target behaviour).
- **E2. "Not now".** She asks and Brian says "Not now". The item is held and heat rises. She raises it later at a natural moment, once, and doesn't ask again in the meantime.
- **E2b. "Yeah" is only for that.** She asks "got a second?" while a draft send is pending, and Brian says "yeah". She delivers the update. The draft is **not** sent, and nothing else is approved or closed. A "yeah" from Bre to a question asked of Brian counts for nothing.
- **E3. Recheck at delivery.** An approved announcement is queued, and Bre walks in before it plays. Protected content is held, and nothing of it is said while Bre can hear (A10 J12).
- **E4. Summary.** After two hours in the shop she tells three items together, most important first. One item is private to Bre and is not in Brian's summary.
- **E5. Commitment.**
  - Brian says "renew the registration by the 15th". She checks in on the 13th at an eligible moment and offers help.
  - A confirmation email arrives. Memory records it at once, attributed. Asked "is the registration done?", she says the email reports it went through and asks whether to close it out. The watch closes only on his yes.
  - If it is still open on the 16th, she says once that it's overdue.
- **E6. Offered watch (C13).** A DMV email shows a deadline. She offers to keep an eye on it, and no watch exists until Brian says yes.
- **E7. Stop watching vs done.** Brian says "stop watching for that". The watch closes, and the remembered situation stays unresolved.
- **E8. Curiosity.** In a relaxed conversation about the engine she asks once about last week's unresolved noise. Brian deflects, and she doesn't ask again or rephrase it.
- **E9. Never a script.** None of her unprompted lines read like a task tracker ("Would you like to update the status of this item?").
- **E10. Interrupted.** An unprompted line is interrupted halfway by the mic button. The record shows where playback stopped and that delivery is uncertain. "What was that?" gets **the whole announcement again**, because Brian may have missed the start too (A06 C9d).
- **E11. Mid-conversation event (ARCH-22).** Micah texts while Brian is talking with Zola about something else. She waits for the next natural pause, then says "Micah just texted, actually", and gives the content, because the audience is private. A time-critical item could cut in.
- **E12. Answering isn't throttled.** After two unprompted lines, Brian asks about the 4Runner. She answers fully, mentions the relevant heat-soak connection, and asks the troubleshooting question she needs. None of this is held back by heat.
- **E13. What's pending, bounded.** Twelve items are held. "What's pending?" gets the eligible ones Brian may hear, most important first, and "a few more if you want them". Nothing of Bre's is included.

- **E14. A brief with nothing waiting.** No held items. Brian says "Give me today's brief". She gives his day: two appointments, the weather and a commitment due Friday. Leaving texts out of his brief doesn't stop her reading him a text when he asks.

---

## 12. Coverage of the source docs

*Status:* **verified** means the destination exists and was checked against a fresh full read on 2026-10-29. **verified (notes)** means it was checked against the full-read notes. **planned** means the destination doc is not yet written.

| Source section | Destination | Treatment | Status |
|---|---|---|---|
| Cognitive Engagement: vision, foundational principle | §1, §2 | preserved | verified |
| Mode 1 curiosity inquiry | §7.3 | preserved; limits unvalidated | verified |
| Mode 2 pattern investigation | §7.3 | preserved; evidence rules from A03 §5.5 added | verified |
| Mode 3 world model building | §7.3 | preserved | verified |
| When engagement happens (passive observation, enrichment, openings, resurfacing) | §7.1–7.2 | preserved | verified |
| Engagement Governor (factors, outputs) | §2 p1; A10 | merged as steps feeding the one decision point (ARCH-09) | verified |
| Memory-driven curiosity, tension, feedback into memory, restraint | §7.3 | preserved; tension as a signal only | verified |
| Integration with Memory Agency; phase sequencing | §7; — | merged; Android phases dropped | verified |
| Open questions OQ-CE1–4 | §10 | preserved | verified |
| Principles CE-P1–P6 | §2, §7.3 | preserved; CE-P3 "two gates" superseded by ARCH-09 (steps feeding one decision) | verified |
| Memory Agency: Open Loop Tracker (what becomes one, states, lifecycle, outputs) | §6; A03 §11 | split: remembered situations → A03; watches → here (matrix §3.4); "abandoned" kept as the A05 *long quiet* signal | verified |
| Memory Agency: cognitive tension | §7.3 | preserved as an attention signal; never output, never a watch | verified |
| Memory Agency: contextual resurfacing engine (candidates, connection types; "the engine does not speak") | §7.2 | preserved | verified |
| Memory Agency: memory use governor | A14 §5.4 | moved | verified |
| Autonomous Behavior §5 emotional regulation | §4 | preserved | verified |
| Autonomous Behavior: deferred summary queue | §5 | preserved | verified |
| Master Plan pillar 16 deferred cognition | §5 | preserved | verified |
| Attention Engine §8 deferred summary coordination | §5 | preserved; alert window vs issue (A10) | verified |
| Perceptual Input: foregrounding levels | §3; A09 (full read when drafted) | merged; ambient level dropped by ARCH-21 (spoken ask only) | verified |
| Cognitive Engine: initiative queue (durable, ages, never silently discarded, empty is valid); CEA-D05 | §6.0, §7.4 | preserved as the held-items queue contract; CEA-D05 not carried | verified (fresh read 2026-11-02) |
| SMS Intelligence: natural surfacing examples | §1, §4 | preserved as examples | verified (fresh read 2026-11-02) |
| Agent Map agent 15 (DailyBriefAgent); Communication Intelligence brief integration and consent surfaces; SMS consent model | §5.1 | **deferred but retained** (ARCH-65); morning window, 4-hour expiry and class names intentionally omitted; `Zola_Daily_Brief_Architecture.md` absent from the checkout (evidence limit) | verified (fresh read 2026-11-02) |
| Cognitive Engine CEA-D06 (curiosity from knowledge density), CEA-D08 (one engine at a time), CEA-D04 removal rules | §7.3; §6.0 | retained as intent and build principle; density score mechanics intentionally omitted | verified (fresh read 2026-11-02) |
| Autonomous Behavior: never manipulate, false urgency, invent memories | §2 p6 | retained | verified (fresh read 2026-11-02) |
