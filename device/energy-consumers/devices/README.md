# Per-device consumer integrations

Each subdirectory is **one consumer**. Folder name must match registry `id`.

**Standard workflow for agents:** [docs/ENERGY_CONSUMER_ADD.md](../../../docs/ENERGY_CONSUMER_ADD.md)

## Add a new device

```bash
python3 device/energy-consumers/scripts/add_consumer.py \
  --id my-new-plug --name "My new plug" --type tuya_meter \
  --tuya-device-id <from sync_devices.py> --order 6
```

Or manually:

```bash
cp -r device/energy-consumers/devices/_template device/energy-consumers/devices/my-new-plug
# Edit device.yaml, add row to config/consumers_registry.yaml
python3 device/energy-consumers/scripts/validate_registry.py
node nodered/live-connection/scripts/generate-flow-840.mjs
```

## Folder contents (per device)

| File | Purpose |
|------|---------|
| `device.yaml` | Consumer metadata (mirrors registry) |
| `README.md` | Optional: connection notes, troubleshooting |

Tuya meters and Tasmota devices use the shared publisher (`tuya_consumers_publisher.py`) — no per-device `publisher.py` required.

## Device types

| `type` in registry | Notes |
|--------------------|-------|
| `tuya_meter` | DPS map in registry; credentials from `tuya_devices.json` |
| `tasmota_meter` | Tasmota `tele/<topic>/SENSOR` → bridge in publisher; see `devices/garden-power-hut/` |
| `shelly_em` | Planned — HTTP or Shelly MQTT |
| `custom` | Document protocol in local README |

## Current devices

| Folder | Registry id |
|--------|-------------|
| `front-lights-breaker/` | `front-lights-breaker` (DIN rail, front house lights) |
| `breaker-inside/` | `breaker-inside` |
| `breaker-outside/` | `breaker-outside` (separate device @ 192.168.2.112) |
| `garden-power-hut/` | `garden-power-hut` (POWR316D @ hut; topic `sonoffPower320D_afara`, flow 310 + 840) |
