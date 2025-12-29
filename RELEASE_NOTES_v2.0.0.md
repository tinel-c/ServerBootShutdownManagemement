# Release Notes - Version 2.0.0

**Release Date:** December 29, 2025  
**Release Type:** Major Update - Node-RED Dashboard Overhaul

---

## 🎉 Overview

Version 2.0.0 represents a **major architectural improvement** to the Node-RED dashboard component of the Server Boot/Shutdown Management system. This release introduces a modular flow architecture, comprehensive health monitoring, and extensive documentation.

## ✨ What's New

### 1. Modular Flow Architecture

The Node-RED dashboard has been completely refactored from a single monolithic `flows.json` file into **8 independent, feature-based modules**:

#### Module Structure
```
nodered/flows/
├── 00-base-config.json       # Core infrastructure (MUST import first)
├── 10-dell-controls.json     # Dell T310 control buttons
├── 11-dell-status.json       # Dell T310 status display
├── 12-dell-health.json       # Dell T310 health monitoring
├── 20-hp-controls.json       # HP DL360p control buttons
├── 21-hp-status.json         # HP DL360p status display
├── 22-hp-health.json         # HP DL360p health monitoring
└── 90-log-console.json       # System log console
```

#### Benefits
- ✅ **Easier Maintenance** - Update individual features without affecting others
- ✅ **Independent Development** - Multiple developers can work on different servers simultaneously
- ✅ **Simplified Testing** - Test features in isolation before integration
- ✅ **Better Version Control** - Clear, feature-specific commits and change tracking
- ✅ **Reusable Components** - Copy and adapt modules for new servers
- ✅ **Scalability** - Reserved slots for 4 additional servers (30-49)

### 2. Comprehensive Health Dashboard

The health monitoring interface has been **completely redesigned** with enterprise-grade features:

#### Visual Design
- 🎨 **Modern UI** - Gradient backgrounds, glass-morphism effects, smooth transitions
- 🎯 **Color Coding** - Green (up), red (down), orange (warning) status indicators
- 💎 **Card Layout** - Individual cards for each health check with full data visualization
- ⚡ **Glowing Effects** - Status pills with shadow effects for better visibility

#### Data Display (16+ Data Points)
Each health check card now displays:

**Header Section:**
- Status icon with glow effect (✅/❌/⚠️)
- Check name and slug
- Status pill (UP/DOWN/WARNING)
- Tags with pill-style badges

**Statistics Grid (2x2):**
- Total pings (formatted with thousands separator)
- Grace period (seconds)
- Timeout value (seconds)
- Manual resume requirement (AUTO/REQUIRED)

**Timing Information:**
- Last ping timestamp (formatted, e.g., "Dec 29, 10:50:01")
- Next ping timestamp (formatted)
- **Live countdown timer** to next ping (updates every second!)
  - Shows hours, minutes, seconds (e.g., "1h 23m" or "45s")
  - Displays "Overdue!" if ping is late

**Optional Fields:**
- Communication methods (📡 HTTP, Email, etc.)
- Email subject for alerts (📧)
- Started status flag (▶️)

**External Links:**
- Clickable badge URL link (🔗)
- Opens in new tab for quick access

#### Empty State
- Beautiful warning display when no health checks are available
- Clear messaging for troubleshooting

#### Real-Time Updates
- **1-second refresh interval** for countdown timers and time deltas
- **Reactive Vue.js** components for smooth, efficient updates
- **Auto-updating** relative time displays (e.g., "2s ago", "5m ago")

### 3. Documentation Suite

Added **2,000+ lines** of comprehensive documentation:

#### NODE_RED_DEVELOPMENT.md (800+ lines)
Complete development reference covering:
- Modular design philosophy and architecture
- File structure and naming conventions
- Step-by-step development workflow
- Feature module reference with customization points
- Instructions for adding new servers
- Best practices and coding standards
- Troubleshooting guide
- Advanced topics (themes, authentication, HTTPS, performance)
- Backup and restore procedures
- Migration guide from v1.x

