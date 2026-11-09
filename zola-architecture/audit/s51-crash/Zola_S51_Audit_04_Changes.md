# Zola S51 Audit — 04 What changed around 2026-10-04/05

Phase 4. Read-only dates. Goal: what lined up with the first python APPCRASH cluster (first AE: **2026-10-05 11:13:49**, pid 12544, `python312.dll`, `0xc0000005`).

## Interpreter and voice packages

| Item | Value | Date evidence |
|------|-------|---------------|
| Hermes venv interpreter | CPython **3.12.14** (`MSC v.1944 64 bit`), path via uv | `python312.dll` LastWriteTime **2026-09-22** |
| `sounddevice` | 0.5.5 | dist-info **2026-09-23 07:27** |
| `libportaudio64bit.dll` (bundled) | 307,712 bytes; no FileVersion resource | **2026-09-23 07:27** (same install) |
| `numpy` | 2.4.3 | 2026-09-23 |
| `faster-whisper` / `ctranslate2` | 1.2.1 / 4.8.2 | 2026-09-23 |
| `onnxruntime` | 1.30.0 | 2026-09-23 |
| `sherpa-onnx` | 1.13.4 | **2026-09-23 15:32** (later same day) |

**EVIDENCE:** packages and PortAudio DLL were already on disk **~12 days before** the first crash. They are necessary for Group A (Phase 3) but **do not by themselves explain the 2026-10-04/05 onset**.

## Windows updates / audio drivers

| Item | Date | Relation to first crash |
|------|------|-------------------------|
| Get-HotFix in 2026-09-25→10-10 window | *(none listed in that range on this machine)* | No hotfix timestamp immediately before 2026-10-05 |
| KB5127647 / KB5127648 / KB5127690 | **2026-10-14 / 10-15** | **After** first crashes |
| Realtek Audio Effects / Universal Service | DriverDate **2026-02-09** | Before crash onset |
| Realtek Audio | 6.0.9661.1, DriverDate **2026-03-25** | Before |
| Intel SST Bluetooth/USB Audio | 10.29.0.12635, **2026-02-17** | Before |
| USB Audio 2.0 (Microsoft) | 10.0.26100.9711, DriverDate **2026-10-09** | **After** first crashes |

**EVIDENCE:** no Windows hotfix or audio-driver date in the inventory sits on 2026-10-04/05 itself. USB Audio driver stamp is after onset.

## Zola-Windows / hermes-agent commits (2026-09-25 → 2026-10-08)

Voice / STT / TTS / wake / supervision / plugins touched (names only):

- **P7-VOICEAUTH** (`f34bd9b`) — capture lifecycle, transcript admission, VoiceController — **closest large voice change before first crashes** (merged in the early-October P7 window; see `git log` 2026-10-01→10-06 merges).
- **P7-CLARIFY** (`f89b9d6`), **P7-LATENCY** (`1fc463a`) — voice clarify / timing.
- Earlier still in range: P4/P5 voice wake/feedback/lock commits; P6 memory store/forget/episodes (sqlite-heavy — plausible touch for Group B only, **INFERENCE**).
- **P8-HARDEN / P8-CONNECT** workspace plugins — not audio natives.
- **hermes-agent** pin `345cd2b` / tag `v2026.9.14`: **no** hermes-agent commits in 2026-09-25→10-08 on this checkout (detached pin; upstream not moving here).

**INFERENCE:** the onset clue aligns more with **Zola client/voice behaviour change (P7 capture/admission)** and/or an environmental factor not captured in HotFix/driver stamps, than with a fresh PortAudio pip install (that was 2026-09-23).

## First crash entries themselves (EVIDENCE)

| Time | Pid | Module | Code | Offset |
|------|----:|--------|------|--------|
| 2026-10-05 11:13:49 | 12544 | `python312.dll` | `0xc0000005` | `0x3b1ff` |
| 2026-10-05 12:06:34 | 25132 | `python312.dll` | `0xc0000005` | `0x3b1ff` |
| 2026-10-05 19:28:51 | 18868 | `python312.dll` | `0xc0000005` | `0x3b1ff` |
| 2026-10-06 08:48:12 | 3992 | `python312.dll` | `0xc0000005` | `0x3b1ff` |
| 2026-10-06 10:52:31 | 18340 | `ntdll.dll` | `0xc0000005` | `0xfa7d` |

Dumps for these first five were **not** preserved. They are **not** proven to be Group A; AE module `python312.dll` / `ntdll.dll` differs from Group A’s AE `unknown` + PortAudio dump stacks. **UNRESOLVED** whether onset signature equals the later PortAudio Group A.

## What could plausibly touch Phase 3 groups

| Change | Group A (PortAudio write) | Group B (python312/_sqlite3) |
|--------|---------------------------|------------------------------|
| sounddevice/PortAudio install 2026-09-23 | Present (precondition) | Unlikely |
| P7 voice capture/admission (early Oct) | Plausible interaction with mic/speaker lifecycle (**INFERENCE**) | Unlikely |
| P6 memory/sqlite (late Sep–early Oct) | Unlikely | Plausible (**INFERENCE**) |
| Windows HotFix 10-14/15 | After onset | After onset |
| USB Audio driver 10-09 | After onset | After onset |

## Finding

- **S51-AUD-06** [GAP] MEDIUM — Onset ~2026-10-05 still **UNRESOLVED** as to root trigger; voice packages predated onset by ~12 days; no HotFix/driver stamp on 10-04/05; first AE signatures lack dumps and may differ from Group A.
