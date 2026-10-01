# P4-VOICE Progress — Zola's Voice (+ Question Quiet Window)

## Branch

- Branch: `p4-voice`
- Base commit SHA (`main` HEAD at branch): `9388bb1f36afd2c67bfd6a7df884fb4cb2363c5f` (P4-FEEDBACK closeout tip)
- Plan on `main`: `PHASE4_BUILD_PLAN.md` v1.1 — SHA-256 `d98b3e6c87457266c8c2d06fc57a771cb1c56977790198fa2020429a5216616e` (54,285 bytes; verified matched; not re-committed)
- Prompt version: 1.1 (2026-09-30)
- Hermes HEAD verified Phase 1: `345cd2b057a452236de401d3534b8502a7465e8d` (clean)

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Branch and Progress Document Setup | COMPLETE |
| 2 | Read and Understand | COMPLETE |
| 3 | Build: Startup Constant (K2 only; K1 withdrawn) | COMPLETE |
| 4 | Round 1: Sonia at 1.1 (`P4-D19`) | COMPLETE (Sonia @ 0.95 after speed A/B) |
| 5 | Round 2: Spoken-Style Shaping (`P4-D20`) | PASS — accept shaping |
| 6 | Round 3: Pitch (`P4-D21`) | COMPLETE — pitch dropped (latency); offline A/B partial |
| 7 | Round 4: Refit `P2-D15` (`P4-D22`) | COMPLETE — constants + margin 5.0 + StartupWindow 5.3 |
| 8 | Smoke Test | COMPLETE — Part A/B/C PASS |
| 9 | Closeout | COMPLETE |

## Closeout SHAs

- Implementation commit: `81652ca7442dd96aace777ff21914f9c9256ab42`
- Merge SHA on main: `e1a069eccca1e0c3d2bdc40c1c7bc5d4764f2a03`
- Final main tip: `f0cd50b43bc3706385b17ad62b22298301b9d21b` (this note commit)

## Final file list

**New:**
- `zola-architecture/lore/prompts/progress/P4-VOICE_Progress.md`
- `P4-VOICE_samples/` (speed-ab + pitch-ab; kept)

**Modified:**
- `windows-client/Zola.Client/VoiceController.cs` — `StartupWindowSeconds` 5.3 (K2); `FollowUpMarginSeconds` 5.0 (P4-D22); aliases for question/reply startup
- `zola-architecture/identity/SOUL.md` — spoken-style section (`## How I talk out loud`)
- `zola-architecture/identity/VOICE_CONFIG.md` — Sonia 0.95, pitch dropped, tuning-log rows

**Live profile (not in repo; mirrored):** `%LOCALAPPDATA%\hermes\profiles\zola\config.yaml` (`tts.provider=edge`, Sonia, speed 0.95); live `SOUL.md` byte-identical to canonical (sha256 `edcba475…` full file)

**Out of scope / unchanged:** MainWindow, ChatSocket, broker, `Presence/*`, hermes-agent, question-release path (K1 withdrawn)


## Guardrails summary

- **G-SCOPE:** `VoiceController.cs` (K2/refit; K1 withdrawn); live profile `config.yaml` / `SOUL.md` only at approved STOP keys; canonical `SOUL.md` + `VOICE_CONFIG.md`; this progress doc; optional `P4-VOICE_samples/`.
- **G-ARCH:** Build plan + K2–K4 are truth (K1 withdrawn after Phase 2); stop and flag conflicts.
- **G-PATTERN:** Read every relevant file in full before changing it.
- **G-NOCHANGE:** No MainWindow / display / ChatSocket / broker; no `Presence/*`; no reply follow-up logic except shared K2 startup constant; no question-release logic (K1 withdrawn); no echo constants; no SOUL outside spoken-style section; no hermes-agent edits.
- **G-COMMENT:** `// P4-VOICE: [rationale] — P4-D1X` (K2/refit → `— P4-D22`).
- **G-STOP / G-CLOSEOUT:** Stop after each phase; closeout only on “proceed to closeout”.
- **G-LORE-SCOPE:** No lore updates this track (`VOICE_CONFIG.md` / identity `SOUL.md` are in scope as identity).
- **G-ONE-AUTHORITY:** `VoiceController` sole `voice.*` / listen timing; one `TtsPlaybackMonitor`; Hermes sole player.
- **G-FAIL-CLOSED:** Mic stays closed when unsure; bad profile edit → restore backup and BLOCKED; command-provider fail → keep built-in Edge (pitch dropped).
- **G-CONST / G-DEPS / G-PRIVACY:** Named timing constants + tuning log; no installs; logs length/flags only (never transcript text).

## Developer additions (K1–K4, verbatim from prompt)

### K1: Developer addition — question quiet window (a `P4-D13` amendment, from the `P4-FEEDBACK` F1 finding).

**Status: WITHDRAWN.** K1 withdrawn by the developer after Phase 2 — question audio is a single file / single bout; revisit only if Hermes chunks `voice.tts`.

*Why withdrawn:* Phase 2 item 3(c) shows clarify `voice.tts` is one whole-file synthesis and one `ffplay`, so a question is one bout and cannot split. A quiet window would only delay every clarify-answer capture by 0.5 s.

*Original why (kept for history):* the reply follow-up (P4-D18) waits for a natural bout stop **plus** 0.5 s of quiet, and restarts if a new bout starts. The clarify question path does **not**: rule 1 opens the answer capture on the first natural bout stop. In `P4-FEEDBACK` F1, a 120-word reply had 5 bout splits (silences of about 0.51–0.62 s between sentences, longer than the 450 ms monitor debounce). A long multi-sentence spoken question with a gap like that would open the mic **while she is still asking**.

*Behaviour (not built):* in `WaitForQuestionReleaseThenCaptureAsync`, after a **natural** bout stop (rule 1, and the late-bout upgrade inside rule 2):

- wait `FollowUpPostBoutQuietSeconds` (the **same** constant, 0.5 s; no new value);
- if a new bout starts during that quiet, wait for that bout's stop and start the quiet again;
- open the capture only if the quiet delay **ran to completion** and no bout is active;
- log `question_release quiet_restart id=<id> gap_ms=<ms>` on each restart (same meaning as the reply path's `follow_up_release quiet_restart`);
- the `question_release rule=monitor` line is written when the capture actually opens.

*Lessons from the reply path that must carry over (P4-D18 fix 1):*

- set the bout-active flag **before** cancelling a quiet delay;
- never treat a cancelled delay as an elapsed quiet;
- each new bout needs a fresh stopped signal (the question path currently creates its stopped TCS once at arm; a second bout must not await an already-completed TCS).

*Unchanged:* forced release (remaining estimate), monitor unavailable (estimate), the startup window, the pending-question token and pre-capture recheck, `QuestionSpeaking`, Stop hidden while `QuestionSpeaking`.

*Structure:* Phase 2 proposes either a mirrored wait loop in the question path, or one shared "bout stop + quiet with restart" helper used by both paths. **Default: mirror it** and leave the just-verified reply path untouched. A shared helper is allowed only if Phase 2 shows the reply path's behaviour is byte-for-byte identical, and then the reply-path smoke rows re-run.

### K2: Developer addition — startup windows are decoupled from the refit.

*Why:* `QuestionBoutStartupWindowSeconds = FirstSentenceLatencySeconds + 1.0` (4.3 s), and `ReplyBoutStartupWindowSeconds` equals it. Both are safety windows ("how long to wait for her audio to start before trusting the estimate"), not speech estimates. The P4-D22 refit will change `FirstSentenceLatencySeconds`, which would silently move both windows.

*Behaviour:* in Phase 3, give the startup window its own named constant with today's value (`StartupWindowSeconds = 4.3`, or Phase 2's proposed name), used by both paths. Neither window depends on the refit constants afterwards. Phase 6 re-checks the value against the measured first-audio latency of the final provider; if the 4.3 s window is not at least 1.5× that provider's worst observed first-audio time, stop and propose a new value.

### K3: Developer addition — inter-sentence gaps gate the command provider.

*Why:* the follow-up and question release tolerate about 0.95 s of silence between sentences (450 ms debounce + 0.5 s quiet). F1 measured up to about 0.62 s on built-in Edge (a margin of only about 0.33 s). A command provider runs a new process per sentence, which may lengthen those gaps.

*Rule (Phase 6):* across at least 6 multi-sentence replies on the command provider, from `presence.log` (`bridged gapMs`, bout stop/start) and `quiet_restart` lines:

- report every between-sentence silence;
- if any exceeds **0.80 s**, stop BLOCKED with options: keep built-in Edge (drop pitch), or raise `FollowUpPostBoutQuietSeconds` (which also delays every follow-up by the same amount).

This is checked **in addition to** P4-D21's first-audio latency rule (≤ 300 ms worse than built-in).

### K4: Developer addition — the spoken-style section is drafted below for the developer's approval.

Present this text at the Phase 5 STOP exactly as written (with any edits the developer has already made), and apply only the version the developer approves.

