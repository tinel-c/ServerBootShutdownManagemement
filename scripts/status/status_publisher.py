#!/usr/bin/env python3
"""
Status publisher for Dell & HP Server Management System.
Publishes server status to MQTT at regular intervals.
Supports multiple servers (IPMI and iLO).
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
from server_factory import get_all_server_managers
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
        self.monitoring_config = config.get('monitoring', {})
        
        # Create MQTT client
        self.mqtt_client = MQTTClientWrapper(
            broker_host=mqtt_config.get('broker', {}).get('host'),
            broker_port=mqtt_config.get('broker', {}).get('port', 1883),
            client_id="server_status_publisher",
            username=mqtt_config.get('authentication', {}).get('username'),
            password=mqtt_config.get('authentication', {}).get('password'),
            keepalive=mqtt_config.get('broker', {}).get('keepalive', 60),
            qos=mqtt_config.get('qos', 1)
        )
        
        # Global publish interval (default fallback)
        self.publish_interval = self.monitoring_config.get('status_interval', 30)
        
        # Initialize server managers
        try:
            self.server_managers = get_all_server_managers(config)
            logger.info(f"Initialized {len(self.server_managers)} server manager(s)")
        except Exception as e:
            logger.error(f"Failed to initialize server managers: {e}")
            self.server_managers = {}
        
        logger.info("Status publisher initialized")
    
    def get_server_status(self, server_name: str, manager_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get current status for a specific server.
        
        Args:
            server_name: Name of the server
            manager_info: Dictionary containing 'config' and 'manager'
            
        Returns:
            Dictionary with server status information
        """
        server_config = manager_info['config']
        manager = manager_info['manager']
        
        status = {
            "timestamp": datetime.now().isoformat(),
            "server_name": server_name,
            "server_type": server_config.get('type', 'unknown'),
            "server_state": "unknown",
            "uptime": None,
            "power_status": None,
            "health": None
        }
        
        try:
            # Get power status
            # Both IPMIWrapper and ILOWrapper implement get_power_status()
            power_status = manager.get_power_status()
            status["power_status"] = power_status
            
            if power_status == "on":
                status["server_state"] = "online"
                
                # Extended status based on server type
                if server_config.get('type') == 'ilo':
                    # iLO specific status
                    # Assuming ILOWrapper has get_server_health() or similar
                    # For now just basic status
                    pass
                    
                elif server_config.get('type') == 'ipmi':
                    # IPMI specific status
                    # Get chassis status if available
                    if hasattr(manager, 'get_chassis_status'):
                        chassis_status = manager.get_chassis_status()
                        if chassis_status and "System Power" in chassis_status:
                            status["power_info"] = chassis_status["System Power"]
                
                # Try to get system metrics (requires guest agent or similar, usually only possible via Proxmox API or SSH)
                # Since we don't have proxmox client here for status, we skip deep system metrics
                # unless we want to instantiate it specifically for T310.
                # For now, we keep it simple conformant with multi-server architecture.
                
            elif power_status == "off":
                status["server_state"] = "offline"
            
        except Exception as e:
            logger.error(f"Error getting status for {server_name}: {e}")
            status["server_state"] = "error"
            status["error"] = str(e)
        
        return status
    
    def publish_all_statuses(self):
        """Publish status for all servers to MQTT."""
        for server_name, manager_info in self.server_managers.items():
            try:
                # Determine topic
                mqtt_prefix = manager_info['config'].get('mqtt_prefix', f"server/{server_name}")
                status_topic = f"{mqtt_prefix}/status"
                
                # Get status
                status = self.get_server_status(server_name, manager_info)
                
                # Publish
                if self.mqtt_client.publish(status_topic, status):
                    logger.debug(f"Status published for {server_name}: {status['server_state']}")
                else:
                    logger.warning(f"Failed to publish status for {server_name}")
                    
            except Exception as e:
                logger.error(f"Error publishing status for {server_name}: {e}")
    
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
                self.publish_all_statuses()
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
    
    # Calculate config directory first
    config_dir = Path(__file__).parent.parent.parent / "config"
    env_path = config_dir / ".env"
    
    # Load environment variables from .env file in config directory
    if env_path.exists():
        print(f"Loading environment from: {env_path}")
        load_dotenv(dotenv_path=env_path)
    else:
        print(f"WARNING: .env file not found at: {env_path}")
        load_dotenv()
    
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
            val = os.getenv(env_var)
            if val is None:
                print(f"WARNING: Environment variable {env_var} not set! Keeping placeholder.")
                return obj
            return val
        return obj
    
    config = replace_env_vars(config)
    
    # Validate critical config
    broker_port = config.get('mqtt', {}).get('broker', {}).get('port')
    if isinstance(broker_port, str) and broker_port.startswith('${'):
        raise ValueError(f"Configuration Error: MQTT_BROKER_PORT not resolved. Value: {broker_port}. Check your .env file.")
    
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
