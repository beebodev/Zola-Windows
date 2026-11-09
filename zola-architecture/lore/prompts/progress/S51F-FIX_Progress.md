# S51F-FIX — Progress

**Prompt:** `C:\Users\test\Dev\zola-spikes\prompts\S51F-FIX_Prompt_v1.1.md`  
**Prompt SHA-256 (verified):** `ca3f296c38c0ea025eabc847288cbe7c152d5fe5f6ff7d45a54471eab440d5dc`  
**Build plan:** `zola-architecture/lore/build-plans/S51F_BUILD_PLAN.md`  
**Plan on-disk SHA-256 (CRLF):** `7d7bc1a63391496449c2746f3bcfef02cfc7446da89b3e8e9b5a41ea58c1ecd3`  
**Plan staged blob SHA-256 (LF):** `fb8445eec2fc6e4a5d41d58f7844b9f0800382211ccf12233ebbffcd74eedfe7`  
**Started:** 2026-11-09  
**SOP:** v3.0 (transition) · Decisions S51F-D01–D06

---

## Repositories

| Repo | Branch | HEAD | Notes |
|------|--------|------|-------|
| `zola-windows` | `s51f-fix` | `9994677682625c2e7cb1d3e19534bbdc662a2b61` (after plan merge) | from `main` |
| `hermes-agent` | detached pin | `345cd2b057a452236de401d3534b8502a7465e8d` | clean, read-only |

**Base `main` before plan:** `702bb62906d197af943b8834430cf026642a1850` (= `origin/main`).  
**Plan commit:** `4d258973c3098fa1b957bc07514246d79d5754e9` (`docs: S51F build plan`).  
**Plan merge on `main`:** `9994677682625c2e7cb1d3e19534bbdc662a2b61`.  
Plan branch `s51f-build-plan` deleted locally (never pushed).

**Discrepancies:** none at setup. Phone floor set with Zola closed: **71 OK**.

---

## Guardrails (summary)

G-SCOPE · G-P4-D25 · G-ARCH · G-NO-RESUBMIT · G-NO-RESTART (SM2 kill exception) · G-LOGS / G-PRIVACY · G-TESTS · G-STOP · G-MERGE · G-ROLLBACK (live profile).

---

## Phase status

| Phase | Status |
|-------|--------|
| 1 Setup, plan commit, baselines, W1 proposal | **done** (W1 approved; phone floor 71) |
| 2 W1 apply / relaunch / check | **done** |
| 3 W2+W3 design proposal | **done** (notice approved) |
| 4 Implement W2+W3 | **done** |
| 5 Review fixes | **done** (incl. follow-ups 1–2) |
| 6 Smoke / experience | **done** |
| 7 Commit and merge | **done** |

---

## Phase 1

### 1. Setup (EVIDENCE)

- Prompt SHA verified.
- `main` = `origin/main` = `702bb62…` before plan; status showed **only** untracked `S51F_BUILD_PLAN.md`.
- `hermes-agent` clean at pin.
- Plan on-disk + staged LF blob SHAs matched developer values (Git Bash `git cat-file blob :… | sha256sum`).
- Plan committed, merged `--no-ff`, pushed; `s51f-fix` created from tip `9994677…`.

### 2. Test baseline (EVIDENCE)

Interpreter: `C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe` (3.12.14).

| Suite | Command | Result | Floor |
|-------|---------|--------|-------|
| `zola_workspace` | `cd hermes-plugins\zola_workspace`; `python -m unittest discover -s tests -t tests` | **582** OK (109.4 s) | 582 |
| `zola_memory` | `cd hermes-plugins\zola_memory`; `python -m unittest discover -s tests -t .` | **162** OK (12.8 s) | 162 |
| `zola_tools` | `cd hermes-plugins\zola_tools`; `python -m unittest discover -s tests -t .` | **44** OK | 44 |
| `zola_tts` | `cd hermes-plugins\zola_tts`; `python -m unittest discover -s tests -t .` | **8** OK | 8 |
| `zola_phone` | `cd hermes-plugins\zola_phone`; `python -m unittest discover -s tests -t .` | first run with live client: **71** ran, **2 failed** (mutex); re-run Zola closed: **71 OK**, EXIT=0 (~35.6 s) | **71** |
| Client build | `dotnet build windows-client\Zola.Client\Zola.Client.csproj -r win-x64 -c Release -o %TEMP%\zola-s51f-fix-client-build` | succeeded, 0 warnings, 0 errors | build OK |
| `Zola.Client.Checks` | `dotnet run --project windows-client\Zola.Client.Checks\Zola.Client.Checks.csproj -c Release` | **250** PASS / **0** FAIL | 250 |
| Kotlin companion | `android-companion\gradlew.bat testDebugUnitTest assembleDebug --offline` (`JAVA_HOME`=Android Studio JBR; gitignored `local.properties` sdk.dir) | **98** unit tests, 0 fail/error/skip; BUILD SUCCESSFUL | 98 |

