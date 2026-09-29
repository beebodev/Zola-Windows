# P4PRE Audit 02 — Lock Surface Map (S32)

**Audit ID:** P4PRE  
**Scope:** S32 — Voice active while Windows is locked  
**Sources:** Windows client on `audit/p4pre-conversation` @ `504ae76…`; Hermes `v2026.9.14` @ `345cd2b…`  
**Architecture labels against:** Privacy Plan §8; Identity §1 Privacy-protective / Restrained; Conversational Attention §10 (`CLOSED` / `PRIVACY_SENSITIVE`); `P2-D01`, `P2-D12`, `P3-D03`

---

## Finding summary (this document)

| ID | Label | Severity | Scope | Summary |
|----|-------|----------|-------|---------|
| P4PRE-AUD-01 | [RISK] | HIGH | [S32] | Lock events pause 3D presence only; voice/wake/TTS continue |
| P4PRE-AUD-02 | [MATCH] | — | [S32] | `SessionLockWatcher` correctly raises Locked/Unlocked from WTS lock codes |
| P4PRE-AUD-03 | [GAP] | HIGH | [S32] | No queryable lock fact shared with `VoiceController` / `ZolaDisplayState` |
| P4PRE-AUD-04 | [MATCH] | — | [X] | Wake→record→transcript path is client-driven through `VoiceController` (P2-D01/D12) |
| P4PRE-AUD-05 | [RISK] | MEDIUM | [S32] | Hermes TTS/barge-in can continue after a turn starts without a client lock gate |
| P4PRE-AUD-06 | [MATCH] | — | [S32] | `wake.pause` releases the mic device (InputStream close) |
| P4PRE-AUD-07 | [GAP] | MEDIUM | [S32] | No lock-specific HUD mic line / PresenceMode (honesty rule P2-D08 / P3-D03) |
| P4PRE-AUD-08 | [RISK] | MEDIUM | [S32] | Client cannot distinguish Win+L from UAC/secure desktop, screensaver, remote disconnect |
| P4PRE-AUD-09 | [MATCH] | — | [S32] | WS teardown releases wake lease — orphan serve does not keep listening for Hey Zola |
| P4PRE-AUD-10 | [GAP] | LOW | [S32] | Suspend/WTS remote codes not treated as voice privacy states (report only) |

---

## 1. SessionLockWatcher subscriptions

**Emitter:** `Presence/SessionLockWatcher.cs` L8–11 (events), L81–104 (dispatch).

| Windows message | Code | Event |
|-----------------|------|-------|
| `WM_WTSSESSION_CHANGE` `0x02B1` | `0x7` `WTS_SESSION_LOCK` | `Locked` |
| same | `0x8` `WTS_SESSION_UNLOCK` | `Unlocked` |
| `WM_POWERBROADCAST` `0x0218` | `0x4` `PBT_APMSUSPEND` | `Suspending` |
| same | `0x12` `PBT_APMRESUMEAUTOMATIC` | `Resumed` |

**Only subscriber:** `PresenceView` ctor (`PresenceView.cs` L211–215):

```211:215:windows-client/Zola.Client/Presence/PresenceView.cs
        _lockWatcher = new SessionLockWatcher(windowHandle);
        _lockWatcher.Locked += () => PauseRendering(PauseLocked);
        _lockWatcher.Unlocked += () => OnUnlockOrPowerResume(PauseLocked);
        _lockWatcher.Suspending += () => PauseRendering(PauseSuspended);
        _lockWatcher.Resumed += () => OnUnlockOrPowerResume(PauseSuspended);
```

| Event | Component reaction |
|-------|--------------------|
| `Locked` | `PauseRendering("locked")` → stop Helix render; `_animator.OnPaused()` when first pause reason |
| `Unlocked` | `OnUnlockOrPowerResume("locked")` → resume render + scene revalidate |
| `Suspending` / `Resumed` | Same pattern with reason `"suspended"` |

