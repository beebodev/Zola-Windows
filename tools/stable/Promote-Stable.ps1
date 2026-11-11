# PROC1-STABLE: prepare and switch a stable Release build - PROC1-D1/D2/D12/D13
#Requires -Version 5.1
[CmdletBinding()]
param(
    [switch]$Prepare,
    [switch]$Switch,
    [Parameter(Mandatory)][string]$Tag,
    [string]$StableRoot = 'C:\Users\test\Zola\stable',
    [string]$ProfileRoot = $(Join-Path $env:LOCALAPPDATA 'hermes\profiles\zola'),
    [string]$ClientDataRoot = $(Join-Path $env:LOCALAPPDATA 'ZolaClient'),
    [string]$HermesRoot = 'C:\Users\test\Dev\hermes-agent',
    [string]$RepoRoot,
    [string]$LiveCheckout = 'C:\Users\test\Dev\zola-windows',
    [string]$DesktopDir = $([Environment]::GetFolderPath('Desktop')),
    [string]$ProgramsDir = $([Environment]::GetFolderPath('Programs')),
    [switch]$ApprovedPluginCopy,
    [switch]$TestMode,
    [switch]$Synthetic,                 # TestMode: skip git worktree / dotnet build
    [string]$SyntheticPluginsRoot,      # TestMode: hermes-plugins-like tree for comparison set
    [string]$SyntheticCommit,           # TestMode: pretend tag commit
    [string]$SyntheticClientRoot,       # TestMode: fake windows-client\Zola.Client for .xaml→.xbf check
    [scriptblock]$RunningZolaProbe,
    [string[]]$MutexNames,
    [scriptblock]$InjectAfterPluginCopy,
    [switch]$ForcePluginPutBackFail,
    # PROC1-ID: TestMode prestable outgoing — never observe real processes — PROC1-D13
    [hashtable]$TestPreStableLaunch
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module (Join-Path $here 'StableCommon.psm1') -Force

if (($Prepare -and $Switch) -or (-not $Prepare -and -not $Switch)) {
    throw 'Specify exactly one of -Prepare or -Switch'
}

if (-not $RepoRoot) {
    $RepoRoot = Resolve-FullPath (Join-Path $here '..\..')
}

$StableRoot = Resolve-FullPath $StableRoot
$ProfileRoot = Resolve-FullPath $ProfileRoot
$ClientDataRoot = Resolve-FullPath $ClientDataRoot
$HermesRoot = Resolve-FullPath $HermesRoot
$RepoRoot = Resolve-FullPath $RepoRoot
$LiveCheckout = Resolve-FullPath $LiveCheckout
$DesktopDir = Resolve-FullPath $DesktopDir
$ProgramsDir = Resolve-FullPath $ProgramsDir

$liveRoots = Get-LiveRootSet
if ($TestMode) {
    Assert-TestModeSafeRoot -Path $StableRoot -LiveRoots $liveRoots -Label 'StableRoot'
    Assert-TestModeSafeRoot -Path $ProfileRoot -LiveRoots $liveRoots -Label 'ProfileRoot'
    Assert-TestModeSafeRoot -Path $DesktopDir -LiveRoots $liveRoots -Label 'DesktopDir'
    Assert-TestModeSafeRoot -Path $ProgramsDir -LiveRoots $liveRoots -Label 'ProgramsDir'
    # PROC1-ID: TestMode refuses real process/mutex scans — PROC1-D13
    if (-not $RunningZolaProbe) {
        throw 'TestMode requires -RunningZolaProbe'
    }
}

function Get-TagCommit {
    param([string]$TagName)
    git -C $RepoRoot rev-parse --verify --quiet "refs/tags/$TagName" 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Unknown tag: $TagName" }
    $commit = (git -C $RepoRoot rev-parse ($TagName + '^{commit}') 2>$null)
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($commit)) { throw "Cannot peel tag: $TagName" }
    $commit = $commit.Trim()
    $originHas = git -C $RepoRoot ls-remote --tags origin $TagName 2>$null
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($originHas)) { throw "Tag not on origin: $TagName" }
    git -C $RepoRoot merge-base --is-ancestor $commit origin/main 2>$null
    if ($LASTEXITCODE -ne 0) { throw "Tag $TagName commit $commit is not an ancestor of origin/main" }
    return $commit
}

