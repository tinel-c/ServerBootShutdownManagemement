# Release Notes — v3.23.0

**Date:** 2026-11-22  
**Author:** Constantin Bogza

## Summary

The SMS gateway no longer texts on every identical watchdog re-enroll. The watchdog page waits longer for gateway status, and the Windows tray client refuses a second copy.

## Changes

### SMS gateway 1.1.3

- Re-enroll with the same `name` and `interval` is a silent no-op. A changed interval still sends an “updated” SMS.
- Devices still re-enroll on their status cadence so a gateway reboot rebuilds the RAM watch list.
- Topics are documented in the device README and in [MQTT_PROTOCOL.md](../MQTT_PROTOCOL.md).

### Watchdog dashboard (flow 613)

- SMS gateway card timeout is **12 minutes**. Status is published about every 5 minutes.
- A dashboard refresh does not publish `garden/camera/{slug}/command/snapshot` unless that topic is present.

### Windows tray client

- `client_monitor.py` takes a Windows mutex (`Local\ClientMonitor_ServerBootShutdown`). A second start from Task Scheduler, VBS, or a manual launch exits immediately.

## Deploy

```bash
cd ~/ServerBootShutdownManagemement && git fetch && git checkout main && git pull
git submodule update --init device/PlatformIO_esp32-sms-gateway
```

Flash the gateway from the device repo with `pio run -e lilygo-t-call` when it should run 1.1.3. Redeploy the dashboard with `node nodered/live-connection/scripts/deploy-flow-613.mjs`.
