# SMS Gateway Device

Embedded SMS gateway device using ESP32 with SIM800 module, integrated with the ServerBootShutdownManagement automation platform.

## Overview

This device provides SMS send/receive capabilities through MQTT, allowing the automation platform to send and receive SMS messages for alerts, notifications, and remote control.

**Hardware:** LilyGo T-Call SIM800  
**Framework:** PlatformIO with Arduino  
**Communication:** MQTT over WiFi (or GPRS)

## Features

- ✅ **Send SMS** via MQTT commands
- ✅ **Receive SMS** and publish to MQTT
- ✅ **MQTT Integration** with project's topic structure
- ✅ **Timestamp Support** via NTP
- ✅ **WiFi or GPRS** connectivity options
- ✅ **Status Monitoring** via MQTT
- ✅ **Self-Recovery** - Automatic reconnection for WiFi and MQTT
- ✅ **Reset Detection** - Announces device resets via MQTT and SMS
- ✅ **Emergency SMS Alerts** - Sends SMS when WiFi/MQTT fails
- ✅ **Watchdog Timer** - Prevents system hangs
- ✅ **Robust Error Handling** - Handles connection failures gracefully

## Hardware Requirements

- **LilyGo T-Call SIM800** development board
  - ESP32 microcontroller
  - SIM800 GSM/GPRS module
  - IP5306 power management
  - BME280 sensor (optional)
- **SIM Card** with SMS capability
- **Micro USB cable** for programming and power

## Installation

### 1. Prerequisites

