# PROC1-STABLE: script tests — scratch roots only — PROC1-D12/D13
#Requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module (Join-Path $here 'StableCommon.psm1') -Force
$Promote = Join-Path $here 'Promote-Stable.ps1'
$Restore = Join-Path $here 'Restore-Stable.ps1'
$RepoRoot = Resolve-FullPath (Join-Path $here '..\..')
$HermesRoot = 'C:\Users\test\Dev\hermes-agent'

$script:Pass = 0
$script:Fail = 0
$script:Results = New-Object System.Collections.Generic.List[string]
# G3: every scratch this harness creates (dirs or log files)
$script:ScratchItems = New-Object System.Collections.Generic.List[string]

function Ok([string]$Name) { $script:Pass++; $script:Results.Add("PASS $Name") | Out-Null; Write-Host "PASS $Name" }
function Bad([string]$Name, [string]$Why) { $script:Fail++; $script:Results.Add("FAIL $Name :: $Why") | Out-Null; Write-Host "FAIL $Name :: $Why" }

function Register-ScratchItem([string]$Path) {
    if ($Path -and -not ($script:ScratchItems -contains $Path)) {
        $script:ScratchItems.Add($Path) | Out-Null
    }
}

function New-ScratchRoot([string]$Name) {
    $p = Join-Path $env:TEMP ("proc1-stable-test-" + $Name + "-" + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Force -Path $p | Out-Null
    Register-ScratchItem $p
    return $p
}

function New-TrackedTempFile([string]$Prefix) {
    $p = Join-Path $env:TEMP ($Prefix + [guid]::NewGuid().ToString('N') + '.log')
    Register-ScratchItem $p
    return $p
}

function Get-ProfileHashMapExclLogsCache([string]$ProfileRoot) {
    $map = [ordered]@{}
    $root = Resolve-FullPath $ProfileRoot
    if (-not (Test-Path -LiteralPath $root)) { return $map }
    Get-ChildItem -LiteralPath $root -Recurse -File -Force -ErrorAction SilentlyContinue | ForEach-Object {
        $rel = $_.FullName.Substring($root.Length).TrimStart('\').Replace('\', '/')
        if ($rel -match '^(logs|cache)(/|$)') { return }
        $map[$rel] = (Get-FileSha256Hex $_.FullName)
    }
    return $map
}

function Remove-TrackedScratch {
    foreach ($p in @($script:ScratchItems)) {
        if (-not $p) { continue }
        if (Test-Path -LiteralPath $p) {
            Remove-Item -LiteralPath $p -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
    # Also sweep this track's known TEMP patterns (drills created by Switch, etc.)
    Get-ChildItem -LiteralPath $env:TEMP -Force -ErrorAction SilentlyContinue | Where-Object {
        $_.Name -like 'proc1-stable-test-*' -or
        $_.Name -like 'zola-restore-drill-*' -or
        $_.Name -like 'putback-*' -or
        $_.Name -like 'restore-head-*'
    } | ForEach-Object {
        Remove-Item -LiteralPath $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
    }
}

function Assert-NoTrackTempLeftovers {
    $left = @(Get-ChildItem -LiteralPath $env:TEMP -Force -ErrorAction SilentlyContinue | Where-Object {
            $_.Name -like 'proc1-stable-test-*' -or
            $_.Name -like 'zola-restore-drill-*' -or
            $_.Name -like 'putback-*' -or
            $_.Name -like 'restore-head-*'
        } | ForEach-Object { $_.Name })
    if ($left.Count -gt 0) {
        Bad 'temp-cleanup-no-leftovers' (($left | Select-Object -First 20) -join ', ')
    } else {
        Ok 'temp-cleanup-no-leftovers'
    }
}

function New-MiniPlugins([string]$Root) {
    foreach ($rel in @(
            'zola_workspace\plugin.yaml', 'zola_workspace\__init__.py',
            'zola_memory\store.py', 'zola_memory\l6_hold_guard.py',
            'zola_tools\calculator.py', 'zola_tools\plugin.yaml', 'zola_tools\__init__.py',
            'zola_phone\runtime.py', 'zola_phone\outage.py',
            'zola_tts\deepgram_tts.py',
            'zola_workspace\tests\test_x.py', 'zola_workspace\__pycache__\x.pyc'
        )) {
        $f = Join-Path $Root $rel
        New-Item -ItemType Directory -Force -Path (Split-Path $f) | Out-Null
        Set-Content -LiteralPath $f -Value ("content:$rel") -NoNewline
    }
}

function New-SyntheticProfile([string]$Root, [string]$PluginsRoot) {
    New-Item -ItemType Directory -Force -Path $Root | Out-Null
    Set-Content -LiteralPath (Join-Path $Root 'config.yaml') -Value 'model: test' -NoNewline
    Set-Content -LiteralPath (Join-Path $Root 'SOUL.md') -Value 'soul' -NoNewline
    Set-Content -LiteralPath (Join-Path $Root 'auth.json') -Value '{"x":1}' -NoNewline
    New-Item -ItemType Directory -Force -Path (Join-Path $Root 'phone') | Out-Null
    Set-Content -LiteralPath (Join-Path $Root 'phone\pc_key.bin') -Value 'key' -NoNewline
    New-Item -ItemType Directory -Force -Path (Join-Path $Root 'logs') | Out-Null
    Set-Content -LiteralPath (Join-Path $Root 'logs\x.log') -Value 'log' -NoNewline
    New-Item -ItemType Directory -Force -Path (Join-Path $Root 'cache') | Out-Null
    Set-Content -LiteralPath (Join-Path $Root 'cache\c.bin') -Value 'cache' -NoNewline
    Copy-ComparisonSetToPromotions -HermesPluginsRoot $PluginsRoot -PromotionsTagDir $Root | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $Root 'plugins\zola_phone') | Out-Null
    Set-Content -LiteralPath (Join-Path $Root 'plugins\zola_phone\outage.py') -Value 'live-outage-only' -NoNewline

    $py = Join-Path $HermesRoot '.venv\Scripts\python.exe'
    $rootEsc = $Root.Replace('\', '\\')
    & $py -c @"
import sqlite3, os
root = r'$rootEsc'
os.makedirs(os.path.join(root, 'proactive'), exist_ok=True)
for path, wal in [
    (os.path.join(root, 'state.db'), True),
    (os.path.join(root, 'proactive', 'proactive.db'), False),
    (os.path.join(root, 'odd_store.dat'), False),
]:
    c = sqlite3.connect(path)
    c.execute('CREATE TABLE t(x INTEGER)')
    c.execute('INSERT INTO t VALUES (1)')
    c.execute('PRAGMA user_version=7')
    c.commit()
    if wal:
        c.execute('PRAGMA journal_mode=WAL')
        c.execute('INSERT INTO t VALUES (2)')
        c.commit()
    c.close()
open(os.path.join(root, 'state.db-journal'), 'wb').write(b'not-a-db-header!!!!!!')
"@
}

function New-Fixture([string]$Name) {
    $stable = New-ScratchRoot "$Name-s"
    $plugins = New-ScratchRoot "$Name-pl"
    New-MiniPlugins $plugins
    $profile = New-ScratchRoot "$Name-p"
    New-SyntheticProfile $profile $plugins
    $desktop = New-ScratchRoot "$Name-desk"
    $programs = New-ScratchRoot "$Name-prog"
    [pscustomobject]@{
        Stable   = $stable
        Profile  = $profile
        Plugins  = $plugins
        Desktop  = $desktop
        Programs = $programs
    }
}

function Get-TestPreStableLaunch {
    # PROC1-ID: injected prestable outgoing — independent of any real Zola.Client — PROC1-D13
    @{
        launch_command = 'dotnet run --project C:\Users\test\Dev\zola-windows\windows-client\Zola.Client\Zola.Client.csproj'
        checkout       = 'C:\Users\test\Dev\zola-windows'
        branch         = 'main'
        head           = '9d6458432c9e56e9a69f2f616e3da727acedfe10'
        client_exe     = 'C:\Users\test\Dev\zola-windows\windows-client\Zola.Client\bin\Debug\net9.0-windows10.0.19041.0\Zola.Client.exe'
    }
}

function Get-IdleRunningProbe {
    { [pscustomobject]@{ Running = $false; Reasons = @() } }
}

function Get-CommonPromoteArgs($fx) {
    @{
        StableRoot           = $fx.Stable
        ProfileRoot          = $fx.Profile
        HermesRoot           = $HermesRoot
        RepoRoot             = $RepoRoot
        DesktopDir           = $fx.Desktop
        ProgramsDir          = $fx.Programs
        TestMode             = $true
        RunningZolaProbe     = (Get-IdleRunningProbe)
        TestPreStableLaunch  = (Get-TestPreStableLaunch)
    }
}

function Invoke-SynPrepare {
    param($fx, $Tag = 'fix-s51f', $Commit = 'abc111')
    $c = Get-CommonPromoteArgs $fx
    & $Promote -Prepare -Tag $Tag @c -Synthetic `
        -SyntheticPluginsRoot $fx.Plugins -SyntheticCommit $Commit
}

function Invoke-SynSwitch {
    param($fx, $Tag = 'fix-s51f', $Commit = 'abc111', [switch]$NoApprove, $Inject, [switch]$ForcePluginPutBackFail)
    $c = Get-CommonPromoteArgs $fx
    $c['Tag'] = $Tag
    $c['Synthetic'] = $true
    $c['SyntheticCommit'] = $Commit
    if ($Inject) { $c['InjectAfterPluginCopy'] = $Inject }
    if ($NoApprove) {
        if ($ForcePluginPutBackFail) {
            & $Promote -Switch @c -ForcePluginPutBackFail
        } else {
            & $Promote -Switch @c
        }
    } else {
        if ($ForcePluginPutBackFail) {
            & $Promote -Switch @c -ApprovedPluginCopy -ForcePluginPutBackFail
        } else {
            & $Promote -Switch @c -ApprovedPluginCopy
        }
    }
}

function Update-PromoRecord($PromoDir, $ProfileRoot) {
    $rec = Get-Content (Join-Path $PromoDir '.prepare-record.json') -Raw | ConvertFrom-Json
    $newHashes = Get-PromotionsPluginHashMap -PromotionsTagDir $PromoDir
    $diff = Compare-PluginSets -TagMap $newHashes -LiveMap (Get-LivePluginHashMap -ProfileRoot $ProfileRoot)
    Write-JsonFile -Object ([ordered]@{
            tag                 = $rec.tag
            commit              = $rec.commit
            client_build_hash   = $rec.client_build_hash
            staging_file_hashes = $rec.staging_file_hashes
            plugin_tag_hashes   = $newHashes
            plugin_diff         = @{
                added   = [string[]]@(@($diff.Added) | ForEach-Object { "$_" } | Sort-Object)
                removed = [string[]]@(@($diff.Removed) | ForEach-Object { "$_" } | Sort-Object)
                changed = [string[]]@(@($diff.Changed) | ForEach-Object { "$_" } | Sort-Object)
                equal   = [bool]$diff.Equal
            }
            outgoing            = $rec.outgoing
            prepared_at         = $rec.prepared_at
            worktree_removed    = $true
        }) -Path (Join-Path $PromoDir '.prepare-record.json')
}

function Get-LnkInfo([string]$Path) {
    $w = New-Object -ComObject WScript.Shell
    $sc = $w.CreateShortcut($Path)
    [pscustomobject]@{ Target = $sc.TargetPath; WorkDir = $sc.WorkingDirectory }
}

# --- Tests ---

try {
    $fx = New-Fixture 'busy'
    Invoke-SynPrepare -fx $fx
    try {
        $c = Get-CommonPromoteArgs $fx
        $c['RunningZolaProbe'] = { [pscustomobject]@{ Running = $true; Reasons = @('injected') } }
        & $Promote -Switch -Tag 'fix-s51f' @c -Synthetic -SyntheticCommit 'abc111'
        Bad 'refuse-when-running' 'expected throw'
    } catch {
        if ("$($_.Exception.Message)" -match 'Refuse: Zola') { Ok 'refuse-when-running' } else { Bad 'refuse-when-running' $_.Exception.Message }
    }
} catch { Bad 'refuse-when-running' $_ }

try {
    # PROC1-ID: test-owned mutex via injected probe — ignore any real Zola.Client — PROC1-D13
    $mtxName = 'Local\ZolaTestMutexProc1'
    $mtx = New-Object System.Threading.Mutex($true, $mtxName)
    try {
        $script:Proc1IdHeldMutexName = $mtxName
        $st = Get-ZolaRunningStatus -Probe {
            $reasons = New-Object System.Collections.Generic.List[string]
            if (Test-MutexHeld $script:Proc1IdHeldMutexName) { $reasons.Add("mutex:$($script:Proc1IdHeldMutexName)") | Out-Null }
            [pscustomobject]@{ Running = ($reasons.Count -gt 0); Reasons = @($reasons) }
        }
        if ($st.Running -and ("$($st.Reasons)" -match 'ZolaTestMutexProc1')) {
            Ok 'refuse-held-mutex-detect'
        } else { Bad 'refuse-held-mutex-detect' "not detected:$($st.Reasons -join ',')" }
    } finally { $mtx.ReleaseMutex() | Out-Null; $mtx.Dispose() }
} catch { Bad 'refuse-held-mutex-detect' $_ }

try {
    $fx = New-Fixture 'badtag'
    try {
        $c = Get-CommonPromoteArgs $fx
        & $Promote -Prepare -Tag 'no-such-tag-proc1' @c
        Bad 'refuse-unknown-tag' 'expected throw'
    } catch {
        if ("$($_.Exception.Message)" -match 'Unknown tag') { Ok 'refuse-unknown-tag' } else { Bad 'refuse-unknown-tag' $_.Exception.Message }
    }
} catch { Bad 'refuse-unknown-tag' $_ }

try {
    try {
        & $Promote -Prepare -Tag 'fix-s51f' -StableRoot $DefaultStableRoot -ProfileRoot (New-ScratchRoot 'x') `
            -HermesRoot $HermesRoot -RepoRoot $RepoRoot -TestMode -Synthetic -SyntheticPluginsRoot (New-ScratchRoot 'y') `
            -DesktopDir (New-ScratchRoot 'd') -ProgramsDir (New-ScratchRoot 'p') `
            -RunningZolaProbe { [pscustomobject]@{ Running = $false; Reasons = @() } }
        Bad 'refuse-live-root' 'expected throw'
    } catch {
        if ("$($_.Exception.Message)" -match 'TestMode refuses live') { Ok 'refuse-live-root' } else { Bad 'refuse-live-root' $_.Exception.Message }
    }
} catch { Bad 'refuse-live-root' $_ }

# Shared fixture for backup/manifest/restore chain
$script:Shared = $null
try {
    $fx = New-Fixture 'bak'
    Invoke-SynPrepare -fx $fx
    Invoke-SynSwitch -fx $fx
    $script:Shared = $fx
    $bak = Get-ChildItem (Join-Path $fx.Stable 'backups') -Directory | Select-Object -First 1
    $idx = Get-Content (Join-Path $bak.FullName 'backup-index.json') -Raw | ConvertFrom-Json
    $paths = @($idx.files | ForEach-Object { $_.path })
    $ok = (-not ($paths | Where-Object { $_ -like 'logs/*' -or $_ -like 'cache/*' -or $_ -like '*-journal' })) `
        -and ($paths -contains 'odd_store.dat') `
        -and (@($idx.databases | Where-Object { $_.path -eq 'odd_store.dat' }).Count -eq 1) `
        -and (@($idx.databases | Where-Object { $_.integrity -ne 'OK' }).Count -eq 0)
    if ($ok) { Ok 'backup-sqlite-journal-nondb' } else { Bad 'backup-sqlite-journal-nondb' 'coverage' }
    if ($idx.outgoing.kind -eq 'pre-stable' -and $idx.incoming.tag -eq 'fix-s51f') { Ok 'backup-outgoing-incoming-first' } else { Bad 'backup-outgoing-incoming-first' 'kind' }

    $manifest = Get-Content (Join-Path $fx.Stable 'fix-s51f\stable-manifest.json') -Raw | ConvertFrom-Json
    $needed = @('tag','commit','client_build_hash','hermes_head','hermes_local_edit_digest','pip_freeze_digest','plugins_tag','plugins_installed','config_yaml_sha256','backup_folder','promotion_scripts_commit','promotion_scripts_digest','promotion_scripts_dirty','promoted_at')
    $missing = @($needed | Where-Object { -not ($manifest.PSObject.Properties.Name -contains $_) })
    $blob = $manifest | ConvertTo-Json -Depth 6
    if ($missing.Count -eq 0 -and $blob -notmatch 'token\.dpapi|api_key|BEGIN ') { Ok 'manifest-fields-no-secrets' } else { Bad 'manifest-fields-no-secrets' ($missing -join ',') }
    if ($manifest.PSObject.Properties.Name -contains 'promotion_scripts_digest' -and ($manifest.PSObject.Properties.Name -contains 'promotion_scripts_dirty')) {
        Ok 'promotion-scripts-digest-dirty'
    } else { Bad 'promotion-scripts-digest-dirty' 'missing' }
    $names = @(Get-ChildItem (Join-Path $fx.Stable 'fix-s51f') -Recurse -File | ForEach-Object { $_.Name })
    if (($names -contains 'stable-manifest.json') -and ($names -contains 'Zola.Client.exe') -and ($names -notcontains '.prepare-record.json')) {
        Ok 'stable-folder-purity'
    } else { Bad 'stable-folder-purity' ($names -join ',') }
    if (Test-Path (Join-Path $fx.Stable '_promotions\fix-s51f\.prepare-record.json')) { Ok 'promotions-record-kept' } else { Bad 'promotions-record-kept' 'missing' }

    # F5: real shortcuts after successful switch
    $deskLnk = Join-Path $fx.Desktop 'Zola.lnk'
    $progLnk = Join-Path $fx.Programs 'Zola.lnk'
    $exeExpected = Join-Path $fx.Stable 'fix-s51f\Zola.Client.exe'
    $workExpected = Join-Path $fx.Stable 'fix-s51f'
    if ((Test-Path $deskLnk) -and (Test-Path $progLnk)) {
        $di = Get-LnkInfo $deskLnk
        $pi = Get-LnkInfo $progLnk
        if ($di.Target -eq $exeExpected -and $di.WorkDir -eq $workExpected -and $pi.Target -eq $exeExpected -and $pi.WorkDir -eq $workExpected) {
            Ok 'shortcuts-point-at-stable-tag'
        } else { Bad 'shortcuts-point-at-stable-tag' "$($di.Target)|$($di.WorkDir)" }
    } else { Bad 'shortcuts-point-at-stable-tag' 'missing lnk' }
} catch { Bad 'backup-sqlite-journal-nondb' $_ }

try {
    $fx = New-Fixture 'pdiff'
    Invoke-SynPrepare -fx $fx
    $promo = Join-Path $fx.Stable '_promotions\fix-s51f'
    Set-Content -LiteralPath (Join-Path $promo 'plugins\zola_tools\calculator.py') -Value 'CHANGED' -NoNewline
    Set-Content -LiteralPath (Join-Path $promo 'plugins\zola_tools\new_mod.py') -Value 'NEW' -NoNewline
    Remove-Item -LiteralPath (Join-Path $promo 'plugins\zola_tools\__init__.py') -Force
    Update-PromoRecord $promo $fx.Profile
    $outageBefore = Get-FileSha256Hex (Join-Path $fx.Profile 'plugins\zola_phone\outage.py')
    try {
        Invoke-SynSwitch -fx $fx -NoApprove
        Bad 'plugin-diff-stop' 'expected STOP'
    } catch {
        if ("$($_.Exception.Message)" -match 'Plugin set differs') { Ok 'plugin-diff-stop' } else { Bad 'plugin-diff-stop' $_.Exception.Message }
    }
    Invoke-SynSwitch -fx $fx
    $outageAfter = Get-FileSha256Hex (Join-Path $fx.Profile 'plugins\zola_phone\outage.py')
    if ((Get-Content (Join-Path $fx.Profile 'plugins\zola_tools\calculator.py') -Raw) -eq 'CHANGED' `
            -and (Test-Path (Join-Path $fx.Profile 'plugins\zola_tools\new_mod.py')) `
            -and (-not (Test-Path (Join-Path $fx.Profile 'plugins\zola_tools\__init__.py'))) `
            -and ($outageBefore -eq $outageAfter)) {
        Ok 'plugin-apply-added-removed-changed'
    } else { Bad 'plugin-apply-added-removed-changed' 'state' }
} catch { Bad 'plugin-diff-stop' $_ }

try {
    $fx = New-Fixture 'recheck'
    Invoke-SynPrepare -fx $fx
    Invoke-SynSwitch -fx $fx
    if (Test-Path (Join-Path $fx.Stable 'fix-s51f\Zola.Client.exe')) { Ok 'switch-after-prepare-no-worktree' } else { Bad 'switch-after-prepare-no-worktree' 'missing' }

    $fx2 = New-Fixture 'tamper'
    Invoke-SynPrepare -fx $fx2
    Add-Content -LiteralPath (Join-Path $fx2.Stable '_promotions\fix-s51f\plugins\zola_tools\calculator.py') -Value 'TAMPER' -NoNewline
    try {
        Invoke-SynSwitch -fx $fx2
        Bad 'recheck-tamper-promotions' 'expected refuse'
    } catch {
        if ("$($_.Exception.Message)" -match 'Promotions recheck|hash changed') { Ok 'recheck-tamper-promotions' } else { Bad 'recheck-tamper-promotions' $_.Exception.Message }
    }
} catch { Bad 'switch-after-prepare-no-worktree' $_ }

try {
    $fx = New-Fixture 'putback'
    # Pre-existing real shortcuts
    New-ShortcutZola -LinkPath (Join-Path $fx.Desktop 'Zola.lnk') -TargetPath 'C:\old\Zola.Client.exe' -WorkDir 'C:\old'
    New-ShortcutZola -LinkPath (Join-Path $fx.Programs 'Zola.lnk') -TargetPath 'C:\old\Zola.Client.exe' -WorkDir 'C:\old'
    $beforeDesk = Get-FileSha256Hex (Join-Path $fx.Desktop 'Zola.lnk')
    $beforeProg = Get-FileSha256Hex (Join-Path $fx.Programs 'Zola.lnk')
    Invoke-SynPrepare -fx $fx
    $promo = Join-Path $fx.Stable '_promotions\fix-s51f'
    Set-Content -LiteralPath (Join-Path $promo 'plugins\zola_tools\calculator.py') -Value 'WILL-PUT-BACK' -NoNewline
    Set-Content -LiteralPath (Join-Path $promo 'plugins\zola_tools\added_only.py') -Value 'ADD' -NoNewline
    Remove-Item (Join-Path $promo 'plugins\zola_tools\plugin.yaml') -Force
    Update-PromoRecord $promo $fx.Profile
    $before = @{
        calc   = Get-FileSha256Hex (Join-Path $fx.Profile 'plugins\zola_tools\calculator.py')
        plugin = Get-FileSha256Hex (Join-Path $fx.Profile 'plugins\zola_tools\plugin.yaml')
        outage = Get-FileSha256Hex (Join-Path $fx.Profile 'plugins\zola_phone\outage.py')
    }
    $log = New-TrackedTempFile 'putback-'
    try {
        Invoke-SynSwitch -fx $fx -Inject { throw 'injected shortcut failure' } *> $log
        Bad 'putback-after-inject' 'expected failure'
    } catch {
        $stagingHashes = Get-DirectoryFileHashMap -Root (Join-Path $fx.Stable '_staging\fix-s51f')
        $rec = Get-Content (Join-Path $fx.Stable '_promotions\fix-s51f\.prepare-record.json') -Raw | ConvertFrom-Json
        $expectedStaging = ConvertTo-HashStringMap $rec.staging_file_hashes
        $stagingOk = $true
        foreach ($k in $expectedStaging.Keys) {
            if (-not $stagingHashes.Contains($k) -or $stagingHashes[$k] -ne $expectedStaging[$k]) { $stagingOk = $false }
        }
        foreach ($k in $stagingHashes.Keys) {
            if (-not $expectedStaging.ContainsKey($k)) { $stagingOk = $false }
        }
        $ok = ((Get-FileSha256Hex (Join-Path $fx.Profile 'plugins\zola_tools\calculator.py')) -eq $before.calc) `
            -and ((Get-FileSha256Hex (Join-Path $fx.Profile 'plugins\zola_tools\plugin.yaml')) -eq $before.plugin) `
            -and (-not (Test-Path (Join-Path $fx.Profile 'plugins\zola_tools\added_only.py'))) `
            -and ((Get-FileSha256Hex (Join-Path $fx.Profile 'plugins\zola_phone\outage.py')) -eq $before.outage) `
            -and (Test-Path (Join-Path $fx.Stable '_staging\fix-s51f\Zola.Client.exe')) `
            -and (-not (Test-Path (Join-Path $fx.Stable 'fix-s51f'))) `
            -and (-not (Test-Path (Join-Path $fx.Stable 'current.txt'))) `
            -and ((Get-FileSha256Hex (Join-Path $fx.Desktop 'Zola.lnk')) -eq $beforeDesk) `
            -and ((Get-FileSha256Hex (Join-Path $fx.Programs 'Zola.lnk')) -eq $beforeProg) `
            -and $stagingOk
        if ($ok) { Ok 'putback-after-inject' } else { Bad 'putback-after-inject' 'state' }
    }
} catch { Bad 'putback-after-inject' $_ }

try {
    $fx = New-Fixture 'putback-incomplete'
    New-ShortcutZola -LinkPath (Join-Path $fx.Desktop 'Zola.lnk') -TargetPath 'C:\old2\Zola.Client.exe' -WorkDir 'C:\old2'
    New-ShortcutZola -LinkPath (Join-Path $fx.Programs 'Zola.lnk') -TargetPath 'C:\old2\Zola.Client.exe' -WorkDir 'C:\old2'
    $beforeDesk = Get-FileSha256Hex (Join-Path $fx.Desktop 'Zola.lnk')
    $beforeProg = Get-FileSha256Hex (Join-Path $fx.Programs 'Zola.lnk')
    Invoke-SynPrepare -fx $fx
    $promo = Join-Path $fx.Stable '_promotions\fix-s51f'
    Set-Content -LiteralPath (Join-Path $promo 'plugins\zola_tools\calculator.py') -Value 'X' -NoNewline
    Update-PromoRecord $promo $fx.Profile
    $log = New-TrackedTempFile 'putback-inc-'
    try {
        Invoke-SynSwitch -fx $fx -ForcePluginPutBackFail -Inject { throw 'injected after copy' } *> $log
        Bad 'putback-incomplete-continues' 'expected failure'
    } catch {
        $out = ''
        if (Test-Path $log) { $out = Get-Content $log -Raw }
        $msg = "$($_.Exception.Message)|||$out"
        $curAbsent = -not (Test-Path (Join-Path $fx.Stable 'current.txt'))
        $deskOk = (Test-Path (Join-Path $fx.Desktop 'Zola.lnk')) -and ((Get-FileSha256Hex (Join-Path $fx.Desktop 'Zola.lnk')) -eq $beforeDesk)
        $progOk = (Test-Path (Join-Path $fx.Programs 'Zola.lnk')) -and ((Get-FileSha256Hex (Join-Path $fx.Programs 'Zola.lnk')) -eq $beforeProg)
        $stagingOk = (Test-Path (Join-Path $fx.Stable '_staging\fix-s51f\Zola.Client.exe')) -and (-not (Test-Path (Join-Path $fx.Stable 'fix-s51f')))
        $othersOk = $curAbsent -and $deskOk -and $progOk -and $stagingOk
        if ($msg -match 'PUT-BACK INCOMPLETE' -and $othersOk) {
            Ok 'putback-incomplete-continues'
        } else {
            Bad 'putback-incomplete-continues' "incomplete=$($msg -match 'PUT-BACK INCOMPLETE') cur=$curAbsent desk=$deskOk prog=$progOk staging=$stagingOk msg=$($_.Exception.Message)"
        }
    }
} catch { Bad 'putback-incomplete-continues' $_ }

try {
    $fx = New-Fixture 'approve-stale'
    Invoke-SynPrepare -fx $fx
    $promo = Join-Path $fx.Stable '_promotions\fix-s51f'
    Set-Content -LiteralPath (Join-Path $promo 'plugins\zola_tools\calculator.py') -Value 'A' -NoNewline
    Update-PromoRecord $promo $fx.Profile
    # Live set changes after Prepare so the path lists no longer match the recorded diff
    Set-Content -LiteralPath (Join-Path $fx.Profile 'plugins\zola_tools\__init__.py') -Value 'LIVE-EXTRA-CHANGE' -NoNewline
    try {
        Invoke-SynSwitch -fx $fx
        Bad 'approved-diff-must-match-prepare' 'expected refuse'
    } catch {
        if ("$($_.Exception.Message)" -match 'plugin differences changed since Prepare') {
            Ok 'approved-diff-must-match-prepare'
        } else { Bad 'approved-diff-must-match-prepare' $_.Exception.Message }
    }
} catch { Bad 'approved-diff-must-match-prepare' $_ }

try {
    $bak = Get-ChildItem (Join-Path $script:Shared.Stable 'backups') -Directory | Select-Object -First 1
    try {
        & $Restore -Backup $bak.FullName -StableRoot $script:Shared.Stable -ProfileRoot (New-ScratchRoot 'r') `
            -HermesRoot $HermesRoot -TestMode -ConfirmName '' `
            -DesktopDir $script:Shared.Desktop -ProgramsDir $script:Shared.Programs `
            -RunningZolaProbe { [pscustomobject]@{ Running = $false; Reasons = @() } }
        Bad 'restore-needs-confirm' 'expected throw'
    } catch {
        if ("$($_.Exception.Message)" -match 'confirmation|ConfirmName|mismatch') { Ok 'restore-needs-confirm' } else { Bad 'restore-needs-confirm' $_.Exception.Message }
    }
} catch { Bad 'restore-needs-confirm' $_ }

try {
    $bak = Get-ChildItem (Join-Path $script:Shared.Stable 'backups') -Directory | Select-Object -First 1
    $tgt = New-ScratchRoot 'drill-ok'
    & $Restore -Backup $bak.FullName -Target $tgt -Drill -ConfirmName $bak.Name -StableRoot $script:Shared.Stable `
        -ProfileRoot $tgt -HermesRoot $HermesRoot -TestMode `
        -DesktopDir $script:Shared.Desktop -ProgramsDir $script:Shared.Programs `
        -RunningZolaProbe (Get-IdleRunningProbe)
    if (-not (Test-Path $tgt)) { Ok 'drill-pass-cleans-scratch' } else { Bad 'drill-pass-cleans-scratch' 'exists' }

    $tgt2 = New-ScratchRoot 'drill-fail'
    $bakCopy = New-ScratchRoot 'bak-corrupt'
    Copy-Item -Path (Join-Path $bak.FullName '*') -Destination $bakCopy -Recurse -Force
    $dbFile = Get-ChildItem $bakCopy -Recurse -Filter 'state.db' | Select-Object -First 1
    Set-Content -LiteralPath $dbFile.FullName -Value 'CORRUPT' -NoNewline
    try {
        & $Restore -Backup $bakCopy -Target $tgt2 -Drill -ConfirmName (Split-Path $bakCopy -Leaf) `
            -StableRoot $script:Shared.Stable -ProfileRoot $tgt2 -HermesRoot $HermesRoot -TestMode `
            -DesktopDir $script:Shared.Desktop -ProgramsDir $script:Shared.Programs `
            -RunningZolaProbe (Get-IdleRunningProbe)
        Bad 'drill-fail-cleans-scratch' 'expected fail'
    } catch {
        if (-not (Test-Path $tgt2)) { Ok 'drill-fail-cleans-scratch' } else { Bad 'drill-fail-cleans-scratch' 'remains' }
    }

    # F1: user_version mismatch fails drill and deletes scratch
    $tgt3 = New-ScratchRoot 'drill-uver'
    $bakU = New-ScratchRoot 'bak-uver'
    Copy-Item -Path (Join-Path $bak.FullName '*') -Destination $bakU -Recurse -Force
    $idxPath = Join-Path $bakU 'backup-index.json'
    $idx = Get-Content $idxPath -Raw | ConvertFrom-Json
    foreach ($d in $idx.databases) {
        if ($d.path -eq 'state.db') { $d.schema_version = 99999 }
    }
    Write-JsonFile -Object $idx -Path $idxPath
    try {
        & $Restore -Backup $bakU -Target $tgt3 -Drill -ConfirmName (Split-Path $bakU -Leaf) `
            -StableRoot $script:Shared.Stable -ProfileRoot $tgt3 -HermesRoot $HermesRoot -TestMode `
            -DesktopDir $script:Shared.Desktop -ProgramsDir $script:Shared.Programs `
            -RunningZolaProbe (Get-IdleRunningProbe)
        Bad 'drill-fail-user-version' 'expected fail'
    } catch {
        if (-not (Test-Path $tgt3) -and ("$($_.Exception.Message)" -match 'user_version')) {
            Ok 'drill-fail-user-version'
        } else { Bad 'drill-fail-user-version' $_.Exception.Message }
    }

    # F1: non-db file hash mismatch
    $tgt4 = New-ScratchRoot 'drill-hash'
    $bakH = New-ScratchRoot 'bak-hash'
    Copy-Item -Path (Join-Path $bak.FullName '*') -Destination $bakH -Recurse -Force
    $idxPath = Join-Path $bakH 'backup-index.json'
    $idx = Get-Content $idxPath -Raw | ConvertFrom-Json
    foreach ($f in $idx.files) {
        if ($f.path -eq 'SOUL.md') { $f.sha256 = 'deadbeef' }
    }
    Write-JsonFile -Object $idx -Path $idxPath
    try {
        & $Restore -Backup $bakH -Target $tgt4 -Drill -ConfirmName (Split-Path $bakH -Leaf) `
            -StableRoot $script:Shared.Stable -ProfileRoot $tgt4 -HermesRoot $HermesRoot -TestMode `
            -DesktopDir $script:Shared.Desktop -ProgramsDir $script:Shared.Programs `
            -RunningZolaProbe (Get-IdleRunningProbe)
        Bad 'drill-fail-file-hash' 'expected fail'
    } catch {
        if (-not (Test-Path $tgt4) -and ("$($_.Exception.Message)" -match 'hash mismatch')) {
            Ok 'drill-fail-file-hash'
        } else { Bad 'drill-fail-file-hash' $_.Exception.Message }
    }

    $profR = New-ScratchRoot 'rest-prof'
    New-Item -ItemType Directory -Force -Path $profR | Out-Null
    & $Restore -Backup $bak.FullName -ConfirmName $bak.Name -StableRoot $script:Shared.Stable -ProfileRoot $profR `
        -HermesRoot $HermesRoot -TestMode -ForceSecondConfirm `
        -DesktopDir $script:Shared.Desktop -ProgramsDir $script:Shared.Programs `
        -RunningZolaProbe { [pscustomobject]@{ Running = $false; Reasons = @() } }
    if ((-not (Test-Path (Join-Path $profR 'auth.json'))) -and (Test-Path (Join-Path $profR 'SOUL.md'))) {
        Ok 'credentials-skipped-by-default'
    } else { Bad 'credentials-skipped-by-default' 'cred' }
} catch { Bad 'drill-pass-cleans-scratch' $_ }

try {
    $bak = Get-ChildItem (Join-Path $script:Shared.Stable 'backups') -Directory | Select-Object -First 1
    $idxPath = Join-Path $bak.FullName 'backup-index.json'
    $idx = Get-Content $idxPath -Raw | ConvertFrom-Json
    $idx.hermes.head = 'deadbeef'
    Write-JsonFile -Object $idx -Path $idxPath
    try {
        & $Restore -Backup $bak.FullName -ConfirmName $bak.Name -StableRoot $script:Shared.Stable `
            -ProfileRoot (New-ScratchRoot 'hm') -HermesRoot $HermesRoot -TestMode `
            -DesktopDir $script:Shared.Desktop -ProgramsDir $script:Shared.Programs `
            -RunningZolaProbe { [pscustomobject]@{ Running = $false; Reasons = @() } }
        Bad 'hermes-mismatch-warning' 'expected throw'
    } catch {
        if ("$($_.Exception.Message)" -match 'Hermes-mismatch') { Ok 'hermes-mismatch-warning' } else { Bad 'hermes-mismatch-warning' $_.Exception.Message }
    }
} catch { Bad 'hermes-mismatch-warning' $_ }

