#!/usr/bin/env bash
# Strip Windows CRLF from shell scripts (run on Linux after copying from Windows).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

find "$REPO_ROOT/scripts/server" "$REPO_ROOT/device" -name '*.sh' -type f -print0 |
  while IFS= read -r -d '' file; do
    sed -i 's/\r$//' "$file"
    chmod +x "$file" 2>/dev/null || true
    echo "fixed: $file"
  done

echo "Done. Retry: sudo ./scripts/server/grant_temporary_agent_sudo.sh"
