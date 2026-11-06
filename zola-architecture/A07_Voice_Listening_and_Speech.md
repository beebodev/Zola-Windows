# A07 — Voice, Listening and Speech

*Draft v0.4, 2026-10-29 (ARCH-30 re-decided, amends ARCH-13; ARCH-31; ChatGPT review). Author: Claude. **Status: approved for the repo by Brian, 2026-11-02 (ARCH-68). States intent; authorises no implementation.***

*v0.5, 2026-11-02 — reconciliation pass after the coverage audit: voice-learning safeguards (audit C06); visitor expiry (ARCH-37); scenario V16.*

*Re-audit corrections, 2026-11-02: who may start without the wake word (ARCH-67); VD-5 narrowed; V17.*

*Coverage-map pass, 2026-11-02: coverage rows closed with exact sections; additions from fresh reads of the source docs (see `audit/arch-docs-swap/ARCH_DOCS_COVERAGE_MAP.md` §5).*

*Phase 10 closeout pass, 2026-11-06: as-built rows and Phase 10 citations rechecked against the Phase 10 lore closeout (tag `p10-closed`) in ARCH-SWAP Phase 2; P10-D18 and P10-D19 cited where they belong.*

**Replaces:**
- `Zola Conversational Attention Architecture.md`: how she decides whether speech is meant for her. Kept nearly whole as vision.
- `Zola Streaming Cognition Architecture.md`: thinking while Brian is still talking. Kept for its behavioural requirements. Android actors (QueryProcessor, Gemini Live, ResponseExecutionService) are dropped.
- `Zola_Architecture_Living_Voiceprint_MultiSpeaker.md`: knowing who is speaking, and being aware of the room. Kept as vision. The Android implementation (CampPlus, sherpa-onnx, EncryptedSharedPreferences, Firestore) is dropped.
- Agent Map agents 3 (attention context) and 11 (speculative intent).

**Governing records:**
- Lore: C3; P2-D01–D04, D06, D12, D14; P4-D18, D28; P7-D01–D09; P9-D14; P9-SPEAK D7(a) and the echo tail; S1, S5, S17, S19, S36, S77.
- `SPEECH_DECISIONS.md`: SP-D01, SP-D02; VD-1 to VD-5 (open); the three listening modes; `SPEECH-BASELINE` and `SPEECH-SPIKE`. `VOICE_SCOPING_NOTE.md`: C-1 to C-4, the proposed ambient rule.
- ARCH-05, ARCH-07, ARCH-11, ARCH-12, ARCH-17, ARCH-13 (as amended by ARCH-30), ARCH-22, ARCH-27, ARCH-28, ARCH-30, ARCH-31; R1.

**This doc sets the intent. The speech track decides the mechanism.** How audio is captured, how echo is rejected and whether a separate audio helper replaces Hermes's voice loop are decided by the speech qualification work on evidence (SP-D02). Nothing here chooses an implementation. **Android numbers are unvalidated**, for example confidence thresholds, window lengths and enrolment counts.

---

## 1. Intent

Zola is a voice. Talking with her should feel like talking with someone in the room, not like operating a device.

> The system should eventually feel less like "a device waiting for a command" and more like "a conversational presence that knows when it is being addressed." (Conversational Attention, kept)

**What this should feel like:**
- Brian asks a question, and then "what about Saturday?" a moment later. She answers both without needing her name again.
- He's talking to Bre in the shop. She stays out of it.
- She's mid-answer and he says "wait, the other one". She stops, takes the correction and carries on.
- She asks him something unprompted and he just answers. No wake word, no restart (vision §3, Engagement).
- Someone new starts talking and she notices. At a natural moment, if she's part of the conversation, she asks who's joining.
- Her opening words aren't clipped, his opening words aren't lost, and she never answers her own voice.

**Three questions, three different jobs:**
1. **Was that meant for me?** Attention (§4). This decides whether speech enters her reasoning at all.
2. **What does he mean?** Understanding. This is the conversation layer's job (A06), not A07's.
3. **Should I speak now?** Outbound engagement (A10, A11). A different authority.

> **Inbound attention and outbound interruption are different authorities.** Merging them makes a system that is too eager to respond and too timid to raise things, or the reverse. (Conversational Attention §15, kept)

---

## 2. Principles

