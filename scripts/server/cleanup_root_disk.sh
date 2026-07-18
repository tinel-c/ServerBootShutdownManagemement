#!/bin/bash
#
# Keep the root filesystem (/) from filling up.
# Heavy logs live on /data (see setup_data_drive_logs.sh); this script
# cleans caches, vacuums journals, and truncates any oversized files
# still on the root volume.
#
# Usage:
#   sudo bash scripts/server/cleanup_root_disk.sh
#   sudo ROOT_DISK_MAX_PERCENT=80 bash scripts/server/cleanup_root_disk.sh
#
# Env:
#   ROOT_DISK_MAX_PERCENT   target max used % on / (default 85)
#   ROOT_DISK_EMERGENCY_PERCENT  hard truncate threshold (default 95)
#   CLEANUP_LOG             log file (default /data/logs/automation/root_disk_cleanup.log)
#
set -euo pipefail

MAX_PCT="${ROOT_DISK_MAX_PERCENT:-85}"
EMERGENCY_PCT="${ROOT_DISK_EMERGENCY_PERCENT:-95}"
DATA_LOG_ROOT="${DATA_LOG_ROOT:-/data/logs}"
CLEANUP_LOG="${CLEANUP_LOG:-${DATA_LOG_ROOT}/automation/root_disk_cleanup.log}"
JOURNAL_VACUUM_SIZE="${JOURNAL_VACUUM_SIZE:-200M}"
TMP_MAX_AGE_DAYS="${TMP_MAX_AGE_DAYS:-3}"

[[ "$(id -u)" -eq 0 ]] || { echo "Run as root (sudo)" >&2; exit 1; }

mkdir -p "$(dirname "$CLEANUP_LOG")" 2>/dev/null || CLEANUP_LOG="/var/tmp/root_disk_cleanup.log"

ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log() {
  local line="[$(ts)] $*"
  echo "$line"
  echo "$line" >> "$CLEANUP_LOG" 2>/dev/null || true
}

root_used_pct() {
  df -P / | awk 'NR==2 { gsub(/%/,"",$5); print $5 }'
}

root_avail_human() {
  df -h / | awk 'NR==2 { print $4 " free of " $2 }'
}

is_on_root() {
  # True if path resolves on the root filesystem (not /data bind).
  local path="$1"
  [[ -e "$path" || -L "$path" ]] || return 1
  local src
  src="$(findmnt -n -o SOURCE --target "$path" 2>/dev/null || true)"
  [[ "$src" == /dev/sda* || "$src" == "$(findmnt -n -o SOURCE /)" ]]
}

PCT="$(root_used_pct)"
log "Root disk usage: ${PCT}% ($(root_avail_human)); target ≤ ${MAX_PCT}%"

if [[ "$PCT" -lt "$MAX_PCT" ]]; then
  log "Under threshold — light maintenance only"
  LIGHT=1
else
  LIGHT=0
  log "At/over threshold — running full cleanup"
fi

# --- always: vacuum journal (lives on /data after setup, still cap size) ---
if command -v journalctl >/dev/null 2>&1; then
  journalctl --vacuum-size="$JOURNAL_VACUUM_SIZE" >/dev/null 2>&1 || true
  journalctl --vacuum-time=14d >/dev/null 2>&1 || true
  log "journalctl vacuumed (size=${JOURNAL_VACUUM_SIZE}, time=14d)"
fi

# --- apt / package caches ---
if [[ "$LIGHT" -eq 0 ]] || [[ "$PCT" -ge $((MAX_PCT - 5)) ]]; then
  apt-get clean >/dev/null 2>&1 || true
  rm -rf /var/cache/apt/archives/*.deb 2>/dev/null || true
  log "apt cache cleaned"
fi

# --- temp / caches on root ---
find /tmp -xdev -type f -mtime +"${TMP_MAX_AGE_DAYS}" -delete 2>/dev/null || true
find /var/tmp -xdev -type f -mtime +7 -delete 2>/dev/null || true
rm -rf /root/.cache/pip /home/*/.cache/pip 2>/dev/null || true
rm -rf /root/.npm /home/*/.npm/_cacache 2>/dev/null || true
log "tmp and user caches pruned"

# --- oversized files still on root /var/log (not under /data) ---
truncate_if_huge() {
  local f="$1"
  local max_bytes="${2:-104857600}" # 100 MiB
  [[ -f "$f" && ! -L "$f" ]] || return 0
  is_on_root "$f" || return 0
  local sz
  sz="$(stat -c%s "$f" 2>/dev/null || echo 0)"
  if [[ "$sz" -gt "$max_bytes" ]]; then
    : > "$f"
    log "Truncated oversized root log: $f (was ${sz} bytes)"
  fi
}

if [[ "$LIGHT" -eq 0 ]]; then
  # Rotated syslog leftovers on root
  find /var/log -xdev -type f \( -name '*.gz' -o -name '*.[0-9]' -o -name '*.old' \) \
    -mtime +7 -delete 2>/dev/null || true
  for f in /var/log/syslog /var/log/kern.log /var/log/auth.log \
           /var/log/dell_server_management.log; do
    truncate_if_huge "$f" 52428800
  done
  # Any single file on /var/log > 200M on root
  while IFS= read -r -d '' f; do
    truncate_if_huge "$f" 209715200
  done < <(find /var/log -xdev -type f -size +200M -print0 2>/dev/null || true)
fi

# --- emergency: root still critical ---
PCT="$(root_used_pct)"
if [[ "$PCT" -ge "$EMERGENCY_PCT" ]]; then
  log "EMERGENCY ${PCT}% — aggressive truncate of largest root logs"
  journalctl --vacuum-size=50M >/dev/null 2>&1 || true
  while IFS= read -r f; do
    [[ -n "$f" ]] || continue
    is_on_root "$f" || continue
    [[ -L "$f" ]] && continue
    : > "$f"
    log "Emergency truncate: $f"
  done < <(find /var/log -xdev -type f -size +20M 2>/dev/null | head -20)
  apt-get clean >/dev/null 2>&1 || true
  PCT="$(root_used_pct)"
fi

# --- optional: prune old files on /data logs (keep disk tidy, not root) ---
if mountpoint -q /data 2>/dev/null; then
  find "${DATA_LOG_ROOT}/syslog" -type f -name '*.gz' -mtime +30 -delete 2>/dev/null || true
  find "${DATA_LOG_ROOT}/automation" -type f -name '*.gz' -mtime +60 -delete 2>/dev/null || true
fi

PCT="$(root_used_pct)"
log "Finished. Root disk usage: ${PCT}% ($(root_avail_human))"

if [[ "$PCT" -ge 100 ]]; then
  log "FAIL: root still at ${PCT}%"
  exit 2
fi
if [[ "$PCT" -gt "$MAX_PCT" ]]; then
  log "WARN: still above target ${MAX_PCT}% (now ${PCT}%)"
  exit 1
fi
exit 0
