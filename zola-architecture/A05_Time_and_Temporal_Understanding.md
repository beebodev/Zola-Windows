# A05 — Time and Temporal Understanding

*Draft v0.2, 2026-10-29, revised after ChatGPT's review. Author: Claude. **Status: approved for the repo by Brian, 2026-11-02 (ARCH-68). States intent; authorises no implementation.***

*Coverage-map pass, 2026-11-02: coverage rows closed with exact sections; additions from fresh reads of the source docs (see `audit/arch-docs-swap/ARCH_DOCS_COVERAGE_MAP.md` §5).*

*Phase 10 closeout pass, 2026-11-06: as-built rows and Phase 10 citations rechecked against the Phase 10 lore closeout (tag `p10-closed`) in ARCH-SWAP Phase 2; P10-D18 and P10-D19 cited where they belong.*

**Replaces:** `Zola_Temporal_Reasoning_Architecture.md`. Its thread-arc resurfacing goes to A10 and A11. It also replaces the decay sections of Memory Hierarchy §6 and the read-time ageing in Perception Memory, together with A03 §5.4 and §8.

**Governing records:**
- Lore: P6-D05 and the P7 UTC-offset stamp, P8-D10, P9-D05, P9-D11, P10-D08.
- The P9 process lesson: *"after" is the source system's own timestamp*.
- Brian's 10/19 direction §3: conditions become "status unknown".
- Audit scope Q5.
- ARCH-13 for who may hear time-bearing facts.

**What this doc does not decide.** It decides no Phase 11 question. Android numbers below (arc windows, urgency tiers, cooldowns) are unvalidated.

---

## 1. Intent

> "Time is meaning, not metadata." (Temporal Reasoning, kept)

Zola understands what the passage of time *means*, not just when things happened:
- A plan mentioned yesterday is different from one mentioned three weeks ago and never revisited.
- A gap between conversations is itself information.
- "Micah's car broke down" was true when he said it. It may not be true now.
- A meeting next Tuesday matters differently on Monday than it does today.

**What this should feel like:**
- *"We settled that yesterday."* She knows roughly when, without reading out timestamps.
- *"Last I heard the 4Runner wasn't running. That was Tuesday, and I haven't heard since."* She distinguishes what was reported from what is true now.
- *"Your dentist appointment is tomorrow at 10, and you've got the shop at 9. That's tight."* She looks ahead, not only back. Noticing the conflict is A10's job; knowing the times is this doc's.
- After a week away, she knows it has been a week. She doesn't hedge everything she knows.

**What it must never feel like:**
- an alarm counting down to topics
- a nag that surfaces unresolved items on a schedule
- a logger that stamps every answer with times
- treating all elapsed time as urgency

---

## 2. Principles

1. **One clock.** One system clock is the authority for "now". It uses local time with an explicit UTC offset for meaning, and monotonic timers for durations. Durations use `perf_counter`, never `time.monotonic()` on Windows; that is a P9 lesson. *Today: the P6-D05 / P7 per-message stamp.*
2. **Three different times, three different rules.** They are never interchangeable.
   - **Communication time** is the source system's own timestamp for the message:
     - an email's internal date;
     - a text's phone-received time (P10-D08).

     It governs **ordering of communications and watch matching**: *"after" is the source system's own timestamp, not the time we ingested the row* (P9 process lesson; the reply-loop false announcement). It is **not** the time of the event the message describes.
   - **Reported event time** is when the underlying event happened, *as reported*. "Fixed it yesterday" received Thursday reports Wednesday. The message date is only the reporting date. For scheduled events, the calendar is the authority on when (P8-D10).
   - **Retrieval time** is when Zola learned about it. It is never treated as either of the other two.
3. **Never invent a time.** An event time is recorded only when it was stated or comes from an authoritative source. Unknown stays unknown (P6-D02 rule 5, P6-D04).
4. **Ages are computed when read, not stored.** "Three weeks ago", "aging" and "stale" are worked out at the moment they are needed. They are never written down as facts that go out of date themselves.
5. **Time is a lens, not a store.** This doc owns no memory. It reads what A03 holds and interprets it. It never writes facts, and it never speaks.
6. **Time informs judgment; it never is judgment.** Elapsed time can make something worth raising again, but A10 decides whether to raise it and A11 decides how. This doc proposes nothing on its own authority.
7. **Don't read stamps aloud.** Time shapes how she speaks ("yesterday", "a few weeks ago"). It is not recited (P6-D05).
8. **Unknown time suppresses time-dependent output.** If the gap since the last conversation can't be established, she doesn't claim one (Temporal Reasoning, kept).

