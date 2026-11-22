# OTA Device Updates - Developer Guide

This guide explains how to develop, test, and deploy Over-The-Air (OTA) firmware updates for embedded devices in the ServerBootShutdownManagement project.

For the full device workflow (submodule, UART first flash, fleet OTA, Windows broker fallback), see [DEVICE_FIRMWARE_DEVELOPMENT.md](DEVICE_FIRMWARE_DEVELOPMENT.md). That playbook is the default for every new ESP device. Copy [device/templates/platformio-esp32](../../device/templates/platformio-esp32/README.md). Post-build flashing goes through [scripts/status/fleet_ota_hook.py](../../scripts/status/fleet_ota_hook.py).

ArduinoOTA listens whenever STA has an IP. There is no MQTT enable/disable command. `sms/gateway/command/ota` is retired as of SMS gateway `fw` 1.1.0.

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

| Device | Path | Automatic post-build OTA |
|--------|------|--------------------------|
| SMS Gateway (ESP32 + SIM800), `fw` ≥ 1.1.0 | `device/PlatformIO_esp32-sms-gateway/` | Yes — after `pio run -e lilygo-t-call` when status has a fresh `ip` |
| 4-ch thyristor illumination (RY1–4 IO32/25/27/12, LED IO5) | `device/PlatformIO_esp32-4ch-thyristor-board-illumination/` | Yes — after `pio run` when the board is online |
| ESP8266 main gate (`fw` ≥ 1.0.0, port 8266) | `device/PlatformIO_ESP8266_Main_Entry/` | After one UART flash of 1.0.0. `flash` stays false until `gate/main/status` has an `ip` |

### Fleet monitor (dev PC)

Registry and state live in the monorepo:

| Path | Role |
|------|------|
| [scripts/status/device_fleet.yaml](../../scripts/status/device_fleet.yaml) | Device list, status topics, flash flags (`expected` for client counts) |
| [scripts/status/device_fleet.py](../../scripts/status/device_fleet.py) | `status` / `watch` / `flash` |
| `scripts/status/device_fleet_state.json` | Local memory (IP, firmware, last_seen); gitignored |
| [client/device_fleet_panel.py](../../client/device_fleet_panel.py) | Windows tray **Device Fleet…** UI (online/expected, `fw`, OTA upload, Tasmota scan) |
| [device/tasmota/catalog.yaml](../../device/tasmota/catalog.yaml) | Tasmota boards merged into that same list |
| [client/config/device_fleet.yaml](../../client/config/device_fleet.yaml) | Offline fallback only. The client fetches the two files above from GitHub |

```bash
# One-shot sighting (writes device_fleet_state.json)
python scripts/status/device_fleet.py status

# Keep memory fresh while developing
python scripts/status/device_fleet.py watch

# Flash a known-good .bin when the sighting is fresh
python scripts/status/device_fleet.py flash \
  --id PlatformIO_esp32-4ch-thyristor-board-illumination \
  --bin device/PlatformIO_esp32-4ch-thyristor-board-illumination/.pio/build/esp32dev/firmware.bin
```

The thyristor `platformio.ini` uses **esptool** for `pio run -t upload` (Serial Burn / first flash). It also runs `scripts/ota_after_build.py` after every successful `firmware.bin` from `pio run`. That hook calls `device_fleet.py flash`. On a new PC it installs `pyyaml` and `paho-mqtt` into a system Python first, because PlatformIO’s Python does not have them. Offline, missing IP, or `flash: false` in the registry is a soft success (the `.bin` remains and a UART upload can continue). Do not rely on PlatformIO’s Upload button for OTA. A failed `espota` to a live board fails the build post-step.

`device_fleet.py flash` binds espota with `-I` to the PC’s LAN IP. If the local attempt fails (common on Windows when the firewall blocks the ESP’s TCP callback), it retries over SSH on `192.168.2.4` (`FLEET_OTA_VIA=auto`). Force with `FLEET_OTA_VIA=broker` or `local`. SSH uses `%USERPROFILE%\.ssh\serverside_192_168_2_4_ed25519` (override with `FLEET_OTA_SSH_KEY`). Set `SKIP_FLEET_OTA=1` during `pio run` / UART upload when you must not touch a live board.

