# P4PRE Audit 05 — Developer Live Checks

**Audit ID:** P4PRE  
**Scope:** S32 (L1–L3), S20 (L4–L5)  
**Developer reply:** (message body; prefix `live check:` omitted but content is the L1–L5 script results)  
**Session:** `20260929_110758_bab81f` / ui_session `26f05d46`  
**Logs read:** `%LOCALAPPDATA%\ZolaClient\logs\{voice-timeline,display-state,presence}.log`; `%LOCALAPPDATA%\hermes\profiles\zola\logs\{gui,agent}.log`

---

## Finding summary (this document)

| ID | Label | Severity | Scope | Summary |
|----|-------|----------|-------|---------|
| P4PRE-AUD-30 | [RISK] | HIGH | [S32] | L1: wake+answer at lock screen; confirms AUD-01 |
| P4PRE-AUD-31 | [RISK] | MEDIUM | [S32] | L2: speech + follow-up continue while locked; confirms AUD-05 |
| P4PRE-AUD-32 | [MATCH] | — | [S32] | L3: Text mode — no wake response while locked |
| P4PRE-AUD-33 | [RISK] | MEDIUM | [S20] | L4/L5: model asked in assistant text; **clarify tool never invoked** — S20 stall not reproduced |
| P4PRE-AUD-34 | [RISK] | MEDIUM | [S20] | L6 live: clarify tool blocked ~84 s; drop path exercised |
| P4PRE-AUD-37 | [RISK] | MEDIUM | [S20] | L5 follow-up open but VAD/hallucination cleared transcript — spoken answer lost |
| P4PRE-AUD-38 | [RISK] | MEDIUM | [X] | Tool lifecycle events unused by client — long turns look like stalls |
| P4PRE-AUD-39 | [RISK] | MEDIUM | [S20][X] | StatusText/DetailText under Conversation panel — notices may be invisible |

---

## Developer observations (verbatim summary)

| Check | Developer report |
|-------|------------------|
| L1 | Zola answered out loud from the lock screen with the current time. HUD shows the conversation at 11:08. |
| L2 | Zola continued speaking after lock. Conversation written to the HUD. |
| L3 | No response on lock screen. Mic inactive in text mode. |
| L4 | Costco directions at ~34 s (address in memory — no clarify). Follow-up: directions to son's house → she asked for address → wrong address → couldn't find → asked again → correct address → directions. |
| L5 | Voice: directions to mom's house → "What's her address?" |

---

## Evidence tables

### L1 — Lock while idle

| Step | Developer | Log evidence |
|------|-----------|--------------|
| HUD listening | (implied) | `11:07:59` `wake.start` (voice-timeline; gui.log) |
| Win+L | — | `presence.log` `11:08:10.326` `P3-RENDER: paused (locked)` |
| "Hey Zola, what time is it?" | Answered out loud with time | `11:08:07.980` `wake.detected phrase=hey zola` (voice-timeline); gui `11:08:07,976` emit to sid `26f05d46`; agent `11:08:24` msg=`Hey, Zola, what time is it?`; prompt accepted chars=27; turn complete 5.7 s; response_len=13 |
| Unlock / HUD | Conversation at 11:08 | `presence.log` `11:08:36.635` `resumed (locked)`; display-state Speaking→Idle→follow-up Listening; follow-up fire `11:08:36.898` |

**Supports:** Phase 2 chain (AUD-01/04/05). Client-side lock gate would need to block `wake.detected` → capture → `prompt.submit` — all fired while render was paused locked.

**Client gate sufficient?** For **new** wake turns: yes, if client refuses capture/submit on lock. Residual: Hermes TTS already playing (see L2). Wake lease still owned by connected client.

---

### L2 — Lock while speaking

| Step | Developer | Log evidence |
|------|-----------|--------------|
| Saturn prompt | Kept speaking after lock | `11:09:55.447` `wake.detected`; agent `11:10:03` msg=`Tell me three facts about Saturn`; web_search; turn complete 7.7 s; response_len=275; words=52 on timeline |
| Lock during speech | Continued at lock screen | `presence.log` `11:10:02.210` `paused (locked)` — **between** Speaking onset (`11:10:03.375` display Speaking) and unlock `11:10:28.030` `resumed (locked)`. Estimated speech end `11:10:32.928`; follow-up started `11:10:35.932` |
| Follow-up listen | (developer asked) | Yes: `followUpStarted=True` at `11:10:35.932`; Listening `11:10:36.730`; idle after empty follow-up `11:10:53` |

