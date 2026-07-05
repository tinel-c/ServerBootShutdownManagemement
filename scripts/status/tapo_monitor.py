#!/usr/bin/env python3
"""
Tapo Camera Event Monitor.
Monitors Tapo cameras for real-time events (motion, person detection) using ONVIF 
and publishes these events to an MQTT broker.
"""

import sys
import os
import json
import time
import signal
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))

from mqtt_client import MQTTClientWrapper
from config_loader import get_config
from logger import get_logger
from tapo_snapshot import (
    build_snapshot_payload,
    capture_camera_jpeg,
    resize_jpeg,
    save_snapshot_jpeg,
    slug_from_mqtt_prefix,
)
from camera_probe import normalize_mac, probe_onvif

try:
    from onvif import ONVIFCamera
except ImportError:
    print("❌ Error: onvif-zeep not installed. Run: pip install onvif-zeep")
    sys.exit(1)

logger = get_logger(__name__)

DEFAULT_SNAPSHOT_INTERVAL_SEC = 300
DEFAULT_SNAPSHOT_MAX_WIDTH = 480
DEFAULT_SNAPSHOT_DIR = "/opt/dell_server_management/data/camera-snapshots"
DEFAULT_HEALTH_INTERVAL_SEC = 300


class TapoCameraMonitor:
    """Monitors a single Tapo camera for events."""
    
    def __init__(self, config: Dict[str, Any], mqtt_client: MQTTClientWrapper):
        self.config = config
        self.mqtt_client = mqtt_client
        self.ip = config.get('ip')
        self.port = config.get('port', 2020)
        self.username = config.get('username')
        self.password = config.get('password')
        self.endpoints = config.get('endpoints') or [{
            'name': config.get('name', 'Unknown Camera'),
            'mqtt_prefix': config.get(
                'mqtt_prefix',
                f"garden/camera/{config.get('name', 'camera').lower().replace(' ', '_')}"
            ),
            'model': config.get('model'),
            'mac': config.get('mac'),
        }]
        self.name = config.get('name') or self.endpoints[0]['name']
        
        self.camera = None
        self.running = False
        self.connected = False
        self.event_service = None
        self.pullpoint = None
        self.snapshot_dir = os.environ.get("CAMERA_SNAPSHOT_DIR", DEFAULT_SNAPSHOT_DIR)

    def _health_topics(self) -> List[str]:
        return [f"{ep['mqtt_prefix']}/health" for ep in self.endpoints]

    def _event_topics(self) -> List[Tuple[str, str]]:
        return [(ep['name'], f"{ep['mqtt_prefix']}/event") for ep in self.endpoints]

    def _snapshot_topics(self) -> List[Tuple[str, str, str]]:
        """Return (slug, camera_name, mqtt_topic) per endpoint."""
        rows = []
        for ep in self.endpoints:
            prefix = ep["mqtt_prefix"]
            rows.append((slug_from_mqtt_prefix(prefix), ep["name"], f"{prefix}/snapshot"))
        return rows

    def _publish_health(self, state: str) -> None:
        for topic in self._health_topics():
            self.mqtt_client.publish(topic, state, retain=True)

    def _publish_endpoint_health(self, endpoint: Dict[str, Any], state: str) -> None:
        topic = f"{endpoint['mqtt_prefix']}/health"
        self.mqtt_client.publish(topic, state, retain=True)

    def _publish_status(self, endpoint: Dict[str, Any], probe: Dict[str, Any]) -> None:
        slug = slug_from_mqtt_prefix(endpoint["mqtt_prefix"])
        expected_mac = normalize_mac(endpoint.get("mac"))
        observed_mac = probe.get("mac_observed")
        payload = {
            "timestamp": datetime.now().isoformat(),
            "slug": slug,
            "name": endpoint.get("name"),
            "ip": self.ip,
            "online": bool(probe.get("online")),
            "model": probe.get("model") or endpoint.get("model"),
            "manufacturer": probe.get("manufacturer"),
            "serial": probe.get("serial"),
            "firmware": probe.get("firmware"),
            "mac_expected": expected_mac,
            "mac_observed": observed_mac,
            "mac_match": (
                expected_mac == observed_mac
                if expected_mac and observed_mac
                else None
            ),
            "error": probe.get("error"),
        }
        topic = f"{endpoint['mqtt_prefix']}/status"
        self.mqtt_client.publish(topic, payload)

    def _probe_endpoint(self, endpoint: Dict[str, Any]) -> Dict[str, Any]:
        return probe_onvif(
            self.ip,
            self.username,
            self.password,
            port=self.port,
        )

    def _health_interval_sec(self) -> int:
        return int(os.environ.get("CAMERA_HEALTH_INTERVAL_SEC", DEFAULT_HEALTH_INTERVAL_SEC))
    def connect(self) -> bool:
        """Establish ONVIF connection to the camera."""
        try:
            logger.info(f"Connecting to ONVIF camera '{self.name}' at {self.ip}:{self.port}...")
            self.camera = ONVIFCamera(self.ip, self.port, self.username, self.password)
            
            # Get event service
            self.event_service = self.camera.create_events_service()
            self.connected = True
            logger.info(f"✓ Connected to '{self.name}' at {self.ip}")
            self._publish_health("online")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to camera '{self.name}' ({self.ip}): {e}")
            self.connected = False
            self._publish_health("offline")
            return False

    def monitor_events(self):
        """Main event Loop for the camera."""
        self.running = True
        
        while self.running:
            if not self.connected:
                if not self.connect():
                    time.sleep(30) # Retry after 30s
                    continue
            
            try:
                # Try to create PullPoint subscription
                try:
                    pullpoint = self.camera.create_pullpoint_service()
                except Exception as e:
                    err_str = str(e).lower()
                    if "pullpoint" in err_str or "authority failure" in err_str or "not supported" in err_str:
                        if "authority" in err_str:
                            logger.error(f"❌ Camera '{self.name}' Authority Failure! IMPORTANT: Check if you are using the 'Camera Account' (created in Tapo App -> Device Settings -> Advanced -> Camera Account) and NOT your Tapo App email/password.")
                        
                        logger.warning(f"⚠️ Camera '{self.name}' ONVIF events are unsupported or unauthorized. Falling back to health monitoring only.")
                        # Stay in a simple health loop (interval from health_status_loop)
                        while self.running and self.connected:
                            time.sleep(self._health_interval_sec())
                        continue
                    else:
                        raise e
                
                logger.info(f"Monitoring events for '{self.name}'...")
                
                while self.running:
                    # Pull messages (timeout 10s)
                    try:
                        messages = pullpoint.PullMessages({'Timeout': 'PT10S', 'MessageLimit': 10})
                        
                        for msg in messages.NotificationMessage:
                            self._process_message(msg)
                             
                    except Exception as e:
                        # Log specific ONVIF errors or timeouts
                        if "Timeout" not in str(e):
                            logger.warning(f"PullPoint error for '{self.name}': {e}")
                            break # Reconnect PullPoint
                            
            except Exception as e:
                logger.error(f"Event subscription failed for '{self.name}': {e}")
                self.connected = False
                self._publish_health("offline")
                time.sleep(10)

    def snapshot_loop(self) -> None:
        """Publish JPEG thumbnails for watchdog dashboard (default every 5 min)."""
        interval = int(os.environ.get("CAMERA_SNAPSHOT_INTERVAL_SEC", DEFAULT_SNAPSHOT_INTERVAL_SEC))
        if interval <= 0:
            return

        max_width = int(os.environ.get("CAMERA_SNAPSHOT_MAX_WIDTH", DEFAULT_SNAPSHOT_MAX_WIDTH))
        # Stagger cameras slightly so they do not all hit ONVIF at once.
        time.sleep((hash(self.ip or self.name) % max(interval, 1)) * 0.25)

        while self.running:
            if self.connected and self.camera:
                try:
                    raw = capture_camera_jpeg(
                        self.camera,
                        self.ip,
                        self.username,
                        self.password,
                    )
                    if raw:
                        jpeg = resize_jpeg(raw, max_width)
                        for slug, camera_name, topic in self._snapshot_topics():
                            image_url = save_snapshot_jpeg(slug, jpeg, self.snapshot_dir)
                            payload = build_snapshot_payload(
                                slug,
                                camera_name,
                                datetime.now().isoformat(),
                                image_url,
                            )
                            self.mqtt_client.publish(topic, payload)
                            logger.info(
                                f"Snapshot published for '{camera_name}' ({slug}) "
                                f"→ {topic} ({len(jpeg)} bytes)"
                            )
                except Exception as e:
                    logger.warning(f"Snapshot failed for '{self.name}' ({self.ip}): {e!r}")

            for _ in range(interval):
                if not self.running:
                    return
                time.sleep(1)

    def health_status_loop(self) -> None:
        """Probe ONVIF and publish health + status JSON (default every 5 min)."""
        interval = self._health_interval_sec()
        if interval <= 0:
            return

        time.sleep((hash(self.ip or self.name) % max(interval, 1)) * 0.15)

        while self.running:
            any_online = False
            for endpoint in self.endpoints:
                probe = self._probe_endpoint(endpoint)
                slug = slug_from_mqtt_prefix(endpoint["mqtt_prefix"])
                if probe.get("online"):
                    any_online = True
                    if not self.connected:
                        try:
                            self.camera = ONVIFCamera(
                                self.ip, self.port, self.username, self.password
                            )
                            self.event_service = self.camera.create_events_service()
                            self.connected = True
                        except Exception:
                            self.connected = False
                    self._publish_endpoint_health(endpoint, "online")
                    logger.info(f"Status OK for '{endpoint['name']}' ({slug}) @ {self.ip}")
                else:
                    self._publish_endpoint_health(endpoint, "offline")
                    logger.warning(
                        f"Status FAIL for '{endpoint['name']}' ({slug}) @ {self.ip}: "
                        f"{probe.get('error')}"
                    )
                self._publish_status(endpoint, probe)

            if not any_online:
                self.connected = False
                self.camera = None

            for _ in range(interval):
                if not self.running:
                    return
                time.sleep(1)

    @staticmethod
    def _classify_event_type(topic: str) -> str:
        """Map ONVIF topic to motion/person (C310/C320 and related Tapo models)."""
        topic_lower = topic.lower()
        person_markers = ("person", "human", "humandetect", "linecrossing", "face")
        if any(marker in topic_lower for marker in person_markers):
            return "person"
        motion_markers = ("motion", "cellmotiondetector", "motiondetector", "tamper")
        if any(marker in topic_lower for marker in motion_markers):
            return "motion"
        return "unknown"

    @staticmethod
    def _is_event_active(data: Dict[str, Any]) -> bool:
        """Return True when ONVIF signals an active detection."""
        active_keys = ("IsMotion", "IsInside", "State", "IsAlarm")
        for key in active_keys:
            value = data.get(key)
            if value is not None and str(value).lower() == "true":
                return True
        return False

    def _process_message(self, msg):
        """Parse ONVIF notification message and publish to MQTT."""
        try:
            topic = msg.Topic._value_1
            event_type = self._classify_event_type(topic)

            data = {}
            for item in msg.Message.Data.SimpleItem:
                data[item.Name] = item.Value

            is_active = self._is_event_active(data)

            for camera_name, event_topic in self._event_topics():
                event_payload = {
                    "timestamp": datetime.now().isoformat(),
                    "camera_name": camera_name,
                    "event": event_type,
                    "state": "active" if is_active else "inactive",
                    "raw_topic": topic,
                    "details": data
                }
                logger.info(
                    f"ONVIF event from '{camera_name}' ({self.ip}): topic={topic} data={data} "
                    f"type={event_type} state={event_payload['state']}"
                )
                self.mqtt_client.publish(event_topic, event_payload)

        except Exception as e:
            logger.error(f"Error processing ONVIF message from '{self.name}': {e}")

    def stop(self):
        """Stop the monitor."""
        self.running = False
        self.connected = False
        if self.mqtt_client:
            self._publish_health("offline")

