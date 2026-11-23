# SPEECH-PRE Audit 05 — Where the owner could live

Against: SP-D04, VD-1, P9-D02, A01, A12. Options and evidence only; decision for Brian.

Shared admission (all options): Hermes/owner candidate → `TranscriptAdmission.Decide` → `TranscriptReady` → `prompt.submit` / clarify. **P7-D01:** no second admit path (`TranscriptAdmission.cs:54–117`).

---

## (a) Inside Windows client (.NET)

| Criterion | Evidence |
|-----------|----------|
| Reply text/events | Already has `message.*`, `tool.*` (`ChatSocket.cs`) |
| Hand-off | Client-minted capture into lifecycle + admission; bypass Hermes `voice.transcript` |
| Crash isolation | Owner crash = client crash; no Job Object fence |
| Dependencies | No WASAPI/`IAudioClock`/Cartesia/sherpa STT in client today; would re-port spike |
| Timing | .NET *can* P/Invoke same APIs (INFERENCE); no existing code. Today’s finished = ffplay monitor |
| PR-D02 | Inherits `ZolaClient` vs `-dev` roots; single-instance mutex |
| Memory | Client cold-rest gate **900 MB** (A13 / P3-D13). Spike S1+S3 archives ~296+460 MB — loading into WinUI threatens gate. **UNRESOLVED:** owner RSS |

---

## (b) Separate supervised local process (spike-shaped)

| Criterion | Evidence |
|-----------|----------|
| Reply text/events | Client forwards deltas/complete/cancel/tool over local IPC (pattern: `PhoneProcess` named pipe `ZolaPhone`) |
| Hand-off | Owner returns candidate text → client lifecycle + `TranscriptAdmission` → one path |
| Crash isolation | `SupervisedPython` / Job Object / 3-per-10-min restart / latch (`SupervisedPython.cs`, `WatcherProcess`, `PhoneProcess`; P9-D02). Speak/listen die with owner; conversation (serve+UI) survive |
| Dependencies | Spike stack proven: comtypes WASAPI, Cartesia WS, Silero, S1+S3. Hermes venv ≠ spike venv |
| Timing | Same as MEASURED Phase 3: `IAudioClock` + QPC (`owner.py`, `wasapi/*`, `common/clock.py`) |
| PR-D02 | Spawn with role-bound env; secrets under `ClientDataRoot\secrets`; one-build mutex |
| Memory | Models in helper → client 900 MB gate unchanged. **UNRESOLVED:** helper RSS with Zola live |

---

## (c) Other

| Option | Fit |
|--------|-----|
| Inside Hermes serve / plugin thread | Rejected by VD-1; shares PortAudio/S51 domain |
| Native C++/Rust supervised helper | Possible; no spike evidence |
| Phone as endpoint | A12 not built; out of scope |

---

## Cursor’s recommendation (labelled)

**Recommend (b): separate supervised Python process**, patterned on watcher/`zola-phone`, hosting spike AudioOwner + Listener.

Trade-offs: matches SP-D04 / VD-1 / R-3; keeps proven timing; isolates STT memory and audio crashes from serve and Helix. Cost: new IPC + client wiring; own venv/models; HUD for helper-down.

**(a)** only if Brian accepts a large in-proc native port and gate pressure; worse crash isolation.

---

## Decision for Brian

**Choose owner placement:** (a) in-client .NET, (b) supervised local process (spike-shaped), or (c) other — before the build plan locks topology.

**SPEECHPRE-AUD-20 [RISK] MEDIUM** — Placement undecided; build plan blocked on Brian’s choice (not a code gap).
