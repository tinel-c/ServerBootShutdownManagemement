# v3.16.0 (2026-07-05) — Tasmota energy consumers & Garden Power Hut

Adds **Tasmota** smart meters to the Energy dashboard alongside Tuya consumers. First live device: **Garden Power Hut** (SONOFF POWR316D) — same hardware as Garden tab Power (flow 310).

## Added

### `tasmota_meter` consumer type

| Item | Detail |
|------|--------|
| Library | `device/energy-consumers/lib/tasmota_meter.py` — parse Tasmota `ENERGY` from `tele/<topic>/SENSOR` |
| Publisher | `energy-consumers-publisher.service` subscribes to Tasmota MQTT; republishes `energy/consumers/<id>/status` |
| Registry | `tasmota_topic`, `tasmota_power_key`, `tasmota_command_key`, `stale_after_s` |
| Commands | Switch → `cmnd/<topic>/Power` (`ON` / `OFF` / `TOGGLE`) |

### Garden Power Hut (`garden-power-hut`)

| Item | Value |
|------|--------|
| Hardware | SONOFF POW Elite 16A (POWR316D), Tasmota WiFi |
| Tasmota topic | `sonoffPower320D_afara` (legacy name) |
| Garden tab | Flow **310** — direct Tasmota UI (unchanged) |
| Energy tab | Flow **840** — full telemetry card (order 6) |

**Energy card sections:** Live (W, V, A, PF) · Energy (Total, Today, Yesterday, Period Wh) · Power quality (Apparent W, Reactive W, Relay, source) · Device time, meter since, MQTT topic · ON/OFF.

### Flow 840 generator

- `tasmota_meter` gets expanded `ui-template` (taller group height 3).
- Tuya breakers keep compact 4-metric card (+ °C when configured).

## Live consumers (Energy tab)

| ID | Name | Type |
|----|------|------|
| `front-lights-breaker` | Front house lights | Tuya DIN rail |
| `breaker-inside` | House consumption | Tongou breaker |
| `breaker-outside` | Garden power (panel) | Tongou breaker |
| `garden-power-hut` | Garden Power Hut | Tasmota POWR316D |

## Upgrade

```bash
git pull
sudo ./update.sh

# Ensure garden-power-hut in device/energy-consumers/config/consumers_registry.yaml (enabled)
python3 device/energy-consumers/scripts/validate_registry.py
sudo systemctl restart energy-consumers-publisher.service

node nodered/live-connection/scripts/generate-flow-840.mjs
node nodered/live-connection/scripts/deploy-flow-840.mjs
```

Verify:

```bash
mosquitto_sub -h localhost -t 'energy/consumers/garden-power-hut/status' -v
```

Open http://192.168.2.4:1880/dashboard/energy

## Related docs

- [device/energy-consumers/devices/garden-power-hut/README.md](../../device/energy-consumers/devices/garden-power-hut/README.md)
- [docs/ENERGY_CONSUMER_ADD.md](../ENERGY_CONSUMER_ADD.md)
- [docs/MQTT_PROTOCOL.md](../MQTT_PROTOCOL.md#energy-consumers-topics-domain-energyconsumers)
