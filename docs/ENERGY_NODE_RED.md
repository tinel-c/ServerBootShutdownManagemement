# Energy — Node-RED Dashboard

Live energy metrics on the Node-RED Dashboard 2.0 **Energy** page, fed by MQTT from Modbus publishers on the automation server.

- **Victron** Cerbo GX / MultiPlus-II → `energy/victron/*` (flows `800`–`812`)
- **Huawei** SUN2000 grid-tie inverter → `energy/huawei/*` (flows `821`–`822`)
- **Consumers** Tuya smart meters / breakers + Tasmota meters → `energy/consumers/*` (flow `840`)

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
5. **Update `/help`:** import `50-telegram-interface.json` (choose **Replace existing nodes** when prompted)
6. **Deploy**
7. Send `/help` in Telegram — confirm **☀️ VICTRON ENERGY** section appears
5. Open dashboard: `http://<automation-server>:1880/dashboard/energy`

## Flow files

### `800-energy-base-config.json`

- **UI page:** Energy (`/energy`, icon `battery-charging-100`)
- **UI groups:** Victron Energy, Huawei Solar (12 columns each)
- **Live dashboard:** page binds to UI base `b89dd587275b51bf` and theme `39a2cf2c0af73875` (same as Gate, Cameras, Watchdog on the automation server)
- **Context init:** creates empty `global.victron_energy_state` and `global.huawei_energy_state` on startup

### `811-victron-energy-status.json`

- **Subscribes:** `energy/victron/status`, `energy/victron/forecast/solar/current`, `energy/victron/forecast/solar/daily` (QoS 1, JSON)
- **Publishes:** `energy/victron/command/discretionary/start|stop`, retained `energy/victron/automation/discretionary_load/state` (dashboard buttons)
- **Stores:** `global.victron_energy_state`, flow `victron_week_history` (7-day, 15 min buckets), `victron_day_history` (24 h, 1 min buckets), discretionary load state, forecast cache
- **Displays:** live metrics, automation headroom banner, **history chart** with **1 hour / 24 hours / 7 days** tabs (1 min buckets for 1h & 1d; 15 min for 7d), hover tooltips; SoC in lower band (100% at top); solar forecast chips; Start/Stop discretionary load buttons

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
| History chart | PV, load, grid, headroom, inverter AC out, SoC — tabs: **1 hour** (1 min), **24 hours** (1 min), **7 days** (15 min); hover for values |
| Solar forecast | Current irradiance (W/m²), today’s sum, day/night (Open-Meteo) |
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

### Live deploy (automation server)

From a workstation with Node-RED Admin API access (`NODE_RED_BASE_URL`, default `http://192.168.2.4:1880`):

```bash
node nodered/live-connection/scripts/deploy-flow-811-821.mjs
```

Merges flows **800**, **811**, and **821** into the running editor (replace-by-node-id). Use after editing energy flow JSON in git.

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

- **Subscribes:** `energy/huawei/status`, `energy/victron/forecast/solar/current`, `energy/victron/forecast/solar/radiation_wm2` (QoS 1; forecast shared with Victron Open-Meteo publisher)
- **Stores:** `global.huawei_energy_state`, flow `huawei_week_history` (7-day, 15 min buckets), `huawei_day_history` (24 h, 1 min buckets)
- **Displays:** model/serial, PV strings (**string 1 · west**, **string 2 · east**), active power, grid frequency, daily yield, **active-power chart** with **1 hour / 24 hours / 7 days** tabs, **PV forecast card** (expected vs actual from irradiance model)

#### PV forecast model

Site wiring: **20 panels** — string 1 west, string 2 east (10 panels per string).

```text
P_est = P_rated × (G / 1000) × η
P_est_string1 = P_est × w_west / (w_east + w_west)
P_est_string2 = P_est × w_east / (w_east + w_west)
```

- **G** — Open-Meteo shortwave radiation (`energy/victron/forecast/solar/current` or scalar `…/radiation_wm2`)
- **η** — system efficiency (default 0.85)
- **w_east / w_west** — Gaussian orientation weights by local hour (Europe/Bucharest)

Reference implementation: [device/huawei-inverter/lib/pv_forecast_model.py](../device/huawei-inverter/lib/pv_forecast_model.py)

Actual power per string: **V × I** from `energy/huawei/status`. Performance % = actual total / expected total.

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
| Huawei section missing on Energy page | Ensure flow 800 includes `ui_group_huawei_energy` and page `ui` = live UI base (`b89dd587275b51bf`) |
| PV forecast expected = 0 W | Check `energy/victron/forecast/solar/current`; `victron-solar-forecast-publisher.service` |

---

## Energy consumers (Tuya & Tasmota)

Per-consumer panels on the same **Energy** page, **after** the Huawei group (`ui.order` 3+). Full agent workflow: [ENERGY_CONSUMER_ADD.md](ENERGY_CONSUMER_ADD.md).

### Data path

```text
Tuya: tuya_devices.json + registry → publisher (tinytuya poll, 30 s)
Tasmota: tele/<topic>/SENSOR on Mosquitto → publisher (subscribe → normalize)
        │
        ▼
Mosquitto  energy/consumers/<id>/status
        │
        ▼
Node-RED flow 840  (mqtt in → ui-template per consumer)
        │
        └── Dashboard /energy  (breakers, DIN rail, Garden Power Hut, …)
```

### Prerequisites

1. `config/tuya_devices.json` synced for **Tuya** consumers (`scripts/tuya/sync_devices.py sync`)
2. `device/energy-consumers/config/consumers_registry.yaml` with `enabled: true` entries
3. **`energy-consumers-publisher.service`** active
4. Flow **`800-energy-base-config.json`** already imported

Verify MQTT:

```bash
mosquitto_sub -h localhost -t 'energy/consumers/+/status' -v
```

### Import / deploy

| Step | Action |
|------|--------|
| Generate | `node nodered/live-connection/scripts/generate-flow-840.mjs` |
| Deploy | `node nodered/live-connection/scripts/deploy-flow-840.mjs` |
| Or manual | Import `nodered/flows/840-energy-consumers.json` after `800` |

Regenerate flow 840 after **any** registry change (add/remove/reorder consumer).

### UI layout

| Group | `ui.order` on Energy page |
|-------|---------------------------|
| Victron Energy | 1 |
| Huawei Energy | 2 |
| Each consumer | 3, 4, 5, 6, … (`ui.order` in registry) |

**Tuya cards** (compact): W, kWh, V, A, °C (breakers), Online + **Updated** timer, relay ON/OFF. Tongou breakers: cloud `phase_a` — [TONGOU_BREAKER_DPS.md](TONGOU_BREAKER_DPS.md).

**Tasmota cards** (`garden-power-hut`, etc.): expanded — Live (W, V, A, PF), Energy (Total, Today, Yesterday, Period Wh), power quality, device time, MQTT topic. May duplicate a Garden-tab device (flow **310**).

---

## Related documentation (both systems)

- [device/victron-multiplus-ii/README.md](../device/victron-multiplus-ii/README.md) — Cerbo setup, Modbus Unit IDs, server install
- [device/huawei-inverter/README.md](../device/huawei-inverter/README.md) — SUN2000 WiFi AP, Modbus probe, systemd install
- [MQTT_PROTOCOL.md](MQTT_PROTOCOL.md) — message formats
- [nodered/flows/README.md](../nodered/flows/README.md) — all modular flows
- [developer/SERVER_DEPLOY.md](developer/SERVER_DEPLOY.md) — deploy publisher to automation server