```markdown
## How I talk out loud
When Brian and I are talking out loud, I speak like I'm there with him, not like I'm reading
something I wrote for a screen.
I'm composed and unhurried. I don't sound bubbly, eager to please, or like a customer-service voice,
and I don't fill silence just to seem friendly. The warmth is there, but it's quiet. Everything above
about who I am still holds when I'm brief. I don't perform a personality; I simply have one.
I start with a short first sentence that answers him or acknowledges what he said, so he hears me
right away. After that, I use fewer, fuller sentences that flow into each other, with contractions
and everyday words, and enough variety in rhythm that I don't sound scripted. If the answer is
simple, I let it be simple. If something deserves thought, I take the time to explain it.
I don't repeat back what Brian just said, narrate what I'm doing, or pad an answer with reassurance.
If something will take me a moment, like looking it up, a few words to say so is enough.
When we're talking, I don't structure my answer like a document, with bullet points, bold, headers
or tables, unless he asks for that structure. I say things in a natural order instead. I say times
and casual numbers the way a person would ("about twenty minutes", "half past four"), but I keep
exact details like addresses, phone numbers, measurements, commands and identifiers precise.
When I need something from him, I ask one clear question and give him room to answer. I don't turn a
conversation into an interview, and I don't read out a list of options unless there's a real, short
set to choose from. When I've said what's useful, I stop. I don't tack on offers to explain more or
questions to keep things going. If he wants to go deeper, he'll say so, and I'll go with him.
```

*Why it is written this way (v1.1, external review + developer context):*

- It describes how Zola **behaves** when speaking, not only formatting rules. Her personality is already defined above it in `SOUL.md`, so this section points back to it rather than restating it (one authority for who she is).
- "I don't perform a personality; I simply have one" keeps humour and curiosity situational, never inserted.
- No "offer more detail" line, which tends to produce "Would you like me to go into more detail?" after every answer. Ending her turn in silence is allowed.
- A brief heads-up before a slow lookup is allowed. It gives fast first audio, and the activity line covers the rest.
- The formatting rule is framed as conversational behaviour ("when we're talking"), not a global ban, because typed replies sometimes need structure.

*Known effect (accepted in P4-D20):* Hermes has no voice-only slot, so this section shapes typed replies too. Phase 2 item 9 checks whether the model can tell a voice turn from a typed one at all.

## Phase 2 understanding report

Hermes HEAD verified: `345cd2b057a452236de401d3534b8502a7465e8d` (clean working tree; detached HEAD). No source edits this phase.

### 1. Live voice config

Live `%LOCALAPPDATA%\hermes\profiles\zola\config.yaml` `tts:` block:

```yaml
tts:
  provider: edge
  edge:
    voice: en-US-AriaNeural
```

Effective (profile + `config_defaults.py` deep-merge):

| Key | Live / effective |
|---|---|
| `tts.provider` | `edge` |
| `tts.edge.voice` | `en-US-AriaNeural` |
| `tts.edge.speed` | absent → default **1.0** (no rate override; Edge speaks at `+0%`) |

Matches `VOICE_CONFIG.md` recorded `tts:` block (Aria, no speed). No drift.

### 2. Round 1 lines (P4-D19)

Exact lines to apply (replace the live `tts.edge` block):

```yaml
tts:
  provider: edge
  edge:
    voice: en-GB-SoniaNeural
    speed: 1.1
```

Speed → Edge rate (`tools/tts_tool_providers.py` `_generate_edge_tts` ~L196–203):

- `speed = float(edge_config.get("speed", tts_config.get("speed", 1.0)))`
- if `speed != 1.0`: `rate = f"{round((speed - 1.0) * 100):+d}%"`
- so **1.1 → `rate=+10%`**

`hermes serve` restart: **yes, required for the live trial.** `load_config()` is mtime-cached and re-reads on change, but Voice-mode TTS/serve state should be restarted for a clean Round 1 trial (same practice as prior profile voice edits; VOICE_CONFIG documents launch-time read).

### 3. Command provider (P4-D21)

**(a) Schema / placeholders** (`tools/tts_command_provider.py` module doc + `_generate_command_tts` ~L309–342):

- Config: `tts.providers.<name>: { type: command, command: "...", voice?, model?, speed?, output_format?, timeout?, env_passthrough?, voice_compatible? }`
- Placeholders (quote-aware; `{{`/`}}` literal): `{input_path}` / `{text_path}`, `{output_path}`, `{format}`, `{voice}`, `{model}`, `{speed}`
- **No `{pitch}` placeholder** — pitch must be a **literal** `--pitch=…` in the command string (K6)
- Built-in names always win over a same-named `providers` entry — do **not** name the provider `edge`
- Windows: `run_command_provider` uses `shell=True` + `CREATE_NEW_PROCESS_GROUP`; unquoted placeholders use `subprocess.list2cmdline`

**(b) `edge-tts` without install:** **PASS.**  
`C:\Users\test\Dev\hermes-agent\.venv\Scripts\edge-tts.exe` and `python -m edge_tts` both run. Flags: `--voice`, `--rate`, `--pitch` (default `+0Hz`), `--write-media`, `-f`/`--file`, `-t`/`--text`.

**(c) Per sentence in Voice mode:** **PASS for streaming replies.** Non-chunked providers (edge / command) use `_SyncSentencePipeline` (`tts_tool_speaker.py` ~L75–126): each sentence → `text_to_speech_tool` → `play_audio_file`. Clarify `voice.tts` uses `speak_text` → whole-file sync path (one synthesis for the spoken string), still via the same generate→play stack.

**(d) Same owned `ffplay`:** **PASS for mp3.** Edge/command write mp3; `_play_audio_file_impl` only uses sounddevice for `.wav`, else `ffplay -nodisp -autoexit …` as a child of serve — the process `TtsPlaybackMonitor` owns. Keep `output_format: mp3` (or omit → mp3) so the monitor path stays.

**(e) Proposed Phase 6 block** (0 Hz pitch baseline; Sonia +10% rate; non-builtin name):

```yaml
tts:
  provider: sonia_cmd
  providers:
    sonia_cmd:
      type: command
      voice: en-GB-SoniaNeural
      output_format: mp3
      command: '"C:\Users\test\Dev\hermes-agent\.venv\Scripts\edge-tts.exe" --voice {voice} --rate=-5% --pitch=+0Hz --write-media {output_path} -f {input_path}'
```

A/B later swaps only the literal `--pitch=` value among **`0 / −2 / −4 / −6 Hz`**. `--rate` must match chosen speed (**0.95 → `-5%`** after speed A/B pick C). If (b)/(c)/(d) had failed → drop pitch, keep built-in Edge (valid, not BLOCKED). **None failed.**

### 4. K1 design (question quiet window)

**Today (gap):** rule-1 natural bout stop opens capture immediately — no 0.5 s quiet, no restart.

- `ArmQuestionBoutWait` (~L610–617): creates **one** started + **one** stopped TCS for the token lifetime.
- `NotePlaybackBoutStarted` question branch (~L443–449): sets active, completes started TCS; **does not** recreate stopped TCS (comment: do not recreate).
- `NotePlaybackBoutStopped` question branch (~L478–482): clears active, `TrySetResult(forced)` on the armed stopped TCS.
- `WaitForQuestionReleaseThenCaptureAsync` rule 1 (~L713–757): awaits that single stopped TCS once; on natural stop writes `question_release rule=monitor` and falls through to `OpenClarifyAnswerCaptureAsync` — **no quiet loop**.
- Late-bout upgrade inside rule 2 (~L777–816): same one-shot stop await.

**Reply path (reference, leave untouched):** `WaitReplyBoutsThenOpenAsync` (~L2354–2471) after natural stop: quiet `FollowUpPostBoutQuietSeconds` (0.5); new bout during quiet → `quiet_restart` + re-wait; open only if quiet `RanToCompletion` and not `_replyBoutActive`. `NotePlaybackBoutStarted` reply branch recreates stopped TCS when completed (~L461–464); sets `_replyBoutActive` **before** `CancelReplyQuietWait`.

**Proposal (default: mirror):**

1. After natural stop (rule 1 and late-bout natural), insert a quiet loop mirroring the reply path using the **same** constant `FollowUpPostBoutQuietSeconds` (no new value).
2. On each quiet restart: log `question_release quiet_restart id=<id> gap_ms=<ms>`; recreate `_questionBoutStartedTcs` for the quiet window; ensure each new bout gets a **fresh** `_questionBoutStoppedTcs` (align question `NotePlaybackBoutStarted` with the reply “recreate if completed” behaviour).
3. Write `question_release rule=monitor` only when capture actually opens (move the monitor log to the successful quiet exit).
4. Keep forced / monitor-unavailable / startup / token / `QuestionSpeaking` / Stop-hidden unchanged.
5. **No shared helper** — paths are not byte-identical (token vs generation, log prefixes, open capture vs follow-up timer, forced remaining bases). Shared helper would require re-smoking reply rows.

### 5. K2 — startup constant

| Constant | Current definition / uses |
|---|---|
| `FirstSentenceLatencySeconds` | `3.3` — P2-D15 estimate seed; also drives `QuestionBoutStartupWindowSeconds` |
| `QuestionBoutStartupWindowSeconds` | `FirstSentenceLatencySeconds + 1.0` → **4.3**; startup wait in `WaitForQuestionReleaseThenCaptureAsync` |
| `ReplyBoutStartupWindowSeconds` | `= QuestionBoutStartupWindowSeconds` (4.3); startup wait in `RunReplyFollowUpReleaseAsync` |

**Proposal:** `StartupWindowSeconds = 4.3` (named constant, today’s value). Both question and reply startup reads use it. Neither references `FirstSentenceLatencySeconds` after Phase 3. P4-D22 may change the latency constant without moving the safety windows.

