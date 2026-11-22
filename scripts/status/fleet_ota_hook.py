"""
Shared PlatformIO post-build hook for fleet ArduinoOTA.

Every PlatformIO device repo calls this from scripts/ota_after_build.py:

    from fleet_ota_hook import register
    register(env, "PlatformIO_…")

When the firmware tree is a submodule of this monorepo, a successful build runs:

    python scripts/status/device_fleet.py flash --id <device id> --bin firmware.bin

A standalone clone (no monorepo parent) leaves the .bin in place.
Offline or missing IP is a soft success (exit 0). A failed espota to a live
device fails the post step. SKIP_FLEET_OTA=1 skips the fleet tool.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def _is_py_launcher(path: str) -> bool:
    name = Path(path).name.lower()
    return name in ("py", "py.exe")


def _python_cmd() -> list:
    """Prefer a system Python that already has PyYAML and paho-mqtt."""
    for candidate in (
        shutil.which("py"),
        shutil.which("python"),
        shutil.which("python3"),
        sys.executable,
    ):
        if not candidate:
            continue
        probe = [candidate]
        if _is_py_launcher(candidate):
            probe = [candidate, "-3"]
        probe.extend(["-c", "import yaml, paho.mqtt.client"])
        try:
            completed = subprocess.run(
                probe,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            if completed.returncode == 0:
                return probe[:-2]
        except OSError:
            continue
    return [sys.executable]


def register(env, device_id: str) -> None:
    """Attach the fleet flash post-action to env (PlatformIO SCons environment)."""

    def after_build(source, target, env):  # noqa: ARG001
        firmware = Path(str(target[0]))
        if os.environ.get("SKIP_FLEET_OTA") == "1":
            print("ota_after_build: SKIP_FLEET_OTA=1 — leaving {}".format(firmware))
            return
        project_dir = Path(env["PROJECT_DIR"]).resolve()
        monorepo = project_dir.parent.parent
        fleet = monorepo / "scripts" / "status" / "device_fleet.py"
        if not fleet.is_file():
            print(
                "ota_after_build: fleet tool not found at {}; "
                "leaving {} for a later flash".format(fleet, firmware)
            )
            return

        cmd = _python_cmd()
        cmd.extend(
            [
                str(fleet),
                "flash",
                "--id",
                device_id,
                "--bin",
                str(firmware),
            ]
        )
        print("ota_after_build:", " ".join(cmd))
        completed = subprocess.run(cmd, cwd=str(monorepo), check=False)
        if completed.returncode != 0:
            sys.exit(completed.returncode)

    env.AddPostAction("$BUILD_DIR/${PROGNAME}.bin", after_build)
