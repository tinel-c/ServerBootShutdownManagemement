# v3.26.3 (2026-11-22) — Device Fleet commands

**Date:** 2026-11-22  
**Author:** Constantin Bogza

## Summary

Device Fleet shows a window icon, and the selected device lists its live status with a button for every command that device already accepts. The main gate is on firmware 1.0.1, so fleet flash is enabled. The Windows updater no longer dies before it copies files.

## Changes

- Device Fleet draws a blue tile icon and, under the device list, prints status (name, online, firmware, IP, age, signal, last payload, and live MQTT) plus one button per command.
- Commands publish the existing topics: thyristor channels, main-gate relays, SMS send, Tasmota power, garden lights, irrigation zones, the pump, and sliding gates.
- `device_commands.py` is included in the client zip and copied by `update_client_files.bat`.
- `apply_update.bat` waits with `ping` instead of `timeout`. `timeout.exe` was closing the updater before the copy ran.
- Main gate `flash` is true in both fleet registries. `pio run -e esp12e` can OTA when `gate/main/status` has a fresh IP.

## Deploy

Installed PCs take `client-v3.26.3.zip` on the next update check.
