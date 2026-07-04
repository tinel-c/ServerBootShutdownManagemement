# Automation server deploy (192.168.2.4)

When installing or updating services on the **serverside** automation host, the agent cannot use interactive `sudo`. Grant **temporary automation sudo** first.

## Server

| Item | Value |
|------|--------|
| Host | `192.168.2.4` |
| SSH user | `tinel` |
| SSH alias | `serverside` (see `scripts/server/ssh_config.snippet`) |
| Install path | `/opt/dell_server_management` |
| Repo on server | `~/ServerBootShutdownManagemement` |

## Sudo modes

| Mode | Grant script | Scope | Use when |
|------|--------------|-------|----------|
| **agent** (recommended) | `grant_temporary_agent_sudo.sh` | **Full** passwordless `sudo -n` for any command | netplan, systemd, apt, WiFi setup, new services |
| **deploy** | `grant_temporary_deploy_sudo.sh` | Whitelisted `install_*.sh`, `update.sh`, `setup_huawei_wifi.sh` only | Routine Victron/service deploys |

Both modes **auto-expire** (default 60 minutes) and can be revoked early.

## Workflow for agents

1. **Sync** files from dev PC to `~/ServerBootShutdownManagemement` on the server (scp or `deploy_*_remote` scripts).
2. **Ask the user** to grant temporary sudo **on the server** (one command, one password prompt).  
   For install/config work (netplan, Huawei WiFi, systemd, packages), use **agent** mode:
   ```bash
   cd ~/ServerBootShutdownManagemement && sudo ./scripts/server/grant_temporary_agent_sudo.sh
   ```
   From Windows, print the command:
   ```powershell
   .\scripts\server\grant_temporary_agent_sudo.ps1
   ```
3. **Verify** sudo is active:
   ```bash
   ssh tinel@192.168.2.4 "bash ~/ServerBootShutdownManagemement/scripts/server/check_deploy_sudo.sh"
   ```
   Expect `mode: agent (full — any install/config command via sudo -n)`.
4. **Run install/config** without `-t`:
   ```bash
   ssh tinel@192.168.2.4 "sudo ~/ServerBootShutdownManagemement/scripts/server/setup_huawei_wifi.sh"
   ssh tinel@192.168.2.4 "cd ~/ServerBootShutdownManagemement && sudo ./install_victron_service.sh"
   ```
5. **Optional:** user revokes early: `sudo ./scripts/server/revoke_deploy_sudo.sh`  
   Otherwise temp sudo **auto-expires** (default 60 minutes).

## Commands for the user (run ON 192.168.2.4)

**Grant full agent sudo (60 minutes, default — use for agent sessions):**

```bash
cd ~/ServerBootShutdownManagemement && sudo ./scripts/server/grant_temporary_agent_sudo.sh
```

**Grant script-only deploy sudo (narrower):**

```bash
cd ~/ServerBootShutdownManagemement && sudo ./scripts/server/grant_temporary_deploy_sudo.sh
```

**Custom duration (e.g. 90 minutes):**

```bash
sudo ./scripts/server/grant_temporary_agent_sudo.sh 90
```

**Revoke immediately:**

```bash
cd ~/ServerBootShutdownManagemement && sudo ./scripts/server/revoke_deploy_sudo.sh
```

## What each mode allows

### Agent mode (`/etc/sudoers.d/automation-agent-temp`)

```sudoers
tinel ALL=(ALL) NOPASSWD: ALL
```

Passwordless **any** command via `sudo -n` during the grant window — netplan, systemctl, apt, file edits under `/etc`, etc.

### Deploy mode (`/etc/sudoers.d/automation-deploy-temp`)

User `tinel` may run **without a password** only:

- `~/ServerBootShutdownManagemement/install_*.sh`
- `/opt/dell_server_management/install_*.sh`
- `update.sh` in those trees
- `scripts/server/setup_huawei_wifi.sh`
- `scripts/server/revoke_deploy_sudo.sh`

Does **not** grant general root — only those deploy paths.

## Permanent deploy sudo (optional)

For home lab only, if you accept persistent NOPASSWD on whitelisted scripts:

```bash
sudo ./scripts/server/install_deploy_sudoers.sh
```

Installs `/etc/sudoers.d/automation-deploy` (no auto-expiry, script whitelist only).

## Related scripts

| Script | Where to run |
|--------|----------------|
| [grant_temporary_agent_sudo.sh](../../scripts/server/grant_temporary_agent_sudo.sh) | **Server** — full temp sudo |
| [grant_temporary_agent_sudo.ps1](../../scripts/server/grant_temporary_agent_sudo.ps1) | Dev PC — prints grant command |
| [grant_temporary_deploy_sudo.sh](../../scripts/server/grant_temporary_deploy_sudo.sh) | **Server** — script-only temp sudo |
| [grant_temporary_automation_sudo.sh](../../scripts/server/grant_temporary_automation_sudo.sh) | **Server** — `[minutes] [deploy\|agent]` |
| [revoke_deploy_sudo.sh](../../scripts/server/revoke_deploy_sudo.sh) | **Server** (with sudo) |
| [check_deploy_sudo.sh](../../scripts/server/check_deploy_sudo.sh) | Server or via SSH |
| [deploy_victron_remote.ps1](../../scripts/server/deploy_victron_remote.ps1) | Dev PC |
| [setup_ssh_key.ps1](../../scripts/server/setup_ssh_key.ps1) | Dev PC |

See also [scripts/server/README.md](../../scripts/server/README.md).
