"""Version compare and release asset selection (no network)."""

from __future__ import annotations

import sys
from pathlib import Path

CLIENT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CLIENT))

from auto_updater import is_newer, read_local_version, release_download_url  # noqa: E402


def test_version_file_matches_release_line():
    assert read_local_version(CLIENT / "VERSION") == "3.26.0"


def test_is_newer_semver():
    assert is_newer("3.25.0", "3.11.2") is True
    assert is_newer("v3.25.0", "3.25.0") is False
    assert is_newer("3.24.0", "3.25.0") is False


def test_release_prefers_client_zip_then_zipball():
    release = {
        "zipball_url": "https://example.test/zipball",
        "assets": [
            {"name": "notes.txt", "browser_download_url": "https://example.test/notes"},
            {"name": "client-v3.25.0.zip", "browser_download_url": "https://example.test/client.zip"},
        ],
    }
    assert release_download_url(release) == "https://example.test/client.zip"
    assert release_download_url({"zipball_url": "https://example.test/zipball", "assets": []}) == (
        "https://example.test/zipball"
    )
    assert release_download_url({"assets": []}) is None
