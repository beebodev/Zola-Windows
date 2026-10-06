# P7PRE Audit 05 — S34 Chunking / S37 Estimate

**Pins:** client `7d77cb51`, Hermes `345cd2b0`  
**Labels:** `S34`, `S37`, `P4-D13`, `P4-D18`, `P4-D20`, `P4-D22`, `P4-D24`, `P2-D15`, `S17`

---

## S34

### 1. Reply → speech

`SentenceChunker` (`tts_streaming.py` L63–91): boundaries `(?<=[.!?])(?:\s|\n)|(?:\n\n)`; **`min_len=20`**; strips think blocks. Per-sentence Edge via `_SyncSentencePipeline` (`tts_tool_speaker.py` L75–126) with `_strip_markdown_for_tts`. **Not configurable** by profile.

### 2. Markdown / em-dashes

`tts_text_normalize.py`: strips fences/links/bold/italic/headings/URLs; em-dash ranges → "to"; emojis removed. Client echo/clock normalization is similar but not identical (LEAD-4). SOUL "How I talk out loud" is policy, not a runtime enforcer.

### 3. `surface: "voice-live"` effects @ pin

| Effect | Where |
|---|---|
| Sets `client_surface` / `voice_live_context` (≤6000) | `methods_prompt.py` L583–588 |
| Per-turn model **input note** (`voice_live_turn_note`) | `voice_live.py` L73–90; `session_notifications` L690–703 |
| No separate model/tool limit for chained Windows path | — |
| GPT-Live/WebRTC path separate; profile `voice_chat_mode` = chained | unused by Windows client |

Client does **not** send `surface=voice-live` today (`ChatSocket`).

### 4. Zola plugin voice-only note without Hermes edit?

`pre_llm_call` has **no** voice flag. Only adding client `surface` (or new param) would signal voice. Plugin-only note: **blocked** without client wire change.

### 5. Interactions

| Change | S38 | S45 haystack |
|---|---|---|
| Whole-line synthesis | May cut chunk wait; longer first Edge job | Haystack still streamed text — LEAD-4 unchanged |
| voice-live note | Small TTFT ↑ | N/A |

**Finding P7PRE-AUD-19** [GAP] LOW — voice-only shaping needs client `surface` or Hermes edit; neither is free.

---

## S37

### 6. Release counts (`voice-timeline.log` all)

| Rule | Count |
|---:|
| `follow_up_release rule=monitor` | **196** |
| `no_bout_estimate` | **6** |
| `forced_estimate` | **3** |
| `monitor_unavailable` | **0** |
| Total `follow_up_release` | **205** |
| `question_release` | **24** (22 monitor, 1 forced, 1 no_bout) |

**LEAD-7: CONFIRMED** — monitor **196/205 = 95.6%**.

Constants: `FirstSentenceLatencySeconds=3.3`, `FollowUpMarginSeconds=5.0`, `StartupWindowSeconds=5.3` (`VoiceController.cs` L42–56).

### 7. Early / late vs playback

Monitor (n=196): **175** late vs `estimatedEnd` (>500 ms; med late ~3044 ms); **10** early; **11** within ±500 ms.  
`forced_estimate` (n=3): remaining 17.5 / 0 / 0 — **no** margin.  
`no_bout_estimate` (n=6): **3/6** fire before a later monitor `bout_stop` on same complete → **capture can open while she still speaks** → S45 risk.

**Finding P7PRE-AUD-20** [RISK] MEDIUM — Rare estimate paths (9/205) can open early; monitor path does not open before complete.

### 8. Re-anchor on first reply text

Move seed from `OnTurnStarted` (~L1596) to first `OnTurnDelta` with words. Matrix rows most affected: **TurnRunning+speaking**, **reply finished/audio playing**, **follow-up armed/recording** (less early capture); resting/wake unchanged; question path can share the fix.

**Finding P7PRE-AUD-21** [MATCH] — S37 is small relative to monitor dominance (LEAD-7); residual value is on the 4.4% estimate/forced paths that feed S45.
