#!/bin/bash
#
# Installation script for Dell & HP Server Management System
# This script installs all components and configures the system
# Supports Dell T310 (IPMI) and HP DL360p (iLO) servers
#

set -e  # Exit on error

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/install/common.sh
source "$SCRIPT_DIR/scripts/install/common.sh"

# Installation directory (also set in common.sh)
LOG_DIR="/var/log"
LOG_FILE="${LOG_DIR}/dell_server_management.log"

# Check if running as root
require_root "$0"

print_info "Starting Dell & HP Server Management System installation..."

# Step 1: Install system dependencies
print_info "Step 1: Installing system dependencies..."
apt-get update
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    ipmitool \
    wakeonlan \
    git

# Step 2: Create installation directory
print_info "Step 2: Creating installation directory..."

# Check for existing .env BEFORE backing up the directory
HAS_EXISTING_ENV=false
if [ -f "$INSTALL_DIR/config/.env" ]; then
    print_warn "Found existing .env configuration. Preserving it..."
    # Create temp backup in /tmp (survives directory moves)
    cp "$INSTALL_DIR/config/.env" /tmp/dell_server_management_env.bak.$(date +%Y%m%d_%H%M%S)
    # Keep the most recent backup with a simple name for restore
    cp "$INSTALL_DIR/config/.env" /tmp/dell_server_management_env.bak
    HAS_EXISTING_ENV=true
    print_info "Configuration backed up to /tmp/dell_server_management_env.bak"
fi

# Check for existing device .env files BEFORE backing up the directory
backup_device_env "$INSTALL_DIR/device/victron-multiplus-ii/config/.env" /tmp/dell_server_victron_env.bak
backup_device_env "$INSTALL_DIR/device/huawei-inverter/config/.env" /tmp/dell_server_huawei_env.bak
backup_device_env "$INSTALL_DIR/device/grundfos-scala1/config/.env" /tmp/dell_server_grundfos_env.bak

HAS_TUYA_DEVICES=false
if [ -f "$INSTALL_DIR/config/tuya_devices.json" ]; then
    cp "$INSTALL_DIR/config/tuya_devices.json" /tmp/dell_server_tuya_devices.bak
    HAS_TUYA_DEVICES=true
    print_info "Tuya device registry backed up to /tmp/dell_server_tuya_devices.bak"
fi

if [ -d "$INSTALL_DIR" ]; then
    print_warn "Installation directory already exists. Backing up..."
    mv "$INSTALL_DIR" "${INSTALL_DIR}.backup.$(date +%Y%m%d_%H%M%S)"
fi

mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Step 3: Copy project files
print_info "Step 3: Copying project files..."

