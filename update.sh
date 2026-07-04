#!/bin/bash
#
# Update script for Dell & HP Server Management System
# This script updates the system while preserving all configuration files
#

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/install/common.sh
source "$SCRIPT_DIR/scripts/install/common.sh"

echo ""
echo "========================================"
echo "  Server Management System - UPDATE"
echo "========================================"
echo ""

require_root "$0"
require_install_dir

print_info "This script will update the system while preserving your configuration."
print_warn "Press Ctrl+C to cancel, or Enter to continue..."
read

# Step 1: Stop services
print_step "Step 1: Stopping services..."
systemctl stop mqtt-boot-listener.service \
               mqtt-shutdown-listener.service \
               status-publisher.service \
               health-monitor.service \
               tapo-monitor.service \
               victron-mqtt-publisher.service \
               victron-solar-forecast-publisher.service \
               huawei-mqtt-publisher.service \
               grundfos-scala1-mqtt-publisher.service || true
sleep 1
print_info "Services stopped."

# Step 2: Backup configuration files
print_step "Step 2: Backing up configuration files..."
BACKUP_DIR="/tmp/server_management_config_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

if [ -f "$INSTALL_DIR/config/.env" ]; then
    cp "$INSTALL_DIR/config/.env" "$BACKUP_DIR/.env"
    print_info "✓ Backed up .env"
else
    print_warn "No existing .env file found"
fi

if [ -f "$INSTALL_DIR/config/mqtt_config.yaml" ]; then
    cp "$INSTALL_DIR/config/mqtt_config.yaml" "$BACKUP_DIR/mqtt_config.yaml"
    print_info "✓ Backed up mqtt_config.yaml"
fi

if [ -f "$INSTALL_DIR/config/server_config.yaml" ]; then
    cp "$INSTALL_DIR/config/server_config.yaml" "$BACKUP_DIR/server_config.yaml"
    print_info "✓ Backed up server_config.yaml"
fi

if [ -f "$INSTALL_DIR/device/victron-multiplus-ii/config/.env" ]; then
    mkdir -p "$BACKUP_DIR/victron"
    cp "$INSTALL_DIR/device/victron-multiplus-ii/config/.env" "$BACKUP_DIR/victron/.env"
    print_info "✓ Backed up Victron .env"
fi

if [ -f "$INSTALL_DIR/device/huawei-inverter/config/.env" ]; then
    mkdir -p "$BACKUP_DIR/huawei"
    cp "$INSTALL_DIR/device/huawei-inverter/config/.env" "$BACKUP_DIR/huawei/.env"
    print_info "✓ Backed up Huawei .env"
fi

if [ -f "$INSTALL_DIR/device/grundfos-scala1/config/.env" ]; then
    mkdir -p "$BACKUP_DIR/grundfos"
    cp "$INSTALL_DIR/device/grundfos-scala1/config/.env" "$BACKUP_DIR/grundfos/.env"
    print_info "✓ Backed up Grundfos SCALA1 .env"
fi

print_info "Configuration backed up to: $BACKUP_DIR"

# Step 3: Update Python scripts
print_step "Step 3: Updating Python scripts..."
cp -r "$SCRIPT_DIR/scripts/"* "$INSTALL_DIR/scripts/"
print_info "✓ Python scripts updated"

# Step 3b: Update device integrations (Victron, Huawei, …)
print_step "Step 3b: Updating device integrations..."
mkdir -p "$INSTALL_DIR/device"
if [ -d "$SCRIPT_DIR/device/victron-multiplus-ii" ]; then
    cp -r "$SCRIPT_DIR/device/victron-multiplus-ii" "$INSTALL_DIR/device/"
    print_info "✓ Victron MultiPlus-II integration updated"
fi
if [ -d "$SCRIPT_DIR/device/huawei-inverter" ]; then
    cp -r "$SCRIPT_DIR/device/huawei-inverter" "$INSTALL_DIR/device/"
    print_info "✓ Huawei SUN2000 integration updated"
fi
if [ -d "$SCRIPT_DIR/device/grundfos-scala1" ]; then
    cp -r "$SCRIPT_DIR/device/grundfos-scala1" "$INSTALL_DIR/device/"
    print_info "✓ Grundfos SCALA1 integration updated"
