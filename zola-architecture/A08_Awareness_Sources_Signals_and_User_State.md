# A08 — Awareness: Sources, Signals and User State

*Draft v0.3, 2026-10-29 (Messenger drop; ARCH-23 location; ChatGPT review). Author: Claude. **Status: approved for the repo by Brian, 2026-11-02 (ARCH-68). States intent; authorises no implementation.***

*v0.4, 2026-11-02 — reconciliation pass after the coverage audit: confidence and urgency separate (ARCH-63); overload contract (audit C07); daily brief sources (ARCH-65); scenario W13.*

*Coverage-map pass, 2026-11-02: coverage rows closed with exact sections; additions from fresh reads of the source docs (see `audit/arch-docs-swap/ARCH_DOCS_COVERAGE_MAP.md` §5).*

*Phase 10 closeout pass, 2026-11-06: as-built rows and Phase 10 citations rechecked against the Phase 10 lore closeout (tag `p10-closed`) in ARCH-SWAP Phase 2; P10-D18 and P10-D19 cited where they belong.*

**Replaces:**
- `Zola Environmental Awareness Architecture.md`: sources, location, time, calendar, weather, traffic, device, notification and workspace awareness, structured events, user state, awareness modes, shared-space rules, anti-noise and endpoint behaviour. The interpretation, fusion, scoring and disposition parts move to A10.
- `Zola_Architecture_Environmental_Event_Bus_and_User_State_Model.md`.
- `Zola_Communication_Intelligence_Architecture.md` and `Zola_Sms_Intelligence_Architecture.md`, kept as design reference.
- Agent Map agents 1 (context cache), 6 (notification priority) and 12 (world-state snapshot).

**Governing records:**
- Lore: P8-D01, D04, D09, D10; P9-D01, D03–D08; P10-D01–D19 (Phase 10 closed 2026-11-06); S12; S13.
- `PHASE12_DECISIONS.md`: P12-D05, OQ-P12-03.
- ARCH-03, ARCH-05, ARCH-06, ARCH-07, ARCH-12, ARCH-13, ARCH-18, ARCH-19.

**Android numbers below are unvalidated.** This covers confidence floors, refresh rates and staleness windows.

---

## 1. Intent

> "The purpose of awareness is context." (Brian, 10/19)

Zola takes in what's happening around the people she lives with. That includes:
- conversation
- email
- calendar
- texts and app notifications from the phone
- the state of her own devices

Later it will include location, weather, home and shop context and, eventually, cameras and sensors (A09).

She keeps a running, honest estimate of **what each person is likely doing right now**: busy, in a call, in the shop, at the desk or asleep. She uses it so that what she says and when she says it fits the moment.

> **Awareness is not interruption.** Signals may be noticed, interpreted, remembered, summarised or ignored without ever becoming speech. Silence is a valid outcome. (Environmental Awareness, kept)

**What this should feel like:**
- She knows a text from Micah arrived two minutes ago, even though nobody told her.
- She knows Brian has a call in 40 minutes, so the bar for raising something minor is higher now.
- She knows the phone link dropped an hour ago. "Nothing from Micah" becomes "I haven't been able to check your texts since 2" (A05 §8).
- She never feels like a surveillance dashboard, a motion-alert system or a raw notification relay.

---

## 2. Principles

1. **Sources are inputs only.** No source decides meaning, importance, timing or output. A source can't speak, notify, write memory or act (A01 principle 2; Event Bus "the bus is the only path").
2. **One governed intake for things she might raise; records stay with their owners.**
   - **What goes into the store.** Incoming observations that Zola might raise unprompted become items in the **proactive store** (P9-D06; P10-D12 "one store owner"). Examples: new mail, texts, notifications, calendar changes, and later sensor events. The Android "event bus" intent is met by that store, and nothing runs a second channel around it.
   - **What stays with its owner.** Other information is *not* copied into the store:
     - conversation turns (Hermes);
     - requested tool results such as Drive reads;
     - live client state;
     - the location history (§6.1).

     One governed intake contract decides what becomes an item. An item may *reference* a record owned elsewhere, by id, instead of copying it.
