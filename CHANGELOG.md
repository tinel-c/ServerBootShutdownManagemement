# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.1.1] - 2026-01-18

### Fixed - Update Script Reliability
- **Parallel Service Stop**: `update.sh` now stops all services in parallel to reduce wait times and prevent hangs.
- **Graceful Health Monitor Exit**: Added `SIGTERM` handler to `health_monitor.py` for cleaner shutdowns.
- **Service Timeouts**: Added `TimeoutStopSec=15` to all systemd service files as a safety fallback.

## [3.1.0] - 2026-01-18

### Added - Enhanced Stability & Status Fallback
- **Ping Fallback (Dell T310)**: Implemented ICMP ping fallback in `status_publisher.py` to correctly identify `offline` state when Proxmox API is unreachable.
- **Watchdog Shutdown Guard**: Added a 10-minute cooldown in Node-RED (`41-client-automation.json`) after a shutdown command to prevent recovery boots during host shutdown.
- **Client-Only Recovery**: Recovery boots now only trigger if active clients are waiting for the server.

### Changed
- **Increased Timeout**: Proxmox API timeout increased from 5s to 15s to handle transition delays.
- **Activity Logging**: Improved recovery boot triggers descriptions in activity log.

### Fixed
- Resolved the "UNKNOWN" status reboot loop on Dell T310 servers.
- Prevented unintended "Recovery Boots" when no clients are connected.

## [3.0.0] - 2026-01-17

### Added - Multi-Domain Automation System

#### Architecture
- **Modular automation system** supporting multiple domains (gates, lights, irrigation, HVAC, etc.)
- **Numbered flow system** (000-999) for organizing automation domains
- **Domain isolation** with independent, self-contained modules
- **Scalable design** supporting unlimited automation types

#### Templates
- `domain-base-template.json` - Base configuration template for new domains
- `control-panel-template.json` - Control interface template with buttons
- `status-display-template.json` - Status monitoring template
- `sensor-monitoring-template.json` - Sensor data collection template
- `automation-logic-template.json` - Automation rules and scheduling template

#### Documentation
- `docs/AUTOMATION_ARCHITECTURE.md` - Complete multi-domain system architecture
- `docs/AUTOMATION_INTEGRATION_GUIDE.md` - Step-by-step migration guide
- `docs/QUICK_START_NEW_AUTOMATION.md` - 5-minute setup guide for new domains
- `nodered/templates/README.md` - Template usage documentation

#### Domain Support
- Reserved number ranges for 9 automation domains:
  - 100-199: Server Management (existing)
  - 200-299: Gate Automation
  - 300-399: Lighting Control
  - 400-499: Irrigation System
  - 500-599: SMS/Notifications
  - 600-699: Security/Cameras
  - 700-799: HVAC/Climate Control
  - 800-899: Energy Management
  - 900-999: Shared Utilities

#### MQTT Structure
- Hierarchical MQTT topic organization: `domain/location/device/type/action`
- Consistent topic patterns across all domains
- Command, status, and sensor topic specifications
- Topic migration patterns for existing systems

### Changed

#### Node-RED Infrastructure
- Removed Docker deployment (Node-RED now runs natively on Ubuntu)
- Updated all Docker commands to systemd service commands
- Changed Node-RED management from `docker-compose` to `systemctl`
- Updated logging from `docker logs` to `journalctl`

#### Documentation Updates
- Updated `README.md` with multi-domain automation overview
- Added automation system documentation section
- Updated version to 3.0.0
- Enhanced project scope description

### Removed
- `nodered/docker-compose.yml` - Docker Compose configuration
- `nodered/Dockerfile` - Docker image definition
- All Docker-specific commands and references from documentation

### Fixed
- Corrected Docker references in all documentation files
- Updated deployment instructions for native Ubuntu installation
- Fixed MQTT broker status checks to use systemctl

## [2.5.0] - 2026-01-11

