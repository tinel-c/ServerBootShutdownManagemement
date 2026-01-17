# Node-RED Flow Templates

This directory contains templates for creating new automation domains and features. Use these as starting points to maintain consistency across the system.

## Available Templates

### 1. domain-base-template.json
Base configuration for a new automation domain. Includes:
- UI groups and page configuration
- MQTT broker reference
- Domain-specific context initialization
- Common utility functions

### 2. control-panel-template.json
Control buttons and command interface template. Includes:
- Button UI elements
- Command payload formatting
- MQTT output configuration
- Confirmation dialogs (optional)

### 3. status-display-template.json
Status monitoring and display template. Includes:
- MQTT input subscription
- State tracking function
- Real-time UI display (Vue.js)
- Status indicators and timestamps

### 4. sensor-monitoring-template.json
Sensor data collection and visualization template. Includes:
- Multi-sensor MQTT subscriptions
- Data processing and validation
- Chart/gauge displays
- Alert thresholds

### 5. automation-logic-template.json
Automated action and scheduling template. Includes:
- Schedule configuration
- Condition checking
- Action triggers
- State machine logic

## Usage

### Creating a New Domain

1. **Choose Domain Number** (see AUTOMATION_ARCHITECTURE.md)
   ```
   200-299: Gates
   300-399: Lights
   400-499: Irrigation
   etc.
   ```

2. **Copy Base Template**
   ```bash
   cp templates/domain-base-template.json flows/200-gate-base-config.json
   ```

3. **Customize the Template**
   - Replace `DOMAIN` with your domain name (e.g., "gate")
   - Replace `200` with your starting number
   - Update UI group names
   - Set MQTT topic prefix

4. **Create Feature Modules**
   ```bash
   cp templates/control-panel-template.json flows/210-main-gate-controls.json
   cp templates/status-display-template.json flows/211-main-gate-status.json
   ```

5. **Import in Order**
   - Import base config first
   - Then import feature modules
   - Deploy and test

### Naming Conventions

#### File Names
```
[number]-[domain]-[feature].json

Examples:
210-main-gate-controls.json
211-main-gate-status.json
310-indoor-lights.json
410-irrigation-zone1.json
```

#### Node IDs
```
[domain]_[feature]_[component]_[id]

Examples:
gate_main_open_button
gate_main_status_display
light_indoor_toggle_switch
irr_zone1_valve_control
```

#### MQTT Topics
```
[domain]/[location]/[device]/[type]/[action]

Examples:
gates/main/gate1/command/open
lights/indoor/living-room/command/on
irrigation/zone1/valve/command/open
```

## Template Placeholders

When using templates, replace these placeholders:

| Placeholder | Description | Example |
|------------|-------------|---------|
| `DOMAIN` | Domain name | gate, light, irrigation |
| `FEATURE` | Feature name | main-gate, zone1, living-room |
| `NUMBER` | Flow number | 210, 310, 410 |
| `MQTT_PREFIX` | Topic prefix | gates/main, lights/indoor |
| `UI_GROUP` | Group ID | ui_group_gates, ui_group_lights |

## Quick Start Examples

### Example 1: Gate Automation

```bash
# 1. Copy base template
cp templates/domain-base-template.json flows/200-gate-base-config.json

# 2. Edit and replace:
#    DOMAIN → gate
#    NUMBER → 200
#    MQTT_PREFIX → gates

# 3. Create control module
cp templates/control-panel-template.json flows/210-main-gate-controls.json

# 4. Edit and replace:
#    DOMAIN → gate
#    FEATURE → main-gate
#    NUMBER → 210
#    MQTT_PREFIX → gates/main
```

### Example 2: Lighting Control

```bash
# 1. Copy base template
cp templates/domain-base-template.json flows/300-light-base-config.json

# 2. Edit and replace:
#    DOMAIN → light
#    NUMBER → 300
#    MQTT_PREFIX → lights

# 3. Create control module
cp templates/control-panel-template.json flows/310-indoor-lights.json

# 4. Edit and replace:
#    DOMAIN → light
#    FEATURE → indoor
#    NUMBER → 310
#    MQTT_PREFIX → lights/indoor
```

### Example 3: Irrigation System

```bash
# 1. Copy base template
cp templates/domain-base-template.json flows/400-irrigation-base-config.json

# 2. Create zone modules
cp templates/control-panel-template.json flows/410-irrigation-zone1.json
cp templates/status-display-template.json flows/411-irrigation-zone1-status.json
cp templates/sensor-monitoring-template.json flows/412-irrigation-zone1-sensors.json
cp templates/automation-logic-template.json flows/413-irrigation-zone1-automation.json
```

## Testing Checklist

After creating new flows from templates:

- [ ] All node IDs are unique
- [ ] MQTT topics follow naming convention
- [ ] UI groups are properly linked
- [ ] Error handling is in place
- [ ] Logging is configured
- [ ] Context variables are initialized
- [ ] Comments are added for complex logic
- [ ] Documentation is created
- [ ] Integration tests pass
- [ ] Security permissions are set

## Common Customizations

### Adding Authentication
```javascript
// In function node
if (!msg.req || !msg.req.user) {
    msg.payload = { error: "Unauthorized" };
    return [null, msg];
}
```

### Adding Confirmation Dialog
```json
{
    "type": "ui-button",
    "confirmationRequired": true,
    "confirmationMessage": "Are you sure?"
}
```

### Adding Rate Limiting
```javascript
// In function node
const lastCommand = flow.get('lastCommand') || 0;
const now = Date.now();
if (now - lastCommand < 5000) {
    node.warn("Rate limit exceeded");
    return null;
}
flow.set('lastCommand', now);
```

### Adding Retry Logic
```javascript
// In function node
const maxRetries = 3;
const retryCount = msg.retryCount || 0;

if (retryCount < maxRetries) {
    msg.retryCount = retryCount + 1;
    // Retry after delay
    setTimeout(() => node.send(msg), 1000);
} else {
    node.error("Max retries exceeded");
}
```

## Best Practices

1. **Always start with base config** - Import domain base before features
2. **Use unique IDs** - Generate new IDs for each flow
3. **Follow naming conventions** - Maintain consistency
4. **Document changes** - Add comments and update docs
5. **Test incrementally** - Import and test one flow at a time
6. **Version control** - Commit after each working feature
7. **Handle errors** - Add catch nodes and logging
8. **Validate inputs** - Check message structure
9. **Set QoS properly** - Commands=1, Status=0
10. **Use context wisely** - Store state, not large data

## Troubleshooting

### Common Issues

**Issue**: "Node configuration error" on import
- **Cause**: Missing dependencies (base config, MQTT broker)
- **Solution**: Import base config first

**Issue**: Duplicate node IDs
- **Cause**: Copy-paste without changing IDs
- **Solution**: Generate new UUIDs for all nodes

**Issue**: MQTT messages not received
- **Cause**: Incorrect topic subscription
- **Solution**: Verify topic matches publisher

**Issue**: UI not displaying
- **Cause**: Missing UI group or page
- **Solution**: Import base config with UI structure

## Support

For detailed guidance, see:
- `docs/AUTOMATION_ARCHITECTURE.md` - System architecture
- `docs/AUTOMATION_INTEGRATION_GUIDE.md` - Step-by-step integration
- `nodered/NODE_RED_DEVELOPMENT.md` - Development guide

---

**Last Updated**: 2026-01-17
