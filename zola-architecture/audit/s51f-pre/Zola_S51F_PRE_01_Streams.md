# Zola S51F-PRE — 01 Remaining PortAudio stream users

Phase 3. Labels **SOURCE** / **EVIDENCE** / **MEASURED** / **INFERENCE** / **UNRESOLVED**.  
Thinking sound is **off** (`S51F-D01`). Brian setup: `barge_in: false`, wake on, Deepgram → mp3 → ffplay, Voice mode.  
Prior inventory: `zola-architecture/audit/s51-crash/Zola_S51_Audit_05_CodePaths.md` (11 sites).

---

## 1. Which of the 11 sites can still run

| # | Site | Still in Brian's setup? | When | Gate (SOURCE) |
|---|------|-------------------------|------|---------------|
| 1 | `_sd_play_blocking` | **Yes** (helper) | Any beep / WAV via sounddevice | `voice_mode.py` L352–359 |
| 2 | `play_beep` | **Yes** | Listen start / capture end (below) | L362–391; callers `hermes_cli/voice.py` |
| 3 | `_thinking_sound_loop` | **No** | — | `start_thinking_sound` returns False when `thinking_sound` false (`voice_mode.py` L480–481) |
| 4 | `start/stop_thinking_sound` | **Armed but no-op** | Per turn still calls start; returns False | `prompt_turn.py` L193–203 |
| 5 | `_play_wav_via_sounddevice` | **Rare** | Only if something plays a `.wav` through `play_audio_file` and sounddevice output is allowed | L991–1012; L1098–1100. Deepgram TTS is **mp3 → ffplay** (P9-D14) — not this path for reply speech |
| 6 | `stop_playback` | **Yes** | Stop speaking / barge cut / new turn cut | L949–961; `methods_voice.py` TTS stop paths |
| 7–8 | `AudioRecorder` InputStream | **Yes** | Every `voice.record` capture (wake, follow-up, clarify) | L718–797; GUI: `methods_voice.py` `voice.record` → `start_continuous` |
| 9–10 | `listen_for_speech` / `full_duplex_listen` | **No** (product) | Barge paths | `barge_in: false` → `_arm_full_duplex_listener` not armed (`prompt_turn.py` L190–191; `methods_voice.py` L160) |
| 11 | Wake `InputStream` | **Yes** | Resting wake listen; paused during capture | `tools/wake_word.py` open L576–578; pause/resume from `methods_voice.py` |

**Reply speech itself** uses ffplay (subprocess), not the shared `sd.play` stream (**SOURCE** / prior S51 inventory).

---

## 2. Brian's two beeps (addition)

No dedicated beep log line exists (search Phase 2 window: none). Times below are **INFERENCE** from capture lifecycle ↔ code order; Brian's ear is **MEASURED** for presence of the cues.

### Cue A — right after he finishes speaking

| Field | Value | Label |
|-------|-------|-------|
| What Brian hears | One short end-of-capture cue (code: **660 Hz × 2**) | Brian MEASURED; frequency SOURCE |
| Trigger | VAD silence after speech → `AudioRecorder` silence callback → `_continuous_on_silence` | SOURCE `hermes_cli/voice.py` L466–491 |
| Code | `_play_beep(frequency=660, count=2)` after `rec.stop()` | SOURCE L490–491 → `_play_beep` L149–157 → `play_beep` → `_sd_play_blocking` |
| Shared `sd.play`? | **Yes** (Windows: `_sounddevice_output_allowed()` true) | SOURCE `voice_mode.py` L50–59, L384–391 |
| Hermes or client? | **Hermes** (serve). Client only opened `voice.record` | SOURCE `methods_voice.py` L747–753 |
| What it tells Brian | "I got the end of your utterance / capture closed" | INFERENCE (product meaning) |
| Phase 2 S1 correlate | Wake capture_stop / Settled `signal=transcript` **11:45:32.055** (len=25). Same pattern on echo turns **11:45:54.212**, **11:46:10.481** | MEASURED lifecycle; beep at those instants **INFERENCE** |

### Cue B — when listening stops (e.g. follow-up window ending)

| Field | Value | Label |
|-------|-------|-------|
| What Brian hears | Same family of end cue (**660 Hz × 2**) | Brian MEASURED |
| Trigger (silence end) | Same `_continuous_on_silence` path when a listen window ends on silence (including follow-up with no / empty speech after VAD) | SOURCE L466–491; GUI `auto_restart=False` then `_deactivate` (no extra beep) L532–535, L200–205 |
| Trigger (explicit stop) | Client `voice.record` `action=stop` → `stop_continuous(force_transcribe=True)` → eventually `_finish_stop` → **same** `_play_beep(660, count=2)` | SOURCE `methods_voice.py` L721–724; `voice.py` L451–457 |
| Shared `sd.play`? | **Yes** | SOURCE as Cue A |
| Hermes or client? | **Hermes** plays; client may *request* stop | SOURCE |
| What it tells Brian | "This listen window is over" | INFERENCE |
| Phase 2 correlate | Follow-up Settled `signal=idle` **11:46:43** (after S1 cluster); S2 follow-up idle **12:13:54** | MEASURED lifecycle; which of silence vs client-stop fired **UNRESOLVED** without beep breadcrumb |

