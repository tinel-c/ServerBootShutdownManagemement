"""Command lists for the Device Fleet detail pane (no MQTT, no Tk)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

CLIENT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CLIENT))

from device_commands import commands_for, format_status, status_topics  # noqa: E402


def _labels(row):
    return [label for label, _topic, _payload in commands_for(row)]


def test_thyristor_has_each_channel_and_all_off():
    row = {"id": "PlatformIO_esp32-4ch-thyristor-board-illumination", "kind": "firmware"}
    commands = commands_for(row)
    labels = [label for label, _topic, _payload in commands]
    assert labels[:4] == ["L1 on", "L1 off", "L2 on", "L2 off"]
    assert labels[-1] == "All off"
    _label, topic, payload = commands[0]
    assert topic == "illumination/4ch-thyristor/command/set"
    assert json.loads(payload) == {"channel": 1, "state": "on"}
    assert json.loads(commands[-1][2]) == {"channel": 0, "state": "off"}


def test_main_gate_open_is_the_coil_safe_pulse():
    row = {"id": "PlatformIO_ESP8266_Main_Entry", "kind": "firmware"}
    by_label = {label: (topic, payload) for label, topic, payload in commands_for(row)}
    assert by_label["Open gate"] == ("MainGate/CMD/Relay2", "ON")
    assert by_label["Actuator on"][0] == "MainGate/CMD/Relay3"


def test_aquarium_and_pump_commands():
    light = commands_for({"id": "tasmota/sursaAcvariu", "kind": "tasmota", "topic": "sursaAcvariu"})
    assert ("Light toggle", "cmnd/sursaAcvariu/POWER", "TOGGLE") in light
    pump = _labels({"id": "tasmota/pompaApa", "kind": "tasmota", "topic": "pompaApa"})
    assert "Start pump on" in pump
    assert "Drain off" in pump
    assert "Trench 2 on" in pump


def test_garden_lights_and_irrigation_cover_every_output():
    lights = commands_for(
        {"id": "tasmota/GardenAutomationLights", "kind": "tasmota", "topic": "GardenAutomationLights"}
    )
    assert ("Garden 12 off", "GardenAutomationLights/CMD/Relay12", "OFF") in lights
    zones = _labels({"id": "tasmota/IrigationSystem", "kind": "tasmota", "topic": "IrigationSystem"})
    assert "24 V supply on" in zones
    assert "I12 off" in zones


def test_unknown_tasmota_gets_a_single_relay():
    row = {"id": "tasmota/new-board", "kind": "tasmota", "topic": "new-board"}
    labels = _labels(row)
    assert "Power on" in labels
    assert "Ask status" in labels


def test_status_text_includes_fleet_fields_and_live_topics():
    row = {
        "id": "tasmota/sursaAcvariu",
        "name": "Aquarium Light",
        "online": True,
        "fw": "15.0.1",
        "ip": "192.168.2.137",
        "age_s": 4,
        "rssi": None,
        "ota_port": "—",
        "last_payload": "Online",
    }
    text = format_status(row, {"stat/sursaAcvariu/POWER": "ON"})
    assert "Aquarium Light" in text
    assert "Online: yes" in text
    assert "Fleet status: Online" in text
    assert "stat/sursaAcvariu/POWER: ON" in text
    assert "tele/sursaAcvariu/#" in status_topics(row)


def test_sms_command_is_the_dialog_marker():
    row = {"id": "PlatformIO_esp32-sms-gateway", "kind": "firmware"}
    assert commands_for(row) == [("Send SMS…", "sms/gateway/command/send", "")]
    assert "sms/gateway/watchdog/status" in status_topics(row)
