# Dell & HP Server Remote Management System

Automated remote boot and shutdown system for Dell T310 (IPMI) and HP DL360p (iLO) servers, controlled via MQTT protocol.

## Features

- 🚀 **Remote Boot** - Wake-on-LAN, IPMI (Dell T310), and iLO (HP DL360p) based boot
- 🛑 **Remote Shutdown** - Graceful VM shutdown and force shutdown options
- 📊 **Status Monitoring** - Real-time server status via MQTT
- 🏥 **Health Monitoring** - HealthChecks.io integration with API v3 support
- 🖥️ **Premium Dashboard** - Modern Glassmorphism-style Node-RED interface with state tracking
- 🔒 **Secure** - TLS/SSL support, credential management
- 🔄 **Auto-Restart** - Systemd services with automatic restart
- 📝 **Comprehensive Logging** - Detailed logs for troubleshooting

## System Architecture

![System Architecture](docs/architecture_diagram_v2.svg)

The system uses a **centralized automation server** running Node-RED dashboard, Mosquitto MQTT broker, and Python management scripts. Users access the web dashboard to control servers, which sends commands via MQTT. Python scripts execute the commands using appropriate methods:

- **Dell T310**: Wake-on-LAN or IPMI for boot, Proxmox API for graceful shutdown
- **HP DL360p**: iLO for boot, Proxmox API for graceful shutdown

Status and health monitoring is published back through MQTT to the dashboard for real-time visibility.

**Detailed Documentation**: See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for complete system architecture, communication flows, and deployment information.

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


## 🖥️ Node-RED Dashboard (v2.0 - Modular Architecture)

A modern, feature-rich Node-RED dashboard with **modular architecture** for easy maintenance and scalability.

### ✨ New in v2.0

#### Modular Flow Architecture
The dashboard has been completely refactored from a monolithic design to a **feature-based modular system**:
- ✅ **8 Independent Modules** - Each feature in its own importable file
- ✅ **Easy Maintenance** - Update individual features without affecting others
- ✅ **Better Collaboration** - Multiple developers can work on different servers
- ✅ **Scalable Design** - Easily add new servers following the established pattern
- ✅ **Version Control Friendly** - Clear, feature-specific commits

#### Comprehensive Health Monitoring
New **advanced health monitoring dashboard** with Healthchecks.io integration:
- 📊 **Real-time Status Cards** - Individual cards for each health check
- ⏱️ **Live Countdown Timers** - See time until next ping (updates every second)
- 📈 **Statistics Display** - Total pings, grace period, timeout, manual resume status
- 🎨 **Modern UI Design** - Gradient backgrounds, color-coded status indicators
- 🔗 **Badge Links** - Quick access to external status badges
- 📋 **Comprehensive Data** - Displays all 16+ data points from health checks

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

### Modular Architecture Benefits

**File Structure:**
```
nodered/flows/
├── 00-base-config.json       # Core: UI base, groups, MQTT broker
├── 10-dell-controls.json     # Dell: Boot/shutdown buttons
├── 11-dell-status.json       # Dell: Status display
├── 12-dell-health.json       # Dell: Health monitoring
├── 20-hp-controls.json       # HP: Boot/shutdown buttons  
├── 21-hp-status.json         # HP: Status display
├── 22-hp-health.json         # HP: Health monitoring
├── 90-log-console.json       # Shared: Log console
└── README.md                 # Quick reference guide
```

**Numbering Convention:**
- `00-09`: Core infrastructure
- `10-19`: Dell T310 features
- `20-29`: HP DL360p features
- `30-39`: Reserved for future server 1
- `40-49`: Reserved for future server 2
- `90-99`: Shared utilities

### Adding a New Server

Thanks to the modular design, adding a new server is straightforward:

1. **Update base config** with new UI groups
2. **Copy templates** from Dell or HP modules (10-12 or 20-22)
3. **Customize** server names, MQTT topics, and boot methods
4. **Import** the new modules (numbered 30-32 for third server)
5. **Deploy** and test

