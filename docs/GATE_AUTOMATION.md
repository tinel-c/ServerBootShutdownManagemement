# Gate Automation System

## Overview

The Gate Automation system provides comprehensive control and monitoring for the main gate controller, including relay control, power monitoring, SMS alerts, and status tracking.

### Hardware

The **main gate** controller runs **[PlatformIO_ESP8266_Main_Entry](https://github.com/tinel-c/PlatformIO_ESP8266_Main_Entry)** firmware on an ESP8266 4-relay board (keypad, MQTT, mains failover, coil protection). The **gate actuator is Relay 3** (`MainGate/CMD/Relay3` / `MainGate/STAT/Relay3` and recurrent status on `MainGate/STAT/reccurentStatusRelay3`).

**See**: [Tasmota Gate Integration Guide](TASMOTA_GATE_INTEGRATION.md) for MQTT topic details (including optional Tasmota-based setups).

## Features

### Main Gate Control
- **Open/Close Switch** - Toggle relay 3 to open/close the main gate
- **1-Second Pulse** - Automatic pulse to prevent continuous relay activation
- **Status Feedback** - Real-time relay state display
- **Command Logging** - All commands logged to flow context

### Status Monitoring
- **Power Status** - Battery/mains power monitoring
- **4 Relays** - Individual relay status display (Relay 1-4)
- **Mains Power** - AC power availability indicator
- **Keypad Status** - Keypad connectivity monitoring
- **Debug Messages** - Real-time debug information display
- **Timestamp** - Last update timestamp

### SMS Notifications
- **Power Alerts** - Automatic SMS on power status changes
- **Change Detection** - Report-by-exception (RBE) filtering
- **Configurable Number** - SMS sent to configured phone number

## Architecture

### Modular Flows

```
Gate Automation (200-299)
├── 200-gate-base-config.json
│   └── UI structure, context initialization
├── 210-main-gate-controls.json
│   └── Open/close switch, relay control
└── 211-main-gate-status.json
    └── Power, relays, mains, keypad, debug
```

### MQTT Topics

#### Commands (Dashboard → Gate Controller)
```
MainGate/CMD/Relay3          # Open/close command (ON/OFF) — main gate actuator
```

#### Status (Gate Controller → Dashboard)
```
MainGate/STAT/Relay3                    # Relay 3 state (main gate)
MainGate/STAT/eventPower                # Power status events
MainGate/STAT/reccurentStatusRelay1     # Relay 1 recurring status
MainGate/STAT/reccurentStatusRelay2     # Relay 2 recurring status
MainGate/STAT/reccurentStatusRelay3     # Relay 3 recurring status (main gate)
MainGate/STAT/reccurentStatusRelay4     # Relay 4 recurring status
MainGate/STAT/reccurentStatusMains      # Mains power status
MainGate/STAT/reccurentStatusKeypad     # Keypad connectivity
MainGate/STAT/message                   # Debug messages
```

#### SMS Integration
```
esp32SMS/smsSend/to          # SMS recipient number
esp32SMS/smsSend/text        # SMS message text
```

## Installation

### Prerequisites

1. Node-RED installed and running
2. Base configuration imported (`000-base-config.json`)
3. MQTT broker running (192.168.2.4:1883 or your broker)
4. Gate controller publishing to MQTT topics

### Import Steps

**1. Import Base Configuration**
```
File: nodered/flows/200-gate-base-config.json
```
- Navigate to Node-RED: http://localhost:1880
- Menu (≡) → Import
- Select `200-gate-base-config.json`
- Click Import
- Click Deploy

✅ You should now see "Gate Management" in the sidebar

**2. Import Main Gate Controls**
```
File: nodered/flows/210-main-gate-controls.json
```
- Menu (≡) → Import
- Select `210-main-gate-controls.json`
- Click Import
- Click Deploy

✅ Control switch now available at `/gates`

**3. Import Main Gate Status**
```
File: nodered/flows/211-main-gate-status.json
```
- Menu (≡) → Import
- Select `211-main-gate-status.json`
- Click Import
- Click Deploy

✅ Status monitoring now active

### Verification

1. **Access Dashboard**: http://localhost:1880/dashboard/gates
2. **Check UI Groups**:
   - Main Gate Control (with switch)
   - Gate Status (power display)
   - Relay Status (relays 1-4, mains, keypad)
   - Debug & Messages

3. **Test Control**:
   - Toggle "Deschide Poarta" switch
   - Check MQTT traffic: `mosquitto_sub -h 192.168.2.4 -t 'MainGate/#' -v`

## Usage

### Opening/Closing the Gate

**From Dashboard:**
1. Navigate to http://localhost:1880/dashboard/gates
2. Click the "Deschide Poarta" switch
3. Switch toggles ON for 1 second (pulse)
4. Gate controller receives command
5. Status updates automatically

**MQTT Command (manual):**
```bash
mosquitto_pub -h 192.168.2.4 -t "MainGate/CMD/Relay3" -m "ON"
```

### Monitoring Status

**Power Status:**
- Displays current power mode (Battery/Mains)
- Sends SMS alert on changes
- Updates in real-time

**Relay Status:**
- Shows ON/OFF state for all 4 relays
- Updates every few seconds (based on controller)

**Mains Power:**
- Indicates AC power availability
- Critical for backup power monitoring

**Keypad:**
- Shows keypad connectivity status
- Helps diagnose communication issues

### SMS Notifications

**When Triggered:**
- Power status changes (battery ↔ mains)
- Only on actual changes (RBE filtering)

**Message Format:**
```
Poarta principala - Status alimentare: [BATTERY/MAINS]
```

**Recipient:**
- Default: 0740244845
- Configurable via global.set("number", "0740244845")

## Configuration

### MQTT Broker

Default broker: `192.168.2.4:1883`

**To Change:**
1. Open any flow file
2. Find `mqtt_broker_local` node
3. Edit broker configuration:
   ```json
   {
       "broker": "YOUR_BROKER_IP",
       "port": "1883"
   }
   ```
4. Deploy

### SMS Number

**Method 1: Global Context**
```javascript
// In Node-RED function node or console
global.set("number", "0740244845");
```

**Method 2: Edit Function Node**
Edit `gate_status_sms_number` function:
```javascript
var smsNumber = "YOUR_PHONE_NUMBER";
msg.payload = smsNumber;
return msg;
```

### UI Customization

**Change Switch Labels:**
Edit `gate_main_switch` node properties:
- `label`: "Deschide Poarta" → "Open Main Gate"
- `onicon`: "lock_open"
- `officon`: "lock"

**Change Colors:**
```json
{
    "oncolor": "green",
    "offcolor": "grey"
}
```

## Troubleshooting

### Issue: Switch Doesn't Control Gate

**Check:**
1. MQTT broker connectivity
   ```bash
   mosquitto_sub -h 192.168.2.4 -t 'MainGate/CMD/#' -v
   ```
2. Gate controller subscribed to `MainGate/CMD/Relay3`
3. Check Node-RED debug panel for errors
4. Verify trigger node sends 1-second pulse

**Solution:**
- Check MQTT broker logs
- Restart gate controller
- Test with direct MQTT publish

### Issue: Status Not Updating

**Check:**
1. Gate controller publishing status
   ```bash
   mosquitto_sub -h 192.168.2.4 -t 'MainGate/STAT/#' -v
   ```
2. MQTT topics match exactly
3. QoS level compatibility

**Solution:**
- Verify topic names (case-sensitive)
- Check QoS settings (currently QoS 2)
- Restart Node-RED

### Issue: SMS Not Sending

**Check:**
1. esp32SMS device online
2. MQTT topics correct
3. SMS gateway operational
4. Phone number format

**Solution:**
- Test SMS gateway manually
- Check SMS device logs
- Verify phone number includes country code if needed

### Issue: No Timestamp Updates

**Check:**
1. Status messages received
2. Timestamp function node working
3. UI group visible

**Solution:**
- Check function node for errors
- Verify date formatting
- Restart Node-RED if needed

## Advanced Features

### Command History

All commands are logged to flow context:

```javascript
// Retrieve last command
let lastCommand = flow.get('lastCommand');

// Retrieve command history (last 10)
let history = flow.get('commandHistory');
```

**Example:**
```json
{
    "action": "relay2_toggle",
    "value": "ON",
    "timestamp": "2026-01-17T10:00:00.000Z",
    "request_id": "gate-relay2-1737108000000"
}
```

### State Management

Gate state stored in context:

```javascript
{
    "initialized": true,
    "timestamp": "2026-01-17T10:00:00.000Z",
    "mainGate": {
        "relay1": "OFF",
        "relay2": "ON",
        "relay3": "OFF",
        "relay4": "OFF",
        "power": "MAINS",
        "mains": "ON",
        "keypad": "CONNECTED",
        "lastUpdate": "2026-01-17T10:05:00.000Z"
    },
    "lastCommand": {...},
    "commandHistory": [...]
}
```

### Adding More Gates

To add pedestrian gate or garage door:

1. Copy control flow:
   ```bash
   cp 210-main-gate-controls.json 220-pedestrian-gate-controls.json
   ```

2. Edit and replace:
   - Topic: `MainGate` → `PedestrianGate`
   - UI group reference
   - Labels and names

3. Import and deploy

## Security Considerations

### Access Control

**Dashboard Authentication:**
Enable in Node-RED settings.js:
```javascript
adminAuth: {
    type: "credentials",
    users: [{
        username: "admin",
        password: "$2b$08$...",
        permissions: "*"
    }]
}
```

**MQTT Authentication:**
Configure broker with username/password:
```
allow_anonymous false
password_file /etc/mosquitto/passwd
```

### Network Security

1. **Firewall**: Restrict MQTT port (1883) to local network
2. **VPN**: Use VPN for remote access
3. **TLS**: Enable MQTT over TLS (port 8883)

## Maintenance

### Regular Checks

- [ ] Gate controller online and responsive
- [ ] MQTT broker running
- [ ] SMS gateway operational
- [ ] Status updates received
- [ ] Command execution working

### Logs

**Node-RED Logs:**
```bash
journalctl -u nodered -f
```

**MQTT Traffic:**
```bash
mosquitto_sub -h 192.168.2.4 -t '#' -v
```

### Backup

Export flows regularly:
```
Menu → Export → All Flows → Clipboard
Save to: backups/gate-flows-YYYY-MM-DD.json
```

## Related Documentation

- [Automation Architecture](AUTOMATION_ARCHITECTURE.md)
- [Integration Guide](AUTOMATION_INTEGRATION_GUIDE.md)
- [Quick Start](QUICK_START_NEW_AUTOMATION.md)
- [MQTT Protocol](MQTT_PROTOCOL.md)

## Support

For issues or questions:
1. Check Node-RED debug panel
2. Monitor MQTT topics
3. Review error logs
4. Test with manual MQTT commands

---

**Version**: 1.0.0  
**Last Updated**: 2026-01-17  
**Domain**: Gate Automation (200-299)
