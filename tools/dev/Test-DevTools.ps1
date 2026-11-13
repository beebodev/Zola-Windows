# PROC1-DEV: tests for the dev profile tools. Uses a temp root, never the live profile.
#Requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'DevCommon.psm1') -Force

$script:Pass = 0
$script:Fail = 0

function Assert-That {
    param([string]$Name, [scriptblock]$Body)
    try {
        if (& $Body) {
            $script:Pass++
            Write-Output "PASS $Name"
        } else {
            $script:Fail++
            Write-Output "FAIL $Name"
        }
    } catch {
        $script:Fail++
        Write-Output "FAIL $Name"
    }
}

function New-Fixture {
    $root = Join-Path $env:TEMP ("proc1-dev-tool-" + [guid]::NewGuid().ToString('N'))
    $live = Join-Path $root 'hermes\profiles\zola'
    New-Item -ItemType Directory -Force -Path $live | Out-Null
    $tts = Join-Path $live 'zola-tts\deepgram_tts.py'
    $clientKey = Join-Path $root 'ZolaClient\secrets\deepgram_api_key'
    $devAlready = Join-Path $root 'hermes\profiles\zola-dev\already.txt'
    $yaml = @"
model:
  provider: openai-codex
plugins:
  enabled: zola_tools,zola_workspace
tts:
  command: $tts
key: $clientKey
note: leave-this-line
also: $devAlready
"@
    [IO.File]::WriteAllText((Join-Path $live 'config.yaml'), $yaml.Replace("`r`n", "`n"))
    [IO.File]::WriteAllText((Join-Path $live 'SOUL.md'), "synthetic-soul-marker`n")
    [IO.File]::WriteAllText((Join-Path $live 'canary.txt'), 'live-canary')
    return $root
}

Assert-That 'rewrite maps the tts command, keeps the shared key, and leaves other lines' {
    $root = New-Fixture
    try {
        $result = New-DevProfileTree -LocalAppData $root
        if (-not $result.Ok) { return $false }
        $config = [IO.File]::ReadAllText((Join-Path $root 'hermes-dev\profiles\zola-dev\config.yaml'))
        $liveTts = Join-Path $root 'hermes\profiles\zola\zola-tts\deepgram_tts.py'
        $devTts = Join-Path $root 'hermes-dev\profiles\zola-dev\zola-tts\deepgram_tts.py'
        $liveKey = Join-Path $root 'ZolaClient\secrets\deepgram_api_key'
        $devKey = Join-Path $root 'ZolaClient-dev\secrets\deepgram_api_key'
        $befores = @($result.Changes | ForEach-Object { $_.Before })
        $afters = @($result.Changes | ForEach-Object { $_.After })
        $soulSame = [IO.File]::ReadAllText((Join-Path $root 'hermes-dev\profiles\zola-dev\SOUL.md')) -eq "synthetic-soul-marker`n"
        $copyOk = @($result.Copies | Where-Object { $_.SourceHash -eq $_.DestHash }).Count -eq 2
        $kept = @($result.Changes | Where-Object { $_.Kept -eq 'kept (shared, D5)' -and $_.Before -eq $liveKey -and $_.After -eq $liveKey })
        return ($config -like "*$devTts*") -and ($config -notlike "*$liveTts*") -and ($config -like "*$liveKey*") -and ($config -notlike "*$devKey*") -and ($config -like '*leave-this-line*') -and ($config -like '*zola_tools,zola_workspace*') -and ($config -like '*hermes\profiles\zola-dev\already.txt*') -and ($config -notlike '*hermes-dev\profiles\zola-dev\already.txt*') -and ($config -notlike '*zola-dev-dev*') -and ($befores -contains $liveTts) -and ($afters -contains $devTts) -and ($kept.Count -eq 1) -and $soulSame -and $copyOk -and -not (Test-Path (Join-Path $root 'hermes-dev\profiles\zola-dev\auth.json'))
    } finally {
        Remove-Item -LiteralPath $root -Recurse -Force
    }
}

