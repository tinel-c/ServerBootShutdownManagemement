#!/usr/bin/env python3
"""Online device catalog for the Windows client.

The fleet list is the GitHub copy of ``scripts/status/device_fleet.yaml`` plus
``device/tasmota/catalog.yaml``. A file under LocalAppData is only a cache used
when GitHub cannot be reached. An explicit ``device_fleet.registry`` path, or
``device_fleet.catalog: local``, keeps the old on-disk registry.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

DEFAULT_REPO = "tinel-c/ServerBootShutdownManagemement"
DEFAULT_REF = "main"
FLEET_REPO_PATH = "scripts/status/device_fleet.yaml"
TASMOTA_REPO_PATH = "device/tasmota/catalog.yaml"

SCAN_FIELDS = (
    "ip",
    "fw",
    "mac",
    "hostname",
    "hardware",
    "module",
    "friendly_name",
    "auth_required",
    "last_scan",
)

FetchFn = Callable[[str], str]


@dataclass
class CatalogResult:
    registry: Dict[str, Any]
    source: str
    note: str
    registry_path: Path
    tasmota_catalog_path: Optional[Path]


def raw_github_url(repo: str, ref: str, path: str) -> str:
    repo = repo.strip().strip("/")
    ref = ref.strip().strip("/")
    path = path.strip().lstrip("/")
    return f"https://raw.githubusercontent.com/{repo}/{ref}/{path}"


def catalog_mode(config: Optional[Dict[str, Any]]) -> str:
    """``github`` unless the user pinned a local registry."""
    cfg = (config or {}).get("device_fleet") or {}
    override = str(cfg.get("registry") or "").strip()
    if override and not override.startswith("${"):
        path = Path(override).expanduser()
        if path.is_file():
            return "local"
    mode = str(cfg.get("catalog") or "github").strip().lower()
    if mode.startswith("${") or mode not in ("github", "local"):
        return "github"
    return mode


def github_repo_ref(config: Optional[Dict[str, Any]]) -> tuple:
    cfg = (config or {}).get("device_fleet") or {}
    repo = str(cfg.get("github_repo") or DEFAULT_REPO).strip()
    ref = str(cfg.get("github_ref") or DEFAULT_REF).strip()
    if not repo or repo.startswith("${"):
        repo = DEFAULT_REPO
    if not ref or ref.startswith("${"):
        ref = DEFAULT_REF
    return repo, ref


def fetch_text(url: str, timeout: float = 15.0) -> str:
    import os

    import requests

    headers = {
        "Accept": "application/vnd.github.raw",
        "User-Agent": "ClientMonitor-device-catalog",
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = requests.get(url, headers=headers, timeout=timeout)
    if response.status_code == 404:
        raise FileNotFoundError(url)
    response.raise_for_status()
    return response.text


def parse_yaml_text(text: str, *, label: str) -> Dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML is required (pip install pyyaml)")
    data = yaml.safe_load(text) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{label} is not a YAML mapping")
    devices = data.get("devices") or []
    if not isinstance(devices, list):
        raise ValueError(f"{label} devices is not a list")
    return data


def load_yaml_file(path: Path) -> Dict[str, Any]:
    return parse_yaml_text(path.read_text(encoding="utf-8"), label=str(path))


def repo_tasmota_catalog(repo_root: Path) -> Optional[Path]:
    """Catalog file inside a checkout of this repo, if that checkout is present."""
    marker = repo_root / "scripts" / "status" / "device_fleet.yaml"
    if marker.is_file():
        return repo_root / "device" / "tasmota" / "catalog.yaml"
    return None


def _blank(value: Any) -> bool:
    return value is None or value == "" or value == []


def device_id_for(*, topic: Optional[str] = None, mac: Optional[str] = None, ip: Optional[str] = None) -> str:
    if topic:
        return f"tasmota/{topic}"
    if mac:
        compact = "".join(ch for ch in str(mac).lower() if ch.isalnum())
        if compact:
            return f"tasmota/{compact}"
    if ip:
        return "tasmota/ip-" + str(ip).replace(".", "-")
    raise ValueError("Tasmota device needs a topic, MAC, or IP")


def normalize_tasmota(item: Dict[str, Any]) -> Dict[str, Any]:
    """One catalog row, shaped so the fleet panel can list it."""
    topic = str(item.get("topic") or "").strip()
    raw_id = str(item.get("id") or "").strip()
    if not topic and raw_id.startswith("tasmota/"):
        suffix = raw_id.split("/", 1)[1]
        if not suffix.startswith("ip-") and not _looks_like_mac(suffix):
            topic = suffix
    if not raw_id:
        raw_id = device_id_for(
            topic=topic or None,
            mac=item.get("mac"),
            ip=item.get("ip"),
        )
    if topic:
        status_topic = str(item.get("status_topic") or f"tele/{topic}/LWT")
    else:
        status_topic = str(item.get("status_topic") or f"fleet/tasmota/{raw_id}/seen")
    row: Dict[str, Any] = {
        "id": raw_id,
        "kind": "tasmota",
        "topic": topic,
        "name": item.get("name") or topic or raw_id,
        "path": item.get("path") or "device/tasmota",
        "status_topic": status_topic,
        "timeout_sec": int(item.get("timeout_sec") or 660),
        "expected": item.get("expected", True) is not False,
        "flash": False,
    }
    role = item.get("role")
    if not _blank(role):
        row["role"] = role
    for key in SCAN_FIELDS:
        if not _blank(item.get(key)):
            row[key] = item.get(key)
    return row


def _looks_like_mac(text: str) -> bool:
    compact = "".join(ch for ch in text.lower() if ch.isalnum())
    return len(compact) == 12 and all(ch in "0123456789abcdef" for ch in compact)


def _index_tasmota(devices: Sequence[Dict[str, Any]]) -> tuple:
    by_id: Dict[str, Dict[str, Any]] = {}
    by_topic: Dict[str, Dict[str, Any]] = {}
    by_mac: Dict[str, Dict[str, Any]] = {}
    by_ip: Dict[str, Dict[str, Any]] = {}
    for item in devices:
        if item.get("kind") != "tasmota" and not str(item.get("id") or "").startswith("tasmota/"):
            continue
        by_id[str(item.get("id"))] = item
        topic = str(item.get("topic") or "")
        if topic:
            by_topic[topic] = item
        mac = _mac_key(item.get("mac"))
        if mac:
            by_mac[mac] = item
        ip = str(item.get("ip") or "")
        if ip:
            by_ip[ip] = item
    return by_id, by_topic, by_mac, by_ip


def _mac_key(mac: Any) -> str:
    if not mac:
        return ""
    return "".join(ch for ch in str(mac).lower() if ch.isalnum())


def _find_tasmota(
    incoming: Dict[str, Any],
    by_id: Dict[str, Dict[str, Any]],
    by_topic: Dict[str, Dict[str, Any]],
    by_mac: Dict[str, Dict[str, Any]],
    by_ip: Dict[str, Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    found = by_id.get(str(incoming.get("id")))
    if found:
        return found
    topic = str(incoming.get("topic") or "")
    if topic and topic in by_topic:
        return by_topic[topic]
    mac = _mac_key(incoming.get("mac"))
    if mac and mac in by_mac:
        return by_mac[mac]
    ip = str(incoming.get("ip") or "")
    if ip and ip in by_ip:
        return by_ip[ip]
    return None


def merge_tasmota(
    devices: List[Dict[str, Any]],
    incoming: Iterable[Dict[str, Any]],
    *,
    overwrite_scan_fields: bool = False,
) -> List[Dict[str, Any]]:
    """Add Tasmota rows. Existing friendly names stay unless a scan fills blanks."""
    rows = list(devices)
    by_id, by_topic, by_mac, by_ip = _index_tasmota(rows)
    for item in incoming:
        if not isinstance(item, dict):
            continue
        try:
            norm = normalize_tasmota(item)
        except ValueError:
            continue
        prev = _find_tasmota(norm, by_id, by_topic, by_mac, by_ip)
        if prev is None:
            rows.append(norm)
            by_id[norm["id"]] = norm
            if norm.get("topic"):
                by_topic[str(norm["topic"])] = norm
            mac = _mac_key(norm.get("mac"))
            if mac:
                by_mac[mac] = norm
            if norm.get("ip"):
                by_ip[str(norm["ip"])] = norm
            continue
        if overwrite_scan_fields:
            _apply_scan_fields(prev, norm)
        else:
            _fill_blanks(prev, norm)
        if prev.get("topic"):
            by_topic[str(prev["topic"])] = prev
        mac = _mac_key(prev.get("mac"))
        if mac:
            by_mac[mac] = prev
        if prev.get("ip"):
            by_ip[str(prev["ip"])] = prev
        if item.get("id") != prev.get("id"):
            item["id"] = prev["id"]
    return _order_devices(rows)


def _fill_blanks(prev: Dict[str, Any], incoming: Dict[str, Any]) -> None:
    for key, value in incoming.items():
        if key in ("id", "kind"):
            continue
        if _blank(prev.get(key)) and not _blank(value):
            prev[key] = value


def _apply_scan_fields(prev: Dict[str, Any], found: Dict[str, Any]) -> None:
    for key in SCAN_FIELDS:
        value = found.get(key)
        if not _blank(value):
            prev[key] = value
    if found.get("topic") and _blank(prev.get("topic")):
        prev["topic"] = found["topic"]
        prev["status_topic"] = found.get("status_topic") or f"tele/{found['topic']}/LWT"
    current_name = str(prev.get("name") or "")
    current_topic = str(prev.get("topic") or "")
    if _blank(current_name) or current_name in (current_topic, prev.get("id")):
        replacement = found.get("friendly_name") or found.get("name")
        if replacement and replacement != current_topic:
            prev["name"] = replacement
        elif _blank(current_name) and found.get("name"):
            prev["name"] = found["name"]


def _order_devices(devices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    firmware = [item for item in devices if item.get("kind") != "tasmota"]
    tasmota = [item for item in devices if item.get("kind") == "tasmota"]
    tasmota.sort(key=lambda item: str(item.get("name") or item.get("id")).lower())
    return firmware + tasmota


def assemble_registry(fleet: Dict[str, Any], *tasmota_groups: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    devices: List[Dict[str, Any]] = []
    for item in fleet.get("devices") or []:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        row = dict(item)
        if row.get("kind") == "tasmota" or str(row.get("id") or "").startswith("tasmota/"):
            row["kind"] = "tasmota"
            row["flash"] = False
        else:
            row.setdefault("kind", "firmware")
        devices.append(row)
    for group in tasmota_groups:
        devices = merge_tasmota(devices, group, overwrite_scan_fields=False)
    if not devices:
        raise ValueError("Device catalog has no devices")
    assembled = dict(fleet)
    assembled["devices"] = _order_devices(devices)
    return assembled


def tasmota_devices(registry: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [item for item in (registry.get("devices") or []) if item.get("kind") == "tasmota"]


def yaml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        return str(value)
    text = str(value)
    special = (":", "#", "{", "}", "[", "]", "&", "*", "!", "|", ">", "'", '"', "%", "@", "`", "\n")
    if text == "" or any(ch in text for ch in special) or text.lower() in ("true", "false", "null", "yes", "no"):
        return json.dumps(text, ensure_ascii=False)
    return text


def dump_tasmota_catalog(devices: Sequence[Dict[str, Any]]) -> str:
    """Human-readable catalog committed under device/tasmota/."""
    rows = [item for item in devices if item.get("kind") == "tasmota" or str(item.get("id") or "").startswith("tasmota/")]
    rows = sorted(rows, key=lambda item: str(item.get("name") or item.get("id")).lower())
    lines = [
        "# Tasmota devices on the automation LAN.",
        "# The Windows client fetches this file from GitHub and lists it with the firmware fleet.",
        "# Device Fleet → Scan Tasmota refreshes addresses and adds newly found boards.",
        "version: 1",
        "devices:",
    ]
    if not rows:
        lines.append("  []")
        return "\n".join(lines) + "\n"
    fields = (
        "topic",
        "name",
        "role",
        "status_topic",
        "timeout_sec",
        "expected",
        "kind",
        "flash",
        "path",
        "hostname",
        "mac",
        "ip",
        "fw",
        "hardware",
        "module",
        "friendly_name",
        "auth_required",
        "last_scan",
    )
    for item in rows:
        lines.append(f"  - id: {yaml_scalar(item.get('id'))}")
        for key in fields:
            if key not in item or _blank(item.get(key)):
                continue
            lines.append(f"    {key}: {yaml_scalar(item.get(key))}")
    return "\n".join(lines) + "\n"


def write_tasmota_catalog(path: Path, devices: Sequence[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_tasmota_catalog(devices), encoding="utf-8")


def write_registry_cache(path: Path, registry: Dict[str, Any]) -> None:
    if yaml is None:
        raise RuntimeError("PyYAML is required (pip install pyyaml)")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(registry, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def _tasmota_from_yaml(data: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not data:
        return []
    return [item for item in (data.get("devices") or []) if isinstance(item, dict)]


def load_merged_catalog(
    config: Optional[Dict[str, Any]],
    *,
    local_fleet_path: Optional[Path],
    cache_path: Path,
    repo_root: Path,
    fetch: Optional[FetchFn] = None,
) -> CatalogResult:
    """GitHub fleet + Tasmota catalog, with local fallback."""
    mode = catalog_mode(config)
    catalog_file = repo_tasmota_catalog(repo_root)
    local_tasmota: List[Dict[str, Any]] = []
    if catalog_file and catalog_file.is_file():
        local_tasmota = _tasmota_from_yaml(load_yaml_file(catalog_file))

    cache_tasmota: List[Dict[str, Any]] = []
    if cache_path.is_file():
        try:
            cache_tasmota = tasmota_devices(load_yaml_file(cache_path))
        except (OSError, ValueError, yaml.YAMLError if yaml else Exception):
            cache_tasmota = []

    if mode == "local":
        if local_fleet_path is None or not local_fleet_path.is_file():
            raise FileNotFoundError(
                "device_fleet.yaml not found. Set device_fleet.registry or device_fleet.catalog: github."
            )
        fleet = load_yaml_file(local_fleet_path)
        registry = assemble_registry(fleet, local_tasmota, cache_tasmota)
        return CatalogResult(
            registry=registry,
            source="local",
            note=f"Local registry {local_fleet_path}",
            registry_path=local_fleet_path,
            tasmota_catalog_path=catalog_file,
        )

    repo, ref = github_repo_ref(config)
    getter = fetch or fetch_text
    fleet_url = raw_github_url(repo, ref, FLEET_REPO_PATH)
    tasmota_url = raw_github_url(repo, ref, TASMOTA_REPO_PATH)
    try:
        fleet = parse_yaml_text(getter(fleet_url), label=FLEET_REPO_PATH)
        if not fleet.get("devices"):
            raise ValueError(f"No devices in {fleet_url}")
        github_tasmota: List[Dict[str, Any]] = []
        try:
            github_tasmota = _tasmota_from_yaml(
                parse_yaml_text(getter(tasmota_url), label=TASMOTA_REPO_PATH)
            )
        except FileNotFoundError:
            github_tasmota = []
        registry = assemble_registry(fleet, github_tasmota, local_tasmota, cache_tasmota)
        write_registry_cache(cache_path, registry)
        note = (
            f"GitHub {repo}@{ref} "
            f"({FLEET_REPO_PATH} + {TASMOTA_REPO_PATH})"
        )
        return CatalogResult(
            registry=registry,
            source="github",
            note=note,
            registry_path=cache_path,
            tasmota_catalog_path=catalog_file,
        )
    except Exception as exc:
        if cache_path.is_file():
            try:
                cached = load_yaml_file(cache_path)
                if cached.get("devices"):
                    registry = assemble_registry(cached, local_tasmota)
                    return CatalogResult(
                        registry=registry,
                        source="fallback",
                        note=f"Cached catalog ({exc})",
                        registry_path=cache_path,
                        tasmota_catalog_path=catalog_file,
                    )
            except (OSError, ValueError):
                pass
        if local_fleet_path is None or not local_fleet_path.is_file():
            raise FileNotFoundError(
                f"Could not fetch the device catalog from GitHub ({exc}) and no local registry exists."
            ) from exc
        fleet = load_yaml_file(local_fleet_path)
        registry = assemble_registry(fleet, local_tasmota, cache_tasmota)
        return CatalogResult(
            registry=registry,
            source="fallback",
            note=f"Local fallback {local_fleet_path} (GitHub fetch failed: {exc})",
            registry_path=local_fleet_path,
            tasmota_catalog_path=catalog_file,
        )
