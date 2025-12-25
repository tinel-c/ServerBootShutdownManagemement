# Dell & HP Server Remote Management System

Automated remote boot and shutdown system for Dell T310 (IPMI) and HP DL360p (iLO) servers, controlled via MQTT protocol.

## Features

- 🚀 **Remote Boot** - Wake-on-LAN, IPMI (Dell T310), and iLO (HP DL360p) based boot
- 🛑 **Remote Shutdown** - Graceful VM shutdown and force shutdown options
- 📊 **Status Monitoring** - Real-time server status via MQTT
- 🔒 **Secure** - TLS/SSL support, credential management
- 🔄 **Auto-Restart** - Systemd services with automatic restart
- 📝 **Comprehensive Logging** - Detailed logs for troubleshooting

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
   sudo nano /opt/dell_t310_management/config/.env
   
   # Edit MQTT configuration
   sudo nano /opt/dell_t310_management/config/mqtt_config.yaml
   
   # Edit server configuration
   sudo nano /opt/dell_t310_management/config/server_config.yaml
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
python3 /opt/dell_t310_management/scripts/boot/wol_boot.py --mac 00:11:22:33:44:55

# Boot via IPMI
python3 /opt/dell_t310_management/scripts/boot/ipmi_boot.py

# Graceful shutdown
python3 /opt/dell_t310_management/scripts/shutdown/graceful_shutdown.py

# Force shutdown (requires --confirm)
python3 /opt/dell_t310_management/scripts/shutdown/force_shutdown.py --confirm
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
├── scripts/
│   ├── boot/                  # Boot scripts
│   ├── shutdown/              # Shutdown scripts
│   ├── status/                # Status monitoring
│   └── utils/                 # Utility modules
├── systemd/                   # Systemd service files
├── docs/                      # Documentation
├── requirements.txt           # Python dependencies
├── install.sh                 # Installation script
├── uninstall.sh               # Uninstallation script
└── DEVELOPMENT_GUIDE.md       # Development documentation
```

## Documentation

- [Development Guide](DEVELOPMENT_GUIDE.md) - Comprehensive development documentation
- [Setup Guide](docs/SETUP.md) - Detailed setup instructions
- [MQTT Protocol](docs/MQTT_PROTOCOL.md) - MQTT message specifications
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions

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

**Version:** 1.0.0  
**Last Updated:** 2025-12-26
