#!/usr/bin/env python3
"""
Optional publisher stub for a single consumer.

Copy to devices/<id>/publisher.py and implement poll_once().
Run: python3 publisher.py --once
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DEVICE_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = DEVICE_DIR.parent.parent
sys.path.insert(0, str(PACKAGE_ROOT / "lib"))

from consumer_schema import ConsumerStatus  # noqa: E402


def poll_once() -> ConsumerStatus:
    """Read hardware and return status. Replace with real integration."""
    device_yaml = DEVICE_DIR / "device.yaml"
    consumer_id = "my-new-plug"
    name = "My new smart plug"
    if device_yaml.is_file():
        import yaml

        meta = yaml.safe_load(device_yaml.read_text(encoding="utf-8")) or {}
        consumer_id = meta.get("id", consumer_id)
        name = meta.get("name", name)

    return ConsumerStatus(
        consumer_id=consumer_id,
        name=name,
        power_w=0.0,
        online=True,
        source="template_stub",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Print one status JSON to stdout")
    args = parser.parse_args()

    status = poll_once()
    payload = json.dumps(status.to_mqtt_dict(), indent=2)
    if args.once:
        print(payload)
        return 0

    print("Implement MQTT publish loop or run with --once to test schema.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
