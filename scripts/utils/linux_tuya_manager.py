#!/usr/bin/env python3
"""
Composite server manager for Linux hosts with Tuya PCIe power cards.
Combines SSH (graceful shutdown / reachability) and Tuya (boot/reset).
"""

from typing import Any, Dict, Optional
from logger import get_logger
from ssh_wrapper import SSHWrapper
from tuya_pc_power_wrapper import TuyaPCPowerWrapper

logger = get_logger(__name__)


class LinuxTuyaManager:
    """Unified interface for linux_tuya server type."""

    def __init__(self, ssh: SSHWrapper, tuya: TuyaPCPowerWrapper):
        self.ssh = ssh
        self.tuya = tuya

    def get_power_status(self) -> str:
        """Prefer SSH reachability; fall back to Tuya relay status."""
        ssh_status = self.ssh.get_power_status()
        if ssh_status == "on":
            return "on"
        tuya_status = self.tuya.get_power_status()
        if tuya_status in ("on", "off"):
            return tuya_status
        return ssh_status

    def power_on(self) -> bool:
        return self.tuya.power_on()

    def power_off(self, force: bool = False) -> bool:
        if force:
            return self.tuya.power_off(force=True)
        return self.ssh.graceful_shutdown()

    def reset(self) -> bool:
        return self.tuya.reset()

    def force_reset(self) -> bool:
        return self.tuya.force_reset()

    def wait_for_power_state(self, target_state: str, timeout: int = 120, interval: int = 5) -> bool:
        """Wait for SSH (when turning on) or SSH down (when shutting down)."""
        if target_state.lower() == "on":
            if self.ssh.wait_for_power_state("on", timeout=timeout, interval=interval):
                return True
            return self.tuya.wait_for_power_state("on", timeout=max(30, timeout // 4), interval=interval)
        return self.ssh.wait_for_power_state("off", timeout=timeout, interval=interval)

    def is_reachable(self) -> bool:
        return self.ssh.is_reachable()

    def graceful_shutdown(self) -> bool:
        return self.ssh.graceful_shutdown()

    def get_uptime(self) -> Optional[str]:
        return self.ssh.get_uptime()


def build_linux_tuya_manager(server_config: Dict[str, Any]) -> LinuxTuyaManager:
    """Create LinuxTuyaManager from server_config ssh + tuya blocks."""
    ssh_cfg = server_config.get("ssh", {})
    tuya_cfg = server_config.get("tuya", {})

    dps_map = {}
    for key, cfg_key in (
        ("power", "dps_power"),
        ("reset", "dps_reset"),
        ("force_reset", "dps_force_reset"),
        ("status", "dps_status"),
    ):
        val = tuya_cfg.get(cfg_key)
        if val and not str(val).startswith("${"):
            dps_map[key] = str(val)

    ssh = SSHWrapper(
        host=ssh_cfg.get("host"),
        user=ssh_cfg.get("user", "tinel"),
        key_path=ssh_cfg.get("key_path"),
        port=int(ssh_cfg.get("port", 22)),
    )
    tuya = TuyaPCPowerWrapper(
        device_id=tuya_cfg.get("device_id"),
        local_key=tuya_cfg.get("local_key"),
        ip=tuya_cfg.get("ip"),
        version=str(tuya_cfg.get("version", "3.3")),
        dps_map=dps_map or None,
        pulse_seconds=float(tuya_cfg.get("pulse_seconds", 0.5)),
    )
    return LinuxTuyaManager(ssh=ssh, tuya=tuya)
