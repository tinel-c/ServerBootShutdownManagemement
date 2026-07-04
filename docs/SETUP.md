# Dell T310 Management System - Setup Guide

This guide provides detailed step-by-step instructions for setting up the Dell T310 remote management system.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Hardware Configuration](#hardware-configuration)
3. [MQTT Broker Setup](#mqtt-broker-setup)
4. [System Installation](#system-installation)
5. [Configuration](#configuration)
6. [Service Setup](#service-setup)
7. [Testing](#testing)
8. [Production Deployment](#production-deployment)

---

## Prerequisites

### Required Hardware

- Dell T310 server
- Network connection (Ethernet)
- Another computer for management/testing

### Required Software

- Ubuntu 22.04 or later (on Proxmox VM)
- Proxmox VE 7.x or later
- MQTT broker (Mosquitto recommended)
- Python 3.8 or later

### Network Requirements

- Static IP for IPMI interface (recommended)
- MQTT broker accessible from server
- Firewall rules configured for:
  - MQTT: Port 1883 (or 8883 for TLS)
  - IPMI: Port 623 (UDP)

---

## Hardware Configuration

### Step 1: Enable IPMI in BIOS

1. **Boot the server and enter BIOS** (usually F2 or F10 during boot)

2. **Navigate to IPMI settings:**
   - Go to: `Integrated Devices` → `IPMI Settings`

3. **Enable IPMI over LAN:**
   - Set `IPMI over LAN` to `Enabled`

4. **Configure network settings:**
   - Choose `Static` IP address (recommended)
   - Set IP address (e.g., 192.168.1.100)
   - Set subnet mask (e.g., 255.255.255.0)
   - Set gateway (e.g., 192.168.1.1)

5. **Set IPMI credentials:**
   - Default username is usually `root` or `admin`
   - Set a strong password
   - Note these credentials for later use

6. **Save and exit BIOS**

### Step 2: Enable Wake-on-LAN

1. **In BIOS, navigate to:**
   - `Integrated Devices` → `Network Interface`

2. **Enable Wake-on-LAN:**
   - Set `Wake on LAN` to `Enabled`

3. **Note the MAC address** of the network interface

4. **Save and exit BIOS**

### Step 3: Verify IPMI Connectivity

From another computer on the same network:

```bash
# Test IPMI connectivity
ipmitool -I lanplus -H 192.168.1.100 -U admin -P <password> chassis status

# Expected output: Chassis Power is on/off
```

If this works, IPMI is configured correctly!

---

## MQTT Broker Setup

### Option 1: Install Mosquitto on Ubuntu Server

```bash
# Update package list
sudo apt update

# Install Mosquitto broker and clients
sudo apt install mosquitto mosquitto-clients

# Enable Mosquitto to start on boot
sudo systemctl enable mosquitto

# Start Mosquitto
sudo systemctl start mosquitto

# Verify Mosquitto is running
sudo systemctl status mosquitto
```

### Option 2: Configure Mosquitto Authentication

Create a password file:

```bash
# Create password for user 'dell_t310'
sudo mosquitto_passwd -c /etc/mosquitto/passwd dell_t310

# Edit Mosquitto configuration
sudo nano /etc/mosquitto/mosquitto.conf
```

Add the following to `/etc/mosquitto/mosquitto.conf`:

```
listener 1883
allow_anonymous false
password_file /etc/mosquitto/passwd
```

Restart Mosquitto:

```bash
sudo systemctl restart mosquitto
```

### Test MQTT Broker

```bash
# Subscribe to test topic (in one terminal)
mosquitto_sub -h localhost -t test/topic -u dell_t310 -P <password>

# Publish to test topic (in another terminal)
mosquitto_pub -h localhost -t test/topic -m "Hello MQTT" -u dell_t310 -P <password>
```

---

## System Installation

### Step 1: Download the Project

```bash
# Clone the repository
cd /tmp
git clone https://github.com/tinel-c/ServerBootShutdownManagemement.git
# OR download and extract ZIP file

cd ServerBootShutdownManagemement
```

### Step 2: Run Installation Script

```bash
# Make installation script executable
chmod +x install.sh

# Run installation as root
sudo ./install.sh
```

The installation script will:
- Install system dependencies (Python, ipmitool, wakeonlan)
- Create installation directory (`/opt/dell_server_management`)
- Set up Python virtual environment
- Install Python packages
- Copy configuration templates (including Victron and Huawei device `.env` from examples when missing)
- Install and enable all systemd services (core + Victron + Huawei energy publishers)

---

## Configuration

### Step 1: Configure Environment Variables

```bash
# Copy example file
sudo cp /opt/dell_server_management/config/.env.example /opt/dell_server_management/config/.env

# Edit with your credentials
sudo nano /opt/dell_server_management/config/.env
```

Update the following values:

```bash
# MQTT Credentials
MQTT_PASSWORD=your_actual_mqtt_password

# IPMI Credentials
IPMI_HOST=192.168.1.100  # Your IPMI IP
IPMI_USERNAME=admin
IPMI_PASSWORD=your_actual_ipmi_password

# Proxmox Credentials
PROXMOX_HOST=192.168.1.100  # Your Proxmox IP
PROXMOX_USERNAME=root@pam
PROXMOX_PASSWORD=your_actual_proxmox_password

# Server Configuration
SERVER_MAC_ADDRESS=00:11:22:33:44:55  # Your server's MAC address

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/dell_t310_management.log
```

**Important:** Set restrictive permissions on `.env`:

```bash
sudo chmod 600 /opt/dell_server_management/config/.env
```

### Step 2: Configure MQTT Settings

```bash
sudo nano /opt/dell_server_management/config/mqtt_config.yaml
```

Update the broker host:

```yaml
mqtt:
  broker:
    host: "localhost"  # Change to your MQTT broker IP if remote
    port: 1883
```

### Step 3: Configure Server Settings

```bash
sudo nano /opt/dell_server_management/config/server_config.yaml
```

Verify all settings match your hardware:

```yaml
server:
  name: "Dell T310"
  mac_address: "00:11:22:33:44:55"  # Your MAC address
  
  ipmi:
    host: "192.168.1.100"  # Your IPMI IP
```

---

## Service Setup

### Step 1: Enable Services

```bash
# Enable all services to start on boot
sudo systemctl enable mqtt-boot-listener.service
sudo systemctl enable mqtt-shutdown-listener.service
sudo systemctl enable status-publisher.service
sudo systemctl enable health-monitor.service
sudo systemctl enable tapo-monitor.service
sudo systemctl enable victron-mqtt-publisher.service
sudo systemctl enable victron-solar-forecast-publisher.service
sudo systemctl enable huawei-mqtt-publisher.service
```

Configure energy devices before expecting live MQTT (install.sh creates `.env` templates and attempts to start services):

**Victron (Cerbo GX):**

```bash
sudo nano /opt/dell_server_management/device/victron-multiplus-ii/config/.env
# Set VICTRON_GX_HOST, Unit IDs; MQTT uses /opt/dell_server_management/config/.env
sudo ./install_victron_service.sh
```

**Huawei (SUN2000):**

```bash
sudo nano /opt/dell_server_management/device/huawei-inverter/config/.env
# Set HUAWEI_INVERTER_HOST, WiFi AP; see device/huawei-inverter/README.md
sudo ./scripts/server/setup_huawei_wifi.sh   # if using USB WiFi → inverter AP
sudo ./install_huawei_service.sh
```

Re-run the device installer after editing `.env`. On first full install, `install.sh` already calls both installers (services may stay inactive until Modbus is reachable).

**Remote deploy from your PC:** see [scripts/server/README.md](../scripts/server/README.md) and [developer/SERVER_DEPLOY.md](developer/SERVER_DEPLOY.md).

On **192.168.2.4**, grant temporary sudo first (use **agent** mode for netplan/systemd/apt; **deploy** mode for script-only installs):

```bash
cd ~/ServerBootShutdownManagemement && sudo ./scripts/server/grant_temporary_agent_sudo.sh
```

### Step 2: Start Services

```bash
# Start all services
sudo systemctl start mqtt-boot-listener.service
sudo systemctl start mqtt-shutdown-listener.service
sudo systemctl start status-publisher.service
sudo systemctl start victron-mqtt-publisher.service
```

### Step 3: Verify Services

```bash
# Check status of all services
sudo systemctl status mqtt-boot-listener.service
sudo systemctl status mqtt-shutdown-listener.service
sudo systemctl status status-publisher.service
sudo systemctl status victron-mqtt-publisher.service
```

All services should show `active (running)`.

---

## Testing

### Test 1: IPMI Power Status

```bash
# Manually test IPMI
cd /opt/dell_server_management
source venv/bin/activate
python3 scripts/utils/ipmi_wrapper.py
```

### Test 2: MQTT Status Monitoring

```bash
# Subscribe to status topic
mosquitto_sub -h localhost -t "dell/t310/status" -u dell_t310 -P <password> -v
```

You should see status messages every 30 seconds.

### Test 3: Boot Command

**Warning:** This will boot your server!

```bash
# Send boot command via MQTT
mosquitto_pub -h localhost -t "dell/t310/command/boot" -u dell_t310 -P <password> -m '{
  "action": "boot",
  "method": "wol",
  "timestamp": "2025-12-25T20:00:00+02:00",
  "request_id": "test-boot-001"
}'
```

Check the response topic:

```bash
mosquitto_sub -h localhost -t "dell/t310/response" -u dell_t310 -P <password> -v
```

### Test 4: Shutdown Command

**Warning:** This will shutdown your server!

```bash
# Send graceful shutdown command
mosquitto_pub -h localhost -t "dell/t310/command/shutdown" -u dell_t310 -P <password> -m '{
  "action": "shutdown",
  "type": "graceful",
  "timeout": 300,
  "timestamp": "2025-12-25T20:00:00+02:00",
  "request_id": "test-shutdown-001"
}'
```

---

## Production Deployment

### Security Hardening

1. **Enable TLS for MQTT:**

```bash
# Generate certificates (example)
sudo openssl req -new -x509 -days 365 -extensions v3_ca -keyout /etc/mosquitto/ca.key -out /etc/mosquitto/ca.crt

# Update mqtt_config.yaml
sudo nano /opt/dell_server_management/config/mqtt_config.yaml
```

Set `tls.enabled: true` and configure certificate paths.

2. **Restrict IPMI Access:**

Use firewall rules to limit IPMI access to management network only:

```bash
sudo ufw allow from 192.168.1.0/24 to any port 623 proto udp
```

3. **Regular Updates:**

```bash
# Update system packages
sudo apt update && sudo apt upgrade

# Update Python packages
cd /opt/dell_server_management
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

### Monitoring

Set up log rotation:

```bash
sudo nano /etc/logrotate.d/dell_t310_management
```

Add:

```
/var/log/dell_t310_management.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

### Backup

Backup configuration files regularly:

```bash
# Create backup script
sudo nano /opt/dell_server_management/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/backup/dell_t310_management"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" /opt/dell_server_management/config/
```

---

## Next Steps

- Review [MQTT_PROTOCOL.md](MQTT_PROTOCOL.md) for message specifications
- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- Read [DEVELOPMENT_GUIDE.md](../DEVELOPMENT_GUIDE.md) for development details

---

**Setup complete!** Your Dell T310 management system is now ready for use.
