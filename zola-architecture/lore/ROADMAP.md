# Zola-Windows Roadmap
Status tracking for the Windows-native rebuild of Zola on Hermes Agent
(pinned tag `v2026.9.14` / `345cd2b057a452236de401d3534b8502a7465e8d`).
## Current stage — Phase SOP (`Phase_SOP_Generic.md`)
1. ✅ **AUDIT** — WINH01–WINH12 + WINH00 synthesis, complete. 187 findings
   across 12 domain audits (55 HIGH / 102 MEDIUM / 27 LOW / 3 OBSERVATION).
   Merged to `main` at `da6c35fd997487db23bb15c08eb9056e28413e39`.
2. 🔶 **DECISIONS LOCKED** — in progress. See `DESIGN_DECISIONS.md` for
   resolved items, `OPEN_QUESTIONS.md` for what's left.
3. ⬜ **BUILD PLAN WRITTEN** — not started. Blocked on Decisions Locked
   completing, and on the two architecture docs called for in `C9`/`C10`
   (capability-acquisition, tool-authorization) once the Security and
   Authorization decision buckets are resolved.
4. ⬜ **TRACKS EXECUTED** — not started.
5. ⬜ **VERIFICATION / SMOKE TEST** — not started.
6. ⬜ **TRACK MERGED** — not started.
7. ⬜ **LORE CLOSEOUT** — not started.
## Source documents
- Audit series: `zola-architecture/audit/winh-hermes-gap/`
- Master synthesis: `zola-architecture/audit/winh-hermes-gap/Zola_WINH00_MasterSynthesis.md`
