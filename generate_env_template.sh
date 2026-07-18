#!/bin/bash
#
# Generate .env template file with all required environment variables
#

TEMPLATE_FILE="config/.env.example"

cat > "$TEMPLATE_FILE" << 'EOF'
# =============================================================================
# Server Management System - Environment Configuration
# =============================================================================
# Copy this file to .env and fill in your actual values
# cp .env.example .env
#
# IMPORTANT: Never commit .env file to git!
# =============================================================================

# -----------------------------------------------------------------------------
# MQTT Broker Configuration
# -----------------------------------------------------------------------------
# Linux automation server / SSH target
MQTT_BROKER_HOST=192.168.2.4
MQTT_BROKER_PORT=1883
MQTT_USERNAME=mqtt_user
MQTT_PASSWORD=mqtt_password

# -----------------------------------------------------------------------------
# Dell T310 Server Configuration
# -----------------------------------------------------------------------------

# IPMI Configuration (for reference, but Proxmox API is now used for status)
T310_IPMI_HOST=192.168.1.10
T310_IPMI_USERNAME=admin
T310_IPMI_PASSWORD=password

# Proxmox Configuration (REQUIRED - used for status monitoring)
T310_PROXMOX_HOST=192.168.1.10
T310_PROXMOX_USERNAME=root@pam
T310_PROXMOX_PASSWORD=proxmox_password

# Network Configuration
T310_MAC_ADDRESS=00:11:22:33:44:55

# Health Check Configuration (from Healthchecks.io)
# Comma-separated list of health check names
T310_HEALTHCHECKS=dell-t310-health,dell-t310-backup

# -----------------------------------------------------------------------------
# HP DL360p Server Configuration
# -----------------------------------------------------------------------------

# iLO Configuration
DL360P_ILO_HOST=192.168.1.20
DL360P_ILO_USERNAME=Administrator
DL360P_ILO_PASSWORD=ilo_password

# Proxmox Configuration
DL360P_PROXMOX_HOST=192.168.1.20
DL360P_PROXMOX_USERNAME=root@pam
DL360P_PROXMOX_PASSWORD=proxmox_password

# Network Configuration
DL360P_MAC_ADDRESS=AA:BB:CC:DD:EE:FF

# Health Check Configuration
DL360P_HEALTHCHECKS=hp-dl360p-health,hp-dl360p-backup

# -----------------------------------------------------------------------------
# Healthchecks.io Configuration
# -----------------------------------------------------------------------------
# Get your Read-Only API Key from: https://healthchecks.io/docs/api/
HEALTHCHECKS_API_KEY=your_read_only_api_key_here

# -----------------------------------------------------------------------------
# Telegram Bot Configuration (Optional)
# -----------------------------------------------------------------------------
# Get bot token from @BotFather on Telegram
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# Comma-separated list of allowed user IDs
# Get your user ID from @userinfobot on Telegram
TELEGRAM_ALLOWED_USERS=123456789,987654321

# -----------------------------------------------------------------------------
# Logging Configuration (Optional)
# -----------------------------------------------------------------------------
LOG_LEVEL=INFO
LOG_FILE=/data/logs/automation/dell_server_management.log
EOF

echo "✓ Created $TEMPLATE_FILE"
echo ""
echo "Next steps:"
echo "  1. Copy template: cp $TEMPLATE_FILE config/.env"
echo "  2. Edit config/.env with your actual values"
echo "  3. Set permissions: chmod 600 config/.env"
