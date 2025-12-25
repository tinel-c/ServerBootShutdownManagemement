#!/usr/bin/env python3
"""
Wake-on-LAN boot script for Dell T310 Management System.
Sends WoL magic packet to boot the server.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))

from wakeonlan import send_magic_packet
from logger import get_logger

logger = get_logger(__name__)


def boot_via_wol(mac_address: str, broadcast_ip: str = "255.255.255.255") -> bool:
    """
    Boot server using Wake-on-LAN.
    
    Args:
        mac_address: MAC address of the server's network interface
        broadcast_ip: Broadcast IP address (default: 255.255.255.255)
        
    Returns:
        True if WoL packet sent successfully, False otherwise
    """
    try:
        logger.info(f"Sending Wake-on-LAN magic packet to {mac_address}")
        send_magic_packet(mac_address, ip_address=broadcast_ip)
        logger.info("Wake-on-LAN magic packet sent successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to send Wake-on-LAN packet: {e}")
        return False


if __name__ == "__main__":
    import argparse
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Boot Dell T310 server via Wake-on-LAN")
    parser.add_argument(
        "--mac",
        default=os.getenv("SERVER_MAC_ADDRESS"),
        help="MAC address of the server"
    )
    parser.add_argument(
        "--broadcast",
        default="255.255.255.255",
        help="Broadcast IP address"
    )
    
    args = parser.parse_args()
    
    if not args.mac:
        logger.error("MAC address not provided. Use --mac or set SERVER_MAC_ADDRESS in .env")
        sys.exit(1)
    
    # Send WoL packet
    success = boot_via_wol(args.mac, args.broadcast)
    sys.exit(0 if success else 1)
