#!/usr/bin/env python3
"""
MQTT shutdown listener for Multi-Server Management System.
Listens for shutdown commands via MQTT and executes appropriate shutdown method.
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
import graceful_shutdown

logger = get_logger(__name__)


class ShutdownListener:
    """MQTT listener for server shutdown commands."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize shutdown listener.
        
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
            client_id="multi_server_shutdown_listener",
            username=mqtt_config.get('authentication', {}).get('username'),
            password=mqtt_config.get('authentication', {}).get('password'),
            keepalive=mqtt_config.get('broker', {}).get('keepalive', 60),
            qos=mqtt_config.get('qos', 1)
        )
        
        logger.info("Shutdown listener initialized")
    
    def validate_message(self, payload: str) -> Dict[str, Any]:
        """
        Validate and parse shutdown command message.
        
        Args:
            payload: JSON message payload
            
        Returns:
            Parsed message dictionary or None if invalid
        """
        try:
            message = json.loads(payload)
            
            # Validate required fields
            if message.get('action') != 'shutdown':
                logger.warning(f"Invalid action: {message.get('action')}")
                return None
            
            # Validate shutdown type
            shutdown_type = message.get('type', 'graceful')
            if shutdown_type not in ['graceful', 'force']:
                logger.warning(f"Invalid shutdown type: {shutdown_type}")
                return None
            
            logger.info(f"Valid shutdown command received: type={shutdown_type}")
            return message
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON payload: {e}")
            return None
        except Exception as e:
            logger.error(f"Error validating message: {e}")
            return None
    
    def execute_shutdown(self, server_name: str, shutdown_type: str, timeout: int = 300) -> bool:
        """
        Execute shutdown command using specified type.
        
        Args:
            server_name: Name of the server to shutdown
            shutdown_type: Shutdown type ('graceful' or 'force')
            timeout: Timeout for graceful shutdown (seconds)
            
        Returns:
            True if shutdown initiated successfully, False otherwise
        """
        try:
            # Get server info
            server_info = self.server_managers.get(server_name)
            if not server_info:
                logger.error(f"Server not found: {server_name}")
                return False
            
            server_config = server_info['config']
            manager = server_info['manager']
            
            if shutdown_type == 'graceful':
                logger.info(f"Executing GRACEFUL shutdown for {server_name}...")
                
                # Special handling for servers with Proxmox configuration
                if 'proxmox' in server_config:
                    proxmox_config = server_config.get('proxmox', {})
                    
                    # api_url parsing logic (moved from listener to be more flexible)
                    api_url = proxmox_config.get('api_url', '')
                    proxmox_host = api_url.replace('/api2/json', '').replace('https://', '').replace(':8006', '')
                    
                    return graceful_shutdown.graceful_shutdown(
                        proxmox_host=proxmox_host,
                        proxmox_username=proxmox_config.get('username'),
                        proxmox_password=proxmox_config.get('password'),
                        manager=manager,
                        vm_timeout=server_config.get('shutdown', {}).get('vm_shutdown_timeout', 120),
                        host_delay=30,
                        verify_ssl=proxmox_config.get('verify_ssl', False)
                    )
                else:
                    # Generic graceful shutdown via ACPI power button press
                    logger.info(f"No Proxmox config found for {server_name}, falling back to ACPI power button press")
                    return manager.power_off(force=False)
                
            elif shutdown_type == 'force':
                logger.warning(f"Executing FORCE shutdown for {server_name}...")
                
                # Use the manager directly for force shutdown
                return manager.power_off(force=True)
            
            return False
            
        except Exception as e:
            logger.error(f"Error executing shutdown for {server_name}: {e}")
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
            "action": "shutdown",
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        self.mqtt_client.publish(response_topic, response)
        logger.info(f"Response sent: {message}")
    
    def on_shutdown_command(self, topic: str, payload: str):
        """
        Callback for shutdown command messages.
        
        Args:
            topic: MQTT topic
            payload: Message payload
        """
        logger.info(f"Shutdown command received on topic: {topic}")
        
        # Identify server from topic prefix
        server_name = None
        response_topic = None
        
        for name, info in self.server_managers.items():
            mqtt_prefix = info['config'].get('mqtt_prefix', '')
            if topic.startswith(mqtt_prefix):
                server_name = name
                response_topic = f"{mqtt_prefix}/response"
                break
        
        if not server_name:
            logger.error(f"No server found for topic: {topic}")
            return
        
        # Validate message
        message = self.validate_message(payload)
        if not message:
            logger.error("Invalid shutdown command message")
            return
        
        request_id = message.get('request_id', 'unknown')
        shutdown_type = message.get('type', 'graceful')
        timeout = message.get('timeout', 300)
        
        # Send acknowledgment
        self.send_response(
            response_topic,
            request_id,
            True,
            f"Shutdown command received for {server_name}. Initiating {shutdown_type} shutdown..."
        )
        
        # Execute shutdown
        success = self.execute_shutdown(server_name, shutdown_type, timeout)
        
        if not success:
            self.send_response(
                response_topic,
                request_id,
                False,
                f"Failed to execute {shutdown_type} shutdown for {server_name}"
            )
    
    def start(self):
        """Start the shutdown listener."""
        logger.info("Starting shutdown listener...")
        
        # Connect to MQTT broker
        if not self.mqtt_client.connect():
            logger.error("Failed to connect to MQTT broker")
            return False
        
        # Subscribe to shutdown topics for all servers
        for server_name, server_info in self.server_managers.items():
            mqtt_prefix = server_info['config'].get('mqtt_prefix', '')
            shutdown_topic = f"{mqtt_prefix}/command/shutdown"
            
            if not self.mqtt_client.subscribe(shutdown_topic, self.on_shutdown_command):
                logger.error(f"Failed to subscribe to shutdown topic for {server_name}: {shutdown_topic}")
            else:
                logger.info(f"Subscribed to shutdown topic for {server_name}: {shutdown_topic}")
        
        self.running = True
        logger.info(f"Shutdown listener started for {len(self.server_managers)} server(s)")
        
        # Keep running
        try:
            while self.running:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        
        return True
    
    def stop(self):
        """Stop the shutdown listener."""
        logger.info("Stopping shutdown listener...")
        self.running = False
        if self.mqtt_client:
            self.mqtt_client.disconnect()
        logger.info("Shutdown listener stopped")


