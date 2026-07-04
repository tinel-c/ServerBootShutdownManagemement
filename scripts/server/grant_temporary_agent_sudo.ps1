#Requires -Version 5.1
<#
.SYNOPSIS
  Print the command to grant temporary full sudo for agent install/config on the server.

.EXAMPLE
  .\scripts\server\grant_temporary_agent_sudo.ps1
  .\scripts\server\grant_temporary_agent_sudo.ps1 -Minutes 90
#>
param(
    [int]$Minutes = 60
)

$HostAlias = "serverside"
$GrantCmd = "cd ~/ServerBootShutdownManagemement && sudo ./scripts/server/grant_temporary_agent_sudo.sh $Minutes"

Write-Host ""
Write-Host "Grant temporary FULL sudo for agent install/config ($Minutes minutes)" -ForegroundColor Cyan
Write-Host ""
Write-Host "Run ON the automation server (one password prompt):" -ForegroundColor Yellow
Write-Host "  ssh -t $HostAlias `"$GrantCmd`"" -ForegroundColor White
Write-Host ""
Write-Host "Or SSH in and run:" -ForegroundColor Yellow
Write-Host "  $GrantCmd" -ForegroundColor White
Write-Host ""
Write-Host "After granting, agent verifies with:" -ForegroundColor Yellow
Write-Host "  ssh $HostAlias `"bash ~/ServerBootShutdownManagemement/scripts/server/check_deploy_sudo.sh`"" -ForegroundColor White
Write-Host ""
Write-Host "Revoke early on server:" -ForegroundColor Yellow
Write-Host "  sudo ~/ServerBootShutdownManagemement/scripts/server/revoke_deploy_sudo.sh" -ForegroundColor White
Write-Host ""
