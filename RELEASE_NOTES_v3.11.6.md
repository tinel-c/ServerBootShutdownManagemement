# v3.11.6 (2026-07-04) — Victron energy integration

**Cerbo GX / MultiPlus-II** energy monitoring, automation, Node-RED dashboard, Telegram commands, and health watchdog.

## Highlights

- **Modbus → MQTT** (`victron-mqtt-publisher.service`): battery, grid, PV, load, inverter metrics on `energy/victron/*`
- **Automation**: `headroom_w = PV − consumption`, `can_add_load`, discretionary load MQTT commands
- **Solar forecast** (`victron-solar-forecast-publisher.service`): Open-Meteo for Lunca Cetătuui (48 h / daily)
- **Node-RED**: flows `800` (Energy page), `811` (live dashboard + 7-day chart), `812` (Telegram `/energy_*`)
- **Telegram `/help`**: Victron energy section and quick-action buttons (flow `50` patch)
- **Watchdog** (flow `90`): monitors `energy/victron/status` (2 min timeout); alerts only on online/offline transitions

## Node-RED import order

1. `800-energy-base-config.json`
2. `811-victron-energy-status.json`
3. `812-victron-energy-telegram.json`
4. Re-import `50-telegram-interface.json` or `50-patch-victron-energy-help.json` (replace nodes)
5. Re-import `90-device-watchdog.json` (replace nodes)

## Server install

```bash
cp device/victron-multiplus-ii/config/.env.example device/victron-multiplus-ii/config/.env
# edit Cerbo IP and Modbus unit IDs
sudo ./install_victron_service.sh
```

See [device/victron-multiplus-ii/README.md](device/victron-multiplus-ii/README.md) and [docs/ENERGY_NODE_RED.md](docs/ENERGY_NODE_RED.md).

## Telegram commands

| Command | Action |
|---------|--------|
| `/energy_status` | Battery, grid, PV, load, headroom, inverter |
| `/energy_start` | Start discretionary loads (when headroom OK) |
| `/energy_stop` | Stop discretionary loads |
| `/energy_help` | Energy help + inline buttons |
