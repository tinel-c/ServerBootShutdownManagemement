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

## 3. Registry

Add the device to both fleet files with `flash: true` (the default for every new device that speaks this contract):

- `scripts/status/device_fleet.yaml`
- `client/config/device_fleet.yaml`

Set `flash: false` only when the firmware cannot accept ArduinoOTA yet.

Playbook: [docs/developer/DEVICE_FIRMWARE_DEVELOPMENT.md](../../../docs/developer/DEVICE_FIRMWARE_DEVELOPMENT.md).
