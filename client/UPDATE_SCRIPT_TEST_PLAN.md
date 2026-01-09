# Update Script Test Plan for v2.4.0

## Overview

This test plan verifies that `update_client_files.bat` correctly installs the v2.4.0 release with the new tooltip enhancement features.

## Pre-Update Checklist

### Environment Setup
- [ ] Previous client version installed (v2.3.0 or earlier)
- [ ] Client Monitor is running in system tray
- [ ] Administrator privileges available
- [ ] Backup space available (minimum 50MB)

### Files to be Updated
- [ ] `client_monitor.py` - Contains tooltip enhancements
- [ ] `auto_updater.py` - Updated to version 2.4.0
- [ ] `README_CLIENT.md` - Updated documentation
- [ ] `TOOLTIP_FEATURE_GUIDE.md` - New feature guide
- [ ] `TOOLTIP_VISUAL_EXAMPLES.md` - New visual examples

## Update Process Test

### Step 1: Backup Creation ✅

**Expected Behavior:**
```
[1/6] Creating backup of current installation...
Removing old backup...
Backup created at C:\Program Files\ClientMonitor\backup
```

**Verification:**
- [ ] Backup directory created
- [ ] Old files preserved in backup folder
- [ ] All essential files backed up:
  - [ ] `client_monitor.py`
  - [ ] `auto_updater.py`
  - [ ] `config\client_config.yaml`
  - [ ] `config\.env`

**Test:**
```cmd
dir "C:\Program Files\ClientMonitor\backup"
```

---

### Step 2: Stop Client Monitor ✅

**Expected Behavior:**
```
[2/6] Stopping Client Monitor...
Client Monitor stopped.
```

**Verification:**
- [ ] System tray icon disappears
- [ ] Python processes terminated
- [ ] No file locks on installation directory

**Test:**
```cmd
tasklist | findstr python
```
Expected: No ClientMonitor processes

---

### Step 3: Copy Updated Files ✅

**Expected Behavior:**
```
[3/6] Copying updated files...
 - client_monitor.py
 - auto_updater.py
 - requirements_client.txt
 - config\client_config.yaml
All files copied successfully.
```

**Verification:**
- [ ] All core files updated
- [ ] Config preserved (`.env` not overwritten)
- [ ] Documentation copied (optional)

**Test:**
```cmd
type "C:\Program Files\ClientMonitor\client_monitor.py" | findstr "2.4.0"
type "C:\Program Files\ClientMonitor\auto_updater.py" | findstr "2.4.0"
```

**Check New Files:**
```cmd
dir "C:\Program Files\ClientMonitor\TOOLTIP*.md"
```
Expected: Two new documentation files

---

### Step 4: Install Dependencies ✅

**Expected Behavior:**
```
[4/6] Installing Python dependencies...
Dependencies installed successfully.
```

**Verification:**
- [ ] No new dependencies required (all already installed)
- [ ] Existing dependencies still work
- [ ] No error messages

**Test:**
```cmd
python -c "import paho.mqtt, pystray, requests, packaging; print('All dependencies OK')"
```

Expected output: `All dependencies OK`

---

### Step 5: Start Client Monitor ✅

**Expected Behavior:**
```
[5/6] Starting Client Monitor...
Scheduled task triggered successfully.
```

**Verification:**
- [ ] Client Monitor process starts
- [ ] System tray icon appears
- [ ] No startup errors in logs

**Test:**
```cmd
tasklist | findstr python
schtasks /query /tn "ClientMonitor"
```

---

### Step 6: Verify Update ✅

**Expected Behavior:**
```
[6/6] Verifying update...
Verification successful.

============================================================
UPDATE COMPLETE!
============================================================

Client Monitor has been updated successfully.
The service/task should now be running with the new version.

To verify the update:
  1. Hover over system tray icon to see version info and update schedule
  2. Check logs: C:\Program Files\ClientMonitor\logs\client_monitor.log
  3. Verify auto-updater is initialized in logs
  4. Check tooltip shows: v2.4.0 and update check countdown
```

**Verification:**
- [ ] All required files exist
- [ ] No rollback triggered
- [ ] Success message displayed

---

## Post-Update Verification

### Tooltip Feature Verification 🔍

#### Test 1: Hover Over System Tray Icon
**Action:** Hover mouse over the system tray icon

