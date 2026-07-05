# Garden Power Hut (Sonoff POWR316D / Tasmota)

**Hardware:** SONOFF POW Elite 16A (**POWR316D**), Tasmota on WiFi.

**Location:** Garden power hut — monitors and switches power at the hut.

## Same device, two dashboards

| Dashboard | Flow | UI group | MQTT source |
|-----------|------|----------|-------------|
| **Garden** → Power | **310** | `ui_group_garden_power` | Direct `tele/sonoffPower320D_afara/SENSOR` |
| **Energy** | **840** | `ui_group_consumer_garden-power-hut` | Bridge → `energy/consumers/garden-power-hut/status` |

Tasmota **topic** is `sonoffPower320D_afara` (legacy name from an earlier Sonoff model). Do not change unless you update flow 310, Telegram `/garden_*`, and watchdog **613** together.

## Tasmota MQTT

| Direction | Topic |
|-----------|-------|
| Telemetry | `tele/sonoffPower320D_afara/SENSOR` |
| Relay state | `stat/sonoffPower320D_afara/POWER` |
| Switch cmd | `cmnd/sonoffPower320D_afara/Power` |
| LWT | `tele/sonoffPower320D_afara/LWT` |

Normalized status: `energy/consumers/garden-power-hut/status` via `energy-consumers-publisher.service`.

## Not the same as `breaker-outside`

| Registry id | What it measures |
|-------------|------------------|
| `breaker-outside` | Tuya breaker in **indoor panel** — whole garden circuit feed |
| `garden-power-hut` | Tasmota meter at the **garden hut** (downstream) |

## Related

- `nodered/flows/310-garden-power-monitor.json`
- `nodered/flows/311-garden-power-telegram.json`
- Watchdog: `tele/sonoffPower320D_afara/STATE` (flow 90 / 613)
