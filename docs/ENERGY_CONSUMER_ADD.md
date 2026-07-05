# Adding an energy consumer (agent playbook)

Standard workflow for any Cursor agent (or human) adding a **new electricity consumer** to the Energy dashboard (`/energy`), after the Huawei canvas.

**Canonical reference:** `device/energy-consumers/` + Node-RED flow **840**.

---

## When to use this

- New Tuya smart meter / breaker / DIN-rail switch with metering
- Tasmota energy device (Sonoff POWR316D, POWR320D, etc.) on local Mosquitto
- Future: Shelly EM, ESP32, custom MQTT publisher

All consumers share the same registry, MQTT layout, publisher service, and UI generator.

---

## Architecture

```text
config/tuya_devices.json          consumers_registry.yaml
        │                                    │
        └──────────┬─────────────────────────┘
                   ▼
     energy-consumers-publisher.service  (Tuya poll + Tasmota bridge)
                   │
                   ▼
        Mosquitto  energy/consumers/<id>/status  (+ command/switch)
                   │
                   ▼
     Node-RED 840  (generate-flow-840.mjs → 840-energy-consumers.json)
                   │
                   ▼
        Dashboard /energy  (ui_group per consumer, order after Huawei=2)
```

---

## Checklist (Tuya meter)

| Step | Command / action |
|------|------------------|
| 1. Tuya credentials | `config/.env` has `TUYA_ACCESS_ID` / `TUYA_ACCESS_KEY`; run `scripts/tuya/sync_devices.py sync` |
| 2. Scaffold | `python3 device/energy-consumers/scripts/add_consumer.py --id <id> --name "<Name>" --type tuya_meter --tuya-device-id <id> --order <3+>` |
| 3. Probe DPS | `python3 device/energy-consumers/scripts/probe_tuya_dps.py --device-id <tuya_id>` — map `dps:` in registry. **DIN rail:** scalars `17`–`20`. **Tongou breaker (`dlq`):** add `phase_a: "6"`; see [TONGOU_BREAKER_DPS.md](TONGOU_BREAKER_DPS.md) |
| 4. Enable | Set `enabled: true` in `config/consumers_registry.yaml` |
| 5. Validate | `python3 device/energy-consumers/scripts/validate_registry.py` |
| 6. Generate UI | `node nodered/live-connection/scripts/generate-flow-840.mjs` |
| 7. Deploy UI | `node nodered/live-connection/scripts/deploy-flow-840.mjs` (or import `840-energy-consumers.json` manually) |
| 8. Publisher | `sudo ./install_energy_consumers_service.sh` on automation server |
| 9. Verify | `mosquitto_sub -h localhost -t 'energy/consumers/+/status' -v` and open `/dashboard/energy` |

**UI order:** Victron = 1, Huawei = 2, consumers = 3, 4, 5, … (set `ui.order` in registry).

---

## Checklist (Tasmota meter)

| Step | Command / action |
|------|------------------|
| 1. Tasmota MQTT | Device broker = automation server Mosquitto; note **Topic** (`Topic` command in console) |
| 2. Scaffold | Copy `devices/garden-power-hut/` or `add_consumer.py --type tasmota_meter --tasmota-topic <topic>` |
| 3. Registry | `type: tasmota_meter`, `tasmota_topic: <topic>`, optional `tele_period_s: 30`, `stale_after_s: 120` |
| 4. Enable | `enabled: true` in `consumers_registry.yaml` |
| 5–9 | Same validate / generate / deploy / restart publisher / verify as Tuya checklist |

Publisher subscribes to `tele/<topic>/SENSOR` and `stat/<topic>/POWER`, republishes to `energy/consumers/<id>/status`. Switch commands forward to `cmnd/<topic>/Power`.

Reference device: [device/energy-consumers/devices/garden-power-hut/README.md](../device/energy-consumers/devices/garden-power-hut/README.md).

---

## Registry entries

### DIN-rail switch with metering (front lights)

```yaml
dps:
  switch: "1"
  power_w: { id: "19", scale: 0.1 }
  voltage_v: { id: "20", scale: 0.1 }
  current_a: { id: "18", scale: 0.001 }
  energy_kwh: { id: "17", scale: 0.01 }
```

### Tongou smart breaker (house / garden)

