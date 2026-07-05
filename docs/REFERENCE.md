# Quick Reference Guide

Quick commands for managing the Server Management System.

## 🚀 Quick Start Scripts

### Check Status
```bash
./status.sh              # Show service status (+ media server config when MEDIA_SERVER_HOST is set)
./status.sh -l           # Show status + recent logs (10 lines)
./status.sh -l -n 20     # Show status + recent logs (20 lines)
./status.sh -a           # Show everything (status, logs, commands)
```

### Manage Services
```bash
sudo ./manage.sh start    # Start all services
sudo ./manage.sh stop     # Stop all services
sudo ./manage.sh restart  # Restart all services
sudo ./manage.sh status   # Show status (same as ./status.sh)
sudo ./manage.sh logs     # Show live logs
```

### Enable/Disable Auto-Start
```bash
sudo ./manage.sh enable   # Enable services on boot
sudo ./manage.sh disable  # Disable services on boot
```

---

## 📦 Installation & Updates

### First Installation
```bash
sudo ./install.sh
```

### Update System (Preserves Configuration)
```bash
git pull
sudo ./update.sh
```

---

## 🔍 Troubleshooting Commands

### Check Individual Service
```bash
systemctl status status-publisher.service
systemctl status mqtt-boot-listener.service
systemctl status mqtt-shutdown-listener.service
systemctl status health-monitor.service
```

### View Live Logs
```bash
sudo journalctl -u status-publisher.service -f        # Follow logs
sudo journalctl -u status-publisher.service -n 50     # Last 50 lines
sudo journalctl -u status-publisher.service --since "10 minutes ago"
```

### Check for Errors
```bash
sudo journalctl -u status-publisher.service -p err -n 20
```

### Restart Specific Service
```bash
sudo systemctl restart status-publisher.service
```

---

## 📂 Important Directories

| Path | Description |
|------|-------------|
| `/opt/dell_server_management/` | Installation directory |
| `/opt/dell_server_management/config/.env` | Environment variables & credentials |
| `/opt/dell_server_management/config/*.yaml` | Configuration files |
| `/opt/dell_server_management/scripts/` | Python scripts |
| `/etc/systemd/system/*.service` | Service definitions |
| `/var/log/dell_server_management.log` | Application log file |

---

## 📝 Configuration Files

### Edit Configuration
```bash
sudo nano /opt/dell_server_management/config/.env
sudo nano /opt/dell_server_management/config/mqtt_config.yaml
sudo nano /opt/dell_server_management/config/server_config.yaml
```

### After Editing Configuration
```bash
sudo ./manage.sh restart  # Apply changes
```

---

## 🔧 Service Management (Systemctl)

### Manual Service Control
```bash
# Start
sudo systemctl start mqtt-boot-listener.service
sudo systemctl start mqtt-shutdown-listener.service
sudo systemctl start status-publisher.service
sudo systemctl start health-monitor.service

# Stop
sudo systemctl stop mqtt-boot-listener.service
sudo systemctl stop mqtt-shutdown-listener.service
sudo systemctl stop status-publisher.service
sudo systemctl stop health-monitor.service

# Restart
sudo systemctl restart status-publisher.service

# Enable on boot
sudo systemctl enable status-publisher.service

# Disable on boot
sudo systemctl disable status-publisher.service
```

---

## 📊 Monitoring

### Check Proxmox API Status (Dell T310)
```bash
sudo journalctl -u status-publisher.service | grep "Proxmox API"
```

Should see:
```
Dell T310 is ONLINE (via Proxmox API)
```
or
```
Dell T310 is OFFLINE (via Proxmox API)
```

### Check for IPMI Errors
```bash
sudo journalctl -u status-publisher.service | grep -i "unable to establish"
```

Should see NO errors for Dell T310 (now using Proxmox API).

### Monitor MQTT Messages
```bash
# Install mosquitto-clients if not already installed
sudo apt-get install mosquitto-clients

# Subscribe to all topics
mosquitto_sub -h localhost -t '#' -v

# Subscribe to specific server
mosquitto_sub -h localhost -t 'dell/t310/#' -v
```

---

## 🆘 Common Issues

### Service Won't Start
```bash
# Check detailed logs
sudo journalctl -u status-publisher.service -n 100

# Check configuration
sudo cat /opt/dell_server_management/config/.env

# Verify Python environment
ls -la /opt/dell_server_management/venv/

# Reinstall dependencies
cd /opt/dell_server_management
source venv/bin/activate
pip install -r requirements.txt
```

### Configuration Lost After Update
```bash
# Check backup
ls -la /tmp/dell_server_management_env.bak*
ls -la /tmp/server_management_config_backup_*

# Restore from backup
sudo cp /tmp/dell_server_management_env.bak /opt/dell_server_management/config/.env
sudo chmod 600 /opt/dell_server_management/config/.env
sudo ./manage.sh restart
```

