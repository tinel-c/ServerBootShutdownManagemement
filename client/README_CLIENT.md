# Client PC Monitor

Windows client application for the Server Boot/Shutdown Management System. Monitors PC state and sends MQTT signals to the automation server for automatic server power management.

## Features

- 🚀 **Automatic Startup** - Runs on Windows login via Task Scheduler
- 📡 **MQTT Communication** - Sends presence and heartbeat signals
- 🔄 **Auto-Reconnect** - Handles network interruptions gracefully
- 🎨 **System Tray Icon** - Color-coded status indicator with server information
- 📊 **Server Status Tracking** - Monitors target server state in real-time
- 📝 **Logging** - Detailed logs for troubleshooting
- ⚙️ **Easy Configuration** - Simple YAML with environment variable placeholder support
- ⏱️ **Heartbeat Countdown** - Real-time countdown to next heartbeat in tray icon
- 🛑 **Remote Shutdown** ⭐ NEW - Graceful and force shutdown via MQTT commands
- 🔄 **Auto-Update** ⭐ NEW - Automatic updates from GitHub releases
- 💾 **Application Save** ⭐ NEW - Saves open applications before shutdown

## Requirements

- **Windows 10/11** (or Windows Server 2016+)
- **Python 3.8+** installed and in PATH
- **Network access** to MQTT broker
- **Administrator privileges** for installation

## Installation

### Quick Install

1. **Download the client folder** to your Windows PC

2. **Run the installer as Administrator:**
   - Right-click `install_client.bat`
   - Select "Run as administrator"

3. **Follow the prompts** to configure MQTT connection:
   - MQTT Broker Host (e.g., `192.168.1.100`)
   - MQTT Broker Port (default: `1883`)
   - MQTT Username (default: `client_monitor`)
   - MQTT Password

4. **Restart your PC** or start manually:
   ```cmd
   python "C:\Program Files\ClientMonitor\client_monitor.py"
   ```

### Manual Installation

If you prefer manual installation:

1. **Install Python dependencies:**
   ```cmd
   pip install -r requirements_client.txt
   ```

2. **Configure MQTT settings:**
   - Copy `config\.env.example` to `config\.env`
   - Edit `config\.env` with your MQTT broker details

3. **Create startup task:**
   ```cmd
   schtasks /create /tn "ClientMonitor" /tr "python C:\path\to\client_monitor.py" /sc onlogon /rl highest
   ```

## Configuration

### Environment Variables (`.env`)

The `.env` file contains sensitive configuration that should not be committed to version control.

**Minimum Required Settings:**
```bash
MQTT_BROKER_HOST=192.168.1.100  # Your automation server IP
MQTT_BROKER_PORT=1883
MQTT_USERNAME=client_monitor
MQTT_PASSWORD=your_password_here
```

**Optional Settings:**
```bash
# Client Identification
CLIENT_CUSTOM_NAME=office-workstation-1  # Override hostname

# Target Server (for tray icon)
TARGET_SERVER=dell/t310  # Which server to monitor

# Heartbeat
HEARTBEAT_INTERVAL=60  # Seconds between heartbeats

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=  # Custom log path (optional)

# Advanced
ENABLE_TRAY_ICON=true  # Enable/disable system tray icon
MQTT_QOS=1  # MQTT quality of service (0, 1, or 2)
MQTT_KEEPALIVE=60  # Keepalive interval in seconds

# TLS/SSL (for secure MQTT)
MQTT_TLS_ENABLED=false
MQTT_TLS_CA_CERT=  # Path to CA certificate
MQTT_TLS_CLIENT_CERT=  # Path to client certificate (mutual TLS)
MQTT_TLS_CLIENT_KEY=  # Path to client key (mutual TLS)
```

See `config/.env.example` for complete documentation of all available options.

### Client Configuration (`client_config.yaml`)

```yaml
client:
  # Custom client name (optional, uses hostname if not set)
  custom_name: ""
  
  # Heartbeat interval in seconds
  heartbeat_interval: 60
  
  # Target server to monitor (for status display in tray icon)
  target_server: "dell/t310"

mqtt:
  broker:
    host: "${MQTT_BROKER_HOST:localhost}"
    port: ${MQTT_BROKER_PORT:1883}
  authentication:
    username: "${MQTT_USERNAME:}"
    password: "${MQTT_PASSWORD:}"
  topics:
    presence: "clients/{client_id}/presence"
    heartbeat: "clients/{client_id}/heartbeat"
  
  qos: 1
```

## System Tray Icon

The client application includes a system tray icon that provides at-a-glance status information.

### Icon Colors

The tray icon changes color based on the current status:

- 🔴 **Red** - Error state (connection failed)
- ⚫ **Gray** - Disconnected from MQTT broker
- 🟡 **Yellow** - Connected to broker, server status unknown
- 🟢 **Green** - Connected and server is ONLINE
- 🟠 **Orange** - Connected and server is OFFLINE

### Tooltip Information

Hover over the tray icon to see:
- Client ID
- Connection status
- Server status (online/offline/unknown)
- **Next heartbeat countdown**
- Recent requests (last 2 actions)

### Context Menu

Right-click the tray icon for options:
- **Status** - Show detailed status (future feature)
- **View Log** - Open the log file in default text editor
- **Quit** - Stop the client monitor and exit

