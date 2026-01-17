# Sliding Gate Automation - Integration Guide

## Overview

The **Primary Sliding Gate** automation provides control for a sliding gate system with 4 independent relays. This is different from the Main Gate and uses a separate Tasmota device.

## Hardware

**Device**: Tasmota-based relay controller  
**MQTT Topic**: `automatizare_poarta`  
**Relays**: 4 independent relays (POWER1-4)

## Features

### Relay Functions

| Relay | Label | Function | Icon | Color |
|-------|-------|----------|------|-------|
| Relay 1 | Deschide (Open) | Opens the sliding gate | ↑ | Green |
| Relay 2 | Inchide (Close) | Closes the sliding gate | ↓ | Red |
| Relay 3 | Trigger | Triggers gate automation | ⟳ | Blue |
| Relay 4 | Deschide (Open) | Alternative open control | ↑ | Green |

### Control Method

All relays use **1-second pulse control**:
1. User toggles switch in dashboard
2. System sends ON command
3. After 1 second, system automatically sends OFF command
4. Prevents relay from staying on continuously

## MQTT Topics

### Status Topics (Subscribed)
```
stat/automatizare_poarta/POWER1   - Relay 1 status (Open)
stat/automatizare_poarta/POWER2   - Relay 2 status (Close)
stat/automatizare_poarta/POWER3   - Relay 3 status (Trigger)
stat/automatizare_poarta/POWER4   - Relay 4 status (Open Alt)
```

### Command Topics (Published)
```
cmnd/automatizare_poarta/Power1   - Control Relay 1 (Open)
cmnd/automatizare_poarta/Power2   - Control Relay 2 (Close)
cmnd/automatizare_poarta/Power3   - Control Relay 3 (Trigger)
cmnd/automatizare_poarta/Power4   - Control Relay 4 (Open Alt)
```

## Flow Structure

### File: `220-sliding-gate-controls.json`

**Tab**: `gate_main_tab` (same as Main Gate)  
**UI Group**: `ui_group_sliding_gate` ("Automatizare poarta")  
**Position**: y: 500-750

### Node Flow Pattern (per relay)

```
MQTT In → Change Node → UI Switch → Trigger (1s) → MQTT Out
         (stat/)      (ON/OFF to    (Dashboard) (Pulse)    (cmnd/)
                       boolean)
```

### Flow Details

1. **MQTT Input**: Subscribes to status topic
2. **Change Node**: Converts Tasmota's "ON"/"OFF" to boolean true/false
3. **UI Switch**: Dashboard control with custom icons and colors
4. **Trigger Node**: Creates 1-second pulse (true → false)
5. **MQTT Output**: Publishes command to Tasmota

## Dashboard

### UI Group: "Automatizare poarta"

Located on the Gate Management page (`/gates`):

```
┌─────────────────────────────┐
│  Automatizare poarta        │
├─────────────────────────────┤
│  ↑ Deschide   [  OFF  ]     │  ← Relay 1 (Open)
│  ↓ Inchide    [  OFF  ]     │  ← Relay 2 (Close)
│  ⟳ Trigger    [  OFF  ]     │  ← Relay 3 (Trigger)
│  ↑ Deschide   [  OFF  ]     │  ← Relay 4 (Open Alt)
└─────────────────────────────┘
```

### Switch Icons

- **Open** (Relays 1 & 4): `arrow_upward` - Green when ON
- **Close** (Relay 2): `arrow_downward` - Red when ON
- **Trigger** (Relay 3): `sync` - Blue when ON

## Usage

### Opening the Gate

**Option 1**: Use Relay 1 (primary)
1. Click "Deschide" switch (Relay 1)
2. System sends 1-second pulse
3. Gate opens

**Option 2**: Use Relay 4 (alternative)
1. Click second "Deschide" switch (Relay 4)
2. System sends 1-second pulse
3. Gate opens

### Closing the Gate

1. Click "Inchide" switch (Relay 2)
2. System sends 1-second pulse
3. Gate closes

### Using Trigger

1. Click "Trigger" switch (Relay 3)
2. System sends 1-second pulse
3. Gate automation sequence triggered

**Note**: The trigger function behavior depends on your gate controller configuration.

## Integration with Main Gate

Both gates coexist on the same dashboard:

```
Gate Management Page
│
├── Main Gate Control (Relay 2)
│   └── Single control switch
│
├── Gate Status (Main Gate)
│   ├── Power status
│   ├── Relay states
│   ├── Mains status
│   └── Keypad status
│
└── Automatizare poarta (Sliding Gate)
    ├── Relay 1 - Open
    ├── Relay 2 - Close
    ├── Relay 3 - Trigger
    └── Relay 4 - Open (Alt)
```

## Configuration

### MQTT Broker

Uses the same MQTT broker as Main Gate:
- **Host**: 192.168.2.4 (or configured in base config)
- **Port**: 1883
- **Client ID**: Auto-generated
- **QoS**: 2 (exactly once delivery)

