#!/usr/bin/env bash
#
# Install passwordless sudo for deploy scripts (one-time, interactive).
# Run ON the automation server after SSH key login works:
#   ssh serverside
#   cd ~/ServerBootShutdownManagemement
#   sudo ./scripts/server/install_deploy_sudoers.sh
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SRC="$REPO_ROOT/scripts/server/sudoers.d-automation-deploy"
DEST="/etc/sudoers.d/automation-deploy"

if [ "$EUID" -ne 0 ]; then
    echo "Run as root: sudo $0"
    exit 1
fi

if [ ! -f "$SRC" ]; then
    echo "Missing $SRC"
    exit 1
fi

cp "$SRC" "$DEST"
sed -i 's/\r$//' "$DEST"
chmod 440 "$DEST"
visudo -cf "$DEST"
echo "Installed $DEST — tinel can run install_victron_service.sh and update.sh without a sudo password."