fi
cp "$SCRIPT_DIR/install_victron_service.sh" "$SCRIPT_DIR/install_huawei_service.sh" "$SCRIPT_DIR/install_grundfos_service.sh" "$INSTALL_DIR/" 2>/dev/null || true
cp -r "$SCRIPT_DIR/scripts/install" "$INSTALL_DIR/scripts/" 2>/dev/null || true

# Step 4: Update systemd service files
print_step "Step 4: Updating systemd services..."
cp "$SCRIPT_DIR/systemd/"*.service /etc/systemd/system/
systemctl daemon-reload
print_info "✓ Systemd services updated"

# Step 5: Update dependencies
print_step "Step 5: Updating Python dependencies..."
source "$INSTALL_DIR/venv/bin/activate"
pip install --upgrade pip
pip install -r "$SCRIPT_DIR/requirements.txt" --upgrade
print_info "✓ Dependencies updated"

# Step 6: Restore configuration files
print_step "Step 6: Restoring configuration files..."

if [ -f "$BACKUP_DIR/.env" ]; then
    cp "$BACKUP_DIR/.env" "$INSTALL_DIR/config/.env"
    chmod 600 "$INSTALL_DIR/config/.env"
    print_info "✓ Restored .env"
fi

if [ -f "$BACKUP_DIR/mqtt_config.yaml" ]; then
    # Check if there are new fields in the template
    if [ -f "$SCRIPT_DIR/config/mqtt_config.yaml" ]; then
        print_warn "New mqtt_config.yaml template available. Your existing config has been preserved."
        print_warn "Compare with: $SCRIPT_DIR/config/mqtt_config.yaml"
    fi
    cp "$BACKUP_DIR/mqtt_config.yaml" "$INSTALL_DIR/config/mqtt_config.yaml"
    print_info "✓ Restored mqtt_config.yaml"
fi

if [ -f "$BACKUP_DIR/server_config.yaml" ]; then
    # Check if there are new fields in the template
    if [ -f "$SCRIPT_DIR/config/server_config.yaml" ]; then
        print_warn "New server_config.yaml template available. Your existing config has been preserved."
        print_warn "Compare with: $SCRIPT_DIR/config/server_config.yaml"
    fi
    cp "$BACKUP_DIR/server_config.yaml" "$INSTALL_DIR/config/server_config.yaml"
    print_info "✓ Restored server_config.yaml"
fi

if [ -f "$BACKUP_DIR/victron/.env" ]; then
    mkdir -p "$INSTALL_DIR/device/victron-multiplus-ii/config"
    cp "$BACKUP_DIR/victron/.env" "$INSTALL_DIR/device/victron-multiplus-ii/config/.env"
    chmod 600 "$INSTALL_DIR/device/victron-multiplus-ii/config/.env"
    print_info "✓ Restored Victron .env"
elif [ ! -f "$INSTALL_DIR/device/victron-multiplus-ii/config/.env" ]; then
    if [ -f "$INSTALL_DIR/device/victron-multiplus-ii/config/.env.example" ]; then
        mkdir -p "$INSTALL_DIR/device/victron-multiplus-ii/config"
        cp "$INSTALL_DIR/device/victron-multiplus-ii/config/.env.example" \
           "$INSTALL_DIR/device/victron-multiplus-ii/config/.env"
        print_warn "Created Victron .env from template — edit Cerbo GX settings before starting service"
    fi
fi

if [ -f "$BACKUP_DIR/huawei/.env" ]; then
    mkdir -p "$INSTALL_DIR/device/huawei-inverter/config"
    cp "$BACKUP_DIR/huawei/.env" "$INSTALL_DIR/device/huawei-inverter/config/.env"
    chmod 600 "$INSTALL_DIR/device/huawei-inverter/config/.env"
    print_info "✓ Restored Huawei .env"
elif [ ! -f "$INSTALL_DIR/device/huawei-inverter/config/.env" ]; then
    if [ -f "$INSTALL_DIR/device/huawei-inverter/config/.env.example" ]; then
        mkdir -p "$INSTALL_DIR/device/huawei-inverter/config"
        cp "$INSTALL_DIR/device/huawei-inverter/config/.env.example" \
           "$INSTALL_DIR/device/huawei-inverter/config/.env"
        print_warn "Created Huawei .env from template — edit inverter/WiFi settings before starting service"
    fi
fi

