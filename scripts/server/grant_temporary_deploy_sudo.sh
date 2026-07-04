#!/usr/bin/env bash
#
# Grant temporary passwordless sudo for deploy scripts on the automation server.
# Run ON 192.168.2.4 (enter your sudo password once):
#
#   cd ~/ServerBootShutdownManagemement
#   sudo ./scripts/server/grant_temporary_deploy_sudo.sh
#
# Optional duration in minutes (default 60):
#   sudo ./scripts/server/grant_temporary_deploy_sudo.sh 90
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SRC="$REPO_ROOT/scripts/server/sudoers.d-automation-deploy-temp"
DEST="/etc/sudoers.d/automation-deploy-temp"
STAMP_FILE="/var/lib/automation-deploy-sudo-expires"
REVOKE_SCRIPT="$REPO_ROOT/scripts/server/revoke_deploy_sudo.sh"
MINUTES="${1:-60}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
err() { echo -e "${RED}[ERROR]${NC} $1"; }

if [ "$EUID" -ne 0 ]; then
    err "Run as root: sudo $0 [minutes]"
    exit 1
fi

if [ ! -f "$SRC" ]; then
    err "Missing $SRC — sync repo to ~/ServerBootShutdownManagemement first"
    exit 1
fi

if ! [[ "$MINUTES" =~ ^[0-9]+$ ]] || [ "$MINUTES" -lt 1 ]; then
    err "Minutes must be a positive integer"
    exit 1
fi

chmod +x "$REVOKE_SCRIPT" 2>/dev/null || true

cp "$SRC" "$DEST"
sed -i 's/\r$//' "$DEST"
chmod 440 "$DEST"
visudo -cf "$DEST"

EXPIRES_AT="$(date -d "+${MINUTES} minutes" -Iseconds 2>/dev/null || date -v+${MINUTES}M -Iseconds 2>/dev/null || echo "in ${MINUTES} minutes")"
echo "$EXPIRES_AT" > "$STAMP_FILE"
chmod 644 "$STAMP_FILE"

if command -v at >/dev/null 2>&1; then
    echo "$REVOKE_SCRIPT" | at "now + ${MINUTES} minutes" 2>/dev/null
    info "Temporary deploy sudo granted for ${MINUTES} minutes (auto-revoke scheduled)"
else
    warn "'at' not installed — sudo will NOT auto-expire"
    warn "Revoke manually: sudo $REVOKE_SCRIPT"
fi

info "Expires: $EXPIRES_AT"
info "Allowed: install_*.sh, update.sh under repo and /opt/dell_server_management"
echo ""
echo "Agent can now run (from your PC):"
echo "  ssh tinel@192.168.2.4 'sudo -n true && echo deploy_sudo_ok'"
echo "  .\\scripts\\server\\deploy_victron_remote.ps1"
