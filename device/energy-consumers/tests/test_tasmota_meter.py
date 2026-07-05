"""Tests for Tasmota ENERGY parsing."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

from tasmota_meter import parse_power_payload, parse_sensor_status, switch_command_payload


CONSUMER = {
    "id": "sonoff-powr316d",
    "name": "Test POWR316D",
    "type": "tasmota_meter",
    "tasmota_topic": "sonoffPowR316D",
    "tags": ["test"],
}


def test_parse_sensor_energy():
    payload = {
        "Time": "2026-07-05T11:00:00",
        "ENERGY": {
            "Total": 123.456,
            "Yesterday": 1.2,
            "Today": 0.5,
            "Power": 2088,
            "Voltage": 238.3,
            "Current": 8.76,
            "Factor": 0.99,
        },
    }
    status = parse_sensor_status(CONSUMER, payload, switch_on=True)
    assert status.power_w == 2088.0
    assert status.energy_kwh == 123.456
    assert status.voltage_v == 238.3
    assert status.current_a == 8.76
    assert status.online is True
    assert status.extra["switch_on"] is True
    assert status.extra["phase_source"] == "tasmota_sensor"


def test_parse_sensor_json_string():
    payload = json.dumps(
        {
            "ENERGY": {
                "Total": 10.0,
                "Power": 100,
                "Voltage": 230,
                "Current": 0.43,
            }
        }
    )
    status = parse_sensor_status(CONSUMER, payload)
    assert status.power_w == 100.0
    assert status.voltage_v == 230.0


def test_parse_power_stat():
    assert parse_power_payload("ON") is True
    assert parse_power_payload("OFF") is False
    assert parse_power_payload('{"POWER":"ON"}') is True


def test_switch_command_payload():
    assert switch_command_payload("on") == "ON"
    assert switch_command_payload("off") == "OFF"
    assert switch_command_payload("toggle") == "TOGGLE"
