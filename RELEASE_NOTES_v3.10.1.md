# Release Notes v3.10.1

**Release Date:** 2026-04-10  
**Type:** Patch (Node-RED layout)

## Overview

Manual update of node positions on the irrigation flow so the Dashboard tab and related logic are easier to read in the Node-RED editor after import.

## Changes

### Node-RED

- **`nodered/flows/420-irrigation-zones-controls.json`** — Layout coordinates adjusted for the irrigation zones / automation UI (Dashboard 2.0); wiring unchanged.
- **`nodered/flows/apply_manual_layout.py`** — Optional helper to merge `x`/`y` from a Node-RED export onto this repo flow using stable fingerprints (see script docstring).

## Upgrade

Deploy updated flow JSON to Node-RED as usual (import or replace tab), then **Deploy** in the editor.
