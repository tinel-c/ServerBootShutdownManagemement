# Automation Integration Guide

## Overview

This guide provides step-by-step instructions for integrating your existing Node-RED automation flows into the modular automation system architecture.

## Prerequisites

Before starting:
- [ ] Read `docs/AUTOMATION_ARCHITECTURE.md`
- [ ] Backup your current Node-RED flows
- [ ] Document existing functionality
- [ ] Map current MQTT topics
- [ ] Identify dependencies between flows

## Integration Strategy

### Approach 1: Gradual Migration (Recommended)

Migrate one domain at a time while keeping existing flows operational.

**Pros:**
- Lower risk
- Test incrementally
- Maintain service continuity
- Learn as you go

**Cons:**
- Takes longer
- Temporary duplication

### Approach 2: Complete Restructure

Rebuild all flows following the new architecture.

**Pros:**
- Clean slate
- Consistent structure
- Better organized

**Cons:**
- Higher risk
- Requires downtime
- All-or-nothing

## Step-by-Step Migration

### Phase 1: Planning (1-2 hours)

#### 1.1 Audit Current Flows

```bash
# Export all current flows for backup
# In Node-RED: Menu → Export → All Flows → Clipboard
# Save to: backups/flows_backup_YYYY-MM-DD.json
```

Create an inventory:

| Flow Name | Purpose | MQTT Topics | Dependencies | Priority |
|-----------|---------|-------------|--------------|----------|
| Gate Control | Open/close gates | gates/main/command | None | High |
| Light Automation | Schedule lights | lights/+/command | Sunset API | Medium |
| Irrigation | Water zones | irrigation/+/valve | Weather | High |

#### 1.2 Assign Number Ranges

Based on your domains, assign ranges:

```
Your Domains → Number Ranges:
├── Servers (existing)     → 100-199 ✓
├── Gates                  → 200-299
├── Lights                 → 300-399
├── Irrigation             → 400-499
├── SMS/Notifications      → 500-599
├── Security/Cameras       → 600-699
├── HVAC                   → 700-799
└── Energy                 → 800-899
```

#### 1.3 Design MQTT Topic Structure

Map old topics to new structure:

**Old Structure (example):**
```
gate1/command
light/living-room
irrigation/zone1
```

**New Structure:**
```
gates/main/gate1/command/open
lights/indoor/living-room/command/on
irrigation/zone1/valve/command/open
```

Create migration map in `docs/MQTT_MIGRATION_MAP.md`

### Phase 2: Preparation (2-3 hours)

#### 2.1 Update Existing Base Config

Ensure `000-base-config.json` is current with UI base and MQTT broker.

#### 2.2 Create Domain Base Configs

For each new domain:

```bash
cd nodered/templates

# Example: Gates
cp domain-base-template.json ../flows/200-gate-base-config.json

# Edit 200-gate-base-config.json:
# - Replace "DOMAIN" with "gate"
# - Replace "NUMBER" with "200"
# - Update MQTT_PREFIX to "gates"
# - Customize UI page settings
```

#### 2.3 Test Base Import

1. Import `200-gate-base-config.json`
2. Deploy
3. Verify UI page appears
4. Check context initialization
5. Fix any errors

### Phase 3: Migration by Domain

Repeat for each domain (estimated 3-6 hours per domain):

#### 3.1 Example: Migrating Gate Automation

**Current State:**
```
Old Flow: "Gate Control"
- Has open/close buttons
- Has status indicator
- Has sensor monitoring
- Mixed together in one flow
```

**Step 1: Extract Control Logic**

1. Copy `control-panel-template.json` to `210-main-gate-controls.json`

2. Edit the template:
```json
Replace:
- DOMAIN → gate
- FEATURE → main-gate  
- MQTT_PREFIX → gates/main
- ACTION1 → open
- ACTION2 → close
```

3. Copy button nodes from old flow

4. Update MQTT topics to new structure:
```javascript
// Old:
msg.topic = "gate1/command";
msg.payload = "open";

// New:
msg.topic = "gates/main/gate1/command/open";
msg.payload = {
    action: "open",
    timestamp: new Date().toISOString(),
    request_id: `open-${Date.now()}`
};
```

5. Import and test

**Step 2: Extract Status Display**

1. Create `211-main-gate-status.json` from old flow status nodes

2. Update MQTT subscription:
```javascript
// Old topic:
topic: "gate1/status"

// New topic:
topic: "gates/main/gate1/status"
```

3. Import and test

**Step 3: Extract Sensor Logic**

1. Create `212-main-gate-sensors.json`

