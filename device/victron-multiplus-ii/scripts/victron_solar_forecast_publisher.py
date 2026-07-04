#!/usr/bin/env python3
"""
Solar irradiance forecast publisher for Victron energy automations.

Fetches Open-Meteo data for Lunca Cetătui (Iași) and publishes current
irradiance plus hourly/daily forecasts to MQTT.
"""

from __future__ import annotations

import os
import signal
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEVICE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "utils"))
sys.path.insert(0, str(DEVICE_ROOT / "lib"))

from logger import get_logger  # noqa: E402
from mqtt_client import MQTTClientWrapper  # noqa: E402
from solar_forecast import fetch_solar_forecast  # noqa: E402

logger = get_logger(__name__)


def load_settings() -> dict:
    load_dotenv(REPO_ROOT / "config" / ".env")
    load_dotenv(DEVICE_ROOT / "config" / ".env", override=True)
    return {
        "host": os.getenv("MQTT_BROKER_HOST", "localhost"),
        "port": int(os.getenv("MQTT_BROKER_PORT", "1883")),
        "username": os.getenv("MQTT_USERNAME") or None,
        "password": os.getenv("MQTT_PASSWORD") or None,
        "prefix": os.getenv("VICTRON_MQTT_PREFIX", "energy/victron").rstrip("/"),
        "interval": int(os.getenv("VICTRON_FORECAST_POLL_INTERVAL", "1800")),
        "qos": int(os.getenv("VICTRON_MQTT_QOS", "1")),
        "latitude": float(os.getenv("VICTRON_FORECAST_LAT", "47.0966")),
        "longitude": float(os.getenv("VICTRON_FORECAST_LON", "27.5632")),
        "location": os.getenv(
            "VICTRON_FORECAST_LOCATION", "Lunca Cetătui, Iași, RO"
        ),
        "timezone": os.getenv("VICTRON_FORECAST_TIMEZONE", "Europe/Bucharest"),
        "forecast_days": int(os.getenv("VICTRON_FORECAST_DAYS", "3")),
        "hourly_hours": int(os.getenv("VICTRON_FORECAST_HOURLY_HOURS", "48")),
    }


def flatten_forecast(prefix: str, forecast: dict) -> dict[str, object]:
    scalars = forecast["scalars"]
    return {
        f"{prefix}/forecast/solar/current": forecast["current"],
        f"{prefix}/forecast/solar/hourly": forecast["hourly"],
        f"{prefix}/forecast/solar/daily": forecast["daily"],
        f"{prefix}/forecast/solar/radiation_wm2": scalars["radiation_wm2"],
        f"{prefix}/forecast/solar/today_sum_kwh_m2": scalars["today_sum_kwh_m2"],
        f"{prefix}/forecast/solar/is_day": scalars["is_day"],
    }


class VictronSolarForecastPublisher:
    def __init__(self, settings: dict):
        self.settings = settings
        self.running = False
        self.mqtt = MQTTClientWrapper(
            broker_host=settings["host"],
            broker_port=settings["port"],
            client_id="victron_solar_forecast_publisher",
            username=settings["username"],
            password=settings["password"],
            qos=settings["qos"],
        )

    def publish_forecast(self, forecast: dict) -> None:
        topics = flatten_forecast(self.settings["prefix"], forecast)
        for topic, payload in topics.items():
            if not self.mqtt.publish(topic, payload, retain=False):
                logger.warning("Failed to publish %s", topic)

    def run_once(self) -> bool:
        try:
            forecast = fetch_solar_forecast(
                latitude=self.settings["latitude"],
                longitude=self.settings["longitude"],
                location_name=self.settings["location"],
                timezone=self.settings["timezone"],
                forecast_days=self.settings["forecast_days"],
                hourly_hours=self.settings["hourly_hours"],
            )
        except Exception as exc:
            logger.error("Forecast fetch failed: %s", exc)
            return False

        self.publish_forecast(forecast)
        current = forecast["current"]
        logger.info(
            "Published solar forecast: %s W/m² is_day=%s today=%s kWh/m²",
            current.get("shortwave_radiation_wm2"),
            current.get("is_day"),
            forecast["scalars"].get("today_sum_kwh_m2"),
        )
        return True

    def start(self) -> bool:
        if not self.mqtt.connect():
            logger.error("MQTT connect failed")
            return False

        interval = self.settings["interval"]
        logger.info(
            "Solar forecast publisher started: %s interval=%ss prefix=%s",
            self.settings["location"],
            interval,
            self.settings["prefix"],
        )
        self.running = True
        while self.running:
            self.run_once()
            time.sleep(interval)
        return True

    def stop(self) -> None:
        self.running = False
        self.mqtt.disconnect()


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Victron solar forecast MQTT publisher")
    parser.add_argument("--once", action="store_true", help="Fetch once and exit")
    args = parser.parse_args()

    settings = load_settings()
    publisher = VictronSolarForecastPublisher(settings)

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