**Phone floor (Zola closed, 2026-11-09 ~13:15):** first baseline failed mutex tests with live `Zola.Client` pid **28424**. After Brian closed Zola: `Ran 71 tests in 35.629s` / `OK` / `EXIT=0`. No `Zola.Client` process. Floor = **71**.

### 3. W1 facts (EVIDENCE / SOURCE)

| Field | Value |
|-------|-------|
| Path | `%LOCALAPPDATA%\hermes\profiles\zola\config.yaml` |
| SHA-256 | `8ea0f37db0cb296de7cf0fd47f7953c01b75bc925d5bb9caf8bcba1ad3ddadf9` |
| `voice.beep_enabled` present? | **No** |
| `voice.thinking_sound` | `false` (line 83; from S51F-D01) |
| Line insertion would follow | `  thinking_sound: false` (2 spaces; exact) |
| Default when key absent | `True` (`config_defaults.py` L1147; `_beeps_enabled` uses `.get("beep_enabled", True)` L143) |
| `false` before PortAudio? | **Yes** — `_play_beep` returns at L152–153 before importing/`play_beep` (`hermes_cli/voice.py` L132–157) | SOURCE |

Voice block (keys only, structure):

```
voice:
  silence_duration: …
  barge_in: …
  stop_phrases: …
  thinking_sound: false
```

### 4. W1 proposal (P4-D25) — approved, then applied in Phase 2

- **Backup:** `%LOCALAPPDATA%\hermes\profiles\zola\config.yaml.bak-S51F-FIX-<yyyyMMdd-HHmmss>`
- **Change:** one-line **insertion** after `  thinking_sound: false`:

| | Exact text |
|--|------------|
| Before (preceding line stays) | `  thinking_sound: false` |
| After (new line) | `  beep_enabled: false` |

- Indentation: 2 spaces (same as siblings). Nothing else.

**Brian approval (verbatim):**  
> Approved: insert one line beep_enabled: false directly after thinking_sound: false in the voice: block, at the same indentation as that line.

---

## Phase 2 — W1 apply (partial; awaiting Brian relaunch)

### 1. Config apply (EVIDENCE)

| Field | Value |
|-------|-------|
| Backup path | `C:\Users\test\AppData\Local\hermes\profiles\zola\config.yaml.bak-S51F-FIX-20261109-131403` |
| Original SHA-256 | `8ea0f37db0cb296de7cf0fd47f7953c01b75bc925d5bb9caf8bcba1ad3ddadf9` |
| New SHA-256 | `f5b4829410e4c89feb2832cfffab02ebfa978bdc283cdf65e490b15e33c938c3` |
| Diff vs backup | **exactly one line added** |

Inserted line with leading spaces visible (`·` = space):

```
··beep_enabled:·false
```

HEX of that line: `20-20-62-65-65-70-5F-65-6E-61-62-6C-65-64-3A-20-66-61-6C-73-65`

Voice block after edit (spaces as `·`):

```
voice:
··silence_duration:·1.5
··barge_in:·false
··stop_phrases:·["stop"]
··thinking_sound:·false
··beep_enabled:·false
```

One-line diff against backup:

```
+  beep_enabled: false
```

### 2. VOICE_CONFIG.md (EVIDENCE)

