#!/usr/bin/env bash
# Check whether temporary/permanent automation sudo is active (for agents and humans).
# Exit 0 = sudo available, 1 = not available.

TEMP_DEPLOY="/etc/sudoers.d/automation-deploy-temp"
TEMP_AGENT="/etc/sudoers.d/automation-agent-temp"
PERM="/etc/sudoers.d/automation-deploy"
STAMP="/var/lib/automation-deploy-sudo-expires"
MODE_STAMP="/var/lib/automation-deploy-sudo-mode"

if [ ! -f "$TEMP_DEPLOY" ] && [ ! -f "$TEMP_AGENT" ] && [ ! -f "$PERM" ]; then
    echo "automation_sudo: not active"
    echo ""
    echo "Grant on server (pick one):"
    echo "  cd ~/ServerBootShutdownManagemement && sudo ./scripts/server/grant_temporary_agent_sudo.sh"
    echo "  cd ~/ServerBootShutdownManagemement && sudo ./scripts/server/grant_temporary_deploy_sudo.sh"
    exit 1
fi

if ! sudo -n true 2>/dev/null; then
    echo "automation_sudo: sudoers files exist but passwordless sudo is not active"
    exit 1
fi

echo "automation_sudo: active"
[ -f "$STAMP" ] && echo "expires: $(cat "$STAMP")"

if [ -f "$TEMP_AGENT" ]; then
    echo "mode: agent (full — any install/config command via sudo -n)"
elif [ -f "$TEMP_DEPLOY" ]; then
    echo "mode: deploy (whitelisted install/update scripts only)"
    echo "hint: for netplan/systemctl/apt use grant_temporary_agent_sudo.sh"
elif [ -f "$PERM" ]; then
    echo "mode: permanent deploy (whitelisted scripts only)"
fi

[ -f "$MODE_STAMP" ] && echo "granted_as: $(cat "$MODE_STAMP")"

# Backward-compatible alias for older agent checks
echo "deploy_sudo: active"

exit 0
