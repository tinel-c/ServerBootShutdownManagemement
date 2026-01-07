# Node-RED Modular Flows

This directory contains feature-based, modular Node-RED flows for the Server Boot/Shutdown Management system.

## Quick Start

### Import Order

**IMPORTANT**: Import flows in this specific order to ensure all dependencies are met:

1. `00-base-config.json` - **MUST BE IMPORTED FIRST**
2. `10-dell-controls.json`
3. `11-dell-status.json`
4. `12-dell-health.json`
5. `20-hp-controls.json`
6. `21-hp-status.json`
7. `22-hp-health.json`
8. `40-client-tracking.json`
9. `41-client-automation.json`
10. `90-log-console.json`

### Import Instructions

1. Open Node-RED: http://localhost:1880
2. Click the menu (≡) in the top-right corner
3. Select **Import**
4. Click **select a file to import**
5. Navigate to this `flows/` directory
6. Select the first file (`00-base-config.json`)
7. Click **Import**
8. Repeat for each file in order
9. Click **Deploy** after all imports are complete

## File Descriptions

### 00-base-config.json
**Core Infrastructure** - Must be imported first

- UI Base configuration
- Dashboard page definition
- All UI groups (Dell, HP, Logs, Health)
- MQTT broker connection
- Main tab

**Dependencies**: None

---

### 10-dell-controls.json
**Dell T310 Control Buttons**

- Boot button (Wake-on-LAN)
- Graceful shutdown button (Proxmox)
- Force shutdown button (IPMI)
- MQTT output node

**Dependencies**: `ui_group_dell`, `mqtt_broker_local`

**MQTT Topics**:
- `dell/t310/command/boot`
- `dell/t310/command/shutdown`

---

### 11-dell-status.json
**Dell T310 Status Display**

- Status subscription (MQTT in)
- Metadata tracking (last report, state changes)
- Real-time status UI (Vue.js template)

**Dependencies**: `ui_group_dell`, `mqtt_broker_local`

**MQTT Topics**:
- Subscribes: `dell/t310/status`

---

### 12-dell-health.json
**Dell T310 Comprehensive Health Monitoring**

- Health data subscription (MQTT in)
- Advanced health monitoring dashboard with full data visualization

**Features**:
- Server status header with overall health badge
- Individual check cards with status icons and color coding
- Statistics grid (pings, grace period, timeout, manual resume)
- Live countdown timers to next ping
- Timing information (last/next ping with formatted dates)
- Tags display with pill styling
- Optional fields (methods, subject, started status)
- Badge URL links
- Empty state handling

**Dependencies**: `ui_group_dell_health`, `mqtt_broker_local`

**MQTT Topics**:
- Subscribes: `dell/t310/health`

---

### 20-hp-controls.json
**HP DL360p Control Buttons**

- Boot button (iLO)
- Graceful shutdown button (Proxmox)
- Force shutdown button (iLO)
- MQTT output node

**Dependencies**: `ui_group_hp`, `mqtt_broker_local`

**MQTT Topics**:
- `hp/dl360p/command/boot`
- `hp/dl360p/command/shutdown`

---

### 21-hp-status.json
**HP DL360p Status Display**

- Status subscription (MQTT in)
- Metadata tracking (last report, state changes)
- Real-time status UI (Vue.js template)

**Dependencies**: `ui_group_hp`, `mqtt_broker_local`

**MQTT Topics**:
- Subscribes: `hp/dl360p/status`

---

### 22-hp-health.json
**HP DL360p Comprehensive Health Monitoring**

- Health data subscription (MQTT in)
- Advanced health monitoring dashboard with full data visualization

**Features**: Same as Dell health (12-dell-health.json)
- Complete health check cards with all metrics
- Real-time countdown timers
- Status badges and color coding
- Modern gradient UI design

**Dependencies**: `ui_group_hp_health`, `mqtt_broker_local`

**MQTT Topics**:
- Subscribes: `hp/dl360p/health`

---

### 40-client-tracking.json
**Client PC Presence Tracking**

- Client presence monitoring (MQTT in)
- Client heartbeat handling
- Client list management
- State change detection (first online / last offline)
- Live client display with Vue.js

**Features**:
- Real-time client count
- Client hostname and IP tracking
- Last seen timestamps
- Automatic stale client cleanup (150s grace)
- Visual client cards with status indicators
- **Activity logging** for first client online / last client offline triggers

**Dependencies**: `ui_group_clients`, `mqtt_broker_local`

**MQTT Topics**:
- Subscribes: `clients/+/presence`
- Subscribes: `clients/+/heartbeat`

**Link Outputs**:
- `link_out_first_client` - Triggers when first client comes online
- `link_out_last_client` - Triggers when last client goes offline

---

### 41-client-automation.json
**Smart Server Automation** ⭐ **NEW v2.3.0**

- Client-aware server boot (smart wake-up)
- Automatic idle shutdown with grace period
- Watchdog recovery system
- 5-minute command cooldown protection
- Comprehensive activity logging
- Modern automation dashboard

**Features**:
- **Smart Boot**: Automatically boots server when clients need it
- **Grace Period**: 5-minute countdown before idle shutdown
- **Cooldown System**: Prevents command spam during boot/shutdown (5 min)
- **Activity Log**: Complete audit trail with timestamps and triggers
- **Visual Feedback**: Live countdown timers and status indicators
- **Cancellation**: Auto-cancels shutdown if client connects

