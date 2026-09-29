# P4PRE Audit — Synthesis

**Audit ID:** P4PRE  
**Scope:** S32 (lock voice), S20 (clarify), S22 (voice naturalness)  
**Branch:** `audit/p4pre-conversation` @ `504ae76…`  
**Hermes:** clean `345cd2b…` / `v2026.9.14`  
Nothing here is a decision. Options and facts only.

---

## Section 1 — Finding Summary Table

| ID | Scope | Severity | Label | File/log | Summary |
|----|-------|----------|-------|----------|---------|
| P4PRE-AUD-01 | [S32] | HIGH | [RISK] | `PresenceView.cs` L211–215 | Lock pauses presence only; voice continues |
| P4PRE-AUD-02 | [S32] | — | [MATCH] | `SessionLockWatcher.cs` L81–104 | WTS lock/unlock events correct |
| P4PRE-AUD-03 | [S32] | HIGH | [GAP] | Voice/display | No queryable lock fact for voice/HUD |
| P4PRE-AUD-04 | [X] | — | [MATCH] | `VoiceController` chain | Client drives wake→record→submit |
| P4PRE-AUD-05 | [S32] | MEDIUM | [RISK] | Hermes TTS/barge | In-flight speech continues without lock gate |
| P4PRE-AUD-06 | [S32] | — | [MATCH] | `wake.pause` | Releases mic device |
| P4PRE-AUD-07 | [S32] | MEDIUM | [GAP] | `ZolaDisplayState.cs` | No lock-specific mic/HUD line |
| P4PRE-AUD-08 | [S32] | MEDIUM | [RISK] | `SessionLockWatcher` | Cannot tell lock from UAC/screensaver/remote |
| P4PRE-AUD-09 | [S32] | — | [MATCH] | `HermesProcessManager` / WS | Orphan serve does not keep wake armed |
| P4PRE-AUD-10 | [S32] | LOW | [GAP] | WTS remote codes | Suspend/remote not in voice privacy policy |
| P4PRE-AUD-11 | [S20] | — | [MATCH] | `server_requests.py` | Clarify is `srq-*` request + response frame |
| P4PRE-AUD-12 | [S20] | HIGH | [GAP] | `ChatSocket.cs` L500–504 | All server requests dropped |
| P4PRE-AUD-13 | [S20] | HIGH | [RISK] | profile + timeout | 3600 s stall / Thinking if clarify opens |
| P4PRE-AUD-14 | [S20] | — | [MATCH] | `clarify_tool.py` | Clarify enabled on serve |
| P4PRE-AUD-15 | [X] | HIGH | [RISK] | approval drop | Dangerous cmds deny ~300 s unseen |
| P4PRE-AUD-16 | [S20] | MEDIUM | [GAP] | `ZolaDisplayState` | No CLARIFICATION_PENDING / HUD |
| P4PRE-AUD-17 | [S20] | MEDIUM | [GAP] | `ChatSocket` resume | `open_requests` unread |
| P4PRE-AUD-18 | [S20] | — | [MATCH] | contracts / shared TS | Generic boundary supported |
| P4PRE-AUD-19 | [S20] | MEDIUM | [RISK] | Voice submit path | Transcripts ≠ clarify answers |
| P4PRE-AUD-20 | [S22] | — | [MATCH] | profile TTS | Edge AriaNeural matches P2-D03 today |
| P4PRE-AUD-21 | [S22] | MEDIUM | [GAP] | `_generate_edge_tts` | pitch/volume not passed |
| P4PRE-AUD-22 | [S22] | — | [MATCH] | command provider | CLI can set pitch/volume |
| P4PRE-AUD-23 | [S22] | — | [MATCH] | Edge+ffplay | P3-D23 **PASS** |
| P4PRE-AUD-24 | [S22] | HIGH | [RISK] | streamers | P3-D23 **BREAK** (ffplay-only monitor) |
| P4PRE-AUD-25 | [S22] | MEDIUM | [RISK] | `VoiceController` P2-D15 | Rate/provider invalidates constants |
| P4PRE-AUD-26 | [S22] | MEDIUM | [GAP] | Hermes→client | No end-of-playback RPC (S17) |
| P4PRE-AUD-27 | [S22] | — | [MATCH] | lazy installs off | Premium needs explicit install |
| P4PRE-AUD-28 | [S22] | LOW | [GAP] | agent prompts | No voice-mode system slot |
| P4PRE-AUD-29 | [S22] | LOW | [RISK] | SentenceChunker | Per-sentence synth flattens intonation |
| P4PRE-AUD-30 | [S32] | HIGH | [RISK] | live L1 | Wake+answer at lock screen — evidence for AUD-01 |
| P4PRE-AUD-31 | [S32] | MEDIUM | [RISK] | live L2 | Speech+follow-up while locked — evidence for AUD-05 |
| P4PRE-AUD-32 | [S32] | — | [MATCH] | live L3 | Text mode no wake on lock |
| P4PRE-AUD-33 | [S20] | MEDIUM | [RISK] | live L4/L5 | Natural-language ask; clarify tool unused |
| P4PRE-AUD-34 | [S20] | MEDIUM | [RISK] | live L6 | Clarify tool blocked ~84 s; drop path exercised |
| P4PRE-AUD-35 | [S22]/S17] | MEDIUM | [RISK] | spike silence | Trailing silence ~0.74–1.17 s (corpus) |
| P4PRE-AUD-36 | [S22] | LOW | [RISK] | spike WPS | Aria ~3.9 WPS vs P2-D15 2.5 |
| P4PRE-AUD-37 | [S20] | MEDIUM | [RISK] | L5 follow-up 11:25:21–38 | Spoken answer to plain-text question can be lost |
| P4PRE-AUD-38 | [X] | MEDIUM | [RISK] | ChatSocket / tool events | Long tool turns look like a stall (no tool.* UI) |
| P4PRE-AUD-39 | [S20][X] | MEDIUM | [RISK] | MainWindow.xaml / ZolaTokens | Notices under Conversation panel (Z 20 < 40) |