**Not subscribed:** `VoiceController`, `MainWindow`, `ChatSocket`, `ZolaDisplayState`, `HermesProcessManager`.

**Queryable fact?**  
- `SessionLockWatcher`: **events only** — no `IsLocked` field.  
- `PresenceView` holds `_pauseReasons` including `"locked"` for **render gate only** — not exposed to voice.

**P4PRE-AUD-02 [MATCH] [S32]** — Lock/unlock detection from WTS matches the intended OS signal.  
**P4PRE-AUD-01 [RISK] HIGH [S32]** — Those events do not gate voice; conflicts with Privacy Plan §8 (always-on listening / household) and Identity **Privacy-protective** / Attention `PRIVACY_SENSITIVE` / `CLOSED` expectations for a locked PC. Evidence: subscription list above; S32 lore observation in `OPEN_QUESTIONS.md` L126–132.

**P4PRE-AUD-03 [GAP] HIGH [S32]** — No lock fact for `VoiceController` / `ZolaDisplayState` (`P3-D03` single display authority cannot express "paused because locked").

---

## 2. Chain: "Hey Zola" → spoken reply

| Hop | File / method | Lines (approx) | Through `VoiceController`? |
|-----|---------------|----------------|----------------------------|
| Wake detect | Hermes `tools/wake_word.py` / `_wake_detect_handler` in `methods_voice.py` | pause then emit `wake.detected` | No (Hermes) |
| Event route | `ChatSocket.DispatchEvent` → `WakeDetected` | ~589 | Socket only |
| Handle | `VoiceController.OnWakeDetected` → `HandleWakeDetectedAsync` → `StartCaptureAsync` | ~1445+ | **Yes** |
| Capture | `VoiceController.RecordAsync` → `voice.record` | ~start capture | **Yes** |
| STT | Hermes `_vr_transcript` → `voice.transcript` event | | No |
| Gate | `VoiceController.OnVoiceTranscript` → `TranscriptReady` | | **Yes** |
| Submit | `MainWindow` wires `TranscriptReady` → `SubmitTurnAsync` → `ChatSocket.SubmitAsync` (`prompt.submit`) | MainWindow ~124 | Window submits text; controller supplied it |
| Reply stream | `message.*` → MainWindow → `_voice.OnTurnStarted/Delta/Completed` | | Clock / Speaking only |
| TTS | Hermes `prompt_turn` / `_tts_stream_begin` after turn starts | | **No client TTS RPC** |

**Does every hop pass `VoiceController`?** No. Wake emit, STT, and TTS live in Hermes. Client owns arm / capture / transcript gate / submit / speaking clock (`P2-D01`, `P2-D12`).

Quote proving client-driven capture after wake (Hermes comment pattern): on detect, emit `wake.detected` and the client opens its own capture (`methods_voice.py` ~309–312 region per research; verified pattern: no auto `prompt.submit` on wake).

**Hermes paths without client RPC:**
- **Speak:** turn TTS starts inside Hermes once a turn is already running; also `voice.tts` RPC.
- **Barge-in:** can cut speech and emit `voice.interrupted` / `voice.transcript` without client RPC; **next turn** still needs client `prompt.submit` on the GUI path.
- **Record start:** only via `voice.record` RPC.
- **Turn start:** GUI wake path does not auto-submit.

**P4PRE-AUD-04 [MATCH] [X]** — Client is sole driver of wake arm / capture / transcript→submit (`P2-D01`/`P2-D12`).  
**P4PRE-AUD-05 [RISK] MEDIUM [S32]** — Once `prompt.submit` has started a turn, Hermes TTS and barge-in continue independently of OS lock; a client-only gate must also stop in-flight turns or accept residual spoken audio at the lock screen.

---

## 3. Wake RPCs

