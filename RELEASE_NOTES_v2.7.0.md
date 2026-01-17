# Release Notes v2.7.0 - Aquarium Light Automation

**Release Date:** January 17, 2026  
**Version:** 2.7.0  
**Type:** Minor Feature Release

---

## 🐠 Overview

This release introduces complete **Aquarium Light Automation** to the home automation system. The aquarium light control includes manual dashboard control, Telegram remote control, automatic daily scheduling, device health monitoring, and full state tracking.

---

## ✨ New Features

### 🐠 Aquarium Light Control System

#### **500-aquarium-light-controls.json** (NEW)
Complete aquarium light control with manual and automatic operation:
- **Manual Control:** Dashboard 2.0 UI switch (🐠 Lumina Acvariu)
- **Automatic Schedule:** Daily timer (ON: 06:00, OFF: 22:00)
- **State Tracking:** Global context for status queries
- **Dashboard 2.0:** Native `ui-switch` with boolean conversion
- **Decoupled Switch:** Prevents feedback loops
- **MQTT Integration:** Full Tasmota device support

**Hardware:**
- Device: `sursaAcvariu` (Tasmota)
- Topics: `stat/sursaAcvariu/POWER`, `cmnd/sursaAcvariu/POWER`

**Features:**
- Single relay control
- Retained message support (`rap: true`)
- Boolean conversion (ON/OFF ↔ true/false)
- Timer-based automation using `node-red-contrib-timerswitch`

---

#### **501-aquarium-telegram.json** (NEW)
Complete Telegram bot integration for remote aquarium control:

**Commands:**
- `/aquarium_on` - Turn light ON
- `/aquarium_off` - Turn light OFF
- `/aquarium_toggle` - Toggle light state
- `/aquarium_status` - Get current status with interactive buttons
- `/aquarium_help` - Show command reference with quick actions

**Features:**
- Direct telegram receiver/event integration
- Command routing with 7 outputs
- MQTT command publishing
- State tracking (reads from `global.aquarium_state`)
- Interactive inline keyboards for all responses
- Status query with refresh button
- Beautiful emoji formatting (🐠 💡 ⚫ 🔄 📊)
- Command logging with request IDs
- Callback query handling

---

### 📱 Main Telegram Interface Updates

#### **50-telegram-interface.json** (UPDATED)
Integrated aquarium commands into main Telegram help system:

**Changes:**
- Added `/aquarium_*` to command filtering for proper routing
- Added **🐠 AQUARIUM CONTROL** section to `/help` command
- Added aquarium section to `/commands` list with detailed documentation
- Added aquarium quick action buttons to inline keyboards
- Listed all 5 aquarium commands in help text

**New Sections:**
```
🐠 *AQUARIUM CONTROL*
💡 `/aquarium_on` - Turn light ON
⚫ `/aquarium_off` - Turn light OFF
🔄 `/aquarium_toggle` - Toggle light
📊 `/aquarium_status` - Get status
❓ `/aquarium_help` - Aquarium help
```

**New Buttons:**
- 💡 Aquarium ON
- ⚫ Aquarium OFF
- 📊 Aquarium Status

---

### 🔍 Device Monitoring Updates

#### **90-device-watchdog.json** (UPDATED)
Added aquarium light to health monitoring system:

**New Monitoring (9th Device):**
- Device: 🐠 Aquarium Light
- Topic: `tele/sursaAcvariu/STATE`
- Timeout: 11 minutes
- Alerts: 
  - `🟢 Aquarium Light ONLINE`
  - `🔴 Aquarium Light OFFLINE`

**Complete Device List (9 devices):**
1. 🚪 Main Gate
2. 🚪 Primary Sliding Gate
3. 🚪 Secondary Sliding Gate
4. 💧 Irrigation System
5. 💧 Water Pump
6. ⚡ Garden Power
7. 💡 Garden Lights
8. ⚡ Front House Power
9. 🐠 Aquarium Light (NEW!)

---

## 🏗️ Architecture

### Control Flow
```
Manual Control:
  Dashboard UI → Boolean Conversion → MQTT Command

Telegram Control:
  Telegram Bot → Command Router → MQTT Command

Automatic Control:
  Timer Switch (06:00/22:00) → MQTT Command

All paths → cmnd/sursaAcvariu/POWER
```

### State Tracking
```
MQTT Status → Boolean Conversion → Dashboard Update
            → State Storage (global.aquarium_state)
            → Telegram Status Queries
```

### Monitoring
```
MQTT Heartbeat → Trigger (11 min timeout) → Telegram Alerts
```

---

## 📊 System Statistics

### Automation Domains
- **Total Domains:** 9 (Servers, Gates x3, Power, Lights, Irrigation, Aquarium)
- **NEW Domain:** Aquarium Light Control

### Device Monitoring
- **Total Devices:** 9 Tasmota devices
- **NEW Device:** sursaAcvariu (Aquarium Light)

### Telegram Commands
- **Total Commands:** 55+ commands across all domains
- **NEW Commands:** 5 aquarium commands (`/aquarium_on`, `/aquarium_off`, `/aquarium_toggle`, `/aquarium_status`, `/aquarium_help`)

