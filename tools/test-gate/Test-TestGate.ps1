#Requires -Version 5.1
# PROC1-GATE self-tests - unit + end-to-end fake suites. No real product suites.
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$gateDir = $PSScriptRoot
Import-Module (Join-Path $gateDir 'TestGate.Common.psm1') -Force -DisableNameChecking
$runGate = Join-Path $gateDir 'Run-TestGate.ps1'

$script:Pass = 0
$script:Fail = 0

function Ok([string]$Name) { $script:Pass++; Write-Host "PASS $Name" }
function Bad([string]$Name, [string]$Why) { $script:Fail++; Write-Host "FAIL $Name - $Why" }
function Assert-That([string]$Name, [scriptblock]$Body) {
    try {
        $r = & $Body
        if ($r) { Ok $Name } else { Bad $Name 'returned false' }
    } catch {
        Bad $Name $_.Exception.Message
    }
}

function New-TempGitRepo {
    $dir = Join-Path $env:TEMP ('gate-self-repo-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    Push-Location $dir
    try {
        git init -q | Out-Null
        git config user.email 'gate-self@test.local'
        git config user.name 'Gate Self'
        Set-Content -Path 'README.md' -Value 'gate-self' -Encoding ASCII
        git add README.md
        git commit -q -m 'init'
    } finally {
        Pop-Location
    }
    return $dir
}

function New-FakeHarness {
    param([switch]$Dirty)
    $root = New-TempGitRepo
    $tools = Join-Path $root 'tools\fake'
    New-Item -ItemType Directory -Force -Path $tools | Out-Null
    @'
$ErrorActionPreference = "Stop"
Write-Host "==== SUMMARY pass=1 fail=0 ===="
exit 0
'@ | Set-Content (Join-Path $tools 'pass.ps1') -Encoding ASCII
    @'
Write-Host "==== SUMMARY pass=0 fail=1 ===="
exit 1
'@ | Set-Content (Join-Path $tools 'fail.ps1') -Encoding ASCII
    @'
Write-Host "no summary here"
exit 0
'@ | Set-Content (Join-Path $tools 'infra.ps1') -Encoding ASCII
    @'
if ($env:PYTHONPATH) { Write-Host "==== SUMMARY pass=0 fail=1 ===="; exit 1 }
Write-Host "==== SUMMARY pass=1 fail=0 ===="
exit 0
'@ | Set-Content (Join-Path $tools 'envcheck.ps1') -Encoding ASCII
    @'
# Grandchild sleep for timeout cleanup
$p = Start-Process -FilePath "$env:SystemRoot\System32\cmd.exe" -ArgumentList '/c','ping -n 60 127.0.0.1 >NUL' -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 120
'@ | Set-Content (Join-Path $tools 'sleep_hang.ps1') -Encoding ASCII
    @'
# Touch a tracked-looking file in repo root during the run
Set-Content -Path (Join-Path $PSScriptRoot '..\..\midrun.txt') -Value 'changed' -Encoding ASCII
Write-Host "==== SUMMARY pass=1 fail=0 ===="
exit 0
'@ | Set-Content (Join-Path $tools 'midrun.ps1') -Encoding ASCII

    $suitePsd1 = Join-Path $root 'fake-suites.psd1'
    @"
@{
  GateVersion = '1.0.0-self'
  JavaHome = 'C:\Program Files\Android\Android Studio\jbr'
  AndroidHome = '%LOCALAPPDATA%\Android\Sdk'
  ClearEnvNames = @('PYTHONPATH','PYTHONHOME','VIRTUAL_ENV','HERMES_HOME','PIP_INDEX_URL','PIP_EXTRA_INDEX_URL','PIP_REQUIRE_VIRTUALENV','PIP_TARGET','PIP_FIND_LINKS')
  Suites = @(
    @{ Name='alpha'; WorkingDirectory=''; Kind='summary_ps1'; TimeoutSec=30; NeedsZolaClosed=`$false; PromoteOnly=`$false; NeedsPythonPath=`$false; NeedsAndroid=`$false; DiscoverS=''; DiscoverT=''; ScriptRelative='tools\fake\pass.ps1'; Command=@() }
    @{ Name='beta'; WorkingDirectory=''; Kind='summary_ps1'; TimeoutSec=30; NeedsZolaClosed=`$false; PromoteOnly=`$false; NeedsPythonPath=`$false; NeedsAndroid=`$false; DiscoverS=''; DiscoverT=''; ScriptRelative='tools\fake\pass.ps1'; Command=@() }
    @{ Name='zola_phone'; WorkingDirectory=''; Kind='summary_ps1'; TimeoutSec=30; NeedsZolaClosed=`$true; PromoteOnly=`$false; NeedsPythonPath=`$false; NeedsAndroid=`$false; DiscoverS=''; DiscoverT=''; ScriptRelative='tools\fake\pass.ps1'; Command=@() }
  )
}
"@ | Set-Content $suitePsd1 -Encoding ASCII

    $floors = Join-Path $root 'fake-floors.json'
    @'
{ "version": 1, "suites": {
  "alpha": { "min_passed": 1, "allowed_skips": [] },
  "beta": { "min_passed": 1, "allowed_skips": [] },
  "zola_phone": { "min_passed": 1, "allowed_skips": [] }
}}
'@ | Set-Content $floors -Encoding ASCII

    # Commit harness so clean-repo E2E starts with a clean tree
    Push-Location $root
    try {
        git add -A | Out-Null
        git commit -q -m 'harness'
    } finally {
        Pop-Location
    }
    if ($Dirty) {
        Set-Content -Path (Join-Path $root 'dirty.txt') -Value 'x' -Encoding ASCII
    }

    return [pscustomobject]@{ Root = $root; SuiteFile = $suitePsd1; FloorsFile = $floors; Tools = $tools }
}

function Commit-HarnessTree {
    param($Root, [string]$Message = 'harness update')
    Push-Location $Root
    try {
        git add -A | Out-Null
        $st = @(git status --porcelain 2>$null)
        if ($st.Count -gt 0) {
            git commit -q -m $Message
        }
    } finally {
        Pop-Location
    }
}

function Invoke-FakeGate {
    param(
        $Harness,
        [string[]]$Only,
        [switch]$UpdateFloors,
        [string]$ZolaRunningProbePath,
        [string]$SuiteFile,
        [string]$FloorsFile
    )
    $sf = if ($SuiteFile) { $SuiteFile } else { $Harness.SuiteFile }
    $ff = if ($FloorsFile) { $FloorsFile } else { $Harness.FloorsFile }
    $json = Join-Path $env:TEMP ('gate-self-result-' + [guid]::NewGuid().ToString('N') + '.json')
    $argList = @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $runGate,
        '-RepoRoot', $Harness.Root,
        '-SuiteFile', $sf,
        '-FloorsFile', $ff,
        '-SkipSelf',
        '-Json', $json
    )
    if ($Only) { $argList += '-Only'; $argList += ($Only -join ',') }
    if ($UpdateFloors) { $argList += '-UpdateFloors' }
    if ($ZolaRunningProbePath) {
        $argList += '-ZolaRunningProbe'; $argList += $ZolaRunningProbePath
    }
    $p = Start-Process -FilePath 'powershell' -ArgumentList $argList -Wait -PassThru -NoNewWindow
    $obj = $null
    if (Test-Path $json) {
        $obj = Get-Content $json -Raw -Encoding UTF8 | ConvertFrom-Json
    }
    return [pscustomobject]@{ ExitCode = $p.ExitCode; Result = $obj; Json = $json }
}

