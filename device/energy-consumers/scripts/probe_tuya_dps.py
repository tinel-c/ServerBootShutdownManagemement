#!/usr/bin/env python3
"""Dump Tuya DPS map for configuring consumer dps: section in registry."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DEVICE_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = DEVICE_ROOT.parent.parent
sys.path.insert(0, str(DEVICE_ROOT / "lib"))

from tuya_credentials import resolve_tuya_device  # noqa: E402
from tuya_meter import read_tuya_status  # noqa: E402
from tongou_phase import decode_phase_raw  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe Tuya device DPS for energy consumer mapping")
    parser.add_argument("--device-id", required=True, help="Tuya device id from tuya_devices.json")
    parser.add_argument("--name", help="Optional Tuya device name match")
    args = parser.parse_args()

    creds = resolve_tuya_device(args.device_id, args.name)
    raw = read_tuya_status(creds)
    print(json.dumps(raw, indent=2))
    dps = raw.get("dps") or {}
    if dps:
        for pid in ("6", "7", "8"):
            if pid in dps and isinstance(dps[pid], str):
                decoded = decode_phase_raw(dps[pid])
                if decoded:
                    print(f"\nTongou phase_a decode (DP {pid}):", json.dumps(decoded), file=sys.stderr)
        print("\nSuggested dps: block for consumers_registry.yaml:", file=sys.stderr)
        print("dps:", file=sys.stderr)
        if "6" in dps and isinstance(dps.get("6"), str):
            print('  phase_a: "6"', file=sys.stderr)
        if "16" in dps:
            print('  switch: "16"', file=sys.stderr)
        elif "1" in dps and isinstance(dps.get("1"), bool):
            print('  switch: "1"', file=sys.stderr)
        if "19" in dps:
            print('  power_w: { id: "19", scale: 0.1 }', file=sys.stderr)
        if "20" in dps:
            print('  voltage_v: { id: "20", scale: 0.1 }', file=sys.stderr)
        if "18" in dps:
            print('  current_a: { id: "18", scale: 0.001 }', file=sys.stderr)
        if "17" in dps:
            print('  energy_kwh: { id: "17", scale: 0.01 }', file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
