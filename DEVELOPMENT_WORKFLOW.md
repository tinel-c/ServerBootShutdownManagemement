# Development Workflow

This document outlines the standardized workflow for implementing features and fixing bugs in the Server Management System.

## 📋 Table of Contents

- [Workflow Overview](#workflow-overview)
- [Feature Development](#feature-development)
- [Bug Fixes](#bug-fixes)
- [Testing](#testing)
- [Documentation](#documentation)
- [Release Process](#release-process)
- [Best Practices](#best-practices)

---

## Workflow Overview

### 1. **Planning Phase**
- Identify the feature or bug
- Document the problem/requirement
- Create hypotheses (for bugs)
- Plan the solution approach

### 2. **Implementation Phase**
- Write code following project conventions
- Add instrumentation/logging if needed
- Test locally

### 3. **Testing Phase**
- Test on development environment
- Verify with runtime evidence
- Test on production (if applicable)

### 4. **Documentation Phase**
- Update relevant documentation
- Update CHANGELOG.md
- Update README.md if needed

### 5. **Release Phase**
- Commit with descriptive messages
- Push to GitHub
- Create release notes (for major changes)

---

## Feature Development

### Step-by-Step Process

#### 1. **Create Feature Branch** (Optional for small features)
```bash
git checkout -b feature/feature-name
```

#### 2. **Implement Feature**
- Write clean, documented code
- Follow existing code patterns
- Add error handling
- Include logging

#### 3. **Test Feature**
```bash
# Test locally
cd /opt/dell_server_management
source venv/bin/activate
python3 scripts/your_script.py

# Test with services
sudo systemctl restart your-service.service
./status.sh -l
```

#### 4. **Update Documentation**
- Add to `CHANGELOG.md` under `[Unreleased]`
- Update `README.md` if user-facing
- Create/update specific guides if needed

#### 5. **Commit Changes**
```bash
git add .
git commit -m "feat: Brief description of feature

- Detailed point 1
- Detailed point 2
- Related issue/requirement

Implements: #issue-number (if applicable)"

git push origin feature/feature-name
```

#### 6. **Merge to Main**
```bash
git checkout main
git merge feature/feature-name
git push origin main
```

---

## Bug Fixes

### Debug-First Approach

#### 1. **Reproduce the Bug**
- Document exact steps to reproduce
- Capture error messages/logs
- Note environment details

#### 2. **Generate Hypotheses**
Create 3-5 specific hypotheses about the root cause:

**Example:**
- **Hypothesis A**: Environment variables not loaded before YAML processing
- **Hypothesis B**: Regex pattern doesn't match embedded placeholders
- **Hypothesis C**: Service runs with wrong working directory
- **Hypothesis D**: Permissions prevent reading .env file
- **Hypothesis E**: Cache/stale code being executed

#### 3. **Add Instrumentation**
Add logging to test hypotheses:

```python
# Example instrumentation
logger.info(f"Testing Hypothesis A: env_var = {os.getenv('VAR_NAME')}")
logger.info(f"Testing Hypothesis B: api_url before = {api_url}")
# ... process ...
logger.info(f"Testing Hypothesis B: api_url after = {api_url}")
```

#### 4. **Collect Runtime Evidence**
```bash
# Restart service with instrumentation
sudo systemctl restart service-name.service

# Collect logs
sudo journalctl -u service-name.service -n 100 > debug_logs.txt

# Analyze logs
grep "Hypothesis" debug_logs.txt
```

#### 5. **Evaluate Hypotheses**
For each hypothesis:
- ✅ **CONFIRMED** - Evidence supports it
- ❌ **REJECTED** - Evidence contradicts it
- ⚠️ **INCONCLUSIVE** - Need more data

#### 6. **Implement Fix**
- Fix based on confirmed hypothesis
- **Keep instrumentation** for verification
- Test the fix

#### 7. **Verify Fix**
```bash
# Test with instrumentation still active
sudo systemctl restart service-name.service
sudo journalctl -u service-name.service -n 50

# Verify:
# - Original error is gone
# - Logs show expected behavior
# - No new errors introduced
```

#### 8. **Remove Instrumentation**
Only after fix is verified:
```bash
# Remove debug logs
# Clean up temporary code
# Commit clean version
```

#### 9. **Document Fix**
```bash
git commit -m "fix: Brief description of bug

Root Cause: Detailed explanation
Solution: What was changed
Tested: How it was verified

Fixes: #issue-number"
```

---

## Testing

### Local Testing

#### Python Scripts
```bash
cd /opt/dell_server_management
source venv/bin/activate

# Test individual script
python3 scripts/status/status_publisher.py

# Test with configuration
python3 -c "
from scripts.utils.config_loader import get_config
config = get_config()
print(config)
"
```

#### Services
```bash
# Stop service
sudo systemctl stop service-name.service

# Run manually to see output
cd /opt/dell_server_management
source venv/bin/activate
python3 scripts/path/to/script.py

# Check for errors
# Restart service
sudo systemctl start service-name.service
```

### Integration Testing

```bash
# Test full workflow
./status.sh -l                    # Check all services
sudo ./manage.sh restart          # Restart everything
./status.sh -l -n 50             # Check logs

# Test specific functionality
# - Send MQTT command
# - Check Telegram notifications
# - Verify dashboard updates
```

### Production Testing

```bash
# Deploy to production
git pull
sudo ./update.sh

# Monitor for issues
./status.sh -l
sudo ./manage.sh logs

# Watch for 5-10 minutes
# Check Telegram notifications
# Verify expected behavior
```

---

## Documentation

### What to Document

#### For Features
- [ ] Update `CHANGELOG.md` with feature description
- [ ] Update `README.md` if user-facing
- [ ] Create specific guide if complex (e.g., `FEATURE_GUIDE.md`)
- [ ] Update `QUICK_REFERENCE.md` if adds commands
- [ ] Add code comments for complex logic

#### For Bug Fixes
- [ ] Update `CHANGELOG.md` with fix description
- [ ] Document root cause in commit message
- [ ] Update troubleshooting guide if common issue
- [ ] Add prevention notes if applicable

### Documentation Standards

#### CHANGELOG.md Format
```markdown
## [Version] - Date

### Added
- New feature description

### Fixed
- Bug fix description with root cause

### Changed
- Modified behavior description

### Deprecated
- Features being phased out
```

#### Commit Message Format
```
type: Brief description (50 chars max)

Detailed explanation of what and why (not how).
Wrap at 72 characters.

- Bullet points for multiple changes
- Reference issues/PRs if applicable

Fixes: #123
Implements: #456
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, no logic change)
- `refactor`: Code restructure (no behavior change)
- `test`: Adding/updating tests
- `chore`: Maintenance tasks

---

## Release Process

### Version Numbering

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR** (X.0.0): Breaking changes
- **MINOR** (2.X.0): New features, backward compatible
- **PATCH** (2.5.X): Bug fixes, backward compatible

### Release Checklist

#### 1. **Pre-Release**
- [ ] All tests passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped in relevant files

#### 2. **Create Release**
```bash
# Update version
# Edit CHANGELOG.md - move [Unreleased] to [X.Y.Z]

# Commit
git add .
git commit -m "chore: Release v2.6.0"

# Tag
git tag -a v2.6.0 -m "Release v2.6.0

Major changes:
- Feature 1
- Feature 2
- Bug fix 1
"

# Push
git push origin main
git push origin v2.6.0
```

#### 3. **GitHub Release**
- Go to GitHub → Releases → New Release
- Select tag `v2.6.0`
- Title: `v2.6.0 - Release Name`
- Description: Copy from CHANGELOG.md
- Attach any binaries (e.g., client zips)
- Publish release

#### 4. **Post-Release**
- [ ] Test installation from fresh clone
- [ ] Update deployment documentation if needed
- [ ] Announce in relevant channels

---

## Best Practices

### Code Quality

#### Python
```python
# Good: Clear, documented, error-handled
def get_server_status(server_name: str) -> Dict[str, Any]:
    """
    Get server status from Proxmox API.
    
    Args:
        server_name: Name of the server
        
    Returns:
        Dictionary with status information
        
    Raises:
        ConnectionError: If Proxmox API unreachable
    """
    try:
        # Implementation
        logger.info(f"Getting status for {server_name}")
        return status
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise
```

#### Shell Scripts
```bash
# Good: Error handling, clear output
check_service() {
    local service=$1
    
    if systemctl is-active --quiet "$service"; then
        echo "✓ $service is running"
        return 0
    else
        echo "✗ $service is not running"
        return 1
    fi
}
```

### Configuration Management

- **Never commit secrets** (.env files)
- **Use environment variables** for credentials
- **Provide templates** (.env.example)
- **Validate configuration** on startup
- **Document all variables** in templates

### Error Handling

```python
# Good: Specific, informative errors
try:
    result = api_call()
except ConnectionError as e:
    logger.error(f"Failed to connect to Proxmox API: {e}")
    logger.info("Check network connectivity and credentials")
    raise
except TimeoutError as e:
    logger.warning(f"API call timed out: {e}")
    logger.info("Retrying...")
    # Retry logic
```

### Logging

```python
# Good: Contextual, leveled logging
logger.debug(f"Connecting to {host}:{port}")
logger.info(f"Successfully connected to Proxmox API")
logger.warning(f"Retry attempt {attempt}/{max_attempts}")
logger.error(f"Failed after {max_attempts} attempts: {error}")
```

### Testing

- **Test happy path** - Normal operation
- **Test error cases** - What happens when things fail
- **Test edge cases** - Boundary conditions
- **Test integration** - Components working together
- **Verify with logs** - Runtime evidence, not assumptions

---

## Example: Complete Bug Fix Workflow

### Scenario: "UNKNOWN" Status Notifications

#### 1. **Problem Report**
```
User reports: Getting repeated "UNKNOWN" status notifications 
every 30-60 seconds on Telegram
```

#### 2. **Reproduction**
```bash
# Monitor logs
sudo journalctl -u status-publisher.service -f

# Observe:
# - IPMI connection errors
# - Status flipping between states
```

#### 3. **Hypotheses**
- **A**: IPMI connection timeouts
- **B**: State conflicts between health monitor and status publisher
- **C**: Proxmox API not being used
- **D**: Environment variables not loaded
- **E**: Placeholder replacement not working

#### 4. **Instrumentation**
```python
# Add logging to test hypotheses
logger.info(f"Hypothesis C: Using Proxmox API for {server_name}")
logger.info(f"Hypothesis D: T310_PROXMOX_HOST = {os.getenv('T310_PROXMOX_HOST')}")
logger.info(f"Hypothesis E: api_url = {proxmox_config.get('api_url')}")
```

#### 5. **Evidence Collection**
```bash
sudo systemctl restart status-publisher.service
sudo journalctl -u status-publisher.service -n 100 > evidence.log
```

#### 6. **Analysis**
```
✅ Hypothesis E CONFIRMED: api_url still has ${T310_PROXMOX_HOST}
❌ Hypothesis D REJECTED: Environment variable loads correctly
⚠️ Hypothesis C INCONCLUSIVE: Code exists but placeholder prevents use
```

#### 7. **Fix Implementation**
```python
# Change from exact match to regex replacement
def replace_env_vars(obj):
    if isinstance(obj, str) and '${' in obj:
        return re.sub(r'\$\{([^}]+)\}', replacer, obj)
```

#### 8. **Verification**
```bash
# Test fix
sudo systemctl restart status-publisher.service
sudo journalctl -u status-publisher.service -n 50

# Verify:
# ✓ api_url now shows: https://192.168.2.9:8006/api2/json
# ✓ Proxmox API connections successful
# ✓ No more UNKNOWN notifications
```

#### 9. **Cleanup & Commit**
```bash
# Remove instrumentation
# Commit clean code
git commit -m "fix: Environment variable replacement in YAML config

Root Cause: replace_env_vars() only matched exact \${VAR} strings,
not embedded patterns like 'https://\${HOST}:8006'

Solution: Implemented regex-based replacement to handle all \${VAR}
patterns within strings

Tested: Verified Proxmox API URL correctly resolves to IP address
and connections succeed

Fixes: Repeated UNKNOWN status notifications"
```

---

## Quick Reference

### Common Commands

```bash
# Development
git checkout -b feature/name
git add .
git commit -m "feat: description"
git push origin feature/name

# Testing
./status.sh -l
sudo ./manage.sh restart
./check_env.sh

# Debugging
sudo journalctl -u service-name.service -f
sudo systemctl status service-name.service
grep "error" /var/log/dell_server_management.log

# Release
git tag -a v2.6.0 -m "Release notes"
git push origin main --tags
```

### File Locations

- **Code**: `/opt/dell_server_management/scripts/`
- **Config**: `/opt/dell_server_management/config/`
- **Services**: `/etc/systemd/system/*.service`
- **Logs**: `journalctl -u service-name.service`

---

## Getting Help

- **Documentation**: Check `docs/` folder
- **Quick Reference**: See `QUICK_REFERENCE.md`
- **Troubleshooting**: See `docs/TROUBLESHOOTING.md`
- **Architecture**: See `docs/ARCHITECTURE.md`

---

**Remember**: Always test with runtime evidence, never assume code works without verification!
