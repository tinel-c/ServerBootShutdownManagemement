# Release Notes - Version 2.4.0

**Release Date:** January 9, 2026

## Overview

Version 2.4.0 introduces major new features for client management, including remote shutdown capabilities, automatic updates, and enhanced application save logic. This release significantly expands the system's ability to manage Windows client PCs remotely.

## 🎉 New Features

### 1. Remote Client Shutdown

Complete remote shutdown control for Windows client PCs via MQTT.

**Features:**
- **Graceful Shutdown**: Attempts to save all open applications before shutting down
- **Force Shutdown**: Immediate shutdown without saving for unresponsive clients
- **Individual Control**: Shutdown specific clients from Node-RED dashboard
- **Bulk Operations**: Shutdown all connected clients at once
- **Response Tracking**: Real-time status updates during shutdown process
- **Activity Logging**: Complete audit trail of shutdown operations

**Technical Details:**
- New MQTT topics: `clients/{client_id}/command/shutdown` and `clients/{client_id}/response`
- Application save via PowerShell SendKeys (Ctrl+S to all windows)
- 30-second graceful shutdown delay, 5-second force shutdown delay
- Multiple response messages: acknowledgment, execution, and error states

**Documentation:** See `client/README_CLIENT_SHUTDOWN.md`

### 2. Automatic Updates

Self-updating client system that checks GitHub for new releases.

**Features:**
- **Automatic Checks**: Periodic update checks (default: every 24 hours)
- **Semantic Versioning**: Intelligent version comparison (e.g., 2.3.0 vs 2.4.0)
- **Auto-Install**: Downloads and installs updates automatically
- **Manual Override**: System tray menu option for immediate checks
- **Update Caching**: Avoids excessive GitHub API calls
- **Service Restart**: Automatically restarts client after update

**Technical Details:**
- GitHub API integration for release checking
- ZIP package download and extraction
- Batch script execution for file updates
- Rollback capability on failure
- Update status logging and notification

**Documentation:** See `client/README_AUTO_UPDATE.md`

### 3. Node-RED Client Shutdown Panel

Beautiful, modern control panel for managing client shutdowns.

**Features:**
- **Client Grid**: Visual display of all connected clients
- **Status Indicators**: Real-time uptime and connection status
- **Confirmation Dialogs**: Safety prompts before shutdown operations
- **Activity Log**: Recent shutdown history with timestamps
- **Responsive Design**: Modern gradient UI with animations
- **Live Updates**: Real-time status changes and response tracking

**Location:** Node-RED Dashboard → "Client Shutdown Control" section

### 4. Enhanced System Tray

Improved system tray icon with additional functionality.

**Changes:**
- **New Name**: Changed from "python" to "ClientServerBootShutdownManagement"
- **Update Menu**: New "Check for Updates" menu option
- **Update Notifications**: Shows update availability in recent requests
- **Better Identification**: More descriptive process name in Task Manager

## 🔧 Improvements

### Client Monitor

- **Threading**: Shutdown operations run in separate thread to avoid blocking
- **Error Handling**: Improved error messages and recovery
- **Logging**: Enhanced logging for shutdown and update operations
- **Configuration**: New auto-update settings in `client_config.yaml`

### MQTT Protocol

- **New Topics**: Added shutdown command and response topics
- **Message Format**: Standardized shutdown message schema
- **Response Tracking**: Multiple response messages for better status tracking
- **Documentation**: Updated MQTT protocol specification

### Node-RED Flows

- **New Flow**: `42-client-shutdown.json` for shutdown control
- **Integration**: Seamless integration with existing client tracking
- **UI Components**: Modern Vue.js templates with gradient design
- **Error Handling**: Graceful handling of offline clients

## 📦 Dependencies

### New Python Packages

Added to `client/requirements_client.txt`:
- `requests>=2.31.0` - For GitHub API and download
- `packaging>=23.0` - For semantic version comparison

### Installation

```bash
pip install -r client/requirements_client.txt
```

## 🔄 Migration Guide

### From v2.3.0 to v2.4.0

#### 1. Update Client Configuration

Add auto-update settings to `client/config/client_config.yaml`:

```yaml
client:
  auto_update:
    enabled: true
    check_interval_hours: 24
    github_repo: "owner/ServerBootShutdownMangement"
```

#### 2. Install New Dependencies

```bash
cd client
pip install -r requirements_client.txt
```

#### 3. Import New Node-RED Flow

1. Open Node-RED: http://localhost:1880
2. Import `nodered/flows/42-client-shutdown.json`
3. Deploy changes

#### 4. Configure GitHub Repository

If using auto-update:
1. Set `GITHUB_REPO` environment variable
2. Ensure releases follow semantic versioning
3. Include client ZIP in release assets

#### 5. Restart Client Service

```cmd
net stop ClientMonitor
net start ClientMonitor
```

## 🔒 Security Considerations

### Shutdown Feature

⚠️ **Important**: The shutdown feature has no built-in authentication.

**Recommendations:**
1. Enable Node-RED authentication
2. Use MQTT authentication (already configured)
3. Secure network access (VPN, firewall)
4. Monitor shutdown activity logs

### Auto-Update Feature

**Recommendations:**
1. Use private GitHub repository for sensitive deployments
2. Consider signature verification for releases
3. Test updates on development machines first
4. Keep backup of previous version

## 📝 Configuration Changes

### New Configuration Options

**client/config/client_config.yaml:**
```yaml
mqtt:
  topics:
    shutdown: "clients/{client_id}/command/shutdown"
    response: "clients/{client_id}/response"

client:
  auto_update:
    enabled: true
    check_interval_hours: 24
    github_repo: "owner/ServerBootShutdownMangement"
```

