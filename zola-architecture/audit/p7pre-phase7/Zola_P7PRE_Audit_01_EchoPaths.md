# P7PRE Audit 01 — S45: Every Way a Transcript Becomes Brian's Words

**Client:** `zola-windows` @ `7d77cb51c3866c50862d09f6d026191fbe25540a`  
**Hermes:** `hermes-agent` @ `345cd2b057a452236de401d3534b8502a7465e8d`  
**Labels:** `P2-D05`, `P2-D06`, `P2-D12`, `P2-D14`, `P4-D02`, `P4-D14`, `P4-D18`, `P4-D28`, `S36`, `S45`

---

## 1. Capture starts (`voice.record` start)

**RPC:** `VoiceController.RecordAsync` → `ChatSocket.InvokeAsync("voice.record")` — `VoiceController.cs` L1820–1847.

**Common gate:** `StartCaptureAsync` L1698–1802 — `VoiceGated`, empty `SessionId`, stale follow-up generation, wake pause, then `CaptureActive=true`; if `requiredGeneration != null` → `_followUpCaptureStarted=true`.

| Path | Entry | Pre-checks | Lines |
|---|---|---|---|
| Wake | `HandleWakeDetectedAsync` | `RefuseIfGated`; `Resting` (blocks TurnRunning/Speaking/CaptureActive/follow-up) | L3249–3290 |
| Mic / Ctrl+Space | `ToggleCaptureAsync` via `CanStartCapture` | Mode voice, available, session, backend, !TurnRunning, !Speaking, !gated | L1537–1548; L377–384; MainWindow L461–497 |
| Reply follow-up | `OnFollowUpTimerAsync` after `RunReplyFollowUpReleaseAsync` | Generation; gate; Mode voice; !CaptureActive; !TurnRunning | L2103–2126; L2275–2491 |
| Echo reopen | `ReopenFollowUpAfterEchoAsync` | Generation; gate; Mode; !TurnRunning | L2042–2065 |
| Clarify answer | `OpenClarifyAnswerCaptureAsync` | Token; gate; Mode voice; TTS on; clarify still valid; arms `_followUpEchoPending` | L858–910 |

No client start on: typed submit, turn start, session ready, gate open alone.

---

## 2. Capture stops

| Path | Behavior | Lines |
|---|---|---|
| Client `voice.record` stop | `StopCaptureAsync` → Hermes `stop_continuous(force_transcribe=True)` — **always attempts transcription** | Client L1804–1818; Hermes `methods_voice.py` L721–725; `voice.py` L388–427 |
| Hermes VAD silence | Auto-stop → transcript event | `voice_mode.py` silence; client `OnVoiceStatus` L1875–1894 |
| Gate close | Stops record if `CaptureActive` | `CloseGateAsync` L1185–1209 |
| Max length | `voice.max_recording_seconds` default 120 | config defaults |

**Ends without a normal text transcript (at this pin):**

| Path | Emits |
|---|---|
| `stop_continuous()` **without** `force_transcribe` (`rec.cancel`) | No transcript — used by `/voice off`, `voice.toggle` off (`voice.py` L424–426, L640–643). **Not** exposed on RPC `voice.record` stop. |
| Empty / filtered / too-short WAV | No `on_transcript` text |
| Stop phrase | `{stop_phrase, text}` — not agent-bound |
| `no_speech_limit` | `{no_speech_limit: true}` |

**Finding P7PRE-AUD-01** [MATCH] — RPC `voice.record` stop always force-transcribes (Probe 2 / known context). Cancel-without-transcript exists only via non-RPC cancel paths.

---

## 3. Cancels that leave Hermes recording — LEAD-1

**`CancelFollowUp`** (`VoiceController.cs` L2128–2157): bumps generation, clears `_followUpCaptureStarted` / armed flags, may stash clarify id — **does not** call `RecordAsync(stop)`.

| Caller reason | Also stops Hermes? |
|---|---|
| `typed-submit` (`OnTypedSubmit` L1675–1679 ← MainWindow L386) | **No** |
| `session-ready`, `stop-speaking`, `mode-text`, `voice.transcript`, echo, interrupt, turn incomplete | **No** (except gate close, which stops separately) |
| `system-gate` | Yes, if `CaptureActive` |

**LEAD-1: CONFIRMED.** Typed Send while a follow-up is already recording:

