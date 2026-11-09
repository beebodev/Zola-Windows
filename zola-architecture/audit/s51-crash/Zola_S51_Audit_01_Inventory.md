# Zola S51 Audit — Phase 1 Inventory

**Prompt:** `C:\Users\test\Dev\zola-spikes\prompts\S51-CRASH_Audit_Prompt_v1.1.md`
**Prompt SHA-256 (verified):** `b6a6f89820bc120bd0179373bcfaddb1c933499acf99895b78b17d6b1a085293`
**Phase:** 1 COMPLETE (STOP — awaiting Brian tool verdict)
**Base:** `main` = `origin/main` = `92e6cc473ae69d7dac88695229b58f24d0167cfb` (clean at branch create)
**Branch:** `s51-crash-audit`
**hermes-agent:** HEAD `345cd2b057a452236de401d3534b8502a7465e8d` (pin), clean, detached `v2026.9.14`

## Dump inventory

| Name | Size (bytes) | File write time (local) | SHA-256 | Folders |
|------|-------------:|-------------------------|---------|---------|
| `python.exe.27712.dmp` | 23,091,216 | 2026-10-17 08:35:09.478 | `9E4E4B4232C03CC99A0948E50887DCA522B370E31CA3867E1DCC2CC0C8E6B087` | saved-2026-10-17 |
| `python.exe.29172.dmp` | 7,543,225 | 2026-10-17 16:53:44.673 | `ECA464182EBD826D00C9225BE6DB3D98B9F2BA311AD76A821BED50AEDD978432` | saved-2026-10-17 |
| `python.exe.28836.dmp` | 22,935,229 | 2026-10-20 14:00:15.520 | `A93DAC4A36BE3705F78BCC1893E259A4C07A135F6B91CC603481EC2B22759AC9` | saved-2026-10-17 |
| `python.exe.43840.dmp` | 22,944,181 | 2026-11-06 14:18:47.130 | `3E3BBEC2D188FD0CB15ECC08EE3BA832EBD3B21514B7B7C5ADBFE9F34AA622CE` | live, saved-2026-11-09 |
| `python.exe.39848.dmp` | 23,032,317 | 2026-11-09 07:51:36.800 | `5450B6B72E9581202BC82194A2E006FC605FFFCD510260615F27A9A707BB0503` | live, saved-2026-11-09 |
| `python.exe.34996.dmp` | 22,917,020 | 2026-11-09 08:21:58.579 | `6DCBC594695529D93D5652C3C7B773DC8DC39B68DF10092E368494CADFF8BCC6` | live, saved-2026-11-09 |

### Preserve action (Phase 1)

