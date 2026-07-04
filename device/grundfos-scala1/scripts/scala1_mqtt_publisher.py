#!/usr/bin/env python3
"""Grundfos SCALA1 BLE to MQTT publisher."""

from __future__ import annotations

import json
import os
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEVICE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "utils"))
sys.path.insert(0, str(DEVICE_ROOT / "lib"))

from logger import get_logger  # noqa: E402
from mqtt_client import MQTTClientWrapper  # noqa: E402
from scala1_ble import (  # noqa: E402
    Scala1BleClient,
    flatten_status,
    load_scala1_config,
    metrics_to_status,
    run_async,
)

logger = get_logger(__name__)


def load_mqtt_settings() -> dict:
    load_dotenv(REPO_ROOT / "config" / ".env")
    load_dotenv(DEVICE_ROOT / "config" / ".env", override=True)
    return {
        "host": os.getenv("MQTT_BROKER_HOST", "localhost"),
        "port": int(os.getenv("MQTT_BROKER_PORT", "1883")),
        "username": os.getenv("MQTT_USERNAME") or None,
        "password": os.getenv("MQTT_PASSWORD") or None,
        "prefix": os.getenv("SCALA1_MQTT_PREFIX", "water/grundfos/scala1").rstrip("/"),
        "interval": int(os.getenv("SCALA1_POLL_INTERVAL", "15")),
        "qos": int(os.getenv("SCALA1_MQTT_QOS", "1")),
        "device_name": os.getenv("SCALA1_DEVICE_NAME", "scala1-booster"),
    }


class Scala1MqttPublisher:
    def __init__(self, ble_config, mqtt_settings: dict):
        self.ble_config = ble_config
        self.mqtt_settings = mqtt_settings
        self.ble = Scala1BleClient(ble_config)
        self.running = False
        self.mqtt = MQTTClientWrapper(
            broker_host=mqtt_settings["host"],
            broker_port=mqtt_settings["port"],
            client_id="grundfos_scala1_mqtt_publisher",
            username=mqtt_settings["username"],
            password=mqtt_settings["password"],
            qos=mqtt_settings["qos"],
        )

    def publish_status(self, status: dict) -> None:
        topics = flatten_status(self.mqtt_settings["prefix"], status)
        for topic, payload in topics.items():
            if not self.mqtt.publish(topic, payload, retain=False):
                logger.warning("Failed to publish %s", topic)

    def run_once(self) -> bool:
        try:
            metrics = run_async(self.ble.read_metrics())
        except Exception as exc:
            logger.error("BLE read failed: %s", exc)
            return False

        status = metrics_to_status(metrics, self.mqtt_settings["device_name"])
        self.publish_status(status)
        logger.info(
            "Published SCALA1: running=%s pressure=%s flow=%s alarm=%s",
            status.get("running"),
            status.get("pressure_bar"),
            status.get("flow_m3h"),
            status.get("alarm_code"),
        )
        return True

    def _handle_command(self, topic: str, payload: str) -> None:
        try:
            data = json.loads(payload) if payload.strip().startswith("{") else {"action": payload.strip()}
        except json.JSONDecodeError:
            data = {"action": payload.strip()}
        action = (data.get("action") or "").lower()
        if action not in ("start", "stop", "reset_alarm"):
            logger.warning("Unknown command on %s: %s", topic, payload)
            return
        try:
            run_async(self.ble.send_command(action))
            logger.info("BLE command sent: %s", action)
            response = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": action,
                "success": True,
            }
            self.mqtt.publish(f"{self.mqtt_settings['prefix']}/response", response)
        except NotImplementedError as exc:
            logger.warning("Command not configured: %s", exc)
            self.mqtt.publish(
                f"{self.mqtt_settings['prefix']}/response",
                {"action": action, "success": False, "error": str(exc)},
            )
        except Exception as exc:
            logger.error("Command failed: %s", exc)
            self.mqtt.publish(
                f"{self.mqtt_settings['prefix']}/response",
                {"action": action, "success": False, "error": str(exc)},
            )

    def start(self) -> bool:
        if not self.ble_config.ble_address:
            logger.error("SCALA1_BLE_ADDRESS not configured")
            return False
        if not self.mqtt.connect():
            logger.error("MQTT connect failed")
            return False

        cmd_topic = f"{self.mqtt_settings['prefix']}/command"
        self.mqtt.subscribe(cmd_topic, self._handle_command)

        interval = self.mqtt_settings["interval"]
        logger.info(
            "SCALA1 publisher started: ble=%s interval=%ss prefix=%s",
            self.ble_config.ble_address,
            interval,
            self.mqtt_settings["prefix"],
        )
        self.running = True
        while self.running:
            try:
                self.run_once()
            except Exception as exc:
                logger.error("Poll cycle failed: %s", exc)
            time.sleep(interval)
        return True

    def stop(self) -> None:
        self.running = False
        self.mqtt.disconnect()


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Grundfos SCALA1 BLE to MQTT publisher")
    parser.add_argument("--once", action="store_true", help="Poll once and exit")
    args = parser.parse_args()

    ble_config = load_scala1_config(DEVICE_ROOT / "config")
    mqtt_settings = load_mqtt_settings()
    publisher = Scala1MqttPublisher(ble_config, mqtt_settings)

    if args.once:
        if not publisher.mqtt.connect():
            return 1
        ok = publisher.run_once()
        publisher.stop()
        return 0 if ok else 1

    def handle_signal(signum, _frame):
        logger.info("Signal %s received, stopping", signum)
        publisher.stop()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    if not publisher.start():
        return 1
    publisher.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
