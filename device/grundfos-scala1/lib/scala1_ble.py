"""Grundfos SCALA1 BLE client — GATT discovery and telemetry reads."""

from __future__ import annotations

import asyncio
import os
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

try:
    from bleak import BleakClient, BleakScanner
    from bleak.backends.characteristic import BleakGATTCharacteristic
except ImportError:  # pragma: no cover - optional at import time on dev machines
    BleakClient = None  # type: ignore[misc, assignment]
    BleakScanner = None  # type: ignore[misc, assignment]
    BleakGATTCharacteristic = Any  # type: ignore[misc, assignment]


@dataclass
class Scala1Config:
    ble_address: str = ""
    ble_adapter: str | None = None
    scan_timeout: float = 10.0
    connect_timeout: float = 20.0
    name_filter: str = "SCALA"
    metrics_map_path: Path | None = None
    telemetry_service_uuid: str = ""
    telemetry_char_uuid: str = ""
    control_service_uuid: str = ""
    control_write_char_uuid: str = ""
    control_start_payload_hex: str = ""
    control_stop_payload_hex: str = ""
    control_reset_alarm_payload_hex: str = ""
    device_model: str = ""
    device_serial: str = ""


def _env_path(config_dir: Path | None) -> Path:
    if config_dir is None:
        return Path(__file__).resolve().parent.parent / "config"
    return config_dir


def load_scala1_config(config_dir: Path | None = None) -> Scala1Config:
    root = Path(__file__).resolve().parent.parent.parent.parent
    load_dotenv(root / "config" / ".env")
    load_dotenv(_env_path(config_dir) / ".env", override=True)

    map_path = os.getenv("SCALA1_METRICS_MAP", "").strip()
    metrics_map_path = Path(map_path) if map_path else _env_path(config_dir) / "metrics_map.yaml"
    if not metrics_map_path.is_file():
        example = _env_path(config_dir) / "metrics_map.example.yaml"
        if example.is_file():
            metrics_map_path = example

    return Scala1Config(
        ble_address=os.getenv("SCALA1_BLE_ADDRESS", "").strip(),
        ble_adapter=os.getenv("SCALA1_BLE_ADAPTER") or None,
        scan_timeout=float(os.getenv("SCALA1_BLE_SCAN_TIMEOUT", "10")),
        connect_timeout=float(os.getenv("SCALA1_BLE_CONNECT_TIMEOUT", "20")),
        name_filter=os.getenv("SCALA1_BLE_NAME_FILTER", "SCALA"),
        metrics_map_path=metrics_map_path if metrics_map_path.is_file() else None,
        telemetry_service_uuid=os.getenv("SCALA1_TELEMETRY_SERVICE_UUID", "").strip(),
        telemetry_char_uuid=os.getenv("SCALA1_TELEMETRY_CHAR_UUID", "").strip(),
        control_service_uuid=os.getenv("SCALA1_CONTROL_SERVICE_UUID", "").strip(),
        control_write_char_uuid=os.getenv("SCALA1_CONTROL_WRITE_CHAR_UUID", "").strip(),
        control_start_payload_hex=os.getenv("SCALA1_CONTROL_START_HEX", "").strip(),
        control_stop_payload_hex=os.getenv("SCALA1_CONTROL_STOP_HEX", "").strip(),
        control_reset_alarm_payload_hex=os.getenv("SCALA1_CONTROL_RESET_ALARM_HEX", "").strip(),
        device_model=os.getenv("SCALA1_DEVICE_MODEL", "").strip(),
        device_serial=os.getenv("SCALA1_DEVICE_SERIAL", "").strip(),
    )


def _require_bleak() -> None:
    if BleakScanner is None or BleakClient is None:
        raise RuntimeError("bleak is not installed — run: pip install bleak>=0.21")


def _hex(data: bytes) -> str:
    return data.hex()


def _parse_field(data: bytes, spec: dict[str, Any]) -> Any:
    offset = int(spec.get("offset", 0))
    fmt = spec.get("format", "uint8")
    scale = float(spec.get("scale", 1.0))
    if offset >= len(data):
        return None

    if fmt == "uint8":
        value = data[offset]
    elif fmt == "int8":
        value = struct.unpack_from("b", data, offset)[0]
    elif fmt == "uint16_le":
        if offset + 2 > len(data):
            return None
        value = struct.unpack_from("<H", data, offset)[0]
    elif fmt == "int16_le":
        if offset + 2 > len(data):
            return None
        value = struct.unpack_from("<h", data, offset)[0]
    elif fmt == "uint32_le":
        if offset + 4 > len(data):
            return None
        value = struct.unpack_from("<I", data, offset)[0]
    elif fmt == "float32_le":
        if offset + 4 > len(data):
            return None
        value = struct.unpack_from("<f", data, offset)[0]
    elif fmt == "bool":
        value = bool(data[offset])
    else:
        return None

    if isinstance(value, float):
        return round(value * scale, 4)
    if isinstance(value, int) and scale != 1.0:
        return round(value * scale, 4)
    return value


