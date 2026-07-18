#!/usr/bin/env python3
"""
Camera ping watchdog — ICMP health for Tapo cameras (no continuous ONVIF).

Continuous ONVIF PullPoint / periodic snapshots overload the cameras and the
HomeGuard DVR. This service only:

  1. Pings each camera IP on an interval and publishes retained MQTT health.
  2. Handles on-demand ONVIF/RTSP snapshot or probe via MQTT commands.

Commands (per camera slug from CAMERA_N_MQTT_PREFIX):
  garden/camera/{slug}/command/snapshot   — grab one JPEG (ONVIF/RTSP once)
  garden/camera/{slug}/command/probe      — one-shot ONVIF GetDeviceInformation
"""

from __future__ import annotations

import json
import os
import platform
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))

from camera_probe import normalize_mac, probe_onvif  # noqa: E402
from config_loader import get_config  # noqa: E402
from logger import get_logger  # noqa: E402
from mqtt_client import MQTTClientWrapper  # noqa: E402
from tapo_snapshot import (  # noqa: E402
    build_snapshot_payload,
    capture_camera_jpeg,
    resize_jpeg,
    save_snapshot_jpeg,
    slug_from_mqtt_prefix,
)

logger = get_logger(__name__)

DEFAULT_PING_INTERVAL_SEC = 60
DEFAULT_PING_TIMEOUT_SEC = 2
DEFAULT_PING_COUNT = 1
DEFAULT_SNAPSHOT_MAX_WIDTH = 480
DEFAULT_SNAPSHOT_DIR = "/opt/dell_server_management/data/camera-snapshots"


