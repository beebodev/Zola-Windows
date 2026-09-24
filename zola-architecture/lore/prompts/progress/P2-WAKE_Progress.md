# P2-WAKE Progress — Track 3: "Hey Zola" Wake Word

## Branch

- Branch: `track3-wake-word`
- Base SHA: `2522c00a734b6065c6dc2e9d74089bded6f645b2` (`docs: reconcile P2-SPEAK closeout record`)
- Plan: `PHASE2_BUILD_PLAN.md` v1.1

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Branch and Progress Document Setup | COMPLETE |
| 2 | Read, Understand, and Probe | COMPLETE |
| 3 | Profile Config, Dependencies, and VOICE_CONFIG.md | COMPLETE |
| 4 | Build: Arm, Pause/Resume, Handover, and Detection | COMPLETE |
| 5 | Smoke Test | COMPLETE |
| 6 | Closeout | COMPLETE |

## Guardrails summary

- **G-SCOPE:** Add the `wake_word` block to the live Zola profile and `VOICE_CONFIG.md`; install sherpa-onnx only if Phase 2 finds it missing and the developer approves the exact command; wire arm, disarm, pause, resume, socket handover, and Resting-only `wake.detected` in `VoiceController`. No client audio, no `/api/audio/*`, no `hermes-agent` edits, no directed-speech (`S19`). Do not change the Track 2 follow-up clock, echo guard, or loop guard.
- **G-ARCH:** Build plan is truth. Stop and flag conflicts; do not silently deviate.
- **G-PATTERN:** Read every relevant file in full before any change. No changes from partial reads or memory of prior phases.
- **G-NOCHANGE:** Edits limited to the files named in the current phase. Tracks 1 and 2 stay as merged: push-to-talk, spoken replies, barge-in, follow-up with echo guard and `EchoReopenLimit`, loop guard, bubbles, typed chat, Cancel, Sessions, unreachable.
- **G-COMMENT:** Every changed line or block carries `// P2-WAKE: [rationale] — P2-D0X` (XAML comment form in markup). Do not comment unchanged lines.
- **G-STOP:** Stop after each phase and wait for that phase's explicit proceed message.
- **G-CLOSEOUT:** Closeout begins only on the explicit message "proceed to closeout".
- **G-LORE-SCOPE:** Do not add, resolve, or update `ROADMAP.md`, `DESIGN_DECISIONS.md`, `OPEN_QUESTIONS.md`, or any project state-audit document in this track, including closeout.
- **G-NO-CROSS-SCOPE:** Android Zola and Ava voice stacks are out of scope. Do not read, cite, or build against them.
- **G-DEPS:** Never run `pip`, `uv`, `winget`, or any installer without the developer's explicit approval of the exact command. `security.allow_lazy_installs: false` is set.
- **G-CONST:** Every RPC method, action, parameter, payload field, state, reason string, and timing this track adds is a named constant.
- **G-ONE-OWNER:** `VoiceController.cs` alone decides when the wake detector is armed, paused, resumed, or stopped, and whether a `wake.detected` starts a capture. `MainWindow` only forwards and renders.

## Discrepancies

None at start. Documents of truth read before Phase 1: `PHASE2_BUILD_PLAN.md` v1.1 (Grounding summary wake bullets, `P2-D04`, `P2-D07`, `P2-D08`, `P2-D10`, `P2-D12`, Track 3), `P2-VOICE_Progress.md`, `P2-SPEAK_Progress.md` (follow-up ✅ MET via echo guard and reopen, `EchoReopenLimit = 3`, loop guard, lid-open setup (f)), `VOICE_CONFIG.md`, `Zola Master Architecture Plan.md` (§12 directed-speech is the long-term target and is deferred as `S19`; §13 always-on listening must be visible and on-device), WINH09 Audit 05 (`AUD-14`, `AUD-15`, `AUD-16`), `ROADMAP.md`, `DESIGN_DECISIONS.md` (`P2` Edge TTS/STT note), `OPEN_QUESTIONS.md`. HEAD on `main` matched `2522c00a734b6065c6dc2e9d74089bded6f645b2` and the working tree was clean.

