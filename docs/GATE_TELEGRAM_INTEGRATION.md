# Gate Telegram Integration Guide

This guide explains how to use Telegram to control and monitor the gate automation system.

## Overview

The gate Telegram integration allows you to:
- Open the main gate remotely via Telegram
- Check gate status (power, relays, mains, keypad)
- Receive automatic notifications for power status changes
- View command history and system state

## Prerequisites

1. **Telegram Bot Configured**: You must have the server management Telegram bot already configured (see `nodered/TELEGRAM_SETUP.md`)
2. **Gate Flows Imported**: Import gate flow files in order:
   - `200-gate-base-config.json`
   - `210-main-gate-controls.json`
   - `211-main-gate-status.json`
   - `212-gate-telegram.json`

## Shared Bot Configuration

The gate automation uses the **same Telegram bot** as the server management system. Both systems run on the same Node-RED instance and share the `telegram_bot_config` configuration node.

### Benefits of Shared Bot:
- ✅ Single bot for all automation tasks
- ✅ Unified command interface
- ✅ No additional bot token needed
- ✅ Consistent user experience

## Available Gate Commands

### `/gate_open` or `/gate`
Opens the main gate by activating Relay 2 with a 1-second pulse.

**Example:**
```
/gate_open
```

**Response:**
```
🚪 Opening Main Gate...

Relay 2 activated (1 second pulse)
Request ID: telegram-gate-1234567890
```

### `/gate_status`
Get comprehensive gate status including power, relays, mains, and keypad.

**Example:**
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

Last Command:
relay2_toggle at 17.01.2026, 14:25:00
```

### `/gate_help`
Show gate-specific help message with available commands and quick action buttons.

**Example:**
```
/gate_help
```

**Response:**
```
🚪 Gate Control Bot

Available Commands:

🚪 /gate_open or /gate
   Open the main gate (Relay 2)

📊 /gate_status
   Get gate status and power info

❓ /gate_help
   Show this help message

Features:
• Automatic power status notifications
• Real-time relay monitoring
• Keypad connectivity tracking
• Command history logging

Quick Actions:
Use the buttons below:
[🚪 Open Main Gate] [📊 Gate Status] [❓ Help]
```

## Automatic Notifications

The gate system sends automatic Telegram notifications for important events.

### Power Status Changes

When the gate controller switches between mains power and battery (or vice versa), you'll receive a notification:

```
🔌 Main Gate Power Status Changed

New Status: BATTERY
Time: 17.01.2026, 14:30:00
```

**Power Status Values:**
- `MAINS` 🔌 - Running on mains power (normal)
- `BATTERY` 🔋 - Running on battery backup (power outage)
- `UNKNOWN` ❓ - Status not yet received

### Notification Settings

Notifications are sent to all users who have:
1. Started a conversation with the bot (sent any command)
2. Executed any gate command (automatically registers for notifications)

## Command History and Logging

All Telegram gate commands are logged with:
- **Action**: Type of command (e.g., `relay2_toggle`)
- **Timestamp**: When command was issued
- **Request ID**: Unique identifier for tracking
- **Source**: Always `telegram` for bot commands
- **User ID**: Telegram user who issued the command

Commands are stored in flow context:
- `lastCommand`: Most recent command
- `commandHistory`: Last 10 commands (FIFO)

View history via `/gate_status` command.

## Integration with Server Commands

The unified `/help` command now shows both server and gate commands:

```
🤖 Server Management Bot

Server Commands:

🟢 /boot [dell|hp]
   Boot a server (default: dell)

🟠 /shutdown [dell|hp]
   Graceful shutdown (default: dell)

🔴 /force [dell|hp]
   Force shutdown (default: dell)

📊 /status
   Get server status

Gate Commands:

🚪 /gate_open or /gate
   Open the main gate

📊 /gate_status
   Get gate status

❓ /gate_help
   Show gate commands

❓ /help
   Show this help message
