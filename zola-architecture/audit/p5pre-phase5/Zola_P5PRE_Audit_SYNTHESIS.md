# P5PRE Audit — Synthesis

**Audit ID:** P5PRE
**Date:** 2026-10-01
**Pin:** zola-windows `6494acace5c124368bf9ce284d2d3d5ddcd22aac` on `p5pre-audit`. Hermes `345cd2b057a452236de401d3534b8502a7465e8d`.
**Scope:** S41, S42, S36, S38. Diagnostic only. No source changes.

Live probes are in `Zola_P5PRE_Audit_05_LiveProbes.md`. Static traces are Audits 01–04.

---

## 1. Finding summary

| ID | Severity | Label | File | Summary |
|---|---|---|---|---|
| P5PRE-AUD-01 | HIGH | [RISK] | `VoiceController.cs` `OnVoiceTranscript` / `OnVoiceStatus` / `OnTurnCompleted` | A spoken clarify answer sets `_followUpTranscriptSeen` and does not start a turn. The reply follow-up's silence then skips `CancelFollowUp`. `Resting` stays false. `wake.resume` is never sent. Reproduced live on L1 try 2. |
| P5PRE-AUD-02 | MEDIUM | [GAP] | `VoiceController.cs` `ReconcileWakeRestingAsync` | Several reconcile exits write nothing, and no line snapshots the `Resting` flags. The stuck pause looks like "no `wake.resume`" with no error. |
| P5PRE-AUD-03 | — | [MATCH] | `MainWindow.OnTranscriptReady` | A bound clarify transcript answers that request and does not call `prompt.submit` (P4-D14). |
| P5PRE-AUD-04 | — | [MATCH] | `VoiceController.ReconcileWakeRestingAsync` | One method owns `wake.pause` / `wake.resume`. Text→Voice recovers by `CancelFollowUp` plus `ArmWakeAsync` (P2-D12). |
| P5PRE-AUD-05 | — | [MATCH] | `tools/memory_tool.py`; live `config.yaml` | The live store is the profile's `MEMORY.md` / `USER.md`. Limits 4400 / 2750. `memory.provider` is unset (C4). |
| P5PRE-AUD-06 | — | [MATCH] | live `memories/` | Both files were under the limit before the probe. The probe `add` succeeded. No `.bak` snapshots. |
| P5PRE-AUD-07 | HIGH | [RISK] | `tools/memory_tool.py` `MEMORY_SCHEMA` | A durable write happens only when an agent calls `memory`. The tool text says to save almost nothing. Before this probe, 2 result rows across 93 sessions. |
| P5PRE-AUD-08 | LOW | [RISK] | `tools/memory_tool_store.py` `format_for_system_prompt` | The system-prompt block is frozen at `load_from_disk()`. Writes update disk and the live lists, and leave that agent's snapshot unchanged. Confirmed: session A's stored prompt lacks the probe after the write. |
| P5PRE-AUD-09 | — | [MATCH] | `tui_gateway/server.py` `_make_agent` | A new client session builds a new `AIAgent` on its first prompt and calls `load_from_disk()`. Confirmed: session B and the post-restart session both had the probe in the stored prompt. |
| P5PRE-AUD-10 | — | [MATCH] | `tools/session_search_tool.py` | `session_search` searches `messages_fts`. It is not the injection path. None of the L2 recall turns called it. |
| P5PRE-AUD-11 | — | [MATCH] | `plugins/memory/__init__.py` | A user provider loads from `$HERMES_HOME/plugins/<name>/` without editing hermes-agent. The zola profile has no plugins directory. |
| P5PRE-AUD-12 | LOW | [GAP] | live `SOUL.md`; `memories/*.md` | The `[tag]` convention is not in the live `SOUL.md`. No entry starts with a `[tag]`. |
| P5PRE-AUD-13 | — | [MATCH] | `methods_voice.py` `_arm_barge_listener_if_enabled` | Live `barge_in: false` means the full-duplex listener is not armed. |
| P5PRE-AUD-14 | HIGH | [RISK] | `methods_voice.py` `_fd_trip` | The barge trip is not clarify-aware. It always cuts TTS and emits `voice.interrupted`. Re-enabling barge-in as-is fails S36 (b). |
| P5PRE-AUD-15 | HIGH | [GAP] | `methods_voice.py` `voice.record` | The answer capture has no pre-roll. S36 (e) fails on this pin. |
| P5PRE-AUD-16 | MEDIUM | [GAP] | `plugins/` | No profile plugin or config key can make the listener clarify-aware or add pre-roll to `voice.record`. |
| P5PRE-AUD-17 | MEDIUM | [GAP] | client timeline | Client logs do not split silence, WAV, Whisper load, inference, `prompt.submit`, or `message.start`. `agent.log` did split silence and WAV for L3. Inference is still a residual. |
| P5PRE-AUD-18 | — | [MATCH] | `hermes_cli/voice.py` `_continuous_on_silence` | One path: VAD silence, WAV, Whisper, `voice.transcript`, `prompt.submit`, `message.start`, Thinking. |
| P5PRE-AUD-19 | — | [MATCH] | `transcription_tools.py`; live `stt` | Local faster-whisper, model `base`, device and compute type `auto`. Idle unload is off. |