3. **Raw signals never produce speech** (Environmental Awareness, non-negotiable). Every user-facing outcome passes through interpretation and the A10 decision point.
4. **Untrusted content is data, framed as such** (P8-D09). Message, notification and event text is framed as untrusted the moment it is read.
5. **Each source records its own time, health and coverage.** That covers communication time, retrieval time and whether the source has been working (A05 §3, §8). A source that has been down is never mistaken for a quiet one.
6. **User state is always an estimate.** Every field carries:
   - its source
   - its confidence
   - its age

   - Stale is treated as unknown.
   - On a tie, she assumes the costlier interpretation. Under-interrupting is better than interrupting at the wrong moment (Event Bus, kept).
7. **User state is per person** (ARCH-03, ARCH-19). What Brian is doing is not what Bre is doing.
8. **Heat is not user state** (A10 §7). User state describes the person's world. Heat describes Zola's own recent demands. They meet only at the A10 decision point. *(The Android doc both stated this and derived interruption tolerance from heat. The first rule wins.)*
9. **Collect for a purpose, and keep what the person chose to keep.**
   - Audio is classified, never recorded (ARCH-05).
   - Raw communication content is kept 7 days at most (P9-D07).
   - Location is kept as Brian chose: coordinates and history (ARCH-23, §6.1).
10. **The PC is the brain; devices are senses** (A01 principle 11; P10-D02). The phone detects and forwards. The PC decides what matters.

---

## 3. Sources

### 3.1 On Windows today

| Source | How it arrives | Owner | State |
|---|---|---|---|
| **Conversation** | Typed or spoken turns in the Hermes session | Hermes; client (capture) | live |
| **Gmail** | Watcher polls every 2 min (INBOX `messageAdded`); bounded body read; framed untrusted | Workspace watcher (P9-D03–D05) | live-tested |
| **Calendar** | Watcher polls every 2 h; new events after baseline; changes matching a watch. Calendar is the authority on *when* (P8-D10) | Workspace watcher | live-tested |
| **Contacts** | Read-time lookup on Brian's turns; contact index for texts | `zola_workspace` in serve (P9-D04: the watcher never calls Contacts; P10-D10, P10-D18) | live (lookup); shipped (index, P10) |
| **Drive** | Tools on Brian's request only; not a background source | `zola_workspace` tools (P8) | live |
| **Texts** (SMS, MMS, RCS) | Phone companion detects and forwards over one signed, held connection; `zola-phone` ingests; history read on request | Companion + `zola-phone` (P10-D01–D12) | shipped (P10) |
| **App notifications** | Allowlisted apps only. List per P10-D16, as amended 2026-10-29: Messages (never forwarded as a notification), Life360, Visual Voicemail, Instagram. **Facebook Messenger is dropped** (Brian, 2026-10-29). | Companion `notify` (P10 Track 4) | shipped (P10); never spoken unprompted (P10-D15) |
| **Client state** | Locked/unlocked, Voice or Text mode, capture, playback, clarify, reviewed draft, current turn | Windows client | live (P9 speech gate) |
| **Source health** | Watcher, Google account, ranker, voice, backend, phone link | Systems panel rows; health rows | live (P9); phone row shipped (P10) |
| **Time** | Local time with UTC offset; gap since last interaction | A05 | live |

### 3.2 Vision (not built)

Each arrives through §2's one path. Each needs its own permission, retention and an A14 decision before it is collected.

| Source | What it adds | Notes |
|---|---|---|
| **Location (Brian, ARCH-23)** | Where he is now, and where he was and when. Also home, shop, away, driving, arriving. | From the phone companion; coordinates kept on the PC. Brian only for now. See §6.1. Life360 arrival notices (P10-D16) remain a separate notification source. |
| **Phone device state** | Call active, do-not-disturb, headphones, car Bluetooth | Through the companion; capability-named contract (P10 R4) |
| **Weather** | Only when it affects something planned (outdoor work, a commute) | Generic forecasts stay silent |
| **Traffic** | Only when tied to a real departure or commitment | "Only valuable when it can change a decision" |
| **Media and health** | Context: working out, sleeping, music | Sensitive (A14) |
| **Home, shop and smart home** | Shop activity, compressor running, garage open, shop speaker | First-class workspace context |
| **Vehicle** | Driving, alerts | — |
| **Cameras, doorbell, environmental audio** | Who's there, what's happening | A09 |
| **Wearables, glasses** | Presence and an ambient surface | A12 / A09 |

