# Release Notes — v3.21.0

**Date:** 2026-11-22  
**Author:** Constantin Bogza

## Summary

ESP firmware now shares one fleet path for status and OTA. The SMS gateway publishes `device`, `fw`, `ip`, and `ota_port`, and `pio run` flashes it. Firmware **1.1.2** is on the live gateway at `192.168.2.60`. SIM800 bring-up no longer toggles a modem that is already on after reboot.

## Changes

### Fleet OTA is the default

- New devices copy [device/templates/platformio-esp32](../../device/templates/platformio-esp32/README.md).
- Post-build flash goes through [scripts/status/fleet_ota_hook.py](../../scripts/status/fleet_ota_hook.py). The hook passes an absolute `firmware.bin` path.
- Status JSON must include `device`, `fw`, `ip`, and `ota_port`. Register the device with `flash: true` unless it cannot run ArduinoOTA.
- Playbook: [DEVICE_FIRMWARE_DEVELOPMENT.md](../developer/DEVICE_FIRMWARE_DEVELOPMENT.md).

### SMS gateway

- Firmware **1.1.2** ([PlatformIO_esp32-sms-gateway](https://github.com/tinel-c/PlatformIO_esp32-sms-gateway) `3ed75ed`).
- `sms/gateway/status` is JSON (`device`, `fw`, `ip`, `ota_port`, plus `wifi`, `mqtt`, `gsm`). `sms/gateway/command/ota` is retired. OTA listens on port 3232 after Wi-Fi has an address.
- SIM800 init keeps the IP5306 boost on, probes `AT` before touching PWRKEY, and pulses the key only when the modem is silent.
- Verified 2026-11-22: fleet OTA of 1.1.1, then 1.1.2. After 1.1.2 the status payload had `gsm` `initialized`. Windows espota failed locally; the retry from `192.168.2.4` completed the upload.

### Commits

- Every commit message names Constantin Bogza with `Co-authored-by: Constantin Bogza <tinel.c@gmail.com>`. Hook: [scripts/git/prepare-commit-msg](../../scripts/git/prepare-commit-msg).

## Deploy

No automation-server service change. Firmware is already on the gateway. To refresh a checkout:

```bash
cd ~/ServerBootShutdownManagemement && git fetch && git checkout main && git pull
git submodule update --init device/PlatformIO_esp32-sms-gateway
```
