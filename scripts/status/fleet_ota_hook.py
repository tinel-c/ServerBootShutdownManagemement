"""
Shared PlatformIO post-build hook for fleet ArduinoOTA.

Every PlatformIO device repo calls this from scripts/ota_after_build.py:

    from fleet_ota_hook import register
    register(env, "PlatformIO_…")

When the firmware tree is a submodule of this monorepo, a successful build runs:

    python scripts/status/device_fleet.py flash --id <device id> --bin firmware.bin

A standalone clone (no monorepo parent) leaves the .bin in place.
Offline, missing IP, or flash disabled in the registry is a soft success
(exit 0) so a UART upload can continue. A failed espota to a live device
fails the post step. SKIP_FLEET_OTA=1 skips the fleet tool.

The fleet tool needs PyYAML and paho-mqtt. PlatformIO's own Python does not
ship them, so a new PC falls through to that interpreter and the post step
crashes. This hook prefers a system Python, installs the two packages into
the first interpreter that can run pip, and leaves the .bin in place when
that install cannot run.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

FLEET_PROBE = "import yaml, paho.mqtt.client"
FLEET_PACKAGES = ("pyyaml>=6.0", "paho-mqtt>=1.6.1")
PIP_TIMEOUT_SEC = 180


def _is_py_launcher(path: str) -> bool:
    name = Path(path).name.lower()
    return name in ("py", "py.exe")


def _is_platformio_python(path: str) -> bool:
    lowered = path.replace("\\", "/").lower()
    return "/.platformio/" in lowered


def _candidate_prefixes(which, executable: str) -> list:
    """System interpreters first; PlatformIO's penv last.

    ``which`` is shutil.which (or a test double). ``executable`` is the
    interpreter that is running this hook, usually PlatformIO's penv.
    """
    raw = []
    for name in ("py", "python", "python3"):
        found = which(name)
        if found:
            raw.append(found)
    if executable:
        raw.append(executable)

    system = []
    platformio = []
    seen = set()
    for path in raw:
        key = os.path.normcase(os.path.normpath(path))
        if key in seen:
            continue
        seen.add(key)
        argv = [path, "-3"] if _is_py_launcher(path) else [path]
        if _is_platformio_python(path):
            platformio.append(argv)
        else:
            system.append(argv)
    return system + platformio


def _probe(prefix: list) -> str:
    """Return 'ready', 'missing', or 'dead' for this interpreter argv."""
    try:
        completed = subprocess.run(
            prefix + ["-c", FLEET_PROBE],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return "dead"
    if completed.returncode == 0:
        return "ready"
    # ImportError exits 1. The Windows Store python stub and a missing
    # py launcher exit with other codes and must not receive pip.
    if completed.returncode == 1:
        return "missing"
    return "dead"


def _pip_install(prefix: list) -> bool:
    cmd = list(prefix) + [
        "-m",
        "pip",
        "install",
        "--disable-pip-version-check",
        *FLEET_PACKAGES,
    ]
    print("ota_after_build:", " ".join(cmd))
    try:
        completed = subprocess.run(cmd, check=False, timeout=PIP_TIMEOUT_SEC)
    except (OSError, subprocess.TimeoutExpired) as exc:
        print("ota_after_build: pip failed: {}".format(exc))
        return False
    return completed.returncode == 0


def _python_cmd() -> list:
    """Interpreter argv for device_fleet.py, or empty when none can be prepared."""
    ranked_missing = []
    for prefix in _candidate_prefixes(shutil.which, sys.executable):
        state = _probe(prefix)
        if state == "ready":
            return prefix
        if state == "missing":
            ranked_missing.append(prefix)
    for prefix in ranked_missing:
        print(
            "ota_after_build: installing PyYAML and paho-mqtt for fleet OTA ({})".format(
                prefix[0]
            )
        )
        if _pip_install(prefix) and _probe(prefix) == "ready":
            return prefix
    return []


def register(env, device_id: str) -> None:
    """Attach the fleet flash post-action to env (PlatformIO SCons environment)."""

    def after_build(source, target, env):  # noqa: ARG001
        firmware = Path(str(target[0]))
        if not firmware.is_absolute():
            firmware = Path(env["PROJECT_DIR"]).resolve() / firmware
        firmware = firmware.resolve()
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
        if not cmd:
            print(
                "ota_after_build: PyYAML and paho-mqtt are missing and could not "
                "be installed; leaving {} for a later flash".format(firmware)
            )
            print(
                'ota_after_build: py -3 -m pip install "pyyaml>=6.0" "paho-mqtt>=1.6.1"'
            )
            return
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