---

## 4. What a source produces: an item

On Windows, each thing a source contributes becomes an **item** in the proactive store. The Android "structured event" intent maps onto it. The shared minimum is below; *how* the store's schema grows toward it is a Phase 11/12 audit question, not a decision here.

| Field (intent) | Means | Windows today |
|---|---|---|
| Stable id and idempotency key | One real thing is one item; replays and resends are recognised as duplicates | yes (P9 items; P10 R2 device id + type + provider id) |
| Revision, completeness, removal | **A duplicate is not an update.** A completed MMS, an edited notification or a rescheduled event is *new information about the same item*: a new revision, never a second item and never silently dropped. A cancellation or removal is recorded as such. | partial (P10 R2 late content and revisions; P9 calendar `<event id>:<updated>` keys) |
| Source and device | Which source and which device | yes (P10 R4 device ids) |
| Communication time / retrieval time | A05 §3 | yes (source time; `detected_at`) |
| Attribution | Sender identity as resolved, with authentication (P12-D05) | partial (address and number hashes; Contacts at read time) |
| Content, framed untrusted, retention-limited | What was said; 7-day limit | yes (P9-D07) |
| Related entities | Links to people, vehicles and projects (A03/A04) | not yet (G1) |
| Alert window | How long it stays worth raising as an interruption (A10 §4.3) | partial (speech maximum age; injection age) |
| Ranking source and judgment slot | Who judged importance: code, model, none | yes (P10-D11 `ranking_source`, `judgment`) |
| Restrictions | Whose information it is, intended recipients (ARCH-13), protected categories | partial |
| Confidence (for sensor items) | How sure the interpretation is | n/a until A09 |

**Rules kept from the Event Bus doc:**
- Duplicates are recognised and counted once.
- An alert whose window has already passed is not raised as an interruption.
- **Confidence and urgency are separate** (ARCH-63). A low-confidence item isn't barred from urgent evaluation: A10 weighs the evidence, the possible consequence and the cost of waiting, and an uncertain item is worded as uncertain. *This replaces the Event Bus rule that low-confidence sensor items never reach high-urgency paths.*
- Each item gets an audited outcome.

**One Android rule is replaced.** The Android single privacy ladder (PUBLIC, HOUSEHOLD, PRIVATE, SENSITIVE) is replaced by A14's composed checks: whose information it is, the audience, the channel, the topic's sensitivity and the kind of content.

**When intake can't keep up** (kept from the Event Bus §2 and Environmental Perception §15; queue technology, retry counts and priorities are build decisions):
- **Items are checked before they're accepted.** A malformed item is rejected, and the rejection is recorded.
- **Resources are bounded.** A burst from one source (a camera, a busy group chat) can't fill storage or starve the rest.
- **Direct speech and important items come first.** A flood of low-value items never delays Brian talking to her.
- **Replay keeps the original identity and time.** Catching up after a backlog never presents old activity as fresh or urgent (A10 §4.3).
- **Loss is recorded as a coverage gap.** If items had to be shed, she knows she has a gap for that source and window, and says so honestly (A05 §8).
- **No unbounded backlog of stale alerts.** Items past their alert window are retired as alerts, though ongoing issues remain (A11 §5).
- **Low confidence isn't a reason to shed something serious** (ARCH-63).

---

## 5. User state: what each person is likely doing

A per-person estimate. Each field records its source, its confidence and its age.

