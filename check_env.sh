#!/bin/bash
#
# Check environment configuration and list missing variables
#

# Try installation directory first, then local
if [ -f "/opt/dell_server_management/config/.env" ]; then
    ENV_FILE="/opt/dell_server_management/config/.env"
elif [ -f "config/.env" ]; then
    ENV_FILE="config/.env"
else
    ENV_FILE="config/.env"  # Will fail with proper error message
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Required variables
REQUIRED_VARS=(
    # MQTT
    "MQTT_BROKER_HOST"
    "MQTT_BROKER_PORT"
    "MQTT_USERNAME"
    "MQTT_PASSWORD"
    
    # Dell T310
    "T310_PROXMOX_HOST"
    "T310_PROXMOX_USERNAME"
    "T310_PROXMOX_PASSWORD"
    "T310_MAC_ADDRESS"
    
    # HP DL360p (if using)
    # "DL360P_ILO_HOST"
    # "DL360P_ILO_USERNAME"
    # "DL360P_ILO_PASSWORD"
)

echo "========================================"
echo "  Environment Configuration Check"
echo "========================================"
echo ""

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ ERROR: $ENV_FILE not found!${NC}"
    echo ""
    echo "To create it:"
    echo "  1. Run: ./generate_env_template.sh"
    echo "  2. Copy: cp config/.env.example config/.env"
    echo "  3. Edit: nano config/.env"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ Found: $ENV_FILE${NC}"
echo ""

# Load .env file
set -a
source "$ENV_FILE"
set +a

# Check each required variable
MISSING_COUNT=0
echo "Checking required variables:"
echo ""

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "  ${RED}❌ $var${NC} - NOT SET"
        MISSING_COUNT=$((MISSING_COUNT + 1))
    else
        # Mask passwords
        if [[ $var == *"PASSWORD"* ]]; then
            echo -e "  ${GREEN}✓ $var${NC} = ****"
        else
            VALUE="${!var}"
            if [ ${#VALUE} -gt 40 ]; then
                echo -e "  ${GREEN}✓ $var${NC} = ${VALUE:0:40}..."
            else
                echo -e "  ${GREEN}✓ $var${NC} = $VALUE"
            fi
        fi
    fi
done

# Check for dynamic Camera configurations
echo ""
echo "Checking dynamic Camera configurations:"
CAM_IDS=$(env | grep '^CAMERA_[0-9]\+_NAME' | cut -d'_' -f2 | sort -u)

if [ -z "$CAM_IDS" ]; then
    echo -e "  ${YELLOW}⚠ No cameras configured (CAMERA_N_NAME pattern not found)${NC}"
else
    for id in $CAM_IDS; do
        CAM_NAME_VAR="CAMERA_${id}_NAME"
        CAM_IP_VAR="CAMERA_${id}_IP"
        CAM_USER_VAR="CAMERA_${id}_USER"
        CAM_PASS_VAR="CAMERA_${id}_PASS"
        
        CAM_NAME="${!CAM_NAME_VAR}"
        echo -en "  Camera $id ($CAM_NAME): "
        
        MISSING_CAM_PROPS=()
        [ -z "${!CAM_IP_VAR}" ] && MISSING_CAM_PROPS+=("IP")
        [ -z "${!CAM_USER_VAR}" ] && MISSING_CAM_PROPS+=("USER")
        [ -z "${!CAM_PASS_VAR}" ] && MISSING_CAM_PROPS+=("PASS")
        
        if [ ${#MISSING_CAM_PROPS[@]} -eq 0 ]; then
            echo -e "${GREEN}✓ Correctly configured${NC}"
        else
            echo -e "${RED}❌ Missing: ${MISSING_CAM_PROPS[*]}${NC}"
            MISSING_COUNT=$((MISSING_COUNT + 1))
        fi
    done
fi

echo ""
echo "========================================"

if [ $MISSING_COUNT -gt 0 ]; then
    echo -e "${RED}❌ $MISSING_COUNT variable(s) missing!${NC}"
    echo ""
    echo "Fix by editing: $ENV_FILE"
    echo "See template: config/.env.example"
    echo ""
    exit 1
else
    echo -e "${GREEN}✅ All required variables are set!${NC}"
    echo ""
    echo "Configuration looks good. Services should work properly."
    echo ""
    exit 0
fi
