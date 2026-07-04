#!/usr/bin/env python3
"""Huawei SUN2000 Modbus to MQTT publisher."""

from __future__ import annotations

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

from huawei_modbus import HuaweiConfig, HuaweiModbusReader, load_huawei_config  # noqa: E402
from logger import get_logger  # noqa: E402
from mqtt_client import MQTTClientWrapper  # noqa: E402

logger = get_logger(__name__)


def load_mqtt_settings() -> dict:
    load_dotenv(REPO_ROOT / "config" / ".env")
    load_dotenv(DEVICE_ROOT / "config" / ".env", override=True)
    return {
        "host": os.getenv("MQTT_BROKER_HOST", "localhost"),
        "port": int(os.getenv("MQTT_BROKER_PORT", "1883")),
        "username": os.getenv("MQTT_USERNAME") or None,
        "password": os.getenv("MQTT_PASSWORD") or None,
        "prefix": os.getenv("HUAWEI_MQTT_PREFIX", "energy/huawei").rstrip("/"),
        "interval": int(os.getenv("HUAWEI_MODBUS_POLL_INTERVAL", "10")),
        "qos": int(os.getenv("HUAWEI_MQTT_QOS", "1")),
        "device_name": os.getenv("HUAWEI_DEVICE_NAME", "huawei-inverter"),
    }


def flatten_metrics(prefix: str, metrics: dict, timestamp: str, device_name: str) -> dict[str, object]:
    dev = metrics.get("device") or {}
    pv = metrics.get("pv") or {}
    inv = metrics.get("inverter") or {}

    topics: dict[str, object] = {
        f"{prefix}/status": {
            "timestamp": timestamp,
            "source": "huawei_modbus",
            "device_name": device_name,
            **metrics,
        },
        f"{prefix}/device/model": dev.get("model"),
        f"{prefix}/device/serial": dev.get("serial"),
        f"{prefix}/device/rated_power_w": dev.get("rated_power_w"),
        f"{prefix}/pv/string1_voltage": pv.get("string1_voltage_v"),
        f"{prefix}/pv/string1_current": pv.get("string1_current_a"),
        f"{prefix}/pv/string2_voltage": pv.get("string2_voltage_v"),
        f"{prefix}/pv/string2_current": pv.get("string2_current_a"),
        f"{prefix}/pv/input_power": pv.get("input_power_w"),
        f"{prefix}/inverter/active_power": inv.get("active_power_w"),
        f"{prefix}/inverter/grid_frequency": inv.get("grid_frequency_hz"),
        f"{prefix}/inverter/daily_yield": inv.get("daily_yield_kwh"),
    }
    return topics


class HuaweiMqttPublisher:
    def __init__(self, huawei_config: HuaweiConfig, mqtt_settings: dict):
        self.huawei_config = huawei_config
        self.mqtt_settings = mqtt_settings
        self.reader = HuaweiModbusReader(huawei_config)
        self.running = False
        self.mqtt = MQTTClientWrapper(
            broker_host=mqtt_settings["host"],
            broker_port=mqtt_settings["port"],
            client_id="huawei_mqtt_publisher",
            username=mqtt_settings["username"],
            password=mqtt_settings["password"],
            qos=mqtt_settings["qos"],
        )

    def publish_metrics(self, metrics: dict) -> None:
        timestamp = datetime.now(timezone.utc).isoformat()
        topics = flatten_metrics(
            self.mqtt_settings["prefix"],
            metrics,
            timestamp,
            self.mqtt_settings["device_name"],
        )
        for topic, payload in topics.items():
            if not self.mqtt.publish(topic, payload, retain=False):
                logger.warning("Failed to publish %s", topic)

    def run_once(self) -> bool:
        if not self.reader.connect():
            logger.error("Modbus connect failed for %s", self.huawei_config.host)
            return False
        try:
            metrics = self.reader.read_metrics()
            self.publish_metrics(metrics)
            inv = metrics.get("inverter") or {}
            dev = metrics.get("device") or {}
            logger.info(
                "Published Huawei metrics: model=%s active=%sW daily=%s kWh",
                dev.get("model"),
                inv.get("active_power_w"),
                inv.get("daily_yield_kwh"),
            )
            return True
        finally:
            self.reader.close()

    def start(self) -> bool:
        if not self.huawei_config.host:
            logger.error("HUAWEI_INVERTER_HOST not configured")
            return False
        if not self.mqtt.connect():
            logger.error("MQTT connect failed")
            return False

        interval = self.mqtt_settings["interval"]
        logger.info(
            "Huawei publisher started: host=%s interval=%ss prefix=%s",
            self.huawei_config.host,
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

    parser = argparse.ArgumentParser(description="Huawei SUN2000 Modbus to MQTT publisher")
    parser.add_argument("--once", action="store_true", help="Poll once and exit")
    args = parser.parse_args()

    huawei_config = load_huawei_config(DEVICE_ROOT / "config")
    mqtt_settings = load_mqtt_settings()
    publisher = HuaweiMqttPublisher(huawei_config, mqtt_settings)

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
