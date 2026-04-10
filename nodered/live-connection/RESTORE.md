# Restoring Node-RED from a `backups/` export

To **create** backups (manual, scheduled, or agent-driven), see **`BACKUP.md`**.

Each run of `npm run backup` creates a timestamped folder under `nodered/live-connection/backups/`, for example:

`backups/backup-2026-04-10-20-39-00/` (folder name uses the Node-RED server’s timezone; see `manifest.json` → `serverClock`)

## What is included (HTTP API)

| File | Use |
|------|-----|
| `flows.json` | Full active flow configuration — primary restore artifact |
| `settings.json` | Subset of runtime/editor settings from `GET /settings` |
| `nodes.json` | Installed palette entries from `GET /nodes` |
| `npm-modules.json` | Unique npm package names; use `modulesExcludingCore` for palette installs under `userDir` after Node-RED is installed |
| `flows-state.json`, `diagnostics.json` | Reference only |
| `context-global.json` | Global context snapshot (if your instance exposes it) |
| `manifest.json` | Export metadata and known limitations |

## What is **not** included (must be handled separately)

- **`flows_cred.json`** — encrypted credential store on the server (`userDir`). The Admin API does not return it. Without it, credential-based nodes (MQTT passwords, API keys, etc.) need passwords re-entered in the editor, or you must restore `flows_cred.json` from a **filesystem** backup of `~/.node-red/` (or your Docker volume).
- **Full `settings.js`** — only partially reflected in `settings.json`. Copy your real `settings.js` if you rely on custom `contextStorage`, `editorTheme`, TLS, etc.

## Restore procedure (new machine / clean Node-RED)

1. **Install Node-RED** (match major version from `settings.json` → `version` if possible).

2. **Install palette dependencies** (from the backup folder). After Node-RED is installed globally or as a service, install contrib packages into the **user directory** (usually `~/.node-red`):

   ```bash
   cd ~/.node-red
   npm install <paste space-separated names from npm-modules.json "modulesExcludingCore">
   ```

   (`modulesExcludingCore` omits the core `node-red` package name, which is not installed as a userDir dependency.) Restart Node-RED after installs.

3. **Import flows**

   - **Editor:** Menu → Import → select `flows.json` → Deploy.  
   - **Or HTTP:** `POST /flows` with the same JSON array and valid Admin auth (see [Admin API](https://nodered.org/docs/api/admin/methods/post/flows/)).

4. **Credentials:** Re-enter secrets in the editor for any broken credential nodes, **or** restore `flows_cred.json` from a filesystem backup alongside the same `flows.json` generation.

5. **Optional:** If you use persistent context on disk, restore those files from server backup; `context-global.json` is mainly useful as documentation of in-memory state at export time.

## Re-running backups

Use `npm run backup` whenever you want a fresh snapshot. Keep copies outside the repo if they contain sensitive data (the default `.gitignore` excludes `backups/`).