2. Map sensor topics:
```
Old: sensor/gate1/motion → gates/main/gate1/sensor/motion
Old: sensor/gate1/position → gates/main/gate1/sensor/position
```

3. Import and test

**Step 4: Extract Automation**

1. Create `213-main-gate-automation.json`

2. Move schedule and trigger logic

3. Update to use new topics

4. Import and test

**Step 5: Parallel Operation**

Run old and new flows in parallel:

```
Old Flow (disabled)  ┐
                     ├→ Monitor for issues
New Flows (active)   ┘
```

**Step 6: Decommission Old Flow**

After 24-48 hours of stable operation:
1. Export old flow as backup
2. Delete old flow
3. Document in migration log

### Phase 4: MQTT Topic Migration

If you have devices using old topics, you need a bridge.

#### 4.1 Create Topic Bridge Flow

Create `990-mqtt-topic-bridge.json`:

```json
[
    {
        "id": "bridge_comment",
        "type": "comment",
        "name": "MQTT Topic Bridge - Temporary",
        "info": "Translates old MQTT topics to new structure.\nRemove after all devices updated."
    },
    {
        "id": "bridge_old_to_new",
        "type": "mqtt in",
        "name": "Old Topics",
        "topic": "gate1/command",
        "broker": "mqtt_broker_local",
        "wires": [["bridge_translate"]]
    },
    {
        "id": "bridge_translate",
        "type": "function",
        "name": "Translate Topic",
        "func": "// Map old topics to new\nconst topicMap = {\n    'gate1/command': 'gates/main/gate1/command',\n    'light/living-room': 'lights/indoor/living-room/command',\n    // Add more mappings\n};\n\nmsg.topic = topicMap[msg.topic] || msg.topic;\nreturn msg;",
        "wires": [["bridge_republish"]]
    },
    {
        "id": "bridge_republish",
        "type": "mqtt out",
        "name": "New Topics",
        "topic": "",
        "broker": "mqtt_broker_local",
        "wires": []
    }
]
```

#### 4.2 Update Devices Gradually

Update device configurations one by one to use new topics.

#### 4.3 Remove Bridge

Once all devices updated, delete bridge flow.

### Phase 5: Documentation

#### 5.1 Create Domain Guides

For each domain, create:

**`docs/GATE_AUTOMATION.md`**
```markdown
# Gate Automation System

## Overview
Description of gate automation features...

## Controls
- Main Gate Open/Close
- Pedestrian Gate
- Access Control

## MQTT Topics
- Commands: gates/main/gate1/command/{action}
- Status: gates/main/gate1/status
- Sensors: gates/main/gate1/sensor/{type}

## Setup
Installation and configuration...

## Troubleshooting
Common issues and solutions...
```

#### 5.2 Update Main Documentation

Add section to `README.md`:

```markdown
## 🚪 Gate Automation

Control gates and access points with automated scheduling.

### Features
- Main gate control with sensors
- Pedestrian gate access
- Scheduled opening/closing
- Motion detection
- Access logs

### Quick Start
1. Navigate to Gate Management page
2. Use control buttons for manual operation
3. Configure schedules in Automation panel

See `docs/GATE_AUTOMATION.md` for details.
```

### Phase 6: Testing & Validation

#### 6.1 Functional Testing

Test each feature:

- [ ] Manual controls work
- [ ] Status updates correctly
- [ ] Sensors report data
- [ ] Automation triggers properly
- [ ] Error handling works
- [ ] Notifications sent

#### 6.2 Integration Testing

Test interactions between domains:

- [ ] Lights turn on when gate opens (if configured)
- [ ] Cameras activate on motion
- [ ] SMS alerts on automation events

#### 6.3 Performance Testing

Monitor for issues:

```bash
# Check MQTT traffic
mosquitto_sub -h localhost -t '#' -v | wc -l

# Check Node-RED logs
journalctl -u nodered -f

# Monitor resource usage
htop
```

#### 6.4 Create Test Checklist

**`docs/TEST_CHECKLIST.md`**
```markdown
# System Test Checklist

## Gate Automation
- [ ] Main gate opens manually
- [ ] Main gate closes manually  
- [ ] Status displays correctly
- [ ] Motion sensor triggers alert
- [ ] Schedule automation works
- [ ] SMS notification sent

## Lights
...
```

### Phase 7: Optimization

#### 7.1 Review and Refactor

Look for:
- Duplicate code → Extract to utilities
- Complex functions → Break into smaller parts
- Magic numbers → Move to configuration
- Hard-coded values → Use variables

#### 7.2 Add Monitoring

Create `940-system-health.json`:

```json
// Monitor key metrics
- Message throughput
- Error rates
- Response times
- Device availability
```

