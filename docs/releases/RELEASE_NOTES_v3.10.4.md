# Release Notes v3.10.4

**Release Date:** 2026-04-10  
**Type:** Patch (Node-RED irrigation status)

## Overview

**Flow 421** (irrigation status dashboard) now sends **SMS** and **Telegram** alerts on each irrigation-related **ON/OFF** transition (24V, pump, zones I1–I12), with reliable MQTT and payload handling.

## Changes

### `421-irrigation-status-dashboard.json`

- **SMS**: Publishes to **`sms/gateway/command/send`** on **`mqtt_broker_local`** (aligned with 510), not the Tasmota/device broker.
- **SMS destination**: **`flow.irrigation_sms_to`**, or fallback **`flow.sms_phone`** from the SMS Gateway UI.
- **Telegram**: Fan-out to registered chats; fallback chat id after restarts; **`topic: send`**; plain text body.
- **State detection**: Handles Tasmota **JSON** stat payloads (`POWER` / `POWERn`) in addition to string `ON`/`OFF`.

## Upgrade

1. Import or replace **421** in Node-RED, **Deploy**.
2. Optional: set **`flow.irrigation_sms_to`** (digits only), or rely on the SMS dashboard phone (**`sms_phone`**).
3. Send any message to the Telegram bot once if you rely on **`telegram_chat_ids`** (fallback id covers the primary allowlisted user).
