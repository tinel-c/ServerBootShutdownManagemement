# Grundfos SCALA1 — BLE protocol notes

> **Status: planned** — capture workflow and placeholder UUID table. See [GRUNDGOS_SCALA1.md](../../GRUNDGOS_SCALA1.md).

The SCALA1 exposes monitoring and control only via **Bluetooth Low Energy** (Grundfos GO app). Grundfos does not publish GATT UUIDs or payload layouts. This document records capture workflow and a placeholder mapping you fill after on-site probing.

## Device identification

| Field | Value |
|-------|--------|
| Product | Grundfos SCALA1 pressure booster |
| Radio | BLE 4.2 (FCC ID `OG3-SCALA1`) |
| App | Grundfos GO / Grundfos GO Remote |
| Typical BLE name | Contains `SCALA` (verify with scan) |

## Capture workflow

1. Install **Grundfos GO** on a phone and pair with the pump (press connect on pump panel).
2. On the automation server (or a laptop near the pump):
   ```bash
   cd /opt/dell_server_management
   source venv/bin/activate
   python3 device/grundfos-scala1/scripts/ble_probe.py --scan
   ```
3. Set `SCALA1_BLE_ADDRESS` in `device/grundfos-scala1/config/.env`.
4. Dump GATT while the pump is idle, then while running, then during an alarm:
   ```bash
   python3 device/grundfos-scala1/scripts/ble_probe.py --dump --json > /tmp/scala1_gatt_idle.json
   ```
5. Optional: use **nRF Connect** on Android/iOS in parallel — log service/characteristic UUIDs and note which values change when Grundfos GO refreshes status.
6. Copy confirmed UUIDs into `.env` or `config/metrics_map.yaml` (see below).
7. Validate:
   ```bash
   python3 device/grundfos-scala1/scripts/ble_probe.py --read
   python3 device/grundfos-scala1/scripts/scala1_mqtt_publisher.py --once
   ```

## Placeholder GATT table (fill after capture)

| Role | Service UUID | Characteristic UUID | Properties | Notes |
|------|--------------|---------------------|------------|-------|
| Telemetry snapshot | _TBD_ | _TBD_ | read, notify? | Pressure, flow, run state |
| Control write | _TBD_ | _TBD_ | write | Start/stop if exposed |
| Device info | _TBD_ | _TBD_ | read | Model, serial, firmware |

## Environment mapping (simple)

After capture, set in `config/.env`:

```bash
SCALA1_TELEMETRY_SERVICE_UUID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
SCALA1_TELEMETRY_CHAR_UUID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
# Optional control (only if writes work without app pairing lock)
SCALA1_CONTROL_WRITE_CHAR_UUID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
SCALA1_CONTROL_START_HEX=
SCALA1_CONTROL_STOP_HEX=
```

## YAML mapping (advanced)

Copy `config/metrics_map.example.yaml` to `config/metrics_map.yaml` and define byte offsets after you decode the telemetry blob.

## Known limitations

- **Pairing:** The pump may require bonding initiated from Grundfos GO; third-party clients might get read-only access or be blocked.
- **Range:** BLE range is typically &lt;10 m through walls — use [ESP32_BLE_PROXY.md](ESP32_BLE_PROXY.md) if the automation server cannot reach the pump.
- **Firmware:** Grundfos may change GATT layout in firmware updates — re-run `--dump` after pump updates.

## References

- [SCALA1 product page](https://product-selection.grundfos.com/products/scala/scala1)
- Grundfos SCALA1 data booklet (Bluetooth + external input)
- Integration manual FCC ID `OG3-SCALA1`
