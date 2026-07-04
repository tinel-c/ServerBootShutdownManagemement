# Release Notes v3.8.0

**Release Date:** 2026-01-28  
**Type:** Minor Release (New Major Feature)

## Overview

This release introduces the **SMS Gateway Device Watchdog System**, a robust hardware-based monitoring solution that enhances the platform's reliability by providing independent device tracking and out-of-band SMS alerting via GSM.

## Key Features

### 🛡️ Hardware Device Watchdog
The SMS Gateway can now monitor other network devices independently of the main automation server:
- **Active MQTT Heartbeats**: Devices check-in via MQTT topics.
- **Smart Connection Monitoring**: Automatically detects "Connection Lost" after a device misses pulses for twice its configured interval.
- **Emergency SMS Alerts**: In the event of a device failure, the SMS Gateway sends a direct SMS notification to the pre-configured emergency contact.
- **Independent Reliability**: Because it uses its own GSM modem, alerts are sent even if the primary internet connection fails.

### 📊 Watchdog Management Dashboard
A new Node-RED module provide complete control over the watchdog system:
- **Live Device Monitoring**: Real-time status list showing online/offline states and heartbeat age.
- **Dynamic Device Management**: Easily enroll, update intervals, or delete monitored devices directly from the UI.
- **Manual Heartbeat Pulse**: Send immediate heartbeats with a simple click (💓) to verify connection logic.
- **Test Simulator**: Integrated "Auto-Pulse" and "Test Device" controls for stress testing the alert system.

### 🛠️ Technical Improvements
- **Instrumentation**: Added comprehensive Serial logging on the device to track every watchdog event.
- **Communication Protocol**: Migrated Node-RED dashboard components to Dashboard 2.0 (Vue.js) standards for improved performance and reliable message delivery.
- **Fail-safe Logic**: Enhanced enrollment handlers to prevent configuration loss during restarts.

## Files Changed

### Node-RED Flows
- `nodered/flows/513-sms-gateway-watchdog.json` - **NEW**: Watchdog dashboard and controls.
- `nodered/flows/00-base-config.json` - Added new UI group for watchdog management.

### Device Code
- `device/sms-gateway/src/main.cpp` - Watchdog logic, SMS alerting, and status reporting.
- `device/sms-gateway/include/config.h` - Added watchdog MQTT topics and configuration.

### Documentation
- `docs/ARCHITECTURE.md` - Added Section 5 detailing the Watchdog System architecture.
- `CHANGELOG.md` - Added v3.8.0 and v3.7.0 entries.

## Migration Guide

### 1. Update Device Firmware
Flash the latest C++ code to your SMS Gateway using PlatformIO. Ensure your `passwords.h` still contains your `EMERGENCY_PHONE_NUMBER`.

### 2. Import Node-RED Flow
Import `nodered/flows/513-sms-gateway-watchdog.json` into your Node-RED instance. It will automatically link to the "SMS Watchdog Management" group on your Home page.

### 3. Enroll Devices
Use the "Enroll" form on the dashboard to register devices you want to monitor. Recommended intervals:
- Critical Infrastructure: 60-120s
- Non-critical sensors: 300s+

---

**Full Changelog:** See [CHANGELOG.md](../CHANGELOG.md) for complete version history.
