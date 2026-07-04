#!/bin/bash
#
# Install or update the Victron Modbus → MQTT publisher on the automation server.
# Run from the repository root with sudo:
#   sudo ./install_victron_service.sh
#

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/install/common.sh
source "$REPO_ROOT/scripts/install/common.sh"
# shellcheck source=scripts/install/device_service.sh
source "$REPO_ROOT/scripts/install/device_service.sh"

require_root "$0"

install_device_publisher \
    "victron-multiplus-ii" \
    "energy/victron/#" \
    victron-mqtt-publisher.service \
    victron-solar-forecast-publisher.service
