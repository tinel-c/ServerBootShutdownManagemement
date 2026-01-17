#!/usr/bin/env python3
"""
Centralized configuration loader for Server Management System.
Handles loading YAML files and replacing environment variable placeholders.
"""

import os
import yaml
import re
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv


class ConfigurationError(Exception):
    """Raised when configuration is invalid or incomplete."""
    pass


class ConfigLoader:
    """Centralized configuration loader with environment variable support."""
    
    def __init__(self, config_dir: Path = None):
        """
        Initialize configuration loader.
        
        Args:
            config_dir: Path to configuration directory (default: ../../config from this file)
        """
        if config_dir is None:
            config_dir = Path(__file__).parent.parent.parent / "config"
        
        self.config_dir = Path(config_dir)
        self.env_loaded = False
        self.missing_vars: List[str] = []
        
    def load_env(self, env_file: str = ".env") -> bool:
        """
        Load environment variables from .env file.
        
        Args:
            env_file: Name of environment file (default: .env)
            
        Returns:
            True if loaded successfully, False otherwise
        """
        env_path = self.config_dir / env_file
        
        if env_path.exists():
            print(f"✓ Loading environment from: {env_path}")
            load_dotenv(dotenv_path=env_path)
            self.env_loaded = True
            return True
        else:
            print(f"⚠ WARNING: .env file not found at: {env_path}")
            print(f"⚠ Trying to load from current directory...")
            load_dotenv()  # Try current directory
            self.env_loaded = True
            return False
    
    def replace_env_vars(self, obj: Any, path: str = "") -> Any:
        """
        Recursively replace ${VAR} placeholders with environment variable values.
        
        Args:
            obj: Object to process (dict, list, str, or other)
            path: Current path in config (for debugging)
            
        Returns:
            Object with environment variables replaced
        """
        if isinstance(obj, dict):
            return {k: self.replace_env_vars(v, f"{path}.{k}") for k, v in obj.items()}
        
        elif isinstance(obj, list):
            return [self.replace_env_vars(item, f"{path}[{i}]") for i, item in enumerate(obj)]
        
        elif isinstance(obj, str) and '${' in obj:
            # Find all ${VAR} patterns
            pattern = r'\$\{([^}]+)\}'
            
            def replacer(match):
                env_var = match.group(1)
                val = os.getenv(env_var)
                
                if val is None:
                    error_msg = f"Environment variable '{env_var}' NOT SET (path: {path})"
                    print(f"❌ CRITICAL: {error_msg}")
                    self.missing_vars.append(env_var)
                    return match.group(0)  # Keep placeholder
                
                print(f"  ✓ Replaced ${{{env_var}}} → {val[:20]}{'...' if len(val) > 20 else ''}")
                return val
            
            result = re.sub(pattern, replacer, obj)
            return result
        
        return obj
    
    def load_yaml(self, filename: str) -> Dict[str, Any]:
        """
        Load YAML file and replace environment variables.
        
        Args:
            filename: Name of YAML file to load
            
        Returns:
            Dictionary with configuration
            
        Raises:
            ConfigurationError: If file not found or has errors
        """
        file_path = self.config_dir / filename
        
        if not file_path.exists():
            raise ConfigurationError(f"Configuration file not found: {file_path}")
        
        print(f"\n📄 Loading configuration: {filename}")
        
        with open(file_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if config is None:
            raise ConfigurationError(f"Empty or invalid YAML file: {filename}")
        
        # Replace environment variables
        config = self.replace_env_vars(config)
        
        return config
    
    def load_all(self) -> Dict[str, Any]:
        """
        Load all configuration files.
        
        Returns:
            Combined configuration dictionary
            
        Raises:
            ConfigurationError: If critical configuration is missing
        """
        # Load environment variables first
        if not self.env_loaded:
            self.load_env()
        
        config = {}
        
        # Load MQTT configuration
        try:
            mqtt_config = self.load_yaml("mqtt_config.yaml")
            config.update(mqtt_config)
        except Exception as e:
            raise ConfigurationError(f"Failed to load mqtt_config.yaml: {e}")
        
        # Load server configuration
        try:
            server_config = self.load_yaml("server_config.yaml")
            config.update(server_config)
        except Exception as e:
            raise ConfigurationError(f"Failed to load server_config.yaml: {e}")
        
        # Check for missing variables
        if self.missing_vars:
            print(f"\n❌ ERROR: {len(self.missing_vars)} environment variable(s) not set:")
            for var in sorted(set(self.missing_vars)):
                print(f"   - {var}")
            print(f"\n💡 Solution:")
            print(f"   1. Edit: {self.config_dir}/.env")
            print(f"   2. Add missing variables (see .env.example for template)")
            print(f"   3. Restart services")
            print()
            
            # Don't raise error, but warn
            print("⚠ WARNING: Continuing with placeholders - some features may not work!")
        
        # Validate critical configuration
        self._validate_config(config)
        
        return config
    
    def _validate_config(self, config: Dict[str, Any]):
        """
        Validate that critical configuration is present and valid.
        
        Args:
            config: Configuration dictionary to validate
            
        Raises:
            ConfigurationError: If critical configuration is missing or invalid
        """
        # Check MQTT broker port is resolved
        broker_port = config.get('mqtt', {}).get('broker', {}).get('port')
        if isinstance(broker_port, str) and '${' in broker_port:
            raise ConfigurationError(
                f"MQTT_BROKER_PORT not resolved. Value: {broker_port}. "
                f"Check your .env file at {self.config_dir}/.env"
            )
        
        # Check servers configuration
        servers = config.get('servers', [])
        if not servers:
            raise ConfigurationError("No servers configured in server_config.yaml")
        
        print(f"\n✅ Configuration loaded successfully!")
        print(f"   - Servers: {len(servers)}")
        print(f"   - MQTT Broker: {config.get('mqtt', {}).get('broker', {}).get('host')}")
        print()


def get_config(config_dir: Path = None) -> Dict[str, Any]:
    """
    Convenience function to load configuration.
    
    Args:
        config_dir: Path to configuration directory
        
    Returns:
        Configuration dictionary
    """
    loader = ConfigLoader(config_dir)
    return loader.load_all()


if __name__ == "__main__":
    """Test configuration loading."""
    try:
        config = get_config()
        print("\n" + "="*80)
        print("Configuration loaded successfully!")
        print("="*80)
        
        # Print summary
        print("\nServers configured:")
        for server in config.get('servers', []):
            print(f"  - {server.get('name')} ({server.get('type')})")
        
        print(f"\nMQTT Broker: {config.get('mqtt', {}).get('broker', {}).get('host')}")
        print(f"MQTT Port: {config.get('mqtt', {}).get('broker', {}).get('port')}")
        
    except ConfigurationError as e:
        print(f"\n❌ Configuration Error: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        exit(1)