| Check | Value |
|-------|-------|
| Repo SHA before | `4a09790788660f7132f07d0f4b0e109aeb4f630276dc63c3b2fa18dea929cb58` (match) |
| Source | `C:\Users\test\Dev\zola-spikes\prompts\S51F-FIX_VOICE_CONFIG.md` |
| Copy method | `Copy-Item` byte-for-byte (no editor) |
| SHA after | `4c12f3f47fe8376c75bb6499655cc7fee9457d30a039c59dc84e327f6f5b63eb` (match; CRLF=231, LF-only=0) |

`git diff --stat`:

```
 zola-architecture/identity/VOICE_CONFIG.md | 3 +++
 1 file changed, 3 insertions(+)
```

Three added lines (content):

- `  beep_enabled: false`
- `- \`voice.beep_enabled\`: \`false\` (\`S51F-D03\`, … PortAudio / presence UI / \`beep_volume: 0\` ruled out …)`
- table row: `voice.beep_enabled` \| `false` \| `2026-11-09` \| S51F-D03 …

### 3. Relaunch (EVIDENCE)

Brian started Zola the normal way (already closed beforehand). Recorded 2026-11-09 ~13:25:

| Process | Pid | Start |
|---------|-----|-------|
| `Zola.Client` | **40132** | 13:23:05 |
| `hermes … serve --isolated` (venv launcher) | **45452** | 13:23:08 |
| `hermes … serve` (worker) | **32056** | 13:23:08 |
| `zola_workspace.watcher` | 24496 / 32952 | 13:23:07 |
| `zola_phone` | 41788 / 42284 | 13:23:07 |

**New crash-watch start:** **2026-11-09 13:23:08** (serve up; neither thinking sound nor beeps use the shared stream).

### 4. Quick check (Brian)

Verbatim: “Test ran. No beeps were heard.”  
Listening check (verbatim): “I can tell when she is listening”

### 5. Crash watch

Since **2026-11-09 11:40:57** (Application Error Id=1000, `python.exe`): **none** (checked 13:25).

### 6. G-ROLLBACK

| Item | Value |
|------|-------|
| Backup full path | `C:\Users\test\AppData\Local\hermes\profiles\zola\config.yaml.bak-S51F-FIX-20261109-131403` |
| Original SHA-256 | `8ea0f37db0cb296de7cf0fd47f7953c01b75bc925d5bb9caf8bcba1ad3ddadf9` |
| Live SHA-256 | `f5b4829410e4c89feb2832cfffab02ebfa978bdc283cdf65e490b15e33c938c3` |
| Outcome | Keep backup in place. Wake/follow-up worked for Brian’s test; no beeps. No restore. `VOICE_CONFIG.md` remains at issued SHA `4c12f3f4…`. |

---

## Phase 3 — W2 + W3 design (proposal only; no edits)

### Pre-Phase-3 floor / rollback anchors

**(a) `zola_phone` re-run (Zola closed):**  
Command: `cd hermes-plugins\zola_phone`; Hermes venv `python -m unittest discover -s tests -t .`  
Result: **Ran 71 tests**, **0 failed**, **0 skipped**, `OK`, `EXIT=0` (~35.6 s). **Floor = 71.**

**(b) Config backup:**  
Full path: `C:\Users\test\AppData\Local\hermes\profiles\zola\config.yaml.bak-S51F-FIX-20261109-131403`  
Original `config.yaml` SHA-256: `8ea0f37db0cb296de7cf0fd47f7953c01b75bc925d5bb9caf8bcba1ad3ddadf9`

### W2 — LostTurnNotice (S51F-D04)

**In-flight detection (at gap):** open iff `!_turnFinalized && (_streaming || TurnTiming.IsOpen)`.  
Fields: `MainWindow._turnFinalized`, `MainWindow._streaming`, `TurnTiming.IsOpen` (`_submitAt != default && !_written`).

**Deliberate vs crash:** `ProcessSupervisor.NoteLoss` returns immediately when `_backend.IsShutdown || _backend.Policy.IsDeliberate` (`RestartPolicy.NoteDeliberateStop` / shutdown). That path never calls `OutageGap.Apply` → `WindowGap.BlockInput` → `ShowSupervisionStatus`. `LostTurnNotice` still takes `deliberate` and returns none.

