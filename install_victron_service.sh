#!/bin/bash
#
# Install or update the Victron Modbus → MQTT publisher on the automation server.
# Run from the repository root with sudo:
#   sudo ./install_victron_service.sh
#

set -e

INSTALL_DIR="/opt/dell_server_management"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
print_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

if [ "$EUID" -ne 0 ]; then
    print_error "Run as root: sudo $0"
    exit 1
fi

if [ ! -d "$SCRIPT_DIR/device/victron-multiplus-ii" ]; then
    print_error "device/victron-multiplus-ii not found — run from repository root"
    exit 1
fi

if [ ! -d "$INSTALL_DIR" ]; then
    print_error "$INSTALL_DIR not found — run install.sh first"
    exit 1
fi

VICTRON_ENV="$INSTALL_DIR/device/victron-multiplus-ii/config/.env"
VICTRON_ENV_EXAMPLE="$SCRIPT_DIR/device/victron-multiplus-ii/config/.env.example"

print_info "Installing Victron MQTT publisher..."

mkdir -p "$INSTALL_DIR/device"
cp -r "$SCRIPT_DIR/device/victron-multiplus-ii" "$INSTALL_DIR/device/"
cp "$SCRIPT_DIR/systemd/victron-mqtt-publisher.service" /etc/systemd/system/
cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/requirements.txt"

if [ -f "$VICTRON_ENV" ]; then
    print_info "Keeping existing $VICTRON_ENV"
elif [ -f "$VICTRON_ENV_EXAMPLE" ]; then
    mkdir -p "$(dirname "$VICTRON_ENV")"
    cp "$VICTRON_ENV_EXAMPLE" "$VICTRON_ENV"
    print_warn "Created $VICTRON_ENV from template — set VICTRON_GX_HOST and Unit IDs"
fi

chmod +x "$INSTALL_DIR/device/victron-multiplus-ii/scripts/"*.py
chmod 600 "$VICTRON_ENV" 2>/dev/null || true

source "$INSTALL_DIR/venv/bin/activate"
pip install --upgrade pip
pip install -r "$INSTALL_DIR/requirements.txt"

systemctl daemon-reload
systemctl enable victron-mqtt-publisher.service
systemctl restart victron-mqtt-publisher.service

sleep 2
if systemctl is-active --quiet victron-mqtt-publisher.service; then
    print_info "victron-mqtt-publisher.service is running"
else
    print_warn "Service not active — check: journalctl -u victron-mqtt-publisher.service -n 30"
    exit 1
fi

print_info "Done. Test MQTT: mosquitto_sub -h localhost -t 'energy/victron/#' -v"
