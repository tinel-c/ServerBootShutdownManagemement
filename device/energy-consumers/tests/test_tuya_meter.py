"""Tests for Tuya meter status parsing."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.modules.setdefault("tinytuya", MagicMock())

LIB = Path(__file__).resolve().parents[1] / "lib"
sys.path.insert(0, str(LIB))

from consumer_schema import ConsumerStatus  # noqa: E402
from tuya_meter import apply_metric_cache, parse_dps_status, phase_stale_after_s  # noqa: E402


def test_lan_err_with_cloud_phase_marks_online_degraded():
    consumer = {
        "id": "breaker-inside",
        "name": "House consumption",
        "dps": {"phase_a": "6"},
    }
    creds = {"id": "bf05a4a80c7e10134dx5gp", "ip": "192.168.2.214"}
    raw = {"Err": "914", "Error": "Check device key or version"}

    cloud = {"power_w": 902.0, "voltage_v": 223.8, "current_a": 4.825}
    with patch("tuya_meter.fetch_cloud_phase_a", return_value=cloud):
        status = parse_dps_status(consumer, raw, creds)

    assert status.online is True
    assert status.power_w == 902.0
    assert status.extra["phase_source"] == "tongou_cloud"
    assert status.extra["lan_degraded"] is True
    assert status.extra["lan_err"] == "914"


def test_lan_err_without_cloud_phase_stays_offline():
    consumer = {"id": "breaker-inside", "dps": {"phase_a": "6"}}
    creds = {"id": "bf05a4a80c7e10134dx5gp", "ip": "192.168.2.214"}
    raw = {"Err": "914"}

    with patch("tuya_meter.fetch_cloud_phase_a", return_value=None):
        status = parse_dps_status(consumer, raw, creds)

    assert status.online is False
    assert "lan_degraded" not in status.extra


def test_lan_dps_without_phase_stays_online():
    consumer = {"id": "breaker-outside", "dps": {"phase_a": "6", "switch": "16"}}
    creds = {"id": "bfb1f58994ced1e2fajvee", "ip": "192.168.2.112"}
    raw = {"dps": {"16": True, "103": "Closed", "110": "Normal"}}

    with patch("tuya_meter.fetch_cloud_phase_a", return_value=None) as fetch_cloud:
        status = parse_dps_status(consumer, raw, creds)

    fetch_cloud.assert_called_once()
    assert status.online is True
    assert status.extra.get("switch_on") is True


def test_apply_metric_cache_reuses_recent_phase_metrics():
    consumer = {"id": "breaker-inside", "dps": {"phase_a": "6"}, "phase_stale_after_s": 600}
    previous = ConsumerStatus(
        consumer_id="breaker-inside",
        name="House consumption",
        power_w=790.0,
        voltage_v=221.8,
        current_a=4.3,
        online=True,
        source="tuya_meter",
        extra={"phase_source": "tongou_cloud"},
    )
    now = time.time()
    current = ConsumerStatus(
        consumer_id="breaker-inside",
        name="House consumption",
        online=True,
        source="tuya_meter",
        extra={"phase_source": "tongou_cloud"},
    )
    cached, _ = apply_metric_cache(
        consumer,
        current,
        previous=previous,
        previous_metrics_ts=now - 120,
        now=now,
    )
    assert cached.power_w == 790.0
    assert cached.extra["metrics_cached"] is True
    assert cached.extra["metrics_age_s"] == 120


def test_phase_stale_default_for_tongou_breakers():
    consumer = {"dps": {"phase_a": "6"}, "poll_interval_s": 30}
    assert phase_stale_after_s(consumer) == 600.0
