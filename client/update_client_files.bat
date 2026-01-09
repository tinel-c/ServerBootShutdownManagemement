@echo off
REM Update Script for Client PC Monitor v2.4.0+
REM Run as Administrator
REM Handles backup, file updates, dependency installation, and rollback

echo ============================================================
echo Client PC Monitor Update v2.4.0+
echo ============================================================
echo.

REM Check for administrator privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator!
    pause
    exit /b 1
)

set INSTALL_DIR=%ProgramFiles%\ClientMonitor
set BACKUP_DIR=%INSTALL_DIR%\backup
set UPDATE_SOURCE=%~dp0

if not exist "%INSTALL_DIR%" (
    echo ERROR: Installation directory not found at %INSTALL_DIR%
    echo Please run install_client.bat first.
    pause
    exit /b 1
)

REM ===========================================================
REM Step 1: Create Backup
REM ===========================================================
echo [1/6] Creating backup of current installation...

if exist "%BACKUP_DIR%" (
    echo Removing old backup...
    rmdir /s /q "%BACKUP_DIR%"
)

mkdir "%BACKUP_DIR%"
xcopy /E /I /Q /Y "%INSTALL_DIR%\*" "%BACKUP_DIR%\" >nul 2>&1
if %errorLevel% neq 0 (
    echo WARNING: Backup may be incomplete. Continue anyway? (Y/N)
    choice /C YN /N
    if errorlevel 2 exit /b 1
)
echo Backup created at %BACKUP_DIR%

REM ===========================================================
REM Step 2: Stop Client Monitor
REM ===========================================================
echo [2/6] Stopping Client Monitor...

REM Try to stop service first (if installed as service)
sc query ClientMonitor >nul 2>&1
if %errorLevel% equ 0 (
    echo Stopping ClientMonitor service...
    net stop ClientMonitor >nul 2>&1
    timeout /t 2 /nobreak >nul
)

REM Kill any running processes
taskkill /F /IM python.exe /FI "WINDOWTITLE eq ClientMonitor*" >nul 2>&1
taskkill /F /IM pythonw.exe /FI "WINDOWTITLE eq ClientServerBootShutdownManagement*" >nul 2>&1
taskkill /F /IM ClientMonitor.exe >nul 2>&1

timeout /t 1 /nobreak >nul
echo Client Monitor stopped.

REM ===========================================================
REM Step 3: Copy Updated Files
REM ===========================================================
echo [3/6] Copying updated files...

REM Copy main Python files
if exist "%UPDATE_SOURCE%client_monitor.py" (
    copy /Y "%UPDATE_SOURCE%client_monitor.py" "%INSTALL_DIR%\" >nul
    echo  - client_monitor.py
)

if exist "%UPDATE_SOURCE%auto_updater.py" (
    copy /Y "%UPDATE_SOURCE%auto_updater.py" "%INSTALL_DIR%\" >nul
    echo  - auto_updater.py
)

if exist "%UPDATE_SOURCE%requirements_client.txt" (
    copy /Y "%UPDATE_SOURCE%requirements_client.txt" "%INSTALL_DIR%\" >nul
    echo  - requirements_client.txt
)

REM Copy config files (preserve user settings by not overwriting .env)
if exist "%UPDATE_SOURCE%config\client_config.yaml" (
    if not exist "%INSTALL_DIR%\config" mkdir "%INSTALL_DIR%\config"
    copy /Y "%UPDATE_SOURCE%config\client_config.yaml" "%INSTALL_DIR%\config\" >nul
    echo  - config\client_config.yaml
)

