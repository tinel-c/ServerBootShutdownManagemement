# Auto-Update Feature Guide

## Overview

The Client Monitor includes an automatic update system that checks GitHub for new releases and installs them automatically. This ensures all clients stay up-to-date with the latest features and security patches.

## Features

### 1. Automatic Update Checks
- Periodic checks for new releases (default: every 24 hours)
- Compares semantic versions (e.g., 2.3.0 vs 2.4.0)
- Caches last check time to avoid excessive API calls
- Respects GitHub API rate limits

### 2. Automatic Installation
- Downloads update packages from GitHub releases
- Extracts and applies updates
- Restarts client service automatically
- Minimal downtime during update

### 3. Manual Update Checks
- System tray menu option: "Check for Updates"
- Forces immediate check regardless of interval
- Useful for testing or urgent updates

## Configuration

### Enable/Disable Auto-Update

Edit `client/config/client_config.yaml`:

```yaml
client:
  auto_update:
    enabled: true  # Set to false to disable
    check_interval_hours: 24  # Hours between checks
    github_repo: "owner/ServerBootShutdownMangement"  # Your repo
```

### Environment Variables

Set in `client/config/.env`:

```bash
# Auto-update settings
AUTO_UPDATE_ENABLED=true
AUTO_UPDATE_CHECK_INTERVAL=24
GITHUB_REPO=owner/ServerBootShutdownMangement
```

### GitHub Repository Setup

The auto-updater expects:
1. GitHub releases with semantic versioning (e.g., v2.4.0)
2. Release assets containing a client package ZIP file
3. ZIP file name must contain "client" (e.g., `client-v2.4.0.zip`)
4. ZIP must contain `update_client_files.bat` script

## How It Works

### Update Check Process

1. **Timing**: Checks occur during heartbeat loop (every 24 hours by default)
2. **API Call**: Queries GitHub API for latest release
3. **Version Compare**: Compares current version with latest
4. **Decision**: If newer version available, proceeds to download

### Download Process

1. **Download**: Fetches ZIP file from GitHub release assets
2. **Verify**: Checks file integrity
3. **Extract**: Unzips to temporary directory
4. **Prepare**: Locates update script

### Installation Process

1. **Execute**: Runs `update_client_files.bat` script
2. **Copy Files**: Script copies new files over old ones
3. **Restart**: Stops and starts client service
4. **Cleanup**: Removes temporary files

### Update Script Format

The `update_client_files.bat` script should:

```batch
@echo off
echo Updating Client Monitor...

REM Stop service
net stop ClientMonitor

REM Copy files
xcopy /Y /E /I ".\client\*" "C:\Program Files\ClientMonitor\"

REM Start service
net start ClientMonitor

echo Update complete!
```

## Creating GitHub Releases

### 1. Prepare Release Package

```bash
# Create client package directory
mkdir client-v2.4.0
cd client-v2.4.0

# Copy client files
cp -r ../client/* .

# Create update script
cat > update_client_files.bat << 'EOF'
@echo off
echo Applying Client Monitor Update v2.4.0...
timeout /t 2 /nobreak >nul

REM Backup current installation
if exist "C:\Program Files\ClientMonitor\backup" (
    rmdir /s /q "C:\Program Files\ClientMonitor\backup"
)
mkdir "C:\Program Files\ClientMonitor\backup"
xcopy /Y /E /I "C:\Program Files\ClientMonitor\*" "C:\Program Files\ClientMonitor\backup\"

REM Stop service
net stop ClientMonitor 2>nul

REM Copy new files
xcopy /Y /E /I ".\*" "C:\Program Files\ClientMonitor\"

REM Start service
timeout /t 2 /nobreak >nul
net start ClientMonitor

echo Update completed successfully!
EOF

# Create ZIP
cd ..
zip -r client-v2.4.0.zip client-v2.4.0/
```

### 2. Create GitHub Release

1. Go to your repository on GitHub
2. Click "Releases" → "Create a new release"
3. Tag version: `v2.4.0`
4. Release title: `Client Monitor v2.4.0`
5. Description: List changes and improvements
6. Upload `client-v2.4.0.zip` as release asset
7. Publish release

### 3. Version Numbering

Follow semantic versioning:
- **Major** (X.0.0): Breaking changes, major features
- **Minor** (2.X.0): New features, backward compatible
- **Patch** (2.4.X): Bug fixes, minor improvements

Examples:
- `v2.3.0` → `v2.4.0`: New shutdown feature (minor)
- `v2.4.0` → `v2.4.1`: Bug fix (patch)
- `v2.4.1` → `v3.0.0`: Complete rewrite (major)

## Monitoring Updates

### Client Logs

Updates are logged in `client/logs/client_monitor.log`:

```
2026-01-09 15:30:00 - INFO - Checking for updates (current version: 2.3.0)
2026-01-09 15:30:02 - INFO - Update available: 2.3.0 -> 2.4.0
2026-01-09 15:30:05 - INFO - Update downloaded successfully
2026-01-09 15:30:10 - INFO - Update installed successfully. Application will restart.
```

