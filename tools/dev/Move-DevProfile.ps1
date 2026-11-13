# PROC1-DEV: move profiles\zola-dev from the native Hermes root to hermes-dev — D4 amendment
#Requires -Version 5.1
param(
    [string]$LocalAppData = $env:LOCALAPPDATA,
    [scriptblock]$RunningProbe
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'DevCommon.psm1') -Force
$result = Move-DevProfileTree -LocalAppData $LocalAppData -RunningProbe $RunningProbe
if ($result.Ok) {
    Write-Output 'move hashes match'
    Write-Output ("config retarget count={0}" -f $result.Retarget)
    foreach ($rel in @($result.OtherFiles)) {
        Write-Output ("other path file={0}" -f $rel)
    }
    exit 0
}
[Console]::Error.WriteLine($result.Reason)
exit 1