**Idempotency:** applying the notice sets `_turnFinalized = true` and records applied-for-this-turn; a second unreachable sees finalized / already-applied → no second notice. Turn already finalized (reply complete; speech may still play) → none.

**SM2 log:** existing `voice-timeline.log` line `turn_timing turn=… kind=… submit_to_complete_ms=…` is written only after `TurnTiming.Finalize` (complete + first audio, or complete + 15s). UI `_turnFinalized` is set earlier in `FinishTurn` on `message.complete`. Propose **one new timeline line** (fields only): `turn_ui_finalized status=complete|error|interrupted|lost` when `FinishTurn` / lost-notice runs, so SM2 can confirm open vs closed at kill. Long-answer text keeps arriving until `message.complete` (often tens of seconds); speech may continue after.

**Where the notice appears:** existing transcript system line — `AddBubble("System", text, mine: false)` (same as `/compress`). Status line stays `SupervisionConstants.StatusRestarting`. Partial reply: `StyleLive("interrupted", keptText, …)` → badge **"Interrupted"** (existing chrome).

**Brian will see:** his You bubble; any partial Zola bubble with Interrupted badge (text kept, not streaming); then a System bubble with the notice; status “Zola's backend stopped. Restarting…”.

**Proposed constants (Brian approval needed):**
- `SupervisionConstants.LostTurnNoticeText` = `Your last request didn't go through. Ask again.`
- Interrupted marker: existing badge text `Interrupted` (no new string unless Brian wants one)

**Clarify / approval / proactive (G-NO-RESUBMIT):** gap already calls `AbandonPendingQuestion(GapReason)`, `DropPendingTranscriptForOutage` (no submit/AnswerClarify), stops playback, blocks input. W2 only finalizes the live bubble + adds the System line + marks turn finalized. Does **not** re-submit, does **not** change `ServerRequestBroker` / approval / clarify / proactive beyond that existing gap path.

**Class:** `Supervision/LostTurnNotice.cs` (pure).  
Inputs: `deliberate`, `turnFinalized`, `streaming`, `timingOpen`, `alreadyApplied`, optional `partialText`.  
Outputs: `ShouldNotice`, `SkipReason`, `FinalizeLiveAsInterrupted`, `NoticeText`.  
Wire from `ShowSupervisionStatus` (once per gap entry when in-flight). Tag `// S51F-FIX: … — S51F-D04`.

**Tests (Checks):** in-flight typed → notice; in-flight voice → notice; no open turn → none; deliberate → none; second unreachable same turn → no second; already finalized (speech may play) → none; partial text kept + interrupted mark.

### W3 — Diagnostics (S51F-D06)

**Start-info sites:**
1. `HermesProcessManager.SpawnAsync` — serve `ProcessStartInfo` (not via `PythonStart`)
2. `PythonStart.Build` — watcher + phone via `SupervisedPython.Spawn`

**Helper:** `PythonStart.ApplyFaultHandler(ProcessStartInfo start)` sets only `PYTHONFAULTHANDLER=1`. Call from `Build` and from serve `SpawnAsync`. Tag `// S51F-FIX: … — S51F-D06`.

**Stderr today (all kept; no new log file):**
| Process | Destination |
|---------|-------------|
| serve | `%LOCALAPPDATA%\ZolaClient\logs\serve-stderr\serve-stderr.log` (`ServeStderrLog`, redirected) |
| watcher | `{HERMES_HOME}\logs\zola_watcher.out.log` (stdout+stderr merged via `SupervisedPython`) |
| phone | `{HERMES_HOME}\logs\zola_phone.out.log` (same) |

**Pids:** launcher = `Process.Id` after `Start()`. Interpreter child: WMI `Win32_Process` where `ParentProcessId=launcher` (same `System.Management` already used for dedicated-serve discovery) — no new package. If none found, log launcher only and say so.

**Log format (extend `SupervisionLog.Format`):**  
`supervisor proc=… event=… restarts=… generation=… launcher_pid=N [child_pid=M]`  
Emit on start / stale / restart (serve + watcher + phone). Existing bare `pid=` call sites migrate to `launcher_pid`.

**Tests:** env helper present for serve/watcher/phone start info, other vars unchanged; log formatting includes pid fields.

---

## Phase 3 close

