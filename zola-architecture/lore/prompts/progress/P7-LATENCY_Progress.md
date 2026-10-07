# P7-LATENCY Progress — Measure, Then Fix

## Branch

- Work branch: `p7-latency`
- Base `main` HEAD: `fa93d1523629566838571e77a316419b72774ef2` (P7-CLARIFY closeout metadata)
- Prompt: `P7-LATENCY_Prompt_v1.1.md` (canonical: `C:\Users\test\Dev\zola-spikes\prompts\P7-LATENCY_Prompt_v1.1.md`)
- Prompt SHA-256 (on-disk, 31,063 bytes): `dc651bdc2f3c3cea0729f52db36c3a70673e683487259737c2e7ddc485de9742`
  - Developer-supplied SHA: **matched** (verified at Phase 1 start)
- Build plan: `PHASE7_BUILD_PLAN.md` v1.1 on `main` (P7-D10 / P7-D11)
- Hermes HEAD (Phase 1): `345cd2b057a452236de401d3534b8502a7465e8d` (`v2026.9.14`); `git status --porcelain` empty
- Scratch: `C:\Users\test\Dev\zola-spikes\p7-latency\` (created; never committed)

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Branch and Baseline | COMPLETE |
| 2 | Grounding and Instrumentation | COMPLETE |
| 3 | Baseline Measure | COMPLETE |
| 4 | STOP: Rank Candidates and Choose Fix | COMPLETE |
| 5 | STOP: Approve the Exact Change | COMPLETE |
| 6 | Apply Fix and Remeasure | COMPLETE (closed on findings) |
| 7 | Closeout | IN PROGRESS |

## Guardrails summary

- **G-SCOPE:** New pure `Voice/TurnTiming.cs` (proposed) + progress doc; Phase 2 minimum instrumentation only (submit, message start/delta/complete, bout start, transcript admit); Checks link helper. Phase 6: only Brian-approved candidate (SOUL / skill / plugin). No other client behavior changes.
- **G-ARCH:** One timing owner; logging never breaks a turn; fix is the narrowest that removes the measured cause; P7-D10 limits (no Whisper/beam/cpu_threads/silence/install/Hermes edit — file those candidates).
- **G-PATTERN:** Read every relevant file in full before changing it.
- **G-NOCHANGE:** hermes-agent; CaptureLifecycle / TranscriptAdmission / Clarify* / cancel / admission / P4-D18 release / wake; ServerRequestBroker / HermesProcessManager / XAML; live profile until Phase 6; `config.yaml` Whisper/silence/voice/approval keys; lore / build-plan.
- **G-NO-INSTALL:** No package or model installs; LT-G1 uses existing installs.
- **G-COMMENT:** `// P7-LATENCY: <rationale> — P7-D10` (language-appropriate elsewhere; never inside Brian-approved SOUL text).
- **G-CONST:** Named constants for log prefixes, field names, boundary (`min_len=20` + file:line), thresholds.
- **G-PRIVACY:** Logs/repo: times, durations, counts, IDs, tool names, reasons only — never transcript/question/reply/memory text. Recordings stay in scratch.
- **G-LIVE:** One live step at a time; Cursor never injects turns; dictation off + P2-D16 before voice.
- **G-CRASH:** Record + relaunch + repeat once; crashed measured turns excluded from medians.
- **G-STOP / G-CLOSEOUT:** Stop after each phase; closeout only on “proceed to closeout”.
- **G-LORE-SCOPE:** No lore edits this track (S38 at Phase 7 lore closeout).
- **G-NO-CROSS-SCOPE:** No Android Zola.

## Discrepancies

none

## Phase 1 baseline

Recorded 2026-10-06 ~13:41 local.

### Live profile hashes (unchanged by this track at Phase 1)

| Path | SHA-256 |
|---|---|
| `config.yaml` | `7BA2E676A04FF92047C8D711FCB022BE8A532B11BAAC6F74B08986744E704570` |
| `SOUL.md` | `E3D7BF9AC29B46237A2685BEBAE2E89E1A5952EDB23E5AFEEE0EE8363009FB49` |
| `plugins/**` aggregate | `82db44e1e51dce2d6adf0694210dc4391db2efc97b250f3ebd83e14f6a1b630d` |

Aggregate method (same as P7-CLARIFY): SHA-256 of UTF-8 join of per-file `HASH \\relpath` lines (sorted by path), including `__pycache__`.

#### plugins/** per file (source)

| Rel path | SHA-256 |
|---|---|
| `\plugins\zola_memory\__init__.py` | `7FAA42BC030B329EB5F078B80EC45183104105361A29E880EAC3CCCCF9994C11` |
| `\plugins\zola_memory\consolidate.py` | `1B2D8D8AD8140EC515D184279DD3BD541952918025ADEDF47761944AE14941C2` |
| `\plugins\zola_memory\fact_index.py` | `AA0CCE9E599BA94F933A8619E2094D3A21192BD4AA785510A9D28FBC53D81B02` |
| `\plugins\zola_memory\forget.py` | `A9B62AA822DBAD0A350FE84CB004C4E63124F4FBEA98F591D4454EDDCC1BB306` |
| `\plugins\zola_memory\llm_access.py` | `EC5A8F319628CB24DEEB0177397D34B754A51B30F80C025D4F93D5E5189FEC57` |
| `\plugins\zola_memory\log.py` | `A2515A96171B2F9B4AB7947A41A7C7181DB3DCA6F636298C11A7373AAFDC1B62` |
| `\plugins\zola_memory\pending.py` | `9FF6156CD946C08BFD737EDFFC15C6DAE2D865AB0C34ED332F48056DDA854769` |
| `\plugins\zola_memory\provider.py` | `E292093763665B0A35E38C67166F84E372493D4F4016704F006217A15E76A18A` |
| `\plugins\zola_memory\registry.py` | `86AA4DA04D67AB911D569AB1D9774A86E1A36F75F9B1931D49CA3F0272EE771D` |
| `\plugins\zola_memory\retrieve.py` | `53D8044D896F6F769AA10EF99BAB67083ADF19AA3E01858A067A870916C0290D` |
| `\plugins\zola_memory\store.py` | `C471EA121F993BD00D5E68EEF0DEFB92FBDD3D606774CA78B89ADF1B34CB00E8` |
| `\plugins\zola_memory\time_context.py` | `C3B61942358CCCEC6DB422B31B7200C8D743C095779B144DB9B174BF105BBF9F` |
| `\plugins\zola_tools\__init__.py` | `A1EF8541406F1A9C199CC8C8CE1BB7C71E087F4C3EAA2151DAC7B59F04C33513` |
| `\plugins\zola_tools\calculator.py` | `0F29F3FC1E1D5EAC3D1E4CEF0BCF6428EF6497EE2AF61BD86503602BE80FE680` |
| `\plugins\zola_tools\plugin.yaml` | `F329E9065493F766712A018DF14541172282666EF516AD3D45781B56AE1D2216` |

`__pycache__\*.pyc` also hashed into the aggregate (14 files under `zola_memory` / `zola_tools`); omitted from the source table for brevity.

#### skills/communication/** per file

