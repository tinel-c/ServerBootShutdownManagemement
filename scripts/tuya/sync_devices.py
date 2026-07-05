#!/usr/bin/env python3
"""
Tuya IoT Cloud helpers — list and sync devices linked to your Smart Life / Tuya app account.

Requires API credentials from https://iot.tuya.com (see docs/TUYA_ACCOUNT_LINK.md).
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import tinytuya
except ImportError as exc:
    raise SystemExit("tinytuya is required: pip install tinytuya") from exc

# Repo paths
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = REPO_ROOT / "config"
DEVICES_FILE = CONFIG_DIR / "tuya_devices.json"
ROLES_FILE = CONFIG_DIR / "tuya_roles.yaml"


class TuyaCloudError(Exception):
    pass


def load_dotenv_config() -> None:
    env_path = CONFIG_DIR / ".env"
    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=env_path)


def get_cloud_credentials() -> Dict[str, str]:
    load_dotenv_config()
    access_id = os.getenv("TUYA_ACCESS_ID", "").strip()
    access_secret = os.getenv("TUYA_ACCESS_SECRET", "").strip()
    region = os.getenv("TUYA_API_REGION", "eu").strip().lower()
    if not access_id or not access_secret:
        raise TuyaCloudError(
            "Set TUYA_ACCESS_ID and TUYA_ACCESS_SECRET in config/.env "
            "(see docs/TUYA_ACCOUNT_LINK.md)"
        )
    return {
        "apiRegion": region,
        "apiKey": access_id,
        "apiSecret": access_secret,
        "apiDeviceID": os.getenv("TUYA_API_DEVICE_ID", "").strip(),
    }


def create_cloud() -> "tinytuya.Cloud":
    creds = get_cloud_credentials()
    return tinytuya.Cloud(
        apiRegion=creds["apiRegion"],
        apiKey=creds["apiKey"],
        apiSecret=creds["apiSecret"],
        apiDeviceID=creds.get("apiDeviceID") or "",
    )


def normalize_cloud_device(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize tinytuya cloud device record."""
    return {
        "id": raw.get("id") or raw.get("device_id") or "",
        "name": raw.get("name") or raw.get("device_name") or "",
        "product_id": raw.get("product_id") or raw.get("product_key") or "",
        "local_key": raw.get("key") or raw.get("local_key") or "",
        "ip": raw.get("ip") or "",
        "version": str(raw.get("version") or "3.3"),
        "online": raw.get("online", None),
        "uuid": raw.get("uuid") or "",
        "category": raw.get("category") or "",
        "source": "cloud",
    }


def scan_lan_devices(timeout: int = 12) -> Dict[str, Dict[str, Any]]:
    """UDP scan local network; returns map device_id -> {ip, version, product_id}."""
    try:
        found = tinytuya.deviceScan(verbose=False, maxretry=timeout)
    except TypeError:
        found = tinytuya.deviceScan(verbose=False)
    if not isinstance(found, dict):
        return {}
    result: Dict[str, Dict[str, Any]] = {}
    for _key, info in found.items():
        if not isinstance(info, dict):
            continue
        dev_id = str(info.get("id") or info.get("gwId") or _key)
        result[dev_id] = {
            "ip": info.get("ip") or _key,
            "version": str(info.get("version") or info.get("ver") or "3.3"),
            "product_id": info.get("productKey") or info.get("product_id") or "",
        }
    return result


def normalize_scan_device(dev_id: str, info: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": dev_id,
        "name": info.get("name") or "",
        "product_id": info.get("productKey") or info.get("product_id") or "",
        "local_key": info.get("key") or "",
        "ip": info.get("ip") or "",
        "version": str(info.get("version") or "3.3"),
        "online": None,
        "uuid": info.get("uuid") or "",
        "category": "",
        "source": "scan",
    }


def fetch_cloud_devices() -> List[Dict[str, Any]]:
    cloud = create_cloud()
    raw = cloud.getdevices(verbose=True)
    if isinstance(raw, dict):
        if raw.get("success") is False or raw.get("code"):
            code = raw.get("code")
            msg = raw.get("msg", "unknown error")
            hint = ""
            if code == 28841002:
                hint = (
                    " Renew IoT Core: iot.tuya.com → Cloud → Cloud Services → IoT Core → "
                    "Extend Trial (or activate the free trial on a new project). "
                    "See docs/TUYA_ACCOUNT_LINK.md#iot-core-subscription."
                )
            raise TuyaCloudError(f"Tuya Cloud error {code}: {msg}.{hint}")
        raw_devices = raw.get("result") or []
    else:
        raw_devices = raw or []
    if not raw_devices:
        raise TuyaCloudError(
            "No devices returned from Tuya Cloud. "
            "Link your Smart Life app account in the IoT portal (docs/TUYA_ACCOUNT_LINK.md Step 2)."
        )
    return [normalize_cloud_device(d) for d in raw_devices]


