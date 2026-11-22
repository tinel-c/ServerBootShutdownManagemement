"""Catalog fetch/merge and Tasmota discovery parsing (no live network)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

CLIENT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CLIENT))

from device_catalog import (  # noqa: E402
    catalog_mode,
    dump_tasmota_catalog,
    load_merged_catalog,
    merge_tasmota,
    raw_github_url,
)
from tasmota_discover import (  # noqa: E402
    absorb_status_json,
    apply_mqtt_message,
    parse_http_probe,
    sighting_to_device,
    subnet24_hosts,
)


def test_raw_url_and_local_mode(tmp_path: Path):
    url = raw_github_url(
        "tinel-c/ServerBootShutdownManagemement",
        "main",
        "device/tasmota/catalog.yaml",
    )
    assert url == (
        "https://raw.githubusercontent.com/tinel-c/"
        "ServerBootShutdownManagemement/main/device/tasmota/catalog.yaml"
    )
    registry = tmp_path / "reg.yaml"
    registry.write_text("devices: []\n", encoding="utf-8")
    assert catalog_mode({"device_fleet": {"registry": str(registry), "catalog": "github"}}) == "local"
    assert catalog_mode({"device_fleet": {}}) == "github"


def test_github_merge_and_fallback(tmp_path: Path):
    def fetch(url: str) -> str:
        if url.endswith("device_fleet.yaml"):
            return (
                "broker: {host: 192.168.2.4, port: 1883}\n"
                "devices:\n"
                "  - id: board\n"
                "    status_topic: board/status\n"
            )
        if url.endswith("catalog.yaml"):
            return (
                "version: 1\n"
                "devices:\n"
                "  - id: tasmota/pompaApa\n"
                "    topic: pompaApa\n"
                "    name: Water Pump\n"
            )
        raise AssertionError(url)

    loaded = load_merged_catalog(
        {"device_fleet": {"catalog": "github", "github_repo": "acme/widgets", "github_ref": "main"}},
        local_fleet_path=None,
        cache_path=tmp_path / "cache.yaml",
        repo_root=tmp_path,
        fetch=fetch,
    )
    assert loaded.source == "github"
    ids = [item["id"] for item in loaded.registry["devices"]]
    assert ids == ["board", "tasmota/pompaApa"]
    pump = loaded.registry["devices"][1]
    assert pump["status_topic"] == "tele/pompaApa/LWT"
    assert pump["flash"] is False
    assert (tmp_path / "cache.yaml").is_file()

    def broken(_url: str) -> str:
        raise OSError("offline")

    fleet = tmp_path / "device_fleet.yaml"
    fleet.write_text(
        "broker: {host: 127.0.0.1, port: 1883}\ndevices:\n  - id: local-board\n    status_topic: x/status\n",
        encoding="utf-8",
    )
    fallback = load_merged_catalog(
        {"device_fleet": {"catalog": "github"}},
        local_fleet_path=fleet,
        cache_path=tmp_path / "missing-cache.yaml",
        repo_root=tmp_path,
        fetch=broken,
    )
    assert fallback.source == "fallback"
    assert fallback.registry["devices"][0]["id"] == "local-board"


def test_scan_keeps_friendly_name_and_updates_ip():
    existing = [
        {
            "id": "tasmota/pompaApa",
            "kind": "tasmota",
            "topic": "pompaApa",
            "name": "Water Pump",
            "status_topic": "tele/pompaApa/LWT",
            "timeout_sec": 660,
            "expected": True,
            "flash": False,
            "path": "device/tasmota",
        }
    ]
    found = {
        "id": "tasmota/pompaApa",
        "topic": "pompaApa",
        "name": "pompaApa",
        "friendly_name": "Pump",
        "ip": "192.168.2.40",
        "fw": "14.2.0",
        "kind": "tasmota",
    }
    merged = merge_tasmota(existing, [found], overwrite_scan_fields=True)
    row = merged[0]
    assert row["name"] == "Water Pump"
    assert row["ip"] == "192.168.2.40"
    assert row["fw"] == "14.2.0"
    text = dump_tasmota_catalog(merged)
    assert "Water Pump" in text
    assert "192.168.2.40" in text


def test_parse_mqtt_status_and_http_probe():
    sightings = {}
    apply_mqtt_message(sightings, "tele/tasmotas/LWT", "Online")
    assert sightings == {}
    payload = {
        "Status": {"Topic": "pompaApa", "DeviceName": "Pump", "FriendlyName": ["Pump house"]},
        "StatusNET": {"IPAddress": "192.168.2.40", "Mac": "AA:BB:CC:DD:EE:FF", "Hostname": "pompa"},
        "StatusFWR": {"Version": "14.2.0(tasmota)", "Hardware": "ESP8266EX"},
    }
    apply_mqtt_message(sightings, "stat/pompaApa/STATUS", json.dumps(payload))
    apply_mqtt_message(sightings, "tele/pompaApa/LWT", "Online")
    device = sighting_to_device(sightings["pompaApa"])
    assert device is not None
    assert device["id"] == "tasmota/pompaApa"
    assert device["ip"] == "192.168.2.40"
    assert device["fw"] == "14.2.0(tasmota)"
    assert device["lwt"] == "online"
    assert device["friendly_name"] == "Pump house"

    blocked = parse_http_probe(
        "192.168.2.41",
        200,
        '{"WARNING":"Need user=<username>&password=<password>"}',
    )
    assert blocked is not None
    assert blocked["auth_required"] is True
    assert parse_http_probe("192.168.2.1", 200, "<html>router</html>") is None

    partial = {}
    absorb_status_json(partial, {"Info1": {"Module": "Sonoff Basic", "Version": "9.5.0"}})
    assert partial["module"] == "Sonoff Basic"
    assert partial["fw"] == "9.5.0"


def test_subnet_is_private_24_only():
    hosts = subnet24_hosts("192.168.2.0/24")
    assert hosts[0] == "192.168.2.1"
    assert hosts[-1] == "192.168.2.254"
    try:
        subnet24_hosts("8.8.8.0/24")
    except ValueError:
        pass
    else:
        raise AssertionError("public subnet should be refused")
