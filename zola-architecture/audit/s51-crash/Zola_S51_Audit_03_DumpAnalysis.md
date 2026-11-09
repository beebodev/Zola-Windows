# Zola S51 Audit — 03 Dump Analysis

Phase 3. Tool: WinDbg `cdb.exe` 10.0.29680.1004. Exact command per Brian verdict:
`cdb -z <dump> -c ".ecxr; kn 50; lm; ~* kn 30; q"` with Microsoft public symbols only.
Scratch outputs: `s51-crash/scratch/cdb_python.exe.<pid>.dmp.txt` (not committed).
Documents quote **exception code**, **faulting module/offset**, **module names**, **frame names** only — never registers.
Python PDBs: not loaded (Brian: no PDB acquisition). **PortAudio:** no PDB — any `libportaudio64bit!Name+offset` string is the **nearest export**, not a verified function identity.

## Per-dump summary

### `python.exe.27712.dmp` (pid 27712)

- Crash event time: 2026-10-17 08:35:01.698 · Dump write: 2026-10-17 08:35:09.478 · Size: 23,091,216
- Process identity (Phase 2): serve (interpreter)
- Zola activity: serve restart window; store_open pid=27712 earlier same morning
- Exception: **0xc000001d** — (6c40.233c): Illegal instruction - code c000001d
- Faulting site: `unknown_unbacked_or_jit` via caller `libportaudio64bit!Pa_WriteStream+0x131c`
- Process uptime at dump: 0 days 0:03:45.000
- Crashing thread top frames:
  1. `0x00000118`81b90fc9`
  1. `libportaudio64bit!Pa_WriteStream+0x131c`
  1. `libportaudio64bit!Pa_WriteStream+0x197c`
  1. `libportaudio64bit!Pa_Sleep+0x6c17`
  1. `libportaudio64bit!PaWasapi_UpdateDeviceList+0x13d43`
  1. `kernel32!BaseThreadInitThunk+0x17`
  1. `ntdll!RtlUserThreadStart+0x2c`
- Interesting native modules loaded (names from `lm`; versions often deferred without private PDBs):
  - `MpOAV`
  - `_ctypes`
  - `_sherpa_onnx_cp312_win_amd64`
  - `_sqlite3`
  - `_ssl`
  - `avcodec_62_984de33114b7fa384296817dec999c9d`
  - `avdevice_62_bf7a3ffbb6a4b577f24a39ea98a958d5`
  - `avfilter_11_aef80fc767dc77e0319469b5bdcdf998`
  - `avformat_62_b6d6bb16ff0b7753371e2d0b285c9dc0`
  - `avicap32`
  - `avrt`
  - `avutil_60_cc1777f859dcfd98b8019bdf459e774e`
  - `ctranslate2`
  - `libSvtAv1Enc_c4dd99c98ddcdb013e820dbd68a30e26`
  - `libdav1d_959ebc1340f7dfcbcf8e299a26281738`
  - `libportaudio64bit`
  - `libssl_3_x64`
  - `ntdll`
  - `onnxruntime`
  - `onnxruntime_providers_shared`
  - `onnxruntime_pybind11_state`
  - `python312`
  - `sqlite3`
- Other threads touching audio/STT/TTS natives: portaudio-like **2**, stt-like **0**, (parsed interest set size 54 / 55 stacks). Frame names only — INFERENCE on role.
  - Example audio thread frames: `ntdll!NtWaitForMultipleObjects+0x14`, `KERNELBASE!WaitForMultipleObjectsEx+0x123`, `KERNELBASE!WaitForMultipleObjects+0x11`, `libportaudio64bit!Pa_Sleep+0x67d6`, `libportaudio64bit!PaWasapi_UpdateDeviceList+0x13d43`

### `python.exe.29172.dmp` (pid 29172)

- Crash event time: 2026-10-17 16:53:37.999 · Dump write: 2026-10-17 16:53:44.673 · Size: 7,543,225
- Process identity (Phase 2): serve (interpreter)
- Zola activity: store_open pid=29172; serve stale/restart; AE module python312.dll
- Exception: **0xc0000005** — (71f4.6bf0): Access violation - code c0000005
- Faulting site: `python312`
- Process uptime at dump: 0 days 0:00:56.000
- Crashing thread top frames:
  1. `python312!PyObject_Vectorcall+0x5f`
  1. `python312!PyObject_Vectorcall+0x39`
  1. `_sqlite3+0x47c8`
  1. `_sqlite3+0x452b`
  1. `python312!PyEval_EvalFrameDefault+0x2297`
  1. `python312!PyFunction_Vectorcall+0x17c`
  1. `python312!PyContext_NewHamtForTests+0x51`
  1. `python312!PyContext_NewHamtForTests+0x35c`
  1. `python312!PySet_Add+0x3bb`
  1. `python312!PyObject_Call+0x125`
- Interesting native modules loaded (names from `lm`; versions often deferred without private PDBs):
  - `MpOAV`
  - `_ctypes`
  - `_sherpa_onnx_cp312_win_amd64`
  - `_sqlite3`
  - `_ssl`
  - `avrt`
  - `libportaudio64bit`
  - `libssl_3_x64`
  - `ntdll`
  - `onnxruntime`
  - `python312`
  - `sqlite3`
- Other threads touching audio/STT/TTS natives: portaudio-like **0**, stt-like **0**, (parsed interest set size 40 / 41 stacks). Frame names only — INFERENCE on role.

### `python.exe.28836.dmp` (pid 28836)

- Crash event time: 2026-10-20 14:00:06.311 · Dump write: 2026-10-20 14:00:15.520 · Size: 22,935,229
- Process identity (Phase 2): serve (interpreter) — INFERENCE from size/signature match Group A
- Zola activity: AE unknown/c000001d; dump preserved in Oct-17 folder
- Exception: **0xc000001d** — (70a4.7910): Illegal instruction - code c000001d
- Faulting site: `unknown_unbacked_or_jit` via caller `libportaudio64bit!Pa_WriteStream+0x131c`
- Process uptime at dump: 0 days 0:46:50.000
- Crashing thread top frames:
  1. `0x00000168`07450f52`
  1. `libportaudio64bit!Pa_WriteStream+0x131c`
  1. `libportaudio64bit!Pa_WriteStream+0x197c`
  1. `libportaudio64bit!Pa_Sleep+0x6c17`
  1. `libportaudio64bit!PaWasapi_UpdateDeviceList+0x13d43`
  1. `kernel32!BaseThreadInitThunk+0x17`
  1. `ntdll!RtlUserThreadStart+0x2c`