Phase 2 (plan vs prompt vs source, not a G-ARCH stop): the build plan Arming line says `reason: owned` → "release and retry once." `wake.stop` only releases the **caller's** lease; `wake.start` already releases a dead owner and then refuses a live foreign owner. The prompt's `WakeOwnedRetryCount = 3` / `WakeOwnedRetryDelayMs = 1000` retry of `wake.start` (no `wake.stop` from the new socket) matches source. Phase 4 follows the prompt.

Phase 4 (undeclared sherpa runtime dep): `sherpa_onnx.text2token` imports `pypinyin` even for BPE. Hermes `wake.sherpa` does not list it. First `wake.start` failed after the model landed. Blocked on an approved install; do not lazy-install.

### Mid-smoke changes

G-SCOPE / G-NOCHANGE forbade changing the Track 2 echo guard. The first mid-smoke echo used bag-of-words at `EchoContainmentRatio = 0.60` across a rolling tail. **Where 0.60 came from:** Track 2 specified **0.80**. P2-SPEAK smoke captured `and less you explicitly share or connect them.` (Whisper split of `unless`); 6/8 = 75% sat in the last-20 tail, so the ratio was lowered 0.80 → 0.60 and a 4-word phrase match was added. That 0.60 bag-of-words over a rolling tail drops real follow-ups (e.g. after "…the capital of France is Paris", `What's the population of France?` is 3/5 scattered overlap). Developer review: replace bag-of-words; keep the rolling haystack; remove the digit-fragment rule.

#### 1. Rolling spoken tail + contiguous-run echo (developer-replaced)

**Failure:** session `20260923_160720_86dec3`. User `What time is it?` then user bubbles `'2026.'` (16:08:38) and `'408 p.m. Pacific Daylight Time.'` (16:09:01). After `'2026.'` submitted, `OnTurnStarted` cleared `_accumulatedReply`, so the 6-word time phrase was checked only against the short ack.

**Kept:** `_echoHaystack` is the last `EchoLookbackWords` (20) normalized words across completed spoken replies. Late STT after follow-up idle is still echo-eligible (`_followUpEchoPending`).

**Final echo rule (developer-approved, 16:44):** text overlap alone cannot tell a user quoting Zola from an echo of her last words. Matching uses `NormalizeEchoWords` (punctuation/list markers stripped; every token containing a digit dropped from both transcript and haystack). A follow-up drops only when all of: ≥ `EchoMinContiguousWords` (3) matched words; matched/transcript ≥ `EchoAnchoredRatio` (0.60); the run ends within `max(EchoEndSlackWords, ceil(EchoEndSlackRatio × transcript words))` of the haystack end (`3` and `0.25`). The run is in-order and may skip at most `EchoMaxGapWords` (1) unmatched word on either side. Transcripts under 3 echo-words are never dropped. Haystack is still the last `EchoLookbackWords` (20) echo-words across completed replies.

**Clock (cumulative count only):** digits `max(SpokenDigitWeightFloor, digitCount)`; a.m./p.m. = `SpokenAbbrevWords` (2); all-caps 2–5 letter tokens = `letterCount × SpokenAcronymPerLetter`.

**Dry-run (2026-09-23 16:44):** no known-user false drops (Portland 5/9 = 0.556, slack 10). Super Bowl list now drops after digit strip (11/11, slack 0). `and less you explicitly share or connect them.` drops (6/8, slack 0). `2026.` and `408 p.m.…` kept (number tails; verify live in (b)). One pre-clock-fix echo still kept: playoff-format tail (`17` vs `seven`; 12/21 = 0.571, slack 8 > 6) — do not tune; verify live.

#### 2. Digit-fragment check (removed)

Removed. `'2026.'` is under 3 words, so the echo guard must not drop it. The leak cause is the clock undercounting time tokens so follow-up opened on her tail.

**Clock-only fix:** `CountSpokenWords` (cumulative estimate only; haystack still one token per `NormalizeSpokenWords` word). A token with digits counts as `max(SpokenDigitWeightFloor, digitCount)` (`SpokenDigitWeightFloor = 1`). `a.m.` / `p.m.` / `am` / `pm` count as `SpokenAbbrevWords` (2).

#### 3. Resting re-arm (developer-approved)