| Field | Values (illustrative) | Windows signals today | Later |
|---|---|---|---|
| **Activity** | at the desk, in a conversation with Zola, in a call, in a meeting, hands-busy in the shop, driving, idle, asleep, unknown | client state (capture, turn, playback); calendar event now; time of day | phone call and DND; location; shop context; health |
| **Workspace** | office, home, shop, vehicle, away, unknown | PC in use | known places (§6) |
| **Interruption tolerance** | open, reduced, low, minimal, emergency-only | Explicit settings first ("quiet", "not now", proactivity level, A10 §6). Inferred activity adjusts only within what those allow. *Not* from heat. | — |
| **Who is present** | participants, audience, unknown others (A06 §7.1) | none today (one user assumed, S1) | voice and face (A07/A09; ARCH-07, ARCH-12) |
| **Noise** | quiet, ambient, loud | — | audio classification, never recording |
| **Conversational readiness** | talking with Zola, just talked, available, distracted, unavailable | turns; last user turn; last Zola speech | — |
| **Calendar context** | in an event now; minutes to next; day density | Calendar (live) | — |
| **Device state** | locked, mode, capture, playback, DND, call | client (live) | phone (companion) |
| **Emotional register** | — | — | **Sensitive inference** (§7) |

**Three kinds of input, kept distinct.** They are never merged into one confidence contest:

| Kind | Examples | Rule |
|---|---|---|
| **Authoritative device state** | PC locked, capture active, playback, a call active on the phone | Treated as fact while fresh |
| **Explicit person settings** | "quiet", "not now", a chosen proactivity level, quiet hours, preferences (ARCH-19) | **Always win over inference.** An inferred "seems available" never overrides an explicit quiet setting |
| **Inferred activity** | Seems to be at the desk; probably in the shop; may be driving | An estimate, with confidence and age |

**Conflict rules (kept), applied among inferences only:**
- Higher confidence wins.
- On a tie, the costlier interpretation wins for interruption purposes.
- An on-change signal beats an older periodic reading.

**A calendar event is evidence of a scheduled meeting, not proof of attending it.** It raises the likelihood that Brian is busy; it doesn't establish it.

**One estimate, read by everyone.** Every component reads the same user-state estimate; nobody builds their own picture from raw signals. A stale field gives its last value with no confidence and never blocks the reader (Agent Map, Agent 12).

**Who reads user state:**
- A10, for timing and audience
- A06, for participants
- A11, for its delivery-time recheck
- A02, for tone

It is read when needed. It never pushes output.

---

## 6. Places and modes (vision)

### 6.1 Location (ARCH-23)

**Brian decided:**
- Location comes from the phone.
- Zola keeps **actual coordinates and their history**, so she can know where he was and when.
- It covers **Brian only, for now**.

**How it works (vision; mechanics belong to a later phase):**
- **Collection.** The companion reports location over the same signed connection (P10-D07), as a capability-named feed (P10 R4). The phone decides nothing. The PC turns coordinates into context: home, the shop, driving, arriving at the school.
- **Each observation is the phone's location, attributed to Brian with a stated basis.** It records:
  - observation time;
  - reported accuracy;
  - gaps in sampling;
  - **the basis for treating the phone as Brian**: his paired phone, normally with him.

  It is evidence about Brian, not certainty. If the phone is left at home, the record says where the *phone* was.
- **Arrivals, departures, visits and "driving" are derived interpretations,** worked out from the points, with their uncertainty. They are never exact facts the points don't support.
- **Two uses, one record.**
  - **Context now:** where he is, for timing and for "you'll be late if you leave after 3:30".
  - **History:** where he was and when, for "when did I leave the shop Tuesday?" and "was I at the parts store last week?".
- **Places are entities.** Named places (A03) are matched against coordinates. Visits become events with times: arrived at the shop 9:12, left 4:40.
- **Local only.** It never goes to a third-party memory service (P6-D07). Model processing of location, if any, is a separate stated boundary on the privacy page.
- **For Brian's reference only** (C16). Zola never tells anyone else where Brian is or was, household members included. The family has Life360 for that. A safety-exception alert (ARCH-03) passes on the concern, never his location.
- **Kept one year** (C15), then expired by policy. He can forget any part sooner.
- **Forget applies.** He can forget a place, a day or a time range, or the whole history (A03 §12). Forgetting reaches **derived visits, place associations and any summaries** built from the points, not just the coordinate rows.
- **It can be switched off** at any time, on the phone or the PC.