try {
    $fx = New-Fixture 'exists'
    Invoke-SynPrepare -fx $fx
    Invoke-SynSwitch -fx $fx
    Invoke-SynPrepare -fx $fx
    try {
        Invoke-SynSwitch -fx $fx
        Bad 'refuse-existing-tag' 'expected throw'
    } catch {
        if ("$($_.Exception.Message)" -match 'already exists') { Ok 'refuse-existing-tag' } else { Bad 'refuse-existing-tag' $_.Exception.Message }
    }
} catch { Bad 'refuse-existing-tag' $_ }

try {
    $fx = New-Fixture 'head'
    Invoke-SynPrepare -fx $fx
    Invoke-SynSwitch -fx $fx
    $bak = Get-ChildItem (Join-Path $fx.Stable 'backups') -Directory | Select-Object -First 1
    $stableHashBefore = Get-ClientBuildHash -PublishDir (Join-Path $fx.Stable 'fix-s51f')
    $currentBefore = Get-Content (Join-Path $fx.Stable 'current.txt') -Raw
    $tgt = New-ScratchRoot 'head-drill'
    & $Restore -Backup $bak.FullName -Target $tgt -Drill -ConfirmName $bak.Name -StableRoot $fx.Stable `
        -ProfileRoot $tgt -HermesRoot $HermesRoot -TestMode `
        -DesktopDir $fx.Desktop -ProgramsDir $fx.Programs `
        -RunningZolaProbe (Get-IdleRunningProbe) | Out-Null
    $stableHashAfter = Get-ClientBuildHash -PublishDir (Join-Path $fx.Stable 'fix-s51f')
    $currentAfter = Get-Content (Join-Path $fx.Stable 'current.txt') -Raw
    if ($stableHashBefore -eq $stableHashAfter -and $currentBefore -eq $currentAfter -and -not (Test-Path $tgt)) {
        Ok 'drill-leaves-stable-untouched'
    } else { Bad 'drill-leaves-stable-untouched' 'modified' }

    $prof = New-ScratchRoot 'head-rest'
    $log = New-TrackedTempFile 'restore-head-'
    & $Restore -Backup $bak.FullName -ConfirmName $bak.Name -StableRoot $fx.Stable -ProfileRoot $prof `
        -HermesRoot $HermesRoot -TestMode -ForceSecondConfirm -LiveCheckout $RepoRoot `
        -DesktopDir $fx.Desktop -ProgramsDir $fx.Programs `
        -RunningZolaProbe { [pscustomobject]@{ Running = $false; Reasons = @() } } *> $log
    $out2 = Get-Content $log -Raw
    if ($out2 -match 'HEAD now differs' -and $out2 -match 'Fallback launch command') {
        Ok 'prestable-head-differs-warning'
    } else { Bad 'prestable-head-differs-warning' 'text' }
    if ((Get-Content (Join-Path $fx.Stable 'current.txt') -Raw) -eq 'none') { Ok 'restore-prestable-current-none' } else { Bad 'restore-prestable-current-none' 'cur' }
} catch { Bad 'drill-leaves-stable-untouched' $_ }

