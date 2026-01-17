# Telegram Bot - Complete Command Reference

This document provides a comprehensive reference for all available Telegram bot commands across all automation domains.

## Quick Access

**Commands:**
- `/help` - Quick help with interactive buttons
- `/commands` or `/list` - Complete command reference (this document)
- `/start` - Start bot conversation (shows help)

## 🖥️ Server Management

### Boot Commands

| Command | Description | Method | Target |
|---------|-------------|--------|--------|
| `/boot` | Boot Dell T310 (default) | WoL | Dell T310 |
| `/boot dell` | Boot Dell T310 | Wake-on-LAN | Dell T310 |
| `/boot hp` | Boot HP DL360p | iLO API | HP DL360p |

**Examples:**
```
/boot
/boot dell
/boot hp
```

**Response:** Confirmation message with request ID and method used.

### Shutdown Commands

| Command | Description | Timeout | Type |
|---------|-------------|---------|------|
| `/shutdown` | Graceful shutdown Dell (default) | 300s | Graceful |
| `/shutdown dell` | Graceful shutdown Dell T310 | 300s | Graceful |
| `/shutdown hp` | Graceful shutdown HP DL360p | 300s | Graceful |

**Examples:**
```
/shutdown
/shutdown dell
/shutdown hp
```

**Response:** Confirmation with timeout and request ID.

**Note:** Graceful shutdown allows services to shut down cleanly.

### Force Shutdown Commands

| Command | Description | Warning |
|---------|-------------|---------|
| `/force` | Force shutdown Dell (default) | ⚠️ Immediate |
| `/force dell` | Force shutdown Dell T310 | ⚠️ Immediate |
| `/force hp` | Force shutdown HP DL360p | ⚠️ Immediate |

**Examples:**
```
/force dell
/force hp
```

**Response:** Warning message with immediate shutdown confirmation.

**⚠️ Warning:** Force shutdown immediately powers off the server without graceful service shutdown.

### Status Commands

| Command | Description | Shows |
|---------|-------------|-------|
| `/status` | Get all server status | Dell T310, HP DL360p |

**Examples:**
```
/status
```

**Response:**
```
📊 Server Status

🟢 Dell T310: ONLINE
   Last update: 17.01.2026, 14:30:00

🟢 HP DL360p: ONLINE
   Last update: 17.01.2026, 14:30:00
```

**Status Indicators:**
- 🟢 **ONLINE** - Server is running
- 🔴 **OFFLINE** - Server is powered off
- 🟡 **UNKNOWN** - No status data available

## 🚪 Main Gate Automation

### Control Commands

| Command | Description | Action | Duration |
|---------|-------------|--------|----------|
| `/gate_open` | Open main gate | Relay 2 ON | 1 second pulse |
| `/gate` | Open main gate (short) | Relay 2 ON | 1 second pulse |

**Examples:**
```
/gate_open
/gate
```

**Response:**
```
🚪 Opening Main Gate...

Relay 2 activated (1 second pulse)
Request ID: telegram-gate-1234567890
```

**Note:** The gate controller uses a 1-second pulse to trigger the gate mechanism.

### Status Commands

| Command | Description | Shows |
|---------|-------------|-------|
| `/gate_status` | Get comprehensive gate status | Power, Relays, Mains, Keypad |

**Examples:**
```
/gate_status
```

**Response:**
```
🚪 Main Gate Status

🔌 Power: MAINS

Relays:
🟢 Relay 1: ON
⚫ Relay 2: OFF
⚫ Relay 3: OFF
⚫ Relay 4: OFF

🔌 Mains: ON
🔢 Keypad: CONNECTED

🕐 Last update: 17.01.2026, 14:30:00
```

**Status Indicators:**
- 🔌 **MAINS** - Running on mains power
- 🔋 **BATTERY** - Running on battery backup
- 🟢 **ON** - Relay is active
- ⚫ **OFF** - Relay is inactive
- 🔢 **CONNECTED** - Keypad is online
- ❌ **DISCONNECTED** - Keypad is offline

### Help Commands

| Command | Description |
|---------|-------------|
| `/gate_help` | Show main gate-specific help with buttons |

**Examples:**
```
/gate_help
```

## 🚪 Sliding Gate Automation

### Control Commands

| Command | Description | Action | Duration |
|---------|-------------|--------|----------|
| `/sliding_open` | Open sliding gate | Relay 1 ON | 1 second pulse |
| `/sliding_close` | Close sliding gate | Relay 2 ON | 1 second pulse |
| `/sliding_trigger` | Trigger gate automation | Relay 3 ON | 1 second pulse |

