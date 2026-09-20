#!/bin/bash
#
# Move growing data off the root SSD (/) onto the data HDD (/data):
#   automation / syslog / journal logs, Home Assistant logs, Mosquitto logs,
#   camera snapshots, and (optionally) the swap file.
# Safe to re-run (idempotent). Requires root and a mounted /data volume.
#
# Usage:
#   sudo bash scripts/server/setup_data_drive_logs.sh
#   sudo SETUP_DATA_SWAP=0 bash scripts/server/setup_data_drive_logs.sh   # skip swap move
#
set -euo pipefail

DATA_ROOT="${DATA_LOG_ROOT:-/data/logs}"
AUTOMATION_LOG_DIR="${DATA_ROOT}/automation"
SYSLOG_DIR="${DATA_ROOT}/syslog"
JOURNAL_DIR="${DATA_ROOT}/journal"
HA_LOG_DIR="${DATA_ROOT}/homeassistant"
MOSQUITTO_LOG_DIR="${DATA_ROOT}/mosquitto"
SNAPSHOT_DIR="${DATA_SNAPSHOT_DIR:-/data/camera-snapshots}"
DATA_SWAP="${DATA_SWAP_FILE:-/data/swapfile}"
SETUP_DATA_SWAP="${SETUP_DATA_SWAP:-1}"
LOGROTATE_FILE="/etc/logrotate.d/dell_server_management"
JOURNALD_DROPIN="/etc/systemd/journald.conf.d/95-data-drive.conf"
FSTAB="/etc/fstab"
ENV_FILE="${ENV_FILE:-/opt/dell_server_management/config/.env}"
APP_LOG_NAME="dell_server_management.log"
HA_CONFIG_DIR="${HA_CONFIG_DIR:-/home/homeassistant/.homeassistant}"

log() { echo "[setup-data-logs] $*"; }
die() { echo "[setup-data-logs] ERROR: $*" >&2; exit 1; }

[[ "$(id -u)" -eq 0 ]] || die "Run as root (sudo)"

mountpoint -q /data || die "/data is not mounted — attach/mount the second disk first"
[[ -d /data ]] || die "/data missing"

mkdir -p "$AUTOMATION_LOG_DIR" "$SYSLOG_DIR" "$JOURNAL_DIR" "$HA_LOG_DIR" "$MOSQUITTO_LOG_DIR" "$SNAPSHOT_DIR"
chmod 755 "$DATA_ROOT" "$AUTOMATION_LOG_DIR" "$SYSLOG_DIR" "$HA_LOG_DIR" "$MOSQUITTO_LOG_DIR" "$SNAPSHOT_DIR"
# journald expects machine-id owned dirs; keep sticky root
chmod 2755 "$JOURNAL_DIR"

# ---------------------------------------------------------------------------
# 1) Application LOG_FILE → /data/logs/automation/
# ---------------------------------------------------------------------------
APP_LOG="${AUTOMATION_LOG_DIR}/${APP_LOG_NAME}"
if [[ -f "/var/log/${APP_LOG_NAME}" && ! -L "/var/log/${APP_LOG_NAME}" ]]; then
  log "Moving existing /var/log/${APP_LOG_NAME} → ${APP_LOG}"
  cat "/var/log/${APP_LOG_NAME}" >> "${APP_LOG}" 2>/dev/null || cp -a "/var/log/${APP_LOG_NAME}" "${APP_LOG}"
  rm -f "/var/log/${APP_LOG_NAME}"
fi
touch "$APP_LOG"
chmod 644 "$APP_LOG"
ln -sfn "$APP_LOG" "/var/log/${APP_LOG_NAME}"

if [[ -f "$ENV_FILE" ]]; then
  if grep -q '^LOG_FILE=' "$ENV_FILE"; then
    sed -i "s|^LOG_FILE=.*|LOG_FILE=${APP_LOG}|" "$ENV_FILE"
  else
    printf '\nLOG_FILE=%s\n' "$APP_LOG" >> "$ENV_FILE"
  fi
  log "Updated LOG_FILE in ${ENV_FILE}"
