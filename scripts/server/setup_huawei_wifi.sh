#!/usr/bin/env bash
# Configure USB WiFi on the automation server for SUN2000 inverter AP access.
# Run ON 192.168.2.4 with sudo after copying repo to ~/ServerBootShutdownManagemement.
set -euo pipefail

REPO_ROOT="${REPO_ROOT:-$HOME/ServerBootShutdownManagemement}"
if [[ "$(id -u)" -eq 0 && "$REPO_ROOT" == /root/* ]]; then
  REPO_ROOT="/home/tinel/ServerBootShutdownManagemement"
fi
ENV_FILE="$REPO_ROOT/device/huawei-inverter/config/.env"
NETPLAN_SNIPPET="/etc/netplan/60-huawei-inverter-wifi.yaml"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing $ENV_FILE — copy from config/.env.example and fill in WiFi credentials."
  exit 1
fi

# shellcheck disable=SC1090
source "$ENV_FILE"

IFACE="${HUAWEI_WIFI_IFACE:-wlxec750caf06b1}"
SSID="${HUAWEI_WIFI_SSID:?Set HUAWEI_WIFI_SSID in config/.env}"
PASSWORD="${HUAWEI_WIFI_PASSWORD:?Set HUAWEI_WIFI_PASSWORD in config/.env}"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run with sudo: sudo REPO_ROOT=$REPO_ROOT $0"
  exit 1
fi

cat > "$NETPLAN_SNIPPET" <<EOF
network:
  version: 2
  wifis:
    ${IFACE}:
      dhcp4: true
      dhcp4-overrides:
        route-metric: 600
      optional: true
      access-points:
        "${SSID}":
          password: "${PASSWORD}"
EOF

chmod 600 "$NETPLAN_SNIPPET"

if ! dpkg -s wpasupplicant >/dev/null 2>&1; then
  echo "Installing wpasupplicant (required for netplan WiFi + systemd-networkd)..."
  apt-get install -y wpasupplicant
fi

netplan generate
netplan apply

echo "Netplan applied: $NETPLAN_SNIPPET"
echo "Check link: ip -br addr show ${IFACE}"
echo "Test Modbus: ping -c1 ${HUAWEI_INVERTER_HOST:-192.168.200.1}"
