# Telegram Bot Setup Guide

This guide explains how to set up and configure the Telegram interface for the Server Boot/Shutdown Management system using the `node-red-contrib-telegrambot` library.

## Overview

The Telegram interface allows you to control your servers and receive status notifications via Telegram. You can:
- Boot and shutdown servers using simple commands
- Check server status
- Receive automatic notifications when server states change
- Get real-time feedback on command execution

## Prerequisites

1. **Telegram Account**: You need a Telegram account
2. **Node-RED Running**: The Node-RED dashboard must be running on Ubuntu
3. **Telegram Bot Library**: Install `node-red-contrib-telegrambot` in Node-RED

## Step 1: Create a Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Start a conversation with BotFather
3. Send the command: `/newbot`
4. Follow the prompts:
   - Choose a name for your bot (e.g., "Server Manager Bot")
   - Choose a username (must end in `bot`, e.g., "my_server_manager_bot")
5. BotFather will provide you with a **Bot Token** (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
6. **Save this token** - you'll need it in the next step

## Step 2: Get Your User ID (Optional - for Authorization)

If you want to restrict bot access to specific users:

1. Search for [@userinfobot](https://t.me/userinfobot) on Telegram
2. Start a conversation - it will reply with your user ID
3. Save your user ID (a numeric value like `123456789`)

## Step 3: Install Telegram Bot Library

Install the `node-red-contrib-telegrambot` package in Node-RED:

**Option 1 - Via Node-RED Palette Manager:**
1. Open Node-RED: http://localhost:1880
2. Click menu (≡) → Manage palette
3. Click "Install" tab
4. Search for `node-red-contrib-telegrambot`
5. Click "Install"

**Option 2 - Via npm (in Node-RED directory):**
```bash
cd ~/.node-red  # or your Node-RED directory
npm install node-red-contrib-telegrambot
sudo systemctl restart nodered
```

## Step 4: Import the Telegram Flow

1. Open Node-RED: http://localhost:1880
2. Click the menu (≡) → **Import**
3. Select `flows/50-telegram-interface.json`
4. Click **Import**

**Note**: If you see "unknown" nodes after importing, the node type identifiers in the flow might not match your installed library version. To verify the correct node types:
   1. Create a simple test flow with a "telegram receiver" and "telegram sender" node
   2. Export the flow (Menu → Export → Clipboard)
   3. Check the `type` field in the JSON for the actual node type identifiers
   4. Update the flow file if needed

5. **DO NOT deploy yet** - you need to configure the bot first

## Step 5: Configure the Telegram Bot

1. In Node-RED editor, find the **"Server Management Bot"** config node (telegrambot-config)
2. Double-click it to open the configuration
3. Enter your **Bot Token** in the "Token" field
4. (Optional) If you want to restrict access, enter comma-separated user IDs in the "Usernames" field, or set the `TELEGRAM_ALLOWED_USERS` environment variable
5. **Polling vs Webhook**:
   - **Polling (Default)**: Works out of the box, no public URL needed. Select "Polling" mode
   - **Webhook (Recommended for Production)**: More efficient, requires public URL. Uncheck "Polling" and configure webhook URL
6. Click **Done** to save

### Polling Mode (Default - Easiest)

- ✅ Works immediately, no configuration needed
- ✅ No public URL required
- ✅ Perfect for testing and local development
- ⚠️ Less efficient (checks for updates every few seconds)
- ⚠️ Not recommended for high-traffic bots

**To use polling mode:**
1. In the telegrambot-config node, ensure "Polling" is checked
2. Leave "Updates" checked
3. No additional configuration needed

### Webhook Mode (Recommended for Production)

- ✅ More efficient (real-time updates)
- ✅ Better for production environments
- ⚠️ Requires public HTTPS URL
- ⚠️ Requires additional setup

**To use webhook mode:**

1. **Get a public URL**:
   - Use a service like [ngrok](https://ngrok.com/) for testing: `ngrok http 1880`
   - Or use your own domain with HTTPS

2. **Configure the webhook**:
   - In the telegrambot-config node, uncheck "Polling"
   - Set the webhook URL (e.g., `https://your-domain.com/telegrambot/your-bot-token`)
   - The library will automatically set up the webhook when you deploy

3. **Or set webhook manually**:
   ```bash
   curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://your-domain.com/telegrambot/<YOUR_BOT_TOKEN>"
   ```

## Step 6: Configure Authorization (Optional)

You can restrict bot access in two ways:

### Option A: Environment Variable

Set `TELEGRAM_ALLOWED_USERS` environment variable for Node-RED service.

Add to Node-RED systemd service file or set in Node-RED settings.js:

```javascript
// In settings.js
functionGlobalContext: {
    TELEGRAM_ALLOWED_USERS: "123456789,987654321"  // Comma-separated user IDs
}
```

### Option B: Config Node

Enter comma-separated user IDs in the "Usernames" field of the telegrambot-config node.

**Note**: The flow also checks `TELEGRAM_ALLOWED_USERS` environment variable, so either method works.

## Step 7: Deploy and Test

1. Click **Deploy** in Node-RED
2. Open Telegram and search for your bot (using the username you created)
3. Start a conversation with `/start` or `/help`
4. Try commands:
   - `/status` - Check server status
   - `/boot dell` - Boot Dell T310
   - `/shutdown hp` - Shutdown HP DL360p

## Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/boot [server]` | Boot a server | `/boot dell` or `/boot hp` |
| `/shutdown [server]` | Graceful shutdown | `/shutdown dell` or `/shutdown hp` |
| `/force [server]` | Force shutdown | `/force dell` or `/force hp` |
| `/status` | Get server status | `/status` |
| `/help` | Show help message | `/help` |
| `/start` | Start conversation (shows help) | `/start` |

**Server Options**:
- `dell` or `t310` - Dell T310 server
- `hp` or `dl360p` - HP DL360p server
- If omitted, defaults to `dell`

## Features

### Automatic Notifications

The bot automatically sends notifications when:
- Server state changes (online ↔ offline)
- Commands are executed (success/error responses)

### Authorization

If `TELEGRAM_ALLOWED_USERS` is set or configured in the config node, only users with IDs in that list can use the bot. Others will receive an "Unauthorized" message.

### Status Tracking

The bot tracks server status and provides:
- Current state (online/offline/unknown)
- Last update timestamp
- State change history

## Troubleshooting

### Bot Doesn't Respond

1. **Check Bot Token**: Verify the token is correctly entered in the telegrambot-config node
2. **Check Node-RED Logs**: Look for errors in Node-RED debug panel or system logs:
   ```bash
   journalctl -u nodered -f
   ```
3. **Check Authorization**: If `TELEGRAM_ALLOWED_USERS` is set, verify your user ID is included
4. **Verify Bot is Running**: Check that the telegrambot-config node shows as "connected" (green dot)

### Polling Mode Issues

1. **Check Internet Connection**: Polling requires internet access to Telegram API
2. **Check Firewall**: Ensure Node-RED can make outbound HTTPS connections
3. **Check Logs**: Look for polling errors in Node-RED debug panel

### Webhook Mode Issues

1. **SSL Certificate**: Telegram requires HTTPS for webhooks. Use ngrok or a proper SSL certificate
2. **URL Accessibility**: Ensure the webhook URL is publicly accessible
3. **Port Forwarding**: If behind a firewall, forward port 1880 (or your Node-RED port)
4. **Verify Webhook**: Check webhook status:
   ```bash
   curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
   ```

### Commands Not Working

1. **Check MQTT**: Verify MQTT broker is running and Node-RED is connected
2. **Check Topics**: Verify MQTT topics match your backend configuration
3. **Check Authorization**: Verify you're authorized (if `TELEGRAM_ALLOWED_USERS` is set)
4. **Check Flow**: Verify the flow is deployed and all nodes are connected

### Status Not Updating

1. **Check MQTT Subscriptions**: Verify Node-RED is subscribed to status topics
2. **Check Backend**: Verify backend services are publishing status updates
3. **Check Flow Context**: Status is stored in flow context - restart Node-RED if needed

### Library Not Found

If you see errors about `node-red-contrib-telegrambot` not being found:

1. **Install the Library**: Make sure the package is installed in Node-RED
2. **Check Installation**: Verify the package is installed:
   ```bash
   cd ~/.node-red  # or your Node-RED directory
   npm list node-red-contrib-telegrambot
   ```
3. **Manual Install** (if needed):
   ```bash
   cd ~/.node-red  # or your Node-RED directory
   npm install node-red-contrib-telegrambot
   sudo systemctl restart nodered
   ```

## Security Considerations

1. **Bot Token**: Keep your bot token secret. Never commit it to version control
2. **Authorization**: Always set `TELEGRAM_ALLOWED_USERS` in production
3. **HTTPS**: Use HTTPS for webhooks (required by Telegram)
4. **Firewall**: Consider restricting webhook endpoint access

## Advanced Configuration

### Custom Command Responses

You can modify the function nodes to customize command responses and notifications.

### Multiple Bots

You can run multiple Telegram bots by:
1. Creating additional bot tokens
2. Duplicating the flow
3. Creating new telegrambot-config nodes with different tokens

### Notification Filters

Modify the status notification functions to filter notifications (e.g., only notify on critical state changes).

### Using Environment Variables for Bot Token

You can also set the bot token via environment variable and reference it in the config node:

1. Set `TELEGRAM_BOT_TOKEN` in Node-RED settings or environment:
   ```javascript
   // In settings.js
   functionGlobalContext: {
       TELEGRAM_BOT_TOKEN: "your_bot_token_here"
   }
   ```

2. In the telegrambot-config node, you can reference it in a function node using `global.get('TELEGRAM_BOT_TOKEN')`.

## Differences from HTTP-based Implementation

This implementation uses the `node-red-contrib-telegrambot` library which provides:

- ✅ **Simpler Setup**: No manual webhook configuration needed
- ✅ **Automatic Reconnection**: Library handles connection issues
- ✅ **Better Error Handling**: Built-in error handling and retries
- ✅ **Polling Support**: Works without public URL
- ✅ **Dedicated Nodes**: Cleaner flow with dedicated Telegram nodes

## Support

For issues or questions:
- Check Node-RED debug panel for errors
- Review MQTT topics using MQTT Explorer
- Check Telegram Bot API documentation: https://core.telegram.org/bots/api
- Check node-red-contrib-telegrambot documentation: https://flows.nodered.org/node/node-red-contrib-telegrambot

---

**Last Updated**: January 2026
**Version**: 2.0.0 (Using node-red-contrib-telegrambot)
