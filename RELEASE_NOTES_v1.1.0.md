# 🚀 v1.1.0: Enhanced Reliability for Proxmox & HA

We are excited to announce the v1.1.0 release of the **Server Remote Management System**! This release builds upon the solid foundation of v1.0.0 by introducing critical reliability improvements for Proxmox environments, specifically targeting High Availability (HA) clusters and automated boot reliability.

## 🌟 Key Features (v1.0.0)

*   **Multi-Server Support**: Seamlessly manage **Dell T310** (IPMI) and **HP DL360p** (iLO) servers in the same ecosystem.
*   **Unified MQTT API**: Standardized topics for boot, shutdown, and status monitoring across different hardware.
*   **Protocol Support**:
    *   🔌 **IPMI** (Dell T310)
    *   ⚡ **HP iLO** (HP DL360p)
    *   🌐 **Wake-on-LAN** (Universal)
*   **Secure Configuration**: 100% environment-variable based config for credentials and secrets.
*   **Status Monitoring**: Real-time health and power status reporting.

## 🆕 New in v1.1.0

### 🏥 Proxmox HA Awareness
*   **Smart Shutdown**: The shutdown logic is now aware of Proxmox High Availability resources. It detects if a VM is managed by HA and **skips explicit shutdown commands** for those specific VMs.
*   **State Preservation**: By allowing the Proxmox Node shutdown process to handle HA VMs, their desired HA state remains `started`. This ensures they are automatically restarted by the cluster manager when the node comes back online.

### 🛡️ Boot Verification & Recovery
*   **Deep Boot Verification**: The boot process doesn't just send a "Power On" signal anymore. It now actively **monitors the Proxmox API** for up to 10 minutes to verify the host has successfully booted.
*   **Auto-Recovery**: Once the host is detected as online, the system performs a self-healing check:
    *   Ensures all HA resources are set to `started`.
    *   Scans all VMs and explicitly sends a start command to any that remain in a `stopped` state.
    *   This guarantees your services come back up, even if the previous shutdown wasn't perfect.

## 📦 Installation / Upgrade

```bash
git pull origin main
# No new dependencies, but ensure proxmoxer is installed
pip3 install -r requirements.txt
sudo systemctl restart boot-listener
sudo systemctl restart shutdown-listener
```

## 🔗 Links

*   [📜 Full Documentation](https://github.com/tinel-c/ServerBootShutdownManagemement/tree/main/docs)
*   [🐛 Issue Tracker](https://github.com/tinel-c/ServerBootShutdownManagemement/issues)

---
*Maintained by Constantin Bogza & Tinel Clenci*
