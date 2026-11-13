# PROC1-DEV: create zola-dev from invented data plus config.yaml and SOUL.md — PROC1-D4/D14
#Requires -Version 5.1
param(
    [string]$LocalAppData = $env:LOCALAPPDATA,
    [switch]$Replace,
    [scriptblock]$RunningProbe
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'DevCommon.psm1') -Force
$result = New-DevProfileTree -LocalAppData $LocalAppData -Replace:$Replace -RunningProbe $RunningProbe
foreach ($copy in @($result.Copies)) {
    Write-Output ("copy {0} source={1} dest={2}" -f $copy.Name, $copy.SourceHash, $copy.DestHash)
}
foreach ($change in @($result.Changes)) {
    Write-Output ("config.yaml path before={0}" -f $change.Before)
    if ($change.Kept) {
        Write-Output ("config.yaml path {0}" -f $change.Kept)
    } else {
        Write-Output ("config.yaml path after={0}" -f $change.After)
    }
}
if (-not $result.Ok) {
    [Console]::Error.WriteLine($result.Reason)
    exit 1
}
exit 0