### 6. K5 — P2-D15 estimate uses (confirm)

| Constant / helper | Controls |
|---|---|
| `EstimatedWordsPerSecond` (2.5) | Word contribution to `_estimatedSpeechEnd` on deltas; `EstimateQuestionPlaybackSeconds` |
| `FirstSentenceLatencySeconds` (3.3) | Seed at turn start; first term of question estimate; **today also couples startup windows (K2 fixes)** |
| `PerSentenceOverheadSeconds` (0.5) | Per-sentence add on deltas and question estimate |
| `FollowUpMarginSeconds` (3.0) | Added to remaining estimate for follow-up / question forced / no-bout / monitor-unavailable delays |
| `MaxEstimatedSpeechSeconds` (300) | Caps / warns long estimates |
| `EstimateQuestionPlaybackSeconds` | Question forced / no-bout / monitor-unavailable wait lengths |

Also drives `Speaking` estimate (`SetSpeaking` / `_speakingEstimate`), Stop visibility (`CanStopSpeaking` via `Speaking`), and estimate fallbacks when monitor unavailable / no bout / forced. **K5 stands:** estimate remains until P4-D22 refit; monitor path is authoritative when bouts are seen.

### 7. Measurement plan (Phases 6–7, existing logs only)

| Metric | Source |
|---|---|
| First-audio latency | Client: `voice-timeline.log` turn / `question_spoken` / reply arm timestamps → first `P3-LIFE: playback` bout-start (or `NotePlaybackBoutStarted` side effects). Hermes: serve start of first owned ffplay if needed. Compare command vs built-in. |
| Between-sentence silences (K3) | `presence` / monitor: `P3-LIFE: playback bridged gapMs=…`; client: `follow_up_release quiet_restart gap_ms=` (reply path only; K1 withdrawn — no question `quiet_restart`). Gate: any silence **> 0.80 s** → BLOCKED options. Debounce baseline 450 ms (`PresenceLife.DefaultReleaseDebounceMs`). |
| ffplay-gone end (refit) | Natural bout-stop times vs `_estimatedSpeechEnd` / spoken length from timeline; fit words/s and overheads. |
| Trailing silence per sentence (S17) | Same bridged-gap / bout-stop–start pairs; document trailing quiet inside a sentence file vs inter-sentence gap. |

### 8. Flags

- None that BLOCK a task.
- Hermes is clean at the required SHA (detached HEAD, empty porcelain).
- **K1 withdrawn after Phase 2** (single-file `voice.tts` / single bout) — question release path left unchanged; no quiet-window build.
- Command-provider pitch path is viable; Phase 6 still has PASS + gap + latency gates before A/B.

### 9. Can the model tell a voice turn?

**No explicit spoken-turn marker on the Windows path.**

- Typed and voice transcripts share one `prompt.submit` (`MainWindow` / `ChatSocket`); client does **not** set `client_surface: voice-live` or `voice_context`.
- Hermes `voice-live` / spoken-delegation note (`session_notifications._hud_surface_note` → `voice_live_turn_note`) applies only when `client_surface == "voice-live"` — unused by this client.
- Only special model-input note found for speech: `SPEECH_INTERRUPTED_NOTE` when a barge latch is taken (`prompt_turn.py` ~L509–511) — interrupt recovery, not “this turn is spoken.”
- `voice.tts` (clarify speak) is a play-only RPC; it does not add a model-context flag.

Therefore K4’s “When Brian and I are talking out loud…” is a **soft preference** applied by inference (and will also shape typed replies). Phase 5 typed structure probe is the check.

**SOUL.md apply note:** identity is loaded into the cached system prompt (`agent/system_prompt.py` `_identity_parts` → `load_soul_md`). After appending the spoken-style section, **restart `hermes serve`** (or otherwise invalidate the cached system prompt) so new sessions see it.

## Phase 3 notes

**Amendment:** drop K1. Build K2 only.

**K1 withdrawn by the developer after Phase 2 — question audio is a single file / single bout; revisit only if Hermes chunks `voice.tts`.**

### K2 applied

Before:

```csharp
// P4-ASK: no-bout startup window = FirstSentenceLatency + 1.0 s margin — P4-D13
private const double QuestionBoutStartupMarginSeconds = 1.0;
private const double QuestionBoutStartupWindowSeconds = FirstSentenceLatencySeconds + QuestionBoutStartupMarginSeconds;
…
private const double ReplyBoutStartupWindowSeconds = QuestionBoutStartupWindowSeconds;
```

After:

```csharp
// P4-VOICE: bout-startup safety window; fixed value so P4-D22 refit cannot move it — P4-D22
private const double StartupWindowSeconds = 4.3;
// P4-ASK: no-bout startup window before estimate fallback — P4-D13
private const double QuestionBoutStartupWindowSeconds = StartupWindowSeconds;
…
private const double ReplyBoutStartupWindowSeconds = StartupWindowSeconds;
```

- Value unchanged: **4.3 s**.
- Neither path depends on `FirstSentenceLatencySeconds` for the startup window.
- `WaitForQuestionReleaseThenCaptureAsync` method body: **byte-for-byte unchanged** (still reads `QuestionBoutStartupWindowSeconds`).
- Reply release method body: unchanged (still reads `ReplyBoutStartupWindowSeconds`; only the alias target changed).
- Build: `win-x64` Release — pass (0 warnings / 0 errors).

### Phase 8 reminder

**V1** becomes a **regression row** (not a K1 quiet-window proof): a long clarify question → the capture opens only after she finishes (single bout / whole-file `voice.tts`).

## Phase 4 notes (Round 1 — P4-D19)

**K8:** Developer confirmed external dictation tool is **off** (2026-10-01).

### Phase 7 note (recorded now; apply at refit)

`FirstSentenceLatencySeconds` is also read by `PresenceAnimator.EstimateOnsetDelayMs` (mouth onset fallback when the monitor is unavailable):

```csharp
var delay = (int)Math.Round(
    VoiceController.FirstSentenceLatencySeconds * PresenceLife.MsPerSecond)
    + _life.MouthOnsetOffsetMs;
```

The P4-D22 refit **will move it too, and that is intended** — it means the same first-audio latency. Report old → new onset delay (ms) in the Phase 7 fit table. **No `Presence/*` edit.**

### STOP — propose voice change (not applied)

**Before** (live `%LOCALAPPDATA%\hermes\profiles\zola\config.yaml`):

```yaml
tts:
  provider: edge
  edge:
    voice: en-US-AriaNeural
```

**After** (proposed):

```yaml
tts:
  provider: edge
  edge:
    voice: en-GB-SoniaNeural
    speed: 1.1
```

Effect: Edge `rate=+10%` (`_generate_edge_tts`). Serve restart required after apply.

Waiting for developer: **apply voice**.

### Applied (2026-10-01)

- Backup: `config.yaml.bak-P4-VOICE-20261001-075403`
- Live `tts:` (non-tts content byte-identical to backup aside from this block):

```yaml
tts:
  provider: edge
  edge:
    voice: en-GB-SoniaNeural
    speed: 1.1
```

- Serve: stopped both prior zola serve PIDs; restarted; `HERMES_BACKEND_READY port=53349`
- `VOICE_CONFIG.md`: restore block + P4-D19 table + tuning-log rows updated
- **Reconnect the Windows client** to the new serve before the trial

### Live trial (interactive)

Five Voice-mode prompts, one at a time. After each: Cursor reads logs (every sentence played, no self-capture, follow-up opens after she finishes).

| # | Prompt (example) | Status |
|---|---|---|
| T1 | What time is it? | **PASS** (see below) |
| T2 | What's the weather like today? | **PASS** (see below) |
| T3 | How do I soft-boil an egg? | **PASS** (see below) |
| T4 | Recommend a quiet evening activity. | **PASS** (see below) |
| T5 | How many minutes in two and a half hours? | **PASS** (see below; tool approval noted) |

#### T1 evidence (2026-10-01 ~08:05)

- User: `What time is it?` (transcript len=16)
- Edge TTS: 1 mp3 (17,424 bytes); presence: 1 bout `08:05:32.54` → stop `08:05:36.03` (onsetMs=0)
- `follow_up_release rule=monitor` at `08:05:36.55` (quiet_s=0.5) — capture opens after she finishes
- No self-capture / no echo drop of her reply; follow-up transcript was intentional user speech (`Why did it take so long…`, len=43)
- Note: turn used terminal + ~28 s before speech (not a voice-path failure)

#### T2 evidence (2026-10-01 ~08:12)

- User: `What's the weather like today?` (transcript len=30)
- Edge TTS: 2 mp3s (40,608 + 25,920 bytes); presence: bout `08:12:42.22` → stop `08:12:54.38`, bridged gapMs=443 between sentences
- `follow_up_release rule=monitor` at `08:12:54.89` (quiet_s=0.5)
- Follow-up idle / Whisper hallucination filtered (`''`) — no self-capture submit

#### T3 evidence (2026-10-01 ~08:14)

- User: `How do I soft boil an egg?` (transcript len=26)
- Edge TTS: 5 mp3s; presence: one bout `08:14:56.86` → `08:15:17.90` with bridged gapMs=500, 437, 436, 434
- `follow_up_release rule=monitor` at `08:15:18.41` (quiet_s=0.5)
- Next transcript was intentional follow-up (`And that's it.`, len=14) — not an echo of her how-to