**Counts:** 39 findings — **7 HIGH**, **16 MEDIUM**, **4 LOW**, **12 MATCH**.

---

## Section 2 — Build Plan Implications

**AUD-01 / 03 / 05 / 07 / 30 / 31 (S32):** Phase 4 must feed a queryable lock fact into `VoiceController` (sole wake/record authority, `P2-D12`) and express HUD truth only through `ZolaDisplayState` (`P3-D03`). RPCs: `wake.pause`/`stop`/`resume`/`start`, optional `voice.record` stop and `session.interrupt` for in-flight TTS. Live **AUD-30/31** are **[RISK]** evidence that AUD-01/05 occur in production — not architecture matches. **L1b** upgrades AUD-30: lock at `12:23:40.875`, wake at `12:23:57.436` (**16.56 s** later). L2 proves interrupt/follow-up cancel is required if speech must stop on lock.

**AUD-12 / 13 / 34 / 39 (S20 clarify live):** L6 forced clarify — tool ran **83.74 s** then Cancel → `interrupted` (86.8 s). Empty bubble from `OnMessageStarted`→`AddLiveBubble` with no deltas. Drop path exercised; `srq-*` / question text / `request.cancel` not in INFO logs (UNVERIFIED fields). **AUD-39:** `DetailText` (Routed notices) sits at Z=20 under Conversation panel Z=40 @ 0.94 opacity — "Ignored a server request" can be invisible while Conversation is open. Build plan must surface clarify in-panel (or raise notice z-order), not only Status/Detail.

**AUD-08 / 10 (S32 scope):** Build plan must state whether the gate is `Locked` only or also suspend / future signals. Do not invent new detectors in Phase 4 without a decision (9b).

