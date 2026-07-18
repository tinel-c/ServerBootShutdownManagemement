#!/bin/bash
#
# Status check script for Dell, HP & media server automation
# Displays service status, optional logs, and media-server configuration checks
#

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Installation directory
INSTALL_DIR="/opt/dell_server_management"
if [ ! -d "$INSTALL_DIR" ]; then
    _STATUS_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    if [ -f "$_STATUS_SCRIPT_DIR/config/.env" ] || [ -f "$_STATUS_SCRIPT_DIR/config/.env.example" ]; then
        INSTALL_DIR="$_STATUS_SCRIPT_DIR"
    fi
fi

# Service names
SERVICES=(
    "mqtt-boot-listener.service"
    "mqtt-shutdown-listener.service"
    "status-publisher.service"
    "health-monitor.service"
    "camera-ping-watchdog.service"
    "victron-mqtt-publisher.service"
    "victron-solar-forecast-publisher.service"
    "huawei-mqtt-publisher.service"
    "grundfos-scala1-mqtt-publisher.service"
    "energy-consumers-publisher.service"
)

# Print header
print_header() {
    echo ""
    echo -e "${BOLD}========================================${NC}"
    echo -e "${BOLD}  Server Management System - STATUS${NC}"
    echo -e "${BOLD}========================================${NC}"
    echo ""
}

# Check if service is active
is_service_active() {
    systemctl is-active --quiet "$1"
    return $?
}

# Get service status with colored output
get_service_status() {
    local service=$1
    if systemctl is-active --quiet "$service"; then
        echo -e "${GREEN}●${NC} ${BOLD}RUNNING${NC}"
    else
        echo -e "${RED}●${NC} ${BOLD}STOPPED${NC}"
    fi
}

# Get service enabled status
is_service_enabled() {
    systemctl is-enabled --quiet "$1" 2>/dev/null
    return $?
}

# Print service status table
print_services_status() {
    echo -e "${CYAN}${BOLD}Services Status:${NC}"
    echo ""
    printf "%-35s %-15s %-15s\n" "Service" "Status" "Enabled"
    echo "────────────────────────────────────────────────────────────────"
    
    for service in "${SERVICES[@]}"; do
        local status=$(get_service_status "$service")
        local enabled="No"
        if is_service_enabled "$service"; then
            enabled="${GREEN}Yes${NC}"
        else
            enabled="${YELLOW}No${NC}"
        fi
        printf "%-35s %-25s %-15s\n" "$service" "$status" "$(echo -e $enabled)"
    done
    echo ""
}

# Print recent logs for a service
print_service_logs() {
    local service=$1
    local lines=${2:-10}
    
    echo -e "${CYAN}${BOLD}Recent logs for $service:${NC}"
    echo "────────────────────────────────────────────────────────────────"
    journalctl -u "$service" -n "$lines" --no-pager | tail -n "$lines"
    echo ""
}

# Print system info
print_system_info() {
    echo -e "${CYAN}${BOLD}System Information:${NC}"
    echo ""
    
    if [ -d "$INSTALL_DIR" ]; then
        echo -e "  Installation Directory: ${GREEN}$INSTALL_DIR${NC}"
        
        if [ -f "$INSTALL_DIR/config/.env" ]; then
            echo -e "  Configuration File:     ${GREEN}Found${NC}"
        else
            echo -e "  Configuration File:     ${RED}Missing${NC}"
        fi
        
        if [ -d "$INSTALL_DIR/venv" ]; then
            echo -e "  Python Virtual Env:     ${GREEN}Found${NC}"
        else
            echo -e "  Python Virtual Env:     ${RED}Missing${NC}"
        fi
    else
        echo -e "  Installation Directory: ${RED}Not found${NC}"
        echo -e "  ${YELLOW}System may not be installed yet.${NC}"
    fi
    echo ""
}

