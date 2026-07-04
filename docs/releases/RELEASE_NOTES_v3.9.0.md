# Release Notes v3.9.0

**Release Date:** 2026-02-01  
**Type:** Patch Release (Bug Fixes & Documentation)

## Overview

This release fixes the SMS command reply reliability issues and adds comprehensive documentation for the SMS interface. The `/help` command and other SMS commands now reply correctly via the gateway.

## Key Fixes

### 📱 SMS Command Reply Reliability
- **HELP command now works**: Shortened the HELP reply to ≤160 characters for reliable single-SMS delivery. Some GSM modems reject longer messages.
- **3-second delay before reply**: Command replies are delayed by 3 seconds to avoid modem conflicts when both the emergency forward and the reply are queued in quick succession.
- **MQTT-based inter-flow communication**: Replaced Node-RED Link nodes with MQTT topic `sms/command/received` for more reliable communication between flows 511 and 514.
- **Explicit JSON payloads**: All MQTT payloads to `sms/gateway/command/send` now use `JSON.stringify()` for gateway device compatibility.
- **Robust payload parsing**: Flow 514 handles object, JSON string, and Buffer payloads from the MQTT in node.

## Documentation Updates

### New Documentation
- **`docs/SMS_INTERFACE.md`**: Comprehensive SMS command reference, message flow, emergency forwarding, and troubleshooting guide.

### Updated Documentation
- **`nodered/flows/README.md`**: SMS flows (510, 511, 514) with 3s delay, shortened HELP, default allowed phones (`+40740244845`, `+40745218721`).
- **`docs/MQTT_PROTOCOL.md`**: Added `sms/command/received` topic and internal schema.
- **`docs/TELEGRAM_INTERFACE.md`**: Added SMS parity reference.
- **`docs/developer/WORKFLOW.md`**: SMS testing in integration test checklist.
- **Main `README.md`**: Added SMS Interface documentation link.

## Files Changed

### Node-RED Flows
- `nodered/flows/514-sms-gateway-interface.json` - 3s delay node, shortened HELP reply.
- `nodered/flows/511-sms-gateway-status.json` - (previous session) MQTT publish to `sms/command/received`.
- `nodered/flows/510-sms-gateway-controls.json` - (previous session) Default allowed phones with full country code.

### Documentation
- `docs/SMS_INTERFACE.md` - **NEW**
- `nodered/flows/README.md`
- `docs/MQTT_PROTOCOL.md`
- `docs/TELEGRAM_INTERFACE.md`
- `docs/developer/WORKFLOW.md`
- `README.md`

## Migration Guide

### 1. Update Node-RED Flows
Re-import the updated flows:
- `nodered/flows/514-sms-gateway-interface.json`

Click **Deploy** after import.

### 2. Verify Configuration
- Ensure allowed phones use full country code (e.g. `+40740244845`).
- Emergency phone is hardcoded to `+40740244845` in flow 511.

### 3. Test
Send `HELP` via SMS to the gateway SIM. You should receive:
1. Forwarded copy of your message (~immediately)
2. Command list reply (~3 seconds later)

---

**Full Changelog:** See [CHANGELOG.md](../../CHANGELOG.md) for complete version history.
