#!/usr/bin/env python3
"""
DEPRECATED — continuous ONVIF monitor removed (overloads cameras / HomeGuard DVR).

Use camera_ping_watchdog.py / camera-ping-watchdog.service instead:
  - ICMP ping → garden/camera/{slug}/health
  - ONVIF snapshot/probe only via MQTT garden/camera/{slug}/command/snapshot|probe

This stub exits immediately so a leftover tapo-monitor.service unit cannot
re-open continuous ONVIF sessions after an incomplete upgrade.
"""

from __future__ import annotations

import sys

print(
    "tapo_monitor.py is retired. "
    "Use camera_ping_watchdog.py (camera-ping-watchdog.service). "
    "See docs/TAPO_CAMERA.md",
    file=sys.stderr,
)
sys.exit(1)
