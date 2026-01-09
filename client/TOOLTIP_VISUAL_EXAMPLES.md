# System Tray Tooltip Visual Examples

Visual representation of the enhanced system tray tooltip showing version information and update scheduling.

## Tooltip Examples

### Example 1: Update Available 🚨

```
┌─────────────────────────────────────┐
│  Client Monitor Tooltip             │
├─────────────────────────────────────┤
│  CM: desktop-workstation            │
│  v2.4.0 → v2.5.0 ⚠                  │
│  Broker: OK                         │
│  Srv: ONLINE                        │
│  HB: 45s                            │
│  Update chk: 23h 15m                │
│  Last: 10:30:45 - Update: 2.5.0    │
└─────────────────────────────────────┘
```

**Status**: Update available  
**Action**: User should know a new version (2.5.0) is ready to install  
**Indicator**: Warning symbol (⚠) alerts user to available update

---

### Example 2: Up to Date ✅

```
┌─────────────────────────────────────┐
│  Client Monitor Tooltip             │
├─────────────────────────────────────┤
│  CM: office-pc-01                   │
│  v2.4.0 (up to date)                │
│  Broker: OK                         │
│  Srv: ONLINE                        │
│  HB: 30s                            │
│  Update chk: 22h 45m                │
│  Last: 10:31:20 - Heartbeat         │
└─────────────────────────────────────┘
```

**Status**: Running latest version  
**Action**: No action needed  
**Indicator**: "(up to date)" confirms latest version is installed

---

### Example 3: First Run / Version Unknown ❓

```
┌─────────────────────────────────────┐
│  Client Monitor Tooltip             │
├─────────────────────────────────────┤
│  CM: laptop-home                    │
│  v2.4.0                             │
│  Broker: OK                         │
│  Srv: UNKNOWN                       │
│  HB: 60s                            │
│  Update chk: Pending                │
│  Last: 10:32:00 - Startup           │
└─────────────────────────────────────┘
```

**Status**: First run, no GitHub check performed yet  
**Action**: Wait for automatic check or manually trigger  
**Indicator**: "Pending" indicates check hasn't occurred

---

### Example 4: Disconnected State 🔌

```
┌─────────────────────────────────────┐
│  Client Monitor Tooltip             │
├─────────────────────────────────────┤
│  CM: remote-worker-pc               │
│  v2.4.0 (up to date)                │
│  Broker: OFF                        │
│  Srv: UNKNOWN                       │
│  HB: 15s                            │
│  Update chk: 1h 30m                 │
│  Last: 10:28:15 - Heartbeat         │
└─────────────────────────────────────┘
```

**Status**: Disconnected from MQTT broker  
**Action**: Check network connectivity  
**Indicator**: "Broker: OFF" shows connection issue

---

### Example 5: Server Offline ⚠️

```
┌─────────────────────────────────────┐
│  Client Monitor Tooltip             │
├─────────────────────────────────────┤
│  CM: main-workstation               │
│  v2.4.0 (up to date)                │
│  Broker: OK                         │
│  Srv: OFFLINE                       │
│  HB: 55s                            │
│  Update chk: 18h 20m                │
│  Last: 10:29:30 - Heartbeat         │
└─────────────────────────────────────┘
```

**Status**: Connected but target server is offline  
**Action**: Normal operation, server can be booted as needed  
**Indicator**: Orange tray icon color

---

### Example 6: Update Check Imminent ⏰

```
┌─────────────────────────────────────┐
│  Client Monitor Tooltip             │
├─────────────────────────────────────┤
│  CM: test-machine                   │
│  v2.4.0 (up to date)                │
│  Broker: OK                         │
│  Srv: ONLINE                        │
│  HB: 20s                            │
│  Update chk: Soon                   │
│  Last: 10:33:45 - Heartbeat         │
└─────────────────────────────────────┘
```

**Status**: Update check will happen in next cycle  
**Action**: Wait for automatic check  
**Indicator**: "Soon" means check is imminent

---

### Example 7: Long Client Name (Truncated) ✂️

```
┌─────────────────────────────────────┐
│  Client Monitor Tooltip             │
├─────────────────────────────────────┤
│  CM: very-long-clien...             │
│  v2.4.0 (up to date)                │
│  Broker: OK                         │
│  Srv: ONLINE                        │
│  HB: 40s                            │
│  Update chk: 5d                     │
│  Last: 10:34:00 - Heartbeat         │
└─────────────────────────────────────┘
```

**Status**: Normal operation with long client name  
**Action**: None  
**Indicator**: Name truncated with "..." to fit character limit

---

### Example 8: Multiple Days Until Check 📅

```
┌─────────────────────────────────────┐
│  Client Monitor Tooltip             │
├─────────────────────────────────────┤
│  CM: weekly-check-pc                │
│  v2.4.0 (up to date)                │
│  Broker: OK                         │
│  Srv: ONLINE                        │
│  HB: 35s                            │
│  Update chk: 6d                     │
│  Last: 10:35:15 - Heartbeat         │
└─────────────────────────────────────┘
```

**Status**: Weekly update check configured (168 hours)  
**Action**: None  
**Indicator**: Days shown when > 24 hours remain

---

## Icon Color Reference

The tray icon color changes based on connection and server status:

### 🔴 Red Icon
```
Status: ERROR
Condition: Connection failed or critical error
Example: Cannot connect to MQTT broker
```

### ⚫ Gray Icon
```
Status: DISCONNECTED
Condition: Not connected to MQTT broker
Example: Network interruption
```

