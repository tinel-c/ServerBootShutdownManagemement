#!/usr/bin/env python3
"""
Server factory for creating appropriate management interface wrappers.
Provides unified interface for IPMI and iLO servers.
"""

from typing import Dict, Any, Union
from logger import get_logger
from ipmi_wrapper import IPMIWrapper
from ilo_wrapper import ILOWrapper

logger = get_logger(__name__)


class ServerManagerError(Exception):
    """Custom exception for server manager errors."""
    pass


def get_server_manager(server_config: Dict[str, Any]) -> Union[IPMIWrapper, ILOWrapper]:
    """
    Factory function to create appropriate server management interface.
    
    Args:
        server_config: Server configuration dictionary containing:
            - type: Server type ("ipmi" or "ilo")
            - ipmi: IPMI configuration (if type is "ipmi")
            - ilo: iLO configuration (if type is "ilo")
    
    Returns:
        IPMIWrapper or ILOWrapper instance
        
    Raises:
        ServerManagerError: If server type is invalid or configuration is missing
    """
    server_type = server_config.get('type', '').lower()
    server_name = server_config.get('name', 'Unknown')
    
    logger.info(f"Creating server manager for {server_name} (type: {server_type})")
    
    if server_type == 'ipmi':
        # Create IPMI wrapper
        ipmi_config = server_config.get('ipmi')
        if not ipmi_config:
            raise ServerManagerError(f"IPMI configuration missing for server: {server_name}")
        
        return IPMIWrapper(
            host=ipmi_config.get('host'),
            username=ipmi_config.get('username'),
            password=ipmi_config.get('password'),
            interface=ipmi_config.get('interface', 'lanplus')
        )
    
    elif server_type == 'ilo':
        # Create iLO wrapper
        ilo_config = server_config.get('ilo')
        if not ilo_config:
            raise ServerManagerError(f"iLO configuration missing for server: {server_name}")
        
        return ILOWrapper(
            host=ilo_config.get('host'),
            username=ilo_config.get('username'),
            password=ilo_config.get('password'),
            verify_ssl=ilo_config.get('verify_ssl', False)
        )
    
    else:
        raise ServerManagerError(f"Unsupported server type: {server_type}")


def get_all_server_managers(config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Create server managers for all configured servers.
    
    Args:
        config: Full configuration dictionary with 'servers' list
    
    Returns:
        Dictionary mapping server names to dict with 'config' and 'manager'
        
    Raises:
        ServerManagerError: If configuration is invalid
    """
    servers = config.get('servers', [])
    
    # Support legacy single-server configuration
    if not servers and 'server' in config:
        logger.warning("Using legacy single-server configuration format")
        legacy_server = config['server']
        # Determine type based on presence of ipmi/ilo config
        if 'ipmi' in legacy_server:
            legacy_server['type'] = 'ipmi'
        elif 'ilo' in legacy_server:
            legacy_server['type'] = 'ilo'
        servers = [legacy_server]
    
    if not servers:
        raise ServerManagerError("No servers configured")
    
    server_managers = {}
    
    for server_config in servers:
        server_name = server_config.get('name', 'Unknown')
        try:
            manager = get_server_manager(server_config)
            server_managers[server_name] = {
                'config': server_config,
                'manager': manager
            }
            logger.info(f"Server manager created for: {server_name}")
        except Exception as e:
            logger.error(f"Failed to create manager for {server_name}: {e}")
            # Continue with other servers
    
    return server_managers


if __name__ == "__main__":
    # Test the server factory
    import yaml
    from pathlib import Path
    
    # Load configuration
    config_path = Path(__file__).parent.parent.parent / "config" / "server_config.yaml"
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Get all server managers
        managers = get_all_server_managers(config)
        
        print(f"Created {len(managers)} server manager(s):")
        for name, info in managers.items():
            print(f"  - {name}: {type(info['manager']).__name__}")
            
    except Exception as e:
        print(f"Error: {e}")
