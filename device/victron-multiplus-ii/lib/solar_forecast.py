"""Open-Meteo solar irradiance forecast for automation (Lunca Cetătuui, Iași)."""

from __future__ import annotations

from datetime import datetime
from datetime import timezone as dt_timezone
from typing import Any

import requests

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
DEFAULT_LAT = 47.0966
DEFAULT_LON = 27.5632
DEFAULT_LOCATION = "Lunca Cetătuui, Iași, RO"
DEFAULT_TIMEZONE = "Europe/Bucharest"


def mj_to_kwh_m2(mj: float | None) -> float | None:
    if mj is None:
        return None
    return round(float(mj) / 3.6, 2)


def fetch_solar_forecast(
    latitude: float = DEFAULT_LAT,
    longitude: float = DEFAULT_LON,
    location_name: str = DEFAULT_LOCATION,
    timezone: str = DEFAULT_TIMEZONE,
    forecast_days: int = 3,
    hourly_hours: int = 48,
    timeout: float = 20.0,
) -> dict[str, Any]:
    """Fetch current irradiance and hourly/daily solar forecast from Open-Meteo."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "timezone": timezone,
        "forecast_days": forecast_days,
        "current": "shortwave_radiation,direct_radiation,diffuse_radiation,is_day",
        "hourly": "shortwave_radiation,direct_radiation,diffuse_radiation",
        "daily": "shortwave_radiation_sum,sunshine_duration",
    }
    response = requests.get(OPEN_METEO_URL, params=params, timeout=timeout)
    response.raise_for_status()
    data = response.json()

    fetched_at = datetime.now(dt_timezone.utc).isoformat()
    current_raw = data.get("current") or {}
    current = {
        "time": current_raw.get("time"),
        "shortwave_radiation_wm2": current_raw.get("shortwave_radiation"),
        "direct_radiation_wm2": current_raw.get("direct_radiation"),
        "diffuse_radiation_wm2": current_raw.get("diffuse_radiation"),
        "is_day": bool(current_raw.get("is_day")),
    }

    hourly_block = data.get("hourly") or {}
    times = hourly_block.get("time") or []
    hours: list[dict[str, Any]] = []
    for idx, time_str in enumerate(times[:hourly_hours]):
        hours.append(
            {
                "time": time_str,
                "shortwave_radiation_wm2": _at(hourly_block, "shortwave_radiation", idx),
                "direct_radiation_wm2": _at(hourly_block, "direct_radiation", idx),
                "diffuse_radiation_wm2": _at(hourly_block, "diffuse_radiation", idx),
            }
        )

    daily_block = data.get("daily") or {}
    daily_dates = daily_block.get("time") or []
    daily: list[dict[str, Any]] = []
    for idx, date_str in enumerate(daily_dates):
        sum_mj = _at(daily_block, "shortwave_radiation_sum", idx)
        sunshine = _at(daily_block, "sunshine_duration", idx)
        daily.append(
            {
                "date": date_str,
                "shortwave_radiation_sum_mj_m2": sum_mj,
                "shortwave_radiation_sum_kwh_m2": mj_to_kwh_m2(sum_mj),
                "sunshine_duration_s": sunshine,
            }
        )

    meta = {
        "timestamp": fetched_at,
        "source": "open-meteo",
        "attribution": "Weather data by Open-Meteo.com (CC BY 4.0)",
        "location": location_name,
        "latitude": latitude,
        "longitude": longitude,
        "timezone": timezone,
    }

    today_sum_mj = daily[0]["shortwave_radiation_sum_mj_m2"] if daily else None

    return {
        "meta": meta,
        "current": {**meta, **current},
        "hourly": {**meta, "hours": hours},
        "daily": {**meta, "days": daily},
        "scalars": {
            "radiation_wm2": current.get("shortwave_radiation_wm2"),
            "today_sum_kwh_m2": mj_to_kwh_m2(today_sum_mj),
            "is_day": current.get("is_day"),
        },
    }


def _at(block: dict, key: str, index: int) -> Any:
    values = block.get(key)
    if not values or index >= len(values):
        return None
    return values[index]