| Rel path | SHA-256 |
|---|---|
| `\skills\communication\conversation-memory\SKILL.md` | `F5ED3DF53E23BD869A41147DCA2B4B851A19BF75B9F889E49BCE9DE0994870E9` |
| `\skills\communication\everyday-assistance\SKILL.md` | `D5F4195A74186527E4F7753BE8E4185252F3365ED7BF9D0CED88617CA3C4A2BE` |
| `\skills\communication\interactive-preferences\SKILL.md` | `FDB7A2F350F3DB3427C5BC806036A3AE05533385CEE44D1608AF0CDC34D5E7E3` |
| `\skills\communication\spoken-conversation\SKILL.md` | `F586AEBDB495FFFA399C8ABC1AF030FEAAB9ADF7AC6586BFD3D734D7A7A9F8BE` |

### Processes

| Process | PID | Start time | Parent | Notes |
|---|---|---|---|---|
| `dotnet.exe` (run Zola.Client) | 25520 | 2026-10-06 13:15:04 | 23468 | `--no-build` (P7-CLARIFY redeploy) |
| `Zola.Client.exe` | 23024 | 2026-10-06 13:15:05 | **25520** | usual Debug apphost |
| `python.exe` (venv serve) | 16816 | 2026-10-06 13:15:07 | **23024** | `-m hermes_cli.main -p zola serve --isolated` |
| `python.exe` (uv cpython) | 24212 | 2026-10-06 13:15:07 | **16816** | serve child |

Serve parent/child: confirmed (24212 ← 16816).

### Logs

| Log | Bytes | Last write |
|---|---|---|
| `%LOCALAPPDATA%\ZolaClient\logs\voice-timeline.log` | 1,008,726 | 2026-10-06 13:23:55 |
| `%LOCALAPPDATA%\ZolaClient\logs\display-state.log` | 975,509 | 2026-10-06 13:23:55 |
| `%LOCALAPPDATA%\ZolaClient\logs\presence.log` | 50,843,900 | 2026-10-06 13:41:21 |
| `%LOCALAPPDATA%\ZolaClient\logs\server-requests.log` | 36,676 | 2026-10-06 13:23:23 |
| `%LOCALAPPDATA%\hermes\profiles\zola\logs\agent.log` | 4,568,960 | 2026-10-06 13:33:44 |
| `%LOCALAPPDATA%\hermes\profiles\zola\logs\zola_memory.log` | 210,220 | 2026-10-06 13:33:44 |

### Pre-change build and checks (branch tip = base, no Track-3 edits yet)

| Command | Result |
|---|---|
| `dotnet build windows-client/Zola.Client/Zola.Client.csproj -r win-x64` | **PASS** — 0 Warning(s), 0 Error(s) |
| `dotnet run --project windows-client/Zola.Client.Checks/Zola.Client.Checks.csproj` | **PASS** — exit 0; coverage lifecycle 22/22, admission 13/13, start 9/9, invalid 6/6, stop_phrase 4/4, amendments 7/7, latch 18/18, wiring 9/9, clarify 20/20 |

## Phase 2 — Grounding and instrumentation

### 2a — Event observability (client)

| Event | file:line | Object / thread |
|---|---|---|
| `prompt.submit` send | `MainWindow.xaml.cs` `SubmitTurnAsync` → `ChatSocket.SubmitAsync` (~414 / `ChatSocket.cs:277`) | MainWindow; typed on UI, voice after UI `Dispatch(OnTranscriptReady)`; await continues off UI sync context |
| `message.start` | `ChatSocket.cs:630` → `MainWindow.OnMessageStarted` (~855) → `_voice.OnTurnStarted` | Socket read-loop → UI `DispatcherQueue` |
| `message.delta` | `ChatSocket.cs:633` → `OnMessageDelta` (~887) → `_voice.OnTurnDelta` | same |
| `message.complete` | `ChatSocket.cs:640` → `OnMessageCompleted` / `FinishTurn` → `_voice.OnTurnCompleted` | same |
| playback bout start | `TtsPlaybackMonitor.cs:477–480` (`P3-LIFE: playback bout start`) → UI → `VoiceController.NotePlaybackBoutStarted` | poll thread logs; raise marshalled to UI |
| transcript admit | `VoiceController.OnVoiceTranscript` → `WriteTimeline(FormatAdmit…)` (~2166) | ChatSocket read-loop (no VC UI marshal); then `TranscriptReady` → UI |
| `tool.start` (tools=) | `ChatSocket.cs:692–699` → `MainWindow.OnToolStarted` | read-loop → UI |
| approval (approval=) | `ServerRequestBroker` approval → `MainWindow.OnApprovalOpened` | read-loop → UI |

**Clock:** client timeline uses `DateTimeOffset.Now` / `ToString("o")` (local offset, 100ns ticks). Hermes `agent.log` uses `YYYY-MM-DD HH:MM:SS,mmm` (ms) on the same machine.

### 2a — Hermes sentence boundary

| Item | Citation |
|---|---|
| Regex | `tools/tts_streaming.py:63` `SENTENCE_BOUNDARY_RE = r"(?<=[.!?])(?:\s|\n)|(?:\n\n)"` |
| `min_len` | `:72` default **20**; emit only if `len(head.strip()) >= min_len` (`:85–87`) |
| Think strip | `:65` `<think…></think>` DOTALL |

Mirrored in client `TurnTiming.MinSentenceLen` / `TryFindFirstSentenceEnd`.

### 2a — `agent.log` lines (exact / actual)

| Topic | String | Where |
|---|---|---|
| Silence | `Silence detected (%.1fs), auto-stopping` | `tools/voice_mode.py:682` |
| Stop | `Voice recording stopped (%.1fs, %d samples)` | `:810–811` |
| WAV | `WAV written: %s (%d bytes)` | `:842` |
| Whisper process | library `faster_whisper`: `Processing audio with duration …` (not hermes logger); hermes load: `Loading faster-whisper model…` `transcription_tools.py:321` |
| Transcribed | `Transcribed %s via local whisper (%s, lang=%s, %.1fs audio)` | `:370–371` |
| TUI accept | `tui prompt accepted: ui_session=…` | `tui_gateway/prompt_turn.py:816–817` |
| API latency | `API call #%d: … latency=%.1fs…` | `agent/turn_usage.py:198` (no INFO “request start”) |
| Tool finish | `tool %s completed (%.2fs, %d chars)` | `agent/tool_executor.py:996` (no INFO tool-start) |
| Edge TTS | `TTS audio saved: %s (%s bytes, provider: %s)` with `provider: edge` | `tools/tts_tool.py:353` (not “Edge TTS saved”) |

### 2a — Time context (P6-TIME)

`hermes-plugins/zola_memory/time_context.py`: injected stamp `[Time: Fri Oct 2, 3:45 PM PDT]` — local wall clock + short zone (`:131–148`); zone from `%Z` or `UTC±HH:MM` via `utcoffset()` (`:112–128`); gap marker after ≥30 min (`:186–200`).

### 2a — Math / `calculate` (P6-D08)

`hermes-plugins/zola_tools`: arithmetic only (`+ - * / **`, parens, `abs/round/min/max/sqrt/floor/ceil`). **Unit conversion not in scope.** Live `SOUL.md` “Doing math” aligns (read at Phase 1 hash; no SOUL edit this phase).

### 2a — Background-review skills

