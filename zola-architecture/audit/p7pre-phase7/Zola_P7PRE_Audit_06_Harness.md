# P7PRE Audit 06 — Harness Probes

**Scratch:** `C:\Users\test\Dev\zola-spikes\p7pre\`  
**Interpreter:** `C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe`  
**Date:** 2026-10-05

---

## H-2 — Echo guard offline (complete)

**Script:** `zola-spikes\p7pre\scripts\echo_guard_offline.py`  
**Exact rule copy of:** `VoiceController.IsEchoOfLastReply` / `NormalizeEchoWords` / gapped run (client `7d77cb51`).

**Command:**
```
C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe C:\Users\test\Dev\zola-spikes\p7pre\scripts\echo_guard_offline.py
```

**Inputs:** last 40 assistant messages from scratch `state.db` snapshot (≥12 echo-normalized words → **31** used); 10 synthetic genuine utterances; quote-style "yes you said …" + last 6 words.

**Results:**

| Group | n | Drops | Drop rate |
|---|---:|---:|---:|
| Head 4 words of her reply | 31 | 0 | **0.000** |
| Head 8 | 31 | 0 | **0.000** |
| Head 12 | 31 | 8 | **0.258** |
| Middle 8 | 31 | 0 | **0.000** |
| Tail 8 | 31 | 31 | **1.000** |
| Synthetic genuine | 10 | 0 | **0.000** |
| Quote of her last 6 words | 31 | 31 | **1.000** |

**Result:** LEAD-3 confirmed quantitatively. Genuine non-quote speech not dropped in this set. Quoting her tail is always dropped (content false positive risk).

---

## H-1 — Whisper timing and accuracy (complete on L-1)

**Date/time:** 2026-10-05 17:56:24  
**Script:** `zola-spikes\p7pre\scripts\h1_whisper.py`  
**Loader:** `tools.transcription_local._load_local_whisper_model` + `build_local_transcribe_kwargs`  
**Model:** `base` (only cached model)  
**Inputs:** Brian L-1 recordings `L1-1`…`L1-6` — original `.m4a` converted in scratch to 16 kHz mono WAV via already-installed WinGet ffmpeg (no new install). Reference text = the six scripted lines.

**Command:**
```
C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe C:\Users\test\Dev\zola-spikes\p7pre\scripts\h1_whisper.py
```

**Clip durations (s):** 3.69, 3.73, 4.52, 6.17, 6.78, 4.93

### Results by configuration

| Config | Reachable by profile? | Cold load (s) | Median infer (s) | p95 | Max | Median RTF | Median WER | Mean WER |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1. Effective (`device=auto`, `compute=auto`; Hermes kwargs, `beam=5`, `lang=en` via global) | Yes | 4.387 | **0.761** | 1.057 | 1.057 | 0.16 | 0.153 | 0.165 |
| 2. Pinned `cpu` / `int8` | Yes (optional YAML keys) | 1.613* | **0.750** | 0.883 | 0.883 | 0.16 | 0.153 | 0.165 |
| 3. Language pinned `en` (already effective) | Yes (`stt.local.language`) | 0.574* | **0.731** | 0.753 | 0.753 | 0.15 | 0.153 | 0.165 |
| 4. `beam_size=1` (direct override) | **No** — `not reachable by config` | 0.713* | **0.739** | 0.801 | 0.801 | 0.15 | **0.222** | 0.198 |

\*Subsequent loads after config 1; not independent cold starts. True cold for this session ≈ **4.4 s** (config 1).

**Alt models:** none cached besides `Systran/faster-whisper-base`. Candidates `tiny.en` / `base.en` / `small.en` / `distil-*` not run (G-NO-INSTALL).

### Interpretation (facts for S38 candidates)

- Warm STT on these short clips is **~0.73–0.76 s** median — below the earlier log-spliced WAV→`Transcribed` medians (~1.6 s), which also include write/delivery overhead.
- Pinning `cpu`/`int8` and explicit `en` did **not** materially change warm infer or WER on this corpus (global `stt.language=en` already forces English in Hermes kwargs).
- **L-2 live warm** WAV→Transcribed **1857 / 2028 ms** on **4.1 / 5.7 s** audio (same duration band as L1 clips **3.69–6.78 s**). Gap vs H-1 warm infer remains **UNEXPLAINED** without `whisper_infer_start`/`end` (P7PRE-AUD-26). Wake closed during STT; no logged presence/wake CPU contention.
- `beam_size=1` saved essentially **0 ms** median here and **worsened** median WER (0.153 → 0.222). Marked not reachable by config.
- Dominant remaining STT lever still needs a **smaller/en model download** (`P2-D17`) to measure — not present locally.

**Finding P7PRE-AUD-22** updated: H-1 complete; prior “deferred” gap closed for L-1 corpus.
