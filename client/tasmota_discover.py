#!/usr/bin/env python3
"""Find Tasmota boards on the automation LAN.

MQTT: subscribe to ``tele/+/LWT`` and ``stat/+/STATUS*``, then ask the default
group topics (``tasmotas`` and legacy ``sonoffs``) for Status 0 and Status 5.
HTTP: one-shot GET of ``/cm?cmnd=Status%200`` across the broker /24. This is
not a periodic poll.

Writing ``--write`` updates ``device/tasmota/catalog.yaml`` when this repo
checkout is present.
"""

from __future__ import annotations

import argparse
import json
import socket
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

CLIENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CLIENT_DIR.parent
if str(CLIENT_DIR) not in sys.path:
    sys.path.insert(0, str(CLIENT_DIR))

from device_catalog import (  # noqa: E402
    device_id_for,
    merge_tasmota,
    normalize_tasmota,
    repo_tasmota_catalog,
    write_tasmota_catalog,
)

GROUP_TOPICS = ("tasmotas", "sonoffs")
IGNORED_NAMES = set(GROUP_TOPICS) | {"+", "#", ""}
STATUS_SUFFIXES = {"STATUS", "STATUS0", "STATUS2", "STATUS5", "RESULT"}


def split_tasmota_topic(topic: str) -> Optional[tuple]:
    parts = (topic or "").split("/")
    if len(parts) != 3:
        return None
    prefix, name, suffix = parts
    if prefix not in ("tele", "stat"):
        return None
    if name in IGNORED_NAMES:
        return None
    return prefix, name, suffix


def _clean_ip(value: Any) -> str:
    text = str(value or "").strip()
    if not text or text in ("0.0.0.0", "255.255.255.255"):
        return ""
    return text


def absorb_status_json(sighting: Dict[str, Any], data: Dict[str, Any]) -> None:
    """Merge one Tasmota status / info JSON object into a sighting."""
    if not isinstance(data, dict):
        return
    warning = data.get("WARNING") or data.get("Warning")
    if warning:
        sighting["auth_required"] = True

    status = data.get("Status") if isinstance(data.get("Status"), dict) else {}
    topic = status.get("Topic")
    if topic:
        sighting["topic"] = str(topic)
    if status.get("DeviceName"):
        sighting["device_name"] = str(status["DeviceName"])
    friendly = status.get("FriendlyName")
    if isinstance(friendly, list) and friendly:
        sighting["friendly_name"] = str(friendly[0])
    elif isinstance(friendly, str) and friendly:
        sighting["friendly_name"] = friendly
    if status.get("Module") not in (None, ""):
        sighting.setdefault("module", str(status["Module"]))

    net = data.get("StatusNET") if isinstance(data.get("StatusNET"), dict) else {}
    ip = _clean_ip(net.get("IPAddress") or net.get("IP"))
    if ip:
        sighting["ip"] = ip
    if net.get("Mac"):
        sighting["mac"] = str(net["Mac"])
    if net.get("Hostname"):
        sighting["hostname"] = str(net["Hostname"])

    firmware = data.get("StatusFWR") if isinstance(data.get("StatusFWR"), dict) else {}
    if firmware.get("Version"):
        sighting["fw"] = str(firmware["Version"])
    if firmware.get("Hardware"):
        sighting["hardware"] = str(firmware["Hardware"])

    info = data.get("Info1") if isinstance(data.get("Info1"), dict) else {}
    if info.get("Module"):
        sighting["module"] = str(info["Module"])
    if info.get("Version") and not sighting.get("fw"):
        sighting["fw"] = str(info["Version"])


def apply_mqtt_message(sightings: Dict[str, Dict[str, Any]], topic: str, payload: str) -> None:
    parsed = split_tasmota_topic(topic)
    if not parsed:
        return
    _prefix, name, suffix = parsed
    upper = suffix.upper()
    if upper not in STATUS_SUFFIXES and upper not in ("LWT", "INFO1", "STATE"):
        return
    sighting = sightings.setdefault(name, {"topic": name})
    text = (payload or "").strip()
    if upper == "LWT":
        sighting["lwt"] = text.strip('"')
        return
    if not text.startswith("{"):
        return
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return
    if isinstance(data, dict):
        absorb_status_json(sighting, data)


