# Client Trigger Logging Update

## Overview
Added comprehensive logging of client connection/disconnection events that trigger automation actions.

## What Was Added

### Client Tracking Enhanced (40-client-tracking.json)
The `Detect State Change` function now logs automation trigger events:

**First Client Connects:**
```javascript
{
    timestamp: "2026-01-07T17:30:42Z",
    action: 'Trigger',
    type: 'client_online',
    trigger: 'First client connected: DESKTOP-PC',
    status: 'detected'
}
```

**Last Client Disconnects:**
```javascript
{
    timestamp: "2026-01-07T18:00:15Z",
    action: 'Trigger',
    type: 'client_offline',
    trigger: 'Last client disconnected: DESKTOP-PC',
    status: 'detected'
}
```

### Automation Dashboard Enhanced (41-client-automation.json)
Updated to display and style the new trigger events:

**Methods Updated:**
- `getLogEntryClass()` - Added handling for trigger events
  - `entry-trigger-online` - Green border for client online
  - `entry-trigger-offline` - Orange border for client offline
  
- `getLogEmoji()` - Added emojis for trigger events
  - 🟢 Green circle for client online
  - 🔴 Red circle for client offline

**CSS Added:**
```css
.log-entry.entry-trigger-online {
    border-left: 3px solid #10b981;  /* Green */
}

.log-entry.entry-trigger-offline {
    border-left: 3px solid #f59e0b;  /* Orange */
}

.log-status.detected {
    color: #6366f1;
    background: rgba(99, 102, 241, 0.15);
}
```

## Visual Example

### Activity Log Display
```
┌────────────────────────────────────────────────────┐
│ 📋 Activity Log                        6 events    │
├────────────────────────────────────────────────────┤
│ 18:05:22  ⏹️ Shutdown       [graceful]   EXECUTED │
│ 18:00:22  ⏱️ Grace Period   [countdown]  STARTED  │
│ 18:00:15  🔴 Trigger        [client_...] DETECTED │ ← NEW!
│ 08:02:45  🚀 Boot           [wol]        SENT     │
│ 08:00:42  🟢 Trigger        [client_...] DETECTED │ ← NEW!
│ 08:00:00  ✅ Automation...  [config]     APPLIED  │
└────────────────────────────────────────────────────┘
```

## Benefits

### 1. Complete Visibility
- See exactly when clients connect/disconnect
- Understand what triggered each automation action
- Full chronological audit trail

### 2. Better Debugging
- Identify if client events are being detected
- Verify timing between trigger and action
- Spot unexpected client behavior

### 3. Improved Understanding
- Clear cause-and-effect relationship
- Visual separation of triggers vs. actions
- Easy to follow automation logic

## Example Timeline

**Morning Startup Sequence:**
```
08:00:42  🟢 Trigger       [client_online]  First client connected: DESKTOP-001  DETECTED
          ↓ (3 seconds later)
08:00:45  🚀 Boot          [wol]            First client online                  SENT
          ↓ (boot cooldown starts)
08:00:45  ⏳ Boot cooldown: 5:00
```

**Evening Shutdown Sequence:**
```
18:00:15  🔴 Trigger       [client_offline] Last client disconnected: DESKTOP-001  DETECTED
          ↓ (7 seconds later)
18:00:22  ⏱️ Grace Period  [countdown]      Last client offline                    STARTED
          ↓ (5 minute countdown)
18:05:22  ⏹️ Shutdown      [graceful]       Grace period expired                   EXECUTED
```

## Log Entry Structure

### Trigger Events
| Field | Value | Description |
|-------|-------|-------------|
| timestamp | ISO8601 | When client state changed |
| action | "Trigger" | Type of log entry |
| type | "client_online" or "client_offline" | What changed |
| trigger | "First client connected: {hostname}" | Details |
| status | "detected" | Event was observed |

### Action Events  
| Field | Value | Description |
|-------|-------|-------------|
| timestamp | ISO8601 | When command was sent |
| action | "Boot", "Shutdown", etc. | What happened |
| type | "wol", "graceful", etc. | How it happened |
| trigger | "First client online", etc. | Why it happened |
| status | "sent", "executed", etc. | Command status |

## Color Coding Guide

| Icon | Color | Meaning |
|------|-------|---------|
| 🟢 | Green | Client comes online (triggers boot) |
| 🔴 | Orange | Client goes offline (triggers shutdown grace) |
| 🚀 | Green | Boot command sent |
| ⏹️ | Red | Shutdown command executed |
| ⏱️ | Yellow | Grace period active |
| ❌ | Purple | Action cancelled |
| ✅/⏸️ | Blue | Configuration change |

## Files Modified

1. **`nodered/flows/40-client-tracking.json`**
   - Updated `func_client_state_change` function
   - Added activity log entries for triggers
   - Captures client hostname in trigger message

2. **`nodered/flows/41-client-automation.json`**
   - Updated `getLogEntryClass()` method
   - Updated `getLogEmoji()` method
   - Added CSS for trigger entry styles
   - Added CSS for "detected" status badge

3. **`nodered/AUTOMATION_UPDATE.md`**
   - Updated example log entries
   - Added color coding guide

4. **`nodered/SMART_WAKEUP_GUIDE.md`**
   - Updated activity log examples
   - Enhanced daily workflow example

## Deployment Notes

- No breaking changes
- Backward compatible with existing logs
- New entries will appear automatically
- Existing logs remain unchanged

## Testing

After deployment, verify:
- [ ] First client connection shows 🟢 Trigger entry
- [ ] Last client disconnection shows 🔴 Trigger entry
- [ ] Trigger entries appear BEFORE action entries
- [ ] Client hostname visible in trigger message
- [ ] Timestamp accuracy (within 1-2 seconds)
- [ ] Color coding matches expectations

---

**Version:** 2.3.1  
**Date:** January 7, 2026  
**Type:** Enhancement - Activity Logging

