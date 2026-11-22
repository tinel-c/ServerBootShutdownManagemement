"""Commands and status lines for one Device Fleet row.

Buttons publish the same MQTT topics the dashboards already use.
A device that is not listed here gets the single-relay Tasmota commands
when it is a Tasmota board, and no buttons when it is unknown firmware.
"""

from __future__ import annotations

import json
from typing import Dict, List, Sequence, Tuple

Command = Tuple[str, str, str]  # label, topic, payload. payload "" opens the SMS dialog.


def _switch(label: str, topic: str, on: str = "ON", off: str = "OFF") -> List[Command]:
    return [(f"{label} on", topic, on), (f"{label} off", topic, off)]


def _power(topic_name: str, index: int, label: str) -> List[Command]:
    return _switch(label, f"cmnd/{topic_name}/POWER{index}")


def _power_single(topic_name: str, label: str) -> List[Command]:
    topic = f"cmnd/{topic_name}/POWER"
    return _switch(label, topic) + [(f"{label} toggle", topic, "TOGGLE")]


def _thyristor(channel: int, state: str, label: str) -> Command:
    payload = json.dumps({"channel": channel, "state": state}, separators=(",", ":"))
    return (label, "illumination/4ch-thyristor/command/set", payload)


def _irrigation() -> List[Command]:
    zones = [
        (1, "24 V supply"),
        (2, "I1"),
        (3, "I2"),
        (4, "I3"),
        (5, "I4"),
        (10, "I5"),
        (11, "I6"),
        (12, "I7"),
        (13, "I8"),
        (14, "I9"),
        (15, "I10"),
        (16, "I11"),
        (17, "I12"),
    ]
    commands: List[Command] = []
    for index, name in zones:
        commands.extend(_power("IrigationSystem", index, name))
    return commands


def _garden_lights() -> List[Command]:
    commands: List[Command] = []
    for index in range(1, 13):
        commands.extend(_switch(f"Garden {index}", f"GardenAutomationLights/CMD/Relay{index}"))
    return commands


def _gate_relays(prefix: str) -> List[Command]:
    """Main-gate firmware. Relay 2 ON is the coil-safe open pulse."""
    commands = _switch("Relay 1", f"{prefix}/CMD/Relay1")
    commands.append(("Open gate", f"{prefix}/CMD/Relay2", "ON"))
    commands.append(("Relay 2 off", f"{prefix}/CMD/Relay2", "OFF"))
    commands.extend(_switch("Actuator", f"{prefix}/CMD/Relay3"))
    commands.extend(_switch("Relay 4", f"{prefix}/CMD/Relay4"))
    return commands


def _sliding_gate(topic_name: str) -> List[Command]:
    names = [(1, "Open"), (2, "Close"), (3, "Trigger"), (4, "Alt open")]
    commands: List[Command] = []
    for index, label in names:
        commands.extend(_power(topic_name, index, label))
    return commands


def _pump() -> List[Command]:
    names = [(1, "Start pump"), (2, "Drain"), (3, "Trench 1"), (4, "Trench 2")]
    commands: List[Command] = []
    for index, label in names:
        commands.extend(_power("pompaApa", index, label))
    return commands


def _tasmota_topic(row: Dict[str, str]) -> str:
    topic = str(row.get("topic") or "")
    if topic:
        return topic
    device_id = str(row.get("id") or "")
    if device_id.startswith("tasmota/"):
        return device_id.split("/", 1)[1]
    return ""


