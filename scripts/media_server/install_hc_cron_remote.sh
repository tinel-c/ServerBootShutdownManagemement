#!/usr/bin/env bash
set -euo pipefail
PING_URL="${1:-https://hc-ping.com/cf1fd460-cd85-4290-bfbf-96d046f9c359}"
KEY="$HOME/.ssh/media_server_192_168_2_185_ed25519"
HOST="tinel@192.168.2.185"
ssh -i "$KEY" -o BatchMode=yes "$HOST" "PING='$PING_URL'; MARKER='# media-server-healthchecks-io'; (crontab -l 2>/dev/null | grep -v media-server-healthchecks-io; echo \"* * * * * curl -fsS -m 10 --retry 5 -o /dev/null \$PING \$MARKER\") | crontab -; crontab -l | grep media-server; curl -fsS -m 10 -o /dev/null \"\$PING\" && echo PING_OK"
