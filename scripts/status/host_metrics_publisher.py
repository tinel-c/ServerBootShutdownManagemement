#!/usr/bin/env python3
"""
Publish automation-host CPU, memory, load, and disk usage to MQTT.

Topics (prefix default ``system/automation``):
  {prefix}/status          retained JSON snapshot
  {prefix}/cpu_pct         scalar
  {prefix}/memory_pct      scalar
  {prefix}/disk_root_pct   scalar
  {prefix}/disk_data_pct   scalar (omitted if /data not mounted)
  {prefix}/load1           scalar (1-minute load average)
"""

from __future__ import annotations

import json
import os
import signal
import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import psutil

sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))

from config_loader import get_config  # noqa: E402
from logger import get_logger  # noqa: E402
from mqtt_client import MQTTClientWrapper  # noqa: E402

logger = get_logger(__name__)

DEFAULT_PREFIX = "system/automation"
DEFAULT_INTERVAL_SEC = 15


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _disk_usage(path: str) -> Optional[Dict[str, Any]]:
    try:
        usage = psutil.disk_usage(path)
    except (OSError, PermissionError) as exc:
        logger.debug("disk_usage(%s) failed: %s", path, exc)
        return None
    return {
        "mount": path,
        "percent": round(float(usage.percent), 2),
        "used_bytes": int(usage.used),
        "total_bytes": int(usage.total),
        "free_bytes": int(usage.free),
    }


def collect_metrics() -> Dict[str, Any]:
    """Sample host metrics once."""
    # First call after import may be 0.0; a short interval gives a real reading.
    cpu = float(psutil.cpu_percent(interval=0.4))
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    try:
        load1, load5, load15 = os.getloadavg()
    except (AttributeError, OSError):
        load1 = load5 = load15 = 0.0

    root = _disk_usage("/")
    data = None
    if os.path.ismount("/data") or Path("/data").is_dir():
        data = _disk_usage("/data")

    payload: Dict[str, Any] = {
        "timestamp": _utc_now(),
        "host": socket.gethostname(),
        "cpu": {
            "percent": round(cpu, 2),
            "count": int(psutil.cpu_count() or 0),
        },
        "load": {
            "1": round(float(load1), 3),
            "5": round(float(load5), 3),
            "15": round(float(load15), 3),
        },
        "memory": {
            "percent": round(float(mem.percent), 2),
            "used_bytes": int(mem.used),
            "total_bytes": int(mem.total),
            "available_bytes": int(mem.available),
        },
        "swap": {
            "percent": round(float(swap.percent), 2),
            "used_bytes": int(swap.used),
            "total_bytes": int(swap.total),
        },
        "disk": {
            "root": root,
            "data": data,
        },
    }
    return payload


class HostMetricsPublisher:
    """Periodic MQTT publisher for local host metrics."""

    def __init__(self) -> None:
        self.config = get_config()
        mqtt_cfg = self.config.get("mqtt", {})
        broker = mqtt_cfg.get("broker", {})
        auth = mqtt_cfg.get("authentication", {})

        self.prefix = (
            os.environ.get("HOST_METRICS_MQTT_PREFIX")
            or self.config.get("host_metrics", {}).get("mqtt_prefix")
            or DEFAULT_PREFIX
        ).rstrip("/")
        self.interval = int(
            os.environ.get(
                "HOST_METRICS_INTERVAL_SEC",
                self.config.get("host_metrics", {}).get(
                    "interval_sec", DEFAULT_INTERVAL_SEC
                ),
            )
        )
        self.running = False
        self.mqtt = MQTTClientWrapper(
            broker_host=broker.get("host", "127.0.0.1"),
            broker_port=int(broker.get("port", 1883)),
            client_id="host_metrics_publisher",
            username=auth.get("username"),
            password=auth.get("password"),
            keepalive=int(broker.get("keepalive", 60)),
            qos=int(mqtt_cfg.get("qos", 1)),
        )

    def _publish(self, payload: Dict[str, Any]) -> None:
        status_topic = f"{self.prefix}/status"
        self.mqtt.publish(status_topic, json.dumps(payload), retain=True)

        cpu = payload["cpu"]["percent"]
        mem = payload["memory"]["percent"]
        load1 = payload["load"]["1"]
        self.mqtt.publish(f"{self.prefix}/cpu_pct", f"{cpu}", retain=True)
        self.mqtt.publish(f"{self.prefix}/memory_pct", f"{mem}", retain=True)
        self.mqtt.publish(f"{self.prefix}/load1", f"{load1}", retain=True)

        root = (payload.get("disk") or {}).get("root") or {}
        if root.get("percent") is not None:
            self.mqtt.publish(
                f"{self.prefix}/disk_root_pct",
                f"{root['percent']}",
                retain=True,
            )
        data = (payload.get("disk") or {}).get("data") or {}
        if data.get("percent") is not None:
            self.mqtt.publish(
                f"{self.prefix}/disk_data_pct",
                f"{data['percent']}",
                retain=True,
            )

    def run(self) -> None:
        logger.info(
            "Host metrics publisher starting (prefix=%s interval=%ss)",
            self.prefix,
            self.interval,
        )
        self.mqtt.connect()
        self.running = True
        # Warm CPU percent baseline
        psutil.cpu_percent(interval=None)

        while self.running:
            started = time.monotonic()
            try:
                payload = collect_metrics()
                self._publish(payload)
                logger.debug(
                    "Published host metrics cpu=%.1f mem=%.1f root=%s",
                    payload["cpu"]["percent"],
                    payload["memory"]["percent"],
                    (payload.get("disk") or {}).get("root", {}).get("percent"),
                )
            except Exception as exc:  # noqa: BLE001 — keep loop alive
                logger.exception("Host metrics publish failed: %s", exc)

            elapsed = time.monotonic() - started
            sleep_for = max(1.0, self.interval - elapsed)
            # Interruptible sleep
            end = time.monotonic() + sleep_for
            while self.running and time.monotonic() < end:
                time.sleep(min(0.5, end - time.monotonic()))

        try:
            self.mqtt.disconnect()
        except Exception:  # noqa: BLE001
            pass
        logger.info("Host metrics publisher stopped")

    def stop(self, *_args: Any) -> None:
        self.running = False


def main() -> int:
    pub = HostMetricsPublisher()
    signal.signal(signal.SIGTERM, pub.stop)
    signal.signal(signal.SIGINT, pub.stop)
    pub.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
