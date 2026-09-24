# P3PRE Audit Progress — Presence UI Pre-Build

Diagnostic audit only. Source of truth for what this audit has completed.

## Repositories

| Repo | Path | Branch | HEAD | Notes |
|---|---|---|---|---|
| zola-windows | `C:\Users\test\Dev\zola-windows` | `audit/p3pre-presence-ui` | `c05bdfc0301b76b5940b7d019bd0f79fa89beeef` | Expected HEAD matched. `main` was already at this SHA (`docs: record P2-LORE merge SHA on main`). Working tree was clean before the branch. |
| hermes-agent | `C:\Users\test\Dev\hermes-agent` | detached HEAD | `345cd2b057a452236de401d3534b8502a7465e8d` | `git describe --tags` → `v2026.9.14`. `git status` clean (no porcelain). Not modified. |

Output directory: `zola-architecture/audit/p3pre-presence-ui/`

Spike folder (outside both repos, never committed): `C:\Users\test\Dev\zola-spikes\p3pre-helix\`

## Phase status

| Phase | Name | Status |
|---|---|---|
| 1 | Setup | COMPLETE |
| 2 | Client Surface Map | COMPLETE |
| 3 | GLB Asset Inventory and Capability Map | COMPLETE |
| 4 | Helix Rendering Spike | COMPLETE |
| 5 | Presence UI Architecture: Windows Applicability Map | COMPLETE |
| 6 | HUD and Dock Data-Source Inventory | COMPLETE |
| 7 | Carry-over Confirmation | COMPLETE |
| 8 | Synthesis | COMPLETE |
| 9 | Closeout | COMPLETE |
| Audit documents commit | `0b331c2b6d3b70d8b6af4777393eb20d2ffb162d` | |

## Guardrails summary

- **G-SCOPE:** Diagnostic only. Spike lives outside the repo. Findings only under the output directory.
- **G-NOCHANGE:** No source, build, project, config, or asset files in `zola-windows` outside the output directory. No Hermes profile edits. No Python installs.
- **G-ARCH:** `Zola_Presence_UI_Architecture.md` is truth except K1 (GLB replaces SVG). Conflicts are findings.
- **G-QUALITY:** Every finding names a file, member, line range, glTF field, package, or measured number.
- **G-CLOSEOUT:** Does not start until the developer says "proceed to closeout".
- **G-NO-CROSS-SCOPE:** Android project is not opened. Android wave status is not a Windows score. K7 colour and type values are the approved exception.
- **G-DEPS:** Spike package commands are the only approved installs, and only inside the spike folder.
- **G-HUMAN-CHECK:** Phase 4 pauses for a reply that starts with `spike check:`. GLB hash mismatch would have stopped the audit; it did not.
- **G-RENDER-AC:** R1–R8 scored separately per package set.

## Toolchain (Phase 1)

Recorded 2026-09-24 from this machine.

`dotnet` is not on the agent shell `PATH` (`The term 'dotnet' is not recognized`). The SDK is installed at `C:\Program Files\dotnet\dotnet.exe`. Session `PATH` will be extended for spike commands only; the machine `PATH` is not changed.

```
.NET SDK: 9.0.318 (MSBuild 17.14.51+25f168cee)
OS: Windows 10.0.26200, RID win-x64
SDKs: 9.0.318 only
Runtimes: Microsoft.NETCore.App 8.0.31, 9.0.20
          Microsoft.WindowsDesktop.App 8.0.31, 9.0.20
          Microsoft.AspNetCore.App 8.0.31, 9.0.20
