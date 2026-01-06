# Release Notes v2.2.0 - Decentralized Automation & Idle Shutdown

**Significantly improved autonomy and reliability through decentralized health monitoring.**

## 🚀 Key Features

### 1. Decentralized Health Monitoring
The automation logic no longer relies on a shared global context or complex cross-flow dependencies. 
- **Direct Subscription**: The automation dashboard listens directly to `dell/t310/health`.
- **Local Status Derivation**: Server status (UP/DOWN) is derived logically from the aggregate of health checks.
- **Fail-safe**: If the status flow (Tab 11) is modified or restarted, the automation (Tab 41) continues to function independently.

### 2. Client-Side Health Integration
The Windows client application has been updated to align with the new server-side logic.
- **Health-Aware**: `client_monitor.py` now subscribes to the health topic instead of the generic status topic.
- **Enhanced Status Indicators**: The system tray icon now correctly interprets "UP" and "DOWN" states, eliminating the "Unknown" (yellow) status issue.

### 3. Reactive Idle Auto-Shutdown
A major enhancement to power management.
- **Smart Idle Detection**: The system now detects if the server is **ONLINE** but has **0 Active Clients**.
- **Auto-Countdown**: If this state is detected, a 5-minute shutdown grace period starts automatically.
- **Safety First**: This handles edge cases like manual server boots or Node-RED restarts, ensuring the server doesn't stay on indefinitely if unused.
- **Instant Cancellation**: If a client connects during the countdown, the shutdown is immediately aborted.

### 4. Code cleanup & Optimization
- Fixed JSON structure issues in `41-client-automation.json`.
- Removed legacy global variable dependencies.
- Standardized UI colors and status labels across all dashboards.

## 🛠️ Upgrade Instructions

### Node-RED
1. Import the updated `41-client-automation.json`.
2. Import the updated `11-dell-status.json` (reverted to local context).
3. Deploy changes.

### Client PC
1. **Administrator Action Required**: Run `update_client_files.bat` as Administrator on all client PCs.
2. This will update the `client_monitor.py` script and restart the service.
