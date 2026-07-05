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
import subprocess
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
    
    def get_server_status_from_proxmox(self, server_name: str, server_config: Dict[str, Any]) -> Optional[str]:
        """
        Get server power status from Proxmox API instead of IPMI/iLO.
        
        Args:
            server_name: Name of the server
            server_config: Server configuration dictionary
            
        Returns:
            Power status string ("on" or "off") or None on error
        """
        proxmox_config = server_config.get('proxmox', {})
        if not proxmox_config:
            logger.warning(f"No Proxmox configuration found for {server_name}")
            return None
        
        # Parse API URL to get host
        api_url = proxmox_config.get('api_url', '')
        proxmox_host = api_url.replace('/api2/json', '').replace('https://', '').replace('http://', '').replace(':8006', '')
        
        try:
            from proxmoxer import ProxmoxAPI
            
            proxmox = ProxmoxAPI(
                proxmox_host,
                user=proxmox_config.get('username'),
                password=proxmox_config.get('password'),
                verify_ssl=proxmox_config.get('verify_ssl', False),
                timeout=15  # Increased timeout from 5 to 15
            )
            
            # Get nodes status
            nodes = proxmox.nodes.get()
            
            # For standalone Proxmox, there should be one node
            # If node status is 'online', server is on
            for node in nodes:
                node_status = node.get('status', 'unknown')
                logger.debug(f"Proxmox node {node.get('node')} status: {node_status}")
                if node_status == 'online':
                    logger.info(f"{server_name} is ONLINE (via Proxmox API)")
                    return "on"
            
            # If no nodes are online, server is off
            logger.info(f"{server_name} is OFFLINE (via Proxmox API)")
            return "off"
            
        except ImportError:
            logger.error("proxmoxer library not installed. Install with: pip install proxmoxer")
            return None
        except Exception as e:
            logger.warning(f"Error getting Proxmox API status for {server_name}: {e}. Falling back to Ping.")
            
            # Fallback to Ping if Proxmox API fails
            if self.ping_host(proxmox_host):
                logger.info(f"{server_name} is reachable via PING (Server is ON, but API failed)")
                return "on"
            else:
                logger.info(f"{server_name} is unreachable via PING (Server is OFF)")
                return "off"

    def ping_host(self, host: str, count: int = 2, timeout: int = 2) -> bool:
        """
        Ping a host to see if it's alive.
        
        Args:
            host: Hostname or IP address
            count: Number of pings to send
            timeout: Timeout per ping in seconds
            
        Returns:
            True if host responds, False otherwise
        """
        # Determine command based on OS
        import platform
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        timeout_param = '-w' if platform.system().lower() == 'windows' else '-W'
        
        # Build command
        command = ['ping', param, str(count), timeout_param, str(timeout * 1000 if platform.system().lower() == 'windows' else timeout), host]
        
        try:
            subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return True
        except (subprocess.CalledProcessError, Exception):
            return False
    
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
            server_type = server_config.get('type', 'unknown')

            if server_type == 'linux_tuya':
                power_status = manager.get_power_status()
                status["power_status"] = power_status
                if power_status == "on":
                    status["server_state"] = "online"
                    status["uptime"] = manager.get_uptime()
                elif power_status == "off":
                    status["server_state"] = "offline"
            else:
                if server_name == "Dell T310" and server_config.get('proxmox'):
                    power_status = self.get_server_status_from_proxmox(server_name, server_config)
                else:
                    power_status = manager.get_power_status()

                status["power_status"] = power_status

                if power_status == "on":
                    status["server_state"] = "online"
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
        elif isinstance(obj, str) and '${' in obj:
            # Use regex to replace all ${VAR} patterns in the string
            import re
            pattern = r'\$\{([^}]+)\}'
            
            def replacer(match):
                env_var = match.group(1)
                val = os.getenv(env_var)
                if val is None:
                    print(f"WARNING: Environment variable {env_var} not set! Keeping placeholder.")
                    return match.group(0)  # Keep original placeholder
                return val
            
            return re.sub(pattern, replacer, obj)
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
