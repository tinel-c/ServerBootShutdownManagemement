# 🚀 v1.2.0: HealthChecks.io Integration & Real-time Monitoring

We are excited to announce the v1.2.0 release of the **Server Remote Management System**! This release introduces professional-grade external monitoring integration with **HealthChecks.io** and a beautiful new console dashboard.

## 🆕 New in v1.2.0

### 🏥 HealthChecks.io Integration (API v3)
*   **External Health Monitoring**: Connect your servers to HealthChecks.io to track uptime and task completions.
*   **Environment-Based Mapping**: Easily map servers to multiple HealthChecks.io checks via simple `.env` variables (`T310_HEALTHCHECKS`, `DL360P_HEALTHCHECKS`).
*   **MQTT Reporting**: Health status is automatically published to MQTT topics (`dell/t310/health`, `hp/dl360p/health`), enabling seamless integration with Node-RED and Home Assistant.

### 🖼️ Node-RED Dashboard Updates
*   **Health Visualization**: New dedicated UI groups for "Dell T310 Health" and "HP DL360p Health".
*   **Live Status Lists**: Beautifully rendered lists of individual health checks with real-time status color codes (UP/DOWN/NEW).
*   **Improved Layout**: Reorganized the dashboard for better usability and status overview.

### 📊 Live Console Dashboard
*   **Rich UI**: A new `health_monitor.py` script provides a stunning, live-updating table in your terminal using the `rich` library.
*   **Real-time Insights**: View check status, last ping times, and state transitions at a glance.

### 🛠️ Infrastructure & Management
*   **New Service**: Added `health-monitor.service` to the systemd ecosystem.
*   **Automated Lifecycle**: The `install.sh`, `restart_services.sh`, and `uninstall.sh` scripts have been fully updated to support the new monitoring service.
*   **Updated Requirements**: Added `rich` library for enhanced terminal visuals.

## 📦 Installation / Upgrade

1.  **Update code and dependencies**:
    ```bash
    git pull origin main
    pip install -r requirements.txt
    ```
2.  **Configure API Key**:
    Add your read-only API key and check mappings to `config/.env`:
    ```env
    HEALTHCHECKS_API_KEY=your_key_here
    T310_HEALTHCHECKS="Check Name 1,Check Name 2"
    DL360P_HEALTHCHECKS="Check Name 3"
    ```
3.  **Deploy new service**:
    ```bash
    sudo ./install.sh
    sudo systemctl enable --now health-monitor.service
    ```

## 🔗 Links

*   [📜 Full Documentation](https://github.com/tinel-c/ServerBootShutdownManagemement/tree/main/docs)
*   [🐛 Issue Tracker](https://github.com/tinel-c/ServerBootShutdownManagemement/issues)

---
*Maintained by Constantin Bogza & Tinel Clenci*
