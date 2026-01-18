# Telegram Interface Documentation

This document provides a comprehensive guide to setting up, using, and managing the Telegram bot interface for the automation system.

## Overview
The Telegram interface allows remote control and monitoring of servers, gates, lights, and other automation domains via a unified bot.

---

## 🚀 Setup Guide

### 1. Create a Bot
1. Message [@BotFather](https://t.me/botfather) on Telegram.
2. Use `/newbot` and follow instructions to get your **Bot Token**.

### 2. Get Your User ID
1. Message [@userinfobot](https://t.me/userinfobot) to get your numeric ID.
2. Use this ID for authorization.

### 3. Installation
1. Install `node-red-contrib-telegrambot` in Node-RED.
2. Import `nodered/flows/50-telegram-interface.json`.
3. Configure the **"Server Management Bot"** node with your token.

---

## 📋 Command Reference

### 🖥️ Server Management
| Command | Description |
|---------|-------------|
| `/boot [dell\|hp]` | Boot a server (default: dell) |
| `/shutdown [dell\|hp]` | Graceful shutdown (default: dell) |
| `/force [dell\|hp]` | Immediate power-off |
| `/status` | Get all server statuses |

### 🚪 Gate Automation
| Command | Description |
|---------|-------------|
| `/gate_open` | Open main gate (pulse) |
| `/gate_status` | Get comprehensive gate status |
| `/sliding_open` | Open sliding gate |
| `/sliding_close` | Close sliding gate |
| `/sliding_status` | Get sliding gate status |

### 💡 Lighting
| Command | Description |
|---------|-------------|
| `/lights_on` | Turn all garden lights ON |
| `/lights_off` | Turn all garden lights OFF |
| `/lights_status` | Get status of all 16 lights |

### 🐠 Aquarium
| Command | Description |
|---------|-------------|
| `/aquarium_on` | Turn aquarium light ON |
| `/aquarium_off` | Turn aquarium light OFF |
| `/aquarium_status` | Get aquarium status |

---

## 🚪 Gate Integration Details
The gate system sends automatic notifications for:
- **Power Changes**: Swapping between `MAINS` and `BATTERY`.
- **Relay State**: Confirmation of open/close actions.

---

## 🛠️ Customization: Help Layout
The `/help` command uses a sectioned layout for scalability.
To add a new domain to help:
1. Update `func_handle_help` in Node-RED.
2. Add a visual separator (`━━━━━`).
3. Use a section header with `callback_data: 'noop'`.

---

## 🆘 Troubleshooting
- **Bot not responding**: Check bot token and Node-RED connectivity.
- **Unauthorized**: Ensure your ID is in `TELEGRAM_ALLOWED_USERS`.
- **Status stale**: Verify MQTT broker is running and services are active.

---
**Version**: 2.0.0  
**Last Updated**: January 2026
