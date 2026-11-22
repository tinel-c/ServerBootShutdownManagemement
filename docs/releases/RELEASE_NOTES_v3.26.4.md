# v3.26.4 (2026-11-22) - ESP firmware harness

**Date:** 2026-11-22  
**Author:** Constantin Bogza

## Summary

The front page and the device playbook now say how this repository builds ESP32 and ESP8266 firmware. A new board is not done until MQTT, OTA, the SMS watchdog, the Windows client, and Node-RED all share one fleet id.

## Changes

- README banners show the ESP family on MQTT and the path from the template to the dashboard.
- [DEVICE_FIRMWARE_DEVELOPMENT.md](../developer/DEVICE_FIRMWARE_DEVELOPMENT.md) lists the five required defaults, the files a new device touches, and the order of work.
- The device-firmware rule, the PlatformIO template, the submodule checklist, the Node-RED flow README, and the MQTT protocol point at that same contract.

## Deploy

Installed PCs take `client-v3.26.4.zip` on the next update check. The client behavior is unchanged from 3.26.3.
