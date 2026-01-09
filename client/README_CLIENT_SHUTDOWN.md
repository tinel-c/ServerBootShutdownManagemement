# Client Shutdown Feature Guide

## Overview

The Client Shutdown feature allows remote shutdown of Windows client PCs via MQTT commands from the Node-RED dashboard. This enables centralized management of all connected client machines.

## Features

### 1. Remote Shutdown Control
- **Graceful Shutdown**: Attempts to save all open applications before shutting down
- **Force Shutdown**: Immediate shutdown without saving
- **Individual Control**: Shutdown specific clients
- **Bulk Operations**: Shutdown all connected clients at once

### 2. Application Save Logic
The graceful shutdown process:
1. Receives shutdown command via MQTT
2. Sends Ctrl+S to all open application windows
3. Waits 3 seconds for applications to save
4. Sends offline presence message
5. Executes Windows shutdown command with 30-second delay

### 3. Response Tracking
Clients send multiple response messages during shutdown:
- **Acknowledged**: Command received and validated
- **Executing**: Shutdown process initiated
- **Error**: If shutdown fails

## Configuration

### Client Configuration

Edit `client/config/client_config.yaml`:

```yaml
mqtt:
  topics:
    shutdown: "clients/{client_id}/command/shutdown"
    response: "clients/{client_id}/response"
```

### Environment Variables

No additional environment variables required. Uses existing MQTT configuration.

## MQTT Protocol

### Shutdown Command Message

**Topic:** `clients/{client_id}/command/shutdown`

**Payload:**
```json
{
  "action": "shutdown",
  "type": "graceful|force",
  "timestamp": "2026-01-09T15:30:00+02:00",
  "request_id": "shutdown-desktop-abc123-1736429400"
}
```

### Response Messages

**Topic:** `clients/{client_id}/response`

**Acknowledgment:**
```json
{
  "request_id": "shutdown-desktop-abc123-1736429400",
  "action": "shutdown",
  "success": true,
  "message": "Shutdown command acknowledged (graceful)",
  "timestamp": "2026-01-09T15:30:01+02:00",
  "client_id": "desktop-abc123",
  "hostname": "DESKTOP-ABC123"
}
```

**Execution:**
```json
{
  "request_id": "shutdown-desktop-abc123-1736429400",
  "action": "shutdown",
  "success": true,
  "message": "Initiating graceful shutdown now",
  "timestamp": "2026-01-09T15:30:05+02:00",
  "client_id": "desktop-abc123",
  "hostname": "DESKTOP-ABC123"
}
```

## Node-RED Dashboard

### Client Shutdown Control Panel

The dashboard provides:

1. **Client Grid**
   - Shows all connected clients
   - Displays hostname, IP address, and uptime
   - Individual shutdown buttons (Graceful/Force)

2. **Bulk Actions**
   - Shutdown All (Graceful)
   - Shutdown All (Force)
   - Confirmation dialogs for safety

3. **Activity Log**
   - Recent shutdown operations
   - Timestamps and status
   - Success/failure indicators

### Using the Dashboard

1. Navigate to Node-RED dashboard: `http://localhost:1880/dashboard`
2. Scroll to "Client Shutdown Control" section
3. Select a client or use bulk actions
4. Confirm the shutdown operation
5. Monitor status in the activity log

## Security Considerations

### Access Control

⚠️ **Important**: The shutdown feature has no built-in authentication. Secure your Node-RED installation:

1. **Enable Node-RED Authentication**:
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

2. **Use MQTT Authentication**:
   Already configured in `client_config.yaml`:
   ```yaml
   mqtt:
     authentication:
       username: "${MQTT_USERNAME:}"
       password: "${MQTT_PASSWORD:}"
   ```

3. **Network Security**:
   - Use VPN for remote access
   - Firewall MQTT port (1883) from external networks
   - Consider MQTT over TLS (port 8883)

### Confirmation Dialogs

The dashboard includes confirmation dialogs for all shutdown operations:
- Individual shutdowns: "Are you sure you want to [type] shutdown [hostname]?"
- Bulk shutdowns: "Are you sure you want to [type] shutdown ALL [count] clients?"

