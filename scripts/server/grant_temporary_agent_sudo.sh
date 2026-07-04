#!/usr/bin/env bash
# Grant temporary full sudo for agent install/config sessions.
# Wrapper — see grant_temporary_automation_sudo.sh

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/grant_temporary_automation_sudo.sh" "${1:-60}" agent