**Environment Variables:**
```bash
AUTO_UPDATE_ENABLED=true
AUTO_UPDATE_CHECK_INTERVAL=24
GITHUB_REPO=owner/ServerBootShutdownMangement
```

## 🐛 Bug Fixes

- Fixed system tray icon name showing as "python"
- Improved MQTT reconnection handling
- Enhanced error logging for network issues
- Fixed tooltip truncation on long client IDs

## 📚 Documentation Updates

### New Documentation

- `client/README_CLIENT_SHUTDOWN.md` - Complete shutdown feature guide
- `client/README_AUTO_UPDATE.md` - Auto-update system documentation
- `nodered/flows/42-client-shutdown.json` - New Node-RED flow

### Updated Documentation

- `docs/MQTT_PROTOCOL.md` - Added shutdown command and response schemas
- `nodered/flows/README.md` - Added client shutdown flow documentation
- `client/README_CLIENT.md` - Updated feature list

## 🔍 Known Issues

### Windows Permissions

- Shutdown requires administrator privileges
- Auto-update requires write access to installation directory
- Some applications may not respond to Ctrl+S save command

**Workarounds:**
- Run client service as administrator
- Install to user directory instead of Program Files
- Use force shutdown for unresponsive applications

### GitHub API Rate Limits

- Anonymous API calls limited to 60/hour
- Authenticated calls limited to 5000/hour

**Workarounds:**
- Use GitHub token for authentication (private repos)
- Increase check interval to reduce API calls
- Cache update information locally

### Network Interruptions

- Shutdown commands may be lost during network outage
- Update downloads may fail on unstable connections

**Workarounds:**
- Retry failed operations
- Monitor client logs for errors
- Use manual update process if auto-update fails

## 🚀 Upgrade Instructions

### Automatic Upgrade (Recommended)

If you have v2.3.0 with auto-update enabled:
1. Wait for automatic update check (within 24 hours)
2. Or use "Check for Updates" from system tray menu
3. Update will install automatically
4. Client will restart

### Manual Upgrade

1. **Download v2.4.0** from GitHub releases

2. **Stop Client Service:**
   ```cmd
   net stop ClientMonitor
   ```

3. **Backup Current Installation:**
   ```cmd
   xcopy /E /I "C:\Program Files\ClientMonitor" "C:\Program Files\ClientMonitor.backup"
   ```

4. **Extract New Version:**
   - Extract ZIP to `C:\Program Files\ClientMonitor`
   - Overwrite existing files

5. **Update Configuration:**
   - Add auto-update settings to `client_config.yaml`
   - Set `GITHUB_REPO` in `.env` if using auto-update

6. **Install Dependencies:**
   ```cmd
   cd "C:\Program Files\ClientMonitor"
   pip install -r requirements_client.txt
   ```

7. **Import Node-RED Flow:**
   - Open Node-RED: http://localhost:1880
   - Import `42-client-shutdown.json`
   - Deploy

8. **Start Client Service:**
   ```cmd
   net start ClientMonitor
   ```

9. **Verify Installation:**
   - Check system tray icon (should show new name)
   - Check logs for auto-updater initialization
   - Test shutdown from Node-RED dashboard

## 🎯 Testing Checklist

After upgrade, verify:

- [ ] Client connects to MQTT broker
- [ ] System tray icon shows correct name
- [ ] Heartbeat messages sent successfully
- [ ] Server status updates in tray icon
- [ ] "Check for Updates" menu option appears
- [ ] Node-RED shows client in "Client PCs" panel
- [ ] Shutdown panel displays connected clients
- [ ] Graceful shutdown works (test on non-critical client)
- [ ] Force shutdown works
- [ ] Shutdown responses appear in activity log
- [ ] Auto-update check runs (check logs after 24 hours)

## 📊 Performance Impact

### Resource Usage

- **Memory**: +5-10 MB for auto-updater module
- **CPU**: Negligible (update checks run in background)
- **Network**: ~100 KB per update check (GitHub API)
- **Disk**: ~50 MB for downloaded update packages (temporary)

### Timing

- **Shutdown Delay**: 
  - Graceful: ~35 seconds (3s save + 30s shutdown + 2s messaging)
  - Force: ~8 seconds (5s shutdown + 3s messaging)
- **Update Check**: ~2-5 seconds (GitHub API call)
- **Update Download**: Varies by package size and connection speed
- **Update Install**: ~10-30 seconds (extract + copy + restart)

## 🔮 Future Enhancements

Planned for future releases:

- **v2.5.0**: Client configuration management from dashboard
- **v2.6.0**: Client groups for bulk operations
- **v2.7.0**: Scheduled shutdown tasks
- **v3.0.0**: Cross-platform support (Linux, macOS)

## 📞 Support

### Getting Help

1. **Documentation**: Check README files in `client/` directory
2. **Logs**: Review `client/logs/client_monitor.log`
3. **MQTT**: Use MQTT Explorer to monitor messages
4. **Node-RED**: Check debug panel for errors

### Reporting Issues

When reporting issues, include:
- Version number (2.4.0)
- Operating system and version
- Client logs (last 100 lines)
- MQTT broker logs (if relevant)
- Steps to reproduce

### Contact

- GitHub Issues: [Repository Issues Page]
- Documentation: See `docs/TROUBLESHOOTING.md`

## 🙏 Acknowledgments

Special thanks to all contributors and testers who helped make this release possible.

## 📜 License

This project is licensed under the MIT License. See LICENSE file for details.

---

**Version:** 2.4.0  
**Release Date:** January 9, 2026  
**Previous Version:** 2.3.0  
**Next Version:** TBD