try {
    $fx = New-Fixture 'second'
    Invoke-SynPrepare -fx $fx -Tag 'tag-a' -Commit 'aaa'
    Invoke-SynSwitch -fx $fx -Tag 'tag-a' -Commit 'aaa'
    Invoke-SynPrepare -fx $fx -Tag 'tag-b' -Commit 'bbb'
    Invoke-SynSwitch -fx $fx -Tag 'tag-b' -Commit 'bbb'
    $bak = Get-ChildItem (Join-Path $fx.Stable 'backups') -Directory | Sort-Object Name -Descending | Select-Object -First 1
    $idx = Get-Content (Join-Path $bak.FullName 'backup-index.json') -Raw | ConvertFrom-Json
    if ($idx.outgoing.kind -eq 'stable-tag' -and $idx.outgoing.tag -eq 'tag-a' -and $idx.incoming.tag -eq 'tag-b') {
        Ok 'backup-outgoing-incoming-later'
    } else { Bad 'backup-outgoing-incoming-later' "$($idx.outgoing.kind)/$($idx.outgoing.tag)" }
} catch { Bad 'backup-outgoing-incoming-later' $_ }

try {
    $fx = New-Fixture 'excl'
    Invoke-SynPrepare -fx $fx
    $hasHold = Test-Path (Join-Path $fx.Stable '_promotions\fix-s51f\plugins\zola_memory\l6_hold_guard.py')
    $hasOut = Test-Path (Join-Path $fx.Stable '_promotions\fix-s51f\plugins\zola_phone\outage.py')
    $hasTests = Test-Path (Join-Path $fx.Stable '_promotions\fix-s51f\plugins\zola_workspace\tests')
    if (-not $hasHold -and -not $hasOut -and -not $hasTests) { Ok 'named-excludes-not-promoted' } else { Bad 'named-excludes-not-promoted' 'present' }
} catch { Bad 'named-excludes-not-promoted' $_ }