### 🟡 Yellow Icon
```
Status: CONNECTED (Server Unknown)
Condition: Connected to broker, server status not determined
Example: First connection or no health messages received
```

### 🟢 Green Icon
```
Status: CONNECTED (Server Online)
Condition: Connected and target server is running
Example: Normal operation, server is up
```

### 🟠 Orange Icon
```
Status: CONNECTED (Server Offline)
Condition: Connected but target server is shut down
Example: Server intentionally offline
```

---

## Tooltip Line-by-Line Breakdown

```
┌─────────────────────────────────────┐
│  CM: desktop-workstation            │  ← Line 1: Client ID
│  v2.4.0 → v2.5.0 ⚠                  │  ← Line 2: Version Info
│  Broker: OK                         │  ← Line 3: MQTT Broker Status
│  Srv: ONLINE                        │  ← Line 4: Target Server Status
│  HB: 45s                            │  ← Line 5: Heartbeat Countdown
│  Update chk: 23h 15m                │  ← Line 6: Next Update Check
│  Last: 10:30:45 - Update: 2.5.0    │  ← Line 7: Last Action (optional)
└─────────────────────────────────────┘
```

### Line 1: Client Identification
- **Purpose**: Identifies which PC this is
- **Format**: `CM: {client_id}`
- **Source**: Hostname or custom name from config
- **Truncation**: Long names shortened to 17 chars + "..."

### Line 2: Version Information (NEW)
- **Purpose**: Shows current and available versions
- **Formats**:
  - `v{current} → v{latest} ⚠` - Update available
  - `v{current} (up to date)` - Latest version
  - `v{current}` - Unknown GitHub version
- **Update**: Changes immediately when new version detected

### Line 3: Broker Connection
- **Purpose**: Shows MQTT broker connection status
- **Values**:
  - `Broker: OK` - Connected successfully
  - `Broker: OFF` - Disconnected
  - `Broker: ERR` - Connection error

### Line 4: Server Status
- **Purpose**: Shows target server state
- **Values**:
  - `Srv: ONLINE` - Server is running
  - `Srv: OFFLINE` - Server is shut down
  - `Srv: UNKNOWN` - Status not yet determined

### Line 5: Heartbeat Countdown
- **Purpose**: Shows time to next heartbeat
- **Format**: `HB: {seconds}s`
- **Update**: Decrements every second
- **Range**: 0-60 seconds (default interval)

### Line 6: Update Check Time (NEW)
- **Purpose**: Shows when next automatic update check occurs
- **Formats**:
  - `Update chk: {days}d` - More than 24 hours
  - `Update chk: {hours}h {minutes}m` - Less than 24 hours
  - `Update chk: {minutes}m` - Less than 1 hour
  - `Update chk: Soon` - Imminent
  - `Update chk: Pending` - No check yet

### Line 7: Last Action
- **Purpose**: Shows most recent activity
- **Format**: `Last: {time} - {action}`
- **Examples**:
  - `Last: 10:30:45 - Heartbeat`
  - `Last: 10:29:15 - Startup`
  - `Last: 10:28:00 - Update: 2.5.0`
- **Optional**: Only shown if space available (< 128 chars total)

---

## Character Limit Management

Windows tooltips are limited to 128 characters. The tooltip uses these strategies to fit:

### Space-Saving Techniques
1. **Abbreviations**:
   - "CM:" instead of "Client Monitor:"
   - "HB:" instead of "Next Heartbeat:"
   - "Srv:" instead of "Server:"
   - "Update chk:" instead of "Next Update Check:"

2. **Smart Truncation**:
   - Client names > 20 chars truncated to 17 + "..."
   - Recent actions truncated if too long

3. **Conditional Display**:
   - Last action only shown if total < 120 chars
   - Reduces recent actions from 2 to 1 item

4. **Compact Time Format**:
   - "23h 15m" instead of "23 hours, 15 minutes"
   - "5d" instead of "5 days"

### Example Calculation
```
Line 1: "CM: desktop-workstation"        = 24 chars
Line 2: "v2.4.0 → v2.5.0 ⚠"             = 19 chars
Line 3: "Broker: OK"                    = 10 chars
Line 4: "Srv: ONLINE"                   = 11 chars
Line 5: "HB: 45s"                       = 7 chars
Line 6: "Update chk: 23h 15m"           = 20 chars
Line 7: "Last: 10:30:45 - Update: ..."  = 30 chars (variable)
Newlines: 6                             = 6 chars
                                        ___________
Total:                                  = 127 chars ✅
```

---

## Testing Checklist

Use these scenarios to test the tooltip display:

- [ ] **Normal Operation**: All green, up to date
- [ ] **Update Available**: Warning symbol appears
- [ ] **First Run**: "Pending" appears for update check
- [ ] **Disconnected**: "Broker: OFF" appears
- [ ] **Server Offline**: Orange icon, "Srv: OFFLINE"
- [ ] **Long Client Name**: Truncation works properly
- [ ] **Manual Update Check**: Context menu triggers check
- [ ] **Real-Time Countdown**: HB decrements every second
- [ ] **Update Check Countdown**: Time decrements properly
- [ ] **Character Limit**: Tooltip never exceeds 128 chars

---

## Related Documentation

- [Tooltip Feature Guide](TOOLTIP_FEATURE_GUIDE.md) - Detailed feature documentation
- [Client README](README_CLIENT.md) - Main client documentation
- [Auto-Update Documentation](README_AUTO_UPDATE.md) - Auto-update system details

---

**Created**: January 9, 2026  
**Feature Version**: 2.4.0+

