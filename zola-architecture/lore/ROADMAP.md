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
## Current stage — Phase 4 complete
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

## Phase 5 — not started
Scope TBD; await developer instruction. Candidates (not a committed order):
- `S36` — Barge-in return (state-aware). **Listed first.**
- `S41` — Wake/mic not restored after clarify until Text↔Voice toggle.
- `S33` — Non-interactive Windows states + Modern Standby.
- `S34` — Hermes chunking / voice-only shaping / `voice-live`.
- `S35` — Approval scopes / `approvals.mode`.
- `S37` — Estimate anchor on first reply text.
- `S38` — Listen-to-think latency.
- `S39` — Voice timbre (premium provider).
- `S40` — UI polish (Esc, notice hold, activity batch).
- `S17` — Audio-driven lip sync / true end-of-playback (remainder).
- `S21` — Typed Cancel latch (remainder).
- `S26` — Missing `message.complete` / resumed-running (remainder).
- `S12` — Daily Brief pipeline.
- `S13` — SMS-reading research.
- `S16` — Google Workspace.
- `S24` — GLB asset rework.
- `S25` — HUD data sources.
- `S31` — Helix reload memory.

## Source documents
- Audit series: `zola-architecture/audit/winh-hermes-gap/`
- Master synthesis: `zola-architecture/audit/winh-hermes-gap/Zola_WINH00_MasterSynthesis.md`
