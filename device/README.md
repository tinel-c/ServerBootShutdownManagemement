# Device firmware

Device projects live in **separate Git repositories** and are included here as **git submodules** so each firmware can have its own history, issues, and releases. Adding/pinning submodules: [DEVICE_SUBMODULES.md](../docs/developer/DEVICE_SUBMODULES.md). **Develop / UART / fleet OTA** (required pattern for agents): [DEVICE_FIRMWARE_DEVELOPMENT.md](../docs/developer/DEVICE_FIRMWARE_DEVELOPMENT.md).

| Path (this repo) | Upstream | Device |
|------------------|----------|--------|
| `device/PlatformIO_esp32-sms-gateway/` | [tinel-c/PlatformIO_esp32-sms-gateway](https://github.com/tinel-c/PlatformIO_esp32-sms-gateway) | ESP32 + SIM800 (LilyGo T-Call) — SMS/MQTT gateway; fleet OTA after `pio run` (`fw` ≥ 1.1.3, same-interval watchdog re-enroll is silent) |
| `device/PlatformIO_ESP8266_Main_Entry/` | [tinel-c/PlatformIO_ESP8266_Main_Entry](https://github.com/tinel-c/PlatformIO_ESP8266_Main_Entry) | ESP8266 — main gate (Node-RED 210–212, 514) |
| `device/PlatformIO_esp32-4ch-thyristor-board-illumination/` | [tinel-c/PlatformIO_esp32-4ch-thyristor-board-illumination](https://github.com/tinel-c/PlatformIO_esp32-4ch-thyristor-board-illumination) | ESP32-WROOM-32E + 4× BT137S (RY1–4: IO32/25/27/12, LED IO5) — 230 V illumination; fleet OTA after `pio run` ([README](PlatformIO_esp32-4ch-thyristor-board-illumination/README.md), [device_fleet.py](../scripts/status/device_fleet.py)) |
| `device/victron-multiplus-ii/` | *(in-repo docs)* | Victron MultiPlus-II — GX/Modbus/MQTT integration ([README](victron-multiplus-ii/README.md)) |
| `device/huawei-inverter/` | *(in-repo docs)* | Huawei SUN2000 — Modbus/MQTT integration ([README](huawei-inverter/README.md)) |
| `device/energy-consumers/` | Tuya + Tasmota smart meters → `energy/consumers/*`, flow **840** ([README](energy-consumers/README.md), [agent playbook](../docs/ENERGY_CONSUMER_ADD.md)) |
| `device/grundfos-scala1/` | *(in-repo docs)* | Grundfos SCALA1 — **planned** BLE/MQTT scaffolding ([README](grundfos-scala1/README.md), [GRUNDGOS_SCALA1.md](../docs/GRUNDGOS_SCALA1.md)) |

**Clone with all device firmware:**  
`git clone --recurse-submodules <this-repo-url>`

**Already cloned without submodules:**  
`git submodule update --init --recursive`

**Refresh pinned revisions** after you pull in a submodule: from the monorepo root, `git add device/<name>` and commit the updated gitlink.

If you see an old inline path `device/sms-gateway/` on disk from before the submodule move, **close any editor using that folder**, delete `device/sms-gateway`, and run `git submodule update --init` so only `device/PlatformIO_esp32-sms-gateway` remains.
