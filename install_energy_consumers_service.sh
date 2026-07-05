#!/bin/bash
#
# Install or update the Tuya energy consumers MQTT publisher.
#   sudo ./install_energy_consumers_service.sh
#

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/install/common.sh
source "$REPO_ROOT/scripts/install/common.sh"
# shellcheck source=scripts/install/device_service.sh
source "$REPO_ROOT/scripts/install/device_service.sh"

require_root "$0"

install_device_publisher \
    "energy-consumers" \
    "energy/consumers/#" \
    energy-consumers-publisher.service
