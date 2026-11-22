"""Unit tests for client fleet_bridge (no live MQTT)."""

from __future__ import annotations

import sys
import time
from pathlib import Path

CLIENT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CLIENT))

from fleet_bridge import (  # noqa: E402
    build_device_rows,
    is_expected,
    resolve_registry_path,
    summarize_rows,
)


def test_resolve_registry_prefers_monorepo_or_bundle():
    path = resolve_registry_path({})
    assert path.is_file()
    assert path.name == "device_fleet.yaml"


def test_resolve_registry_override(tmp_path: Path):
    custom = tmp_path / "custom_fleet.yaml"
    custom.write_text(
        "broker: {host: 127.0.0.1, port: 1883}\ndevices: []\n",
        encoding="utf-8",
    )
    path = resolve_registry_path({"device_fleet": {"registry": str(custom)}})
    assert path == custom.resolve()


def test_is_expected_defaults_true():
    assert is_expected({"id": "a"}) is True
    assert is_expected({"id": "a", "expected": True}) is True
    assert is_expected({"id": "a", "expected": False}) is False


def test_summarize_online_expected():
    now = time.time()
    registry = {
        "devices": [
            {"id": "online-dev", "timeout_sec": 90, "ota_port": 3232},
            {"id": "offline-dev", "timeout_sec": 90, "ota_port": 3232},
            {
                "id": "optional-dev",
                "timeout_sec": 90,
                "ota_port": 3232,
                "expected": False,
            },
        ]
    }
    state = {
        "devices": {
            "online-dev": {
                "last_seen": now - 5,
                "ip": "192.168.2.49",
                "fw": "0.2.2",
                "ota_port": 3232,
            },
            "optional-dev": {
                "last_seen": now - 5,
                "ip": "192.168.2.50",
                "fw": "1.0.0",
            },
            "offline-dev": {"last_seen": now - 500},
        }
    }
    rows = build_device_rows(registry, state, now=now)
    summary = summarize_rows(rows)
    assert summary["registered"] == 3
    assert summary["expected"] == 2
    assert summary["online"] == 2
    assert summary["online_expected"] == 1

    by_id = {r["id"]: r for r in rows}
    assert by_id["online-dev"]["can_upload"] is True
    assert by_id["online-dev"]["fw"] == "0.2.2"
    assert by_id["offline-dev"]["can_upload"] is False
    assert "offline" in by_id["offline-dev"]["upload_reason"]
    assert by_id["online-dev"]["kind"] == "firmware"


def test_tasmota_lwt_offline_is_not_online():
    now = time.time()
    registry = {
        "devices": [
            {
                "id": "tasmota/pompaApa",
                "kind": "tasmota",
                "topic": "pompaApa",
                "name": "Water Pump",
                "status_topic": "tele/pompaApa/LWT",
                "timeout_sec": 660,
            }
        ]
    }
    state = {
        "devices": {
            "tasmota/pompaApa": {
                "last_seen": now - 2,
                "last_payload": "Offline",
            }
        }
    }
    rows = build_device_rows(registry, state, now=now)
    assert rows[0]["online"] is False
    assert rows[0]["can_upload"] is False
    assert rows[0]["name"] == "Water Pump"


def test_local_catalog_includes_tasmota_folder(tmp_path: Path):
    from fleet_bridge import FleetBridge

    registry = tmp_path / "device_fleet.yaml"
    registry.write_text(
        "broker: {host: 127.0.0.1, port: 1883}\n"
        "devices:\n"
        "  - id: demo\n"
        "    status_topic: demo/status\n"
        "    timeout_sec: 30\n",
        encoding="utf-8",
    )
    bridge = FleetBridge(
        {
            "device_fleet": {
                "catalog": "local",
                "registry": str(registry),
                "state": str(tmp_path / "state.json"),
                "cache": str(tmp_path / "cache.yaml"),
            }
        }
    )
    assert bridge.catalog_source == "local"
    ids = [row["id"] for row in bridge.rows()]
    assert ids[0] == "demo"
    assert "tasmota/pompaApa" in ids
    pump = next(row for row in bridge.rows() if row["id"] == "tasmota/pompaApa")
    assert pump["kind"] == "tasmota"
    assert pump["can_upload"] is False


def test_tray_client_does_not_import_tk():
    bridge = (CLIENT / "fleet_bridge.py").read_text(encoding="utf-8")
    monitor = (CLIENT / "client_monitor.py").read_text(encoding="utf-8")
    assert "import tkinter" not in bridge
    assert "import device_fleet_panel" not in monitor
    assert "from device_fleet_panel" not in monitor


def test_claim_panel_rejects_live_owner(monkeypatch, tmp_path: Path):
    import fleet_bridge as fb

    monkeypatch.setattr(fb, "PANEL_PID", tmp_path / "panel.pid")
    monkeypatch.setattr(fb, "pid_alive", lambda pid: pid == 42)
    assert fb.claim_panel_process(42) is True
    assert fb.claim_panel_process(99) is False


def test_claim_replaces_dead_owner(monkeypatch, tmp_path: Path):
    import fleet_bridge as fb

    monkeypatch.setattr(fb, "PANEL_PID", tmp_path / "panel.pid")
    monkeypatch.setattr(fb, "pid_alive", lambda pid: False)
    (tmp_path / "panel.pid").write_text("7", encoding="ascii")
    assert fb.claim_panel_process(8) is True
    assert fb.read_panel_pid() == 8


def test_launch_raises_existing_window_without_spawn(monkeypatch):
    import fleet_bridge as fb

    monkeypatch.setattr(fb, "raise_device_fleet_window", lambda: True)
    spawned = []
    monkeypatch.setattr(fb.subprocess, "Popen", lambda *args, **kwargs: spawned.append(args))
    fb.launch_device_fleet_panel({})
    assert spawned == []


def test_launch_writes_config_and_spawns_panel(monkeypatch, tmp_path: Path):
    import json

    import fleet_bridge as fb

    monkeypatch.setattr(fb, "PANEL_PID", tmp_path / "panel.pid")
    monkeypatch.setattr(fb, "PANEL_CONFIG", tmp_path / "panel.json")
    monkeypatch.setattr(fb, "raise_device_fleet_window", lambda: False)
    monkeypatch.setattr(fb, "pid_alive", lambda pid: False)
    monkeypatch.setattr(fb, "gui_python", lambda: Path("pythonw.exe"))
    spawned = {}

    def popen(cmd, **kwargs):
        spawned["cmd"] = cmd
        spawned["cwd"] = kwargs.get("cwd")
        return type("Proc", (), {"pid": 99})()

    monkeypatch.setattr(fb.subprocess, "Popen", popen)
    fb.launch_device_fleet_panel({"mqtt": {"broker": {"host": "192.168.2.4"}}})
    assert spawned["cmd"][0] == "pythonw.exe"
    assert spawned["cmd"][1].endswith("device_fleet_panel.py")
    assert spawned["cmd"][2:] == ["--config", str(tmp_path / "panel.json")]
    saved = json.loads((tmp_path / "panel.json").read_text(encoding="utf-8"))
    assert saved["mqtt"]["broker"]["host"] == "192.168.2.4"