Assert-That 'invented memories are the seed and nothing else is copied' {
    $root = New-Fixture
    try {
        $result = New-DevProfileTree -LocalAppData $root
        if (-not $result.Ok) { return $false }
        $user = [IO.File]::ReadAllText((Join-Path $root 'hermes-dev\profiles\zola-dev\memories\USER.md'))
        $memory = [IO.File]::ReadAllText((Join-Path $root 'hermes-dev\profiles\zola-dev\memories\MEMORY.md'))
        $names = @(Get-ChildItem -LiteralPath (Join-Path $root 'hermes-dev\profiles\zola-dev') -Force | ForEach-Object { $_.Name })
        $allowed = @('config.yaml', 'SOUL.md', 'memories')
        $extra = @($names | Where-Object { $allowed -notcontains $_ })
        $section = [char]0x00A7
        $userSeed = "[identity] The user's name is Casey Quinn.`n$section`n[home] Casey lives in the made-up town of Northglass.`n"
        $memorySeed = "[person] Jordan Hale is Casey's invented neighbour and keeps bees.`n$section`n[fact] Casey's favourite colour is slate.`n$section`n[project] The demo codename is Paper Kite.`n"
        return ($user -eq $userSeed) -and ($memory -eq $memorySeed) -and ($extra.Count -eq 0) -and ((Get-FileHash (Join-Path $root 'hermes\profiles\zola\canary.txt')).Hash -eq (Get-FileHash (Join-Path $root 'hermes\profiles\zola\canary.txt')).Hash)
    } finally {
        Remove-Item -LiteralPath $root -Recurse -Force
    }
}

Assert-That 'an unmapped live path refuses and removes the partial dev profile' {
    $root = New-Fixture
    $alias = Join-Path $root 'alias-live'
    $live = Join-Path $root 'hermes\profiles\zola'
    cmd /c mklink /J "$alias" "$live" | Out-Null
    $yaml = "command: $alias\hidden.txt`n"
    [IO.File]::WriteAllText((Join-Path $live 'config.yaml'), $yaml)
    try {
        $result = New-DevProfileTree -LocalAppData $root
        $canary = [IO.File]::ReadAllText((Join-Path $live 'canary.txt'))
        return (-not $result.Ok) -and ($result.Reason -like 'refusing: a live path in config.yaml could not be mapped:*') -and -not (Test-Path (Join-Path $root 'hermes-dev\profiles\zola-dev\config.yaml')) -and ($canary -eq 'live-canary')
    } finally {
        if (Test-Path -LiteralPath $alias) { cmd /c rmdir "$alias" | Out-Null }
        Remove-Item -LiteralPath $root -Recurse -Force
    }
}

Assert-That 'shared deepgram key path is kept and reported' {
    $root = New-Fixture
    try {
        $script = Join-Path $PSScriptRoot 'New-DevProfile.ps1'
        $output = @(& powershell -NoProfile -ExecutionPolicy Bypass -File $script -LocalAppData $root)
        if ($LASTEXITCODE -ne 0) { return $false }
        $config = [IO.File]::ReadAllText((Join-Path $root 'hermes-dev\profiles\zola-dev\config.yaml'))
        $liveKey = Join-Path $root 'ZolaClient\secrets\deepgram_api_key'
        $devKey = Join-Path $root 'ZolaClient-dev\secrets\deepgram_api_key'
        $liveTts = Join-Path $root 'hermes\profiles\zola\zola-tts\deepgram_tts.py'
        $devTts = Join-Path $root 'hermes-dev\profiles\zola-dev\zola-tts\deepgram_tts.py'
        $kept = @($output | Where-Object { $_ -eq 'config.yaml path kept (shared, D5)' })
        $beforeKey = @($output | Where-Object { $_ -eq "config.yaml path before=$liveKey" })
        $afterKey = @($output | Where-Object { $_ -like "config.yaml path after=*$liveKey" })
        return ($config.Contains($liveKey)) -and (-not $config.Contains($devKey)) -and ($config.Contains($devTts)) -and (-not $config.Contains($liveTts)) -and ($kept.Count -eq 1) -and ($beforeKey.Count -eq 1) -and ($afterKey.Count -eq 0)
    } finally {
        Remove-Item -LiteralPath $root -Recurse -Force
    }
}

