# Release Notes v3.11.3

**Release Date:** 2026-04-14  
**Type:** Patch (Node-RED main gate MQTT alignment)

## Overview

Main gate **dashboard, Telegram, and SMS** paths now use **Relay 3** on topics **`MainGate/CMD/Relay3`**, **`MainGate/STAT/Relay3`**, and recurrent **`MainGate/STAT/reccurentStatusRelay3`**, matching the deployed **[PlatformIO_ESP8266_Main_Entry](https://github.com/tinel-c/PlatformIO_ESP8266_Main_Entry)** firmware (ESP8266 main gate controller).

## Changes

### Node-RED

| File | Change |
|------|--------|
| `210-main-gate-controls.json` | MQTT in/out and logging for Relay 3; flow comment links firmware repo |
| `211-main-gate-status.json` | Relay 3 labeled “main gate”; status comment references firmware |
| `212-gate-telegram.json` | Open command, context updates from `reccurentStatusRelay3`, user-facing copy |
| `514-sms-gateway-interface.json` | `GATE_OPEN` / `GATE` → `MainGate/CMD/Relay3` |
| `50-telegram-interface.json` | `/commands` text: Relay 3 for main gate pulse |
| `nodered/flows/README.md` | Gate automation (200–212) subsection + MQTT summary |

### Documentation

- **`docs/GATE_AUTOMATION.md`**, **`docs/GATE_IMPORT_INSTRUCTIONS.md`**, **`docs/TELEGRAM_INTERFACE.md`**: topics, tests, and device reference.
- **`docs/TASMOTA_GATE_INTEGRATION.md`**: current PlatformIO device and topics; Tasmota kept as alternate/legacy.

## Upgrade

1. On the Node-RED host, ensure **`node-red-contrib-telegrambot`** is installed if you use flows **50** / **212** (Palette → Install, or `npm install node-red-contrib-telegrambot` in Node-RED `userDir`).
2. Re-import updated JSON flows (210, 211, 212, 50, 514 as needed) and **Deploy**.

## References

- Device firmware and MQTT reference: [tinel-c/PlatformIO_ESP8266_Main_Entry](https://github.com/tinel-c/PlatformIO_ESP8266_Main_Entry)
