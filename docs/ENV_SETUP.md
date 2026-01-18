# Environment Variable Setup Guide

This guide explains how to properly configure environment variables for the Server Management System.

## 🚨 The Problem

If you see errors like:
```
Error getting Proxmox status for Dell T310: HTTPSConnectionPool(host='$%7bt310_proxmox_host%7d', port=8006)
```

This means environment variables are not properly configured in your `.env` file.

---

## ✅ Quick Fix (On Remote Server)

```bash
# 1. Navigate to repository
cd /opt/dell_server_management

# 2. Generate .env template
./generate_env_template.sh

# 3. Copy template to .env
cp config/.env.example config/.env

# 4. Edit with your actual values
sudo nano config/.env

# 5. Set secure permissions
sudo chmod 600 config/.env

# 6. Check configuration
./check_env.sh

# 7. Restart services
sudo ./manage.sh restart

# 8. Verify it works
./status.sh -l
```

---

## 📋 Required Environment Variables

### MQTT Broker
```bash
MQTT_BROKER_HOST=localhost          # or your MQTT broker IP
MQTT_BROKER_PORT=1883
MQTT_USERNAME=your_mqtt_user
MQTT_PASSWORD=your_mqtt_password
```

### Dell T310 (Primary focus)
```bash
# Proxmox API (REQUIRED - used for status monitoring)
T310_PROXMOX_HOST=192.168.1.10     # IP of your Dell T310 Proxmox
T310_PROXMOX_USERNAME=root@pam      # Proxmox username
T310_PROXMOX_PASSWORD=your_proxmox_password

# Network
T310_MAC_ADDRESS=00:11:22:33:44:55 # For Wake-on-LAN

# Optional: IPMI (kept for backward compatibility)
T310_IPMI_HOST=192.168.1.10
T310_IPMI_USERNAME=admin
T310_IPMI_PASSWORD=ipmi_password

# Optional: Health checks
T310_HEALTHCHECKS=check1,check2
```

### HP DL360p (If you have one)
```bash
DL360P_ILO_HOST=192.168.1.20
DL360P_ILO_USERNAME=Administrator
DL360P_ILO_PASSWORD=ilo_password
DL360P_PROXMOX_HOST=192.168.1.20
DL360P_PROXMOX_USERNAME=root@pam
DL360P_PROXMOX_PASSWORD=proxmox_password
DL360P_MAC_ADDRESS=AA:BB:CC:DD:EE:FF
```

---

## 🔧 Helper Scripts

### 1. Generate Template
```bash
./generate_env_template.sh
```
Creates `config/.env.example` with all required variables.

### 2. Check Configuration
```bash
./check_env.sh
```
Validates your `.env` file and shows which variables are missing.

**Example output:**
```
✓ Found: config/.env

Checking required variables:

  ✓ MQTT_BROKER_HOST = localhost
  ✓ MQTT_BROKER_PORT = 1883
  ✓ MQTT_USERNAME = mqtt_user
  ✓ MQTT_PASSWORD = ****
  ✓ T310_PROXMOX_HOST = 192.168.1.10
  ✓ T310_PROXMOX_USERNAME = root@pam
  ✓ T310_PROXMOX_PASSWORD = ****
  ✓ T310_MAC_ADDRESS = 00:11:22:33:44:55

✅ All required variables are set!
```

---

## 🔍 Troubleshooting

### Problem: "Environment variable X not set"

**Solution:**
```bash
# Check what's missing
./check_env.sh

# Edit .env file
sudo nano /opt/dell_server_management/config/.env

# Add the missing variable
# Example:
T310_PROXMOX_HOST=192.168.1.10

# Save and restart
sudo ./manage.sh restart
```

### Problem: "HTTPSConnectionPool(host='$%7b...%7d'..."

This means the placeholder `${VARIABLE}` wasn't replaced.

**Solution:**
```bash
# 1. Check .env file exists
ls -la /opt/dell_server_management/config/.env

# 2. Check .env has correct permissions
sudo chmod 600 /opt/dell_server_management/config/.env

# 3. Verify variables are set
./check_env.sh

# 4. Check for typos in variable names
cat /opt/dell_server_management/config/.env | grep T310_PROXMOX

# Should show:
# T310_PROXMOX_HOST=192.168.1.10  (NOT t310_proxmox_host)
```

