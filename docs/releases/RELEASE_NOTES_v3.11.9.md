# v3.11.9 (2026-07-04) — Install cleanup, docs, and architecture diagram

Post-v3.11.8 maintenance release: unified installers, repository cleanup, release tooling, and an updated platform architecture diagram.

## Changed

### Install & update

- **`install.sh`** — backs up/restores Victron and Huawei `.env`; enables core services; runs both energy device installers automatically.
- **`scripts/install/`** — shared `common.sh` + `device_service.sh`; root `install_*_service.sh` wrappers preserve device config on copy.
- **`update.sh`** / **`uninstall.sh`** — Huawei backup, restore, service restart, and removal.

### Repository cleanup

- Release notes moved to **`docs/releases/`** (removed root clutter).
- Replaced six `release_push_v3.10.*.bat` scripts with **`scripts/release/create_release.{sh,ps1,bat}`**.
- Removed agent one-off patch/build scripts and unused diagram generators; flow JSON remains source of truth.

### Documentation

- **`docs/architecture_diagram_v4.svg`** + **`architecture_diagram_v4.png`** — marketing-quality platform overview (Victron + Huawei energy, multi-domain IoT, servers).
- README and [ARCHITECTURE.md](../ARCHITECTURE.md) updated to reference v4 diagram.

## Upgrade

```bash
git pull
sudo ./update.sh
# Re-import Node-RED flows if not already on v3.11.8 energy flows
```

## Quick links

- [Architecture diagram (SVG)](architecture_diagram_v4.svg)
- [Install helpers](../../scripts/install/README.md)
- [Release script](../../scripts/release/create_release.sh)