def sighting_to_device(sighting: Dict[str, Any], *, now: Optional[float] = None) -> Optional[Dict[str, Any]]:
    topic = str(sighting.get("topic") or "").strip()
    ip = _clean_ip(sighting.get("ip"))
    mac = sighting.get("mac")
    if not topic and not ip and not mac:
        return None
    try:
        device_id = device_id_for(topic=topic or None, mac=mac, ip=ip or None)
    except ValueError:
        return None
    name = (
        sighting.get("friendly_name")
        or sighting.get("device_name")
        or sighting.get("hostname")
        or topic
        or device_id
    )
    when = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now if now is not None else time.time()))
    item: Dict[str, Any] = {
        "id": device_id,
        "topic": topic,
        "name": name,
        "kind": "tasmota",
        "last_scan": when,
    }
    for key in ("ip", "fw", "mac", "hostname", "hardware", "module", "friendly_name"):
        if sighting.get(key):
            item[key] = sighting[key]
    if sighting.get("auth_required"):
        item["auth_required"] = True
    lwt = str(sighting.get("lwt") or "").strip().strip('"').lower()
    if not lwt and (ip or sighting.get("fw")):
        lwt = "online"
    row = normalize_tasmota(item)
    row["lwt"] = lwt
    return row


def state_payload_for(device: Dict[str, Any], lwt: str) -> str:
    """Payload stored in fleet state so online/offline follows LWT, not mere delivery."""
    if device.get("ip") or device.get("fw"):
        body = {key: device.get(key) for key in ("ip", "fw") if device.get(key)}
        return json.dumps(body)
    if lwt == "offline":
        return "Offline"
    return "Online"


def parse_http_probe(ip: str, status_code: int, body: str, server_header: str = "") -> Optional[Dict[str, Any]]:
    """Return a sighting when an HTTP response is Tasmota, otherwise None."""
    text = body or ""
    lowered = text.lower()
    server = (server_header or "").lower()
    markers = ("tasmota", "statusfwr", "statusnet", "need user", "enter command")
    if not any(marker in lowered for marker in markers) and "tasmota" not in server:
        return None
    if status_code not in (200, 401):
        return None
    sighting: Dict[str, Any] = {"ip": ip, "lwt": "online"}
    if "tasmota/" in server:
        sighting["fw"] = server_header.split("/", 1)[-1].strip()
    stripped = text.strip()
    if stripped.startswith("{"):
        try:
            data = json.loads(stripped)
        except json.JSONDecodeError:
            data = None
        if isinstance(data, dict):
            absorb_status_json(sighting, data)
    if not sighting.get("ip"):
        sighting["ip"] = ip
    return sighting


def is_private_ipv4(ip: str) -> bool:
    parts = ip.split(".")
    if len(parts) != 4:
        return False
    try:
        nums = [int(part) for part in parts]
    except ValueError:
        return False
    if any(num < 0 or num > 255 for num in nums):
        return False
    if nums[0] == 10:
        return True
    if nums[0] == 192 and nums[1] == 168:
        return True
    if nums[0] == 172 and 16 <= nums[1] <= 31:
        return True
    return False


def subnet24_hosts(cidr: str) -> List[str]:
    text = (cidr or "").strip()
    if not text.endswith("/24"):
        raise ValueError(f"Only /24 scans are supported ({cidr})")
    base = text.split("/", 1)[0]
    parts = base.split(".")
    if len(parts) != 4 or not is_private_ipv4(base):
        raise ValueError(f"Refusing non-private subnet {cidr}")
    prefix = ".".join(parts[:3])
    return [f"{prefix}.{host}" for host in range(1, 255)]


def local_ip_toward(remote: str) -> Optional[str]:
    if not remote or remote in ("localhost", "127.0.0.1"):
        return None
    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            probe.connect((remote, 9))
            host_ip = probe.getsockname()[0]
        finally:
            probe.close()
    except OSError:
        return None
    if not host_ip or host_ip.startswith("127."):
        return None
    return host_ip


def default_scan_subnets(broker_host: str, configured: Optional[Sequence[str]] = None) -> List[str]:
    if configured:
        return [str(item).strip() for item in configured if str(item).strip()]
    found: List[str] = []
    for target in (broker_host, "192.168.2.4"):
        ip = local_ip_toward(target)
        if not ip or not is_private_ipv4(ip):
            continue
        cidr = ".".join(ip.split(".")[:3]) + ".0/24"
        if cidr not in found:
            found.append(cidr)
    if "192.168.2.0/24" not in found:
        found.append("192.168.2.0/24")
    return found


