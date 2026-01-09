# Quick Start - Client Management Features

## 🚀 Quick Reference

### Remote Shutdown

**Dashboard:** http://localhost:1880/dashboard → "Client Shutdown Control"

**Individual Shutdown:**
1. Find client in grid
2. Click "Graceful" or "Force"
3. Confirm

**Bulk Shutdown:**
1. Click "Graceful Shutdown All" or "Force Shutdown All"
2. Confirm

**Via MQTT:**
```bash
mosquitto_pub -h localhost -t "clients/CLIENT_ID/command/shutdown" \
  -m '{"action":"shutdown","type":"graceful","timestamp":"2026-01-09T15:30:00Z","request_id":"shutdown-001"}'
```

### Auto-Update

**Check Manually:**
1. Right-click system tray icon
2. Select "Check for Updates"

**Configure:**
```yaml
# client/config/client_config.yaml
client:
  auto_update:
    enabled: true
    check_interval_hours: 24
    github_repo: "owner/ServerBootShutdownMangement"
```

**Disable:**
```yaml
client:
  auto_update:
    enabled: false
```

### Monitoring

**Client Status:**
- Dashboard: "Client PCs" panel
- MQTT: `mosquitto_sub -h localhost -t "clients/+/presence"`

**Shutdown Responses:**
- Dashboard: Activity log in "Client Shutdown Control"
- MQTT: `mosquitto_sub -h localhost -t "clients/+/response"`

**Logs:**
```bash
# Client logs
tail -f client/logs/client_monitor.log

# Node-RED logs
docker logs -f nodered
```

## 📋 Configuration

### Minimal Setup

**client/config/.env:**
```bash
MQTT_BROKER_HOST=192.168.1.100
MQTT_BROKER_PORT=1883
MQTT_USERNAME=client_monitor
MQTT_PASSWORD=your_password
```

### With Auto-Update

**client/config/.env:**
```bash
MQTT_BROKER_HOST=192.168.1.100
MQTT_BROKER_PORT=1883
MQTT_USERNAME=client_monitor
MQTT_PASSWORD=your_password
AUTO_UPDATE_ENABLED=true
GITHUB_REPO=owner/ServerBootShutdownMangement
```

## 🔧 Troubleshooting

### Shutdown Not Working

```bash
# Check client is connected
mosquitto_sub -h localhost -t "clients/+/presence"

# Check client logs
tail -f client/logs/client_monitor.log

# Test MQTT
mosquitto_pub -h localhost -t "clients/test/command/shutdown" \
  -m '{"action":"shutdown","type":"graceful","timestamp":"2026-01-09T15:30:00Z","request_id":"test-001"}'
```

### Update Not Working

```bash
# Test manually
cd client
python auto_updater.py

# Check logs
tail -f client/logs/client_monitor.log | grep -i update

# Verify config
cat client/config/client_config.yaml | grep -A 3 auto_update
```

### Client Offline

```bash
# Check service status
sc query ClientMonitor

# Restart service
net stop ClientMonitor
net start ClientMonitor

# Check logs
type "C:\Program Files\ClientMonitor\logs\client_monitor.log"
```

## 📚 Documentation

- **Shutdown:** [client/README_CLIENT_SHUTDOWN.md](client/README_CLIENT_SHUTDOWN.md)
- **Auto-Update:** [client/README_AUTO_UPDATE.md](client/README_AUTO_UPDATE.md)
- **Complete Guide:** [CLIENT_MANAGEMENT_GUIDE.md](CLIENT_MANAGEMENT_GUIDE.md)
- **Release Notes:** [RELEASE_NOTES_v2.4.0.md](RELEASE_NOTES_v2.4.0.md)
- **MQTT Protocol:** [docs/MQTT_PROTOCOL.md](docs/MQTT_PROTOCOL.md)

## 🎯 Common Tasks

### Deploy Update to All Clients

1. Create GitHub release with version tag (e.g., v2.4.0)
2. Upload client ZIP package
3. Wait 24 hours for automatic updates
4. Or trigger manual check from each client

### Shutdown All Clients at End of Day

1. Open dashboard
2. Click "Graceful Shutdown All"
3. Confirm
4. Monitor activity log

### Check Client Status

1. Open dashboard
2. View "Client PCs" panel
3. Check last seen timestamps
4. Verify connection status

### Enable/Disable Auto-Update

**Disable:**
```yaml
client:
  auto_update:
    enabled: false
```

**Enable:**
```yaml
client:
  auto_update:
    enabled: true
```

Restart client after change.

## ⚠️ Important Notes

### Security

- Enable Node-RED authentication
- Use MQTT authentication (already configured)
- Secure network access (VPN, firewall)
- Monitor activity logs

### Shutdown Types

- **Graceful:** Saves applications, 30s delay
- **Force:** No save, 5s delay

### Update Timing

- Checks every 24 hours by default
- Manual check available in tray menu
- Service restarts during update

### Permissions

- Shutdown requires admin privileges
- Auto-update requires write access
- Service should run as admin

## 🆘 Emergency Procedures

### Client Won't Shutdown

1. Try force shutdown
2. If fails, manually shutdown:
   ```cmd
   shutdown /s /f /t 0
   ```

### Update Failed

1. Check logs for errors
2. Manual update:
   ```cmd
   net stop ClientMonitor
   # Extract new files
   net start ClientMonitor
   ```

### Service Won't Start

1. Check logs
2. Test manually:
   ```cmd
   cd "C:\Program Files\ClientMonitor"
   python client_monitor.py
   ```
3. Reinstall if needed:
   ```cmd
   install_client.bat
   ```

## 📞 Support

1. Check documentation
2. Review logs
3. Test MQTT connectivity
4. See [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

---

**Version:** 2.4.0  
**Last Updated:** January 9, 2026