Thyristor firmware ≥ **0.2.2** starts ArduinoOTA only after Wi-Fi has an IP (serial: `OTA listening on …:3232`). An OTA reboot turns the 230 V channels off; the firmware already forces channels off on OTA start and on boot.

Windows ClientMonitor tray → **Device Fleet…** shows online vs expected counts, firmware versions, and per-device `.bin` upload (same `device_fleet.py` / broker fallback). See [client/README_CLIENT.md](../../client/README_CLIENT.md) and [DEVICE_FIRMWARE_DEVELOPMENT.md](DEVICE_FIRMWARE_DEVELOPMENT.md).

### OTA Technology Stack

- **Protocol**: ArduinoOTA (ESP32 native OTA) / `espota.py`
- **Transport**: WiFi (requires active WiFi connection)
- **Port**: 3232 (default, configurable)
- **Authentication**: Optional password protection
- **Control**: OTA is always listening after Wi-Fi has an IP (illumination and SMS gateway). Do not gate it behind an MQTT enable command.
- **Monitoring**: MQTT topics for status and progress; fleet tool listens to status for IP memory. Status JSON must include `device`, `fw`, `ip`, `ota_port`.

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

| Topic | Direction | Payload |
|-------|-----------|---------|
| `sms/gateway/status` | Device → subscribers | JSON: `device`, `fw`, `ip`, `ota_port`, `wifi`, `mqtt`, `gsm`, `uptime_s`, `rssi`, `boot_count`, `timestamp` |
| `sms/gateway/status/timestamp` | Device → subscribers | ISO8601 timestamp string |
| `sms/gateway/ota/status` | Device → subscribers | `{"device","fw","state":"started\|completed\|error","detail"}` |
| `sms/gateway/ota/progress` | Device → subscribers | `{"device","progress","total","percent"}` |

`sms/gateway/command/ota` is not used. OTA binds after the STA address is up (`fw` ≥ 1.1.0).

### OTA States

1. **Disabled** - OTA not available (default if WiFi disconnected)
2. **Enabled** - OTA ready to accept updates
3. **In Progress** - Update being received/flashed
4. **Completed** - Update finished, device will reboot
5. **Error** - Update failed, device remains operational

---

## Development Workflow

### 1. Initial Setup

OTA is part of the firmware. It is not behind `#ifdef OTA_ENABLED` and it is not toggled with MQTT.

- `platformio.ini`: `upload_protocol = esptool` and `extra_scripts = post:scripts/ota_after_build.py`
- `scripts/ota_after_build.py` sets `DEVICE_ID` and calls `fleet_ota_hook.register`
- Status JSON includes `device`, `fw`, `ip`, `ota_port`
- `ArduinoOTA.begin()` runs only after STA has an IP; `ArduinoOTA.handle()` runs from `loop()`
- Optional `OTA_PASSWORD` in `include/passwords.h` (empty means no password)

### 2. Development Cycle

#### Step 1: First flash (UART)

```bash
cd device/PlatformIO_esp32-sms-gateway
# Skip post-build OTA while the serial adapter is attached:
# PowerShell: $env:SKIP_FLEET_OTA = "1"
SKIP_FLEET_OTA=1 pio run -e lilygo-t-call -t upload --upload-port COMx
pio device monitor -b 115200
```

Serial should show `[OTA] listening on <ip>:3232` after Wi-Fi connects.

#### Step 2: Later updates

From the device directory, a plain build flashes when the fleet sighting is fresh:

```bash
pio run -e lilygo-t-call
```

Or from the monorepo root:

```bash
python scripts/status/device_fleet.py flash \
  --id PlatformIO_esp32-sms-gateway \
  --bin device/PlatformIO_esp32-sms-gateway/.pio/build/lilygo-t-call/firmware.bin
```

Do not use `pio run -t upload --upload-port <ip>`. That path is UART (`esptool`), and a placeholder IP breaks the IDE Upload button.

#### Step 3: Confirm

`sms/gateway/status` publishes `fw` `1.1.0` or newer, plus `ip` and `ota_port`. `device_fleet.py status` shows the gateway online with that firmware.

