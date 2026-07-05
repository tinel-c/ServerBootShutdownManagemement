#!/usr/bin/env python3
"""Probe HomeGuard NVR RTSP channels and HTTP API (run on automation server)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from urllib.parse import quote

import requests
from requests.auth import HTTPDigestAuth, HTTPBasicAuth


RTSP_PATHS = (
    "live/ch0",
    "live/ch1",
    "live/ch2",
    "live/ch3",
    "11",
    "Streaming/Channels/101",
    "Streaming/Channels/102",
    "Streaming/Channels/201",
    "Streaming/Channels/301",
    "cam/realmonitor?channel=1&subtype=0",
    "cam/realmonitor?channel=2&subtype=0",
)

HTTP_SNAPSHOT_PATHS = (
    "img/snapshot.cgi?size=2",
    "image/1.jpg",
    "image/0.jpg",
    "cgi-bin/snapshot.cgi?channel=1",
)


def probe_rtsp(ip: str, user: str, password: str, port: int = 554) -> None:
    u, p = quote(user, safe=""), quote(password, safe="")
    print(f"\nRTSP probe {ip}:{port}")
    for path in RTSP_PATHS:
        url = f"rtsp://{u}:{p}@{ip}:{port}/{path}"
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
            proc = subprocess.run(cmd, capture_output=True, timeout=15, check=False)
        except subprocess.TimeoutExpired:
            print(f"  TIME  /{path}")
            continue
        ok = proc.returncode == 0 and proc.stdout.startswith(b"\xff\xd8")
        status = "OK" if ok else "FAIL"
        err = (proc.stderr or b"").decode(errors="replace")[:80].strip()
        print(f"  {status:4} /{path} ({len(proc.stdout)} bytes) {err}")


def probe_http(ip: str, user: str, password: str) -> None:
    print(f"\nHTTP probe {ip}")
    for auth in (HTTPDigestAuth(user, password), HTTPBasicAuth(user, password)):
        label = "digest" if isinstance(auth, HTTPDigestAuth) else "basic"
        for path in HTTP_SNAPSHOT_PATHS:
            url = f"http://{ip}/{path}"
            try:
                resp = requests.get(url, auth=auth, timeout=5)
            except requests.RequestException as exc:
                print(f"  ERR  {label} {path}: {exc}")
                continue
            kind = "jpeg" if resp.content.startswith(b"\xff\xd8") else resp.headers.get("content-type", "?")
            print(f"  {resp.status_code} {label} {path} -> {kind} ({len(resp.content)} bytes)")

    for path in ("/api/", "/api/v1/system/info", "/api/system/deviceinfo", "/ISAPI/System/deviceInfo"):
        url = f"http://{ip}{path}"
        try:
            resp = requests.get(url, auth=HTTPDigestAuth(user, password), timeout=5)
            body = resp.text[:200].replace("\n", " ")
            print(f"  GET {path} -> {resp.status_code} {body}")
        except requests.RequestException as exc:
            print(f"  GET {path} -> ERR {exc}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe HomeGuard NVR")
    parser.add_argument("--ip", default="192.168.2.59")
    parser.add_argument("--user", default="tinelc")
    parser.add_argument("--password", default="tinelc")
    args = parser.parse_args()
    probe_http(args.ip, args.user, args.password)
    probe_rtsp(args.ip, args.user, args.password)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
