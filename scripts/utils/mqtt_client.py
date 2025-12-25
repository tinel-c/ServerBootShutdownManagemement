#!/usr/bin/env python3
"""
MQTT client wrapper for Dell T310 Management System.
Provides a reusable MQTT client with auto-reconnect and error handling.
"""

import json
import time
from typing import Callable, Optional, Dict, Any
import paho.mqtt.client as mqtt
from logger import get_logger

logger = get_logger(__name__)


class MQTTClientWrapper:
    """Wrapper class for MQTT client operations."""
    
    def __init__(
        self,
        broker_host: str,
        broker_port: int = 1883,
        client_id: str = None,
        username: str = None,
        password: str = None,
        keepalive: int = 60,
        qos: int = 1,
        use_tls: bool = False,
        tls_config: Dict[str, str] = None
    ):
        """
        Initialize MQTT client wrapper.
        
        Args:
            broker_host: MQTT broker hostname or IP
            broker_port: MQTT broker port (default: 1883)
            client_id: MQTT client ID (auto-generated if None)
            username: MQTT username (optional)
            password: MQTT password (optional)
            keepalive: Keepalive interval in seconds
            qos: Quality of Service level (0, 1, or 2)
            use_tls: Enable TLS/SSL
            tls_config: TLS configuration dictionary
        """
        self.broker_host = broker_host
        self.broker_port = int(broker_port)
        self.keepalive = int(keepalive)
        self.qos = int(qos)
        self.use_tls = use_tls
        self.tls_config = tls_config or {}
        
        # Create MQTT client
        self.client = mqtt.Client(client_id=client_id or "")
        
        # Set username and password if provided
        if username and password:
            self.client.username_pw_set(username, password)
            logger.info(f"MQTT authentication configured for user: {username}")
        
        # Configure TLS if enabled
        if use_tls:
            self._configure_tls()
        
        # Set callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        
        # Connection state
        self.connected = False
        self.subscriptions = {}  # topic -> callback mapping
        
        logger.info(f"MQTT client initialized for broker: {broker_host}:{broker_port}")
    
    def _configure_tls(self):
        """Configure TLS/SSL for MQTT connection."""
        try:
            self.client.tls_set(
                ca_certs=self.tls_config.get('ca_certs'),
                certfile=self.tls_config.get('certfile'),
                keyfile=self.tls_config.get('keyfile')
            )
            logger.info("TLS/SSL configured for MQTT connection")
        except Exception as e:
            logger.error(f"Failed to configure TLS: {e}")
            raise
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for when client connects to broker."""
        if rc == 0:
            self.connected = True
            logger.info(f"Connected to MQTT broker: {self.broker_host}:{self.broker_port}")
            
            # Re-subscribe to all topics after reconnection
            for topic in self.subscriptions.keys():
                self.client.subscribe(topic, qos=self.qos)
                logger.info(f"Re-subscribed to topic: {topic}")
        else:
            self.connected = False
            error_messages = {
                1: "Connection refused - incorrect protocol version",
                2: "Connection refused - invalid client identifier",
                3: "Connection refused - server unavailable",
                4: "Connection refused - bad username or password",
                5: "Connection refused - not authorized"
            }
            error_msg = error_messages.get(rc, f"Unknown error code: {rc}")
            logger.error(f"Failed to connect to MQTT broker: {error_msg}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for when client disconnects from broker."""
        self.connected = False
        if rc != 0:
            logger.warning(f"Unexpected disconnection from MQTT broker (code: {rc})")
        else:
            logger.info("Disconnected from MQTT broker")
    
    def _on_message(self, client, userdata, msg):
        """Callback for when a message is received."""
        topic = msg.topic
        payload = msg.payload.decode('utf-8')
        
        logger.debug(f"Received message on topic '{topic}': {payload}")
        
        # Call the registered callback for this topic
        if topic in self.subscriptions:
            callback = self.subscriptions[topic]
            try:
                callback(topic, payload)
            except Exception as e:
                logger.error(f"Error in message callback for topic '{topic}': {e}")
        else:
            logger.warning(f"No callback registered for topic: {topic}")
    
    def connect(self, retry_count: int = 5, retry_delay: int = 5) -> bool:
        """
        Connect to MQTT broker with retry logic.
        
        Args:
            retry_count: Number of connection attempts
            retry_delay: Delay between retries in seconds
            
        Returns:
            True if connected successfully, False otherwise
        """
        for attempt in range(1, retry_count + 1):
            try:
                logger.info(f"Connecting to MQTT broker (attempt {attempt}/{retry_count})...")
                self.client.connect(self.broker_host, self.broker_port, self.keepalive)
                self.client.loop_start()
                
                # Wait for connection to establish
                timeout = 10
                start_time = time.time()
                while not self.connected and time.time() - start_time < timeout:
                    time.sleep(0.1)
                
                if self.connected:
                    logger.info("Successfully connected to MQTT broker")
                    return True
                else:
                    logger.warning(f"Connection attempt {attempt} timed out")
                    
            except Exception as e:
                logger.error(f"Connection attempt {attempt} failed: {e}")
            
            if attempt < retry_count:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
        
        logger.error("Failed to connect to MQTT broker after all attempts")
        return False
    
    def disconnect(self):
        """Disconnect from MQTT broker."""
        logger.info("Disconnecting from MQTT broker...")
        self.client.loop_stop()
        self.client.disconnect()
        self.connected = False
    
    def subscribe(self, topic: str, callback: Callable[[str, str], None]) -> bool:
        """
        Subscribe to an MQTT topic.
        
        Args:
            topic: MQTT topic to subscribe to
            callback: Function to call when message received (topic, payload)
            
        Returns:
            True if subscription successful, False otherwise
        """
        if not self.connected:
            logger.error("Cannot subscribe: not connected to broker")
            return False
        
        try:
            result, mid = self.client.subscribe(topic, qos=self.qos)
            if result == mqtt.MQTT_ERR_SUCCESS:
                self.subscriptions[topic] = callback
                logger.info(f"Subscribed to topic: {topic}")
                return True
            else:
                logger.error(f"Failed to subscribe to topic '{topic}': {result}")
                return False
        except Exception as e:
            logger.error(f"Error subscribing to topic '{topic}': {e}")
            return False
    
    def unsubscribe(self, topic: str) -> bool:
        """
        Unsubscribe from an MQTT topic.
        
        Args:
            topic: MQTT topic to unsubscribe from
            
        Returns:
            True if unsubscription successful, False otherwise
        """
        if not self.connected:
            logger.error("Cannot unsubscribe: not connected to broker")
            return False
        
        try:
            result, mid = self.client.unsubscribe(topic)
            if result == mqtt.MQTT_ERR_SUCCESS:
                if topic in self.subscriptions:
                    del self.subscriptions[topic]
                logger.info(f"Unsubscribed from topic: {topic}")
                return True
            else:
                logger.error(f"Failed to unsubscribe from topic '{topic}': {result}")
                return False
        except Exception as e:
            logger.error(f"Error unsubscribing from topic '{topic}': {e}")
            return False
    
    def publish(
        self,
        topic: str,
        payload: Any,
        retain: bool = False,
        qos: int = None
    ) -> bool:
        """
        Publish a message to an MQTT topic.
        
        Args:
            topic: MQTT topic to publish to
            payload: Message payload (will be JSON-encoded if dict/list)
            retain: Retain message flag
            qos: Quality of Service (uses default if None)
            
        Returns:
            True if publish successful, False otherwise
        """
        if not self.connected:
            logger.error("Cannot publish: not connected to broker")
            return False
        
        # Convert payload to JSON if it's a dict or list
        if isinstance(payload, (dict, list)):
            payload = json.dumps(payload)
        
        try:
            qos_level = qos if qos is not None else self.qos
            result = self.client.publish(topic, payload, qos=qos_level, retain=retain)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Published to topic '{topic}': {payload}")
                return True
            else:
                logger.error(f"Failed to publish to topic '{topic}': {result.rc}")
                return False
        except Exception as e:
            logger.error(f"Error publishing to topic '{topic}': {e}")
            return False
    
    def is_connected(self) -> bool:
        """Check if client is connected to broker."""
        return self.connected


if __name__ == "__main__":
    # Test the MQTT client wrapper
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Get configuration from environment
    broker = os.getenv("MQTT_BROKER", "localhost")
    port = int(os.getenv("MQTT_PORT", "1883"))
    username = os.getenv("MQTT_USERNAME")
    password = os.getenv("MQTT_PASSWORD")
    
    # Create MQTT client
    mqtt_client = MQTTClientWrapper(
        broker_host=broker,
        broker_port=port,
        client_id="test_client",
        username=username,
        password=password
    )
    
    # Test callback
    def test_callback(topic, payload):
        print(f"Received: {topic} -> {payload}")
    
    # Connect and test
    if mqtt_client.connect():
        mqtt_client.subscribe("test/topic", test_callback)
        mqtt_client.publish("test/topic", {"message": "Hello MQTT!"})
        
        # Keep running for a bit
        time.sleep(5)
        
        mqtt_client.disconnect()
