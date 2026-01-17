#!/usr/bin/env python3
"""
IPMI wrapper for Dell T310 Management System.
Provides a Python interface to ipmitool commands.
"""

import subprocess
import time
from typing import Dict, Optional, Tuple
from logger import get_logger

logger = get_logger(__name__)


class IPMIError(Exception):
    """Custom exception for IPMI-related errors."""
    pass


class IPMIWrapper:
    """Wrapper class for IPMI operations using ipmitool."""
    
    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        interface: str = "lanplus"
    ):
        """
        Initialize IPMI wrapper.
        
        Args:
            host: IPMI interface IP address or hostname
            username: IPMI username
            password: IPMI password
            interface: IPMI interface type (default: lanplus)
        """
        self.host = host
        self.username = username
        self.password = password
        self.interface = interface
        
        logger.info(f"IPMI wrapper initialized for host: {host}")
    
    def _execute_command(self, command: list, timeout: int = 30) -> Tuple[bool, str, str]:
        """
        Execute an ipmitool command.
        
        Args:
            command: List of command arguments
            timeout: Command timeout in seconds
            
        Returns:
            Tuple of (success, stdout, stderr)
        """
        # Build full command
        full_command = [
            "ipmitool",
            "-I", self.interface,
            "-H", self.host,
            "-U", self.username,
            "-P", self.password
        ] + command
        
        # Mask password in log
        log_command = full_command.copy()
        if "-P" in log_command:
            pwd_index = log_command.index("-P") + 1
            log_command[pwd_index] = "***"
        
        logger.debug(f"Executing IPMI command: {' '.join(log_command)}")
        
        try:
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            success = result.returncode == 0
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
            
            if success:
                logger.debug(f"IPMI command successful: {stdout}")
            else:
                logger.error(f"IPMI command failed: {stderr}")
            
            return success, stdout, stderr
            
        except subprocess.TimeoutExpired:
            logger.error(f"IPMI command timed out after {timeout} seconds")
            return False, "", f"Command timed out after {timeout} seconds"
        except FileNotFoundError:
            logger.error("ipmitool not found. Please install ipmitool.")
            return False, "", "ipmitool not found"
        except Exception as e:
            logger.error(f"Error executing IPMI command: {e}")
            return False, "", str(e)
    
    def get_power_status(self, retries: int = 2, retry_delay: float = 1.0) -> Optional[str]:
        """
        Get current power status of the server with automatic retry on failure.
        
        Args:
            retries: Number of retry attempts on failure (default: 2)
            retry_delay: Delay between retries in seconds (default: 1.0)
        
        Returns:
            Power status string ("on" or "off") or None on error
        """
        logger.info("Getting power status")
        
        for attempt in range(retries + 1):
            if attempt > 0:
                logger.warning(f"Retrying IPMI command (attempt {attempt + 1}/{retries + 1}) after {retry_delay}s delay...")
                time.sleep(retry_delay)
            
            success, stdout, stderr = self._execute_command(["chassis", "power", "status"])
            
            if success:
                # Parse output: "Chassis Power is on" or "Chassis Power is off"
                if "on" in stdout.lower():
                    logger.info("Server is powered ON")
                    return "on"
                elif "off" in stdout.lower():
                    logger.info("Server is powered OFF")
                    return "off"
            else:
                # Log the failure but continue to retry if attempts remain
                if attempt < retries:
                    logger.warning(f"IPMI command failed (attempt {attempt + 1}/{retries + 1}): {stderr}")
                else:
                    logger.error(f"IPMI command failed after {retries + 1} attempts: {stderr}")
        
        # All retries exhausted
        return None
    
    def power_on(self) -> bool:
        """
        Power on the server.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Powering ON server")
        success, stdout, stderr = self._execute_command(["chassis", "power", "on"])
        
        if success:
            logger.info("Server power ON command sent successfully")
            return True
        else:
            logger.error(f"Failed to power on server: {stderr}")
            return False
    
    def power_off(self, force: bool = False) -> bool:
        """
        Power off the server.
        
        Args:
            force: If True, perform hard power off. If False, soft power off.
            
        Returns:
            True if successful, False otherwise
        """
        command_type = "off" if force else "soft"
        logger.info(f"Powering OFF server ({'force' if force else 'graceful'})")
        
        success, stdout, stderr = self._execute_command(["chassis", "power", command_type])
        
        if success:
            logger.info(f"Server power OFF command sent successfully ({command_type})")
            return True
        else:
            logger.error(f"Failed to power off server: {stderr}")
            return False
    
    def power_cycle(self) -> bool:
        """
        Power cycle the server (hard reset).
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Power cycling server")
        success, stdout, stderr = self._execute_command(["chassis", "power", "cycle"])
        
        if success:
            logger.info("Server power cycle command sent successfully")
            return True
        else:
            logger.error(f"Failed to power cycle server: {stderr}")
            return False
    
    def power_reset(self) -> bool:
        """
        Reset the server (warm reset).
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Resetting server")
        success, stdout, stderr = self._execute_command(["chassis", "power", "reset"])
        
        if success:
            logger.info("Server reset command sent successfully")
            return True
        else:
            logger.error(f"Failed to reset server: {stderr}")
            return False
    
    def get_chassis_status(self) -> Optional[Dict[str, str]]:
        """
        Get detailed chassis status.
        
        Returns:
            Dictionary with chassis status information or None on error
        """
        logger.info("Getting chassis status")
        success, stdout, stderr = self._execute_command(["chassis", "status"])
        
        if success:
            # Parse the output into a dictionary
            status = {}
            for line in stdout.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    status[key.strip()] = value.strip()
            
            logger.debug(f"Chassis status: {status}")
            return status
        
        logger.error(f"Failed to get chassis status: {stderr}")
        return None
    
    def get_sensor_data(self) -> Optional[str]:
        """
        Get sensor data (temperature, voltage, fans, etc.).
        
        Returns:
            Sensor data string or None on error
        """
        logger.info("Getting sensor data")
        success, stdout, stderr = self._execute_command(["sensor"])
        
        if success:
            logger.debug("Sensor data retrieved successfully")
            return stdout
        
        logger.error(f"Failed to get sensor data: {stderr}")
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
    # Test the IPMI wrapper
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Get credentials from environment
    ipmi_host = os.getenv("IPMI_HOST", "192.168.1.100")
    ipmi_user = os.getenv("IPMI_USERNAME", "admin")
    ipmi_pass = os.getenv("IPMI_PASSWORD", "password")
    
    # Create IPMI wrapper instance
    ipmi = IPMIWrapper(ipmi_host, ipmi_user, ipmi_pass)
    
    # Test commands
    print("Testing IPMI wrapper...")
    print(f"Power Status: {ipmi.get_power_status()}")
    print(f"Chassis Status: {ipmi.get_chassis_status()}")
