# Release Notes — v3.18.0

**Date:** 2026-07-18

## Summary

Stops continuous ONVIF polling of Tapo cameras (which made the HomeGuard DVR unresponsive). Camera watchdog now uses **ICMP ping**. ONVIF/RTSP snapshots are **on request only**.

## Changes

- New service: `camera-ping-watchdog.service` (`scripts/status/camera_ping_watchdog.py`)
- Retired: continuous `tapo-monitor` ONVIF loops (`tapo_monitor.py` is a stub; unit disabled)
- Flow **612**: 3-minute timeout on ICMP health
- Flow **613**: **Capture** button → `garden/camera/{slug}/command/snapshot`
- Docs: [TAPO_CAMERA.md](../TAPO_CAMERA.md), registry, MQTT protocol
- Agent memory: `.cursor/rules/camera-no-continuous-onvif.mdc`

## Deploy

```bash
# On automation server (after git pull + update.sh)
sudo systemctl disable --now tapo-monitor.service
sudo systemctl enable --now camera-ping-watchdog.service
systemctl status camera-ping-watchdog.service
mosquitto_sub -h localhost -t 'garden/camera/+/health' -C 7 -v
```

Redeploy Node-RED flows **612** and **613** from the repo scripts.
