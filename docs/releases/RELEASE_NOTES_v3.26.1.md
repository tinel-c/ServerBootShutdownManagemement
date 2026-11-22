# Release Notes — v3.26.1

**Date:** 2026-11-22  
**Author:** Constantin Bogza

## Summary

Opening Device Fleet was aborting the Windows tray client. The icon disappeared because Tk and pystray shared one process and Windows faulted `python.exe` inside `tcl86t.dll`.

## Changes

- Device Fleet starts with `pythonw` in its own process. The tray client never loads Tk.
- A second click on **Device Fleet…** raises the window that is already open.
- The tray loop no longer blocks inside the fleet window, so heartbeats and update checks keep running while it is open.

## Deploy

Installed PCs take `client-v3.26.1.zip` on the next update check. This PC can be restarted from the ClientMonitor scheduled task after the zip is on the release.