### Problem: Still not working after setting variables

**Debug steps:**
```bash
# 1. Check service is loading .env file
sudo systemctl status status-publisher.service

# 2. Check for warnings in logs
sudo journalctl -u status-publisher.service -n 100 | grep -i "warning\|critical"

# 3. Test configuration loading
cd /opt/dell_server_management
source venv/bin/activate
python3 -c "
from scripts.utils.config_loader import get_config
config = get_config()
print('Proxmox Host:', config['servers'][0]['proxmox']['api_url'])
"

# Should print the actual URL, not ${T310_PROXMOX_HOST}
```

---

## 📝 Example .env File

Here's a complete working example:

```bash
# MQTT
MQTT_BROKER_HOST=192.168.1.5
MQTT_BROKER_PORT=1883
MQTT_USERNAME=automation
MQTT_PASSWORD=secure_mqtt_pass_123

# Dell T310
T310_PROXMOX_HOST=192.168.1.10
T310_PROXMOX_USERNAME=root@pam
T310_PROXMOX_PASSWORD=MyProxmoxPass123!
T310_MAC_ADDRESS=00:1A:2B:3C:4D:5E
T310_IPMI_HOST=192.168.1.10
T310_IPMI_USERNAME=admin
T310_IPMI_PASSWORD=ipmi_pass
T310_HEALTHCHECKS=t310-health,t310-backup

# HP DL360p
DL360P_ILO_HOST=192.168.1.20
DL360P_ILO_USERNAME=Administrator  
DL360P_ILO_PASSWORD=MyIloPass456!
DL360P_PROXMOX_HOST=192.168.1.20
DL360P_PROXMOX_USERNAME=root@pam
DL360P_PROXMOX_PASSWORD=MyProxmoxPass789!
DL360P_MAC_ADDRESS=AA:BB:CC:DD:EE:FF
DL360P_HEALTHCHECKS=dl360p-health

# Optional
HEALTHCHECKS_API_KEY=hc_abc123def456
TELEGRAM_BOT_TOKEN=123456:ABC-DEF
TELEGRAM_ALLOWED_USERS=123456789
LOG_LEVEL=INFO
```

---

## 🔐 Security Best Practices

1. **Never commit .env to git**
   ```bash
   # .gitignore already excludes .env files
   git status  # Should NOT show config/.env
   ```

2. **Set secure permissions**
   ```bash
   sudo chmod 600 /opt/dell_server_management/config/.env
   sudo chown root:root /opt/dell_server_management/config/.env
   ```

3. **Use strong passwords**
   - Proxmox: Use complex password
   - MQTT: Use unique password
   - Don't reuse passwords across services

4. **Backup your .env file** (securely)
   ```bash
   # Backup to encrypted location
   sudo cp /opt/dell_server_management/config/.env ~/server-mgmt-env-backup.txt
   # Or use a password manager
   ```

---

## 🚀 Quick Setup Workflow

```bash
# On your remote server:

# 1. Pull latest code
cd /path/to/ServerBootShutdownMangement
git pull

# 2. Generate template
./generate_env_template.sh

# 3. Create .env from template
sudo cp config/.env.example /opt/dell_server_management/config/.env

# 4. Edit with your values
sudo nano /opt/dell_server_management/config/.env

# 5. Check configuration
./check_env.sh

# 6. If all good, update system
sudo ./update.sh

# 7. Verify it works
./status.sh -l

# Should see: "Dell T310 is ONLINE (via Proxmox API)"
```

---

## ✅ Verification Checklist

After setup, verify:

- [ ] `.env` file exists at `/opt/dell_server_management/config/.env`
- [ ] `./check_env.sh` shows all variables set ✅
- [ ] Services start without errors: `./status.sh`
- [ ] Logs show Proxmox API connections: `./status.sh -l | grep Proxmox`
- [ ] No placeholder errors in logs: `sudo journalctl -u status-publisher.service | grep -i "\$"`
- [ ] Telegram notifications work (if configured)

---

## 📚 Related Documentation

- `QUICK_REFERENCE.md` - Command reference
- `UPDATE_GUIDE.md` - How to update the system
- `TROUBLESHOOTING.md` - Common issues
- `config/.env.example` - Full template with comments

---

**Need help?** Run `./check_env.sh` to diagnose configuration issues!
