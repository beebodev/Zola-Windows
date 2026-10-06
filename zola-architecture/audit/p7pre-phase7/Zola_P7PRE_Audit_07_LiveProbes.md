# P7PRE Audit 07 — Live Probes

**Started:** 2026-10-05  
**Pins:** client `7d77cb51`, Hermes `345cd2b0`

---

## P2-D16 machine setup

| Item | Brian's answer |
|---|---|
| Lid open | **yes** |
| Mic input 100 | **yes** |
| Windows audio enhancements ON | **yes** |
| Speakers about 15 | **yes** |
| Differences | **none listed** |
| Same during L-1? | **yes** (implied by “Proceed to L-2” with no differences) |

**Confirmed:** 2026-10-05 (Brian, verbatim checklist).

---

## L-1 — Scripted recordings (complete)

**When:** 2026-10-05 ~17:51–17:53  
**Location:** `C:\Users\test\Dev\zola-spikes\p7pre\audio\`  
**Format as saved by Brian:** `.m4a` (`L1-1` … `L1-6`)  
**Scratch conversion:** 16 kHz mono `.wav` via already-installed WinGet ffmpeg (no new package install)

| File | Bytes (m4a) | WAV duration (s) | Script line |
|---|---:|---:|---|
| L1-1 | 95391 | 3.69 | What time is it in Tokyo right now? |
| L1-2 | 96010 | 3.73 | Remind me how many cups are in a quart. |
| L1-3 | 116311 | 4.52 | Okay, and what about the one after that? |
| L1-4 | 158985 | 6.17 | Can you add eggs, flour, and two lemons to the list? |
| L1-5 | 173632 | 6.78 | Hmm, let me think. Actually, no, make it Thursday. |
| L1-6 | 126508 | 4.93 | Read me the last thing you said again, slowly. |

**H-1:** run complete — see `Zola_P7PRE_Audit_06_Harness.md`. Warm median infer ≈ **0.75 s**; median WER ≈ **0.15** on effective config.

---

## L-2 — Timed voice turns (COMPLETE)

**Deviation:** Planned “new session”; actual Hermes session was the **existing** serve session `20261005_130256_aef4be` (not a new session id).

**Pre-L2 log offsets (2026-10-05 ~18:06):**

| File | Bytes |
|---|---:|
| `voice-timeline.log` | 779805 |
| `display-state.log` | 877005 |
| `presence.log` | 44936573 |
| `agent.log` | 4195458 |
| `zola_memory.log` | 151494 |

**Setup:** Voice mode; speak after the beep. Lines **1, 2, 4** only (one at a time).

### L-2.1 — line 1 (COMPLETE)

**Brian (own words):** *"It took about 15 seconds from the time I finished speaking to the time that she started speaking. It took about two seconds from the time her response showed in the box to the time that she started speaking."*

**Session note:** Hermes `agent_session_id=20261005_130256_aef4be` (existing serve session — see deviation). Wake path used (`hey zola`). Transcript len=35. **Cold Whisper load** this turn (`Loading faster-whisper model 'base'…`). HUD: `Checking a skill.` / `Running a command.` Tools: **`skill_view`** (1.73 s) then **`terminal`** (1.26 s). `calculate` **not** invoked. Memory: `pending_id=b538748c-bc76-4ec4-9c46-befdeaa1c319` written (neutral L-2 turn).

#### Measured timeline (local)

| Event | Timestamp |
|---|---|
| Wake detected | 18:47:42.545 |
| Recording start | 18:47:43.395 |
| **EoS** (Silence − 1.5 s) | **18:47:46.160** |
| Silence fire / stop | 18:47:47.660 / .664 |
| WAV written | 18:47:47.672 |
| Whisper load start (cold) | 18:47:48.645 |
| Transcribed | 18:47:50.557 |
| Client transcript / Thinking | 18:47:50.564 / .577 |
| `prompt.submit` accepted | 18:47:50.614 |
| Reply text / HUD Speaking | 18:48:03.463 / .468 |
| **First audio** (`playback bout start`) | **18:48:06.249** |

#### EoS → first audio (Q1a)

| Cumulative | ms |
|---|---:|
| EoS → VAD trigger | 1500 |
| EoS → transcript ready | 4397 |
| EoS → `prompt.submit` | 4454 |
| EoS → first model token | UNMEASURABLE |
| EoS → first TTS audio | **20089** |

| Stage | ms | % of 20089 |
|---|---:|---:|
| Silence wait | 1500 | 7.5% |
| STT (incl. cold load + delivery → submit) | 2954 | 14.7% |
| Submit + prefetch | ~25 | &lt;1% |
| Model + tools + Edge + ffplay (submit→bout) | 15635 | **77.8%** |

**Cross-check vs Brian:** text-in-box → audio ≈ 18:48:06.249 − 18:48:03.468 = **~2.8 s** (matches “about two seconds”). Felt ~15 s aligns with Thinking/transcript → audio (~15.7 s), not full EoS→audio (~20 s, which includes silence + cold STT).

### L-2.2 — line 2 (COMPLETE)

**Brian (own words):** *"6 seconds until the approval card. About 1 second to speak after the card was approved."*

**Notes:** Warm Whisper (no load line). HUD `Running a command…` then approval **`srq-8cce60bcb55f`** shown 18:51:34.725, answered `once` 18:51:39.579. Tool: **`terminal`** (5.27 s after approve). `calculate` **not** invoked. `pattern_key`: **not present** in available logs (`server-requests.log` has id/method/session only; agent.log has no `pattern_key` line). Transcript len=39. Pending `3e1ef784-eac4-485b-a95f-63d4f72bb8b6`. Submit → card: **5691 ms ≈ 5.7 s**.

#### Measured timeline

| Event | Timestamp |
|---|---|
| Recording start | 18:51:23.104 |
| **EoS** (Silence − 1.5 s) | **18:51:25.650** |
| Silence / WAV | 18:51:27.150 / .161 |
| Transcribed (warm) | 18:51:29.018 |
| Thinking / `prompt.submit` | 18:51:29.026 / .034 |
| **Approval shown** | **18:51:34.725** |
| Approval answered | 18:51:39.579 |
| Reply complete / HUD Speaking | 18:51:42.201 / .202 |
| **First audio** (bout start) | **18:51:43.469** |

#### EoS → first audio (includes human approval wait)

| Cumulative | ms |
|---|---:|
| EoS → VAD trigger | 1500 |
| EoS → transcript | 3368 |
| EoS → `prompt.submit` | 3384 |
| EoS → approval card | **9075** |
| Approval shown → answered (Brian) | 4854 |
| Answered → first audio | 3890 |
| HUD Speaking → first audio | **1267** |
| EoS → first TTS audio (wall) | **17819** |

| Stage (machine-only, excl. Brian approve dwell) | ms | Notes |
|---|---:|---|
| Silence | 1500 | |
| STT warm → submit | ~1884 | WAV→Transcribed 1857 |
| Submit → approval card | ~5691 | model+tool before card |
| Post-approve → audio | ~3890 | includes remaining model/TTS; HUD→audio ~1.3 s matches Brian |

**Cross-check:** Thinking→approval ≈ **5.7 s** ≈ Brian’s “6 seconds until the approval card.” HUD Speaking→audio ≈ **1.3 s** ≈ “about 1 second to speak after…approved.”

### L-2.3 — line 4 (COMPLETE)

**Brian (own words):** *"About six seconds until her responds. Again about a second to speak after text shows. STT misunderstood lemon for limits."*

**Notes:** Warm Whisper. No approval card. Hermes turn context logged mis-hear: scripted “lemons” → STT **“limits”** (`msg` len=51). API latency logged **5.0 s**; turn duration **5.1 s**. Edge TTS saved 18:53:13.860. `presence.log` had no bout-start line in the tail window; first-audio proxy = TTS save time (bout_stop on follow-up at 18:53:19.278). Pending `35421edf-59b8-490f-842e-80da65251750`.

#### Measured timeline

| Event | Timestamp |
|---|---|
| Recording start | 18:52:59.600 |
| **EoS** (Silence − 1.5 s) | **18:53:03.798** |
| Silence / WAV | 18:53:05.298 / .309 |
| Transcribed (warm) | 18:53:07.337 |
| Thinking / `prompt.submit` | 18:53:07.345 / .361 |
| Reply complete / HUD Speaking | 18:53:12.476 / .479 |
| Edge TTS saved (first-audio proxy) | **18:53:13.860** |

#### EoS → first audio

| Cumulative | ms |
|---|---:|
| EoS → VAD | 1500 |
| EoS → transcript | 3539 |
| EoS → submit | 3563 |
| EoS → first audio (TTS-save proxy) | **10062** |

| Stage | ms | % of ~10062 |
|---|---:|---:|
| Silence | 1500 | 15% |
| STT warm → submit | ~2063 | 20% |
| Model (submit→complete) | ~5115 | **51%** |
| TTS startup (complete→audio proxy) | ~1384 | 14% |

**Cross-check:** Thinking→HUD Speaking ≈ **5.1 s** ≈ Brian’s “about six seconds.” HUD→TTS-save ≈ **1.4 s** ≈ “about a second.”

### L-2 summary (three turns)

| Turn | Felt wait | Machine EoS→audio | Notes |
|---|---|---|---|
| L-2.1 Tokyo | ~15 s | ~20.1 s | Cold Whisper; tools `skill_view`+`terminal` |
| L-2.2 cups/quart | 6 s to card; ~1 s after approve | wall ~17.8 s (incl. approve) | Warm STT; `terminal` + approval; submit→card ≈ 5.7 s |
| L-2.3 shopping list | ~6 s; ~1 s text→speech | ~10.1 s | Warm STT; STT “limits” |

**Finding P7PRE-AUD-25** [RISK] MEDIUM — Simple questions answered with tools: L-2.1 `skill_view`+`terminal`; L-2.2 `terminal` + approval `srq-8cce60bcb55f` (`pattern_key` unlogged). Outside `calculate`’s scope; **not** a P6-D08 calculator regression (`calculate` never called). Latency cost: submit → card ≈ **5.7 s** on L-2.2.

**STT vs H-1:** L-2 audio 4.3 / 4.1 / 5.7 s vs L-1 clips 3.69–6.78 s. Warm WAV→Transcribed 1857 / 2028 ms vs H-1 warm infer ~0.75 s. See AUD-26 in Audit_04 / SYNTHESIS 5.4.

**L-2 pending fate:** `b538748c…`, `3e1ef784…`, `35421edf…` — `zola_memory.log` `19:03:14` `consolidate trigger=quiet turns=3 episodes=0 ok=true` → **consolidated into nothing** (not failed). Store episodes remain 0.

---

## L-3 — Echo reproduce (GO/NO-GO)

### Memory placement forecast (before Brian OK)

Effective `CONSOLIDATE_QUIET_MINUTES` = **10** (`consolidate.py` L28). Quiet timer starts on provider init; consolidate also on session_end / session_switch.

An L-3 turn that completes will:
1. **Immediately:** `pending_turns` row via `sync_turn` (as L-2 already did — three pending ids above).
2. **After ~10 minutes quiet** (or sooner on session end/switch): consolidator may create **episode** and/or **fact** rows from pending — not guaranteed to stay pending-only.
3. **P7PRE will not clean up** anything created (G-NOCHANGE). Cleanup only via Zola’s approved forget path, as a developer decision at synthesis 5.2.

Neutral prompts planned: *"Tell me two facts about octopuses."* then typed *"And one about squid."*

### What Brian would do (if OK)

In Voice mode: ask for a spoken reply of two+ sentences; wait for the beep (follow-up recording); then **type** the next prompt at once (LEAD-1). Repeat once, typing **before** the beep instead.

### Status

**Brian OK** (2026-10-05): run L-3 with conditions — pre-snapshot counts; new session + session ID; tag LIVE-PROBE-CONTAMINATION by ID; no cleanup; record redirect marker + `on_turn_start` vs `sync_turn` lengths; one step at a time.

### Pre-L3 memory snapshot (2026-10-05T19:28:46)

| Table | Count |
|---|---:|
| `pending_turns` | **0** |
| `episodes` | **0** |
| `facts` | **16** |
| `episode_fact_refs` | **0** |
| `tombstones` | **30** |

Log offsets: `voice-timeline.log`=794415, `agent.log`=4217811, `zola_memory.log`=155721.

### Session

**Session ID:** `20261005_192949_1f4302`

### L-3 Run A — type **after** beep (COMPLETE)

Brian spoke octopuses, heard beep, then typed (already done when reported “done”): timeline shows `typed-submit` at 19:30:29 while `capture=true`, then orphan transcript **len=58** at 19:30:44 submitted as a **new whole turn** (not mid-turn redirect — typed turn had already finished at 19:30:33).

| Turn | on_turn_start msg_len | sync_turn user_len | `"User correction during the turn"` in stored user msg? |
|---|---:|---:|---|
| 1 (spoken octopuses) | 33 | 33 | **No** |
| 2 (typed squid) | 19 | 19 | **No** |
| 3 (echo transcript) | 58 | 58 | **No** |

Turn 3 user len=58 **equal** to prior assistant (ratio 1.000) — confirmed echo as whole user turn. Echo check skipped (`followUpStarted=False` after typed-submit).

**LIVE-PROBE-CONTAMINATION (Run A):**

| Kind | ID |
|---|---|
| pending_turns | `d518805a-de66-4666-b132-6a7f283e33e6` (turn 1) |
| pending_turns | `f5255068-5a04-4e2c-8e1e-19ad053281b0` (turn 2) |
| pending_turns | `b679670c-d203-4042-a295-39db9f18ad8d` (turn 3 echo) |
| episodes / new facts / episode_fact_refs | none yet (counts: pending=3, episodes=0, facts=16, refs=0, tombs=30) |

### L-3 Run B — type near / before beep (COMPLETE)

**Observed timeline:** octopus turn `complete` 19:33:28; bout_stop / follow-up fire 19:33:38.491; **`typed-submit` 19:33:38.878** (~0.4 s after beep); typed turn finished 19:33:41; orphan transcript **len=59** at 19:33:50 → new whole user turn equal to squid reply. Hermes was **not** still `running` at typed-submit (post-complete), so **no** busy redirect.

| Turn | on_turn_start msg_len | sync_turn user_len | `"User correction during the turn"` in stored user msg? |
|---|---:|---:|---|
| 4 (spoken octopuses again) | 33 | 33 | **No** |
| 5 (typed squid) | 20 | 20 | **No** |
| 6 (echo transcript) | 59 | 59 | **No** |

Turn 6 user len=59 **equal** to prior assistant — confirmed whole-turn echo again. Client transcript line showed **stale** `capture_start/stop` from the wake capture (19:33:12–19:33:19) while Hermes recorded 19:33:39–19:33:48 — logging provenance gap.

**LIVE-PROBE-CONTAMINATION (Run B additions):**

| Kind | ID |
|---|---|
| pending_turns | `07299cfa-d89a-47c2-8a62-1eac3286e703` (turn 4) |
| pending_turns | `09fb5434-c1de-4f83-a914-051725993304` (turn 5) |
| pending_turns | `4ecf0f19-8a53-4a47-a4a9-bd23a7321a26` (turn 6 echo) |

**Post–L-3 counts:** pending=**6**, episodes=**0**, facts=**16**, episode_fact_refs=**0**, tombstones=**30**.  
**Redirect string in `state.db` for this session:** **0** rows. Mid-turn `"User correction…"` path **not reproduced live** (both runs landed as whole-turn echoes after turn complete). Static LEAD-2 / E2 evidence remains from Phase 3.

### L-3 complete

---

## L-4 — Clarify in Voice (COMPLETE)

**Brian (own words):** *"She used the clarify tool offering three colors. I gave a response verbally. She showed my answer in text and then provided a verbal response."*

**Session note:** Same Hermes session `20261005_192949_1f4302` (not a fresh session). Clarify id `srq-702897de9735`.

### Against Phase 4 Q2 map

| Step | Observed |
|---|---|
| Clarify request received/shown | 19:35:37.975 / .977 `method=clarify` |
| Panel / card | Implied by Brian (“offering three colors”); HUD `Waiting for your answer` 19:35:37.994 |
| Question spoken | `question_spoken id=srq-702897de9735 chars=45` 19:35:38.001 |
| Capture after release | `question_release rule=monitor` 19:35:43.272 → record 19:35:44.618 |
| Answer routed | transcript len=15 `bound=srq-702897de9735` 19:35:49.617 → `answered … text_or_len=15` |
| Card collapse / reply | clarify tool completed 19:35:49.631; verbal reply TTS ~19:35:54–58; HUD Speaking 19:35:54.889 |

**Pending from this turn:** `5b2aff76-57d6-4fe6-9959-82fc4d153b11` (tagged LIVE-PROBE-CONTAMINATION with L-3 set).

---

## Pre-synthesis hash check

`config.yaml`, `SOUL.md`, and all `plugins/**` hashes **match Phase 1**.  
`MEMORY.md` / `USER.md` hashes **unchanged**.  
Memory store deltas vs Phase 1 at pre-synthesis: pending 0→**7**, episodes 0→0, facts 16→16, refs 0→0, tombs 30→30.

**Post-quiet consolidate (doc revision):** L-3/L-4 seven pending IDs drained at `19:46:03` `quiet turns=7 episodes=0 ok=true` — same path as L-2 (into nothing; no episodes). Current store: pending=**0**, episodes=**0**, facts=16.
