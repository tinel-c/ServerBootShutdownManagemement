#!/usr/bin/env python3
"""Build dist/client-v<VERSION>.zip for GitHub release assets.

Installed Client Monitor copies look for a release asset whose name contains
"client" and ends in .zip. Uploading this archive is what lets every PC
apply the release.
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CLIENT_DIR = REPO_ROOT / "client"
VERSION_FILE = CLIENT_DIR / "VERSION"

INCLUDE = (
    "client_monitor.py",
    "auto_updater.py",
    "fleet_bridge.py",
    "device_catalog.py",
    "tasmota_discover.py",
    "device_fleet_panel.py",
    "update_client_files.bat",
    "install_client.bat",
    "uninstall_client.bat",
    "requirements_client.txt",
    "VERSION",
    "README_CLIENT.md",
    "README_AUTO_UPDATE.md",
    "config/client_config.yaml",
    "config/device_fleet.yaml",
    "config/.env.example",
)


def client_version() -> str:
    text = VERSION_FILE.read_text(encoding="utf-8").strip().lstrip("vV")
    if not text:
        raise SystemExit(f"Empty version file: {VERSION_FILE}")
    return text


def build_client_zip(dest: Path) -> Path:
    """Zip the Windows client at the archive root (update_client_files.bat at top)."""
    missing = [name for name in INCLUDE if not (CLIENT_DIR / name).is_file()]
    if missing:
        raise SystemExit("Client package is missing: " + ", ".join(missing))
    fleet = REPO_ROOT / "scripts" / "status" / "device_fleet.py"
    if not fleet.is_file():
        raise SystemExit(f"Missing {fleet}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in INCLUDE:
            archive.write(CLIENT_DIR / name, name.replace("\\", "/"))
        archive.write(fleet, "device_fleet.py")
    return dest


def main() -> int:
    version = client_version()
    dest = REPO_ROOT / "dist" / f"client-v{version}.zip"
    build_client_zip(dest)
    print(dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
