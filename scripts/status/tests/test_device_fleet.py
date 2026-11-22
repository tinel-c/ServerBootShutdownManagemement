"""Unit tests for device_fleet flash decisions (no network)."""

from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path

STATUS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STATUS))

spec = importlib.util.spec_from_file_location("device_fleet", STATUS / "device_fleet.py")
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


def test_parse_status_payload_json():
    parsed = mod.parse_status_payload(
        '{"ip":"192.168.2.61","fw":"0.2.0","rssi":-55,"ota_port":3232}'
    )
    assert parsed["ip"] == "192.168.2.61"
    assert parsed["fw"] == "0.2.0"
    assert parsed["rssi"] == -55
    assert parsed["ota_port"] == 3232


def test_parse_status_payload_non_json():
    assert mod.parse_status_payload("online") == {}


def test_record_sighting_merges_fields():
    state: dict = {"devices": {}}
    mod.record_sighting(
        state,
        "PlatformIO_esp32-4ch-thyristor-board-illumination",
        '{"ip":"192.168.2.61","fw":"0.2.0","rssi":-40}',
        now=1000.0,
    )
    entry = state["devices"]["PlatformIO_esp32-4ch-thyristor-board-illumination"]
    assert entry["ip"] == "192.168.2.61"
    assert entry["fw"] == "0.2.0"
    assert entry["last_seen"] == 1000.0
    assert entry["ota_port"] == 3232


def test_is_online_fresh_and_stale():
    now = time.time()
    fresh = {"last_seen": now - 10}
    stale = {"last_seen": now - 200}
    assert mod.is_online(fresh, 90, now=now) is True
    assert mod.is_online(stale, 90, now=now) is False
    assert mod.is_online(None, 90, now=now) is False


def test_flash_decision_ok():
    cfg = {"flash": True, "timeout_sec": 90, "ota_port": 3232}
    entry = {"ip": "192.168.2.61", "last_seen": time.time(), "ota_port": 3232}
    ok, reason = mod.flash_decision(entry, cfg)
    assert ok is True
    assert reason == "ok"


def test_flash_decision_disabled():
    cfg = {"flash": False, "timeout_sec": 90}
    entry = {"ip": "192.168.2.61", "last_seen": time.time()}
    ok, reason = mod.flash_decision(entry, cfg)
    assert ok is False
    assert "disabled" in reason
    assert mod.flash_skip_exit(reason) == 0


def test_flash_skip_exit_soft_and_hard():
    assert mod.flash_skip_exit("device offline or sighting stale") == 0
    assert mod.flash_skip_exit("no IP in state (device must publish ip in status)") == 0
    assert mod.flash_skip_exit("unknown device") == 2


def test_flash_decision_stale():
    cfg = {"flash": True, "timeout_sec": 90}
    entry = {"ip": "192.168.2.61", "last_seen": time.time() - 500}
    ok, reason = mod.flash_decision(entry, cfg)
    assert ok is False
    assert "offline" in reason or "stale" in reason


def test_flash_decision_missing_ip():
    cfg = {"flash": True, "timeout_sec": 90}
    entry = {"last_seen": time.time()}
    ok, reason = mod.flash_decision(entry, cfg)
    assert ok is False
    assert "no IP" in reason


def test_load_registry_lists_thyristor():
    registry = mod.load_registry(STATUS / "device_fleet.yaml")
    ids = [d["id"] for d in registry["devices"]]
    assert "PlatformIO_esp32-4ch-thyristor-board-illumination" in ids
    thy = mod.device_by_id(registry, "PlatformIO_esp32-4ch-thyristor-board-illumination")
    assert thy["flash"] is True
    assert thy["status_topic"] == "illumination/4ch-thyristor/status"
