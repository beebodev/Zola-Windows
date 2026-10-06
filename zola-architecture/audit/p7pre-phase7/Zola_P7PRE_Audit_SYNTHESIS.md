# P7PRE Audit — Synthesis

**Pins:** client `7d77cb51`, Hermes `345cd2b0` / `v2026.9.14`  
**Prompt SHA-256:** `38A01D7CC707DA495FB823BA3C72CB147397A9A807E49A13111164E579C2C39F`  
**Date:** 2026-10-05  
**This document does not choose.** Decisions wait for the developer after review.

---

## Section 1 — Finding summary

| ID | Label | Severity | File | Summary |
|---|---|---|---|---|
| P7PRE-AUD-01 | [MATCH] | — | methods_voice.py / voice.py | RPC `voice.record` stop always force-transcribes |
| P7PRE-AUD-02 | [RISK] | HIGH | VoiceController.cs L2128–2157 | CancelFollowUp does not stop Hermes; typed-submit orphans capture (LEAD-1) |
| P7PRE-AUD-03 | [RISK] | HIGH | VoiceController.cs L2614–2642 | Echo guard end-anchored; head/middle drop ~0 (LEAD-3; H-2) |
| P7PRE-AUD-04 | [RISK] | MEDIUM | VoiceController.cs L2595–2612 | Haystack = streamed text, not Edge-spoken (LEAD-4) |
| P7PRE-AUD-05 | [MATCH] | — | turn_iteration_prep.py L318–325 | Busy interrupt builds `User correction during the turn:` (LEAD-2) |
| P7PRE-AUD-06 | [MATCH] | — | ChatSocket.cs L735–737 | `message.interim` dropped; not in haystack |
| P7PRE-AUD-07 | [RISK] | MEDIUM | zola_memory forget/provider | Echo can enter pending when disposition keep |
| P7PRE-AUD-08 | [GAP] | HIGH | VoiceController / MainWindow | No single provenance authority for “this is Brian” |
| P7PRE-AUD-09 | [RISK] | HIGH | voice-timeline + state.db | E1/E2 + L-3 whole-turn echoes take LEAD-1 path |
| P7PRE-AUD-10 | [MATCH] | — | state.db / VT | History reports candidates; confirmed only with timeline |
| P7PRE-AUD-11 | [GAP] | LOW | zola_memory.db | No episodes at audit; fact contamination unproven |
| P7PRE-AUD-12 | [RISK] | MEDIUM | MainWindow / VC clarify | LEAD-5 partly; unbound routing + short miss |
| P7PRE-AUD-13 | [GAP] | MEDIUM | MainWindow L1557–1559 | No-card Voice breaks batch voice answers |
| P7PRE-AUD-14 | [GAP] | MEDIUM | VoiceController L656–667 | Choices never spoken |
| P7PRE-AUD-15 | [MATCH] | — | MainWindow | Text keeps card; approvals never voice |
| P7PRE-AUD-16 | [GAP] | MEDIUM | logs | Dominant EoS→audio bucket under-instrumented |
| P7PRE-AUD-17 | [GAP] | MEDIUM | transcription_local.py L170 | beam_size/cpu_threads not config keys |
| P7PRE-AUD-18 | [GAP] | LOW | voice_mode VAD | Cannot judge shorter silence from logs alone |
| P7PRE-AUD-19 | [GAP] | LOW | methods_prompt voice-live | Voice-only note needs client surface or Hermes edit |
| P7PRE-AUD-20 | [RISK] | MEDIUM | VoiceController release | Rare estimate paths can open while speaking |
| P7PRE-AUD-21 | [MATCH] | — | voice-timeline | Monitor 95.6% of releases (LEAD-7) |
| P7PRE-AUD-22 | [MATCH] | — | H-1 harness | Warm STT ~0.75s; beam1 no win; lang already en |
| P7PRE-AUD-23 | [RISK] | MEDIUM | VoiceController transcript window | L-3 Run B: stale capture_start/stop on echo transcript line |
| P7PRE-AUD-24 | [MATCH] | — | L-4 live | Clarify voice path works: speak Q → bound capture → answer → verbal reply |
| P7PRE-AUD-25 | [RISK] | MEDIUM | L-2.1 / L-2.2 agent.log | Simple questions used `skill_view`/`terminal` (+ approval); not `calculate` |
| P7PRE-AUD-26 | [GAP] | MEDIUM | agent.log / H-1 | Live warm WAV→Transcribed ≫ H-1 warm infer; UNEXPLAINED without infer markers |

