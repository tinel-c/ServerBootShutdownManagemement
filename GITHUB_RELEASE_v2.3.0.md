# v2.3.0 - Smart Client-Aware Automation with Activity Logging

**Release Date:** January 7, 2026  
**Tag:** v2.3.0

---

## 🎉 What's New

### 🤖 Smart Client-Aware Boot
Server automatically boots when clients need it! No more manual intervention required.

**How it works:**
- System detects when clients connect but server is down/offline/unknown
- Automatically sends WOL boot command
- Prevents duplicate commands with 5-minute cooldown
- Retries after cooldown if server still down

**Benefits:**
- ✅ Zero manual intervention
- ✅ Server ready when you need it
- ✅ Works with multiple clients
- ✅ Handles edge cases gracefully

### ⏳ Command Cooldown Protection
5-minute protection prevents command spam during boot/shutdown operations.

**Features:**
- Tracks last boot and shutdown timestamps
- Prevents duplicate commands within cooldown window
- Visual countdown banner in dashboard
- Respects server boot time (~2-3 minutes) + buffer

### 📋 Comprehensive Activity Logging
Complete audit trail of all automation events with timestamps and triggers.

**What's logged:**
- 🟢 Client connections (first client online)
- 🔴 Client disconnections (last client offline)
- 🚀 Boot commands (with cooldown tracking)
- ⏱️ Grace periods (5-minute countdowns)
- ⏹️ Shutdown executions
- ❌ Cancellations (when clients connect during grace)
- ✅ Configuration changes (automation toggle)

**UI Features:**
- Scrollable activity log (8 most recent events)
- Color-coded borders by event type
- Status badges (DETECTED, SENT, EXECUTED, CANCELLED)
- Emoji indicators for quick scanning
- Real-time timestamp formatting

### 🎨 Modern Dashboard Redesign
Complete UI overhaul with glassmorphism and live countdowns.

**Visual Improvements:**
- Dark gradient background (#0f172a → #1e293b)
- Glass-morphism effects with backdrop blur
- Smooth animations and transitions
- Live countdown timers
- Responsive grid layout
- Professional color scheme

**Dashboard Components:**
- Server status bar with pulsing indicator
- Cooldown banner with live countdown
- Action cards showing current state
- Activity log window
- Automation toggle switch

---

## 🐛 Critical Bug Fixes

### Shutdown Not Executing After Grace Period
**Problem:** Grace period expired but shutdown command wasn't sent.

**Root Cause:** 
- Mixed command outputs (boot + shutdown on same output)
- Incomplete MQTT message format

**Solution:**
- Separated command routing into 3 distinct outputs
- Fixed MQTT message format with all required fields
- Added proper timestamp and request_id tracking

**Result:** ✅ Shutdown now executes properly after grace period!

---

## 📊 Technical Improvements

### Files Modified
- `nodered/flows/40-client-tracking.json` - Client trigger logging
- `nodered/flows/41-client-automation.json` - Complete smart automation rewrite
- `nodered/flows/README.md` - Updated feature descriptions
- `README.md` - Added v2.3.0 changelog
- `docs/ARCHITECTURE.md` - Smart automation details
- `docs/architecture_diagram_v3.svg` - New modern SVG diagram

### New Flow Context Variables
```javascript
flow.set('last_boot_timestamp', ms);       // Cooldown tracking
flow.set('last_shutdown_timestamp', ms);   // Cooldown tracking
flow.set('activity_log', array);           // Event history (max 50)
```

### Enhanced Logic
- 3-output command routing (boot/shutdown/refresh separated)
- Cooldown checks in watchdog loop
- Client-aware boot detection
- Smart retry after cooldown
- Activity log storage and rotation

---

## 📚 New Documentation

1. **AUTOMATION_UPDATE.md** - Technical documentation for automation features
2. **SMART_WAKEUP_GUIDE.md** - User guide for smart wake-up functionality
3. **CLIENT_AWARE_BOOT_SUMMARY.md** - Implementation summary
4. **TRIGGER_LOGGING_UPDATE.md** - Activity logging details
5. **RELEASE_NOTES_v2.3.0.md** - Complete release notes
6. **ARCHITECTURE_DIAGRAM_DESCRIPTION.md** - Diagram specification
7. **docs/architecture_diagram_v3.svg** - Modern architecture diagram

---

## 🚀 Upgrade Instructions

### For Existing Users

1. **Backup current flows:**
   ```bash
   cd nodered
   cp flows.json flows.json.backup-$(date +%Y%m%d)
   ```

2. **Pull latest changes:**
   ```bash
   git pull origin main
   ```

3. **Import updated flows:**
   - Open Node-RED: http://localhost:1880
   - Import: `flows/40-client-tracking.json` (overwrite)
   - Import: `flows/41-client-automation.json` (overwrite)

4. **Deploy:**
   - Click "Deploy" button
   - Verify automation toggle is enabled

5. **Test:**
   - Boot a client PC
   - Check activity log for events
   - Verify automation responds

### Verification Checklist
- [ ] Dashboard loads without errors
- [ ] Automation toggle works
- [ ] Activity log displays events
- [ ] Cooldown banner appears after commands
- [ ] Client triggers logged (🟢/🔴)
- [ ] Shutdown executes after grace period

---

## 📈 What's Next (Future Enhancements)

Potential features for future releases:
- Configurable cooldown duration via UI
- Per-command cooldown settings
- Smart retry with exponential backoff
- Client priority levels
- Scheduled maintenance mode
- Email notifications
- Historical analytics

---

## 🔗 Links

- **Repository:** https://github.com/tinel-c/ServerBootShutdownManagemement
- **Documentation:** See `README.md` and `docs/` directory
- **Release Notes:** See `RELEASE_NOTES_v2.3.0.md`
- **Architecture Diagram:** `docs/architecture_diagram_v3.svg`

---

## 💬 Feedback & Support

For issues, questions, or feedback:
1. Check documentation in `nodered/` and `docs/` directories
2. Review activity log for automation events
3. See `docs/TROUBLESHOOTING.md`
4. Open GitHub issue with activity log excerpt

---

## 🙏 Thank You!

Thank you for using the Server Boot/Shutdown Management System. This release brings the automation to a production-ready state with intelligent, self-managing capabilities.

**Version:** 2.3.0  
**Release Date:** January 7, 2026  
**Status:** ✅ Production Ready

