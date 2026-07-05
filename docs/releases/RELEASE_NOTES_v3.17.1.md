# v3.17.1 (2026-07-05) — Camera credentials hygiene & Gazon Curte fix

Patch release: fixes **Gazon Curte** ONVIF authentication and removes camera/NVR credentials from tracked repo files.

## Fixed

- **Gazon Curte (`gazonCurte`, TC65 @ 192.168.2.38)** — uses a dedicated Tapo Camera Account on the server (`CAMERA_4_USER` / `CAMERA_4_PASS` in `config/.env`). All seven cameras now pass `camera_connect.py`.

## Changed — security

| Before | After |
|--------|--------|
| `apply_cameras_env.py` embedded `tinelc` / passwords in git | Placeholders only; **preserves** credentials from existing server `.env` |
| `probe_homeguard_nvr.py` default `tinelc`/`tinelc` | No default credentials (`--user` / `--password` required) |
| Docs/examples showed real usernames | `YOUR_CAMERA_ACCOUNT` / `your_camera_password` placeholders |

**Rule:** Tapo Camera Account credentials belong in **`/opt/dell_server_management/config/.env`** on the automation server only — never in git.

## Upgrade

```bash
git pull
# Re-apply camera metadata (keeps existing credentials on server):
sudo python3 scripts/server/apply_cameras_env.py
sudo systemctl restart tapo-monitor.service
sudo /opt/dell_server_management/venv/bin/python3 scripts/status/camera_connect.py
```

## Note on git history

Commit `3ce633b` and later briefly contained `tinelc` in `apply_cameras_env.py` on GitHub. This release removes them from **HEAD**. Rotate the Tapo Camera Account password if the repo is or was public.