**Failure:** Hermes detected `hey zola` at 15:59:59 and 16:01:32; client `wake ignored: follow-up`. After "Nevermind." the follow-up listen started 15:54:58. One 15s silence produced empty STT (`Filtered Whisper hallucination`) and **not** `no_speech_limit` (that takes three). `_followUpArmed` stayed true. After idle was wired to `CancelFollowUp("follow-up-idle")`, 16:05:29 and 16:06:58 were still `wake ignored: follow-up` because `CancelFollowUp` left `_followUpCaptureStarted` true and Resting requires both flags off.

**Kept:** first Hermes `idle` on a follow-up capture with no transcript calls `CancelFollowUp("follow-up-idle")`. `CancelFollowUp` clears `_followUpArmed` and `_followUpCaptureStarted`. No extra cooldown.

**Residual:** user pauses until Hermes reports idle, then says `and one more thing` as a follow-up — the window is already closed; they must "Hey Zola" again if STT never arrives.

## Phase 2 findings

### Pause/resume ownership

`_wake_detect_handler` pauses the detector **before** it emits (`methods_voice.py` 411–428):

```
from tools.wake_word import get_last_match, owns_listener, pause_listening
if not pause_listening(owner=transport) or not owns_listener(transport):
    return
…
_emit("wake.detected", sid, {…})
```

`pause_listening` (`wake_word.py` 781–783) is `_owned_call(owner, WakeWordDetector.pause)`. That returns **True whenever the caller still holds the lease**, then runs `pause()`. If the detector is already paused, `_halt_thread` is a no-op and the return is still True. It does **not** return False just because the stream is already down.

`voice.record start` (`methods_voice.py` 741–746) calls `pause_listening` and records `_voice_wake_owner` only when that call returns True. Because an already-paused detector still returns True for the owner, a client `voice.record` after `wake.detected` **does** set `_voice_wake_owner`, and `_vr_on_status` idle / `_vr_transcript` call `_resume_voice_wake()`. Same-transport record after detect **will** resume Hermes-side.

The client still owns pause/resume when leaving Resting without going through `voice.record` (turn start, Speaking). `voice.record` already pauses the owner's detector atomically before `start_continuous`.

`wake.resume` (`methods_voice.py` 538–543) calls `_wake_resume_if_owner`. `resume_listening` is `_owned_call(owner, WakeWordDetector.resume)`. `start()` is idempotent if already running (`wake_word.py` 503–507). If the caller is not the owner or nothing is armed, `_owned_call` returns False and the RPC is `{resumed: false, reason: "not_owner"}`. Safe when armed, paused, or not armed.

Hermes also has a 2.0 s fire cooldown (`_FIRE_COOLDOWN_SECONDS`) and pauses before emit, so one detection does not immediately re-fire. No client cooldown timer is required if Resting ends as soon as a capture is active.

### Concurrent listeners

The wake detector stays armed until `pause` / `stop` / detect. A running turn's barge-in listener (`methods_voice.py` 139–261) does **not** pause wake by itself. If the detector is still armed during Thinking or Speaking, both can hear one "Hey Zola": barge-in submits a transcript and `wake.detected` would start a second capture. The client must pause on leaving Resting (`P2-D12`).

### Socket handover

`ws.py` 384–385: on disconnect, `server._release_wake_for_transport(transport)` runs in the websocket `finally` after `transport.close()`. `_transport_is_dead` (`session_reaper.py` 133–147) is True when `_closed is True` or the transport is the drop sentinel.

`wake.start` (`methods_voice.py` 483–488) releases a dead or non-owning existing owner, then refuses `{started: false, reason: "owned"}` if another **live** transport still holds the lease. `wake.stop` only releases the **caller's** lease (`_release_wake_for_transport(_caller_transport())`). Do not call `wake.stop` from the new socket to clear a foreign owner.

`ChatSocket.OpenAsync` (`ChatSocket.cs` 112–122) `Abort()`s the previous socket **before** any further RPC can be sent on it. There is currently no pre-close hook. `wake.stop` must run **before** `BeginNewSessionAsync` / `ResumeStoredAsync` / `OpenAsync` abort. After Abort, release is async on the serve `finally`; a new `wake.start` can still see `owned` until `_closed` is set. The planned `WakeOwnedRetryCount = 3` / `WakeOwnedRetryDelayMs = 1000` matches that race. The build plan's "release and retry once" from the new socket does **not** match source; the prompt's retry-`wake.start` design does.