def _make_mqtt_client(client_id: str):
    import paho.mqtt.client as mqtt

    if hasattr(mqtt, "CallbackAPIVersion"):
        return mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
    return mqtt.Client(client_id=client_id)


def discover_mqtt(
    host: str,
    port: int,
    *,
    known_topics: Sequence[str] = (),
    wait_sec: float = 8.0,
) -> Dict[str, Dict[str, Any]]:
    """Ask Tasmota devices on the broker to publish Status. Returns topic → sighting."""
    import os

    sightings: Dict[str, Dict[str, Any]] = {}
    client = _make_mqtt_client(f"tasmota-discover-{os.getpid()}")

    def on_message(_client: Any, _userdata: Any, msg: Any) -> None:
        payload = msg.payload.decode("utf-8", errors="replace") if isinstance(msg.payload, (bytes, bytearray)) else str(msg.payload)
        apply_mqtt_message(sightings, msg.topic, payload)

    client.on_message = on_message
    client.connect(host, int(port), keepalive=30)
    for topic in (
        "tele/+/LWT",
        "tele/+/INFO1",
        "tele/+/STATE",
        "stat/+/STATUS",
        "stat/+/STATUS0",
        "stat/+/STATUS2",
        "stat/+/STATUS5",
        "stat/+/RESULT",
    ):
        client.subscribe(topic, qos=0)
    client.loop_start()
    try:
        time.sleep(min(1.5, max(0.3, wait_sec / 4)))
        targets = set(GROUP_TOPICS)
        targets.update(t for t in known_topics if t)
        targets.update(sightings.keys())
        for name in sorted(targets):
            client.publish(f"cmnd/{name}/Status", "0", qos=0)
            client.publish(f"cmnd/{name}/Status", "5", qos=0)
        remaining = max(0.5, wait_sec - 1.5)
        time.sleep(remaining)
    finally:
        client.loop_stop()
        client.disconnect()
    return sightings


def _probe_http(ip: str, timeout: float) -> Optional[Dict[str, Any]]:
    import requests

    url = f"http://{ip}/cm?cmnd=Status%200"
    try:
        response = requests.get(url, timeout=(timeout, timeout), allow_redirects=False)
    except requests.RequestException:
        return None
    server = response.headers.get("Server", "")
    return parse_http_probe(ip, response.status_code, response.text or "", server)


def discover_http(
    subnets: Sequence[str],
    *,
    skip_ips: Iterable[str] = (),
    timeout: float = 6.0,
    workers: int = 48,
) -> List[Dict[str, Any]]:
    """One-shot HTTP probe. Only private /24 ranges."""
    skip = {ip for ip in skip_ips if ip}
    hosts: List[str] = []
    for cidr in subnets:
        for ip in subnet24_hosts(cidr):
            if ip not in skip:
                hosts.append(ip)
    found: List[Dict[str, Any]] = []
    if not hosts:
        return found
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = {pool.submit(_probe_http, ip, timeout): ip for ip in hosts}
        for future in as_completed(futures):
            try:
                sighting = future.result()
            except Exception:
                continue
            if sighting:
                found.append(sighting)
    return found


