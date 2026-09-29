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
## Current stage — Phase 3 complete
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
## Phase 4 — not started
Candidates for Brian to prioritize. Not a committed order. No plan yet.
- `S32` — Voice active while Windows is locked (security/privacy). Listed
  first.
- `S17` — Audio-driven lip sync / precise speaking end (remainder).
- `S22` — Voice naturalness (pacing and inflection).
- `S16` — Google Workspace (Gmail, Calendar, Drive, Contacts).
- `S20` — Client cannot answer Hermes clarify-tool requests.
- `S24` — GLB asset rework.
- `S25` — HUD data sources (includes ALERT trigger).
- `S13` — SMS-reading research.
- `S12` — Daily Brief pipeline.
- `S31` — Helix reload memory.

## Source documents
- Audit series: `zola-architecture/audit/winh-hermes-gap/`
- Master synthesis: `zola-architecture/audit/winh-hermes-gap/Zola_WINH00_MasterSynthesis.md`