**Supports:** AUD-05 — in-flight TTS and follow-up `voice.record` are **not** stopped by lock. HUD still received conversation text (developer).

---

### L3 — Lock in Text mode

| Step | Developer | Log evidence |
|------|-----------|--------------|
| Text mode | Mic inactive | display-state `11:11:40.323` `voice="Text mode" mic="Mic: off"` |
| Win+L + "Hey Zola…" | No response | `presence.log` `11:11:56.823` `paused (locked)` … `11:12:28.259` resumed. **No** `wake.detected` between Text mode and unlock. |
| Unlock → Voice | — | Later `11:13:14` brief `wake.start` then Text again `11:13:26` (developer may have toggled); final Voice re-arm for L5 at `11:24:30` |

**Supports:** Phase 2 §6 — Text mode already stops wake (`wake.stop` / mic off). Lock gate less critical in Text for *new* Hey Zola; in-flight Voice turns still matter (L2).

---

### L4 — Clarify (typed)

| Step | Developer | Log evidence |
|------|-----------|--------------|
| Costco directions | Answered ~34 s; no clarify (memory has address) | `11:14:13` prompt chars=49 msg=`Give me driving directions to the nearest Costco.`; tools: skill_view, terminal×N; **no `clarify` tool**; turn finished `11:14:49` duration **36.4 s**; Thinking `11:14:13`→Idle `11:14:49` |
| Son's house | Asked what address is | `11:21:09` msg=`Can you give me directions to my son's house?`; turn 5.0 s; response_len=70; tools: skill_view only — **no clarify** |
| Wrong address | Couldn't find; asked again | `11:21:43` msg=`2914 13st Se, Everett Wa`; geocode error; turn 24.8 s; response_len=113 |
| Correct address | Gave directions | `11:22:50` msg=`Oh. Try 2914 13th St in Everett.`; turn 12.6 s; response_len=510 |

**Clarify server request?** **No.** Searched agent/gui/errors for `clarify`, `request.cancel`, `Ignored a server request` on `2026-09-29` → **zero hits**. Questions were ordinary assistant `text_response` turns; answers were new `prompt.submit` turns. Turns completed normally — no stall, no Cancel, no `SPEECH_INTERRUPTED_NOTE` latch observed in this window.

**Stale-thinking / S26?** Not triggered — each turn got `message.complete` (turn finished within seconds to ~36 s).

**Supports / contradicts:** Source GAP AUD-12 (drop clarify) remains valid but **was not exercised live**. Live behaviour shows a second path: model asks in chat without the clarify tool — S20 "stall until timeout" did not appear. **P4PRE-AUD-33 [RISK]** — Phase 4 must account for both (a) unanswered `srq-clarify` and (b) natural-language "what's the address?" that already works via `prompt.submit`.

---

### L5 follow-up — spoken answer lost (AUD-37)

Developer live-check reply for L5 quoted only the ask and her spoken "What's her address?" — **no spoken address text was reported** in that reply. Logs for the follow-up window:

| Time | Evidence |
|------|----------|
| `11:25:16.503` | display Speaking; turn complete; Edge TTS of 19-char reply |
| `11:25:17.805` | `estimatedEnd` (P2-D15 clock) |
| `11:25:20.806` | `followUpStarted=True` delay=4.302s (voice-timeline) — capture window **opened** |
| `11:25:21.370` | `Voice recording started` (agent.log) — mic open |
| `11:25:38.391` | recording stopped 17.0 s |
| `11:25:39.444` | `VAD filter removed 00:17.027 of audio` (entire clip) |
| `11:25:39.445` | `Filtered Whisper hallucination: ''` (`voice_mode.py` → empty transcript, `filtered: True`) |

**P4PRE-AUD-37 [RISK] MEDIUM [S20]** — In Voice mode, after a plain-text question, a spoken answer can be lost: follow-up capture may be open on the P2-D15 estimate, yet VAD/hallucination filtering yields no `prompt.submit`. Distinct from unanswered `srq-clarify`.

---

### L4 long tool turn — looks like a stall (AUD-38)

Costco turn `11:14:13`→`11:14:49` (36.4 s): tools `skill_view` + multiple `terminal`; presence **Thinking**; no assistant deltas until end.

Hermes emits (contracts): `tool.start`, `tool.complete`, `tool.generating`, `tool.output_risk` (`tui_gateway/contracts/events.py`, `tool_progress.py`).  
Client `ChatSocket.DispatchEvent` switch has **no** `tool.*` cases — `default: return` (~595–597) drops them silently (does **not** even `Routed`).

**P4PRE-AUD-38 [RISK] MEDIUM [X]** — Long tool turns present as undifferentiated THINKING (same symptom class as S20 clarify stall / S26), with no tool-progress HUD. *(Developer prompt item C6 was truncated mid-sentence after "which tool.* / progress"; this answers the identifiable ask from source. Restate if more was intended.)*

**Where "Ignored a server request" would appear:** `ChatSocket` → `Routed` → `MainWindow.OnRouted` → `DetailText` / `_routedNote` only. **Not** written to `voice-timeline.log`, `display-state.log`, `presence.log`, or Hermes `gui.log`/`agent.log`.

---

## L1b — Wake after lock (≥10 s)

| Step | Developer | Log evidence |
|------|-----------|--------------|
| Voice + listening | HUD listening | Pre-lock wake armed (prior state) |
| Win+L + wait 10 s | Counted full 10 s | `presence.log` **`12:23:40.875`** `P3-RENDER: paused (locked)` |
| "Hey Zola, what time is it?" | Answered out loud; bubble "12:24 PM PDT." | `voice-timeline` **`12:23:57.436`** `wake.detected`; gui emit same; prompt `12:24:01.980` msg=`What time is it?`; turn complete 4.6 s; TTS |
| Unlock ~20 s | — | `presence.log` **`12:24:15.615`** `resumed (locked)` |

**Lock preceded wake:** `12:23:57.436 − 12:23:40.875` = **16.56 s** ≥ 10 s. **AUD-30 evidence upgraded** — wake after sustained lock, not mid-capture race (unlike L1 where wake was ~2.3 s before pause).

---

## L6 — Forced clarify (Text mode)

| Step | Developer | Log evidence |
|------|-----------|--------------|
| Send forced-clarify ~12:27 | Empty assistant bubble; CANCEL; no notice seen | display-state **`12:27:07.367`** `voice="Text mode" mode=Thinking`; gui prompt accepted chars=107; agent turn msg starts `Before you answer, use your clarify tool…` |
| Watch 60 s | Bubble never filled | **No** `message.delta` / reply text; Thinking held until Cancel |
| Cancel ~12:28 | "interrupted" | **`12:28:34.106`** `tool clarify completed (83.74s, 149 chars)`; turn `reason=interrupted_by_user` `response_len=0`; gui `status=interrupted` **duration=86.8s**; display **`12:28:34.127`** → Idle |

### Clarify tool / wire details

| Item | Result |
|------|--------|
| Clarify tool invoked? | **Yes** — `tool clarify completed (83.74s, …)` |
| Question text / choices / `srq-*` id | **UNVERIFIED in file logs** (not logged at INFO). Inferred from user prompt + tool blocking ~84 s for server-request answer that never arrived (AUD-12 drop). |
| `request.cancel` | **Not present in gui/agent/errors INFO logs.** Source: `session.interrupt` → `_clear_pending` → cancel reason `interrupted` (`session_lifecycle.py`). |
| Cancel path | Client Cancel → `session.interrupt`; Hermes turn `interrupted_by_user` / `status=interrupted`. |
| `SPEECH_INTERRUPTED_NOTE` (S21) | `session.interrupt` calls `_tts_stream_stop()` default `user_barge=True` (`methods_session.py` ~1997). Latch runs **only if** an in-flight TTS stream state exists (`methods_voice.py` ~117–125); if `state is None`, returns without latch. L6 was Text mode with no spoken reply — **latch likely did not fire** (no TTS). Still S21 risk when Cancel cuts speech. |
| Presence / display 12:27–12:28 | **Thinking throughout** from `12:27:07.367` until Idle at `12:28:34.127` (~86.8 s). |

**AUD-12 / AUD-13 / AUD-34:** Drop path **exercised live**. Stall matches 3600 s timeout design but Cancel cut at ~87 s — developer saw empty bubble + Thinking, not a clarify UI.

### Empty assistant bubble (source)

1. `SubmitTurnAsync` sets `_streaming = true` without creating an assistant bubble (`MainWindow.xaml.cs` ~267–272).  
2. Hermes emits `message.start` → `OnMessageStarted` (~509–537) → `AddLiveBubble()` (~697+) with **empty** `Body.Text`.  
3. Clarify blocks; **no** `message.delta` → bubble stays empty until Cancel → `FinishTurn("interrupted", …)` badges "Interrupted".

### Notice occlusion (AUD-39)

| Layer | Token | ZIndex |
|-------|-------|--------|
| HUD (incl. top-right voice lines) | `ZolaLayerHud` | **10** |
| StatusText / DetailText | `ZolaLayerNotice` | **20** |
| ConversationOverlay | `ZolaLayerPanel` | **40** |

Panel `Background` = `ZolaOverlayBrush` (`#080808` @ **Opacity 0.94**) — HUD/notice can ghost faintly through; Routed "Ignored a server request (clarify)" lands on `DetailText` **under** the open Conversation panel → **invisible to the developer** while the panel is open. Matches screenshot observation.