Hermes loads a **compact skill index** into the system prompt; full body via **`skill_view` only** (`prompt_builder.py` ~1207–1339) — not always-loaded.

| Skill | Body headings (titles only) |
|---|---|
| `everyday-assistance` | `# Everyday Assistance` → `## When to Use` / `## Procedure` / `## Pitfalls` / `## Verification` |
| `conversation-memory` | `# Conversation Memory` → `## Procedure` / `## Pitfalls` |

### 2b — Design (implemented)

| Choice | Decision |
|---|---|
| Owner | **`VoiceController`** — sole writer of `voice-timeline.log`; already sees admit, bout start, turn delta/complete. MainWindow reports submit / tool.start / approval. |
| Helper | Pure `Voice/TurnTiming.cs` (no UI/I/O; time passed in). |
| Destination | **`voice-timeline.log`** (same file; `turn_timing` prefix). |
| Line | One line per turn when complete∧first_audio, or complete + `FinalizeSeconds=15` with no audio; new submit force-finalizes a prior open record. |
| First sentence | Client mirrors Hermes regex + `min_len=20` on accumulated deltas. |
| Coupling | No new shared state beyond VC methods; timing failures → `turn_timing error=<type>`; never read by decisions. |

### Diff summary (Phase 2)

| File | Change |
|---|---|
| `Voice/TurnTiming.cs` | **new** — record, boundary, format, finalize |
| `VoiceController.cs` | own `_turnTiming`; note submit/delta/complete/audio/tool/approval; write line |
| `MainWindow.xaml.cs` | `SubmitTurnAsync(…, kind)`; tool/approval notes |
| `Zola.Client.Checks/*` | link `TurnTiming`; 8 timing rows |

### Checks / purity (Phase 2)

| Item | Result |
|---|---|
| Build `-r win-x64` | **PASS** 0W/0E |
| Checks | **PASS** exit 0 — prior coverage unchanged + **timing rows 8/8** |
| `CaptureLifecycle` / `TranscriptAdmission` / `Clarify*` vs `main` | **IDENTICAL** (newline-normalized) |
| Timing read by decision code | **none** (write/observe only) |

## Phase 3 — Deploy and baseline

### 3a — Deploy

Close confirmed: old PIDs 25520 / 23024 / 16816 / 24212 **GONE**. Build PASS (RID + non-RID, exe mtime 13:54:40).

| Process | PID | Start time | Parent |
|---|---|---|---|
| `dotnet.exe` (run) | **18512** | 2026-10-06 13:54:47 | 6852 |
| `Zola.Client.exe` | **19228** | 2026-10-06 13:54:48 | **18512** |
| serve parent | **23308** | 2026-10-06 13:54:49 | **19228** |
| serve child | **15552** | 2026-10-06 13:54:49 | **23308** |

Serve parent/child: confirmed (15552 ← 23308).

| Log | Bytes at deploy |
|---|---|
| voice-timeline.log | **1,009,398** |
| display-state.log | **975,918** |
| presence.log | **50,979,460** |
| server-requests.log | **36,676** |
| agent.log | **4,576,144** |
| zola_memory.log | **210,220** |

Live `silence_duration`: **1.5** s (`config.yaml`).

### Part A (Brian, verbatim — 2026-10-06 ~13:58)

| Check | Brian |
|---|---|
| Dictation tool off | "Yes" |
| P2-D16 setup holds | "Yes" |
| Voice mode on | "Yes" |
| New session open | "Yes. session ID: b86ca4a2" |
| Conversation panel closed | "Yes" |
| B8 line approved | "Approved" |

### 3c — B8 memory line

| Field | Value |
|---|---|
| Line | `Hey Zola, what's my favorite season?` |
| Fact id | `1dfa6cc8-a1bd-446b-a90c-ab923c40fbe5` |
| Brian | Approved |

### Part B — baseline turns (Brian + logs)

Throwaway (not measured): turn=1. Accidental follow-up “408” after B3: turn=5 **excluded**.

| # | turn | tools (client) | approval | sub→δ ms | δ→sent | sent→TTS* | TTS→audio* | sub→audio | Brian |
|---|---:|---|---:|---:|---:|---:|---:|---:|---|
| B1 Tokyo | 2 | 1 `terminal` | 0 | 7119 | — | 3044 | 366 | 10529 | "no card. Answer was natural." |
| B2 cups/quart | 3 | 2 `tool_describe`+`calculate` | 0 | 16068 | — | 2567 | 483 | 19118 | "no card. answer is normal." |
| B3 17×24 | 4 | 1 `calculate` | 0 | 10520 | — | 12903 | — | — | "no card. natural response." (no first_audio in line) |
| B4 unwind | 6 | 1 `skill_view` | 0 | 10969 | — | 6547 | 292 | 17808 | "natural." |
| B5 one more idea | 7 | 0 | 0 | 1795 | 945 | 1640 | 113 | 4493 | "natural." (wake; follow-up window had closed) |
| B6 octopuses | 8 | 0 | 0 | 3553 | — | 2603 | 138 | 6294 | "natural." |
| B7 why | 9 | 0 | 0 | 2140 | 297 | 1325 | 154 | 3917 | "natural." (wake; follow-up had idled) |
| B8 season | 10 | 0 | 0 | 5349 | — | 1107 | 92 | 6548 | "she got it right and responded naturally." |

\*Phase 3 proxy (superseded in Phase 4 correction below): empty `first_sentence` used first_delta→TTS. Clocks: client `DateTimeOffset` o-format; agent `HH:MM:SS,mmm`; same machine, local −07:00.

**B1–B3 tool sequences (agent):** B1 `terminal`; B2 `tool_describe` → `calculate`; B3 `calculate`. No approvals this run. `silence_duration=1.5`.

### Medians (B1–B8; ms; n/min/max)

| Stage | n | median | min | max | notes |
|---|---:|---:|---:|---:|---|
| EoS→WAV | 8 | 1507 | 1504 | 1511 | silence wait ≈1500 |
| WAV→STT | 8 | 1645 | 1411 | 1800 | |
| **S-model** | 8 | **6234** | 1795 | 16068 | |
| S-sentence / S-tts | — | — | — | — | see **Phase 4 correction** |
| **S-play** | 7 | **154** | 92 | 483 | |
| submit→first_audio | 7 | 6548 | 3917 | 19118 | |
| EoS→first_audio | 7 | 9534 | 6922 | 22438 | |

Join script: `zola-spikes/p7-latency/join_baseline.py` (scratch). Cross-turn stage/median ratios from Phase 3 are **withdrawn** — replaced by per-turn additive shares in Phase 4.

### LT-G2 (AUD-25) — 30-day counts only

Window: `state.db` messages with `timestamp` in last 30 days (2464 rows). Classifier: short (≤120 chars) matching time/zone/unit/arithmetic/definition patterns vs other.

| Class | turns | with any tool | approvals in tool results |
|---|---:|---:|---:|
| short_factual | 43 | **39 (91%)** | 0 |
| other | 752 | 232 (31%) | 0 |

Top tools **short_factual:** `terminal` 32, `execute_code` 4, `calculate` 3, `skill_view` 2, `tool_describe` 2.  
Top tools **other:** `skill_view` 80, `clarify` 59, `memory` 59, `terminal` 47, `web_search` 39.

