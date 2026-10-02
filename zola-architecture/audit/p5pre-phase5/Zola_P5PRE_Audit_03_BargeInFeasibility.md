# P5PRE Audit 03 — S36 barge-in feasibility

Static trace only. No winner. The synthesis states the feasibility gate. Live profile `voice.barge_in` is `false` (P4-D28). Hermes pin `345cd2b0`.

Acceptance criteria, all required (OQ S36):

- **(a)** talk-over stops a long reply
- **(b)** a spoken clarify answer works, with no "Interrupted"
- **(c)** no P2-D13 self-interrupt loop
- **(d)** the Track 1 lock gate still fails closed (P4-D02)
- **(e)** an answer that starts as soon as she stops, before the beep, keeps its first word (needs about 1.2 s of pre-roll; `voice.record` has none)

---

## 1. Listener ownership

With `barge_in: true`, playback is watched by one process-global thread.

`_arm_barge_listener_if_enabled` (`tui_gateway/methods_voice.py` 158–161) arms only when voice mode is on and `voice.barge_in` is not false. The default of that lookup is `True`. The live profile sets it `false`, so this arm does not run today.

`_arm_full_duplex_listener` (148–155) is idempotent: `_fd_listener_active` is the single flag, and it starts one daemon thread named `voice-full-duplex`. That thread calls `full_duplex_listen` (173–191). State it holds: the active flag, a per-listen `tripped` event, and `_fd_speak_pipelines` (TTS stop/done events). It stops itself when voice mode is off, or when nothing is generating, speaking, or playing (`_should_stop`, 180–182).

On a trip, `_fd_trip` (219–246) always does the same thing, with no clarify check:

1. `mark_speech_interrupted()`
2. cut streaming TTS, every speak pipeline, and the file player
3. if the phase is not `"playback"`, `agent.interrupt()` on every running session
4. emit `voice.interrupted`

`_deliver_fd_transcript` (249–259) then emits `voice.transcript`. There is no clarify branch. That is the P4-era "Interrupted" path: the spoken question is TTS, the listener treats the next speech as a barge, cuts her, and the client shows the interrupt notice.

The client receives `voice.interrupted` in `VoiceController.OnVoiceInterrupted` (2074–2084). That is the P2-D13 loop in code: it cancels any follow-up, increments `_selfInterruptCount`, and at `SelfInterruptLimit` (3, line 115) calls `EnterTextModeAsync`. A completed turn resets the count elsewhere. The guard does not prevent the trips. It leaves Voice after three of them.

**P5PRE-AUD-13** [MATCH] — With the live `barge_in: false`, the full-duplex listener is not armed. One listener, one mic, when it is armed.

**P5PRE-AUD-14** [RISK] HIGH — `_fd_trip` (`methods_voice.py` 219–246) is not clarify-aware. Re-enabling `barge_in` as-is restores the "Interrupted" path that P4-D28 turned off so spoken clarify answers would work. Fails S36 (b).

---

## 2. Pre-roll

`full_duplex_listen` (`tools/voice_mode.py` 1378–1407) keeps a `pre_roll` deque, default `pre_roll_ms=1200`, and feeds it into the capture after a trip. That buffer belongs to the barge listener, not to the answer capture the client uses.

`voice.record` (`methods_voice.py` 703–756) calls `start_continuous` with `silence_threshold`, `silence_duration`, `auto_restart`, and `max_recording_seconds` only. There is no pre-roll or "keep buffer" parameter. `start_continuous` (`hermes_cli/voice.py` 331–340) has the same shape. The beep is played before the stream opens (374–376), so speech that starts before the beep is not in the buffer.

`listen_for_speech(..., capture=True, pre_roll_ms=1200)` (`voice_mode.py` 1111–1165) does keep a pre-roll. Its only in-tree caller is `tests/tools/test_voice_mode.py`. It is not on the RPC surface and not a plugin hook. The comment that it has had no production caller since `full_duplex_listen` took over matches the tree.

**P5PRE-AUD-15** [GAP] HIGH — The capture the client uses for a clarify answer and a follow-up (`voice.record`) has no pre-roll. The 1200 ms buffer exists only on the barge listener and on an uncalled function. S36 (e) does not pass on this pin. This is the residual P4-D18 first-word clip.

---

## 3. Echo handling

`_BargeDetector.feed` (`voice_mode.py` 1344–1375) calibrates a quiet-room floor before playback. While `playing` is true the floor is held: ambient samples are appended only when `not playing`. The playback trigger is clamped to at least `PLAYBACK_MIN_TRIGGER` (1500, line 1276). `grace_ms` (default 500, passed from `barge_in_grace_seconds` default 0.5) suppresses the onset. The multiplier default is 3.0 unless `barge_in_threshold_multiplier` is set.

That is not the older bleed-baked floor. `listen_for_speech` still raises its floor from speaker bleed (8×, ceiling 4000). That function is not the armed listener.

Capture opens `sounddevice.InputStream` at `SAMPLE_RATE` 16000 (`voice_mode.py` 30), one channel, `int16`, no `device=` argument (734 and 1407). PortAudio's default input device is used. Which Windows host API and which device that is on this laptop is **UNVERIFIED** (a live device query would verify it).

No acoustic echo cancellation appears in `tools/` (no AEC, WASAPI, or echo-cancel symbols on the capture path). Windows audio enhancements (echo cancellation) are required ON by `identity/VOICE_CONFIG.md` and P2-D16. Whether they are on at this moment is **UNVERIFIED** until a live check. They are not implemented in this repository.

