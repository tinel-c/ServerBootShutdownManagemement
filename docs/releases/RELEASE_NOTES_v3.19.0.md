# Release Notes — v3.19.0

**Date:** 2026-07-18

## Summary

Moves automation logs to the `/data` HDD and adds root-disk cleanup; improves energy charts (1h / 24h / 7d) and Tongou breaker low-load `phase_a` handling.

## Changes

### Disk
- `scripts/server/setup_data_drive_logs.sh` — app/syslog/journal → `/data/logs/`
- `cleanup-root-disk.timer` — keep `/` ≤ 85%
- Docs: [SERVER_DISK.md](../developer/SERVER_DISK.md)

### Energy
- Chart range tabs on Victron **811** and Huawei **821**
- Tongou metric cache (`phase_stale_after_s`) + cloud/LAN online fixes
- Energy dashboard page uses `ui_base`

## Deploy

```bash
cd ~/ServerBootShutdownManagemement && git pull
printf '\n' | sudo bash ./update.sh
# Logs layout (idempotent if already run):
sudo bash /opt/dell_server_management/scripts/server/setup_data_drive_logs.sh
systemctl status cleanup-root-disk.timer
```

Redeploy Node-RED flows **811**, **821**, **840** if charts/consumers UI need refresh.
