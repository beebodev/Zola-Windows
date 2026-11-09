# Zola S51F-PRE — Synthesis

Stage 1 audit for the S51 fix track + live `thinking_sound: false` (S51F-D01).  
Prompt `S51F-PRE_Prompt_v1.0.md` SHA-256 `58d9c461…d27d58e8`. Branch `s51f-pre`.  
No code changes. Crash watch **continues** after this document.

---

## 1. Crash watch so far

| Field | Value |
|-------|-------|
| Watch start | **2026-11-09 11:40:57** local (serve pid 31636 / interpreter 18244; client 28424 @ 11:40:54) |
| Config | `voice.thinking_sound: false` since edit ~10:22; serve after edit |
| `python.exe` Application Error (Id 1000) since watch start | **none** (checked at Phase 7 write) |
| Pre-watch baseline (Phase 1) | last crash 2026-11-09 08:21:50, pid 34996 |

Report again on the fix track. Watch remains active.

---

## 2. Finding table

| ID | Severity | Label | File / locus | Summary |
|----|----------|-------|--------------|---------|
| S51F-AUD-01 | HIGH | [RISK] | `hermes_cli/voice.py` beeps → `sd.play` | Shared play stream still used for listen-start / capture-end beeps |
| S51F-AUD-02 | MEDIUM | [RISK] | beep vs InputStream | End beep can overlap kept-alive mic / wake streams |
| S51F-AUD-03 | LOW | [INFO] | `voice.beep_volume` | Volume 0 silences but still calls PortAudio play |
| S51F-AUD-04 | INFO | [GAP] | logs | No beep breadcrumb; Cue A/B times inferred |
| S51F-AUD-05 | MEDIUM | [MEASURED] | Phase 2 S2 | No pre-tool assistant text; no spoken ack that turn |
| S51F-AUD-06 | MEDIUM | [SOURCE] | `SentenceChunker` min_len=20 | Short pre-tool lines held; no tool-start flush |
| S51F-AUD-07 | INFO | [SOURCE] | `SOUL.md` | Already asks for a few words before slow work; not enforced |
| S51F-AUD-08 | HIGH | [GAP] | `ShowUnreachable` | Restart shown; lost request still not announced (S51 carry) |
| S51F-AUD-09 | MEDIUM | [RISK] | auto-resubmit | Blind replay unsafe for send / calendar write / forget / watch |
| S51F-AUD-10 | INFO | [DESIGN] | Zira vs Pandora | Local speak while serve down is possible; voice identity question |
| S51F-AUD-11 | MEDIUM | [DIAG] | serve env | `PYTHONFAULTHANDLER=1` via client env; partial on native faults |
| S51F-AUD-12 | MEDIUM | [DIAG] | supervisor log | Serve pid not logged on stale/restart |
| S51F-AUD-13 | LOW | [DIAG] | stream sites | No structured PortAudio site events |

**Counts: 13 findings — 2 HIGH, 6 MEDIUM, 2 LOW, 3 INFO.**

---

## 3. Options for the fix track (by area)

### Remaining shared-stream users (beeps)

| Option | Integration | Brian experiences | Risk | Prove with |
|--------|-------------|-------------------|------|------------|
| Leave beeps as-is | none | Keeps "listening" / "got it" cues | Shared `sd.play` remains | Crash watch; optional stress |
| `voice.beep_enabled: false` | config (P4-D25) | No Hermes beeps; loses those cues unless replaced | Losing status cues Brian uses | Ear smoke after apply |
| `beep_volume: 0` | config (P4-D25) | Silent cues; PortAudio still touched | False sense of "stream gone" | Code review + smoke ear |
| Route beeps via ffplay/tempfile on Windows | Hermes source | Same cues, non-PortAudio | Latency / path bugs | Unit + live smoke |
| Disable Hermes beeps; client plays cues | Zola + `beep_enabled: false` | Cues if client implements | Cue loss if only disable | Scripted listen start/end |
| Disable specific cue (start vs end) | Hermes source (no per-cue config today) | Brian picks which signal to keep | Losing a needed status cue | Brian A/B ear test |

### Mic stream lifecycle