1. **Attention before understanding.** No captured speech is treated as a request until it has been judged as meant for her (§4).
2. **One governed listening flow.** Every utterance goes through one capture flow and one admission decision: wake word, push-to-talk, follow-up, clarify answer or interruption. There is one authoritative admitted transcript and no second transcript path (P7-D01; Conversational Attention §13). The audio work inside that flow may overlap (§3).
3. **Hearing is not permission to participate.** Speech not meant for her never triggers a reply, a tool, an approval or a sent message. If she isn't part of the conversation, it isn't remembered either; that would be eavesdropping (ARCH-30, §9).
4. **Fail silent, not chatty.** When she isn't sure speech was for her and it's low-value, she stays quiet (§4.3).
5. **A false positive in a sensitive area costs more than a miss.** Messages, email, calendar changes, health, money, location and family details need more confidence that she was addressed (§4.4).
6. **The wake word is an override, not the foundation.** It always works. The goal is that it is rarely needed (§4.5).
7. **Attention is stateful.** "Raymond." is meaningless on its own and an obvious answer after she asked "Raymond or Tom?" (§4.6).
8. **Think early, commit late.** She may prepare while Brian is still talking. Nothing provisional is ever treated as what he said, written to memory or acted on (§7).
9. **Recognition is not permission.** Knowing who is speaking tells her who it probably is. What that person may do comes only from policy (ARCH-07, ARCH-12; A15).
10. **Speech never alters facts.** She speaks authorised content in her own words. Phrasing never adds facts, and she never draws on her own unfinished drafts (Streaming Cognition, "speaks authorised content only"; A01).
11. **She never treats her own voice as Brian's.** Self-echo is a correctness failure, not a nuisance (P7-D06; SP-D01).
12. **Never recordings.** She keeps understood facts and voice signatures, never raw audio of conversations (ARCH-05).

---

## 3. The listening flow

**One governed flow, not a strict sequence.** These jobs all happen to the same captured audio:
- **capture:** the active endpoint's microphone. On the PC today, Hermes's serve process owns the device and the client drives it (P2-D01, C3). On the phone, the phone captures its own audio (A12 §2 p7).
- **speech detection and echo handling:** is this speech, and is it her own voice?
- **speech to text:** local faster-whisper today (P2-D02). Audio doesn't leave the PC without a deliberate decision (VD-4).
- **who is speaking** (§8), when that exists.

These may run on overlapping audio. Speaker recognition, for example, need not wait for the transcript. How they are arranged is for the speech qualification work to decide.

**What must stay single:**
- **One admission decision** on whether the speech was meant for her (§4). On Windows today this is `TranscriptAdmission` (P7-D01).
- **One authoritative admitted transcript**, carrying its speaker (when known), its capture, its session and any question it answers (P7-D05).
- **Only admitted speech becomes a request** to the conversation (Hermes; A06).

**Two different permissions, never confused:**

| Permission | What it allows | Who gets it |
|---|---|---|
| **Admitted as a request** | Enters the conversation as a turn: may be answered, acted on, approved | Only speech meant for her (§4) |
| **Learned from as an observation** | Understood facts, attributed to the speaker, kept in memory under ARCH-05 and ARCH-13 | Only speech in a conversation she is **part of** (§9). Never as a user turn, never as a request |

Example: Brian and Marcus are both talking with Zola, and Marcus says to Brian, "I'll bring the jack stands Saturday." Zola is part of that conversation, so she may remember it as Marcus's statement. It is not a request to her, and she does nothing with it unless asked.

**Required constraints** (Conversational Attention §13, kept):
- no second transcript path
- nothing downstream makes its own attention judgment
- attention logic never rewrites what Brian said
- suppression never hides a direct question from Brian
- speech not meant for her never triggers tools, approvals or sends

---

## 4. Attention: was that meant for me?

### 4.1 What kind of speech is it?

| Kind | Example | What happens |
|---|---|---|
| **Directed** | "Zola, remind me to check the oil." / a question when only Brian is there and nothing else is going on | Admitted |
| **Continuation** | "What about Saturday?" just after she answered about the weekend | Admitted while the conversation is open (§4.6) |
| **Answer to her question** | "Raymond." after "Raymond or Tom?" | Admitted, bound to that question (P7-D05) |
| **Interruption** | "Wait, explain that part" while she speaks | Admitted as an interruption (§6) |
| **Ambient** | Brian talking to Bre; the TV; a phone call; shop talk | Not admitted. If she isn't part of the conversation, used only to judge attention, then discarded (ARCH-30, §9) |
| **Her own voice** | Her reply picked up by the mic | Never admitted (§10.4) |

### 4.2 Signals

Text alone can't decide it (Conversational Attention §2). Signals include:
- her name or the wake word
- whether a conversation with her is open, and whether she just asked something
- question or request phrasing, and references to what she just said
- timing: a reply right after her turn
- who is speaking (§8) and whether others are talking to each other (§4.7)
- the endpoint and the noise level (§4.8)