#### flows/README.md (350+ lines)
Quick reference guide with:
- Import order and instructions
- Detailed file descriptions
- Dependencies for each module
- MQTT topic patterns and payload examples
- Troubleshooting common import/configuration issues
- Testing procedures

#### HEALTH_DASHBOARD_GUIDE.md (400+ lines)
Visual guide covering:
- Dashboard layout explanation with ASCII diagrams
- Complete data flow documentation
- Color coding reference
- MQTT payload structure and examples
- Customization options (colors, heights, statistics)
- Performance notes
- Browser compatibility
- Troubleshooting visual/display issues
- Integration with Healthchecks.io

### 4. Improved Scalability

The new architecture makes it easy to add more servers:

**Reserved Numbering Slots:**
- `00-09`: Core infrastructure
- `10-19`: Dell T310 features
- `20-29`: HP DL360p features
- `30-39`: **Reserved for future server 1**
- `40-49`: **Reserved for future server 2**
- `50-59`: **Reserved for future server 3**
- `60-69`: **Reserved for future server 4**
- `90-99`: Shared utilities

**Adding a New Server:**
1. Update `00-base-config.json` with new UI groups
2. Copy existing modules (e.g., 10-12 → 30-32)
3. Update IDs, names, topics, and server-specific settings
4. Import and deploy

See documentation for complete step-by-step guide.

---

## 🔄 Changes & Improvements

### Modified Files

#### Core Node-RED Files
- **`nodered/flows.json`** → Deprecated (use modular flows instead)
- Added **8 new modular flow files** in `nodered/flows/` directory
- Updated `nodered/docker-compose.yml` - No changes needed (fully compatible)
- Updated `nodered/Dockerfile` - No changes needed (Dashboard 2.0 already installed)

#### Documentation Updates
- **`README.md`** - Major update with:
  - Expanded Node-RED Dashboard section (v2.0 features)
  - Modular architecture explanation
  - Health monitoring details
  - Migration instructions
  - Updated project structure
  - Added changelog section
  - Version bumped to 2.0.0
  
- **New documentation files:**
  - `nodered/NODE_RED_DEVELOPMENT.md`
  - `nodered/flows/README.md`
  - `nodered/HEALTH_DASHBOARD_GUIDE.md`
  - `RELEASE_NOTES_v2.0.0.md` (this file)

### Unchanged Components

The following components remain **fully compatible** and unchanged:
- ✅ Python backend scripts (boot, shutdown, status)
- ✅ MQTT protocol and topics
- ✅ Systemd services
- ✅ Configuration files (`.env`, `mqtt_config.yaml`, `server_config.yaml`)
- ✅ Installation/uninstallation scripts
- ✅ IPMI/iLO integrations
- ✅ Wake-on-LAN functionality
- ✅ Proxmox shutdown logic

**This is purely a frontend/dashboard update** - no backend changes required!

---

## 📦 Installation

### New Installations

Follow the standard installation procedure, then:

1. Start Node-RED:
   ```bash
   cd nodered
   docker-compose up -d
   ```

2. Access Node-RED editor: http://localhost:1880

3. Import modular flows in order:
   - Menu → Import → Select file
   - Import: `flows/00-base-config.json` (**MUST BE FIRST**)
   - Import: `flows/10-dell-controls.json`
   - Import: `flows/11-dell-status.json`
   - Import: `flows/12-dell-health.json`
   - Import: `flows/20-hp-controls.json`
   - Import: `flows/21-hp-status.json`
   - Import: `flows/22-hp-health.json`
   - Import: `flows/90-log-console.json`

4. Click **Deploy**

5. Access dashboard: http://localhost:1880/dashboard/home

### Upgrading from v1.x

If you're currently using v1.3.0 or earlier:

#### Option 1: Clean Import (Recommended)

1. **Backup your current flows:**
   - Open Node-RED editor
   - Menu → Export → All Flows
   - Save to a backup file

