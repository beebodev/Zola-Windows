# P4PRE Audit — Progress

**Audit ID:** P4PRE  
**Scope:** S32 (voice while Windows locked), S20 (clarify), S22 (voice naturalness)  
**Type:** Read-only diagnostic; two developer live checks; scratch spike outside both repos  
**Started:** 2026-09-29

---

## Repositories

| Repo | Path | Branch | HEAD SHA | Notes |
|------|------|--------|----------|-------|
| zola-windows (audited) | `C:\Users\test\Dev\zola-windows` | `audit/p4pre-conversation` | `504ae768b3097c6c16b5d9a387bdbe5a2391bdad` | Handoff expected `159646b312b558430cca77560169347354c891e0` (P3 lore merge). Actual approved base is tip `504ae76…` — one closeout SHA-record commit ahead (`docs: record P3-LORE merge SHA`, touches only `P3-LORE_Progress.md`). Parent confirmed `159646b…`. Developer-approved 2026-09-29. |
| hermes-agent (read-only) | `C:\Users\test\Dev\hermes-agent` | detached `v2026.9.14` | `345cd2b057a452236de401d3534b8502a7465e8d` | `git status --porcelain` empty at Phase 1 start. Never edited. |

**Output directory:** `zola-architecture/audit/p4pre-conversation/`  
**Spike folder (outside both repos, never committed):** `C:\Users\test\Dev\zola-spikes\p4pre-voice\`

---

## Phase status

| Phase | Name | Status |
|-------|------|--------|
| 1 | Setup | COMPLETE |
| 2 | Lock Surface Map (S32) | COMPLETE → `Zola_P4PRE_Audit_02_LockSurface.md` |
| 3 | Clarify and Server-Request Protocol (S20) | COMPLETE → `Zola_P4PRE_Audit_03_Clarify.md` |
| 4 | TTS Providers, Keys, and Playback Paths (S22) | COMPLETE → `Zola_P4PRE_Audit_04_TtsPaths.md` |
| 5 | Developer Live Checks | COMPLETE → `Zola_P4PRE_Audit_05_LiveChecks.md` |
| 6 | Voice Sample Set and Edge Measurements | COMPLETE → `Zola_P4PRE_Audit_06_VoiceSamples.md` |
| 7 | Synthesis | COMPLETE → `Zola_P4PRE_Audit_SYNTHESIS.md` |
| 8 | Closeout | IN PROGRESS |

---

## Guardrails summary

| ID | Rule | Status |
|----|------|--------|
| G-SCOPE | Diagnostic only; audit docs + spike folder | In force |
| G-NOCHANGE | Zero source mods in zola-windows outside output dir; never edit hermes or live profile | In force |
| G-ARCH | Architecture/lore are truth; conflicts = findings; no silent decisions | In force |
| G-QUALITY | Every finding names file/class/method/lines or log/config/number | In force |
| G-CLOSEOUT | Closeout only after explicit `proceed to closeout` | Satisfied 2026-09-29 |
| G-NO-CROSS-SCOPE | Android out of scope | In force |
| G-DEPS | No installs; only hermes venv python + existing packages | In force |
| G-SECRETS | Credentials recorded present/absent or redacted | In force |
| G-SINGLE-CLIENT | No second WS to hermes serve | In force |
| G-HUMAN-CHECK | Stop at Phase 5 and Phase 6 for developer replies | Both stops done |
| G-EVIDENCE | Live/measured claims need evidence; else UNVERIFIED | In force |

---

## Spike command log

| Command | Working directory | Exit code | Notes |
|---------|-------------------|-----------|-------|
| `python generate_samples.py` (first) | `C:\Users\test\Dev\zola-spikes\p4pre-voice` | 1 | `NoAudioReceived` mid-run; partial `v_*` written |
| `python generate_samples.py` (resume) | same | 0 | 9 voices × 2 rates; chunks; shape; pitch attempt |
| `edge-tts --pitch=-2Hz/+2Hz` ×4 | same | 0 | Aria + AvaMultilingual pitch samples |
| `python measure_aria.py` | same | 0 | Aria latency n=10 per rate |
| WPS backfill over `_sent_*.mp3` | same | 0 | 18 voice×rate medians |
| `edge-tts --pitch=-2Hz/+2Hz` ×4 (regenerate all pitch) | same | 0 | Fix empty Ava p2Hz; ensure m2Hz both voices |
| `rebuild_index.py` (ffprobe verify all mp3 + INDEX) | same | 0 | FAIL_COUNT 0; 42 listening files |
| `python sonia_r10_deeper.py` | same | 0 | Sonia +10% chunk/pitch/shape; 8 new files |
| `rebuild_index.py` (after Sonia deeper) | same | 0 | FAIL_COUNT 0; INDEX includes Sonia r10 set |

---

## Phase 1 evidence snapshot

### Tip-commit approval check

```
git show --stat 504ae768b3097c6c16b5d9a387bdbe5a2391bdad
→ 1 file: zola-architecture/lore/prompts/progress/P3-LORE_Progress.md (| 2 +-)
git rev-parse 504ae76…^ → 159646b312b558430cca77560169347354c891e0
```

### Lore files present

- `zola-architecture/lore/ROADMAP.md` — present  
- `zola-architecture/lore/DESIGN_DECISIONS.md` — present  
- `zola-architecture/lore/OPEN_QUESTIONS.md` — present  

### Live profile (`%LOCALAPPDATA%\hermes\profiles\zola\config.yaml`)

- **mtime (Phase 1):** `2026-09-23T15:32:27.1953228-07:00`  
- **`.env` file:** absent at profile root  
- **Sections present (non-secret values):**

| Section | Values |
|---------|--------|
| `model` | `provider: openai-codex`, `base_url: https://chatgpt.com/backend-api/codex`, `default: gpt-5.6-terra` |
| `agent` | `reasoning_effort: medium` — **no** `clarify_timeout` |
| `memory` | `memory_char_limit: 4400`, `user_char_limit: 2750` |
| `stt` | `provider: local`, `local.model: base` |
| `tts` | `provider: edge`, `edge.voice: en-US-AriaNeural` — **no** `edge.speed` / `tts.speed` |
| `voice` | `silence_duration: 1.5`, `barge_in: true`, `stop_phrases: ["stop"]`, `thinking_sound: true` |
| `wake_word` | `enabled: true`, `provider: sherpa`, `phrase: "hey zola"`, `capture: local`, `surface: auto`, `start_new_session: false`, `profile_routing: false`, `sensitivity: 0.6` |
| `security` | `allow_lazy_installs: false` |
| `clarify` | **absent** (effective timeout → Hermes default 3600 via `resolve_clarify_timeout`) |
| `approvals` | **absent** |

