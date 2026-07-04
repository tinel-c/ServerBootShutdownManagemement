#!/usr/bin/env bash
# Shared helpers for install.sh, update.sh, and device publisher installers.

INSTALL_DIR="${INSTALL_DIR:-/opt/dell_server_management}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
print_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

require_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "Run as root: sudo $*"
        exit 1
    fi
}

require_install_dir() {
    if [ ! -d "$INSTALL_DIR" ]; then
        print_error "$INSTALL_DIR not found — run install.sh first"
        exit 1
    fi
}

backup_device_env() {
    local env_path="$1"
    local backup_dir="$2"

    if [ ! -f "$env_path" ]; then
        return 0
    fi

    print_warn "Found existing $(basename "$(dirname "$env_path")")/.env — preserving..."
    mkdir -p "$backup_dir"
    cp "$env_path" "$backup_dir/.env"
    print_info "Backed up to $backup_dir/.env"
}

restore_device_env() {
    local env_path="$1"
    local backup_dir="$2"
    local example_path="$3"
    local configure_hint="$4"

    if [ -f "$backup_dir/.env" ]; then
        mkdir -p "$(dirname "$env_path")"
        cp "$backup_dir/.env" "$env_path"
        chmod 600 "$env_path"
        print_info "Restored $(basename "$(dirname "$env_path")")/.env"
        return 0
    fi

    if [ ! -f "$env_path" ] && [ -f "$example_path" ]; then
        mkdir -p "$(dirname "$env_path")"
        cp "$example_path" "$env_path"
        chmod 600 "$env_path"
        print_warn "Created $env_path from template — $configure_hint"
    fi
}

install_python_deps() {
    require_install_dir
    # shellcheck source=/dev/null
    source "$INSTALL_DIR/venv/bin/activate"
    pip install --upgrade pip
    pip install -r "$INSTALL_DIR/requirements.txt"
}

enable_and_restart_units() {
    local units=("$@")

    systemctl daemon-reload
    for unit in "${units[@]}"; do
        systemctl enable "$unit"
        systemctl restart "$unit"
    done
}

check_units_active() {
    local failed=0
    local unit

    for unit in "$@"; do
        sleep 1
        if systemctl is-active --quiet "$unit"; then
            print_info "$unit is running"
        else
            print_warn "$unit not active — check: journalctl -u $unit -n 30"
            failed=1
        fi
    done

    if [ "$failed" -ne 0 ] && [ "${ALLOW_INACTIVE_SERVICE:-0}" != "1" ]; then
        return 1
    fi
    return 0
}