| RPC | Params (client usage) | Result fields used |
|-----|----------------------|--------------------|
| `wake.start` | `surface=gui`, `session_id` | `started`, `reason`, `hint`, `error` |
| `wake.stop` | `{}` | `stopped` |
| `wake.pause` | `{}` | `paused` |
| `wake.resume` | `{}` | `resumed` |
| `wake.status` | `surface=gui` | `listening`, `owned_by_caller`, `available`, `audio_silent`, `hint` |

Implementations: `tui_gateway/methods_voice.py` (~449–582). Client constants: `VoiceController.cs` L77–81.

### What `wake.pause` does

Hermes docstring: *"Release the mic (e.g. while the desktop's browser captures audio)."*  
`pause_listening(owner=…)` → `WakeWordDetector.pause` → halt reader thread → `cap.close()` → `InputStream.stop/close`. **Mic device released.** Engine/ownership lease retained; `wake.resume` re-opens the stream.

### In-flight `wake.detected`

Hermes pauses before emit. Client on event sets `WakePaused` then requires `Resting` or ignores (`HandleWakeDetectedAsync`).

### Survive `/api/ws` reconnect?

**No.** WS close → `_release_wake_for_transport` → `stop_listening`. Client `BeforeReplaceAsync = DisarmWakeAsync`. `OnSessionReady` bumps connection generation (clears `WakeArmed`/`WakePaused`) then `SyncVoiceAndWakeAsync` re-arms.

**P4PRE-AUD-06 [MATCH] [S32]** — `wake.pause` releases the device; suitable primitive for option A if the client also blocks `ReconcileWakeRestingAsync` from auto-resuming during lock.

---

## 4. Stopping record / barge-in / TTS

| Concern | Exact RPC / path | Side effects |
|---------|------------------|--------------|
| Stop capture | `voice.record` `{action: stop, session_id}` | Ends capture; client `StopCaptureAsync` |
| Barge-in | Hermes-internal; emits `voice.interrupted` (+ later transcript) | `mark_speech_interrupted` → latches `SPEECH_INTERRUPTED_NOTE` (S21); `_tts_stream_stop` |
| Cancel turn + cut TTS | `session.interrupt` `{session_id}` | Hermes `_tts_stream_stop()` first; `_clear_pending` cancels open server requests |
| Voice → Text | `voice.toggle` `{action: off}` | Disarms wake; `user_barge=False` on stop path (no SPEECH latch) |
| Dedicated stop-TTS RPC | none on client | Server `_tts_stream_stop` only |

`SPEECH_INTERRUPTED_NOTE` (`tools/tts_streaming.py` ~46–60): latched by barge-in and by `_tts_stream_stop(user_barge=True)` default; taken on next `_prepare_turn_input` (TTL 120 s). Typed Send / Cancel also trip the default latch (S21 lore).

---

## 5. Ownership state and lock-gate insertion points

**`VoiceController` holds today:** `Mode`, `WakeArmed`, `WakePaused`, `CaptureActive`, `Speaking`, `Resting`, `CanStartCapture`, `_connectionGeneration`, `_followUpGeneration`. Sole wake RPC owner and sole `WakeDetected` subscriber (`P2-D12`).

**Insertion points (no code):**

| Gate | Where | Purpose |
|------|-------|---------|
| Hold lock fact | New fact fed like `UpdateWindowFacts`, or MainWindow/Presence feed into VoiceController | Queryable for unlock policy |
| Refuse new wake capture | `HandleWakeDetectedAsync` | Block Hey Zola while locked |
| Refuse mic / follow-up | `CanStartCapture` / `StartCaptureAsync` / `OnFollowUpTimerAsync` | No `voice.record` |
| Refuse submit | `MainWindow.SubmitTurnAsync` | No new turns (typed or transcript) |
| Keep wake paused | `ResumeWakeAsync` / `ReconcileWakeRestingAsync` | Prevent Resting auto-`wake.resume` fighting the gate |
| Hard stop in-flight | From Locked: `voice.record stop`, `session.interrupt`, `wake.pause`/`stop` | Cut TTS/capture |
| Display | `ZolaDisplayStateModel.Recompute` only | Avoid second HUD authority (`P3-D03`) |

