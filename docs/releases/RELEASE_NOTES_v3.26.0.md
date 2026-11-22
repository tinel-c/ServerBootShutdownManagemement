# Release Notes — v3.26.0

**Date:** 2026-11-22  
**Author:** Constantin Bogza

## Summary

A first PlatformIO build on a new PC no longer fails after the firmware image is written. The main gate and the SMS gateway pins move forward. The thyristor board is unchanged; it uses the same post-build hook.

## Changes

### Fleet OTA on a new PC

- `scripts/status/fleet_ota_hook.py` looks for a system Python before PlatformIO’s Python.
- When that interpreter cannot `import yaml` and `paho.mqtt.client`, the hook runs `pip install pyyaml paho-mqtt` and then flashes.
- If pip cannot run, the `.bin` stays on disk and the compile succeeds. Set `SKIP_FLEET_OTA=1` to skip the fleet tool entirely.
- Every device post-script (`PlatformIO_ESP8266_Main_Entry`, the SMS gateway, and the thyristor board) calls this hook.

### Main gate firmware 1.0.1

- Relay commands match `ON` and `OFF` with any case and surrounding space.
- `flash` stays false until firmware 1.0.0 has been written over UART once. The image now on the board, if it is older than 1.0.0, still has no OTA listener.

### SMS gateway firmware 1.1.4

- A watchdog device is marked offline after 2 × its interval, as before.
- An SMS is sent only after 10 minutes continuously offline, at most one “lost” text per device every 30 minutes, and one “online” text only after that lost text.
- A short MQTT flap does not text, and `sendSMS` no longer runs inside the MQTT callback.

## Deploy

Pull this monorepo, then `git submodule update --init`. Rebuild any device with `pio run`. The first build on a PC without PyYAML installs it and then runs the fleet flash.

The SMS gateway (`flash: true`) takes 1.1.4 from `pio run -e lilygo-t-call` when it is online. The main gate still needs one UART flash of an image that binds OTA before later `pio run` updates can land.
