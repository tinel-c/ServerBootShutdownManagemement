"""Read power metrics from Tuya energy meters / breakers via tinytuya."""

from __future__ import annotations

import os
import time
from dataclasses import replace
from typing import Any, Dict, Optional, Tuple

try:
    import tinytuya
except ImportError as exc:
    raise ImportError("tinytuya is required") from exc

from consumer_schema import ConsumerStatus
from tongou_phase import decode_phase_raw, fetch_cloud_phase_a, find_phase_raw


def _phase_spec_ids(mapping: Dict[str, Any]) -> list[str]:
    ids: list[str] = []
    for key in ("phase_a", "phase"):
        spec = mapping.get(key)
        if spec is None:
            continue
        if isinstance(spec, dict):
            ids.append(str(spec.get("id", "")))
        else:
            ids.append(str(spec))
    return [x for x in ids if x]


def _parse_phase_metrics(dps: Dict[str, Any], mapping: Dict[str, Any]) -> Optional[Dict[str, float]]:
    phase_ids = _phase_spec_ids(mapping)
    if not phase_ids:
        # Common dlq breaker defaults: phase_a is often DP 6 (cloud); try on LAN too.
        phase_ids = ["6", "7", "8"]
    raw = find_phase_raw(dps, phase_ids)
    if raw is None:
        return None
    phase_cfg = mapping.get("phase_a") or mapping.get("phase") or {}
    power_in_kw = bool(phase_cfg.get("power_in_kw")) if isinstance(phase_cfg, dict) else False
    power_scale = float(phase_cfg.get("power_scale", 1)) if isinstance(phase_cfg, dict) else 1.0
    return decode_phase_raw(raw, power_in_kw=power_in_kw, power_scale=power_scale)


def _dps_value(dps: Dict[str, Any], spec: Any) -> Any:
    if spec is None:
        return None
    if isinstance(spec, dict):
        key = str(spec.get("id", ""))
        scale = float(spec.get("scale", 1))
        raw = dps.get(key)
        if raw is None:
            return None
        try:
            return float(raw) * scale
        except (TypeError, ValueError):
            return raw
    key = str(spec)
    return dps.get(key)


def _auto_power_w(dps: Dict[str, Any]) -> Optional[float]:
    for key, scale in (
        ("cur_power", 0.1),
        ("19", 0.1),
        ("power", 1),
        ("active_power", 1),
    ):
        if key in dps:
            try:
                return float(dps[key]) * scale
            except (TypeError, ValueError):
                continue
    return None


def _auto_voltage_v(dps: Dict[str, Any]) -> Optional[float]:
    for key, scale in (("cur_voltage", 0.1), ("20", 0.1), ("voltage", 1)):
        if key in dps:
            try:
                return float(dps[key]) * scale
            except (TypeError, ValueError):
                continue
    return None


def _auto_current_a(dps: Dict[str, Any]) -> Optional[float]:
    for key, scale in (("cur_current", 0.001), ("18", 0.001), ("current", 1)):
        if key in dps:
            try:
                return float(dps[key]) * scale
            except (TypeError, ValueError):
                continue
    return None


def _auto_energy_kwh(dps: Dict[str, Any]) -> Optional[float]:
    for key, scale in (("add_ele", 0.01), ("17", 0.01), ("total_electricity", 0.01)):
        if key in dps:
            try:
                return float(dps[key]) * scale
            except (TypeError, ValueError):
                continue
    return None


def _auto_switch(dps: Dict[str, Any]) -> Optional[bool]:
    for key in ("switch", "switch_1", "1"):
        if key in dps:
            return bool(dps[key])
    return None


def _has_phase_metrics(metrics: Optional[Dict[str, float]]) -> bool:
    if not metrics:
        return False
    return any(metrics.get(k) is not None for k in ("power_w", "voltage_v", "current_a"))


def _has_electrical_metrics(status: ConsumerStatus) -> bool:
    return any(
        value is not None for value in (status.power_w, status.voltage_v, status.current_a)
    )


def phase_stale_after_s(consumer: Dict[str, Any]) -> float:
    """How long to reuse last V/I/P when Tongou phase_a is quiet (low load)."""
    if consumer.get("phase_stale_after_s") is not None:
        return float(consumer["phase_stale_after_s"])
    mapping = consumer.get("dps") or {}
    if mapping.get("phase_a") or mapping.get("phase"):
        return float(os.getenv("ENERGY_CONSUMERS_PHASE_STALE_SEC", "600"))
    interval = float(consumer.get("poll_interval_s") or os.getenv("ENERGY_CONSUMERS_DEFAULT_INTERVAL", "30"))
    return interval * 2