# Print media server configuration (no secrets)
print_media_server_config() {
    local env_file="$INSTALL_DIR/config/.env"

    if [ ! -f "$env_file" ]; then
        return 0
    fi

    # shellcheck disable=SC1090
    set -a
    source "$env_file"
    set +a

    if [ -z "${MEDIA_SERVER_HOST:-}" ]; then
        return 0
    fi

    echo -e "${CYAN}${BOLD}Media Server (linux_tuya):${NC}"
    echo ""
    echo -e "  Host:              ${GREEN}${MEDIA_SERVER_HOST}${NC}"
    echo -e "  SSH user:          ${MEDIA_SERVER_SSH_USER:-tinel}"

    if [ -n "${MEDIA_SERVER_SSH_KEY:-}" ] && [ -f "${MEDIA_SERVER_SSH_KEY}" ]; then
        echo -e "  SSH key:           ${GREEN}Found${NC} (${MEDIA_SERVER_SSH_KEY})"
    elif [ -n "${MEDIA_SERVER_SSH_KEY:-}" ]; then
        echo -e "  SSH key:           ${RED}Missing${NC} (${MEDIA_SERVER_SSH_KEY})"
    else
        echo -e "  SSH key:           ${YELLOW}Not set${NC}"
    fi

    if [ -n "${MEDIA_SERVER_TUYA_DEVICE_ID:-}" ] && [ "${MEDIA_SERVER_TUYA_DEVICE_ID}" != "your_tuya_device_id" ]; then
        echo -e "  Tuya device ID:    ${GREEN}Configured${NC}"
    else
        echo -e "  Tuya device ID:    ${YELLOW}Not set${NC} — run scripts/tuya/tuya_link.sh"
    fi

    if [ -f "$INSTALL_DIR/config/tuya_devices.json" ]; then
        echo -e "  Tuya registry:     ${GREEN}config/tuya_devices.json${NC}"
    else
        echo -e "  Tuya registry:     ${YELLOW}Missing${NC} — scripts/tuya/sync_devices.py sync"
    fi

    if [ -n "${TUYA_ACCESS_ID:-}" ]; then
        echo -e "  Tuya cloud API:    ${GREEN}Configured${NC}"
    else
        echo -e "  Tuya cloud API:    ${YELLOW}Not set${NC} — see docs/TUYA_ACCOUNT_LINK.md"
    fi

    if [ -n "${MEDIA_SERVER_HEALTHCHECK_PING_URL:-}" ] && [[ "${MEDIA_SERVER_HEALTHCHECK_PING_URL}" != *"your-uuid"* ]]; then
        echo -e "  Healthchecks ping: ${GREEN}Configured${NC}"
    else
        echo -e "  Healthchecks ping: ${YELLOW}Not set${NC}"
    fi

    if command -v ping >/dev/null 2>&1; then
        if ping -c 1 -W 1 "$MEDIA_SERVER_HOST" >/dev/null 2>&1; then
            echo -e "  Host ping:         ${GREEN}Reachable${NC}"
        else
            echo -e "  Host ping:         ${RED}Unreachable${NC}"
        fi
    fi

    if [ -n "${MEDIA_SERVER_SSH_KEY:-}" ] && [ -f "${MEDIA_SERVER_SSH_KEY}" ]; then
        if ssh -i "$MEDIA_SERVER_SSH_KEY" -o BatchMode=yes -o ConnectTimeout=3 \
            "${MEDIA_SERVER_SSH_USER:-tinel}@${MEDIA_SERVER_HOST}" true 2>/dev/null; then
            echo -e "  SSH login:         ${GREEN}OK${NC}"
        else
            echo -e "  SSH login:         ${YELLOW}Failed${NC} — run scripts/server/setup_media_server_ssh.sh"
        fi
    fi

    echo -e "  MQTT topics:       media/server/{status,health,command/*}"
    echo -e "  Handled by:        mqtt-boot-listener, mqtt-shutdown-listener, status-publisher"
    echo ""
}

# Print quick commands
print_quick_commands() {
    echo -e "${CYAN}${BOLD}Quick Commands:${NC}"
    echo ""
    echo "  Manage all services:"
    echo -e "    ${YELLOW}sudo ./manage.sh start|stop|restart|enable|disable${NC}"
    echo ""
    echo "  Check status and logs:"
    echo -e "    ${YELLOW}./status.sh -l${NC}"
    echo ""
    echo "  View live logs:"
    echo -e "    ${YELLOW}sudo ./manage.sh logs${NC}"
    echo -e "    ${YELLOW}sudo journalctl -u mqtt-boot-listener.service -f${NC}"
    echo ""
    echo "  Media server MQTT:"
    echo -e "    ${YELLOW}mosquitto_sub -h localhost -t 'media/server/status' -C 1${NC}"
    echo ""
}

# Main script
main() {
    local show_logs=false
    local log_lines=10
    local show_all=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -l|--logs)
                show_logs=true
                shift
                ;;
            -n|--lines)
                log_lines="$2"
                shift 2
                ;;
            -a|--all)
                show_all=true
                show_logs=true
                shift
                ;;
            -h|--help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  -l, --logs        Show recent logs for each service"
                echo "  -n, --lines N     Show N lines of logs (default: 10)"
                echo "  -a, --all         Show all information including detailed logs"
                echo "  -h, --help        Show this help message"
                echo ""
                echo "Examples:"
                echo "  $0                Show service status only"
                echo "  $0 -l             Show status and recent logs (10 lines)"
                echo "  $0 -l -n 20       Show status and recent logs (20 lines)"
                echo "  $0 -a             Show everything"
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                echo "Use -h or --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Print header
    print_header
    
    # Print system info
    print_system_info
    
    # Print services status
    print_services_status

    # Media server config (when MEDIA_SERVER_HOST is set)
    print_media_server_config
    
    # Print logs if requested
    if [ "$show_logs" = true ]; then
        for service in "${SERVICES[@]}"; do
            if is_service_active "$service" || [ "$show_all" = true ]; then
                print_service_logs "$service" "$log_lines"
            fi
        done
    fi
    
    # Print quick commands
    if [ "$show_all" = true ]; then
        print_quick_commands
    else
        echo -e "${CYAN}Tip: Use './status.sh -h' for more options${NC}"
        echo ""
    fi
}

# Run main function
main "$@"
