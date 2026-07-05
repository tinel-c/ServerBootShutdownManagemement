#!/usr/bin/env bash
# Run on automation server: healthcheck API, SSH key gen, service restart
set -euo pipefail

OPT=/opt/dell_server_management
ENV="$OPT/config/.env"

set_env() {
    local key="$1" val="$2"
    if sudo grep -q "^${key}=" "$ENV" 2>/dev/null; then
        sudo sed -i "s|^${key}=.*|${key}=${val}|" "$ENV"
    else
        echo "${key}=${val}" | sudo tee -a "$ENV" >/dev/null
    fi
}

echo "=== Healthchecks.io media-server check ==="
HC_KEY=$(sudo grep '^HEALTHCHECKS_API_KEY=' "$ENV" | cut -d= -f2- | tr -d '"')
if [ -z "$HC_KEY" ] || [ "$HC_KEY" = "your_read_only_api_key_here" ]; then
    echo "SKIP: HEALTHCHECKS_API_KEY not configured"
else
    PING_URL=$(python3 <<PY || true
import json, urllib.request, urllib.error
key = """$HC_KEY"""
try:
    req = urllib.request.Request(
        "https://healthchecks.io/api/v3/checks/",
        headers={"X-Api-Key": key},
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.load(r)
    for c in data.get("checks", []):
        if c.get("name") == "media-server":
            print(c.get("ping_url", ""))
            break
    else:
        body = json.dumps({"name": "media-server", "timeout": 120, "grace": 300, "schedule": "* * * * *"}).encode()
        req = urllib.request.Request(
            "https://healthchecks.io/api/v3/checks/",
            data=body,
            headers={"X-Api-Key": key, "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            print(json.load(r).get("ping_url", ""))
except urllib.error.HTTPError as e:
    print("", end="")
    import sys
    print(f"HC API error: {e.code}", file=sys.stderr)
PY
)
    if [ -n "$PING_URL" ] && [ "$PING_URL" != "placeholder" ]; then
        set_env MEDIA_SERVER_HEALTHCHECK_PING_URL "$PING_URL"
        echo "PING_URL configured"
    fi
fi

echo "=== SSH key for media server ==="
KEY="$HOME/.ssh/media_server_192_168_2_185_ed25519"
if [ ! -f "$KEY" ]; then
    ssh-keygen -t ed25519 -f "$KEY" -N "" -C "tinel@media-server-automation"
fi
CONFIG="$HOME/.ssh/config"
if ! grep -q "Host media-server" "$CONFIG" 2>/dev/null; then
    cat >> "$CONFIG" <<EOF

Host media-server
    HostName 192.168.2.185
    User tinel
    IdentityFile $KEY
    IdentitiesOnly yes
EOF
fi
set_env MEDIA_SERVER_SSH_KEY "$KEY"
echo "SSH public key (add to media server if ssh-copy-id not done):"
cat "${KEY}.pub"

echo "=== Restart services ==="
sudo systemctl restart mqtt-boot-listener.service mqtt-shutdown-listener.service status-publisher.service health-monitor.service
sleep 2
systemctl is-active mqtt-boot-listener mqtt-shutdown-listener status-publisher health-monitor

echo "=== Media server manager test ==="
cd "$OPT"
sudo "$OPT/venv/bin/python3" - <<'PY' || true
import os, sys
sys.path.insert(0, "scripts/utils")
from pathlib import Path
from dotenv import load_dotenv
import yaml, re
load_dotenv("config/.env")
with open("config/server_config.yaml") as f:
    cfg = yaml.safe_load(f)
def sub(v):
    if isinstance(v, str) and "${" in v:
        return re.sub(r"\$\{([^}]+)\}", lambda m: os.getenv(m.group(1), m.group(0)), v)
    return v
for s in cfg.get("servers", []):
    if s.get("type") == "linux_tuya":
        s["ssh"] = {k: sub(v) for k,v in s.get("ssh",{}).items()}
        s["tuya"] = {k: sub(v) for k,v in s.get("tuya",{}).items()}
        from server_factory import get_server_manager
        try:
            m = get_server_manager(s)
            print("Manager OK:", type(m).__name__)
            print("Power status:", m.get_power_status())
        except Exception as e:
            print("Manager error:", e)
PY

echo "DONE"
