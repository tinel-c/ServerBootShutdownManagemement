/**
 * Deploy flow 514 (SMS command ingress) to live Node-RED.
 *   node nodered/live-connection/scripts/deploy-flow-514.mjs
 */
import { readFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { createClient, loadConfig } from "../src/client.mjs";

const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(here, "..", "..");
const flowFile = "514-sms-gateway-interface.json";
const patch = JSON.parse(readFileSync(join(repoRoot, "flows", flowFile), "utf8"));
const patchIds = new Set(patch.map((n) => n.id));
// Removed when 514 became ingress-only (handlers moved to 515).
const obsoleteIds = new Set(["func_sms_command_handler", "mqtt_out_sms_cmd"]);

const client = createClient(loadConfig());
const live = await client.request("/flows");

if (!live.some((n) => n.id === "mqtt_broker_local")) {
  throw new Error("mqtt_broker_local is missing on Node-RED. Import 00-base-config.json first.");
}

const before = live.length;
const dropIds = new Set([...patchIds, ...obsoleteIds]);
const merged = live.filter((n) => !dropIds.has(n.id));
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
    },
    null,
    2
  )
);
