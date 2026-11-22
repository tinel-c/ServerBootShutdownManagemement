#!/usr/bin/env python3
"""Roll Client Monitor out to every PC that already has it installed.

Strategy
--------
Each PC pulls the newest GitHub release on its own. There is no central
installer push and no shared database of PCs.

1. Set client/VERSION to the release number (it must match the git tag).
2. Publish the release. scripts/release/create_release.ps1 builds
   dist/client-vX.Y.Z.zip and uploads it. Installed copies (including 3.11.2)
   download any asset whose name contains "client" and ends in .zip, then run
   update_client_files.bat. .env is left in place.
3. Wake PCs that are online now so they do not wait for the 24 hour timer::

       python scripts/client/deploy_client_update.py --notify

   That publishes clients/all/command/update on the automation broker.
   Each client also subscribes to clients/<id>/command/update.
4. See who is running which build::

       python scripts/client/deploy_client_update.py --status

   Presence and clients/<id>/update include the version after this build.
   PCs still on the previous updater show a version only after they install
   this release (their presence payload did not include it).

PCs that are off or logged out update the next time the scheduled task
starts Client Monitor and the check interval has elapsed. The task runs
at logon with highest privileges, which is what the file copy into
Program Files needs.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "release"))

from package_client import build_client_zip, client_version  # noqa: E402


def _broker(host: Optional[str], port: Optional[int]) -> Tuple[str, int]:
    return (
        host or os.environ.get("MQTT_BROKER_HOST") or "192.168.2.4",
        int(port or os.environ.get("MQTT_BROKER_PORT") or 1883),
    )


def _client():
    import paho.mqtt.client as mqtt

    if hasattr(mqtt, "CallbackAPIVersion"):
        return mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"client-deploy-{os.getpid()}")
    return mqtt.Client(client_id=f"client-deploy-{os.getpid()}")


def notify(host: str, port: int) -> None:
    client = _client()
    client.connect(host, port, keepalive=30)
    payload = json.dumps({"action": "now", "requested_by": "deploy_client_update"})
    client.publish("clients/all/command/update", payload, qos=1)
    client.loop(timeout=2.0)
    client.disconnect()
    print(f"Published clients/all/command/update on {host}:{port}")


def status(host: str, port: int, wait_sec: float) -> None:
    import paho.mqtt.client as mqtt

    rows: Dict[str, Dict[str, str]] = {}

    def on_message(_client, _userdata, msg) -> None:
        try:
            data = json.loads(msg.payload.decode("utf-8", errors="replace"))
        except json.JSONDecodeError:
            return
        if not isinstance(data, dict):
            return
        client_id = str(data.get("client_id") or "")
        parts = msg.topic.split("/")
        if not client_id and len(parts) >= 2:
            client_id = parts[1]
        if not client_id or client_id == "all":
            return
        row = rows.setdefault(client_id, {"id": client_id, "status": "", "version": "", "latest": "", "hostname": ""})
        if data.get("hostname"):
            row["hostname"] = str(data["hostname"])
        if data.get("status"):
            row["status"] = str(data["status"])
        version = data.get("version") or data.get("current_version")
        if version:
            row["version"] = str(version)
        if data.get("latest"):
            row["latest"] = str(data["latest"])

    client = _client()
    client.on_message = on_message
    client.connect(host, port, keepalive=30)
    client.subscribe("clients/+/presence", qos=0)
    client.subscribe("clients/+/update", qos=0)
    client.subscribe("clients/+/heartbeat", qos=0)
    client.loop_start()
    time.sleep(wait_sec)
    client.loop_stop()
    client.disconnect()
    if not rows:
        print(f"No client messages on {host}:{port} in {wait_sec:.0f}s")
        return
    print(f"{'client':<28} {'host':<20} {'status':<10} {'version':<12} latest")
    for row in sorted(rows.values(), key=lambda item: item["id"]):
        print(
            f"{row['id']:<28} {row['hostname']:<20} {row['status']:<10} "
            f"{row['version'] or '-':<12} {row['latest'] or '-'}"
        )


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Package and wake Client Monitor installs")
    parser.add_argument("--package", action="store_true", help="Write dist/client-v<VERSION>.zip")
    parser.add_argument("--notify", action="store_true", help="Tell online PCs to check GitHub now")
    parser.add_argument("--status", action="store_true", help="List client versions seen on MQTT")
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--wait", type=float, default=20.0, help="Seconds to listen for --status")
    args = parser.parse_args(argv)
    if not (args.package or args.notify or args.status):
        args.package = True
        args.status = True
    if args.package:
        version = client_version()
        dest = build_client_zip(REPO_ROOT / "dist" / f"client-v{version}.zip")
        print(f"Package: {dest}")
        print("Upload with the release: gh release upload v{0} {1}".format(version, dest))
    host, port = _broker(args.host, args.port)
    if args.notify:
        notify(host, port)
    if args.status:
        status(host, port, args.wait)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
