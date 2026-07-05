"""Tests for Tongou phase_a RAW decoding."""

import base64
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

from tongou_phase import decode_phase_raw


def test_tongou_example_from_spec():
    # 08 e9 00 00 15 00 00 05 -> 228.1 V, 0.021 A, 5 W
    raw = bytes([0x08, 0xE9, 0x00, 0x00, 0x15, 0x00, 0x00, 0x05])
    b64 = base64.b64encode(raw).decode()
    out = decode_phase_raw(b64)
    assert out is not None
    assert out["voltage_v"] == 228.1
    assert out["current_a"] == 0.021
    assert out["power_w"] == 5.0


def test_decode_bytes_directly():
    raw = bytes([0x09, 0x4F, 0x00, 0x21, 0xEE, 0x00, 0x08, 0x16])
    out = decode_phase_raw(raw)
    assert out is not None
    assert out["voltage_v"] == 238.3
    assert out["current_a"] == 8.686
    assert out["power_w"] == 2070.0