2. **Clear existing flows:**
   - Delete all tabs/flows in Node-RED
   - Or: Menu → Configuration nodes → Delete all

3. **Import new modular flows:**
   - Follow "New Installations" steps above

4. **Verify functionality:**
   - Test all buttons
   - Check status displays update
   - Verify health monitoring works
   - Confirm logs display correctly

5. **Archive old flows:**
   ```bash
   cd nodered
   mv flows.json flows.json.v1-backup
   ```

#### Option 2: Side-by-Side Testing

1. **Keep existing flows running**

2. **Create new tab in Node-RED** for testing

3. **Import modular flows** to the new tab

4. **Test thoroughly** before switching

5. **Delete old flows** once confident

### Health Monitoring Setup

If using Healthchecks.io or similar service:

1. Ensure your Python backend publishes health data to MQTT:
   ```python
   topic = "dell/t310/health"  # or hp/dl360p/health
   payload = {
       "timestamp": "2025-12-29T10:51:43Z",
       "server": "Dell T310",
       "checks": [
           {
               "name": "nextcloud",
               "slug": "nextcloud",
               "status": "up",
               "n_pings": 255949,
               "grace": 300,
               "timeout": 120,
               "last_ping": "2025-12-29T10:50:01+00:00",
               "next_ping": "2025-12-29T10:52:01+00:00",
               "badge_url": "https://healthchecks.io/badge/...",
               # ... more fields optional
           }
       ]
   }
   ```

2. The dashboard will automatically display all data

---

## ⚠️ Breaking Changes

### 1. Flow File Structure

**Before (v1.x):**
```
nodered/
└── flows.json  (single monolithic file)
```

**After (v2.0):**
```
nodered/
├── flows.json.legacy  (deprecated)
└── flows/
    ├── 00-base-config.json
    ├── 10-dell-controls.json
    ├── ...
    └── 90-log-console.json
```

**Impact:** You must import multiple files instead of one.

**Migration:** Follow upgrade instructions above.

### 2. Health Payload Structure

**Before (v1.x):**
Simple health check display required minimal data:
```json
{
  "checks": [
    {"name": "service", "status": "up"}
  ]
}
```

**After (v2.0):**
Comprehensive display expects full Healthchecks.io format:
```json
{
  "timestamp": "ISO-8601",
  "server": "Server Name",
  "checks": [
    {
      "name": "service",
      "status": "up",
      "n_pings": 12345,
      "grace": 300,
      "timeout": 120,
      "last_ping": "ISO-8601",
      "next_ping": "ISO-8601",
      "badge_url": "https://...",
      "unique_key": "...",
      # ... other fields optional
    }
  ]
}
```

**Impact:** If using custom health monitoring, update payload structure.

**Backward Compatibility:** The dashboard gracefully handles missing optional fields - only `name` and `status` are required. Additional fields enhance the display.

### 3. Import Order Requirement

**Before (v1.x):**
Single file, no order considerations.

**After (v2.0):**
Must import `00-base-config.json` **FIRST**, others can follow in any order.

**Impact:** Importing modules out of order causes "Node configuration error".

**Solution:** Always import base config first.

---

## 🐛 Bug Fixes

- **Fixed:** Dell T310 status display was missing MQTT input node (now in `11-dell-status.json`)
- **Fixed:** Health groups had insufficient height allocation (increased from 1 to 8 units)
- **Improved:** Error handling for missing health check data
- **Improved:** Empty state display when no checks available

---

## 🚀 Performance Improvements

- **Efficient Updates:** Vue.js reactive components only re-render changed data
- **Optimized Timers:** Single 1-second interval per dashboard (not per check)
- **Lightweight Design:** Pure CSS styling, no external JavaScript dependencies
- **Smaller Files:** Modular files are easier to parse and load than monolithic file
- **Reduced Complexity:** Each module focuses on single responsibility

---

## 📝 Documentation

All documentation is included in the repository:

