# Troubleshooting Guide

Common issues and solutions for the Dell T310 Management System.

## Table of Contents

1. [MQTT Connection Issues](#mqtt-connection-issues)
2. [IPMI Problems](#ipmi-problems)
3. [Wake-on-LAN Issues](#wake-on-lan-issues)
4. [Service Issues](#service-issues)
5. [Boot Problems](#boot-problems)
6. [Shutdown Problems](#shutdown-problems)
7. [Logging and Debugging](#logging-and-debugging)

---

## MQTT Connection Issues

### Problem: Cannot connect to MQTT broker

**Symptoms:**
- Services fail to start
- Logs show "Failed to connect to MQTT broker"

**Solutions:**

1. **Verify MQTT broker is running:**
   ```bash
   sudo systemctl status mosquitto
   ```

2. **Check network connectivity:**
   ```bash
   ping <mqtt-broker-ip>
   telnet <mqtt-broker-ip> 1883
   ```

3. **Test MQTT broker manually:**
   ```bash
   mosquitto_sub -h <broker> -t test/topic -v
   ```

4. **Check firewall rules:**
   ```bash
   sudo ufw status
   sudo ufw allow 1883/tcp
   ```

5. **Verify credentials:**
   - Check `/opt/dell_t310_management/config/.env`
   - Ensure `MQTT_PASSWORD` is correct

6. **Check MQTT broker logs:**
   ```bash
   sudo journalctl -u mosquitto -f
   ```

---

### Problem: Authentication failed

**Symptoms:**
- "Connection refused - bad username or password"

**Solutions:**

1. **Verify password file exists:**
   ```bash
   ls -l /etc/mosquitto/passwd
   ```

2. **Reset password:**
   ```bash
   sudo mosquitto_passwd -b /etc/mosquitto/passwd dell_t310 <new-password>
   sudo systemctl restart mosquitto
   ```

3. **Update .env file:**
   ```bash
   sudo nano /opt/dell_t310_management/config/.env
   # Update MQTT_PASSWORD
   ```

4. **Restart services:**
   ```bash
   sudo systemctl restart mqtt-boot-listener.service
   sudo systemctl restart mqtt-shutdown-listener.service
   sudo systemctl restart status-publisher.service
   ```

---

## IPMI Problems

### Problem: IPMI commands failing

**Symptoms:**
- "ipmitool not found"
- "Connection timeout"
- "Authentication failed"

**Solutions:**

1. **Install ipmitool:**
   ```bash
   sudo apt install ipmitool
   ```

2. **Test IPMI connectivity:**
   ```bash
   ipmitool -I lanplus -H <ipmi-ip> -U <username> -P <password> chassis status
   ```

3. **Verify IPMI is enabled in BIOS:**
   - Reboot server
   - Enter BIOS (F2 or F10)
   - Navigate to: Integrated Devices → IPMI Settings
   - Ensure "IPMI over LAN" is Enabled

4. **Check IPMI IP address:**
   ```bash
   ping <ipmi-ip>
   ```

5. **Verify credentials:**
   - Check `/opt/dell_t310_management/config/.env`
   - Ensure `IPMI_HOST`, `IPMI_USERNAME`, `IPMI_PASSWORD` are correct

6. **Check IPMI user list:**
   ```bash
   ipmitool -I lanplus -H <ipmi-ip> -U <username> -P <password> user list
   ```

7. **Reset IPMI password (if needed):**
   ```bash
   ipmitool -I lanplus -H <ipmi-ip> -U <username> -P <old-password> user set password 2 <new-password>
   ```

---

### Problem: IPMI slow to respond

**Symptoms:**
- Commands take a long time
- Timeouts occur

**Solutions:**

1. **Check network latency:**
   ```bash
   ping -c 10 <ipmi-ip>
   ```

2. **Increase timeout in scripts:**
   - Edit `scripts/utils/ipmi_wrapper.py`
   - Increase `timeout` parameter in `_execute_command()`

3. **Verify IPMI interface is not overloaded:**
   - Reduce polling frequency in configuration
   - Check for other IPMI clients

---

## Wake-on-LAN Issues

### Problem: Wake-on-LAN not working

**Symptoms:**
- Server doesn't boot when WoL command sent
- No error messages

**Solutions:**

1. **Verify WoL is enabled in BIOS:**
   - Reboot server
   - Enter BIOS
   - Navigate to: Integrated Devices → Network Interface
   - Enable "Wake on LAN"

2. **Verify MAC address is correct:**
   ```bash
   # Check MAC address in configuration
   cat /opt/dell_t310_management/config/server_config.yaml | grep mac_address
   
   # Verify with actual MAC address (when server is on)
   ip link show
   ```

3. **Test WoL manually:**
   ```bash
   wakeonlan <mac-address>
   ```

4. **Check network configuration:**
   - Ensure server is on same subnet
   - Or configure router to forward WoL packets

5. **Verify network cable is connected:**
   - WoL requires physical network connection

6. **Try different WoL tools:**
   ```bash
   # Install etherwake
   sudo apt install etherwake
   sudo etherwake <mac-address>
   ```

---

## Service Issues

### Problem: Services won't start

**Symptoms:**
- `systemctl start` fails
- Services show "failed" status

**Solutions:**

1. **Check service status:**
   ```bash
   sudo systemctl status mqtt-boot-listener.service
   ```

2. **View detailed logs:**
   ```bash
   sudo journalctl -u mqtt-boot-listener.service -n 50
   ```

3. **Check Python dependencies:**
   ```bash
   cd /opt/dell_t310_management
   source venv/bin/activate
   pip list
   ```

4. **Reinstall dependencies:**
   ```bash
   cd /opt/dell_t310_management
   source venv/bin/activate
   pip install -r requirements.txt --force-reinstall
   ```

5. **Check file permissions:**
   ```bash
   ls -la /opt/dell_t310_management/scripts/
   chmod +x /opt/dell_t310_management/scripts/boot/*.py
   chmod +x /opt/dell_t310_management/scripts/shutdown/*.py
   chmod +x /opt/dell_t310_management/scripts/status/*.py
   ```

6. **Verify configuration files exist:**
   ```bash
   ls -la /opt/dell_t310_management/config/
   ```

---

### Problem: Services keep restarting

**Symptoms:**
- Services restart repeatedly
- Logs show connection errors

**Solutions:**

1. **Check what's causing the crash:**
   ```bash
   sudo journalctl -u mqtt-boot-listener.service -f
   ```

2. **Common causes:**
   - MQTT broker not running
   - Invalid credentials
   - Configuration file errors
   - Network issues

3. **Temporarily disable auto-restart for debugging:**
   ```bash
   sudo systemctl edit mqtt-boot-listener.service
   ```
   
   Add:
   ```ini
   [Service]
   Restart=no
   ```

4. **Run script manually for debugging:**
   ```bash
   cd /opt/dell_t310_management
   source venv/bin/activate
   python3 scripts/boot/mqtt_boot_listener.py
   ```

---

## Boot Problems

### Problem: Server won't boot via MQTT

**Symptoms:**
- Boot command sent but server doesn't start
- Response shows success but server remains off

**Solutions:**

1. **Check power status:**
   ```bash
   ipmitool -I lanplus -H <ipmi-ip> -U <username> -P <password> chassis power status
   ```

2. **Try manual boot:**
   ```bash
   # Via WoL
   wakeonlan <mac-address>
   
   # Via IPMI
   ipmitool -I lanplus -H <ipmi-ip> -U <username> -P <password> chassis power on
   ```

3. **Check boot method:**
   - WoL only works if server is completely off
   - IPMI works in most cases

4. **Verify server is plugged in:**
   - Check power cable
   - Check power supply

5. **Check BIOS settings:**
   - Ensure server is set to power on after power loss (if desired)

---

## Shutdown Problems

### Problem: Graceful shutdown fails

**Symptoms:**
- VMs don't shutdown
- Timeout errors
- Server remains on

**Solutions:**

1. **Check Proxmox API connectivity:**
   ```bash
   curl -k https://<proxmox-ip>:8006/api2/json/version
   ```

2. **Verify Proxmox credentials:**
   - Check `/opt/dell_t310_management/config/.env`
   - Test login to Proxmox web interface

3. **Check VM guest agents:**
   - VMs need qemu-guest-agent installed for graceful shutdown
   ```bash
   # On each VM
   sudo apt install qemu-guest-agent
   sudo systemctl enable qemu-guest-agent
   sudo systemctl start qemu-guest-agent
   ```

4. **Increase timeout:**
   - Edit `config/server_config.yaml`
   - Increase `shutdown.vm_shutdown_timeout`

5. **Use force shutdown as fallback:**
   ```bash
   mosquitto_pub -h <broker> -t "dell/t310/command/shutdown" -m '{
     "action": "shutdown",
     "type": "force",
     "timestamp": "2025-12-25T20:00:00+02:00",
     "request_id": "force-shutdown-001"
   }'
   ```

---

### Problem: Force shutdown doesn't work

**Symptoms:**
- Server remains on after force shutdown command

**Solutions:**

1. **Verify IPMI power off command:**
   ```bash
   ipmitool -I lanplus -H <ipmi-ip> -U <username> -P <password> chassis power off
   ```

2. **Check IPMI credentials:**
   - Ensure user has power control permissions

3. **Try power cycle:**
   ```bash
   ipmitool -I lanplus -H <ipmi-ip> -U <username> -P <password> chassis power cycle
   ```

4. **Last resort - physical power button:**
   - Press and hold power button for 5 seconds

---

## Logging and Debugging

### Enable Debug Logging

1. **Edit .env file:**
   ```bash
   sudo nano /opt/dell_t310_management/config/.env
   ```

2. **Set log level to DEBUG:**
   ```bash
   LOG_LEVEL=DEBUG
   ```

3. **Restart services:**
   ```bash
   sudo systemctl restart mqtt-boot-listener.service
   sudo systemctl restart mqtt-shutdown-listener.service
   sudo systemctl restart status-publisher.service
   ```

### View Logs

**Service logs:**
```bash
# Boot listener
sudo journalctl -u mqtt-boot-listener.service -f

# Shutdown listener
sudo journalctl -u mqtt-shutdown-listener.service -f

# Status publisher
sudo journalctl -u status-publisher.service -f

# All services
sudo journalctl -u mqtt-*.service -u status-publisher.service -f
```

**Application log file:**
```bash
tail -f /var/log/dell_t310_management.log
```

**MQTT broker logs:**
```bash
sudo journalctl -u mosquitto -f
```

### Test Individual Components

**Test MQTT client:**
```bash
cd /opt/dell_t310_management
source venv/bin/activate
python3 scripts/utils/mqtt_client.py
```

**Test IPMI wrapper:**
```bash
cd /opt/dell_t310_management
source venv/bin/activate
python3 scripts/utils/ipmi_wrapper.py
```

**Test WoL boot:**
```bash
cd /opt/dell_t310_management
source venv/bin/activate
python3 scripts/boot/wol_boot.py --mac <mac-address>
```

---

## Getting Help

If you're still experiencing issues:

1. **Check logs** with DEBUG level enabled
2. **Review configuration files** for typos
3. **Test components individually** to isolate the problem
4. **Consult documentation:**
   - [SETUP.md](SETUP.md)
   - [MQTT_PROTOCOL.md](MQTT_PROTOCOL.md)
   - [DEVELOPMENT_GUIDE.md](../DEVELOPMENT_GUIDE.md)

---

**Last Updated:** 2025-12-25
