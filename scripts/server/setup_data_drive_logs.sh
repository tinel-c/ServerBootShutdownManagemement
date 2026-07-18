#!/bin/bash
#
# Move automation / system logs from the root SSD (/) onto the data HDD (/data).
# Safe to re-run (idempotent). Requires root and a mounted /data volume.
#
# Usage:
#   sudo bash scripts/server/setup_data_drive_logs.sh
#
set -euo pipefail

DATA_ROOT="${DATA_LOG_ROOT:-/data/logs}"
AUTOMATION_LOG_DIR="${DATA_ROOT}/automation"
SYSLOG_DIR="${DATA_ROOT}/syslog"
JOURNAL_DIR="${DATA_ROOT}/journal"
LOGROTATE_FILE="/etc/logrotate.d/dell_server_management"
JOURNALD_DROPIN="/etc/systemd/journald.conf.d/95-data-drive.conf"
FSTAB="/etc/fstab"
ENV_FILE="${ENV_FILE:-/opt/dell_server_management/config/.env}"
APP_LOG_NAME="dell_server_management.log"

log() { echo "[setup-data-logs] $*"; }
die() { echo "[setup-data-logs] ERROR: $*" >&2; exit 1; }

[[ "$(id -u)" -eq 0 ]] || die "Run as root (sudo)"

mountpoint -q /data || die "/data is not mounted — attach/mount the second disk first"
[[ -d /data ]] || die "/data missing"

mkdir -p "$AUTOMATION_LOG_DIR" "$SYSLOG_DIR" "$JOURNAL_DIR"
chmod 755 "$DATA_ROOT" "$AUTOMATION_LOG_DIR" "$SYSLOG_DIR"
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

log "Done."
log "  App log:     ${APP_LOG}"
log "  Syslog dir:  ${SYSLOG_DIR}"
log "  Journal:     ${JOURNAL_DIR} (bind → /var/log/journal)"
df -h / /data | sed 's/^/[setup-data-logs] /'