**Brian approval (verbatim notice):** “Sorry, your last request didn’t go through. Please ask again.”  
(Brian’s words: “I guess the first one for now.”) Stored as `SupervisionConstants.LostTurnNoticeText`.

---

## Phase 4 — Implement W2+W3 (EVIDENCE)

### Voice capture gap (condition)

Existing client state: `VoiceController.RecorderState == StateTranscribing` (`"transcribing"`) — capture ended / waiting for transcript from serve (`CaptureActive` stays true). Included in in-flight:  
`awaitingTranscript || (!turnFinalized && (streaming || timingOpen))`.  
Test: `lost turn notice while awaiting transcript after capture`.

**Not covered (G-ARCH gap, no new turn state):** the brief window after an admitted transcript is raised (`TranscriptReady`) but before `prompt.submit` / `NoteTurnSubmit` — `_pendingTranscriptAt` is private and is not a public “waiting to submit” turn flag. Listening (user still speaking) is also not treated as in-flight.

### W2 implemented

- `Supervision/LostTurnNotice.cs` + wire in `ShowSupervisionStatus` / `TryApplyLostTurnNotice`
- Notice constant exact Brian text; System bubble via `AddBubble("System", …)`; partial → Interrupted badge
- `turn_ui_finalized turn=… status=… time=…` (fields only) on FinishTurn and lost notice
- Idempotent via `_lostNoticeApplied`

### W3 implemented

- `PythonStart.ApplyFaultHandler` → serve + watcher + phone
- `ChildPidLookup`: off-thread, 500 ms cap, never awaited on restart; `child_pid=unknown` on fail/timeout; test with slow finder
- Log: `launcher_pid` + `child_pid` on start / job_assigned / stale / restart / keeps_failing when pid known

### SM2 timing (Phase 3 question)

Reply **text streams ahead of and overlaps speech**: deltas paint the live bubble first; streaming TTS can start a bout after the first sentence **while text is still arriving** (`NoteFirstAudio` can fire before `message.complete`). Text of a long answer keeps arriving until `message.complete` (often **tens of seconds**); speech may continue after complete (`TurnTiming.FinalizeSeconds` = 15 s wait for first audio after complete).

### Suites

| Suite | Result | vs floor |
|-------|--------|----------|
| Client build | 0 warn / 0 err | OK |
| `Zola.Client.Checks` | **263** PASS / 0 FAIL (supervision 51/51) | ≥ 250 |
| `zola_workspace` | **582** OK | = 582 |
| `zola_memory` | **162** OK | = 162 |
| `zola_tools` | **44** OK | = 44 |
| `zola_tts` | **8** OK | = 8 |
| `zola_phone` | 71 ran, **2 FAIL** mutex (Zola.Client live; G-NO-RESTART) | floor **71** from closed re-run still stands |
| Kotlin | UP-TO-DATE; BUILD SUCCESSFUL | 98 floor unchanged |

`hermes-agent` clean at `345cd2b…`.

`git diff` / untracked (allowed): client W2/W3 + Checks + `LostTurnNotice.cs` + `ChildPidLookup.cs` + `VOICE_CONFIG.md` + progress doc.

### Done checklist

- [x] Client builds clean
- [x] New tests present and passing; suites at/above Phase 1 floors (phone closed-floor retained; live-client mutex noted)
- [x] Diff limited to allowed paths

---

## Phase 5 — Review fixes (Claude)

### Apostrophe

`LostTurnNoticeText` now uses straight ASCII `'` (U+0027):  
`Sorry, your last request didn't go through. Please ask again.`  
Checks updated to match.

### Stale `transcribing` (no code change)

On unreachable via `OutageGap.Apply` → `WindowGap.InvalidateCapture` → `InvalidateCaptureForOutage`:

```
RecorderState = StateIdle;
```

(`VoiceController.cs` L1679; runs before `BlockInput` → `ShowSupervisionStatus`.)

On session recover, `OnSessionReady` → `InvalidateAndStopCaptureAsync` (orphan capture stop). Because the gap path already forces Idle at L1679, `transcribing` cannot remain across that restart to trigger a second notice for the same lost capture. **No clear/ignore change.**

### Admit→submit gap (for KNOWN_ISSUES; no code change)