**AUD-12 / 16 / 17 / 18 / 19 (S20):** Insert a server-request boundary at `ChatSocket.Dispatch` (~500–504). One open-request owner by `srq-*` id; respond with JSON-RPC result frames / `clarify.lock`. Do not add a second transcript→submit path — redirect while clarify is open (`P2-D05`/`P2-D12`). Surface awaiting-answer via `ZolaDisplayState` / Conversation Panel (`P3-D03`/`P3-D04`). Read `open_requests` on resume.

**AUD-13 / 15:** Timeout and approval fail modes belong in the same boundary decision. Approval drop is fail-closed deny (~300 s) — same socket, different severity.

**AUD-33 / 37 (S20 voice answers):** Live checks showed the model often asks in assistant text instead of the clarify tool. Build plan must not assume every “what’s the address?” is an `srq-clarify`. **AUD-37:** after a plain-text question, the follow-up capture can open (P2-D15) yet yield empty transcript (VAD / hallucination filter) — spoken answers can be lost without a clarify response path.

**AUD-38 (tool progress):** Hermes emits `tool.start` / `tool.complete` / `tool.generating` / `tool.output_risk`; the client drops unknown event types. Long tool turns (L4 Costco 36.4 s) stay in THINKING with no tool chrome — looks like an S20/S26 stall.

**AUD-20–29 / 35–36 (S22):** Preference path (developer evidence) → Sonia +10%, command-provider pitch −2Hz, shaping, whole-line chunks. Playback if staying Edge+ffplay remains **P3-D23 PASS**. Retune `P2-D15` (AUD-25/36). Streaming providers remain **BREAK** (AUD-24) — not implied by current pick.

**Shared-file track order:** `VoiceController.cs` and `ZolaDisplayState.cs` are touched by S32 and S20; `TtsPlaybackMonitor.cs` only if S22 leaves Edge+ffplay. Expected **S32 → S20 → S22** still holds if S22 stays Edge/command-provider (no monitor rewrite). Challenge only if S22 adopts streaming (**BREAK**) before lock/clarify land.

---

## Section 3 — Pre-Work Required

| Item | Why |
|------|-----|
| Developer decisions in §5 | Required before `PHASE4_BUILD_PLAN.md` |
| Live Hermes trial of Sonia +10% / pitch / shaping | Offline samples only; developer noted final confirm during S22 track |
| Optional: persist `ChatSocket` Routed / server-request frames to client log | Live AUD-34 — `srq-clarify` drop not observed this session |
| Optional profile config change | Voice/rate/command-provider keys — developer-approved only (`P2-D09`); no audit edit |
| Installs | **None** required for preferred Edge+Sonia+command-provider path. ElevenLabs/Piper still need explicit approval if chosen later (`P2-D10`/`P2-D17`) |

If command-provider Edge CLI is chosen for pitch: confirm `tts.providers.*` shape against pinned Hermes and that serve PATH still has `edge-tts` / writes MP3 played via ffplay (keeps **PASS**).

---

## Section 4 — Architecture Assumptions Confirmed

Every **[MATCH]**: AUD-02, 04, 06, 09, 11, 14, 18, 20, 22, 23, 27, 32.

Notable confirms: WTS lock detection works; client owns wake→submit; `wake.pause` releases mic; clarify wire format is `srq-*` + response; clarify tool enabled; generic server-request protocol; Edge+ffplay is P3-D23 PASS; live L3 Text mode stops wake. **AUD-30/31 are not matches** — they are live [RISK] confirmations of the lock-surface gap.

---

## Section 5 — Open Questions / Decisions Needed

**16 decisions** (items 1–14, 13b, 13c).

### S32 — Lock voice gate

