# Client Management Guide

## Overview

This guide covers the complete client management features introduced in v2.4.0, including remote shutdown and automatic updates.

## Quick Links

- [Client Shutdown Guide](client/README_CLIENT_SHUTDOWN.md) - Remote shutdown feature
- [Auto-Update Guide](client/README_AUTO_UPDATE.md) - Automatic update system
- [Client Setup](client/README_CLIENT.md) - Initial client installation
- [MQTT Protocol](docs/MQTT_PROTOCOL.md) - Complete protocol specification

## Features Summary

### 1. Remote Shutdown Control

Shutdown Windows client PCs remotely from the Node-RED dashboard.

**Key Features:**
- Graceful shutdown with application save
- Force shutdown for unresponsive clients
- Individual and bulk operations
- Real-time status tracking
- Activity logging

**Use Cases:**
- End-of-day shutdown automation
- Emergency shutdown during incidents
- Maintenance window preparation
- Power management

**Dashboard Location:** Node-RED → "Client Shutdown Control"

### 2. Automatic Updates

Self-updating client system that keeps all clients current.

**Key Features:**
- Automatic GitHub release checking
- Semantic version comparison
- Automatic download and installation
- Manual check option in system tray
- Rollback on failure

**Use Cases:**
- Deploying bug fixes
- Rolling out new features
- Security patch distribution
- Maintaining consistency across clients

**Configuration:** `client/config/client_config.yaml`

### 3. Application Save Logic

Graceful shutdown attempts to save all open applications.

**How It Works:**
1. PowerShell sends Ctrl+S to all windows
2. 3-second delay for save operations
3. Offline presence message sent
4. Windows shutdown initiated (30s delay)

**Limitations:**
- Not all applications respond to Ctrl+S
- Some applications may show save dialogs
- User interaction may be required
- Use force shutdown if graceful fails

## Architecture

### Client-Side Components

```
client_monitor.py
├── MQTT Subscription (shutdown commands)
├── Message Handler (_on_message)
├── Shutdown Thread (_handle_shutdown_command)
├── Application Save (_save_open_applications)
├── System Shutdown (_execute_system_shutdown)
└── Response Publisher (_send_shutdown_response)

auto_updater.py
├── Update Checker (check_for_updates)
├── Version Comparator (packaging.version)
├── Downloader (download_update)
├── Installer (install_update)
└── Cache Manager (.update_cache.json)
```

### Server-Side Components

```
Node-RED Flows
├── 40-client-tracking.json (presence/heartbeat)
├── 41-client-automation.json (server automation)
└── 42-client-shutdown.json (shutdown control)
    ├── UI Template (Vue.js control panel)
    ├── Command Processor (MQTT publisher)
    ├── Response Handler (status tracking)
    └── Client Sync (list management)
```

### MQTT Topics

```
Client → Server:
  clients/{client_id}/presence      # Online/offline status
  clients/{client_id}/heartbeat     # Periodic heartbeat
  clients/{client_id}/response      # Command responses

Server → Client:
  clients/{client_id}/command/shutdown  # Shutdown commands
```

## Configuration

### Client Configuration

**File:** `client/config/client_config.yaml`

```yaml
client:
  # Basic settings
  custom_name: "${CLIENT_CUSTOM_NAME:}"
  heartbeat_interval: ${HEARTBEAT_INTERVAL:60}
  target_server: "${TARGET_SERVER:dell/t310}"
  debug: ${DEBUG:false}
  
  # Auto-update settings
  auto_update:
    enabled: ${AUTO_UPDATE_ENABLED:true}
    check_interval_hours: ${AUTO_UPDATE_CHECK_INTERVAL:24}
    github_repo: "${GITHUB_REPO:}"

mqtt:
  broker:
    host: "${MQTT_BROKER_HOST:localhost}"
    port: ${MQTT_BROKER_PORT:1883}
    keepalive: 60
  
  authentication:
    username: "${MQTT_USERNAME:}"
    password: "${MQTT_PASSWORD:}"
  
  topics:
    presence: "clients/{client_id}/presence"
    heartbeat: "clients/{client_id}/heartbeat"
    shutdown: "clients/{client_id}/command/shutdown"
    response: "clients/{client_id}/response"
  
  qos: 1
```

### Environment Variables

**File:** `client/config/.env`

```bash
# MQTT Connection
MQTT_BROKER_HOST=192.168.1.100
MQTT_BROKER_PORT=1883
MQTT_USERNAME=client_monitor
MQTT_PASSWORD=your_password

# Client Identity
CLIENT_CUSTOM_NAME=office-workstation-1

# Auto-Update
AUTO_UPDATE_ENABLED=true
AUTO_UPDATE_CHECK_INTERVAL=24
GITHUB_REPO=owner/ServerBootShutdownMangement

# Optional
TARGET_SERVER=dell/t310
HEARTBEAT_INTERVAL=60
DEBUG=false
```

## Usage

### Shutting Down Clients

#### Individual Shutdown

