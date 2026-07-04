#!/usr/bin/env python3
"""Append Huawei watchdog nodes to 90-device-watchdog.json."""

from __future__ import annotations

import json
from pathlib import Path

path = Path(__file__).resolve().parent / "90-device-watchdog.json"
data = json.loads(path.read_text(encoding="utf-8"))

if any(n.get("id") == "watchdog_huawei_in" for n in data):
    print("Huawei watchdog already present")
    raise SystemExit(0)

# Update top comment monitored devices list
for node in data:
    if node.get("type") == "comment" and "Device Watchdog" in node.get("name", ""):
        info = node.get("info", "")
        if "Huawei Solar" not in info:
            insert = (
                "\n\n6. **Huawei Solar** (SUN2000)\n"
                "   - Topic: energy/huawei/status\n"
                "   - Timeout: 2 minutes\n"
                "   - Alert: \"Huawei Solar online/offline\""
            )
            node["info"] = info.replace(
                "5. **Victron Energy**",
                "5. **Victron Energy**",
            ).replace(
                "   - Alert: \"Victron Energy online/offline\"",
                "   - Alert: \"Victron Energy online/offline\"" + insert,
            )
        break

huawei_nodes = [
    {
        "id": "watchdog_huawei_comment",
        "type": "comment",
        "z": "8becda4e1ec6a8b9",
        "name": "Huawei Solar Watchdog (2 min timeout)",
        "info": "Monitors energy/huawei/status (huawei-mqtt-publisher.service)\nPoll interval: ~10 s · Timeout: 2 minutes",
        "x": 350,
        "y": 1980,
        "wires": [],
    },
    {
        "id": "watchdog_huawei_in",
        "type": "mqtt in",
        "z": "8becda4e1ec6a8b9",
        "name": "Huawei Status Heartbeat",
        "topic": "energy/huawei/status",
        "qos": "1",
        "datatype": "json",
        "broker": "mqtt_broker_local",
        "nl": False,
        "rap": True,
        "rh": 0,
        "inputs": 0,
        "x": 310,
        "y": 2040,
        "wires": [["watchdog_huawei_validate"]],
    },
    {
        "id": "watchdog_huawei_validate",
        "type": "function",
        "z": "8becda4e1ec6a8b9",
        "name": "Validate Huawei status",
        "func": "let data = msg.payload;\nif (typeof data === 'string') {\n    try { data = JSON.parse(data); } catch (e) { return null; }\n}\nif (!data || typeof data !== 'object' || !data.timestamp) return null;\nflow.set('watchdog_huawei_last', data);\nreturn msg;",
        "outputs": 1,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "libs": [],
        "x": 550,
        "y": 2040,
        "wires": [["watchdog_huawei_trigger"]],
    },
    {
        "id": "watchdog_huawei_trigger",
        "type": "trigger",
        "z": "8becda4e1ec6a8b9",
        "name": "2 min timeout",
        "op1": "1",
        "op2": "0",
        "op1type": "str",
        "op2type": "str",
        "duration": "2",
        "extend": True,
        "overrideDelay": False,
        "units": "min",
        "reset": "",
        "bytopic": "all",
        "topic": "topic",
        "outputs": 1,
        "x": 770,
        "y": 2040,
        "wires": [["watchdog_huawei_switch"]],
    },
    {
        "id": "watchdog_huawei_switch",
        "type": "switch",
        "z": "8becda4e1ec6a8b9",
        "name": "Online/Offline",
        "property": "payload",
        "propertyType": "msg",
        "rules": [
            {"t": "eq", "v": "1", "vt": "str"},
            {"t": "eq", "v": "0", "vt": "str"},
        ],
        "checkall": "true",
        "repair": False,
        "outputs": 2,
        "x": 990,
        "y": 2040,
        "wires": [
            ["watchdog_huawei_filter_online"],
            ["watchdog_huawei_filter_offline"],
        ],
    },
    {
        "id": "watchdog_huawei_online",
        "type": "function",
        "z": "8becda4e1ec6a8b9",
        "name": "Huawei solar online",
        "func": "const d = flow.get('watchdog_huawei_last') || {};\nconst dev = d.device || {};\nconst inv = d.inverter || {};\nlet content = '🟢 *Huawei Solar ONLINE*\\n\\n';\nif (dev.model) content += `Model: ${dev.model}\\n`;\nif (inv.active_power_w != null) content += `Active: ${Math.round(Number(inv.active_power_w))} W\\n`;\nif (inv.daily_yield_kwh != null) content += `Today: ${inv.daily_yield_kwh} kWh\\n`;\ncontent += `Topic: energy/huawei/status`;\nmsg.payload = { chatId: 991635368, type: 'message', content, parse_mode: 'Markdown' };\nreturn msg;",
        "outputs": 1,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "libs": [],
        "x": 1520,
        "y": 2000,
        "wires": [["watchdog_telegram_sender"]],
    },
    {
        "id": "watchdog_huawei_offline",
        "type": "change",
        "z": "8becda4e1ec6a8b9",
        "name": "Huawei solar offline",
        "rules": [
            {"t": "set", "p": "payload", "pt": "msg", "to": "{}", "tot": "json"},
            {"t": "set", "p": "payload.type", "pt": "msg", "to": "message", "tot": "str"},
            {
                "t": "set",
                "p": "payload.content",
                "pt": "msg",
                "to": "🔴 Huawei Solar OFFLINE\n\nNo energy/huawei/status for 2 min.\nCheck huawei-mqtt-publisher.service and USB WiFi to inverter AP.",
                "tot": "str",
            },
            {"t": "set", "p": "payload.chatId", "pt": "msg", "to": "991635368", "tot": "num"},
        ],
        "action": "",
        "property": "",
        "from": "",
        "to": "",
        "reg": False,
        "x": 1580,
        "y": 2100,
        "wires": [["watchdog_telegram_sender"]],
    },
    {
        "id": "watchdog_huawei_filter_online",
        "type": "function",
        "z": "8becda4e1ec6a8b9",
        "name": "Notify only on state change",
        "func": "const key = 'watchdog_state_watchdog_huawei';\nconst prev = flow.get(key);\nconst next = 'online';\nif (prev === next) return null;\nflow.set(key, next);\nreturn msg;",
        "outputs": 1,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "libs": [],
        "x": 1220,
        "y": 2000,
        "wires": [["watchdog_huawei_online"]],
    },
    {
        "id": "watchdog_huawei_filter_offline",
        "type": "function",
        "z": "8becda4e1ec6a8b9",
        "name": "Notify only on state change",
        "func": "const key = 'watchdog_state_watchdog_huawei';\nconst prev = flow.get(key);\nconst next = 'offline';\nif (prev === next) return null;\nflow.set(key, next);\nreturn msg;",
        "outputs": 1,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "libs": [],
        "x": 1220,
        "y": 2100,
        "wires": [["watchdog_huawei_offline"]],
    },
]

data.extend(huawei_nodes)
path.write_text(json.dumps(data, indent=4) + "\n", encoding="utf-8")
print(f"Patched {path} (+{len(huawei_nodes)} nodes)")