```

The main help keyboard now includes gate buttons:
```
[🟢 Boot Dell] [🟢 Boot HP]
[🟠 Shutdown Dell] [🟠 Shutdown HP]
[🔴 Force Dell] [🔴 Force HP]
[🚪 Open Gate] [📊 Gate Status]
[📊 Server Status] [❓ Help]
```

## Quick Action Buttons

All gate commands support **inline keyboards** for one-tap actions:

### Gate Help Keyboard:
```
[🚪 Open Main Gate]
[📊 Gate Status] [❓ Help]
```

### Main Help Keyboard:
Includes gate buttons alongside server controls for unified access.

## State Management

The gate system tracks state in flow context:

```javascript
gate_state: {
    initialized: true,
    timestamp: "2026-01-17T14:30:00.000Z",
    mainGate: {
        relay1: "ON",
        relay2: "OFF",
        relay3: "OFF",
        relay4: "OFF",
        power: "MAINS",
        mains: "ON",
        keypad: "CONNECTED",
        lastUpdate: "2026-01-17T14:30:00.000Z"
    }
}
```

This state is:
- Updated in real-time from MQTT
- Used by `/gate_status` command
- Shared between UI dashboard and Telegram

## MQTT Topics

The Telegram integration publishes to and subscribes from these topics:

### Commands (Published):
- `MainGate/CMD/Relay2` - Open gate command

### Status (Subscribed):
- `MainGate/STAT/eventPower` - Power status changes (triggers notifications)
- `MainGate/STAT/reccurentStatusRelay2` - Relay 2 status (main gate)
- `MainGate/STAT/reccurentStatusMains` - Mains power availability
- `MainGate/STAT/reccurentStatusKeypad` - Keypad connectivity

## Security Considerations

### Authorization

The gate Telegram integration respects the same authorization as server commands:

- If `TELEGRAM_ALLOWED_USERS` environment variable is set, only users in the list can use gate commands
- Unauthorized users receive an "Unauthorized" message
- Authorization is checked in the parse function before routing commands

### Command Tracking

All commands are logged with:
- User ID (Telegram user identifier)
- Timestamp (when command was issued)
- Request ID (unique tracking identifier)
- Source (always "telegram")

This provides full audit trail for security and troubleshooting.

## Troubleshooting

### Gate Commands Not Working

1. **Check Bot Configuration**:
   ```bash
   # View Node-RED logs
   journalctl -u nodered -f
   ```
   Look for errors related to `telegram_bot_config`

2. **Verify Gate Flows Imported**:
   - Open Node-RED editor: http://localhost:1880
   - Check that `212-gate-telegram.json` is imported
   - Verify all nodes are connected (no warnings)

3. **Check MQTT Broker**:
   ```bash
   # Check MQTT broker is running
   systemctl status mosquitto
   
   # Subscribe to gate topics
   mosquitto_sub -t "MainGate/#" -v
   ```

4. **Test MQTT Manually**:
   ```bash
   # Manually trigger gate
   mosquitto_pub -t "MainGate/CMD/Relay2" -m "ON"
   ```

### Notifications Not Received

1. **Check Chat ID Registration**:
   - Send any gate command (e.g., `/gate_help`)
   - This automatically registers your chat ID
   - Verify in Node-RED debug: `gate_telegram_chat_ids` context

2. **Check Power Status Topic**:
   ```bash
   # Subscribe to power status
   mosquitto_sub -t "MainGate/STAT/eventPower" -v
   ```
   Ensure messages are being published

3. **Check RBE Node**:
   - Notifications only sent when power status **changes**
   - If status stays the same, no notification (by design)

### State Not Updating

1. **Check MQTT Subscriptions**:
   - Verify all `mqtt in` nodes are connected in Node-RED
   - Check for subscription errors in Node-RED logs

2. **Check Context**:
   - Open Node-RED debug panel
   - Inject test message to check context:
     ```javascript
     msg.payload = flow.get('gate_state');
     return msg;
     ```

3. **Restart Node-RED**:
   ```bash
   sudo systemctl restart nodered
   ```

## Advanced Usage

### Custom Command Responses

You can modify the gate command handler functions to customize responses:

**Example - Add confirmation emoji:**
```javascript
// In gate_telegram_handle_open function
const confirmationMsg = {
    ...msg,
    payload: {
        chatId: telegramData.chatId,
        type: 'message',
        content: `✅ Gate opened successfully!\\n\\n🚪 Main gate is now open.`,
        parse_mode: 'Markdown'
    },
    topic: 'send'
};
```

### Additional Notifications

You can add more notification triggers by subscribing to other MQTT topics:

**Example - Notify on relay status change:**
```javascript
// Add new mqtt in node for relay status
// Topic: MainGate/STAT/reccurentStatusRelay2
// Process with rbe node
// Format notification and send to telegram_sender
```

### Multiple Gate Support

To control multiple gates:

1. Duplicate the gate flows (213, 214, etc.)
2. Change MQTT topics (e.g., `SecondGate/...`)
3. Add new commands (e.g., `/gate2_open`)
4. Update help text and keyboards

## Integration with Dashboard

The Telegram interface and Node-RED dashboard are fully synchronized:

- Commands from Telegram update dashboard in real-time
- Dashboard actions can trigger Telegram notifications
- Both use the same flow context for state
- MQTT topics are shared between both interfaces

## Best Practices

1. **Use Quick Action Buttons**: Faster and prevents typos
2. **Check Status First**: Use `/gate_status` before opening gate
3. **Monitor Notifications**: Enable notifications for power alerts
4. **Test Commands**: Use `/gate_help` to see available options
5. **Audit Trail**: Check command history periodically

## Support

For issues or questions:
- Check Node-RED debug panel for errors
- Review MQTT topics using MQTT Explorer
- Check Telegram Bot API documentation: https://core.telegram.org/bots/api
- Review Node-RED logs: `journalctl -u nodered -f`

---

**Last Updated**: January 2026  
**Version**: 1.0.0 (Gate Telegram Integration)