**Expected Tooltip:**
```
CM: [your-hostname]
v2.4.0 (up to date)
Broker: OK
Srv: ONLINE/OFFLINE/UNKNOWN
HB: [countdown]s
Update chk: Pending
Last: [timestamp] - Startup
```

**Checklist:**
- [ ] Client ID displayed
- [ ] Version shows `v2.4.0`
- [ ] Update check status shows "Pending" (first run)
- [ ] Broker status visible
- [ ] Server status visible
- [ ] Heartbeat countdown visible

#### Test 2: Wait for First Update Check
**Action:** Wait or manually trigger update check (Right-click → Check for Updates)

**Expected Tooltip After Check:**
```
CM: [your-hostname]
v2.4.0 (up to date)
Broker: OK
Srv: ONLINE
HB: [countdown]s
Update chk: 23h 59m
Last: [timestamp] - Up to date
```

**Checklist:**
- [ ] Update check countdown appears
- [ ] Shows time until next check (e.g., "23h 59m")
- [ ] Last action shows update check result

#### Test 3: Manual Update Check
**Action:** Right-click system tray icon → "Check for Updates"

**Expected Behavior:**
- [ ] "Check for Updates" option visible in context menu
- [ ] Tooltip shows "Checking updates..." briefly
- [ ] Result appears in "Last:" line
- [ ] No errors in log file

#### Test 4: Version Display States
**Verify all possible version states:**

- [ ] **Unknown State** (before first check):
  ```
  v2.4.0
  ```

- [ ] **Up to Date** (after check, no update):
  ```
  v2.4.0 (up to date)
  ```

- [ ] **Update Available** (if newer version exists):
  ```
  v2.4.0 → v2.5.0 ⚠
  ```

### Log File Verification 📋

**Action:** Check the log file

```cmd
type "C:\Program Files\ClientMonitor\logs\client_monitor.log"
```

**Expected Log Entries:**
```
Client Monitor initialized for: [hostname]
Auto-updater initialized (check interval: 24h)
Connected to MQTT broker
```

**Checklist:**
- [ ] Auto-updater initialization logged
- [ ] Current version (2.4.0) mentioned
- [ ] No error messages about missing modules
- [ ] MQTT connection successful

### Configuration Preservation 🔒

**Verify user settings preserved:**

```cmd
type "C:\Program Files\ClientMonitor\config\.env"
```

**Checklist:**
- [ ] `.env` file still exists
- [ ] MQTT credentials unchanged
- [ ] Custom client name preserved (if set)
- [ ] All custom settings intact

### Documentation Verification 📚

**Check documentation files installed:**

```cmd
dir "C:\Program Files\ClientMonitor\*.md"
```

**Expected Files:**
- [ ] `README_CLIENT.md` (updated)
- [ ] `README_CLIENT_SHUTDOWN.md`
- [ ] `README_AUTO_UPDATE.md`
- [ ] `TOOLTIP_FEATURE_GUIDE.md` (new)
- [ ] `TOOLTIP_VISUAL_EXAMPLES.md` (new)

---

## Rollback Test (Optional)

### Trigger Rollback Scenario

**Scenario:** Simulate a failed update to test rollback

**Steps:**
1. Manually delete `client_monitor.py` after Step 3
2. Let update script continue to Step 6
3. Verify rollback triggers

**Expected Behavior:**
```
ERROR: client_monitor.py not found!

============================================================
UPDATE FAILED - ROLLING BACK
============================================================

Restoring from backup...
Rollback complete. Previous version restored.
```

**Verification:**
- [ ] Rollback message displayed
- [ ] Files restored from backup
- [ ] Client Monitor restarted with old version
- [ ] No data loss

---

## Common Issues and Resolutions

### Issue 1: Update Script Won't Run
**Symptom:** Script exits immediately or shows access denied

**Cause:** Not running as Administrator

**Solution:**
```cmd
Right-click update_client_files.bat → Run as administrator
```

### Issue 2: Tooltip Doesn't Show New Version
**Symptom:** Tooltip still shows old format

**Cause:** Old process still running

**Solution:**
```cmd
taskkill /F /IM python.exe /FI "WINDOWTITLE eq ClientMonitor*"
schtasks /run /tn "ClientMonitor"
```

