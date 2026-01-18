#!/usr/bin/env python3
"""
HealthChecks.io Monitor for Dell & HP Server Management System.
Polls HealthChecks.io API v3 every 1 minute and publishes status to MQTT.
Displays a live dashboard in the console using the 'rich' library.
"""

import sys
import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime
import signal
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Add utils directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))

from mqtt_client import MQTTClientWrapper
from logger import get_logger
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich import box

logger = get_logger(__name__)
console = Console()

def load_config() -> Dict[str, Any]:
    """Load configuration from files."""
    import yaml
    
    # Calculate config directory
    config_dir = Path(__file__).parent.parent.parent / "config"
    env_path = config_dir / ".env"
    
    # Load environment variables
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
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
            return val if val is not None else obj
        return obj
    
    config = replace_env_vars(config)
    return config

class HealthMonitor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = os.getenv("HEALTHCHECKS_API_KEY")
        self.servers = config.get("servers", [])
        
        # Initialize MQTT client
        mqtt_config = config.get('mqtt', {})
        self.mqtt_client = MQTTClientWrapper(
            broker_host=mqtt_config.get('broker', {}).get('host'),
            broker_port=mqtt_config.get('broker', {}).get('port', 1883),
            client_id="health_monitor",
            username=mqtt_config.get('authentication', {}).get('username'),
            password=mqtt_config.get('authentication', {}).get('password'),
            keepalive=mqtt_config.get('broker', {}).get('keepalive', 60),
            qos=mqtt_config.get('qos', 1)
        )
        
        self.base_url = "https://healthchecks.io/api/v3/checks/"
        self.headers = {"X-Api-Key": self.api_key} if self.api_key else {}
        self.running = False

    def stop(self):
        """Stop the monitor gracefully."""
        logger.info("Stopping Health Monitor...")
        self.running = False
        if self.mqtt_client:
            self.mqtt_client.disconnect()

    def fetch_checks(self) -> List[Dict[str, Any]]:
        """Fetch all checks from HealthChecks.io."""
        if not self.api_key or self.api_key == "your_read_only_api_key_here":
            return []
        
        try:
            response = requests.get(self.base_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json().get("checks", [])
        except Exception as e:
            logger.error(f"Failed to fetch health checks: {e}")
            return []

    def generate_table(self, checks: List[Dict[str, Any]]) -> Table:
        """Generate a Rich Table for display."""
        table = Table(title="HealthChecks.io Status", box=box.ROUNDED, show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Last Ping", justify="right")
        table.add_column("Last Flip", justify="right")
        table.add_column("Tags", style="dim")

        for check in checks:
            status = check.get("status", "unknown")
            color = "green" if status == "up" else "red" if status == "down" else "yellow"
            
            last_ping = check.get("last_ping") or "Never"
            if last_ping != "Never":
                try:
                    dt = datetime.fromisoformat(last_ping.replace("Z", "+00:00"))
                    last_ping = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    pass
            
            last_flip = check.get("flip_time") or "Never"
            
            table.add_row(
                check.get("name", "Unnamed"),
                f"[{color}]{status.upper()}[/{color}]",
                last_ping,
                last_flip,
                check.get("tags", "")
            )
        
        return table

    def publish_to_mqtt(self, checks: List[Dict[str, Any]]):
        """Publish check statuses to MQTT topics based on server mapping."""
        for server in self.servers:
            hc_names = server.get("healthcheck_names", [])
            if not hc_names:
                continue
            
            # Handle if names are a comma-separated string from environment variables
            if isinstance(hc_names, str):
                hc_names = [name.strip() for name in hc_names.split(",")]
            
            # Find checks matching these names
            matching_checks = [c for c in checks if c.get("name") in hc_names]
            if not matching_checks:
                continue
            
            mqtt_prefix = server.get("mqtt_prefix", f"server/{server.get('name')}")
            topic = f"{mqtt_prefix}/health"
            
            payload = {
                "timestamp": datetime.now().isoformat(),
                "server": server.get("name"),
                "checks": matching_checks
            }
            
            self.mqtt_client.publish(topic, payload)

    def run(self):
        """Main loop."""
        if not self.api_key or self.api_key == "your_read_only_api_key_here":
            console.print("[bold red]Error: HEALTHCHECKS_API_KEY not set or invalid in .env[/bold red]")
            return

        logger.info("Starting Health Monitor...")
        if not self.mqtt_client.connect():
            logger.error("Failed to connect to MQTT broker")
        
        self.running = True
        with Live(self.generate_table([]), refresh_per_second=1, console=console) as live:
            while self.running:
                checks = self.fetch_checks()
                live.update(self.generate_table(checks))
                
                if checks:
                    self.publish_to_mqtt(checks)
                
                # Wait 1 minute in small increments to respond to stop signal faster
                for _ in range(60):
                    if not self.running:
                        break
                    time.sleep(1)

if __name__ == "__main__":
    try:
        config = load_config()
        monitor = HealthMonitor(config)
        
        # Signal handling
        def handle_signal(sig, frame):
            monitor.stop()
            
        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)
        
        monitor.run()
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)
