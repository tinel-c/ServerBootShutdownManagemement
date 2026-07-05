# Install helpers

Shared by `install.sh`, `update.sh`, and the root device installer scripts.

| File | Purpose |
|------|---------|
| `common.sh` | Colors, `require_root`, env backup/restore, `chmod_runtime_scripts`, pip + systemd helpers |
| `device_service.sh` | `install_device_publisher` — copy device tree, preserve `.env`, enable units |

Root wrappers (backward compatible with deploy sudoers):

- `install_victron_service.sh` — Victron + solar forecast publishers
- `install_huawei_service.sh` — Huawei SUN2000 publisher

**Media server (v3.14.0+)** uses existing core services (`mqtt-boot-listener`, `mqtt-shutdown-listener`, `status-publisher`, `health-monitor`) — no separate systemd unit. After `install.sh` / `update.sh`, configure `MEDIA_SERVER_*` in `config/.env`, run `scripts/tuya/tuya_link.sh`, and `scripts/server/setup_media_server_ssh.sh`. See [docs/MEDIA_SERVER.md](../../docs/MEDIA_SERVER.md).

Set `ALLOW_INACTIVE_SERVICE=1` to skip hard failure when Modbus/MQTT is not ready yet (used by `install.sh` on first run).
