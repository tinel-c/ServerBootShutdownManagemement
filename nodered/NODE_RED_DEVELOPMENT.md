# Node-RED Development Guide

## Overview

This document describes how to develop, update, and maintain the Node-RED dashboard for the Server Boot/Shutdown Management system. The dashboard has been refactored from a monolithic approach to a modular, feature-based architecture.

## Architecture

### Modular Design Philosophy

The Node-RED flows are now organized into separate, importable feature modules:

- **Base Configuration**: Core UI and MQTT broker setup
- **Dell T310 Features**: Control buttons, status display, and health monitoring
- **HP DL360p Features**: Control buttons, status display, and health monitoring
- **Log Console**: Centralized logging display

This modular approach provides:
- ✅ Easier maintenance and updates
- ✅ Independent feature development
- ✅ Simplified testing and debugging
- ✅ Better version control and collaboration
- ✅ Reusable components for future servers

## File Structure

```
nodered/
├── flows.json                  # Legacy monolithic flows (deprecated)
├── flows/                      # Modular feature-based flows
│   ├── 00-base-config.json     # Base UI, page, and MQTT broker
│   ├── 10-dell-controls.json   # Dell T310 boot/shutdown buttons
│   ├── 11-dell-status.json     # Dell T310 status display
│   ├── 12-dell-health.json     # Dell T310 health monitoring
│   ├── 20-hp-controls.json     # HP DL360p boot/shutdown buttons
│   ├── 21-hp-status.json       # HP DL360p status display
│   ├── 22-hp-health.json       # HP DL360p health monitoring
│   └── 90-log-console.json     # System log console
└── NODE_RED_DEVELOPMENT.md     # This file
```

### Naming Convention

Flow files follow a numbered prefix system:
- `00-09`: Core infrastructure (base, config, MQTT)
- `10-19`: Dell server features
- `20-29`: HP server features
- `30-39`: Reserved for future server type 1
- `40-49`: Reserved for future server type 2
- `90-99`: Shared utilities (logs, notifications)

## Getting Started

### Prerequisites

1. **Node-RED** installed on Ubuntu
2. **MQTT Broker** running (localhost:1883)
3. **Node-RED Dashboard 2.0** (@flowfuse/node-red-dashboard) installed in Node-RED

### Initial Setup

1. **Ensure Node-RED is Running**:
   ```bash
   sudo systemctl status nodered
   # If not running:
   sudo systemctl start nodered
   ```

2. **Access Node-RED Editor**:
   - Open browser: http://localhost:1880

3. **Import Base Configuration**:
   - Click menu (≡) → Import
   - Select `flows/00-base-config.json`
   - Click "Import"

4. **Import Feature Modules** (in order):
   - `10-dell-controls.json`
   - `11-dell-status.json`
   - `12-dell-health.json`
   - `20-hp-controls.json`
   - `21-hp-status.json`
   - `22-hp-health.json`
   - `90-log-console.json`

5. **Deploy**:
   - Click "Deploy" button (top right)

## Development Workflow

### Adding a New Feature

1. **Create Feature Branch** (Git workflow):
   ```bash
   git checkout -b feature/new-server-controls
   ```

2. **Design in Node-RED Editor**:
   - Build and test your feature in the editor
   - Keep related nodes together
   - Use consistent naming conventions

3. **Export Feature Module**:
   - Select all nodes for the feature
   - Click menu → Export → Clipboard
   - Save to new file: `flows/30-newserver-controls.json`

4. **Test Independently**:
   - Create fresh Node-RED instance
   - Import base config + your new feature only
   - Verify functionality

5. **Document**:
   - Add entry to this file
   - Update README if user-facing changes

### Modifying Existing Features

1. **Identify Feature Module**:
   - Locate the appropriate `.json` file in `flows/`

2. **Make Changes in Editor**:
   - Import the feature module
   - Make your modifications
   - Test thoroughly

3. **Export Updated Module**:
   - Select all nodes in the feature
   - Export and overwrite the original file
   - **Important**: Keep node IDs consistent

4. **Version Control**:
   - Commit changes with descriptive message
   - Include before/after screenshots if UI changes

### Best Practices

#### Node Organization
- **Group related nodes**: Use the same `z` (flow ID)
- **Consistent naming**: Use descriptive names with server prefix
  - Example: `btn_dell_boot`, `mqtt_out_hp`, `func_dell_status_metadata`
- **Logical positioning**: Arrange nodes left-to-right following data flow

#### Configuration Nodes
- **Shared MQTT Broker**: All features should reference `mqtt_broker_local`
- **UI Groups**: Each server should have separate groups
  - Control group: `ui_group_dell`
  - Status group: Same parent group
  - Health group: `ui_group_dell_health`

