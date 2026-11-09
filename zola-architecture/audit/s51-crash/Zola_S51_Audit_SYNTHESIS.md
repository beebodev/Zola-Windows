# Zola S51 Audit — SYNTHESIS

Phase 6 STOP (corrected after Brian review, 2026-11-09). Diagnostic only.  
Prompt SHA `b6a6f89820bc120bd0179373bcfaddb1c933499acf99895b78b17d6b1a085293`.  
Base `main` `92e6cc473ae69d7dac88695229b58f24d0167cfb`. hermes-agent pin `345cd2b…`.  
Build under discussion for stability gate: speech-baseline tag **`p10-closed`** (`898b1e6…`) on Brian’s PC during 2026-11-09 crashes.

---

## Brian verdicts (verbatim decisions, recorded)

1. **No Python PDB acquisition.**
2. **Group A blocks Phase 11 under PR-D03;** a fix track comes next.
3. **Fix track priority:** PortAudio crash first, with the **lost-request announcement in the same track**; sqlite and the `0x3b1ff` class get **diagnostics** (`faulthandler`, serve pid logging) rather than a fix for now.

---

## 1. Answers to the six questions

### Q1 — Which process crashed each time?

**EVIDENCE:** Of 43 Application Error rows: **10** are `Zola.Client.exe` (UI); **33** are `python.exe`. Among python rows with log identity: **none** matched watcher/phone `job_assigned` pids; **~29** classified as **serve (interpreter pid)** via `store_open` and/or serve `stale`/`restart` (Phase 2). Preserved dumps **27712, 29172, 39848, 34996, 43840** (and **28836** by signature/size) are serve interpreters.  
**UNRESOLVED:** a few early python rows without supervisor/memory coverage; launcher vs interpreter sibling pid (supervisor does not log serve pid).  
**Counts:** serve ~29 / watcher 0 / zola-phone 0 / Zola.Client 10 / UNRESOLVED ~4.

### Q2 — Where did it crash?

**EVIDENCE (dumps, Phase 3):**
- **Group A (5 dumps):** A PortAudio **internal stream thread** transferred control to an **unbacked** address (AE module `unknown`). Three dumps: illegal instruction `0xc000001d` (27712, 28836, 43840); two: AV `0xc0000005` (39848, 34996). Frame strings such as `Pa_WriteStream+0x131c` / `PaWasapi_UpdateDeviceList+0x13d43` are **nearest exports only** (no PortAudio PDB) — not identified real functions. Stream direction (**input vs output**) is **UNRESOLVED**.
- **INFERENCE:** Consistent with a stream callback that was **freed or replaced** while PortAudio’s thread still used it.
- **Group B (1 dump, 29172):** `0xc0000005` in `python312!PyObject_Vectorcall` with `_sqlite3` frames. Role: **eval + sqlite** (**INFERENCE**).

**EVIDENCE (event log):** full python.exe signature table in Phase 02 (21 signatures). See also §3a below.

### Q3 — What was Zola doing?

**EVIDENCE:** 2026-11-09 A11/B6 — Thinking/Speaking / reply-generation; unreachable; serve restart. Other serve crashes often near voice markers when extracts exist.  
**INFERENCE:** Group A co-occurs with voice activity; Hermes may have had play and/or InputStream PortAudio streams live — which one faulted is **UNRESOLVED**.

### Q4 — How many distinct causes?

**EVIDENCE:** at least **two** dump-proven signatures (Group A PortAudio stream-thread → unbacked; Group B python312/sqlite).  
**INFERENCE:** AE-only classes (`python312+0x3b1ff`, `ntdll`, `_ctypes`) may be further causes — **UNRESOLVED** without dumps.  
Zola.Client Xaml cluster: separate client issue (INFO).

### Q5 — What changed around 2026-10-04/05?

**EVIDENCE:** first python AE **2026-10-05 11:13:49**; packages/PortAudio DLL **2026-09-23** (predate); no HotFix/driver on 10-04/05.  
**UNRESOLVED:** onset trigger; early AE `python312`/`ntdll` may differ from Group A.

### Q6 — What happens to Brian’s request when serve dies?

**EVIDENCE:** unreachable; status **“Zola's backend stopped. Restarting…”**; abandon clarify; fail-closed voice; serve restart (P9-D02 **[MATCH]**); no turn retry in that handler.  
**[GAP]/[RISK]:** no lost-request/answer announcement (Brian: include announcement in the PortAudio fix track).

---

## 2. Finding summary

