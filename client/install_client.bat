@echo off
REM Client PC Monitor Installation Script for Windows
REM Run as Administrator

echo ============================================================
echo Client PC Monitor Installation
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

echo [1/6] Checking Python installation...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python 3.8 or higher from https://www.python.org/
    pause
    exit /b 1
)
echo Python found.
echo.

REM Set installation directory
set INSTALL_DIR=%ProgramFiles%\ClientMonitor
echo [2/6] Creating installation directory: %INSTALL_DIR%
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if not exist "%INSTALL_DIR%\config" mkdir "%INSTALL_DIR%\config"
if not exist "%INSTALL_DIR%\logs" mkdir "%INSTALL_DIR%\logs"

REM Grant write permissions to the logs and config directory for all authenticated users
REM This prevents PermissionError when writing logs or .env in Program Files
icacls "%INSTALL_DIR%\logs" /grant *S-1-5-11:(OI)(CI)M /T >nul 2>&1
icacls "%INSTALL_DIR%\config" /grant *S-1-5-11:(OI)(CI)M /T >nul 2>&1
echo Directory permissions configured.
echo.

REM Stop existing instance if running
echo Checking for running instances...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq ClientMonitor*" >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1
echo Done.
echo.

REM Copy files
echo [3/6] Copying application files...
copy /Y "%~dp0client_monitor.py" "%INSTALL_DIR%\" >nul
if exist "%~dp0auto_updater.py" copy /Y "%~dp0auto_updater.py" "%INSTALL_DIR%\" >nul
copy /Y "%~dp0uninstall_client.bat" "%INSTALL_DIR%\" >nul
copy /Y "%~dp0requirements_client.txt" "%INSTALL_DIR%\" >nul
copy /Y "%~dp0config\client_config.yaml" "%INSTALL_DIR%\config\" >nul

REM Check if .env already exists, if not copy example
if not exist "%INSTALL_DIR%\config\.env" (
    copy /Y "%~dp0config\.env.example" "%INSTALL_DIR%\config\.env" >nul
    echo Created new .env file from example
) else (
    echo .env file already exists, keeping existing configuration
)
echo.

REM Install Python dependencies
echo [4/6] Installing Python dependencies...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r "%INSTALL_DIR%\requirements_client.txt"
if %errorLevel% neq 0 (
    echo WARNING: Some dependencies may have failed to install
    echo Please check the output above
)
echo.

REM Configure MQTT settings
echo [5/6] Configuring MQTT connection...
echo.
echo Please enter your MQTT broker details:
echo (Press Enter to keep default values shown in brackets)
echo.

set /p MQTT_HOST="MQTT Broker Host [192.168.2.4]: "
if "%MQTT_HOST%"=="" set MQTT_HOST=192.168.2.4

set /p MQTT_PORT="MQTT Broker Port [1883]: "
if "%MQTT_PORT%"=="" set MQTT_PORT=1883

set /p MQTT_USER="MQTT Username [none]: "
if "%MQTT_USER%"=="" set MQTT_USER=none

set /p MQTT_PASS="MQTT Password [none]: "
if "%MQTT_PASS%"=="" set MQTT_PASS=none

set /p TARGET_SRV="Target Server to monitor [dell/t310]: "
if "%TARGET_SRV%"=="" set TARGET_SRV=dell/t310

echo.
echo Writing configuration to .env file...
(
echo # MQTT Broker Configuration
echo MQTT_BROKER_HOST=%MQTT_HOST%
echo MQTT_BROKER_PORT=%MQTT_PORT%
echo.
echo # MQTT Authentication
echo MQTT_USERNAME=%MQTT_USER%
echo MQTT_PASSWORD=%MQTT_PASS%
echo.
echo # Target Server
echo TARGET_SERVER=%TARGET_SRV%
echo.
echo # Standard Defaults
echo HEARTBEAT_INTERVAL=60
echo LOG_LEVEL=INFO
echo ENABLE_TRAY_ICON=true
) > "%INSTALL_DIR%\config\.env"
echo Created %INSTALL_DIR%\config\.env successfully.
echo.

REM Create startup task
echo [6/6] Creating Windows startup task...

REM Create VBS script to run Python without console window
echo Set WshShell = CreateObject("WScript.Shell") > "%INSTALL_DIR%\run_hidden.vbs"
echo WshShell.Run "python ""%INSTALL_DIR%\client_monitor.py""", 0, False >> "%INSTALL_DIR%\run_hidden.vbs"

REM Create Task Scheduler task
schtasks /query /tn "ClientMonitor" >nul 2>&1
if %errorLevel% equ 0 (
    echo Task already exists, deleting old task...
    schtasks /delete /tn "ClientMonitor" /f >nul
)

schtasks /create /tn "ClientMonitor" /tr "wscript.exe \"%INSTALL_DIR%\run_hidden.vbs\"" /sc onlogon /rl highest /f >nul
if %errorLevel% equ 0 (
    echo Startup task created successfully
) else (
    echo ERROR: Failed to create startup task
    echo You may need to create it manually
)
echo.

echo ============================================================
echo Installation Complete!
echo ============================================================
echo.
echo Installation directory: %INSTALL_DIR%
echo Configuration file: %INSTALL_DIR%\config\.env
echo Log file: %INSTALL_DIR%\logs\client_monitor.log
echo.
echo The client monitor will start automatically on next login.
echo.
echo To start the monitor now, run:
echo   python "%INSTALL_DIR%\client_monitor.py"
echo.
echo To test the installation:
echo   1. Check Task Scheduler for "ClientMonitor" task
2. Restart your PC and check the log file
3. Verify MQTT messages on broker (topic: clients/+/presence)

To uninstall:
  Right-click "%INSTALL_DIR%\uninstall_client.bat" and run as Administrator.
echo.
pause