- Interesting native modules loaded (names from `lm`; versions often deferred without private PDBs):
  - `MpOAV`
  - `_ctypes`
  - `_sherpa_onnx_cp312_win_amd64`
  - `_sqlite3`
  - `_ssl`
  - `avcodec_62_984de33114b7fa384296817dec999c9d`
  - `avdevice_62_bf7a3ffbb6a4b577f24a39ea98a958d5`
  - `avfilter_11_aef80fc767dc77e0319469b5bdcdf998`
  - `avformat_62_b6d6bb16ff0b7753371e2d0b285c9dc0`
  - `avicap32`
  - `avrt`
  - `avutil_60_cc1777f859dcfd98b8019bdf459e774e`
  - `ctranslate2`
  - `libSvtAv1Enc_c4dd99c98ddcdb013e820dbd68a30e26`
  - `libdav1d_959ebc1340f7dfcbcf8e299a26281738`
  - `libportaudio64bit`
  - `libssl_3_x64`
  - `ntdll`
  - `onnxruntime`
  - `onnxruntime_providers_shared`
  - `onnxruntime_pybind11_state`
  - `python312`
  - `sqlite3`
- Other threads touching audio/STT/TTS natives: portaudio-like **2**, stt-like **0**, (parsed interest set size 54 / 55 stacks). Frame names only — INFERENCE on role.
  - Example audio thread frames: `ntdll!NtWaitForMultipleObjects+0x14`, `KERNELBASE!WaitForMultipleObjectsEx+0x123`, `KERNELBASE!WaitForMultipleObjects+0x11`, `libportaudio64bit!Pa_Sleep+0x67d6`, `libportaudio64bit!PaWasapi_UpdateDeviceList+0x13d43`

### `python.exe.43840.dmp` (pid 43840)

