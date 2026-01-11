# Dell & HP Server Remote Management System

Automated remote boot and shutdown system for Dell T310 (IPMI) and HP DL360p (iLO) servers, controlled via MQTT protocol.

## Features

### Server Management
- 🚀 **Remote Boot** - Wake-on-LAN, IPMI (Dell T310), and iLO (HP DL360p) based boot
- 🛑 **Remote Shutdown** - Graceful VM shutdown and force shutdown options
- 📊 **Status Monitoring** - Real-time server status via MQTT
- 🏥 **Health Monitoring** - HealthChecks.io integration with API v3 support
- 🤖 **Smart Automation** - Client-aware boot, 5-minute grace periods, command cooldown protection
- 📋 **Activity Logging** - Complete audit trail with triggers, commands, and status changes

### Client Management (NEW v2.4.0)
- 💻 **Client PC Monitoring** - Automatic server power management based on client PC presence
- 🛑 **Remote Client Shutdown** - Graceful and force shutdown of Windows client PCs
- 💾 **Application Save** - Automatically saves open applications before shutdown
- 🔄 **Auto-Update** - Clients self-update from GitHub releases automatically
- 🎨 **System Tray** - Modern icon with status indicators and update checks

### User Interface
- 🖥️ **Premium Dashboard** - Modern glassmorphism-style Node-RED interface with live countdowns
- 🎛️ **Client Control Panel** - Individual and bulk client shutdown operations
- 🔒 **Secure** - TLS/SSL support, credential management
- 📝 **Comprehensive Logging** - Detailed logs for troubleshooting
- 🔄 **Auto-Restart** - Systemd services with automatic restart

## System Architecture

![System Architecture](docs/architecture_diagram_v3.svg)

The system uses a **centralized automation server** running Node-RED dashboard, Mosquitto MQTT broker, and Python management scripts with **smart client-aware automation**.

### Architecture Highlights:
- **Client Monitoring**: Windows PCs send presence/heartbeat → Automation detects client needs
- **Smart Boot**: Server automatically boots when clients connect (if server is down)
- **Smart Shutdown**: 5-minute grace period when all clients disconnect  
- **Command Cooldown**: 5-minute protection prevents boot/shutdown spam
- **Activity Logging**: Complete audit trail of all automation events

### Server Control Methods:
- **Dell T310**: Wake-on-LAN or IPMI for boot, Proxmox API for graceful shutdown
- **HP DL360p**: iLO for boot, Proxmox API for graceful shutdown

Status and health monitoring is published back through MQTT to the dashboard for real-time visibility.

**Detailed Documentation**: See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for complete system architecture, communication flows, and deployment information.  
**Architecture Diagram Source**: See [docs/ARCHITECTURE_DIAGRAM_DESCRIPTION.md](docs/ARCHITECTURE_DIAGRAM_DESCRIPTION.md) for diagram specification.

## Quick Start

### Prerequisites

