# Architecture Diagram Description for Image Generation

## System Overview
A comprehensive server management system with smart client-aware automation, featuring Dell T310 and HP DL360p servers controlled via MQTT through a centralized Node-RED dashboard.

## Visual Layout (Top to Bottom)

### Layer 1: User & Client Layer
```
┌──────────────────────────────────────────────────────────────┐
│                    USER & CLIENT LAYER                        │
├────────────────────┬─────────────────────────────────────────┤
│   🖥️ Web Browser   │   💻 Client PCs (Windows)               │
│   Dashboard UI     │   - Client Monitor App                  │
│   localhost:1880   │   - Auto-start on login                 │
│                    │   - System tray icon                    │
└────────────────────┴─────────────────────────────────────────┘
           │                           │
           │ HTTP                      │ MQTT
           ▼                           ▼
```

### Layer 2: Automation Server (Central Hub)
```
┌──────────────────────────────────────────────────────────────┐
│           🐳 AUTOMATION SERVER (Ubuntu VM)                    │
├──────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐  ┌──────────────────────────────┐  │
│  │  Node-RED Dashboard │  │   Mosquitto MQTT Broker      │  │
│  │  :1880 (Native)     │  │   :1883                      │  │
│  │                     │  │                              │  │
│  │  • Server Controls  │  │   📡 Central Message Bus     │  │
│  │  • Status Display   │  │                              │  │
│  │  • Health Monitor   │◄─┤   Topics:                    │  │
│  │  • Client Tracking  │  │   - dell/t310/*              │  │
│  │  • Smart Automation │  │   - hp/dl360p/*              │  │
│  │  • Activity Logs    │  │   - clients/+/*              │  │
│  └─────────────────────┘  └──────────────────────────────┘  │
│                                      ▲                        │
│  ┌────────────────────────────────────────────────────────┐  │
│  │         🐍 Python Systemd Services                     │  │
│  ├────────────────────────────────────────────────────────┤  │
│  │  • mqtt-boot-listener      • status-publisher         │  │
│  │  • mqtt-shutdown-listener  • health-monitor           │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
           │                                    │
           │ Network                            │
           ▼                                    ▼
```

### Layer 3: Managed Servers
```
┌────────────────────────────┐  ┌────────────────────────────┐
│   🖥️ Dell T310 Server      │  │   🖥️ HP DL360p Server      │
├────────────────────────────┤  ├────────────────────────────┤
│  Management:               │  │  Management:               │
│  • IPMI Interface          │  │  • iLO Interface           │
│  • Wake-on-LAN (MAC)       │  │  • Remote Power Control    │
│                            │  │                            │
│  Software:                 │  │  Software:                 │
│  • Proxmox VE Hypervisor   │  │  • Proxmox VE Hypervisor   │
│  • API :8006               │  │  • API :8006               │
│  • Virtual Machines        │  │  • Virtual Machines        │
│                            │  │                            │
│  Status: UP/DOWN/UNKNOWN   │  │  Status: UP/DOWN/UNKNOWN   │
└────────────────────────────┘  └────────────────────────────┘
```

## Key Features Highlighted

### Smart Automation (v2.3.0)
```
┌─────────────────────────────────────────────────────────┐
│              🤖 SMART AUTOMATION ENGINE                  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Client-Aware Boot:                                     │
│  • Detects clients needing server                       │
│  • Automatically boots server via WOL                   │
│  • 5-minute command cooldown                            │
│                                                          │
│  Idle Shutdown:                                         │
│  • Monitors server + client state                       │
│  • 5-minute grace period countdown                      │
│  • Executes graceful shutdown                           │
│                                                          │
│  Activity Logging:                                      │
│  • Client triggers (🟢 online, 🔴 offline)              │
│  • Commands (🚀 boot, ⏹️ shutdown)                       │
│  • Status changes (⏱️ grace, ❌ cancel)                  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Communication Flow Example

### Morning Boot Sequence:
```
Client PC Starts
    │
    ├─→ MQTT: clients/pc-001/presence (online)
    │
    ▼
Node-RED Detects
    │
    ├─→ Log: 🟢 Trigger [client_online] DETECTED
    │
    ├─→ Check: Server status = DOWN
    │
    ├─→ Send: MQTT dell/t310/command/boot
    │
    ▼
Python Service
    │
    ├─→ Execute: Wake-on-LAN
    │
    ├─→ Cooldown: 5 minutes
    │
    ▼
Server Boots
    │
    ├─→ MQTT: dell/t310/status (ONLINE)
    │
    ▼
Dashboard Updates
    └─→ Status: UP ✅
```

### Evening Shutdown Sequence:
```
Client PC Shuts Down
    │
    ├─→ MQTT: clients/pc-001/presence (offline)
    │
    ▼
Node-RED Detects
    │
    ├─→ Log: 🔴 Trigger [client_offline] DETECTED
    │
    ├─→ Check: Last client? YES
    │
    ├─→ Start: Grace period (5:00 countdown)
    │
    ▼
5 Minutes Pass
    │
    ├─→ Check: Still no clients? YES
    │
    ├─→ Send: MQTT dell/t310/command/shutdown
    │
    ▼
Python Service
    │
    ├─→ Execute: Graceful shutdown (VMs → Host)
    │
    ▼
Server Powers Off
    │
    ├─→ MQTT: dell/t310/status (OFFLINE)
    │
    ▼
Dashboard Updates
    └─→ Status: DOWN ⏹️
```

## Color Scheme Recommendations

### Primary Colors:
- **Background**: Dark blue gradient (#0f172a → #1e293b)
- **Automation Server**: Blue/Purple (#3b82f6)
- **Dell Server**: Green (#10b981)
- **HP Server**: Orange (#f59e0b)
- **Client PCs**: Light blue (#60a5fa)
- **MQTT Broker**: Yellow/Gold (#fbbf24)

### Status Colors:
- **Online/Up**: Green (#10b981)
- **Offline/Down**: Red (#ef4444)
- **Unknown/Warning**: Gray (#64748b)
- **Grace Period**: Yellow (#f59e0b)
- **Trigger Events**: Purple (#8b5cf6)

## Key Components to Emphasize

1. **Central MQTT Broker** - Heart of the system
2. **Node-RED Dashboard** - User interface and automation logic
3. **Python Services** - Command execution layer
4. **Client Monitoring** - NEW feature (v2.3.0)
5. **Smart Automation** - NEW feature (v2.3.0)
6. **Activity Logging** - Complete audit trail

## Technical Details to Include

- **Protocols**: HTTP, MQTT, Wake-on-LAN, IPMI, iLO, Proxmox API
- **Ports**: 1880 (Node-RED), 1883 (MQTT), 8006 (Proxmox), 623 (IPMI)
- **Technologies**: Python 3.8+, Node-RED, Mosquitto, Systemd
- **Platform**: Ubuntu VM (automation), Windows (clients), Proxmox VE (servers)

---

**Use this description to generate a modern, professional system architecture diagram with clear visual hierarchy, color-coded components, and emphasis on the smart automation features.**

