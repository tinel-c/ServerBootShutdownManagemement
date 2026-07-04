# Release Notes - v2.6.0

**Release Date**: January 17, 2026  
**Type**: Major Feature Release  
**Status**: ✅ Stable

---

## 🎉 What's New

### Dell T310 Proxmox API Integration

The biggest change in this release is **replacing unreliable IPMI with Proxmox API** for Dell T310 status monitoring.

**Benefits:**
- ✅ **No more IPMI timeouts** - Stable, consistent connections
- ✅ **No more "UNKNOWN" notifications** - Accurate status reporting
- ✅ **Faster response** - 5-second timeout vs 20+ second IPMI hangs
- ✅ **Better reliability** - Direct Proxmox node status checks

**Before:**
```
Error: Unable to establish IPMI v2 / RMCP+ session
Status: UNKNOWN (every 30-60 seconds)
```

**After:**
```
Dell T310 is ONLINE (via Proxmox API)
Status: Accurate and stable
```

### Management Scripts Suite

New CLI tools make system management much easier:

#### `status.sh` - Service Status Checker
```bash
./status.sh              # Quick status check
./status.sh -l           # With recent logs
./status.sh -l -n 50     # With 50 log lines
./status.sh -a           # Show everything
```

**Features:**
- Color-coded service status (🟢 Running, 🔴 Stopped)
- Shows if services are enabled on boot
- Optional log viewing
- System health overview

#### `manage.sh` - Service Management
```bash
sudo ./manage.sh start    # Start all services
sudo ./manage.sh stop     # Stop all services
sudo ./manage.sh restart  # Restart all services
sudo ./manage.sh enable   # Enable auto-start
sudo ./manage.sh logs     # View live logs
```

**Benefits:**
- Manage all services with one command
- No need to remember service names
- Clear success/error feedback

#### `update.sh` - Safe System Updates
```bash
git pull
sudo ./update.sh
```

**Features:**
- Automatically backs up configuration
- Updates scripts and dependencies
- Restores your `.env` and YAML configs
- Graceful service restarts
- No configuration loss!

### Environment Configuration Tools

#### `check_env.sh` - Configuration Validator
```bash
./check_env.sh
```

Validates all required environment variables and shows:
- ✅ Which variables are set
- ❌ Which variables are missing
- Masked passwords for security

#### `generate_env_template.sh` - Template Generator
```bash
./generate_env_template.sh
```

Creates a comprehensive `.env.example` with:
- All required variables
- Detailed comments
- Example values
- Configuration notes

---

## 🐛 Bug Fixes

### Fixed: Repeated "UNKNOWN" Status Notifications

**Problem:**
- Telegram receiving "UNKNOWN" status every 30-60 seconds
- IPMI connection timeouts
- State conflicts between monitoring systems

**Root Causes Identified:**
1. **Health monitor conflict**: Using 'up'/'down' states
2. **Status publisher**: Using 'online'/'offline' states
3. **IPMI unreliability**: Frequent connection failures
4. **State flip-flopping**: Conflicting updates

**Solutions Implemented:**
1. ✅ Removed conflicting health monitor logic
2. ✅ Replaced IPMI with Proxmox API for Dell T310
3. ✅ Added retry logic for remaining IPMI/iLO connections
4. ✅ Made MQTT status publisher single source of truth

**Result:** Stable status monitoring with notifications only on real state changes.

### Fixed: Environment Variable Placeholders Not Replaced

**Problem:**
```
Error: HTTPSConnectionPool(host='$%7bt310_proxmox_host%7d', port=8006)
```

**Root Cause:**
The `replace_env_vars()` function only replaced strings that were EXACTLY `${VARIABLE}`, not embedded patterns like `https://${HOST}:8006`.

**Solution:**
Implemented regex-based replacement to handle all `${VAR}` patterns within strings.

**Code Change:**
```python
# Before: Only matched exact strings
elif isinstance(obj, str) and obj.startswith('${') and obj.endswith('}'):

# After: Matches embedded patterns
elif isinstance(obj, str) and '${' in obj:
    return re.sub(r'\$\{([^}]+)\}', replacer, obj)
```

**Result:** All environment variables now properly replaced in configuration.

### Fixed: Configuration Loss on Reinstall

**Problem:**
Running `install.sh` would erase the `.env` file.

**Root Cause:**
Script backed up entire directory before checking for `.env` file.

