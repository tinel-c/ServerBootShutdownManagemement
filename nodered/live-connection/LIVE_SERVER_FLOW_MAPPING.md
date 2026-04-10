# Live Node-RED ↔ `nodered/flows` mapping

This document ties the **running** Node-RED instance to the **modular JSON exports** in `nodered/flows/`. It was generated from:

- **Live server** (Admin HTTP API): `GET /flows` — tab `id`, `label`, and full flow list  
- **Repo** — each file: nodes whose parent flow tab is the `z` property (standard flow nodes)

**Snapshot:** 2026-04-10 (see `scripts/tab-mapping-analysis.json` for machine-readable output). Re-run:

```bash
cd nodered/live-connection
npm run analyze-tabs
```

**Important:** Imports in this repo are **fragments**: almost only `00-base-config.json` defines a `type: tab` node. Other files attach nodes to a few **stable tab ids** (`tab_dashboard`, `gate_main_tab`, irrigation tab ids). The live editor can still **move nodes between tabs** or **create new tabs**; after that, the live runtime no longer matches the `z` values in git unless you re-export from the server.

---

## 1. Tab IDs used in the repository

These are the **only** flow tab ids referenced by `z` across all `nodered/flows/*.json` files:

| Tab id (in JSON) | Live tab label (192.168.2.4) |
|------------------|------------------------------|
| `tab_dashboard` | Server Management |
| `gate_main_tab` | Gate Management |
| `b3b5bbeab11d67eb` | Irigation control |
| `dd53b5c74524e7c3` | Irigation old ui |

So: **four** logical “home” tabs in git; **19** tabs on the live server.

---

## 2. Live tabs → repo coverage (by tab id)

### 2.1 Tabs that appear in repo exports (`z` matches)

| Live tab label | Tab id | Repo file(s) that reference this id |
|----------------|--------|----------------------------------------|
| Server Management | `tab_dashboard` | Most `nodered/flows/*.json` (see §3). Excludes gate/irrigation-specific files that only use other ids. |
| Gate Management | `gate_main_tab` | `200-gate-base-config.json`, `210-main-gate-controls.json`, `211-main-gate-status.json`, `220-sliding-gate-controls.json`, `230-secondary-gate-controls.json`, plus telegram helpers that mostly use `gate_main_tab` with a few nodes on `tab_dashboard` (`212-gate-telegram.json`, `221-sliding-gate-telegram.json`, `231-secondary-gate-telegram.json`) |
| Irigation control | `b3b5bbeab11d67eb` | `420-irrigation-zones-controls.json` |
| Irigation old ui | `dd53b5c74524e7c3` | `420-irrigation-zones-ORIGINAL.json` |

### 2.2 Live tabs with **no** `z` reference in the repo exports

These tabs exist on the server but **no** file under `nodered/flows/` attaches nodes to these tab ids. They are either created only on the device, moved there after import, or populated from flows not checked into this mapping.

| Live tab label | Tab id |
|----------------|--------|
| SMS gateway | `df2ec36c3dbdb923` |
| Main Gate | `78a53e75516b910d` |
| Automatizare poarta | `1443ac5c69d1a2ac` |
| Automatizare poarta mica | `402ae319d72eccf6` |
| Power Garden | `ec1761727ca60cf2` |
| Garden Lights | `30c2080cd95f07e3` |
| Email to sms | `b4bebeffd798d684` |
| Water pump old ui | `23aa7fa50f4c8897` |
| Acvariu | `857d3990d66f478f` |
| Watchdogs | `8becda4e1ec6a8b9` |
| Telegram interface | `3195cc3e12704648` |
| Tapo Cameras | `9337e17fae1562ac` |
| sms-gateway | `3ad4d40302b85f75` |
| Waterpump | `505d65598f2b53fe` |
| Irrigation UI status | `e826d780f81b166d` |

**Interpretation:** Features whose **module names** in git suggest “garden lights”, “telegram”, “watchdog”, “SMS”, “aquarium”, “camera”, etc., often still list `z: "tab_dashboard"` in the exports, while the **live** system uses **separate tabs** for many of those areas. Treat the live layout as authoritative for what operators see; treat git `z` values as the last import baseline unless you refresh exports from the server.

---

## 3. Repo files → live tab(s) (direct `z` mapping)

`00-base-config.json` defines config (e.g. `ui-base`, MQTT, **and** the `tab_dashboard` tab node) but its config nodes typically have **no** `z`, so it does not show up in per-tab node counts below.