1. Open Node-RED dashboard: `http://localhost:1880/dashboard`
2. Scroll to "Client Shutdown Control"
3. Find the target client in the grid
4. Click "Graceful" or "Force" button
5. Confirm the operation
6. Monitor status in activity log

#### Bulk Shutdown

1. Open Node-RED dashboard
2. Scroll to "Client Shutdown Control"
3. Click "Graceful Shutdown All" or "Force Shutdown All"
4. Confirm the operation
5. Monitor status for each client

#### Via MQTT Command

```bash
# Graceful shutdown
mosquitto_pub -h localhost -t "clients/desktop-abc123/command/shutdown" \
  -m '{"action":"shutdown","type":"graceful","timestamp":"2026-01-09T15:30:00Z","request_id":"shutdown-001"}'

# Force shutdown
mosquitto_pub -h localhost -t "clients/desktop-abc123/command/shutdown" \
  -m '{"action":"shutdown","type":"force","timestamp":"2026-01-09T15:30:00Z","request_id":"shutdown-002"}'
```

### Managing Updates

#### Automatic Updates

Updates check automatically every 24 hours (configurable). No user action required.

**Monitor Updates:**
- Check client logs: `client/logs/client_monitor.log`
- Watch system tray: Recent requests show "Update: X.X.X"
- Review update cache: `client/.update_cache.json`

#### Manual Update Check

**From System Tray:**
1. Right-click system tray icon
2. Select "Check for Updates"
3. Wait for check to complete
4. Update installs automatically if available

**From Command Line:**
```bash
cd client
python auto_updater.py
```

#### Disabling Auto-Update

**Method 1 - Configuration:**
```yaml
client:
  auto_update:
    enabled: false
```

**Method 2 - Environment:**
```bash
AUTO_UPDATE_ENABLED=false
```

### Creating GitHub Releases

For administrators deploying updates:

1. **Prepare Package:**
   ```bash
   # Create client package
   mkdir client-v2.4.0
   cp -r client/* client-v2.4.0/
   
   # Create update script
   cat > client-v2.4.0/update_client_files.bat << 'EOF'
   @echo off
   net stop ClientMonitor
   xcopy /Y /E /I ".\*" "C:\Program Files\ClientMonitor\"
   net start ClientMonitor
   EOF
   
   # Create ZIP
   zip -r client-v2.4.0.zip client-v2.4.0/
   ```

2. **Create Release:**
   - Go to GitHub repository
   - Releases → New release
   - Tag: `v2.4.0`
   - Upload `client-v2.4.0.zip`
   - Publish

3. **Clients Update:**
   - Within 24 hours, all clients check for updates
   - Download and install automatically
   - Service restarts
   - Update complete

## Monitoring

### Client Status

**Node-RED Dashboard:**
- "Client PCs" panel shows all connected clients
- Hostname, IP address, last seen timestamp
- Real-time connection status

**MQTT Topics:**
```bash
# Monitor presence
mosquitto_sub -h localhost -t "clients/+/presence" -v

# Monitor heartbeats
mosquitto_sub -h localhost -t "clients/+/heartbeat" -v

# Monitor responses
mosquitto_sub -h localhost -t "clients/+/response" -v
```

### Shutdown Operations

**Activity Log:**
- Shows last 5 shutdown operations
- Timestamp, client, type, status
- Clear button to reset log

**Client Logs:**
```
2026-01-09 15:30:00 - WARNING - Shutdown command received: graceful (request_id: shutdown-001)
2026-01-09 15:30:01 - INFO - Processing shutdown command: graceful
2026-01-09 15:30:01 - INFO - Saving open applications...
2026-01-09 15:30:05 - INFO - Sending offline presence message...
2026-01-09 15:30:06 - INFO - Executing GRACEFUL shutdown...
```

### Update Operations

**Client Logs:**
```
2026-01-09 14:00:00 - INFO - Checking for updates (current version: 2.3.0)
2026-01-09 14:00:02 - INFO - Update available: 2.3.0 -> 2.4.0
2026-01-09 14:00:05 - INFO - Downloading update from: https://github.com/...
2026-01-09 14:00:10 - INFO - Update downloaded successfully
2026-01-09 14:00:15 - INFO - Update installed successfully. Application will restart.
```

**Update Cache:**
```json
{
  "last_check": "2026-01-09T14:00:00",
  "latest_version": "2.4.0",
  "current_version": "2.3.0"
}
```

## Security

### Access Control

**Node-RED Authentication:**

Edit `nodered/settings.js`:
```javascript
adminAuth: {
    type: "credentials",
    users: [{
        username: "admin",
        password: "$2b$08$...",  // bcrypt hash
        permissions: "*"
    }]
}
```

Generate password hash:
```bash
node-red admin hash-pw
```

**MQTT Authentication:**

Already configured in client. Ensure broker requires authentication:
```bash
# Mosquitto config
allow_anonymous false
password_file /etc/mosquitto/passwd
```