**Drivers (this baseline):** B1 used `terminal` (zone/time) despite time context carrying zone/offset (`time_context.py`). B2 used `tool_describe`+`calculate` for unit conversion (`calculate` arithmetic-only — units out of scope). B3 used `calculate` for arithmetic (in scope). `everyday-assistance` / `skill_view` on B4 conversational, not on B1–B3 this run. No approval cards on B1–B8.

### LT-G1 (AUD-26) — `transcribe_recording` wall time

**Entry:** `tools.voice_mode.transcribe_recording` via hermes-agent venv; `HERMES_HOME` = zola profile.  
**Inputs:** Brian L1-1…6 + free-1…3 → 16 kHz mono in scratch `audio16/`; P4 samples → `synth/` (`speed_1.0`, `B1_pitch_p0Hz`, `B2_pitch_p0Hz`).  
**Protocol:** 1 cold discard + 1 per-file warm discard + 5 warm runs. No mic. Scripts: `lt_g1_transcribe.py`, results under `results/`.

| Condition | L1 warm median (ms) | L1 min–max | all-warm median (n=60) |
|---|---:|---:|---:|
| **1. standalone** (client+serve closed) | **1006** | 931–1178 | 1101 |
| **2. idle-serve** (wake idle, nobody speaking) | **1175** | 750–2850 | 1184 |
| **3. live** baseline B1–B8 `WAV→Transcribed` | **1645** | 1411–1800 | — |
| H-1 (P7PRE) warm `model.transcribe` only | ~750 | — | — |

L1 per-file medians (ms):

| file | dur s | standalone | idle-serve |
|---|---:|---:|---:|
| L1-1 | 4.07 | 967 | 763 |
| L1-2 | 4.55 | 971 | 799 |
| L1-3 | 5.06 | 980 | 1455 |
| L1-4 | 6.40 | 994 | 1186 |
| L1-5 | 6.27 | 1144 | 1241 |
| L1-6 | 4.78 | 1109 | 1141 |

**Verdict — AUD-26: in-call (primary), with a smaller live residual.**  
Standalone entry is already ~1.0 s (≈ +250 ms vs H-1 infer-only), so most of the former “live ≫ H-1” gap is **inside the call path** (prep / local STT path beyond bare `transcribe`, not serve contention). Idle-serve adds only ~170 ms on the L1 median vs standalone (not enough to reach live 1645). Live log still ~470–640 ms above idle-serve — residual without Hermes `whisper_infer_*` markers (no fix this phase; P7-D10).

### LT-G3 (pauses; silence unchanged)

Offline energy pauses (20 ms frames, silent if RMS &lt; 8% of peak; min pause 80 ms; leading/trailing trimmed). Live `silence_duration` = **1500 ms**.

| | |
|---|---:|
| pause count (9 clips) | 78 |
| median | **120 ms** |
| p90 | **484 ms** |
| max | **1360 ms** |
| pauses ≥ 1500 ms | **0** |

No evidence that within-utterance pauses approach the live silence threshold. **No change** to `silence_duration` (P7-D10).

## Phase 3 STOP — Attribution packet (no ranking)

**Baseline EoS→first audio median:** 9534 ms (6922–22438; n=7).  
**Stage shares:** Phase 3 cross-turn ratios withdrawn — see Phase 4 additive median shares (S-model **51.4%**, S-tts **19.3%**, pre-submit **31.3%**).

**LT-G1 / AUD-26:** **in-call** — standalone `transcribe_recording` ≈1.0 s already; idle-serve ≈1.2 s; live log ≈1.6 s. Serve contention is secondary; bare-infer H-1 (0.75 s) understates the entry-point cost.

**LT-G2 / AUD-25:** Short factual turns tool **91%** (30d); this baseline B1 `terminal`, B2 `tool_describe`+`calculate`, B3 `calculate`. Drivers: zone/time still tools despite time context; units out of `calculate` scope; arithmetic in-scope. No approval cards this run (`approvals.mode=manual` / dangerous-pattern only).

**LT-G3:** Pause median 120 ms / max 1360 ms vs silence 1500 ms — silence left alone.

**Joined evidence:** scratch `join_baseline.py` + `results/lt_g1_*.json` + `results/lt_g3_pauses.json`. Client `turn_timing` wired; Checks timing 8/8 earlier.

## Phase 4 — Corrected attribution (re-join only; no new runs)

**Flush rule:** when `first_sentence` empty → sentence ready at `message.complete` (Hermes end-of-text flush).  
`S-sentence = first δ → complete`; `S-tts = complete → first TTS audio saved`. Boundary turns keep true δ→sentence values.

### Corrected per-turn post-submit

| # | rule | S-sentence | S-tts (Edge) | S-play | sub→audio | EoS→audio |
|---|---|---:|---:|---:|---:|---:|
| B1 | **flush** | 376 | 2668 | 366 | 10529 | 13842 |
| B2 | **flush** | 438 | 2129 | 483 | 19118 | 22438 |
| B3 | **flush** | 381 | **12522** | — | — | — |
| B4 | **flush** | 1192 | 5355 | 292 | 17808 | 21142 |
| B5 | boundary | 945 | 1640 | 113 | 4493 | 7433 |
| B6 | **flush** | 723 | 1880 | 138 | 6294 | 9354 |
| B7 | boundary | 297 | 1325 | 154 | 3917 | 6922 |
| B8 | **flush** | 284 | 823 | 92 | 6548 | 9534 |

**Flush-spoken:** **6/8** turns (B1–B4, B6, B8). Only B5, B7 hit a sentence boundary ≥ `min_len=20` before complete.

**Corrected S-tts median (real Edge synthesis):** **2004 ms** (823–12522; n=8). Prior proxy median 2585 overstated Edge by folding δ→complete into S-tts on flush turns.

**B3 no first_audio:** excluded turn=5 (“408”) began while B3 Edge TTS was still in flight (~12.5 s save after complete). `TurnTiming.Begin` **force-finalized** turn 4 before `NoteFirstAudio`. Presence bout at 14:03:59 matches turn=5 TTS (~14:03:58.8), not B3’s TTS save (~14:03:48.1).

### Additive shares (per-turn % of that turn’s EoS→audio; then median %)

n=7 turns with first_audio. Cross-turn ratio of stage-median/EoS-median **dropped**.

| Stage | median share |
|---|---:|
| pre-submit | **31.3%** |
| S-model | **51.4%** |
| S-sentence | **4.3%** |
| S-tts | **19.3%** |
| S-play | **1.5%** |

### S-model split (agent.log)

| # | api_n | api_sum ms | tool_sum ms | remainder | tools |
|---|---:|---:|---:|---:|---|
| B1 | 2 | 6500 | 890 | 0* | terminal |
| B2 | 3 | 12500 | 3890 | 0* | tool_describe, calculate |
| B3 | 2 | 10800 | 0 | 0* | calculate |
| B4 | 3 | 17200 | 170 | 0* | skill_view ×2 |
| B5 | 1 | 3100 | 0 | 0 | — |
| B6 | 1 | 4200 | 0 | 0 | — |
| B7 | 1 | 3700 | 0 | 0 | — |
| B8 | 2 | 9900 | 140 | 0* | skill_view |

