#!/usr/bin/env python3
"""Poll Tuya / bridge Tasmota energy consumers; publish MQTT status; handle switch commands."""

from __future__ import annotations

import json
import os
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

DEVICE_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = DEVICE_ROOT.parent.parent
sys.path.insert(0, str(DEVICE_ROOT / "lib"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "utils"))

from consumer_schema import ConsumerStatus  # noqa: E402
from registry import load_consumers_registry  # noqa: E402
from tasmota_meter import (  # noqa: E402
    command_topics,
    parse_power_payload,
    parse_sensor_status,
    power_stat_key,
    stale_after_s,
    switch_command_payload,
)
from tuya_credentials import resolve_tuya_device  # noqa: E402
from tuya_meter import (  # noqa: E402
    apply_metric_cache,
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


def _poll_tuya_consumer(consumer: Dict[str, Any]) -> ConsumerStatus:
    creds = resolve_tuya_device(
        consumer.get("tuya_device_id", ""),
        consumer.get("tuya_name"),
    )
    raw = read_tuya_status(creds)
    return parse_dps_status(consumer, raw, creds)


def _handle_tuya_command(consumer: Dict[str, Any], action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    creds = resolve_tuya_device(
        consumer.get("tuya_device_id", ""),
        consumer.get("tuya_name"),
    )
    controls = consumer.get("controls") or {}
    if not controls.get("switch"):
        return {"success": False, "message": "Switch control disabled for this consumer"}

    action = (action or payload.get("action", "")).lower()
    if action == "toggle":
        st = _poll_tuya_consumer(consumer)
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


class TasmotaConsumerState:
    def __init__(self) -> None:
        self.last_sensor_ts: float = 0.0
        self.last_sensor_payload: Any = None
        self.switch_on: Optional[bool] = None
        self.lwt_online: Optional[bool] = None
        self.last_status: Optional[ConsumerStatus] = None
        self.reported_offline: bool = False


class TuyaConsumerState:
    def __init__(self) -> None:
        self.last_metrics_ts: float = 0.0
        self.last_status: Optional[ConsumerStatus] = None


class ConsumerPublisher:
    def __init__(self) -> None:
        load_dotenv(DEVICE_ROOT / "config" / ".env")
        load_dotenv(REPO_ROOT / "config" / ".env")
        enabled = _load_enabled_consumers()
        self.tuya_consumers = [c for c in enabled if c.get("type", "tuya_meter") == "tuya_meter"]
        self.tasmota_consumers = [c for c in enabled if c.get("type") == "tasmota_meter"]
        self.consumers = enabled
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
        self._last_tuya_poll: Dict[str, float] = {}
        self._tuya: Dict[str, TuyaConsumerState] = {}
        self._tasmota: Dict[str, TasmotaConsumerState] = {}

    def start(self) -> None:
        self.mqtt.connect()
        self.mqtt.subscribe("energy/consumers/+/command/#", self._on_mqtt_command)
        for consumer in self.tasmota_consumers:
            self._setup_tasmota(consumer)
        logger.info(
            "Energy consumers publisher started (%d consumer(s): %d Tuya, %d Tasmota)",
            len(self.consumers),
            len(self.tuya_consumers),
            len(self.tasmota_consumers),
        )

    def _tasmota_state(self, consumer_id: str) -> TasmotaConsumerState:
        if consumer_id not in self._tasmota:
            self._tasmota[consumer_id] = TasmotaConsumerState()
        return self._tasmota[consumer_id]

    def _tuya_state(self, consumer_id: str) -> TuyaConsumerState:
        if consumer_id not in self._tuya:
            self._tuya[consumer_id] = TuyaConsumerState()
        return self._tuya[consumer_id]

    def _finalize_tuya_status(
        self, consumer: Dict[str, Any], status: ConsumerStatus
    ) -> ConsumerStatus:
        state = self._tuya_state(consumer["id"])
        status, state.last_metrics_ts = apply_metric_cache(
            consumer,
            status,
            previous=state.last_status,
            previous_metrics_ts=state.last_metrics_ts,
        )
        state.last_status = status
        return status

    def _setup_tasmota(self, consumer: Dict[str, Any]) -> None:
        cid = consumer["id"]
        topics = command_topics(consumer)
        self._tasmota_state(cid)

        def on_sensor(_topic: str, payload: str) -> None:
            self._on_tasmota_sensor(consumer, payload)

        def on_power(_topic: str, payload: str) -> None:
            self._on_tasmota_power(consumer, payload)

        def on_lwt(_topic: str, payload: str) -> None:
            self._on_tasmota_lwt(consumer, payload)

        self.mqtt.subscribe(topics["sensor"], on_sensor)
        self.mqtt.subscribe(topics["power_stat"], on_power)
        pk = power_stat_key(consumer)
        if pk != "POWER":
            self.mqtt.subscribe(f"stat/{consumer['tasmota_topic']}/POWER", on_power)
        self.mqtt.subscribe(topics["lwt"], on_lwt)

        tele_period = consumer.get("tele_period_s")
        if tele_period is not None:
            self.mqtt.publish(topics["command_tele_period"], str(int(tele_period)), retain=False)
        # Request immediate energy telemetry (Status 8 → SENSOR on many builds)
        self.mqtt.publish(topics["command_status"], "8", retain=False)
        logger.info("Tasmota consumer %s subscribed (%s)", cid, consumer.get("tasmota_topic"))

    def _tasmota_online(self, consumer: Dict[str, Any], state: TasmotaConsumerState) -> bool:
        if state.lwt_online is False:
            return False
        if state.last_sensor_ts <= 0:
            return state.lwt_online is True
        return (time.time() - state.last_sensor_ts) <= stale_after_s(consumer)

    def _on_tasmota_sensor(self, consumer: Dict[str, Any], payload: str) -> None:
        cid = consumer["id"]
        state = self._tasmota_state(cid)
        state.last_sensor_ts = time.time()
        state.last_sensor_payload = payload
        state.reported_offline = False
        status = parse_sensor_status(
            consumer,
            payload,
            switch_on=state.switch_on,
            online=True,
            extra={"tasmota_topic": consumer.get("tasmota_topic")},
        )
        if state.lwt_online is False:
            status.online = False
        state.last_status = status
        _publish_status(self.mqtt, consumer, status)
        logger.debug("%s power=%s W (tasmota)", cid, status.power_w)

    def _on_tasmota_power(self, consumer: Dict[str, Any], payload: str) -> None:
        cid = consumer["id"]
        state = self._tasmota_state(cid)
        switch_on = parse_power_payload(payload)
        if switch_on is None:
            return
        state.switch_on = switch_on
        if state.last_sensor_payload is not None:
            status = parse_sensor_status(
                consumer,
                state.last_sensor_payload,
                switch_on=switch_on,
                online=self._tasmota_online(consumer, state),
                extra={"tasmota_topic": consumer.get("tasmota_topic")},
            )
            state.last_status = status
            _publish_status(self.mqtt, consumer, status)

    def _on_tasmota_lwt(self, consumer: Dict[str, Any], payload: str) -> None:
        cid = consumer["id"]
        state = self._tasmota_state(cid)
        val = (payload or "").strip()
        if val == "Online":
            state.lwt_online = True
        elif val == "Offline":
            state.lwt_online = False
            err = ConsumerStatus(
                consumer_id=cid,
                name=consumer.get("name", cid),
                online=False,
                source="tasmota_meter",
                tags=list(consumer.get("tags") or []),
                extra={"switch_on": state.switch_on, "lwt": val},
            )
            state.last_status = err
            _publish_status(self.mqtt, consumer, err)

    def _handle_tasmota_command(
        self, consumer: Dict[str, Any], action: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        controls = consumer.get("controls") or {}
        if not controls.get("switch"):
            return {"success": False, "message": "Switch control disabled for this consumer"}

        action = (action or payload.get("action", "")).lower()
        cmd = switch_command_payload(action)
        if not cmd:
            return {"success": False, "message": f"Unknown switch action: {action}"}

        topics = command_topics(consumer)
        ok = self.mqtt.publish(topics["command_switch"], cmd, retain=False)
        return {
            "success": ok,
            "action": action if action != "toggle" else "toggle",
            "message": "Switch command sent" if ok else "MQTT publish failed",
            "consumer_id": consumer["id"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

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
                if consumer.get("type") == "tasmota_meter":
                    result = self._handle_tasmota_command(consumer, payload.get("action", ""), payload)
                else:
                    result = self._handle_tuya_command(consumer, payload.get("action", ""), payload)
            else:
                result = {"success": False, "message": f"Unknown command: {command}"}
            prefix = _mqtt_prefix(consumer)
            self.mqtt.publish(f"{prefix}/response", result, retain=False)
            if result.get("success") and consumer.get("type", "tuya_meter") == "tuya_meter":
                time.sleep(0.5)
                status = self._finalize_tuya_status(consumer, _poll_tuya_consumer(consumer))
                _publish_status(self.mqtt, consumer, status)
        except Exception as exc:
            logger.exception("Command failed for %s: %s", consumer_id, exc)
            prefix = _mqtt_prefix(consumer)
            self.mqtt.publish(
                f"{prefix}/response",
                {"success": False, "message": str(exc), "consumer_id": consumer_id},
                retain=False,
            )

    def _poll_tuya_due(self) -> None:
        now = time.time()
        for consumer in self.tuya_consumers:
            cid = consumer["id"]
            interval = float(consumer.get("poll_interval_s") or os.getenv("ENERGY_CONSUMERS_DEFAULT_INTERVAL", "30"))
            last = self._last_tuya_poll.get(cid, 0)
            if now - last < interval:
                continue
            try:
                status = self._finalize_tuya_status(consumer, _poll_tuya_consumer(consumer))
                _publish_status(self.mqtt, consumer, status)
                self._last_tuya_poll[cid] = now
                logger.debug("%s power=%s W (tuya)", cid, status.power_w)
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
                err = self._finalize_tuya_status(consumer, err)
                _publish_status(self.mqtt, consumer, err)

    def _check_tasmota_stale(self) -> None:
        now = time.time()
        for consumer in self.tasmota_consumers:
            cid = consumer["id"]
            state = self._tasmota_state(cid)
            if state.last_sensor_ts <= 0 or state.reported_offline:
                continue
            if now - state.last_sensor_ts <= stale_after_s(consumer):
                continue
            state.reported_offline = True
            prev = state.last_status
            err = ConsumerStatus(
                consumer_id=cid,
                name=consumer.get("name", cid),
                power_w=prev.power_w if prev else None,
                energy_kwh=prev.energy_kwh if prev else None,
                voltage_v=prev.voltage_v if prev else None,
                current_a=prev.current_a if prev else None,
                online=False,
                source="tasmota_meter",
                tags=list(consumer.get("tags") or []),
                extra={
                    "switch_on": state.switch_on,
                    "stale": True,
                    "last_sensor_age_s": int(now - state.last_sensor_ts),
                },
            )
            state.last_status = err
            _publish_status(self.mqtt, consumer, err)
            logger.warning("Tasmota consumer %s stale (no SENSOR for %ds)", cid, int(now - state.last_sensor_ts))

    def run(self) -> None:
        self.start()
        while _running:
            self._poll_tuya_due()
            self._check_tasmota_stale()
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