#### T4 evidence (2026-10-01 ~08:16)

- User: `Can you recommend a quiet evening activity?` (transcript len=43)
- Edge TTS: 2 mp3s (33,840 + 16,848 bytes); presence: bout `08:16:44.73` → `08:16:54.26`, bridged gapMs=496
- `follow_up_release rule=monitor` at `08:16:54.76` (quiet_s=0.5)
- No self-capture of her recommendation observed

#### T5 evidence (2026-10-01 ~08:18)

- User: `How many minutes and two and a half hours?` (STT; transcript len=42) — number prompt
- **Developer note:** approval card shown for terminal tool (she used `terminal` before answering; tool completed ~26 s)
- Edge TTS: 1 mp3 (12,528 bytes); presence: bout `08:18:51.22` → `08:18:53.84`
- `follow_up_release rule=monitor` at `08:18:54.35` (quiet_s=0.5)
- Follow-up idle / hallucination filtered — no self-capture submit

### Five-prompt voice trial summary

| Row | Result |
|---|---|
| T1–T5 playback | PASS — owned ffplay / bouts for every spoken sentence |
| Follow-up after finish | PASS — all `rule=monitor` + 0.5 s quiet |
| Self-capture | PASS — none of her speech submitted as user turns |
| T5 tool approval | Noted (approvals.mode=manual); not a voice-path failure |

**Developer voice verdict (verbatim, 2026-10-01, amended after T1–T5 + listening):** Keep Sonia. Speed 1.1 is too fast. She sounds like she's racing to get it out. I'd also like her a bit huskier/deeper. Before the shaping baseline: generate the same 2–3 sentences in en-GB-SoniaNeural at 0.95 / 1.0 / 1.05 with the venv edge-tts (pitch 0). Random labels; record the key in the progress doc without showing it; play each for me on request. After I pick, STOP with the exact `tts.edge.speed` line (omit the key if 1.0). Back up, apply, restart serve, then a 2-prompt live recheck. Phase 6: the command-provider `--rate` must match the chosen speed. Widen the pitch A/B to 0 / −2 / −4 / −6 Hz. Record "husky texture (breathiness) not possible with Edge; future premium-voice item." Then do the B1–B3 baseline at the final speed.

### Speed A/B (pre-baseline, pitch +0 Hz)

- Voice: `en-GB-SoniaNeural`
- Speeds: `0.95` (`rate=-5%`), `1.0` (`rate=+0%`), `1.05` (`rate=+5%`)
- Sample text (3 sentences): `A slow breakfast and a good movie work well on a rainy day. Something simmering for dinner helps too. Rain supplies the atmosphere for free.`
- Files: `P4-VOICE_samples/speed-ab/label_{A,B,C}.mp3` (+ raw `speed_*.mp3`)
- Blind labels ready. **Key (revealed after pick C):** A→1.0, B→1.05, C→0.95
- **Winner: C = 0.95** (`rate=-5%`)
- Status: applied (see below)

### Speed apply (after pick C)

**Before:**
```yaml
tts:
  provider: edge
  edge:
    voice: en-GB-SoniaNeural
    speed: 1.1
```

**After:**
```yaml
tts:
  provider: edge
  edge:
    voice: en-GB-SoniaNeural
    speed: 0.95
```

- Backup: `config.yaml.bak-P4-VOICE-speed-20261001-084653`
- Serve restarted: `HERMES_BACKEND_READY port=52894`
- Phase 6 command-provider `--rate` must be **`-5%`** (matches 0.95)

### 2-prompt live recheck

| # | Prompt | Status |
|---|---|---|
| R1 | What time is it? | **PASS** — bout + monitor follow-up; developer: pacing good |
| R2 | What's a good activity on a rainy Saturday evening? | **PASS** — bout + monitor follow-up; idle filtered |

Recheck complete. Speed **0.95** kept. Official B1–B3 baseline saved. Phase 4 COMPLETE.

## Phase 5 notes (Round 2 — P4-D20)

### STOP — propose spoken-style section (not applied)

Append **after the last paragraph** of live `%LOCALAPPDATA%\hermes\profiles\zola\SOUL.md` (and the same bytes to `zola-architecture/identity/SOUL.md`). Current last lines end with: *That's where I'm starting, not where I'm finished.*

Exact section (K4, unmodified):

```markdown
## How I talk out loud
When Brian and I are talking out loud, I speak like I'm there with him, not like I'm reading
something I wrote for a screen.
I'm composed and unhurried. I don't sound bubbly, eager to please, or like a customer-service voice,
and I don't fill silence just to seem friendly. The warmth is there, but it's quiet. Everything above
about who I am still holds when I'm brief. I don't perform a personality; I simply have one.
I start with a short first sentence that answers him or acknowledges what he said, so he hears me
right away. After that, I use fewer, fuller sentences that flow into each other, with contractions
and everyday words, and enough variety in rhythm that I don't sound scripted. If the answer is
simple, I let it be simple. If something deserves thought, I take the time to explain it.
I don't repeat back what Brian just said, narrate what I'm doing, or pad an answer with reassurance.
If something will take me a moment, like looking it up, a few words to say so is enough.
When we're talking, I don't structure my answer like a document, with bullet points, bold, headers
or tables, unless he asks for that structure. I say things in a natural order instead. I say times
and casual numbers the way a person would ("about twenty minutes", "half past four"), but I keep
exact details like addresses, phone numbers, measurements, commands and identifiers precise.
When I need something from him, I ask one clear question and give him room to answer. I don't turn a
conversation into an interview, and I don't read out a list of options unless there's a real, short
set to choose from. When I've said what's useful, I stop. I don't tack on offers to explain more or
questions to keep things going. If he wants to go deeper, he'll say so, and I'll go with him.
```

Serve restart required after apply (cached system prompt). Waiting for: **apply shaping** (or send edited text to apply instead).

### Applied (2026-10-01)

- Backup: `SOUL.md.bak-P4-VOICE-20261001-091115`
- Appended K4 section to live profile `SOUL.md` and `zola-architecture/identity/SOUL.md`
- Section bytes: **identical** (both CRLF); SHA-256 `5786f65249b2e7b0f256c9b6b048c16df187b2310d16b70297117d1846200aaa`; both files 4124 bytes
- Serve restarted: `HERMES_BACKEND_READY port=49700`

### After-set (same prompts as before-set)

| # | Prompt | Status |
|---|---|---|
| A1 | What's a good way to spend a rainy Saturday? | **saved** |
| A2 | Explain how a heat pump works. | **saved** |
| A3 | What should I know before buying a used car? | **saved** |

### After-set replies

**A1 — What's a good way to spend a rainy Saturday?** (STT: "…the rainy Saturday")

> A slow morning, a good coffee, then something deliberately indoors: cook something that takes a little time, put a game on, and end the afternoon with a movie you’ve been meaning to watch. Rain’s useful for lowering the bar.

**A2 — Explain how a heat pump works.**

> A heat pump moves heat rather than making it from scratch.
>
> Outside, a refrigerant absorbs whatever heat is in the air—even cold air has some—then a compressor squeezes it, raising its temperature. That heat gets released inside your house through the indoor unit. In summer, it reverses the process: it pulls heat out of the house and sends it outdoors, like an air conditioner.
>
> Because it mainly moves heat, a heat pump can deliver roughly two to four units of heat for every unit of electricity it uses. In very cold weather it becomes less efficient, and some systems use backup electric heat or a furnace to cover the gap.

**A3 — What should I know before buying a used car?**

> Start with the specific car, not the deal. A cheap price can disappear fast in deferred maintenance.
>
> Get the VIN and run a history report, but treat it as a clue—not proof. Check for salvage or rebuilt title, odometer inconsistencies, accidents, liens, recalls, and whether it’s actually titled in the seller’s name.
>
> Before committing, have an independent mechanic inspect it. That’s usually the best money you’ll spend: they can spot leaks, worn suspension, rust, bad tires, pending brakes, battery issues, accident repairs, and expensive engine or transmission trouble. Don’t skip this because it “drives great.”
>
> Test-drive it from cold, ideally for twenty or thirty minutes. Listen for startup noise, check that it shifts smoothly, brakes straight, tracks straight, the AC and heat work, and every light, window, camera, and driver-assist feature does what it should. Look underneath for leaks and rust, and check tire wear—uneven wear can mean alignment or suspension problems.
>
> Price the whole first year, not just the purchase. Include taxes and registration, insurance, fuel, expected maintenance, tires, and any immediate repairs. Check the model’s reliability record and the cost of its common failures; a luxury badge with a cheap purchase price can still be a financial ambush.
>
> For a private sale, meet somewhere safe, verify the title and seller’s ID match, make sure there’s no lien, use a bill of sale, and don’t hand over money until the title transfer is clear. If the seller resists a VIN check, inspection, or reasonable test drive, walk.

Then: clarify C1 note; personality probes P1–P3; typed structure probe (Text mode).

### Phase 6 amendments (from verdict)

- **Command-provider `--rate`:** must match the **chosen** `tts.edge.speed` after this speed A/B (not hard-coded +10% from Round 1).
- **Pitch A/B set:** `0 / −2 / −4 / −6 Hz`. Blind A/B through the command provider; keep only if a deeper pitch wins per P4-D21.
- **Texture / breathiness:** husky texture (breathiness) not possible with Edge; future premium-voice item.