\*remainder = max(0, S-model − api_sum − tool_sum). When api+tool ≥ S-model, the last API latency **spans past first δ** (accounting overcount), not negative gateway time. Gateway/prefetch not separately visible as a positive remainder on this run.

### Tool (B1–B4) vs no-tool group (B5–B8)

(Script groups as named; B8 had a 140 ms `skill_view` in agent.log / client tools=0.)

| Group | median sub→δ | median sub→audio |
|---|---:|---:|
| B1–B4 (tool) | **10744** (7119–16068) | **17808** (10529–19118, n=3) |
| B5–B8 | **2846** (1795–5349) | **5394** (3917–6548) |
| **Δ (bound)** | **~7900 ms** | **~12400 ms** |

### Track 4 / S34 input (no change now)

**Single-sentence flush:** a reply with no chunker boundary ≥ `min_len=20` is spoken only after the whole reply streams (`message.complete` → TTS). 6/8 baseline turns. File for `P7-VOICEPROSE` / S34 — not a Phase 7 Latency fix.

## Phase 4 STOP — Ranked candidates

Bounded saving reference: removing the tool round-trip pattern is worth up to **~7.9 s** on submit→δ and **~12.4 s** on submit→audio (tool vs no-tool medians). Per-turn ceilings: B1 sub→audio 10529 (−~5.1 s vs no-tool med); B2 19118 (−~13.7 s).

| Rank | Candidate | Cause / turns | Bounded saving | Accuracy / behavior risk | Type | P7-D10 |
|---:|---|---|---|---|---|---|
| 1 | **`SOUL.md`:** answer common knowledge, unit conversions, and time-zone questions directly (no tools) | AUD-25; B1 terminal, B2 tool_describe+calculate; 91% short-factual tool rate | Up to ~5–14 s submit→audio on B1/B2-class turns; group bound ~12.4 s | **Zone math without a tool can be wrong across DST**; **unit conversions from memory can be wrong**; conversational tone risk if over-broad | SOUL.md | Yes |
| 2 | **Time context:** add UTC offset (+ zone name) so she can convert zones without `terminal` | B1; time stamp already has short zone but she still shelled out | B1-class: up to ~5 s submit→audio / ~4 s on S-model vs no-tool med | Static/wrong offset at DST change → wrong remote time; narrower than SOUL | `zola_memory` | Yes |
| 3 | **`calculate` + unit conversion** (P6-D08 shape: bounded, no code, fail closed) | B2 (units out of scope → describe+wrong-tool path) | B2-class: up to ~13.7 s submit→audio if one cheap calculate replaces multi-call path | Conversion-table bugs; still a tool (smaller than terminal/describe stack). **Does not remove arithmetic `calculate`** | `zola_tools` | Yes |
| 4 | **`everyday-assistance` skill edit** (Brian’s call; kept at P6 closeout) | Historical Tokyo→skill_view+terminal; this run B1 skipped skill_view but B4 used it | Uncertain on this baseline; may cut skill_view prelude (~0.2 s tool + extra API) | Skill text drift; may not stop terminal if SOUL still pushes tools | skill | Yes |
| 5 | **In-process STT** | AUD-26; live WAV→STT 1645 vs standalone entry ~1006 | ~0.5–0.6 s residual live, or ~0.25 s entry-vs-H1 — small vs tool gap | LT-G1: gap is **in-call**; no reachable fix without Hermes edit / install / Whisper knobs | **filed** | Out |
| — | ~~Bypass `calculate` for arithmetic~~ | B3 | Would cut B3’s extra API (~5–11 s class) | **Conflicts with P6-D08** — tool chosen for correctness / no-code math; do **not** rank as a Latency fix | — | No |

**Recommendation:** Choose **#1 (`SOUL.md` direct answers for zones / units / common knowledge)** as the primary fix — it targets the measured tool vs no-tool gap on the AUD-25 controls. Optionally pair **#2** (offset in time context) if Brian wants a structural assist for zones. Prefer **#3** over trusting memory if unit accuracy matters more than avoiding the tool. **Keep `calculate` for arithmetic** (P6-D08). Do not touch silence, Whisper, or flush/sentence streaming in this track.

**Brian’s verdict (verbatim):**
- Fix: "Narrow SOUL + UTC offset (Recommended)"
- Arithmetic: "Keep calculate (Recommended)" (P6-D08 unchanged; "Doing math" not edited)

## Phase 5 STOP — Drafts (no live change)

### A. `SOUL.md` — narrow everyday answers (draft only)

| | |
|---|---|
| Live path | `%LOCALAPPDATA%\hermes\profiles\zola\SOUL.md` |
| Current SHA-256 | `E3D7BF9AC29B46237A2685BEBAE2E89E1A5952EDB23E5AFEEE0EE8363009FB49` |
| Backup (at Phase 6 apply) | `C:\Users\test\Dev\zola-spikes\p7-latency\SOUL.md.bak-P7-LATENCY-<timestamp>` |
| Placement | New section **after** “How I talk out loud” (time-notes guidance) and **immediately before** `## Doing math`. **Doing math untouched.** |
| Out of scope | Arithmetic (stays with calculate / P6-D08); general facts; current events; anything that changes over time |

**Before** (junction only — no text removed):

```
questions to keep things going. If he wants to go deeper, he'll say so, and I'll go with him.

## Doing math
When Brian asks me to work out numbers, I do simple arithmetic in my head when I'm sure of it. When precision
```

**After** (insertion only):

```
questions to keep things going. If he wants to go deeper, he'll say so, and I'll go with him.

## Everyday answers
When Brian asks what time it is somewhere else, I work it out from the UTC offset in my time
context and that place's offset. If the place observes daylight saving and I'm genuinely unsure
whether it's in effect on today's date, I look it up instead of guessing.
When he asks for a common everyday unit conversion — kitchen measures, distance, weight,
temperature, and the like — I answer directly. If it's unusual, or precision really matters, I say
so or look it up.
I don't reach for tools for those. Arithmetic stays with my calculator under Doing math. This isn't
for general facts, current events, or anything that changes over time.

## Doing math
When Brian asks me to work out numbers, I do simple arithmetic in my head when I'm sure of it. When precision
```

No other `SOUL.md` text is touched.

### B. `zola_memory` time stamp — explicit UTC offset (repo draft; not copied live)

**Grounding — stamp format consumers (none parse the body):**

| Consumer | File:line | Uses | Breaks? |
|---|---|---|---|
| Stamp builder | `time_context.py` `format_stamp_body` / `format_stamp` (~131–148) | produces `[Time: …]` | **changed (producer)** |
| Gap line | `time_context.py` `build_turn_time_context` (~186–200) | `format_stamp` + `format_stamp_body` in `[Gap: … (past_body)]` | No — past_body gains offset too |
| Marker persist | `time_context.py` `marker_iso` / `_parse_marker` (~203–219) | ISO-8601 only | No |
| Hook | `time_context.py` `handle_pre_llm_call` (~241–305) | returns built block | No |
| Episodes / stated time | `consolidate.py` (~763+, `marker_iso`) | ISO markers | No |
| Retrieval labels | `retrieve.py` (~90–177) | `localize_marker`, `DOW_NAMES`, `MONTH_NAMES` — not stamp body | No |
| SOUL.md | live L56–58 | “time notes” generically; no format parse | No |
| Unit tests | `tests/test_zola_memory.py` | exact string asserts | **updated** |