**Totals:** 26 findings — **4 HIGH**, **11 MEDIUM**, **3 LOW**, **8 MATCH**

---

## Section 2 — Build plan implications (GAP / RISK only)

**P7PRE-AUD-02 / 08 / 09 (S45 authority).** Any Phase 7 build that leaves `CancelFollowUp` without stopping Hermes will keep reproducing whole-turn echoes when Brian types with Voice mode on. A single client-side provenance gate is the missing authority; content echo alone cannot close the matrix.

**P7PRE-AUD-03 / 04.** End-anchored haystack-from-streamed-text will keep missing head echoes and mis-scoring spoken vs written forms. Un-anchoring or spoken haystack are content defenses only.

**P7PRE-AUD-07.** Pending rows from echoed turns are live contamination until consolidator runs; forget fail-closed helps only when disposition was marked.

**P7PRE-AUD-12 / 13 / 14 (S44).** Voice-only clarify needs S45 so the answer capture is Brian-only; also needs a non-card channel for choices and broker-backed batch state.

**P7PRE-AUD-16 / 17 / 18 / 26 (S38).** Felt delay is dominated by model+tools+TTS after submit on live turns; STT warm log median ~1.66 s vs H-1 warm infer ~0.75 s (AUD-26 UNEXPLAINED). Profile knobs (silence, language pin, cpu/int8) are small; beam_size needs Hermes edit; smaller models need `P2-D17` download.

**P7PRE-AUD-19 / 20 / 21 (S34 / S37).** S37 is small (monitor-dominated). S34 voice shaping needs a client `surface` signal or upstream. Estimate early-open remains a minor S45 feeder.

**P7PRE-AUD-23.** Capture-window logging can disagree with Hermes’s actual recording interval — weakens provenance debugging.

**P7PRE-AUD-25.** Simple factual voice questions (Tokyo time; cups in a quart) invoked `skill_view`/`terminal` (and an approval card on L-2.2), not `calculate` — outside calculate’s scope; not evidenced as a P6-D08 calculator regression (`calculate` never called). Cost: submit → approval card ≈ **5.7 s**.

---

## Section 3 — Pre-work required

- Developer decisions on synthesis §5 (especially 5.1 S45 authority and 5.2 contamination cleanup) before the Phase 7 build.
- Optional: Whisper model downloads under `P2-D17` if STT model swaps are chosen. ffmpeg is already installed (used for L-1 under P2-D17); no ffmpeg install pre-work.
- No other pre-work (hashes clean; hermes pin clean).

---

## Section 4 — Assumptions confirmed (MATCH)

- RPC stop force-transcribes (AUD-01).
- Busy interrupt redirect string assembly (AUD-05).
- Interim messages dropped client-side (AUD-06).
- Echo-candidate vs confirmed-echo discipline (AUD-10).
- Text clarify card + approvals never voice (AUD-15).
- Monitor-dominated follow-up release (AUD-21).
- H-1 warm STT characteristics (AUD-22).
- Live clarify voice path works today (AUD-24).

---

## Section 5 — Open questions for the developer

### 5.1 S45 — who decides “this is Brian”

| Shape | Class | Belongs to Brian vs resembles Zola | Closes matrix cells | Revises P2-D05/D12/D14? | Hermes edit? | Fail | Genuine speech lost |
|---|---|---|---|---|---|---|---|
| A. Stop Hermes on every cancel + drop forced transcript | Provenance | Belongs (cancel → not current) | Orphan CAP / Stop / typed-submit | **Yes** (revises P2-D05 — drops a transcript) | No | Closed if stop+drop atomic | Forced transcript of real speech after cancel |
| B. Drop/hold transcripts while turn running (unless clarify-bound) | Provenance | Belongs (time/state) | TurnRunning cells | **Yes** (revises P2-D12) | No | Closed on hold timeout policy | Mid-turn barge speech if ever enabled |
| C. Echo guard on every capture | Content | Resembles only | Wake/mic gaps | Revises P2-D14 eligibility | No | Open (misses head) | Brian quoting her |
| D. Un-anchor guard (head/middle) | Content | Resembles only | Head-echo cells | Revises P2-D14 end-anchor | No | Open | Quotes / shared phrases |
| E. Haystack from spoken text | Content | Resembles only | LEAD-4 misses | Implementation of D14 | No* | Open | Same as C |
| F. No capture while bout active | Provenance/state | Belongs (playback) | Reply-finished/audio playing | No | No | Closed while bout known | Instant answers in residual ~1 s (P4-D18) |
| G. Change `busy_input_mode` | Hermes policy | Neither (downstream) | Redirect landing only | No | Profile only | Open (still submits) | Steer/queue UX change |
| H. A+B (+ optional F) | Defense-in-depth | Belongs first | Orphan + mid-turn | Yes (inherits A+B) | No | Closed | Cancel-edge true speech |