**Examples:**
```
/sliding_open
/sliding_close
/sliding_trigger
```

**Response:**
```
🔓 Opening Sliding Gate...

Relay 1 activated (1 second pulse)
Request ID: telegram-sliding-open-1234567890
```

**Note:** 
- Relay 1: Opens the gate
- Relay 2: Closes the gate
- Relay 3: Triggers automated operation
- Relay 4: Alternative open (available for future use)

### Status Commands

| Command | Description | Shows |
|---------|-------------|-------|
| `/sliding_status` | Get sliding gate status | Relays 1-4 status |

**Examples:**
```
/sliding_status
```

**Response:**
```
🚪 Sliding Gate Status

Relays:
Relay 1 (Open): OFF
Relay 2 (Close): OFF
Relay 3 (Trigger): OFF
Relay 4 (Open Alt): OFF

🕐 Last update: 17.01.2026, 14:30:00
```

**Status Indicators:**
- 🟢 **ON** - Relay is active
- ⚫ **OFF** - Relay is inactive
- **UNKNOWN** - No status data available

### Help Commands

| Command | Description |
|---------|-------------|
| `/sliding_help` | Show sliding gate-specific help with buttons |

**Examples:**
```
/sliding_help
```

## ℹ️ General Commands

### Help & Information

| Command | Description |
|---------|-------------|
| `/help` | Show quick help with interactive buttons |
| `/commands` | Show complete command reference (detailed) |
| `/list` | Alias for `/commands` |
| `/start` | Start bot conversation (shows help) |

**Examples:**
```
/help
/commands
/list
/start
```

## 🔔 Automatic Notifications

The bot automatically sends notifications for:

### Server Notifications

1. **State Changes**
   ```
   🟢 Dell T310 Status Changed
   
   State: ONLINE
   Previous: OFFLINE
   Time: 17.01.2026, 14:30:00
   ```

2. **Command Responses**
   ```
   ✅ Command Response
   
   Server: DELL T310
   Status: SUCCESS
   Message: Server booted successfully
   
   Request ID: telegram-boot-1234567890
   ```

### Gate Notifications

1. **Power Status Changes**
   ```
   🔋 Main Gate Power Status Changed
   
   New Status: BATTERY
   Time: 17.01.2026, 14:30:00
   ```

2. **Command Confirmations**
   ```
   🚪 Opening Main Gate...
   
   Relay 2 activated (1 second pulse)
   Request ID: telegram-gate-1234567890
   ```

## 💡 Usage Tips

### Command Defaults
- **Server commands** default to `dell` if no server specified
- **Gate commands** have no defaults (always explicit)

### Button Usage
- Use inline keyboard buttons for faster access
- Buttons automatically fill in command parameters
- Buttons prevent typos and syntax errors

### Case Sensitivity
- All commands are case-insensitive
- `/BOOT dell` works the same as `/boot dell`

### Status Checks
- Always check `/status` before critical operations
- Use `/gate_status` before opening gates
- Status includes last update timestamp

### Command History
- All commands are logged with user ID
- Request IDs track command execution
- View history in command responses

## 🔐 Authorization

If `TELEGRAM_ALLOWED_USERS` environment variable is set:
- Only authorized user IDs can use the bot
- Unauthorized users receive: `❌ Unauthorized. You are not allowed to use this bot.`
- Contact admin to be added to allowed users list

## 📊 System Capabilities

The automation system provides:

✅ **Remote server boot/shutdown**
- Wake-on-LAN for Dell T310
- iLO API for HP DL360p
- Force and graceful shutdown options

✅ **Gate automation control (2 gates)**
- Main gate: Remote opening, power monitoring
- Sliding gate: Open, close, trigger operations
- Power status monitoring (main gate)
- Multi-relay control (both gates)

✅ **Real-time status monitoring**
- Server online/offline status
- Gate power and relay states
- Last update timestamps

✅ **Multi-channel notifications**
- Telegram instant messaging
- SMS alerts (gate power changes)
- Command execution feedback

✅ **Command history & logging**
- Request ID tracking
- User ID logging
- Execution timestamps

## 🆘 Getting Help

### Within Telegram

1. **Quick Help**: `/help` - Shows main commands with buttons
2. **Complete Reference**: `/commands` - This detailed guide
3. **Domain-Specific**: `/gate_help` - Gate automation help

### Common Issues

