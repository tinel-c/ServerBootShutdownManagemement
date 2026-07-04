"""Modbus TCP reader for Huawei SUN2000 (WiFi AP or SDongle LAN)."""

from __future__ import annotations

import inspect
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pymodbus.client import ModbusTcpClient


@dataclass
class HuaweiConfig:
    host: str
    port: int = 6607
    unit_id: int = 0
    connect_wait_s: float = 2.0
    wifi_ssid: str = ""
    wifi_iface: str = ""


def load_huawei_config(config_dir: Path | None = None) -> HuaweiConfig:
    if config_dir is None:
        config_dir = Path(__file__).resolve().parent.parent / "config"
    load_dotenv(config_dir / ".env")
    return HuaweiConfig(
        host=os.getenv("HUAWEI_INVERTER_HOST", "192.168.200.1"),
        port=int(os.getenv("HUAWEI_MODBUS_PORT", "6607")),
        unit_id=int(os.getenv("HUAWEI_MODBUS_UNIT_ID", "0")),
        connect_wait_s=float(os.getenv("HUAWEI_MODBUS_CONNECT_WAIT", "2")),
        wifi_ssid=os.getenv("HUAWEI_WIFI_SSID", "").strip(),
        wifi_iface=os.getenv("HUAWEI_WIFI_IFACE", "").strip(),
    )


def _unit_kw(client: ModbusTcpClient, unit_id: int) -> dict[str, int]:
    params = inspect.signature(client.read_holding_registers).parameters
    if "device_id" in params:
        return {"device_id": unit_id}
    return {"slave": unit_id}


def _to_signed16(value: int) -> int:
    return value - 65536 if value >= 32768 else value


def _decode_i32(registers: list[int]) -> int:
    hi, lo = registers[0], registers[1]
    value = (hi << 16) | lo
    if value >= 0x80000000:
        value -= 0x100000000
    return value


def _decode_u32(registers: list[int]) -> int:
    hi, lo = registers[0], registers[1]
    return (hi << 16) | lo


def _decode_string(registers: list[int]) -> str:
    raw = b"".join(reg.to_bytes(2, byteorder="big") for reg in registers)
    return raw.split(b"\x00", 1)[0].decode("ascii", errors="replace").strip()


class HuaweiModbusReader:
    def __init__(self, config: HuaweiConfig):
        self.config = config
        self._client: ModbusTcpClient | None = None

    def connect(self) -> bool:
        if not self.config.host:
            raise ValueError("HUAWEI_INVERTER_HOST is not set")
        self._client = ModbusTcpClient(self.config.host, port=self.config.port)
        if not self._client.connect():
            return False
        if self.config.connect_wait_s > 0:
            time.sleep(self.config.connect_wait_s)
        return True

    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None

    def _holding(self, address: int, count: int = 1) -> list[int]:
        assert self._client is not None
        result = self._client.read_holding_registers(
            address,
            count=count,
            **_unit_kw(self._client, self.config.unit_id),
        )
        if result.isError():
            raise RuntimeError(f"register {address} x{count}: {result}")
        return result.registers

    def _read_optional(self, fn, *args) -> Any | None:
        try:
            return fn(*args)
        except RuntimeError:
            return None

    def read_metrics(self) -> dict[str, Any]:
        model_regs = self._read_optional(self._holding, 30000, 15)
        sn_regs = self._read_optional(self._holding, 30015, 10)
        rated_regs = self._read_optional(self._holding, 30073, 2)

        pv1_v = self._read_optional(lambda: _to_signed16(self._holding(32016)[0]) / 10)
        pv1_a = self._read_optional(lambda: _to_signed16(self._holding(32017)[0]) / 100)
        pv2_v = self._read_optional(lambda: _to_signed16(self._holding(32018)[0]) / 10)
        pv2_a = self._read_optional(lambda: _to_signed16(self._holding(32019)[0]) / 100)

        input_power_w = self._read_optional(lambda: _decode_i32(self._holding(32064, 2)))
        active_power_w = self._read_optional(lambda: _decode_i32(self._holding(32080, 2)))
        grid_hz = self._read_optional(lambda: self._holding(32085)[0] / 100)
        daily_yield_kwh = self._read_optional(
            lambda: _decode_u32(self._holding(32114, 2)) / 100
        )

        return {
            "device": {
                "model": _decode_string(model_regs) if model_regs else None,
                "serial": _decode_string(sn_regs) if sn_regs else None,
                "rated_power_w": _decode_u32(rated_regs) if rated_regs else None,
            },
            "pv": {
                "string1_voltage_v": pv1_v,
                "string1_current_a": pv1_a,
                "string2_voltage_v": pv2_v,
                "string2_current_a": pv2_a,
                "input_power_w": input_power_w,
            },
            "inverter": {
                "active_power_w": active_power_w,
                "grid_frequency_hz": grid_hz,
                "daily_yield_kwh": daily_yield_kwh,
            },
        }
