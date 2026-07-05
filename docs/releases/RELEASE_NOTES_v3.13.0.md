# v3.13.0 (2026-07-05) — Energy dashboards, Huawei PV forecast, Tapo cameras

Energy page overhaul (Victron + Huawei charts, PV forecast model), Tapo camera dashboard/watchdogs, and live Node-RED deploy helpers.

## Added

### Energy — dashboards & PV forecast

- **Victron flow 811** — 7-day SVG chart: thinner lines, Y-axis labels, hover tooltips with stored values; SoC band fixed (100% at top of lower band).
- **Huawei flow 821** — 7-day active-power chart (0 W at bottom, full plot height); hover tooltips.
- **Huawei PV forecast model** — Open-Meteo irradiance → expected power; **string 1 = west**, **string 2 = east** (10 panels each); performance vs actual (V×I); rolling 24 h average. Library: `device/huawei-inverter/lib/pv_forecast_model.py`.
- **Flow 821** subscribes to `energy/victron/forecast/solar/current` and `…/radiation_wm2` (shared Open-Meteo feed with Victron).
- **Deploy helpers:** `nodered/live-connection/scripts/deploy-flow-811-821.mjs` (merges flows 800, 811, 821 to live Node-RED).

### Tapo cameras

- **Flow 611** — Camera dashboard (`/dashboard/page6`), MQTT `garden/camera/#`, Telegram/SMS commands.
- **Flow 612** — Per-camera health watchdog (2 min), Telegram via flow 90.
- **Flow 613** — Unified watchdog status dashboard (`/dashboard/watchdog`).
- **`tapo-monitor.service`** — ONVIF motion/person, health heartbeats, SMS gateway enrollments.
- **Discovery:** `scripts/utils/camera_network_scan.py`, `config/cameras.env.example`, `scripts/server/apply_cameras_env.py`.
- **Docs:** [docs/TAPO_CAMERA.md](../TAPO_CAMERA.md).

### Node-RED live deploy scripts

- `deploy-flow-611.mjs`, `deploy-flow-612.mjs`, `deploy-flow-613.mjs`, `generate-flow-613.mjs`.

## Changed

- **Flow 800** — Energy page icon `battery-charging-100`; live dashboard binds to UI base `b89dd587275b51bf` / theme `39a2cf2c0af73875` (matches Gate, Cameras, Watchdog pages).
- **Flow 800** — `ui_group_huawei_energy` on Energy page (required for Huawei dashboard widget).
- **[docs/ENERGY_NODE_RED.md](../ENERGY_NODE_RED.md)** — chart behaviour, PV forecast, deploy notes.
- **[docs/MQTT_PROTOCOL.md](../MQTT_PROTOCOL.md)** — camera topics (if not already in your tree).
- **[nodered/flows/README.md](../../nodered/flows/README.md)** — flows 611–613, energy deploy, format version.

## Upgrade

```bash
git pull
sudo ./update.sh   # if publisher/monitor units changed

# Node-RED — import or deploy to automation server (192.168.2.4)
node nodered/live-connection/scripts/deploy-flow-811-821.mjs
node nodered/live-connection/scripts/deploy-flow-611.mjs
node nodered/live-connection/scripts/deploy-flow-612.mjs
node nodered/live-connection/scripts/deploy-flow-613.mjs

# Cameras — configure .env then restart monitor
python3 scripts/server/apply_cameras_env.py   # optional helper
sudo systemctl restart tapo-monitor.service
```

Verify:

- Energy: `http://<server>:1880/dashboard/energy` — Victron chart, Huawei PV forecast card, icon in nav.
- Cameras: `http://<server>:1880/dashboard/page6`
- Watchdog: `http://<server>:1880/dashboard/watchdog`
- MQTT: `mosquitto_sub -h localhost -t 'garden/camera/#' -v`
- MQTT: `mosquitto_sub -h localhost -t 'energy/victron/forecast/solar/current' -v`

## Quick links

- [Energy Node-RED](ENERGY_NODE_RED.md)
- [Tapo cameras](TAPO_CAMERA.md)
- [MQTT protocol](MQTT_PROTOCOL.md)
- [Flows README](../../nodered/flows/README.md)
