# Media Server Management

Ubuntu barebone media server at **192.168.2.185** with:

- **SSH** graceful shutdown from the automation server (`192.168.2.4`)
- **Tuya PCIe PC power card** for boot, reset, and force power-off (ATX button simulation)
- **Healthchecks.io** uptime monitoring
- **Node-RED** dashboard controls and configurable daily schedule

## Architecture

```
Node-RED (30–33) → MQTT media/server/command/*
                 → mqtt-boot-listener / mqtt-shutdown-listener
                 → SSH (shutdown) + tinytuya (boot/reset)
Media server     → cron curl → healthchecks.io
health_monitor   → API poll → MQTT media/server/health
```

## Prerequisites

1. Media server on LAN at `192.168.2.185`, user `tinel`
2. Tuya PCIe power card installed, wired to motherboard **PWR_SW** and **RESET** headers
3. Card paired in Tuya Smart / Smart Life app (2.4 GHz WiFi)
4. Healthchecks.io account (API key already on automation server)

---

## 1. SSH setup (automation server → media server)

Run **on the automation server** (`192.168.2.4`):

```bash
cd ~/ServerBootShutdownManagemement
chmod +x scripts/server/setup_media_server_ssh.sh
./scripts/server/setup_media_server_ssh.sh
```

This creates `~/.ssh/media_server_192_168_2_185_ed25519` and adds `Host media-server` to `~/.ssh/config`.

Verify:

```bash
ssh media-server echo ok
```

### Passwordless shutdown (on media server)

```bash
sudo visudo -f /etc/sudoers.d/media-automation
```

Add:

```
tinel ALL=(ALL) NOPASSWD: /sbin/shutdown, /usr/sbin/shutdown, /bin/systemctl poweroff, /bin/systemctl halt
```

Test from automation server:

```bash
ssh media-server 'sudo shutdown -h +1'   # cancel with: sudo shutdown -c
```

---

## 2. Tuya PCIe card — local API credentials

1. Pair the card in the Tuya Smart app
2. Link **all** Tuya devices from your account on the automation server — see **[TUYA_ACCOUNT_LINK.md](TUYA_ACCOUNT_LINK.md)** (recommended):

```bash
cd /opt/dell_server_management
bash scripts/tuya/tuya_link.sh all
```