- Dell T310 server with IPMI enabled (optional)
- HP DL360p server with iLO enabled (optional)
- Proxmox VE installed on Dell T310 (optional)
- Ubuntu VM for running management scripts
- MQTT broker (Mosquitto recommended)
- Network connectivity between all components

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/tinel-c/ServerBootShutdownManagemement.git
   cd ServerBootShutdownManagemement
   ```

2. **Run the installation script:**
   ```bash
   sudo chmod +x install.sh
   sudo ./install.sh
   ```

3. **Configure the system:**
   
   Edit the configuration files with your settings:
   
   ```bash
   # Edit environment variables
   sudo nano /opt/dell_server_management/config/.env
   
   # Edit MQTT configuration
   sudo nano /opt/dell_server_management/config/mqtt_config.yaml
   
   # Edit server configuration
   sudo nano /opt/dell_server_management/config/server_config.yaml
   ```

4. **Enable and start services:**
   ```bash
   sudo systemctl enable mqtt-boot-listener.service
   sudo systemctl enable mqtt-shutdown-listener.service
   sudo systemctl enable status-publisher.service
   
   sudo systemctl start mqtt-boot-listener.service
   sudo systemctl start mqtt-shutdown-listener.service
   sudo systemctl start status-publisher.service
   ```

5. **Verify services are running:**
   ```bash
   sudo systemctl status mqtt-boot-listener.service
   sudo systemctl status mqtt-shutdown-listener.service
   sudo systemctl status status-publisher.service
   ```

## Usage

### Client Setup (Windows PCs)

Install the client monitor on Windows PCs for automatic server management:

1. **Download client folder** to Windows PC
2. **Run installer as Administrator:**
   ```cmd
   install_client.bat
   ```
3. **Configure MQTT connection** when prompted
4. **Restart PC** or start manually

The client will:
- ✅ Send presence/heartbeat to automation server
- ✅ Trigger automatic server boot when needed
- ✅ Allow server shutdown when all clients offline
- ✅ Receive remote shutdown commands
- ✅ Auto-update from GitHub releases

**Documentation**: See `client/README_CLIENT.md` for detailed setup

### Remote Client Shutdown (v2.4.0)

Shutdown client PCs from the Node-RED dashboard:

1. Open dashboard: `http://localhost:1880/dashboard`
2. Navigate to "Client Shutdown Control"
3. Select **Graceful** (saves applications) or **Force** (immediate)
4. Confirm operation

**Via MQTT:**
```bash
mosquitto_pub -h <mqtt-broker> -t "clients/CLIENT_ID/command/shutdown" -m '{
  "action": "shutdown",
  "type": "graceful",
  "timestamp": "2026-01-09T15:30:00Z",
  "request_id": "shutdown-001"
}'
```

**Documentation**: See `client/README_CLIENT_SHUTDOWN.md`

### Boot Server via MQTT

Send a boot command to the MQTT topic:

```bash
mosquitto_pub -h <mqtt-broker> -t "dell/t310/command/boot" -m '{
  "action": "boot",
  "method": "wol",
  "timestamp": "2025-12-25T20:00:00+02:00",
  "request_id": "boot-001"
}'
```

Methods:
- `wol` - Wake-on-LAN (recommended for powered-off server)
- `ipmi` - IPMI power on (Dell T310)
- `ilo` - iLO power on (HP DL360p)

**Boot HP DL360p via iLO:**

```bash
mosquitto_pub -h <mqtt-broker> -t "hp/dl360p/command/boot" -m '{
  "action": "boot",
  "method": "ilo",
  "timestamp": "2025-12-26T00:00:00+02:00",
  "request_id": "boot-002"
}'
```

### Shutdown Server via MQTT

Send a shutdown command to the MQTT topic:

```bash
mosquitto_pub -h <mqtt-broker> -t "dell/t310/command/shutdown" -m '{
  "action": "shutdown",
  "type": "graceful",
  "timeout": 300,
  "timestamp": "2025-12-25T20:00:00+02:00",
  "request_id": "shutdown-001"
}'
```

Types:
- `graceful` - Shutdown VMs first, then host (recommended)
- `force` - Immediate hard power off

**Shutdown HP DL360p:**

```bash
mosquitto_pub -h <mqtt-broker> -t "hp/dl360p/command/shutdown" -m '{
  "action": "shutdown",
  "type": "graceful",
  "timeout": 300,
  "timestamp": "2025-12-26T00:00:00+02:00",
  "request_id": "shutdown-002"
}'
```

### Monitor Server Status

Subscribe to the status topic for each server:

```bash
# Monitor Dell T310
mosquitto_sub -h <mqtt-broker> -t "dell/t310/status" -v

# Monitor HP DL360p
mosquitto_sub -h <mqtt-broker> -t "hp/dl360p/status" -v
```

Status messages are published every 30 seconds (configurable).


## 💻 Client PC Monitoring & Automation

Monitor client PCs and automatically manage server power based on client presence.

### Features

