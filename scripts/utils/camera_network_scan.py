#!/usr/bin/env python3
"""
Scan the local network for Tapo / ONVIF cameras (port 2020 + optional RTSP 554).

Use on the automation server (same LAN as the cameras):
    python3 scripts/utils/camera_network_scan.py
    python3 scripts/utils/camera_network_scan.py --subnet 192.168.2
"""

import argparse
import re
import socket
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))

try:
    from onvif import ONVIFCamera
except ImportError:
    print("❌ Error: onvif-zeep not installed. Run: pip install onvif-zeep")
    sys.exit(1)

DEFAULT_SUBNETS = ("192.168.2",)
ONVIF_PORT = 2020
RTSP_PORT = 554


def _scan_port(subnet: str, port: int, timeout: float = 0.35) -> List[str]:
    def check(ip: str) -> Optional[str]:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            if sock.connect_ex((ip, port)) == 0:
                return ip
        finally:
            sock.close()
        return None

    ips = [f"{subnet}.{i}" for i in range(1, 255)]
    found: List[str] = []
    with ThreadPoolExecutor(max_workers=64) as executor:
        futures = {executor.submit(check, ip): ip for ip in ips}
        for future in as_completed(futures):
            result = future.result()
            if result:
                found.append(result)
    return sorted(found, key=lambda x: int(x.split(".")[-1]))


def _probe_onvif(ip: str, port: int, username: str, password: str) -> Optional[Dict[str, str]]:
    try:
        camera = ONVIFCamera(ip, port, username, password)
        info = camera.devicemgmt.GetDeviceInformation()
        return {
            "ip": ip,
            "port": str(port),
            "manufacturer": getattr(info, "Manufacturer", "") or "",
            "model": getattr(info, "Model", "") or "",
            "serial": getattr(info, "SerialNumber", "") or "",
        }
    except Exception:
        return None


def scan_network(
    subnets: Tuple[str, ...],
    username: str,
    password: str,
) -> Tuple[List[Dict[str, str]], List[str]]:
    """Return (onvif_cameras, rtsp_only_hosts)."""
    onvif_hosts: List[str] = []
    rtsp_hosts: List[str] = []
    for subnet in subnets:
        onvif_hosts.extend(_scan_port(subnet, ONVIF_PORT))
        for ip in _scan_port(subnet, RTSP_PORT):
            if ip not in onvif_hosts and ip not in rtsp_hosts:
                rtsp_hosts.append(ip)

    onvif_hosts = sorted(set(onvif_hosts), key=lambda x: int(x.split(".")[-1]))
    rtsp_hosts = sorted(set(rtsp_hosts), key=lambda x: int(x.split(".")[-1]))

    cameras: List[Dict[str, str]] = []
    for ip in onvif_hosts:
        details = _probe_onvif(ip, ONVIF_PORT, username, password)
        if details:
            cameras.append(details)

    rtsp_only = [ip for ip in rtsp_hosts if ip not in {c["ip"] for c in cameras}]
    return cameras, rtsp_only


def _slug(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", name.strip().lower()).strip("_")
    return slug or "camera"


def print_env_template(cameras: List[Dict[str, str]], rtsp_only: List[str]) -> None:
    print("\n# Suggested CAMERA_N_* entries (verify names in Tapo app):\n")
    for index, cam in enumerate(cameras, 1):
        slug = _slug(cam["model"] or f"cam{index}")
        print(f'CAMERA_{index}_NAME="Tapo {cam["model"]} ({cam["ip"]})"')
        print(f"CAMERA_{index}_IP={cam['ip']}")
        print(f"CAMERA_{index}_PORT={cam['port']}")
        print("CAMERA_{}_USER=your_camera_account".format(index))
        print("CAMERA_{}_PASS=your_camera_password".format(index))
        print(f'CAMERA_{index}_MQTT_PREFIX="garden/camera/{slug}"')
        print()

    if rtsp_only:
        print("# RTSP-only hosts (Tapo web UI detected but ONVIF :2020 closed — enable ONVIF in Tapo app):")
        for ip in rtsp_only:
            print(f"#   {ip}")
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan LAN for Tapo/ONVIF cameras")
    parser.add_argument(
        "--subnet",
        action="append",
        default=list(DEFAULT_SUBNETS),
        help="Subnet prefix to scan (default: 192.168.2). Repeat for multiple.",
    )
    parser.add_argument("--user", default="", help="ONVIF Camera Account username (optional)")
    parser.add_argument("--pass", dest="password", default="", help="ONVIF Camera Account password")
    args = parser.parse_args()

    username = args.user or None
    password = args.password or None
    if not username or not password:
        print("Scanning ports only (pass --user and --pass to probe ONVIF device info).\n")

    print("Scanning subnet(s):", ", ".join(f"{s}.0/24" for s in args.subnet))
    if username and password:
        cameras, rtsp_only = scan_network(tuple(args.subnet), username, password)
    else:
        cameras = []
        rtsp_only = []
        for subnet in args.subnet:
            for ip in _scan_port(subnet, ONVIF_PORT):
                cameras.append({"ip": ip, "port": str(ONVIF_PORT), "manufacturer": "?", "model": "?", "serial": "?"})
            for ip in _scan_port(subnet, RTSP_PORT):
                if ip not in {c["ip"] for c in cameras}:
                    rtsp_only.append(ip)

    if cameras:
        print(f"\nONVIF port {ONVIF_PORT} open on {len(cameras)} host(s):")
        for cam in cameras:
            print(
                f"  {cam['ip']}:{cam['port']}\t{cam.get('manufacturer', '?')}\t"
                f"{cam.get('model', '?')}\t{cam.get('serial', '')}"
            )
    else:
        print(f"\nNo hosts with ONVIF port {ONVIF_PORT} open.")

    if rtsp_only:
        print(f"\nRTSP :{RTSP_PORT} without ONVIF (enable ONVIF in Tapo app):")
        for ip in rtsp_only:
            print(f"  {ip}")

    if username and password:
        print_env_template(cameras, rtsp_only)


if __name__ == "__main__":
    main()
