# Front house lights breaker

DIN-rail smart breaker **outside** the house. Powers the **lights in front of the house**.

| Field | Value |
|-------|-------|
| Tuya name | WiFi Din Rail Switch with metering |
| Tuya ref | `eu1663483618285BSTqb` |
| Device ID | `bf8cc8cf863af4b600yc53` |
| Product ID | `jdj6ccklup7btq3a` |
| LAN IP | `192.168.2.172` |
| Protocol | 3.4 |

## MQTT

- Status: `energy/consumers/front-lights-breaker/status`
- Switch: `energy/consumers/front-lights-breaker/command/switch`

## On-site checks

```bash
# DPS map (on automation server)
python3 device/energy-consumers/scripts/probe_tuya_dps.py --device-id bf8cc8cf863af4b600yc53

# Live MQTT
mosquitto_sub -h localhost -t 'energy/consumers/front-lights-breaker/status' -v
```

## Note

The separate Tuya device named **"Breaker outside"** (`bfb1f58994ced1e2fajvee` @ 192.168.2.112) is a different breaker — enable in registry when ready.
