#Requires -Version 5.1
$ErrorActionPreference = "Stop"
$HostAlias = "tinel@192.168.2.4"
$RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $RepoRoot
& bash "$PSScriptRoot/deploy_huawei_remote.sh" $HostAlias
