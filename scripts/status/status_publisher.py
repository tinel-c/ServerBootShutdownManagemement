#!/usr/bin/env python3
"""
Status publisher for Dell T310 Management System.
Publishes server status to MQTT at regular intervals.
"""

import sys
import os
import json
import signal
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))

from mqtt_client import MQTTClientWrapper
from ipmi_wrapper import IPMIWrapper
from logger import get_logger

logger = get_logger(__name__)


class StatusPublisher:
    """Publishes server status to MQTT."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize status publisher.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.mqtt_client = None
        self.running = False
        
        # Extract configuration
        mqtt_config = config.get('mqtt', {})
        self.server_config = config.get('server', {})
        self.monitoring_config = config.get('monitoring', {})
        
        # Create MQTT client
        self.mqtt_client = MQTTClientWrapper(
            broker_host=mqtt_config.get('broker', {}).get('host'),
            broker_port=mqtt_config.get('broker', {}).get('port', 1883),
            client_id="dell_t310_status_publisher",
            username=mqtt_config.get('authentication', {}).get('username'),
            password=mqtt_config.get('authentication', {}).get('password'),
            keepalive=mqtt_config.get('broker', {}).get('keepalive', 60),
            qos=mqtt_config.get('qos', 1)
        )
        
        self.status_topic = mqtt_config.get('topics', {}).get('status', 'dell/t310/status')
        self.publish_interval = self.monitoring_config.get('status_interval', 30)
        
        # Create IPMI wrapper
        ipmi_config = self.server_config.get('ipmi', {})
        self.ipmi = IPMIWrapper(
            host=ipmi_config.get('host'),
            username=ipmi_config.get('username'),
            password=ipmi_config.get('password')
        )
        
        logger.info("Status publisher initialized")
    
    def get_server_status(self) -> Dict[str, Any]:
        """
        Get current server status.
        
        Returns:
            Dictionary with server status information
        """
        status = {
            "timestamp": datetime.now().isoformat(),
            "server_name": self.server_config.get('name', 'Dell T310'),
            "server_state": "unknown",
            "uptime": None,
            "cpu_usage": None,
            "memory_usage": None,
            "temperature": None,
            "power_status": None
        }
        
        try:
            # Get power status
            power_status = self.ipmi.get_power_status()
            status["power_status"] = power_status
            
            if power_status == "on":
                status["server_state"] = "online"
                
                # Get chassis status for additional info
                chassis_status = self.ipmi.get_chassis_status()
                if chassis_status:
                    # Extract uptime if available
                    if "System Power" in chassis_status:
                        status["power_info"] = chassis_status["System Power"]
                
                # Try to get system metrics if psutil is available
                try:
                    import psutil
                    
                    # CPU usage
                    status["cpu_usage"] = psutil.cpu_percent(interval=1)
                    
                    # Memory usage
                    memory = psutil.virtual_memory()
                    status["memory_usage"] = memory.percent
                    status["memory_total_gb"] = round(memory.total / (1024**3), 2)
                    status["memory_used_gb"] = round(memory.used / (1024**3), 2)
                    
                    # Disk usage
                    disk = psutil.disk_usage('/')
                    status["disk_usage"] = disk.percent
                    status["disk_total_gb"] = round(disk.total / (1024**3), 2)
                    status["disk_used_gb"] = round(disk.used / (1024**3), 2)
                    
                    # Uptime
                    boot_time = psutil.boot_time()
                    uptime_seconds = time.time() - boot_time
                    status["uptime"] = int(uptime_seconds)
                    status["uptime_formatted"] = self._format_uptime(uptime_seconds)
                    
                except ImportError:
                    logger.debug("psutil not available, skipping system metrics")
                except Exception as e:
                    logger.warning(f"Error getting system metrics: {e}")
                
            elif power_status == "off":
                status["server_state"] = "offline"
            
        except Exception as e:
            logger.error(f"Error getting server status: {e}")
            status["server_state"] = "error"
            status["error"] = str(e)
        
        return status
    
    def _format_uptime(self, seconds: float) -> str:
        """
        Format uptime in human-readable format.
        
        Args:
            seconds: Uptime in seconds
            
        Returns:
            Formatted uptime string
        """
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        
        return " ".join(parts) if parts else "< 1m"
    
    def publish_status(self):
        """Publish current server status to MQTT."""
        try:
            status = self.get_server_status()
            
            if self.mqtt_client.publish(self.status_topic, status):
                logger.debug(f"Status published: {status['server_state']}")
            else:
                logger.warning("Failed to publish status")
                
        except Exception as e:
            logger.error(f"Error publishing status: {e}")
    
    def start(self):
        """Start the status publisher."""
        logger.info("Starting status publisher...")
        
        # Connect to MQTT broker
        if not self.mqtt_client.connect():
            logger.error("Failed to connect to MQTT broker")
            return False
        
        self.running = True
        logger.info(f"Status publisher started. Publishing every {self.publish_interval} seconds")
        
        # Main loop
        try:
            while self.running:
                self.publish_status()
                time.sleep(self.publish_interval)
                
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Error in status publisher loop: {e}")
        
        return True
    
    def stop(self):
        """Stop the status publisher."""
        logger.info("Stopping status publisher...")
        self.running = False
        if self.mqtt_client:
            self.mqtt_client.disconnect()
        logger.info("Status publisher stopped")


def load_config() -> Dict[str, Any]:
    """Load configuration from files."""
    import yaml
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Load YAML configuration
    config_dir = Path(__file__).parent.parent.parent / "config"
    
    config = {}
    
    # Load MQTT config
    mqtt_config_file = config_dir / "mqtt_config.yaml"
    if mqtt_config_file.exists():
        with open(mqtt_config_file, 'r') as f:
            mqtt_config = yaml.safe_load(f)
            config.update(mqtt_config)
    
    # Load server config
    server_config_file = config_dir / "server_config.yaml"
    if server_config_file.exists():
        with open(server_config_file, 'r') as f:
            server_config = yaml.safe_load(f)
            config.update(server_config)
    
    # Replace environment variable placeholders
    def replace_env_vars(obj):
        if isinstance(obj, dict):
            return {k: replace_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [replace_env_vars(item) for item in obj]
        elif isinstance(obj, str) and obj.startswith('${') and obj.endswith('}'):
            env_var = obj[2:-1]
            return os.getenv(env_var, obj)
        return obj
    
    config = replace_env_vars(config)
    
    return config


if __name__ == "__main__":
    # Load configuration
    config = load_config()
    
    # Create and start publisher
    publisher = StatusPublisher(config)
    
    # Handle signals for graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Signal received, shutting down...")
        publisher.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start publisher
    success = publisher.start()
    sys.exit(0 if success else 1)
