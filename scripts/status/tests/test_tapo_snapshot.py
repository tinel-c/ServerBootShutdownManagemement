"""Tests for Tapo snapshot helpers."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tapo_snapshot import build_snapshot_payload, resize_jpeg, slug_from_mqtt_prefix


def test_slug_from_mqtt_prefix():
    assert slug_from_mqtt_prefix("garden/camera/interior") == "interior"
    assert slug_from_mqtt_prefix("garden/camera/interior/") == "interior"


def test_build_snapshot_payload():
    payload = build_snapshot_payload(
        "interior",
        "Interior curte",
        "2026-07-05T12:00:00",
        "/camera-snapshots/interior.jpg",
    )
    assert payload["slug"] == "interior"
    assert payload["image_url"] == "/camera-snapshots/interior.jpg"


def test_resize_jpeg():
    pytest.importorskip("PIL")
    from PIL import Image
    import io

    img = Image.new("RGB", (800, 600), color=(10, 20, 30))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    raw = buf.getvalue()

    out = resize_jpeg(raw, 320)
    out_img = Image.open(io.BytesIO(out))
    assert out_img.width == 320
    assert out_img.height == 240
