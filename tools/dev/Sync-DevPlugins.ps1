# PROC1-DEV: copy this branch's plugins into zola-dev only, never zola_phone — PROC1-D13
#Requires -Version 5.1
param(
    [Parameter(Mandatory)][string]$From,
    [string]$LocalAppData = $env:LOCALAPPDATA,
    [switch]$Replace,
    [scriptblock]$RunningProbe
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'DevCommon.psm1') -Force
$result = Sync-DevPluginTree -From $From -LocalAppData $LocalAppData -Replace:$Replace -RunningProbe $RunningProbe
if (-not $result.Ok) {
    [Console]::Error.WriteLine($result.Reason)
    exit 1
}
Write-Output ("synced {0}" -f @($result.Copied).Count)
exit 0