function Resolve-OutgoingForPrepare {
    $currentTxt = Join-Path $StableRoot 'current.txt'
    $currentVal = $null
    if (Test-Path -LiteralPath $currentTxt) {
        $currentVal = (Get-Content -LiteralPath $currentTxt -Raw).Trim()
    }
    if ($currentVal -and $currentVal -ne 'none') {
        return [ordered]@{
            kind        = 'stable-tag'
            tag         = $currentVal
            folder      = (Join-Path $StableRoot $currentVal)
            current_txt = $currentVal
            shortcuts   = @{
                desktop  = (Get-ShortcutTargetOrNull (Get-DesktopShortcutPath -DesktopDir $DesktopDir))
                programs = (Get-ShortcutTargetOrNull (Get-ProgramsShortcutPath -ProgramsDir $ProgramsDir))
            }
        }
    }
    # PROC1-ID: TestMode never looks at real processes — injected launch only — PROC1-D13
    if ($TestMode) {
        if (-not $TestPreStableLaunch) {
            throw 'TestMode requires -TestPreStableLaunch'
        }
        $obs = [pscustomobject]$TestPreStableLaunch
    } else {
        $obs = Get-ObservedPreStableLaunch -LiveCheckout $LiveCheckout
    }
    if (-not $obs) {
        throw 'Prepare: no running Zola.Client and no stable current.txt - cannot record pre-stable outgoing. Start Zola or set current.txt.'
    }
    return [ordered]@{
        kind           = 'pre-stable'
        launch_command = $obs.launch_command
        checkout       = $obs.checkout
        branch         = $obs.branch
        head           = [string]$obs.head
        client_exe     = [string]$obs.client_exe
        current_txt    = $null
        shortcuts      = @{ desktop = $null; programs = $null }
    }
}

function Write-PrepareRecordAndCompare {
    param(
        [string]$Commit,
        [string]$PromoDir,
        [string]$StagingDir,
        [object]$Outgoing,
        [bool]$WorktreeRemoved
    )
    $clientHash = Get-ClientBuildHash -PublishDir $StagingDir
    $pluginHashes = Get-PromotionsPluginHashMap -PromotionsTagDir $PromoDir
    $stagingHashes = Get-DirectoryFileHashMap -Root $StagingDir
    $diff = Compare-PluginSets -TagMap $pluginHashes -LiveMap (Get-LivePluginHashMap -ProfileRoot $ProfileRoot)
    Write-Host "Prepare: plugin compare equal=$($diff.equal)"
    if (-not $diff.Equal) {
        Write-Host ("  added: " + (($diff.Added) -join ', '))
        Write-Host ("  removed: " + (($diff.Removed) -join ', '))
        Write-Host ("  changed: " + (($diff.Changed) -join ', '))
    }
    $record = [ordered]@{
        tag                 = $Tag
        commit              = $Commit
        client_build_hash   = $clientHash
        staging_file_hashes = $stagingHashes
        plugin_tag_hashes   = $pluginHashes
        plugin_diff         = @{
            added   = [string[]]@(@($diff.Added) | ForEach-Object { "$_" } | Sort-Object)
            removed = [string[]]@(@($diff.Removed) | ForEach-Object { "$_" } | Sort-Object)
            changed = [string[]]@(@($diff.Changed) | ForEach-Object { "$_" } | Sort-Object)
            equal   = [bool]$diff.Equal
        }
        outgoing            = $Outgoing
        prepared_at         = (Get-Date).ToString('o')
        worktree_removed    = $WorktreeRemoved
    }
    Write-JsonFile -Object $record -Path (Join-Path $PromoDir '.prepare-record.json')
    Write-Host "Prepare: done tag=$Tag commit=$Commit client_build_hash=$clientHash"
}

