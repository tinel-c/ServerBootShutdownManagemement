"""Load and validate the consumers registry YAML."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_REQUIRED_KEYS = ("id", "name", "type", "mqtt_prefix")


def _package_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_consumers_registry(path: str | Path | None = None) -> dict[str, Any]:
    """Load consumers_registry.yaml. Returns dict with key 'consumers' (list)."""
    if path is None:
        path = _package_root() / "config" / "consumers_registry.yaml"
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Consumers registry not found: {path}")

    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}

    if not isinstance(data, dict):
        raise ValueError("Registry root must be a mapping")

    consumers = data.get("consumers", [])
    if not isinstance(consumers, list):
        raise ValueError("'consumers' must be a list")

    errors = validate_registry(data)
    if errors:
        raise ValueError("Registry validation failed:\n  - " + "\n  - ".join(errors))

    return data


def validate_registry(data: dict[str, Any]) -> list[str]:
    """Validate registry structure; return error messages."""
    errors: list[str] = []
    consumers = data.get("consumers", [])
    if not isinstance(consumers, list):
        return ["'consumers' must be a list"]

    seen_ids: set[str] = set()
    for i, entry in enumerate(consumers):
        prefix = f"consumers[{i}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix}: must be a mapping")
            continue

        for key in _REQUIRED_KEYS:
            if not entry.get(key):
                errors.append(f"{prefix}: missing '{key}'")

        cid = entry.get("id")
        if isinstance(cid, str):
            if cid in seen_ids:
                errors.append(f"duplicate consumer id: {cid}")
            seen_ids.add(cid)
            if cid != cid.lower() or " " in cid:
                errors.append(f"{prefix}: id should be lowercase hyphenated, got {cid!r}")

        mqtt_prefix = entry.get("mqtt_prefix")
        if isinstance(mqtt_prefix, str) and cid and not mqtt_prefix.endswith(str(cid)):
            errors.append(f"{prefix}: mqtt_prefix should end with consumer id ({cid})")

        ctype = entry.get("type")
        if ctype == "tuya_meter" and not entry.get("tuya_device_id"):
            errors.append(f"{prefix}: tuya_meter requires tuya_device_id")
        if ctype == "tasmota_meter" and not entry.get("tasmota_topic"):
            errors.append(f"{prefix}: tasmota_meter requires tasmota_topic")

    return errors