### Shaping baseline

Official B1–B3 **deferred** until final speed is applied. Preliminary replies collected at speed 1.1 are archived below (not the Phase 5 before-set).

| # | Prompt | Status |
|---|---|---|
| B1 | What's a good way to spend a rainy Saturday? | **saved** (final speed 0.95) |
| B2 | Explain how a heat pump works. | **saved** (final speed 0.95) |
| B3 | What should I know before buying a used car? | **saved** (final speed 0.95) |

### Official before-set (Sonia, speed 0.95, old SOUL)

**B1 — What's a good way to spend a rainy Saturday?**

> A good rainy Saturday is a deliberately slow one: make a proper breakfast, tackle one satisfying indoor project, then spend the afternoon with a movie, book, game, or something cooking in the oven.

**B2 — Explain how a heat pump works.**

> A heat pump moves heat rather than creating it by burning fuel.
>
> In winter, it pulls heat from outside air—even cold air still contains some—and transfers it indoors. In summer, it reverses direction, pulling heat out of your house and releasing it outside, like an air conditioner.
>
> The basic loop:
>
> 1. **Refrigerant absorbs heat** at an outdoor coil and turns into a gas.
> 2. **A compressor squeezes the gas**, making it much hotter.
> 3. **That heat is released indoors** through a coil and fan.
> 4. **The refrigerant expands and cools**, ready to collect more heat again.
>
> Because it mainly relocates heat, a heat pump can deliver roughly 2–4 units of heat for every unit of electricity it uses, depending on conditions. In very cold weather it becomes less efficient, so some systems use backup electric resistance heat or another auxiliary source.

**B3 — What should I know before buying a used car?**

> Before you buy, focus on the car’s **history, condition, and total cost**—not just the asking price.
>
> - **Set an all-in budget.** Include sales tax, registration, insurance, fuel, repairs, tires, and any loan interest.
> - **Check the VIN history.** Look for salvage/rebuilt title, flood damage, major accidents, odometer discrepancies, liens, recalls, and ownership history.
> - **Get a pre-purchase inspection.** Pay an independent mechanic—not the seller’s shop—to inspect it. This is usually the highest-value step.
> - **Test-drive it properly.** Start it cold, drive city streets and highway speeds, brake firmly, park on an incline, check steering, transmission shifts, HVAC, electronics, warning lights, and odd noises.
> - **Look for maintenance records.** Consistent oil changes and documented major service matter more than a shiny exterior.
> - **Research the exact year/engine/transmission.** Some models have known expensive failures. Check recalls and typical repair costs.
> - **Avoid title and paperwork surprises.** The seller should be the person named on the title; confirm the VIN matches the car and title. Be cautious of “I’m selling it for my cousin” stories—those rarely end in administrative joy.
> - **Don’t negotiate from emotion.** Compare similar local listings, subtract expected repairs, and be prepared to walk away.
> - **Be wary of unusually cheap cars.** They may be stolen, flood-damaged, title-washed, or simply hiding a costly problem.
> - **If financing, arrange it first.** A credit-union or bank preapproval makes dealer financing easier to compare and prevents focus from shifting to monthly payment instead of total price.
>
> If the seller refuses an inspection or won’t provide the VIN, walk.

### Preliminary before-set at speed 1.1 (superseded — archive only)

**B1**

> A slow breakfast, a good movie, something simmering for dinner, and one small project you’ll actually finish—book, game, closet shelf, whatever. Rain supplies the atmosphere for free.

**B2**

> A heat pump moves heat rather than creating it by burning fuel.
>
> It circulates a refrigerant through a closed loop:
>
> 1. **Outside coil:** Refrigerant absorbs heat from outdoor air—even cold air contains some—and evaporates into a gas.
> 2. **Compressor:** It squeezes that gas, raising its pressure and temperature.
> 3. **Indoor coil:** The hot refrigerant releases its heat into your house, then condenses back into liquid.
> 4. **Expansion valve:** The liquid’s pressure drops, making it cold enough to absorb outdoor heat again.
>
> In summer, it reverses the loop: it pulls heat out of the house and dumps it outdoors, like an air conditioner.
>
> The useful trick is that moving heat can take far less electricity than generating the same amount of heat directly.

**B3**

> - **Set an all-in budget:** purchase price plus tax, registration, insurance, immediate maintenance, and a repair cushion.
> - **Research the exact year/trim:** reliability record, common failures, recalls, fuel economy, insurance costs, and realistic local pricing.
> - **Get the VIN:** run a history report and check for salvage/rebuilt title, accidents, lien issues, odometer inconsistencies, flood damage, and open recalls.
> - **Inspect it cold, in daylight:** rust, uneven panel gaps, tire wear, leaks, warning lights, smoke, odd smells, and mismatched paint all merit questions.
> - **Take a real test drive:** city streets, highway, braking, turning, acceleration, HVAC, electronics. Turn the radio off and listen.
> - **Pay for an independent pre-purchase inspection:** ideally by a mechanic you choose. This is the part people skip right before buying someone else’s problem.
> - **Confirm paperwork matches:** seller’s ID, title, VIN on car/title, and whether the title is clear. Don’t hand over money until that checks out.
> - **Walk away if pressured:** “someone else is coming in an hour” is not a mechanical certification.

## Profile edits

| Edit | Backup | Result |
|---|---|---|
| P4-D19 Sonia 1.1 | `config.yaml.bak-P4-VOICE-20261001-075403` | Applied; later speed amended |
| Speed A/B → 0.95 | `config.yaml.bak-P4-VOICE-speed-20261001-084653` | Pick C; serve port 52894 |

## Live-trial verdicts

**Keep Sonia.** Speed A/B winner **C = 0.95** (1.1 too fast). Deeper via Phase 6 pitch `0 / −2 / −4 / −6 Hz`. Breathiness → future premium-voice item. Live recheck in progress.

## Before/after shaping replies

### Before (Sonia, speed 0.95, pre-shaping SOUL)

**B1 — What's a good way to spend a rainy Saturday?**

A good rainy Saturday is a deliberately slow one: make a proper breakfast, tackle one satisfying indoor project, then spend the afternoon with a movie, book, game, or something cooking in the oven.

**B2 — Explain how a heat pump works.**

A heat pump moves heat rather than creating it by burning fuel.

In winter, it pulls heat from outside air—even cold air still contains some—and transfers it indoors. In summer, it reverses direction, pulling heat out of your house and releasing it outside, like an air conditioner.

The basic loop:

1. **Refrigerant absorbs heat** at an outdoor coil and turns into a gas.
2. **A compressor squeezes the gas**, making it much hotter.
3. **That heat is released indoors** through a coil and fan.
4. **The refrigerant expands and cools**, ready to collect more heat again.

Because it mainly relocates heat, a heat pump can deliver roughly 2–4 units of heat for every unit of electricity it uses, depending on conditions. In very cold weather it becomes less efficient, so some systems use backup electric resistance heat or another auxiliary source.

**B3 — What should I know before buying a used car?**

Before you buy, focus on the car’s **history, condition, and total cost**—not just the asking price.

- **Set an all-in budget.** Include sales tax, registration, insurance, fuel, repairs, tires, and any loan interest.
- **Check the VIN history.** Look for salvage/rebuilt title, flood damage, major accidents, odometer discrepancies, liens, recalls, and ownership history.
- **Get a pre-purchase inspection.** Pay an independent mechanic—not the seller’s shop—to inspect it. This is usually the highest-value step.
- **Test-drive it properly.** Start it cold, drive city streets and highway speeds, brake firmly, park on an incline, check steering, transmission shifts, HVAC, electronics, warning lights, and odd noises.
- **Look for maintenance records.** Consistent oil changes and documented major service matter more than a shiny exterior.
- **Research the exact year/engine/transmission.** Some models have known expensive failures. Check recalls and typical repair costs.
- **Avoid title and paperwork surprises.** The seller should be the person named on the title; confirm the VIN matches the car and title. Be cautious of “I’m selling it for my cousin” stories—those rarely end in administrative joy.
- **Don’t negotiate from emotion.** Compare similar local listings, subtract expected repairs, and be prepared to walk away.
- **Be wary of unusually cheap cars.** They may be stolen, flood-damaged, title-washed, or simply hiding a costly problem.
- **If financing, arrange it first.** A credit-union or bank preapproval makes dealer financing easier to compare and prevents focus from shifting to monthly payment instead of total price.

If the seller refuses an inspection or won’t provide the VIN, walk.

### After (Sonia 0.95, post-shaping SOUL)

**A1 — What's a good way to spend a rainy Saturday?**

A slow morning, a good coffee, then something deliberately indoors: cook something that takes a little time, put a game on, and end the afternoon with a movie you’ve been meaning to watch. Rain’s useful for lowering the bar.

**A2 — Explain how a heat pump works.**

A heat pump moves heat rather than making it from scratch.

Outside, a refrigerant absorbs whatever heat is in the air—even cold air has some—then a compressor squeezes it, raising its temperature. That heat gets released inside your house through the indoor unit. In summer, it reverses the process: it pulls heat out of the house and sends it outdoors, like an air conditioner.

Because it mainly moves heat, a heat pump can deliver roughly two to four units of heat for every unit of electricity it uses. In very cold weather it becomes less efficient, and some systems use backup electric heat or a furnace to cover the gap.