**Dependencies**: `ui_group_clients`, `mqtt_broker_local`

**MQTT Topics**:
- Subscribes: `dell/t310/health` (for health sync)
- Publishes: `dell/t310/command/boot`
- Publishes: `dell/t310/command/shutdown`

**Link Inputs**:
- `link_in_first_client` - Receives first client online trigger
- `link_in_last_client` - Receives last client offline trigger

**Documentation**: See `../SMART_WAKEUP_GUIDE.md` for complete usage guide

---

### 90-log-console.json
**System Log Console**

- System logs subscription
- Command responses subscription (wildcard)
- Log accumulator (50-entry buffer)
- Terminal-style rolling log display

**Dependencies**: `ui_group_logs`, `mqtt_broker_local`

**MQTT Topics**:
- Subscribes: `system/logs`
- Subscribes: `+/+/response` (wildcard)

---

## Customization

### Modifying a Feature

1. Make changes in Node-RED editor
2. Select all nodes for that feature
3. Menu → Export → Clipboard
4. Save to the appropriate file, overwriting the old version
5. Commit to version control

### Adding a New Server

See `NODE_RED_DEVELOPMENT.md` for detailed instructions on adding support for additional servers.

Basic steps:
1. Add UI groups to `00-base-config.json`
2. Create `30-newserver-controls.json` (copy from Dell or HP)
3. Create `31-newserver-status.json`
4. Create `32-newserver-health.json`
5. Update backend to publish to correct MQTT topics

## MQTT Topic Patterns

### Commands (Dashboard → Backend)
```
{server}/{model}/command/boot
{server}/{model}/command/shutdown
```

### Status (Backend → Dashboard)
```
{server}/{model}/status
{server}/{model}/health
system/logs
```

### Expected Payloads

**Boot Command**:
```json
{
  "action": "boot",
  "method": "wol|ipmi|ilo"
}
```

**Shutdown Command**:
```json
{
  "action": "shutdown",
  "type": "graceful|force"
}
```

**Status Update**:
```json
{
  "server_state": "online|offline|unknown",
  "timestamp": "2025-12-29T12:34:56Z"
}
```

**Health Update**:
```json
{
  "timestamp": "2025-12-29T12:34:56Z",
  "server": "Dell T310",
  "checks": [
    {
      "unique_key": "check_id",
      "name": "Check Name",
      "slug": "check-name",
      "tags": "tag1,tag2",
      "desc": "Optional description",
      "status": "up|down|warning",
      "n_pings": 12345,
      "grace": 300,
      "timeout": 120,
      "last_ping": "2025-12-29T12:34:00+00:00",
      "next_ping": "2025-12-29T12:36:00+00:00",
      "manual_resume": false,
      "started": false,
      "methods": "http",
      "subject": "Alert subject",
      "badge_url": "https://healthchecks.io/badge/..."
    }
  ]
}
```

**Log Entry**:
```json
{
  "timestamp": "12:34:56",
  "level": "INFO|WARNING|ERROR|CRITICAL",
  "service": "service_name",
  "message": "Log message text"
}
```

## Troubleshooting

### "Node configuration error" on Import

**Problem**: Missing dependencies (broker or UI groups)

**Solution**: Import `00-base-config.json` first

---

### Status Widget Shows "UNKNOWN"

**Problem**: No MQTT messages received

**Solution**:
1. Verify MQTT broker is running
2. Check Python services are publishing
3. Use MQTT Explorer to monitor topics
4. Check Node-RED debug panel

---

### Buttons Don't Work

**Problem**: MQTT connection or topic mismatch

**Solution**:
1. Check `mqtt_broker_local` configuration
2. Verify topic names match backend
3. Add debug nodes to trace messages

---

### Import Causes Duplicate Nodes

**Problem**: Importing same file multiple times

**Solution**:
1. Delete all flows
2. Reimport in correct order
3. Or manually delete duplicate nodes

## File Naming Convention

- `00-09`: Core infrastructure
- `10-19`: Dell T310 features
- `20-29`: HP DL360p features
- `30-39`: Reserved for future server 1
- `40-49`: Client automation and tracking
- `50-59`: Reserved for future features
- `90-99`: Shared utilities

## Version Control

Each `.json` file should be tracked in Git independently. This allows:
- Feature-specific commits
- Easy rollback of individual features
- Collaborative development
- Clear change history

## Testing

After importing flows:

1. **Visual Check**: Verify all UI elements appear in dashboard
2. **Status Test**: Confirm status updates display correctly
3. **Button Test**: Click each button, verify MQTT publish
4. **Health Test**: Confirm health checks display
5. **Logs Test**: Verify log console receives messages

## Support

For detailed development guidance, see:
- `../NODE_RED_DEVELOPMENT.md` - Comprehensive development guide
- `../../docs/MQTT_PROTOCOL.md` - MQTT protocol specification
- `../../docs/TROUBLESHOOTING.md` - System troubleshooting

---

**Last Updated**: January 7, 2026
**Format Version**: 2.3.0 (Modular + Smart Automation)

