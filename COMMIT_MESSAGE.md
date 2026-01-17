# Commit Message for GitHub

## Title
```
Fix Dell T310 status monitoring and add management scripts
```

## Description
```
## Fixed Issues

### 1. Dell T310 "UNKNOWN" Status Notifications
- **Root Cause**: Multiple conflicting systems updating server state
  - Health monitor was using 'up'/'down' states
  - IPMI status publisher was using 'online'/'offline'/'unknown' states
  - IPMI connection timeouts causing intermittent failures
  
- **Solutions Implemented**:
  - Removed conflicting health monitor logic from Node-RED automation flow
  - Replaced unreliable IPMI with Proxmox API for Dell T310 status checking
  - Added automatic retry logic (3 attempts) for IPMI/iLO on other servers
  - Made MQTT status publisher the single source of truth for server states

### 2. Configuration Loss on Reinstall
- **Root Cause**: install.sh backed up directory before preserving .env file
- **Solution**: Fixed backup order and created dedicated update.sh script

## New Features

### Management Scripts
- **status.sh**: Quick status checker with colored output and log viewing
- **manage.sh**: Service management tool (start/stop/restart/enable/disable)
- **update.sh**: Safe update script that preserves all configuration

### Documentation
- **QUICK_REFERENCE.md**: Comprehensive command reference guide
- **UPDATE_GUIDE.md**: Detailed update instructions with best practices

## Modified Files

### Core Functionality
- `scripts/status/status_publisher.py`
  - Added `get_server_status_from_proxmox()` method
  - Dell T310 now uses Proxmox API instead of IPMI
  - Maintains backward compatibility for other servers

- `scripts/utils/ipmi_wrapper.py`
  - Added retry logic to `get_power_status()` method
  - Now retries failed IPMI commands up to 3 times with 1s delay

### Node-RED Flows
- `nodered/flows/41-client-automation.json`
  - Removed conflicting health monitor state updates
  - Standardized to use only 'online'/'offline'/'unknown'/'error' states

- `nodered/flows/50-telegram-interface.json`
  - Cleaned up state handling logic
  - Fixed notification text formatting

### Installation & Updates
- `install.sh`
  - Fixed .env preservation logic
  - Now correctly backs up config before directory move

## New Files

- `status.sh` - Service status checker
- `manage.sh` - Service management tool
- `update.sh` - Safe update script
- `QUICK_REFERENCE.md` - Quick command reference
- `UPDATE_GUIDE.md` - Detailed update guide

## Testing

Tested on production system:
- ✅ No more repeated "UNKNOWN" status notifications
- ✅ Dell T310 status via Proxmox API working reliably
- ✅ Configuration preserved during updates
- ✅ All services restart successfully
- ✅ Telegram notifications only on real state changes

## Breaking Changes

None. All changes are backward compatible.

## Migration Notes

After pulling these changes:
1. Run `sudo ./update.sh` to update the system
2. Configuration will be automatically preserved
3. Services will restart with new code
4. Use `./status.sh -l` to verify everything works

## Dependencies

Added requirement: `proxmoxer` (already in requirements.txt)
```

---

## Git Commands to Execute

```bash
# Stage all changes
git add .

# Commit with message
git commit -m "Fix Dell T310 status monitoring and add management scripts

- Fixed UNKNOWN status notifications by replacing IPMI with Proxmox API for Dell T310
- Removed conflicting health monitor state updates in Node-RED
- Added retry logic for IPMI commands on other servers
- Fixed configuration preservation in install.sh
- Added management scripts: status.sh, manage.sh, update.sh
- Added comprehensive documentation: QUICK_REFERENCE.md, UPDATE_GUIDE.md

Resolves repeated false UNKNOWN status alerts and configuration loss issues."

# Push to GitHub
git push origin main
```

Or if you have a different branch:
```bash
git push origin master
# or
git push origin <your-branch-name>
```
