# Zola S51F-PRE — Progress

**Prompt:** `C:\Users\test\Dev\zola-spikes\prompts\S51F-PRE_Prompt_v1.0.md`  
**Prompt SHA-256 (verified match):** `58d9c461b6ee5086bdef0ba4e573132b96735aad3715721a8eec6ab1d27d58e8`  
**Audit started:** 2026-11-09  
**SOP:** v3.0 (transition) · Stage 1 (audit) + approved live-profile change S51F-D01 under P4-D25  
**Decision:** S51F-D01 — turn thinking sound off

---

## Repositories

| Repo | Branch / state | HEAD | Clean? |
|------|----------------|------|--------|
| `zola-windows` | `s51f-pre` (from `main`) | `5302548dcb1e63d3b2893a86c241936e0d50c413` at branch create | yes at create |
| `hermes-agent` | detached pin | `345cd2b057a452236de401d3534b8502a7465e8d` | yes |

`main` = `origin/main` = `5302548dcb1e63d3b2893a86c241936e0d50c413` (matches prompt expected or later). Working tree was clean before branch create.

---

## Folders

| Role | Path |
|------|------|
| Output | `zola-architecture/audit/s51f-pre/` |
| Progress | `zola-architecture/audit/s51f-pre/Zola_S51F_PRE_PROGRESS.md` |
| Live profile | `%LOCALAPPDATA%\hermes\profiles\zola\config.yaml` |
| Evidence (read-only) | `C:\Users\test\Dev\zola-spikes\s51-crash\evidence\` |
| Binding prior audit | `zola-architecture/audit/s51-crash/` |

Finding IDs: `S51F-AUD-NN`.

---

## Guardrails (summary)

G-SCOPE · G-P4-D25 · G-NO-RESTART · G-NO-REPRO · G-LOGS · G-EVENTLOG · G-DUMP-PRIVACY · G-LIVE · G-HONEST · G-INTEGRATION · G-NO-FIX · G-STOP · G-CLOSEOUT (wait for exact words).

---

## Phase status

| Phase | Status |
|-------|--------|
| 1 Setup and the exact change | **COMPLETE** |
| 2 Apply, record, relaunch, smoke | **COMPLETE** |
| 3 Remaining PortAudio stream users | **COMPLETE** → `Zola_S51F_PRE_01_Streams.md` |
| 4 "Let me look" before tool | **COMPLETE** → `Zola_S51F_PRE_02_Acknowledgement.md` |
| 5 Lost-request handling | **COMPLETE** → `Zola_S51F_PRE_03_LostRequest.md` |
| 6 Better evidence next time | **COMPLETE** → `Zola_S51F_PRE_04_Diagnostics.md` |
| 7 Synthesis | **COMPLETE** → `Zola_S51F_PRE_SYNTHESIS.md` |
| 8 Closeout | **IN PROGRESS** |

---

## Phase 1 — Setup and the exact change

### 1. Setup (EVIDENCE)

- Prompt SHA-256 verified: `58d9c461b6ee5086bdef0ba4e573132b96735aad3715721a8eec6ab1d27d58e8`.
- `zola-windows`: `main` = `origin/main` = `5302548d…`; clean; branch `s51f-pre` created; output folder created.
- `hermes-agent`: HEAD = pin `345cd2b…`; clean (detached).

### 2. Live `config.yaml` keys only (EVIDENCE)

| Field | Value |
|-------|-------|
| Path | `%LOCALAPPDATA%\hermes\profiles\zola\config.yaml` |
| SHA-256 | `823dbd95c6d63eb66be07182faa82acb5c48528a79f01109b6c4120560c74afc` |
| `voice:` block | present at line 79 |
| `voice.thinking_sound` | `true` (expected) |
| Exact line (indent included) | `  thinking_sound: true` (2 spaces; line 83) |

Voice keys observed (no values beyond the gate key beyond structure): `silence_duration`, `barge_in`, `stop_phrases`, `thinking_sound`. Gate is under `voice:` — proceed.

### 3. What `voice.thinking_sound: false` does (SOURCE)

| Claim | Cite | Label |
|-------|------|-------|
| Flag read via `_voice_config().get("thinking_sound", True)` inside `thinking_sound_enabled()` | `tools/voice_mode.py` L424–428; `_voice_config` in `tools/voice_mode_transcript.py` L10–16 → `load_config()` | SOURCE |
| `start_thinking_sound` returns `False` and **does not** start the thread when disabled | `tools/voice_mode.py` L476–481 (`if not thinking_sound_enabled(): return False` before `Thread(..._thinking_sound_loop...)` at L487–488) | SOURCE |
| `_thinking_sound_loop` only runs on that daemon thread | `tools/voice_mode.py` L449–473; started only from `start_thinking_sound` L487–488 | SOURCE |
| Serve / TUI gateway arms it **per turn** via `_start_turn_voice` → `start_thinking_sound(...)` | `tui_gateway/prompt_turn.py` L183–203 | SOURCE |
| CLI chat path similarly calls `start_thinking_sound` while a turn's agent thread runs | `hermes_cli/cli_chat_turn_mixin.py` L363–370 | SOURCE |
| Config is not launch-only: each `start_thinking_sound` re-checks `thinking_sound_enabled()` → `load_config()` (mtime/size cache) | `voice_mode.py` L480; `voice_mode_transcript.py` L10–16; `hermes_cli/config.py` L1979–1983 | SOURCE |

**Verdict:** with `thinking_sound: false`, the thinking-sound thread is never started. Serve re-reads the gate on each turn that would arm thinking sound (not only at process launch). Phase 2 still requires a full relaunch for crash-watch start and clean serve-after-edit.

### 4. Crash-watch baseline (EVIDENCE — Application log)

Most recent `python.exe` Application Error (Id 1000) **before** any Phase 2 edit:

| Field | Value |
|-------|-------|
| TimeCreated | 2026-11-09 08:21:50 AM (local) |
| Faulting process id | `0x88B4` = **34996** |
| Exception code | `0xc0000005` |
| Faulting module | unknown |
| App path | `...\uv\python\cpython-3.12-windows-x86_64-none\python.exe` |

Prior same-day crash: 2026-11-09 07:51:27 AM, pid `0x9BA8` = 39848 (also `0xc0000005`). Crash watch itself starts at the Phase 2 relaunch time (not yet).

### 5. Proposed edit (P4-D25)

Shown in Phase 1 STOP; applied in Phase 2 after approval below.

---

## Phase 2 — Apply, record, relaunch, check

### Brian approval (verbatim)

> Approved: back up config.yaml as config.yaml.bak-S51F-\<timestamp\>, then change the one line thinking_sound: true → thinking_sound: false, nothing else. Proceed to Phase 2.

### 1. Live config edit (EVIDENCE · P4-D25)

| Field | Value |
|-------|-------|
| Backup | `%LOCALAPPDATA%\hermes\profiles\zola\config.yaml.bak-S51F-20261109-102200` |
| Backup SHA-256 | `823dbd95c6d63eb66be07182faa82acb5c48528a79f01109b6c4120560c74afc` (= pre-edit live) |
| Live SHA-256 after | `8ea0f37db0cb296de7cf0fd47f7953c01b75bc925d5bb9caf8bcba1ad3ddadf9` |
| Diff vs backup | exactly one line: `  thinking_sound: true` → `  thinking_sound: false` |
| Byte delta | 4850 → 4851 (+1; `false` vs `true`) |

### 2. `VOICE_CONFIG.md` (EVIDENCE)

Three edits applied (CRLF kept): YAML `thinking_sound: false`; bullet rewritten for S51F-D01; tuning-log row after `tts.provider` / `deepgram` / 2026-10-12.

| Check | Result |
|-------|--------|
| Bytes | 18,358 |
| Lines | 228 |
| Line endings | CRLF |
| SHA-256 | `4a09790788660f7132f07d0f4b0e109aeb4f630276dc63c3b2fa18dea929cb58` (matches prompt expected) |

### 3. Relaunch / crash-watch start (EVIDENCE)

| Process | Pid | StartTime (local) |
|---------|-----|-------------------|
| `Zola.Client` | 28424 | 2026-11-09 11:40:54 |
| watcher (`-m zola_workspace.watcher`, venv) | 47524 | 2026-11-09 11:40:56 |
| phone (`-m zola_phone`, venv) | 6136 | 2026-11-09 11:40:56 |
| **serve** (`hermes_cli.main -p zola serve`, venv) | **31636** | **2026-11-09 11:40:57** |
| serve interpreter (uv cpython) | 18244 | 2026-11-09 11:40:57 |

Supervisor: watcher/phone `job_assigned` at 11:40:56. Serve-stderr mtime / session stamp `20261109_114109` → listening ~**11:41:09**.  
**Crash-watch start:** **2026-11-09 11:40:57** (serve start; after config edit at ~10:22).  
`python.exe` Application Error since watch start: **none** (as of Phase 2 close).

### 4. Smoke — Brian report (verbatim intent)

> S1: There is a beep after my speech. No soud while thinking. She overheard herself twice during the process.  
> S2: She did not state "Let me look". No thinking sound.

| Check | Brian | Expect |
|-------|-------|--------|
| Thinking sound S1 | no ("No soud while thinking") | none |
| Thinking sound S2 | no | none |
| S2 "let me look" / similar before answer ready | no ("did not state") | audit question (not a pass/fail of D01) |
| Beep after speech (S1) | yes | remaining shared-stream user (Phase 3) |
| Self-echo | twice during S1 process | known speech-track issue (INFO / out of scope for fix track) |

### 4b. Smoke — allowlisted log timeline (EVIDENCE · MEASURED)

G-LOGS: times, event names, lengths, tool names, durations only. No transcript/reply/calendar text.

**Thinking-sound log events since relaunch:** none in agent/gui/errors/voice-timeline/serve-stderr (search: `thinking sound`, `thinking_sound`, `voice-thinking`, `play_beep`). Matches Brian + `thinking_sound: false`.

**S1 cluster (no-tool, then two follow-up turns — aligns with Brian's two self-overhears):**

| Turn | Submit window | tools | submit→first_delta | submit→complete | submit→first_audio |
|------|---------------|-------|--------------------|-----------------|--------------------|
| 1 | ~11:45:32 | 0 | 4789 ms | 6533 ms | 8014 ms |
| 2 | ~11:45:54 (transcript len=59) | 0 | 2690 ms | 3910 ms | 22 ms |
| 3 | ~11:46:10 (transcript len=26) | 0 | 2738 ms | 3278 ms | 49 ms |

`Generating speech` (agent): 11:45:37, 11:45:38, 11:45:56, 11:45:59, 11:46:13.

**S2 (tool turn = client `turn_timing turn=4`, wake capture 12:12:55 → transcript len=31):**

| Milestone | Time (local) | Basis |
|-----------|--------------|-------|
| Wake / capture start | 12:12:55.037 | voice-timeline |
| Turn submit | ~12:13:01.50 | transcript admit + turn_timing; agent `conversation turn` 12:13:01.571 |
| Display Thinking | 12:13:01.480 | display-state |
| First tool completes | skill_view 12:13:06.580 (0.13s, 4673 chars); tool_describe 12:13:06.723 (0.27s, 905 chars) | agent `tool_executor` |
| calendar_query complete | 12:13:11.969 (1.54s, 3487 chars) | agent |
| First text delta | ~12:13:15.87 | submit + 14369 ms |
| First sentence | ~12:13:16.65 | submit + 15146 ms |
| `Generating speech` #1 / #2 | 12:13:16.612 / 12:13:22.866 | agent `tts_tool` |
| Reply complete (text) | ~12:13:18.16 | submit + 16663 ms; display Speaking 12:13:18.165 |
| First playback audio | ~12:13:23.51 | submit + 22003 ms (`first_sentence_to_first_audio_ms=6857`) |
| Bout stop / follow-up | bout_stop 12:13:48.398 | voice-timeline |

**S2 read for Phase 4:** first delta and first `Generating speech` are **after** tool completion. No spoken pre-tool acknowledgement in this smoke (Brian + MEASURED).

---

## Phases 3–7 (developer continue + three additions)

Developer: proceed with Phases 3–7; beep cue mapping; S2 pre-tool text analysis; record S1 self-echo turns under out-of-scope INFO.

| Doc | Path |
|-----|------|
| 01 Streams + beeps | `Zola_S51F_PRE_01_Streams.md` |
| 02 Acknowledgement | `Zola_S51F_PRE_02_Acknowledgement.md` |
| 03 Lost request | `Zola_S51F_PRE_03_LostRequest.md` |
| 04 Diagnostics | `Zola_S51F_PRE_04_Diagnostics.md` |
| Synthesis | `Zola_S51F_PRE_SYNTHESIS.md` |

**Crash watch:** still running from **2026-11-09 11:40:57**; **0** `python.exe` Application Errors since start (as of Phase 7).  
**S2 pre-tool ack:** no (MEASURED).  
**Findings:** 13 — 2 HIGH, 6 MEDIUM, 2 LOW, 3 INFO.

### Beep cues (Phase 3 addition, summary)

| Cue | Code | Shared `sd.play` | Meaning |
|-----|------|------------------|---------|
| After speech / listen end | `hermes_cli/voice.py` 660 Hz × 2 | yes | Capture / listen window closed |
| Listen start (also in setup) | 880 Hz × 1 on `start_continuous` | yes | Listening opened |

### S1 self-echo (synthesis out-of-scope)

Turns 2 and 3 admitted: len=59 @ ~11:45:54; len=26 @ ~11:46:10.

---

## STOP — Phase 7

Await Claude review before the fix prompt. Closeout only on **"proceed to closeout"**. Crash watch keeps running.

---

## Phase 8 — Closeout

**Trigger:** `proceed to closeout` (2026-11-09).

### 8a Verify

- `git status` on `s51f-pre`: only `zola-architecture/audit/s51f-pre/` and `zola-architecture/identity/VOICE_CONFIG.md`.
- `VOICE_CONFIG.md` SHA-256 = `4a09790788660f7132f07d0f4b0e109aeb4f630276dc63c3b2fa18dea929cb58` (Phase 2 expected).
- `hermes-agent` clean at pin `345cd2b057a452236de401d3534b8502a7465e8d`.

### 8b Privacy

Allowlisted fields only in audit docs (times, pids, lengths, event names, tool names). No transcript/reply/email/contact/memory body text; no keys/tokens.

### 8c–8g SHAs

| Record | SHA |
|--------|-----|
| Audit commit | _(pending)_ |
| Tip-SHA commit | _(pending)_ |
| Merge on `main` | _(pending)_ |

Backup deleted (P6-D11): _(pending)_

---

## Phase 3 — Remaining PortAudio stream users

**Output:** `zola-architecture/audit/s51f-pre/Zola_S51F_PRE_01_Streams.md`

### Headline (SOURCE + MEASURED)

With `thinking_sound: false`, sites 3–4 (thinking loop) do not open PortAudio play. Sites 9–10 (barge) stay off (`barge_in: false`). **Still active:** record beeps via shared `sd.play` (site 1–2), `stop_playback`’s `sd.stop` (site 6), `AudioRecorder` InputStream (7–8), wake InputStream (11). Deepgram mp3 → ffplay does **not** use site 5 WAV/`sd.play`. Code read is client Zira/winmm, not Hermes PortAudio.

### Beeps Brian hears (A)/(B)

| Cue | Trigger | Play site | Shared `sd.play`? |
|-----|---------|-----------|-------------------|
| (A) after speech | VAD silence → `_continuous_on_silence` | `hermes_cli/voice.py` L491 `660 Hz × 2` | yes |
| (B) listening window end | same stop cue on silence/max_wait or `_finish_stop` | L491 or L456 `660 Hz × 2` | yes |
| Also: listen start | `start_continuous` before mic arm | L376 `880 Hz × 1` | yes |

`voice.beep_enabled` unset → default true. Supported off-switch: config `beep_enabled: false` (no Hermes fork); removes cues unless client/ffplay replacement (see streams doc §3).

### S1/S2 Settled correlation

Beeps not logged. **INFERENCE** from SOURCE order + **MEASURED** timeline: stop beep precedes `Settled signal=transcript`; follow-up idle ~15–16 s listen → `Settled signal=idle` matches `_max_wait` 15 s (gen=4 @ 11:46:43).
