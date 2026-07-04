#!/bin/bash
#
# Install or update the Huawei SUN2000 Modbus → MQTT publisher on the automation server.
# Run from the repository root with sudo:
#   sudo ./install_huawei_service.sh
#

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/install/common.sh
source "$REPO_ROOT/scripts/install/common.sh"
# shellcheck source=scripts/install/device_service.sh
source "$REPO_ROOT/scripts/install/device_service.sh"

require_root "$0"

install_device_publisher \
    "huawei-inverter" \
    "energy/huawei/#" \
    huawei-mqtt-publisher.service