---

## 3. The times every piece of knowledge can carry

These are separate fields, never merged into one "timestamp". They extend A03 §4's time-and-validity dimension.

| Time | Means | Example |
|---|---|---|
| **Event time (reported)** | When it happened, as reported, with its precision | The car broke down Tuesday (a day, not a moment) |
| **Statement / communication time** | When someone said or wrote it; the source's own timestamp | Micah texted Thursday 4:12 pm |
| **Observation / retrieval time** | When Zola read, heard or saw it | Zola received it Thursday 4:13 pm (or Friday, if delivery was delayed) |
| **Validity** | When the claim is or was true, as an interval if known | Worked at the garage 2019–2023; the car is not running *from* Tuesday, *until* unknown |
| **Last evidence** | The most recent independent evidence supporting it | Nothing since Thursday |
| **Future time** | When something is due or scheduled | Appointment next Tuesday 10 am; "in two weeks" |

**Event time vs mention time.** A person telling Zola on Thursday that something happened on Tuesday creates an event dated Tuesday and a statement dated Thursday. Recall uses each one correctly:
- *"He said Thursday that it broke down Tuesday."*

**Relative expressions** ("last weekend", "yesterday", "in two weeks") are resolved against **the author's statement context**, never against the PC's current date. "Yesterday" in a text written late Monday night but delivered Tuesday morning means Sunday. For each one Zola keeps:
- **the original expression**, as said;
- **the anchor**: the statement time it was resolved from;
- **the time zone of the author or source**, when known;
- **precision**: a day, a weekend, "around" two weeks, or an exact time. "Tuesday" stays a day. It never silently becomes a midnight timestamp;
- **the resolved date or interval.**

P6-FIX-2 already resolves "last weekend" to a Sat–Sun interval.

**Future local times follow local rules.** An appointment at 10 am, or a weekly practice at 6 pm, is kept as *local time in its time zone*, not as a fixed UTC offset. It stays at 10 am, or 6 pm, across daylight-saving changes. A UTC offset alone does not define how future or recurring local events behave.

---

## 4. Conditions, and when they become unknown

Brian's 4Runner case needs something the Android design didn't have. A *reported condition* becomes *status unknown* without fresh evidence. The *report itself* stays true forever (direction §3; digest §2.8).

**How each kind of knowledge (A03 §3.3) ages:**

