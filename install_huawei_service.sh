#!/bin/bash
#
# Install or update the Huawei SUN2000 Modbus → MQTT publisher on the automation server.
# Run from the repository root with sudo:
#   sudo ./install_huawei_service.sh
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

if [ ! -d "$SCRIPT_DIR/device/huawei-inverter" ]; then
    print_error "device/huawei-inverter not found — run from repository root"
    exit 1
fi

if [ ! -d "$INSTALL_DIR" ]; then
    print_error "$INSTALL_DIR not found — run install.sh first"
    exit 1
fi

HUAWEI_ENV="$INSTALL_DIR/device/huawei-inverter/config/.env"
HUAWEI_ENV_EXAMPLE="$SCRIPT_DIR/device/huawei-inverter/config/.env.example"

print_info "Installing Huawei MQTT publisher..."

mkdir -p "$INSTALL_DIR/device"
cp -r "$SCRIPT_DIR/device/huawei-inverter" "$INSTALL_DIR/device/"
cp "$SCRIPT_DIR/systemd/huawei-mqtt-publisher.service" /etc/systemd/system/
cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/requirements.txt"

if [ -f "$HUAWEI_ENV" ]; then
    print_info "Keeping existing $HUAWEI_ENV"
elif [ -f "$HUAWEI_ENV_EXAMPLE" ]; then
    mkdir -p "$(dirname "$HUAWEI_ENV")"
    cp "$HUAWEI_ENV_EXAMPLE" "$HUAWEI_ENV"
    print_warn "Created $HUAWEI_ENV from template — set HUAWEI_INVERTER_HOST and WiFi settings"
fi

chmod +x "$INSTALL_DIR/device/huawei-inverter/scripts/"*.py
chmod 600 "$HUAWEI_ENV" 2>/dev/null || true

source "$INSTALL_DIR/venv/bin/activate"
pip install --upgrade pip
pip install -r "$INSTALL_DIR/requirements.txt"

systemctl daemon-reload
systemctl enable huawei-mqtt-publisher.service
systemctl restart huawei-mqtt-publisher.service

sleep 2
if systemctl is-active --quiet huawei-mqtt-publisher.service; then
    print_info "huawei-mqtt-publisher.service is running"
else
    print_warn "huawei-mqtt-publisher not active — check: journalctl -u huawei-mqtt-publisher.service -n 30"
    exit 1
fi

print_info "Done. Test MQTT: mosquitto_sub -h localhost -t 'energy/huawei/#' -v"
