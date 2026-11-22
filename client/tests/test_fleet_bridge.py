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
