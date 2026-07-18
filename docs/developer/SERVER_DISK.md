# Automation server disk layout

The automation host (`192.168.2.4`) has two disks:

| Disk | Mount | Role |
|------|-------|------|
| `/dev/sda` (~15 GB) | `/` | OS, `/opt/dell_server_management`, packages |
| `/dev/sdb` (~120 GB) | `/data` | Logs, backups, large data (`LABEL=server-data`) |

## Logs on `/data`

Run once (root):

```bash
sudo bash /opt/dell_server_management/scripts/server/setup_data_drive_logs.sh
```

This places:

| Path | Contents |
|------|----------|
| `/data/logs/automation/` | App `LOG_FILE` (`dell_server_management.log`) |
| `/data/logs/syslog/` | `syslog`, `auth.log`, `kern.log` (symlinked from `/var/log/`) |
| `/data/logs/journal/` | systemd journal (bind-mounted on `/var/log/journal`) |

`config/.env` is updated to `LOG_FILE=/data/logs/automation/dell_server_management.log`.

## Root-disk cleanup

```bash
sudo bash /opt/dell_server_management/scripts/server/cleanup_root_disk.sh
```

- Default target: keep `/` **≤ 85%** used (`ROOT_DISK_MAX_PERCENT`)
- Emergency truncate at **≥ 95%**
- Hourly timer: `cleanup-root-disk.timer`

```bash
sudo systemctl enable --now cleanup-root-disk.timer
systemctl list-timers cleanup-root-disk.timer
```

Cleanup log: `/data/logs/automation/root_disk_cleanup.log`

## Related

- [scripts/server/README.md](../../scripts/server/README.md)
- [SERVER_DEPLOY.md](SERVER_DEPLOY.md)
