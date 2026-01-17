# Tasmota Gate Controller Integration

## Overview

The main gate automation uses a [Tasmota](https://tasmota.github.io/docs/) device as the gate controller. Tasmota is open-source firmware for ESP8266/ESP32 devices that provides MQTT control, web UI, and extensive customization options.

## Device Configuration

### Current MQTT Topics

Your Tasmota device is configured with custom topics:

**Commands (Node-RED → Tasmota):**
```
MainGate/CMD/Relay2
```

**Status (Tasmota → Node-RED):**
```
MainGate/STAT/Relay2                    # Relay 2 state
MainGate/STAT/eventPower                # Power status events
MainGate/STAT/reccurentStatusRelay1     # Relay 1 recurring status
MainGate/STAT/reccurentStatusRelay2     # Relay 2 recurring status
MainGate/STAT/reccurentStatusRelay3     # Relay 3 recurring status
MainGate/STAT/reccurentStatusRelay4     # Relay 4 recurring status
MainGate/STAT/reccurentStatusMains      # Mains power status
MainGate/STAT/reccurentStatusKeypad     # Keypad connectivity
MainGate/STAT/message                   # Debug messages
```

## Tasmota Configuration

### Basic Settings

**MQTT Configuration (Web UI):**
1. Navigate to Tasmota Web UI: http://[DEVICE_IP]
2. Configuration → Configure MQTT
3. Set MQTT parameters:
   ```
   Host: 192.168.2.4
   Port: 1883
   Client: MainGate
   Topic: MainGate
   Full Topic: %prefix%/%topic%/
   ```

### Custom Topic Structure

Your device uses custom topic prefixes. To configure:

**Via Console:**
```
Topic MainGate
FullTopic %prefix%/%topic%/
```

This creates the structure:
- `CMD/MainGate/` for commands
- `STAT/MainGate/` for status

### Relay Configuration

**Configure 4 Relays:**

Via Console:
```
# Enable relays
Backlog Module 18; GPIO4 Relay1; GPIO5 Relay2; GPIO12 Relay3; GPIO13 Relay4

# Set relay names
WebButton1 Gate Relay 1
WebButton2 Main Gate Open
WebButton3 Gate Relay 3
WebButton4 Gate Relay 4

# Configure relay modes
PowerOnState 0    # Keep relays off on power-up
PulseTime1 0      # No pulse for Relay 1
PulseTime2 10     # 1-second pulse for Relay 2 (gate control)
PulseTime3 0      # No pulse for Relay 3
PulseTime4 0      # No pulse for Relay 4
```

### Power Monitoring

If your Tasmota device has power monitoring:

**Enable Power Monitoring:**
```
# Configure power monitoring
VoltageSet 230.0
CurrentSet 1000
PowerSet 230000

# Set telemetry period (seconds)
TelePeriod 300

# Enable power change reporting
SetOption21 1
```

**Power Status Topic:**
```
tele/MainGate/SENSOR
{
    "Time": "2026-01-17T10:00:00",
    "ENERGY": {
        "Power": 150,
        "ApparentPower": 160,
        "Voltage": 230,
        "Current": 0.65
    }
}
```

### Status Reporting

**Configure Regular Status Updates:**

Via Console:
```
# Status update interval (seconds)
TelePeriod 30

# Enable status on state change
SetOption0 1

# Enable MQTT retained messages for POWER
PowerRetain 1

# Status format
StateText1 OFF
StateText2 ON
```

## Tasmota Rules for Custom Status

To generate the custom status topics used in your automation, add Tasmota rules:

### Rule 1: Relay Status Publishing

```
Rule1
  ON Power1#State DO Publish STAT/MainGate/reccurentStatusRelay1 %value% ENDON
  ON Power2#State DO Publish STAT/MainGate/reccurentStatusRelay2 %value% ENDON
  ON Power3#State DO Publish STAT/MainGate/reccurentStatusRelay3 %value% ENDON
  ON Power4#State DO Publish STAT/MainGate/reccurentStatusRelay4 %value% ENDON

Rule1 1
```

### Rule 2: Power Status Events

```
Rule2
  ON Power#State DO Publish STAT/MainGate/eventPower %value% ENDON
  ON Wifi#Connected DO Publish STAT/MainGate/message WiFi Connected ENDON
  ON Mqtt#Connected DO Publish STAT/MainGate/message MQTT Connected ENDON

Rule2 1
```

### Rule 3: Mains and System Status

```
Rule3
  ON System#Boot DO Publish STAT/MainGate/message System Booted ENDON
  ON Time#Minute|5 DO Backlog Publish STAT/MainGate/reccurentStatusMains ONLINE; Publish STAT/MainGate/reccurentStatusKeypad CONNECTED ENDON

Rule3 1
```

**Enable Rules:**
```
Rule1 1
Rule2 1
Rule3 1
```

## Advanced Features

### Timers for Automated Opening

**Set up timers in Tasmota:**

```
# Open gate at 7:00 AM on weekdays
Timer1 {"Enable":1,"Mode":0,"Time":"07:00","Window":0,"Days":"1111100","Repeat":1,"Output":2,"Action":1}

# Close gate at 10:00 PM daily
Timer2 {"Enable":1,"Mode":0,"Time":"22:00","Window":0,"Days":"1111111","Repeat":1,"Output":2,"Action":0}
```

**Via Web UI:**
1. Configuration → Configure Timer
2. Set up timers for automatic operation

### Interlock for Safety

Prevent multiple relays from activating simultaneously:

```
# Interlock relays 1 and 2
Interlock 1,2

# Set interlock mode
SetOption73 1
```

### Watchdog Timer

Automatic recovery if device becomes unresponsive:

```
# Enable watchdog
WdgTime 60

# Reset if no MQTT communication
SetOption31 1
```

### Button/Switch Integration

If you have physical buttons connected:

```
# Configure GPIO for buttons
GPIO14 Button1
GPIO16 Button2

# Button mode (toggle)
SetOption13 0

# Button hold time (seconds)
SetOption32 40
```

## Web UI Integration

### Access Tasmota Dashboard

**Direct Access:**
```
http://[DEVICE_IP]
```

**Control Relays:**
- Toggle buttons in web UI
- View real-time status
- Access console for commands

### Firmware Updates

**Update via Web UI:**
1. Configuration → Firmware Upgrade
2. Enter OTA URL or upload file
3. Start upgrade

**OTA Update URL:**
```
http://ota.tasmota.com/tasmota/release/tasmota.bin.gz
```

## Troubleshooting

### MQTT Connection Issues

**Check Configuration:**
```
# View MQTT settings
MqttHost
MqttPort
MqttUser
Topic
FullTopic
```

**Test MQTT:**
```
# Publish test message
Publish test/topic Test Message
```

**Check Connection:**
```
Status 6
```

### Relay Not Responding

**Check Relay Status:**
```
Power1
Power2
Power3
Power4
```

**Check GPIO Configuration:**
```
GPIO
```

**Test Relay Directly:**
```
Power2 Toggle
```

### Debug Mode

**Enable Debug Logging:**
```
# Enable web logging
WebLog 4

# Enable serial logging
SerialLog 4

# View logs in web console
```

## Integration with Node-RED

### Enhanced Control Flow

You can add more sophisticated Tasmota controls:

**Read Sensor Data:**
```javascript
// Subscribe to telemetry
topic: tele/MainGate/SENSOR

// Parse JSON
const data = JSON.parse(msg.payload);
const power = data.ENERGY.Power;
const voltage = data.ENERGY.Voltage;
```

**Send Complex Commands:**
```javascript
// Backlog command (multiple commands)
msg.payload = "Backlog Power2 ON; Delay 10; Power2 OFF";
msg.topic = "cmnd/MainGate/Backlog";
```

**Status Queries:**
```javascript
// Request status
msg.payload = "";
msg.topic = "cmnd/MainGate/Status";
// Response: stat/MainGate/STATUS
```

## Security Best Practices

### MQTT Authentication

**Configure Credentials:**
```
# Set MQTT username/password
MqttUser your_username
MqttPassword your_password
```

### Web UI Password

**Protect Web Interface:**
```
WebPassword your_secure_password
```

### Disable Unnecessary Features

```
# Disable web server (if only using MQTT)
WebServer 0

# Disable AP mode after setup
SetOption55 1
```

### Firmware Updates

Keep Tasmota updated for security patches:
```
# Check current version
Status 2

# Update to latest
OtaUrl http://ota.tasmota.com/tasmota/release/tasmota.bin.gz
Upgrade 1
```

## Monitoring and Maintenance

### Health Check

**Create Status Check Flow in Node-RED:**

```javascript
// Check if device is online
// Subscribe to: tele/MainGate/LWT
// Payload: Online/Offline

if (msg.payload === "Offline") {
    // Send alert
    msg.alert = "Main Gate controller offline!";
}
```

### Uptime Monitoring

**Subscribe to Status:**
```
tele/MainGate/STATE
{
    "Time": "2026-01-17T10:00:00",
    "Uptime": "5T02:30:15",
    "Wifi": {
        "RSSI": -62,
        "Signal": 76
    }
}
```

### Log Rotation

Tasmota logs are in memory only. For persistent logs:

**Forward to Node-RED:**
```
Rule
  ON System#Boot DO Publish logs/MainGate Boot_%timestamp% ENDON
  ON Mqtt#Connected DO Publish logs/MainGate MQTT_Connected ENDON
```

## Useful Tasmota Commands

### Information Commands

```
Status        # Basic status
Status 0      # All status
Status 1      # Device parameters
Status 2      # Firmware version
Status 5      # Network info
Status 6      # MQTT info
Status 11     # Device state
```

### Control Commands

```
Power<x> ON|OFF|TOGGLE    # Control relay
PowerOnState <0-5>        # Power-on behavior
PulseTime<x> <time>       # Pulse duration
Blink<x> <count>          # Blink relay
BlinkTime <time>          # Blink duration
```

### Configuration Commands

```
Backlog       # Execute multiple commands
Restart 1     # Restart device
Reset 1       # Reset to defaults
SetOption<x>  # Set option flag
Module        # Show/set module type
GPIO          # Show GPIO configuration
```

## Resources

- **Tasmota Documentation**: https://tasmota.github.io/docs/
- **Commands Reference**: https://tasmota.github.io/docs/Commands/
- **MQTT Guide**: https://tasmota.github.io/docs/MQTT/
- **Rules**: https://tasmota.github.io/docs/Rules/
- **Device Templates**: https://templates.blakadder.com/

## Support

### Tasmota Community

- **Discord**: https://discord.gg/Ks2Kzd4
- **GitHub**: https://github.com/arendst/Tasmota
- **Support Chat**: https://discord.gg/Ks2Kzd4

### Debugging

**Console Access:**
1. Web UI → Console
2. Enter commands
3. View real-time output

**Serial Console:**
```
Speed: 115200 baud
Tool: PuTTY, Arduino Serial Monitor
```

---

**Version**: 1.0.0  
**Last Updated**: 2026-01-17  
**Tasmota Version**: Compatible with v15.2.0+