### Tasmota Device Configuration

Configure your Tasmota device with:

1. **MQTT Settings**:
   ```
   Topic: automatizare_poarta
   Full Topic: %prefix%/%topic%/
   ```

2. **Module Configuration**:
   - Set as "Generic (18)"
   - Configure GPIO for 4 relays

3. **PowerOnState**:
   ```
   PowerOnState 0
   ```
   (Keeps relays OFF after power cycle)

4. **PulseTime** (Optional):
   ```
   PulseTime1 10  (Relay 1: 1 second)
   PulseTime2 10  (Relay 2: 1 second)
   PulseTime3 10  (Relay 3: 1 second)
   PulseTime4 10  (Relay 4: 1 second)
   ```
   **Note**: Node-RED already handles the pulse, but this provides backup.

## Import Instructions

### Prerequisites
- `200-gate-base-config.json` must be imported first
- MQTT broker must be running
- Tasmota device must be configured

### Import Steps

1. Open Node-RED: http://localhost:1880
2. Menu (≡) → Import
3. Select `220-sliding-gate-controls.json`
4. Click "Import"
5. Deploy

### Verification

1. Check dashboard: http://localhost:1880/dashboard/gates
2. You should see "Automatizare poarta" group
3. Test each relay switch
4. Verify MQTT commands are published:
   ```bash
   mosquitto_sub -t "cmnd/automatizare_poarta/#" -v
   ```

## Troubleshooting

### Switches Don't Respond

**Check MQTT connection**:
```bash
# Subscribe to status
mosquitto_sub -t "stat/automatizare_poarta/#" -v

# Publish test command
mosquitto_pub -t "cmnd/automatizare_poarta/Power1" -m "ON"
```

### Relays Stay ON

**Problem**: Trigger node not working

**Solution**:
1. Check trigger node configuration (should be 1 second)
2. Verify boolean conversion is working
3. Check Tasmota PulseTime settings

### Wrong Relay Activates

**Problem**: MQTT topics mismatched

**Solution**:
1. Verify Tasmota topic is exactly: `automatizare_poarta`
2. Check relay numbering (POWER1-4)
3. Test with mosquitto_sub to see actual topics

### UI Not Showing

**Problem**: UI group not created

**Solution**:
1. Import `200-gate-base-config.json` first
2. Check that `ui_group_sliding_gate` exists
3. Deploy flows

## Advanced Configuration

### Custom Pulse Duration

To change pulse duration, edit the trigger nodes:

```javascript
// In trigger node
duration: "1"    // Change to desired seconds
units: "s"       // Can be: "ms", "s", "min", "hr"
```

### Custom Icons

To change switch icons, edit the ui-switch nodes:

```javascript
// Available Material Design Icons
onicon: "arrow_upward"     // Open
onicon: "arrow_downward"   // Close
onicon: "sync"             // Trigger
onicon: "power_settings_new" // Power
onicon: "settings_remote"   // Remote
```

### Custom Colors

```javascript
// In ui-switch node
oncolor: "green"   // Open
oncolor: "red"     // Close
oncolor: "blue"    // Trigger
oncolor: "yellow"  // Custom
```

## Comparison: Main Gate vs Sliding Gate

| Feature | Main Gate | Sliding Gate |
|---------|-----------|--------------|
| **MQTT Topic** | `MainGate` | `automatizare_poarta` |
| **Relays Used** | 1 (Relay 2) | 4 (Power 1-4) |
| **Functions** | Single control | Open, Close, Trigger, Open Alt |
| **Status Monitoring** | Full (power, relays, mains, keypad) | Basic (relay states) |
| **SMS Alerts** | Yes (power changes) | No |
| **Telegram** | Yes | Future enhancement |
| **UI Icons** | Lock/Unlock | Arrows and Sync |

## Future Enhancements

### Planned Features

1. **Status Monitoring**:
   - Add comprehensive status like Main Gate
   - Monitor gate position sensors
   - Track open/close cycles

2. **Telegram Integration**:
   - `/sliding_open` - Open sliding gate
   - `/sliding_close` - Close sliding gate
   - `/sliding_status` - Get sliding gate status

3. **Automation**:
   - Auto-close after X minutes
   - Scheduled opening/closing
   - Integration with presence detection

4. **Safety Features**:
   - Obstruction detection
   - Auto-reverse on obstacle
   - Manual override lockout

## Related Documentation

- **Base Configuration**: `200-gate-base-config.json` implementation
- **Main Gate**: `docs/GATE_AUTOMATION.md`
- **Tasmota**: `docs/TASMOTA_GATE_INTEGRATION.md`
- **Import Guide**: `docs/GATE_IMPORT_INSTRUCTIONS.md`

---

**Version**: 1.0.0  
**Last Updated**: January 2026  
**Status**: Operational  
**Relays**: 4 (Open, Close, Trigger, Open Alt)