- **`nous` managed provider:** not configured as active. Comments mention `nous` as a possible fallback OAuth provider; `fallback_model` is commented out. Active auth is `openai-codex` OAuth tokens in `auth.json` (token values recorded only as `present`).

### API-key presence (process/user/machine env + auth.json structure)

| Key / credential | Presence |
|------------------|----------|
| `ELEVENLABS_API_KEY` | absent |
| `OPENAI_API_KEY` | absent |
| `GEMINI_API_KEY` / `GOOGLE_API_KEY` | absent |
| `XAI_API_KEY` | absent |
| `MINIMAX_API_KEY` | absent |
| `MISTRAL_API_KEY` | absent |
| `auth.json` `providers.openai-codex.tokens.*` | present (OAuth; values not copied) |
| `auth.json` `nous` provider block | absent |

### Installed / importable (Hermes venv `…\hermes-agent\.venv\Scripts\python.exe`)

| Package | Result |
|---------|--------|
| `edge_tts` | **7.2.7** |
| `sounddevice` | **YES** (`0.5.5`) |
| `elevenlabs` | NO |
| `piper` | NO |
| `neutts` | NO |
| `kittentts` | NO |
| `ffplay` / `ffmpeg` | Binaries present at `%LOCALAPPDATA%\Microsoft\WinGet\Links\ffplay.exe` / `ffmpeg.exe` (Gyan 9.0.2). **Not on PATH of this audit shell** (`shutil.which` → None). Per `VOICE_CONFIG.md`, serve inherits PATH at launch; P2-D16 spoken replies require ffplay on the serve process PATH. |

