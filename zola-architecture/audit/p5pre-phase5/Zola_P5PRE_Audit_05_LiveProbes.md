# P5PRE Audit 05 — Live probes

Phase 6. One step at a time. Probe text only.

## Prep

Dictation tool confirmed off. Build of `windows-client/Zola.Client/Zola.Client.csproj -r win-x64` succeeded (0 warnings, 0 errors). Hashes and log offsets are in the progress doc. Client pid 15960 launched 2026-10-01T17:17:44-07:00. HUD reached Idle, mic listening for "Hey Zola", link connected.

## L1 — S41 clarify then mic

**Brian, step 1 (his words):** Her response: "Quick, or sit-down?" His response: "Something quick." Her response: "[restaurant recommendation — redacted]."

**Log, after that reply's follow-up window** (`display-state.log`, last line of this probe):

`2026-10-01T17:21:29.1445054-07:00` voice="Idle" mic="Mic: listening for "Hey Zola"" mode=Idle link connected.

The line immediately before it is `17:21:29.119` voice="Idle" mic="Wake listening paused". Wake resume is logged.

**Brian, step 2 (his words):** "The HUD shows Idle." The screenshot at 17:28 also shows `MIC: LISTENING FOR "HEY ZOLA"`. That matches the log.

**Brian, step 3 (his words):** "She woke." `voice-timeline.log` `2026-10-01T17:31:28.6757832-07:00 wake.detected phrase=hey zola`, then `17:31:38.9368952 wake.resume reason=capture-idle`.

### Try 1 result: not the clarify path

`server-requests.log` stayed at byte 23018. Every transcript in this probe is `bound=none`. She asked in an ordinary reply. His answer started a new turn (`OnTurnStarted`), and the later silent follow-up did call `CancelFollowUp`.

Mapped ending: reply follow-up, silent. `17:21:29.117` `fireOrCancel=follow-up-idle`. `17:21:29.143` `wake.resume reason=follow-up-end`. `17:21:29.144` `wake reconcile pass=2 reason=capture-idle`. Final `Resting` expected true. HUD Idle, mic listening. LEAD Q3 is not tested by this try, because no clarify request was open.

### Original 2026-10-01 window (still in `voice-timeline.log`)

The ~09:55–10:05 window is present. The clarify path is:

- `09:58:41.510` `question_spoken id=srq-6da0b01ac047 chars=22`
- `09:58:45.520` `question_release`
- `09:58:52.299` `transcript len=15 bound=srq-6da0b01ac047` and `fireOrCancel=voice.transcript` with `complete=` empty and `words=0` (answer consumed, no new turn)
- `09:59:16.508` `follow_up_release` for the reply that completed `09:58:59.661`

No `follow-up-idle` and no `wake.resume` after that release. The next voice line is the lock gate at `10:38:31` (`gate step: cancel follow-up/echo`, then `gate refuse: wake-reconcile-resume`). That is the stuck ending in the Phase 2 table: armed flags left true, reconcile already paused, no `wake.resume`. An earlier non-clarify silence in the same window did resume: `09:56:16.894 wake.resume reason=follow-up-end`.

Second try is still required.

## L1 try 2 — clarify tool

**Brian (his words):** She asked "Do you want it in one word or a sentence." He responded "one word." She answered "5:54 PM."

This try did open a clarify request.

- `server-requests.log`: `17:54:25.153` received `id=srq-ed0515905199 method=clarify session_id=3da8e6ef`; `17:54:25.156` shown; `17:54:37.021` answered `text_or_len=8`.
- `17:54:25.182` `question_spoken` chars=50. `17:54:31.479` `question_release`.
- `17:54:37.011` `transcript len=8 bound=srq-ed0515905199`, then `fireOrCancel=voice.transcript followUpStarted=False words=0` with `complete=` empty. The answer cleared the capture and did not start a turn.
- `17:54:47.983` `follow_up_release` for the reply completed `17:54:43.165`, and `followUpStarted=True`.

No `follow-up-idle` and no `wake.resume` after that release. `display-state.log` last line of the probe: `17:54:57.453` voice="Idle" mic="Mic: off". The follow-up capture opened (`17:54:48` Listening / recording, `17:54:56` Transcribing) and ended on mic off.

**Brian, HUD (screenshot at 17:57):** voice Idle, `MIC: OFF`. That matches the log.

**Brian, wake check (his words):** "She did not wake." No `wake.detected` after `17:54:06`. `server-requests.log` stayed at 23381 bytes. `display-state.log` stayed on `17:54:57` Idle / `Mic: off`.

