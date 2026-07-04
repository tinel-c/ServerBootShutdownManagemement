#!/usr/bin/env bash
# Sync Huawei integration to automation server and install systemd service.
set -euo pipefail

HOST_ALIAS="${1:-tinel@192.168.2.4}"
REPO="~/ServerBootShutdownManagemement"

scp -r device/huawei-inverter "${HOST_ALIAS}:${REPO}/device/"
scp systemd/huawei-mqtt-publisher.service install_huawei_service.sh requirements.txt \
    "${HOST_ALIAS}:${REPO}/"
scp systemd/huawei-mqtt-publisher.service "${HOST_ALIAS}:${REPO}/systemd/"

ssh "${HOST_ALIAS}" "chmod +x ${REPO}/install_huawei_service.sh ${REPO}/device/huawei-inverter/scripts/*.py"

echo "Installing huawei-mqtt-publisher.service (requires agent sudo on server)..."
ssh "${HOST_ALIAS}" "cd ${REPO} && sudo ./install_huawei_service.sh"

echo "Verify:"
echo "  ssh ${HOST_ALIAS} 'systemctl status huawei-mqtt-publisher.service'"
echo "  ssh ${HOST_ALIAS} \"mosquitto_sub -h localhost -t 'energy/huawei/status' -C1 -v\""
