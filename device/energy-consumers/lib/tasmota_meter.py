"""Parse Tasmota ENERGY telemetry and switch state for energy consumers."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from consumer_schema import ConsumerStatus


def tasmota_topic(consumer: Dict[str, Any]) -> str:
    topic = (consumer.get("tasmota_topic") or "").strip()
    if not topic:
        raise ValueError(f"Consumer {consumer.get('id')}: missing tasmota_topic")
    return topic


def power_stat_key(consumer: Dict[str, Any]) -> str:
    return (consumer.get("tasmota_power_key") or "POWER").strip() or "POWER"


def command_key(consumer: Dict[str, Any]) -> str:
    return (consumer.get("tasmota_command_key") or "Power").strip() or "Power"


def stale_after_s(consumer: Dict[str, Any]) -> float:
    if consumer.get("stale_after_s") is not None:
        return float(consumer["stale_after_s"])
    interval = float(consumer.get("poll_interval_s") or 30)
    tele = consumer.get("tele_period_s")
    if tele is not None:
        return max(float(tele) * 2.5, 90.0)
    return max(interval * 3.0, 120.0)


def _parse_json_payload(payload: Any) -> Optional[dict[str, Any]]:
    if isinstance(payload, dict):
        return payload
    if not isinstance(payload, str) or not payload.strip():
        return None
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def parse_power_payload(payload: Any) -> Optional[bool]:
    """Return relay on/off from stat/<topic>/POWER (or JSON POWER key)."""
    if isinstance(payload, str):
        upper = payload.strip().upper()
        if upper in ("ON", "1", "TRUE"):
            return True
        if upper in ("OFF", "0", "FALSE"):
            return False
    data = _parse_json_payload(payload)
    if not data:
        return None
    for key in ("POWER", "Power", "POWER1"):
        if key in data:
            val = data[key]
            if isinstance(val, bool):
                return val
            if isinstance(val, str):
                return val.upper() == "ON"
    return None


def parse_sensor_status(
    consumer: Dict[str, Any],
    payload: Any,
    *,
    switch_on: Optional[bool] = None,
    online: bool = True,
    extra: Optional[dict[str, Any]] = None,
) -> ConsumerStatus:
    """Build ConsumerStatus from tele/<topic>/SENSOR JSON."""
    cid = consumer["id"]
    name = consumer.get("name", cid)
    merged_extra: dict[str, Any] = dict(extra or {})
    merged_extra.setdefault("phase_source", "tasmota_sensor")

    data = _parse_json_payload(payload)
    energy = (data or {}).get("ENERGY") if data else None
    if not isinstance(energy, dict):
        return ConsumerStatus(
            consumer_id=cid,
            name=name,
            online=online,
            source="tasmota_meter",
            tags=list(consumer.get("tags") or []),
            extra={**merged_extra, "switch_on": switch_on} if switch_on is not None else merged_extra,
        )

    def _num(key: str) -> Optional[float]:
        val = energy.get(key)
        if val is None:
            return None
        try:
            return float(val)
        except (TypeError, ValueError):
            return None

    if switch_on is not None:
        merged_extra["switch_on"] = switch_on

    for key in ("Today", "Yesterday", "Period", "Factor", "ApparentPower", "ReactivePower", "TotalStartTime"):
        val = energy.get(key)
        if val is not None:
            merged_extra[f"energy_{key.lower()}"] = val

    if data and data.get("Time"):
        merged_extra["tasmota_time"] = data["Time"]

    return ConsumerStatus(
        consumer_id=cid,
        name=name,
        power_w=_num("Power"),
        energy_kwh=_num("Total"),
        voltage_v=_num("Voltage"),
        current_a=_num("Current"),
        online=online,
        source="tasmota_meter",
        tags=list(consumer.get("tags") or []),
        extra=merged_extra,
    )


def switch_command_payload(action: str) -> Optional[str]:
    action = (action or "").lower()
    if action in ("on", "true", "1"):
        return "ON"
    if action in ("off", "false", "0"):
        return "OFF"
    if action == "toggle":
        return "TOGGLE"
    return None


def command_topics(consumer: Dict[str, Any]) -> dict[str, str]:
    """Tasmota MQTT topics for a consumer."""
    base = tasmota_topic(consumer)
    pk = power_stat_key(consumer)
    ck = command_key(consumer)
    return {
        "sensor": f"tele/{base}/SENSOR",
        "power_stat": f"stat/{base}/{pk}",
        "lwt": f"tele/{base}/LWT",
        "command_switch": f"cmnd/{base}/{ck}",
        "command_tele_period": f"cmnd/{base}/TelePeriod",
        "command_status": f"cmnd/{base}/Status",
    }