See `nodered/NODE_RED_DEVELOPMENT.md` for detailed instructions.

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
├── nodered/                   # Node-RED dashboard (v2.0 modular)
│   ├── flows/                 # Modular flow files
│   │   ├── 00-base-config.json
│   │   ├── 10-dell-controls.json
│   │   ├── 11-dell-status.json
│   │   ├── 12-dell-health.json
│   │   ├── 20-hp-controls.json
│   │   ├── 21-hp-status.json
│   │   ├── 22-hp-health.json
│   │   ├── 90-log-console.json
│   │   └── README.md
│   ├── docker-compose.yml
│   ├── Dockerfile
│   ├── NODE_RED_DEVELOPMENT.md
│   ├── HEALTH_DASHBOARD_GUIDE.md
│   └── flows.json             # Legacy (deprecated)
├── docs/                      # Documentation
│   ├── SETUP.md
│   ├── MQTT_PROTOCOL.md
│   └── TROUBLESHOOTING.md
├── requirements.txt           # Python dependencies
├── install.sh                 # Installation script
├── uninstall.sh               # Uninstallation script
└── DEVELOPMENT_GUIDE.md       # Development documentation
```

## Documentation

### Core Documentation
- [Development Guide](DEVELOPMENT_GUIDE.md) - Comprehensive development documentation
- [Setup Guide](docs/SETUP.md) - Detailed setup instructions
- [MQTT Protocol](docs/MQTT_PROTOCOL.md) - MQTT message specifications
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions

### Node-RED Dashboard Documentation
- [Node-RED Development Guide](nodered/NODE_RED_DEVELOPMENT.md) - Complete development reference (800+ lines)
- [Flows Quick Reference](nodered/flows/README.md) - Import instructions and module descriptions
- [Health Dashboard Guide](nodered/HEALTH_DASHBOARD_GUIDE.md) - Visual layout and customization guide

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

**Version:** 2.0.0  
**Last Updated:** 2025-12-29

## Changelog

### v2.0.0 (2025-12-29) - Major Node-RED Dashboard Overhaul
**🎉 Modular Architecture & Enhanced Health Monitoring**

#### Major Changes
- ✨ **Modular Flow Architecture**: Refactored from monolithic to 8 independent, importable modules
- 📊 **Comprehensive Health Dashboard**: Advanced health monitoring with 16+ data points per check
- ⏱️ **Live Countdown Timers**: Real-time countdown to next health check ping
- 🎨 **Modern UI Design**: Gradient backgrounds, glass-morphism effects, color-coded status indicators
- 📚 **Extensive Documentation**: Added 3 new documentation files (2,000+ lines total)

#### New Features
- Individual check cards with full data visualization
- Statistics grid (total pings, grace period, timeout, manual resume)
- Live timing information (last ping, next ping, time until)
- Tags display with pill styling
- Badge URL links to external monitoring
- Empty state handling
- Scalable naming convention for future servers (slots 30-49 reserved)

#### Documentation Added
- `nodered/NODE_RED_DEVELOPMENT.md` - 800+ line comprehensive guide
- `nodered/flows/README.md` - Quick reference for modular flows
- `nodered/HEALTH_DASHBOARD_GUIDE.md` - Visual dashboard guide

#### Breaking Changes
- Old monolithic `flows.json` deprecated (renamed to `flows.json.legacy`)
- Must import modular flows in specific order (see documentation)
- Health dashboard now requires full payload structure from Healthchecks.io

#### Migration Path
Users on v1.x should:
1. Backup existing flows
2. Import new modular flows in order
3. Update health monitoring payloads if using custom service

See `nodered/NODE_RED_DEVELOPMENT.md` for complete migration guide.

---

### v1.3.0 (Previous)
- Health monitoring integration with Healthchecks.io API v3
- Premium glassmorphism dashboard
- Multi-server support (Dell T310 & HP DL360p)
