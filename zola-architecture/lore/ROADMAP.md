# Zola-Windows Roadmap
Status tracking for the Windows-native rebuild of Zola on Hermes Agent
(pinned tag `v2026.9.14` / `345cd2b057a452236de401d3534b8502a7465e8d`).
## Phase 1 complete
Phase 1 closed at four tracks. Tracks 5 (Email) and 6 (Confirmed Send)
were deferred, not completed. See `OPEN_QUESTIONS.md` S16.
1. ✅ **AUDIT** — WINH01–WINH12 + WINH00 synthesis, complete. 187 findings
   across 12 domain audits (55 HIGH / 102 MEDIUM / 27 LOW / 3 OBSERVATION).
   Merged to `main` at `da6c35fd997487db23bb15c08eb9056e28413e39`.
2. ✅ **DECISIONS LOCKED** — complete. See `DESIGN_DECISIONS.md` for all
   resolved items (C1–C12, S1–S11, P1–P4, H1–H6, A1–A9).
3. ✅ **BUILD PLAN WRITTEN** — complete. See
   `zola-architecture/lore/build-plans/PHASE1_BUILD_PLAN.md`.
4. ✅ **TRACKS EXECUTED** — four tracks merged. Tracks 5 and 6 were
   deferred after Track 5's Phase 2 grounding, not finished.
5. ✅ **VERIFICATION / SMOKE TEST** — each landed track's own smoke test
   passed. The original combined pass that included email read and
   confirmed send was not run, because those tracks left Phase 1.
6. ✅ **TRACK MERGED**
   - P1-CLIENT: `c3542c678b063b1321927e23c5b91ae90149a155`
   - P1-IDENTITY: `83405c34ea96a598e6bb6a32bd3d9137d078cee2`
   - P1-SESSION: `eecd72821d31587a824f55b97892c9f1a7841483`
   - P1-MEMORY: `28ba0f4bd4ea3a750244ce80a2703c95720e2282`
7. ✅ **LORE CLOSEOUT** — this pass. S16 records the deferred Google
   Workspace work.
## Phase 2 complete
Phase 2 closed at three voice tracks plus this lore pass. Voice is
the primary input: "Hey Zola" (or the mic button / `Ctrl+Space`)
starts a turn, transcripts submit immediately, Zola speaks in Voice
mode, barge-in and a follow-up listen continue the conversation, and
Text mode stays a silent fallback. Spoken replies require the
Latitude 7430 lid open, mic input 100, Windows audio enhancements
ON, speakers ~15, and `ffplay` on PATH (`P2-D16`).
1. ✅ **AUDIT** — no new audit series. Phase 2 used WINH09 against the
   same pinned Hermes tag; `P2-D11`.
2. ✅ **DECISIONS LOCKED** — `P2-D01`–`P2-D17`. See
   `DESIGN_DECISIONS.md` Phase 2 — Voice.
3. ✅ **BUILD PLAN WRITTEN** — complete. See
   `zola-architecture/lore/build-plans/PHASE2_BUILD_PLAN.md` v1.1.
4. ✅ **TRACKS EXECUTED** — three tracks merged.
5. ✅ **VERIFICATION / SMOKE TEST** — each track's smoke passed. Combined
   pass on `main` after Track 3 passed 2026-09-24 (cold launch, barge-in,
   follow-up, timeout-then-wake, Text mode, Resume, relaunch, distance).
6. ✅ **TRACK MERGED**
   - Plan v1.0: `c8c83f7dcf146c2626d18adc840c0fad645f6903`
   - Plan v1.1: `791769362190fa7b50058f13c692fb360a19e1b5` (merged with
     P2-VOICE)
   - P2-VOICE: `8bfbf64272949957da8ca333416431c802cbb660`
   - P2-SPEAK: `29e11d0cac195ae547bb7cb42c74b31cb7b15d54`
   - P2-SPEAK reconcile (docs): `2522c00a734b6065c6dc2e9d74089bded6f645b2`
   - P2-WAKE: `0c375efee1ea58d937a1e468ab614bfcf109e0f6`
7. ✅ **LORE CLOSEOUT** — this pass. `S17`–`S23` recorded;
   `S17` recommended first for Phase 3.
