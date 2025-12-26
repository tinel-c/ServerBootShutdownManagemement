#!/usr/bin/env python3
"""
Graceful shutdown script for Dell T310 Management System.
Performs graceful shutdown of VMs and Proxmox host.
"""

import sys
import os
import time
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))

from ipmi_wrapper import IPMIWrapper
from logger import get_logger

logger = get_logger(__name__)


def shutdown_proxmox_vms(
    proxmox_host: str,
    username: str,
    password: str,
    timeout: int = 120,
    verify_ssl: bool = False
) -> bool:
    """
    Shutdown all running VMs on Proxmox host.
    
    Args:
        proxmox_host: Proxmox host IP or hostname
        username: Proxmox username
        password: Proxmox password
        timeout: Timeout for VM shutdown (seconds)
        verify_ssl: Verify SSL certificate
        
    Returns:
        True if all VMs shutdown successfully, False otherwise
    """
    try:
        from proxmoxer import ProxmoxAPI
        
        logger.info(f"Connecting to Proxmox: {proxmox_host}")
        
        # Connect to Proxmox API
        proxmox = ProxmoxAPI(
            proxmox_host,
            user=username,
            password=password,
            verify_ssl=verify_ssl
        )
        
        # Get all nodes
        nodes = proxmox.nodes.get()
        
        for node in nodes:
            node_name = node['node']
            logger.info(f"Processing node: {node_name}")
            
            # Get all VMs on this node
            vms = proxmox.nodes(node_name).qemu.get()
            
            # Shutdown running VMs
            for vm in vms:
                vm_id = vm['vmid']
                vm_name = vm.get('name', f'VM-{vm_id}')
                status = vm.get('status', 'unknown')
                
                if status == 'running':
                    logger.info(f"Shutting down VM: {vm_name} (ID: {vm_id})")
                    try:
                        proxmox.nodes(node_name).qemu(vm_id).status.shutdown.post()
                    except Exception as e:
                        logger.error(f"Failed to shutdown VM {vm_name}: {e}")
                else:
                    logger.info(f"VM {vm_name} is already stopped")
            
            # Wait for VMs to shutdown
            logger.info(f"Waiting for VMs to shutdown (timeout: {timeout}s)...")
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                vms = proxmox.nodes(node_name).qemu.get()
                running_vms = [vm for vm in vms if vm.get('status') == 'running']
                
                if not running_vms:
                    logger.info("All VMs have shutdown successfully")
                    break
                
                logger.debug(f"Waiting for {len(running_vms)} VMs to shutdown...")
                time.sleep(5)
            else:
                logger.warning(f"Timeout waiting for VMs to shutdown on node {node_name}")
                return False
        
        return True
        
    except ImportError:
        logger.error("proxmoxer library not installed. Install with: pip install proxmoxer")
        return False
    except Exception as e:
        logger.error(f"Error shutting down Proxmox VMs: {e}")
        return False


def shutdown_proxmox_host(
    manager: any,
    force: bool = False
) -> bool:
    """
    Shutdown Proxmox host via management interface (IPMI/iLO).
    
    Args:
        manager: Manager instance (IPMIWrapper or ILOWrapper)
        force: Force shutdown (hard power off)
        
    Returns:
        True if shutdown successful, False otherwise
    """
    try:
        logger.info(f"Shutting down Proxmox host via {manager.__class__.__name__}: {manager.host}")
        
        # Shutdown the host
        if force:
            logger.warning("Performing FORCE shutdown")
            success = manager.power_off(force=True)
        else:
            logger.info("Performing graceful shutdown (ACPI power button)")
            success = manager.power_off(force=False)
        
        if success:
            logger.info("Host shutdown command sent successfully")
            return True
        else:
            logger.error("Failed to send shutdown command")
            return False
            
    except Exception as e:
        logger.error(f"Error shutting down Proxmox host: {e}")
        return False


