# Irrigation Zones Conversion - Step by Step

## 📋 Steps to Convert

### 1. Paste Your Original Flow
Open `nodered/flows/420-irrigation-zones-ORIGINAL.json` and replace the entire content with your original irrigation flow JSON (the one you provided in your message).

**Make sure:**
- The content starts with `[`
- The content ends with `]`
- It's valid JSON

### 2. Run the Conversion Script
```bash
cd D:\NextCloud\Git\ServerBootShutdownMangement
python convert_irrigation_zones.py
```

### 3. What the Script Does

The script will automatically:
- ✅ Convert all 12 `ui_switch` nodes → `ui-switch` (Dashboard 2.0)
- ✅ Convert the Power `ui_switch` → `ui-switch` (Dashboard 2.0)
- ✅ Convert all `ui_button` nodes → `ui-button` (Dashboard 2.0)
- ✅ Convert all `ui_text` nodes → `ui-text` (Dashboard 2.0)
- ✅ Add boolean conversion nodes (ON/OFF ↔ true/false)
- ✅ Add state tracking to global context
- ✅ Update MQTT in node wires
- ✅ Enable `rap: true` for retained messages
- ❌ **PRESERVE** all automation nodes (zone-timer, zone in, run-gate, program, etc.)
- ❌ **PRESERVE** all wiring and connections
- ❌ **PRESERVE** all MQTT, link, switch, change, delay nodes

### 4. Output
The script creates: `nodered/flows/420-irrigation-zones-controls.json`

### 5. Import and Test in Node-RED
1. In Node-RED, import `420-irrigation-zones-controls.json`
2. Deploy
3. Test:
   - [ ] All 12 zones toggle correctly
   - [ ] 24V power switch works
   - [ ] Start button triggers automation
   - [ ] Pause/Skip/Resume work
   - [ ] Status displays update
   - [ ] Automated sequences run
   - [ ] Pump coordination works

### 6. Commit
Once tested and working:
```bash
git add nodered/flows/420-irrigation-zones-controls.json
git commit -m "feat(irrigation): convert zones to Dashboard 2.0

Converted 12-zone irrigation system from legacy UI to Dashboard 2.0:
✓ 12 zone switches (ui_switch → ui-switch)
✓ Power switch (24V)
✓ Control buttons (Start/Pause/Resume)
✓ Status displays
✓ Boolean conversion added
✓ State tracking in global context
✓ Preserved node-red-contrib-sprinkler automation"
```

## 🛠️ Troubleshooting

### Script Error: "File not found"
- Make sure you pasted your flow into `420-irrigation-zones-ORIGINAL.json`
- Check the file path

### Script Error: "Invalid JSON"
- Verify your pasted content is valid JSON
- Use a JSON validator

### Node-RED: Nodes missing after import
- Check that all required nodes are installed:
  - `@flowfuse/node-red-dashboard` (Dashboard 2.0)
  - `node-red-contrib-sprinkler` (scheduling)
  - `node-red-contrib-simpletime` (timestamps)

### Switches don't work
- Check MQTT broker is running
- Verify device topics match: `stat/IrigationSystem/POWERX`
- Check global context initialization

### Automation doesn't run
- Verify all `zone-timer`, `zone in`, `run-gate` nodes are present
- Check `program` node configuration
- Test with Start button

## 📁 Files Created
- `nodered/flows/420-irrigation-zones-ORIGINAL.json` - Your original flow (paste here)
- `convert_irrigation_zones.py` - Conversion script
- `nodered/flows/420-irrigation-zones-controls.json` - Converted output

## 🎯 Ready?
1. Paste your flow into `420-irrigation-zones-ORIGINAL.json`
2. Run `python convert_irrigation_zones.py`
3. Import the output into Node-RED
4. Test and commit!
