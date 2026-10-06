# P7PRE Audit 03 — S44: Every User of the Clarify Card

**Client:** `7d77cb51` · **Hermes:** `345cd2b0`  
**Labels:** `P4-D07`–`P4-D15`, `P4-D10`, `S44`, LEAD-5

---

## 1. Inventory (card / panel)

| # | Path | File:lines | Voice today | If no card in Voice |
|---|---|---|---|---|
| A | Broker accept / `ClarifyOpened` | `ServerRequestBroker.cs` L188–197, L360–432, L69 | Unchanged | Unchanged |
| B | Show card + **`EnsureConversationOpen`** | `MainWindow.xaml.cs` L1096–1133, L1621–1632 | Panel forced open | **Must not** auto-open (S44); TTS/HUD still needed |
| C | Build card / choices UI | L1227–1436 | Choices visible | Choices unheard unless spoken |
| D | Batch fill / send from card | L1528–1607 | Voice fills rows | **Broken:** `BatchHasUnansweredRows` true when no card (L1557–1559) |
| E | Answer / skip / collapse | Broker L320–348, L543–593; UI L1166–1224 | Collapse to record | Broker close still required |
| F | Voice speak + capture | `VoiceController.cs` L564–910 | Independent of card | OK |
| G | `OnTranscriptReady` / P4-D14 | MainWindow L562–632 | Bound → answer | Single non-batch OK without card |
| H | HUD waiting | `ZolaDisplayState.cs` L326–353 | Broker-driven | OK without card |
| I | Stop phrase → `SkipClarify` | MainWindow L544–555 | Works | Works |
| J | Approvals | L1136–1163, L1439–1525 | Card + panel | Unchanged (`P4-D07`) |

---

## 2. Voice clarify today (step map)

| Step | What | Lines |
|---|---|---|
| 1 | Hermes `clarify` server request | `server.py` L1325–1341 |
| 2 | Broker shown → `ClarifyOpened` | Broker L419–425 |
| 3 | Panel opens | MainWindow L1122 |
| 4 | Card built | L1119–1131 |
| 5 | `SpeakQuestionAsync` — question only (`P4-D13`) | VC L564–671 |
| 6 | `voice.tts` + `RememberSpokenEcho` | VC L604–616 |
| 7 | Wait playback release | VC L688–856 |
| 8 | Clarify capture (`_activeClarifyCaptureId`) | VC L858–910, L1788–1790 |
| 9 | HUD "Waiting for your answer" | MainWindow L1657–1659 |
| 10 | Transcript → echo (if eligible) → `ApplyVoiceClarifyAnswer` | VC L1908–1984; MW L570–631 |
| 11 | Broker result → collapse | Broker L570–581; MW L1166–1183 |

---

## 3. Choices

- **Spoken:** question only; choices **not** spoken (`P4-D13` amendment) — VC L656–667.
- **Hermes gateway coerce** (typed path): index or exact label; free prose on choice prompt → reject (`clarify_gateway.py` L162–184).
- **Zola server-request path:** raw string via `AnswerClarify` — **spoken free text is accepted**; no index/label validation in broker.

Without a card, Brian cannot see choices unless TTS speaks them or free-text is accepted as today.

---

## 4. Multi-select and batch

**Wire:** `questions[]` with `{qid, question, choices, multi_select}` → answer `{answers: {qid: string}}`; multi-select value = JSON array of labels.

**Log frequency (`server-requests.log`):** schema logs method/id/len only — **no** choices/multi/batch-size fields.

| Metric | Count |
|---:|
| clarify `received` | 47 |
| unique clarify ids | 42 |
| answered | 35 (skip=6) |
| cancelled | 8 |
| late_answer_dropped | 2 |
| has choices / multi / batch size | **not countable from log** |

---

## 5. Skip / cancel / timeout by voice

| Utterance | Stop phrase? (`voice.stop_phrases=["stop"]`) | Effect |
|---|---|---|
| `stop` (exact) | Yes | Ends voice chat; open clarify → `SkipClarify` |
| `never mind` / `skip` / `cancel` | **No** | Treated as answer text if captured |
| `no_speech` / idle | — | Cancels follow-up; **clarify stays open** |
| 300 s timeout (`P4-D10`) | — | Hermes `request.cancel` reason timeout → broker Cancelled + abandon |

---

## 6. Late-answer drop (`P4-D14`)

`_closedClarifyCaptureId` is tied to **broker close + capture lifecycle** (`AbandonPendingQuestionIfId`, interrupt-like `CancelFollowUp` reasons) — **not** specifically to the card Cancel button. Survives a no-card Voice design if abandon-on-close remains.

---

## 7. Approvals

No voice path (`P4-D07`). Panel still auto-opens on approval. Voice-only clarify does not change approvals.

---

## 8. S45 link — LEAD-5

**LEAD-5 as written:** "echo guard does not run on clarify captures" — **REFUTED** for **bound** clarify captures (`_followUpCaptureStarted` / `_followUpEchoPending` set at L895–897; echo runs at L1940).

**LEAD-5 residual (PARTLY confirmed):**

1. Unbound transcripts while a clarify is open route to newest clarify (MainWindow L585–593) — **no second echo gate** in MainWindow.
2. Question TTS is in the echo haystack; short answers can miss the ≥3-word / 0.60 test → her words can still answer her question.
3. Voice-only clarify **depends** on S45 provenance fix so the clarify capture hears only Brian.

**Finding P7PRE-AUD-12** [RISK] MEDIUM — Clarify×echo: guard runs on bound captures but unbound routing + short-answer miss remain; voice-only clarify needs S45.

---

## 9. Text mode

Card UX unchanged (`P4-D08`, `P4-D09`). `SpeakQuestionAsync` skipped when not Voice.

---

## Findings

| ID | Label | Severity | Summary |
|---|---|---|---|
| P7PRE-AUD-12 | [RISK] | MEDIUM | LEAD-5 partly; unbound clarify routing + short echo miss |
| P7PRE-AUD-13 | [GAP] | MEDIUM | No-card Voice breaks batch voice answers (`_requestCards`) |
| P7PRE-AUD-14 | [GAP] | MEDIUM | Choices never spoken; no-card leaves no channel for choices |
| P7PRE-AUD-15 | [MATCH] | — | Text keeps card; approvals never voice; late-drop not card-only |
