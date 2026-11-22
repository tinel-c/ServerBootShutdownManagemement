# SMS Interface Documentation

SMS is a command gateway with the same reach as Telegram, plus per-switch control for lights, illumination channels, irrigation zones, and energy breakers. Texts are pull-only: you send a command, the gateway replies. State-change alerts stay on Telegram.

## Overview

1. Phone texts the SIM on the ESP32 SMS gateway.
2. Gateway publishes `sms/gateway/receive/*`.
3. Flow 511 forwards the message for monitoring and publishes `sms/command/received`.
4. Flow 514 authorizes the sender, normalizes the command, and either answers `HELP` or publishes `sms/command/dispatch`.
5. Flow 515 runs the domain handler and publishes `sms/command/reply` (and device MQTT commands).
6. Flow 514 is the only path that sends `sms/gateway/command/send` for command replies (3 s delay, then 1 SMS / 5 s).

## Prerequisites

- SMS gateway online (MQTT + GSM)
- Flows 510, 511, 514, 515 deployed
- Your number on the allowlist (Dashboard → SMS Gateway → Allowed phones)

## Protocol

- Case-insensitive. Optional leading `/`.
- Underscores and spaces are equivalent: `ENERGY_STATUS` = `ENERGY STATUS`, `LIGHT_3_ON` = `LIGHT 3 ON`.
- Replies are ASCII (no emoji). Each part ≤ 150 characters.
- Only allowlisted numbers can run commands. Other SMS are still forwarded to the emergency phone.

### Help

| Command | Reply |
|---------|--------|
| `HELP` / `COMMANDS` / `LIST` / `START` | One SMS: domain index |
| `HELP ENERGY` (or `LIGHTS`, `ILLUM`, `IRRIG`, `GATE`, `SERVER`, …) | That domain’s commands |

### Servers

| Command | Description |
|---------|-------------|
| `BOOT [dell\|hp\|media]` | Boot (default dell) |
| `SHUTDOWN [dell\|hp\|media]` | Graceful shutdown |
| `FORCE [dell\|hp\|media]` | Force power-off |
| `STATUS` | Dell / HP / media status |

### Gates

| Command | Description |
|---------|-------------|
| `GATE_OPEN` / `GATE` | Open main gate |
| `GATE_STATUS` | Main gate status |
| `SLIDING_OPEN` / `CLOSE` / `TRIGGER` / `STATUS` | Sliding gate |
| `SECONDARY_OPEN` / `CLOSE` / `TRIGGER` / `STOP` / `STATUS` | Secondary gate |
| `SECONDARY_LIGHT_LEFT` / `SECONDARY_LIGHT_RIGHT` | Gate lights (120 s) |

### Garden power and lights

| Command | Description |
|---------|-------------|
| `GARDEN_ON` / `OFF` / `TOGGLE` / `STATUS` | Garden power outlet |
| `LIGHTS_ON` / `LIGHTS_OFF` / `LIGHTS_STATUS` | All 16 lights |
| `LIGHT <n> ON\|OFF` | Light 1–16 |

### Illumination (4-channel thyristor)

| Command | Description |
|---------|-------------|
| `ILLUM <n> ON\|OFF` | Channel 1–4 |
| `ILLUM OFF` | All channels off |
| `ILLUM_STATUS` | Channel states |

### Irrigation

| Command | Description |
|---------|-------------|
| `IRRIG <n> ON\|OFF` | Zone I1–I12 |
| `IRRIG_STATUS` | Zone summary |
| `IRRIG_A_START` / `PAUSE` / `RESUME` / `SKIP` | Lawn program (Area A) |
| `IRRIG_B_START` / `PAUSE` / `RESUME` / `SKIP` | Flowers program (Area B) |

### Water pump / aquarium / camera / SMS

| Command | Description |
|---------|-------------|
| `PUMP_START` / `STOP` / `DRAIN` / `STATUS` | Pump |
| `PUMP_TRENCH1_ON` / `OFF`, `PUMP_TRENCH2_ON` / `OFF` | Trenches |
| `AQUARIUM_ON` / `OFF` / `TOGGLE` / `STATUS` | Aquarium light |
| `CAMERA_STATUS` / `CAMERA_HELP` | Tapo health |
| `SMS_STATUS` / `SMS_LOG` | Gateway status / last SMS |

### Energy

| Command | Description |
|---------|-------------|
| `ENERGY_STATUS` / `START` / `STOP` | Victron + discretionary load |
| `HUAWEI_STATUS` | Huawei PV |
| `SCALA1_STATUS` / `START` / `STOP` | Grundfos SCALA1 |
| `CONSUMER_STATUS` | All breakers |
| `CONSUMER <id> ON\|OFF` | `front-lights-breaker`, `breaker-inside`, `breaker-outside`, `garden-power-hut` (aliases: `front`, `inside`, `outside`, `hut`) |

Unknown command → one SMS: `Unknown. Send HELP`.

## MQTT bus (Node-RED internal)

| Topic | Direction | Payload |
|-------|-----------|---------|
| `sms/command/received` | 511 → 514 | `{ messages, messageCount, latest }` |
| `sms/command/dispatch` | 514 → 515 | `{ from, command, args, originalText }` |
| `sms/command/reply` | 515 → 514 | `{ to, text }` or array of parts |
| `sms/gateway/command/send` | 514 → gateway | `{ to, text }` (JSON string) |
| `irrigation/command/area_a` | 515 → 420 bridge | `ON` / `pause` / `resume` / `skip` |
| `irrigation/command/area_b` | 515 → 420 bridge | same |

## Configuration

### Allowed phones

Dashboard → SMS Gateway → Allowed phones (comma-separated with country code). Defaults: `+40740244845`, `+40745218721`.

### Emergency forward

Hardcoded in flow 511. All received SMS are forwarded; only allowlisted numbers execute commands.

## Troubleshooting

- No reply: number must be on the allowlist with country code.
- Late reply: 3 s delay before the first reply, then 5 s between parts.
- Unknown command: send `HELP`, then `HELP <domain>`.

**Version:** 2.0.0  
**Last Updated:** November 2026
