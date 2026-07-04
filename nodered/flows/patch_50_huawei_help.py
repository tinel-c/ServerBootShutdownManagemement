#!/usr/bin/env python3
"""Patch 50-telegram-interface.json with Huawei help/commands."""

from __future__ import annotations

import json
from pathlib import Path

path = Path(__file__).resolve().parent / "50-telegram-interface.json"
data = json.loads(path.read_text(encoding="utf-8"))

for node in data:
    if node.get("id") != "func_handle_help":
        continue
    func = node["func"]
    old = (
        "    `❓ \\`/energy_help\\` - Victron energy help\\n\\n` +\n"
        "    `━━━━━━━━━━━━━━━━━━━━━━━━━━\\n\\n` +\n"
        "    `💡 *GARDEN LIGHTS*\\n` +"
    )
    new = (
        "    `❓ \\`/energy_help\\` - Victron energy help\\n\\n` +\n"
        "    `━━━━━━━━━━━━━━━━━━━━━━━━━━\\n\\n` +\n"
        "    `☀️ *HUAWEI SOLAR*\\n` +\n"
        "    `📊 \\`/huawei_status\\` - SUN2000 PV status\\n` +\n"
        "    `❓ \\`/huawei_help\\` - Huawei solar help\\n\\n` +\n"
        "    `━━━━━━━━━━━━━━━━━━━━━━━━━━\\n\\n` +\n"
        "    `💡 *GARDEN LIGHTS*\\n` +"
    )
    if old not in func:
        raise SystemExit("help anchor not found")
    func = func.replace(old, new, 1)
    old_kb = (
        "        [{ text: '⏹ Stop Load', callback_data: '/energy_stop' }, { text: '❓ Energy Help', callback_data: '/energy_help' }],\n"
        "        [{ text: '━━━━━ 💡 LIGHTS ━━━━━', callback_data: 'noop' }],"
    )
    new_kb = (
        "        [{ text: '⏹ Stop Load', callback_data: '/energy_stop' }, { text: '❓ Energy Help', callback_data: '/energy_help' }],\n"
        "        [{ text: '📊 Huawei Status', callback_data: '/huawei_status' }, { text: '❓ Huawei Help', callback_data: '/huawei_help' }],\n"
        "        [{ text: '━━━━━ 💡 LIGHTS ━━━━━', callback_data: 'noop' }],"
    )
    func = func.replace(old_kb, new_kb, 1)
    node["func"] = func
    break
else:
    raise SystemExit("func_handle_help not found")

for node in data:
    if node.get("id") != "func_handle_commands":
        continue
    func = node["func"]
    old = (
        "    `❓ \\`/energy_help\\` - Show Victron energy help\\n\\n` +\n"
        "    `━━━━━━━━━━━━━━━━━━━━━━━━━━\\n\\n` +\n"
        "    `💡 *GARDEN LIGHTS CONTROL*\\n\\n` +"
    )
    new = (
        "    `❓ \\`/energy_help\\` - Show Victron energy help\\n\\n` +\n"
        "    `━━━━━━━━━━━━━━━━━━━━━━━━━━\\n\\n` +\n"
        "    `☀️ *HUAWEI SOLAR (SUN2000)*\\n\\n` +\n"
        "    `*Status Commands:*\\n` +\n"
        "    `📊 \\`/huawei_status\\` - PV power, yield, strings\\n\\n` +\n"
        "    `*Help Commands:*\\n` +\n"
        "    `❓ \\`/huawei_help\\` - Show Huawei solar help\\n\\n` +\n"
        "    `━━━━━━━━━━━━━━━━━━━━━━━━━━\\n\\n` +\n"
        "    `💡 *GARDEN LIGHTS CONTROL*\\n\\n` +"
    )
    if old not in func:
        raise SystemExit("commands anchor not found")
    func = func.replace(old, new, 1)
    if "Huawei SUN2000 solar monitoring" not in func:
        func = func.replace(
            "    `✅ Victron energy & discretionary loads\\n` +",
            "    `✅ Victron energy & discretionary loads\\n` +\n"
            "    `✅ Huawei SUN2000 solar monitoring\\n` +",
            1,
        )
    node["func"] = func
    break
else:
    raise SystemExit("func_handle_commands not found")

for node in data:
    if node.get("id") == "link_out_authorized_telegram":
        links = node.get("links", [])
        if "link_in_822_huawei_energy_telegram" not in links:
            links.append("link_in_822_huawei_energy_telegram")
            node["links"] = links
        break

path.write_text(json.dumps(data, indent=4) + "\n", encoding="utf-8")
print(f"Patched {path}")