- Live folder listed 2026-11-09: `34996`, `39848`, `43840`.
- `34996` and `39848` already in `crash-dumps-2026-11-09` (SHA match).
- **Copied** (not moved) `python.exe.43840.dmp` → `C:\Users\test\Dev\zola-spikes\crash-dumps-2026-11-09\` (SHA `3E3BBEC2D188FD0CB15ECC08EE3BA832EBD3B21514B7B7C5ADBFE9F34AA622CE`).

### Known from lore / baseline but gone from live (14-day prune)

| Pid (dump name) | Lore note | Status |
|-----------------|-----------|--------|
| 25760 | 2026-11-03 | **GONE** — not in live or saved folders |
| 41148 | 2026-11-04 (~23,071,438) | **GONE** |
| 18424 | 2026-11-05 (~7,457,959) | **GONE** |
| 15400 | 2026-11-05 (~22,598,519) | **GONE** |

Unique dumps preserved: **6** (3 in Oct-17 save, 3 in Nov-09 save / live). Size classes: ~7.5 MB (`29172` only among preserved) and ~23 MB (all others).

## Application event log (G-EVENTLOG)

Scope: Application Error (1000), Windows Error Reporting (1001), .NET Runtime — `python.exe` / `Zola.Client.exe`, since 2026-09-01. .NET Runtime matches: **0**.

### Application Error (ID 1000) — oldest first

| Time (local) | Process | Pid (dec) | Pid (hex) | Faulting module | Module ver | Exception | Fault offset | Report Id |
|--------------|---------|----------:|-----------|-----------------|------------|-----------|--------------|-----------|
| 2026-09-29 08:55:39.325 | Zola.Client.exe | 8980 | 0x2314 | `Microsoft.UI.Xaml.dll` | 3.2.3.0 | 0xc000027b | 0x00000000003a9dbd | 82e3f92d-3bf9-4518-85a3-9beb43ee671e |
| 2026-09-29 08:57:29.179 | Zola.Client.exe | 8124 | 0x1FBC | `Microsoft.UI.Xaml.dll` | 3.2.3.0 | 0xc000027b | 0x00000000003a9dbd | 712fa2f3-dd38-4dfa-952d-067b94043c48 |
| 2026-09-29 08:58:09.374 | Zola.Client.exe | 16820 | 0x41B4 | `Microsoft.UI.Xaml.dll` | 3.2.3.0 | 0xc000027b | 0x00000000003a9dbd | 11c62d33-1750-4f6c-9db3-d8f1f722129e |
| 2026-09-29 08:58:46.773 | Zola.Client.exe | 6372 | 0x18E4 | `Microsoft.UI.Xaml.dll` | 3.2.3.0 | 0xc000027b | 0x00000000003a9dbd | 36a14934-229c-4ca8-8f58-be9cd0fd82d4 |
| 2026-09-29 09:01:39.084 | Zola.Client.exe | 20792 | 0x5138 | `Microsoft.UI.Xaml.dll` | 3.2.3.0 | 0xc000027b | 0x00000000003a9dbd | aef98704-f499-43c1-9e21-28cdc819e182 |
| 2026-09-29 09:02:50.787 | Zola.Client.exe | 24340 | 0x5F14 | `Microsoft.UI.Xaml.dll` | 3.2.3.0 | 0xc000027b | 0x00000000003a9dbd | 4d8c37f1-298d-4d4e-9402-9c9cc6c71d50 |
| 2026-09-29 09:03:35.069 | Zola.Client.exe | 17912 | 0x45F8 | `Microsoft.UI.Xaml.dll` | 3.2.3.0 | 0xc000027b | 0x00000000003a9dbd | 822ca17d-6163-4e1c-8768-cb30a984bd4e |
| 2026-09-29 09:04:32.379 | Zola.Client.exe | 12284 | 0x2FFC | `Microsoft.UI.Xaml.dll` | 3.2.3.0 | 0xc000027b | 0x00000000003a9dbd | 1ae375c1-096a-4994-a806-ca1ce6c1c006 |
| 2026-09-29 09:05:06.090 | Zola.Client.exe | 7656 | 0x1DE8 | `Microsoft.UI.Xaml.dll` | 3.2.3.0 | 0xc000027b | 0x00000000003a9dbd | 87e3f4b8-65fb-4a07-a242-62860478742a |
| 2026-10-05 11:13:49.335 | python.exe | 12544 | 0x3100 | `python312.dll` | 0.0.0.0 | 0xc0000005 | 0x000000000003b1ff | 84648916-ce9c-4e5e-9213-98f547ce1cf8 |
| 2026-10-05 12:06:34.517 | python.exe | 25132 | 0x622C | `python312.dll` | 0.0.0.0 | 0xc0000005 | 0x000000000003b1ff | 4f440847-c0bb-40e3-81e9-24e10320e227 |
| 2026-10-05 19:28:51.861 | python.exe | 18868 | 0x49B4 | `python312.dll` | 0.0.0.0 | 0xc0000005 | 0x000000000003b1ff | ea36d5af-be55-4f2b-b4a3-b4fb0bd2b2f5 |
| 2026-10-06 08:48:12.697 | python.exe | 3992 | 0xF98 | `python312.dll` | 0.0.0.0 | 0xc0000005 | 0x000000000003b1ff | 16578150-fc45-4ec5-a14a-63e463931f86 |
| 2026-10-06 10:52:31.600 | python.exe | 18340 | 0x47A4 | `ntdll.dll` | 10.0.26100.9444 | 0xc0000005 | 0x000000000000fa7d | f7d652db-030f-456d-9e7b-9e3de65ea635 |
| 2026-10-08 09:40:06.683 | python.exe | 20044 | 0x4E4C | `python312.dll` | 0.0.0.0 | 0xc0000005 | 0x000000000003b1ff | 66c246e3-bdcb-4c35-ad53-31cd9b6aa43b |
| 2026-10-08 11:07:55.907 | python.exe | 8568 | 0x2178 | `python312.dll` | 0.0.0.0 | 0xc0000005 | 0x000000000003b1ff | 9ca8a54e-ae75-4d0c-8dc1-9ff50ed4949b |
| 2026-10-10 15:53:01.446 | python.exe | 21768 | 0x5508 | `_ctypes.pyd` | 0.0.0.0 | 0xc0000005 | 0x0000000000010426 | a640f6fd-a2f7-48c4-ae55-874dbf213cd7 |
| 2026-10-12 11:33:19.425 | python.exe | 7940 | 0x1F04 | `_ctypes.pyd` | 0.0.0.0 | 0xc0000005 | 0x0000000000010426 | 1cd0642e-3ab2-4d51-a1a4-d4664e2f0e2e |
| 2026-10-13 14:26:32.666 | python.exe | 21680 | 0x54B0 | `python312.dll` | 0.0.0.0 | 0xc0000005 | 0x000000000003b1ff | b17ff3e8-b9f3-4eaa-8919-fc214caa517b |
| 2026-10-13 15:34:04.391 | Zola.Client.exe | 5760 | 0x1680 | `CoreMessagingXP.dll` | 10.0.27200.1054 | 0xc000027b | 0x0000000000097976 | 7266da4f-a1fc-456f-b661-0076d9e1388b |
| 2026-10-16 11:21:51.743 | python.exe | 26244 | 0x6684 | `sqlite3.dll` | 0.0.0.0 | 0xc0000005 | 0x00000000000c92b0 | 839e40cf-8291-4256-a50c-147f427f3060 |
| 2026-10-16 14:15:11.694 | python.exe | 27332 | 0x6AC4 | `unknown` | 0.0.0.0 | 0xc0000005 | 0x000001ac2bbf0fc9 | 09f518b8-c25a-4a56-8b49-b341b5115612 |
| 2026-10-17 00:51:19.936 | python.exe | 22636 | 0x586C | `unknown` | 0.0.0.0 | 0xc0000005 | 0x000001bb00450f52 | df5c19f7-eabf-4cb5-a46e-8f047d6d9f8a |
| 2026-10-17 08:17:45.874 | python.exe | 27636 | 0x6BF4 | `unknown` | 0.0.0.0 | 0xc0000005 | 0x000001c6154a0ef8 | eb8035d2-e03e-4045-b0f1-846bd26e5878 |
| 2026-10-17 08:20:40.514 | python.exe | 10156 | 0x27AC | `unknown` | 0.0.0.0 | 0xc0000005 | 0x0000027019920f53 | 46aaf379-44bd-42e8-908c-edcfcf50e587 |
| 2026-10-17 08:31:13.506 | python.exe | 2812 | 0xAFC | `unknown` | 0.0.0.0 | 0xc000001d | 0x000002d682450ee2 | abc0325e-89a4-45d5-b21b-43b33af7166d |
| 2026-10-17 08:35:01.698 | python.exe | 27712 | 0x6C40 | `unknown` | 0.0.0.0 | 0xc000001d | 0x0000011881b90fc9 | 8f89158b-a40e-4225-ade8-4192ecee9667 |
| 2026-10-17 16:53:37.999 | python.exe | 29172 | 0x71F4 | `python312.dll` | 0.0.0.0 | 0xc0000005 | 0x000000000003b1ff | c7392427-853b-4f79-a7d1-49b2747ed227 |
| 2026-10-20 14:00:06.311 | python.exe | 28836 | 0x70A4 | `unknown` | 0.0.0.0 | 0xc000001d | 0x0000016807450f52 | e20ae0a8-9d60-4853-af8b-3b316980a58c |
| 2026-10-28 07:30:00.255 | python.exe | 20916 | 0x51B4 | `unknown` | 0.0.0.0 | 0xc0000005 | 0x000001fd4a7f0fc5 | 4469de65-bfb8-4a4b-b61d-03d0593fde0f |
| 2026-10-29 10:17:35.971 | python.exe | 28308 | 0x6E94 | `unknown` | 0.0.0.0 | 0xc0000005 | 0x0000026d52db0fc5 | a8a72d64-7fce-426a-8dd4-6463ed4c38de |
| 2026-10-30 15:12:53.541 | python.exe | 40560 | 0x9E70 | `unknown` | 0.0.0.0 | 0xc0000096 | 0x000001a0016d0ee2 | 6aa8d8aa-2a28-4445-915a-96a268844c2a |
| 2026-10-30 15:16:22.305 | python.exe | 42072 | 0xA458 | `unknown` | 0.0.0.0 | 0xc0000005 | 0x000002960c700ee5 | b24a43b5-23ae-4f78-83ca-27ac1661dee0 |
| 2026-11-02 11:11:37.141 | python.exe | 34768 | 0x87D0 | `libportaudio64bit.dll` | 0.0.0.0 | 0xc0000005 | 0x000000000000ea02 | 65ae9f88-1261-4034-aaae-aa248f0eb31b |
| 2026-11-03 10:13:50.762 | python.exe | 25760 | 0x64A0 | `unknown` | 0.0.0.0 | 0xc000001d | 0x000001c3063e0fc2 | 7601927f-52a1-420a-b561-28441f28971f |
| 2026-11-03 10:48:24.326 | python.exe | 46976 | 0xB780 | `python312.dll` | 0.0.0.0 | 0xc0000005 | 0x000000000003b1ff | a325888a-3221-48c3-922d-e09c9153e2a8 |
| 2026-11-04 10:21:33.748 | python.exe | 41764 | 0xA324 | `sqlite3.dll` | 0.0.0.0 | 0xc0000005 | 0x00000000000c92b0 | 43a26ec6-813c-41aa-9e90-710cd6201f77 |
| 2026-11-04 11:04:01.977 | python.exe | 41148 | 0xA0BC | `python312.dll` | 0.0.0.0 | 0xc0000005 | 0x000000000003b1ff | b3d901f8-0099-49da-b08e-df90d9dcd7b2 |
| 2026-11-05 13:32:47.359 | python.exe | 18424 | 0x47F8 | `sqlite3.dll` | 0.0.0.0 | 0xc0000005 | 0x00000000000c92b0 | 3f470442-20da-4293-b606-76f6cc9cecaa |
| 2026-11-05 14:46:49.180 | python.exe | 15400 | 0x3C28 | `unknown` | 0.0.0.0 | 0xc0000096 | 0x00000243d57a0f2e | 7d81516c-8ec0-4258-b18a-bc7a74164e4e |
| 2026-11-06 14:18:38.638 | python.exe | 43840 | 0xAB40 | `unknown` | 0.0.0.0 | 0xc000001d | 0x0000021081600f1a | 217a1238-eb14-47f1-8939-6f1286180f4a |
| 2026-11-09 07:51:27.170 | python.exe | 39848 | 0x9BA8 | `unknown` | 0.0.0.0 | 0xc0000005 | 0x0000022b4ba00fc2 | daaba0b5-4eec-4bc4-b06d-75e73a6c2a0e |
| 2026-11-09 08:21:50.445 | python.exe | 34996 | 0x88B4 | `unknown` | 0.0.0.0 | 0xc0000005 | 0x0000020019ae0fc3 | 5816c951-f7e7-48a4-b76f-fd956c254485 |

### WER (ID 1001): 46 entries

Paired WER rows (time, process, report id) are in `s51-crash/scratch/eventlog.csv`. First python APPCRASH cluster begins **2026-10-05 11:13:49** (pid 12544, `python312.dll`, `0xc0000005`). No python.exe 1000 between 2026-09-01 and that time (matches S51 clue).

Zola.Client.exe 1000 entries (Sep 29 ×9 `Microsoft.UI.Xaml.dll` / `0xc000027b`; Oct 13 ×1 `CoreMessagingXP.dll`) are listed above for completeness; process-identity work in Phase 2 will separate them from serve crashes.

## Log evidence extracts (G-LOGS)

Working folder: `C:\Users\test\Dev\zola-spikes\s51-crash\evidence\` — **646** files, allowlisted fields only (event names, ids, pids, lengths, reasons, timestamps).

- Shared (no timestamps in source): `ALL_serve-stderr.txt` SHA-256 `961DB5CA65F25CAEF9CB3D5D5667F017A11D6D052C87D9C61644544A07D2A9E8` — listening ports only; no traceback frames found in current file.
- Windowing uses naive local wall-clock (±5 min) so PDT/PST embedded offsets do not skew matches.
- `zola_workspace.log`: no usable timestamps on lines → all 43 windows empty (file present; not time-sliceable).
- `supervisor.log` oldest: 2026-10-10 → earlier crashes marked not_available for supervisor.
- `agent.log` current starts 2026-10-09; `agent.log.1` covers 2026-09-22 → 2026-10-09.
- Phone rotations begin ~2026-11-03; watcher current from 2026-10-30 (`zola_watcher.log.1` earlier).

### Per-log window summary (43 crash times)

| Log | With lines | Empty window | Not available (rotated out) | Notes |
|-----|----------:|-------------:|----------------------------:|-------|
| supervisor | 24 | 3 | 16 | oldest 2026-10-10 |
| display-state | 42 | 1 | 0 | |
| voice-timeline | 38 | 5 | 0 | names/times only |
| presence | 43 | 0 | 0 | event tags only |
| server-requests | 1 | 33 | 9 | sparse |
| serve-stderr | — | — | — | shared file, no timestamps |
| agent | 26 | 1 | 16 | + agent.1 for earlier |
| agent.1 | 16 | 27 | 0 | ends 2026-10-09 |
| zola_memory | 33 | 1 | 9 | |
| zola_watcher / .1 | 12 / 11 | 0 / 12 | 31 / 20 | |
| zola_phone / .1-.3 | 3 / 4 / 0 / 2 | varies | mostly N/A before Nov | |
| zola_workspace | 0 | 43 | 0 | no timestamps |

Full per-file SHA-256 list: `s51-crash/scratch/evidence_files.csv` (scratch; deleted at closeout). Evidence `*.txt` kept under the working folder (not committed).

## Tools present (read-only check)

| Tool | Status |
|------|--------|
| `cdb.exe` / Debugging Tools for Windows | **Not installed** (not on PATH; not under Windows Kits / VS / WinDbg paths) |
| WinDbg (Store / WinDbgX) | **Not installed** (`winget list` empty) |
| Python | `C:\Python314\python.exe` **3.14.4**; `py -0p` also lists Astral CPython **3.12.14** |
| Hermes venv Python | `hermes-agent\.venv\Scripts\python.exe` **3.12.14** (do not install into this) |
| Python `minidump` / `construct` packages | **Not** installed in system 3.14 |

## Tool proposal (needs Brian approval — G-DEPS / G-STOP)

**Preferred (smallest, privacy-aligned):** install **WinDbg** via winget (`Microsoft.WinDbg`) or Microsoft Store, outside the repo and Hermes venv. Provides `cdb.exe`.

Exact read commands per dump (output redirected to `s51-crash\scratch\<dump>.txt` only):

```text
cdb -z <dump-path> -c ".ecxr; !analyze -v; lm; ~* kp; q"
```

If `!analyze` is too chatty for G-DUMP-PRIVACY, use the narrower set:

```text
cdb -z <dump-path> -c ".ecxr; r; kv; lm vm; ~* kp; q"
```

Keep from that output only: exception code/address/params; faulting module + version + offset; module list (name/version/base); thread list; stack frames (`module!function+offset`). Discard registers beyond exception context, memory dumps, PEB/env/strings.

**Symbols:**
- Microsoft public symbols for `ntdll` / OS: `srv*C:\Users\test\Dev\zola-spikes\s51-crash\scratch\symbols*https://msdl.microsoft.com/download/symbols`
- Python 3.12 symbols if available for the uv build seen in faulting application path (`...\uv\python\cpython-3.12-windows-x86_64-none\python.exe`). Without them, frames may be `python312+offset` only (still usable for grouping).

**Fallback if WinDbg declined:** create a separate venv at `C:\Users\test\Dev\zola-spikes\s51-crash\.venv-dump` and `pip install minidump` (PyPI) there only. Scratch script reads exception record + module list + thread stacks from minidump streams (no memory/string scans). Weaker than cdb with symbols.

**Nothing installed until Brian approves.**

