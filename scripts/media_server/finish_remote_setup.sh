#!/usr/bin/env bash
# Complete media-server setup on automation server when secrets are in config/.env:
#   MEDIA_SERVER_SSH_PASSWORD  (one-time, for ssh-copy-id)
#   TUYA_ACCESS_ID / TUYA_ACCESS_SECRET / TUYA_API_REGION (iot.tuya.com cloud project)
set -euo pipefail

OPT=/opt/dell_server_management
ENV="$OPT/config/.env"
# shellcheck disable=SC1090
source <(sudo grep -E '^(MEDIA_SERVER_|TUYA_ACCESS_|TUYA_API_REGION|HEALTHCHECKS_API_KEY)=' "$ENV" | sed 's/^/export /')

KEY="${MEDIA_SERVER_SSH_KEY:-$HOME/.ssh/media_server_192_168_2_185_ed25519}"
HOST="${MEDIA_SERVER_HOST:-192.168.2.185}"
USER="${MEDIA_SERVER_SSH_USER:-tinel}"

set_env() {
    local k="$1" v="$2"
    if sudo grep -q "^${k}=" "$ENV"; then sudo sed -i "s|^${k}=.*|${k}=${v}|" "$ENV"
    else echo "${k}=${v}" | sudo tee -a "$ENV" >/dev/null; fi
}

if [ -n "${MEDIA_SERVER_SSH_PASSWORD:-}" ] && ! ssh -o BatchMode=yes -i "$KEY" "${USER}@${HOST}" true 2>/dev/null; then
    sudo apt-get install -y sshpass >/dev/null 2>&1 || true
    if command -v sshpass >/dev/null; then
        sshpass -p "$MEDIA_SERVER_SSH_PASSWORD" ssh-copy-id -i "${KEY}.pub" -o StrictHostKeyChecking=accept-new "${USER}@${HOST}"
        echo "SSH key installed on media server"
        sudo sed -i '/^MEDIA_SERVER_SSH_PASSWORD=/d' "$ENV"
    fi
fi

if [ -n "${TUYA_ACCESS_ID:-}" ] && [ -n "${TUYA_ACCESS_SECRET:-}" ]; then
    sudo "$OPT/venv/bin/python3" "$OPT/scripts/tuya/sync_devices.py" sync
    sudo "$OPT/venv/bin/python3" "$OPT/scripts/tuya/sync_devices.py" apply-role media_server || true
    echo "Tuya devices synced; media_server role applied (see config/tuya_devices.json)"
fi

if ssh -o BatchMode=yes -i "$KEY" "${USER}@${HOST}" true 2>/dev/null; then
    PING="${MEDIA_SERVER_HEALTHCHECK_PING_URL:-}"
    if [ -n "$PING" ] && [ "$PING" != "placeholder" ]; then
        ssh -i "$KEY" "${USER}@${HOST}" "bash -s" < "$OPT/scripts/media_server/install_healthcheck_cron.sh" "$PING" || true
    fi
    ssh -i "$KEY" "${USER}@${HOST}" "sudo grep -q media-automation /etc/sudoers.d/media-automation 2>/dev/null || echo '${USER} ALL=(ALL) NOPASSWD: /sbin/shutdown, /usr/sbin/shutdown, /bin/systemctl poweroff, /bin/systemctl halt' | sudo tee /etc/sudoers.d/media-automation >/dev/null && sudo chmod 440 /etc/sudoers.d/media-automation" || true
fi

sudo systemctl restart mqtt-boot-listener mqtt-shutdown-listener status-publisher health-monitor
echo "FINISH"
