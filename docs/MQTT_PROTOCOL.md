# MQTT Protocol Specification

This document defines the MQTT message format and protocol for the Dell T310 Management System.

## Overview

The system uses MQTT for remote commands, status updates, and telemetry. Most command/response payloads are **JSON**. Victron per-metric topics under `energy/victron/` use **plain-text scalars**; only `energy/victron/status` is JSON.

## Topics

### Command Topics (Client → Server)

| Topic | Purpose | QoS |
|-------|---------|-----|
| `dell/t310/command/boot` | Boot server | 1 |
| `dell/t310/command/shutdown` | Shutdown server | 1 |
| `dell/t310/command/status` | Request immediate status | 1 |

### Status Topics (Server → Client)

| Topic | Purpose | QoS |
|-------|---------|-----|
| `dell/t310/status` | Server status updates | 1 |
| `dell/t310/response` | Command responses | 1 |
| `dell/t310/logs` | Log messages | 0 |

### Client PC Topics (Client ↔ Server)

| Topic | Purpose | QoS | Direction |
|-------|---------|-----|-----------|
| `clients/{client_id}/presence` | Client startup/shutdown notifications | 1 | Client → Server |
| `clients/{client_id}/heartbeat` | Client heartbeat messages | 1 | Client → Server |
| `clients/{client_id}/command/shutdown` | Client shutdown commands | 1 | Server → Client |
| `clients/{client_id}/response` | Client command responses | 1 | Client → Server |
| `automation/clients/status` | Automation status updates | 1 | Server → Server |

### SMS Gateway Topics (Domain: 500-599)

| Topic | Purpose | QoS | Direction |
|-------|---------|-----|-----------|
| `sms/gateway/command/send` | Send SMS command | 1 | Dashboard → Device |
| `sms/gateway/status` | Device status timestamp | 1 | Device → Dashboard |
| `sms/gateway/status/timestamp` | Last status update | 1 | Device → Dashboard |
| `sms/gateway/receive/from` | Phone number of received SMS | 1 | Device → Dashboard |
| `sms/gateway/receive/text` | Text content of received SMS | 1 | Device → Dashboard |
| `sms/gateway/receive/timestamp` | Timestamp when SMS was received | 1 | Device → Dashboard |
| `sms/gateway/send/response` | Send operation result | 1 | Device → Dashboard |
| `sms/gateway/send/timestamp` | Timestamp when SMS was sent | 1 | Device → Dashboard |
| `sms/gateway/command/ota` | OTA enable/disable command | 1 | Dashboard → Device |
| `sms/gateway/ota/status` | OTA update status | 1 | Device → Dashboard |
| `sms/gateway/ota/progress` | OTA update progress | 1 | Device → Dashboard |
| `sms/command/received` | Internal: new SMS for command processing | 1 | Node-RED 511 → 514 |

### Victron Energy Topics (Domain: energy/victron)

Published by **`victron-mqtt-publisher.service`** on the automation server (`scripts/victron_mqtt_publisher.py`). The service polls the Cerbo GX via **Modbus TCP** every **10 seconds** (configurable) and publishes to the central MQTT broker.

| Setting | Default | Config |
|---------|---------|--------|
| Topic prefix | `energy/victron` | `VICTRON_MQTT_PREFIX` in [device/victron-multiplus-ii/config/.env](../device/victron-multiplus-ii/config/.env) |
| Poll interval | `10` s | `VICTRON_MODBUS_POLL_INTERVAL` |
| QoS | `1` | `VICTRON_MQTT_QOS` |
| Broker | root `config/.env` | `MQTT_BROKER_HOST`, `MQTT_BROKER_PORT`, credentials |

**Direction:** Server → subscribers (Node-RED, dashboards, automations). Messages are **not retained**.

#### Per-metric topics (always published)

