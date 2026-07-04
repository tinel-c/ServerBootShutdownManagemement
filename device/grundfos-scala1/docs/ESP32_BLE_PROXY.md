# ESP32 BLE-to-MQTT proxy (optional)

Use this when the Ubuntu automation server **cannot** maintain reliable BLE range to the SCALA1 pump (typical if the pump is in a basement, pump house, or >10 m away).

## Architecture

```text
SCALA1 (BLE)  ←→  ESP32 (WiFi)  →  Mosquitto  →  Node-RED / Telegram / watchdog
```

The ESP32 runs near the pump, connects over BLE using the same GATT UUIDs documented in [BLE_PROTOCOL.md](BLE_PROTOCOL.md), and publishes **identical MQTT topics** as `scala1_mqtt_publisher.py`:

| Topic | Payload |
|-------|---------|
| `water/grundfos/scala1/status` | JSON snapshot (same schema as Python publisher) |
| `water/grundfos/scala1/running` | scalar |
| `water/grundfos/scala1/pressure_bar` | scalar |
| `water/grundfos/scala1/command` | subscribe — `{ "action": "start" \| "stop" \| "reset_alarm" }` |

When the proxy is deployed, **do not** run `grundfos-scala1-mqtt-publisher.service` on the server (disable it to avoid duplicate BLE clients).

## Recommended hardware

- ESP32-WROOM-32 or ESP32-C3 module with external antenna (better range through walls)
- USB power near the pump
- WiFi credentials for the same LAN as Mosquitto (`192.168.2.4`)

## Firmware outline

1. WiFi + MQTT client (Arduino/ESP-IDF or ESPHome custom component).
2. BLE client (`NimBLE-Arduino` or ESP-IDF Bluedroid) — connect to `SCALA1_BLE_ADDRESS`.
3. Poll telemetry characteristic every 15 s; publish JSON to `water/grundfos/scala1/status`.
4. Subscribe to `water/grundfos/scala1/command`; forward writes to control characteristic when configured.
5. LWT on `water/grundfos/scala1/status` or a dedicated `.../bridge/status` topic for proxy health.

## Configuration (proposed)

Store in device NVS or `config.h`:

```cpp
#define WIFI_SSID "..."
#define WIFI_PASS "..."
#define MQTT_HOST "192.168.2.4"
#define MQTT_PORT 1883
#define SCALA1_BLE_ADDRESS "AA:BB:CC:DD:EE:FF"
#define TELEMETRY_CHAR_UUID "..."
#define CONTROL_CHAR_UUID "..."
```

## Range test (Phase 1 decision)

On the automation server:

```bash
sudo hciconfig hci0 up
python3 device/grundfos-scala1/scripts/ble_probe.py --scan
```

If the pump does not appear consistently, plan for ESP32 proxy instead of host BLE.

## Future work

A dedicated firmware repo under `device/grundfos-scala1-esp32/` (PlatformIO) can be added as a git submodule when UUIDs are confirmed and range testing fails on the host.
