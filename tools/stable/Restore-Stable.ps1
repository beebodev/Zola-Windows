# PROC1-STABLE: restore profile and outgoing release from a promotion backup — PROC1-D12
#Requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Backup,
    [string]$Target,
    [switch]$IncludeCredentials,
    [string]$StableRoot = 'C:\Users\test\Zola\stable',
    [string]$ProfileRoot = $(Join-Path $env:LOCALAPPDATA 'hermes\profiles\zola'),
    [string]$ClientDataRoot = $(Join-Path $env:LOCALAPPDATA 'ZolaClient'),
    [string]$HermesRoot = 'C:\Users\test\Dev\hermes-agent',
    [string]$LiveCheckout = 'C:\Users\test\Dev\zola-windows',
    [string]$DesktopDir = $([Environment]::GetFolderPath('Desktop')),
    [string]$ProgramsDir = $([Environment]::GetFolderPath('Programs')),
    [switch]$TestMode,
    [switch]$Drill,
    [string]$ConfirmName,
    [switch]$ForceSecondConfirm,
    [scriptblock]$RunningZolaProbe,
    [string[]]$MutexNames
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module (Join-Path $here 'StableCommon.psm1') -Force

$StableRoot = Resolve-FullPath $StableRoot
$ProfileRoot = Resolve-FullPath $ProfileRoot
$ClientDataRoot = Resolve-FullPath $ClientDataRoot
$HermesRoot = Resolve-FullPath $HermesRoot
$LiveCheckout = Resolve-FullPath $LiveCheckout
$DesktopDir = Resolve-FullPath $DesktopDir
$ProgramsDir = Resolve-FullPath $ProgramsDir

$liveRoots = Get-LiveRootSet

$backupDir = $Backup
if (-not [IO.Path]::IsPathRooted($backupDir)) {
    $backupDir = Join-Path $StableRoot "backups\$Backup"
}
$backupDir = Resolve-FullPath $backupDir
if (-not (Test-Path -LiteralPath (Join-Path $backupDir 'backup-index.json'))) {
    throw "Backup index missing: $backupDir"
}

$isDrill = $Drill -or ($PSBoundParameters.ContainsKey('Target') -and $Target)
$writeRoot = if ($isDrill) {
    if (-not $Target) { throw 'Drill requires -Target' }
    Resolve-FullPath $Target
} else {
    $ProfileRoot
}

if ($TestMode -or $isDrill) {
    Assert-TestModeSafeRoot -Path $writeRoot -LiveRoots $liveRoots -Label 'Target/Profile'
    if ($TestMode) {
        Assert-TestModeSafeRoot -Path $DesktopDir -LiveRoots $liveRoots -Label 'DesktopDir'
        Assert-TestModeSafeRoot -Path $ProgramsDir -LiveRoots $liveRoots -Label 'ProgramsDir'
    }
    if ($isDrill) {
        Assert-TestModeSafeRoot -Path $writeRoot -LiveRoots @((Resolve-FullPath $DefaultStableRoot)) -Label 'StableRoot'
    }
}

if (-not $isDrill) {
    Assert-ZolaNotRunning -Probe $RunningZolaProbe -MutexNames $MutexNames
}

$index = Read-JsonFile (Join-Path $backupDir 'backup-index.json')
$outgoing = $index.outgoing
$backupLeaf = Split-Path -Leaf $backupDir

Write-Host 'WARNING (D12): restore loses data stored since this promotion and cannot undo sends.'
$outKind = $outgoing.kind
$outTag = $null
$outHead = $null
if ($outgoing.PSObject.Properties.Name -contains 'tag') { $outTag = $outgoing.tag }
if ($outgoing.PSObject.Properties.Name -contains 'head') { $outHead = $outgoing.head }
Write-Host ("This backup belongs to outgoing kind=$outKind tag=$outTag head=$outHead")

if (-not $ConfirmName) {
    if ($TestMode) {
        throw 'Restore refuses without typed confirmation (-ConfirmName)'
    }
    $ConfirmName = Read-Host "Type the backup folder name ($backupLeaf) to confirm"
}
if ($ConfirmName -ne $backupLeaf) {
    throw "Confirmation mismatch: expected '$backupLeaf'"
}

