#!/bin/bash
# Move Home Assistant config onto /data via bind mount (logs/DB stay off root SSD).
set -euo pipefail
[[ "$(id -u)" -eq 0 ]] || { echo "Run as root" >&2; exit 1; }
mountpoint -q /data || { echo "/data not mounted" >&2; exit 1; }

HA_SRC=/home/homeassistant/.homeassistant
HA_DST=/data/homeassistant/config
STAMP=$(date +%Y%m%d%H%M%S)

systemctl stop homeassistant.service || true
mkdir -p "$HA_DST"

if [[ -d "$HA_SRC" ]] && ! mountpoint -q "$HA_SRC"; then
  rsync -a "$HA_SRC"/ "$HA_DST"/
fi
if [[ -f /data/logs/homeassistant/home-assistant.log ]]; then
  cat /data/logs/homeassistant/home-assistant.log >> "$HA_DST/home-assistant.log" 2>/dev/null || true
fi
chown -R homeassistant:homeassistant /data/homeassistant

if [[ -d "$HA_SRC" ]] && ! mountpoint -q "$HA_SRC" && [[ ! -L "$HA_SRC" ]]; then
  mv "$HA_SRC" "${HA_SRC}.root-bak.${STAMP}"
fi
mkdir -p "$HA_SRC"
if ! mountpoint -q "$HA_SRC"; then
  mount --bind "$HA_DST" "$HA_SRC"
fi
if ! grep -qE '[[:space:]]/home/homeassistant/\.homeassistant[[:space:]]' /etc/fstab; then
  echo "$HA_DST $HA_SRC none bind 0 0" >> /etc/fstab
fi

systemctl start homeassistant.service || true
echo "HA config bind-mounted: $HA_DST -> $HA_SRC"
df -h / /data
findmnt -n -o SOURCE,TARGET "$HA_SRC"
ls -lah "$HA_SRC/home-assistant.log"
