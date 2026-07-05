# v3.17.0 (2026-07-05) — Camera registry, watchdog thumbnails, 5-minute polling

Documents and deploys **seven Tapo cameras**, adds **live thumbnails** on the Watchdog dashboard, and aligns health/snapshot polling to **5 minutes**. HomeGuard NVR at `192.168.2.59` is documented for follow-up channel import.

## Added

### Camera registry

| # | Name | Slug | IP |
|---|------|------|-----|
| 1 | Back Gate | `backGate` | 192.168.2.34 |
| 2 | Casa Spate | `casaSpate` | 192.168.2.32 |
| 3 | Front House | `frontHouse` | 192.168.2.36 |
| 4 | Gazon Curte | `gazonCurte` | 192.168.2.38 |
| 5 | Gradina Lunca Cetatuii | `gradinaLunca` | 192.168.2.37 |
| 6 | Small Gate Entrance | `smallGateEntrance` | 192.168.2.10 |
| 7 | Street View Camera | `streetView` | 192.168.2.35 |

See [docs/cameras/REGISTRY.md](../cameras/REGISTRY.md).

### Watchdog thumbnails (flow 613)

- `tapo-monitor` writes JPEGs to `data/camera-snapshots/{slug}.jpg`
- Node-RED serves `http://<host>:1880/camera-snapshots/{slug}.jpg`
- MQTT `garden/camera/{slug}/snapshot` carries `image_url` (lightweight JSON)
- Dashboard `/dashboard/watchdog` — camera grid with thumbnails, 10 s UI refresh

### Scripts

| Script | Purpose |
|--------|---------|
| `scripts/status/tapo_snapshot.py` | ONVIF + RTSP/ffmpeg capture, resize, disk save |
| `scripts/status/camera_probe.py` | ONVIF + ARP MAC probe |
| `scripts/status/camera_connect.py` | Test all configured cameras |
| `scripts/status/probe_homeguard_nvr.py` | HomeGuard NVR RTSP/HTTP probe |
| `scripts/status/homeguard_nvr.py` | NVR `/API/*` client (WIP) |

### HomeGuard NVR

- **IP:** `192.168.2.59` — [docs/HOMEGUARD_NVR.md](../HOMEGUARD_NVR.md)
- Per-channel MQTT + Watchdog import pending NVR admin credentials

## Changed

- `CAMERA_HEALTH_INTERVAL_SEC=300` — health + status JSON every 5 min
- `CAMERA_SNAPSHOT_INTERVAL_SEC=300` — thumbnails every 5 min
- Flow **612** camera watchdog timeout: **7 min**
- Flows **611–613** slug labels aligned with registry

## Upgrade (automation server)

```bash
git pull
sudo ./update.sh

# Or deploy camera block only:
sudo python3 scripts/server/apply_cameras_env.py
sudo systemctl restart tapo-monitor.service

node nodered/live-connection/scripts/generate-flow-613.mjs
node nodered/live-connection/scripts/deploy-flow-611.mjs
node nodered/live-connection/scripts/deploy-flow-612.mjs
node nodered/live-connection/scripts/deploy-flow-613.mjs
```

Verify:

```bash
sudo /opt/dell_server_management/venv/bin/python3 scripts/status/camera_connect.py
# Watchdog UI: http://192.168.2.4:1880/dashboard/watchdog
```

## Docs

- [TAPO_CAMERA.md](../TAPO_CAMERA.md), [MQTT_PROTOCOL.md](../MQTT_PROTOCOL.md), [nodered/flows/README.md](../../nodered/flows/README.md)
