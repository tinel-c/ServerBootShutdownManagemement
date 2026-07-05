#!/usr/bin/env python3
"""Quick verify media server Tuya via production config path."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "utils"))
from config_loader import get_config
from server_factory import get_all_server_managers

m = get_all_server_managers(get_config())["Media Server"]["manager"]
print("ssh:", m.is_reachable())
print("power:", m.get_power_status())
t = m.tuya._read_status()
print("tuya_ok:", isinstance(t, dict) and "dps" in t)
if isinstance(t, dict) and "dps" in t:
    print("dps:", json.dumps(t["dps"]))
