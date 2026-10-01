# P4-FEEDBACK — P4-D18 Probe 2: where the front of an immediate answer goes

**Mode:** read-only investigation (2026-09-30). No code/config/profile changes.  
**Sources:** `%LOCALAPPDATA%\ZolaClient\logs\voice-timeline.log`, `presence.log`; Hermes Agent **v2026.9.14** (`C:\Users\test\Dev\hermes-agent` @ `345cd2b`); Zola client `VoiceController.cs`, `TtsPlaybackMonitor.cs`, `PresenceLife.cs`; Hermes `profiles\zola\logs\agent.log`.

**Context:** AUD-37 immediate ×5 → 0/5 full, 5/5 partial, no self-capture. Observed gap ≈ **1.2 s quiet + ~0.55 s to live mic**.

---

## Q1. Gaps between reply bouts (what the quiet window has to cover)

### Evidence — within-reply bout→bout gaps (today’s monitor releases)

Definition used: two **bout** events inside one `follow_up_release rule=monitor` window (from ~8 s before `complete` through `fire`). Gap = next bout start − prior bout stop.

All ten `rule=monitor` fires in `voice-timeline.log` (AUD-37 window 16:40–16:46) had **exactly one bout start and one bout stop** in the window. Examples:

| complete | fire | bout starts in window |
|----------|------|------------------------|
| 16:40:13.364 | 16:40:18.284 | 1 |
| 16:41:54.233 | 16:42:00.031 | 1 |
| 16:43:02.678 | 16:43:08.691 | 1 |
| 16:44:28.237 | 16:44:34.097 | 1 |
| 16:45:33.362 | 16:45:38.945 | 1 |

(and the five short “her reply to truncated answer” releases likewise each had one bout)

**Within-reply bout→bout gaps:** count = **0** (before `message.complete`: n=0; after: n=0). Min/median/max: **n/a**.

Cross-turn gaps of ~9–11 s (her question bout stop → her next-turn bout start after the user spoke) are **not** within-reply; they include quiet + user speech + her next turn.

### Evidence — inter-**segment** gaps inside one bout (multi-sentence)

A bout is **not** one sentence. `TtsPlaybackMonitor` ends a bout only after owned ffplay is gone for `_releaseDebounceMs`; a new segment within that window **bridges** and keeps the same bout (`TtsPlaybackMonitor.cs` ~420–453, log `playback bridged gapMs=`).

Example (long reply, 13:46 — one bout, many sentences):

```
13:46:00.958 bout start
13:46:10.291 segment stop → 13:46:10.478 segment start  bridged gapMs=187
13:46:20.211 → 13:46:20.396  bridged gapMs=185
… (further bridges 266, 190, 183, 349, 185)
13:47:02.400 segment stop → 13:47:02.901 bout stop
```

**Bridged gapMs on 2026-09-30:** n=9, min=183, median=187, max=441.

AUD-37 short questions were single-segment bouts (no bridges).

### Evidence — debounce vs 1.2 s quiet

| Constant | Value | Source |
|----------|-------|--------|
| `PresenceLife.DefaultReleaseDebounceMs` | **450** | `PresenceLife.cs:92` |
| `PresenceLife.DefaultPlaybackPollHz` | **20** (50 ms period) | `PresenceLife.cs:91` |

AUD-37 segment-stop → bout-stop deltas (ms): 493, 483, 500, 497, 499, 501, 497, 492, 505, 481 → **min 481, median 497, max 505** (≈ 450 ms debounce + one poll).

Measured bout-stop → `rule=monitor` fire (attempts 1–5): **1203–1214 ms** (= `FollowUpPostBoutQuietSeconds` 1.2).

**Answer (Q1):** Today’s immediate replies never needed the quiet window for a second bout (0 within-reply bout gaps). A bout already spans multiple sentences via ≤~0.45 s bridged segment gaps. Bout stop **already includes** ~0.45–0.50 s debounce after last audio; the **1.2 s quiet is entirely on top of that.**

