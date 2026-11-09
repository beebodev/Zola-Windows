# Zola-Windows S51F Build Plan
## Backend crash fix (S51): remove the shared audio stream from use, tell Brian when a request is lost, capture better evidence

**Base branch:** `main`
**Base SHA:** record at plan commit (the S51F-PRE merge tip or later).
**Audits:** S51-CRASH (merge `7be69490f1ce7a89d52c33a47d9003089e117ea6`) and S51F-PRE (Stage 1 of this track; audit
`53877a824a90940695777be29f8638c8fc4766bb`, merge `4368af2cc8012688d6a538d89df8c6790664b93c`; `main` after it
`702bb62906d197af943b8834430cf026642a1850`).
**Theme:** Zola's backend crashes inside PortAudio, most likely on the shared `sd.play` stream (S51; blocks Phase 11 under
the SOP v3 stability gate). S51F-D01 already turned the thinking sound off. This plan turns off the remaining user of
that stream (Hermes beeps), shows Brian a visible line when a crash drops his request, and turns on crash diagnostics.
Remediation only: no new capability, no Hermes source change, no speech-pipeline change.

**SOP:** v3.0 under its transition rules (v2.2 verification and merge rules; no merge replaces the everyday build without
Brian's approval). This plan is the full-lane Stage 3 for a single-track fix.

---

## Overview

| Track | Name | Scope | Complexity |
|-------|------|-------|------------|
| S51F-FIX | Beeps off, lost-request line, diagnostics | Live `config.yaml` (one line, P4-D25); `identity/VOICE_CONFIG.md`; Windows client (`MainWindow`, supervision, process launch); client checks | Small-Medium |

**Sequencing rule:** one track, three waves in order: W1 config → W2 lost-request line → W3 diagnostics. Each wave ends at
a STOP.

---

## Decisions resolved in this build plan

Full text and Brian's verdicts: Claude's project `claude/S51_FIX_DECISIONS.md`. Summary:

**S51F-D01 — Thinking sound off.** Applied 2026-11-09 in S51F-PRE (`voice.thinking_sound: false`). Crash watch started
2026-11-09 11:40:57.

**S51F-D02 — Pre-tool acknowledgement moves to the speech track.** The model emitted no text before the tool, and Hermes
holds a short pre-tool line until after the tool (no TTS flush at tool start). Fixing it needs speech-pipeline work.
Nothing in this plan touches it.

**S51F-D03 — Hermes beeps off.** `voice.beep_enabled: false` (supported Hermes config; gated before any PortAudio call).
Removes the listen-start (880 Hz) and capture-end (660 Hz ×2) cues. Listening state remains visible in the presence UI.
Rules out `beep_volume: 0` (still calls PortAudio). With D01 and D03, nothing in Brian's setup uses the shared stream.

**S51F-D04 — Lost request: a visible line now.** When the backend becomes unreachable while a turn is open, the client
shows one visible line in the conversation (exact wording approved by Brian at the W2 STOP) and stops showing any partial
reply as live. No automatic re-submission. No spoken notice now (speech track later).

**S51F-D05 — No Zira notice.** The client does not speak any crash notice.

**S51F-D06 — Diagnostics.** The client sets `PYTHONFAULTHANDLER=1` in the environment of every Python process it
launches (serve, watcher, `zola-phone`), and logs process ids at start, stale and restart. No Hermes change.

---

## Track S51F-FIX

### Problem

- S51 audit Group A: PortAudio stream thread → unbacked address, 5 of 6 dumps, including both 2026-11-09 crashes; observed
  on `p10-closed`. INFERENCE: callback freed or replaced on the shared `sd.play` stream.
- S51F-AUD-01 (HIGH): after D01, Hermes beeps still use the shared stream (`hermes_cli/voice.py` `_play_beep` → `play_beep`
  → `_sd_play_blocking`).
- S51F-AUD-08 (HIGH) / S51-AUD-02: on a crash Brian sees only "Zola's backend stopped. Restarting…"; the in-flight request
  is dropped silently (`MainWindow.ShowUnreachable` L1289–1298 discards the reason; `ShowSupervisionStatus` L1301–1314 clears
  `_streaming` but not `_turnFinalized`; the live bubble can remain).
- S51F-AUD-11/12: no Python faulthandler; serve pid not in the supervision log.

### Files to read

- Live profile `config.yaml` (keys only; one edit in W1).
- `zola-architecture/identity/VOICE_CONFIG.md`.
- `windows-client/Zola.Client/MainWindow.xaml.cs` (focus: `ShowUnreachable`, `ShowSupervisionStatus`, turn submit and
  finalize, live-bubble handling, how system/notice lines are added to the conversation).
- `windows-client/Zola.Client/Supervision/*` (`ProcessSupervisor`, `SupervisionConstants`), `HermesProcessManager.cs`,
  `HermesProcessManager.Supervision.cs`, `WatcherProcess.cs`, `PhoneProcess.cs`, `HermesLaunchResolver.cs` (where each
  Python process is launched and its environment built; where supervision logs are written).
- `windows-client/Zola.Client/Voice/TurnTiming.cs` (open-turn state).
- `windows-client/Zola.Client.Checks/*` (existing check style; `SupervisionChecks.cs`).
- `hermes-agent` (read-only at pin `345cd2b…`): `hermes_cli/voice.py` L132–157 (beep gate), `hermes_cli/config_defaults.py`
  (`beep_enabled` default).

### Changes

**W1 — Config (P4-D25).**
- Live `config.yaml`: set `voice.beep_enabled: false`. If the key exists, change its one line; if it doesn't, add one line
  in the `voice:` block with the same indentation. Backup `config.yaml.bak-S51F-FIX-<yyyyMMdd-HHmmss>` first. Exact
  before/after shown and approved by Brian at the W1 STOP.
- **Rollback (live profile).** The backup's exact path is reported at the W1 apply STOP and kept until Phase 7 (P6-D11)
  or until Brian says otherwise. If wake word or follow-up stops working after the relaunch, Cursor restores the backup at
  once, confirms the original SHA-256, reverts `VOICE_CONFIG.md`, asks Brian to relaunch, and STOPs. If a beep is still
  heard, or Brian can't tell when she is listening, Cursor STOPs with the change in place and Brian decides whether to
  restore. If the track stops after W1 for any other reason, the line stays (it is an approved mitigation that doesn't
  depend on the client changes) and the backup stays.
- `identity/VOICE_CONFIG.md`: exact text issued by Claude after the W1 STOP (it depends on whether the key already
  existed), with its expected SHA-256.

**W2 — Lost-request line (D04), client only.**
- A small pure class (e.g. `Supervision/LostTurnNotice.cs`) decides, from the turn state at the moment the backend becomes
  unreachable, whether a request was in flight: a turn submitted and not finalized (`TurnTiming.IsOpen` or `_streaming`
  with `_turnFinalized == false`). No notice when nothing was in flight, or when the gap is a deliberate shutdown.
- In the unreachable path (`ShowSupervisionStatus` / `ShowUnreachable`): if a request was in flight, (1) finalize the live
  bubble so it no longer appears to be streaming, keeping any text already shown, marked as interrupted per the approved
  wording; (2) add one visible notice line to the conversation using the client's existing system/notice line style;
  (3) mark the turn finalized so nothing later treats it as open. At most one notice per dropped turn.
- Never re-submit the request; never touch approvals or pending sends beyond what the gap already abandons.
- Wording: a constant in `SupervisionConstants` (or the existing constants home), proposed by Cursor at the W2 STOP and
  approved by Brian verbatim. Neutral system wording, not first-person Zola speech; not spoken.
- Comment tag: `// S51F-FIX: <why> — S51F-D04`.

**W3 — Diagnostics (D06), client only.**
- Wherever the client builds the start info for a Python process (serve, watcher, `zola-phone`), add
  `PYTHONFAULTHANDLER=1` to its environment through one shared helper, without changing any other variable.
- Supervision log: at process start, stale and restart, include the launcher pid and, if the client can obtain it
  cheaply and reliably, the interpreter child pid. If the child pid can't be obtained without a new dependency, log the
  launcher pid only and say so.
- Confirm from source where each process's stderr goes. Faulthandler writes to stderr; for any process whose stderr is
  not kept, report it at the W3 STOP (no new log file without approval).
- Comment tag: `// S51F-FIX: <why> — S51F-D06`.

### Tests (new, PR-D01)

- `LostTurnNotice`: in-flight typed turn → notice; in-flight voice turn → notice; no open turn → none; deliberate
  shutdown → none; second unreachable for the same turn → no second notice; **turn already finalized (reply complete,
  speech may still be playing), then unreachable → none**; in-flight turn with partial text → the text is kept, marked
  interrupted.
- Environment helper: `PYTHONFAULTHANDLER=1` present for serve, watcher and phone start info; other variables unchanged.
- Supervision log line formatting includes the pid fields.
- All existing suites keep passing at no fewer tests than their current counts.

### Smoke (Brian and Cursor)

- **SM1 (Brian):** wake word and a normal question, a follow-up, and a voice clarify answer all work; **no beeps**; he can
  still tell when she is listening (presence UI).
- **SM2 (Cursor-run kill drill, Brian present):** Brian asks a question with a long answer. Cursor stops the **serve
  interpreter** by pid only while the turn is **confirmed open**: the reply text is still arriving and the client log shows
  no finalize event for that turn (a deliberate kill, like the P9-SUPERVISE R1 drill, not a crash reproduction). Killing
  after the text is complete, while speech is still playing, doesn't count: that turn was not lost, and no notice is
  expected. Pass: the client log confirms the turn was open at the kill time; the approved notice line appears once; any
  partial text already shown stays visible, marked interrupted, and is no longer live; serve restarts; nothing is
  re-submitted; the next question works.
- **SM3 (Cursor):** after SM2's restart, the supervision log shows the pid fields, and the restarted serve has
  `PYTHONFAULTHANDLER=1` (read from the process environment if possible, otherwise from the client's launch log line).

### Experience checks (Brian's words to confirm)

- "She no longer beeps at me, and I can still tell when she's listening."
- "If her backend dies while I'm asking something, I'm told it didn't go through and to ask again."

### Exit criteria

- [ ] `voice.beep_enabled: false` live, one-line diff, backup made; `VOICE_CONFIG.md` matches the issued SHA-256.
- [ ] Lost-request notice appears exactly once per dropped turn, never when idle, never re-submits; partial reply not left
      live.
- [ ] `PYTHONFAULTHANDLER=1` set for serve, watcher and phone; pids in the supervision log.
- [ ] New tests present and passing; client builds; all suites pass at no fewer tests than before.
- [ ] SM1–SM3 pass; Brian confirms both experience checks.
- [ ] No Hermes, plugin, Kotlin or companion change; no other config key changed.

**Complexity:** Small-Medium.
**Primary risk:** the notice firing on a deliberate shutdown or twice for one turn, or the live-bubble cleanup clearing
text Brian already saw. The tests above pin these.

---

## After merge: crash watch

About a week of normal use from the W1 relaunch. Report every `python.exe` crash (event log) and any faulthandler output.
The closeout compares the quiet period with the crash rate before the fix; if earlier crashes were days apart, the watch
is extended until the gap is clearly longer than usual.
- No crashes: evidence the mitigation works, not proof of the cause. Group A is closed operationally, with D01/D03 as the
  mitigation. The record keeps the stream direction (shared output vs microphone input) UNRESOLVED, and S51 reopens if a
  Group A crash returns.
- Crashes continue: the remaining suspect is the mic stream lifecycle (`AudioRecorder._close_stream_with_timeout` closes on
  a helper thread while a callback may still run). Fixing that needs Hermes source; Brian decides whether to reopen the
  2026-10-06 no-fork decision.

## Lore closeout (after the watch)

- `DESIGN_DECISIONS.md`: S51F-D01–D06.
- `OPEN_QUESTIONS.md`: S51 updated with the audits, the fix and the watch result (RESOLVED or narrowed); new OQs for the
  speech-track items below.
- `ROADMAP.md`: S51 fix recorded; Phase 11 readiness re-checked against the stability gate.
- `KNOWN_ISSUES` (created by the first process track): self-echo (incl. 2026-11-09 S1 turns), mic button not interrupting
  a reply, Stop Speaking unavailable on unprompted lines, clipped opening words, the `python312+0x3b1ff` and sqlite crash
  classes (diagnostics only).

## Explicitly deferred

| Item | Reason | When |
|------|--------|------|
| Pre-tool acknowledgement in her own words (D02) | Needs speech-pipeline change (tool-start flush) and model behaviour | Speech track |
| Spoken lost-request notice in her voice | Needs serve up and speech work | Speech track |
| Audible listening cue off PortAudio | Only if Brian misses it | On request |
| Mic stream lifecycle fix | Needs Hermes source; only if the watch shows crashes continue | After the watch |
| Stream breadcrumbs inside Hermes | Hermes source | With a Hermes change, if ever |
| Sqlite / `0x3b1ff` crash classes | Diagnostics first | After faulthandler evidence |
| Self-echo, mic interrupt, Stop Speaking on unprompted lines | Speech/voice behaviour | Speech track / known issues |

*S51F Build Plan version 1.1 — created 2026-11-09; v1.1 the same day (kill drill timing, completed-turn test, config
rollback, crash-watch wording). Base SHA: record at plan commit. Prerequisite audits: S51-CRASH, S51F-PRE.
All decisions locked before the plan was written (Brian, 2026-11-09). Next: commit this plan in S51F-FIX Phase 1, then W1.*