Existing `voice-timeline.log` `turn_timing` field `transcript_to_submit_ms` (admit stamp → submit): **n=434**, **min=9 ms**, **max=159 ms**, **median≈22 ms** (typical ~20–40 ms). Record as known gap: crash in this window is not covered by LostTurnNotice without new turn state.

### Suites (Zola closed)

| Suite | Result | Floor |
|-------|--------|-------|
| Client build | 0 warn / 0 err | OK |
| `Zola.Client.Checks` | **263** PASS / 0 FAIL | ≥ 250 |
| `zola_workspace` | **582** OK | 582 |
| `zola_memory` | **162** OK | 162 |
| `zola_tools` | **44** OK | 44 |
| `zola_tts` | **8** OK | 8 |
| `zola_phone` | **71** OK | 71 |
| Kotlin | **98** (15+39+30+14), 0 fail/error/skip | 98 |

---

### Follow-up — awaitingTranscript never fired (Claude)

**Defect:** `OutageGap.Apply` calls `InvalidateCapture` (sets `RecorderState = Idle` at L1679) before `BlockInput` → `ShowSupervisionStatus`, so reading `RecorderState` was always false.

**Fix:** `OutageAwaitingMark` one-shot on `VoiceController`:
- `InvalidateCaptureForOutage`: `BeginGap()` then `NoteWasTranscribing` before Idle
- `DropPendingTranscriptForOutage`: `NotePendingTranscriptDropped` if admitted pending or deferred start discarded
- `ShowSupervisionStatus`: `ConsumeWasAwaitingTranscriptAtOutage()` as `awaitingTranscript`
- Gap order unchanged (P9-D02)

**Tests:** 5 new supervision rows (gap order, pending drop, consume-once, idle, wiring). Checks **268** PASS.

**Suites (Zola closed, follow-up):** build 0/0; Checks 268; workspace 582; memory 162; tools 44; tts 8; phone **71**; Kotlin **98**.

---

### Follow-up 2 — false notice from admit stamp

`_pendingTranscriptAt` is a P7-D10 latency stamp, not “request pending.” Removed `hadAdmittedPending` from `NotePendingTranscriptDropped`; only `discardedDeferredStart` (non-empty `DiscardPending` log) sets the mark. Admit→submit remains the known gap. Test (e): stop-phrase stamp + idle gap → no notice.

**Suites:** Checks **269**; phone **71**; Kotlin **98**; others at floor.

---

## Phase 6 — Smoke / experience

### Deploy (EVIDENCE)

Brian started the new build (client already up at Phase 6 start). Recorded 2026-11-09 ~14:16:

| Process | Pid | Start |
|---------|-----|-------|
| `Zola.Client` | **30388** | 14:15:14 |
| watcher launcher / worker | 42540 / 25692 | 14:15:16 |
| phone launcher / worker | 24564 / 36480 | 14:15:16 |
| serve launcher / **interpreter** | 49120 / **21964** | 14:15:17 |

Supervisor lines (pid fields):
- `watcher event=job_assigned … launcher_pid=42540 child_pid=unknown`
- `phone event=job_assigned … launcher_pid=24564 child_pid=unknown`
- `serve event=start … launcher_pid=49120 child_pid=28856` (live interpreter observed as **21964**)

### SM1 (Brian)

Verbatim: “SM1 is done. No beeps heard. I could tell when she was listening.”  
(Wake / follow-up / clarify treated as done per his SM1 complete report.)

### SM2

**Attempt 1 — too late (no kill):** finalize before kill (times only):
- `…14:29:38.6187972… turn_ui_finalized turn=4 status=complete time=…14:29:38.6186063…`
- `…14:29:56.6681607… turn_ui_finalized turn=5 status=complete time=…14:29:56.6680119…`

**Attempt 2 — pass (Brian agreed “go”):**
- Transcript `…14:31:57.977…`; turn open `…14:31:57.990…`
- Kill serve interpreter **pid=21964** at **14:31:58.704** (`Stop-Process`, uv `hermes_cli` serve `--isolated`)
- Quoted lost line: `2026-11-09T14:31:58.8037980-08:00 turn_ui_finalized turn=7 status=lost time=2026-11-09T14:31:58.8035756-08:00`
- Supervisor: `stale` @ 14:32:00.460; `restart` @ 14:32:01.795 `launcher_pid=49120`; `start` @ 14:32:04.135 `launcher_pid=14288 child_pid=20708`
- New serve live: launcher **14288** / interpreter **1848** (14:32:03)