- **Automatic Server Boot** - Servers power on when first client PC starts
- **Automatic Server Shutdown** - Servers shut down when all clients are offline (with grace period)
- **Heartbeat Monitoring** - Track active clients in real-time
- **System Tray Icon** - Color-coded status indicator showing connection and server state
- **Windows Integration** - Runs on startup via Task Scheduler
- **Configurable Grace Period** - Prevent rapid power cycling (default: 5 minutes)

### Client Installation

1. **On each Windows PC**, navigate to the `client` directory

2. **Run the installer as Administrator:**
   ```cmd
   Right-click install_client.bat → Run as administrator
   ```

3. **Configure MQTT connection** when prompted:
   - MQTT Broker Host (e.g., `192.168.1.100`)
   - MQTT Broker Port (default: `1883`)
   - MQTT Username
   - MQTT Password

4. **Restart the PC** or start manually:
   ```cmd
   python "C:\Program Files\ClientMonitor\client_monitor.py"
   ```

**To Uninstall:**
```cmd
Right-click client\uninstall_client.bat → Run as administrator
```

### How It Works

```
Client PC Startup → Presence Signal → Server Boots (if offline)
       ↓
   Heartbeat every 60s → Server stays online
       ↓
Client PC Shutdown → Offline Signal → Wait 5 min → Server Shuts Down (if all clients offline)
```

### Monitoring Clients

View active clients in the Node-RED dashboard:
- Navigate to http://localhost:1880/dashboard/home
- Check the "Client PCs" panel
- See active clients with last seen time
- Enable/disable automation with toggle switch

### Client MQTT Topics

```bash
# Monitor client presence
mosquitto_sub -h <mqtt-broker> -t "clients/+/presence" -v

# Monitor client heartbeats
mosquitto_sub -h <mqtt-broker> -t "clients/+/heartbeat" -v
```

**See [client/README_CLIENT.md](client/README_CLIENT.md) for detailed client documentation.**


## 🖥️ Node-RED Dashboard (Modular Architecture)

Modern, feature-rich dashboard with modular flows for easy maintenance and scalability.

### Key Features
- **8 Independent Modules** - Update features without affecting others
- **Real-time Health Monitoring** - Live status cards with countdown timers
- **Client Automation** - Smart boot/shutdown based on client presence
- **Modern UI** - Glassmorphism design with color-coded indicators
- **Telegram Bot** - Optional remote control via Telegram (v2.5.0+)

### Quick Setup

1. **Navigate to the nodered directory:**
   ```bash
   cd nodered
   ```

2. **Start Node-RED using Docker:**
   ```bash
   docker-compose up -d
   ```

3. **Access Node-RED Editor:** http://localhost:1880

4. **Import Modular Flows** (in order):
   ```
   flows/00-base-config.json      # Core configuration (import first)
   flows/10-dell-controls.json    # Dell T310 buttons
   flows/11-dell-status.json      # Dell T310 status display
   flows/12-dell-health.json      # Dell T310 health monitoring
   flows/20-hp-controls.json      # HP DL360p buttons
   flows/21-hp-status.json        # HP DL360p status display
   flows/22-hp-health.json        # HP DL360p health monitoring
   flows/40-client-tracking.json  # Client PC presence tracking
   flows/41-client-automation.json # Server automation based on clients
   flows/50-telegram-interface.json # Telegram bot interface (optional)
   flows/90-log-console.json      # System log console
   ```

5. **Click Deploy** and access dashboard: http://localhost:1880/dashboard/home

### Dashboard Features

#### Per-Server Control Panels
Each server (Dell T310 & HP DL360p) has dedicated panels:
- **Control Buttons**:
  - 🟢 BOOT SERVER - Wake server using appropriate method (WOL/IPMI/iLO)
  - 🟠 PROXMOX SHUTDOWN - Graceful VM + host shutdown
  - 🔴 FORCE SHUTDOWN - Immediate hard power off
  
