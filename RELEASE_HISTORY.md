# Release History

> **Note**: For the latest releases (v2.3.0+), see individual release note files.

This document provides a consolidated overview of historical releases from v1.0.0 through v2.2.0.

---

## v2.2.0 - Decentralized Automation & Idle Shutdown (Jan 7, 2026)

### Key Features
- **Decentralized Health Monitoring**: Automation no longer relies on shared global context
- **Client-Side Health Integration**: Client monitors health topic instead of generic status
- **Reactive Idle Auto-Shutdown**: Detects idle servers (0 clients) and auto-shuts down after 5-min grace
- **Enhanced Fail-safety**: Automation continues independently if status flows restart

### Benefits
- More reliable automation
- Better power management
- Handles edge cases (manual boots, Node-RED restarts)
- Instant shutdown cancellation when client connects

---

## v2.1.0 - Client PC Monitoring & Automation (Jan 6, 2026)

### Major Features
- **Windows Client Application**: Python-based monitoring for Windows PCs
  - Auto-startup via Task Scheduler
  - MQTT presence detection & heartbeat (60s interval)
  - Automatic reconnection
  - System tray icon with status indicators

- **Server Automation**:
  - Auto-boot when first client connects
  - Auto-shutdown when all clients disconnect (5-min grace period)
  - Client tracking dashboard in Node-RED

- **Installation**: One-click installer with configuration wizard

### New Files
- `client/client_monitor.py` - Main client application
- `client/install_client.bat` - Windows installer
- `nodered/flows/40-client-tracking.json` - Client tracking
- `nodered/flows/41-client-automation.json` - Automation logic

---

## v2.0.0 - Modular Node-RED Dashboard (Dec 29, 2025)

### Architectural Overhaul
- **Modular Flow Architecture**: Split monolithic `flows.json` into 8 independent modules
  - `00-base-config.json` - Core infrastructure
  - `10-12-dell-*.json` - Dell T310 controls/status/health
  - `20-22-hp-*.json` - HP DL360p controls/status/health
  - `90-log-console.json` - System logs

### Health Monitoring Enhancement
- **Comprehensive Health Dashboard**: 16+ data points per check
- **Live Countdown Timers**: Real-time countdown to next health ping
- **Modern UI**: Glassmorphism effects, gradient backgrounds, color-coded statuses
- **Individual Check Cards**: Statistics, timing info, tags display, badge URLs

### Benefits
- Easier maintenance (update features independently)
- Better organization (feature-based structure)
- Scalable design (reserved slots for future servers)
- Version control friendly

### Documentation
- Added `nodered/NODE_RED_DEVELOPMENT.md` (800+ lines)
- Added `nodered/flows/README.md` (quick reference)
- Added `nodered/HEALTH_DASHBOARD_GUIDE.md`

---

## v1.3.0 - Health Monitoring & Premium Dashboard

### Features
- Health monitoring integration with Healthchecks.io API v3
- Premium glassmorphism dashboard design
- Multi-server support (Dell T310 & HP DL360p)
- Real-time status updates with visual indicators

---

## v1.2.0 - Enhanced Status Monitoring

### Features
- Improved status reporting frequency
- Enhanced error handling for MQTT disconnections
- Better logging with log rotation
- Status message optimization

---

## v1.1.0 - Configuration Improvements

### Features
- YAML-based configuration files
- Environment variable support for sensitive data
- Better credential management
- Enhanced documentation

---

## v1.0.0 - Initial Release

### Core Features
- **Multi-Server Support**: Dell T310 (IPMI) and HP DL360p (iLO)
- **Unified MQTT API**: Standardized topics for boot/shutdown/status
- **Protocol Support**: IPMI, HP iLO, Wake-on-LAN
- **Security**: Environment-variable based configuration
- **Status Monitoring**: Real-time health and power status

### Technical Stack
- Python 3.8+
- MQTT (Mosquitto)
- Libraries: paho-mqtt, python-hpilo, ipmitool

### Installation
- Automated installation script (`install.sh`)
- Systemd service integration
- Configuration templates

---

## Migration Notes

### From v2.1.0 or Earlier
If upgrading from v2.1.0 or earlier to v2.3.0+:
1. Backup existing Node-RED flows
2. Import updated modular flows in numerical order
3. Update client applications to latest version
4. Verify automation toggle is enabled
5. Test client presence detection

### From v1.x
If upgrading from v1.x:
1. Complete system backup recommended
2. Review new MQTT protocol (see `docs/MQTT_PROTOCOL.md`)
3. Update Node-RED flows (modular architecture)
4. Install client monitoring if desired
5. Update documentation references

---

## See Also

- **Current Releases**: See [docs/releases/](docs/releases/) (`RELEASE_NOTES_v2.3.0.md` … `RELEASE_NOTES_v3.11.8.md`)
- **Architecture**: See `docs/ARCHITECTURE.md`
- **MQTT Protocol**: See `docs/MQTT_PROTOCOL.md`
- **Development Guide**: See `DEVELOPMENT_GUIDE.md`

---

**Last Updated**: January 11, 2026  
**Maintained By**: Project Documentation Team