def merge_scan_ips(devices: List[Dict[str, Any]], scan: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    merged = []
    for dev in devices:
        d = dict(dev)
        scan_info = scan.get(d["id"], {})
        if scan_info.get("ip"):
            d["ip"] = scan_info["ip"]
            d["source"] = "cloud+scan"
        if scan_info.get("version") and d.get("version") in ("", "3.3"):
            d["version"] = scan_info["version"]
        if scan_info.get("product_id") and not d.get("product_id"):
            d["product_id"] = scan_info["product_id"]
        merged.append(d)
    return merged


def sync_lan_only(timeout: int = 12) -> Dict[str, Any]:
    """LAN scan only — IDs and IPs without local keys (cloud API required for keys)."""
    try:
        found = tinytuya.deviceScan(verbose=False, maxretry=timeout)
    except TypeError:
        found = tinytuya.deviceScan(verbose=False)
    devices = []
    if isinstance(found, dict):
        for _key, info in found.items():
            if not isinstance(info, dict):
                continue
            dev_id = str(info.get("id") or info.get("gwId") or _key)
            devices.append(normalize_scan_device(dev_id, info))
    creds: Dict[str, str] = {}
    try:
        creds = get_cloud_credentials()
    except TuyaCloudError:
        pass
    payload = {
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "cloud_region": creds.get("apiRegion", ""),
        "device_count": len(devices),
        "devices": devices,
        "note": "LAN scan only — local_key empty until cloud sync succeeds",
    }
    DEVICES_FILE.parent.mkdir(parents=True, exist_ok=True)
    DEVICES_FILE.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def sync_devices(include_scan: bool = True) -> Dict[str, Any]:
    devices = fetch_cloud_devices()
    if include_scan:
        scan = scan_lan_devices()
        devices = merge_scan_ips(devices, scan)
    creds = get_cloud_credentials()
    payload = {
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "cloud_region": creds["apiRegion"],
        "device_count": len(devices),
        "devices": devices,
    }
    DEVICES_FILE.parent.mkdir(parents=True, exist_ok=True)
    DEVICES_FILE.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def load_devices_registry() -> Dict[str, Any]:
    if not DEVICES_FILE.exists():
        raise TuyaCloudError(f"No registry at {DEVICES_FILE}. Run: sync_devices.py sync")
    return json.loads(DEVICES_FILE.read_text(encoding="utf-8"))


def load_roles() -> Dict[str, Any]:
    if not ROLES_FILE.exists():
        raise TuyaCloudError(f"Missing {ROLES_FILE}")
    import yaml
    with open(ROLES_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def match_role(device: Dict[str, Any], role_cfg: Dict[str, Any]) -> bool:
    name = (device.get("name") or "").lower()
    pid = (device.get("product_id") or "").lower()
    for token in role_cfg.get("match_name_contains", []):
        if token.lower() in name:
            return True
    for product_id in role_cfg.get("match_product_ids", []):
        if product_id.lower() == pid:
            return True
    return False


def find_device_for_role(role_name: str) -> Dict[str, Any]:
    registry = load_devices_registry()
    roles = load_roles().get("roles", {})
    if role_name not in roles:
        raise TuyaCloudError(f"Unknown role: {role_name}. See config/tuya_roles.yaml")
    role_cfg = roles[role_name]
    devices = registry.get("devices", [])
    matches = [d for d in devices if match_role(d, role_cfg)]
    if not matches:
        names = [d.get("name", d.get("id")) for d in devices]
        raise TuyaCloudError(
            f"No device matched role '{role_name}'. "
            f"Available: {names}. Edit config/tuya_roles.yaml or pick by --device-id."
        )
    if len(matches) > 1:
        # Prefer device with LAN IP from scan
        with_ip = [d for d in matches if d.get("ip")]
        if len(with_ip) == 1:
            return with_ip[0]
        raise TuyaCloudError(
            f"Multiple devices match role '{role_name}': "
            + ", ".join(f"{d.get('name')} ({d.get('id')})" for d in matches)
            + ". Use --device-id to select one."
        )
    return matches[0]


TUYA_ENV_START = "# === Tuya devices (scripts/tuya/sync_devices.py apply-env) ==="
TUYA_ENV_END = "# === end Tuya devices ==="


def format_env_value(val: str, always_quote: bool = False) -> str:
    if val == "":
        return ""
    special = ' \t#="$\\\'!&|;<>()[]{}^`~%@'
    if always_quote or any(c in val for c in special):
        escaped = val.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return val


def build_tuya_env_lines(devices: List[Dict[str, Any]]) -> List[str]:
    ordered = sorted(devices, key=lambda d: (d.get("name") or d.get("id") or "").lower())
    lines = [TUYA_ENV_START, f"TUYA_DEVICE_COUNT={len(ordered)}", ""]
    for i, dev in enumerate(ordered, 1):
        name = dev.get("name") or f"device_{i}"
        lines.extend([
            f"TUYA_DEVICE_{i}_NAME={format_env_value(name, always_quote=True)}",
            f"TUYA_DEVICE_{i}_ID={dev.get('id', '')}",
            f"TUYA_DEVICE_{i}_LOCAL_KEY={format_env_value(dev.get('local_key', ''), always_quote=True)}",
            f"TUYA_DEVICE_{i}_IP={dev.get('ip') or ''}",
            f"TUYA_DEVICE_{i}_VERSION={dev.get('version', '3.3')}",
            f"TUYA_DEVICE_{i}_PRODUCT_ID={dev.get('product_id', '')}",
            "",
        ])
    lines.append(TUYA_ENV_END)
    return lines


def replace_tuya_env_block(env_path: Path, devices: List[Dict[str, Any]]) -> int:
    if not env_path.exists():
        raise TuyaCloudError(f"Missing {env_path}")
    text = env_path.read_text(encoding="utf-8")
    new_block = "\n".join(build_tuya_env_lines(devices)) + "\n"

    if TUYA_ENV_START in text and TUYA_ENV_END in text:
        before, rest = text.split(TUYA_ENV_START, 1)
        _, after = rest.split(TUYA_ENV_END, 1)
        text = before.rstrip() + "\n\n" + new_block + after.lstrip("\n")
    else:
        import re
        lines = []
        for line in text.splitlines():
            key = line.split("=", 1)[0].strip() if "=" in line and not line.strip().startswith("#") else ""
            if key == "TUYA_DEVICE_COUNT" or re.match(r"^TUYA_DEVICE_\d+_", key):
                continue
            lines.append(line)
        text = "\n".join(lines).rstrip() + "\n\n" + new_block

    env_path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
    return len(devices)


def apply_all_devices_to_env(env_path: Optional[Path] = None) -> int:
    registry = load_devices_registry()
    devices = registry.get("devices", [])
    if not devices:
        raise TuyaCloudError("No devices in registry. Run: sync_devices.py sync")
    path = env_path or (CONFIG_DIR / ".env")
    count = replace_tuya_env_block(path, devices)
    return count


def update_env_file(updates: Dict[str, str], env_path: Path = CONFIG_DIR / ".env") -> None:
    if not env_path.exists():
        raise TuyaCloudError(f"Missing {env_path}")
    lines = env_path.read_text(encoding="utf-8").splitlines()
    remaining = {k: v for k, v in updates.items()}
    out: List[str] = []
    for line in lines:
        key = line.split("=", 1)[0] if "=" in line and not line.strip().startswith("#") else None
        if key and key in remaining:
            out.append(f"{key}={remaining.pop(key)}")
        else:
            out.append(line)
    for key, val in remaining.items():
        out.append(f"{key}={val}")
    env_path.write_text("\n".join(out) + "\n", encoding="utf-8")


def apply_role_to_env(role_name: str, device_id: Optional[str] = None) -> Dict[str, str]:
    if device_id:
        registry = load_devices_registry()
        device = next((d for d in registry.get("devices", []) if d.get("id") == device_id), None)
        if not device:
            raise TuyaCloudError(f"Device id not in registry: {device_id}")
    else:
        device = find_device_for_role(role_name)

    roles = load_roles().get("roles", {})
    mapping = roles[role_name].get("env_mapping", {})
    field_map = {
        "device_id": device.get("id", ""),
        "local_key": device.get("local_key", ""),
        "ip": device.get("ip", ""),
        "version": device.get("version", "3.3"),
    }
    updates = {env_key: field_map[src] for src, env_key in mapping.items()}
    update_env_file(updates)
    return updates


def print_device_table(devices: List[Dict[str, Any]]) -> None:
    if not devices:
        print("No devices.")
        return
    print(f"{'NAME':<24} {'ID':<24} {'IP':<16} {'VER':<5} {'PRODUCT_ID':<20}")
    print("-" * 95)
    for d in devices:
        print(
            f"{(d.get('name') or '')[:24]:<24} "
            f"{(d.get('id') or '')[:24]:<24} "
            f"{(d.get('ip') or '-'):<16} "
            f"{(d.get('version') or '-'):<5} "
            f"{(d.get('product_id') or '-'):<20}"
        )


def test_local_device(device: Dict[str, Any]) -> str:
    dev = tinytuya.Device(
        device["id"],
        device.get("ip") or "",
        device.get("local_key") or "",
        version=device.get("version") or "3.3",
    )
    try:
        status = dev.status()
        return json.dumps(status, indent=2)
    except Exception as e:
        return f"ERROR: {e}"


def main(argv: Optional[List[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Tuya Cloud device sync for automation server")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List devices from Tuya Cloud (live API)")

    p_sync = sub.add_parser("sync", help="Fetch cloud devices, merge LAN IPs, save config/tuya_devices.json")
    p_sync.add_argument("--no-scan", action="store_true", help="Skip UDP LAN scan for IPs")

    p_apply = sub.add_parser("apply-role", help="Write role-matched device credentials to config/.env")
    p_apply.add_argument("role", help="Role name from config/tuya_roles.yaml (e.g. media_server)")
    p_apply.add_argument("--device-id", help="Force specific device id from registry")

    p_test = sub.add_parser("test", help="Test local API connection to a device")
    p_test.add_argument("--device-id", help="Device id (default: MEDIA_SERVER_TUYA_DEVICE_ID from .env)")

    p_verify = sub.add_parser("verify", help="Verify cloud API credentials only")

    sub.add_parser("scan-lan", help="LAN scan only (no local keys); use when cloud trial is expired")

    sub.add_parser("apply-env", help="Write all registry devices to config/.env (TUYA_DEVICE_N_* block)")

    args = parser.parse_args(argv)

    try:
        if args.command == "verify":
            devices = fetch_cloud_devices()
            print(f"OK — cloud API works, {len(devices)} device(s) linked")
            return 0

        if args.command == "list":
            devices = fetch_cloud_devices()
            print_device_table(devices)
            return 0

        if args.command == "sync":
            payload = sync_devices(include_scan=not args.no_scan)
            print(f"Synced {payload['device_count']} device(s) → {DEVICES_FILE}")
            print_device_table(payload["devices"])
            missing_ip = [d for d in payload["devices"] if not d.get("ip")]
            if missing_ip:
                print(f"\nNote: {len(missing_ip)} device(s) have no LAN IP — run sync again while devices are online on WiFi.")
            return 0

        if args.command == "scan-lan":
            payload = sync_lan_only()
            print(f"LAN scan: {payload['device_count']} device(s) → {DEVICES_FILE}")
            print_device_table(payload["devices"])
            print("\nNote: local_key is empty — renew IoT Core trial, then run: sync_devices.py sync")
            return 0

        if args.command == "apply-env":
            count = apply_all_devices_to_env()
            print(f"Updated config/.env — {count} device(s) as TUYA_DEVICE_1..{count}_*")
            print_device_table(
                sorted(load_devices_registry().get("devices", []), key=lambda d: (d.get("name") or "").lower())
            )
            return 0

        if args.command == "apply-role":
            updates = apply_role_to_env(args.role, device_id=args.device_id)
            print(f"Updated config/.env for role '{args.role}':")
            for k, v in updates.items():
                masked = v if k.endswith("_KEY") else v
                if k.endswith("_KEY") and len(v) > 6:
                    masked = v[:3] + "..." + v[-3:]
                print(f"  {k}={masked}")
            return 0

        if args.command == "test":
            load_dotenv_config()
            dev_id = args.device_id or os.getenv("MEDIA_SERVER_TUYA_DEVICE_ID", "")
            registry = load_devices_registry()
            device = next((d for d in registry.get("devices", []) if d.get("id") == dev_id), None)
            if not device:
                raise TuyaCloudError(f"Device not found: {dev_id}")
            print(test_local_device(device))
            return 0

    except TuyaCloudError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