function Invoke-Prepare {
    $promoDir = Join-Path $StableRoot "_promotions\$Tag"
    $stagingDir = Join-Path $StableRoot "_staging\$Tag"
    if (Test-Path -LiteralPath $stagingDir) {
        Remove-Item -LiteralPath $stagingDir -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $promoDir | Out-Null
    New-Item -ItemType Directory -Force -Path $stagingDir | Out-Null

    $outgoing = Resolve-OutgoingForPrepare

    if ($TestMode -and $Synthetic) {
        if (-not $SyntheticPluginsRoot) { throw 'Synthetic Prepare requires -SyntheticPluginsRoot' }
        $commit = if ($SyntheticCommit) { $SyntheticCommit } else { 'synthetic-commit' }
        Set-Content -LiteralPath (Join-Path $stagingDir 'Zola.Client.exe') -Value 'fake-exe' -NoNewline
        Set-Content -LiteralPath (Join-Path $stagingDir 'Zola.Client.dll') -Value 'fake-dll' -NoNewline
        Set-Content -LiteralPath (Join-Path $stagingDir 'Zola.Client.pri') -Value 'fake-pri' -NoNewline
        Set-Content -LiteralPath (Join-Path $stagingDir 'App.xbf') -Value 'fake-app-xbf' -NoNewline
        Set-Content -LiteralPath (Join-Path $stagingDir 'MainWindow.xbf') -Value 'fake-main-xbf' -NoNewline
        New-Item -ItemType Directory -Force -Path (Join-Path $stagingDir 'Themes') | Out-Null
        Set-Content -LiteralPath (Join-Path $stagingDir 'Themes\ZolaTokens.xbf') -Value 'fake-tokens-xbf' -NoNewline
        New-Item -ItemType Directory -Force -Path (Join-Path $stagingDir 'Assets') | Out-Null
        Set-Content -LiteralPath (Join-Path $stagingDir 'Assets\zola.glb') -Value 'glb' -NoNewline
        Assert-StagingHasWinUiResources -StagingDir $stagingDir -ClientSourceDir $SyntheticClientRoot
        foreach ($leaf in @('plugins', 'zola-tts')) {
            $p = Join-Path $promoDir $leaf
            if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p -Recurse -Force }
        }
        $copied = Copy-ComparisonSetToPromotions -HermesPluginsRoot $SyntheticPluginsRoot -PromotionsTagDir $promoDir
        Write-Host "Prepare(Synthetic): copied $copied files; worktree never created (removed=true)"
        Write-PrepareRecordAndCompare -Commit $commit -PromoDir $promoDir -StagingDir $stagingDir -Outgoing $outgoing -WorktreeRemoved $true
        return
    }

    $commit = Get-TagCommit -TagName $Tag
    $stamp = Get-Date -Format 'yyyyMMddHHmmss'
    $wt = Join-Path $env:TEMP "zola-stable-build-$Tag-$stamp"
    if (Test-Path -LiteralPath $wt) { Remove-Item -LiteralPath $wt -Recurse -Force }
    Write-Host "Prepare: worktree $wt @ $commit"
    git -C $RepoRoot worktree add --detach $wt $commit
    if ($LASTEXITCODE -ne 0) { throw 'git worktree add failed' }

    try {
        $csproj = Join-Path $wt 'windows-client\Zola.Client\Zola.Client.csproj'
        Write-Host "Prepare: dotnet build -> $stagingDir"
        & dotnet build $csproj -c Release -r win-x64 -o $stagingDir
        if ($LASTEXITCODE -ne 0) { throw 'dotnet build failed' }
        $clientSrc = Join-Path $wt 'windows-client\Zola.Client'
        Assert-StagingHasWinUiResources -StagingDir $stagingDir -ClientSourceDir $clientSrc

        if (-not $TestMode) {
            $jbr = 'C:\Program Files\Android\Android Studio\jbr'
            $env:JAVA_HOME = $jbr
            $env:ANDROID_HOME = Join-Path $env:LOCALAPPDATA 'Android\Sdk'
            Push-Location (Join-Path $wt 'android-companion')
            try {
                & .\gradlew.bat assembleDebug --offline
                if ($LASTEXITCODE -ne 0) { throw 'assembleDebug failed' }
            } finally {
                Pop-Location
            }
        } else {
            Write-Host 'Prepare: TestMode skips assembleDebug'
        }

        $pluginsSrc = Join-Path $wt 'hermes-plugins'
        foreach ($leaf in @('plugins', 'zola-tts')) {
            $p = Join-Path $promoDir $leaf
            if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p -Recurse -Force }
        }
        $copied = Copy-ComparisonSetToPromotions -HermesPluginsRoot $pluginsSrc -PromotionsTagDir $promoDir
        Write-Host "Prepare: copied $copied comparison-set files to _promotions\$Tag"
        Write-PrepareRecordAndCompare -Commit $commit -PromoDir $promoDir -StagingDir $stagingDir -Outgoing $outgoing -WorktreeRemoved $true
    }
    finally {
        git -C $RepoRoot worktree remove --force $wt 2>$null
        if (Test-Path -LiteralPath $wt) {
            Remove-Item -LiteralPath $wt -Recurse -Force -ErrorAction SilentlyContinue
        }
        Write-Host "Prepare: temp worktree removed exists=$(Test-Path -LiteralPath $wt)"
    }
}

