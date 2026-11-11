# PROC1-STABLE: shared helpers for promote/restore — PROC1-D1/D12/D13
#Requires -Version 5.1
Set-StrictMode -Version Latest

# PROC1-STABLE: named path/name constants — PROC1-D1
$script:DefaultStableRoot = 'C:\Users\test\Zola\stable'
$script:DefaultProfileRoot = Join-Path $env:LOCALAPPDATA 'hermes\profiles\zola'
$script:DefaultClientDataRoot = Join-Path $env:LOCALAPPDATA 'ZolaClient'
$script:DefaultHermesRoot = 'C:\Users\test\Dev\hermes-agent'
$script:DefaultLiveCheckout = 'C:\Users\test\Dev\zola-windows'
$script:ShortcutName = 'Zola.lnk'
$script:MutexPhone = 'Local\ZolaPhone'
$script:MutexWatcher = 'Local\ZolaWatcher'
# "SQLite format 3\0" (16 bytes)
$script:SqliteHeader = [byte[]](83,81,76,105,116,101,32,102,111,114,109,97,116,32,51,0)

# PROC1-STABLE: explicit test-only excludes (not pattern guess) — P10-READ/WATCH — PROC1-D13
$script:NamedPluginExcludes = @(
    'zola_memory/l6_hold_guard.py',
    'zola_phone/outage.py'
)

$script:PluginMaps = @(
    @{ Repo = 'zola_workspace'; LiveRel = 'plugins\zola_workspace' },
    @{ Repo = 'zola_memory';    LiveRel = 'plugins\zola_memory' },
    @{ Repo = 'zola_tools';     LiveRel = 'plugins\zola_tools' },
    @{ Repo = 'zola_phone';     LiveRel = 'plugins\zola_phone' }
)

$script:CredentialRelPaths = @(
    'auth.json',
    'token.dpapi'
)

function Get-StableModuleRoot {
    Split-Path -Parent $PSCommandPath
}