### System Tray

The system tray icon shows update activity:
- "Checking updates..." - Check in progress
- "Update: 2.4.0" - Update available/downloaded
- Recent requests list shows update events

### Update Cache

Status cached in `client/.update_cache.json`:

```json
{
  "last_check": "2026-01-09T15:30:00",
  "latest_version": "2.4.0",
  "current_version": "2.3.0"
}
```

## Troubleshooting

### Update Check Fails

**Symptoms**: No updates detected despite new release

**Solutions**:
1. Check GitHub repository URL in config
2. Verify release has client ZIP asset
3. Check GitHub API rate limit:
   ```bash
   curl https://api.github.com/rate_limit
   ```
4. Review client logs for errors
5. Test manually:
   ```bash
   python client/auto_updater.py
   ```

### Download Fails

**Symptoms**: Update detected but download fails

**Solutions**:
1. Check internet connectivity
2. Verify GitHub release asset URL
3. Check disk space in temp directory
4. Review firewall/proxy settings
5. Try manual download to test

### Installation Fails

**Symptoms**: Download succeeds but installation fails

**Solutions**:
1. Check Windows permissions (requires admin)
2. Verify update script is in ZIP
3. Test update script manually
4. Check if service is running
5. Review Windows Event Viewer

### Service Won't Restart

**Symptoms**: Update completes but service doesn't start

**Solutions**:
1. Check service status:
   ```cmd
   sc query ClientMonitor
   ```
2. Start manually:
   ```cmd
   net start ClientMonitor
   ```
3. Check service dependencies
4. Review service configuration
5. Check for file permission issues

### Updates Disabled

**Symptoms**: No update checks occurring

**Solutions**:
1. Verify `auto_update.enabled: true` in config
2. Check if auto-updater module loaded:
   ```
   # Look for this in logs:
   Auto-updater initialized (check interval: 24h)
   ```
3. Ensure `requests` and `packaging` packages installed:
   ```bash
   pip install -r client/requirements_client.txt
   ```

## Security Considerations

### GitHub Authentication

For private repositories, use GitHub token:

```python
# In auto_updater.py, add to headers:
headers = {
    'Accept': 'application/vnd.github.v3+json',
    'Authorization': f'token {GITHUB_TOKEN}'
}
```

Set token in environment:
```bash
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
```

### Signature Verification

For enhanced security, verify release signatures:

1. Sign releases with GPG
2. Include signature in release assets
3. Verify signature before installation
4. Reject unsigned or invalid updates

### Rollback Capability

The update script includes backup:

```batch
REM Rollback if update fails
if errorlevel 1 (
    echo Update failed, rolling back...
    xcopy /Y /E /I "C:\Program Files\ClientMonitor\backup\*" "C:\Program Files\ClientMonitor\"
    net start ClientMonitor
    exit /b 1
)
```

## Best Practices

### Testing Updates

Before releasing:
1. Test update package on development machine
2. Verify all files are included
3. Test update script execution
4. Confirm service restarts correctly
5. Check logs for errors

### Release Notes

Include in GitHub release description:
- New features
- Bug fixes
- Breaking changes
- Migration steps (if any)
- Known issues

### Gradual Rollout

For large deployments:
1. Release to test group first
2. Monitor for issues
3. Gradually expand to more clients
4. Keep previous version available

### Update Scheduling

Consider update timing:
- Default 24-hour interval is reasonable
- Avoid peak usage hours
- Consider time zones for global deployments
- Allow manual override for urgent updates

## Disabling Auto-Update

To disable auto-update:

### Method 1: Configuration File

```yaml
client:
  auto_update:
    enabled: false
```

### Method 2: Environment Variable

```bash
AUTO_UPDATE_ENABLED=false
```

### Method 3: Remove Module

```bash
# Rename or delete auto_updater.py
mv client/auto_updater.py client/auto_updater.py.disabled
```

## Manual Update Process

If auto-update is disabled:

1. Download latest release from GitHub
2. Stop client service:
   ```cmd
   net stop ClientMonitor
   ```
3. Extract ZIP to installation directory
4. Start client service:
   ```cmd
   net start ClientMonitor
   ```

## Version History

- **v2.4.0** (2026-01-09)
  - Initial release of auto-update feature
  - GitHub integration
  - Automatic installation
  - Manual check option

## Related Documentation

- [Client Monitor README](README_CLIENT.md) - Client setup
- [Development Guide](../DEVELOPMENT_GUIDE.md) - Development workflow
- [Troubleshooting](../docs/TROUBLESHOOTING.md) - System troubleshooting

## Support

For issues:
1. Check `client/logs/client_monitor.log`
2. Test with `python client/auto_updater.py`
3. Verify GitHub release format
4. Review update script execution