def load_config() -> Dict[str, Any]:
    """Load configuration from files."""
    import yaml
    from dotenv import load_dotenv
    
    # Calculate config directory first
    config_dir = Path(__file__).parent.parent.parent / "config"
    env_path = config_dir / ".env"
    
    # Load environment variables from .env file in config directory
    if env_path.exists():
        logger.info(f"Loading environment from: {env_path}")
        load_dotenv(dotenv_path=env_path)
    else:
        logger.warning(f"Environment file NOT found at: {env_path}")
        load_dotenv()
    
    config = {}
    
    # Load MQTT config
    mqtt_config_file = config_dir / "mqtt_config.yaml"
    if mqtt_config_file.exists():
        with open(mqtt_config_file, 'r') as f:
            mqtt_config = yaml.safe_load(f)
            if mqtt_config:
                config.update(mqtt_config)
    
    # Load server config
    server_config_file = config_dir / "server_config.yaml"
    if server_config_file.exists():
        with open(server_config_file, 'r') as f:
            server_config = yaml.safe_load(f)
            if server_config:
                config.update(server_config)
    
    # Replace environment variable placeholders
    import re
    
    def replace_env_vars(obj, path=""):
        if isinstance(obj, dict):
            return {k: replace_env_vars(v, f"{path}.{k}") for k, v in obj.items()}
        elif isinstance(obj, list):
            return [replace_env_vars(item, f"{path}[{i}]") for i, item in enumerate(obj)]
        elif isinstance(obj, str) and '${' in obj:
            # Regex to find all ${VAR} patterns
            pattern = r'\$\{([^}]+)\}'
            
            def replacer(match):
                env_var = match.group(1)
                val = os.getenv(env_var)
                if val is None:
                    logger.error(f"CRITICAL: Environment variable {env_var} NOT SET (path: {path})")
                    return match.group(0) # Keep placeholder
                
                # Check if it's sensitive
                is_sensitive = 'PASS' in env_var or 'KEY' in env_var
                logger.debug(f"Resolved {env_var} in '{path}' -> {'***' if is_sensitive else val}")
                return val
            
            return re.sub(pattern, replacer, obj)
        return obj
    
    config = replace_env_vars(config)
    
    # Final validation - ensure no placeholders remain in critical fields
    def check_placeholders(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                check_placeholders(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                check_placeholders(item, f"{path}[{i}]")
        elif isinstance(obj, str) and obj.startswith('${') and obj.endswith('}'):
            error_msg = f"Configuration Error: Unresolved variable {obj} at {path}. Check your .env file."
            logger.error(error_msg)
            raise ValueError(error_msg)
            
    check_placeholders(config)
    
    return config


if __name__ == "__main__":
    # Load configuration
    config = load_config()
    
    # Create and start listener
    listener = ShutdownListener(config)
    
    # Handle signals for graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Signal received, shutting down listener...")
        listener.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start listener
    success = listener.start()
    sys.exit(0 if success else 1)