### Config effects

- `capture: local`: `resolve_capture_mode` (`wake_word.py` 193–196) returns `"local"` whenever `raw == "local"`, even if `prefer_client` is set for `surface: "gui"`. Confirmed.
- `profile_routing: false`: `_SherpaKwsEngine._build` (`wake_word_engines.py` 185–189) enrolls only this profile's phrase unless `cfg.get("profile_routing", True)` is true. `false` limits detection to `wake_word.phrase`. Confirmed.
- `start_new_session`: only copied into the `wake.detected` payload (`methods_voice.py` 426–428, 490–491). The client will ignore it (`P2-D04`).

### Flags

No codebase conflict that blocks the Track 3 design. The build plan line "Hermes resumes the detector itself after the capture's terminal event" is true for same-transport `voice.record`. The client still must pause/resume around Resting so the detector is not armed beside barge-in.

## Dependencies and model download

Interpreter: `C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe`. `HERMES_HOME` = `%LOCALAPPDATA%\hermes\profiles\zola`.

| Probe | Result |
|---|---|
| `import sherpa_onnx` | `ModuleNotFoundError: No module named 'sherpa_onnx'` |
| `lazy_deps.is_available("wake.sherpa")` | `False` |
| `_allow_lazy_installs()` | `False` (profile `security.allow_lazy_installs: false`) |
| Hermes install command (`venv_pip=True`) | `C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe -m pip install 'sherpa-onnx==1.13.4' 'sentencepiece==0.2.2' 'sounddevice==0.5.5' 'numpy==2.4.3'` |
| sherpa keyword model | not present |

Model download is **not** gated by `allow_lazy_installs`. `_ensure_sherpa_model` (`wake_word_engines.py` 147–164) uses `urllib.request.urlretrieve` on first engine build. URL: `https://github.com/k2-fsa/sherpa-onnx/releases/download/kws-models/sherpa-onnx-kws-zipformer-gigaspeech-3.3M-2024-01-01.tar.bz2`. Destination: `%LOCALAPPDATA%\hermes\profiles\zola\cache\wakewords\sherpa-onnx-kws-zipformer-gigaspeech-3.3M-2024-01-01` (`tokens.txt` missing). It will run on first successful arm after the package is installed.

Phase 2 was **BLOCKED** on the missing `sherpa-onnx` package. The model download is not a separate blocker. The developer approved the exact install command and Phase 3 ran it.

## Phase 3 results

Approved command (exact):

```
C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe -m pip install 'sherpa-onnx==1.13.4' 'sentencepiece==0.2.2' 'sounddevice==0.5.5' 'numpy==2.4.3'
```

| Probe | Before (Phase 2) | After (Phase 3) |
|---|---|---|
| `import sherpa_onnx` | `ModuleNotFoundError` | `1.13.4` |
| `sentencepiece` | not installed | `0.2.2` |
| `lazy_deps.is_available("wake.sherpa")` | False | True |
| `_allow_lazy_installs()` | False | False |
| `pip check` | not run | `No broken requirements found.` |
| New packages | — | `sherpa-onnx==1.13.4`, `sherpa-onnx-core==1.13.4`, `sentencepiece==0.2.2` |
| Already present | — | `sounddevice==0.5.5`, `numpy==2.4.3` |

Live `wake_word` block matches `VOICE_CONFIG.md` verbatim. Added to both with comment `# P2-WAKE: sherpa "hey zola", local capture, this profile only — P2-D04`.

Fresh launch from a shell with User+Machine PATH reloaded. Client PID `20804` started `2026-09-23T15:33:44-07:00`. Serve PID `21352` started `2026-09-23T15:33:45-07:00` on `127.0.0.1:55814`. Default client mode is Voice.

