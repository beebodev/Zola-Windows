# P7-CLARIFY Progress — Clarify by Voice

## Branch

- Work branch: `p7-clarify`
- Base `main` HEAD: `512d91490be6317e6f644afc8051160b7cb560ef` (P7-FORENSIC-SERVE disposition merge)
- Prompt: `P7-CLARIFY_Prompt_v1.0.md` (canonical: `C:\Users\test\Dev\zola-spikes\prompts\P7-CLARIFY_Prompt_v1.0.md`)
- Prompt SHA-256 (on-disk, 30,129 bytes): `680c64fa914b5a358416fd022fdf34af9539280664b08c3f9d304f3623a6bd28`
  - Developer-supplied SHA: **matched** (verified at Phase 1 start)
- Quiet-card decision (binding, supersedes plan Track-2 “do not build or show the card”): single-question card still built; panel never auto-opens in Voice mode
- Build plan: `PHASE7_BUILD_PLAN.md` v1.1 on `main` (P7-D09 + quiet-card amendment)
- Hermes HEAD (Phase 1): `345cd2b057a452236de401d3534b8502a7465e8d` (`v2026.9.14`); `git status --porcelain` empty

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Branch and Baseline | COMPLETE |
| 2 | Grounding | COMPLETE |
| 3 | STOP: Approve the Voice-Clarify Contract | COMPLETE |
| 4 | Implementation | COMPLETE |
| 5 | Deploy | COMPLETE |
| 6 | Smoke Test | COMPLETE — passed (C7 PASS on pattern-matched retry; C9b PASS after ScrollToEnd) |
| 7 | Closeout | COMPLETE |

## Guardrails summary

- **G-SCOPE:** New pure helpers under `Voice/` (proposed `ClarifyShape` / `ClarifySpeech`); progress doc; modify only named clarify paths in `MainWindow.xaml.cs`, `BuildSpokenQuestionText` / `SpeakQuestionAsync` (+ optional no-answer callback) in `VoiceController.cs`, and Checks links. No live-profile / SOUL / config / plugin / Hermes edits.
- **G-ARCH:** Plan + quiet-card decision is truth. Track 1 admission / lifecycle / Clarify(id) / cancel / terminals untouched. Broker owns clarify lifecycle. Approval card untouched.
- **G-PATTERN:** Read every relevant file in full before changing it.
- **G-NOCHANGE:** hermes-agent; live profile; ServerRequestBroker / ChatSocket / ZolaDisplayState / HermesProcessManager / CaptureLifecycle / TranscriptAdmission / XAML; approval card; Text-mode / batch / multi-select clarify; `OnVoiceChatEnded`; lore / build-plan.
- **G-ONE-PATH:** Same broker answer calls as today; typed fix reuses voice fill-then-send when approved.
- **G-NO-INSTALL:** Checks stay dependency-free.
- **G-COMMENT:** `// P7-CLARIFY: <rationale> — P7-D09` per distinct changed block.
- **G-CONST:** Named constants for template pieces, classification, log prefixes, reasons.
- **G-PRIVACY:** No question/choice/answer/reply text in logs, progress, or real-use fixtures.
- **G-LIVE:** One live step at a time; Cursor never injects turns; dictation off + P2-D16 before voice smoke.
- **G-CRASH:** Serve native crash filed for future phase; record + relaunch + repeat once; not a track fail unless it repeats.
- **G-STOP / G-CLOSEOUT:** Stop after each phase; closeout only on “proceed to closeout”.
- **G-LORE-SCOPE:** No lore edits this track (S44 at Phase 7 lore closeout).
- **G-NO-CROSS-SCOPE:** No Android Zola.

## Discrepancies

none

## Phase 1 baseline

Recorded 2026-10-06 ~11:40 local.

### Live profile hashes (unchanged by this track)

| Path | SHA-256 |
|---|---|
| `config.yaml` | `7BA2E676A04FF92047C8D711FCB022BE8A532B11BAAC6F74B08986744E704570` |
| `SOUL.md` | `E3D7BF9AC29B46237A2685BEBAE2E89E1A5952EDB23E5AFEEE0EE8363009FB49` |
| `plugins/**` aggregate | `82db44e1e51dce2d6adf0694210dc4391db2efc97b250f3ebd83e14f6a1b630d` |

### Processes

| Process | PID | Start time | Parent | Notes |
|---|---|---|---|---|
| `dotnet.exe` (run Zola.Client) | 23464 | 2026-10-06 10:54:28 | — | parent runner |
| `Zola.Client.exe` | 18452 | 2026-10-06 10:54:29 | 23464 | S1b-attempt-2 client (P7-VOICEAUTH) |
| `python.exe` (venv) | 3052 | 2026-10-06 10:54:30 | 18452 | `-m hermes_cli.main -p zola serve --isolated` |
| `python.exe` (uv cpython) | 25004 | 2026-10-06 10:54:30 | **3052** | serve child |

Serve parent/child: confirmed (25004 ← 3052).

### Logs

| Log | Bytes | Last write |
|---|---|---|
| `%LOCALAPPDATA%\ZolaClient\logs\voice-timeline.log` | 913,101 | 2026-10-06 10:58:20 |
| `%LOCALAPPDATA%\ZolaClient\logs\server-requests.log` | 32,302 | 2026-10-06 09:50:52 |
| `%LOCALAPPDATA%\hermes\profiles\zola\logs\agent.log` | 4,434,491 | 2026-10-06 11:35:01 |

