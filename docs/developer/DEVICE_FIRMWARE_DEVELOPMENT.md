# Device firmware development (canonical)

This is the **required** way to add or change an ESP / PlatformIO device in this monorepo. Copy [device/templates/platformio-esp32](../../device/templates/platformio-esp32/README.md). Working copies: [`device/PlatformIO_esp32-4ch-thyristor-board-illumination`](../../device/PlatformIO_esp32-4ch-thyristor-board-illumination/) (`fw` ≥ 0.2.7, dashboard flow 330) and [`device/PlatformIO_esp32-sms-gateway`](../../device/PlatformIO_esp32-sms-gateway/) (`fw` ≥ 1.1.5, voice call and 5-call alarm). Submodule policy: [DEVICE_SUBMODULES.md](DEVICE_SUBMODULES.md). OTA details: [OTA_DEVICE_UPDATES.md](OTA_DEVICE_UPDATES.md).

A new device is not done when the firmware compiles. It is done when the five defaults below are in git and a fresh board shows up in Device Fleet, on the SMS watchdog, and on a Node-RED page that sends the same commands the client buttons send.

## One identity

Use **one string** everywhere. It is the GitHub repo name, the submodule directory, the MQTT client id, the status JSON `device` field, the watchdog `name`, and the `id` in both fleet YAML files.

Example: `PlatformIO_esp32-4ch-thyristor-board-illumination`.

A short hostname (`esp32-4ch-thyristor`) is only for DHCP and ArduinoOTA. Do not use it as the fleet id.

## Default features

Every new ESP device implements all five. The Wi-Fi LED is also required when the board has one indicator LED.

| Feature | What “done” means |
|---------|-------------------|
| **MQTT** | Status JSON on a dedicated topic about every 30 s. Commands on one topic. Topics written in the device README and [MQTT_PROTOCOL.md](../MQTT_PROTOCOL.md). |
| **OTA** | `ArduinoOTA.begin()` after STA has an IP. Post-build hook flashes through the fleet. `flash: true` once that image is on the board. |
| **Watchdog** | `smsWatchdogRegister` on MQTT connect and on the status cadence. `name` is the fleet id, interval 60 s. |
| **Client** | Same row in both fleet YAML files. `commands_for` and `status_topics` in [`client/device_commands.py`](../../client/device_commands.py) cover every command and status topic. |
| **Node-RED** | A generated flow with a dashboard page. Buttons publish the same topic and payload as the client buttons. Deployed with `deploy-flow-NNN.mjs`. |

### MQTT

Broker is `192.168.2.4:1883`, anonymous. QoS 1. Do not retain status or commands. New firmware uses this layout (`<domain>/<slug>` is stable, lowercase, and is not the fleet id):

| Role | Topic | Payload |
|------|--------|---------|
| Status | `<domain>/<slug>/status` | JSON, about every 30 s |
| Command | `<domain>/<slug>/command/set` | One JSON object per action |
| OTA state | `<domain>/<slug>/ota/status` | `{"device","fw","state":"started\|completed\|error","detail"}` |
| OTA progress | `<domain>/<slug>/ota/progress` | `{"device","progress","total","percent"}` |

Status JSON must include `device`, `fw`, `ip`, and `ota_port`. Add `rssi`, `uptime_s`, and the live outputs the dashboard shows (the illumination board sends `channels`). [`device_fleet.py`](../../scripts/status/device_fleet.py) reads `device` only to know who spoke; it reads `fw`, `ip`, `rssi`, and `ota_port` from that payload. Any message on `status_topic` counts as online.

Reference: `illumination/4ch-thyristor/status` and `illumination/4ch-thyristor/command/set` with `{"channel":1,"state":"on"}`. Channel `0` and `"off"` is the all-off command.

Boards that already have topics keep them. The main gate still uses `MainGate/CMD/RelayN` plus `gate/main/status`. Tasmota stays on `cmnd/<topic>/POWER`. A new device does not add a second command path beside the one the dashboard uses.

On boot and on OTA start, put outputs in a safe state (illumination: every channel off; main gate: Relay 3 off).

### OTA