function Invoke-PluginApplyFromPromotions {
    param(
        [object]$Diff,
        [string]$PromoDir
    )
    foreach ($rel in $Diff.Added) {
        $src = Join-Path $PromoDir ($rel.Replace('/', '\'))
        $dst = Join-Path $ProfileRoot ($rel.Replace('/', '\'))
        $d = Split-Path -Parent $dst
        if (-not (Test-Path -LiteralPath $d)) { New-Item -ItemType Directory -Force -Path $d | Out-Null }
        Copy-Item -LiteralPath $src -Destination $dst -Force
    }
    foreach ($rel in $Diff.Changed) {
        $src = Join-Path $PromoDir ($rel.Replace('/', '\'))
        $dst = Join-Path $ProfileRoot ($rel.Replace('/', '\'))
        Copy-Item -LiteralPath $src -Destination $dst -Force
    }
    foreach ($rel in $Diff.Removed) {
        $dst = Join-Path $ProfileRoot ($rel.Replace('/', '\'))
        if (Test-Path -LiteralPath $dst) { Remove-Item -LiteralPath $dst -Force }
    }
}

function Invoke-PluginPutBack {
    param(
        [object]$Diff,
        [string]$SnapshotDir,
        [hashtable]$BeforeHashes
    )
    foreach ($rel in $Diff.Added) {
        $dst = Join-Path $ProfileRoot ($rel.Replace('/', '\'))
        if (Test-Path -LiteralPath $dst) { Remove-Item -LiteralPath $dst -Force }
    }
    foreach ($rel in @(@($Diff.Changed) + @($Diff.Removed))) {
        $src = Join-Path $SnapshotDir ($rel.Replace('/', '\'))
        $dst = Join-Path $ProfileRoot ($rel.Replace('/', '\'))
        if (Test-Path -LiteralPath $src) {
            $d = Split-Path -Parent $dst
            if (-not (Test-Path -LiteralPath $d)) { New-Item -ItemType Directory -Force -Path $d | Out-Null }
            Copy-Item -LiteralPath $src -Destination $dst -Force
        }
    }
    $after = Get-LivePluginHashMap -ProfileRoot $ProfileRoot
    foreach ($k in $BeforeHashes.Keys) {
        if (-not $after.Contains($k)) { throw "Put-back missing file: $k" }
        if ($after[$k] -ne $BeforeHashes[$k]) { throw "Put-back hash mismatch: $k" }
    }
    foreach ($rel in $Diff.Added) {
        if ($after.Contains($rel)) { throw "Put-back left added file: $rel" }
    }
}

function Invoke-PutBackAll {
    param(
        [bool]$PluginsApplied,
        [object]$Diff,
        [string]$PluginSnapDir,
        [hashtable]$BeforePluginHashes,
        $BeforeCurrent,
        $ShortcutMeta,
        [bool]$Moved,
        [string]$StagingDir,
        [string]$FinalDir,
        [object]$PrepareRecord
    )
    $states = [ordered]@{}
    $errors = New-Object System.Collections.Generic.List[string]

    # plugins
    try {
        if ($ForcePluginPutBackFail) { throw 'forced plugin put-back fail' }
        if ($PluginsApplied -and -not $Diff.Equal) {
            Invoke-PluginPutBack -Diff $Diff -SnapshotDir $PluginSnapDir -BeforeHashes $BeforePluginHashes
        }
        $after = Get-LivePluginHashMap -ProfileRoot $ProfileRoot
        foreach ($k in $BeforePluginHashes.Keys) {
            if (-not $after.Contains($k)) { throw "verify missing $k" }
            if ($after[$k] -ne $BeforePluginHashes[$k]) { throw "verify hash $k" }
        }
        foreach ($rel in @($Diff.Added)) {
            if ($after.Contains($rel)) { throw "added left behind $rel" }
        }
        Write-Host 'putback plugins OK'
        $states['plugins'] = 'OK'
    } catch {
        Write-Host 'putback plugins FAIL'
        $states['plugins'] = 'FAIL'
        $errors.Add("plugins: $($_.Exception.Message)") | Out-Null
    }

    # current.txt
    try {
        $ct = Join-Path $StableRoot 'current.txt'
        if ($null -eq $BeforeCurrent) {
            if (Test-Path -LiteralPath $ct) { Remove-Item -LiteralPath $ct -Force }
            if (Test-Path -LiteralPath $ct) { throw 'current.txt still present' }
        } else {
            Set-Content -LiteralPath $ct -Value $BeforeCurrent -NoNewline
            $got = (Get-Content -LiteralPath $ct -Raw).Trim()
            if ($got -ne $BeforeCurrent) { throw 'current.txt content mismatch' }
        }
        Write-Host 'putback current.txt OK'
        $states['current.txt'] = 'OK'
    } catch {
        Write-Host 'putback current.txt FAIL'
        $states['current.txt'] = 'FAIL'
        $errors.Add("current.txt: $($_.Exception.Message)") | Out-Null
    }

    # desktop shortcut
    try {
        $null = Restore-ShortcutBytes -BackupDir (Split-Path -Parent $PluginSnapDir) -ShortcutMeta $ShortcutMeta `
            -DesktopDir $DesktopDir -ProgramsDir $ProgramsDir
        # Restore-ShortcutBytes restores both; verify desktop alone here then programs
        $desk = Get-DesktopShortcutPath -DesktopDir $DesktopDir
        $deskMeta = $ShortcutMeta.desktop
        $deskPresent = [bool]$deskMeta.present
        if ($deskPresent) {
            if (-not (Test-Path -LiteralPath $desk)) { throw 'desktop shortcut missing' }
            if ((Get-FileSha256Hex $desk) -ne $deskMeta.sha256) { throw 'desktop shortcut hash mismatch' }
        } else {
            if (Test-Path -LiteralPath $desk) { throw 'desktop shortcut should be absent' }
        }
        Write-Host 'putback shortcut-desktop OK'
        $states['shortcut-desktop'] = 'OK'
    } catch {
        Write-Host 'putback shortcut-desktop FAIL'
        $states['shortcut-desktop'] = 'FAIL'
        $errors.Add("shortcut-desktop: $($_.Exception.Message)") | Out-Null
    }

    # programs shortcut (already restored above; verify)
    try {
        $prog = Get-ProgramsShortcutPath -ProgramsDir $ProgramsDir
        $progMeta = $ShortcutMeta.programs
        $progPresent = [bool]$progMeta.present
        if ($progPresent) {
            if (-not (Test-Path -LiteralPath $prog)) { throw 'programs shortcut missing' }
            if ((Get-FileSha256Hex $prog) -ne $progMeta.sha256) { throw 'programs shortcut hash mismatch' }
        } else {
            if (Test-Path -LiteralPath $prog) { throw 'programs shortcut should be absent' }
        }
        Write-Host 'putback shortcut-programs OK'
        $states['shortcut-programs'] = 'OK'
    } catch {
        Write-Host 'putback shortcut-programs FAIL'
        $states['shortcut-programs'] = 'FAIL'
        $errors.Add("shortcut-programs: $($_.Exception.Message)") | Out-Null
    }

    # staging folder
    try {
        # PROC1-ID: role + manifest are Switch-only; strip before staging hash recheck — PROC1-D7/D13
        $switchOnlyNames = @('stable-manifest.json', 'build-role.json')
        if ($Moved -and (Test-Path -LiteralPath $FinalDir)) {
            if (Test-Path -LiteralPath $StagingDir) { Remove-Item -LiteralPath $StagingDir -Recurse -Force }
            foreach ($n in $switchOnlyNames) {
                $p = Join-Path $FinalDir $n
                if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p -Force }
            }
            Move-Item -LiteralPath $FinalDir -Destination $StagingDir
        } elseif (-not $Moved) {
            foreach ($n in $switchOnlyNames) {
                $p = Join-Path $StagingDir $n
                if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p -Force }
            }
        }
        $stagingNow = Get-DirectoryFileHashMap -Root $StagingDir
        $expected = ConvertTo-HashStringMap $PrepareRecord.staging_file_hashes
        foreach ($k in $expected.Keys) {
            if (-not $stagingNow.Contains($k)) { throw "staging missing $k" }
            if ($stagingNow[$k] -ne $expected[$k]) { throw "staging hash $k" }
        }
        foreach ($k in $stagingNow.Keys) {
            if (-not $expected.ContainsKey($k)) { throw "staging unexpected $k" }
        }
        Write-Host 'putback staging OK'
        $states['staging'] = 'OK'
    } catch {
        Write-Host 'putback staging FAIL'
        $states['staging'] = 'FAIL'
        $errors.Add("staging: $($_.Exception.Message)") | Out-Null
    }

    $anyFail = @($states.Values | Where-Object { $_ -eq 'FAIL' }).Count -gt 0
    if ($anyFail) {
        $detail = ($states.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }) -join '; '
        Write-Host "PUT-BACK INCOMPLETE $detail"
        throw ("PUT-BACK INCOMPLETE: " + ($errors -join ' | '))
    }
}

function Invoke-Switch {
    Assert-ZolaNotRunning -Probe $RunningZolaProbe -MutexNames $MutexNames -RequireProbe:$TestMode

    $promoDir = Join-Path $StableRoot "_promotions\$Tag"
    $stagingDir = Join-Path $StableRoot "_staging\$Tag"
    $finalDir = Join-Path $StableRoot $Tag
    $recordPath = Join-Path $promoDir '.prepare-record.json'
    if (-not (Test-Path -LiteralPath $recordPath)) { throw "Missing prepare record: $recordPath" }
    if (-not (Test-Path -LiteralPath $stagingDir)) { throw "Missing staging: $stagingDir" }
    if (Test-Path -LiteralPath $finalDir) { throw "Refuse: stable\$Tag already exists" }

    $record = Read-JsonFile $recordPath
    if ($TestMode -and $Synthetic) {
        if ($SyntheticCommit -and $SyntheticCommit -ne $record.commit) {
            throw 'Staging recheck: tag commit changed since Prepare'
        }
    } else {
        $commitNow = Get-TagCommit -TagName $Tag
        if ($commitNow -ne $record.commit) { throw 'Staging recheck: tag commit changed since Prepare' }
    }

    $stagingNow = Get-DirectoryFileHashMap -Root $stagingDir
    $expectedStaging = $record.staging_file_hashes
    foreach ($prop in $expectedStaging.PSObject.Properties) {
        if (-not $stagingNow.Contains($prop.Name)) { throw "Staging recheck: missing $($prop.Name)" }
        if ($stagingNow[$prop.Name] -ne $prop.Value) { throw "Staging recheck: hash changed $($prop.Name)" }
    }
    foreach ($k in $stagingNow.Keys) {
        if (-not ($expectedStaging.PSObject.Properties.Name -contains $k)) {
            throw "Staging recheck: unexpected file $k"
        }
    }

    $pluginNow = Get-PromotionsPluginHashMap -PromotionsTagDir $promoDir
    $expectedPlugins = $record.plugin_tag_hashes
    foreach ($prop in $expectedPlugins.PSObject.Properties) {
        if (-not $pluginNow.Contains($prop.Name)) { throw "Promotions recheck: missing $($prop.Name)" }
        if ($pluginNow[$prop.Name] -ne $prop.Value) { throw "Promotions recheck: hash changed $($prop.Name)" }
    }
    foreach ($k in $pluginNow.Keys) {
        if (-not ($expectedPlugins.PSObject.Properties.Name -contains $k)) {
            throw "Promotions recheck: unexpected file $k"
        }
    }

    $clientHashNow = Get-ClientBuildHash -PublishDir $stagingDir
    if ($clientHashNow -ne $record.client_build_hash) { throw 'Staging recheck: client_build_hash changed' }

    $diff = Compare-PluginSets -TagMap $pluginNow -LiveMap (Get-LivePluginHashMap -ProfileRoot $ProfileRoot)
    if (-not $diff.Equal) {
        Write-Host 'Switch: plugin STOP - differences:'
        Write-Host ("  added: " + ((@($diff.Added) | Sort-Object) -join ', '))
        Write-Host ("  removed: " + ((@($diff.Removed) | Sort-Object) -join ', '))
        Write-Host ("  changed: " + ((@($diff.Changed) | Sort-Object) -join ', '))
        if (-not $ApprovedPluginCopy) {
            throw 'Plugin set differs; re-run with -ApprovedPluginCopy after Brian approves the file list'
        }
        # F6: approval covers exactly the Prepare-time list
        if (-not (Test-PluginDiffMatchesPrepare -LiveDiff $diff -PrepareDiff $record.plugin_diff)) {
            throw 'the plugin differences changed since Prepare; re-run Prepare and re-approve'
        }
    }

    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $backupDir = Join-Path $StableRoot "backups\$Tag-$stamp"
    $outgoing = $record.outgoing
    $incoming = @{ kind = 'stable-tag'; tag = $Tag; commit = $record.commit }
    Write-Host "Switch: backup -> $backupDir"
    $index = Invoke-ProfileBackup -BackupDir $backupDir -ProfileRoot $ProfileRoot -HermesRoot $HermesRoot `
        -StableRoot $StableRoot -DesktopDir $DesktopDir -ProgramsDir $ProgramsDir `
        -Outgoing $outgoing -Incoming $incoming -StopOnIntegrityFail

    $beforeCurrent = $index.current_txt_before
    $shortcutMeta = $index.shortcuts_before
    $beforePluginHashes = ConvertTo-HashStringMap $index.live_plugin_hashes
    $pluginSnapDir = Join-Path $backupDir '_plugin_snapshot'

    # F1: drill uses the real Restore-Stable.ps1
    Write-Host 'Switch: restore drill via Restore-Stable.ps1'
    $scratch = Join-Path $env:TEMP ("zola-restore-drill-" + [guid]::NewGuid().ToString('N'))
    $restoreScript = Join-Path $here 'Restore-Stable.ps1'
    & $restoreScript -Backup $backupDir -Target $scratch -Drill -ConfirmName (Split-Path -Leaf $backupDir) `
        -StableRoot $StableRoot -ProfileRoot $scratch -HermesRoot $HermesRoot `
        -DesktopDir $DesktopDir -ProgramsDir $ProgramsDir -TestMode:$TestMode `
        -LiveCheckout $LiveCheckout -RunningZolaProbe $RunningZolaProbe

    $liveChangeStarted = $false
    $pluginsApplied = $false
    $moved = $false
    try {
        if (-not $diff.Equal) {
            Invoke-PluginApplyFromPromotions -Diff $diff -PromoDir $promoDir
            $pluginsApplied = $true
            $liveChangeStarted = $true
        }

        # PROC1-ID: fail-closed digests stop Switch before live change — PROC1-D13
        $hermes = Get-HermesStateDigest -HermesRoot $HermesRoot
        $configPath = Join-Path $ProfileRoot 'config.yaml'
        $installed = Get-LivePluginHashMap -ProfileRoot $ProfileRoot
        $scriptsState = Get-PromotionScriptsState -RepoRoot $RepoRoot
        $manifest = @{
            tag                        = $Tag
            commit                     = $record.commit
            client_build_hash          = $record.client_build_hash
            hermes_head                = $hermes.head
            hermes_local_edit_digest   = $hermes.local_edit_digest
            pip_freeze_digest          = $hermes.pip_freeze_digest
            plugins_tag                = $pluginNow
            plugins_installed          = $installed
            config_yaml_sha256         = $(if (Test-Path $configPath) { Get-FileSha256Hex $configPath } else { $null })
            backup_folder              = Split-Path -Leaf $backupDir
            promotion_scripts_commit   = (git -C $RepoRoot rev-parse HEAD 2>$null)
            promotion_scripts_digest   = $scriptsState.digest
            promotion_scripts_dirty    = $scriptsState.dirty
            promoted_at                = (Get-Date).ToString('o')
            plugin_compare_rules       = (Get-PluginCompareRulesObject)
            digest_algorithms          = (Get-DigestAlgorithmsObject)
        }
        # PROC1-ID Phase 4c: save freeze text for drift package add/remove/change — PROC1-D13
        $freezePath = Join-Path $promoDir 'pip-freeze.txt'
        $utf8 = New-Object System.Text.UTF8Encoding $false
        $freezeText = ''
        if ($null -ne $hermes.pip_freeze_text) { $freezeText = [string]$hermes.pip_freeze_text }
        [System.IO.File]::WriteAllText($freezePath, $freezeText, $utf8)
        Write-JsonFile -Object $manifest -Path (Join-Path $stagingDir 'stable-manifest.json')
        # PROC1-ID: role file beside the exe; excluded from Prepare client_build_hash (written at Switch) — PROC1-D7
        $role = [ordered]@{
            role     = 'stable'
            tag      = $Tag
            commit   = [string]$record.commit
            manifest = 'stable-manifest.json'
        }
        Write-JsonFile -Object $role -Path (Join-Path $stagingDir 'build-role.json')

        Move-Item -LiteralPath $stagingDir -Destination $finalDir
        $moved = $true
        $liveChangeStarted = $true

        Set-Content -LiteralPath (Join-Path $StableRoot 'current.txt') -Value $Tag -NoNewline

        if ($InjectAfterPluginCopy) {
            & $InjectAfterPluginCopy
        }

        $exe = Join-Path $finalDir 'Zola.Client.exe'
        New-ShortcutZola -LinkPath (Get-DesktopShortcutPath -DesktopDir $DesktopDir) -TargetPath $exe -WorkDir $finalDir
        New-ShortcutZola -LinkPath (Get-ProgramsShortcutPath -ProgramsDir $ProgramsDir) -TargetPath $exe -WorkDir $finalDir

        Write-Host "Switch: SUCCESS stable=$finalDir backup=$backupDir"
    } catch {
        Write-Host "Switch: FAILURE - all-or-nothing put-back: $($_.Exception.Message)"
        if ($liveChangeStarted) {
            Invoke-PutBackAll -PluginsApplied $pluginsApplied -Diff $diff -PluginSnapDir $pluginSnapDir `
                -BeforePluginHashes $beforePluginHashes -BeforeCurrent $beforeCurrent `
                -ShortcutMeta $shortcutMeta -Moved $moved -StagingDir $stagingDir -FinalDir $finalDir `
                -PrepareRecord $record
        }
        throw
    }
}

if ($Prepare) { Invoke-Prepare }
if ($Switch) { Invoke-Switch }