- Crash event time: 2026-11-06 14:18:38.638 · Dump write: 2026-11-06 14:18:47.130 · Size: 22,944,181
- Process identity (Phase 2): serve (interpreter)
- Zola activity: serve stale→restart; post store_open new pid
- Exception: **0xc000001d** — (ab40.61ac): Illegal instruction - code c000001d
- Faulting site: `unknown_unbacked_or_jit` via caller `libportaudio64bit!Pa_WriteStream+0x131c`
- Process uptime at dump: 0 days 1:49:22.000
- Crashing thread top frames:
  1. `0x00000210`81600f1a`
  1. `libportaudio64bit!Pa_WriteStream+0x131c`
  1. `libportaudio64bit!Pa_WriteStream+0x197c`
  1. `libportaudio64bit!Pa_Sleep+0x6c17`
  1. `libportaudio64bit!PaWasapi_UpdateDeviceList+0x13d43`
  1. `kernel32!BaseThreadInitThunk+0x17`
  1. `ntdll!RtlUserThreadStart+0x2c`
- Interesting native modules loaded (names from `lm`; versions often deferred without private PDBs):
  - `MpOAV`
  - `_ctypes`
  - `_sherpa_onnx_cp312_win_amd64`
  - `_sqlite3`
  - `_ssl`
  - `avcodec_62_984de33114b7fa384296817dec999c9d`
  - `avdevice_62_bf7a3ffbb6a4b577f24a39ea98a958d5`
  - `avfilter_11_aef80fc767dc77e0319469b5bdcdf998`
  - `avformat_62_b6d6bb16ff0b7753371e2d0b285c9dc0`
  - `avicap32`
  - `avrt`
  - `avutil_60_cc1777f859dcfd98b8019bdf459e774e`
  - `ctranslate2`
  - `libSvtAv1Enc_c4dd99c98ddcdb013e820dbd68a30e26`
  - `libdav1d_959ebc1340f7dfcbcf8e299a26281738`
  - `libportaudio64bit`
  - `libssl_3_x64`
  - `ntdll`
  - `onnxruntime`
  - `onnxruntime_providers_shared`
  - `onnxruntime_pybind11_state`
  - `python312`
  - `sqlite3`
- Other threads touching audio/STT/TTS natives: portaudio-like **2**, stt-like **0**, (parsed interest set size 52 / 53 stacks). Frame names only — INFERENCE on role.
  - Example audio thread frames: `ntdll!NtWaitForMultipleObjects+0x14`, `KERNELBASE!WaitForMultipleObjectsEx+0x123`, `KERNELBASE!WaitForMultipleObjects+0x11`, `libportaudio64bit!Pa_Sleep+0x67d6`, `libportaudio64bit!PaWasapi_UpdateDeviceList+0x13d43`

### `python.exe.39848.dmp` (pid 39848)

- Crash event time: 2026-11-09 07:51:27.170 · Dump write: 2026-11-09 07:51:36.800 · Size: 23,032,317
- Process identity (Phase 2): serve (interpreter)
- Zola activity: A11 reply-generation; Thinking/Speaking → unreachable
- Exception: **0xc0000005** — (9ba8.8168): Access violation - code c0000005
- Faulting site: `unknown_unbacked_or_jit` via caller `libportaudio64bit!Pa_WriteStream+0x131c`
- Process uptime at dump: 0 days 0:22:28.000
- Crashing thread top frames:
  1. `0x0000022b`4ba00fc2`
  1. `libportaudio64bit!Pa_WriteStream+0x131c`
  1. `libportaudio64bit!Pa_WriteStream+0x197c`
  1. `libportaudio64bit!Pa_Sleep+0x6c17`
  1. `libportaudio64bit!PaWasapi_UpdateDeviceList+0x13d43`
  1. `kernel32!BaseThreadInitThunk+0x17`
  1. `ntdll!RtlUserThreadStart+0x2c`
- Interesting native modules loaded (names from `lm`; versions often deferred without private PDBs):
  - `MpOAV`
  - `_ctypes`
  - `_sherpa_onnx_cp312_win_amd64`
  - `_sqlite3`
  - `_ssl`
  - `avcodec_62_984de33114b7fa384296817dec999c9d`
  - `avdevice_62_bf7a3ffbb6a4b577f24a39ea98a958d5`
  - `avfilter_11_aef80fc767dc77e0319469b5bdcdf998`
  - `avformat_62_b6d6bb16ff0b7753371e2d0b285c9dc0`
  - `avicap32`
  - `avrt`
  - `avutil_60_cc1777f859dcfd98b8019bdf459e774e`
  - `ctranslate2`
  - `libSvtAv1Enc_c4dd99c98ddcdb013e820dbd68a30e26`
  - `libdav1d_959ebc1340f7dfcbcf8e299a26281738`
  - `libportaudio64bit`
  - `libssl_3_x64`
  - `ntdll`
  - `onnxruntime`
  - `onnxruntime_providers_shared`
  - `onnxruntime_pybind11_state`
  - `python312`
  - `sqlite3`
