# PlatformIO ESP fleet defaults

Copy these pieces into every new ESP / PlatformIO device repository. The illumination board (`fw` ≥ 0.2.2) and the SMS gateway (`fw` ≥ 1.1.0) are the working copies of this contract.

## 1. Post-build OTA

1. Copy [scripts/ota_after_build.py](scripts/ota_after_build.py) to the device repo as `scripts/ota_after_build.py`.
2. Set `DEVICE_ID` to the fleet id (repository name, MQTT client id, and status `device` field — one string).
3. In `platformio.ini`:

```ini
upload_protocol = esptool
extra_scripts =
    post:scripts/ota_after_build.py
```

Do not set `upload_protocol = espota` and do not pin a placeholder IP. First flash is UART (`SKIP_FLEET_OTA=1 pio run -e <env> -t upload --upload-port COMx`). Later updates are `pio run` (build). The hook calls `scripts/status/fleet_ota_hook.py`, which runs `device_fleet.py flash`.

## 2. Firmware

Status JSON on the topic listed in `scripts/status/device_fleet.yaml`, about every 30 s, not retained:

- `device` — fleet id
- `fw` — semver; bump on every flashable change
- `ip` — STA address
- `ota_port` — ESP32 default **3232** (ESP8266 ArduinoOTA default is 8266)

`ArduinoOTA.begin()` only after STA has an IP. `ArduinoOTA.handle()` in `loop()` while connected. Log `OTA listening on x.x.x.x:3232`. On Wi-Fi loss, `ArduinoOTA.end()`.

## 2b. SMS gateway watchdog (required for new ESP devices)

Copy [include/sms_watchdog_client.h](include/sms_watchdog_client.h) into the device repo as `include/sms_watchdog_client.h`. Call `smsWatchdogRegister(mqtt, fleetId)`:

1. Immediately after a successful MQTT connect (subscribe first if needed).
2. On the same ~30 s status publish cadence (skip while OTA is active).

`name` is the fleet id (same string as MQTT client id / status `device`). Default `interval` is **60** s (gateway alerts after **2 × interval** of silence once the device has heartbeated once). The gateway watch list is RAM-only (max 10 slots); repeating enroll recovers monitoring after an SMS gateway reboot. Same name + same interval does not send an “updated” SMS (`fw` ≥ 1.1.3).

Working copy: illumination board `fw` ≥ 0.2.3.

## 2c. Wi-Fi status LED (required when the board has one indicator LED)

Copy [include/wifi_status_led.h](include/wifi_status_led.h). Include `board_pins.h` first. It must define `PIN_STATUS_LED`, `LED_ACTIVE_LEVEL`, and `LED_IDLE_LEVEL`. Use `PIN_STATUS_LED` `-1` when the board has no such LED.

Call `updateWifiStatusLed(lastWifiBeginMs)` from `loop()`. Pass `millis()` of the latest `WiFi.begin()`, or `0` before the first attempt. "Lit" is `LED_ACTIVE_LEVEL`. Confirm polarity on the board before shipping. The thyristor blue LED on IO5 is lit when the pin is low (`fw` ≥ 0.2.7).

| Pattern | Meaning |
|---------|---------|
| Lit, 80 ms dark wink every 2 s | Associated |
| 100 ms lit / 100 ms dark for 3 s after `WiFi.begin` | Joining |
| 500 ms lit / 500 ms dark | Not associated, waiting to retry |
| Two 80 ms flashes, then dark, every 1.2 s | No SSID, connect failed, or link lost |

The LED shows Wi-Fi only. Do not tie it to load or channel state.

## 3. Registry, client, and Node-RED

Add the same device entry to both fleet files with `flash: true` (the default once this contract is on the board):

- `scripts/status/device_fleet.yaml` — the catalog the Windows tray loads from GitHub
- `client/config/device_fleet.yaml` — the offline copy

Set `flash: false` only when the firmware cannot accept ArduinoOTA yet.

Then wire the rest of the contract, in [docs/developer/DEVICE_FIRMWARE_DEVELOPMENT.md](../../../docs/developer/DEVICE_FIRMWARE_DEVELOPMENT.md):

- `client/device_commands.py` — `commands_for` and `status_topics` for every command and status topic, plus a test
- A Node-RED page generated like flow 330 (`generate-flow-NNN.mjs`, committed JSON, `deploy-flow-NNN.mjs`) whose buttons publish those same payloads
- Topic table in `docs/MQTT_PROTOCOL.md`, `nodered/flows/README.md`, and `device/README.md`

The fleet id is one string: repo name, MQTT client id, status `device`, watchdog `name`, and YAML `id`.
