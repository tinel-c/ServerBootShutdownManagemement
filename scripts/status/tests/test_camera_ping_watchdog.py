"""Unit tests for camera_ping_watchdog helpers."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

STATUS = Path(__file__).resolve().parents[1]
UTILS = STATUS.parent / "utils"
sys.path.insert(0, str(STATUS))
sys.path.insert(0, str(UTILS))

# Avoid importing real MQTT/config when loading the module under test.
for name in (
    "mqtt_client",
    "config_loader",
    "logger",
    "camera_probe",
    "tapo_snapshot",
):
    sys.modules.setdefault(name, MagicMock())

spec = importlib.util.spec_from_file_location(
    "camera_ping_watchdog",
    STATUS / "camera_ping_watchdog.py",
)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)
ping_host = mod.ping_host


def test_ping_host_success():
    with patch.object(mod.subprocess, "run") as run:
        run.return_value = None
        assert ping_host("192.168.2.34", count=1, timeout_sec=1) is True
        run.assert_called_once()


def test_ping_host_failure():
    with patch.object(
        mod.subprocess, "run", side_effect=subprocess.CalledProcessError(1, "ping")
    ):
        assert ping_host("192.168.2.34") is False