# ---------- unit tests (kept / extended) ----------
$floorOk = [pscustomobject]@{ min_passed = 10; allowed_skips = @() }

Assert-That 'FAIL on a failing suite' {
    $c = Classify-SuiteResult -Floor $floorOk -InfraReason '' -HasMarker $true -Passed 9 -Failed 1 -Skipped 0 -SkipItems @() -ZeroTestsFail:$false -ExitSuccess:$false
    $c.Result -eq 'FAIL'
}
Assert-That 'FAIL on zero tests' {
    $c = Classify-SuiteResult -Floor $floorOk -InfraReason '' -HasMarker $true -Passed 0 -Failed 0 -Skipped 0 -SkipItems @() -ZeroTestsFail:$true -ExitSuccess:$false
    $c.Result -eq 'FAIL'
}
Assert-That 'FAIL below floor' {
    $c = Classify-SuiteResult -Floor $floorOk -InfraReason '' -HasMarker $true -Passed 5 -Failed 0 -Skipped 0 -SkipItems @() -ZeroTestsFail:$false -ExitSuccess:$true
    $c.Result -eq 'FAIL'
}
Assert-That 'FAIL on an extra skip' {
    $c = Classify-SuiteResult -Floor $floorOk -InfraReason '' -HasMarker $true -Passed 10 -Failed 0 -Skipped 1 -SkipItems @([pscustomobject]@{id='t';reason='r'}) -ZeroTestsFail:$false -ExitSuccess:$true
    $c.Result -eq 'FAIL'
}
Assert-That 'different skipped test same count is FAIL' {
    $floor = [pscustomobject]@{ min_passed = 1; allowed_skips = @([pscustomobject]@{ id = 'a.Test'; reason = 'old' }) }
    $c = Classify-SuiteResult -Floor $floor -HasMarker $true -Passed 1 -Failed 0 -Skipped 1 `
        -SkipItems @([pscustomobject]@{ id = 'a.Test'; reason = 'new' }) -ZeroTestsFail:$false -ExitSuccess:$true
    $c.Result -eq 'FAIL'
}
Assert-That 'INFRA on missing marker' {
    $c = Classify-SuiteResult -Floor $floorOk -HasMarker $false -Passed 10 -Failed 0 -Skipped 0 -SkipItems @() -ZeroTestsFail:$false -ExitSuccess:$true
    $c.Result -eq 'INFRA'
}
Assert-That 'INFRA on timeout reason' {
    $c = Classify-SuiteResult -Floor $floorOk -InfraReason 'timeout after 1s' -HasMarker $false -Passed 0 -Failed 0 -Skipped 0 -SkipItems @() -ZeroTestsFail:$false -ExitSuccess:$false
    $c.Result -eq 'INFRA'
}
Assert-That 'PASS when marker floor and exit ok' {
    $c = Classify-SuiteResult -Floor $floorOk -HasMarker $true -Passed 10 -Failed 0 -Skipped 0 -SkipItems @() -ZeroTestsFail:$false -ExitSuccess:$true
    $c.Result -eq 'PASS'
}
Assert-That 'Parse unittest uses last Ran match' {
    $text = "Ran 1 tests in 0.001s`r`nOK`r`nRan 44 tests in 0.021s`r`nOK`r`n"
    $p = Parse-UnittestOutput -Text $text -ExitCode 0
    $p.Ran -eq 44 -and $p.Passed -eq 44
}
Assert-That 'Parse unittest OK (skipped=N)' {
    $text = "test_a (pkg.mod.T.test_a) ... skipped 'why'`r`nRan 2 tests in 0.01s`r`nOK (skipped=1)`r`n"
    $p = Parse-UnittestOutput -Text $text -ExitCode 0
    $p.Skipped -eq 1 -and $p.SkipItems.Count -eq 1 -and $p.SkipItems[0].id -eq 'pkg.mod.T.test_a' -and $p.SkipItems[0].reason -eq 'why'
}
Assert-That 'Parse unittest skip count/identity mismatch is FAIL' {
    $floor = [pscustomobject]@{ min_passed = 0; allowed_skips = @([pscustomobject]@{ id = 'a'; reason = 'r' }) }
    $c = Classify-SuiteResult -Floor $floor -HasMarker $true -Passed 1 -Failed 0 -Skipped 2 `
        -SkipItems @([pscustomobject]@{ id = 'a'; reason = 'r' }) -ZeroTestsFail:$false -ExitSuccess:$true
    $c.Result -eq 'FAIL' -and ($c.Reason -match 'skip count/identity mismatch')
}
Assert-That 'Parse unittest NO TESTS RAN is zero-fail' {
    $p = Parse-UnittestOutput -Text "Ran 0 tests in 0.000s`r`nNO TESTS RAN`r`n" -ExitCode 5
    $p.ZeroFail -and $p.Ran -eq 0
}
Assert-That 'Parse real venv Python -v skips; allowed PASS; wrong id FAIL' {
    $hermes = Get-HermesRoot
    $py = Get-HermesPython -HermesRoot $hermes
    if (-not $py -or -not (Test-Path -LiteralPath $py)) { throw "venv python missing: $py" }
    $dir = Join-Path $env:TEMP ('gate-skip-real-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    try {
        $mod = Join-Path $dir 'test_skip_real.py'
        @'
import unittest

class T(unittest.TestCase):
    @unittest.skip("no-doc reason")
    def test_no_doc(self):
        pass

    @unittest.skip("with-doc reason")
    def test_with_doc(self):
        """Doc line one.
        Doc line two.
        """
        pass

if __name__ == "__main__":
    unittest.main(verbosity=2)
'@ | Set-Content -LiteralPath $mod -Encoding UTF8
        $outFile = Join-Path $dir 'out.txt'
        $errFile = Join-Path $dir 'err.txt'
        $pinfo = Start-Process -FilePath $py -ArgumentList @($mod, '-v') -Wait -PassThru -NoNewWindow `
            -RedirectStandardOutput $outFile -RedirectStandardError $errFile
        $text = ((Get-Content -LiteralPath $outFile -Raw -EA SilentlyContinue) + "`n" +
                 (Get-Content -LiteralPath $errFile -Raw -EA SilentlyContinue))
        $p = Parse-UnittestOutput -Text $text -ExitCode $pinfo.ExitCode
        $ids = @($p.SkipItems | ForEach-Object { $_.id })
        $reasons = @($p.SkipItems | ForEach-Object { $_.reason })
        $parsedOk = ($p.Skipped -eq 2) -and ($p.SkipItems.Count -eq 2) -and `
            ($ids -contains '__main__.T.test_no_doc') -and ($ids -contains '__main__.T.test_with_doc') -and `
            ($reasons -contains 'no-doc reason') -and ($reasons -contains 'with-doc reason') -and `
            ($text -match 'Doc line one')
        $floorOkSkip = [pscustomobject]@{
            min_passed = 0
            allowed_skips = @(
                [pscustomobject]@{ id = '__main__.T.test_no_doc'; reason = 'no-doc reason' },
                [pscustomobject]@{ id = '__main__.T.test_with_doc'; reason = 'with-doc reason' }
            )
        }
        $pass = Classify-SuiteResult -Floor $floorOkSkip -HasMarker $true -Passed $p.Passed -Failed 0 `
            -Skipped $p.Skipped -SkipItems $p.SkipItems -ZeroTestsFail:$false -ExitSuccess:$true
        $floorBad = [pscustomobject]@{
            min_passed = 0
            allowed_skips = @(
                [pscustomobject]@{ id = '__main__.T.test_no_doc'; reason = 'no-doc reason' },
                [pscustomobject]@{ id = '__main__.T.other'; reason = 'with-doc reason' }
            )
        }
        $fail = Classify-SuiteResult -Floor $floorBad -HasMarker $true -Passed $p.Passed -Failed 0 `
            -Skipped $p.Skipped -SkipItems $p.SkipItems -ZeroTestsFail:$false -ExitSuccess:$true
        $parsedOk -and ($pass.Result -eq 'PASS') -and ($fail.Result -eq 'FAIL')
    } finally {
        Remove-Item -LiteralPath $dir -Recurse -Force -EA SilentlyContinue
    }
}
Assert-That 'Parse SUMMARY' {
    $p = Parse-SummaryPs1 -Text "==== SUMMARY pass=16 fail=0 ====`r`n"
    $p.Marker -and $p.Passed -eq 16
}
Assert-That 'Parse Checks requires coverage' {
    $p = Parse-ChecksOutput -Text "PASS a`r`ncoverage: x`r`n" -ExitCode 0
    $p.Marker -and $p.Passed -eq 1
}
Assert-That 'stale Kotlin XML cannot PASS marker' {
    $dir = Join-Path $env:TEMP ('gate-self-xml-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    try {
        $xml = Join-Path $dir 'TEST-Fake.xml'
        Set-Content -LiteralPath $xml -Value '<?xml version="1.0"?><testsuite tests="1" failures="0" errors="0" skipped="0"></testsuite>'
        (Get-Item $xml).LastWriteTimeUtc = (Get-Date).ToUniversalTime().AddMinutes(-5)
        $p = Parse-KotlinXml -ResultDir $dir -RunStartUtc (Get-Date).ToUniversalTime()
        -not $p.Marker
    } finally {
        Remove-Item -LiteralPath $dir -Recurse -Force -ErrorAction SilentlyContinue
    }
}
Assert-That 'environment clear drops PYTHONPATH' {
    $prev = $env:PYTHONPATH
    $env:PYTHONPATH = 'should-not-leak'
    try {
        $defs = @{ ClearEnvNames = @('PYTHONPATH', 'HERMES_HOME') }
        $map = New-ClearedSuiteEnvironment -SuiteDef $defs -Extra @{ FOO = 'bar' }
        (-not $map.ContainsKey('PYTHONPATH')) -and ($map['FOO'] -eq 'bar')
    } finally {
        if ($null -eq $prev) { Remove-Item Env:PYTHONPATH -EA SilentlyContinue } else { $env:PYTHONPATH = $prev }
    }
}
Assert-That 'OpenExisting free mutex' {
    -not (Test-MutexHeld -Name ('Local\ZolaGateSelfTestMutex' + [guid]::NewGuid().ToString('N')))
}
Assert-That 'OpenExisting held mutex without WaitOne' {
    $name = 'Local\ZolaGateSelfTestHeld' + [guid]::NewGuid().ToString('N')
    $m = New-Object System.Threading.Mutex($true, $name)
    try { Test-MutexHeld -Name $name } finally { $m.ReleaseMutex(); $m.Dispose() }
}
# ---------- end-to-end fake gate ----------
Assert-That 'E2E exit 0 PASS on clean repo' {
    $h = New-FakeHarness
    try {
        # Without phone hold: need probe false - default Test-ZolaRunningForGate may be true if Zola up.
        # Exclude zola_phone via floors/suites that only have alpha+beta for this case.
        $suite = Join-Path $h.Root 'clean-suites.psd1'
        @"
@{
  GateVersion='1.0.0-self'; JavaHome='C:\Program Files\Android\Android Studio\jbr'; AndroidHome='%LOCALAPPDATA%\Android\Sdk'
  ClearEnvNames=@('PYTHONPATH','HERMES_HOME','PYTHONHOME','VIRTUAL_ENV','PIP_INDEX_URL','PIP_EXTRA_INDEX_URL','PIP_REQUIRE_VIRTUALENV','PIP_TARGET','PIP_FIND_LINKS')
  Suites=@(
    @{ Name='alpha'; WorkingDirectory=''; Kind='summary_ps1'; TimeoutSec=30; NeedsZolaClosed=`$false; PromoteOnly=`$false; NeedsPythonPath=`$false; NeedsAndroid=`$false; DiscoverS=''; DiscoverT=''; ScriptRelative='tools\fake\pass.ps1'; Command=@() }
  )
}
"@ | Set-Content $suite -Encoding ASCII
        $floors = Join-Path $h.Root 'clean-floors.json'
        '{ "version":1, "suites": { "alpha": { "min_passed": 1, "allowed_skips": [] } } }' | Set-Content $floors -Encoding ASCII
        Commit-HarnessTree -Root $h.Root -Message 'clean suites'
        $r = Invoke-FakeGate -Harness $h -SuiteFile $suite -FloorsFile $floors
        $r.ExitCode -eq 0 -and $r.Result.overall -eq 'PASS'
    } finally {
        Remove-Item -LiteralPath $h.Root -Recurse -Force -EA SilentlyContinue
    }
}

Assert-That 'E2E exit 1 FAIL' {
    $h = New-FakeHarness
    try {
        $suite = Join-Path $h.Root 'fail-suites.psd1'
        @"
@{
  GateVersion='1.0.0-self'; JavaHome='C:\Program Files\Android\Android Studio\jbr'; AndroidHome='%LOCALAPPDATA%\Android\Sdk'
  ClearEnvNames=@('PYTHONPATH','HERMES_HOME','PYTHONHOME','VIRTUAL_ENV','PIP_INDEX_URL','PIP_EXTRA_INDEX_URL','PIP_REQUIRE_VIRTUALENV','PIP_TARGET','PIP_FIND_LINKS')
  Suites=@(
    @{ Name='alpha'; WorkingDirectory=''; Kind='summary_ps1'; TimeoutSec=30; NeedsZolaClosed=`$false; PromoteOnly=`$false; NeedsPythonPath=`$false; NeedsAndroid=`$false; DiscoverS=''; DiscoverT=''; ScriptRelative='tools\fake\fail.ps1'; Command=@() }
  )
}
"@ | Set-Content $suite -Encoding ASCII
        $floors = Join-Path $h.Root 'fail-floors.json'
        '{ "version":1, "suites": { "alpha": { "min_passed": 1, "allowed_skips": [] } } }' | Set-Content $floors -Encoding ASCII
        $r = Invoke-FakeGate -Harness $h -SuiteFile $suite -FloorsFile $floors
        $r.ExitCode -eq 1 -and $r.Result.overall -eq 'FAIL'
    } finally {
        Remove-Item -LiteralPath $h.Root -Recurse -Force -EA SilentlyContinue
    }
}

Assert-That 'E2E exit 2 INFRA only' {
    $h = New-FakeHarness
    try {
        $suite = Join-Path $h.Root 'infra-suites.psd1'
        @"
@{
  GateVersion='1.0.0-self'; JavaHome='C:\Program Files\Android\Android Studio\jbr'; AndroidHome='%LOCALAPPDATA%\Android\Sdk'
  ClearEnvNames=@('PYTHONPATH','HERMES_HOME','PYTHONHOME','VIRTUAL_ENV','PIP_INDEX_URL','PIP_EXTRA_INDEX_URL','PIP_REQUIRE_VIRTUALENV','PIP_TARGET','PIP_FIND_LINKS')
  Suites=@(
    @{ Name='alpha'; WorkingDirectory=''; Kind='summary_ps1'; TimeoutSec=30; NeedsZolaClosed=`$false; PromoteOnly=`$false; NeedsPythonPath=`$false; NeedsAndroid=`$false; DiscoverS=''; DiscoverT=''; ScriptRelative='tools\fake\infra.ps1'; Command=@() }
  )
}
"@ | Set-Content $suite -Encoding ASCII
        $floors = Join-Path $h.Root 'infra-floors.json'
        '{ "version":1, "suites": { "alpha": { "min_passed": 1, "allowed_skips": [] } } }' | Set-Content $floors -Encoding ASCII
        $r = Invoke-FakeGate -Harness $h -SuiteFile $suite -FloorsFile $floors
        $r.ExitCode -eq 2 -and $r.Result.overall -eq 'INFRA'
    } finally {
        Remove-Item -LiteralPath $h.Root -Recurse -Force -EA SilentlyContinue
    }
}

Assert-That 'E2E exit 3 DIRTY' {
    $h = New-FakeHarness -Dirty
    try {
        $suite = Join-Path $h.Root 'dirty-suites.psd1'
        @"
@{
  GateVersion='1.0.0-self'; JavaHome='C:\Program Files\Android\Android Studio\jbr'; AndroidHome='%LOCALAPPDATA%\Android\Sdk'
  ClearEnvNames=@('PYTHONPATH','HERMES_HOME','PYTHONHOME','VIRTUAL_ENV','PIP_INDEX_URL','PIP_EXTRA_INDEX_URL','PIP_REQUIRE_VIRTUALENV','PIP_TARGET','PIP_FIND_LINKS')
  Suites=@(
    @{ Name='alpha'; WorkingDirectory=''; Kind='summary_ps1'; TimeoutSec=30; NeedsZolaClosed=`$false; PromoteOnly=`$false; NeedsPythonPath=`$false; NeedsAndroid=`$false; DiscoverS=''; DiscoverT=''; ScriptRelative='tools\fake\pass.ps1'; Command=@() }
  )
}
"@ | Set-Content $suite -Encoding ASCII
        $floors = Join-Path $h.Root 'dirty-floors.json'
        '{ "version":1, "suites": { "alpha": { "min_passed": 1, "allowed_skips": [] } } }' | Set-Content $floors -Encoding ASCII
        $r = Invoke-FakeGate -Harness $h -SuiteFile $suite -FloorsFile $floors
        ($r.ExitCode -eq 3) -and ($r.Result.overall -eq 'DIRTY') -and `
            ([string]$r.Result.overall_reason -match 'uncommitted changes in the working tree')
    } finally {
        Remove-Item -LiteralPath $h.Root -Recurse -Force -EA SilentlyContinue
    }
}