### Running Without Tray Icon

To run the client without the system tray icon (console mode):
```cmd
python client_monitor.py --no-tray
```

---

## MQTT Topics

The client publishes to the following topics:

### Presence Topic: `clients/{client_id}/presence`

**Startup Message:**
```json
{
  "status": "online",
  "hostname": "DESKTOP-ABC123",
  "client_id": "desktop-abc123",
  "timestamp": "2026-01-06T17:30:00+02:00",
  "ip_address": "192.168.1.50"
}
```

**Shutdown Message:**
```json
{
  "status": "offline",
  "hostname": "DESKTOP-ABC123",
  "client_id": "desktop-abc123",
  "timestamp": "2026-01-06T18:30:00+02:00",
  "ip_address": "192.168.1.50"
}
```

### Heartbeat Topic: `clients/{client_id}/heartbeat`

**Heartbeat Message (every 60 seconds):**
```json
{
  "client_id": "desktop-abc123",
  "hostname": "DESKTOP-ABC123",
  "timestamp": "2026-01-06T17:31:00+02:00",
  "uptime": 3600
}
```

## Verification

### Check Installation

1. **Verify Task Scheduler entry:**
   ```cmd
   schtasks /query /tn "ClientMonitor"
   ```

2. **Check log file:**
   ```cmd
   type "C:\Program Files\ClientMonitor\logs\client_monitor.log"
   ```

3. **Monitor MQTT messages:**
   ```bash
   mosquitto_sub -h <broker> -t "clients/#" -v
   ```

### Expected Behavior

- ✅ Application starts automatically on login
- ✅ Presence message sent on startup
- ✅ Heartbeat messages sent every 60 seconds
- ✅ Shutdown message sent before PC powers off
- ✅ Automatic reconnection if MQTT connection lost

## Troubleshooting

### Client Not Starting

**Check Python installation:**
```cmd
python --version
```

**Check Task Scheduler:**
- Open Task Scheduler (`taskschd.msc`)
- Look for "ClientMonitor" task
- Check "Last Run Result" (should be 0x0 for success)

**Check logs:**
```cmd
type "C:\Program Files\ClientMonitor\logs\client_monitor.log"
```

### MQTT Connection Failed

**Verify broker is reachable:**
```cmd
ping <broker_host>
telnet <broker_host> 1883
```

**Check credentials:**
- Verify username/password in `.env` file
- Test with mosquitto_pub:
  ```cmd
  mosquitto_pub -h <broker> -u <username> -P <password> -t "test" -m "hello"
  ```

### Messages Not Appearing

**Check MQTT broker logs:**
```bash
journalctl -u mosquitto -f
```

**Use MQTT Explorer:**
- Download MQTT Explorer
- Connect to broker
- Subscribe to `clients/#`
- Restart client PC and watch for messages

## Uninstallation

### Automatic Uninstallation (Recommended)

1. **Navigate to the client directory** where you originally installed from

2. **Run the uninstall script as Administrator:**
   ```cmd
   Right-click uninstall_client.bat → Run as administrator
   ```

3. **Confirm uninstallation** when prompted

4. **Done!** The script will:
   - Stop the client monitor if running
   - Remove Task Scheduler entry
   - Delete installation directory and all files
   - Clean up configuration and logs

### Manual Uninstallation

If you prefer to uninstall manually or the script fails:

1. **Stop the client monitor** (if running):
   ```cmd
   taskkill /F /IM python.exe /FI "WINDOWTITLE eq Client*"
   ```

2. **Delete Task Scheduler entry:**
   ```cmd
   schtasks /delete /tn "ClientMonitor" /f
   ```

3. **Remove installation directory:**
   ```cmd
   rmdir /s "C:\Program Files\ClientMonitor"
   ```

### What Gets Removed

The uninstallation process removes:
- ✓ Client Monitor application files
- ✓ Configuration files (`.env`, `client_config.yaml`)
- ✓ Log files
- ✓ Task Scheduler entry
- ✓ VBScript wrapper for hidden execution

**What Remains:**
- Python installation (if you want to keep it)
- MQTT broker (on automation server)
- Node-RED flows (on automation server)

### Reinstallation

To reinstall after uninstalling:
1. Run `install_client.bat` again
2. Reconfigure MQTT settings when prompted
3. Restart PC or start manually

## File Structure

```
client/
├── client_monitor.py           # Main application
├── install_client.bat          # Installation script
├── uninstall_client.bat        # Uninstallation script
├── requirements_client.txt     # Python dependencies
├── config/
│   ├── client_config.yaml      # Client configuration
│   ├── .env.example            # Example environment file
│   └── .env                    # Actual credentials (created during install)
├── logs/
│   └── client_monitor.log      # Application logs
└── README_CLIENT.md            # This file
```

## Security Considerations

⚠️ **Important:**
- Store MQTT credentials securely in `.env` file
- Use strong MQTT passwords
- Consider enabling MQTT TLS/SSL for production
- Restrict MQTT user permissions to publish-only on client topics

## Support

For issues and questions:
- Check the main [README.md](../README.md)
- Review [TROUBLESHOOTING.md](../docs/TROUBLESHOOTING.md)
- Check application logs in `logs/client_monitor.log`

## Version

**Version:** 2.2.0  
**Last Updated:** 2026-01-07