---

## Q2. The ~0.55 s from release to a live mic

### Measured (attempts 1–5, question follow-ups)

| # | `rule=monitor` fire | Hermes `Voice recording started` | Client `capture_start` | fire→Hermes | fire→capture_start |
|---|---------------------|----------------------------------|------------------------|-------------|-------------------|
| 1 | 16:40:18.284 | 16:40:18.848 | 16:40:18.851 | **564 ms** | 568 ms |
| 2 | 16:42:00.031 | 16:42:00.595 | 16:42:00.598 | **564 ms** | 567 ms |
| 3 | 16:43:08.691 | 16:43:09.236 | 16:43:09.238 | **545 ms** | 547 ms |
| 4 | 16:44:34.097 | 16:44:34.644 | 16:44:34.647 | **547 ms** | 550 ms |
| 5 | 16:45:38.945 | 16:45:39.507 | 16:45:39.512 | **562 ms** | 568 ms |

Median fire→Hermes ≈ **562 ms**; Hermes→client `capture_start` ≈ **2–5 ms** (bookkeeping after RPC returns).

### Breakdown

**1. `PauseWakeForCaptureAsync` — ~0 ms on these paths**

- `StartCaptureAsync` always awaits it (`VoiceController.cs:1705–1707`).
- It no-ops when `WakePaused` (`:2977–2985`).
- Timeline shows only `wake.pause reason=turn-start` for each attempt; **no** `wake.pause reason=capture`. Wake was already paused for the turn / follow-up arm.

**2. Client `voice.record start` round trip — essentially the whole ~550 ms**

- `OnFollowUpTimerAsync` → `StartCaptureAsync` → `RecordAsync(ActionStart)` (`:2084–2106`, `:1721`).
- `capture_start` is stamped only after a successful reply (`:1764–1766`).

**3. Inside Hermes (v2026.9.14) between RPC and “Voice recording started”**

`methods_voice.py` `voice.record` start (`:747–753`):

1. Optional `wake_word.pause_listening` (already paused here).
2. `start_continuous(...)` (`hermes_cli/voice.py:331+`):
   - Reuses `_continuous_recorder` if present (`:364–366`).
   - **`_play_beep(880 Hz, count=1)` before `rec.start()`** (`:374–378`) — `play_beep` default **duration 0.12 s**, blocking (`tools/voice_mode.py:362–391`).
   - `AudioRecorder.start` → `_ensure_stream()` opens `sounddevice.InputStream` once and keeps it alive; later starts only flip `_recording` (`:718–777`). Log line `Voice recording started` is at end of `start` (`:777`).

No separate VAD/model warm-up on this path (local Whisper runs only after stop). Beep is enabled by default; zola profile does not set `beep_enabled: false`.

**What could be done earlier without opening the mic (facts only):**

- Ensure `_continuous_recorder` / InputStream already exists (often true after a prior capture; cold open cost not isolated in these five runs).
- The **start beep** (~0.12 s) is work before `_recording=True`; skipping/moving it would not open the mic earlier by itself but shortens time-to-record once start is called.
- Wake pause is already done at turn-start — nothing left to pre-warm there for follow-up.

**Answer (Q2):** On follow-up, wake pause is free; ~550 ms is almost all Hermes `voice.record start` handling (beep ~0.12 s + stream ensure/start + RPC), then the client stamps `capture_start` within a few ms of Hermes’s “recording started” log.

---

## Q3. Can a capture be cancelled cleanly (discard, no transcript)?

### Evidence

