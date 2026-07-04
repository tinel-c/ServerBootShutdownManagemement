#!/usr/bin/env bash
#
# Revoke passwordless deploy sudo (temporary and permanent).
# Run ON the server: sudo ./scripts/server/revoke_deploy_sudo.sh
#

set -euo pipefail

TEMP="/etc/sudoers.d/automation-deploy-temp"
PERM="/etc/sudoers.d/automation-deploy"
STAMP="/var/lib/automation-deploy-sudo-expires"

removed=0
for f in "$TEMP" "$PERM"; do
    if [ -f "$f" ]; then
        rm -f "$f"
        echo "Removed $f"
        removed=1
    fi
done

rm -f "$STAMP" 2>/dev/null || true

for job in $(atq 2>/dev/null | awk '{print $1}'); do
    atrm "$job" 2>/dev/null || true
done

if [ "$removed" -eq 0 ]; then
    echo "No deploy sudoers files were installed"
else
    visudo -c
    echo "Deploy sudo revoked"
fi
