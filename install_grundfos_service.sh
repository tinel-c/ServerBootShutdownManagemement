#!/bin/bash
#
# Install or update the Grundfos SCALA1 BLE → MQTT publisher (planned feature).
# Run manually after on-site BLE GATT capture — see docs/GRUNDGOS_SCALA1.md
#   sudo ./install_grundfos_service.sh
#

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/install/common.sh
source "$REPO_ROOT/scripts/install/common.sh"
# shellcheck source=scripts/install/device_service.sh
source "$REPO_ROOT/scripts/install/device_service.sh"

require_root "$0"

install_device_publisher \
    "grundfos-scala1" \
    "water/grundfos/scala1/#" \
    grundfos-scala1-mqtt-publisher.service