Assert-That 'replace refuses an injected running client or serve and allows an injected idle probe' {
    $root = New-Fixture
    $dev = Join-Path $root 'hermes-dev\profiles\zola-dev'
    New-Item -ItemType Directory -Force -Path (Join-Path $dev 'plugins\zola_workspace') | Out-Null
    [IO.File]::WriteAllText((Join-Path $dev 'canary.txt'), 'dev-canary')
    try {
        $refused = New-DevProfileTree -LocalAppData $root -Replace -RunningProbe { $true }
        $still = [IO.File]::ReadAllText((Join-Path $dev 'canary.txt'))
        $from = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $sync = Sync-DevPluginTree -From $from -LocalAppData $root -Replace -RunningProbe { $true }
        $stillAfterSync = [IO.File]::ReadAllText((Join-Path $dev 'canary.txt'))
        $allowed = New-DevProfileTree -LocalAppData $root -Replace -RunningProbe { $false }
        $gone = -not (Test-Path -LiteralPath (Join-Path $dev 'canary.txt'))
        return (-not $refused.Ok) -and ($refused.Reason -eq 'refusing: Zola is running') -and ($still -eq 'dev-canary') -and (-not $sync.Ok) -and ($sync.Reason -eq 'refusing: Zola is running') -and ($stillAfterSync -eq 'dev-canary') -and $allowed.Ok -and $gone
    } finally {
        Remove-Item -LiteralPath $root -Recurse -Force
    }
}

Assert-That 'replace refuses while Zola is running and leaves the dev folder' {
    $root = New-Fixture
    $dev = Join-Path $root 'hermes-dev\profiles\zola-dev'
    New-Item -ItemType Directory -Force -Path $dev | Out-Null
    [IO.File]::WriteAllText((Join-Path $dev 'canary.txt'), 'dev-canary')
    $created = $false
    $mutex = $null
    try {
        $mutex = New-Object System.Threading.Mutex($false, 'Local\ZolaClient')
        try { $created = $mutex.WaitOne(0) } catch { $created = $false }
        $result = New-DevProfileTree -LocalAppData $root -Replace
        $still = [IO.File]::ReadAllText((Join-Path $dev 'canary.txt'))
        return (-not $result.Ok) -and ($result.Reason -eq 'refusing: Zola is running') -and ($still -eq 'dev-canary')
    } finally {
        if ($created -and $null -ne $mutex) { $mutex.ReleaseMutex() }
        if ($null -ne $mutex) { $mutex.Dispose() }
        Remove-Item -LiteralPath $root -Recurse -Force
    }
}

Assert-That 'a live profile target is not a safe dev destination' {
    $root = New-Fixture
    try {
        $roots = Get-DevRoots $root
        $safe = Test-SafeDevDestination -Path $roots.DevProfile -Expected $roots.DevProfile -LiveProfile $roots.LiveProfile -LiveClient $roots.LiveClient -NativeHermes $roots.NativeHermes
        $live = Test-SafeDevDestination -Path $roots.LiveProfile -Expected $roots.DevProfile -LiveProfile $roots.LiveProfile -LiveClient $roots.LiveClient -NativeHermes $roots.NativeHermes
        $client = Test-SafeDevDestination -Path $roots.LiveClient -Expected $roots.DevClient -LiveProfile $roots.LiveProfile -LiveClient $roots.LiveClient -NativeHermes $roots.NativeHermes
        $native = Test-SafeDevDestination -Path $roots.OldDevProfile -Expected $roots.DevProfile -LiveProfile $roots.LiveProfile -LiveClient $roots.LiveClient -NativeHermes $roots.NativeHermes
        return $safe -and -not $live -and -not $client -and -not $native -and ($roots.DevProfile -eq (Join-Path $root 'hermes-dev\profiles\zola-dev'))
    } finally {
        Remove-Item -LiteralPath $root -Recurse -Force
    }
}

Assert-That 'sync copies deepgram into zola-tts and does not copy zola_phone or the hold guard' {
    $root = New-Fixture
    try {
        New-Item -ItemType Directory -Force -Path (Join-Path $root 'hermes-dev\profiles\zola-dev') | Out-Null
        [IO.File]::WriteAllText((Join-Path $root 'hermes-dev\profiles\zola-dev\auth.json'), 'do-not-touch')
        $from = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $result = Sync-DevPluginTree -From $from -LocalAppData $root
        if (-not $result.Ok) { return $false }
        $dev = Join-Path $root 'hermes-dev\profiles\zola-dev'
        $tts = Join-Path $dev 'zola-tts\deepgram_tts.py'
        $repo = Join-Path $from 'hermes-plugins\zola_tts\deepgram_tts.py'
        $canary = [IO.File]::ReadAllText((Join-Path $root 'hermes\profiles\zola\canary.txt'))
        return (Test-Path -LiteralPath $tts) -and ((Get-FileHash -LiteralPath $tts).Hash -eq (Get-FileHash -LiteralPath $repo).Hash) -and -not (Test-Path (Join-Path $dev 'plugins\zola_phone')) -and -not (Test-Path (Join-Path $dev 'plugins\zola_memory\l6_hold_guard.py')) -and (([IO.File]::ReadAllText((Join-Path $dev 'auth.json'))) -eq 'do-not-touch') -and ($canary -eq 'live-canary') -and (@($result.Copied) -notcontains 'plugins/zola_phone')
    } finally {
        Remove-Item -LiteralPath $root -Recurse -Force
    }
}

