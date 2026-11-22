#!/usr/bin/env python3
"""
Fleet monitor and OTA flasher for firmware devices under device/.

Commands:
  status  — subscribe briefly and print online/offline + last IP
  watch   — keep refreshing scripts/status/device_fleet_state.json
  flash   — espota a .bin when the sighting is fresh and has an IP

State file is the memory used after a PlatformIO compile:
  scripts/status/device_fleet_state.json
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

try:
    import paho.mqtt.client as mqtt
except ImportError:  # pragma: no cover
    mqtt = None

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
DEFAULT_REGISTRY = SCRIPT_DIR / "device_fleet.yaml"
DEFAULT_STATE = SCRIPT_DIR / "device_fleet_state.json"


def load_registry(path: Path) -> Dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML is required (pip install pyyaml)")
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    devices = data.get("devices") or []
    if not isinstance(devices, list) or not devices:
        raise ValueError(f"No devices listed in {path}")
    return data


def load_state(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"devices": {}}
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        return {"devices": {}}
    data.setdefault("devices", {})
    return data


def save_state(path: Path, state: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, sort_keys=True)
        fh.write("\n")
    tmp.replace(path)


def device_by_id(registry: Dict[str, Any], device_id: str) -> Dict[str, Any]:
    for item in registry.get("devices") or []:
        if item.get("id") == device_id:
            return item
    raise KeyError(f"Unknown device id: {device_id}")


def parse_status_payload(payload: str) -> Dict[str, Any]:
    """Extract optional ip / fw / rssi / ota_port from a status payload."""
    out: Dict[str, Any] = {}
    text = (payload or "").strip()
    if not text:
        return out
    if text[0] == "{":
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return out
        if not isinstance(data, dict):
            return out
        if "ip" in data and data["ip"]:
            out["ip"] = str(data["ip"])
        fw = data.get("fw") or data.get("version") or data.get("firmware")
        if fw:
            out["fw"] = str(fw)
        if "rssi" in data:
            try:
                out["rssi"] = int(data["rssi"])
            except (TypeError, ValueError):
                pass
        if "ota_port" in data:
            try:
                out["ota_port"] = int(data["ota_port"])
            except (TypeError, ValueError):
                pass
        return out
    return out


def record_sighting(
    state: Dict[str, Any],
    device_id: str,
    payload: str,
    *,
    now: Optional[float] = None,
    default_ota_port: int = 3232,
) -> Dict[str, Any]:
    """Update one device entry from a live MQTT status message."""
    when = float(now if now is not None else time.time())
    parsed = parse_status_payload(payload)
    devices = state.setdefault("devices", {})
    entry = dict(devices.get(device_id) or {})
    entry["last_seen"] = when
    entry["last_payload"] = payload[:500]
    if "ip" in parsed:
        entry["ip"] = parsed["ip"]
    if "fw" in parsed:
        entry["fw"] = parsed["fw"]
    if "rssi" in parsed:
        entry["rssi"] = parsed["rssi"]
    entry["ota_port"] = int(parsed.get("ota_port") or entry.get("ota_port") or default_ota_port)
    devices[device_id] = entry
    return entry


def is_online(entry: Optional[Dict[str, Any]], timeout_sec: int, *, now: Optional[float] = None) -> bool:
    if not entry:
        return False
    last = entry.get("last_seen")
    if last is None:
        return False
    when = float(now if now is not None else time.time())
    return (when - float(last)) <= float(timeout_sec)


def flash_decision(
    entry: Optional[Dict[str, Any]],
    device_cfg: Dict[str, Any],
    *,
    now: Optional[float] = None,
) -> Tuple[bool, str]:
    """Return (ok_to_flash, reason)."""
    if not device_cfg.get("flash"):
        return False, "flash disabled for this device"
    timeout = int(device_cfg.get("timeout_sec") or 90)
    if not is_online(entry, timeout, now=now):
        return False, "device offline or sighting stale"
    if not entry or not entry.get("ip"):
        return False, "no IP in state (device must publish ip in status)"
    return True, "ok"


def find_espota() -> Path:
    home = Path(os.environ.get("PLATFORMIO_CORE_DIR", Path.home() / ".platformio"))
    candidates = [
        home / "packages" / "tool-esptoolpy" / "espota.py",
        home / "packages" / "framework-arduinoespressif32" / "tools" / "espota.py",
    ]
    # PlatformIO also keeps espota next to the Arduino package tools on some installs.
    packages = home / "packages"
    if packages.is_dir():
        for path in packages.rglob("espota.py"):
            candidates.append(path)
    for path in candidates:
        if path.is_file():
            return path
    raise FileNotFoundError(
        "espota.py not found under ~/.platformio/packages. Install PlatformIO and build once."
    )


def guess_host_ip(remote_ip: str) -> Optional[str]:
    """Local IPv4 used to reach remote_ip (espota -I). Avoids bind 0.0.0.0 callback misses."""
    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            probe.connect((remote_ip, 9))
            host_ip = probe.getsockname()[0]
        finally:
            probe.close()
    except OSError:
        return None
    if not host_ip or host_ip.startswith("127."):
        return None
    return host_ip


def _ssh_identity() -> Path:
    override = os.environ.get("FLEET_OTA_SSH_KEY")
    if override:
        return Path(override)
    return Path.home() / ".ssh" / "serverside_192_168_2_4_ed25519"


def run_espota_local(bin_path: Path, ip: str, port: int, password: Optional[str] = None) -> int:
    espota = find_espota()
    cmd = [
        sys.executable,
        str(espota),
        "-i",
        ip,
        "-p",
        str(port),
        "-f",
        str(bin_path),
        "-r",
    ]
    host_ip = guess_host_ip(ip)
    if host_ip:
        cmd.extend(["-I", host_ip])
    if password:
        cmd.extend(["-a", password])
    print(f"espota: {' '.join(cmd)}")
    completed = subprocess.run(cmd, check=False)
    return int(completed.returncode)


def run_espota_via_broker(
    bin_path: Path, ip: str, port: int, password: Optional[str] = None
) -> int:
    """Run espota on the MQTT broker host (bypasses Windows inbound firewall)."""
    broker = os.environ.get("FLEET_OTA_BROKER", "192.168.2.4")
    user = os.environ.get("FLEET_OTA_SSH_USER", "tinel")
    key = _ssh_identity()
    if not key.is_file():
        print(f"broker OTA: SSH key not found: {key}", file=sys.stderr)
        return 1
    espota = find_espota()
    remote_bin = f"/tmp/fleet-ota-{os.getpid()}.bin"
    remote_espota = f"/tmp/fleet-espota-{os.getpid()}.py"
    target = f"{user}@{broker}"
    scp = ["scp", "-o", "BatchMode=yes", "-i", str(key)]
    ssh = ["ssh", "-o", "BatchMode=yes", "-i", str(key), target]
    print(f"espota via broker: {target} → {ip}:{port}")
    for src, dst in ((bin_path, remote_bin), (espota, remote_espota)):
        rc = subprocess.run(scp + [str(src), f"{target}:{dst}"], check=False)
        if rc.returncode != 0:
            print(f"broker OTA: scp failed for {src}", file=sys.stderr)
            return int(rc.returncode)
    ota = [
        "python3",
        remote_espota,
        "-i",
        ip,
        "-p",
        str(port),
        "-f",
        remote_bin,
        "-r",
        "-I",
        broker,
    ]
    if password:
        ota.extend(["-a", password])
    # Quote remotely so paths stay intact.
    remote_cmd = " ".join(ota) + f"; ec=$?; rm -f {remote_bin} {remote_espota}; exit $ec"
    completed = subprocess.run(ssh + [remote_cmd], check=False)
    return int(completed.returncode)


def run_espota(bin_path: Path, ip: str, port: int, password: Optional[str] = None) -> int:
    """Local espota, with optional SSH fallback to the automation broker.

    FLEET_OTA_VIA=auto|local|broker (default auto). Windows often needs broker
    because inbound TCP from the ESP is blocked by the firewall.
    """
    mode = (os.environ.get("FLEET_OTA_VIA") or "auto").strip().lower()
    if mode == "broker":
        return run_espota_via_broker(bin_path, ip, port, password=password)
    rc = run_espota_local(bin_path, ip, port, password=password)
    if rc == 0 or mode == "local":
        return rc
    print("espota local failed; retrying via broker …", file=sys.stderr)
    return run_espota_via_broker(bin_path, ip, port, password=password)


def _make_mqtt_client(client_id: str) -> "mqtt.Client":
    if mqtt is None:
        raise RuntimeError("paho-mqtt is required (pip install paho-mqtt)")
    if hasattr(mqtt, "CallbackAPIVersion"):
        return mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=client_id,
        )
    return mqtt.Client(client_id=client_id)


def collect_status(
    registry: Dict[str, Any],
    state: Dict[str, Any],
    *,
    host: str,
    port: int,
    wait_sec: float = 35.0,
) -> Dict[str, Any]:
    """Subscribe to every status topic and merge sightings into state."""
    by_topic: Dict[str, Dict[str, Any]] = {}
    for item in registry.get("devices") or []:
        topic = item["status_topic"]
        by_topic[topic] = item

    client = _make_mqtt_client(f"device-fleet-{os.getpid()}")
    seen: Dict[str, str] = {}

    def on_message(_client: Any, _userdata: Any, msg: Any) -> None:
        topic = msg.topic
        payload = msg.payload.decode("utf-8", errors="replace")
        cfg = by_topic.get(topic)
        if not cfg:
            return
        seen[cfg["id"]] = payload
        record_sighting(
            state,
            cfg["id"],
            payload,
            default_ota_port=int(cfg.get("ota_port") or 3232),
        )

    client.on_message = on_message
    try:
        client.connect(host, int(port), keepalive=60)
    except OSError as exc:
        print(f"MQTT connect failed ({host}:{port}): {exc}", file=sys.stderr)
        return seen
    for topic in by_topic:
        client.subscribe(topic, qos=1)
    client.loop_start()
    try:
        deadline = time.time() + wait_sec
        while time.time() < deadline:
            time.sleep(0.2)
    finally:
        client.loop_stop()
        try:
            client.disconnect()
        except Exception:  # pragma: no cover
            pass
    return seen


def print_status(registry: Dict[str, Any], state: Dict[str, Any], *, now: Optional[float] = None) -> None:
    when = float(now if now is not None else time.time())
    rows: List[str] = []
    for item in registry.get("devices") or []:
        device_id = item["id"]
        entry = (state.get("devices") or {}).get(device_id)
        timeout = int(item.get("timeout_sec") or 90)
        online = is_online(entry, timeout, now=when)
        ip = (entry or {}).get("ip") or "-"
        fw = (entry or {}).get("fw") or "-"
        rssi = (entry or {}).get("rssi")
        rssi_s = str(rssi) if rssi is not None else "-"
        age = "-"
        if entry and entry.get("last_seen") is not None:
            age = f"{int(when - float(entry['last_seen']))}s"
        flash = "yes" if item.get("flash") else "no"
        rows.append(
            f"{device_id:55} {'online' if online else 'offline':7} "
            f"ip={ip:15} fw={fw:8} rssi={rssi_s:4} age={age:5} flash={flash}"
        )
    print("\n".join(rows))


def cmd_status(args: argparse.Namespace) -> int:
    registry = load_registry(Path(args.registry))
    state_path = Path(args.state)
    state = load_state(state_path)
    broker = registry.get("broker") or {}
    host = args.host or broker.get("host") or "192.168.2.4"
    port = int(args.port or broker.get("port") or 1883)
    collect_status(registry, state, host=host, port=port, wait_sec=float(args.wait))
    save_state(state_path, state)
    print_status(registry, state)
    return 0


def cmd_watch(args: argparse.Namespace) -> int:
    registry = load_registry(Path(args.registry))
    state_path = Path(args.state)
    state = load_state(state_path)
    broker = registry.get("broker") or {}
    host = args.host or broker.get("host") or "192.168.2.4"
    port = int(args.port or broker.get("port") or 1883)
    print(f"watching broker {host}:{port} → {state_path}")
    while True:
        collect_status(registry, state, host=host, port=port, wait_sec=float(args.wait))
        save_state(state_path, state)
        print_status(registry, state)
        print("---")
        time.sleep(float(args.interval))


def cmd_flash(args: argparse.Namespace) -> int:
    registry = load_registry(Path(args.registry))
    state_path = Path(args.state)
    state = load_state(state_path)
    device_cfg = device_by_id(registry, args.id)
    entry = (state.get("devices") or {}).get(args.id)

    # Optionally refresh once before flashing so the IP is current.
    if not args.no_refresh:
        broker = registry.get("broker") or {}
        host = args.host or broker.get("host") or "192.168.2.4"
        port = int(args.port or broker.get("port") or 1883)
        collect_status(registry, state, host=host, port=port, wait_sec=float(args.wait))
        save_state(state_path, state)
        entry = (state.get("devices") or {}).get(args.id)

    ok, reason = flash_decision(entry, device_cfg)
    if not ok:
        print(f"skip OTA for {args.id}: {reason}")
        # Offline / no IP is a soft success for post-build hooks.
        if reason.startswith("device offline") or reason.startswith("no IP"):
            return 0
        return 2

    bin_path = Path(args.bin).resolve()
    if not bin_path.is_file():
        print(f"firmware image not found: {bin_path}", file=sys.stderr)
        return 1

    assert entry is not None
    ip = str(entry["ip"])
    ota_port = int(entry.get("ota_port") or device_cfg.get("ota_port") or 3232)
    password = args.password or os.environ.get("OTA_PASSWORD")
    rc = run_espota(bin_path, ip, ota_port, password=password)
    if rc != 0:
        print(f"espota failed with exit code {rc}", file=sys.stderr)
        return rc
    print(f"OTA ok → {args.id} @ {ip}:{ota_port}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Monitor and OTA-flash repo firmware devices")
    parser.add_argument(
        "--registry",
        default=str(DEFAULT_REGISTRY),
        help="path to device_fleet.yaml",
    )
    parser.add_argument(
        "--state",
        default=str(DEFAULT_STATE),
        help="path to device_fleet_state.json",
    )
    parser.add_argument("--host", default=None, help="MQTT broker host override")
    parser.add_argument("--port", default=None, type=int, help="MQTT broker port override")
    sub = parser.add_subparsers(dest="command", required=True)

    p_status = sub.add_parser("status", help="one-shot fleet status")
    p_status.add_argument("--wait", type=float, default=35.0, help="seconds to listen")
    p_status.set_defaults(func=cmd_status)

    p_watch = sub.add_parser("watch", help="continuous monitor")
    p_watch.add_argument("--wait", type=float, default=35.0, help="listen window per cycle")
    p_watch.add_argument("--interval", type=float, default=10.0, help="pause between cycles")
    p_watch.set_defaults(func=cmd_watch)

    p_flash = sub.add_parser("flash", help="OTA flash from state memory")
    p_flash.add_argument("--id", required=True, help="device id from the registry")
    p_flash.add_argument("--bin", required=True, help="path to firmware.bin")
    p_flash.add_argument("--wait", type=float, default=35.0, help="MQTT refresh window")
    p_flash.add_argument(
        "--no-refresh",
        action="store_true",
        help="use state file only (no MQTT listen)",
    )
    p_flash.add_argument("--password", default=None, help="ArduinoOTA password")
    p_flash.set_defaults(func=cmd_flash)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