### Log locations (from P3-LIFE / client constants)

| Log | Path |
|-----|------|
| Client voice timeline | `%LOCALAPPDATA%\ZolaClient\logs\voice-timeline.log` |
| Client display state | `%LOCALAPPDATA%\ZolaClient\logs\display-state.log` |
| Client presence | `%LOCALAPPDATA%\ZolaClient\logs\presence.log` |
| Hermes profile serve | `%LOCALAPPDATA%\hermes\profiles\zola\logs\` (`agent.log`, `gui.log`, `errors.log`) |
| Hermes root logs | `%LOCALAPPDATA%\hermes\logs\` (older / non-profile) |

---

## Documents produced

| File | Phase |
|------|-------|
| `Zola_P4PRE_Audit_PROGRESS.md` | 1 (this file) |
| `Zola_P4PRE_Audit_02_LockSurface.md` | 2 |
| `Zola_P4PRE_Audit_03_Clarify.md` | 3 |
| `Zola_P4PRE_Audit_04_TtsPaths.md` | 4 |
| `Zola_P4PRE_Audit_05_LiveChecks.md` | 5 |
| `Zola_P4PRE_Audit_06_VoiceSamples.md` | 6 |
| `Zola_P4PRE_Audit_SYNTHESIS.md` | 7 |

---

## Running findings list

| ID | Severity | Scope | File/log | One-line summary |
|----|----------|-------|----------|------------------|
| P4PRE-AUD-01 | HIGH | [S32] [RISK] | `PresenceView.cs` L211–215 | Lock pauses presence only; voice continues |
| P4PRE-AUD-02 | — | [S32] [MATCH] | `SessionLockWatcher.cs` L81–104 | WTS lock/unlock events correct |
| P4PRE-AUD-03 | HIGH | [S32] [GAP] | Voice/display | No queryable lock fact for voice/HUD |
| P4PRE-AUD-04 | — | [X] [MATCH] | `VoiceController` chain | Client drives wake→record→submit |
| P4PRE-AUD-05 | MEDIUM | [S32] [RISK] | Hermes TTS/barge | In-flight speech continues without lock gate |
| P4PRE-AUD-06 | — | [S32] [MATCH] | `wake.pause` | Releases mic device |
| P4PRE-AUD-07 | MEDIUM | [S32] [GAP] | `ZolaDisplayState.cs` | No lock-specific mic/HUD line |
| P4PRE-AUD-08 | MEDIUM | [S32] [RISK] | `SessionLockWatcher` | Cannot tell lock from UAC/screensaver/remote |
| P4PRE-AUD-09 | — | [S32] [MATCH] | `HermesProcessManager` / WS teardown | Orphan serve does not keep wake armed |
| P4PRE-AUD-10 | LOW | [S32] [GAP] | WTS remote codes | Suspend/remote not in voice privacy policy |
| P4PRE-AUD-11 | — | [S20] [MATCH] | `server_requests.py` | Clarify is `srq-*` request + response frame |
| P4PRE-AUD-12 | HIGH | [S20] [GAP] | `ChatSocket.cs` L500–504 | All server requests dropped |
| P4PRE-AUD-13 | HIGH | [S20] [RISK] | profile + `resolve_clarify_timeout` | 3600 s stall / Thinking |
| P4PRE-AUD-14 | — | [S20] [MATCH] | `clarify_tool.py` | Clarify enabled on serve |
| P4PRE-AUD-15 | HIGH | [X] [RISK] | approval drop | Dangerous cmds deny ~300 s unseen |
| P4PRE-AUD-16 | MEDIUM | [S20] [GAP] | `ZolaDisplayState` | No CLARIFICATION_PENDING / HUD |
| P4PRE-AUD-17 | MEDIUM | [S20] [GAP] | `ChatSocket` resume | `open_requests` unread |
| P4PRE-AUD-18 | — | [S20] [MATCH] | contracts / shared TS | Generic boundary supported |
| P4PRE-AUD-19 | MEDIUM | [S20] [RISK] | `VoiceController`/`MainWindow` | Transcripts ≠ clarify answers |
| P4PRE-AUD-20 | — | [S22] [MATCH] | profile TTS | Edge AriaNeural matches P2-D03 |
| P4PRE-AUD-21 | MEDIUM | [S22] [GAP] | `_generate_edge_tts` | pitch/volume not passed |
| P4PRE-AUD-22 | — | [S22] [MATCH] | command provider | CLI can set pitch/volume |
| P4PRE-AUD-23 | — | [S22] [MATCH] | Edge+ffplay | P3-D23 PASS |
| P4PRE-AUD-24 | HIGH | [S22] [RISK] | streamers | P3-D23 BREAK (ffplay-only monitor) |
| P4PRE-AUD-25 | MEDIUM | [S22] [RISK] | `VoiceController` P2-D15 | Rate/provider invalidates constants |
| P4PRE-AUD-26 | MEDIUM | [S22] [GAP] | Hermes→client | No end-of-playback RPC (S17) |
| P4PRE-AUD-27 | — | [S22] [MATCH] | `allow_lazy_installs: false` | Premium needs explicit install |
| P4PRE-AUD-28 | LOW | [S22] [GAP] | agent prompts | No voice-mode system slot |
| P4PRE-AUD-29 | LOW | [S22] [RISK] | SentenceChunker | Per-sentence synth flattens intonation |
| P4PRE-AUD-30 | HIGH | [S32] [RISK] | live L1 | Wake+answer at lock — evidence for AUD-01 |
| P4PRE-AUD-31 | MEDIUM | [S32] [RISK] | live L2 | Speech+follow-up while locked — evidence for AUD-05 |
| P4PRE-AUD-32 | — | [S32] [MATCH] | live L3 | Text mode no wake on lock |
| P4PRE-AUD-33 | MEDIUM | [S20] [RISK] | live L4/L5 | Natural-language ask; clarify tool unused |
| P4PRE-AUD-34 | MEDIUM | [S20] [RISK] | live L6 | Clarify ~84 s; drop path exercised |
| P4PRE-AUD-35 | MEDIUM | [S22] [RISK] | spike silence | Trailing silence ~0.74–1.17 s (S17) |
| P4PRE-AUD-36 | LOW | [S22] [RISK] | spike WPS | Aria ~3.9 WPS vs P2-D15 2.5 |
| P4PRE-AUD-37 | MEDIUM | [S20] [RISK] | L5 follow-up | Spoken answer to plain-text Q can be lost |
| P4PRE-AUD-38 | MEDIUM | [X] [RISK] | tool.* events | Long tool turns look like a stall |
| P4PRE-AUD-39 | MEDIUM | [S20][X] [RISK] | Notice Z-order | Status/Detail under Conversation panel |

**Counts so far:** 39 findings — HIGH 7, MEDIUM 16, LOW 4, MATCH 12

Phases 1–7 COMPLETE (correction round L1b/L6 done). Listening observations: **recorded**.  
Decisions needed (Synthesis §5): **16**.  
**Final findings:** 39 — 7 HIGH, 16 MEDIUM, 4 LOW, 12 MATCH.

### Closeout 8a (2026-09-29)

- `git status`: changes only under `zola-architecture/audit/p4pre-conversation/` (untracked audit docs).
- hermes-agent: clean @ `345cd2b057a452236de401d3534b8502a7465e8d`.
- Live profile `config.yaml` mtime unchanged: `2026-09-23T15:32:27.1953228-07:00`.
- Spike folder not staged.
