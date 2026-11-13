# PROC1-DEV: isolation check. Open handles are a Process Monitor capture, not this script.
# Phase 6 only, and only if Brian approves the Sysinternals download and an administrator run.
# Filter: Path contains \hermes\profiles\zola\ and not \hermes-dev\,
# or Path contains \ZolaClient\ and not \ZolaClient-dev\.
# Process is the smoke Zola.Client.exe under %TEMP%\proc1-dev-smoke\ and its python.exe children.
# Review Process Name, PID, Operation, Path, and Result. Do not keep Detail. No file contents.
# Delete the capture afterwards.
# Live SQLite: AfterClose compares hashes and does not open a database.
# Invoke-LiveSqliteReadOnly is the only opener. It uses mode=ro&immutable=1 and refuses while stable runs.
#Requires -Version 5.1
param(
    [ValidateSet('WhileRunning', 'AfterClose')]
    [string]$Mode = 'WhileRunning',
    [string]$LocalAppData = $env:LOCALAPPDATA,
    [string]$BeforeMap,
    [string]$AfterMap,
    [scriptblock]$StableProbe
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'DevCommon.psm1') -Force

function Test-StableIsRunning {
    param([scriptblock]$Probe)
    if ($null -ne $Probe) { return [bool](& $Probe) }
    foreach ($proc in @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)) {
        $cmd = [string]$proc.CommandLine
        if (Test-FinishedProfileToken -CommandLine $cmd -ProfileName 'zola') { return $true }
        $name = [string]$proc.Name
        if ($name -match '^(?i)Zola\.Client(\.exe)?$') {
            $exe = [string]$proc.ExecutablePath
            if ($exe -notmatch '(?i)proc1-dev-smoke' -and $exe -notmatch '(?i)ZolaClient-dev') { return $true }
        }
    }
    return $false
}

function Invoke-LiveSqliteReadOnly {
    param(
        [Parameter(Mandatory)][string]$Database,
        [Parameter(Mandatory)][string]$Query,
        [scriptblock]$Probe
    )
    if ($Query -notmatch '^(?is)\s*select\b') {
        return [pscustomobject]@{ Ok = $false; Reason = 'refusing: live SQLite queries are select only'; Rows = @() }
    }
    if (Test-StableIsRunning -Probe $Probe) {
        return [pscustomobject]@{ Ok = $false; Reason = 'refusing: stable is running'; Rows = @() }
    }
    $python = 'C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe'
    $code = @'
import sqlite3
import sys
from pathlib import Path
db = Path(sys.argv[1])
uri = db.resolve().as_uri() + "?mode=ro&immutable=1"
conn = sqlite3.connect(uri, uri=True)
try:
    cur = conn.execute(sys.argv[2])
    for row in cur.fetchall():
        print("\t".join("" if value is None else str(value) for value in row))
finally:
    conn.close()
'@
    $temp = Join-Path $env:TEMP ("proc1-dev-sqlite-" + [guid]::NewGuid().ToString('N') + '.py')
    $utf8 = New-Object System.Text.UTF8Encoding $false
    [IO.File]::WriteAllText($temp, $code, $utf8)
    try {
        $rows = @(& $python $temp $Database $Query)
        $exit = $LASTEXITCODE
    } finally {
        Remove-Item -LiteralPath $temp -Force -ErrorAction SilentlyContinue
    }
    if ($exit -ne 0) {
        return [pscustomobject]@{ Ok = $false; Reason = 'refusing: sqlite open failed'; Rows = @() }
    }
    return [pscustomobject]@{ Ok = $true; Reason = ''; Rows = @($rows) }
}

if ($MyInvocation.InvocationName -eq '.') { return }

if ($Mode -eq 'AfterClose') {
    if (-not $BeforeMap -or -not $AfterMap) {
        [Console]::Error.WriteLine('refusing: AfterClose needs -BeforeMap and -AfterMap')
        exit 1
    }
    $before = Import-Clixml -LiteralPath $BeforeMap
    $after = Import-Clixml -LiteralPath $AfterMap
    $diff = @(Compare-TreeHashMaps -Before $before -After $after)
    if ($diff.Count -gt 0) {
        $diff | ForEach-Object { Write-Output $_ }
        exit 1
    }
    Write-Output 'after-close hashes match'
    exit 0
}

$bad = New-Object System.Collections.Generic.List[string]
$sawDevServe = $false
Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | ForEach-Object {
    $cmd = [string]$_.CommandLine
    if ([string]::IsNullOrWhiteSpace($cmd)) { return }
    if (Test-FinishedProfileToken -CommandLine $cmd -ProfileName 'zola') {
        $bad.Add(("stable-token pid={0}" -f $_.ProcessId)) | Out-Null
    }
    if (Test-FinishedProfileToken -CommandLine $cmd -ProfileName 'zola-dev') {
        $sawDevServe = $sawDevServe -or ($cmd -match '(?i)hermes_cli\.main' -and $cmd -match '(?i)\bserve\b')
    }
}
if (-not $sawDevServe) { $bad.Add('no dev serve') | Out-Null }
$phone = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
        $_.Name -match '(?i)python' -and ([string]$_.CommandLine) -match '(?i)-m\s+zola_phone'
    })
if ($phone.Count -gt 0) { $bad.Add('zola-phone is running') | Out-Null }
if ($bad.Count -gt 0) {
    $bad | ForEach-Object { Write-Output $_ }
    exit 1
}
Write-Output 'while-running command lines match zola-dev'
exit 0