**What's still open:** at-rest protection for a location history. H4 is deferred, so today it would rely on BitLocker only. Claude recommends deciding this before it is built.

### 6.2 Known places and contexts

**Known places.** These are named anchors. A known place is matched against Brian's coordinates (§6.1): home, shop, office, "Dad's house". Each has:
- a location
- an optional associated device (the shop speaker, the car)
- default context and privacy profiles

They are created by the person, or suggested when a place recurs and then confirmed. **Location alone gives moderate confidence at most** that Brian is at a known place: being near the shop isn't being in it. A second signal (the shop device, a known pattern) is needed before a high-restraint context like Shop is applied with confidence (Event Bus failure modes, kept). They are editable and deletable. A known place is an **entity** in the world model (A03), not a separate list.

**Awareness contexts.** The Android awareness modes become **contexts that feed A10's timing profiles**. They are not separate authorities.

| Context | Effect |
|---|---|
| Focus / meeting | Raises the bar; only high-urgency items |
| Shop | Hands-free preferred; high restraint; project memory activated |
| Driving | **Unprompted** output limited to safety and navigation; short replies. Brian's own questions are still answered (A10 principle 7). |
| Quiet hours | Near-full suppression of non-emergency output (P9-D11 floor) |
| Security watch | *Deferred (A09)* |

The proactivity levels (A10 §6) are the person's choice. Contexts are what Zola infers. Both feed A10.

---

## 7. Privacy at the source

These apply A14 at intake:
- **Raw content.** Kept 7 days at most. Distilled observations follow A03 and DQ-7.
- **Message and calendar text in background processing.** The Android rule was "message previews and calendar titles never enter the pipeline as readable text without permission". On Windows, **Brian chose otherwise for email**:
  - The watcher reads the full email, trimmed, and the ranker produces a gist (Brian, P9: *"the watcher should be able to read the full email and provide a gist"*).
  - That decision stands, and it is disclosed on the privacy page (P9-D08).
  - Texts are ranked by code only (P10-D11). Widening that is DQ-6 / P12-D03.
- **Codes and reset links.** Masked on the phone, fail closed. Read aloud only on explicit request, through the direct path (P10-D04, R1).
- **Spam and blocked texts.** *Required policy:* texts the phone marks as spam or blocked are not sent (P10-D09). *Implementation unverified:* the transport spike didn't read those columns, and Track 3 was required to find and read them or stop. No recorded result was found in the project docs. Confirm from the Track 3 records before calling this guaranteed.
- **Audio.** Classified for noise and presence, never recorded (ARCH-05). Recognising *who* is speaking is A07's job, under ARCH-07 and ARCH-12. It replaces the Android "never identify speakers" rule.
- **Emotional register.** Any estimate of someone's mood is a **sensitive inference**.
  - It may shape timing and tone in the moment.
  - It is never stored as a fact about the person (A03 §5.7).
  - It is never spoken as an observation unprompted.
- **Location** (ARCH-23). Brian's coordinates and history are kept by his choice. The record is local, for Brian's reference only (C16), kept one year (C15), can be forgotten by place or time, and can be switched off.
- **Source-level control.** Each source and integration can be switched off, and Brian can always ask what is being monitored and why. Switching a source **off** means:
  - collection stops at once;
  - anything queued from that source is not processed further;
  - pending announcements based on it are dropped;
  - already-kept history stays until it expires or is forgotten.

  Switching off never silently means "delete everything", and never "keep processing the backlog". Deleting is a separate, explicit forget.

---

## 8. Anti-noise protections

These are kept from the Android docs. Each is enforced in A10 or A11, and fed by what A08 provides:
- duplicate suppression
- cooldowns per category
- grouping into summaries
- minimum confidence for sensor items, weighed against the possible consequence (ARCH-63)
- heat
- learning from ignored categories, as an inspectable preference (ARCH-19)
- quiet hours

---

## 9. Communications as a source