**Network Security:**
- Use VPN for remote access
- Firewall MQTT port (1883) externally
- Consider MQTT over TLS (port 8883)
- Restrict Node-RED dashboard access

### Audit Trail

All operations logged:
- Client presence changes
- Shutdown commands and responses
- Update checks and installations
- Errors and failures

**Review Logs:**
```bash
# Client logs
tail -f client/logs/client_monitor.log

# Node-RED logs
docker logs -f nodered

# MQTT broker logs
docker logs -f mosquitto
```

## Troubleshooting

### Common Issues

#### Shutdown Command Not Received

**Symptoms:** Client doesn't respond to shutdown

**Solutions:**
1. Verify client is connected (check "Client PCs" panel)
2. Check MQTT broker: `docker ps | grep mosquitto`
3. Review client logs for errors
4. Test MQTT connectivity: `mosquitto_sub -h localhost -t "clients/+/response"`

#### Application Save Fails

**Symptoms:** Applications don't save before shutdown

**Solutions:**
1. Some apps don't respond to Ctrl+S
2. Increase save delay in code (default: 3 seconds)
3. Use force shutdown if graceful fails
4. Check PowerShell execution policy

#### Update Check Fails

**Symptoms:** No updates detected despite new release

**Solutions:**
1. Verify GitHub repository URL in config
2. Check release has client ZIP asset
3. Review GitHub API rate limit
4. Test manually: `python client/auto_updater.py`

#### Update Installation Fails

**Symptoms:** Download succeeds but installation fails

**Solutions:**
1. Check Windows permissions (requires admin)
2. Verify update script in ZIP
3. Test update script manually
4. Check service status: `sc query ClientMonitor`

### Debug Mode

Enable debug logging:

```yaml
client:
  debug: true
```

Or:
```bash
DEBUG=true
```

Restart client to apply. Logs will include detailed debug information.

### Manual Recovery

If client becomes unresponsive:

1. **Stop Service:**
   ```cmd
   net stop ClientMonitor
   ```

2. **Check Logs:**
   ```cmd
   type "C:\Program Files\ClientMonitor\logs\client_monitor.log"
   ```

3. **Test Manually:**
   ```cmd
   cd "C:\Program Files\ClientMonitor"
   python client_monitor.py
   ```

4. **Reinstall if Needed:**
   ```cmd
   cd "C:\Program Files\ClientMonitor"
   install_client.bat
   ```

## Best Practices

### Shutdown Operations

1. **Use Graceful by Default:** Always try graceful shutdown first
2. **Notify Users:** Warn users before remote shutdown if possible
3. **Avoid Peak Hours:** Schedule shutdowns during off-hours
4. **Monitor Results:** Check activity log for failures
5. **Have Rollback Plan:** Be prepared to manually restart if needed

### Update Management

1. **Test First:** Test updates on development machines
2. **Gradual Rollout:** Deploy to small groups first
3. **Monitor Logs:** Watch for update failures
4. **Keep Backups:** Maintain previous version for rollback
5. **Document Changes:** Include clear release notes

### Client Deployment

1. **Standardize Config:** Use same settings across clients
2. **Document Hostnames:** Maintain list of client IDs
3. **Monitor Connectivity:** Set up alerts for offline clients
4. **Regular Maintenance:** Review logs periodically
5. **Security Audits:** Review access controls regularly

## Performance

### Resource Usage

**Per Client:**
- Memory: ~50 MB (including Python runtime)
- CPU: <1% (idle), ~5% (during operations)
- Network: ~1 KB/minute (heartbeats)
- Disk: ~100 MB (installation + logs)

**Shutdown Operations:**
- Graceful: ~35 seconds total
- Force: ~8 seconds total
- Network: ~2 KB per operation

**Update Operations:**
- Check: ~2-5 seconds, ~100 KB
- Download: Varies by package size
- Install: ~10-30 seconds

### Scalability

**Tested Configurations:**
- Up to 50 clients per MQTT broker
- Up to 100 clients per Node-RED instance
- Heartbeat interval: 60 seconds recommended
- Update check: 24 hours recommended

**Recommendations:**
- Use dedicated MQTT broker for >50 clients
- Increase heartbeat interval for >100 clients
- Stagger update checks to avoid API rate limits
- Monitor broker resource usage

## Related Documentation

- [Client Setup Guide](client/README_CLIENT.md)
- [Shutdown Feature Guide](client/README_CLIENT_SHUTDOWN.md)
- [Auto-Update Guide](client/README_AUTO_UPDATE.md)
- [MQTT Protocol](docs/MQTT_PROTOCOL.md)
- [Node-RED Development](nodered/NODE_RED_DEVELOPMENT.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Release Notes v2.4.0](RELEASE_NOTES_v2.4.0.md)

## Support

For assistance:
1. Review relevant documentation
2. Check client and server logs
3. Test MQTT connectivity
4. Verify configuration settings
5. See troubleshooting guide

---

**Last Updated:** January 9, 2026  
**Version:** 2.4.0