$hermesNow = Get-HermesStateDigest -HermesRoot $HermesRoot
$hermesOut = $index.hermes
$mismatch = @()
if ($hermesOut.head -and $hermesNow.head -ne $hermesOut.head) { $mismatch += 'head' }
if ($hermesOut.local_edit_digest -and $hermesNow.local_edit_digest -ne $hermesOut.local_edit_digest) { $mismatch += 'local_edit_digest' }
if ($hermesOut.pip_freeze_digest -and $hermesNow.pip_freeze_digest -ne $hermesOut.pip_freeze_digest) { $mismatch += 'pip_freeze_digest' }
if ($mismatch.Count -gt 0 -and -not $isDrill) {
    Write-Host ("Hermes mismatch vs outgoing backup: " + ($mismatch -join ', '))
    if (-not $ForceSecondConfirm) {
        if ($TestMode) {
            throw "Hermes-mismatch warning fires: $($mismatch -join ',')"
        }
        $ans = Read-Host 'Type YES to restore anyway (cannot roll Hermes back)'
        if ($ans -ne 'YES') { throw 'Restore aborted on Hermes mismatch' }
    }
}

$hasOutHead = $outgoing.PSObject.Properties.Name -contains 'head'
if ($outgoing.kind -eq 'pre-stable' -and $hasOutHead -and $outgoing.head) {
    $liveHead = (git -C $LiveCheckout rev-parse HEAD 2>$null)
    Write-Host "Pre-stable outgoing checkout HEAD recorded: $($outgoing.head)"
    if ($liveHead -and $liveHead -ne $outgoing.head) {
        Write-Host "WARNING: live checkout HEAD now differs ($liveHead). The fallback command would run that newer code."
    }
}

function Get-DbSchemaVersionFromIndex {
    param($Index, [string]$PathNorm)
    foreach ($d in @($Index.databases)) {
        if ($d.path -eq $PathNorm) { return [int]$d.schema_version }
    }
    return $null
}

