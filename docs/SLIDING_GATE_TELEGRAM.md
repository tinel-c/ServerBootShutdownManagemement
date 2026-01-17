# Sliding Gate - Telegram Integration Guide

Complete guide for controlling and monitoring the sliding gate via Telegram bot.

## 📱 Overview

The sliding gate Telegram integration provides remote control and status monitoring for the primary sliding gate system through the same Telegram bot used for server management and main gate control.

## 🎯 Features

### Remote Control
- **Open Gate**: Activate Relay 1 to open the gate
- **Close Gate**: Activate Relay 2 to close the gate
- **Trigger Automation**: Activate Relay 3 for automated operation
- **1-Second Pulse**: All commands use safe 1-second pulse activation

### Status Monitoring
- Real-time relay states (Relays 1-4)
- Last update timestamps
- Command execution confirmations

### Interactive Help
- Command reference with inline keyboard
- Quick action buttons
- Context-sensitive help

## 📋 Available Commands

### Control Commands

#### `/sliding_open`
Opens the sliding gate by activating Relay 1.

**Usage:**
```
/sliding_open
```

**Response:**
```
🔓 Opening Sliding Gate...

Relay 1 activated (1 second pulse)
Request ID: telegram-sliding-open-1705500000000
```

**Action:** Sends MQTT command to `cmnd/automatizare_poarta/Power1`

---

#### `/sliding_close`
Closes the sliding gate by activating Relay 2.

**Usage:**
```
/sliding_close
```

**Response:**
```
🔒 Closing Sliding Gate...

Relay 2 activated (1 second pulse)
Request ID: telegram-sliding-close-1705500000000
```

**Action:** Sends MQTT command to `cmnd/automatizare_poarta/Power2`

---

#### `/sliding_trigger`
Triggers the gate automation by activating Relay 3.

**Usage:**
```
/sliding_trigger
```

**Response:**
```
🔄 Triggering Sliding Gate...

Relay 3 activated (1 second pulse)
Request ID: telegram-sliding-trigger-1705500000000
```

**Action:** Sends MQTT command to `cmnd/automatizare_poarta/Power3`

---

### Status Commands

#### `/sliding_status`
Displays comprehensive status of all sliding gate relays.

**Usage:**
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

**Information Shown:**
- All 4 relay states (ON/OFF/UNKNOWN)
- Last status update timestamp
- Relay function labels

---

### Help Commands

#### `/sliding_help`
Shows sliding gate-specific help with interactive buttons.

**Usage:**
```
/sliding_help
```

**Response:**
```
🚪 Sliding Gate Control Bot

Available Commands:

🔓 /sliding_open
   Open the sliding gate (Relay 1)

🔒 /sliding_close
   Close the sliding gate (Relay 2)

🔄 /sliding_trigger
   Trigger gate automation (Relay 3)

📊 /sliding_status
   Get sliding gate status

❓ /sliding_help
   Show this help message

Features:
• 1-second pulse control
• Command history logging
• Request ID tracking

Quick Actions:
Use the buttons below:
```

**Interactive Buttons:**
- 🔓 Open Sliding Gate
- 🔒 Close Sliding Gate
- 🔄 Trigger
- 📊 Status
- ❓ Help

---

## 🎮 Using Interactive Buttons

All commands are available as inline keyboard buttons for faster access:

### Main Help Menu (`/help`)
The main bot help includes sliding gate buttons:
```
━━━━━ 🚪 GATES ━━━━━
[🚪 Open Main Gate] [📊 Main Status]
[🔓 Open Sliding] [🔒 Close Sliding]
[📊 Sliding Status]
```

### Sliding Gate Help Menu (`/sliding_help`)
Dedicated sliding gate buttons:
```
[🔓 Open Sliding Gate]
[🔒 Close Sliding Gate]
[🔄 Trigger] [📊 Status]
[❓ Help]
```

**Advantages:**
- No typing required
- Prevents command typos
- Faster operation
- Mobile-friendly

## 🔧 Technical Details

### MQTT Topics

**Status Topics (Subscribe):**
```
stat/automatizare_poarta/POWER1  # Relay 1 (Open)
stat/automatizare_poarta/POWER2  # Relay 2 (Close)
stat/automatizare_poarta/POWER3  # Relay 3 (Trigger)
stat/automatizare_poarta/POWER4  # Relay 4 (Open Alt)
```

**Command Topics (Publish):**
```
cmnd/automatizare_poarta/Power1  # Open gate
cmnd/automatizare_poarta/Power2  # Close gate
cmnd/automatizare_poarta/Power3  # Trigger automation
cmnd/automatizare_poarta/Power4  # Alternative open
```

### Relay Functions

| Relay | Function | Command | Use Case |
|-------|----------|---------|----------|
| 1 | Open | `/sliding_open` | Opens the gate |
| 2 | Close | `/sliding_close` | Closes the gate |
| 3 | Trigger | `/sliding_trigger` | Automated operation |
| 4 | Open Alt | (Reserved) | Alternative open method |

### Command Flow

1. **User sends command** → Telegram Bot
2. **Bot parses command** → Routes to handler
3. **Handler creates MQTT message** → Publishes to broker
4. **Tasmota device receives** → Activates relay (1 sec)
5. **Relay state updates** → Published to status topic
6. **Bot receives status** → Updates flow context
7. **Confirmation sent** → User receives response

### State Tracking

The flow maintains sliding gate state in Node-RED flow context:

```javascript
{
  relay1: "ON" | "OFF" | "UNKNOWN",
  relay2: "ON" | "OFF" | "UNKNOWN",
  relay3: "ON" | "OFF" | "UNKNOWN",
  relay4: "ON" | "OFF" | "UNKNOWN",
  lastUpdate: "2026-01-17T14:30:00.000Z"
}
```

