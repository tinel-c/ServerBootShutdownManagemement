#!/usr/bin/env python3
"""BLE discovery and GATT dump for Grundfos SCALA1 (Grundfos GO protocol capture aid)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

from scala1_ble import Scala1BleClient, load_scala1_config, run_async  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan and probe Grundfos SCALA1 over BLE")
    parser.add_argument("--scan", action="store_true", help="Scan for SCALA* BLE devices")
    parser.add_argument("--dump", metavar="MAC", nargs="?", const="", help="Connect and dump GATT table")
    parser.add_argument("--read", action="store_true", help="Read metrics using configured UUIDs / metrics_map")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    config = load_scala1_config()
    client = Scala1BleClient(config)

    if args.scan:
        devices = run_async(client.scan())
        if args.json:
            print(json.dumps(devices, indent=2))
        else:
            if not devices:
                print("No devices matching SCALA1 name filter found.")
                print(f"Filter: {config.name_filter!r}  Timeout: {config.scan_timeout}s")
                return 1
            print(f"Found {len(devices)} device(s):\n")
            for dev in devices:
                print(f"  {dev['address']}  {dev['name']}")
            print("\nSet SCALA1_BLE_ADDRESS in device/grundfos-scala1/config/.env then re-run --dump")
        return 0

    if args.dump is not None:
        address = args.dump or config.ble_address
        if not address:
            print("Error: provide MAC or set SCALA1_BLE_ADDRESS")
            return 1
        try:
            dump = run_async(client.dump_gatt(address))
        except Exception as exc:
            print(f"GATT dump failed: {exc}")
            return 1
        if args.json:
            print(json.dumps(dump, indent=2))
        else:
            print(f"Connected: {dump['address']}\n")
            for svc in dump.get("services", []):
                print(f"Service {svc['uuid']}  {svc.get('description') or ''}")
                for char in svc.get("characteristics", []):
                    props = ",".join(char.get("properties", []))
                    line = f"  Char {char['uuid']}  [{props}]"
                    if "value_hex" in char:
                        line += f"  hex={char['value_hex'][:64]}"
                        if char.get("value_len", 0) > 32:
                            line += "..."
                    if "read_error" in char:
                        line += f"  ERR={char['read_error']}"
                    print(line)
                print()
            print("Document UUIDs in device/grundfos-scala1/docs/BLE_PROTOCOL.md")
        return 0

    if args.read:
        if not config.ble_address:
            print("Error: SCALA1_BLE_ADDRESS not set")
            return 1
        try:
            metrics = run_async(client.read_metrics())
        except Exception as exc:
            print(f"Read failed: {exc}")
            return 1
        if args.json:
            print(json.dumps(metrics, indent=2))
        else:
            print(json.dumps(metrics, indent=2))
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
