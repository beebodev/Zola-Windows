# SPEECH-PRE Audit 06 — Spike rules vs Zola decisions and code

Spike MEASURED results quoted from spike docs only (not re-claimed as measured here). Talk-over parked (SP-D10).

---

## Rule table

| Spike rule (file:line) | Closest Zola decision + code | Status | Consequence | Risk |
|------------------------|------------------------------|--------|-------------|------|
| Mic from `safe_to_listen` (IAudioClock drain + 220 ms) — `owner.py:22–33,835–863`; `wasapi/render.py:239–262`; `gate.py`; `config_frozen.json:23` | P7-D06 / P4-D18 / P2-D15: monitor 450 ms + 0.5 s quiet + estimate (`TtsPlaybackMonitor`; `VoiceController` follow-up) | **Superseded** (listen release) | Follow-up only after device drain + 220 ms | Wrong clock → premature listen again |
| 500 ms pre-roll never into playback — `config_frozen.json:22`; `boundary.py`; gate `block` | No record pre-roll today | **New** | Opening words kept | Gate leak includes her |
| Silero VAD — `listener/vad.py`; pin in freeze | Hermes `silence_duration` 1.5 s | **New** | Endpointing in listener | Mistune cut/lag |
| 0.3 s provisional / 2.5 s merge — `continuation.py`; config | Hermes 1.5 s silence; no merge | **New** | Median reply start ~0.32 s (spike MEASURED) | Split turns if resume broken |
| S1 Zipformer + S3 Parakeet local — `stt.py`; VD-4 | P2-D02 faster-whisper | **Extended** (supersedes model choice) | Local streaming + final | CPU; rare-word misses |
| Reply IDs — `owner.py`; `cartesia.py` | Clarify id only; no TTS reply_id | **New** | Late audio droppable | Silent drop if mismatch |
| Explicit outcomes — `owner.py` complete/failed/cancelled | P9-D11 delivered/uncertain; A06/A07 §10.5 | **Extended** | Map to A06 outcomes for all lines | Semantic gap: no named `uncertain`/`partial` in owner enum |
| Drain-idle failure timeout — `owner.py:776–828` | None | **New** | Never false `safe_to_listen` | Too short → false fail |
| `listen_open(after_release)` after cancel/fail | Prompt rule; owner releases without `safe_to_listen` on fail | **New** / partial impl | 220 ms then listen after non-interrupt fail | Missing named event |
| ≤1 `would_submit` per capture | P7-D01 / P7-D03 | **Extended** | Feed single admission | Dual-fire if Hermes path left live |
| Late audio/partials/finals by id | P7-D02 cancel drops | **Extended** | Drop late Cartesia/STT | Need capture-id discipline |
| Mic loss/recovery | Prompt; Part E not scored | **New** / unproven | Discard in-flight; reopen | Blind until measured |
| Stop speed (~2.5 ms cancel; ~77 ms silent) — spike MEASURED Part 1 | ffplay kill / toggle off | **New** (owned renderer) | Hard stop + unplayed frames | Piece-size trade-off |

**Counts (this table):** kept 0 · superseded 1 (listen-release stack) · extended 5 · new 7 (+ partial/unproven notes). Echo matcher / D7(a) product called out below separately.

---

## 1. Mechanisms that become unnecessary / need new decision IDs

| Mechanism | Fate |
|-----------|------|
| Playback monitor as **listen** authority | Unnecessary for mic open; may remain for mouth (P3-D23) |
| Estimate releases | Unnecessary for listen |
| 450 ms + 0.5 s quiet | Superseded by drain + 220 ms |
| Echo matcher P7-D07 | Unnecessary as **primary** defense if gate never admits her; optional depth until live proof |
| 2 s echo tail (proactive) | Technically unnecessary once EOS+gate proven; **D7(a) product** separate |

**Need new SP-* IDs** to supersede: P7-D06/P4-D18 listen timing; P2-D02 model; adopt owner (SP-D04 adoption); endpointing; reply ids; outcome mapping; optional retire P7-D07 / echo tail.

**SPEECHPRE-AUD-21 [GAP] HIGH** — Lore still encodes monitor+estimate listen release; speech track must issue superseding decisions before build treats them as truth.

---

## 2. Exact EOS and lifting D7(a) — facts only

Exact EOS removes the technical cause of premature listening. That makes **lifting D7(a) possible**. It does **not** auto-lift it (P9-SPEAK product choice). Also touched if lifted: A07 engagement follow-up, A06 §6, SP-D01, `SpeechEchoGuard`, proactive coordinator gates, A11 delivery. **Brian’s decision.**

---

## 3. Playback outcomes (A06 / A07 §10.5)

| A06/A07 | Owner evidence |
|---------|----------------|
| completed | `released` complete after drain + 220 ms → `safe_to_listen` |
| partial | cancel: `playback_stopped` + unplayed frames / `heard_up_to` (talk-over harness; parked) |
| failed | `no_final_marker`, drain/connect failures |
| uncertain | Not first-class in owner; map e.g. start without trustworthy drain (like P9 `delivery_uncertain`) |

Ordinary replies today lack a delivery ledger; proactive has P9-D11.

---

## 4. Harness vs mechanism

**Mechanism (port):** `owner.py`, `wasapi/*`, `listener/{gate,vad,boundary,continuation,stt,__init__}`, `adapters/cartesia.py` (+ base), `common/{clock,events}`, frozen thresholds.

**Harness only:** `runner.py`, `immediate_reply.py`, `talkover.py`, offline/scoring scripts, `connection_guard`, `device_gate`, schedules.

**Replay-mostly:** `adapters/replay.py`, offline `SpeakingGate(intervals=…)`, AEC tune. Live Phase 3 used real Cartesia + Realtek.

---

## 5. STT findings (spike progress — facts)

- Opening captured 10/10 (Phase 3); STT accuracy separate.
- Charlie / Kilo first-word misses (S3); S1 sometimes keeps what S3 drops.
- Options (S1∪S3 opening / hotwords) noted, **not tested or decided**.
