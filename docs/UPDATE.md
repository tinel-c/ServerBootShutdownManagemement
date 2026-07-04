# Update Guide

This guide explains how to update the Server Management System while preserving your configuration.

## Quick Update (Recommended)

Use the dedicated update script that automatically preserves all configuration:

```bash
# Pull latest changes from git
cd /path/to/ServerBootShutdownMangement
git pull

# Run the update script
sudo ./update.sh
```

The `update.sh` script will:
- ✅ Stop all services gracefully
- ✅ Backup all configuration files (.env, mqtt_config.yaml, server_config.yaml)
- ✅ Update Python scripts and systemd services
- ✅ Update Python dependencies
- ✅ Restore your existing configuration
- ✅ Restart all services

**Your configuration is automatically preserved!**

---

## Full Reinstall

If you need to do a complete reinstall, the `install.sh` script also preserves your configuration:

```bash
cd /path/to/ServerBootShutdownMangement
sudo ./install.sh
```

The `install.sh` script will:
- Check for existing `.env` file **before** backing up directories
- Preserve it in `/tmp/dell_server_management_env.bak`
- Restore it after copying new files
- Print confirmation: "✓ Configuration successfully preserved from previous installation!"

---

## Manual Configuration Backup (Optional)

If you want to manually backup your configuration before updating:

```bash
# Backup configuration
mkdir -p ~/server_mgmt_backup_$(date +%Y%m%d)
sudo cp /opt/dell_server_management/config/.env ~/server_mgmt_backup_$(date +%Y%m%d)/
sudo cp /opt/dell_server_management/config/*.yaml ~/server_mgmt_backup_$(date +%Y%m%d)/

# After update, restore if needed
sudo cp ~/server_mgmt_backup_*/config/.env /opt/dell_server_management/config/
sudo chmod 600 /opt/dell_server_management/config/.env
```

---

## What Gets Preserved

### Always Preserved ✅
- `.env` file (credentials and environment variables)
- `mqtt_config.yaml` (MQTT broker configuration)
- `server_config.yaml` (server-specific settings)

### Updated 🔄
- Python scripts (`scripts/`)
- Device integrations (`device/victron-multiplus-ii/`, `device/huawei-inverter/`, …)
- Systemd service files (`systemd/`)
- Python dependencies (from `requirements.txt`)

---

## Troubleshooting

### Configuration Not Preserved?

Check the backup location:
```bash
ls -lah /tmp/dell_server_management_env.bak*
```

If update.sh was used, check:
```bash
ls -lah /tmp/server_management_config_backup_*
```

### Service Won't Start After Update?

Check if configuration is valid:
```bash
sudo cat /opt/dell_server_management/config/.env
sudo systemctl status status-publisher.service
sudo journalctl -u status-publisher.service -n 50
```

### Need to Revert?

The install script creates timestamped backups:
```bash
ls -lah /opt/dell_server_management.backup.*
```

To restore:
```bash
sudo systemctl stop mqtt-boot-listener.service mqtt-shutdown-listener.service status-publisher.service
sudo mv /opt/dell_server_management /opt/dell_server_management.failed_update
sudo mv /opt/dell_server_management.backup.YYYYMMDD_HHMMSS /opt/dell_server_management
sudo systemctl restart mqtt-boot-listener.service mqtt-shutdown-listener.service status-publisher.service
```

---

## Best Practices

1. **Always use `update.sh` for updates** - it's safer and faster than reinstalling
2. **Test after updating** - check service status and logs
3. **Keep your git repository clean** - don't commit your `.env` file
4. **Document custom changes** - if you modify config templates, keep notes

---

## Comparison: install.sh vs update.sh

| Feature | install.sh | update.sh |
|---------|-----------|----------|
| Preserves device .env (Victron/Huawei) | ✅ Yes | ✅ Yes |
| Preserves YAML configs | ❌ No | ✅ Yes |
| Stops services first | ❌ No | ✅ Yes |
| Updates dependencies | ✅ Yes | ✅ Yes |
| Faster | ❌ Full reinstall | ✅ Selective update |
| Use case | First install | Regular updates |

**Recommendation**: Use `update.sh` for all updates after initial installation.

---

## Update Checklist

Before updating:
- [ ] Pull latest changes: `git pull`
- [ ] Check current service status
- [ ] Note any custom modifications

During update:
- [ ] Run `sudo ./update.sh`
- [ ] Watch for any errors or warnings

After update:
- [ ] Verify services are running: `systemctl status status-publisher.service`
- [ ] **Victron** (if configured): `systemctl status victron-mqtt-publisher.service victron-solar-forecast-publisher.service`
- [ ] **Huawei** (if configured): `systemctl status huawei-mqtt-publisher.service`
- [ ] **Victron MQTT**: `mosquitto_sub -h localhost -t 'energy/victron/status' -C 1`
- [ ] **Huawei MQTT**: `mosquitto_sub -h localhost -t 'energy/huawei/status' -C 1`
- [ ] **Node-RED** (v3.11.6+): re-import flows `800`, `811`, `812`, update `50` and `90` — see [ENERGY_NODE_RED.md](ENERGY_NODE_RED.md)
- [ ] **Node-RED** (v3.11.8+): re-import flows `821`, `822`, update `50` and `90` for Huawei — see [ENERGY_NODE_RED.md](ENERGY_NODE_RED.md)
- [ ] Check logs: `journalctl -u status-publisher.service -n 20`
- [ ] Test functionality (boot/shutdown commands, status monitoring)
- [ ] Verify Telegram notifications work (`/help`, `/energy_status`, `/huawei_status`)

---

## Getting Help

If you encounter issues:
1. Check service logs: `sudo journalctl -u status-publisher.service -f`
2. Verify configuration: `sudo cat /opt/dell_server_management/config/.env`
3. Check backup files in `/tmp/` or `/opt/dell_server_management.backup.*`
4. Review `TROUBLESHOOTING.md` for common issues
