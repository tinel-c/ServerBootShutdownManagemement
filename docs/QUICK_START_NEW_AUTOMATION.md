# Quick Start: Adding a New Automation Domain

This guide shows you how to quickly add a new automation domain (gates, lights, irrigation, etc.) to your system.

## Before You Start

- [ ] Node-RED is running
- [ ] Base configuration (000-base-config.json) is imported
- [ ] You have your current flows backed up
- [ ] You've decided on your domain name and number range

## Choose Your Domain

Pick an available number range for your automation:

| Range | Domain | Example |
|-------|--------|---------|
| 200-299 | Gates/Doors | Main gate, garage door |
| 300-399 | Lighting | Indoor/outdoor lights |
| 400-499 | Irrigation | Watering zones |
| 500-599 | Notifications | SMS, email alerts |
| 600-699 | Security | Cameras, alarms |
| 700-799 | HVAC | Heating, cooling |
| 800-899 | Energy | Power monitoring |

**Example: We'll add Gate Automation (200-299)**

## 5-Minute Setup

### Step 1: Copy Base Template (1 minute)

```bash
cd nodered/templates
cp domain-base-template.json ../flows/200-gate-base-config.json
```

### Step 2: Edit Base Config (2 minutes)

Open `nodered/flows/200-gate-base-config.json` and find/replace:

| Find | Replace With | Example |
|------|-------------|---------|
| `DOMAIN_tab` | `gate_tab` | Flow ID |
| `DOMAIN` | `gate` | Throughout file |
| `NUMBER` | `200` | Starting number |
| `MQTT_PREFIX` | `gates` | Topic prefix |

**Quick Replace (in editor):**
```
Find: "DOMAIN"    Replace: "gate"
Find: "NUMBER"    Replace: "200"
```

### Step 3: Import to Node-RED (1 minute)

1. Open Node-RED: http://localhost:1880
2. Menu (≡) → Import
3. Select `200-gate-base-config.json`
4. Click Import
5. Click Deploy

✅ You should now see "Gate Management" page in your dashboard!

### Step 4: Add Control Panel (1 minute)

```bash
cp control-panel-template.json ../flows/210-main-gate-controls.json
```

Edit `210-main-gate-controls.json`:

| Find | Replace With |
|------|-------------|
| `DOMAIN_FEATURE_tab` | `gate_main_tab` |
| `DOMAIN` | `gate` |
| `FEATURE` | `main-gate` |
| `MQTT_PREFIX` | `gates/main` |
| `ACTION1` | `open` |
| `ACTION2` | `close` |

Import to Node-RED and deploy.

✅ You now have Open/Close buttons!

## That's It!

You now have a working automation domain with:
- ✅ Dedicated dashboard page
- ✅ Control buttons
- ✅ MQTT integration
- ✅ Error handling
- ✅ Logging

## Next Steps

### Add Status Display

```bash
# Copy and customize status template
cp status-display-template.json ../flows/211-main-gate-status.json
```

Update MQTT topics to receive status from your device.

### Add Automation Rules

```bash
# Copy and customize automation template  
cp automation-logic-template.json ../flows/213-main-gate-automation.json
```

Add schedules, triggers, and conditional logic.

### Connect Your Device

Update your gate controller to publish/subscribe to:

**Commands (from Node-RED):**
```
Topic: gates/main/gate1/command/open
Payload: {"action":"open","timestamp":"2026-01-17T10:00:00Z"}
```

**Status (to Node-RED):**
```
Topic: gates/main/gate1/status
Payload: {"state":"open","timestamp":"2026-01-17T10:00:05Z"}
```

## Example: Complete Gate Setup

### 1. Base Config (200-gate-base-config.json)
```json
{
    "ui_page": "/gates",
    "groups": ["Control", "Status", "Automation", "Logs"]
}
```

### 2. Main Gate Controls (210-main-gate-controls.json)
```
Buttons:
- Open Main Gate → MQTT: gates/main/gate1/command/open
- Close Main Gate → MQTT: gates/main/gate1/command/close
- Stop → MQTT: gates/main/gate1/command/stop
```

