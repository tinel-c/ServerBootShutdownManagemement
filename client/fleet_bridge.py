#!/usr/bin/env python3
"""Bridge between the Windows client UI and scripts/status/device_fleet.py."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from device_catalog import (
    load_merged_catalog,
    tasmota_devices,
    write_registry_cache,
    write_tasmota_catalog,
)

CLIENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CLIENT_DIR.parent
STATE_DIR = Path(os.getenv("LOCALAPPDATA", str(CLIENT_DIR))) / "ClientMonitor"
DEFAULT_STATE = STATE_DIR / "device_fleet_state.json"
DEFAULT_CACHE = STATE_DIR / "device_catalog.yaml"


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


def sighting_is_offline(entry: Dict[str, Any]) -> bool:
    """Tasmota LWT is the literal Offline, which is still a fresh MQTT message."""
    text = str(entry.get("last_payload") or "").strip().strip('"').lower()
    return text == "offline"


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
        kind = "tasmota" if item.get("kind") == "tasmota" else "firmware"
        entry = (state.get("devices") or {}).get(device_id) or {}
        timeout = int(item.get("timeout_sec") or (660 if kind == "tasmota" else 90))
        online = bool(fleet.is_online(entry, timeout, now=when))
        if kind == "tasmota" and sighting_is_offline(entry):
            online = False
        age_s: Optional[int] = None
        if entry.get("last_seen") is not None:
            age_s = int(when - float(entry["last_seen"]))
        ip = entry.get("ip") or item.get("ip")
        fw = entry.get("fw") or item.get("fw") or "—"
        if kind == "tasmota":
            can_upload = False
            upload_reason = "Tasmota uses its own web OTA"
            ota_port = None
        else:
            can_upload = online and bool(ip)
            upload_reason = ""
            if not online:
                upload_reason = "device offline or sighting stale"
            elif not ip:
                upload_reason = "no IP in status"
            ota_port = int(entry.get("ota_port") or item.get("ota_port") or 3232)
        name = str(item.get("name") or device_id)
        topic = str(item.get("topic") or "")
        rows.append(
            {
                "id": device_id,
                "kind": kind,
                "name": name,
                "topic": topic,
                "expected": is_expected(item),
                "online": online,
                "fw": fw,
                "ip": ip or "—",
                "age_s": age_s,
                "ota_port": ota_port if ota_port is not None else "—",
                "flash_auto": bool(item.get("flash")),
                "can_upload": can_upload,
                "upload_reason": upload_reason,
                "timeout_sec": timeout,
                "status_topic": item.get("status_topic"),
                "path": item.get("path"),
                "rssi": entry.get("rssi"),
                "last_payload": entry.get("last_payload") or "",
            }
        )
    return rows


def summarize_rows(rows: List[Dict[str, Any]]) -> Dict[str, int]:
    expected = [r for r in rows if r.get("expected")]
    online_expected = [r for r in expected if r.get("online")]
    tasmota = [r for r in rows if r.get("kind") == "tasmota"]
    return {
        "registered": len(rows),
        "expected": len(expected),
        "online": sum(1 for r in rows if r.get("online")),
        "online_expected": len(online_expected),
        "tasmota": len(tasmota),
        "tasmota_online": sum(1 for r in tasmota if r.get("online")),
    }


class FleetBridge:
    """Load registry, refresh MQTT sightings, flash firmware."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.fleet_cfg = self.config.get("device_fleet") or {}
        self.state_path = Path(self.fleet_cfg.get("state") or DEFAULT_STATE)
        self.cache_path = Path(self.fleet_cfg.get("cache") or DEFAULT_CACHE)
        self._mod = load_device_fleet_module()
        self._lock = threading.Lock()
        self._apply_catalog(self._load_catalog())
        self.state = self._mod.load_state(self.state_path)
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

    def _local_fleet_path(self) -> Optional[Path]:
        try:
            return resolve_registry_path(self.config)
        except FileNotFoundError:
            return None

    def _load_catalog(self):
        return load_merged_catalog(
            self.config,
            local_fleet_path=self._local_fleet_path(),
            cache_path=self.cache_path,
            repo_root=REPO_ROOT,
        )

    def _apply_catalog(self, loaded) -> None:
        self.registry = loaded.registry
        self.registry_path = loaded.registry_path
        self.catalog_source = loaded.source
        self.catalog_note = loaded.note
        self.tasmota_catalog_path = loaded.tasmota_catalog_path

    def reload_catalog(self) -> str:
        """Fetch the GitHub catalog again. Returns the source note."""
        loaded = self._load_catalog()
        with self._lock:
            self._apply_catalog(loaded)
            return self.catalog_note

    def refresh(self, wait_sec: Optional[float] = None, *, reload_catalog: bool = False) -> List[Dict[str, Any]]:
        if reload_catalog:
            self.reload_catalog()
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

    def publish_mqtt(self, topic: str, payload: str) -> None:
        """Publish one command. Raises on broker errors."""
        host, port = self.broker()
        client = _mqtt_client(f"fleet-cmd-{os.getpid()}")
        client.connect(host, port, keepalive=15)
        client.loop_start()
        try:
            info = client.publish(topic, payload, qos=1)
            info.wait_for_publish(timeout=5)
        finally:
            client.loop_stop()
            client.disconnect()

    def listen_topics(
        self,
        topics: List[str],
        on_message: Callable[[str, str], None],
        stop: threading.Event,
    ) -> None:
        """Subscribe until stop is set. on_message runs on the MQTT thread."""
        if not topics:
            return
        host, port = self.broker()
        client = _mqtt_client(f"fleet-detail-{os.getpid()}")

        def _on_message(_client, _userdata, msg) -> None:
            try:
                text = msg.payload.decode("utf-8", "replace")
            except Exception:
                text = ""
            on_message(str(msg.topic), text)

        client.on_message = _on_message
        client.connect(host, port, keepalive=30)
        for topic in topics:
            client.subscribe(topic, qos=0)
        client.loop_start()
        try:
            while not stop.wait(0.4):
                pass
        finally:
            client.loop_stop()
            try:
                client.disconnect()
            except Exception:
                pass

    def stop_watching(self) -> None:
        if self._watch_stop is not None:
            self._watch_stop.set()
        if self._watch_thread is not None and self._watch_thread.is_alive():
            self._watch_thread.join(timeout=2.0)
        self._watch_stop = None
        self._watch_thread = None

    def scan_tasmota(self) -> Dict[str, Any]:
        """Find Tasmota boards and merge them into the device-folder catalog."""
        from tasmota_discover import discover_tasmota, state_payload_for

        from device_catalog import merge_tasmota

        host, port = self.broker()
        known = [
            str(item.get("topic"))
            for item in (self.registry.get("devices") or [])
            if item.get("topic")
        ]
        wait = float(self.fleet_cfg.get("tasmota_scan_sec") or 8)
        http_flag = self.fleet_cfg.get("tasmota_http_scan", True)
        if isinstance(http_flag, str):
            http_flag = http_flag.strip().lower() in ("1", "true", "yes", "on")
        subnets = self.fleet_cfg.get("scan_subnets") or None
        if isinstance(subnets, str):
            subnets = [part.strip() for part in subnets.split(",") if part.strip()]
        report = discover_tasmota(
            host,
            port,
            known_topics=known,
            wait_sec=wait,
            http=bool(http_flag),
            subnets=subnets,
        )
        with self._lock:
            before = {str(item.get("id")) for item in tasmota_devices(self.registry)}
            merged = merge_tasmota(
                list(self.registry.get("devices") or []),
                report.get("devices") or [],
                overwrite_scan_fields=True,
            )
            self.registry["devices"] = merged
            for device in report.get("devices") or []:
                payload = state_payload_for(device, str(device.get("lwt") or ""))
                self._mod.record_sighting(
                    self.state,
                    str(device["id"]),
                    payload,
                    default_ota_port=int(device.get("ota_port") or 0),
                )
            self._mod.save_state(self.state_path, self.state)
            if self.tasmota_catalog_path is not None and report.get("devices"):
                write_tasmota_catalog(self.tasmota_catalog_path, merged)
                report["catalog_path"] = str(self.tasmota_catalog_path)
            else:
                report["catalog_path"] = ""
            try:
                write_registry_cache(self.cache_path, self.registry)
            except OSError as exc:
                report["cache_error"] = str(exc)
            after = [str(item.get("id")) for item in tasmota_devices(self.registry)]
            report["added"] = [device_id for device_id in after if device_id not in before]
            report["updated"] = [device_id for device_id in after if device_id in before]
        return report

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