Workloads: none listed
global.json: not found
```

GPU (`Win32_VideoController`):

| Name | DriverVersion | DriverDate |
|---|---|---|
| Intel(R) Iris(R) Xe Graphics | 32.0.101.7088 | 2026-06-16 |
| DisplayLink USB Device | 11.5.6380.0 | 2024-12-17 |
| DisplayLink USB Device | 11.5.6380.0 | 2024-12-17 |

## Reference asset hashes

| File | Exists | Bytes | Expected SHA-256 | Actual SHA-256 | Result |
|---|---|---|---|---|---|
| `zola.glb` | yes | 33,972,240 | `1edf2bf5898528fd405cd3131fcf75548c6d5d1e893501467c65845b5d7a054b` | `1edf2bf5898528fd405cd3131fcf75548c6d5d1e893501467c65845b5d7a054b` | match |
| `zola_concept_reference.png` | yes | 1,894,981 | `71392aa9ea71bd43f3612030866e51893770c9c57f12ee6ed4b8a4dafc483e6e` | `71392aa9ea71bd43f3612030866e51893770c9c57f12ee6ed4b8a4dafc483e6e` | match (1122×1402) |
| `android_hud_reference.png` | yes | 415,983 | `8493a1aec5d0eb19d0f948a5cd683d3472fe5330825f765f9478f4097614647c` | `8493a1aec5d0eb19d0f948a5cd683d3472fe5330825f765f9478f4097614647c` | match. The earlier expected value `c47e…` was a superseded prompt copy. |
| `fonts\rajdhani_regular.ttf` | yes | 352,088 | `f0ba67d6ef91bcff8b0e43a051f7483dd83ebfcade19880cd15df29890234d2e` | match | match |
| `fonts\rajdhani_semibold.ttf` | yes | 363,500 | `5fd51c1334cafd3654059b0ee61aa470088a70e4637a9cfc0274557c751eb0cd` | match | match |
| `fonts\orbitron_regular.ttf` | yes | 24,716 | `739162ac8e6fcadb559226f2fee57f55baad126728cec901b321042c7224088e` | match | match |
| `fonts\orbitron_medium.ttf` | yes | 24,752 | `0963c8736d45390ebf17d75486d581f6ca4ad186c221801891a5801bb17df41b` | match | match |

`zola.glb` matched. The Android HUD image matches the corrected expected hash (`P3PRE-AUD-01` [MATCH]).

## Running findings

| ID | Severity | File/asset/package | One-line summary |
|---|---|---|---|
| P3PRE-AUD-01 | — | `android_hud_reference.png` | [MATCH] SHA-256 `8493a1ae…647c`. The earlier `c47e…` expected value was a superseded prompt copy. |
| P3PRE-AUD-02 | MEDIUM | `MainWindow.xaml` | [GAP] Permanent composer and header, not a contextual dock (§15–§16). |
| P3PRE-AUD-03 | — | `MainWindow.xaml.cs` `SubmitTurnAsync` | [MATCH] Phase 1/2 smoke behaviors share one submit path and route actions through the controller. |
| P3PRE-AUD-04 | HIGH | `MainWindow.xaml.cs` 316–394 `ApplyVoiceChrome` | [RISK] Voice-state and mic labels are derived in the window, not in `VoiceController`. |
| P3PRE-AUD-05 | MEDIUM | `MainWindow.xaml.cs` transcript and chrome writes | [RISK] Bubbles, scroll, and status text are hard-wired to named elements. |
| P3PRE-AUD-06 | LOW | `MainWindow.xaml.cs` 39; `App.xaml` | [GAP] 960×720 theme-following window; no obsidian tokens or custom fonts. |
| P3PRE-AUD-07 | — | `zola.glb` | [MATCH] K3 inventory confirmed (15 morphs, off-origin node, four 2048 JPEGs). |
| P3PRE-AUD-08 | — | `zola.glb` morph names | [MATCH] Blink, jaw, and six viseme targets exist. |
| P3PRE-AUD-09 | LOW | `zola.glb` morphs | [GAP] Blink suppression is not a morph target. |
| P3PRE-AUD-10 | MEDIUM | `zola.glb` morphs | [GAP] No negative mouth-curve target. |
| P3PRE-AUD-11 | MEDIUM | `zola.glb` morphs | [GAP] `eyeSoftness` has no target. |
| P3PRE-AUD-12 | MEDIUM | `zola.glb` morphs | [GAP] `projectionStability` has no geometry. |
| P3PRE-AUD-13 | HIGH | `zola.glb` | [GAP] No separate eye geometry for micro-saccade. |
| P3PRE-AUD-14 | HIGH | `zola.glb` | [GAP] No hair mesh for strand shimmer. |
| P3PRE-AUD-15 | HIGH | `zola.glb` | [GAP] No pixel-projection geometry. |
| P3PRE-AUD-16 | HIGH | `zola.glb` `materials[0]` emissive | [RISK] One near-black emissive map; chest glow is not separable. |
| P3PRE-AUD-17 | — | repo `.gitattributes` | [MATCH] 34 MB file is under GitHub's 100 MB limit; LFS is not configured. |
| P3PRE-AUD-18 | HIGH | Helix baseline render | [RISK] Much darker than the Android HUD reference. Fidelity, not a missing mesh. |
| P3PRE-AUD-19 | MEDIUM | `Viewport3DX` in XAML | [RISK] XAML construction crashes. Code construction renders. |
| P3PRE-AUD-20 | MEDIUM | rendered node origin | [RISK] Bust is near the origin, not at the glTF translation −1.75. |
| P3PRE-AUD-21 | HIGH | `PhongMaterialCore` | [RISK] Importer did not produce PBR. Metallic-roughness map is unbound. |
| P3PRE-AUD-22 | — | root `Grid` accelerator | [MATCH] `Ctrl+Space` fired while the viewport had focus. |
| P3PRE-AUD-23 | MEDIUM | `EnvironmentMap3D.SkipRendering` | [RISK] Cube can be hidden (`#080808` remains). Phong shows no measurable light from it. |
| P3PRE-AUD-24 | MEDIUM | Helix spike working set | [RISK] 168 MB before the GLB, 671 MB after the load. The model accounts for most of it. |
| P3PRE-AUD-25 | MEDIUM | `Viewport3DX.BackgroundColor` alpha 0 | [GAP] A radial gradient behind the viewport did not show through. |
| P3PRE-AUD-26 | HIGH | Helix spike Cycle 60 s | [RISK] Continuous animation cost 1.8% CPU and 34.5% summed GPU on the Iris Xe. Static and minimized were about 0% GPU. |

