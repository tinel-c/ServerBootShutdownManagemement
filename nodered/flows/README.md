# Node-RED Modular Flows

This directory contains feature-based, modular Node-RED flows for the Server Boot/Shutdown Management system.

## Quick Start

### Import Order

**IMPORTANT**: Import flows in this specific order to ensure all dependencies are met:

1. `00-base-config.json` - **MUST BE IMPORTED FIRST**
2. `10-dell-controls.json`
3. `11-dell-status.json`
4. `12-dell-health.json`
5. `20-hp-controls.json`
6. `21-hp-status.json`
7. `22-hp-health.json`
8. `40-client-tracking.json`
9. `41-client-automation.json`
10. `42-client-shutdown.json`
11. `50-telegram-interface.json` - **Telegram Bot Interface** (optional)
12. `90-log-console.json`

**Energy (Victron):** after base config, import `800`, `811`, `812`, and re-import `50-telegram-interface.json` (replace existing nodes) for `/help`. See [docs/ENERGY_NODE_RED.md](../../docs/ENERGY_NODE_RED.md).

**Energy (Huawei):** after `800`, import `821`, `822`; re-import `50` and `90` (replace existing nodes). Requires `huawei-mqtt-publisher.service`. See [docs/ENERGY_NODE_RED.md](../../docs/ENERGY_NODE_RED.md).

**Grundfos SCALA1 *(planned)*:** after on-site BLE setup, import `412`, `413`; re-import `50` and `90` (replace existing nodes). Do **not** import until [docs/GRUNDGOS_SCALA1.md](../../docs/GRUNDGOS_SCALA1.md) checklist is done. Requires manual `install_grundfos_service.sh`.

**Tapo cameras:** after base config and `50-telegram-interface.json`, import `611-camera-management.json`, `612-camera-watchdog.json`, and `613-watchdog-status-dashboard.json`. Requires `tapo-monitor.service` and `CAMERA_N_*` in `.env`. Deploy: `deploy-flow-611.mjs`, `612`, `613`. See [docs/TAPO_CAMERA.md](../../docs/TAPO_CAMERA.md).

**Watchdog dashboard:** import `613-watchdog-status-dashboard.json` after flows `90` and `612`. Page `/dashboard/watchdog`.

### Import Instructions

1. Open Node-RED: http://localhost:1880
2. Click the menu (≡) in the top-right corner
3. Select **Import**
4. Click **select a file to import**
5. Navigate to this `flows/` directory
6. Select the first file (`00-base-config.json`)
7. Click **Import**
8. Repeat for each file in order
9. Click **Deploy** after all imports are complete

## File Descriptions

### 00-base-config.json
**Core Infrastructure** - Must be imported first

- UI Base configuration
- Dashboard page definition
- All UI groups (Dell, HP, Logs, Health)
- MQTT broker connection
- Main tab

**Dependencies**: None

---

### 10-dell-controls.json
**Dell T310 Control Buttons**

- Boot button (Wake-on-LAN)
- Graceful shutdown button (Proxmox)
- Force shutdown button (IPMI)
- MQTT output node

**Dependencies**: `ui_group_dell`, `mqtt_broker_local`

**MQTT Topics**:
- `dell/t310/command/boot`
- `dell/t310/command/shutdown`

---

### 11-dell-status.json
**Dell T310 Status Display**

- Status subscription (MQTT in)
- Metadata tracking (last report, state changes)
- Real-time status UI (Vue.js template)

**Dependencies**: `ui_group_dell`, `mqtt_broker_local`

**MQTT Topics**:
- Subscribes: `dell/t310/status`

---

### 12-dell-health.json
**Dell T310 Comprehensive Health Monitoring**

- Health data subscription (MQTT in)
- Advanced health monitoring dashboard with full data visualization