try {
    $src = Get-Content (Join-Path $here 'StableCommon.psm1') -Raw
    if ($src -match 'Zola\.Client\.csproj') { Ok 'detect-dotnet-csproj' } else { Bad 'detect-dotnet-csproj' 'missing' }
} catch { Bad 'detect-dotnet-csproj' $_ }

# F2: stale WAL beside restore target is removed
try {
    $py = Join-Path $HermesRoot '.venv\Scripts\python.exe'
    $tool = Join-Path $here 'sqlite_tool.py'
    $dir = New-ScratchRoot 'wal'
    $src = Join-Path $dir 'good.db'
    $dst = Join-Path $dir 'target.db'
    $other = Join-Path $dir 'other.db'
    & $py -c @"
import sqlite3, os, shutil
src=r'$($src.Replace('\','\\'))'
dst=r'$($dst.Replace('\','\\'))'
other=r'$($other.Replace('\','\\'))'
c=sqlite3.connect(src); c.execute('CREATE TABLE t(x)'); c.execute('INSERT INTO t VALUES (1)'); c.execute('PRAGMA user_version=42'); c.commit(); c.close()
c=sqlite3.connect(other)
c.execute('CREATE TABLE t(x)')
c.execute('PRAGMA journal_mode=WAL')
c.execute('INSERT INTO t VALUES (9)')
c.commit()
# Force WAL file onto disk before close
c.execute('PRAGMA wal_checkpoint(TRUNCATE)')
c.close()
wal=other+'-wal'
if not os.path.exists(wal):
    # Some builds omit -wal after checkpoint; write a non-empty stale sidecar explicitly
    open(wal,'wb').write(b'stale-wal-from-other-db')
shutil.copy2(other, dst)
shutil.copy2(wal, dst + '-wal')
"@
    if ($LASTEXITCODE -ne 0) { throw 'wal fixture setup failed' }
    & $py $tool backup $src $dst | Out-Null
    $ir = & $py $tool integrity $dst
    $vr = & $py $tool user_version $dst
    $walGone = -not (Test-Path ($dst + '-wal'))
    if (($ir -join '') -match 'status=OK' -and ($vr -join '') -match 'user_version=42' -and $walGone) {
        Ok 'sqlite-backup-removes-stale-wal'
    } else { Bad 'sqlite-backup-removes-stale-wal' "$ir|$vr|walGone=$walGone" }
} catch { Bad 'sqlite-backup-removes-stale-wal' $_ }