### Telegram Notifications Not Working
```bash
# Check Node-RED
sudo systemctl status nodered

# Check Node-RED logs
journalctl -u nodered -f

# Check if bot token is set
sudo grep TELEGRAM /opt/dell_server_management/config/.env
```

---

## 🎯 Testing Commands

### Test MQTT Publishing
```bash
# Publish test message
mosquitto_pub -h localhost -t 'test/message' -m '{"test": "data"}'
```

### Test Server Boot (from Python scripts)
```bash
cd /opt/dell_server_management
source venv/bin/activate
python3 scripts/boot/wol_boot.py  # For testing WOL
```

### Test Status Check
```bash
cd /opt/dell_server_management
source venv/bin/activate
python3 scripts/status/status_publisher.py  # Run once manually
```

---

## 📱 Telegram Bot Commands

| Command | Description |
|---------|-------------|
| `/start` or `/help` | Show help message |
| `/status` | Get current server status |
| `/boot [dell\|hp]` | Boot a server |
| `/shutdown [dell\|hp]` | Graceful shutdown |
| `/force [dell\|hp]` | Force shutdown (dangerous) |

### Victron energy (v3.11.6+)

| Command | Description |
|---------|-------------|
| `/energy_status` | Battery, grid, PV, load, headroom, inverter |
| `/energy_start` | Start discretionary loads (when PV surplus) |
| `/energy_stop` | Stop discretionary loads |
| `/energy_help` | Victron energy help + buttons |

### Huawei energy (v3.11.8+)

| Command | Description |
|---------|-------------|
| `/huawei_status` | Model, PV strings, active power, daily yield |
| `/huawei_help` | Huawei solar help |

See [TELEGRAM_INTERFACE.md](TELEGRAM_INTERFACE.md) and [ENERGY_NODE_RED.md](ENERGY_NODE_RED.md).

---

## 🔄 Update Workflow

```bash
# 1. Pull latest changes
cd /path/to/ServerBootShutdownMangement
git pull

# 2. Run update script
sudo ./update.sh

# 3. Check status
./status.sh -l

# 4. Test functionality
# - Check Telegram bot responds
# - Verify status monitoring works
# - Check logs for errors
```

---

## 📚 Additional Documentation

- `README.md` - Full documentation
- `UPDATE_GUIDE.md` - Detailed update instructions
- `TROUBLESHOOTING.md` - Troubleshooting guide
- `docs/ARCHITECTURE.md` - System architecture
- `docs/MQTT_PROTOCOL.md` - MQTT protocol specification

---

## 💡 Pro Tips

1. **Always use `./status.sh -l` after making changes** to verify everything works
2. **Use `./manage.sh restart` instead of manual systemctl commands** for convenience
3. **Check logs with timestamps:** `sudo journalctl -u status-publisher.service -o short-iso`
4. **Create aliases** for frequently used commands:
   ```bash
   echo "alias srvstatus='cd /path/to/repo && ./status.sh -l'" >> ~/.bashrc
   echo "alias srvrestart='cd /path/to/repo && sudo ./manage.sh restart'" >> ~/.bashrc
   source ~/.bashrc
   ```
5. **Monitor in real-time** with `watch`: `watch -n 5 './status.sh'`

---

## 🚨 Emergency Commands

### All Services Not Responding
```bash
sudo ./manage.sh stop
sudo systemctl daemon-reload
sudo ./manage.sh start
./status.sh -l
```

### Restore from Backup
```bash
# Find latest backup
ls -lah /opt/dell_server_management.backup.*

# Stop services
sudo ./manage.sh stop

# Restore
sudo mv /opt/dell_server_management /opt/dell_server_management.failed
sudo mv /opt/dell_server_management.backup.YYYYMMDD_HHMMSS /opt/dell_server_management

# Start services
sudo ./manage.sh start
```

### Complete Reinstall
```bash
sudo ./manage.sh stop
sudo rm -rf /opt/dell_server_management
sudo ./install.sh
# Edit configuration
sudo nano /opt/dell_server_management/config/.env
sudo ./manage.sh start
```

---

## ✅ Health Check Checklist

- [ ] All services running: `./status.sh`
- [ ] No errors in logs: `./status.sh -l`
- [ ] Telegram bot responds: Send `/status` to bot
- [ ] Status updates working: Check Telegram notifications
- [ ] Configuration preserved: `ls -la /opt/dell_server_management/config/.env`
- [ ] Proxmox API working: `sudo journalctl -u status-publisher.service | grep Proxmox`

---

**Need Help?** Check the full documentation in `README.md` or review logs with `./status.sh -a`
