# Energy — Node-RED Dashboard

Live energy metrics on the Node-RED Dashboard 2.0 **Energy** page, fed by MQTT from Modbus publishers on the automation server.

- **Victron** Cerbo GX / MultiPlus-II → `energy/victron/*` (flows `800`–`812`)
- **Huawei** SUN2000 grid-tie inverter → `energy/huawei/*` (flows `821`–`822`)

---

## Victron Cerbo GX / MultiPlus-II

## Data transmission

```text
Cerbo GX (192.168.x.x:502 Modbus TCP)
        │
        ▼
victron-mqtt-publisher.service  (poll every 10 s)
        │
        ▼
Mosquitto MQTT broker
  • energy/victron/status     ← JSON snapshot (used by Node-RED)
  • energy/victron/battery/soc, grid/power_l1, …  ← plain-text scalars
        │
        ▼
Node-RED flow 811 (mqtt in → function → ui-template)
        │
        ├── Dashboard 2.0  /energy  (Victron Energy group)
        └── global.victron_energy_state  (for Telegram / automations)
```

The dashboard subscribes only to **`energy/victron/status`**. One message per poll cycle keeps battery, grid, PV, load, and inverter values in sync.

Full topic list: [MQTT_PROTOCOL.md — Victron Energy](MQTT_PROTOCOL.md#victron-energy-topics-domain-energyvictron).

## Prerequisites

1. **Node-RED** running (`systemctl status nodered`)
2. **Dashboard 2.0** (`@flowfuse/node-red-dashboard`) installed
3. **`00-base-config.json`** already imported (`mqtt_broker_local`, `ui_base`)
4. **`victron-mqtt-publisher.service`** active on the automation server
5. **`victron-solar-forecast-publisher.service`** for Open-Meteo forecast topics (optional but recommended)
6. MQTT broker reachable from Node-RED (same host or `MQTT_BROKER_HOST`)

Verify MQTT before importing flows:

```bash
mosquitto_sub -h localhost -t 'energy/victron/status' -v
```

You should see JSON every ~10 seconds.

## Import order

Import **after** `00-base-config.json`. Recommended position in the full stack:

| Order | File | Purpose |
|-------|------|---------|
| 1 | `00-base-config.json` | MQTT broker, home page groups |
| … | *(server, gate, power, … flows as needed)* | |
| N | **`800-energy-base-config.json`** | Energy page + `ui_group_victron_energy` |
| N+1 | **`811-victron-energy-status.json`** | Live dashboard |
| N+2 | **`812-victron-energy-telegram.json`** | Telegram commands (requires flow 50) |

### Steps

1. Open Node-RED: `http://<automation-server>:1880`
2. Menu → **Import** → select `nodered/flows/800-energy-base-config.json` → **Import**
3. Repeat for `811-victron-energy-status.json`
4. Import `812-victron-energy-telegram.json`
5. **Update `/help`:** import `50-telegram-interface.json` **or** the smaller patch `50-patch-victron-energy-help.json` (choose **Replace existing nodes** when prompted)
6. **Deploy**
7. Send `/help` in Telegram — confirm **☀️ VICTRON ENERGY** section appears
5. Open dashboard: `http://<automation-server>:1880/dashboard/energy`

## Flow files

### `800-energy-base-config.json`

- **UI page:** Energy (`/energy`, icon `solar_power`)
- **UI group:** Victron Energy (12 columns)
- **Context init:** creates empty `global.victron_energy_state` on startup

### `811-victron-energy-status.json`

- **Subscribes:** `energy/victron/status`, `energy/victron/forecast/solar/current`, `energy/victron/forecast/solar/daily` (QoS 1, JSON)
- **Publishes:** `energy/victron/command/discretionary/start|stop`, retained `energy/victron/automation/discretionary_load/state` (dashboard buttons)
- **Stores:** `global.victron_energy_state`, flow `victron_week_history` (7-day, 15 min buckets), discretionary load state, forecast cache
- **Displays:** live metrics, automation headroom banner, **7-day SVG chart** (PV, load, grid, headroom, inverter out, SoC), solar forecast chips, Start/Stop discretionary load buttons

### `812-victron-energy-telegram.json`

- **Commands:** `/energy_status`, `/energy_start`, `/energy_stop`, `/energy_help`
- **Reads:** `global.victron_energy_state` (updated by flow 811)
- **Publishes:** same discretionary MQTT topics as the dashboard (start/stop + retained state)
- **Requires:** `50-telegram-interface.json` (authorization + link to domain parsers)

## Dashboard layout

| Section | Metrics |
|---------|---------|
| Header | Inverter state badge, grid-lost alert, last update |
| Summary cards | Battery SoC, grid L1, consumption L1, PV AC output |
| Automation | Headroom (PV − load), `can_add_load`, Start/Stop discretionary buttons, ON/OFF badge |
| 7-day chart | PV, load, grid, headroom, inverter AC out, SoC (15 min buckets, flow context) |
| Solar forecast | Current irradiance, today’s sum, day/night (Open-Meteo) |
| Battery | Voltage, charge/discharge power |
| Load & VE.Bus | Output L1, input L1, AC out power |
| Inverter | State code, AC in V/P, DC bus |
| Solar / PV | AC grid L1, DC current |

**Sign conventions** (from Victron Modbus registers):

- **Grid L1:** positive = import, negative = export
- **Battery power:** positive = charging, negative = discharging

## Shared global context

Other flows (Telegram flow **812**, future automations) can read:

```javascript
const energy = global.get('victron_energy_state');
// energy.battery.soc_pct, energy.grid.power_l1_w, energy.inverter.state, …
```

Initialized by flow **800**; updated on every `energy/victron/status` message in flow **811**.

**Watchdog:** flow **90** monitors `energy/victron/status` (2 min timeout) and sends Telegram alerts when `victron-mqtt-publisher.service` or Cerbo reporting stops.

## Troubleshooting

| Symptom | Check |
|---------|--------|
| Dashboard shows “Waiting for energy/victron/status” | `systemctl status victron-mqtt-publisher.service`; `mosquitto_sub -t 'energy/victron/status'` |
| “Node configuration error” on import | Import `800-energy-base-config.json` before `811` |
| Stale values | Publisher poll interval (default 10 s); Cerbo Modbus connectivity |
| Empty MPPT section | Normal if no MPPT on VE.Direct; AC-coupled PV still shown under PV cards |

---

## Huawei SUN2000

### Data transmission

```text
SUN2000 inverter AP (192.168.200.1:6607 Modbus TCP, unit ID 0)
        │  USB WiFi on automation server
        ▼
huawei-mqtt-publisher.service  (poll every 10 s)
        │
        ▼
Mosquitto MQTT broker
  • energy/huawei/status     ← JSON snapshot (used by Node-RED)
  • energy/huawei/pv/*, inverter/*  ← plain-text scalars
        │
        ▼
Node-RED flow 821 (mqtt in → function → ui-template)
        │
        ├── Dashboard 2.0  /energy  (Huawei Energy group)
        └── global.huawei_energy_state  (for Telegram / automations)
```

The dashboard subscribes only to **`energy/huawei/status`**. One message per poll cycle keeps device, PV, and inverter values in sync.

Full topic list: [MQTT_PROTOCOL.md — Huawei Energy](MQTT_PROTOCOL.md#huawei-energy-topics-domain-energyhuawei).

### Prerequisites

1. **Node-RED** running (`systemctl status nodered`)
2. **Dashboard 2.0** installed
3. **`00-base-config.json`** and **`800-energy-base-config.json`** imported
4. **`huawei-mqtt-publisher.service`** active; USB WiFi connected to inverter AP
5. MQTT broker reachable from Node-RED

Verify MQTT before importing flows:

```bash
mosquitto_sub -h localhost -t 'energy/huawei/status' -v
```

### Import order

| Order | File | Purpose |
|-------|------|---------|
| 1 | `800-energy-base-config.json` | Energy page + `ui_group_huawei_energy` |
| 2 | **`821-huawei-energy-status.json`** | Live Huawei dashboard |
| 3 | **`822-huawei-energy-telegram.json`** | Telegram `/huawei_*` commands |

Re-import **`50-telegram-interface.json`** (Replace existing nodes) for `/help` Huawei section. Re-import **`90-device-watchdog.json`** to monitor `energy/huawei/status` (2 min timeout).

### Flow files

#### `821-huawei-energy-status.json`

- **Subscribes:** `energy/huawei/status` (QoS 1, JSON)
- **Stores:** `global.huawei_energy_state`
- **Displays:** model/serial, PV strings, active power, grid frequency, daily yield

#### `822-huawei-energy-telegram.json`

- **Commands:** `/huawei_status`, `/huawei_help`
- **Reads:** `global.huawei_energy_state` (updated by flow 821)
- **Requires:** `50-telegram-interface.json`

### Shared global context

```javascript
const huawei = global.get('huawei_energy_state');
// huawei.device.model, huawei.pv.input_power_w, huawei.inverter.active_power_w, …
```

Initialized by flow **800**; updated on every `energy/huawei/status` message in flow **821**.

**Watchdog:** flow **90** monitors `energy/huawei/status` (2 min timeout) and sends Telegram alerts when the publisher or inverter reporting stops.

### Troubleshooting

| Symptom | Check |
|---------|--------|
| Dashboard shows “Waiting for energy/huawei/status” | `systemctl status huawei-mqtt-publisher.service`; WiFi to inverter AP; `mosquitto_sub -t 'energy/huawei/status'` |
| Modbus connect failed | `device/huawei-inverter/scripts/modbus_probe.py`; verify `192.168.200.1:6607` from automation server |
| “Node configuration error” on import | Import `800-energy-base-config.json` before `821` |

---

## Related documentation (both systems)

- [device/victron-multiplus-ii/README.md](../device/victron-multiplus-ii/README.md) — Cerbo setup, Modbus Unit IDs, server install
- [device/huawei-inverter/README.md](../device/huawei-inverter/README.md) — SUN2000 WiFi AP, Modbus probe, systemd install
- [MQTT_PROTOCOL.md](MQTT_PROTOCOL.md) — message formats
- [nodered/flows/README.md](../nodered/flows/README.md) — all modular flows
- [developer/SERVER_DEPLOY.md](developer/SERVER_DEPLOY.md) — deploy publisher to automation server