19 findings: 4 HIGH, 3 MEDIUM, 2 LOW, 10 MATCH.

---

## 2. Build plan implications

**P5PRE-AUD-01 (S41, `VoiceController.cs`).** The fix belongs in the one wake owner (P2-D12). A clarify answer must not leave `_followUpTranscriptSeen` set across the reply's follow-up, or the silent follow-up must still be allowed to call `CancelFollowUp`. L1 try 2 ended Idle / mic off, and "Hey Zola" produced no `wake.detected`. Try 1 never opened a clarify request, so it does not weaken this.

**P5PRE-AUD-02 (S41, `VoiceController.cs`).** The stuck state is invisible in `voice-timeline.log` except as a missing `wake.resume`. A fix track needs a `Resting` snapshot and a log on the silent reconcile return before that fix can be confirmed from the client log alone. Do not add those lines in this audit.

**P5PRE-AUD-07 (S42, `tools/memory_tool.py`).** The cross-session miss was not reproduced once the model called `memory`. An explicit "please remember" wrote the fact, and both a new session and a restarted serve recalled it from the stored prompt. A build that only refreshes the snapshot does not address turns where the tool is never called. Any change to the save instructions is a prompt change, not a hermes-agent edit.

**P5PRE-AUD-08 (S42, `tools/memory_tool_store.py`).** Downgraded after L2: B1 and C1 show the freeze affects only the writing agent; it is not the cross-session cause. The freeze is real for the agent that wrote the fact. Session A's stored prompt still lacked the probe. It is not why session B or the restarted serve missed it: they did not miss it. Refreshing the snapshot on write would be a hermes-agent edit, which this track cannot make, and L2 does not show that edit as the cross-session fix.

**P5PRE-AUD-12 (S42, live `SOUL.md`).** The `[tag]` convention from P1-MEMORY is not in the live soul, and no entry uses a tag. That is separate from whether a fact crosses sessions.

**P5PRE-AUD-14 (S36, `methods_voice.py`).** Turning `barge_in` back on rearms a listener that interrupts a spoken clarify. Client-side echo filtering runs after the transcript and cannot stop `_fd_trip`. This fails acceptance (b). It also reverses P4-D28.

**P5PRE-AUD-15 (S36, `methods_voice.py`).** `voice.record` has no pre-roll. The 1200 ms buffer exists on `full_duplex_listen` and on `listen_for_speech`, and the second of those has no production caller. Acceptance (e) fails on this pin. Adding pre-roll to `voice.record` is a hermes-agent edit.

**P5PRE-AUD-16 (S36, plugins).** There is no profile-plugin route to a clarify-aware listener or to record pre-roll. Config can only set `barge_in` and the two threshold numbers.

**P5PRE-AUD-17 (S38, client logs).** L3 could still be measured because `agent.log` has silence and WAV lines and the Thinking label is in `display-state.log`. A client-only diagnosis of a future regression still cannot split those stages. S38 is measure-only; this audit does not tune `silence_duration` or the Whisper model.

---

## 3. Pre-work required

S41 needs diagnostic lines before a fix is verifiable from `voice-timeline.log` alone: a `Resting` flag snapshot at reconcile time, and a log on the early returns (`!WakeArmed`, generation mismatch, `!Resting` inside resume, and the silent "already converged" return). Audit 01 names them. They were not added.

S38's largest stage was measurable from logs that already exist (`agent.log` plus `display-state.log`). No new logging is required to keep that conclusion. A dedicated Whisper inference start/end line does not exist. The figure used here is the residual from `WAV written` to the client transcript line.

---

## 4. Architecture assumptions confirmed

P5PRE-AUD-03, 04, 05, 06, 09, 10, 11, 13, 18, 19.

In particular: one wake owner (P2-D12); bound clarify answers do not submit a new turn (P4-D14); the v1 store is the profile flat files with `memory.provider` empty (C4, P4); a new session reloads those files from disk; `session_search` is not that injection path; `barge_in` is off so the full-duplex listener is not armed; listen-to-think is the single VAD → Whisper → submit path; the live STT model is `base` on `auto`.

---

## 5. Open questions / decisions for the developer

### S41

Root cause is confirmed. On the answered clarify path the answer itself clears the armed flags (`followUpStarted=False` at `17:54:37`, `words=0`, `complete=` empty). The reply then arms follow-up again (`17:54:47`, `followUpStarted=True`) without clearing `_followUpTranscriptSeen`, because that flag is cleared in `OnTurnStarted` and a clarify answer does not start a turn. The silent follow-up skips `CancelFollowUp`. HUD went Idle / mic off. "Hey Zola" did not wake. The same shape is in the 09:58–09:59 log: `question_spoken`, a bound answer, `follow_up_release` at 09:59:16, and no `wake.resume` until a lock gate at 10:38.

