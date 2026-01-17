#!/bin/bash
#
# Installation script for Dell & HP Server Management System
# This script installs all components and configures the system
# Supports Dell T310 (IPMI) and HP DL360p (iLO) servers
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Installation directory
INSTALL_DIR="/opt/dell_server_management"
LOG_DIR="/var/log"
LOG_FILE="${LOG_DIR}/dell_server_management.log"

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

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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

# Step 9: Install systemd services
print_info "Step 9: Installing systemd services..."
cp "$INSTALL_DIR/systemd/"*.service /etc/systemd/system/
systemctl daemon-reload

# Step 10: Set permissions
print_info "Step 10: Setting permissions..."
chmod +x "$INSTALL_DIR/scripts/boot/"*.py
chmod +x "$INSTALL_DIR/scripts/shutdown/"*.py
chmod +x "$INSTALL_DIR/scripts/status/"*.py
chmod 600 "$INSTALL_DIR/config/.env"

# Step 11: Test IPMI connectivity
print_info "Step 11: Testing IPMI connectivity..."
print_warn "Skipping IPMI test. Please test manually after configuration."

# Installation complete
print_info "Installation complete!"
echo ""
print_info "Next steps:"
echo "  1. Edit configuration files:"
echo "     - $INSTALL_DIR/config/.env"
echo "     - $INSTALL_DIR/config/mqtt_config.yaml"
echo "     - $INSTALL_DIR/config/server_config.yaml"
echo ""
echo "  2. Test IPMI connectivity:"
echo "     ipmitool -I lanplus -H <ipmi-ip> -U <username> -P <password> chassis status"
echo ""
echo "  3. Enable and start services:"
echo "     systemctl enable mqtt-boot-listener.service"
echo "     systemctl enable mqtt-shutdown-listener.service"
echo "     systemctl enable status-publisher.service"
echo "     systemctl enable health-monitor.service"
echo "     systemctl start mqtt-boot-listener.service"
echo "     systemctl start mqtt-shutdown-listener.service"
echo "     systemctl start status-publisher.service"
echo "     systemctl start health-monitor.service"
echo ""
echo "  4. Check service status:"
echo "     systemctl status mqtt-boot-listener.service"
echo "     systemctl status mqtt-shutdown-listener.service"
echo "     systemctl status status-publisher.service"
echo "     systemctl status health-monitor.service"
echo ""
echo "  5. View logs:"
echo "     journalctl -u mqtt-boot-listener.service -f"
echo "     journalctl -u mqtt-shutdown-listener.service -f"
echo "     journalctl -u status-publisher.service -f"
echo "     journalctl -u health-monitor.service -f"
echo ""
print_info "Installation directory: $INSTALL_DIR"
print_info "Log file: $LOG_FILE"