Copy [`scripts/ota_after_build.py`](../../device/templates/platformio-esp32/scripts/ota_after_build.py). Set `DEVICE_ID` to the fleet id. `platformio.ini` stays `upload_protocol = esptool` plus `extra_scripts = post:scripts/ota_after_build.py`. Never `espota` with `127.0.0.1`.

`ArduinoOTA.begin()` only after STA has a real IP. `ArduinoOTA.handle()` in `loop()` while connected. On Wi-Fi loss, `ArduinoOTA.end()`. Log `OTA listening on x.x.x.x:3232` (ESP8266 default port is **8266**). Idle OTA is UDP; a closed TCP probe of that port is normal.

First image is UART: `SKIP_FLEET_OTA=1 pio run -e <env> -t upload --upload-port COMx`. After `device_fleet.py status` shows an IP, set `flash: true` and day-to-day updates are `pio run` (build only). The hook calls [`fleet_ota_hook.py`](../../scripts/status/fleet_ota_hook.py), which runs `device_fleet.py flash`. Offline, missing IP, or `flash: false` is a soft success so a UART upload can continue. A failed `espota` to a live board fails the post-step.

On Windows, local `espota` often fails the TCP callback. The fleet retries over SSH to `192.168.2.4` (`FLEET_OTA_VIA=auto`). Key: `%USERPROFILE%\.ssh\serverside_192_168_2_4_ed25519`.

### Watchdog

Copy [`include/sms_watchdog_client.h`](../../device/templates/platformio-esp32/include/sms_watchdog_client.h). Call `smsWatchdogRegister(mqtt, fleetId)` immediately after MQTT connect and again on the ~30 s status cadence. Skip the call while OTA is active.

`name` is the fleet id. Default interval is **60** s. The gateway marks the device offline after **2 × interval** without a heartbeat, and from gateway `fw` 1.1.4 it texts only after **10 minutes** offline, at most once per **30 minutes**. The list is RAM-only (max 10). The same name and interval does not send an “updated” SMS, so repeating enroll is how a device comes back after the gateway reboots. Topics: `sms/gateway/watchdog/*` in [MQTT_PROTOCOL.md](../MQTT_PROTOCOL.md).

### Client reporting

The tray reads the catalog from GitHub `main` ([`scripts/status/device_fleet.yaml`](../../scripts/status/device_fleet.yaml)). [`client/config/device_fleet.yaml`](../../client/config/device_fleet.yaml) is the offline copy the updater installs. Put the same entry in both:

```yaml
  - id: PlatformIO_esp32-example
    path: device/PlatformIO_esp32-example
    status_topic: example/board/status
    timeout_sec: 90
    flash: true
    pio_env: esp32dev
    ota_port: 3232
```

`timeout_sec` is how long a silent status topic stays “online” (use 90 unless the device publishes slower). `expected: false` hides it from the “should be online” count. Leave `flash: false` only until the running image binds ArduinoOTA and publishes `ip`.

Command buttons and the live status pane come from [`client/device_commands.py`](../../client/device_commands.py), which is inside the installed client, not from GitHub:

- `commands_for` returns `(label, topic, payload)` for **every** command the device accepts. Those topics and payloads must match the firmware and the Node-RED buttons.
- `status_topics` lists every status subscription the detail pane should show, including the fleet status topic.
- Add a case in [`client/tests/test_device_commands.py`](../../client/tests/test_device_commands.py).

Pushing the YAML makes the row appear in Device Fleet. The buttons appear after the next client release, because `device_commands.py` is copied by `update_client_files.bat` from `client-vX.Y.Z.zip`.

### Node-RED

The editor on `192.168.2.4:1880` is not the source of truth. Generate the flow, commit the JSON, then deploy.

Copy the illumination pair:

- [`nodered/live-connection/scripts/generate-flow-330.mjs`](../../nodered/live-connection/scripts/generate-flow-330.mjs) writes [`nodered/flows/330-4ch-thyristor-illumination.json`](../../nodered/flows/330-4ch-thyristor-illumination.json)
- [`nodered/live-connection/scripts/deploy-flow-330.mjs`](../../nodered/live-connection/scripts/deploy-flow-330.mjs) replaces that tab on the live editor