1. **Which option?** A pause wake+mic; B keep listening refuse replies; C keep deliberately; D safe-replies allowlist. Facts: L1/L2 confirm exposure; Privacy-protective / S32 lore; `wake.pause` releases mic (AUD-06).
2. **Unlock policy?** Auto-resume listening vs stay paused until click / Ctrl+Space / Hey Zola. Facts: unlock today is render-only; `ReconcileWakeRestingAsync` will fight an undifferentiated pause.
3. **Sleep / user-switch?** Treat `Suspending` like lock? Ignore remote disconnect (not subscribed)? Facts: AUD-08/10.
4. **Gate scope (9b)?** `Locked` only vs also other non-interactive states. Facts: UAC/screensaver/remote raise no current events.
5. **HUD while locked?** New mic/voice strings via `ZolaDisplayState` only? Facts: AUD-07; P2-D08 honesty.

### S20 — Clarify / server requests

6. **Surface in Voice and Text?** Card / HUD / speak via `voice.tts` / show-only. Facts: L6 empty bubble + no clarify UI; AUD-12/16/39 (notices under panel).
7. **Speak the question?** (i) `voice.tts` (ii) Hermes path (none found) (iii) show only.
8. **Spoken answer routing?** Redirect `VoiceController` transcript consumer vs MainWindow-owned respond — one submit/respond authority. Facts: AUD-19; P2-D05; AUD-37 follow-up loss.
9. **Clarify timeout?** Keep 3600 / lower `agent.clarify_timeout` / UI countdown. Facts: AUD-13; L6 Cancel at ~87 s before timeout.
10. **`PresenceMode` while waiting?** Stay Thinking / Listening if capture open / new mode (amends `P3-D04`). L6 stayed Thinking ~87 s.
11. **`approval` and other server requests in Phase 4 or new open question?** Facts: AUD-15 same drop; approval fail-closed.
12. **Boundary:** generic server-request boundary first (clarify as first handler) vs clarify-only? Facts: AUD-18; L6 proves first handler needed; races in Audit 03 §12c.
13. **Natural-language asks vs clarify tool?** Live L4/L5 used text asks (AUD-33); L6 proves tool path also fires when instructed — both must be handled.
13b. **Notice visibility:** Raise notice z-order / in-panel status when Conversation open (AUD-39)?
13c. **Tool progress visibility:** Show tool activity during long turns (Hermes `tool.start` / `tool.complete` / `tool.generating` events) so a 36 s tool turn does not look like a stall? In Phase 4 scope or new open question? Facts: AUD-38; L4 Costco 36.4 s silent THINKING; developer's real-world symptom "she just sits there thinking".

### S22 — Voice naturalness

Developer listening (verbatim evidence; **not** ranked findings):

> Pick: en-GB-SoniaNeural at +10% (Hermes speed 1.1). Set on this voice. The British accent is intentional. Whole over split; definitely shaped; Pitch −2Hz preferred. Others out (Ana = child, not considered). Judged on laptop speakers from offline files; final voice to be confirmed in a live Hermes trial during the S22 track.

| Preference | Phase 4 item | Feasibility facts | **P3-D23** |
|------------|--------------|-------------------|------------|
| **Whole-line synthesis** | **Item 7** — larger chunks without Hermes source edits; latency-to-first-audio | Hermes Voice stream hardcodes `SentenceChunker` (`min_len=20`, `.!?` boundaries) — **no profile knob** for whole-line / paragraph chunks without Hermes source change or a non-stream speak path. SOUL can ask for fewer short sentences but boundaries still split on `.!?` (AUD-29). Whole-line **increases** latency to first audio (must synth full line before ffplay) vs first-sentence onset (~0.74 s median synth for Aria sentence; whole L2/L4 longer). Offline: developer prefers whole (`chunk_*_r10_*_whole`). | Staying Edge MP3→ffplay: **PASS**. Chunk size does not change player. |
| **Pitch −2Hz** | **Item 2** — command-provider route | Built-in `_generate_edge_tts` does **not** pass pitch (AUD-21). Command provider + `edge-tts --pitch=-2Hz` **is viable** without Hermes edits (AUD-22); spike produced `pitch_en-GB-SoniaNeural_r10_m2Hz.mp3`. Requires profile `tts.providers.*` + provider switch; serve must still end in ffplay-visible MP3 for mouth. | If command provider → MP3 → ffplay child of serve: **PASS**. If it switched to sounddevice: **BREAK**. |
| **Shaping** | **Item 8** — identity/prompt files | No Hermes source edit. Touches profile **`SOUL.md`** (and optionally other identity/persona files under the live profile). No dedicated voice-mode system-prompt slot (AUD-28). Edge has no audio-tag rewrite. Offline: `shape_sonia_r10_shaped` preferred. | **PASS** (playback unchanged). |
| **Voice + rate** | Item 1 | Profile `tts.edge.voice: en-GB-SoniaNeural`, `tts.edge.speed` / `tts.speed: 1.1` (+10%). Retune P2-D15 (AUD-25/36). Live confirm still pending. | **PASS** |
| ElevenLabs / Piper | Item 3 / 3b | Not preferred offline; would need install/key; stream **BREAK**. | PASS only if sync+ffplay |

