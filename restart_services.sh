#!/bin/bash
#
# Helper script to restart all Dell & HP Server Management services
#

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "This script must be run as root. Try: sudo ./restart_services.sh"
    exit 1
fi

echo -e "${GREEN}Restarting Dell & HP Server Management Services...${NC}"

# Restart services
echo "Restarting mqtt-boot-listener..."
systemctl restart mqtt-boot-listener.service

echo "Restarting mqtt-shutdown-listener..."
systemctl restart mqtt-shutdown-listener.service

echo "Restarting status-publisher..."
systemctl restart status-publisher.service

echo -e "${GREEN}All services restarted successfully!${NC}"
echo ""
echo -e "${GREEN}Current Status:${NC}"
systemctl status mqtt-boot-listener.service --no-pager | head -n 3
echo "..."
systemctl status mqtt-shutdown-listener.service --no-pager | head -n 3
echo "..."
systemctl status status-publisher.service --no-pager | head -n 3
