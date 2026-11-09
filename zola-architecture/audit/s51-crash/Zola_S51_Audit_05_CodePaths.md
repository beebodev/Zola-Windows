# Zola S51 Audit — 05 Code paths and request-on-crash

Phase 5. Scoped to Phase 3 groups + S51 silence/STT clue path. Labels **EVIDENCE** / **INFERENCE** / **UNRESOLVED**.  
Corrected after Brian review: Group A is not labelled “output write”; stream direction remains **UNRESOLVED**.

## 1. PortAudio / sounddevice stream sites in serve (source only)

All paths below are in the pinned `hermes-agent` tree unless noted. Module: `sounddevice` → `libportaudio64bit.dll`.

### Shared module-level play/stop stream — [EXT]

**[EXT]** python-sounddevice 0.5.5 (`sounddevice.play` docstring in installed package): `sd.play()` “cannot be used for multiple overlapping playbacks”; internally it calls `sd.stop()`, creates one `OutputStream`, and starts it. `sd.stop()` / `sd.get_stream()` apply **only** to the stream from the last `play()`/`rec()`/`playrec()`, not to separately constructed `InputStream`/`OutputStream` objects.  
**EVIDENCE (code):** Hermes uses that shared path via `_sd_play_blocking` → `sd.play` / `sd.get_stream` / `sd.stop` (`tools/voice_mode.py` L352–359).

### Inventory (create / start / replace / stop)

| # | Site | What happens to a PortAudio stream | Thread / caller | File:lines |
|---|------|------------------------------------|-----------------|------------|
| 1 | `_sd_play_blocking` | **Replace/start** shared play stream (`sd.play`); **stop** via `sd.stop` after poll | Caller’s thread (blocking) | `voice_mode.py` L352–359 |
| 2 | `play_beep` | Calls `_sd_play_blocking` (shared play stream) | Caller’s thread | L362–391 |
| 3 | `_thinking_sound_loop` | Repeated `sd.play` / `sd.stop` on shared play stream | Daemon `voice-thinking-sound` | L449–469; started L487–488 |
| 4 | `start_thinking_sound` / `stop_thinking_sound` | Starts/stops the thinking-sound thread (which owns play/stop); does not open InputStream | Host / RPC path that arms thinking sound | L476–498 |
| 5 | `_play_wav_via_sounddevice` | Calls `_sd_play_blocking` for WAV PCM | Caller’s thread (often TTS play path) | L991–1012; from `play_audio_file` L1098–1100 |
| 6 | `stop_playback` | Terminates ffplay subprocess if any; **`sd.stop()`** on shared play stream | Caller’s thread (e.g. `methods_voice` toggle/stop) | L949–961; callers `tui_gateway/methods_voice.py` ~L133–134, ~L224–236 |
| 7 | `AudioRecorder._ensure_stream` | **Create+start** dedicated `sd.InputStream` (kept between recordings) | First `AudioRecorder.start` on that instance | L718–751 |
| 8 | `AudioRecorder.start` / `stop` / close | Arms recording flag on existing InputStream; `_close_stream_with_timeout` → `stream.stop`/`close` on helper thread | Voice continuous / record RPC threads; close on daemon | L753–777; L779–797 |
| 9 | `listen_for_speech` | **Create** `sd.InputStream` (context manager) for barge monitor | Caller / barge side thread | L1165+ |
| 10 | `full_duplex_listen` | **Create** `sd.InputStream` (context manager) | Daemon `voice-full-duplex` (when barge enabled) | L1378–1407+ |
| 11 | Wake `WakeWordDetector` open | **Create+start** `sd.InputStream` for wake capture | Wake arm path; daemon wake reader | `tools/wake_word.py` L576–578; stop/close L444–445 |

No other `sd.OutputStream` / `RawOutputStream` constructions were found under hermes-agent voice paths for the current Zola Windows TTS path — Deepgram command TTS → mp3 → ffplay (P9-D14) (**EVIDENCE** search). Streaming-TTS `OutputStream` is a different provider path (documented in P4PRE); not the current Deepgram→mp3→ffplay / shared `sd.play` (thinking-sound/beep) stack.