Assert-That 'E2E INFRA with dirty tree mentions uncommitted changes' {
    $h = New-FakeHarness -Dirty
    try {
        $suite = Join-Path $h.Root 'infra-dirty-suites.psd1'
        @"
@{
  GateVersion='1.0.0-self'; JavaHome='C:\Program Files\Android\Android Studio\jbr'; AndroidHome='%LOCALAPPDATA%\Android\Sdk'
  ClearEnvNames=@('PYTHONPATH','HERMES_HOME','PYTHONHOME','VIRTUAL_ENV','PIP_INDEX_URL','PIP_EXTRA_INDEX_URL','PIP_REQUIRE_VIRTUALENV','PIP_TARGET','PIP_FIND_LINKS')
  Suites=@(
    @{ Name='alpha'; WorkingDirectory=''; Kind='summary_ps1'; TimeoutSec=30; NeedsZolaClosed=`$false; PromoteOnly=`$false; NeedsPythonPath=`$false; NeedsAndroid=`$false; DiscoverS=''; DiscoverT=''; ScriptRelative='tools\fake\infra.ps1'; Command=@() }
  )
}
"@ | Set-Content $suite -Encoding ASCII
        $floors = Join-Path $h.Root 'infra-dirty-floors.json'
        '{ "version":1, "suites": { "alpha": { "min_passed": 1, "allowed_skips": [] } } }' | Set-Content $floors -Encoding ASCII
        $r = Invoke-FakeGate -Harness $h -SuiteFile $suite -FloorsFile $floors
        ($r.ExitCode -eq 2) -and ($r.Result.overall -eq 'INFRA') -and `
            ([string]$r.Result.overall_reason -match 'uncommitted changes in the working tree')
    } finally {
        Remove-Item -LiteralPath $h.Root -Recurse -Force -EA SilentlyContinue
    }
}

Assert-That 'E2E exit 3 PARTIAL with -Only' {
    $h = New-FakeHarness
    try {
        $suite = Join-Path $h.Root 'partial-suites.psd1'
        @"
@{
  GateVersion='1.0.0-self'; JavaHome='C:\Program Files\Android\Android Studio\jbr'; AndroidHome='%LOCALAPPDATA%\Android\Sdk'
  ClearEnvNames=@('PYTHONPATH','HERMES_HOME','PYTHONHOME','VIRTUAL_ENV','PIP_INDEX_URL','PIP_EXTRA_INDEX_URL','PIP_REQUIRE_VIRTUALENV','PIP_TARGET','PIP_FIND_LINKS')
  Suites=@(
    @{ Name='alpha'; WorkingDirectory=''; Kind='summary_ps1'; TimeoutSec=30; NeedsZolaClosed=`$false; PromoteOnly=`$false; NeedsPythonPath=`$false; NeedsAndroid=`$false; DiscoverS=''; DiscoverT=''; ScriptRelative='tools\fake\pass.ps1'; Command=@() }
    @{ Name='beta'; WorkingDirectory=''; Kind='summary_ps1'; TimeoutSec=30; NeedsZolaClosed=`$false; PromoteOnly=`$false; NeedsPythonPath=`$false; NeedsAndroid=`$false; DiscoverS=''; DiscoverT=''; ScriptRelative='tools\fake\pass.ps1'; Command=@() }
  )
}
"@ | Set-Content $suite -Encoding ASCII
        $floors = Join-Path $h.Root 'partial-floors.json'
        '{ "version":1, "suites": { "alpha": { "min_passed": 1, "allowed_skips": [] }, "beta": { "min_passed": 1, "allowed_skips": [] } } }' | Set-Content $floors -Encoding ASCII
        $r = Invoke-FakeGate -Harness $h -SuiteFile $suite -FloorsFile $floors -Only @('alpha')
        $r.ExitCode -eq 3 -and $r.Result.overall -eq 'PARTIAL'
    } finally {
        Remove-Item -LiteralPath $h.Root -Recurse -Force -EA SilentlyContinue
    }
}

Assert-That 'E2E mid-run file change blocks PASS' {
    $h = New-FakeHarness
    try {
        $suite = Join-Path $h.Root 'mid-suites.psd1'
        @"
@{
  GateVersion='1.0.0-self'; JavaHome='C:\Program Files\Android\Android Studio\jbr'; AndroidHome='%LOCALAPPDATA%\Android\Sdk'
  ClearEnvNames=@('PYTHONPATH','HERMES_HOME','PYTHONHOME','VIRTUAL_ENV','PIP_INDEX_URL','PIP_EXTRA_INDEX_URL','PIP_REQUIRE_VIRTUALENV','PIP_TARGET','PIP_FIND_LINKS')
  Suites=@(
    @{ Name='alpha'; WorkingDirectory=''; Kind='summary_ps1'; TimeoutSec=30; NeedsZolaClosed=`$false; PromoteOnly=`$false; NeedsPythonPath=`$false; NeedsAndroid=`$false; DiscoverS=''; DiscoverT=''; ScriptRelative='tools\fake\midrun.ps1'; Command=@() }
  )
}
"@ | Set-Content $suite -Encoding ASCII
        $floors = Join-Path $h.Root 'mid-floors.json'
        '{ "version":1, "suites": { "alpha": { "min_passed": 1, "allowed_skips": [] } } }' | Set-Content $floors -Encoding ASCII
        $r = Invoke-FakeGate -Harness $h -SuiteFile $suite -FloorsFile $floors
        # Drift => INFRA exit 2 (cannot PASS)
        $r.ExitCode -ne 0 -and $r.Result.overall -ne 'PASS'
    } finally {
        Remove-Item -LiteralPath $h.Root -Recurse -Force -EA SilentlyContinue
    }
}

Assert-That 'E2E suite/floor mismatch is INFRA whole run' {
    $h = New-FakeHarness
    try {
        $suite = Join-Path $h.Root 'mm-suites.psd1'
        @"
@{
  GateVersion='1.0.0-self'; JavaHome='C:\Program Files\Android\Android Studio\jbr'; AndroidHome='%LOCALAPPDATA%\Android\Sdk'
  ClearEnvNames=@('PYTHONPATH','HERMES_HOME','PYTHONHOME','VIRTUAL_ENV','PIP_INDEX_URL','PIP_EXTRA_INDEX_URL','PIP_REQUIRE_VIRTUALENV','PIP_TARGET','PIP_FIND_LINKS')
  Suites=@(
    @{ Name='alpha'; WorkingDirectory=''; Kind='summary_ps1'; TimeoutSec=30; NeedsZolaClosed=`$false; PromoteOnly=`$false; NeedsPythonPath=`$false; NeedsAndroid=`$false; DiscoverS=''; DiscoverT=''; ScriptRelative='tools\fake\pass.ps1'; Command=@() }
  )
}
"@ | Set-Content $suite -Encoding ASCII
        $floors = Join-Path $h.Root 'mm-floors.json'
        '{ "version":1, "suites": { "alpha": { "min_passed": 1, "allowed_skips": [] }, "ghost": { "min_passed": 1, "allowed_skips": [] } } }' | Set-Content $floors -Encoding ASCII
        $r = Invoke-FakeGate -Harness $h -SuiteFile $suite -FloorsFile $floors
        $r.ExitCode -eq 2 -and $r.Result.overall -eq 'INFRA'
    } finally {
        Remove-Item -LiteralPath $h.Root -Recurse -Force -EA SilentlyContinue
    }
}

Assert-That 'E2E PYTHONPATH cleared so envcheck passes' {
    $h = New-FakeHarness
    $prev = $env:PYTHONPATH
    $env:PYTHONPATH = 'should-not-leak-into-suite'
    try {
        $suite = Join-Path $h.Root 'env-suites.psd1'
        @"
@{
  GateVersion='1.0.0-self'; JavaHome='C:\Program Files\Android\Android Studio\jbr'; AndroidHome='%LOCALAPPDATA%\Android\Sdk'
  ClearEnvNames=@('PYTHONPATH','HERMES_HOME','PYTHONHOME','VIRTUAL_ENV','PIP_INDEX_URL','PIP_EXTRA_INDEX_URL','PIP_REQUIRE_VIRTUALENV','PIP_TARGET','PIP_FIND_LINKS')
  Suites=@(
    @{ Name='alpha'; WorkingDirectory=''; Kind='summary_ps1'; TimeoutSec=30; NeedsZolaClosed=`$false; PromoteOnly=`$false; NeedsPythonPath=`$false; NeedsAndroid=`$false; DiscoverS=''; DiscoverT=''; ScriptRelative='tools\fake\envcheck.ps1'; Command=@() }
  )
}
"@ | Set-Content $suite -Encoding ASCII
        $floors = Join-Path $h.Root 'env-floors.json'
        '{ "version":1, "suites": { "alpha": { "min_passed": 1, "allowed_skips": [] } } }' | Set-Content $floors -Encoding ASCII
        Commit-HarnessTree -Root $h.Root -Message 'env suites'
        $r = Invoke-FakeGate -Harness $h -SuiteFile $suite -FloorsFile $floors
        $r.ExitCode -eq 0 -and $r.Result.overall -eq 'PASS'
    } finally {
        if ($null -eq $prev) { Remove-Item Env:PYTHONPATH -EA SilentlyContinue } else { $env:PYTHONPATH = $prev }
        Remove-Item -LiteralPath $h.Root -Recurse -Force -EA SilentlyContinue
    }
}

Assert-That 'E2E UpdateFloors refuses after -Only' {
    $h = New-FakeHarness
    try {
        $suite = Join-Path $h.Root 'uf-suites.psd1'
        @"
@{
  GateVersion='1.0.0-self'; JavaHome='C:\Program Files\Android\Android Studio\jbr'; AndroidHome='%LOCALAPPDATA%\Android\Sdk'
  ClearEnvNames=@('PYTHONPATH','HERMES_HOME','PYTHONHOME','VIRTUAL_ENV','PIP_INDEX_URL','PIP_EXTRA_INDEX_URL','PIP_REQUIRE_VIRTUALENV','PIP_TARGET','PIP_FIND_LINKS')
  Suites=@(
    @{ Name='alpha'; WorkingDirectory=''; Kind='summary_ps1'; TimeoutSec=30; NeedsZolaClosed=`$false; PromoteOnly=`$false; NeedsPythonPath=`$false; NeedsAndroid=`$false; DiscoverS=''; DiscoverT=''; ScriptRelative='tools\fake\pass.ps1'; Command=@() }
    @{ Name='beta'; WorkingDirectory=''; Kind='summary_ps1'; TimeoutSec=30; NeedsZolaClosed=`$false; PromoteOnly=`$false; NeedsPythonPath=`$false; NeedsAndroid=`$false; DiscoverS=''; DiscoverT=''; ScriptRelative='tools\fake\pass.ps1'; Command=@() }
  )
}
"@ | Set-Content $suite -Encoding ASCII
        $floors = Join-Path $h.Root 'uf-floors.json'
        '{ "version":1, "suites": { "alpha": { "min_passed": 1, "allowed_skips": [ {"id":"keep","reason":"me"} ] }, "beta": { "min_passed": 1, "allowed_skips": [] } } }' | Set-Content $floors -Encoding ASCII
        $before = Get-Content $floors -Raw
        $r = Invoke-FakeGate -Harness $h -SuiteFile $suite -FloorsFile $floors -Only @('alpha') -UpdateFloors
        $after = Get-Content $floors -Raw
        # refused: floors unchanged including allowed_skips
        ($after -eq $before) -and ($after -match 'keep')
    } finally {
        Remove-Item -LiteralPath $h.Root -Recurse -Force -EA SilentlyContinue
    }
}

Assert-That 'E2E UpdateFloors refuses to lower' {
    $h = New-FakeHarness
    try {
        $suite = Join-Path $h.Root 'low-suites.psd1'
        @"
@{
  GateVersion='1.0.0-self'; JavaHome='C:\Program Files\Android\Android Studio\jbr'; AndroidHome='%LOCALAPPDATA%\Android\Sdk'
  ClearEnvNames=@('PYTHONPATH','HERMES_HOME','PYTHONHOME','VIRTUAL_ENV','PIP_INDEX_URL','PIP_EXTRA_INDEX_URL','PIP_REQUIRE_VIRTUALENV','PIP_TARGET','PIP_FIND_LINKS')
  Suites=@(
    @{ Name='alpha'; WorkingDirectory=''; Kind='summary_ps1'; TimeoutSec=30; NeedsZolaClosed=`$false; PromoteOnly=`$false; NeedsPythonPath=`$false; NeedsAndroid=`$false; DiscoverS=''; DiscoverT=''; ScriptRelative='tools\fake\pass.ps1'; Command=@() }
  )
}
"@ | Set-Content $suite -Encoding ASCII
        $floors = Join-Path $h.Root 'low-floors.json'
        '{ "version":1, "suites": { "alpha": { "min_passed": 99, "allowed_skips": [ {"id":"keep","reason":"me"} ] } } }' | Set-Content $floors -Encoding ASCII
        # Suite will FAIL below floor first - UpdateFloors refused for non-PASS
        $r = Invoke-FakeGate -Harness $h -SuiteFile $suite -FloorsFile $floors -UpdateFloors
        $doc = Get-Content $floors -Raw | ConvertFrom-Json
        ([int]$doc.suites.alpha.min_passed -eq 99) -and ($null -ne $doc.suites.alpha.allowed_skips)
    } finally {
        Remove-Item -LiteralPath $h.Root -Recurse -Force -EA SilentlyContinue
    }
}

Assert-That 'E2E UpdateFloors refuses when any suite is not PASS' {
    $h = New-FakeHarness
    try {
        $suite = Join-Path $h.Root 'uf-infra-suites.psd1'
        @"
@{
  GateVersion='1.0.0-self'; JavaHome='C:\Program Files\Android\Android Studio\jbr'; AndroidHome='%LOCALAPPDATA%\Android\Sdk'
  ClearEnvNames=@('PYTHONPATH','HERMES_HOME','PYTHONHOME','VIRTUAL_ENV','PIP_INDEX_URL','PIP_EXTRA_INDEX_URL','PIP_REQUIRE_VIRTUALENV','PIP_TARGET','PIP_FIND_LINKS')
  Suites=@(
    @{ Name='alpha'; WorkingDirectory=''; Kind='summary_ps1'; TimeoutSec=30; NeedsZolaClosed=`$false; PromoteOnly=`$false; NeedsPythonPath=`$false; NeedsAndroid=`$false; DiscoverS=''; DiscoverT=''; ScriptRelative='tools\fake\pass.ps1'; Command=@() }
    @{ Name='beta'; WorkingDirectory=''; Kind='summary_ps1'; TimeoutSec=30; NeedsZolaClosed=`$false; PromoteOnly=`$false; NeedsPythonPath=`$false; NeedsAndroid=`$false; DiscoverS=''; DiscoverT=''; ScriptRelative='tools\fake\infra.ps1'; Command=@() }
  )
}
"@ | Set-Content $suite -Encoding ASCII
        $floors = Join-Path $h.Root 'uf-infra-floors.json'
        '{ "version":1, "suites": { "alpha": { "min_passed": 1, "allowed_skips": [ {"id":"keep","reason":"me"} ] }, "beta": { "min_passed": 1, "allowed_skips": [] } } }' | Set-Content $floors -Encoding ASCII
        $before = Get-Content $floors -Raw
        $r = Invoke-FakeGate -Harness $h -SuiteFile $suite -FloorsFile $floors -UpdateFloors
        $after = Get-Content $floors -Raw
        ($r.Result.overall -eq 'INFRA') -and ($after -eq $before) -and ($after -match 'keep')
    } finally {
        Remove-Item -LiteralPath $h.Root -Recurse -Force -EA SilentlyContinue
    }
}

Assert-That 'E2E UpdateFloors raise keeps allowed_skips' {
    $h = New-FakeHarness
    try {
        # Report pass=5 so floor 1 is raised; allowed_skips must survive the write.
        @'
Write-Host "==== SUMMARY pass=5 fail=0 ===="
exit 0
'@ | Set-Content (Join-Path $h.Tools 'raise.ps1') -Encoding ASCII
        $suite = Join-Path $h.Root 'uf-raise-suites.psd1'
        @"
@{
  GateVersion='1.0.0-self'; JavaHome='C:\Program Files\Android\Android Studio\jbr'; AndroidHome='%LOCALAPPDATA%\Android\Sdk'
  ClearEnvNames=@('PYTHONPATH','HERMES_HOME','PYTHONHOME','VIRTUAL_ENV','PIP_INDEX_URL','PIP_EXTRA_INDEX_URL','PIP_REQUIRE_VIRTUALENV','PIP_TARGET','PIP_FIND_LINKS')
  Suites=@(
    @{ Name='alpha'; WorkingDirectory=''; Kind='summary_ps1'; TimeoutSec=30; NeedsZolaClosed=`$false; PromoteOnly=`$false; NeedsPythonPath=`$false; NeedsAndroid=`$false; DiscoverS=''; DiscoverT=''; ScriptRelative='tools\fake\raise.ps1'; Command=@() }
  )
}
"@ | Set-Content $suite -Encoding ASCII
        $floors = Join-Path $h.Root 'uf-raise-floors.json'
        '{ "version":1, "suites": { "alpha": { "min_passed": 1, "allowed_skips": [ {"id":"keep","reason":"me"} ] } } }' | Set-Content $floors -Encoding ASCII
        Commit-HarnessTree -Root $h.Root -Message 'raise suites'
        $r = Invoke-FakeGate -Harness $h -SuiteFile $suite -FloorsFile $floors -UpdateFloors
        $raw = Get-Content $floors -Raw
        $doc = $raw | ConvertFrom-Json
        ($r.Result.overall -eq 'PASS' -or $r.Result.overall -eq 'DIRTY') -and `
            ([int]$doc.suites.alpha.min_passed -eq 5) -and `
            ($raw -match '"id"\s*:\s*"keep"') -and ($raw -match '"reason"\s*:\s*"me"')
    } finally {
        Remove-Item -LiteralPath $h.Root -Recurse -Force -EA SilentlyContinue
    }
}

Assert-That 'E2E timeout leaves no grandchild processes' {
    $h = New-FakeHarness
    try {
        $suite = Join-Path $h.Root 'to-suites.psd1'
        @"
@{
  GateVersion='1.0.0-self'; JavaHome='C:\Program Files\Android\Android Studio\jbr'; AndroidHome='%LOCALAPPDATA%\Android\Sdk'
  ClearEnvNames=@('PYTHONPATH','HERMES_HOME','PYTHONHOME','VIRTUAL_ENV','PIP_INDEX_URL','PIP_EXTRA_INDEX_URL','PIP_REQUIRE_VIRTUALENV','PIP_TARGET','PIP_FIND_LINKS')
  Suites=@(
    @{ Name='alpha'; WorkingDirectory=''; Kind='summary_ps1'; TimeoutSec=3; NeedsZolaClosed=`$false; PromoteOnly=`$false; NeedsPythonPath=`$false; NeedsAndroid=`$false; DiscoverS=''; DiscoverT=''; ScriptRelative='tools\fake\sleep_hang.ps1'; Command=@() }
  )
}
"@ | Set-Content $suite -Encoding ASCII
        $floors = Join-Path $h.Root 'to-floors.json'
        '{ "version":1, "suites": { "alpha": { "min_passed": 1, "allowed_skips": [] } } }' | Set-Content $floors -Encoding ASCII
        $beforePings = @(Get-Process -Name ping -EA SilentlyContinue | Select-Object -ExpandProperty Id)
        $r = Invoke-FakeGate -Harness $h -SuiteFile $suite -FloorsFile $floors
        Start-Sleep -Milliseconds 500
        $afterPings = @(Get-Process -Name ping -EA SilentlyContinue | Select-Object -ExpandProperty Id)
        $newPings = @($afterPings | Where-Object { $beforePings -notcontains $_ })
        ($r.ExitCode -eq 2) -and ($r.Result.suites[0].result -eq 'INFRA') -and ($newPings.Count -eq 0)
    } finally {
        Remove-Item -LiteralPath $h.Root -Recurse -Force -EA SilentlyContinue
    }
}

Assert-That 'E2E -ZolaRunningProbe partway: earlier runs, phone INFRA, no marker' {
    $h = New-FakeHarness
    try {
        $marker = Join-Path $h.Root 'phone-ran.marker'
        @'
Set-Content -Path (Join-Path $PSScriptRoot '..\..\phone-ran.marker') -Value 'ran' -Encoding ASCII
Write-Host "==== SUMMARY pass=1 fail=0 ===="
exit 0
'@ | Set-Content (Join-Path $h.Tools 'phone_mark.ps1') -Encoding ASCII
        $suite = Join-Path $h.Root 'probe-suites.psd1'
        @"
@{
  GateVersion='1.0.0-self'; JavaHome='C:\Program Files\Android\Android Studio\jbr'; AndroidHome='%LOCALAPPDATA%\Android\Sdk'
  ClearEnvNames=@('PYTHONPATH','HERMES_HOME','PYTHONHOME','VIRTUAL_ENV','PIP_INDEX_URL','PIP_EXTRA_INDEX_URL','PIP_REQUIRE_VIRTUALENV','PIP_TARGET','PIP_FIND_LINKS')
  Suites=@(
    @{ Name='alpha'; WorkingDirectory=''; Kind='summary_ps1'; TimeoutSec=30; NeedsZolaClosed=`$false; PromoteOnly=`$false; NeedsPythonPath=`$false; NeedsAndroid=`$false; DiscoverS=''; DiscoverT=''; ScriptRelative='tools\fake\pass.ps1'; Command=@() }
    @{ Name='zola_phone'; WorkingDirectory=''; Kind='summary_ps1'; TimeoutSec=30; NeedsZolaClosed=`$true; PromoteOnly=`$false; NeedsPythonPath=`$false; NeedsAndroid=`$false; DiscoverS=''; DiscoverT=''; ScriptRelative='tools\fake\phone_mark.ps1'; Command=@() }
  )
}
"@ | Set-Content $suite -Encoding ASCII
        $floors = Join-Path $h.Root 'probe-floors.json'
        '{ "version":1, "suites": { "alpha": { "min_passed": 1, "allowed_skips": [] }, "zola_phone": { "min_passed": 1, "allowed_skips": [] } } }' | Set-Content $floors -Encoding ASCII
        Commit-HarnessTree -Root $h.Root -Message 'probe suites'
        $probeState = Join-Path $h.Root 'probe-state.txt'
        $probeLog = Join-Path $h.Root 'probe-calls.log'
        Set-Content -LiteralPath $probeState -Value '0' -Encoding ASCII
        Set-Content -LiteralPath $probeLog -Value '' -Encoding ASCII
        $probePs1 = Join-Path $h.Root 'zola-probe.ps1'
        @"
`$state = '$($probeState.Replace('''', ''''''))'
`$log = '$($probeLog.Replace('''', ''''''))'
`$n = [int](Get-Content -LiteralPath `$state -Raw).Trim()
`$n++
Set-Content -LiteralPath `$state -Value ([string]`$n) -Encoding ASCII
Add-Content -LiteralPath `$log -Value ("call=`$n suite-tick") -Encoding ASCII
# First call false; subsequent calls true (partway hold)
return (`$n -gt 1)
"@ | Set-Content -LiteralPath $probePs1 -Encoding ASCII
        $r = Invoke-FakeGate -Harness $h -SuiteFile $suite -FloorsFile $floors -ZolaRunningProbePath $probePs1
        $alpha = @($r.Result.suites | Where-Object { $_.name -eq 'alpha' })[0]
        $phone = @($r.Result.suites | Where-Object { $_.name -eq 'zola_phone' })[0]
        $calls = [int](Get-Content -LiteralPath $probeState -Raw).Trim()
        $ov = $r.Result.overrides
        ($alpha.result -eq 'PASS') -and `
            ($phone.result -eq 'INFRA') -and ($phone.reason -match 'running') -and `
            (-not (Test-Path -LiteralPath $marker)) -and `
            ($calls -ge 2) -and `
            ([bool]$ov.zola_running_probe) -and `
            ($r.ExitCode -eq 2)
    } finally {
        Remove-Item -LiteralPath $h.Root -Recurse -Force -EA SilentlyContinue
    }
}

$summary = '==== SUMMARY pass={0} fail={1} ====' -f $script:Pass, $script:Fail
Write-Host $summary
# Persist floor hint
Write-Host ("SELFTEST_COUNT pass={0}" -f $script:Pass)
if ($script:Fail -gt 0) { exit 1 } else { exit 0 }
