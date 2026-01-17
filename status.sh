#!/bin/bash
#
# Status check script for Dell & HP Server Management System
# Displays the current status of all services and recent logs
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

# Service names
SERVICES=(
    "mqtt-boot-listener.service"
    "mqtt-shutdown-listener.service"
    "status-publisher.service"
    "health-monitor.service"
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

# Print quick commands
print_quick_commands() {
    echo -e "${CYAN}${BOLD}Quick Commands:${NC}"
    echo ""
    echo "  Start all services:"
    echo -e "    ${YELLOW}sudo systemctl start mqtt-boot-listener mqtt-shutdown-listener status-publisher health-monitor${NC}"
    echo ""
    echo "  Stop all services:"
    echo -e "    ${YELLOW}sudo systemctl stop mqtt-boot-listener mqtt-shutdown-listener status-publisher health-monitor${NC}"
    echo ""
    echo "  Restart all services:"
    echo -e "    ${YELLOW}sudo systemctl restart mqtt-boot-listener mqtt-shutdown-listener status-publisher health-monitor${NC}"
    echo ""
    echo "  View live logs:"
    echo -e "    ${YELLOW}sudo journalctl -u status-publisher.service -f${NC}"
    echo ""
    echo "  Enable on boot:"
    echo -e "    ${YELLOW}sudo systemctl enable mqtt-boot-listener mqtt-shutdown-listener status-publisher health-monitor${NC}"
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
