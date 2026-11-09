# Zola S51F-PRE — 04 Better evidence next time

Phase 6. Labels **SOURCE** / **EVIDENCE** / **[EXT]** / **INFERENCE** / **UNRESOLVED**. G-NO-FIX.

---

## 1. Python faulthandler for serve

| Question | Answer | Label |
|----------|--------|-------|
| Can the client enable it via env it already passes? | Client already sets serve child env (`HERMES_HOME`, `PYTHONUNBUFFERED`, `PYTHONPATH`, …) in `HermesProcessManager.cs` ~L245–254. Adding `PYTHONFAULTHANDLER=1` is the **same supported mechanism** (client launch env) — **no Hermes source required** | SOURCE |
| Where would output go? | Serve stderr is redirected into rotating `serve-stderr.log` (P9-D02: `ServeStderrLog`, max 1 MiB × 3, 14-day retention) | SOURCE `SupervisionConstants` / `ServeStderrLog.cs`; `RedirectStandardError = true` |
| Native crash: all-thread Python stacks? | `PYTHONFAULTHANDLER=1` dumps on fatal Python signals where the interpreter still runs the handler. A hard native fault inside PortAudio may **not** always produce a useful dump (process can die in C without returning to Python) | [EXT] Python faulthandler docs; INFERENCE for PortAudio Class A |
| Privacy | Faulthandler prints **tracebacks** (file/line/function), not local variable values | [EXT] Python docs — confirm: traceback-only; still avoid logging secrets in frames' *code constants*; no transcript requirement |

**Integration:** supported client env pass-through. Optional Hermes-side `faulthandler.enable()` would be source change — unnecessary if env works.

---

## 2. Serve pid in the supervision log

| Topic | Finding | Label |
|-------|---------|-------|
| Where client learns pid | On spawn: `ServeProcessId = child.Id` (`HermesProcessManager.cs` L336). Attach path sets from existing process (L191). Cleared on shutdown/supervision paths | SOURCE |
| Launcher vs interpreter | Zola may spawn a launcher python that starts an interpreter sibling; Application Error often shows the **interpreter** pid (`store_open`), while `ServeProcessId` may be the **child the client started** — S51 left launcher/interpreter pairing **UNRESOLVED** without a pair record | EVIDENCE S51; still open |
| One place to log | Supervisor already logs watcher/phone `job_assigned` **with pid**. Serve restart/stale lines historically **omit** pid. **Minimal fix:** log `ServeProcessId` (and, if separately known, interpreter pid) on serve `job`/`restart`/`stale` in the same supervision log format | SOURCE gap; Zola client change — supported |

---

## 3. Which PortAudio stream was active

| Existing breadcrumb? | Verdict | Label |
|----------------------|---------|-------|
| Beep / WAV play start–end | **No** dedicated events (Phase 2 search empty; beeps only `logger.debug` on failure) | MEASURED / SOURCE |
| Mic open/close | Partial: `Voice recording started` info log; wake markers exist; not a structured in/out stream id | SOURCE |
| Thinking sound | Off now; previously no crash-useful stream id either | — |

**Minimal events** (for the next dump match) — describe only:

1. `audio.out_shared start|end site=beep|wav|thinking` (thread name optional)  
2. `audio.in open|close|stop site=recorder|wake|barge`  
3. Correlate with existing `turn_timing` / display Thinking window  

Prefer Hermes log lines at existing `play_beep` / `_ensure_stream` / wake open sites (**Hermes source**) or client-side only where the client already knows capture lifecycle (**Zola** — does not see serve PortAudio directly).

---

## Findings

| ID | Severity | Summary |
|----|----------|---------|
| S51F-AUD-11 | MEDIUM | `PYTHONFAULTHANDLER=1` can be added on serve spawn without Hermes fork; help on native PortAudio faults is partial |
| S51F-AUD-12 | MEDIUM | Supervision log should record serve launcher (+ interpreter if known) pid on restart/stale |
| S51F-AUD-13 | LOW | No stream-site breadcrumbs for beep/WAV/mic — next dump still hard to attribute |