| Topic | Payload type | Unit | Description |
|-------|--------------|------|-------------|
| `energy/victron/battery/voltage` | number | V | Battery voltage (system register 840) |
| `energy/victron/battery/soc` | integer | % | State of charge (register 843) |
| `energy/victron/battery/power` | signed integer | W | Battery power; positive = charging (register 842) |
| `energy/victron/grid/power_l1` | signed integer | W | Grid L1 power; positive = import, negative = export (register 820) |
| `energy/victron/pv/dc_power` | integer | W | PV DC power (register 850) |
| `energy/victron/pv/dc_current` | number | A | PV DC current (register 851) |
| `energy/victron/pv/ac_output_l1` | integer | W | AC-coupled PV on inverter output L1 (register 808) |
| `energy/victron/pv/ac_grid_l1` | integer | W | AC-coupled PV on grid L1 (register 811) |
| `energy/victron/load/consumption_l1` | integer | W | AC consumption L1 (register 817) |
| `energy/victron/load/output_l1` | signed integer | W | VE.Bus AC output L1 power (register 878) |
| `energy/victron/load/input_l1` | signed integer | W | VE.Bus AC input L1 power (register 872) |
| `energy/victron/inverter/ac_in_voltage_l1` | number | V | AC input voltage L1 (VE.Bus register 3) |
| `energy/victron/inverter/ac_in_power_l1` | signed integer | W | AC input power L1 (VE.Bus register 12) |
| `energy/victron/inverter/ac_out_power_l1` | signed integer | W | AC output power L1 (VE.Bus register 23) |
| `energy/victron/inverter/dc_voltage` | number | V | DC voltage (VE.Bus register 26) |
| `energy/victron/inverter/state` | string | — | Human-readable inverter state (e.g. `Passthru`, `Inverting`) |
| `energy/victron/inverter/state_code` | integer | — | Raw VE.Bus state code (register 31) |
| `energy/victron/inverter/grid_lost` | boolean | — | `True` when grid lost alarm active (register 64 = 2) |

Per-metric payloads are **plain text** (not JSON): numbers as decimal strings, booleans as `True`/`False`.

#### Aggregate snapshot

| Topic | Purpose | QoS |
|-------|---------|-----|
| `energy/victron/status` | Full JSON snapshot of all metrics below | 1 |

#### Optional topics (when hardware is detected or configured)

Published only when an MPPT solar charger is found on Modbus (auto-scan or `VICTRON_SOLARCHARGER_UNIT_ID`):

| Topic | Payload type | Unit | Description |
|-------|--------------|------|-------------|
| `energy/victron/solar/pv_voltage` | number | V | MPPT PV voltage |
| `energy/victron/solar/charge_current` | number | A | Charge current |
| `energy/victron/solar/pv_power` | number | W | PV power |
| `energy/victron/solar/yield_today` | number | kWh | Yield today |
| `energy/victron/solar/state` | string | — | Charger state (e.g. `Bulk`, `Float`) |

Published only when `VICTRON_PVINVERTER_UNIT_ID` is set in device config:

| Topic | Payload type | Unit | Description |
|-------|--------------|------|-------------|
| `energy/victron/pvinverter/ac_power_l1` | integer | W | Grid-tie PV AC power L1 |
| `energy/victron/pvinverter/ac_voltage_l1` | number | V | AC voltage L1 |
| `energy/victron/pvinverter/ac_current_l1` | number | A | AC current L1 |
| `energy/victron/pvinverter/position` | string | — | Meter position (`AC input 1`, `AC output`, `AC input 2`) |

See [device/victron-multiplus-ii/README.md](../device/victron-multiplus-ii/README.md) for Cerbo GX setup, Modbus Unit IDs, and deployment.

---

## Message Schemas

### Boot Command

**Topic:** `dell/t310/command/boot`

