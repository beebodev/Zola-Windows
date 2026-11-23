# SPEECH-PRE Audit — Progress

**Prompt:** `C:\Users\test\Dev\zola-spikes\prompts\SPEECH-PRE_Audit_Prompt_v1.0.md`  
**Prompt SHA-256 (verified):** `f1cba41957591a555edea335e3a676b39cac4d200bb0fd3e796d1ec96c8ee8c4`  
**Branch:** `speech-pre-audit`  
**Base:** `main` = `origin/main` = `bc4fd8b4dab18da2b0026d7423825d5715e75500` (clean tree at branch create)  
**Hermes pin:** `345cd2b057a452236de401d3534b8502a7465e8d` (HEAD match, clean tree)  
**Finding IDs:** `SPEECHPRE-AUD-NN`  
**Started:** 2026-11-23  
**Phase 11 STOP:** 2026-11-23 — synthesis ready for Claude; closeout waits for `proceed to closeout`.

## Attached Document of Truth (speech track) — hashes

| File | Path used | SHA-256 |
|------|-----------|---------|
| SPEECH-PRE prompt v1.0 | `zola-spikes\prompts\SPEECH-PRE_Audit_Prompt_v1.0.md` | `f1cba41957591a555edea335e3a676b39cac4d200bb0fd3e796d1ec96c8ee8c4` (MATCH expected) |
| SPEECH_DECISIONS.md (with SP-D10) | `zola-spikes\prompts\speech-pre-inputs\SPEECH_DECISIONS.md` | `2c618bc95023941b1b870c24c8766d7e75865fb16866a689a672a55104991b7e` (MATCH expected) |
| SPEECH_SPIKE_2_PAUSED.md | `zola-spikes\prompts\speech-pre-inputs\SPEECH_SPIKE_2_PAUSED.md` | `8b19fe05f791ba73c63a5b61792a4e701eea1a28cf0249ff66ed8e67018c6214` (MATCH expected) |
| SPEECH_SPIKE_1_CLOSED.md | `zola-spikes\speech-spike-2\docs\SPEECH_SPIKE_1_CLOSED.md` | `d82b69e9dd8a1050bd3d0ca24a86dc9973d92cc0eb03311deda01412baab0ef5` |
| SPEECH_BASELINE_RESULTS.md | `zola-spikes\speech-spike-2\docs\SPEECH_BASELINE_RESULTS.md` | `ffb6fcb34184d70cd55a70da0f0b2e08f451cd2383aea5decabfa2b8d758bcf9` |
| VOICE_SCOPING_NOTE.md | `zola-spikes\prompts\VOICE_SCOPING_NOTE.md` | `b85c68c41d9b5fcecc3c5a1b1f77a697fcebe848354934726e6b50916f8c9780` |
| NUPLEX_FRONTEND_DIRECTION (background only) | `zola-arch-drafts\nuplex\NUPLEX_FRONTEND_DIRECTION_2026-11-22.md` | `be6d86a7cac653c0a360993e2a3f614f75faf865aea01015c029e4a9b4e7a100` |

Older `SPEECH_DECISIONS.md` copies under spike `docs\` (no SP-D10) ignored per Brian.

## Spike folder listings (Phase 1)

| Folder | File count (recursive) | Listing store |
|--------|------------------------|---------------|
| `speech-spike-2` | 6594 | agent store `spike2_listing_before.txt` |
| `speech-spike` | 3179 | agent store `spike1_listing_before.txt` |

Re-check at closeout (Phase 12a).

## Guardrails (summary)

G-SCOPE diagnostic only · G-NOCHANGE · G-NO-AUDIO · G-NO-RESTART · G-SECRETS · G-LOGS · G-ARCH · G-QUALITY · G-HONEST · G-NO-DESIGN · G-NO-CROSS-SCOPE · G-CLOSEOUT only on "proceed to closeout".

## Phase table

| Phase | Doc | Status |
|-------|-----|--------|
| 1 Readiness | `Zola_SPEECHPRE_Audit_01_Readiness.md` | COMPLETE — readiness PASS; crashes since watch = 0 |
| 2 Speaking | `Zola_SPEECHPRE_Audit_02_Speaking.md` | COMPLETE |
| 3 Listening | `Zola_SPEECHPRE_Audit_03_Listening.md` | COMPLETE |
| 4 Hermes seams | `Zola_SPEECHPRE_Audit_04_HermesSeams.md` | COMPLETE |
| 5 Owner placement | `Zola_SPEECHPRE_Audit_05_OwnerPlacement.md` | COMPLETE |
| 6 Spike vs Zola | `Zola_SPEECHPRE_Audit_06_SpikeVsZola.md` | COMPLETE |
| 7 Boundary | `Zola_SPEECHPRE_Audit_07_Boundary.md` | COMPLETE |
| 8 Devices/privacy | `Zola_SPEECHPRE_Audit_08_DevicesPrivacy.md` | COMPLETE |
| 9 Tests/refactor | `Zola_SPEECHPRE_Audit_09_TestsRefactor.md` | COMPLETE |
| 10 Missing evidence | `Zola_SPEECHPRE_Audit_10_MissingEvidence.md` | COMPLETE |
| 11 Synthesis | `Zola_SPEECHPRE_Audit_SYNTHESIS.md` | COMPLETE — STOP for Claude |
| 12 Closeout | — | COMPLETE |

## Readiness verdict

**PASS** — no open serious voice/speech issue (KI-S51-PA mitigated/watching); live serve crashes since 2026-11-16 07:43:37 = **0**.

## Findings (through Phase 11)

**27** — SPEECHPRE-AUD-01 … AUD-27 · **7 HIGH · 12 MEDIUM · 8 LOW**

## Hermes seams snapshot

| Seam | Label |
|------|-------|
| TTS disarm (turn stream) | MATCH |
| TTS disarm (`voice.tts`) | RISK |
| Mic+wake disarm | MATCH (ops) / GAP (no guarantee RPC) |
| Reply deltas | MATCH |
| Reply complete | MATCH |
| Tool events | MATCH |

## Owner placement (Cursor’s)

**(b) separate supervised Python process** — decision for Brian.

## Spike rules (Phase 6 table)

kept 0 · superseded 1 · extended 5 · new 7 (+ partial/unproven notes; echo/D7(a) called separately)

## Refactor-first candidates

`VoiceController.cs` (4447 lines) — AUD-27. Optionally thin seam vs full refactor track.

## Missing evidence that blocks plan shape

Owner placement (Brian); wake-under-owner strategy; `voice.tts` disarm policy. Bluetooth Part G blocks BT claim, not Realtek-first wave.

## Closeout SHAs (Phase 12)

| Record | SHA |
|--------|-----|
| Audit commit (12d) | `8bdd4347445e68d8e89e21da1b415bb0e7426684` |
| Tip SHA commit (12e) | _(this commit)_ |
| Merge to `main` (12g) | _(pending)_ |

**12a:** changes only under `zola-architecture/audit/speech-pre/`; hermes-agent clean at pin; spike listings identical (6594 / 3179).  
**12b:** privacy scan — 0 transcript/reply/email/message/memory content hits; 0 key-like strings (false positives only: test names / table rules).  
**12c:** phases COMPLETE; findings **27** (7 HIGH, 12 MEDIUM, 8 LOW).
