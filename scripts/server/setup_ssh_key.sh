#!/usr/bin/env bash
# Set up SSH key authentication to the automation server (serverside / 192.168.2.4).
set -euo pipefail

HOST_ALIAS=serverside
HOST_NAME=192.168.2.4
USER_NAME=tinel
SSH_DIR="$HOME/.ssh"
KEY_PATH="$SSH_DIR/serverside_192_168_2_4_ed25519"
CONFIG_PATH="$SSH_DIR/config"

mkdir -p "$SSH_DIR"
chmod 700 "$SSH_DIR"

if [ ! -f "$KEY_PATH" ]; then
    echo "Generating ED25519 key: $KEY_PATH"
    ssh-keygen -t ed25519 -f "$KEY_PATH" -N "" -C "${USER_NAME}@${HOST_ALIAS}-automation"
else
    echo "Using existing key: $KEY_PATH"
fi

echo "Installing public key on ${USER_NAME}@${HOST_NAME} (enter server password once)..."
ssh-copy-id -i "$KEY_PATH.pub" "${USER_NAME}@${HOST_NAME}" 2>/dev/null || \
    cat "$KEY_PATH.pub" | ssh "${USER_NAME}@${HOST_NAME}" \
        "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"

if ! grep -q "Host ${HOST_ALIAS}" "$CONFIG_PATH" 2>/dev/null; then
    cat >> "$CONFIG_PATH" << EOF

Host ${HOST_ALIAS}
    HostName ${HOST_NAME}
    User ${USER_NAME}
    IdentityFile ~/.ssh/serverside_192_168_2_4_ed25519
    IdentitiesOnly yes
EOF
    echo "Added Host ${HOST_ALIAS} to $CONFIG_PATH"
fi

ssh -o BatchMode=yes "${HOST_ALIAS}" "echo SSH key authentication OK for \$(whoami)@\$(hostname)"
echo ""
echo "Next: ./scripts/server/deploy_victron_remote.sh"
