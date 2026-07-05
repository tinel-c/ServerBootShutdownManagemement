#!/usr/bin/env python3
"""
Scaffold a new energy consumer (folder + registry entry).

Usage:
  python3 add_consumer.py --id workshop-plug --name "Workshop plug" --type tuya_meter --tuya-device-id abc123
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

import yaml

DEVICE_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = DEVICE_ROOT / "devices" / "_template"
REGISTRY = DEVICE_ROOT / "config" / "consumers_registry.yaml"


def _slug(value: str) -> str:
    s = value.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def main() -> int:
    parser = argparse.ArgumentParser(description="Add energy consumer scaffold")
    parser.add_argument("--id", help="Consumer id (lowercase-hyphen)")
    parser.add_argument("--name", required=True, help="Display name")
    parser.add_argument("--type", default="tuya_meter", choices=["tuya_meter", "tasmota_meter", "shelly_em", "custom"])
    parser.add_argument("--tuya-device-id", help="Tuya device id from sync_devices.py list")
    parser.add_argument("--tasmota-topic", help="Tasmota MQTT topic (Topic command on device)")
    parser.add_argument("--order", type=int, default=10, help="UI order on Energy page (after Huawei=2)")
    parser.add_argument("--accent", default="#38bdf8", help="Dashboard accent color")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cid = _slug(args.id or args.name)
    if not cid:
        print("ERROR: invalid id", file=sys.stderr)
        return 1

    dest = DEVICE_ROOT / "devices" / cid
    if dest.exists():
        print(f"ERROR: {dest} already exists", file=sys.stderr)
        return 1

    entry = {
        "id": cid,
        "name": args.name,
        "type": args.type,
        "enabled": False,
        "mqtt_prefix": f"energy/consumers/{cid}",
        "device_path": f"devices/{cid}",
        "poll_interval_s": 30,
        "tags": [],
        "controls": {"switch": args.type in ("tuya_meter", "tasmota_meter")},
        "ui": {"order": args.order, "accent": args.accent},
    }
    if args.tuya_device_id:
        entry["tuya_device_id"] = args.tuya_device_id
    if args.type == "tuya_meter":
        entry["dps"] = {
            "switch": "1",
            "power_w": {"id": "19", "scale": 0.1},
            "voltage_v": {"id": "20", "scale": 0.1},
            "current_a": {"id": "18", "scale": 0.001},
            "energy_kwh": {"id": "17", "scale": 0.01},
        }
    if args.type == "tasmota_meter":
        topic = args.tasmota_topic or _slug(args.name).replace("-", "")
        entry["tasmota_topic"] = topic
        entry["tasmota_power_key"] = "POWER"
        entry["tasmota_command_key"] = "Power"
        entry["tele_period_s"] = 30
        entry["stale_after_s"] = 120

    if args.dry_run:
        print(yaml.dump({"consumers": [entry]}, sort_keys=False))
        return 0

    shutil.copytree(TEMPLATE, dest)
    device_yaml = dest / "device.yaml"
    device_yaml.write_text(
        yaml.dump(
            {
                "id": cid,
                "name": args.name,
                "type": args.type,
                "enabled": False,
                "mqtt_prefix": entry["mqtt_prefix"],
                "poll_interval_s": 30,
                "tags": [],
                "config_file": "config.yaml",
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    if not REGISTRY.is_file():
        data = {"version": 1, "consumers": [entry]}
        REGISTRY.write_text(yaml.dump(data, sort_keys=False), encoding="utf-8")
    else:
        data = yaml.safe_load(REGISTRY.read_text(encoding="utf-8")) or {"version": 1, "consumers": []}
        consumers = data.get("consumers", [])
        if any(c.get("id") == cid for c in consumers):
            print(f"ERROR: {cid} already in registry", file=sys.stderr)
            shutil.rmtree(dest)
            return 1
        consumers.append(entry)
        data["consumers"] = consumers
        REGISTRY.write_text(yaml.dump(data, sort_keys=False), encoding="utf-8")

    print(f"Created {dest}")
    print(f"Updated {REGISTRY}")
    print("\nNext steps:")
    if args.type == "tuya_meter":
        print(f"  1. python3 device/energy-consumers/scripts/probe_tuya_dps.py --device-id {args.tuya_device_id or '<id>'}")
        print("  2. Edit dps: mapping in consumers_registry.yaml if needed")
    elif args.type == "tasmota_meter":
        print("  1. Confirm tasmota_topic matches Tasmota console (Topic)")
        print("  2. Ensure device MQTT broker points to automation server")
    print("  3. Set enabled: true in registry")
    print("  4. python3 device/energy-consumers/scripts/validate_registry.py")
    print("  5. node nodered/live-connection/scripts/generate-flow-840.mjs")
    print("  6. node nodered/live-connection/scripts/deploy-flow-840.mjs")
    print("  7. sudo ./install_energy_consumers_service.sh")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