| ID | Sev | Label | Where | Summary |
|----|-----|-------|-------|---------|
| S51-AUD-01 | MED | [MATCH] | supervisor / `ProcessSupervisor` | Serve restarts after unexpected exit. |
| S51-AUD-02 | HIGH | [GAP]/[RISK] | `ShowUnreachable` / status strings | Restart status shown; lost in-flight reply not announced or retried. |
| S51-AUD-03 | HIGH | [RISK] | `libportaudio64bit` (export labels only) | Group A: PortAudio stream thread → unbacked address; in vs out **UNRESOLVED**; both 2026-11-09 crashes. |
| S51-AUD-04 | MED | [RISK] | `python312` + `_sqlite3` dump 29172 | Second dump signature (~7.5 MB). Diagnostics-only per Brian. |
| S51-AUD-05 | MED | [GAP] | uv CPython PDB | Matching PDBs not found; **no acquisition** (Brian). |
| S51-AUD-06 | MED | [GAP] | Phase 4 | Onset ~2026-10-05 still UNRESOLVED. |
| S51-AUD-07 | HIGH | [RISK] | `voice_mode.py` / `wake_word.py` stream sites | Multiple PortAudio streams possible concurrently; shared `sd.play`/`sd.stop` ([EXT]); Group A owner stream UNRESOLVED. |
| S51-AUD-08 | LOW | [GAP] | S52 vs Phase 3 | S52 not matched to preserved dump groups. |

**Totals: 8 findings — 3 HIGH, 4 MEDIUM, 1 LOW.**

---

## 3. Crash groups (ranked)

| Rank | Group | Count (dumps) | Recency | Known | Unknown |
|------|-------|---------------|---------|-------|---------|
| 1 | A — PortAudio stream thread → unbacked | 5 | 2026-11-09 | Unbacked RIP; export-relative PortAudio frames; serve; mid-reply on 11-09 | Real functions; **input vs output**; which Hermes site |
| 2 | B — python312/`_sqlite3` | 1 | 2026-10-17 | Stack; serve | Link to AE `sqlite3.dll` rows |
| 3 | AE `python312+0x3b1ff` | 10 AE, 0 dumps | 2026-10-05 → **2026-11-04** | Event-log only | Dump stack |
| 4 | AE `ntdll` silence/STT | 1 AE | 2026-10-06 | Lore S51/S52 | Dump gone |
| 5 | Other AE | few | Oct–Nov | Event-log | — |
| — | Zola.Client Xaml | 10 AE | Sep–Oct | UI | No dumps |

### 3a. python.exe AE signatures vs PortAudio class

Full table: Phase 02. **EVIDENCE:** first AE `unknown` (Group A family): **2026-10-16**. First AE `libportaudio64bit.dll`: **2026-11-02**. The **`python312.dll` / `0xc0000005` / `0x3b1ff` class still occurs after** that — last seen **2026-11-04 11:04:01**.

---

## 4. Stability gate (PR-D03) — per signature

| Signature | Relevance verdict | Still in current code? |
|-----------|-------------------|------------------------|
| Group A PortAudio stream → unbacked | **observed on this build** — dumps **39848** & **34996** on 2026-11-09 on **`p10-closed`** | **yes** — PortAudio/`sounddevice` stream sites still in pin (`voice_mode.py`, `wake_word.py`). **Brian: blocks Phase 11.** |
| Group B python312/sqlite | observed in lineage (2026-10-17); not in 11-09 dumps | path present; **diagnostics only** (Brian) |
| AE `python312+0x3b1ff` | **UNRESOLVED** (no dump); still seen after PortAudio class appears | **diagnostics only** (Brian) |
| AE `ntdll` / S52 | **not observed in available dump evidence** | UNRESOLVED |
| Zola.Client Xaml | not a serve stability blocker for Phase 11 | separate |

---

## 5. Fix track decisions (Brian)

Already decided:
1. PortAudio Group A is the **fix** (blocks Phase 11).  
2. **Lost-request announcement** ships in the **same** track.  
3. Sqlite / `0x3b1ff`: **diagnostics** (`faulthandler`, serve pid logging) — not a fix in this track.  
4. No Python PDB work.

Still for the fix track to choose (design, not this audit):
- Upstream Hermes vs local policy for stream lifetime / avoiding unsafe stop-replace.  
- How to announce a lost in-flight turn (copy/UX).  
- Whether S52 is a separate track.

---

## 6. Evidence still missing

| Gap | Next capture (proposal) |
|-----|-------------------------|
| Serve pid (launcher + interpreter) | Supervisor log fields |
| Which stream was live at fault | faulthandler + stream-site breadcrumb (in/out, wake/record/play) |
| `0x3b1ff` / sqlite dumps | Preserve before 14-day prune; faulthandler |
| PortAudio real functions | Would need PortAudio symbols (not pursued) |
| Onset dumps 2026-10-05 | Gone |

**INFERENCE:** With `voice.thinking_sound: true`, the shared `sd.play` stream is used mainly by the thinking-sound loop and beeps; both 2026-11-09 crashes fell in the Thinking/reply-generation window.

---

## 7. Open questions

None blocking review: Brian’s three verdicts are recorded. Closeout proceeded on **`proceed to closeout`**.

---

## Tool / privacy notes

- WinDbg/`cdb` approved command only; scratch only.  
- No register values / memory / strings from dumps in documents.  
- PortAudio frame names = nearest exports only.  
- minidump fallback not used.
