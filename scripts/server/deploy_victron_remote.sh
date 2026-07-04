#!/usr/bin/env bash
# Sync Victron integration to the automation server and install the systemd service.
set -euo pipefail

HOST_ALIAS=serverside
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

echo "Syncing to ${HOST_ALIAS}:~/ServerBootShutdownManagemement ..."
scp -r device/victron-multiplus-ii "${HOST_ALIAS}:~/ServerBootShutdownManagemement/device/"
scp systemd/victron-mqtt-publisher.service "${HOST_ALIAS}:~/ServerBootShutdownManagemement/systemd/"
scp requirements.txt install_victron_service.sh "${HOST_ALIAS}:~/ServerBootShutdownManagemement/"
scp scripts/server/sudoers.d-automation-deploy scripts/server/install_deploy_sudoers.sh \
    "${HOST_ALIAS}:~/ServerBootShutdownManagemement/scripts/server/"

ssh "${HOST_ALIAS}" "chmod +x ~/ServerBootShutdownManagemement/install_victron_service.sh ~/ServerBootShutdownManagemement/scripts/server/install_deploy_sudoers.sh ~/ServerBootShutdownManagemement/device/victron-multiplus-ii/scripts/*.py"

echo "Installing victron-mqtt-publisher.service (sudo may prompt once)..."
ssh -t "${HOST_ALIAS}" "cd ~/ServerBootShutdownManagemement && sudo ./install_victron_service.sh"

echo ""
echo "Verify: ssh ${HOST_ALIAS} 'systemctl status victron-mqtt-publisher.service'"
