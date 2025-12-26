import logging
import json
from datetime import datetime
import threading

class MQTTHandler(logging.Handler):
    """
    Custom logging handler that publishes log records to MQTT.
    Uses the raw paho-mqtt client to avoid recursion loops with MQTTClientWrapper.
    """
    
    def __init__(self, mqtt_client, service_name: str, topic: str = "system/logs"):
        """
        Initialize MQTT Handler.
        
        Args:
            mqtt_client: The underlying paho-mqtt client object (not the wrapper)
            service_name: Name of the service generating logs (e.g., "boot-listener")
            topic: MQTT topic to publish logs to
        """
        super().__init__()
        self.mqtt_client = mqtt_client
        self.service_name = service_name
        self.topic = topic
        # Recursion guard in case internal paho logging triggers us
        self._recursion_guard = threading.local()

    def emit(self, record):
        """
        Emit a record.
        """
        # Prevent infinite recursion
        if getattr(self._recursion_guard, 'publishing', False):
            return

        try:
            self._recursion_guard.publishing = True
            
            # Format message
            msg = self.format(record)
            
            # Create JSON payload
            payload = {
                "timestamp": datetime.now().isoformat(),
                "level": record.levelname,
                "service": self.service_name,
                "message": msg,
                "module": record.module,
                "action": "LOG" # For compatibility with dashboard
            }
            
            # Publish using the raw client
            # qos=0 to be fire-and-forget and minimize overhead
            if self.mqtt_client.is_connected():
                self.mqtt_client.publish(
                    self.topic, 
                    json.dumps(payload), 
                    qos=0, 
                    retain=False
                )
                
        except Exception:
            self.handleError(record)
        finally:
            self._recursion_guard.publishing = False