## Phase 3 complete
Phase 3 closed at five presence tracks plus this lore pass. The Windows
client is presence-first: Helix renders `zola.glb` with the approved unlit
look (`P3-D20` / `P3-D24`), `ZolaDisplayState` owns labels and
`PresenceMode` (`P3-D03` / `P3-D04`), and procedural life drives blink,
expression, brightness, and a TTS-gated mouth (`P3-D22` / `P3-D23`).
Particles were dropped. Idle GPU with blinks averages **2.27%** (≤ 10%);
static look ~**0.0013%**; cold rest memory **809 MB** (2048²).
1. ✅ **AUDIT** — P3PRE presence-UI audit, merged at
   `c2d6110fec5d9ee6c40a0d42d963d3838ab6fd63`.
2. ✅ **DECISIONS LOCKED** — `P3-D01`–`P3-D24`. See `DESIGN_DECISIONS.md`
   Phase 3 — Presence UI. `P2-D01` and `P2-D08` annotated.
3. ✅ **BUILD PLAN WRITTEN** — complete. See
   `zola-architecture/lore/build-plans/PHASE3_BUILD_PLAN.md` v1.7.
4. ✅ **TRACKS EXECUTED** — five tracks merged.
5. ✅ **VERIFICATION / SMOKE TEST** — each track's smoke passed. Track 5
   HUMAN-RUN smoke passed (developer: "smoke test passed").
6. ✅ **TRACK MERGED**
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
7. ✅ **LORE CLOSEOUT** — this pass. `S17` updated; `S24`–`S32` filed.
## Phase 4 complete
Phase 4 closed five conversation-safety and voice tracks plus this lore
pass. Lock/sleep gate; server-request broker; spoken clarify; tool activity
and Stop speaking; Sonia at 0.95 with spoken-style shaping; pitch dropped
(Edge). Idle GPU (Voice app idle, window foreground, presence blinks
confirmed, 60 s GPU Engine sum): avg **3.5291%** (≤ 10% budget;
Phase 3 blinks baseline was 2.27%).
1. ✅ **AUDIT** — P4PRE conversation audit, merge
   `4181f0402eaaaabf137bace3650615be00dca6af`.
2. ✅ **DECISIONS LOCKED** — `P4-D01`–`P4-D29`. See `DESIGN_DECISIONS.md`
   Phase 4 — Conversation Safety and Voice.
3. ✅ **BUILD PLAN WRITTEN** — `PHASE4_BUILD_PLAN.md` v1.1, commit
   `5eb8fd94c69889701fe12809fc2b56b79644a8dc`.
4. ✅ **TRACKS EXECUTED** — five tracks merged.
5. ✅ **VERIFICATION / SMOKE TEST** — per-track Part B; acknowledged
   PARTIALs: LOCK sleep/Modern Standby; REQUEST B11; VOICE V7 GPU
   measured at lore closeout (PASS ≤ 10%; pid 7940 → Zola.Client, 26 blinks).
6. ✅ **TRACK MERGED**
   - Plan v1.1: `5eb8fd94c69889701fe12809fc2b56b79644a8dc`
   - P4-LOCK impl: `c01fe3b6725a3814a368d48c0d06a2da1d16305f`
   - P4-LOCK merge: `245d171ebd106f5af52190b63c7d18f866c5a923`
   - P4-REQUEST impl: `d21ff9f9ceeeb1fecb16c5603c6b0b9549f41ace`
   - P4-REQUEST merge: `76ea698542da538d2f8c8a0a32bf9ac1986ea062`
   - P4-ASK impl: `7d0d81fcd8283234a62ed54a3f0acaf15fb3d46c`
   - P4-ASK merge: `95578b10843feed473b83482c30e199bb909aa61`
   - P4-FEEDBACK impl: `5c3197ed0b7f16ac75c95ccb12dc04bac0a2a290`
   - P4-FEEDBACK merge: `044df5e3ab6ec7d6393e0ebfa915583782177c3c`
   - P4-VOICE impl: `81652ca7442dd96aace777ff21914f9c9256ab42`
   - P4-VOICE merge: `e1a069eccca1e0c3d2bdc40c1c7bc5d4764f2a03`
   - Final `main` tip after this lore task: `5a43c3698ebc4796992f2709c1bfd2e1d96a8e05`
