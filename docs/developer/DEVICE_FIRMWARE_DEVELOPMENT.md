# Device firmware development (canonical)

This is the **required** way to build and iterate ESP / PlatformIO firmware in this monorepo. Working copies: [`device/PlatformIO_esp32-4ch-thyristor-board-illumination`](../../device/PlatformIO_esp32-4ch-thyristor-board-illumination/) (`fw` ≥ 0.2.7) and [`device/PlatformIO_esp32-sms-gateway`](../../device/PlatformIO_esp32-sms-gateway/) (`fw` ≥ 1.1.4). New devices start from [device/templates/platformio-esp32](../../device/templates/platformio-esp32/README.md). Submodule policy: [DEVICE_SUBMODULES.md](DEVICE_SUBMODULES.md). OTA details: [OTA_DEVICE_UPDATES.md](OTA_DEVICE_UPDATES.md).

## Layout

| Piece | Where |
|-------|--------|
| Firmware source | Own GitHub repo, pinned as `device/<repo-name>/` submodule |
| Secrets | `include/secrets.h` (gitignored); ship `secrets.h.example` only |
| MQTT topics | Document in device `README.md` + [MQTT_PROTOCOL.md](../MQTT_PROTOCOL.md) |
| Fleet registry | [scripts/status/device_fleet.yaml](../../scripts/status/device_fleet.yaml) |
| Fleet tool | [scripts/status/device_fleet.py](../../scripts/status/device_fleet.py) |
| Post-build OTA | Device `scripts/ota_after_build.py` → monorepo [`scripts/status/fleet_ota_hook.py`](../../scripts/status/fleet_ota_hook.py) → `device_fleet.py flash` |

Prefer `PlatformIO_*` repo names for PlatformIO boards. Register every new device in [device/README.md](../../device/README.md).

## MQTT contract (device → fleet)

Status JSON (not retained unless there is a strong reason) must include at least:

- `device` — stable id (same as fleet `id` / MQTT client id)
- `fw` — semver string; bump on every flashable change
- `ip` — STA address after connect
- `ota_port` — ArduinoOTA port (ESP32 default **3232**)

Publish on a dedicated status topic listed in `device_fleet.yaml`. Commands and OTA event topics are optional but recommended (`…/command/…`, `…/ota/status`, `…/ota/progress`). OTA event payloads match the illumination board: `ota/status` is `{"device","fw","state":"started|completed|error","detail"}` and `ota/progress` is `{"device","progress","total","percent"}`.

**SMS gateway watchdog (required for every new ESP device):** copy [`device/templates/platformio-esp32/include/sms_watchdog_client.h`](../../device/templates/platformio-esp32/include/sms_watchdog_client.h) into the device repo and call `smsWatchdogRegister(mqtt, fleetId)` on MQTT connect and on the ~30 s status cadence (skip during OTA). Payload `name` is the fleet id; default interval **60** s. The SMS gateway keeps the list in RAM (max 10); re-enroll recovers after a gateway reboot. See [MQTT_PROTOCOL.md](../MQTT_PROTOCOL.md) (`sms/gateway/watchdog/*`).

**Wi-Fi status LED (required when the board has one indicator LED):** copy [`device/templates/platformio-esp32/include/wifi_status_led.h`](../../device/templates/platformio-esp32/include/wifi_status_led.h). `board_pins.h` defines `PIN_STATUS_LED`, `LED_ACTIVE_LEVEL`, and `LED_IDLE_LEVEL` (`PIN_STATUS_LED` `-1` if there is no LED). Call `updateWifiStatusLed(lastWifiBeginMs)` from `loop()`. The LED shows Wi-Fi only:

| Pattern | Meaning |
|---------|---------|
| Lit, 80 ms dark wink every 2 s | Associated |
| 100 ms blink for 3 s after `WiFi.begin` | Joining |
| 500 ms blink | Not associated, waiting to retry |
| Two short flashes every 1.2 s | No SSID, connect failed, or link lost |

Confirm polarity on the hardware. Reference: thyristor IO5, lit when the pin is low, `fw` ≥ 0.2.7. Dashboard: `/dashboard/illumination`.

**Default for every new device:** `flash: true`, status interval about 30 s, `upload_protocol = esptool`, the template post script, SMS watchdog self-registration, and the Wi-Fi LED protocol when the board has one indicator LED. Set `flash: false` only until the running image binds ArduinoOTA and publishes `ip`. The ESP8266 main gate source does that from `fw` 1.0.0; `flash` stays false until that image is UART-flashed once.

## Flash paths (do not mix)

