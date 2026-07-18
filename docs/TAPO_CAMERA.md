# Tapo Camera — ICMP watchdog & on-demand ONVIF

Tapo cameras are **not** continuously polled via ONVIF. Continuous ONVIF
PullPoint / periodic snapshots overload the cameras and make the HomeGuard DVR
unresponsive.

**Default:** ICMP ping health for the watchdog.  
**ONVIF / RTSP:** only when explicitly requested (MQTT command or Watchdog
**Capture** button).

## Data flow

```text
Tapo camera (LAN ICMP)
        │
        ▼
camera-ping-watchdog.service  (scripts/status/camera_ping_watchdog.py)
        │
        ▼
Mosquitto MQTT
  • garden/camera/{slug}/health   ← retained online|offline (ICMP, ~60 s)
  • garden/camera/{slug}/status   ← JSON (method: icmp_ping)
  • garden/camera/{slug}/snapshot ← only after command/snapshot
        │
        ▼
Node-RED flow 611  — dashboard (health + optional events if published)
Node-RED flow 612  — watchdog (3 min timeout on health)
Node-RED flow 613  — Watchdog UI + Capture button + HTTP JPEG serve
```

## Why no continuous ONVIF

Periodic ONVIF GetSnapshotUri / PullPoint from `tapo-monitor` stressed the
camera LAN path and caused the DVR at `192.168.2.59` to stop responding.
Policy (remember across sessions):

1. **Never** run a continuous ONVIF/snapshot poller against site cameras.
2. Watchdog health = **ICMP ping** only.
3. ONVIF/RTSP = **on request** (`command/snapshot` or `command/probe`).

## Prerequisites

### Tapo app (per camera)

1. **Enable ONVIF** — only needed for on-demand snapshots/probes
2. **Create Camera Account** — Advanced → Camera Account  
   Credentials live only in server `config/.env` (see [cameras.env.example](../config/cameras.env.example))

### Automation server

```bash
CAMERA_PING_INTERVAL_SEC=60
CAMERA_PING_TIMEOUT_SEC=2
CAMERA_SNAPSHOT_MAX_WIDTH=480
CAMERA_SNAPSHOT_DIR=/opt/dell_server_management/data/camera-snapshots

CAMERA_1_NAME="Back Gate"
CAMERA_1_IP=192.168.2.34
# ... see docs/cameras/REGISTRY.md
```

Legacy `CAMERA_HEALTH_INTERVAL_SEC` is still read as a fallback for the ping
interval if `CAMERA_PING_INTERVAL_SEC` is unset.

```bash
sudo ./install.sh   # enables camera-ping-watchdog.service
sudo systemctl disable --now tapo-monitor.service   # retired
sudo systemctl enable --now camera-ping-watchdog.service
```

Import/deploy flows **611**, **612**, **613**.

## MQTT topics

| Topic | Payload | Notes |
|-------|---------|-------|
| `garden/camera/{slug}/health` | `online` / `offline` | Retained; ICMP every ~60 s |
| `garden/camera/{slug}/status` | JSON | `method: icmp_ping` or `onvif_probe_on_request` |
| `garden/camera/{slug}/command/snapshot` | JSON or any | **On-demand** JPEG (ONVIF/RTSP once) |
| `garden/camera/{slug}/command/probe` | JSON or any | **On-demand** ONVIF GetDeviceInformation |
| `garden/camera/{slug}/command/result` | JSON | Success/failure of last command |
| `garden/camera/{slug}/snapshot` | JSON | Published only after a successful capture |
| `garden/camera/{slug}/event` | JSON | Not produced by the ping watchdog (no PullPoint) |

### On-demand snapshot examples

```bash
mosquitto_pub -h localhost -t 'garden/camera/frontHouse/command/snapshot' -m '{"action":"snapshot"}'
mosquitto_pub -h localhost -t 'garden/camera/frontHouse/command/probe' -m '{}'
```

Watchdog UI (**Capture** on each camera card) publishes the same snapshot command.

HTTP serve (existing file only): `http://<host>:1880/camera-snapshots/{slug}.jpg`

## Watchdog (flow 612)

| Setting | Value |
|---------|-------|
| Heartbeat | ICMP via `camera-ping-watchdog` (~60 s) |
| Timeout | **3 minutes** without `online` |
| Explicit offline | Immediate Telegram on retained `offline` |

## Verification

```bash
systemctl status camera-ping-watchdog.service
mosquitto_sub -h localhost -t 'garden/camera/#' -v
journalctl -u camera-ping-watchdog -f
```

Expect `…/health online` within ~60 s of service start. Do **not** expect
periodic `…/snapshot` or `…/event` without a command.

## Troubleshooting

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| All cameras offline | Ping blocked / wrong IPs | `ping -c1 <ip>` from server; check `CAMERA_N_IP` |
| Capture fails | Bad Camera Account | Fix `CAMERA_N_USER`/`PASS`; run `camera_connect.py` |
| DVR unresponsive again | Continuous ONVIF restarted | Ensure `tapo-monitor` is disabled; only ping watchdog runs |
| No motion Telegram | PullPoint removed by design | Use Tapo app / NVR for motion; do not re-enable continuous ONVIF |

## Related files

| File | Purpose |
|------|---------|
| `scripts/status/camera_ping_watchdog.py` | ICMP health + on-demand ONVIF |
| `scripts/status/tapo_snapshot.py` | JPEG capture helpers (on request) |
| `scripts/status/camera_probe.py` / `camera_connect.py` | Manual ONVIF tests |
| `scripts/status/tapo_monitor.py` | **Retired stub** (exits 1) |
| `systemd/camera-ping-watchdog.service` | systemd unit |
| `nodered/flows/611–613` | Dashboard, watchdog, UI |
| [docs/cameras/REGISTRY.md](cameras/REGISTRY.md) | Camera inventory |
| [docs/HOMEGUARD_NVR.md](HOMEGUARD_NVR.md) | NVR notes |