### Added - Telegram Bot Interface
- Complete Telegram bot integration for server management
- Command interface: `/boot`, `/shutdown`, `/force`, `/status`, `/help`
- Inline keyboard buttons matching Node-RED dashboard
- Real-time notifications for server state changes
- User authorization support via `TELEGRAM_ALLOWED_USERS`
- Polling and webhook modes
- New flow: `50-telegram-interface.json`

### Documentation
- `nodered/TELEGRAM_SETUP.md` - Complete Telegram bot setup guide
- Updated `README.md` with Telegram interface documentation

### Dependencies
- Added `node-red-contrib-telegrambot` library

## [2.4.0] - 2026-01-09

### Added - Client Management & Auto-Update
- Remote client shutdown (graceful/force) from Node-RED dashboard
- Application save logic before shutdown (Ctrl+S to all windows)
- Bulk client shutdown operations
- Auto-update system with GitHub release integration
- Semantic version comparison for updates
- Manual update check via system tray
- Automatic rollback on failed updates
- Version display in system tray tooltip
- New flow: `42-client-shutdown.json`

### Documentation
- `client/README_CLIENT_SHUTDOWN.md` - Remote shutdown guide
- `client/README_AUTO_UPDATE.md` - Auto-update system guide
- Updated `CLIENT_MANAGEMENT_GUIDE.md`

## [2.3.0] - 2026-01-07

### Added - Smart Client-Aware Automation
- Automatic server boot when clients connect
- Automatic server shutdown with 5-minute grace period
- Command cooldown protection (5 minutes)
- Comprehensive activity logging
- Smart retry logic for transient failures
- State machine for automation management
- New flow: `41-client-automation.json`

### Documentation
- `nodered/SMART_WAKEUP_GUIDE.md` - Smart automation guide
- Updated `docs/ARCHITECTURE.md` with v2.3 features

## [2.2.0] - 2025-12-29

### Added - Advanced Health Monitoring
- Comprehensive health dashboard with 16+ data points per check
- Real-time countdown timers to next ping
- Statistics grid (pings, grace period, timeout, manual resume)
- Status badges and color-coded indicators
- Tags display with pill styling
- Badge URL links
- Modern gradient UI design
- Updated flows: `12-dell-health.json`, `22-hp-health.json`

### Documentation
- `nodered/HEALTH_DASHBOARD_GUIDE.md` - Health monitoring guide

## [2.1.0] - 2025-12-28

### Added - Client PC Monitoring
- Windows client monitoring application
- Presence and heartbeat tracking
- Automatic server power management
- System tray integration
- New flows: `40-client-tracking.json`

### Documentation
- `client/README_CLIENT.md` - Client setup guide
- Updated `README.md` with client monitoring features

## [2.0.0] - 2025-12-27

### Changed - Modular Architecture
- Refactored from monolithic `flows.json` to modular flow files
- Feature-based organization (00-base, 10-dell, 20-hp, 90-logs)
- Independent feature modules for easier maintenance
- Version control friendly structure

### Added
- Modular flow files in `nodered/flows/`
- Flow-specific documentation
- Base configuration module
- Per-server feature modules

### Documentation
- `nodered/NODE_RED_DEVELOPMENT.md` - Complete development guide
- `nodered/flows/README.md` - Flow import instructions

### Deprecated
- `flows.json` (monolithic, renamed to flows.json.legacy)

## [1.x] - 2025-12 and earlier

See `RELEASE_HISTORY.md` for older version history.

### Initial Features
- Dell T310 boot/shutdown control
- HP DL360p support
- MQTT protocol implementation
- Basic Node-RED dashboard
- Python systemd services
- Status monitoring
- Health checks integration

---

## Version Numbering

- **Major** (X.0.0): Significant architectural changes, breaking changes
- **Minor** (x.X.0): New features, non-breaking enhancements
- **Patch** (x.x.X): Bug fixes, documentation updates

## Links

- [Release Notes v2.5.0](RELEASE_NOTES_v2.5.0.md)
- [Release Notes v2.4.0](RELEASE_NOTES_v2.4.0.md)
- [Release Notes v2.3.0](RELEASE_NOTES_v2.3.0.md)
- [Release History](RELEASE_HISTORY.md) - Versions 1.x - 2.2.0