### Try 2 mapped onto the Phase 2 ending table

| Moment | What the log shows | Resting flags | Reconcile | Expected `Resting` |
|---|---|---|---|---|
| Answer consumed `17:54:37` | `bound=srq-ed0515905199`, `fireOrCancel=voice.transcript`, `followUpStarted=False`, `words=0`, `complete=` empty | `CancelFollowUp("voice.transcript")` clears the armed flags. It does not clear `_followUpTranscriptSeen`. The Hermes turn is still running, so `TurnRunning` stays true. | No `wake.resume`. A resume while the turn is running would not be `Resting`. | false, because the turn is still running |
| Reply follow-up opens `17:54:47` | `follow_up_release`, `followUpStarted=True`, `words=5` | `OnTurnCompleted("complete")` sets `_followUpArmed` again and does not clear `_followUpTranscriptSeen` | none on this line | false |
| Follow-up silence `17:54:48`–`17:54:57` | Listening, then Transcribing, then Idle / `Mic: off`. No `transcript` line. No `follow-up-idle`. | Armed flags stay set. Seen stays true, so the idle path skips `CancelFollowUp`. | No `wake.resume` and no reconcile line. That is the silent converged return: not resting, and wake already paused. | false |
| "Hey Zola" ~18:02 | No `wake.detected` | unchanged | none | false |

**LEAD Q3.** Refuted as an immediate post-answer state: the answer's `voice.transcript` line has `followUpStarted=False`. Confirmed as the stuck end-state: the reply follow-up sets `followUpStarted=True`, the silent ending never logs `follow-up-idle`, and wake stays paused. The flag values themselves are not logged (P5PRE-AUD-02). Mic off plus the missing cancel is the evidence.

**L1 result:** reproduced on try 2. Try 1 did not open a clarify request. The 09:58–09:59 window is the same stuck ending.

Session id for this conversation, from the clarify line: `3da8e6ef`. Hermes stored session id for the same window: `20261001_171748_4c0672`.

## L2 — cross-session memory

**Brian, A1 (his words):** "Remembered." He also reported she returned to Idle and is listening for "Hey Zola". That typed turn is a new turn, which is the path that clears the stuck follow-up flags. It is not part of the L2 score.

**A2 — write:** PASS.

- `memory` tool ran once in session `20261001_171748_4c0672`, message id 1662. Action `add`, target `user`. `session_search` did not run.
- `USER.md`: 13 entries, 1984/2750 chars, no `[tag]`. Probe entry: `Brian's P5PRE test color is teal-forty-two.`
- `MEMORY.md`: unchanged. 1 entry, 234/4400 chars, no `[tag]`. SHA-256 still `8264268512E5CC7A37FFF847F523CA142C310DBF21BEF30C2AD601EE3A5986EB`.
- Prep `USER.md` was 12 entries, 1938/2750, SHA-256 `881E6D34683E77B078E84BE856D9BC91F689BEFAEC39E5630869ECB22A9F8BE7`. Now SHA-256 `87DA21EE35A93B094CF0016D9545D55A325EC252E1FA9A748496BDC240F8375C`.

**Brian, A3 (his words):** "teal-forty-two."

**A3 classification: conversation-context control only.** Messages after the write, same session: user id 1664 (the question), assistant id 1665 (the answer contains the probe string). No `memory` tool and no `session_search` on that turn. A correct answer does not show that `USER.md` was injected.

**Brian, B1 (his words):** "Teal-forty-two."

**B1 — cross-session, same process: PASS. Memory recall, not transcript search.**

| | Session id | Stored prompt contains `teal-forty-two` | Tools on the recall turn |
|---|---|---|---|
| A (write) | `20261001_171748_4c0672` | no (`system_prompts` hash `12457c9c…`, 25127 chars) | `memory` add, on the write turn only |
| B (new session, app not restarted) | `20261001_180933_8c38a5` | yes (hash `8a3e325c…`, 25173 chars) | none |

Session B's messages are only the question (id 1666) and the answer (id 1667). No `memory` call and no `session_search` call. Both prompts contain the `USER PROFILE` and `MEMORY (your personal notes)` headers. The probe string is absent from A's stored prompt and present in B's. That is a new `load_from_disk()` on the new agent, not a search of A's transcript.

**Brian, C1 (his words):** "Teal-forty-two."

**C1 — after serve restart: PASS. Memory recall, not transcript search.**

Session `20261001_181135_bce549`. Question id 1668, answer id 1669. No tool ran. Stored prompt hash `a3e43ad5…` contains `teal-forty-two` (58736 chars). The new serve's parent is the new client (pid 6468).