7. ✅ **LORE CLOSEOUT** — this pass. `S20`/`S22`/`S32` resolved; `S17`/`S21`/
   `S26` updated; `S33`–`S41` filed; `P2`/`P3`/`A3` annotated.

One-line track results:
- **P4-LOCK** — lock/sleep voice gate; Modern Standby ⚠️ PARTIAL.
- **P4-REQUEST** — broker + cards; `approvals.mode: manual`; B11 ⚠️ PARTIAL.
- **P4-ASK** — spoken clarify; barge_in false; question-only speech.
- **P4-FEEDBACK** — activity + notices + Stop; AUD-37 closed.
- **P4-VOICE** — Sonia 0.95; shaping; pitch dropped; P2-D15 refit/margin/
  startup window.

## Phase 5 complete
Phase 5 closed two tracks plus this lore pass. S41 fixed; S42 facts
carried across sessions; S36 deferred (feasibility gate NO); S38
measured (no tuning).

1. ✅ **AUDIT** — P5PRE, merge `c5be52e47ef8686d3643f5c57cf262cfd3991b8b`.
2. ✅ **DECISIONS LOCKED** — `P5-D01`–`P5-D11`.
3. ✅ **BUILD PLAN WRITTEN** — v1.1 commit
   `4c6c6439ec20e689a584d42b4c073920fb1afcd2`, merge
   `198fb00a28ea7036624ff44d0d3e58fa228e474a`; v1.2 commit
   `e2150607f24f9efa04098049dc0610f59d3c79bb`, merge
   `97dd29b40ae16d4b79aff436cfed08b35c2d18ca`.
4. ✅ **TRACKS EXECUTED** — two tracks.
5. ✅ **VERIFICATION / SMOKE TEST**
   - P5-WAKE B1–B8 PASS;
   - P5-MEMORY save rate PASS, routing ⚠️ 9/10, bridge timing ⚠️ (both
     developer-acknowledged).
6. ✅ **TRACK MERGED**
   - kickoff `41585cfdff5f00ee6845fe12753bad8390573ebd` /
     `9b2ca57f94d42ea5a4a7388c8fddb5d649b1d7b1`;
   - P5-WAKE impl `fdfe3bf255e7c0847a90f241d9e03e6293434727` / merge
     `d20fbe96fc4af4bf78d48b753b2e3acfa2615418`;
   - P5-MEMORY impl `9a0e45991d45a7e0d191db2e8df864399551bf48` / merge
     `569d0d0f24414b3493586237d8039ae2866f93e8`.
7. ✅ **LORE CLOSEOUT** — this pass.

One-line track results:
- **P5-WAKE** — wake after clarify answer; B1–B8 PASS; reconcile
  diagnostics.
- **P5-MEMORY** — lasting-fact saving + routing + explicit-only search;
  save rate PASS; routing ⚠️ 9/10; bridge timing ⚠️.

## Phase 6 — COMPLETE: Memory Foundation
Phase 6 closed five tracks plus FIX-WHEN and FIX-2, then this lore pass.
"Complete" means the planned phase shipped — not that Zola's memory work
is done. Shipped: a local structured fact index (the flat files remain
the fact authority); episodic memory with consolidation and retrieval;
ambient temporal context; destructive forget with physical erasure; a
bounded calculator; and measured limitations (associative recall 0/4;
same-day "when" may still be omitted; notebook clarification is model
judgment). `S43` and `S42` resolved; `S14` foundation complete, not
resolved; `S35` arithmetic resolved (scopes remain).

1. ✅ **AUDIT** — P6PRE, merge `92dc707ac047d2808b9f1848bb0e31f96689065a`
   (audit commit `84f14d83db8efd7e495acbfa078a8da66b415683`).
2. ✅ **DECISIONS LOCKED** — `P6-D01`–`P6-D08` (Appendix A); decisions
   adopted during Phase 6: `P6-D09`–`P6-D11`.