\*Spoken haystack may need TTS text events; still client-side if Edge text is known.

**Today (split authority):**

```
mic → Hermes capture → voice.transcript → VoiceController
        (gate / stop / no-speech / echo-if-follow-up)
      → MainWindow (clarify bind vs prompt.submit)
      → Hermes busy (queue|steer|interrupt) → memory provider
```

**Shape A+B (example single client decision point):**

```
mic → Hermes capture → voice.transcript → [CLIENT AUTHORITY]
        provenance: current capture? cancelled? turn running? clarify-bound?
        optional content echo
      → clarify answer OR prompt.submit OR drop
      → Hermes busy → memory
```

#### 5.1a Feasibility — can the client attribute `voice.transcript` to a specific capture?

**Evidence:**

| Fact | Source |
|---|---|
| Hermes `VoiceTranscriptPayload` fields are `text` / `stop_phrase` / `typed` / `no_speech_limit` only — **no capture ID** | `events.py` L617–623 |
| Client-driven record uses `auto_restart=False` | `methods_voice.py` L752 |
| Client capture-window bookkeeping can be **stale** vs Hermes’s actual record interval | AUD-23 / L-3 Run B |

**Ordering (one capture at a time) is not enough alone.** Usual path is single-flight client start/stop, but attribution breaks when:

1. **Cancel without Hermes stop** (LEAD-1 / AUD-02): flags clear while Hermes keeps recording → late transcript has no binding capture id and often skips echo eligibility.
2. **Stop racing silence auto-stop:** client `voice.record` stop and Hermes VAD silence both end the same recording; the client’s `_captureWindowStart/Stop` (AUD-23) can disagree with Hermes’s interval.
3. **Late transcript after a new start:** a transcript from an orphaned prior capture can arrive after a new `NoteCaptureWindowStarted`, so log fields (and any order-based attribution) attach to the wrong window.

Without a Hermes-supplied capture ID (or equivalent correlation token), the client can only infer by timing/flags — AUD-23 shows that inference already mis-labels live turns.

### 5.2 S45 cleanup

| Item | Fate (facts from `zola_memory.log` + store) | Options |
|---|---|---|
| L-2 pending `b538748c…`, `3e1ef784…`, `35421edf…` (session `20261005_130256_aef4be`) | **Consolidated into nothing** — `2026-10-05 19:03:14` `trigger=quiet turns=3 episodes=0 ok=true` (not a failed consolidate) | none left in pending |
| L-3/L-4 tagged seven IDs `d518805a…` … `5b2aff76…` (session `20261005_192949_1f4302`) | **Same drain** — `2026-10-05 19:46:03` `trigger=quiet turns=7 episodes=0 ok=true`; store now `pending_turns=0` | none left in pending |
| Store episodes | **episodes=0** throughout; these quiet consolidations produced **zero episodes** (facts still 16) | — |
| Historical E1/E2 in `state.db` session `20261004_213345_e1ca3d` | Chat history only; not in pending | leave / flag |

**Will the seven tagged IDs drain the same way?** They already did: same `quiet` path, `episodes=0`, pending cleared. No episodes were produced. Facts unchanged (16).

**P7PRE did not clean up.** LIVE-PROBE-CONTAMINATION IDs remain the audit tag for those former pending rows (now absent from store via consolidator, not auditor delete).

### 5.3 S44 — voice-only clarify shapes

| Topic | Options | Needs from 5.1 |
|---|---|---|
| Choices heard | Speak choices in TTS; or accept free-text only; or card for choices-only | Capture must be Brian-only |
| Skip/cancel words | Add phrases vs collide with `stop` | — |
| Multi-select / batch | Voice protocol vs **card fallback for batch only** | Provenance bind per answer |
| Timeout / late drop | Keep broker timeout; late-drop stays on abandon (not card) | — |
| Panel | Do not auto-open on clarify | — |

### 5.4 S38 — latency

**EoS → first audible (live):**