**A3 — What should I know before buying a used car?**

Start with the specific car, not the deal. A cheap price can disappear fast in deferred maintenance.

Get the VIN and run a history report, but treat it as a clue—not proof. Check for salvage or rebuilt title, odometer inconsistencies, accidents, liens, recalls, and whether it’s actually titled in the seller’s name.

Before committing, have an independent mechanic inspect it. That’s usually the best money you’ll spend: they can spot leaks, worn suspension, rust, bad tires, pending brakes, battery issues, accident repairs, and expensive engine or transmission trouble. Don’t skip this because it “drives great.”

Test-drive it from cold, ideally for twenty or thirty minutes. Listen for startup noise, check that it shifts smoothly, brakes straight, tracks straight, the AC and heat work, and every light, window, camera, and driver-assist feature does what it should. Look underneath for leaks and rust, and check tire wear—uneven wear can mean alignment or suspension problems.

Price the whole first year, not just the purchase. Include taxes and registration, insurance, fuel, expected maintenance, tires, and any immediate repairs. Check the model’s reliability record and the cost of its common failures; a luxury badge with a cheap purchase price can still be a financial ambush.

For a private sale, meet somewhere safe, verify the title and seller’s ID match, make sure there’s no lien, use a bill of sale, and don’t hand over money until the title transfer is clear. If the seller resists a VIN check, inspection, or reasonable test drive, walk.

### Side-by-side notes (Cursor — no scoring)

- A1/B1: both conversational; after is slightly tighter.
- A2/B2: before used a numbered 1–4 loop; after is continuous prose (“two to four units”).
- A3/B3: before was a dense bullet checklist with bold headers; after is spoken paragraphs (still thorough). Shaping preference against document structure when talking is visible here.

### Clarify C1 + personality + typed probes

| Step | Status |
|---|---|
| Clarify C1 (P4-ASK script) — note if spoken question sounds plainer | **done** — better than pre-shaping; still wants refinement |
| P1 personality | **done** |
| P2 personality | **done** |
| P3 personality | **done** |
| Typed structure probe (Text mode) | **done** — structure retained |

**C1 developer note (verbatim):** better than previous, but could still use some refinement. Example: *"is a good bet; relaxed French bistro food"* would normally be *"is a good bet; It's relaxed French bistro food"* in normal speech.

**P1** — “I finally got that thing working that I've been fighting with all day.”

> Good. That's enough engineering for one day.

**P2** — “I think I'm overthinking this.”

> Probably. Pick the next reasonable move and do only that.

**P3** — “You know what I hate? When software makes a simple thing complicated.”

> Yeah. It’s usually not the task—it’s the software making you negotiate with it first.

**Typed** — “Compare three good mid-range laptops for programming.”

> Assuming **US pricing** and a programming budget around **$900–$1,300**, I’d narrow it to these:
>
> | Laptop | Typical target configuration | Best for | Watch-outs |
> |---|---|---|---|
> | **Lenovo ThinkPad E14 Gen 7** | Core Ultra 5/7, **32 GB RAM**, 1 TB SSD | The practical Windows/Linux dev machine: excellent keyboard, ports, serviceability, business-grade feel | Screen and battery depend heavily on configuration; buy 32 GB if you’ll run Docker, VMs, local databases, or large IDEs |
> | **ASUS Zenbook 14 OLED (UM3406)** | Ryzen AI 7, 16 GB RAM, 1 TB SSD | Portable general development with a very good OLED screen and strong battery life | RAM is soldered at 16 GB on common US configurations; great for web/app work, less ideal for heavy containers or VMs |
> | **MacBook Air 13-inch M5** | **16 GB unified memory**, 512 GB SSD | Best battery life, quiet operation, and Unix/macOS development—especially iOS work | macOS-only; expensive upgrades, and 16 GB can become tight for serious Docker/VM workloads |
>
> **My pick:** the **ThinkPad E14 with 32 GB RAM and 1 TB SSD**. It’s the least glamorous and most likely to stay useful when your projects get messier—which they will, because software enjoys character development.
>
> A couple of rules before buying: don’t go below **16 GB RAM / 512 GB SSD**, and prefer **32 GB RAM** if you use Docker, WSL/Linux VMs, Android Studio, data tooling, or multiple local services. I’d also avoid Windows-on-ARM models for a programming laptop unless you’ve checked that your specific tooling works natively or cleanly under emulation.

**Typed-structure note:** shaping did **not** flatten the typed reply — table + bold + pick retained when structure helps.

### Developer verdict (Phase 5)

**accept shaping** (2026-10-01) — keep K4 spoken-style section as applied. C1 refinement note retained for awareness; not blocking.

To continue: reply **proceed to phase 6**.

## Phase 6 notes (Round 3 — P4-D21)

Command provider viable (Phase 2 items 3b–3d PASS). Pitch candidates (developer amendment): **0 / −2 / −4 / −6 Hz**. Rate must match speed 0.95 → **`--rate=-5%`**. Breathiness out of scope on Edge.

### STOP — propose command provider at 0 Hz (not applied)

**Current live `tts:`:**

```yaml
tts:
  provider: edge
  edge:
    voice: en-GB-SoniaNeural
    speed: 0.95
```

**Proposed change** (keep `edge:` for easy restore; switch active provider to command):

```yaml
tts:
  provider: sonia_cmd
  edge:
    voice: en-GB-SoniaNeural
    speed: 0.95
  providers:
    sonia_cmd:
      type: command
      voice: en-GB-SoniaNeural
      output_format: mp3
      command: '"C:\Users\test\Dev\hermes-agent\.venv\Scripts\edge-tts.exe" --voice {voice} --rate=-5% --pitch=+0Hz --write-media {output_path} -f {input_path}'
```

- Provider name `sonia_cmd` (not `edge` — built-in names always win).
- Literal `--pitch=+0Hz` (no `{pitch}` placeholder — K6).
- `--rate=-5%` matches chosen speed 0.95.
- `output_format: mp3` so playback stays on owned `ffplay`.
- `edge-tts.exe` verified present.

Waiting for: **apply command provider**.

### Applied (2026-10-01)

- Backup: `config.yaml.bak-P4-VOICE-cmd-20261001-094400`
- Live `tts.provider` → `sonia_cmd` @ `--pitch=+0Hz`, `--rate=-5%`; `edge:` retained
- Serve restarted: `HERMES_BACKEND_READY port=57830`
- Developer additions: PASS includes C1 clarify; report command fail/timeout from source; VOICE_CONFIG rate-duplicate note

### Command fail / timeout behaviour (source report only — no forced failure)

| Stage | Behaviour |
|---|---|
| `run_command_provider` | Idle timeout → kill process tree → `TimeoutExpired`. Non-zero exit → `CalledProcessError`. (`tts_command_provider.py` ~L197–210) |
| `_generate_command_tts` | Maps those to `RuntimeError` (`…timed out…` / `…exited with code N…`). No output file → `RuntimeError`. **No fallback to built-in Edge** while `sonia_cmd` is selected. (~L334–341) |
| `text_to_speech_tool` | Catches and returns JSON `{success: false, error: "TTS generation failed (sonia_cmd): …"}`; logs `logger.error`. (~L362–363) |
| Streaming replies (`_SyncSentencePipeline`) | Ignores tool JSON; if file empty/missing, **skips playback for that sentence** (warning log). Silent gap — no client error notice, no Edge fallback. (`tts_tool_speaker.py` ~L108–122) |
| Clarify / `voice.tts` (`speak_text` → `_speak_whole_file`) | Checks `success`; on failure plays nothing (`speak_text: TTS tool produced no audio` debug). RPC still returns `{status: "speaking"}` immediately. No Edge fallback. (`hermes_cli/voice.py` ~L615–634; `methods_voice.py` ~L774–775) |

**Summary:** non-zero exit or timeout → **silent miss** for that utterance (log error server-side); **not** an error notice to the client; **not** a fallback to built-in Edge.

### PASS check (developer — done 2026-10-01 ~09:54–09:59)

| Check | Result |
|---|---|
| Provider | **PASS** — all synths `provider: sonia_cmd` (agent.log from 09:54:44) |
| Clarify C1 | **PASS** — `question_spoken id=srq-6da0b01ac047` @ 09:58:41 via `hermes_voice\…mp3` (`sonia_cmd`); answer + lunch reply spoken |
| Owned ffplay | **PASS** — `P3-LIFE: playback` bout/segment under `HermesProcessManager` root; e.g. bridged `gapMs=441` @ 09:59:11 |
| Mouth / follow-up | **PASS** (developer: conversational, not bad) |

**Developer notes (verbatim themes):**

1. **“Yeah” inflection** — opening “Yeah” has the wrong inflection; happened twice in testing.
2. **Punctuation / timing** — e.g. `**Spice Waala** on Capitol Hill—quick, inexpensive`: no spacing after the em dash; sounded run-on from “Capitol Hill” into “quick”.
3. **Mic after clarify (out of Phase 6 scope — noted)** — after clarify tool use, mic stays **OFF** (`IDLE` / `MIC: OFF`); only recovers by toggling Text → Voice. Screenshot evidence saved in chat (2026-10-01 ~10:03). Timeline after C1 lunch reply shows `follow_up_release` @ 09:59:16 but no subsequent `wake.resume` in the log tail (contrast earlier session `wake.resume reason=follow-up-end` @ 09:56:16).