#### 7.3 Document Lessons Learned

**`docs/MIGRATION_NOTES.md`**
```markdown
# Migration Notes

## What Worked Well
- Parallel operation strategy
- Incremental testing
- Topic bridge for compatibility

## Challenges
- Old flows had undocumented dependencies
- MQTT topic changes needed device updates
- UI layout adjustments took time

## Recommendations
- Start with simplest domain
- Test thoroughly before moving on
- Keep backups of everything
```

## Example: Complete Gate Migration

### Before (Old Flow)
```
Single "Gate Control" flow with:
- 25 nodes mixed together
- Unclear dependencies
- Custom MQTT topics
- No error handling
- Limited logging
```

### After (New Structure)
```
Modular flows:
├── 200-gate-base-config.json (5 nodes)
│   └── UI structure, context init
├── 210-main-gate-controls.json (12 nodes)
│   └── Control buttons, command formatting
├── 211-main-gate-status.json (8 nodes)
│   └── Status display, state tracking
├── 212-main-gate-sensors.json (10 nodes)
│   └── Motion, position sensors
└── 213-main-gate-automation.json (15 nodes)
    └── Schedule, triggers, rules

Total: 50 nodes (organized, documented, tested)
```

### Benefits Realized
- ✅ Clear separation of concerns
- ✅ Easy to update individual features
- ✅ Comprehensive error handling
- ✅ Consistent logging
- ✅ Better documentation
- ✅ Easier troubleshooting

## Common Issues & Solutions

### Issue 1: MQTT Topics Not Working

**Symptom**: Commands not reaching devices

**Cause**: Topic structure changed

**Solution**:
1. Use MQTT Explorer to verify topics
2. Check topic in function nodes
3. Implement topic bridge if needed
4. Update device configurations

### Issue 2: UI Groups Not Showing

**Symptom**: Dashboard pages empty

**Cause**: Base config not imported

**Solution**:
1. Verify base config imported first
2. Check UI group IDs match
3. Restart Node-RED if needed

### Issue 3: Context Not Persisting

**Symptom**: State lost on restart

**Cause**: Flow context not configured

**Solution**:
1. Check settings.js for context storage
2. Use persistent context if needed
3. Initialize context on startup

### Issue 4: Performance Degradation

**Symptom**: Slow response times

**Cause**: Too many messages or complex processing

**Solution**:
1. Add rate limiting
2. Optimize function nodes
3. Use change nodes instead of functions where possible
4. Check for infinite loops

## Migration Timeline Example

**Small System (3-5 domains):** 1-2 weeks
- Week 1: Planning, preparation, first domain
- Week 2: Remaining domains, testing, documentation

**Medium System (6-10 domains):** 3-4 weeks
- Week 1: Planning, preparation
- Week 2-3: Domain migration (2-3 per week)
- Week 4: Integration testing, optimization

**Large System (10+ domains):** 1-2 months
- Week 1-2: Planning, preparation
- Week 3-6: Domain migration (gradual)
- Week 7-8: Testing, optimization, documentation

## Post-Migration Checklist

- [ ] All domains migrated
- [ ] Old flows decommissioned
- [ ] Documentation complete
- [ ] Team trained on new structure
- [ ] Monitoring in place
- [ ] Backup strategy updated
- [ ] Performance baseline established
- [ ] Support documentation ready

## Getting Help

If you encounter issues during migration:

1. **Check Documentation**
   - `docs/AUTOMATION_ARCHITECTURE.md`
   - `docs/TROUBLESHOOTING.md`
   - Domain-specific guides

2. **Review Logs**
   ```bash
   journalctl -u nodered -f
   mosquitto_sub -h localhost -t '#' -v
   ```

3. **Test Incrementally**
   - Migrate one feature at a time
   - Test before moving to next
   - Keep backups

4. **Ask for Help**
   - Include error messages
   - Provide flow exports
   - Describe expected vs actual behavior

## Next Steps

After completing migration:

1. **Monitor System** (first 2 weeks)
   - Watch for errors
   - Track performance
   - Gather user feedback

2. **Optimize** (ongoing)
   - Refactor inefficient flows
   - Add missing features
   - Improve UI/UX

3. **Scale** (as needed)
   - Add new domains
   - Integrate new devices
   - Expand automation

4. **Maintain** (ongoing)
   - Regular backups
   - Update documentation
   - Version control commits

---

**Need Help?** Create an issue in the repository with:
- Description of problem
- Current flow export
- Error logs
- Expected behavior

**Good luck with your migration!** 🚀

---

**Last Updated**: 2026-01-17  
**Version**: 1.0.0
