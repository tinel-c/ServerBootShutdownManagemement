"""Modbus TCP reader for Victron Cerbo GX / MultiPlus-II."""

from __future__ import annotations

import inspect
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pymodbus.client import ModbusTcpClient

INVERTER_STATES = {
    0: "Off",
    1: "Low Power",
    2: "Fault",
    3: "Bulk",
    4: "Absorption",
    5: "Float",
    6: "Storage",
    7: "Equalize",
    8: "Passthru",
    9: "Inverting",
    10: "Power assist",
    11: "Power supply",
    252: "External control",
}

SOLAR_CHARGER_STATES = {
    0: "Off",
    2: "Fault",
    3: "Bulk",
    4: "Absorption",
    5: "Float",
    6: "Storage",
    7: "Equalize",
    11: "Other (Hub-1)",
    252: "Hub-1",
}

SOLAR_UNIT_CANDIDATES = [226, 224, 223, 247]


@dataclass
class VictronConfig:
    gx_host: str
    gx_port: int = 502
    vebus_unit: int = 227
    system_unit: int = 100
    solar_unit: str = ""
    pv_inverter_unit: str = ""


def load_victron_config(config_dir: Path | None = None) -> VictronConfig:
    if config_dir is None:
        config_dir = Path(__file__).resolve().parent.parent / "config"
    load_dotenv(config_dir / ".env")
    return VictronConfig(
        gx_host=os.getenv("VICTRON_GX_HOST", ""),
        gx_port=int(os.getenv("VICTRON_GX_MODBUS_PORT", "502")),
        vebus_unit=int(os.getenv("VICTRON_VEBUS_UNIT_ID", "227")),
        system_unit=int(os.getenv("VICTRON_SYSTEM_UNIT_ID", "100")),
        solar_unit=os.getenv("VICTRON_SOLARCHARGER_UNIT_ID", "").strip(),
        pv_inverter_unit=os.getenv("VICTRON_PVINVERTER_UNIT_ID", "").strip(),
    )


def to_signed16(value: int) -> int:
    return value - 65536 if value >= 32768 else value


def _unit_kw(client: ModbusTcpClient, unit_id: int) -> dict[str, int]:
    params = inspect.signature(client.read_input_registers).parameters
    if "device_id" in params:
        return {"device_id": unit_id}
    return {"slave": unit_id}


class VictronModbusReader:
    def __init__(self, config: VictronConfig):
        self.config = config
        self._client: ModbusTcpClient | None = None
        self._solar_unit: int | None = None

    def connect(self) -> bool:
        if not self.config.gx_host:
            raise ValueError("VICTRON_GX_HOST is not set")
        self._client = ModbusTcpClient(self.config.gx_host, port=self.config.gx_port)
        return bool(self._client.connect())

    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None

    def _reg(self, unit_id: int, address: int) -> int:
        assert self._client is not None
        result = self._client.read_input_registers(
            address, count=1, **_unit_kw(self._client, unit_id)
        )
        if result.isError():
            raise RuntimeError(f"unit {unit_id} register {address}: {result}")
        return result.registers[0]

    def _reg_s16(self, unit_id: int, address: int) -> int:
        return to_signed16(self._reg(unit_id, address))

    def _reg_s32(self, unit_id: int, address: int) -> int:
        assert self._client is not None
        result = self._client.read_input_registers(
            address, count=2, **_unit_kw(self._client, unit_id)
        )
        if result.isError():
            raise RuntimeError(f"unit {unit_id} register {address}: {result}")
        hi, lo = result.registers
        value = (hi << 16) | lo
        if value >= 0x80000000:
            value -= 0x100000000
        return value

    def _read_optional(self, fn, *args) -> Any | None:
        try:
            return fn(*args)
        except RuntimeError:
            return None

    def _find_solar_unit(self) -> int | None:
        if self._solar_unit is not None:
            return self._solar_unit
        candidates: list[int] = []
        if self.config.solar_unit:
            candidates.append(int(self.config.solar_unit))
        for unit_id in SOLAR_UNIT_CANDIDATES:
            if unit_id not in candidates:
                candidates.append(unit_id)
        for unit_id in candidates:
            if self._read_optional(self._reg, unit_id, 789) is not None:
                self._solar_unit = unit_id
                return unit_id
        return None

    def read_metrics(self) -> dict[str, Any]:
        cfg = self.config
        metrics: dict[str, Any] = {
            "battery": {
                "voltage_v": round(self._reg(cfg.system_unit, 840) * 0.1, 1),
                "soc_pct": self._reg(cfg.system_unit, 843),
                "power_w": self._reg_s16(cfg.system_unit, 842),
            },
            "grid": {
                "power_l1_w": self._reg_s16(cfg.system_unit, 820),
            },
            "pv": {
                "dc_power_w": self._reg(cfg.system_unit, 850),
                "dc_current_a": round(self._reg_s16(cfg.system_unit, 851) * 0.1, 1),
                "ac_output_l1_w": self._reg(cfg.system_unit, 808),
                "ac_grid_l1_w": self._reg(cfg.system_unit, 811),
            },
            "load": {
                "consumption_l1_w": self._reg(cfg.system_unit, 817),
                "output_l1_w": self._reg_s32(cfg.system_unit, 878),
                "input_l1_w": self._reg_s32(cfg.system_unit, 872),
            },
            "inverter": {
                "ac_in_voltage_l1_v": round(self._reg(cfg.vebus_unit, 3) * 0.1, 1),
                "ac_in_power_l1_w": round(self._reg_s16(cfg.vebus_unit, 12) * 0.1),
                "ac_out_power_l1_w": round(self._reg_s16(cfg.vebus_unit, 23) * 0.1),
                "dc_voltage_v": round(self._reg(cfg.vebus_unit, 26) * 0.01, 2),
                "state_code": self._reg(cfg.vebus_unit, 31),
                "grid_lost": self._reg(cfg.vebus_unit, 64) == 2,
            },
            "solar_charger": None,
            "pv_inverter": None,
        }

        state_code = metrics["inverter"]["state_code"]
        metrics["inverter"]["state"] = INVERTER_STATES.get(state_code, str(state_code))

        solar_unit = self._find_solar_unit()
        if solar_unit is not None:
            state_raw = self._read_optional(self._reg, solar_unit, 775)
            metrics["solar_charger"] = {
                "unit_id": solar_unit,
                "pv_voltage_v": round(self._reg(solar_unit, 776) * 0.01, 2),
                "charge_current_a": round(self._reg_s16(solar_unit, 772) * 0.1, 1),
                "pv_power_w": round(self._reg(solar_unit, 789) * 0.1),
                "yield_today_kwh": round(self._reg(solar_unit, 784) * 0.1, 1),
                "state_code": state_raw,
                "state": SOLAR_CHARGER_STATES.get(state_raw, str(state_raw))
                if state_raw is not None
                else None,
            }

        if self.config.pv_inverter_unit:
            unit = int(self.config.pv_inverter_unit)
            pos = self._read_optional(self._reg, unit, 1026)
            pos_labels = {0: "AC input 1", 1: "AC output", 2: "AC input 2"}
            metrics["pv_inverter"] = {
                "unit_id": unit,
                "ac_power_l1_w": self._reg(unit, 1029),
                "ac_voltage_l1_v": round(self._reg(unit, 1027) * 0.1, 1),
                "ac_current_l1_a": round(self._reg_s16(unit, 1028) * 0.1, 1),
                "position": pos_labels.get(pos, pos) if pos is not None else None,
            }

        return metrics
