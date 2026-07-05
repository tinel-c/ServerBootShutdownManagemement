# Release notes

Per-version release notes for GitHub tags.

## Create a release

From the repo root (after pushing the tag):

```powershell
# Windows
.\scripts\release\create_release.ps1 3.11.8

# or
scripts\release\create_release.bat 3.11.8
```

```bash
# Linux / Git Bash
./scripts/release/create_release.sh 3.11.8
```

Optional custom title:

```bash
./scripts/release/create_release.sh 3.11.8 "v3.11.8 — Custom title"
```

The script reads `docs/releases/RELEASE_NOTES_vX.Y.Z.md` and derives the title from the first heading when omitted.

Manual fallback:

```bash
gh release create vX.Y.Z --title "vX.Y.Z — …" --notes-file docs/releases/RELEASE_NOTES_vX.Y.Z.md
```

## Recent

| Version | Notes |
|---------|-------|
| v3.16.0 | [RELEASE_NOTES_v3.16.0.md](RELEASE_NOTES_v3.16.0.md) — Tasmota energy consumers, Garden Power Hut |
| v3.15.0 | [RELEASE_NOTES_v3.15.0.md](RELEASE_NOTES_v3.15.0.md) — Energy consumers, Tongou breakers, flow 840 |
| v3.14.0 | [RELEASE_NOTES_v3.14.0.md](RELEASE_NOTES_v3.14.0.md) — Media server, Tuya linking, Server dashboard UI |
| v3.13.0 | [RELEASE_NOTES_v3.13.0.md](RELEASE_NOTES_v3.13.0.md) — Energy charts, Huawei PV forecast, Tapo cameras |
| v3.12.0 | [RELEASE_NOTES_v3.12.0.md](RELEASE_NOTES_v3.12.0.md) — Grundfos SCALA1 scaffolding (planned) |
| v3.11.9 | [RELEASE_NOTES_v3.11.9.md](RELEASE_NOTES_v3.11.9.md) — Install cleanup & architecture v4 |
| v3.11.8 | [RELEASE_NOTES_v3.11.8.md](RELEASE_NOTES_v3.11.8.md) — Huawei SUN2000 energy |
| v3.11.7 | [RELEASE_NOTES_v3.11.7.md](RELEASE_NOTES_v3.11.7.md) — Victron docs |
| v3.11.6 | [RELEASE_NOTES_v3.11.6.md](RELEASE_NOTES_v3.11.6.md) — Victron energy |
| v3.11.5 | [RELEASE_NOTES_v3.11.5.md](RELEASE_NOTES_v3.11.5.md) — Device submodules |

Older versions: see files in this directory or [CHANGELOG.md](../../CHANGELOG.md). Pre-v2.3 overview: [RELEASE_HISTORY.md](../../RELEASE_HISTORY.md).