### Also playable in his setup (list)

| Cue | Code | Freq / count | When | Shared `sd.play`? | Tells Brian |
|-----|------|--------------|------|-------------------|-------------|
| Listen **start** | `voice.py` L376; restart L537 | **880 Hz × 1** | Every `start_continuous` (wake record, follow-up, clarify) — before mic stream opens | Yes | "I'm listening now" |
| End of capture / stop | L491, L456 | **660 Hz × 2** | Cue A/B above | Yes | Capture / listen ended |
| Thinking sound | off | — | — | N/A | — |
| Reply speech | Deepgram mp3 + **ffplay** | — | Each spoken sentence | **No** (subprocess) | Her words |
| Code-read verification | Client **Zira** (local) | — | Explicit code-read only (R1) | No PortAudio in serve | Spoken code |
| WAV via sounddevice | `play_audio_file` `.wav` branch | — | Uncommon on Deepgram path | Yes if taken | File playback |
| `stop_playback` `sd.stop` | may cut shared stream | — | Interrupt | touches shared stream | Stops in-process play |

---

## 3. Shared-stream concurrency (thinking sound off)

| Pair | Concurrent? | Cite |
|------|-------------|------|
| Beep `sd.play` vs another beep/WAV `sd.play` | No — replaced ([EXT] sounddevice) | Prior S51; `_sd_play_blocking` |
| Beep vs `AudioRecorder` InputStream | **Yes possible** — distinct streams; end beep runs after `rec.stop()` but InputStream often **kept alive** (`stop` clears recording flag; stream closed on timeout path L779–797) | SOURCE L799+; L718–721 |
| Beep vs wake InputStream | **Yes possible** when wake not fully released | wake vs record pause rules — typically wake paused for record (**INFERENCE** product); code still has two InputStream sites |
| Two beeps overlapping | Unlikely by design (blocking play) | SOURCE blocking `_sd_play_blocking` |

---

## 4. Supported ways to take shared play stream out of beeps (G-INTEGRATION)

Options only — **Brian decides which cues to keep**. Do not treat removal of a needed cue as default.

| Option | Integration | Effect on Brian | Removes PortAudio play? |
|--------|-------------|-----------------|-------------------------|
| `voice.beep_enabled: false` | **Supported config** (`config_defaults.py` L1147; gated in `_play_beep` before any play — `hermes_cli/voice.py` L132–153) | No listen-start / capture-end beeps | **Yes** — returns before `play_beep` / `sd.play` |
| `voice.beep_volume: 0.0` | **Supported config** (tests honor 0.0) | Beeps inaudible | **No** — still synthesizes and calls `sd.play` at zero amplitude (`voice_mode.py` L372–391) |
| Route beeps through tempfile → ffplay (like macOS `_play_int16_via_tempfile`) | Needs **Hermes source** change on Windows (today only Darwin skips sounddevice output, L50–59) | Same cues, non-PortAudio output | Yes for beeps |
| Client plays listen/end cues (SystemSounds / NAudio) instead of Hermes | **Zola client change** (supported as Zola-owned); set `beep_enabled: false` so Hermes does not also play | Cue ownership moves to client | Yes if Hermes gated |
| Keep cues; only leave thinking sound off | Already done (S51F-D01) | Brian still hears listen/end beeps | Thinking path gone; beep path remains |

**Cue meaning reminder (for Brian's choice):**  
- **880 × 1** ≈ listening opened.  
- **660 × 2** ≈ listening/capture closed (after speech or window end).  
Removing both without a replacement removes those non-verbal status signals.

---

## 5. Mic stream lifecycle / locks

| Topic | Finding | Label |
|-------|---------|-------|
| Recorder lock | `AudioRecorder` uses `self._lock` around start/stop recording flag | SOURCE L764–776, L801–804 |
| Stream close thread | `_close_stream_with_timeout` stops/closes on a **helper daemon thread** while caller continues | SOURCE L779–797 |
| Callback after close | Close moves `self._stream` aside then `stop`/`close` on helper; PortAudio may still invoke callback briefly — **classic race class** | INFERENCE; exact dump tie **UNRESOLVED** |
| Wake vs recorder | Pause wake before `voice.record` start; resume on terminal capture | SOURCE `methods_voice.py` L741–746, resume helpers |
| Serialization of open/close across wake + recorder | Product intends pause/resume; not a single global PortAudio lock across modules | SOURCE + INFERENCE |

---

## Findings (this doc)

| ID | Severity | Summary |
|----|----------|---------|
| S51F-AUD-01 | HIGH | Shared `sd.play` still used for listen-start and capture-end beeps after thinking sound off |
| S51F-AUD-02 | MEDIUM | End beep can overlap kept-alive mic InputStream / wake InputStream lifetimes |
| S51F-AUD-03 | LOW | `beep_volume: 0` silences but does not remove PortAudio play; prefer `beep_enabled: false` to skip play entirely |
| S51F-AUD-04 | INFO | No beep start/end log events — Cue A/B times inferred from capture lifecycle |