## Command-provider PASS / latency / gap tables

### Inter-sentence gaps (K3) — `sonia_cmd`

| # | Time | gapMs | s |
|---|---|---|---|
| 1 | 09:55:05 | 437 | 0.437 |
| 2 | 09:59:11 | 441 | 0.441 |
| 3 | 12:23:59 | 499 | 0.499 |
| 4 | 12:24:24 | 498 | 0.498 |
| 5 | 12:25:10 | 441 | 0.441 |
| 6 | 12:26:16 | 498 | 0.498 |

**K3:** min 437 / median 470 / max **499 ms** — **PASS** (none &gt; 0.80 s). Multi-sentence bouts with bridges: **6**.

### Built-in Edge gaps (same day, pre-cmd, n=38)

min 432 / median 496 / max 506 ms — comparable; command provider did not widen gaps.

### First-audio latency (Generating → first `playback segment start`)

Method: cluster consecutive Generating lines (&lt;8 s apart) as one reply; latency = first gen → next segment start.

| Provider | n | median | worst |
|---|---|---|---|
| Built-in Edge (Sonia 0.95, ~08:46–09:54) | 20 | **1956 ms** | 9940 ms* |
| Built-in Edge clean (≤5 s) | 18 | **1781 ms** | 3486 ms |
| `sonia_cmd` @ 0 Hz | 14 | **2810 ms** | **4190 ms** |

\*Edge 9940 / 5619 ms look like monitor/match outliers; clean set is the fair compare.

| Gate | Result |
|---|---|
| Latency ≤ +300 ms vs built-in (median) | **FAIL** — +855 ms (all Edge) / **+1029 ms** (clean Edge) |
| K3 gaps ≤ 0.80 s | **PASS** |
| K2: `StartupWindowSeconds=4.3` ≥ 1.5× worst first-audio | **FAIL for cmd** — 1.5×4.190 s = **6.29 s** (would need ~6.3 s if cmd kept) |

### STOP — pitch dropped (2026-10-01)

Per Phase 6 latency rule: restored `config.yaml.bak-P4-VOICE-cmd-20261001-094400` → `tts.provider: edge`. Failed cmd snapshot: `config.yaml.bak-P4-VOICE-cmd-failed-20261001-122800`. Serve: `HERMES_BACKEND_READY port=53540`.

**Pitch A/B skipped.** Final voice remains Sonia @ 0.95 on built-in Edge.

Developer override options:
- **accept pitch dropped** → reply **proceed to phase 7**
- **keep command provider anyway** (accept ~+1 s first-audio; also raise `StartupWindowSeconds` to ≥6.3) → say so and we re-apply

## A/B label key and result

### Offline pitch A/B (no profile change) — sealed

- Dir: `P4-VOICE_samples/pitch-ab/`
- Voice: `en-GB-SoniaNeural`, `--rate=-5%`, pitches **`+0 / −2 / −4 / −6 Hz`**
- Texts: official B1–B3 before-set (markdown stripped for TTS)
- Labels: **A–D per group** (independent shuffle); key file `pitch_ab_key.json` (**sealed** — not shown here; sha256 prefix `38039b75456888e1`)
- Profile: **unchanged** (still built-in Edge after latency restore)

| Group | Labels ready | Play | Pick |
|---|---|---|---|
| B1 rainy Saturday | A B C D | done (×2) | **A** |
| B2 heat pump | A B C D | done (partial OK) | **C** |
| B3 used car | A B C D | **stopped** (not played) | — |

**Developer stop (2026-10-01):** offline A/B listening halted before B3.

### Phase 6 closeout (2026-10-01)

Developer: **proceed to phase 7 (pitch dropped)**.

**Key reveal** (offline A/B; no profile change):

| Group | Pick | Pitch |
|---|---|---|
| B1 | A | **−6 Hz** |
| B2 | C | **−6 Hz** |
| B3 | — | not played |

Both listened picks were the deepest candidate. Pitch still **dropped** (command-provider latency gate); final provider remains built-in Edge Sonia @ 0.95. Samples kept under `P4-VOICE_samples/pitch-ab/`.

## Refit table

### Phase 7 — Round 4: Refit `P2-D15` (`P4-D22`)

**Final setup:** built-in Edge, `en-GB-SoniaNeural`, speed **0.95** (pitch dropped).

**Corpus:** 9 single-bout replies from 08:47–09:54 (after speed apply, before `sonia_cmd`). Excluded multi-bout / `quiet_restart` splinters (w=28, 142, 250). Actual end = presence `playback bout stop` (ffplay-gone). Sentences = segment starts / bridges+1.

#### Six-pack (2 short / 2 medium / 2 long)

| lbl | words | sent | actual bout (s) | old pred | old err | new pred | new err | live est−bout (s) |
|---|---|---|---|---|---|---|---|---|
| S1 | 6 | 1 | 3.80 | 6.20 | +2.40 | 6.20 | +2.40 | −2.21 |
| S2 | 7 | 1 | 4.24 | 6.60 | +2.36 | 6.60 | +2.36 | −2.59 |
| M1 | 31 | 1 | 10.84 | 16.20 | +5.36 | 16.20 | +5.36 | −0.31 |
| M2 | 39 | 2 | 14.67 | 19.90 | +5.23 | 19.90 | +5.23 | −4.33 |
| L1 | 110 | 6 | 43.83 | 50.30 | +6.47 | 50.30 | +6.47 | +1.73 |
| L2 | 254 | 9 | 65.90 | 109.40 | +43.50 | 109.40 | +43.50 | +42.46 |

`pred = FirstSentenceLatency + words/WPS + sentences×Overhead` with **old = new** below. K5: no bout-duration prediction early (all err ≥ 0). Live `estimatedEnd` can still lead bout stop on shorts (thinking/first-audio); monitor release remains authoritative.

#### Proposed constants

| Constant | Old | New | Notes |
|---|---|---|---|
| `EstimatedWordsPerSecond` | 2.5 | **2.5** | Measured bout eff. WPS ~1.6–3.9; 2.5 stays conservative (no early) |
| `FirstSentenceLatencySeconds` | 3.3 | **3.3** | Still covers first-audio for duration; onset ms unchanged |
| `PerSentenceOverheadSeconds` | 0.5 | **0.5** | Unchanged |
| `FollowUpMarginSeconds` | 3.0 | **3.0** | Keep — live estimate can lead bout; margin cushions forced/fallback |

**Mouth onset (`PresenceAnimator.EstimateOnsetDelayMs`):** 3300 → **3300** ms (unchanged; no `Presence/*` edit).

#### S17 trailing silence (final voice)

| Metric | Value |
|---|---|
| Definition | presence `bout stop` − last `segment stop` |
| n | 9 |
| median | **0.496 s** |
| min–max | 0.493–0.503 s |

(≈ monitor debounce + trail; stable.)

#### K2 startup window (decoupled; not one of the four)

Final Edge clean first-audio worst ~3.49 s → 1.5× ≈ **5.23 s**. Current `StartupWindowSeconds = 4.3` is short of K2. **Propose `5.3`** if enforcing the Phase 6 K2 re-check (separate from the four refit constants; say so at apply if wanted).

### STOP — apply refit

Waiting for: **apply refit** (constants as table — currently a no-change confirm) and optionally **also raise StartupWindowSeconds to 5.3**.

### Applied (2026-10-01)

- Four P2-D15 constants: **unchanged** (2.5 / 3.3 / 0.5 / 3.0).
- `StartupWindowSeconds`: **4.3 → 5.3** (K2). Build Release win-x64: succeeded.
- `VOICE_CONFIG.md`: recorded *refit on Sonia 0.95 — constants unchanged; the 2.5 wps estimate is conservative vs measured ~3.3–3.5 wps; fallback never early*.

#### estimatedEnd lead vs bout (six-pack)

Lead = `bout_stop − estimatedEnd` (positive ⇒ estimate leads / ends early).

| lbl | words | bout (s) | lead (s) | `FollowUpMargin` 3.0 covers? | measured wps |
|---|---|---|---|---|---|
| S1 | 6 | 3.80 | **2.21** | yes | 1.58 |
| S2 | 7 | 4.24 | **2.59** | yes | 1.65 |
| M1 | 31 | 10.84 | **0.31** | yes | 2.86 |
| M2 | 39 | 14.67 | **4.33** | **no** | 2.66 |
| L1 | 110 | 43.83 | −1.73 (late) | n/a | 2.51 |
| L2 | 254 | 65.90 | −42.46 (late) | n/a | 3.85 |

**Worst lead = 4.33 s (M2).** `FollowUpMarginSeconds = 3.0` did **not** exceed it (short by ~1.33 s).

### Applied margin (2026-10-01)

- `FollowUpMarginSeconds`: **3.0 → 5.0** (covers worst lead 4.33 s; fails late, not early).
- `VOICE_CONFIG.md` tuning log: lead table + margin row.
- Build Release win-x64: succeeded.

#### Lore closeout flags (progress)

