# Server SSH access, temporary deploy sudo, and remote install

Automation server: **192.168.2.4** (`tinel`, SSH alias `serverside`).

Full agent workflow: [docs/developer/SERVER_DEPLOY.md](../../docs/developer/SERVER_DEPLOY.md)

## Temporary deploy sudo (recommended)

SSH keys log you in; **systemd installs need sudo**. Grant **time-limited** passwordless sudo for deploy scripts only.

### Run on the server (one password prompt)

```bash
cd ~/ServerBootShutdownManagemement && sudo ./scripts/server/grant_temporary_deploy_sudo.sh
```

Default **60 minutes**, then auto-revokes (requires `at` package). Custom duration:

```bash
sudo ./scripts/server/grant_temporary_deploy_sudo.sh 90
```

Revoke early:

```bash
sudo ./scripts/server/revoke_deploy_sudo.sh
```

Check status (from PC or server):

```bash
bash ~/ServerBootShutdownManagemement/scripts/server/check_deploy_sudo.sh
```

## SSH key setup (new PC)

```powershell
.\scripts\server\setup_ssh_key.ps1
```

## Deploy Victron publisher (after temp sudo granted)

```powershell
.\scripts\server\deploy_victron_remote.ps1
```

Or from server:

```bash
cd ~/ServerBootShutdownManagemement && sudo ./install_victron_service.sh
```

## Files

| File | Purpose |
|------|---------|
| [grant_temporary_deploy_sudo.sh](grant_temporary_deploy_sudo.sh) | **Grant temp sudo (run on server)** |
| [revoke_deploy_sudo.sh](revoke_deploy_sudo.sh) | Revoke temp/permanent deploy sudo |
| [check_deploy_sudo.sh](check_deploy_sudo.sh) | Verify agent can deploy |
| [sudoers.d-automation-deploy-temp](sudoers.d-automation-deploy-temp) | Temp sudoers rules |
| [install_deploy_sudoers.sh](install_deploy_sudoers.sh) | Permanent sudo (optional) |
| [setup_ssh_key.ps1](setup_ssh_key.ps1) | SSH key setup (dev PC) |
| [deploy_victron_remote.ps1](deploy_victron_remote.ps1) | Sync + install Victron |
