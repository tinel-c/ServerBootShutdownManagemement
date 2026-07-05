#!/usr/bin/env python3
"""
SSH wrapper for remote Linux server management (graceful shutdown, reachability).
"""

import subprocess
from typing import Optional, Tuple
from logger import get_logger

logger = get_logger(__name__)


class SSHError(Exception):
    """Custom exception for SSH-related errors."""
    pass


class SSHWrapper:
    """Wrapper for SSH operations to a remote Linux host."""

    def __init__(
        self,
        host: str,
        user: str,
        key_path: Optional[str] = None,
        port: int = 22,
        connect_timeout: int = 10,
    ):
        self.host = host
        self.user = user
        self.key_path = key_path
        self.port = port
        self.connect_timeout = connect_timeout
        logger.info(f"SSH wrapper initialized for {user}@{host}")

    def _base_command(self) -> list:
        cmd = [
            "ssh",
            "-o", "BatchMode=yes",
            "-o", f"ConnectTimeout={self.connect_timeout}",
            "-o", "StrictHostKeyChecking=accept-new",
            "-p", str(self.port),
        ]
        if self.key_path:
            cmd.extend(["-i", self.key_path])
        cmd.append(f"{self.user}@{self.host}")
        return cmd

    def _run_remote(self, remote_command: str, timeout: int = 30) -> Tuple[bool, str, str]:
        full_command = self._base_command() + [remote_command]
        log_target = f"{self.user}@{self.host}"
        logger.debug(f"SSH remote command on {log_target}: {remote_command}")
        try:
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            logger.error(f"SSH command timed out on {log_target}")
            return False, "", "timeout"
        except FileNotFoundError:
            raise SSHError("ssh client not found in PATH")
        except Exception as e:
            logger.error(f"SSH command failed on {log_target}: {e}")
            return False, "", str(e)

    def is_reachable(self) -> bool:
        """Return True if SSH login succeeds."""
        success, _, _ = self._run_remote("echo ok", timeout=self.connect_timeout + 5)
        return success

    def graceful_shutdown(self, delay_minutes: int = 0) -> bool:
        """
        Initiate graceful OS shutdown via SSH.

        Requires passwordless sudo for shutdown on the remote host.
        """
        if delay_minutes > 0:
            remote = f"sudo shutdown -h +{delay_minutes}"
        else:
            remote = "sudo shutdown -h now"
        success, stdout, stderr = self._run_remote(remote, timeout=30)
        if success:
            logger.info(f"Graceful shutdown initiated on {self.host}")
            return True
        logger.error(f"Graceful shutdown failed on {self.host}: {stderr or stdout}")
        return False

    def get_uptime(self) -> Optional[str]:
        """Return uptime string from remote host, or None on failure."""
        success, stdout, _ = self._run_remote("uptime -p 2>/dev/null || uptime", timeout=15)
        return stdout if success and stdout else None

    def get_power_status(self) -> str:
        """
        Infer power status from SSH reachability.

        Returns 'on' if SSH responds, 'off' otherwise (compatible with IPMI wrapper API).
        """
        return "on" if self.is_reachable() else "off"

    def power_on(self) -> bool:
        """Not supported over SSH — use Tuya PCIe card."""
        logger.warning("SSH cannot power on hardware; use Tuya boot method")
        return False

    def power_off(self, force: bool = False) -> bool:
        """Graceful shutdown when force=False; not a hard power cut."""
        if force:
            logger.warning("SSH cannot force power off; use Tuya power_off")
            return False
        return self.graceful_shutdown()

    def wait_for_power_state(self, target_state: str, timeout: int = 120, interval: int = 5) -> bool:
        """Wait until SSH reachability matches target on/off state."""
        import time

        deadline = time.time() + timeout
        want_on = target_state.lower() == "on"
        while time.time() < deadline:
            is_on = self.is_reachable()
            if want_on and is_on:
                return True
            if not want_on and not is_on:
                return True
            time.sleep(interval)
        return False


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: ssh_wrapper.py <host> [user]")
        sys.exit(1)
    host = sys.argv[1]
    user = sys.argv[2] if len(sys.argv) > 2 else "tinel"
    wrapper = SSHWrapper(host=host, user=user)
    print(f"Reachable: {wrapper.is_reachable()}")
    print(f"Power status: {wrapper.get_power_status()}")