# F3: live restore displaces extras; missing outgoing refuses
try {
    $fx = New-Fixture 'live-rest'
    Invoke-SynPrepare -fx $fx -Tag 'tag-out' -Commit 'out1'
    Invoke-SynSwitch -fx $fx -Tag 'tag-out' -Commit 'out1'
    # second promotion so outgoing is stable-tag
    Invoke-SynPrepare -fx $fx -Tag 'tag-in' -Commit 'in1'
    $promo = Join-Path $fx.Stable '_promotions\tag-in'
    Set-Content -LiteralPath (Join-Path $promo 'plugins\zola_tools\incoming_added.py') -Value 'INCOMING' -NoNewline
    Update-PromoRecord $promo $fx.Profile
    Invoke-SynSwitch -fx $fx -Tag 'tag-in' -Commit 'in1'
    # Now live has incoming_added.py; create an extra non-plugin file too
    Set-Content -LiteralPath (Join-Path $fx.Profile 'extra_after.txt') -Value 'extra' -NoNewline
    $bak = Get-ChildItem (Join-Path $fx.Stable 'backups') -Directory | Where-Object { $_.Name -like 'tag-in-*' } | Select-Object -First 1
    $hashesBefore = Get-DirectoryFileHashMap -Root $fx.Profile
    & $Restore -Backup $bak.FullName -ConfirmName $bak.Name -StableRoot $fx.Stable -ProfileRoot $fx.Profile `
        -HermesRoot $HermesRoot -TestMode -ForceSecondConfirm `
        -DesktopDir $fx.Desktop -ProgramsDir $fx.Programs `
        -RunningZolaProbe { [pscustomobject]@{ Running = $false; Reasons = @() } }
    $pre = Get-ChildItem (Join-Path $fx.Stable 'backups') -Directory | Where-Object { $_.Name -like 'pre-restore-*' } | Select-Object -First 1
    $dispExtra = Join-Path $pre.FullName '_displaced\extra_after.txt'
    $dispPlugin = Join-Path $pre.FullName '_displaced\plugins\zola_tools\incoming_added.py'
    $ok = (Test-Path $pre.FullName) `
        -and (Test-Path (Join-Path $pre.FullName 'backup-index.json')) `
        -and (Test-Path $dispExtra) `
        -and (Test-Path $dispPlugin) `
        -and (-not (Test-Path (Join-Path $fx.Profile 'extra_after.txt'))) `
        -and (-not (Test-Path (Join-Path $fx.Profile 'plugins\zola_tools\incoming_added.py')))
    if ($ok) { Ok 'live-restore-displaces-extras' } else { Bad 'live-restore-displaces-extras' 'state' }

    # Missing outgoing folder refuses before change
    $fx2 = New-Fixture 'miss-out'
    Invoke-SynPrepare -fx $fx2 -Tag 'tag-a' -Commit 'a1'
    Invoke-SynSwitch -fx $fx2 -Tag 'tag-a' -Commit 'a1'
    Invoke-SynPrepare -fx $fx2 -Tag 'tag-b' -Commit 'b1'
    Invoke-SynSwitch -fx $fx2 -Tag 'tag-b' -Commit 'b1'
    $bak2 = Get-ChildItem (Join-Path $fx2.Stable 'backups') -Directory | Where-Object { $_.Name -like 'tag-b-*' } | Select-Object -First 1
    # Point outgoing at missing tag by editing index
    $idxPath = Join-Path $bak2.FullName 'backup-index.json'
    $idx = Get-Content $idxPath -Raw | ConvertFrom-Json
    $idx.outgoing.tag = 'missing-tag-xyz'
    Write-JsonFile -Object $idx -Path $idxPath
    Remove-Item -LiteralPath (Join-Path $fx2.Stable 'tag-a') -Recurse -Force -ErrorAction SilentlyContinue
    $mapBefore = Get-DirectoryFileHashMap -Root $fx2.Profile
    try {
        & $Restore -Backup $bak2.FullName -ConfirmName $bak2.Name -StableRoot $fx2.Stable -ProfileRoot $fx2.Profile `
            -HermesRoot $HermesRoot -TestMode -ForceSecondConfirm `
            -DesktopDir $fx2.Desktop -ProgramsDir $fx2.Programs `
            -RunningZolaProbe { [pscustomobject]@{ Running = $false; Reasons = @() } }
        Bad 'refuse-missing-outgoing-stable' 'expected throw'
    } catch {
        $mapAfter = Get-DirectoryFileHashMap -Root $fx2.Profile
        $unchanged = $true
        foreach ($k in $mapBefore.Keys) {
            if (-not $mapAfter.Contains($k) -or $mapAfter[$k] -ne $mapBefore[$k]) { $unchanged = $false }
        }
        foreach ($k in $mapAfter.Keys) {
            if (-not $mapBefore.Contains($k)) { $unchanged = $false }
        }
        if (("$($_.Exception.Message)" -match 'outgoing stable folder missing') -and $unchanged) {
            Ok 'refuse-missing-outgoing-stable'
        } else { Bad 'refuse-missing-outgoing-stable' $_.Exception.Message }
    }
} catch { Bad 'live-restore-displaces-extras' $_ }

# F8: integrity FAIL stops switch at backup
try {
    $fx = New-Fixture 'integ'
    Invoke-SynPrepare -fx $fx
    $py = Join-Path $HermesRoot '.venv\Scripts\python.exe'
    $db = Join-Path $fx.Profile 'state.db'
    # Create a well-formed DB then corrupt interior bytes so backup() can copy but integrity_check fails
    & $py -c @"
import sqlite3
p=r'$($db.Replace('\','\\'))'
c=sqlite3.connect(p)
c.execute('CREATE TABLE IF NOT EXISTS t(x)')
c.execute('INSERT INTO t VALUES (1)')
c.execute('PRAGMA user_version=1')
c.commit(); c.close()
with open(p,'r+b') as f:
    f.seek(80)
    f.write(b'\xff'*64)
"@
    try {
        Invoke-SynSwitch -fx $fx
        Bad 'backup-stops-on-integrity-fail' 'expected throw'
    } catch {
        $msg = "$($_.Exception.Message)"
        if (($msg -match 'integrity FAIL' -or $msg -match 'sqlite backup failed') -and (-not (Test-Path (Join-Path $fx.Stable 'fix-s51f'))) -and (-not (Test-Path (Join-Path $fx.Stable 'current.txt')))) {
            Ok 'backup-stops-on-integrity-fail'
        } else { Bad 'backup-stops-on-integrity-fail' $msg }
    }
} catch { Bad 'backup-stops-on-integrity-fail' $_ }

# G1: undo via pre-restore-snapshot; unknown kind refuses
try {
    $fx = New-Fixture 'undo-pr'
    New-ShortcutZola -LinkPath (Join-Path $fx.Desktop 'Zola.lnk') -TargetPath 'C:\before\Zola.Client.exe' -WorkDir 'C:\before'
    New-ShortcutZola -LinkPath (Join-Path $fx.Programs 'Zola.lnk') -TargetPath 'C:\before\Zola.Client.exe' -WorkDir 'C:\before'
    Invoke-SynPrepare -fx $fx
    Invoke-SynSwitch -fx $fx
    # Mutate live profile after promotion so first restore changes something
    Set-Content -LiteralPath (Join-Path $fx.Profile 'extra_for_undo.txt') -Value 'will-displace' -NoNewline
    $beforeProfile = Get-ProfileHashMapExclLogsCache $fx.Profile
    $beforePlugins = Get-LivePluginHashMap -ProfileRoot $fx.Profile
    $beforeCurrent = (Get-Content (Join-Path $fx.Stable 'current.txt') -Raw).Trim()
    $beforeDesk = Get-FileSha256Hex (Join-Path $fx.Desktop 'Zola.lnk')
    $beforeProg = Get-FileSha256Hex (Join-Path $fx.Programs 'Zola.lnk')

    $bakA = Get-ChildItem (Join-Path $fx.Stable 'backups') -Directory | Where-Object { $_.Name -like 'fix-s51f-*' } | Select-Object -First 1
    & $Restore -Backup $bakA.FullName -ConfirmName $bakA.Name -StableRoot $fx.Stable -ProfileRoot $fx.Profile `
        -HermesRoot $HermesRoot -TestMode -ForceSecondConfirm `
        -DesktopDir $fx.Desktop -ProgramsDir $fx.Programs `
        -RunningZolaProbe { [pscustomobject]@{ Running = $false; Reasons = @() } }
    $pre = Get-ChildItem (Join-Path $fx.Stable 'backups') -Directory | Where-Object { $_.Name -like 'pre-restore-*' } | Select-Object -First 1
    if (-not $pre) { throw 'pre-restore backup missing after first restore' }

    & $Restore -Backup $pre.FullName -ConfirmName $pre.Name -StableRoot $fx.Stable -ProfileRoot $fx.Profile `
        -HermesRoot $HermesRoot -TestMode -ForceSecondConfirm `
        -DesktopDir $fx.Desktop -ProgramsDir $fx.Programs `
        -RunningZolaProbe { [pscustomobject]@{ Running = $false; Reasons = @() } }

    $afterProfile = Get-ProfileHashMapExclLogsCache $fx.Profile
    $afterPlugins = Get-LivePluginHashMap -ProfileRoot $fx.Profile
    $afterCurrent = (Get-Content (Join-Path $fx.Stable 'current.txt') -Raw).Trim()
    $afterDesk = Get-FileSha256Hex (Join-Path $fx.Desktop 'Zola.lnk')
    $afterProg = Get-FileSha256Hex (Join-Path $fx.Programs 'Zola.lnk')
    # Non-DB files: byte hash must match pre-first-restore. DB files pass through sqlite
    # backup so on-disk hash changes; require same paths + integrity OK + user_version.
    $preIdx = Get-Content (Join-Path $pre.FullName 'backup-index.json') -Raw | ConvertFrom-Json
    $dbPaths = @{}
    foreach ($d in @($preIdx.databases)) { $dbPaths["$($d.path)"] = [int]$d.schema_version }

    $profEq = $true
    foreach ($k in $beforeProfile.Keys) {
        if (-not $afterProfile.Contains($k)) { $profEq = $false; continue }
        if ($dbPaths.ContainsKey($k)) {
            $full = Join-Path $fx.Profile ($k.Replace('/', '\'))
            $ir = Invoke-SqliteTool -HermesRoot $HermesRoot -Args @('integrity', $full)
            $vr = Invoke-SqliteTool -HermesRoot $HermesRoot -Args @('user_version', $full)
            $ver = 0
            if ($vr.Output -match 'user_version=(\d+)') { $ver = [int]$Matches[1] }
            if ($ir.Output -notmatch 'status=OK' -or $ver -ne $dbPaths[$k]) { $profEq = $false }
        } else {
            if ($afterProfile[$k] -ne $beforeProfile[$k]) { $profEq = $false }
        }
    }
    foreach ($k in $afterProfile.Keys) {
        if (-not $beforeProfile.Contains($k)) { $profEq = $false }
    }
    $plugEq = $true
    foreach ($k in $beforePlugins.Keys) {
        if (-not $afterPlugins.Contains($k) -or $afterPlugins[$k] -ne $beforePlugins[$k]) { $plugEq = $false }
    }
    foreach ($k in $afterPlugins.Keys) {
        if (-not $beforePlugins.Contains($k)) { $plugEq = $false }
    }
    $extraBack = Test-Path (Join-Path $fx.Profile 'extra_for_undo.txt')
    if ($profEq -and $plugEq -and $extraBack -and $afterCurrent -eq $beforeCurrent -and $afterDesk -eq $beforeDesk -and $afterProg -eq $beforeProg) {
        Ok 'undo-pre-restore-snapshot'
    } else {
        Bad 'undo-pre-restore-snapshot' "prof=$profEq plug=$plugEq extra=$extraBack cur=$($afterCurrent -eq $beforeCurrent) desk=$($afterDesk -eq $beforeDesk) prog=$($afterProg -eq $beforeProg)"
    }
} catch { Bad 'undo-pre-restore-snapshot' $_ }

try {
    $fx = New-Fixture 'unk-kind'
    Invoke-SynPrepare -fx $fx
    Invoke-SynSwitch -fx $fx
    $bak = Get-ChildItem (Join-Path $fx.Stable 'backups') -Directory | Select-Object -First 1
    $idxPath = Join-Path $bak.FullName 'backup-index.json'
    $idx = Get-Content $idxPath -Raw | ConvertFrom-Json
    $idx.outgoing.kind = 'no-such-kind'
    Write-JsonFile -Object $idx -Path $idxPath
    $mapBefore = Get-ProfileHashMapExclLogsCache $fx.Profile
    try {
        & $Restore -Backup $bak.FullName -ConfirmName $bak.Name -StableRoot $fx.Stable -ProfileRoot $fx.Profile `
            -HermesRoot $HermesRoot -TestMode -ForceSecondConfirm `
            -DesktopDir $fx.Desktop -ProgramsDir $fx.Programs `
            -RunningZolaProbe { [pscustomobject]@{ Running = $false; Reasons = @() } }
        Bad 'refuse-unknown-outgoing-kind' 'expected throw'
    } catch {
        $mapAfter = Get-ProfileHashMapExclLogsCache $fx.Profile
        $unchanged = $true
        foreach ($k in $mapBefore.Keys) {
            if (-not $mapAfter.Contains($k) -or $mapAfter[$k] -ne $mapBefore[$k]) { $unchanged = $false }
        }
        foreach ($k in $mapAfter.Keys) {
            if (-not $mapBefore.Contains($k)) { $unchanged = $false }
        }
        if (("$($_.Exception.Message)" -match 'unknown outgoing\.kind') -and $unchanged) {
            Ok 'refuse-unknown-outgoing-kind'
        } else { Bad 'refuse-unknown-outgoing-kind' $_.Exception.Message }
    }
} catch { Bad 'refuse-unknown-outgoing-kind' $_ }

