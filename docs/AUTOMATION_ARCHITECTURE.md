# Automation System Architecture

## Overview

The Server Boot/Shutdown Management system has been extended to support multiple automation domains through a scalable, modular architecture. Each automation domain (servers, gates, lights, irrigation, SMS, etc.) is managed through independent, self-contained Node-RED flow modules.

## Design Philosophy

### Core Principles

1. **Domain Isolation**: Each automation domain is independent and self-contained
2. **Modular Design**: Features can be added, updated, or removed without affecting others
3. **Consistent Structure**: All domains follow the same organizational pattern
4. **Scalability**: Easy to add new automation types without restructuring
5. **Maintainability**: Clear naming conventions and documentation

## Modular Flow Structure

### Numbering System

Flows are organized by domain using a three-digit prefix system:

```
[Domain][Category][Feature]
 └─ 00-99  └─ 0-9    └─ 0-9

Examples:
- 00x: Core infrastructure (shared)
- 10x-19x: Server Management (Dell, HP, etc.)
- 20x-29x: Gate Automation
- 30x-39x: Lighting Control
- 40x-49x: Irrigation System
- 50x-59x: SMS/Notification System
- 60x-69x: Security/Cameras
- 70x-79x: HVAC/Climate Control
- 80x-89x: Energy Management
- 90x-99x: Shared Utilities (logs, alerts, etc.)
```

### Detailed Numbering Scheme

#### Core Infrastructure (000-099)
- `000-009`: Base configuration (UI, MQTT, themes)
- `010-019`: Reserved for future core features

#### Server Management Domain (100-199)
- `100-109`: Base server infrastructure
- `110-119`: Dell T310 (controls, status, health)
- `120-129`: HP DL360p (controls, status, health)
- `130-139`: Reserved for Server 3
- `140-149`: Client PC management
- `150-159`: Telegram interface
- `190-199`: Server utilities

#### Gate Automation Domain (200-299)
- `200-209`: Base gate infrastructure
- `210-219`: Main Gate (controls, status, sensors)
- `220-229`: Pedestrian Gate (controls, status, sensors)
- `230-239`: Garage Door (controls, status, sensors)
- `240-249`: Access Control System
- `250-259`: Gate scheduling and automation
- `290-299`: Gate utilities and logs

#### Lighting Control Domain (300-399)
- `300-309`: Base lighting infrastructure
- `310-319`: Indoor Lights (zones, scenes, schedules)
- `320-329`: Outdoor Lights (perimeter, garden, security)
- `330-339`: Smart Bulbs (individual control)
- `340-349`: Lighting automation (motion, schedules)
- `350-359`: Energy monitoring
- `390-399`: Lighting utilities

#### Irrigation System Domain (400-499)
- `400-409`: Base irrigation infrastructure
- `410-419`: Zone 1 (lawn front)
- `420-429`: Zone 2 (lawn back)
- `430-439`: Zone 3 (garden)
- `440-449`: Zone 4 (greenhouse)
- `450-459`: Weather integration
- `460-469`: Soil moisture sensors
- `470-479`: Scheduling and automation
- `490-499`: Irrigation utilities

#### SMS/Notification System (500-599)
- `500-509`: Base notification infrastructure
- `510-519`: SMS gateway
- `520-529`: Email notifications
- `530-539`: Telegram notifications
- `540-549`: Push notifications
- `550-559`: Alert rules and triggers
- `560-569`: Notification history
- `590-599`: Notification utilities

#### Security/Camera Domain (600-699)
- `600-609`: Base security infrastructure
- `610-619`: Camera 1 (front entrance)
- `620-629`: Camera 2 (back yard)
- `630-639`: Camera 3 (garage)
- `640-649`: Motion sensors
- `650-659`: Alarm system
- `660-669`: Recording and storage
- `690-699`: Security utilities

#### HVAC/Climate Control (700-799)
- `700-709`: Base HVAC infrastructure
- `710-719`: Heating system
- `720-729`: Cooling/AC system
- `730-739`: Ventilation
- `740-749`: Temperature sensors
- `750-759`: Humidity control
- `760-769`: Scheduling and automation
- `790-799`: HVAC utilities

#### Energy Management (800-899)
- `800-809`: Base energy infrastructure (`800-energy-base-config.json`)
- `810-819`: Victron Cerbo GX (`811-victron-energy-status.json`, `812-victron-energy-telegram.json`)
- `820-829`: Huawei SUN2000 solar (`821-huawei-energy-status.json`, `822-huawei-energy-telegram.json`)
- `830-839`: Battery storage
- `840-849`: Smart plugs/switches
- `850-859`: Energy analytics
- `860-869`: Cost tracking
- `890-899`: Energy utilities

#### Shared Utilities (900-999)
- `900-909`: System logs and console
- `910-919`: Dashboard home/navigation
- `920-929`: Global alerts and notifications
- `930-939`: System health monitoring
- `940-949`: Database/storage
- `950-959`: API integrations
- `990-999`: Debug and troubleshooting