function Resolve-FullPath {
    param([Parameter(Mandatory)][string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) { throw 'Path is empty' }
    $full = [System.IO.Path]::GetFullPath($Path)
    return $full.TrimEnd('\')
}

function Get-DefaultDesktopDir {
    [Environment]::GetFolderPath('Desktop')
}

function Get-DefaultProgramsDir {
    [Environment]::GetFolderPath('Programs')
}

function Get-DesktopShortcutPath {
    param([string]$DesktopDir = $(Get-DefaultDesktopDir))
    Join-Path $DesktopDir $script:ShortcutName
}

function Get-ProgramsShortcutPath {
    param([string]$ProgramsDir = $(Get-DefaultProgramsDir))
    Join-Path $ProgramsDir $script:ShortcutName
}

function Get-LiveRootSet {
    param(
        [string]$StableRoot = $script:DefaultStableRoot,
        [string]$ProfileRoot = $script:DefaultProfileRoot,
        [string]$ClientDataRoot = $script:DefaultClientDataRoot
    )
    @(
        (Resolve-FullPath $StableRoot)
        (Resolve-FullPath $ProfileRoot)
        (Resolve-FullPath $ClientDataRoot)
        (Resolve-FullPath (Get-DefaultDesktopDir))
        (Resolve-FullPath (Get-DefaultProgramsDir))
        (Resolve-FullPath (Get-DesktopShortcutPath))
        (Resolve-FullPath (Get-ProgramsShortcutPath))
        (Resolve-FullPath $script:DefaultLiveCheckout)
    )
}

function Test-PathUnderOrEqual {
    param([string]$Candidate, [string]$Root)
    $c = (Resolve-FullPath $Candidate).ToLowerInvariant()
    $r = (Resolve-FullPath $Root).ToLowerInvariant()
    return ($c -eq $r) -or $c.StartsWith($r + '\')
}

function Assert-TestModeSafeRoot {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string[]]$LiveRoots,
        [string]$Label = 'root'
    )
    $full = Resolve-FullPath $Path
    foreach ($live in $LiveRoots) {
        if (Test-PathUnderOrEqual -Candidate $full -Root $live) {
            throw "TestMode refuses live $Label path: $full (under $live)"
        }
        if (Test-PathUnderOrEqual -Candidate $live -Root $full) {
            # Path is an ancestor of a live root — still refuse to avoid writing above live trees via Target
            # Only refuse when Path equals a live root or is under one; being ancestor of live is OK for scratch parents
        }
    }
}

function Get-FileSha256Hex {
    param([Parameter(Mandatory)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-DirectoryFileHashMap {
    param([Parameter(Mandatory)][string]$Root)
    $map = [ordered]@{}
    if (-not (Test-Path -LiteralPath $Root)) { return $map }
    Get-ChildItem -LiteralPath $Root -Recurse -File -Force | ForEach-Object {
        $rel = $_.FullName.Substring((Resolve-FullPath $Root).Length).TrimStart('\').Replace('\', '/')
        $map[$rel] = (Get-FileSha256Hex $_.FullName)
    }
    return $map
}

# PROC1-STABLE: client_build_hash = staged build output only (every file under staging dir)
function Get-ClientBuildHash {
    param([Parameter(Mandatory)][string]$PublishDir)
    $lines = New-Object System.Collections.Generic.List[string]
    $root = Resolve-FullPath $PublishDir
    Get-ChildItem -LiteralPath $root -Recurse -File -Force | Sort-Object FullName | ForEach-Object {
        $rel = $_.FullName.Substring($root.Length).TrimStart('\').Replace('\', '/')
        $sha = Get-FileSha256Hex $_.FullName
        $lines.Add("$rel`n$sha")
    }
    $text = ($lines -join "`n") + $(if ($lines.Count -gt 0) { "`n" } else { '' })
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($text)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        return ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '').ToLowerInvariant()
    } finally {
        $sha.Dispose()
    }
}

# Minimum WinUI resources always required (Phase 6c crash); plus every .xaml→.xbf from client source (Phase 6d)
function Get-ExpectedWinUiResourceRels {
    param([string]$ClientSourceDir)
    $minimum = @(
        'Zola.Client.pri',
        'App.xbf',
        'MainWindow.xbf',
        'Themes\ZolaTokens.xbf'
    )
    $set = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
    foreach ($m in $minimum) { [void]$set.Add($m) }
    if ($ClientSourceDir -and (Test-Path -LiteralPath $ClientSourceDir)) {
        $root = Resolve-FullPath $ClientSourceDir
        Get-ChildItem -LiteralPath $root -Recurse -Filter '*.xaml' -File -Force -ErrorAction SilentlyContinue | ForEach-Object {
            $rel = $_.FullName.Substring($root.Length).TrimStart('\')
            $parts = @($rel -split '[\\/]')
            if ($parts -contains 'bin' -or $parts -contains 'obj') { return }
            $xbf = [IO.Path]::ChangeExtension($rel, '.xbf')
            [void]$set.Add($xbf)
        }
    }
    return @($set | Sort-Object)
}

# Prepare must refuse a staging tree that would APPCRASH without WinUI XAML/PRI
function Assert-StagingHasWinUiResources {
    param(
        [Parameter(Mandatory)][string]$StagingDir,
        [string]$ClientSourceDir,
        [string[]]$ExpectedRels
    )
    $required = if ($null -ne $ExpectedRels -and $ExpectedRels.Count -gt 0) {
        @($ExpectedRels)
    } else {
        Get-ExpectedWinUiResourceRels -ClientSourceDir $ClientSourceDir
    }
    $missing = New-Object System.Collections.Generic.List[string]
    foreach ($rel in $required) {
        $path = Join-Path $StagingDir $rel
        if (-not (Test-Path -LiteralPath $path)) {
            $missing.Add($rel) | Out-Null
        }
    }
    if ($missing.Count -gt 0) {
        throw ("Prepare: staging missing WinUI resources: " + ($missing -join ', '))
    }
    Write-Host ("Prepare: WinUI resource check OK checked=" + ($required -join ', '))
}

function Test-PluginPathExcluded {
    param([Parameter(Mandatory)][string]$RepoRelative) # e.g. zola_memory/foo.py
    $n = $RepoRelative.Replace('\', '/')
    if ($n -match '(^|/)tests(/|$)') { return $true }
    if ($n -match '(^|/)__pycache__(/|$)') { return $true }
    if ($n -like '*.pyc') { return $true }
    foreach ($e in $script:NamedPluginExcludes) {
        if ($n -eq $e) { return $true }
    }
    return $false
}

function Get-ComparisonFilesFromRepoTree {
    param([Parameter(Mandatory)][string]$HermesPluginsRoot)
    $files = [ordered]@{}
    foreach ($m in $script:PluginMaps) {
        $repoDir = Join-Path $HermesPluginsRoot $m.Repo
        if (-not (Test-Path -LiteralPath $repoDir)) { continue }
        Get-ChildItem -LiteralPath $repoDir -Recurse -File -Force | ForEach-Object {
            $relInPlugin = $_.FullName.Substring((Resolve-FullPath $repoDir).Length).TrimStart('\').Replace('\', '/')
            $repoKey = "$($m.Repo)/$relInPlugin"
            if (Test-PluginPathExcluded $repoKey) { return }
            $liveRel = (Join-Path $m.LiveRel ($relInPlugin.Replace('/', '\'))).Replace('\', '/')
            $files[$liveRel] = $_.FullName
        }
    }
    $tts = Join-Path $HermesPluginsRoot 'zola_tts\deepgram_tts.py'
    if (Test-Path -LiteralPath $tts) {
        $files['zola-tts/deepgram_tts.py'] = $tts
    }
    return $files
}

function Copy-ComparisonSetToPromotions {
    param(
        [Parameter(Mandatory)][string]$HermesPluginsRoot,
        [Parameter(Mandatory)][string]$PromotionsTagDir
    )
    $files = Get-ComparisonFilesFromRepoTree -HermesPluginsRoot $HermesPluginsRoot
    foreach ($liveRel in $files.Keys) {
        $src = $files[$liveRel]
        $dst = Join-Path $PromotionsTagDir ($liveRel.Replace('/', '\'))
        $dstDir = Split-Path -Parent $dst
        if (-not (Test-Path -LiteralPath $dstDir)) {
            New-Item -ItemType Directory -Force -Path $dstDir | Out-Null
        }
        Copy-Item -LiteralPath $src -Destination $dst -Force
    }
    return $files.Count
}

function Get-PromotionsPluginHashMap {
    param([Parameter(Mandatory)][string]$PromotionsTagDir)
    $map = [ordered]@{}
    $pluginsRoot = Join-Path $PromotionsTagDir 'plugins'
    if (Test-Path -LiteralPath $pluginsRoot) {
        Get-ChildItem -LiteralPath $pluginsRoot -Recurse -File -Force | ForEach-Object {
            $rel = ('plugins/' + $_.FullName.Substring((Resolve-FullPath $pluginsRoot).Length).TrimStart('\').Replace('\', '/'))
            $map[$rel] = (Get-FileSha256Hex $_.FullName)
        }
    }
    $tts = Join-Path $PromotionsTagDir 'zola-tts\deepgram_tts.py'
    if (Test-Path -LiteralPath $tts) {
        $map['zola-tts/deepgram_tts.py'] = (Get-FileSha256Hex $tts)
    }
    return $map
}

function Get-LivePluginHashMap {
    param([Parameter(Mandatory)][string]$ProfileRoot)
    $map = [ordered]@{}
    foreach ($m in $script:PluginMaps) {
        $liveDir = Join-Path $ProfileRoot $m.LiveRel
        if (-not (Test-Path -LiteralPath $liveDir)) { continue }
        Get-ChildItem -LiteralPath $liveDir -Recurse -File -Force | ForEach-Object {
            $relIn = $_.FullName.Substring((Resolve-FullPath $liveDir).Length).TrimStart('\').Replace('\', '/')
            $repoKey = "$($m.Repo)/$relIn"
            # return = next pipeline object; continue would skip remaining files in this plugin
            if (Test-PluginPathExcluded $repoKey) { return }
            $liveRel = (Join-Path $m.LiveRel ($relIn.Replace('/', '\'))).Replace('\', '/')
            $map[$liveRel] = (Get-FileSha256Hex $_.FullName)
        }
    }
    $tts = Join-Path $ProfileRoot 'zola-tts\deepgram_tts.py'
    if (Test-Path -LiteralPath $tts) {
        $map['zola-tts/deepgram_tts.py'] = (Get-FileSha256Hex $tts)
    }
    return $map
}

function Compare-PluginSets {
    param(
        [Parameter(Mandatory)]$TagMap,   # ordered hashtable liveRel -> sha
        [Parameter(Mandatory)]$LiveMap
    )
    $added = New-Object System.Collections.Generic.List[string]
    $removed = New-Object System.Collections.Generic.List[string]
    $changed = New-Object System.Collections.Generic.List[string]
    $tagKeys = @($TagMap.Keys)
    $liveKeys = @($LiveMap.Keys)
    foreach ($k in $tagKeys) {
        if ($liveKeys -notcontains $k) {
            $added.Add($k) | Out-Null
        } elseif ("$($LiveMap[$k])" -ne "$($TagMap[$k])") {
            $changed.Add($k) | Out-Null
        }
    }
    foreach ($k in $liveKeys) {
        if ($tagKeys -notcontains $k) {
            $removed.Add($k) | Out-Null
        }
    }
    [pscustomobject]@{
        Added   = @($added)
        Removed = @($removed)
        Changed = @($changed)
        Equal   = ($added.Count -eq 0 -and $removed.Count -eq 0 -and $changed.Count -eq 0)
    }
}

function Test-MutexHeld {
    param([Parameter(Mandatory)][string]$Name)
    try {
        $m = [System.Threading.Mutex]::OpenExisting($Name)
        $m.Dispose()
        return $true
    } catch [System.Threading.WaitHandleCannotBeOpenedException] {
        return $false
    } catch {
        return $true
    }
}

# PROC1-STABLE: running-Zola detection incl. dotnet Zola.Client.csproj — Claude review
function Get-ZolaRunningStatus {
    param(
        [scriptblock]$Probe,
        [string[]]$MutexNames
    )
    if ($Probe) {
        return & $Probe
    }
    $phone = if ($MutexNames -and $MutexNames.Count -ge 1) { $MutexNames[0] } else { $script:MutexPhone }
    $watcher = if ($MutexNames -and $MutexNames.Count -ge 2) { $MutexNames[1] } else { $script:MutexWatcher }

    $reasons = New-Object System.Collections.Generic.List[string]
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | ForEach-Object {
        $name = $_.Name
        $cmd = $_.CommandLine
        if ($name -match '^(?i)Zola\.Client(\.exe)?$') {
            $reasons.Add(("process:{0}:{1}" -f $name, $_.ProcessId)) | Out-Null
        }
        elseif ($name -match '^(?i)dotnet(\.exe)?$' -and $cmd -and ($cmd -match 'Zola\.Client\.csproj')) {
            $reasons.Add(("dotnet:Zola.Client.csproj:{0}" -f $_.ProcessId)) | Out-Null
        }
        elseif ($cmd -and (
                $cmd -match '-p\s+zola\s+serve' -or
                $cmd -match 'zola_workspace\.watcher' -or
                $cmd -match '-m\s+zola_phone' -or
                $cmd -match '(?i)python.*\bzola_phone\b'
            )) {
            $reasons.Add(("cmdline:{0}" -f $_.ProcessId)) | Out-Null
        }
    }
    if (Test-MutexHeld $phone) { $reasons.Add("mutex:$phone") | Out-Null }
    if (Test-MutexHeld $watcher) { $reasons.Add("mutex:$watcher") | Out-Null }

    [pscustomobject]@{
        Running = ($reasons.Count -gt 0)
        Reasons = @($reasons)
    }
}

function Assert-ZolaNotRunning {
    param(
        [scriptblock]$Probe,
        [string[]]$MutexNames,
        [switch]$RequireProbe
    )
    # PROC1-ID: TestMode must inject a probe — never scan real processes — PROC1-D13
    if ($RequireProbe -and -not $Probe) {
        throw 'TestMode requires -RunningZolaProbe'
    }
    $st = Get-ZolaRunningStatus -Probe $Probe -MutexNames $MutexNames
    if ($st.Running) {
        throw ("Refuse: Zola appears running: " + ($st.Reasons -join '; '))
    }
}

function Get-ObservedPreStableLaunch {
    param([string]$LiveCheckout = $script:DefaultLiveCheckout)
    $client = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match '^(?i)Zola\.Client(\.exe)?$' } |
        Select-Object -First 1
    if (-not $client) {
        return $null
    }
    $parent = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object { $_.ProcessId -eq $client.ParentProcessId } |
        Select-Object -First 1
    $launchCmd = $null
    if ($parent -and $parent.CommandLine) {
        $launchCmd = $parent.CommandLine
    }
    $branch = $null
    $head = $null
    if (Test-Path -LiteralPath (Join-Path $LiveCheckout '.git')) {
        $branch = (git -C $LiveCheckout rev-parse --abbrev-ref HEAD 2>$null)
        $head = (git -C $LiveCheckout rev-parse HEAD 2>$null)
    }
    [pscustomobject]@{
        kind           = 'pre-stable'
        client_exe     = $client.ExecutablePath
        launch_command = $launchCmd
        checkout       = (Resolve-FullPath $LiveCheckout)
        branch         = $branch
        head           = $head
    }
}

function New-ShortcutZola {
    param(
        [Parameter(Mandatory)][string]$LinkPath,
        [Parameter(Mandatory)][string]$TargetPath,
        [Parameter(Mandatory)][string]$WorkDir
    )
    $dir = Split-Path -Parent $LinkPath
    if (-not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
    $w = New-Object -ComObject WScript.Shell
    $sc = $w.CreateShortcut($LinkPath)
    $sc.TargetPath = "$TargetPath"
    $sc.WorkingDirectory = "$WorkDir"
    $sc.Save()
}

function Remove-ShortcutIfExists {
    param([string]$LinkPath)
    if (Test-Path -LiteralPath $LinkPath) {
        Remove-Item -LiteralPath $LinkPath -Force
    }
}

function Get-ShortcutTargetOrNull {
    param([string]$LinkPath)
    if (-not (Test-Path -LiteralPath $LinkPath)) { return $null }
    $w = New-Object -ComObject WScript.Shell
    $sc = $w.CreateShortcut($LinkPath)
    return $sc.TargetPath
}

function Test-IsCredentialRelPath {
    param([string]$RelPath)
    # PROC1-STABLE F7: G-SECRETS credential list (names only; never open for classification beyond path)
    $n = $RelPath.Replace('\', '/').ToLowerInvariant()
    $leaf = Split-Path -Leaf $n
    if ($n -eq 'auth.json') { return $true }
    if ($n -eq 'token.dpapi' -or $n -like '*/token.dpapi') { return $true }
    if ($n -like 'phone/*' -or $n -eq 'phone') { return $true }
    if ($leaf -like '.env*') { return $true }
    if ($leaf -like '*.pem') { return $true }
    if ($leaf -like 'credentials*') { return $true }
    return $false
}

function Get-CredentialListDescription {
    @(
        'auth.json',
        'token.dpapi',
        '*/token.dpapi',
        'phone/*',
        '.env*',
        '*.pem',
        'credentials*'
    )
}

function Get-PromotionScriptsState {
    param(
        [Parameter(Mandatory)][string]$RepoRoot,
        [string]$ToolsStableDir
    )
    if (-not $ToolsStableDir) {
        $ToolsStableDir = Join-Path $RepoRoot 'tools\stable'
    }
    $root = Resolve-FullPath $ToolsStableDir
    $lines = New-Object System.Collections.Generic.List[string]
    if (Test-Path -LiteralPath $root) {
        Get-ChildItem -LiteralPath $root -Recurse -File -Force | Sort-Object FullName | ForEach-Object {
            $rel = $_.FullName.Substring($root.Length).TrimStart('\').Replace('\', '/')
            $sha = Get-FileSha256Hex $_.FullName
            $lines.Add("$rel`n$sha")
        }
    }
    $text = ($lines -join "`n") + $(if ($lines.Count -gt 0) { "`n" } else { '' })
    $digest = Get-DigestOfText $text
    $porcelain = (git -C $RepoRoot status --porcelain -- tools/stable 2>$null)
    $dirty = -not [string]::IsNullOrWhiteSpace((@($porcelain) -join ''))
    [pscustomobject]@{
        digest = $digest
        dirty  = [bool]$dirty
    }
}

function Save-ShortcutBytesBefore {
    param(
        [Parameter(Mandatory)][string]$BackupDir,
        [Parameter(Mandatory)][string]$DesktopDir,
        [Parameter(Mandatory)][string]$ProgramsDir
    )
    $dir = Join-Path $BackupDir '_shortcuts_before'
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    $result = @{
        desktop  = @{ present = $false; sha256 = $null; rel = 'Desktop-Zola.lnk' }
        programs = @{ present = $false; sha256 = $null; rel = 'Programs-Zola.lnk' }
    }
    $desk = Get-DesktopShortcutPath -DesktopDir $DesktopDir
    $prog = Get-ProgramsShortcutPath -ProgramsDir $ProgramsDir
    if (Test-Path -LiteralPath $desk) {
        $dst = Join-Path $dir 'Desktop-Zola.lnk'
        Copy-Item -LiteralPath $desk -Destination $dst -Force
        $result.desktop.present = $true
        $result.desktop.sha256 = (Get-FileSha256Hex $dst)
    }
    if (Test-Path -LiteralPath $prog) {
        $dst = Join-Path $dir 'Programs-Zola.lnk'
        Copy-Item -LiteralPath $prog -Destination $dst -Force
        $result.programs.present = $true
        $result.programs.sha256 = (Get-FileSha256Hex $dst)
    }
    return $result
}

function Restore-ShortcutBytes {
    param(
        [Parameter(Mandatory)][string]$BackupDir,
        [Parameter(Mandatory)]$ShortcutMeta,
        [Parameter(Mandatory)][string]$DesktopDir,
        [Parameter(Mandatory)][string]$ProgramsDir
    )
    $dir = Join-Path $BackupDir '_shortcuts_before'
    $desk = Get-DesktopShortcutPath -DesktopDir $DesktopDir
    $prog = Get-ProgramsShortcutPath -ProgramsDir $ProgramsDir
    $deskPresent = $false
    $progPresent = $false
    $deskSha = $null
    $progSha = $null
    if ($ShortcutMeta -is [System.Collections.IDictionary]) {
        $deskPresent = [bool]$ShortcutMeta['desktop'].present
        $progPresent = [bool]$ShortcutMeta['programs'].present
        $deskSha = $ShortcutMeta['desktop'].sha256
        $progSha = $ShortcutMeta['programs'].sha256
    } else {
        $deskPresent = [bool]$ShortcutMeta.desktop.present
        $progPresent = [bool]$ShortcutMeta.programs.present
        $deskSha = $ShortcutMeta.desktop.sha256
        $progSha = $ShortcutMeta.programs.sha256
    }
    if ($deskPresent) {
        $src = Join-Path $dir 'Desktop-Zola.lnk'
        $d = Split-Path -Parent $desk
        if (-not (Test-Path -LiteralPath $d)) { New-Item -ItemType Directory -Force -Path $d | Out-Null }
        Copy-Item -LiteralPath $src -Destination $desk -Force
    } else {
        Remove-ShortcutIfExists $desk
    }
    if ($progPresent) {
        $src = Join-Path $dir 'Programs-Zola.lnk'
        $d = Split-Path -Parent $prog
        if (-not (Test-Path -LiteralPath $d)) { New-Item -ItemType Directory -Force -Path $d | Out-Null }
        Copy-Item -LiteralPath $src -Destination $prog -Force
    } else {
        Remove-ShortcutIfExists $prog
    }
    return @{
        desktop_sha_expected  = $deskSha
        programs_sha_expected = $progSha
        desktop_present       = $deskPresent
        programs_present      = $progPresent
    }
}

function Test-ShortcutHashesMatch {
    param(
        [Parameter(Mandatory)]$Meta,
        [Parameter(Mandatory)][string]$DesktopDir,
        [Parameter(Mandatory)][string]$ProgramsDir
    )
    $desk = Get-DesktopShortcutPath -DesktopDir $DesktopDir
    $prog = Get-ProgramsShortcutPath -ProgramsDir $ProgramsDir
    $deskPresent = [bool]$Meta.desktop_present
    $progPresent = [bool]$Meta.programs_present
    if ($deskPresent) {
        if (-not (Test-Path -LiteralPath $desk)) { return $false }
        if ((Get-FileSha256Hex $desk) -ne $Meta.desktop_sha_expected) { return $false }
    } else {
        if (Test-Path -LiteralPath $desk) { return $false }
    }
    if ($progPresent) {
        if (-not (Test-Path -LiteralPath $prog)) { return $false }
        if ((Get-FileSha256Hex $prog) -ne $Meta.programs_sha_expected) { return $false }
    } else {
        if (Test-Path -LiteralPath $prog) { return $false }
    }
    return $true
}

function ConvertTo-HashStringMap {
    param($Object)
    $map = @{}
    if ($null -eq $Object) { return $map }
    if ($Object -is [System.Collections.IDictionary]) {
        foreach ($k in @($Object.Keys)) { $map["$k"] = "$($Object[$k])" }
    } else {
        foreach ($p in $Object.PSObject.Properties) { $map[$p.Name] = "$($p.Value)" }
    }
    return $map
}

function Normalize-StringList {
    param($Value)
    if ($null -eq $Value) { return [string[]]@() }
    if ($Value -is [string]) { return [string[]]@($Value) }
    # Empty PSCustomObject from legacy ConvertTo-Json of empty ArrayList → treat as empty list
    if ($Value -is [PSCustomObject] -and @($Value.PSObject.Properties).Count -eq 0) {
        return [string[]]@()
    }
    if ($Value -is [System.Collections.IDictionary] -and $Value.Count -eq 0) {
        return [string[]]@()
    }
    $list = New-Object System.Collections.Generic.List[string]
    foreach ($i in @($Value)) {
        if ($null -eq $i) { continue }
        if ($i -is [PSCustomObject] -and @($i.PSObject.Properties).Count -eq 0) { continue }
        $list.Add("$i") | Out-Null
    }
    return [string[]]@($list.ToArray())
}

function Test-StringListsEqualSorted {
    param($A, $B)
    $sa = @(Normalize-StringList $A | Sort-Object)
    $sb = @(Normalize-StringList $B | Sort-Object)
    if ($sa.Count -ne $sb.Count) { return $false }
    for ($i = 0; $i -lt $sa.Count; $i++) {
        if ($sa[$i] -ne $sb[$i]) { return $false }
    }
    return $true
}

function Test-PluginDiffMatchesPrepare {
    param(
        [Parameter(Mandatory)]$LiveDiff,
        [Parameter(Mandatory)]$PrepareDiff
    )
    $prepAdded = @()
    $prepRemoved = @()
    $prepChanged = @()
    if ($null -ne $PrepareDiff) {
        $names = @($PrepareDiff.PSObject.Properties | ForEach-Object { $_.Name })
        if ($names -contains 'added') { $prepAdded = Normalize-StringList $PrepareDiff.added }
        if ($names -contains 'removed') { $prepRemoved = Normalize-StringList $PrepareDiff.removed }
        if ($names -contains 'changed') { $prepChanged = Normalize-StringList $PrepareDiff.changed }
    }
    return (
        (Test-StringListsEqualSorted -A $LiveDiff.Added -B $prepAdded) -and
        (Test-StringListsEqualSorted -A $LiveDiff.Removed -B $prepRemoved) -and
        (Test-StringListsEqualSorted -A $LiveDiff.Changed -B $prepChanged)
    )
}

function Invoke-ProfileBackup {
    param(
        [Parameter(Mandatory)][string]$BackupDir,
        [Parameter(Mandatory)][string]$ProfileRoot,
        [Parameter(Mandatory)][string]$HermesRoot,
        [Parameter(Mandatory)][string]$StableRoot,
        [Parameter(Mandatory)][string]$DesktopDir,
        [Parameter(Mandatory)][string]$ProgramsDir,
        [Parameter(Mandatory)]$Outgoing,
        [Parameter(Mandatory)]$Incoming,
        [switch]$StopOnIntegrityFail
    )
    New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
    $filesMeta = New-Object System.Collections.Generic.List[object]
    $dbMeta = New-Object System.Collections.Generic.List[object]
    $profileFiles = Get-ProfileFilesForBackup -ProfileRoot $ProfileRoot
    foreach ($f in $profileFiles) {
        $dst = Join-Path $BackupDir $f.RelPath
        $dstDir = Split-Path -Parent $dst
        if (-not (Test-Path -LiteralPath $dstDir)) {
            New-Item -ItemType Directory -Force -Path $dstDir | Out-Null
        }
        if ($f.IsDatabase) {
            $r = Invoke-SqliteTool -HermesRoot $HermesRoot -Args @('backup', $f.FullName, $dst)
            if ($r.ExitCode -ne 0) { throw "sqlite backup failed for $($f.RelPath): $($r.Output)" }
            $ir = Invoke-SqliteTool -HermesRoot $HermesRoot -Args @('integrity', $dst)
            $integrityOk = ($ir.Output -match 'status=OK')
            if ($StopOnIntegrityFail -and -not $integrityOk) {
                throw "sqlite integrity FAIL for $($f.RelPath) (stop before live change)"
            }
            $vr = Invoke-SqliteTool -HermesRoot $HermesRoot -Args @('user_version', $dst)
            $ver = 0
            if ($vr.Output -match 'user_version=(\d+)') { $ver = [int]$Matches[1] }
            $dbMeta.Add(@{
                path           = $f.RelNorm
                schema_version = $ver
                integrity      = $(if ($integrityOk) { 'OK' } else { 'FAIL' })
                sha256         = (Get-FileSha256Hex $dst)
                size           = (Get-Item -LiteralPath $dst).Length
            }) | Out-Null
            $filesMeta.Add(@{
                path   = $f.RelNorm
                size   = (Get-Item -LiteralPath $dst).Length
                sha256 = (Get-FileSha256Hex $dst)
                kind   = 'database'
            }) | Out-Null
        } else {
            Copy-Item -LiteralPath $f.FullName -Destination $dst -Force
            $filesMeta.Add(@{
                path   = $f.RelNorm
                size   = $f.Length
                sha256 = (Get-FileSha256Hex $dst)
                kind   = $(if ($f.IsCredential) { 'credential' } else { 'file' })
            }) | Out-Null
        }
    }

    $pluginSnap = Join-Path $BackupDir '_plugin_snapshot'
    New-Item -ItemType Directory -Force -Path $pluginSnap | Out-Null
    $liveMap = Get-LivePluginHashMap -ProfileRoot $ProfileRoot
    foreach ($rel in $liveMap.Keys) {
        $src = Join-Path $ProfileRoot ($rel.Replace('/', '\'))
        $dst = Join-Path $pluginSnap ($rel.Replace('/', '\'))
        $d = Split-Path -Parent $dst
        if (-not (Test-Path -LiteralPath $d)) { New-Item -ItemType Directory -Force -Path $d | Out-Null }
        Copy-Item -LiteralPath $src -Destination $dst -Force
    }

    $hermes = Get-HermesStateDigest -HermesRoot $HermesRoot
    $configPath = Join-Path $ProfileRoot 'config.yaml'
    $configSha = if (Test-Path -LiteralPath $configPath) { Get-FileSha256Hex $configPath } else { $null }

    $liveHashTable = @{}
    foreach ($k in @($liveMap.Keys)) { $liveHashTable["$k"] = "$($liveMap[$k])" }

    $shortcutMeta = Save-ShortcutBytesBefore -BackupDir $BackupDir -DesktopDir $DesktopDir -ProgramsDir $ProgramsDir

    $index = @{
        outgoing             = $Outgoing
        incoming             = $Incoming
        hermes               = $hermes
        config_yaml_sha256   = $configSha
        live_plugin_hashes   = $liveHashTable
        plugin_snapshot_dir  = '_plugin_snapshot'
        files                = @($filesMeta.ToArray())
        databases            = @($dbMeta.ToArray())
        shortcuts_before     = $shortcutMeta
        current_txt_before   = $(if (Test-Path -LiteralPath (Join-Path $StableRoot 'current.txt')) {
                (Get-Content -LiteralPath (Join-Path $StableRoot 'current.txt') -Raw).Trim()
            } else { $null })
    }
    Write-JsonFile -Object $index -Path (Join-Path $BackupDir 'backup-index.json')
    return $index
}

function Test-IsSqliteDatabaseFile {
    param([Parameter(Mandatory)][string]$Path)
    # PROC1-STABLE: identify DB by 16-byte header; skip credentials — Claude review
    $name = [IO.Path]::GetFileName($Path)
    if ($name -match '(-wal|-shm|-journal)$') { return $false }
    $relGuess = $Path # caller filters credentials by rel
    try {
        $fs = [IO.File]::Open($Path, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite)
        try {
            $buf = New-Object byte[] 16
            $read = $fs.Read($buf, 0, 16)
            if ($read -lt 16) { return $false }
            for ($i = 0; $i -lt 16; $i++) {
                if ($buf[$i] -ne $script:SqliteHeader[$i]) { return $false }
            }
            return $true
        } finally {
            $fs.Dispose()
        }
    } catch {
        return $false
    }
}

function Get-ProfileFilesForBackup {
    param([Parameter(Mandatory)][string]$ProfileRoot)
    $root = Resolve-FullPath $ProfileRoot
    $files = New-Object System.Collections.Generic.List[object]
    Get-ChildItem -LiteralPath $root -Recurse -Force -File -ErrorAction SilentlyContinue | ForEach-Object {
        $rel = $_.FullName.Substring($root.Length).TrimStart('\')
        $relNorm = $rel.Replace('\', '/')
        if ($relNorm -match '^(logs|cache)(/|$)') { return }
        $name = $_.Name
        if ($name -match '(-wal|-shm|-journal)$') { return }
        $isCred = Test-IsCredentialRelPath $relNorm
        $isDb = $false
        if (-not $isCred) {
            $isDb = Test-IsSqliteDatabaseFile $_.FullName
        }
        $files.Add([pscustomobject]@{
            FullName     = $_.FullName
            RelPath      = $rel
            RelNorm      = $relNorm
            Length       = $_.Length
            IsCredential = $isCred
            IsDatabase   = $isDb
        }) | Out-Null
    }
    return $files
}

function Invoke-SqliteTool {
    param(
        [Parameter(Mandatory)][string]$HermesRoot,
        [Parameter(Mandatory)][string[]]$Args
    )
    $py = Join-Path $HermesRoot '.venv\Scripts\python.exe'
    $tool = Join-Path (Get-StableModuleRoot) 'sqlite_tool.py'
    if (-not (Test-Path -LiteralPath $py)) { throw "Hermes venv python missing: $py" }
    # Native stderr becomes ErrorRecords under $ErrorActionPreference Stop — capture without throwing
    $prevEa = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $out = & $py $tool @Args 2>&1
        $code = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $prevEa
    }
    $text = ($out | ForEach-Object { "$_" }) -join "`n"
    return [pscustomobject]@{ ExitCode = $code; Output = $text }
}

function Get-DigestOfText {
    param([string]$Text)
    if ($null -eq $Text) { $Text = '' }
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Text)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        return ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '').ToLowerInvariant()
    } finally {
        $sha.Dispose()
    }
}

# PROC1-ID: digest algorithm versions recorded in the stable manifest — PROC1-D13
$script:DigestAlgoLocalEditV2 = 'v2-content'
$script:DigestAlgoPipFreezeV1 = 'v1-pip-freeze' # script golden / legacy only
$script:DigestAlgoPipFreezeV2 = 'v2-pip-freeze-clean'
$script:DigestAlgoLocalEditV1 = 'v1-porcelain' # script golden / legacy only

function Get-PluginCompareRulesObject {
    # PROC1-ID: one authority — Switch embeds this in the manifest for the client — PROC1-D13
    [ordered]@{
        maps = @(
            foreach ($m in $script:PluginMaps) {
                [ordered]@{ repo = [string]$m.Repo; live_rel = ([string]$m.LiveRel).Replace('\', '/') }
            }
        )
        structural_excludes = @('tests/', '__pycache__/', '*.pyc')
        named_excludes      = @($script:NamedPluginExcludes)
        tts_rel             = 'zola-tts/deepgram_tts.py'
    }
}

function Get-DigestAlgorithmsObject {
    [ordered]@{
        hermes_local_edit = $script:DigestAlgoLocalEditV2
        pip_freeze        = $script:DigestAlgoPipFreezeV2
    }
}

function Test-OmitPythonEnvName {
    param([Parameter(Mandatory)][string]$Name)
    if ($Name -eq 'PYTHONPATH' -or $Name -eq 'PYTHONHOME' -or $Name -eq 'PYTHONSTARTUP' -or
        $Name -eq 'PYTHONUSERBASE' -or $Name -eq 'VIRTUAL_ENV' -or $Name -eq 'PYTHONNOUSERSITE') {
        return $true
    }
    return $Name.StartsWith('PIP_', [StringComparison]::OrdinalIgnoreCase)
}

function Invoke-ExternalTextCapture {
    # PROC1-ID: fail closed — nonzero exit / missing exe is not hashed as empty — PROC1-D13
    # Phase 6b: optional WD + PythonClean/GitClean env (match HermesDigests) — PROC1-D13
    param(
        [Parameter(Mandatory)][string]$FilePath,
        [string[]]$ArgumentList,
        [int]$TimeoutMs = 30000,
        [string]$WorkingDirectory,
        [ValidateSet('None', 'PythonClean', 'GitClean')][string]$EnvironmentProfile = 'None'
    )
    if (-not (Test-Path -LiteralPath $FilePath)) {
        return [pscustomobject]@{ Ok = $false; Reason = "missing:$FilePath"; Text = $null; ExitCode = -1 }
    }
    $utf8 = New-Object System.Text.UTF8Encoding $false
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $FilePath
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true
    $psi.StandardOutputEncoding = $utf8
    $psi.StandardErrorEncoding = $utf8
    if ($WorkingDirectory) { $psi.WorkingDirectory = $WorkingDirectory }
    # PS 5.1: ArgumentList collection may be unavailable — quote into Arguments string
    $psi.Arguments = @($ArgumentList | ForEach-Object {
            $a = "$_"
            if ($a -match '[\s"]') { '"' + ($a.Replace('"', '\"')) + '"' } else { $a }
        }) -join ' '

    if ($EnvironmentProfile -ne 'None') {
        $keep = New-Object System.Collections.Generic.List[object]
        foreach ($entry in [System.Environment]::GetEnvironmentVariables().GetEnumerator()) {
            $k = [string]$entry.Key
            if ($EnvironmentProfile -eq 'PythonClean' -and (Test-OmitPythonEnvName -Name $k)) { continue }
            if ($EnvironmentProfile -eq 'GitClean' -and $k.StartsWith('GIT_', [StringComparison]::OrdinalIgnoreCase)) { continue }
            $keep.Add([pscustomobject]@{ K = $k; V = [string]$entry.Value }) | Out-Null
        }
        $psi.EnvironmentVariables.Clear()
        foreach ($kv in $keep) { $psi.EnvironmentVariables[$kv.K] = $kv.V }
        if ($EnvironmentProfile -eq 'PythonClean') { $psi.EnvironmentVariables['PYTHONUTF8'] = '1' }
    }

    $p = $null
    try {
        $p = New-Object System.Diagnostics.Process
        $p.StartInfo = $psi
        if (-not $p.Start()) {
            return [pscustomobject]@{ Ok = $false; Reason = 'start_failed'; Text = $null; ExitCode = -1 }
        }
        $stdout = $p.StandardOutput.ReadToEnd()
        $null = $p.StandardError.ReadToEnd()
        if (-not $p.WaitForExit($TimeoutMs)) {
            try { $p.Kill() } catch { }
            return [pscustomobject]@{ Ok = $false; Reason = "timeout:$TimeoutMs"; Text = $null; ExitCode = -1 }
        }
        $code = [int]$p.ExitCode
        if ($code -ne 0) {
            return [pscustomobject]@{ Ok = $false; Reason = "exit:$code"; Text = $null; ExitCode = $code }
        }
        return [pscustomobject]@{ Ok = $true; Reason = $null; Text = $stdout; ExitCode = 0 }
    } finally {
        if ($null -ne $p) { $p.Dispose() }
    }
}

function ConvertTo-V1JoinedText {
    # PROC1-ID Phase 4c: match proc1-stable `(cmd output) -join "`n"` (no trailing LF) — PROC1-D13
    # Fail-closed capture keeps the process trailing LF; stripping it is part of v1, not a new algorithm.
    param([string]$Text)
    if ($null -eq $Text) { return '' }
    $normalized = ($Text -replace "`r`n", "`n") -replace "`r", "`n"
    return $normalized.TrimEnd("`n")
}

function Get-HermesLocalEditDigestV1 {
    # Legacy porcelain-text digest — must match proc1-stable Get-HermesStateDigest local_edit
    param([Parameter(Mandatory)][string]$HermesRoot)
    $gitCmd = Get-Command git -ErrorAction SilentlyContinue
    $git = if ($gitCmd) { $gitCmd.Source } else { $null }
    if (-not $git) { return [pscustomobject]@{ Ok = $false; Reason = 'missing:git'; Digest = $null } }
    $cap = Invoke-ExternalTextCapture -FilePath $git -ArgumentList @('-C', $HermesRoot, 'status', '--porcelain')
    if (-not $cap.Ok) { return [pscustomobject]@{ Ok = $false; Reason = $cap.Reason; Digest = $null } }
    $joined = ConvertTo-V1JoinedText -Text $cap.Text
    return [pscustomobject]@{ Ok = $true; Reason = $null; Digest = (Get-DigestOfText $joined); Text = $joined }
}

function Get-HermesLocalEditDigestV2 {
    # PROC1-ID: content-aware local-edit digest; Phase 6b WD=hermesRoot, strip GIT_* — PROC1-D13
    param([Parameter(Mandatory)][string]$HermesRoot)
    $gitCmd = Get-Command git -ErrorAction SilentlyContinue
    $git = if ($gitCmd) { $gitCmd.Source } else { $null }
    if (-not $git) { return [pscustomobject]@{ Ok = $false; Reason = 'missing:git'; Digest = $null } }
    $cap = Invoke-ExternalTextCapture -FilePath $git -ArgumentList @(
        '-C', $HermesRoot, 'status', '--porcelain=v1', '-z', '--untracked-files=all'
    ) -WorkingDirectory $HermesRoot -EnvironmentProfile GitClean -TimeoutMs 30000
    if (-not $cap.Ok) { return [pscustomobject]@{ Ok = $false; Reason = $cap.Reason; Digest = $null } }
    $raw = $cap.Text
    $entries = New-Object System.Collections.Generic.List[string]
    if (-not [string]::IsNullOrEmpty($raw)) {
        $parts = $raw.Split([char]0)
        $i = 0
        while ($i -lt $parts.Length) {
            $chunk = $parts[$i]
            if ([string]::IsNullOrEmpty($chunk)) { $i++; continue }
            # XY PATH or for renames XY ORIG\0NEW (porcelain -z)
            if ($chunk.Length -lt 3) { $i++; continue }
            $code = $chunk.Substring(0, 2)
            $pathPart = $chunk.Substring(3)
            $path = $pathPart
            if ($code -match 'R|C') {
                # next nul field is the destination path
                $i++
                if ($i -lt $parts.Length -and -not [string]::IsNullOrEmpty($parts[$i])) {
                    $path = $parts[$i]
                }
            }
            $full = Join-Path $HermesRoot ($path -replace '/', '\')
            $payload = 'deleted'
            if (Test-Path -LiteralPath $full -PathType Leaf) {
                $payload = Get-FileSha256Hex -Path $full
            }
            $entries.Add(('{0}|{1}|{2}' -f $code, ($path -replace '\\', '/'), $payload)) | Out-Null
            $i++
        }
    }
    $sorted = @($entries | Sort-Object)
    $text = ($sorted -join "`n") + $(if ($sorted.Count -gt 0) { "`n" } else { '' })
    return [pscustomobject]@{ Ok = $true; Reason = $null; Digest = (Get-DigestOfText $text) }
}

function Get-PipFreezeDigest {
    # PROC1-ID Phase 4c: v1-pip-freeze (legacy / golden only; inherits ambient env) — PROC1-D13
    param([Parameter(Mandatory)][string]$HermesRoot)
    $py = Join-Path $HermesRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $py)) {
        return [pscustomobject]@{ Ok = $false; Reason = "missing:$py"; Digest = $null; Text = $null }
    }
    $cap = Invoke-ExternalTextCapture -FilePath $py -ArgumentList @('-m', 'pip', 'freeze') -TimeoutMs 60000
    if (-not $cap.Ok) { return [pscustomobject]@{ Ok = $false; Reason = $cap.Reason; Digest = $null; Text = $null } }
    $joined = ConvertTo-V1JoinedText -Text $cap.Text
    return [pscustomobject]@{ Ok = $true; Reason = $null; Digest = (Get-DigestOfText $joined); Text = $joined }
}

function Get-PipFreezeDigestV2 {
    # PROC1-ID Phase 6b: v2-pip-freeze-clean — PROC1-D13
    param([Parameter(Mandatory)][string]$HermesRoot)
    $py = Join-Path $HermesRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $py)) {
        return [pscustomobject]@{ Ok = $false; Reason = "missing:$py"; Digest = $null; Text = $null; RawText = $null }
    }
    $cap = Invoke-ExternalTextCapture -FilePath $py -ArgumentList @('-m', 'pip', 'freeze') `
        -WorkingDirectory $HermesRoot -EnvironmentProfile PythonClean -TimeoutMs 60000
    if (-not $cap.Ok) {
        return [pscustomobject]@{ Ok = $false; Reason = $cap.Reason; Digest = $null; Text = $null; RawText = $null }
    }
    $joined = ConvertTo-V1JoinedText -Text $cap.Text
    return [pscustomobject]@{
        Ok = $true; Reason = $null
        Digest = (Get-DigestOfText $joined)
        Text = $joined
        RawText = $cap.Text
    }
}

function Get-HermesStateDigest {
    # PROC1-ID: fail-closed digests; v2-content + v2-pip-freeze-clean — PROC1-D13
    param(
        [Parameter(Mandatory)][string]$HermesRoot,
        [string]$LocalEditAlgorithm = $script:DigestAlgoLocalEditV2
    )
    $gitCmd = Get-Command git -ErrorAction SilentlyContinue
    $git = if ($gitCmd) { $gitCmd.Source } else { $null }
    $headCap = $null
    if ($git) {
        $headCap = Invoke-ExternalTextCapture -FilePath $git -ArgumentList @('-C', $HermesRoot, 'rev-parse', 'HEAD') `
            -WorkingDirectory $HermesRoot -EnvironmentProfile GitClean
    } else {
        $headCap = [pscustomobject]@{ Ok = $false; Reason = 'missing:git'; Text = $null }
    }
    if (-not $headCap.Ok) {
        throw "Hermes digest not completed (head): $($headCap.Reason)"
    }
    $head = ($headCap.Text -split "`r?`n")[0].Trim()

    if ($LocalEditAlgorithm -eq $script:DigestAlgoLocalEditV2) {
        $local = Get-HermesLocalEditDigestV2 -HermesRoot $HermesRoot
    } elseif ($LocalEditAlgorithm -eq $script:DigestAlgoLocalEditV1) {
        $local = Get-HermesLocalEditDigestV1 -HermesRoot $HermesRoot
    } else {
        throw "Hermes digest not completed (local_edit): unknown algorithm $LocalEditAlgorithm"
    }
    if (-not $local.Ok) {
        throw "Hermes digest not completed (local_edit): $($local.Reason)"
    }
    $pip = Get-PipFreezeDigestV2 -HermesRoot $HermesRoot
    if (-not $pip.Ok) {
        throw "Hermes digest not completed (pip_freeze): $($pip.Reason)"
    }
    [pscustomobject]@{
        head               = $head
        local_edit_digest  = $local.Digest
        pip_freeze_digest  = $pip.Digest
        pip_freeze_text    = $pip.Text
        local_edit_algo    = $LocalEditAlgorithm
        pip_freeze_algo    = $script:DigestAlgoPipFreezeV2
    }
}

function ConvertTo-JsonFriendly {
    param($Object)
    if ($null -eq $Object) { return $null }
    # Strings first — they are IEnumerable of chars
    if ($Object -is [string]) { return $Object }
    if ($Object -is [bool] -or $Object -is [int] -or $Object -is [long] -or $Object -is [double] -or $Object -is [decimal]) {
        return $Object
    }
    if ($Object -is [System.Collections.IDictionary]) {
        # Plain Hashtable (not OrderedDictionary) for ConvertTo-Json
        $h = New-Object System.Collections.Hashtable
        foreach ($k in @($Object.Keys)) {
            $h[[string]$k] = (ConvertTo-JsonFriendly $Object[$k])
        }
        return $h
    }
    if ($Object -is [PSCustomObject]) {
        $h = New-Object System.Collections.Hashtable
        foreach ($p in $Object.PSObject.Properties) {
            # Skip NoteProperty only; ignore parameterized/script properties
            if ($p.MemberType -ne 'NoteProperty') { continue }
            $h[[string]$p.Name] = (ConvertTo-JsonFriendly $p.Value)
        }
        return $h
    }
    if ($Object -is [System.Collections.IEnumerable]) {
        # ArrayList + unary comma: empty collections must not collapse to $null on return
        $list = New-Object System.Collections.ArrayList
        foreach ($item in $Object) { [void]$list.Add((ConvertTo-JsonFriendly $item)) }
        return , $list
    }
    # Fallback: stringify unknown objects rather than serialize PS adapters
    return "$Object"
}

function Escape-JsonString {
    param([string]$Text)
    if ($null -eq $Text) { return '' }
    $sb = New-Object System.Text.StringBuilder
    foreach ($ch in $Text.ToCharArray()) {
        switch ($ch) {
            '"' { [void]$sb.Append('\"') }
            '\' { [void]$sb.Append('\\') }
            "`b" { [void]$sb.Append('\b') }
            "`f" { [void]$sb.Append('\f') }
            "`n" { [void]$sb.Append('\n') }
            "`r" { [void]$sb.Append('\r') }
            "`t" { [void]$sb.Append('\t') }
            default {
                $code = [int]$ch
                if ($code -lt 0x20) {
                    [void]$sb.AppendFormat('\u{0:x4}', $code)
                } else {
                    [void]$sb.Append($ch)
                }
            }
        }
    }
    return $sb.ToString()
}

function ConvertTo-JsonText {
    param($Object)
    # Hand-rolled JSON for PS 5.1 — ConvertTo-Json corrupts single-element string arrays
    # into {"Length":N} and empty ArrayList into {}.
    if ($null -eq $Object) { return 'null' }
    if ($Object -is [bool]) { if ($Object) { return 'true' } else { return 'false' } }
    if ($Object -is [byte] -or $Object -is [int16] -or $Object -is [uint16] -or
        $Object -is [int] -or $Object -is [uint32] -or $Object -is [long] -or
        $Object -is [uint64] -or $Object -is [decimal] -or $Object -is [double] -or
        $Object -is [float]) {
        return (($Object).ToString([System.Globalization.CultureInfo]::InvariantCulture))
    }
    if ($Object -is [string]) { return ('"' + (Escape-JsonString $Object) + '"') }
    if ($Object -is [System.Collections.IDictionary]) {
        $parts = New-Object System.Collections.Generic.List[string]
        foreach ($k in @($Object.Keys)) {
            $parts.Add(('"' + (Escape-JsonString "$k") + '":' + (ConvertTo-JsonText $Object[$k]))) | Out-Null
        }
        return ('{' + ($parts -join ',') + '}')
    }
    if ($Object -is [System.Collections.IEnumerable]) {
        $parts = New-Object System.Collections.Generic.List[string]
        foreach ($item in $Object) {
            $parts.Add((ConvertTo-JsonText $item)) | Out-Null
        }
        return ('[' + ($parts -join ',') + ']')
    }
    return ('"' + (Escape-JsonString "$Object") + '"')
}

function Write-JsonFile {
    param(
        [Parameter(Mandatory)]$Object,
        [Parameter(Mandatory)][string]$Path
    )
    $dir = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
    $friendly = ConvertTo-JsonFriendly $Object
    $json = ConvertTo-JsonText $friendly
    [IO.File]::WriteAllText($Path, $json)
}

function Read-JsonFile {
    param([Parameter(Mandatory)][string]$Path)
    $raw = [IO.File]::ReadAllText($Path)
    return $raw | ConvertFrom-Json
}

Export-ModuleMember -Function @(
    'Resolve-FullPath', 'Get-DefaultDesktopDir', 'Get-DefaultProgramsDir',
    'Get-DesktopShortcutPath', 'Get-ProgramsShortcutPath', 'Get-LiveRootSet',
    'Test-PathUnderOrEqual', 'Assert-TestModeSafeRoot', 'Get-FileSha256Hex',
    'Get-DirectoryFileHashMap', 'Get-ClientBuildHash', 'Get-ExpectedWinUiResourceRels', 'Assert-StagingHasWinUiResources', 'Test-PluginPathExcluded',
    'Get-ComparisonFilesFromRepoTree', 'Copy-ComparisonSetToPromotions',
    'Get-PromotionsPluginHashMap', 'Get-LivePluginHashMap', 'Compare-PluginSets',
    'Test-MutexHeld', 'Get-ZolaRunningStatus', 'Assert-ZolaNotRunning',
    'Get-ObservedPreStableLaunch', 'New-ShortcutZola', 'Remove-ShortcutIfExists',
    'Get-ShortcutTargetOrNull', 'Test-IsCredentialRelPath', 'Get-CredentialListDescription',
    'Get-PromotionScriptsState', 'Save-ShortcutBytesBefore', 'Restore-ShortcutBytes',
    'Test-ShortcutHashesMatch', 'ConvertTo-HashStringMap', 'Normalize-StringList',
    'Test-StringListsEqualSorted', 'Test-PluginDiffMatchesPrepare', 'Invoke-ProfileBackup',
    'Test-IsSqliteDatabaseFile', 'Get-ProfileFilesForBackup', 'Invoke-SqliteTool',
    'Get-DigestOfText', 'ConvertTo-V1JoinedText', 'Get-HermesStateDigest', 'Get-HermesLocalEditDigestV1', 'Get-HermesLocalEditDigestV2',
    'Get-PipFreezeDigest', 'Get-PipFreezeDigestV2', 'Get-PluginCompareRulesObject', 'Get-DigestAlgorithmsObject',
    'Invoke-ExternalTextCapture', 'Write-JsonFile', 'Read-JsonFile'
) -Variable DefaultStableRoot, DefaultProfileRoot, DefaultClientDataRoot, DefaultHermesRoot, DefaultLiveCheckout, ShortcutName, NamedPluginExcludes, PluginMaps, MutexPhone, MutexWatcher, DigestAlgoLocalEditV2, DigestAlgoPipFreezeV1, DigestAlgoPipFreezeV2, DigestAlgoLocalEditV1
