# Release Notes v3.2.0 - Stability & Reliability Release

## Overview

This release focuses on hardening the system's stability and reliability, addressing critical edge cases in status reporting and automation, and streamlining the update lifecycle.

## Key Changes

### 🏥 Robust Status Monitoring
- **Ping Fallback (Dell T310)**: Implemented ICMP ping fallback in `status_publisher.py`. If the Proxmox API is unreachable, the system now uses ping to differentiate between an API failure and a true server power-down. This eliminates the "UNKNOWN" status reboot loop.
- **Improved API Resilience**: Increased Proxmox API connection timeout from 5s to 15s to handle transition delays more effectively.

### 🛡️ Intelligent Watchdog Guard
- **Shutdown Guard**: Introduced a 10-minute cooldown period in Node-RED (`41-client-automation.json`) after a shutdown command. The watchdog is automatically suspended during this window to prevent unintended recovery boots while the host is powering off.
- **Client-Requirement Boot**: Recovery boots (triggered by server health loss) now only occur if at least one client is connected and waiting for server resources.

### ⚡ Update & Lifecycle Reliability
- **Parallel Service Operations**: Modified `update.sh` to stop and start all services in parallel, significantly reducing wait times and preventing sequential hang issues.
- **Graceful Termination**: Added proper signal handling (`SIGTERM`) to the Health Monitor service for clean exits and MQTT state cleanup.
- **systemd Safety Fallback**: Integrated `TimeoutStopSec=15` into all systemd service definitions to ensure the system never hangs indefinitely during a service stop.
- **Automated Permissions**: The update script now automatically ensures all management shell scripts are executable.

## Files Changed

- `scripts/status/status_publisher.py`: Ping utility and fallback logic.
- `scripts/status/health_monitor.py`: Signal handling and graceful exit.
- `nodered/flows/41-client-automation.json`: Watchdog guard & client-only recovery.
- `update.sh`: Parallelization and permission management.
- `systemd/*.service`: Timeout configurations.
- `README.md`, `CHANGELOG.md`, `docs/ARCHITECTURE.md`: Documentation updates.

## Installation / Update

1. Pull the latest changes: `git pull origin main`
2. Run the update script: `sudo ./update.sh`
3. If using Node-RED, ensure flow `41-client-automation.json` is synced.

---
**Version**: 3.2.0  
**Date**: January 18, 2026  
**Backward Compatible**: Yes  
