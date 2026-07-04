# Victron MultiPlus-II — connection and data access

Documentation for integrating a **Victron MultiPlus-II** inverter/charger with this automation stack. The MultiPlus-II itself has no Ethernet or Modbus port; all programmatic access goes through a **GX device** (Cerbo GX, Venus GX, or the built-in GX in a **MultiPlus-II GX** model).

Planned use in this repo: energy monitoring and control under the **Energy Management** domain (Node-RED flows `80x`, see [AUTOMATION_ARCHITECTURE.md](../../docs/AUTOMATION_ARCHITECTURE.md)).

---

## Table of contents

1. [Hardware variants](#1-hardware-variants)
2. [Physical wiring](#2-physical-wiring)
3. [Network prerequisites](#3-network-prerequisites)
4. [Integration methods (overview)](#4-integration-methods-overview)
5. [Method A — Modbus TCP (recommended for polling)](#5-method-a--modbus-tcp-recommended-for-polling)
6. [Method B — MQTT on the GX (recommended for event-driven)](#6-method-b--mqtt-on-the-gx-recommended-for-event-driven)
7. [Method C — VRM portal (cloud)](#7-method-c--vrm-portal-cloud)
8. [Key data points for MultiPlus-II](#8-key-data-points-for-multiplus-ii)
9. [Example: read inverter state (Python)](#9-example-read-inverter-state-python)
10. [Example: MQTT subscription](#10-example-mqtt-subscription)
11. [Integration with this automation repo](#11-integration-with-this-automation-repo)
12. [Limitations and safety](#12-limitations-and-safety)
13. [Troubleshooting](#13-troubleshooting)
14. [Official references](#14-official-references)

---

## 1. Hardware variants

| Model | GX built-in | Typical automation path |
|-------|-------------|-------------------------|
| **MultiPlus-II** (standalone) | No | Connect to external **Cerbo GX** (or Venus GX) via VE.Bus |
| **MultiPlus-II GX** | Yes (on-board GX card) | Use GX Ethernet/Wi‑Fi directly; optional external Cerbo for extra I/O |
| **EasySolar-II GX** | Yes | Same Modbus/MQTT model as MultiPlus-II GX (different default Unit ID) |

Firmware on VE.Bus products must be **≥ 111** for Cerbo GX compatibility.

---

## 2. Physical wiring

### MultiPlus-II + external Cerbo GX

1. Connect **one VE.Bus port** on the Cerbo GX to the **VE.Bus port** on the MultiPlus-II using a standard **RJ45 UTP** cable (Victron-approved cable recommended).
2. Use either VE.Bus socket on the Cerbo — they are equivalent for a single inverter.
3. Connect the Cerbo GX to your LAN (Ethernet or Wi‑Fi).
4. **Do not** connect to the Remote panel socket on a VE.Bus BMS — use the MultiPlus/Quattro VE.Bus socket instead.

### MultiPlus-II GX (built-in GX)

The GX card shares the VE.Bus connection internally. Connect the unit to LAN via the GX Ethernet port. For parallel or three-phase stacks, Victron recommends MultiPlus-II **GX** models with only **one** external control path (one GX).

### Remote On/Off

Unlike older Multi/Quattro units, **MultiPlus-II supports Remote On/Off together with a GX device**. The factory jumper (left–middle terminal) can remain, or a remote switch can be wired per the product manual.

### Power and battery

- DC battery cables sized per Victron manual (sum of parallel unit cross-sections rules apply).
- For ESS / lithium with BMS: enable **DVCC** on the GX and verify the battery appears in the device list before relying on SoC-driven automation.

Further wiring detail: [Cerbo GX — Connecting Victron products](https://www.victronenergy.com/media/pg/Cerbo_GX/en/connecting-victron-products.html).

---

## 3. Network prerequisites

| Item | Value |
|------|--------|
| GX device on same LAN as automation server (or routable) | Required |
| Static or DHCP reservation for GX IP | Strongly recommended |
| Modbus TCP port | **502** (disabled by default) |
| MQTT port (local) | **1883** (TLS **8883** if enabled); disabled by default for plain TCP |
| VRM Portal ID | Required for MQTT topic paths; find under **Settings → VRM online portal → VRM Portal ID** |

Copy [config/.env.example](config/.env.example) to `config/.env` (gitignored) and fill in your GX address, Unit ID, and portal ID.

---

## 4. Integration methods (overview)

The GX acts as a **protocol gateway**: it exposes data from the MultiPlus-II (VE.Bus service `com.victronenergy.vebus`) over the network.

| Method | Protocol | Best for | Write support |
|--------|----------|----------|---------------|
| **Modbus TCP** | TCP 502 | Node-RED Modbus nodes, Python `pymodbus`, PLCs | Limited (mode, ESS setpoints, relays — not VEConfigure settings) |
| **MQTT (FlashMQ)** | TCP 1883 | Real-time dashboards, Node-RED `mqtt in`, bridging to project MQTT broker | Some paths (mode, current limit, ESS) |
| **VRM API** | HTTPS | Historical data, remote sites, mobile | Portal permissions dependent |

**You cannot** talk Modbus or MQTT directly to the MultiPlus-II without a GX (or equivalent VE.Bus monitor).

Official overview: [Data communication whitepaper (PDF)](https://www.victronenergy.com/upload/documents/Whitepaper-Data-communication-with-Victron-Energy-products_EN.pdf).

---

## 5. Method A — Modbus TCP (recommended for polling)

### Enable on the GX

**Settings → Services → Modbus TCP → Enabled**

Confirm the inverter appears under **Settings → Services → Modbus TCP → Available services** (lists each service name and **Unit ID**).

### Addressing model

Modbus requests use two fields:

| Field | Meaning |
|-------|---------|
| **Unit ID** (slave address) | Selects which connected device (MultiPlus-II = `com.victronenergy.vebus`) |
| **Register address** | Selects the parameter (voltage, power, state, …) |

**Function codes:** 3 (Read Holding), 4 (Read Input), 6 (Write Single), 16 (Write Multiple). FC 3 and 4 behave the same on Victron.

**Scaling:** Raw register value ÷ scale factor = engineering value (e.g. register `3` raw `2302` ÷ 10 → **230.2 V**).

### Unit ID — do not assume 246

Unit IDs depend on **which GX** and **which port** the inverter uses. Always verify on your installation.

| GX hardware | VE.Bus port | Typical Unit ID | Device instance |
|-------------|-------------|-----------------|-----------------|
| Cerbo GX | VE.Bus (ttyS4) | **227** | 276 |
| CCGX / Venus GX | VE.Bus (ttyO1) | **246** | 257 |
| MultiPlus-II GX / EasySolar-II GX | Internal VE.Bus | **228** | 275 |

Source: [unitid2di.csv](https://github.com/victronenergy/dbus_modbustcp/blob/master/unitid2di.csv) (mirrors the Excel “Unit ID mapping” tab).

**System-wide data** (battery summary, grid power, consumption totals): Unit ID **100**, service `com.victronenergy.system`.

### Register map (VE.Bus / MultiPlus-II)

Service: **`com.victronenergy.vebus`** — registers **3–60+** (not all exist on every product).

| Reg | D-Bus path | Description | Type | Scale | R/W |
|-----|------------|-------------|------|-------|-----|
| 3 | `/Ac/ActiveIn/L1/V` | AC input voltage L1 | uint16 | 10 | R |
| 6 | `/Ac/ActiveIn/L1/I` | AC input current L1 | int16 | 10 | R |
| 12 | `/Ac/ActiveIn/L1/P` | AC input power L1 | int16 | 0.1 | R |
| 15 | `/Ac/Out/L1/V` | AC output voltage L1 | uint16 | 10 | R |
| 18 | `/Ac/Out/L1/I` | AC output current L1 | int16 | 10 | R |
| 23 | `/Ac/Out/L1/P` | AC output power L1 | int16 | 0.1 | R |
| 26 | `/Dc/0/Voltage` | Battery voltage | uint16 | 100 | R |
| 27 | `/Dc/0/Current` | Battery current | int16 | 10 | R |
| 28 | `/Ac/NumberOfPhases` | Phase count | uint16 | 1 | R |
| 29 | `/Ac/ActiveIn/ActiveInput` | Active AC input (0=in1, 1=in2, 240=disconnected) | uint16 | 1 | R |
| 30 | `/Soc` | State of charge | uint16 | 10 | W |
| 31 | `/State` | Inverter/charger state (see below) | uint16 | 1 | R |
| 32 | `/VebusError` | VE.Bus error code | uint16 | 1 | R |
| 33 | `/Mode` | 1=Charger Only, 2=Inverter Only, 3=On, 4=Off | uint16 | 1 | W |
| 34–36 | `/Alarms/*` | Temperature, battery, overload | uint16 | 1 | R |
| 64 | `/Alarms/GridLost` | Grid lost alarm (0=ok, 2=alarm) | uint16 | 1 | R |
| 22 | `/Ac/ActiveIn/CurrentLimit` | Input current limit | int16 | 10 | W |

**Inverter state (`/State`, register 31):**

| Value | State |
|-------|--------|
| 0 | Off |
| 1 | Low Power |
| 2 | Fault |
| 3 | Bulk |
| 4 | Absorption |
| 5 | Float |
| 6 | Storage |
| 7 | Equalize |
| 8 | Passthru |
| 9 | Inverting |
| 10 | Power assist |
| 11 | Power supply |
| 252 | External control |

Full register list: [CCGX-Modbus-TCP-register-list.xlsx](https://github.com/victronenergy/dbus_modbustcp/blob/master/CCGX-Modbus-TCP-register-list.xlsx) or [attributes.csv](https://github.com/victronenergy/dbus_modbustcp/blob/master/attributes.csv).

### System registers (Unit ID 100)

Useful for ESS dashboards and battery-centric automation:

| Reg | Path | Description | Scale |
|-----|------|-------------|-------|
| 840 | `/Dc/Battery/Voltage` | Battery voltage | 10 |
| 841 | `/Dc/Battery/Current` | Battery current | 10 |
| 842 | `/Dc/Battery/Power` | Battery power (W) | 1 |
| 843 | `/Dc/Battery/Soc` | State of charge (%) | 1 |
| 820–822 | `/Ac/Grid/Lx/Power` | Grid power per phase | 1 |
| 817–819 | `/Ac/Consumption/Lx/Power` | Consumption per phase | 1 |
| 826 | `/Ac/ActiveIn/Source` | 0=N/A, 1=Grid, 2=Generator, 3=Shore, 240=Not connected | 1 |
| 806–807 | `/Relay/0/State`, `/Relay/1/State` | Programmable relays | 1 (R/W) |

### Modbus read example (register 3 = input voltage L1)

```
Host:    <GX_IP>
Port:    502
Unit ID: <your_vebus_unit_id>   # e.g. 227, 228, or 246
FC:      3 or 4
Address: 3
Count:   1
Result:  raw_value / 10 → volts AC
```

Official worked example: [GX Modbus-TCP Manual — mapping example](https://www.victronenergy.com/live/ccgx:modbustcp_faq).

---

## 6. Method B — MQTT on the GX (recommended for event-driven)

Since **Venus OS 3.20+**, the GX runs **FlashMQ** with the **dbus-flashmq** plugin (replacing Mosquitto + dbus-mqtt). Messages are **not retained**; clients must use the **keep-alive** handshake.

### Enable on the GX

**Settings → Services → MQTT → Enabled**

Enable **MQTT on LAN** (plain TCP 1883) if clients on your automation network need access. Authentication may use the VNC password when configured.

### Topic layout

**Notifications (GX → client):**

```
N/<portal_id>/<service>/<instance>/<dbus_path>
```

Example — battery voltage:

```
Topic:   N/e0ff50a097c0/system/0/Dc/Battery/Voltage
Payload: {"value": 27.64}
```

Example — VE.Bus AC output power L1 (instance from your device list, often `276` on Cerbo):

```
Topic:   N/<portal_id>/vebus/276/Ac/Out/L1/P
Payload: {"value": 450.0}
```

**Read / refresh requests (client → GX):**

```
R/<portal_id>/<dbus_path>
```

Wildcards are **not** supported on read requests.

### Keep-alive procedure (required)

1. Subscribe to `N/<portal_id>/#`
2. Publish **empty** payload to `R/<portal_id>/keepalive` → triggers full data publish
3. Wait for `N/<portal_id>/full_publish_completed`
4. Every **30 seconds**, publish to `R/<portal_id>/keepalive`:

```json
{"keepalive-options": ["suppress-republish"]}
```

Without step 2, you may see no data after subscribing (no retained messages).

### Discover VE.Bus instance for MQTT

Subscribe after keep-alive, or read:

```
N/<portal_id>/system/0/VebusService
```

Use the returned service name / instance in `vebus/<instance>/…` topics. See [venus-html5-app TOPICS.md](https://github.com/victronenergy/venus-html5-app/blob/master/TOPICS.md).

### Bridge to project MQTT broker

This repo’s automation server already runs an MQTT broker (see [MQTT_PROTOCOL.md](../../docs/MQTT_PROTOCOL.md)). Typical pattern:

1. Node-RED or a small bridge service subscribes to the GX on `N/<portal_id>/#`
2. Normalizes readings to project topics (e.g. `energy/victron/battery/soc`)
3. Republishes to the central broker at `192.168.2.4` (or your `MQTT_BROKER_HOST`)

---

## 7. Method C — VRM portal (cloud)

If the GX is linked to [VRM](https://vrm.victronenergy.com/):

- **Dashboard & history** — no local integration required
- **VRM MQTT** — TLS broker farm; same topic layout as local MQTT, encrypted; requires site in your VRM account and appropriate permissions (Full Control for writes)
- **VRM API** — REST access for sites, alarms, and downloads ([VRM API documentation](https://vrm-api-docs.victronenergy.com/))

Use VRM when the GX is not on the same LAN as the automation server. Prefer local Modbus/MQTT when on-LAN latency and reliability matter.

---

## 8. Key data points for MultiPlus-II

| Use case | Modbus (Unit = vebus) | Modbus (Unit = 100 system) | MQTT path (example) |
|----------|----------------------|----------------------------|---------------------|
| Battery voltage | Reg 26 | Reg 840 | `…/system/0/Dc/Battery/Voltage` |
| Battery SoC | Reg 30 (if exposed) | Reg 843 | `…/system/0/Dc/Battery/Soc` |
| Inverter state | Reg 31 | — | `…/vebus/<inst>/State` |
| Grid lost | Reg 64 | — | `…/vebus/<inst>/Alarms/GridLost` |
| AC out power | Reg 23–25 | Reg 878+ (consumption) | `…/vebus/<inst>/Ac/Out/L1/P` |
| ESS grid power | — | Reg 820–822 | `…/system/0/Ac/Grid/L1/Power` |
| On/Off/Charge-only mode | Reg 33 (write) | — | `…/vebus/<inst>/Mode` |
| Input current limit | Reg 22 (write) | — | `…/vebus/<inst>/Ac/In/0/CurrentLimit` |

Poll interval guidance: **2–5 s** for UI; **10–60 s** for logging; avoid sub-second polling on Modbus (GX is shared with GUI and VRM).

---

## 9. Example: read inverter state (Python)

Requires: `pip install pymodbus`

```python
from pymodbus.client import ModbusTcpClient

GX_HOST = "192.168.x.x"      # Cerbo / MultiPlus-II GX IP
UNIT_ID = 227                  # Verify on your GX Modbus → Available services
REG_STATE = 31

client = ModbusTcpClient(GX_HOST, port=502)
client.connect()

result = client.read_input_registers(REG_STATE, count=1, slave=UNIT_ID)
if result.isError():
    raise RuntimeError(result)

state = result.registers[0]
states = {
    0: "Off", 3: "Bulk", 4: "Absorption", 5: "Float",
    8: "Passthru", 9: "Inverting", 2: "Fault",
}
print(f"Inverter state: {states.get(state, state)}")

client.close()
```

Read input voltage L1 (register 3, scale ÷10):

```python
raw = client.read_input_registers(3, count=1, slave=UNIT_ID).registers[0]
print(f"AC in L1: {raw / 10:.1f} V")
```

---

## 10. Example: MQTT subscription

Requires: `mosquitto-clients` or any MQTT library.

```bash
PORTAL_ID="your_portal_id"
GX_IP="192.168.x.x"

# Terminal 1 — subscribe
mosquitto_sub -h "$GX_IP" -t "N/${PORTAL_ID}/#" -v

# Terminal 2 — initial keep-alive (empty payload)
mosquitto_pub -h "$GX_IP" -t "R/${PORTAL_ID}/keepalive" -m ""

# Terminal 2 — repeat every 30s to maintain stream without full republish
mosquitto_pub -h "$GX_IP" -t "R/${PORTAL_ID}/keepalive" \
  -m '{"keepalive-options": ["suppress-republish"]}'
```

---

## 11. Integration with this automation repo

| Layer | Location | Notes |
|-------|----------|-------|
| Config template | [config/.env.example](config/.env.example) | GX IP, Unit IDs, portal ID |
| Modbus probe | [scripts/modbus_probe.py](scripts/modbus_probe.py) | Read-only connectivity test |
| MQTT publisher | [scripts/victron_mqtt_publisher.py](scripts/victron_mqtt_publisher.py) | Polls Modbus every 10s → MQTT |
| Node-RED dashboard | [nodered/flows/811-victron-energy-status.json](../../nodered/flows/811-victron-energy-status.json) | Subscribes `energy/victron/status` → Dashboard 2.0 |
| Solar forecast | [scripts/victron_solar_forecast_publisher.py](scripts/victron_solar_forecast_publisher.py) | Open-Meteo → `energy/victron/forecast/solar/*` |
| systemd (Modbus) | [systemd/victron-mqtt-publisher.service](../../systemd/victron-mqtt-publisher.service) | Install on automation server |
| systemd (forecast) | [systemd/victron-solar-forecast-publisher.service](../../systemd/victron-solar-forecast-publisher.service) | Open-Meteo forecast service |
| Energy flows (planned) | `nodered/flows/80x-*.json` | Domain 80–89 in architecture doc |
| Energy dashboard | `800-energy-base-config.json`, `811-victron-energy-status.json` | [ENERGY_NODE_RED.md](../../docs/ENERGY_NODE_RED.md) |
| Central MQTT | `MQTT_BROKER_HOST` in root [config/.env.example](../../config/.env.example) | Publisher uses automation broker |
| Node-RED Modbus | `node-red-contrib-modbus` | TCP to GX:502, unit ID from GX menu |

### MQTT topics on the automation broker

The publisher posts to prefix **`energy/victron`** (override: `VICTRON_MQTT_PREFIX`). Full specification: **[docs/MQTT_PROTOCOL.md](../../docs/MQTT_PROTOCOL.md#victron-energy-topics-domain-energyvictron)**.

| Topic | Payload | Notes |
|-------|---------|-------|
| `energy/victron/status` | JSON | Full snapshot each poll |
| `energy/victron/battery/voltage` | number (V) | |
| `energy/victron/battery/soc` | integer (%) | |
| `energy/victron/battery/power` | signed int (W) | + = charging |
| `energy/victron/grid/power_l1` | signed int (W) | + = import |
| `energy/victron/pv/dc_power` | int (W) | |
| `energy/victron/pv/dc_current` | number (A) | |
| `energy/victron/pv/ac_output_l1` | int (W) | AC-coupled solar on output |
| `energy/victron/pv/ac_grid_l1` | int (W) | AC-coupled solar on grid |
| `energy/victron/load/consumption_l1` | int (W) | |
| `energy/victron/load/output_l1` | signed int (W) | |
| `energy/victron/load/input_l1` | signed int (W) | |
| `energy/victron/inverter/ac_in_voltage_l1` | number (V) | |
| `energy/victron/inverter/ac_in_power_l1` | signed int (W) | |
| `energy/victron/inverter/ac_out_power_l1` | signed int (W) | |
| `energy/victron/inverter/dc_voltage` | number (V) | |
| `energy/victron/inverter/state` | string | e.g. `Passthru`, `Inverting` |
| `energy/victron/inverter/state_code` | integer | VE.Bus register 31 |
| `energy/victron/inverter/grid_lost` | boolean | |
| `energy/victron/solar/*` | scalars | Only if MPPT found on Modbus |
| `energy/victron/pvinverter/*` | scalars | Only if `VICTRON_PVINVERTER_UNIT_ID` set |

Per-metric topics use **plain text** payloads; only `energy/victron/status` is JSON. Poll interval default **10 s**; QoS **1**; not retained.

### Automation MQTT (load headroom)

| Topic | Description |
|-------|-------------|
| `energy/victron/automation/headroom_w` | PV − consumption (W); **positive = surplus** |
| `energy/victron/automation/can_add_load` | `True` / `False` — allow discretionary loads (AC, etc.) |
| `energy/victron/automation/pv_power_w` | PV value used in calculation |
| `energy/victron/automation/consumption_l1_w` | Consumption L1 mirror |

Set `VICTRON_AUTOMATION_MIN_HEADROOM_W` (default `0`) for hysteresis.

### Solar forecast MQTT (Open-Meteo, Lunca Cetătui)

| Topic | Description |
|-------|-------------|
| `energy/victron/forecast/solar/current` | Current irradiance JSON |
| `energy/victron/forecast/solar/hourly` | 48 h hourly forecast JSON |
| `energy/victron/forecast/solar/daily` | Multi-day daily sums JSON |
| `energy/victron/forecast/solar/radiation_wm2` | Current W/m² (scalar) |
| `energy/victron/forecast/solar/today_sum_kwh_m2` | Today forecast kWh/m² |

### Run the MQTT publisher

1. Copy [config/.env.example](config/.env.example) → `config/.env` (Cerbo IP, Unit IDs).
2. Ensure root [config/.env](../../config/.env) has `MQTT_BROKER_HOST`, credentials.
3. **Server deploy:** [docs/developer/SERVER_DEPLOY.md](../../docs/developer/SERVER_DEPLOY.md) — grant temp sudo on `192.168.2.4`, then deploy.
4. Test one cycle (on server or dev PC with Cerbo reachable):

```bash
python device/victron-multiplus-ii/scripts/victron_mqtt_publisher.py --once
```

5. Deploy to automation server (`192.168.2.4`):

```powershell
# Windows — from repo root
.\scripts\server\setup_ssh_key.ps1          # once per PC
.\scripts\server\deploy_victron_remote.ps1  # sync + install service
```

```bash
# Linux / macOS
./scripts/server/setup_ssh_key.sh
./scripts/server/deploy_victron_remote.sh
```

Or manually on the server after `ssh serverside`:

```bash
cd ~/ServerBootShutdownManagemement
sudo ./install_victron_service.sh
```

Monitor on the broker:

```bash
mosquitto_sub -h localhost -t 'energy/victron/#' -v
```

Import Node-RED flows and open **Dashboard → Energy**: see [docs/ENERGY_NODE_RED.md](../../docs/ENERGY_NODE_RED.md).

---

## 12. Limitations and safety

- **No VEConfigure settings over Modbus** — absorption voltage, ESS assistant install, grid code, etc. require VEConfigure (MK3-USB or VRM remote console), not Modbus.
- **Parallel / three-phase VE.Bus stacks** — individual units cannot be addressed separately; use system totals and per-phase registers.
- **Unit IDs are stable** across reboots but must be verified after hardware changes.
- **Writes affect real hardware** — mode changes, current limits, and ESS setpoints can switch loads or affect grid feed-in. Gate write access behind authentication and explicit automation rules.
- **ESS modes 2 & 3** — additional Modbus registers under Hub4; see [ESS mode 2 and 3 manual](https://www.victronenergy.com/live/ess:ess_mode_2_and_3).

---

## 13. Troubleshooting

| Symptom | Check |
|---------|--------|
| Connection refused on 502 | Modbus TCP disabled; wrong IP; firewall |
| Modbus error 0x0B (GatewayTargetDeviceFailedToRespond) | Wrong Unit ID — open **Available services** on GX |
| Modbus error 0x0A (GatewayPathUnavailable) | Unit ID valid but device offline — VE.Bus cable, inverter off |
| Modbus error 0x02 (IllegalDataAddress) | Register not supported on this product — consult Excel map |
| MQTT connects but no messages | Missing keep-alive to `R/<portal_id>/keepalive` |
| Wrong scaling | Apply **scale** column from register list (÷10, ÷100, ×0.1, etc.) |
| Last Modbus error on GX | **Settings → Services → Modbus TCP** shows last fault |

GX Modbus log (SSH as root): `cat /var/log/dbus-modbustcp/current | tai64nlocal`

Community support: [Victron Modifications forum](https://community.victronenergy.com/spaces/31/index.html).

---

## Live test

**Verified:** 2026-07-04 from Windows dev PC → Cerbo GX `192.168.2.205:502` (Modbus TCP enabled).

| Setting | Value |
|---------|-------|
| VE.Bus Unit ID | **227** (confirmed — no adjustment needed) |
| System Unit ID | **100** |

Sample readings (`python device/victron-multiplus-ii/scripts/modbus_probe.py`):

| Metric | Value |
|--------|-------|
| Battery voltage | 53.7 V |
| Battery SoC | 90 % |
| Battery power | 896 W |
| Grid L1 power | -10 W |
| AC input L1 | 228.4 V |
| DC voltage | 53.86 V |
| Inverter state | Bulk |
| Grid lost alarm | No alarm |

Re-run the probe anytime after updating [config/.env](config/.env).

---

## 14. Official references

| Resource | URL |
|----------|-----|
| GX Modbus-TCP manual | https://www.victronenergy.com/live/ccgx:modbustcp_faq |
| Modbus register list (Excel) | https://github.com/victronenergy/dbus_modbustcp/blob/master/CCGX-Modbus-TCP-register-list.xlsx |
| Register list (CSV) | https://github.com/victronenergy/dbus_modbustcp/blob/master/attributes.csv |
| Unit ID mapping (CSV) | https://github.com/victronenergy/dbus_modbustcp/blob/master/unitid2di.csv |
| dbus-flashmq (MQTT) | https://github.com/victronenergy/dbus-flashmq |
| D-Bus service spec | https://github.com/victronenergy/venus/wiki/dbus |
| Data communication whitepaper | https://www.victronenergy.com/upload/documents/Whitepaper-Data-communication-with-Victron-Energy-products_EN.pdf |
| Cerbo GX manual (PDF) | https://www.victronenergy.com/upload/documents/Cerbo_GX/140558-Ekrano_GX__Venus_GX__Cerbo_GX__Cerbo-S_GX_Manual-pdf-en.pdf |
| MultiPlus-II GX manual (PDF) | https://www.victronenergy.com/upload/documents/MultiPlus-II_4k5_6k5_GX/2983-MultiPlus-II_GX-pdf-en.pdf |
| Connecting Victron products | https://www.victronenergy.com/media/pg/Cerbo_GX/en/connecting-victron-products.html |

---

*Last reviewed against Victron documentation and Venus OS 3.20+ MQTT (FlashMQ) behaviour.*
