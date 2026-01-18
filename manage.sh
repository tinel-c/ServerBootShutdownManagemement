#!/bin/bash
#
# Service management script for Dell & HP Server Management System
# Quick commands to start, stop, restart, and enable/disable services
#

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Service names
SERVICES=(
    "mqtt-boot-listener.service"
    "mqtt-shutdown-listener.service"
    "status-publisher.service"
    "health-monitor.service"
    "tapo-monitor.service"
)

# Print functions
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}→${NC} $1"
}

# Check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Start all services
start_services() {
    print_info "Starting all services..."
    echo ""
    
    for service in "${SERVICES[@]}"; do
        if systemctl start "$service" 2>/dev/null; then
            print_success "Started $service"
        else
            print_error "Failed to start $service"
        fi
    done
    
    echo ""
    print_info "Done! Use './status.sh' to check status"
}

# Stop all services
stop_services() {
    print_info "Stopping all services..."
    echo ""
    
    for service in "${SERVICES[@]}"; do
        if systemctl stop "$service" 2>/dev/null; then
            print_success "Stopped $service"
        else
            print_error "Failed to stop $service (may not be running)"
        fi
    done
    
    echo ""
    print_info "Done! Use './status.sh' to check status"
}

# Restart all services
restart_services() {
    print_info "Restarting all services..."
    echo ""
    
    for service in "${SERVICES[@]}"; do
        if systemctl restart "$service" 2>/dev/null; then
            print_success "Restarted $service"
        else
            print_error "Failed to restart $service"
        fi
    done
    
    echo ""
    print_info "Done! Use './status.sh -l' to check status and logs"
}

# Enable services on boot
enable_services() {
    print_info "Enabling services to start on boot..."
    echo ""
    
    for service in "${SERVICES[@]}"; do
        if systemctl enable "$service" 2>/dev/null; then
            print_success "Enabled $service"
        else
            print_error "Failed to enable $service"
        fi
    done
    
    echo ""
    print_info "Services will now start automatically on system boot"
}

# Disable services on boot
disable_services() {
    print_info "Disabling services from starting on boot..."
    echo ""
    
    for service in "${SERVICES[@]}"; do
        if systemctl disable "$service" 2>/dev/null; then
            print_success "Disabled $service"
        else
            print_error "Failed to disable $service"
        fi
    done
    
    echo ""
    print_info "Services will no longer start automatically on system boot"
}

# Show usage
show_usage() {
    echo "Usage: sudo $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     Start all services"
    echo "  stop      Stop all services"
    echo "  restart   Restart all services"
    echo "  enable    Enable services to start on boot"
    echo "  disable   Disable services from starting on boot"
    echo "  status    Show current status (runs ./status.sh)"
    echo "  logs      Show live logs for status-publisher"
    echo ""
    echo "Examples:"
    echo "  sudo $0 start"
    echo "  sudo $0 restart"
    echo "  sudo $0 status"
    echo ""
}

# Main script
main() {
    if [ $# -eq 0 ]; then
        show_usage
        exit 0
    fi
    
    local command=$1
    
    case $command in
        start)
            check_root
            start_services
            ;;
        stop)
            check_root
            stop_services
            ;;
        restart)
            check_root
            restart_services
            ;;
        enable)
            check_root
            enable_services
            ;;
        disable)
            check_root
            disable_services
            ;;
        status)
            # No root required for status
            if [ -f "./status.sh" ]; then
                ./status.sh
            else
                echo "Error: status.sh not found in current directory"
                exit 1
            fi
            ;;
        logs)
            # No root required for logs
            print_info "Showing live logs for status-publisher (Ctrl+C to exit)..."
            echo ""
            journalctl -u status-publisher.service -f
            ;;
        -h|--help|help)
            show_usage
            ;;
        *)
            print_error "Unknown command: $command"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