- **Status Display**:
  - Real-time server state (ONLINE/OFFLINE/UNKNOWN)
  - Last report timestamp with auto-updating countdown
  - State change tracking (when server switched states)
  - Previous state history
  
- **Health Monitoring**:
  - Individual check cards with status icons (✅/❌/⚠️)
  - Statistics: Total pings, grace period, timeout
  - Timing: Last ping, next ping, countdown to next ping
  - Optional data: Methods, subjects, tags, descriptions
  - Clickable badge URLs
  - Color-coded borders (green=up, red=down, orange=warning)

#### System Log Console
- Terminal-style display with dark background
- Color-coded by log level (INFO/WARNING/ERROR/CRITICAL)
- Rolling buffer (last 50 entries)
- Auto-scroll to latest entries
- Subscribes to all MQTT response topics

#### Telegram Bot Interface (Optional)
- 🤖 Control servers via Telegram commands
- 📊 Real-time status notifications
- 🔔 Automatic alerts on server state changes
- 🔐 User authorization support
- **Commands**: `/boot`, `/shutdown`, `/force`, `/status`, `/help`
- **See**: [nodered/TELEGRAM_SETUP.md](nodered/TELEGRAM_SETUP.md) for setup instructions

**Flow Structure:**
```
nodered/flows/
├── 00-base-config.json        # Core configuration
├── 10-12-dell-*.json          # Dell T310 management
├── 20-22-hp-*.json            # HP DL360p management
├── 40-42-client-*.json        # Client tracking & automation
├── 50-telegram-interface.json # Telegram bot (optional)
└── 90-log-console.json        # System logging
```

See `nodered/flows/README.md` for import instructions and `nodered/NODE_RED_DEVELOPMENT.md` for detailed documentation.

### Health Check Integration

The dashboard integrates with **Healthchecks.io** (or compatible services):

**MQTT Payload Example:**
```json
{
  "timestamp": "2025-12-29T10:51:43Z",
  "server": "Dell T310",
  "checks": [
    {
      "name": "nextcloud",
      "status": "up",
      "n_pings": 255949,
      "grace": 300,
      "timeout": 120,
      "last_ping": "2025-12-29T10:50:01+00:00",
      "next_ping": "2025-12-29T10:52:01+00:00",
      "badge_url": "https://healthchecks.io/badge/..."
    }
  ]
}
```

### Configuration Notes

- **MQTT Broker**: Configured in `00-base-config.json`, defaults to `localhost:1883`
- **Dashboard Path**: `/dashboard/home` (customizable in base config)
- **Auto-Refresh**: Status and health widgets update automatically
- **Persistence**: Flow context stores metadata (resets on Node-RED restart)

### Documentation

- **Development Guide**: `nodered/NODE_RED_DEVELOPMENT.md` (800+ lines)
  - Complete feature reference
  - Customization instructions
  - Best practices and conventions
  - Troubleshooting guide
  
- **Quick Reference**: `nodered/flows/README.md`
  - Import instructions
  - File descriptions
  - MQTT payload examples
  
- **Visual Guide**: `nodered/HEALTH_DASHBOARD_GUIDE.md`
  - Dashboard layout explanation
  - Color coding reference
  - Customization options

### Migration from v1.x

If you're using the old monolithic `flows.json`:

1. **Backup existing flows** (Menu → Export → All Flows)
2. **Clear all flows** in Node-RED
3. **Import modular flows** in the order listed above
4. **Deploy and test** all functionality
5. **Archive old flows.json** (automatically renamed to `flows.json.legacy`)

The modular architecture offers better maintainability and makes future updates much easier!

---

*Note: The setup assumes the MQTT broker is running on the host machine (`localhost:1883`). Update the broker configuration in `00-base-config.json` if needed.*

## Configuration

### Environment Variables (.env)

