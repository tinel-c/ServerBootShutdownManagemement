# v3.14.0 (2026-07-05) — Media server, Tuya account linking, Server dashboard UI

Production media server management (SSH + Tuya PCIe), Tuya IoT Cloud device sync, and a polished **Server** dashboard page layout.

## Added

### Media server (`linux_tuya`)

- **Ubuntu media server** @ `192.168.2.185` — SSH graceful shutdown, Tuya PCIe boot / reset / force power-off.
- **Python**: `linux_tuya_manager.py`, `ssh_wrapper.py`, `tuya_pc_power_wrapper.py`; `server_factory` type `linux_tuya`.
- **MQTT listeners** extended for `media/server/command/boot` and `media/server/command/shutdown`.
- **Healthchecks.io** cron installer: `scripts/media_server/install_healthcheck_cron.sh`.
- **SSH setup**: `scripts/server/setup_media_server_ssh.sh`, `scripts/media_server/finish_remote_setup.sh`.
- **Config**: `config/server_config.yaml` entry; `MEDIA_SERVER_*` in `config/.env.example`.
- **Docs**: [docs/MEDIA_SERVER.md](../MEDIA_SERVER.md).

### Tuya account linking

- **`scripts/tuya/sync_devices.py`** — `list`, `sync`, `apply-env`, `apply-role`, `test`, `verify`, `scan-lan`.
- **`scripts/tuya/tuya_link.sh`** — guided setup wrapper.
- **`config/tuya_roles.yaml`**, `config/tuya.env.example`, `config/tuya_devices.json.example`.
- **Docs**: [docs/TUYA_ACCOUNT_LINK.md](../TUYA_ACCOUNT_LINK.md).

### Node-RED — media flows (30–33)

| Flow | Purpose |
|------|---------|
| `30-media-server-controls.json` | Boot, shutdown, reset, force buttons |
| `31-media-server-status.json` | Status card (matches Dell/HP style) |
| `32-media-server-health.json` | Full-width Healthchecks.io monitor |
| `33-media-server-schedule.json` | Daily boot/shutdown schedule UI |

- **Server page** (`/dashboard/page2`): media widgets in **Server management** group alongside Dell/HP.
- **Telegram** (`12-server-telegram.json`): `media` server target for boot/shutdown commands.
- **Live deploy**: `nodered/live-connection/scripts/deploy-media-ui.mjs`, `fix-dashboard-layout.mjs`.

## Changed

- **Server dashboard layout** — Rolling Log terminal moved to the **end** of the page; media health full-width (Dell/HP template); schedule merged into Server management group; redundant “Last command” panel removed (toasts retained).
- **MQTT protocol** — `media/server/*` topics documented in [MQTT_PROTOCOL.md](../MQTT_PROTOCOL.md).
- **Flows README** — import order, deploy notes, flow `08-server-dashboard-config.json` for live Server page IDs.

## Upgrade

```bash
git pull
pip install -r requirements.txt
sudo ./update.sh

# Tuya (if not done) — on automation server
bash scripts/tuya/tuya_link.sh all
python3 scripts/tuya/sync_devices.py apply-role media_server

# Media SSH (one-time)
./scripts/server/setup_media_server_ssh.sh

# Node-RED — from dev PC
node nodered/live-connection/scripts/deploy-media-ui.mjs
```

Verify:

- Dashboard: `http://<server>:1880/dashboard/page2` — HP, Dell, Media sections; schedule card; Rolling Log at bottom.
- MQTT: `mosquitto_sub -h localhost -t 'media/server/status' -C 1`
- Boot test: dashboard **BOOT MEDIA SERVER** or `mosquitto_pub … media/server/command/boot`
- Telegram: `/boot media`, `/status` (includes media server)

## Quick links

- [Media server](MEDIA_SERVER.md)
- [Tuya account linking](TUYA_ACCOUNT_LINK.md)
- [MQTT protocol](MQTT_PROTOCOL.md)
- [Flows README](../../nodered/flows/README.md)
