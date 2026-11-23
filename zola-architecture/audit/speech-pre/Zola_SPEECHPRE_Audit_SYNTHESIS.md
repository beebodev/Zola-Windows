# SPEECH-PRE Audit — SYNTHESIS

**STOP:** Brian brings this synthesis to Claude. Closeout only on exact words `proceed to closeout`.  
**Base:** `bc4fd8b4…` · **Branch:** `speech-pre-audit` · **Hermes pin:** `345cd2b…` · **Readiness:** PASS · **Live serve crashes since 2026-11-16 07:43:37:** 0  
**Prompt SHA-256:** `f1cba41957591a555edea335e3a676b39cac4d200bb0fd3e796d1ec96c8ee8c4`

---

## 1. Finding summary table

| ID | Sev | Label | Area | Summary |
|----|-----|-------|------|---------|
| SPEECHPRE-AUD-01 | HIGH | RISK | Speaking / follow-up | Premature listening: mic opens on monitor silence (~450 ms + 0.5 s), not exact EOS |
| SPEECHPRE-AUD-02 | MEDIUM | GAP | Speaking signals | No client-visible device-clock end-of-playback |
| SPEECHPRE-AUD-03 | LOW | MATCH | Unprompted / D7(a) | Proactive uses `voice.tts`; no follow-up + 2 s echo tail |
| SPEECHPRE-AUD-04 | LOW | MATCH/RISK | R1 code-read | Zira local MATCH; concurrent device with ffplay RISK |
| SPEECHPRE-AUD-05 | HIGH | RISK | Hermes TTS | `voice.tts` ignores `HERMES_VOICE_TTS` |
| SPEECHPRE-AUD-06 | MEDIUM | RISK | Stop | Mic-while-speaking doesn’t stop TTS; unprompted Stop weak |
| SPEECHPRE-AUD-07 | MEDIUM | GAP | Devices | No BT-aware hold/stream-keep; Part G never ran |
| SPEECHPRE-AUD-08 | LOW | MATCH | Mic ownership | P2-D01 serve owns mic today |
| SPEECHPRE-AUD-09 | HIGH | GAP | Wake under owner | Second PortAudio open impossible; wake path undefined if owner holds mic |
| SPEECHPRE-AUD-10 | MEDIUM | RISK | First words | No pre-roll on `voice.record` |
| SPEECHPRE-AUD-11 | HIGH | GAP | Admission | Owner needs Accepting/correlation signals or capture id |
| SPEECHPRE-AUD-12 | LOW | MATCH | Clarify | ClarifyId binding on Zola side |
| SPEECHPRE-AUD-13 | LOW | MATCH | Lock/Text | Fail closed for mic |
| SPEECHPRE-AUD-14 | MEDIUM | RISK | S51-PA | Moving mic out of serve relevant; not decided |
| SPEECHPRE-AUD-15 | MEDIUM | MATCH/GAP | Mic disarm | Ops MATCH; no single guarantee RPC |
| SPEECHPRE-AUD-16 | MEDIUM | GAP | Reply id | Deltas lack stable reply_id |
| SPEECHPRE-AUD-17 | LOW | MATCH | Tool events | `tool.*` visible; ack can be client-spoken |
| SPEECHPRE-AUD-18 | LOW | MATCH | Submit | One `prompt.submit` path |
| SPEECHPRE-AUD-19 | MEDIUM | RISK | Residual speech | Heartbeat/complete paths if TTS re-enabled |
| SPEECHPRE-AUD-20 | MEDIUM | RISK | Placement | Owner placement undecided (Brian) |
| SPEECHPRE-AUD-21 | HIGH | GAP | Lore vs spike | Monitor/estimate listen release needs superseding decision IDs |
| SPEECHPRE-AUD-22 | LOW | MATCH | P8 wording | Passphrase/save use admitted submitted text |
| SPEECHPRE-AUD-23 | HIGH | RISK | Portability | Hermes voice RPCs + ffplay-monitor hard-wired → rebuild if not gated |
| SPEECHPRE-AUD-24 | MEDIUM | RISK | Keys | Deepgram key path hardcodes stable `ZolaClient\secrets` |
| SPEECHPRE-AUD-25 | MEDIUM | GAP | Privacy page | Must disclose Cartesia before live use |
| SPEECHPRE-AUD-26 | LOW | RISK | Deepgram residual | Profile/plugin/tests still Pandora-wired |
| SPEECHPRE-AUD-27 | HIGH | RISK | Refactor | `VoiceController.cs` 4447 lines — refactor-first candidate |