def commands_for(row: Dict[str, Any]) -> List[Command]:
    """Every button for this device: (label, mqtt topic, payload)."""
    device_id = str(row.get("id") or "")
    kind = str(row.get("kind") or "")
    topic_name = _tasmota_topic(row)

    if device_id == "PlatformIO_esp32-4ch-thyristor-board-illumination":
        commands = []
        for channel in range(1, 5):
            commands.append(_thyristor(channel, "on", f"L{channel} on"))
            commands.append(_thyristor(channel, "off", f"L{channel} off"))
        commands.append(_thyristor(0, "off", "All off"))
        return commands

    if device_id == "PlatformIO_ESP8266_Main_Entry":
        return _gate_relays("MainGate")

    if device_id == "PlatformIO_esp32-sms-gateway":
        return [("Send SMS…", "sms/gateway/command/send", "")]

    specific = {
        "tasmota/sursaAcvariu": _power_single("sursaAcvariu", "Light"),
        "tasmota/sonoffPower320D_afara": _power_single("sonoffPower320D_afara", "Power"),
        "tasmota/sonoffAtelier": _power_single("sonoffAtelier", "Power"),
        "tasmota/lumina1sufragerie": _power_single("lumina1sufragerie", "Light"),
        "tasmota/lumina2sufragerie": _power_single("lumina2sufragerie", "Light"),
        "tasmota/automatizare_poarta": _sliding_gate("automatizare_poarta"),
        "tasmota/LuncaCetatuiiSlidingGateAutomation": _sliding_gate(
            "LuncaCetatuiiSlidingGateAutomation"
        ),
        "tasmota/portaSecundara": _sliding_gate("portaSecundara"),
        "tasmota/MainGate": _sliding_gate("MainGate"),
        "tasmota/pompaApa": _pump(),
        "tasmota/frontHousePower": [
            command
            for index in range(1, 5)
            for command in _power("frontHousePower", index, f"Front {index}")
        ],
        "tasmota/GardenAutomationLights": _garden_lights(),
        "tasmota/IrigationSystem": _irrigation(),
    }
    if device_id in specific:
        return list(specific[device_id])
    if kind == "tasmota" and topic_name:
        return _power_single(topic_name, "Power") + [
            ("Ask status", f"cmnd/{topic_name}/Status", "0")
        ]
    return []


def status_topics(row: Dict[str, Any]) -> List[str]:
    """MQTT subscriptions that carry this device's status fields."""
    device_id = str(row.get("id") or "")
    topic_name = _tasmota_topic(row)
    if device_id == "PlatformIO_esp32-4ch-thyristor-board-illumination":
        return ["illumination/4ch-thyristor/status"]
    if device_id == "PlatformIO_ESP8266_Main_Entry":
        return ["gate/main/status", "MainGate/STAT/#"]
    if device_id == "PlatformIO_esp32-sms-gateway":
        return ["sms/gateway/status", "sms/gateway/watchdog/status"]
    if device_id == "tasmota/GardenAutomationLights":
        return ["GardenAutomationLights/STAT/#", "tele/GardenAutomationLights/#"]
    if topic_name:
        return [f"tele/{topic_name}/#", f"stat/{topic_name}/#"]
    status_topic = str(row.get("status_topic") or "")
    return [status_topic] if status_topic else []


def format_status(row: Dict[str, Any], live: Dict[str, str]) -> str:
    """Plain-text status block for the selected device."""
    lines = [
        f"{row.get('name') or row.get('id')}  ({row.get('id')})",
        f"Online: {'yes' if row.get('online') else 'no'}",
        f"Firmware: {row.get('fw') or '—'}",
        f"IP: {row.get('ip') or '—'}",
        f"Age: {row.get('age_s')}s" if row.get("age_s") is not None else "Age: —",
    ]
    if row.get("rssi") is not None:
        lines.append(f"RSSI: {row.get('rssi')}")
    if row.get("ota_port") not in (None, "—", ""):
        lines.append(f"OTA port: {row.get('ota_port')}")
    payload = str(row.get("last_payload") or "").strip()
    if payload:
        lines.append("Fleet status: " + _pretty(payload))
    for topic in sorted(live):
        lines.append(f"{topic}: {_pretty(live[topic])}")
    return "\n".join(lines)


def _pretty(payload: str) -> str:
    text = payload.strip()
    if text.startswith("{") or text.startswith("["):
        try:
            return json.dumps(json.loads(text), ensure_ascii=False, separators=(",", ":"))
        except json.JSONDecodeError:
            return text
    return text


def command_labels(commands: Sequence[Command]) -> List[str]:
    return [label for label, _topic, _payload in commands]
