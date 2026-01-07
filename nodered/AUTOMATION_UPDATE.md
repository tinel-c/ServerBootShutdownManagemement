# Server Automation Update - January 2026

## Overview
Complete redesign of the server automation logic and interface with bug fixes, modern UI, comprehensive activity logging, and intelligent client-aware boot management.

## 🔧 Critical Bug Fixes

### 1. Fixed Shutdown Command Not Executing
**Problem:** When the grace period expired, the shutdown command was not being sent properly. The logic would reset the counter and restart.

**Solution:**
- Separated command outputs into 3 distinct outputs:
  - Output 1: Boot commands only
  - Output 2: Shutdown commands only  
  - Output 3: UI refresh triggers
- Fixed MQTT message format to match protocol specification exactly
- Added proper `request_id` generation for command tracking

### 2. Corrected MQTT Message Format
**Before:**
```json
{
  "action": "shutdown",
  "type": "graceful"
}
```

**After (Correct Protocol):**
```json
{
  "action": "shutdown",
  "type": "graceful",
  "timeout": 300,
  "timestamp": "2026-01-07T...",
  "request_id": "shutdown-1736265432001"
}
```

All messages now include:
- ISO8601 timestamp
- Unique request_id for tracking
- All required fields per MQTT_PROTOCOL.md

## 🎨 UI Redesign

