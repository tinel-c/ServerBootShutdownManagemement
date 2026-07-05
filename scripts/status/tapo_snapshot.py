"""ONVIF snapshot capture and JPEG resize for Tapo camera watchdog thumbnails."""

from __future__ import annotations

import io
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import quote, urlparse, urlunparse

import requests
from requests.auth import HTTPDigestAuth

try:
    from PIL import Image
except ImportError:  # pragma: no cover - optional at import time
    Image = None  # type: ignore


def slug_from_mqtt_prefix(mqtt_prefix: str) -> str:
    return mqtt_prefix.rstrip("/").split("/")[-1]


def _fix_snapshot_host(uri: str, camera_ip: str) -> str:
    parsed = urlparse(uri)
    if parsed.port and parsed.port not in (80, 443):
        netloc = f"{camera_ip}:{parsed.port}"
    else:
        netloc = camera_ip
    return urlunparse(parsed._replace(netloc=netloc))


def _extract_snapshot_uri(response: Any) -> Optional[str]:
    """Tapo / ONVIF variants: Uri, MediaUri.Uri, or nested zeep values."""
    direct = getattr(response, "Uri", None)
    if direct:
        return str(direct)

    media = getattr(response, "MediaUri", None)
    if media is None:
        return None
    if isinstance(media, str):
        return media

    nested = getattr(media, "Uri", None) or getattr(media, "_value_1", None)
    if nested:
        return str(nested)
    if hasattr(media, "__dict__"):
        for value in media.__dict__.values():
            if isinstance(value, str) and value.startswith("http"):
                return value
    return None


def capture_onvif_jpeg(
    camera: Any,
    ip: str,
    username: str,
    password: str,
    timeout: float = 15.0,
) -> Optional[bytes]:
    """Fetch a JPEG snapshot via ONVIF GetSnapshotUri."""
    media = camera.create_media_service()
    profiles = media.GetProfiles()
    if not profiles:
        return None

    token = profiles[0].token
    res = media.GetSnapshotUri({"ProfileToken": token})
    uri = _extract_snapshot_uri(res)
    if not uri:
        return None

    uri = _fix_snapshot_host(uri, ip)
    resp = requests.get(
        uri,
        auth=HTTPDigestAuth(username, password),
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.content
    if not data or not data.startswith(b"\xff\xd8"):
        return None
    return data


DEFAULT_RTSP_STREAMS = ("stream1", "stream2")


def capture_rtsp_jpeg(
    ip: str,
    username: str,
    password: str,
    timeout: float = 15.0,
    streams: tuple[str, ...] = DEFAULT_RTSP_STREAMS,
) -> Optional[bytes]:
    """Fallback: grab one frame from Tapo RTSP (port 554). Tries stream1 then stream2."""
    user = quote(username, safe="")
    pwd = quote(password, safe="")
    per_stream_timeout = max(8.0, timeout / max(len(streams), 1))

    for stream in streams:
        url = f"rtsp://{user}:{pwd}@{ip}:554/{stream}"
        cmd = [
            "ffmpeg",
            "-nostdin",
            "-loglevel",
            "error",
            "-rtsp_transport",
            "tcp",
            "-i",
            url,
            "-frames:v",
            "1",
            "-f",
            "image2pipe",
            "-vcodec",
            "mjpeg",
            "pipe:1",
        ]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                timeout=per_stream_timeout,
                check=False,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

        if proc.returncode == 0 and proc.stdout.startswith(b"\xff\xd8"):
            return proc.stdout
    return None


def capture_camera_jpeg(
    camera: Any,
    ip: str,
    username: str,
    password: str,
    timeout: float = 15.0,
) -> Optional[bytes]:
    """ONVIF snapshot first, then RTSP/ffmpeg fallback."""
    try:
        data = capture_onvif_jpeg(camera, ip, username, password, timeout=timeout)
        if data:
            return data
    except Exception:
        pass
    return capture_rtsp_jpeg(ip, username, password, timeout=timeout)


def resize_jpeg(data: bytes, max_width: int) -> bytes:
    """Downscale JPEG for MQTT/dashboard; returns original if Pillow unavailable."""
    if max_width <= 0 or Image is None:
        return data

    img = Image.open(io.BytesIO(data))
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    if img.width <= max_width:
        out = io.BytesIO()
        img.save(out, format="JPEG", quality=82, optimize=True)
        return out.getvalue()

    ratio = max_width / img.width
    size = (max_width, max(1, int(img.height * ratio)))
    img = img.resize(size, Image.Resampling.LANCZOS)
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=82, optimize=True)
    return out.getvalue()


def save_snapshot_jpeg(slug: str, jpeg: bytes, snapshot_dir: str) -> str:
    """Write JPEG atomically; returns public URL path."""
    root = Path(snapshot_dir)
    root.mkdir(parents=True, exist_ok=True)
    dest = root / f"{slug}.jpg"
    tmp = root / f"{slug}.jpg.tmp"
    tmp.write_bytes(jpeg)
    tmp.replace(dest)
    return f"/camera-snapshots/{slug}.jpg"


def build_snapshot_payload(
    slug: str,
    camera_name: str,
    timestamp: str,
    image_url: str,
) -> Dict[str, Any]:
    return {
        "timestamp": timestamp,
        "slug": slug,
        "camera_name": camera_name,
        "content_type": "image/jpeg",
        "image_url": image_url,
    }