**Bot not responding:**
- Check bot is configured (see `nodered/TELEGRAM_SETUP.md`)
- Verify you're authorized (if `TELEGRAM_ALLOWED_USERS` is set)
- Check Node-RED is running: `sudo systemctl status nodered`

**Commands not working:**
- Verify MQTT broker is running: `sudo systemctl status mosquitto`
- Check Node-RED logs: `journalctl -u nodered -f`
- Ensure flows are deployed in Node-RED

**Status not updating:**
- Check backend services are running
- Verify MQTT topics are correct
- Restart Node-RED if needed: `sudo systemctl restart nodered`

## 💡 Garden Lights Control

### Control Commands

| Command | Description | Action | Targets |
|---------|-------------|--------|---------|
| `/lights_on` | Turn all lights ON | Activates all 16 lights | All garden lights |
| `/lights_off` | Turn all lights OFF | Deactivates all 16 lights | All garden lights |

**Examples:**
```
/lights_on
/lights_off
```

**Response:**
```
💡 All garden lights turned ON
```

**Hardware:**
- **Lights 1-12**: GardenAutomationLights (12-relay Tasmota device)
  - MQTT: `GardenAutomationLights/CMD/Relay[1-12]`
- **Lights 13-16**: frontHousePower (4-relay Sonoff Power device)
  - MQTT: `cmnd/frontHousePower/POWER[1-4]`

### Status Commands

| Command | Description | Shows |
|---------|-------------|-------|
| `/lights_status` | Get all lights status | Status of all 16 lights |

**Examples:**
```
/lights_status
```

**Response:**
```
💡 Garden Lights Status

GardenAutomationLights:
🟢 Light 1: ON
⚫ Light 2: OFF
🟢 Light 3: ON
... (up to Light 12)

Front House Power:
🟢 Light 13: ON
⚫ Light 14: OFF
🟢 Light 15: ON
⚫ Light 16: OFF

Summary: 8 ON | 8 OFF | 0 Unknown
```

**Status Indicators:**
- 🟢 **ON** - Light is currently ON
- ⚫ **OFF** - Light is currently OFF
- ❓ **UNKNOWN** - Status not available

**Interactive Buttons:**
- 🟢 Turn All ON
- ⚫ Turn All OFF
- 🔄 Refresh Status

### Help Commands

| Command | Description |
|---------|-------------|
| `/lights_help` | Show garden lights help |

**Examples:**
```
/lights_help
```

**Response:** Comprehensive help for garden lights control with hardware information and interactive buttons.

## 📚 Additional Documentation

- **Telegram Setup**: `nodered/TELEGRAM_SETUP.md`
- **Gate Integration**: `docs/GATE_TELEGRAM_INTEGRATION.md`
- **Architecture**: `docs/ARCHITECTURE.md`
- **Troubleshooting**: `docs/TROUBLESHOOTING.md`

## 🔄 Command Summary Table

| Category | Command | Action |
|----------|---------|--------|
| **Server Boot** | `/boot [server]` | Boot server (WoL/iLO) |
| **Server Shutdown** | `/shutdown [server]` | Graceful shutdown |
| **Server Force** | `/force [server]` | Immediate power off |
| **Server Status** | `/status` | Get all server status |
| **Main Gate Open** | `/gate_open` or `/gate` | Open main gate (Relay 2) |
| **Main Gate Status** | `/gate_status` | Get main gate status |
| **Main Gate Help** | `/gate_help` | Main gate help |
| **Sliding Open** | `/sliding_open` | Open sliding gate (Relay 1) |
| **Sliding Close** | `/sliding_close` | Close sliding gate (Relay 2) |
| **Sliding Trigger** | `/sliding_trigger` | Trigger automation (Relay 3) |
| **Sliding Status** | `/sliding_status` | Get sliding gate status |
| **Sliding Help** | `/sliding_help` | Sliding gate help |
| **Lights ON** | `/lights_on` | Turn all 16 lights ON |
| **Lights OFF** | `/lights_off` | Turn all 16 lights OFF |
| **Lights Status** | `/lights_status` | Get all lights status |
| **Lights Help** | `/lights_help` | Garden lights help |
| **Help** | `/help` | Quick help |
| **Commands** | `/commands` or `/list` | Complete reference |
| **Start** | `/start` | Start bot |

---

**Version**: 1.2.0  
**Last Updated**: January 2026  
**Domains**: Server Management, Gate Automation (3 gates), Power Monitoring, Garden Lights  
**Total Commands**: 20+
