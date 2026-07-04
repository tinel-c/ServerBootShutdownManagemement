#Requires -Version 5.1
<#
.SYNOPSIS
  Sync Victron integration to the automation server and install the systemd service.

.EXAMPLE
  .\scripts\server\deploy_victron_remote.ps1
#>
$ErrorActionPreference = "Stop"

$HostAlias = "serverside"
$RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $RepoRoot

Write-Host "Syncing to ${HostAlias}:~/ServerBootShutdownManagemement ..."
scp -r device/victron-multiplus-ii "${HostAlias}:~/ServerBootShutdownManagemement/device/"
scp systemd/victron-mqtt-publisher.service "${HostAlias}:~/ServerBootShutdownManagemement/systemd/"
scp requirements.txt install_victron_service.sh "${HostAlias}:~/ServerBootShutdownManagemement/"
scp scripts/server/sudoers.d-automation-deploy scripts/server/install_deploy_sudoers.sh `
    "${HostAlias}:~/ServerBootShutdownManagemement/scripts/server/"

ssh $HostAlias "chmod +x ~/ServerBootShutdownManagemement/install_victron_service.sh ~/ServerBootShutdownManagemement/scripts/server/install_deploy_sudoers.sh ~/ServerBootShutdownManagemement/device/victron-multiplus-ii/scripts/*.py"

Write-Host "Installing victron-mqtt-publisher.service (sudo may prompt once)..."
ssh -t $HostAlias "cd ~/ServerBootShutdownManagemement && sudo ./install_victron_service.sh"

Write-Host ""
Write-Host "Verify:"
Write-Host "  ssh $HostAlias `"systemctl status victron-mqtt-publisher.service`""
