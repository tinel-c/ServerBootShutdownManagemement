#!/usr/bin/env bash
# Step-by-step Tuya account linking on the automation server.
# Run: bash scripts/tuya/tuya_link.sh [step]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PY="${TUYA_PYTHON:-$REPO_ROOT/../venv/bin/python3}"
if [ ! -x "$PY" ]; then
  PY="${TUYA_PYTHON:-/opt/dell_server_management/venv/bin/python3}"
fi
if [ ! -x "$PY" ]; then
  PY=python3
fi
SYNC="$SCRIPT_DIR/sync_devices.py"
ENV_FILE="$REPO_ROOT/config/.env"

env_grep() {
  if [ -r "$ENV_FILE" ]; then
    grep "$@" "$ENV_FILE"
  else
    sudo grep "$@" "$ENV_FILE"
  fi
}

run_py() {
  if [ -r "$ENV_FILE" ] && { [ -w "$ENV_FILE" ] || [ "$(id -u)" -eq 0 ]; }; then
    "$PY" "$SYNC" "$@"
  else
    sudo "$PY" "$SYNC" "$@"
  fi
}

step="${1:-}"

print_step() {
  echo ""
  echo "════════════════════════════════════════════════════════════"
  echo "  $1"
  echo "════════════════════════════════════════════════════════════"
  echo ""
}

step1() {
  print_step "STEP 1 — Tuya IoT Cloud project (do in browser)"
  cat <<'EOF'
1. Open https://iot.tuya.com and sign in
2. Cloud → Development → Create Cloud Project
   - Industry: Smart Home (or General)
   - Data center: Central Europe (or closest to you) → use TUYA_API_REGION=eu
3. Open the project → API → enable "IoT Core" / Device Management APIs
4. Overview → Authorization Key → copy Access ID and Access Secret

EOF
  echo "Then add to $ENV_FILE :"
  echo "  TUYA_ACCESS_ID=your_access_id"
  echo "  TUYA_ACCESS_SECRET=your_access_secret"
  echo "  TUYA_API_REGION=eu"
}

step2() {
  print_step "STEP 2 — Link Smart Life / Tuya app account (browser)"
  cat <<'EOF'
1. In your IoT project: Devices → Link Tuya App Account
2. Scan QR code with Smart Life or Tuya Smart app (same account as your devices)
3. Confirm devices appear under the project device list

EOF
}

step3() {
  print_step "STEP 3 — Verify cloud API credentials"
  if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: $ENV_FILE not found"
    exit 1
  fi
  if ! env_grep -q '^TUYA_ACCESS_ID=' 2>/dev/null; then
    echo "ERROR: TUYA_ACCESS_ID not set in $ENV_FILE — complete Step 1 first"
    exit 1
  fi
  run_py verify
}

step4() {
  print_step "STEP 4 — List all linked devices (cloud)"
  run_py list
}

step5() {
  print_step "STEP 5 — Sync to config/tuya_devices.json (cloud + LAN IP scan)"
  run_py sync
}

step6() {
  print_step "STEP 6 — Apply media_server role → config/.env"
  run_py apply-role media_server --device-id bfd81b15990104836cxqma 2>/dev/null || run_py apply-role media_server || true
  echo ""
  echo "Restart listeners:"
  echo "  sudo systemctl restart mqtt-boot-listener mqtt-shutdown-listener"
}

step6b() {
  print_step "STEP 6b — Write all devices to config/.env (TUYA_DEVICE_N_*)"
  run_py apply-env
}

step7() {
  print_step "STEP 7 — Test local Tuya connection"
  run_py test
}

usage() {
  cat <<EOF
Tuya account linking — step by step

Usage: $0 [step|all]

  step1   Browser: create IoT project, copy API keys
  step2   Browser: link Smart Life app account (QR)
  step3   Verify API credentials on this server
  step4   List devices from cloud
  step5   Sync registry (config/tuya_devices.json)
  step6   Apply media_server credentials to .env
  step6b  Write all devices to .env (TUYA_DEVICE_N_*)
  step7   Test local device API
  all     Run steps 3–7 (after browser steps 1–2)

Examples:
  $0           # show all step instructions
  $0 step3     # verify credentials
  $0 all       # sync + apply after browser setup

Docs: docs/TUYA_ACCOUNT_LINK.md
EOF
}

case "$step" in
  ""|help|-h|--help) usage; step1; step2 ;;
  step1) step1 ;;
  step2) step2 ;;
  step3) step3 ;;
  step4) step4 ;;
  step5) step5 ;;
  step6) step6 ;;
  step6b) step6b ;;
  step7) step7 ;;
  all) step3; step4; step5; step6b; step7 ;;
  *) echo "Unknown step: $step"; usage; exit 1 ;;
esac
