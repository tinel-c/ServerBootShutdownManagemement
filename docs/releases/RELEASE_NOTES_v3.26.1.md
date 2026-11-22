# Release Notes — v3.26.1

**Date:** 2026-11-22  
**Author:** Constantin Bogza

## Summary

Opening Device Fleet was aborting the Windows tray client. The icon disappeared because Tk and pystray shared one process and Windows faulted `python.exe` inside `tcl86t.dll`. A main-gate UART upload also failed after a good build when fleet flash was still disabled. SMS commands now split between an ingress flow and a domain handler.

## Changes

- Device Fleet starts with `pythonw` in its own process. The tray client never loads Tk.
- A second click on **Device Fleet…** raises the window that is already open.
- The tray loop no longer blocks inside the fleet window, so heartbeats and update checks keep running while it is open.
- `device_fleet.py flash` treats `flash: false`, an offline device, or a missing IP as a soft success, so `pio run -t upload` can reach esptool. A failed `espota` to a live board still fails the post-step.
- Flow 514 authorizes SMS and publishes `sms/command/dispatch`. Flow 515 handles domain commands and publishes `sms/command/reply`. Only 514 sends `sms/gateway/command/send`.

## Deploy

Installed PCs take `client-v3.26.1.zip` on the next update check. This PC can be restarted from the ClientMonitor scheduled task after the zip is on the release.

Node-RED: `node nodered/live-connection/scripts/deploy-flow-514.mjs` and `node nodered/live-connection/scripts/deploy-flow-515.mjs`.
