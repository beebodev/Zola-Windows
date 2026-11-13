#Requires -Version 5.1
<#
.SYNOPSIS
  PROC1-GATE one-command test gate (FAIL / INFRA / floors). Phase 4.
#>
[CmdletBinding()]
param(
  [string]$RepoRoot,
  [switch]$Promote,
  [string[]]$Only,
  [switch]$UpdateFloors,
  [string]$Json,
  [switch]$SkipSelf,
  $ZolaRunningProbe = $null,
  [string]$SuiteFile,
  [string]$FloorsFile
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$gateDir = $PSScriptRoot
$outRoot = Join-Path $env:TEMP 'zola-test-gate'
New-Item -ItemType Directory -Force -Path $outRoot | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$runDir = Join-Path $outRoot $stamp
New-Item -ItemType Directory -Force -Path $runDir | Out-Null
$debugLog = Join-Path $runDir 'gate-debug.log'
function Write-GateDebug([string]$Msg) {
    Add-Content -LiteralPath $debugLog -Value ("{0} {1}" -f (Get-Date -Format 'o'), $Msg)
}

try {
Import-Module (Join-Path $gateDir 'TestGate.Common.psm1') -Force -DisableNameChecking
Write-GateDebug 'module imported'

if (-not $RepoRoot) {
    $RepoRoot = (Resolve-Path (Join-Path $gateDir '..\..')).Path
}
$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
Write-GateDebug "repo=$RepoRoot"

$overrideSuiteFile = $PSBoundParameters.ContainsKey('SuiteFile') -and [bool]$SuiteFile
$overrideFloorsFile = $PSBoundParameters.ContainsKey('FloorsFile') -and [bool]$FloorsFile
$overrideZolaProbe = $PSBoundParameters.ContainsKey('ZolaRunningProbe') -and ($null -ne $ZolaRunningProbe)

if (-not $SuiteFile) { $SuiteFile = Join-Path $gateDir 'Suites.psd1' }
elseif (-not [IO.Path]::IsPathRooted($SuiteFile)) { $SuiteFile = Join-Path $gateDir $SuiteFile }
if (-not $FloorsFile) { $FloorsFile = Join-Path $gateDir 'floors.json' }
elseif (-not [IO.Path]::IsPathRooted($FloorsFile)) { $FloorsFile = Join-Path $gateDir $FloorsFile }

# Path-string probes (E2E / Start-Process cannot pass scriptblocks)
if ($overrideZolaProbe -and ($ZolaRunningProbe -is [string])) {
    $probePath = [string]$ZolaRunningProbe
    if (-not [IO.Path]::IsPathRooted($probePath)) { $probePath = Join-Path $gateDir $probePath }
    if (-not (Test-Path -LiteralPath $probePath)) { throw "ZolaRunningProbe path not found: $probePath" }
    $ZolaRunningProbe = [scriptblock]::Create("& '$($probePath.Replace('''', ''''''))'")
}

$testOverrides = [ordered]@{
    suite_file         = $overrideSuiteFile
    floors_file        = $overrideFloorsFile
    zola_running_probe = $overrideZolaProbe
}
if ($overrideSuiteFile -or $overrideFloorsFile -or $overrideZolaProbe) {
    Write-Host 'TEST OVERRIDES IN USE - not merge evidence'
    Write-Host ("  SuiteFile={0} FloorsFile={1} ZolaRunningProbe={2}" -f `
        $overrideSuiteFile, $overrideFloorsFile, $overrideZolaProbe)
}

$defs = Import-PowerShellDataFile -Path $SuiteFile
$floorsDoc = Get-Content -LiteralPath $FloorsFile -Raw -Encoding UTF8 | ConvertFrom-Json
Write-GateDebug ("suites={0}" -f @($defs.Suites).Count)

$javaHome = Expand-GatePath $defs.JavaHome
$androidHome = Expand-GatePath $defs.AndroidHome
$hermesRoot = Get-HermesRoot
$hermesPython = if ($hermesRoot) { Get-HermesPython -HermesRoot $hermesRoot } else { $null }
Write-GateDebug "hermes=$hermesRoot python=$hermesPython"

if (-not $Json) {
    $Json = Join-Path $runDir 'result.json'
}

$gateVersion = [string]$defs.GateVersion
$startTime = Get-Date
$before = Get-CommitRecord -RepoRoot $RepoRoot
Add-HermesRecord -Record $before -HermesRoot $hermesRoot

$toolVersions = Get-ToolVersions -JavaHome $javaHome -AndroidHome $androidHome -HermesPython $hermesPython
$androidCompanion = Join-Path $RepoRoot 'android-companion'
$gradlewPath = Join-Path $androidCompanion 'gradlew.bat'
if (Test-Path -LiteralPath $gradlewPath) {
    try {
        $gwVer = & $gradlewPath --version 2>&1 | Out-String
        if ($gwVer -match 'Gradle\s+([\d.]+)') {
            $toolVersions['gradle'] = $Matches[1]
        } elseif ($gwVer) {
            $toolVersions['gradle'] = ($gwVer.Trim() -split "`r?`n" | Select-Object -First 1)
        }
    } catch {
        Write-GateDebug "gradle --version failed: $($_.Exception.Message)"
    }
}

# G-COVERAGE
$definedNames = @($defs.Suites | ForEach-Object { $_.Name })
$floorNames = @($floorsDoc.suites.PSObject.Properties.Name)
$coverageMismatch = $false
$coverageReason = ''
foreach ($n in $definedNames) {
    if ($floorNames -notcontains $n) {
        $coverageMismatch = $true
        $coverageReason = "suite '$n' missing from floors.json"
        break
    }
}
if (-not $coverageMismatch) {
    foreach ($n in $floorNames) {
        if ($definedNames -notcontains $n) {
            $coverageMismatch = $true
            $coverageReason = "floor '$n' has no suite definition"
            break
        }
    }
}

$partial = $false
$selected = @($defs.Suites)
$onlyNames = @()
if ($Only) {
    foreach ($item in @($Only)) {
        foreach ($piece in @("$item".Split(','))) {
            $t = $piece.Trim()
            if ($t) { $onlyNames += $t }
        }
    }
}
if ($onlyNames.Count -gt 0) {
    $partial = $true
    $selected = @($defs.Suites | Where-Object { $onlyNames -contains $_.Name })
}
if (-not $Promote) {
    $selected = @($selected | Where-Object {
        -not ($_.ContainsKey('PromoteOnly') -and $_.PromoteOnly)
    })
}
if ($SkipSelf) {
    $selected = @($selected | Where-Object { $_.Name -ne 'gate_self' })
}

function Resolve-ZolaRunning {
    if ($null -ne $ZolaRunningProbe) {
        return [bool](& $ZolaRunningProbe)
    }
    return Test-ZolaRunningForGate
}

function Get-ZolaHeldReason {
    if ($overrideZolaProbe) {
        return 'stable is running; close Zola for a clean run'
    }
    return Get-ZolaRunningInfraReason
}

$suiteResults = @()
$suggestedFloors = @{}

Write-GateDebug ("selected={0}" -f (($selected | ForEach-Object { $_.Name }) -join ','))
foreach ($suite in $selected) {
    $name = $suite.Name
    Write-GateDebug "start suite $name"
    $floor = $floorsDoc.suites.$name
    $logOut = Join-Path $runDir "$name.stdout.log"
    $logErr = Join-Path $runDir "$name.stderr.log"
    $suiteStart = Get-Date
    $suiteStartUtc = $suiteStart.ToUniversalTime()
    $row = [ordered]@{
        name           = $name
        result         = 'INFRA'
        passed         = 0
        failed         = 0
        skipped        = 0
        floor          = if ($floor) { [int]$floor.min_passed } else { 0 }
        seconds        = 0
        reason         = ''
        exit_code      = $null
        interpreter    = $null
        completion     = $null
    }

    if ($coverageMismatch) {
        $row.result = 'INFRA'
        $row.reason = $coverageReason
        $row.seconds = 0
        $suiteResults += [pscustomobject]$row
        continue
    }

    # With -ZolaRunningProbe, call before every suite so a partway flip is observable.
    # Without probe, only query when the suite requires Zola closed.
    $zolaHeld = $false
    if ($overrideZolaProbe) {
        $zolaHeld = Resolve-ZolaRunning
    } elseif ($suite.NeedsZolaClosed) {
        $zolaHeld = Resolve-ZolaRunning
    }
    if ($suite.NeedsZolaClosed -and $zolaHeld) {
        $row.result = 'INFRA'
        $row.reason = Get-ZolaHeldReason
        $row.seconds = [Math]::Round(((Get-Date) - $suiteStart).TotalSeconds, 3)
        $suiteResults += [pscustomobject]$row
        continue
    }

    $cwd = $RepoRoot
    if ($suite.WorkingDirectory) {
        $cwd = Join-Path $RepoRoot $suite.WorkingDirectory
    }

    $extraEnv = @{}
    $filePath = $null
    $arguments = $null
    $infra = ''

    switch ($suite.Kind) {
        'checks' {
            $filePath = 'dotnet'
            $arguments = ($suite.Command | Select-Object -Skip 1) -join ' '
            if ($arguments -match 'drift-dry-run') {
                $infra = 'refusing --drift-dry-run'
            }
            $row.interpreter = "dotnet $((Get-Command dotnet -ErrorAction SilentlyContinue).Source)"
        }
        'summary_ps1' {
            $scriptPath = Join-Path $RepoRoot $suite.ScriptRelative
            if (-not (Test-Path -LiteralPath $scriptPath)) {
                $infra = "missing script $scriptPath"
            } else {
                $filePath = 'powershell'
                $arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`""
            }
            $row.interpreter = 'powershell'
        }
        'gate_self' {
            $scriptPath = Join-Path $RepoRoot $suite.ScriptRelative
            $filePath = 'powershell'
            $arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`""
            $row.interpreter = 'powershell'
        }
        'unittest' {
            if (-not $hermesRoot -or -not (Test-Path -LiteralPath $hermesRoot)) {
                $infra = 'ZOLA_HERMES_ROOT (User) missing or path not found'
            } elseif (-not (Test-Path -LiteralPath $hermesPython)) {
                $infra = "venv python missing: $hermesPython"
            } else {
                $filePath = $hermesPython
                $arguments = "-m unittest discover -s $($suite.DiscoverS) -t $($suite.DiscoverT) -v"
                if ($suite.NeedsPythonPath) {
                    $extraEnv['PYTHONPATH'] = $hermesRoot
                }
                $row.interpreter = $hermesPython
                try { $row.interpreter = "$hermesPython ($(& $hermesPython --version 2>&1))" } catch {}
            }
        }
        'kotlin_unit' {
            if (-not (Test-Path -LiteralPath $javaHome)) {
                $infra = "JAVA_HOME/JBR missing: $javaHome"
            } elseif (-not (Test-Path -LiteralPath $androidHome)) {
                $infra = "ANDROID_HOME missing: $androidHome"
            } else {
                $extraEnv['JAVA_HOME'] = $javaHome
                $extraEnv['ANDROID_HOME'] = $androidHome
                $resultDir = Join-Path $cwd 'app\build\test-results\testDebugUnitTest'
                if (Test-Path -LiteralPath $resultDir) {
                    Remove-Item -LiteralPath $resultDir -Recurse -Force -ErrorAction SilentlyContinue
                }
                $gw = Join-Path $cwd 'gradlew.bat'
                $filePath = $gw
                # --no-daemon: avoid leftover Gradle daemon under the job object
                $arguments = 'testDebugUnitTest --offline --rerun --no-daemon'
                $row.interpreter = "JAVA_HOME=$javaHome ANDROID_HOME=$androidHome"
            }
        }
        'assemble_debug' {
            if (-not (Test-Path -LiteralPath $javaHome)) {
                $infra = "JAVA_HOME/JBR missing: $javaHome"
            } elseif (-not (Test-Path -LiteralPath $androidHome)) {
                $infra = "ANDROID_HOME missing: $androidHome"
            } else {
                $extraEnv['JAVA_HOME'] = $javaHome
                $extraEnv['ANDROID_HOME'] = $androidHome
                $gw = Join-Path $cwd 'gradlew.bat'
                $filePath = $gw
                # --no-daemon: avoid leftover Gradle daemon under the job object
                $arguments = 'assembleDebug --offline --no-daemon'
                $row.interpreter = "JAVA_HOME=$javaHome ANDROID_HOME=$androidHome"
            }
        }
        default {
            $infra = "unknown kind $($suite.Kind)"
        }
    }

    if ($infra) {
        $row.result = 'INFRA'
        $row.reason = $infra
        $row.seconds = [Math]::Round(((Get-Date) - $suiteStart).TotalSeconds, 3)
        $suiteResults += [pscustomobject]$row
        continue
    }

    $envMap = New-ClearedSuiteEnvironment -SuiteDef $defs -Extra $extraEnv

    $handle = Start-GateProcess -FilePath $filePath -Arguments $arguments -WorkingDirectory $cwd `
        -Environment $envMap -StdOutPath $logOut -StdErrPath $logErr
    $waited = Wait-GateProcess -Handle $handle -TimeoutSec ([int]$suite.TimeoutSec)
    $row.seconds = [Math]::Round(((Get-Date) - $suiteStart).TotalSeconds, 3)
    $row.exit_code = $waited.ExitCode
    $text = $waited.Combined

    if ($waited.TimedOut) {
        $row.result = 'INFRA'
        $row.reason = "timeout after $($suite.TimeoutSec)s"
        $suiteResults += [pscustomobject]$row
        continue
    }

    if (@($waited.Leftovers).Count -gt 0) {
        $names = @($waited.Leftovers | ForEach-Object { $_.Name }) -join ', '
        $row.result = 'INFRA'
        $row.reason = "left processes running: $names"
        $suiteResults += [pscustomobject]$row
        continue
    }

    $parsedPassed = 0
    $parsedFailed = 0
    $parsedSkipped = 0
    $skipItems = @()
    $hasMarker = $false
    $zeroFail = $false
    $exitSuccess = ($waited.ExitCode -eq 0)
    $parseReason = ''

    switch ($suite.Kind) {
        'unittest' {
            $p = Parse-UnittestOutput -Text $text -ExitCode $waited.ExitCode
            $hasMarker = $p.Marker
            $parsedPassed = $p.Passed
            $parsedFailed = $p.Failed
            $parsedSkipped = $p.Skipped
            $skipItems = @($p.SkipItems)
            $zeroFail = $p.ZeroFail
            $exitSuccess = $p.Ok -and ($waited.ExitCode -eq 0)
            $row.completion = "Ran $($p.Ran)"
        }
        'summary_ps1' {
            $p = Parse-SummaryPs1 -Text $text
            $hasMarker = $p.Marker
            $parsedPassed = $p.Passed
            $parsedFailed = $p.Failed
            $parsedSkipped = $p.Skipped
            $skipItems = @($p.SkipItems)
            $exitSuccess = ($waited.ExitCode -eq 0) -and ($p.Failed -eq 0)
            $row.completion = 'SUMMARY'
        }
        'gate_self' {
            $p = Parse-SummaryPs1 -Text $text
            $hasMarker = $p.Marker
            $parsedPassed = $p.Passed
            $parsedFailed = $p.Failed
            $parsedSkipped = $p.Skipped
            $skipItems = @($p.SkipItems)
            $exitSuccess = ($waited.ExitCode -eq 0) -and ($p.Failed -eq 0)
            $row.completion = 'SUMMARY'
        }
        'checks' {
            $p = Parse-ChecksOutput -Text $text -ExitCode $waited.ExitCode
            $hasMarker = $p.Marker
            $parsedPassed = $p.Passed
            $parsedFailed = $p.Failed
            $parsedSkipped = $p.Skipped
            $skipItems = @($p.SkipItems)
            $exitSuccess = $p.ExitOk -and ($p.Failed -eq 0)
            $row.completion = 'coverage'
        }
        'kotlin_unit' {
            $resultDir = Join-Path $cwd 'app\build\test-results\testDebugUnitTest'
            $p = Parse-KotlinXml -ResultDir $resultDir -RunStartUtc $suiteStartUtc
            # Marker = fresh XML + Gradle exited (do not require BUILD SUCCESSFUL)
            $hasMarker = [bool]$p.Marker
            $parsedPassed = $p.Passed
            $parsedFailed = $p.Failed
            $parsedSkipped = $p.Skipped
            $skipItems = @($p.SkipItems)
            # XML failures => FAIL; Gradle fail with no fresh XML => INFRA (below)
            $exitSuccess = ($p.Failed -eq 0)
            if (-not $hasMarker) {
                if ($waited.ExitCode -ne 0) {
                    $parseReason = 'Gradle failed with no fresh XML'
                } elseif ($p.Reason) {
                    $parseReason = $p.Reason
                }
            }
            $row.completion = 'JUnit XML'
        }
        'assemble_debug' {
            $hasMarker = ($text -match 'BUILD SUCCESSFUL')
            $parsedPassed = if ($hasMarker -and $waited.ExitCode -eq 0) { 1 } else { 0 }
            $parsedFailed = if ($waited.ExitCode -ne 0 -or -not $hasMarker) { 1 } else { 0 }
            $exitSuccess = ($waited.ExitCode -eq 0) -and $hasMarker
            $row.completion = 'BUILD SUCCESSFUL'
        }
    }

    $row.passed = $parsedPassed
    $row.failed = $parsedFailed
    $row.skipped = $parsedSkipped

    if (-not $floor) {
        $row.result = 'INFRA'
        $row.reason = "suite '$name' missing from floors.json"
    } else {
        $class = Classify-SuiteResult -Floor $floor -InfraReason $parseReason `
            -HasMarker $hasMarker -Passed $parsedPassed -Failed $parsedFailed -Skipped $parsedSkipped `
            -SkipItems $skipItems -ZeroTestsFail $zeroFail -ExitSuccess $exitSuccess
        $row.result = $class.Result
        $row.reason = $class.Reason
    }
    $suggestedFloors[$name] = $parsedPassed
    $suiteResults += [pscustomobject]$row
}

$after = Get-CommitRecord -RepoRoot $RepoRoot
Add-HermesRecord -Record $after -HermesRoot $hermesRoot
$endTime = Get-Date

$anyFail = @($suiteResults | Where-Object { $_.result -eq 'FAIL' }).Count -gt 0
$anyInfra = @($suiteResults | Where-Object { $_.result -eq 'INFRA' }).Count -gt 0
$allPass = -not $anyFail -and -not $anyInfra -and ($suiteResults.Count -gt 0)
$dirty = [bool]$before.dirty -or [bool]$after.dirty
$headDrift = ($before.head -ne $after.head) -or ((@($before.porcelain) -join "`n") -ne (@($after.porcelain) -join "`n"))

$overall = 'FAIL'
$exitCode = 1
$overallReason = ''
if ($headDrift) {
    $overall = 'INFRA'
    $exitCode = 2
    $overallReason = 'HEAD or change set drifted during the run'
} elseif ($anyFail) {
    $overall = 'FAIL'
    $exitCode = 1
    $overallReason = 'one or more suites FAIL'
} elseif ($anyInfra) {
    $overall = 'INFRA'
    $exitCode = 2
    $overallReason = 'one or more suites INFRA'
} elseif ($allPass -and ($dirty -or $partial)) {
    $overall = if ($partial) { 'PARTIAL' } else { 'DIRTY' }
    $exitCode = 3
    $overallReason = if ($partial) { 'PARTIAL (-Only)' } else { 'uncommitted changes in the working tree' }
} elseif ($allPass -and -not $dirty -and -not $partial) {
    $overall = 'PASS'
    $exitCode = 0
    $overallReason = ''
} else {
    $overall = 'INFRA'
    $exitCode = 2
    $overallReason = 'no suites ran'
}

# When the tree is dirty, say so on OVERALL even if the primary result is INFRA/FAIL/etc.
$overallDisplay = $overallReason
if ($dirty -and $overall -ne 'DIRTY' -and $overall -ne 'PARTIAL') {
    $dirtyNote = 'uncommitted changes in the working tree'
    if ($overallDisplay) {
        $overallDisplay = "$overallDisplay - $dirtyNote"
    } else {
        $overallDisplay = $dirtyNote
    }
}

# -UpdateFloors: complete run only; every suite PASS; no head drift; never lower; preserve allowed_skips
if ($UpdateFloors) {
    if ($partial) {
        Write-Host 'UpdateFloors refused: complete run required (not -Only)'
    } elseif ($headDrift) {
        Write-Host 'UpdateFloors refused: HEAD or change set drifted during the run'
    } elseif (-not $allPass) {
        Write-Host "UpdateFloors refused: not every suite PASS (overall=$overall)"
    } else {
        $newDoc = Get-Content -LiteralPath $FloorsFile -Raw -Encoding UTF8 | ConvertFrom-Json
        $lowered = $false
        $raised = $false
        foreach ($name in $suggestedFloors.Keys) {
            $cur = [int]$newDoc.suites.$name.min_passed
            $sug = [int]$suggestedFloors[$name]
            if ($sug -lt $cur) {
                Write-Host "UpdateFloors refused to lower $name ($cur -> $sug)"
                $lowered = $true
            } elseif ($sug -gt $cur) {
                $newDoc.suites.$name.min_passed = $sug
                Write-Host "UpdateFloors raise $name $cur -> $sug"
                $raised = $true
            }
        }
        if (-not $lowered) {
            $tmp = "$FloorsFile.tmp"
            # Manual JSON so single-element allowed_skips arrays survive (PS 5.1 ConvertTo-Json unwraps them)
            $sb = New-Object System.Text.StringBuilder
            [void]$sb.AppendLine('{')
            [void]$sb.AppendLine(('  "version": {0},' -f [int]$newDoc.version))
            [void]$sb.AppendLine('  "suites": {')
            $suiteProps = @($newDoc.suites.PSObject.Properties)
            for ($si = 0; $si -lt $suiteProps.Count; $si++) {
                $sp = $suiteProps[$si]
                $minP = [int]$sp.Value.min_passed
                [void]$sb.AppendLine(('    "{0}": {{' -f $sp.Name))
                [void]$sb.AppendLine(('      "min_passed": {0},' -f $minP))
                [void]$sb.AppendLine('      "allowed_skips": [')
                $skips = @($sp.Value.allowed_skips)
                for ($ki = 0; $ki -lt $skips.Count; $ki++) {
                    $sk = $skips[$ki]
                    if ($null -eq $sk) { continue }
                    $id = ([string]$sk.id).Replace('\', '\\').Replace('"', '\"')
                    $reason = ([string]$sk.reason).Replace('\', '\\').Replace('"', '\"')
                    $comma = if ($ki -lt $skips.Count - 1) { ',' } else { '' }
                    [void]$sb.AppendLine(('        {{ "id": "{0}", "reason": "{1}" }}{2}' -f $id, $reason, $comma))
                }
                [void]$sb.AppendLine('      ]')
                $sComma = if ($si -lt $suiteProps.Count - 1) { ',' } else { '' }
                [void]$sb.AppendLine(('    }}{0}' -f $sComma))
            }
            [void]$sb.AppendLine('  }')
            [void]$sb.AppendLine('}')
            $jsonOut = $sb.ToString()
            $utf8Bom = New-Object System.Text.UTF8Encoding $true
            [System.IO.File]::WriteAllText($tmp, $jsonOut, $utf8Bom)
            Move-Item -LiteralPath $tmp -Destination $FloorsFile -Force
            if ($raised) {
                Write-Host 'floors.json updated; tree is now dirty - run again on a committed tip for overall PASS'
            } else {
                Write-Host 'floors.json unchanged (no raises)'
            }
        }
    }
}

# Summary table
Write-Host ''
Write-Host ("{0,-16} {1,-6} {2,8} {3,8} {4,8} {5,6} {6,8}  {7}" -f 'SUITE', 'RESULT', 'PASS', 'FAIL', 'SKIP', 'FLOOR', 'SEC', 'REASON')
Write-Host ('-' * 100)
foreach ($r in $suiteResults) {
    Write-Host ("{0,-16} {1,-6} {2,8} {3,8} {4,8} {5,6} {6,8}  {7}" -f `
        $r.name, $r.result, $r.passed, $r.failed, $r.skipped, $r.floor, $r.seconds, $r.reason)
}
Write-Host ('-' * 100)
if ($overallDisplay) {
    Write-Host ("OVERALL {0} exit={1} - {2}" -f $overall, $exitCode, $overallDisplay)
} else {
    Write-Host ("OVERALL {0} exit={1}" -f $overall, $exitCode)
}
Write-Host ("commit before={0} dirty={1} after={2} dirty={3}" -f $before.head, $before.dirty, $after.head, $after.dirty)
Write-Host ("result json: {0}" -f $Json)
Write-Host ("logs: {0}" -f $runDir)

$resultObj = [ordered]@{
    gate_version   = $gateVersion
    machine        = $env:COMPUTERNAME
    start          = $startTime.ToString('o')
    end            = $endTime.ToString('o')
    overall        = $overall
    exit_code      = $exitCode
    overall_reason = $overallDisplay
    partial        = $partial
    promote        = [bool]$Promote
    overrides      = $testOverrides
    paths          = [ordered]@{
        hermes_root   = $hermesRoot
        hermes_python = $hermesPython
        java_home     = $javaHome
        android_home  = $androidHome
        repo_root     = $RepoRoot
        suite_file    = $SuiteFile
        floors_file   = $FloorsFile
        run_dir       = $runDir
    }
    versions      = $toolVersions
    commit_before = $before
    commit_after  = $after
    suites        = @($suiteResults)
}
$jsonText = ($resultObj | ConvertTo-Json -Depth 8)
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($Json, $jsonText, $utf8NoBom)
Write-GateDebug "done exit=$exitCode"

exit $exitCode

} catch {
    $err = $_ | Out-String
    try { Write-GateDebug "ERROR: $err" } catch {}
    Write-Host "GATE FATAL: $($_.Exception.Message)"
    Write-Host $err
    exit 2
}