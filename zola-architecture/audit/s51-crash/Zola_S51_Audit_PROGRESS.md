# Zola S51 Audit — Progress

**Prompt:** `C:\Users\test\Dev\zola-spikes\prompts\S51-CRASH_Audit_Prompt_v1.1.md`
**Prompt SHA-256 (verified match):** `b6a6f89820bc120bd0179373bcfaddb1c933499acf99895b78b17d6b1a085293`
**Audit started:** 2026-11-09
**SOP:** v3.0 (transition) · Audit template v2.1 · Diagnostic only (S51 serious / PR-D03)

---

## Repositories

| Repo | Branch | HEAD | Clean? |
|------|--------|------|--------|
| `zola-windows` | `s51-crash-audit` (from `main`) | `92e6cc473ae69d7dac88695229b58f24d0167cfb` at branch create | yes at create; audit docs only expected |
| `hermes-agent` | detached `v2026.9.14` | `345cd2b057a452236de401d3534b8502a7465e8d` (pin) | yes |

`main` = `origin/main` = `92e6cc473ae69d7dac88695229b58f24d0167cfb` before branch create. Working tree was clean.

---

## Folders

| Role | Path |
|------|------|
| Output | `zola-architecture/audit/s51-crash/` |
| Progress | `zola-architecture/audit/s51-crash/Zola_S51_Audit_PROGRESS.md` |
| Working (not git) | `C:\Users\test\Dev\zola-spikes\s51-crash\` |
| Evidence (kept) | `C:\Users\test\Dev\zola-spikes\s51-crash\evidence\` |
| Scratch (deleted at closeout) | `C:\Users\test\Dev\zola-spikes\s51-crash\scratch\` |
| Live dumps | `%LOCALAPPDATA%\ZolaClient\dumps\` |
| Saved dumps | `zola-spikes\crash-dumps-2026-10-17\`, `crash-dumps-2026-11-09\` |

---

## Guardrails (summary)

G-SCOPE · G-NOCHANGE · G-NO-RESTART · G-DEPS (no install until Phase 1 STOP verdict) · G-DUMP-PRIVACY · G-LOGS · G-EVENTLOG · G-HONEST · G-PID · G-QUALITY · G-NO-FIX · G-NO-CROSS-SCOPE · G-STOP · G-CLOSEOUT (wait for exact words).

---

## Phase status

| Phase | Status |
|-------|--------|
| 1 Setup, evidence inventory, tool plan | **COMPLETE** |
| 2 Crash timeline (which process / when) | **COMPLETE** → `Zola_S51_Audit_02_CrashTimeline.md` |
| 3 Dump analysis (where) | **COMPLETE** → `Zola_S51_Audit_03_DumpAnalysis.md` |
| 4 What changed ~2026-10-04/05 | **COMPLETE** → `Zola_S51_Audit_04_Changes.md` |
| 5 Code paths / request-on-crash | **COMPLETE** → `Zola_S51_Audit_05_CodePaths.md` |
| 6 Synthesis | **COMPLETE** → `Zola_S51_Audit_SYNTHESIS.md` |
| 7 Closeout | **COMPLETE** (2026-11-09 on `proceed to closeout`) |

---

## Closeout

- 7a: `git status` on `s51-crash-audit` — changes only under `zola-architecture/audit/s51-crash/`; `hermes-agent` clean at pin `345cd2b…`; no dumps/scratch in repo.  
- 7b: Privacy search — 0 hits for transcript/email/message text, keys/tokens, or dump memory contents (allowed fields only).  
- 7c: All phases COMPLETE. Findings: **8 — 3 HIGH, 4 MEDIUM, 1 LOW**.  
- 7d–7g: SHAs below.  
- 7h: Scratch deleted (keep `evidence\` and dump folders). WinDbg remains installed.

| Record | SHA |
|--------|-----|
| Audit commit | `6050cf250b6a22c8303b6a142c68341a6c71bfcf` |
| Tip-SHA commit | _(pending 7e)_ |
| Merge on `main` | _(pending 7f/g)_ |

---

## Findings

Eight IDs: S51-AUD-01 … S51-AUD-08 (see SYNTHESIS). **3 HIGH, 4 MEDIUM, 1 LOW.**

Dominant dump signature: **Group A** — PortAudio internal stream thread → unbacked address (export labels only; in vs out **UNRESOLVED**); 5 dumps including both 2026-11-09 crashes on `p10-closed`.

### Doc corrections (2026-11-09, pre-closeout)

- **03 / SYNTHESIS:** Group A restated; PortAudio frames = nearest exports; “output write” → **UNRESOLVED**; freed/replaced callback = **INFERENCE**.
- **05:** Full serve PortAudio stream inventory + concurrency pairs; shared `sd.play`/`sd.stop` cited **[EXT]**.
- **02 / SYNTHESIS:** Full python.exe AE signature table; `python312+0x3b1ff` **still occurs after** PortAudio-class appearance (last 2026-11-04).

### Brian verdicts (recorded in SYNTHESIS)

1. No Python PDB acquisition.  
2. Group A **blocks Phase 11** under PR-D03; fix track next.  
3. Fix priority: PortAudio crash first, lost-request announcement **same track**; sqlite / `0x3b1ff` → diagnostics only (`faulthandler`, serve pid logging).

---

## Phase 1 notes

- Prompt SHA verified against developer-supplied value.
- Dump preserve: copied live `python.exe.43840.dmp` into `crash-dumps-2026-11-09` (already had 34996/39848).
- Lore dumps **gone** (pruned): 25760, 41148, 18424, 15400.
- Unique dumps on disk: 6. Event-log Application Error rows: 43 (33 python.exe + 10 Zola.Client.exe). WER 1001: 46. .NET Runtime: 0.
- Evidence extracts: 646 allowlisted window files under working `evidence\`.
- Tools: no cdb/WinDbg; Python 3.14.4 + 3.12.14 available. Proposal: WinDbg/`cdb` preferred; `minidump` venv fallback.
- Brian tool verdict (verbatim, 2026-11-09):

> Verdict: Approved: install WinDbg (Microsoft.WinDbg) outside the repo and every venv. If the installed package doesn’t include cdb.exe, stop and report before trying anything else.
> Per dump, use exactly: cdb -z <dump> -c ".ecxr; kn 50; lm; ~* kn 30; q". Do not use kp, kv, !analyze, or any memory-display command. Output goes to scratch\ only; documents quote exception code, faulting module+offset, module names/versions and frame names only, never register values.
> Symbols: Microsoft public symbol server only. For Python symbols, first report whether matching PDBs exist for this exact interpreter build; don’t download any until I approve.
> Fallback (separate minidump venv): declined unless WinDbg fails.
> Include the 10 Zola.Client.exe crashes in the Phase 2 timeline (event-log fields only; there are no dumps for them).
> Proceed to Phase 2.

- WinDbg 1.2611.4001.0 installed. `cdb.exe` **present** at `...\Microsoft.WinDbg_...\amd64\cdb.exe` (also `cdbX64.exe` alias); version 10.0.29680.1004.
- Python PDB check (no download): uv CPython 3.12.14 `python312.dll` embeds PDB `python312.pdb` GUID `A87681D9-9A7A-496F-BE9D-4A0700F827C4` age 1. Local PDB beside DLL: **absent**. MSDL HEAD for that key: **404**. python.org/ftp/python/3.12.14/: source tarballs only (no Windows/amd64/pdb). GitHub `v3.12.14` release assets: **404**. **Matching PDBs for this exact build: not found.** Brian: **no Python PDB acquisition.**

See `Zola_S51_Audit_01_Inventory.md` for Phase 1 tables.
