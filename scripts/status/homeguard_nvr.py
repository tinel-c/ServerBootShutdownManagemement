#!/usr/bin/env python3
"""HomeGuard / OEM NVR HTTP API client (webpack SPA @ /API/*)."""

from __future__ import annotations

import hashlib
import secrets
from typing import Any, Dict, List, Optional, Tuple

import requests
from requests.auth import HTTPDigestAuth

API_PREFIX = "/API"


class HomeGuardNvrError(RuntimeError):
    pass


class HomeGuardNvrClient:
  """Minimal client for NVR web API used by HomeGuard devices."""

  def __init__(
      self,
      ip: str,
      username: str,
      password: str,
      port: int = 80,
      timeout: float = 15.0,
      use_https: bool = False,
  ):
      self.ip = ip
      self.username = username
      self.password = password
      self.port = port
      self.timeout = timeout
      scheme = "https" if use_https else "http"
      if (use_https and port == 443) or (not use_https and port == 80):
          self.base = f"{scheme}://{ip}"
      else:
          self.base = f"{scheme}://{ip}:{port}"
      self.session = requests.Session()
      self.token: Optional[str] = None
      self.user: Optional[str] = None
      self._auth = HTTPDigestAuth(username, password)

  def _url(self, path: str) -> str:
      path = path if path.startswith("/") else f"{API_PREFIX}/{path}"
      if not path.startswith(API_PREFIX):
          path = f"{API_PREFIX}/{path.lstrip('/')}"
      return f"{self.base}{path}"

  def _post(self, path: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
      url = self._url(path)
      headers = {
          "Content-Type": "application/json",
          "X-Requested-With": "XMLHttpRequest",
      }
      body = {"data": data or {}}
      resp = self.session.post(
          url,
          json=body,
          headers=headers,
          auth=self._auth,
          timeout=self.timeout,
      )
      try:
          payload = resp.json()
      except ValueError as exc:
          raise HomeGuardNvrError(f"{path}: HTTP {resp.status_code} non-JSON") from exc
      if resp.status_code >= 400 or payload.get("error_code"):
          code = payload.get("error_code", resp.status_code)
          raise HomeGuardNvrError(f"{path}: {code}")
      return payload.get("data", payload)

  def login_range(self) -> Dict[str, Any]:
      return self._post("Login/Range")

  def get_private_key(self, number: Optional[str] = None) -> Dict[str, Any]:
      num = number or str(secrets.randbelow(900000) + 100000)
      return self._post("Web/Get_Private_Key", {"number": num})

  def _encrypt_password(self, plain: str, key_data: Dict[str, Any]) -> str:
      """Best-effort password encryption matching web client (MD5-based OEM scheme)."""
      key = str(key_data.get("key", ""))
      if not key:
          return plain
      # Common OEM pattern: MD5(password + key) or MD5(key + password)
      for material in (f"{plain}{key}", f"{key}{plain}", plain):
          digest = hashlib.md5(material.encode()).hexdigest()  # noqa: S324
          if material != plain:
              return digest
      return hashlib.md5(f"{plain}{key}".encode()).hexdigest()  # noqa: S324

  def login(self) -> Dict[str, Any]:
      """Authenticate and store session token."""
      self.login_range()
      key_data = self.get_private_key()
      enc_pwd = self._encrypt_password(self.password, key_data)
      data = self._post(
          "Web/Login",
          {
              "user": self.username,
              "password": enc_pwd,
              "key_number": key_data.get("number"),
          },
      )
      self.token = data.get("token")
      self.user = data.get("user", self.username)
      return data

  def _auth_data(self, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
      payload: Dict[str, Any] = {"user": self.user or self.username}
      if self.token:
          payload["token"] = self.token
      if extra:
          payload.update(extra)
      return payload

  def device_info(self) -> Dict[str, Any]:
      return self._post("Login/DeviceInfo/Get", self._auth_data())

  def channel_info(self) -> Dict[str, Any]:
      return self._post("Login/ChannelInfo/Get", self._auth_data())

  def stream_url(self, channel: int, stream_type: str = "substream") -> Dict[str, Any]:
      """Return preview stream URL metadata for a channel (1-based)."""
      return self._post(
          "Preview/StreamUrl",
          self._auth_data(
              {
                  "channel": channel,
                  "stream_type": stream_type,
              }
          ),
      )

  def heartbeat(self) -> Dict[str, Any]:
      return self._post("Login/Heartbeat", self._auth_data())

  def list_online_channels(self) -> List[Dict[str, Any]]:
      info = self.channel_info()
      rows = []
      channel_info = info.get("channel_info") or {}
      if isinstance(channel_info, dict):
          for ch_id, meta in channel_info.items():
              if not isinstance(meta, dict):
                  continue
              if str(meta.get("status", "")).lower() == "offline":
                  continue
              if meta.get("reason"):
                  continue
              try:
                  ch_num = int(ch_id)
              except (TypeError, ValueError):
                  ch_num = int(meta.get("channel", 0) or 0)
              rows.append(
                  {
                      "channel": ch_num,
                      "name": meta.get("name") or meta.get("chn_name") or f"Channel {ch_num}",
                      "meta": meta,
                  }
              )
      rows.sort(key=lambda r: r["channel"])
      return rows


def probe_nvr(ip: str, username: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
      try:
          client = HomeGuardNvrClient(ip, username, password)
          client.login()
          dev = client.device_info()
          channels = client.list_online_channels()
          return True, f"online channels={len(channels)}", {"device": dev, "channels": channels}
      except Exception as exc:
          return False, str(exc), None