### Control Points
- **Total Relays/Switches:** 30+ across all devices
- **NEW Control:** 1 aquarium light relay

---

## 🔧 Technical Details

### New Dependencies
- `node-red-contrib-timerswitch` - Timer scheduling library for automatic daily schedule

### Flow Numbers
- **500:** Aquarium Light Controls (manual + automatic)
- **501:** Aquarium Telegram Integration

### MQTT Topics
- `stat/sursaAcvariu/POWER` - Status updates
- `cmnd/sursaAcvariu/POWER` - Commands (ON/OFF/TOGGLE)
- `tele/sursaAcvariu/STATE` - Heartbeat (monitoring)

### Global Context
- `global.aquarium_state` - Stores light status and last update time

### UI Components
- **Page:** Home
- **Group:** Acvariu
- **Switch:** 🐠 Lumina Acvariu (Dashboard 2.0)

---

## 🎯 Use Cases

### Energy Management
- Automatic OFF at 22:00 saves energy during night hours
- Automatic ON at 06:00 ensures light during daylight hours

### Fish Health
- Regular light cycle (16 hours ON, 8 hours OFF)
- Consistent daily schedule promotes healthy aquatic environment

### Remote Control
- Telegram control from anywhere
- Manual override via Dashboard
- Status monitoring on demand

### Home Automation
- Integrated with existing automation system
- Health monitoring with alerts
- Centralized control interface

---

## 📦 Files Changed

### New Files
- `nodered/flows/500-aquarium-light-controls.json` - Complete aquarium control flow
- `nodered/flows/501-aquarium-telegram.json` - Telegram integration
- `RELEASE_NOTES_v2.7.0.md` - This file

### Modified Files
- `nodered/flows/50-telegram-interface.json` - Added aquarium commands
- `nodered/flows/90-device-watchdog.json` - Added aquarium monitoring

---

## 🚀 Installation

### For New Installations
1. Ensure `node-red-contrib-timerswitch` is installed
2. Import `500-aquarium-light-controls.json`
3. Import `501-aquarium-telegram.json`
4. Update `50-telegram-interface.json` with new version
5. Update `90-device-watchdog.json` with new version
6. Configure MQTT broker if needed
7. Deploy flows

### For Existing Installations
1. Update flows via Node-RED import
2. Deploy and test all functionality

---

## ✅ Testing Checklist

### Manual Control
- [ ] Dashboard switch turns light ON
- [ ] Dashboard switch turns light OFF
- [ ] State updates correctly in UI

### Telegram Control
- [ ] `/aquarium_on` turns light ON
- [ ] `/aquarium_off` turns light OFF
- [ ] `/aquarium_toggle` toggles state
- [ ] `/aquarium_status` shows current state
- [ ] `/aquarium_help` displays command reference
- [ ] Inline keyboard buttons work

### Automatic Schedule
- [ ] Light turns ON at 06:00 (or test with custom time)
- [ ] Light turns OFF at 22:00 (or test with custom time)
- [ ] Manual override still works during automatic schedule

### Monitoring
- [ ] Device shows as ONLINE in watchdog
- [ ] Offline alert works (disconnect device temporarily)
- [ ] Online alert works (reconnect device)

### Integration
- [ ] `/help` shows aquarium section
- [ ] `/commands` shows aquarium section
- [ ] State tracking works across Dashboard and Telegram

---

## 📝 Configuration

### Modify Schedule
To change automatic ON/OFF times:
1. Open Node-RED
2. Double-click "Aquarium Daily Schedule" node
3. Edit `on_h`, `on_m`, `on_s` for ON time
4. Edit `off_h`, `off_m`, `off_s` for OFF time
5. Deploy changes

### Disable Automatic Schedule
To disable timer:
1. Open Node-RED
2. Double-click "Aquarium Daily Schedule" node
3. Uncheck the schedule or set `disabled: true`
4. Deploy changes

---

## 🐛 Known Issues

None reported.

---

## 📚 Documentation

### Updated Documentation
- Updated architecture diagram descriptions
- Updated command reference
- Updated Telegram help system

### New Documentation
- Aquarium control flow documentation (inline)
- Aquarium Telegram integration documentation (inline)
- Schedule configuration documentation

---

## 🔄 Breaking Changes

None. This is a purely additive release.

---

## 🙏 Acknowledgments

- `node-red-contrib-timerswitch` for timer scheduling functionality
- Tasmota firmware for reliable device control
- Node-RED Dashboard 2.0 for modern UI components

---

## 📞 Support

For issues or questions:
1. Check the inline documentation in flow files
2. Review the testing checklist
3. Verify MQTT broker connectivity
4. Check Tasmota device configuration

---

## 🔮 Future Enhancements

Potential future additions:
- Temperature monitoring integration
- Water quality sensors
- Feeding schedule automation
- Multiple lighting zones
- Adaptive scheduling based on daylight

---

**Version:** 2.7.0  
**Released:** January 17, 2026  
**Focus:** Aquarium Light Automation Integration  
**Status:** Stable ✅