# Copy files from source
cp -r "$SCRIPT_DIR"/* "$INSTALL_DIR/"

# Restore .env if it existed
if [ "$HAS_EXISTING_ENV" = true ]; then
    print_info "Restoring preserved .env configuration..."
    cp /tmp/dell_server_management_env.bak "$INSTALL_DIR/config/.env"
    
    # Ensure permissions are still correct
    chmod 600 "$INSTALL_DIR/config/.env"
    print_info "✓ Configuration successfully preserved from previous installation!"
fi

restore_device_env "$INSTALL_DIR/device/victron-multiplus-ii/config/.env" \
    /tmp/dell_server_victron_env.bak \
    "$INSTALL_DIR/device/victron-multiplus-ii/config/.env.example" \
    "edit VICTRON_GX_HOST and Unit IDs"

restore_device_env "$INSTALL_DIR/device/huawei-inverter/config/.env" \
    /tmp/dell_server_huawei_env.bak \
    "$INSTALL_DIR/device/huawei-inverter/config/.env.example" \
    "edit HUAWEI_INVERTER_HOST and WiFi settings"

restore_device_env "$INSTALL_DIR/device/grundfos-scala1/config/.env" \
    /tmp/dell_server_grundfos_env.bak \
    "$INSTALL_DIR/device/grundfos-scala1/config/.env.example" \
    "edit SCALA1_BLE_ADDRESS after ble_probe.py --scan"

if [ "$HAS_TUYA_DEVICES" = true ]; then
    mkdir -p "$INSTALL_DIR/config"
    cp /tmp/dell_server_tuya_devices.bak "$INSTALL_DIR/config/tuya_devices.json"
    chmod 600 "$INSTALL_DIR/config/tuya_devices.json"
    print_info "Restored config/tuya_devices.json"
fi

# Step 4: Create Python virtual environment
print_info "Step 4: Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Step 5: Install Python dependencies
print_info "Step 5: Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Step 6: Create log directory and file
print_info "Step 6: Setting up logging..."
touch "$LOG_FILE"
chmod 644 "$LOG_FILE"

# Step 7: Configure environment
print_info "Step 7: Configuring environment..."
if [ ! -f "$INSTALL_DIR/config/.env" ]; then
    print_warn "Creating .env file from template..."
    cp "$INSTALL_DIR/config/.env.example" "$INSTALL_DIR/config/.env"
    print_warn "IMPORTANT: Edit $INSTALL_DIR/config/.env with your credentials!"
else
    print_info ".env file already exists, skipping..."
fi

# Step 8: Configure YAML files
print_info "Step 8: Checking configuration files..."
if [ ! -f "$INSTALL_DIR/config/mqtt_config.yaml" ]; then
    print_error "mqtt_config.yaml not found!"
    exit 1
fi

if [ ! -f "$INSTALL_DIR/config/server_config.yaml" ]; then
    print_error "server_config.yaml not found!"
    exit 1
fi

print_warn "IMPORTANT: Review and update configuration files:"
print_warn "  - $INSTALL_DIR/config/mqtt_config.yaml"
print_warn "  - $INSTALL_DIR/config/server_config.yaml"
print_warn "  - $INSTALL_DIR/config/.env"
print_warn "  - $INSTALL_DIR/device/victron-multiplus-ii/config/.env"
print_warn "  - $INSTALL_DIR/device/huawei-inverter/config/.env"
print_warn "  - $INSTALL_DIR/device/grundfos-scala1/config/.env"

# Step 9: Install systemd services
print_info "Step 9: Installing systemd services..."
cp "$INSTALL_DIR/systemd/"*.service /etc/systemd/system/
systemctl daemon-reload

# Step 10: Set permissions
print_info "Step 10: Setting permissions..."
chmod_runtime_scripts "$INSTALL_DIR"
chmod 600 "$INSTALL_DIR/config/.env"
if [ -f "$INSTALL_DIR/device/victron-multiplus-ii/config/.env" ]; then
    chmod 600 "$INSTALL_DIR/device/victron-multiplus-ii/config/.env"
fi
if [ -f "$INSTALL_DIR/device/huawei-inverter/config/.env" ]; then
    chmod 600 "$INSTALL_DIR/device/huawei-inverter/config/.env"
fi
if [ -f "$INSTALL_DIR/device/grundfos-scala1/config/.env" ]; then
    chmod 600 "$INSTALL_DIR/device/grundfos-scala1/config/.env"
fi

# Step 11: Enable and start core services
print_info "Step 11: Enabling core systemd services..."
CORE_SERVICES=(
    mqtt-boot-listener.service
    mqtt-shutdown-listener.service
    status-publisher.service
    health-monitor.service
    camera-ping-watchdog.service
)
for service in "${CORE_SERVICES[@]}"; do
    systemctl enable "$service" 2>/dev/null || true
    if systemctl start "$service" 2>/dev/null; then
        print_info "Started $service"
    else
        print_warn "Could not start $service — check configuration and journalctl"
    fi
done

# Step 12: Energy device publishers (Victron + Huawei)
print_info "Step 12: Installing energy device services..."
export ALLOW_INACTIVE_SERVICE=1
if [ -x "$INSTALL_DIR/install_victron_service.sh" ]; then
    bash "$INSTALL_DIR/install_victron_service.sh" || \
        print_warn "Victron install incomplete — edit device/victron-multiplus-ii/config/.env and re-run install_victron_service.sh"
fi
if [ -x "$INSTALL_DIR/install_huawei_service.sh" ]; then
    bash "$INSTALL_DIR/install_huawei_service.sh" || \
        print_warn "Huawei install incomplete — edit device/huawei-inverter/config/.env and re-run install_huawei_service.sh"
fi
if [ -f "$INSTALL_DIR/config/tuya_devices.json" ] && \
   [ -f "$INSTALL_DIR/device/energy-consumers/config/consumers_registry.yaml" ]; then
    if [ -x "$INSTALL_DIR/install_energy_consumers_service.sh" ]; then
        bash "$INSTALL_DIR/install_energy_consumers_service.sh" || \
            print_warn "Energy consumers install incomplete — see docs/ENERGY_CONSUMER_ADD.md"
    fi
fi
# Grundfos SCALA1: planned — install manually after on-site BLE GATT capture (see docs/GRUNDGOS_SCALA1.md)
print_info "Grundfos SCALA1: scaffolding in repo — run install_grundfos_service.sh manually when BLE is configured"
unset ALLOW_INACTIVE_SERVICE

# Step 13: Test IPMI connectivity
print_info "Step 13: Testing IPMI connectivity..."
print_warn "Skipping IPMI test. Please test manually after configuration."

# Installation complete
print_info "Installation complete!"
echo ""
print_info "Next steps:"
echo "  1. Edit configuration files:"
echo "     - $INSTALL_DIR/config/.env"
echo "     - $INSTALL_DIR/config/mqtt_config.yaml"
echo "     - $INSTALL_DIR/config/server_config.yaml"
echo "     - $INSTALL_DIR/device/victron-multiplus-ii/config/.env (if using Victron)"
echo "     - $INSTALL_DIR/device/huawei-inverter/config/.env (if using Huawei)"
echo "     - $INSTALL_DIR/device/grundfos-scala1/config/.env (if using Grundfos SCALA1)"
echo ""
echo "  2. Test IPMI connectivity:"
echo "     ipmitool -I lanplus -H <ipmi-ip> -U <username> -P <password> chassis status"
echo ""
echo "  3. Re-run device installers after editing energy config:"
echo "     sudo $INSTALL_DIR/install_victron_service.sh"
echo "     sudo $INSTALL_DIR/install_huawei_service.sh"
echo "     sudo $INSTALL_DIR/install_energy_consumers_service.sh  # Tuya smart meters"
echo "     # Planned SCALA1 (after BLE setup): sudo $INSTALL_DIR/install_grundfos_service.sh"
echo ""
echo "  4. Check service status:"
echo "     systemctl status mqtt-boot-listener.service status-publisher.service"
echo "     systemctl status victron-mqtt-publisher.service victron-solar-forecast-publisher.service"
echo "     systemctl status huawei-mqtt-publisher.service"
echo "     systemctl status energy-consumers-publisher.service"
echo "     systemctl status grundfos-scala1-mqtt-publisher.service"
echo ""
echo "  5. View logs:"
echo "     journalctl -u status-publisher.service -f"
echo "     journalctl -u victron-mqtt-publisher.service -f"
echo "     journalctl -u huawei-mqtt-publisher.service -f"
echo "     journalctl -u grundfos-scala1-mqtt-publisher.service -f"
echo ""
echo "  6. Media server (optional, v3.14.0+):"
echo "     - Set MEDIA_SERVER_* and TUYA_ACCESS_* in $INSTALL_DIR/config/.env"
echo "     - bash $INSTALL_DIR/scripts/tuya/tuya_link.sh all"
echo "     - $INSTALL_DIR/scripts/server/setup_media_server_ssh.sh"
echo "     - See $INSTALL_DIR/docs/MEDIA_SERVER.md and docs/TUYA_ACCOUNT_LINK.md"
echo ""
print_info "Installation directory: $INSTALL_DIR"
print_info "Log file: $LOG_FILE"