LEAD Q3 is refuted as the immediate post-answer state and confirmed as this later stuck end-state.

The fix belongs in `VoiceController`, in the one reconcile owner. Not a second resume path.

### S42 lifecycle

```
user turn
  → write trigger: model chooses the memory tool          [RISK P5PRE-AUD-07]
      (no built-in automatic extraction on the empty provider)
  → memory add / replace / remove
  → MEMORY.md or USER.md on disk                          [MATCH P5PRE-AUD-05]
  → MemoryStore live list updated
  → that agent's _system_prompt_snapshot left unchanged   [RISK P5PRE-AUD-08]
  → that agent's stored system prompt stays stale         [RISK P5PRE-AUD-08]
new session (session.create, first prompt)
  → new AIAgent
  → load_from_disk()                                      [MATCH P5PRE-AUD-09]
  → new system prompt includes the disk fact              [MATCH P5PRE-AUD-09]
  → answer, with no session_search                        [MATCH P5PRE-AUD-10]
```

`session_search` is a separate FTS path over `state.db`. It is not on the arrows above. L2 recall did not use it.

L2 root cause: a fact that is actually written does cross sessions, in the same serve and after a restart. The snapshot freeze explains only later turns of the writing agent. It does not explain a new session missing a fact already on disk. The behavior that still matches the original symptom is AUD-07: most turns never call `memory` at all. Budget was not the blocker. The tool was enabled.

| Shape | C4 | S14 | P4 | C8 | Hermes edit | Would it fix the L2 result? |
|---|---|---|---|---|---|---|
| (i) built-in store: save behavior / when the model writes | Fits. Stays the flat files. | Does not build the structured store. | Fits. Provider stays empty. | Fits if forget still targets the flat file the entry lives in. The probe `remove` targeted `user`, while C8 names `MEMORY.md`. | No, if the change is the profile prompt. Yes, if the change is snapshot refresh inside `memory_tool_store.py`. | A prompt change can make writes happen more often. Snapshot refresh would not have changed B1 or C1: those already passed. |
| (ii) Zola-owned local provider in the profile plugins folder | Leaves the flat files in place beside the provider. | Not the structured projection. | Conflicts. P4 forbids an external memory provider, including a local Zola-owned one. Not decided here. | Depends on whether forget still only touches `MEMORY.md`. | No. Loading is already implemented. | L2 did not fail in a way this provider would repair. |
| (iii) S14 structured store projecting into `MEMORY.md` | Fits only if the projected files remain the live store. | This is the deferred target. Not designed here. | Fits if `memory.provider` stays empty. | Fits if forget still edits the projected `MEMORY.md`. | Must not require a hermes-agent edit. | Not required by the L2 pattern. |

No recommendation. P4 is not treated as revised.

### S36

| | (a) | (b) | (c) | (d) | (e) | Hermes edit | Conflict | Hardware |
|---|---|---|---|---|---|---|---|---|
| O1 barge-in as-is, client mitigations only | PASS | FAIL | UNKNOWN | PASS | FAIL | no | P4-D28 | no |
| O2 upstream clarify-aware listener, discardable stop, pre-roll on `voice.record`. Not on this pin. | PASS if adopted | PASS if adopted | UNKNOWN | PASS | PASS if adopted | yes | none | no |
| O3 config / plugin, only the hooks that exist | PASS only by turning barge-in on | FAIL | UNKNOWN | PASS | FAIL | no | P4-D28 if barge-in is turned on | no |
| O4 headset or OS echo cancellation | UNKNOWN | FAIL | UNKNOWN | PASS | FAIL | no | none | yes |
| O5 client-side detector | UNKNOWN | UNKNOWN | UNKNOWN | PASS if the gate still refuses | UNKNOWN | no, unless a new capture RPC is required | P2-D01. The client would open a second input device. | no |

**Feasibility gate: NO.** No option passes (a)–(e) without editing `hermes-agent`. O2 is the only row that can pass (a), (b), and (e), and it is not available at this pin. (c) stays UNKNOWN for every row until a barge-on playback in the P2-D16 setup (enhancements on, lid open).

### S38

Per-turn table from L3. Warm model. Times in ms.

| Turn | Silence (configured) | Stop | WAV | WAV → transcript | Transcript → Thinking | Silence fire → Thinking |
|---|---|---|---|---|---|---|
| 1 short | 1500 | 3 | 13 | 1680 | 3 | 1696 |
| 2 short | 1500 | 2 | 4 | 1562 | 2 | 1568 |
| 3 medium | 1500 | 3 | 11 | 1819 | 3 | 1833 |
| 4 medium | 1500 | 1 | 9 | 1801 | 2 | 1813 |
| 5 long | 1500 | 3 | 11 | 1847 | 2 | 1860 |

The largest single contributor after he stops talking is the WAV → transcript residual: Whisper inference plus delivery to the client. It is 1562–1847 ms, larger than the 1500 ms silence wait on four of the five turns, and about equal on the second short turn. Stop, WAV write, and submit-to-Thinking are each under 15 ms. No tuning recommendation.
