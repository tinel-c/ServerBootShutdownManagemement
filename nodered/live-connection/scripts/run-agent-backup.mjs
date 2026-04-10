#!/usr/bin/env node
/**
 * Agent-oriented backup runner: prints a single JSON object on stdout (success or failure).
 * Exit code 0 on success, 1 on failure.
 *
 * Usage:
 *   node scripts/run-agent-backup.mjs
 *   npm run agent-backup
 *
 * Options:
 *   --verbose  Log human-readable lines to stderr; JSON still on stdout.
 */

import "dotenv/config";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";
import { createClient, loadConfig } from "../src/client.mjs";
import { runBackup } from "../src/backup.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const rootDir = join(__dirname, "..");
const verbose = process.argv.includes("--verbose");

function out(obj) {
  console.log(JSON.stringify(obj));
}

function logErr(msg) {
  if (verbose) console.error(msg);
}

try {
  const config = loadConfig();
  logErr(`Connecting to ${config.baseUrl} …`);
  const client = createClient(config);
  const { dir, manifest } = await runBackup(client, rootDir);
  const rel = relative(rootDir, dir).replace(/\\/g, "/");
  logErr(`Backup written to ${dir}`);
  out({
    ok: true,
    backupDir: dir,
    backupDirRelative: rel,
    manifestPath: join(dir, "manifest.json").replace(/\\/g, "/"),
    exportedAt: manifest.exportedAt,
    serverClock: manifest.serverClock,
    nodeRedBaseUrl: manifest.nodeRedBaseUrl,
    files: Object.keys(manifest.files),
  });
  process.exit(0);
} catch (e) {
  out({
    ok: false,
    error: e.message || String(e),
    code: e.code,
  });
  process.exit(1);
}