Assert-That 'sync refuses a live profile target' {
    $root = New-Fixture
    try {
        $from = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $before = [IO.File]::ReadAllText((Join-Path $root 'hermes\profiles\zola\canary.txt'))
        $direct = Test-SafeDevDestination -Path (Join-Path $root 'hermes\profiles\zola') -Expected (Join-Path $root 'hermes-dev\profiles\zola-dev') -LiveProfile (Join-Path $root 'hermes\profiles\zola') -LiveClient (Join-Path $root 'ZolaClient') -NativeHermes (Join-Path $root 'hermes')
        # Point the module at the live folder by using a local root whose dev path is the fixture live path via a junction.
        $linkRoot = Join-Path $root 'link-root'
        New-Item -ItemType Directory -Force -Path (Join-Path $linkRoot 'hermes-dev\profiles') | Out-Null
        cmd /c mklink /J "$(Join-Path $linkRoot 'hermes-dev\profiles\zola-dev')" "$(Join-Path $root 'hermes\profiles\zola')" | Out-Null
        $refused = Sync-DevPluginTree -From $from -LocalAppData $linkRoot
        $after = [IO.File]::ReadAllText((Join-Path $root 'hermes\profiles\zola\canary.txt'))
        return (-not $direct) -and (-not $refused.Ok) -and ($after -eq $before)
    } finally {
        $junction = Join-Path $root 'link-root\hermes-dev\profiles\zola-dev'
        if (Test-Path -LiteralPath $junction) { cmd /c rmdir "$junction" | Out-Null }
        Remove-Item -LiteralPath $root -Recurse -Force
    }
}

