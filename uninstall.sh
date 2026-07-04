#!/bin/bash
#
# Uninstallation script for Dell & HP Server Management System
# This script removes all installed components
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Installation directory
INSTALL_DIR="/opt/dell_server_management"
LOG_FILE="/var/log/dell_server_management.log"

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

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "This script must be run as root"
    exit 1
fi

print_warn "This will uninstall the Dell & HP Server Management System"
print_warn "Installation directory: $INSTALL_DIR"
echo ""

# Ask for confirmation
read -p "Are you sure you want to continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    print_info "Uninstallation cancelled"
    exit 0
fi

echo ""
print_info "Starting uninstallation..."

# Step 1: Stop and disable systemd services
print_info "Step 1: Stopping and disabling systemd services..."

services=(
    "mqtt-boot-listener.service"
    "mqtt-shutdown-listener.service"
    "status-publisher.service"
    "health-monitor.service"
    "tapo-monitor.service"
    "victron-mqtt-publisher.service"
    "victron-solar-forecast-publisher.service"
)

for service in "${services[@]}"; do
    if systemctl is-active --quiet "$service"; then
        print_info "Stopping $service..."
        systemctl stop "$service" 2>/dev/null || true
    fi
    
    if systemctl is-enabled --quiet "$service" 2>/dev/null; then
        print_info "Disabling $service..."
        systemctl disable "$service" 2>/dev/null || true
    fi
done

# Step 2: Remove systemd service files
print_info "Step 2: Removing systemd service files..."
for service in "${services[@]}"; do
    if [ -f "/etc/systemd/system/$service" ]; then
        rm -f "/etc/systemd/system/$service"
        print_info "Removed /etc/systemd/system/$service"
    fi
done

systemctl daemon-reload
print_info "Systemd daemon reloaded"

# Step 3: Remove installation directory
print_info "Step 3: Removing installation directory..."
if [ -d "$INSTALL_DIR" ]; then
    # Create backup before removing
    backup_dir="${INSTALL_DIR}.backup.$(date +%Y%m%d_%H%M%S)"
    print_info "Creating backup at: $backup_dir"
    cp -r "$INSTALL_DIR" "$backup_dir"
    
    # Remove installation directory
    rm -rf "$INSTALL_DIR"
    print_info "Removed $INSTALL_DIR"
    print_info "Backup saved at: $backup_dir"
else
    print_warn "Installation directory not found: $INSTALL_DIR"
fi

# Step 4: Remove log file
print_info "Step 4: Removing log file..."
if [ -f "$LOG_FILE" ]; then
    # Backup log file
    log_backup="${LOG_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$LOG_FILE" "$log_backup"
    rm -f "$LOG_FILE"
    print_info "Removed $LOG_FILE"
    print_info "Log backup saved at: $log_backup"
else
    print_warn "Log file not found: $LOG_FILE"
fi

# Step 5: Optional - Remove Python packages
print_info "Step 5: Python packages..."
print_warn "Python packages (paho-mqtt, python-hpilo, etc.) were NOT removed"
print_warn "To remove them manually, run:"
echo "  pip3 uninstall paho-mqtt pyyaml python-dotenv python-hpilo proxmoxer"

# Step 6: Optional - Remove system packages
print_info "Step 6: System packages..."
print_warn "System packages (ipmitool, wakeonlan) were NOT removed"
print_warn "To remove them manually, run:"
echo "  apt-get remove ipmitool wakeonlan"

echo ""
print_info "Uninstallation complete!"
echo ""
print_info "Summary:"
echo "  - Systemd services stopped and disabled"
echo "  - Service files removed from /etc/systemd/system/"
echo "  - Installation directory backed up and removed"
echo "  - Log file backed up and removed"
echo ""
print_info "Backups created:"
if [ -d "$backup_dir" ]; then
    echo "  - Configuration backup: $backup_dir"
fi
if [ -f "$log_backup" ]; then
    echo "  - Log backup: $log_backup"
fi
echo ""
print_warn "Note: Python and system packages were not removed automatically"
print_warn "Remove them manually if they are no longer needed"