## Troubleshooting

### Shutdown Command Not Received

**Symptoms**: Client doesn't respond to shutdown command

**Solutions**:
1. Check MQTT broker is running: `docker ps | grep mosquitto`
2. Verify client is connected: Check Node-RED "Client PCs" panel
3. Check client logs: `client/logs/client_monitor.log`
4. Test MQTT connectivity:
   ```bash
   mosquitto_sub -h localhost -t "clients/+/response" -v
   ```

### Application Save Not Working

**Symptoms**: Applications don't save before shutdown

**Solutions**:
1. Some applications may not respond to Ctrl+S
2. Increase save delay in `client_monitor.py`:
   ```python
   time.sleep(3)  # Increase to 5 or more
   ```
3. Use Force Shutdown if graceful fails
4. Check PowerShell execution policy:
   ```powershell
   Get-ExecutionPolicy
   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

### Shutdown Fails to Execute

**Symptoms**: Client acknowledges but doesn't shut down

**Solutions**:
1. Check Windows permissions (requires admin for shutdown)
2. Review client logs for error messages
3. Test manual shutdown:
   ```cmd
   shutdown /s /t 30
   ```
4. Verify client service is running as admin

### Dashboard Shows "Shutting Down" Forever

**Symptoms**: Status doesn't clear after 30 seconds

**Solutions**:
1. This is expected if client actually shut down (can't send final response)
2. Status auto-clears after 30 seconds
3. Refresh dashboard to update client list
4. Check if client went offline in "Client PCs" panel

## Implementation Details

### Client-Side Components

1. **MQTT Subscription**: `client_monitor.py` subscribes to shutdown commands
2. **Message Handler**: `_on_message()` processes shutdown commands
3. **Shutdown Thread**: `_handle_shutdown_command()` executes shutdown
4. **Application Save**: `_save_open_applications()` sends Ctrl+S
5. **System Shutdown**: `_execute_system_shutdown()` calls Windows shutdown

### Server-Side Components

1. **Node-RED Flow**: `42-client-shutdown.json`
2. **UI Template**: Vue.js-based control panel
3. **Command Processor**: Formats and publishes MQTT messages
4. **Response Handler**: Processes client responses
5. **Client Sync**: Maintains client list from tracking flow

## Best Practices

### When to Use Graceful vs Force

**Use Graceful Shutdown When**:
- Normal end-of-day shutdown
- Scheduled maintenance
- Saving work is important
- Users may have unsaved documents

**Use Force Shutdown When**:
- Client is unresponsive
- Emergency situations
- Graceful shutdown failed
- No critical work in progress

### Bulk Shutdown Considerations

Before using bulk shutdown:
1. Verify all clients in list are intended targets
2. Notify users if possible
3. Consider time of day (avoid during work hours)
4. Use graceful type unless emergency
5. Monitor activity log for failures

### Scheduled Shutdowns

For automated shutdowns, use Node-RED scheduling:

```javascript
// Example: Shutdown all clients at 6 PM daily
// Add an inject node with cron: 0 18 * * *
// Connect to shutdown function
```

## Version History

- **v2.4.0** (2026-01-09)
  - Initial release of client shutdown feature
  - Graceful and force shutdown support
  - Application save logic
  - Node-RED control panel
  - Response tracking

## Related Documentation

- [Client Monitor README](README_CLIENT.md) - Client setup and configuration
- [MQTT Protocol](../docs/MQTT_PROTOCOL.md) - Complete MQTT specification
- [Node-RED Development](../nodered/NODE_RED_DEVELOPMENT.md) - Dashboard customization
- [Troubleshooting Guide](../docs/TROUBLESHOOTING.md) - System-wide troubleshooting

## Support

For issues or questions:
1. Check client logs: `client/logs/client_monitor.log`
2. Check Node-RED debug panel
3. Review MQTT messages with MQTT Explorer
4. See [TROUBLESHOOTING.md](../docs/TROUBLESHOOTING.md)

