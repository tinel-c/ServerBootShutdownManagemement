#!/usr/bin/env python3
"""
Victron Cerbo GX / MultiPlus-II MQTT publisher.

Polls Modbus TCP every VICTRON_MODBUS_POLL_INTERVAL seconds (default 10)
and publishes readings to the automation MQTT broker.
"""

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

from logger import get_logger  # noqa: E402
from mqtt_client import MQTTClientWrapper  # noqa: E402
from victron_modbus import VictronConfig, VictronModbusReader, load_victron_config  # noqa: E402

logger = get_logger(__name__)


def load_mqtt_settings() -> dict:
    load_dotenv(REPO_ROOT / "config" / ".env")
    load_dotenv(DEVICE_ROOT / "config" / ".env", override=True)
    return {
        "host": os.getenv("MQTT_BROKER_HOST", "localhost"),
        "port": int(os.getenv("MQTT_BROKER_PORT", "1883")),
        "username": os.getenv("MQTT_USERNAME") or None,
        "password": os.getenv("MQTT_PASSWORD") or None,
        "prefix": os.getenv("VICTRON_MQTT_PREFIX", "energy/victron").rstrip("/"),
        "interval": int(os.getenv("VICTRON_MODBUS_POLL_INTERVAL", "10")),
        "qos": int(os.getenv("VICTRON_MQTT_QOS", "1")),
    }


def flatten_metrics(prefix: str, metrics: dict, timestamp: str) -> dict[str, object]:
    """Map nested metrics to MQTT topic suffix -> payload."""
    topics: dict[str, object] = {
        f"{prefix}/status": {
            "timestamp": timestamp,
            "source": "victron_modbus",
            **metrics,
        },
        f"{prefix}/battery/voltage": metrics["battery"]["voltage_v"],
        f"{prefix}/battery/soc": metrics["battery"]["soc_pct"],
        f"{prefix}/battery/power": metrics["battery"]["power_w"],
        f"{prefix}/grid/power_l1": metrics["grid"]["power_l1_w"],
        f"{prefix}/pv/dc_power": metrics["pv"]["dc_power_w"],
        f"{prefix}/pv/dc_current": metrics["pv"]["dc_current_a"],
        f"{prefix}/pv/ac_output_l1": metrics["pv"]["ac_output_l1_w"],
        f"{prefix}/pv/ac_grid_l1": metrics["pv"]["ac_grid_l1_w"],
        f"{prefix}/load/consumption_l1": metrics["load"]["consumption_l1_w"],
        f"{prefix}/load/output_l1": metrics["load"]["output_l1_w"],
        f"{prefix}/load/input_l1": metrics["load"]["input_l1_w"],
        f"{prefix}/inverter/ac_in_voltage_l1": metrics["inverter"]["ac_in_voltage_l1_v"],
        f"{prefix}/inverter/ac_in_power_l1": metrics["inverter"]["ac_in_power_l1_w"],
        f"{prefix}/inverter/ac_out_power_l1": metrics["inverter"]["ac_out_power_l1_w"],
        f"{prefix}/inverter/dc_voltage": metrics["inverter"]["dc_voltage_v"],
        f"{prefix}/inverter/state": metrics["inverter"]["state"],
        f"{prefix}/inverter/state_code": metrics["inverter"]["state_code"],
        f"{prefix}/inverter/grid_lost": metrics["inverter"]["grid_lost"],
    }

    solar = metrics.get("solar_charger")
    if solar:
        topics.update(
            {
                f"{prefix}/solar/pv_voltage": solar["pv_voltage_v"],
                f"{prefix}/solar/charge_current": solar["charge_current_a"],
                f"{prefix}/solar/pv_power": solar["pv_power_w"],
                f"{prefix}/solar/yield_today": solar["yield_today_kwh"],
                f"{prefix}/solar/state": solar["state"],
            }
        )

    pv_inv = metrics.get("pv_inverter")
    if pv_inv:
        topics.update(
            {
                f"{prefix}/pvinverter/ac_power_l1": pv_inv["ac_power_l1_w"],
                f"{prefix}/pvinverter/ac_voltage_l1": pv_inv["ac_voltage_l1_v"],
                f"{prefix}/pvinverter/ac_current_l1": pv_inv["ac_current_l1_a"],
                f"{prefix}/pvinverter/position": pv_inv["position"],
            }
        )

    return topics


class VictronMqttPublisher:
    def __init__(self, victron_config: VictronConfig, mqtt_settings: dict):
        self.victron_config = victron_config
        self.mqtt_settings = mqtt_settings
        self.reader = VictronModbusReader(victron_config)
        self.running = False
        self.mqtt = MQTTClientWrapper(
            broker_host=mqtt_settings["host"],
            broker_port=mqtt_settings["port"],
            client_id="victron_mqtt_publisher",
            username=mqtt_settings["username"],
            password=mqtt_settings["password"],
            qos=mqtt_settings["qos"],
        )

    def publish_metrics(self, metrics: dict) -> None:
        timestamp = datetime.now(timezone.utc).isoformat()
        topics = flatten_metrics(self.mqtt_settings["prefix"], metrics, timestamp)
        for topic, payload in topics.items():
            if isinstance(payload, (dict, list)):
                body = payload
            else:
                body = payload
            if not self.mqtt.publish(topic, body, retain=False):
                logger.warning("Failed to publish %s", topic)

    def run_once(self) -> bool:
        if not self.reader.connect():
            logger.error("Modbus connect failed for %s", self.victron_config.gx_host)
            return False
        try:
            metrics = self.reader.read_metrics()
            self.publish_metrics(metrics)
            logger.info(
                "Published Victron metrics: battery=%s%% grid=%sW load=%sW",
                metrics["battery"]["soc_pct"],
                metrics["grid"]["power_l1_w"],
                metrics["load"]["consumption_l1_w"],
            )
            return True
        finally:
            self.reader.close()

    def start(self) -> bool:
        if not self.victron_config.gx_host:
            logger.error("VICTRON_GX_HOST not configured")
            return False
        if not self.mqtt.connect():
            logger.error("MQTT connect failed")
            return False

        interval = self.mqtt_settings["interval"]
        logger.info(
            "Victron publisher started: gx=%s interval=%ss prefix=%s",
            self.victron_config.gx_host,
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

    parser = argparse.ArgumentParser(description="Victron Modbus to MQTT publisher")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Poll once and exit (for testing)",
    )
    args = parser.parse_args()

    victron_config = load_victron_config(DEVICE_ROOT / "config")
    mqtt_settings = load_mqtt_settings()
    publisher = VictronMqttPublisher(victron_config, mqtt_settings)

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
