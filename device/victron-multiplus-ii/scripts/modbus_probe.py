#!/usr/bin/env python3
"""Read-only Modbus TCP probe for Victron Cerbo GX / MultiPlus-II."""

from __future__ import annotations

import socket
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

from victron_modbus import load_victron_config, VictronModbusReader  # noqa: E402


def main() -> int:
    config = load_victron_config()
    if not config.gx_host:
        print("Error: VICTRON_GX_HOST not set in config/.env")
        return 1

    print(f"Cerbo GX: {config.gx_host}:{config.gx_port}")
    try:
        with socket.create_connection((config.gx_host, config.gx_port), timeout=3):
            print("  TCP connection OK\n")
    except OSError:
        print("  TCP connection FAILED\n")
        return 1

    reader = VictronModbusReader(config)
    if not reader.connect():
        print("  Modbus client connect FAILED")
        return 1

    try:
        m = reader.read_metrics()
    finally:
        reader.close()

    print("--- System / Battery & Grid ---")
    print(f"  Battery voltage: {m['battery']['voltage_v']} V")
    print(f"  Battery SoC:     {m['battery']['soc_pct']} %")
    print(f"  Battery power:   {m['battery']['power_w']} W")
    print(f"  Grid L1 power:   {m['grid']['power_l1_w']} W\n")

    print("--- System / PV (aggregate) ---")
    print(f"  DC PV power (all MPPT): {m['pv']['dc_power_w']} W")
    print(f"  DC PV current:          {m['pv']['dc_current_a']} A")
    print(f"  AC PV on output L1:     {m['pv']['ac_output_l1_w']} W")
    print(f"  AC PV on grid L1:       {m['pv']['ac_grid_l1_w']} W\n")

    print("--- System / AC loads ---")
    print(f"  AC consumption L1:           {m['load']['consumption_l1_w']} W")
    print(f"  AC load on inverter output L1: {m['load']['output_l1_w']} W")
    print(f"  AC load on AC input L1:      {m['load']['input_l1_w']} W\n")

    if m["solar_charger"]:
        s = m["solar_charger"]
        print(f"--- Solar charger (MPPT) unit {s['unit_id']} ---")
        print(f"  PV panel voltage: {s['pv_voltage_v']} V")
        print(f"  Charge current:   {s['charge_current_a']} A")
        print(f"  PV power:         {s['pv_power_w']} W")
        print(f"  Yield today:      {s['yield_today_kwh']} kWh")
        print(f"  Charger state:    {s['state']}\n")
    else:
        print("--- Solar charger (MPPT) ---")
        print("  Not found — set VICTRON_SOLARCHARGER_UNIT_ID or connect MPPT\n")

    if m["pv_inverter"]:
        p = m["pv_inverter"]
        print(f"--- PV inverter unit {p['unit_id']} ---")
        print(f"  AC power L1:   {p['ac_power_l1_w']} W")
        print(f"  AC voltage L1: {p['ac_voltage_l1_v']} V")
        print(f"  AC current L1: {p['ac_current_l1_a']} A")
        print(f"  Position:      {p['position']}\n")
    else:
        print("--- PV inverter ---")
        print("  Skipped — set VICTRON_PVINVERTER_UNIT_ID if connected\n")

    print("--- VE.Bus / MultiPlus-II ---")
    inv = m["inverter"]
    print(f"  AC input voltage L1: {inv['ac_in_voltage_l1_v']} V")
    print(f"  AC input power L1:   {inv['ac_in_power_l1_w']} W")
    print(f"  AC output power L1:  {inv['ac_out_power_l1_w']} W")
    print(f"  DC voltage:          {inv['dc_voltage_v']} V")
    print(f"  Inverter state:      {inv['state']}")
    print(f"  Grid lost alarm:     {'Alarm' if inv['grid_lost'] else 'No alarm'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
