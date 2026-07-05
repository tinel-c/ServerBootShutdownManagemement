# HomeGuard NVR

The site **HomeGuard NVR** is on the automation LAN at **`192.168.2.59`** (MAC `00:23:63:91:e6:99`). It uses a webpack web UI with a JSON **`/API/*`** interface (same family as many OEM NVR firmwares).

Tapo cameras are monitored by `tapo-monitor.service` and Node-RED flows **611–613**. HomeGuard integration is **documented and probed** here; full NVR channel import requires valid NVR login credentials (separate from Tapo Camera Account).

## Network

| Item | Value |
|------|--------|
| IP | `192.168.2.59` |
| HTTP | port `80` (web UI + `/API/*`) |
| RTSP | port `554` |
| ONVIF | not on port `2020` (Tapo-style) |

## API (discovered from web UI)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/API/Login/Range` | POST | Login capabilities, password rules |
| `/API/Web/Get_Private_Key` | POST | Session key for password encryption |
| `/API/Web/Login` | POST | Authenticate (HTTP Digest + encrypted password) |
| `/API/Login/DeviceInfo/Get` | POST | NVR model, channel count |
| `/API/Login/ChannelInfo/Get` | POST | Per-channel name and online status |
| `/API/Preview/StreamUrl` | POST | RTSP URL for a channel |
| `/API/Login/Heartbeat` | POST | Keep session alive |

Web UI version string: `1.0.0.131`.

## Probe tools

On the automation server:

```bash
# RTSP path sweep + HTTP snapshot attempts
sudo /opt/dell_server_management/venv/bin/python3 scripts/status/probe_homeguard_nvr.py --ip 192.168.2.59 --user USER --password PASS

# Python API client (login + channel list) — work in progress
/opt/dell_server_management/venv/bin/python3 -c "
from scripts.status.homeguard_nvr import probe_nvr
print(probe_nvr('192.168.2.59', 'USER', 'PASS'))
"
```

## Credentials

Use the **NVR local admin account** created in the HomeGuard web UI — not Tapo cloud credentials.

If login fails with `login_failed` or `no_login`, verify username/password in the NVR web UI at `http://192.168.2.59/` and ensure the account is not locked (too many failed attempts).

## Planned integration

When NVR credentials are confirmed:

1. Poll NVR health every 5 min (`/API/Login/Heartbeat` or TCP 80/554).
2. Publish per-channel health to `garden/camera/homeguardCh{N}/health` (or names from `ChannelInfo`).
3. Snapshots via `Preview/StreamUrl` + ffmpeg (same 5 min interval as Tapo).
4. Show channels on Watchdog flow **613** alongside the seven Tapo cameras.

## Related

- [docs/cameras/REGISTRY.md](cameras/REGISTRY.md) — Tapo camera list
- [docs/TAPO_CAMERA.md](TAPO_CAMERA.md) — Tapo ONVIF monitor
- `scripts/status/homeguard_nvr.py` — API client stub
- `scripts/status/probe_homeguard_nvr.py` — connectivity probe