**Features**:
- Server status header with overall health badge
- Individual check cards with status icons and color coding
- Statistics grid (pings, grace period, timeout, manual resume)
- Live countdown timers to next ping
- Timing information (last/next ping with formatted dates)
- Tags display with pill styling
- Optional fields (methods, subject, started status)
- Badge URL links
- Empty state handling

**Dependencies**: `ui_group_dell_health`, `mqtt_broker_local`

**MQTT Topics**:
- Subscribes: `dell/t310/health`

---

### 20-hp-controls.json
**HP DL360p Control Buttons**

- Boot button (iLO)
- Graceful shutdown button (Proxmox)
- Force shutdown button (iLO)
- MQTT output node

**Dependencies**: `ui_group_hp`, `mqtt_broker_local`

**MQTT Topics**:
- `hp/dl360p/command/boot`
- `hp/dl360p/command/shutdown`

---

### 21-hp-status.json
**HP DL360p Status Display**

- Status subscription (MQTT in)
- Metadata tracking (last report, state changes)
- Real-time status UI (Vue.js template)

**Dependencies**: `ui_group_hp`, `mqtt_broker_local`

**MQTT Topics**:
- Subscribes: `hp/dl360p/status`

---

### 22-hp-health.json
**HP DL360p Comprehensive Health Monitoring**

- Health data subscription (MQTT in)
- Advanced health monitoring dashboard with full data visualization

**Features**: Same as Dell health (12-dell-health.json)
- Complete health check cards with all metrics
- Real-time countdown timers
- Status badges and color coding
- Modern gradient UI design

**Dependencies**: `ui_group_hp_health`, `mqtt_broker_local`

**MQTT Topics**:
- Subscribes: `hp/dl360p/health`

---

### 40-client-tracking.json
**Client PC Presence Tracking**

- Client presence monitoring (MQTT in)
- Client heartbeat handling
- Client list management
- State change detection (first online / last offline)
- Live client display with Vue.js

**Features**:
- Real-time client count
- Client hostname and IP tracking
- Last seen timestamps
- Automatic stale client cleanup (150s grace)
- Visual client cards with status indicators
- **Activity logging** for first client online / last client offline triggers

**Dependencies**: `ui_group_clients`, `mqtt_broker_local`

**MQTT Topics**:
- Subscribes: `clients/+/presence`
- Subscribes: `clients/+/heartbeat`

**Link Outputs**:
- `link_out_first_client` - Triggers when first client comes online
- `link_out_last_client` - Triggers when last client goes offline

---

### 41-client-automation.json
**Smart Server Automation** ⭐ **NEW v2.3.0**

- Client-aware server boot (smart wake-up)
- Automatic idle shutdown with grace period
- Watchdog recovery system
- 5-minute command cooldown protection
- Comprehensive activity logging
- Modern automation dashboard

**Features**:
- **Smart Boot**: Automatically boots server when clients need it
- **Grace Period**: 5-minute countdown before idle shutdown
- **Cooldown System**: Prevents command spam during boot/shutdown (5 min)
- **Activity Log**: Complete audit trail with timestamps and triggers
- **Visual Feedback**: Live countdown timers and status indicators
- **Cancellation**: Auto-cancels shutdown if client connects

**Dependencies**: `ui_group_clients`, `mqtt_broker_local`

**MQTT Topics**:
- Subscribes: `dell/t310/health` (for health sync)
- Publishes: `dell/t310/command/boot`
- Publishes: `dell/t310/command/shutdown`

**Link Inputs**:
- `link_in_first_client` - Receives first client online trigger
- `link_in_last_client` - Receives last client offline trigger

**Documentation**: See `../SMART_WAKEUP_GUIDE.md` for complete usage guide

---

### 42-client-shutdown.json
**Client PC Shutdown Control** ⭐ **NEW v2.4.0**

- Individual client shutdown controls (graceful/force)
- Bulk shutdown operations (all clients)
- Shutdown response tracking
- Activity logging with status updates
- Modern control panel UI