**Second-authority risks:** Hermes TTS after turn start; barge-in mic during Speaking; `ReconcileWakeRestingAsync` resume vs lock-pause; bot-relay `prompt.submit` on same serve; attach-vs-spawn orphan serve.

---

## 6. Text mode

`EnterTextModeAsync` → `voice.toggle off` + `DisarmWakeAsync` (`wake.stop`). Wake listener **is stopped** in Text mode.

While locked **today** (no gate): UI still interactive if session ready; in-flight `prompt.submit` continues; TTS continues if Voice+tts was on. Lock does **not** force Text mode. A typed prompt cannot be typed at the lock screen, but an **already in-flight** turn can still complete and be spoken.

---

## 7. In-flight at the moment of lock

| In-flight | Stopped by lock today? |
|-----------|------------------------|
| Streaming turn | **No** |
| Speaking / TTS | **No** |
| Follow-up `voice.record` / timer | **No** |
| Echo reopen (`EchoReopenLimit`) | **No** |
| Wake detector | **No** |
| Presence 3D | **Yes** |

---

## 8. Unlock

Unlock today: **render-only** resume. Voice/`Mode`/`WakeArmed` unchanged. If pre-lock was Voice + Resting + armed, that remains (wake was never paused for lock).

| Unlock option | Would require |
|---------------|---------------|
| Auto-resume listening | Held lock fact; on unlock re-evaluate Resting + Mode + session ready; call `wake.resume`/`start` if pre-lock armed |
| Stay paused until click / Ctrl+Space / Hey Zola | On lock: `wake.pause` or `stop` + set a "user must re-arm" flag that `ReconcileWakeRestingAsync` respects until explicit user action |

---

## 9. Suspend / fast-user-switch

`SessionLockWatcher` handles **only** lock/unlock + APM suspend/resume (see §1). **Not handled:** `WTS_CONSOLE_DISCONNECT` (`0x2`), `WTS_REMOTE_CONNECT`/`DISCONNECT` (`0x3`/`0x4`), logon/logoff. Those messages may arrive but fall through to `DefSubclassProc`.

For presence, suspend ≈ lock (render pause). For voice, **neither** affects voice today. Whether S32 policy should equate sleep/remote disconnect with Win+L is a **developer decision** (report only).

**P4PRE-AUD-10 [GAP] LOW [S32]** — No voice policy for suspend/remote; architecture consideration only.

### 9b. Lock ≠ every privacy-sensitive Windows state

| Scenario | Raises today’s events? | Distinguishable? |
|----------|------------------------|------------------|
| Win+L / session lock | `Locked` / `Unlocked` | Yes |
| UAC / credential secure desktop | **UNVERIFIED**; typically not `WTS_SESSION_LOCK` | No dedicated signal in this client |
| Sign-in after user switch | May see unlock/logon variants; only `0x8` handled | Partial at best |
| Remote disconnect | Not subscribed | No |
| Display off / screensaver without lock | Not subscribed | No |
| Sleep/hibernate | `Suspending` / `Resumed` | Separate from lock |
| Minimize / hide | Separate pause reasons (`minimized`/`hidden`) | Not SessionLock |

**P4PRE-AUD-08 [RISK] MEDIUM [S32]** — A gate on `Locked` alone leaves residual exposure on secure desktop / screensaver / remote disconnect. Architecture note: `Locked` ≠ every privacy-sensitive Windows state. Do not expand detection in this audit.

---

## 10. Client closed / crash while serve runs

`HermesProcessManager.Shutdown`: kills process tree **only if** `OwnsProcess` (spawned). Attached serve is left running (explicit).

| Case | Serve outlives? | Wake without client? |
|------|-----------------|----------------------|
| Orderly close, spawned | Killed | N/A |
| Orderly close, attached | **Yes** | WS dispose → Hermes releases wake lease → **stopped** |
| Crash / kill client, spawned | Likely yes (no Job Object observed — **UNVERIFIED** OS reparent) | WS drop still releases wake |
| After disconnect | Serve may run | Wake **not** armed until some client `wake.start` |