# Phase 6c: Assert-StagingHasWinUiResources names missing .pri / .xbf
try {
    $dir = New-ScratchRoot 'winui-missing'
    try {
        Assert-StagingHasWinUiResources -StagingDir $dir
        Bad 'refuse-missing-winui-resources' 'expected throw'
    } catch {
        $msg = "$($_.Exception.Message)"
        $ok = ($msg -match 'Zola\.Client\.pri') -and ($msg -match 'App\.xbf') `
            -and ($msg -match 'MainWindow\.xbf') -and ($msg -match 'Themes\\ZolaTokens\.xbf')
        if ($ok) { Ok 'refuse-missing-winui-resources' } else { Bad 'refuse-missing-winui-resources' $msg }
    }
} catch { Bad 'refuse-missing-winui-resources' $_ }

try {
    $dir = New-ScratchRoot 'winui-partial'
    Set-Content -LiteralPath (Join-Path $dir 'Zola.Client.pri') -Value 'pri' -NoNewline
    Set-Content -LiteralPath (Join-Path $dir 'App.xbf') -Value 'x' -NoNewline
    try {
        Assert-StagingHasWinUiResources -StagingDir $dir
        Bad 'refuse-missing-winui-xbf-names' 'expected throw'
    } catch {
        $msg = "$($_.Exception.Message)"
        $ok = ($msg -notmatch 'Zola\.Client\.pri') -and ($msg -notmatch '(^|[, ])App\.xbf') `
            -and ($msg -match 'MainWindow\.xbf') -and ($msg -match 'Themes\\ZolaTokens\.xbf')
        if ($ok) { Ok 'refuse-missing-winui-xbf-names' } else { Bad 'refuse-missing-winui-xbf-names' $msg }
    }
} catch { Bad 'refuse-missing-winui-xbf-names' $_ }

