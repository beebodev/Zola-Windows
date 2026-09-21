# WINH11 Audit 05 — Sandboxing, Telemetry, and Process Privilege

Pinned tag: `v2026.9.14` (Hermes Agent v0.21.3)
Commit: `345cd2b057a452236de401d3534b8502a7465e8d`

Half B inventory except item 3 (runtime privilege), which is labeled Half A if it touches access control — here it is primarily Half B `[MECHANISM]`, with UAC limited to gateway scheduled-task install.

Privacy Plan §2/§3 “data has purpose or it is not collected” / explicit consent: this phase only asks whether Hermes’s **own** telemetry would violate that for a Windows build.

---

## 1. Electron sandbox / context isolation

Shared chat-window preferences (`apps/desktop/electron/session-windows.ts` `chatWindowWebPreferences` L46–57):

- `contextIsolation: true`
- `sandbox: true`
- `nodeIntegration: false`
- `preload` set
- `webviewTag: true` (guest webviews; still under the same isolation flags)
- `devTools: true` (packaged builds can open DevTools — convenience, not a sandbox off-switch)

This is the standard Electron hardening trio. Primary and secondary session windows share this helper (comment L13–18) so they cannot drift.

**Windows-specific weakening:** `apps/desktop/electron/windows-sandbox-fallback.ts` recovers from Chromium GPU/renderer `STATUS_BREAKPOINT` (`0x80000003`, electron#51761 / hermes-agent#38216):

1. ACL grant `S-1-15-2-2` (ALL APPLICATION PACKAGES) RX on the install tree (`install.ps1` L4300–4308 does this at install; launch repeats only after an aborted boot).
2. `--no-sandbox` after signature-confirmed GPU/renderer breakpoint death, or two consecutive mid-boot aborts (L15–22, `BOOT_ABORTS_BEFORE_FALLBACK = 2`).
3. Sticky per app version; re-probed after update.

`updater-process.ts` `sandboxFallbackFromEnv` (L200–209): `ELECTRON_DISABLE_SANDBOX` or argv `--no-sandbox` is treated as a user/host opt-out and preserved across relaunch.

On a healthy Windows host the renderer is sandboxed. On the documented failure mode the app **intentionally disables the Chromium sandbox** so the UI can boot. That is a real, code-backed weakening — not theoretical.

**Label:** `[MECHANISM]` `WINH11-AUD-19` (MEDIUM) — `contextIsolation` / `sandbox` / `nodeIntegration: false` on chat windows.

**Label:** `[RISK]` `WINH11-AUD-20` (MEDIUM) — Windows fallback can relaunch with `--no-sandbox` after GPU/renderer breakpoint or boot-loop.

---

## 2. Telemetry

**Product claim:** `website/docs/reference/faq.md` L54 — “Hermes Agent does not collect telemetry, usage data, or analytics. Your conversations, memory, and skills are stored locally in `~/.hermes/`.”

**Verified in this tag (not assumed from the FAQ):**

| Surface | Behavior |
|---|---|
| Dashboard `/api/analytics` | Local usage/cost from session history (`website/docs/user-guide/features/web-dashboard.md` L280, L513–515). Config `show_token_analytics` default **false** (`config_defaults.py` near L2830 per docs). |
| Computer-use | `cua_telemetry` default **False** (`hermes_cli/config_defaults.py` L2279). Docs: “default: false (telemetry off)” (`computer-use.md` L475). Opt-in PostHog path, not always-on. |
| Vercel sandbox SDK | `tools/environments/vercel_sandbox.py` L44–46: SDK default-on telemetry is forced off via `os.environ.setdefault("VERCEL_TELEMETRY_DISABLED", "1")` before import. “Hermes policy is opt-in only.” |
| Desktop `apps/desktop` | No Sentry/PostHog/crashReporter client in renderer/main (search of `apps/desktop` for those names hits MCP directory metadata and a storage-subscriber comment, not a collector). |
| Skill usage sidecar | Local JSONL under `HERMES_HOME` (`tools/skill_usage.py`) — on-device, not a vendor beacon. |

No always-on first-party analytics pipeline was found in the Desktop app or CLI. Optional third-party SDK telemetry is default-off or explicitly disabled.

This **does not** conflict with Privacy Plan §2/§3 for Hermes’s own collection. Provider-side retention (OpenRouter, ElevenLabs, etc.) is a third-party contract issue, not Hermes telemetry — out of this item.

**Label:** `[MECHANISM]` `WINH11-AUD-21` (LOW) — no always-on Hermes telemetry; CUA/Vercel paths are opt-in or forced off; dashboard analytics are local.

---

## 3. Process privilege at runtime

**Normal operation:** `hermes serve`, the Desktop sidecar, and the JSON-RPC gateway run as the **logged-in user**. NSIS `perMachine: false` (Audit_04) means the installed `Hermes.exe` is a per-user binary. No `requireAdministrator` manifest was found for the Electron app.

**Elevation that does exist** is operator-initiated, for **Windows Gateway scheduled-task install/uninstall**, not for chat:

- `hermes_cli/gateway_windows.py` `_is_running_as_admin` L152–158 (`IsUserAnAdmin`).
- `_launch_elevated_gateway_command` L169–189: `ShellExecuteW(..., "runas", ...)` UAC prompt for `gateway install` / `gateway uninstall`.
- Called when schtasks would otherwise Access Denied (L778–783, L801, L1123–1129). If the user declines UAC, install falls back to Startup-folder (`_install_startup_fallback`).

The elevated child is a hidden `python.exe -m hermes_cli.main gateway install|uninstall`. It is not the Desktop renderer and is not required for `hermes serve`.

**Terminal `sudo`:** `terminal_tool_sudo.py` is a tool-approval concern already covered in WINH07/WINH08. It is not an unattended background admin service. Not re-audited.

**Label:** `[MECHANISM]` `WINH11-AUD-22` (LOW) — runtime is the logged-in user; UAC only for gateway scheduled-task install/uninstall. Does not by itself satisfy §9 authentication-before-data-management (`WINH11-AUD-06`); it only shows the agent does not need admin to operate.

---

## Finding table (this phase)

| ID | Half | Label | Severity | File | One-line |
|---|---|---|---|---|---|
| WINH11-AUD-19 | B | MECHANISM | MEDIUM | `session-windows.ts` L46–57 | Electron `contextIsolation` + `sandbox` + `nodeIntegration: false` |
| WINH11-AUD-20 | B | RISK | MEDIUM | `windows-sandbox-fallback.ts` L15–22 | Windows can fall back to `--no-sandbox` |
| WINH11-AUD-21 | B | MECHANISM | LOW | `config_defaults.py` L2279; `vercel_sandbox.py` L44–46 | No always-on Hermes telemetry |
| WINH11-AUD-22 | B | MECHANISM | LOW | `gateway_windows.py` L152–189, L778–783 | Runs as user; UAC only for gateway task install |
