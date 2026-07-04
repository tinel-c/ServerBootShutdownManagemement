#!/usr/bin/env bash
# Shared helpers for temporary automation sudo (deploy + agent modes).

set -euo pipefail

AUTOMATION_SUDO_STAMP="/var/lib/automation-deploy-sudo-expires"
AUTOMATION_SUDO_MODE_STAMP="/var/lib/automation-deploy-sudo-mode"

automation_sudo_repo_root() {
    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    echo "$(cd "$script_dir/../.." && pwd)"
}

automation_sudo_revoke_script() {
    echo "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/revoke_deploy_sudo.sh"
}

automation_sudo_src_for_mode() {
    local mode="$1"
    local repo_root
    repo_root="$(automation_sudo_repo_root)"
    case "$mode" in
        deploy) echo "$repo_root/scripts/server/sudoers.d-automation-deploy-temp" ;;
        agent) echo "$repo_root/scripts/server/sudoers.d-automation-agent-temp" ;;
        *)
            echo "Unknown sudo mode: $mode (expected deploy or agent)" >&2
            return 1
            ;;
    esac
}

automation_sudo_dest_for_mode() {
    local mode="$1"
    case "$mode" in
        deploy) echo "/etc/sudoers.d/automation-deploy-temp" ;;
        agent) echo "/etc/sudoers.d/automation-agent-temp" ;;
        *)
            echo "Unknown sudo mode: $mode (expected deploy or agent)" >&2
            return 1
            ;;
    esac
}

automation_sudo_other_temp() {
    local mode="$1"
    case "$mode" in
        deploy) echo "/etc/sudoers.d/automation-agent-temp" ;;
        agent) echo "/etc/sudoers.d/automation-deploy-temp" ;;
        *)
            echo "Unknown sudo mode: $mode (expected deploy or agent)" >&2
            return 1
            ;;
    esac
}

automation_sudo_grant() {
    local mode="$1"
    local minutes="$2"
    local src dest other revoke_script expires_at

    src="$(automation_sudo_src_for_mode "$mode")"
    dest="$(automation_sudo_dest_for_mode "$mode")"
    other="$(automation_sudo_other_temp "$mode")"
    revoke_script="$(automation_sudo_revoke_script)"

    if [ ! -f "$src" ]; then
        echo "Missing $src — sync repo to ~/ServerBootShutdownManagemement first" >&2
        return 1
    fi

    if ! [[ "$minutes" =~ ^[0-9]+$ ]] || [ "$minutes" -lt 1 ]; then
        echo "Minutes must be a positive integer" >&2
        return 1
    fi

    chmod +x "$revoke_script" 2>/dev/null || true

    # One active temporary mode at a time.
    rm -f "$other"

    cp "$src" "$dest"
    sed -i 's/\r$//' "$dest"
    chmod 440 "$dest"
    visudo -cf "$dest" >/dev/null

    expires_at="$(date -d "+${minutes} minutes" -Iseconds 2>/dev/null || date -v+${minutes}M -Iseconds 2>/dev/null || echo "in ${minutes} minutes")"
    echo "$expires_at" > "$AUTOMATION_SUDO_STAMP"
    echo "$mode" > "$AUTOMATION_SUDO_MODE_STAMP"
    chmod 644 "$AUTOMATION_SUDO_STAMP" "$AUTOMATION_SUDO_MODE_STAMP"

    for job in $(atq 2>/dev/null | awk '{print $1}'); do
        atrm "$job" 2>/dev/null || true
    done

    if command -v at >/dev/null 2>&1; then
        echo "$revoke_script" | at "now + ${minutes} minutes" 2>/dev/null
    else
        echo "WARN: 'at' not installed — sudo will NOT auto-expire" >&2
        echo "Revoke manually: sudo $revoke_script" >&2
    fi

    echo "$expires_at"
}
