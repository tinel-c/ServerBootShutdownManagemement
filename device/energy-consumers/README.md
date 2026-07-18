# Energy consumer monitoring

Per-device **electricity consumption** reporting for the automation platform. **Tuya** meters (polled) and **Tasmota** devices (MQTT bridge) publish under `energy/consumers/<id>/…`. Node-RED flow **840** displays each consumer on the Energy dashboard after Huawei.

**Agent playbook:** [docs/ENERGY_CONSUMER_ADD.md](../../docs/ENERGY_CONSUMER_ADD.md)

## Layout

```text
device/energy-consumers/
├── config/consumers_registry.yaml      # canonical list (enabled → UI + publisher)
├── lib/
│   ├── consumer_schema.py              # MQTT status JSON shape
│   ├── tuya_meter.py                   # DPS parse, switch control, cloud phase
│   ├── tasmota_meter.py                # Tasmota ENERGY / POWER parse
│   └── tongou_phase.py                 # Tongou phase_a RAW decode (smart breakers)
├── scripts/
│   ├── tuya_consumers_publisher.py     # poll + MQTT + switch commands
│   ├── probe_tuya_dps.py               # discover Tuya DPS IDs
│   ├── add_consumer.py                 # scaffold folder + registry row
│   └── export_registry_for_nodered.py  # feed generate-flow-840.mjs
└── devices/<id>/                       # per-consumer device.yaml + README
```

## Architecture

```text
config/tuya_devices.json + consumers_registry.yaml  (Tuya)
tele/<tasmota_topic>/SENSOR on Mosquitto              (Tasmota)
              │
              ▼
energy-consumers-publisher.service  (tinytuya poll + Tasmota subscribe)
              │
              ▼
Mosquitto  energy/consumers/<id>/status
              │
              ▼
Node-RED 840  →  Dashboard /energy  (groups order 3+)
```

| Layer | Responsibility |
|-------|----------------|
| `consumers_registry.yaml` | IDs, Tuya device IDs, DPS map, UI order, enable flag |
| `lib/tongou_phase.py` | [Tongou phase_a](https://www.tongou.com/es/api/tuya-smart-device-api/) Base64 decode; cloud fetch |
| `lib/tuya_meter.py` | DPS parse, switch control, merge LAN + cloud metrics |
| `scripts/tuya_consumers_publisher.py` | Tuya poll + Tasmota bridge + switch commands |
| `nodered/flows/840-energy-consumers.json` | Generated UI (one card per consumer) |

## Device types

| Type | Example | DPS source |
|------|---------|------------|
| **DIN-rail switch + metering** | Front house lights | Scalar DPS `17`–`20`, switch `1` |
| **Tongou smart breaker** (`dlq`) | House consumption, Garden power | Cloud `phase_a` (DP 6) for V/I/P; LAN for switch, temp, energy — see [docs/TONGOU_BREAKER_DPS.md](../../docs/TONGOU_BREAKER_DPS.md) |
| **Tasmota** (`tasmota_meter`) | Garden Power Hut (POWR316D) | `sonoffPower320D_afara`; also Garden tab flow **310** |

## Quick start

```bash
python3 device/energy-consumers/scripts/validate_registry.py
sudo ./install_energy_consumers_service.sh    # on automation server
node nodered/live-connection/scripts/generate-flow-840.mjs
node nodered/live-connection/scripts/deploy-flow-840.mjs
mosquitto_sub -h localhost -t 'energy/consumers/+/status' -v
```

Dashboard: http://192.168.2.4:1880/dashboard/energy

## MQTT topics

| Topic | Retain | Payload |
|-------|--------|---------|
| `energy/consumers/<id>/status` | yes | JSON snapshot (see `lib/consumer_schema.py`) |
| `energy/consumers/<id>/command/switch` | no | `{ "action": "on" \| "off" \| "toggle" }` |

Status `extra` fields (when available): `switch_on`, `temperature_c`, `breaker_state`, `run_mode`, `phase_source`; when LAN poll fails but cloud phase_a succeeds: `lan_degraded`, `lan_err` (device still marked **online**); Tasmota: `energy_today`, `energy_yesterday`, `energy_period`, `energy_factor`, `energy_apparentpower`, `energy_reactivepower`, `energy_totalstarttime`, `tasmota_time`, `tasmota_topic`.

Full reference: [docs/MQTT_PROTOCOL.md](../../docs/MQTT_PROTOCOL.md#energy-consumers-topics-domain-energyconsumers).

## Related docs

- [docs/ENERGY_CONSUMER_ADD.md](../../docs/ENERGY_CONSUMER_ADD.md) — **standard agent workflow**
- [docs/TONGOU_BREAKER_DPS.md](../../docs/TONGOU_BREAKER_DPS.md) — smart breaker electrical decoding
- [docs/ENERGY_NODE_RED.md](../../docs/ENERGY_NODE_RED.md) — Energy dashboard
- [docs/TUYA_ACCOUNT_LINK.md](../../docs/TUYA_ACCOUNT_LINK.md) — Tuya account + device sync

## Status (v3.16.0)

| ID | Name | Enabled |
|----|------|---------|
| `front-lights-breaker` | Front house lights | yes |
| `breaker-inside` | House consumption | yes |
| `breaker-outside` | Garden power | yes |
| `garden-power-hut` | Garden Power Hut (Tasmota) | yes |

Flow **840** deployed. Publisher: `energy-consumers-publisher.service` on automation server.