```bash
# MQTT Credentials
MQTT_PASSWORD=your_mqtt_password

# IPMI Credentials
IPMI_HOST=192.168.1.100
IPMI_USERNAME=admin
IPMI_PASSWORD=your_ipmi_password

# Proxmox Credentials
PROXMOX_HOST=192.168.1.100
PROXMOX_USERNAME=root@pam
PROXMOX_PASSWORD=your_proxmox_password

# Server Configuration
SERVER_MAC_ADDRESS=00:11:22:33:44:55

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/dell_t310_management.log
```

### MQTT Topics

| Topic | Direction | Purpose |
|-------|-----------|---------|
| `dell/t310/command/boot` | Client → Server | Boot commands |
| `dell/t310/command/shutdown` | Client → Server | Shutdown commands |
| `dell/t310/status` | Server → Client | Status updates |
| `dell/t310/response` | Server → Client | Command responses |

## Manual Testing

### Test IPMI Connection

```bash
ipmitool -I lanplus -H 192.168.1.100 -U admin -P password chassis status
```

### Test Wake-on-LAN

```bash
wakeonlan 00:11:22:33:44:55
```

### Test Individual Scripts

```bash
# Boot via WoL
python3 /opt/dell_server_management/scripts/boot/wol_boot.py --mac 00:11:22:33:44:55

# Boot via IPMI
python3 /opt/dell_server_management/scripts/boot/ipmi_boot.py

# Graceful shutdown
python3 /opt/dell_server_management/scripts/shutdown/graceful_shutdown.py

# Force shutdown (requires --confirm)
python3 /opt/dell_server_management/scripts/shutdown/force_shutdown.py --confirm
```

## Troubleshooting

### Check Service Logs

```bash
# Boot listener logs
journalctl -u mqtt-boot-listener.service -f

# Shutdown listener logs
journalctl -u mqtt-shutdown-listener.service -f

# Status publisher logs
journalctl -u status-publisher.service -f
```

### Common Issues

1. **MQTT Connection Failed**
   - Verify MQTT broker is running
   - Check network connectivity
   - Verify credentials in `.env`

2. **IPMI Commands Failing**
   - Verify IPMI is enabled in BIOS
   - Check IPMI IP address is correct
   - Test with `ipmitool` command directly

3. **Wake-on-LAN Not Working**
   - Enable WoL in BIOS
   - Verify MAC address is correct
   - Ensure server is on same subnet

## Project Structure

```
ServerBootShutdownMangement/
├── config/                    # Configuration files
│   ├── mqtt_config.yaml
│   └── server_config.yaml
├── scripts/
│   ├── boot/                  # Boot scripts (WOL, IPMI, iLO)
│   ├── shutdown/              # Shutdown scripts (graceful, force)
│   ├── status/                # Status monitoring & health checks
│   └── utils/                 # Utility modules (MQTT, logging)
├── systemd/                   # Systemd service files
├── client/                    # Client PC monitoring application
│   ├── client_monitor.py      # Main client application
│   ├── install_client.bat     # Windows installation script
│   ├── uninstall_client.bat   # Windows uninstallation script
│   ├── requirements_client.txt
│   ├── config/
│   │   ├── client_config.yaml
│   │   └── .env.example
│   └── README_CLIENT.md       # Client documentation
├── nodered/                   # Node-RED dashboard (v2.1 modular)
│   ├── flows/                 # Modular flow files
│   │   ├── 00-base-config.json
│   │   ├── 10-dell-controls.json
│   │   ├── 11-dell-status.json
│   │   ├── 12-dell-health.json
│   │   ├── 20-hp-controls.json
│   │   ├── 21-hp-status.json
│   │   ├── 22-hp-health.json
│   │   ├── 40-client-tracking.json    # NEW: Client presence tracking
│   │   ├── 41-client-automation.json  # NEW: Server automation
│   │   ├── 50-telegram-interface.json # NEW: Telegram bot interface
│   │   ├── 90-log-console.json
│   │   └── README.md
│   ├── docker-compose.yml
│   ├── Dockerfile
│   ├── NODE_RED_DEVELOPMENT.md
│   ├── HEALTH_DASHBOARD_GUIDE.md
│   ├── TELEGRAM_SETUP.md      # Telegram bot setup guide
│   └── flows.json             # Legacy (deprecated)
├── docs/                      # Documentation
│   ├── SETUP.md
│   ├── MQTT_PROTOCOL.md
│   ├── ARCHITECTURE.md
│   └── TROUBLESHOOTING.md
├── requirements.txt           # Python dependencies
├── install.sh                 # Installation script
├── uninstall.sh               # Uninstallation script
└── DEVELOPMENT_GUIDE.md       # Development documentation
```

