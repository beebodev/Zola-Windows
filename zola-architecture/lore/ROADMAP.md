# Zola-Windows Roadmap
Status tracking for the Windows-native rebuild of Zola on Hermes Agent
(pinned tag `v2026.9.14` / `345cd2b057a452236de401d3534b8502a7465e8d`).
## Current stage — Phase 1 complete
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
## Phase 2 — not started
Candidates for Brian to prioritize. Not a committed order.
- Google Workspace Integration (Gmail, Calendar, Drive, Contacts) —
  the deferred Track 5/6 work, properly scoped (see S16).
- Visual/UI theme work — the "Obsidian Interface" look (presence
  portrait, gold/black palette, bottom nav bar, attention-level
  indicator) discussed during Track 3 and left out of that track.
- Voice — Zola is intended to be primarily voice-driven, with text as
  a fallback toggle, per the Master Architecture Plan's Vocal Computing
  pillar. No voice work exists yet. Track 1's client is text-only, as
  a starting point.
- `S13` (SMS-reading research) — already open, untouched by Phase 1.
- `S12`'s Daily Brief pipeline — already deferred, untouched by Phase 1.
## Source documents
- Audit series: `zola-architecture/audit/winh-hermes-gap/`
- Master synthesis: `zola-architecture/audit/winh-hermes-gap/Zola_WINH00_MasterSynthesis.md`
