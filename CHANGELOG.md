# Changelog

All notable changes to the Server Management System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.6.0] - 2026-01-17

### 🎉 Major Features

#### Dell T310 Proxmox API Integration
- **Replaced unreliable IPMI with Proxmox API** for Dell T310 status monitoring
- Provides stable, consistent server status without IPMI connection timeouts
- Automatically detects Proxmox node status (online/offline)
- 5-second timeout for fast, responsive status checks

#### Management Scripts Suite
- **`status.sh`** - Interactive status checker with color-coded output
  - Shows all service states with visual indicators
  - Optional log viewing with customizable line count
  - System health overview
- **`manage.sh`** - One-command service management
  - Start/stop/restart all services at once
  - Enable/disable auto-start on boot
  - Live log viewing
- **`update.sh`** - Safe system updates with automatic config preservation
  - Backs up all configuration files
  - Updates scripts and dependencies
  - Restores configuration automatically
  - Graceful service restarts

#### Environment Configuration Tools
- **`check_env.sh`** - Validates environment variable configuration
  - Checks all required variables are set
  - Masks sensitive passwords in output
  - Color-coded validation results
- **`generate_env_template.sh`** - Creates comprehensive `.env` template
- **`config_loader.py`** - Centralized configuration loading with validation

### 🐛 Bug Fixes

#### Fixed: Repeated "UNKNOWN" Status Notifications
- **Root Cause**: Multiple conflicting systems updating server state
  - Health monitor using 'up'/'down' states
  - Status publisher using 'online'/'offline' states
  - IPMI timeouts causing state flip-flops
- **Solution**: 
  - Removed conflicting health monitor state updates from Node-RED
  - Made MQTT status publisher the single source of truth
  - Standardized all state values across the system

#### Fixed: IPMI Connection Reliability
- **Added automatic retry logic** (3 attempts with 1s delay)
- Handles transient "Unable to establish IPMI v2 / RMCP+ session" errors
- Continues to work for HP DL360p iLO connections

#### Fixed: Environment Variable Placeholders Not Replaced
- **Root Cause**: `replace_env_vars()` only matched exact `${VAR}` strings
- **Solution**: Implemented regex-based replacement for embedded placeholders
- Now correctly replaces `https://${HOST}:8006` → `https://192.168.2.9:8006`

#### Fixed: Configuration Loss on Reinstall
- **Root Cause**: `install.sh` backed up directory before preserving `.env`
- **Solution**: 
  - Check for `.env` file BEFORE directory backup
  - Create timestamped backups in `/tmp/`
  - Restore configuration after copying new files

### 📚 Documentation

#### New Guides
- **`ENV_SETUP_GUIDE.md`** - Comprehensive environment configuration guide
- **`QUICK_REFERENCE.md`** - Command cheat sheet for daily operations
- **`UPDATE_GUIDE.md`** - Detailed update instructions and best practices
- **`DEVELOPMENT_WORKFLOW.md`** - Contribution and development workflow
- **`CHANGELOG.md`** - This file

#### Updated Documentation
- **`README.md`** - Updated with new features and management scripts
- **`COMMIT_MESSAGE.md`** - Template for consistent commit messages

### 🔧 Technical Improvements

#### Code Quality
- Removed all debug instrumentation after verification
- Added comprehensive error handling in Proxmox API calls
- Improved logging with context-specific messages
- Standardized state values across all components

#### Configuration Management
- Environment variables now properly loaded before YAML processing
- Regex-based placeholder replacement supports complex patterns
- Validation ensures critical config is present
- Clear error messages for missing variables

#### Service Reliability
- Services restart gracefully during updates
- Configuration preserved across updates
- Proper systemd service definitions
- Health checks and monitoring improved

### 🔄 Modified Files

**Core Functionality:**
- `scripts/status/status_publisher.py` - Added Proxmox API support
- `scripts/utils/ipmi_wrapper.py` - Added retry logic
- `scripts/utils/config_loader.py` - NEW: Centralized config loading
- `nodered/flows/41-client-automation.json` - Fixed state conflicts
- `nodered/flows/50-telegram-interface.json` - Cleaned up notifications
- `install.sh` - Fixed configuration preservation

**New Scripts:**
- `status.sh` - Service status checker
- `manage.sh` - Service management tool
- `update.sh` - Safe update script
- `check_env.sh` - Environment validation
- `generate_env_template.sh` - Template generator

### ⚠️ Breaking Changes

None. All changes are backward compatible.

### 📦 Dependencies

No new dependencies added. Uses existing:
- `proxmoxer` - Already in requirements.txt
- `python-dotenv` - Already in requirements.txt
- `pyyaml` - Already in requirements.txt

### 🚀 Migration Guide

For existing installations:

```bash
# 1. Pull latest changes
cd /path/to/ServerBootShutdownMangement
git pull

# 2. Run update script (preserves configuration)
sudo ./update.sh

# 3. Verify environment variables
./check_env.sh

# 4. Restart services
sudo ./manage.sh restart

# 5. Verify everything works
./status.sh -l
```

### 🎯 What's Next (v2.7.0)

- [ ] Web dashboard for system monitoring
- [ ] Email notifications in addition to Telegram
- [ ] Advanced power scheduling
- [ ] VM-level monitoring integration
- [ ] Enhanced health check dashboard

---

## [2.5.1] - Previous Release

See `RELEASE_HISTORY.md` for older versions.

---

## Versioning Scheme

- **Major (X.0.0)**: Breaking changes or major feature overhauls
- **Minor (2.X.0)**: New features, non-breaking changes
- **Patch (2.5.X)**: Bug fixes, documentation updates

---

**Full Changelog**: https://github.com/tinel-c/ServerBootShutdownManagemement/compare/v2.5.1...v2.6.0
