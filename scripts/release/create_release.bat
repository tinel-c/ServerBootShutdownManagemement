@echo off
REM Create GitHub release from docs/releases/RELEASE_NOTES_vX.Y.Z.md
cd /d "%~dp0\..\.."
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0create_release.ps1" %*
