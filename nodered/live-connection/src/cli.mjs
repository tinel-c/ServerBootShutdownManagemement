import "dotenv/config";
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { createClient, loadConfig } from "./client.mjs";
import { runBackup } from "./backup.mjs";
import { resolveBackupStamp } from "./server-time.mjs";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const rootDir = join(__dirname, "..");

function summarizeFlows(flowJson) {
  if (!Array.isArray(flowJson)) {
    return { tabs: 0, nodes: 0, subflows: 0 };
  }
  let tabs = 0;
  let subflows = 0;
  for (const n of flowJson) {
    if (n.type === "tab") tabs += 1;
    if (n.type === "subflow") subflows += 1;
  }
  return { tabs, nodes: flowJson.length, subflows };
}

async function cmdStatus(client) {
  await client.request("/");
  const version = await client.request("/settings").catch(() => null);
  const flows = await client.request("/flows");
  const sum = summarizeFlows(flows);
  console.log("OK: reachable");
  console.log(`  Base: ${client.baseUrl}`);
  if (version && typeof version === "object") {
    if (version.version != null) console.log(`  Node-RED version: ${version.version}`);
  }
  console.log(`  Flow tabs: ${sum.tabs}, subflows: ${sum.subflows}, total nodes: ${sum.nodes}`);
}

async function cmdFlows(client) {
  const flows = await client.request("/flows");
  console.log(JSON.stringify(flows, null, 2));
}

async function cmdSnapshot(client) {
  const clock = await resolveBackupStamp(client);
  const flows = await client.request("/flows");
  const dir = join(rootDir, "snapshots");
  mkdirSync(dir, { recursive: true });
  const file = join(dir, `flows-${clock.stamp}.json`);
  writeFileSync(file, JSON.stringify(flows, null, 2), "utf8");
  console.log(`Wrote ${file}`);
}

async function cmdBackup(client) {
  const { dir, manifest } = await runBackup(client, rootDir);
  console.log(`Backup written to ${dir}`);
  console.log(`  Files: ${Object.keys(manifest.files).join(", ")}`);
  if (manifest.limitations?.length) {
    console.log("Note: see manifest.json limitations (credentials / settings.js).");
  }
}

const cmd = process.argv[2] || "status";

const config = loadConfig();
const client = createClient(config);

try {
  if (cmd === "status") await cmdStatus(client);
  else if (cmd === "flows") await cmdFlows(client);
  else if (cmd === "snapshot") await cmdSnapshot(client);
  else if (cmd === "backup") await cmdBackup(client);
  else {
    console.error("Usage: node src/cli.mjs <status|flows|snapshot|backup>");
    process.exit(1);
  }
} catch (e) {
  console.error(e.message || e);
  process.exit(1);
}