**Sonia r10 trailing silence vs S17:** median **0.387 s**, max **0.991 s** (n=12) vs corpus median **0.740 s** / max **1.170 s** (AUD-35). Lower trailing silence on Sonia r10 may shorten post-speech mouth hold under `TtsPlaybackMonitor`, but S17 (envelope / true end) remains open — no client end-of-playback RPC (AUD-26).

### Track order

14. Confirm or challenge **S32 → S20 → S22**? Shared: `VoiceController`, `ZolaDisplayState`. `TtsPlaybackMonitor` only if S22 leaves Edge+ffplay. With Sonia+Edge+command-provider+shaping, monitor untouched → order still sound. If S20 generic boundary and S32 lock gate both land in `VoiceController`/`MainWindow`/`ChatSocket`, sequence S32 then S20 reduces conflict on wake/submit ownership.

---

## Section 6 — Evidence Gaps

| UNVERIFIED / gap | What would verify |
|------------------|-------------------|
| AUD-34 — `srq-clarify` not seen in early live session | **Superseded by L6:** tool clarify ran 83.74 s; wire `srq-*` / question / choices / `request.cancel` still **UNVERIFIED in INFO logs** (not emitted there). Persist Routed + server-request frames to client log to capture `Ignored a server request (clarify)` and `srq-*` id |
| Exact lock timestamp vs wake in L1 | L1 race noted; **L1b proves** lock `12:23:40.875` ≪ wake `12:23:57.436` (16.56 s) |
| Assistant reply text in client logs | Only `response_len` / UI Routed→DetailText (often under panel — AUD-39) |
| UAC / screensaver / remote vs lock | No client signal today (AUD-08) |
| Crash orphan serve mid-`voice.record` | Not tested |
| Live Sonia through Hermes playback | Developer deferred to S22 track trial |
| Pitch content identity | **Corrected 2026-09-29:** all six `pitch_*.mp3` re-hashed; **no pair shares a SHA-256**. Sonia r10 m2Hz `d06e7aeb…` ≠ p2Hz `e749c3c1…` (same byte *length* 182132, different content). Earlier synthesis note that a pair was “byte-identical” was wrong — it conflated equal file size/duration with equal content. The only historical empty file was Ava `p2Hz` at SHA `e3b0c442…` (0 bytes) before regenerate. |
| L6 clarify question / choices / `srq-*` / `request.cancel` in logs | Not in INFO; need higher log level or client frame logging |
| L6 SPEECH_INTERRUPTED_NOTE after typed Cancel | Source: latch only if TTS stream active; L6 Text+no TTS → likely not latched — **UNVERIFIED** in logs (debug-only stack in `_tts_stream_stop`) |

---

## Listening observations (placement complete)

Recorded verbatim in `Zola_P4PRE_Audit_06_VoiceSamples.md`. Mapped to Phase 4 items 7 / 2 / 8 above with P3-D23 values and Sonia silence vs S17.

---
