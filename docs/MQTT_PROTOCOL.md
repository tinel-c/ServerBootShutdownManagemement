# MQTT Protocol Specification

This document defines the MQTT message format and protocol for the Dell T310 Management System.

## Overview

The system uses MQTT for all remote commands and status updates. All messages are JSON-formatted and follow a consistent structure.

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

- **v1.0** (2025-12-25) - Initial protocol specification

---

For implementation details, see [DEVELOPMENT_GUIDE.md](../DEVELOPMENT_GUIDE.md).