**P4PRE-AUD-39 [RISK] MEDIUM [S20][X]**

---

### L5 — Clarify (voice)

| Step | Developer | Log evidence |
|------|-----------|--------------|
| Mom's house | Said "What's her address?" | `11:25:01` `wake.detected`; transcript→prompt chars=45 msg=`Can you give me directions to my mom's house?`; turn 6.9 s; response_len=**19**; Edge TTS `11:25:16–17`; display Speaking; follow-up listen `11:25:20` |
| "I'm in Sacramento" / Cancel | (developer did not report stall path) | Follow-up capture `11:25:21–38` transcribed empty / hallucination filtered; no second prompt; no Cancel in logs |

**Clarify `srq-`?** **No** — same as L4. Spoken question was assistant text + Edge TTS, not a server request.

---

## Answers to required questions

### 1. L1–L3 vs Phase 2

Timestamps **confirm** the Phase 2 chain: lock pauses render only (`P3-RENDER: paused (locked)`); `wake.detected` → client capture → `prompt.submit` → TTS still fire. A **client lock gate is sufficient** to stop *new* locked-screen turns **if** it owns wake/record/submit in `VoiceController`/`SubmitTurnAsync`. It is **not** sufficient alone for L2 unless it also interrupts in-flight TTS (`session.interrupt` / `_tts_stream_stop`) and cancels follow-up capture. Text mode already fails closed for wake (L3).

