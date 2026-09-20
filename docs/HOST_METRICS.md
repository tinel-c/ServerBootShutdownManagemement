# Automation host metrics (CPU / memory / disk)

Publishes live resource usage from the automation server (`192.168.2.4`) to MQTT and shows it on the Node-RED **Host** dashboard with history charts.

## MQTT

Prefix: `system/automation` (override with `HOST_METRICS_MQTT_PREFIX`).

| Topic | Payload |
|-------|---------|
| `system/automation/status` | Retained JSON snapshot (see below) |
| `system/automation/cpu_pct` | Scalar % |
| `system/automation/memory_pct` | Scalar % |
| `system/automation/disk_root_pct` | Scalar % for `/` |
| `system/automation/disk_data_pct` | Scalar % for `/data` (when mounted) |
| `system/automation/load1` | 1‑minute load average |

Default interval: **15 s** (`HOST_METRICS_INTERVAL_SEC`).

### Status JSON shape

```json
{
  "timestamp": "2026-09-20T08:00:00+00:00",
  "host": "ubuntu-automation",
  "cpu": { "percent": 12.5, "count": 4 },
  "load": { "1": 0.42, "5": 0.55, "15": 0.61 },
  "memory": { "percent": 48.1, "used_bytes": 1, "total_bytes": 1, "available_bytes": 1 },
  "swap": { "percent": 10.0, "used_bytes": 1, "total_bytes": 1 },
  "disk": {
    "root": { "mount": "/", "percent": 50.0, "used_bytes": 1, "total_bytes": 1, "free_bytes": 1 },
    "data": { "mount": "/data", "percent": 3.0, "used_bytes": 1, "total_bytes": 1, "free_bytes": 1 }
  }
}
```

## Service

```bash
sudo ./install_host_metrics_service.sh
systemctl status host-metrics-publisher.service
timeout 20 mosquitto_sub -h localhost -t 'system/automation/status' -C 1 -v
```

Unit: `systemd/host-metrics-publisher.service`  
Script: `scripts/status/host_metrics_publisher.py`

## Node-RED UI

- Flow **910** — `nodered/flows/910-host-metrics-dashboard.json`
- Page: **Host** → `/dashboard/host`
- Charts: **1 hour**, **25 hours** (1‑min buckets), **1 month** (1‑hour buckets)
- History is kept in Node-RED flow context (not on the root SSD)

```bash
cd nodered/live-connection
node scripts/generate-flow-910.mjs
node scripts/deploy-flow-910.mjs
```

## Related

- Disk layout: [SERVER_DISK.md](developer/SERVER_DISK.md)
- MQTT overview: [MQTT_PROTOCOL.md](MQTT_PROTOCOL.md)