**P4PRE-AUD-09 [MATCH] [S32]** — Client-side gate is sufficient for wake while the client owns the socket; orphan serve does not keep Hey Zola listening after WS teardown. Residual: in-flight TTS already playing may finish; mid-record capture behaviour on abrupt crash is **UNVERIFIED**.

---

## 11. `ZolaDisplayState` for "voice paused because locked"

No lock-specific label / `PresenceMode`. Closest mic line:

```236:238:windows-client/Zola.Client/ZolaDisplayState.cs
        else if (_voice.Resting && _voice.WakeArmed && _voice.WakePaused)
        {
            micLine = WakePausedLabel;  // "Wake listening paused"
```

That string is for **operational** wake pause (turn/speaking/follow-up), not OS lock. While locked with wake still listening: typically Idle + `listening for "Hey Zola"` if Resting+armed+unpaused — **false at the lock screen** relative to privacy intent (P2-D08 honesty).

**Window visible while locked?** Presence render paused (`IsRendering=false`); WinUI window still exists; OS lock screen covers it. No code hides the window on lock. Label still matters at unlock.

**P4PRE-AUD-07 [GAP] MEDIUM [S32]** — Need a distinct mic/voice string via `ZolaDisplayState` only (`P3-D03`), e.g. truth that wake is paused because Windows is locked.

---

## 12. Options table (no recommendation)

| Option | Touches | Single authority | Fails closed | Residual exposure | S21 | P3-D23 mouth |
|--------|---------|------------------|--------------|-------------------|-----|--------------|
| **A — Pause wake + mic on lock** | `VoiceController` + lock fact feed; `wake.pause`/`stop`; `voice.record stop`; optional `session.interrupt`; `ZolaDisplayState` strings; block `ReconcileWakeRestingAsync` during lock | `VoiceController` for voice RPCs; `ZolaDisplayState` for HUD | No new wake/record/submit while locked; cut in-flight if interrupt chosen | Secure desktop / screensaver / remote (9b); Hermes TTS if interrupt not used | Interrupt may latch `SPEECH_INTERRUPTED_NOTE` | Speaking clears when TTS stops / interrupt |
| **B — Keep listening, refuse replies** | Gate `SubmitTurnAsync` / transcript consumer; optional refuse TTS; mic stays open | Submit gate in MainWindow **or** VoiceController transcript path — must stay one submit path | No new `prompt.submit`; in-flight may still speak unless interrupted | Mic still captures at lock; STT of secrets; barge-in transcripts | Same if interrupt used | Same |
| **C — Keep deliberately** | Docs / lore only | N/A | N/A | Full S32 exposure (current) | Unchanged | Unchanged |
| **D — Safe-replies allowlist** (variant of B) | Filter before `prompt.submit` and/or Hermes `prompt_turn`; config phrases | Must not create second submit authority | Non-allowlisted refused | Allowlisted replies still audible; mic still open | Unchanged unless interrupt | Mouth still tracks spoken allowlist |

---

## Architecture labels (cross-check)

| Expectation | Verdict |
|-------------|---------|
| Privacy Plan §8 — always-on listening / household / autonomous restraint | **[RISK]** AUD-01 — listening continues at lock |
| Identity Privacy-protective / Restrained | **[RISK]** AUD-01 |
| Attention `CLOSED` / `PRIVACY_SENSITIVE` | **[GAP]** no mapped client state for lock |
| `P2-D01` Hermes owns devices; client drives | **[MATCH]** AUD-04; option A uses existing `wake.pause` |
| `P2-D12` one voice owner | Gate must live in / feed `VoiceController`, not a parallel owner |
| `P3-D03` one display authority | Lock HUD only via `ZolaDisplayState` — AUD-07 |

---
