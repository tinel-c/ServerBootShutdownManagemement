# Release Notes v3.10.0

**Release Date:** 2026-02-08  
**Type:** Minor Release (New Features)

## Overview

This release adds multi-SMS reply support for the SMS gateway, a comprehensive HELP that sends 8 messages with full command descriptions, and full Telegram parity including camera commands (CAMERA_STATUS, CAMERA_HELP).

## New Features

### 📱 Multi-SMS Replies
- **Reply from device in multiple SMS messages**: Flow 514 can now send multiple SMS replies (e.g. HELP sends 8 chunks) with proper spacing so the modem sends one at a time.
- **`replyMultiple(texts)` helper**: New helper in the command handler returns an array of MQTT messages; a rate-limit delay (1 message per 5 seconds) after the 3s delay spaces them.
- **Rate-limit delay node**: New "Rate 1 per 5s (multi-SMS)" delay in flow 514 between the 3s delay and SMS Reply MQTT out.

### 📋 Comprehensive HELP (8 SMS)
- **HELP / COMMANDS / LIST / START** now send **8 SMS messages** with descriptions:
  1. Server: BOOT, SHUTDOWN, FORCE, STATUS
  2. Gate + Sliding gate
  3. Secondary gate
  4. Garden + Lights (16 lights)
  5. Pump (including trenches)
  6. Aquarium
  7. Camera
  8. SMS gateway + help commands
- **LIST** added as alias for COMMANDS (Telegram parity).

### 📷 Camera Commands (Telegram Parity)
- **CAMERA_STATUS**: Returns Tapo camera health and last detection event (uses same flow context as flow 611).
- **CAMERA_HELP**: Short help for camera commands.

### Documentation
- **`docs/SMS_INTERFACE.md`**: Camera section, HELP documents 8-SMS and LIST; message flow and reply delay describe multi-SMS.
- **`nodered/flows/README.md`**: 514 section updated with multi-SMS HELP, CAMERA commands, LIST.

## Files Changed

### Node-RED Flows
- `nodered/flows/514-sms-gateway-interface.json` - replyMultiple(), 8-chunk HELP, rate-limit delay node, camera_status/camera_help, list alias; flow comment updated.

### Documentation
- `docs/SMS_INTERFACE.md` - Camera commands, multi-SMS HELP, LIST.
- `nodered/flows/README.md` - 514 multi-SMS and camera.

## Migration Guide

### 1. Update Node-RED Flows
Re-import the updated flow:
- `nodered/flows/514-sms-gateway-interface.json`

Click **Deploy** after import.

### 2. Test
- Send **HELP** (or **COMMANDS** or **LIST**) via SMS. You should receive 8 SMS messages (first after ~3s, then one every ~5s).
- Send **CAMERA_STATUS** or **CAMERA_HELP** to verify camera parity.

---

**Full Changelog:** See [CHANGELOG.md](CHANGELOG.md) for complete version history.
