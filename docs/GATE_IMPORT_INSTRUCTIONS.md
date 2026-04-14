# Gate Automation - Import Instructions

## Overview

The gate automation consists of **3 separate JSON files** that all import into a **single "Gate Management" tab** in Node-RED.

The **main gate** device firmware is **[PlatformIO_ESP8266_Main_Entry](https://github.com/tinel-c/PlatformIO_ESP8266_Main_Entry)** (ESP8266). Node-RED publishes opens to **`MainGate/CMD/Relay3`** (Relay 3 is the gate actuator).

## Files to Import

```
1. 200-gate-base-config.json      → Base setup & UI structure
2. 210-main-gate-controls.json    → Control switch & commands
3. 211-main-gate-status.json      → Status monitoring & SMS
4. 212-gate-telegram.json         → Telegram bot integration (Optional)
```

## Single Tab Result

All files share the same tab ID (`gate_main_tab`), so when you import them, they will appear together on one tab called **"Gate Management"**.

## Import Steps

### Step 1: Import Base Configuration

```
File: nodered/flows/200-gate-base-config.json
```

1. Open Node-RED: http://localhost:1880
2. Menu (≡) → Import
3. Click "select a file to import"
4. Select `200-gate-base-config.json`
5. Click "Import"
6. Click "Deploy"

✅ You should now see **"Gate Management"** tab with base configuration

**Contains:**
- UI page structure (`/gates`)
- 4 UI groups (Control, Status, Relays, Debug)
- Context initialization
- Position: Top section (y: 40-100)

### Step 2: Import Control Panel

```
File: nodered/flows/210-main-gate-controls.json
```

1. Menu (≡) → Import
2. Select `210-main-gate-controls.json`
3. Click "Import"
4. Click "Deploy"

✅ Control nodes added to **same "Gate Management" tab**

**Contains:**
- Relay 3 control switch (main gate)
- 1-second pulse trigger
- Command formatting
- MQTT publishing
- Error handling
- Position: Middle section (y: 140-280)

### Step 3: Import Status Monitoring

```
File: nodered/flows/211-main-gate-status.json
```

1. Menu (≡) → Import
2. Select `211-main-gate-status.json`
3. Click "Import"
4. Click "Deploy"

✅ Status nodes added to **same "Gate Management" tab**

**Contains:**
- Power status monitoring & SMS alerts
- 4 relay status displays
- Mains power monitoring
- Keypad status
- Debug messages
- Timestamp tracking
- Position: Lower section (y: 360-1040)

### Step 4: Import Telegram Integration (Optional)

```
File: nodered/flows/212-gate-telegram.json
```

**Prerequisites:**
- Telegram bot must be configured (see `nodered/TELEGRAM_SETUP.md`)
- `50-telegram-interface.json` must be imported with `telegram_bot_config` set up

1. Menu (≡) → Import
2. Select `212-gate-telegram.json`
3. Click "Import"
4. Click "Deploy"

✅ Telegram nodes added to **same "Gate Management" tab**

**Contains:**
- Telegram command handlers (`/gate_open`, `/gate_status`, `/gate_help`)
- Automatic power status notifications via Telegram
- Gate state tracking for Telegram status queries
- Integration with existing server management bot
- Position: Bottom section (y: 1360-1940)

**Telegram Commands:**
- `/gate_open` or `/gate` - Open main gate
- `/gate_status` - Get comprehensive gate status
- `/gate_help` - Show gate-specific commands
- `/help` - Show all commands (updated to include gates)

**Note:** The gate Telegram integration uses the same bot (`telegram_bot_config`) as the server management system. Both run simultaneously on one bot.

See `docs/GATE_TELEGRAM_INTEGRATION.md` for detailed usage and troubleshooting.

## Verification

### Check Node-RED Editor

You should see **ONE tab** called "Gate Management" with sections:

```
Gate Management Tab
│
├── ═══════════════ BASE CONFIGURATION ═══════════════
│   └── [Context init nodes]
│
├── ═══════════════ MAIN GATE CONTROL - Relay 3 ═══════════════
│   └── [Control switch and command nodes]
│
├── ═══════════════ POWER STATUS & SMS ALERTS ═══════════════
│   └── [Power monitoring and SMS nodes]
│
├── ═══════════════ RELAY STATUS MONITORING ═══════════════
│   └── [Relay 1-4, Mains, Keypad status nodes]
│
└── ═══════════════ DEBUG & TIMESTAMP ═══════════════
    └── [Debug messages and timestamp nodes]
```

### Check Dashboard

Navigate to: http://localhost:1880/dashboard/gates

You should see **4 UI groups:**

1. **Main Gate Control**
   - "Deschide Poarta" switch

2. **Gate Status**
   - Power status display

3. **Relay Status**
   - Relay 1, 2, 3 (main gate), 4
   - Mains Power
   - Keypad

4. **Debug & Messages**
   - Debug messages display
   - Last update timestamp

## Visual Layout in Editor

Nodes are organized spatially within the single tab:

**Vertical Sections (y-coordinates):**
```
y: 40-100     │ BASE CONFIGURATION
              │
y: 140-280    │ MAIN GATE CONTROL
              │
y: 360-780    │ POWER STATUS & SMS ALERTS
              │
y: 780-1080   │ RELAY STATUS MONITORING
              │
y: 1080+      │ DEBUG & TIMESTAMP
```

**Horizontal Layout (x-coordinates):**
```
x: 100-200    │ MQTT Inputs
x: 400-600    │ Processing & UI Elements
x: 800-1200   │ MQTT Outputs
```

## Key Features

### Same Tab, Different Files
- ✅ All 3 files use `"z": "gate_main_tab"`
- ✅ Import creates/reuses same tab
- ✅ Nodes positioned to not overlap
- ✅ Visual sections for organization

### Section Separators
Each file adds comment nodes with section headers:
```
═══════════════ SECTION NAME ═══════════════
```

These make it easy to identify which nodes belong to which feature.

### MQTT Broker
All files reference `mqtt_broker_local` which should be configured in your base Node-RED config (000-base-config.json) or update the broker settings in each file.

## Configuration

### MQTT Broker IP

Your gate uses broker: **192.168.2.4:1883**

Update in files if different:
1. Open any flow JSON file
2. Find `mqtt_broker_local` node
3. Update broker IP

### SMS Phone Number

Default: **0740244845**

To change:
- Edit `gate_status_sms_number` function in 211-main-gate-status.json
- Or set via global context: `global.set("number", "0740244845")`

## Testing

### Test 1: Control Switch

1. Go to http://localhost:1880/dashboard/gates
2. Toggle "Deschide Poarta" switch
3. Should send command to `MainGate/CMD/Relay3`

**Monitor MQTT:**
```bash
mosquitto_sub -h 192.168.2.4 -t 'MainGate/CMD/#' -v
```

### Test 2: Status Updates

Publish test status:
```bash
mosquitto_pub -h 192.168.2.4 -t 'MainGate/STAT/Relay3' -m 'ON'
mosquitto_pub -h 192.168.2.4 -t 'MainGate/STAT/eventPower' -m 'MAINS'
```

Check dashboard updates accordingly.

### Test 3: SMS Alert

1. Change power status: `MainGate/STAT/eventPower`
2. SMS should be sent to configured number
3. Check SMS gateway receives message

## Troubleshooting

### Issue: Can't see all nodes

**Zoom Out:** Ctrl + Mouse Wheel or View → Zoom Out

The tab has nodes spanning y: 0 to y: 1100, so you may need to scroll.

### Issue: Nodes overlapping

**Solution:** This shouldn't happen as y-coordinates are carefully spaced. If it does:
- Select overlapping nodes
- Use arrow keys to reposition

### Issue: Tab appears 3 times

**Cause:** Node-RED might create duplicate tabs if tab IDs conflict

**Solution:**
1. Delete all "Gate Management" tabs
2. Restart Node-RED: `sudo systemctl restart nodered`
3. Re-import files in order

### Issue: MQTT not connecting

**Check broker:**
```bash
# Verify broker is running
sudo systemctl status mosquitto

# Test connection
mosquitto_pub -h 192.168.2.4 -t 'test' -m 'hello'
```

**Update broker IP** in flow files if needed.

## Import Order

**Recommended order:** Import in sequence (200 → 210 → 211)

**Can you import in any order?** Yes! Since they all use the same tab ID, they'll merge correctly regardless of order.

**Can you re-import?** Yes, but existing nodes won't be replaced. Delete the tab first if you need to re-import fresh.

## File Management

### Export Complete Tab

To export the entire gate system:

1. Open "Gate Management" tab
2. Select All (Ctrl+A)
3. Menu → Export → Clipboard
4. Save as: `gate-complete-backup-YYYY-MM-DD.json`

### Version Control

Commit individual files:
```bash
git add nodered/flows/200-gate-base-config.json
git add nodered/flows/210-main-gate-controls.json
git add nodered/flows/211-main-gate-status.json
git commit -m "Gate automation - modular single-tab structure"
```

### Updates

To update a specific feature:
1. Delete only those nodes
2. Re-import the relevant file
3. Or edit directly in Node-RED

## Advanced: Adding More Features

To add new gate features to the same tab:

1. Create new file: `220-pedestrian-gate.json`
2. Use same tab ID: `"z": "gate_main_tab"`
3. Position below existing (y: 1200+)
4. Import - will add to same tab!

## Benefits of This Approach

### Single Tab View
- ✅ See all gate features together
- ✅ Easy to trace data flow
- ✅ No tab switching

### Modular Files
- ✅ Version control friendly
- ✅ Update features independently
- ✅ Clear file organization
- ✅ Easy to share specific features

### Best of Both Worlds
- ✅ One tab in Node-RED (simplicity)
- ✅ Separate files in filesystem (maintainability)

---

**Ready to Import!** 🚀

Start with Step 1 above and import all files in sequence:
1. Base config (200)
2. Main gate controls (210)
3. Main gate status (211)
4. Main gate Telegram (212)
5. Sliding gate controls (220)
6. Sliding gate Telegram (221)

**Need Help?** Check:
- [Gate Automation Guide](GATE_AUTOMATION.md)
- [Sliding Gate Integration](SLIDING_GATE_INTEGRATION.md)
- [Tasmota Integration](TASMOTA_GATE_INTEGRATION.md)
- [Telegram Commands Reference](TELEGRAM_COMMANDS_REFERENCE.md)
- [Migration Notes](../MIGRATION_NOTES_GATES.md)

---

**Version**: 1.1.0  
**Last Updated**: 2026-01-17  
**Files**: 200, 210, 211, 212, 220, 221  
**Features**: Main Gate + Sliding Gate + Telegram Integration
