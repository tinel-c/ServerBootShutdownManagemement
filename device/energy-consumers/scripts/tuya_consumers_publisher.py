#!/usr/bin/env python3
"""Poll Tuya energy consumers and publish MQTT status; handle switch commands."""

from __future__ import annotations

import json
import os
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv

DEVICE_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = DEVICE_ROOT.parent.parent
sys.path.insert(0, str(DEVICE_ROOT / "lib"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "utils"))

from consumer_schema import ConsumerStatus  # noqa: E402
from registry import load_consumers_registry  # noqa: E402
from tuya_credentials import resolve_tuya_device  # noqa: E402
from tuya_meter import (  # noqa: E402
    parse_dps_status,
    read_tuya_status,
    set_tuya_switch,
    switch_dps_key,
)
from logger import get_logger  # noqa: E402
from mqtt_client import MQTTClientWrapper  # noqa: E402

logger = get_logger(__name__)

_running = True


def _handle_signal(signum, frame):  # noqa: ARG001
    global _running
    _running = False


def _registry_path() -> Path:
    env_path = os.getenv("ENERGY_CONSUMERS_REGISTRY", "")
    if env_path:
        p = Path(env_path)
        return p if p.is_absolute() else DEVICE_ROOT / p
    for name in ("consumers_registry.yaml", "consumers_registry.example.yaml"):
        p = DEVICE_ROOT / "config" / name
        if p.is_file():
            return p
    return DEVICE_ROOT / "config" / "consumers_registry.yaml"


def _load_enabled_consumers() -> List[Dict[str, Any]]:
    data = load_consumers_registry(_registry_path())
    return [c for c in data.get("consumers", []) if c.get("enabled")]


def _mqtt_prefix(consumer: Dict[str, Any]) -> str:
    return (consumer.get("mqtt_prefix") or f"energy/consumers/{consumer['id']}").rstrip("/")


def _publish_status(mqtt: MQTTClientWrapper, consumer: Dict[str, Any], status: ConsumerStatus) -> None:
    prefix = _mqtt_prefix(consumer)
    payload = status.to_mqtt_dict()
    mqtt.publish(f"{prefix}/status", payload, retain=True)
    if status.power_w is not None:
        mqtt.publish(f"{prefix}/power_w", int(round(status.power_w)), retain=False)
    if status.energy_kwh is not None:
        mqtt.publish(f"{prefix}/energy_kwh", status.energy_kwh, retain=False)


def _poll_consumer(consumer: Dict[str, Any]) -> ConsumerStatus:
    creds = resolve_tuya_device(
        consumer.get("tuya_device_id", ""),
        consumer.get("tuya_name"),
    )
    raw = read_tuya_status(creds)
    return parse_dps_status(consumer, raw, creds)


def _handle_command(consumer: Dict[str, Any], action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    creds = resolve_tuya_device(
        consumer.get("tuya_device_id", ""),
        consumer.get("tuya_name"),
    )
    controls = consumer.get("controls") or {}
    if not controls.get("switch"):
        return {"success": False, "message": "Switch control disabled for this consumer"}

    action = (action or payload.get("action", "")).lower()
    if action == "toggle":
        st = _poll_consumer(consumer)
        on = not bool(st.extra.get("switch_on"))
    elif action in ("on", "true", "1"):
        on = True
    elif action in ("off", "false", "0"):
        on = False
    else:
        return {"success": False, "message": f"Unknown switch action: {action}"}

    dps_key = switch_dps_key(consumer)
    result = set_tuya_switch(creds, dps_key, on)
    ok = "Error" not in str(result.get("Err", ""))
    return {
        "success": ok,
        "action": "on" if on else "off",
        "message": "Switch updated" if ok else str(result),
        "consumer_id": consumer["id"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


class ConsumerPublisher:
    def __init__(self) -> None:
        load_dotenv(DEVICE_ROOT / "config" / ".env")
        load_dotenv(REPO_ROOT / "config" / ".env")
        self.consumers = _load_enabled_consumers()
        if not self.consumers:
            logger.warning("No enabled consumers in registry")
        self.mqtt = MQTTClientWrapper(
            broker_host=os.getenv("MQTT_BROKER_HOST", "localhost"),
            broker_port=int(os.getenv("MQTT_BROKER_PORT", "1883")),
            username=os.getenv("MQTT_USERNAME") or None,
            password=os.getenv("MQTT_PASSWORD") or None,
            client_id="energy-consumers-publisher",
            qos=int(os.getenv("ENERGY_CONSUMERS_MQTT_QOS", "1")),
        )
        self._by_id = {c["id"]: c for c in self.consumers}
        self._last_poll: Dict[str, float] = {}

    def start(self) -> None:
        self.mqtt.connect()
        self.mqtt.subscribe("energy/consumers/+/command/#", self._on_mqtt_command)
        logger.info("Energy consumers publisher started (%d consumer(s))", len(self.consumers))

    def _on_mqtt_command(self, topic: str, payload: Any) -> None:
        parts = topic.split("/")
        if len(parts) < 5 or parts[0] != "energy" or parts[1] != "consumers":
            return
        consumer_id = parts[2]
        command = parts[4] if len(parts) > 4 else ""
        consumer = self._by_id.get(consumer_id)
        if not consumer:
            logger.warning("Command for unknown consumer: %s", consumer_id)
            return
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                payload = {"action": payload}
        if not isinstance(payload, dict):
            payload = {}
        try:
            logger.info("Command %s for %s action=%s", command, consumer_id, payload.get("action"))
            if command == "switch":
                result = _handle_command(consumer, payload.get("action", ""), payload)
            else:
                result = {"success": False, "message": f"Unknown command: {command}"}
            prefix = _mqtt_prefix(consumer)
            self.mqtt.publish(f"{prefix}/response", result, retain=False)
            if result.get("success"):
                time.sleep(0.5)
                status = _poll_consumer(consumer)
                _publish_status(self.mqtt, consumer, status)
        except Exception as exc:
            logger.exception("Command failed for %s: %s", consumer_id, exc)
            prefix = _mqtt_prefix(consumer)
            self.mqtt.publish(
                f"{prefix}/response",
                {"success": False, "message": str(exc), "consumer_id": consumer_id},
                retain=False,
            )

    def poll_due(self) -> None:
        now = time.time()
        for consumer in self.consumers:
            cid = consumer["id"]
            interval = float(consumer.get("poll_interval_s") or os.getenv("ENERGY_CONSUMERS_DEFAULT_INTERVAL", "30"))
            last = self._last_poll.get(cid, 0)
            if now - last < interval:
                continue
            try:
                status = _poll_consumer(consumer)
                _publish_status(self.mqtt, consumer, status)
                self._last_poll[cid] = now
                logger.debug("%s power=%s W", cid, status.power_w)
            except Exception as exc:
                logger.error("Poll failed for %s: %s", cid, exc)
                err = ConsumerStatus(
                    consumer_id=cid,
                    name=consumer.get("name", cid),
                    online=False,
                    source="tuya_meter",
                    tags=list(consumer.get("tags") or []),
                    extra={"error": str(exc)},
                )
                _publish_status(self.mqtt, consumer, err)

    def run(self) -> None:
        self.start()
        while _running:
            self.poll_due()
            # loop_start() in MQTTClientWrapper.connect() handles the network thread
            time.sleep(1.0)
        self.mqtt.disconnect()


def main() -> int:
    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)
    pub = ConsumerPublisher()
    pub.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