def discover_tasmota(
    host: str,
    port: int = 1883,
    *,
    known_topics: Sequence[str] = (),
    wait_sec: float = 8.0,
    http: bool = True,
    subnets: Optional[Sequence[str]] = None,
    skip_ips: Iterable[str] = (),
    http_timeout: float = 6.0,
) -> Dict[str, Any]:
    """MQTT discovery, then an optional LAN sweep. Does not remove known devices."""
    report: Dict[str, Any] = {
        "devices": [],
        "mqtt": 0,
        "http": 0,
        "error": "",
        "subnets": [],
    }
    sightings: Dict[str, Dict[str, Any]] = {}
    try:
        sightings = discover_mqtt(host, port, known_topics=known_topics, wait_sec=wait_sec)
    except Exception as exc:
        report["error"] = f"MQTT discover failed ({host}:{port}): {exc}"

    devices: List[Dict[str, Any]] = []
    lwt_by_id: Dict[str, str] = {}
    for sighting in sightings.values():
        device = sighting_to_device(sighting)
        if not device:
            continue
        devices.append(device)
        lwt_by_id[device["id"]] = str(sighting.get("lwt") or "")
    report["mqtt"] = len(devices)

    if http and not report["error"]:
        nets = default_scan_subnets(host, subnets)
        report["subnets"] = list(nets)
        try:
            http_sightings = discover_http(
                nets,
                skip_ips=list(skip_ips),
                timeout=http_timeout,
            )
        except Exception as exc:
            report["error"] = (report["error"] + f" HTTP scan failed: {exc}").strip()
            http_sightings = []
        report["http"] = len(http_sightings)
        for sighting in http_sightings:
            device = sighting_to_device(sighting)
            if not device:
                continue
            devices.append(device)
            lwt_by_id.setdefault(device["id"], str(sighting.get("lwt") or "online"))
    elif http and report["error"]:
        # Broker down: still look on the LAN so boards with a web UI are listed.
        nets = default_scan_subnets(host, subnets)
        report["subnets"] = list(nets)
        try:
            http_sightings = discover_http(nets, skip_ips=skip_ips, timeout=http_timeout)
            report["http"] = len(http_sightings)
            if http_sightings:
                report["error"] = ""
            for sighting in http_sightings:
                device = sighting_to_device(sighting)
                if device:
                    devices.append(device)
                    lwt_by_id[device["id"]] = str(sighting.get("lwt") or "online")
        except Exception as exc:
            report["error"] = (report["error"] + f" HTTP scan failed: {exc}").strip()

    report["devices"] = devices
    report["lwt"] = lwt_by_id
    return report


def apply_discoveries(
    registry: Dict[str, Any],
    discovered: Sequence[Dict[str, Any]],
) -> Dict[str, List[str]]:
    """Merge scan rows into a registry. Returns added and updated ids."""
    before = {str(item.get("id")) for item in registry.get("devices") or []}
    merged = merge_tasmota(list(registry.get("devices") or []), discovered, overwrite_scan_fields=True)
    registry["devices"] = merged
    after_ids = [str(item.get("id")) for item in merged if item.get("kind") == "tasmota"]
    added = [device_id for device_id in after_ids if device_id not in before]
    updated = [device_id for device_id in after_ids if device_id in before]
    return {"added": added, "updated": updated}


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="List Tasmota devices on the LAN")
    parser.add_argument("--host", default="192.168.2.4")
    parser.add_argument("--port", type=int, default=1883)
    parser.add_argument("--wait", type=float, default=8.0)
    parser.add_argument("--http", action="store_true", help="Also sweep the private /24 for Tasmota web UI")
    parser.add_argument("--subnet", action="append", default=[], help="Private /24 to sweep (repeatable)")
    parser.add_argument("--write", action="store_true", help="Update device/tasmota/catalog.yaml")
    args = parser.parse_args(argv)

    catalog_path = repo_tasmota_catalog(REPO_ROOT)
    known: List[str] = []
    existing: List[Dict[str, Any]] = []
    if catalog_path and catalog_path.is_file():
        import yaml

        data = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
        for item in data.get("devices") or []:
            if isinstance(item, dict):
                existing.append(item)
                if item.get("topic"):
                    known.append(str(item["topic"]))

    report = discover_tasmota(
        args.host,
        args.port,
        known_topics=known,
        wait_sec=args.wait,
        http=bool(args.http),
        subnets=args.subnet or None,
    )
    merged = merge_tasmota(existing, report["devices"], overwrite_scan_fields=True)
    if args.write:
        if catalog_path is None:
            print("No repo checkout; catalog not written", file=sys.stderr)
            return 1
        write_tasmota_catalog(catalog_path, merged)
        print(f"Wrote {catalog_path}")
    print(f"MQTT {report['mqtt']}  HTTP {report['http']}  catalog {sum(1 for item in merged if item.get('kind') == 'tasmota' or item.get('topic'))}")
    if report.get("error"):
        print(report["error"], file=sys.stderr)
    for item in merged:
        if item.get("kind") != "tasmota" and not str(item.get("id") or "").startswith("tasmota/"):
            continue
        print(
            f"{item.get('id')}\t{item.get('name')}\t{item.get('ip') or '-'}\t{item.get('fw') or '-'}"
        )
    return 1 if report.get("error") and not report["devices"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
