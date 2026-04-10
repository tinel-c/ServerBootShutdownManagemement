@echo off
REM Create GitHub Release v3.10.2 (run from normal terminal if gh uses proxy in Cursor)
cd /d "%~dp0"

set HTTP_PROXY=
set HTTPS_PROXY=
set ALL_PROXY=

echo Creating GitHub Release for v3.10.2...
gh release create v3.10.2 --title "v3.10.2 - Irrigation system GUI" --notes-file RELEASE_NOTES_v3.10.2.md
if errorlevel 1 (
  echo.
  echo If gh failed (e.g. proxy), create release in browser:
  echo   https://github.com/tinel-c/ServerBootShutdownManagemement/releases/new?tag=v3.10.2
  echo   Title: v3.10.2 - Irrigation system GUI
  echo   Paste content from RELEASE_NOTES_v3.10.2.md
  exit /b 1
)
echo Done. Release is live at https://github.com/tinel-c/ServerBootShutdownManagemement/releases