This preserves the useful design intent of the two Android communication docs:
- **Analysis is not storage.** Reading a message to judge it doesn't make it memory. Memory follows A03's rules.
- **Heuristics first, model second.** Code filters obvious noise before any model sees anything (P12-D03).
- **Consent per channel.** Email and texts are separate decisions. Switching one on is explained in plain words: what is read, what is kept and what is discarded.
- **Texts move in real time.** A thread with five messages in the last two hours means something a single three-day-old message doesn't. How fast a thread is moving is a signal in itself, passed to A10 (SMS Intelligence, kept).

**Superseded on Windows:**
- **The Android "known contacts only" SMS gate.** Unknown numbers were never analysed. Windows orders contacts above unknown numbers instead of excluding them (P10-D10). Vision §3 holds: "an unknown sender may be important".
- **Relationship weight by contact source** (memory 0.9 / calendar 1.0 / phone book 0.6). This collapses trust and importance into one number. It is replaced by A10's six responsibilities.
- **The Daily Brief pipeline.** Still deferred (S12). The brief itself is kept as a deferred feature in A11 §5.1 (ARCH-65); A08 supplies its sources, each with its own per-person choice.

---

## 10. As built on Windows (2026-10-29)

See §3.1 for sources. In addition:

| Capability | State | Evidence | Decisions |
|---|---|---|---|
| One store for all sources; items commit before cursors advance; leases; forget cascades | live-tested | P9 | P9-D06 |
| Watcher: separate supervised process, no model, no tools, fixed read API | live-tested | P9 | P9-D03, D04 |
| `zola-phone`: third supervised process; only PC link to the phone; no Google tokens, no model | shipped (P10) | P10 closeout | P10-D12 |
| Phone controls visibility only; PC decides importance | shipped (P10) | P10 closeout | P10-D02 |
| Source health on the Systems panel; stale watcher wording | live-tested (some wording scratch-only) | P9 | P9-D12 |
| Disconnect reason codes on the phone link | shipped (P10); an unexplained drop of 2026-10-16 is recorded | P10 closeout | P10-D12; S92 |
| Per-period coverage tracking ("was the source working all of Tuesday?") | **not built** | — | A05 §8 |
| Per-person user-state model | **not built** (client state only) | — | — |
| Location, weather, traffic, device state from the phone, home, shop | **not built** | — | — |

---

## 11. Limits