| Goal | How |
|------|-----|
| First bring-up / recovery | UART **esptool** only — `upload_protocol = esptool` in `platformio.ini` |
| Day-to-day updates | **`pio run`** (build) → post-action OTA via fleet — **not** PlatformIO Upload |
| Skip post-build OTA | `SKIP_FLEET_OTA=1` (e.g. UART-flashing an OTA fix while the board still has a fleet IP) |

**Never** set `upload_protocol = espota` with a placeholder IP (`127.0.0.1`). That breaks IDE Upload after a soft OTA skip.

```bash
# UART (Serial Burn: GND, RX, TX, BOOT/Reset; hold BOOT, tap Reset)
SKIP_FLEET_OTA=1 pio run -e esp32dev -t upload --upload-port COMx

# Build + automatic OTA when MQTT sighting is fresh
pio run -e esp32dev

# Manual fleet flash
python scripts/status/device_fleet.py status
python scripts/status/device_fleet.py flash \
  --id <device-id> \
  --bin device/<name>/.pio/build/<env>/firmware.bin
```

On Windows, local `espota` often fails after the UDP invite (`No response from device`) because the firewall blocks the ESP TCP callback. `device_fleet.py` retries over SSH on **`192.168.2.4`** (`FLEET_OTA_VIA=auto|broker|local`). Key: `%USERPROFILE%\.ssh\serverside_192_168_2_4_ed25519`.

## ArduinoOTA rules

1. Configure callbacks early; call **`ArduinoOTA.begin()` only after STA has a real IP**. Binding in `setup()` right after a non-blocking `WiFi.begin()` leaves port 3232 silent.
2. Call `ArduinoOTA.handle()` in `loop()` while connected.
3. Serial should log something like `OTA listening on x.x.x.x:3232`.
4. Idle OTA is **UDP**; a TCP probe to 3232 may show closed — that is normal.
5. On OTA start: put outputs in a safe state (thyristor: all channels off). Same on boot.

## Power and bring-up

- Prefer the board’s intended supply for Wi-Fi soak tests (thyristor: **230 V L/N**). USB-UART 5 V alone often brownouts on TX → no MQTT → no OTA.
- If mains already powers the board, UART flash with GND/RX/TX (+ BOOT) only — do not back-feed adapter 5 V.
- Confirm GPIOs in hardware docs and a `BOARD_PINS_CONFIRMED` (or equivalent) gate before driving loads.

## Agent checklist (new or changed firmware)

1. Submodule under `device/<name>`; secrets only via example templates.
2. `platformio.ini`: `upload_protocol = esptool`; post-script calls fleet flash when appropriate.
3. Status MQTT includes `device`, `fw`, `ip`, `ota_port`; entry in both fleet YAML files with `flash: true` unless ArduinoOTA is impossible.
4. SMS watchdog client: `smsWatchdogRegister` on MQTT connect and status cadence (`name` = fleet id).
5. Wi-Fi LED: `updateWifiStatusLed` from `loop()` when the board has one indicator LED. Same four patterns as `wifi_status_led.h`. Do not drive that LED from load state.
6. OTA begins after Wi-Fi IP; version bumped; safe defaults on boot/OTA.
7. Docs: device README + HARDWARE (if any), MQTT_PROTOCOL, OTA guide if behavior changes. Record LED polarity.
8. Commit **device repo first**, push, then pin gitlink + monorepo docs/scripts; push monorepo.
9. Verify: `device_fleet.py status` → online with IP → `flash` (or `pio run`) → status `fw` matches; `sms/gateway/watchdog/status` lists the device `online: true`. Associated LED winks off once every 2 s.

## Windows client (status + manual OTA)

The tray app under [`client/`](../../client/) exposes **Device Fleet…** ([`device_fleet_panel.py`](../../client/device_fleet_panel.py)): expected vs online counts, firmware/`ip`, and per-device `.bin` upload through [`device_fleet.py`](../../scripts/status/device_fleet.py). The list is fetched from GitHub (`scripts/status/device_fleet.yaml` and [`device/tasmota/catalog.yaml`](../../device/tasmota/catalog.yaml)). [`client/config/device_fleet.yaml`](../../client/config/device_fleet.yaml) is only the offline fallback. **Scan Tasmota** merges boards on the LAN into that catalog. Details: [README_CLIENT.md](../../client/README_CLIENT.md).

## Do not

- Commit `secrets.h` / passwords / `.env` with credentials.
- Use PlatformIO Upload for OTA or leave `espota` + `127.0.0.1` as upload defaults.
- Blame the device for OTA failure before checking brownout, missing `ip`, closed OTA bind, and Windows firewall / broker fallback.
- Deploy firmware trees with `scp` as the normal path — git submodule pin + documented flash/OTA only.
