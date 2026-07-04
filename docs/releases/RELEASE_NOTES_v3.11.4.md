# v3.11.4 (2026-04-26) — patch

**SMS gateway (ESP32):** Fixes endless **“MQTT broker unavailable”** SMS after power/broker return. Sync WiFi state every loop; reset TCP before reconnect; “MQTT restored” SMS only after a failed connect (not first boot). Docs: README, MQTT protocol, architecture.

**Upgrade:** `cd device/esp32-sms-gateway && pio run -t upload` — no Node-RED changes.
