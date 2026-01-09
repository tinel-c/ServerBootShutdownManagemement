# System Tray Tooltip Feature Guide

This guide explains the enhanced system tray tooltip feature that displays version information and update scheduling.

## Overview

The client application now shows detailed version information and update scheduling directly in the system tray tooltip when you hover over the icon. This provides at-a-glance information about your client version and when the next update check will occur.

## Tooltip Information Display

### Example Tooltip (Up to Date)

```
CM: desktop-workstation
v2.4.0 (up to date)
Broker: OK
Srv: ONLINE
HB: 45s
Update chk: 23h 15m
Last: 10:30:45 - Heartbeat
```

### Example Tooltip (Update Available)

```
CM: office-pc-01
v2.4.0 → v2.5.0 ⚠
Broker: OK
Srv: ONLINE
HB: 30s
Update chk: 2h 30m
Last: 10:31:20 - Update: 2.5.0
```

### Example Tooltip (First Run)

```
CM: laptop-home
v2.4.0
Broker: OK
Srv: UNKNOWN
HB: 60s
Update chk: Pending
```

## Tooltip Fields Explained

### Line 1: Client Identification
- **Format:** `CM: {client_id}`
- **Example:** `CM: desktop-workstation`
- Shows your configured client ID (custom name or hostname)
- Long names are truncated with "..." to fit

### Line 2: Version Information
Shows one of three states:

#### 1. Update Available
- **Format:** `v{current} → v{latest} ⚠`
- **Example:** `v2.4.0 → v2.5.0 ⚠`
- Warning symbol (⚠) indicates an update is available
- Shows version progression arrow (→)

#### 2. Up to Date
- **Format:** `v{current} (up to date)`
- **Example:** `v2.4.0 (up to date)`
- Confirms you're running the latest version

#### 3. Version Unknown
- **Format:** `v{current}`
- **Example:** `v2.4.0`
- Shown when GitHub version hasn't been checked yet

### Line 3: Broker Connection Status
- **Broker: OK** - Connected to MQTT broker successfully
- **Broker: OFF** - Disconnected from MQTT broker
- **Broker: ERR** - Connection error occurred

### Line 4: Server Status
- **Srv: ONLINE** - Target server is running
- **Srv: OFFLINE** - Target server is shut down
- **Srv: UNKNOWN** - Server status not yet determined

### Line 5: Heartbeat Countdown
- **Format:** `HB: {seconds}s`
- **Example:** `HB: 45s`
- Shows seconds until next heartbeat is sent
- Updates in real-time every second

### Line 6: Next Update Check
Shows time remaining until the next automatic update check:

#### Time Formats
- **Days:** `Update chk: 5d` (when > 24 hours remain)
- **Hours:** `Update chk: 23h 15m` (when < 24 hours remain)
- **Minutes:** `Update chk: 45m` (when < 1 hour remains)
- **Soon:** `Update chk: Soon` (check is imminent)
- **Pending:** `Update chk: Pending` (no check performed yet)

### Line 7: Last Action (Optional)
- **Format:** `Last: {timestamp} - {action}`
- **Example:** `Last: 10:30:45 - Heartbeat`
- Shows the most recent activity
- Only displayed if space permits (within 128 char limit)

## Configuration

### Update Check Interval

The update check interval is configured in `client_config.yaml`:

```yaml
client:
  auto_update:
    enabled: true
    check_interval_hours: 24  # Check every 24 hours
```

**Common Intervals:**
- `1` - Check every hour (frequent, for testing)
- `6` - Check every 6 hours (active monitoring)
- `24` - Check daily (default, recommended)
- `168` - Check weekly (minimal checking)

### Disabling Auto-Update

To disable automatic updates but keep version display:

```yaml
client:
  auto_update:
    enabled: false
```

Note: Version information will still be displayed in the tooltip, but automatic updates won't be installed.

## Manual Update Check

You can manually trigger an update check at any time:

1. **Right-click** the system tray icon
2. Select **"Check for Updates"**
3. Watch the tooltip for results

The tooltip will update to show:
- "Checking updates..." (during check)
- New version information (if update found)
- "Up to date" (if no update available)

## Update Notifications

When an update is available, you'll see:

1. **Tooltip Change:** Version line changes to `v2.4.0 → v2.5.0 ⚠`
2. **Recent Activity:** Shows `Update: 2.5.0` in last action
3. **Icon Update:** Tray icon updates to reflect new status

## Character Limit Optimization

The tooltip is optimized for Windows' 128-character limit:

- **Version info:** Concise format with symbols
- **Update time:** Shortened to "Update chk"
- **Recent actions:** Limited to last 1 action
- **Smart truncation:** Automatically shortens long names

If the tooltip exceeds 128 characters, it will be truncated with "..." to ensure compatibility.

## Troubleshooting

### Version Shows as "?"

**Cause:** GitHub version hasn't been fetched yet

**Solution:**
1. Wait for automatic check (based on interval)
2. Manually check for updates via context menu
3. Check internet connectivity

### Update Check Shows "Pending"

**Cause:** First run or cache cleared

**Solution:**
- This is normal on first run
- Wait for first automatic check
- Manually trigger check via context menu

### Tooltip Not Updating

**Cause:** Icon refresh issue

**Solution:**
1. Move mouse away and hover again
2. Restart the client application
3. Check logs for errors

### Update Available But Not Installing

**Cause:** Auto-update might be disabled or installation failed

**Solution:**
1. Check `auto_update.enabled` in config
2. Review logs at `logs/client_monitor.log`
3. Manually trigger update check
4. Check GitHub release assets are available

## Benefits

✅ **Instant Visibility** - Know your version at a glance  
✅ **Update Awareness** - See when updates are available immediately  
✅ **Predictable Updates** - Know exactly when next check will occur  
✅ **Manual Control** - Trigger checks on demand  
✅ **Version History** - Track current and available versions  

## Related Documentation

- [Auto-Update System](README_AUTO_UPDATE.md) - Detailed auto-update documentation
- [Client README](README_CLIENT.md) - Main client documentation
- [Troubleshooting](../docs/TROUBLESHOOTING.md) - General troubleshooting guide

## Version History

- **v2.4.0** - Initial implementation of version and update time display in tooltip
- **v2.4.0** - Added update available indicator (⚠)
- **v2.4.0** - Added "up to date" status display

---

**Last Updated:** January 9, 2026  
**Feature Version:** 2.4.0+

