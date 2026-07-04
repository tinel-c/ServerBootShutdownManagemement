# Server SSH access, temporary deploy sudo, and remote install

Automation server: **192.168.2.4** (`tinel`, SSH alias `serverside`).

Full agent workflow: [docs/developer/SERVER_DEPLOY.md](../../docs/developer/SERVER_DEPLOY.md)

## Temporary sudo for agent sessions

SSH keys log you in; **install/config needs sudo**. For agent work (netplan, systemd, apt, WiFi, new services), grant **full temporary sudo**:

### Run on the server (one password prompt)

```bash
cd ~/ServerBootShutdownManagemement && sudo ./scripts/server/grant_temporary_agent_sudo.sh
```

Default **60 minutes**, then auto-revokes (requires `at` package). Custom duration:

```bash
sudo ./scripts/server/grant_temporary_agent_sudo.sh 90
```

From your dev PC (prints the SSH command):

```powershell
.\scripts\server\grant_temporary_agent_sudo.ps1
```

### Narrower deploy sudo (script whitelist only)

For routine Victron installs without full root:

```bash
cd ~/ServerBootShutdownManagemement && sudo ./scripts/server/grant_temporary_deploy_sudo.sh
```

### Revoke early

```bash
sudo ./scripts/server/revoke_deploy_sudo.sh
```

### Check status (from PC or server)

```bash
bash ~/ServerBootShutdownManagemement/scripts/server/check_deploy_sudo.sh
```

Expect `mode: agent (full — …)` or `mode: deploy (whitelisted …)`.

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

## Huawei inverter WiFi (after **agent** sudo granted)

```bash
sudo ~/ServerBootShutdownManagemement/scripts/server/setup_huawei_wifi.sh
python ~/ServerBootShutdownManagemement/device/huawei-inverter/scripts/modbus_probe.py
```

## Files

| File | Purpose |
|------|---------|
| [grant_temporary_agent_sudo.sh](grant_temporary_agent_sudo.sh) | **Grant full temp sudo (run on server)** |
| [grant_temporary_agent_sudo.ps1](grant_temporary_agent_sudo.ps1) | Print grant command (dev PC) |
| [grant_temporary_deploy_sudo.sh](grant_temporary_deploy_sudo.sh) | Grant script-only temp sudo |
| [grant_temporary_automation_sudo.sh](grant_temporary_automation_sudo.sh) | Core grant logic `[minutes] [deploy\|agent]` |
| [revoke_deploy_sudo.sh](revoke_deploy_sudo.sh) | Revoke all temp/permanent automation sudo |
| [check_deploy_sudo.sh](check_deploy_sudo.sh) | Verify agent sudo is active |
| [sudoers.d-automation-agent-temp](sudoers.d-automation-agent-temp) | Full temp sudoers rules |
| [sudoers.d-automation-deploy-temp](sudoers.d-automation-deploy-temp) | Script-only temp sudoers rules |
| [install_deploy_sudoers.sh](install_deploy_sudoers.sh) | Permanent script-only sudo (optional) |
| [setup_ssh_key.ps1](setup_ssh_key.ps1) | SSH key setup (dev PC) |
| [deploy_victron_remote.ps1](deploy_victron_remote.ps1) | Sync + install Victron |
| [setup_huawei_wifi.sh](setup_huawei_wifi.sh) | Netplan USB WiFi → SUN2000 AP |
