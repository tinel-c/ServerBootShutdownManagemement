#!/usr/bin/env bash
# Install or update a Modbus → MQTT device publisher under /opt/dell_server_management.

install_device_publisher() {
    local device_subdir="$1"
    local mqtt_test_topic="$2"
    shift 2
    local systemd_units=("$@")

    local repo_root="${REPO_ROOT:?REPO_ROOT must be set}"
    local device_name
    device_name="$(basename "$device_subdir")"
    local device_src="$repo_root/device/$device_subdir"
    local device_dest="$INSTALL_DIR/device/$device_subdir"
    local env_path="$device_dest/config/.env"
    local env_example="$device_src/config/.env.example"

    if [ ! -d "$device_src" ]; then
        print_error "device/$device_subdir not found under $repo_root"
        exit 1
    fi

    require_install_dir

    print_info "Installing $device_name MQTT publisher..."

    local env_backup=""
    if [ -f "$env_path" ]; then
        env_backup="$(mktemp)"
        cp "$env_path" "$env_backup"
    fi

    mkdir -p "$INSTALL_DIR/device"
    rm -rf "$device_dest"
    cp -r "$device_src" "$INSTALL_DIR/device/"

    if [ -n "$env_backup" ] && [ -f "$env_backup" ]; then
        mkdir -p "$(dirname "$env_path")"
        cp "$env_backup" "$env_path"
        rm -f "$env_backup"
    fi

    cp "$repo_root/requirements.txt" "$INSTALL_DIR/requirements.txt"

    for unit in "${systemd_units[@]}"; do
        cp "$repo_root/systemd/$unit" /etc/systemd/system/
    done

    if [ -f "$env_path" ]; then
        print_info "Keeping existing $env_path"
    elif [ -f "$env_example" ]; then
        mkdir -p "$(dirname "$env_path")"
        cp "$env_example" "$env_path"
        chmod 600 "$env_path"
        print_warn "Created $env_path from template — configure before production use"
    fi

    if [ -d "$device_dest/scripts" ]; then
        chmod +x "$device_dest/scripts/"*.py
    fi
    chmod 600 "$env_path" 2>/dev/null || true

    install_python_deps
    enable_and_restart_units "${systemd_units[@]}"
    check_units_active "${systemd_units[@]}"

    print_info "Done. Test MQTT: mosquitto_sub -h localhost -t '$mqtt_test_topic' -v"
}
