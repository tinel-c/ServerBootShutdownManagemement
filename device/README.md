# Device firmware

Embedded firmware in this repository:

| Directory | Device | Role |
|-----------|--------|------|
| `sms-gateway/` | ESP32 + SIM800 (LilyGo T-Call) | SMS/MQTT gateway for alerts and commands |
| `PlatformIO_ESP8266_Main_Entry/` | ESP8266 (esp12e, 4-relay board) | **Main gate** — keypad, MQTT (`MainGate/CMD/Relay3`, `MainGate/STAT/…`), local/offline behavior |

`PlatformIO_ESP8266_Main_Entry` is a **git submodule** ([upstream](https://github.com/tinel-c/PlatformIO_ESP8266_Main_Entry)). It matches the main gate automation in Node-RED (flows 210–212, SMS 514, etc.); see `docs/GATE_AUTOMATION.md` and `nodered/flows/README.md`.

**Clone with submodules:** `git clone --recurse-submodules <repo-url>`  
**If you already cloned:** `git submodule update --init --recursive`
