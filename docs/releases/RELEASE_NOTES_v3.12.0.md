# Release Notes — v3.12.0

**Date:** 2026-07-04

## Planned: Grundfos SCALA1 scaffolding (not production-ready)

This release adds **in-repo scaffolding only** for a future Grundfos SCALA1 BLE→MQTT integration. It is marked **planned** until on-site BLE GATT capture is complete.

### Added (scaffolding)

- **Device module** `device/grundfos-scala1/` — BLE probe, MQTT publisher skeleton, metrics map template
- **MQTT spec** `water/grundfos/scala1/#` — documented target topics (not active until configured)
- **systemd unit** + `install_grundfos_service.sh` — run manually after GATT mapping (not invoked by default `install.sh`)
- **Node-RED** flows `412` / `413` and watchdog hooks in `90` — import when publisher works
- **Telegram** `/scala1_*` handlers in flow `413` + `/help` entries in flow `50`
- **Docs** — [GRUNDGOS_SCALA1.md](../GRUNDGOS_SCALA1.md), [device/grundfos-scala1/README.md](../../device/grundfos-scala1/README.md)

### Not included / still required

- Proprietary GATT UUIDs and payload decoding (run `ble_probe.py --dump` on site)
- Validated pressure, flow, alarm, and control commands
- Production deployment on the automation server

Existing Tasmota water pump flows (`410`/`411`, `pompaApa`) are unchanged.

**Next step:** [docs/GRUNDGOS_SCALA1.md](../GRUNDGOS_SCALA1.md)