## Spike log

All commands in `C:\Users\test\Dev\zola-spikes\p3pre-helix\`. `dotnet` invoked after prepending `C:\Program Files\dotnet` to the session PATH only.

| Command | Exit |
|---|---|
| `python parse_glb.py` (Hermes venv) | 0 |
| `python extract_textures.py` | 0 |
| `dotnet add package Microsoft.WindowsAppSDK --version 2.5.1` | 0 |
| `dotnet add package Microsoft.Windows.SDK.BuildTools --version 10.0.26100.4654` | 0 |
| `dotnet add package HelixToolkit.WinUI.SharpDX --version 3.1.2` | 0 |
| `dotnet add package HelixToolkit.SharpDX.Assimp --version 3.1.2` | 0 |
| `dotnet build -c Debug -p:Platform=x64` | 1 (WMC9999; later C# errors fixed) |
| `dotnet build -c Debug -r win-x64` | 0, 0 warnings |

Set A is in use. The spike window is running for the visual check. Full command log also in `spike-commands.log` in the spike folder.

## Documents of truth read before Phase 1

- `zola-architecture/Zola_Presence_UI_Architecture.md` (full, §1–§25)
- `zola-architecture/Zola Master Architecture Plan.md` Windows Track notes (`S5`, `C1`, `C3`, Tier 1) and endpoint / presence sections
- `PHASE2_BUILD_PLAN.md`: `P2-D07`, `P2-D08`, `P2-D12`, Phase 2 Exit Checklist
- `PHASE1_BUILD_PLAN.md`: Track 1 (Path B, unreachable), Track 3 (sessions UI)
- `identity/VOICE_CONFIG.md`
- Progress: `P1-CLIENT`, `P1-SESSION`, `P2-VOICE`, `P2-SPEAK`, `P2-WAKE` (smoke-tested behaviors)
- `ROADMAP.md`, `DESIGN_DECISIONS.md`, `OPEN_QUESTIONS.md`
- Prior audits (cross-check): `Zola_WINH02_Audit_01_SurfaceInventory.md`, `Zola_WINH02_Audit_02_DesktopReference.md`
