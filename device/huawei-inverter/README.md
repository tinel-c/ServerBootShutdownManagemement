# Huawei SUN2000 inverter — connection and data access



Documentation for integrating a **Huawei SUN2000** grid-tie PV inverter with this automation stack.



**This installation:** USB WiFi dongle on the automation server (`192.168.2.4`) connects to the inverter’s built-in WiFi AP for Modbus TCP polling. The server stays on the main LAN via Ethernet (`enp1s0`) for MQTT, Node-RED, and Telegram.



Planned use in this repo: solar production monitoring under the **Energy Management** domain (Node-RED flows `820–829`, see [AUTOMATION_ARCHITECTURE.md](../../docs/AUTOMATION_ARCHITECTURE.md)).



---



## Folder layout



```

device/huawei-inverter/

├── config/.env.example        # Template (copy to config/.env)

├── config/netplan-wifi.example.yaml

├── lib/huawei_modbus.py       # Modbus reader

├── scripts/modbus_probe.py    # Connectivity test

└── README.md

```



Mirrors [device/victron-multiplus-ii](../victron-multiplus-ii/) — probe → publisher → MQTT → Node-RED → Telegram → watchdog.



---



## Site connection (this install)



| Item | Value |

|------|--------|

| Server | `192.168.2.4` (Ethernet `enp1s0`) |

| USB WiFi | `wlxec750caf06b1` |

| Inverter AP SSID | `SUN2000-HV2310027721` |

| AP password | Set in `config/.env` only (default factory password is often `Changeme`) |

| Inverter Modbus IP | `192.168.200.1` |

| Modbus port | `6607` (AP mode; try `502` on older firmware) |

| Modbus unit ID | `0` (AP mode; SDongle LAN uses `1`) |



```

[Automation server 192.168.2.4]

  enp1s0 ──────────────► LAN / MQTT / Node-RED

  wlx USB WiFi ────────► SUN2000 AP (192.168.200.0/24)

                              │

                         192.168.200.1 Modbus TCP

```



**Important:** Enable **Modbus TCP** in the FusionSolar / SUN2000 installer app if reads time out (Communication configuration → Modbus TCP unrestricted).



---



## Quick start



1. Copy [config/.env.example](config/.env.example) to `config/.env` and fill WiFi + Modbus settings.

2. On the server, configure USB WiFi (once):



   ```bash

   sudo ~/ServerBootShutdownManagemement/scripts/server/setup_huawei_wifi.sh

   ```



   Or merge [config/netplan-wifi.example.yaml](config/netplan-wifi.example.yaml) into `/etc/netplan/` manually.



3. Verify link and Modbus:



   ```bash

   ping -c1 192.168.200.1

   python device/huawei-inverter/scripts/modbus_probe.py

   ```



---



## Network prerequisites



| Item | WiFi AP mode | SDongle LAN |

|------|----------------|-------------|

| Path | Server USB WiFi → inverter AP | SDongle on same LAN as server |

| Inverter IP | `192.168.200.1` | DHCP on your router |

| Modbus port | **6607** (typical) | **502** |

| Unit ID | **0** | **1** |

| Dual-homed server | Yes — keep Ethernet as default route | No extra WiFi needed |



---



## MQTT topic prefix (planned)



| Setting | Default |

|---------|---------|

| Prefix | `energy/huawei` |

| Full status snapshot | `energy/huawei/status` |



See [MQTT_PROTOCOL.md](../../docs/MQTT_PROTOCOL.md) (Huawei section — to be added).



---



## Integration roadmap



| Step | Status |

|------|--------|

| Device folder + config template | Done |

| Modbus probe script | Done |

| USB WiFi netplan setup script | Done |

| MQTT publisher + systemd service | Done |

| Node-RED dashboard (`821-*`) | Done |

| Telegram commands (`822-*`) | Done |

| Device watchdog on `energy/huawei/status` | Done |



---



## Troubleshooting



| Symptom | Check |

|---------|--------|

| `192.168.200.1` unreachable | USB WiFi down; run `setup_huawei_wifi.sh`; `ip -br addr` |

| TCP OK, Modbus timeout | Modbus TCP disabled in FusionSolar app; wrong port (try 6607 vs 502) |

| Modbus error / no data | Wrong unit ID (0 for AP, 1 for SDongle LAN) |

| Server loses main LAN | WiFi must use `route-metric: 600` and `optional: true` in netplan |
| WiFi UP but no AP association | Install `wpasupplicant` (handled by `setup_huawei_wifi.sh`) |

---

## Live test

**Verified:** 2026-07-04 on `192.168.2.4` → AP `SUN2000-HV2310027721` → Modbus `192.168.200.1:6607` (unit 0).

| Setting | Value |
|---------|--------|
| Model | SUN2000-6KTL-L1 |
| Serial | HV2310027721 |
| USB WiFi | TL-WN722N → `192.168.200.2/24` |

Sample probe: active power **211 W**, daily yield **45.63 kWh**, grid **50.01 Hz**.

Run probe on server: `source /opt/dell_server_management/venv/bin/activate && python device/huawei-inverter/scripts/modbus_probe.py`

---

## PV forecast model (Node-RED flow 821)

Maps Open-Meteo shortwave radiation to expected inverter power for a **20-panel** array: **string 1 west**, **string 2 east** (10 panels each).

```text
P_est = P_rated × (G / 1000) × η
P_est_string1 = P_est × w_west / (w_east + w_west)
P_est_string2 = P_est × w_east / (w_east + w_west)
```

- **G** from `energy/victron/forecast/solar/current` (same Open-Meteo publisher as Victron)
- **Actual** from string V×I in `energy/huawei/status`
- Python reference: [lib/pv_forecast_model.py](lib/pv_forecast_model.py)
- Dashboard: [docs/ENERGY_NODE_RED.md](../../docs/ENERGY_NODE_RED.md)

---

*Last updated 2026-07-05 — PV forecast model on flow 821.*

