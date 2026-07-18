# Automation server deploy (192.168.2.4)

When installing or updating services on the automation host, the agent cannot use interactive `sudo`. Grant **temporary automation sudo** first — always via **single-line** commands in an **existing SSH session** on the server.

## Server

| Item | Value |
|------|--------|
| Host | `192.168.2.4` |
| SSH user | `tinel` |
| Install path | `/opt/dell_server_management` |
| Dev copy (optional) | `~/ServerBootShutdownManagemement` |
| Data HDD | `/data` (`/dev/sdb1`) — logs & backups; see [SERVER_DISK.md](SERVER_DISK.md) |

**SSH access** (password or your own key) is assumed before any agent work. This repo does not ship scripts to provision SSH from a dev PC.

**Agent memory:** `.cursor/rules/automation-server-access.mdc` — SSH key path, `sudo -n` grant, git → `update.sh` workflow (no scp).

## SSH from agent (dev PC)

`ssh -o BatchMode=yes -i ~/.ssh/serverside_192_168_2_4_ed25519 tinel@192.168.2.4 "<command>"`

Key on Windows: `%USERPROFILE%\.ssh\serverside_192_168_2_4_ed25519`

## Git deploy (required workflow)

1. Dev: commit and push.
2. Server: `cd ~/ServerBootShutdownManagemement && git pull`
3. Server: `printf '\n' | sudo ./update.sh` (syncs to `/opt/dell_server_management`, restarts services)
4. If needed: `sudo ./install_<service>_service.sh` under `/opt/dell_server_management`

Do **not** use `scp` for routine file transfer.

## Sudo modes

| Mode | Grant script | Scope | Use when |
|------|--------------|-------|----------|
| **agent** (recommended) | `grant_temporary_agent_sudo.sh` | **Full** passwordless `sudo -n` for any command | netplan, systemd, apt, WiFi setup, new services |
| **deploy** | `grant_temporary_deploy_sudo.sh` | Whitelisted `install_*.sh`, `update.sh`, `setup_huawei_wifi.sh` only | Routine service deploys |

Both modes **auto-expire** (default 60 minutes) and can be revoked early.

## Workflow for agents

1. User opens SSH to `tinel@192.168.2.4` (terminal, Cursor remote, etc.).
2. User runs one grant command (password prompt once):

   `cd /opt/dell_server_management && sudo ./scripts/server/grant_temporary_agent_sudo.sh`

3. Verify in the same session:

   `bash /opt/dell_server_management/scripts/server/check_deploy_sudo.sh`

   Expect `mode: agent (full — any install/config command via sudo -n)`.
4. Agent runs install/config via `sudo -n` on the server (no interactive password).
5. Optional revoke: `sudo /opt/dell_server_management/scripts/server/revoke_deploy_sudo.sh` — otherwise auto-expires in 60 minutes.

## Commands for the user (existing SSH session on 192.168.2.4)

Copy-paste one line at a time.

| Action | Command |
|--------|---------|
| Fix CRLF | `sed -i 's/\r$//' /opt/dell_server_management/scripts/server/*.sh` |
| Grant agent sudo (60 min) | `cd /opt/dell_server_management && sudo ./scripts/server/grant_temporary_agent_sudo.sh` |
| Grant agent sudo (90 min) | `cd /opt/dell_server_management && sudo ./scripts/server/grant_temporary_agent_sudo.sh 90` |
| Grant deploy sudo | `cd /opt/dell_server_management && sudo ./scripts/server/grant_temporary_deploy_sudo.sh` |
| Verify | `bash /opt/dell_server_management/scripts/server/check_deploy_sudo.sh` |
| Revoke | `sudo /opt/dell_server_management/scripts/server/revoke_deploy_sudo.sh` |

## What each mode allows

### Agent mode (`/etc/sudoers.d/automation-agent-temp`)

```sudoers
tinel ALL=(ALL) NOPASSWD: ALL
```

Passwordless **any** command via `sudo -n` during the grant window.

### Deploy mode (`/etc/sudoers.d/automation-deploy-temp`)

User `tinel` may run **without a password** only whitelisted install/update scripts under the repo and `/opt/dell_server_management`.

## Permanent deploy sudo (optional)

`cd /opt/dell_server_management && sudo ./scripts/server/install_deploy_sudoers.sh`

## Related scripts

| Script | Where to run |
|--------|----------------|
| [grant_temporary_agent_sudo.sh](../../scripts/server/grant_temporary_agent_sudo.sh) | **Server** — full temp sudo |
| [grant_temporary_deploy_sudo.sh](../../scripts/server/grant_temporary_deploy_sudo.sh) | **Server** — script-only temp sudo |
| [grant_temporary_automation_sudo.sh](../../scripts/server/grant_temporary_automation_sudo.sh) | **Server** — `[minutes] [deploy\|agent]` |
| [revoke_deploy_sudo.sh](../../scripts/server/revoke_deploy_sudo.sh) | **Server** |
| [check_deploy_sudo.sh](../../scripts/server/check_deploy_sudo.sh) | **Server** |

See also [scripts/server/README.md](../../scripts/server/README.md).