**Features**:
- **Individual Control**: Shutdown specific clients with confirmation
- **Bulk Operations**: Shutdown all clients at once
- **Graceful Shutdown**: Saves open applications before shutdown
- **Force Shutdown**: Immediate shutdown without save
- **Response Tracking**: Real-time status updates from clients
- **Activity Log**: Recent shutdown history with timestamps

**Dependencies**: `ui_group_client_shutdown`, `mqtt_broker_local`

**MQTT Topics**:
- Publishes: `clients/{client_id}/command/shutdown`
- Subscribes: `clients/+/response`

---

### 50-telegram-interface.json
**Telegram Bot Interface** ⭐ **NEW**

- Telegram bot command interface using `node-red-contrib-telegrambot`
- Server control via Telegram commands
- Real-time status notifications
- Command response notifications
- User authorization support

**Features**:
- **Commands**: `/boot`, `/shutdown`, `/force`, `/status`, `/help`
- **Server Control**: Control Dell T310 and HP DL360p via Telegram
- **Status Notifications**: Automatic notifications on server state changes
- **Command Responses**: Real-time feedback on command execution
- **Authorization**: Restrict access to authorized Telegram user IDs
- **Polling & Webhook**: Supports both polling (default) and webhook modes

**Dependencies**: 
- `mqtt_broker_local`
- `node-red-contrib-telegrambot` (install via npm in Node-RED)

**MQTT Topics**:
- Publishes: `dell/t310/command/boot`, `dell/t310/command/shutdown`
- Publishes: `hp/dl360p/command/boot`, `hp/dl360p/command/shutdown`
- Subscribes: `dell/t310/status`, `hp/dl360p/status`
- Subscribes: `+/+/response` (command responses)