| Kind | Ages how |
|---|---|
| Event | Doesn't. It happened. Recall gets less likely over time, but the event stays true. |
| Claim | Doesn't. It was said. |
| Condition | Its *current* status becomes less certain as time passes without new evidence, until it is **unknown**. |
| Established fact: **immutable history** (a birth date, an event that happened, who someone's parent is) | Doesn't age. It changes only by correction or forget. |
| Established fact: **changeable attribute** (a job, an address, who owns a car, some relationships) | **Valid as of its evidence date.** The record itself stays true: "as of March, she worked at the garage". Confidence that it is *still current* fades slowly without fresh evidence. How fast depends on the kind of attribute (P11 audit, Q5). It fades slowly enough that Zola does not start hedging everything she has been told. |
| Inference | Follows its sources. |

**Conditions age differently by kind.** A breakdown, a job, an illness, a move and a cancelled appointment each go stale at their own pace. The design stays open (digest §2.8). Candidates, for the P11 audit:
- an expected duration per kind of condition
- a validity window
- treating status as unknown until refreshed, with no assumed duration

A single fixed window for everything is not the intent.

**How she speaks about an ageing condition:**
- *"Last I heard…"*
- *"As of Tuesday…"*
- *"I haven't heard since."*

The ageing never silently turns into "it's fixed" or "it's still broken".

**A new report closes the old condition with the reported time.** When Micah texts on Thursday that he "fixed it yesterday", the "not running" condition ends on **Wednesday**, with day precision. His message (Thursday) is the reporting date. If he gives no time ("it's fixed"), the condition ends *on or before* the message date. The history stays.

**Absence scaling** (Self-Model Awareness, kept). A long gap in *conversation* is different from a long gap in *evidence about the world*. After Brian has been away a while, well-reinforced knowledge keeps its strength. She doesn't start hedging everything. *The Android cap (30-day effective age after a 14-day gap) is unvalidated.*

---

## 5. Looking ahead

Future time is in scope, not only elapsed time:
- **Scheduled events.** Calendar is the authority on when (P8-D10). Memory keeps what was said and decided about an event. The live calendar result wins on the time, and calendar results are never saved as stated facts.
- **Deadlines and commitments.** Examples: "I need to get the registration done by the 15th"; "Micah's practice is Thursdays". These are stored with their future time, or their recurrence, and their provenance.
- **Relative future.** "In two weeks" and "after the trip" are resolved against the statement time when possible. If the anchor is unknown ("after the trip", with no trip known), the time stays unresolved and the original wording is kept.
- **Recurring things.** Weekly practice, monthly bills and seasonal routines each have a recurrence, not a list of copies. Seasonal and annual reasoning remains a deferred capability.

Spotting *conflicts* between future times (two things at once, a deadline before a trip) is situational intelligence. It belongs to A10 and Phase 12. This doc makes sure the times are there to compare.

---

## 6. Time between conversations

- **The gap since the last interaction** comes from one source: a content-free `last_interaction_at` marker (P6-D05). Gaps above `MeaningfulGapMinutes` (30, tunable) count as meaningful.
- **Surfacing uses its own gap** (P9-D10: `SURFACE_GAP_SECONDS` 1800). Over time, these should resolve through one gap authority, not two independent calculations. *Open: Q-T2.*
- **If the gap is unknown,** she says nothing that depends on it.
- **Recalling past conversations** carries roughly-when (P6-FIX-WHEN): *"We talked about that last week."*
- **Per person (ARCH-03).** Gaps are per person. Bre's last conversation with Zola is not Brian's.

---

## 7. Threads going quiet (vision)

Temporal Reasoning's thread arcs are kept as a *signal*, owned here. What to do with the signal belongs to A10 and A11.

| Arc | Meaning | *Android window (unvalidated)* |
|---|---|---|
| Fresh | Just touched | < 24 h |
| Active | In progress | < 7 d |
| Aging | Starting to drift | 7–21 d |
| Quiet | Meaningful silence; may be resolved without anyone saying so, or neglected | 21–60 d |
| Long quiet | Long silence, still open | > 60 d |
| Overdue | **An expected date or commitment has passed**, and the thread is still open. Silence alone never makes something overdue. | n/a (needs a due date) |
| Dormant | Its owner has already marked it inactive | — |

**Rules (kept):**
- An arc is computed, never stored.
- An arc applies to **remembered situations** (A03 §11) and to **watches** (A11). Each keeps its own status owner.
- **Elapsed silence alone never creates urgency.** An old topic doesn't become urgent because it is old. *The Android cap on silence-based resurfacing was 0.55; unvalidated.*
- **Explicit deadlines and time-sensitive consequences** are different. An approaching appointment, or a registration due Friday, does inform A10's urgency judgment, because time is running out.
- Cooldowns between resurfacings of the same thread live in **one central place**, the A10 decision point. They are not applied by each source of candidates.
- A topic someone has repeatedly declined to engage with is not resurfaced on time alone.
- Resolved topics are not kept artificially open just to track how often they come back.

---

## 8. Freshness of sources

Sources have time too:
- **How current a source is.** Example: the watcher last polled Gmail 2 minutes ago, or the phone has been unreachable for an hour.
  - This changes what she can claim. "Nothing new from Micah" is only true if she can currently hear from Micah's channels.
  - When a source is stale or unreachable, she says so, as Phase 9 and Phase 10 already do. Examples: the stale thresholds (360 s Gmail, 14,400 s Calendar, P9-D12) and "the phone isn't reachable" (P10-D03).
- **"I haven't heard" vs "I can't hear".** These are different statements, and "nothing new" needs **coverage**, not just a working link now.
  - *"Micah hasn't texted since Tuesday"* is claimable only if the sources she relies on synchronised successfully and covered **that whole period on that channel**. The phone's text channel must have had no outage, no incomplete replay, and no unavailable channel in that window.
  - If coverage had a gap, she says so in bounded terms: *"I haven't received anything newer, but there was a gap in the phone connection Wednesday."*
  - If the source can't be reached at all, she says so: *"I haven't been able to check your texts since this morning."*
  - Coverage is a property of each source and each channel. A working Gmail watcher says nothing about texts.

---

## 9. Quiet hours and timing

- **Quiet hours** are 22:00–07:00 local today (P9-D11). They are a *temporary limit* and a default. Brian's classification (10/19) keeps them as his floor.
- **Delivery timing** belongs to A10, which judges when to raise something.
- This doc provides the time facts that judgment needs: local time, gaps, how old an item is, and what's coming up.
- A delayed item still keeps its own event time. *At 07:00, an item speaks only if it is still inside its maximum age* (P9-D11: `SPEECH_MAX_AGE_SECONDS` 7200).

---

## 10. As built on Windows (2026-10-29)

| Capability | State | Evidence | Decisions |
|---|---|---|---|
| Per-message local time stamp with UTC offset, never read aloud | live-tested | P6, P7 | P6-D05 |
| Gap since last interaction via `last_interaction_at`; meaningful gap 30 min | live-tested | P6 | P6-D05 |
| Episode `event_time` only when stated or from an authoritative source; relative phrases resolved ("yesterday", "last weekend") | live-tested (C2 blind test; P6-FIX-2) | P6 | P6-D04 |
| Roughly-when in recall | live-tested; same-day recall may omit it | P6 | P6-FIX-WHEN |
| Calendar is the authority on when; historical events visible | live-tested | P8 | P8-D10 |
| Source timestamps for "after"; reply loops use Gmail `internal_date` | live-tested | P9 | P9-D09 fix |
| Text time = phone's received time | shipped (P10) | P10 closeout | P10-D08 |
| Watcher staleness shown and spoken | live-tested (stale wording proven in scratch only) | P9 | P9-D12 |
| Quiet hours 22:00–07:00; maximum age at 07:00 | harness-tested (K4) | P9 | P9-D11 |
| Validity intervals, conditions becoming unknown, last-evidence time | **not built** | — | Phase 11 (Q5) |
| Future commitments and deadlines from conversation | **not built** (calendar only) | — | — |
| Thread arcs; time-based resurfacing | **not built** | — | Phase 12 (A10/A11) |

---

## 11. Limits

| Limit | Kind | Accepted risk | Note |
|---|---|---|---|
| No validity or condition model; observed conditions vanish with the 7-day raw-content limit | temporary limit | — | Phase 11 (Q5) |
| Two gap calculations (memory gap and surfacing gap) | temporary limit | — | Q-T2 |
| Fixed quiet hours | temporary limit (a default; Brian's floor) | — | P9-D11; timing judged in Phase 12 |
| 24-hour injection bound uses `detected_at`, not the message's own time | temporary limit | yes | P9 known limit; contrary to principle 2 |
| Seasonal and annual reasoning | deferred capability | — | — |
| Never invent a time | lasting boundary | — | P6-D02 |
| Never read stamps aloud | lasting boundary | — | P6-D05 |
| Elapsed silence alone never creates urgency (deadlines may) | lasting boundary (proposed) | — | Temporal Reasoning, narrowed |
| "Nothing new" is claimable only with coverage of the period and channel | lasting boundary (proposed) | — | §8 |
| Coverage of a period isn't tracked yet; only current health is | temporary limit | — | P9-D12 health rows; P10 disconnect reason codes are a start |

---

## 12. Open questions

- **Q5 (P11 audit).** How conditions become "status unknown": an expected duration per kind, validity windows, or unknown until refreshed.
- **Q-T1. Future commitments.** *Resolved by ARCH-15.*
  - A commitment Brian states with a time ("renew the registration by the 15th") is remembered with its due date (A03).
  - It is also watched (A11).
  - Zola checks in ahead of the due date and helps with the task.
  - She verifies completion, closing the watch only when Brian confirms.
  - **What counts as a commitment (C12):**
    - A clear task with a time is watched automatically.
    - A vague one with no time is remembered only.
    - An in-between one gets one question: "keep track of it?"
  - **Deadlines found in email, bills or texts (C13):** Zola offers to track them. She never creates a watch from untrusted content on her own.
- **Q-T2.** One gap authority for memory and surfacing, or two kept on purpose. The answer comes from evidence in the P11 audit.
- **Q-T3.** Time zones. The household shares one, and the phone and PC use local time. Travel, or someone texting from another zone, may need the source's offset kept. It is kept today through the UTC offset.

---

## 13. Acceptance scenarios

- **T1. Event vs mention.** Thursday: "Micah's car broke down Tuesday." Later she says it broke down Tuesday. She doesn't say "you told me it broke down" with a Thursday date.
- **T2. Status unknown.** A week later, with no new evidence: "Last I heard it wasn't running, as of Tuesday. I haven't heard since." She says neither "still broken" nor "fixed".
- **T3. Status change uses the reported time.** Thursday, Micah texts "fixed it yesterday". The condition ends **Wednesday**, with day precision. Thursday is recorded as the reporting date, and the earlier report stays.
- **T4. Can't hear vs haven't heard.** With the phone link down since morning, "Has Micah texted?" gets *"I haven't been able to check your texts since this morning."* It does not get "No."
- **T4b. Coverage gap.** The link is healthy now but was down for three hours Wednesday. "Anything from Micah since Tuesday?" gets *"Nothing newer that I've received, but there was a gap in the phone connection Wednesday."* It does not get a flat "No."
- **T5. Communication time for ordering.** An email delayed in delivery is ordered by its own time, not by when the watcher saw it. A watched-reply match never fires on the message the watch was created from (the P9 lesson).
- **T5b. Delayed message across midnight.** Micah writes "it broke down yesterday" at 11:50 pm Monday. It is delivered at 12:20 am Tuesday. "Yesterday" resolves to **Sunday**, from the author's statement time, not the delivery date.
- **T5c. Daylight-saving change.** A weekly 6 pm practice stays at 6 pm local time across the clock change. It doesn't shift to 5 pm or 7 pm.
- **T6. Relative time.** "We'll do it in two weeks", said on the 1st, resolves to around the 15th, with its origin kept. "After the trip", with no trip known, stays unresolved.
- **T7. Away and back.** After ten days away, she knows it has been about ten days. She doesn't hedge well-reinforced facts.
- **T7b. Changeable fact.** Brian said in March that Dave works at the garage. Months later, with no new evidence, she says *"Dave worked at the garage, as of March"* if it matters. She doesn't hedge settled history ("Micah is your son").
- **T7c. Overdue vs long quiet.** A thread untouched for 70 days with no due date is "long quiet", never "overdue". A registration due the 15th, still open on the 16th, is overdue.
- **T7d. Stated commitment (ARCH-15).** Brian says "I need to renew the registration by the 15th".
  - She remembers it with that date, and a linked watch exists.
  - Ahead of the 15th, and within A10's timing rules, she checks in and offers help.
  - A renewal-confirmation email arrives. She asks Brian whether it is done and closes the watch only when he says yes.
  - If it is still open on the 16th, it is *overdue*.
- **T7e. Observed deadline (C13).** A DMV email says the registration expires the 15th. Zola offers to keep an eye on it. No watch exists until Brian accepts.
- **T7f. Vague intention (C12).** "I should clean the garage sometime" is remembered, and no watch is created. "I need to call the insurance guy this week" gets one question about whether to track it.
- **T8. No invented time.** Asked when something happened that was never dated: *"I don't know when. You mentioned it on the 3rd."*

---

## 14. Coverage of the source docs

**Status:** *verified* means the destination exists and was checked against a fresh full read on 2026-10-29. *planned* means the destination doc is not yet written.

| Source section | Destination | Treatment | Status |
|---|---|---|---|
| Vision, Core Philosophy (time is meaning; lens not store; how a person uses time) | §1, §2 | preserved | verified |
| Non-goals | §2 p5, p6 | preserved | verified |
| Architectural position (reads, produces, never) | §2, §7 | merged | verified |
| Clock authority | §2 p1 | preserved, Windows-mapped | verified |
| Session boundary resolution; short-session amnesia | §6 | superseded on Windows by `last_interaction_at` (P6-D05), which covers short sessions | verified |
| SessionBoundaryResolver (null = unknown, suppress) | §2 p8, §6 | preserved | verified |
| ThreadArcClassifier | §7 | preserved as a signal; windows unvalidated | verified |
| TemporalContextAssembler, `[TEMPORAL]` brief section | A03 §10 (one context path) | merged | verified |
| TemporalInitiativeSource, urgency tiers | A10 §4.3; A11 §6 | moved (numbers unvalidated) | verified |
| Initiative Queue temporal gate (central cooldown) | §7; A10 §7 | merged; principle kept here, mechanism moved | verified |
| Integration tables (Kotlin, Firestore) | — | intentionally dropped: platform plumbing | n/a |
| Known constraints: resolved-topic cadence, no seasonal reasoning, clock fragmentation | §7, §11, §2 p1 | preserved | verified |
| Authority boundaries | §2 p5, p6 | preserved | verified |
| Relationship to the Relational Intelligence Layer | A02b §4, §5.4 | moved | verified |
| Long-term end state; final principle | §1 | preserved | verified |
| **Not in the source; added from direction §3 and the audit scope:** event vs mention time, validity, conditions becoming unknown, future time, source freshness | §3–§5, §8 | new (vision) | — |