**Schema:**
```json
{
  "action": "boot",
  "method": "wol|ipmi",
  "timestamp": "ISO8601 timestamp",
  "request_id": "unique identifier"
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `action` | string | Yes | Must be "boot" |
| `method` | string | Yes | Boot method: "wol" or "ipmi" |
| `timestamp` | string | Yes | ISO8601 timestamp |
| `request_id` | string | Yes | Unique request identifier |

**Example:**
```json
{
  "action": "boot",
  "method": "wol",
  "timestamp": "2025-12-25T20:00:00+02:00",
  "request_id": "boot-20251225-001"
}
```

---

### Shutdown Command

**Topic:** `dell/t310/command/shutdown`

**Schema:**
```json
{
  "action": "shutdown",
  "type": "graceful|force",
  "timeout": 300,
  "timestamp": "ISO8601 timestamp",
  "request_id": "unique identifier"
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `action` | string | Yes | Must be "shutdown" |
| `type` | string | Yes | Shutdown type: "graceful" or "force" |
| `timeout` | integer | No | Timeout in seconds (default: 300) |
| `timestamp` | string | Yes | ISO8601 timestamp |
| `request_id` | string | Yes | Unique request identifier |

**Example:**
```json
{
  "action": "shutdown",
  "type": "graceful",
  "timeout": 300,
  "timestamp": "2025-12-25T20:00:00+02:00",
  "request_id": "shutdown-20251225-001"
}
```

---

### Status Request

**Topic:** `dell/t310/command/status`

**Schema:**
```json
{
  "action": "status",
  "timestamp": "ISO8601 timestamp",
  "request_id": "unique identifier"
}
```

**Example:**
```json
{
  "action": "status",
  "timestamp": "2025-12-25T20:00:00+02:00",
  "request_id": "status-20251225-001"
}
```

---

### Status Update

**Topic:** `dell/t310/status`

**Schema:**
```json
{
  "timestamp": "ISO8601 timestamp",
  "server_name": "string",
  "server_state": "online|offline|booting|shutting_down|error",
  "power_status": "on|off",
  "uptime": 3600,
  "uptime_formatted": "1h 0m",
  "cpu_usage": 45.2,
  "memory_usage": 62.8,
  "memory_total_gb": 16.0,
  "memory_used_gb": 10.0,
  "disk_usage": 75.5,
  "disk_total_gb": 500.0,
  "disk_used_gb": 377.5,
  "temperature": 45
}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | string | ISO8601 timestamp of status |
| `server_name` | string | Server name |
| `server_state` | string | Current state: online, offline, booting, shutting_down, error |
| `power_status` | string | Power status: on or off |
| `uptime` | integer | Uptime in seconds (null if offline) |
| `uptime_formatted` | string | Human-readable uptime |
| `cpu_usage` | float | CPU usage percentage (null if offline) |
| `memory_usage` | float | Memory usage percentage (null if offline) |
| `memory_total_gb` | float | Total memory in GB |
| `memory_used_gb` | float | Used memory in GB |
| `disk_usage` | float | Disk usage percentage (null if offline) |
| `disk_total_gb` | float | Total disk space in GB |
| `disk_used_gb` | float | Used disk space in GB |
| `temperature` | integer | System temperature in Celsius (null if unavailable) |

**Example:**
```json
{
  "timestamp": "2025-12-25T20:00:00+02:00",
  "server_name": "Dell T310",
  "server_state": "online",
  "power_status": "on",
  "uptime": 86400,
  "uptime_formatted": "1d 0h 0m",
  "cpu_usage": 25.5,
  "memory_usage": 45.2,
  "memory_total_gb": 16.0,
  "memory_used_gb": 7.2,
  "disk_usage": 60.5,
  "disk_total_gb": 500.0,
  "disk_used_gb": 302.5,
  "temperature": 42
}
```

---

### Command Response

**Topic:** `dell/t310/response`

**Schema:**
```json
{
  "request_id": "string",
  "action": "boot|shutdown|status",
  "success": true,
  "message": "string",
  "timestamp": "ISO8601 timestamp"
}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `request_id` | string | Original request ID |
| `action` | string | Action that was performed |
| `success` | boolean | Whether action succeeded |
| `message` | string | Human-readable message |
| `timestamp` | string | ISO8601 timestamp of response |

**Example (Success):**
```json
{
  "request_id": "boot-20251225-001",
  "action": "boot",
  "success": true,
  "message": "Server boot initiated successfully via WOL",
  "timestamp": "2025-12-25T20:00:05+02:00"
}
```

**Example (Failure):**
```json
{
  "request_id": "shutdown-20251225-001",
  "action": "shutdown",
  "success": false,
  "message": "Failed to shutdown server via IPMI: Connection timeout",
  "timestamp": "2025-12-25T20:00:05+02:00"
}
```

---

### Client Presence Message

**Topic:** `clients/{client_id}/presence`

**Schema:**
```json
{
  "status": "online|offline",
  "hostname": "string",
  "client_id": "string",
  "timestamp": "ISO8601 timestamp",
  "ip_address": "string",
  "reason": "string (optional)"
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | string | Yes | Client status: "online" or "offline" |
| `hostname` | string | Yes | Windows hostname |
| `client_id` | string | Yes | Unique client identifier |
| `timestamp` | string | Yes | ISO8601 timestamp |
| `ip_address` | string | Yes | Client IP address |
| `reason` | string | No | Reason for offline (e.g., "connection_lost") |

**Example (Online):**
```json
{
  "status": "online",
  "hostname": "DESKTOP-ABC123",
  "client_id": "desktop-abc123",
  "timestamp": "2026-01-06T17:30:00+02:00",
  "ip_address": "192.168.1.50"
}
```

**Example (Offline):**
```json
{
  "status": "offline",
  "hostname": "DESKTOP-ABC123",
  "client_id": "desktop-abc123",
  "timestamp": "2026-01-06T18:30:00+02:00",
  "ip_address": "192.168.1.50"
}
```

---

### Client Heartbeat Message

**Topic:** `clients/{client_id}/heartbeat`

**Schema:**
```json
{
  "client_id": "string",
  "hostname": "string",
  "timestamp": "ISO8601 timestamp",
  "uptime": 3600
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `client_id` | string | Yes | Unique client identifier |
| `hostname` | string | Yes | Windows hostname |
| `timestamp` | string | Yes | ISO8601 timestamp |
| `uptime` | integer | Yes | System uptime in seconds |

**Example:**
```json
{
  "client_id": "desktop-abc123",
  "hostname": "DESKTOP-ABC123",
  "timestamp": "2026-01-06T17:31:00+02:00",
  "uptime": 3600
}
```

---

### Client Shutdown Command

**Topic:** `clients/{client_id}/command/shutdown`

**Schema:**
```json
{
  "action": "shutdown",
  "type": "graceful|force",
  "timestamp": "ISO8601 timestamp",
  "request_id": "unique identifier"
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `action` | string | Yes | Must be "shutdown" |
| `type` | string | Yes | Shutdown type: "graceful" or "force" |
| `timestamp` | string | Yes | ISO8601 timestamp |
| `request_id` | string | Yes | Unique request identifier |

**Example (Graceful):**
```json
{
  "action": "shutdown",
  "type": "graceful",
  "timestamp": "2026-01-09T15:30:00+02:00",
  "request_id": "shutdown-desktop-abc123-1736429400"
}
```

**Example (Force):**
```json
{
  "action": "shutdown",
  "type": "force",
  "timestamp": "2026-01-09T15:30:00+02:00",
  "request_id": "shutdown-desktop-abc123-1736429400"
}
```

**Behavior:**
- **Graceful**: Attempts to save all open applications before shutting down (30 second delay)
- **Force**: Immediate shutdown without saving (5 second delay)

---

### Client Shutdown Response

**Topic:** `clients/{client_id}/response`

**Schema:**
```json
{
  "request_id": "string",
  "action": "shutdown",
  "success": true,
  "message": "string",
  "timestamp": "ISO8601 timestamp",
  "client_id": "string",
  "hostname": "string"
}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `request_id` | string | Original request ID from shutdown command |
| `action` | string | Action performed ("shutdown") |
| `success` | boolean | Whether action succeeded |
| `message` | string | Human-readable status message |
| `timestamp` | string | ISO8601 timestamp of response |
| `client_id` | string | Client identifier |
| `hostname` | string | Windows hostname |

**Example (Acknowledged):**
```json
{
  "request_id": "shutdown-desktop-abc123-1736429400",
  "action": "shutdown",
  "success": true,
  "message": "Shutdown command acknowledged, will shutdown in 30 seconds",
  "timestamp": "2026-01-09T15:30:01+02:00",
  "client_id": "desktop-abc123",
  "hostname": "DESKTOP-ABC123"
}
```

---

## SMS Gateway Messages

### Send SMS Command

**Topic:** `sms/gateway/command/send`

**Schema:**
```json
{
  "to": "string",
  "text": "string"
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `to` | string | Yes | Phone number with country code (e.g., "+1234567890") |
| `text` | string | Yes | SMS message text (max 160 characters recommended) |

**Example:**
```json
{
  "to": "+1234567890",
  "text": "Server is online and running normally."
}
```

---

### SMS Send Response

**Topic:** `sms/gateway/send/response`

**Schema:**
```json
{
  "success": true,
  "to": "string",
  "timestamp": "ISO8601 timestamp"
}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether SMS was sent successfully |
| `to` | string | Phone number that received the SMS |
| `timestamp` | string | ISO8601 timestamp when SMS was sent |

**Example (Success):**
```json
{
  "success": true,
  "to": "+1234567890",
  "timestamp": "2026-01-25T17:00:00+00:00"
}
```

**Example (Failure):**
```json
{
  "success": false,
  "to": "+1234567890",
  "timestamp": "2026-01-25T17:00:00+00:00"
}
```

---

### SMS Receive Messages

**Topic:** `sms/gateway/receive/from` and `sms/gateway/receive/text`

**Schema (from topic):**
```
Phone number string (e.g., "+1234567890")
```

**Schema (text topic):**
```
SMS message text string
```

**Note:** These are published as separate topics. The timestamp is published to `sms/gateway/receive/timestamp`.

### SMS Command Received (Internal Node-RED)

**Topic:** `sms/command/received`

**Schema:** JSON string with `messages`, `messageCount`, `latest` fields. Flow 511 publishes; Flow 514 subscribes for command processing.

---

**Example Usage:**
```bash
# Monitor received SMS
mosquitto_sub -h localhost -t "sms/gateway/receive/+" -v
```

**Example Messages:**
- `sms/gateway/receive/from`: `"+1234567890"`
- `sms/gateway/receive/text`: `"Hello from phone!"`
- `sms/gateway/receive/timestamp`: `"2026-01-25T17:05:00+00:00"`

---

## Victron Energy Messages

Published by `victron-mqtt-publisher.service` every poll cycle (default **10 s**). Topic prefix defaults to `energy/victron`; override with `VICTRON_MQTT_PREFIX`.

### Status Snapshot

**Topic:** `energy/victron/status`

**Schema:**
```json
{
  "timestamp": "ISO8601 UTC timestamp",
  "source": "victron_modbus",
  "battery": {
    "voltage_v": 52.3,
    "soc_pct": 91,
    "power_w": -450
  },
  "grid": {
    "power_l1_w": 32
  },
  "pv": {
    "dc_power_w": 0,
    "dc_current_a": 0.0,
    "ac_output_l1_w": 3100,
    "ac_grid_l1_w": 0
  },
  "load": {
    "consumption_l1_w": 2163,
    "output_l1_w": 2200,
    "input_l1_w": 50
  },
  "inverter": {
    "ac_in_voltage_l1_v": 230.5,
    "ac_in_power_l1_w": 50,
    "ac_out_power_l1_w": 2150,
    "dc_voltage_v": 52.30,
    "state_code": 8,
    "state": "Passthru",
    "grid_lost": false
  },
  "solar_charger": null,
  "pv_inverter": null
}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | string | UTC ISO8601 time of the poll |
| `source` | string | Always `"victron_modbus"` |
| `battery` | object | Voltage (V), SoC (%), power (W) |
| `grid` | object | Grid L1 power (W); signed — import positive, export negative |
| `pv` | object | DC and AC-coupled PV metrics (W / A) |
| `load` | object | Consumption and VE.Bus input/output power (W) |
| `inverter` | object | AC/DC electrical values, state name/code, grid-lost flag |
| `solar_charger` | object \| null | MPPT data when a solar charger is found; omitted from per-metric topics when null |
| `pv_inverter` | object \| null | Grid-tie inverter data when `VICTRON_PVINVERTER_UNIT_ID` is configured |

**Inverter state codes** (register 31 → `inverter/state`):

| Code | State |
|------|-------|
| 0 | Off |
| 1 | Low Power |
| 2 | Fault |
| 3 | Bulk |
| 4 | Absorption |
| 5 | Float |
| 6 | Storage |
| 7 | Equalize |
| 8 | Passthru |
| 9 | Inverting |
| 10 | Power assist |
| 11 | Power supply |
| 252 | External control |

When `solar_charger` is present, the snapshot includes:

```json
"solar_charger": {
  "unit_id": 226,
  "pv_voltage_v": 48.50,
  "charge_current_a": 12.3,
  "pv_power_w": 580,
  "yield_today_kwh": 4.2,
  "state_code": 3,
  "state": "Bulk"
}
```

When `pv_inverter` is present:

```json
"pv_inverter": {
  "unit_id": 32,
  "ac_power_l1_w": 1500,
  "ac_voltage_l1_v": 230.0,
  "ac_current_l1_a": 6.5,
  "position": "AC output"
}
```

### Per-Metric Payloads

Individual topics under `energy/victron/` publish **scalar plain-text** values (not JSON). Examples from a live poll:

```
energy/victron/battery/soc          91
energy/victron/battery/voltage      52.3
energy/victron/battery/power        -450
energy/victron/grid/power_l1        32
energy/victron/load/consumption_l1  2163
energy/victron/inverter/state       Passthru
energy/victron/inverter/grid_lost   False
```

**Monitor all Victron topics:**

```bash
mosquitto_sub -h localhost -t 'energy/victron/#' -v
```

**Subscribe to a single metric (Node-RED, scripts):**

```bash
mosquitto_sub -h 192.168.2.4 -t 'energy/victron/battery/soc' -v
```

---

### SMS Gateway Status

**Topic:** `sms/gateway/status`

**Schema:**
```
ISO8601 timestamp string
```

**Description:** Timestamp when device went online or last status update.

**Example:**
```
2026-01-25T17:00:00+00:00
```

---

### SMS Gateway: WiFi / MQTT link recovery (firmware)

The ESP32 device keeps MQTT **in the same “connected” state as the user-visible WiFi link**:

- The firmware updates its internal WiFi-connected flag from **`WiFi.status()` on every main-loop pass**, not only on the slower periodic WiFi check. That way, when the stack **auto-reconnects** after a router or power outage, **MQTT reconnection runs immediately** instead of being skipped until a full device reboot.
- On each **MQTT** connect attempt, the firmware **closes the previous TCP session** (disconnect + stop on the `WiFiClient`) so a half-open socket from a long brownout does not block a new connection to the broker.
- **Emergency SMS** for MQTT exhaustion can still fire in repeated cycles; when the broker is back, the device recovers and may send a **“MQTT connection restored”** text only if that success follows **at least one failed connect** in the same recovery (not on a clean first connect at cold boot).

---

### OTA Update Command

**Topic:** `sms/gateway/command/ota`

**Schema:**
```json
{
  "action": "enable|disable"
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `action` | string | Yes | Must be "enable" or "disable" |

**Example (Enable):**
```json
{
  "action": "enable"
}
```

**Example (Disable):**
```json
{
  "action": "disable"
}
```

---

### OTA Update Status

**Topic:** `sms/gateway/ota/status`

**Schema:**
```json
{
  "status": "started|completed|error",
  "type": "sketch|filesystem",
  "timestamp": "ISO8601 timestamp",
  "duration_ms": 5000,
  "error": "Error message",
  "error_code": 1
}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Update status: "started", "completed", or "error" |
| `type` | string | Update type: "sketch" or "filesystem" (only when status="started") |
| `timestamp` | string | ISO8601 timestamp |
| `duration_ms` | integer | Update duration in milliseconds (only when status="completed") |
| `error` | string | Error message (only when status="error") |
| `error_code` | integer | Error code (only when status="error") |

**Example (Started):**
```json
{
  "status": "started",
  "type": "sketch",
  "timestamp": "2026-01-25T17:00:00+00:00"
}
```

**Example (Completed):**
```json
{
  "status": "completed",
  "duration_ms": 45230,
  "timestamp": "2026-01-25T17:00:45+00:00"
}
```

**Example (Error):**
```json
{
  "status": "error",
  "error": "Receive Failed",
  "error_code": 3,
  "timestamp": "2026-01-25T17:00:00+00:00"
}
```

---

### OTA Update Progress

**Topic:** `sms/gateway/ota/progress`

**Schema:**
```json
{
  "progress": 50,
  "bytes": 524288,
  "total": 1048576
}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `progress` | integer | Progress percentage (0-100) |
| `bytes` | integer | Bytes received so far |
| `total` | integer | Total bytes to receive |

**Example:**
```json
{
  "progress": 50,
  "bytes": 524288,
  "total": 1048576
}
```

**Note:** Progress updates are published every 10% increment.

---

**Example (Acknowledged):**
```json
{
  "request_id": "shutdown-desktop-abc123-1736429400",
  "action": "shutdown",
  "success": true,
  "message": "Shutdown command acknowledged (graceful)",
  "timestamp": "2026-01-09T15:30:01+02:00",
  "client_id": "desktop-abc123",
  "hostname": "DESKTOP-ABC123"
}
```

**Example (Executing):**
```json
{
  "request_id": "shutdown-desktop-abc123-1736429400",
  "action": "shutdown",
  "success": true,
  "message": "Initiating graceful shutdown now",
  "timestamp": "2026-01-09T15:30:05+02:00",
  "client_id": "desktop-abc123",
  "hostname": "DESKTOP-ABC123"
}
```

**Example (Error):**
```json
{
  "request_id": "shutdown-desktop-abc123-1736429400",
  "action": "shutdown",
  "success": false,
  "message": "Failed to execute shutdown command",
  "timestamp": "2026-01-09T15:30:05+02:00",
  "client_id": "desktop-abc123",
  "hostname": "DESKTOP-ABC123"
}
```

---

## Usage Examples

### Python Client Example

```python
import paho.mqtt.client as mqtt
import json
from datetime import datetime

# MQTT settings
BROKER = "localhost"
PORT = 1883
USERNAME = "dell_t310"
PASSWORD = "your_password"

# Create client
client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)

# Connect to broker
client.connect(BROKER, PORT)

# Send boot command
boot_command = {
    "action": "boot",
    "method": "wol",
    "timestamp": datetime.now().isoformat(),
    "request_id": "boot-001"
}

client.publish("dell/t310/command/boot", json.dumps(boot_command))

# Subscribe to responses
def on_message(client, userdata, msg):
    response = json.loads(msg.payload)
    print(f"Response: {response}")

client.on_message = on_message
client.subscribe("dell/t310/response")
client.loop_forever()
```

### Command Line Examples

**Boot server:**
```bash
mosquitto_pub -h localhost -t "dell/t310/command/boot" \
  -u dell_t310 -P password \
  -m '{"action":"boot","method":"wol","timestamp":"2025-12-25T20:00:00+02:00","request_id":"boot-001"}'
```

**Shutdown server:**
```bash
mosquitto_pub -h localhost -t "dell/t310/command/shutdown" \
  -u dell_t310 -P password \
  -m '{"action":"shutdown","type":"graceful","timeout":300,"timestamp":"2025-12-25T20:00:00+02:00","request_id":"shutdown-001"}'
```

**Monitor status:**
```bash
mosquitto_sub -h localhost -t "dell/t310/status" \
  -u dell_t310 -P password -v
```

**Monitor responses:**
```bash
mosquitto_sub -h localhost -t "dell/t310/response" \
  -u dell_t310 -P password -v
```

**Monitor Victron energy metrics:**
```bash
mosquitto_sub -h localhost -t "energy/victron/#" -v
```

---

## Error Handling

### Invalid Messages

If a message doesn't match the schema, the server will:
1. Log an error
2. Not execute the command
3. Not send a response (invalid messages are ignored)

### Command Failures

If a command fails to execute:
1. An error is logged
2. A response is sent with `success: false`
3. The `message` field contains error details

---

## Best Practices

1. **Always include request_id** - Use unique IDs for tracking
2. **Use ISO8601 timestamps** - Include timezone information
3. **Subscribe to responses** - Monitor command execution
4. **Handle timeouts** - Commands may take time to execute
5. **Use appropriate QoS** - QoS 1 for commands, QoS 0 for logs

---

## Version History

- **v1.1** (2026-07-04) - Victron Cerbo GX energy metrics (`energy/victron/#`) via Modbus publisher
- **v1.0** (2025-12-25) - Initial protocol specification

---

For implementation details, see [DEVELOPMENT_GUIDE.md](../DEVELOPMENT_GUIDE.md).
