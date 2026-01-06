@echo off
REM Client PC Monitor Uninstallation Script for Windows
REM Run as Administrator

echo ============================================================
echo Client PC Monitor Uninstallation
echo ============================================================
echo.

REM Check for administrator privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator!
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

set INSTALL_DIR=%ProgramFiles%\ClientMonitor

echo This will completely remove the Client Monitor from your system.
echo.
echo The following will be removed:
echo   - Task Scheduler entry (ClientMonitor)
echo   - Installation directory: %INSTALL_DIR%
echo   - All configuration files and logs
echo.
set /p CONFIRM="Are you sure you want to continue? (Y/N): "

if /i not "%CONFIRM%"=="Y" (
    echo.
    echo Uninstallation cancelled.
    pause
    exit /b 0
)

echo.
echo [1/3] Stopping Client Monitor (if running)...

REM Try to stop the process gracefully
tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq Client*" 2>nul | find /i "python.exe" >nul
if %errorLevel% equ 0 (
    echo Client Monitor is running, attempting to stop...
    taskkill /FI "WINDOWTITLE eq Client*" /IM python.exe /F >nul 2>&1
    timeout /t 2 /nobreak >nul
    echo Client Monitor stopped.
) else (
    echo Client Monitor is not running.
)

echo.
echo [2/3] Removing Task Scheduler entry...

schtasks /query /tn "ClientMonitor" >nul 2>&1
if %errorLevel% equ 0 (
    schtasks /delete /tn "ClientMonitor" /f >nul 2>&1
    if %errorLevel% equ 0 (
        echo Task Scheduler entry removed successfully.
    ) else (
        echo WARNING: Failed to remove Task Scheduler entry.
        echo You may need to remove it manually.
    )
) else (
    echo Task Scheduler entry not found (already removed or never created).
)

echo.
echo [3/3] Removing installation directory...

if exist "%INSTALL_DIR%" (
    echo Deleting: %INSTALL_DIR%
    
    REM Remove read-only attributes
    attrib -r "%INSTALL_DIR%\*.*" /s /d >nul 2>&1
    
    REM Delete directory
    rmdir /s /q "%INSTALL_DIR%" >nul 2>&1
    
    if exist "%INSTALL_DIR%" (
        echo WARNING: Could not fully remove installation directory.
        echo Some files may be in use. Please:
        echo   1. Close any programs using files in this directory
        echo   2. Manually delete: %INSTALL_DIR%
    ) else (
        echo Installation directory removed successfully.
    )
) else (
    echo Installation directory not found (already removed).
)

echo.
echo ============================================================
echo Uninstallation Complete!
echo ============================================================
echo.
echo The Client Monitor has been removed from your system.
echo.
echo If you had any custom configurations, they have been deleted.
echo To reinstall, run install_client.bat again.
echo.
echo Note: Python and pip remain installed on your system.
echo       If you want to remove them, use Windows Settings.
echo.
pause