3. Or manually: create a project at [iot.tuya.com](https://iot.tuya.com), set `TUYA_ACCESS_*` in `.env`, then:

```bash
python3 scripts/tuya/sync_devices.py sync
python3 scripts/tuya/sync_devices.py apply-role media_server
```

4. Legacy alternative: `python -m tinytuya wizard` (writes `devices.json` in home dir)
5. Test local control:

```bash
export $(grep MEDIA_SERVER_TUYA config/.env | xargs)
python scripts/utils/tuya_pc_power_wrapper.py
```

If power status reads `unknown`, adjust DPS IDs in `.env` (see `MEDIA_SERVER_TUYA_DPS_*` in `.env.example`) using the JSON from `tinytuya` status output.

### BIOS / OS tips (from card vendor)

- Disable **ErP Ready** in BIOS if the PC does not wake reliably
- Set Windows/Ubuntu power button action to **Shut down**
- Disable Wake-on-LAN if it conflicts with remote boot

---

## 3. Healthchecks.io

### Create check (healthchecks.io dashboard)

1. New check named **`media_server`** (must match `MEDIA_SERVER_HEALTHCHECKS`)
2. Period: **1 minute**, grace: **5 min**, timeout: **2 min**
3. Copy ping URL: `https://hc-ping.com/<uuid>`

### Automation server `.env`

```bash
MEDIA_SERVER_HEALTHCHECKS="media_server"
MEDIA_SERVER_HEALTHCHECK_PING_URL=https://hc-ping.com/your-uuid
```

### Install ping cron (on media server)

```bash
chmod +x scripts/media_server/install_healthcheck_cron.sh
./scripts/media_server/install_healthcheck_cron.sh https://hc-ping.com/your-uuid
```

---

## 4. Configuration summary

| Variable | Example |
|----------|---------|
| `MEDIA_SERVER_HOST` | `192.168.2.185` |
| `MEDIA_SERVER_SSH_USER` | `tinel` |
| `MEDIA_SERVER_SSH_KEY` | `/home/tinel/.ssh/media_server_192_168_2_185_ed25519` |
| `MEDIA_SERVER_HEALTHCHECKS` | `media_server` |

Server entry: [`config/server_config.yaml`](../config/server_config.yaml) (`type: linux_tuya`, `mqtt_prefix: media/server`).

---

## 5. Deploy on automation server

```bash
cd ~/ServerBootShutdownManagemement
git pull
pip install -r requirements.txt
sudo rsync -a scripts/ /opt/dell_server_management/scripts/
sudo rsync -a config/server_config.yaml /opt/dell_server_management/config/
sudo /opt/dell_server_management/venv/bin/pip install tinytuya
sudo ./manage.sh restart
```

**One-shot finish** (after adding optional secrets to `/opt/dell_server_management/config/.env`):

```bash
# Optional in .env (then run finish script on automation server):
# MEDIA_SERVER_SSH_PASSWORD=...        # one-time for ssh-copy-id
# TUYA_ACCESS_ID / TUYA_ACCESS_SECRET / TUYA_API_REGION=eu
sudo bash /opt/dell_server_management/scripts/media_server/finish_remote_setup.sh
```

**Node-RED** (from dev PC):

```bash
cd nodered/live-connection
node scripts/deploy-media-ui.mjs
```

This deploys flows `30`–`33`, `08-server-dashboard-config.json`, and applies the Server page layout fix (Rolling Log at end, full-width health/schedule).

---

## 6. Node-RED flows

Widgets live on the **Server** dashboard page (`/dashboard/page2`) in the **Server management** group — same layout style as Dell T310 and HP DL360p.

| Order | File | Widget |
|-------|------|--------|
| 15–18 | `30-media-server-controls.json` | Boot, shutdown, reset, force buttons |
| 20 | `31-media-server-status.json` | Status card |
| 21 | `32-media-server-health.json` | Healthchecks.io monitor (full width) |
| 22 | `33-media-server-schedule.json` | Daily schedule config |
| 30 | `90-log-console.json` | Rolling Log (shared; rendered at page end) |

Import **after** `00-base-config.json` and HP flows (`22`). On live Node-RED, use `deploy-media-ui.mjs` instead of manual import.

**Schedule defaults:** boot `08:00`, shutdown `23:30` (editable on dashboard, stored in flow context).

---

## 7. MQTT topics

| Topic | Payload |
|-------|---------|
| `media/server/command/boot` | `{"action":"boot","method":"tuya_power"}` or `"tuya_reset"` |
| `media/server/command/shutdown` | `{"action":"shutdown","type":"graceful"}` or `"force"` |
| `media/server/status` | Status JSON from `status_publisher` |
| `media/server/health` | Healthchecks.io checks |
| `media/server/response` | Command result |

### Manual test

```bash
mosquitto_pub -h 192.168.2.4 -t media/server/command/boot \
  -m '{"action":"boot","method":"tuya_power","request_id":"test-1"}'

mosquitto_pub -h 192.168.2.4 -t media/server/command/shutdown \
  -m '{"action":"shutdown","type":"graceful","request_id":"test-2"}'
```

---

## 8. Troubleshooting

| Issue | Check |
|-------|--------|
| Boot does nothing | Tuya IP/key; card on WiFi; `python -m tinytuya wizard` |
| Graceful shutdown fails | `ssh media-server` works; sudoers for `shutdown` |
| Health always down | Cron on media server; ping URL; check name matches API |
| Status `unknown` | Ping `192.168.2.185`; Tuya relay DPS mapping |

Logs:

```bash
journalctl -u mqtt-boot-listener.service -f
journalctl -u mqtt-shutdown-listener.service -f
journalctl -u status-publisher.service -f
```