The client's own echo filter is separate and runs after a transcript arrives: `IsEchoOfLastReply` (`VoiceController.cs` 2596), rule at 96–98, applied at 1929. It drops a follow-up only when a ≥3-word in-order run is ≥0.60 of the transcript and ends near her last spoken words (P2-D14). It does not run inside the barge detector, and it cannot stop `_fd_trip`.

---

## 4. Extension points

A profile plugin cannot replace this behavior without editing `hermes-agent`.

Searched `plugins/` for `barge_in`, `full_duplex`, and `pre_roll`. The only hit is `plugins/google_meet/meet_bot.py`, which tracks a Meet bot timestamp. It is not the GUI voice listener.

Config keys that do exist, and only these:

- `voice.barge_in` — arm or don't (`methods_voice.py` 160)
- `voice.barge_in_threshold_multiplier` and `voice.barge_in_grace_seconds` — numbers passed into `full_duplex_listen` (208–216)

None of them make the trip clarify-aware, and none add a pre-roll to `voice.record`.

**P5PRE-AUD-16** [GAP] MEDIUM — No profile-plugin or config hook changes the barge listener's clarify behavior or `voice.record` pre-roll. Config can only turn the existing listener on or off and set its floor multiplier and grace.

The client lock gate (P4-D02) is independent of that listener. It turns voice off, stops wake, and refuses capture. `_should_stop` returns true when voice mode is off (180–182), so a gate that has completed `voice.toggle` off disarms the listener. An in-flight trip that already passed `_should_stop` is **UNVERIFIED** as a race; the gate's refuse path is client-side and does not depend on barge-in.

Stop speaking (P4-D29) is the client's `ExecuteStopSpeakingAsync` path. It is a user action, not a barge detector.

---

## 5. Options matrix

Scored from this pin. O2 is marked not available here and scored as if the named upstream changes were adopted.

| | (a) talk-over stops her | (b) spoken clarify, no "Interrupted" | (c) no P2-D13 loop | (d) gate fails closed | (e) first word kept | Hermes edit | Locked-decision conflict | Hardware | Probe that resolves UNKNOWN |
|---|---|---|---|---|---|---|---|---|---|
| **O1** Re-enable `barge_in: true` plus client-only mitigations | **PASS** — `_fd_trip` cuts TTS (`methods_voice.py` 232–236) | **FAIL** — trip always emits `voice.interrupted` and has no clarify check (AUD-14). The client cannot stop that latch. | **UNKNOWN** — the counter still switches to Text at 3 (`VoiceController.cs` 2074–2084). P2-D16's required setup did not self-trip in a 15 s playback; a closed lid did. | **PASS** — gate still calls `voice.toggle` off; `_should_stop` follows voice mode | **FAIL** — answer capture is `voice.record`, which has no pre-roll (AUD-15) | no | P4-D28 set `barge_in: false` so spoken clarify would work. Re-enabling it reverses that decision. | no | A barge-on playback in the P2-D16 setup (enhancements on, lid open) for (c) |
| **O2** Upstream: clarify-aware listener, discardable record stop, pre-roll on `voice.record`. **Not available at this pin.** | **PASS** as if adopted — pause-barge during a reply can stay the current trip | **PASS** as if adopted — a clarify-aware trip would not emit `voice.interrupted` for the answer | **UNKNOWN** — the named change does not specify the quiet-room floor. The loop can still happen if playback bleed trips three times | **PASS** as if adopted — the client gate is unchanged | **PASS** as if adopted — pre-roll on `voice.record` is the missing buffer (AUD-15). `full_duplex_listen` already has 1200 ms; the answer path does not | **yes** | none of C4, S14, P4, P2-D01. It would revise the practical effect of P4-D28 | no | After an upstream build: the five criteria, live |
| **O3** Profile plugin or config, using only what Q4 found | **PASS** only by setting `barge_in: true` — same listener as O1 | **FAIL** — no hook adds clarify awareness (AUD-16) | **UNKNOWN** — same as O1; thresholds can be raised, which can also fail (a) | **PASS** — config does not touch the gate | **FAIL** — no hook adds pre-roll to `voice.record` | no | same as O1 if `barge_in` is turned on | no | none for (b) or (e); those need a hook that does not exist |
| **O4** Headset, or OS echo cancellation | **UNKNOWN** — AEC can change whether bleed trips; it does not itself stop a reply. Talk-over still needs the listener | **FAIL** — user speech during her question still trips `_fd_trip` if barge is on. AEC does not add a clarify policy. OS echo cancellation is already required by VOICE_CONFIG | **UNKNOWN** — the historical loop was bleed and a closed lid. A headset might remove that bleed. Not measured | **PASS** — hardware does not touch the gate | **FAIL** — a headset does not add a pre-roll buffer | no | none | **yes** | Headset capture during playback, barge on, P2-D16 setup, for (a) and (c) |
| **O5** A client-side detector | **UNKNOWN** — the client could call `session.interrupt` or `voice.toggle` only if it had audio | **UNKNOWN** — would need its own clarify policy | **UNKNOWN** | **PASS** if it still refuses while the gate is closed | **UNKNOWN** — a client buffer could keep pre-roll | no, if it only called existing RPCs; **yes** if it needed a new capture RPC | **P2-D01** — the serve child is the sole mic owner. A client detector has to open an input device, which is a second listener on the same mic | no | Not worth a probe while P2-D01 stands |

O1 client mitigations cannot reach inside `_fd_trip`. The echo filter (P2-D14) runs on a transcript that has already been delivered. The P2-D13 guard runs after `voice.interrupted` and leaves Voice. Neither is a clarify-aware listener, and neither adds pre-roll.

No option is selected here.
