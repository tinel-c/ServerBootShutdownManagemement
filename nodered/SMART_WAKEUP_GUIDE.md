# Smart Client-Aware Wake-Up Guide

## Overview
The automation system now intelligently boots the server when clients need it, with built-in protection against command spam.

## How It Works

### Scenario 1: Client Boots, Server is Down
```
┌─────────────────────────────────────────────────┐
│ 1. User turns on their PC                      │
│ 2. Client monitor starts → Sends presence      │
│ 3. Node-RED detects: clients=1, server=down    │
│ 4. Automation: "Clients need server!"          │
│ 5. Sends WOL boot command                      │
│ 6. Starts 5-minute cooldown                    │
│ 7. Server boots up (~2-3 minutes)              │
│ 8. Health checks return → Server UP            │
│ 9. Client can now access resources ✓           │
└─────────────────────────────────────────────────┘
```

### Scenario 2: Multiple Clients Boot Simultaneously
```
┌─────────────────────────────────────────────────┐
│ 1. Three PCs boot at same time                 │
│ 2. All send presence messages                  │
│ 3. Node-RED detects: clients=3, server=down    │
│ 4. Sends ONE boot command (not three)          │
│ 5. Cooldown prevents duplicate commands        │
│ 6. All clients wait for server to boot         │
└─────────────────────────────────────────────────┘
```

### Scenario 3: Server Stuck, Needs Retry
```
┌─────────────────────────────────────────────────┐
│ 1. Boot command sent at 10:00                  │
│ 2. Cooldown active until 10:05                 │
│ 3. At 10:05, if server still down:             │
│    → Sends another boot command                │
│    → New 5-minute cooldown starts              │
│ 4. Retries until server comes up               │
└─────────────────────────────────────────────────┘
```

## Visual Indicators

### Cooldown Banner
When a boot command is sent, you'll see:

```
┌─────────────────────────────────────────────────┐
│ ⏳ Boot cooldown: 4:35 (waiting for state...) │
└─────────────────────────────────────────────────┘
```

**Color Coding:**
- 🟢 **Green Banner** = Boot cooldown (server starting up)
- 🔴 **Red Banner** = Shutdown cooldown (server shutting down)

**What it means:**
- System has sent a command
- Waiting for server to complete the operation
- Will NOT send duplicate commands during this time
- Countdown shows time remaining

### Activity Log Entries
All events are logged with full details, including the trigger moments:

```
17:30:42  🟢 Trigger  [client_online]  First client connected: DESKTOP-PC  DETECTED
17:30:45  🚀 Boot     [wol]            2 client(s) need server             SENT
```

**Fields:**
- **Timestamp:** Exact time event occurred
- **Action:** 🟢 Trigger (client event) or 🚀 Boot (command)
- **Type:** [client_online], [client_offline], [wol], etc.
- **Trigger:** What caused it ("First client connected: DESKTOP-PC")
- **Status:** DETECTED (observed) or SENT (command transmitted)

**Client Trigger Events:**
- 🟢 **First client connects** - Green indicator, triggers boot logic
- 🔴 **Last client disconnects** - Orange indicator, triggers grace period

## Configuration

### Cooldown Duration
**Default:** 5 minutes (300 seconds)

**Why 5 minutes?**
- Typical server boot time: 2-3 minutes
- Typical graceful shutdown: 1-2 minutes
- Buffer time for health checks
- Prevents IPMI/WOL command spam

### When Cooldown Applies
✅ **Applies to:**
- Client-aware boot (smart wake-up)
- Watchdog recovery boot (health loss)
- Graceful shutdown execution

❌ **Does NOT apply to:**
- First client online (immediate boot)
- Grace period initiation (5-minute countdown)
- Shutdown cancellation (client connects during grace)

## Troubleshooting

### Problem: Server won't boot
**Check:**
1. Is cooldown active? (Look for banner)
2. Check activity log - was command sent?
3. Is automation enabled? (Toggle should show "AUTOMATED")
4. Check server power/network cables
5. Verify WOL is enabled in BIOS

### Problem: Too many boot attempts
**Cause:** Server may not be reporting health status

**Solution:**
1. Check health monitor service is running
2. Verify MQTT connection
3. Check network connectivity
4. Review health monitor logs

### Problem: Server boots but immediately shuts down
**Cause:** No clients detected + idle server detection

**Solution:**
1. Ensure client monitor is running on your PC
2. Check client presence messages in MQTT
3. Verify heartbeat messages every 60 seconds
4. Review client tracking logs

## Advanced: Adjusting Cooldown

If you need to adjust the 5-minute cooldown:

1. Open Node-RED flow editor
2. Find node: "Watchdog & Grace Loop"
3. Edit the function
4. Change this line:
```javascript
const COMMAND_COOLDOWN_MS = 5 * 60 * 1000; // 5 minutes
```

To (example - 3 minutes):
```javascript
const COMMAND_COOLDOWN_MS = 3 * 60 * 1000; // 3 minutes
```

5. Deploy changes

**⚠️ Warning:** Setting cooldown too low may cause:
- Command spam
- IPMI/iLO overload
- False positive triggers
- Unnecessary wear on hardware

## Best Practices

1. **Let it work:** The system is designed to handle everything automatically
2. **Monitor the log:** Check activity log to see what's happening
3. **Trust the cooldown:** If banner shows, a command was sent - be patient
4. **Health checks matter:** Ensure health monitor is always running
5. **Client monitoring:** Keep client monitor running on all PCs

## Example Workflow

### Typical Daily Use:
```
08:00 → You arrive at work, turn on PC
        ↓
08:00 → Client monitor starts, sends presence
        ↓
        📋 Activity Log: 🟢 Trigger [client_online] DETECTED
        ↓
08:00 → Automation detects: client=1, server=down
        ↓
08:00 → Sends WOL boot command
        ↓
        📋 Activity Log: 🚀 Boot [wol] SENT
        ↓
08:00 → Cooldown banner appears (5:00 countdown)
        ↓
08:02 → Server finishes booting
        ↓
08:02 → Health checks report: Server UP
        ↓
08:02 → You can access network shares, services ✓
        ↓
18:00 → You shutdown your PC
        ↓
18:00 → Client sends offline presence
        ↓
        📋 Activity Log: 🔴 Trigger [client_offline] DETECTED
        ↓
18:00 → Automation: Last client offline
        ↓
18:00 → Grace period starts (5:00 countdown)
        ↓
        📋 Activity Log: ⏱️ Grace Period [countdown] STARTED
        ↓
18:05 → No clients returned
        ↓
18:05 → Server gracefully shuts down
        ↓
        📋 Activity Log: ⏹️ Shutdown [graceful] EXECUTED
        ↓
18:05 → Power saved until next morning 💰
```

## Support

For issues or questions:
1. Check activity log first
2. Review health monitor status
3. Verify client monitor is running
4. Check MQTT broker connectivity
5. See [TROUBLESHOOTING.md](../docs/TROUBLESHOOTING.md)

---

**Last Updated:** January 7, 2026  
**Feature Version:** 2.3.0