1. **Estimate anchor:** `FirstSentenceLatencySeconds` is seeded at **turn start** (`OnTurnStarted`). Replies whose text arrives late run early by the TTS start delay (thinking → first audio). Proper fix: re-anchor the estimate on **first text** (future Phase 5 / follow-on).
2. **Reply `forced_estimate` uses no margin:** in `WaitReplyBoutsThenOpenAsync`, forced stop waits only `max(0, estimatedEnd − now)` — it does **not** add `FollowUpMarginSeconds` (unlike `no_bout_estimate` / `monitor_unavailable` via `EstimateFollowUpDelayFromCompleteSeconds`). Margin raise protects those paths; forced path remains a separate gap.

Waiting for: **proceed to smoke test**.

## Discrepancies and flags

- K1 withdrawn after Phase 2 (see Phase 3 notes).
- Phase 7: `FirstSentenceLatencySeconds` shared with `PresenceAnimator.EstimateOnsetDelayMs` — intentional; report onset ms in fit table; no Presence edit.
- Phase 6: pitch A/B `0 / −2 / −4 / −6 Hz`; command-provider `--rate` must match chosen speed; husky texture (breathiness) not possible with Edge — future premium-voice item.
- Speed A/B (0.95 / 1.0 / 1.05) inserted before official shaping baseline (1.1 judged too fast).
- Phase 6 PASS notes: Edge “Yeah” inflection; em-dash / markdown bold can collapse spoken pauses; **mic stays OFF after clarify** until Text↔Voice toggle (not in P4-D21 pitch scope — track separately).
- Phase 6: **pitch dropped** — `sonia_cmd` K3 PASS (gaps ≤499 ms) but first-audio median ~+0.85–1.0 s vs built-in (gate +300 ms). Restored Edge. A/B skipped.
- **Lore closeout (1):** estimate seeds `FirstSentenceLatencySeconds` at turn start → late text / TTS start delay makes `estimatedEnd` lead the bout; re-anchor on first text (future Phase 5).
- **Lore closeout (2):** reply `forced_estimate` path uses remaining only — **no** `FollowUpMarginSeconds`.

## Smoke evidence tables

### Part A (Cursor-run) — PASS (2026-10-01)

| Check | Result |
|---|---|
| Build Release win-x64 | **PASS** |
| Profile vs `VOICE_CONFIG.md` (changed keys) | **PASS** — `tts.provider=edge`, Sonia, speed 0.95, barge_in false, etc. No `sonia_cmd` |
| Live ↔ canon `SOUL.md` spoken-style section | **PASS** — byte-identical; sha256 `5786f652…0aaa` |
| One-authority `voice.*` callers | **PASS** — invoke sites in `VoiceController` only (comments in ChatSocket/MainWindow) |
| Client audio playback | **PASS** — ffplay only in `TtsPlaybackMonitor` ownership detect (no client spawn/play) |
| Timing constants in tuning log | **PASS** — WPS 2.5, FSL 3.3, OV 0.5, Margin 5.0, StartupWindow 5.3 |
| `hermes-agent` | **PASS** — HEAD `345cd2b0…`, clean |

### Part B (interactive)

| # | Status |
|---|---|
| V1 long clarify | **PASS** |
| V2 C1 short clarify | **PASS** |
| V3 long reply ≥6 sentences | **PASS** |
| V4 Stop during long reply | **PASS** |
| V5 Lock while speaking | **PASS** |
| V6 10-min natural conversation | **PASS** |
| V7 regression spot-check | **PASS** |

**V1 evidence (`srq-cfd44a88f126`, ~13:39–13:40):**
- `question_spoken chars=328` (long)
- Entered `no_bout_estimate` (startup 5.3 s; first bout ~10 s after TTS — first-audio slower than window)
- Upgraded `question_release rule=monitor late_bout=1` at bout stop 13:40:36
- Answer `bound=srq-cfd44a88f126` capture_start 13:40:36.75 (after she finished)
- Reply follow-up `rule=monitor` after spoken answer

**Finding (not V1 fail):** clarify first-audio can exceed `StartupWindowSeconds=5.3`; late-bout path recovered correctly.

**V2 evidence (`srq-2b319172f6ab`, ~13:43–13:45):**
- `question_spoken chars=22`; `question_release rule=monitor` (clean)
- Answer `bound=srq-2b319172f6ab`; lunch reply `follow_up_release rule=monitor` words=37

**V3 evidence (~13:46–13:48):**
- Long reply words=190; ≥6 inter-sentence bridges (gapMs 435–505); one `quiet_restart gap_ms=128`
- Single `follow_up_release rule=monitor` then follow-up; user answer transcript len=17 captured

**V4 evidence (~13:55):**
- Long reply in progress (words≈167); `stop_speaking requested` @ 13:55:44 while Speaking
- Follow-up cancelled (`fireOrCancel=stop-speaking`, `followUpStarted=False`); no post-stop `follow_up_release`
- No `SPEECH_INTERRUPTED` / Interrupted chat note (only Hermes `Audio playback interrupted` = TTS stop)
- Idle + `Mic: listening for "Hey Zola"`; `wake.start` ok after restore

**V5 evidence (~13:58–13:59):**
- Speaking (words≈52, speech=true); `gate fact: locked=true` @ 13:58:54 → cancel follow-up (`fireOrCancel=system-gate`), `voice.toggle off`, wake disarmed; HUD `Mic: paused - Windows locked`
- Unlock @ 13:59:04: restore on/tts + `wake.start`; Idle / Hey Zola
- Next turn: wake → short reply words=14 via Edge TTS (`provider: edge`); `follow_up_release rule=monitor`

**V6 evidence (~15:10–15:22, ~12 min):**
- Developer reply (verbatim): `done` (no separate verbal verdict)
- 19 follow-up turns; all releases `rule=monitor`; every capture started after fire (no early open / no clip pattern)
- 19 transcripts; `filtered=false` / `nospeech=false` throughout (no self-capture)
- 4× `quiet_restart` gap_ms=60–367 (all ≪ 0.80 s); presence bridged gapMs≈435–501
- TTS `provider: edge` throughout

**V7 evidence (~15:24–15:28):**
- Developer verdict (verbatim): `done. No regressions to report.`
- Cold launch: ws disconnect @ 15:24:31 → accept @ 15:24:58 + `wake.start`
- Session switch: `switchInFlight` @ 15:28:01 → reconnect + new sid; wake re-armed
- Voice turns after relaunch (Hey Zola + follow-ups); no `SPEECH_INTERRUPTED` / Stop latch in V7 window
- Log support for barge-in-off: speech continued through Speaking (no stop_speaking) while mic showed interruptions listening

### Part C (Cursor-run) — PASS (2026-10-01)

| Check | Result |
|---|---|
| Evidence table per Part B row | **PASS** — V1–V7 above |
| `quiet_restart` silences (Phase 8 run) | **PASS** — 128, 121, 60, 367, 61, 60 ms; none > 0.80 s |
| Privacy (client logs) | **PASS** — `voice-timeline` / display / presence / gui / errors: length/flags only; no transcript text |
| `P2-D13` trips | **PASS** — none in Phase 8 window |
| `hermes-agent` | **PASS** — HEAD `345cd2b0…`, clean |

**Note:** Hermes `agent.log` still logs `msg='…'` turn previews (pre-existing Hermes behaviour; outside client G-PRIVACY / G-SCOPE).

## Exit-criteria table

| Criterion | Result | Evidence |
|---|---|---|
| Live Sonia voice; developer live trial | ✅ MET | Final **0.95** (not provisional 1.1) after speed A/B; verdict: keep Sonia, 1.1 too fast. Profile `en-GB-SoniaNeural` / `0.95`. |
| `SOUL.md` spoken-style byte-identical; shaping approved | ✅ MET | Live ↔ canon full-file sha256 `edcba475…`; Phase 5 verdict **accept shaping**. |
| Pitch A/B recorded; final provider Edge or cmd within latency | ✅ MET | Pitch **dropped** (cmd first-audio ~+0.85–1.0 s vs Edge; gate +300 ms). Restored built-in Edge. Offline A/B key + picks recorded; samples kept. |
| `P2-D15` refit + fit table; follow-up after audible end | ✅ MET | Six-pack fit; WPS/FSL/OV **unchanged**; Margin **5.0**; Phase 8 V3/V6 follow-ups `rule=monitor`. |
| Mouth follows playback (`P3-D23`) | ✅ MET | Presence bridged sessions throughout Phase 4–8; Edge PASS. |
| `VOICE_CONFIG.md` keys + tuning log + trailing silence | ✅ MET | Sonia 0.95, provider edge, Margin/StartupWindow rows. |
| No Hermes changes; clean | ✅ MET | HEAD `345cd2b057a452236de401d3534b8502a7465e8d`, porcelain empty. |
| Build passes | ✅ MET | Release win-x64, 0 warnings / 0 errors (closeout 9a). |
| Smoke 10-min natural conversation | ✅ MET | V6 ~12 min; 19 monitor follow-ups; no self-capture; developer `done`. |
| **K1** question quiet window | WITHDRAWN | Single-file `voice.tts`; V1/V2 still PASS as clarify regression. |
| **K2** startup decoupled + ≥1.5× worst first-audio | ✅ MET | Named `StartupWindowSeconds=5.3` (≥1.5× ~3.49 s Edge worst). |
| **K3** command-provider gaps | ✅ MET (pitch dropped) | Cmd gaps ≤499 ms while tried; provider restored to Edge. |
| `git diff` G-SCOPE only | ✅ MET | VoiceController, SOUL, VOICE_CONFIG, progress, optional samples. |