try {
    $dir = New-ScratchRoot 'winui-ok'
    Set-Content -LiteralPath (Join-Path $dir 'Zola.Client.pri') -Value 'pri' -NoNewline
    Set-Content -LiteralPath (Join-Path $dir 'App.xbf') -Value 'x' -NoNewline
    Set-Content -LiteralPath (Join-Path $dir 'MainWindow.xbf') -Value 'x' -NoNewline
    New-Item -ItemType Directory -Force -Path (Join-Path $dir 'Themes') | Out-Null
    Set-Content -LiteralPath (Join-Path $dir 'Themes\ZolaTokens.xbf') -Value 'x' -NoNewline
    Assert-StagingHasWinUiResources -StagingDir $dir
    Ok 'accept-winui-resources-present'
} catch { Bad 'accept-winui-resources-present' $_ }

try {
    $fx = New-Fixture 'syn-winui'
    Invoke-SynPrepare -fx $fx
    $st = Join-Path $fx.Stable '_staging\fix-s51f'
    $has = (Test-Path (Join-Path $st 'Zola.Client.pri')) -and (Test-Path (Join-Path $st 'App.xbf')) `
        -and (Test-Path (Join-Path $st 'MainWindow.xbf')) -and (Test-Path (Join-Path $st 'Themes\ZolaTokens.xbf'))
    if ($has) { Ok 'synthetic-prepare-includes-winui-resources' } else { Bad 'synthetic-prepare-includes-winui-resources' 'missing files' }
} catch { Bad 'synthetic-prepare-includes-winui-resources' $_ }

# Phase 6d: synthetic client with an extra .xaml and no matching .xbf → Prepare refuses, names it
try {
    $fx = New-Fixture 'xaml-extra'
    $client = New-ScratchRoot 'client-xaml'
    Set-Content -LiteralPath (Join-Path $client 'App.xaml') -Value '<Page/>' -NoNewline
    Set-Content -LiteralPath (Join-Path $client 'MainWindow.xaml') -Value '<Window/>' -NoNewline
    New-Item -ItemType Directory -Force -Path (Join-Path $client 'Themes') | Out-Null
    Set-Content -LiteralPath (Join-Path $client 'Themes\ZolaTokens.xaml') -Value '<ResourceDictionary/>' -NoNewline
    Set-Content -LiteralPath (Join-Path $client 'ExtraPage.xaml') -Value '<Page/>' -NoNewline
    $c = Get-CommonPromoteArgs $fx
    try {
        & $Promote -Prepare -Tag 'fix-s51f' @c -Synthetic `
            -SyntheticPluginsRoot $fx.Plugins -SyntheticCommit 'abc111' `
            -SyntheticClientRoot $client
        Bad 'refuse-extra-xaml-missing-xbf' 'expected throw'
    } catch {
        $msg = "$($_.Exception.Message)"
        if ($msg -match 'ExtraPage\.xbf') { Ok 'refuse-extra-xaml-missing-xbf' } else { Bad 'refuse-extra-xaml-missing-xbf' $msg }
    }
} catch { Bad 'refuse-extra-xaml-missing-xbf' $_ }

# G2: FAIL after pre-restore names the undo backup
try {
    $fx = New-Fixture 'fail-pr'
    Invoke-SynPrepare -fx $fx
    Invoke-SynSwitch -fx $fx
    $bak = Get-ChildItem (Join-Path $fx.Stable 'backups') -Directory | Select-Object -First 1
    # Remove a required non-credential file so restore fails after pre-restore backup
    $soul = Join-Path $bak.FullName 'SOUL.md'
    if (Test-Path $soul) { Remove-Item -LiteralPath $soul -Force }
    $log = New-TrackedTempFile 'restore-fail-'
    try {
        & $Restore -Backup $bak.FullName -ConfirmName $bak.Name -StableRoot $fx.Stable -ProfileRoot $fx.Profile `
            -HermesRoot $HermesRoot -TestMode -ForceSecondConfirm `
            -DesktopDir $fx.Desktop -ProgramsDir $fx.Programs `
            -RunningZolaProbe { [pscustomobject]@{ Running = $false; Reasons = @() } } *> $log
        Bad 'fail-names-pre-restore-backup' 'expected throw'
    } catch {
        $out = if (Test-Path $log) { Get-Content $log -Raw } else { '' }
        if ($out -match '"pre_restore_backup"\s*:\s*"pre-restore-') {
            Ok 'fail-names-pre-restore-backup'
        } else { Bad 'fail-names-pre-restore-backup' 'field missing' }
    }
} catch { Bad 'fail-names-pre-restore-backup' $_ }

try {
    # PROC1-ID: injected prestable wins while a real Zola.Client.exe may be running — PROC1-D13
    $fx = New-Fixture 'inj'
    $inj = Get-TestPreStableLaunch
    $inj['head'] = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    $inj['launch_command'] = 'injected-launch-command-for-test'
    $c = Get-CommonPromoteArgs $fx
    $c['TestPreStableLaunch'] = $inj
    & $Promote -Prepare -Tag 'fix-s51f' @c -Synthetic -SyntheticPluginsRoot $fx.Plugins -SyntheticCommit 'abc111'
    $rec = Get-Content (Join-Path $fx.Stable '_promotions\fix-s51f\.prepare-record.json') -Raw | ConvertFrom-Json
    if ($rec.outgoing.head -eq 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' -and $rec.outgoing.launch_command -eq 'injected-launch-command-for-test') {
        Ok 'testmode-prepare-ignores-real-zola'
    } else {
        Bad 'testmode-prepare-ignores-real-zola' "$($rec.outgoing.head)/$($rec.outgoing.launch_command)"
    }
} catch { Bad 'testmode-prepare-ignores-real-zola' $_ }

try {
    # PROC1-ID: TestMode without probe refuses before touching live processes — PROC1-D13
    $fx = New-Fixture 'noprobe'
    try {
        & $Promote -Prepare -Tag 'fix-s51f' -StableRoot $fx.Stable -ProfileRoot $fx.Profile `
            -HermesRoot $HermesRoot -RepoRoot $RepoRoot -TestMode -Synthetic `
            -SyntheticPluginsRoot $fx.Plugins -SyntheticCommit 'abc111' `
            -DesktopDir $fx.Desktop -ProgramsDir $fx.Programs `
            -TestPreStableLaunch (Get-TestPreStableLaunch)
        Bad 'testmode-requires-running-probe' 'expected throw'
    } catch {
        if ("$($_.Exception.Message)" -match 'TestMode requires -RunningZolaProbe') {
            Ok 'testmode-requires-running-probe'
        } else { Bad 'testmode-requires-running-probe' $_.Exception.Message }
    }
} catch { Bad 'testmode-requires-running-probe' $_ }

