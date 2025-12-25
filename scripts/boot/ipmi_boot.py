#!/usr/bin/env python3
"""
IPMI boot script for Dell T310 Management System.
Powers on the server using IPMI commands.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))

from ipmi_wrapper import IPMIWrapper
from logger import get_logger

logger = get_logger(__name__)


def boot_via_ipmi(
    host: str,
    username: str,
    password: str,
    wait_for_boot: bool = True,
    timeout: int = 120
) -> bool:
    """
    Boot server using IPMI.
    
    Args:
        host: IPMI interface IP address
        username: IPMI username
        password: IPMI password
        wait_for_boot: Wait for server to power on
        timeout: Maximum time to wait for boot (seconds)
        
    Returns:
        True if boot successful, False otherwise
    """
    try:
        logger.info(f"Booting server via IPMI: {host}")
        
        # Create IPMI wrapper
        ipmi = IPMIWrapper(host, username, password)
        
        # Check current power status
        current_status = ipmi.get_power_status()
        if current_status == "on":
            logger.info("Server is already powered on")
            return True
        
        # Power on the server
        if not ipmi.power_on():
            logger.error("Failed to send power on command")
            return False
        
        # Wait for server to boot if requested
        if wait_for_boot:
            logger.info(f"Waiting for server to boot (timeout: {timeout}s)...")
            if ipmi.wait_for_power_state("on", timeout=timeout):
                logger.info("Server booted successfully")
                return True
            else:
                logger.warning("Server boot verification timed out")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error booting server via IPMI: {e}")
        return False


if __name__ == "__main__":
    import argparse
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Boot Dell T310 server via IPMI")
    parser.add_argument(
        "--host",
        default=os.getenv("IPMI_HOST"),
        help="IPMI interface IP address"
    )
    parser.add_argument(
        "--username",
        default=os.getenv("IPMI_USERNAME"),
        help="IPMI username"
    )
    parser.add_argument(
        "--password",
        default=os.getenv("IPMI_PASSWORD"),
        help="IPMI password"
    )
    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="Don't wait for boot completion"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Boot timeout in seconds"
    )
    
    args = parser.parse_args()
    
    # Validate required arguments
    if not all([args.host, args.username, args.password]):
        logger.error("Missing required arguments. Provide --host, --username, --password or set in .env")
        sys.exit(1)
    
    # Boot server
    success = boot_via_ipmi(
        args.host,
        args.username,
        args.password,
        wait_for_boot=not args.no_wait,
        timeout=args.timeout
    )
    
    sys.exit(0 if success else 1)