Per [Tongou Tuya smart device API](https://www.tongou.com/es/api/tuya-smart-device-api/) — `phase_a` is an 8-byte Base64 blob (V ÷10, A ÷1000, P in W). On our `dlq` breakers, **cloud** `phase_a` (DP 6) is used for V/I/P; LAN provides switch, temperature, energy.

```yaml
dps:
  phase_a: "6"
  switch: "16"
  power_w: { id: "119", scale: 0.271475 }      # LAN fallback only
  voltage_v: { id: "115", scale: 0.916538 }
  current_a: { id: "114", scale: 0.21715 }
  temperature_c: { id: "131", scale: 0.1 }
  energy_kwh: { id: "125", scale: 0.0001 }
```

Full detail: [TONGOU_BREAKER_DPS.md](TONGOU_BREAKER_DPS.md).

### Tasmota meter (Garden Power Hut)

Same physical device can appear on **Garden** (flow 310) and **Energy** (flow 840). Registry bridges Tasmota MQTT into `energy/consumers/<id>/status`:

```yaml
- id: garden-power-hut
  name: Garden Power Hut
  type: tasmota_meter
  enabled: true
  tasmota_topic: sonoffPower320D_afara
  tasmota_power_key: POWER
  tasmota_command_key: Power
  stale_after_s: 660
  controls:
    switch: true
  ui:
    order: 6
    accent: "#f59e0b"
```

Do **not** set `tele_period_s` unless you intend to change the device’s Tasmota `TelePeriod` on publisher start.

---

### Legacy scalar example (DIN-rail plug)

```yaml
- id: example-plug
  name: Example plug
  type: tuya_meter
  enabled: false
  tuya_device_id: xxxxxxxxxxxxxxxx
  mqtt_prefix: energy/consumers/example-plug
  device_path: devices/example-plug
  poll_interval_s: 30
  controls:
    switch: true
  ui:
    order: 6
    accent: "#38bdf8"
  dps:
    switch: "1"
    power_w: { id: "19", scale: 0.1 }
    voltage_v: { id: "20", scale: 0.1 }
    current_a: { id: "18", scale: 0.001 }
    energy_kwh: { id: "17", scale: 0.01 }
```

Credentials (`local_key`, `ip`) come from `config/tuya_devices.json` — **never** put keys in the registry.

---

## MQTT contract

| Topic | Direction | Payload |
|-------|-----------|---------|
| `energy/consumers/<id>/status` | Publisher → broker (retained) | JSON: `power_w`, `energy_kwh`, `voltage_v`, `current_a`, `online`, `timestamp`, `extra` (`switch_on`, `temperature_c`, `breaker_state`, `run_mode`, `phase_source`) |
| `energy/consumers/<id>/command/switch` | Node-RED → publisher | `{ "action": "on" \| "off" \| "toggle" }` |
| `energy/consumers/<id>/response` | Publisher → broker | Command result JSON |

See [MQTT_PROTOCOL.md](MQTT_PROTOCOL.md#energy-consumers-domain-energyconsumers).

---

## Node-RED flow 840

- **Source:** `nodered/flows/840-energy-consumers.json` (generated — do not hand-edit)
- **Regenerate** after any registry change (add/remove/reorder consumer):

  ```bash
  node nodered/live-connection/scripts/generate-flow-840.mjs
  ```

- **Deploy to live Node-RED:**

  ```bash
  node nodered/live-connection/scripts/deploy-flow-840.mjs
  ```

Each enabled consumer gets:
- `ui_group_consumer_<id>` on `ui_page_energy` (full width)
- Dashboard card: W, kWh, V, A, °C (when `temperature_c` in DPS), Online pill, **Updated MM:SS ago**, ON/OFF (if `controls.switch: true`)

Requires `800-energy-base-config.json` imported first (Energy page + Huawei group).

---

## Files an agent must touch

| Path | Purpose |
|------|---------|
| `device/energy-consumers/config/consumers_registry.yaml` | Canonical consumer list |
| `device/energy-consumers/devices/<id>/` | Per-device notes + `device.yaml` |
| `device/energy-consumers/lib/tuya_meter.py` | DPS parse, switch, cloud phase merge |
| `device/energy-consumers/lib/tasmota_meter.py` | Tasmota ENERGY parse + topic helpers |
| `device/energy-consumers/lib/tongou_phase.py` | Tongou phase_a decode + cloud fetch |
| `device/energy-consumers/scripts/add_consumer.py` | Scaffold new consumer |
| `device/energy-consumers/scripts/probe_tuya_dps.py` | Discover Tuya DPS IDs |
| `nodered/live-connection/scripts/generate-flow-840.mjs` | Build flow JSON from registry |
| `nodered/live-connection/scripts/deploy-flow-840.mjs` | Push flow to Node-RED |
| `install_energy_consumers_service.sh` | Install/update systemd publisher |

Do **not** duplicate UI nodes manually — always regenerate flow 840.

---

## Current consumers (v3.16.0)

| ID | Name | Source | UI order | Notes |
|----|------|--------|----------|-------|
| `front-lights-breaker` | Front house lights | Tuya `bf8cc8cf863af4b600yc53` | 3 | DIN-rail, outdoor |
| `breaker-inside` | House consumption | Tuya `bf05a4a80c7e10134dx5gp` | 4 | Tongou breaker, main panel |
| `breaker-outside` | Garden power (panel) | Tuya `bfb1f58994ced1e2fajvee` | 5 | Tongou breaker, indoor panel feed |
| `garden-power-hut` | Garden Power Hut | Tasmota `sonoffPower320D_afara` | 6 | POWR316D @ hut; also Garden tab flow 310 |

---

## Troubleshooting

| Symptom | Check |
|---------|--------|
| No MQTT | `systemctl status energy-consumers-publisher.service`, `journalctl -u energy-consumers-publisher -f` |
| Wrong readings (breaker) | Confirm `phase_a: "6"` in registry; check `extra.phase_source` is `tongou_cloud`; see [TONGOU_BREAKER_DPS.md](TONGOU_BREAKER_DPS.md) |
| Wrong readings (DIN rail) | Re-run `probe_tuya_dps.py`, fix `dps:` scales |
| Missing dashboard panel | Consumer `enabled: true`? Re-run `generate-flow-840.mjs` + deploy |
| Switch buttons no-op | Publisher subscribed to `energy/consumers/+/command/#`; device `controls.switch: true` |

---

## Related

- [device/energy-consumers/README.md](../device/energy-consumers/README.md)
- [ENERGY_NODE_RED.md](ENERGY_NODE_RED.md)
- [TUYA_ACCOUNT_LINK.md](TUYA_ACCOUNT_LINK.md)
