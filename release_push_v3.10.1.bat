@echo off
REM Create GitHub Release v3.10.1 (run from normal terminal if gh uses proxy in Cursor)
cd /d "%~dp0"

set HTTP_PROXY=
set HTTPS_PROXY=
set ALL_PROXY=

echo Creating GitHub Release for v3.10.1...
gh release create v3.10.1 --title "v3.10.1 - Irrigation tab UI layout" --notes-file RELEASE_NOTES_v3.10.1.md
if errorlevel 1 (
  echo.
  echo If gh failed (e.g. proxy), create release in browser:
  echo   https://github.com/tinel-c/ServerBootShutdownManagemement/releases/new?tag=v3.10.1
  echo   Title: v3.10.1 - Irrigation tab UI layout
  echo   Paste content from RELEASE_NOTES_v3.10.1.md
  exit /b 1
)
echo Done. Release is live at https://github.com/tinel-c/ServerBootShutdownManagemement/releases
