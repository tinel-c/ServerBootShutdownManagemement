# v3.11.8 (2026-07-04) — Huawei SUN2000 energy integration

Grid-tie solar monitoring for the Huawei SUN2000 inverter, following the same Modbus → MQTT → Node-RED → Telegram → watchdog pattern as Victron (v3.11.6).

## Added

### Device & publisher

- **`device/huawei-inverter/`** — Modbus reader, probe script, MQTT publisher, config template
- **`huawei-mqtt-publisher.service`** — polls inverter at `192.168.200.1:6607` (unit ID 0) every 10 s
- **MQTT namespace** `energy/huawei/#` — JSON snapshot on `energy/huawei/status`, plain-text scalars for metrics
- **Install/deploy:** `install_huawei_service.sh`, `scripts/server/setup_huawei_wifi.sh`, remote deploy scripts
- **Server verified:** SUN2000-6KTL-L1 (serial HV2310027721) via USB WiFi → inverter AP

### Node-RED

- **`800-energy-base-config.json`** — `ui_group_huawei_energy`, `global.huawei_energy_state` init
- **`821-huawei-energy-status.json`** — live dashboard cards (PV, inverter, daily yield)
- **`822-huawei-energy-telegram.json`** — `/huawei_status`, `/huawei_help`
- **`50-telegram-interface.json`** — Huawei section in `/help` and `/commands`
- **`90-device-watchdog.json`** — monitors `energy/huawei/status` (2 min timeout)

### Documentation

- [MQTT_PROTOCOL.md](../MQTT_PROTOCOL.md) — Huawei topics + status JSON schema (protocol v1.3)
- [ENERGY_NODE_RED.md](../ENERGY_NODE_RED.md) — Huawei import order and troubleshooting
- [ARCHITECTURE.md](../ARCHITECTURE.md), [AUTOMATION_ARCHITECTURE.md](../AUTOMATION_ARCHITECTURE.md)
- [REFERENCE.md](../REFERENCE.md), [UPDATE.md](../UPDATE.md), [README.md](../../README.md)

## Post-deploy checklist

```bash
# Publisher
systemctl status huawei-mqtt-publisher.service
mosquitto_sub -h localhost -t 'energy/huawei/status' -C 1

# Node-RED: import 800 → 821 → 822; re-import 50 and 90 (Replace existing nodes)
# Telegram: /huawei_status, /help (Huawei section)
```

## Quick links

- [Huawei device README](../../device/huawei-inverter/README.md)
- [MQTT Huawei topics](../MQTT_PROTOCOL.md#huawei-energy-topics-domain-energyhuawei)
- [Energy Node-RED guide](../ENERGY_NODE_RED.md)
