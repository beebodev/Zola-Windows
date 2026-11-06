# Architecture Docs Rewrite — Brian's Decisions

*Paths beginning `claude/` refer to the claude.ai project "Zola-Windows", where the rewrite was drafted. In the repo, the 16 docs and this log live in `zola-architecture/`, and the coverage records in `zola-architecture/audit/arch-docs-swap/`.*

*Started 2026-10-29. This file records Brian's verdicts on `claude/ARCH_DOCS_MERGE_MATRIX.md` (v1.2). Brian's own words are quoted where it matters. "Claude's reading" marks an interpretation, and it is labelled where Brian has not confirmed it. These are decisions about the architecture docs only: they do not authorise implementation, and the repo is unchanged.*


## ID map (AD → ARCH, renamed 2026-10-29, ARCH-20)

Earlier reviews and chats cite the old **AD-xx** numbers. The number stays the same; only the prefix changes. Phase 12's own direction items are written **P12-AD-01** to **P12-AD-04** to keep them distinct.

| Old | New | Subject |
|---|---|---|
| AD-01 | ARCH-01 | Doc structure approved |
| AD-02 | ARCH-02 | Zola grows in her own world |
| AD-03 | ARCH-03 | Household: presence for each person, privacy, requests, shared calendar, guests |
| AD-04 | ARCH-04 | Sensitive topics: brief opening, then confirm |
| AD-05 | ARCH-05 | Keeps what she observes; facts, never recordings |
| AD-06 | ARCH-06 | Learns from observed sources |
| AD-07 | ARCH-07 | Learns voices and faces; recognition is not permission |
| AD-08 | ARCH-08 | New skills and tools need approval |
| AD-09 | ARCH-09 | One final decision point for unprompted output |
| AD-10 | ARCH-10 | No assumption license |
| AD-11 | ARCH-11 | Message content spoken only to a known-private audience |
| AD-12 | ARCH-12 | Unverified speaker is a guest |
| AD-13 | ARCH-13 | Who may hear information (amended: subject's own affairs) |
| AD-14 | ARCH-14 | Siblings derived at read time |
| AD-15 | ARCH-15 | Stated commitments become watched (C12, C13) |
| AD-16 | ARCH-16 | One conversation across devices |
| AD-17 | ARCH-17 | Someone joins: fresh shared session; re-raised topic exception |
| — | ARCH-18 | Heat per person |
| — | ARCH-19 | Per-person proactivity and preferences |
| — | ARCH-20 | This rename |
| — | ARCH-21 | Spoken ask only, no on-screen cue |
| — | ARCH-22 | Interjections wait for a natural pause |
| — | ARCH-23 | Location from the phone, coordinates and history, Brian only |
| — | ARCH-24 | The companion app: voice and typed, away from the PC, full avatar |
| — | ARCH-25 | PC unreachable: refuse spoken turns, hold typed ones |
| — | ARCH-26 | Raising things on the phone: a notification, then she proceeds once opened |
| — | ARCH-27 | Approvals on the phone are spoken only |
| — | ARCH-28 | Who is holding the phone: camera or voice recognition |
| — | ARCH-29 | Shop and car devices are Android companions, same as the phone |
| — | ARCH-30 | Overheard speech discarded unless she is part of the conversation (amends ARCH-13) |
| — | ARCH-31 | The goal: talk to her naturally without routinely using the wake word |
| — | ARCH-32 | Work is a context, not a room |
| — | ARCH-33 | Sensitive topics; credentials a separate category |
| — | ARCH-34 | Serious conversations: stronger privacy, not a ban |
| — | ARCH-35 | B14 closed: family is never permission; no trusted list |
| — | ARCH-36 | A14 smaller items: visitors, "don't use it", sharing approvals, codes voice, location encryption timing |
| — | ARCH-37 | Visitor signatures two weeks; any household member can add to the sensitive list |
| — | ARCH-38 | Guests may use a shortlist of harmless lookups |
| — | ARCH-39 | Never pre-authorised list; safety restrictions always confirmed |
| — | ARCH-40 | Stakes ladder and low-stakes definition, for now |
| — | ARCH-41 | Calendar write access is wanted |
| — | ARCH-42 | Family calendar by effect: invitations and outside notifications are consequential |
| — | ARCH-43 | Skill edits judged by effect; installing is not permission to use (amends ARCH-08) |
| — | ARCH-44 | Single-user risks reviewed before household operation |
| — | ARCH-45 | "Disciplined about interrupting" replaces "restrained" (B13 closed) |
| — | ARCH-46 | Her own growth, inheriting privacy |
| — | ARCH-47 | Honest disagreement and knowing her authority are locked |
| — | ARCH-48 | Each person can inspect, correct or reset their own learned style |
| — | ARCH-49 | Identity review timing; stale SOUL lines at the doc swap |
| — | ARCH-50 | A separate relationship with each household member |
| — | ARCH-51 | Asked directly, she answers; the person can correct or reset her read |
| — | ARCH-52 | Relationship layer revisited after Phase 11 |
| — | ARCH-53 | Relationship reads start from what's said; tone later, weak only |
| — | ARCH-54 | Head and hair motion wanted; "no head motion" was a temporary limit (B12 closed) |
| — | ARCH-55 | Head, gaze and hair behaviour; phone layout open until a mockup |
| — | ARCH-56 | Hologram effects dropped; waveform space released |
| — | ARCH-57 | Screen privacy: prevent and conceal |
| — | ARCH-58 | Alert only for urgent items A10 authorises now |
| — | ARCH-59 | First perception: PC webcam presence; phone camera only while the app is in use |
| — | ARCH-60 | Reading faces follows ARCH-53 |
| — | ARCH-61 | Licence plates deferred |
| — | ARCH-62 | Vision local first; cloud off, per stated purpose only |
| — | ARCH-63 | Confidence and urgency separate; each safety event its own rule |
| — | ARCH-64 | Privacy acts at once; the webcam is partial evidence |
| — | ARCH-65 | Daily brief kept as a deferred feature |
| — | ARCH-66 | Four distinct turn-off actions |
| — | ARCH-67 | Starting a conversation without the wake word is a per-person permission |
| — | ARCH-68 | Coverage map v1.1 signed off; repo swap authorised |

## ARCH-01 — The doc structure is approved (2026-10-29)
The 16 target docs are approved as proposed in matrix v1.2 §2: A01–A15, plus A02b (Relationship with Brian) as its own doc.

## ARCH-02 — Guiding principle: Zola grows in her own world (2026-10-29)
Brian: *"I don't want her to be a reflection of me, but of herself growing in the world."* She takes in her environment from many sources.
- Goes into A01 (principles) and A02 (identity).
- Basis for ARCH-05, ARCH-06 and ARCH-07.

## ARCH-03 — People in Brian's household (B3, C1, C6–C11; 2026-10-29)
**Who she is to each person.** Zola is *"a trusted presence for each person."*
- She eventually recognises household members (Bre and the boys) by voice and camera.
- She builds her own relationship with each of them.
- **Supersedes** the Privacy Plan rule barring non-consenting household members "in identifiable form". Household members are full entities in A03/A04.

**The same rules apply to everyone in the household (C9).** That includes Brian and the boys.

**Privacy runs every direction (C6).**
- She doesn't discuss one person's information with anyone else unless that person approves.
- This holds both ways between Brian and Bre: what Bre tells Zola isn't shared with Brian without Bre's approval, and the reverse.

**Exceptions (C9), limited to what is needed.**
1. **Unauthorised attempts.** She may tell the affected person that someone attempted something unauthorised (e.g. using Brian's accounts). She says only what was attempted, not the person's private information around it.
2. **Safety.** She may tell another household member if someone appears hurt or in danger. She gives only the safety concern.

**Acting on requests (C1, C7).**
- She acts on a household member's requests only for things that pertain to that person.
- Policy permits a verified household member's own low-stakes requests. Recognition only establishes who is speaking. (Wording clarified 2026-10-29.)
- Anything consequential needs that person's own approval method.
- Nothing another person asks can reach Brian's accounts.

**Shared household information (C8, C10, C11).**
- **What is shared:** today, only the **family calendar**. Anything else becomes shared only by Brian's explicit decision (confirmed 2026-10-29).
- **Who can use it:** any **household member** may update and discuss it. Guests may not.

**Guests (C10).**
- Guests may talk with Zola, but **no tools or scripts run** for a guest.
- Guests do not get household information. Disclosure follows the rules above.
- What a guest says is still kept as understood, attributed facts (ARCH-05).

**Where it lives.**
- A14: disclosure, the exceptions, per-person privacy, what is shared.
- A15: per-person action scope, approval methods, and the guest "no tools" rule.
- A02/A02b: Zola as a presence for each person.

## ARCH-04 — Sensitive topics and proactivity (B6, C2; 2026-10-29)
- She may bring up a sensitive topic herself, with a short opening and no details. Example: "Something came up about your appointment. Want to go over it?"
- She gives details only after the person confirms.
- If others may be present, she says at most the subject, or waits.
- **Supersedes** the rule "sacred facts are never proactive".

## ARCH-05 — Observations, others present, guests (B7, C3; 2026-10-29)
*"This is her world, so she can keep what she observes."* This covers household members and guests.
- She keeps **understood facts only, never recordings**: no raw audio or video of conversations, in any jurisdiction.
- What other people say is kept as their attributed statements.
- Provenance, forget and retention rules still apply, and disclosure follows ARCH-03.
- **Supersedes** the rule that memory writes stop while a third party is present.
- **Someone she doesn't recognise:** she may ask who they are if she is engaged in the conversation. Otherwise she notices them (ARCH-07) and takes no other action.

## ARCH-06 — Learning from observed sources (B8; 2026-10-29)
Yes. She learns about people from email, texts, Contacts and sensors, not only from what Brian tells her. This follows the per-source promotion rules and the self-reinforcement safeguards (matrix §3.2–3.3).

## ARCH-07 — Learning voices and faces (B5, C4; 2026-10-29)
She learns the voice and face of **anyone she sees**.

**Purposes:**
- her own recognition of people
- giving accurate information if someone attempts something unauthorised (exception 1 in ARCH-03)

**Accepted guardrail (wording clarified 2026-10-29):**
- Recognition only identifies who is probably speaking or present.
- Permission comes only from policy. Under ARCH-03, a verified household member may make low-stakes requests that pertain to them.
- Recognition never stands in for anyone's approval method.
- A15 defines "low stakes". It excludes anything that would expose another person's information.

**Recommended, not decided:**
- embeddings stay on Brian's own devices
- they can be viewed and deleted per person
- A14 sets how long people she never sees again are kept

## ARCH-08 — Self-changes needing approval (B15, C5; 2026-10-29)
**Need Brian's approval:**
- new skills
- new tools
- edits that let a skill run code or reach new things

**Do not need approval:** wording-only edits.

**Status:** decided policy, **not yet enforced**. Today's Hermes default lets skill writes through, and the P8 guards cover only config, SOUL, identity, plugins and memory code.

## ARCH-09 — B1: One final say on unprompted output (2026-10-29)
- One decision point, owned by A10 (Understanding Events and Judgment), decides whether to speak now, wait, or only log. This applies to everything Zola says or shows that Brian didn't ask for.
- It keeps one record of why she spoke or stayed quiet.
- Privacy (A14), endpoint/device (A12) and action (A15) checks feed into it and can each **block** it independently. They are not absorbed into it.
- **Resolves** the double claim between the Response Governor (Autonomous Behavior) and the Attention Engine. The Engagement Governor → Attention/Relevance ordered chain survives as the steps leading up to that one decision.
- Hermes's extra output paths (F10) are mapped before A10 claims it covers everything.

## ARCH-10 — B2: No "assumption license" (2026-10-29)
- Relationship depth never creates authority to act.
- Familiarity may only let her skip unnecessary *preference* questions inside an action that has already been authorised (e.g. "the usual reply style?").
- Acting without approval is a separate, deferred A15 decision.
- The assumption license is removed from A02b.

## ARCH-11 — B4: Speaking message content unprompted (2026-10-29)
- **Audience known to be private:** she may speak the content in her own words (e.g. "Micah texted — his car won't start at the school lot.").
- **Audience unknown:** restrained, saying only who it's from (e.g. "Micah texted you.").
- **Codes:** follow R1 exactly. She reads one aloud only on explicit request, and never into model, history, memory, logs or TTS caches.
- Household recognition (ARCH-07) is what eventually lets her know the audience. Desk presence alone does not prove a private audience.

## ARCH-12 — An unverified speaker is a guest (2026-10-29)
Brian: *"If she can't verify the speaker, then it should be considered a guest until verified."*
- Until a speaker is verified, ARCH-03's guest rules apply: conversation only, no tools or scripts, and no household or private information.
- A07 and A09 own verification and how sure she is. A15 applies the guest rule.
- This holds even when the voice or face resembles a household member's.

## ARCH-13 — Who may hear information (2026-10-29)
Brian approved Claude's proposal ("Sounds good. Let's make edits.").

**What is recorded.** Every piece of information records these separately:
- **speaker or source**
- **subject**
- **intended recipients**

Its **permitted audience** is derived from those three.

**Default audience:**
- the speaker
- the intended recipients
- the subject

**Anyone else** needs the speaker's approval. For a sensitive topic, the subject's approval is needed as well.

**Messages follow their recipients.** Micah's text to Brian may be told to Brian.

**What is said privately to Zola, or overheard**, is the speaker's information. *(Overheard: amended by ARCH-30. Only within conversations she is part of; otherwise discarded.)*

**Forget and use:**
- The speaker can make Zola forget their own statement.
- The subject can ask Zola not to use it. This suppresses use and disclosure. It does not erase the speaker's statement.

**Examples confirmed:**
- **Brian tells Zola "Bre has a doctor's appointment Tuesday".** Zola may mention it to Bre. She may not mention it to the boys without Brian's approval, plus Bre's, because the topic is health.
- **Bre tells Zola she is planning a surprise party.** Zola keeps it from Brian.
- ~~**Zola overhears Bre on the phone.** What she hears is treated as Bre's private information.~~ *Superseded by ARCH-30: she isn't part of the call, so it is discarded and never kept.*

**Amendment (2026-10-29, Brian: "Option B").** Being the subject of something does not by itself give someone access to another person's private conversation. As originally written, the default audience (which included the subject) contradicted the rule that private statements stay with the speaker. The amendment narrows the subject's default access to **plain facts about the subject's own affairs**.

What the subject may hear by default:
- their appointment
- their schedule
- their car
- their plans

What stays with the speaker:
- the speaker's views about the subject
- the speaker's observations about the subject
- the speaker's discussion of the subject

Examples:
- "Bre has a doctor's appointment Tuesday" may go to Bre.
- "Brian's been stressed lately", said privately by Bre, stays with Bre.

When Zola cannot tell which kind a statement is, she treats it as private to the speaker (fail closed).

This replaces Claude's earlier suggestion, which ChatGPT challenged: that both the speaker and the subject own the information and either can erase it everywhere.

## ARCH-14 — B9: Siblings are worked out when needed, not stored (2026-10-29)
Brian: *"I agree with your assessment on A04."*
- Sibling relationships are **derived at read time** from shared parents, not stored at write time.
- This reverses Android P19-D03 for Windows. That decision was an Android lock and never a Windows one.
- A sibling relationship is stored only when a person states it directly ("Dom and Micah are brothers").
- The general rule from vision §4 now applies without exception: stored relationships are the stated or established ones, and everything derived is worked out when needed.
- The P11 audit may still bring evidence against this, for example on performance. Any change would be a new decision.

## ARCH-15 — Stated commitments become watched commitments (2026-10-29)
Brian: *"I think she should remember it and add a watcher. She should check in and assist with remembering and verify that it was completed."*

**What happens.** When Brian states a commitment with a time, for example "I need to renew the registration by the 15th", Zola does three things:
- **Remembers it** in A03, as a remembered situation with its due date.
- **Creates a watch** linked to it in A11, with no separate offer step.
- **Checks in and helps:**
  - reminds ahead of the due date;
  - helps with the task;
  - verifies completion.

Check-ins are still unprompted output, governed by the A10 decision point: quiet hours, active conversations and interruption limits.

**How completion is verified.** Evidence can suggest a commitment is done, for example a confirmation email. Zola then asks Brian to confirm. She closes the watch on his confirmation, consistent with P9-D09 ("ask before a self-selected close"; "I never stop watching on my own").

**Relation to existing lore.**
- P9-D09 creates watches only on a ticket turn, from Brian's own words or from an offer he accepts. Brian stating a commitment in his own turn fits "Brian's words". The change is that no offer step is needed for stated commitments. It is recorded in lore as an annotation at the relevant phase, not as a silent edit.
- The SOUL line "I can offer once to watch for it" would need an approved SOUL change when this is built.

**C12 — What counts as a commitment.** Brian: *"I agree on both"*, 2026-10-29.

| What Brian says | What Zola does |
|---|---|
| A clear task with a time ("renew the registration by the 15th") | Remembers it and watches it automatically |
| Vague, with no time ("I should clean the garage sometime") | Remembers it only, no watch |
| In between ("I need to call the insurance guy this week") | Asks once whether to keep track of it |

**C13 — Deadlines found in observed sources.** Examples are an email from the DMV or a bill. Zola **offers** to track the deadline ("Want me to keep an eye on that?"). She never creates a watch from untrusted content on her own. Once Brian accepts, it is handled exactly like a commitment he stated himself.

## ARCH-16 — B11: One conversation across devices (2026-10-29)
Brian: *"The same conversation. All of Zola-Windows should be PC controlled, so we are continuing the same conversation with the same brain."*
- When Brian moves from the PC to the phone, or to any later endpoint, the **same Hermes session continues**.
- The PC is the single brain and session authority. Endpoints attach to that conversation; they never hold their own.
- The A06 §7 participant and handoff rules still apply on every device. For example, the phone in Bre's hand is not Brian's conversation.
- This **reverses** the Android Session Identity rule "a new device always starts a new session" (MD-D05). That rule was an Android lock, never a Windows one.

## ARCH-17 — Q-C1: Someone joins mid-conversation (2026-10-29)
Brian: *"option b unless the speaker brings up the subject again in mixed company. Then Zola can assume that it is okay to speak on it."*
- **Fresh shared session.** When someone joins a private conversation, Zola moves to a fresh shared session. The earlier private session stays with its owner and never enters the shared one.
- **Exception, re-raised subjects.** If the person whose private conversation it was **raises that subject again themselves** in the mixed company, Zola may speak on that subject there.

**C14, confirmed 2026-10-29.** Brian: *"That is correct. Just the particular topic that was brought up."* The exception covers the subject the speaker re-raised, and only that person's own information about it. It does not unlock:
- other topics from the earlier private conversation
- another person's private information that came up in it
- details the speaker didn't re-open, when the topic is sensitive

**Q-C3, agreed 2026-10-29.** When the joint conversation ends and the person is alone again, Zola resumes that person's own earlier session. She is informed by memory of the shared one. Under ARCH-13, the shared session's contents are available to everyone who was present.

## ARCH-18 — B10: Attention heat is per person (2026-10-29)
Brian: *"I agree on all 3."*

Heat is tracked per person, not per device. That keeps restraint with Brian when he moves from the PC to the phone, consistent with ARCH-16, which treats PC and phone as one conversation.

When one announcement is heard by several listeners, each listener's heat is charged. No listener's preferences change as a result.

## ARCH-19 — Q-J2: Per-person proactivity and preferences (2026-10-29)
Each household member has their own:
- proactivity level
- preferences
- feedback, such as "stop telling me about these"

Bre's settings never change Brian's, and Brian's never change hers.

## ARCH-20 — Decision IDs renamed (2026-10-29)
These architecture-doc decisions are renumbered from **AD-xx** to **ARCH-xx**. The reason is that `PHASE12_DECISIONS.md` already uses AD-01 to AD-04 for its own direction items, which are now written as **P12-AD-01** to **P12-AD-04**. The old-to-new map is at the top of this file.

## ARCH-21 — Getting attention: a spoken ask only, no on-screen cue (2026-10-29)
Brian: *"I don't think we need the on screen cue. Just the verbal ask."*

Zola gets someone's attention by asking aloud ("Got a second?") or, when it's time-critical or he's clearly listening, by telling him directly. There is no ambient on-screen "I have something" cue.

Items that would only have earned a quiet cue are held for later instead:
- the next natural moment
- a summary
- "what's pending"

The rare hard foreground for safety remains.

## ARCH-22 — Interjecting mid-conversation waits for a natural pause (2026-10-29)
Brian: *"She should wait for a natural pause unless time critical."*

When an eligible live event arrives while someone is talking with Zola, she waits for a natural pause before bringing it in. Only time-critical items may cut in.

## ARCH-23 — Location from the phone, with history (2026-10-29)
Brian: *"Yes. We should pull location from the phone."* / *"Actual coordinates. I want Zola to be able to know where I was and when."* / *"For now, just me."*

**What is decided:**
- Zola gets Brian's location from the phone companion. The PC keeps control, consistent with ARCH-16.
- She keeps **actual coordinates**, not only named places, so she can answer "where was I, and when?".
- This covers Brian only for now. Other household members are not included.

**What this supersedes:** the Android rule "location is context, not tracking… not a movement surveillance record". A location history is now an intended capability.

**What still applies:**
- Location stays local (P6-D07).
- It falls under forget (A03 §12).
- It is Brian's private information under ARCH-13.

**C15, retention (2026-10-29).** Brian: *"Let's say a year for now."* The location history is kept for **one year**, then expires by policy. Brian can forget any part of it sooner.

**C16, who may be told (2026-10-29).** Brian: *"No, this would be for my reference only. The family has access to life360 if they need to know where I am."* Zola's location record is **for Brian's own reference only**. She does not tell anyone else where Brian is or was, including household members. The family uses Life360 for that. The ARCH-03 safety exception passes on only the safety concern, never Brian's location.

## ARCH-24 — The companion app: how Zola is presented (2026-10-29, A12 Q-D1, Q-D2, Q-D4)
Brian: *"A12 is different than the original Android application. In this instant, it will depend on the companion app and how we present Zola within the app while actual Zola resides on the PC."*
- **Talking to her (Q-D1).** Brian: *"Both."* Voice (push-to-talk) and typed chat, both into the same PC conversation (ARCH-16). Which is built first is a build-plan choice; Claude suggested voice first.
- **When the app is used (Q-D2).** Brian: *"Only when away from the PC."* The app is Zola's presence when Brian is away from the PC. At the PC, the PC is her endpoint.
  - **Confirmed 2026-10-29.** Brian: *"Away from the PC means anywhere away from the office, so shop and other rooms apply."*
- **Her look (Q-D4).** Brian: *"Full avatar, but how it is presented yet I'm not sure."* The full avatar is the target on the phone. How it is laid out in the app stays open (A12 Q-D4, A13).

## ARCH-25 — When the PC can't be reached (2026-10-29, A12 Q-D3)
Brian: *"Agreed."* (to Claude's lean)
- The app never answers as Zola without the PC.
- **Spoken turns are refused.** The app says Zola can't be reached right now.
- **Typed turns are held.** They are clearly marked as not yet sent and go through once the PC is reachable, processed at most once.

## ARCH-26 — Raising things on the phone: a notification first (2026-10-29, A12 Q-D6)
Brian: *"I would go with a notification and once opened, she can proceed. Otherwise she stays silent."*
- When the phone is the right endpoint and Zola has something to raise, she sends a **phone notification**. When Brian opens it, she continues in the app as she would on the PC.
- If he doesn't open it, **she stays silent**. The item stays held for the next natural moment (A11).
- **Relation to ARCH-21.** ARCH-21 (a spoken ask only, no on-screen cue) still governs the PC. On the phone, the notification takes the place of the spoken "Got a second?". This is a phone-specific rule, not a change to ARCH-21.
- **Confirmed 2026-10-29:**
  - **No content.** Brian: *"No content besides 'Zola needs your attention' or something to that effect."*
  - **One notification for everything.** Brian: *"The notification should cover everything and be withdrawn if you deal with it at the pc."*
  - **She speaks when it's opened.** Brian: *"Speaking."* What she says aloud is still limited by who is using the phone (ARCH-28) and who can hear (A14).

## ARCH-27 — Approvals on the phone are spoken only (2026-10-29, A12 Q-D7)
Brian: *"Spoken only."* On the phone, an approval is Brian's spoken approval in his own turn. This rule is scoped to the phone; the PC's existing approval rules are unchanged (A15). A tap on a screen is not an approval. A typed message is not an approval either.

## ARCH-28 — Who is holding the phone (2026-10-29, A12 Q-D5)
Brian: *"Camera or voice recognition once implemented."*
- Zola treats a phone turn as Brian's once **camera (face) or voice recognition** establishes it. Those are not built yet (A07, A09).
- A paired, unlocked phone by itself does not establish that the person using it is Brian.
- **Until recognition exists:** sensitive content and approvals are not offered on the phone. The speaker is treated under ARCH-12 (unverified = guest). Recognition still grants no permission by itself (ARCH-07).
- **Where recognition runs is open.** It could run on the PC or partly on the phone. Either way, the PC makes the final decision on who is speaking. *(Claude's earlier reading, that a phone-side model would be a second authority, is withdrawn after review: processing on a device is not authority.)*

**Interim, option b (2026-10-29).** Brian: *"I would go with option b."* Until recognition exists, Brian's own paired, unlocked phone counts as Brian for **his own everyday items**: for example, who texted and the gist.
- Still waiting for recognition: sensitive items, other people's private information, and all approvals.
- **Accepted risk:** someone else holding the unlocked phone could hear Brian's everyday items.
- This is a temporary limit and ends when recognition is built.
- **Opening Zola's notification (ARCH-26) gets her attention only.** It releases no content and approves nothing. Before speaking any content she checks who is using the phone and who can hear.

## ARCH-29 — Shop and car devices are Android companions (2026-10-29, A12 Q-D8)
Brian: *"Future shop or car devices should be android devices that perform same as the phone."*
- Shop and car devices run the companion app and follow every A12 rule, as the phone does.
- They have **no local authority** (answers Distributed Presence §5).
- Each is its own endpoint with its own device id.
- *Claude's notes, unconfirmed:*
  - The driving limits come from Brian's user state (A08), so they apply on any device while he drives.
  - Whether a mounted device also takes over phone sources (texts, location) is settled when one is built. Claude assumes it only presents Zola.

## ARCH-30 — Overheard speech is discarded unless she is part of the conversation (2026-10-29, A07 Q-V1; amends ARCH-13)
**Re-decided 2026-10-29.** Brian: *"I think it is safer to go with overheard speech is discarded unless she is actively part of the conversation. If not, then it really becomes eavesdropping I guess."*

**Why re-decided.** Brian's first answer (*"I agree. A for now."*) was given on Claude's framing, which wrongly said the overheard case had never been asked. ARCH-13 had covered it ("Zola overhears Bre on the phone": treated as Bre's private information). ChatGPT caught the error. Brian decided again with the correct picture and chose to change ARCH-13.

**What is decided:**
- **She is part of the conversation:** ARCH-05 governs. She keeps understood facts, attributed, never recordings, including what others say to each other within it. Disclosure follows ARCH-13.
- **She is not part of it:** the speech is processed locally only to judge whether it was meant for her. It is then discarded at once: no conversation, memory, background reasoning, approvals or tools. Logs keep metadata only, never the words.
- **Speech not meant for her never triggers a reply, tool, approval or send.**

**Amends ARCH-13.** The confirmed example "Zola overhears Bre on the phone" no longer applies: she keeps nothing from it. ARCH-13's rule "what is said privately to Zola, or overheard, is the speaker's information" now covers overheard speech only within conversations she is part of.

**When she counts as part of a conversation** (Claude's proposal; Brian: *"agreed"*, 2026-10-29):
- She has been addressed in it, or is answering or asking in it.
- Someone who joins while she is already talking with Brian is part of it too (ARCH-17).
- It ends when the follow-up window closes and nobody present is talking with her. An earlier conversation doesn't make a later, separate one hers.
- A phone call is never hers unless she's put on it.

Learning from overheard speech where Brian switches it on remains only a possible later direction, needing its own decision.

## ARCH-31 — The goal: talk to her without routinely using the wake word (2026-10-29, A07 Q-V9)
Claude's reading of Brian's goal, after ChatGPT's review; Brian: *"agreed"*.
- Brian can talk to Zola naturally without routinely saying "Hey Zola". She tells that apart from him talking to someone else. "Walk into the shop and just ask" is the target experience, not an optional extra.
- **Still open:** how and when it is rolled out (VD-2), meaning which rooms, with others present, with the radio on. The mechanism belongs to the speech track.
- The wake word stays as a reliable override.

## ARCH-32 — Work is a context, not a room (2026-10-29, A14 Q-P6)
Brian: *"Gpt is correct on 3."* This confirms ChatGPT's description: Brian works from home, and his work involves customer cases, internal company information, employee reviews and HR discussions.
- Work and personal information are separated by **subject and audience**, not by location.
- **Work information** (customer cases, internal company information, employee reviews, HR) stays out of family and shop conversations.
- **Personal information** stays out of work-facing replies.
- **Brian's own planning may combine them** without exposing details. "You have a work call at three" is fine; the customer details aren't, in front of others.

## ARCH-33 — Sensitive topics; credentials are separate (2026-10-29, A14 Q-P2)
Brian: *"Yes to all."* (Claude's proposal, refined by ChatGPT's review.)
- **Sensitive topics:** health and medical (including mental health); money trouble; legal matters; relationship conflict; grief and loss; abuse and trauma; addiction and recovery; workplace HR matters; intimate or sexual matters; location history.
- Sensitivity is judged by what's actually said, not the subject heading. A routine purchase isn't money trouble.
- Anyone can mark their own information private or sensitive. "Keep that between us" mainly restricts who may hear it (ARCH-13).
- **Credentials are a separate category:** passwords, PINs, codes, security answers. Never discussed after a "yes". Codes follow R1; passwords and security answers are never stored or spoken.
- Handling of sensitive topics follows ARCH-04 (brief opening, then confirm). Sensitive facts are never used casually.

## ARCH-34 — Serious conversations: stronger privacy, not a ban (2026-10-29, A14 Q-P7)
Brian: *"Yes to all."*
- What's said in a clearly serious, private conversation gets that person's tightest audience.
- If the same person returns to the topic privately, she follows naturally without asking again.
- Unprompted follow-ups use the ARCH-04 opening.
- Unrelated facts mentioned in passing don't become permanently restricted.
- A reminder or watch the person asked for stays active.
- Detection must not be keyword-only. Vision; not built.

## ARCH-35 — Matrix B14 closed (2026-10-29, A14 Q-P1)
Brian: *"Yes to all."* B14 is resolved by ARCH-03 and ARCH-13 (as amended). Being family never grants access by itself, and there is no trusted-contact list. Nothing is household-shared except what Brian decides (today, the family calendar). Sharing approvals and enforcement still need design (ARCH-36).

## ARCH-36 — A14 smaller items (2026-10-29)
Brian: *"Yes to all."*
- **Visitors (Q-P4).** A one-time visitor's voice or face signature has a limited retention period, separate from people deliberately known. The period is still to set.
- **"Don't use it" (Q-P3).** An enforced restriction that also blocks derived uses. The speaker isn't notified automatically.
- **Sharing approvals (Q-P5).** By default an approval covers one item or topic for a named audience. Standing grants are explicit and revocable.
- **Codes (Q-P8, R1).** A local voice speaks codes, so a code never goes to the cloud voice.
- **Location at rest (Q-P9, H4).** Decided when location history is built, with the actual threat and access model in front of Brian.

## ARCH-37 — Visitor signatures and the sensitive list (2026-10-29, A14 Q-P4, Q-P10)
Brian: *"A visitor signature can last 2 weeks. Any household member can add to the sensitive list."*
- A one-time visitor's voice or face signature is kept **two weeks**, then deleted. People deliberately known are unaffected.
- **Any household member** may add a topic to the sensitive list. Adding only tightens how everyone's information is treated.
- *Not yet decided:* how a topic is removed from the list again.

## ARCH-38 — Guests: a shortlist of harmless lookups (2026-10-29, A15 Q-A10)
Brian: *"We can have a shortlist of harmless lookups."*
- Amends X5 (guests: conversation only). A guest may use a short list of lookups that touch nobody's data, such as the weather, the time or a timer.
- *To define:* the list itself. Anything not on it stays conversation only.

## ARCH-39 — Never pre-authorised; safety restrictions confirmed (2026-10-29, A15 Q-A8)
Brian: *"Agreed."*
- **Never pre-authorised** without a new architecture review: actions with significant cost or that can't be undone; broad system configuration changes; communications sent to third parties on someone's behalf; any action of a kind the person hasn't approved before in a similar context.
- **Safety restrictions are always confirmed.** When an action applies a safety restriction (an allergy, a health avoidance), she confirms that it was applied. **Refined 2026-10-29** (ChatGPT's review; Brian agreed to the corrections): confirmed to the person who asked, through a channel the privacy rules allow, and confirming the result, not just the request.

## ARCH-40 — Stakes ladder and low-stakes definition, for now (2026-10-29, A15 Q-A7)
Brian: *"Confirm for now."* The A15 §4 ladder (talk, read, prepare, low-stakes own scope, consequential, changes to Zola) and the low-stakes definition are confirmed as the current rule, open to revision.

## ARCH-41 — Calendar write access is wanted (2026-10-29, A15 Q-A3)
Brian: *"I thought we had write access for the calendar. If not, we do want that."*
- **Fact:** there are no calendar writes today. The Google consent is `calendar.readonly` (P8-D03), and calendar writes were deferred on purpose (P8 scope; ROADMAP S60–S64).
- **Decided:** calendar write access is wanted. It needs a new Google consent (a calendar write scope), its own scoping, and a phase to build it. It is **not** added to Phase 10.

## ARCH-42 — Family calendar, judged by effect (2026-10-29, A15)
Brian: *"Agree."* (Claude's proposal after ChatGPT's review.)
- Adding or changing a family-calendar event that notifies no one outside the house is **low-stakes**.
- Any household member may change any family-calendar event; it's shared.
- Anything that sends an invitation or notifies someone outside the household is **consequential** (it contacts someone) and needs that person's approval method.
- Applies once calendar writes exist (ARCH-41).

## ARCH-43 — Skill edits judged by effect; installing is not permission to use (2026-10-29, amends ARCH-08)
Brian: *"Agree."*
- An edit skips Brian's approval only if it leaves **behaviour, access and authority unchanged**. A text-only edit that changes when a skill uses a tool, or what it sends elsewhere, needs approval like code.
- Approving a new tool doesn't approve everything it can do. Each use still follows the normal rules.
- Narrows ARCH-08's "wording-only edits don't need approval".

## ARCH-44 — Review single-user risks before household operation (2026-10-29)
Brian: *"Agree."*
Before household operation is switched on, these accepted risks are reviewed, not only before public distribution:
- ungated skill writes and background review's combined authority (A8, A5, H5);
- BitLocker-only protection at rest (H2, H4, C4);
- Hermes's unarbitrated extra speech paths (A2);
- plugins and MCP servers inheriting stored secrets (H6);
- scheduled work's authority (S7);
- every client turn being assumed to be Brian's.

## ARCH-45 — "Disciplined about interrupting" (2026-11-02, A02 Q-I1; closes matrix B13)
Brian agreed with ChatGPT's recommendation (*"I agree with its answers to your questions."*).
The locked trait "restrained" is reworded **"disciplined about interrupting"**. Her attention costs the person something, so she raises things when they're worth it and at a good moment. It is not passivity: she takes initiative, notices and brings things up.

## ARCH-46 — Her own growth, inheriting privacy (2026-11-02, A02 Q-I2)
Brian agreed with ChatGPT's recommendation.
- Her own **interests, perspective, opinions and humour** may grow from her experience (ARCH-02). She distinguishes what she observed or investigated from someone else's account, and revises her view when evidence changes.
- **Privacy is inherited.** Discarded overheard speech contributes nothing (ARCH-30). A view derived from a private conversation keeps that source's restrictions; calling it "Zola's view" never strips them. Forget and "don't use it" reach derived views.
- Ordinary growth and learned delivery need **no further approval**. Changes to SOUL, capabilities, permissions or governing rules follow their own approval processes.

## ARCH-47 — Two more locked traits (2026-11-02, A02 Q-I3)
Brian agreed with ChatGPT's recommendation. **Honest disagreement** (she says when a plan has a problem and why, then respects the decision unless it crosses a boundary) and **knowing her authority** (initiative is not permission) are locked identity traits.

## ARCH-48 — Seeing and resetting learned style (2026-11-02, A02 Q-I4)
Brian agreed with ChatGPT's recommendation.
- Each person can **inspect, correct or reset** their own learned style. Nobody sees anyone else's.
- Every learned preference records whose it is, its context, whether stated or inferred, its evidence and confidence.
- Drift corrections are **visible on request**.

## ARCH-49 — Identity review timing; stale SOUL lines (2026-11-02, A02 Q-I5, Q-I6)
Brian agreed with ChatGPT's recommendation.
- Baseline review frequency is set at implementation. A review also runs after any meaningful identity (SOUL) or model change.
- The stale SOUL ("text-based Windows client") and VOICE_CONFIG (Sonia/Edge) lines are fixed **at the doc swap**, through the P4-D25 approval process.

## ARCH-50 — A separate relationship with each household member (2026-11-02, A02b Q-R1)
Brian: *"go"* (adopting ChatGPT's recommendations and Claude's revision).
- The relationship model applies to each household member separately, consistent with ARCH-03.
- One person's private history with Zola never shapes how she talks to another. Explicitly shared information isn't off-limits.
- **Also adopted with this decision:** the Android friction-state model and two-step recovery are dropped. How she talks follows the moment; whether something has changed between them is a separate, rare question needing strong evidence. Corrections never count against the relationship. Familiarity limits presumed intimacy, not the use of permitted memory. Relationship context is built only from information permitted for that person and purpose.

## ARCH-51 — Talking about the relationship (2026-11-02, A02b Q-R2)
Brian: *"go"*.
- She doesn't volunteer relationship reports or internal labels.
- Asked directly, she answers naturally, as her own read.
- The person can correct or reset her read; their explanation replaces her guess **immediately**.

## ARCH-52 — When to build the relationship layer (2026-11-02, A02b Q-R3)
Brian: *"go"*. Revisit S2 and S3 after Phase 11 lays the foundations. Calibrating how she responds can be considered separately from proactive relationship observations, which also need A10 and A11's delivery controls.

## ARCH-53 — What relationship reads are based on (2026-11-02, A02b Q-R4)
Brian: *"go"*. Start with what's said and explicit feedback. Tone of voice and pace may later be weak, temporary supporting hints once qualified. On their own they never create a lasting "strained relationship" judgment.

## ARCH-54 — Head and hair motion (2026-11-02, matrix B12)
Brian: *"We are in the process of reworking the Avatar for head movement and hair movement as well."* Consistent with his avatar-track decision of 2026-10-08 (head motion: *"Yes, plan for it."*).
- P3-D22's "no head motion" was a **temporary limit** of the old model, not a boundary. B12 closed.
- Head motion and hair motion (mainly the hanging ends) are wanted, arriving with the avatar v2 integration phase.
- Breathing stays out (P3-D22, Brian: *"Not necessary for AI to breathe."*).

## ARCH-55 — Head, gaze and hair behaviour; phone layout (2026-11-02, A13 Q-U1, Q-U2)
Brian: *"go"* (adopting ChatGPT's recommendations).
- Subtle head movement, idle gaze, and hair following her motion are the target for the avatar v2 integration.
- When addressed, she makes a slight engaged movement **towards the viewer**. Without a qualified position source she never appears to track someone around the room, with head or gaze.
- The phone layout stays open until there's a mockup. The leaning is the full avatar for voice and a smaller presence for typed chat.

## ARCH-56 — Hologram effects dropped; waveform space released (2026-11-02, A13 Q-U3, Q-U6)
Brian: *"go"*.
- Hologram and projection effects (scanlines, edge dissolve, noise shimmer; S24) are dropped from the intended design. Her look carries the entity feel. They can be revisited deliberately later.
- The waveform space reserved in the HUD (S27, P3-D07) is released; added later only for a real purpose.

## ARCH-57 — Screen privacy: prevent and conceal (2026-11-02, A13 Q-U4)
Brian: *"go"*.
- When the audience changes or may have changed, newly disallowed content doesn't appear, and protected content **already visible** is hidden at once.
- Covers conversation history, streaming text, memory panels, approval details and notifications.
- Recognition alone doesn't establish who can see the screen. The detection mechanism is open (A09).

## ARCH-58 — Alert state (2026-11-02, A13 Q-U5)
Brian: *"go"*. Alert is used only for an urgent item A10 has authorised her to present now. A waiting item never changes her expression; that would be a silent attention cue, against ARCH-21.

## ARCH-59 — What perception comes first (2026-11-02, A09 Q-P1, Q-P2 in part)
Brian: *"go"* (adopting ChatGPT's answers).
- **PC webcam presence first**: at the desk or away, how many people are in view. Coverage claims stay conservative (ARCH-64).
- **Phone camera only while the app is in use**, for the recognition purpose Brian approves (ARCH-28).
- **Next candidates:** shop presence, bay-door state and tool activity.
- *Not yet decided:* which cameras or devices Brian has or would add (Q-P2).

## ARCH-60 — Reading faces follows ARCH-53 (2026-11-02, A09 Q-P3)
Brian: *"go"*. Not at first. Later, at most a weak, temporary hint to shape her own delivery: never stored, never stated as fact, never a lasting judgment.

## ARCH-61 — Licence plates deferred (2026-11-02, A09 Q-P4)
Brian: *"go"*. Deferred until there's a concrete use that recognising a car by its appearance can't handle. Known vehicles are recognised by confirmed appearance.

## ARCH-62 — Vision is local first; cloud only per stated purpose (2026-11-02, A09 Q-P5)
Brian: *"go"*.
- Perception and recognition run locally.
- Cloud vision is off by default. Brian can enable it for a stated purpose with a defined input scope.
- It never covers biometrics, and enabling it never overrides the biometric rules or another person's privacy.

## ARCH-63 — Confidence and urgency are separate; each safety event gets its own rule (2026-11-02, A09 Q-P6 in part; supersedes Android Perceptual Input P5)
Brian: *"go"*.
- "High confidence before high urgency" is dropped as a rule. A10 weighs the evidence, the possible consequence and the cost of waiting.
- An uncertain but serious item may be raised promptly, worded as uncertain ("I may be hearing a smoke alarm. Can you check?").
- A possible smoke or CO alarm, an open door and an unknown visitor don't share one threshold. The endpoint and privacy rules still apply.
- *Not yet decided:* which safety events Brian wants, and how she reaches him for each (Q-P6).

## ARCH-64 — Privacy acts at once; the webcam is partial evidence (2026-11-02, A09 review)
Brian: *"go"* (adopting ChatGPT's corrections).
- Privacy restrictions driven by perception (an audience change) are enforced by A14/A13 immediately and never wait for A10. A10 decides only whether she says anything.
- A camera can show someone **is** present, never that nobody else is. Seeing no one else never loosens privacy. A recognised car supports "the car arrived", not "the person is home".

## ARCH-65 — Daily brief kept as a deferred feature (2026-11-02, coverage audit C01)
Brian: *"go"* (adopting ChatGPT's answer).
- Kept in the vision as a deferred feature, distinct from catching up on held items (A11).
- **On demand:** "Give me today's brief" works even when nothing is waiting.
- **Optional morning overview.** Each person chooses their sources and whether morning delivery is on.
- It still follows the normal privacy and interruption rules (A10, A14).

## ARCH-66 — Four distinct turn-off actions (2026-11-02, coverage audit C08)
Brian: *"go"* (adopting ChatGPT's wording).
- **Stop collection:** new fetching and source-dependent queued processing stop immediately. Already-learned information stays under its existing privacy and retention rules.
- **Disconnect an account:** the same, plus access credentials are revoked or removed. Operational caches are cleared, and anything claiming to represent the account's **current** state is invalidated. Historical knowledge is kept unless deletion is also requested.
- **Delete collected information:** the selected information and what was derived from it are erased through the normal forget process, with any exclusions explained.
- **Withdraw one use:** that use stops immediately, including queued work and prepared output. Other permitted uses of the source continue ("don't use texts in my brief" leaves other text functions available).
- An explicitly requested reminder doesn't disappear because the account its deadline came from was disconnected.
- Retained information never passes for a fresh check ("as of when I last had access…").
- Disconnecting doesn't mean forgetting. Deletion is offered as a clear, separate choice.
- Reconnecting keeps any use restrictions set earlier. No consent through repeated asking.

## ARCH-67 — Starting a conversation without the wake word is a per-person permission (2026-11-02, coverage re-audit R04)
Brian: *"I agree."* (Claude's proposal.)
- Anyone can start a conversation with the wake word. A guest then gets guest rules: conversation plus the harmless-lookup shortlist (ARCH-38).
- Starting a conversation **without** the wake word (ARCH-31) is granted per person. Brian has it by default; Bre or the boys only when Brian grants it.
- A visitor's voice never gets it, however often she has heard them.
- Recognising someone, letting them start a conversation, judging whether speech is meant for her, and permitting an action stay four separate decisions (A07 §4.5).
- Supersedes the Android "Gatekeeper background activation" grant (Living Voiceprint §12).

## ARCH-68 — Coverage map signed off; repo swap authorised (2026-11-02)
Brian: *"Let's prompt it"*, after the coverage map v1.1 recommended the 39 originals as ready for deletion in the repo-swap track.
- The 16 docs, this decisions log, the coverage map and the heading inventory go into the repo through one Cursor track (`ARCH-SWAP`).
- The 39 Android-derived copies are deleted in that track. The originals remain in the Android repo.
- Historical lore, closeouts and audits are not rewritten; they get successor pointers. Active references are updated.
- The stale SOUL and VOICE_CONFIG lines are fixed in that track only through P4-D25: exact text proposed, applied on Brian's approval.

## Not yet decided
None from matrix §5: B12 closed by ARCH-54, B13 by ARCH-45, B14 by ARCH-35.

## Open clarifications
- A09 Q-P2: which cameras or smart devices Brian has or would add.
- A09 Q-P6: which safety events she alerts on, and how she reaches him for each.
- ARCH-29: whether a mounted shop or car device also takes over phone sources, or only presents Zola.