try {
    # PROC1-ID: TestMode without TestPreStableLaunch refuses — PROC1-D13
    $fx = New-Fixture 'nolaunch'
    try {
        & $Promote -Prepare -Tag 'fix-s51f' -StableRoot $fx.Stable -ProfileRoot $fx.Profile `
            -HermesRoot $HermesRoot -RepoRoot $RepoRoot -TestMode -Synthetic `
            -SyntheticPluginsRoot $fx.Plugins -SyntheticCommit 'abc111' `
            -DesktopDir $fx.Desktop -ProgramsDir $fx.Programs `
            -RunningZolaProbe (Get-IdleRunningProbe)
        Bad 'testmode-requires-prestable-launch' 'expected throw'
    } catch {
        if ("$($_.Exception.Message)" -match 'TestMode requires -TestPreStableLaunch') {
            Ok 'testmode-requires-prestable-launch'
        } else { Bad 'testmode-requires-prestable-launch' $_.Exception.Message }
    }
} catch { Bad 'testmode-requires-prestable-launch' $_ }

try {
    # PROC1-ID: Switch writes build-role.json + digest rules — PROC1-D7/D13
    $fx = New-Fixture 'role'
    Invoke-SynPrepare -fx $fx
    Invoke-SynSwitch -fx $fx
    $rolePath = Join-Path $fx.Stable 'fix-s51f\build-role.json'
    $mfPath = Join-Path $fx.Stable 'fix-s51f\stable-manifest.json'
    if (-not (Test-Path $rolePath)) { Bad 'switch-writes-build-role' 'missing role'; throw 'x' }
    $role = Get-Content $rolePath -Raw | ConvertFrom-Json
    $mf = Get-Content $mfPath -Raw | ConvertFrom-Json
    $hasRules = $null -ne $mf.plugin_compare_rules
    $hasAlgo = $null -ne $mf.digest_algorithms `
        -and $mf.digest_algorithms.hermes_local_edit -eq 'v2-content' `
        -and $mf.digest_algorithms.pip_freeze -eq 'v2-pip-freeze-clean'
    if ($role.role -eq 'stable' -and $role.tag -eq 'fix-s51f' -and $hasRules -and $hasAlgo) {
        Ok 'switch-writes-build-role'
    } else { Bad 'switch-writes-build-role' 'fields' }
    # PROC1-ID Phase 4c: Switch writes pip-freeze.txt under _promotions\<tag> — PROC1-D13
    $freezePath = Join-Path $fx.Stable '_promotions\fix-s51f\pip-freeze.txt'
    if (-not (Test-Path -LiteralPath $freezePath)) {
        Bad 'switch-writes-pip-freeze' 'missing'
    } else {
        $freezeRaw = [System.IO.File]::ReadAllText($freezePath)
        if ($mf.pip_freeze_digest -eq (Get-DigestOfText $freezeRaw)) {
            Ok 'switch-writes-pip-freeze'
        } else { Bad 'switch-writes-pip-freeze' 'digest mismatch' }
    }
} catch { if ("$_" -ne 'x') { Bad 'switch-writes-build-role' $_ } }

try {
    # PROC1-ID Phase 4c: v1 digests match proc1-stable Get-DigestOfText on fixtures — PROC1-D13
    $tmpModDir = Join-Path $env:TEMP ('proc1-id-golden-' + [guid]::NewGuid().ToString('N'))
    Register-ScratchItem $tmpModDir
    New-Item -ItemType Directory -Force -Path $tmpModDir | Out-Null
    $tmpMod = Join-Path $tmpModDir 'StableCommon.psm1'
    git -C $RepoRoot show 'proc1-stable:tools/stable/StableCommon.psm1' | Set-Content -LiteralPath $tmpMod -Encoding UTF8
    $freezeFixture = "aiohttp==3.14.3`npypdf==6.19.0`nyarl==1.25.1"
    $freezeCaptured = $freezeFixture + "`n"
    $porcelainFixture = " M tracked.py`n?? untracked.txt"
    $porcelainCaptured = $porcelainFixture + "`n"
    # Isolated process so Import-Module does not replace this harness's StableCommon
    $goldenFreeze = & powershell -NoProfile -ExecutionPolicy Bypass -Command {
        param($Mod, $Text)
        Import-Module $Mod -Force
        Get-DigestOfText -Text $Text
    } -args $tmpMod, $freezeFixture
    $goldenPorc = & powershell -NoProfile -ExecutionPolicy Bypass -Command {
        param($Mod, $Text)
        Import-Module $Mod -Force
        Get-DigestOfText -Text $Text
    } -args $tmpMod, $porcelainFixture
    $curFreeze = Get-DigestOfText (ConvertTo-V1JoinedText -Text $freezeCaptured)
    $curPorc = Get-DigestOfText (ConvertTo-V1JoinedText -Text $porcelainCaptured)
    if ($curFreeze -eq $goldenFreeze -and $curPorc -eq $goldenPorc) {
        Ok 'v1-digests-match-proc1-stable-tag'
    } else {
        Bad 'v1-digests-match-proc1-stable-tag' "freeze=$curFreeze/$goldenFreeze porc=$curPorc/$goldenPorc"
    }
} catch { Bad 'v1-digests-match-proc1-stable-tag' $_ }

try {
    # PROC1-ID Phase 4c: v2 local-edit digest stable across two runs on one fixture — PROC1-D13
    $root = Join-Path $env:TEMP ('proc1-id-v2fix-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Force -Path $root | Out-Null
    git -C $root init | Out-Null
    git -C $root config user.email 't@t' | Out-Null
    git -C $root config user.name 't' | Out-Null
    Set-Content -LiteralPath (Join-Path $root 'a.txt') -Value 'one' -NoNewline
    git -C $root add a.txt | Out-Null
    git -C $root commit -m c1 | Out-Null
    Set-Content -LiteralPath (Join-Path $root 'a.txt') -Value 'two' -NoNewline
    Set-Content -LiteralPath (Join-Path $root 'u.txt') -Value 'untracked' -NoNewline
    $d1 = Get-HermesLocalEditDigestV2 -HermesRoot $root
    $d2 = Get-HermesLocalEditDigestV2 -HermesRoot $root
    if ($d1.Ok -and $d2.Ok -and $d1.Digest -eq $d2.Digest -and $d1.Digest -ne (Get-DigestOfText '')) {
        Ok 'v2-local-edit-stable-across-runs'
    } else { Bad 'v2-local-edit-stable-across-runs' "$($d1.Digest)/$($d2.Digest)" }
    Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue
} catch { Bad 'v2-local-edit-stable-across-runs' $_ }

try {
    # PROC1-ID Phase 6b: v2-pip-freeze-clean ignores ambient PYTHONPATH — PROC1-D13
    $savedPp = [Environment]::GetEnvironmentVariable('PYTHONPATH', 'Process')
    try {
        [Environment]::SetEnvironmentVariable('PYTHONPATH', $HermesRoot, 'Process')
        $withPp = Get-PipFreezeDigestV2 -HermesRoot $HermesRoot
        [Environment]::SetEnvironmentVariable('PYTHONPATH', $null, 'Process')
        $withoutPp = Get-PipFreezeDigestV2 -HermesRoot $HermesRoot
        if ($withPp.Ok -and $withoutPp.Ok -and $withPp.Digest -eq $withoutPp.Digest) {
            Ok 'v2-pip-freeze-clean-ignores-pythonpath'
        } else {
            Bad 'v2-pip-freeze-clean-ignores-pythonpath' "$($withPp.Digest)/$($withoutPp.Digest)"
        }
    } finally {
        [Environment]::SetEnvironmentVariable('PYTHONPATH', $savedPp, 'Process')
    }
} catch { Bad 'v2-pip-freeze-clean-ignores-pythonpath' $_ }

try {
    # PROC1-ID Phase 6b: v2-content ignores ambient GIT_DIR — PROC1-D13
    $root = Join-Path $env:TEMP ('proc1-id-v2git-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Force -Path $root | Out-Null
    git -C $root init | Out-Null
    git -C $root config user.email 't@t' | Out-Null
    git -C $root config user.name 't' | Out-Null
    Set-Content -LiteralPath (Join-Path $root 'a.txt') -Value 'one' -NoNewline
    git -C $root add a.txt | Out-Null
    git -C $root commit -m c1 | Out-Null
    Set-Content -LiteralPath (Join-Path $root 'a.txt') -Value 'two' -NoNewline
    $savedGitDir = [Environment]::GetEnvironmentVariable('GIT_DIR', 'Process')
    try {
        $bogus = Join-Path $env:TEMP ('proc1-id-bogus-git-' + [guid]::NewGuid().ToString('N'))
        [Environment]::SetEnvironmentVariable('GIT_DIR', $bogus, 'Process')
        $withGitDir = Get-HermesLocalEditDigestV2 -HermesRoot $root
        [Environment]::SetEnvironmentVariable('GIT_DIR', $null, 'Process')
        $withoutGitDir = Get-HermesLocalEditDigestV2 -HermesRoot $root
        if ($withGitDir.Ok -and $withoutGitDir.Ok -and $withGitDir.Digest -eq $withoutGitDir.Digest) {
            Ok 'v2-local-edit-ignores-git-dir'
        } else {
            Bad 'v2-local-edit-ignores-git-dir' "$($withGitDir.Ok)/$($withoutGitDir.Ok)/$($withGitDir.Digest)/$($withoutGitDir.Digest)"
        }
    } finally {
        [Environment]::SetEnvironmentVariable('GIT_DIR', $savedGitDir, 'Process')
        Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue
    }
} catch { Bad 'v2-local-edit-ignores-git-dir' $_ }

# G3: always clean this track's scratch, pass or fail; then assert none remain
try {
    Remove-TrackedScratch
    Assert-NoTrackTempLeftovers
} catch {
    Bad 'temp-cleanup-no-leftovers' $_
}

Write-Host ''
Write-Host "==== SUMMARY pass=$script:Pass fail=$script:Fail ===="
$script:Results | ForEach-Object { Write-Host $_ }
if ($script:Fail -gt 0) { exit 1 } else { exit 0 }