def ping_host(host: str, count: int = 1, timeout_sec: int = 2) -> bool:
    """Return True if ICMP echo succeeds."""
    system = platform.system().lower()
    if system == "windows":
        command = ["ping", "-n", str(count), "-w", str(timeout_sec * 1000), host]
    else:
        command = ["ping", "-c", str(count), "-W", str(timeout_sec), host]
    try:
        subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
            timeout=timeout_sec * count + 5,
        )
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return False


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class CameraPingWatchdog:
    """ICMP health publisher + on-demand ONVIF snapshot/probe."""

    def __init__(self) -> None:
        self.config = get_config()
        mqtt_config = self.config.get("mqtt", {})
        self.mqtt = MQTTClientWrapper(
            broker_host=mqtt_config.get("broker", {}).get("host"),
            broker_port=mqtt_config.get("broker", {}).get("port", 1883),
            client_id="camera_ping_watchdog",
            username=mqtt_config.get("authentication", {}).get("username"),
            password=mqtt_config.get("authentication", {}).get("password"),
        )
        self.cameras: List[Dict[str, Any]] = list(self.config.get("cameras") or [])
        self.by_slug: Dict[str, Dict[str, Any]] = {}
        for cam in self.cameras:
            prefix = cam.get("mqtt_prefix") or (
                f"garden/camera/{(cam.get('name') or 'camera').lower().replace(' ', '_')}"
            )
            cam = {**cam, "mqtt_prefix": prefix.rstrip("/")}
            slug = slug_from_mqtt_prefix(cam["mqtt_prefix"])
            self.by_slug[slug] = cam

        self.ping_interval = int(
            os.environ.get("CAMERA_PING_INTERVAL_SEC")
            or os.environ.get("CAMERA_HEALTH_INTERVAL_SEC")
            or DEFAULT_PING_INTERVAL_SEC
        )
        self.ping_timeout = int(os.environ.get("CAMERA_PING_TIMEOUT_SEC", DEFAULT_PING_TIMEOUT_SEC))
        self.ping_count = int(os.environ.get("CAMERA_PING_COUNT", DEFAULT_PING_COUNT))
        self.snapshot_dir = os.environ.get("CAMERA_SNAPSHOT_DIR", DEFAULT_SNAPSHOT_DIR)
        self.snapshot_max_width = int(
            os.environ.get("CAMERA_SNAPSHOT_MAX_WIDTH", DEFAULT_SNAPSHOT_MAX_WIDTH)
        )
        self.running = False

    def start(self) -> None:
        if not self.cameras:
            logger.warning("No CAMERA_N_* entries configured; idle until stop")
        if not self.mqtt.connect():
            logger.error("Failed to connect to MQTT broker")
            return

        self.running = True
        self.mqtt.subscribe("garden/camera/+/command/#", self._on_command)
        logger.info(
            "Camera ping watchdog started (%d camera(s), interval=%ss)",
            len(self.cameras),
            self.ping_interval,
        )

        try:
            while self.running:
                self._poll_all()
                for _ in range(max(1, self.ping_interval)):
                    if not self.running:
                        break
                    time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self) -> None:
        logger.info("Stopping camera ping watchdog...")
        self.running = False
        for cam in self.cameras:
            self._publish_health(cam, "offline")
        self.mqtt.disconnect()
        logger.info("Stopped.")

    def _publish_health(self, cam: Dict[str, Any], state: str) -> None:
        topic = f"{cam['mqtt_prefix']}/health"
        self.mqtt.publish(topic, state, retain=True)

    def _publish_status(self, cam: Dict[str, Any], online: bool, method: str, error: Optional[str] = None) -> None:
        slug = slug_from_mqtt_prefix(cam["mqtt_prefix"])
        payload = {
            "timestamp": _utc_now(),
            "slug": slug,
            "name": cam.get("name"),
            "ip": cam.get("ip"),
            "online": online,
            "method": method,
            "model": cam.get("model"),
            "mac_expected": normalize_mac(cam.get("mac")),
            "error": error,
        }
        self.mqtt.publish(f"{cam['mqtt_prefix']}/status", payload)

    def _poll_all(self) -> None:
        for cam in self.cameras:
            ip = cam.get("ip")
            if not ip:
                continue
            ok = ping_host(ip, count=self.ping_count, timeout_sec=self.ping_timeout)
            state = "online" if ok else "offline"
            self._publish_health(cam, state)
            self._publish_status(cam, ok, method="icmp_ping")
            slug = slug_from_mqtt_prefix(cam["mqtt_prefix"])
            if ok:
                logger.debug("Ping OK %s (%s)", slug, ip)
            else:
                logger.warning("Ping FAIL %s (%s)", slug, ip)

    def _on_command(self, topic: str, payload: Any) -> None:
        parts = (topic or "").strip("/").split("/")
        # garden/camera/{slug}/command/{action}
        if len(parts) < 5 or parts[0] != "garden" or parts[1] != "camera" or parts[3] != "command":
            return
        slug = parts[2]
        action = parts[4].lower()
        cam = self.by_slug.get(slug)
        if not cam:
            logger.warning("Command for unknown camera slug=%s topic=%s", slug, topic)
            return

        if isinstance(payload, (bytes, bytearray)):
            payload = payload.decode("utf-8", errors="replace")
        if isinstance(payload, str):
            try:
                payload = json.loads(payload) if payload.strip().startswith("{") else {"action": payload}
            except json.JSONDecodeError:
                payload = {"action": payload}

        if action in ("snapshot", "snap", "picture"):
            self._handle_snapshot(cam, slug)
        elif action in ("probe", "onvif", "status"):
            self._handle_probe(cam, slug)
        else:
            logger.warning("Unknown camera command %s for %s", action, slug)

    def _handle_probe(self, cam: Dict[str, Any], slug: str) -> None:
        logger.info("On-demand ONVIF probe for %s (%s)", slug, cam.get("ip"))
        probe = probe_onvif(
            cam["ip"],
            cam.get("username") or "",
            cam.get("password") or "",
            port=int(cam.get("port") or 2020),
        )
        online = bool(probe.get("online"))
        # Do not override ICMP health from a one-shot probe; publish status only.
        expected_mac = normalize_mac(cam.get("mac"))
        observed = probe.get("mac_observed")
        payload = {
            "timestamp": _utc_now(),
            "slug": slug,
            "name": cam.get("name"),
            "ip": cam.get("ip"),
            "online": online,
            "method": "onvif_probe_on_request",
            "model": probe.get("model") or cam.get("model"),
            "manufacturer": probe.get("manufacturer"),
            "serial": probe.get("serial"),
            "firmware": probe.get("firmware"),
            "mac_expected": expected_mac,
            "mac_observed": observed,
            "mac_match": (
                expected_mac == observed if expected_mac and observed else None
            ),
            "error": probe.get("error"),
        }
        self.mqtt.publish(f"{cam['mqtt_prefix']}/status", payload)
        result_topic = f"{cam['mqtt_prefix']}/command/result"
        self.mqtt.publish(
            result_topic,
            {"action": "probe", "success": online, "slug": slug, "error": probe.get("error")},
        )

    def _handle_snapshot(self, cam: Dict[str, Any], slug: str) -> None:
        logger.info("On-demand snapshot for %s (%s)", slug, cam.get("ip"))
        result_topic = f"{cam['mqtt_prefix']}/command/result"
        try:
            from onvif import ONVIFCamera  # local import — only when requested
        except ImportError:
            self.mqtt.publish(
                result_topic,
                {"action": "snapshot", "success": False, "slug": slug, "error": "onvif-zeep missing"},
            )
            return

        camera = None
        try:
            camera = ONVIFCamera(
                cam["ip"],
                int(cam.get("port") or 2020),
                cam.get("username") or "",
                cam.get("password") or "",
            )
            raw = capture_camera_jpeg(
                camera,
                cam["ip"],
                cam.get("username") or "",
                cam.get("password") or "",
            )
            if not raw:
                raise RuntimeError("No JPEG from ONVIF/RTSP")
            jpeg = resize_jpeg(raw, self.snapshot_max_width)
            image_url = save_snapshot_jpeg(slug, jpeg, self.snapshot_dir)
            snap_payload = build_snapshot_payload(
                slug,
                cam.get("name") or slug,
                _utc_now(),
                image_url,
            )
            snap_payload["source"] = "on_request"
            self.mqtt.publish(f"{cam['mqtt_prefix']}/snapshot", snap_payload)
            self.mqtt.publish(
                result_topic,
                {
                    "action": "snapshot",
                    "success": True,
                    "slug": slug,
                    "image_url": image_url,
                    "bytes": len(jpeg),
                },
            )
            logger.info("Snapshot OK %s → %s (%d bytes)", slug, image_url, len(jpeg))
        except Exception as exc:
            logger.warning("On-demand snapshot failed for %s: %s", slug, exc)
            self.mqtt.publish(
                result_topic,
                {"action": "snapshot", "success": False, "slug": slug, "error": str(exc)},
            )


def main() -> None:
    service = CameraPingWatchdog()

    def _stop(signum, frame):  # noqa: ARG001
        service.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)
    service.start()


if __name__ == "__main__":
    main()