def _merge_camera_configs(cameras: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merge entries that share the same IP/port/credentials (one ONVIF session per device)."""
    merged: Dict[tuple, Dict[str, Any]] = {}
    for cam in cameras:
        key = (
            cam.get('ip'),
            cam.get('port', 2020),
            cam.get('username'),
            cam.get('password'),
        )
        endpoint = {
            'name': cam.get('name', 'Unknown Camera'),
            'mqtt_prefix': cam.get(
                'mqtt_prefix',
                f"garden/camera/{cam.get('name', 'camera').lower().replace(' ', '_')}"
            ),
            'model': cam.get('model'),
            'mac': cam.get('mac'),
        }
        if key not in merged:
            merged[key] = {
                **cam,
                'name': cam.get('name', 'Unknown Camera'),
                'endpoints': [endpoint],
            }
        else:
            merged[key]['endpoints'].append(endpoint)
            names = [ep['name'] for ep in merged[key]['endpoints']]
            merged[key]['name'] = ' / '.join(names)
    return list(merged.values())

class TapoMonitorService:
    """Service to manage monitoring for all configured cameras."""
    
    def __init__(self):
        self.config = get_config()
        mqtt_config = self.config.get('mqtt', {})
        
        self.mqtt_client = MQTTClientWrapper(
            broker_host=mqtt_config.get('broker', {}).get('host'),
            broker_port=mqtt_config.get('broker', {}).get('port', 1883),
            client_id="tapo_event_monitor",
            username=mqtt_config.get('authentication', {}).get('username'),
            password=mqtt_config.get('authentication', {}).get('password')
        )
        
        raw_cameras = self.config.get('cameras', [])
        self.configured_count = len(raw_cameras)
        self.cameras = _merge_camera_configs(raw_cameras)
        self.monitors = []
        self.threads = []
        self.running = False
        
    def start(self):
        """Start monitoring all cameras."""
        logger.info(
            f"Starting Tapo Monitor Service with {len(self.cameras)} device(s) "
            f"({self.configured_count} configured entries)..."
        )
        
        if not self.mqtt_client.connect():
            logger.error("Failed to connect to MQTT broker. Exiting.")
            return

        self.running = True
        
        for cam_config in self.cameras:
            monitor = TapoCameraMonitor(cam_config, self.mqtt_client)
            self.monitors.append(monitor)
            
            thread = threading.Thread(target=monitor.monitor_events, name=f"Monitor-{monitor.name}")
            thread.daemon = True
            thread.start()
            self.threads.append(thread)

            snap_thread = threading.Thread(
                target=monitor.snapshot_loop,
                name=f"Snapshot-{monitor.name}",
            )
            snap_thread.daemon = True
            snap_thread.start()
            self.threads.append(snap_thread)

            health_thread = threading.Thread(
                target=monitor.health_status_loop,
                name=f"Health-{monitor.name}",
            )
            health_thread.daemon = True
            health_thread.start()
            self.threads.append(health_thread)
            
        logger.info("Service started successfully.")
        
        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Gracefully stop all monitors and MQTT client."""
        logger.info("Stopping Tapo Monitor Service...")
        self.running = False
        for monitor in self.monitors:
            monitor.stop()
        if self.mqtt_client:
            self.mqtt_client.disconnect()
        logger.info("Service stopped.")

def main():
    service = TapoMonitorService()
    
    def signal_handler(sig, frame):
        service.stop()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    service.start()

if __name__ == "__main__":
    main()
