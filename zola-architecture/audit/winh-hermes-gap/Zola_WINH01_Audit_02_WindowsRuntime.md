# WINH01 Audit 02 — Native Windows Runtime Verification

Requirement under test: "a Windows desktop build of Zola can run Hermes natively with full feature parity to Linux/macOS."

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`
Clone: `C:\Users\test\Dev\hermes-agent` (read-only)

Labels: [MATCH] / [GAP] / [PARTIAL] / [RISK] as defined for later WINH prompts. Used here only against the native-Windows full-parity requirement.

---

## 1. Exact tag / version and release date

**Answer:** Tag `v2026.9.14`, marketing name "Hermes Agent v0.21.3", commit `345cd2b057a452236de401d3534b8502a7465e8d`.

Evidence:
- `git checkout v2026.9.14` landed on `HEAD is now at 345cd2b057 chore(release): v0.21.3 (v2026.9.14)`.
- `git describe --tags --exact-match HEAD` → `v2026.9.14`.
- `pyproject.toml` L4: `version = "0.21.3"`.
- Annotated tag creator date: 2026-09-14 09:04:09 -0700.
- GitHub Releases API (`/releases/latest`): `tag_name: "v2026.9.14"`, `name: "Hermes Agent v0.21.3 (v2026.9.14)"`, `published_at: "2026-09-14T16:04:14Z"`, `draft: false`, `prerelease: false`.
- Local `git tag --sort=-creatordate` first five: `v2026.9.14`, `v2026.9.11`, `v2026.9.7`, `v2026.8.31`, `v2026.8.27` — matches the GitHub published list. This is a real published release, not a prerelease and not a lightweight tag older than the latest release.

There is no `CHANGELOG.md` in this tag. The GitHub release body is the changelog for this patch (`v2026.9.11...v2026.9.14`).

**Label:** not a parity finding (factual pin).

---

## 2. Does this tag support native Windows (not WSL2), per its own docs / changelog?

**Answer:** Yes, native Windows is a documented first-class install path. The same docs refuse full parity.

Root `README.md` L43-45 (verbatim):

> **Heads up:** Native Windows runs Hermes without WSL — CLI, gateway, TUI, and tools all work natively. If you'd rather use WSL2, the Linux/macOS one-liner above works there too. Found a bug? Please [file issues](https://github.com/NousResearch/hermes-agent/issues).

`README.md` L57-59 (verbatim):

> **Windows:** Native Windows is fully supported — the PowerShell one-liner above installs everything. If you'd rather use WSL2, the Linux command works there too. Native Windows install lives under `%LOCALAPPDATA%\hermes`; WSL2 installs under `~/.hermes` as on Linux.

`website/docs/user-guide/windows-native.md` L10 (verbatim):

> Hermes runs natively on Windows 10 and Windows 11 — no WSL, no Cygwin, no Docker.

Caveat language, same file L85-87 and L99-102 (verbatim):

> Everything except the dashboard's embedded terminal pane runs natively on Windows.

> The dashboard's `/chat` tab embeds a real terminal via a POSIX PTY (`ptyprocess`). Native Windows has no equivalent primitive; Python's `pywinpty` / Windows ConPTY would work but is a separate implementation — treat as future work. **The rest of the dashboard works natively** — only that one tab shows a "use WSL2 for this" banner.

The GitHub release notes for `v2026.9.14` do **not** restate Windows support or list Windows-only gaps. They mention "Windows updates stop reporting false failures" only in the *previous* release body for `v2026.9.11` (fetched from the releases HTML, still in this repo's history). This patch release does not add a new Windows support claim.

**Docs-vs-docs tension:** `README.md` says "fully supported" and "CLI, gateway, TUI, and tools all work natively." `windows-native.md` immediately qualifies that with a feature matrix that marks dashboard `/chat` as native-Windows ✗. See Q4 and finding WINH01-AUD-03 for a further docs-vs-code conflict on that same pane.

**Label:** [PARTIAL] — native Windows exists; the project does not claim full parity.

Finding **WINH01-AUD-01** — [PARTIAL] — MEDIUM — `README.md` L43-45 + `website/docs/user-guide/windows-native.md` L85-102.

---

## 3. Actual native-Windows code path (process spawn, PTY, file paths)

**Answer:** Yes. This tag has explicit `sys.platform == "win32"` / `sys.platform.startswith("win")` branches for stdio, shell spawn, PTY, and path normalization. Native Windows is not "run the Linux scripts under WSL."

### Process spawning / shell

- `tools/environments/local.py::_windows_bash_candidates` (L364-383) and `_find_bash` (L386-413). On Windows, commands run through `bash.exe`. Resolution order (from the function and from `windows-native.md` L108-114): `HERMES_GIT_BASH_PATH`, `%LOCALAPPDATA%\hermes\git\bin\bash.exe`, `%LOCALAPPDATA%\hermes\git\usr\bin\bash.exe`, Git-for-Windows under Program Files, then PATH. Probe helper: `tools/environments/local_gitbash_probe.py`.
- `tools/process_registry.py` (~L930-952): `from winpty import PtyProcess` on Windows vs `from ptyprocess import PtyProcess` on POSIX; `use_pty` requests a ConPTY via pywinpty. Comments at L1948-1949 document ConPTY line-ending (`\\r` vs `\\n`) behavior.

### PTY / terminal

- POSIX dashboard bridge: `hermes_cli/pty_bridge.py`.
- Windows dashboard bridge: `hermes_cli/win_pty_bridge.py` — module docstring: "Windows ConPTY bridge for the `hermes dashboard` chat tab." `WinPtyBridge.spawn` (L57-71) calls `winpty.PtyProcess.spawn`.
- Selector: `hermes_cli/web_server_chat.py` L26-33 (verbatim comment): "POSIX uses pty_bridge (fcntl/termios); native Windows uses win_pty_bridge (pywinpty/ConPTY); same surface, no handler guards." Then `if sys.platform.startswith("win"): from hermes_cli.win_pty_bridge import WinPtyBridge as PtyBridge`.
- Dependencies: `pyproject.toml` L136-141 — `ptyprocess` when `sys_platform != 'win32'`; `pywinpty` and `pywin32` when `sys_platform == 'win32'`.

### File-path handling

- `tools/file_tools_paths.py::_host_text` (L132-139) translates Git Bash `/c/Users/...` paths via `_msys_to_windows_path`.
- `tools/file_tools_paths.py::_anchor` (L142-154): `if sys.platform == "win32": import ntpath` and `Path(ntpath.normpath(text))`.
- `hermes_cli/stdio.py::configure_windows_stdio` (L47+): `SetConsoleCP(65001)`, reconfigure stdout/stderr/stdin to UTF-8, set `PYTHONIOENCODING` / `PYTHONUTF8`, default `EDITOR=notepad`. `is_windows()` (L18-20) is `sys.platform == "win32"`.
- Memory file locking: `tools/memory_tool.py` L18-28 — `fcntl` on Unix, `msvcrt` on Windows.
- `pyproject.toml` L111-116 — `tzdata` only on `sys_platform == 'win32'` because Windows has no IANA zoneinfo.

### Install / data layout

- Installer: `scripts/install.ps1` (PowerShell 5.1 compatible). Default `HermesHome` = `%LOCALAPPDATA%\hermes` (L33-34).
- `docker-compose.windows.yml` L2-7: Windows Docker Desktop compose overlay (host networking removed; Windows volume path).

**Label:** [PARTIAL] for full parity (the native path is real, but the shell is Git Bash, not a native Windows process model). [MATCH] for "there is a native code path."

Finding **WINH01-AUD-07** — [PARTIAL] — MEDIUM — `tools/environments/local.py` L364-413.

---

## 4. Features docs / changelog say are not yet available on native Windows

Listed from this tag's in-tree docs and code (not live GitHub issues):

1. **Dashboard `/chat` embedded terminal pane** — `website/docs/user-guide/windows-native.md` L99-102 and L87-100 feature matrix (`Dashboard /chat` native Windows ✗, WSL2 ✓). Repeated in `website/docs/user-guide/features/web-dashboard.md` L89: "pywinpty (native Windows — note that the embedded TUI itself still requires WSL)" and L148: "POSIX kernel (Linux, macOS, or WSL2). The `/chat` terminal pane specifically needs a POSIX PTY — native Windows Python has no equivalent."
   - **Conflict with code in this same tag:** `hermes_cli/win_pty_bridge.py` and `hermes_cli/web_server_chat.py` L26-33 implement ConPTY for that pane. `web/AGENTS.md` L15 still says "ptyprocess (POSIX PTY — WSL works, native Windows does not)." Docs, AGENTS.md, and implementation disagree. Treat the docs as the published user-facing claim; treat the code as evidence the claim may be stale.

2. **Matrix E2EE / python-olm** — `tools/lazy_deps.py::_unsupported_feature_reason` L341-343 (verbatim):
   > unsupported on Windows: Matrix E2EE depends on python-olm, which has no Windows wheel and requires make + libolm to build from sdist. Run Hermes under WSL to use Matrix on Windows.
   - `pyproject.toml` L387-392: `python-olm` "has Linux-only wheels and no native build path on Windows or modern macOS. With matrix in [all], `uv sync --locked` on Windows tried to build it from sdist and failed on `make`."

3. **CJK FTS5 tokenizer** — `native/fts5_cjk/build.sh` is a bash/`gcc` script emitting `libfts5_cjk.so` (L15-18). No `.dll` / MSVC / `build.ps1` in that directory. This is an optional session-search accelerator (`native/fts5_cjk/README.md`), not the core FTS index (unicode61 FTS5 still runs via Python/SQLite).

4. **macOS-only bundled skills** — e.g. `skills/apple/imessage/SKILL.md` frontmatter `platforms: [macos]`. These are also unavailable on Linux; they are not Windows-vs-Linux gaps.

5. **Nix / systemd auto-start** — `nix/` and systemd units (e.g. kanban dispatcher mentioned in `cron/AGENTS.md`) are Linux packaging. Windows equivalent for the gateway is Scheduled Tasks (`windows-native.md` L167-193: `hermes gateway install` → `schtasks /Create /SC ONLOGON`).

The `v2026.9.14` GitHub release body does not list additional Windows-unavailable features.

**Labels:**
- Matrix: [GAP] HIGH — finding **WINH01-AUD-02**
- Dashboard `/chat` docs vs code: [RISK] MEDIUM — finding **WINH01-AUD-03**
- CJK FTS tokenizer: [GAP] LOW — finding **WINH01-AUD-06**

---

## 5. Native Windows installation method, prerequisites, compiled dependencies

**Answer:** PowerShell one-liner or optional GUI `Hermes-Setup.exe`. Core path does **not** require Visual Studio Build Tools on a stock Windows machine. Some optional extras do require a POSIX toolchain if forced.

### Installer type

- Canonical CLI: `iex (irm https://hermes-agent.nousresearch.com/install.ps1)` (`README.md` L49-50). In-tree script: `scripts/install.ps1`. Also `scripts/install.cmd`.
- GUI: Tauri bootstrap `apps/bootstrap-installer/` producing `Hermes-Setup.exe` (`Cargo.toml` L4, L14). `windows-native.md` L46-48: first launch calls `install.ps1` under the hood. `install.ps1` L60-75: `-IncludeDesktop` builds `apps/desktop`.
- No admin required (`windows-native.md` L26).

### What the installer provisions (`windows-native.md` L66-79; `install.ps1` header + stages)

1. `uv` (Astral Python manager) into `%USERPROFILE%\.local\bin` / `%LOCALAPPDATA%\hermes\bin`
2. Python 3.11 via `uv` (no pre-existing Python required)
3. Node.js 26 (winget, else portable tarball under `%LOCALAPPDATA%\hermes\node`)
4. PortableGit / MinGit (~45 MB) to `%LOCALAPPDATA%\hermes\git` if `git` is not on PATH
5. Clone to `%LOCALAPPDATA%\hermes\hermes-agent` + venv
6. Tiered `uv pip install` (`[all]` → smaller extras)
7. Sets `HERMES_GIT_BASH_PATH`, User PATH, `HERMES_HOME=%LOCALAPPDATA%\hermes`
8. Best-effort `cua-driver` unless `-SkipComputerUse` (`windows-native.md` computer-use docs; `install.ps1` `-SkipComputerUse`)
9. Lazy non-Python deps via `hermes_cli/dep_ensure.py`: ffmpeg, ripgrep (`BurntSushi.ripgrep.MSVC` winget id in `install.ps1` ~L1999 — a **prebuilt** ripgrep binary, not a request that the user own MSVC)

### Compiled / native dependencies

On the **default** install, native bits arrive as wheels or prebuilt binaries:

- `cryptography==50.0.0`, `pydantic`/`pydantic-core`, `Pillow`, `psutil`, `pywin32`, `pywinpty` — declared in `pyproject.toml` with Windows markers; CI comment in `tests-os.yml` L90-92 says `[all]` is "Windows/macOS-installable" after matrix/python-olm was removed from `[all]`.
- `tzdata` — pure data package, Windows-only marker.
- PortableGit, uv.exe, Node, ffmpeg, ripgrep — downloaded binaries.

**Not required for core:** a C compiler, Visual Studio Build Tools, or `make`.

**Would need a compiler / POSIX toolchain if the user enables them:**

- Matrix extra → `python-olm` sdist (`make` + libolm). Explicitly refused on win32 in `tools/lazy_deps.py` L341-343 rather than attempting the build.
- `native/fts5_cjk/build.sh` → `gcc`.
- Desktop/TUI native addon `node-pty` (`package.json` `allowScripts["node-pty@1.1.0"]`). Prebuilt Electron binaries are the normal path; a from-source rebuild can require node-gyp / MSVC. The signed desktop installer is the intended Windows GUI path, not a source build on a stock machine.
- Voice/wake extras (`faster-whisper`, `onnxruntime`, `openwakeword`) are **not** in `[all]` (`pyproject.toml` L381-385). They lazy-install; those packages generally ship Windows wheels, but this audit did not execute an install.

**Label:** [MATCH] for "can install and run natively on stock Windows without VS Build Tools" (core + `[all]` as defined). Not a match for every extra.

Finding **WINH01-AUD-08** — [MATCH] — LOW — `scripts/install.ps1` + `pyproject.toml` L19-141.

---

## 6. Does CI run tests on a Windows runner?

**Answer:** Yes, but only a Windows-specific subset. The main pytest suite is Linux-only. Desktop E2E is Linux-only and currently disabled.

| Workflow | Runner | What it covers |
|---|---|---|
| `.github/workflows/tests.yml` (via `ci.yaml` job `tests`) | Linux (ubuntu; see workflow comment in `tests-os.yml` L5-6) | Main Python suite. `windows_only` tests are **skipped** here by design (`tests-os.yml` L7-10). |
| `.github/workflows/tests-os.yml` (via `ci.yaml` job `tests-os`, L83-92) | `windows-latest-32-core` | `pytest -m "windows_only and not integration"` only. Fail if zero tests selected. Optional desktop-update `windows.ps1` tests when `desktop_updater` input is true. |
| `.github/workflows/installer-tests.yml` (via `ci.yaml` L108-113, gated on installer path changes) | `windows-latest` | `scripts/install.ps1` PowerShell tests on **Windows PowerShell 5.1 and pwsh 7** (8.3 short paths, Node/npm compatibility). |
| `.github/workflows/install-e2e.yml` + `install-e2e-windows-run.yml` | Windows (scheduled / tag / dispatch; **not** on pull_request — `install-e2e.yml` L42-44) | Real Windows install/update matrix (Hermes-Setup.exe, AutoHotkey, Playwright). |
| `.github/workflows/windows-venv-e2e.yml` | `windows-latest` | Live venv-holder / Telegram CLOSE-WAIT / process-registry E2E. Trigger: `push` to `wine2e/**` only — "Deliberately NOT wired to pull_request/main" (L11-13). |
| `.github/workflows/lint.yml` job `windows-footguns` | `ubuntu-latest` | Static scan `scripts/check-windows-footguns.py --all` (not a Windows runner; blocks `os.kill(pid, 0)` etc.). |
| `.github/workflows/e2e-desktop.yml` | `ubuntu-latest-32-core` (L18-23: "Playwright E2E (Linux)") | Electron under xvfb. `ci.yaml` L123-139: **`if: false`** — "Re-disabled (Sep 2026)". |
| `.github/workflows/rust-tests.yml` | not Windows (comment L12-14: Unix `cfg`; Windows half covered by `scripts/desktop-update/windows.ps1`) | Rust crate tests. |
| `.github/workflows/case-collision-check.yml` | Linux | Guards Windows/macOS case-insensitive filesystem collisions. |

Implication: a green PR CI does **not** mean the full agent/tool/gateway suite passed on Windows. Trust in the native-Windows claim should be proportional to the `windows_only` marker set plus installer E2E (the latter is not on every PR).

Finding **WINH01-AUD-04** — [RISK] — MEDIUM.
Finding **WINH01-AUD-05** — [RISK] — MEDIUM — desktop E2E disabled and Linux-only.

---

## 7. In-repo open / unresolved Windows issues

**Answer:** There is no `KNOWN_ISSUES.md` (or equivalent living Windows bug list) in this tag. Absence is not proof GitHub has no open Windows issues; this audit was instructed not to use a live GitHub API issue search as evidence.

In-repo tracked files that mention Windows failures:

- `tests/install/KNOWN_FAILURES.md` — "Confirmed historical upgrade limitations." Windows-specific records:
  - "Windows launcher self-lock": running `hermes.exe update` cannot replace `venv/Scripts/hermes.exe` (`Access is denied. (os error 5)`). Classified unfixable **in the update target** for releases `v2026.3.12` and `v2026.4.8` installer-script → hermes-update.
  - "July Windows app offers only a manual update for script installs" (`v2026.7.1`).
- `tests/install/e2e-assets/known-failures.json` / `.cjs` — machine-readable matchers for those historical legs.
- `tests-js/install-known-failures.test.ts` — JS tests for the matcher.

Those are historical upgrade-path classifications, not a current Windows runtime defect list for `v2026.9.14`.

Finding **WINH01-AUD-09** — [RISK] — LOW — no in-repo live Windows issue tracker; historical updater known-failures only.

---

## Roll-up against the requirement

"A Windows desktop build of Zola can run Hermes natively with full feature parity to Linux/macOS."

This tag supports **running Hermes natively on Windows** (CLI, gateway, TUI, Electron desktop, cron, browser tool, MCP, most extras) via `install.ps1` / `Hermes-Setup.exe` without WSL. It does **not** offer full parity:

- Matrix E2EE is a hard code-level refuse on win32.
- Shell/PTY semantics are Git Bash + ConPTY, not POSIX.
- Published docs still mark dashboard `/chat` as WSL-only while this tag contains a ConPTY implementation (unresolved conflict).
- Optional CJK FTS tokenizer is POSIX-build only.
- CI does not run the full test suite on Windows; desktop E2E is off.

Overall series-usable conclusion for later prompts: treat native Windows as **[PARTIAL]**, not [MATCH]. Do not assume Linux-only modules (Matrix olm, fts5_cjk `.so`, POSIX PTY comments in stale docs) work. Do not assume every pytest in `tests/` has been executed on win32.
