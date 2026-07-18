# SMS Interface Documentation

This document provides a comprehensive guide to the SMS command interface and emergency forwarding for the automation system.

## Overview

The SMS interface mirrors the full Telegram command set. Send commands via SMS to the gateway SIM; only numbers in the allowed list can execute commands. All received SMS are forwarded to the emergency phone for monitoring.

---

## 🚀 Prerequisites

- SMS Gateway device (ESP32 + SIM800) connected to MQTT
- Node-RED flows 510, 511, 514 imported and deployed
- Your phone number added to the allowed list (Dashboard → SMS Gateway tab)

---

## 📱 Command Reference

Commands are case-insensitive. Use with or without `/` prefix (e.g. `help`, `/help`, `HELP` all work).

### 🖥️ Server Management
| Command | Description |
|---------|-------------|
| `BOOT [dell\|hp]` | Boot a server (default: dell) |
| `SHUTDOWN [dell\|hp]` | Graceful shutdown (default: dell) |
| `FORCE [dell\|hp]` | Immediate power-off |
| `STATUS` | Get all server statuses |

### 🚪 Main Gate
| Command | Description |
|---------|-------------|
| `GATE_OPEN` or `GATE` | Open main gate (pulse) |
| `GATE_STATUS` | Get gate status |

### 🚪 Sliding Gate
| Command | Description |
|---------|-------------|
| `SLIDING_OPEN` | Open sliding gate |
| `SLIDING_CLOSE` | Close sliding gate |
| `SLIDING_TRIGGER` | Trigger automation |
| `SLIDING_STATUS` | Get status |

### 🚪 Secondary Gate
| Command | Description |
|---------|-------------|
| `SECONDARY_OPEN` | Open gate |
| `SECONDARY_CLOSE` | Close gate |
| `SECONDARY_TRIGGER` | Trigger automation |
| `SECONDARY_STOP` | Stop gate |
| `SECONDARY_LIGHT_LEFT` | Left light (120s) |
| `SECONDARY_LIGHT_RIGHT` | Right light (120s) |
| `SECONDARY_STATUS` | Get status |

### 💡 Garden Power & Lights
| Command | Description |
|---------|-------------|
| `GARDEN_ON` | Turn garden power ON |
| `GARDEN_OFF` | Turn garden power OFF |
| `GARDEN_TOGGLE` | Toggle power |
| `GARDEN_STATUS` | Get power status |
| `LIGHTS_ON` | Turn all 16 lights ON |
| `LIGHTS_OFF` | Turn all 16 lights OFF |
| `LIGHTS_STATUS` | Get lights summary |

### 💧 Water Pump
| Command | Description |
|---------|-------------|
| `PUMP_START` | Start pump |
| `PUMP_STOP` | Stop pump |
| `PUMP_DRAIN` | Drain water (10s pulse) |
| `PUMP_TRENCH1_ON` / `PUMP_TRENCH1_OFF` | Feed trench 1 |
| `PUMP_TRENCH2_ON` / `PUMP_TRENCH2_OFF` | Feed trench 2 |
| `PUMP_STATUS` | Get pump status |

### 🐠 Aquarium
| Command | Description |
|---------|-------------|
| `AQUARIUM_ON` | Light ON |
| `AQUARIUM_OFF` | Light OFF |
| `AQUARIUM_TOGGLE` | Toggle light |
| `AQUARIUM_STATUS` | Get status |

### 📷 Camera (Tapo ICMP watchdog)
| Command | Description |
|---------|-------------|
| `CAMERA_STATUS` | Camera health and last detection event |
| `CAMERA_HELP` | Camera system help |

### 📱 SMS Gateway
| Command | Description |
|---------|-------------|
| `SMS_STATUS` | Gateway WiFi/MQTT/GSM status |
| `SMS_LOG` | Last 3 received SMS |

### ❓ Help
| Command | Description |
|---------|-------------|
| `HELP` or `COMMANDS` or `LIST` or `START` | Full command list: **8 SMS messages** with descriptions (sent with 3s then 5s spacing) |

---

## 🔄 Message Flow

1. **Receive**: SMS arrives on gateway SIM → device publishes to `sms/gateway/receive/*`
2. **Forward**: Flow 511 forwards all SMS to emergency phone (`+40740244845`) via `sms/gateway/command/send`
3. **Process**: Flow 511 publishes to `sms/command/received` → Flow 514 subscribes
4. **Parse**: Flow 514 extracts command from text (strips modem `+CMGR:` lines if present)
5. **Authorize**: Only allowed phone numbers can trigger commands
6. **Reply**: Flow 514 sends reply with 3-second delay (avoids modem conflict with forward). For HELP/COMMANDS/LIST, **multiple SMS** are sent (8 chunks) with 5-second spacing between each (rate limit) so the modem can send one at a time.

---

## ⚙️ Configuration

### Allowed Phones
- **Location**: Dashboard → SMS Gateway tab → Allowed phones (SMS commands)
- **Format**: Comma-separated with country code (e.g. `+40740244845, +40745218721`)
- **Default**: `+40740244845`, `+40745218721` (set at flow init)

### Emergency Phone
- **Hardcoded**: `+40740244845` in flow 511
- All received SMS are forwarded to this number

---

## 🔧 Technical Details

### MQTT Topics
| Topic | Purpose |
|-------|---------|
| `sms/command/received` | Internal: Flow 511 → 514 (JSON payload with `latest`) |
| `sms/gateway/command/send` | Send SMS (JSON: `{ to, text }`) |

### Payload Format
- **Send SMS**: JSON string `{"to":"40740244845","text":"Hello"}` (digits-only for `to`)
- **Internal**: Flow 511 publishes `JSON.stringify({ messages, messageCount, latest })`

### Modem Output Handling
Gateway may include raw AT response lines (e.g. `+CMGR: "REC READ",...`) in the SMS text. Flow 514 strips these and extracts the actual command line.

### Reply Delay
A 3-second delay before sending command replies avoids GSM modem conflicts when both the forward and reply are queued in quick succession. **Multi-SMS**: When the reply is multiple messages (e.g. HELP), a rate-limit delay (1 message per 5 seconds) after the 3s delay spaces them so the device sends one SMS at a time.

---

## 🆘 Troubleshooting

- **No reply to HELP**: Ensure your number is in the allowed list with full country code (`+40...`)
- **Reply arrives late**: Expected—3-second delay to avoid modem conflict with forward
- **Forward not received**: Check emergency phone is correct and gateway has GSM signal
- **Unknown command**: Send `HELP` for the command list; commands are case-insensitive

---
**Version**: 1.0.0  
**Last Updated**: February 2026
