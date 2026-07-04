# Release Notes v3.10.2

**Release Date:** 2026-04-10  
**Type:** Minor (Node-RED irrigation GUI)

## Overview

Implements a dedicated **irrigation status** dashboard page and fixes **Pause / Skip / Resume** on the sprinkler program controls so they work with FlowFuse Dashboard 2.0 and `node-red-contrib-sprinkler` `timerctl out`.

## Changes

### Node-RED — new dashboard (421)

- **`nodered/flows/421-irrigation-status-dashboard.json`** — New Dashboard 2.0 page at **`/irrigation-status`**:
  - MQTT: `stat/IrigationSystem/#`, `stat/pompaApa/POWER1`, `tele/pompaApa/STATE`
  - Zone cards with per-zone icons and **Started / Ended / Duration**
  - Pump row with optional **Tasmota** link from telemetery IP
  - **Event log** (last 25 lines): pump, zones, 24V — timestamp + icon + message
  - 1s tick to refresh running durations

Import this flow **after** flows that define the same MQTT broker (e.g. 420).

### Node-RED — irrigation controls (420)

- **`nodered/flows/420-irrigation-zones-controls.json`** — **Pause**, **Skip**, and **Resume** buttons now set `msg.topic` to `pause` / `skip` / `resume` (`topicType: str`), matching `timerctl out` (which keys off **topic**, not payload). Layout/editor coordinates updated where applicable.

## Upgrade

1. Deploy updated JSON to Node-RED (import or replace tabs), then **Deploy**.
2. Ensure **`421`** is deployed on the same Dashboard base as **`420`** if you use the status page.