3. ✅ **BUILD PLAN WRITTEN** — `PHASE6_BUILD_PLAN.md` v1.1, commit
   `187275981bdcbfcf3acd87a148bb0606a1c2d1e1`, merge
   `aee0f0da2ce0382c117013dc57f2cc32f1cd8370`.
4. ✅ **TRACKS EXECUTED** — five tracks + FIX-WHEN + FIX-2.
5. ✅ **VERIFICATION / SMOKE TEST** — per-track; recorded ⚠️: associative
   recall 0/4; forget_guard / deferred-sanitize not fired live;
   paraphrase-forget via fact-ref; R6 kiln PASS used an approved
   one-day seed (deviation).
6. ✅ **TRACK MERGED**
   - Plan: `aee0f0da2ce0382c117013dc57f2cc32f1cd8370`
   - P6-CALC: `5303e368969eaf60a68eb5950867ef302971119b`
   - P6-STORE: `79a0e3e7504eea98083b2f66066428bc69a56570`
   - P6-TIME: `1c7357e1f9f7c3927fa6e70763d1582b60143979`
   - P6-FORGET: `7b8f030b611372b5d2c35f0c460455916e781384`
   - P6-EPISODES: `8e12ff0c8226db0cd0ec95a881eabad166f7c00b`
   - P6-FIX-WHEN: `a2900eefae3b45222510962d5eb640e7641a0727`
   - P6-FIX-2: `fa6c7f078ab988a5c07c992f53f4c77b34521f5f`
7. ✅ **LORE CLOSEOUT** — this pass.

One-line track results:
- **P6-CALC** — bounded `calculate`; arithmetic cards gone; approvals stand.
- **P6-STORE** — local SQLite fact index beside the files; import/sync.
- **P6-TIME** — per-message stamps + cross-session gap; never read aloud.
- **P6-FORGET** — cascade erase; `forget_memory`; G-AUTHORITY / G-LABELS.
- **P6-EPISODES** — pending→consolidate→prefetch; G-ERASE; blind C2 PASS.
- **P6-FIX-WHEN** — SOUL: mention roughly when on recall.
- **P6-FIX-2** — "last weekend" interval + episodes-block say-when cue;
  R6 PASS (seeded).

