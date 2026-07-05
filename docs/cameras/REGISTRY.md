# Camera registry

Canonical list of cameras on the **192.168.2.0/24** LAN. Tapo devices use `tapo-monitor.service` and Node-RED flows **611–613**. See also [HOMEGUARD_NVR.md](../HOMEGUARD_NVR.md) for the NVR at `.59`.

## Tapo cameras (7)

| # | Name | IP | MAC | Model | MQTT slug | Prefix ||---|------|-----|-----|-------|-----------|--------|
| 1 | Back Gate | 192.168.2.34 | `5C:E9:31:E0:21:93` | C310 | `backGate` | `garden/camera/backGate` |
| 2 | Casa Spate | 192.168.2.32 | `3C:52:A1:80:BA:81` | C310 | `casaSpate` | `garden/camera/casaSpate` |
| 3 | Front House | 192.168.2.36 | `5C:E9:31:41:4B:83` | C310 | `frontHouse` | `garden/camera/frontHouse` |
| 4 | Gazon Curte | 192.168.2.38 | `A8:29:48:96:3A:E0` | TC65 | `gazonCurte` | `garden/camera/gazonCurte` |
| 5 | Gradina Lunca Cetatuii | 192.168.2.37 | `E4:FA:C4:78:F1:C9` | C510W | `gradinaLunca` | `garden/camera/gradinaLunca` |
| 6 | Small Gate Entrance | 192.168.2.10 | `3C:52:A1:5A:28:61` | C500 | `smallGateEntrance` | `garden/camera/smallGateEntrance` |
| 7 | Street View Camera | 192.168.2.35 | `5C:E9:31:E0:34:07` | C310 | `streetView` | `garden/camera/streetView` |

> **Note:** IPs `192.168.2.36` and `192.168.2.38` were provided as `182.168.2.x` — corrected to the `192.168.2.x` subnet used on site.

### Per-camera notes

#### 1 — Back Gate (`backGate`)

- **Location:** rear / sliding gate area
- **Hardware:** Tapo C310 @ `192.168.2.34`
- **ONVIF:** port `2020` (enable in Tapo app → Advanced → ONVIF)
- **Credentials:** Camera Account (not Tapo cloud login)

#### 2 — Casa Spate (`casaSpate`)

- **Location:** back of house
- **Hardware:** Tapo C310 @ `192.168.2.32`

#### 3 — Front House (`frontHouse`)

- **Location:** front of house
- **Hardware:** Tapo C310 @ `192.168.2.36`

#### 4 — Gazon Curte (`gazonCurte`)

- **Location:** lawn / yard
- **Hardware:** Tapo TC65 @ `192.168.2.38`
- **Note:** TC65 is a pan/tilt model; confirm ONVIF is enabled. Observed LAN MAC is `A8:29:48:96:3A:E0` (differs from label sticker `A8:23:…` — use ARP). If health probe reports **Authority failure**, recreate the Camera Account in the Tapo app for this device.

#### 5 — Gradina Lunca Cetatuii (`gradinaLunca`)

- **Location:** garden — Lunca Cetatuii
- **Hardware:** Tapo C510W @ `192.168.2.37`

#### 6 — Small Gate Entrance (`smallGateEntrance`)

- **Location:** small gate entry
- **Hardware:** Tapo C500 @ `192.168.2.10`
- **Note:** Previously unreachable from automation server (`No route to host`) — confirm camera is powered and on the same LAN/VLAN as `192.168.2.4`.

#### 7 — Street View Camera (`streetView`)

- **Location:** street-facing yard view
- **Hardware:** Tapo C310 @ `192.168.2.35`

## HomeGuard NVR

| Item | Value |
|------|--------|
| IP | `192.168.2.59` |
| MAC | `00:23:63:91:e6:99` |
| HTTP API | `/API/*` on port 80 |
| RTSP | port 554 |

NVR channels will be added to MQTT and the Watchdog dashboard once local admin credentials are confirmed. See [HOMEGUARD_NVR.md](../HOMEGUARD_NVR.md).

## Polling intervals

| Setting | Default | Purpose |
|---------|---------|---------|
| `CAMERA_HEALTH_INTERVAL_SEC` | `300` | ONVIF health + status JSON |
| `CAMERA_SNAPSHOT_INTERVAL_SEC` | `300` | JPEG thumbnails for Watchdog |

## Health MQTT
| Topic | Payload |
|-------|---------|
| `garden/camera/{slug}/health` | `online` or `offline` (retained) |
| `garden/camera/{slug}/status` | JSON device probe (model, serial, MAC match) |

Watchdog flow **612** uses a **7 minute** timeout (health interval + margin).

## Verify connectivity

On the automation server:

```bash
cd /opt/dell_server_management
sudo /opt/dell_server_management/venv/bin/python3 scripts/status/camera_connect.py
```

Port scan (no credentials):

```bash
python3 scripts/utils/camera_network_scan.py --subnet 192.168.2
```

## Configuration

Copy from [config/cameras.env.example](../../config/cameras.env.example) into `config/.env`, or run `scripts/server/apply_cameras_env.py` on the server.

Deploy Node-RED after slug changes:

```bash
node nodered/live-connection/scripts/generate-flow-613.mjs
node nodered/live-connection/scripts/deploy-flow-611.mjs
node nodered/live-connection/scripts/deploy-flow-612.mjs
node nodered/live-connection/scripts/deploy-flow-613.mjs
```