`wake.status` `{surface: "gui"}` (second socket on the same serve; Phase 4 will call it on the client's socket):

| Field | Value |
|---|---|
| `available` | `true` |
| `capture` | `"local"` |
| `provider` | `"sherpa"` |
| `phrase` | `"hey zola"` |
| `hint` | `""` |
| `enabled` | `true` |
| `listening` | `false` (not armed; Phase 4) |
| `owned_by_caller` | `false` (not armed) |
| `local_input_available` | `true` |
| input device | `Microphone Array (Realtek(R) Au` / MME |

Keyword model:

| Item | Value |
|---|---|
| URL | `https://github.com/k2-fsa/sherpa-onnx/releases/download/kws-models/sherpa-onnx-kws-zipformer-gigaspeech-3.3M-2024-01-01.tar.bz2` |
| Destination | `%LOCALAPPDATA%\hermes\profiles\zola\cache\wakewords\sherpa-onnx-kws-zipformer-gigaspeech-3.3M-2024-01-01` |
| Result | not present; download not blocked by `allow_lazy_installs`; first `wake.start` in Phase 4 will `urlretrieve` it |

`dotnet build` Debug: 0 warnings, 0 errors. `hermes-agent` git clean.

## Phase 4 results

Wiring is in. Local check is **BLOCKED** on `pypinyin`.

`InvokeAsync` default timeout is `RpcTimeoutMs = 45_000` and a timeout **Faults the socket**. First-arm download can exceed that, so `wake.start` uses `WakeStartTimeoutSeconds = 60` with `faultOnTimeout: false`. A timeout returns `error=timeout` and goes through `wake.status` reconcile, not the owned retry path. Status line while pending: `Setting up wake word…`.

Pause choice: **keep** an explicit `wake.pause` before `voice.record` for mic, hotkey, and follow-up. `voice.record` also pauses atomically (Phase 2), but confirmed-state-only needs `paused: true` so `WakePaused` is set and Resting-entry resume is the only re-arm path. `wake.detected` already paused Hermes, so that path skips the extra pause RPC.

Handover hook: `ChatSocket.BeforeReplaceAsync` runs **before** `Abort()` while the old socket can still send. `VoiceController` assigns `DisarmWakeAsync`. MainWindow only forwards. Dead socket skips the hook.

No client cooldown timer (Phase 2: pause-before-emit + Resting ends on capture).

First arm (client PID `21644` at 15:40:07, serve `20812` / `4496` at 15:40:08):

| Item | Value |
|---|---|
| `wake.start` duration | **3.45 s** |
| `started` | failed |
| error | `No module named 'pypinyin'` |
| `wake.status` after | `available=true`, `listening=false`, `owned=false` |
| Model URL | `https://github.com/k2-fsa/sherpa-onnx/releases/download/kws-models/sherpa-onnx-kws-zipformer-gigaspeech-3.3M-2024-01-01.tar.bz2` |
| Model destination | `%LOCALAPPDATA%\hermes\profiles\zola\cache\wakewords\sherpa-onnx-kws-zipformer-gigaspeech-3.3M-2024-01-01` |
| Model result | **landed** (`tokens.txt` 5006 bytes). Download finished; engine build then failed in `sherpa_onnx.text2token`. |

`sherpa_onnx.utils.text2token` imports `pypinyin` unconditionally, including for `tokens_type="bpe"`. Hermes `wake.sherpa` lazy_deps lists sherpa-onnx, sentencepiece, sounddevice, numpy — not pypinyin. `allow_lazy_installs: false` so Hermes will not fetch it.

Approved and installed:

```
C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe -m pip install 'pypinyin==0.55.0'
```

`pip check`: `No broken requirements found.` Recorded in `VOICE_CONFIG.md` as required by `sherpa_onnx.text2token` but missing from Hermes's `wake.sherpa` list.

Re-arm after a full client/serve stop and a fresh User+Machine PATH:

| Item | Value |
|---|---|
| Client | PID `21220` started `2026-09-23T15:43:14-07:00` |
| Serve | PID `17416` / `23640` started `2026-09-23T15:43:15-07:00` |
| `wake.start` duration | **1.924 s** (`started=True`) |
| Model | already on disk; `tokens.txt` confirmed after arm |

`faultOnTimeout: false` is used only by `wake.start`. The two-arg `InvokeAsync` goes to `CallAsync(..., faultOnTimeout: true)`. The four-arg overload is called from one site: `ArmWakeAsync` → `wake.start`.

Local check:

1. Launch — done.
2. Mic indicator — `Mic: listening for "Hey Zola"` (UI Automation). After the P2-D08 fix, status is `Session ready.` once `wake.start` resolves.
3–6. Covered by smoke steps 1–2.

`dotnet build` Debug: 0 warnings. `hermes-agent` git clean. `wake.*` RPCs only in `VoiceController.cs`.

## Smoke results

Phase 5 is **HUMAN-RUN**. Client relaunched lid-open after the setup-notice fix.

- Client PID `18768` started `2026-09-23T15:50:18-07:00`
- Serve PID `18168` / `15404` started `2026-09-23T15:50:19-07:00`
- Chrome: `Session ready.` and `Mic: listening for "Hey Zola"`
- `wake.start` 1.496 s, `started=True`

Smoke observation (2026-09-23 16:01): wake word works intermittently.

Hermes detected `hey zola` at 15:59:59 and 16:01:32. The client logged `wake ignored: follow-up`. After the "Nevermind." turn, follow-up listen started at 15:54:58. Hermes's 15s silence (15:55:15) produced empty STT (`Filtered Whisper hallucination`) and did **not** emit `no_speech_limit` (that takes three silent captures). `_followUpArmed` stayed true, so Resting stayed false and later detections were ignored until Text mode at 16:01:53. Mode toggle then re-armed and the next detect at 16:01:58 was accepted.

Fix: silent follow-up idle now `CancelFollowUp("follow-up-idle")`. A failed follow-up `voice.record` also ends the window. Clock/echo/reopen unchanged.

Retry after that fix (16:05:20 `follow-up-idle`, 16:05:29 still `wake ignored: follow-up`): `CancelFollowUp` cleared `_followUpArmed` but left `_followUpCaptureStarted` true, so Resting stayed false. `CancelFollowUp` now clears `_followUpCaptureStarted` too. Rebuilt 0 warnings and relaunched (PID `19016`). Wake then stayed consistent.

Smoke observation (2026-09-23 16:08–16:09): Zola speech landed in user bubbles. Session `20260923_160720_86dec3`: user "What time is it?" then user `'2026.'` (16:08:38) and `'408 p.m. Pacific Daylight Time.'` (16:09:01). Echo missed them because (1) `EchoMinWords = 3` skips the 1-word year and (2) `IsEchoOfLastReply` used only `_accumulatedReply` of the latest turn, so the 6-word time phrase was checked against the short reply to `"2026."` after `OnTurnStarted` wiped the original spoken time.

Fix (clock/echo ratios/loop unchanged): rolling `_echoHaystack` of the last `EchoLookbackWords` across completed spoken replies; late follow-up-idle transcripts still echo-check via `_followUpEchoPending`; a short digit fragment already in that tail (`2026`) is treated as TTS. Rebuilt 0 warnings and relaunched (PID `4124`, session `20260923_161441_c26dac`). Chrome: `Session ready.` and `Mic: listening for "Hey Zola"`.

An earlier "smoke test passed" (16:20) was not a full checklist pass. The full HUMAN-RUN pass is below (2026-09-24). Closeout is **not** started.

### Phase 5 checklist (developer-reported pass, 2026-09-24)

Final live client after the position-anchored echo rebuild: PID `11080`, session `20260923_164549_5d1077`, chrome `Session ready.` and `Mic: listening for "Hey Zola"`. Sensitivity **0.6**, no tune. Mid-smoke Resting re-arm and the final echo/clock rule were already in.

1. **Minimized wake** — **pass**. Client minimized; "Hey Zola" then a question; she answered; one follow-up without the wake word; timeout returned to *listening for "Hey Zola"*.

2. **Re-arm 5 times** — **pass**. 5 of 5 detections, no click between them.

3. **Straight-through phrase** — **pass**. "Hey Zola, what time is it?" without a pause; the question survived.

4. **Wake while she speaks** — **pass**. "Hey Zola, stop talking about that" produced one user bubble and one turn.

5. **Session switch** — **pass**. New session + "Hey Zola" + question; Resume + "Hey Zola" + question. Mic never reported `wake_owned`.

6. **Text mode** — **pass**. "Hey Zola" in Text did nothing; mic *Mic: off*. Voice again, wake worked.

7. **Wrong phrase** — **pass**. "Hey Hermes" did not wake Zola.

8. **False wakes (10 min)** — **pass**. **0** false wakes in 10 minutes of video audio, seated **directly in front of the laptop**. Sensitivity **0.6**, no tradeoff table, no tune.

9. **Restart** — **pass**. Close and relaunch; wake armed with no clicks.

10. **Sleep/resume** — **pass**. Windows sleep ≥ 1 minute, then "Hey Zola" plus a question without touching the client; socket, mic, and detector recovered.

**(a) France follow-up** — **pass**. After a France answer, `What's the population of France?` submitted (not ignored).

**(b) Time tail** — **pass**. After "What time is it?" her spoken time tail did not become a user bubble.

**(c) Super Bowl list tail** — **pass**. "List the last five Super Bowl winners with the year," silent follow-up; no list fragment became a user bubble.

**No Zola speech as a user bubble** — **pass** on this run. The 16:08 leak (`2026.` / `408 p.m. Pacific Daylight Time.`) did not repeat. The offline "17 vs seven" playoff-format echo did **not** reproduce live.

`wake_word.sensitivity` stays **0.6**.

## Closeout

- `dotnet build windows-client/Zola.Client/Zola.Client.csproj` succeeded with 0 warnings and 0 errors.
- Existing tests: N/A. This project has no automated test suite.
- `hermes-agent` `git status` is clean at `345cd2b057a452236de401d3534b8502a7465e8d` (pinned `v2026.9.14`).
- No lore files were updated (`ROADMAP.md`, `DESIGN_DECISIONS.md`, `OPEN_QUESTIONS.md`).
- Final sensitivity: `0.6`.
- Feature commit SHA: `06038ca28a3d8a58484e12490f5a0afe7d0c834f`
- Branch tip merged: `06038ca28a3d8a58484e12490f5a0afe7d0c834f`
- Merge commit SHA on `main`: `0c375efee1ea58d937a1e468ab614bfcf109e0f6`

### Exit criteria (PHASE2_BUILD_PLAN.md v1.1 Track 3)

| Criterion | Result |
|---|---|
| Live `config.yaml` `wake_word` block matches `VOICE_CONFIG.md` verbatim | ✅ MET |
| `wake.status` reports `available: true`, `capture: "local"`, `listening: true`, `owned_by_caller: true` in Voice | ✅ MET |
| "Hey Zola, what time is it?" idle → current session | ✅ MET |
| Detection with client minimized / unfocused | ✅ MET |
| Re-arm after voice turn and follow-up timeout, no click | ✅ MET |
| After New session and Resume, wake works; mic never `busy / wake_owned` | ✅ MET |
| Wake while speaking → one user bubble, one turn (`P2-D12`) | ✅ MET |
| Mic: listening for "Hey Zola" in Resting; *Mic: off* in Text | ✅ MET |
| Text mode: "Hey Zola" does nothing; `listening: false` | ✅ MET |
| "Hey Hermes" does not wake Zola | ✅ MET |
| `hermes-agent` `git status` clean | ✅ MET |
| `dotnet build` 0 warnings | ✅ MET |
| Smoke HUMAN-RUN 1–10 + (a)(b)(c); 0 false wakes at 0.6 in front of laptop | ✅ MET |

## Files

### Created this track

- `zola-architecture/lore/prompts/progress/P2-WAKE_Progress.md`

### Modified this track

- `windows-client/Zola.Client/VoiceController.cs`
- `windows-client/Zola.Client/ChatSocket.cs`
- `windows-client/Zola.Client/MainWindow.xaml.cs`
- `zola-architecture/identity/VOICE_CONFIG.md`

### Outside-repo

- Live profile `%LOCALAPPDATA%\hermes\profiles\zola\config.yaml` `wake_word` block (matches `VOICE_CONFIG.md` verbatim)
- Approved venv installs: `sherpa-onnx==1.13.4`, `sentencepiece==0.2.2`, `pypinyin==0.55.0` (`sounddevice` / `numpy` already present)
