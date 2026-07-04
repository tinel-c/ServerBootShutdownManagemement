#!/usr/bin/env bash
# Check whether temporary/permanent deploy sudo is active (for agents and humans).
# Exit 0 = deploy sudo available, 1 = not available.

TEMP="/etc/sudoers.d/automation-deploy-temp"
PERM="/etc/sudoers.d/automation-deploy"
STAMP="/var/lib/automation-deploy-sudo-expires"

if [ -f "$TEMP" ] || [ -f "$PERM" ]; then
    if ! sudo -n -l 2>/dev/null | grep -q NOPASSWD; then
        echo "deploy_sudo: sudoers files exist but NOPASSWD not active for this session"
        exit 1
    fi
    echo "deploy_sudo: active"
    [ -f "$STAMP" ] && echo "expires: $(cat "$STAMP")"
    [ -f "$TEMP" ] && echo "mode: temporary ($TEMP)"
    [ -f "$PERM" ] && echo "mode: permanent ($PERM)"
    exit 0
fi

echo "deploy_sudo: not active — run on server:"
echo "  cd ~/ServerBootShutdownManagemement && sudo ./scripts/server/grant_temporary_deploy_sudo.sh"
exit 1