### Pre-change build and checks (branch tip = base, no Track-2 edits yet)

| Command | Result |
|---|---|
| `dotnet build windows-client/Zola.Client/Zola.Client.csproj -r win-x64` | **PASS** — 0 Warning(s), 0 Error(s) |
| `dotnet run --project windows-client/Zola.Client.Checks/Zola.Client.Checks.csproj` | **PASS** — exit 0; coverage lifecycle 22/22, admission 13/13, start 9/9, invalid 6/6, stop_phrase 4/4, amendments 7/7, latch 18/18, wiring 9/9 |

---

## CL-G1–G7 answers (Phase 2)

Recorded 2026-10-06. Read-only grounding + scratch harness. No Track-2 code edits.

### CL-G1 — Classification

**Hermes wire shape**
- Schema requires `questions` (`clarify_tool.py` `CLARIFY_SCHEMA` L258–292; `required: ["questions"]`).
- Handler still accepts legacy top-level `question`/`choices`/`multi_select` when `questions` is absent or empty (`clarify_tool.py` L199–230).
- Live TUI bridge: batch path sends `{"questions": wire}` (`tui_gateway/server.py` `_clarify_block` L1331–1335); legacy single path sends `{"question","choices"[,"multi_select"]}` (L1339–1340).
- Client: any `questions` array → `IsBatch=true` (`ServerRequestBroker.BuildClarifyView` L677–705); else legacy single (`L708–716`). So live model clarifies are **always** `IsBatch` even for one question (matches comment `MainWindow.xaml.cs` L604).

**"Single question" (proposed; for quiet-card / spoken path)**
- Batch shape: `IsBatch && Questions.Count == 1 && !Questions[0].MultiSelect`
- Legacy shape: `!IsBatch && !MultiSelect`
- Everything else (0 questions, 2+ questions, any multi-select) = **card-required** (panel + card behavior unchanged).

**Stability**
- View built once at accept (`BuildClarifyView` in `AcceptRequestLocked` L419–425) and stored on the entry; re-show reuses the same `ClarifyView` (`OnSessionChanged` L166–169). Shape is known at `ClarifyOpened` and stable for the request life.

**Choices / limits (Hermes)**
- Zero choices allowed → open-ended (`_clean_choices` returns `None` when nothing survives; schema omits choices).
- Max choices: `MAX_CHOICES = 4` (`clarify_tool.py` L9); capped in `_clean_choices` L94–97.
- Max questions per call: `MAX_QUESTIONS = 5` (L10, L115–116).
- No max label-length enforced; empty/garbage labels dropped via `_flatten_choice` (L20–32).
- First of ≥2 choices gets ` (Recommended)` via `mark_recommended` (L35–41); stripped on the way back to the model (`strip_recommended` / `_clean_answer` L44–49, L89–91).

### CL-G2 — Choice answers

**Client payload (voice, live `questions[]`)**
- `ApplyVoiceClarifyAnswer` → `FillFirstUnansweredBatchRow` → when no unanswered rows → `AnswerBatch(id, answers)` (`MainWindow.xaml.cs` L602–614).
- Broker sends `{ "answers": { qid: text } }` (`ServerRequestBroker.AnswerBatch` L329–330). No index/label coercion on the Zola path.

**What the model receives**
- Bridge returns JSON `{"answers":…}` to the tool (`server.py` L1336–1338).
- Tool assembles `{"responses":[{"question", "choices_offered", "user_response": …}]}` via `_batch_result` (`clarify_tool.py` L139–152, L164–172).
- `user_response` is `_clean_answer(raw, …)`: strips `(Recommended)` / multi-select JSON; **does not** map free prose to a choice index (`L89–91`). Raw spoken/typed string is what the model sees (after presentation strip only).
- `clarify_gateway.py` `_coerce_text_response_detailed` (L162–184) is the **typed gateway** path (CLI/gateway surfaces), **not** the TUI `server_requests` / Zola `AnswerBatch` path.

### CL-G3 — Record line

- Close record strings are UI-only (`RecordAnsweredPrefix` / `RecordSkipped` / `RecordCancelled` / … at `MainWindow.xaml.cs` L99–106).
- Set in `_requestCloseRecords` before broker answer/skip; applied in `OnRequestClosed` → `CollapseCardToRecord` (L1157–1215), which swaps the card for a `TextBlock` bubble in `Transcript`.
- No `prompt.submit`, no Hermes user message, no `sync_turn`, no memory candidate from the record path — only the prior broker `SendResponse` closed the request.
- Quiet card: same collapse; only `EnsureConversationOpen` on collapse must be suppressed in Voice for quiet singles (see CL-G4).

### CL-G4 — Panel opening sites

