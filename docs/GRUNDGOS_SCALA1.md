# Grundfos SCALA1 — planned integration

**Status: planned (not production-ready)**

Scaffolding for a separate [Grundfos SCALA1](https://product-selection.grundfos.com/products/scala/scala1) pressure booster lives in this repo. It is **not** a finished feature: there is no public BLE/GATT specification, and decoded telemetry requires on-site capture with Grundfos GO + `ble_probe.py`.

Water pump control today remains the Tasmota board (`pompaApa`, Node-RED flows **410** / **411**). SCALA1 is a **new, additional** pump — those flows are unchanged.

## What is in the repo (scaffolding)

| Area | Path | Notes |
|------|------|--------|
| BLE probe & publisher | [device/grundfos-scala1/](../device/grundfos-scala1/) | `ble_probe.py`, `scala1_mqtt_publisher.py`, `.env.example` |
| Protocol capture guide | [device/grundfos-scala1/docs/BLE_PROTOCOL.md](../device/grundfos-scala1/docs/BLE_PROTOCOL.md) | Fill UUIDs after on-site dump |
| ESP32 proxy spec (optional) | [device/grundfos-scala1/docs/ESP32_BLE_PROXY.md](../device/grundfos-scala1/docs/ESP32_BLE_PROXY.md) | If host BLE range is insufficient |
| MQTT topic spec | [MQTT_PROTOCOL.md](MQTT_PROTOCOL.md#grundfos-scala1-topics-domain-watergrundfosscala1) | Target namespace `water/grundfos/scala1/*` |
| Node-RED flows | `412`, `413` | Dashboard + Telegram `/scala1_*` — import **only when publisher is working** |
| systemd unit | `grundfos-scala1-mqtt-publisher.service` | Install manually: `sudo ./install_grundfos_service.sh` |
| Watchdog | flow `90` | Monitors `water/grundfos/scala1/status` once enabled |

## Blockers before “finished”

1. **BLE GATT reverse engineering** — proprietary Grundfos GO protocol; UUIDs and payload layout unknown until captured on the pump.
2. **BLE range** — automation server must reach the pump, or deploy an ESP32 BLE→MQTT proxy (see ESP32 doc).
3. **On-site validation** — pressure, flow, alarms, and optional start/stop must be verified against Grundfos GO.

## When ready (checklist)

1. Install pump; pair with Grundfos GO on a phone.
2. `python3 device/grundfos-scala1/scripts/ble_probe.py --scan` → set `SCALA1_BLE_ADDRESS`.
3. `ble_probe.py --dump` → document UUIDs in `BLE_PROTOCOL.md` and `.env` / `metrics_map.yaml`.
4. `sudo ./install_grundfos_service.sh` — verify `mosquitto_sub -t 'water/grundfos/scala1/status'`.
5. Import Node-RED `412`, `413`; re-import `50` and `90` (Replace existing nodes).
6. Update this doc and [device/grundfos-scala1/README.md](../device/grundfos-scala1/README.md) status to **production**.

## Do not enable yet

- Do **not** run `install_grundfos_service.sh` on the live server until step 3 is done (service will fail without a valid BLE address and GATT map).
- Do **not** import flows `412`/`413` or re-import watchdog/Telegram until MQTT publishes valid snapshots.

See [RELEASE_NOTES_v3.12.0.md](releases/RELEASE_NOTES_v3.12.0.md) for what landed in the repo in this scaffolding pass.
