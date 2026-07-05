#!/usr/bin/env python3
"""Export enabled consumers as JSON for Node-RED flow generator."""

from __future__ import annotations

import json
import sys
from pathlib import Path

DEVICE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DEVICE_ROOT / "lib"))

from registry import load_consumers_registry  # noqa: E402


def main() -> int:
    path = DEVICE_ROOT / "config" / "consumers_registry.yaml"
    if not path.is_file():
        path = DEVICE_ROOT / "config" / "consumers_registry.example.yaml"
    data = load_consumers_registry(path)
    consumers = [c for c in data.get("consumers", []) if c.get("enabled")]
    consumers.sort(key=lambda c: (c.get("ui") or {}).get("order", 99))
    json.dump({"consumers": consumers}, sys.stdout, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