## Documentation

### Getting Started
- [README.md](README.md) - This file (overview and quick start)
- [Setup Guide](docs/SETUP.md) - Installation and configuration
- [Client Management Guide](CLIENT_MANAGEMENT_GUIDE.md) - Complete client management

### Core Documentation
- [Development Guide](DEVELOPMENT_GUIDE.md) - Development and contribution
- [Architecture](docs/ARCHITECTURE.md) - System architecture and design
- [MQTT Protocol](docs/MQTT_PROTOCOL.md) - Message specifications
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues

### Node-RED Dashboard
- [Node-RED Development](nodered/NODE_RED_DEVELOPMENT.md) - Complete reference
- [Flows Quick Reference](nodered/flows/README.md) - Import instructions
- [Health Dashboard Guide](nodered/HEALTH_DASHBOARD_GUIDE.md) - Health monitoring
- [Smart Wakeup Guide](nodered/SMART_WAKEUP_GUIDE.md) - Automation guide
- [Telegram Setup](nodered/TELEGRAM_SETUP.md) - Telegram bot configuration

### Release Information
- [Release Notes v2.5.0](RELEASE_NOTES_v2.5.0.md) - Latest release
- [Release Notes v2.4.0](RELEASE_NOTES_v2.4.0.md) - Client management
- [Release Notes v2.3.0](RELEASE_NOTES_v2.3.0.md) - Smart automation
- [Release History](RELEASE_HISTORY.md) - Older versions (v1.x - v2.2.0)

## Requirements

### Hardware
- Dell T310 server with IPMI interface
- Network interface with Wake-on-LAN support

### Software
- Ubuntu 22.04+ (on VM)
- Proxmox VE 7.x+
- Python 3.8+
- ipmitool
- MQTT broker (Mosquitto)

## Security Considerations

⚠️ **Important Security Notes:**

- Never commit `.env` file with real credentials
- Use TLS/SSL for MQTT in production
- Restrict IPMI access to management network
- Use strong passwords for all services
- Regularly update all components

## License

[Specify your license here]

## Support

For issues and questions, please refer to:
- [Development Guide](DEVELOPMENT_GUIDE.md)
- [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
- [GitHub Issues](https://github.com/tinel-c/ServerBootShutdownManagemement/issues)

## Repository

**GitHub:** https://github.com/tinel-c/ServerBootShutdownManagemement

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**Constantin Bogza**

---

**Version:** 2.5.0  
**Last Updated:** 2026-01-11

## Recent Releases

### v2.5.0 (2026-01-11) - Telegram Bot Interface
- 🤖 Control servers via Telegram commands
- 📊 Real-time status notifications
- 🔔 Automatic alerts on server state changes
- See `RELEASE_NOTES_v2.5.0.md` for details

### v2.4.0 (2026-01-09) - Client Management & Auto-Update
- 🛑 Remote client shutdown (graceful/force)
- 🔄 Auto-update from GitHub releases
- 📌 Version display in system tray tooltip
- See `RELEASE_NOTES_v2.4.0.md` for details

### v2.3.0 (2026-01-07) - Smart Client-Aware Automation
- ✨ Auto-boot when clients connect
- 📋 Complete activity logging
- 🛡️ Command cooldown protection
- See `RELEASE_NOTES_v2.3.0.md` for details

**Older Versions:** See `RELEASE_HISTORY.md` for v1.x - v2.2.0