---

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
cd device/PlatformIO_esp32-sms-gateway
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
pio run -e lilygo-t-call
# or, from the monorepo root:
python scripts/status/device_fleet.py flash \
  --id PlatformIO_esp32-sms-gateway \
  --bin device/PlatformIO_esp32-sms-gateway/.pio/build/lilygo-t-call/firmware.bin

mosquitto_sub -h 192.168.2.4 -t "sms/gateway/+" -v
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
# Fleet OTA. Run from the monorepo root after a build.
python scripts/status/device_fleet.py flash \
  --id PlatformIO_esp32-sms-gateway \
  --bin device/PlatformIO_esp32-sms-gateway/.pio/build/lilygo-t-call/firmware.bin
```

---

## Deployment Process

### 1. Pre-Deployment

#### Build Release Firmware

```bash
cd device/PlatformIO_esp32-sms-gateway

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
# From the monorepo root, after pio run produced firmware.bin:
python scripts/status/device_fleet.py flash \
  --id PlatformIO_esp32-sms-gateway \
  --bin device/PlatformIO_esp32-sms-gateway/.pio/build/lilygo-t-call/firmware.bin
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
- `device_fleet.py flash` reports offline, stale, or no IP
- Serial never prints `[OTA] listening on …`

**Solutions:**
1. Confirm status JSON includes `ip` and `ota_port`:
   ```bash
   mosquitto_sub -h 192.168.2.4 -t "sms/gateway/status" -v
   ```
2. OTA binds only after Wi-Fi has an address. A TCP probe of port 3232 while idle can look closed; ArduinoOTA’s invite is UDP.
3. On Windows, if espota invites the board and then gets no TCP callback, the fleet tool retries on `192.168.2.4` (`FLEET_OTA_VIA=auto`).
   - Check serial monitor
   - Check MQTT status topic
   - Ping device: `ping <device_ip>`

#### Issue 2: Upload Timeout / `No response from device`

**Symptoms:**
- `Sending invitation` then `No response from device` (UDP OK, TCP callback never arrives)
- Or invitation dots then `No response from the ESP` (device not listening)
- Progress stops mid-transfer

**Solutions:**
1. Confirm MQTT status has a fresh `ip` and (thyristor) serial shows `OTA listening on <ip>:3232`.
2. Prefer fleet flash (auto broker fallback) instead of PlatformIO `upload_protocol=espota`:
   ```bash
   python scripts/status/device_fleet.py flash \
     --id PlatformIO_esp32-4ch-thyristor-board-illumination \
     --bin device/PlatformIO_esp32-4ch-thyristor-board-illumination/.pio/build/esp32dev/firmware.bin
   # or force: set FLEET_OTA_VIA=broker
   ```
3. On Windows: allow inbound TCP to Python for the espota host port, or use the broker path above.
4. Check network stability: `ping <device_ip>` — brownouts/Wi-Fi drops abort OTA.
5. Do not use Upload → `127.0.0.1`; thyristor UART is `esptool` on COMx.

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
        cd device/PlatformIO_esp32-sms-gateway
        pio run -e lilygo-t-call
        
    - name: Deploy to Devices
      env:
        DEVICE_IPS: ${{ secrets.DEVICE_IPS }}
        MQTT_BROKER: ${{ secrets.MQTT_BROKER }}
        OTA_PASSWORD: ${{ secrets.OTA_PASSWORD }}
      run: |
        cd device/PlatformIO_esp32-sms-gateway
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
        cd device/PlatformIO_esp32-sms-gateway
        pio run -e esp32dev
        
    - name: Test OTA (if device available)
      run: |
        # Run OTA test script
        ./scripts/test_ota.sh
```

---

## Device-Specific Guides

### SMS Gateway Device

**Location:** `device/PlatformIO_esp32-sms-gateway/`

**OTA Configuration:**
- Port: 3232
- Hostname (ArduinoOTA): `esp32-sms-gateway` (fleet / repo id: `PlatformIO_esp32-sms-gateway`)
- Password: Set in `include/passwords.h`

**Quick Update:**
```bash
cd device/PlatformIO_esp32-sms-gateway
pio run -e lilygo-t-call
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
- [Device README](../device/PlatformIO_esp32-sms-gateway/README.md)

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
