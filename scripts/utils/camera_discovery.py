#!/usr/bin/env python3
"""
Tapo Camera Discovery Tool.
Scans the local network for ONVIF-compatible Tapo cameras.
"""

import sys
import time
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

try:
    from wsdiscovery.discovery import ThreadedWSDiscovery as WSDiscovery
except ImportError:
    try:
        from WSDiscovery import WSDiscovery
    except ImportError:
        print("❌ Error: WSDiscovery not installed. Run: pip install WSDiscovery")
        sys.exit(1)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))
from logger import setup_logger

console = Console()
logger = setup_logger("camera_discovery", log_level="INFO")

def discover_cameras(timeout=5):
    """
    Search for ONVIF devices using WS-Discovery.
    """
    wsd = WSDiscovery()
    wsd.start()
    
    with Progress(console=console) as progress:
        task = progress.add_task("[cyan]Scanning network for ONVIF cameras...", total=timeout)
        for _ in range(timeout):
            time.sleep(1)
            progress.update(task, advance=1)
            
    services = wsd.searchServices()
    wsd.stop()
    
    found_cameras = []
    for service in services:
        # Tapo cameras usually have specific ONVIF service types or scopes
        # We collect all ONVIF devices and then filter
        xaddrs = service.getXAddrs()
        if xaddrs:
            addr = xaddrs[0]
            if "onvif" in addr.lower():
                # Extract IP from address (e.g., http://192.168.1.50:2020/onvif/device_service)
                import re
                match = re.search(r'//([\d\.]+)[:/]', addr)
                ip = match.group(1) if match else "Unknown"
                
                # Check if we already have this IP
                if not any(c['ip'] == ip for c in found_cameras):
                    found_cameras.append({
                        'ip': ip,
                        'addr': addr,
                        'types': [str(t) for t in service.getTypes()],
                        'scopes': [str(s) for s in service.getScopes()]
                    })
                    
    return found_cameras

def main():
    console.print("[bold blue]Tapo Camera Discovery Tool[/bold blue]")
    console.print("Searching for ONVIF-compatible devices on your network...\n")
    
    try:
        cameras = discover_cameras(timeout=5)
        
        if not cameras:
            console.print("[yellow]No ONVIF cameras found.[/yellow]")
            console.print("Make sure your cameras are powered on and ONVIF is enabled in the Tapo app.")
            return

        table = Table(title="Discovered ONVIF Devices")
        table.add_column("IP Address", style="cyan")
        table.add_column("Service URL", style="magenta")
        table.add_column("Status", style="green")

        for cam in cameras:
            table.add_row(cam['ip'], cam['addr'], "Ready")

        console.print(table)
        
        console.print("\n[bold green]Success![/bold green] Found " + str(len(cameras)) + " camera(s).")
        console.print("\n[bold]To configure them, add the following to your .env file:[/bold]")
        
        for i, cam in enumerate(cameras, 1):
            console.print(f"\n# Camera {i}")
            console.print(f"CAMERA_{i}_NAME=\"Discovered Camera {i}\"")
            console.print(f"CAMERA_{i}_IP={cam['ip']}")
            console.print(f"CAMERA_{i}_PORT=2020")
            console.print(f"CAMERA_{i}_USER=your_tapo_account_username")
            console.print(f"CAMERA_{i}_PASS=your_tapo_account_password")
            console.print(f"CAMERA_{i}_MQTT_PREFIX=\"garden/camera/cam{i}\"")
            
        console.print("\n[yellow]Note: Remember to run 'check_env.sh' after updating your .env file.[/yellow]")

    except KeyboardInterrupt:
        console.print("\n[red]Scan interrupted by user.[/red]")
    except Exception as e:
        console.print(f"\n[red]Error during discovery: {e}[/red]")
        logger.error(f"Discovery error: {e}", exc_info=True)

if __name__ == "__main__":
    main()
