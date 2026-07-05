"""Tests for east/west PV forecast model."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

from pv_forecast_model import (
    build_pv_forecast,
    estimate_pv_power_w,
    orientation_weights,
)


def test_orientation_morning_favours_east():
    w_east, w_west = orientation_weights(8.0)
    assert w_east > w_west
    assert w_east > 0.5


def test_orientation_afternoon_favours_west():
    w_east, w_west = orientation_weights(16.0)
    assert w_west > w_east
    assert w_west > 0.5


def test_estimate_splits_strings_by_orientation():
    est = estimate_pv_power_w(800, 6000, 9.0)
    assert est["string2_w"] > est["string1_w"]
    assert est["total_w"] > 0
    assert est["string1_w"] + est["string2_w"] == est["total_w"]


def test_build_pv_forecast_performance():
    payload = build_pv_forecast(
        radiation_wm2=900,
        rated_power_w=6000,
        local_hour=10.0,
        string1_voltage_v=300,
        string1_current_a=2.0,
        string2_voltage_v=280,
        string2_current_a=1.0,
        history=[{"dc": 1200}, {"dc": 1400}],
        is_day=True,
    )
    assert payload["actual"]["total_w"] == 880
    assert payload["avg_pv_w"] == 1300
    assert payload["performance_pct"] is not None
