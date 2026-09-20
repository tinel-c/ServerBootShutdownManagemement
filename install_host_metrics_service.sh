#!/bin/bash
#
# Install / update the automation-host metrics MQTT publisher.
#   sudo ./install_host_metrics_service.sh
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Prefer production install path when present
INSTALL_DIR="${INSTALL_DIR:-/opt/dell_server_management}"
if [[ ! -d "$INSTALL_DIR/scripts/status" ]]; then
  INSTALL_DIR="$REPO_ROOT"
fi

UNIT_SRC="$REPO_ROOT/systemd/host-metrics-publisher.service"
UNIT_DST="/etc/systemd/system/host-metrics-publisher.service"

[[ "$(id -u)" -eq 0 ]] || { echo "Run as root (sudo)" >&2; exit 1; }
[[ -f "$UNIT_SRC" ]] || { echo "Missing $UNIT_SRC" >&2; exit 1; }
[[ -f "$INSTALL_DIR/scripts/status/host_metrics_publisher.py" ]] || {
  echo "Missing publisher script under $INSTALL_DIR" >&2
  exit 1
}

cp -f "$UNIT_SRC" "$UNIT_DST"
# Point ExecStart at the active install tree
sed -i "s|/opt/dell_server_management|${INSTALL_DIR}|g" "$UNIT_DST"

systemctl daemon-reload
systemctl enable host-metrics-publisher.service
systemctl restart host-metrics-publisher.service
systemctl --no-pager --full status host-metrics-publisher.service | head -20

echo "OK — host-metrics-publisher.service installed"
echo "  Topics: system/automation/status (+ cpu_pct, memory_pct, disk_*_pct, load1)"
