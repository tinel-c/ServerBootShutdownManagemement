#!/usr/bin/env python3
"""Read-only Modbus TCP probe for Huawei SUN2000 (WiFi AP or SDongle LAN)."""

from __future__ import annotations

import socket
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

from huawei_modbus import HuaweiModbusReader, load_huawei_config  # noqa: E402


def main() -> int:
    config = load_huawei_config()
    if not config.host:
        print("Error: HUAWEI_INVERTER_HOST not set in config/.env")
        return 1

    if config.wifi_ssid:
        print(f"WiFi AP: {config.wifi_ssid}")
        if config.wifi_iface:
            print(f"  Server interface: {config.wifi_iface}")
        print()

    print(f"Inverter Modbus: {config.host}:{config.port} (unit {config.unit_id})")
    try:
        with socket.create_connection((config.host, config.port), timeout=5):
            print("  TCP connection OK\n")
    except OSError as exc:
        print(f"  TCP connection FAILED ({exc})")
        print(
            "\nHint: connect the server USB WiFi to the inverter AP, then verify "
            "192.168.200.1 is reachable on that interface."
        )
        return 1

    reader = HuaweiModbusReader(config)
    if not reader.connect():
        print("  Modbus client connect FAILED")
        return 1

    try:
        m = reader.read_metrics()
    finally:
        reader.close()

    dev = m["device"]
    pv = m["pv"]
    inv = m["inverter"]

    print("--- Device ---")
    print(f"  Model:  {dev['model'] or 'n/a'}")
    print(f"  Serial: {dev['serial'] or 'n/a'}")
    if dev["rated_power_w"] is not None:
        print(f"  Rated:  {dev['rated_power_w']} W")
    print()

    print("--- PV strings ---")
    print(f"  PV1: {pv['string1_voltage_v']} V / {pv['string1_current_a']} A")
    print(f"  PV2: {pv['string2_voltage_v']} V / {pv['string2_current_a']} A")
    print(f"  Input power (DC): {pv['input_power_w']} W\n")

    print("--- Inverter output ---")
    print(f"  Active power:     {inv['active_power_w']} W")
    print(f"  Grid frequency:   {inv['grid_frequency_hz']} Hz")
    print(f"  Daily yield:      {inv['daily_yield_kwh']} kWh")

    return 0


if __name__ == "__main__":
    sys.exit(main())