**Shape:** `[Time: Tue Oct 6, 3:16 PM PDT (UTC−07:00)]` (Unicode minus). When `%Z` is missing and the zone label is already `UTC±HH:MM`, no doubled parenthetical.

**Repo change:** `hermes-plugins/zola_memory/time_context.py` — added `utc_offset_label`; `format_stamp_body` appends `(UTC±HH:MM)`. Tests added/updated (offset present, DST/standard, no-%Z).

**Plugin suite:** `python -m unittest discover -s hermes-plugins/zola_memory/tests -t hermes-plugins/zola_memory` → **112 tests OK**.

**Per-file SHA-256 (live copy table):**

| File | Live (current) | Repo (to copy at Phase 6) | Action |
|---|---|---|---|
| `time_context.py` | `C3B61942358CCCEC6DB422B31B7200C8D743C095779B144DB9B174BF105BBF9F` | `327A027A740D4CD4DAA6A046245A0B44606DC39B774BAECACDB5A327597BC1BE` | **replace** |
| `__init__.py` | `7FAA42BC…` | same | unchanged |
| `provider.py` | `E2920937…` | same | unchanged |
| `store.py` | `C471EA12…` | same | unchanged |
| `retrieve.py` | `53D8044D…` | same | unchanged |
| `consolidate.py` | `1B2D8D8A…` | same | unchanged |
| `fact_index.py` | `AA0CCE9E…` | same | unchanged |
| `forget.py` | `A9B62AA8…` | same | unchanged |
| `log.py` | `A2515A96…` | same | unchanged |
| `llm_access.py` | `EC5A8F31…` | same | unchanged |
| `registry.py` | `86AA4DA0…` | same | unchanged |
| `pending.py` | `9FF6156C…` | same | unchanged |

Live backup of `time_context.py` at apply: `zola-spikes/p7-latency/time_context.py.bak-P7-LATENCY-<timestamp>`.

### Apply mechanics / Phase 6 targets

| | |
|---|---|
| Plugin apply | **Serve restart** required (live `plugins/zola_memory` is loaded by serve) |
| SOUL apply | **New session** (SOUL is session/system-prompt material; restart+new session is safest) |
| Phase 6 targets | **B1, B2:** no tool; **B3:** still uses `calculate` (expected); **B4–B8:** no behavior change; **B4 `skill_view`:** not targeted — record either way |
| Brian correctness checks | Tokyo time vs a real clock; cups per quart = **4** |

**Live profile:** untouched in Phase 5.

**Brian’s Phase 5 verdict (verbatim):** "Approved, with Claude's one edit to the SOUL.md draft."

Claude edit applied in the Everyday answers closer:
- was: `I don't reach for tools for those. Arithmetic stays with my calculator under Doing math. …`
- now: `I don't reach for tools for those. Any arithmetic follows what I do under Doing math. …`

## Phase 6 — Apply

| File | Before SHA-256 | After SHA-256 | Backup |
|---|---|---|---|
| live `SOUL.md` | `E3D7BF9AC29B46237A2685BEBAE2E89E1A5952EDB23E5AFEEE0EE8363009FB49` | `B4163D7EC004FAFF3FB2F4D9F99029E14747BB4D695BF0ABA65D6D45C619C031` | `zola-spikes/p7-latency/SOUL.md.bak-P7-LATENCY-20261006_153304` |
| `identity/SOUL.md` | (matched live before) | `B4163D7EC004FAFF3FB2F4D9F99029E14747BB4D695BF0ABA65D6D45C619C031` (byte-equal live) | — |
| live `plugins/zola_memory/time_context.py` | `C3B61942358CCCEC6DB422B31B7200C8D743C095779B144DB9B174BF105BBF9F` | `327A027A740D4CD4DAA6A046245A0B44606DC39B774BAECACDB5A327597BC1BE` (= repo) | `zola-spikes/p7-latency/time_context.py.bak-P7-LATENCY-20261006_153304` |

Doing math unchanged. Plugin suite was 112 OK at draft. Serve/client relaunched for remeasure (new session required).

### Remeasure (HUMAN-RUN)

| Field | Value |
|---|---|
| Session | ui `89fa477f` / agent `20261006_153348_3bd3c0` |
| Part A | Confirmed on each |
| Log bases | VT `1059645` / AG `4647373` |
| Stamp sample | `[Time: Tue Oct 6, 6:47 PM PDT (UTC−07:00)]` ✅ offset present |

**Brian per turn (verbatim):** B1 "Card decline. Gave answer"; B2–B3 "normal response"; B4–B5/B8 "normal… Speech started a couple seconds after text"; B6–B7 "normal… Full text before speech starts".

### Remeasure per-turn (corrected flush join)

| # | tools (client) | approval | agent tools | sub→δ | S-sent | S-tts | S-play | sub→audio | EoS→audio |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| B1 Tokyo | 3 | **1** (declined) | skill_view, terminal, terminal(BLOCKED) | 22478 | 281 f | 1309 | 376 | 24444 | 27812 |
| B2 cups | 2 | 0 | tool_describe, calculate | 10262 | 468 f | 768 | 407 | 11905 | 15321 |
| B3 17×24 | 1 | 0 | **calculate** | 8865 | 313 f | 1301 | 396 | 10875 | 14221 |
| B4 unwind | 0 | 0 | — | 2940 | 2526 b | 2211 | 103 | 7781 | 11227 |
| B5 one more | 0 | 0 | — | 2007 | 1524 f | 2807 | 367 | 6705 | 10134 |
| B6 octopuses | 0 | 0 | — | 2599 | 526 b | 1898 | 377 | 5400 | 8765 |
| B7 why | 0 | 0 | — | 1553 | 675 b | 2712 | 389 | 5330 | *join inflated* |
| B8 season | 0 | 0 | — | 1723 | 632 f | 1126 | 358 | 3839 | 7188 |

\*B7 EoS→audio join hit an earlier Silence in the 30s window (first-match); submit→audio **5330** is trustworthy.

**Answers (state.db):** B1 “It’s 10:47 AM Wednesday in Tokyo.” (after card); B2 “Four cups.” (`calculate`→4); B3 “408”; B8 “Summer.”

### Before / after (medians; corrected stages)

| Metric | Baseline | Remeasure | Note |
|---|---:|---:|---|
| S-model | 6234 | **2770** | noise + mix; B1 worse (22478) |
| S-sentence | 410 | 579 | |
| S-tts (Edge) | 2004 | 1604 | |
| S-play | 154 | 376 | |
| submit→audio | 6548 | 7243 | aggregate not improved |
| EoS→audio | 9534 | ~10–12k (B7 EoS noisy) | observed only |

Additive median shares (remeasure, n=8 incl. noisy B7 EoS): pre **32.2%**, S-model **27.9%**, S-tts **12.4%**, S-sentence **4.5%**, S-play **2.8%**.

### Causal pass bar

