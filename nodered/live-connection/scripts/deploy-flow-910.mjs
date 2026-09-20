/**
 * Deploy flow 910 (host metrics dashboard) to live Node-RED.
 *   node nodered/live-connection/scripts/deploy-flow-910.mjs
 */
import { readFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { createClient, loadConfig } from "../src/client.mjs";

const repoRoot = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const flowFile = "910-host-metrics-dashboard.json";
const patch = JSON.parse(readFileSync(join(repoRoot, "flows", flowFile), "utf8"));
const patchIds = new Set(patch.map((n) => n.id));

const client = createClient(loadConfig());
const live = await client.request("/flows");
const before = live.length;
const merged = live.filter((n) => !patchIds.has(n.id));
const removed = before - merged.length;
merged.push(...patch);

await client.request("/flows", {
  method: "POST",
  json: merged,
  headers: { "Node-RED-Deployment-Type": "full" },
});

console.log(
  JSON.stringify(
    {
      ok: true,
      flow: flowFile,
      liveNodesBefore: before,
      patchNodes: patch.length,
      replacedExisting: removed,
      liveNodesAfter: merged.length,
      dashboard: "http://192.168.2.4:1880/dashboard/host",
    },
    null,
    2
  )
);
