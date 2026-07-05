#!/usr/bin/env bash
# Set up SSH key authentication from the automation server to the media server.
# Run this ON the automation server (192.168.2.4), not on your dev PC.
set -euo pipefail

HOST_ALIAS=media-server
HOST_NAME="${MEDIA_SERVER_HOST:-192.168.2.185}"
USER_NAME="${MEDIA_SERVER_SSH_USER:-tinel}"
SSH_DIR="$HOME/.ssh"
KEY_PATH="$SSH_DIR/media_server_192_168_2_185_ed25519"
CONFIG_PATH="$SSH_DIR/config"

mkdir -p "$SSH_DIR"
chmod 700 "$SSH_DIR"

if [ ! -f "$KEY_PATH" ]; then
    echo "Generating ED25519 key: $KEY_PATH"
    ssh-keygen -t ed25519 -f "$KEY_PATH" -N "" -C "${USER_NAME}@${HOST_ALIAS}-automation"
else
    echo "Using existing key: $KEY_PATH"
fi

echo "Installing public key on ${USER_NAME}@${HOST_NAME} (enter media server password once)..."
ssh-copy-id -i "$KEY_PATH.pub" -o StrictHostKeyChecking=accept-new "${USER_NAME}@${HOST_NAME}" 2>/dev/null || \
    cat "$KEY_PATH.pub" | ssh -o StrictHostKeyChecking=accept-new "${USER_NAME}@${HOST_NAME}" \
        "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"

if ! grep -q "Host ${HOST_ALIAS}" "$CONFIG_PATH" 2>/dev/null; then
    cat >> "$CONFIG_PATH" << EOF

Host ${HOST_ALIAS}
    HostName ${HOST_NAME}
    User ${USER_NAME}
    IdentityFile ${KEY_PATH}
    IdentitiesOnly yes
EOF
    echo "Added Host ${HOST_ALIAS} to $CONFIG_PATH"
fi

ssh -o BatchMode=yes -i "$KEY_PATH" "${HOST_ALIAS}" "echo SSH key authentication OK for \$(whoami)@\$(hostname)"
echo ""
echo "Next: configure passwordless shutdown on the media server (see docs/MEDIA_SERVER.md)"
echo "  sudo visudo -f /etc/sudoers.d/media-automation"
