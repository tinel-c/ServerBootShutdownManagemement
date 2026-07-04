# Install helpers

Shared by `install.sh`, `update.sh`, and the root device installer scripts.

| File | Purpose |
|------|---------|
| `common.sh` | Colors, `require_root`, env backup/restore, pip + systemd helpers |
| `device_service.sh` | `install_device_publisher` — copy device tree, preserve `.env`, enable units |

Root wrappers (backward compatible with deploy sudoers):

- `install_victron_service.sh` — Victron + solar forecast publishers
- `install_huawei_service.sh` — Huawei SUN2000 publisher

Set `ALLOW_INACTIVE_SERVICE=1` to skip hard failure when Modbus/MQTT is not ready yet (used by `install.sh` on first run).
