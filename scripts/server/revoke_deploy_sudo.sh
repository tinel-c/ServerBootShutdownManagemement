#!/usr/bin/env bash
#
# Revoke passwordless automation sudo (temporary deploy, temporary agent, permanent deploy).
# Run ON the server: sudo ./scripts/server/revoke_deploy_sudo.sh
#

set -euo pipefail

TEMP_DEPLOY="/etc/sudoers.d/automation-deploy-temp"
TEMP_AGENT="/etc/sudoers.d/automation-agent-temp"
PERM="/etc/sudoers.d/automation-deploy"
STAMP="/var/lib/automation-deploy-sudo-expires"
MODE_STAMP="/var/lib/automation-deploy-sudo-mode"

removed=0
for f in "$TEMP_DEPLOY" "$TEMP_AGENT" "$PERM"; do
    if [ -f "$f" ]; then
        rm -f "$f"
        echo "Removed $f"
        removed=1
    fi
done

rm -f "$STAMP" "$MODE_STAMP" 2>/dev/null || true

for job in $(atq 2>/dev/null | awk '{print $1}'); do
    atrm "$job" 2>/dev/null || true
done

if [ "$removed" -eq 0 ]; then
    echo "No automation sudoers files were installed"
else
    visudo -c
    echo "Automation sudo revoked"
fi
