#!/usr/bin/env bash
#
# Grant temporary passwordless sudo on the automation server.
#
# Modes:
#   deploy  — whitelisted install/update scripts only (lower risk)
#   agent   — full passwordless sudo for install/config (netplan, systemd, apt, …)
#
# Run ON 192.168.2.4 (one sudo password prompt):
#
#   cd ~/ServerBootShutdownManagemement
#   sudo ./scripts/server/grant_temporary_agent_sudo.sh
#
# Optional duration in minutes (default 60):
#   sudo ./scripts/server/grant_temporary_agent_sudo.sh 90
#
# Wrappers:
#   grant_temporary_deploy_sudo.sh  → deploy mode
#   grant_temporary_agent_sudo.sh   → agent mode
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=automation_sudo_common.sh
source "$SCRIPT_DIR/automation_sudo_common.sh"

MINUTES="${1:-60}"
MODE="${2:-agent}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
err() { echo -e "${RED}[ERROR]${NC} $1"; }

if [ "$EUID" -ne 0 ]; then
    err "Run as root: sudo $0 [minutes] [deploy|agent]"
    exit 1
fi

case "$MODE" in
    deploy|agent) ;;
    *)
        err "Mode must be deploy or agent (got: $MODE)"
        exit 1
        ;;
esac

EXPIRES_AT="$(automation_sudo_grant "$MODE" "$MINUTES")"

if command -v at >/dev/null 2>&1; then
    info "Temporary ${MODE} sudo granted for ${MINUTES} minutes (auto-revoke scheduled)"
else
    warn "'at' not installed — sudo will NOT auto-expire"
    warn "Revoke manually: sudo $(automation_sudo_revoke_script)"
fi

info "Mode: ${MODE}"
info "Expires: ${EXPIRES_AT}"

if [ "$MODE" = "agent" ]; then
    info "Allowed: any command via sudo -n (netplan, systemctl, apt, install scripts, …)"
else
    info "Allowed: install_*.sh, update.sh, setup_huawei_wifi.sh under repo and /opt/dell_server_management"
fi

echo ""
echo "Agent can verify (from your PC):"
echo "  ssh tinel@192.168.2.4 \"bash ~/ServerBootShutdownManagemement/scripts/server/check_deploy_sudo.sh\""
