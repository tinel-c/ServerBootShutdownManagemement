#!/usr/bin/env python3
"""
Ensure Proxmox and VMs are up after boot.
Waits for Proxmox API availability and enforces running state for VMs/HA resources.
"""

import sys
import time
import logging
from pathlib import Path
from typing import Optional, List

# Add parent directory to path for imports to find utils if needed
# (Assuming this script is in scripts/boot/)
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))

from logger import get_logger

logger = get_logger(__name__)

def ensure_proxmox_up(
    proxmox_host: str,
    username: str,
    password: str,
    timeout: int = 600,
    verify_ssl: bool = False
) -> bool:
    """
    Wait for Proxmox API to be available and ensure VMs are started.
    
    Args:
        proxmox_host: Proxmox host IP or hostname
        username: Proxmox username
        password: Proxmox password
        timeout: Max wait time in seconds (default 10 mins)
        verify_ssl: Verify SSL certificate
        
    Returns:
        True if Proxmox is up and recovery commands sent, False if timeout.
    """
    try:
        from proxmoxer import ProxmoxAPI
    except ImportError:
        logger.error("proxmoxer library not installed. Install with: pip install proxmoxer")
        return False

    logger.info(f"Waiting for Proxmox API ({proxmox_host}) to become available (Timeout: {timeout}s)...")
    
    start_time = time.time()
    proxmox = None
    
    # 1. Wait for API availability
    while time.time() - start_time < timeout:
        try:
            proxmox = ProxmoxAPI(
                proxmox_host,
                user=username,
                password=password,
                verify_ssl=verify_ssl,
                timeout=5 # Short connection timeout for polling
            )
            # Try a lightweight call to verify auth and connectivity
            proxmox.version.get()
            logger.info("Proxmox API is UP! Proceeding with VM recovery...")
            break
        except Exception as e:
            logger.debug(f"Connection attempt failed: {e}")
            time.sleep(10)
    else:
        logger.error("Timeout waiting for Proxmox API to become available")
        return False

    try:
        # 2. Fix HA Resources State
        logger.info("Checking HA resources...")
        try:
            ha_resources = proxmox.cluster.ha.resources.get()
            for resource in ha_resources:
                sid = resource.get('sid')
                state = resource.get('state')
                
                # If HA is managed, we want it 'started', not 'stopped' or 'frozen'
                if state != 'started':
                    logger.info(f"Setting HA resource {sid} state to 'started' (current: {state})")
                    try:
                        proxmox.cluster.ha.resources(sid).put(state='started')
                    except Exception as e:
                        logger.error(f"Failed to set HA state for {sid}: {e}")
        except Exception as e:
            # Maybe not a cluster, or HA not configured
            logger.warning(f"Failed to check HA resources (ignoring if standalone): {e}")

        # 3. Start All VMs
        logger.info("Checking all VMs state...")
        nodes = proxmox.nodes.get()
        
        for node in nodes:
            node_name = node['node']
            if node.get('status') != 'online':
                logger.warning(f"Node {node_name} is offline, skipping VM checks for this node.")
                continue
                
            vms = proxmox.nodes(node_name).qemu.get()
            
            for vm in vms:
                vm_id = vm['vmid']
                vm_name = vm.get('name', f'VM-{vm_id}')
                status = vm.get('status')
                template = vm.get('template', 0)
                
                # Skip templates
                if template == 1:
                    continue
                
                if status == 'stopped':
                    logger.info(f"Starting VM: {vm_name} (ID: {vm_id})")
                    try:
                        proxmox.nodes(node_name).qemu(vm_id).status.start.post()
                    except Exception as e:
                        logger.error(f"Failed to start VM {vm_name}: {e}")
                elif status == 'running':
                    logger.debug(f"VM {vm_name} is already running")
                    
        logger.info("Boot recovery sequence completed.")
        return True

    except Exception as e:
        logger.error(f"Error during post-boot recovery: {e}")
        return False

if __name__ == "__main__":
    # Simple CLI for testing
    import argparse
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Wait for Proxmox and start VMs")
    parser.add_argument("--host", default=os.getenv("PROXMOX_HOST"))
    parser.add_argument("--user", default=os.getenv("PROXMOX_USERNAME"))
    parser.add_argument("--password", default=os.getenv("PROXMOX_PASSWORD"))
    
    args = parser.parse_args()
    
    if all([args.host, args.user, args.password]):
        ensure_proxmox_up(args.host, args.user, args.password)
    else:
        print("Missing credentials")
