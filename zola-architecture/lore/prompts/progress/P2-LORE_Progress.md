# P2-LORE Progress — Phase 2 Combined Smoke Pass and Lore Closeout

## Branch

- Branch: `phase2-lore-closeout`
- Base SHA: `8572ac82a1ac9a52306c2da7119463f58d906231` (`docs: record P2-WAKE merge SHA on main`)
- Plan: `PHASE2_BUILD_PLAN.md` v1.1
- Prompt: P2-LORE v1.0

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Branch and Progress Document | COMPLETE |
| 2 | Combined Smoke Pass on `main` (HUMAN-RUN) | COMPLETE |
| 3 | Draft Lore Edits (no commit) | COMPLETE |
| 4 | Closeout | COMPLETE |

## Guardrails summary

- **G-SCOPE:** Combined smoke on built `main`, then lore closeout only. Editable files: `ROADMAP.md`, `DESIGN_DECISIONS.md`, `OPEN_QUESTIONS.md`, Master Plan Tier 1 Windows Track note, this progress doc. No source, config, client, or Hermes edits. Smoke failure is BLOCKED; nothing is fixed here.
- **G-ARCH:** Build plan and the three track progress docs are the source of truth for what happened. Lore must match them. If they conflict, stop and flag; do not choose.
- **G-PATTERN:** Read each lore file in full before editing. Match heading style, ID format, and tone. Do not restructure except the listed corrections.
- **G-RECONCILE:** Check each lore file for existing Phase 2 entries before adding any. Reconcile rather than duplicate.
- **G-STOP:** Stop after each phase and wait for that phase's exact proceed message.
- **G-CLOSEOUT:** Closeout begins only on "proceed to closeout".
- **G-NO-CROSS-SCOPE:** Android Zola and Ava are out of scope. Nothing from them is cited in lore.

## Combined smoke results

Client launched for HUMAN-RUN. Awaiting developer pass/fail.

- Built `windows-client/Zola.Client/Zola.Client.csproj` from `8572ac82` (same tree as `main`): 0 warnings, 0 errors.
- Stopped leftover Zola `hermes serve` (pids 14084 / 19668, started 2026-09-23 16:29, parent gone).
- Fresh shell PATH (Machine + User). `ffplay` = `%LOCALAPPDATA%\Microsoft\WinGet\Links\ffplay.exe`.
- Client PID `2728` spawned serve `17444` / `23668`. Chrome: `Session ready.` and `Mic: listening for "Hey Zola"`.
- Required setup (developer): lid open, mic input 100, Windows audio enhancements ON, speakers ~15.

Developer reported `combined smoke passed` (2026-09-24). No Zola speech as a user bubble.

1. **Cold launch** — **pass**. "Hey Zola" → question → spoken answer, no clicks.
2. **Barge-in** — **pass**. Spoken reply interrupted at normal volume; she stopped; one turn.
3. **Follow-up** — **pass**. Follow-up with no wake word was answered.
4. **Timeout, then wake** — **pass**. Indicator returned to *listening for "Hey Zola"*; wake worked with no click.
5. **Text mode** — **pass**. Typed turn silent, mic off, "Hey Zola" did nothing; Voice restored.
6. **Resume** — **pass**. Older session; wake word worked.
7. **Relaunch** — **pass**. Closed and relaunched normally; wake armed; pipeline reconnected.
8. **Distance** — **pass**. "Hey Zola" from normal speaking distance across the room.

## Lore edits

Developer approved 2026-09-24 after two wording corrections (`P2-D14` history; `S22` provenance). Committed in closeout.

| File | Entry IDs |
|---|---|
| `DESIGN_DECISIONS.md` | `C3` annotated (`P2-D01`); `S1` annotated (still deferred); `P2` corrected; new section Phase 2 — Voice: `P2-D01`–`P2-D17`; P2-D04 handover correction; pypinyin gap; Phase 1 bubble/interjection fixes |
| `OPEN_QUESTIONS.md` | `S17`–`S23` added; `S17` marked top Phase 3 candidate; `S13`/`S16` unchanged; closing italic updated |
| `ROADMAP.md` | Phase 1 heading no longer "Current stage"; Phase 2 COMPLETE (seven stages + SHA table + summary); Phase 3 stub (`S17` first) |
| `Zola Master Architecture Plan.md` | Tier 1 Windows Track note: Edge TTS + local faster-whisper (`P2-D02`) |

## Discrepancies