### 3. Status Display (211-main-gate-status.json)
```
Subscribe: gates/main/gate1/status
Display: 
- State: Open/Closed/Moving
- Last Updated: Timestamp
- Position: 0-100%
```

### 4. Sensors (212-main-gate-sensors.json)
```
Subscribe: 
- gates/main/gate1/sensor/motion
- gates/main/gate1/sensor/position
- gates/main/gate1/sensor/obstacle

Display: Sensor values and alerts
```

### 5. Automation (213-main-gate-automation.json)
```
Rules:
- Open at 07:00 on weekdays
- Close at 22:00 every day
- Open when car detected (if authorized)
- Alert on motion when closed
```

## Copy from Existing Flows

If you already have flows in Node-RED:

### Method 1: Copy Nodes Directly

1. Select nodes from old flow (Ctrl+A)
2. Copy (Ctrl+C)
3. Open new flow tab
4. Paste (Ctrl+V)
5. Update node IDs and topics
6. Connect to new structure

### Method 2: Export and Modify

1. Export old flow to JSON
2. Copy nodes section
3. Paste into template
4. Update references
5. Import new flow

## Testing Your Setup

### 1. Test Control Buttons

Click "Open" button:
```bash
# Monitor MQTT to see command
mosquitto_sub -h localhost -t 'gates/main/gate1/command/#' -v
```

### 2. Test Status Display

Publish status update:
```bash
mosquitto_pub -h localhost \
  -t 'gates/main/gate1/status' \
  -m '{"state":"open","timestamp":"2026-01-17T10:00:00Z"}'
```

Check dashboard shows "Open"

### 3. Test Error Handling

Send invalid command:
```bash
mosquitto_pub -h localhost \
  -t 'gates/main/gate1/command/invalid' \
  -m '{}'
```

Check error appears in logs

## Common Customizations

### Change Button Colors

```json
{
    "type": "ui-button",
    "bgcolor": "green",  // or "blue", "red", "#ff0000"
    "icon": "open_in_browser"  // Material Design icon
}
```

### Add Confirmation Dialog

```json
{
    "type": "ui-button",
    "confirmationRequired": true,
    "confirmationMessage": "Really open gate?"
}
```

### Add Time-Based Rules

```javascript
// In automation flow
const now = new Date();
const hour = now.getHours();

if (hour >= 7 && hour < 22) {
    // Allow operation
    return msg;
} else {
    // Block operation
    node.warn("Operation not allowed at this time");
    return null;
}
```

### Add User Authorization

```javascript
// In command function
const allowedUsers = ['admin', 'family'];
const user = msg.req?.user?.username || 'anonymous';

if (!allowedUsers.includes(user)) {
    msg.payload = { error: "Unauthorized" };
    return [null, msg]; // Send to error output
}

return [msg, null]; // Send to success output
```

## Troubleshooting

### Issue: Page doesn't appear in dashboard

**Solution:**
```
1. Check base config was imported first
2. Verify ui_page and ui_base are linked
3. Restart Node-RED: sudo systemctl restart nodered
```

### Issue: Buttons don't work

**Solution:**
```
1. Check MQTT broker is running
2. Verify topic names match
3. Check function node for errors
4. Use debug nodes to trace messages
```

### Issue: Status not updating

**Solution:**
```
1. Verify MQTT subscription topic
2. Check device is publishing
3. Use mosquitto_sub to monitor
4. Check JSON payload format
```

## Resources

- **Full Documentation**: `docs/AUTOMATION_ARCHITECTURE.md`
- **Templates**: `nodered/templates/`
- **Examples**: See existing server management flows (100-199)
- **MQTT Topics**: `docs/AUTOMATION_ARCHITECTURE.md#mqtt-topic-structure`

## Need Help?

1. Check documentation in `docs/` folder
2. Review existing flows for examples
3. Test with MQTT Explorer
4. Check Node-RED debug panel

---

**Next**: Read [Integration Guide](AUTOMATION_INTEGRATION_GUIDE.md) for advanced migration strategies.

**Version**: 1.0.0  
**Last Updated**: 2026-01-17