- [PlatformIO](https://platformio.org/) installed (VS Code extension recommended)
- USB drivers for ESP32
- Active SIM card with SMS capability

### 2. Clone and Setup

```bash
cd device/sms-gateway
```

### 3. Configuration

1. **Copy configuration template:**
   ```bash
   cp include/passwords.h.example include/passwords.h
   ```

2. **Edit `include/passwords.h`** with your settings:
   ```cpp
   // WiFi credentials (if using WiFi)
   const char* ssid = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";

   // MQTT Broker
   const char* mqtt_server = "192.168.1.100";
   const int mqtt_port = 1883;
   const char* mqtt_username = "your_username";
   const char* mqtt_password = "your_password";

   // MQTT Client ID
   const char* mqtt_client_id = "esp32-sms-gateway";

   // GPRS/APN (if using GPRS)
   const char apn[] = "net";
   const char user[] = "";
   const char pass[] = "";
   
   // Emergency SMS notification (optional)
   // Phone number to receive alerts when WiFi/MQTT fails
   #define EMERGENCY_PHONE_NUMBER "+1234567890"  // Include country code
   
   // OTA (Over-The-Air) update password (optional but recommended)
   #define OTA_PASSWORD "your_ota_password"  // Leave empty to disable password
   ```

3. **Configure YAML** (optional, for reference):
   ```bash
   cp config/.env.example config/.env
   # Edit config/.env with your values
   ```

### 4. Build and Upload

```bash
# Build the project
pio run

# Upload to device
pio run --target upload

# Monitor serial output
pio device monitor
```

## MQTT Topic Structure

The device follows the project's MQTT topic convention: `{domain}/{location}/{device}/{type}/{action}`

### Command Topics (Subscribe)

| Topic | Direction | Description |
|-------|-----------|-------------|
| `sms/gateway/command/send` | Dashboard → Device | Send SMS command |

**Send SMS Command Format:**
```json
{
  "to": "+1234567890",
  "text": "Hello from automation!"
}
```

### Status Topics (Publish)

| Topic | Direction | Description |
|-------|-----------|-------------|
| `sms/gateway/status` | Device → Dashboard | Device status timestamp |
| `sms/gateway/status/timestamp` | Device → Dashboard | Last status update |

### Receive Topics (Publish)

| Topic | Direction | Description |
|-------|-----------|-------------|
| `sms/gateway/receive/from` | Device → Dashboard | Phone number of received SMS |
| `sms/gateway/receive/text` | Device → Dashboard | Text content of received SMS |
| `sms/gateway/receive/timestamp` | Device → Dashboard | Timestamp when SMS was received |

### Send Topics (Publish)

| Topic | Direction | Description |
|-------|-----------|-------------|
| `sms/gateway/send/response` | Device → Dashboard | Send operation result |
| `sms/gateway/send/timestamp` | Device → Dashboard | Timestamp when SMS was sent |
| `sms/gateway/reset` | Device → Dashboard | Device reset announcement |
| `sms/gateway/error` | Device → Dashboard | Error notifications |
| `sms/gateway/command/ota` | Dashboard → Device | OTA enable/disable command |
| `sms/gateway/ota/status` | Device → Dashboard | OTA update status |
| `sms/gateway/ota/progress` | Device → Dashboard | OTA update progress |

**Send Response Format:**
```json
{
  "success": true,
  "to": "+1234567890",
  "timestamp": "2026-01-25T17:00:00+00:00"
}
```

## Usage Examples

### Send SMS via MQTT

```bash
# Using mosquitto_pub
mosquitto_pub -h 192.168.1.100 \
  -t "sms/gateway/command/send" \
  -m '{"to": "+1234567890", "text": "Server is online!"}'
```

### Monitor Received SMS

```bash
# Monitor received SMS messages
mosquitto_sub -h 192.168.1.100 -t "sms/gateway/receive/+" -v
```

### Check Device Status

```bash
# Monitor device status
mosquitto_sub -h 192.168.1.100 -t "sms/gateway/status" -v
```

## Integration with Automation Platform

The SMS gateway integrates with the automation platform's SMS/Notification domain (500-599):

- **Domain:** SMS/Notifications (500-599)
- **Device:** SMS Gateway (510-519)
- **Node-RED Flows:** Can be added to `nodered/flows/510-sms-gateway-controls.json`

### Example Node-RED Integration

Create a Node-RED flow to send SMS from automation:

```json
{
  "id": "sms_send_flow",
  "type": "mqtt out",
  "topic": "sms/gateway/command/send",
  "qos": 1,
  "payload": "{\"to\": \"{{msg.phone}}\", \"text\": \"{{msg.message}}\"}"
}
```

## Configuration Files

- **`include/passwords.h`** - WiFi, MQTT, and GPRS credentials (not in git)
- **`include/config.h`** - Hardware pins, MQTT topics, timing (in git)
- **`config/sms_gateway_config.yaml`** - YAML configuration reference
- **`config/.env.example`** - Environment variables template

## Self-Recovery Features

The device includes robust self-recovery mechanisms:

### Automatic Reconnection
- **WiFi**: Automatically reconnects with up to 3 attempts
- **MQTT**: Automatically reconnects with up to 5 attempts
- **GSM**: Modem is reinitialized on startup

### Reset Detection
- Device tracks boot count using RTC memory
- Announces resets via MQTT (`sms/gateway/reset`)
- Sends SMS notification if MQTT unavailable (if emergency number configured)

### Emergency SMS Alerts
When WiFi or MQTT fails, the device can send SMS alerts:
- Configure `EMERGENCY_PHONE_NUMBER` in `include/passwords.h`
- Alerts sent when:
  - WiFi connection fails on boot
  - WiFi reconnection attempts exhausted
  - MQTT connection attempts exhausted
  - Device resets (if MQTT unavailable)

### Watchdog Timer
- 60-second watchdog timer prevents system hangs
- Automatic reset if main loop stops responding

### OTA (Over-The-Air) Updates
The device supports OTA firmware updates via WiFi:

**Features:**
- **ArduinoOTA Integration** - Standard ESP32 OTA protocol
- **MQTT Control** - Enable/disable OTA via MQTT commands
- **Progress Tracking** - Real-time update progress via MQTT
- **SMS Notifications** - Alerts sent when OTA starts/completes/fails
- **Password Protection** - Optional password to secure OTA updates

**Usage:**

1. **Enable OTA via MQTT:**
   ```bash
   mosquitto_pub -h 192.168.1.100 \
     -t "sms/gateway/command/ota" \
     -m '{"action": "enable"}'
   ```

2. **Upload firmware via PlatformIO:**
   ```bash
   pio run --target upload --upload-port <device_ip>
   ```

3. **Or use Arduino IDE:**
   - Tools → Port → Select device IP address
   - Sketch → Upload

4. **Monitor OTA progress:**
   ```bash
   mosquitto_sub -h 192.168.1.100 -t "sms/gateway/ota/+" -v
   ```

**OTA Command Format:**
```json
{
  "action": "enable|disable"
}
```

**OTA Status Messages:**
- `started` - OTA update started
- `progress` - Update progress (0-100%)
- `completed` - Update completed successfully
- `error` - Update failed with error details

**Security:**
- Set `OTA_PASSWORD` in `include/passwords.h` to require password for updates
- OTA is automatically disabled if WiFi disconnects
- OTA can be enabled/disabled via MQTT commands

## Troubleshooting

### Device Not Connecting to MQTT

1. Check WiFi credentials in `include/passwords.h`
2. Verify MQTT broker is accessible
3. Check serial monitor for connection errors
4. Verify MQTT username/password are correct
5. Device will automatically retry - check serial monitor for retry attempts

### SMS Not Sending

1. Verify SIM card is active and has credit
2. Check signal strength (should be visible in serial monitor)
3. Verify phone number format includes country code (e.g., +1234567890)
4. Check serial monitor for AT command errors

### SMS Not Receiving

1. Verify SIM card supports SMS reception
2. Check that SMS buffer is being read (see serial monitor)
3. Ensure device is powered and connected to network

### Serial Monitor Debugging

Enable AT command debugging by uncommenting in `src/main.cpp`:
```cpp
#define DUMP_AT_COMMANDS
```

## Hardware Pin Reference

| Pin | Function | Description |
|-----|----------|-------------|
| 5 | MODEM_RST | SIM800 reset & IP5306 IRQ |
| 4 | MODEM_PWKEY | SIM800 power key |
| 23 | MODEM_POWER_ON | SY8089 4V4 regulator enable |
| 27 | MODEM_TX | SIM800 TX (to ESP32 RX) |
| 26 | MODEM_RX | SIM800 RX (from ESP32 TX) |
| 35 | ADC_BAT | Battery voltage ADC |

## Library Dependencies

- **TinyGSM** - GSM/GPRS communication
- **PubSubClient** - MQTT client
- **ArduinoJson** - JSON parsing
- **SparkFun BME280** - Environmental sensor (optional)

## Development

### Project Structure

```
device/sms-gateway/
├── src/
│   └── main.cpp              # Main application code
├── include/
│   ├── config.h              # Configuration constants
│   ├── passwords.h.example   # Credentials template
│   └── passwords.h           # Your credentials (not in git)
├── config/
│   ├── sms_gateway_config.yaml # YAML config reference
│   └── .env.example          # Environment variables template
├── platformio.ini            # PlatformIO configuration
├── .gitignore                # Git ignore rules
└── README.md                 # This file
```

### Building

```bash
# Build for LilyGo T-Call
pio run -e lilygo-t-call

# Build for generic ESP32
pio run -e esp32dev

# Clean build
pio run --target clean
```

### Uploading

**Serial Upload (Initial Setup):**
```bash
# Upload to device via USB
pio run --target upload

# Upload and monitor
pio run --target upload && pio device monitor
```

**OTA Upload (After Initial Setup):**
```bash
# 1. Enable OTA via MQTT
mosquitto_pub -h 192.168.1.100 \
  -t "sms/gateway/command/ota" \
  -m '{"action": "enable"}'

# 2. Upload via OTA (replace <device_ip> with actual IP)
pio run --target upload --upload-port <device_ip>

# Example:
pio run --target upload --upload-port 192.168.1.50
```

**Find Device IP:**
- Check serial monitor on boot
- Check MQTT status topic: `sms/gateway/status`
- Check your router's DHCP client list

## License

Part of the ServerBootShutdownManagement project. See main project LICENSE file.

## References

- [LilyGo T-Call SIM800](https://github.com/Xinyuan-LilyGO/LilyGo-T-Call-SIM800)
- [TinyGSM Library](https://github.com/vshymanskyy/TinyGSM)
- [PlatformIO Documentation](https://docs.platformio.org/)
- [Project MQTT Protocol](../docs/MQTT_PROTOCOL.md)
- [OTA Developer Guide](../docs/developer/OTA_DEVICE_UPDATES.md) - Complete OTA development guide

## Support

For issues and questions:
- Check [Troubleshooting](#troubleshooting) section
- See main project [Troubleshooting Guide](../docs/TROUBLESHOOTING.md)
- Review [MQTT Protocol Documentation](../docs/MQTT_PROTOCOL.md)