| Target | Result |
|---|---|
| B1/B2 no tool, no approval | **FAIL** — B1: skill_view+terminal+card; B2: tool_describe+calculate (same pattern as baseline) |
| B1/B2 attributable cost reduced | **FAIL** — B1 sub→audio 10529→**24444**; B2 19118→11905 (improved but still tooled) |
| B3 still `calculate` | **PASS** |
| B4–B8 no behavior change | **PASS** (B4 dropped baseline skill_view → 0 tools; no new approvals) |
| Answers correct (Brian) | Tokyo/cups checks: *(ask Brian)*; B2/B3/B8 look correct in logs |

**Smoke test failed:** causal target on B1/B2 not met. SOUL+offset did not stop the everyday-assistance → terminal / describe→calculate path.

**Brian on wait (verbatim):** "The wait still feels the same."  
**Tokyo clock:** "Time was accurate"  
**Cups:** "Answer was correct, ok"

## Phase 6b — Read-only diagnosis (no profile changes)

### Did SOUL reach her?

| Check | Result |
|---|---|
| Live `SOUL.md` hash | `B4163D7EC004FAFF3FB2F4D9F99029E14747BB4D695BF0ABA65D6D45C619C031` = approved after-hash ✅ |
| Apply mtime | 2026-10-06 **15:33:29** |
| Serve / client start | **15:33:45** / **15:33:44** (PIDs 9884/5972/25284) |
| Remeasure first user turn | **18:47:03** (session `20261006_153348_3bd3c0`) — after apply+restart ✅ |
| Assembled system prompt | `system_prompts` hash `6d9ab116…` for this session contains `## Everyday answers` + “Any arithmetic follows…” ✅ |

**Verdict:** SOUL change was loaded. Failure is **outrank / conflict**, not a missed deploy.

### B1 (Tokyo)

- **skill_view** opened: `everyday-assistance`.
- Skill headings: `# Everyday Assistance`, `## When to Use`, `## Procedure`, `## Pitfalls`, `## Verification`.
- Time lines (short): Procedure §1 — *“For a time-zone question, calculate from the conversation's current timestamp and the destination's UTC offset when daylight-saving status is known; look it up when that status is uncertain.”*; also *“for calculations, use the calculator tool rather than a terminal or code runner.”*
- **Terminal 1** (allowed): `TZ=Asia/Tokyo date '+%A, %B %-d, %-I:%M %p JST (UTC%:z)'` → wrong offset in output (`UTC+00:00`).
- **Terminal 2** (blocked): `python -c "from datetime import datetime; from zoneinfo import ZoneInfo; …Asia/Tokyo…"`.
- Dangerous pattern: **`script execution via -e/-c flag`** — `approval_detection.py` `_execution_flag_findings` **L917** (returned via `detect_dangerous_command` **L1439–1440**). Alias table L429.
- After block, answer time only: **10:47 AM Wednesday in Tokyo** (accurate per Brian).

### B2 (cups)

- Path: `tool_describe(calculate)` → `calculate(expression="4")` → “Four cups.”
- No separate “reason” string in logs beyond tool_calls.
- Drivers: skill **Verification** — *“any conversion is tool-calculated”* (SKILL.md L44); Procedure §1 pushes calculator for calculations. `calculate` schema is **arithmetic only** (`zola_tools/__init__.py` L22–27) — units out of scope — so she described then ran a trivial `4`. “Doing math” (SOUL) steers precision arithmetic to the calculator; it does **not** mention unit conversions (those are under Everyday answers). Skill Verification still pulls conversions to a tool.

### What outranks SOUL for times/numbers

| Lever | Where | Encouragement |
|---|---|---|
| **Hermes mandatory tool use** | `hermes-agent/agent/prompt_builder.py` **L411–419** (`OPENAI_MODEL_EXECUTION_GUIDANCE`) | “NEVER answer from memory… Current time, date, timezone → use terminal”; also “Arithmetic… → use terminal or execute_code” |
| **Act don’t ask** | same file **L423–428** | “‘What time is it?’ → run `date`” |
| **Skills MUST load** | `prompt_builder.py` **L1322–1331** (`## Skills`) | If a skill is even partially relevant, **MUST** `skill_view` and follow it |
| **Skills index** | live prompt / skills index | `everyday-assistance: Handle quick everyday questions…` (matches time/conversion) |
| **Skill body** | live `skills/…/everyday-assistance/SKILL.md` **L26, L44** | Time: stamp math or look up; conversions: **tool-calculated** |
| **SOUL Everyday answers** | live SOUL L64–72 (in prompt) | Answer zone/units **without tools** — **lost** to the above |
| **SOUL Doing math** | SOUL after Everyday | Calculator for precision arithmetic (kept; not the B2 bug by itself) |
| **`calculate` tool desc** | `zola_tools/__init__.py` L22–27 | Arithmetic only — does not teach cups→quart; encourages describe+noop path |

UTC offset stamp change: keep live (verified in `api_content`).

### Revised candidates (do not apply)

1. **Edit `everyday-assistance`** (Brian’s call): Procedure/Verification — zone time from stamp UTC offset (look up only if DST unsure); common conversions as **direct facts**, not tool-calculated. Highest leverage inside P7-D10.
2. **Reword SOUL Everyday answers** so conversions are explicitly “stated facts, not math / not calculate” — secondary; alone may still lose to skill MUST-load + Verification.
3. **File Hermes conflict** (`mandatory_tool_use` time→terminal) — out of Phase 7 (Hermes edit / P7-D10).
4. **Revert SOUL Everyday answers**; keep UTC offset — if Brian wants a clean slate before a skill-first fix.
5. **`calculate` + units** — still optional; does not fix B1 terminal path; B2 would still be a tool turn.

**Brian Track 3 verdict (verbatim):** "C: close on findings (Recommended)"  
**Brian SOUL verdict (verbatim):** "Revert it (Recommended)"

## Phase 6c — Close on findings (SOUL revert; offset kept)

### SOUL revert

| | |
|---|---|
| Restored from | `zola-spikes/p7-latency/SOUL.md.bak-P7-LATENCY-20261006_153304` |
| Live `SOUL.md` SHA-256 | **`E3D7BF9AC29B46237A2685BEBAE2E89E1A5952EDB23E5AFEEE0EE8363009FB49`** ✅ |
| `identity/SOUL.md` | same hash; **no repo SOUL.md diff** |
| `## Everyday answers` | absent |

### UTC offset (kept)

| File | Live = Repo SHA-256 |
|---|---|
| `time_context.py` | `327A027A740D4CD4DAA6A046245A0B44606DC39B774BAECACDB5A327597BC1BE` |
| `__init__.py` | `7FAA42BC030B329EB5F078B80EC45183104105361A29E880EAC3CCCCF9994C11` |
| `provider.py` | `E292093763665B0A35E38C67166F84E372493D4F4016704F006217A15E76A18A` |
| `store.py` | `C471EA121F993BD00D5E68EEF0DEFB92FBDD3D606774CA78B89ADF1B34CB00E8` |
| `retrieve.py` | `53D8044D896F6F769AA10EF99BAB67083ADF19AA3E01858A067A870916C0290D` |
| `consolidate.py` | `1B2D8D8AD8140EC515D184279DD3BD541952918025ADEDF47761944AE14941C2` |
| `fact_index.py` | `AA0CCE9E599BA94F933A8619E2094D3A21192BD4AA785510A9D28FBC53D81B02` |
| `forget.py` | `A9B62AA822DBAD0A350FE84CB004C4E63124F4FBEA98F591D4454EDDCC1BB306` |
| `log.py` | `A2515A96171B2F9B4AB7947A41A7C7181DB3DCA6F636298C11A7373AAFDC1B62` |
| `llm_access.py` | `EC5A8F319628CB24DEEB0177397D34B754A51B30F80C025D4F93D5E5189FEC57` |
| `registry.py` | `86AA4DA04D67AB911D569AB1D9774A86E1A36F75F9B1931D49CA3F0272EE771D` |
| `pending.py` | `9FF6156CD946C08BFD737EDFFC15C6DAE2D865AB0C34ED332F48056DDA854769` |

