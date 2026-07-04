# Automation server deploy (192.168.2.4)

When installing or updating services on the **serverside** automation host, the agent cannot use interactive `sudo`. Use **temporary deploy sudo** first.

## Server

| Item | Value |
|------|--------|
| Host | `192.168.2.4` |
| SSH user | `tinel` |
| SSH alias | `serverside` (see `scripts/server/ssh_config.snippet`) |
| Install path | `/opt/dell_server_management` |
| Repo on server | `~/ServerBootShutdownManagemement` |

## Workflow for agents

1. **Sync** deploy files from dev PC to `~/ServerBootShutdownManagemement` on the server (scp or `deploy_*_remote` scripts).
2. **Ask the user** to grant temporary sudo **on the server** (one command, one password prompt).
3. **Verify** deploy sudo is active:
   ```bash
   ssh tinel@192.168.2.4 "bash ~/ServerBootShutdownManagemement/scripts/server/check_deploy_sudo.sh"
   ```
4. **Run install** without `-t`:
   ```bash
   ssh tinel@192.168.2.4 "cd ~/ServerBootShutdownManagemement && sudo ./install_victron_service.sh"
   ```
5. **Optional:** user revokes early: `sudo ./scripts/server/revoke_deploy_sudo.sh`  
   Otherwise temp sudo **auto-expires** (default 60 minutes).

## Command for the user (run ON 192.168.2.4)

**Grant temporary deploy sudo (60 minutes, default):**

```bash
cd ~/ServerBootShutdownManagemement && sudo ./scripts/server/grant_temporary_deploy_sudo.sh
```

**Custom duration (e.g. 90 minutes):**

```bash
cd ~/ServerBootShutdownManagemement && sudo ./scripts/server/grant_temporary_deploy_sudo.sh 90
```

**Revoke immediately:**

```bash
cd ~/ServerBootShutdownManagemement && sudo ./scripts/server/revoke_deploy_sudo.sh
```

## What temporary sudo allows

User `tinel` may run **without a password** (via `/etc/sudoers.d/automation-deploy-temp`):

- `~/ServerBootShutdownManagemement/install_*.sh`
- `/opt/dell_server_management/install_*.sh`
- `update.sh` in those trees
- `scripts/server/revoke_deploy_sudo.sh`

Does **not** grant general root — only those deploy paths.

## Permanent deploy sudo (optional)

For home lab only, if you accept persistent NOPASSWD:

```bash
sudo ./scripts/server/install_deploy_sudoers.sh
```

Installs `/etc/sudoers.d/automation-deploy` (no auto-expiry).

## Related scripts

| Script | Where to run |
|--------|----------------|
| [grant_temporary_deploy_sudo.sh](../../scripts/server/grant_temporary_deploy_sudo.sh) | **Server** (with sudo) |
| [revoke_deploy_sudo.sh](../../scripts/server/revoke_deploy_sudo.sh) | **Server** (with sudo) |
| [check_deploy_sudo.sh](../../scripts/server/check_deploy_sudo.sh) | Server or via SSH |
| [deploy_victron_remote.ps1](../../scripts/server/deploy_victron_remote.ps1) | Dev PC |
| [setup_ssh_key.ps1](../../scripts/server/setup_ssh_key.ps1) | Dev PC |

See also [scripts/server/README.md](../../scripts/server/README.md).
