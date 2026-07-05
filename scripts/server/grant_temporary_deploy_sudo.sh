#!/usr/bin/env bash
# Grant temporary script-only deploy sudo (narrower scope).
# Wrapper — see grant_temporary_automation_sudo.sh

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
for _f in "$SCRIPT_DIR"/*.sh; do
    [ -f "$_f" ] && sed -i 's/\r$//' "$_f" 2>/dev/null || true
done
exec "$SCRIPT_DIR/grant_temporary_automation_sudo.sh" "${1:-60}" deploy