**Configuration**:
1. Create a Telegram bot via [@BotFather](https://t.me/botfather)
2. Get your bot token
3. After importing, configure the `telegrambot-config` node:
   - Enter bot token in the config node
   - (Optional) Set `TELEGRAM_ALLOWED_USERS` environment variable for authorization
   - Choose polling (default) or webhook mode

**Setup Instructions**:
1. Install the telegrambot library in Node-RED (Palette Manager or npm)
2. Import the flow
3. Configure the `telegrambot-config` node with your bot token
4. Deploy the flow
5. Start chatting with your bot!

**Commands**:
- `/boot [dell|hp]` - Boot a server (default: dell)
- `/shutdown [dell|hp]` - Graceful shutdown (default: dell)
- `/force [dell|hp]` - Force shutdown (default: dell)
- `/status` - Get current server status
- `/help` - Show help message

**Documentation**: See `../TELEGRAM_SETUP.md` for complete setup guide

---

### 510-sms-gateway-controls.json
**SMS Gateway Control Dashboard**

- Dashboard UI for sending SMS messages (phone number + message input)
- Real-time gateway status display (WiFi, MQTT, GSM state)
- Send response tracking with success/error notifications
- Configuration UI for:
  - **Allowed phones (SMS commands)**: Comma-separated list of numbers authorized to send SMS commands

**MQTT Topics**:
- Publish: `sms/gateway/command/send` (to send SMS)
- Subscribe: `sms/gateway/status`, `sms/gateway/send/response`

**Default Config** (set at flow init):
- Allowed phones: `+40740244845`, `+40745218721`

---

### 511-sms-gateway-status.json
**SMS Gateway Status & Message Logging**

- Subscribes to `sms/gateway/receive/from`, `sms/gateway/receive/text`, `sms/gateway/receive/timestamp` to capture incoming SMS.
- Combines all three into a complete message object and logs to flow context (`sms_message_log`, max 100).
- Displays in Dashboard with modern UI, timestamps, and "NEW" badges.
- Publishes to `sms/command/received` so flow 514 can process SMS commands.
- **SMS Forwarding**: Automatically forwards ALL received SMS to the hardcoded emergency phone number `+40740244845`. Format: "SMS from +40xxx: [message text]".

---

### 512-sms-gateway-telegram.json
**SMS Gateway Telegram Integration**

- Telegram commands to interact with the SMS gateway:
  - `/sms <phone> <message>` – Send SMS via Telegram
  - `/sms_status` – Get gateway status
  - `/sms_log` – View recent received SMS

---

### 513-sms-gateway-watchdog.json
**SMS Gateway Watchdog & Alerts**

- Monitors SMS gateway connectivity
- Sends Telegram alerts when gateway goes offline/online
- Heartbeat monitoring

---

### 514-sms-gateway-interface.json
**SMS Gateway Command Interface** (mirrors ALL Telegram commands)

- Subscribes to `sms/command/received` (published by flow 511 when new SMS arrives).
- Parses SMS text as a command (with or without `/`) and replies via SMS to the sender.
- **3-second delay** before reply, then **rate limit 1 per 5s** for multi-SMS (e.g. HELP sends 8 messages with descriptions).
- **HELP / COMMANDS / LIST / START**: Sends **8 SMS chunks** with full command descriptions (same as Telegram).
- **Full Telegram parity**: All commands available on Telegram work via SMS, including CAMERA_STATUS and CAMERA_HELP.

**Commands (send via SMS to the gateway SIM):**

*Server Management:*
- `BOOT [dell|hp]` – Boot server (WoL/iLO)
- `SHUTDOWN [dell|hp]` – Graceful shutdown
- `FORCE [dell|hp]` – Force shutdown
- `STATUS` – Get server status

*Main Gate:*
- `GATE_OPEN` or `GATE` – Open main gate
- `GATE_STATUS` – Get main gate status

*Sliding Gate:*
- `SLIDING_OPEN` – Open sliding gate
- `SLIDING_CLOSE` – Close sliding gate
- `SLIDING_TRIGGER` – Trigger automation
- `SLIDING_STATUS` – Get status

*Secondary Gate:*
- `SECONDARY_OPEN` – Open gate
- `SECONDARY_CLOSE` – Close gate
- `SECONDARY_TRIGGER` – Trigger automation
- `SECONDARY_STOP` – Stop gate
- `SECONDARY_LIGHT_LEFT` – Left light (120s)
- `SECONDARY_LIGHT_RIGHT` – Right light (120s)
- `SECONDARY_STATUS` – Get status

*Garden Power:*
- `GARDEN_ON` – Turn on garden power
- `GARDEN_OFF` – Turn off garden power
- `GARDEN_TOGGLE` – Toggle power
- `GARDEN_STATUS` – Get power status & metrics

*Garden Lights:*
- `LIGHTS_ON` – Turn all 16 lights ON
- `LIGHTS_OFF` – Turn all 16 lights OFF
- `LIGHTS_STATUS` – Get lights summary

*Water Pump:*
- `PUMP_START` – Start water pump
- `PUMP_STOP` – Stop water pump
- `PUMP_DRAIN` – Drain water (10s pulse)
- `PUMP_TRENCH1_ON/OFF` – Feed trench 1
- `PUMP_TRENCH2_ON/OFF` – Feed trench 2
- `PUMP_STATUS` – Get pump status

*Aquarium:*
- `AQUARIUM_ON` – Light ON
- `AQUARIUM_OFF` – Light OFF
- `AQUARIUM_TOGGLE` – Toggle light
- `AQUARIUM_STATUS` – Get status

*Camera (Tapo ONVIF):*
- `CAMERA_STATUS` – Camera health and last detection event
- `CAMERA_HELP` – Camera system help

*SMS Gateway:*
- `SMS_STATUS` – Gateway WiFi/MQTT/GSM status
- `SMS_LOG` – Last 3 received SMS

*Help:*
- `HELP` or `COMMANDS` or `LIST` or `START` – Full command list (8 SMS with descriptions)

**Configuration (Dashboard → SMS Gateway tab):**
- **Allowed phones (SMS commands)**: Comma-separated numbers (e.g. `+40123456789, +40987654321`). Only these can send commands. Leave empty to allow all. Default: `+40740244845, +40745218721`.

**SMS Forwarding**: All received SMS are automatically forwarded to the hardcoded emergency number `+40740244845` (see flow 511).

**Dependencies**: Flow 511 (publishes to `sms/command/received`), `mqtt_broker_local`, flow/global context for device states.

**Import**: After 511-sms-gateway-status.json so the topic is available.

---

### 611-camera-management.json
**Tapo Camera Dashboard & Notifications**

- Subscribes to `garden/camera/+/event` and `garden/camera/+/health`
- Dashboard page `/dashboard/cameras` — status cards + rolling event log
- Telegram `/camera_status`, `/camera_help` (via link from flow 50)
- SMS parity via flow 514 (`CAMERA_STATUS`, `CAMERA_HELP`)

**Dependencies**: `mqtt_broker_local`, `ui_base`, `tapo-monitor.service`, `CAMERA_N_*` in server `.env`

**MQTT Topics**:
- Subscribes: `garden/camera/+/event`, `garden/camera/+/health`

**Setup**: [docs/TAPO_CAMERA.md](../../docs/TAPO_CAMERA.md)

**Import**: After `00-base-config.json` and `50-telegram-interface.json`. Re-import with **Replace existing nodes** if updating.

---

### 612-camera-watchdog.json
**Per-camera health watchdog (Telegram + SMS Gateway)**

- One watchdog per camera slug on `garden/camera/{slug}/health`
- **Timeout:** 2 minutes without `online` heartbeat (tapo-monitor republishes ~every 60 s)
- **Explicit offline:** immediate alert when monitor publishes `offline`
- Telegram alerts on transitions only (via flow 90 `watchdog_telegram_sender`)
- `tapo-monitor.service` enrolls each camera on SMS Gateway watchdog as `camera_{slug}` (60 s)

**Import**: After `90-device-watchdog.json` (shares `watchdog_telegram_sender`). Deploy: `node nodered/live-connection/scripts/deploy-flow-612.mjs`

---

### 613-watchdog-status-dashboard.json
**Unified watchdog status dashboard**

- Dashboard page `/dashboard/watchdog` — all monitored devices in one view
- **Node-RED watchdogs** (flow 90): gates, garden, energy, water, SMS gateway
- **Camera watchdogs** (flow 612): per-slug health with 2 min timeout
- **SMS Gateway hardware** enrollments from `sms/gateway/watchdog/status`
- Summary pills (online / offline / unknown) and cards grouped by category
- Refreshes every 30 s; heartbeats update live via MQTT

**Deploy:** `node nodered/live-connection/scripts/generate-flow-613.mjs` (after editing registry), then `node nodered/live-connection/scripts/deploy-flow-613.mjs`

---

### Energy / Victron (800–812)

**Files:** `800-energy-base-config.json`, `811-victron-energy-status.json`, `812-victron-energy-telegram.json`

Import order and MQTT transmission chain: [docs/ENERGY_NODE_RED.md](../../docs/ENERGY_NODE_RED.md).

| File | Purpose |
|------|---------|
| `800-energy-base-config.json` | Energy page (`battery-charging-100` icon), Victron + Huawei UI groups, global context init |
| `811-victron-energy-status.json` | Live dashboard: metrics, 7-day chart (hover tooltips), discretionary Start/Stop |
| `812-victron-energy-telegram.json` | Telegram: `/energy_status`, `/energy_start`, `/energy_stop`, `/energy_help` |

**Deploy (live server):** `node nodered/live-connection/scripts/deploy-flow-811-821.mjs`

**MQTT:** Subscribes `energy/victron/status` (QoS 1, JSON). Requires `victron-mqtt-publisher.service` on the automation server.

**Dashboard:** `/dashboard/energy` — battery SoC, grid import/export, load, PV, inverter state, 7-day history chart.

---

### Energy / Huawei (821–822)

**Files:** `821-huawei-energy-status.json`, `822-huawei-energy-telegram.json`

Requires `800-energy-base-config.json` (Huawei UI group). Full import order: [docs/ENERGY_NODE_RED.md](../../docs/ENERGY_NODE_RED.md).

| File | Purpose |
|------|---------|
| `821-huawei-energy-status.json` | Live dashboard: PV strings (S1 west, S2 east), 7-day chart, Open-Meteo PV forecast vs actual |
| `822-huawei-energy-telegram.json` | Telegram: `/huawei_status`, `/huawei_help` |

**Deploy (live server):** included in `deploy-flow-811-821.mjs`

**MQTT:** Subscribes `energy/huawei/status` and Victron forecast topics for PV model. Requires `huawei-mqtt-publisher.service` and `victron-solar-forecast-publisher.service`.

**Dashboard:** `/dashboard/energy` — Huawei Energy group on the same Energy page as Victron.

---

### Irrigation / Grundfos SCALA1 (412–413) — **planned**

> Not production-ready. See [docs/GRUNDGOS_SCALA1.md](../../docs/GRUNDGOS_SCALA1.md).

**Files:** `412-grundfos-scala1-status.json`, `413-grundfos-scala1-telegram.json`

Requires `400-irrigation-base-config.json` (adds `ui_group_grundfos_scala1`). See [device/grundfos-scala1/README.md](../../device/grundfos-scala1/README.md).

| File | Purpose |
|------|---------|
| `412-grundfos-scala1-status.json` | Live dashboard: pressure, flow, power, alarms; optional start/stop buttons |
| `413-grundfos-scala1-telegram.json` | Telegram: `/scala1_status`, `/scala1_start`, `/scala1_stop`, `/scala1_help` |

**MQTT:** Subscribes `water/grundfos/scala1/status` (QoS 1, JSON). Requires `grundfos-scala1-mqtt-publisher.service` and BLE GATT configuration.

**Dashboard:** `/dashboard/irrigation` — Grundfos SCALA1 group (separate from Tasmota `pompaApa` in flow 410).

---

### Gate automation (200–212)

**Files:** `200-gate-base-config.json`, `210-main-gate-controls.json`, `211-main-gate-status.json`, `212-gate-telegram.json` (optional). Import order and layout: see [docs/GATE_IMPORT_INSTRUCTIONS.md](../../docs/GATE_IMPORT_INSTRUCTIONS.md).

**Main gate device:** [PlatformIO_ESP8266_Main_Entry](https://github.com/tinel-c/PlatformIO_ESP8266_Main_Entry) (ESP8266). Main gate open uses **`MainGate/CMD/Relay3`** (Relay 3 is the gate actuator; status on `MainGate/STAT/Relay3` and `MainGate/STAT/reccurentStatusRelay3`).

---

### 90-log-console.json
**System Log Console**

- System logs subscription
- Command responses subscription (wildcard)
- Log accumulator (50-entry buffer)
- Terminal-style rolling log display

**Dependencies**: `ui_group_logs`, `mqtt_broker_local`

**MQTT Topics**:
- Subscribes: `system/logs`
- Subscribes: `+/+/response` (wildcard)

---

## Customization

### Modifying a Feature

1. Make changes in Node-RED editor
2. Select all nodes for that feature
3. Menu → Export → Clipboard
4. Save to the appropriate file, overwriting the old version
5. Commit to version control

### Adding a New Server

See `NODE_RED_DEVELOPMENT.md` for detailed instructions on adding support for additional servers.

Basic steps:
1. Add UI groups to `00-base-config.json`
2. Create `30-newserver-controls.json` (copy from Dell or HP)
3. Create `31-newserver-status.json`
4. Create `32-newserver-health.json`
5. Update backend to publish to correct MQTT topics

## MQTT Topic Patterns

### Commands (Dashboard → Backend)
```
{server}/{model}/command/boot
{server}/{model}/command/shutdown
```

### Status (Backend → Dashboard)
```
{server}/{model}/status
{server}/{model}/health
system/logs
```

### Expected Payloads

**Boot Command**:
```json
{
  "action": "boot",
  "method": "wol|ipmi|ilo"
}
```

**Shutdown Command**:
```json
{
  "action": "shutdown",
  "type": "graceful|force"
}
```

**Status Update**:
```json
{
  "server_state": "online|offline|unknown",
  "timestamp": "2025-12-29T12:34:56Z"
}
```

**Health Update**:
```json
{
  "timestamp": "2025-12-29T12:34:56Z",
  "server": "Dell T310",
  "checks": [
    {
      "unique_key": "check_id",
      "name": "Check Name",
      "slug": "check-name",
      "tags": "tag1,tag2",
      "desc": "Optional description",
      "status": "up|down|warning",
      "n_pings": 12345,
      "grace": 300,
      "timeout": 120,
      "last_ping": "2025-12-29T12:34:00+00:00",
      "next_ping": "2025-12-29T12:36:00+00:00",
      "manual_resume": false,
      "started": false,
      "methods": "http",
      "subject": "Alert subject",
      "badge_url": "https://healthchecks.io/badge/..."
    }
  ]
}
```

**Log Entry**:
```json
{
  "timestamp": "12:34:56",
  "level": "INFO|WARNING|ERROR|CRITICAL",
  "service": "service_name",
  "message": "Log message text"
}
```

## Troubleshooting

### "Node configuration error" on Import

**Problem**: Missing dependencies (broker or UI groups)

**Solution**: Import `00-base-config.json` first

---

### Status Widget Shows "UNKNOWN"

**Problem**: No MQTT messages received

**Solution**:
1. Verify MQTT broker is running
2. Check Python services are publishing
3. Use MQTT Explorer to monitor topics
4. Check Node-RED debug panel

---

### Buttons Don't Work

**Problem**: MQTT connection or topic mismatch

**Solution**:
1. Check `mqtt_broker_local` configuration
2. Verify topic names match backend
3. Add debug nodes to trace messages

---

### Import Causes Duplicate Nodes

**Problem**: Importing same file multiple times

**Solution**:
1. Delete all flows
2. Reimport in correct order
3. Or manually delete duplicate nodes

## File Naming Convention

- `00-09`: Core infrastructure
- `10-19`: Dell T310 features
- `20-29`: HP DL360p features
- `30-39`: Reserved for future server 1
- `40-49`: Client automation and tracking
- `50-59`: External interfaces (Telegram, etc.)
- `300-399`: Power monitoring (garden Sonoff, lights)
- `800-899`: Energy management (Victron Cerbo GX, Huawei SUN2000)
- `90-99`: Shared utilities

## Version Control

Each `.json` file should be tracked in Git independently. This allows:
- Feature-specific commits
- Easy rollback of individual features
- Collaborative development
- Clear change history

## Testing

After importing flows:

1. **Visual Check**: Verify all UI elements appear in dashboard
2. **Status Test**: Confirm status updates display correctly
3. **Button Test**: Click each button, verify MQTT publish
4. **Health Test**: Confirm health checks display
5. **Logs Test**: Verify log console receives messages

## Support

For detailed development guidance, see:
- `../NODE_RED_DEVELOPMENT.md` - Comprehensive development guide
- `../../docs/MQTT_PROTOCOL.md` - MQTT protocol specification
- `../../docs/TROUBLESHOOTING.md` - System troubleshooting

---

**Last Updated**: July 4, 2026  
**Format Version**: 3.13.0 (Energy charts + PV forecast, Tapo flows 611–613)