#### MQTT Topics
Follow the established pattern:
```
{server}/{model}/command/{action}     # Commands to backend
{server}/{model}/status               # Status updates from backend
{server}/{model}/health               # Health check data
system/logs                           # Centralized logging
```

#### Function Nodes
- **Add comments**: Explain complex logic
- **Use flow context**: For persistent data across messages
- **Error handling**: Always include try-catch for robustness

#### UI Templates
- **Responsive design**: Use flexbox/grid layouts
- **Consistent styling**: Match existing color scheme
- **Vue.js components**: Leverage Dashboard 2.0 reactivity
- **Performance**: Avoid heavy computations in templates

## Feature Module Reference

### 00-base-config.json

**Purpose**: Core infrastructure setup

**Contains**:
- `ui_base`: Dashboard base configuration
- `ui_page_home`: Main page definition
- `ui_group_*`: UI group containers
- `mqtt_broker_local`: MQTT broker connection
- `tab_dashboard`: Main tab

**Dependencies**: None (must be imported first)

**Customization Points**:
- Dashboard path: Change `path` in `ui_base`
- MQTT broker: Update `broker` and `port` in `mqtt_broker_local`
- Theme: Modify `theme` in `ui_page_home`

### 10-dell-controls.json

**Purpose**: Boot and shutdown buttons for Dell T310

**Contains**:
- `btn_dell_boot`: WOL boot button
- `btn_dell_shutdown`: Graceful shutdown button
- `btn_dell_force_shutdown`: Force shutdown button
- `mqtt_out_dell`: MQTT output node

**Dependencies**: 
- Requires `ui_group_dell` from base config
- Requires `mqtt_broker_local` from base config

**MQTT Topics**:
- `dell/t310/command/boot`
- `dell/t310/command/shutdown`

**Customization Points**:
- Button labels and tooltips
- Button colors (bgcolor)
- Icons (Material Design Icons)
- Payload structure

### 11-dell-status.json

**Purpose**: Real-time status display for Dell T310

**Contains**:
- `mqtt_in_dell_status`: Status subscription
- `func_dell_status_metadata`: Metadata tracking (last report, state changes)
- `template_dell_status`: Vue.js status UI

**Dependencies**:
- Requires `ui_group_dell` from base config
- Requires `mqtt_broker_local` from base config

**MQTT Topics**:
- Subscribes to: `dell/t310/status`

**Features**:
- Color-coded state indicator (green=online, red=offline, orange=unknown)
- Last report timestamp (human-readable)
- State change tracking
- Auto-refresh every second

**Customization Points**:
- Color scheme in computed `statusStyle`
- Additional metrics in metadata function
- UI layout in template

### 12-dell-health.json

**Purpose**: Comprehensive health monitoring dashboard for Dell T310

**Contains**:
- `mqtt_in_dell_health`: Health data subscription
- `ui_template_dell_health`: Advanced health monitoring UI with full data display

**Dependencies**:
- Requires `ui_group_dell_health` from base config
- Requires `mqtt_broker_local` from base config

**MQTT Topics**:
- Subscribes to: `dell/t310/health`

**Expected Payload Structure**:
```json
{
  "timestamp": "ISO-8601 timestamp",
  "server": "Server Name",
  "checks": [
    {
      "name": "Check Name",
      "slug": "check-slug",
      "tags": "tag1,tag2",
      "desc": "Description",
      "unique_key": "unique_identifier",
      "status": "up|down|warning",
      "n_pings": 12345,
      "grace": 300,
      "timeout": 120,
      "last_ping": "ISO-8601 timestamp",
      "next_ping": "ISO-8601 timestamp",
      "manual_resume": false,
      "started": false,
      "methods": "http,email",
      "subject": "Alert subject",
      "badge_url": "https://..."
    }
  ]
}
```

**Features**:
- **Header Section**: Server name, overall status badge, sync time, check count
- **Check Cards**: Individual cards for each health check with:
  - Status icon and colored border (green=up, red=down, orange=warning)
  - Check name, slug, and description
  - Tags display with pill styling
  - Statistics grid: Total pings, grace period, timeout, manual resume
  - Timing information: Last ping, next ping, time until next ping (live countdown)
  - Optional fields: Methods, subject, started status
  - Badge URL link
- **Real-time Updates**: 1-second refresh for countdowns and time deltas
- **Empty State**: Warning message when no checks available
- **Responsive Design**: Modern gradient backgrounds, glass-morphism effects, shadows