### Issue 3: Update Check Shows "Pending" Forever
**Symptom:** Never changes from "Pending"

**Cause:** No update check performed yet

**Solution:**
- Wait for automatic check (24 hours)
- Or manually trigger: Right-click → Check for Updates
- Check internet connectivity

### Issue 4: Dependencies Installation Failed
**Symptom:** Warning about failed dependency installation

**Cause:** Python pip issue or no internet

**Solution:**
```cmd
cd "C:\Program Files\ClientMonitor"
python -m pip install --upgrade pip
python -m pip install -r requirements_client.txt
```

### Issue 5: Backup Directory Full
**Symptom:** Warning about incomplete backup

**Cause:** Insufficient disk space

**Solution:**
- Free up disk space (need ~50MB)
- Delete old backup manually
- Retry update

---

## Success Criteria ✅

Update is considered successful if:

1. **Core Functionality:**
   - [ ] Client Monitor running without errors
   - [ ] MQTT connection established
   - [ ] Heartbeats being sent
   - [ ] System tray icon visible

2. **New Features:**
   - [ ] Tooltip shows version information
   - [ ] Tooltip shows update check countdown
   - [ ] "Check for Updates" menu option works
   - [ ] Update indicator appears correctly

3. **Stability:**
   - [ ] No crashes or exceptions
   - [ ] Log file shows clean startup
   - [ ] Auto-updater initialized properly
   - [ ] Configuration preserved

4. **Documentation:**
   - [ ] New documentation files installed
   - [ ] README updated with new features
   - [ ] Feature guides accessible

---

## Test Report Template

```
Update Test Report
==================

Date: [Date]
Tester: [Name]
Previous Version: [Version]
New Version: 2.4.0

Pre-Update Environment:
- OS: Windows [version]
- Python: [version]
- Installation: [Service/Task]

Update Process:
□ Backup Created Successfully
□ Client Stopped Successfully
□ Files Copied Successfully
□ Dependencies Installed Successfully
□ Client Started Successfully
□ Verification Passed

Tooltip Feature Tests:
□ Version displayed correctly
□ Update check countdown shows
□ Manual update check works
□ All tooltip states verified

Issues Encountered:
[None / List issues]

Overall Result: PASS / FAIL

Notes:
[Additional observations]
```

---

## Automated Verification Script

Create a PowerShell script to verify the update:

```powershell
# verify_update.ps1
$installDir = "${env:ProgramFiles}\ClientMonitor"

Write-Host "Verifying Client Monitor Update v2.4.0..." -ForegroundColor Cyan

# Check files
$files = @(
    "client_monitor.py",
    "auto_updater.py",
    "config\client_config.yaml",
    "TOOLTIP_FEATURE_GUIDE.md",
    "TOOLTIP_VISUAL_EXAMPLES.md"
)

$allFilesExist = $true
foreach ($file in $files) {
    $path = Join-Path $installDir $file
    if (Test-Path $path) {
        Write-Host "✓ $file" -ForegroundColor Green
    } else {
        Write-Host "✗ $file MISSING" -ForegroundColor Red
        $allFilesExist = $false
    }
}

# Check version
$version = python -c "import sys; sys.path.insert(0, '${installDir}'); from auto_updater import CURRENT_VERSION; print(CURRENT_VERSION)"
if ($version -eq "2.4.0") {
    Write-Host "✓ Version: $version" -ForegroundColor Green
} else {
    Write-Host "✗ Version: $version (expected 2.4.0)" -ForegroundColor Red
}

# Check process
$process = Get-Process -Name python* -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowTitle -match "ClientMonitor"}
if ($process) {
    Write-Host "✓ Client Monitor is running" -ForegroundColor Green
} else {
    Write-Host "✗ Client Monitor is NOT running" -ForegroundColor Red
}

if ($allFilesExist -and $version -eq "2.4.0" -and $process) {
    Write-Host "`nUPDATE VERIFICATION: PASSED" -ForegroundColor Green
} else {
    Write-Host "`nUPDATE VERIFICATION: FAILED" -ForegroundColor Red
}
```

---

**Test Plan Version:** 1.0  
**Target Release:** v2.4.0  
**Last Updated:** January 9, 2026  
**Status:** Ready for Testing