**Counts:** 27 findings — **7 HIGH**, **12 MEDIUM**, **8 LOW** (MATCH-only lows included).

---

## 2. Answers to the seven questions

### Q1 — How she speaks today; what the owner replaces
**EVIDENCE:** Hermes streams reply deltas into a sentence chunker; Deepgram command TTS synthesizes per sentence to temp mp3; each sentence plays via a new `ffplay` under serve; the client estimates speaking and opens follow-up after monitor bout silence (~450 ms debounce + 0.5 s quiet). Unprompted/clarify use `voice.tts` on the same ffplay path; codes use local Zira. **INFERENCE:** The owner would replace Hermes turn TTS + `voice.tts` playback and the listen-release role of the monitor/estimates, supplying device-clock EOS (`safe_to_listen`). Zira stays local (R1).

### Q2 — How she listens today; one listening path under the owner
**EVIDENCE:** Serve owns the mic (wake sherpa PortAudio, then `voice.record` → faster-whisper → `voice.transcript` → `TranscriptAdmission`). Six capture kinds share `StartCaptureAsync`. **INFERENCE:** One listening path means the owner holds capture+VAD+local STT and hands candidates to the same admission authority; Hermes wake/record must stay disarmed. **UNRESOLVED:** Exact “Hey Zola” mechanism when owner holds the mic (AUD-09).

### Q3 — Supported Hermes seams (VD-1)
**EVIDENCE:** Turn TTS disarm via `HERMES_VOICE_TTS` while deltas continue **[MATCH]**; mic/wake disarm by never arming + profile **[MATCH]** ops; `message.delta`/`complete` **[MATCH]**; `tool.*` **[MATCH]**; `prompt.submit` **[MATCH]**; cancel via `session.interrupt` **[MATCH]**. **[RISK]** `voice.tts` ignores TTS-off. **[GAP]** no reply_id on deltas; no single “never open devices” RPC.

### Q4 — Where the owner could live
**EVIDENCE:** Client has events but no WASAPI/IAudioClock/Cartesia/STT stack; supervised Python pattern exists (watcher/phone); spike proved timing outside the app. **Cursor’s recommendation:** supervised separate process (b). **Decision for Brian.**

### Q5 — Spike rules vs Zola
**EVIDENCE (spike MEASURED, by reference):** Phase 3: 0/15 self-admissions with `safe_to_listen`; opening word 10/10; mid-thought 0/3 cut; median reply start 0.32 s. **INFERENCE for Zola:** that gate **supersedes** monitor+estimate listen release; pre-roll/VAD/endpointing/reply ids are **new**; STT model **extends** P2-D02; echo matcher becomes optional defense. New decision IDs required (AUD-21).

### Q6 — Conversation boundary; Brian’s wording
**EVIDENCE:** Narrow boundary = reply text/events in; admitted words + finished/outcomes out. Passphrase and save-phrase read `TurnRecord.user_message` from admitted `prompt.submit` text **[MATCH]** (AUD-22). **INFERENCE:** Listening can separate from speaking at the spike gate seam for a later wake-only listener. Hard wires (AUD-23) make an ungated dual path a rebuild.

### Q7 — Devices, privacy, keys, tests, scenarios, refactor
**EVIDENCE:** BT clipping observed by Brian; Part G unrun; Deepgram key+guards exist; Cartesia path specified; privacy page needs Cartesia update; Checks + zola_tts + P8/P9 tests exist; `VoiceController` 4447 lines is refactor-first candidate. **UNRESOLVED:** BT numbers; combined CPU/RSS; wake-under-owner behaviour.

---

## 3. Build plan implications (GAP / RISK)

| Finding | Plan must account for |
|---------|----------------------|
| AUD-01/02/21 | Wave that installs owner EOS before retiring monitor listen authority; lore supersession IDs |
| AUD-05/23 | Client stops calling `voice.tts` (or routes through owner); keep Hermes turn TTS off |
| AUD-09/11 | Pre-work: choose wake strategy; define owner→lifecycle signals |
| AUD-07 | BT measurements before claiming day-to-day headphone quality |
| AUD-20 | Brian picks placement before topology |
| AUD-24/25/26 | Cartesia secrets+guards; privacy page; Deepgram retire/keep decision |
| AUD-27 | Refactor or slice `VoiceController` before large listen rewire |
| AUD-06 | Explicit Stop/mic-while-speaking policy under SP-D10 (talk-over parked) |
| AUD-14 | Record serve InputStream retirement as S51-relevant, not a crash fix claim |

