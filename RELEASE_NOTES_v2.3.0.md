# Release Notes - v2.3.0

**Release Date:** January 7, 2026  
**Codename:** "Smart Automation"

---

## 🎉 Overview

Version 2.3.0 introduces **intelligent client-aware server management** with comprehensive activity logging and enhanced automation logic. The system now automatically boots servers when clients need them and properly executes shutdowns after grace periods.

---

## 🚀 New Features

### 1. Client-Aware Boot (Smart Wake-Up) ⭐

**Problem Solved:** Clients boot up but can't access resources because server is offline.

**Solution:** Automation detects when clients need the server and automatically boots it.

**How It Works:**
- Monitors client count and server status every second
- If `clients > 0` AND `server = down/offline/unknown`
- Sends WOL boot command automatically
- Tracks boot timestamp for cooldown management

**Example:**
```
08:00:42  🟢 Trigger  [client_online]   First client connected: PC-001     DETECTED
08:00:45  🚀 Boot     [wol]             1 client(s) need server            SENT
```

**Benefits:**
- ✅ Zero manual intervention
- ✅ Server boots when needed
- ✅ Handles multiple clients intelligently
- ✅ Works 24/7 automatically

**Documentation:** `nodered/SMART_WAKEUP_GUIDE.md`

---

### 2. Command Cooldown System 🛡️

**Problem Solved:** Multiple boot commands sent during server startup causing spam.

**Solution:** 5-minute cooldown between commands.

**Implementation:**
- Tracks `last_boot_timestamp` and `last_shutdown_timestamp`
- Prevents duplicate commands within 5-minute window
- Allows retry after cooldown if server still down
- Respects server boot time (~2-3 min) + buffer

**Visual Feedback:**
```
┌─────────────────────────────────────────────────┐
│ ⏳ Boot cooldown: 3:45 (waiting for state...) │
└─────────────────────────────────────────────────┘
```

**Benefits:**
- ✅ No command spam
- ✅ Respects boot/shutdown timing
- ✅ Clear visual indication
- ✅ Automatic retry logic

---

### 3. Comprehensive Activity Logging 📋

**Problem Solved:** No visibility into what triggers automation actions.

**Solution:** Complete audit trail with timestamps, triggers, and status.

**What's Logged:**
- 🟢 **Client Triggers** - First client online (triggers boot)
- 🔴 **Client Triggers** - Last client offline (triggers grace)
- 🚀 **Boot Commands** - WOL/IPMI with cooldown
- ⏱️ **Grace Periods** - 5-minute countdown
- ⏹️ **Shutdowns** - Graceful execution
- ❌ **Cancellations** - Shutdown aborted
- ✅ **Config Changes** - Automation toggle

**Log Entry Format:**
```
timestamp  emoji  action  [type]  trigger  STATUS
```

**Example Timeline:**
```
18:05:22  ⏹️ Shutdown      [graceful]       Grace period expired             EXECUTED
18:00:22  ⏱️ Grace Period  [countdown]      Last client offline              STARTED
18:00:15  🔴 Trigger       [client_offline] Last client disconnected: PC-001 DETECTED
```

**UI Features:**
- Scrollable window (last 20 events)
- Color-coded borders
- Status badges
- Emoji indicators
- Real-time timestamps

**Benefits:**
- ✅ Complete visibility
- ✅ Easy debugging
- ✅ Audit compliance
- ✅ User transparency

---

### 4. Modern Automation Dashboard 🎨