def graceful_shutdown(
    proxmox_host: str,
    proxmox_username: str,
    proxmox_password: str,
    manager: any,
    vm_timeout: int = 120,
    host_delay: int = 30,
    verify_ssl: bool = False
) -> bool:
    """
    Perform graceful shutdown of entire system.
    
    Args:
        proxmox_host: Proxmox host IP or hostname
        proxmox_username: Proxmox username
        proxmox_password: Proxmox password
        manager: Manager instance (IPMIWrapper or ILOWrapper)
        vm_timeout: Timeout for VM shutdown (seconds)
        host_delay: Delay before host shutdown (seconds)
        verify_ssl: Verify SSL certificate
        
    Returns:
        True if shutdown successful, False otherwise
    """
    logger.info(f"Starting graceful shutdown sequence for host: {manager.host}")
    
    # Step 1: Shutdown VMs
    logger.info("Step 1: Shutting down VMs...")
    if not shutdown_proxmox_vms(
        proxmox_host,
        proxmox_username,
        proxmox_password,
        timeout=vm_timeout,
        verify_ssl=verify_ssl
    ):
        logger.warning("VM shutdown completed with warnings")
    
    # Step 2: Wait before shutting down host
    logger.info(f"Step 2: Waiting {host_delay} seconds before host shutdown...")
    time.sleep(host_delay)
    
    # Step 3: Shutdown Proxmox host
    logger.info("Step 3: Shutting down Proxmox host...")
    if not shutdown_proxmox_host(manager):
        logger.error("Failed to shutdown Proxmox host")
        return False
    
    logger.info("Graceful shutdown sequence completed successfully")
    return True


if __name__ == "__main__":
    import argparse
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Gracefully shutdown Dell T310 server")
    parser.add_argument(
        "--proxmox-host",
        default=os.getenv("PROXMOX_HOST"),
        help="Proxmox host IP or hostname"
    )
    parser.add_argument(
        "--proxmox-user",
        default=os.getenv("PROXMOX_USERNAME"),
        help="Proxmox username"
    )
    parser.add_argument(
        "--proxmox-password",
        default=os.getenv("PROXMOX_PASSWORD"),
        help="Proxmox password"
    )
    parser.add_argument(
        "--ipmi-host",
        default=os.getenv("IPMI_HOST"),
        help="IPMI interface IP address"
    )
    parser.add_argument(
        "--ipmi-user",
        default=os.getenv("IPMI_USERNAME"),
        help="IPMI username"
    )
    parser.add_argument(
        "--ipmi-password",
        default=os.getenv("IPMI_PASSWORD"),
        help="IPMI password"
    )
    parser.add_argument(
        "--vm-timeout",
        type=int,
        default=120,
        help="VM shutdown timeout in seconds"
    )
    parser.add_argument(
        "--host-delay",
        type=int,
        default=30,
        help="Delay before host shutdown in seconds"
    )
    parser.add_argument(
        "--no-verify-ssl",
        action="store_true",
        help="Don't verify SSL certificate"
    )
    
    args = parser.parse_args()
    
    # Validate required arguments
    required_args = [
        args.proxmox_host, args.proxmox_user, args.proxmox_password,
        args.ipmi_host, args.ipmi_user, args.ipmi_password
    ]
    
    if not all(required_args):
        logger.error("Missing required arguments. Provide all credentials or set in .env")
        sys.exit(1)
    
    # Perform graceful shutdown
    if args.ipmi_host:
        from ipmi_wrapper import IPMIWrapper
        manager = IPMIWrapper(args.ipmi_host, args.ipmi_user, args.ipmi_password)
    else:
        # Fallback/Default to manual testing with iLO if wanted, or error
        logger.error("No manager credentials provided (--ipmi-host etc.)")
        sys.exit(1)
        
    success = graceful_shutdown(
        args.proxmox_host,
        args.proxmox_user,
        args.proxmox_password,
        manager=manager,
        vm_timeout=args.vm_timeout,
        host_delay=args.host_delay,
        verify_ssl=not args.no_verify_ssl
    )
    
    sys.exit(0 if success else 1)