## File Naming Convention

### Pattern
```
[Domain]-[Category]-[Feature].json

Examples:
- 000-base-config.json
- 110-dell-controls.json
- 111-dell-status.json
- 210-main-gate-controls.json
- 211-main-gate-status.json
- 310-indoor-lights.json
- 410-irrigation-zone1.json
```

### Component Naming
```
[domain]_[category]_[feature]_[type]

Examples:
- srv_dell_boot_button
- gate_main_open_button
- light_outdoor_toggle_switch
- irr_zone1_timer
- sms_alert_trigger
```

## MQTT Topic Structure

### Hierarchical Organization

```
[domain]/[location]/[device]/[type]/[action]

Examples:
servers/dell/t310/command/boot
gates/main/gate1/command/open
lights/outdoor/perimeter/command/on
irrigation/zone1/valve/command/open
sms/alert/system/status
```

### Topic Patterns

#### Commands (Dashboard → Devices)
```
{domain}/{location}/{device}/command/{action}

Examples:
gates/main/gate1/command/open
lights/indoor/living-room/command/on
irrigation/zone1/valve/command/open
```

#### Status (Devices → Dashboard)
```
{domain}/{location}/{device}/status
{domain}/{location}/{device}/state

Examples:
gates/main/gate1/status
lights/indoor/living-room/state
irrigation/zone1/valve/status
```

#### Sensors (Devices → Dashboard)
```
{domain}/{location}/{sensor}/sensor/{type}

Examples:
gates/main/sensor/motion
irrigation/zone1/sensor/moisture
lights/outdoor/sensor/ambient-light
```

#### Automation Events
```
automation/{domain}/event/{event-type}

Examples:
automation/gates/event/car-detected
automation/lights/event/sunset
automation/irrigation/event/rain-detected
```

## Dashboard Organization

### Page Structure

```
Home Dashboard
├── Server Management
│   ├── Dell T310 Control
│   ├── HP DL360p Control
│   └── Client PCs
├── Gate Management
│   ├── Main Gate
│   ├── Pedestrian Gate
│   └── Access Logs
├── Lighting Control
│   ├── Indoor Lights
│   ├── Outdoor Lights
│   └── Scenes
├── Irrigation
│   ├── Zone Management
│   ├── Schedule
│   └── Weather
├── Security
│   ├── Cameras
│   ├── Sensors
│   └── Alerts
└── System
    ├── Notifications
    ├── Logs
    └── Settings
```

### Navigation Flow

```
Main Menu (Sidebar)
├── 🏠 Home
├── 🖥️ Servers
│   ├── Dell T310
│   └── HP DL360p
├── 🚪 Gates
│   ├── Main Gate
│   └── Pedestrian Gate
├── 💡 Lights
│   ├── Indoor
│   └── Outdoor
├── 💧 Irrigation
│   ├── Zones
│   └── Schedule
├── 📱 Notifications
└── ⚙️ Settings
```

## Implementation Guide

### Adding a New Automation Domain

#### Step 1: Reserve Number Range
Choose an available 100-number range (e.g., 200-299 for gates)

#### Step 2: Create Base Configuration
```
200-gate-base-config.json
- MQTT topic definitions
- UI groups
- Common functions
- Shared variables
```

#### Step 3: Create Feature Modules
```
210-main-gate-controls.json     # Control buttons
211-main-gate-status.json       # Status display
212-main-gate-sensors.json      # Sensor monitoring
213-main-gate-automation.json   # Automated actions
```

#### Step 4: Create Documentation
- Feature guide in `docs/GATE_AUTOMATION.md`
- MQTT protocol in `docs/MQTT_GATES.md`
- User guide in `docs/GATE_USER_GUIDE.md`

#### Step 5: Update Main Documentation
- Add domain to README.md
- Update ARCHITECTURE.md
- Add to QUICK_REFERENCE.md

### Module Template Structure

Each feature module should contain:

1. **MQTT Subscriptions** - Listen for device updates
2. **MQTT Publications** - Send commands to devices
3. **UI Components** - Buttons, status displays, charts
4. **Business Logic** - Function nodes for processing
5. **Error Handling** - Catch and log errors
6. **State Management** - Context storage for persistence

## Integration Patterns

### Pattern 1: Simple Control
```
Button → Function → MQTT Out → Device
Device → MQTT In → Function → UI Update
```

### Pattern 2: Sensor Monitoring
```
Sensor → MQTT In → Function (process) → UI Display
                                      → Alert Trigger
                                      → Data Logger
```

### Pattern 3: Automated Action
```
Trigger → Function (rules) → Decision Node → Action
    ↓                            ↓              ↓
Schedule                     Conditions      MQTT Out
Sensor                       Checks          Device Control
Event                        Validation      Notification
```