| Site | File:lines | Today | Quiet single (Voice) | Text / card-required |
|---|---|---|---|---|
| Clarify open / first show | `OnClarifyOpened` → `EnsureConversationOpen` L1110–1114 | Always opens panel | **Skip** auto-open; still build card + speak | Open (unchanged) |
| Clarify re-show (session/history) | `OnSessionChanged` L162–169 → `ClarifyOpened`; after history `ClearTranscript` then re-show L1814–1815 | Rebuild card if missing → `EnsureConversationOpen`; if card already present, early return L1099–1102 | Quiet; no auto-open; no re-speak (`_spokenClarifyIds` L1117–1123) | Open as today |
| Collapse to record | `CollapseCardToRecord` → `EnsureConversationOpen` L1212–1214 | Opens panel on answer/skip/cancel | **Skip** auto-open for quiet single | Open (unchanged) |
| Approval open | `OnApprovalOpened` L1150–1154 | Opens panel | Untouched (P4-D07) | Untouched |
| User Conversation click | `OnConversationClick` L2329–2348 | Manual open | Allowed (card already in transcript) | Same |
| Notices | `ShowRequestNotice` L634–648 | StatusText only; no panel | No panel | No panel |

**Mode switches**
- **Voice → Text** (`OnModeClick` L514–516 → `EnterTextModeAsync` L1496–1526): abandons pending question (`AbandonReasonTextMode`), `InvalidateAndStopCaptureAsync(CancelReasonModeText)`; broker request **stays Open**. Today does **not** open the panel — Phase 4 must `EnsureConversationOpen` when a quiet single is open so the card is visible (P4-D08).
- **Text → Voice**: no re-speak (`_spokenClarifyIds`); card stays; capture not auto-restarted by mode entry alone.

### CL-G5 — Echo haystack

**Wiring today**
- `SpeakQuestionAsync` TTS text = `BuildSpokenQuestionText`; then `RememberSpokenEcho(spoken)` (`VoiceController.cs` L613–641).
- Clarify capture sets `_followUpEchoPending` / `_followUpCaptureStarted` (L929–933, L1881–1883); `OnVoiceTranscript` echo-checks before `TranscriptAdmission.Decide` (L2021–2036). Echo = reject-only (`AdmissionReasons.Echo`).

**Offline harness** (scratch, synthetic only): `C:\Users\test\Dev\zola-spikes\p7-clarify\cl_g5_echo_harness.py`  
Mirrors `IsEchoOfLastReply` / `NormalizeEchoWords` (min 3 words, ≥0.60 ratio, end-anchored slack). Matrix: 2/3/4-choice lists; 1/2/3+-word labels; answers bare / "the {label} one" / "{label} please" / "I'll go with {label}" / ordinals. **90 cases × 2 haystacks.**

| Haystack | Dropped |
|---|---|
| Question only (current spoken text) | **0 / 90 (0%)** |
| Question + draft spoken choices | **3 / 90 (3%)** |

Drops with choices haystack: only the **last** 3-word label in the 3w list (`bright forest green` bare / "the … one" / "… please") — end-anchor matches the spoken tail. 1–2 word answers never drop (`EchoMinContiguousWords = 3`). Ordinals and "I'll go with …" kept in this matrix.

**Proposal:** keep **question-only haystack** even when TTS speaks choices (feed `RememberSpokenEcho` the question stem; speak the full template). Retains 0% synthetic drop; P7-D06 already blocks capture during question TTS. Alternative (haystack = full spoken string): accept ~3% risk concentrated on last multi-word choice — not recommended.

### CL-G6 — No answer heard

**Today when bound clarify capture ends without Admit while request still Open**
- Silence / `no_speech_limit`: drop path + `CancelFollowUp("no-speech")` + status notice (`VoiceController.cs` L2083–2086); no `AnswerBatch`.
- Echo drop: Admit refused; may `ReopenFollowUpAfterEchoAsync` as `CaptureKind.EchoReopen` (unbound) L2231–2253 — does not answer clarify.
- Gate / mode Text / cancelled / settled: `Decide` drops (`TranscriptAdmission.cs` L68–96); no answer.
- Track 1 cancel / mode→Text: capture invalidated; request remains Open in broker.
- HUD stays **Waiting for your answer** while `HasOpenClarify` (`UpdateChrome` L1648–1650 → `ZolaDisplayState` L351–353).
- Panel was already open from `OnClarifyOpened`, so the card was visible.

**Timeout:** live profile `agent.clarify_timeout: 300` (P4-D10); Hermes `get_clarify_timeout` / `_clarify_block` timeout closes the server request either way (default in code 3600 if unset; profile = 300).

**Proposal (default):** when the bound capture for an **open quiet single** settles without an admitted answer, in Voice mode, open the panel once (`EnsureConversationOpen`) so the card is fail-visible; do not re-open a capture. Safer alternative considered: status-only + HUD (no panel) — weaker visibility with quiet card. Prefer panel-once.

### CL-G7 — Typed answer in Voice mode

**Today (`OnSendClick` L358–377):** for `view.IsBatch` (all live clarifies), typed Send calls `FillFirstUnansweredBatchRow` and **returns without** `AnswerBatch`. Voice path (`ApplyVoiceClarifyAnswer` L602–614) fills then auto-sends when no unanswered rows remain. Text mode: Brian sees the filled row and clicks card Send. Quiet card + closed panel: typed Send would appear to do nothing.

**Proposal (G-ONE-PATH):** for a **single** question (`Questions.Count == 1`, not multi-select), typed composer answer fills then sends exactly like the voice path.  
**Scope options for STOP:**
- **A (recommended):** apply fill-then-send for single-question clarifies in **both** modes — Text mode gains one fewer click; still one broker path.
- **B:** Voice mode only — preserves today's Text "fill then card Send" (P4-D09 letter).

