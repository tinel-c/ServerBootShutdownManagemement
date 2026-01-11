# Release Notes - Version 2.5.0

**Release Date:** January 2026

## Overview

Version 2.5.0 introduces Telegram bot integration, allowing users to control servers and receive status notifications directly from Telegram. This release adds a complete Telegram interface with inline keyboard buttons matching the Node-RED dashboard functionality.

## 🎉 New Features

### 1. Telegram Bot Interface

Complete Telegram bot integration for server management via mobile or desktop Telegram clients.

**Features:**
- **Command Interface**: Control servers using simple text commands (`/boot`, `/shutdown`, `/force`, `/status`, `/help`)
- **Inline Keyboard**: Interactive buttons matching all Node-RED dashboard controls
- **Real-time Notifications**: Automatic alerts on server state changes
- **Command Responses**: Real-time feedback on command execution
- **User Authorization**: Restrict access to authorized Telegram user IDs
- **Polling & Webhook Support**: Works with polling (default) or webhook mode

**Available Commands:**
- `/boot [dell|hp]` - Boot a server (default: dell)
- `/shutdown [dell|hp]` - Graceful shutdown (default: dell)
- `/force [dell|hp]` - Force shutdown (default: dell)
- `/status` - Get current server status
- `/help` - Show help with interactive buttons

**Inline Keyboard Buttons:**
- Boot Dell T310 | Boot HP DL360p
- Shutdown Dell T310 | Shutdown HP DL360p
- Force Dell T310 | Force HP DL360p
- Server Status | Help

**Technical Details:**
- Uses `node-red-contrib-telegrambot` library
- New flow: `50-telegram-interface.json`
- MQTT integration for command execution
- Status tracking and change detection
- Callback query handling for button clicks

**Documentation:** See `nodered/TELEGRAM_SETUP.md` for complete setup guide

## 🔧 Improvements

### Node-RED Integration

- **New Flow Module**: `50-telegram-interface.json` for Telegram interface
- **Modular Design**: Follows existing modular flow architecture
- **MQTT Integration**: Seamlessly integrates with existing MQTT command system
- **Status Notifications**: Subscribes to server status topics for real-time updates

### Docker Configuration

- **Updated Dockerfile**: Includes `node-red-contrib-telegrambot` package installation
- **Environment Variables**: Support for `TELEGRAM_BOT_TOKEN` and `TELEGRAM_ALLOWED_USERS`

### Documentation

- **Setup Guide**: Complete Telegram bot setup instructions in `nodered/TELEGRAM_SETUP.md`
- **Flow Documentation**: Updated `nodered/flows/README.md` with Telegram interface details
- **Main README**: Added Telegram interface to main documentation

## 📦 Dependencies

### New Dependencies

- `node-red-contrib-telegrambot` (v17.0.5+) - Telegram bot integration library

### Updated Dependencies

- Node-RED Docker image includes Telegram bot library

## 🚀 Installation

### Prerequisites

1. Telegram account
2. Bot token from [@BotFather](https://t.me/botfather)
3. Node-RED running (Docker container)

### Setup Steps

1. **Rebuild Docker Container:**
   ```bash
   cd nodered
   docker-compose build
   docker-compose up -d
   ```

2. **Create Telegram Bot:**
   - Contact [@BotFather](https://t.me/botfather) on Telegram
   - Send `/newbot` and follow instructions
   - Save the bot token

3. **Import Telegram Flow:**
   - Open Node-RED: http://localhost:1880
   - Import `flows/50-telegram-interface.json`
   - Configure the `telegrambot-config` node with your bot token
   - Deploy

4. **Configure Authorization (Optional):**
   - Set `TELEGRAM_ALLOWED_USERS` environment variable with comma-separated user IDs
   - Or configure in the telegrambot-config node

5. **Test:**
   - Open Telegram and search for your bot
   - Send `/help` to see available commands and buttons

**Detailed Setup:** See `nodered/TELEGRAM_SETUP.md`

## 🔄 Migration from Previous Versions

No migration required. This is a new feature that doesn't affect existing functionality.

## 📝 Files Changed

### New Files
- `nodered/flows/50-telegram-interface.json` - Telegram bot flow
- `nodered/TELEGRAM_SETUP.md` - Complete setup guide
- `RELEASE_NOTES_v2.5.0.md` - This file

### Modified Files
- `nodered/Dockerfile` - Added telegrambot library installation
- `nodered/flows/README.md` - Added Telegram interface documentation
- `README.md` - Added Telegram interface to main documentation

## 🐛 Bug Fixes

- None (new feature release)

## 🔒 Security

- Bot token stored in environment variables (not in code)
- Optional user authorization via `TELEGRAM_ALLOWED_USERS`
- HTTPS required for webhook mode (Telegram requirement)

## 📚 Documentation

- **Telegram Setup Guide**: `nodered/TELEGRAM_SETUP.md`
- **Flow Documentation**: `nodered/flows/README.md`
- **Main Documentation**: `README.md`

## 🙏 Acknowledgments

- `node-red-contrib-telegrambot` library by windkh
- Telegram Bot API documentation

---

**Full Changelog**: See git commit history for detailed changes.