@dataclass
class Scala1BleClient:
    config: Scala1Config
    _metrics_map: dict[str, Any] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        if self.config.metrics_map_path and self.config.metrics_map_path.is_file():
            with open(self.config.metrics_map_path, encoding="utf-8") as fh:
                self._metrics_map = yaml.safe_load(fh) or {}

    async def scan(self) -> list[dict[str, str]]:
        _require_bleak()
        kwargs: dict[str, Any] = {"timeout": self.config.scan_timeout}
        if self.config.ble_adapter:
            kwargs["adapter"] = self.config.ble_adapter
        devices = await BleakScanner.discover(**kwargs)
        found: list[dict[str, str]] = []
        for dev in devices:
            name = dev.name or ""
            if self.config.name_filter and self.config.name_filter.lower() not in name.lower():
                continue
            found.append({"name": name, "address": dev.address})
        return found

    async def dump_gatt(self, address: str | None = None) -> dict[str, Any]:
        _require_bleak()
        addr = address or self.config.ble_address
        if not addr:
            raise ValueError("SCALA1_BLE_ADDRESS not set and no address argument")

        result: dict[str, Any] = {"address": addr, "services": []}
        kwargs: dict[str, Any] = {"timeout": self.config.connect_timeout}
        if self.config.ble_adapter:
            kwargs["adapter"] = self.config.ble_adapter

        async with BleakClient(addr, **kwargs) as client:
            if not client.is_connected:
                raise ConnectionError(f"Failed to connect to {addr}")
            for service in client.services:
                svc = {
                    "uuid": str(service.uuid),
                    "description": service.description or "",
                    "characteristics": [],
                }
                for char in service.characteristics:
                    props = list(char.properties)
                    entry: dict[str, Any] = {
                        "uuid": str(char.uuid),
                        "description": char.description or "",
                        "properties": props,
                    }
                    if "read" in props:
                        try:
                            raw = await client.read_gatt_char(char.uuid)
                            entry["value_hex"] = _hex(raw)
                            entry["value_len"] = len(raw)
                        except Exception as exc:  # noqa: BLE001
                            entry["read_error"] = str(exc)
                    svc["characteristics"].append(entry)
                result["services"].append(svc)
        return result

    async def _read_char(self, client: BleakClient, service_uuid: str, char_uuid: str) -> bytes:
        for service in client.services:
            if service_uuid and str(service.uuid).lower() != service_uuid.lower():
                continue
            for char in service.characteristics:
                if str(char.uuid).lower() != char_uuid.lower():
                    continue
                if "read" not in char.properties:
                    raise PermissionError(f"Characteristic not readable: {char_uuid}")
                return await client.read_gatt_char(char.uuid)
        raise LookupError(f"Characteristic not found: {char_uuid}")

    def _parse_metrics_from_map(self, raw_chunks: dict[str, bytes]) -> dict[str, Any]:
        metrics: dict[str, Any] = {
            "device": {
                "model": self.config.device_model or None,
                "serial": self.config.device_serial or None,
            },
            "raw": {k: _hex(v) for k, v in raw_chunks.items()},
        }
        fields = self._metrics_map.get("fields") or {}
        for name, spec in fields.items():
            source = spec.get("source", "telemetry")
            data = raw_chunks.get(source)
            if not data:
                continue
            metrics[name] = _parse_field(data, spec)
        return metrics

    def _parse_metrics_from_env(self, telemetry: bytes) -> dict[str, Any]:
        return {
            "device": {
                "model": self.config.device_model or None,
                "serial": self.config.device_serial or None,
            },
            "running": None,
            "pressure_bar": None,
            "flow_m3h": None,
            "power_w": None,
            "alarm_code": None,
            "alarm_text": None,
            "mode": None,
            "raw": {"telemetry": _hex(telemetry)},
        }

    async def read_metrics(self, address: str | None = None) -> dict[str, Any]:
        _require_bleak()
        addr = address or self.config.ble_address
        if not addr:
            raise ValueError("SCALA1_BLE_ADDRESS not configured")

        kwargs: dict[str, Any] = {"timeout": self.config.connect_timeout}
        if self.config.ble_adapter:
            kwargs["adapter"] = self.config.ble_adapter

        async with BleakClient(addr, **kwargs) as client:
            if not client.is_connected:
                raise ConnectionError(f"Failed to connect to {addr}")

            raw_chunks: dict[str, bytes] = {}
            char_map = self._metrics_map.get("characteristics") or {}

            if char_map:
                for key, spec in char_map.items():
                    svc = spec.get("service_uuid", "")
                    cuuid = spec.get("char_uuid", "")
                    if not cuuid:
                        continue
                    raw_chunks[key] = await self._read_char(client, svc, cuuid)
                return self._parse_metrics_from_map(raw_chunks)

            if self.config.telemetry_char_uuid:
                telemetry = await self._read_char(
                    client,
                    self.config.telemetry_service_uuid,
                    self.config.telemetry_char_uuid,
                )
                return self._parse_metrics_from_env(telemetry)

            # Fallback: dump all readable characteristics into raw map
            for service in client.services:
                for char in service.characteristics:
                    if "read" not in char.properties:
                        continue
                    key = f"{service.uuid}/{char.uuid}"
                    try:
                        raw_chunks[key] = await client.read_gatt_char(char.uuid)
                    except Exception:
                        continue
            return self._parse_metrics_from_map(raw_chunks) if self._metrics_map.get("fields") else {
                "device": {
                    "model": self.config.device_model or None,
                    "serial": self.config.device_serial or None,
                },
                "raw": {k: _hex(v) for k, v in raw_chunks.items()},
            }

    async def send_command(self, action: str, address: str | None = None) -> bool:
        _require_bleak()
        addr = address or self.config.ble_address
        if not addr:
            raise ValueError("SCALA1_BLE_ADDRESS not configured")

        action_map = {
            "start": self.config.control_start_payload_hex,
            "stop": self.config.control_stop_payload_hex,
            "reset_alarm": self.config.control_reset_alarm_payload_hex,
        }
        payload_hex = action_map.get(action, "")
        if not payload_hex or not self.config.control_write_char_uuid:
            raise NotImplementedError(
                f"Control action '{action}' not configured — set SCALA1_CONTROL_* in .env after BLE capture"
            )

        payload = bytes.fromhex(payload_hex.replace(" ", ""))
        kwargs: dict[str, Any] = {"timeout": self.config.connect_timeout}
        if self.config.ble_adapter:
            kwargs["adapter"] = self.config.ble_adapter

        async with BleakClient(addr, **kwargs) as client:
            if not client.is_connected:
                raise ConnectionError(f"Failed to connect to {addr}")
            char = None
            for service in client.services:
                if (
                    self.config.control_service_uuid
                    and str(service.uuid).lower() != self.config.control_service_uuid.lower()
                ):
                    continue
                for c in service.characteristics:
                    if str(c.uuid).lower() == self.config.control_write_char_uuid.lower():
                        char = c
                        break
            if char is None:
                raise LookupError(f"Control characteristic not found: {self.config.control_write_char_uuid}")
            if "write" not in char.properties and "write-without-response" not in char.properties:
                raise PermissionError(f"Characteristic not writable: {char.uuid}")
            await client.write_gatt_char(char.uuid, payload, response="write" in char.properties)
            return True