| Turn | EoS→audio | Dominant share |
|---|---:|---|
| L-2.1 (cold+tools) | ~20.1 s | model+tools+TTS ~78% |
| L-2.2 (warm+approval) | ~17.8 s wall | human approve + model |
| L-2.3 (warm, no card) | ~10.1 s | model ~51%, STT ~20%, silence 15%, TTS ~14% |
| Log median (Phase 5) | ~8.6 s | model+TTS bucket ~62% |

**Live STT vs H-1 (AUD-26):** Phase-5 warm WAV→Transcribed median **~1665 ms**; L-2 warm turns **1857 / 2028 ms** (audio **4.1 / 5.7 s**). L-1 H-1 clips **3.69–6.78 s**, warm infer median **~0.75 s**. Durations overlap; gap not explained by longer audio. Wake stream closed during STT; presence only routine blinks — no logged CPU-contention proof. **UNEXPLAINED** without `whisper_infer_start` / `whisper_infer_end`.

**Candidates ranked by measured/estimated saving (not a choice):**

| Rank | Candidate | Saving | Risk | Type |
|---|---|---|---|---|
| 1 | Reduce model/tool path / TTFT (needs instrumentation) | largest bucket | quality | client/plugin/model |
| 1a | Simple questions answered without tools (AUD-25) | L-2.2 submit→card ≈ **5.7 s** avoided when no tool/approval | quality / tool policy | model/tools |
| 2 | Warm STT already ~0.75 s (H-1); smaller model; close AUD-26 gap | est. 30–50% of STT / ~0.9 s if live→H-1 | WER; **P2-D17 download**; need infer markers | profile+install+logs |
| 3 | `silence_duration` 1.5→1.0 | 500 ms | cutoffs | profile |
| 4 | Pin cpu/int8, lang en | ~0 on this machine (already en/cpu-like) | — | profile |
| 5 | beam_size 1 | ~0 ms H-1; WER↑ | accuracy | **Hermes out** |
| 6 | S23 warm-up | cold first turn only | RAM | Hermes/feature |

Install-sized candidates: tiny.en ~75 MiB, base.en ~145 MiB, distil-small.en ~166 MiB, small.en ~466 MiB.

### 5.5 S34

| Option | Evidence |
|---|---|
| Adopt `voice-live` surface from client | Adds speakable-prose note; unused today |
| Zola plugin voice-only note | **No** voice signal without client param |
| Leave as is | Chunker min_len=20; markdown normalize exists |

### 5.6 S37

| Option | Evidence |
|---|---|
| Keep | Fallback for 4.4% estimate/forced |
| Fold into 5.1 | Early-open estimate paths feed S45 |
| Close | Monitor 95.6% — residual small |

### 5.7 Dependencies / order (facts)

- **S44 voice-only clarify depends on S45** (answer capture must be Brian).
- **S34 whole-line synthesis interacts with S38** (first audio) and **S45** (haystack mismatch).
- **S37 folds into S45** if early capture open is treated as provenance.
- **S38 STT knobs** independent of S45; **S38 model/TTS** independent but dominates felt wait.
- **S38 tool misuse on simple questions (AUD-25)** is independent of S45; it inflates the post-submit bucket (L-2.1 tools; L-2.2 terminal + approval ≈ 5.7 s submit→card) and is outside `calculate` / not a measured P6-D08 regression.
- **S38 STT live vs H-1 gap (AUD-26)** needs Hermes `whisper_infer_start`/`end` before attributing the ~0.9 s to model choice vs scheduling.
- Contamination IDs in 5.2 already drained via consolidator (`episodes=0`); no auditor cleanup. Developer still decides whether chat-history echoes need forget/flag.

---

## Section 6 — LEAD outcomes

| LEAD | Outcome | Finding |
|---|---|---|
| LEAD-1 | **Confirmed** (code + E1/E2 + L-3) | AUD-02, AUD-09 |
| LEAD-2 | **Confirmed** (code); mid-turn redirect **not** live-reproduced in L-3 | AUD-05 |
| LEAD-3 | **Confirmed** (code + H-2) | AUD-03 |
| LEAD-4 | **Confirmed** | AUD-04 |
| LEAD-5 | **Partly** (guard runs on bound clarify; unbound/short miss) | AUD-12 |
| LEAD-6 | **Partly** (device/lang yes; beam_size no) | AUD-17 |
| LEAD-7 | **Confirmed** (196/205 monitor) | AUD-21 |

**LEADs:** 5 confirmed / 0 refuted / 2 partly.