### Which pairs can run at the same time

| Pair | Concurrent? | Basis |
|------|-------------|-------|
| Shared `sd.play` stream vs another `sd.play` | **No** (replaced) | [EXT] play stops prior play; Hermes thinking loop and WAV/beep all share that one stream |
| Shared `sd.play` vs `AudioRecorder` InputStream | **Yes (possible)** | Distinct stream objects; `sd.stop` does not close InputStream ([EXT] + code) |
| Shared `sd.play` vs wake InputStream | **Yes (possible)** when wake not paused | Separate InputStream (`wake_word.py`) |
| Shared `sd.play` vs `full_duplex_listen` / `listen_for_speech` InputStream | **Yes (possible)** if barge armed | Separate InputStream |
| Wake InputStream vs `AudioRecorder` InputStream | **Typically serialized** by product rules (wake paused for record) — still two code paths that each open InputStream | Lore/P2-WAKE; not re-proven here as impossible if mis-ordered |
| Two InputStreams (wake + full-duplex + recorder) | **Possible in process** if armed overlapping | Separate `InputStream` instances; PortAudio host may still conflict — **UNRESOLVED** at native layer |

**Tie to Group A:** dump shows a PortAudio **internal** stream thread hitting an unbacked address. That is consistent with **any** live PortAudio stream (input **or** output). Which Hermes site owned the stream is **UNRESOLVED**. **INFERENCE:** freed/replaced callback still invoked by PortAudio’s thread (Phase 3).

### Group B — `python312` + `_sqlite3`

**EVIDENCE:** dump 29172 frames; `zola_memory` SQLite. **INFERENCE:** eval + DB, not PortAudio.

### S51 clue / S52

**EVIDENCE:** AE `ntdll` 2026-10-06 during silence/stop/wake lore path — dump gone. **Does not match** Group A dump signature. S52 remains separate.

## 2. Request on crash (source)

| Concern | Behaviour | Label | Cite |
|---------|-----------|-------|------|
| Detect dead backend | unreachable; supervisor `stale`→`restart` | EVIDENCE | Phase 2; `ProcessSupervisor.cs` |
| UI status | “Zola's backend stopped. Restarting…”; `_unreachable=true` | EVIDENCE | `MainWindow.xaml.cs` L1301–1314; `SupervisionConstants.StatusRestarting` |
| Detail / reason | `ShowUnreachable` discards reason | EVIDENCE | L1289–1298 |
| Pending clarify | `AbandonPendingQuestion(GapReason)` | EVIDENCE | L1307 |
| Voice / wake | Fail closed in gap | EVIDENCE | `VoiceController` ~L1645–1659 |
| In-flight turn | Not retried in unreachable handler | EVIDENCE | `_sessionReady=false`; no resubmit in that path |
| Lost-reply announcement | Absent (restart status only) | [GAP]/[RISK] | Status strings name backend restart, not lost answer |

### A01 / P9-D02

| Expectation | Verdict |
|-------------|---------|
| Supervision restarts serve | **[MATCH]** |
| Voice fails closed in gap | **[MATCH]** |
| Brian told backend is restarting | **[MATCH]** |
| Brian told in-flight request/answer was dropped | **[GAP]** |
| Turn recovered/replayed | **[GAP]** |

## 3. S52 vs Phase 3 groups

**No match (EVIDENCE of mismatch).** S52 → stop-vs-silence-STT / `ntdll` lore. Group A → PortAudio stream thread → unbacked. Group B → sqlite/python312.

## Findings

- **S51-AUD-07** [RISK] HIGH — Serve creates/stops multiple PortAudio streams (shared `sd.play`/`sd.stop` plus several `InputStream`s). Group A is a PortAudio stream-thread failure; **which stream (in vs out) is UNRESOLVED**. Overlap of play stream with InputStreams is possible by construction ([EXT] + source).
- **S51-AUD-02** (reaffirmed) [GAP]/[RISK] — Restart status shown; lost in-flight reply not announced or retried.
- **S51-AUD-08** [GAP] LOW — S52 not implicated by preserved Group A/B dumps.