### For Users
- **README.md** - Updated main documentation with v2.0 features
- **nodered/flows/README.md** - Quick import guide and troubleshooting

### For Developers
- **nodered/NODE_RED_DEVELOPMENT.md** - Complete development reference
- **nodered/HEALTH_DASHBOARD_GUIDE.md** - Visual design and customization guide
- **DEVELOPMENT_GUIDE.md** - Backend development (unchanged)

### For Admins
- **docs/SETUP.md** - System setup instructions
- **docs/MQTT_PROTOCOL.md** - MQTT message specifications
- **docs/TROUBLESHOOTING.md** - Common issues and solutions

---

## 🔮 Future Enhancements

Potential improvements for future releases:

### v2.1.0 (Planned)
- Additional server templates (Synology NAS, TrueNAS, etc.)
- Advanced alerting system
- Historical data charts
- Mobile-responsive improvements

### v2.2.0 (Planned)
- Authentication and user roles
- Multi-dashboard support
- Custom themes
- Backup/restore automation

### v3.0.0 (Concept)
- Web-based configuration editor
- Plugin system for custom integrations
- REST API for external control
- Kubernetes deployment support

---

## 🆘 Support & Troubleshooting

### Common Issues

#### 1. "Node configuration error" on Import

**Problem:** Missing dependencies.

**Solution:** Import `00-base-config.json` first, then other modules.

#### 2. Health Cards Not Displaying

**Problem:** Health data not reaching dashboard.

**Solution:**
- Check MQTT broker is running
- Verify topic names match (`dell/t310/health`, `hp/dl360p/health`)
- Use MQTT Explorer to monitor traffic
- Add debug nodes to trace messages

#### 3. Countdown Timer Not Updating

**Problem:** JavaScript timer not running.

**Solution:**
- Check browser console for errors
- Verify Dashboard 2.0 is installed: `npm list @flowfuse/node-red-dashboard`
- Clear browser cache
- Ensure timestamps are valid ISO-8601 format

#### 4. Old and New Flows Conflict

**Problem:** Both v1.x and v2.0 flows imported simultaneously.

**Solution:**
- Delete all flows
- Reimport only v2.0 modular flows
- Or use separate Node-RED instances

### Getting Help

1. **Check Documentation:**
   - `nodered/NODE_RED_DEVELOPMENT.md` - Comprehensive guide
   - `nodered/flows/README.md` - Quick reference
   - `docs/TROUBLESHOOTING.md` - Common issues

2. **Enable Debug Mode:**
   - Add debug nodes to flows
   - Check browser console (F12)
   - Review Node-RED logs: `docker logs node-red-dashboard`

3. **Community Support:**
   - GitHub Issues: https://github.com/tinel-c/ServerBootShutdownManagemement/issues
   - Include: Node-RED version, browser, screenshots, error messages

---

## 👏 Acknowledgments

This release represents a complete architectural overhaul of the dashboard component, designed to support the growing needs of server management infrastructure while maintaining backward compatibility with existing backend services.

Special thanks to the Node-RED and Vue.js communities for excellent documentation and examples.

---

## 📊 Statistics

### Code Metrics
- **8 new modular flow files** created
- **2,000+ lines** of documentation added
- **3 major documentation files** created
- **16+ data points** displayed per health check
- **1-second** real-time update interval
- **50-entry** log buffer (configurable)
- **4 reserved server slots** (30-69) for future expansion

### File Changes
- **Modified:** 1 file (`README.md`)
- **Created:** 12 files (8 flows + 3 docs + 1 release notes)
- **Deprecated:** 1 file (`flows.json`)

---

## 📄 License

This project remains under the MIT License. See [LICENSE](LICENSE) file for details.

---

## 📞 Contact

**Author:** Constantin Bogza  
**Repository:** https://github.com/tinel-c/ServerBootShutdownManagemement  
**Version:** 2.0.0  
**Release Date:** December 29, 2025

---

**Enjoy the new modular architecture and comprehensive health monitoring! 🎉**

