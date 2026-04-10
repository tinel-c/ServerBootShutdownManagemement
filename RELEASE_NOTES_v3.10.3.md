# Release Notes v3.10.3

**Release Date:** 2026-04-10  
**Type:** Minor (Node-RED irrigation)

## Overview

Extends the **Lawn** sprinkler program to **twelve zones (I1–I12)**, reorganizes the irrigation **Dashboard 2.0** layout into **Area A** and **Area B** with duplicate transport controls, and aligns the **status** page (**421**) with **I1–I10** in Area A (including **I2**).

## Changes

### Node-RED — `420-irrigation-zones-controls.json`

- **Sprinkler chain:** Zone timers **I9–I12** follow **I8**; **I12** ends the sequence and triggers the existing pump / 24V stop behaviour (previously tied to I8 only).
- **Zone in** + **link** wiring for **I9–I12** to the existing `POWER14`–`POWER17` MQTT paths.
- **UI groups:** **Area A** — I1 & I3–I10 + Start / Resume / Pause / Skip; **Area B** — I11 & I12 + duplicate same buttons; **I2** kept in a separate small group for manual control (automation path unchanged).
- Flow comment updated to describe I1–I12 and group layout.

### Node-RED — `421-irrigation-status-dashboard.json`

- **Area A** lists **I1–I10** (including **I2**) in one grid; **Area B** — **I11 & I12**.
- Removed the standalone **I2** strip after moving I2 into Area A.

## Upgrade

1. Import or replace **420** and **421** in Node-RED, then **Deploy**.
2. Re-test a full program run: order is **I1 → … → I12** before pump/24V shutdown.