- Other threads touching audio/STT/TTS natives: portaudio-like **2**, stt-like **0**, (parsed interest set size 53 / 54 stacks). Frame names only — INFERENCE on role.
  - Example audio thread frames: `ntdll!NtWaitForMultipleObjects+0x14`, `KERNELBASE!WaitForMultipleObjectsEx+0x123`, `KERNELBASE!WaitForMultipleObjects+0x11`, `libportaudio64bit!Pa_Sleep+0x67d6`, `libportaudio64bit!PaWasapi_UpdateDeviceList+0x13d43`

### `python.exe.34996.dmp` (pid 34996)

- Crash event time: 2026-11-09 08:21:50.445 · Dump write: 2026-11-09 08:21:58.579 · Size: 22,917,020
- Process identity (Phase 2): serve (interpreter); pair 13516/34996
- Zola activity: B6 answer generation; store_open pid=34996 since A11 restart
- Exception: **0xc0000005** — (88b4.6e1c): Access violation - code c0000005
- Faulting site: `unknown_unbacked_or_jit` via caller `libportaudio64bit!Pa_WriteStream+0x131c`
- Process uptime at dump: 0 days 0:30:18.000
- Crashing thread top frames:
  1. `0x00000200`19ae0fc3`
  1. `libportaudio64bit!Pa_WriteStream+0x131c`
  1. `libportaudio64bit!Pa_WriteStream+0x197c`
  1. `libportaudio64bit!Pa_Sleep+0x6c17`
  1. `libportaudio64bit!PaWasapi_UpdateDeviceList+0x13d43`
  1. `kernel32!BaseThreadInitThunk+0x17`
  1. `ntdll!RtlUserThreadStart+0x2c`
- Interesting native modules loaded (names from `lm`; versions often deferred without private PDBs):
  - `MpOAV`
  - `_ctypes`
  - `_sherpa_onnx_cp312_win_amd64`
  - `_sqlite3`
  - `_ssl`
  - `avcodec_62_984de33114b7fa384296817dec999c9d`
  - `avdevice_62_bf7a3ffbb6a4b577f24a39ea98a958d5`
  - `avfilter_11_aef80fc767dc77e0319469b5bdcdf998`
  - `avformat_62_b6d6bb16ff0b7753371e2d0b285c9dc0`
  - `avicap32`
  - `avrt`
  - `avutil_60_cc1777f859dcfd98b8019bdf459e774e`
  - `ctranslate2`
  - `libSvtAv1Enc_c4dd99c98ddcdb013e820dbd68a30e26`
  - `libdav1d_959ebc1340f7dfcbcf8e299a26281738`
  - `libportaudio64bit`
  - `libssl_3_x64`
  - `ntdll`
  - `onnxruntime`
  - `onnxruntime_providers_shared`
  - `onnxruntime_pybind11_state`
  - `python312`
  - `sqlite3`
- Other threads touching audio/STT/TTS natives: portaudio-like **2**, stt-like **0**, (parsed interest set size 53 / 54 stacks). Frame names only — INFERENCE on role.
  - Example audio thread frames: `ntdll!NtWaitForMultipleObjects+0x14`, `KERNELBASE!WaitForMultipleObjectsEx+0x123`, `KERNELBASE!WaitForMultipleObjects+0x11`, `libportaudio64bit!Pa_Sleep+0x67d6`, `libportaudio64bit!PaWasapi_UpdateDeviceList+0x13d43`

## Signature groups

### Group A — PortAudio stream thread → unbacked address

**Symbol caveat (EVIDENCE):** `libportaudio64bit.dll` has **no PDB** in these sessions (export symbols only). Names such as `Pa_WriteStream+0x131c` or `PaWasapi_UpdateDeviceList+0x13d43` are the **nearest exports**, not identified real functions. `PaWasapi_UpdateDeviceList+…` appearing near thread start is an export-relative label, not proof that device-list code ran.

**Group A restatement (EVIDENCE):** A PortAudio **internal stream thread** transferred control to an **unbacked** address (RIP not in any loaded module — AE faulting module `unknown`). Three preserved dumps show illegal instruction `0xc000001d` (27712, 28836, 43840); two show access violation `0xc0000005` (39848, 34996). Return addresses sit in `libportaudio64bit` export space with the same relative offsets across dumps.

| Dump | Date | Exception | AE module | Nearest-export frame labels (not real funcs) | Process | Zola doing | Stream direction |
|------|------|-----------|-----------|-----------------------------------------------|---------|------------|------------------|
| 27712 | 2026-10-17 | `0xc000001d` | `unknown` | unbacked → `…!Pa_WriteStream+0x131c` → `+0x197c` → `Pa_Sleep+0x6c17` → `PaWasapi_UpdateDeviceList+0x13d43` | serve | morning serve gen | **UNRESOLVED** (input or output) |
| 28836 | 2026-10-20 | `0xc000001d` | `unknown` | same export-relative pattern | serve (INFERENCE) | — | **UNRESOLVED** |
| 43840 | 2026-11-06 | `0xc000001d` | `unknown` | same | serve | serve restart window | **UNRESOLVED** |
| 39848 | 2026-11-09 | `0xc0000005` | `unknown` | same | serve | A11 reply generation | **UNRESOLVED** |
| 34996 | 2026-11-09 | `0xc0000005` | `unknown` | same | serve | B6 answer generation | **UNRESOLVED** |

**Count:** 5 preserved dumps. **Recency:** through 2026-11-09.

**INFERENCE:** Consistent with a PortAudio stream **callback that was freed or replaced** while PortAudio’s internal thread still invoked it (control transfer to unbacked / stale code). Not proven which Hermes path created/stopped the stream.

Loaded alongside in Group A dumps: `python312`, `ctranslate2`, `onnxruntime` / `onnxruntime_pybind11_state`, `_sherpa_onnx_cp312_win_amd64`, `sqlite3`/`_sqlite3`, `_ctypes`, `libportaudio64bit` (from `_sounddevice_data\portaudio-binaries`). **EVIDENCE** from `lm`.

### Group B — `python312` + `_sqlite3`

| Dump | Date | Exception | Faulting module | Top frames | Process | Zola doing | Role |
|------|------|-----------|-----------------|------------|---------|------------|------|
| 29172 | 2026-10-17 | `0xc0000005` | AE `python312.dll` / dump `python312!PyObject_Vectorcall` with `_sqlite3` frames | PyObject_Vectorcall → _sqlite3 → PyEval_EvalFrameDefault | serve | store_open pid=29172; serve restart | **main/eval + sqlite** (INFERENCE) |

**Count:** 1 preserved dump (~7.5 MB size class). May relate to AE rows that name `sqlite3.dll` / `python312.dll` without dumps (**INFERENCE**).

### Event-log-only signatures (no dump / dump gone)

Grouped from Phase 1 AE table for context (not Phase 3 dump-proven):

| Signature (AE module + code + offset) | Approx count | Notes |
|--------------------------------------|-------------:|-------|
| `python312.dll` + `0xc0000005` + `0x3b1ff` | many (Oct 5–Nov 4) | No preserved dump with that exact AE module/offset among the 6 opened |
| `ntdll.dll` + `0xc0000005` + `0xfa7d` | 1 (2026-10-06) | S51 lore: silence auto-stop / STT in flight — dump not preserved |
| `_ctypes.pyd` + `0xc0000005` + `0x10426` | 2 | |
| `sqlite3.dll` + `0xc0000005` + `0xc92b0` | 3 | Possibly related to Group B |
| `libportaudio64bit.dll` + `0xc0000005` + `0xea02` | 1 (2026-11-02) | AE named portaudio directly; family of Group A |
| `unknown` + `0xc0000005`/`0xc000001d`/`0xc0000096` | many | **EVIDENCE:** opened dumps show these are often Group A (unbacked RIP from a PortAudio stream thread) |
| Zola.Client `Microsoft.UI.Xaml.dll` / `CoreMessagingXP.dll` + `0xc000027b` | 10 | Client UI; no dumps |

## Findings

- **S51-AUD-03** [RISK] HIGH — Dominant preserved-dump signature: PortAudio internal stream thread → unbacked address (export-only labels in `libportaudio64bit`; input vs output **UNRESOLVED**), including both 2026-11-09 crashes. Module path from `lm`: `_sounddevice_data\portaudio-binaries\libportaudio64bit.dll`.
- **S51-AUD-04** [RISK] MEDIUM — Distinct second signature in `29172`: `python312` vectorcall with `_sqlite3` frames (~7.5 MB dump class).
- **S51-AUD-05** [GAP] MEDIUM — Matching Python PDBs for this uv 3.12.14 build were not available (Brian: no PDB acquisition). PortAudio frames are export-relative only.

