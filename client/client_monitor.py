#!/usr/bin/env python3
"""
Client PC Monitor for Server Boot/Shutdown Management
Monitors PC state and sends MQTT signals to automation server
Includes system tray icon with status indicators
"""

import os
import sys
import time
import json
import socket
import signal
import logging
import re
import threading
from datetime import datetime
from pathlib import Path
from collections import deque

import paho.mqtt.client as mqtt
import yaml
from dotenv import load_dotenv
import pystray
from PIL import Image, ImageDraw
from pystray import MenuItem as item

# Configuration
SCRIPT_DIR = Path(__file__).parent
CONFIG_DIR = SCRIPT_DIR / "config"
CONFIG_FILE = CONFIG_DIR / "client_config.yaml"
ENV_FILE = CONFIG_DIR / ".env"
ROOT_ENV_FILE = SCRIPT_DIR.parent / "config" / ".env"

# Logging setup
LOG_DIR = SCRIPT_DIR / "logs"
LOG_FILE = LOG_DIR / "client_monitor.log"

def setup_logging():
    """Setup logging with handles for permission errors"""
    try:
        LOG_DIR.mkdir(exist_ok=True)
        # Test if writable
        test_file = LOG_DIR / ".test"
        test_file.touch()
        test_file.unlink()
        
        handler = logging.FileHandler(LOG_FILE)
    except (PermissionError, OSError):
        # Fallback to AppData if Program Files is read-only
        app_data = Path(os.getenv('LOCALAPPDATA', '.')) / "ClientMonitor"
        app_data.mkdir(exist_ok=True)
        fallback_log = app_data / "client_monitor.log"
        print(f"WARNING: No write access to {LOG_FILE}. Falling back to {fallback_log}")
        handler = logging.FileHandler(fallback_log)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            handler,
            logging.StreamHandler(sys.stdout)
        ]
    )

setup_logging()
logger = logging.getLogger(__name__)

# Import auto-updater after logging is set up
try:
    from auto_updater import AutoUpdater
    AUTO_UPDATE_AVAILABLE = True
except ImportError:
    logger.warning("Auto-updater module not available")
    AUTO_UPDATE_AVAILABLE = False