if [ -f "$BACKUP_DIR/grundfos/.env" ]; then
    mkdir -p "$INSTALL_DIR/device/grundfos-scala1/config"
    cp "$BACKUP_DIR/grundfos/.env" "$INSTALL_DIR/device/grundfos-scala1/config/.env"
    chmod 600 "$INSTALL_DIR/device/grundfos-scala1/config/.env"
    print_info "✓ Restored Grundfos SCALA1 .env"
elif [ ! -f "$INSTALL_DIR/device/grundfos-scala1/config/.env" ]; then
    if [ -f "$INSTALL_DIR/device/grundfos-scala1/config/.env.example" ]; then
        mkdir -p "$INSTALL_DIR/device/grundfos-scala1/config"
        cp "$INSTALL_DIR/device/grundfos-scala1/config/.env.example" \
           "$INSTALL_DIR/device/grundfos-scala1/config/.env"
        print_warn "Created Grundfos .env from template — edit SCALA1_BLE_ADDRESS before starting service"
    fi
fi

print_info "Configuration restored successfully!"

# Step 7: Set permissions
print_step "Step 7: Setting permissions..."
chmod +x "$INSTALL_DIR/scripts/boot/"*.py
chmod +x "$INSTALL_DIR/scripts/shutdown/"*.py
chmod +x "$INSTALL_DIR/scripts/status/"*.py
if [ -d "$INSTALL_DIR/device/victron-multiplus-ii/scripts" ]; then
    chmod +x "$INSTALL_DIR/device/victron-multiplus-ii/scripts/"*.py
fi
if [ -d "$INSTALL_DIR/device/huawei-inverter/scripts" ]; then
    chmod +x "$INSTALL_DIR/device/huawei-inverter/scripts/"*.py
fi
if [ -d "$INSTALL_DIR/device/grundfos-scala1/scripts" ]; then
    chmod +x "$INSTALL_DIR/device/grundfos-scala1/scripts/"*.py
fi
chmod +x "$INSTALL_DIR/install_"*.sh 2>/dev/null || true
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
print_info "✓ Permissions set"

# Step 8: Restart services
print_step "Step 8: Restarting services..."
systemctl restart mqtt-boot-listener.service
systemctl restart mqtt-shutdown-listener.service
systemctl restart status-publisher.service
systemctl restart health-monitor.service || true
systemctl restart tapo-monitor.service || true
if [ -f "$INSTALL_DIR/device/victron-multiplus-ii/config/.env" ]; then
    systemctl enable victron-mqtt-publisher.service || true
    systemctl enable victron-solar-forecast-publisher.service || true
    systemctl restart victron-mqtt-publisher.service || true
    systemctl restart victron-solar-forecast-publisher.service || true
else
    print_warn "Victron .env missing — victron services not started"
fi
if [ -f "$INSTALL_DIR/device/huawei-inverter/config/.env" ]; then
    systemctl enable huawei-mqtt-publisher.service || true
    systemctl restart huawei-mqtt-publisher.service || true
else
    print_warn "Huawei .env missing — huawei-mqtt-publisher.service not started"
fi
if [ -f "$INSTALL_DIR/device/grundfos-scala1/config/.env" ]; then
    systemctl enable grundfos-scala1-mqtt-publisher.service || true
    systemctl restart grundfos-scala1-mqtt-publisher.service || true
else
    print_warn "Grundfos .env missing — grundfos-scala1-mqtt-publisher.service not started"
fi
print_info "✓ Services restarted"

# Update complete
echo ""
echo "========================================"
print_info "✓ UPDATE COMPLETE!"
echo "========================================"
echo ""
print_info "Configuration backup location: $BACKUP_DIR"
print_info "Your existing configuration has been preserved."
echo ""
print_info "Check service status with:"
echo "  systemctl status mqtt-boot-listener.service"
echo "  systemctl status mqtt-shutdown-listener.service"
echo "  systemctl status status-publisher.service"
echo "  systemctl status health-monitor.service"
echo "  systemctl status tapo-monitor.service"
echo "  systemctl status victron-mqtt-publisher.service"
echo "  systemctl status victron-solar-forecast-publisher.service"
echo "  systemctl status huawei-mqtt-publisher.service"
echo "  systemctl status grundfos-scala1-mqtt-publisher.service"
echo ""
print_info "View logs with:"
echo "  journalctl -u status-publisher.service -f"
echo "  journalctl -u victron-mqtt-publisher.service -f"
echo "  journalctl -u huawei-mqtt-publisher.service -f"
echo "  journalctl -u grundfos-scala1-mqtt-publisher.service -f"
echo ""
