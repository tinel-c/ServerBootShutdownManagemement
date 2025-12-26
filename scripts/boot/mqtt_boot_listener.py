#!/usr/bin/env python3
"""
MQTT boot listener for Multi-Server Management System.
Listens for boot commands via MQTT and executes appropriate boot method.
Supports Dell T310 (IPMI) and HP DL360p (iLO) servers.
"""

import sys
import os
import json
import signal
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))

from mqtt_client import MQTTClientWrapper
from server_factory import get_all_server_managers
from logger import get_logger
import wol_boot

logger = get_logger(__name__)


class BootListener:
    """MQTT listener for server boot commands."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize boot listener.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.mqtt_client = None
        self.running = False
        self.server_managers = {}
        
        # Extract configuration
        mqtt_config = config.get('mqtt', {})
        
        # Get all server managers
        try:
            self.server_managers = get_all_server_managers(config)
            logger.info(f"Initialized {len(self.server_managers)} server manager(s)")
        except Exception as e:
            logger.error(f"Failed to initialize server managers: {e}")
        
        # Create MQTT client
        self.mqtt_client = MQTTClientWrapper(
            broker_host=mqtt_config.get('broker', {}).get('host'),
            broker_port=mqtt_config.get('broker', {}).get('port', 1883),
            client_id="multi_server_boot_listener",
            username=mqtt_config.get('authentication', {}).get('username'),
            password=mqtt_config.get('authentication', {}).get('password'),
            keepalive=mqtt_config.get('broker', {}).get('keepalive', 60),
            qos=mqtt_config.get('qos', 1)
        )
        
        logger.info("Boot listener initialized")
    
    def validate_message(self, payload: str) -> Dict[str, Any]:
        """
        Validate and parse boot command message.
        
        Args:
            payload: JSON message payload
            
        Returns:
            Parsed message dictionary or None if invalid
        """
        try:
            message = json.loads(payload)
            
            # Validate required fields
            if message.get('action') != 'boot':
                logger.warning(f"Invalid action: {message.get('action')}")
                return None
            
            # Validate boot method
            method = message.get('method', 'wol')
            if method not in ['wol', 'ipmi', 'ilo']:
                logger.warning(f"Invalid boot method: {method}")
                return None
            
            logger.info(f"Valid boot command received: method={method}")
            return message
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON payload: {e}")
            return None
        except Exception as e:
            logger.error(f"Error validating message: {e}")
            return None
    
    def execute_boot(self, server_name: str, method: str) -> bool:
        """
        Execute boot command using specified method.
        
        Args:
            server_name: Name of the server to boot
            method: Boot method ('wol', 'ipmi', or 'ilo')
            
        Returns:
            True if boot successful, False otherwise
        """
        try:
            # Get server info
            server_info = self.server_managers.get(server_name)
            if not server_info:
                logger.error(f"Server not found: {server_name}")
                return False
            
            server_config = server_info['config']
            manager = server_info['manager']
            
            if method == 'wol':
                mac_address = server_config.get('mac_address')
                if not mac_address:
                    logger.error(f"MAC address not configured for {server_name}")
                    return False
                
                logger.info(f"Executing Wake-on-LAN boot for {server_name}: {mac_address}")
                return wol_boot.boot_via_wol(mac_address)
                
            elif method in ['ipmi', 'ilo']:
                # Use the server manager (IPMI or iLO wrapper)
                logger.info(f"Executing {method.upper()} boot for {server_name}")
                
                # Check if already on
                current_status = manager.get_power_status()
                if current_status == "on":
                    logger.info(f"{server_name} is already powered on")
                    return True
                
                # Power on
                if not manager.power_on():
                    logger.error(f"Failed to send power on command to {server_name}")
                    return False
                
                # Wait for boot
                logger.info(f"Waiting for {server_name} to boot...")
                if manager.wait_for_power_state("on", timeout=120):
                    logger.info(f"{server_name} booted successfully")
                    return True
                else:
                    logger.warning(f"{server_name} boot verification timed out")
                    return False
            
            return False
            
        except Exception as e:
            logger.error(f"Error executing boot for {server_name}: {e}")
            return False
    
    def send_response(self, response_topic: str, request_id: str, success: bool, message: str):
        """
        Send response message to MQTT.
        
        Args:
            response_topic: Topic to send response to
            request_id: Original request ID
            success: Whether operation was successful
            message: Response message
        """
        response = {
            "request_id": request_id,
            "action": "boot",
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        self.mqtt_client.publish(response_topic, response)
        logger.info(f"Response sent: {message}")
    
    def on_boot_command(self, topic: str, payload: str):
        """
        Callback for boot command messages.
        
        Args:
            topic: MQTT topic
            payload: Message payload
        """
        logger.info(f"Boot command received on topic: {topic}")
        
        # Extract server name from topic (e.g., "dell/t310/command/boot" or "hp/dl360p/command/boot")
        # Find matching server by mqtt_prefix
        server_name = None
        response_topic = None
        
        for name, info in self.server_managers.items():
            mqtt_prefix = info['config'].get('mqtt_prefix', '')
            if topic.startswith(mqtt_prefix):
                server_name = name
                # Response topic is mqtt_prefix + "/response"
                response_topic = f"{mqtt_prefix}/response"
                break
        
        if not server_name:
            logger.error(f"No server found for topic: {topic}")
            return
        
        # Validate message
        message = self.validate_message(payload)
        if not message:
            logger.error("Invalid boot command message")
            return
        
        request_id = message.get('request_id', 'unknown')
        method = message.get('method', 'wol')
        
        # Execute boot
        success = self.execute_boot(server_name, method)
        
        # Send response
        if success:
            self.send_response(
                response_topic,
                request_id,
                True,
                f"{server_name} boot initiated successfully via {method.upper()}"
            )
        else:
            self.send_response(
                response_topic,
                request_id,
                False,
                f"Failed to boot {server_name} via {method.upper()}"
            )
    
    def start(self):
        """Start the boot listener."""
        logger.info("Starting boot listener...")
        
        # Connect to MQTT broker
        if not self.mqtt_client.connect():
            logger.error("Failed to connect to MQTT broker")
            return False
        
        # Subscribe to boot command topics for all servers
        for server_name, server_info in self.server_managers.items():
            mqtt_prefix = server_info['config'].get('mqtt_prefix', '')
            boot_topic = f"{mqtt_prefix}/command/boot"
            
            if not self.mqtt_client.subscribe(boot_topic, self.on_boot_command):
                logger.error(f"Failed to subscribe to boot topic for {server_name}: {boot_topic}")
            else:
                logger.info(f"Subscribed to boot topic for {server_name}: {boot_topic}")
        
        self.running = True
        logger.info(f"Boot listener started for {len(self.server_managers)} server(s)")
        
        # Keep running
        try:
            while self.running:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        
        return True
    
    def stop(self):
        """Stop the boot listener."""
        logger.info("Stopping boot listener...")
        self.running = False
        if self.mqtt_client:
            self.mqtt_client.disconnect()
        logger.info("Boot listener stopped")


def load_config() -> Dict[str, Any]:
    """Load configuration from files."""
    import yaml
    from dotenv import load_dotenv
    
    # Calculate config directory first
    config_dir = Path(__file__).parent.parent.parent / "config"
    env_path = config_dir / ".env"
    
    # Load environment variables from .env file in config directory
    if env_path.exists():
        # logger is not available here unless we move import or pass it, but print works for startup
        print(f"Loading environment from: {env_path}")
        load_dotenv(dotenv_path=env_path)
    else:
        print(f"WARNING: .env file not found at: {env_path}")
        # Try loading from current directory as fallback
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
    
    # Create and start listener
    listener = BootListener(config)
    
    # Handle signals for graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Signal received, shutting down...")
        listener.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start listener
    success = listener.start()
    sys.exit(0 if success else 1)
