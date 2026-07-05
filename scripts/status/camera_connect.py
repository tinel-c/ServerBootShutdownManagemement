#!/usr/bin/env python3
"""Test ONVIF connectivity for all configured Tapo cameras."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))
sys.path.insert(0, str(Path(__file__).parent))

from config_loader import get_config
from camera_probe import normalize_mac, probe_onvif
from tapo_snapshot import slug_from_mqtt_prefix


def main() -> int:
    config = get_config()
    cameras = config.get("cameras", [])
    if not cameras:
        print("No cameras configured (CAMERA_N_* in .env).")
        return 1

    print(f"{'Slug':<14} {'Name':<16} {'IP':<15} {'ONVIF':<6} {'MAC ok':<7} Model")
    print("-" * 80)

    failures = 0
    for cam in cameras:
        slug = slug_from_mqtt_prefix(cam.get("mqtt_prefix", ""))
        name = cam.get("name", slug)
        ip = cam.get("ip", "")
        port = int(cam.get("port", 2020))
        expected_mac = normalize_mac(cam.get("mac"))
        probe = probe_onvif(
            ip,
            cam.get("username", ""),
            cam.get("password", ""),
            port=port,
        )
        observed = probe.get("mac_observed")
        mac_ok = "—"
        if expected_mac and observed:
            mac_ok = "yes" if expected_mac == observed else "NO"
        elif expected_mac and not observed:
            mac_ok = "?"
        onvif = "ok" if probe.get("online") else "FAIL"
        model = probe.get("model") or cam.get("model") or "—"
        if not probe.get("online"):
            failures += 1
        err = probe.get("error")
        print(f"{slug:<14} {name:<16} {ip:<15} {onvif:<6} {mac_ok:<7} {model}")
        if err and not probe.get("online"):
            print(f"  └─ {err}")

    print("-" * 80)
    if failures:
        print(f"{failures} camera(s) failed ONVIF probe.")
        return 1
    print("All cameras reachable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