For a new device, add `generate-flow-NNN.mjs` and `deploy-flow-NNN.mjs`. Pick a free number in the domain range (200 gates, 300 lights, 400 irrigation, 800 energy). The dashboard path is `/dashboard/<slug>`. The deploy script must require `mqtt_broker_local` from `00-base-config.json` and must refuse the path if another page already uses it.

The page shows firmware, IP, online/age, and the outputs from the status JSON. Each button publishes the same MQTT command as `commands_for`. Run:

```bash
node nodered/live-connection/scripts/generate-flow-NNN.mjs
node nodered/live-connection/scripts/deploy-flow-NNN.mjs
```

`deploy-flow-NNN.mjs` uses `NODE_RED_BASE_URL` (default `http://192.168.2.4:1880`). Then add a row to [nodered/flows/README.md](../../nodered/flows/README.md) and the topic table to [MQTT_PROTOCOL.md](../MQTT_PROTOCOL.md).

### Wi-Fi LED

Required when the board has one indicator LED. Copy [`include/wifi_status_led.h`](../../device/templates/platformio-esp32/include/wifi_status_led.h). `board_pins.h` defines `PIN_STATUS_LED`, `LED_ACTIVE_LEVEL`, and `LED_IDLE_LEVEL` (`PIN_STATUS_LED` `-1` when there is no such LED). Call `updateWifiStatusLed(lastWifiBeginMs)` from `loop()`. The LED shows Wi-Fi only.

| Pattern | Meaning |
|---------|---------|
| Lit, 80 ms dark wink every 2 s | Associated |
| 100 ms blink for 3 s after `WiFi.begin` | Joining |
| 500 ms blink | Not associated, waiting to retry |
| Two short flashes every 1.2 s | No SSID, connect failed, or link lost |

Confirm polarity on the hardware. Reference: thyristor IO5, lit when the pin is low, `fw` ≥ 0.2.7.

## Files a new device touches

| File | Why |
|------|-----|
| `device/<fleet-id>/` | Firmware repo, then a submodule pin |
| Device `README.md` | Build, flash, topic table, LED polarity |
| [device/README.md](../../device/README.md) | One row in the device table |
| [scripts/status/device_fleet.yaml](../../scripts/status/device_fleet.yaml) | Catalog the tray loads from GitHub |
| [client/config/device_fleet.yaml](../../client/config/device_fleet.yaml) | Same row, offline fallback |
| [client/device_commands.py](../../client/device_commands.py) | Status subscriptions and one button per command |
| [client/tests/test_device_commands.py](../../client/tests/test_device_commands.py) | Locks those topics and payloads |
| `nodered/live-connection/scripts/generate-flow-NNN.mjs` | Writes the dashboard flow |
| `nodered/live-connection/scripts/deploy-flow-NNN.mjs` | Pushes that tab to Node-RED |
| `nodered/flows/NNN-<slug>.json` | Committed flow |
| [nodered/flows/README.md](../../nodered/flows/README.md) | Page path and deploy command |
| [docs/MQTT_PROTOCOL.md](../MQTT_PROTOCOL.md) | Topic table |

## Order of work

1. Create the device repo from the template. Secrets only in gitignored headers (`secrets.h.example` / `passwords.h.example` committed).
2. Implement MQTT, OTA, watchdog, and the Wi-Fi LED. Bump `fw` on every flashable change.
3. UART-flash the first image. Confirm serial logs `OTA listening on …`.
4. Register both YAML files. Set `flash: true` once status shows an IP.
5. Add `commands_for`, `status_topics`, and a test.
6. Generate the Node-RED flow, document it, deploy it.
7. Commit and push the **device repo first**, then pin the gitlink and push the monorepo.
8. Verify: `python scripts/status/device_fleet.py status` shows online, IP, and `fw`. `sms/gateway/watchdog/status` lists the device `online: true`. Dashboard buttons and Device Fleet buttons publish the same payload. Associated LED winks off once every 2 s.

## Layout