### Also recorded

**Current `BuildSpokenQuestionText` (`VoiceController.cs` L681–696)**
- Single batch (`IsBatch`, 1 question, any choices): spoken = **question text only** (choices never spoken today; P4-D13 amend).
- Single free text: same (question only).
- Batch 2+: first question + `SpokenBatchMoreSuffix` = `" …and there are more on screen."` (L75, L692).
- Legacy `!IsBatch`: `view.Question.Trim()`.

**HUD:** `Waiting for your answer` while open clarify for current session (`ZolaDisplayState.cs` L39, L351–353). Needs **no change** for quiet card.

### Phase-2 proposals (for Phase 3 approval — not implemented)

1. Spoken template (draft): with choices `"{q} Is it {A}, {B}, or {C}?"` / two-choice `or`; free text `{q}` only; strip `(Recommended)` from spoken labels (Brian chooses speak-vs-drop at STOP).
2. Haystack: **question only** (even when choices spoken).
3. No-answer: panel once for quiet single.
4. Typed fix: fill-then-send for single; prefer both modes (option A).
5. Quiet panel table: see CL-G4.

## Phase 3 STOP verdicts

Brian's verdicts (verbatim selections, 2026-10-06):

> "(Recommended)" when choices are spoken: "Drop it (Recommended)". The card still shows it; speech never does.

> Typed answer scope (CL-G7): "Voice mode only (Recommended)". A typed composer answer to a single question sends immediately only in Voice mode, through the voice path's existing fill-then-send logic. Text mode is byte-for-byte unchanged (it fills the row; the card's Send sends).

> Long choices: "Cap → show card (Recommended)". If the spoken choice list (labels after stripping "(Recommended)") exceeds SpokenChoicesMaxWords = 20 words, classify the request as card-required: panel and card exactly as today, question spoken the current way (question only).