---

## 4. Pre-work required

1. **Brian decisions** listed in §7 (placement, wake, D7(a), Stop, BT scope, Deepgram retire, supersession IDs).  
2. **Refactor-first consideration** for `VoiceController.cs` (AUD-27) — Cursor suggests a thin “speech gateway” seam rather than a full rewrite unless Brian orders a refactor track.  
3. **Measurements:** wake-under-owner smoke design; Part G when BT is in scope (does not block Realtek-first wave).  
4. **Privacy page Cartesia update** before live Cartesia use.  
5. Else for Realtek immediate-reply wave: **none** beyond decisions + Hermes TTS/`voice.tts` disarm policy.

---

## 5. Architecture assumptions confirmed (MATCH)

AUD-03 D7(a) enforcement · AUD-04 R1 Zira · AUD-08 P2-D01 · AUD-12 clarify bind · AUD-13 lock/Text · AUD-15 mic disarm ops · AUD-17 tool events · AUD-18 submit path · AUD-22 P8 wording · Phase 4 turn-TTS disarm + deltas/complete.

---

## 6. Possible track split — Cursor’s suggestion (labelled)

| Wave | Changes | Must not break |
|------|---------|----------------|
| **0 — Seams / optional VC slice** | Owner IPC contract; keep `TranscriptAdmission`; stop calling `voice.tts` from new code paths; TTS-off sync | Admission, P8 passphrase, clarify ids, lock/Text |
| **1 — Speak Julia + exact EOS** | Supervised owner plays Cartesia Julia from `message.*`; `safe_to_listen`; Hermes turn TTS off; monitor demoted for listen | Codes Zira; beeps/thinking stay off; proactive still delivered (via owner); HUD Speaking |
| **2 — Listen via owner** | Owner mic+VAD+STT → admission; Hermes wake/record disarmed; wake strategy from Brian | One admit path; clarify; no dual mic |
| **3 — Retire superseded** | Estimate follow-up; optional echo matcher; Deepgram profile if chosen | Presence mouth if still monitor-based until retargeted |
| **4 — Baseline tone / BT** | SP-D05 baseline delivery; Part G-informed BT hold | Privacy page; R1 |

Talk-over remains parked (SP-D10). This is input to the build plan, not the plan.

---

## 7. Decisions for Brian

| # | Decision | Evidence | Options |
|---|----------|----------|---------|
| 1 | Where the owner lives | Phase 5 | (a) in-client · **(b) supervised process (Cursor)** · (c) other |
| 2 | What replaces “Hey Zola” capture | AUD-09 | Owner phrase detect · `wake.feed` to Hermes KWS · temporary PTT-only |
| 3 | Lift D7(a)? | Phase 6 Q2 | Keep no-follow-up after unprompted · Lift after EOS proven |
| 4 | Stop / mic-while-speaking while she speaks | AUD-06; talk-over parked | Stop cuts owner playback · Mic ignored for interrupt until talk-over returns |
| 5 | Bluetooth in first ship? | AUD-07; Part G | Realtek-first · Require Part G before BT claim |
| 6 | Retire Deepgram TTS? | AUD-26; SP-D09 | Retire · Keep fallback · Keep tests only |
| 7 | Which decisions get new IDs | AUD-21 | Supersede P7-D06/P4-D18 listen · P2-D02 models · adopt SP-D04 · optional P7-D07 |

---

## 8. Scenarios at release

**Existing:** SC-S51F-SM1, EXP-BEEP, SM2/EXP-LOST, SC-PROC1-S1; privacy DEV as touching secrets/roots.

**Add:** premature listening gone on long paused reply; opening word kept; mid-thought pause not split; exact EOS before mic; owner/helper down fail-closed; passphrase after owner STT; Cartesia (no Deepgram) on privacy check; BT first/last word (if BT in scope).

---

## 9. Open questions (not decisions)

- Cartesia voice withdrawal policy (SP-D09 UNRESOLVED).  
- KI-S51-PA input vs output stream.  
- Combined Zola+owner RSS/CPU.  
- Whether mouth/presence keeps ffplay monitor until owner events.  
- S1∪S3 opening-word policy (spike noted, undecided).  
- Nuplex as future conversation layer (provisional only; out of scope).

---

*End of synthesis. Awaiting Claude’s review before decisions and the build plan.*
