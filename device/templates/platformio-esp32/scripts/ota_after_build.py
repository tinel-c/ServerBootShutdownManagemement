"""
Copy this file to a PlatformIO device repo as scripts/ota_after_build.py.
Set DEVICE_ID to the fleet id (same string as MQTT client id and status "device").

Requires in platformio.ini:

    upload_protocol = esptool
    extra_scripts =
        post:scripts/ota_after_build.py

The hook lives in the monorepo at scripts/status/fleet_ota_hook.py.
A standalone clone of the device repo skips OTA and keeps firmware.bin.
"""

Import("env")  # type: ignore[name-defined]  # noqa: F821 — PlatformIO injects this

import sys
from pathlib import Path

DEVICE_ID = "REPLACE_WITH_FLEET_ID"


def _standalone(source, target, env):  # noqa: ARG001
    print(
        "ota_after_build: fleet hook not found (not a monorepo submodule); "
        "leaving {}".format(target[0])
    )


project_dir = Path(env["PROJECT_DIR"]).resolve()  # type: ignore[name-defined]
hook_dir = project_dir.parent.parent / "scripts" / "status"
hook = hook_dir / "fleet_ota_hook.py"
if hook.is_file() and DEVICE_ID != "REPLACE_WITH_FLEET_ID":
    sys.path.insert(0, str(hook_dir))
    from fleet_ota_hook import register

    register(env, DEVICE_ID)  # type: ignore[name-defined]
else:
    if DEVICE_ID == "REPLACE_WITH_FLEET_ID":
        print("ota_after_build: set DEVICE_ID before flashing via the fleet")
    env.AddPostAction("$BUILD_DIR/${PROGNAME}.bin", _standalone)  # type: ignore[name-defined]
