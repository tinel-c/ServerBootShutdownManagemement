# Tasmota devices

Boards that run [Tasmota](https://tasmota.github.io/docs/) and take part in automation (gates, irrigation, pump, lights, power meters) are listed in [`catalog.yaml`](catalog.yaml). They live in this device folder so the Windows client can fetch one online list. They are not PlatformIO projects and Device Fleet does not ArduinoOTA-flash them.

The client loads this file from GitHub next to [`scripts/status/device_fleet.yaml`](../../scripts/status/device_fleet.yaml). **Device Fleet → Scan Tasmota** asks the broker (`cmnd/tasmotas/Status` and each known topic) and, unless disabled, probes the LAN `/24` once with `http://<ip>/cm?cmnd=Status%200`. A scan from a checkout of this repo rewrites `catalog.yaml` with current IP, firmware, and any new topic. Push that file for other PCs to pick it up.

Each row's status topic is `tele/<topic>/LWT` (`Online` / `Offline`). Telemetry period on these boards is several minutes, so `timeout_sec` is 660.

A scan on 2026-11-22 against broker `192.168.2.4` and `192.168.2.0/24` produced this list. Rows with an IP answered Tasmota `Status`. Irrigation, both living-room lights, and Main Gate published MQTT without an address. Garden Lights, Primary Sliding Gate, and Secondary Sliding Gate did not answer; they stay listed because Node-RED flow 613 already watches those topics. The HTTP sweep found no further Tasmota web UI on the LAN.

| Topic | Name | IP | Firmware |
|-------|------|----|----------|
| `automatizare_poarta` | Main Sliding Gate | 192.168.2.96 | 12.5.0 (bluetooth) |
| `frontHousePower` | Front House Power | 192.168.2.202 | 14.6.0 (release-lite) |
| `pompaApa` | Water Pump | 192.168.2.17 | 13.4.0 |
| `sonoffAtelier` | Workshop Sonoff | 192.168.2.108 | 8.3.1 |
| `sonoffPower320D_afara` | Garden Power Hut | 192.168.2.7 | 13.0.0 (tasmota32) |
| `sursaAcvariu` | Aquarium Light | 192.168.2.137 | 15.0.1 |
| `GardenAutomationLights` | Garden Lights | | |
| `IrigationSystem` | Irrigation System | | |
| `lumina1sufragerie` | Living room light 1 | | |
| `lumina2sufragerie` | Living room light 2 | | |
| `LuncaCetatuiiSlidingGateAutomation` | Primary Sliding Gate | | |
| `MainGate` | Main Gate | | |
| `portaSecundara` | Secondary Sliding Gate | | |

The production main-gate controller is the PlatformIO firmware under `device/PlatformIO_ESP8266_Main_Entry/`. The broker still has a Tasmota topic `MainGate`, so that topic is listed here as well.