1. `CancelFollowUp("typed-submit")` clears echo eligibility flags.
2. Hermes keeps recording until VAD / silence.
3. Late `voice.transcript` arrives with `_followUpCaptureStarted` and usually `_followUpEchoPending` both false → echo check at L1940 skipped.
4. `TranscriptReady` → `MainWindow.SubmitTurnAsync` (L394–430) — mid-turn or as a new whole turn.

Incident corroboration: Audit 02 (E1/E2).

**Finding P7PRE-AUD-02** [RISK] HIGH — Cancel without Hermes stop is the primary mid-turn echo injection path under `P2-D05`/`P2-D12` as written.

---

## 4. State matrix

| State | Capture live? | Provenance | Echo check | Destination | Her voice → Brian? |
|---|---|---|---|---|---|
| Resting | Only if wake/mic started | Weak (no capture class enum) | No (unless follow-up flags) | `prompt.submit` | Low |
| Wake capture | Yes | Unbound | **No** | submit / unbound→clarify if open | Medium |
| Follow-up armed | No | N/A | Pending after idle only | — | Low |
| Follow-up recording | Yes | `_followUpCaptureStarted` | **Yes** | submit after echo | Low if guard hits; **HIGH after cancel-without-stop** |
| TurnRunning, not speaking | Orphan capture possible | Flags often cleared | Often **skipped** | mid-turn submit / redirect | **HIGH** |
| TurnRunning, speaking | Should be no new follow-up | Haystack from deltas | On follow-up only | — | Medium (skew) |
| Question speaking | Not yet | Question in haystack | Later clarify | — | Medium |
| Clarify capture open | Yes, bound id | `_activeClarifyCaptureId` | **Yes** (flags set L895–897) | `ApplyVoiceClarifyAnswer` | Medium (short answers) |
| Reply done, audio playing | No until release | Haystack at complete | N/A until open | — | Tail bleed → follow-up |
| Stop pressed | Flags cleared; **CAP may continue** | Lost | Late tx often no echo | submit | **HIGH** |
| Gated | Existing CAP stopped on close | Dropped L1913–1918 | N/A | drop | Low |

---

## 5. Echo guard — LEAD-3, LEAD-4

**Eligibility** (`OnVoiceTranscript` L1937–1941):

```
var echoEligible = _followUpCaptureStarted || _followUpEchoPending;
if (echoEligible && IsEchoOfLastReply(transcript.Text))
```

**Algorithm** (`IsEchoOfLastReply` L2614–2642): normalize (strip digits/list markers) → last **20** haystack words → longest gapped in-order run ≥ **3** words and ≥ **60%** of heard → end within slack of haystack **tail**.

**Haystack** (`RememberSpokenEcho` L2595–2612): streamed `_accumulatedReply` (`message.delta` via `OnTurnDelta` L1600–1627) at `message.complete` L1653; clarify question text at L616. **Not** Edge-spoken text after markdown cleanup.

| LEAD | Outcome |
|---|---|
| LEAD-3 | **CONFIRMED** — end-anchored; head/middle escapes |
| LEAD-4 | **CONFIRMED** — haystack = streamed text; digits stripped; markdown asymmetry vs TTS |

**Offline probe (H-2), 31 replies ≥12 echo-words:**

| Group | n | Drop rate |
|---|---:|---:|
| Head 4 words | 31 | 0.000 |
| Head 8 | 31 | 0.000 |
| Head 12 | 31 | 0.258 |
| Middle 8 | 31 | 0.000 |
| Tail 8 | 31 | **1.000** |
| Synthetic genuine | 10 | 0.000 |
| Quote of her last 6 words | 31 | **1.000** |

**Finding P7PRE-AUD-03** [RISK] HIGH — End-anchor + follow-up-only eligibility allow head/orphan echoes through (`P2-D14` as locked).  
**Finding P7PRE-AUD-04** [RISK] MEDIUM — Haystack ≠ spoken text lowers match quality (`P2-D14` implementation detail).

---

## 6. Hermes busy submit — LEAD-2

Effective `display.busy_input_mode` = **`interrupt`** (default; not in profile).