**Brian, D1 (his words):** "Forgotten."

**D1 — byte-identical restore.**

`memory` `remove`, target `user` (message id 1672). The probe entry is absent. `MEMORY.md` and `USER.md` both match the Prep backup on entry count, character count, `[tag]` set (none), and SHA-256.

| File | Entries | Chars | SHA-256 |
|---|---|---|---|
| `MEMORY.md` | 1 | 234/4400 | `8264268512E5CC7A37FFF847F523CA142C310DBF21BEF30C2AD601EE3A5986EB` |
| `USER.md` | 12 | 1938/2750 | `881E6D34683E77B078E84BE856D9BC91F689BEFAEC39E5630869ECB22A9F8BE7` |

The remove targeted `user`, not `MEMORY.md`. C8 scopes forget to `MEMORY.md`. The files were not edited by hand. HUD after the reply returned to Idle, mic listening for "Hey Zola" (`18:13:49`).

### L2 result table

| Step | Result | Tool evidence |
|---|---|---|
| Write (A2) | PASS | `memory` `add` target `user`. Entry in `USER.md` only. |
| Same-session control (A3) | PASS as conversation context | No `memory`, no `session_search`. Not evidence the file was injected. |
| Cross-session, same process (B1) | PASS | No tools. Probe is in B's stored system prompt and not in A's. |
| After restart (C1) | PASS | No tools. Probe is in the new session's stored system prompt. |

The pattern supports a successful built-in write plus a fresh `load_from_disk()` on each new agent. It does not support "a fact already on disk is missed by the next session" or "recall came from `session_search`." The snapshot freeze is visible only inside session A: A's stored prompt still lacks the probe after the write. Session B and the post-restart session both loaded it from disk.

## L3 — listen-to-think timings

Five spoken turns, 18:52:24–18:54:39, after the Windows lock cleared at 18:47:46. A lock from 18:28:52 to 18:47:45 sat between D1 and these turns. It is not one of the five.

`agent.log` does record silence, capture stop, and WAV write. Those stages are measurable there. Whisper load end and inference start/end are still not their own lines. The inference figure below is the residual from `WAV written` to the client `transcript` line. `prompt.submit` and `message.start` are not their own lines; the Thinking label is the proxy, and it follows the transcript line by 2–3 ms.

The cold load for this serve was not on these turns. `agent.log` `18:12:16.668` `Loading faster-whisper model 'base'` fired on an earlier no-speech capture. The next line is `18:12:20.692`. There is no load-end line, so that 4.5 s includes the load and that empty clip. All five L3 turns are warm.

Silence is the configured 1.5 s. The log prints that configured value (`Silence detected (1.5s)`), not a measured start time.

| Turn | len | Recording includes silence | Silence fired | Stop after silence | WAV after silence | WAV → transcript | Transcript → Thinking | Silence fire → Thinking |
|---|---|---|---|---|---|---|---|---|
| 1 short | 16 | 4.1 s | 18:52:28.568 | 3 ms | 13 ms | 1680 ms | 3 ms | 1696 ms |
| 2 short | 16 | 2.5 s | 18:52:45.979 | 2 ms | 4 ms | 1562 ms | 2 ms | 1568 ms |
| 3 medium | 66 | 6.5 s | 18:53:06.379 | 3 ms | 11 ms | 1819 ms | 3 ms | 1833 ms |
| 4 medium | 66 | 6.5 s | 18:53:55.259 | 1 ms | 9 ms | 1801 ms | 2 ms | 1813 ms |
| 5 long | 120 | 11.0 s | 18:54:38.078 | 3 ms | 11 ms | 1847 ms | 2 ms | 1860 ms |

Adding the configured 1500 ms silence to "silence fire → Thinking" gives 3196, 3068, 3333, 3313, and 3360 ms from the moment the silence timer starts. The timer's start is not logged, so those five sums assume the fired threshold was the whole wait.

Largest measured stage after he stops talking: the WAV → transcript residual (Whisper inference plus delivery), 1562–1847 ms. The silence wait is 1500 ms by config. Capture stop and WAV write are 1–13 ms. Submit to the Thinking label is 2–3 ms.

## After the probes

Client pid 6468 and its serve (pids 14684, 13584) were stopped. `config.yaml` and `SOUL.md` hashes match Prep. `MEMORY.md` and `USER.md` match Prep (byte-identical restore). `hermes-agent` is clean at `345cd2b057a452236de401d3534b8502a7465e8d`.