| File | Primary live tab (from `z`) | Notes |
|------|-----------------------------|--------|
| `10-dell-controls.json` | Server Management | |
| `11-dell-status.json` | Server Management | |
| `12-dell-health.json` | Server Management | |
| `12-server-telegram.json` | Server Management | |
| `20-hp-controls.json` | Server Management | |
| `21-hp-status.json` | Server Management | |
| `22-hp-health.json` | Server Management | |
| `200-gate-base-config.json` | Gate Management (+ config without `z`) | |
| `210-main-gate-controls.json` | Gate Management | |
| `211-main-gate-status.json` | Gate Management | |
| `212-gate-telegram.json` | Gate Management (+ few nodes Server Management) | Same feature split across tabs in editor |
| `220-sliding-gate-controls.json` | Gate Management | |
| `221-sliding-gate-telegram.json` | Gate Management (+ few Server Management) | |
| `230-secondary-gate-controls.json` | Gate Management | |
| `231-secondary-gate-telegram.json` | Gate Management (+ few Server Management) | |
| `300-power-base-config.json` | Server Management | |
| `310-garden-power-monitor.json` | Server Management | |
| `311-garden-power-telegram.json` | Server Management | |
| `320-garden-lights-controls.json` | Server Management | Live also has tab **Garden Lights** — likely manual split |
| `321-garden-lights-telegram.json` | Server Management | |
| `40-client-tracking.json` | Server Management | |
| `41-client-automation.json` | Server Management | |
| `42-client-shutdown.json` | Server Management | |
| `400-irrigation-base-config.json` | Server Management | |
| `410-water-pump-controls.json` | Server Management | Live also has **Waterpump** / **Water pump old ui** |
| `411-water-pump-telegram.json` | Server Management | |
| `420-irrigation-zones-ORIGINAL.json` | Irigation old ui | Legacy / alternate UI |
| `420-irrigation-zones-controls.json` | Irigation control | |
| `421-irrigation-status-dashboard.json` | Server Management | Live has **Irrigation UI status** tab — repo still parents nodes to `tab_dashboard` |
| `50-telegram-interface.json` | Server Management | Live has **Telegram interface** tab |
| `500-aquarium-light-controls.json` | Server Management | Live has **Acvariu** tab |
| `501-aquarium-telegram.json` | Server Management | |
| `510-sms-gateway-controls.json` | Server Management | Live has **SMS gateway** / **sms-gateway** tabs |
| `511-sms-gateway-status.json` | Server Management | |
| `512-sms-gateway-telegram.json` | Server Management | |
| `513-sms-gateway-watchdog.json` | Server Management | Live has **Watchdogs** tab |
| `514-sms-gateway-interface.json` | Server Management | |
| `611-camera-management.json` | Server Management | Live has **Tapo Cameras** tab |
| `90-device-watchdog.json` | Server Management | |
| `90-log-console.json` | Server Management | |

---

## 4. Multiple repo modules on one live tab

### Server Management (`tab_dashboard`)

All files listed in §3 that map only to **Server Management** share that single tab in git. On the live server, equivalent functionality may be **spread across** additional tabs (§2.2); the exports do not reflect that split.

### Gate Management (`gate_main_tab`)

Several imports target the same tab: `200-*`, `210-*`, `211-*`, `220-*`, `230-*`, plus telegram variants with most nodes on `gate_main_tab`.

### Irrigation

Two large exports target different irrigation UIs: **Irigation control** vs **Irigation old ui** (`420-irrigation-zones-controls.json` vs `420-irrigation-zones-ORIGINAL.json`).

---

## 5. Manual changes on the live server (how to reconcile)

1. **Tab moves / new tabs:** If nodes were moved to a new tab in the editor, their `z` in git is stale until you export flows from the server and replace or merge files.  
2. **Dedicated “status” tab:** `421-irrigation-status-dashboard.json` uses `tab_dashboard` in git; live includes **Irrigation UI status** — indicates re-parenting or duplicate layout on the device.  
3. **Duplicates / “old ui” tabs:** Live retains **Water pump old ui**, **Irigation old ui**, etc.; git keeps parallel modules (e.g. ORIGINAL irrigation) for some of that.  
4. **Regenerate this mapping:** Run `npm run analyze-tabs` after any major live change; commit the updated `tab-mapping-analysis.json` if you want history.

---

## 6. Related tooling

| Tool | Purpose |
|------|--------|
| `npm run status` | Reachability, Node-RED version, tab/node counts |
| `npm run snapshot` | Save full live `flows.json` under `snapshots/` for diffing against git |
| `npm run backup` | Full Admin API export under `backups/backup-<timestamp>/`; see `RESTORE.md` to import on a new server |
| `npm run agent-backup` | Same backup; single-line JSON on stdout for agents — see `BACKUP.md` |

The `backups/` folder is gitignored; copy archives off-machine if you need them after a host failure.