def run_async(coro):
    return asyncio.run(coro)


def metrics_to_status(metrics: dict[str, Any], device_name: str) -> dict[str, Any]:
    """Normalize BLE metrics into MQTT status payload."""
    from datetime import datetime, timezone

    status = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "grundfos_ble",
        "device_name": device_name,
        "running": metrics.get("running"),
        "pressure_bar": metrics.get("pressure_bar"),
        "flow_m3h": metrics.get("flow_m3h"),
        "power_w": metrics.get("power_w"),
        "alarm_code": metrics.get("alarm_code"),
        "alarm_text": metrics.get("alarm_text"),
        "mode": metrics.get("mode"),
        "device": metrics.get("device") or {},
        "raw": metrics.get("raw"),
    }
    return status


def flatten_status(prefix: str, status: dict[str, Any]) -> dict[str, object]:
    topics: dict[str, object] = {f"{prefix}/status": status}
    scalar_keys = (
        "running",
        "pressure_bar",
        "flow_m3h",
        "power_w",
        "alarm_code",
        "mode",
    )
    for key in scalar_keys:
        val = status.get(key)
        if val is not None:
            topics[f"{prefix}/{key}"] = val
    dev = status.get("device") or {}
    if dev.get("model"):
        topics[f"{prefix}/device/model"] = dev["model"]
    if dev.get("serial"):
        topics[f"{prefix}/device/serial"] = dev["serial"]
    return topics
