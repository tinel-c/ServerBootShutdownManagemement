"""Resolve Tuya LAN credentials for a consumer from config/tuya_devices.json."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEVICES_FILE = _REPO_ROOT / "config" / "tuya_devices.json"
_ENV_FILE = _REPO_ROOT / "config" / ".env"


def _load_env_tuya_devices() -> Dict[str, Dict[str, str]]:
    """Parse TUYA_DEVICE_N_* block from config/.env."""
    if not _ENV_FILE.is_file():
        return {}
    text = _ENV_FILE.read_text(encoding="utf-8")
    count_match = re.search(r"^TUYA_DEVICE_COUNT=(\d+)", text, re.M)
    if not count_match:
        return {}
    count = int(count_match.group(1))
    by_id: Dict[str, Dict[str, str]] = {}
    for i in range(1, count + 1):
        prefix = f"TUYA_DEVICE_{i}_"
        fields: Dict[str, str] = {}
        for key in ("NAME", "ID", "LOCAL_KEY", "IP", "VERSION", "PRODUCT_ID"):
            m = re.search(rf"^{prefix}{key}=(.*)$", text, re.M)
            if not m:
                continue
            val = m.group(1).strip().strip('"')
            fields[key.lower()] = val
        dev_id = fields.get("id", "")
        if dev_id:
            by_id[dev_id] = {
                "id": dev_id,
                "name": fields.get("name", ""),
                "local_key": fields.get("local_key", ""),
                "ip": fields.get("ip", ""),
                "version": fields.get("version", "3.3"),
                "product_id": fields.get("product_id", ""),
            }
    return by_id


def load_tuya_registry() -> Dict[str, Dict[str, Any]]:
    """Device id -> credentials dict."""
    merged: Dict[str, Dict[str, Any]] = {}
    if _DEVICES_FILE.is_file():
        data = json.loads(_DEVICES_FILE.read_text(encoding="utf-8"))
        for dev in data.get("devices", []):
            dev_id = dev.get("id") or ""
            if dev_id:
                merged[dev_id] = dev
    for dev_id, dev in _load_env_tuya_devices().items():
        if dev_id not in merged or not merged[dev_id].get("local_key"):
            merged[dev_id] = {**merged.get(dev_id, {}), **dev}
    return merged


def resolve_tuya_device(
    tuya_device_id: str,
    tuya_name: Optional[str] = None,
) -> Dict[str, Any]:
    registry = load_tuya_registry()
    if tuya_device_id and tuya_device_id in registry:
        return registry[tuya_device_id]
    if tuya_name:
        name_l = tuya_name.lower()
        for dev in registry.values():
            if (dev.get("name") or "").lower() == name_l:
                return dev
    raise FileNotFoundError(
        f"Tuya device {tuya_device_id!r} not in config/tuya_devices.json — "
        "run: python3 scripts/tuya/sync_devices.py sync"
    )
