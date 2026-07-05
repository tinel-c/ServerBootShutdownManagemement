"""Decode Tongou / Tuya smart breaker phase_a RAW payloads.

Spec: https://www.tongou.com/es/api/tuya-smart-device-api/

8-byte big-endian payload (after Base64 decode):
  bytes 0-1: voltage, unit 0.1 V
  bytes 2-4: current, unit 0.001 A
  bytes 5-7: active power, unit 1 W (Tongou); some firmware uses 0.001 kW instead
"""

from __future__ import annotations

import base64
import binascii
from typing import Any, Dict, Optional


def _to_bytes(value: Any) -> Optional[bytes]:
    if value is None:
        return None
    if isinstance(value, (bytes, bytearray)):
        return bytes(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return base64.b64decode(text, validate=False)
        except (binascii.Error, ValueError):
            pass
        try:
            return bytes.fromhex(text.replace(" ", ""))
        except ValueError:
            return None
    return None


def decode_phase_raw(
    value: Any,
    *,
    power_scale: float = 1.0,
    power_in_kw: bool = False,
) -> Optional[Dict[str, float]]:
    """Return voltage_v, current_a, power_w from a phase_a RAW value."""
    raw = _to_bytes(value)
    if not raw or len(raw) < 8:
        return None
    voltage_v = int.from_bytes(raw[0:2], "big") / 10.0
    current_a = int.from_bytes(raw[2:5], "big") / 1000.0
    power_raw = int.from_bytes(raw[5:8], "big")
    if power_in_kw:
        power_w = power_raw * power_scale * 1000.0
    else:
        power_w = power_raw * power_scale
    return {
        "voltage_v": round(voltage_v, 1),
        "current_a": round(current_a, 3),
        "power_w": round(power_w, 1),
    }


def find_phase_raw(dps: Dict[str, Any], phase_ids: list[str]) -> Optional[Any]:
    for pid in phase_ids:
        if pid in dps:
            val = dps[pid]
            if isinstance(val, str) and val:
                return val
    return None


def fetch_cloud_phase_a(device_id: str) -> Optional[Dict[str, float]]:
    """Fetch phase_a from Tuya cloud when LAN status lacks RAW phase data."""
    try:
        import sys
        from pathlib import Path

        repo = Path(__file__).resolve().parents[3]
        tuya_scripts = repo / "scripts" / "tuya"
        if str(tuya_scripts) not in sys.path:
            sys.path.insert(0, str(tuya_scripts))
        from sync_devices import create_cloud  # noqa: WPS433

        cloud = create_cloud()
        status = cloud.getstatus(device_id)
        items = []
        if isinstance(status, dict):
            items = status.get("result") or status.get("data") or []
        if isinstance(items, dict):
            items = [{"code": k, "value": v} for k, v in items.items()]
        for item in items:
            if not isinstance(item, dict):
                continue
            code = str(item.get("code", ""))
            if code == "phase_a":
                return decode_phase_raw(item.get("value"))
    except Exception:
        return None
    return None
