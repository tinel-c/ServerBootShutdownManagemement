# Release Notes v3.1.0 - Enhanced Stability & Status Fallback

## Overview

This release addresses the critical "UNKNOWN" status reboot loop issue on Dell T310 servers and introduces several stability improvements to the watchdog automation.

## Key Changes

### 🏥 Status Reporting Improvements
- **Ping Fallback**: Added ICMP ping as a fallback when the Proxmox API is unreachable. If the API fails but the host responds to ping, it reports `online`. If both fail, it reports `offline`.
- **Increased Timeout**: Proxmox API connection timeout increased to 15 seconds to ensure stability during high-load periods or state transitions.

### 🛡️ Watchdog & Automation Refinement
- **Shutdown Guard**: Introduced a 10-minute cooldown period after any manual or automatic shutdown. The system will no longer attempt a "Recovery Boot" during this window, preventing loops during the host's actual power-down sequence.
- **Client-Requirement Boot**: Recovery boots (triggered by lost server health) now only occur if at least one client is connected and waiting for server resources.
- **Improved Logging**: Activity logs now specify exactly why a recovery event was triggered (e.g., "Status lost, 3 client(s) need server").

## Files Changed

- `scripts/status/status_publisher.py`: Added ping utility and fallback logic.
- `nodered/flows/41-client-automation.json`: Updated "Watchdog & Grace Loop" logic.
- `README.md` & `CHANGELOG.md`: Updated documentation and version.

## Installation / Update

1. Pull the latest changes: `git pull origin main`
2. Restart the status publisher service: `sudo ./manage.sh restart status`
3. If using Node-RED, the updated flow `41-client-automation.json` should be re-imported or manually patched.

---
**Version**: 3.1.0  
**Date**: January 18, 2026  
**Backward Compatible**: Yes  
