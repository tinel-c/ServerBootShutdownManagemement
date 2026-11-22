/**
 * Deploy flow 515 (SMS domain gateway + irrigation program bridge) to live Node-RED.
 *   node nodered/live-connection/scripts/deploy-flow-515.mjs
 */
import { readFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { createClient, loadConfig } from "../src/client.mjs";

const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(here, "..", "..");
const flowFile = "515-sms-domain-gateway.json";
const patch = JSON.parse(readFileSync(join(repoRoot, "flows", flowFile), "utf8"));
const patchIds = new Set(patch.map((n) => n.id));

const client = createClient(loadConfig());
const live = await client.request("/flows");

if (!live.some((n) => n.id === "mqtt_broker_local")) {
  throw new Error("mqtt_broker_local is missing on Node-RED. Import 00-base-config.json first.");
}

const irrigTabId = "b3b5bbeab11d67eb";
const hasIrrigTab = live.some((n) => n.type === "tab" && n.id === irrigTabId);
const irrigBridgeIds = new Set([
  "sms_irrig_bridge_comment",
  "mqtt_in_sms_irrig_area_a",
  "mqtt_in_sms_irrig_area_b",
  "func_sms_irrig_program_bridge",
]);

const normalizedPatch = patch.filter((n) => {
  if (irrigBridgeIds.has(n.id) && !hasIrrigTab) {
    return false;
  }
  return true;
});

const before = live.length;
const merged = live.filter((n) => !patchIds.has(n.id));
const removed = before - merged.length;
merged.push(...normalizedPatch);

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
      irrigationTabPresent: hasIrrigTab,
      irrigBridgeDeployed: hasIrrigTab,
      liveNodesBefore: before,
      patchNodes: normalizedPatch.length,
      replacedExisting: removed,
      liveNodesAfter: merged.length,
    },
    null,
    2
  )
);