None at start among the three track progress docs and the Reference SHA table. Documents of truth read before Phase 1: `PHASE2_BUILD_PLAN.md` v1.1 (`P2-D01`–`P2-D12`, Phase 2 Lore Closeout, Phase 2 Exit Checklist, What Phase 2 Explicitly Defers), `P2-VOICE_Progress.md`, `P2-SPEAK_Progress.md`, `P2-WAKE_Progress.md`, `VOICE_CONFIG.md`, `ROADMAP.md`, `DESIGN_DECISIONS.md`, `OPEN_QUESTIONS.md`, Master Plan External API Strategy → Tier 1 Windows Track note, `PHASE1_BUILD_PLAN.md` Phase Lore Closeout (style). HEAD on `main` matched `8572ac82a1ac9a52306c2da7119463f58d906231` and the working tree was clean. `hermes-agent` was clean at `345cd2b057a452236de401d3534b8502a7465e8d`.

Plan-vs-prompt, resolved in Phase 3 by following this closeout prompt (Brian's order) and citing progress-doc evidence:

1. **Phase 3 stub list.** Draft uses the prompt's order: `S17`, `S22`, Obsidian, `S16`, `S20`, `S13`, `S12`. The plan's shorter list is a subset.
2. **Open questions.** Filed `S17`–`S23`. `S21` and `S23` match track progress. `S20` uses the prompt title and cites the P2-VOICE `clarify` 115 s observation. `S22` provenance was corrected on review: raised by Brian after the P2-SPEAK smoke test (2026-09-23).
3. **`P2-D13`–`P2-D17`.** Numbered as the prompt specified. Facts match the progress docs.

## Closeout

- Feature / merge SHAs: recorded on `main` after merge.
- `hermes-agent` `git status` is clean at `345cd2b057a452236de401d3534b8502a7465e8d` (pinned `v2026.9.14`).
- No client, config, or Hermes source was changed in this prompt.

### Phase 2 Exit Checklist (PHASE2_BUILD_PLAN.md v1.1)

| Criterion | Result |
|---|---|
| Track 1 (`P2-VOICE`) complete and merged; mic/hotkey, auto-submit, Voice/Text, local STT | ✅ MET — merge `8bfbf64272949957da8ca333416431c802cbb660`; P2-VOICE smoke |
| Track 2 (`P2-SPEAK`) complete and merged; spoken replies, barge-in, follow-up; no self-transcription over 5 replies | ✅ MET — merge `29e11d0cac195ae547bb7cb42c74b31cb7b15d54`; echo guard load-bearing; combined smoke: no Zola speech as a user bubble |
| Track 3 (`P2-WAKE`) complete and merged; minimized, re-arm, Text silent | ✅ MET — merge `0c375efee1ea58d937a1e468ab614bfcf109e0f6`; P2-WAKE smoke 1–10 |
| Named constants for RPC methods, events, timings, thresholds | ✅ MET — `VoiceController` named `voice.*` / `wake.*` methods; track `G-CONST` closeouts |
| `hermes-agent` unmodified; `git status` clean | ✅ MET — clean at `345cd2b057a452236de401d3534b8502a7465e8d` after every Phase 2 track and this closeout |
| No client audio device (no NAudio/WASAPI/MediaCapture) | ✅ MET — no matches in `windows-client` |
| Exactly one submit path (`prompt.submit`) | ✅ MET — typed and spoken both use `MainWindow.SubmitTurnAsync` |
| Live `config.yaml` voice/STT/TTS/wake keys match `VOICE_CONFIG.md` | ✅ MET — compared 2026-09-24 |
| `dotnet build` on `main` after merges | ✅ MET — 0 warnings, 0 errors on `8572ac82` (same tree as `main` at combined smoke) |
| Combined smoke 1–8 + Latitude 7430 | ✅ MET — developer pass 2026-09-24; machine is the Latitude 7430 |
| One voice-state owner (`VoiceController.cs`) | ✅ MET — `voice.record` / `wake.*` sends only from `VoiceController`; `MainWindow` forwards transcripts to `SubmitTurnAsync` |
| No utterance produced two submitted turns | ✅ MET — P2-D12 smokes; combined barge-in was one turn |
| `DESIGN_DECISIONS.md`: `P2-D01`–`P2-D12` recorded; `P2` corrected | ✅ MET — plus `P2-D13`–`P2-D17`; `C3`/`S1` annotated |
| `OPEN_QUESTIONS.md`: `S17`, `S18`, `S19` filed | ✅ MET — also `S20`–`S23` |
| `ROADMAP.md`: Phase 2 COMPLETE with SHAs; Phase 3 stub | ✅ MET |
| Master Plan Tier 1 Windows note corrected | ✅ MET |

## Files

### Created this track

- `zola-architecture/lore/prompts/progress/P2-LORE_Progress.md`

### Modified this track

- `zola-architecture/lore/DESIGN_DECISIONS.md`
- `zola-architecture/lore/OPEN_QUESTIONS.md`
- `zola-architecture/lore/ROADMAP.md`
- `zola-architecture/Zola Master Architecture Plan.md` (Tier 1 Windows Track note only)
