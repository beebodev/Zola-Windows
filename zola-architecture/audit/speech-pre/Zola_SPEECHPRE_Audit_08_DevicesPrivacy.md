# SPEECH-PRE Audit 08 — Devices, privacy, keys, vendor

Against: VD-4, R1, A14, PR-D02.

---

## 1. Devices

| Concern | Today | Owner must handle |
|---------|-------|-------------------|
| Default-device choice | OS default; ffplay no `-device`; monitor binds multimedia default once | Default render/capture; re-bind on change |
| Device loss | Limited client paths; no WASAPI invalidate recovery in client | `AUDCLNT_E_DEVICE_INVALIDATED` (spike prompt / Part E unproven) |
| Bluetooth output | Brian hears first/last word cut (OBSERVED, Known context); Part G **never ran** | Hidden delay, idle sleep, avoid communications stream (call-mode) |
| Stream lifetime | New ffplay per sentence (closed between) | Part G G2/G3: kept-open vs closed; hold after `playback_finished` |

**Measurements needed (by reference — Part G addendum; do not run):**

- G1 hidden delay vs `IAudioClock`
- G2 start clipping after idle (closed vs kept-open; gaps 0.5–30 s)
- G3 end clipping (0 / 300 / 600 ms hold)
- G4 Julia by ear (cached)
- G5 listening after finish on BT vs `safe_to_listen` / 220 ms tail

**SPEECHPRE-AUD-07** (devices GAP) carried from Phase 2.

---

## 2. Keys

| Item | Evidence |
|------|----------|
| Deepgram key location | `%LOCALAPPDATA%\ZolaClient\secrets\deepgram_api_key` (`deepgram_tts.py:24`; DESIGN_DECISIONS P9-FIX-TTS) |
| Guard rows | Folder + filename block `terminal`/`read_file`/`write_file`/`patch`; `profiles/.../zola-tts` blocks write/patch/terminal; `read_file` of zola-tts folder allowed; `execute_code` not in lists (DESIGN_DECISIONS ~1823) |
| Cartesia key location (G-SECRETS: location only) | `%LOCALAPPDATA%\ZolaClient\secrets\cartesia_api_key.txt` (prompt / SP-D06) |
| Same pattern needed | Guard rows for Cartesia path/name; tools blocked from reading |
| Dev/stable share keys? | PROC1 D5 / PR-D02: separate data roots (`ZolaClient` vs `ZolaClient-dev`). Deepgram path in script is **hardcoded stable** `ZolaClient\secrets` — **[RISK]** |

**SPEECHPRE-AUD-24 [RISK] MEDIUM** — `deepgram_tts.py` KEY_PATH hardcodes stable `ZolaClient\secrets`; Cartesia must not repeat that for PR-D02 isolation (use role data root).

---

## 3. Privacy

| | Today | After owner (immediate reply) |
|--|-------|-------------------------------|
| Leaves PC | Reply **text** to Deepgram TTS | Reply **text** to Cartesia |
| Mic audio | Local faster-whisper (P2-D02 / VD-4) | Local S1+S3 (VD-4); never cloud |
| Codes | Local Zira (R1 / ARCH-36) | Unchanged |

Privacy page: A14 states it must disclose cloud voice provider; last updated 2026-11-06 (phone paragraph). **Cartesia update required before live use** (A14 §6 precondition).

Logs: P7-D08 lengths only; never transcript/reply text (G-LOGS).

**SPEECHPRE-AUD-25 [GAP] MEDIUM** — Privacy page still names Deepgram as cloud voice (A14 table); Cartesia not yet disclosed.

---

## 4. Pandora / Deepgram after change

Places that still depend on Deepgram TTS (retire or keep deliberately):

| Area | Path |
|------|------|
| Profile TEMPLATE | `VOICE_CONFIG.md` `tts.provider: deepgram`, Pandora model, command |
| Live profile (not read) | Same keys historically |
| Command script | `hermes-plugins/zola_tts/deepgram_tts.py` |
| Tests | `hermes-plugins/zola_tts/tests/test_deepgram_tts.py` |
| Decisions / lore | P9-D14 Pandora; SP-D09 supersedes voice identity to Julia |
| Client monitor assumption | ffplay under serve (Deepgram mp3 path) |

**SPEECHPRE-AUD-26 [RISK] LOW** — Deepgram remains wired until profile + plugin + tests are deliberately retired or kept as fallback; SP-D09 already chose Julia.
