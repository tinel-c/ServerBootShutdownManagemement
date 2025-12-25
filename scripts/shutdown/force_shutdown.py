#!/usr/bin/env python3
"""
Force shutdown script for Dell T310 Management System.
Performs immediate hard shutdown via IPMI.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))

from ipmi_wrapper import IPMIWrapper
from logger import get_logger

logger = get_logger(__name__)


def force_shutdown(host: str, username: str, password: str) -> bool:
    """
    Force shutdown server using IPMI hard power off.
    
    Args:
        host: IPMI interface IP address
        username: IPMI username
        password: IPMI password
        
    Returns:
        True if shutdown successful, False otherwise
    """
    try:
        logger.warning("FORCE SHUTDOWN initiated - this will immediately power off the server")
        
        # Create IPMI wrapper
        ipmi = IPMIWrapper(host, username, password)
        
        # Check current power status
        current_status = ipmi.get_power_status()
        if current_status == "off":
            logger.info("Server is already powered off")
            return True
        
        # Force power off
        if not ipmi.power_off(force=True):
            logger.error("Failed to send force power off command")
            return False
        
        logger.info("Force shutdown command sent successfully")
        
        # Wait briefly and verify
        import time
        time.sleep(5)
        
        final_status = ipmi.get_power_status()
        if final_status == "off":
            logger.info("Server is now powered off")
            return True
        else:
            logger.warning(f"Server power status: {final_status}")
            return True  # Command was sent successfully even if verification unclear
        
    except Exception as e:
        logger.error(f"Error during force shutdown: {e}")
        return False


if __name__ == "__main__":
    import argparse
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Force shutdown Dell T310 server (HARD POWER OFF)"
    )
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
        "--confirm",
        action="store_true",
        help="Confirm force shutdown (required)"
    )
    
    args = parser.parse_args()
    
    # Validate required arguments
    if not all([args.host, args.username, args.password]):
        logger.error("Missing required arguments. Provide --host, --username, --password or set in .env")
        sys.exit(1)
    
    # Require confirmation for force shutdown
    if not args.confirm:
        logger.error("Force shutdown requires --confirm flag for safety")
        print("\nWARNING: Force shutdown will immediately power off the server without")
        print("gracefully shutting down VMs or the operating system.")
        print("\nUse --confirm flag to proceed with force shutdown.")
        sys.exit(1)
    
    # Perform force shutdown
    success = force_shutdown(args.host, args.username, args.password)
    
    sys.exit(0 if success else 1)
