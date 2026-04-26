# Release Notes v3.11.4

**Release Date:** 2026-04-26  
**Type:** Patch (SMS gateway firmware — MQTT recovery after power or broker outages)

## Overview

The ESP32 SMS gateway firmware no longer gets stuck in a loop of **“MQTT broker unavailable”** emergency texts after the WiFi access point and MQTT broker return. The device **resumes MQTT without a full power cycle** by aligning its WiFi state with the ESP32 stack on every main-loop iteration and by **resetting the TCP client** before each MQTT connect attempt.

## Changes

### Firmware (`device/sms-gateway`)

| Area | Change |
|------|--------|
| **WiFi vs. MQTT gating** | `wifiConnected` is synced to `WiFi.status()` every loop (via `syncWifiLinkState()`), not only on the 60s periodic check. If the stack auto-reconnects after a brownout, MQTT reconnection runs immediately. |
| **MQTT connect** | Before `mqttClient.connect()`, the firmware calls `mqttClient.disconnect()` and `espClient.stop()` with a short delay so a **stale socket** from a long outage does not block reconnection until reboot. |
| **Emergency SMS** | The **“MQTT connection restored”** SMS is sent only when reconnecting after at least one failed connect attempt in that recovery (not on a clean first connect at boot). |

### Documentation

- **`device/sms-gateway/README.md`**: Self-recovery and emergency SMS behavior updated to match the firmware.
- **`docs/MQTT_PROTOCOL.md`**: New subsection under SMS Gateway: link recovery, TCP reset, and emergency SMS policy.
- **`docs/ARCHITECTURE.md`**: SMS Gateway section notes firmware link recovery.
- **`CHANGELOG.md`**: [3.11.4] entry.

## Upgrade (device)

1. Build and flash from `device/sms-gateway` (PlatformIO: `pio run -t upload`).
2. No Node-RED or server-side changes for this release.

## References

- Firmware: `device/sms-gateway/src/main.cpp` (`syncWifiLinkState`, `reconnectMQTT`).
