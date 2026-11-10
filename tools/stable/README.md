# tools/stable — Zola stable promotion, backup, restore

Scripts for PROC1-STABLE: a Release build of Zola outside the live checkout, with backup and restore at every promotion.

## Layout

| Path | Purpose |
|------|---------|
| `C:\Users\test\Zola\stable\<tag>\` | Release build output (`dotnet build -c Release -r win-x64 -o`) + `stable-manifest.json` only |
| `C:\Users\test\Zola\stable\_staging\<tag>\` | Prepare output (moved on Switch) |
| `C:\Users\test\Zola\stable\_promotions\<tag>\` | Comparison-set plugin bytes + `.prepare-record.json` (kept after Switch) |
| `C:\Users\test\Zola\stable\current.txt` | Active tag name, or `none` |
| `C:\Users\test\Zola\stable\backups\<tag>-<stamp>\` | Profile backup + `backup-index.json` |

## Prerequisites

- User env `ZOLA_HERMES_ROOT=C:\Users\test\Dev\hermes-agent` (set once; Phase 5 of PROC1-STABLE)
- Windows PowerShell 5.1
- Hermes venv Python for `sqlite_tool.py`
- .NET SDK; Android JBR + SDK for `assembleDebug` during Prepare (not TestMode)

## Prepare (Zola may keep running)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools\stable\Promote-Stable.ps1 -Prepare -Tag fix-s51f
```

Builds with `dotnet build <csproj> -c Release -r win-x64 -o _staging\<tag>\` (not `dotnet publish` — publish omitted `.xbf`/`.pri` and the Desktop copy APPCRASHed). Prepare derives expected `.xbf` paths from `.xaml` under the tag’s `windows-client\Zola.Client\` (excluding `bin\`/`obj\`), always requiring at least `Zola.Client.pri`, `App.xbf`, `MainWindow.xbf`, and `Themes\ZolaTokens.xbf`, and refuses naming any missing. Copies comparison-set plugins into `_promotions\<tag>\`, records pre-stable or current outgoing launch into `.prepare-record.json`, prints a read-only plugin diff. Removes the temporary git worktree.

## Switch (Zola must be closed)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools\stable\Promote-Stable.ps1 -Switch -Tag fix-s51f
# If plugins differ and Brian approved the list:
# ... -Switch -Tag fix-s51f -ApprovedPluginCopy
```

Rechecks staging + `_promotions`, backs up the live profile, runs a restore drill via `Restore-Stable.ps1 -Drill` (same code path as emergency restore), optionally updates plugins only when `-ApprovedPluginCopy` matches the Prepare-time diff exactly, writes the manifest (including `promotion_scripts_digest` / `promotion_scripts_dirty`), moves staging to `stable\<tag>\`, updates `current.txt` and the **Zola** shortcuts (real `.lnk` files). Failures after the first live change put everything back (plugins, `current.txt`, shortcuts by byte copy, staging), verifying each step.

## Restore

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools\stable\Restore-Stable.ps1 -Backup fix-s51f-yyyyMMdd-HHmmss
```

Restores to the **outgoing** release recorded in the backup (not the incoming tag). Live restore first takes a `pre-restore-*` backup, moves live-only files (and promotion-added plugins) into `_displaced\`, then restores. Default skips credentials; use `-IncludeCredentials` to include them. A pre-stable outgoing removes shortcuts, sets `current.txt` to `none`, and prints the fallback `dotnet run` command. A `pre-restore-snapshot` outgoing (undo) restores the profile/plugins, then puts back `current.txt` and the shortcut `.lnk` bytes from that backup. Unknown `outgoing.kind` values refuse before any change. If the live checkout HEAD differs from the recorded one, Restore warns that the fallback would run newer code. `-DesktopDir` / `-ProgramsDir` override shortcut folders (tests pass scratch dirs).

If a live restore **fails after** the `pre-restore-*` backup was taken, the FAIL line includes `pre_restore_backup=<name>` and the profile may be partially restored — undo with `Restore-Stable` on that `pre-restore-*` folder.

## Drill

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools\stable\Restore-Stable.ps1 -Backup <folder> -Target %TEMP%\zola-drill -Drill -ConfirmName <folder-name>
```

Writes only under `-Target`, skips credentials, deletes the scratch target whether pass or fail.

## Emergency

Close stable Zola and start from the live checkout:

`dotnet run --project C:\Users\test\Dev\zola-windows\windows-client\Zola.Client\Zola.Client.csproj`

## Tests

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools\stable\Test-StableScripts.ps1
```

Scratch roots under `%TEMP%` only; refuses live roots.
