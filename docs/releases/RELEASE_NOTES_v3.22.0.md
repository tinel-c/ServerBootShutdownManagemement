# Release Notes — v3.22.0

**Date:** 2026-11-22  
**Author:** Constantin Bogza

## Summary

The 4-channel thyristor board has a Node-RED page and a confirmed GPIO map. Its blue LED shows Wi-Fi with a blink pattern that is now the standard for every new ESP device.

## Changes

### Illumination dashboard

- Flow **330** at `/dashboard/illumination` ([nodered/flows/330-4ch-thyristor-illumination.json](../../nodered/flows/330-4ch-thyristor-illumination.json)).
- Status `illumination/4ch-thyristor/status`. Commands `illumination/4ch-thyristor/command/set`. Channel 0 off turns every output off.
- Deploy: `node nodered/live-connection/scripts/deploy-flow-330.mjs`.

### Thyristor firmware 0.2.7

- Live at `192.168.2.49`. Gates are active-high: RY1=IO32, RY2=IO25, RY3=IO27, RY4=IO12.
- Boot and OTA force every channel off. Commands are not retained.
- Blue LED IO5 is active-low and shows Wi-Fi only.

### Wi-Fi LED protocol

Copy [device/templates/platformio-esp32/include/wifi_status_led.h](../../device/templates/platformio-esp32/include/wifi_status_led.h) into each new device that has one indicator LED. Call `updateWifiStatusLed` from `loop()`.

| Pattern | Meaning |
|---------|---------|
| Lit, 80 ms dark wink every 2 s | Associated |
| 100 ms blink for 3 s after `WiFi.begin` | Joining |
| 500 ms blink | Not associated, waiting to retry |
| Two short flashes every 1.2 s | No SSID, connect failed, or link lost |

Confirm `LED_ACTIVE_LEVEL` on the board. Do not use this LED for load state. Rule: [.cursor/rules/wifi-status-led.mdc](../../.cursor/rules/wifi-status-led.mdc). Playbook: [DEVICE_FIRMWARE_DEVELOPMENT.md](../developer/DEVICE_FIRMWARE_DEVELOPMENT.md).

## Deploy

The dashboard and firmware 0.2.7 are already on the automation server and the board. To refresh a checkout:

```bash
cd ~/ServerBootShutdownManagemement && git fetch && git checkout main && git pull
git submodule update --init device/PlatformIO_esp32-4ch-thyristor-board-illumination
```
