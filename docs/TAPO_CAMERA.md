# Tapo Camera — ONVIF Motion & Person Detection

Tapo C310/C320 (and related models) are monitored via ONVIF PullPoint events on the automation server. Events are published to MQTT; Node-RED flow **611** drives the dashboard, Telegram, and SMS.

## Data flow

```text
Tapo camera (ONVIF :2020, Camera Account)
        │
        ▼
tapo-monitor.service  (scripts/status/tapo_monitor.py)
        │
        ▼
Mosquitto MQTT
  • garden/camera/{slug}/health   ← retained online|offline
  • garden/camera/{slug}/event    ← JSON motion/person events
        │
        ▼
Node-RED flow 611
        ├── Dashboard  /dashboard/page6
        ├── Telegram   /camera_status, /camera_help
        └── SMS        CAMERA_STATUS, CAMERA_HELP
        │
Node-RED flow 612 (watchdog)
        ├── Per-camera 2 min timeout on garden/camera/{slug}/health
        └── Telegram online/offline (transitions)
        │
SMS Gateway watchdog (camera_{slug}, 60 s heartbeat from tapo-monitor)
```

## Prerequisites

### Tapo app (per camera)

1. **Enable ONVIF** — Device Settings → Advanced → ONVIF
2. **Create Camera Account** — Advanced → Camera Account (username/password for ONVIF/RTSP)
   - Use this account in `.env`, **not** your Tapo cloud email/password
3. **Enable detection** — Device Settings → Detection → Motion (and Person if available)

### Automation server

1. Configure cameras in `.env` (see [config/cameras.env.example](../config/cameras.env.example) for the 7-camera site layout):

```bash
# Example — Interior curte (discovered C510W @ 192.168.2.37)
CAMERA_1_NAME="Interior curte"
CAMERA_1_IP=192.168.2.37
CAMERA_1_PORT=2020
CAMERA_1_USER=your_camera_account
CAMERA_1_PASS=your_camera_password
CAMERA_1_MQTT_PREFIX="garden/camera/interior"
```

## Network discovery

On the automation server (same LAN as the cameras):

```bash
# Port scan only
python3 scripts/utils/camera_network_scan.py --subnet 192.168.2

# Probe ONVIF model/serial (Camera Account credentials)
python3 scripts/utils/camera_network_scan.py --subnet 192.168.2 --user tinelc --pass YOUR_PASS

# WS-Discovery (multicast; may return empty if blocked)
python3 scripts/utils/camera_discovery.py
```

**Site scan (2026-07-05):**

| IP | Model | MQTT slug | Notes |
|----|-------|-----------|-------|
| 192.168.2.10 | Tapo C500 | smallGate | Poarta mica |
| 192.168.2.32 | Tapo C310 | backyard | Spate casa |
| 192.168.2.34 | Tapo C310 | gate2 / gate1 | Poarta glisanta 2 (+ glisanta 1 alias, merged by IP) |
| 192.168.2.36 | Tapo C310 | fataCasa | Fata casa |
| 192.168.2.37 | Tapo C510W | interior | Interior curte (was .38) |
| 192.168.2.59 | Tapo (RTSP) | strada | Curte strada — **enable ONVIF** in Tapo app |
| — | — | — | Retired: .35, .38 |

`tapo-monitor` merges multiple `CAMERA_N_*` entries that share the same IP into one ONVIF session and publishes health/events to each `CAMERA_N_MQTT_PREFIX`.

2. Install and enable the service:

```bash
sudo ./install.sh          # includes tapo-monitor.service
sudo systemctl enable tapo-monitor.service
sudo systemctl start tapo-monitor.service
```

3. Import Node-RED flows (after `00-base-config.json`):

   - `611-camera-management.json`
   - `612-camera-watchdog.json`

4. **Deploy** Node-RED and open: `http://<host>:1880/dashboard/page6`

## Discovery helper

```bash
python3 scripts/utils/camera_discovery.py
```

Prints suggested `CAMERA_N_*` lines for cameras found via WS-Discovery.

## MQTT topics

| Topic | Payload | Notes |
|-------|---------|-------|
| `garden/camera/{slug}/health` | `online` or `offline` | Retained; republished ~every 60 s while online |
| `garden/camera/{slug}/event` | JSON | See [MQTT_PROTOCOL.md](MQTT_PROTOCOL.md#tapo-camera-messages) |
| `sms/gateway/watchdog/enroll` | `{"name":"camera_{slug}","interval":60}` | Sent once at tapo-monitor startup |
| `sms/gateway/watchdog/heartbeat` | `{"name":"camera_{slug}"}` | Each online health publish |

`{slug}` comes from `CAMERA_N_MQTT_PREFIX` (last path segment) or auto-generated from the camera name.

## Verification

```bash
# Service and env
systemctl status tapo-monitor.service
./check_env.sh

# Live MQTT (expect health within ~30s of service start)
mosquitto_sub -h localhost -t 'garden/camera/#' -v

# Service logs while triggering motion in front of camera
journalctl -u tapo-monitor -f
```

**Expected on motion:**

```text
garden/camera/front/event {"event":"motion","state":"active",...}
```

**Dashboard:** status cards show **ONLINE**; event log fills on detection.

## Troubleshooting

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| Dashboard empty, no MQTT | Wrong broker in flow 611 | Re-import fixed `611-camera-management.json` (`mqtt_broker_local`) |
| `health online` but no `event` | ONVIF PullPoint unsupported (firmware) | Check `journalctl -u tapo-monitor`; see firmware note below |
| Authority failure in logs | Wrong credentials | Use **Camera Account** from Tapo app |
| Events in MQTT but no Telegram | `state: inactive` in payload | Fixed in tapo_monitor (IsMotion field); restart service |
| `/camera_status` shows no cameras | No retained health received | Confirm MQTT prefix matches `CAMERA_N_MQTT_PREFIX` |

### Firmware / ONVIF limitations

C310/C320 ONVIF event support varies by firmware. Some builds break PullPoint subscriptions while the Tapo app still detects motion. If logs show:

```text
ONVIF events are unsupported or unauthorized. Falling back to health monitoring only.
```

you will get **online/offline** on the dashboard but **no motion events**. Options:

- Update or roll back camera firmware
- Contact TP-Link support
- Future fallback: `pytapo` polling (not enabled by default)

## Commands

| Channel | Command | Description |
|---------|---------|-------------|
| Telegram | `/camera_status` | Health + last detection per camera |
| Telegram | `/camera_help` | Help text |
| SMS | `CAMERA_STATUS` | Same as Telegram status |
| SMS | `CAMERA_HELP` | Same as Telegram help |

## Related files

| File | Purpose |
|------|---------|
| `scripts/status/tapo_monitor.py` | ONVIF → MQTT |
| `systemd/tapo-monitor.service` | systemd unit |
| `nodered/flows/611-camera-management.json` | Dashboard + notifications |
| `scripts/utils/camera_discovery.py` | Network discovery |
