# Release Notes v3.7.0

**Release Date:** 2026-01-25  
**Type:** Minor Release (New Features)

## Overview

This release adds comprehensive Node-RED integration for the SMS Gateway device, providing a complete management interface with dashboard controls, message logging, Telegram automation, and watchdog monitoring.

## Changes

### SMS Gateway Node-RED Integration

#### New Node-RED Flows
- ✅ **510-sms-gateway-controls.json** - Dashboard control interface
  - Send SMS via web UI
  - Phone number and message input fields
  - Real-time status display (WiFi, MQTT, GSM)
  - Connection status indicators
  - Send response notifications

- ✅ **511-sms-gateway-status.json** - Status monitoring and message logging
  - Complete SMS message history (last 100 messages)
  - Real-time message logging
  - Sender, message text, and timestamp display
  - Clear log functionality
  - Modern UI with message cards

- ✅ **512-sms-gateway-telegram.json** - Telegram bot integration
  - `/sms <phone> <message>` - Send SMS via Telegram
  - `/sms_status` - Get SMS Gateway status
  - `/sms_log` - View recent SMS messages
  - Automatic notifications for received SMS
  - Command response tracking

#### Watchdog Integration
- ✅ **Updated 90-device-watchdog.json**
  - Added SMS Gateway monitoring
  - Topic: `sms/gateway/status`
  - Timeout: 5 minutes
  - Telegram alerts for online/offline status

#### UI Components
- ✅ **Updated 00-base-config.json**
  - Added `ui_group_sms_gateway` for control interface
  - Added `ui_group_sms_logs` for message history

### SMS Gateway Device Features

#### Device Online Notification
- ✅ Automatically sends SMS when device completes initialization
- Includes boot count, WiFi status, IP address, MQTT status, and GSM status
- Provides immediate feedback that device is operational

### SMS Gateway Device Fixes

#### Compilation Fixes
- ✅ Fixed TinyGSM API compatibility - Implemented SMS reading using AT commands
- ✅ Fixed `emptySMSBuffer()` error - Replaced with AT command implementation
- ✅ Fixed `serialGsm` declaration order
- ✅ Added forward declarations for SMS functions

#### Build System Fixes
- ✅ Fixed intelhex ModuleNotFoundError - Pinned esptool version
- ✅ Fixed CRC32 library conflict
- ✅ Removed duplicate TINY_GSM_MODEM_SIM800 definition
- ✅ Simplified platformio.ini (removed redundant esp32dev environment)

## Files Changed

### Node-RED Flows
- `nodered/flows/510-sms-gateway-controls.json` - NEW: Control interface
- `nodered/flows/511-sms-gateway-status.json` - NEW: Status and logging
- `nodered/flows/512-sms-gateway-telegram.json` - NEW: Telegram integration
- `nodered/flows/00-base-config.json` - Added UI groups
- `nodered/flows/50-telegram-interface.json` - Added SMS Gateway router link
- `nodered/flows/90-device-watchdog.json` - Added SMS Gateway monitoring

### Device Code
- `device/sms-gateway/src/main.cpp` - Device Online notification, AT command implementation
- `device/sms-gateway/platformio.ini` - Simplified configuration, pinned esptool
- `device/sms-gateway/.gitignore` - Enhanced PlatformIO exclusions
- `device/sms-gateway/README.md` - Updated documentation

## Migration Guide

### Importing Node-RED Flows

Import the new flows in this order:

1. `00-base-config.json` (if not already imported, or re-import to get new UI groups)
2. `510-sms-gateway-controls.json`
3. `511-sms-gateway-status.json`
4. `512-sms-gateway-telegram.json`
5. `90-device-watchdog.json` (re-import to get SMS Gateway monitoring)

**Note:** The SMS Gateway flows depend on:
- `mqtt_broker_local` (from 00-base-config.json)
- `telegram_bot_config` (from 50-telegram-interface.json)
- UI groups from 00-base-config.json

### Telegram Commands

New Telegram commands available:
- `/sms +1234567890 Hello from automation!` - Send SMS
- `/sms_status` - Check SMS Gateway status
- `/sms_log` - View recent SMS messages

## Testing

✅ All Node-RED flows created and validated  
✅ Dashboard UI components functional  
✅ Message logging working  
✅ Telegram commands integrated  
✅ Watchdog monitoring configured  
✅ Device Online SMS notification tested  
✅ All compilation errors resolved  
✅ Project builds successfully  
✅ All features verified on hardware

## Known Issues

None. All features are working as expected.

## Contributors

- SMS Gateway device implementation
- Node-RED integration
- Telegram automation
- Watchdog monitoring

## Next Steps

- Monitor SMS Gateway in production
- Test automation workflows
- Expand Telegram command set if needed
- Add SMS templates/shortcuts

---

**Full Changelog:** See [CHANGELOG.md](../CHANGELOG.md) for complete version history.