| Piece | Where |
|-------|--------|
| Firmware source | Own GitHub repo, pinned as `device/<repo-name>/` submodule |
| Secrets | `include/secrets.h` (gitignored); ship `secrets.h.example` only |
| MQTT topics | Device `README.md` + [MQTT_PROTOCOL.md](../MQTT_PROTOCOL.md) |
| Fleet registry | [scripts/status/device_fleet.yaml](../../scripts/status/device_fleet.yaml) and [client/config/device_fleet.yaml](../../client/config/device_fleet.yaml) |
| Client commands | [client/device_commands.py](../../client/device_commands.py) |
| Dashboard | `nodered/flows/NNN-*.json`, generated and deployed from `nodered/live-connection/scripts/` |
| Fleet tool | [scripts/status/device_fleet.py](../../scripts/status/device_fleet.py) |
| Post-build OTA | Device `scripts/ota_after_build.py` → monorepo [`scripts/status/fleet_ota_hook.py`](../../scripts/status/fleet_ota_hook.py) → `device_fleet.py flash` |

Prefer `PlatformIO_*` repo names for PlatformIO boards. Register every new device in [device/README.md](../../device/README.md).

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

1. One fleet id across the repo name, MQTT client id, status `device`, watchdog `name`, and both YAML `id`s.
2. Submodule under `device/<fleet-id>`; secrets only via example templates.
3. MQTT status (`device`, `fw`, `ip`, `ota_port`) and one command topic. Document both in the device README and [MQTT_PROTOCOL.md](../MQTT_PROTOCOL.md).
4. `platformio.ini`: `upload_protocol = esptool`; `scripts/ota_after_build.py` calls the fleet hook. `ArduinoOTA.begin()` only after STA has an IP. Bump `fw`. Safe outputs on boot and OTA start.
5. Both fleet YAML files, `flash: true` once the board publishes `ip`.
6. SMS watchdog: `smsWatchdogRegister` on MQTT connect and on the status cadence (`name` = fleet id, interval 60 s).
7. Wi-Fi LED: `updateWifiStatusLed` from `loop()` when the board has one indicator LED. Same four patterns as `wifi_status_led.h`. Do not drive that LED from load state. Record polarity.
8. Client: `commands_for` and `status_topics` for every command and status topic, plus a test in `client/tests/test_device_commands.py`.
9. Node-RED: `generate-flow-NNN.mjs`, committed `nodered/flows/NNN-*.json`, `deploy-flow-NNN.mjs`, and a row in `nodered/flows/README.md`. Buttons use the same payloads as `commands_for`.
10. Commit **device repo first**, push, then pin the gitlink and the monorepo docs. Push the monorepo before expecting the tray to list the device.
11. Verify: `device_fleet.py status` shows online, IP, and `fw`. Watchdog status lists `online: true`. Dashboard and Device Fleet buttons move the same output. Associated LED winks off once every 2 s.

## Windows client (status, commands, manual OTA)

The tray app under [`client/`](../../client/) opens **Device Fleet…** in its own process ([`device_fleet_panel.py`](../../client/device_fleet_panel.py)). The list is fetched from GitHub (`scripts/status/device_fleet.yaml` and [`device/tasmota/catalog.yaml`](../../device/tasmota/catalog.yaml)). [`client/config/device_fleet.yaml`](../../client/config/device_fleet.yaml) is only the offline fallback.

The window shows expected vs online counts, firmware, and IP. Selecting a row shows that device’s status and one button per command from [`device_commands.py`](../../client/device_commands.py). **Upload firmware…** sends a `.bin` through [`device_fleet.py`](../../scripts/status/device_fleet.py). **Scan Tasmota** merges boards on the LAN into that catalog. Details: [README_CLIENT.md](../../client/README_CLIENT.md).

## Do not

- Commit `secrets.h` / passwords / `.env` with credentials.
- Use PlatformIO Upload for OTA or leave `espota` + `127.0.0.1` as upload defaults.
- Blame the device for OTA failure before checking brownout, missing `ip`, closed OTA bind, and Windows firewall / broker fallback.
- Deploy firmware trees with `scp` as the normal path — git submodule pin + documented flash/OTA only.