## Phase 7 — COMPLETE: Voice She Can Trust
Phase 7 closed three tracks plus a read-only forensic pass; Track 4 was
cut. "Complete" means the planned phase shipped — not that voice work is
done. Shipped: transcript admission authority (her voice can't become
Brian's turn); voice clarify with spoken choices and the quiet card;
per-turn latency instrumentation and the first stage-level attribution;
the UTC offset in the time stamp. Measured limitations: latency was not
improved (causal target ❌); root cause identified as Hermes
`execution_guidance` outranking `SOUL.md`. `S45` and `S37` resolved;
`S44` partly resolved (remainder → `S57`); `S38` updated, not resolved;
`S34`/`S36` annotated.

1. ✅ **AUDIT** — P7PRE, merge `3e87e7c47ed2eee4a26f53dc9c4bba7d6f16b1ee`
   (audit content `044fe10a857edc364b0fa69cd2f72be5f45067d8`).
2. ✅ **DECISIONS LOCKED** — `P7-D01`–`P7-D13` (Appendix A); Brian
   (verbatim): "approved."; S34: "Yes. keep S34". Quiet-card reading of
   P7-D09 adopted during Track 2.
3. ✅ **BUILD PLAN WRITTEN** — `PHASE7_BUILD_PLAN.md` v1.1, commit
   `b5583f97c3e13870abc5d483ec23566458cd828e`, merge
   `ffef6f050a3fd6a8092d77fc055370296e2b522b`.
4. ✅ **TRACKS EXECUTED** — Tracks 1–3 merged; Track 4 cut; FORENSIC-SERVE
   read-only merged.
5. ✅ **VERIFICATION / SMOKE TEST** — per-track; recorded ⚠️: Track 1 S1
   PARTIAL at Starting (S1b PASS); Track 2 C3 adapted (composer in panel);
   Track 3 causal ❌ closed on findings (Brian: "C: close on findings
   (Recommended)"); serve APPCRASH class unresolved (`S51`/`S52`).
6. ✅ **TRACK MERGED**
   - Plan: `ffef6f050a3fd6a8092d77fc055370296e2b522b`
   - P7-VOICEAUTH: `3d264f07bb026c499c1fa8d82cce6dc71892f4e2`
   - P7-FORENSIC-SERVE: `512d91490be6317e6f644afc8051160b7cb560ef`
   - P7-CLARIFY: `80498b99f0e999efd91250fcc1c1d9315616bbb9`
   - P7-LATENCY: `7b168cfbb4daa95f5fa58307fd2377176f9ffd35`
   - Track 4 (VOICEPROSE): **cut** — Brian (verbatim): "Cut it; go to lore
     closeout (Recommended)"
7. ✅ **LORE CLOSEOUT** — this pass.

One-line track results:
- **P7-VOICEAUTH** — admission authority; cancel-before-stop; frozen
  terminal set; D06 hand-back; S45/S37 closed.
- **P7-FORENSIC-SERVE** — native APPCRASH class documented; filed `S51`/`S52`.
- **P7-CLARIFY** — spoken choices + quiet card; C1–C9/T1 PASS (C3 adapted).
- **P7-LATENCY** — `turn_timing`; stage attribution; UTC offset kept; SOUL
  Everyday reverted; closed on findings.
- **P7-VOICEPROSE** — cut (S-sentence ≈4%; depends on streaming-TTS choice).

## Phase 8 — COMPLETE: Google Workspace, Inside a Boundary
Phase 8 shipped Google Workspace through `zola_workspace` only. "Complete"
means the planned phase shipped. The boundary is the application, not the
operating system. `S16` is resolved. Send is a passphrase, not a card.

Shipped:
- the boundary: config and `.env` self-edit guard, terminal Google guard,
  self-modification rows, memory-taint guard, Brian-only (`platform == "tui"`,
  empty `parent_session_id`), cron exclusion, `code_execution` off `cli`,
  and `google-workspace`, `himalaya`, and `email-inbox-triage` retired;
- Calendar past and upcoming;
- read-only Gmail triage;
- Drive find and read (Docs, Sheets, Slides, text, PDF);
- Contacts lookup;
- Gmail drafts plus passphrase-approved sends;
- session taint and the memory guard, with the save-phrase amendment;
- the client `/compress` (`slash.exec`; a second press is held).

Recorded limits: residual terminal and self-modification paths were tested
as not blocked; summary selectivity was accepted and not fixed (`S67`);
the self-modification guard and the C2 replay were unit-tested, not live;
a long gist was not verified; a read-back interrupted mid-speech can already
count as reviewed; late cancel was proven by harness only, and after
`drafts.send` cancel is the Gmail round trip; a delete phrase followed by a
merged "don't delete" in the same turn still deletes; CONNECT C2 overwrote
a fact and the closeout line was wrong until P8-CONNECT-FIX. OAuth is in
Testing (about 7-day refresh tokens; weekly re-setup until published).

1. ✅ **AUDIT** — P8PRE, merge `26a8f0063dfe8f0919707b05cdf56d9fddbc8138`
   (audit content `fba2663d0fbb030b42a925b58e6de960e21327f6`).
2. ✅ **DECISIONS LOCKED** — `P8-D01`–`P8-D12` (Appendix A). Brian
   (verbatim, 2026-10-07): "approved." Publishing deviation (verbatim):
   "I went with test for now to keep things moving. I will work on setting
   up the site later."
3. ✅ **BUILD PLAN WRITTEN** — `PHASE8_BUILD_PLAN.md` v1.1, commit
   `49a3b86aee9d3c9401292a6bc1742ad92af197c7`, merge
   `89d395a60d8c9ece1252400e52ab51d1fa7c678b`.
4. ✅ **TRACKS EXECUTED** — HARDEN, CONNECT, CONNECT-FIX, READ, SEND merged.
5. ✅ **VERIFICATION / SMOKE TEST** — per-track. SEND closeout: five
   `drafts.send`, zero `messages.send`. Recorded ⚠️: C2 failed after its
   first closeout; R1 accepted, not fixed; S9 harness only.
6. ✅ **TRACK MERGED**
   - Plan: `89d395a60d8c9ece1252400e52ab51d1fa7c678b`
   - P8-HARDEN: `872e9eeabffacb6c7677d3f5eb57f52a3a3327dc`
   - P8-CONNECT: `74255bb309ed71f6d480222de5ec2b0893c2e0e7`
   - P8-CONNECT-FIX: `744787821ee4253f9c120f53273ab4c0a5e871e1`
   - P8-READ: `7f54b52c50022b3a553c58ceadb522f6a0fb021a`
   - P8-SEND: `89b41dfef585993d1d178590515e1ba602aad071`
7. ✅ **LORE CLOSEOUT** — this pass.

One-line track results:
- **P8-HARDEN** — posture veto, config guard, Brian-only, cron exclusion,
  `turn_id`.
- **P8-CONNECT** — OAuth in Testing, Calendar, taint, memory guard.
- **P8-CONNECT-FIX** — save phrase must lead; C2 repair; route labels.
- **P8-READ** — Gmail, Drive, Contacts, PDF; Office fail-closed; `/compress`.
- **P8-SEND** — drafts, passphrase send, 900 s review, send-time re-check.

## Current stage — Phase 9 (scope is Brian's call)
Candidates only (not a committed order); each with one line of evidence:
- **Workspace expansions (`S60`, `S61`, `S62`, `S64`, `S66`)** — mark read / archive
  / label, calendar writes, attachment bytes, Office extraction (an install
  decision), and proactive surfacing were deferred on purpose.
- **Summary selectivity (`S67`)** — triage summaries and one gist omitted
  addresses; Brian accepted the smoke and did not ask for a fix.
- **OAuth publishing (`S68`)** — Testing, about 7-day refresh tokens; production
  needs a homepage and a privacy-policy URL.
- **Voice I/O ownership study (`S56`)** — every upstream-blocked voice item
  sits in the voice/audio layer; Brian asked whether to fork. Related: `S69`
  (Hermes-injected text versus whole-message matches) and `S70` (no
  playback-completion signal).
- **`agent.execution_guidance` decision (`S54`)** — largest measured latency
  lever (tool rounds ≈ +8–12 s/turn; 17.8 s vs 5.4 s submit→audio). The
  Gmail skill route is gone; the decision stays open.
- **Backend crash / recovery (`S51`)** — five APPCRASHes in two days after
  zero 09-01→10-04; no automatic relaunch. Phase 8 added a process death on
  2026-10-08 whose replay carried an interrupted-turn note.
- **Memory round two (`S46`–`S50`, P6-D01 migration, `S63`)** — associative
  recall, fact-authority migration, and provenance that would allow an
  attributed save. Option B was not chosen.
- **Phase 7 voice items still open** — `S52` (stop-vs-silence race), `S55`
  (streaming TTS bake-off), `S57` (no cards in voice; Workspace sends are
  done, batch and command approvals are not), `S58` (smaller Whisper models),
  `S59` (`silence_duration`, data only).
- **Carried, not closed by Phase 8 (`S35`, `S40`, `S28`)** — session/always
  approvals; UI polish; session UI retirement (episodes exist; evaluate).
- **Also open from Phase 8: `S65`** — an OS-level credential boundary, if the
  application boundary proves insufficient.
- **Brainstorm intake (P9-KICKOFF, 2026-10-09; candidates, nothing decided)** —
  open loops (`S71`) as the foundation for proactive surfacing (`S66`; quiet
  first, and the `P8-D02` Brian-only conflict to resolve); background agents
  with HUD and spoken status (`S72`); Android companion and distributed
  presence (`S73`, strawman committed); remote escalation (`S74`, late);
  speaker and face recognition as signals (`S75`); Kasa lights (`S76`, small).


## Source documents
- Audit series: `zola-architecture/audit/winh-hermes-gap/`
- Master synthesis: `zola-architecture/audit/winh-hermes-gap/Zola_WINH00_MasterSynthesis.md`
- Companion strawman (v0.1, proposals only): `zola-architecture/Zola_Architecture_Distributed_Presence_Device_Capabilities.md`
