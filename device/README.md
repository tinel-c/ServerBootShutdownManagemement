# Device firmware

Device projects live in **separate Git repositories** and are included here as **git submodules** so each firmware can have its own history, issues, and releases. The policy for adding and maintaining them is documented in [DEVICE_SUBMODULES.md](../docs/developer/DEVICE_SUBMODULES.md).

| Path (this repo) | Upstream | Device |
|------------------|----------|--------|
| `device/esp32-sms-gateway/` | [tinel-c/esp32-sms-gateway](https://github.com/tinel-c/esp32-sms-gateway) | ESP32 + SIM800 (LilyGo T-Call) — SMS/MQTT gateway |
| `device/PlatformIO_ESP8266_Main_Entry/` | [tinel-c/PlatformIO_ESP8266_Main_Entry](https://github.com/tinel-c/PlatformIO_ESP8266_Main_Entry) | ESP8266 — main gate (Node-RED 210–212, 514) |

**Clone with all device firmware:**  
`git clone --recurse-submodules <this-repo-url>`

**Already cloned without submodules:**  
`git submodule update --init --recursive`

**Refresh pinned revisions** after you pull in a submodule: from the monorepo root, `git add device/<name>` and commit the updated gitlink.

If you see an old inline path `device/sms-gateway/` on disk from before the submodule move, **close any editor using that folder**, delete `device/sms-gateway`, and run `git submodule update --init` so only `device/esp32-sms-gateway` remains.
