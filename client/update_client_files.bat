@echo off
REM Update Script for Client PC Monitor
REM Run as Administrator

echo ============================================================
echo Client PC Monitor Update
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

if not exist "%INSTALL_DIR%" (
    echo ERROR: Installation directory not found at %INSTALL_DIR%
    echo Please run install_client.bat first.
    pause
    exit /b 1
)

echo [1/3] Copying updated application files...
copy /Y "%~dp0client_monitor.py" "%INSTALL_DIR%\" >nul
copy /Y "%~dp0config\client_config.yaml" "%INSTALL_DIR%\config\" >nul
echo Files updated.

echo [2/3] Restarting Client Monitor...
REM Kill existing processes if any
taskkill /F /IM python.exe /FI "WINDOWTITLE eq ClientMonitor*" >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1

REM Restart the scheduled task
schtasks /run /tn "ClientMonitor" >nul 2>&1
if %errorLevel% equ 0 (
    echo Task "ClientMonitor" triggered successfully.
) else (
    echo WARNING: Could not trigger "ClientMonitor" task. 
    echo Please start it manually or log out and back in.
)

echo.
echo [3/3] Update Complete!
echo ============================================================
echo.
pause
