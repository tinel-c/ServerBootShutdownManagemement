# Release Notes — v3.25.0

**Date:** 2026-11-22  
**Author:** Constantin Bogza

## Summary

Windows Client Monitor loads its device list from GitHub, lists the Tasmota boards on the automation LAN, and installs a newer release by itself. Publishing this release with `client-v3.25.0.zip` is what moves every PC that already has the app.

## Changes

### Device list from GitHub

- Device Fleet fetches `scripts/status/device_fleet.yaml` and `device/tasmota/catalog.yaml` from this repository. The copy under `client/config/` is only used when GitHub cannot be reached.
- **Scan Tasmota** asks the broker and probes `192.168.2.0/24` once. A scan from a checkout updates `device/tasmota/catalog.yaml`.

### Tasmota boards in the device folder

Thirteen topics are listed under `device/tasmota/`. Six answered with an address during the 2026-11-22 scan: Main Sliding Gate (`192.168.2.96`), Front House Power (`192.168.2.202`), Water Pump (`192.168.2.17`), Workshop Sonoff (`192.168.2.108`), Garden Power Hut (`192.168.2.7`), and Aquarium Light (`192.168.2.137`).

### Self-update for every installed PC

- The client reads `client/VERSION`, checks GitHub at startup and every 24 hours, and applies a newer release with `update_client_files.bat`. `config\.env` is kept. The unattended log is `%LOCALAPPDATA%\ClientMonitor\update.log`.
- `scripts/release/create_release.ps1` uploads `dist/client-v3.25.0.zip`. Installs from 3.11.2 onward download a release asset whose name contains `client` and ends in `.zip`.
- Online PCs can be woken with `python scripts/client/deploy_client_update.py --notify`. That works after this build is installed. Until then they update on the next check or logon.
- Presence, heartbeat, and `clients/<id>/update` include the running version.

## Deploy

Installed PCs do not need a manual copy. After this release is on GitHub they take the zip on the next update check (within 24 hours) or the next logon.

To see who is online, and to ask PCs that already run 3.25.0 to check immediately:

```bash
python scripts/client/deploy_client_update.py --notify --status
```
