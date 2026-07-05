#!/usr/bin/env python3
"""Replace CAMERA_N_* block in config/.env (run on automation server as root)."""

import re
import sys
from pathlib import Path

ENV_PATH = Path("/opt/dell_server_management/config/.env")
CAMERAS_BLOCK = """
# Tapo Camera Configuration — phase 1 (4 cameras)
# Registry: docs/cameras/REGISTRY.md
CAMERA_HEALTH_INTERVAL_SEC=300
CAMERA_SNAPSHOT_INTERVAL_SEC=300
CAMERA_SNAPSHOT_MAX_WIDTH=480
CAMERA_SNAPSHOT_DIR=/opt/dell_server_management/data/camera-snapshots

CAMERA_1_NAME="Back Gate"
CAMERA_1_IP=192.168.2.34
CAMERA_1_PORT=2020
CAMERA_1_MODEL=C310
CAMERA_1_MAC=5C-E9-31-E0-21-93
CAMERA_1_USER=tinelc
CAMERA_1_PASS=tinelc
CAMERA_1_MQTT_PREFIX="garden/camera/backGate"

CAMERA_2_NAME="Casa Spate"
CAMERA_2_IP=192.168.2.32
CAMERA_2_PORT=2020
CAMERA_2_MODEL=C310
CAMERA_2_MAC=3C-52-A1-80-BA-81
CAMERA_2_USER=tinelc
CAMERA_2_PASS=tinelc
CAMERA_2_MQTT_PREFIX="garden/camera/casaSpate"

CAMERA_3_NAME="Front House"
CAMERA_3_IP=192.168.2.36
CAMERA_3_PORT=2020
CAMERA_3_MODEL=C310
CAMERA_3_MAC=5C-E9-31-41-4B-83
CAMERA_3_USER=tinelc
CAMERA_3_PASS=tinelc
CAMERA_3_MQTT_PREFIX="garden/camera/frontHouse"

CAMERA_4_NAME="Gazon Curte"
CAMERA_4_IP=192.168.2.38
CAMERA_4_PORT=2020
CAMERA_4_MODEL=TC65
CAMERA_4_MAC=A8-29-48-96-3A-E0
CAMERA_4_USER=tinelc
CAMERA_4_PASS=tinelc
CAMERA_4_MQTT_PREFIX="garden/camera/gazonCurte"

CAMERA_5_NAME="Gradina Lunca Cetatuii"
CAMERA_5_IP=192.168.2.37
CAMERA_5_PORT=2020
CAMERA_5_MODEL=C510W
CAMERA_5_MAC=E4-FA-C4-78-F1-C9
CAMERA_5_USER=tinelc
CAMERA_5_PASS=tinelc
CAMERA_5_MQTT_PREFIX="garden/camera/gradinaLunca"

CAMERA_6_NAME="Small Gate Entrance"
CAMERA_6_IP=192.168.2.10
CAMERA_6_PORT=2020
CAMERA_6_MODEL=C500
CAMERA_6_MAC=3C-52-A1-5A-28-61
CAMERA_6_USER=tinelc
CAMERA_6_PASS=tinelc
CAMERA_6_MQTT_PREFIX="garden/camera/smallGateEntrance"

CAMERA_7_NAME="Street View Camera"
CAMERA_7_IP=192.168.2.35
CAMERA_7_PORT=2020
CAMERA_7_MODEL=C310
CAMERA_7_MAC=5C-E9-31-E0-34-07
CAMERA_7_USER=tinelc
CAMERA_7_PASS=tinelc
CAMERA_7_MQTT_PREFIX="garden/camera/streetView"
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
            if (
                stripped.startswith("CAMERA_")
                or stripped.startswith("CAMERA_HEALTH_")
                or stripped.startswith("CAMERA_SNAPSHOT_")
                or stripped == ""
            ):
                continue
            skip = False
        if re.match(r"^CAMERA_\d+_", stripped):
            continue
        if stripped.startswith("CAMERA_HEALTH_") or stripped.startswith("CAMERA_SNAPSHOT_"):
            continue
        cleaned.append(line)

    text = "".join(cleaned).rstrip() + "\n\n" + CAMERAS_BLOCK
    ENV_PATH.write_text(text, encoding="utf-8")
    print(f"Updated camera block in {ENV_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
