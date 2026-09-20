# Release Notes — v3.20.0

**Date:** 2026-09-20

## Summary

Adds live **automation-host CPU / memory / disk** metrics to MQTT and a Node-RED **Host** dashboard with **1 hour / 25 hours / 1 month** charts. Also expands `/data` HDD usage (swap, Home Assistant config, Mosquitto logs, snapshots) so the 15 GB root SSD stays free, and pins Mosquitto at **2.0.18** after the 2.1.2 crash loop.

## Changes

### Host metrics
- New service: `host-metrics-publisher.service` (`scripts/status/host_metrics_publisher.py`)
- MQTT prefix `system/automation/` — retained JSON `status` + scalar `%` / load topics
- Flow **910** — dashboard `/dashboard/host` (gauges + history charts)
- Docs: [HOST_METRICS.md](../HOST_METRICS.md), [MQTT_PROTOCOL.md](../MQTT_PROTOCOL.md)

### Data drive / root SSD
- Swap → `/data/swapfile`; Home Assistant config bind-mounted on `/data`
- Mosquitto logs + camera snapshots on `/data`
- Cleanup target ≤ 80%; remove duplicate logrotate symlink config
- Docs / rules: [SERVER_DISK.md](../developer/SERVER_DISK.md), `.cursor/rules/data-drive-root-ssd.mdc`

### Mosquitto
- Pin apt **2.0.18** (hold); do not use 2.1.x (double-free crash loop)
- Rule / docs: `.cursor/rules/mosquitto-pin-2.0.18.mdc`, [SERVER_DEPLOY.md](../developer/SERVER_DEPLOY.md)

## Deploy

```bash
cd ~/ServerBootShutdownManagemement && git fetch && git checkout main && git pull
printf '\n' | sudo bash ./update.sh
sudo bash /opt/dell_server_management/install_host_metrics_service.sh
systemctl status host-metrics-publisher.service
timeout 20 mosquitto_sub -h localhost -t 'system/automation/status' -C 1 -v
```

Redeploy Node-RED flow **910** from the dev PC:

```bash
cd nodered/live-connection
node scripts/generate-flow-910.mjs
node scripts/deploy-flow-910.mjs
```

Open **http://192.168.2.4:1880/dashboard/host**