else
  log "WARN: ${ENV_FILE} not found — set LOG_FILE=${APP_LOG} manually"
fi

cat > "$LOGROTATE_FILE" <<EOF
${AUTOMATION_LOG_DIR}/*.log {
    weekly
    rotate 8
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
EOF
log "Installed logrotate: ${LOGROTATE_FILE}"

# ---------------------------------------------------------------------------
# 2) systemd journal → /data/logs/journal (bind-mount over /var/log/journal)
# ---------------------------------------------------------------------------
systemctl stop systemd-journald.socket systemd-journald-dev-log.socket systemd-journald 2>/dev/null || true

if [[ -d /var/log/journal ]] && ! mountpoint -q /var/log/journal; then
  log "Copying existing journal to ${JOURNAL_DIR}"
  rsync -a /var/log/journal/ "${JOURNAL_DIR}/" || true
  # Keep a small placeholder so bind mount target exists
  rm -rf /var/log/journal/*
fi

mkdir -p /var/log/journal
if ! mountpoint -q /var/log/journal; then
  mount --bind "$JOURNAL_DIR" /var/log/journal
fi

if ! grep -qE '[[:space:]]/var/log/journal[[:space:]]' "$FSTAB"; then
  echo "${JOURNAL_DIR} /var/log/journal none bind 0 0" >> "$FSTAB"
  log "Added bind mount to ${FSTAB}"
fi

mkdir -p "$(dirname "$JOURNALD_DROPIN")"
cat > "$JOURNALD_DROPIN" <<EOF
[Journal]
Storage=persistent
SystemMaxUse=2G
SystemKeepFree=5G
RuntimeMaxUse=100M
MaxRetentionSec=30day
Compress=yes
EOF
log "Wrote ${JOURNALD_DROPIN}"

systemctl start systemd-journald.socket systemd-journald 2>/dev/null || systemctl restart systemd-journald
systemctl restart systemd-journald

# ---------------------------------------------------------------------------
# 3) rsyslog (syslog/auth/kern) → /data/logs/syslog/ via symlinks
#    Keep /etc/rsyslog.d/50-default.conf paths (/var/log/...) so packages
#    stay happy; the files themselves live on the data drive.
# ---------------------------------------------------------------------------
systemctl stop rsyslog 2>/dev/null || true

move_or_link() {
  local name="$1"
  local src="/var/log/${name}"
  local dst="${SYSLOG_DIR}/${name}"
  if [[ -L "$src" ]]; then
    # Already a symlink — ensure it points at the data drive
    ln -sfn "$dst" "$src"
    touch "$dst"
    return
  fi
  if [[ -f "$src" ]]; then
    cat "$src" >> "$dst" 2>/dev/null || cp -a "$src" "$dst"
    rm -f "$src"
  fi
  touch "$dst"
  chmod 640 "$dst" 2>/dev/null || chmod 644 "$dst"
  chown syslog:adm "$dst" 2>/dev/null || true
  ln -sfn "$dst" "$src"
}

for f in syslog auth.log kern.log; do
  move_or_link "$f"
done
# Drop huge rotated leftovers still on the root volume
rm -f /var/log/syslog.[0-9]* /var/log/syslog.*.gz \
      /var/log/auth.log.[0-9]* /var/log/auth.log.*.gz \
      /var/log/kern.log.[0-9]* /var/log/kern.log.*.gz 2>/dev/null || true

# Remove obsolete drop-in from earlier revisions of this script (if any)
rm -f /etc/rsyslog.d/00-data-drive.conf 2>/dev/null || true

systemctl start rsyslog || systemctl restart rsyslog

# ---------------------------------------------------------------------------
# 4) logrotate for syslog tree on /data
# ---------------------------------------------------------------------------
cat > /etc/logrotate.d/data-drive-syslog <<EOF
${SYSLOG_DIR}/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 syslog adm
    sharedscripts
    postrotate
        /usr/lib/rsyslog/rsyslog-rotate 2>/dev/null || systemctl kill -s HUP rsyslog.service 2>/dev/null || true
    endscript
}
EOF
# Also rotate via the classic /var/log paths (symlinks → same files)
cat > /etc/logrotate.d/rsyslog-data-symlinks <<EOF
/var/log/syslog
/var/log/kern.log
/var/log/auth.log
{
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    sharedscripts
    postrotate
        /usr/lib/rsyslog/rsyslog-rotate 2>/dev/null || systemctl kill -s HUP rsyslog.service 2>/dev/null || true
    endscript
}
EOF

# ---------------------------------------------------------------------------
# 5) Home Assistant config → /data/homeassistant/config (bind-mount)
#    Symlinking only the .log file fails: HA unlinks and recreates it on root.
# ---------------------------------------------------------------------------
HA_MIGRATE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/migrate_homeassistant_to_data.sh"
if [[ -x "$HA_MIGRATE" ]] || [[ -f "$HA_MIGRATE" ]]; then
  bash "$HA_MIGRATE"
else
  log "WARN: migrate_homeassistant_to_data.sh not found — HA config left on root"
fi

# Keep a rotated copy path for cleanup/logrotate compatibility
mkdir -p "$HA_LOG_DIR"
cat > /etc/logrotate.d/homeassistant-data <<EOF
/data/homeassistant/config/home-assistant.log
${HA_LOG_DIR}/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
    su homeassistant homeassistant
}
EOF
log "Home Assistant → /data/homeassistant/config (bind → ${HA_CONFIG_DIR})"

# ---------------------------------------------------------------------------
# 6) Mosquitto logs → /data/logs/mosquitto/
# ---------------------------------------------------------------------------
if [[ -d /var/log/mosquitto ]] || command -v mosquitto >/dev/null 2>&1; then
  MOSQ_DST="${MOSQUITTO_LOG_DIR}/mosquitto.log"
  mkdir -p /var/log/mosquitto
  if [[ -f /var/log/mosquitto/mosquitto.log && ! -L /var/log/mosquitto/mosquitto.log ]]; then
    log "Moving Mosquitto log → ${MOSQ_DST}"
    systemctl stop mosquitto.service 2>/dev/null || true
    cat /var/log/mosquitto/mosquitto.log >> "$MOSQ_DST" 2>/dev/null || cp -a /var/log/mosquitto/mosquitto.log "$MOSQ_DST"
    rm -f /var/log/mosquitto/mosquitto.log
  fi
  touch "$MOSQ_DST"
  chown mosquitto:mosquitto "$MOSQ_DST" 2>/dev/null || true
  chmod 600 "$MOSQ_DST" 2>/dev/null || chmod 644 "$MOSQ_DST"
  ln -sfn "$MOSQ_DST" /var/log/mosquitto/mosquitto.log
  # Rotated gz still on root
  find /var/log/mosquitto -maxdepth 1 -type f \( -name '*.gz' -o -name 'mosquitto.log.[0-9]*' \) \
    -exec mv -f {} "$MOSQUITTO_LOG_DIR/" \; 2>/dev/null || true
  chown -R mosquitto:mosquitto "$MOSQUITTO_LOG_DIR" 2>/dev/null || true
  cat > /etc/logrotate.d/mosquitto-data <<EOF
${MOSQUITTO_LOG_DIR}/*.log {
    weekly
    rotate 8
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
    su mosquitto mosquitto
}
EOF
  systemctl start mosquitto.service 2>/dev/null || systemctl restart mosquitto.service 2>/dev/null || true
  log "Mosquitto logs → ${MOSQUITTO_LOG_DIR}"
fi

# ---------------------------------------------------------------------------
# 7) Camera snapshots → /data/camera-snapshots
# ---------------------------------------------------------------------------
OPT_SNAP="/opt/dell_server_management/data/camera-snapshots"
mkdir -p "$SNAPSHOT_DIR"
chmod 755 "$SNAPSHOT_DIR"
if [[ -d "$OPT_SNAP" && ! -L "$OPT_SNAP" ]]; then
  if [[ "$(find "$OPT_SNAP" -mindepth 1 -maxdepth 1 2>/dev/null | wc -l)" -gt 0 ]]; then
    rsync -a "$OPT_SNAP"/ "$SNAPSHOT_DIR"/ || true
  fi
  rm -rf "$OPT_SNAP"
fi
mkdir -p "$(dirname "$OPT_SNAP")"
ln -sfn "$SNAPSHOT_DIR" "$OPT_SNAP"
if [[ -f "$ENV_FILE" ]]; then
  if grep -q '^CAMERA_SNAPSHOT_DIR=' "$ENV_FILE"; then
    sed -i "s|^CAMERA_SNAPSHOT_DIR=.*|CAMERA_SNAPSHOT_DIR=${SNAPSHOT_DIR}|" "$ENV_FILE"
  else
    printf '\nCAMERA_SNAPSHOT_DIR=%s\n' "$SNAPSHOT_DIR" >> "$ENV_FILE"
  fi
  log "CAMERA_SNAPSHOT_DIR=${SNAPSHOT_DIR} in ${ENV_FILE}"
fi
if systemctl list-unit-files camera-ping-watchdog.service >/dev/null 2>&1; then
  systemctl try-restart camera-ping-watchdog.service 2>/dev/null || true
fi

# ---------------------------------------------------------------------------
# 8) Swap file on /data (frees ~3 GB on the 15 GB root SSD)
# ---------------------------------------------------------------------------
if [[ "$SETUP_DATA_SWAP" == "1" ]]; then
  ROOT_SWAP="/swap.img"
  if [[ -f "$ROOT_SWAP" ]] || grep -qE '^/swap\.img[[:space:]]' "$FSTAB"; then
    SWAP_SIZE_BYTES="$(stat -c%s "$ROOT_SWAP" 2>/dev/null || echo $((3 * 1024 * 1024 * 1024)))"
    if [[ ! -f "$DATA_SWAP" ]]; then
      log "Creating ${DATA_SWAP} ($((SWAP_SIZE_BYTES / 1024 / 1024)) MiB)"
      fallocate -l "$SWAP_SIZE_BYTES" "$DATA_SWAP" || dd if=/dev/zero of="$DATA_SWAP" bs=1M count=$((SWAP_SIZE_BYTES / 1024 / 1024)) status=none
      chmod 600 "$DATA_SWAP"
      mkswap "$DATA_SWAP"
    fi
    chmod 600 "$DATA_SWAP"
    if ! swapon --show=NAME --noheadings 2>/dev/null | grep -qx "$DATA_SWAP"; then
      swapon "$DATA_SWAP"
      log "Enabled swap ${DATA_SWAP}"
    fi
    if ! grep -qE "^${DATA_SWAP}[[:space:]]" "$FSTAB"; then
      echo "${DATA_SWAP} none swap sw 0 0" >> "$FSTAB"
    fi
    if swapon --show=NAME --noheadings 2>/dev/null | grep -qx "$ROOT_SWAP"; then
      log "Disabling root swap ${ROOT_SWAP}"
      swapoff "$ROOT_SWAP" || die "swapoff ${ROOT_SWAP} failed — free memory and re-run"
    fi
    sed -i '\#^/swap\.img[[:space:]]#d' "$FSTAB"
    if [[ -f "$ROOT_SWAP" ]]; then
      rm -f "$ROOT_SWAP"
      log "Removed ${ROOT_SWAP}"
    fi
  else
    log "No /swap.img on root — swap move skipped"
  fi
else
  log "SETUP_DATA_SWAP=0 — swap move skipped"
fi

log "Done."
log "  App log:     ${APP_LOG}"
log "  Syslog dir:  ${SYSLOG_DIR}"
log "  Journal:     ${JOURNAL_DIR} (bind → /var/log/journal)"
log "  HA logs:     ${HA_LOG_DIR}"
log "  Mosquitto:   ${MOSQUITTO_LOG_DIR}"
log "  Snapshots:   ${SNAPSHOT_DIR}"
log "  Swap:        $(swapon --show --noheadings 2>/dev/null | tr '\n' ' ' || echo none)"
df -h / /data | sed 's/^/[setup-data-logs] /'
