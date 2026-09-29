# P4PRE Audit 06 — Voice Sample Set and Edge Measurements (S22)

**Audit ID:** P4PRE  
**Spike folder (not committed):** `C:\Users\test\Dev\zola-spikes\p4pre-voice\`  
**Index:** `C:\Users\test\Dev\zola-spikes\p4pre-voice\INDEX.md`  
**Hermes venv:** `edge_tts` 7.2.7; `ffmpeg`/`ffprobe` via WinGet Links (Gyan 9.0.2)

---

## Voice inventory

| Item | Value |
|------|-------|
| `en-US` + `en-GB` voices listed | **22** (`voices.txt`) |
| Candidate list | All present (none missing) |
| Extra en-US female added | `en-US-AnaNeural` (only one additional matched the multilingual/newer filter beyond the fixed list) |
| Voices synthesized | Aria, Jenny, Ava, AvaMultilingual, Emma, EmmaMultilingual, Michelle, Sonia (en-GB), Ana |

---

## Sample files

Non-underscore `*.mp3` count: **42** (full scripts × voice × rate, chunk comparisons, shape, pitch).

Rates: `r0` = Edge `+0%` (Hermes speed 1.0); `r10` = `+10%` (speed 1.1).  
Join gaps: **110 ms** between sentences (P3-D23 median), **800 ms** between script lines.

Pitch via `edge-tts` CLI (`--pitch=-2Hz` / `+2Hz`): produced for Aria and AvaMultilingual (command-provider path viable — Phase 4 AUD-22). Initial `-2Hz` failed under PowerShell arg parsing; re-run with `--pitch=-2Hz` succeeded.

Shaping texts:
- Unshaped (after Hermes `prepare_spoken_text`): see `shape_unshaped.txt` — markdown stripped; `~` → `about`.
- Shaped: L4 script line → `shape_shaped.mp3` (per-sentence).

Hashes: see `INDEX.md` (SHA-256 per listening file).

---

## Measurements (this machine)

### Synth latency — `en-US-AriaNeural`, 10 sentences/rate

Computed with `time.perf_counter()` around `Communicate(...).save()` in `measure_aria.py` (wall-clock to file saved). **Independent of** silence measurement (which uses `ffmpeg silencedetect` on already-written MP3s).

| Rate | n | median (s) | min (s) | max (s) |
|------|---|------------|---------|---------|
| `+0%` | 10 | **0.739857** | 0.700563 | 0.829789 |
| `+10%` | 10 | **0.805068** | 0.730650 | 2.477145 |

Spot-check (3 fresh Aria +0% synths, separate run): `[0.810, 0.725, 0.722]` s — same order of magnitude, not tied to silence values.

Note: this is **request→file saved** for one sentence, not end-to-end first-audio including ffplay start (P2-D15 FirstSentenceLatency 3.3 s remains a different clock).

### Silence (`ffmpeg silencedetect=noise=-45dB:d=0.05`) — 132 sentence MP3s from full scripts

Computed only from audio analysis of `_sent_*.mp3` files (leading/trailing from silence_start/end vs duration). **Not** taken from synth timers.

| | median (s) | max (s) |
|--|------------|---------|
| Leading | 0.170 | 0.233 |
| **Trailing** | **0.740125** | **1.169875** |

The synth-latency median (~0.740 s) and trailing-silence median (~0.740 s) matching to three decimals is **coincidence** of two independent distributions (wall-clock vs audio silence), not a shared variable.

**S17 relevance:** median trailing silence **~0.74 s**, max **~1.17 s** inside sentence MP3s while ffplay session stays Active — consistent with lore “mouth moves ~1 s after audible speech ends.”

### Words/sec (audio duration minus silences)

| Voice | +0% median WPS | +10% median WPS |
|-------|----------------|-----------------|
| en-US-AriaNeural | 3.89 | 4.30 |
| en-US-JennyNeural | 4.03 | 4.43 |
| en-US-AvaNeural | 3.92 | 4.31 |
| en-US-AvaMultilingualNeural | 3.83 | 4.14 |
| en-US-EmmaNeural | 3.74 | 4.11 |
| en-US-EmmaMultilingualNeural | 3.84 | 4.17 |
| en-US-MichelleNeural | 4.18 | 4.61 |
| en-US-AnaNeural | 3.25 | 3.57 |
| en-GB-SoniaNeural | 3.55 | 3.89 |

**P2-D15:** client `EstimatedWordsPerSecond = 2.5` is **below** measured Aria ~3.9 WPS at +0% — follow-up clock would fire early relative to true speech if estimate-only; `P3-D23` observed playback is the corrective path for mouth, but follow-up still uses the estimate.

Finding cross-ref: strengthens **P4PRE-AUD-25** / **AUD-26** / S17 silence note.

---

## Commands (spike log; also in PROGRESS)

| Command | cwd | Exit |
|---------|-----|------|
| `python generate_samples.py` (first run; failed mid-Emma NoAudioReceived) | spike | 1 |
| `python generate_samples.py` (resume + retries) | spike | 0 |
| `edge-tts --pitch=-2Hz/+2Hz …` (4 pitch files) | spike | 0 |
| `python measure_aria.py` | spike | 0 |
| WPS backfill from `_sent_*.mp3` | spike | 0 |

---

## Developer listening observations

Marked as **developer evidence** (not `[MATCH]` / `[GAP]` / `[RISK]` rankings).

```
voice samples:
Pick: en-GB-SoniaNeural at +10% (Hermes speed 1.1). Set on this voice.
The British accent is intentional.
Preferences, all judged on the Sonia r10 samples (developer evidence,
not decisions — feasibility is for the synthesis to report):
- Whole over split: whole-line synthesis sounds more natural than
  sentence-by-sentence (chunk_en-GB-SoniaNeural_r10_L2/L4).
- Shaping: definitely shaped (shape_sonia_r10_shaped over _unshaped).
- Pitch: -2Hz preferred (pitch_en-GB-SoniaNeural_r10_m2Hz).
Others out: Aria (current baseline), Jenny, Ava, AvaMultilingual, Emma,
EmmaMultilingual, Michelle — Sonia was the clear fit. Ana not
considered (child voice).
Note: judged on laptop speakers from offline files. Final voice to be
confirmed in a live trial through Hermes playback during the S22 track.
```

Preferences for synthesis mapping (Phase 4):
- whole-line → item 7 (larger chunks without Hermes source edits; latency-to-first-audio)
- −2Hz → item 2 (command-provider pitch viability)
- shaping → item 8 (identity/prompt files)
Include P3-D23 PASS/ADAPT/BREAK for implied playback paths; Sonia r10 trailing silence median **0.387 s** vs corpus **0.740 s** against S17.

---

## Findings from measurements only (not preference rankings)

| ID | Label | Severity | Scope | Summary |
|----|-------|----------|-------|---------|
| P4PRE-AUD-35 | [RISK] | MEDIUM | [S22]/S17] | Trailing silence median 0.74 s / max 1.17 s in Edge sentence MP3s |
| P4PRE-AUD-36 | [RISK] | LOW | [S22] | Measured Aria WPS ~3.9 vs P2-D15 constant 2.5 |

No subjective voice ranking in this document.

---
