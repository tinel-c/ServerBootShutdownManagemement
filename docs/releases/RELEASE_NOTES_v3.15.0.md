# v3.15.0 (2026-07-05) — Energy consumers & Tongou smart breakers

Tuya energy meters and smart breakers on the **Energy** dashboard (`/energy`), with a standardized agent workflow for adding more consumers.

## Added

### Energy consumers package (`device/energy-consumers/`)

- **Registry**: `config/consumers_registry.yaml` — enable flag, Tuya device ID, DPS map, UI order, MQTT prefix.
- **Publisher**: `energy-consumers-publisher.service` — polls tinytuya every 30 s, retained `energy/consumers/<id>/status`, switch commands on `command/switch`.
- **Scripts**: `add_consumer.py`, `probe_tuya_dps.py`, `validate_registry.py`, `export_registry_for_nodered.py`.
- **Install**: `./install_energy_consumers_service.sh` (also wired in `install.sh` / `update.sh`).

### Node-RED flow 840

| Item | Detail |
|------|--------|
| Generate | `node nodered/live-connection/scripts/generate-flow-840.mjs` |
| Deploy | `node nodered/live-connection/scripts/deploy-flow-840.mjs` |
| Dashboard | `/dashboard/energy` — one full-width card per consumer (order 3+) |
| UI | Power, kWh, V, A, temperature (breakers), relay ON/OFF, **Updated** timer beside Online pill |

### Tongou smart breaker decoding

Per [Tongou Tuya smart device API](https://www.tongou.com/es/api/tuya-smart-device-api/):

- **`lib/tongou_phase.py`** — Base64 `phase_a` → voltage (÷10), current (÷1000), power (W).
- **Cloud fallback** — when LAN status has no RAW `phase_a` (typical for `dlq` breakers), publisher fetches cloud `phase_a` (DP 6).
- **Docs**: [docs/TONGOU_BREAKER_DPS.md](../TONGOU_BREAKER_DPS.md).

### Live consumers

| ID | Name | Device |
|----|------|--------|
| `front-lights-breaker` | Front house lights | DIN rail `bf8cc8cf863af4b600yc53` |
| `breaker-inside` | House consumption | Main breaker `bf05a4a80c7e10134dx5gp` |
| `breaker-outside` | Garden power | Indoor panel garden circuit `bfb1f58994ced1e2fajvee` |

### Agent / deploy

- [docs/ENERGY_CONSUMER_ADD.md](../ENERGY_CONSUMER_ADD.md) — step-by-step playbook.
- `.cursor/rules/automation-server-access.mdc` — git pull + `update.sh` on `192.168.2.4` (no scp for routine deploy).

## Fixed

- MQTT client wildcard matching for `energy/consumers/+/command/#`.
- Publisher MQTT loop conflict (`loop_start` + `loop()`).
- `device_service.sh` in-place install bug.

## Upgrade

```bash
git pull
pip install -r requirements.txt
sudo ./update.sh

# On automation server — if publisher not yet installed
sudo ./install_energy_consumers_service.sh

# Regenerate + deploy flow 840 (from dev machine with Node-RED API access)
node nodered/live-connection/scripts/generate-flow-840.mjs
node nodered/live-connection/scripts/deploy-flow-840.mjs
```

Verify:

```bash
systemctl status energy-consumers-publisher.service
mosquitto_sub -h localhost -t 'energy/consumers/+/status' -v
```

Open http://192.168.2.4:1880/dashboard/energy

## Related docs

- [device/energy-consumers/README.md](../../device/energy-consumers/README.md)
- [docs/TONGOU_BREAKER_DPS.md](../TONGOU_BREAKER_DPS.md)
- [docs/MQTT_PROTOCOL.md](../MQTT_PROTOCOL.md#energy-consumers-topics-domain-energyconsumers)
- [docs/ENERGY_NODE_RED.md](../ENERGY_NODE_RED.md)