| Option | Integration | Brian | Risk | Prove |
|--------|-------------|-------|------|-------|
| Serialize close vs callback more strictly | Hermes source | Invisible if correct | Deadlocks / hung close | Stress record/wake |
| Breadcrumb open/close | Hermes source (diag) | None | Log volume | Match next dump |

### Pre-tool acknowledgement

| Option | Integration | Brian | Risk | Prove |
|--------|-------------|-------|------|-------|
| SOUL wording only (P4-D25 identity; no draft here) | identity | May hear her own short line more often | Model may still skip or emit &lt;20 chars | Tool-heavy smoke |
| Flush TTS chunker on tool start | Hermes source | Held short lines can speak before wait | Speaking mid-tool policy | S2-like calendar smoke |
| Zola non-speech cue at tool start | Zola client/plugin | Knows work started without canned phrase | Not "her words" | UI/timeline check |

### Lost-request handling

| Option | Integration | Brian | Risk | Prove |
|--------|-------------|-------|------|-------|
| (a) Conversation line | Zola client | Sees request dropped | Wording/privacy | Kill-serve drill (Brian) |
| (b) Spoken notice when back | Zola ± model | Hears it | Wrong voice if Zira; authority if auto-prompt | Same drill |
| (c) Auto-resubmit | Avoid as default | Replay | Consequential duplicate actions | Fail-closed review vs P8-D06 |

### Diagnostics

| Option | Integration | Brian | Risk | Prove |
|--------|-------------|-------|------|-------|
| `PYTHONFAULTHANDLER=1` on spawn | Zola client env | None day-to-day | Slightly larger stderr | Forced Python fault in lab only |
| Log serve pids on restart/stale | Zola client | None | — | Supervisor line after restart |
| Stream-site log events | Hermes source | None | Privacy if over-logged (event names only) | Correlate with dump |

---

## 4. Decisions Brian needs to make

1. **Beep cues:** Keep listen-start (880×1), keep capture-end (660×2), keep both, turn off with supported `voice.beep_enabled: false`, silence-only via `beep_volume: 0` (still PortAudio), or move off PortAudio — given what each tells him?
2. **Pre-tool acknowledgement:** SOUL-only nudge, invest in Hermes flush/hook, Zola non-speech cue, or accept silence during tools for now?
3. **Lost request:** Visible line (a), spoken notice (b), neither until after PortAudio work, or (c) auto-resubmit despite fail-closed risks?
4. **If spoken while serve down is ever used:** Is Zira acceptable for that one line, or wait for Pandora after restart?
5. **Diagnostics now vs with the fix:** Enable faulthandler + pid logging on the client in this track's follow-on, or bundle later?

---

## 5. Out of scope noticed (INFO → known-issues / speech track)

| Item | Note |
|------|------|
| Mic button not interrupting a reply | Known; barge_in false |
| Stop Speaking unavailable on unprompted lines | Known |
| Self-echo | See Phase 2 S1 cluster below |
| Clipped opening words | Speech-baseline SYM-02 |

### Phase 2 S1 self-echo turns (record for known-issues list)

After S1 no-tool turn (`turn_timing turn=1`, tools=0), two follow-up captures were **admitted as full voice turns** (Brian: she overheard herself twice). No transcript text recorded here (G-LOGS).

| Client turn | Approx submit window | transcript len | tools | Admitted? |
|-------------|----------------------|----------------|-------|-----------|
| 2 | ~11:45:54 | **59** | 0 | **Yes** (`turn_timing turn=2`, kind=voice) |
| 3 | ~11:46:10 | **26** | 0 | **Yes** (`turn_timing turn=3`, kind=voice) |

Belong on the speech / known-issues list — not the PortAudio fix scope.

---

## 6. Live change already applied (not a promotion)

| Item | Value |
|------|-------|
| `thinking_sound` | `false` (backup `config.yaml.bak-S51F-20261109-102200`) |
| config SHA | `823dbd95…` → `8ea0f37d…` |
| `VOICE_CONFIG.md` SHA | `4a09790788660f7132f07d0f4b0e109aeb4f630276dc63c3b2fa18dea929cb58` |
| S2 "Let me look" before tool | **no** (MEASURED) |

---

*End of synthesis. STOP for Brian / Claude review before the fix prompt.*