def apply_metric_cache(
    consumer: Dict[str, Any],
    status: ConsumerStatus,
    *,
    previous: Optional[ConsumerStatus],
    previous_metrics_ts: float,
    now: Optional[float] = None,
) -> tuple[ConsumerStatus, float]:
    """Reuse recent V/I/P when phase_a was not refreshed this poll (device reports less at low A)."""
    now = time.time() if now is None else now
    stale_after = phase_stale_after_s(consumer)

    if _has_electrical_metrics(status):
        return status, now

    if not previous or not _has_electrical_metrics(previous):
        return status, previous_metrics_ts
    if previous_metrics_ts <= 0 or (now - previous_metrics_ts) > stale_after:
        return status, previous_metrics_ts

    extra = dict(previous.extra or {})
    extra.update(status.extra or {})
    extra["metrics_cached"] = True
    extra["metrics_age_s"] = int(now - previous_metrics_ts)
    cached = replace(
        status,
        power_w=previous.power_w,
        voltage_v=previous.voltage_v,
        current_a=previous.current_a,
        energy_kwh=status.energy_kwh if status.energy_kwh is not None else previous.energy_kwh,
        online=status.online if status.online else previous.online,
        extra=extra,
    )
    return cached, previous_metrics_ts


def parse_dps_status(
    consumer: Dict[str, Any],
    raw_status: Dict[str, Any],
    creds: Dict[str, Any],
) -> ConsumerStatus:
    dps = raw_status.get("dps") or raw_status.get("Data") or {}
    if not isinstance(dps, dict):
        dps = {}

    mapping = consumer.get("dps") or {}
    phase = _parse_phase_metrics(dps, mapping)

    power = phase.get("power_w") if phase else None
    voltage = phase.get("voltage_v") if phase else None
    current = phase.get("current_a") if phase else None

    if power is None:
        power = _dps_value(dps, mapping.get("power_w")) or _auto_power_w(dps)
    if voltage is None:
        voltage = _dps_value(dps, mapping.get("voltage_v")) or _auto_voltage_v(dps)
    if current is None:
        current = _dps_value(dps, mapping.get("current_a")) or _auto_current_a(dps)
    energy = _dps_value(dps, mapping.get("energy_kwh")) or _auto_energy_kwh(dps)
    switch_val = _dps_value(dps, mapping.get("switch"))
    if switch_val is None:
        switch_val = _auto_switch(dps)

    online = "Error" not in str(raw_status.get("Err", ""))
    lan_err = raw_status.get("Err")
    if lan_err:
        online = False
    # LAN status without phase_a still means the breaker is reachable (switch/temp/state DPS).
    if not lan_err and dps:
        online = True

    extra: Dict[str, Any] = {}
    if switch_val is not None:
        extra["switch_on"] = bool(switch_val)
    if creds.get("ip"):
        extra["tuya_ip"] = creds["ip"]
    cloud_phase: Optional[Dict[str, float]] = None
    if phase:
        extra["phase_source"] = "tongou_raw"
    elif _phase_spec_ids(mapping) and creds.get("id"):
        cloud_phase = fetch_cloud_phase_a(str(creds["id"]))
        if cloud_phase:
            power = cloud_phase.get("power_w", power)
            voltage = cloud_phase.get("voltage_v", voltage)
            current = cloud_phase.get("current_a", current)
            extra["phase_source"] = "tongou_cloud"

    # LAN key/version can fail (e.g. tinytuya 914) while Tuya cloud still reports phase_a.
    if not online and _has_phase_metrics(cloud_phase):
        online = True
        extra["lan_degraded"] = True
        if lan_err:
            extra["lan_err"] = str(lan_err)

    temp = _dps_value(dps, mapping.get("temperature_c"))
    if temp is not None:
        try:
            extra["temperature_c"] = round(float(temp), 1)
        except (TypeError, ValueError):
            pass

    for field, dps_id in (("breaker_state", "103"), ("run_mode", "110")):
        raw = dps.get(str(dps_id))
        if isinstance(raw, str) and raw:
            extra[field] = raw

    return ConsumerStatus(
        consumer_id=consumer["id"],
        name=consumer.get("name") or consumer["id"],
        power_w=round(power, 1) if power is not None else None,
        energy_kwh=round(energy, 3) if energy is not None else None,
        voltage_v=round(voltage, 1) if voltage is not None else None,
        current_a=round(current, 3) if current is not None else None,
        online=online,
        source="tuya_meter",
        tags=list(consumer.get("tags") or []),
        extra=extra,
    )


def read_tuya_status(creds: Dict[str, Any]) -> Dict[str, Any]:
    dev = tinytuya.Device(
        creds["id"],
        creds.get("ip") or "",
        creds.get("local_key") or "",
        version=str(creds.get("version") or "3.3"),
    )
    return dev.status()


def set_tuya_switch(creds: Dict[str, Any], switch_dps: str, on: bool) -> Dict[str, Any]:
    dev = tinytuya.Device(
        creds["id"],
        creds.get("ip") or "",
        creds.get("local_key") or "",
        version=str(creds.get("version") or "3.3"),
    )
    result = dev.set_value(switch_dps, on)
    if result.get("Err"):
        result = dev.set_value(switch_dps, 1 if on else 0)
    return result


def switch_dps_key(consumer: Dict[str, Any]) -> str:
    mapping = consumer.get("dps") or {}
    spec = mapping.get("switch", "1")
    if isinstance(spec, dict):
        return str(spec.get("id", "1"))
    return str(spec)
