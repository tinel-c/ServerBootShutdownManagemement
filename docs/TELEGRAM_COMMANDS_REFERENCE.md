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

## 🚪 Gate Automation

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
| `/gate_help` | Show gate-specific help with buttons |

**Examples:**
```
/gate_help
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

✅ **Gate automation control**
- Remote gate opening
- Power status monitoring
- Relay control

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
| **Gate Open** | `/gate_open` | Open main gate |
| **Gate Status** | `/gate_status` | Get gate status |
| **Gate Help** | `/gate_help` | Gate-specific help |
| **Help** | `/help` | Quick help |
| **Commands** | `/commands` | Complete reference |
| **Start** | `/start` | Start bot |

---

**Version**: 1.0.0  
**Last Updated**: January 2026  
**Domains**: Server Management, Gate Automation