### Modern Dashboard Features
1. **Clean, Dark Theme**
   - Gradient backgrounds (#0f172a → #1e293b)
   - Glass-morphism effects with backdrop blur
   - Smooth animations and transitions
   - Professional color scheme

2. **Enhanced Status Indicators**
   - Pulsing animation for online servers
   - Color-coded status bars (green/red/gray)
   - Real-time health check timestamps
   - Visual countdown timer for shutdowns

3. **Improved Toggle Switch**
   - Larger, more accessible toggle
   - Visual state labels (AUTOMATED / MANUAL)
   - Smooth animations
   - Clear visual feedback

4. **Action Cards**
   - Grid layout for current status
   - Color-coded actions (boot=green, shutdown=red, grace=yellow)
   - Live countdown display
   - Details at a glance

## 📋 Activity Log Feature

### New Comprehensive Logging
Every automation event is now logged with:
- **Timestamp:** Exact time of event
- **Action:** What happened (Boot, Shutdown, Grace Period, etc.)
- **Type:** Command type (wol, graceful, countdown, config, etc.)
- **Trigger:** What caused the action
- **Status:** Command status (sent, executed, started, cancelled, applied)

### Log Display Features
- **Scrollable window** - Shows last 8 events, stores 50 (optimized for layout)
- **Color-coded entries** - Visual differentiation by action type
- **Emoji indicators** - Quick visual reference
  - 🚀 Boot commands
  - ⏹️ Shutdown commands
  - ⏱️ Grace periods
  - ❌ Cancellations
  - ✅/⏸️ Config changes
- **Status badges** - Clear status indicators
- **Hover effects** - Improved readability

### Example Log Entries
```
17:30:42  🟢 Trigger       [client_online]  First client connected: PC-001    DETECTED
17:30:45  🚀 Boot          [wol]            First client online               SENT
17:45:19  🔴 Trigger       [client_offline] Last client disconnected: PC-001  DETECTED
17:45:22  ⏱️ Grace Period  [countdown]      Last client offline               STARTED
17:50:22  ⏹️ Shutdown      [graceful]       Grace period expired              EXECUTED
17:51:10  ❌ Cancelled     [abort]          Client connected                  CANCELLED
```

### Log Entry Color Coding
- 🟢 **Green border** - Client comes online (triggers boot)
- 🔴 **Orange border** - Client goes offline (triggers grace period)
- 🚀 **Green border** - Boot commands
- ⏹️ **Red border** - Shutdown commands
- ⏱️ **Yellow border** - Grace periods
- ❌ **Purple border** - Cancellations
- ✅/⏸️ **Blue border** - Configuration changes

## 🔄 Logic Improvements

### 1. Enhanced Watchdog System
- Monitors server health continuously
- 60-second grace period before recovery boot
- Logs all recovery attempts
- Prevents false triggers
- Respects 5-minute cooldown period

### 2. **NEW: Smart Client-Aware Boot** ⭐
**Problem:** Clients connect but server is down/offline - they can't access resources.

**Solution:** Intelligent wake-up logic that monitors client presence:
- **Detects when clients need server:** If any client is connected AND server is down/offline/unknown
- **Automatically boots server:** Sends WOL command to wake up the server
- **5-minute cooldown:** Prevents retry spam during boot/shutdown operations
- **Respects server state updates:** Waits for actual status changes before retrying
- **Activity logging:** Logs trigger as "X client(s) need server"

**Example Scenario:**
```
1. Server is offline
2. User PC boots up and connects → Client count = 1
3. Automation detects: clients > 0 AND server = down
4. Sends boot command via WOL
5. Enters 5-minute cooldown (waiting for server to boot)
6. After 5 minutes, if still down, will retry
7. Once server is UP, normal operation resumes
```

**Benefits:**
- ✅ Server boots automatically when needed
- ✅ No manual intervention required
- ✅ Prevents command spam during boot process
- ✅ Works with multiple clients
- ✅ Full activity log visibility

### 3. Idle Server Detection
- Automatically detects idle servers (up but no clients)
- Initiates grace period
- Prevents unnecessary power consumption
- Respects 5-minute cooldown after shutdown

### 4. Smart Cancellation
- Automatically cancels shutdown if client connects
- Logs cancellation events
- Immediate status update

### 5. Activity Tracking
- All automation events logged to flow context
- Persistent across page refreshes
- Limited to 50 entries (automatic cleanup)
- Displays most recent 8 in UI (optimized for layout)

## 📊 Dashboard Layout

```
┌─────────────────────────────────────────────────┐
│  Server Automation          [2 Clients] [●AUTO] │
├─────────────────────────────────────────────────┤
│  ● DELL T310                              UP    │
│    Last Health Check: 2s ago                    │
├─────────────────────────────────────────────────┤
│  ⏳ Boot cooldown: 3:45 (waiting for state...) │ ← NEW!
├─────────────────────────────────────────────────┤
│  CURRENT ACTION          │  SHUTDOWN IN         │
│  Boot                    │  4:37                │
│  First client online     │                      │
├─────────────────────────────────────────────────┤
│  📋 Activity Log                    12 events   │
│  ┌───────────────────────────────────────────┐  │
│  │ 17:30:45  🚀 Boot [wol] ...      SENT    │  │
│  │ 17:28:12  ⏱️ Grace [countdown]... STARTED│  │
│  │ 17:23:05  ⏹️ Shutdown [graceful] EXECUTED│  │
│  │ ...                                       │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

### Cooldown Banner (NEW)
When a boot or shutdown command is sent, a cooldown banner appears:
- **Green banner** for boot cooldown
- **Red banner** for shutdown cooldown
- **Live countdown timer** showing remaining time
- **Helpful hint** explaining it's waiting for server state update
- **Auto-hides** when cooldown period expires

## 🚀 Benefits

1. **Reliability:** Shutdown commands now execute properly after grace period
2. **Visibility:** Complete audit trail of all automation actions with timestamps
3. **Debugging:** Easy to see what triggered each action and when
4. **User Experience:** Modern, professional interface with smooth animations
5. **Monitoring:** Real-time status with visual feedback and cooldown indicators
6. **Intelligence:** Server automatically boots when clients need it ⭐
7. **Efficiency:** Prevents command spam with intelligent cooldown system
8. **Transparency:** Visual cooldown banner shows exactly what's happening
9. **Robustness:** Respects server boot/shutdown timing (5-minute window)
10. **Automation:** Zero manual intervention needed for client-server coordination

## 📝 Technical Details

### Node Changes
1. **func_server_boot** - Added activity logging and proper message format
2. **func_server_shutdown** - Added activity logging
3. **func_process_grace_timer** - Fixed routing (3 outputs), added logging
4. **func_set_automation_state** - Added activity logging
5. **func_prepare_dashboard_data** - Added activity log to payload
6. **ui_template_automation_dashboard** - Complete redesign with log display

### Flow Context Variables
- `activity_log` - Array of log entries (max 50)
- `last_command` - Current command info
- `shutdown_deadline` - ISO timestamp for shutdown
- `client_automation_enabled` - Boolean automation state
- `clients` - Active client dictionary
- `status_metadata_dell_t310_status` - Server health metadata
- `last_boot_timestamp` - Timestamp (ms) of last boot command (NEW)
- `last_shutdown_timestamp` - Timestamp (ms) of last shutdown command (NEW)

### Cooldown Management
**Duration:** 5 minutes (300 seconds)

**Prevents:**
- Boot command spam during server startup
- Shutdown command spam during graceful shutdown
- IPMI/WOL overload
- False positive triggers

**Applies to:**
- Client-aware boot (smart wake-up)
- Watchdog recovery boot
- Graceful shutdown commands

**Does NOT apply to:**
- Manual commands (first client trigger)
- Grace period initiation
- Shutdown cancellation

## 🔍 Testing Checklist

### Core Functionality
- [ ] Deploy updated flow to Node-RED
- [ ] Verify shutdown executes after grace period
- [ ] Check activity log displays events
- [ ] Test automation enable/disable toggle
- [ ] Verify client connection cancels shutdown
- [ ] Check MQTT message format matches protocol
- [ ] Test recovery boot on health loss
- [ ] Verify UI updates in real-time

### NEW: Smart Client-Aware Boot
- [ ] **Test 1:** Server down, client connects → Should boot server
- [ ] **Test 2:** Verify cooldown banner appears (5 min countdown)
- [ ] **Test 3:** During cooldown, verify no duplicate boot commands
- [ ] **Test 4:** After 5 min, if still down, verify retry attempt
- [ ] **Test 5:** Multiple clients connect → Should boot once
- [ ] **Test 6:** Check activity log shows "X client(s) need server"
- [ ] **Test 7:** Server boots successfully → Cooldown clears

### Cooldown System
- [ ] Boot cooldown prevents duplicate WOL commands
- [ ] Shutdown cooldown respected
- [ ] Cooldown banner shows correct countdown
- [ ] Cooldown clears after 5 minutes
- [ ] UI updates cooldown status every second

## 📚 Related Documentation

- [MQTT Protocol](../docs/MQTT_PROTOCOL.md) - Message format specification
- [Node-RED Development](NODE_RED_DEVELOPMENT.md) - Development guide
- [Architecture](../docs/ARCHITECTURE.md) - System overview

---

**Version:** 2.3.0  
**Date:** January 7, 2026  
**Author:** Server Automation Team