REM Copy documentation (optional, won't fail if missing)
if exist "%UPDATE_SOURCE%README_CLIENT.md" (
    copy /Y "%UPDATE_SOURCE%README_CLIENT.md" "%INSTALL_DIR%\" >nul 2>&1
)
if exist "%UPDATE_SOURCE%README_CLIENT_SHUTDOWN.md" (
    copy /Y "%UPDATE_SOURCE%README_CLIENT_SHUTDOWN.md" "%INSTALL_DIR%\" >nul 2>&1
)
if exist "%UPDATE_SOURCE%README_AUTO_UPDATE.md" (
    copy /Y "%UPDATE_SOURCE%README_AUTO_UPDATE.md" "%INSTALL_DIR%\" >nul 2>&1
)

echo All files copied successfully.

REM ===========================================================
REM Step 4: Install/Update Python Dependencies
REM ===========================================================
echo [4/6] Installing Python dependencies...

if exist "%INSTALL_DIR%\requirements_client.txt" (
    python -m pip install --quiet --upgrade pip >nul 2>&1
    python -m pip install --quiet -r "%INSTALL_DIR%\requirements_client.txt" >nul 2>&1
    if %errorLevel% equ 0 (
        echo Dependencies installed successfully.
    ) else (
        echo WARNING: Failed to install dependencies. Update may not work correctly.
        echo You may need to run: pip install -r requirements_client.txt
    )
) else (
    echo WARNING: requirements_client.txt not found. Skipping dependency installation.
)

REM ===========================================================
REM Step 5: Start Client Monitor
REM ===========================================================
echo [5/6] Starting Client Monitor...

REM Try to start service first (if installed as service)
sc query ClientMonitor >nul 2>&1
if %errorLevel% equ 0 (
    echo Starting ClientMonitor service...
    net start ClientMonitor >nul 2>&1
    timeout /t 2 /nobreak >nul
    
    REM Check if service started successfully
    sc query ClientMonitor | find "RUNNING" >nul
    if %errorLevel% equ 0 (
        echo Service started successfully.
        goto :update_complete
    ) else (
        echo WARNING: Service failed to start. Trying scheduled task...
    )
)

REM Try scheduled task
schtasks /run /tn "ClientMonitor" >nul 2>&1
if %errorLevel% equ 0 (
    echo Scheduled task triggered successfully.
    timeout /t 3 /nobreak >nul
    goto :update_complete
) else (
    echo WARNING: Could not start via service or scheduled task.
    echo Please start manually or log out and back in.
)

:update_complete

REM ===========================================================
REM Step 6: Verify Update
REM ===========================================================
echo [6/6] Verifying update...

REM Check if required files exist
set VERIFY_OK=1

if not exist "%INSTALL_DIR%\client_monitor.py" (
    echo ERROR: client_monitor.py not found!
    set VERIFY_OK=0
)

if not exist "%INSTALL_DIR%\auto_updater.py" (
    echo ERROR: auto_updater.py not found!
    set VERIFY_OK=0
)

if not exist "%INSTALL_DIR%\config\client_config.yaml" (
    echo ERROR: client_config.yaml not found!
    set VERIFY_OK=0
)

if %VERIFY_OK% equ 0 (
    echo.
    echo ============================================================
    echo UPDATE FAILED - ROLLING BACK
    echo ============================================================
    echo.
    echo Restoring from backup...
    
    REM Stop any running instances
    net stop ClientMonitor >nul 2>&1
    taskkill /F /IM python.exe /FI "WINDOWTITLE eq ClientMonitor*" >nul 2>&1
    
    REM Restore from backup
    xcopy /E /I /Q /Y "%BACKUP_DIR%\*" "%INSTALL_DIR%\" >nul 2>&1
    
    REM Restart
    net start ClientMonitor >nul 2>&1
    schtasks /run /tn "ClientMonitor" >nul 2>&1
    
    echo Rollback complete. Previous version restored.
    echo.
    echo Please check the logs and try updating again.
    pause
    exit /b 1
)

echo Verification successful.
echo.
echo ============================================================
echo UPDATE COMPLETE!
echo ============================================================
echo.
echo Client Monitor has been updated successfully.
echo The service/task should now be running with the new version.
echo.
echo Backup location: %BACKUP_DIR%
echo.
echo To verify the update:
echo   1. Check system tray icon (should show new name)
echo   2. Check logs: %INSTALL_DIR%\logs\client_monitor.log
echo   3. Verify auto-updater is initialized in logs
echo.
echo You can delete the backup folder once you confirm everything works.
echo.
pause