| Limit | Kind | Accepted risk | Note |
|---|---|---|---|
| Gmail every 2 min, Calendar every 2 h | temporary limit (Brian's choice) | — | P9-D05 |
| Brian's own sent mail not watched | temporary limit | — | P9 (not INBOX) |
| Notifications: allowlist only, never spoken | temporary limit | — | P10-D15/D16; OQ-P12-03 |
| No replying or sending texts | temporary limit | — | P10-D17 |
| Text ranking by code only | temporary limit | — | P10-D11 |
| One user assumed; no presence detection | temporary limit | — | S1 |
| No coverage tracking per period | temporary limit | — | A05 §8 |
| 24-hour injection bound uses `detected_at` | temporary limit | yes | P9 known limit |
| Sources never speak or act | lasting boundary | — | §2 p1 |
| Untrusted content framed at intake | lasting boundary | — | P8-D09 |
| Raw communication content 7 days at most | lasting boundary unless changed | — | P9-D07; Brian 10/19 |
| Audio classified, never recorded | lasting boundary | — | ARCH-05 |
| Mood never stored as a fact about a person | lasting boundary | — | A03 §5.7 |
| Location from the phone, with history (Brian) | deferred capability (decided, not built) | — | ARCH-23 |
| Location history kept without application-level encryption | temporary limit | yes, if built before H4 is revisited | H4 |
| Weather, traffic, home, vehicle, health sources | deferred capability | — | §3.2 |

---

## 12. Open questions

- **Q-W1.** *Resolved (2026-10-29):* Facebook Messenger is dropped. P10-D16 is amended. The Track 4 build-plan items and the kickoff are corrected in the T4 prompt.
- **Q-W2: what Bre's and the boys' sources are.** Their own calendars, phones or email (A15 open question). Today only Brian's Google account and phone exist.
- **Q-W3: per-period coverage.** How each source records the windows it was actually working, so "nothing new" can be claimed honestly (A05 §8). Phase 11/12 audit.
- **Q-W4: item schema growth.** Which item fields from §4 the store gains, and when: entities, restrictions, alert windows. Phase 11 (entities, observations) and Phase 12 (judgment).
- **C15.** *Resolved:* keep one year.
- **C16.** *Resolved:* for Brian's reference only.
- **Q-W5: the first presence signal.** "Is Brian at his desk?" would help timing a great deal. It could come from PC input activity, the webcam (A09) or the phone. Which comes first is a later decision.

---

## 13. Acceptance scenarios

- **W1. One path.** A Gmail item, a text and (later) a notification each land in the proactive store as one item each. No source triggers speech or memory by itself.
- **W2. Replay.** The phone resends a text after a reconnect. It is recognised as the same item, and nothing is told twice (P10 R2).
- **W2b. Update vs repeat.** A calendar event is rescheduled. The change is processed once, as a new revision of the same event. A repeated delivery of that same change produces no second announcement.
- **W5b. Explicit beats inferred.** Brian said "quiet". Inference says he seems idle at the desk. Quiet holds.
- **W12. Switching off.** Brian turns location off. Collection stops, queued points aren't processed and a pending "you'll be late" line is dropped. The kept history remains until it expires or he forgets it.
- **W3. Source down.** The phone link is down from 2 pm. At 4 pm Brian asks "anything from Micah?" and is told she couldn't check since 2. There is no false "no" (A05 T4).
- **W4. User state.** Brian is in a calendar meeting. Interruption tolerance is low, with the source (calendar) and age recorded. A minor item is held. A10 decides; A08 only informs.
- **W5. Stale state.** The user-state reading is older than its window. It is treated as unknown, and A10 assumes the costlier case.
- **W6. Unknown sender.** A text from an unknown number is ingested, ranked below contacts by code, and remains judgeable for importance. It is not excluded.
- **W7. Mood is not a fact.** Zola's estimate that Brian sounds stressed shapes her timing today. It is never saved as "Brian is stressed" and never mentioned unprompted.
- **W9. Where was I (ARCH-23).** Brian asks "when did I leave the shop Tuesday?" With a sampling gap, she says "You were last recorded at the shop at 4:35, and away by 4:45." She gives no invented exact departure time.
- **W9b. Forget a day.** "Forget where I was Saturday" removes Saturday's points, the visits derived from them and any summary mentioning them.
- **W10. Location is for Brian only (C16).** Bre asks Zola "where's Brian?" and Zola doesn't say; the family uses Life360. A guest gets the same answer.
- **W11. One-year expiry (C15).** Location points older than a year are gone, and "where was I last October?" gets "I don't keep location that far back."
- **W8. Code masked.** A text with a verification code arrives. The code is masked on the phone. Brian asks "what's the code?" and it is read through the R1 direct path only.

- **W13. A burst.** The drive camera floods intake with motion events during a storm. Brian's question is answered without delay. Nothing fills the disk. When the backlog clears, the old events aren't raised as new. If some were shed, she says the drive's coverage has a gap for that hour.

---

## 14. Coverage of the source docs

*Status:*
- **verified** — the destination exists and was checked against a fresh full read on 2026-10-29.
- **verified (notes)** — checked against the full-read notes.
- **planned** — the destination doc is not yet written.

| Source section | Destination | Treatment | Status |
|---|---|---|---|
| Env Awareness: vision; "awareness is not interruption"; silence valid | §1 | preserved | verified |
| Pipeline; non-negotiable rule; required separation (signal → perception → interpretation → awareness → attention → action) | §2 p2–p3; A10 §3 | merged | verified |
| §1 signal sources | §3 | preserved and split into today / vision | verified |
| §2 location (context, not tracking) | §3.2, §6.1, §7 | **superseded by ARCH-23** (coordinates and history kept, by Brian's choice) | verified |
| §3 temporal awareness | A05; §6 | merged | verified |
| §4 calendar awareness | §3.1, §5 | preserved; "never read calendar content aloud without permission" superseded by ARCH-11 / A14 | verified |
| §5 weather, §6 traffic and driving rules | §3.2, §6 | preserved | verified |
| §7 device state | §3, §5 | preserved | verified |
| §8 notification and communication awareness, privacy rules | §3.1, §9; A14 P9 | merged; "never read content aloud" superseded by ARCH-11 | verified |
| §9 home, shop and workspace | §3.2, §6 | preserved | verified |
| §10 security and camera | A09 §3, §10 | moved | verified |
| §11 structured events (schema) | §4 | merged into the item model; privacy ladder replaced by A14 | verified |
| §12 interpretation, §13 fusion | A10 §3 | moved | verified |
| §14 user state | §5 | merged with the Event Bus §4 | verified |
| §15 scoring, §16 dampening, §17 dispositions | A10 | moved | verified |
| §18 environmental memory | A03, A09 | moved | verified (A09 §5.2 checked) |
| §19 cross-domain correlation | A10 §8 | moved | verified |
| §20 privacy and trust boundaries | §7; A14 | merged | verified (A14 checked) |
| §21 shared-space behaviour | A06 §7.1; A14 | merged; "never read messages aloud" superseded (ARCH-11) | verified |
| §22 awareness and autonomy; §23 workers; §24 authority boundaries | §2 | preserved | verified |
| §25 confidence and uncertainty | §2 p6, §4 | preserved | verified |
| §26 anti-noise | §8 | preserved | verified |
| §27 awareness modes | §6 | preserved as contexts feeding A10 | verified |
| §28 endpoint-aware behaviour | A12 §7, §8 | moved | verified |
| Principles, failure modes, observability, open questions, end state (Env Awareness) | §1, §2, §11–§12 | merged | verified (notes for end sections) |
| Event Bus: philosophy (signal ≠ event ≠ insight) | §1, §2; A10 §3 | preserved | verified (fresh read 2026-11-02) |
| Event Bus §1 schema, required and optional fields, integrity rules | §4 | merged; numbers unvalidated | verified |
| Event Bus §2 bus, lanes, what may emit, lifecycle | §2 p2, §4 | preserved; Windows store is the path | verified |
| Event Bus §2 validation, audit, backpressure; Env Perception §15 delivery failures; Event Bus flood and coalescing | §4 "When intake can't keep up"; A09 §4 | retained (audit C07); queue technology and retry counts left to build plans | verified (fresh read 2026-11-02) |
| Event Bus known-place misidentification | §6.2 | retained | verified (fresh read 2026-11-02) |
| Event Bus §3 interpretation | A10 §3; A09 §4 (false positives, coalescing) | moved; "tier 1 needs high confidence from multiple signals" superseded by ARCH-63 (independent corroboration raises confidence; uncertain-serious is raised worded as uncertain) | verified (fresh read 2026-11-02) |
| Event Bus §4 user-state fields | §5 | merged | verified |
| Event Bus §5 update architecture, conflict rules | §5 | preserved; Android refresh rates dropped | verified |
| Event Bus §6 known places | §6 | preserved as entities | verified |
| Event Bus §7 calendar reader | §5 | merged | verified |
| Event Bus §8 audio monitor | §7 | preserved; "never identify speakers" superseded by ARCH-07/12 | verified |
| Event Bus principles (bus is the only path, interpretation before routing, estimate, staleness, heat ≠ state, privacy by default) | §2 | preserved; heat-derived tolerance contradiction resolved | verified |
| Communication Intelligence (Android as built) | §9; A11 §5.1 | design reference; the brief kept as deferred (ARCH-65); per-channel consent and "analysis is not storage" retained | verified (fresh read 2026-11-02) |
| SMS Intelligence | §9 (consent explained, thread speed); A11 §5.1; A15 §5 (send) | known-contacts gate, weights and two-step confirm superseded; examples kept | verified (fresh read 2026-11-02) |
| Agent Map agents 1, 6, 12 | §5 (one estimate), §9; A10 §9.1 (agent 1) | merged | verified (fresh read 2026-11-02) |