Log pass (Cursor): open at kill; `status=lost`; serve restarted.

**Brian SM2 UI (verbatim):** “SM2: The original speech was interrupted, but the kill took effect on the interrupted speech and the system notification was displayed. When she came back up, I used the wake word and continue to re-engage.”

Treated as pass: notice shown; partial interrupted / not left live; re-engage after restart (wake word); no report of auto re-submit.

### SM3 — pass

Post-SM2 supervisor lines (quoted):
- `2026-11-09T14:32:01.7953013-08:00 supervisor proc=serve event=restart restarts=1 generation=1 launcher_pid=49120 child_pid=unknown`
- `2026-11-09T14:32:04.1355093-08:00 supervisor proc=serve event=start restarts=1 generation=2 launcher_pid=14288 child_pid=20708`

`PYTHONFAULTHANDLER=1` (PEB) on serve-interp **1848**, watcher-interp **25692**, phone-interp **36480**. Launchers rpm_failed; `ApplyFaultHandler` still on start path.

### Crash watch (since 13:23:08)

Application Error / WER / python fault events: **none**. Supervisor serve restart in window: **only** the deliberate SM2 kill (14:32). Watcher/phone: stop/start only on client relaunches, no mid-session crash.

### Experience checks — pass

Brian (verbatim, 2026-11-09):
- “she no longer beeps at me.”
- “If her backend dies while I'm asking something, I'm told it didn't go through and to ask again”

Listening half of the first planned line already confirmed in SM1: “I could tell when she was listening.” Combined → both experience checks pass.

## Phase 6 review (Claude) — ChildPid leaf fix

**Problem:** `child_pid` was the launcher’s first child, not the leaf `python*.exe` interpreter (e.g. start logged 28856 vs live 21964; restart 20708 vs 1848). Watcher/phone often `unknown`.

**Fix (S51F-D06):** `ChildPidLookup` walks descendants to a leaf `python*.exe` (no `python*.exe` child), max depth 5; retries up to **3 s** on the existing fire-and-forget path; `child_pid=unknown` if none. Still WMI only.

**Checks added:** fake tree deepest leaf; parent→child python prefers deeper; timeout → unknown.

### Suites after fix (Zola closed)

| Suite | Result | Floor |
|-------|--------|-------|
| Client build Release win-x64 | OK → `%TEMP%\zola-s51f-fix-client-build` | build OK |
| Checks | **271** PASS / 0 FAIL | ≥269 |
| zola_workspace | **582** OK | 582 |
| zola_memory | **162** OK | 162 |
| zola_tools | **44** OK | 44 |
| zola_tts | **8** OK | 8 |
| zola_phone | **71** OK | 71 |
| Kotlin | **98** / assembleDebug OK | 98 |

### SM2 / SM3 re-run — launch issue (2026-11-09 ~14:58)

Brian: TEMP build showed “Zola's backend keeps failing.”

EVIDENCE: `supervisor.log` — `watcher`/`phone` `resolve_failed`; `serve` restart×3 then `keeps_failing` (no `event=start` / no pids). Client pid **12192** from `%TEMP%\zola-s51f-fix-client-build`. `ZOLA_HERMES_ROOT` unset. Hermes discovery walks cwd / BaseDirectory for sibling `hermes-agent`; from TEMP that is **NOT_FOUND**; from `C:\Users\test\Dev\zola-windows` it finds the checkout. Not caused by the ChildPid change.

Relaunch with cwd under Dev (or set `ZOLA_HERMES_ROOT`), then SM2/SM3.

**Deploy (cwd-fixed):** client **37204**; serve launch/interp **43740/3900**; watcher **17416/25212**; phone **42076/18452**.  
Supervisor start already matches interpreters: `child_pid=3900` / `25212` / `18452`.