**Displayed Data Points**:
- ✅ Server name and timestamp
- ✅ Overall health status (ALL HEALTHY / ISSUES DETECTED / WARNING)
- ✅ Per-check: name, slug, tags, description
- ✅ Status with icon and color coding
- ✅ Total pings count (formatted with thousands separator)
- ✅ Grace period and timeout values
- ✅ Manual resume requirement
- ✅ Last ping time (formatted)
- ✅ Next ping time (formatted)
- ✅ Live countdown to next ping
- ✅ Optional: methods, subject, started flag
- ✅ Badge URL with clickable link

**Customization Points**:
- Card heights (adjust `height` in node config)
- Color scheme (modify status colors in computed styles)
- Statistics displayed (add/remove grid items)
- Timing format (change date formatting)
- Animation effects (adjust transitions)
- Empty state message

### 20-hp-controls.json

**Purpose**: Boot and shutdown buttons for HP DL360p

**Contains**:
- `btn_hp_boot`: iLO boot button
- `btn_hp_shutdown`: Graceful shutdown button
- `btn_hp_force_shutdown`: Force shutdown button
- `mqtt_out_hp`: MQTT output node

**Dependencies**:
- Requires `ui_group_hp` from base config
- Requires `mqtt_broker_local` from base config

**MQTT Topics**:
- `hp/dl360p/command/boot`
- `hp/dl360p/command/shutdown`

**Customization Points**:
- Same as Dell controls (button styling, payloads)

### 21-hp-status.json

**Purpose**: Real-time status display for HP DL360p

**Contains**:
- `mqtt_in_hp_status`: Status subscription
- `func_hp_status_metadata`: Metadata tracking
- `template_hp_status`: Vue.js status UI

**Dependencies**:
- Requires `ui_group_hp` from base config
- Requires `mqtt_broker_local` from base config

**MQTT Topics**:
- Subscribes to: `hp/dl360p/status`

**Features**: Same as Dell status module

**Customization Points**: Same as Dell status module

### 22-hp-health.json

**Purpose**: Comprehensive health monitoring dashboard for HP DL360p

**Contains**:
- `mqtt_in_hp_health`: Health data subscription
- `ui_template_hp_health`: Advanced health monitoring UI with full data display

**Dependencies**:
- Requires `ui_group_hp_health` from base config
- Requires `mqtt_broker_local` from base config

**MQTT Topics**:
- Subscribes to: `hp/dl360p/health`

**Features**: Identical to Dell health module (see 12-dell-health.json for full feature list)
- Complete health check visualization
- Real-time countdown timers
- Status badges and color coding
- Statistics grid display
- Modern UI with gradients and shadows

**Customization Points**: Same as Dell health module

### 90-log-console.json

**Purpose**: Centralized system logging display

**Contains**:
- `mqtt_in_all_response`: System logs subscription
- `mqtt_in_legacy_responses`: Command response subscription
- `func_log_accumulator`: Log buffer management (last 50 entries)
- `ui_template_logs`: Rolling log console UI

**Dependencies**:
- Requires `ui_group_logs` from base config
- Requires `mqtt_broker_local` from base config

**MQTT Topics**:
- Subscribes to: `system/logs`
- Subscribes to: `+/+/response` (wildcard for all server responses)

**Expected Log Payload**:
```json
{
  "timestamp": "HH:MM:SS or ISO-8601",
  "level": "INFO|WARNING|ERROR|CRITICAL",
  "service": "service_name",
  "message": "Log message",
  "success": true|false  // Optional, for legacy responses
}
```

**Features**:
- Terminal-style display (dark background, monospace font)
- Color-coded by severity
- Automatic scrolling
- 50-entry buffer (configurable)
- Reverse chronological order

**Customization Points**:
- Buffer size (change 50 to desired value in `func_log_accumulator`)
- Colors for each log level
- Console styling (background, font, etc.)

## Adding a New Server

To add support for a new server (e.g., "Synology NAS"):

### 1. Update Base Configuration

Edit `flows/00-base-config.json`:

```json
{
  "id": "ui_group_synology",
  "type": "ui-group",
  "name": "Synology NAS Control",
  "page": "ui_page_home",
  "width": "6",
  "height": "1",
  "order": 6,  // Next available order
  "showTitle": true,
  "className": "",
  "visible": "true",
  "disabled": "false"
},
{
  "id": "ui_group_synology_health",
  "type": "ui-group",
  "name": "Synology NAS Health",
  "page": "ui_page_home",
  "width": "6",
  "height": "1",
  "order": 7,
  "showTitle": true,
  "className": "",
  "visible": "true",
  "disabled": "false"
}
```

