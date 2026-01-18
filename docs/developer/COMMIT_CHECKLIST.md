# GitHub Commit & Release Checklist v3.1.1

## Pre-Commit Checklist

### ✅ Documentation Updated

- [x] `README.md` - Updated version to 3.1.1 and added release entry
- [x] `CHANGELOG.md` - Added v3.1.1 entry
- [x] `walkthrough.md` - Reliability fixes documented

### ✅ Code Files

- [x] `update.sh` - Parallel service stop implementation
- [x] `scripts/status/health_monitor.py` - Added SIGTERM handler and clean exit
- [x] `systemd/*.service` - All services updated with `TimeoutStopSec=15`

### ✅ Testing

- [x] Verified `health_monitor.py` signal handling
- [x] Audited `update.sh` parallel stop syntax
- [x] Verified systemd service timeouts
- [x] No linting errors

### ✅ Architecture

- [x] Version numbers updated (3.1.0 → 3.1.1)

## Commit Message

```
fix: Enhance update script reliability and service shutdown (v3.1.1)

Reliability Improvements:
- Parallelized service stops in update.sh to reduce total wait time
- Implemented GRACEFUL shutdown in health_monitor.py (SIGTERM handler)
- Added TimeoutStopSec=15 fallback to all systemd service definitions
- Improved shutdown responsiveness for manage.sh and updates

Fixes:
- Resolves occasional hangs during update.sh at "Step 1: Stopping services"
- Ensures Health Monitor cleans up MQTT connections on termination
```

## Git Commands

### 1. Stage All Changes
```bash
git add .
```

### 2. Commit with Message
```bash
git commit -m "fix: Enhance update script reliability and service shutdown (v3.1.1)"
```

### 3. Push to GitHub
```bash
git push origin main
```

## GitHub Release Steps

1. Go to repository on GitHub
2. Click "Releases" → "Create a new release"
3. **Tag version**: `v3.1.1`
4. **Target**: `main` branch
5. **Release title**: `v3.1.1 - Update Script Reliability & Shutdown Fixes`
6. **Description**: 
   - Parallel service stop in update.sh
   - Proper SIGTERM handler in health_monitor.py
   - TimeoutStopSec=15 fallback for all services
7. Click **"Publish release"**

---
**Status**: ✅ Ready for commit and release  
**Version**: 3.1.1  
**Date**: January 18, 2026  
**Breaking Changes**: None  
**Backward Compatible**: Yes