**Prepared hints** (who's usually around at this time and place, which topics are active) may make this faster. They are hints only: the attention decision is still made here, by the one listening flow, and stale hints are ignored rather than waited for (Agent Map, Agent 3).

### 4.3 How sure, and what then

| Confidence | What she does |
|---|---|
| **High** | Treats it as meant for her |
| **Medium** | Asks lightly, and only if it matters: "Were you asking me?" |
| **Low** | Stays silent. No reply is generated |

**Low confidence fails silent.** The cost of joining a conversation she wasn't invited to is higher than the cost of missing a casual remark. If she missed something, Brian can say it again or use her name.

**Three kinds of clarification are never confused** (Conversational Attention §11):
- **attention:** "Were you asking me?" (rare)
- **meaning:** "Bumblebee or Double R?"
- **action confirmation:** "Want me to send that?" (A15)

### 4.4 Sensitive areas need more confidence

Messages, email, calendar changes, reminders, health, money, location, cameras, family details and personal memories need more confidence that she was addressed before she acts or discloses anything. The bar rises with how irreversible or sensitive the result would be (Conversational Attention §12).

### 4.5 The wake word

"Hey Zola" (P2-D04) is always a reliable way in: the first time, in a noisy shop, or when Brian wants to be sure she heard. It is **never required** for a follow-up, an answer to her question, an interruption or a confirmation.

**Whether the wake word comes back after a long silence** is Brian's choice (VD-5). It is not assumed (VOICE_SCOPING_NOTE C-3).

**Who may start a conversation without it (ARCH-67).** Four separate questions, never collapsed:

| Question | Decided by |
|---|---|
| Who is this? | Recognition (§8) |
| May they start a conversation with her? | **Anyone, with the wake word.** Without it: a **per-person permission**. Brian has it by default; Bre or the boys only when Brian grants it; **a visitor never**, however often she has heard them |
| Is this speech meant for her? | Attention (§4) |
| May she do what they ask? | A15 (guests: conversation plus the harmless-lookup shortlist, ARCH-38) |

Learning someone's voice doesn't change their ability to start a conversation. *This supersedes the Android "Gatekeeper background activation" grant (Living Voiceprint §12) with a Windows rule owned by the listening flow.*

### 4.6 Attention has state

She always knows which state she is in, and every change is logged with its reason (Conversational Attention §10):

| State | Meaning |
|---|---|
| **Idle** | No conversation open. Listening for the wake word, or (later) for speech addressed to her |
| **In conversation** | A confirmed exchange is under way |
| **Follow-up open** | She just spoke; a short follow-up counts as for her |
| **Waiting for an answer** | She asked something; a short answer is bound to that question |
| **Interrupted** | Brian cut in; what she was saying is kept until resolved |
| **Others talking** | People are talking to each other; she stays out |
| **Noisy** | The signal is unreliable; she leans on the wake word |

The follow-up window **closes gracefully**. It narrows with time, when the topic is finished, when other people start talking, and with noise. An old topic never holds the door open indefinitely.

### 4.7 Knowing when not to join

When Brian is clearly talking with someone else, she stays quiet. That holds even when what he said would pass on its own ("What time is it?"). Conversational intelligence includes knowing when not to join (Conversational Attention §9).

### 4.8 The endpoint changes the answer

The same words can need different handling depending on where they were heard (Conversational Attention §8):

| Endpoint | Attention profile |
|---|---|
| **PC (office)** | Quiet room, usually Brian alone (SP-D01). May pick up calls and meetings, so stronger privacy |
| **Phone, shop and car devices** | Push-to-talk first (ARCH-24, A12). Wake-free listening on them is separate research. Shop: noisy, more false positives. Car: driving rules (A08) |
| **Glasses, wearables** | Vision. Must not speak private information aloud in public |

---

## 5. Listening modes

Three different behaviours, decided separately (`SPEECH_DECISIONS.md`, 2026-10-21):

| Mode | What it is | Why it matters | State |
|---|---|---|---|
| **Immediate reply** | Listening for Brian's answer right after she speaks to him | Without it, she can't start a conversation (vision §3, Engagement) | Exists after ordinary replies (P2-D06); **not after unprompted lines** (P9 D7(a)) |
| **Talk-over** | Listening while she speaks, so he can interrupt | Natural conversation; stopping her mid-sentence | **Off** (P4-D28) because spoken clarify answers were treated as interruptions; Brian wants it back without breaking them (S36) |
| **Idle wake-free** | Listening without a wake word while nothing is going on | "Walk into the shop and just ask" | Not built; **Brian's choice** whether and when (VD-2) |

**The intended experience on the PC (ARCH-31, confirmed by Brian):** Brian can talk to Zola naturally, without routinely saying "Hey Zola", and she can tell that apart from him talking to someone else. "Walk into the shop and just ask" (VOICE_SCOPING_NOTE C-2) is the target, not an optional extra. What is still open is **how and when** that is rolled out (VD-2): in which rooms, with others present, with the radio on. A build that delivers excellent follow-ups after the wake word but never this would miss the goal.

**Prerequisites for her starting conversations** (SP-D01): accurate detection of when she finished speaking, natural follow-up listening, reliable talk-over, no self-echo, no clipped opening words, and the existing voice and conversation safety rules kept.

---

## 6. Interruptions and corrections

Interruptions are control signals, not noise. Each kind is recognised and handled deliberately (Conversational Attention §5; Streaming Cognition §8):

| Kind | Example | What happens |
|---|---|---|
| **Stop** | "Stop." / "Not now." | She stops speaking at once |
| **Pause** | "Hold on." / "Wait." | She pauses; what she was saying is kept |
| **Correction** | "No, I meant Micah." / "Make it tomorrow." | Corrects the current request |
| **Redirect** | "Actually, check traffic first." | A new request; a new turn |
| **Go back** | "Wait, what was the second thing?" | Revisits part of what she said |

**The commit line: four stages** (Streaming Cognition §9, sharpened):

| Stage | Example | What a correction does |
|---|---|---|
| **1. Still being spoken** | "Remind me Friday… no, Thursday" | Folded in. Only Thursday ever existed |
| **2. Request admitted, nothing done yet** | Her reply is being generated | The request is **revised**. Anything prepared for the old version is discarded |
| **3. Work under way** | A reminder is being set, or a draft written | The old work is **cancelled or replaced**. It must never finish later using the superseded meaning |
| **4. Already done** | The reminder exists | A new turn: the normal update or cancel path. Nothing is silently changed |

**Rules:**
- Superseded work never completes afterwards on the old interpretation.
- If it isn't known whether the old work finished (stage 3 with an uncertain outcome), she says so and checks; she never assumes.
- **Stopping her speech is not undoing an action.** "Stop" ends what she's saying. Something already done stays done until Brian asks for it to be changed (A15).

**Playback outcome, not "heard".** When she is interrupted, the line is recorded as **completed, partial (with the part known to have played), failed or uncertain** (A06). She never claims to know what Brian heard. For repeats and summaries, anything not confirmed as played counts as **not delivered**.

---

## 7. Thinking while he talks (vision)

> **Think early, commit late.** Streaming cognition may think early, but it may not commit early. (Streaming Cognition, kept)

While Brian is still speaking, she may:
- start interpreting what he's saying as the words arrive
- notice who and what he's talking about
- look up likely memories and prepare likely tools
- notice a correction ("not Micah, Madden") before he finishes
- sketch a reply

**Hard rules:**
- **Provisional is not truth.** Nothing prepared during speech is treated as what he said.
- **The final transcript wins.** Anything that conflicts with it is discarded.
- **No streaming writes.** Nothing is written to memory, no tool runs, no approval counts, and the topic stack doesn't change before the turn is final.
- **She speaks authorised content only.** She never draws on her own draft as a source of fact.
- **Nothing provisional survives the turn** unless the normal authority promotes it.
- **No hidden second router.** Preparation may make the right path faster; it never chooses the path.
- **Observable.** Logs show that every provisional item was either discarded or promoted properly.
- **Tool arguments come from the final transcript,** re-extracted before anything runs, never from a partial phrase. When preparation guessed a different path from the one finally chosen, that disagreement is logged.

On Windows, Hermes runs speech-to-text, then the model, then speech as a chain, and full duplex is not a requirement (S5). Most of this section is vision. Its first practical value is speed: she is ready when he finishes.

---

## 8. Who is speaking (vision)

### 8.1 What she learns

**Decided (ARCH-07):** she learns the voice and face of **anyone she sees**, for her own recognition of people and to give accurate information if someone attempts something unauthorised. This settles the conflict between the Android sources: Perceptual Input said "never capture third-party biometrics"; Living Voiceprint enrolled introduced people. Brian chose to learn them.

**What she keeps:** a voice signature (numbers that describe a voice), the name, and when and where it was learned. **Never raw audio** (ARCH-05).

**Kept from Living Voiceprint as intent:**
- **A living signature.** It improves over time from clean, verified samples, across different rooms and noise levels. It is never rebuilt from doubtful samples.
- **Detection vs tracking.** "Is this someone I know?" and "who is talking right now, and has that changed?" are separate jobs.
- **Unknown voices.** A single odd sound (a dropped wrench, a compressor) never counts as a new person. Several seconds of clear, unfamiliar speech does.
- **Asking who's joining.** If she's part of the conversation, she may ask at a natural pause: "I don't think we've met. Who's joining us?" (ARCH-05). Otherwise she notices and does nothing else.
- **Names.** Brian can introduce someone ("Zola, this is Marcus"), or the person can answer her. An unanswered unknown voice gets a placeholder that Brian can name later.
- **Never narrate.** She doesn't announce "Brian is now speaking". Knowing who is talking shapes how she responds.
- **Room awareness.** She knows who said what in the conversation, answers the person who asked, and addresses the room when something concerns everyone.
- **Turn-taking with several people.** She waits for a natural pause in the human conversation. The bar for cutting into a two-person conversation is higher than for a one-on-one (ARCH-22).

**Safeguards when learning voices** (kept from Living Voiceprint §§6–8 as behaviour; the Android model, pool size and thresholds aren't carried):
- **Only clean, attributable samples teach.** If she can't separate two unknown speakers, she learns from neither. Two people never blend into one new identity.
- **Naming is not a sample.** When Brian says "that's Marcus", Brian's voice never trains Marcus's signature. Only Marcus's own speech does.
- **A safe baseline is kept.** Each signature keeps a reliable baseline she can fall back to, so a bad update can be undone.
- **Learning is bounded.** Small mistaken matches can't gradually redefine who someone is. Updates that move a signature far from its baseline are held back until confirmed.
- **Improvement samples are held in memory until the conversation ends cleanly.** After a crash they're discarded, never half-applied. Samples from varied conditions (quiet, compressor running) are preferred over more of the same.
- **"Learns anyone she sees" doesn't make every sample fit to learn from.** Unclear or mixed audio is used for attention only, then discarded (ARCH-30).

### 8.2 What recognition is used for

| Use | Decided by |
|---|---|
| Knowing who probably said what | A07 |
| Who may hear what she says (audience) | A14, ARCH-13 |
| Verified household member's low-stakes requests | A15, ARCH-03 |
| Treating an unverified speaker as a guest | ARCH-12 |
| Brian on the phone (sensitive content, approvals) | ARCH-28, A12 |

**Recognition is never an approval.** It never stands in for anyone's approval method (ARCH-07). A voice that resembles Brian's is still a guest until verified (ARCH-12).

**When someone joins,** the conversation moves to a fresh shared session, and the earlier private one stays with its owner (ARCH-17; A06 §7).

### 8.3 Keeping it safe

- Signatures stay on the PC; they are never sent to a cloud service. *Kept from Living Voiceprint as a proposed lasting boundary.*
- Brian can see every voice she knows (including ones still being learned), when each was last improved, rename it and delete it. Deleting is immediate and complete.
- Signatures are kept out of backups that leave the PC. *Kept from Living Voiceprint as intent; the Windows mechanism is a build decision.*
- A newly learned voice gets no special abilities by being learned (§8.2).
- Biometric data is the most sensitive category (A14).
- **A visitor's signature lasts two weeks** (ARCH-37). The expiry reaches every copy and anything derived from it, and repeat sightings don't make it permanent (A09 §6).

---

## 9. What she does with what she overhears

**Firm, whatever else changes:** speech that isn't meant for her never becomes a reply, a tool call, an approval, a send or a change to her settings (§2 p3).

**Decided (ARCH-30, re-decided 2026-10-29):** overheard speech is **discarded unless she is actively part of the conversation.** Brian: *"I think it is safer to go with overheard speech is discarded unless she is actively part of the conversation. If not, then it really becomes eavesdropping I guess."*

- **She is part of the conversation:** ARCH-05 governs. She keeps understood facts, attributed to whoever said them, never recordings, including what others say to each other within it (§3 example). Disclosure follows ARCH-13.
- **She is not part of it** (Brian and Bre talking in the shop, Bre on the phone, the TV):
  - the speech may be processed **locally** only to judge whether it was meant for her;
  - then it is **discarded at once**: no conversation, memory, background reasoning, approvals or tools;
  - logs keep metadata only, never the words.
  This matches the speech track's proposed ambient rule (VD-3).
- **This deliberately amends ARCH-13.** ARCH-13's example "Zola overhears Bre on the phone: treated as Bre's private information" no longer applies. She doesn't keep it at all. ARCH-13 still governs what is said privately to her, and everything she keeps from conversations she is part of.
- **Correction of the record:** draft v0.1 wrongly said the overheard case "wasn't asked". ARCH-13 had covered it. Brian re-decided with the correct picture.

**When she counts as part of the conversation (ARCH-30, confirmed by Brian):**
- She has been addressed in it, or is answering or asking in it.
- Someone joined while she was already in a conversation with Brian (ARCH-17 applies).
- It ends when the follow-up window closes (§4.6) and the people present are no longer talking with her. A conversation she was part of earlier doesn't make a later, separate one hers.
- **A phone call is never hers** unless she's put on it, even when Brian takes it mid-conversation with her.

**Later path (direction from ARCH-30's first version, not built):** learning from overheard speech only where Brian switches it on, for example in the shop when he's alone. It needs its own decision if ever wanted.

---

## 10. Speaking

### 10.1 Her voice

- **One voice, everywhere.** Deepgram Aura-2 Pandora at 0.95 today (P9-D14), on the PC and, later, played on the phone (A12 §4).
- **How she talks out loud** follows SOUL's speaking rules (P4 naturalness). Clarify questions are asked conversationally in Voice mode, with choices spoken (P7-D09).
- **Speech is a costly act.** Each unprompted line spends Brian's attention (A10, heat per person, ARCH-18).

### 10.2 One speaking authority

- Only authorised content is spoken, and only through the single delivery path for unprompted lines (A10 ARCH-09, A11).
- Hermes's own extra speech paths (review summaries, background completions, heartbeat) are accepted for now without arbitration (A2; A01 Q1). That remains an open question for A10.

### 10.3 Codes

A verification code is read aloud **only on Brian's explicit request**, through the direct path that bypasses the model, history, memory, logs and persistent speech caches (R1). **A local voice speaks codes** (Microsoft Zira; Brian: "I'm going with Zira."), so a code never goes to the cloud voice (ARCH-36; R1, shipped in Phase 10).

### 10.4 Never answering herself

- She never admits her own voice as Brian's (P7-D06). The playback monitor outranks estimates: if she is still audible, her speech cannot become his input.
- **Paired requirement: echo rejection and interruption are tested together.** While she speaks through the laptop speakers, **her voice is rejected and Brian's overlapping speech still gets through**, for interruption and for understanding. Rejecting everything during playback would pass "never answers herself" and make talk-over impossible. The test covers "stop", a correction, and **an answer to her clarify question given while she is still speaking**, the case that broke talk-over before (P4-D28).
- Today's echo matcher catches only the end of her reply (P2-D14, P7-D07). Ordinary-reply echo can still become a turn in some cases (S77, accepted risk). Self-echo rejection during talk-over is the main unknown for the speech track (VOICE_SCOPING_NOTE C-1).

### 10.5 Timing

- **Interjections in a live conversation wait for a natural pause** unless time-critical (ARCH-22).
- **Playback outcome, not "heard".** Each line is recorded as completed, partial (with the known played part), failed or uncertain, on evidence (A06; P9-SPEAK). She never claims to know what Brian heard.

---

## 11. As built on Windows (2026-10-29)

| Capability | State | Evidence | Decisions |
|---|---|---|---|
| Serve owns the mic and speaker; the client drives voice over the socket; one RPC owner | live-tested | P2 | P2-D01, C3 |
| Local faster-whisper speech-to-text, pinned; no silent cloud fallback | live-tested | P2 | P2-D02 (A01 Q4: confirm still current) |
| "Hey Zola" wake word; mic button and hotkey fallback; same session | live-tested | P2 | P2-D04 |
| Follow-up window after ordinary replies | live-tested (precise end of playback is S17) | P2, P5 | P2-D06, P5-D01 |
| One admission authority; cancelled captures dropped; no unbound transcripts mid-turn; only the bound capture answers a clarify; drops logged, not announced | live-tested | P7 | P7-D01–D05, D08 |
| Playback monitor outranks estimates; echo matcher as defence only | live-tested | P7 | P7-D06, D07 |
| Clarify asked conversationally in Voice mode | live-tested | P7 | P7-D09 |
| Deepgram Aura-2 Pandora voice | live-tested | P9 | P9-D14 |
| Code read only on explicit request: local Zira voice, one-time handle, value never in the model, history, memory, logs or a file | shipped (P10) | P10 closeout | R1, P10-D04 |
| Unprompted line: no follow-up listening afterwards; 2-second echo tail | live-tested | P9 T6 | D7(a) |
| Talk-over (barge-in) | **off** | P4 | P4-D28; S36 |
| Directed speech without a wake word; speaker recognition; streaming cognition | **not built** | — | S19, S1 |
| Speech qualification (`SPEECH-BASELINE`, then `SPEECH-SPIKE`) | approved, not yet run | — | SP-D02 |

`identity/VOICE_CONFIG.md` still documents an older voice (Sonia / Edge). The live voice is Pandora. Fixing it is a config-doc change that needs its own approval (A01 §6).

---

## 12. Limits

| Limit | Kind | Accepted risk | Note |
|---|---|---|---|
| Wake word or button needed to start | temporary limit | — | S19; VD-2 |
| No follow-up listening after an unprompted line | temporary limit | — | D7(a); blocks vision §3 Engagement until fixed |
| Talk-over off | temporary limit | — | P4-D28; S36 |
| Follow-up window ends on a fixed timeout after an estimate | temporary limit | — | S17 |
| Ordinary-reply echo can sometimes become a turn | temporary limit | yes | S77 |
| No speaker recognition; one user assumed | temporary limit | — | S1 |
| Local speech-to-text only | lasting boundary unless changed | — | P2-D02; VD-4 |
| One listening path; one admission authority | lasting boundary | — | P7-D01 |
| Overheard speech never triggers replies, tools, approvals or sends | lasting boundary | — | §2 p3 |
| Overheard speech, when she isn't part of the conversation, is discarded and never remembered | lasting boundary unless changed (amends ARCH-13) | — | ARCH-30 |
| Never recordings; voice signatures only | lasting boundary | — | ARCH-05 |
| Recognition is never an approval | lasting boundary | — | ARCH-07 |
| Nothing provisional is written or acted on | lasting boundary | — | §7 |
| Voice signatures never leave the PC | lasting boundary (proposed) | — | §8.3 |

---

## 13. Open questions

**Brian's call:**
- **Q-V1.** *Resolved by ARCH-30 (re-decided):* overheard speech is discarded unless she is actively part of the conversation. This amends ARCH-13.
- **Q-V8.** *Resolved:* when she counts as part of a conversation, as in §9 (ARCH-30).
- **Q-V9.** *Resolved by ARCH-31:* talking to her naturally without routinely using the wake word is the goal. Rollout stays open (VD-2).
- **VD-2: idle wake-free listening.** Whether, and in which conditions: alone in the shop, with others present, with the radio on. Speech track.
- **VD-5: wake-word requirement after silence.** Whether, and when, a long silence makes the wake word required again. The "Hey Zola" override itself always stays available (§4.5; A14 §8). Speech track.
- **VD-4: speech-to-text locality.** Local only, or cloud streaming while the mic is open. Speech track.
- **R1 voice for codes.** *Resolved by ARCH-36:* a local voice speaks codes.

**For the speech track, on evidence (SP-D02, VD-1):**
- **Q-V2.** Whether a supervised audio helper owns audio in place of Hermes's voice loop (VOICE_SCOPING_NOTE R-2).
- **Q-V3.** Self-echo rejection during talk-over on Brian's laptop speakers and integrated mic (C-1).
- **Q-V4.** Admitting speech without a wake word: ambient, then candidate, then admitted or discarded (C-2).
- **Q-V5.** Thresholds and window lengths. All the Android numbers are unvalidated.

**Later:**
- **Q-V6.** Where speaker recognition runs for phone audio: on the PC from what the phone sends, or partly on the phone. The PC decides either way (A12 §5).
- **Q-V7.** Voice signature ↔ person link. How a known voice connects to the person in her world model (A03, A04).

---

## 14. Acceptance scenarios

- **V1. Follow-up without her name.** Brian asks about the weekend, then "what about Saturday?" She answers. Then he talks to Bre about something else, and she stays silent.
- **V2. Bound short answer.** She asks "Raymond or Tom?" He says "Raymond." It answers that question; it isn't a new request (P7-D05).
- **V3. Overheard, not addressed.** Brian tells Bre "we should probably leave soon". She does not offer traffic (Conversational Attention §16).
- **V3b. Overheard, not remembered.** Brian tells Bre in the shop that his brother is visiting next week; Zola isn't part of that conversation. Later, she has no memory of it. Logs show only that speech was heard and judged not addressed (ARCH-30).
- **V3c. Part of the conversation.** Brian and Marcus are talking with Zola about the build, and Marcus says to Brian that he'll bring the jack stands Saturday. She may remember it as Marcus's statement. It is not a request, and she does nothing with it unless asked.
- **V4. Low confidence, low value.** A muttered phrase she half-caught. She says nothing.
- **V5. Sensitive area, unsure.** "Text him I'm running late" said while Brian seems to be talking to someone else. She doesn't send; at most she asks "Were you asking me?". A send still needs the approval rules (A15).
- **V6. Correction before acting.** "Remind me Friday… no, Thursday." One reminder, Thursday.
- **V7. Correction after acting.** The reminder is set for Friday, then he says "make it Thursday". It goes through the normal update path; nothing is silently changed.
- **V8. Stop.** "Stop." She stops at once. The line is recorded as partial with the known played part, and the rest counts as not delivered. Nothing she already did is undone.
- **V9. No self-echo, with interruption still working.** Over a session of replies on the laptop speakers, none of her own speech becomes a turn. In the same session, "stop", a correction and an answer to her clarify question, each spoken over her voice, all get through.
- **V9b. Thinking pause.** Brian says "Can you check whether… um… the parts order shipped" with a long pause in the middle. She waits; she doesn't answer half a question.
- **V9c. Superseded work.** "Draft a reply to Micah… actually, to Madden." The Micah draft never appears later.
- **V9d. Her name in the background.** Brian tells Bre "Zola said the parts ship Tuesday". She doesn't answer, and nothing is kept (ARCH-30).
- **V9e. Responsiveness.** Over a session, missed requests (he spoke to her, she ignored him) are measured and reported alongside false activations. Both must meet thresholds Brian approves (VOICE_SCOPING_NOTE §4).
- **V10. Opening words kept.** Brian answers her immediately after she finishes. His first words are in the transcript.
- **V11. Unprompted, then just answer** (when built). She raises something unprompted, and he replies without the wake word. The reply is part of the same conversation.
- **V12. Unknown voice.** A friend starts talking in the shop while Brian and Zola are talking. A dropped tool doesn't trigger anything. After a few seconds of clear speech, she asks at a pause who's joining. She never asks mid-sentence.
- **V13. Voice like Brian's.** An unverified voice similar to Brian's asks for his email. Treated as a guest (ARCH-12).
- **V14. Nothing provisional kept.** Brian starts "remember that Micah…" and stops: "never mind". Nothing is written.
- **V15. Several people.** Brian and Marcus are both talking with her. She answers Marcus's question to Marcus and doesn't announce who is speaking.

- **V17. A known visitor.** Marcus has visited four times and she knows his voice. He says "what's the weather doing?" without the wake word: she doesn't treat it as addressed to her. He says "Hey Zola, what's the weather?": she answers, under guest rules.
- **V16. Two strangers.** Two unfamiliar people talk over each other in the shop. She can't separate them, so neither voice is learned. Later Brian says "that's Marcus"; only Marcus's own words train Marcus's signature. A bad update the next week is rolled back to his baseline.

---

## 15. Coverage of the source docs

**Status of this map.** "Verified" means the destination section exists and was checked against the source. Rows pointing to docs not yet written are "planned".

**`Zola Conversational Attention Architecture.md`**

| Source section | Destination | Treatment | Status |
|---|---|---|---|
| Vision; attention before understanding | §1, §2 p1 | preserved | verified |
| §1 Attention authority | §2 p2, §3 | preserved; Windows authority = `TranscriptAdmission`; one governed flow, not a strict sequence | verified |
| §2 Directed speech | §4.1, §4.2 | preserved | verified |
| §3 Ambient speech | §4.1, §9 | preserved; no memory writes when she isn't part of the conversation (ARCH-30, amends ARCH-13) | verified |
| §4 Continuation | §4.1, §4.6 | preserved | verified |
| §5 Interruptions | §6 | merged with Streaming Cognition §8 | verified |
| §6 Confidence bands | §4.3 | preserved; Android numbers unvalidated | verified |
| §7 Wake word | §4.5 | preserved; fallback is VD-5 | verified |
| §8 Endpoint profiles | §4.8; A12 §10 | merged | verified |
| §9 Social context | §4.7 | preserved | verified |
| §10 Attention states | §4.6 | condensed | verified |
| §11 Clarification types | §4.3 | preserved | verified |
| §12 Privacy, sensitive areas | §4.4, §9; A14 | merged | verified (A14 §5 checked) |
| §13 Speech pipeline | §3 | preserved | verified |
| §14 Continuity | §4.6; A06 | merged | verified |
| §15 Inbound vs outbound | §1; A10 | preserved | verified |
| §16 Autonomous behaviour | §2 p3, V3 | preserved | verified |
| Core principles | §2 | merged | verified |
| Failure modes | §2, §4, §14 | merged | verified |
| Roadmap ("existing foundations in Ava") | §11 | superseded by the Windows as-built | verified |
| Open questions, risks | §13 | merged | verified |

**`Zola Streaming Cognition Architecture.md`**

| Source section | Destination | Treatment | Status |
|---|---|---|---|
| Vision; think early, commit late; non-goals | §7 | preserved | verified |
| §1–§7 Engine, turn state, artefacts, phrase, intent, entity, topic tracking | §7 | condensed to behaviour | verified (notes: component names dropped) |
| §8 Interruptions | §6 | merged | verified |
| §9 Corrections | §6 | preserved | verified |
| §10–§11 Memory and tool candidates | §7 | preserved as rules | verified |
| §12 Tone | §7; A02 | rule kept: tone shapes style, never content | verified |
| §13 Attention gate | §4 | merged (one authority) | verified |
| §14 Draft buffer | §7 | preserved as rules | verified |
| Lifecycle stages | §3, §7 | condensed | verified |
| Authority rules | §7, §2 p10 | preserved; Android actor names dropped | verified |
| State model | §7 | condensed | verified |
| Observability | §7 | preserved | verified |
| Cursor guardrails, files likely involved | — | intentionally dropped (Android build detail) | verified |
| Open questions, success criteria, risks | §13, §14 | merged | verified |

**`Zola_Architecture_Living_Voiceprint_MultiSpeaker.md`**

| Source section | Destination | Treatment | Status |
|---|---|---|---|
| §1–§2 Purpose; living signature; detection vs tracking | §8.1 | preserved | verified |
| §3 Audio tap | §3 (one capture path) | superseded by the Windows capture ownership (P2-D01) | verified |
| §4–§5 Tracker, speaker events | §8.1 | condensed to behaviour | verified |
| §6 Introductions, unknown cluster gate; who answers the name; ambiguous attribution paused | §8.1 (incl. safeguards) | retained; consent superseded by ARCH-07; 30-day provisional expiry superseded by ARCH-37 (two weeks) | verified (fresh read 2026-11-02) |
| §7–§8 Pool, refinement, drift protection (anchor kept, clean close only, condition diversity) | §8.1 safeguards; §8.3 | retained as behaviour; pool size, thresholds and CampPlus intentionally omitted | verified (fresh read 2026-11-02) |
| §9 Multi-speaker conversation | §8.1, §8.2 | preserved; turn-taking aligned with ARCH-22 | verified |
| §10–§11 Schema, session lifecycle | — | intentionally dropped (Android implementation) | verified |
| §12 Privacy and consent (incl. backup exclusion, refinement history visible) | §8.3; A14 | merged; "on-device" becomes "on the PC" | verified (fresh read 2026-11-02) |
| §12 Gatekeeper eligibility (background activation needs Brian's grant) | §4.5 "Who may start a conversation without it" | **superseded by ARCH-67**: per-person permission to start without the wake word; visitors never | verified |
| §13 Firestore metadata | — | intentionally dropped (no Firestore on Windows) | verified |
| §14 Open questions | §13 (Q-V5, Q-V7) | merged | verified |

**Agent Map**

| Source | Destination | Treatment | Status |
|---|---|---|---|
| Agent 3, Attention Context | §4.2 (prepared hints), §4.6 | merged | verified (fresh read 2026-11-02) |
| Agent 11, speculative intent | §7 | merged (preparation without authority) | verified |