Assert-That 'profile tokens do not prefix-match and hash maps notice a change' {
    $dev = Test-FinishedProfileToken -CommandLine 'python -m hermes_cli.main -p zola-dev serve --isolated' -ProfileName 'zola-dev'
    $notStable = -not (Test-FinishedProfileToken -CommandLine 'python -m hermes_cli.main -p zola-dev serve --isolated' -ProfileName 'zola')
    $stable = Test-FinishedProfileToken -CommandLine 'python -m hermes_cli.main -p zola serve --isolated' -ProfileName 'zola'
    $root = Join-Path $env:TEMP ("proc1-dev-hash-" + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Force -Path $root | Out-Null
    try {
        [IO.File]::WriteAllText((Join-Path $root 'a.txt'), 'one')
        $before = Get-TreeHashMap $root
        $same = Get-TreeHashMap $root
        [IO.File]::WriteAllText((Join-Path $root 'a.txt'), 'two')
        $after = Get-TreeHashMap $root
        return $dev -and $notStable -and $stable -and (@(Compare-TreeHashMaps $before $same).Count -eq 0) -and (@(Compare-TreeHashMaps $before $after).Count -eq 1)
    } finally {
        Remove-Item -LiteralPath $root -Recurse -Force
    }
}

Assert-That 'move refuses while a probe says Zola is running' {
    $root = New-Fixture
    $source = Join-Path $root 'hermes\profiles\zola-dev'
    New-Item -ItemType Directory -Force -Path $source | Out-Null
    [IO.File]::WriteAllText((Join-Path $source 'canary.txt'), 'keep')
    try {
        $result = Move-DevProfileTree -LocalAppData $root -RunningProbe { $true }
        $still = [IO.File]::ReadAllText((Join-Path $source 'canary.txt'))
        $absent = -not (Test-Path -LiteralPath (Join-Path $root 'hermes-dev\profiles\zola-dev'))
        return (-not $result.Ok) -and ($result.Reason -eq 'refusing: Zola is running') -and ($still -eq 'keep') -and $absent
    } finally {
        Remove-Item -LiteralPath $root -Recurse -Force
    }
}

Assert-That 'move matches hashes, retargets config, and leaves the old folder' {
    $root = New-Fixture
    $source = Join-Path $root 'hermes\profiles\zola-dev'
    New-Item -ItemType Directory -Force -Path (Join-Path $source 'memories') | Out-Null
    $config = "tts: $source\zola-tts\deepgram_tts.py`n"
    [IO.File]::WriteAllText((Join-Path $source 'config.yaml'), $config)
    [IO.File]::WriteAllText((Join-Path $source 'memories\USER.md'), 'seed')
    [IO.File]::WriteAllText((Join-Path $source 'notes.txt'), "see $source\notes.txt")
    $live = [IO.File]::ReadAllText((Join-Path $root 'hermes\profiles\zola\canary.txt'))
    try {
        $result = Move-DevProfileTree -LocalAppData $root -RunningProbe { $false }
        $dest = Join-Path $root 'hermes-dev\profiles\zola-dev'
        $moved = [IO.File]::ReadAllText((Join-Path $dest 'config.yaml'))
        $notes = [IO.File]::ReadAllText((Join-Path $dest 'notes.txt'))
        $user = [IO.File]::ReadAllText((Join-Path $dest 'memories\USER.md'))
        $liveAfter = [IO.File]::ReadAllText((Join-Path $root 'hermes\profiles\zola\canary.txt'))
        $expected = "tts: $dest\zola-tts\deepgram_tts.py`n"
        return $result.Ok -and ($result.Retarget -eq 1) -and ($moved -eq $expected) -and ($notes -eq "see $source\notes.txt") -and (@($result.OtherFiles) -contains 'notes.txt') -and ($user -eq 'seed') -and -not (Test-Path -LiteralPath $source) -and ($liveAfter -eq $live)
    } finally {
        Remove-Item -LiteralPath $root -Recurse -Force
    }
}

. (Join-Path $PSScriptRoot 'Test-DevIsolation.ps1')

Assert-That 'live sqlite refuses while stable runs and otherwise opens immutable' {
    $root = Join-Path $env:TEMP ("proc1-dev-sqlite-" + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Force -Path $root | Out-Null
    $db = Join-Path $root 'sample.db'
    $maker = Join-Path $root 'make.py'
    [IO.File]::WriteAllText($maker, "import sqlite3, sys`nconn = sqlite3.connect(sys.argv[1])`nconn.execute('pragma journal_mode=wal')`nconn.execute('create table t(n integer)')`nconn.execute('insert into t values (7)')`nconn.commit()`nconn.execute('pragma wal_checkpoint(truncate)')`nconn.close()`n")
    $python = 'C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe'
    & $python $maker $db | Out-Null
    $shm = "$db-shm"
    $before = if (Test-Path -LiteralPath $shm) { (Get-FileHash -LiteralPath $shm).Hash } else { '' }
    try {
        $blocked = Invoke-LiveSqliteReadOnly -Database $db -Query 'select n from t' -Probe { $true }
        $mid = if (Test-Path -LiteralPath $shm) { (Get-FileHash -LiteralPath $shm).Hash } else { '' }
        $opened = Invoke-LiveSqliteReadOnly -Database $db -Query 'select n from t' -Probe { $false }
        $after = if (Test-Path -LiteralPath $shm) { (Get-FileHash -LiteralPath $shm).Hash } else { '' }
        $text = [IO.File]::ReadAllText((Join-Path $PSScriptRoot 'Test-DevIsolation.ps1'))
        return (-not $blocked.Ok) -and ($blocked.Reason -eq 'refusing: stable is running') -and ($mid -eq $before) -and $opened.Ok -and (@($opened.Rows) -contains '7') -and ($after -eq $before) -and $text.Contains('mode=ro&immutable=1') -and $text.Contains('AfterClose compares hashes')
    } finally {
        Remove-Item -LiteralPath $root -Recurse -Force
    }
}

$python = 'C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe'
$plugins = (Resolve-Path (Join-Path $PSScriptRoot '..\..\hermes-plugins')).Path
$hermes = 'C:\Users\test\Dev\hermes-agent'
$pyOut = @(& $python (Join-Path $PSScriptRoot 'dev_behavior_tests.py') $plugins $hermes)
$pyOut | ForEach-Object { Write-Output $_ }
$pyPass = @($pyOut | Where-Object { "$_" -like 'PASS *' }).Count
$script:Pass += $pyPass
if ($LASTEXITCODE -ne 0) {
    $script:Fail++
    Write-Output 'FAIL python behavior tests'
}

Write-Output "==== SUMMARY pass=$($script:Pass) fail=$($script:Fail) ===="
if ($script:Fail -gt 0) { exit 1 }
exit 0
