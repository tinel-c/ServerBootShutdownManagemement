#!/bin/bash
#
# Update script for Dell & HP Server Management System
# This script updates the system while preserving all configuration files
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Installation directory
INSTALL_DIR="/opt/dell_server_management"

# Print functions
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "This script must be run as root"
    exit 1
fi

# Check if already installed
if [ ! -d "$INSTALL_DIR" ]; then
    print_error "System is not installed yet. Please run install.sh first."
    exit 1
fi

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "========================================"
echo "  Server Management System - UPDATE"
echo "========================================"
echo ""

print_info "This script will update the system while preserving your configuration."
print_warn "Press Ctrl+C to cancel, or Enter to continue..."
read

# Step 1: Stop services
print_step "Step 1: Stopping services..."
systemctl stop mqtt-boot-listener.service \
               mqtt-shutdown-listener.service \
               status-publisher.service \
               health-monitor.service \
               tapo-monitor.service || true
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

print_info "Configuration backed up to: $BACKUP_DIR"

# Step 3: Update Python scripts
print_step "Step 3: Updating Python scripts..."
cp -r "$SCRIPT_DIR/scripts/"* "$INSTALL_DIR/scripts/"
print_info "✓ Python scripts updated"

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

print_info "Configuration restored successfully!"

# Step 7: Set permissions
print_step "Step 7: Setting permissions..."
chmod +x "$INSTALL_DIR/scripts/boot/"*.py
chmod +x "$INSTALL_DIR/scripts/shutdown/"*.py
chmod +x "$INSTALL_DIR/scripts/status/"*.py
chmod +x "$INSTALL_DIR/"*.sh
chmod 600 "$INSTALL_DIR/config/.env"
print_info "✓ Permissions set"

# Step 8: Restart services
print_step "Step 8: Restarting services..."
systemctl restart mqtt-boot-listener.service
systemctl restart mqtt-shutdown-listener.service
systemctl restart status-publisher.service
systemctl restart health-monitor.service || true
systemctl restart tapo-monitor.service || true
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
echo ""
print_info "View logs with:"
echo "  journalctl -u status-publisher.service -f"
echo ""