def _mqtt_client(client_id: str):
    import paho.mqtt.client as mqtt

    if hasattr(mqtt, "CallbackAPIVersion"):
        return mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
    return mqtt.Client(client_id=client_id)


PANEL_TITLE = "Device Fleet"
PANEL_PID = STATE_DIR / "device_fleet_panel.pid"
PANEL_CONFIG = STATE_DIR / "device_fleet_panel_config.json"
_CREATE_NO_WINDOW = 0x08000000


def gui_python() -> Path:
    """pythonw so the fleet window does not open a console."""
    exe = Path(sys.executable)
    if os.name == "nt":
        pythonw = exe.with_name("pythonw.exe")
        if pythonw.is_file():
            return pythonw
    return exe


def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name != "nt":
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        return True
    import ctypes

    handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, int(pid))
    if not handle:
        return False
    ctypes.windll.kernel32.CloseHandle(handle)
    return True


def read_panel_pid() -> int:
    try:
        return int(PANEL_PID.read_text(encoding="ascii").strip() or "0")
    except (OSError, ValueError):
        return 0


def claim_panel_process(pid: Optional[int] = None) -> bool:
    """Exclusive owner of the fleet window. A live owner keeps the claim."""
    PANEL_PID.parent.mkdir(parents=True, exist_ok=True)
    me = int(os.getpid() if pid is None else pid)
    for _ in range(2):
        try:
            fd = os.open(str(PANEL_PID), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            other = read_panel_pid()
            if pid_alive(other):
                return False
            try:
                PANEL_PID.unlink()
            except OSError:
                return False
            continue
        os.write(fd, str(me).encode("ascii"))
        os.close(fd)
        return True
    return False


def release_panel_process() -> None:
    if read_panel_pid() != os.getpid():
        return
    try:
        PANEL_PID.unlink()
    except OSError:
        pass


def raise_device_fleet_window() -> bool:
    """Bring an existing Device Fleet window forward. No Tk import."""
    if os.name != "nt":
        return False
    import ctypes

    user32 = ctypes.windll.user32
    hwnd = user32.FindWindowW(None, PANEL_TITLE)
    if not hwnd:
        return False
    user32.ShowWindow(hwnd, 9)  # SW_RESTORE
    user32.SetForegroundWindow(hwnd)
    return True


def launch_device_fleet_panel(config: Optional[Dict[str, Any]] = None) -> None:
    """Open Device Fleet in a separate process.

    The tray client also runs pystray. Loading Tk in that same process aborts
    python inside tcl86t.dll and takes the tray icon with it.
    """
    if raise_device_fleet_window():
        return
    if pid_alive(read_panel_pid()):
        return
    PANEL_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(config or {}, ensure_ascii=False, default=str)
    tmp = PANEL_CONFIG.with_suffix(".json.tmp")
    tmp.write_text(payload, encoding="utf-8")
    tmp.replace(PANEL_CONFIG)
    script = CLIENT_DIR / "device_fleet_panel.py"
    exe = gui_python()
    kwargs: Dict[str, Any] = {
        "cwd": str(CLIENT_DIR),
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "close_fds": True,
    }
    if os.name == "nt":
        kwargs["creationflags"] = _CREATE_NO_WINDOW
    subprocess.Popen([str(exe), str(script), "--config", str(PANEL_CONFIG)], **kwargs)
