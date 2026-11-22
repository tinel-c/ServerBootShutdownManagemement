#!/usr/bin/env python3
"""Bridge between the Windows client UI and scripts/status/device_fleet.py."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

CLIENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CLIENT_DIR.parent
STATE_DIR = Path(os.getenv("LOCALAPPDATA", str(CLIENT_DIR))) / "ClientMonitor"
DEFAULT_STATE = STATE_DIR / "device_fleet_state.json"


def resolve_registry_path(config: Optional[Dict[str, Any]] = None) -> Path:
    """Locate device_fleet.yaml (config override → monorepo → bundled)."""
    cfg = (config or {}).get("device_fleet") or {}
    override = (cfg.get("registry") or "").strip()
    if override:
        path = Path(override).expanduser()
        if path.is_file():
            return path.resolve()

    monorepo = REPO_ROOT / "scripts" / "status" / "device_fleet.yaml"
    if monorepo.is_file():
        return monorepo.resolve()

    bundled = CLIENT_DIR / "config" / "device_fleet.yaml"
    if bundled.is_file():
        return bundled.resolve()

    raise FileNotFoundError(
        "device_fleet.yaml not found. Set device_fleet.registry in client_config.yaml "
        "or keep client/config/device_fleet.yaml next to the client."
    )


def resolve_device_fleet_script() -> Path:
    """Locate device_fleet.py (monorepo → installed copy beside client)."""
    monorepo = REPO_ROOT / "scripts" / "status" / "device_fleet.py"
    if monorepo.is_file():
        return monorepo.resolve()
    local = CLIENT_DIR / "device_fleet.py"
    if local.is_file():
        return local.resolve()
    raise FileNotFoundError(
        "device_fleet.py not found under scripts/status/ or next to the client."
    )


def load_device_fleet_module():
    script = resolve_device_fleet_script()
    spec = importlib.util.spec_from_file_location("device_fleet", script)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {script}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["device_fleet"] = mod
    spec.loader.exec_module(mod)
    return mod


def is_expected(device_cfg: Dict[str, Any]) -> bool:
    """Devices count toward 'should be online' unless expected: false."""
    return device_cfg.get("expected", True) is not False


def build_device_rows(
    registry: Dict[str, Any],
    state: Dict[str, Any],
    *,
    now: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """One UI row per registry device."""
    when = float(now if now is not None else time.time())
    fleet = load_device_fleet_module()
    rows: List[Dict[str, Any]] = []
    for item in registry.get("devices") or []:
        device_id = str(item["id"])
        entry = (state.get("devices") or {}).get(device_id) or {}
        timeout = int(item.get("timeout_sec") or 90)
        online = bool(fleet.is_online(entry, timeout, now=when))
        age_s: Optional[int] = None
        if entry.get("last_seen") is not None:
            age_s = int(when - float(entry["last_seen"]))
        ip = entry.get("ip")
        can_upload = online and bool(ip)
        upload_reason = ""
        if not online:
            upload_reason = "device offline or sighting stale"
        elif not ip:
            upload_reason = "no IP in status"
        rows.append(
            {
                "id": device_id,
                "expected": is_expected(item),
                "online": online,
                "fw": entry.get("fw") or "—",
                "ip": ip or "—",
                "age_s": age_s,
                "ota_port": int(
                    entry.get("ota_port")
                    or item.get("ota_port")
                    or 3232
                ),
                "flash_auto": bool(item.get("flash")),
                "can_upload": can_upload,
                "upload_reason": upload_reason,
                "timeout_sec": timeout,
                "status_topic": item.get("status_topic"),
                "path": item.get("path"),
            }
        )
    return rows


def summarize_rows(rows: List[Dict[str, Any]]) -> Dict[str, int]:
    expected = [r for r in rows if r.get("expected")]
    online_expected = [r for r in expected if r.get("online")]
    return {
        "registered": len(rows),
        "expected": len(expected),
        "online": sum(1 for r in rows if r.get("online")),
        "online_expected": len(online_expected),
    }


class FleetBridge:
    """Load registry, refresh MQTT sightings, flash firmware."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.fleet_cfg = self.config.get("device_fleet") or {}
        self.registry_path = resolve_registry_path(self.config)
        self.state_path = Path(
            self.fleet_cfg.get("state")
            or DEFAULT_STATE
        )
        self._mod = load_device_fleet_module()
        self.registry = self._mod.load_registry(self.registry_path)
        self.state = self._mod.load_state(self.state_path)
        self._lock = threading.Lock()
        self._watch_stop: Optional[threading.Event] = None
        self._watch_thread: Optional[threading.Thread] = None

    def broker(self) -> Tuple[str, int]:
        mqtt_cfg = (self.config.get("mqtt") or {}).get("broker") or {}
        reg_broker = self.registry.get("broker") or {}
        host = (
            mqtt_cfg.get("host")
            or reg_broker.get("host")
            or "192.168.2.4"
        )
        port = int(mqtt_cfg.get("port") or reg_broker.get("port") or 1883)
        return str(host), port

    def listen_sec(self) -> float:
        return float(self.fleet_cfg.get("listen_sec") or 20)

    def refresh(self, wait_sec: Optional[float] = None) -> List[Dict[str, Any]]:
        host, port = self.broker()
        wait = float(wait_sec if wait_sec is not None else self.listen_sec())
        with self._lock:
            self._mod.collect_status(
                self.registry,
                self.state,
                host=host,
                port=port,
                wait_sec=wait,
            )
            self._mod.save_state(self.state_path, self.state)
            return build_device_rows(self.registry, self.state)

    def rows(self) -> List[Dict[str, Any]]:
        with self._lock:
            return build_device_rows(self.registry, self.state)

    def summary(self) -> Dict[str, int]:
        return summarize_rows(self.rows())

    def start_watching(self, on_update: Callable[[List[Dict[str, Any]]], None]) -> None:
        """Background loop: collect MQTT then invoke on_update with rows."""
        self.stop_watching()
        stop = threading.Event()
        self._watch_stop = stop

        def loop() -> None:
            while not stop.is_set():
                try:
                    rows = self.refresh()
                    on_update(rows)
                except Exception as exc:  # pragma: no cover
                    on_update([])
                    # Still surface something via empty rows; panel logs separately.
                    sys.stderr.write(f"fleet watch error: {exc}\n")
                # Pause between listen windows unless stopped.
                if stop.wait(2.0):
                    break

        thread = threading.Thread(target=loop, name="fleet-watch", daemon=True)
        self._watch_thread = thread
        thread.start()

    def stop_watching(self) -> None:
        if self._watch_stop is not None:
            self._watch_stop.set()
        if self._watch_thread is not None and self._watch_thread.is_alive():
            self._watch_thread.join(timeout=2.0)
        self._watch_stop = None
        self._watch_thread = None

    def flash(
        self,
        device_id: str,
        bin_path: Path,
        *,
        password: Optional[str] = None,
        wait_sec: Optional[float] = None,
    ) -> Tuple[int, str]:
        """OTA-flash via device_fleet.py (auto broker fallback). Returns (rc, log)."""
        script = resolve_device_fleet_script()
        bin_path = Path(bin_path).resolve()
        if not bin_path.is_file():
            return 1, f"firmware image not found: {bin_path}"

        host, port = self.broker()
        wait = float(wait_sec if wait_sec is not None else self.listen_sec())
        cmd = [
            sys.executable,
            str(script),
            "--registry",
            str(self.registry_path),
            "--state",
            str(self.state_path),
            "--host",
            host,
            "--port",
            str(port),
            "flash",
            "--id",
            device_id,
            "--bin",
            str(bin_path),
            "--wait",
            str(wait),
        ]
        if password:
            cmd.extend(["--password", password])

        env = os.environ.copy()
        env.setdefault("FLEET_OTA_VIA", "auto")

        completed = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )
        log = (completed.stdout or "") + (completed.stderr or "")
        # Reload state after flash attempt.
        with self._lock:
            self.state = self._mod.load_state(self.state_path)
        return int(completed.returncode), log.strip()
