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
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))

from mqtt_client import MQTTClientWrapper
from config_loader import get_config
from logger import get_logger

try:
    from onvif import ONVIFCamera
except ImportError:
    print("❌ Error: onvif-zeep not installed. Run: pip install onvif-zeep")
    sys.exit(1)

logger = get_logger(__name__)

class TapoCameraMonitor:
    """Monitors a single Tapo camera for events."""
    
    def __init__(self, config: Dict[str, Any], mqtt_client: MQTTClientWrapper):
        self.config = config
        self.mqtt_client = mqtt_client
        self.name = config.get('name', 'Unknown Camera')
        self.ip = config.get('ip')
        self.port = config.get('port', 2020)
        self.username = config.get('username')
        self.password = config.get('password')
        self.mqtt_prefix = config.get('mqtt_prefix', f"garden/camera/{self.name.lower().replace(' ', '_')}")
        
        self.camera = None
        self.running = False
        self.connected = False
        self.event_service = None
        self.pullpoint = None
        
        # Topics
        self.health_topic = f"{self.mqtt_prefix}/health"
        self.event_topic = f"{self.mqtt_prefix}/event"
        
    def connect(self) -> bool:
        """Establish ONVIF connection to the camera."""
        try:
            logger.info(f"Connecting to ONVIF camera '{self.name}' at {self.ip}:{self.port}...")
            self.camera = ONVIFCamera(self.ip, self.port, self.username, self.password)
            
            # Get event service
            self.event_service = self.camera.create_events_service()
            self.connected = True
            logger.info(f"✓ Connected to '{self.name}'")
            self.mqtt_client.publish(self.health_topic, "online", retain=True)
            return True
        except Exception as e:
            logger.error(f"Failed to connect to camera '{self.name}': {e}")
            self.connected = False
            self.mqtt_client.publish(self.health_topic, "offline", retain=True)
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
                # Create PullPoint subscription
                pullpoint = self.camera.create_pullpoint_service()
                
                logger.info(f"Monitoring events for '{self.name}'...")
                
                while self.running:
                    # Pull messages (timeout 10s)
                    try:
                        messages = pullpoint.PullMessages({'Timeout': 'PT10S', 'MessageLimit': 10})
                        
                        for msg in messages.NotificationMessage:
                            self._process_message(msg)
                            
                        # Periodically refresh health status
                        if int(time.time()) % 60 == 0:
                             self.mqtt_client.publish(self.health_topic, "online", retain=True)
                             
                    except Exception as e:
                        # Log specific ONVIF errors or timeouts
                        if "Timeout" not in str(e):
                            logger.warning(f"PullPoint error for '{self.name}': {e}")
                            break # Reconnect PullPoint
                            
            except Exception as e:
                logger.error(f"Event subscription failed for '{self.name}': {e}")
                self.connected = False
                self.mqtt_client.publish(self.health_topic, "offline", retain=True)
                time.sleep(10)

    def _process_message(self, msg):
        """Parse ONVIF notification message and publish to MQTT."""
        try:
            # Tapo cameras usually send RuleEngine/CellMotionDetector events
            topic = msg.Topic._value_1
            
            event_type = "unknown"
            if "MotionDetector" in topic:
                event_type = "motion"
            elif "CellMotionDetector" in topic:
                event_type = "motion"
            elif "Person" in topic:
                event_type = "person"
                
            # Extract state (simple binary for now)
            # PullPoint messages wrap data in simple item elements
            data = {}
            for item in msg.Message.Data.SimpleItem:
                data[item.Name] = item.Value
                
            is_active = data.get('IsInside') == 'true' or data.get('State') == 'true'
            
            event_payload = {
                "timestamp": datetime.now().isoformat(),
                "camera_name": self.name,
                "event": event_type,
                "state": "active" if is_active else "inactive",
                "raw_topic": topic,
                "details": data
            }
            
            logger.info(f"Event from '{self.name}': {event_type} -> {event_payload['state']}")
            self.mqtt_client.publish(self.event_topic, event_payload)
            
        except Exception as e:
            logger.error(f"Error processing ONVIF message from '{self.name}': {e}")

    def stop(self):
        """Stop the monitor."""
        self.running = False
        self.connected = False
        if self.mqtt_client:
            self.mqtt_client.publish(self.health_topic, "offline", retain=True)

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
        
        self.cameras = self.config.get('cameras', [])
        self.monitors = []
        self.threads = []
        self.running = False
        
    def start(self):
        """Start monitoring all cameras."""
        logger.info(f"Starting Tapo Monitor Service with {len(self.cameras)} camera(s)...")
        
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
