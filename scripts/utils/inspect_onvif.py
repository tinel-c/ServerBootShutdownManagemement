#!/usr/bin/env python3
"""
ONVIF Service Inspector.
Used to debug available services on a camera when standard monitoring fails.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))

from config_loader import get_config
from onvif import ONVIFCamera

def inspect_camera(config):
    name = config.get('name', 'Unknown')
    ip = config.get('ip')
    port = config.get('port', 2020)
    user = config.get('username')
    pw = config.get('password')

    print(f"\n--- Inspecting Camera: {name} ({ip}:{port}) ---")
    
    try:
        cam = ONVIFCamera(ip, port, user, pw)
        print("✅ Core Connection: Success")
        
        # List all services
        print("\nAvailable Services:")
        services = cam.get_services()
        for service in services:
            print(f"  - {service.Namespace}: {service.XAddr}")
            
        # Try to create Event service
        try:
            event_service = cam.create_events_service()
            print("\n✅ Event Service: Supported")
            
            # Try GetEventProperties
            try:
                props = event_service.GetEventProperties()
                print("✅ GetEventProperties: Supported")
                print(f"  Available Topics: {len(props.TopicSet)}")
            except Exception as e:
                print(f"❌ GetEventProperties: Failed ({e})")
                
            # Try to create PullPoint service
            try:
                # This is where the user's error happens
                pullpoint_service = cam.create_pullpoint_service()
                print("✅ PullPoint Service: Supported")
            except Exception as e:
                print(f"❌ PullPoint Service: Failed ({e})")
                
        except Exception as e:
            print(f"❌ Event Service: Failed ({e})")
            
    except Exception as e:
        print(f"❌ Core Connection: Failed ({e})")

def main():
    try:
        config = get_config()
        cameras = config.get('cameras', [])
        
        if not cameras:
            print("No cameras found in configuration.")
            return
            
        for cam in cameras:
            inspect_camera(cam)
            
    except Exception as e:
        print(f"Error loading configuration: {e}")

if __name__ == "__main__":
    main()
