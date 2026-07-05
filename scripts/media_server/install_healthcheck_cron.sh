#!/usr/bin/env bash
# Install Healthchecks.io ping cron on the media server (192.168.2.185).
# Run ON the media server as the user that should own the cron job.
set -euo pipefail

PING_URL="${1:-${MEDIA_SERVER_HEALTHCHECK_PING_URL:-}}"

if [ -z "$PING_URL" ]; then
    echo "Usage: $0 <https://hc-ping.com/your-uuid>"
    echo "   or: MEDIA_SERVER_HEALTHCHECK_PING_URL=... $0"
    exit 1
fi

CRON_LINE="* * * * * curl -fsS -m 10 --retry 5 -o /dev/null ${PING_URL}"

MARKER="# media-server-healthchecks-io"
TMP="$(mktemp)"
(crontab -l 2>/dev/null | grep -v "$MARKER" || true) > "$TMP"
echo "$CRON_LINE $MARKER" >> "$TMP"
crontab "$TMP"
rm -f "$TMP"

echo "Installed cron job (every minute):"
crontab -l | grep "$MARKER" || true
echo ""
echo "Test ping now:"
curl -fsS -m 10 --retry 2 -o /dev/null "$PING_URL" && echo "Ping OK"
