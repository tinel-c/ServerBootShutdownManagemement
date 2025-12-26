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
        
        # Get HA resources to identify HA-managed VMs
        ha_vm_ids = set()
        try:
            # HA resources typically return a list of dicts with 'sid' like 'vm:100'
            # We catch errors just in case HA is not configured or accessible
            ha_resources = proxmox.cluster.ha.resources.get()
            for resource in ha_resources:
                sid = resource.get('sid', '')
                if sid.startswith('vm:'):
                    # Extract ID from 'vm:100'
                    ha_vm_ids.add(str(sid.split(':')[1]))
            
            if ha_vm_ids:
                logger.info(f"Identified HA-managed VMs (skipping explicit shutdown): {', '.join(ha_vm_ids)}")
        except Exception as e:
            logger.debug(f"Could not fetch HA resources (normal for standalone nodes): {e}")

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
                    # Check if HA managed
                    if str(vm_id) in ha_vm_ids:
                        logger.info(f"Skipping explicit shutdown for HA-managed VM: {vm_name} (ID: {vm_id})")
                        continue

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


def shutdown_proxmox_node(
    proxmox_host: str,
    username: str,
    password: str,
    verify_ssl: bool = False
) -> bool:
    """
    Shutdown Proxmox node via API (clean OS shutdown).
    
    Args:
        proxmox_host: Proxmox host IP or hostname
        username: Proxmox username
        password: Proxmox password
        verify_ssl: Verify SSL certificate
        
    Returns:
        True if shutdown command accepted, False otherwise
    """
    try:
        from proxmoxer import ProxmoxAPI
        
        logger.info(f"Initiating Proxmox Node Shutdown via API: {proxmox_host}")
        
        proxmox = ProxmoxAPI(
            proxmox_host,
            user=username,
            password=password,
            verify_ssl=verify_ssl
        )
        
        # Shutdown all nodes (usually just one in standalone)
        nodes = proxmox.nodes.get()
        success = True
        
        for node in nodes:
            node_name = node['node']
            status = node.get('status', 'unknown')
            
            if status == 'online':
                logger.info(f"Sending shutdown command to node: {node_name}")
                try:
                    # Execute 'shutdown' command on the node via status endpoint
                    # Correct API: POST /nodes/{node}/status with parameter command='shutdown'
                    proxmox.nodes(node_name).status.post(command='shutdown')
                    logger.info(f"Shutdown command sent to node {node_name}")
                except Exception as e:
                    logger.error(f"Failed to shutdown node {node_name} via API: {e}")
                    success = False
            else:
                logger.info(f"Node {node_name} is already offline (status: {status})")
                
        return success

    except Exception as e:
        logger.error(f"Error during Proxmox API node shutdown: {e}")
        return False


def shutdown_host_hardware(
    manager: any,
    force: bool = False
) -> bool:
    """
    Shutdown host via management interface (IPMI/iLO).
    Used as fallback or for forced shutdown.
    """
    try:
        method = "FORCE" if force else "ACPI"
        logger.info(f"Shutting down host via {manager.__class__.__name__} ({method}): {manager.host}")
        
        return manager.power_off(force=force)
            
    except Exception as e:
        logger.error(f"Error shutting down host hardware: {e}")
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
    
    # Step 3: Shutdown Proxmox Node (OS Level)
    logger.info("Step 3: Shutting down Proxmox Host (OS Level)...")
    
    # Try API shutdown first (cleanest method)
    api_shutdown_success = shutdown_proxmox_node(
        proxmox_host,
        proxmox_username,
        proxmox_password,
        verify_ssl=verify_ssl
    )
    
    if api_shutdown_success:
        logger.info("Proxmox Node shutdown initiated via API. System should power off shortly.")
        # We assume success if API call worked. 
        # Ideally we could wait and check if it actually goes down, 
        # but for now we trust the API unless it threw an error.
        return True
    
    # Fallback to ACPI/IPMI if API failed
    logger.warning("API shutdown failed. Falling back to IPMI/iLO ACPI shutdown...")
    if not shutdown_host_hardware(manager, force=False):
        logger.error("Failed to shutdown host via fallback method")
        return False
    
    logger.info("Graceful shutdown sequence completed (via fallback)")
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