**Solution:**
- Check for `.env` BEFORE backing up directory
- Create timestamped backups in `/tmp/`
- Restore configuration after installation
- Clear confirmation messages

**Result:** Configuration automatically preserved during reinstalls.

### Fixed: IPMI Connection Reliability

**Problem:**
Intermittent "Unable to establish IPMI v2 / RMCP+ session" errors.

**Solution:**
Added automatic retry logic (3 attempts with 1s delay) for IPMI commands.

**Result:** Transient IPMI failures handled gracefully for HP DL360p.

---

## 📚 Documentation

### New Documentation

1. **`CHANGELOG.md`** - Complete version history
2. **`DEVELOPMENT_WORKFLOW.md`** - Standardized development process
3. **`ENV_SETUP_GUIDE.md`** - Environment configuration guide
4. **`QUICK_REFERENCE.md`** - Command cheat sheet
5. **`UPDATE_GUIDE.md`** - Update instructions
6. **`RELEASE_NOTES_v2.6.0.md`** - This file

### Updated Documentation

- **`README.md`** - Updated with new features and scripts
- **`COMMIT_MESSAGE.md`** - Git commit guidelines

---

## 🔧 Technical Details

### Architecture Changes

**Dell T310 Status Flow (Before):**
```
IPMI → get_power_status() → timeout/error → "unknown" state
```

**Dell T310 Status Flow (After):**
```
Proxmox API → get_nodes() → check status → "online"/"offline" state
```

### Configuration Loading

**Improved Order:**
1. Load `.env` file
2. Load YAML files
3. Replace `${VAR}` placeholders with regex
4. Validate configuration
5. Report missing variables

### Service Management

**New Service Lifecycle:**
```bash
./manage.sh stop      # Graceful stop
./update.sh           # Update with config preservation
./manage.sh start     # Clean start
./status.sh -l        # Verify
```

---

## 📊 Statistics

### Commits in This Release
- **Total Commits**: 5
- **Files Changed**: 15
- **Lines Added**: 2,100+
- **Lines Removed**: 100+

### New Files Created
- 6 new scripts
- 5 new documentation files
- 1 new utility module

### Bug Fixes
- 4 major bugs fixed
- 0 known issues remaining

---

## 🚀 Upgrade Instructions

### For Existing Installations

```bash
# 1. Pull latest code
cd /path/to/ServerBootShutdownMangement
git pull

# 2. Verify environment configuration
./check_env.sh

# 3. Run update script (preserves config)
sudo ./update.sh

# 4. Verify everything works
./status.sh -l

# Should see: "Dell T310 is ONLINE (via Proxmox API)"
```

### Fresh Installation

```bash
# 1. Clone repository
git clone https://github.com/tinel-c/ServerBootShutdownManagemement.git
cd ServerBootShutdownManagemement

# 2. Run installer
chmod +x install.sh
sudo ./install.sh

# 3. Configure environment
./generate_env_template.sh
sudo cp config/.env.example /opt/dell_server_management/config/.env
sudo nano /opt/dell_server_management/config/.env

# 4. Validate and start
./check_env.sh
sudo ./manage.sh enable
sudo ./manage.sh start
./status.sh -l
```

---

## ⚠️ Breaking Changes

**None.** This release is fully backward compatible.

---

## 🎯 What's Next (v2.7.0)

Planned features for the next release:

- [ ] Web-based dashboard (alternative to Node-RED)
- [ ] Email notification support
- [ ] Advanced power scheduling
- [ ] VM-level monitoring integration
- [ ] Multi-server health dashboard
- [ ] Automated backup integration

---

## 🙏 Acknowledgments

This release focused on stability and usability based on real-world deployment experience.

Special thanks to the debug-driven development approach that identified and fixed all root causes with runtime evidence.

---

## 📝 Full Changelog

See [CHANGELOG.md](../../CHANGELOG.md) for complete version history.

---

## 🔗 Links

- **Repository**: https://github.com/tinel-c/ServerBootShutdownManagemement
- **Release Tag**: v2.6.0
- **Documentation**: See `docs/` folder
- **Quick Reference**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- **Development Workflow**: [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md)

---

## 💬 Feedback

Found a bug? Have a feature request? 

Open an issue on GitHub or check the troubleshooting guide in `docs/TROUBLESHOOTING.md`.

---

**Enjoy the stable, reliable server management! 🎉**
