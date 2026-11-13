# PROC1-DEV: create and check the dev profile without touching the live one — PROC1-D4/D13/D14
#Requires -Version 5.1
Set-StrictMode -Version Latest

$script:Utf8 = New-Object System.Text.UTF8Encoding $false
$script:Section = [char]0x00A7
$script:UserSeed = "[identity] The user's name is Casey Quinn.`n$($script:Section)`n[home] Casey lives in the made-up town of Northglass.`n"
$script:MemorySeed = "[person] Jordan Hale is Casey's invented neighbour and keeps bees.`n$($script:Section)`n[fact] Casey's favourite colour is slate.`n$($script:Section)`n[project] The demo codename is Paper Kite.`n"
$script:MarkerPattern = '(?i)profiles([\\/])zola(?![A-Za-z0-9_-])|(?<![A-Za-z0-9_-])ZolaClient(?![A-Za-z0-9_-])'
$script:SharedKeyPattern = '(?i)(?<![A-Za-z0-9_-])ZolaClient[\\/]secrets[\\/]deepgram_api_key$'
$script:SharedKeyToken = '(?i)(?<![A-Za-z0-9_-])ZolaClient[\\/]secrets[\\/]deepgram_api_key'

function Get-DevRoots {
    param([Parameter(Mandatory)][string]$LocalAppData)
    $local = [IO.Path]::GetFullPath($LocalAppData).TrimEnd('\')
    [pscustomobject]@{
        Local            = $local
        NativeHermes     = Join-Path $local 'hermes'
        LiveProfile      = Join-Path $local 'hermes\profiles\zola'
        OldDevProfile    = Join-Path $local 'hermes\profiles\zola-dev'
        DevProfile       = Join-Path $local 'hermes-dev\profiles\zola-dev'
        LiveClient       = Join-Path $local 'ZolaClient'
        DevClient        = Join-Path $local 'ZolaClient-dev'
        HermesRootAuth   = Join-Path $local 'hermes-dev\auth.json'
    }
}

function Test-PathUnder {
    param([string]$Path, [string]$Root)
    if ([string]::IsNullOrWhiteSpace($Path) -or [string]::IsNullOrWhiteSpace($Root)) { return $false }
    $full = [IO.Path]::GetFullPath($Path).TrimEnd('\')
    $base = [IO.Path]::GetFullPath($Root).TrimEnd('\')
    if ($full.Equals($base, [StringComparison]::OrdinalIgnoreCase)) { return $true }
    return $full.StartsWith($base + '\', [StringComparison]::OrdinalIgnoreCase)
}

function Resolve-ExistingFinal {
    param([Parameter(Mandatory)][string]$Path)
    $current = [IO.Path]::GetFullPath($Path)
    for ($i = 0; $i -lt 32; $i++) {
        if (-not (Test-Path -LiteralPath $current)) { return $current.TrimEnd('\') }
        $item = Get-Item -LiteralPath $current -Force
        if (-not ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) { return $current.TrimEnd('\') }
        $target = $item.Target
        if ($target -is [System.Array]) { $target = $target | Select-Object -First 1 }
        if ([string]::IsNullOrWhiteSpace([string]$target)) { return $current.TrimEnd('\') }
        if (-not [IO.Path]::IsPathRooted([string]$target)) {
            $current = [IO.Path]::GetFullPath((Join-Path (Split-Path -Parent $current) ([string]$target)))
        } else {
            $current = [IO.Path]::GetFullPath([string]$target)
        }
    }
    return $current.TrimEnd('\')
}

function Resolve-FinalPath {
    param([Parameter(Mandatory)][string]$Path)
    $full = [IO.Path]::GetFullPath($Path)
    $suffix = New-Object System.Collections.Generic.List[string]
    $cursor = $full
    while (-not (Test-Path -LiteralPath $cursor)) {
        $parent = Split-Path -Parent $cursor
        if ([string]::IsNullOrWhiteSpace($parent) -or $parent.Equals($cursor, [StringComparison]::OrdinalIgnoreCase)) {
            return $full.TrimEnd('\')
        }
        $suffix.Insert(0, (Split-Path -Leaf $cursor))
        $cursor = $parent
    }
    $resolved = Resolve-ExistingFinal $cursor
    foreach ($part in $suffix) {
        $resolved = Join-Path $resolved $part
    }
    return ([IO.Path]::GetFullPath($resolved)).TrimEnd('\')
}

function Test-SafeDevDestination {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Expected,
        [Parameter(Mandatory)][string]$LiveProfile,
        [Parameter(Mandatory)][string]$LiveClient,
        [Parameter(Mandatory)][string]$NativeHermes
    )
    $full = [IO.Path]::GetFullPath($Path).TrimEnd('\')
    $expectedFull = [IO.Path]::GetFullPath($Expected).TrimEnd('\')
    if (-not $full.Equals($expectedFull, [StringComparison]::OrdinalIgnoreCase)) { return $false }
    if (Test-PathUnder $full $LiveProfile) { return $false }
    if (Test-PathUnder $full $LiveClient) { return $false }
    if (Test-PathUnder $full $NativeHermes) { return $false }
    $final = Resolve-FinalPath $full
    if (Test-PathUnder $final $LiveProfile) { return $false }
    if (Test-PathUnder $final $LiveClient) { return $false }
    if (Test-PathUnder $final $NativeHermes) { return $false }
    if (Test-Path -LiteralPath $full) {
        $item = Get-Item -LiteralPath $full -Force
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { return $false }
    }
    return $true
}

function Test-ZolaClientOrServeRunning {
    param([scriptblock]$Probe)
    # PROC1-DEV: -Replace uses one probe so a test can answer without scanning the live machine — PROC1-D4
    if ($null -ne $Probe) {
        return [bool](& $Probe)
    }

    try {
        $opened = [Threading.Mutex]::OpenExisting('Local\ZolaClient')
        $opened.Dispose()
        return $true
    } catch [System.Threading.WaitHandleCannotBeOpenedException] {
    } catch {
        return $true
    }

    if (@(Get-Process -Name 'Zola.Client' -ErrorAction SilentlyContinue).Count -gt 0) {
        return $true
    }

    foreach ($proc in @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)) {
        $name = [string]$proc.Name
        $cmd = [string]$proc.CommandLine
        if ($name -match '^(?i)dotnet(\.exe)?$' -and $cmd -match 'Zola\.Client\.csproj') {
            return $true
        }
        if ($cmd -match '(?i)hermes_cli\.main' -and $cmd -match '(?i)(^|\s)serve(\s|$)') {
            return $true
        }
    }
    return $false
}

function Get-Sha256Hex {
    param([Parameter(Mandatory)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Convert-LiveMarkers {
    param([Parameter(Mandatory)][string]$Text)
    $updated = [regex]::Replace($Text, '(?i)(?<![A-Za-z0-9_-])hermes(?![A-Za-z0-9_-])([\\/])profiles([\\/])zola(?![A-Za-z0-9_-])', 'hermes-dev$1profiles$2zola-dev')
    $updated = [regex]::Replace($updated, '(?i)(?<![A-Za-z0-9_-])ZolaClient(?![A-Za-z0-9_-])', 'ZolaClient-dev')
    return [regex]::Replace($updated, '(?i)profiles([\\/])zola(?![A-Za-z0-9_-])', 'profiles$1zola-dev')
}

function Get-MarkerSpans {
    param([Parameter(Mandatory)][string]$Text)
    $regex = [regex]$script:MarkerPattern
    $raw = New-Object System.Collections.Generic.List[object]
    foreach ($match in $regex.Matches($Text)) {
        $start = $match.Index
        while ($start -gt 0) {
            $ch = $Text[$start - 1]
            if ([char]::IsWhiteSpace($ch) -or $ch -eq '"' -or $ch -eq "'") { break }
            $start--
        }
        $end = $match.Index + $match.Length
        while ($end -lt $Text.Length) {
            $ch = $Text[$end]
            if ([char]::IsWhiteSpace($ch) -or $ch -eq '"' -or $ch -eq "'") { break }
            $end++
        }
        $raw.Add([pscustomobject]@{ Start = $start; Length = ($end - $start) }) | Out-Null
    }
    $merged = New-Object System.Collections.Generic.List[object]
    foreach ($span in ($raw | Sort-Object Start)) {
        if ($merged.Count -eq 0) {
            $merged.Add($span) | Out-Null
            continue
        }
        $last = $merged[$merged.Count - 1]
        $lastEnd = $last.Start + $last.Length
        if ($span.Start -le $lastEnd) {
            $newEnd = [Math]::Max($lastEnd, $span.Start + $span.Length)
            $merged[$merged.Count - 1] = [pscustomobject]@{ Start = $last.Start; Length = ($newEnd - $last.Start) }
        } else {
            $merged.Add($span) | Out-Null
        }
    }
    return $merged.ToArray()
}

function Get-AbsoluteTokens {
    param([Parameter(Mandatory)][string]$Text)
    $regex = [regex]'(?i)(?:[A-Za-z]:[\\/]|%[A-Za-z0-9_]+%[\\/])[^\s"''<>|*?\r\n]+'
    $tokens = New-Object System.Collections.Generic.List[string]
    foreach ($match in $regex.Matches($Text)) {
        $token = $match.Value.TrimEnd('.', ',', ';', ')', ']', '}')
        if (-not [string]::IsNullOrWhiteSpace($token)) { $tokens.Add($token) | Out-Null }
    }
    return @($tokens)
}

function Update-DevConfigText {
    param(
        [Parameter(Mandatory)][string]$Text,
        [Parameter(Mandatory)][string]$LiveProfile,
        [Parameter(Mandatory)][string]$LiveClient
    )
    $unmapped = New-Object System.Collections.Generic.List[string]
    foreach ($token in (Get-AbsoluteTokens $Text)) {
        $expanded = [Environment]::ExpandEnvironmentVariables($token)
        try { $lexical = [IO.Path]::GetFullPath($expanded) } catch { continue }
        $final = Resolve-FinalPath $lexical
        $lexicalLive = (Test-PathUnder $lexical $LiveProfile) -or (Test-PathUnder $lexical $LiveClient)
        $finalLive = (Test-PathUnder $final $LiveProfile) -or (Test-PathUnder $final $LiveClient)
        if ($finalLive -and -not $lexicalLive) {
            $unmapped.Add($token) | Out-Null
        }
    }
    if ($unmapped.Count -gt 0) {
        return [pscustomobject]@{ Ok = $false; Text = $Text; Changes = @(); Unmapped = @($unmapped) }
    }

    $spans = @(Get-MarkerSpans $Text)
    $changes = New-Object System.Collections.Generic.List[object]
    $builder = New-Object System.Text.StringBuilder $Text
    for ($i = $spans.Count - 1; $i -ge 0; $i--) {
        $span = $spans[$i]
        $before = $Text.Substring([int]$span.Start, [int]$span.Length)
        if ($before -match $script:SharedKeyPattern) {
            $changes.Add([pscustomobject]@{ Before = $before; After = $before; Kept = 'kept (shared, D5)' }) | Out-Null
            continue
        }
        $after = Convert-LiveMarkers $before
        if ($after -eq $before) {
            $unmapped.Add($before) | Out-Null
            continue
        }
        $changes.Add([pscustomobject]@{ Before = $before; After = $after; Kept = '' }) | Out-Null
        [void]$builder.Remove($span.Start, $span.Length)
        [void]$builder.Insert($span.Start, $after)
    }
    if ($unmapped.Count -gt 0) {
        return [pscustomobject]@{ Ok = $false; Text = $Text; Changes = @(); Unmapped = @($unmapped) }
    }
    $updated = $builder.ToString()
    $scan = [regex]::Replace($updated, $script:SharedKeyToken, '')
    if ([regex]::IsMatch($scan, $script:MarkerPattern)) {
        return [pscustomobject]@{ Ok = $false; Text = $Text; Changes = @(); Unmapped = @('marker remains') }
    }
    $ordered = @($changes | Sort-Object { $_.Before })
    return [pscustomobject]@{ Ok = $true; Text = $updated; Changes = $ordered; Unmapped = @() }
}

function Remove-DevTree {
    param([Parameter(Mandatory)]$Roots)
    foreach ($path in @($Roots.DevProfile, $Roots.DevClient)) {
        if (-not (Test-SafeDevDestination -Path $path -Expected $(if ($path -eq $Roots.DevProfile) { $Roots.DevProfile } else { $Roots.DevClient }) -LiveProfile $Roots.LiveProfile -LiveClient $Roots.LiveClient -NativeHermes $Roots.NativeHermes)) {
            continue
        }
        if (Test-Path -LiteralPath $path) {
            Remove-Item -LiteralPath $path -Recurse -Force
        }
    }
}

function New-DevProfileTree {
    param(
        [string]$LocalAppData = $env:LOCALAPPDATA,
        [switch]$Replace,
        [scriptblock]$RunningProbe
    )
    $roots = Get-DevRoots $LocalAppData
    foreach ($pair in @(
            @{ Path = $roots.DevProfile; Expected = $roots.DevProfile },
            @{ Path = $roots.DevClient; Expected = $roots.DevClient }
        )) {
        if (-not (Test-SafeDevDestination -Path $pair.Path -Expected $pair.Expected -LiveProfile $roots.LiveProfile -LiveClient $roots.LiveClient -NativeHermes $roots.NativeHermes)) {
            return [pscustomobject]@{ Ok = $false; Reason = 'refusing: destination resolves into the native Hermes root or is not the dev folder'; Changes = @(); Copies = @() }
        }
    }
    $existed = (Test-Path -LiteralPath $roots.DevProfile) -or (Test-Path -LiteralPath $roots.DevClient)
    if ($existed -and -not $Replace) {
        return [pscustomobject]@{ Ok = $false; Reason = 'refusing: zola-dev already exists'; Changes = @(); Copies = @() }
    }
    if ($Replace -and $existed) {
        if (Test-ZolaClientOrServeRunning -Probe $RunningProbe) {
            return [pscustomobject]@{ Ok = $false; Reason = 'refusing: Zola is running'; Changes = @(); Copies = @() }
        }
        Remove-DevTree $roots
    }

    $configSrc = Join-Path $roots.LiveProfile 'config.yaml'
    $soulSrc = Join-Path $roots.LiveProfile 'SOUL.md'
    if (-not (Test-Path -LiteralPath $configSrc) -or -not (Test-Path -LiteralPath $soulSrc)) {
        return [pscustomobject]@{ Ok = $false; Reason = 'refusing: live config.yaml or SOUL.md is missing'; Changes = @(); Copies = @() }
    }

    New-Item -ItemType Directory -Force -Path $roots.DevProfile, (Join-Path $roots.DevProfile 'memories'), (Join-Path $roots.DevClient 'logs'), (Join-Path $roots.DevClient 'dumps'), (Join-Path $roots.DevClient 'debug'), (Join-Path $roots.DevClient 'secrets') | Out-Null
    $configDst = Join-Path $roots.DevProfile 'config.yaml'
    $soulDst = Join-Path $roots.DevProfile 'SOUL.md'
    [IO.File]::Copy($configSrc, $configDst, $true)
    [IO.File]::Copy($soulSrc, $soulDst, $true)
    $copies = @(
        [pscustomobject]@{ Name = 'config.yaml'; SourceHash = (Get-Sha256Hex $configSrc); DestHash = (Get-Sha256Hex $configDst) },
        [pscustomobject]@{ Name = 'SOUL.md'; SourceHash = (Get-Sha256Hex $soulSrc); DestHash = (Get-Sha256Hex $soulDst) }
    )

    $text = [IO.File]::ReadAllText($configDst)
    $rewritten = Update-DevConfigText -Text $text -LiveProfile $roots.LiveProfile -LiveClient $roots.LiveClient
    if (-not $rewritten.Ok) {
        Remove-DevTree $roots
        $which = (@($rewritten.Unmapped) | Select-Object -First 1)
        return [pscustomobject]@{ Ok = $false; Reason = "refusing: a live path in config.yaml could not be mapped: $which"; Changes = @(); Copies = @() }
    }
    if ($rewritten.Text -ne $text) {
        [IO.File]::WriteAllText($configDst, $rewritten.Text, $script:Utf8)
    }
    [IO.File]::WriteAllText((Join-Path $roots.DevProfile 'memories\USER.md'), $script:UserSeed, $script:Utf8)
    [IO.File]::WriteAllText((Join-Path $roots.DevProfile 'memories\MEMORY.md'), $script:MemorySeed, $script:Utf8)
    return [pscustomobject]@{ Ok = $true; Reason = ''; Changes = @($rewritten.Changes); Copies = $copies }
}

function Sync-DevPluginTree {
    param(
        [Parameter(Mandatory)][string]$From,
        [string]$LocalAppData = $env:LOCALAPPDATA,
        [switch]$Replace,
        [scriptblock]$RunningProbe
    )
    $roots = Get-DevRoots $LocalAppData
    if (-not (Test-SafeDevDestination -Path $roots.DevProfile -Expected $roots.DevProfile -LiveProfile $roots.LiveProfile -LiveClient $roots.LiveClient -NativeHermes $roots.NativeHermes)) {
        return [pscustomobject]@{ Ok = $false; Reason = 'refusing: destination resolves into the native Hermes root' }
    }
    $pluginsRoot = Join-Path $From 'hermes-plugins'
    if (-not (Test-Path -LiteralPath $pluginsRoot)) {
        return [pscustomobject]@{ Ok = $false; Reason = 'refusing: hermes-plugins was not found' }
    }
    $stable = Join-Path (Split-Path -Parent $PSScriptRoot) 'stable\StableCommon.psm1'
    Import-Module $stable -Force
    $files = Get-ComparisonFilesFromRepoTree -HermesPluginsRoot $pluginsRoot
    $selected = [ordered]@{}
    foreach ($key in @($files.Keys)) {
        if ($key -like 'plugins/zola_phone/*' -or $key -eq 'plugins/zola_phone') { continue }
        $selected[$key] = $files[$key]
    }
    if (-not $selected.Contains('zola-tts/deepgram_tts.py')) {
        return [pscustomobject]@{ Ok = $false; Reason = 'refusing: deepgram_tts.py was not in the comparison set' }
    }
    $destRoots = @(
        (Join-Path $roots.DevProfile 'plugins\zola_workspace'),
        (Join-Path $roots.DevProfile 'plugins\zola_memory'),
        (Join-Path $roots.DevProfile 'plugins\zola_tools'),
        (Join-Path $roots.DevProfile 'zola-tts')
    )
    $present = @($destRoots | Where-Object { Test-Path -LiteralPath $_ })
    if ($present.Count -gt 0 -and -not $Replace) {
        return [pscustomobject]@{ Ok = $false; Reason = 'refusing: dev plugins already exist' }
    }
    if ($Replace -and $present.Count -gt 0 -and (Test-ZolaClientOrServeRunning -Probe $RunningProbe)) {
        return [pscustomobject]@{ Ok = $false; Reason = 'refusing: Zola is running' }
    }
    foreach ($key in @($selected.Keys)) {
        $dest = Join-Path $roots.DevProfile ($key.Replace('/', '\'))
        $final = Resolve-FinalPath $dest
        if ((Test-PathUnder $final $roots.LiveProfile) -or (Test-PathUnder $final $roots.LiveClient) -or (Test-PathUnder $final $roots.NativeHermes)) {
            return [pscustomobject]@{ Ok = $false; Reason = 'refusing: a plugin destination resolves into the native Hermes root' }
        }
        $destDir = Split-Path -Parent $dest
        if (-not (Test-Path -LiteralPath $destDir)) {
            New-Item -ItemType Directory -Force -Path $destDir | Out-Null
        }
        Copy-Item -LiteralPath $selected[$key] -Destination $dest -Force
    }
    return [pscustomobject]@{ Ok = $true; Reason = ''; Copied = @($selected.Keys) }
}

function Test-FinishedProfileToken {
    param(
        [Parameter(Mandatory)][string]$CommandLine,
        [Parameter(Mandatory)][string]$ProfileName
    )
    $pattern = '(?i)(?:^|\s)(?:-p|--profile)(?:=|\s+)' + [regex]::Escape($ProfileName) + '(?:\s|$)'
    return [regex]::IsMatch($CommandLine, $pattern)
}

function Get-TreeHashMap {
    param([Parameter(Mandatory)][string]$Root)
    $map = [ordered]@{}
    if (-not (Test-Path -LiteralPath $Root)) { return $map }
    $base = [IO.Path]::GetFullPath($Root)
    Get-ChildItem -LiteralPath $Root -Recurse -File -Force | ForEach-Object {
        $rel = $_.FullName.Substring($base.Length).TrimStart('\').Replace('\', '/')
        $map[$rel] = (Get-Sha256Hex $_.FullName)
    }
    return $map
}

function Update-MovedProfilePrefix {
    param(
        [Parameter(Mandatory)][string]$Text,
        [Parameter(Mandatory)][string]$OldPrefix,
        [Parameter(Mandatory)][string]$NewPrefix
    )
    $updated = $Text
    $count = 0
    foreach ($pair in @(
            @{ Old = $OldPrefix; New = $NewPrefix },
            @{ Old = $OldPrefix.Replace('\', '/'); New = $NewPrefix.Replace('\', '/') }
        )) {
        $old = [string]$pair.Old
        $builder = New-Object System.Text.StringBuilder
        $cursor = 0
        $found = $false
        while ($true) {
            $at = $updated.IndexOf($old, $cursor, [StringComparison]::OrdinalIgnoreCase)
            if ($at -lt 0) { break }
            $found = $true
            [void]$builder.Append($updated.Substring($cursor, $at - $cursor))
            [void]$builder.Append([string]$pair.New)
            $cursor = $at + $old.Length
            $count++
        }
        if ($found) {
            [void]$builder.Append($updated.Substring($cursor))
            $updated = $builder.ToString()
        }
    }
    return [pscustomobject]@{ Text = $updated; Count = $count }
}

function Get-FilesContainingPrefix {
    param(
        [Parameter(Mandatory)][string]$Root,
        [Parameter(Mandatory)][string]$Prefix
    )
    $needle = $script:Utf8.GetBytes($Prefix)
    $slash = $script:Utf8.GetBytes($Prefix.Replace('\', '/'))
    $hits = New-Object System.Collections.Generic.List[string]
    if (-not (Test-Path -LiteralPath $Root)) { return @() }
    $base = [IO.Path]::GetFullPath($Root)
    Get-ChildItem -LiteralPath $Root -Recurse -File -Force | ForEach-Object {
        $bytes = [IO.File]::ReadAllBytes($_.FullName)
        if ((Test-ByteSpan $bytes $needle) -or (Test-ByteSpan $bytes $slash)) {
            $hits.Add($_.FullName.Substring($base.Length).TrimStart('\').Replace('\', '/')) | Out-Null
        }
    }
    return @($hits)
}

function Test-ByteSpan {
    param([byte[]]$Haystack, [byte[]]$Needle)
    if ($Needle.Length -eq 0 -or $Haystack.Length -lt $Needle.Length) { return $false }
    for ($i = 0; $i -le $Haystack.Length - $Needle.Length; $i++) {
        $match = $true
        for ($j = 0; $j -lt $Needle.Length; $j++) {
            $left = $Haystack[$i + $j]
            $right = $Needle[$j]
            if ($left -ge 65 -and $left -le 90) { $left = $left + 32 }
            if ($right -ge 65 -and $right -le 90) { $right = $right + 32 }
            if ($left -ne $right) { $match = $false; break }
        }
        if ($match) { return $true }
    }
    return $false
}

function Move-DevProfileTree {
    param(
        [string]$LocalAppData = $env:LOCALAPPDATA,
        [scriptblock]$RunningProbe
    )
    if (Test-ZolaClientOrServeRunning -Probe $RunningProbe) {
        return [pscustomobject]@{ Ok = $false; Reason = 'refusing: Zola is running'; Retarget = 0; OtherFiles = @() }
    }
    $roots = Get-DevRoots $LocalAppData
    $source = $roots.OldDevProfile
    $dest = $roots.DevProfile
    if (-not (Test-Path -LiteralPath $source)) {
        return [pscustomobject]@{ Ok = $false; Reason = 'refusing: the old dev profile is missing'; Retarget = 0; OtherFiles = @() }
    }
    $sourceItem = Get-Item -LiteralPath $source -Force
    if ($sourceItem.Attributes -band [IO.FileAttributes]::ReparsePoint) {
        return [pscustomobject]@{ Ok = $false; Reason = 'refusing: the old dev profile is a link'; Retarget = 0; OtherFiles = @() }
    }
    $sourceFinal = Resolve-FinalPath $source
    if ((Test-PathUnder $sourceFinal $roots.LiveProfile) -or (Test-PathUnder $sourceFinal $roots.LiveClient)) {
        return [pscustomobject]@{ Ok = $false; Reason = 'refusing: the old dev profile resolves into a live root'; Retarget = 0; OtherFiles = @() }
    }
    if (-not (Test-SafeDevDestination -Path $dest -Expected $dest -LiveProfile $roots.LiveProfile -LiveClient $roots.LiveClient -NativeHermes $roots.NativeHermes)) {
        return [pscustomobject]@{ Ok = $false; Reason = 'refusing: destination resolves into the native Hermes root or is not the dev folder'; Retarget = 0; OtherFiles = @() }
    }
    if (Test-Path -LiteralPath $dest) {
        return [pscustomobject]@{ Ok = $false; Reason = 'refusing: the new dev profile already exists'; Retarget = 0; OtherFiles = @() }
    }
    $before = Get-TreeHashMap $source
    $parent = Split-Path -Parent $dest
    if (-not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    Move-Item -LiteralPath $source -Destination $dest
    $after = Get-TreeHashMap $dest
    $diff = @(Compare-TreeHashMaps -Before $before -After $after)
    if ($diff.Count -gt 0 -or (Test-Path -LiteralPath $source)) {
        if ((Test-Path -LiteralPath $dest) -and -not (Test-Path -LiteralPath $source)) {
            Move-Item -LiteralPath $dest -Destination $source
        }
        return [pscustomobject]@{ Ok = $false; Reason = 'refusing: move hashes did not match'; Retarget = 0; OtherFiles = @() }
    }
    $config = Join-Path $dest 'config.yaml'
    $retarget = 0
    if (Test-Path -LiteralPath $config) {
        $text = [IO.File]::ReadAllText($config)
        $rewritten = Update-MovedProfilePrefix -Text $text -OldPrefix $source -NewPrefix $dest
        $retarget = [int]$rewritten.Count
        if ($retarget -gt 0) {
            [IO.File]::WriteAllText($config, $rewritten.Text, $script:Utf8)
        }
    }
    $others = @(Get-FilesContainingPrefix -Root $dest -Prefix $source | Where-Object { $_ -ne 'config.yaml' })
    return [pscustomobject]@{ Ok = $true; Reason = ''; Retarget = $retarget; OtherFiles = $others }
}

function Compare-TreeHashMaps {
    param($Before, $After)
    $changed = New-Object System.Collections.Generic.List[string]
    $beforeKeys = @($Before.Keys)
    $afterKeys = @($After.Keys)
    foreach ($key in $beforeKeys) {
        if ($afterKeys -notcontains $key) { $changed.Add("removed $key") | Out-Null }
        elseif ("$($Before[$key])" -ne "$($After[$key])") { $changed.Add("changed $key") | Out-Null }
    }
    foreach ($key in $afterKeys) {
        if ($beforeKeys -notcontains $key) { $changed.Add("added $key") | Out-Null }
    }
    return @($changed)
}

Export-ModuleMember -Function *
