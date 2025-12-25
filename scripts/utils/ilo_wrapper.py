#!/usr/bin/env python3
"""
iLO wrapper for HP DL360p Management System.
Provides a Python interface to HP iLO commands.
"""

import time
from typing import Dict, Optional, Tuple
from logger import get_logger

logger = get_logger(__name__)


class ILOError(Exception):
    """Custom exception for iLO-related errors."""
    pass


class ILOWrapper:
    """Wrapper class for iLO operations using python-hpilo."""
    
    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        verify_ssl: bool = False
    ):
        """
        Initialize iLO wrapper.
        
        Args:
            host: iLO interface IP address or hostname
            username: iLO username
            password: iLO password
            verify_ssl: Verify SSL certificates (default: False)
        """
        self.host = host
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self._ilo = None
        
        logger.info(f"iLO wrapper initialized for host: {host}")
    
    def _get_ilo_connection(self):
        """
        Get or create iLO connection.
        
        Returns:
            iLO connection object
        """
        if self._ilo is None:
            try:
                import hpilo
                self._ilo = hpilo.Ilo(
                    self.host,
                    self.username,
                    self.password,
                    timeout=30,
                    protocol=hpilo.ILO_HTTP if not self.verify_ssl else hpilo.ILO_RAW
                )
                logger.debug(f"iLO connection established to {self.host}")
            except ImportError:
                logger.error("python-hpilo library not found. Please install: pip install python-hpilo")
                raise ILOError("python-hpilo library not installed")
            except Exception as e:
                logger.error(f"Failed to connect to iLO: {e}")
                raise ILOError(f"Failed to connect to iLO: {e}")
        
        return self._ilo
    
    def _execute_command(self, command_name: str, *args, **kwargs):
        """
        Execute an iLO command.
        
        Args:
            command_name: Name of the iLO command method
            *args: Positional arguments for the command
            **kwargs: Keyword arguments for the command
            
        Returns:
            Command result
        """
        try:
            ilo = self._get_ilo_connection()
            command = getattr(ilo, command_name)
            
            logger.debug(f"Executing iLO command: {command_name}")
            result = command(*args, **kwargs)
            logger.debug(f"iLO command successful: {command_name}")
            
            return result
            
        except AttributeError:
            logger.error(f"iLO command not found: {command_name}")
            raise ILOError(f"Invalid iLO command: {command_name}")
        except Exception as e:
            logger.error(f"iLO command failed ({command_name}): {e}")
            raise ILOError(f"iLO command failed: {e}")
    
    def get_power_status(self) -> Optional[str]:
        """
        Get current power status of the server.
        
        Returns:
            Power status string ("on" or "off") or None on error
        """
        logger.info("Getting power status")
        try:
            status = self._execute_command('get_host_power_status')
            
            # iLO returns "ON" or "OFF"
            if status and isinstance(status, str):
                power_state = status.lower()
                logger.info(f"Server is powered {power_state.upper()}")
                return power_state
            
            logger.error(f"Unexpected power status format: {status}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get power status: {e}")
            return None
    
    def power_on(self) -> bool:
        """
        Power on the server.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Powering ON server")
        try:
            # Check if already on
            current_status = self.get_power_status()
            if current_status == "on":
                logger.info("Server is already powered on")
                return True
            
            self._execute_command('press_pwr_btn')
            logger.info("Server power ON command sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to power on server: {e}")
            return False
    
    def power_off(self, force: bool = False) -> bool:
        """
        Power off the server.
        
        Args:
            force: If True, perform hard power off (hold power button).
                  If False, graceful shutdown (press power button).
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Powering OFF server ({'force' if force else 'graceful'})")
        try:
            if force:
                # Hold power button for 5 seconds (hard shutdown)
                self._execute_command('hold_pwr_btn')
            else:
                # Press power button (graceful shutdown)
                self._execute_command('press_pwr_btn')
            
            logger.info(f"Server power OFF command sent successfully ({'force' if force else 'graceful'})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to power off server: {e}")
            return False
    
    def power_reset(self) -> bool:
        """
        Reset the server (warm reset).
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Resetting server")
        try:
            self._execute_command('reset_server')
            logger.info("Server reset command sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset server: {e}")
            return False
    
    def cold_boot(self) -> bool:
        """
        Perform a cold boot (power cycle).
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Cold booting server")
        try:
            self._execute_command('cold_boot_server')
            logger.info("Server cold boot command sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cold boot server: {e}")
            return False
    
    def get_server_status(self) -> Optional[Dict[str, any]]:
        """
        Get detailed server status.
        
        Returns:
            Dictionary with server status information or None on error
        """
        logger.info("Getting server status")
        try:
            # Get embedded health data
            health = self._execute_command('get_embedded_health')
            
            # Get host power status
            power_status = self.get_power_status()
            
            status = {
                'power_status': power_status,
                'health_data': health
            }
            
            logger.debug(f"Server status retrieved")
            return status
            
        except Exception as e:
            logger.error(f"Failed to get server status: {e}")
            return None
    
    def get_health_status(self) -> Optional[Dict[str, any]]:
        """
        Get server health information.
        
        Returns:
            Dictionary with health information or None on error
        """
        logger.info("Getting health status")
        try:
            health = self._execute_command('get_embedded_health')
            logger.debug("Health status retrieved successfully")
            return health
            
        except Exception as e:
            logger.error(f"Failed to get health status: {e}")
            return None
    
    def get_host_data(self) -> Optional[Dict[str, any]]:
        """
        Get host data including model, serial number, etc.
        
        Returns:
            Dictionary with host data or None on error
        """
        logger.info("Getting host data")
        try:
            host_data = self._execute_command('get_host_data')
            logger.debug("Host data retrieved successfully")
            return host_data
            
        except Exception as e:
            logger.error(f"Failed to get host data: {e}")
            return None
    
    def wait_for_power_state(
        self,
        desired_state: str,
        timeout: int = 120,
        poll_interval: int = 5
    ) -> bool:
        """
        Wait for server to reach desired power state.
        
        Args:
            desired_state: Desired power state ("on" or "off")
            timeout: Maximum time to wait in seconds
            poll_interval: Time between status checks in seconds
            
        Returns:
            True if desired state reached, False if timeout
        """
        logger.info(f"Waiting for power state: {desired_state} (timeout: {timeout}s)")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            current_state = self.get_power_status()
            
            if current_state == desired_state:
                logger.info(f"Server reached desired power state: {desired_state}")
                return True
            
            logger.debug(f"Current state: {current_state}, waiting...")
            time.sleep(poll_interval)
        
        logger.warning(f"Timeout waiting for power state: {desired_state}")
        return False


if __name__ == "__main__":
    # Test the iLO wrapper
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Get credentials from environment
    ilo_host = os.getenv("DL360P_ILO_HOST", "192.168.1.101")
    ilo_user = os.getenv("DL360P_ILO_USERNAME", "Administrator")
    ilo_pass = os.getenv("DL360P_ILO_PASSWORD", "password")
    
    # Create iLO wrapper instance
    ilo = ILOWrapper(ilo_host, ilo_user, ilo_pass)
    
    # Test commands
    print("Testing iLO wrapper...")
    print(f"Power Status: {ilo.get_power_status()}")
    print(f"Host Data: {ilo.get_host_data()}")
