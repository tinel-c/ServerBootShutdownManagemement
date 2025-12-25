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