### 2. L4–L5 clarify protocol

| Question | Result |
|----------|--------|
| Did Hermes send a `clarify` server request? | **No** (no frame/log line) |
| `id` / `question` / `choices` | N/A |
| Time to `request.cancel` / reason | N/A — never opened |
| Cancel / `session.interrupt` / S21 latch | Not used in this run |
| L5 "I'm in Sacramento" | Not observed as a submitted transcript in logs (follow-up empty) |
| Stale-thinking / S26 | Not observed |

**P4PRE-AUD-34 [GAP] LOW [S20]** — Live verification of the drop path remains from P2-VOICE lore (115 s clarify stall), not this session.

### 3. UNVERIFIED (logging would help)

| Item | Why | What would verify |
|------|-----|-------------------|
| Exact spoken TTS wording for L1/L5 | Client does not log reply text; agent logs `response_len` only | Log assistant text on `message.complete` or Hermes TTS text |
| Whether Win+L occurred *before* L1 wake | Presence pause `11:08:10` is **after** wake `11:08:07` — lock may have been mid-capture; developer says answer from lock screen (TTS after `11:08:24` while paused until `11:08:36`) | Client log of lock event with wall clock next to wake |
| Raw JSON `srq-` frames | Not present today; ChatSocket drop only appears in UI Routed string — **not** in file logs | Persist Routed / server-request frames to client log (Phase 4 build item) |
| L3 spoken "Hey Zola" while locked | No wake.detected — either unheard or wake truly off | Optional wake attempt counter |

---

## Architecture cross-check

| Phase 2/3 finding | Live |
|-------------------|------|
| AUD-01 voice continues at lock | **Confirmed** L1/L2 |
| AUD-05 in-flight speech | **Confirmed** L2 |
| Text mode stops wake | **Confirmed** L3 |
| AUD-12 clarify drop | **Not exercised**; natural-language Q&A used instead (AUD-33) |

---
