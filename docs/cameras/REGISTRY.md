# Cameras — site registry

Canonical list of cameras on the **192.168.2.0/24** LAN. Tapo devices use
**`camera-ping-watchdog.service`** (ICMP health) and Node-RED flows **611–613**.
ONVIF is **on request only** — see [TAPO_CAMERA.md](../TAPO_CAMERA.md).
HomeGuard NVR: [HOMEGUARD_NVR.md](../HOMEGUARD_NVR.md).

## Policy

- **Do not** run continuous ONVIF/snapshot polling (hurts cameras + DVR).
- Watchdog = ICMP ping (~60 s).
- Snapshots = MQTT `command/snapshot` or Watchdog **Capture**.

## Tapo cameras (phase 1)

| # | Name | IP | Model | MAC | MQTT slug |
|---|------|-----|-------|-----|-----------|
| 1 | Back Gate | 192.168.2.34 | C310 | 5C-E9-31-E0-21-93 | `backGate` |
| 2 | Casa Spate | 192.168.2.32 | C310 | 3C-52-A1-80-BA-81 | `casaSpate` |
| 3 | Front House | 192.168.2.36 | C310 | 5C-E9-31-41-4B-83 | `frontHouse` |
| 4 | Gazon Curte | 192.168.2.38 | TC65 | A8-29-48-96-3A-E0 | `gazonCurte` |
| 5 | Gradina Lunca Cetatuii | 192.168.2.37 | C510W | E4-FA-C4-78-F1-C9 | `gradinaLunca` |
| 6 | Small Gate Entrance | 192.168.2.10 | C500 | 3C-52-A1-5A-28-61 | `smallGateEntrance` |
| 7 | Street View Camera | 192.168.2.35 | C310 | 5C-E9-31-E0-34-07 | `streetView` |

Credentials: Tapo **Camera Account** in server `config/.env` only (`CAMERA_N_USER` / `CAMERA_N_PASS`). Placeholders: [config/cameras.env.example](../../config/cameras.env.example).

## Env knobs

| Variable | Default | Meaning |
|----------|---------|---------|
| `CAMERA_PING_INTERVAL_SEC` | `60` | ICMP health interval |
| `CAMERA_PING_TIMEOUT_SEC` | `2` | Per-ping timeout |
| `CAMERA_SNAPSHOT_MAX_WIDTH` | `480` | On-demand JPEG width |
| `CAMERA_SNAPSHOT_DIR` | `/opt/dell_server_management/data/camera-snapshots` | Snapshot files |

`CAMERA_HEALTH_INTERVAL_SEC` is a legacy alias for the ping interval.

## Verify

```bash
sudo venv/bin/python3 scripts/status/camera_connect.py   # ONVIF once (manual)
systemctl status camera-ping-watchdog.service
mosquitto_sub -h localhost -t 'garden/camera/+/health' -v
```
