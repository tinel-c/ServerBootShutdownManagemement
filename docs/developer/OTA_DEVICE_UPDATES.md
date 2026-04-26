# OTA Device Updates - Developer Guide

This guide explains how to develop, test, and deploy Over-The-Air (OTA) firmware updates for embedded devices in the ServerBootShutdownManagement project.

## 📋 Table of Contents

- [Overview](#overview)
- [OTA Architecture](#ota-architecture)
- [Development Workflow](#development-workflow)
- [Testing OTA Updates](#testing-ota-updates)
- [Deployment Process](#deployment-process)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)
- [Security Considerations](#security-considerations)
- [CI/CD Integration](#cicd-integration)

---

## Overview

### What is OTA?

Over-The-Air (OTA) updates allow firmware to be updated remotely without physical access to the device. This is essential for:
- **Remote maintenance** - Update devices in the field
- **Bug fixes** - Deploy fixes without service interruption
- **Feature updates** - Add new capabilities remotely
- **Security patches** - Apply security updates quickly

### Supported Devices

Currently supported devices:
- **SMS Gateway** (ESP32 with SIM800) - `device/esp32-sms-gateway/`

### OTA Technology Stack

- **Protocol**: ArduinoOTA (ESP32 native OTA)
- **Transport**: WiFi (requires active WiFi connection)
- **Port**: 3232 (default, configurable)
- **Authentication**: Optional password protection
- **Control**: MQTT commands for enable/disable
- **Monitoring**: MQTT topics for status and progress

---

## OTA Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Developer Machine                    │
│  ┌──────────────┐         ┌──────────────┐              │
│  │ PlatformIO   │────────▶│  OTA Upload  │              │
│  │   Build      │         │   Tool       │              │
│  └──────────────┘         └──────┬───────┘              │
└──────────────────────────────────┼──────────────────────┘
                                   │ WiFi (Port 3232)
                                   ▼
┌─────────────────────────────────────────────────────────┐
│                    ESP32 Device                        │
│  ┌──────────────┐         ┌──────────────┐              │
│  │  ArduinoOTA  │◀────────│  WiFi Stack  │              │
│  │   Handler    │         │              │              │
│  └──────┬───────┘         └──────────────┘              │
│         │                                                 │
│         ▼                                                 │
│  ┌──────────────┐         ┌──────────────┐              │
│  │   Flash      │         │   MQTT       │              │
│  │   Memory     │         │  Publisher   │              │
│  └──────────────┘         └──────────────┘              │
└─────────────────────────────────────────────────────────┘
```

### MQTT Topics

| Topic | Direction | Purpose |
|-------|-----------|---------|
| `sms/gateway/command/ota` | Dashboard → Device | Enable/disable OTA |
| `sms/gateway/ota/status` | Device → Dashboard | Update status (started/completed/error) |
| `sms/gateway/ota/progress` | Device → Dashboard | Progress updates (0-100%) |

### OTA States

1. **Disabled** - OTA not available (default if WiFi disconnected)
2. **Enabled** - OTA ready to accept updates
3. **In Progress** - Update being received/flashed
4. **Completed** - Update finished, device will reboot
5. **Error** - Update failed, device remains operational

---

## Development Workflow

### 1. Initial Setup

#### Enable OTA in Code

OTA is automatically enabled when:
- WiFi is connected
- Device is initialized
- OTA library is included

**Check in `src/main.cpp`:**
```cpp
#ifdef OTA_ENABLED
#include <ArduinoOTA.h>
// ... OTA setup code
#endif
```

#### Configure OTA Settings

**In `include/config.h`:**
```cpp
#define OTA_PORT 3232
#define OTA_HOSTNAME "esp32-sms-gateway"
```

**In `include/passwords.h`:**
```cpp
#define OTA_PASSWORD "your_secure_password"  // Optional but recommended
```

### 2. Development Cycle

#### Step 1: Build Firmware

```bash
cd device/esp32-sms-gateway

# Build for target device
pio run -e lilygo-t-call

# Or for generic ESP32
pio run -e esp32dev
```

#### Step 2: Initial Flash (USB)

**First time setup requires USB:**
```bash
# Connect device via USB
pio run --target upload

# Monitor output
pio device monitor
```

#### Step 3: Enable OTA on Device

**Via MQTT:**
```bash
mosquitto_pub -h <mqtt_broker> \
  -t "sms/gateway/command/ota" \
  -m '{"action": "enable"}'
```

**Or via Serial Monitor:**
- Check device IP address from serial output
- OTA is automatically enabled when WiFi connects

#### Step 4: Subsequent Updates (OTA)

```bash
# Get device IP (from serial monitor or MQTT status)
DEVICE_IP="192.168.1.50"

# Upload via OTA
pio run --target upload --upload-port $DEVICE_IP
```

### 3. Version Management

#### Add Version Information

**In `src/main.cpp`:**
```cpp
#define FIRMWARE_VERSION "1.0.0"
#define FIRMWARE_BUILD_DATE __DATE__ " " __TIME__

void setup() {
    Serial.print("Firmware Version: ");
    Serial.println(FIRMWARE_VERSION);
    Serial.print("Build Date: ");
    Serial.println(FIRMWARE_BUILD_DATE);
}
```

#### Publish Version to MQTT

```cpp
if (mqttConnected) {
    StaticJsonDocument<128> version;
    version["version"] = FIRMWARE_VERSION;
    version["build_date"] = FIRMWARE_BUILD_DATE;
    version["device_id"] = mqtt_client_id;
    
    char buffer[128];
    serializeJson(version, buffer);
    mqttClient.publish("sms/gateway/version", buffer);
}
```

---

## Testing OTA Updates

### 1. Local Testing

#### Test Environment Setup

```bash
# Terminal 1: Monitor device serial output
cd device/esp32-sms-gateway
pio device monitor

# Terminal 2: Monitor MQTT OTA topics
mosquitto_sub -h <mqtt_broker> -t "sms/gateway/ota/+" -v

# Terminal 3: Build and upload
pio run --target upload --upload-port <device_ip>
```

#### Test Scenarios

**Scenario 1: Successful Update**
1. Enable OTA via MQTT
2. Build new firmware
3. Upload via OTA
4. Verify progress messages
5. Verify device reboots with new firmware
6. Check version in serial output

**Scenario 2: Failed Update (Network Interruption)**
1. Start OTA update
2. Disconnect WiFi mid-update
3. Verify error message published to MQTT
4. Verify device remains operational
5. Verify old firmware still running

**Scenario 3: Invalid Firmware**
1. Try uploading incompatible firmware
2. Verify error handling
3. Verify device recovery

### 2. Production Testing

#### Pre-Deployment Checklist

- [ ] Firmware version incremented
- [ ] All tests pass locally
- [ ] OTA password configured (if using)
- [ ] MQTT broker accessible
- [ ] Device WiFi connected
- [ ] Backup plan ready (USB flash if needed)

#### Staged Rollout

**Phase 1: Single Device**
```bash
# Test on one device first
DEVICE_IP="192.168.1.50"
pio run --target upload --upload-port $DEVICE_IP

# Monitor for 24 hours
mosquitto_sub -h <mqtt_broker> -t "sms/gateway/+" -v
```

**Phase 2: Small Batch (10%)**
- Update 10% of devices
- Monitor for issues
- Check error rates

**Phase 3: Full Rollout**
- Update remaining devices
- Monitor all devices

### 3. Automated Testing

#### Test Script Example

```bash
#!/bin/bash
# test_ota.sh

DEVICE_IP=$1
MQTT_BROKER=$2

echo "Testing OTA update on $DEVICE_IP"

# 1. Enable OTA
mosquitto_pub -h $MQTT_BROKER \
  -t "sms/gateway/command/ota" \
  -m '{"action": "enable"}'

sleep 2

# 2. Upload firmware
pio run --target upload --upload-port $DEVICE_IP

# 3. Wait for completion
sleep 10

# 4. Verify version
# (Check MQTT or serial output)
```

---

## Deployment Process

### 1. Pre-Deployment

#### Build Release Firmware

```bash
cd device/esp32-sms-gateway

# Clean previous builds
pio run --target clean

# Build release version
pio run -e lilygo-t-call

# Verify build
ls -lh .pio/build/lilygo-t-call/firmware.bin
```

#### Prepare Deployment Script

```bash
#!/bin/bash
# deploy_ota.sh

# Configuration
MQTT_BROKER="192.168.1.100"
DEVICE_IPS=(
    "192.168.1.50"
    "192.168.1.51"
    "192.168.1.52"
)

FIRMWARE_VERSION="1.0.1"

echo "Deploying firmware version $FIRMWARE_VERSION"

for DEVICE_IP in "${DEVICE_IPS[@]}"; do
    echo "Updating device at $DEVICE_IP..."
    
    # Enable OTA
    mosquitto_pub -h $MQTT_BROKER \
        -t "sms/gateway/command/ota" \
        -m '{"action": "enable"}' \
        -q 1
    
    sleep 2
    
    # Upload firmware
    pio run --target upload --upload-port $DEVICE_IP
    
    if [ $? -eq 0 ]; then
        echo "✓ Successfully updated $DEVICE_IP"
    else
        echo "✗ Failed to update $DEVICE_IP"
    fi
    
    sleep 5  # Wait between devices
done
```

### 2. Deployment Execution

#### Manual Deployment

```bash
# Single device
./deploy_ota.sh 192.168.1.50

# Multiple devices
for ip in 192.168.1.{50..60}; do
    ./deploy_ota.sh $ip
done
```

#### Automated Deployment

```bash
# Use deployment script
chmod +x deploy_ota.sh
./deploy_ota.sh
```

### 3. Post-Deployment

#### Verification

**Check Device Status:**
```bash
# Monitor all devices
mosquitto_sub -h <mqtt_broker> \
  -t "sms/gateway/status" \
  -t "sms/gateway/version" \
  -v
```

**Verify Firmware Version:**
```bash
# Check version on each device
for ip in 192.168.1.{50..60}; do
    echo "Checking $ip..."
    mosquitto_pub -h <mqtt_broker> \
        -t "sms/gateway/command/status" \
        -m '{"action": "status"}'
done
```

#### Rollback Plan

**If update fails:**
1. Identify affected devices
2. Flash previous firmware via USB (if accessible)
3. Or wait for automatic recovery (if implemented)
4. Document issue for next update

---

## Troubleshooting

### Common Issues

#### Issue 1: OTA Not Available

**Symptoms:**
- `pio run --target upload --upload-port <ip>` fails
- "OTA not enabled" error

**Solutions:**
1. Check WiFi connection:
   ```bash
   mosquitto_sub -h <mqtt_broker> -t "sms/gateway/status" -v
   # Should show "wifi": "connected"
   ```

2. Enable OTA via MQTT:
   ```bash
   mosquitto_pub -h <mqtt_broker> \
     -t "sms/gateway/command/ota" \
     -m '{"action": "enable"}'
   ```

3. Check device IP:
   - Check serial monitor
   - Check MQTT status topic
   - Ping device: `ping <device_ip>`

#### Issue 2: Upload Timeout

**Symptoms:**
- Upload starts but times out
- Progress stops at certain percentage

**Solutions:**
1. Check network stability:
   ```bash
   ping -c 10 <device_ip>
   # Check for packet loss
   ```

2. Increase timeout in PlatformIO:
   ```ini
   [env:lilygo-t-call]
   upload_timeout = 120  # seconds
   ```

3. Check firewall:
   - Ensure port 3232 is open
   - Check router settings

#### Issue 3: Update Fails Mid-Transfer

**Symptoms:**
- OTA progress stops
- Error message in MQTT
- Device remains on old firmware

**Solutions:**
1. Check error message:
   ```bash
   mosquitto_sub -h <mqtt_broker> \
     -t "sms/gateway/ota/status" -v
   ```

2. Common errors:
   - **OTA_RECEIVE_ERROR**: Network interruption
   - **OTA_END_ERROR**: Insufficient flash space
   - **OTA_AUTH_ERROR**: Wrong password

3. Retry update:
   ```bash
   # Wait 30 seconds, then retry
   sleep 30
   pio run --target upload --upload-port <device_ip>
   ```

#### Issue 4: Device Boots to Old Firmware

**Symptoms:**
- Update appears successful
- Device reboots but shows old version

**Solutions:**
1. Check if update actually completed:
   ```bash
   # Check OTA status topic
   mosquitto_sub -h <mqtt_broker> \
     -t "sms/gateway/ota/status" -v
   ```

2. Verify flash partition:
   - Check partition table in `platformio.ini`
   - Ensure OTA partition is large enough

3. Force USB flash:
   ```bash
   # Flash via USB to ensure clean state
   pio run --target upload
   ```

### Debug Mode

#### Enable Verbose Logging

**In `src/main.cpp`:**
```cpp
#define OTA_DEBUG true

#ifdef OTA_DEBUG
#define OTA_LOG(x) Serial.println("[OTA DEBUG] " x)
#else
#define OTA_LOG(x)
#endif
```

#### Monitor OTA Process

```bash
# Terminal 1: Serial monitor
pio device monitor

# Terminal 2: MQTT monitor
mosquitto_sub -h <mqtt_broker> \
  -t "sms/gateway/ota/+" -v

# Terminal 3: Network monitor
tcpdump -i any port 3232
```

---

## Best Practices

### 1. Version Management

- **Always increment version** before OTA update
- **Use semantic versioning**: MAJOR.MINOR.PATCH
- **Tag releases** in git
- **Document changes** in CHANGELOG.md

### 2. Testing Strategy

- **Test locally first** on development device
- **Test on staging** before production
- **Staged rollout** (10% → 50% → 100%)
- **Monitor for 24 hours** after deployment

### 3. Safety Measures

- **Backup plan**: Always have USB flash option
- **Rollback procedure**: Document how to revert
- **Health checks**: Verify device functionality after update
- **Monitoring**: Watch for errors after deployment

### 4. Code Quality

- **Incremental updates**: Small, focused changes
- **Backward compatibility**: When possible
- **Error handling**: Robust error recovery
- **Logging**: Comprehensive logging for debugging

### 5. Security

- **Use OTA password**: Always set password in production
- **Secure network**: Use WPA2/WPA3 WiFi
- **Verify firmware**: Check firmware integrity
- **Limit OTA window**: Enable OTA only when needed

---

## Security Considerations

### 1. Authentication

**Always use OTA password in production:**
```cpp
// In include/passwords.h
#define OTA_PASSWORD "strong_random_password_here"
```

**Generate secure password:**
```bash
# Generate random password
openssl rand -base64 32
```

### 2. Network Security

- **Use WPA2/WPA3** WiFi encryption
- **Isolate device network** (VLAN if possible)
- **Firewall rules**: Only allow OTA from trusted IPs
- **VPN access**: Use VPN for remote updates

### 3. Firmware Integrity

**Consider adding checksum verification:**
```cpp
#include <MD5Builder.h>

void verifyFirmware() {
    // Calculate and verify firmware checksum
    // Reject update if checksum doesn't match
}
```

### 4. Access Control

- **MQTT authentication**: Use MQTT username/password
- **OTA enable/disable**: Control via MQTT commands
- **Time-based access**: Enable OTA only during maintenance windows
- **Audit logging**: Log all OTA attempts

---

## CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/ota-deploy.yml
name: OTA Device Update

on:
  release:
    types: [published]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup PlatformIO
      uses: platformio/platformio-core-action@v1
      
    - name: Build Firmware
      run: |
        cd device/esp32-sms-gateway
        pio run -e lilygo-t-call
        
    - name: Deploy to Devices
      env:
        DEVICE_IPS: ${{ secrets.DEVICE_IPS }}
        MQTT_BROKER: ${{ secrets.MQTT_BROKER }}
        OTA_PASSWORD: ${{ secrets.OTA_PASSWORD }}
      run: |
        cd device/esp32-sms-gateway
        ./scripts/deploy_ota.sh
```

### Automated Testing

```yaml
# .github/workflows/test-ota.yml
name: Test OTA Update

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup PlatformIO
      uses: platformio/platformio-core-action@v1
      
    - name: Build Firmware
      run: |
        cd device/esp32-sms-gateway
        pio run -e esp32dev
        
    - name: Test OTA (if device available)
      run: |
        # Run OTA test script
        ./scripts/test_ota.sh
```

---

## Device-Specific Guides

### SMS Gateway Device

**Location:** `device/esp32-sms-gateway/`

**OTA Configuration:**
- Port: 3232
- Hostname: `esp32-sms-gateway`
- Password: Set in `include/passwords.h`

**Quick Update:**
```bash
cd device/esp32-sms-gateway

# Enable OTA
mosquitto_pub -h <mqtt_broker> \
  -t "sms/gateway/command/ota" \
  -m '{"action": "enable"}'

# Upload
pio run --target upload --upload-port <device_ip>
```

**Monitor:**
```bash
mosquitto_sub -h <mqtt_broker> \
  -t "sms/gateway/ota/+" -v
```

---

## Additional Resources

- [PlatformIO OTA Documentation](https://docs.platformio.org/en/latest/platforms/espressif32.html#ota-update)
- [ArduinoOTA Library](https://github.com/esp8266/Arduino/tree/master/libraries/ArduinoOTA)
- [ESP32 OTA Updates](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/system/ota.html)
- [Project MQTT Protocol](MQTT_PROTOCOL.md)
- [Device README](../device/esp32-sms-gateway/README.md)

---

## Support

For issues and questions:
- Check [Troubleshooting](#troubleshooting) section
- Review device-specific README
- Check [MQTT Protocol Documentation](../MQTT_PROTOCOL.md)
- Open issue on GitHub

---

**Last Updated:** 2026-01-25  
**Version:** 1.0.0