| Path | Behavior | Cite |
|------|----------|------|
| `voice.record` **stop** | Always `stop_continuous(force_transcribe=True)` | `methods_voice.py:721–725` |
| `stop_continuous(force_transcribe=True)` | `rec.stop()` → WAV → background transcribe → can emit `voice.transcript` | `hermes_cli/voice.py:412–422`, `:430+` |
| `stop_continuous(force_transcribe=False)` | **`rec.cancel()` discards buffer**; no transcribe | `hermes_cli/voice.py:424–427`; docstring `:388–393` |
| `AudioRecorder.cancel` | Clears frames; “discard all captured audio” | `tools/voice_mode.py:826–829` |
| `AudioRecorder.stop` short/quiet | Returns `None` if &lt;0.3 s samples or peak RMS below threshold (no WAV) | `tools/voice_mode.py:812–819` |
| Gateway exposure | **No** `voice.record` action calls `force_transcribe=False`. Discard is used by toggle-off / end-chat (`methods_voice.py:56–57`, `:642–643`) | |

If record starts and a new bout appears 0.3 s later: the **only** client-facing stop is `voice.record stop` → **force transcribe**. Speech in that clip becomes a transcript (and Zola may submit). Empty/near-empty may die in `stop()` as too short/quiet (no transcript) — that is length/VAD discard after stop, not a deliberate abort API.

**Answer (Q3):** Internally Hermes can discard (`cancel` / `stop_continuous(False)`), but **`voice.record stop` always force-transcribes**; there is no RPC today that aborts a follow-up capture with a guaranteed discard and no `voice.transcript`.

---

## Q4. Pre-roll

### Evidence

| Mechanism | Exists? | Used by `voice.record`? |
|-----------|---------|---------------------------|
| `AudioRecorder` while not recording | Callback **discards** chunks; stream may stay open | Yes path, **no** keep-before-start (`voice_mode.py:718–729`) |
| `listen_for_speech` / `full_duplex_listen` | Rolling **`pre_roll_ms` default 1200** deque | Barge-in / full-duplex only (`voice_mode.py:1118–1159`, `:1381–1410`) — **not** wired to `voice.record` PTT |
| Wake detector | On pause/resume, **`engine.reset()` drops** buffered audio/features so resume doesn’t re-fire | `wake_word.py:624–627` — anti-retrigger, not STT pre-roll |

**Answer (Q4):** Hermes has a 1.2 s pre-roll buffer on the barge-in/full-duplex listen path, but **`voice.record` has none**; the wake path explicitly clears buffers on resume rather than feeding STT.

---

## Candidate levers (measured savings only)

Totals from attempts 1–5: **quiet ≈ 1.21 s** after bout stop (which itself is ~0.49 s after last segment); **fire→live mic ≈ 0.55 s** (median ~0.56 s). End-to-end after last audio ≈ **1.21 + 0.55 ≈ 1.76 s** before mic is live.

| Lever | What the numbers say it could save | Notes (facts, not a design pick) |
|-------|--------------------------------------|----------------------------------|
| Shorten / remove `FollowUpPostBoutQuietSeconds` (1.2 s) | **Up to ~1.20 s** per 0.1 s cut; full remove ≈ **1.21 s** | Today’s within-reply bout gaps = 0; bridged sentence gaps already ≤0.44 s inside debounce |
| Rely on debounce only (quiet → 0) | **~1.21 s** | Bout stop already waits ~0.48–0.50 s after last segment |
| Disable / defer start beep (`play_beep` 0.12 s before record) | **~0.12 s** of the ~0.55 s | Part of every `start_continuous` before `_recording=True` |
| Pre-create InputStream / recorder before fire | **Unknown slice** of remaining ~0.43 s | Stream often already warm; these five runs don’t isolate cold-open cost |
| Overlap / skip `PauseWakeForCaptureAsync` on follow-up | **~0 s** | Already no-op when wake paused |
| Optimistic `voice.record` during quiet / at bout stop | Up to **1.21 s** (quiet) + portion of **0.55 s** if start overlaps | Needs a **discard** stop if a new bout appears — not available via `voice.record stop` today |
| Barge-in / FD pre-roll for follow-up | Would cover speech **before** start (up to **1.2 s** buffer on that API) | Exists only on FD/barge path; **not** on `voice.record` |

**STOP.** No code or config changed.
