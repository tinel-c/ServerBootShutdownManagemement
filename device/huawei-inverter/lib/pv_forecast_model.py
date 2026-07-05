"""PV power estimate from Open-Meteo irradiance for east/west split strings.

Site layout (Huawei SUN2000):
- 20 panels total
- String 1: 10 panels facing west
- String 2: 10 panels facing east

Uses horizontal shortwave radiation (GHI, W/m²) and time-of-day orientation
weights to split expected power between strings.
"""

from __future__ import annotations

import math
from typing import Any

PANELS_STRING1_WEST = 10
PANELS_STRING2_EAST = 10
PANELS_TOTAL = PANELS_STRING1_WEST + PANELS_STRING2_EAST
G_REF_WM2 = 1000.0  # STC reference irradiance
EAST_PEAK_H = 9.5  # string 1 — 10 east-facing panels
WEST_PEAK_H = 15.5  # string 2 — 10 west-facing panels
ORIENTATION_SIGMA_H = 2.5
DEFAULT_SYSTEM_EFFICIENCY = 0.85


def orientation_weights(
    local_hour: float,
    *,
    east_peak: float = EAST_PEAK_H,
    west_peak: float = WEST_PEAK_H,
    sigma: float = ORIENTATION_SIGMA_H,
) -> tuple[float, float]:
    """Relative east (string 2) vs west (string 1) response by local hour."""
    w_east = math.exp(-((local_hour - east_peak) ** 2) / (2 * sigma**2))
    w_west = math.exp(-((local_hour - west_peak) ** 2) / (2 * sigma**2))
    return w_east, w_west


def string_dc_power_w(voltage_v: float | None, current_a: float | None) -> float | None:
    if voltage_v is None or current_a is None:
        return None
    return float(voltage_v) * float(current_a)


def estimate_pv_power_w(
    radiation_wm2: float | None,
    rated_power_w: float,
    local_hour: float,
    *,
    system_efficiency: float = DEFAULT_SYSTEM_EFFICIENCY,
) -> dict[str, Any]:
    """Estimate total and per-string PV power from forecast irradiance.

    P_est = P_rated × (G / 1000) × η × min(1, w_east + w_west)
    P_est_string1 = P_est × w_west / (w_east + w_west)
    P_est_string2 = P_est × w_east / (w_east + w_west)
    """
    w_east, w_west = orientation_weights(local_hour)
    w_sum = w_east + w_west
    if not radiation_wm2 or radiation_wm2 <= 0 or rated_power_w <= 0:
        return {
            "total_w": 0,
            "string1_w": 0,
            "string2_w": 0,
            "w_east": round(w_east, 3),
            "w_west": round(w_west, 3),
            "g_frac": 0.0,
        }

    g_frac = float(radiation_wm2) / G_REF_WM2
    total = rated_power_w * g_frac * system_efficiency
    if w_sum <= 0:
        return {
            "total_w": round(total),
            "string1_w": round(total / 2),
            "string2_w": round(total / 2),
            "w_east": round(w_east, 3),
            "w_west": round(w_west, 3),
            "g_frac": round(g_frac, 4),
        }
    return {
        "total_w": round(total),
        "string1_w": round(total * w_west / w_sum),
        "string2_w": round(total * w_east / w_sum),
        "w_east": round(w_east, 3),
        "w_west": round(w_west, 3),
        "g_frac": round(g_frac, 4),
    }


def average_pv_power_w(history: list[dict[str, Any]], *, max_samples: int = 96) -> int | None:
    """Rolling average DC/active power from 15-min history buckets (default 24 h)."""
    values: list[float] = []
    for point in history[-max_samples:]:
        raw = point.get("dc")
        if raw is None:
            raw = point.get("active")
        if raw is None:
            continue
        val = float(raw)
        if val > 0:
            values.append(val)
    if not values:
        return None
    return round(sum(values) / len(values))


def build_pv_forecast(
    *,
    radiation_wm2: float | None,
    rated_power_w: float,
    local_hour: float,
    string1_voltage_v: float | None,
    string1_current_a: float | None,
    string2_voltage_v: float | None,
    string2_current_a: float | None,
    input_power_w: float | None = None,
    active_power_w: float | None = None,
    history: list[dict[str, Any]] | None = None,
    is_day: bool | None = None,
) -> dict[str, Any]:
    s1 = string_dc_power_w(string1_voltage_v, string1_current_a)
    s2 = string_dc_power_w(string2_voltage_v, string2_current_a)
    if s1 is not None and s2 is not None:
        total_actual = s1 + s2
    elif input_power_w is not None:
        total_actual = float(input_power_w)
    elif active_power_w is not None:
        total_actual = float(active_power_w)
    else:
        total_actual = None

    expected = estimate_pv_power_w(radiation_wm2, rated_power_w, local_hour)
    avg_pv = average_pv_power_w(history or [])
    performance_pct = None
    if expected["total_w"] > 0 and total_actual is not None:
        performance_pct = round((total_actual / expected["total_w"]) * 100)

    return {
        "formula": (
            "P_est = P_rated × (G/1000) × η; "
            "split total by east/west orientation weights"
        ),
        "panels": {
            "string1_west": PANELS_STRING1_WEST,
            "string2_east": PANELS_STRING2_EAST,
            "total": PANELS_TOTAL,
        },
        "radiation_wm2": radiation_wm2,
        "is_day": is_day,
        "local_hour": round(local_hour, 1),
        "actual": {
            "string1_w": round(s1) if s1 is not None else None,
            "string2_w": round(s2) if s2 is not None else None,
            "total_w": round(total_actual) if total_actual is not None else None,
        },
        "expected": expected,
        "avg_pv_w": avg_pv,
        "performance_pct": performance_pct,
    }
