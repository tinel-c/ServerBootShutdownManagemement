# ✨ v1.3.0: Premium Dashboard & Intelligent State Tracking

We are proud to release **v1.3.0** of the **Server Remote Management System**! This update focuses on visual excellence and deeper operational insights within the Node-RED dashboard.

## 🆕 New in v1.3.0

### 💎 Premium "Glassmorphism" Dashboard
*   **Modern Aesthetics**: The server status cards have been redesigned with a semi-transparent, blurred background ("Glassmorphism") for a high-end, futuristic feel.
*   **Enhanced Typography**: Improved readability with grid-based metadata display and monospace font for timestamps.
*   **Dynamic Visuals**: Status indicators now feature a subtle glow effect that changes color dynamically (Green for Online, Red for Offline, Orange for Transitioning).

### 🧠 Intelligent State Tracking
*   **History at a Glance**: The system now remembers the **Previous State** of your servers, displaying exactly what they transitioned from.
*   **Precision Timing**: Added **Switched At** timestamps to track the exact moment a server changed its power state.
*   **Latency-Aware Reporting**: Reports now use the **MQTT Payload Timestamp**, ensuring the "Last Reported" time is accurate to when the server actually sent the data, not just when Node-RED received it.

### 🏥 Health Sync Visualization
*   **Report Synced Indicator**: Added a dedicated status bar to the Health Check lists, providing immediate visual confirmation of when the last health report was synchronized.

## 📦 Upgrade Instructions

1.  **Pull the latest changes**:
    ```bash
    git pull origin main
    ```
2.  **Redeploy Node-RED**:
    If you are using Docker, simply restart the container to pick up the new `flows.json`:
    ```bash
    cd nodered
    docker-compose restart
    ```
    *Alternatively, you can manually import the new `nodered/flows.json` into your existing Node-RED instance.*

## 🔗 Links

*   [📈 Node-RED Flows](nodered/flows.json)
*   [📜 Full Documentation](https://github.com/tinel-c/ServerBootShutdownManagemement/tree/main/docs)
*   [🐛 Issue Tracker](https://github.com/tinel-c/ServerBootShutdownManagemement/issues)

---
*Maintained by Constantin Bogza & Tinel Clenci*
