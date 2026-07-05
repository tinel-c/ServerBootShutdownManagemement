#!/usr/bin/env python3
"""Replace CAMERA_N_* block in config/.env (run on automation server as root)."""

import re
import sys
from pathlib import Path

ENV_PATH = Path("/opt/dell_server_management/config/.env")
CAMERAS_BLOCK = """
# Tapo Camera Configuration (updated by apply_cameras_env.py)
CAMERA_1_NAME="Interior curte"
CAMERA_1_IP=192.168.2.37
CAMERA_1_PORT=2020
CAMERA_1_USER=tinelc
CAMERA_1_PASS=tinelc
CAMERA_1_MQTT_PREFIX="garden/camera/interior"

CAMERA_2_NAME="Poarta mica"
CAMERA_2_IP=192.168.2.10
CAMERA_2_PORT=2020
CAMERA_2_USER=tinelc
CAMERA_2_PASS=tinelc
CAMERA_2_MQTT_PREFIX="garden/camera/smallGate"

CAMERA_3_NAME="Spate casa"
CAMERA_3_IP=192.168.2.32
CAMERA_3_PORT=2020
CAMERA_3_USER=tinelc
CAMERA_3_PASS=tinelc
CAMERA_3_MQTT_PREFIX="garden/camera/backyard"

CAMERA_4_NAME="Poarta glisanta 2"
CAMERA_4_IP=192.168.2.34
CAMERA_4_PORT=2020
CAMERA_4_USER=tinelc
CAMERA_4_PASS=tinelc
CAMERA_4_MQTT_PREFIX="garden/camera/gate2"

CAMERA_5_NAME="Fata casa"
CAMERA_5_IP=192.168.2.36
CAMERA_5_PORT=2020
CAMERA_5_USER=tinelc
CAMERA_5_PASS=tinelc
CAMERA_5_MQTT_PREFIX="garden/camera/fataCasa"

CAMERA_6_NAME="Curte strada"
CAMERA_6_IP=192.168.2.59
CAMERA_6_PORT=2020
CAMERA_6_USER=tinelc
CAMERA_6_PASS=tinelc
CAMERA_6_MQTT_PREFIX="garden/camera/strada"

CAMERA_7_NAME="Poarta glisanta 1"
CAMERA_7_IP=192.168.2.34
CAMERA_7_PORT=2020
CAMERA_7_USER=tinelc
CAMERA_7_PASS=tinelc
CAMERA_7_MQTT_PREFIX="garden/camera/gate1"
""".strip() + "\n"


def main() -> int:
    if not ENV_PATH.exists():
        print(f"Missing {ENV_PATH}", file=sys.stderr)
        return 1

    text = ENV_PATH.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    cleaned = []
    skip = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# Tapo Camera Configuration"):
            skip = True
            continue
        if skip:
            if stripped.startswith("CAMERA_") or stripped == "":
                continue
            skip = False
        if re.match(r"^CAMERA_\d+_", stripped):
            continue
        cleaned.append(line)

    text = "".join(cleaned).rstrip() + "\n\n" + CAMERAS_BLOCK
    ENV_PATH.write_text(text, encoding="utf-8")
    print(f"Updated camera block in {ENV_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
