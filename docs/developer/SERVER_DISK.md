# Automation server disk layout

The automation host (`192.168.2.4`) has two disks:

| Disk | Mount | Role |
|------|-------|------|
| `/dev/sda` (~15 GB) | `/` | OS, `/opt/dell_server_management`, packages |
| `/dev/sdb` (~120 GB) | `/data` | Logs, swap, snapshots, backups (`LABEL=server-data`) |

Keep growth off the root SSD. Prefer `/data` for anything that can grow without bound.

## Setup (idempotent)

```bash
sudo bash /opt/dell_server_management/scripts/server/setup_data_drive_logs.sh
```

Skip moving swap (rare): `sudo SETUP_DATA_SWAP=0 bash …/setup_data_drive_logs.sh`

### What it places on `/data`

| Path | Contents |
|------|----------|
| `/data/logs/automation/` | App `LOG_FILE` (`dell_server_management.log`) |
| `/data/logs/syslog/` | `syslog`, `auth.log`, `kern.log` (symlinked from `/var/log/`) |
| `/data/logs/journal/` | systemd journal (bind-mounted on `/var/log/journal`) |
| `/data/homeassistant/config/` | Full Home Assistant config (bind-mounted on `~homeassistant/.homeassistant`) |
| `/data/logs/mosquitto/` | Mosquitto broker log |
| `/data/camera-snapshots/` | On-demand camera JPEGs (`CAMERA_SNAPSHOT_DIR`) |
| `/data/swapfile` | Swap (replaces `/swap.img` on the root SSD) |

`config/.env` is updated for `LOG_FILE` and `CAMERA_SNAPSHOT_DIR`.

## Root-disk cleanup

```bash
sudo bash /opt/dell_server_management/scripts/server/cleanup_root_disk.sh
```

- Default target: keep `/` **≤ 80%** used (`ROOT_DISK_MAX_PERCENT`)
- Emergency truncate at **≥ 92%**
- Truncates oversized HA / Mosquitto logs if they reappear on root
- Hourly timer: `cleanup-root-disk.timer`

```bash
sudo systemctl enable --now cleanup-root-disk.timer
systemctl list-timers cleanup-root-disk.timer
```

Cleanup log: `/data/logs/automation/root_disk_cleanup.log`

## Verify

```bash
df -h / /data
swapon --show
mountpoint /data /var/log/journal
readlink -f /home/homeassistant/.homeassistant/home-assistant.log /var/log/syslog
```

Expect root well under 80% after setup (swap move frees ~3 GB); `/data` holds logs and swap.

## Related

- [scripts/server/README.md](../../scripts/server/README.md)
- [SERVER_DEPLOY.md](SERVER_DEPLOY.md)
- Cursor rule: `.cursor/rules/mosquitto-pin-2.0.18.mdc` (broker pin; unrelated to disk but same host)