**SM2 re-run attempt 1 — too early (no reply text):** kill ~1.1 s after open; `submit_to_first_delta_ms=` empty.  
`…15:06:11.1818606… turn_ui_finalized turn=1 status=lost …`

**SM2 re-run attempt 2 — tools only, still no reply text:** kill pid **25468** at **15:07:47.314** (~6.9 s open). Display showed `Checking a skill…`;  
`…15:07:47.3600372… turn_ui_finalized turn=2 status=lost …`  
`turn_timing turn=2 … submit_to_first_delta_ms=` (empty) `tools=2`.  
Restart: `…15:07:53.7473896… start … launcher_pid=37224 child_pid=19272` (= live interp **19272**).

**SM2 re-run attempt 3 — log pass (Brian “now” = reply text visible):**
- Admit / open: `…15:11:41.1258458… transcript admit gen=4…`; turn open ~15:11:41.13
- First delta present: `…15:13:29.9244354… turn_timing turn=4 … submit_to_first_delta_ms=3800 … submit_to_complete_ms=108770 tools=0`
- Kill serve interpreter **pid=19272** at **15:13:29.674** (Brian signal; ~108 s open; before finalize)
- Lost: `2026-11-09T15:13:29.9313047-08:00 turn_ui_finalized turn=4 status=lost time=2026-11-09T15:13:29.9309808-08:00`
- Restart: `…15:13:34.8327930… restart … launcher_pid=37224 child_pid=unknown` then  
  `2026-11-09T15:13:36.3898915-08:00 supervisor proc=serve event=start restarts=3 generation=4 launcher_pid=37568 child_pid=39740`

**Brian SM2 UI (first report, verbatim):** “There was no interruption this time. I received the system notice. I asked her to continue when she came back and she did.”

**Brian SM2 clarification (verbatim):** “I think we are good. I may not have explained well enough to Cursor. Everything happened as expected.”

**SM2 full pass** (citing clarification): partial reply kept and marked Interrupted; notice once; serve restarted; nothing re-submitted; next question worked. Log: `turn=4 status=lost` with prior `submit_to_first_delta_ms=3800`.

### SM3 re-check — pass

Logged `child_pid` equals live interpreter after restart:

| Proc | Logged line (child_pid) | Live interp | Match |
|------|-------------------------|-------------|-------|
| serve | `…15:13:36.3898915… start … launcher_pid=37568 child_pid=39740` | **39740** | PASS |
| watcher | `…15:03:36.7391186… job_assigned … launcher_pid=17416 child_pid=25212` | **25212** | PASS |
| phone | `…15:03:36.7362146… job_assigned … launcher_pid=42076 child_pid=18452` | **18452** | PASS |

## Phase 6 complete

SM1–SM3 pass; experience checks pass; ChildPid leaf fix + suites green.

## Phase 7 — Commit and merge

Brian, verbatim: “proceed to commit and merge.” (SOP v3 transition = everyday-build approval.)

Scope verified: allowed client/Checks/`VOICE_CONFIG.md`/progress only; `VOICE_CONFIG.md` SHA-256 `4c12f3f47fe8376c75bb6499655cc7fee9457d30a039c59dc84e327f6f5b63eb`; hermes-agent clean at `345cd2b057a452236de401d3534b8502a7465e8d`.

**Implementation SHA:** `37e5f494b20c885d784aec81b3ca5736a02db61f`  
Subject: `fix(S51F): Hermes beeps off, lost-request notice, faulthandler and pid logging — S51F-D03/D04/D06`.

**Merge SHA:** `74941cf72f1e00bb979a9f29ec13aa03fa6b4666`  
Subject: `Merge branch 's51f-fix'`.  
**Tag:** `fix-s51f` → merge commit. `main` / `origin/main` = merge.

### Suites on merged tip (Zola closed)

| Suite | Result |
|-------|--------|
| Client build | OK |
| Checks | **271** PASS / 0 FAIL |
| zola_workspace | **582** OK |
| zola_memory | **162** OK |
| zola_tools | **44** OK |
| zola_tts | **8** OK |
| zola_phone | **71** OK |
| Kotlin | **98** / assembleDebug OK |

### P6-D11

After merge push + clean tree: delete `config.yaml.bak-S51F-FIX-20261109-131403` only.