**Complete UI Redesign:**
- Dark gradient background (#0f172a → #1e293b)
- Glass-morphism effects with backdrop blur
- Smooth animations and transitions
- Live countdown timers (updates every second)
- Responsive grid layout

**Dashboard Sections:**

**Header:**
- Title + client count badge
- Automation toggle (AUTOMATED / MANUAL)

**Server Status Bar:**
- Pulsing status indicator
- Server name and state (UP/DOWN/UNKNOWN)
- Last health check timestamp

**Cooldown Banner (NEW):**
- Live countdown (MM:SS format)
- Color-coded (green=boot, red=shutdown)
- Auto-hides when expired

**Action Cards:**
- Current action display
- Live countdown or timestamp
- Trigger details

**Activity Log:**
- Scrollable list (280px max height)
- Color-coded entries
- Hover effects
- Status badges

**Benefits:**
- ✅ Professional appearance
- ✅ Instant status visibility
- ✅ Clear automation state
- ✅ Real-time updates

---

## 🔧 Bug Fixes

### Critical: Shutdown Command Not Executing

**Problem:** Grace period expired but shutdown command wasn't sent.

**Root Cause:** 
- Command outputs were mixed (boot + shutdown on same output)
- Message format incomplete (missing fields)

**Solution:**
1. Separated command routing:
   - Output 1: Boot commands only → `mqtt_out_dell_boot`
   - Output 2: Shutdown commands only → `mqtt_out_dell_shutdown`
   - Output 3: UI refresh triggers only

2. Fixed MQTT message format:
```javascript
// Before (incomplete)
{
  action: 'shutdown',
  type: 'graceful'
}

// After (correct)
{
  action: 'shutdown',
  type: 'graceful',
  timeout: 300,
  timestamp: '2026-01-07T18:05:22Z',
  request_id: 'shutdown-1736265922001'
}
```

**Result:** Shutdown now executes properly after grace period! ✅

---

## 📝 Technical Changes

### Files Modified

#### 1. `nodered/flows/40-client-tracking.json`
- Added activity logging to `func_client_state_change`
- Logs client online/offline trigger events
- Captures client hostname in trigger message

#### 2. `nodered/flows/41-client-automation.json`
- **Complete rewrite** with 3-output routing
- Added cooldown tracking variables
- Added client-aware boot logic (Part 2)
- Enhanced watchdog with cooldown checks
- Updated dashboard with cooldown banner
- Added activity log display
- Enhanced CSS with modern styling

### New Documentation

1. **`nodered/AUTOMATION_UPDATE.md`** (Technical)
   - Complete implementation details
   - Bug fixes documentation
   - Logic improvements
   - UI redesign details

2. **`nodered/SMART_WAKEUP_GUIDE.md`** (User Guide)
   - How smart wake-up works
   - Visual indicators explained
   - Configuration options
   - Troubleshooting guide

3. **`nodered/CLIENT_AWARE_BOOT_SUMMARY.md`** (Summary)
   - Implementation summary
   - Key features list
   - Testing checklist
   - Benefits breakdown

4. **`nodered/TRIGGER_LOGGING_UPDATE.md`** (Logging)
   - Log entry structure
   - Color coding guide
   - Example timelines
   - Visual examples

5. **`docs/ARCHITECTURE_DIAGRAM_DESCRIPTION.md`** (Visual)
   - Architecture diagram specification
   - Layer descriptions
   - Color scheme
   - Component details

### Flow Context Variables (NEW)

```javascript
flow.set('last_boot_timestamp', ms);      // Cooldown tracking
flow.set('last_shutdown_timestamp', ms);  // Cooldown tracking
flow.set('activity_log', array);          // Event history (max 50)
```

---

## 🎯 Configuration

### Cooldown Duration

**Default:** 5 minutes (300 seconds)

**To Adjust:**
1. Edit Node-RED flow: "Watchdog & Grace Loop"
2. Change: `const COMMAND_COOLDOWN_MS = 5 * 60 * 1000;`
3. Deploy changes

**Recommended Range:** 3-10 minutes

---

## 📊 Benefits Summary

| Feature | Before | After |
|---------|--------|-------|
| **Shutdown After Grace** | ❌ Not working | ✅ Executes properly |
| **Client Needs Server** | ⚠️ Manual boot needed | ✅ Auto-boots |
| **Command Spam** | ⚠️ Duplicates sent | ✅ Cooldown prevents |
| **Visibility** | ❌ No audit trail | ✅ Complete log |
| **UI Design** | ⚠️ Basic | ✅ Modern/Professional |
| **Cooldown Feedback** | ❌ None | ✅ Live countdown banner |

---

## 🚀 Deployment

### Update Steps

1. **Backup current flows:**
   ```bash
   cd nodered
   cp flows.json flows.json.backup-$(date +%Y%m%d)
   ```

2. **Import updated flows:**
   - Open Node-RED: http://localhost:1880
   - Import: `flows/40-client-tracking.json` (overwrite)
   - Import: `flows/41-client-automation.json` (overwrite)

3. **Deploy:**
   - Click "Deploy" button
   - Verify no errors in debug panel

4. **Test:**
   - Check automation toggle is enabled
   - Boot a client PC
   - Verify activity log shows events
   - Check for boot command in logs

### Verification Checklist

- [ ] Dashboard loads without errors
- [ ] Automation toggle works
- [ ] Activity log displays events
- [ ] Cooldown banner appears after command
- [ ] Client triggers logged (🟢/🔴)
- [ ] Commands logged (🚀/⏹️)
- [ ] Shutdown executes after grace period

---

## ⚠️ Breaking Changes

**None.** This release is fully backward compatible.

**Migration:** No manual migration required. Simply import updated flows.

---

## 🐛 Known Issues

None at this time.

---

## 🔮 Future Enhancements

Potential features for future releases:

1. **Configurable Cooldown** - Adjust via UI (no code edit)
2. **Per-Command Cooldown** - Different times for boot vs shutdown
3. **Smart Retry Logic** - Exponential backoff for failed commands
4. **Client Priority** - Boot faster for high-priority clients
5. **Scheduled Maintenance** - Skip automation during maintenance windows
6. **Email Notifications** - Alert on automation events
7. **Historical Analytics** - Track automation patterns over time

---

## 📚 Documentation Index

### User Documentation
- `README.md` - Overview and quick start
- `client/README_CLIENT.md` - Client installation guide
- `nodered/SMART_WAKEUP_GUIDE.md` - Smart wake-up user guide

### Technical Documentation
- `docs/ARCHITECTURE.md` - System architecture
- `docs/MQTT_PROTOCOL.md` - MQTT message format
- `nodered/AUTOMATION_UPDATE.md` - Automation technical details
- `nodered/NODE_RED_DEVELOPMENT.md` - Node-RED development guide

### Implementation Details
- `nodered/CLIENT_AWARE_BOOT_SUMMARY.md` - Implementation summary
- `nodered/TRIGGER_LOGGING_UPDATE.md` - Activity logging details
- `docs/ARCHITECTURE_DIAGRAM_DESCRIPTION.md` - Diagram specification

---

## 🙏 Acknowledgments

This release brings the automation system to a production-ready state with intelligent, self-managing capabilities and complete transparency through comprehensive logging.

---

## 📞 Support

For issues or questions:
1. Check documentation in `nodered/` and `docs/` directories
2. Review activity log for automation events
3. Check cooldown banner status
4. See `docs/TROUBLESHOOTING.md`
5. Open GitHub issue with activity log excerpt

---

**Thank you for using the Server Boot/Shutdown Management System!**

**Version:** 2.3.0  
**Date:** January 7, 2026  
**Next Release:** TBD