**Storage:** `flow.get('sliding_gate_state')`

### Request ID Format

Each command generates a unique request ID for tracking:

```
telegram-sliding-open-1705500000000
telegram-sliding-close-1705500000000
telegram-sliding-trigger-1705500000000
```

**Format:** `telegram-sliding-{action}-{timestamp}`

## 🔐 Security & Authorization

### User Authorization

If `TELEGRAM_ALLOWED_USERS` environment variable is set:
- Only authorized user IDs can execute commands
- Unauthorized users receive: `❌ Unauthorized. You are not allowed to use this bot.`
- Contact system administrator to be added to allowed users list

**Configuration:**
```bash
# In Node-RED settings.js or environment
TELEGRAM_ALLOWED_USERS=123456789,987654321
```

### Command Logging

All commands are logged with:
- User ID (Telegram user ID)
- Command executed
- Timestamp
- Request ID
- Execution result

**View logs:**
```bash
journalctl -u nodered -f | grep sliding
```

## 🚀 Quick Start

### First Time Setup

1. **Start conversation with bot**
   ```
   /start
   ```

2. **Check sliding gate help**
   ```
   /sliding_help
   ```

3. **Check status before operation**
   ```
   /sliding_status
   ```

4. **Test gate control** (if safe)
   ```
   /sliding_open
   ```

### Daily Usage

**Open the gate:**
```
/sliding_open
```
or tap the "🔓 Open Sliding" button in `/help`

**Close the gate:**
```
/sliding_close
```
or tap the "🔒 Close Sliding" button in `/help`

**Check status:**
```
/sliding_status
```
or tap the "📊 Sliding Status" button

## 🔍 Troubleshooting

### Command not working

**Check bot is running:**
```bash
sudo systemctl status nodered
```

**Check MQTT broker:**
```bash
sudo systemctl status mosquitto
```

**Test MQTT manually:**
```bash
# Subscribe to status
mosquitto_sub -h localhost -t "stat/automatizare_poarta/#" -v

# Send test command
mosquitto_pub -h localhost -t "cmnd/automatizare_poarta/Power1" -m "ON"
```

### Status not updating

**Check Tasmota device:**
- Device is online
- MQTT configured correctly
- Publishing to correct topics

**Check Node-RED flows:**
- Flows are deployed
- MQTT broker connection is active
- No errors in debug panel

**View logs:**
```bash
journalctl -u nodered -f
```

### Bot not responding

**Verify bot token:**
- Check `telegram_bot_config` in Node-RED
- Ensure token is valid
- Test with BotFather

**Check authorization:**
- If `TELEGRAM_ALLOWED_USERS` is set, verify your user ID is included
- Ask admin to add your user ID

### Relay activation but gate not moving

**Hardware issues:**
- Check gate motor power
- Verify relay connections
- Test manual operation
- Check gate mechanical components

**Tasmota configuration:**
- Verify relay assignments
- Check pulse time settings
- Review Tasmota rules

## 📊 Integration with Other Systems

### Combined with Main Gate

Both gates use the same Telegram bot:
```
/help          # Shows all gates
/gate_open     # Main gate
/sliding_open  # Sliding gate
```

### Combined with Server Management

Unified bot for all automation:
```
/status         # Server status
/gate_status    # Main gate status
/sliding_status # Sliding gate status
```

### Command Reference

View all commands across all domains:
```
/commands
```

## 📚 Related Documentation

- **[Sliding Gate Integration](SLIDING_GATE_INTEGRATION.md)** - Hardware and MQTT setup
- **[Telegram Commands Reference](TELEGRAM_COMMANDS_REFERENCE.md)** - Complete command list
- **[Gate Import Instructions](GATE_IMPORT_INSTRUCTIONS.md)** - Flow installation
- **[Telegram Setup](../nodered/TELEGRAM_SETUP.md)** - Bot configuration
- **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues

## 💡 Tips & Best Practices

### Safety First
- Always check status before operating
- Ensure area is clear before opening/closing
- Use `/sliding_status` to verify gate position
- Test in safe conditions first

### Efficient Usage
- Use buttons instead of typing commands
- Save frequently used commands
- Check status regularly
- Monitor for unexpected state changes

### Monitoring
- Enable notifications for status changes
- Review command history periodically
- Check logs for errors
- Verify relay states match physical gate position

### Maintenance
- Test commands regularly
- Update bot token if needed
- Review authorization list
- Keep Node-RED and dependencies updated

## 🎯 Example Scenarios

### Scenario 1: Remote Gate Opening
```
User: /sliding_status
Bot: All relays OFF

User: /sliding_open
Bot: 🔓 Opening Sliding Gate...
     Relay 1 activated (1 second pulse)

User: /sliding_status
Bot: Relay 1 (Open): OFF  # Returns to OFF after 1-sec pulse
```

### Scenario 2: Automated Operation
```
User: /sliding_trigger
Bot: 🔄 Triggering Sliding Gate...
     Relay 3 activated (1 second pulse)
     
# Gate automation takes over
```

### Scenario 3: Full Cycle
```
User: /sliding_open
Bot: Gate opening...

# Wait for gate to fully open

User: /sliding_close
Bot: Gate closing...

User: /sliding_status
Bot: All relays OFF (gate closed)
```

---

**Version**: 1.0.0  
**Last Updated**: January 2026  
**Flow File**: `221-sliding-gate-telegram.json`  
**Related Flows**: `220-sliding-gate-controls.json`, `50-telegram-interface.json`
