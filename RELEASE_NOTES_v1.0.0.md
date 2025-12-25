# 🚀 v1.0.0: Multi-Server MQTT Management System

We are excited to announce the first stable release of the **Server Remote Management System**! This release brings unified power management for mixed server environments (Dell & HP) controlled via a lightweight MQTT interface.

## 🌟 Key Features

*   **Multi-Server Support**: Seamlessly manage **Dell T310** (IPMI) and **HP DL360p** (iLO) servers in the same ecosystem.
*   **Unified MQTT API**: Standardized topics for boot, shutdown, and status monitoring across different hardware.
*   **Protocol Support**:
    *   🔌 **IPMI** (Dell T310)
    *   ⚡ **HP iLO** (HP DL360p)
    *   🌐 **Wake-on-LAN** (Universal)
*   **Secure Configuration**: 100% environment-variable based config for credentials and secrets.
*   **Status Monitoring**: Real-time health and power status reporting.

## 📋 Technical Stack

*   **Language**: Python 3.8+
*   **Messaging**: MQTT (Mosquitto recommended)
*   **Libraries**: `paho-mqtt`, `python-hpilo`, `ipmitool`

## 📦 Installation

```bash
git clone https://github.com/tinel-c/ServerBootShutdownManagemement.git
cd ServerBootShutdownManagemement
sudo ./install.sh
```

## ⚙️ Quick Configuration

Update your `.env` file:

```env
MQTT_BROKER_HOST=localhost
T310_IPMI_PASSWORD=secret
DL360P_ILO_PASSWORD=secret
```

## 🔗 Links

*   [📜 Full Documentation](https://github.com/tinel-c/ServerBootShutdownManagemement/tree/main/docs)
*   [🐛 Issue Tracker](https://github.com/tinel-c/ServerBootShutdownManagemement/issues)

---
*Maintained by Constantin Bogza & Tinel Clenci*
