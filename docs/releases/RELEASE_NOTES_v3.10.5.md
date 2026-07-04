# Release Notes v3.10.5

**Release Date:** 2026-04-10  
**Type:** Patch (Node-RED irrigation status & zones)

## Overview

**Flow 421** (irrigation status dashboard) adds **rain-aware scheduling** (Open-Meteo), clearer **next-run** UI, **manual trigger** buttons, and maintainable **source** files for embedded functions. **Flow 420** registers extra link nodes so triggers from 421 reach the same **run-gate** paths as the daily scheduler.

## Changes

### `421-irrigation-status-dashboard.json`

- **Weather**: Open-Meteo daily forecast; **wet day** flags from rain amount / probability thresholds (`flow.irrigation_rain_skip_mm`, `flow.irrigation_rain_skip_prob`).
- **Next run**: Greedy scan to the **next dry** calendar day at the configured local time (aligned with scheduler rain skip).
- **UI**: Lawn/Flowers countdown from epoch; **Rain-smart schedule** card (logic + next planned dates); forecast **day tags** for next Lawn/Flowers run; layout/spacing tweaks.
- **Trigger Irrigation Lawn / Flowers**: Same `ON` message as the scheduler, via **`Trigger irrigation → Gate lawn/flowers`** → link nodes to **420** (no rain check — manual only).

### `420-irrigation-zones-controls.json`

- **Link in** nodes for scheduler gates also accept **421** test link outs (`irr421_link_out_test_lawn` / `irr421_link_out_test_flowers`).

### Source helpers (`nodered/flows/`)

- **`_irr421_merge_func.js`** — merge function (sync into flow JSON for deploy).
- **`_irr421_openmeteo.js`**, **`_irr421_scheduler.js`** — reference copies of function bodies.
- **`_patch421.py`** — embeds the `.js` sources into the 421 flow JSON (run after editing sources).

## Upgrade

1. Import **420** and **421** in Node-RED, **Deploy**.
2. Ensure **421** tab runs: weather inject, merge, scheduler tick, MQTT inputs.
3. Optional: set **`flow.irrigation_lat`**, **`flow.irrigation_lon`**, thresholds; use **Trigger Irrigation** only for controlled tests.
