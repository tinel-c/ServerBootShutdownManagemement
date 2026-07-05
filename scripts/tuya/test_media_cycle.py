#!/usr/bin/env python3
"""Full media server cycle: graceful SSH shutdown → Tuya boot → verify SSH up."""
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "utils"))

import paho.mqtt.client as mqtt
from config_loader import get_config
from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).resolve().parent.parent.parent / "config" / ".env")

HOST = os.getenv("MEDIA_SERVER_HOST", "192.168.2.185")
SSH_USER = os.getenv("MEDIA_SERVER_SSH_USER", "tinel")
SSH_KEY = os.getenv("MEDIA_SERVER_SSH_KEY", "")
BROKER = os.getenv("MQTT_BROKER_HOST", "127.0.0.1")
PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
MQTT_USER = os.getenv("MQTT_USERNAME", "")
MQTT_PASS = os.getenv("MQTT_PASSWORD", "")


def ssh_up() -> bool:
    cmd = [
        "ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5",
        "-i", SSH_KEY, f"{SSH_USER}@{HOST}", "echo up",
    ]
    try:
        return subprocess.run(cmd, capture_output=True, timeout=15).returncode == 0
    except Exception:
        return False


def wait_ssh(target_up: bool, timeout: int, interval: int = 5) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if ssh_up() == target_up:
            return True
        time.sleep(interval)
    return ssh_up() == target_up


def mqtt_command(topic: str, payload: dict, timeout: int = 180) -> dict:
    response = {}

    def on_message(client, userdata, msg):
        response["body"] = json.loads(msg.payload.decode())

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"media-cycle-{int(time.time())}")
    if MQTT_USER:
        client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)
    client.subscribe("media/server/response", qos=1)
    client.loop_start()
    client.publish(topic, json.dumps(payload), qos=1)
    deadline = time.time() + timeout
    while time.time() < deadline and "body" not in response:
        time.sleep(0.5)
    client.loop_stop()
    client.disconnect()
    return response.get("body", {})


def main() -> int:
    print("=== Media server full cycle test ===\n")

    if not ssh_up():
        print("FAIL: media server not reachable via SSH before test")
        return 1
    print("1. Pre-check: SSH reachable")

    req_shutdown = f"cycle-shutdown-{int(time.time())}"
    print("2. Sending graceful shutdown via MQTT...")
    shutdown_resp = mqtt_command(
        "media/server/command/shutdown",
        {
            "action": "shutdown",
            "type": "graceful",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "request_id": req_shutdown,
        },
        timeout=150,
    )
    print(f"   Response: {json.dumps(shutdown_resp)}")
    if not shutdown_resp.get("success"):
        print("FAIL: shutdown command rejected")
        return 1

    print("3. Waiting for SSH down (max 150s)...")
    if not wait_ssh(False, timeout=150, interval=5):
        print("FAIL: SSH still up after graceful shutdown window")
        return 1
    print("   SSH down confirmed")

    req_boot = f"cycle-boot-{int(time.time())}"
    print("4. Sending Tuya boot via MQTT...")
    boot_resp = mqtt_command(
        "media/server/command/boot",
        {
            "action": "boot",
            "method": "tuya_power",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "request_id": req_boot,
        },
        timeout=330,
    )
    print(f"   Response: {json.dumps(boot_resp)}")
    if not boot_resp.get("success"):
        print("FAIL: boot command failed")
        return 1

    print("5. Waiting for SSH up (max 300s)...")
    if not wait_ssh(True, timeout=300, interval=10):
        print("FAIL: SSH did not return after boot")
        return 1

    uptime = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-i", SSH_KEY, f"{SSH_USER}@{HOST}", "uptime"],
        capture_output=True, text=True, timeout=15,
    )
    print(f"6. SUCCESS — server back online: {uptime.stdout.strip()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
