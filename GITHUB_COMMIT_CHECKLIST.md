# GitHub Commit & Release Checklist v3.1.0

## Pre-Commit Checklist

### ✅ Documentation Updated

- [x] `README.md` - Updated features (Ping Fallback, Shutdown Guard) and version
- [x] `CHANGELOG.md` - Added v3.1.0 entry
- [x] `RELEASE_NOTES_v3.1.0.md` - Created detailed changelog
- [x] `walkthrough.md` - Verification details documented

### ✅ Code Files

- [x] `scripts/status/status_publisher.py` - Ping fallback and timeout increase
- [x] `nodered/flows/41-client-automation.json` - Watchdog guard & client-only recovery

### ✅ Testing

- [x] Automated logic test for ping fallback (test_fallback.py)
- [x] Manual inspection of Node-RED logic
- [x] Verified status transitions (online/offline)
- [x] No linting errors

### ✅ Architecture

- [x] Version numbers updated (3.0.0 → 3.1.0)
- [x] Stability improvements documented

## Commit Message

```
feat: Enhance Dell T310 stability with Ping Fallback and Shutdown Guard (v3.1.0)

Major Improvements:
- Added ICMP ping fallback to status_publisher.py for Dell T310
- Increased Proxmox API timeout to 15s for better stability
- Implemented 10-minute Shutdown Guard in Node-RED watchdog
- Restricted Recovery Boots to connections with active clients
- Improved activity logging for recovery events

Technical Details:
- Integrated subprocess-based ping utility in status_publisher
- Corrected "UNKNOWN" status logic to report "offline" on API+Ping failure
- Added timeSinceLastShutdown check in 41-client-automation.json

Fixes:
- Resolves the "UNKNOWN" status reboot loop on hardware power-down
- Prevents unintended boots when no clients are connected
```

## Git Commands

### 1. Stage All Changes
```bash
git add .
```

### 2. Commit with Message
```bash
git commit -m "feat: Enhance Dell T310 stability with Ping Fallback and Shutdown Guard (v3.1.0)"
```

### 3. Push to GitHub
```bash
git push origin main
```

## GitHub Release Steps

1. Go to repository on GitHub
2. Click "Releases" → "Create a new release"
3. **Tag version**: `v3.1.0`
4. **Target**: `main` branch
5. **Release title**: `v3.1.0 - Enhanced Stability & Status Fallback`
6. **Description**: Copy from `RELEASE_NOTES_v3.1.0.md`
7. Click **"Publish release"**

---
**Status**: ✅ Ready for commit and release  
**Version**: 3.1.0  
**Date**: January 18, 2026  
**Breaking Changes**: None  
**Backward Compatible**: Yes
