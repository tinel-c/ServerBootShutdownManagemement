# Release Notes — v3.24.0

**Date:** 2026-11-22  
**Author:** Constantin Bogza

## Summary

The ESP8266 main-gate repository follows the fleet firmware contract. The board that is running the older image still needs one UART flash before later updates can go over the air.

## Changes

### Main gate firmware 1.0.0

- ArduinoOTA listens on UDP 8266 after Wi-Fi has an address. Hostname `esp8266-main-gate`. An OTA start forces Relay 3 off.
- New fleet topic `gate/main/status` carries `device`, `fw`, `ip`, and `ota_port`. Existing `MainGate/CMD` and `MainGate/STAT` relay topics are unchanged.
- The device enrolls on the SMS watchdog (`name` = `PlatformIO_ESP8266_Main_Entry`, interval 60 s).
- The ESP-12E module LED on GPIO2 (active-low) uses the shared Wi-Fi blink pattern.
- `pio run -e esp12e` calls the fleet post-build hook. `flash` stays **false** until `gate/main/status` shows an IP.
- Wi-Fi credentials live only in gitignored `src/password.h`. The committed template is `src/password.h_template`.

## Deploy

```bash
cd ~/ServerBootShutdownManagemement && git fetch && git checkout main && git pull
git submodule update --init device/PlatformIO_ESP8266_Main_Entry
```

Copy `src/password.h_template` to `src/password.h`, then flash once:

```bash
SKIP_FLEET_OTA=1 pio run -e esp12e -t upload --upload-port COMx
```

After `gate/main/status` publishes an IP, set `flash: true` in both fleet YAML files. Later updates are `pio run -e esp12e`.
