"""ONVIF probe and LAN MAC lookup for Tapo cameras."""

from __future__ import annotations

import re
import socket
import subprocess
from typing import Any, Dict, Optional

try:
    from onvif import ONVIFCamera
except ImportError:  # pragma: no cover
    ONVIFCamera = None  # type: ignore


def normalize_mac(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    hex_only = re.sub(r"[^0-9a-fA-F]", "", value)
    if len(hex_only) != 12:
        return None
    pairs = [hex_only[i : i + 2].upper() for i in range(0, 12, 2)]
    return ":".join(pairs)


def onvif_port_open(ip: str, port: int = 2020, timeout: float = 2.0) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        return sock.connect_ex((ip, port)) == 0
    finally:
        sock.close()


def get_lan_mac(ip: str) -> Optional[str]:
    """Best-effort MAC from ARP/neighbor table (Linux automation server)."""
    for cmd in (
        ["ip", "neigh", "show", ip],
        ["arp", "-n", ip],
    ):
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=3, check=False)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
        text = (proc.stdout or "") + (proc.stderr or "")
        match = re.search(r"([0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5})", text)
        if match:
            return normalize_mac(match.group(1))
    return None


def probe_onvif(
    ip: str,
    username: str,
    password: str,
    port: int = 2020,
    timeout: float = 10.0,
) -> Dict[str, Any]:
    """Return connection probe result for one camera."""
    result: Dict[str, Any] = {
        "ip": ip,
        "port": port,
        "onvif_port_open": onvif_port_open(ip, port),
        "online": False,
        "manufacturer": None,
        "model": None,
        "serial": None,
        "firmware": None,
        "mac_observed": get_lan_mac(ip),
        "error": None,
    }

    if not result["onvif_port_open"]:
        result["error"] = "ONVIF port closed"
        return result

    if ONVIFCamera is None:
        result["error"] = "onvif-zeep not installed"
        return result

    try:
        camera = ONVIFCamera(ip, port, username, password, no_cache=True)
        info = camera.devicemgmt.GetDeviceInformation()
        result["online"] = True
        result["manufacturer"] = getattr(info, "Manufacturer", None) or None
        result["model"] = getattr(info, "Model", None) or None
        result["serial"] = getattr(info, "SerialNumber", None) or None
        result["firmware"] = getattr(info, "FirmwareVersion", None) or None
    except Exception as exc:
        result["error"] = str(exc)

    return result