### Pattern 4: Complex Workflow
```
Input Event → Validation → State Check → Action Sequence
    ↓            ↓            ↓              ↓
Multiple      Schema       Context        Multiple Steps
Sources       Check        Lookup         Parallel Actions
Sensors       Auth         Rules          Error Handling
```

## Best Practices

### Domain Design

1. **Single Responsibility**: Each flow should have one clear purpose
2. **Loose Coupling**: Minimize dependencies between domains
3. **High Cohesion**: Related functionality stays together
4. **Clear Interfaces**: Well-defined MQTT topic contracts

### Node-RED Development

1. **Use Link Nodes**: For cross-flow communication within domain
2. **Context Storage**: Use flow context for domain state
3. **Error Handling**: Catch nodes on every MQTT/HTTP request
4. **Logging**: Consistent log format across all domains
5. **Comments**: Document complex logic in function nodes

### MQTT Design

1. **Consistent Naming**: Follow the hierarchical topic structure
2. **QoS Levels**: Use QoS 1 for commands, QoS 0 for telemetry
3. **Retained Messages**: Use for status topics
4. **Last Will**: Configure for device connectivity
5. **JSON Payloads**: Standardized message format

### UI Design

1. **Consistent Layout**: Same structure across all domains
2. **Color Coding**: Standard colors for states (green=on, red=off)
3. **Responsive**: Works on desktop, tablet, and mobile
4. **Accessibility**: Clear labels and status indicators
5. **Performance**: Optimize updates and rendering

## Security Considerations

### Access Control

1. **Authentication**: Node-RED password protection
2. **Authorization**: Role-based access per domain
3. **MQTT ACLs**: Topic-level permissions
4. **API Keys**: Secure external integrations
5. **Audit Logs**: Track all user actions

### Network Security

1. **MQTT over TLS**: Encrypted broker communication
2. **HTTPS**: Secure dashboard access
3. **VPN**: Remote access via secure tunnel
4. **Firewall**: Restrict external access
5. **Segmentation**: Separate IoT network

### Data Protection

1. **Credentials**: Store in environment variables
2. **Sensitive Data**: Encrypt at rest
3. **Backup**: Regular automated backups
4. **Retention**: Data lifecycle policies
5. **Privacy**: Minimize data collection

## Monitoring and Maintenance

### Health Checks

1. **Service Status**: All components running
2. **MQTT Connectivity**: Broker reachable
3. **Device Availability**: Devices responding
4. **Error Rates**: Monitor failures
5. **Performance**: Response times

### Logging Strategy

```
System Logs (900-log-console.json)
├── Info: Normal operations
├── Warning: Degraded performance
├── Error: Failed operations
└── Critical: System failures

Per-Domain Logs
├── Domain-specific events
├── State changes
├── User actions
└── Automation triggers
```

### Backup and Recovery

1. **Node-RED Flows**: Version control in Git
2. **Configuration**: Backup .env and YAML files
3. **Database**: Regular exports
4. **Documentation**: Keep current
5. **Test Restores**: Verify backups work

## Migration Guide

### From Existing Node-RED Setup

1. **Audit Current Flows**
   - Document all existing functionality
   - Identify dependencies
   - Map MQTT topics

2. **Plan Organization**
   - Assign number ranges to domains
   - Group related functionality
   - Design MQTT topic structure

3. **Create Base Modules**
   - Extract common infrastructure
   - Create domain base configs
   - Set up UI structure

4. **Migrate Domain by Domain**
   - Start with simplest domain
   - Test thoroughly before moving on
   - Document as you go

5. **Update Documentation**
   - Create domain guides
   - Update main README
   - Write migration notes

## Examples

See the following guides for complete examples:

- **Server Management**: `docs/SERVER_MANAGEMENT_EXAMPLE.md`
- **Gate Automation**: `docs/GATE_AUTOMATION_EXAMPLE.md`
- **Light Control**: `docs/LIGHT_CONTROL_EXAMPLE.md`
- **Irrigation**: `docs/IRRIGATION_EXAMPLE.md`

## Support and Resources

### Documentation Structure

```
docs/
├── AUTOMATION_ARCHITECTURE.md    # This file
├── MQTT_PROTOCOL.md              # MQTT specifications
├── [DOMAIN]_GUIDE.md             # Per-domain guides
├── [DOMAIN]_SETUP.md             # Setup instructions
└── [DOMAIN]_TROUBLESHOOTING.md   # Common issues

nodered/
├── flows/
│   ├── 000-base-config.json
│   ├── [domain]-[feature].json
│   └── README.md
├── templates/
│   ├── domain-template.json      # New domain template
│   └── feature-template.json     # New feature template
└── DEVELOPMENT_GUIDE.md
```

### Tools and Utilities

- **Flow Validator**: Check flow structure and naming
- **MQTT Monitor**: Debug topic traffic
- **Performance Profiler**: Identify bottlenecks
- **Backup Script**: Automated flow backups

---

**Version**: 3.0.0  
**Last Updated**: 2026-01-17  
**Maintainer**: System Administrator