Approved from Phase 2 (Brian approved via Claude's summary):

- **Template:** 3–4 choices `"{q} Is it {A}, {B}, or {C}?"`; 2 choices `"{q} Is it {A} or {B}?"`; 1 choice `"{q} Is it {A}?"`; free text `"{q}"` only. Labels trimmed, "(Recommended)" stripped. Plus (Claude): if every label already appears in the question text (case-insensitive, normalized), speak `"{q}"` only, with no duplicate list.
- **Haystack:** question only. Call `RememberSpokenEcho` with the question stem, while TTS speaks the full template.
- **Single question:** `IsBatch && Questions.Count == 1 && !Questions[0].MultiSelect`, or `!IsBatch && !MultiSelect`, and not over the word cap. Everything else is card-required, unchanged.
- **Panel rules:** the CL-G4 table as proposed, plus Voice → Text with an open quiet single opens the panel (`EnsureConversationOpen`). Re-shows are quiet and not re-spoken.
- **No-answer fallback:** when the bound Clarify(id) capture for an open quiet single settles or is cancelled without an admitted answer, in Voice mode, open the panel once (log `clarify panel_open reason=no_answer`). Never reopen a capture. Must cover the echo-drop path. Fallback must not fire when the request has already closed; mode → Text handled by panel rule above.

**Checks to add (approved):** classification over every CL-G1 shape plus the word cap (at, under and over 20); the template for 0/1/2/3/4 choices, "(Recommended)" stripping and the already-named-in-question case; the haystack helper returns the question stem only. Keep Track 1's checks byte-identical and passing.

## Checks (Phase 4+)

| Suite | Result |
|---|---|
| Track 1 lifecycle / admission / start / invalid / stop_phrase / amendments / latch / wiring | **PASS** — byte-coverage unchanged: 22/22, 13/13, 9/9, 6/6, 4/4, 7/7, 18/18, 9/9 |
| Clarify (new) | **PASS** — 20/20 (shapes, word cap, templates, Recommended strip, already-in-question, whole-word containment, haystack stem) |
| `dotnet build` Zola.Client `-r win-x64` | **PASS** — 0 Warning(s), 0 Error(s) |
| `dotnet run` Zola.Client.Checks | **PASS** — exit 0 |

### Byte-identical confirmations (vs `main`)

| Artifact | Result |
|---|---|
| `Voice/TranscriptAdmission.cs` | IDENTICAL (newline-normalized) |
| `Voice/CaptureLifecycle.cs` (incl. `Cancel`) | IDENTICAL (newline-normalized) |
| `OnVoiceChatEnded` | IDENTICAL |
| `OnApprovalOpened` | IDENTICAL |
| `BuildApprovalCard` | IDENTICAL |

### TurnRunning / EchoReopen (Phase 3 ask, confirmed in Phase 4)

- `TurnRunning` ← `_streaming` via `ZolaDisplayState.UpdateWindowFacts` → `SetCaptureGate` (`ZolaDisplayState.cs` L157; `VoiceController.SetCaptureGate`).
- While a clarify tool call blocks the agent turn, `message.complete` has not fired, so `_streaming` / `TurnRunning` stay **true**.
- `ReopenFollowUpAfterEchoAsync` returns early when `TurnRunning` (`VoiceController.cs` ~L2308 area) → timeline `echo-reopen skipped`.
- `ReleasePendingStartAsync` discards non-Clarify pending starts when `TurnRunning` (`~L2466`).
- Belt: also skip EchoReopen when `AwaitingAnswer`; clarify echo path calls `CancelFollowUp("clarify-echo")` (no EchoReopen) and raises no-answer.

### Diff summary (Phase 4)

| File | Change |
|---|---|
| `Voice/ClarifyShape.cs` | **new** — quiet vs card-required, word cap, Recommended strip |
| `Voice/ClarifySpeech.cs` | **new** — spoken template + haystack stem |
| `Voice/ClarifyLog.cs` | **new** — log format/reason constants |
| `VoiceController.cs` | template + haystack; no-answer event; clarify-echo / CancelFollowUp fallback; EchoReopen×AwaitingAnswer |
| `MainWindow.xaml.cs` | quiet panel rules; Voice→Text open; typed fill-then-send (Voice only); no-answer panel once |
| `Zola.Client.Checks/*` | link helpers; 18 clarify rows |
| `P7-CLARIFY_Progress.md` | Phase 3 verdicts + Phase 4 record |

## Deploy record

### Phase 5 — close confirmed

| Phase-1 PID | Status |
|---|---|
| 23464 (`dotnet run`) | GONE |
| 18452 (`Zola.Client`) | GONE |
| 3052 (serve parent) | GONE |
| 25004 (serve child) | GONE |

No leftover `Zola.Client` or `hermes … serve` processes.

### Build (after close)

| Output | Path | mtime | Notes |
|---|---|---|---|
| Usual launch exe | `windows-client/Zola.Client/bin/Debug/net9.0-windows10.0.19041.0/Zola.Client.exe` | **2026-10-06 12:10:09** | matches Phase-1 `dotnet run` path |
| RID win-x64 exe | `…/win-x64/Zola.Client.exe` | **2026-10-06 12:10:58** | `dotnet build … -r win-x64 --no-incremental` |

Build: **PASS** — 0 Warning(s), 0 Error(s).

### Post-relaunch processes

Recorded 2026-10-06 ~12:12 local. Exactly one client and one serve parent/child; all start times after the deploy build.

| Process | PID | Start time | Parent | Notes |
|---|---|---|---|---|
| `dotnet.exe` (run Zola.Client) | 5296 | 2026-10-06 12:11:52 | 23968 | usual launch (no `--no-build`) |
| `Zola.Client.exe` | 25116 | 2026-10-06 12:12:03 | **5296** | `…/net9.0-windows10.0.19041.0/Zola.Client.exe` (mtime 12:10:09) |
| `python.exe` (venv serve) | 21436 | 2026-10-06 12:12:03 | **25116** | `-m hermes_cli.main -p zola serve --isolated` |
| `python.exe` (uv cpython) | 12084 | 2026-10-06 12:12:03 | **21436** | serve child |

Serve parent/child: confirmed (12084 ← 21436).

### Smoke log baselines (byte offsets at deploy)

| Log | Bytes | Last write |
|---|---|---|
| `%LOCALAPPDATA%\ZolaClient\logs\voice-timeline.log` | **914,079** | 2026-10-06 12:12:09 |
| `%LOCALAPPDATA%\ZolaClient\logs\server-requests.log` | **32,302** | 2026-10-06 09:50:52 |
| `%LOCALAPPDATA%\ZolaClient\logs\display-state.log` | **934,557** | 2026-10-06 12:12:09 |
| `%LOCALAPPDATA%\hermes\profiles\zola\logs\agent.log` | **4,448,789** | 2026-10-06 12:12:09 |
| `%LOCALAPPDATA%\hermes\profiles\zola\logs\zola_memory.log` | **192,017** | 2026-10-06 12:12:09 |

## Smoke results

### Part A (Brian, verbatim — 2026-10-06 ~12:15)

| Check | Brian |
|---|---|
| Dictation tool off | "Yes" |
| P2-D16 setup holds | "Yes" |
| Voice mode on | "Yes" |
| New session open | "Yes: b4f25be3" |
| Conversation panel closed | "Yes" |

| Baseline | Value |
|---|---|
| Client session HUD | `b4f25be3` |
| `state.db` agent session | **unbound** at Part A; after C1 bound as `20261006_121206_0979a2` |
| `state.db` user/assistant counts (this session) | **0 / 0** at Part A; after C1 **users=1 / assts=3** (wake only as user; clarify via broker) |
| `zola_memory.pending_turns` | **0** → **1** after C1 |
| voice-timeline bytes (smoke start) | 914,079 → after C1 **921,551** |
| server-requests bytes | 32,302 → after C1 **32,666** |

### Smoke table

| Step | Expected | Observed (logs / counts) | Brian | Result |
|---|---|---|---|---|
| C1 — choices, voice | quiet; speak q+3 choices; bound admit; answered; record on panel open | `clarify quiet … choices=3`; `question_spoken chars=93`; admit `Clarify(srq-0d1241ade00b)`; `answered … len=15`; **no** `panel_open`; users+1 only (wake) | "I replied 'The second one'. No card appeared and she answered normally." | **PASS** |
| C2 — free text | quiet; question only (0 choices); spoken answer | Model used clarify with **choices=4** (seasons); `clarify quiet … choices=4`; admit `Clarify(srq-79ecad82936c)`; `answered len=18`; no `panel_open`; users 1→2 | "No card shown. She asked and listed each season. I replied 'Definitely summer'. She responded that she would remember that." | **PASS** (quiet/bind/answer); 0-choice via C2b |
| C2b — free text 0 choices (retry) | quiet; `choices=0`; spoken answer | `clarify quiet … choices=0`; `question_spoken chars=28`; admit `Clarify(srq-6f99d328774b)`; `answered len=6`; no `panel_open` | "she did not list options this time." | **PASS** |
| C3 — typed in Voice | quiet; type answer; answered; no extra user msg | **Finding:** composer is inside `ConversationOverlay` — cannot type with panel closed. Adapted: open panel (or no_answer opened it). `clarify quiet … choices=2`; capture idle → `panel_open reason=no_answer`; `answered len=8` (`pretzels`); no user msg "pretzels" (users stay wake-only for that turn) | "pretzels" / "done"; earlier: can't type if panel closed | **PASS** (adapted); shell limitation noted |
| C4 — never mind | ordinary clarify answer; natural handling | `clarify quiet … choices=0`; admit len=10; `answered len=10`; no `panel_open` | "she handled it naturally responding 'alright'" | **PASS** |
| C5 — batch (attempt 1) | panel opens; batch card | **No clarify shown.** Provider HTTP 500 after 3 retries: `native turn auth context mismatch: scopes` (openai-codex). Client/serve PIDs unchanged. | Screenshot + "I'm trying again." | **retry** (provider) |
| C5 — batch (attempt 2) | panel opens; batch card; answer works | `panel_open reason=clarify_open` (not quiet); spoken batch; admit then `answered len=59`; `panel_open reason=collapse` | "I responded in one sentence and then hit send. She responded normally." | **PASS** |
| C6 — Voice→Text mid-Q | panel opens; click answers; no stray voice | `clarify quiet … choices=3`; `question_abandoned … text_mode`; `panel_open reason=mode_text`; `answered len=10`; `panel_open reason=collapse`; no Clarify admit after mode switch | "done." | **PASS** |
| C7 — approval (attempt 1) | approval card + panel; decline | Terminal ran with **no** `server-requests` approval line (`approvals.mode: manual` in profile). Wake admit only. Commands were non-dangerous under `manual` (see grounding). | "No card popped. She ran the command and responded" | **retry** (wrong stimulus) |
| C7 — approval (attempt 2) | approval card + panel; decline | Still **no** approval line; `rm -f` single temp file — not in `DANGEROUS_PATTERNS`. | "She ran the command without approval." | superseded by grounding + attempt 3 |
| C7 — approval (attempt 3) | approval card + panel; Deny; file remains | Exact cmd `Remove-Item -Force …\c7-scratch.txt` (matches `approval_detection.py:227`). `server-requests`: `received`/`shown`/`answered … deny` for `srq-36b1ea3b6f34` method=approval; terminal `BLOCKED: Command denied by user`; file still present (mtime unchanged). Panel was open (Brian); `panel_open reason=collapse` after deny. | "The card showed. It went away when I denied. Then she spoke saying that she cannot run it because the command wasn't authorized." | **PASS** |
| C8 — no answer heard | panel once `no_answer`; still answerable | `clarify quiet … choices=0`; capture idle → `panel_open reason=no_answer`; later `answered len=6`; request stayed open until answer | "done. worked as expected" | **PASS** |
| C9 — panel already open | card visible; click or voice | Logs: `clarify quiet … choices=3`; voice admit → `answered len=10`; no auto `panel_open`. Brian: "No card offered." Quiet path lacked `ScrollToEnd` when panel already open. | "done. No card offered." | **PARTIAL** → fixed; see **C9b** |
| C9b — panel open; click while listening | card visible w/o scroll; click → request_closed; no no_answer; reply uses choice | After ScrollToEnd redeploy: `clarify quiet`; `answered len=10`; Accepting→Cancelled `request_closed`→`stop_sent`→Settled; no forced transcript; no `panel_open`; users=1; asst `Dusty blue.` | "card was visible without scrolling… dusty blue… She simply replied 'Dusty Blue'" | **PASS** |
| T1 — Text mode control | panel + card; click answers | `mode=text`; `panel_open reason=clarify_open` (not quiet); `answered len=7`; `panel_open reason=collapse`; no `question_spoken` | "done" | **PASS** |

### Part C (whole smoke window)

| Check | Result |
|---|---|
| No clarify answered by unbound transcript | **OK** — every Clarify admit had matching `clarify=srq-*` |
| Answers once via broker / card / composer; no record-line sync_turn | **OK** — clarify answers via `server-requests` `answered`; wake turns are the user msgs |
| Auto `panel_open` only for approved reasons | **OK** — reasons seen: `clarify_open` (batch/Text), `mode_text`, `no_answer`, `collapse`; quiet singles had no auto-open except C8/C3 no_answer and C6 mode_text |
| Zero admits with cancelled/settled/absent owner | **OK** — no `transcript drop reason=cancelled\|settled` in smoke window for bad admits |
| G-CRASH | **none** |
| C5 provider HTTP 500 | recorded; retry PASS |
| `hermes-agent` | `345cd2b0…`; `git status --porcelain` empty |
| Live profile hashes | config + SOUL unchanged; plugins aggregate **match** Phase 1 `82db44e1…` |

### Smoke verdict

**smoke test passed** (C7 PASS on pattern-matched Deny; C9b PASS after quiet `ScrollToEnd`; C3 adapted — composer only inside overlay; C9 PARTIAL superseded by C9b).

## Post-smoke follow-ups (not closeout)

### C9 fix (quiet ScrollToEnd)

In `OnClarifyOpened` quiet branch: when `ConversationOverlay` is already `Visible`, call `ScrollToEnd()` after adding the card; never open the panel. Comment: `// P7-CLARIFY: quiet card stays in view when the panel is already open — P7-D09`.

| Item | Status |
|---|---|
| Code change | applied (`MainWindow.xaml.cs`) |
| Pre-close build | RID **PASS**; non-RID **FAIL** MSB3027 (exe locked by 25116); checks **PASS** |
| Close confirmed | Phase-5 PIDs 5296 / 25116 / 21436 / 12084 **GONE**; no leftover client/serve |
| Post-close rebuild | RID + non-RID **PASS** 0W/0E; checks **PASS** exit 0 (`clarify rows 20/20`) |
| Relaunch | `dotnet run --project …Zola.Client.csproj --no-build` at 2026-10-06 ~13:15 |

#### Redeploy processes (post-ScrollToEnd)

| Process | PID | Start time | Parent | Notes |
|---|---|---|---|---|
| `dotnet.exe` (run Zola.Client) | **25520** | 2026-10-06 13:15:04 | 23468 | `--no-build` after post-close rebuild |
| `Zola.Client.exe` | **23024** | 2026-10-06 13:15:05 | **25520** | usual `…/net9.0-windows10.0.19041.0/Zola.Client.exe` |
| `python.exe` (venv serve) | **16816** | 2026-10-06 13:15:07 | **23024** | `-m hermes_cli.main -p zola serve --isolated` |
| `python.exe` (uv cpython) | **24212** | 2026-10-06 13:15:07 | **16816** | serve child |

Serve parent/child: confirmed (24212 ← 16816). One client + one serve pair.

#### Redeploy log baselines

| Log | Bytes | Last write |
|---|---|---|
| `voice-timeline.log` | **998,197** | 2026-10-06 13:15:13 |
| `server-requests.log` | **35,938** | 2026-10-06 12:56:45 |
| `display-state.log` | **970,640** | 2026-10-06 13:15:13 |
| `agent.log` | **4,555,028** | 2026-10-06 13:15:17 |

### C7 — Hermes approval grounding (`hermes-agent` @ `345cd2b0`)

**What `approvals.mode: manual` means**

| Source | Citation | Meaning |
|---|---|---|
| Docs | `website/docs/user-guide/security.md:58` | **manual** = "Always prompt the user for approval on **dangerous** commands." Not approve-everything. |
| Mode enum | `tools/approval_context.py:197` (`_VALID_MODES = ("manual", "smart", "off")`); `:228–236` (`_get_approval_mode`) | `manual` / `smart` / `off` only. |
| Gate | `tools/approval.py:1093–1124` (`check_all_command_guards`) | After bypass/`off`/allowlist: run Tirith + `detect_dangerous_command`; **if `warnings` empty → `_approved()` with no prompt**. `smart` only affects `_human_decision` when warnings already exist (`approval.py:1137`). |
| Patterns | `tools/approval_detection.py:200+` (`DANGEROUS_PATTERNS`) | Curated regex list (e.g. recursive `rm`, `Remove-Item … -Force/-Recurse`, `del … /s|/q`, etc.). Plain `rm -f file` and bare `date` are **not** listed. |

**Conclusion:** under `manual`, Hermes prompts for the dangerous-pattern (and Tirith) list only — **not** every terminal command. Classifier (`approval_smart`) is for `smart` mode on already-flagged commands.

**C7 attempt commands (from `state.db` session `20261006_121206_0979a2`)**

| Attempt | User ask | Actual `terminal` command(s) | `detect_dangerous_command` @ 345cd2b0 | Required approval? |
|---|---|---|---|---|
| 1 | "prints today's date" | `date` | False | **No** |
| 2 | create/delete `zola-c7-probe.txt` + approval card | `probe_path="$LOCALAPPDATA/Temp/zola-c7-probe.txt"; : > "$probe_path" && rm -f "$probe_path"` then `test ! -e …` | False / False (`rm -f` single file ≠ recursive patterns) | **No** |

**Hermes-side approval raise / delivery**

`agent.log` around both attempts (12:43 and 12:47): terminal tools completed (`exit_code` 0); **zero** lines matching `approval` / `pending_approval` / `dangerous` / `Waiting for approval`. No gateway approval pending was created — nothing for the client to fail to deliver. Assistant text (msg 2412): claimed no approval-card tool and reported create/remove done.

**Grounding (record):** `manual` = dangerous-pattern only — `security.md:58`, `approval.py:1093–1124`, pattern incl. `Remove-Item … -Force` at `approval_detection.py:227`. Attempts 1–2 were non-dangerous → no card was correct (not a safety finding).

**C7 attempt 3 (Brian OK — pattern-matched retry) — PASS**

| Field | Value |
|---|---|
| Scratch | created `C:\Users\test\Dev\zola-spikes\p7-clarify\c7-scratch.txt` before turn |
| Typed (Voice, panel open) | `Run this exact command in the terminal: Remove-Item -Force C:\Users\test\Dev\zola-spikes\p7-clarify\c7-scratch.txt` |
| Actual `terminal` cmd | `Remove-Item -Force C:\Users\test\Dev\zola-spikes\p7-clarify\c7-scratch.txt` (unrewritten; matches `:227`) |
| Approval id | `srq-36b1ea3b6f34` |
| `server-requests` | `received` / `shown` method=approval; `answered … text_or_len=deny reason=choice` |
| Hermes | `BLOCKED: Command denied by user` (`exit_code: -1`) |
| File after Deny | **still exists** (mtime 2026-10-06 13:21:51 unchanged) |
| Brian | card showed; went away on Deny; she said command wasn't authorized |
| Result | **PASS** |

### C9b — panel open; click while listening

| Field | Value |
|---|---|
| Prompt | paint color / clarify three colors (Brian; panel open first) |
| Clarify id | `srq-7921c7be5041` |
| Brian | "The card was visible without scrolling. I chose dusty blue. She simply replied 'Dusty Blue'" |
| Logs | `clarify quiet … choices=3`; `question_spoken chars=93`; **no** `panel_open`; `answered … len=10`; Accepting → Cancelled `reason=request_closed` → `capture stop_sent` → Settled via idle |
| Forced transcript | **none** (Hermes returned no transcript after cancel; cancel + `stop_sent` are the proof) |
| Extra user msg | **none** — `state.db` users=1 (wake only); asst reply `Dusty blue.` |
| G-CRASH | **none** (PIDs 25520/23024/16816/24212 still up) |
| Result | **PASS** |

## Exit criteria verification (Phase 7a)

Quiet-card reading: plan “no card” = quiet card built, panel never auto-opens (binding Phase 1 decision).

| Criterion | Verdict | Evidence |
|---|---|---|
| CL-G1–G5 answered; template / record / haystack approved | ✅ MET | Phase 2–3 in this doc; Brian STOP verdicts recorded |
| Build passes; checks pass | ✅ MET | Closeout: build 0W/0E; checks exit 0 (`clarify 20/20` + Track-1 coverage unchanged) |
| C1 single + 3 choices (quiet; voice answer) | ✅ MET | Smoke C1 PASS — `clarify quiet`; panel closed; spoken choices; broker `answered` |
| C2 free-text single | ✅ MET | Smoke C2/C2b PASS — `choices=0` on C2b |
| C3 typed in Voice | ⚠️ PARTIAL | Smoke C3 PASS adapted — composer lives inside overlay; typed after panel open / no_answer |
| C4 “never mind” as ordinary answer | ✅ MET | Smoke C4 PASS |
| C5 batch/multi-select card | ✅ MET | Smoke C5 attempt 2 PASS |
| C6 Voice→Text mid-Q | ✅ MET | Smoke C6 PASS — `panel_open reason=mode_text` |
| C7 approval card + panel (control) | ✅ MET | Smoke C7 attempt 3 PASS — Deny; file remains; grounding: `manual`=dangerous-only |
| Text mode clarify unchanged | ✅ MET | Smoke T1 PASS |
| No unbound clarify answers (D05) | ✅ MET | Part C OK |
| Answer once as clarify result (no record-line sync_turn) | ✅ MET | Part C OK |
| hermes clean; live profile hashes unchanged | ✅ MET | `345cd2b0…` clean; config/SOUL/plugins aggregate match Phase 1 |
| C8 no-answer panel once | ✅ MET | Smoke C8 PASS |
| C9 panel already open → card visible / clickable | ✅ MET | C9b PASS after quiet `ScrollToEnd` (C9 PARTIAL superseded) |
| Byte-identical: CaptureLifecycle / TranscriptAdmission / approval / OnVoiceChatEnded | ✅ MET | Phase 4 + closeout recheck: `OnApprovalOpened` / `BuildApprovalCard` / `OnVoiceChatEnded` IDENTICAL vs `main` |

**All criteria met:** YES (C3 noted PARTIAL for shell/composer placement; accepted in smoke).

## Final file list

| Path | Role |
|---|---|
| `windows-client/Zola.Client/Voice/ClarifyShape.cs` | **new** |
| `windows-client/Zola.Client/Voice/ClarifySpeech.cs` | **new** |
| `windows-client/Zola.Client/Voice/ClarifyLog.cs` | **new** |
| `windows-client/Zola.Client/VoiceController.cs` | modified |
| `windows-client/Zola.Client/MainWindow.xaml.cs` | modified (incl. quiet `ScrollToEnd`) |
| `windows-client/Zola.Client.Checks/Program.cs` | modified |
| `windows-client/Zola.Client.Checks/Zola.Client.Checks.csproj` | modified |
| `zola-architecture/lore/prompts/progress/P7-CLARIFY_Progress.md` | progress |

## Closeout SHAs

| Step | SHA |
|---|---|
| Implementation commit (7e) | *(filled after 7e)* |
| Merge on `main` (7h) | *(filled after 7h)* |
| Final `main` HEAD (after 7i docs) | *(filled after 7i)* |
