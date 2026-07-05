"""MQTT payload schema for energy/consumers/<id>/status."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class ConsumerStatus:
    """Standard retained status payload for a single consumer."""

    consumer_id: str
    name: str
    power_w: Optional[float] = None
    energy_kwh: Optional[float] = None
    voltage_v: Optional[float] = None
    current_a: Optional[float] = None
    online: bool = True
    source: str = "unknown"
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    tags: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    def to_mqtt_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if not data["extra"]:
            data.pop("extra")
        return data


def validate_status_payload(payload: dict[str, Any]) -> list[str]:
    """Return list of validation errors (empty if OK)."""
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["payload must be a JSON object"]

    for key in ("consumer_id", "name", "timestamp"):
        if key not in payload or payload[key] in (None, ""):
            errors.append(f"missing required field: {key}")

    if "power_w" in payload and payload["power_w"] is not None:
        try:
            float(payload["power_w"])
        except (TypeError, ValueError):
            errors.append("power_w must be numeric")

    if "energy_kwh" in payload and payload["energy_kwh"] is not None:
        try:
            float(payload["energy_kwh"])
        except (TypeError, ValueError):
            errors.append("energy_kwh must be numeric")

    if "online" in payload and not isinstance(payload["online"], bool):
        errors.append("online must be boolean")

    return errors
