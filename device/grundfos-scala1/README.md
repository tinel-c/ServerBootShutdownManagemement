# Grundfos SCALA1 — BLE to MQTT integration

> **Status: planned (scaffolding only)** — not production-ready until on-site BLE GATT capture.  
> Overview and checklist: [docs/GRUNDGOS_SCALA1.md](../../docs/GRUNDGOS_SCALA1.md)

Planned pressure booster telemetry and control for the [Grundfos SCALA1](https://product-selection.grundfos.com/products/scala/scala1) via Bluetooth Low Energy → Mosquitto → Node-RED / Telegram.

This integration is **separate** from the Tasmota `pompaApa` relay board (flows `410`/`411`). Do not enable the systemd service or import flows `412`/`413` until GATT mapping is complete.

## Architecture

```text
SCALA1 (BLE)  →  grundfos-scala1-mqtt-publisher.service  →  Mosquitto
                                                                    ↓
                         Node-RED 412/413  ·  watchdog 90  ·  Telegram /scala1_*
```

If the automation server is out of BLE range, use an [ESP32 BLE proxy](docs/ESP32_BLE_PROXY.md) publishing the same MQTT topics.

## Prerequisites

- Ubuntu automation server with Bluetooth adapter (`hci0`) **or** ESP32 proxy near the pump
- Mosquitto on the LAN
- Pump commissioned with Grundfos GO (for initial pairing / reference readings)
- Python venv with `bleak` (installed via root `requirements.txt`)

## Quick start

1. **Scan for the pump**
   ```bash
   cd /opt/dell_server_management
   source venv/bin/activate
   python3 device/grundfos-scala1/scripts/ble_probe.py --scan
   ```

2. **Configure**
   ```bash
   sudo cp device/grundfos-scala1/config/.env.example device/grundfos-scala1/config/.env
   sudo nano device/grundfos-scala1/config/.env
   # Set SCALA1_BLE_ADDRESS and MQTT credentials
   sudo chmod 600 device/grundfos-scala1/config/.env
   ```

3. **Capture GATT layout** (required for decoded metrics)
   ```bash
   python3 device/grundfos-scala1/scripts/ble_probe.py --dump --json > /tmp/scala1_gatt.json
   ```
   Document UUIDs in [docs/BLE_PROTOCOL.md](docs/BLE_PROTOCOL.md) and set env vars or copy `metrics_map.example.yaml` → `metrics_map.yaml`.

4. **Install systemd service**
   ```bash
   sudo ./install_grundfos_service.sh
   ```

5. **Verify MQTT**
   ```bash
   mosquitto_sub -h localhost -t 'water/grundfos/scala1/status' -v
   journalctl -u grundfos-scala1-mqtt-publisher.service -f
   ```

6. **Node-RED** — import (after `400-irrigation-base-config.json`):
   - `412-grundfos-scala1-status.json`
   - `413-grundfos-scala1-telegram.json`
   - Re-import `50-telegram-interface.json` and `90-device-watchdog.json` (**Replace existing nodes**)

## Configuration reference

| Variable | Purpose |
|----------|---------|
| `SCALA1_BLE_ADDRESS` | Pump MAC (required) |
| `SCALA1_BLE_ADAPTER` | Linux HCI adapter (optional) |
| `SCALA1_MQTT_PREFIX` | Default `water/grundfos/scala1` |
| `SCALA1_POLL_INTERVAL` | Seconds between BLE reads (default 15) |
| `SCALA1_TELEMETRY_*_UUID` | GATT service/char for telemetry |
| `SCALA1_CONTROL_*` | GATT write + hex payloads for start/stop |
| `SCALA1_METRICS_MAP` | Path to YAML byte layout (optional) |

See [config/.env.example](config/.env.example).

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/ble_probe.py` | `--scan`, `--dump`, `--read` |
| `scripts/scala1_mqtt_publisher.py` | Production publisher (`--once` for test) |

## MQTT

Full specification: [docs/MQTT_PROTOCOL.md](../../docs/MQTT_PROTOCOL.md#grundfos-scala1-topics-domain-watergrundfosscala1).

## Telegram commands

- `/scala1_status` — live snapshot
- `/scala1_start`, `/scala1_stop` — BLE control (when configured)
- `/scala1_help`

## Troubleshooting

| Symptom | Check |
|---------|--------|
| Service fails immediately | `SCALA1_BLE_ADDRESS` set? `bluetoothctl` shows adapter up? |
| MQTT connects but empty metrics | Run `ble_probe.py --dump`; fill GATT UUIDs / metrics_map |
| Intermittent offline watchdog | BLE range — see [ESP32_BLE_PROXY.md](docs/ESP32_BLE_PROXY.md) |
| Control commands no effect | Pairing may block writes; verify with Grundfos GO first |

## Related flows

- **410/411** — Tasmota `pompaApa` relays (unchanged)
- **412/413** — Grundfos SCALA1 dashboard + Telegram
