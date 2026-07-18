# Tongou / Tuya smart breaker electrical data

Reference: [Tongou Tuya smart device API](https://www.tongou.com/es/api/tuya-smart-device-api/)

## phase_a RAW (preferred)

Cloud API and some LAN firmware expose `phase_a` (often **DP 6** on `dlq` breakers) as a Base64-encoded 8-byte blob:

| Bytes | Field   | Unit   | Decode |
|-------|---------|--------|--------|
| 0–1   | Voltage | 0.1 V  | `uint16_be / 10` |
| 2–4   | Current | 0.001 A | `uint24_be / 1000` |
| 5–7   | Power   | 1 W    | `uint24_be` |

Example from the spec: `08 e9 00 00 15 00 00 05` → **228.1 V**, **0.021 A**, **5 W**.

Implementation: `device/energy-consumers/lib/tongou_phase.py`  
Used automatically when registry contains `phase_a: "6"` and the DPS value is present.

## LAN fallback (scalar DPS)

When cloud `phase_a` and LAN RAW are both unavailable, scalar DPS on local tinytuya status are used (calibrated 2026-07-05):

| Metric | DPS | LAN scale |
|--------|-----|-----------|
| Switch | 16 | bool |
| Power | 119 | ×0.271475 |
| Voltage | 115 | ×0.916538 |
| Current | 114 | ×0.21715 (house) / ×0.1425 (garden) |
| Temperature | 131 | ×0.1 (°C) |
| Energy | 125 | ×0.0001 (kWh) |

## Data path (production)

1. **LAN poll** — switch, temperature, energy, breaker state (`103`), run mode (`110`).
2. **Cloud `phase_a`** (if `phase_a: "6"` in registry) — voltage, current, power via Tongou decode (`extra.phase_source: tongou_cloud`).
3. **LAN scalars** — fallback for V/I/P if cloud unavailable.

Implementation: `device/energy-consumers/lib/tongou_phase.py`, `lib/tuya_meter.py`.

## Registry example

```yaml
dps:
  phase_a: "6"
  switch: "16"
  power_w: { id: "119", scale: 0.271475 }
  voltage_v: { id: "115", scale: 0.916538 }
  current_a: { id: "114", scale: 0.21715 }
  temperature_c: { id: "131", scale: 0.1 }
  energy_kwh: { id: "125", scale: 0.0001 }
```

When `phase_a` appears on LAN or via cloud polling, V/I/P are taken from the Tongou decode and override the scalar fields.

Cloud `phase_a` is used automatically for consumers with `phase_a` in registry when LAN lacks RAW data (typical for Tongou `dlq` breakers on local tinytuya).

## Low load: phase_a reporting interval

Tongou breakers **do not push `phase_a` on a fixed schedule**. At low current draw the device refreshes electrical metrics less often (sometimes several minutes apart). Our **30 s LAN poll** still runs, but a given poll may return switch/temperature/state DPS **without** a new `phase_a` blob.

To avoid treating that as offline or skewing dashboard “Updated” timers:

| Layer | Behaviour |
|-------|-----------|
| **Publisher** (`tuya_consumers_publisher.py`) | Reuses last V/I/P for up to `phase_stale_after_s` (default **600 s** for `phase_a` consumers) when a poll has no fresh electrical metrics. Sets `extra.metrics_cached` and `extra.metrics_age_s`. |
| **Online** | LAN DPS without `Error` ⇒ `online: true` even when `phase_a` is missing this cycle. Cloud fallback still applies when LAN key fails (e.g. Err 914). |
| **Dashboard** (flow 840) | Tongou breaker cards use `staleAfterS: 600` and prefer `metadata.receivedAtMs` (publisher poll) over device `timestamp` for the “Updated … ago” clock. |

Registry:

```yaml
poll_interval_s: 30
phase_stale_after_s: 600   # optional; default 600 when phase_a is configured
```

Override globally with `ENERGY_CONSUMERS_PHASE_STALE_SEC`.
