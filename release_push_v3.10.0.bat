@echo off
REM Create GitHub Release so v3.10.0 appears on Releases page (run from normal terminal if gh uses proxy in Cursor)
cd /d "%~dp0"

set HTTP_PROXY=
set HTTPS_PROXY=
set ALL_PROXY=

echo Creating GitHub Release for v3.10.0...
gh release create v3.10.0 --title "v3.10.0 - SMS Multi-Reply and Comprehensive HELP" --notes-file docs/releases/RELEASE_NOTES_v3.10.0.md
if errorlevel 1 (
  echo.
  echo If gh failed (e.g. proxy), create release in browser:
  echo   https://github.com/tinel-c/ServerBootShutdownManagemement/releases/new?tag=v3.10.0
  echo   Title: v3.10.0 - SMS Multi-Reply and Comprehensive HELP
  echo   Paste content from docs/releases/RELEASE_NOTES_v3.10.0.md
  exit /b 1
)
echo Done. Release is live at https://github.com/tinel-c/ServerBootShutdownManagemement/releases
