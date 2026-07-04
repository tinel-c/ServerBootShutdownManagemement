# Release Notes v3.6.0 - SMS Gateway Device & OTA Updates

**Release Date:** 2026-01-25  
**Version:** 3.6.0

---

## 🎉 Major Features

### SMS Gateway Device Application

A complete embedded device application for ESP32 with SIM800 module, providing SMS send/receive capabilities through the automation platform.

**Key Features:**
- ✅ **SMS Send/Receive** via MQTT commands
- ✅ **Self-Recovery** - Automatic WiFi/MQTT reconnection
- ✅ **Reset Detection** - Announces resets via MQTT and SMS
- ✅ **Emergency Alerts** - SMS notifications when WiFi/MQTT fails
- ✅ **Watchdog Timer** - Prevents system hangs
- ✅ **OTA Updates** - Remote firmware updates via WiFi

**Hardware:** LilyGo T-Call SIM800 (ESP32 + SIM800 GSM module)

**Location:** `device/sms-gateway/`

---

## 📦 What's New

### SMS Gateway Device (`device/sms-gateway/`)

#### Core Functionality
- **MQTT Integration**: Full integration with project topic structure (`sms/gateway/*`)
- **SMS Operations**: Send and receive SMS messages via MQTT commands
- **Status Monitoring**: Real-time device status via MQTT
- **Timestamp Support**: NTP integration for accurate timestamps

#### Self-Recovery Features
- **WiFi Reconnection**: Automatic reconnection with up to 3 attempts
- **MQTT Reconnection**: Automatic reconnection with up to 5 attempts
- **GSM Recovery**: Modem reinitialization on startup
- **Connection Health Checks**: Periodic connection monitoring

#### Monitoring & Alerts
- **Reset Announcements**: Tracks boot count and announces resets
- **Emergency SMS**: Sends SMS alerts when critical failures occur
- **Error Publishing**: Publishes errors to MQTT for monitoring
- **Status Updates**: Periodic status updates every 5 minutes

### OTA (Over-The-Air) Updates

#### Features
- **ArduinoOTA Integration**: Standard ESP32 OTA protocol
- **MQTT Control**: Enable/disable OTA via MQTT commands
- **Progress Tracking**: Real-time update progress (0-100%) via MQTT
- **SMS Notifications**: Alerts sent when OTA starts/completes/fails
- **Password Protection**: Optional password to secure OTA updates
- **Automatic Recovery**: OTA disabled if WiFi disconnects

#### MQTT Topics
- `sms/gateway/command/ota` - Enable/disable OTA
- `sms/gateway/ota/status` - Update status (started/completed/error)
- `sms/gateway/ota/progress` - Progress updates (every 10%)

### Documentation

#### New Documentation
- **`docs/developer/OTA_DEVICE_UPDATES.md`** - Comprehensive OTA developer guide
  - Development workflow
  - Testing strategies
  - Deployment procedures
  - Troubleshooting guide
  - Security best practices
  - CI/CD integration examples

- **`device/sms-gateway/README.md`** - Complete device documentation
  - Installation instructions
  - Configuration guide
  - Usage examples
  - Troubleshooting
  - Hardware reference

#### Updated Documentation
- **`docs/MQTT_PROTOCOL.md`** - Added SMS gateway message schemas
- **`README.md`** - Added SMS gateway and OTA guide references

---

## 🔧 Configuration

### New Configuration Files

**Device Configuration:**
- `device/sms-gateway/include/passwords.h.example` - Credentials template
- `device/sms-gateway/config/sms_gateway_config.yaml` - YAML configuration
- `device/sms-gateway/config/.env.example` - Environment variables template

**Updated Configuration:**
- `config/mqtt_config.yaml` - Added SMS gateway MQTT topics

---

## 📋 MQTT Topics Added

### SMS Gateway Topics (Domain: 500-599)

**Commands:**
- `sms/gateway/command/send` - Send SMS command
- `sms/gateway/command/ota` - OTA enable/disable command

**Status:**
- `sms/gateway/status` - Device status with connection states
- `sms/gateway/status/timestamp` - Last status update

**SMS Operations:**
- `sms/gateway/receive/from` - Phone number of received SMS
- `sms/gateway/receive/text` - Text content of received SMS
- `sms/gateway/receive/timestamp` - Timestamp when SMS was received
- `sms/gateway/send/response` - Send operation result
- `sms/gateway/send/timestamp` - Timestamp when SMS was sent

