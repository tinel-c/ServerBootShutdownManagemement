#!/usr/bin/env python3
"""Auto-updater for Client Monitor.

Installed copies check GitHub for a newer release and apply it with
update_client_files.bat. A release asset named like client-vX.Y.Z.zip is
preferred. If that asset is missing, the release zipball is used so a normal
git tag still updates every PC.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import tempfile
import zipfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import requests
from packaging import version

logger = logging.getLogger(__name__)

GITHUB_REPO = "tinel-c/ServerBootShutdownManagemement"
_VERSION_FILE = Path(__file__).resolve().parent / "VERSION"


def read_local_version(path: Optional[Path] = None) -> str:
    """Version installed next to this file (client/VERSION)."""
    target = path or _VERSION_FILE
    try:
        text = target.read_text(encoding="utf-8").strip().lstrip("vV")
        if text:
            return text
    except OSError:
        pass
    return "0.0.0"


def is_newer(latest: str, current: str) -> bool:
    latest_text = (latest or "").strip().lstrip("vV")
    current_text = (current or "").strip().lstrip("vV")
    if not latest_text or not current_text:
        return False
    try:
        return version.parse(latest_text) > version.parse(current_text)
    except Exception:
        return latest_text != current_text


def release_download_url(release: Dict[str, Any]) -> Optional[str]:
    """Client zip asset, or the tag zipball when the asset was not uploaded."""
    for asset in release.get("assets") or []:
        name = str(asset.get("name") or "")
        url = asset.get("browser_download_url")
        if url and "client" in name.lower() and name.lower().endswith(".zip"):
            return str(url)
    zipball = release.get("zipball_url")
    return str(zipball) if zipball else None


class AutoUpdater:
    """Check GitHub and install a newer Client Monitor build."""

    def __init__(self, check_interval_hours: float = 24, repo: Optional[str] = None):
        self.repo = (repo or "").strip() or GITHUB_REPO
        self.api_url = f"https://api.github.com/repos/{self.repo}/releases/latest"
        self.check_interval = timedelta(hours=float(check_interval_hours))
        self.script_dir = Path(__file__).resolve().parent
        cache_root = Path(os.environ.get("LOCALAPPDATA", tempfile.gettempdir())) / "ClientMonitor"
        self.update_cache = cache_root / "update_cache.json"
        self.current_version = read_local_version(self.script_dir / "VERSION")
        self.last_check: Optional[datetime] = None
        self.latest_version: Optional[str] = None
        self._load_cache()

    def _load_cache(self) -> None:
        try:
            if self.update_cache.is_file():
                cache = json.loads(self.update_cache.read_text(encoding="utf-8"))
                self.last_check = datetime.fromisoformat(cache.get("last_check", "2000-01-01"))
                self.latest_version = cache.get("latest_version")
        except Exception as exc:
            logger.debug("Could not load update cache: %s", exc)
            self.last_check = datetime.min

    def _save_cache(self) -> None:
        try:
            self.update_cache.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "last_check": datetime.now().isoformat(),
                "latest_version": self.latest_version,
                "current_version": self.current_version,
            }
            self.update_cache.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception as exc:
            logger.warning("Could not save update cache: %s", exc)

    def should_check_for_updates(self) -> bool:
        if self.last_check is None:
            return True
        return datetime.now() - self.last_check >= self.check_interval

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "ClientMonitor-updater",
        }
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def check_for_updates(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """Return (has_update, latest_version, download_url)."""
        try:
            logger.info("Checking for updates (current version: %s)", self.current_version)
            response = requests.get(self.api_url, headers=self._headers(), timeout=15)
            if response.status_code != 200:
                logger.warning("GitHub API returned status %s", response.status_code)
                return False, None, None
            release = response.json()
            latest = str(release.get("tag_name") or "").lstrip("vV")
            download_url = release_download_url(release)
            if not latest or not download_url:
                logger.warning("Latest release has no tag or download")
                return False, None, None
            has_update = is_newer(latest, self.current_version)
            self.latest_version = latest
            self.last_check = datetime.now()
            self._save_cache()
            if has_update:
                logger.info("Update available: %s -> %s", self.current_version, latest)
            else:
                logger.info("No updates available")
            return has_update, latest, download_url
        except requests.RequestException as exc:
            logger.error("Network error checking for updates: %s", exc)
            return False, None, None
        except Exception as exc:
            logger.error("Error checking for updates: %s", exc, exc_info=True)
            return False, None, None

    def download_update(self, download_url: str) -> Optional[Path]:
        try:
            logger.info("Downloading update from %s", download_url)
            temp_dir = Path(tempfile.gettempdir()) / "client_monitor_update"
            temp_dir.mkdir(exist_ok=True)
            response = requests.get(
                download_url,
                headers=self._headers(),
                stream=True,
                timeout=120,
                allow_redirects=True,
            )
            response.raise_for_status()
            download_path = temp_dir / "client_update.zip"
            with download_path.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=65536):
                    if chunk:
                        handle.write(chunk)
            logger.info("Update downloaded to %s", download_path)
            return download_path
        except Exception as exc:
            logger.error("Error downloading update: %s", exc, exc_info=True)
            return None

    def install_update(self, update_package_path: Path) -> bool:
        """Extract the package and start update_client_files.bat detached."""
        try:
            logger.info("Installing update...")
            extract_dir = Path(tempfile.gettempdir()) / "client_monitor_update" / "extracted"
            if extract_dir.exists():
                shutil.rmtree(extract_dir)
            extract_dir.mkdir(parents=True)
            with zipfile.ZipFile(update_package_path, "r") as archive:
                archive.extractall(extract_dir)

            update_script = None
            for root, _dirs, files in os.walk(extract_dir):
                if "update_client_files.bat" in files:
                    update_script = Path(root) / "update_client_files.bat"
                    break
            if update_script is None:
                logger.error("update_client_files.bat not found in package")
                return False

            restart_script = extract_dir / "apply_update.bat"
            log_dir = Path(os.environ.get("LOCALAPPDATA", tempfile.gettempdir())) / "ClientMonitor"
            restart_script.write_text(
                "\r\n".join(
                    [
                        "@echo off",
                        "set CLIENT_UPDATE_INTERACTIVE=",
                        "echo Waiting for Client Monitor to release files...",
                        "timeout /t 5 /nobreak >nul",
                        f'call "{update_script}" >> "{log_dir / "update.log"}" 2>&1',
                        "exit /b %errorlevel%",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            flags = 0
            if sys.platform == "win32":
                flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
            log_dir.mkdir(parents=True, exist_ok=True)
            subprocess.Popen(
                ["cmd", "/c", str(restart_script)],
                creationflags=flags,
                close_fds=True,
                cwd=str(update_script.parent),
            )
            logger.info("Update started. Log: %s", log_dir / "update.log")
            return True
        except Exception as exc:
            logger.error("Error installing update: %s", exc, exc_info=True)
            return False

    def check_and_install_updates(self, auto_install: bool = True) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "checked": False,
            "update_available": False,
            "current_version": self.current_version,
            "latest_version": None,
            "installed": False,
            "error": None,
        }
        try:
            if not self.should_check_for_updates():
                logger.debug("Skipping update check (too soon since last check)")
                return result
            has_update, latest_version, download_url = self.check_for_updates()
            result["checked"] = True
            result["update_available"] = has_update
            result["latest_version"] = latest_version
            if not has_update or not download_url:
                return result
            if not auto_install:
                logger.info("Auto-install disabled, skipping installation")
                return result
            package = self.download_update(download_url)
            if not package:
                result["error"] = "Failed to download update"
                return result
            success = self.install_update(package)
            result["installed"] = success
            if not success:
                result["error"] = "Failed to install update"
            return result
        except Exception as exc:
            logger.error("Error in check_and_install_updates: %s", exc, exc_info=True)
            result["error"] = str(exc)
            return result


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    updater = AutoUpdater(check_interval_hours=0)
    result = updater.check_and_install_updates(auto_install=False)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
