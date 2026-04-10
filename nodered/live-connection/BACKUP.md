# Node-RED live backups

This folder connects to your running Node-RED instance over the **Admin HTTP API** and writes exports under `backups/`. Use these instructions for manual runs, scheduled jobs, or **automation agents** that need a reliable, scriptable backup.

## Prerequisites

1. **Node.js 18+** and dependencies installed:

   ```bash
   cd nodered/live-connection
   npm install
   ```

2. **Network reachability** from the machine running the backup to the Node-RED editor URL (default `http://192.168.2.4:1880`).

3. **Configuration** — copy `.env.example` to `.env` and set at least:

   | Variable | Purpose |
   |----------|---------|
   | `NODE_RED_BASE_URL` | Base URL of the instance (no trailing slash required) |
   | `NODE_RED_BEARER_TOKEN` | If Admin API uses Bearer auth |
   | `NODE_RED_USERNAME` / `NODE_RED_PASSWORD` | If Admin API uses HTTP Basic auth |

   If the editor is open on the LAN without auth, you only need `NODE_RED_BASE_URL`.

## What gets backed up

Each run creates a new directory:

`backups/backup-<YYYY-MM-DD-HH-mm-ss>/`

The **folder name uses the Node-RED host’s clock** in the server’s configured timezone (from `GET /diagnostics`, e.g. `Europe/Bucharest`), not your PC’s local time. If diagnostics are unavailable, the name falls back to UTC. `manifest.json` includes `serverClock` (timezone, UTC/local strings, and the same stamp) and `exportedAt` as an ISO instant aligned to the server-reported time.

The folder contains `flows.json`, `settings.json`, `nodes.json`, `npm-modules.json`, optional runtime snapshots, and `manifest.json`. See `manifest.json` for details and **limitations** (encrypted credentials and full `settings.js` are not available via HTTP).

The `backups/` directory is listed in `.gitignore` — copy archives to safe storage if you need them after a disk or host loss.

---

## Ways to run a backup

### 1. Interactive (human-friendly)

Prints a short message and the folder path:

```bash
cd nodered/live-connection
npm run backup
```

Equivalent:

```bash
node src/cli.mjs backup
```

### 2. Agent / automation (machine-readable)

Use this when a **Cursor agent**, CI job, or script must parse the result. It prints **exactly one JSON object** on **stdout** (single line). Exit code **0** means success, **1** means failure.

```bash
cd nodered/live-connection
npm run agent-backup
```

Equivalent:

```bash
node scripts/run-agent-backup.mjs
```

Optional stderr logging (stdout JSON is unchanged):

```bash
node scripts/run-agent-backup.mjs --verbose
```

**Success stdout example:**

```json
{"ok":true,"backupDir":"D:/.../backups/backup-2026-04-10-20-35-45","backupDirRelative":"backups/backup-2026-04-10-20-35-45","manifestPath":".../manifest.json","exportedAt":"2026-04-10T17:35:45.000Z","serverClock":{"timeZone":"Europe/Bucharest","utc":"Fri, 10 Apr 2026 17:35:45 GMT","local":"4/10/2026, 8:35:45 PM","folderStamp":"2026-04-10-20-35-45"},"nodeRedBaseUrl":"http://192.168.2.4:1880","files":["flows.json", "..."]}
```

**Failure stdout example:**

```json
{"ok":false,"error":"fetch failed","code":"..."}
```

Agents should parse stdout as JSON and check `ok === true` before using `backupDir` or paths.

---

## Scheduling (optional)

Run the same commands from **Task Scheduler** (Windows) or **cron** (Linux) on a host that can reach Node-RED. Point the task at `npm run backup` or `npm run agent-backup` inside `nodered/live-connection`, with `PATH` including Node and `cwd` set to that directory.

---

## After a failure: restore

See **`RESTORE.md`** in this folder for importing `flows.json`, reinstalling palette modules, and handling credentials.
