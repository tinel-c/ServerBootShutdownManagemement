#!/usr/bin/env python3
"""
MQTT shutdown listener for Dell T310 Management System.
Listens for shutdown commands via MQTT and executes appropriate shutdown method.
"""

import sys
import os
import json
import signal
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))

from mqtt_client import MQTTClientWrapper
from logger import get_logger
import graceful_shutdown
import force_shutdown

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
        
        # Extract configuration
        mqtt_config = config.get('mqtt', {})
        self.server_config = config.get('server', {})
        
        # Create MQTT client
        self.mqtt_client = MQTTClientWrapper(
            broker_host=mqtt_config.get('broker', {}).get('host'),
            broker_port=mqtt_config.get('broker', {}).get('port', 1883),
            client_id="dell_t310_shutdown_listener",
            username=mqtt_config.get('authentication', {}).get('username'),
            password=mqtt_config.get('authentication', {}).get('password'),
            keepalive=mqtt_config.get('broker', {}).get('keepalive', 60),
            qos=mqtt_config.get('qos', 1)
        )
        
        self.shutdown_topic = mqtt_config.get('topics', {}).get('command_shutdown', 'dell/t310/command/shutdown')
        self.response_topic = mqtt_config.get('topics', {}).get('response', 'dell/t310/response')
        
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
    
    def execute_shutdown(self, shutdown_type: str, timeout: int = 300) -> bool:
        """
        Execute shutdown command using specified type.
        
        Args:
            shutdown_type: Shutdown type ('graceful' or 'force')
            timeout: Timeout for graceful shutdown (seconds)
            
        Returns:
            True if shutdown initiated successfully, False otherwise
        """
        try:
            if shutdown_type == 'graceful':
                logger.info("Executing graceful shutdown...")
                
                proxmox_config = self.server_config.get('proxmox', {})
                ipmi_config = self.server_config.get('ipmi', {})
                shutdown_config = self.server_config.get('shutdown', {})
                
                return graceful_shutdown.graceful_shutdown(
                    proxmox_host=proxmox_config.get('api_url', '').replace('/api2/json', '').replace('https://', '').replace(':8006', ''),
                    proxmox_username=proxmox_config.get('username'),
                    proxmox_password=proxmox_config.get('password'),
                    ipmi_host=ipmi_config.get('host'),
                    ipmi_username=ipmi_config.get('username'),
                    ipmi_password=ipmi_config.get('password'),
                    vm_timeout=shutdown_config.get('vm_shutdown_timeout', 120),
                    host_delay=30,
                    verify_ssl=proxmox_config.get('verify_ssl', False)
                )
                
            elif shutdown_type == 'force':
                logger.warning("Executing FORCE shutdown...")
                
                ipmi_config = self.server_config.get('ipmi', {})
                
                return force_shutdown.force_shutdown(
                    host=ipmi_config.get('host'),
                    username=ipmi_config.get('username'),
                    password=ipmi_config.get('password')
                )
            
            return False
            
        except Exception as e:
            logger.error(f"Error executing shutdown: {e}")
            return False
    
    def send_response(self, request_id: str, success: bool, message: str):
        """
        Send response message to MQTT.
        
        Args:
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
        
        self.mqtt_client.publish(self.response_topic, response)
        logger.info(f"Response sent: {message}")
    
    def on_shutdown_command(self, topic: str, payload: str):
        """
        Callback for shutdown command messages.
        
        Args:
            topic: MQTT topic
            payload: Message payload
        """
        logger.info(f"Shutdown command received on topic: {topic}")
        
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
            request_id,
            True,
            f"Shutdown command received. Initiating {shutdown_type} shutdown..."
        )
        
        # Execute shutdown (this will disconnect us, so send response first)
        success = self.execute_shutdown(shutdown_type, timeout)
        
        if not success:
            self.send_response(
                request_id,
                False,
                f"Failed to execute {shutdown_type} shutdown"
            )
    
    def start(self):
        """Start the shutdown listener."""
        logger.info("Starting shutdown listener...")
        
        # Connect to MQTT broker
        if not self.mqtt_client.connect():
            logger.error("Failed to connect to MQTT broker")
            return False
        
        # Subscribe to shutdown command topic
        if not self.mqtt_client.subscribe(self.shutdown_topic, self.on_shutdown_command):
            logger.error("Failed to subscribe to shutdown topic")
            return False
        
        self.running = True
        logger.info(f"Shutdown listener started. Listening on topic: {self.shutdown_topic}")
        
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
    
    # Load environment variables from .env file in config directory
    load_dotenv(dotenv_path=config_dir / ".env")
    
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
