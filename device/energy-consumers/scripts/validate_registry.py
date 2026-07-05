#!/usr/bin/env python3
"""Validate energy consumers registry YAML."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

DEVICE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DEVICE_ROOT / "lib"))

from registry import load_consumers_registry  # noqa: E402


def _default_registry_path() -> Path:
    base = Path(__file__).resolve().parent.parent / "config"
    for name in ("consumers_registry.yaml", "consumers_registry.example.yaml"):
        p = base / name
        if p.is_file():
            return p
    return base / "consumers_registry.yaml"


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate consumers registry YAML")
    parser.add_argument(
        "registry",
        nargs="?",
        type=Path,
        default=_default_registry_path(),
        help="Path to consumers_registry.yaml",
    )
    args = parser.parse_args()

    try:
        data = load_consumers_registry(args.registry)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    consumers = data.get("consumers", [])
    enabled = sum(1 for c in consumers if c.get("enabled"))
    print(f"OK: {len(consumers)} consumer(s) defined, {enabled} enabled")
    for c in consumers:
        flag = "on" if c.get("enabled") else "off"
        print(f"  [{flag}] {c.get('id')} ({c.get('type')}) -> {c.get('mqtt_prefix')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