| Mode | Gateway | Model sees text? | `state.db` | Memory |
|---|---|---|---|---|
| **interrupt** | `redirect` if supported → `status: redirected`; else queue + interrupt | Yes on next iteration via `begin_iteration` | Persist on redirect apply | `sync_all(original_user_message)` at turn end — includes `"User correction during the turn: …"` |
| **steer** | `steer()` or queue | Yes when drained | When flushed | End-of-turn sync |
| **queue** | Enqueue only | Next turn only | On drained submit | On that turn |

**Redirect string** (`agent/turn_iteration_prep.py` L318–325):

```python
original_user_message = (
    f"{original_user_message}\n\n" f"User correction during the turn: {_redirect_text}"
)
```

**LEAD-2: CONFIRMED.**  
**Finding P7PRE-AUD-05** [MATCH] — Busy-submit + redirect assembly matches the P6-FORGET 7c-1 incident mechanism.

---

## 7. "TTS is playing" signals

| Owner | Signal | Kind |
|---|---|---|
| Hermes | `_tts_stream_state` / `done`; `is_audio_output_active()`; `_fd_tts_pending`; `_tts_playing`; speaker `tts_done_event` | State (playback) |
| Client | `TtsPlaybackMonitor` bout/segment; `Speaking` (`_speakingEstimate \|\| _replyReleaseArmed`); estimate clock | State (playback / timing) |

**Client-side policy without Hermes edits:** bout-active + Speaking + estimate can gate capture open / transcript accept. Hermes TTS state is not on the wire to the client today.

---

## 8. Interim speech

`display.interim_assistant_messages` = **true** (default).  
`prompt_turn.py` L529–538: deltas → TTS queue + `message.delta`; interim → `message.interim` (**no TTS**).  
Client `ChatSocket.DispatchEvent` L735–737: **drops** unknown events including `message.interim`.  
**Not in echo haystack.**

**Finding P7PRE-AUD-06** [MATCH] — Interim UI events dropped; spoken path is delta-only.

---

## 9. Echo in memory

Trace for a redirect-augmented user message with `zola_memory` active:

| Stage | Can store her echo as Brian? | Fail-closed? |
|---|---|---|
| `on_turn_start(message)` | Sees current user text (redirect form if already applied) | Forget-intent hooks only |
| `sync_turn(user_content)` | Pending turn / consolidator input | **P6-FORGET 7c-1:** `turn_disposition` drop on exact, **contained**, or forget-intent (`forget.py` L798–819) |
| Pending turns | Yes if disposition keep | — |
| Episodes / facts / `episode_fact_refs` | Yes if consolidated from contaminated pending | — |

Phase 3 snapshot: `pending_turns=0`, `episodes=0`, `facts=16`, `episode_fact_refs=0` — no confirmed echo rows in store at audit time (contamination may have been forgotten/tombstoned).

**Finding P7PRE-AUD-07** [RISK] MEDIUM — Echo text can enter pending/episodes/facts when disposition is `keep`; forget path fail-closed for marked forget turns only.

---

## 10. One authority

Today **several partial deciders**:

1. Hermes STT filters (`stop_phrase`, `no_speech`, `filtered` — client **ignores** `filtered` for submit).
2. `VoiceController.OnVoiceTranscript` — gate, stop, no-speech, **echo** (content + follow-up state).
3. `MainWindow.OnTranscriptReady` — clarify vs `prompt.submit` (state).
4. Hermes busy mode — queue / steer / redirect.

**Missing:** a single provenance authority that can say "this transcript belongs to a current Brian capture."

**Finding P7PRE-AUD-08** [GAP] HIGH — No single client authority for "this is Brian."

---

## 11. Provenance vs content (keep apart)

| Mechanism | Class |
|---|---|
| Gate, Resting, TurnRunning, CaptureActive, generation, clarify bind/closed ids, bout/Speaking/estimate | **Provenance / state** — can support "belongs to Brian" |
| `IsEchoOfLastReply`, haystack overlap, Hermes `filtered` | **Content** — only "resembles Zola"; false +/− both ways |

---

## LEAD summary (this doc)

| LEAD | Status | Finding |
|---|---|---|
| LEAD-1 | **Confirmed** | P7PRE-AUD-02 |
| LEAD-2 | **Confirmed** | P7PRE-AUD-05 |
| LEAD-3 | **Confirmed** | P7PRE-AUD-03 |
| LEAD-4 | **Confirmed** | P7PRE-AUD-04 |
| LEAD-5 | See Audit 03 | P7PRE-AUD-12 |