### 2. Create Control Module

Create `flows/30-synology-controls.json`:
- Copy from `10-dell-controls.json` or `20-hp-controls.json`
- Replace all IDs (generate new UUIDs)
- Update node names, topics, and group references
- Customize boot method (WOL, IPMI, API, etc.)

### 3. Create Status Module

Create `flows/31-synology-status.json`:
- Copy from `11-dell-status.json`
- Update IDs, names, topics, and group references

### 4. Create Health Module

Create `flows/32-synology-health.json`:
- Copy from `12-dell-health.json`
- Update IDs, names, topics, and group references

### 5. Update Backend

Ensure your Python backend publishes to the correct MQTT topics:
- `synology/nas/status`
- `synology/nas/health`
- Listens on: `synology/nas/command/boot`, `synology/nas/command/shutdown`

### 6. Test

1. Import all four modules (base + new features)
2. Deploy
3. Test each button and monitor status updates
4. Verify health checks display correctly

## Troubleshooting

### Import Fails

**Error**: "Node configuration error"
- **Cause**: Missing dependencies (broker, groups)
- **Solution**: Import base config first

### Status Not Updating

**Error**: Status widget shows "UNKNOWN"
- **Cause**: MQTT not receiving messages
- **Solution**: 
  1. Check MQTT broker is running
  2. Verify Python services are publishing
  3. Use MQTT Explorer to monitor topics
  4. Check Node-RED debug panel

### Buttons Not Working

**Error**: Button clicks have no effect
- **Cause**: MQTT connection issues or wrong topics
- **Solution**:
  1. Check `mqtt_broker_local` configuration
  2. Verify topic names match Python listeners
  3. Add debug nodes to trace message flow

### UI Styling Issues

**Error**: Templates not rendering correctly
- **Cause**: Vue.js syntax errors or missing Dashboard 2.0
- **Solution**:
  1. Check browser console for errors
  2. Verify @flowfuse/node-red-dashboard is installed
  3. Validate template syntax

### Flow Context Lost

**Error**: Metadata (timestamps, state) resets unexpectedly
- **Cause**: Node-RED restart or flow context not persisted
- **Solution**: 
  1. Use context storage in settings.js for persistence
  2. Or accept that metadata is session-based

## Advanced Topics

### Custom Themes

Dashboard 2.0 supports custom themes. Edit `ui_base`:

```json
{
  "id": "ui_base",
  "type": "ui-base",
  "theme": {
    "name": "Custom Dark",
    "colors": {
      "surface": "#1a1a1a",
      "primary": "#2196f3",
      "bgPage": "#121212"
    }
  }
}
```

### Authentication

Enable authentication in Node-RED settings.js:

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

### HTTPS/TLS

1. Generate certificates
2. Place certificates in Node-RED directory
3. Configure in settings.js:

```javascript
https: {
    key: fs.readFileSync('/data/certs/privkey.pem'),
    cert: fs.readFileSync('/data/certs/cert.pem')
}
```

### Performance Optimization

For large deployments:
- Increase buffer sizes carefully (memory usage)
- Use message rate limiting
- Consider separate flows/tabs for each server
- Enable context persistence only when needed

## Backup and Restore

### Export All Flows

1. Menu → Export → All Flows
2. Save as `flows-backup-YYYY-MM-DD.json`
3. Store in version control

### Restore Flows

1. Menu → Import
2. Select backup file
3. Choose "Import to new flow" to avoid conflicts
4. Deploy

### Node-RED Data Backup

```bash
sudo systemctl stop nodered
tar -czvf nodered-backup.tar.gz ~/.node-red
sudo systemctl start nodered
```

## Migration from Monolithic

If migrating from the old `flows.json`:

1. **Backup current flows**
2. **Clear all flows**: Menu → Configuration nodes → Delete all
3. **Import in order**: 00, 10-12, 20-22, 90
4. **Deploy and test**
5. **Verify all features work**
6. **Archive old flows.json**

## Version History

- **v2.0.0** (Current): Modular feature-based architecture
- **v1.x**: Monolithic flows.json (deprecated)

## Contributing

1. Follow the naming conventions
2. Keep features self-contained
3. Document custom nodes and functions
4. Test imports on clean instance
5. Update this guide with new features

## Support

For issues or questions:
1. Check TROUBLESHOOTING.md
2. Review Node-RED logs: `journalctl -u nodered -f`
3. Check MQTT traffic with MQTT Explorer
4. Create issue in project repository

---

**Last Updated**: December 29, 2025
**Node-RED Version**: Latest (Dashboard 2.0)
**Maintainer**: Server Management Team

