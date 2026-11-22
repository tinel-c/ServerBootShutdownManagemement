# Release Notes — v3.26.2

**Date:** 2026-11-22  
**Author:** Constantin Bogza

## Summary

A main-gate UART upload failed after a good build because fleet flash is still disabled for that board. SMS commands now split between an ingress flow and a domain handler.

## Changes

- `device_fleet.py flash` treats `flash: false`, an offline device, or a missing IP as a soft success, so `pio run -t upload` can reach esptool. A failed `espota` to a live board still fails the post-step.
- Flow 514 authorizes SMS and publishes `sms/command/dispatch`. Flow 515 handles domain commands and publishes `sms/command/reply`. Only 514 sends `sms/gateway/command/send`.

## Deploy

Installed PCs take `client-v3.26.2.zip` on the next update check.

Node-RED: `node nodered/live-connection/scripts/deploy-flow-514.mjs` and `node nodered/live-connection/scripts/deploy-flow-515.mjs`.
