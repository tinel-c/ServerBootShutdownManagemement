#!/usr/bin/env python3
"""
Tuya PCIe PC power card wrapper (local API via tinytuya).

Controls ATX power/reset simulation and reads relay power status from
Tuya WiFi remote boot cards (e.g. A3 PCIe power switch).
"""

import time
from typing import Any, Dict, Optional
from logger import get_logger

logger = get_logger(__name__)

try:
    import tinytuya
except ImportError:
    tinytuya = None


class TuyaError(Exception):
    """Custom exception for Tuya device errors."""
    pass


class TuyaPCPowerWrapper:
    """Local Tuya API wrapper for PCIe PC power control cards."""

    # Common DPS IDs for A3-style PC power cards (override via config)
    DEFAULT_DPS = {
        "power": "1",
        "reset": "2",
        "force_reset": "3",
        "status": "101",
    }

    def __init__(
        self,
        device_id: str,
        local_key: str,
        ip: str,
        version: str = "3.3",
        dps_map: Optional[Dict[str, str]] = None,
        pulse_seconds: float = 0.5,
    ):
        if tinytuya is None:
            raise TuyaError("tinytuya is not installed; pip install tinytuya")

        self.device_id = device_id
        self.local_key = local_key
        self.ip = ip
        self.version = version
        self.dps_map = {**self.DEFAULT_DPS, **(dps_map or {})}
        self.pulse_seconds = pulse_seconds

        self._device = tinytuya.Device(device_id, ip, local_key, version=version)
        self._device.set_socketPersistent(True)
        logger.info(f"Tuya PC power wrapper initialized for {device_id} @ {ip}")

    def _set_dps(self, dps_id: str, value: Any) -> bool:
        try:
            result = self._device.set_value(dps_id, value)
            if result is False:
                logger.error(f"Tuya set_value failed for DPS {dps_id}")
                return False
            return True
        except Exception as e:
            logger.error(f"Tuya set_value error for DPS {dps_id}: {e}")
            return False

    def _pulse_dps(self, dps_id: str, on_value: Any = True, off_value: Any = False) -> bool:
        """Momentary button press: ON then OFF after pulse_seconds."""
        if not self._set_dps(dps_id, on_value):
            return False
        time.sleep(self.pulse_seconds)
        return self._set_dps(dps_id, off_value)

    def _read_status(self) -> Optional[Dict[str, Any]]:
        try:
            return self._device.status()
        except Exception as e:
            logger.error(f"Tuya status read failed: {e}")
            return None

    def get_power_status(self) -> str:
        """
        Read relay/power status from the card.

        Returns 'on', 'off', or 'unknown'.
        """
        status = self._read_status()
        if not status or "dps" not in status:
            return "unknown"

        dps = status["dps"]
        status_dps = self.dps_map.get("status", "101")
        power_dps = self.dps_map.get("power", "1")

        raw = dps.get(status_dps)
        if raw is None:
            raw = dps.get(power_dps)

        if raw is None:
            return "unknown"
        if raw in (True, "true", "on", "ON", 1, "1"):
            return "on"
        if raw in (False, "false", "off", "OFF", 0, "0"):
            return "off"
        return "unknown"

    def power_on(self) -> bool:
        """Simulate ATX power button press to turn on PC."""
        logger.info("Tuya: power on (ATX pulse)")
        return self._pulse_dps(self.dps_map["power"], on_value=True, off_value=False)

    def power_off(self, force: bool = False) -> bool:
        """
        Simulate ATX power button press.

        When OS is running this triggers ACPI shutdown; when hung, may force off
        depending on motherboard/firmware behavior.
        """
        logger.info(f"Tuya: power off pulse (force={force})")
        return self._pulse_dps(self.dps_map["power"], on_value=True, off_value=False)

    def reset(self) -> bool:
        """Simulate reset button press."""
        logger.info("Tuya: reset pulse")
        reset_dps = self.dps_map.get("reset", "2")
        return self._pulse_dps(reset_dps, on_value=True, off_value=False)

    def force_reset(self) -> bool:
        """Simulate force reset (long press / dedicated DPS if available)."""
        logger.info("Tuya: force reset")
        force_dps = self.dps_map.get("force_reset", "3")
        if not self._set_dps(force_dps, True):
            return self.reset()
        time.sleep(3.0)
        return self._set_dps(force_dps, False)

    def wait_for_power_state(self, target_state: str, timeout: int = 120, interval: int = 5) -> bool:
        """Wait until Tuya relay status matches target on/off."""
        deadline = time.time() + timeout
        want_on = target_state.lower() == "on"
        while time.time() < deadline:
            state = self.get_power_status()
            if want_on and state == "on":
                return True
            if not want_on and state == "off":
                return True
            time.sleep(interval)
        return False


if __name__ == "__main__":
    import os
    import sys

    device_id = os.getenv("MEDIA_SERVER_TUYA_DEVICE_ID")
    local_key = os.getenv("MEDIA_SERVER_TUYA_LOCAL_KEY")
    ip = os.getenv("MEDIA_SERVER_TUYA_IP")
    if not all([device_id, local_key, ip]):
        print("Set MEDIA_SERVER_TUYA_DEVICE_ID, MEDIA_SERVER_TUYA_LOCAL_KEY, MEDIA_SERVER_TUYA_IP")
        sys.exit(1)
    wrapper = TuyaPCPowerWrapper(device_id, local_key, ip, version=os.getenv("MEDIA_SERVER_TUYA_VERSION", "3.3"))
    print(f"Status: {wrapper.get_power_status()}")
    print(f"Raw: {wrapper._read_status()}")