**System:**
- `sms/gateway/reset` - Device reset announcement
- `sms/gateway/error` - Error notifications
- `sms/gateway/ota/status` - OTA update status
- `sms/gateway/ota/progress` - OTA update progress

---

## 🚀 Getting Started

### For Device Developers

1. **Setup PlatformIO:**
   ```bash
   cd device/sms-gateway
   cp include/passwords.h.example include/passwords.h
   # Edit include/passwords.h with your credentials
   ```

2. **Build and Upload:**
   ```bash
   pio run
   pio run --target upload
   ```

3. **Enable OTA (after initial setup):**
   ```bash
   mosquitto_pub -h <mqtt_broker> \
     -t "sms/gateway/command/ota" \
     -m '{"action": "enable"}'
   ```

4. **Read Documentation:**
   - Device README: `device/sms-gateway/README.md`
   - OTA Guide: `docs/developer/OTA_DEVICE_UPDATES.md`

### For Automation Platform Users

The SMS gateway is ready to integrate with Node-RED flows:
- Domain: SMS/Notifications (500-599)
- Device: SMS Gateway (510-519)
- MQTT Topics: `sms/gateway/*`

---

## 📝 Migration Notes

### No Breaking Changes

This is a new feature addition. No existing functionality is affected.

### Optional Integration

To use the SMS gateway:
1. Build and deploy the device firmware
2. Configure device credentials
3. Add Node-RED flows for SMS automation (optional)
4. Start sending/receiving SMS via MQTT

---

## 🔒 Security Considerations

### OTA Updates
- **Set OTA Password**: Configure `OTA_PASSWORD` in `include/passwords.h`
- **Secure Network**: Use WPA2/WPA3 WiFi encryption
- **Access Control**: Enable OTA only during maintenance windows

### MQTT
- **Use Authentication**: Configure MQTT username/password
- **TLS/SSL**: Consider enabling TLS for production

### Emergency SMS
- **Phone Number**: Configure `EMERGENCY_PHONE_NUMBER` for alerts
- **Privacy**: Be aware SMS alerts may contain system information

---

## 📚 Documentation

### New Documentation
- [SMS Gateway README](../../device/sms-gateway/README.md) - Complete device guide
- [OTA Developer Guide](../developer/OTA_DEVICE_UPDATES.md) - OTA development guide

### Updated Documentation
- [MQTT Protocol](../MQTT_PROTOCOL.md) - Added SMS gateway schemas
- [README](../../README.md) - Added SMS gateway references

---

## 🐛 Known Issues

None at this time.

---

## 🙏 Acknowledgments

- Original SMS gateway code from [PlatformIO_Arduino_SIM800_ESP32](https://github.com/tinel-c/PlatformIO_Arduino_SIM800_ESP32)
- TinyGSM library for GSM/GPRS communication
- ArduinoOTA for OTA update functionality

---

## 📦 Files Changed

### New Files (13 files)
- `device/sms-gateway/` - Complete device application
- `docs/developer/OTA_DEVICE_UPDATES.md` - OTA developer guide

### Modified Files (4 files)
- `.gitignore` - Added device credentials exclusion
- `README.md` - Added SMS gateway references
- `config/mqtt_config.yaml` - Added SMS gateway topics
- `docs/MQTT_PROTOCOL.md` - Added SMS gateway schemas

**Total:** 13 new files, 4 modified files, 2,636+ lines added

---

## 🔄 Upgrade Instructions

1. **Pull latest changes:**
   ```bash
   git pull origin main
   ```

2. **Review new files:**
   - Check `device/sms-gateway/` for device application
   - Review `docs/developer/OTA_DEVICE_UPDATES.md` for OTA guide

3. **Build device (if using SMS gateway):**
   ```bash
   cd device/sms-gateway
   # Follow setup instructions in README.md
   ```

4. **No server-side changes required** - SMS gateway is a standalone device

---

## 📞 Support

For issues and questions:
- Check device README: `device/sms-gateway/README.md`
- Review OTA guide: `docs/developer/OTA_DEVICE_UPDATES.md`
- See troubleshooting sections in documentation
- Open issue on GitHub

---

**Full Changelog:** See [CHANGELOG.md](../../CHANGELOG.md)
