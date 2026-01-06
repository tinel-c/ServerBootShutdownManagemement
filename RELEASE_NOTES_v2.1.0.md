# Release Notes - Version 2.1.0

**Release Date:** January 6, 2026

## 🎉 Client PC Monitoring & Automation

This release introduces a major new feature: **automatic server power management based on client PC presence**. The system now monitors Windows client PCs and intelligently manages server power to ensure servers are available when needed and conserve energy when not in use.

---

## ✨ New Features

### Client PC Monitoring Application

- **Windows Client Application** - Python-based monitoring application for Windows PCs
  - Automatic startup via Windows Task Scheduler
  - MQTT-based communication with automation server
  - Presence detection (startup/shutdown)
  - Heartbeat monitoring (every 60 seconds)
  - Automatic reconnection on network interruptions
  - Comprehensive logging for troubleshooting

- **Easy Installation** - One-click installation script for Windows
  - Interactive configuration wizard
  - Automatic dependency installation
  - Task Scheduler integration
  - No manual configuration required

### Server Automation

- **Smart Power Management** - Automatic server boot/shutdown based on client presence
  - **Auto-Boot**: Server powers on when first client PC starts
  - **Auto-Shutdown**: Server shuts down when all clients are offline
  - **Grace Period**: Configurable delay (default: 5 minutes) prevents rapid power cycling
  - **Cancellation**: Shutdown cancelled if client comes back online during grace period

- **Node-RED Automation Flows** - Two new modular flows for client management
  - `40-client-tracking.json` - Client presence tracking and state management
  - `41-client-automation.json` - Server power automation logic
  - Enable/disable automation via dashboard toggle
  - Real-time client monitoring dashboard

### Dashboard Enhancements

- **Client PCs Panel** - New dashboard panel showing active clients
  - Live client list with hostnames and IP addresses
  - Last seen timestamps with auto-updating relative times
  - Active client count
  - Modern gradient card design

- **Automation Control Panel** - Manage automation behavior
  - Enable/disable toggle switch
  - Automation status display
  - Configuration summary (boot trigger, shutdown trigger, target server)
  - Visual status indicators

### MQTT Protocol Extensions

- **New Topics**:
  - `clients/{client_id}/presence` - Client startup/shutdown notifications
  - `clients/{client_id}/heartbeat` - Client heartbeat messages
  - `automation/clients/status` - Automation status updates

- **Message Schemas**:
  - Client presence messages (online/offline with metadata)
  - Client heartbeat messages (with uptime tracking)
  - Full protocol documentation in MQTT_PROTOCOL.md

---

## 📦 What's Included

### New Files

**Client Application:**
- `client/client_monitor.py` - Main monitoring application
- `client/install_client.bat` - Windows installation script
- `client/requirements_client.txt` - Python dependencies
- `client/config/client_config.yaml` - Client configuration
- `client/config/.env.example` - Environment template
- `client/README_CLIENT.md` - Client documentation

**Node-RED Flows:**
- `nodered/flows/40-client-tracking.json` - Client presence tracking
- `nodered/flows/41-client-automation.json` - Server automation logic

**Configuration:**
- Updated `config/mqtt_config.yaml` with client topics
- Updated `config/server_config.yaml` with automation settings

**Documentation:**
- Updated `README.md` with client PC monitoring section
- Updated `docs/MQTT_PROTOCOL.md` with client message schemas
- Updated `docs/ARCHITECTURE.md` with client integration details
- New `RELEASE_NOTES_v2.1.0.md` (this file)

---

## 🔧 Configuration

### Server Configuration

New section in `config/server_config.yaml`:

```yaml
client_automation:
  enabled: true
  shutdown_grace_period: 300  # seconds (5 minutes)
  heartbeat_timeout: 120  # seconds
  target_server: "dell/t310"  # Server to control
```

### Client Configuration

Client settings in `client/config/client_config.yaml`:

```yaml
client:
  custom_name: ""  # Optional custom name
  heartbeat_interval: 60  # seconds
  
mqtt:
  broker:
    host: "localhost"
    port: 1883
```

---

## 📋 Installation & Upgrade

### New Installation

Follow the updated installation guide in README.md, which now includes client PC setup.

### Upgrading from v2.0.0

1. **Pull latest changes:**
   ```bash
   cd ServerBootShutdownManagemement
   git pull
   ```

2. **Update Node-RED flows:**
   - Import `flows/40-client-tracking.json`
   - Import `flows/41-client-automation.json`
   - Deploy changes

3. **Install client application on Windows PCs:**
   - Copy `client` folder to each Windows PC
   - Run `install_client.bat` as Administrator
   - Configure MQTT connection when prompted

4. **Update configuration files** (optional):
   - Review `config/server_config.yaml` for new `client_automation` section
   - Review `config/mqtt_config.yaml` for new client topics

---

## 🎯 Use Cases

### Home Lab Automation

**Scenario:** You have a home server that hosts VMs for development work.

**Before v2.1.0:**
- Manually boot server when starting work
- Manually shutdown server when done
- Server runs 24/7 or requires manual intervention

**With v2.1.0:**
- Install client monitor on your workstation
- Server automatically boots when you start your PC
- Server automatically shuts down 5 minutes after you shut down your PC
- Zero manual intervention required

### Small Office Setup

**Scenario:** Office with 3-5 workstations requiring access to file server.

**Before v2.1.0:**
- Server runs 24/7 (energy waste)
- Or first person to arrive manually boots server

**With v2.1.0:**
- Install client monitor on all workstations
- Server boots when first employee arrives
- Server stays online as long as any employee is working
- Server shuts down 5 minutes after last employee leaves
- Automatic energy savings during nights and weekends

---

## 🔍 Technical Details

### Architecture Changes

- **Client Layer Added**: New component in system architecture
- **MQTT Topics Extended**: Three new topic patterns for client communication
- **Node-RED Flows**: Two new modular flows (numbered 40-41)
- **Flow Context**: Client tracking uses Node-RED flow context for state management

### Performance Impact

- **Minimal Overhead**: Client application uses <50MB RAM
- **Network Traffic**: ~1KB per minute per client (heartbeat messages)
- **MQTT Load**: Negligible impact on broker performance
- **Server Impact**: No performance impact on managed servers

### Security Considerations

- Client credentials stored in `.env` file (not committed to git)
- MQTT authentication required for client connections
- Consider enabling MQTT TLS/SSL for production deployments
- Client application runs with user privileges (not elevated)

---

## 🐛 Known Issues

None at this time.

---

## 🔜 Future Enhancements

Potential features for future releases:

- Linux client support
- macOS client support
- Multiple server automation (different servers for different client groups)
- Client grouping and policies
- Email/SMS notifications for automation events
- Historical client presence tracking
- Web-based client configuration

---

## 📚 Documentation

- **Client Installation**: See `client/README_CLIENT.md`
- **MQTT Protocol**: See `docs/MQTT_PROTOCOL.md`
- **Architecture**: See `docs/ARCHITECTURE.md`
- **Main README**: See `README.md`

---

## 🙏 Acknowledgments

This release adds significant automation capabilities to the Server Boot/Shutdown Management System, making it more intelligent and user-friendly for home labs and small office environments.

---

**Version:** 2.1.0  
**Previous Version:** 2.0.0  
**Release Date:** January 6, 2026