class SystemTrayIcon:
    """System tray icon manager with status indicators"""
    
    def __init__(self, monitor):
        """Initialize system tray icon"""
        self.monitor = monitor
        self.icon = None
        self.status = "disconnected"  # disconnected, connected, error
        self.server_status = "unknown"  # online, offline, unknown
        self.recent_requests = deque(maxlen=5)  # Last 5 requests
        
    def create_icon_image(self, color):
        """Create a colored icon image"""
        # Create a 64x64 image with a circle
        width = 64
        height = 64
        image = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(image)
        
        # Draw circle
        margin = 8
        draw.ellipse(
            [margin, margin, width - margin, height - margin],
            fill=color,
            outline='black',
            width=2
        )
        
        return image
    
    def get_icon_color(self):
        """Get icon color based on status"""
        if self.status == "error":
            return 'red'
        elif self.status == "disconnected":
            return 'gray'
        elif self.server_status in ["online", "up"]:
            return 'green'
        elif self.server_status in ["offline", "down"]:
            return 'orange'
        else:
            return 'yellow'  # connected but server status unknown
    
    def update_icon(self):
        """Update the tray icon"""
        if self.icon:
            color = self.get_icon_color()
            # Only recreate image if color changed or not yet set
            if not hasattr(self, '_last_color') or self._last_color != color:
                self.icon.icon = self.create_icon_image(color)
                self._last_color = color
            self.icon.title = self.get_tooltip()
    
    def get_tooltip(self):
        """Get tooltip text (constrained to 128 chars for Windows)"""
        # Header with shortened client ID if needed
        client_id = self.monitor.client_id
        if len(client_id) > 20:
            client_id = client_id[:17] + "..."
        
        lines = [f"CM: {client_id}"]
        
        # Connection status (shorter symbols)
        conn_text = "Broker: OK" if self.status == "connected" else ("Broker: OFF" if self.status == "disconnected" else "Broker: ERR")
        lines.append(conn_text)
        
        # Server status
        srv_text = f"Srv: {self.server_status.upper()}"
        lines.append(srv_text)
        
        # Countdown
        if hasattr(self.monitor, 'next_heartbeat') and self.monitor.next_heartbeat > 0:
            remaining = int(max(0, self.monitor.next_heartbeat - time.time()))
            lines.append(f"Next HB: {remaining}s")
        
        # Recent requests (only if space permits)
        if self.recent_requests:
            recent_lines = ["\nRec:"]
            # Show fewer recent items and shorter text
            for req in list(self.recent_requests)[-2:]:
                # Truncate request text if too long
                text = str(req)
                if len(text) > 25:
                    text = text[:22] + "..."
                recent_lines.append(f" {text}")
            
            # Check if adding these would exceed limit
            current_len = sum(len(l) + 1 for l in lines)
            recent_len = sum(len(l) + 1 for l in recent_lines)
            
            if current_len + recent_len < 120:
                lines.extend(recent_lines)
        
        tooltip = "\n".join(lines)
        # Final safety truncation
        if len(tooltip) >= 128:
            return tooltip[:124] + "..."
        return tooltip
    
    def add_request(self, request_type):
        """Add a request to recent list"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.recent_requests.append(f"{timestamp} - {request_type}")
        self.update_icon()
    
    def set_status(self, status):
        """Set connection status"""
        self.status = status
        self.update_icon()
    
    def set_server_status(self, server_status):
        """Set server status"""
        self.server_status = server_status
        self.update_icon()
    
    def on_quit(self, icon, item):
        """Handle quit action"""
        logger.info("Quit requested from system tray")
        icon.stop()
        self.monitor.stop()
    
    def on_show_log(self, icon, item):
        """Open log file"""
        try:
            os.startfile(str(LOG_FILE))
        except Exception as e:
            logger.error(f"Failed to open log file: {e}")
    
    def on_show_status(self, icon, item):
        """Show status window (placeholder)"""
        # Could implement a GUI window here in the future
        logger.info("Status requested from system tray")
    
    def on_check_updates(self, icon, item):
        """Check for updates manually"""
        try:
            if self.monitor.auto_updater:
                logger.info("Manual update check requested")
                # Force check regardless of interval
                self.monitor.auto_updater.last_check = None
                update_thread = threading.Thread(
                    target=self.monitor._check_updates_async,
                    daemon=True
                )
                update_thread.start()
                self.add_request("Checking updates...")
            else:
                logger.warning("Auto-updater not available")
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
    
    def create_menu(self):
        """Create system tray menu"""
        menu_items = [
            item('Status', self.on_show_status),
            item('View Log', self.on_show_log),
        ]
        
        # Add update check option if auto-updater is available
        if self.monitor.auto_updater:
            menu_items.append(item('Check for Updates', self.on_check_updates))
        
        menu_items.extend([
            pystray.Menu.SEPARATOR,
            item('Quit', self.on_quit)
        ])
        
        return pystray.Menu(*menu_items)
    
    def run(self):
        """Run the system tray icon"""
        color = self.get_icon_color()
        image = self.create_icon_image(color)
        
        self.icon = pystray.Icon(
            "ClientServerBootShutdownManagement",
            image,
            self.get_tooltip(),
            self.create_menu()
        )
        
        # Run in separate thread
        self.icon.run()


class ClientMonitor:
    """Monitor client PC state and communicate via MQTT"""
    
    def __init__(self, use_tray=True):
        """Initialize the client monitor"""
        self.config = self._load_config()
        self.client_id = self._get_client_id()
        self.mqtt_client = None
        self.running = False
        self.heartbeat_thread = None
        self.connected = False
        self.use_tray = use_tray
        self.tray_icon = None
        self.next_heartbeat = 0
        self.auto_updater = None
        
        if self.use_tray:
            self.tray_icon = SystemTrayIcon(self)
        
        # Apply debug log level if configured
        if self.config.get('client', {}).get('debug'):
            logging.getLogger().setLevel(logging.DEBUG)
            logger.debug("Debug logging enabled via configuration")
        
        # Initialize auto-updater if enabled
        if AUTO_UPDATE_AVAILABLE and self.config.get('client', {}).get('auto_update', {}).get('enabled', True):
            try:
                check_interval = self.config.get('client', {}).get('auto_update', {}).get('check_interval_hours', 24)
                self.auto_updater = AutoUpdater(check_interval_hours=check_interval)
                logger.info(f"Auto-updater initialized (check interval: {check_interval}h)")
            except Exception as e:
                logger.warning(f"Could not initialize auto-updater: {e}")
        
        logger.info(f"Client Monitor initialized for: {self.client_id}")
    
    def _load_config(self):
        """Load configuration from YAML and environment"""
        # Load environment variables from local config if it exists
        if ENV_FILE.exists():
            load_dotenv(ENV_FILE)
        # Also try root config .env for convenience if running from source
        if ROOT_ENV_FILE.exists():
            load_dotenv(ROOT_ENV_FILE)
        
        # Load YAML config
        if not CONFIG_FILE.exists():
            logger.error(f"Configuration file not found: {CONFIG_FILE}")
            raise FileNotFoundError(f"Configuration file not found: {CONFIG_FILE}")
        
        with open(CONFIG_FILE, 'r') as f:
            config = yaml.safe_load(f)
        
        # Resolve environment variables in config
        config = self._resolve_env_vars(config)
        
        # Tray icon override (still need some logic for this since it affects self)
        enable_tray = str(config.get('client', {}).get('enable_tray', 'true')).lower() == 'true'
        if not enable_tray:
            self.use_tray = False
        
        return config

    def _resolve_env_vars(self, obj):
        """Recursively resolve environment variables in a dictionary/list"""
        if isinstance(obj, dict):
            return {k: self._resolve_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._resolve_env_vars(v) for v in obj]
        elif isinstance(obj, str):
            # Match ${VAR_NAME} or ${VAR_NAME:default}
            pattern = r'\$\{([^:]+)(?::([^}]*))?\}'
            
            def replace(match):
                var_name = match.group(1)
                default_value = match.group(2) if match.group(2) is not None else ""
                return os.getenv(var_name, default_value)
            
            # Check if the whole string is just a placeholder (to maintain types)
            full_match = re.fullmatch(pattern, obj)
            if full_match:
                var_name = full_match.group(1)
                default_value = full_match.group(2) if full_match.group(2) is not None else ""
                val = os.getenv(var_name, default_value)
                
                # Conversion logic
                if val.lower() == 'true': return True
                if val.lower() == 'false': return False
                try:
                    if '.' in val: return float(val)
                    return int(val)
                except ValueError:
                    return val
            
            return re.sub(pattern, replace, obj)
        return obj
    
    def _get_client_id(self):
        """Get unique client identifier"""
        # Use custom name from config if available, otherwise use hostname
        custom_name = self.config.get('client', {}).get('custom_name', '')
        if custom_name:
            return custom_name
        
        hostname = socket.gethostname()
        return hostname.lower().replace(' ', '_')
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker"""
        if rc == 0:
            logger.info(f"Connected to MQTT broker at {self.config['mqtt']['broker']['host']}")
            self.connected = True
            
            # Update tray icon
            if self.tray_icon:
                self.tray_icon.set_status("connected")
            
            # Subscribe to server status topics
            self._subscribe_to_server_status()
            
            # Send startup presence message
            self._send_presence_message("online")
            
            if self.tray_icon:
                self.tray_icon.add_request("Startup")
        else:
            logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")
            self.connected = False
            if self.tray_icon:
                self.tray_icon.set_status("error")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from MQTT broker"""
        logger.warning(f"Disconnected from MQTT broker. Return code: {rc}")
        self.connected = False
        
        if self.tray_icon:
            self.tray_icon.set_status("disconnected")
        
        if self.running:
            logger.info("Attempting to reconnect...")
    
    def _on_message(self, client, userdata, msg):
        """Callback when message received"""
        try:
            payload = json.loads(msg.payload.decode())
            
            # Handle client shutdown command
            if '/command/shutdown' in msg.topic:
                action = payload.get('action', '')
                if action == 'shutdown':
                    shutdown_type = payload.get('type', 'graceful')
                    request_id = payload.get('request_id', 'unknown')
                    logger.warning(f"Shutdown command received: {shutdown_type} (request_id: {request_id})")
                    
                    if self.tray_icon:
                        self.tray_icon.add_request(f"Shutdown ({shutdown_type})")
                    
                    # Handle shutdown in a separate thread
                    shutdown_thread = threading.Thread(
                        target=self._handle_shutdown_command,
                        args=(shutdown_type, request_id),
                        daemon=False
                    )
                    shutdown_thread.start()
            
            # Handle server health messages
            elif '/health' in msg.topic:
                checks = payload.get('checks', [])
                # Derived logic: if any check is 'up', server is alive
                is_up = len(checks) > 0 and any(c.get('status') == 'up' for c in checks)
                server_state = 'up' if is_up else 'down'
                logger.info(f"Server health received. Derived state: {server_state}")
                
                if self.tray_icon:
                    self.tray_icon.set_server_status(server_state)
            
            # Legacy status check (optional, for backward compatibility during transition)
            elif '/status' in msg.topic:
                server_state = payload.get('server_state', 'unknown')
                logger.info(f"Server status received: {server_state}")
                
                if self.tray_icon:
                    self.tray_icon.set_server_status(server_state)
            
            # Handle server response messages
            elif '/response' in msg.topic:
                action = payload.get('action', 'unknown')
                success = payload.get('success', False)
                logger.info(f"Server response: {action} - {'success' if success else 'failed'}")
                
                if self.tray_icon:
                    status_text = f"{action.capitalize()} {'✓' if success else '✗'}"
                    self.tray_icon.add_request(status_text)
                    
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def _subscribe_to_server_status(self):
        """Subscribe to server status topics"""
        # Get target server from config (default to dell/t310)
        target_server = self.config.get('client', {}).get('target_server', 'dell/t310')
        
        # Subscribe to health and response topics
        health_topic = f"{target_server}/health"
        response_topic = f"{target_server}/response"
        
        self.mqtt_client.subscribe(health_topic, qos=1)
        self.mqtt_client.subscribe(response_topic, qos=1)
        
        logger.info(f"Subscribed to server topics: {health_topic}, {response_topic}")
        
        # Subscribe to client shutdown command topic
        shutdown_topic = self.config['mqtt']['topics']['shutdown'].replace(
            '{client_id}', 
            self.client_id
        )
        self.mqtt_client.subscribe(shutdown_topic, qos=1)
        logger.info(f"Subscribed to shutdown commands: {shutdown_topic}")
    
    def _on_publish(self, client, userdata, mid):
        """Callback when message is published"""
        logger.debug(f"Message published: {mid}")
    
    def _send_presence_message(self, status):
        """Send presence message (online/offline)"""
        topic = self.config['mqtt']['topics']['presence'].replace(
            '{client_id}', 
            self.client_id
        )
        
        message = {
            "status": status,
            "hostname": socket.gethostname(),
            "client_id": self.client_id,
            "timestamp": datetime.now().isoformat(),
            "ip_address": self._get_ip_address()
        }
        
        payload = json.dumps(message)
        
        if self.mqtt_client and self.connected:
            result = self.mqtt_client.publish(
                topic,
                payload,
                qos=self.config['mqtt']['qos'],
                retain=False
            )
            logger.info(f"Presence message sent: {status} (topic: {topic})")
            return result
        else:
            logger.warning(f"Cannot send presence message - not connected to broker")
            return None
    
    def _send_heartbeat(self):
        """Send heartbeat message"""
        topic = self.config['mqtt']['topics']['heartbeat'].replace(
            '{client_id}', 
            self.client_id
        )
        
        message = {
            "client_id": self.client_id,
            "hostname": socket.gethostname(),
            "timestamp": datetime.now().isoformat(),
            "uptime": self._get_uptime()
        }
        
        payload = json.dumps(message)
        
        if self.mqtt_client and self.connected:
            result = self.mqtt_client.publish(
                topic,
                payload,
                qos=self.config['mqtt']['qos'],
                retain=False
            )
            logger.debug(f"Heartbeat sent (topic: {topic})")
            return result
        else:
            logger.debug("Cannot send heartbeat - not connected to broker")
            return None
    
    def _get_ip_address(self):
        """Get local IP address"""
        try:
            # Create a socket to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception as e:
            logger.debug(f"Could not determine IP address: {e}")
            return "unknown"
    
    def _get_uptime(self):
        """Get system uptime in seconds (Windows)"""
        try:
            import ctypes
            lib = ctypes.windll.kernel32
            uptime_ms = lib.GetTickCount64()
            return int(uptime_ms / 1000)
        except Exception as e:
            logger.debug(f"Could not determine uptime: {e}")
            return 0
    
    def _send_shutdown_response(self, request_id, success, message):
        """Send shutdown response message"""
        topic = self.config['mqtt']['topics']['response'].replace(
            '{client_id}', 
            self.client_id
        )
        
        response = {
            "request_id": request_id,
            "action": "shutdown",
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "client_id": self.client_id,
            "hostname": socket.gethostname()
        }
        
        payload = json.dumps(response)
        
        if self.mqtt_client and self.connected:
            self.mqtt_client.publish(topic, payload, qos=1, retain=False)
            logger.info(f"Shutdown response sent: {message}")
    
    def _save_open_applications(self):
        """Attempt to save all open applications (Windows)"""
        try:
            import subprocess
            logger.info("Attempting to save all open applications...")
            
            # Send Ctrl+S to all windows (best effort)
            # This uses PowerShell to send save command to foreground windows
            ps_script = '''
            Add-Type -AssemblyName System.Windows.Forms
            $windows = Get-Process | Where-Object {$_.MainWindowTitle -ne ""}
            foreach ($window in $windows) {
                try {
                    $null = [Microsoft.VisualBasic.Interaction]::AppActivate($window.Id)
                    Start-Sleep -Milliseconds 100
                    [System.Windows.Forms.SendKeys]::SendWait("^s")
                    Start-Sleep -Milliseconds 50
                } catch {}
            }
            '''
            
            # Run PowerShell script
            result = subprocess.run(
                ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps_script],
                capture_output=True,
                timeout=10,
                text=True
            )
            
            logger.info("Save command sent to open applications")
            return True
            
        except subprocess.TimeoutExpired:
            logger.warning("Application save operation timed out")
            return False
        except Exception as e:
            logger.error(f"Error saving applications: {e}")
            return False
    
    def _execute_system_shutdown(self, shutdown_type):
        """Execute Windows system shutdown"""
        try:
            import subprocess
            
            if shutdown_type == 'force':
                # Force shutdown (immediate, no save)
                logger.warning("Executing FORCE shutdown...")
                subprocess.run(['shutdown', '/s', '/f', '/t', '5'], check=True)
            else:
                # Graceful shutdown (with save prompts)
                logger.info("Executing GRACEFUL shutdown...")
                subprocess.run(['shutdown', '/s', '/t', '30'], check=True)
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing shutdown: {e}")
            return False
    
    def _handle_shutdown_command(self, shutdown_type, request_id):
        """Handle shutdown command with graceful application save"""
        try:
            logger.info(f"Processing shutdown command: {shutdown_type}")
            
            # Send acknowledgment
            self._send_shutdown_response(
                request_id,
                True,
                f"Shutdown command acknowledged ({shutdown_type})"
            )
            
            # Wait a moment for message to be sent
            time.sleep(1)
            
            if shutdown_type == 'graceful':
                # Try to save all open applications
                logger.info("Saving open applications...")
                self._save_open_applications()
                
                # Give applications time to save
                time.sleep(3)
            
            # Send offline presence
            logger.info("Sending offline presence message...")
            self._send_presence_message("offline")
            time.sleep(1)
            
            # Final response before shutdown
            self._send_shutdown_response(
                request_id,
                True,
                f"Initiating {shutdown_type} shutdown now"
            )
            time.sleep(1)
            
            # Execute shutdown
            success = self._execute_system_shutdown(shutdown_type)
            
            if not success:
                self._send_shutdown_response(
                    request_id,
                    False,
                    "Failed to execute shutdown command"
                )
                logger.error("Shutdown command failed")
            
        except Exception as e:
            logger.error(f"Error handling shutdown command: {e}", exc_info=True)
            self._send_shutdown_response(
                request_id,
                False,
                f"Shutdown error: {str(e)}"
            )
    
    def _heartbeat_loop(self):
        """Background thread for sending heartbeats with countdown support"""
        interval = self.config.get('client', {}).get('heartbeat_interval', 60)
        logger.info(f"Heartbeat loop started (interval: {interval}s)")
        
        # Check for updates on first heartbeat
        update_checked = False
        
        while self.running:
            # Set next heartbeat time
            self.next_heartbeat = time.time() + interval
            
            # Check for updates periodically (only once per heartbeat cycle)
            if not update_checked and self.auto_updater and self.running:
                try:
                    if self.auto_updater.should_check_for_updates():
                        logger.info("Checking for updates...")
                        update_thread = threading.Thread(
                            target=self._check_updates_async,
                            daemon=True
                        )
                        update_thread.start()
                except Exception as e:
                    logger.error(f"Error checking for updates: {e}")
                update_checked = True
            
            # Use small sleeps to allow for responsive tooltip updates and shutdown
            while time.time() < self.next_heartbeat and self.running:
                # Update tray icon periodically (every second) to refresh countdown
                if self.tray_icon:
                    self.tray_icon.update_icon()
                time.sleep(1)
            
            if self.running and self.connected:
                self._send_heartbeat()
                if self.tray_icon:
                    self.tray_icon.add_request("Heartbeat")
            
            # Reset update check flag for next cycle
            update_checked = False
    
    def _check_updates_async(self):
        """Check for updates asynchronously"""
        try:
            result = self.auto_updater.check_and_install_updates(auto_install=True)
            
            if result.get('update_available'):
                logger.info(f"Update available: {result.get('latest_version')}")
                if self.tray_icon:
                    self.tray_icon.add_request(f"Update: {result.get('latest_version')}")
                
                if result.get('installed'):
                    logger.info("Update installed successfully. Application will restart.")
                elif result.get('error'):
                    logger.error(f"Update error: {result.get('error')}")
        except Exception as e:
            logger.error(f"Error in update check: {e}", exc_info=True)
    
    def _setup_mqtt(self):
        """Setup MQTT client"""
        client_name = f"client_monitor_{self.client_id}"
        self.mqtt_client = mqtt.Client(client_id=client_name)
        
        # Set callbacks
        self.mqtt_client.on_connect = self._on_connect
        self.mqtt_client.on_disconnect = self._on_disconnect
        self.mqtt_client.on_publish = self._on_publish
        self.mqtt_client.on_message = self._on_message
        
        # Set authentication if configured
        username = self.config['mqtt']['authentication'].get('username')
        password = self.config['mqtt']['authentication'].get('password')
        if username and password:
            self.mqtt_client.username_pw_set(username, password)
            logger.info(f"MQTT authentication configured for user: {username}")
        
        # Set last will (offline message when connection lost unexpectedly)
        will_topic = self.config['mqtt']['topics']['presence'].replace(
            '{client_id}', 
            self.client_id
        )
        will_message = json.dumps({
            "status": "offline",
            "hostname": socket.gethostname(),
            "client_id": self.client_id,
            "timestamp": datetime.now().isoformat(),
            "reason": "connection_lost"
        })
        self.mqtt_client.will_set(will_topic, will_message, qos=1, retain=False)
        
        logger.info("MQTT client configured")
    
    def _connect_mqtt(self):
        """Connect to MQTT broker with retry logic"""
        broker_host = self.config['mqtt']['broker']['host']
        broker_port = self.config['mqtt']['broker']['port']
        keepalive = self.config['mqtt']['broker'].get('keepalive', 60)
        
        max_retries = 5
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Connecting to MQTT broker at {broker_host}:{broker_port} (attempt {attempt + 1}/{max_retries})")
                self.mqtt_client.connect(broker_host, broker_port, keepalive)
                self.mqtt_client.loop_start()
                
                # Wait for connection
                timeout = 10
                start_time = time.time()
                while not self.connected and (time.time() - start_time) < timeout:
                    time.sleep(0.1)
                
                if self.connected:
                    logger.info("Successfully connected to MQTT broker")
                    return True
                else:
                    logger.warning("Connection timeout")
                    
            except Exception as e:
                logger.error(f"Connection attempt failed: {e}")
            
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
        
        logger.error("Failed to connect to MQTT broker after all retries")
        if self.tray_icon:
            self.tray_icon.set_status("error")
        return False
    
    def start(self):
        """Start the client monitor"""
        logger.info("Starting Client Monitor...")
        self.running = True
        
        # Setup and connect MQTT
        self._setup_mqtt()
        if not self._connect_mqtt():
            logger.error("Failed to start - could not connect to MQTT broker")
            return False
        
        # Start heartbeat thread
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
        
        # Start system tray icon in separate thread
        if self.tray_icon:
            tray_thread = threading.Thread(target=self.tray_icon.run, daemon=False)
            tray_thread.start()
        
        logger.info("Client Monitor started successfully")
        return True
    
    def stop(self):
        """Stop the client monitor"""
        logger.info("Stopping Client Monitor...")
        self.running = False
        
        # Send offline presence message
        self._send_presence_message("offline")
        
        if self.tray_icon:
            self.tray_icon.add_request("Shutdown")
        
        # Wait a moment for message to be sent
        time.sleep(1)
        
        # Stop MQTT client
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
        
        # Stop tray icon
        if self.tray_icon and self.tray_icon.icon:
            self.tray_icon.icon.stop()
        
        logger.info("Client Monitor stopped")
    
    def run(self):
        """Run the client monitor (blocking)"""
        if not self.start():
            return
        
        try:
            # Keep running until interrupted
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            self.stop()


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}")
    if hasattr(signal_handler, 'monitor'):
        signal_handler.monitor.stop()
    sys.exit(0)


def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("Client PC Monitor Starting")
    logger.info("=" * 60)
    
    try:
        # Check if running with --no-tray argument
        use_tray = '--no-tray' not in sys.argv
        
        monitor = ClientMonitor(use_tray=use_tray)
        
        # Register signal handlers for graceful shutdown
        signal_handler.monitor = monitor
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Run monitor
        monitor.run()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