Plugin suite after keep: **112 tests OK**.

### Root cause of AUD-25 (findings, not a fix)

Hermes injects `OPENAI_MODEL_EXECUTION_GUIDANCE` for her model family:

- Gating: `EXECUTION_GUIDANCE_MODELS` `prompt_builder.py` **L333–348**; applied in `system_prompt.py` **L520–522** via `_model_gate` (**L40–51**).
- Text: `OPENAI_MODEL_EXECUTION_GUIDANCE` **L402–431**; rendered by `execution_guidance_text` **L469–478**.
- Includes `<mandatory_tool_use>` (NEVER answer time/date/timezone from memory → **terminal**; arithmetic → terminal/execute_code) and `<act_dont_ask>` (“What time is it?” → run `date`).
- Also carries: tool persistence, prerequisite checks, verification, read-back / grounding discipline (same block).
- **Outranks SOUL.md.** Reinforced by skills-block MUST-`skill_view` (**L1322–1331**) and `everyday-assistance` Procedure/Verification.

**Switch (unchanged):** `agent.execution_guidance` — read in `agent_init.py` **L1312** (`config` → `agent._execution_guidance`, default **`"auto"`** from `config_defaults.py` **L132**). Live `config.yaml` has **no** override → auto. Values: `auto` | `true`/`false` (and synonyms via `_GATE_WORDS` L37: always/yes/on, never/no/off) | list of model-name substrings (`system_prompt.py` L40–51; docs `configuration.md` ~L1842).

**B1 evidence:** `TZ=… date` returned wrong time on Windows; `python -c` blocked (L917/L1439–40); her post-block answer **10:47 AM Wednesday** was correct. Tool rounds added ~**20 s** with no accuracy benefit.

### Filed for Phase 8

| | |
|---|---|
| (a) | Decision on `agent.execution_guidance` — own audit (what each part protects, broad regression, possible SOUL replacement for good parts) |
| (b) | Upstream: time/date rule vs trusted time context; `TZ=`+`date` wrong on Windows |
| (c) | Streaming-TTS bake-off (ElevenLabs/OpenAI/Gemini/xAI streamers at pin; Edge none; Cartesia not built-in) — Brian |
| (d) | Track 4 / S34: one-sentence replies speak only after full stream; Brian: speech starts seconds after text |

### Sanity turn (2026-10-07 ~07:11)

| Field | Value |
|---|---|
| Session | ui `e02176b7` / agent `20261007_071042_c9c538` |
| Line | “Hey Zola, what time is it?” |
| Brian | "Reply is normal. The tool took a long time so the response was slow. She gave the correct time. It's 7:11AM." |
| Answer | “It’s 7:11 AM.” |
| Stamp | `[Time: Wed Oct 7, 7:11 AM PDT (UTC−07:00)]` ✅ |
| SOUL in prompt | `Everyday answers` **absent**; Doing math present ✅ |
| Tools | `skill_view(everyday-assistance)` + `terminal` → `Wednesday, October 7, 7:11 AM PDT` |
| `turn_timing` | turn=10 voice t2s=34 **s2d=19298** s2c=20028 **s2a=23000** tools=2 approval=0 |

Confirms: offset live; SOUL revert loaded; AUD-25 path still active on a plain local-time ask (~23 s submit→audio).

## Phase 6 STOP — pre-closeout packet

**Revert:** SOUL `E3D7BF9A…` (live + identity). **Offset kept:** `time_context.py` `327A027A…` live=repo; suite 112 OK.

**Sanity:** normal correct 7:11 AM; stamp has `(UTC−07:00)`; slow via tools (s2a 23000 ms).

**Exit table:** causal B1/B2 ❌ acknowledged (close on findings); measurement/LT-G* ✅; SOUL fix reverted / offset kept ⚠️; scratch/backups ⏳ closeout.

## Phase 7 — Closeout

### 7a — Verify

| Check | Result |
|---|---|
| `dotnet build` Zola.Client win-x64 | **PASS** (0 warnings/errors) |
| Zola.Client.Checks | **PASS** exit 0; timing rows **8/8** |
| `zola_memory` plugin suite | **112 OK** |
| hermes-agent HEAD | `345cd2b057a452236de401d3534b8502a7465e8d` clean |
| Live `SOUL.md` | `E3D7BF9A…` (= Phase 1 / post-revert) |
| Live `time_context.py` | `327A027A…` (= repo; UTC offset kept) |
| Live `config.yaml` | `7BA2E676…` (= Phase 1 unchanged) |
| Causal B1/B2 | ❌ **NOT MET** — developer ack: Brian "C: close on findings (Recommended)" |

### Exit Criteria Verification (PHASE7_BUILD_PLAN.md Track 3)

| Criterion | Status | Evidence |
|---|---|---|
| `turn_timing` + join + baseline; EoS→audio median + stage shares | ✅ | Phase 3/4 tables; corrected additive shares |
| LT-G1 settles AUD-26 | ✅ | **in-call**; standalone ~1006 ms vs H-1 ~750; live residual noted |
| LT-G2 + LT-G3 | ✅ | 91% short-factual tools; pause max 1360 ≪ silence 1500 |
| Brian STOP + fix under rules | ⚠️ | Close on findings; SOUL Everyday **reverted**; UTC offset **kept** (plugin tests OK) |
| HUMAN-RUN causal target B1/B2 | ❌ | Ack’d — root cause `execution_guidance` / mandatory_tool_use (Phase 8) |
| Scratch deleted; backups after merge | ⏳ | 7j |
| hermes-agent clean; profile only approved | ✅ | hermes clean; SOUL restored; offset approved/kept |

### Final file list (G-SCOPE)

**New:** `windows-client/Zola.Client/Voice/TurnTiming.cs`; `zola-architecture/lore/prompts/progress/P7-LATENCY_Progress.md`

**Modified:** `VoiceController.cs`, `MainWindow.xaml.cs`, `Zola.Client.Checks/Program.cs`, `Zola.Client.Checks.csproj`, `hermes-plugins/zola_memory/time_context.py`, `hermes-plugins/zola_memory/tests/test_zola_memory.py`

**Live profile:** `plugins/zola_memory/time_context.py` → `327A027A…`; `SOUL.md` unchanged from Phase 1 (`E3D7BF9A…`)

### Implementation / merge SHAs

| | SHA |
|---|---|
| Implementation (7e) | `1fc463abc19aa4ee61c575256fc5469119471ea6` |
| Merge on main (7h) | *(pending)* |
| Final main HEAD (7i) | *(pending)* |
