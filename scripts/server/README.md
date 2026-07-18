# Automation server — temporary sudo and install helpers

Automation server: **192.168.2.4** (`tinel`).

**Prerequisite:** Interactive SSH session on the server. All commands below are **single lines** — copy-paste one at a time.

Full workflow: [docs/developer/SERVER_DEPLOY.md](../../docs/developer/SERVER_DEPLOY.md) · Agent rule: `.cursor/rules/automation-server-access.mdc`

## Temporary sudo

| Action | Command |
|--------|---------|
| Fix CRLF | `sed -i 's/\r$//' /opt/dell_server_management/scripts/server/*.sh` |
| Grant agent sudo (60 min) | `cd /opt/dell_server_management && sudo ./scripts/server/grant_temporary_agent_sudo.sh` |
| Grant agent sudo (90 min) | `cd /opt/dell_server_management && sudo ./scripts/server/grant_temporary_agent_sudo.sh 90` |
| Grant deploy sudo | `cd /opt/dell_server_management && sudo ./scripts/server/grant_temporary_deploy_sudo.sh` |
| Verify | `bash /opt/dell_server_management/scripts/server/check_deploy_sudo.sh` |
| Revoke | `sudo /opt/dell_server_management/scripts/server/revoke_deploy_sudo.sh` |

Home-repo path instead of `/opt`: replace prefix with `cd ~/ServerBootShutdownManagemement &&`.

## Example installs (after agent sudo)

| Service | Command |
|---------|---------|
| Victron | `sudo /opt/dell_server_management/install_victron_service.sh` |
| Huawei | `sudo /opt/dell_server_management/install_huawei_service.sh` |
| Energy consumers | `sudo /opt/dell_server_management/install_energy_consumers_service.sh` |
| Huawei WiFi | `sudo /opt/dell_server_management/scripts/server/setup_huawei_wifi.sh` |

## Files

| File | Purpose |
|------|---------|
| [grant_temporary_agent_sudo.sh](grant_temporary_agent_sudo.sh) | Grant full temp sudo |
| [grant_temporary_deploy_sudo.sh](grant_temporary_deploy_sudo.sh) | Grant script-only temp sudo |
| [grant_temporary_automation_sudo.sh](grant_temporary_automation_sudo.sh) | Core logic `[minutes] [deploy\|agent]` |
| [revoke_deploy_sudo.sh](revoke_deploy_sudo.sh) | Revoke temp/permanent sudo |
| [check_deploy_sudo.sh](check_deploy_sudo.sh) | Verify grant is active |
| [fix_shell_scripts_crlf.sh](fix_shell_scripts_crlf.sh) | Strip Windows CRLF from `*.sh` |
| [setup_media_server_ssh.sh](setup_media_server_ssh.sh) | SSH key automation server → media server |
| [setup_data_drive_logs.sh](setup_data_drive_logs.sh) | Move app/syslog/journal logs to `/data` HDD |
| [cleanup_root_disk.sh](cleanup_root_disk.sh) | Keep `/` under ~85% (hourly timer) |

Disk layout: [docs/developer/SERVER_DISK.md](../../docs/developer/SERVER_DISK.md)
