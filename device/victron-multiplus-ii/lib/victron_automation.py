"""Derived automation metrics from Victron Modbus readings."""

from __future__ import annotations

from typing import Any


def pv_power_w_for_automation(metrics: dict[str, Any]) -> tuple[int, str]:
    """
    PV production (W) used for load headroom.

    Prefer grid-tie PV inverter register when configured; otherwise system PV
    (AC-coupled output, AC grid, DC, or MPPT).
    """
    pv_inv = metrics.get("pv_inverter")
    if pv_inv and pv_inv.get("ac_power_l1_w") is not None:
        return int(pv_inv["ac_power_l1_w"]), "pvinverter.ac_power_l1"

    pv = metrics.get("pv") or {}
    ac_out = int(pv.get("ac_output_l1_w") or 0)
    ac_grid = int(pv.get("ac_grid_l1_w") or 0)
    dc = int(pv.get("dc_power_w") or 0)

    solar = metrics.get("solar_charger")
    mppt = int(solar.get("pv_power_w") or 0) if solar else 0

    if ac_out > 0:
        return ac_out, "pv.ac_output_l1"
    if ac_grid > 0:
        return ac_grid, "pv.ac_grid_l1"
    if dc > 0:
        return dc, "pv.dc_power"
    if mppt > 0:
        return mppt, "solar_charger.pv_power"
    return 0, "none"


def compute_automation_metrics(
    metrics: dict[str, Any],
    min_headroom_w: int = 0,
) -> dict[str, Any]:
    """
    PV production minus AC consumption L1.

    Positive headroom → surplus solar; optional loads (e.g. AC) may run.
    Zero or negative → not enough on-site PV; defer discretionary loads.
    """
    consumption = int(metrics["load"]["consumption_l1_w"])
    pv_power, pv_source = pv_power_w_for_automation(metrics)
    headroom = pv_power - consumption

    return {
        "pv_power_w": pv_power,
        "pv_source": pv_source,
        "consumption_l1_w": consumption,
        "headroom_w": headroom,
        "can_add_load": headroom > min_headroom_w,
        "min_headroom_w": min_headroom_w,
    }
