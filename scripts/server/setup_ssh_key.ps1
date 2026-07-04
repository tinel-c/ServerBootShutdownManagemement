#Requires -Version 5.1
<#
.SYNOPSIS
  Set up SSH key authentication to the automation server (serverside / 192.168.2.4).

.EXAMPLE
  .\scripts\server\setup_ssh_key.ps1
#>
$ErrorActionPreference = "Stop"

$HostAlias = "serverside"
$HostName = "192.168.2.4"
$User = "tinel"
$SshDir = Join-Path $env:USERPROFILE ".ssh"
$KeyPath = Join-Path $SshDir "serverside_192_168_2_4_ed25519"
$PubPath = "$KeyPath.pub"
$ConfigPath = Join-Path $SshDir "config"

New-Item -ItemType Directory -Force -Path $SshDir | Out-Null

if (-not (Test-Path $KeyPath)) {
    Write-Host "Generating ED25519 key: $KeyPath"
    ssh-keygen -t ed25519 -f $KeyPath -N '""' -C "${User}@${HostAlias}-automation"
} else {
    Write-Host "Using existing key: $KeyPath"
}

$pub = Get-Content $PubPath -Raw
Write-Host "Installing public key on ${User}@${HostName} (enter server password once)..."
$remoteCmd = @"
mkdir -p ~/.ssh && chmod 700 ~/.ssh
grep -qxF '$($pub.Trim())' ~/.ssh/authorized_keys 2>/dev/null || echo '$($pub.Trim())' >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
echo key_installed
"@
ssh "${User}@${HostName}" $remoteCmd

$snippet = @"

Host $HostAlias
    HostName $HostName
    User $User
    IdentityFile ~/.ssh/serverside_192_168_2_4_ed25519
    IdentitiesOnly yes
"@

if (-not (Test-Path $ConfigPath) -or (Get-Content $ConfigPath -Raw) -notmatch "Host\s+$HostAlias") {
    Add-Content -Path $ConfigPath -Value $snippet
    Write-Host "Added Host $HostAlias to $ConfigPath"
} else {
    Write-Host "Host $HostAlias already in $ConfigPath"
}

ssh -o BatchMode=yes $HostAlias "echo SSH key authentication OK for $(whoami)@$(hostname)"
Write-Host ""
Write-Host "Next: deploy Victron publisher"
Write-Host "  .\scripts\server\deploy_victron_remote.ps1"
Write-Host ""
Write-Host "Optional (one-time, passwordless sudo for deploy):"
Write-Host "  ssh -t $HostAlias `"cd ~/ServerBootShutdownManagemement && sudo ./scripts/server/install_deploy_sudoers.sh`""