function Invoke-DrillVerify {
    param([string]$ScratchRoot)
    $dbChecked = 0
    $fileChecked = 0
    $credChecked = 0
    $schemaByPath = @{}
    foreach ($d in @($index.databases)) {
        $schemaByPath["$($d.path)"] = [int]$d.schema_version
    }
    foreach ($f in $index.files) {
        if ($f.kind -eq 'credential') {
            $src = Join-Path $backupDir ($f.path.Replace('/', '\'))
            $got = Get-FileSha256Hex $src
            if ($got -ne $f.sha256) { throw "credential backup hash mismatch path=$($f.path)" }
            $credChecked++
            continue
        }
        $dst = Join-Path $ScratchRoot ($f.path.Replace('/', '\'))
        if ($f.kind -eq 'database') {
            $ir = Invoke-SqliteTool -HermesRoot $HermesRoot -Args @('integrity', $dst)
            if ($ir.Output -notmatch 'status=OK') { throw "drill integrity fail path=$($f.path)" }
            $vr = Invoke-SqliteTool -HermesRoot $HermesRoot -Args @('user_version', $dst)
            $ver = 0
            if ($vr.Output -match 'user_version=(\d+)') { $ver = [int]$Matches[1] }
            $expected = $schemaByPath["$($f.path)"]
            if ($null -eq $expected) { throw "drill schema_version missing in index path=$($f.path)" }
            if ($ver -ne $expected) { throw "drill user_version mismatch path=$($f.path) got=$ver expected=$expected" }
            $dbChecked++
        } else {
            $got = Get-FileSha256Hex $dst
            if ($got -ne $f.sha256) { throw "drill hash mismatch path=$($f.path)" }
            $fileChecked++
        }
    }
    Write-Host "Drill verify: databases=$dbChecked files=$fileChecked credentials=$credChecked"
}

function Move-DisplacedFile {
    param(
        [string]$SrcFull,
        [string]$RelNorm,
        [string]$DisplacedRoot,
        [System.Collections.Generic.List[string]]$List
    )
    $dst = Join-Path $DisplacedRoot ($RelNorm.Replace('/', '\'))
    $d = Split-Path -Parent $dst
    if (-not (Test-Path -LiteralPath $d)) { New-Item -ItemType Directory -Force -Path $d | Out-Null }
    if (Test-Path -LiteralPath $dst) { Remove-Item -LiteralPath $dst -Force }
    Move-Item -LiteralPath $SrcFull -Destination $dst -Force
    $List.Add($RelNorm) | Out-Null
}

$scratchGone = $true
$preRestoreName = $null
try {
    if ($isDrill -and -not (Test-Path -LiteralPath $writeRoot)) {
        New-Item -ItemType Directory -Force -Path $writeRoot | Out-Null
    }

    if (-not $isDrill) {
        # G1: known outgoing kinds only — refuse before any change
        $outKindNow = "$($outgoing.kind)"
        if ($outKindNow -ne 'pre-stable' -and $outKindNow -ne 'stable-tag' -and $outKindNow -ne 'pre-restore-snapshot') {
            throw "Refuse: unknown outgoing.kind=$outKindNow"
        }

        # F3.1: refuse missing outgoing stable folder before any change
        if ($outKindNow -eq 'stable-tag') {
            $tag = $outgoing.tag
            $exe = Join-Path $StableRoot "$tag\Zola.Client.exe"
            if (-not (Test-Path -LiteralPath $exe)) {
                throw "Refuse: outgoing stable folder missing exe: $exe"
            }
        }

        # F3.2: pre-restore backup
        $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
        $preRestoreDir = Join-Path $StableRoot "backups\pre-restore-$stamp"
        $preRestoreName = Split-Path -Leaf $preRestoreDir
        Write-Host "Restore: pre-restore backup -> $preRestoreDir"
        $preOutgoing = @{ kind = 'pre-restore-snapshot'; of_backup = $backupLeaf }
        $preIncoming = @{ kind = 'restore-target'; backup = $backupLeaf }
        $null = Invoke-ProfileBackup -BackupDir $preRestoreDir -ProfileRoot $ProfileRoot -HermesRoot $HermesRoot `
            -StableRoot $StableRoot -DesktopDir $DesktopDir -ProgramsDir $ProgramsDir `
            -Outgoing $preOutgoing -Incoming $preIncoming -StopOnIntegrityFail

        $displacedRoot = Join-Path $preRestoreDir '_displaced'
        New-Item -ItemType Directory -Force -Path $displacedRoot | Out-Null
        $displaced = New-Object System.Collections.Generic.List[string]

        # Build set of backed-up relative paths
        $backedUp = @{}
        foreach ($f in $index.files) {
            if ($f.kind -eq 'credential' -and -not $IncludeCredentials) { continue }
            $backedUp["$($f.path)"] = $true
        }

        # F3.3: move live-only profile files (excl logs/cache/creds) into _displaced
        $liveFiles = Get-ProfileFilesForBackup -ProfileRoot $writeRoot
        foreach ($lf in $liveFiles) {
            if ($lf.IsCredential -and -not $IncludeCredentials) { continue }
            if (-not $backedUp.ContainsKey($lf.RelNorm)) {
                Move-DisplacedFile -SrcFull $lf.FullName -RelNorm $lf.RelNorm -DisplacedRoot $displacedRoot -List $displaced
            }
        }

        # F3.4: equalize plugin comparison set to snapshot
        $snap = Join-Path $backupDir '_plugin_snapshot'
        $expectedPlugins = ConvertTo-HashStringMap $index.live_plugin_hashes
        $livePlugins = Get-LivePluginHashMap -ProfileRoot $writeRoot
        foreach ($rel in @($livePlugins.Keys)) {
            if (-not $expectedPlugins.ContainsKey($rel)) {
                $src = Join-Path $writeRoot ($rel.Replace('/', '\'))
                if (Test-Path -LiteralPath $src) {
                    Move-DisplacedFile -SrcFull $src -RelNorm $rel -DisplacedRoot $displacedRoot -List $displaced
                }
            }
        }
        foreach ($rel in @($expectedPlugins.Keys)) {
            $src = Join-Path $snap ($rel.Replace('/', '\'))
            $dst = Join-Path $writeRoot ($rel.Replace('/', '\'))
            $d = Split-Path -Parent $dst
            if (-not (Test-Path -LiteralPath $d)) { New-Item -ItemType Directory -Force -Path $d | Out-Null }
            Copy-Item -LiteralPath $src -Destination $dst -Force
        }
        $afterPlugins = Get-LivePluginHashMap -ProfileRoot $writeRoot
        foreach ($k in $expectedPlugins.Keys) {
            if (-not $afterPlugins.Contains($k)) { throw "plugin restore missing $k" }
            if ($afterPlugins[$k] -ne $expectedPlugins[$k]) { throw "plugin restore hash mismatch $k" }
        }
        foreach ($k in $afterPlugins.Keys) {
            if (-not $expectedPlugins.ContainsKey($k)) { throw "plugin restore leftover $k" }
        }
        if ($displaced.Count -gt 0) {
            Write-Host ("Displaced paths: " + ($displaced -join ', '))
        }
    }

    foreach ($f in $index.files) {
        if ($f.kind -eq 'credential') {
            if ($isDrill) {
                $src = Join-Path $backupDir ($f.path.Replace('/', '\'))
                $got = Get-FileSha256Hex $src
                if ($got -ne $f.sha256) { throw "credential backup hash mismatch path=$($f.path)" }
                continue
            }
            if (-not $IncludeCredentials) { continue }
        }
        $src = Join-Path $backupDir ($f.path.Replace('/', '\'))
        if (-not (Test-Path -LiteralPath $src)) {
            if ($f.kind -eq 'credential') { continue }
            throw "Missing backup file: $($f.path)"
        }

        $dst = Join-Path $writeRoot ($f.path.Replace('/', '\'))
        $dstFull = [IO.Path]::GetFullPath($dst)
        if (-not (Test-PathUnderOrEqual -Candidate $dstFull -Root $writeRoot)) {
            throw "Refuse path escape: $dstFull"
        }
        $d = Split-Path -Parent $dstFull
        if (-not (Test-Path -LiteralPath $d)) { New-Item -ItemType Directory -Force -Path $d | Out-Null }

        if ($f.kind -eq 'database') {
            $r = Invoke-SqliteTool -HermesRoot $HermesRoot -Args @('backup', $src, $dstFull)
            if ($r.ExitCode -ne 0) { throw "db restore failed path=$($f.path)" }
        } else {
            Copy-Item -LiteralPath $src -Destination $dstFull -Force
        }
    }

    if ($isDrill) {
        Invoke-DrillVerify -ScratchRoot $writeRoot
    }

    if (-not $isDrill) {
        if ($outgoing.kind -eq 'pre-stable') {
            Set-Content -LiteralPath (Join-Path $StableRoot 'current.txt') -Value 'none' -NoNewline
            Remove-ShortcutIfExists (Get-DesktopShortcutPath -DesktopDir $DesktopDir)
            Remove-ShortcutIfExists (Get-ProgramsShortcutPath -ProgramsDir $ProgramsDir)
            Write-Host "Fallback launch command: $($outgoing.launch_command)"
        } elseif ($outgoing.kind -eq 'stable-tag') {
            $tag = $outgoing.tag
            Set-Content -LiteralPath (Join-Path $StableRoot 'current.txt') -Value $tag -NoNewline
            $exe = Join-Path $StableRoot "$tag\Zola.Client.exe"
            $work = Join-Path $StableRoot $tag
            New-ShortcutZola -LinkPath (Get-DesktopShortcutPath -DesktopDir $DesktopDir) -TargetPath $exe -WorkDir $work
            New-ShortcutZola -LinkPath (Get-ProgramsShortcutPath -ProgramsDir $ProgramsDir) -TargetPath $exe -WorkDir $work
        } elseif ($outgoing.kind -eq 'pre-restore-snapshot') {
            # G1: undo a prior restore — put back current.txt and shortcut bytes from this backup
            $beforeCurrent = $null
            if ($index.PSObject.Properties.Name -contains 'current_txt_before') {
                $beforeCurrent = $index.current_txt_before
            }
            $ct = Join-Path $StableRoot 'current.txt'
            if ($null -eq $beforeCurrent) {
                if (Test-Path -LiteralPath $ct) { Remove-Item -LiteralPath $ct -Force }
                if (Test-Path -LiteralPath $ct) { throw 'pre-restore-snapshot: current.txt still present' }
            } else {
                Set-Content -LiteralPath $ct -Value "$beforeCurrent" -NoNewline
                $got = (Get-Content -LiteralPath $ct -Raw).Trim()
                if ($got -ne "$beforeCurrent") { throw 'pre-restore-snapshot: current.txt content mismatch' }
            }
            $scMeta = $index.shortcuts_before
            $restored = Restore-ShortcutBytes -BackupDir $backupDir -ShortcutMeta $scMeta `
                -DesktopDir $DesktopDir -ProgramsDir $ProgramsDir
            if (-not (Test-ShortcutHashesMatch -Meta $restored -DesktopDir $DesktopDir -ProgramsDir $ProgramsDir)) {
                throw 'pre-restore-snapshot: shortcut hash verify failed'
            }
            Write-Host 'Restore: pre-restore-snapshot put back current.txt and shortcuts'
        } else {
            throw "Refuse: unknown outgoing.kind=$($outgoing.kind)"
        }
        Write-Host "Restore: PASS pre-restore-backup=$preRestoreName (undo with Restore-Stable on that folder)"
    } else {
        Write-Host 'Restore: PASS'
    }
}
catch {
    # G2: name the undo backup when live restore fails after it was taken
    $failFields = @{ status = 'FAIL'; error = $_.Exception.Message }
    if ($preRestoreName) {
        $failFields['pre_restore_backup'] = $preRestoreName
    }
    Write-Host ("Restore: FAIL fields=" + (ConvertTo-Json -InputObject $failFields -Compress))
    throw
}
finally {
    if ($isDrill -and $Target) {
        $t = Resolve-FullPath $Target
        if (Test-Path -LiteralPath $t) {
            Remove-Item -LiteralPath $t -Recurse -Force -ErrorAction SilentlyContinue
        }
        $scratchGone = -not (Test-Path -LiteralPath $t)
        Write-Host "Drill: scratch_deleted=$scratchGone path=$t"
    }
}
